"""The complete conversation as a CSV file, in the layout of Kore's transcript export.

Kore columns:  Bot Name, User, Channel, Language, Bot Message, User Message, Timestamp, emailData
One row per message: a bot row has only "Bot Message", a customer row only "User Message". A file the customer sent shows
as the user message "Attachment uploaded", as in Kore.

The file is rewritten after every turn, so it is always the whole conversation so far (also when the customer walks
away half-way). It is stored next to the conversation state (see shared/state_store.py):

    transcripts/<yyyy-mm-dd>/<conversation key>.csv        (a folder per day, named by the day the conversation started, e.g. 2026-10-09)

By default personal details are masked, as Kore's export does: the customer's name, the spa record name, e-mail addresses
and phone numbers become #*#NAME#*#, #*#EMAIL#*#, #*#PHONE#*#. The raw messages stay in the conversation state (which the
Zendesk ticket needs), so masking can be switched off later without losing anything.

Settings (environment variables, all optional):
  TRANSCRIPT_ENABLED       "false" to write no transcript file (default true)
  TRANSCRIPT_MASK_PII      "false" to keep names, e-mails and phone numbers as typed (default true)
  TRANSCRIPT_BOT_NAME      the "Bot Name" column (default "Marina")
  TRANSCRIPT_CHANNEL       the "Channel" column (default "Foundry")
"""

import csv
import io
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from shared.state_store import safe_key

HEADER = ["Bot Name", "User", "Channel", "Language", "Bot Message", "User Message", "Timestamp", "emailData"]
MAX_ROWS = 600
ATTACHMENT_TEXT = "Attachment uploaded"
_TIME_FORMAT = "%a %b %d %Y %I:%M:%S %p UTC"          # Fri Oct 09 2026 01:35:03 AM UTC
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\+?\(?\d[\d\s().\-]{5,}\d")
_DATE_LIKE = re.compile(r"^\s*(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}-\d{1,2}-\d{2,4})\s*$")


@dataclass(frozen=True)
class TranscriptConfig:
    enabled: bool = True
    mask_pii: bool = True
    bot_name: str = "Marina"
    channel: str = "Foundry"

    @classmethod
    def from_env(cls) -> "TranscriptConfig":
        def flag(name: str) -> bool:
            return os.environ.get(name, "true").strip().lower() not in ("false", "0", "no", "off")

        return cls(enabled=flag("TRANSCRIPT_ENABLED"), mask_pii=flag("TRANSCRIPT_MASK_PII"),
                   bot_name=os.environ.get("TRANSCRIPT_BOT_NAME", "").strip() or "Marina",
                   channel=os.environ.get("TRANSCRIPT_CHANNEL", "").strip() or "Foundry")


def record_turn(session: dict[str, Any], user_text: str, replies: list[str], files: int, now: datetime) -> None:
    """Add this turn's messages to the conversation log kept in the session (raw text, in order)."""
    stamp = now.isoformat(timespec="seconds")
    session.setdefault("started_at", stamp)
    rows = session.setdefault("transcript_rows", [])
    if user_text and user_text.strip():
        rows.append({"ts": stamp, "who": "user", "text": user_text})
    if files:
        rows.append({"ts": stamp, "who": "user", "text": ATTACHMENT_TEXT})
    rows.extend({"ts": stamp, "who": "bot", "text": reply} for reply in replies if reply and reply.strip())
    session["transcript_rows"] = rows[-MAX_ROWS:]


def _known_names(session: dict[str, Any]) -> list[str]:
    pii = session.get("piiEntities") or {}
    values = [pii.get("name"), pii.get("sparecordname"), pii.get("nameAsPerSpa"), session.get("spa_record_name"),
              session.get("customerName")]
    names = {str(v).strip() for v in values if v and len(str(v).strip()) >= 3 and str(v).strip().lower() != "not provided"}
    return sorted(names, key=len, reverse=True)                  # longest first, so "Jane Doe" goes before "Jane"


def mask_text(text: str, session: dict[str, Any]) -> str:
    """Replace the customer's name(s), e-mail addresses and phone numbers with placeholders."""
    pii = session.get("piiEntities") or {}
    for name in _known_names(session):
        text = re.sub(re.escape(name), "#*#NAME#*#", text, flags=re.I)
    text = _EMAIL.sub("#*#EMAIL#*#", text)
    known_phone = str(pii.get("phoneNumber") or "").strip()
    if known_phone:
        text = text.replace(known_phone, "#*#PHONE#*#")

    def phone(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        return match.group(0) if not 7 <= len(digits) <= 15 or _DATE_LIKE.match(match.group(0)) else "#*#PHONE#*#"

    return _PHONE.sub(phone, text)


def _stamp(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime(_TIME_FORMAT)
    except ValueError:
        return iso


def to_csv(session: dict[str, Any], key: str, config: TranscriptConfig) -> str:
    """The whole conversation so far, as CSV text in Kore's column layout."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(HEADER)
    for row in session.get("transcript_rows") or []:
        text = mask_text(row["text"], session) if config.mask_pii else row["text"]
        bot, user = (text, "") if row["who"] == "bot" else ("", text)
        writer.writerow([config.bot_name, key, config.channel, "en", bot, user, _stamp(row["ts"]), ""])
    return out.getvalue()


def blob_path(session: dict[str, Any], key: str) -> str:
    """transcripts/<yyyy-mm-dd>/<key>.csv, by the day the conversation started (stable for the whole conversation)."""
    try:
        folder = datetime.fromisoformat(str(session.get("started_at") or "")).strftime("%Y-%m-%d")
    except ValueError:
        folder = "undated"
    return f"transcripts/{folder}/{safe_key(key)}.csv"
