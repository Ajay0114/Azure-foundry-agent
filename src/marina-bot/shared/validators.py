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


_NOT_A_NAME = {"no", "yes", "y", "n", "ok", "okay", "hi", "hello", "hey", "skip", "help", "none", "nope", "yeah", "thanks", "thank"}


def parse_name(text: str) -> str | None:
    """A first name, a last name, or both (up to five words). Returns None if it is not a name."""
    cleaned = _NAME_PREFIX.sub("", (text or "").strip()).strip(" .")
    tokens = cleaned.split()
    if not (1 <= len(tokens) <= 5):
        return None
    if len(tokens) == 1 and (len(tokens[0]) < 2 or tokens[0].lower() in _NOT_A_NAME):     # "n", "no", "hello" are not names
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


# ============================================================================================
# Product count and product details (Kore: PC_HomeDelivery_Agent_ProductCount / _ProductDetails)
# ============================================================================================
_NUMBER_WORDS = {"zero": 0, "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                 "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "couple": 2, "pair": 2}
_NUMBER_REPLY = re.compile(r"^(?:just |only |about |around |total of |a total of )?(\d{1,3}|[a-z]+)"
                           r"(?: (?:items?|products?|things?|pieces?|units?|in total|total))?$")
_CONDITION_WORDS = {
    "new": ["new", "unopened", "sealed", "unused", "never opened", "never used", "not opened", "arrived late",
            "no longer need", "dont need", "changed my mind", "changed mind", "brand new"],
    "used": ["used", "tried", "opened", "tested", "partially used", "used it"],
    "damaged": ["damaged", "broken", "defective", "not working", "stopped working", "cracked", "faulty", "leaked"],
    "wrong product": ["wrong product", "wrong item", "wrong", "not what i ordered", "received wrong", "different product",
                      "sent wrong", "incorrect"],
}
_FINISHED = re.compile(r"^(?:no,? )?(?:that'?s (?:all|it|everything)|thats (?:all|it)|no more|nothing (?:else|more)|"
                       r"nope|done|that is all|that is it|only (?:that|this|those|these)|just (?:that|this|those|these))\b[ .!]*$"
                       r"|\b(?:no more|nothing else|that'?s all|thats all)\b", re.I)
_FILLER_WORDS = re.compile(r"\b(?:products?|items?|units?|things?)\b", re.I)


def parse_quantity(text: str) -> int | None:
    """A bare quantity, 1 to 999 ("3", "two", "just 1"). Anything with other words in it is not a bare quantity."""
    reply = " ".join((text or "").lower().replace(",", " ").split()).strip(" .!")
    match = _NUMBER_REPLY.match(re.sub(r"^a (couple|pair)(?: of)?$", r"\1", reply))
    if not match:
        return None
    word = match.group(1)
    value = int(word) if word.isdigit() else _NUMBER_WORDS.get(word)
    return value if value and 1 <= value <= 999 else None


def parse_product_count(text: str) -> int | None:
    """The total number of items, when the reply is just a number (digits or words)."""
    return parse_quantity(text)


def parse_condition(text: str) -> str | None:
    """new | used | damaged | wrong product, from Kore's synonym lists. None when no word or more than one condition.

    A word inside a longer phrase of another condition does not count ("never opened" is new, not used).
    """
    lowered = " ".join(re.sub(r"[^a-z0-9' ]", " ", (text or "").lower()).replace("'", "").split())
    found = [(m.start(), m.end(), condition) for condition, words in _CONDITION_WORDS.items() for w in words
             for m in re.finditer(rf"\b{re.escape(w.replace(chr(39), ''))}\b", lowered)]
    hits = {c for s, e, c in found
            if not any(c2 != c and s2 <= s and e <= e2 and (e2 - s2) > (e - s) for s2, e2, c2 in found)}
    if "wrong product" in hits:
        hits.discard("new")              # "wrong item, never opened" is still a wrong product
    return hits.pop() if len(hits) == 1 else None


def says_finished(text: str) -> bool:
    """"that's all", "no more", "done": the customer has no further products to list."""
    return bool(_FINISHED.search(" ".join((text or "").lower().split())))


def clean_product_name(name: str | None) -> str | None:
    """The product noun without filler words ("the cream product" -> "cream"); None when nothing real is left."""
    cleaned = " ".join(_FILLER_WORDS.sub(" ", name or "").split()).strip(" .,;:-")
    return cleaned if cleaned and not cleaned.isdigit() and len(cleaned) <= 120 else None


def same_product(a: str | None, b: str | None) -> bool:
    return bool(a and b) and " ".join(re.sub(r"[^a-z0-9 ]", " ", a.lower()).split()) == " ".join(
        re.sub(r"[^a-z0-9 ]", " ", b.lower()).split())
