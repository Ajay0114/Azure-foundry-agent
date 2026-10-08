"""Kore "agent node" (aiassist) as an Agent Framework executor.

A Kore agent node is an LLM that can call tools and talk to the user over several turns until it
calls `end_orchestration`. Around the LLM Kore runs two scripts:

  pre_process   runs before the LLM each turn (syncs entities, initialises counters)
  post_process  runs on each tool result (parses it, updates entities, decides completion)

One chat turn runs this node once:

  pre_process -> build prompt -> LLM (may call tools in a loop) -> done?
        done      -> continue to the next node
        not done  -> say the LLM's text (its question) and pause here; the next message resumes here

The LLM call itself is behind `AgentRunner`, so tests can script it without Azure.
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from agent_framework import Agent, Executor, Message, WorkflowContext, handler, tool

from models import Turn
from shared.flow import goto, pause

log = logging.getLogger(__name__)

HISTORY_MESSAGES = 20  # how many past messages the agent sees (Kore: Noofprevioususerinputs)


@dataclass
class AgentTool:
    """One tool the LLM may call. `handler` receives the parsed arguments and returns text."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema
    handler: Callable[[dict[str, Any]], Awaitable[str]]


# (system_prompt, history, user_input, tools) -> the assistant's final text (may be empty)
AgentRunner = Callable[[str, list[dict[str, str]], str, list[AgentTool]], Awaitable[str]]


def end_orchestration_tool(on_end: Callable[[dict[str, Any]], None],
                           guard: Callable[[], str | None] | None = None) -> AgentTool:
    """Kore's built-in End Orchestration tool: the agent calls it when its task is finished.

    `guard` is checked when the tool is CALLED (not when the tool list is built), because state changes
    during a turn: e.g. a lookup that runs mid-turn makes ending legitimate. It returns a refusal message
    to hand back to the model, or None to allow the call. Kore hides the tool in the same situations.
    """

    async def run(args: dict[str, Any]) -> str:
        refusal = guard() if guard else None
        if refusal:
            return refusal
        on_end(args)
        return "Orchestration ended."

    return AgentTool(
        name="end_orchestration",
        description="End the conversation when the task is complete.",
        parameters={
            "type": "object",
            "properties": {
                "conv_status": {"type": "string", "description": "Final status, normally 'completed'."},
                "end_message": {"type": "string", "description": "Optional closing message for the user."},
            },
            "required": ["conv_status"],
        },
        handler=run,
    )


@dataclass
class AgentSpec:
    """Everything that differs between agent nodes."""
    name: str                                             # Kore node name, e.g. HD_VesselLookupAgent
    pre_process: Callable[[Turn], None]
    build_prompt: Callable[[Turn], str]
    make_tools: Callable[[Turn, Callable[[dict[str, Any]], None]], list[AgentTool]]  # (turn, on_end) -> tools
    is_complete: Callable[[Turn], bool]                   # set by the post-processor
    already_done: Callable[[Turn], bool] = lambda turn: False   # skip the LLM entirely
    reset: Callable[[Turn], None] = lambda turn: None            # hook after the node completes


class AgentNode(Executor):
    def __init__(self, id: str, spec: AgentSpec, run_agent: AgentRunner, next_id: str,
                 failure_id: str | None = None):
        super().__init__(id=id)
        self._spec, self._run_agent, self._next, self._failure = spec, run_agent, next_id, failure_id or next_id

    @handler
    async def run(self, turn: Turn, ctx: WorkflowContext[Turn, Turn]) -> None:
        spec = self._spec
        ended: dict[str, Any] = {}

        spec.pre_process(turn)
        if spec.already_done(turn):
            await self._complete(ctx, turn)
            return

        tools = spec.make_tools(turn, lambda args: ended.update(args or {"conv_status": "completed"}))
        history = list(turn.session.get("messages", []))[-HISTORY_MESSAGES:]
        try:
            text = await self._run_agent(spec.build_prompt(turn), history, turn.text, tools)
        except Exception:
            # Kore: fallbackBehavior onLLMFail = skipEvent -> carry on to the configured node.
            log.exception("%s failed; skipping to %s", spec.name, self._failure)
            turn.resuming = False
            await goto(ctx, turn, self._failure)
            return

        if ended or spec.is_complete(turn):
            closing = (ended.get("end_message") or "").strip()
            if closing:
                turn.say(closing)
            await self._complete(ctx, turn)
            return

        # Not finished: the LLM's text is its question to the user. Resume here next turn.
        turn.say(text.strip() or "Sorry, could you say that again?")
        await pause(ctx, turn, self.id)

    async def _complete(self, ctx: Any, turn: Turn) -> None:
        self._spec.reset(turn)
        turn.resuming = False
        await goto(ctx, turn, self._next)


class FoundryAgentRunner:
    """AgentRunner backed by a Foundry chat client: a fresh Agent per call, tools auto-invoked."""

    def __init__(self, client: Any):
        self._client = client

    async def __call__(self, system_prompt: str, history: list[dict[str, str]], user_input: str,
                       tools: list[AgentTool]) -> str:
        agent = Agent(client=self._client, name="agent_node", instructions=system_prompt,
                      tools=[self._to_function_tool(t) for t in tools])
        messages = [Message(role=m["role"], contents=[m["content"]]) for m in history if m.get("content")]
        messages.append(Message(role="user", contents=[user_input]))
        response = await agent.run(messages, stream=False)
        return response.text or ""

    @staticmethod
    def _to_function_tool(spec: AgentTool):
        async def call(**arguments: Any) -> str:
            return await spec.handler(arguments)

        return tool(call, name=spec.name, description=spec.description, schema=spec.parameters,
                    approval_mode="never_require")
