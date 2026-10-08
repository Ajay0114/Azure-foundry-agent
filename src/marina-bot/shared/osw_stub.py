"""Offline stand-in for the OSW APIs: FAKE vessels and voyages for tests and local development.

Same behaviour contract as OswClient (vessel name search, cruise-line fallback, exact then nearest voyage),
so the dialogs behave the same with either. The IDs and dates below are invented.
"""

from shared.osw import Vessel, Voyage, VoyageMatch, find_voyage_with


class StubOsw:
    VESSELS = [
        Vessel("1042", "Harmony of the Seas", "ROYAL CARIBBEAN INTERNATIONAL"),
        Vessel("1043", "Wonder of the Seas", "ROYAL CARIBBEAN INTERNATIONAL"),
        Vessel("2051", "Carnival Dream", "CARNIVAL"),
        Vessel("2052", "Carnival Panorama", "CARNIVAL"),
        Vessel("3060", "Celebrity Edge", "CELEBRITY"),
    ]
    VOYAGES = {
        "1042": [Voyage("9001", "2026-01-11", "2026-01-18", 8, "CARIB W", "GALVESTON", "GALVESTON"),
             Voyage("9002", "2026-01-18", "2026-01-25", 8, "CARIB W", "GALVESTON", "GALVESTON")],
        "2051": [Voyage("9101", "2026-02-01", "2026-02-08")],
    }

    async def find_vessels(self, query: str) -> list[Vessel]:
        q = (query or "").strip().lower()
        if not q:
            return []
        by_name = [v for v in self.VESSELS if q in v.name.lower()]
        by_line = [v for v in self.VESSELS if q in v.cruise_line.lower()]
        found = by_name or by_line
        exact = [v for v in found if v.name.lower() == q]
        return exact or found

    async def find_voyage(self, vessel_id: str, iso_date: str) -> VoyageMatch:
        voyages = self.VOYAGES.get(str(vessel_id), [])

        async def embarked():
            return [v for v in voyages if v.start_date == iso_date]

        async def containing():
            return [v for v in voyages if v.start_date <= iso_date <= (v.end_date or v.start_date)]

        return await find_voyage_with(iso_date, embarked, containing)
