import unittest
from types import SimpleNamespace

from pydantic import ValidationError

from shared.dates import UNCLEAR, DateReading, PartialDate
from shared.llm_dates import FoundryDateReader, LlmDatePart, LlmDateReading, to_reading


def reading(answer_type, start=None, end=None, year=None):
    return LlmDateReading(answer_type=answer_type, start=start, end=end, year=year)


class ToReadingTests(unittest.TestCase):
    def test_dates(self):
        r = to_reading(reading("dates", LlmDatePart(day=11, month=1, year=2026), LlmDatePart(day=18, month=1, year=2026)))
        self.assertEqual(r, DateReading("dates", PartialDate(11, 1, 2026), PartialDate(18, 1, 2026)))

    def test_a_partial_date_keeps_the_year_unknown(self):
        r = to_reading(reading("dates", LlmDatePart(day=10, month=1)))
        self.assertEqual(r.start, PartialDate(10, 1, None))

    def test_impossible_or_incomplete_dates_are_not_dates(self):
        self.assertEqual(to_reading(reading("dates", LlmDatePart(day=30, month=2, year=2026))), UNCLEAR)
        self.assertEqual(to_reading(reading("dates", LlmDatePart(month=3, year=2026))), UNCLEAR)      # no day
        self.assertEqual(to_reading(reading("dates")), UNCLEAR)

    def test_an_end_only_answer_becomes_the_start_slot(self):
        r = to_reading(reading("dates", None, LlmDatePart(day=18, month=1, year=2026)))
        self.assertEqual((r.start, r.end), (PartialDate(18, 1, 2026), None))

    def test_other_kinds(self):
        self.assertEqual(to_reading(reading("year", year=2026)), DateReading("year", year=2026))
        self.assertEqual(to_reading(reading("year")), UNCLEAR)
        for kind in ("skip", "yes", "no"):
            self.assertEqual(to_reading(reading(kind)).kind, kind)
        self.assertEqual(to_reading(reading("unclear")), UNCLEAR)

    def test_the_schema_rejects_out_of_range_numbers(self):
        with self.assertRaises(ValidationError):
            LlmDatePart(day=45, month=1)
        with self.assertRaises(ValidationError):
            LlmDatePart(day=1, month=13)
        with self.assertRaises(ValidationError):
            LlmDateReading(answer_type="maybe")


class FakeAgent:
    def __init__(self, value=None, error=None):
        self.value, self.error, self.calls = value, error, []

    async def run(self, prompt, stream=False, options=None):
        self.calls.append((prompt, options))
        if self.error:
            raise self.error
        return SimpleNamespace(value=self.value)


class ReaderTests(unittest.IsolatedAsyncioTestCase):
    async def test_asks_for_structured_output_and_converts_it(self):
        agent = FakeAgent(reading("dates", LlmDatePart(day=11, month=1, year=2026)))
        result = await FoundryDateReader(client=None, agent=agent)("the eleventh of january 2026", "start")
        self.assertEqual(result.start, PartialDate(11, 1, 2026))
        prompt, options = agent.calls[0]
        self.assertIs(options["response_format"], LlmDateReading)
        self.assertIn("start date", prompt)
        self.assertIn("the eleventh of january 2026", prompt)

    async def test_output_outside_the_schema_is_ignored(self):
        for error in (ValueError("bad json"), ValidationError.from_exception_data("x", [])):
            self.assertIsNone(await FoundryDateReader(client=None, agent=FakeAgent(error=error))("x", "end"))

    async def test_an_unparsed_value_is_ignored(self):
        self.assertIsNone(await FoundryDateReader(client=None, agent=FakeAgent(value=None))("x", "end"))


if __name__ == "__main__":
    unittest.main()
