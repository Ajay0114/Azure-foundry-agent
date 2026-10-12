"""Building blocks that turn Kore node types into Agent Framework executors.

Routing convention: every executor sets `turn.route` to the id of the executor that should run
next, and every edge in the graph is gated on `route == <target id>` (see `connect`). The graph
therefore documents the allowed Kore transitions, while each node's Python decides which one to take.

Pausing convention: a node that needs the user's answer calls `pause`, which stores its own id in
session["dialog_step"] and ends the turn. On the next turn the dialog's entry node routes straight
back to that node with `turn.resuming = True` and `turn.text` holding the answer.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from agent_framework import Executor, WorkflowContext, handler

from models import Turn
from shared import trace

PERSIST = "persist"

PromptRunner = Callable[[str], Awaitable[str]]


def connect(builder, source: Executor, target: Executor):
    """Add an edge that only fires when the turn is routed to `target`."""
    target_id = target.id
    return builder.add_edge(source, target, condition=lambda t: isinstance(t, Turn) and t.route == target_id)


async def goto(ctx: Any, turn: Turn, target_id: str) -> None:
    trace.event(turn, "transition", turn.route or "turn_entry", to=target_id)       # the node that just ran -> the next one
    turn.route = target_id
    await ctx.send_message(turn)


async def pause(ctx: Any, turn: Turn, step_id: str) -> None:
    """End the turn; the user's next message resumes at `step_id`."""
    trace.event(turn, "wait", step_id, "waiting for user input")
    turn.session["dialog_step"] = step_id
    turn.route = PERSIST
    await ctx.yield_output(turn)


async def finish(ctx: Any, turn: Turn) -> None:
    """End the turn and the dialog; the next message is classified from scratch."""
    trace.event(turn, "end", turn.route or "dialog", "dialog finished")
    turn.session.pop("dialog_step", None)
    turn.session["active_dialog"] = None
    turn.route = PERSIST
    await ctx.yield_output(turn)


class ScriptNode(Executor):
    """Kore script node: plain Python over the turn, then continue."""

    def __init__(self, id: str, fn: Callable[[Turn], None], next_id: str):
        super().__init__(id=id)
        self._fn, self._next = fn, next_id

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        self._fn(turn)
        await goto(ctx, turn, self._next)


class MessageNode(Executor):
    """Kore message node: say something, then continue (shown together with the next question)."""

    def __init__(self, id: str, text: Callable[[Turn], str], next_id: str):
        super().__init__(id=id)
        self._text, self._next = text, next_id

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        turn.say(self._text(turn))
        await goto(ctx, turn, self._next)


class PromptNode(Executor):
    """Kore generativeai node: one LLM call; output stored under session['nodeOutputs'][name]."""

    def __init__(self, id: str, run_prompt: PromptRunner, build_prompt: Callable[[Turn], str],
                 output_name: str, next_id: str):
        super().__init__(id=id)
        self._run, self._build, self._name, self._next = run_prompt, build_prompt, output_name, next_id

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        text = await trace.call(turn, "llm", self._name, self._run(self._build(turn)), lambda out: f"{len(out)} characters returned")
        turn.session.setdefault("nodeOutputs", {})[self._name] = text
        await goto(ctx, turn, self._next)


class SlotNode(Executor):
    """Kore entity node: ask for a value, validate the reply, retry with the error message.

    Skipped when the entity is already collected (Kore's behaviour when context already has it).
    """

    def __init__(self, id: str, slot: str, prompt: Callable[[Turn], str], error: str,
                 parse: Callable[[str], Any], next_id: str):
        super().__init__(id=id)
        self._slot, self._prompt, self._error, self._parse, self._next = slot, prompt, error, parse, next_id

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        if self._slot in turn.entities:
            await goto(ctx, turn, self._next)
            return
        if not turn.resuming:
            turn.say(self._prompt(turn))
            await pause(ctx, turn, self.id)
            return
        value = self._parse(turn.text)
        if value is None:
            turn.say(self._error)
            await pause(ctx, turn, self.id)
            return
        turn.entities[self._slot] = value
        turn.resuming = False
        await goto(ctx, turn, self._next)


class ConfirmNode(Executor):
    """Kore dialogAct (yes/no) node."""

    def __init__(self, id: str, prompt: Callable[[Turn], str], yes_id: str, no_id: str,
                 parse_yes_no: Callable[[str], bool | None]):
        super().__init__(id=id)
        self._prompt, self._yes, self._no, self._parse = prompt, yes_id, no_id, parse_yes_no

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        if not turn.resuming:
            turn.say(self._prompt(turn))
            turn.suggest("Yes", "No")
            await pause(ctx, turn, self.id)
            return
        answer = self._parse(turn.text)
        if answer is None:
            turn.say("Sorry, I didn't catch that. " + self._prompt(turn))
            turn.suggest("Yes", "No")
            await pause(ctx, turn, self.id)
            return
        turn.resuming = False
        await goto(ctx, turn, self._yes if answer else self._no)
