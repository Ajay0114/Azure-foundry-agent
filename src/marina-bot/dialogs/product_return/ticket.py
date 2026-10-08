"""The Zendesk ticket for a return request.

Ports this stretch of the Kore dialog:

  PC_Common_Entity_AdditionalDescription                        pd_ask_additional      (pause point)
  PC_HomeDelivery_Script_PrepareZendeskData
    + PC_HomeDelivery_Service_CreateTicket
    + PC_HomeDelivery_Script_ConversationPrivateNote
    + PC_HomeDelivery_Service_ConversationPrivateNote
    + PC_HomeDelivery_ThanksMessage / _Message_TicketFailed     pd_create_ticket       (pause point on failure)

How it differs from Kore, on purpose:
  * everything the customer typed is HTML-escaped before it goes into the ticket (Kore pastes it in raw, so a message
    containing markup would be rendered inside the agent's Zendesk view);
  * the payload is built by one plain function, `build_ticket_payload`, instead of six string fragments joined by
    service-node tokens, and an empty custom field (for example no delivery type) is left out rather than sent blank;
  * a ticket is created at most once per request: every ticket carries an `external_id`, and before any retry the bot
    first looks for a ticket with that id, so a timeout cannot produce a duplicate;
  * a failed create does not throw the customer's answers away: they are offered a retry (three attempts);
  * the private note carries the whole conversation (`session["transcript"]`), not the last few lines, and a failure to add
    it does not undo the ticket;
  * the tags are configurable (ZENDESK_TAGS) and default to what Kore sent.

Still to be ported (shown as "N/A" in the ticket, as in Kore when absent): booking number, credit card (last 4),
attachments, and the return-document API calls.
"""

import html
import logging
import re
import uuid
from datetime import date
from typing import Any

from agent_framework import Executor, WorkflowContext, handler

from dialogs.product_return.purchase_details import PurchaseDetailsState, QuestionNode, is_resolved
from models import Turn
from shared.cancel import is_cancel_request
from shared.dates import read_yes_no, says_skip
from shared.deps import Deps
from shared.flow import connect, finish
from shared.validators import says_finished
from shared.zendesk import TicketSettings, ZendeskApi, ZendeskError

log = logging.getLogger(__name__)

PD_ASK_ADDITIONAL, PD_CREATE_TICKET = "pd_ask_additional", "pd_create_ticket"
MAX_TICKET_ATTEMPTS = 3
MAX_ADDITIONAL_LENGTH = 2000
SUBJECT = "Your Product Return Request Has Been Received"
PRIORITY = "urgent"
NOT_PROVIDED = "Not Provided"
CATEGORIES = {"Onboard Purchase": "osw_onboard_purchase", "Home Delivery": "osw_home_delivery_hd"}

MSG_ADDITIONAL = "Is there anything else you'd like to add? Any additional details will help us assist you faster."
MSG_TICKET_FAILED = "Something went wrong in creating your request."
MSG_RETRY_QUESTION = "Would you like me to try again? Reply *Yes* to try again or *No* to stop."
MSG_TICKET_GIVE_UP = ("I'm sorry, I wasn't able to create your request. Please try again later or contact our team "
                      "directly. Nothing has been submitted.")
MSG_NOT_SUBMITTED = "Okay, I haven't submitted this request."
MSG_DIDNT_CATCH = "Sorry, I didn't catch that."


def msg_thanks(name: str, ticket_id: int, email: str) -> str:
    return (f"Thank you, {name}. Your return request has been submitted. Your ticket number is *{ticket_id}*. "
            f"Our team will also follow up with you at {email}.")


# ============================================================================================
# The payload (pure functions)
# ============================================================================================
def esc(value: Any) -> str:
    """HTML-escape anything the customer typed."""
    return html.escape(str(value), quote=False)


def _text(value: Any, default: str) -> str:
    return str(value).strip() if value is not None and str(value).strip() else default


def _line(label: str, value: Any) -> str:
    return f"<b>{label} :</b> {esc(value)}<br>"


def _products_html(products: Any) -> str:
    slots = [p for p in products if isinstance(p, dict)] if isinstance(products, list) else []
    if not slots:
        return "No product details captured."
    rows = []
    for number, p in enumerate(slots, 1):
        row = (f"• <b>Product {number}:</b> {esc(p.get('product_name') or 'N/A')} | <b>Qty:</b> {esc(p.get('quantity') or 'N/A')}"
               f" | <b>Condition:</b> {esc(p.get('condition') or 'N/A')}")
        if p.get("condition") == "wrong product" and p.get("expected_product_name"):
            row += f" | <b>Expected:</b> {esc(p['expected_product_name'])}"
        rows.append(row + "<br>")
    return "".join(rows)


def build_description(session: dict[str, Any], entities: dict[str, Any], request_date: str) -> str:
    """The ticket's first comment (Kore: PrepareZendeskData's description fragments), with every value escaped."""
    pii = session.get("piiEntities") or {}
    reason = entities.get("PC_HomeDelivery_Entity_IssueReasonButtons") or session.get("reasonDisplay") or "Other"
    extra = session.get("otherReturnReason") or ""
    additional = entities.get("PC_Common_Entity_AdditionalDescription") or ""
    count = session.get("ProductCount") or entities.get("ProductCount")
    booking = session.get("bookingNumber")
    card = pii.get("creditcard")
    delivery = session.get("deliveryType") or entities.get("PC_HomeDelivery_Entity_DeliveryType") or NOT_PROVIDED
    return "".join([
        f"<b>MARINA BOT  —  PRODUCT RETURN REQUEST | Submitted : {esc(request_date)}</b><br><br><br>",
        "<b>CUSTOMER DETAILS :</b><br>-------------------------<br>",
        _line("Request Details", _text(session.get("initialMessage"), "Not provided")),
        _line("Name", _text(pii.get("name"), "Guest")),
        _line("Email", _text(pii.get("emailId"), "guest@onespaworld.com")),
        _line("Phone", _text(pii.get("phoneNumber"), "Not specified")),
        _line("Country", _text(session.get("Country"), "Not specified")),
        _line("Delivery Type", delivery), "<br>",
        "<b>VOYAGE DETAILS:</b><br>-----------------------<br>",
        _line("Cruise Line", _text(session.get("usr_cruise_line"), "Not specified")),
        _line("Ship Name", _text(session.get("usr_ship_name"), "Not specified")),
        _line("Sail Date", session.get("usr_start_date") or ""), "<br>",
        "<b>SPA RECORD DETAILS :</b><br>---------------------------<br>",
        f"<b>Spa Guest Name(s) : </b>  {esc(_text(session.get('spa_record_name'), NOT_PROVIDED))}<br>",
        _line("Cabin Number", _text(session.get("CabinNumber"), NOT_PROVIDED)), "<br>",
        "<b>RETURN DETAILS:</b><br>-----------------------<br>",
        _line("Purchase Date", _text(session.get("purchaseDateFormatted"), "Unknown")),
        _line("Return Request Date", request_date),
        _line("Return Reason", reason),
        _line("Additional Reason Details", extra) if extra else "",
        _line("Product Count", count if is_resolved(count) else NOT_PROVIDED), "<br>",
        _line("Booking Number", booking if is_resolved(booking) else "N/A"),
        _line("Credit Card (Last 4)", card if is_resolved(card) else "N/A"), "<br>",
        "<b>PRODUCTS :</b><br>--------------<br>", _products_html(session.get("products")), "<br><br>",
        "<b>ADDITIONAL INFORMATION:</b><br>--------------------------------<br>",
        f"{esc(additional)}<br><br>" if additional else "N/A<br>",
    ])


def build_ticket_payload(session: dict[str, Any], entities: dict[str, Any], settings: TicketSettings,
                         external_id: str, today: date) -> dict[str, Any]:
    """The body of POST /api/v2/tickets.json (Kore: PrepareZendeskData + the CreateTicket payload)."""
    pii = session.get("piiEntities") or {}
    request_date = session.get("requestedDate") or today.isoformat()
    ids = settings.field_ids
    delivery = session.get("deliveryType") or entities.get("PC_HomeDelivery_Entity_DeliveryType")
    sail_date = session.get("usr_start_date") or ""
    fields = [
        (ids["inquiry_type"], "osw_product_return"),
        (ids["category"], CATEGORIES.get(delivery or "", "")),
        (ids["product_reason"], session.get("returnReason") or "osw_other2"),
        (ids["return_status"], "osw_return_requested"),
        (ids["created_by"], "chatbot"),
        (ids["cruise_line"], _text(session.get("usr_cruise_line"), "Not specified")),
        (ids["cruise_ship"], _text(session.get("usr_ship_name"), "Not specified")),
        (ids["priority"], PRIORITY),
        (ids["sail_date"], sail_date if re.fullmatch(r"\d{4}-\d{2}-\d{2}", sail_date) else ""),
    ]
    return {"ticket": {
        "subject": SUBJECT,
        "comment": {"html_body": build_description(session, entities, request_date)},
        "requester": {"name": _text(pii.get("name"), "Guest"), "email": _text(pii.get("emailId"), "guest@onespaworld.com")},
        "ticket_form_id": settings.form_id, "brand_id": settings.brand_id, "group_id": settings.group_id,
        "priority": PRIORITY, "tags": list(settings.tags), "external_id": external_id,
        "custom_fields": [{"id": field_id, "value": value} for field_id, value in fields if value != ""],
    }}


def build_private_note(transcript: list[str]) -> str:
    """The conversation as a private comment (Kore: Script_ConversationPrivateNote)."""
    body = "<br><br>".join(esc(line).replace("\n", "<br>") for line in transcript) or "No conversation"
    return f"<b>Conversation Transcript - Product Details : </b><br>------------------------------------------<br><br>{body}"


# ============================================================================================
# Nodes
# ============================================================================================
class AdditionalInfo(QuestionNode):
    """"Anything else to add?" (Kore: PC_Common_Entity_AdditionalDescription). Free text, optional."""

    def __init__(self, deps: Deps, next_id: str):
        super().__init__(PD_ASK_ADDITIONAL, deps, next_id)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st = PurchaseDetailsState.load(turn.session)
        if not turn.resuming:
            await self._ask(ctx, turn, st, MSG_ADDITIONAL)
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        text = " ".join((turn.text or "").split())
        if text and not (says_skip(text) or says_finished(text) or text.lower().strip(" .!") in ("nothing", "none")):
            turn.entities["PC_Common_Entity_AdditionalDescription"] = text[:MAX_ADDITIONAL_LENGTH]
        await self._continue(ctx, turn, st)


class CreateTicket(QuestionNode):
    """Creates the ticket, adds the private transcript, thanks the customer. On failure offers a retry."""

    def __init__(self, deps: Deps):
        super().__init__(PD_CREATE_TICKET, deps, "")

    async def _thank(self, ctx: Any, turn: Turn) -> None:
        pii = turn.session.get("piiEntities") or {}
        turn.say(msg_thanks(_text(pii.get("name"), "there"), turn.session["TicketId"], _text(pii.get("emailId"), "your email")))
        await finish(ctx, turn)

    async def _failed(self, ctx: Any, turn: Turn, st: PurchaseDetailsState) -> None:
        if st.count(st.failures, "ticket") >= MAX_TICKET_ATTEMPTS:
            turn.session["ticketError"] = "failed"
            turn.say(MSG_TICKET_GIVE_UP)
            st.save(turn.session)
            await finish(ctx, turn)
            return
        await self._ask(ctx, turn, st, MSG_TICKET_FAILED, MSG_RETRY_QUESTION)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st, s = PurchaseDetailsState.load(turn.session), turn.session
        if s.get("TicketId"):                                   # never create a second ticket for the same request
            await self._thank(ctx, turn)
            return
        if turn.resuming:                                       # we offered a retry
            turn.resuming = False
            answer = read_yes_no(turn.text)
            if answer is None:
                await self._ask(ctx, turn, st, MSG_DIDNT_CATCH, MSG_RETRY_QUESTION)
                return
            if not answer:
                turn.say(MSG_NOT_SUBMITTED)
                st.save(s)
                await finish(ctx, turn)
                return
        zendesk: ZendeskApi | None = self._deps.zendesk
        if zendesk is None:
            log.error("Zendesk is not configured; cannot create the ticket")
            await self._failed(ctx, turn, st)
            return
        external_id = s.setdefault("ticketExternalId", uuid.uuid4().hex)
        try:
            ticket_id = await zendesk.find_by_external_id(external_id) if st.failures.get("ticket") else None
            if ticket_id is None:
                payload = build_ticket_payload(s, turn.entities, zendesk.ticket_settings, external_id, self._deps.today())
                ticket_id = await zendesk.create_ticket(payload)
        except ZendeskError as exc:
            log.error("ticket creation failed: %s", exc)
            await self._failed(ctx, turn, st)
            return
        s["TicketId"] = ticket_id
        st.save(s)
        try:
            transcript = [*s.get("transcript", []), f"User: {turn.text}"]
            await zendesk.add_private_note(ticket_id, build_private_note(transcript))
        except ZendeskError as exc:                             # the ticket exists; the transcript is a bonus
            s["privateNoteFailed"] = True
            log.warning("private note for ticket %s failed: %s", ticket_id, exc)
        await self._thank(ctx, turn)


# ============================================================================================
# Wiring
# ============================================================================================
class TicketNodes:
    def __init__(self, start: Executor, last: Executor, pause_nodes: list[Executor], edges: list[tuple[Executor, Executor]]):
        self.start, self.last, self.pause_nodes, self.edges = start, last, pause_nodes, edges


def build_ticket_nodes(deps: Deps, cancel: Executor) -> TicketNodes:
    additional = AdditionalInfo(deps, PD_CREATE_TICKET)
    create = CreateTicket(deps)
    edges = [(additional, create), (additional, cancel)]
    return TicketNodes(start=additional, last=create, pause_nodes=[additional, create], edges=edges)


def connect_ticket_nodes(builder: Any, nodes: TicketNodes) -> None:
    for source, target in nodes.edges:
        connect(builder, source, target)
