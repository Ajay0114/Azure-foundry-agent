"""Everything the dialogs need from the outside world, passed in once so tests can swap it."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from shared.agent_node import AgentRunner
from shared.dates import utc_today
from shared.flow import PromptRunner
from shared.llm_dates import DateReader
from shared.osw import OswApi


@dataclass
class Deps:
    run_prompt: PromptRunner   # prompt nodes: one-shot LLM call
    run_agent: AgentRunner     # agent nodes: tool-calling LLM loop
    osw: OswApi                # OneSpaWorld vessel + itinerary APIs (real client, or StubOsw offline)
    today: Callable[[], date] = utc_today        # the clock: tests pin it, production uses UTC
    read_dates: DateReader | None = None         # model fallback for dates the parser cannot read (optional)
