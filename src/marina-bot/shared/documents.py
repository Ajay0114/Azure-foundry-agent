"""The document-creation API: the products-return document and the transactions document for a ticket.

Kore: DocumentCreation_Service_Returns and PC_HomeDelivery_DocumentCreation_Service_Transcations, each with its own
OAuth profile (client credentials against Azure Entra ID; the same client, a different scope per document type).

  POST {DOCUMENT_API_URL}/cscbot/post-voyage/products-return/documents/requests     scope DOCUMENT_RETURNS_SCOPE
  POST {DOCUMENT_API_URL}/cscbot/post-voyage/transactions/documents/requests        scope DOCUMENT_TRANSACTIONS_SCOPE

Configuration (environment variables; NEVER commit values; Kore: env.Document_Creation and the two auth profiles):
  DOCUMENT_API_URL              base address
  DOCUMENT_CLIENT_ID            OAuth client id (Kore: DocumentCreationClientID)
  DOCUMENT_CLIENT_SECRET        OAuth client secret. A secret.
  DOCUMENT_RETURNS_SCOPE        api://<id>/.default (Kore: ReturnScope)
  DOCUMENT_TRANSACTIONS_SCOPE   api://<id>/.default (Kore: TransactionScope)
  DOCUMENT_TOKEN_URL            optional; defaults to OSW_TOKEN_URL (the same tenant)

An error carries the HTTP status and the API's own message (which goes into a private ticket note, as in Kore) but is
logged with the status only.
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

RETURNS_PATH = "/cscbot/post-voyage/products-return/documents/requests"
TRANSACTIONS_PATH = "/cscbot/post-voyage/transactions/documents/requests"


class DocumentError(Exception):
    """A document request failed. `detail` is the API's message (Kore's "errorDetails[0].message", errorMessage, title)."""

    def __init__(self, message: str, status: int | None = None, detail: str = ""):
        super().__init__(message)
        self.status, self.detail = status, detail


@dataclass(frozen=True)
class DocumentConfig:
    base_url: str
    token_url: str
    client_id: str
    client_secret: str = field(default="", repr=False)
    returns_scope: str = ""
    transactions_scope: str = ""
    timeout: float = 20.0

    def __repr__(self) -> str:
        return f"DocumentConfig(base_url={self.base_url!r}, client_id={self.client_id!r}, client_secret='***')"

    @classmethod
    def from_env(cls) -> "DocumentConfig":
        names = ("DOCUMENT_API_URL", "DOCUMENT_CLIENT_ID", "DOCUMENT_CLIENT_SECRET", "DOCUMENT_RETURNS_SCOPE",
                 "DOCUMENT_TRANSACTIONS_SCOPE")
        values = {k: os.environ.get(k, "").strip() for k in names}
        token_url = os.environ.get("DOCUMENT_TOKEN_URL", "").strip() or os.environ.get("OSW_TOKEN_URL", "").strip()
        missing = [k for k, v in values.items() if not v] + ([] if token_url else ["DOCUMENT_TOKEN_URL"])
        if missing:
            raise RuntimeError(f"Document API settings are missing: {', '.join(missing)}. Set them in .env.")
        if not values["DOCUMENT_API_URL"].startswith("https://"):
            raise RuntimeError("DOCUMENT_API_URL must start with https://")
        return cls(base_url=values["DOCUMENT_API_URL"].rstrip("/"), token_url=token_url,
                   client_id=values["DOCUMENT_CLIENT_ID"], client_secret=values["DOCUMENT_CLIENT_SECRET"],
                   returns_scope=values["DOCUMENT_RETURNS_SCOPE"], transactions_scope=values["DOCUMENT_TRANSACTIONS_SCOPE"])


class DocumentApi(Protocol):
    async def create_returns_document(self, payload: dict[str, Any]) -> None: ...
    async def create_transactions_document(self, payload: dict[str, Any]) -> None: ...


def error_detail(body: Any) -> str:
    """Kore's error text: errorDetails[0].message, else errorMessage, else title, else "Unknown API Error"."""
    if isinstance(body, dict):
        details = body.get("errorDetails")
        if isinstance(details, list) and details and isinstance(details[0], dict) and details[0].get("message"):
            return str(details[0]["message"])
        return str(body.get("errorMessage") or body.get("title") or "Unknown API Error")
    return "Unknown API Error"


class DocumentClient:
    def __init__(self, config: DocumentConfig):
        self._cfg = config
        self._tokens: dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def from_env(cls) -> "DocumentClient":
        return cls(DocumentConfig.from_env())

    async def _token(self, client: httpx.AsyncClient, scope: str, force: bool = False) -> str:
        async with self._lock:
            cached = self._tokens.get(scope)
            if cached and not force and time.monotonic() < cached[1]:
                return cached[0]
            response = await client.post(self._cfg.token_url, data={
                "grant_type": "client_credentials", "client_id": self._cfg.client_id,
                "client_secret": self._cfg.client_secret, "scope": scope})
            if response.status_code >= 300:
                raise DocumentError(f"document API token request returned HTTP {response.status_code}", response.status_code,
                                    "Could not get an access token")
            body = response.json()
            self._tokens[scope] = (body["access_token"], time.monotonic() + max(30, int(body.get("expires_in", 3600)) - 60))
            return self._tokens[scope][0]

    async def _post(self, path: str, scope: str, payload: dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(base_url=self._cfg.base_url, timeout=self._cfg.timeout) as client:
                for attempt in (0, 1):
                    token = await self._token(client, scope, force=attempt == 1)
                    response = await client.post(path, json=payload, headers={"Authorization": f"Bearer {token}"})
                    if response.status_code != 401 or attempt == 1:       # a 401 once: refresh the token and retry
                        break
        except httpx.HTTPError as exc:
            raise DocumentError(f"document request {path} failed: {type(exc).__name__}", None, type(exc).__name__) from exc
        if response.status_code >= 300:
            try:
                detail = error_detail(response.json())
            except ValueError:
                detail = "Unknown API Error"
            raise DocumentError(f"document request {path} returned HTTP {response.status_code}", response.status_code, detail)

    async def create_returns_document(self, payload: dict[str, Any]) -> None:
        await self._post(RETURNS_PATH, self._cfg.returns_scope, payload)

    async def create_transactions_document(self, payload: dict[str, Any]) -> None:
        await self._post(TRANSACTIONS_PATH, self._cfg.transactions_scope, payload)
