"""Vessel lookup stage of the Product Return dialog.

Ported Kore nodes:
  HD_VesselLookupAgent (aiassist)            -> VESSEL_SPEC (pre/post processors, prompt, tools)
  HD_TriggerAgenticAppForVesselData (service)-> the VesselLookupTool handler, now calling the real OSW
                                                vessel API (shared/osw.py) instead of the agentic app
  PC_Cruise_Entities (script)                -> save_cruise_entities
  Prompt "Vessel_Identification_Prompt"      -> prompts/vessel_identification.md (+ vessel_step0.md)

Deviations from the Kore JavaScript are marked with "DEVIATION".
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from models import Turn
from shared.agent_node import AgentSpec, AgentTool, end_orchestration_tool
from shared.osw import OswApi, Vessel
from shared.prompts import render

log = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
AGENT_NAME = "HD_VesselLookupAgent"
NO_DATA = "No vessel data found."          # Kore service post-processor's value when nothing matches
MAX_VESSELS_SHOWN = 50                     # a cruise line has ~30 ships and the user must see theirs: show them all
MAX_FAILED_LOOKUPS = 2

SENTINEL_VALUES = {"unknown", "not sure", "i don't know", "i dont know", "dont know",
                   "no idea", "n/a", "na", "none", "not applicable"}
VAGUE_TERMS = {"ship", "boat", "cruise", "the ship", "the vessel", "a ship", "vessel", "a cruise", "the cruise"}


def is_valid_string(val: Any) -> bool:
    if not val:
        return False
    s = str(val).lower().strip()
    return s not in SENTINEL_VALUES and s not in VAGUE_TERMS


def is_valid_vessel_id(vid: Any) -> bool:
    if not vid:
        return False
    s = str(vid).lower().strip()
    return s not in SENTINEL_VALUES and bool(re.fullmatch(r"\d+", s))


# --------------------------------------------------------------------------------------------
# Pre-processor (generativeAI.preProcessorScript)
# --------------------------------------------------------------------------------------------
def pre_process(turn: Turn) -> None:
    s, e = turn.session, turn.entities
    if not isinstance(s.get("vesselSkippedFields"), list):
        s["vesselSkippedFields"] = []
    if not isinstance(s.get("vesselLookupFailCount"), (int, float)):
        s["vesselLookupFailCount"] = 0
    s.setdefault("lastVesselAttempt", "")
    s.setdefault("lastCountedVesselValue", "")
    s.setdefault("vesselLookupInvoked", False)

    for field_name in ("ship_name", "cruise_line"):
        if is_valid_string(s.get(field_name)) and not is_valid_string(e.get(field_name)):
            e[field_name] = s[field_name]

    candidate = s.get("vessel_id")
    if is_valid_vessel_id(candidate):
        e["vessel_id"] = s["vessel_id"] = str(candidate)
    else:
        e.pop("vessel_id", None)
        s["vessel_id"] = None


# --------------------------------------------------------------------------------------------
# Post-processor (generativeAI.postProcessorScript), run on every VesselLookupTool result
# --------------------------------------------------------------------------------------------
def _set_vessel(turn: Turn, vid: Any, name: Any, cruise_line: Any) -> None:
    s, e = turn.session, turn.entities
    if is_valid_vessel_id(vid):
        e["vessel_id"] = s["vessel_id"] = str(vid)
    if is_valid_string(name):
        e["ship_name"] = s["ship_name"] = name
    if is_valid_string(cruise_line):
        e["cruise_line"] = s["cruise_line"] = cruise_line


def _first(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, re.I)
    return m.group(1).strip() if m else None


def post_process(turn: Turn, tool_text: str, user_text: str) -> None:
    s, e = turn.session, turn.entities
    if not isinstance(s.get("vesselSkippedFields"), list):
        s["vesselSkippedFields"] = []
    if not isinstance(s.get("vesselLookupFailCount"), (int, float)):
        s["vesselLookupFailCount"] = 0
    s.setdefault("lastVesselAttempt", "")
    s.setdefault("lastCountedVesselValue", "")

    multiple_found = False  # a list of candidate ships is NOT a failed lookup
    raw = tool_text or ""
    if raw:
        s["vesselLookupInvoked"] = True
        data: Any = None
        match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", raw)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                data = None

        # DEVIATION: a one-element JSON array is treated as a single vessel. The Kore script ignores it
        # (it only handles a bare object or an array longer than 1) and would count it as a failed lookup.
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
            data = data[0]

        if isinstance(data, dict):
            _set_vessel(turn,
                        data.get("vessel_id") or data.get("id") or "",
                        data.get("vessel_name") or data.get("ship_name") or "",
                        data.get("cruise_line") or data.get("fleet") or "")
        elif isinstance(data, list) and len(data) > 1:
            multiple_found = True
        elif data is None:
            # Fallback: free-text answer, extract with regexes.
            ids = (re.findall(r"Vessel\s*ID[^0-9]*(\d+)", raw, re.I)
                   + re.findall(r"\(ID\s*[:\-]?\s*(\d+)\)", raw, re.I)
                   + re.findall(r'"vessel_id"\s*:\s*"?(\d+)"?', raw, re.I))
            unique = list(dict.fromkeys(ids))
            if len(unique) == 1 and is_valid_vessel_id(unique[0]):
                name = (_first(r'\*{0,2}Vessel\s*Name\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*\{\}"]+)', raw)
                        or _first(r'"(?:vessel_name|ship_name)"\s*:\s*"([^"]+)"', raw))
                line = (_first(r'\*{0,2}(?:Fleet|Cruise\s*Line)\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*\{\}"]+)', raw)
                        or _first(r'"cruise_line"\s*:\s*"([^"]+)"', raw))
                _set_vessel(turn, unique[0], name, line)
            elif len(unique) > 1:
                multiple_found = True

    # Cap lookups at MAX_FAILED_LOOKUPS, then accept the user's value and move on (never ask a 3rd time).
    resolved_now = is_valid_vessel_id(e.get("vessel_id"))
    lookup_failed = bool(raw) and not resolved_now and not multiple_found
    if lookup_failed:
        attempted = (user_text or "").strip()
        if not attempted:
            attempted = _first(r"matching\s+['\"]?([^'\"]+?)['\"]?\s+(?:was|were)?\s*(?:not\s+)?found", raw) or ""
        already_counted = bool(attempted) and attempted.lower() == str(s.get("lastCountedVesselValue", "")).lower()
        if not already_counted:
            s["vesselLookupFailCount"] = (s.get("vesselLookupFailCount") or 0) + 1
            s["lastCountedVesselValue"] = attempted
            if is_valid_string(attempted):
                s["lastVesselAttempt"] = attempted
        if s["vesselLookupFailCount"] >= MAX_FAILED_LOOKUPS:
            final_name = (s["lastVesselAttempt"] if is_valid_string(s["lastVesselAttempt"])
                          else attempted if is_valid_string(attempted) else "")
            if final_name:
                e["ship_name"] = s["ship_name"] = final_name
            s["vesselForceContinue"] = True
            s["vesselCompleted"] = True
            s["conversationState"] = "COMPLETED"

    if is_valid_vessel_id(e.get("vessel_id")):
        s["vesselLookupFailCount"] = 0
        s["lastCountedVesselValue"] = ""
        s["vesselForceContinue"] = False
        if is_valid_string(e.get("ship_name")) or is_valid_string(e.get("cruise_line")):
            s["vesselCompleted"] = True
            s["conversationState"] = "COMPLETED"


# --------------------------------------------------------------------------------------------
# Prompt (Vessel_Identification_Prompt) and tools
# --------------------------------------------------------------------------------------------
def build_prompt(turn: Turn) -> str:
    s = turn.session
    ship = s.get("ship_name") if is_valid_string(s.get("ship_name")) else ""
    cruise = s.get("cruise_line") if is_valid_string(s.get("cruise_line")) else ""
    vessel_id = s.get("vessel_id") if is_valid_vessel_id(s.get("vessel_id")) else ""
    fail_count = int(s.get("vesselLookupFailCount") or 0)
    skipped = s.get("vesselSkippedFields") or []
    skipped_section = ("SKIPPED FIELDS (user could not provide — NEVER ask for these again):\n" + ", ".join(skipped)
                       if skipped else "SKIPPED FIELDS: none")
    force_continue = s.get("vesselForceContinue") is True or fail_count >= MAX_FAILED_LOOKUPS
    step0 = (PROMPTS_DIR / "vessel_step0.md").read_text(encoding="utf-8") if force_continue else ""
    template = (PROMPTS_DIR / "vessel_identification.md").read_text(encoding="utf-8")
    return render(template,
                  ship_name=ship or "(not yet known)",
                  cruise_line=cruise or "(not yet known)",
                  vessel_id=vessel_id or "(not yet resolved)",
                  fail_count=str(fail_count),
                  skipped_section=skipped_section,
                  force_continue_section=step0)


def vessels_to_tool_text(vessels: list[Vessel]) -> str:
    """The text the model (and post_process) receive: nothing, one vessel object, or a list of vessels.

    Same contract as the old agentic-app answer, so post_process is unchanged: one object resolves the
    vessel, several objects mean "ask which one", NO_DATA counts as a failed lookup.
    """
    rows = [{"vessel_id": v.id, "vessel_name": v.name, "cruise_line": v.cruise_line}
            for v in sorted(vessels, key=lambda v: v.name.lower())[:MAX_VESSELS_SHOWN]]   # A-Z is easier to scan
    if not rows:
        return NO_DATA
    return json.dumps(rows[0] if len(rows) == 1 else rows)


def make_tools(osw: OswApi):
    def factory(turn: Turn, on_end) -> list[AgentTool]:
        s = turn.session

        async def vessel_lookup(args: dict[str, Any]) -> str:
            text = vessels_to_tool_text(await osw.find_vessels(str(args.get("input", ""))))
            post_process(turn, text, turn.text)
            return text

        lookup = AgentTool(
            name="VesselLookupTool",  # Kore's tool is HD_VesselLookupTool, but its prompt calls it VesselLookupTool
            description="Fetch vessel details using ship name or cruise line",
            parameters={"type": "object",
                        "properties": {"input": {"type": "string", "description": "cruise line or ship name"}},
                        "required": ["input"]},
            handler=vessel_lookup)
        def guard() -> str | None:
            # Kore's "FIX #1": with nothing known, the ship never asked about and no lookup done yet,
            # end_orchestration is withdrawn so the model must ask. Evaluated at call time (see agent_node).
            if must_ask_ship_first(s):
                return "end_orchestration is not available yet. Ask the user: Which ship were you on during your cruise?"
            return None

        return [lookup, end_orchestration_tool(on_end, guard)]

    return factory


def must_ask_ship_first(s: dict[str, Any]) -> bool:
    no_entities = (not any(is_valid_string(s.get(k)) for k in ("ship_name", "cruise_line"))
                   and not is_valid_vessel_id(s.get("vessel_id")))
    return (no_entities and "ship_name" not in (s.get("vesselSkippedFields") or [])
            and not s.get("vesselForceContinue") and not s.get("vesselLookupInvoked")
            and int(s.get("vesselLookupFailCount") or 0) < MAX_FAILED_LOOKUPS)


def make_vessel_spec(osw: OswApi) -> AgentSpec:
    return AgentSpec(
        name=AGENT_NAME,
        pre_process=pre_process,
        build_prompt=build_prompt,
        make_tools=make_tools(osw),
        is_complete=lambda turn: bool(turn.session.get("vesselCompleted")),
        already_done=lambda turn: is_valid_vessel_id(turn.session.get("vessel_id")),
    )


# --------------------------------------------------------------------------------------------
# PC_Cruise_Entities (script node): copy the vessel entities into the long-lived usr_* session keys
# --------------------------------------------------------------------------------------------
def save_cruise_entities(turn: Turn) -> None:
    s, e = turn.session, turn.entities
    if e.get("ship_name"):
        s["usr_ship_name"] = e["ship_name"]
    if e.get("cruise_line"):
        s["usr_cruise_line"] = e["cruise_line"]
    if e.get("vessel_id"):
        s["usr_vessel_id"] = e["vessel_id"]
