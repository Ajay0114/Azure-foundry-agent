import unittest
from datetime import date

from shared.dates import (DateReading, PartialDate, find_dates, is_future, read_text, read_yes_no)


def full(y, m, d):
    return PartialDate(d, m, y)


class PartialDateTests(unittest.TestCase):
    def test_full_and_possible(self):
        self.assertEqual(full(2026, 1, 11).to_iso(), "2026-01-11")
        self.assertTrue(PartialDate(29, 2, None).is_possible)        # leap day allowed with no year
        self.assertFalse(PartialDate(29, 2, 2026).is_possible)
        self.assertFalse(PartialDate(31, 4, 2026).is_possible)
        self.assertFalse(PartialDate(5, None, 2026).is_possible)
        self.assertIsNone(PartialDate(10, 1, None).to_iso())         # year unknown: not a full date

    def test_describe_and_round_trip(self):
        self.assertEqual(PartialDate(10, 1, None).describe(), "Jan 10")
        p = PartialDate(10, 1, 2026)
        self.assertEqual(PartialDate.from_dict(p.to_dict()), p)
        self.assertIsNone(PartialDate.from_dict(None))


class SingleDateTests(unittest.TestCase):
    def start_of(self, text):
        reading = read_text(text)
        self.assertEqual(reading.kind, "dates", text)
        return reading.start

    def test_formats_meaning_the_same_day(self):
        for text in ["January 11 2026", "Jan 11, 2026", "11 January 2026", "11th of January 2026", "11 jan 2026",
                     "2026-01-11", "2026/1/11", "1/11/2026", "01-11-26", "Jan 11th, 2026", "JANUARY 11TH 2026"]:
            self.assertEqual(self.start_of(text), full(2026, 1, 11), text)

    def test_numeric_is_month_first_unless_the_first_number_must_be_a_day(self):
        self.assertEqual(self.start_of("10/04/2026"), full(2026, 10, 4))
        self.assertEqual(self.start_of("25/04/2026"), full(2026, 4, 25))
        self.assertEqual(self.start_of("7/19/26"), full(2026, 7, 19))

    def test_two_digit_years(self):
        self.assertEqual(self.start_of("1/2/68").year, 2068)
        self.assertEqual(self.start_of("1/2/69").year, 1969)

    def test_date_inside_a_sentence(self):
        self.assertEqual(self.start_of("Star Princess 7/19/26 was the one"), full(2026, 7, 19))
        self.assertEqual(self.start_of("we sailed on March 3 2025 and loved it"), full(2025, 3, 3))

    def test_partial_date_keeps_the_year_unknown(self):
        self.assertEqual(self.start_of("Jan 10"), PartialDate(10, 1, None))
        self.assertEqual(self.start_of("the 5th of march"), PartialDate(5, 3, None))

    def test_the_verb_may_is_not_the_month(self):
        self.assertEqual(read_text("it was 2 may be a week ago").kind, "unclear")
        self.assertEqual(self.start_of("2 May 2026"), full(2026, 5, 2))
        self.assertEqual(self.start_of("May 2"), PartialDate(2, 5, None))

    def test_impossible_dates_are_not_dates(self):
        for text in ["Feb 30 2026", "31 April 2026", "13/45/2026", "0 January 2026"]:
            self.assertEqual(read_text(text).kind, "unclear", text)

    def test_month_only_or_year_month_is_not_a_date(self):
        self.assertEqual(read_text("March").kind, "unclear")
        self.assertEqual(read_text("March 2026").kind, "unclear")


class RangeTests(unittest.TestCase):
    def both(self, text):
        reading = read_text(text)
        self.assertEqual(reading.kind, "dates", text)
        self.assertIsNotNone(reading.end, text)
        return reading.start, reading.end

    def test_compressed_ranges_share_month_and_year(self):
        for text in ["January 11 to 18 2026", "Jan 11-18, 2026", "11-18 January 2026", "11 to 18 Jan 2026"]:
            self.assertEqual(self.both(text), (full(2026, 1, 11), full(2026, 1, 18)), text)

    def test_two_month_ranges(self):
        self.assertEqual(self.both("Nov 29 to Dec 6 2025"), (full(2025, 11, 29), full(2025, 12, 6)))
        self.assertEqual(self.both("29 Nov - 6 Dec 2025"), (full(2025, 11, 29), full(2025, 12, 6)))

    def test_two_separate_full_dates(self):
        self.assertEqual(self.both("jan 10 2026 to jan 16 2026"), (full(2026, 1, 10), full(2026, 1, 16)))
        self.assertEqual(self.both("from 7/19/26 until 7/26/26"), (full(2026, 7, 19), full(2026, 7, 26)))

    def test_year_rollover(self):
        self.assertEqual(self.both("Dec 28 to Jan 4 2026"), (full(2025, 12, 28), full(2026, 1, 4)))
        self.assertEqual(self.both("Dec 28 2025 to Jan 4"), (full(2025, 12, 28), full(2026, 1, 4)))

    def test_range_without_a_year_stays_partial_on_both_sides(self):
        start, end = self.both("Jan 2-6")
        self.assertEqual((start, end), (PartialDate(2, 1, None), PartialDate(6, 1, None)))

    def test_a_range_is_not_misread_as_its_trailing_date(self):
        start, _ = self.both("13-20 July 2026")
        self.assertEqual(start.day, 13)


class OtherKindsTests(unittest.TestCase):
    def test_year_only(self):
        for text in ["2026", "it was 2026", "in 2026.", "year 2025"]:
            self.assertEqual(read_text(text), DateReading("year", year=int(text[-5:-1] if text.endswith('.') else text[-4:])), text)
        self.assertEqual(read_text("1/2/2026").kind, "dates")                 # a full date, not a bare year

    def test_skip(self):
        for text in ["I don't know", "not sure", "No idea", "idk", "skip", "can't remember", "don't remember it",
                     "n/a", "no", "Nope.", "unsure"]:
            self.assertEqual(read_text(text).kind, "skip", text)

    def test_a_date_beats_a_skip_phrase(self):
        reading = read_text("not sure but i think Jan 11 2026")
        self.assertEqual((reading.kind, reading.start), ("dates", full(2026, 1, 11)))

    def test_yes_no(self):
        for text, kind in [("yes", "yes"), ("Yeah", "yes"), ("ok", "yes"), ("that's right", "yes"),
                           ("sure thing", "yes"), ("nope", "skip"), ("no thanks", "no")]:
            self.assertEqual(read_text(text).kind, kind, text)
        self.assertTrue(read_yes_no("Proceed please"))
        self.assertFalse(read_yes_no("No, that's wrong"))
        self.assertIsNone(read_yes_no("maybe"))
        self.assertIsNone(read_yes_no(""))

    def test_unclear(self):
        for text in ["", "   ", "hello there", "last tuesday", "maybe", "a while ago"]:
            self.assertEqual(read_text(text).kind, "unclear", text)


class RulesTests(unittest.TestCase):
    def test_future_has_one_day_of_tolerance(self):
        today = date(2026, 10, 7)
        self.assertFalse(is_future("2026-10-07", today))
        self.assertFalse(is_future("2026-10-08", today))
        self.assertTrue(is_future("2026-10-09", today))
        self.assertFalse(is_future("2026-01-11", today))

    def test_find_dates_returns_reading_order(self):
        self.assertEqual(find_dates("end Jan 18 2026, start Jan 11 2026"), [full(2026, 1, 18), full(2026, 1, 11)])


if __name__ == "__main__":
    unittest.main()
