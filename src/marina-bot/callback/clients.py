"""The two Azure Functions the callback calls besides Zendesk.

  DocumentFunction  POST {CALLBACK_UPLOAD_API_URL}/api/upload  {"requestType", "documentId"} -> {"token": "..."}
                    NOT the function that scans customers' files (ATTACHMENT_API_URL): that one takes file links. This one
                    takes a document id, downloads the generated document from the document service and stages it in
                    Zendesk; the token is what a ticket comment needs to attach it. (Kore: AzureGetUploadToken.)
  RedriveQueue      POST {REDRIVE_API_URL}/api/enqueue        the event as JSON
                    Puts an event we could not process on the retry queue; a separate redrive worker replays it later.
                    (Kore: EnqueueFailedEvent.)

Both authenticate with a function key sent as the `x-functions-key` header (never in the URL). Environment variables, never
committed:  CALLBACK_UPLOAD_API_URL, CALLBACK_UPLOAD_API_KEY, REDRIVE_API_URL, REDRIVE_API_KEY.
Errors carry the HTTP status only, never a response body or the key.
"""

import os
from typing import Any, Protocol

import httpx


class CallbackError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class DocumentTokens(Protocol):
    async def token_for(self, request_type: str, document_id: int) -> str: ...


class RetryQueue(Protocol):
    async def enqueue(self, event: dict[str, Any]) -> None: ...


def _settings(url_var: str, key_var: str, path: str) -> tuple[str, str]:
    """(the function app's address, its key). The address may be given with or without the endpoint path on the end."""
    url, key = os.environ.get(url_var, "").strip(), os.environ.get(key_var, "").strip()
    missing = [name for name, value in ((url_var, url), (key_var, key)) if not value]
    if missing:
        raise RuntimeError(f"Settings are missing: {', '.join(missing)}.")
    if not url.startswith("https://"):
        raise RuntimeError(f"{url_var} must start with https://")
    return url.rstrip("/").removesuffix(path), key


async def _post(base: str, path: str, key: str, body: dict[str, Any], timeout: float) -> Any:
    try:
        async with httpx.AsyncClient(base_url=base, timeout=timeout) as client:
            response = await client.post(path, json=body, headers={"x-functions-key": key})
    except httpx.HTTPError as exc:
        raise CallbackError(f"POST {path} failed: {type(exc).__name__}") from exc
    if response.status_code >= 300:
        raise CallbackError(f"POST {path} returned HTTP {response.status_code}", response.status_code)
    try:
        return response.json() if response.content else None
    except ValueError:
        return None


class DocumentFunction:
    def __init__(self, base_url: str, key: str, timeout: float = 60.0):
        self._base, self._key, self._timeout = base_url, key, timeout

    @classmethod
    def from_env(cls) -> "DocumentFunction":
        return cls(*_settings("CALLBACK_UPLOAD_API_URL", "CALLBACK_UPLOAD_API_KEY", "/api/upload"))

    async def token_for(self, request_type: str, document_id: int) -> str:
        body = await _post(self._base, "/api/upload", self._key,
                           {"requestType": request_type, "documentId": str(document_id)}, self._timeout)
        token = body.get("token") if isinstance(body, dict) else None
        if not isinstance(token, str) or not token:
            raise CallbackError("the upload function returned no token")
        return token


class RedriveQueue:
    def __init__(self, base_url: str, key: str, timeout: float = 20.0):
        self._base, self._key, self._timeout = base_url, key, timeout

    @classmethod
    def from_env(cls) -> "RedriveQueue":
        return cls(*_settings("REDRIVE_API_URL", "REDRIVE_API_KEY", "/api/enqueue"))

    async def enqueue(self, event: dict[str, Any]) -> None:
        await _post(self._base, "/api/enqueue", self._key, event, self._timeout)
