import json
import unittest

from dialogs.product_return.intake_scripts import (
    has_day,
    is_valid_entity_value,
    normalize_date,
    process_extracted_entities,
    set_initial_message,
)
from shared.session import DialogContext


def extraction(**fields):
    base = {
        "ship_name_candidate": None, "cruise_line_candidate": None,
        "start_date_raw": None, "end_date_raw": None, "service_date_raw": None,
        "unknown_indicated_fields": [], "extractionSuccessful": "success", "reason": "",
    }
    base.update(fields)
    return json.dumps(base)


class InitialMessageTests(unittest.TestCase):
    def test_stored_once(self):
        ctx = DialogContext()
        set_initial_message(ctx, "I want to return a product")
        set_initial_message(ctx, "my cabin is 8012")
        self.assertEqual(ctx.session["initialMessage"], "I want to return a product")


class DateTests(unittest.TestCase):
    def test_normalize(self):
        cases = {
            "2026-04-20": "2026-04-20",
            "2026/4/20": "2026-04-20",
            "January 11 2026": "2026-01-11",
            "11 January 2026": "2026-01-11",
            "March 3rd, 2025": "2025-03-03",
            "10/04/2026": "2026-10-04",   # both <= 12: month-first
            "25/04/2026": "2026-04-25",   # 25 can only be a day: DD-MM
            "04/25/2026": "2026-04-25",   # 25 can only be a day: MM-DD
            "Feb 30 2026": None,          # impossible day
            "Mar 17": None,               # no year
            "": None,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_date(raw), expected)

    def test_has_day(self):
        self.assertTrue(has_day("Mar 17"))
        self.assertTrue(has_day("January 11 2026"))
        self.assertTrue(has_day("2026-04-20"))
        self.assertFalse(has_day("April 2026"))
        self.assertFalse(has_day("last April"))
        self.assertFalse(has_day(None))

    def test_sentinels(self):
        for bad in (None, "", "  ", "unknown", "Not Sure", "the ship", "N/A"):
            with self.subTest(bad=bad):
                self.assertFalse(is_valid_entity_value(bad))
        self.assertTrue(is_valid_entity_value("Harmony of the Seas"))


class ProcessExtractedEntitiesTests(unittest.TestCase):
    def test_full_extraction(self):
        ctx = DialogContext()
        process_extracted_entities(ctx, extraction(
            ship_name_candidate="Harmony of the Seas", cruise_line_candidate="Royal Caribbean",
            start_date_raw="January 11 2026", end_date_raw="January 18 2026"))
        self.assertEqual(ctx.entities["ship_name"], "Harmony of the Seas")
        self.assertEqual(ctx.session["cruise_line"], "Royal Caribbean")
        self.assertEqual(ctx.entities["start_date"], "2026-01-11")
        self.assertEqual(ctx.entities["end_date"], "2026-01-18")
        self.assertNotIn("service_date", ctx.entities)

    def test_partial_date_kept_for_year_followup(self):
        ctx = DialogContext()
        process_extracted_entities(ctx, extraction(start_date_raw="Mar 17"))
        self.assertEqual(ctx.entities["start_date"], "Mar 17")

    def test_invalid_and_month_only_dates_rejected(self):
        ctx = DialogContext()
        process_extracted_entities(ctx, extraction(
            start_date_raw="Feb 30 2026", end_date_raw="April 2026"))
        self.assertEqual(ctx.entities, {})

    def test_unknown_fields_recorded_and_sentinels_dropped(self):
        ctx = DialogContext()
        process_extracted_entities(ctx, extraction(
            ship_name_candidate="the ship", unknown_indicated_fields=["ship_name"]))
        self.assertEqual(ctx.session["unknownIndicatedFields"], ["ship_name"])
        self.assertNotIn("ship_name", ctx.entities)

    def test_markdown_fenced_json(self):
        ctx = DialogContext()
        process_extracted_entities(ctx, "```json\n" + extraction(cruise_line_candidate="Carnival") + "\n```")
        self.assertEqual(ctx.entities["cruise_line"], "Carnival")

    def test_bad_or_missing_output_is_ignored(self):
        for bad in (None, "", "not json", "[1, 2]"):
            with self.subTest(bad=bad):
                ctx = DialogContext()
                process_extracted_entities(ctx, bad)
                self.assertEqual(ctx.entities, {})
                self.assertEqual(ctx.session, {})


if __name__ == "__main__":
    unittest.main()
