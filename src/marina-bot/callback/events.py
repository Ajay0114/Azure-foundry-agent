"""The events OneSpaWorld's document service sends, and what each one means for the Zendesk ticket.

Ports the routing of the Kore "CallBackAgent" (DocumentEventRouter): there a model read the JSON and picked one of eight tools;
here the routing is a table, because it never needs judgement.

An event looks like this (all of these fields are sent):

  {"id": 1234, "eventType": "DocumentCreated", "requestType": "products-return", "scope": "...", "requestId": 55,
   "requestReferenceId": "8147", "documentId": 77, "createdAt": "2026-10-12T10:00:00Z", "metadata": {...}}

`requestReferenceId` is the Zendesk ticket id we gave the document API when the return was submitted. `documentId` is sent
for DocumentCreated only.

  DocumentCreated             fetch the document, attach it to the ticket, tag it
  DocumentsRequestCreated     tag the ticket and add an internal comment
  DocumentsSearchInitiated    "
  DocumentsSearchStopped      "
  DocumentsSearchDelegated    tag, comment, and put the vessel's SPA manager e-mail in the ticket
  DocumentDeleted             tag the ticket and add an internal comment
  error                       "
  unknown (or anything else)  "
"""

import json
import re
from dataclasses import dataclass
from typing import Any

CREATED, DELEGATED, TAG_ONLY = "created", "delegated", "tag_only"

KINDS = {
    "documentcreated": CREATED,
    "documentssearchdelegated": DELEGATED,
    "documentsrequestcreated": TAG_ONLY,
    "documentssearchinitiated": TAG_ONLY,
    "documentssearchstopped": TAG_ONLY,
    "documentdeleted": TAG_ONLY,
    "error": TAG_ONLY,
    "unknown": TAG_ONLY,
}


class EventError(ValueError):
    """The message is not a usable event. Not worth retrying: the sender has to fix it."""


@dataclass(frozen=True)
class Event:
    id: str
    event_type: str            # as sent
    request_type: str          # as sent
    scope: str
    request_id: str
    ticket_id: int
    created_at: str
    document_id: int | None = None

    @property
    def kind(self) -> str:
        return KINDS.get(self.event_type.lower().strip(), TAG_ONLY)      # an event we do not know is tagged like "unknown"

    @property
    def request_name(self) -> str:
        """The request type as it appears in tags and comments (Kore: lower case, trimmed)."""
        return self.request_type.lower().strip()

    def as_payload(self) -> dict[str, Any]:
        """The event as the redrive queue expects it (Kore: EnqueueFailedEvent)."""
        payload: dict[str, Any] = {"id": self.id, "eventType": self.event_type, "requestType": self.request_type,
                                   "scope": self.scope, "requestId": self.request_id,
                                   "requestReferenceId": str(self.ticket_id), "createdAt": self.created_at}
        if self.document_id is not None:
            payload["documentId"] = self.document_id
        return payload


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def parse_event(text: str) -> Event:
    """The event inside a message. Accepts the JSON object, or a JSON string holding it (some senders encode twice)."""
    try:
        data: Any = json.loads(text)
        if isinstance(data, str):
            data = json.loads(data)
    except (TypeError, ValueError) as exc:
        raise EventError("The message is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise EventError("The message is not a JSON object.")
    ticket = _text(data.get("requestReferenceId"))
    if not re.fullmatch(r"\d{1,12}", ticket):
        raise EventError("requestReferenceId must be the numeric Zendesk ticket id.")
    event_type = _text(data.get("eventType"))
    if not event_type:
        raise EventError("eventType is missing.")
    document_id = None
    if _text(data.get("documentId")):
        if not re.fullmatch(r"\d{1,12}", _text(data.get("documentId"))):
            raise EventError("documentId must be a number.")
        document_id = int(_text(data.get("documentId")))
    event = Event(id=_text(data.get("id")), event_type=event_type, request_type=_text(data.get("requestType")),
                  scope=_text(data.get("scope")), request_id=_text(data.get("requestId")), ticket_id=int(ticket),
                  created_at=_text(data.get("createdAt")), document_id=document_id)
    if event.kind == CREATED and (document_id is None or not event.request_name):
        raise EventError("A DocumentCreated event needs documentId and requestType.")
    return event


def safe_tag(text: str) -> str:
    """A Zendesk tag: lower case, with anything Zendesk would reject (spaces, symbols) turned into "_"."""
    return re.sub(r"[^a-z0-9_\-]+", "_", text.lower().strip())


def tag_for(event: Event) -> str:
    """`<requestType>_<eventType>`, for example products-return_documentssearchinitiated."""
    return safe_tag(f"{event.request_name}_{event.event_type}")
