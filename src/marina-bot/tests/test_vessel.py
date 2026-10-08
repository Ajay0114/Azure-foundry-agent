import json
import unittest

from dialogs.product_return.vessel import (
    build_prompt,
    is_valid_string,
    is_valid_vessel_id,
    make_tools,
    post_process,
    pre_process,
    save_cruise_entities,
    vessels_to_tool_text,
)
from models import Turn
from shared.osw import Vessel
from shared.osw_stub import StubOsw


def new_turn(text="", **session):
    return Turn(text=text, save_keys=[], session=dict(session), entities={})


class ValidityTests(unittest.TestCase):
    def test_strings(self):
        for bad in (None, "", "unknown", "N/A", "the ship", "Vessel", "a cruise"):
            self.assertFalse(is_valid_string(bad), bad)
        self.assertTrue(is_valid_string("Carnival Dream"))

    def test_vessel_ids_are_numeric_only(self):
        self.assertTrue(is_valid_vessel_id("1042"))
        self.assertTrue(is_valid_vessel_id(1042))
        for bad in (None, "", "unknown", "abc", "12a", "1042 "[:0]):
            self.assertFalse(is_valid_vessel_id(bad), bad)


class PreProcessTests(unittest.TestCase):
    def test_initialises_trackers_and_syncs_entities(self):
        t = new_turn(ship_name="Carnival Dream", cruise_line="the ship", vessel_id="1042")
        pre_process(t)
        self.assertEqual(t.entities["ship_name"], "Carnival Dream")
        self.assertNotIn("cruise_line", t.entities)          # vague value is not synced
        self.assertEqual(t.entities["vessel_id"], "1042")
        self.assertEqual(t.session["vesselLookupFailCount"], 0)
        self.assertEqual(t.session["vesselSkippedFields"], [])

    def test_invalid_vessel_id_is_cleared(self):
        t = new_turn(vessel_id="not-a-number")
        t.entities["vessel_id"] = "stale"
        pre_process(t)
        self.assertNotIn("vessel_id", t.entities)
        self.assertIsNone(t.session["vessel_id"])


class PostProcessTests(unittest.TestCase):
    def test_single_vessel_json(self):
        t = new_turn("Harmony of the Seas")
        post_process(t, json.dumps({"vessel_id": 1042, "vessel_name": "Harmony of the Seas",
                                    "cruise_line": "ROYAL CARIBBEAN INTERNATIONAL"}), t.text)
        self.assertEqual(t.entities["vessel_id"], "1042")
        self.assertEqual(t.session["vessel_id"], "1042")
        self.assertTrue(t.session["vesselCompleted"])
        self.assertEqual(t.session["vesselLookupFailCount"], 0)

    def test_one_element_array_is_a_single_vessel(self):
        t = new_turn("x")
        post_process(t, json.dumps([{"id": "7", "ship_name": "Carnival Dream", "fleet": "CARNIVAL"}]), "x")
        self.assertEqual(t.entities["vessel_id"], "7")
        self.assertTrue(t.session["vesselCompleted"])

    def test_several_vessels_is_not_a_failure(self):
        t = new_turn("Carnival")
        post_process(t, json.dumps([{"vessel_id": "1"}, {"vessel_id": "2"}]), "Carnival")
        self.assertEqual(t.session["vesselLookupFailCount"], 0)
        self.assertFalse(t.session.get("vesselCompleted"))
        self.assertTrue(t.session["vesselLookupInvoked"])

    def test_free_text_answer_with_one_id(self):
        t = new_turn("Carnival Dream")
        post_process(t, "**Vessel Name:** Carnival Dream\n**Vessel ID:** 2051\n**Fleet:** CARNIVAL", t.text)
        self.assertEqual(t.entities["vessel_id"], "2051")
        self.assertEqual(t.entities["ship_name"], "Carnival Dream")
        self.assertEqual(t.entities["cruise_line"], "CARNIVAL")
        self.assertTrue(t.session["vesselCompleted"])

    def test_free_text_answer_with_several_ids(self):
        t = new_turn("Carnival")
        post_process(t, "Vessel ID: 2051 (Dream) and Vessel ID: 2052 (Panorama)", "Carnival")
        self.assertEqual(t.session["vesselLookupFailCount"], 0)

    def test_failure_counts_once_per_value_then_caps_at_two(self):
        t = new_turn("Zorba")
        post_process(t, "No vessel data found.", "Zorba")
        post_process(t, "No vessel data found.", "Zorba")             # same value: de-duplicated
        self.assertEqual(t.session["vesselLookupFailCount"], 1)
        self.assertFalse(t.session.get("vesselCompleted"))

        post_process(t, "No vessel data found.", "Zorbb")             # a different value: 2nd failure
        self.assertEqual(t.session["vesselLookupFailCount"], 2)
        self.assertTrue(t.session["vesselCompleted"])
        self.assertTrue(t.session["vesselForceContinue"])
        self.assertEqual(t.entities["ship_name"], "Zorbb")
        self.assertEqual(t.session["conversationState"], "COMPLETED")

    def test_vague_attempt_is_not_stored_as_ship_name(self):
        t = new_turn("the ship")
        post_process(t, "No vessel data found.", "the ship")
        post_process(t, "No vessel data found.", "boat")
        self.assertNotIn("ship_name", t.entities)
        self.assertTrue(t.session["vesselCompleted"])


class PromptAndToolsTests(unittest.TestCase):
    def test_prompt_with_nothing_known(self):
        t = new_turn()
        pre_process(t)
        p = build_prompt(t)
        self.assertIn("ship_name:   (not yet known)", p)
        self.assertIn("vessel_id:   (not yet resolved)", p)
        self.assertIn("SKIPPED FIELDS: none", p)
        self.assertNotIn("LOOKUP LIMIT REACHED", p)
        self.assertNotIn("{{", p)

    def test_prompt_after_two_failures_has_step0_first(self):
        t = new_turn(vesselLookupFailCount=2, ship_name="Zorbb")
        p = build_prompt(t)
        self.assertIn("STEP 0 — LOOKUP LIMIT REACHED", p)
        self.assertLess(p.index("STEP 0"), p.index("STEP 1"))

class EndOrchestrationGuardTests(unittest.IsolatedAsyncioTestCase):
    async def end(self, turn):
        ended = []
        tools = {t.name: t for t in make_tools(StubOsw())(turn, ended.append)}
        reply = await tools["end_orchestration"].handler({"conv_status": "completed", "end_message": ""})
        return ended, reply, tools

    async def test_refused_when_nothing_known_and_ship_never_asked(self):
        t = new_turn(); pre_process(t)
        ended, reply, _ = await self.end(t)
        self.assertEqual(ended, [])
        self.assertIn("Which ship were you on", reply)

    async def test_allowed_once_something_is_known(self):
        t = new_turn(cruise_line="Carnival"); pre_process(t)
        ended, _, _ = await self.end(t)
        self.assertEqual(len(ended), 1)

    async def test_becomes_allowed_after_a_lookup_in_the_same_turn(self):
        t = new_turn("Carnival Dream"); pre_process(t)
        ended = []
        tools = {x.name: x for x in make_tools(StubOsw())(t, ended.append)}
        refused = await tools["end_orchestration"].handler({"conv_status": "completed"})
        self.assertEqual(ended, [])
        await tools["VesselLookupTool"].handler({"input": "Carnival Dream"})   # sets vesselLookupInvoked
        await tools["end_orchestration"].handler({"conv_status": "completed"})
        self.assertEqual(len(ended), 1)
        self.assertIn("not available yet", refused)


class VesselsToToolTextTests(unittest.TestCase):
    def test_none_one_many(self):
        self.assertEqual(vessels_to_tool_text([]), "No vessel data found.")
        one = json.loads(vessels_to_tool_text([Vessel("905", "HARMONY OF THE SEAS", "RCI")]))
        self.assertEqual(one, {"vessel_id": "905", "vessel_name": "HARMONY OF THE SEAS", "cruise_line": "RCI"})
        self.assertEqual(len(json.loads(vessels_to_tool_text([Vessel("1", "B"), Vessel("2", "A")]))), 2)

    def test_sorted_a_to_z_and_a_whole_cruise_line_is_not_truncated(self):
        ships = [Vessel(str(i), f"SHIP {chr(90 - i)}") for i in range(30)]       # 30 ships, listed Z..A by id
        rows = json.loads(vessels_to_tool_text(ships))
        self.assertEqual(len(rows), 30)
        names = [r["vessel_name"] for r in rows]
        self.assertEqual(names, sorted(names))


class SaveEntitiesTests(unittest.TestCase):
    def test_copies_only_present_values(self):
        t = new_turn(usr_ship_name="Old Name")
        t.entities.update({"cruise_line": "CARNIVAL", "vessel_id": "2051"})
        save_cruise_entities(t)
        self.assertEqual(t.session["usr_ship_name"], "Old Name")      # never overwritten with nothing
        self.assertEqual(t.session["usr_cruise_line"], "CARNIVAL")
        self.assertEqual(t.session["usr_vessel_id"], "2051")


if __name__ == "__main__":
    unittest.main()
