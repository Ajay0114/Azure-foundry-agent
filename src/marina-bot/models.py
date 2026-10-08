"""Messages that flow between workflow executors.

One chat turn = one workflow run. The user's message enters as a TurnInput, becomes a Turn that
carries the saved dialog state from node to node, and ends at the Persist executor which saves
the state and returns the bot's reply. Everything here is plain JSON-friendly data so workflow
checkpoints can serialise it.
"""

from dataclasses import dataclass, field
from typing import Any

from shared.session import DialogContext


@dataclass
class TurnInput:
    """What the host hands to the workflow for one user message."""
    text: str
    load_keys: list[str] = field(default_factory=list)   # state keys to look up (conversation / previous response)
    save_keys: list[str] = field(default_factory=list)   # state keys to write after this turn


@dataclass
class Turn:
    """Mutable per-turn envelope passed between executors."""
    text: str
    save_keys: list[str]
    session: dict[str, Any]          # Kore's context.session.BotUserSession
    entities: dict[str, Any]         # Kore's context.entities
    route: str = ""                  # id of the executor that must run next
    resuming: bool = False           # True when `text` is the answer to the question a node asked last turn
    replies: list[str] = field(default_factory=list)

    @property
    def ctx(self) -> DialogContext:
        """View onto session/entities that shares the same dicts (writes persist)."""
        return DialogContext(session=self.session, entities=self.entities)

    def say(self, text: str) -> None:
        self.replies.append(text)
