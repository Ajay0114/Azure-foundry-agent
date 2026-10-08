"""Per-conversation dialog state, persisted between chat turns.

POC implementation: one JSON file per key under MARINA_STATE_DIR (default ~/marina_state).
Hosted agents keep $HOME across idle periods, so this survives a session going idle.
Replace with Cosmos DB / the Foundry state store before production by implementing the same
two methods.
"""

import json
import os
import re
from pathlib import Path
from typing import Any


def _default_root() -> Path:
    return Path(os.environ.get("MARINA_STATE_DIR") or Path.home() / "marina_state")


class FileStateStore:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else _default_root()

    def _path(self, key: str) -> Path:
        return self.root / (re.sub(r"[^A-Za-z0-9_.-]", "_", key) + ".json")

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
