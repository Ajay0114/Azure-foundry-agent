"""LLM fallback for dates the deterministic parser (shared/dates.py) could not read.

The model never writes a date. It returns the pieces the customer actually said (day, month, year, each
optional) through a typed schema (Foundry structured output), and `to_reading` turns them into the same
`DateReading` the parser produces. Everything after that (calendar validity, "not in the future", ordering,
asking for a missing year) is ordinary code, so a model slip cannot create an impossible date.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from agent_framework import Agent
from pydantic import BaseModel, Field, ValidationError

from shared.dates import UNCLEAR, DateReading, PartialDate

log = logging.getLogger(__name__)

# (customer's reply, "start" | "end") -> a reading, or None when the model could not help
DateReader = Callable[[str, str], Awaitable[DateReading | None]]

INSTRUCTIONS = """You read a customer's reply in a chat about the dates of a past cruise.
The customer was asked for the cruise START date or END date. Report ONLY what the reply literally says.

answer_type:
- "dates":  the reply states one date, or two dates / a range. Put the first in `start` and the second, if any, in `end`.
- "year":   the reply is only a year (for example "2026").
- "skip":   the customer says they do not know or cannot remember.
- "yes" / "no": a plain yes or no.
- "unclear": anything else, including relative wording such as "last Tuesday", "two weeks ago" or "in the spring".

For each date give day, month (1-12) and year as separate numbers. Leave a part null when it was not stated.
NEVER guess a missing year, month or day. NEVER do date arithmetic. Month names and abbreviations in any
language are fine ("sept", "janvier"). A range such as "11-18 January 2026" means start 11 January 2026 and
end 18 January 2026. Numeric dates like 7/19/26 are month/day/year unless the first number is above 12."""


class LlmDatePart(BaseModel):
    day: int | None = Field(None, ge=1, le=31)
    month: int | None = Field(None, ge=1, le=12)
    year: int | None = Field(None, ge=1900, le=2100)


class LlmDateReading(BaseModel):
    answer_type: Literal["dates", "year", "skip", "yes", "no", "unclear"]
    start: LlmDatePart | None = None
    end: LlmDatePart | None = None
    year: int | None = Field(None, ge=1900, le=2100)


def _part(part: LlmDatePart | None) -> PartialDate | None:
    if part is None or part.day is None or part.month is None:
        return None                                         # a date needs at least a day and a month
    candidate = PartialDate(part.day, part.month, part.year)
    return candidate if candidate.is_possible else None     # the model cannot invent Feb 30


def to_reading(parsed: LlmDateReading) -> DateReading:
    """Validate the model's answer and convert it to the parser's type."""
    if parsed.answer_type == "dates":
        start, end = _part(parsed.start), _part(parsed.end)
        if start is None and end is not None:
            start, end = end, None
        return DateReading("dates", start=start, end=end) if start else UNCLEAR
    if parsed.answer_type == "year":
        return DateReading("year", year=parsed.year) if parsed.year else UNCLEAR
    if parsed.answer_type in ("skip", "yes", "no"):
        return DateReading(parsed.answer_type)
    return UNCLEAR


class FoundryDateReader:
    """DateReader backed by a Foundry chat client using structured output."""

    def __init__(self, client: Any):
        self._agent = Agent(client=client, name="date_reader", instructions=INSTRUCTIONS)

    async def __call__(self, text: str, field: str) -> DateReading | None:
        prompt = f"The customer was asked for the cruise {field} date. Their reply:\n{text}"
        try:
            response = await self._agent.run(prompt, stream=False, options={"response_format": LlmDateReading})
            parsed = response.value
        except (ValidationError, ValueError):
            log.warning("date reader returned something outside the schema; ignoring it")
            return None
        return to_reading(parsed) if isinstance(parsed, LlmDateReading) else None
