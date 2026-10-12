"""Product count and product details for the Product Return dialog.

Ports this stretch of the Kore dialog (wording is Kore's; the agent nodes become a model reader plus plain code):

  PC_HomeDelivery_Agent_ProductCount + Script_ProductCount     pd_ask_product_count   (pause point)
  PC_HomeDelivery_Agent_ProductDetails                         pd_ask_products       (pause point, loops)
  "Please confirm if everything looks correct" (never answered in Kore)   pd_confirm_products   (pause point)
  PC_HomeDelivery_Script_SavingAgentData                       pd_save_products

How it differs from Kore, on purpose:
  * Kore lets the model decide what to ask, what to store and when to stop, then repairs it with a very long
    post-processing script (provenance flags, bleed guards, vetoes). Here the model only READS one reply
    (shared/llm_products.py, typed output) and code decides the rest: which slot a value belongs to, which question
    comes next, and when the list is complete. A bare number or a plain condition word never reaches the model.
  * When the customer does not know how many items there are, Kore silently assumes 1. Here the list simply ends when
    the customer says "that's all".
  * "I don't know the expected product" is recorded as "Not provided" instead of leaving the product out of the ticket.
  * Kore says "Please confirm if everything looks correct" and then never reads the answer (the next node would take
    "yes" as a booking number). Here the products are listed and a real yes/no is asked; "no" starts the list again.
"""

import json
import logging
import re
from typing import Any

from agent_framework import Executor, WorkflowContext, handler

from dialogs.product_return.purchase_details import (MSG_CONTINUE_WITHOUT, PurchaseDetailsState,
                                                     QuestionNode, is_resolved)
from models import Turn
from shared import trace
from shared.cancel import is_cancel_request
from shared.dates import read_yes_no, says_skip
from shared.deps import Deps
from shared.flow import ScriptNode, connect, goto
from shared.llm_products import CONDITIONS, ProductMention, ProductReading
from shared.validators import parse_condition, parse_product_count, parse_quantity, same_product, says_finished

log = logging.getLogger(__name__)

PD_ASK_PRODUCT_COUNT, PD_ASK_PRODUCTS = "pd_ask_product_count", "pd_ask_products"
PD_CONFIRM_PRODUCTS, PD_RESET_PRODUCTS, PD_SAVE_PRODUCTS = "pd_confirm_products", "pd_reset_products", "pd_save_products"
MAX_PRODUCT_ATTEMPTS = 5            # Kore: retry cap 5, then the node ends with what it has
MAX_COUNT_ATTEMPTS = 3
NOT_PROVIDED = "Not provided"

# ============================================================================================
# Messages (Kore's wording)
# ============================================================================================
MSG_COUNT = "How many items are you returning in total? Please reply with just the number — for example, 4."
MSG_COUNT_CONFIRM = "Just to confirm — how many items in total are you returning, counting each one separately?"
MSG_COUNT_RETRY = "I'm sorry, I couldn't tell how many items that is. Please reply with just the number — for example, 4."
MSG_NAME = "Thanks. Please tell me the name of the product you are returning."
MSG_EXPECTED = "Thanks. What product did you expect to receive instead?"
MSG_NEXT_PRODUCT = "Got it. Please provide the name of the next product."
MSG_NEXT_OR_DONE = ("Got it. Please provide the name of the next product, or say \"that's all\" if there are no more "
                    "products to return.")
MSG_NEED_ONE = ("Before I can submit this, I need the details of at least one product. Please tell me the name of the "
                "first product you are returning.")
MSG_CANCEL_HINT = " (You can also type cancel if you'd like to stop.)"
MSG_TROUBLE = "I'm having trouble capturing this detail, so I'll pass on the details I have to our team."
MSG_CONFIRM_QUESTION = "Is this correct? Reply *Yes* to confirm or *No* to enter the products again."
MSG_DIDNT_CATCH = "Sorry, I didn't catch that."


def msg_quantity_and_condition(name: str) -> str:
    return (f"Thanks. How many of the {name} are you returning, and what condition are they in? "
            "You can say new, used, damaged, or wrong product.")


def msg_quantity(name: str) -> str:
    return f"Thanks. How many of the {name} are you returning? Please reply with just the number."


def msg_condition(name: str) -> str:
    return f"Thanks. What condition is the {name} in? You can say new, used, damaged, or wrong product."


def msg_missing_details(names: str) -> str:
    return (f"Before I submit this, I still need a few details for {names}. Could you give me the missing quantity or "
            "condition? If you'd rather finish without it, just say \"that's all\" again.")


# ============================================================================================
# Product slots (pure functions: the whole decision logic, easy to read and to test)
# ============================================================================================
Slot = dict[str, Any]
FIELDS = ("product_name", "quantity", "condition", "expected_product_name")


def new_slot() -> Slot:
    return {field: None for field in FIELDS}


def normalised(raw: Any) -> list[Slot]:
    """The stored list as clean slots (the first-message extraction may have left partial ones)."""
    slots = []
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, dict):
            slot = new_slot()
            for field in FIELDS:
                value = item.get(field)
                slot[field] = str(value).strip() if value not in (None, "") else None
            slots.append(slot)
    return slots


def is_complete(slot: Slot) -> bool:
    if not (slot["product_name"] and slot["quantity"] and slot["condition"]):
        return False
    return slot["condition"] != "wrong product" or bool(slot["expected_product_name"])


def total_quantity(slots: list[Slot]) -> int:
    return sum(int(slot["quantity"]) for slot in slots if slot["quantity"])


def target_count(turn: Turn) -> int | None:
    value = turn.entities.get("ProductCount") or turn.session.get("ProductCount")
    try:
        count = int(value)
    except (TypeError, ValueError):
        return None
    return count if count >= 1 else None


def next_question(slots: list[Slot], target: int | None) -> tuple[str, dict[str, Any]]:
    """The first thing still missing, in Kore's order: name, expected product, quantity and condition."""
    for index, slot in enumerate(slots):
        name = slot["product_name"]
        if not name:
            return MSG_NAME, {"slot": index, "field": "name"}
        if slot["condition"] == "wrong product" and not slot["expected_product_name"]:
            return MSG_EXPECTED, {"slot": index, "field": "expected"}
        if not slot["quantity"] and not slot["condition"]:
            return msg_quantity_and_condition(name), {"slot": index, "field": "both"}
        if not slot["quantity"]:
            return msg_quantity(name), {"slot": index, "field": "quantity"}
        if not slot["condition"]:
            return msg_condition(name), {"slot": index, "field": "condition"}
    if not slots:
        return MSG_NAME, {"slot": None, "field": "name"}
    return (MSG_NEXT_PRODUCT if target else MSG_NEXT_OR_DONE), {"slot": None, "field": "next"}


def describe(slots: list[Slot]) -> str:
    return "; ".join(f"{s['product_name'] or '?'} x{s['quantity'] or '?'} ({s['condition'] or 'condition unknown'})"
                     for s in slots)


def describe_question(slots: list[Slot], asked: dict[str, Any] | None) -> str:
    if not asked:
        return ""
    index, field = asked.get("slot"), asked.get("field")
    name = slots[index]["product_name"] if isinstance(index, int) and 0 <= index < len(slots) else None
    return {"name": "the name of a product", "expected": f"the product they expected instead of {name}",
            "both": f"the quantity and condition of {name}", "quantity": f"the quantity of {name}",
            "condition": f"the condition of {name}", "next": "the next product (or that's all)",
            "count": "how many items in total"}.get(field, "")


def apply_reading(slots: list[Slot], reading: ProductReading, asked: dict[str, Any] | None) -> bool:
    """Merge what the model read from ONE reply into the slots. Returns True when anything changed.

    Empty fields are filled; a value already there is replaced only when the customer is answering that very field.
    A different product name always gets its own slot: a product the customer named is never dropped or overwritten.
    """
    changed = False
    asked = asked or {}
    pending = asked.get("slot") if isinstance(asked.get("slot"), int) and 0 <= asked["slot"] < len(slots) else None
    pending_field = asked.get("field")
    claimed: set[int] = set()

    def put(index: int, field: str, value: Any) -> None:
        nonlocal changed
        if value in (None, ""):
            return
        value = str(value)
        current = slots[index][field]
        if not current or (current != value and index == pending and pending_field in (field, "both", "name")
                           and field != "expected_product_name"):
            slots[index][field] = value
            changed = True

    if reading.applies_to_all:
        shared = next((m.condition for m in reading.products if m.condition), None)
        if shared:
            for slot in slots:
                if not slot["condition"]:
                    slot["condition"], changed = shared, True
        reading = ProductReading([m for m in reading.products if m.product_name or m.quantity],
                                 reading.expected_product_name, reading.finished)

    if reading.expected_product_name:
        waiting = [i for i, s in enumerate(slots) if s["condition"] == "wrong product" and not s["expected_product_name"]]
        index = pending if pending in waiting else (waiting[0] if waiting else None)
        if index is not None:
            slots[index]["expected_product_name"], changed = reading.expected_product_name, True

    for mention in reading.products:
        quantity = str(mention.quantity) if mention.quantity else None
        index: int | None = None
        if mention.product_name:
            index = next((i for i, s in enumerate(slots)
                          if i not in claimed and same_product(s["product_name"], mention.product_name)
                          and not is_complete(s)), None)
            if index is None:
                twin = next((s for s in slots if same_product(s["product_name"], mention.product_name)
                             and is_complete(s)), None)
                if twin and quantity in (None, twin["quantity"]) and mention.condition in (None, twin["condition"]):
                    continue                                        # the customer repeated a product we already have
            if index is None and pending is not None and pending not in claimed and not slots[pending]["product_name"]:
                index = pending
            if index is None:
                index = next((i for i, s in enumerate(slots) if i not in claimed and not s["product_name"]), None)
        else:
            if pending is not None and pending not in claimed:
                index = pending
            else:
                index = next((i for i, s in enumerate(slots) if i not in claimed and not is_complete(s)), None)
        if index is None:
            slots.append(new_slot())
            index = len(slots) - 1
            if not mention.product_name and pending is not None:     # "1 new and 1 used": the second is the same product
                slots[index]["product_name"] = slots[pending]["product_name"]
        claimed.add(index)
        put(index, "product_name", mention.product_name)
        put(index, "quantity", quantity)
        put(index, "condition", mention.condition if mention.condition in CONDITIONS else None)
        put(index, "expected_product_name", mention.expected_product_name)
    return changed


_MANY = re.compile(r"\b(?:all|both|every|each|everything|rest)\b", re.I)    # "they are all new": for the model


def shortcut_reading(text: str, slots: list[Slot], asked: dict[str, Any] | None) -> ProductReading | None:
    """Replies that need no model: a bare quantity, a plain condition word, "I don't know" for the expected product."""
    field = (asked or {}).get("field")
    if field == "quantity" and (quantity := parse_quantity(text)):
        return ProductReading([ProductMention(quantity=quantity)])
    if field == "condition" and not _MANY.search(text) and (condition := parse_condition(text)):
        return ProductReading([ProductMention(condition=condition)])
    if field == "expected" and says_skip(text):
        return ProductReading(expected_product_name=NOT_PROVIDED)
    return None


# ============================================================================================
# Nodes
# ============================================================================================
class ProductCountNode(QuestionNode):
    """Total items being returned. A bare number is read directly; a list of products goes to the model."""

    def __init__(self, deps: Deps, next_id: str):
        super().__init__(PD_ASK_PRODUCT_COUNT, deps, next_id)

    def _set_count(self, turn: Turn, count: int) -> None:
        turn.entities["ProductCount"] = turn.session["ProductCount"] = count
        turn.session["resolvedProductCount"] = str(count)
        turn.session["ProductCountUnknown"] = False

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st, s = PurchaseDetailsState.load(turn.session), turn.session
        if is_resolved(turn.entities.get("ProductCount")) or s.get("ProductCountUnknown"):
            s["productCountCompleted"] = True
            await self._continue(ctx, turn, st)
            return
        if not turn.resuming:
            await self._ask(ctx, turn, st, MSG_COUNT)
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        slots = normalised(s.get("products"))
        count = parse_product_count(turn.text)
        if count:
            self._set_count(turn, count)
        elif says_skip(turn.text):
            s["ProductCountUnknown"] = True
        else:
            reading = await self._read(turn, slots)
            named = [m for m in (reading.products if reading else []) if m.product_name]
            if named:
                apply_reading(slots, ProductReading(named), {"slot": None, "field": "name"})
                s["products"] = slots
                if all(m.quantity for m in named):                   # "2 gels and 2 face creams" -> 4
                    self._set_count(turn, sum(m.quantity for m in named))
                else:                                                # names without quantities: do not guess
                    await self._ask(ctx, turn, st, MSG_COUNT_CONFIRM)
                    return
            elif st.count(st.failures, "count") < MAX_COUNT_ATTEMPTS:
                await self._ask(ctx, turn, st, MSG_COUNT_RETRY)
                return
            else:
                s["ProductCountUnknown"] = True
                turn.say(MSG_CONTINUE_WITHOUT)
        s["productCountCompleted"] = True
        s["returnDetailsCompleted"] = bool(s.get("countryCompleted"))
        await self._continue(ctx, turn, st)

    async def _read(self, turn: Turn, slots: list[Slot]) -> ProductReading | None:
        if self._deps.read_products is None:
            return None
        return await trace.call(turn, "llm", "product_reader",
                                self._deps.read_products(turn.text, "how many items in total are being returned", describe(slots)),
                                lambda r: f"{len(r.products) if r else 0} product(s) read")


class ProductDetailsNode(QuestionNode):
    """Collects name, quantity, condition (and the expected product) for each item, until the count is reached."""

    def __init__(self, deps: Deps, next_id: str):
        super().__init__(PD_ASK_PRODUCTS, deps, next_id)

    async def _done(self, ctx: Any, turn: Turn, st: PurchaseDetailsState, slots: list[Slot], path: str) -> None:
        s, target = turn.session, target_count(turn)
        s["products"] = slots
        s["agentNodeExitPath"] = path
        s["partialReturn"] = bool(target and total_quantity(slots) < target and path != "completed")
        turn.entities["AllProductsCaptured"] = path == "completed"
        s["ProductsCollected"] = turn.entities["ProductsCollected"] = total_quantity(slots)
        s["remainingQuantity"] = max(0, (target or 0) - total_quantity(slots))
        await self._continue(ctx, turn, st)

    async def _ask_next(self, ctx: Any, turn: Turn, st: PurchaseDetailsState, slots: list[Slot], prefix: str = "",
                        suffix: str = "") -> None:
        question, st.asked = next_question(slots, target_count(turn))
        turn.session["products"] = slots
        await self._ask(ctx, turn, st, *([prefix] if prefix else []), question + suffix)

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st, s = PurchaseDetailsState.load(turn.session), turn.session
        slots, target = normalised(s.get("products")), target_count(turn)
        if not turn.resuming:
            if slots and all(is_complete(x) for x in slots) and target and total_quantity(slots) >= target:
                await self._done(ctx, turn, st, slots, "completed")          # everything came with the first message
                return
            await self._ask_next(ctx, turn, st, slots)
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return

        finished = says_finished(turn.text)
        reading = shortcut_reading(turn.text, slots, st.asked)
        if reading is None and not (finished and not slots):
            if self._deps.read_products is not None:
                reading = await trace.call(turn, "llm", "product_reader",
                                           self._deps.read_products(turn.text, describe_question(slots, st.asked), describe(slots)),
                                           lambda r: f"{len(r.products) if r else 0} product(s) read")
        changed = apply_reading(slots, reading, st.asked) if reading else False
        finished = finished or bool(reading and reading.finished)

        if finished:
            if not slots:                                          # "that's all" before any product: ask for one
                st.asked = {"slot": None, "field": "name"}
                await self._ask(ctx, turn, st, MSG_NEED_ONE)
                return
            incomplete = [x["product_name"] or "an unnamed product" for x in slots if not is_complete(x)]
            if incomplete and not st.exit_challenged:
                st.exit_challenged = True
                st.asked = next_question(slots, target)[1]
                s["products"] = slots
                await self._ask(ctx, turn, st, msg_missing_details(", ".join(incomplete)))
                return
            await self._done(ctx, turn, st, slots, "thats_all")
            return

        if slots and all(is_complete(x) for x in slots) and target and total_quantity(slots) >= target:
            await self._done(ctx, turn, st, slots, "completed")
            return
        if changed:
            await self._ask_next(ctx, turn, st, slots)
            return
        failures = st.count(st.failures, "products")                       # nothing usable in the reply
        if failures >= MAX_PRODUCT_ATTEMPTS:
            turn.say(MSG_TROUBLE)
            await self._done(ctx, turn, st, slots, "retry_cap")
            return
        await self._ask_next(ctx, turn, st, slots, suffix=MSG_CANCEL_HINT if failures == 3 else "")


def product_lines(slots: list[Slot]) -> list[str]:
    lines = []
    for number, slot in enumerate((x for x in slots if is_complete(x)), 1):
        line = f"• Product {number}: {slot['product_name']} | Qty: {slot['quantity']} | Condition: {slot['condition']}"
        if slot["condition"] == "wrong product" and slot["expected_product_name"]:
            line += f" | Expected: {slot['expected_product_name']}"
        lines.append(line)
    return lines


class ConfirmProducts(QuestionNode):
    """Reads the list back and asks for a real yes/no (Kore asks "please confirm" but never reads an answer)."""

    def __init__(self, deps: Deps, next_id: str, no_id: str):
        super().__init__(PD_CONFIRM_PRODUCTS, deps, next_id)
        self._no = no_id

    def _prompt(self, slots: list[Slot]) -> list[str]:
        left_out = sum(1 for x in slots if not is_complete(x))
        lines = ["Here are the return details I have:", *product_lines(slots)]
        if left_out:
            lines.append(f"({left_out} item(s) were left incomplete and are not listed above.)")
        return ["\n".join(lines), MSG_CONFIRM_QUESTION]

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        st, slots = PurchaseDetailsState.load(turn.session), normalised(turn.session.get("products"))
        if not any(is_complete(x) for x in slots):
            await self._continue(ctx, turn, st)                  # nothing to confirm: the save step records "nothing submittable"
            return
        if not turn.resuming:
            await self._ask(ctx, turn, st, *self._prompt(slots), suggest=["Yes", "No"])
            return
        turn.resuming = False
        if is_cancel_request(turn.text):
            await self._cancel(ctx, turn, st)
            return
        answer = read_yes_no(turn.text)
        if answer is None:
            await self._ask(ctx, turn, st, MSG_DIDNT_CATCH, *self._prompt(slots), suggest=["Yes", "No"])
            return
        if not answer:
            st.save(turn.session)
            await goto(ctx, turn, self._no)
            return
        await self._continue(ctx, turn, st)


def reset_products(turn: Turn) -> None:
    """The customer said the list is wrong: start the list again (the count stays)."""
    s = turn.session
    for key in ("products", "agentNodeExitPath", "partialReturn", "ProductsCollected", "remainingQuantity"):
        s.pop(key, None)
    for key in ("ProductsCollected", "AllProductsCaptured"):
        turn.entities.pop(key, None)
    st = PurchaseDetailsState.load(s)
    st.asked, st.exit_challenged = None, False
    st.failures.pop("products", None)
    st.save(s)


# Kore's SavingAgentData: 1 = used or damaged, 2 = new or wrong product
CONDITION_CODE = {"new": 2, "wrong product": 2, "used": 1, "damaged": 1}


def save_products(turn: Turn) -> None:
    """PC_HomeDelivery_Script_SavingAgentData: the list the ticket and the document request are built from."""
    s = turn.session
    slots = [x for x in normalised(s.get("products")) if x["product_name"]]
    if len(slots) != len(normalised(s.get("products"))):
        s["productDataAnomaly"] = True                            # a slot with no name was dropped
    s["products"] = slots
    complete = [x for x in slots if is_complete(x)]
    to_return = [{"productName": x["product_name"], "quantity": int(x["quantity"]),
                  "productCondition": CONDITION_CODE[x["condition"]], "expectedProductName": x["expected_product_name"] or "",
                  "condition": x["condition"]} for x in complete]
    summary = "\n".join(product_lines(slots)) + "\n" if to_return else "No products captured."
    incomplete = len(slots) - len(complete)
    if incomplete:
        summary += f"({incomplete} item(s) were left incomplete and are not listed above.)\n"
    expected = target_count(turn) or 0
    collected = sum(x["quantity"] for x in to_return)
    s["all_products_summary"] = summary
    s["collectedUnits"] = collected
    s["countMismatch"] = bool(expected and collected != expected)
    s["productsToReturn"] = to_return
    s["productsToReturnJSON"] = json.dumps(to_return)
    s["collectionOutcome"] = ("nothing_submittable" if not to_return else
                              "partial_review" if (incomplete or s["countMismatch"] or s.get("agentNodeExitPath") == "retry_cap")
                              else "clean")
    s["returnDetailsCompleted"] = bool(s.get("countryCompleted") and s.get("productCountCompleted"))
    s.pop("agentNodeExitPath", None)
    log.info("products saved: %d complete, %d incomplete, outcome=%s", len(complete), incomplete, s["collectionOutcome"])


# ============================================================================================
# Wiring
# ============================================================================================
class ProductNodes:
    def __init__(self, start: Executor, last: Executor, pause_nodes: list[Executor], outputs: list[Executor],
                 edges: list[tuple[Executor, Executor]]):
        self.start, self.last, self.pause_nodes, self.outputs, self.edges = start, last, pause_nodes, outputs, edges


def build_product_nodes(deps: Deps, next_id: str, cancel: Executor) -> ProductNodes:
    count = ProductCountNode(deps, PD_ASK_PRODUCTS)
    details = ProductDetailsNode(deps, PD_CONFIRM_PRODUCTS)
    confirm = ConfirmProducts(deps, PD_SAVE_PRODUCTS, PD_RESET_PRODUCTS)
    reset = ScriptNode(PD_RESET_PRODUCTS, reset_products, PD_ASK_PRODUCTS)
    save = ScriptNode(PD_SAVE_PRODUCTS, save_products, next_id)
    pauses = [count, details, confirm]
    edges = [(count, details), (details, confirm), (confirm, save), (confirm, reset), (reset, details)]
    edges += [(node, cancel) for node in pauses]
    return ProductNodes(start=count, last=save, pause_nodes=pauses, outputs=pauses, edges=edges)


def connect_product_nodes(builder: Any, nodes: ProductNodes) -> None:
    for source, target in nodes.edges:
        connect(builder, source, target)
