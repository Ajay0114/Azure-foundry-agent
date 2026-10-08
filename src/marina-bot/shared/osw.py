"""Real OneSpaWorld (OSW) APIs: vessel information and ended-voyage itineraries.

Endpoints (from the Postman collections "OSW Dev Vessels Information API" / "Itinerary Voyages API"):

  GET {base}/info/vessels?filter=co(name,"<text>")                          vessel search by name
  GET {base}/info/cruiselines?filter=co(name,"<text>")                      cruise line search
  GET {base}/info/cruiselines/{id}/vessels                                  vessels of a cruise line
  GET {base}/info/cruiselines/{id}                                          one cruise line (name lookup)
  GET {base}/master/itinerary/vessels/{vesselId}/embarkation/date/{yyyymmdd}  voyage that started on the date
  GET {base}/master/itinerary/vessels/{vesselId}/any/date/{yyyymmdd}          voyages containing the date

Auth: OAuth2 client credentials against Azure Entra ID. The two APIs use different scopes.

Configuration (environment variables; NEVER commit values):
  OSW_BASE_URL            default https://oswbus-dev.onespaworld.com
  OSW_TOKEN_URL           Postman variable accessTokenUrl
  OSW_CLIENT_ID           Postman variable clientId
  OSW_CLIENT_SECRET       Postman variable clientSecret   (a secret: keep it in .env / Key Vault only)
  OSW_VESSELS_SCOPE       scope of the Vessels collection   (api://<id>/.default)
  OSW_ITINERARY_SCOPE     scope of the Itinerary collection (api://<id>/.default)

The response shapes were confirmed with probe_osw.py against the dev API (see the "Parsing" section). All
response parsing lives in that one section, so a change in the API means editing only those functions.
"""

import asyncio
import logging
import os
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import date
from typing import Any, Protocol

import httpx

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://oswbus-dev.onespaworld.com"
MAX_CRUISE_LINES_EXPANDED = 3     # when searching by cruise line, expand at most this many matching lines


# ============================================================================================
# Models and the interface the dialogs depend on
# ============================================================================================
@dataclass(frozen=True)
class Vessel:
    id: str
    name: str
    cruise_line: str = ""
    cruise_line_id: str = ""


@dataclass(frozen=True)
class Voyage:
    id: str                     # the API has no voyage id: "<vesselId>:<embarkation date>"
    start_date: str | None      # ISO YYYY-MM-DD (embarkation)
    end_date: str | None        # ISO YYYY-MM-DD (debarkation)
    days: int | None = None
    region: str = ""
    embark_port: str = ""
    debark_port: str = ""


@dataclass(frozen=True)
class VoyageMatch:
    kind: str                   # "exact" (a voyage embarked on that date), "nearest", or "none"
    voyage: Voyage | None = None


class OswApi(Protocol):
    async def find_vessels(self, query: str) -> list[Vessel]:
        """Vessels whose name contains `query`; if none, vessels of cruise lines matching `query`."""

    async def find_voyage(self, vessel_id: str, iso_date: str) -> VoyageMatch:
        """Voyage embarking on `iso_date`; otherwise the nearest voyage found through the any-date API."""


# ============================================================================================
# Parsing. Shapes confirmed against the dev API with probe_osw.py:
#   /info/vessels            -> [ {"id": 905, "name": "HARMONY OF THE SEAS", ...,
#                                  "cruiseline": {"id": 55, "code": "RCCL", "name": "ROYAL CARIBBEAN INTERNATIONAL"}} ]
#   /master/itinerary/...    -> [ {"vesselId": 905, "days": 8, "region": "CARIB W",
#                                  "embarkationDay":  {"date": "2026-01-11", "port": {"name": "GALVESTON", ...}, ...},
#                                  "debarkationDay":  {"date": "2026-01-18", "port": {"name": "GALVESTON", ...}, ...}} ]
# The cruise-line endpoints (/info/cruiselines...) have only been seen empty, so their records are assumed to
# carry "id" and "name"; vessels listed under a cruise line may lack the nested "cruiseline" object.
# ============================================================================================
def extract_items(payload: Any) -> list[dict[str, Any]]:
    """The records of a response: a bare list of objects, or a single object."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict) and payload:
        return [payload]
    return []


def parse_vessel(item: dict[str, Any], cruise_line: str = "") -> Vessel | None:
    vessel_id, name = item.get("id"), item.get("name")
    if vessel_id is None or not name:
        return None
    line = item.get("cruiseline") if isinstance(item.get("cruiseline"), dict) else {}
    line_id = line.get("id")
    return Vessel(id=str(vessel_id), name=str(name).strip(),
                  cruise_line=(cruise_line or str(line.get("name") or "")).strip(),
                  cruise_line_id=str(line_id) if line_id is not None else "")


def _iso(year: str, month: str, day: str) -> str | None:
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def to_iso_date(value: Any) -> str | None:
    """20260111 (int or str), '2026-01-11' or '2026-01-11T00:00:00Z' -> '2026-01-11'; otherwise None."""
    if value is None or isinstance(value, bool) or value == "":
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{8}", text):
        return _iso(text[:4], text[4:6], text[6:8])
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    return _iso(*m.groups()) if m else None


def _day(item: dict[str, Any], key: str) -> dict[str, Any]:
    day = item.get(key)
    return day if isinstance(day, dict) else {}


def _port(day: dict[str, Any]) -> str:
    port = day.get("port")
    return str(port.get("name") or "") if isinstance(port, dict) else ""


def parse_voyage(item: dict[str, Any]) -> Voyage | None:
    embark, debark = _day(item, "embarkationDay"), _day(item, "debarkationDay")
    start, end = to_iso_date(embark.get("date")), to_iso_date(debark.get("date"))
    if start is None:                      # a voyage without an embarkation date is unusable
        return None
    days = item.get("days")
    return Voyage(id=f"{item.get('vesselId', '')}:{start}", start_date=start, end_date=end,
                  days=days if isinstance(days, int) else None, region=str(item.get("region") or ""),
                  embark_port=_port(embark), debark_port=_port(debark))


def exact_match(voyages: list[Voyage], iso_date: str) -> Voyage | None:
    """The embarkation endpoint already filters by date, but we still verify the voyage really starts then."""
    return next((v for v in voyages if v.start_date == iso_date), None)


def pick_nearest(voyages: list[Voyage], iso_date: str) -> Voyage | None:
    """The voyage containing the date, else the one whose start or end is closest to it.

    Ties (e.g. the date is both one voyage's last day and the next one's first day) prefer a voyage the
    date is strictly inside, then the earlier one.
    """
    target = date.fromisoformat(iso_date)

    def distance(v: Voyage) -> tuple[int, int, str]:
        start = date.fromisoformat(v.start_date)
        end = date.fromisoformat(v.end_date) if v.end_date else start
        gap = 0 if start <= target <= end else min(abs((target - start).days), abs((target - end).days))
        return gap, 0 if start < target < end else 1, v.start_date

    dated = [v for v in voyages if v.start_date]
    return min(dated, key=distance) if dated else None


async def find_voyage_with(iso_date: str,
                           fetch_embarkation: Callable[[], Awaitable[list[Voyage]]],
                           fetch_any_date: Callable[[], Awaitable[list[Voyage]]]) -> VoyageMatch:
    """Embarkation API first; only if it has no match, the any-date API, then pick the nearest voyage."""
    embarked = await fetch_embarkation()
    hit = exact_match(embarked, iso_date)
    if hit:
        return VoyageMatch("exact", hit)
    near = pick_nearest(embarked + await fetch_any_date(), iso_date)
    return VoyageMatch("nearest", near) if near else VoyageMatch("none")


# ============================================================================================
# HTTP client
# ============================================================================================
@dataclass(frozen=True)
class OswConfig:
    base_url: str
    token_url: str
    client_id: str
    client_secret: str = ""
    vessels_scope: str = ""
    itinerary_scope: str = ""
    timeout: float = 20.0

    def __repr__(self) -> str:                      # never print the secret
        return f"OswConfig(base_url={self.base_url!r}, client_id={self.client_id!r}, client_secret='***')"

    @classmethod
    def from_env(cls) -> "OswConfig | None":
        values = {k: os.environ.get(k, "").strip() for k in (
            "OSW_TOKEN_URL", "OSW_CLIENT_ID", "OSW_CLIENT_SECRET", "OSW_VESSELS_SCOPE", "OSW_ITINERARY_SCOPE")}
        missing = [k for k, v in values.items() if not v]
        if missing:
            log.warning("OSW API not configured (missing: %s).", ", ".join(missing))
            return None
        return cls(base_url=os.environ.get("OSW_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
                   token_url=values["OSW_TOKEN_URL"], client_id=values["OSW_CLIENT_ID"],
                   client_secret=values["OSW_CLIENT_SECRET"], vessels_scope=values["OSW_VESSELS_SCOPE"],
                   itinerary_scope=values["OSW_ITINERARY_SCOPE"])


def rql_text(value: str) -> str:
    """Make free text safe inside an RQL string literal."""
    return re.sub(r'["\\]', "", value or "").strip()[:80]


class OswClient:
    def __init__(self, config: OswConfig, transport: httpx.AsyncBaseTransport | None = None):
        self._cfg = config
        self._transport = transport                  # tests inject httpx.MockTransport
        self._tokens: dict[str, tuple[str, float]] = {}
        self._token_lock = asyncio.Lock()
        self._line_names: dict[str, str] = {}

    # ---- low level -------------------------------------------------------------------------
    async def _token(self, client: httpx.AsyncClient, scope: str, force: bool = False) -> str:
        async with self._token_lock:
            cached = self._tokens.get(scope)
            if cached and not force and time.monotonic() < cached[1]:
                return cached[0]
            response = await client.post(self._cfg.token_url, data={
                "grant_type": "client_credentials", "client_id": self._cfg.client_id,
                "client_secret": self._cfg.client_secret, "scope": scope})
            response.raise_for_status()
            body = response.json()
            self._tokens[scope] = (body["access_token"],
                                   time.monotonic() + max(30, int(body.get("expires_in", 3600)) - 60))
            return self._tokens[scope][0]

    async def get_json(self, path: str, scope: str, params: dict[str, str] | None = None,
                       allow_404: bool = False) -> Any:
        async with httpx.AsyncClient(base_url=self._cfg.base_url, timeout=self._cfg.timeout,
                                     transport=self._transport) as client:
            for attempt in (0, 1):
                token = await self._token(client, scope, force=attempt == 1)
                response = await client.get(path, params=params, headers={"Authorization": f"Bearer {token}"})
                if response.status_code != 401 or attempt == 1:   # a 401 once: refresh the token and retry
                    break
        if response.status_code == 404 and allow_404:
            return None
        response.raise_for_status()
        return response.json() if response.content else None

    # ---- vessels ---------------------------------------------------------------------------
    async def _search_vessels(self, text: str) -> list[Vessel]:
        payload = await self.get_json("/info/vessels", self._cfg.vessels_scope,
                                      params={"filter": f'co(name,"{text}")'})
        return [v for v in (parse_vessel(i) for i in extract_items(payload)) if v]

    async def _cruise_line_name(self, line_id: str) -> str:
        if line_id not in self._line_names:
            payload = await self.get_json(f"/info/cruiselines/{line_id}", self._cfg.vessels_scope, allow_404=True)
            record = (extract_items(payload) or [{}])[0]
            self._line_names[line_id] = str(record.get("name") or "")
        return self._line_names[line_id]

    async def _vessels_of_cruise_lines(self, text: str) -> list[Vessel]:
        """Fallback when the user gave a cruise line ("Royal Caribbean") instead of a ship name."""
        payload = await self.get_json("/info/cruiselines", self._cfg.vessels_scope,
                                      params={"filter": f'co(name,"{text}")'})
        found: list[Vessel] = []
        for line in extract_items(payload)[:MAX_CRUISE_LINES_EXPANDED]:
            line_id, line_name = line.get("id"), line.get("name")
            if line_id is None:
                continue
            vessels = await self.get_json(f"/info/cruiselines/{line_id}/vessels", self._cfg.vessels_scope)
            found += [v for v in (parse_vessel(i, cruise_line=str(line_name or "")) for i in extract_items(vessels)) if v]
        return found

    async def find_vessels(self, query: str) -> list[Vessel]:
        text = rql_text(query)
        if not text:
            return []
        vessels = await self._search_vessels(text)       # the API search is case-insensitive
        if not vessels:
            vessels = await self._vessels_of_cruise_lines(text)
        # Fill in the cruise line name when the vessel record only carries its id.
        vessels = [replace(v, cruise_line=await self._cruise_line_name(v.cruise_line_id))
                   if not v.cruise_line and v.cruise_line_id else v for v in vessels]
        exact = [v for v in vessels if v.name.lower() == text.lower()]
        return exact or vessels

    # ---- itinerary -------------------------------------------------------------------------
    async def _voyages(self, path: str) -> list[Voyage]:
        payload = await self.get_json(path, self._cfg.itinerary_scope, allow_404=True)
        return [v for v in (parse_voyage(i) for i in extract_items(payload)) if v]

    async def find_voyage(self, vessel_id: str, iso_date: str) -> VoyageMatch:
        ymd = iso_date.replace("-", "")
        base = f"/master/itinerary/vessels/{vessel_id}"
        return await find_voyage_with(
            iso_date,
            lambda: self._voyages(f"{base}/embarkation/date/{ymd}"),
            lambda: self._voyages(f"{base}/any/date/{ymd}"))


def osw_from_env(fallback: OswApi) -> OswApi:
    """The real client when configured, otherwise the supplied stub (local development)."""
    config = OswConfig.from_env()
    if config is None:
        log.warning("Using the built-in STUB for vessel and voyage data (fake data).")
        return fallback
    return OswClient(config)
