"""Top-level workflow: load state -> (classify intent) -> run the active dialog -> save state -> reply.

  turn_entry --(no active dialog)--> intent_classifier --> product_return (sub-workflow) --> persist
      |                                    |                                                  ^
      +--------(active dialog)-------------+----------> fallback -----------------------------+

Each dialog is a sub-workflow wrapped in a WorkflowExecutor; adding a dialog = one more sub-workflow,
one more classifier label and two more edges.
"""

from typing import Never

from agent_framework import Executor, Workflow, WorkflowBuilder, WorkflowContext, WorkflowExecutor, handler

from dialogs.product_return.workflow import build_product_return_workflow
from models import Turn, TurnInput
from shared.deps import Deps
from shared.flow import PERSIST, PromptRunner, connect, goto
from shared.state_store import FileStateStore

PRODUCT_RETURN = "PRODUCT_RETURN"
OTHER = "OTHER"
HISTORY_LINES = 10
HISTORY_MESSAGES = 20

CLASSIFIER_PROMPT = (
    "You classify the customer's latest message for a cruise-ship spa and retail bot. "
    f"Reply with exactly one label and nothing else: {PRODUCT_RETURN} if the customer wants "
    "to return, exchange, complain about or get a refund for a purchased product (including "
    f"home delivery orders), otherwise {OTHER}.\n\nCustomer message: "
)


class TurnEntry(Executor):
    """Loads the saved dialog state for this conversation and routes the turn."""

    def __init__(self, store: FileStateStore):
        super().__init__(id="turn_entry")
        self._store = store

    @handler
    async def run(self, inp: TurnInput, ctx: WorkflowContext[Turn]) -> None:
        saved = self._store.load(inp.load_keys) or {}
        turn = Turn(text=inp.text, save_keys=inp.save_keys,
                    session=saved.get("session", {}), entities=saved.get("entities", {}))
        active = turn.session.get("active_dialog")
        await goto(ctx, turn, PRODUCT_RETURN.lower() if active == PRODUCT_RETURN else "intent_classifier")


class IntentClassifier(Executor):
    """Prompt node that picks the dialog for a new conversation topic."""

    def __init__(self, run_prompt: PromptRunner):
        super().__init__(id="intent_classifier")
        self._run = run_prompt

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn]) -> None:
        label = (await self._run(CLASSIFIER_PROMPT + turn.text)).strip().upper()
        if PRODUCT_RETURN in label:
            turn.session["active_dialog"] = PRODUCT_RETURN
            turn.session.pop("dialog_step", None)
            await goto(ctx, turn, PRODUCT_RETURN.lower())
        else:
            await goto(ctx, turn, "fallback")


class Fallback(Executor):
    def __init__(self):
        super().__init__(id="fallback")

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn]) -> None:
        turn.say("Sorry, I can only help with product returns right now.")
        await goto(ctx, turn, PERSIST)


class Persist(Executor):
    """Records the exchange, saves the state, and returns the bot's reply."""

    def __init__(self, store: FileStateStore):
        super().__init__(id=PERSIST)
        self._store = store

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Never, str]) -> None:
        reply = "\n\n".join(turn.replies) or "Sorry, something went wrong. Could you say that again?"
        lines = turn.session.get("conversationHistoryString", "").splitlines()
        lines += [f"User: {turn.text}", f"Bot: {reply}"]
        turn.session["conversationHistoryString"] = "\n".join(lines[-HISTORY_LINES:])
        # Structured history for agent nodes (Kore: Conversation_History). Appended after the agents ran,
        # so an agent receives the current turn's user text separately, never twice.
        messages = turn.session.setdefault("messages", [])
        messages += [{"role": "user", "content": turn.text}, {"role": "assistant", "content": reply}]
        turn.session["messages"] = messages[-HISTORY_MESSAGES:]
        self._store.save(turn.save_keys, {"session": turn.session, "entities": turn.entities})
        await ctx.yield_output(reply)


def build_orchestrator(deps: Deps, store: FileStateStore) -> Workflow:
    entry = TurnEntry(store)
    classifier = IntentClassifier(deps.run_prompt)
    product_return = WorkflowExecutor(build_product_return_workflow(deps), id=PRODUCT_RETURN.lower())
    fallback = Fallback()
    persist = Persist(store)

    builder = WorkflowBuilder(name="marina-bot", start_executor=entry, output_from=[persist])
    for src, dst in [(entry, classifier), (entry, product_return), (classifier, product_return),
                     (classifier, fallback), (product_return, persist), (fallback, persist)]:
        connect(builder, src, dst)
    return builder.build()
