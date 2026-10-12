"""Applying one document event to its Zendesk ticket (Kore: the eight Handle... tools and the retry rules of the router).

What a customer-facing run never sees: this runs when OneSpaWorld's document service reports progress on a document we
requested when the return ticket was created, and it only touches that ticket.

Kore's rules, kept:
  * every tool is tried twice; if both attempts fail the event goes to the redrive queue and is reported as queued;
  * a tag is `<requestType>_<eventType>` and an internal comment says "Automated update: <eventType> for <requestType>.";
  * DocumentCreated attaches the document and tags the ticket `<requestType>_<documentId>`.
Differences, on purpose:
  * no model: the event type picks the handler;
  * an event already processed successfully (same event id) is acknowledged and skipped, so a re-delivery does not add a
    second comment;
  * all text that came in the event is HTML-escaped before it goes into a comment;
  * the SPA manager's e-mail comes from the vessel record. Kore's QA tool overwrote it with a fixed test address; set
    CALLBACK_SPA_MANAGER_EMAIL_OVERRIDE to do the same in a test environment.

Settings: ZENDESK_FIELD_SPA_MANAGER_EMAIL (id of the ticket field that holds the manager's e-mail), optional
CALLBACK_SPA_MANAGER_EMAIL_OVERRIDE.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Protocol

from callback.clients import CallbackError, DocumentTokens, RetryQueue
from callback.events import CREATED, DELEGATED, Event, safe_tag, tag_for
from shared.htmltext import esc
from shared.osw import OswApi
from shared.state_store import StateStore
from shared.zendesk import zendesk_id

log = logging.getLogger(__name__)

ATTEMPTS = 2
SUCCESS, QUEUED, FAILED, DUPLICATE = "success", "queued_for_retry", "failed", "duplicate"


class TicketApi(Protocol):
    ticket_settings: Any

    async def add_tags(self, ticket_id: int, tags: list[str]) -> None: ...
    async def update_ticket(self, ticket_id: int, html_body: str, uploads: list[str] | None = None,
                            custom_fields: list[dict[str, Any]] | None = None) -> Any: ...
    async def get_ticket(self, ticket_id: int) -> dict[str, Any]: ...
    async def create_or_update_user(self, email: str, name: str) -> None: ...


@dataclass(frozen=True)
class CallbackSettings:
    manager_email_field: int | str | None = None
    manager_email_override: str = ""

    @classmethod
    def from_env(cls) -> "CallbackSettings":
        field_id = os.environ.get("ZENDESK_FIELD_SPA_MANAGER_EMAIL", "").strip()
        return cls(zendesk_id(field_id) if field_id else None, os.environ.get("CALLBACK_SPA_MANAGER_EMAIL_OVERRIDE", "").strip())


def _comment(event: Event) -> str:
    return f"Automated update: {esc(event.event_type.lower().strip())} for {esc(event.request_name)}."


def _attachment_url(reply: Any) -> str | None:
    """The link to the file Zendesk attached (Kore's tool returned it as downloadUrl)."""
    try:
        return reply["audit"]["events"][0]["attachments"][0]["url"]
    except (TypeError, KeyError, IndexError):
        return None


class EventHandler:
    def __init__(self, zendesk: TicketApi, documents: DocumentTokens, queue: RetryQueue | None, osw: OswApi | Any,
                 store: StateStore, settings: CallbackSettings):
        self._zd, self._documents, self._queue, self._osw = zendesk, documents, queue, osw
        self._store, self._settings = store, settings
        self._in_flight: set[str] = set()                  # event ids being processed now (a re-delivery must not run twice)

    # ---- the handlers ---------------------------------------------------------------------------------------------
    async def _created(self, event: Event) -> dict[str, Any]:
        assert event.document_id is not None
        token = await self._documents.token_for(event.request_type, event.document_id)
        reply = await self._zd.update_ticket(
            event.ticket_id, f"Automated update: Processed document id {event.document_id} for {esc(event.request_name)}.",
            uploads=[token])
        await self._zd.add_tags(event.ticket_id, [safe_tag(f"{event.request_name}_{event.document_id}")])
        return {"downloadUrl": _attachment_url(reply)}

    async def _tag_only(self, event: Event) -> dict[str, Any]:
        await self._zd.add_tags(event.ticket_id, [tag_for(event)])
        await self._zd.update_ticket(event.ticket_id, _comment(event))
        return {"tagApplied": tag_for(event)}

    async def _manager_email(self, ticket: dict[str, Any]) -> tuple[str, str | None]:
        """(ship name, the SPA manager's e-mail or None) for the ticket's vessel."""
        field_id = str(self._zd.ticket_settings.field_ids["cruise_ship"])
        ship = next((str(f.get("value") or "").strip() for f in ticket.get("custom_fields") or []
                     if str(f.get("id")) == field_id), "")
        if not ship:
            raise CallbackError("the ticket has no ship name")
        email = self._settings.manager_email_override or await self._osw.vessel_manager_email(ship)
        return ship, email

    async def _delegated(self, event: Event) -> dict[str, Any]:
        ship, email = await self._manager_email(await self._zd.get_ticket(event.ticket_id))
        await self._zd.add_tags(event.ticket_id, [tag_for(event)])
        if not email:
            await self._zd.update_ticket(
                event.ticket_id, f"Automated update: No SPA Manager email address is available for vessel {esc(ship)}. "
                                 "The Manager Email field was not updated. Please verify the SPA Manager details manually.")
            return {"tagApplied": tag_for(event), "managerEmail": None}
        if self._settings.manager_email_field is None:
            raise CallbackError("ZENDESK_FIELD_SPA_MANAGER_EMAIL is not set")
        await self._zd.create_or_update_user(email, email.split("@")[0])
        await self._zd.update_ticket(event.ticket_id, _comment(event),
                                     custom_fields=[{"id": self._settings.manager_email_field, "value": email}])
        return {"tagApplied": tag_for(event), "managerEmail": email}

    async def _dispatch(self, event: Event) -> dict[str, Any]:
        if event.kind == CREATED:
            return await self._created(event)
        if event.kind == DELEGATED:
            return await self._delegated(event)
        return await self._tag_only(event)

    # ---- the run: duplicate check, two attempts, the retry queue ---------------------------------------------------
    def _key(self, event: Event) -> str | None:
        return f"callback-event-{event.id}" if event.id else None

    async def handle(self, event: Event) -> dict[str, Any]:
        base = {"eventType": event.event_type, "requestType": event.request_type, "ticketId": event.ticket_id}
        key = self._key(event)
        if key and (key in self._in_flight or await self._already_done(key)):
            log.info("event %s was already processed or is being processed; skipped", event.id)
            return {"status": DUPLICATE, **base}
        if key:
            self._in_flight.add(key)
        try:
            return await self._run(event, key, base)
        finally:
            self._in_flight.discard(key)

    async def _already_done(self, key: str) -> bool:
        try:
            return bool(await asyncio.to_thread(self._store.load, [key]))
        except Exception as exc:                          # noqa: BLE001  (an unreadable store must not lose the event)
            log.warning("could not check for an earlier run of this event: %s", type(exc).__name__)
            return False

    async def _run(self, event: Event, key: str | None, base: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(1, ATTEMPTS + 1):
            try:
                result = await self._dispatch(event)
            except Exception as exc:                  # noqa: BLE001  (Zendesk, the functions, the vessel API: all the same to us)
                log.warning("event %s attempt %d failed: %s %s", event.id, attempt, type(exc).__name__, getattr(exc, "status", ""))
                continue
            if key:
                try:
                    await asyncio.to_thread(self._store.save, [key], {"status": SUCCESS, "ticketId": event.ticket_id})
                except Exception as exc:              # noqa: BLE001  (the ticket is updated; only the duplicate guard is lost)
                    log.warning("could not record event %s as processed: %s", event.id, type(exc).__name__)
            return {"status": SUCCESS, **base, **{k: v for k, v in result.items() if v is not None}}
        return {"status": await self._queue_for_later(event), **base}

    async def _queue_for_later(self, event: Event) -> str:
        if self._queue is None:
            log.error("event %s failed twice and no retry queue is configured", event.id)
            return FAILED
        try:
            await self._queue.enqueue(event.as_payload())
        except Exception as exc:                      # noqa: BLE001
            log.error("event %s failed twice and could not be queued: %s", event.id, type(exc).__name__)
            return FAILED
        log.warning("event %s failed twice; queued for retry", event.id)
        return QUEUED
