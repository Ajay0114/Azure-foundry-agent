"""Small input parsers standing in for Kore's built-in person_name and email entity types.

These are deliberately simple POC approximations of Kore's NLP-based entities. Yes/no answers are read by
shared.dates.read_yes_no.
"""

import re

_NAME_PREFIX = re.compile(r"^(my name is|my name's|name is|i am|i'm|it is|it's|this is)\s+", re.I)
_NAME_TOKEN = re.compile(r"^[A-Za-z][A-Za-z'’.\-]*$")
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def parse_full_name(text: str) -> str | None:
    """First and last name required (matches the Kore error message). Returns None if not a name."""
    cleaned = _NAME_PREFIX.sub("", (text or "").strip()).strip(" .")
    tokens = cleaned.split()
    if not (2 <= len(tokens) <= 5):
        return None
    if not all(_NAME_TOKEN.match(t) for t in tokens):
        return None
    return " ".join(tokens)


def parse_email(text: str) -> str | None:
    match = _EMAIL.search(text or "")
    return match.group(0) if match else None
