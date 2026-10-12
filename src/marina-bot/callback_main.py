"""The document-event callback as a Foundry hosted agent (Kore: the CallBackAgent app).

OneSpaWorld's document service sends an event for each step of a document request. Marina asked for the documents when
the return ticket was created; this agent receives the events and updates that ticket. It is a second hosted agent beside
`marina-bot` (azure.yaml service `marina-callback`), running this file instead of main.py, so the chat bot and the callback
have separate endpoints, identities and logs, and nothing a customer types can reach this code.

The sender POSTs to the agent's Responses endpoint with the event JSON as the input text:

    POST <project endpoint>/agents/marina-callback/endpoint/protocols/openai/responses?api-version=v1
    Authorization: Bearer <Entra token, scope https://ai.azure.com/.default>
    {"input": "<the event as a JSON string>"}

and gets back at once one line of JSON as the output text, an acknowledgement only:
    {"status": "accepted", "message": "Event received and is being processed", "eventId": "2221", "ticketId": 8147}
The work then happens after the answer has gone (as with Kore's "202 processing"). Its outcome is in the log (success, duplicate,
queued_for_retry when it failed twice and went to the redrive queue, failed); the sender is not sent it. A message that is not
a usable event gets {"status": "rejected", "error": "..."} instead, so the sender can fix it. There is no model in this agent.

CALLBACK_WAIT_FOR_RESULT=true makes it work first and answer with the outcome instead: for testing from Postman.
"""

import asyncio
import json
import logging
import os
from typing import Never

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler
from agent_framework_foundry_hosting import HostedResponseRequest, ResponsesHostServer, WorkflowTurn
from dotenv import load_dotenv

try:
    from agent_framework_foundry_hosting import CheckpointStoreProvider
except ImportError:  # not re-exported in this release
    from agent_framework_foundry_hosting._state_store import CheckpointStoreProvider

from callback.clients import DocumentFunction, RedriveQueue
from callback.events import EventError, parse_event
from callback.handler import CallbackSettings, EventHandler
from models import TurnInput
from shared.osw import OswClient
from shared.state_store import make_state_store
from shared.zendesk import ZendeskClient

load_dotenv()
log = logging.getLogger(__name__)

ALLOWED_CHECKPOINT_TYPES = ["models:TurnInput"]


class EventEntry(Executor):
    """One request = one event: parse it, apply it, answer with the outcome as JSON."""

    def __init__(self, events: EventHandler, wait: bool, background: set[asyncio.Task]):
        super().__init__(id="event_entry")
        self._events, self._wait, self._background = events, wait, background

    async def _apply(self, event) -> dict:
        try:
            outcome = await self._events.handle(event)
        except Exception as exc:                      # noqa: BLE001  (handle() should not raise; never let a task die unseen)
            log.error("event %s crashed: %s", event.id, type(exc).__name__)
            return {"status": "failed"}
        log.info("event %s (%s) ticket %s -> %s", event.id, event.event_type, event.ticket_id, outcome["status"])
        return outcome

    @handler
    async def run(self, message: TurnInput, ctx: WorkflowContext[Never, str]) -> None:
        try:
            event = parse_event(message.text)
        except EventError as exc:
            log.warning("event rejected: %s", exc)
            await ctx.yield_output(json.dumps({"status": "rejected", "error": str(exc)}))
            return
        if self._wait:
            await ctx.yield_output(json.dumps({**await self._apply(event), "eventId": event.id}))
            return
        task = asyncio.create_task(self._apply(event))
        self._background.add(task)                    # keep a reference: a task nobody holds can be collected mid-run
        task.add_done_callback(self._background.discard)
        await ctx.yield_output(json.dumps({"status": "accepted", "message": "Event received and is being processed",
                                           "eventId": event.id, "ticketId": event.ticket_id}))


def build_workflow(events: EventHandler, wait: bool = False, background: set[asyncio.Task] | None = None):
    entry = EventEntry(events, wait, background if background is not None else set())
    return WorkflowBuilder(name="marina-callback", start_executor=entry, output_from=[entry]).build()


async def parse_response(request: HostedResponseRequest) -> WorkflowTurn[TurnInput]:
    return WorkflowTurn(input=TurnInput(text=await request.get_input_text() or ""))


def make_handler() -> EventHandler:
    try:
        queue = RedriveQueue.from_env()
    except RuntimeError as exc:                       # the retry queue is optional: without it a failed event is only reported
        log.warning("%s Failed events will NOT be queued for retry.", exc)
        queue = None
    return EventHandler(ZendeskClient.from_env(), DocumentFunction.from_env(), queue, OswClient.from_env(),
                        make_state_store(), CallbackSettings.from_env())


def main():
    events = make_handler()
    wait = os.environ.get("CALLBACK_WAIT_FOR_RESULT", "").strip().lower() in ("1", "true", "yes", "on")
    background: set[asyncio.Task] = set()
    checkpoints = CheckpointStoreProvider(allowed_checkpoint_types=ALLOWED_CHECKPOINT_TYPES)
    ResponsesHostServer(workflow=lambda request: build_workflow(events, wait, background), parse_response=parse_response,
                        checkpoint_store_provider=checkpoints).run()


if __name__ == "__main__":
    main()
