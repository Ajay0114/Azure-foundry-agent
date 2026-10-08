"""Understanding dates in chat messages: deterministic, tested, no LLM.

`read_text(text)` turns what a customer typed into a `DateReading`:

    "January 11 2026"                -> dates: start = 2026-01-11
    "Jan 2-6, 2026" / "13-20 July 2026" / "Nov 29 to Dec 6 2025"
                                     -> dates: start and end (a compressed range shares month/year)
    "7/19/26"                        -> dates: 2026-07-19 (month first unless the first number can only be a day)
    "Jan 10"                         -> dates: day+month, year unknown (the caller asks for the year)
    "2026"                           -> year (answers a pending "what year?")
    "not sure" / "idk" / "skip"      -> skip
    "yes please" / "nope"            -> yes / no
    anything else                    -> unclear (the caller may try an LLM, then re-ask)

Nothing here guesses a missing year, and nothing accepts an impossible calendar date (Feb 30).
Kore's rules are kept: numeric dates are month-first, two-digit years are 19xx above 68 and 20xx otherwise.
"""

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

MONTHS = {"jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3, "apr": 4, "april": 4,
          "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7, "aug": 8, "august": 8,
          "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10, "nov": 11, "november": 11,
          "dec": 12, "december": 12}
_MONTH_ABBR = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_M = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
_TO = r"(?:-|–|—|to|through|thru|until|till)"
_YEAR = r"((?:19|20)\d{2})"
_FLAGS = re.IGNORECASE

SKIP_PHRASES = (
    "don't know", "dont know", "do not know", "i don't know", "no idea", "not sure", "unsure", "no clue", "idk",
    "don't remember", "dont remember", "do not remember", "can't remember", "cant remember", "cannot remember",
    "not remember", "forgot", "n/a", "not applicable", "skip", "unknown", "none",
)
_YES_FIRST = {"yes", "y", "yeah", "yep", "yup", "sure", "ok", "okay", "correct", "right", "proceed", "confirm",
              "confirmed", "absolutely", "definitely", "affirmative"}
_NO_FIRST = {"no", "n", "nope", "nah", "incorrect", "wrong", "negative"}
_YES_PHRASES = ("that's right", "thats right", "that is correct", "that's correct", "sounds good", "go ahead")


# ============================================================================================
# Values
# ============================================================================================
@dataclass(frozen=True)
class PartialDate:
    """A date as stated: any of day / month / year may be missing."""
    day: int | None = None
    month: int | None = None
    year: int | None = None

    @property
    def has_day_and_month(self) -> bool:
        return self.day is not None and self.month is not None

    @property
    def is_possible(self) -> bool:
        """Day and month form a real calendar day (Feb 29 allowed when the year is unknown)."""
        if not self.has_day_and_month or not 1 <= self.month <= 12 or self.day < 1:
            return False
        year = self.year if self.year is not None else 2000          # 2000 is a leap year
        return self.day <= calendar.monthrange(year, self.month)[1]

    @property
    def is_full(self) -> bool:
        return self.year is not None and self.is_possible

    def to_iso(self) -> str | None:
        return date(self.year, self.month, self.day).isoformat() if self.is_full else None

    def with_year(self, year: int) -> "PartialDate":
        return PartialDate(self.day, self.month, year)

    def describe(self) -> str:
        """For questions: 'Jan 10'."""
        return f"{_MONTH_ABBR[self.month]} {self.day}" if self.has_day_and_month else ""

    def to_dict(self) -> dict[str, Any]:
        return {"day": self.day, "month": self.month, "year": self.year}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PartialDate | None":
        return cls(data.get("day"), data.get("month"), data.get("year")) if data else None


@dataclass(frozen=True)
class DateReading:
    kind: str                         # "dates" | "year" | "skip" | "yes" | "no" | "unclear"
    start: PartialDate | None = None  # first date mentioned
    end: PartialDate | None = None    # second date mentioned (range or "from X to Y")
    year: int | None = None           # bare year


UNCLEAR = DateReading("unclear")


# ============================================================================================
# Reading text
# ============================================================================================
def _norm_year(text: str) -> int:
    value = int(text)
    if len(text) == 4:
        return value
    return 2000 + value if value <= 68 else 1900 + value


def _month(token: str) -> int:
    return MONTHS[token.lower().rstrip(".")]


def _numeric(a: int, b: int, year: int) -> PartialDate:
    """a/b/year: month-first, unless the first number can only be a day (a > 12)."""
    if a > 12 and b <= 12:
        return PartialDate(a, b, year)
    return PartialDate(b, a, year)


def _opt_year(token: str | None) -> int | None:
    return int(token) if token else None


# Each pattern: (regex, builder(match) -> list[PartialDate]). Earlier patterns win overlapping text.
_PATTERNS: list[tuple[re.Pattern[str], Any]] = [
    # 2026-01-11, 2026/1/11
    (re.compile(r"\b((?:19|20)\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b"),
     lambda m: [PartialDate(int(m[3]), int(m[2]), int(m[1]))]),
    # 7/19/26, 07-19-2026, 25/04/2026
    (re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4}|\d{2})\b"),
     lambda m: [_numeric(int(m[1]), int(m[2]), _norm_year(m[3]))]),
    # Nov 29 to Dec 6 2025  /  Dec 28 2025 - Jan 4 2026
    (re.compile(rf"\b{_M}\.?\s+(\d{{1,2}})(?:\s*,?\s*{_YEAR})?\s*{_TO}\s*{_M}\.?\s+(\d{{1,2}})(?:\s*,?\s*{_YEAR})?\b", _FLAGS),
     lambda m: [PartialDate(int(m[2]), _month(m[1]), _opt_year(m[3])),
                PartialDate(int(m[5]), _month(m[4]), _opt_year(m[6]))]),
    # 29 Nov to 6 Dec 2025
    (re.compile(rf"\b(\d{{1,2}})\s+(?:of\s+)?{_M}\.?(?:\s*,?\s*{_YEAR})?\s*{_TO}\s*(\d{{1,2}})\s+(?:of\s+)?{_M}\.?(?:\s*,?\s*{_YEAR})?\b", _FLAGS),
     lambda m: [PartialDate(int(m[1]), _month(m[2]), _opt_year(m[3])),
                PartialDate(int(m[4]), _month(m[5]), _opt_year(m[6]))]),
    # Jan 2-6, 2026  /  January 11 to 18 2026  (one month, compressed)
    (re.compile(rf"\b{_M}\.?\s+(\d{{1,2}})\s*{_TO}\s*(\d{{1,2}})(?:\s*,?\s*{_YEAR})?\b", _FLAGS),
     lambda m: [PartialDate(int(m[2]), _month(m[1]), _opt_year(m[4])),
                PartialDate(int(m[3]), _month(m[1]), _opt_year(m[4]))]),
    # 13-20 July 2026
    (re.compile(rf"\b(\d{{1,2}})\s*{_TO}\s*(\d{{1,2}})\s+(?:of\s+)?{_M}\.?(?:\s*,?\s*{_YEAR})?\b", _FLAGS),
     lambda m: [PartialDate(int(m[1]), _month(m[3]), _opt_year(m[4])),
                PartialDate(int(m[2]), _month(m[3]), _opt_year(m[4]))]),
    # January 11, 2026  /  Jan 10
    (re.compile(rf"\b{_M}\.?\s+(\d{{1,2}})(?:\s*,?\s*{_YEAR})?\b", _FLAGS),
     lambda m: [PartialDate(int(m[2]), _month(m[1]), _opt_year(m[3]))]),
    # 11 January 2026  /  11th of Jan
    (re.compile(rf"\b(\d{{1,2}})\s+(?:of\s+)?{_M}\.?(?:\s*,?\s*{_YEAR})?\b", _FLAGS),
     lambda m: [PartialDate(int(m[1]), _month(m[2]), _opt_year(m[3]))]),
]


def _strip_ordinals(text: str) -> str:
    return re.sub(r"(?<=\d)(?:st|nd|rd|th)\b", "", text, flags=re.IGNORECASE)


def _is_the_verb_may(text: str, match: re.Match[str]) -> bool:
    """'5 may be' is not May 5th: a bare 'may' needs a year or nothing after it to count as a month."""
    if "may" not in match.group(0).lower() or re.search(r"\d{4}", match.group(0)):
        return False
    following = text[match.end():].strip()
    return bool(following) and following[0].isalpha()


def find_dates(text: str) -> list[PartialDate]:
    """Every date in the text, in reading order. Ranges yield two entries. Impossible dates are dropped."""
    text = _strip_ordinals(text)
    taken: list[tuple[int, int]] = []
    found: list[tuple[int, list[PartialDate]]] = []
    for pattern, build in _PATTERNS:
        for match in pattern.finditer(text):
            span = match.span()
            if any(span[0] < end and start < span[1] for start, end in taken):
                continue
            if _is_the_verb_may(text, match):
                continue
            parts = build(match)
            if not all(p.is_possible for p in parts):
                continue
            taken.append(span)
            found.append((span[0], parts))
    dates = [p for _, parts in sorted(found, key=lambda item: item[0]) for p in parts]
    return _infer_years(dates)


def _infer_years(dates: list[PartialDate]) -> list[PartialDate]:
    """Within one answer a range shares its year: 'Nov 29 to Dec 6 2025', 'Dec 28 to Jan 4 2026'."""
    if len(dates) < 2:
        return dates
    first, second = dates[0], dates[1]
    if first.year is None and second.year is not None:
        year = second.year
        first = first.with_year(year)
        if first.is_full and second.is_full and date.fromisoformat(first.to_iso()) > date.fromisoformat(second.to_iso()):
            first = first.with_year(year - 1)                  # Dec 28 -> Jan 4 2026 started in 2025
    elif second.year is None and first.year is not None:
        year = first.year
        second = second.with_year(year)
        if first.is_full and second.is_full and date.fromisoformat(second.to_iso()) < date.fromisoformat(first.to_iso()):
            second = second.with_year(year + 1)                # Dec 28 2025 -> Jan 4 ends in 2026
    return [first, second, *dates[2:]]


def read_yes_no(text: str) -> bool | None:
    """True / False for an affirmative / negative reply, None if neither."""
    lowered = (text or "").lower().strip()
    if any(phrase in lowered for phrase in _YES_PHRASES):
        return True
    words = re.findall(r"[a-z']+", lowered)
    if not words:
        return None
    if words[0] in _YES_FIRST:
        return True
    if words[0] in _NO_FIRST:
        return False
    return None


def _says_skip(lowered: str) -> bool:
    if re.fullmatch(r"\W*(no|nope|nah)\W*", lowered):
        return True
    return any(re.search(rf"(?<![a-z']){re.escape(phrase)}(?![a-z'])", lowered) for phrase in SKIP_PHRASES)


def says_skip(text: str) -> bool:
    """True when the reply is a 'don't know / not sure / skip / no' (Kore's sentinel phrases)."""
    return _says_skip((text or "").lower())


def read_text(text: str) -> DateReading:
    """What did the customer say about a date? See the module docstring."""
    text = (text or "").strip()
    if not text:
        return UNCLEAR
    dates = find_dates(text)
    if dates:
        return DateReading("dates", start=dates[0], end=dates[1] if len(dates) > 1 else None)

    lowered = text.lower()
    years = re.findall(r"\b((?:19|20)\d{2})\b", lowered)
    words = re.findall(r"[a-z']+|\d+", lowered)
    if (len(years) == 1 and len(words) <= 6 and sum(w.isdigit() for w in words) == 1
            and not any(w in MONTHS for w in words)):          # "March 2026" names a month: not a bare year
        return DateReading("year", year=int(years[0]))

    if _says_skip(lowered):
        return DateReading("skip")
    answer = read_yes_no(text)
    if answer is not None:
        return DateReading("yes" if answer else "no")
    return UNCLEAR


# ============================================================================================
# Rules
# ============================================================================================
def utc_today() -> date:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).date()


def is_future(iso: str, today: date, tolerance_days: int = 1) -> bool:
    """After today. One day of tolerance so a ship in a time zone ahead of UTC is not rejected."""
    return date.fromisoformat(iso) > today + timedelta(days=tolerance_days)
