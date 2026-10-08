"""Tests for shared/osw.py.

The fixtures are REAL response shapes captured with probe_osw.py from the dev API (vessel 905, Harmony of
the Seas, January 2026), trimmed to the interesting fields. The cruise-line endpoints were only seen empty,
so their fixtures are assumed shapes and marked as such.
"""

import unittest
from urllib.parse import parse_qsl

import httpx

from shared.osw import (OswClient, OswConfig, Vessel, Voyage, exact_match, extract_items, parse_vessel,
                        parse_voyage, pick_nearest, rql_text, to_iso_date)
from shared.osw_stub import StubOsw

CONFIG = OswConfig(base_url="https://osw.test", token_url="https://login.test/token", client_id="cid",
                   client_secret="TOP-SECRET", vessels_scope="api://vessels/.default",
                   itinerary_scope="api://itinerary/.default")

# ---- real shapes (trimmed) ----------------------------------------------------------------------
HARMONY = {"id": 905, "imo": 9682875, "code": "HOS", "name": "HARMONY OF THE SEAS", "active": True,
           "cruiseline": {"id": 55, "code": "RCCL", "name": "ROYAL CARIBBEAN INTERNATIONAL"}}


def voyage(start, end, port="GALVESTON", days=8, vessel_id=905):
    return {"vesselId": vessel_id, "isCurrent": False, "days": days, "region": "CARIB W",
            "embarkationDay": {"vesselId": vessel_id, "date": start, "dayType": "embarkation",
                               "departure": f"{start}T15:00:00", "port": {"id": 675, "code": "GLV", "name": port},
                               "country": {"id": 493, "name": "USA"}},
            "debarkationDay": {"vesselId": vessel_id, "date": end, "dayType": "debarkation",
                               "arrival": f"{end}T07:00:00", "port": {"id": 675, "code": "GLV", "name": port},
                               "country": {"id": 493, "name": "USA"}}}


JAN_04_11 = voyage("2026-01-04", "2026-01-11")
JAN_11_18 = voyage("2026-01-11", "2026-01-18")
BASE = "/master/itinerary/vessels/905"


class FakeOsw:
    """Mock HTTP server for OswClient. `routes` maps a path to a JSON body (or an int status)."""

    def __init__(self, routes):
        self.routes, self.calls, self.token_requests = routes, [], []
        self.client = OswClient(CONFIG, transport=httpx.MockTransport(self.handle))

    def handle(self, request: httpx.Request) -> httpx.Response:
        if str(request.url) == CONFIG.token_url:
            form = dict(parse_qsl(request.content.decode()))
            self.token_requests.append(form)
            return httpx.Response(200, json={"access_token": "tok-" + form["scope"].split("/")[2], "expires_in": 3600})
        self.calls.append((request.url.path, request.url.params.get("filter"), request.headers.get("authorization")))
        body = self.routes.get(request.url.path)
        if isinstance(body, int):
            return httpx.Response(body)
        return httpx.Response(200, json=body) if body is not None else httpx.Response(404)


class ParsingTests(unittest.TestCase):
    def test_extract_items(self):
        self.assertEqual(extract_items([{"id": 1}, "junk"]), [{"id": 1}])
        self.assertEqual(extract_items({"id": 5}), [{"id": 5}])
        for empty in (None, "", [], {}):
            self.assertEqual(extract_items(empty), [])

    def test_parse_real_vessel(self):
        self.assertEqual(parse_vessel(HARMONY),
                         Vessel("905", "HARMONY OF THE SEAS", "ROYAL CARIBBEAN INTERNATIONAL", "55"))

    def test_parse_vessel_edge_cases(self):
        self.assertEqual(parse_vessel({"id": 1, "name": " X "}), Vessel("1", "X", "", ""))      # no cruise line
        self.assertEqual(parse_vessel({"id": 1, "name": "X"}, cruise_line="CUNARD").cruise_line, "CUNARD")
        self.assertIsNone(parse_vessel({"name": "no id"}))
        self.assertIsNone(parse_vessel({"id": 3}))

    def test_parse_real_voyage(self):
        self.assertEqual(parse_voyage(JAN_11_18),
                         Voyage("905:2026-01-11", "2026-01-11", "2026-01-18", 8, "CARIB W", "GALVESTON", "GALVESTON"))

    def test_parse_voyage_edge_cases(self):
        self.assertIsNone(parse_voyage({"vesselId": 905, "days": 8}))                     # no embarkation day
        self.assertIsNone(parse_voyage({"vesselId": 1, "embarkationDay": {"date": "2026-01-11"}}).end_date)

    def test_dates(self):
        for raw, iso in [(20260111, "2026-01-11"), ("20260111", "2026-01-11"), ("2026-01-11", "2026-01-11"),
                         ("2026-01-11T15:00:00", "2026-01-11"), (None, None), ("", None), ("Jan 11", None),
                         (20261340, None), (True, None)]:
            self.assertEqual(to_iso_date(raw), iso, raw)

    def test_exact_and_nearest(self):
        a, b = parse_voyage(JAN_11_18), parse_voyage(voyage("2026-02-01", "2026-02-08"))
        self.assertEqual(exact_match([a, b], "2026-01-11"), a)
        self.assertIsNone(exact_match([a, b], "2026-01-12"))
        self.assertEqual(pick_nearest([a, b], "2026-01-14"), a)     # inside a voyage
        self.assertEqual(pick_nearest([a, b], "2026-01-29"), b)     # between: 3 days from Feb 1 vs 11 from Jan 18
        self.assertEqual(pick_nearest([a, b], "2026-01-20"), a)     # 2 days after Jan 18
        self.assertIsNone(pick_nearest([], "2026-01-20"))

    def test_boundary_tie_prefers_the_voyage_the_date_is_inside(self):
        ending, starting = parse_voyage(JAN_04_11), parse_voyage(JAN_11_18)
        both = [ending, starting]
        self.assertEqual(pick_nearest(both, "2026-01-11"), ending)      # touches both: earlier wins
        self.assertEqual(pick_nearest(both, "2026-01-08"), ending)      # strictly inside
        self.assertEqual(pick_nearest(both, "2026-01-15"), starting)

    def test_rql_escaping(self):
        self.assertEqual(rql_text('Harmony "of" the\\Seas'), "Harmony of theSeas")
        self.assertEqual(rql_text("  x  "), "x")


class AuthTests(unittest.IsolatedAsyncioTestCase):
    async def test_token_per_scope_is_cached_and_sent_as_bearer(self):
        fake = FakeOsw({"/info/vessels": [HARMONY], f"{BASE}/embarkation/date/20260111": [JAN_11_18]})
        await fake.client.find_vessels("Harmony")
        await fake.client.find_vessels("Harmony")
        await fake.client.find_voyage("905", "2026-01-11")
        self.assertEqual([r["scope"] for r in fake.token_requests],
                         ["api://vessels/.default", "api://itinerary/.default"])   # one token per scope
        self.assertEqual(fake.calls[0][2], "Bearer tok-vessels")
        self.assertEqual(fake.calls[-1][2], "Bearer tok-itinerary")

    def test_secret_never_in_repr(self):
        self.assertNotIn("TOP-SECRET", repr(CONFIG))

    async def test_401_refreshes_the_token_once(self):
        state = {"n": 0}

        def handle(request):
            if str(request.url) == CONFIG.token_url:
                state["n"] += 1
                return httpx.Response(200, json={"access_token": f"t{state['n']}", "expires_in": 3600})
            return httpx.Response(401) if request.headers["authorization"] == "Bearer t1" else httpx.Response(
                200, json=[HARMONY])

        client = OswClient(CONFIG, transport=httpx.MockTransport(handle))
        self.assertEqual((await client.find_vessels("Harmony"))[0].id, "905")
        self.assertEqual(state["n"], 2)


class VesselSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_sends_the_documented_filter_and_extracts_id_name_and_cruise_line(self):
        fake = FakeOsw({"/info/vessels": [HARMONY]})
        found = await fake.client.find_vessels("Harmony")
        self.assertEqual(found, [Vessel("905", "HARMONY OF THE SEAS", "ROYAL CARIBBEAN INTERNATIONAL", "55")])
        self.assertEqual(fake.calls[0][:2], ("/info/vessels", 'co(name,"Harmony")'))
        self.assertEqual(len(fake.calls), 1)                  # no cruise-line fallback needed

    async def test_exact_name_wins_over_partial_matches(self):
        other = {**HARMONY, "id": 906, "name": "HARMONY OF THE SEAS II"}
        fake = FakeOsw({"/info/vessels": [other, HARMONY]})
        self.assertEqual([v.id for v in await fake.client.find_vessels("harmony of the seas")], ["905"])

    async def test_several_partial_matches_are_all_returned(self):
        wonder = {**HARMONY, "id": 907, "name": "WONDER OF THE SEAS"}
        fake = FakeOsw({"/info/vessels": [HARMONY, wonder]})
        self.assertEqual([v.id for v in await fake.client.find_vessels("of the seas")], ["905", "907"])

    async def test_cruise_line_fallback(self):                # cruise-line shapes are ASSUMED (only seen empty)
        fake = FakeOsw({
            "/info/vessels": [],
            "/info/cruiselines": [{"id": 55, "code": "RCCL", "name": "ROYAL CARIBBEAN INTERNATIONAL"}],
            "/info/cruiselines/55/vessels": [{"id": 905, "name": "HARMONY OF THE SEAS"},
                                             {"id": 907, "name": "WONDER OF THE SEAS"}]})
        found = await fake.client.find_vessels("Royal Caribbean")
        self.assertEqual([(v.id, v.cruise_line) for v in found],
                         [("905", "ROYAL CARIBBEAN INTERNATIONAL"), ("907", "ROYAL CARIBBEAN INTERNATIONAL")])

    async def test_cruise_line_name_looked_up_when_the_record_only_has_an_id(self):
        record = {"id": 1, "name": "X", "cruiseline": {"id": 33}}
        fake = FakeOsw({"/info/vessels": [record], "/info/cruiselines/33": {"id": 33, "name": "CARNIVAL"}})
        self.assertEqual((await fake.client.find_vessels("X"))[0].cruise_line, "CARNIVAL")

    async def test_nothing_found_and_blank_input(self):
        fake = FakeOsw({"/info/vessels": [], "/info/cruiselines": []})
        self.assertEqual(await fake.client.find_vessels("Zorba"), [])
        self.assertEqual(await fake.client.find_vessels('  "  '), [])
        self.assertEqual(len(fake.calls), 2)                  # Zorba: vessels, then cruise lines; blank: nothing

    async def test_server_error_propagates(self):
        fake = FakeOsw({"/info/vessels": 500})
        with self.assertRaises(httpx.HTTPStatusError):
            await fake.client.find_vessels("Harmony")


class VoyageTests(unittest.IsolatedAsyncioTestCase):
    async def test_exact_embarkation_does_not_call_any_date(self):
        fake = FakeOsw({f"{BASE}/embarkation/date/20260111": [JAN_11_18]})
        match = await fake.client.find_voyage("905", "2026-01-11")
        self.assertEqual(match.kind, "exact")
        self.assertEqual((match.voyage.start_date, match.voyage.end_date, match.voyage.embark_port),
                         ("2026-01-11", "2026-01-18", "GALVESTON"))
        self.assertFalse(any("/any/" in c[0] for c in fake.calls))

    async def test_no_embarkation_falls_back_to_any_date_and_picks_the_nearest(self):
        fake = FakeOsw({f"{BASE}/embarkation/date/20260114": [],                 # nothing embarked that day
                        f"{BASE}/any/date/20260114": [JAN_11_18]})
        match = await fake.client.find_voyage("905", "2026-01-14")
        self.assertEqual((match.kind, match.voyage.start_date), ("nearest", "2026-01-11"))
        self.assertEqual([c[0] for c in fake.calls][-2:],
                         [f"{BASE}/embarkation/date/20260114", f"{BASE}/any/date/20260114"])

    async def test_404_from_the_embarkation_endpoint_means_no_match(self):
        fake = FakeOsw({f"{BASE}/any/date/20260114": [JAN_11_18]})               # embarkation route -> 404
        self.assertEqual((await fake.client.find_voyage("905", "2026-01-14")).kind, "nearest")

    async def test_an_embarkation_on_a_different_date_is_not_accepted_as_exact(self):
        fake = FakeOsw({f"{BASE}/embarkation/date/20260112": [JAN_11_18], f"{BASE}/any/date/20260112": []})
        match = await fake.client.find_voyage("905", "2026-01-12")
        self.assertEqual((match.kind, match.voyage.start_date), ("nearest", "2026-01-11"))

    async def test_real_probe_case_two_voyages_around_the_date(self):
        """2026-01-11 is the last day of one voyage and the first day of the next (seen with the real API)."""
        fake = FakeOsw({f"{BASE}/embarkation/date/20260111": [JAN_11_18],
                        f"{BASE}/any/date/20260111": [JAN_04_11, JAN_11_18]})
        self.assertEqual((await fake.client.find_voyage("905", "2026-01-11")).voyage.start_date, "2026-01-11")

    async def test_nothing_anywhere(self):
        fake = FakeOsw({f"{BASE}/any/date/20260301": []})
        self.assertEqual((await fake.client.find_voyage("905", "2026-03-01")).kind, "none")


class StubParityTests(unittest.IsolatedAsyncioTestCase):
    """The offline stub must behave like the client so dialog tests mean something."""

    async def test_stub_vessels(self):
        stub = StubOsw()
        self.assertEqual([v.id for v in await stub.find_vessels("Harmony of the Seas")], ["1042"])
        self.assertEqual(len(await stub.find_vessels("Carnival")), 2)
        self.assertEqual(len(await stub.find_vessels("royal caribbean")), 2)       # cruise-line fallback
        self.assertEqual(await stub.find_vessels("Zorba"), [])

    async def test_stub_voyages(self):
        stub = StubOsw()
        self.assertEqual((await stub.find_voyage("1042", "2026-01-11")).kind, "exact")
        self.assertEqual((await stub.find_voyage("1042", "2026-01-14")).voyage.id, "9001")
        self.assertEqual((await stub.find_voyage("1042", "2026-06-01")).kind, "none")
        self.assertEqual((await stub.find_voyage("9999", "2026-01-11")).kind, "none")


if __name__ == "__main__":
    unittest.main()
