"""End-to-end multi-turn tests of the real workflow graph with a fake LLM (no Azure needed)."""

import json
import re
import tempfile
import unittest
from datetime import date
from pathlib import Path

from shared.osw_stub import StubOsw
from models import TurnInput
from orchestrator import build_orchestrator
from shared.deps import Deps
from shared.state_store import FileStateStore

ASK_SHIP = "Which ship were you on during your cruise?"


TODAY = date(2026, 10, 7)          # the pinned test clock


def make_fake_llm(ship=None, cruise_line=None, start="January 11 2026", end="January 18 2026"):
    """Prompt-node LLM: classifier + the cruise-entity extraction prompt."""

    async def fake_llm(prompt: str) -> str:
        if prompt.startswith("You classify"):
            return "PRODUCT_RETURN" if "return" in prompt.lower().split("customer message:")[-1] else "OTHER"
        if "Extract cruise-related entity values" in prompt:
            return "```json\n" + json.dumps({
                "ship_name_candidate": ship, "cruise_line_candidate": cruise_line,
                "start_date_raw": start, "end_date_raw": end,
                "service_date_raw": None, "unknown_indicated_fields": [],
                "extractionSuccessful": "success", "reason": "test"}) + "\n```"
        raise AssertionError("unexpected prompt: " + prompt[:80])

    return fake_llm


async def fake_agent(system_prompt, history, user_input, tools):
    """Stands in for the vessel agent LLM by following the rules written in the Kore prompt."""
    by_name = {t.name: t for t in tools}

    def field(label):
        return re.search(rf"^{label}:\s+(.*)$", system_prompt, re.M).group(1).strip()

    async def end():
        await by_name["end_orchestration"].handler({"conv_status": "completed", "end_message": ""})
        return ""

    async def lookup(value):
        result = await by_name["VesselLookupTool"].handler({"input": value})
        if result.lstrip().startswith("{"):
            return await end()                                   # STEP 7: single vessel
        if result.lstrip().startswith("["):
            return "Which of these ships were you on?\nHarmony of the Seas\nWonder of the Seas"   # STEP 6
        return "I wasn't able to find a ship matching that name. Could you provide the full ship name?"  # 2A

    if "STEP 0 — LOOKUP LIMIT REACHED" in system_prompt:
        return await end()
    if not field("vessel_id").startswith("("):
        return await end()                                       # STEP 1

    last_bot = history[-1]["content"] if history and history[-1]["role"] == "assistant" else ""
    fails = int(re.search(r"failed_lookup_attempts: (\d+)", system_prompt).group(1))
    known = [v for v in (field("ship_name"), field("cruise_line")) if not v.startswith("(")]
    if fails > 0 or "Which of these ships" in last_bot or ASK_SHIP in last_bot:
        return await lookup(user_input)                          # the user just answered our question
    if known:
        return await lookup(known[0])                            # STEP 2: look up what we already know
    return ASK_SHIP                                              # STEP 3


class ConversationBase(unittest.IsolatedAsyncioTestCase):
    ship = None
    cruise_line = None
    start = "January 11 2026"        # what the extraction prompt finds in the first message
    end = "January 18 2026"
    read_dates = None

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = FileStateStore(Path(self._tmp.name))
        self.deps = Deps(run_prompt=make_fake_llm(self.ship, self.cruise_line, self.start, self.end),
                         run_agent=fake_agent, osw=StubOsw(), today=lambda: TODAY, read_dates=self.read_dates)

    def tearDown(self):
        self._tmp.cleanup()

    async def say(self, text: str, conversation: str = "conv-1") -> str:
        """One chat turn = one fresh workflow run, exactly like one hosted request."""
        wf = build_orchestrator(self.deps, self.store)
        # AgentNode logs an ERROR when its LLM/tool call raises and then skips ahead: never accept that silently.
        with self.assertNoLogs("shared.agent_node", level="ERROR"):
            result = await wf.run(TurnInput(text=text, load_keys=[conversation], save_keys=[conversation]))
        outputs = result.get_outputs()
        self.assertEqual(len(outputs), 1, outputs)
        return outputs[0]

    async def to_email_confirmed(self) -> str:
        """Drive the dialog through name + email; returns the reply to the final 'yes'."""
        await self.say("I want to return a product I bought")
        await self.say("John Smith")
        await self.say("john@example.com")
        return await self.say("yes")

    def saved(self):
        return self.store.load(["conv-1"])


class IntakeTests(ConversationBase):
    ship = "Harmony of the Seas"
    cruise_line = "Royal Caribbean"

    async def test_name_and_email_with_retries(self):
        r = await self.say("I want to return a product I bought")
        self.assertIn("full name", r)
        self.assertIn("Thanks for reaching out", r)

        self.assertIn("did not recognize the name", await self.say("Bob"))      # first name only
        r = await self.say("my name is John Smith")
        self.assertIn("*John Smith*", r)
        self.assertIn("did not recognize the email", await self.say("not an email"))
        r = await self.say("john@example.com")
        self.assertIn("is this the best email", r)
        self.assertIn("email address", await self.say("no"))                      # re-enter the email
        self.assertIn("john.smith@example.org", await self.say("john.smith@example.org"))
        self.assertIn("didn't catch that", await self.say("maybe"))               # neither yes nor no

        r = await self.say("Yes")                                                 # extraction -> vessel -> next
        self.assertIn("Cruise dates step complete", r)
        saved = self.saved()["session"]
        self.assertEqual(saved["piiEntities"]["emailId"], "john.smith@example.org")
        self.assertEqual(saved["initialMessage"], "I want to return a product I bought")
        self.assertIsNone(saved["active_dialog"])

    async def test_other_topics_use_fallback(self):
        r = await self.say("What time does the spa open?")
        self.assertIn("only help with product returns", r)
        self.assertFalse((self.store.load(["conv-1"]) or {}).get("session", {}).get("active_dialog"))

    async def test_conversations_are_isolated(self):
        await self.say("I want to return a product", "a")
        r = await self.say("John Smith", "b")          # conversation b never started a dialog
        self.assertIn("only help with product returns", r)


class VesselFoundInFirstMessage(ConversationBase):
    ship = "Harmony of the Seas"
    cruise_line = "Royal Caribbean"

    async def test_vessel_resolved_without_asking(self):
        r = await self.to_email_confirmed()
        self.assertIn("Cruise dates step complete", r)
        self.assertIn("1042", r)
        s = self.saved()["session"]
        self.assertEqual(s["usr_vessel_id"], "1042")
        self.assertEqual(s["usr_ship_name"], "Harmony of the Seas")
        self.assertEqual(s["usr_cruise_line"], "ROYAL CARIBBEAN INTERNATIONAL")   # canonical name from the engine
        self.assertTrue(s["vesselCompleted"])


class VesselAskedFor(ConversationBase):
    async def test_asks_for_ship_then_resolves(self):
        r = await self.to_email_confirmed()
        self.assertEqual(r, ASK_SHIP)
        self.assertEqual(self.saved()["session"]["dialog_step"], "pr_vessel_agent")   # paused inside the agent node

        r = await self.say("Carnival Dream")
        self.assertIn("Cruise dates step complete", r)
        self.assertEqual(self.saved()["session"]["usr_vessel_id"], "2051")


class VesselNotFoundTwice(ConversationBase):
    async def test_second_failure_accepts_the_value_and_moves_on(self):
        self.assertEqual(await self.to_email_confirmed(), ASK_SHIP)
        r = await self.say("Zorba")
        self.assertIn("wasn't able to find", r)
        self.assertEqual(self.saved()["session"]["vesselLookupFailCount"], 1)

        r = await self.say("Zorbb")                                  # 2nd failure: never ask a third time
        self.assertIn("Cruise dates step complete", r)
        s = self.saved()["session"]
        self.assertEqual(s["usr_ship_name"], "Zorbb")
        self.assertNotIn("usr_vessel_id", s)
        self.assertTrue(s["vesselForceContinue"])


class VesselCruiseLineWithSeveralShips(ConversationBase):
    cruise_line = "Carnival"

    async def test_multiple_results_are_not_a_failure(self):
        r = await self.to_email_confirmed()
        self.assertIn("Which of these ships", r)
        self.assertEqual(self.saved()["session"]["vesselLookupFailCount"], 0)

        r = await self.say("Carnival Dream")
        self.assertIn("Cruise dates step complete", r)
        self.assertEqual(self.saved()["session"]["usr_vessel_id"], "2051")


if __name__ == "__main__":
    unittest.main()
