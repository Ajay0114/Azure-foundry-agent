"""Per-conversation dialog state, persisted between chat turns.

Two stores with the same two methods (`load`, `save`); `make_state_store()` picks one from the environment:

  * BlobStateStore: one JSON blob per key in an Azure Blob Storage container, read and written with the agent's own
    identity (no keys). Use it when the bot runs in Foundry: a container restart, a new session or a second instance
    must not lose a customer's place. Selected when STATE_BLOB_ACCOUNT_URL (or STATE_BLOB_CONNECTION_STRING) is set.
        STATE_BLOB_ACCOUNT_URL         https://<storage-account>.blob.core.windows.net  (access with the identity, no key)
        STATE_BLOB_CONNECTION_STRING   optional STOPGAP: the account's connection string (access with the shared key).
                                       It is a master key for the whole storage account, so use it only for a short
                                       sandbox test, rotate the key afterwards, and prefer the role-based access above.
                                       When both are set, the connection string wins.
        STATE_BLOB_CONTAINER           container name (default "marina-state-ai-foundry"); it must already exist
    Expire old conversations with a lifecycle-management rule on the container (for example delete after 7 days).
  * FileStateStore: one JSON file per key under MARINA_STATE_DIR (default ~/marina_state). Fine for local runs; hosted
    agents keep $HOME only across idle periods of one session, so it is not enough for production.

The methods are synchronous; the workflow calls them through `asyncio.to_thread` so a slow store never blocks the loop.
Two simultaneous messages from one customer can overwrite each other in either store (last write wins).
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Protocol

log = logging.getLogger(__name__)

BLOB_TIMEOUT_SECONDS = 15


class StateStore(Protocol):
    def load(self, keys: list[str]) -> dict[str, Any] | None: ...
    def save(self, keys: list[str], data: dict[str, Any]) -> None: ...
    def save_transcript(self, path: str, csv_text: str) -> None: ...      # the conversation as a CSV file (shared/transcript.py)


def safe_key(key: str) -> str:
    """A key as it may appear in a file or blob name."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", key)


_safe = safe_key


def _default_root() -> Path:
    return Path(os.environ.get("MARINA_STATE_DIR") or Path.home() / "marina_state")


class FileStateStore:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else _default_root()

    def _path(self, key: str) -> Path:
        return self.root / (_safe(key) + ".json")

    def load(self, keys: list[str]) -> dict[str, Any] | None:
        """Return the state saved under the first key that has one."""
        for key in keys:
            path = self._path(key)
            if path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
        return None

    def save(self, keys: list[str], data: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, ensure_ascii=False)
        for key in keys:
            tmp = self._path(key).with_suffix(".tmp")
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(self._path(key))

    def save_transcript(self, path: str, csv_text: str) -> None:
        target = self.root.joinpath(*path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        tmp.write_text(csv_text, encoding="utf-8-sig")          # the BOM makes Excel read the dashes and accents correctly
        tmp.replace(target)


class BlobStateStore:
    """State in Azure Blob Storage. `container` is an azure.storage.blob ContainerClient (or anything shaped like one)."""

    def __init__(self, container: Any):
        self._container = container

    @classmethod
    def from_env(cls) -> "BlobStateStore":
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import ContainerClient

        name = os.environ.get("STATE_BLOB_CONTAINER", "").strip() or "marina-state-ai-foundry"
        connection_string = os.environ.get("STATE_BLOB_CONNECTION_STRING", "").strip()
        if connection_string:
            if "AccountName=" not in connection_string and "BlobEndpoint=" not in connection_string:
                raise RuntimeError("STATE_BLOB_CONNECTION_STRING does not look like a storage connection string")
            log.warning("conversation state: using a storage ACCOUNT KEY (STATE_BLOB_CONNECTION_STRING). This is a shared "
                        "master key: fine for a short sandbox test, replace it with role-based access and rotate the key.")
            return cls(ContainerClient.from_connection_string(connection_string, name))
        account_url = os.environ.get("STATE_BLOB_ACCOUNT_URL", "").strip().rstrip("/")
        if not account_url.startswith("https://"):
            raise RuntimeError("STATE_BLOB_ACCOUNT_URL must be https://<storage-account>.blob.core.windows.net")
        return cls(ContainerClient(account_url, name, credential=DefaultAzureCredential()))

    @staticmethod
    def _name(key: str) -> str:
        return f"state/{_safe(key)}.json"

    @property
    def _where(self) -> str:
        return f"container '{getattr(self._container, 'container_name', '?')}' of storage account '{getattr(self._container, 'account_name', '?')}'"

    def _explain(self, exc: Exception) -> Exception | None:
        """A clear error for the two causes people actually hit: no permission, and a container that does not exist."""
        from azure.core.exceptions import HttpResponseError

        if not isinstance(exc, HttpResponseError):
            return None
        if "ContainerNotFound" in str(getattr(exc, "error_code", "")):
            return RuntimeError(f"The state {self._where} does not exist. Create it, or fix STATE_BLOB_CONTAINER.")
        if getattr(exc, "status_code", None) in (401, 403):
            if os.environ.get("STATE_BLOB_CONNECTION_STRING", "").strip():
                return RuntimeError(f"Azure Storage refused the account key for the state {self._where}. The key in "
                                    "STATE_BLOB_CONNECTION_STRING may have been rotated, or the account may not allow shared-key access.")
            return RuntimeError(
                f"Azure Storage refused access to the state {self._where}. The identity running the bot (your az login "
                "locally, the agent's own identity when hosted) needs the role 'Storage Blob Data Contributor' on the container, "
                "and the storage account must allow the network the bot runs from.")
        return None

    def check(self) -> None:
        """Start-up probe: log a clear error if the state storage cannot be used. Never raises, so a role that is granted a
        minute after the first deploy does not leave the agent in a crash loop."""
        try:
            next(iter(self._container.list_blobs(results_per_page=1, timeout=BLOB_TIMEOUT_SECONDS)), None)
        except Exception as exc:                                      # noqa: BLE001  (a probe: report, never fail)
            log.error("conversation state storage is NOT usable: %s", self._explain(exc) or f"{type(exc).__name__}")
        else:
            log.info("conversation state storage is reachable (%s)", self._where)

    def load(self, keys: list[str]) -> dict[str, Any] | None:
        from azure.core.exceptions import ResourceNotFoundError

        for key in keys:
            try:
                raw = self._container.download_blob(self._name(key), timeout=BLOB_TIMEOUT_SECONDS).readall()
            except ResourceNotFoundError as exc:
                if (explained := self._explain(exc)) is not None:   # the whole container is missing, not just this blob
                    raise explained from exc
                continue
            except Exception as exc:
                if (explained := self._explain(exc)) is not None:
                    raise explained from exc
                raise
            return json.loads(raw)
        return None

    def save(self, keys: list[str], data: dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        for key in keys:
            try:
                self._container.upload_blob(self._name(key), payload, overwrite=True, timeout=BLOB_TIMEOUT_SECONDS)
            except Exception as exc:
                if (explained := self._explain(exc)) is not None:
                    raise explained from exc
                raise

    def save_transcript(self, path: str, csv_text: str) -> None:
        from azure.storage.blob import ContentSettings

        try:
            self._container.upload_blob(path, csv_text.encode("utf-8-sig"), overwrite=True, timeout=BLOB_TIMEOUT_SECONDS,
                                        content_settings=ContentSettings(content_type="text/csv; charset=utf-8"))
        except Exception as exc:
            if (explained := self._explain(exc)) is not None:
                raise explained from exc
            raise


def make_state_store() -> StateStore:
    """Blob Storage when STATE_BLOB_ACCOUNT_URL or STATE_BLOB_CONNECTION_STRING is set (Foundry), otherwise local files."""
    if os.environ.get("STATE_BLOB_ACCOUNT_URL", "").strip() or os.environ.get("STATE_BLOB_CONNECTION_STRING", "").strip():
        store = BlobStateStore.from_env()
        log.info("conversation state: Azure Blob Storage")
        store.check()
        return store
    store = FileStateStore()
    log.info("conversation state: local files in %s", store.root)
    return store
