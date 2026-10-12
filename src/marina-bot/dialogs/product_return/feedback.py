"""The satisfaction (CSAT) question after the ticket is created.

Not a Kore node: it is the survey step the web chat shows at the end of a conversation. Flow:

  pd_feedback   "How would you rate your experience? 1 to 5"  (buttons 1-5)
                4 or 5  -> thank the customer
                1 to 3  -> one optional follow-up ("What could we have done better?"), then thank the customer
                "no" / "skip" / an answer that is not a rating (asked twice) -> thank the customer, nothing recorded

The answer is kept in session["csat"] ({"rating", "comment"}) and added to the Zendesk ticket as a private note, so the
agent who picks the ticket up sees it. A failed note never changes what the customer sees. Reached only after a ticket
exists: a failed request ends without a survey.
"""

import logging
import re

from agent_framework import Executor, WorkflowContext, handler

from models import Turn
from shared import trace
from shared.dates import says_skip
from shared.deps import Deps
from shared.flow import finish, pause
from shared.htmltext import esc
from shared.zendesk import ZendeskError

log = logging.getLogger(__name__)

PD_FEEDBACK = "pd_feedback"
MAX_RATING_ASKS = 2
MAX_COMMENT_LENGTH = 1000
RATINGS = ["1", "2", "3", "4", "5"]
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

MSG_ASK_RATING = ("How would you rate your experience today?\n"
                  "Please choose from *1* (very dissatisfied) to *5* (very satisfied).")
MSG_RATING_AGAIN = "Sorry, I didn't catch that. Please reply with a number from *1* to *5*."
MSG_ASK_COMMENT = "I'm sorry we fell short. What could we have done better? You can also type *Skip*."
MSG_THANKS = "Thank you for your feedback. Have a great day!"
MSG_THANKS_NO_RATING = "No problem. Thank you for contacting us. Have a great day!"


def parse_rating(text: str) -> int | None:
    """1 to 5 from "4", "four", "5 stars", "I'd say 3". None when there is no single rating in a short reply."""
    lowered = (text or "").lower().strip()
    if not lowered or len(lowered) > 40:
        return None
    found = {int(m) for m in re.findall(r"(?<![\d.])[1-5](?!\d|\.\d)", lowered)}
    found |= {value for word, value in WORDS.items() if re.search(rf"\b{word}\b", lowered)}
    return found.pop() if len(found) == 1 else None


def declines(text: str) -> bool:
    """True for "no thanks", "skip", "not now": the customer does not want to rate."""
    return says_skip(text) or bool(re.search(r"\b(no thank(s| you)|not now|pass|nothing)\b", (text or "").lower()))


def build_feedback_note(rating: int, comment: str) -> str:
    note = f"<b>CUSTOMER SATISFACTION (CSAT): </b>{rating} / 5"
    return note + (f"<br><b>Comment: </b>{esc(comment)}" if comment else "")


class Feedback(Executor):
    def __init__(self, deps: Deps):
        super().__init__(id=PD_FEEDBACK)
        self._deps = deps

    async def _ask_rating(self, ctx, turn: Turn, *lines: str) -> None:
        for line in lines:
            turn.say(line)
        turn.suggest(*RATINGS)
        turn.session["csatStage"] = "rating"
        await pause(ctx, turn, self.id)

    async def _record(self, ctx, turn: Turn, rating: int, comment: str) -> None:
        s = turn.session
        s["csat"] = {"rating": rating, "comment": comment}
        ticket_id, zendesk = s.get("TicketId"), self._deps.zendesk
        if ticket_id and zendesk is not None:
            try:
                await trace.call(turn, "api", "zendesk.add_private_note", zendesk.add_private_note(ticket_id, build_feedback_note(rating, comment)),
                                 lambda _: f"csat {rating}")
            except ZendeskError as exc:
                log.warning("CSAT note for ticket %s failed: %s", ticket_id, exc)
        await self._end(ctx, turn, MSG_THANKS)

    async def _end(self, ctx, turn: Turn, message: str) -> None:
        for key in ("csatStage", "csatAsks"):
            turn.session.pop(key, None)
        turn.resuming = False
        turn.say(message)
        await finish(ctx, turn)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        s = turn.session
        if not turn.resuming:
            s["csatAsks"] = 1
            await self._ask_rating(ctx, turn, MSG_ASK_RATING)
            return
        turn.resuming = False
        if s.get("csatStage") == "comment":
            comment = "" if says_skip(turn.text) else turn.text.strip()[:MAX_COMMENT_LENGTH]
            await self._record(ctx, turn, s["csat"]["rating"], comment)
            return
        rating = parse_rating(turn.text)
        if rating is None:
            if declines(turn.text) or s.get("csatAsks", 1) >= MAX_RATING_ASKS:
                await self._end(ctx, turn, MSG_THANKS_NO_RATING)
                return
            s["csatAsks"] = s.get("csatAsks", 1) + 1
            await self._ask_rating(ctx, turn, MSG_RATING_AGAIN)
            return
        if rating <= 3:
            s["csat"] = {"rating": rating, "comment": ""}
            s["csatStage"] = "comment"
            turn.say(MSG_ASK_COMMENT)
            turn.suggest("Skip")
            await pause(ctx, turn, self.id)
            return
        await self._record(ctx, turn, rating, "")
