"""Zendesk: create the return ticket and add the private conversation note.

Endpoints (from the Kore service nodes PC_HomeDelivery_Service_CreateTicket / _ConversationPrivateNote):

  POST {base}/api/v2/tickets.json                 create a ticket
  PUT  {base}/api/v2/tickets/{id}.json            add a private (internal) comment
  GET  {base}/api/v2/tickets.json?external_id=    find a ticket this bot already created (duplicate guard)

Configuration (environment variables; NEVER commit values; Kore called these the env.Zendesk* settings):

  ZENDESK_BASE_URL               https://<subdomain>.zendesk.com
  ZENDESK_AUTHORIZATION          the value after "Basic " (base64 of "email/token:api_token"), as Kore stored it.
                                 Alternatively set ZENDESK_EMAIL and ZENDESK_API_TOKEN and it is built for you.
  ZENDESK_FORM_ID, ZENDESK_BRAND_ID, ZENDESK_RETURN_GROUP_ID
  ZENDESK_FIELD_INQUIRY_TYPE, ZENDESK_FIELD_CATEGORY, ZENDESK_FIELD_PRODUCT_REASON, ZENDESK_FIELD_RETURN_STATUS,
  ZENDESK_FIELD_CREATED_BY, ZENDESK_FIELD_CRUISE_LINE, ZENDESK_FIELD_CRUISE_SHIP, ZENDESK_FIELD_PRIORITY,
  ZENDESK_FIELD_SAIL_DATE        ids of the custom ticket fields
  ZENDESK_TAGS                   optional, comma separated. Default kore_ai,tag_website (what Kore sent), so Zendesk
                                 triggers that key on those tags keep working.

A POST is never retried automatically (a timeout does not tell us the ticket was not created); `find_by_external_id`
lets the dialog check before it tries again.
"""

import base64
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

log = logging.getLogger(__name__)

DEFAULT_TAGS = ("kore_ai", "tag_website")
FIELD_ENV = {
    "inquiry_type": "ZENDESK_FIELD_INQUIRY_TYPE", "category": "ZENDESK_FIELD_CATEGORY",
    "product_reason": "ZENDESK_FIELD_PRODUCT_REASON", "return_status": "ZENDESK_FIELD_RETURN_STATUS",
    "created_by": "ZENDESK_FIELD_CREATED_BY", "cruise_line": "ZENDESK_FIELD_CRUISE_LINE",
    "cruise_ship": "ZENDESK_FIELD_CRUISE_SHIP", "priority": "ZENDESK_FIELD_PRIORITY",
    "sail_date": "ZENDESK_FIELD_SAIL_DATE",
}


class ZendeskError(Exception):
    """A Zendesk call failed. Carries the status code, never the response body (it can echo customer details)."""

    def __init__(self, message: str, status: int | None = None, timed_out: bool = False):
        super().__init__(message)
        self.status, self.timed_out = status, timed_out


def zendesk_id(value: str) -> int | str:
    """Zendesk accepts numeric ids as numbers; keep anything else as given."""
    return int(value) if value.strip().isdigit() else value.strip()


@dataclass(frozen=True)
class TicketSettings:
    """The non-secret ids the ticket payload needs."""
    form_id: int | str
    brand_id: int | str
    group_id: int | str
    field_ids: dict[str, int | str]
    tags: tuple[str, ...] = DEFAULT_TAGS


@dataclass(frozen=True)
class ZendeskConfig:
    base_url: str
    authorization: str = field(default="", repr=False)
    ticket: TicketSettings | None = None
    timeout: float = 20.0

    def __repr__(self) -> str:                      # never print the credential
        return f"ZendeskConfig(base_url={self.base_url!r}, authorization='***')"

    @classmethod
    def from_env(cls) -> "ZendeskConfig":
        env = {k: os.environ.get(k, "").strip() for k in
               ["ZENDESK_BASE_URL", "ZENDESK_FORM_ID", "ZENDESK_BRAND_ID", "ZENDESK_RETURN_GROUP_ID", *FIELD_ENV.values()]}
        authorization = os.environ.get("ZENDESK_AUTHORIZATION", "").strip()
        email, token = os.environ.get("ZENDESK_EMAIL", "").strip(), os.environ.get("ZENDESK_API_TOKEN", "").strip()
        if not authorization and email and token:
            authorization = base64.b64encode(f"{email}/token:{token}".encode()).decode()
        missing = [k for k, v in env.items() if not v] + ([] if authorization else ["ZENDESK_AUTHORIZATION"])
        if missing:
            raise RuntimeError(f"Zendesk settings are missing: {', '.join(missing)}. Set them in .env.")
        base_url = env["ZENDESK_BASE_URL"].rstrip("/")
        if not base_url.startswith("https://"):
            raise RuntimeError("ZENDESK_BASE_URL must start with https://")
        tags = tuple(t.strip() for t in os.environ.get("ZENDESK_TAGS", "").split(",") if t.strip()) or DEFAULT_TAGS
        ticket = TicketSettings(
            form_id=zendesk_id(env["ZENDESK_FORM_ID"]), brand_id=zendesk_id(env["ZENDESK_BRAND_ID"]),
            group_id=zendesk_id(env["ZENDESK_RETURN_GROUP_ID"]),
            field_ids={name: zendesk_id(env[var]) for name, var in FIELD_ENV.items()}, tags=tags)
        return cls(base_url=base_url, authorization=authorization, ticket=ticket)


class ZendeskApi(Protocol):
    """What the dialogs depend on (the tests supply a fake)."""

    ticket_settings: TicketSettings

    async def create_ticket(self, payload: dict[str, Any]) -> int: ...
    async def add_private_note(self, ticket_id: int, html_body: str, uploads: list[str] | None = None) -> None: ...
    async def find_by_external_id(self, external_id: str) -> int | None: ...


class ZendeskClient:
    def __init__(self, config: ZendeskConfig):
        assert config.ticket is not None
        self._cfg = config
        self.ticket_settings = config.ticket

    @classmethod
    def from_env(cls) -> "ZendeskClient":
        return cls(ZendeskConfig.from_env())

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = {"Authorization": f"Basic {self._cfg.authorization}", "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(base_url=self._cfg.base_url, timeout=self._cfg.timeout) as client:
                response = await client.request(method, path, headers=headers, **kwargs)
        except httpx.TimeoutException as exc:
            raise ZendeskError(f"Zendesk {method} {path} timed out", timed_out=True) from exc
        except httpx.HTTPError as exc:
            raise ZendeskError(f"Zendesk {method} {path} failed: {type(exc).__name__}") from exc
        if response.status_code >= 300:
            raise ZendeskError(f"Zendesk {method} {path} returned HTTP {response.status_code}", response.status_code)
        return response.json() if response.content else None

    async def create_ticket(self, payload: dict[str, Any]) -> int:
        body = await self._request("POST", "/api/v2/tickets.json", json=payload)
        try:
            return int(body["ticket"]["id"])
        except (TypeError, KeyError, ValueError) as exc:
            raise ZendeskError("Zendesk created a ticket but the reply had no ticket id") from exc

    async def add_private_note(self, ticket_id: int, html_body: str, uploads: list[str] | None = None) -> None:
        comment: dict[str, Any] = {"html_body": html_body, "public": False}
        if uploads:
            comment["uploads"] = uploads                      # tokens from the attachment service
        await self._request("PUT", f"/api/v2/tickets/{int(ticket_id)}.json", json={"ticket": {"comment": comment}})

    async def find_by_external_id(self, external_id: str) -> int | None:
        body = await self._request("GET", "/api/v2/tickets.json", params={"external_id": external_id})
        tickets = body.get("tickets") if isinstance(body, dict) else None
        return int(tickets[0]["id"]) if tickets else None
