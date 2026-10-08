"""File attachments: read them from the request, scan and stage them, hand Zendesk the upload tokens.

Kore: HomeDelivery_Entity_Upload + HomeDelivery_Script_PrepareAzureData + HomeDelivery_Service_ScanUpload +
HomeDelivery_Script_HandleScanResult. The customer attaches a file in the chat; the channel supplies a URL; an Azure
Function downloads it, scans it for malware and file type, uploads it to Zendesk and returns Zendesk upload tokens.

  POST {ATTACHMENT_API_URL}/api/upload
       headers: x-functions-key, x-bot-id: marina, x-session-id, x-customer-email
       body:    {"files": [{"fileUrl": "...", "fileName": "..."}]}
       200 -> {"tokens": ["..."]}      422 -> {"blocked": [{"reason": "File type ..." | <malware reason>}]}

Configuration (environment variables; NEVER commit values):
  ATTACHMENT_API_URL   base address of the Azure Function app (Kore: AzureFileAttachmentUrl)
  ATTACHMENT_API_KEY   its function key (Kore: AzureFunctionKey). A secret.

How files reach the bot: the Responses request carries them as `input_image` / `input_file` items. Only items that
carry an https URL are used, because the scan function fetches the file itself (inline base64 data is not accepted).
The function is the one that decides which hosts it will download from.
"""

import logging
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)

MAX_FILES = 5
MAX_NAME_LENGTH = 120


class AttachmentBlocked(Exception):
    """The scan refused a file. `kind` is "filetype" or "malware"."""

    def __init__(self, kind: str):
        super().__init__(f"attachment blocked: {kind}")
        self.kind = kind


class AttachmentError(Exception):
    """The upload service failed (anything other than a block). Carries the status, never the body."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def _item_field(item: Any, name: str) -> Any:
    return item.get(name) if isinstance(item, Mapping) else getattr(item, name, None)


def clean_name(name: Any, fallback: str) -> str:
    cleaned = re.sub(r"[^\w.\- ()]", "_", str(name or "").strip().split("/")[-1].split("\\")[-1])[:MAX_NAME_LENGTH]
    return cleaned or fallback


def extract_attachments(items: Any) -> tuple[list[dict[str, str]], int]:
    """The files in one request's input items as [{"url", "name"}], plus how many could not be used.

    Works on plain dicts or objects. An item is usable only when it has an https URL; inline data or a stored-file id
    cannot be handed to the scan function, so it is counted as unusable.
    """
    files: list[dict[str, str]] = []
    unusable = 0
    for item in items or []:
        content = _item_field(item, "content")
        for part in content if isinstance(content, list) else []:
            kind = _item_field(part, "type")
            if kind not in ("input_image", "input_file"):
                continue
            url = _item_field(part, "image_url" if kind == "input_image" else "file_url")
            if isinstance(url, str) and urlparse(url).scheme == "https" and urlparse(url).netloc:
                number = len(files) + 1
                files.append({"url": url, "name": clean_name(_item_field(part, "filename") or urlparse(url).path,
                                                              f"attachment_{number}")})
            else:
                unusable += 1
    return files, unusable


@dataclass(frozen=True)
class AttachmentConfig:
    base_url: str
    function_key: str = field(default="", repr=False)
    timeout: float = 30.0

    def __repr__(self) -> str:
        return f"AttachmentConfig(base_url={self.base_url!r}, function_key='***')"

    @classmethod
    def from_env(cls) -> "AttachmentConfig":
        values = {k: os.environ.get(k, "").strip() for k in ("ATTACHMENT_API_URL", "ATTACHMENT_API_KEY")}
        missing = [k for k, v in values.items() if not v]
        if missing:
            raise RuntimeError(f"Attachment service settings are missing: {', '.join(missing)}. Set them in .env.")
        if not values["ATTACHMENT_API_URL"].startswith("https://"):
            raise RuntimeError("ATTACHMENT_API_URL must start with https://")
        return cls(base_url=values["ATTACHMENT_API_URL"].rstrip("/"), function_key=values["ATTACHMENT_API_KEY"])


class AttachmentUploader(Protocol):
    async def upload(self, files: list[dict[str, str]], session_id: str, customer_email: str) -> list[str]: ...


class AttachmentClient:
    def __init__(self, config: AttachmentConfig):
        self._cfg = config

    @classmethod
    def from_env(cls) -> "AttachmentClient":
        return cls(AttachmentConfig.from_env())

    async def upload(self, files: list[dict[str, str]], session_id: str, customer_email: str) -> list[str]:
        """Scan and stage the files; returns Zendesk upload tokens. Raises AttachmentBlocked / AttachmentError."""
        body = {"files": [{"fileUrl": f["url"], "fileName": f["name"]} for f in files[:MAX_FILES]]}
        headers = {"Content-Type": "application/json", "x-functions-key": self._cfg.function_key, "x-bot-id": "marina",
                   "x-session-id": session_id, "x-customer-email": customer_email}
        try:
            async with httpx.AsyncClient(base_url=self._cfg.base_url, timeout=self._cfg.timeout) as client:
                response = await client.post("/api/upload", json=body, headers=headers)
        except httpx.HTTPError as exc:
            raise AttachmentError(f"attachment upload failed: {type(exc).__name__}") from exc
        if response.status_code == 200:
            tokens = (response.json() or {}).get("tokens")
            return [str(t) for t in tokens] if isinstance(tokens, list) else []
        if response.status_code == 422:
            try:
                reason = str(((response.json() or {}).get("blocked") or [{}])[0].get("reason") or "")
            except (ValueError, AttributeError, IndexError):
                reason = ""
            raise AttachmentBlocked("filetype" if reason.startswith("File type") else "malware")
        raise AttachmentError(f"attachment upload returned HTTP {response.status_code}", response.status_code)
