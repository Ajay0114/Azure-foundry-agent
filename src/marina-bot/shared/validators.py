"""Small input parsers standing in for Kore's built-in entity types and the rules inside its agent nodes.

Deliberately simple and deterministic: name, email, purchaser name, cabin numbers and phone numbers. Yes/no
answers and dates are read by shared.dates.
"""

import re
from dataclasses import dataclass, field

from shared.dates import MONTHS, find_dates, says_skip

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


# ============================================================================================
# Purchaser name (Kore: PC_HomeDelivery_Agent_SpaRecordName)
# ============================================================================================
_PURCHASER_PREFIXES = (
    "i think it was", "i think its", "i think it's", "i think", "my name is", "my name was", "the name is",
    "the name was", "name used was", "name used is", "name was", "name is", "it was", "it is", "it's", "its",
    "that was", "under the name", "under",
)
_NAME_WORD = re.compile(r"^[^\W\d_]+(?:[-'’][^\W\d_]+)*$")     # letters, with inner hyphens / apostrophes
_MULTI_NAME_SPLIT = re.compile(r"\s+(?:or|and|to|from)\s+|\s*[&,]\s*", re.I)
MAX_NAME_WORDS = 6


@dataclass(frozen=True)
class PurchaserName:
    kind: str                                   # "name" | "skip" | "multiple" | "invalid"
    name: str = ""
    options: list[str] = field(default_factory=list)


def _clean_name(text: str) -> str | None:
    words = text.strip(" .!?,;:").split()
    if not 1 <= len(words) <= MAX_NAME_WORDS or not all(_NAME_WORD.match(w) for w in words):
        return None
    return " ".join(words)


def _strip_prefixes(text: str) -> str:
    text = " ".join((text or "").split())
    changed = True
    while changed:
        changed = False
        lowered = text.lower()
        for prefix in _PURCHASER_PREFIXES:
            if lowered.startswith(prefix + " "):
                text, changed = text[len(prefix) + 1:].lstrip(), True
                break
    return text


def parse_purchaser_name(text: str) -> PurchaserName:
    """The name as it appears on the spa record.

    One to six words made of letters (hyphens and apostrophes allowed inside a word): "Karthik", "M Umer",
    "Robert D", "Jean-Luc O'Brien". Two names joined by or / and / & are NOT accepted: the customer must say which.
    """
    if says_skip(text):
        return PurchaserName("skip")
    stripped = _strip_prefixes(text)
    parts = [p for p in _MULTI_NAME_SPLIT.split(stripped) if p and p.strip()]
    if len(parts) >= 2:
        cleaned = [_clean_name(p) for p in parts]
        return PurchaserName("multiple", options=cleaned) if all(cleaned) else PurchaserName("invalid")
    name = _clean_name(stripped)
    return PurchaserName("name", name=name) if name else PurchaserName("invalid")


# ============================================================================================
# Cabin numbers (Kore: PC_Home_Delivery_Agent_CabinNumber)
# ============================================================================================
_BAD_SEPARATOR = re.compile(r"[A-Za-z0-9][@/;|\\#$%*_+=!?:\-][A-Za-z0-9]")
_ALNUM = re.compile(r"[A-Za-z0-9]+")
_ORDINAL = re.compile(r"^\d{1,2}(?:st|nd|rd|th)$", re.I)
_YEAR_LIKE = re.compile(r"^(?:19|20)\d{2}$")
MAX_CABIN_LENGTH = 10


@dataclass(frozen=True)
class CabinReading:
    cabins: list[str] = field(default_factory=list)
    bad_separator: bool = False                 # "294@TC03": we do not guess where one cabin ends


def parse_cabins(text: str) -> CabinReading:
    """One or more cabin numbers: letters and digits only, at least one digit (4201, A9202, TC03).

    Several may be joined by commas, "and", "&", "then", "or" and so on. A cabin joined to another with a symbol
    (294@TC03) is not guessed at. This reads the reply to "What's your cabin number?", so a number in a sentence
    ("I was in 294 and then moved to TC03") counts; phone numbers, ordinals and years next to a month do not.
    """
    text = (text or "").strip()
    if _BAD_SEPARATOR.search(text) and re.search(r"\d", text):
        return CabinReading(bad_separator=True)
    words = text.split()
    mentions_month = any(w.lower().rstrip(".,") in MONTHS for w in words)
    cabins: list[str] = []
    for token in _ALNUM.findall(text):
        if not re.search(r"\d", token) or len(token) > MAX_CABIN_LENGTH or _ORDINAL.match(token):
            continue
        if token.isdigit() and len(token) >= 9:                  # a phone number, not a cabin
            continue
        if mentions_month and _YEAR_LIKE.match(token):           # "March 2026"
            continue
        if token.upper() not in cabins:
            cabins.append(token.upper())
    return CabinReading(cabins)


# ============================================================================================
# Phone number (Kore: PC_HomeDelivery_Entity_PhoneNumber, entity type phone_number)
# ============================================================================================
_PHONE = re.compile(r"\+?\(?\d[\d\s().\-]{5,}\d")
MIN_PHONE_DIGITS, MAX_PHONE_DIGITS = 7, 15                      # 15 is the E.164 maximum


def parse_phone(text: str) -> str | None:
    """A phone number as typed ("+1 555 123 4567"), or None. 7 to 15 digits; a date is not a phone number."""
    text = (text or "").strip()
    if not text or (find_dates(text) and "+" not in text):
        return None
    for match in _PHONE.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if MIN_PHONE_DIGITS <= len(digits) <= MAX_PHONE_DIGITS:
            return " ".join(match.group(0).split())
    return None


# ============================================================================================
# Delivery type (Kore: PC_HomeDelivery_Entity_DeliveryType, a list of two values with synonyms)
# ============================================================================================
ONBOARD, HOME_DELIVERY = "Onboard Purchase", "Home Delivery"
_ONBOARD = re.compile(r"\b(?:on\s?board|aboard|on the (?:ship|boat|vessel)|in the (?:shop|store|spa)|during (?:the |my )?cruise"
                      r"|bought (?:it )?on the ship|ship)\b", re.I)
_HOME = re.compile(r"\b(?:home|deliver(?:y|ed)?|shipp?(?:ed|ing)|sent|mail(?:ed)?|house|ordered|order)\b", re.I)


def parse_delivery_type(text: str) -> str | None:
    """"Onboard Purchase" or "Home Delivery" (the customer's words, a number 1 or 2), else None. Both or neither -> None."""
    text = (text or "").strip()
    if text in ("1", "2"):
        return ONBOARD if text == "1" else HOME_DELIVERY
    onboard, home = bool(_ONBOARD.search(text)), bool(_HOME.search(text))
    if onboard == home:
        return None
    return ONBOARD if onboard else HOME_DELIVERY


# ============================================================================================
# Return reason (Kore: PC_HomeDelivery_Entity_IssueReasonButtons + IssueResonButtonsValidations)
# ============================================================================================
@dataclass(frozen=True)
class ReturnReason:
    title: str           # shown to the customer and sent to Zendesk as the reason text
    zendesk: str         # value of the Zendesk reason field
    api: str             # value sent to the document API


RETURN_REASONS = [
    ReturnReason("Item(s) arrived damaged or incorrect", "osw_items_damaged_or_incorrect", "itemsArrivedDamagedOrIncorrect"),
    ReturnReason("Product(s) did not meet expectations", "osw_products_didn’t_meet_expectation",
                 "productsDidNotMeetExprectations"),
    ReturnReason("Health or sensitivity concern", "osw_health_or_sensitivity_concern", "healthOrSensitiveConcerns"),
    ReturnReason("Order, delivery, or billing issue", "osw_order_delivery_or_billing_issue", "orderDeliveryOrBillingIssue"),
    ReturnReason("Other", "osw_other2", "other"),
]
_REASON_WORDS = [
    re.compile(r"damag|broken|broke|leak|spill|crack|incorrect|wrong|defect|missing", re.I),
    re.compile(r"expect|did ?n[o']?t (?:like|work)|not (?:as|what)|disappoint|no results?|quality|smell|texture", re.I),
    re.compile(r"health|sensitiv|allerg|rash|reaction|irritat|skin|doctor|pregnan|medical", re.I),
    re.compile(r"order|deliver|billing|billed|charge|invoice|late|shipping|never arrived|not received|didn.t arrive", re.I),
]


def parse_return_reason(text: str) -> ReturnReason | None:
    """One of the five reasons: by number (1-5), by title, or by a clear keyword. None when unclear or ambiguous."""
    text = " ".join((text or "").split())
    if not text:
        return None
    if text in {"1", "2", "3", "4", "5"}:
        return RETURN_REASONS[int(text) - 1]
    for reason in RETURN_REASONS:
        if text.lower().rstrip(".") == reason.title.lower():
            return reason
    if text.lower().rstrip(".!") == "other":
        return RETURN_REASONS[4]
    hits = [i for i, pattern in enumerate(_REASON_WORDS) if pattern.search(text)]
    return RETURN_REASONS[hits[0]] if len(hits) == 1 else None
