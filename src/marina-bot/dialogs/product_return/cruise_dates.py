"""Cruise start / end dates for the Product Return dialog.

Replaces Kore's HD_CruiseDateOrchestrator (an LLM-driven state machine) and PC_CruiseDate_Entities with
explicit workflow nodes. The LLM is only used, through typed structured output, for replies the
deterministic date parser cannot read; everything else is plain, tested code.

    cd_start ──► cd_ask_start ──► cd_validate ──┬─ exact voyage ───────────────► cd_finish
        │             │                          ├─ nearest voyage ► cd_confirm_nearest ─► cd_finish
        │             │                          │                         └─ other date ► cd_validate
        │             └─ skipped / no vessel ────┴─ none / API down ► cd_ask_end ─► cd_finish
        └─ dates already known from the first message skip straight ahead

Pause points (they ask, end the turn, and resume next message): cd_ask_start, cd_confirm_nearest, cd_ask_end.

Behaviour kept from Kore: the exact wording of the questions and of the "closest sailing" confirmation;
a don't-know skips a field; a future start date is rejected; an end date before the start is rejected;
a date without a year makes us ask only for the year; a range gives start and end together.
Changes on purpose: the end date comes from the voyage API when a voyage matches; a corrected date is
validated again instead of being trusted; a field is given up after MAX_FAILED_ATTEMPTS unreadable replies
instead of asking forever; an API outage no longer ends the conversation, we just ask for the end date.
"""

import logging
from dataclasses import dataclass, field, fields
from datetime import date
from typing import Any

from agent_framework import Executor, WorkflowContext, handler

from dialogs.product_return.vessel import is_valid_vessel_id
from models import Turn
from shared import trace
from shared.dates import DateReading, PartialDate, is_future, read_text
from shared.deps import Deps
from shared.flow import connect, goto, pause

log = logging.getLogger(__name__)

STATE_KEY = "cruiseDates"
MAX_FAILED_ATTEMPTS = 3        # unreadable / rejected replies before we continue without that date
MAX_SUGGESTION_ROUNDS = 3      # "closest sailing" proposals before we trust the customer's date
START, END = "start", "end"

# Node ids
CD_START, CD_ASK_START, CD_VALIDATE = "cd_start", "cd_ask_start", "cd_validate"
CD_CONFIRM, CD_ASK_END, CD_FINISH = "cd_confirm_nearest", "cd_ask_end", "cd_finish"


# ============================================================================================
# Messages (wording from the Kore dialog where it had fixed text)
# ============================================================================================
def question(field_name: str) -> str:
    return f"What was the {field_name} date of your cruise? Please include the day, month, and year."


def question_again(field_name: str) -> str:
    return (f"I couldn't match that to a valid {field_name} date — could you confirm the {field_name} date again "
            "with the day, month, and year (e.g., 21 December 2025)?")


def question_year(field_name: str, partial: PartialDate) -> str:
    return f"What year did your cruise {field_name} on {partial.describe()}? Please provide the 4-digit year."


MSG_FUTURE_START = "The start date cannot be a future date. Please provide a past date for when your cruise started."
MSG_FUTURE_END = "The end date cannot be a future date. Please provide the date your cruise ended."
MSG_ASK_CORRECT_START = ("To proceed further, could you please provide the correct start date of your cruise? "
                         "Please include the day, month, and year.")
MSG_YES_NO = "Please reply with *YES* or *NO*."


def msg_end_before_start(start: str) -> str:
    return f"The end date cannot be before the start date ({start}). Please provide the date your cruise ended."


def msg_no_such_cruise(iso: str) -> str:
    return f"We don't have a valid cruise on {iso}. Could you please provide a different start date?"


def msg_giving_up(field_name: str) -> str:
    return f"No problem — we'll continue without the {field_name} date."


def msg_suggestion(s: dict[str, Any]) -> str:
    lines = ["The requested sailing date is not available. The closest cruise itinerary is:",
             f"- Start Date: {s['start']}"]
    if s.get("end"):
        lines.append(f"- End Date: {s['end']}")
    if s.get("days"):
        lines.append(f"- Duration: {s['days']} days")
    if s.get("region"):
        lines.append(f"- Region: {s['region']}")
    return "\n".join(lines) + "\n\nWould you like to proceed with this sailing? Please reply with *YES* or *NO*."


# ============================================================================================
# State: one typed object in session["cruiseDates"] instead of a dozen loose flags
# ============================================================================================
@dataclass
class CruiseDatesState:
    start: str | None = None                                   # ISO, validated
    end: str | None = None                                     # ISO, validated
    end_hint: str | None = None                                # an end date the customer gave; used if the API has none
    partial: dict[str, dict] = field(default_factory=dict)     # field -> PartialDate (no year yet)
    skipped: list[str] = field(default_factory=list)           # fields the customer could not give
    failures: dict[str, int] = field(default_factory=dict)     # unreadable / rejected replies per field
    suggestion: dict[str, Any] | None = None                   # the "closest sailing" waiting for YES / NO
    rejected_starts: list[str] = field(default_factory=list)   # dates the customer turned down
    rounds: int = 0                                            # suggestions made so far
    lookup: str = ""                                           # exact | nearest | none | unavailable | not-run
    notice: str = ""                                           # shown before the next question
    done: bool = False

    @classmethod
    def load(cls, session: dict[str, Any]) -> "CruiseDatesState":
        data = session.get(STATE_KEY) or {}
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, session: dict[str, Any]) -> None:
        session[STATE_KEY] = {f.name: getattr(self, f.name) for f in fields(self)}

    def partial_date(self, field_name: str) -> PartialDate | None:
        return PartialDate.from_dict(self.partial.get(field_name))


def vessel_id_of(turn: Turn) -> str | None:
    for candidate in (turn.entities.get("vessel_id"), turn.session.get("vessel_id"), turn.session.get("usr_vessel_id")):
        if is_valid_vessel_id(candidate):
            return str(candidate).strip()
    return None


def usable_end_hint(st: CruiseDatesState, today: date) -> str | None:
    hint = st.end_hint
    if not hint or is_future(hint, today) or (st.start and hint < st.start):
        return None
    return hint


def route_after_start(turn: Turn, st: CruiseDatesState, today: date) -> str:
    """The start date is settled (or skipped): validate it against the voyage API, or go on to the end date."""
    if st.start and vessel_id_of(turn):
        return CD_VALIDATE
    return route_end_or_finish(st, today)


def route_end_or_finish(st: CruiseDatesState, today: date) -> str:
    if st.end or END in st.skipped:
        return CD_FINISH
    hint = usable_end_hint(st, today)
    if hint:
        st.end = hint
        return CD_FINISH
    return CD_ASK_END


async def interpret(deps: Deps, text: str, field_name: str, turn: Turn | None = None) -> DateReading:
    """Deterministic parser first; the model only for replies the parser cannot read."""
    reading = read_text(text)
    if reading.kind == "unclear" and deps.read_dates is not None:
        try:
            call = deps.read_dates(text, field_name)
            smarter = await (trace.call(turn, "llm", "date_reader", call, lambda r: f"read as {r.kind if r else 'nothing'}")
                             if turn is not None else call)
        except Exception:                       # a model failure must never break the conversation
            log.exception("date reader failed; treating the reply as unclear")
            smarter = None
        if smarter is not None:
            return smarter
    return reading


# ============================================================================================
# Nodes
# ============================================================================================
class CruiseDatesStart(Executor):
    """Starts from scratch, using any dates already extracted from the customer's first message."""

    def __init__(self, deps: Deps):
        super().__init__(id=CD_START)
        self._deps = deps

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        today = self._deps.today()
        st = CruiseDatesState()
        self._seed(turn, st, START, turn.entities.get("start_date") or turn.session.get("usr_start_date"), today)
        self._seed(turn, st, END, turn.entities.get("end_date") or turn.session.get("usr_end_date"), today)
        # Raw text from the extraction step ("Mar 17") must not look like a finished date downstream.
        turn.entities.pop("start_date", None)
        turn.entities.pop("end_date", None)
        nxt = route_after_start(turn, st, today) if st.start else CD_ASK_START
        st.save(turn.session)
        log.info("cruise dates start: start=%s end_hint=%s partial=%s -> %s", st.start, st.end_hint, st.partial, nxt)
        await goto(ctx, turn, nxt)

    @staticmethod
    def _seed(turn: Turn, st: CruiseDatesState, field_name: str, value: Any, today: date) -> None:
        if not value:
            return
        reading = read_text(str(value))
        candidate = reading.start if reading.kind == "dates" else None
        if candidate is None:
            return
        iso = candidate.to_iso()
        if iso is None:                                          # day and month but no year
            st.partial[field_name] = candidate.to_dict()
            return
        if is_future(iso, today):
            if field_name == START:
                st.notice = MSG_FUTURE_START
            return
        if field_name == START:
            st.start = iso
        else:
            st.end_hint = iso


class AskDate(Executor):
    """Asks for the start or end date, then interprets the reply on the next turn."""

    def __init__(self, deps: Deps, field_name: str):
        super().__init__(id=CD_ASK_START if field_name == START else CD_ASK_END)
        self._deps, self._field = deps, field_name

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        f, today = self._field, self._deps.today()
        st = CruiseDatesState.load(turn.session)
        if (st.start if f == START else st.end) or f in st.skipped:     # already settled
            await self._advance(ctx, turn, st, today)
            return
        if not turn.resuming:
            await self._ask(ctx, turn, st)
            return
        await self._answer(ctx, turn, st, today)

    # ---- asking ------------------------------------------------------------------------------
    async def _ask(self, ctx: Any, turn: Turn, st: CruiseDatesState, text: str | None = None) -> None:
        partial = st.partial_date(self._field)
        if st.notice:
            turn.say(st.notice)
            st.notice = ""
        turn.say(text or (question_year(self._field, partial) if partial else question(self._field)))
        st.save(turn.session)
        await pause(ctx, turn, self.id)

    async def _advance(self, ctx: Any, turn: Turn, st: CruiseDatesState, today: date) -> None:
        nxt = route_after_start(turn, st, today) if self._field == START else CD_FINISH
        st.save(turn.session)
        await goto(ctx, turn, nxt)

    # ---- answering ---------------------------------------------------------------------------
    async def _answer(self, ctx: Any, turn: Turn, st: CruiseDatesState, today: date) -> None:
        f = self._field
        turn.resuming = False                      # the reply is consumed here; the next node must not reuse it
        reading = await interpret(self._deps, turn.text, f, turn)

        if reading.kind in ("skip", "no"):                                # "no" to a date question = don't know
            st.skipped.append(f)
            st.partial.pop(f, None)
            await self._advance(ctx, turn, st, today)
            return

        if reading.kind == "year":
            partial = st.partial_date(f)
            if partial is None:
                await self._fail(ctx, turn, st, today)                  # a year with no date to attach it to
                return
            # A range typed without a year left both ends pending: the one year answers both.
            other = st.partial_date(END) if f == START else None
            await self._candidates(ctx, turn, st, today, partial.with_year(reading.year),
                                   self._with_rollover(partial.with_year(reading.year), other, reading.year))
            return

        if reading.kind == "dates":
            first, second = reading.start, reading.end
            if f == START:
                await self._candidates(ctx, turn, st, today, first, second)
            else:
                await self._candidates(ctx, turn, st, today, second or first, None)
            return

        await self._fail(ctx, turn, st, today)

    @staticmethod
    def _with_rollover(start: PartialDate, end: PartialDate | None, year: int) -> PartialDate | None:
        """Give the pending end date the answered year, a year later if it would otherwise precede the start."""
        if end is None:
            return None
        end = end.with_year(year)
        if start.is_full and end.is_full and end.to_iso() < start.to_iso():
            end = end.with_year(year + 1)              # Dec 28 - Jan 4 crosses New Year
        return end

    async def _candidates(self, ctx: Any, turn: Turn, st: CruiseDatesState, today: date,
                          candidate: PartialDate, other: PartialDate | None) -> None:
        f = self._field
        if candidate.year is None:                                       # keep what we have, ask only for the year
            st.partial[f] = candidate.to_dict()
            if f == START and other is not None and other.year is None and other.is_possible:
                st.partial[END] = other.to_dict()
            await self._ask(ctx, turn, st)
            return

        iso = candidate.to_iso()
        if iso is None:                                                  # e.g. Feb 30: never accept, whoever read it
            await self._fail(ctx, turn, st, today)
            return
        if f == START:
            problem = (MSG_FUTURE_START if is_future(iso, today)
                       else msg_no_such_cruise(iso) if iso in st.rejected_starts else None)
            if problem:
                await self._fail(ctx, turn, st, today, problem)
                return
            st.start = iso
            st.partial.pop(START, None)
            end_iso = other.to_iso() if other else None
            if end_iso and end_iso >= iso and not is_future(end_iso, today):
                st.end_hint = end_iso
            st.partial.pop(END, None)
            st.failures[f] = 0
            await self._advance(ctx, turn, st, today)
            return

        problem = (MSG_FUTURE_END if is_future(iso, today)
                   else msg_end_before_start(st.start) if st.start and iso < st.start else None)
        if problem:
            await self._fail(ctx, turn, st, today, problem)
            return
        st.end = iso
        st.partial.pop(END, None)
        st.failures[f] = 0
        await self._advance(ctx, turn, st, today)

    async def _fail(self, ctx: Any, turn: Turn, st: CruiseDatesState, today: date, notice: str | None = None) -> None:
        f = self._field
        st.failures[f] = st.failures.get(f, 0) + 1
        if st.failures[f] >= MAX_FAILED_ATTEMPTS:
            log.info("cruise dates: giving up on %s after %d failed attempts", f, st.failures[f])
            st.skipped.append(f)
            st.partial.pop(f, None)
            turn.say(msg_giving_up(f))
            await self._advance(ctx, turn, st, today)
            return
        await self._ask(ctx, turn, st, notice or question_again(f))


class CruiseDatesLookup(Executor):
    """Service node: is there a voyage on that date? Embarkation API first, then the nearest voyage."""

    def __init__(self, deps: Deps):
        super().__init__(id=CD_VALIDATE)
        self._deps = deps

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        today = self._deps.today()
        turn.resuming = False
        st = CruiseDatesState.load(turn.session)
        vessel = vessel_id_of(turn)
        try:
            match = await trace.call(turn, "api", "osw.find_voyage", self._deps.osw.find_voyage(vessel, st.start),
                                     lambda m: f"{st.start}: {m.kind} match")
        except Exception:
            log.exception("voyage lookup failed for vessel %s on %s; continuing without validation", vessel, st.start)
            st.lookup = "unavailable"
            nxt = route_end_or_finish(st, today)
        else:
            st.lookup = match.kind
            log.info("voyage lookup vessel=%s date=%s -> %s", vessel, st.start, match.kind)
            if match.kind == "exact":
                if match.voyage.end_date:
                    st.end = match.voyage.end_date               # the API is the authority on the end date
                nxt = route_end_or_finish(st, today)
            elif match.kind == "nearest":
                v = match.voyage
                st.suggestion = {"start": v.start_date, "end": v.end_date, "days": v.days, "region": v.region,
                                 "embark_port": v.embark_port, "debark_port": v.debark_port}
                st.rounds += 1
                nxt = CD_CONFIRM
            else:
                nxt = route_end_or_finish(st, today)
        st.save(turn.session)
        await goto(ctx, turn, nxt)


class ConfirmNearest(Executor):
    """Shows the closest sailing; the customer accepts it, gives another date, or says no."""

    def __init__(self, deps: Deps):
        super().__init__(id=CD_CONFIRM)
        self._deps = deps

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        today = self._deps.today()
        st = CruiseDatesState.load(turn.session)
        if not st.suggestion:                                           # nothing to confirm: carry on
            await goto(ctx, turn, route_after_start(turn, st, today))
            return
        if not turn.resuming:
            turn.say(msg_suggestion(st.suggestion))
            turn.suggest("Yes", "No")
            st.save(turn.session)
            await pause(ctx, turn, self.id)
            return

        turn.resuming = False                          # the reply is consumed here; the next node must not reuse it
        reading = await interpret(self._deps, turn.text, START, turn)
        if reading.kind == "yes":
            await self._accept(ctx, turn, st, today)
        elif reading.kind == "dates" and reading.start is not None:
            await self._other_date(ctx, turn, st, today, reading.start)
        elif reading.kind in ("no", "skip"):
            await self._decline(ctx, turn, st)
        else:                                                           # unreadable: ask once more, then treat as no
            st.failures[CD_CONFIRM] = st.failures.get(CD_CONFIRM, 0) + 1
            if st.failures[CD_CONFIRM] >= 2:
                await self._decline(ctx, turn, st)
                return
            turn.say(MSG_YES_NO)
            turn.say(msg_suggestion(st.suggestion))
            turn.suggest("Yes", "No")
            st.save(turn.session)
            await pause(ctx, turn, self.id)

    async def _accept(self, ctx: Any, turn: Turn, st: CruiseDatesState, today: date) -> None:
        suggestion = st.suggestion
        st.start, st.end = suggestion["start"], suggestion.get("end")
        st.suggestion = None
        st.lookup = "nearest-accepted"
        nxt = route_end_or_finish(st, today)
        st.save(turn.session)
        turn.resuming = False
        await goto(ctx, turn, nxt)

    async def _other_date(self, ctx: Any, turn: Turn, st: CruiseDatesState, today: date, candidate: PartialDate) -> None:
        """'No, it was March 3 2026': validate that date too, a few times at most."""
        requested = st.start
        iso = candidate.to_iso()
        if iso is None:                                                  # no year: ask for it at the start question
            st.partial[START] = candidate.to_dict()
            await self._reask_start(ctx, turn, st, question_year(START, candidate), reject=requested)
            return
        if is_future(iso, today):
            await self._reask_start(ctx, turn, st, MSG_FUTURE_START, reject=requested)
            return
        if iso in st.rejected_starts:
            await self._reask_start(ctx, turn, st, msg_no_such_cruise(iso), reject=requested)
            return
        if requested:
            st.rejected_starts.append(requested)
        st.start, st.suggestion = iso, None
        st.save(turn.session)
        turn.resuming = False
        # Past the round limit the customer's date is trusted as given and only the end date is needed.
        await goto(ctx, turn, route_end_or_finish(st, today) if st.rounds >= MAX_SUGGESTION_ROUNDS else CD_VALIDATE)

    async def _decline(self, ctx: Any, turn: Turn, st: CruiseDatesState) -> None:
        await self._reask_start(ctx, turn, st, MSG_ASK_CORRECT_START, reject=st.start)

    async def _reask_start(self, ctx: Any, turn: Turn, st: CruiseDatesState, text: str, reject: str | None) -> None:
        if reject and reject not in st.rejected_starts:
            st.rejected_starts.append(reject)
        st.start, st.suggestion = None, None
        st.failures[CD_CONFIRM] = 0
        turn.say(text)
        st.save(turn.session)
        await pause(ctx, turn, CD_ASK_START)                            # the next reply answers the start question


class CruiseDatesFinish(Executor):
    """Publishes the result under the names the rest of the Kore flow reads (PC_CruiseDate_Entities)."""

    def __init__(self, next_id: str):
        super().__init__(id=CD_FINISH)
        self._next = next_id

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st = CruiseDatesState.load(turn.session)
        st.done = True
        for key, value in (("start_date", st.start), ("end_date", st.end)):
            if value:
                turn.entities[key] = value
                turn.session["usr_" + key] = value
        turn.session["dateCompleted"] = True
        turn.resuming = False
        st.save(turn.session)
        log.info("cruise dates done: start=%s end=%s lookup=%s skipped=%s", st.start, st.end, st.lookup, st.skipped)
        await goto(ctx, turn, self._next)


# ============================================================================================
# Wiring
# ============================================================================================
@dataclass
class CruiseDateNodes:
    start: Executor
    finish: Executor
    pause_nodes: list[Executor]            # where a turn can end and later resume
    all_nodes: list[Executor]
    edges: list[tuple[Executor, Executor]]


def build_cruise_date_nodes(deps: Deps, next_id: str) -> CruiseDateNodes:
    start, finish = CruiseDatesStart(deps), CruiseDatesFinish(next_id)
    ask_start, ask_end = AskDate(deps, START), AskDate(deps, END)
    validate, confirm = CruiseDatesLookup(deps), ConfirmNearest(deps)
    edges = [(start, ask_start), (start, validate), (start, ask_end), (start, finish),
             (ask_start, validate), (ask_start, ask_end), (ask_start, finish),
             (validate, confirm), (validate, ask_end), (validate, finish),
             (confirm, validate), (confirm, finish), (confirm, ask_end),
             (ask_end, finish)]
    return CruiseDateNodes(start=start, finish=finish, pause_nodes=[ask_start, confirm, ask_end],
                           all_nodes=[start, ask_start, validate, confirm, ask_end, finish], edges=edges)


def connect_cruise_date_nodes(builder: Any, nodes: CruiseDateNodes) -> None:
    for source, target in nodes.edges:
        connect(builder, source, target)
