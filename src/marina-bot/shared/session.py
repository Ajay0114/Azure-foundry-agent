"""Python stand-in for Kore's dialog context.

Kore script nodes read and write three places:
  context.session.BotUserSession.*  -> DialogContext.session  (persists for the whole conversation)
  context.entities.*                -> DialogContext.entities (values collected in this dialog)
  context.<node outputs>            -> returned from the executors, not stored here

Keeping the same key names as Kore (e.g. "initialMessage", "ship_name") makes each script
port line-for-line comparable with the export in docs/kore-reference.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DialogContext:
    session: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"session": self.session, "entities": self.entities}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DialogContext":
        return cls(session=dict(data.get("session", {})), entities=dict(data.get("entities", {})))
