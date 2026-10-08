"""Small input parsers standing in for Kore's built-in entity types and dialog acts.

These are deliberately simple POC approximations of Kore's NLP-based person_name / email
entities and yes/no dialog acts.
"""

import re

_NAME_PREFIX = re.compile(r"^(my name is|my name's|name is|i am|i'm|it is|it's|this is)\s+", re.I)
_NAME_TOKEN = re.compile(r"^[A-Za-z][A-Za-z'’.\-]*$")
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

_YES = {"yes", "y", "yeah", "yep", "yup", "correct", "sure", "ok", "okay", "confirm", "confirmed", "right"}
_NO = {"no", "n", "nope", "nah", "incorrect", "wrong", "change"}


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


def parse_yes_no(text: str) -> bool | None:
    words = re.findall(r"[a-z']+", (text or "").lower())
    if not words:
        return None
    if words[0] in _YES:
        return True
    if words[0] in _NO:
        return False
    return None
