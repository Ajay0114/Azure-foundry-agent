"""Product Return dialog (Kore: PC_HomeDelivery) as one sub-workflow.

Ported so far (in Kore order):

  intent0
   -> PC_Common_1_Script_InitialUserMessage        pr_initial_message
   -> PC_Common_Empathy_Check                      (no config in export; skipped)
   -> PC_Common_1_Msg_Display                      pr_greeting
   -> PC_Common_1_Entity_Name                      pr_name
   -> PC_Common_1_Script_redactionName             pr_redact_name
   -> PC_Common_1_Entity_Emailid                   pr_email
   -> PC_Common_1_Script_redactEmail               pr_redact_email
   -> PC_Common_1_Confirmation_EmailConfirmation   pr_email_confirm   (yes / no)
        no  -> PC_Common_1_Script_DeleteEmailId    pr_delete_email -> pr_email
        yes -> PC_ExtractCruiseEntitiesFromInitialUserMessage   pr_extract
   -> PC_Script_ProcessExtractedEntities           pr_process_extracted
   -> HD_VesselLookupAgent                         pr_vessel_agent    (agent node, may take several turns)
   -> PC_Cruise_Entities                           pr_cruise_entities
   -> HD_CruiseDateOrchestrator + PC_CruiseDate_Entities   cd_* nodes, see cruise_dates.py (redesigned, not a copy)
   -> purchaser name, second extraction, cabin number, return policy note, purchase date, phone
                                                   pd_* nodes, see purchase_details.py
   -> country, product count, product details, confirmation, save    pd_* nodes, see product_details.py
   -> anything else to add, file upload, create the Zendesk ticket + private notes, attachment note, return and
      transactions documents, thank the customer      pd_ask_additional ... pd_finalise_request, see ticket.py
"""

from pathlib import Path

from agent_framework import Executor, Workflow, WorkflowBuilder, WorkflowContext, handler

from dialogs.product_return.cruise_dates import CD_START, build_cruise_date_nodes, connect_cruise_date_nodes
from dialogs.product_return.intake_scripts import process_extracted_entities, set_initial_message
from dialogs.product_return.product_details import (PD_ASK_PRODUCT_COUNT, build_product_nodes,
                                                    connect_product_nodes)
from dialogs.product_return.ticket import PD_ASK_ADDITIONAL, build_ticket_nodes, connect_ticket_nodes
from dialogs.product_return.purchase_details import (PD_VARS, build_purchase_detail_nodes,
                                                     connect_purchase_detail_nodes)
from dialogs.product_return.vessel import make_vessel_spec, save_cruise_entities
from models import Turn
from shared.agent_node import AgentNode
from shared.deps import Deps
from shared.flow import ConfirmNode, MessageNode, PromptNode, ScriptNode, SlotNode, connect, finish, goto
from shared.prompts import load_prompt
from shared.dates import read_yes_no
from shared.validators import parse_email, parse_name

PROMPTS_DIR = Path(__file__).parent / "prompts"

NAME_SLOT = "PC_Common_1_Entity_Name"
EMAIL_SLOT = "PC_Common_1_Entity_Emailid"
EXTRACT_NODE = "PC_ExtractCruiseEntitiesFromInitialUserMessage"


class ProductReturnEntry(Executor):
    """Start node. New dialog -> first node; otherwise resume at the node that asked a question."""

    def __init__(self):
        super().__init__(id="pr_entry")

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        step = turn.session.get("dialog_step")
        turn.resuming = bool(step)
        if not step:
            turn.session["transcript"] = []       # a new request starts a new transcript (the ticket's private note)
        await goto(ctx, turn, step or "pr_initial_message")




def _redact_name(turn: Turn) -> None:
    turn.session.setdefault("piiEntities", {})["name"] = turn.entities.get(NAME_SLOT)


def _redact_email(turn: Turn) -> None:
    turn.session.setdefault("piiEntities", {})["emailId"] = turn.entities.get(EMAIL_SLOT)


def _delete_email(turn: Turn) -> None:
    turn.entities.pop(EMAIL_SLOT, None)
    turn.session.get("piiEntities", {}).pop("emailId", None)


def build_product_return_workflow(deps: Deps) -> Workflow:
    run_prompt = deps.run_prompt
    entry = ProductReturnEntry()
    initial = ScriptNode("pr_initial_message", lambda t: set_initial_message(t.ctx, t.text), "pr_greeting")
    greeting = MessageNode(
        "pr_greeting",
        lambda t: "Thanks for reaching out — I see this is related to something from your cruise. "
                  "I can help with that.",
        "pr_name")
    name = SlotNode(
        "pr_name", NAME_SLOT,
        prompt=lambda t: "Before we get started, please can you provide your name?",
        error="I'm sorry, I did not recognize the name you entered. "
              "Please enter your name (first name, last name, or both).",
        parse=parse_name, next_id="pr_redact_name")
    redact_name = ScriptNode("pr_redact_name", _redact_name, "pr_email")
    email = SlotNode(
        "pr_email", EMAIL_SLOT,
        prompt=lambda t: f"Thanks, *{t.entities.get(NAME_SLOT, '')}*.\n"
                         "Please provide the email address our team should use to follow up on this request.",
        error="I'm sorry, I did not recognize the email you entered. Please enter the email again. "
              "An example of an email address is JohnDoe@abc.com.",
        parse=parse_email, next_id="pr_redact_email")
    redact_email = ScriptNode("pr_redact_email", _redact_email, "pr_email_confirm")
    confirm = ConfirmNode(
        "pr_email_confirm",
        prompt=lambda t: "Just to confirm — is this the best email to contact you?\n"
                         f"*{t.entities.get(EMAIL_SLOT, '')}*\n\n"
                         "Reply *Yes* to confirm or *No* to re-enter it.",
        yes_id="pr_extract", no_id="pr_delete_email", parse_yes_no=read_yes_no)
    delete_email = ScriptNode("pr_delete_email", _delete_email, "pr_email")
    extract = PromptNode(
        "pr_extract", run_prompt,
        build_prompt=lambda t: load_prompt(
            PROMPTS_DIR, "extract_cruise_entities",
            conversation_history=t.session.get("conversationHistoryString", ""),
            initial_message=t.session.get("initialMessage", "")),
        output_name=EXTRACT_NODE, next_id="pr_process_extracted")
    process = ScriptNode(
        "pr_process_extracted",
        lambda t: process_extracted_entities(t.ctx, t.session.get("nodeOutputs", {}).get(EXTRACT_NODE)),
        "pr_vessel_agent")
    vessel_agent = AgentNode("pr_vessel_agent", make_vessel_spec(deps.osw), deps.run_agent,
                             next_id="pr_cruise_entities", failure_id="pr_cruise_entities")
    cruise_entities = ScriptNode("pr_cruise_entities", save_cruise_entities, CD_START)
    dates = build_cruise_date_nodes(deps, next_id=PD_VARS)
    purchase = build_purchase_detail_nodes(deps, next_id=PD_ASK_PRODUCT_COUNT)
    products = build_product_nodes(deps, next_id=PD_ASK_ADDITIONAL, cancel=purchase.cancel)
    tickets = build_ticket_nodes(deps, cancel=purchase.cancel)

    builder = WorkflowBuilder(name="product-return", start_executor=entry,
                              output_from=[name, email, confirm, vessel_agent, *dates.pause_nodes,
                                           *purchase.outputs, *products.outputs, *tickets.outputs])
    for src, dst in [
        (entry, initial), (entry, name), (entry, email), (entry, confirm), (entry, vessel_agent),  # new dialog / resume points
        *[(entry, node) for node in [*dates.pause_nodes, *purchase.pause_nodes, *products.pause_nodes,
                                                         *tickets.pause_nodes]],
        (initial, greeting), (greeting, name), (name, redact_name), (redact_name, email),
        (email, redact_email), (redact_email, confirm),
        (confirm, extract), (confirm, delete_email), (delete_email, email),
        (extract, process), (process, vessel_agent), (vessel_agent, cruise_entities), (cruise_entities, dates.start),
        (dates.finish, purchase.start), (purchase.last, products.start), (products.last, tickets.start),
    ]:
        connect(builder, src, dst)
    connect_cruise_date_nodes(builder, dates)
    connect_purchase_detail_nodes(builder, purchase)
    connect_product_nodes(builder, products)
    connect_ticket_nodes(builder, tickets)
    return builder.build()
