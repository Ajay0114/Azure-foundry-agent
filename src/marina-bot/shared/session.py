"""Python stand-in for Kore's dialog context.

Kore script nodes read and write three places:
  context.session.BotUserSession.*  -> DialogContext.session  (persists for the whole conversation)
  context.entities.*                -> DialogContext.entities (values collected in this dialog)
  context.<node outputs>            -> returned from the executors, not stored here

Keeping the same key names as Kore (e.g. "initialMessage", "ship_name") keeps each ported script
line-for-line comparable with the original Kore node.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DialogContext:
    session: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, Any] = field(default_factory=dict)
