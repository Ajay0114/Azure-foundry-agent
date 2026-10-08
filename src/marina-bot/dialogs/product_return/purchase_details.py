"""Purchase details for the Product Return dialog: purchaser name, cabin, purchase date, delivery type,
return reason, phone.

Ports this stretch of the Kore dialog (the agent nodes become plain, tested code; wording is Kore's):

  PC_Common_1_Script_VariablestoBotUserSession        pd_vars
  PC_Common_2_Msg_DisplayMsg                          pd_intro
  PC_Common_2_Entity_NameAsPerSpaRecords
    + PC_HomeDelivery_Agent_SpaRecordName
    + PC_HomeDelivery_Script_FullName                 pd_ask_spa_name        (pause point)
  PC_HomeDelivery_PromptNode (model call)             pd_extract
  PC_HomeDelivery_Script_SaveEntities                 pd_save_extraction     (return_extraction.py)
  PC_Home_Delivery_Agent_CabinNumber
    + PC_HomeDelivery_Script_CabinNumber              pd_ask_cabin           (pause point)
  PC_HomeDelivery_Msg_ReturnPolicyInfo                pd_policy_info
  PC_HomeDelivery_Script_SetRequestDate               pd_set_request_date
  PC_HomeDelivery_Agent_PurchasedDate + DateValidations + Msg_FutureDate + Message0075 + Entity_PurchasedDate
                                                      pd_ask_purchase_date   (pause point)
  PC_HomeDelivery_Entity_DeliveryType                 pd_ask_delivery        (pause point)
  PC_HomeDelivery_Entity_IssueReasonButtons
    + PC_HomeDelivery_Script_IssueResonButtonsValidations   pd_ask_reason     (pause point)
  PC_HomeDelivery_Entity_Reason                       pd_ask_reason_text     (pause point, "Other" only)
  Phonenumber_Logic + PC_HomeDelivery_Entity_PhoneNumber + Script0084
                                                      pd_ask_phone           (pause point)
  Cancel_Mid_Workflow                                 pd_cancel

In Kore the phone question comes after the return-details agent (country and similar), which is not ported yet.

Differences from Kore, on purpose:
  * the second extraction fills what it can and the customer is never asked for something they already told us
    (including "I don't know my cabin / purchase date / phone" said in the first message);
  * every question has a retry cap, then the bot continues without that value;
  * names may contain hyphens and apostrophes (Kore's rule rejects "O'Brien"); the purchaser name is not read back
    for confirmation, because the customer typed it moments earlier;
  * a cabin needs at least one digit; a cancel request is recognised at every question below.
"""

import logging
import re
from dataclasses import dataclass, field, fields
from datetime import date
from pathlib import Path
from typing import Any

from agent_framework import Executor, WorkflowContext, handler

from dialogs.product_return.return_extraction import EXTRACT_NODE, process_return_extraction
from models import Turn
from shared.cancel import MSG_CANCELLED, is_cancel_request
from shared.dates import MONTHS, PartialDate, is_future, read_text, says_skip
from shared.deps import Deps
from shared.flow import MessageNode, PromptNode, ScriptNode, connect, finish, goto, pause
from shared.prompts import load_prompt
from shared.validators import (RETURN_REASONS, parse_cabins, parse_delivery_type, parse_phone, parse_purchaser_name,
                               parse_return_reason)

log = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
STATE_KEY = "purchaseDetails"
MAX_NAME_ATTEMPTS = 3
MAX_CABIN_ASKS = 2                 # Kore: the question is put twice, then "I'll continue without it"
MAX_PHONE_ATTEMPTS = 3
MAX_CHOICE_ATTEMPTS = 3            # delivery type and return reason
MAX_REASON_TEXT_LENGTH = 1000
MAX_DATE_ATTEMPTS = 4              # Kore: dateRetryCount >= 4 -> unknown
RETURN_POLICY_DAYS = 60
NAME_SLOT, EMAIL_SLOT = "PC_Common_1_Entity_Name", "PC_Common_1_Entity_Emailid"

PD_VARS, PD_INTRO, PD_ASK_NAME = "pd_vars", "pd_intro", "pd_ask_spa_name"
PD_EXTRACT, PD_SAVE, PD_ASK_CABIN = "pd_extract", "pd_save_extraction", "pd_ask_cabin"
PD_POLICY, PD_SET_DATE, PD_ASK_DATE = "pd_policy_info", "pd_set_request_date", "pd_ask_purchase_date"
PD_ASK_DELIVERY, PD_ASK_REASON, PD_ASK_REASON_TEXT = "pd_ask_delivery", "pd_ask_reason", "pd_ask_reason_text"
PD_ASK_PHONE, PD_CANCEL = "pd_ask_phone", "pd_cancel"


# ============================================================================================
# Messages (Kore's wording)
# ============================================================================================
MSG_INTRO = "To help us locate your purchase, I'll need a few details starting with the purchaser's name."
MSG_ASK_NAME = "What is the name of the purchaser related to this request?"
MSG_NAME_INVALID = ("The name should contain only letters and spaces. For example: John Smith, M Umer, or Robert D. "
                    "Please provide the name again.")
MSG_CONTINUE_WITHOUT = "That's all right — I'll continue without it."


def msg_which_name(options: list[str]) -> str:
    return f"Please confirm which single name was on the spa record: {' or '.join(options)}?"


MSG_CABIN_1 = "What's your cabin number? You'll find it on your end-of-cruise statement or your booking confirmation."
MSG_CABIN_2 = "I just need your cabin number to find your spa details for this cruise. It's usually a number like 8102 or D228."
MSG_CABIN_SEPARATOR = "Please separate multiple cabin numbers using commas only. For example: 4201, 5102"
MSG_CABIN_UNKNOWN = ("That's all right — I'll continue without it. I've noted your cabin number wasn't available, "
                     "so our team can look it up when they follow up.")
MSG_CABIN_THANKS = "Thanks, I've noted your cabin number."
MSG_CABINS_THANKS = "Thanks, I've noted your cabin numbers."

MSG_POLICY = ("Before we continue, please note that returns requested within 60 days of purchase will be eligible "
              "for a refund. Our team will review your request and confirm next steps by email.")
MSG_DATE_FIRST = "Please share the date when you purchased the item."
MSG_DATE_AGAIN = "Please enter the purchase date (MM/DD/YYYY). If you’re not sure, you can enter your best estimate."
MSG_DATE_UNREADABLE = ("I'm sorry, I am unable to recognize the date you entered. Please enter the date again, "
                       "in the YYYY-MM-DD or MM-DD-YYYY form.")
MSG_DATE_FUTURE = "That date appears to be in the future. Please check and enter the actual purchase date."
MSG_DATE_ASK_YEAR = "Could you please specify which year you made the purchase?"
MSG_DATE_ASK_DAY = "Could you please share the specific day of the month you made the purchase?"
MSG_DATE_SEVERAL = ("I noticed a couple of different dates in your message — could you confirm the single, exact "
                    "date you purchased the item?")


def msg_date_outside(start: str, end: str) -> str:
    return f"That date appears to be outside your cruise dates ({start} to {end})."


MSG_DELIVERY = "Was this product bought while you were on the ship, or was it a Home Delivery order?"
MSG_DELIVERY_INVALID = ("I'm sorry, I did not recognize the value you have entered. Please select a value from the list: "
                        "Onboard Purchase or Home Delivery.")
MSG_REASON = "What is the reason for the return?"
MSG_REASON_INVALID = "I'm sorry, I am unable to recognize the string. Please enter again."
MSG_REASON_TEXT = "Please briefly describe the reason for your return"
MSG_REASON_TEXT_INVALID = "I'm sorry, I am unable to recognize the description. Please enter again."


def msg_reason_choices() -> str:
    return MSG_REASON + "\n" + "\n".join(f"{i}. {r.title}" for i, r in enumerate(RETURN_REASONS, 1))


MSG_PHONE = "Please enter a phone number where we can reach you if needed."
MSG_PHONE_INVALID = ("I apologize, I am unable to recognize the phone number you entered. "
                     "Please enter the phone number including the area code.")


# ============================================================================================
# State
# ============================================================================================
@dataclass
class PurchaseDetailsState:
    asks: dict[str, int] = field(default_factory=dict)          # times each question was put
    failures: dict[str, int] = field(default_factory=dict)      # replies we could not use
    date_partial: dict[str, Any] | None = None                  # purchase date still missing its year or day
    last_rejected: str | None = None                            # a purchase date we turned down
    date_seeded: bool = False                                   # the first-message date has been looked at

    @classmethod
    def load(cls, session: dict[str, Any]) -> "PurchaseDetailsState":
        data = session.get(STATE_KEY) or {}
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, session: dict[str, Any]) -> None:
        session[STATE_KEY] = {f.name: getattr(self, f.name) for f in fields(self)}

    def count(self, bucket: dict[str, int], key: str) -> int:
        bucket[key] = bucket.get(key, 0) + 1
        return bucket[key]


def is_resolved(value: Any) -> bool:
    return value is not None and str(value).strip().upper() not in ("", "NULL", "UNKNOWN", "NOT PROVIDED")


def _iso(value: Any) -> str | None:
    return value if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) else None


# ============================================================================================
# Plain steps
# ============================================================================================
# Values this stage (and its extraction) set. Cleared when the stage starts, so a second return in the same
# conversation asks again instead of reusing the first one's answers (the part of Kore's ClearData that applies here).
_STAGE_SESSION_KEYS = (
    "spa_record_name", "CabinNumber", "CabinNumbers", "resolvedCabinNumber", "cabinExtractionCompleted",
    "CabinNumberUnknown", "PurchasedDate", "PCAgentPurchasedDate", "purchaseDateFormatted", "purchaseDateAPI",
    "lastEnteredDate", "isWithinReturnPolicyPeriod", "PurchasedDateUnknown", "Country", "resolvedCountry",
    "CountryUnknown", "ProductCount", "resolvedProductCount", "ProductCountUnknown", "products",
    "PhoneNumberUnknown", "extractionStatus", "requestedDate", "deliveryType", "reasonDisplay", "returnReason",
    "returnReasonMapped", "otherReturnReason")
_STAGE_PII_KEYS = ("sparecordname", "nameAsPerSpa", "phoneNumber")
_STAGE_ENTITY_KEYS = ("SpaRecordName", "PC_Common_2_Entity_NameAsPerSpaRecords", "CabinNumber", "CabinNumbers",
                      "PurchasedDate", "Country", "ProductCount", "PC_HomeDelivery_Entity_PhoneNumber",
                      "PC_HomeDelivery_Entity_DeliveryType", "PC_HomeDelivery_Entity_IssueReasonButtons",
                      "PC_HomeDelivery_Entity_Reason")


def start_purchase_details(turn: Turn) -> None:
    """PC_Common_1_Script_VariablestoBotUserSession, and a clean slate for this stage."""
    for key in _STAGE_SESSION_KEYS:
        turn.session.pop(key, None)
    for key in _STAGE_PII_KEYS:
        turn.session.get("piiEntities", {}).pop(key, None)
    for key in _STAGE_ENTITY_KEYS:
        turn.entities.pop(key, None)
    turn.session["customerName"] = turn.entities.get(NAME_SLOT)
    turn.session["customerEmail"] = turn.entities.get(EMAIL_SLOT)
    PurchaseDetailsState().save(turn.session)


def make_set_request_date(deps: Deps):
    def set_request_date(turn: Turn) -> None:
        turn.session["requestedDate"] = deps.today().isoformat()      # PC_HomeDelivery_Script_SetRequestDate
    return set_request_date


# ============================================================================================
# Question nodes
# ============================================================================================
class _Question(Executor):
    """Shared plumbing for the nodes that ask the customer something and resume on the next message."""

    def __init__(self, node_id: str, deps: Deps, next_id: str):
        super().__init__(id=node_id)
        self._deps, self._next = deps, next_id

    async def _continue(self, ctx: Any, turn: Turn, st: PurchaseDetailsState) -> None:
        st.save(turn.session)
        turn.resuming = False
        await goto(ctx, turn, self._next)

    async def _ask(self, ctx: Any, turn: Turn, st: PurchaseDetailsState, *lines: str) -> None:
        for line in lines:
            turn.say(line)
        st.save(turn.session)
        await pause(ctx, turn, self.id)

    async def _cancel(self, ctx: Any, turn: Turn, st: PurchaseDetailsState) -> None:
        st.save(turn.session)
        turn.resuming = False
        await goto(ctx, turn, PD_CANCEL)


def set_purchaser_name(turn: Turn, name: str) -> None:
    """PC_HomeDelivery_Script_FullName. nameAsPerSpa is read by the transactions document but never set in Kore."""
    pii = turn.session.setdefault("piiEntities", {})
    turn.session["spa_record_name"] = name
    pii["sparecordname"] = pii["nameAsPerSpa"] = name
    turn.entities["SpaRecordName"] = name


class PurchaserName(_Question):
    """The name on the spa record. Accepts one name, a skip ("Not provided"), and asks again for two names."""

    def __init__(self, deps: Deps, next_id: str):
        super().__init__(PD_ASK_NAME, deps, next_id)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st = PurchaseDetailsState.load(turn.session)
        if turn.session.get("spa_record_name"):
            await self._continue(ctx, turn, st)
            return
        if not turn.resuming:
            await self._ask(ctx, turn, st, MSG_ASK_NAME)
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        reading = parse_purchaser_name(turn.text)
        if reading.kind == "name":
            set_purchaser_name(turn, reading.name)
        elif reading.kind == "skip":
            set_purchaser_name(turn, "Not provided")
        elif reading.kind == "multiple":
            await self._ask(ctx, turn, st, msg_which_name(reading.options))
            return
        else:
            if st.count(st.failures, "name") >= MAX_NAME_ATTEMPTS:
                set_purchaser_name(turn, "Not provided")
                turn.say(MSG_CONTINUE_WITHOUT)
            else:
                await self._ask(ctx, turn, st, MSG_NAME_INVALID)
                return
        await self._continue(ctx, turn, st)


class CabinNumber(_Question):
    """One or more cabin numbers. Asked twice at most, with Kore's two wordings, then we move on."""

    def __init__(self, deps: Deps, next_id: str):
        super().__init__(PD_ASK_CABIN, deps, next_id)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st, s = PurchaseDetailsState.load(turn.session), turn.session
        if is_resolved(turn.entities.get("CabinNumber")) or s.get("CabinNumberUnknown"):
            await self._continue(ctx, turn, st)           # already told us, or said they do not know
            return
        if not turn.resuming:
            st.count(st.asks, "cabin")
            await self._ask(ctx, turn, st, MSG_CABIN_1)
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        reading = parse_cabins(turn.text)
        if reading.cabins:
            turn.entities["CabinNumber"] = s["CabinNumber"] = s["resolvedCabinNumber"] = ", ".join(reading.cabins)
            turn.entities["CabinNumbers"] = s["CabinNumbers"] = reading.cabins
            s["cabinExtractionCompleted"] = True
            turn.say(MSG_CABINS_THANKS if len(reading.cabins) > 1 else MSG_CABIN_THANKS)
        elif st.asks.get("cabin", 0) >= MAX_CABIN_ASKS:
            s["CabinNumberUnknown"] = True
            s["cabinExtractionCompleted"] = False
            turn.say(MSG_CABIN_UNKNOWN)
        else:
            st.count(st.asks, "cabin")
            await self._ask(ctx, turn, st, MSG_CABIN_SEPARATOR if reading.bad_separator else MSG_CABIN_2)
            return
        await self._continue(ctx, turn, st)


_MONTH_NAMES = "|".join(sorted(MONTHS, key=len, reverse=True))
_MONTH_YEAR = re.compile(rf"^\s*({_MONTH_NAMES})\.?\s*,?\s*((?:19|20)\d{{2}})\s*$", re.I)       # "feb 2026"
_NUMERIC_MONTH_YEAR = re.compile(r"^\s*(\d{1,2})\s*[/-]\s*((?:19|20)\d{2})\s*$")                  # "02/2026"
_DAY_ONLY = re.compile(r"^\D{0,12}(\d{1,2})(?:st|nd|rd|th)?\D{0,3}$", re.I)                         # "14", "the 14th"


class PurchaseDate(_Question):
    """The purchase date: a real, past date inside the cruise. Partial dates get one targeted follow-up."""

    def __init__(self, deps: Deps, next_id: str):
        super().__init__(PD_ASK_DATE, deps, next_id)

    # ---- entry ---------------------------------------------------------------------------------
    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st, s = PurchaseDetailsState.load(turn.session), turn.session
        if s.get("purchaseDateFormatted") or s.get("PurchasedDate") == "unknown":
            await self._continue(ctx, turn, st)
            return
        today = self._deps.today()
        if not turn.resuming:
            if not st.date_seeded:
                st.date_seeded = True
                if s.get("PurchasedDateUnknown"):                         # they said so in the first message
                    self._set_unknown(turn)
                    await self._continue(ctx, turn, st)
                    return
                raw = turn.entities.get("PurchasedDate")
                if raw:                                                   # what the second extraction found
                    await self._process(ctx, turn, st, today, str(raw), seeded=True)
                    return
            await self._ask(ctx, turn, st, MSG_DATE_FIRST)
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        await self._process(ctx, turn, st, today, turn.text, seeded=False)

    # ---- reading what was typed -----------------------------------------------------------------
    async def _process(self, ctx: Any, turn: Turn, st: PurchaseDetailsState, today: date, text: str,
                       seeded: bool) -> None:
        completed = self._complete_partial(st, text)
        if completed is not None:
            await self._judge(ctx, turn, st, today, completed)
            return
        reading = read_text(text)
        if reading.kind in ("skip", "no") or (reading.kind == "unclear" and says_skip(text)):
            self._set_unknown(turn)
            await self._continue(ctx, turn, st)
            return
        if reading.kind == "dates":
            if reading.end is not None:                                   # a range or two dates: ask for one
                await self._ask(ctx, turn, st, MSG_DATE_SEVERAL)
                return
            candidate = reading.start
            if candidate.year is None:
                st.date_partial = {"day": candidate.day, "month": candidate.month, "year": None}
                await self._ask(ctx, turn, st, MSG_DATE_ASK_YEAR)
                return
            await self._judge(ctx, turn, st, today, candidate)
            return
        month_year = self._month_year(text)
        if month_year is not None:
            st.date_partial = {"day": None, "month": month_year[0], "year": month_year[1]}
            await self._ask(ctx, turn, st, MSG_DATE_ASK_DAY)
            return
        if seeded:                                                        # nothing usable in the first message
            await self._ask(ctx, turn, st, MSG_DATE_FIRST)
            return
        await self._reject(ctx, turn, st, MSG_DATE_UNREADABLE, rejected=None)

    @staticmethod
    def _month_year(text: str) -> tuple[int, int] | None:
        if m := _MONTH_YEAR.match(text):
            return MONTHS[m.group(1).lower()], int(m.group(2))
        if (m := _NUMERIC_MONTH_YEAR.match(text)) and 1 <= int(m.group(1)) <= 12:
            return int(m.group(1)), int(m.group(2))
        return None

    @staticmethod
    def _complete_partial(st: PurchaseDetailsState, text: str) -> PartialDate | None:
        """Answer to 'which year?' or 'which day?' joined to the part we already have."""
        partial = st.date_partial
        if not partial:
            return None
        if partial.get("year") is None:
            reading = read_text(text)
            if reading.kind == "year":
                return PartialDate(partial["day"], partial["month"], reading.year)
        elif partial.get("day") is None and (m := _DAY_ONLY.match(text)) and 1 <= int(m.group(1)) <= 31:
            return PartialDate(int(m.group(1)), partial["month"], partial["year"])
        return None

    # ---- judging a full date --------------------------------------------------------------------
    async def _judge(self, ctx: Any, turn: Turn, st: PurchaseDetailsState, today: date, candidate: PartialDate) -> None:
        st.date_partial = None
        iso = candidate.to_iso()
        if iso is None:                                                   # e.g. 31 June
            await self._reject(ctx, turn, st, MSG_DATE_UNREADABLE, rejected=None)
            return
        if iso == st.last_rejected:                                       # the same date again: Kore gives up
            self._set_unknown(turn)
            await self._continue(ctx, turn, st)
            return
        if is_future(iso, today):
            await self._reject(ctx, turn, st, MSG_DATE_FUTURE, rejected=iso, ask_again=True)
            return
        start, end = _iso(turn.session.get("usr_start_date")), _iso(turn.session.get("usr_end_date"))
        if start and end and not start <= iso <= end:
            await self._reject(ctx, turn, st, msg_date_outside(start, end), rejected=iso, ask_again=True)
            return
        self._accept(turn, st, iso, today)
        await self._continue(ctx, turn, st)

    def _accept(self, turn: Turn, st: PurchaseDetailsState, iso: str, today: date) -> None:
        s, d = turn.session, date.fromisoformat(iso)
        mdy = d.strftime("%m/%d/%Y")
        turn.entities["PurchasedDate"] = s["PurchasedDate"] = s["PCAgentPurchasedDate"] = mdy
        s["purchaseDateFormatted"] = s["purchaseDateAPI"] = s["lastEnteredDate"] = iso
        s["isWithinReturnPolicyPeriod"] = (today - d).days <= RETURN_POLICY_DAYS
        st.last_rejected = None
        st.failures.pop("date", None)

    @staticmethod
    def _set_unknown(turn: Turn) -> None:
        s = turn.session
        turn.entities["PurchasedDate"] = s["PurchasedDate"] = "unknown"
        s["purchaseDateFormatted"] = s["purchaseDateAPI"] = s["lastEnteredDate"] = None
        s["isWithinReturnPolicyPeriod"] = False

    async def _reject(self, ctx: Any, turn: Turn, st: PurchaseDetailsState, message: str, rejected: str | None,
                      ask_again: bool = False) -> None:
        """Explain why, then ask again. A rejected real date is followed by Kore's 'best estimate' question."""
        st.last_rejected = rejected or st.last_rejected
        if st.count(st.failures, "date") >= MAX_DATE_ATTEMPTS:
            self._set_unknown(turn)
            turn.say(MSG_CONTINUE_WITHOUT)
            await self._continue(ctx, turn, st)
            return
        await self._ask(ctx, turn, st, message, *([MSG_DATE_AGAIN] if ask_again else []))



class DeliveryType(_Question):
    """Onboard purchase or home delivery. Three tries, then it is recorded as "Not Provided" (Kore's default)."""

    def __init__(self, deps: Deps, next_id: str):
        super().__init__(PD_ASK_DELIVERY, deps, next_id)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st = PurchaseDetailsState.load(turn.session)
        if not turn.resuming:
            await self._ask(ctx, turn, st, MSG_DELIVERY)
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        choice = parse_delivery_type(turn.text)
        if choice is None:
            if st.count(st.failures, "delivery") < MAX_CHOICE_ATTEMPTS:
                await self._ask(ctx, turn, st, MSG_DELIVERY_INVALID)
                return
            turn.say(MSG_CONTINUE_WITHOUT)
            choice = "Not Provided"
        turn.session["deliveryType"] = turn.entities["PC_HomeDelivery_Entity_DeliveryType"] = choice
        await self._continue(ctx, turn, st)


class ReturnReason(_Question):
    """One of Kore's five reasons. "Other" leads to a free-text description; three failures count as "Other"."""

    def __init__(self, deps: Deps, next_id: str, other_id: str):
        super().__init__(PD_ASK_REASON, deps, next_id)
        self._other = other_id

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st, s = PurchaseDetailsState.load(turn.session), turn.session
        if not turn.resuming:
            await self._ask(ctx, turn, st, msg_reason_choices())
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        reason = parse_return_reason(turn.text)
        if reason is None:
            if st.count(st.failures, "reason") < MAX_CHOICE_ATTEMPTS:
                await self._ask(ctx, turn, st, MSG_REASON_INVALID, msg_reason_choices())
                return
            turn.say(MSG_CONTINUE_WITHOUT)
            reason = RETURN_REASONS[-1]
        s["reasonDisplay"] = turn.entities["PC_HomeDelivery_Entity_IssueReasonButtons"] = reason.title
        s["returnReason"], s["returnReasonMapped"] = reason.zendesk, reason.api         # IssueResonButtonsValidations
        s["otherReturnReason"] = ""
        st.save(s)
        if reason.api == "other":
            await goto(ctx, turn, self._other)
            return
        await self._continue(ctx, turn, st)


class ReturnReasonText(_Question):
    """The description that goes with "Other"."""

    def __init__(self, deps: Deps, next_id: str):
        super().__init__(PD_ASK_REASON_TEXT, deps, next_id)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st = PurchaseDetailsState.load(turn.session)
        if not turn.resuming:
            await self._ask(ctx, turn, st, MSG_REASON_TEXT)
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        text = " ".join((turn.text or "").split())[:MAX_REASON_TEXT_LENGTH]
        if len(text) < 3 or says_skip(text):
            if st.count(st.failures, "reason_text") < MAX_CHOICE_ATTEMPTS:
                await self._ask(ctx, turn, st, MSG_REASON_TEXT_INVALID)
                return
            text = "Other"
        turn.session["otherReturnReason"] = turn.entities["PC_HomeDelivery_Entity_Reason"] = text
        await self._continue(ctx, turn, st)


_NO_PHONE = re.compile(r"\b(?:(?:do not|don'?t|dont|doesn'?t|have no|no)\s+(?:have\s+)?(?:a\s+|any\s+)?(?:phone|number|one)\b"
                       r"|no phone)", re.I)


class PhoneNumber(_Question):
    """A contact phone number, skipped when the customer already gave one (or said they have none)."""

    def __init__(self, deps: Deps, next_id: str):
        super().__init__(PD_ASK_PHONE, deps, next_id)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st, s = PurchaseDetailsState.load(turn.session), turn.session
        pii = s.setdefault("piiEntities", {})
        if is_resolved(pii.get("phoneNumber")) or s.get("PhoneNumberUnknown"):
            await self._continue(ctx, turn, st)           # Phonenumber_Logic: only ask when it is missing
            return
        if not turn.resuming:
            await self._ask(ctx, turn, st, MSG_PHONE)
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        phone = parse_phone(turn.text)
        if phone:
            pii["phoneNumber"] = turn.entities["PC_HomeDelivery_Entity_PhoneNumber"] = phone
        elif says_skip(turn.text) or _NO_PHONE.search(turn.text):
            s["PhoneNumberUnknown"] = True
        elif st.count(st.failures, "phone") >= MAX_PHONE_ATTEMPTS:
            s["PhoneNumberUnknown"] = True
            turn.say(MSG_CONTINUE_WITHOUT)
        else:
            await self._ask(ctx, turn, st, MSG_PHONE_INVALID)
            return
        await self._continue(ctx, turn, st)


class CancelRequest(Executor):
    """Cancel_Mid_Workflow: the customer asked to stop."""

    def __init__(self):
        super().__init__(id=PD_CANCEL)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        turn.say(MSG_CANCELLED)
        await finish(ctx, turn)


# ============================================================================================
# Wiring
# ============================================================================================
@dataclass
class PurchaseDetailNodes:
    start: Executor
    last: Executor
    pause_nodes: list[Executor]           # where a turn can end and later resume
    outputs: list[Executor]               # nodes that can end a turn (pause nodes and the cancel node)
    edges: list[tuple[Executor, Executor]]


def build_purchase_detail_nodes(deps: Deps, next_id: str) -> PurchaseDetailNodes:
    vars_ = ScriptNode(PD_VARS, start_purchase_details, PD_INTRO)
    intro = MessageNode(PD_INTRO, lambda t: MSG_INTRO, PD_ASK_NAME)
    name = PurchaserName(deps, PD_EXTRACT)
    extract = PromptNode(
        PD_EXTRACT, deps.run_prompt,
        build_prompt=lambda t: load_prompt(
            PROMPTS_DIR, "extract_return_details",
            conversation_history=t.session.get("conversationHistoryString", ""),
            initial_message=t.session.get("initialMessage", "")),
        output_name=EXTRACT_NODE, next_id=PD_SAVE)
    save = ScriptNode(PD_SAVE, process_return_extraction, PD_ASK_CABIN)
    cabin = CabinNumber(deps, PD_POLICY)
    policy = MessageNode(PD_POLICY, lambda t: MSG_POLICY, PD_SET_DATE)
    set_date = ScriptNode(PD_SET_DATE, make_set_request_date(deps), PD_ASK_DATE)
    purchase = PurchaseDate(deps, PD_ASK_DELIVERY)
    delivery = DeliveryType(deps, PD_ASK_REASON)
    reason = ReturnReason(deps, PD_ASK_PHONE, PD_ASK_REASON_TEXT)
    reason_text = ReturnReasonText(deps, PD_ASK_PHONE)
    phone = PhoneNumber(deps, next_id)
    cancel = CancelRequest()

    pauses = [name, cabin, purchase, delivery, reason, reason_text, phone]
    edges = [(vars_, intro), (intro, name), (name, extract), (extract, save), (save, cabin), (cabin, policy),
             (policy, set_date), (set_date, purchase), (purchase, delivery), (delivery, reason), (reason, reason_text),
             (reason, phone), (reason_text, phone)]
    edges += [(node, cancel) for node in pauses]
    return PurchaseDetailNodes(start=vars_, last=phone, pause_nodes=pauses, outputs=[*pauses, cancel], edges=edges)


def connect_purchase_detail_nodes(builder: Any, nodes: PurchaseDetailNodes) -> None:
    for source, target in nodes.edges:
        connect(builder, source, target)
