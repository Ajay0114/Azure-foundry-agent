"""The execution trace of a conversation: Kore's "Debug Log" for this bot.

For every message it records what ran and in what order: the start of the turn, each move from one node to the next, where the
bot stopped to wait for the customer, each model call and each outside-service call with how long it took, errors, and every
conversation variable the turn changed. The developer page (web/dev.html) shows it next to the chat.

It is OFF unless DEBUG_TRACE=true, because the trace and the variable values contain what the customer typed. A deployed
production agent should leave it off; a dev or test deployment turns it on. When off, every function here does nothing.

Where it goes: Persist (orchestrator.py) appends one record per message to session["debug_turns"] (the last MAX_TURNS), which is
saved with the rest of the conversation state; the developer page reads it from there.
"""

import copy
import os
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from models import Turn

MAX_TURNS = 40
MAX_VALUE = 200
NOISY = {"messages", "transcript", "transcript_rows", "conversationHistoryString", "nodeOutputs", "debug_turns",
         "suggestions", "purchaseDetails", "cruiseDates"}          # bookkeeping, not variables worth diffing


def enabled() -> bool:
    return os.environ.get("DEBUG_TRACE", "").strip().lower() in ("1", "true", "yes", "on")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def short(value: Any, limit: int = MAX_VALUE) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def event(turn: Turn, kind: str, name: str, detail: Any = "", ms: int | None = None, **data: Any) -> None:
    """Add one line to this turn's trace. kinds: turn, transition, wait, end, llm, api, var, error."""
    if not enabled():
        return
    record = {"t": _now(), "kind": kind, "name": name, "detail": short(detail) if detail != "" else "", "ms": ms, **data}
    turn.trace.append({k: v for k, v in record.items() if v is not None and v != ""})


async def call(turn: Turn, kind: str, name: str, awaitable: Awaitable[Any], detail: Callable[[Any], Any] | None = None) -> Any:
    """Await a model or service call and record how long it took (and that it failed, if it did)."""
    if not enabled():
        return await awaitable
    started = time.perf_counter()
    try:
        result = await awaitable
    except Exception as exc:
        status = getattr(exc, "status", None)
        event(turn, "error", name, type(exc).__name__ + (f" (HTTP {status})" if status else ""),
              ms=round((time.perf_counter() - started) * 1000), of=kind)
        raise
    event(turn, kind, name, detail(result) if detail else "", ms=round((time.perf_counter() - started) * 1000))
    return result


# ---- variables ---------------------------------------------------------------------------------------------------------
def _filtered(session: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy({k: v for k, v in session.items() if k not in NOISY})


def snapshot(turn: Turn) -> None:
    """Remember the variables as they are when the turn starts, to show what the turn changed."""
    if enabled():
        turn.trace_before = {"session": _filtered(turn.session), "entities": copy.deepcopy(turn.entities)}


def _changes(scope: str, before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for key in sorted(set(before) | set(after)):
        old, new = before.get(key), after.get(key)
        if old == new:
            continue
        if isinstance(old, dict) or isinstance(new, dict):            # one level deeper, e.g. piiEntities.phoneNumber
            old_d, new_d = old if isinstance(old, dict) else {}, new if isinstance(new, dict) else {}
            for sub in sorted(set(old_d) | set(new_d)):
                if old_d.get(sub) != new_d.get(sub):
                    out.append({"path": f"{scope}.{key}.{sub}", "old": short(old_d.get(sub)), "new": short(new_d.get(sub))})
        else:
            out.append({"path": f"{scope}.{key}", "old": short(old), "new": short(new)})
    return out


def variable_changes(turn: Turn) -> list[dict[str, str]]:
    before = turn.trace_before or {}
    return (_changes("session", before.get("session", {}), _filtered(turn.session))
            + _changes("entities", before.get("entities", {}), turn.entities))


def record_turn(session: dict[str, Any], turn: Turn, replies: list[str]) -> None:
    """Called once at the end of a turn: file this turn's trace under the conversation (newest last, capped)."""
    if not enabled():
        return
    for change in variable_changes(turn):
        turn.trace.append({"t": _now(), "kind": "var", "name": change["path"], "old": change["old"], "new": change["new"]})
    turns = session.setdefault("debug_turns", [])
    turns.append({"n": (turns[-1]["n"] + 1) if turns else 1, "user": short(turn.text, 400), "replies": [short(r, 600) for r in replies],
                  "suggestions": list(turn.suggestions), "events": turn.trace})
    session["debug_turns"] = turns[-MAX_TURNS:]
