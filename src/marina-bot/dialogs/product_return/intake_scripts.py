"""Intake-stage script nodes, ported from the Kore PC_HomeDelivery dialog.

Ported nodes:
  PC_Common_1_Script_InitialUserMessage  -> set_initial_message
  PC_Script_ProcessExtractedEntities     -> process_extracted_entities
"""

import json
import logging
import re
from datetime import date
from typing import Any

from shared.session import DialogContext

log = logging.getLogger(__name__)

SENTINEL_VALUES = {
    "unknown", "not sure", "i don't know", "i dont know", "dont know",
    "don't know", "no idea", "n/a", "na", "none", "not applicable",
    "ship", "boat", "cruise", "vessel", "the ship", "a ship",
}

_MONTHS = {"jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
           "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"}
_MONTH_WORDS = (r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?"
                r"|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b")


def set_initial_message(ctx: DialogContext, last_message_body: str) -> None:
    """Store the user's first message once; later turns never overwrite it."""
    if not ctx.session.get("initialMessage"):
        ctx.session["initialMessage"] = last_message_body
    log.info("Initial Message: %s", ctx.session.get("initialMessage"))


def is_valid_entity_value(val: Any) -> bool:
    if val is None:
        return False
    text = str(val).strip()
    if text == "":
        return False
    return text.lower() not in SENTINEL_VALUES


def has_day(raw: Any) -> bool:
    """True for a full date, or day+month. Month-only / year-only returns False."""
    if not raw:
        return False
    s = str(raw).strip()
    if re.fullmatch(r"\d{4}[/.\-]\d{1,2}[/.\-]\d{1,2}", s):
        return True
    if re.fullmatch(r"\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4}", s):
        return True
    stripped = re.sub(_MONTH_WORDS, "", s, flags=re.I)
    stripped = re.sub(r"\b(last|next|this|the)\b", "", stripped, flags=re.I)
    stripped = re.sub(r"\b(20\d{2}|19\d{2})\b", "", stripped)
    stripped = re.sub(r"\b(st|nd|rd|th)\b", "", stripped, flags=re.I)
    stripped = re.sub(r"[^0-9]", " ", stripped).strip()
    return bool(re.search(r"\d+", stripped))


def _build(y: Any, mo: Any, d: Any) -> str | None:
    try:
        yy, mm, dd = int(y), int(mo), int(d)
        date(yy, mm, dd)  # rejects impossible days such as Feb 30
    except (ValueError, TypeError):
        return None
    return f"{yy:04d}-{mm:02d}-{dd:02d}"


def normalize_date(value: Any) -> str | None:
    """Normalise any supported format to ISO YYYY-MM-DD, or None if not a complete valid date."""
    if not value:
        return None
    s = str(value).strip()
    s = re.sub(r"(\d{1,2})(st|nd|rd|th)\b", r"\1", s, flags=re.I)
    s = re.sub(r",", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    m = re.fullmatch(r"(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})", s)
    if m:
        return _build(m[1], m[2], m[3])

    m = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", s)
    if m:
        a, b = int(m[1]), int(m[2])
        if a > 12 and b <= 12:
            return _build(m[3], b, a)  # DD-MM-YYYY
        if b > 12 and a <= 12:
            return _build(m[3], a, b)  # MM-DD-YYYY
        return _build(m[3], a, b)      # both <= 12: month-first by default

    mo_hit = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", s.lower())
    if mo_hit:
        year = re.search(r"\b(\d{4})\b", s)
        rest = re.sub(r"\b\d{4}\b", " ", s, count=1)
        day = re.search(r"\b(\d{1,2})\b", rest)
        if year and day:
            return _build(year[1], _MONTHS[mo_hit[1]], day[1])
    return None


def _store_date(ctx: DialogContext, field_name: str, raw_val: Any) -> None:
    if not is_valid_entity_value(raw_val):
        return
    if not has_day(raw_val):
        log.info("%s rejected (no day component): %s", field_name, raw_val)
        return
    iso = normalize_date(raw_val)
    if iso:
        ctx.entities[field_name] = iso
        ctx.session[field_name] = iso
        log.info("%s stored: %s (normalised)", field_name, iso)
        return
    # Has a 4-digit year but will not parse: malformed. Reject; never store the raw text.
    if re.search(r"\b(?:19|20)\d{2}\b", str(raw_val)):
        log.info("%s rejected (unparseable/invalid date): %s", field_name, raw_val)
        return
    # Partial such as "mar 10" (no year): keep raw so a later node asks for the year.
    partial = str(raw_val).strip()
    ctx.entities[field_name] = partial
    ctx.session[field_name] = partial
    log.info("%s stored: %s (partial, awaiting year)", field_name, partial)


def process_extracted_entities(ctx: DialogContext, llm_text: str | None) -> None:
    """Parse the extraction prompt's JSON output into ctx.entities / ctx.session.

    Never raises: bad or missing output leaves the context unchanged, as in Kore.
    """
    if not llm_text:
        log.info("No prompt output found, skipping extraction.")
        return
    clean = re.sub(r"```json|```", "", llm_text, flags=re.I).strip()
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError as exc:
        log.info("JSON parse error in extraction output: %s", exc)
        return
    if not isinstance(parsed, dict):
        return

    unknown = parsed.get("unknown_indicated_fields")
    if isinstance(unknown, list) and unknown:
        ctx.session["unknownIndicatedFields"] = unknown

    for out_key, in_key in (("ship_name", "ship_name_candidate"), ("cruise_line", "cruise_line_candidate")):
        if is_valid_entity_value(parsed.get(in_key)):
            ctx.entities[out_key] = parsed[in_key]
            ctx.session[out_key] = parsed[in_key]

    _store_date(ctx, "start_date", parsed.get("start_date_raw"))
    _store_date(ctx, "end_date", parsed.get("end_date_raw"))
    _store_date(ctx, "service_date", parsed.get("service_date_raw"))
