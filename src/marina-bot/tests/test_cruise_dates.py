"""Multi-turn tests of the cruise start/end date collection against the real workflow graph.

The vessel is Harmony of the Seas (stub id 1042) which has voyages 2026-01-11..18 and 2026-01-18..25.
The test clock is 2026-10-07. The first message contains no dates unless a test says so.
"""

import unittest

from dialogs.product_return.cruise_dates import (MAX_FAILED_ATTEMPTS, MSG_ASK_CORRECT_START, MSG_FUTURE_END,
                                                 MSG_FUTURE_START, CruiseDatesState, msg_end_before_start,
                                                 msg_giving_up, msg_no_such_cruise, question, question_again,
                                                 question_year)
from shared.dates import DateReading, PartialDate
from shared.osw_stub import StubOsw
from tests.test_conversation import ASK_SHIP, ConversationBase


class DatesBase(ConversationBase):
    ship, cruise_line = "Harmony of the Seas", "Royal Caribbean"
    start = end = None                      # the first message mentions no dates

    async def at_start_question(self):
        reply = await self.to_email_confirmed()
        self.assertEqual(reply, question("start"))
        self.assertEqual(self.saved()["session"]["dialog_step"], "cd_ask_start")

    def dates(self):
        return CruiseDatesState.load(self.saved()["session"])

    def assertFinished(self, reply, start, end):
        self.assertIn("Cruise dates step complete", reply)
        saved = self.saved()
        self.assertEqual((saved["entities"].get("start_date"), saved["entities"].get("end_date")), (start, end))
        self.assertEqual((saved["session"].get("usr_start_date"), saved["session"].get("usr_end_date")), (start, end))
        self.assertTrue(saved["session"]["dateCompleted"])


class ExactMatch(DatesBase):
    async def test_end_date_comes_from_the_voyage_api(self):
        await self.at_start_question()
        self.assertFinished(await self.say("January 11 2026"), "2026-01-11", "2026-01-18")
        self.assertEqual(self.dates().lookup, "exact")

    async def test_a_guessed_end_date_never_overrides_the_api(self):
        await self.at_start_question()
        self.assertFinished(await self.say("11-20 January 2026"), "2026-01-11", "2026-01-18")

    async def test_date_given_inside_a_sentence(self):
        await self.at_start_question()
        self.assertFinished(await self.say("we sailed on 1/11/2026, it was great"), "2026-01-11", "2026-01-18")


class NearestVoyage(DatesBase):
    async def test_confirm_the_closest_sailing(self):
        await self.at_start_question()
        reply = await self.say("January 14 2026")
        self.assertIn("The requested sailing date is not available. The closest cruise itinerary is:", reply)
        for line in ("- Start Date: 2026-01-11", "- End Date: 2026-01-18", "- Duration: 8 days", "- Region: CARIB W",
                     "Please reply with *YES* or *NO*."):
            self.assertIn(line, reply)
        self.assertEqual(self.saved()["session"]["dialog_step"], "cd_confirm_nearest")
        self.assertFinished(await self.say("Yes"), "2026-01-11", "2026-01-18")

    async def test_no_with_a_different_date_is_validated_again(self):
        await self.at_start_question()
        await self.say("January 14 2026")
        self.assertFinished(await self.say("No, it was January 18 2026"), "2026-01-18", "2026-01-25")
        self.assertEqual(self.dates().rejected_starts, ["2026-01-14"])

    async def test_no_without_a_date_asks_again_and_refuses_the_rejected_date(self):
        await self.at_start_question()
        await self.say("January 14 2026")
        self.assertEqual(await self.say("no"), MSG_ASK_CORRECT_START)
        self.assertEqual(self.saved()["session"]["dialog_step"], "cd_ask_start")
        self.assertEqual(await self.say("January 14 2026"), msg_no_such_cruise("2026-01-14"))
        self.assertFinished(await self.say("January 18 2026"), "2026-01-18", "2026-01-25")

    async def test_unreadable_confirmation_is_asked_once_more_then_treated_as_no(self):
        await self.at_start_question()
        await self.say("January 14 2026")
        self.assertIn("Please reply with *YES* or *NO*.", await self.say("hmm"))
        self.assertEqual(self.saved()["session"]["dialog_step"], "cd_confirm_nearest")
        self.assertEqual(await self.say("dunno"), MSG_ASK_CORRECT_START)


class NoVoyageFound(DatesBase):
    async def test_start_is_kept_and_the_end_date_is_asked(self):
        await self.at_start_question()
        self.assertEqual(await self.say("June 1 2026"), question("end"))
        self.assertEqual(self.dates().lookup, "none")
        self.assertFinished(await self.say("June 8 2026"), "2026-06-01", "2026-06-08")

    async def test_end_before_start_and_future_end_are_rejected(self):
        await self.at_start_question()
        await self.say("June 1 2026")
        self.assertEqual(await self.say("May 20 2026"), msg_end_before_start("2026-06-01"))
        self.assertEqual(await self.say("January 1 2027"), MSG_FUTURE_END)
        self.assertFinished(await self.say("2026-06-08"), "2026-06-01", "2026-06-08")

    async def test_an_end_date_the_customer_already_gave_is_used_without_asking(self):
        await self.at_start_question()
        self.assertFinished(await self.say("June 1 to June 8 2026"), "2026-06-01", "2026-06-08")


class PartialDates(DatesBase):
    async def test_only_the_year_is_asked_for(self):
        await self.at_start_question()
        reply = await self.say("Jan 11")
        self.assertEqual(reply, question_year("start", PartialDate(11, 1, None)))
        self.assertEqual(self.saved()["session"]["dialog_step"], "cd_ask_start")
        self.assertFinished(await self.say("2026"), "2026-01-11", "2026-01-18")

    async def test_a_range_without_a_year_asks_once_and_the_year_covers_both(self):
        await self.at_start_question()
        self.assertIn("What year did your cruise start on Jan 11?", await self.say("Jan 11-18"))
        self.assertFinished(await self.say("it was 2026"), "2026-01-11", "2026-01-18")

    async def test_a_year_with_no_date_is_not_an_answer(self):
        await self.at_start_question()
        self.assertEqual(await self.say("2026"), question_again("start"))

    async def test_first_message_with_a_partial_date_asks_for_the_year(self):
        self.start = "Mar 17"
        self.deps.run_prompt = __import__("tests.test_conversation", fromlist=["x"]).make_fake_llm(
            self.ship, self.cruise_line, "Mar 17", None)
        reply = await self.to_email_confirmed()
        self.assertEqual(reply, question_year("start", PartialDate(17, 3, None)))


class Rejections(DatesBase):
    async def test_future_start_date(self):
        await self.at_start_question()
        self.assertEqual(await self.say("December 25 2026"), MSG_FUTURE_START)
        self.assertFinished(await self.say("January 11 2026"), "2026-01-11", "2026-01-18")

    async def test_impossible_date_is_not_a_date(self):
        await self.at_start_question()
        self.assertEqual(await self.say("February 30 2026"), question_again("start"))

    async def test_future_date_from_the_first_message_is_explained_before_asking(self):
        self.deps.run_prompt = __import__("tests.test_conversation", fromlist=["x"]).make_fake_llm(
            self.ship, self.cruise_line, "December 25 2026", None)
        reply = await self.to_email_confirmed()
        self.assertEqual(reply, MSG_FUTURE_START + "\n\n" + question("start"))


class Skips(DatesBase):
    async def test_dont_know_skips_the_field_and_moves_on(self):
        await self.at_start_question()
        self.assertEqual(await self.say("I don't know"), question("end"))     # no validation without a start date
        self.assertIn("start", self.dates().skipped)
        reply = await self.say("not sure")
        self.assertFinished(reply, None, None)
        self.assertEqual(self.dates().skipped, ["start", "end"])

    async def test_a_plain_no_to_a_date_question_is_a_skip(self):
        await self.at_start_question()
        self.assertEqual(await self.say("no"), question("end"))

    async def test_gives_up_after_repeated_unreadable_replies(self):
        await self.at_start_question()
        for _ in range(MAX_FAILED_ATTEMPTS - 1):
            self.assertEqual(await self.say("blah blah"), question_again("start"))
        reply = await self.say("???")
        self.assertEqual(reply, msg_giving_up("start") + "\n\n" + question("end"))
        self.assertEqual(self.dates().skipped, ["start"])


class FirstMessageHadDates(DatesBase):
    start, end = "January 11 2026", "January 18 2026"

    async def test_no_questions_when_the_voyage_matches(self):
        reply = await self.to_email_confirmed()
        self.assertFinished(reply, "2026-01-11", "2026-01-18")
        self.assertEqual(self.dates().lookup, "exact")


class NoVessel(DatesBase):
    ship = cruise_line = None

    async def test_dates_are_collected_without_validation(self):
        self.assertEqual(await self.to_email_confirmed(), ASK_SHIP)
        await self.say("Zorba")
        reply = await self.say("Zorbb")                       # accepted after the second failed lookup
        self.assertEqual(reply, question("start"))
        self.assertEqual(await self.say("January 11 2026"), question("end"))   # nothing to validate against
        self.assertFinished(await self.say("January 18 2026"), "2026-01-11", "2026-01-18")
        self.assertEqual(self.dates().lookup, "")


class VoyageApiDown(DatesBase):
    async def test_conversation_continues_and_asks_for_the_end_date(self):
        class Broken(StubOsw):
            async def find_voyage(self, vessel_id, iso_date):
                raise ConnectionError("down")

        self.deps.osw = Broken()
        await self.at_start_question()
        with self.assertLogs("dialogs.product_return.cruise_dates", level="ERROR"):    # logged, not swallowed
            self.assertEqual(await self.say("January 11 2026"), question("end"))
        self.assertEqual(self.dates().lookup, "unavailable")
        self.assertFinished(await self.say("January 18 2026"), "2026-01-11", "2026-01-18")


class ModelFallback(DatesBase):
    async def test_only_called_when_the_parser_cannot_read_the_reply(self):
        calls = []

        async def read_dates(text, field):
            calls.append((text, field))
            return DateReading("dates", start=PartialDate(11, 1, 2026))

        self.deps.read_dates = read_dates
        await self.at_start_question()
        reply = await self.say("the eleventh of january twenty twenty six")
        self.assertFinished(reply, "2026-01-11", "2026-01-18")
        self.assertEqual(calls, [("the eleventh of january twenty twenty six", "start")])

    async def test_parseable_replies_never_reach_the_model(self):
        async def read_dates(text, field):
            raise AssertionError("the parser should have handled this")

        self.deps.read_dates = read_dates
        await self.at_start_question()
        self.assertFinished(await self.say("January 11 2026"), "2026-01-11", "2026-01-18")

    async def test_a_model_failure_is_treated_as_unclear(self):
        async def read_dates(text, field):
            raise TimeoutError("model down")

        self.deps.read_dates = read_dates
        await self.at_start_question()
        with self.assertLogs("dialogs.product_return.cruise_dates", level="ERROR"):
            self.assertEqual(await self.say("sometime in spring"), question_again("start"))

    async def test_the_model_cannot_make_an_impossible_date_pass(self):
        async def read_dates(text, field):
            return DateReading("dates", start=PartialDate(30, 2, 2026))      # code, not the model, validates

        self.deps.read_dates = read_dates
        await self.at_start_question()
        # PartialDate(30, 2, 2026).to_iso() is None, so it can never become the start date.
        reply = await self.say("the thirtieth of february")
        self.assertNotIn("Cruise dates step complete", reply)
        self.assertIsNone(self.dates().start)


class StateTests(unittest.TestCase):
    def test_round_trip_and_unknown_keys_are_ignored(self):
        st = CruiseDatesState(start="2026-01-11", skipped=["end"], partial={"start": {"day": 1, "month": 2, "year": None}})
        session = {}
        st.save(session)
        session["cruiseDates"]["someFutureField"] = 1                  # an older bot reading newer state
        self.assertEqual(CruiseDatesState.load(session), st)

    def test_empty_session_gives_a_fresh_state(self):
        self.assertEqual(CruiseDatesState.load({}), CruiseDatesState())


if __name__ == "__main__":
    unittest.main()
