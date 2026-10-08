"""Shows the REAL response shapes of the OSW APIs and what our parsers make of them.

Usage (from src/marina-bot, after filling the OSW_* values in .env):

    uv run --no-sync python probe_osw.py --vessel "Harmony" --date 2026-01-11
    uv run --no-sync python probe_osw.py --vessel "Royal Caribbean"            (cruise-line fallback)
    uv run --no-sync python probe_osw.py --vessel "Harmony" --vessel-id 901 --date 2026-06-06

It prints only structure and a few short sample values. It never prints the token or the client secret.
Paste the output back so shared/osw.py can be tightened to the real field names.
"""

import argparse
import asyncio
import json
import sys

import httpx
from dotenv import load_dotenv

from shared.osw import OswClient, OswConfig, extract_items, rql_text

load_dotenv()


def shape(value, depth=0):
    """Structure of a JSON value with short sample values."""
    if isinstance(value, dict):
        return {k: shape(v, depth + 1) for k, v in list(value.items())[:40]}
    if isinstance(value, list):
        return ([shape(value[0], depth + 1)] if value else []) + ([f"... {len(value)} items"] if value else ["(empty)"])
    if isinstance(value, str):
        return value if len(value) <= 40 else value[:37] + "..."
    return value


async def call(client: OswClient, title: str, path: str, scope: str, params=None):
    print(f"\n=== {title}\n    GET {path} {params or ''}")
    try:
        payload = await client.get_json(path, scope, params=params, allow_404=True)
    except httpx.HTTPStatusError as exc:
        print(f"    HTTP {exc.response.status_code}: {exc.response.text[:300]!r}")
        return None
    except Exception as exc:  # network, auth, JSON...
        print(f"    FAILED: {type(exc).__name__}: {exc}")
        return None
    if payload is None:
        print("    -> 404 / empty body")
        return None
    items = extract_items(payload)
    print(f"    top-level type: {type(payload).__name__}; records found by extract_items: {len(items)}")
    print("    shape:", json.dumps(shape(payload if not isinstance(payload, list) else payload[:2]), indent=2).replace("\n", "\n    "))
    return payload


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vessel", default="Harmony", help="ship name or cruise line to search")
    parser.add_argument("--vessel-id", help="vessel id for the voyage calls (default: first vessel found)")
    parser.add_argument("--date", default="2026-01-11", help="YYYY-MM-DD")
    args = parser.parse_args()

    config = OswConfig.from_env()
    if config is None:
        print("Set OSW_TOKEN_URL, OSW_CLIENT_ID, OSW_CLIENT_SECRET, OSW_VESSELS_SCOPE and OSW_ITINERARY_SCOPE in .env")
        return 1
    print(f"Using {config}")
    client = OswClient(config)
    text, ymd = rql_text(args.vessel), args.date.replace("-", "")

    vessels = await call(client, "Vessel search by name", "/info/vessels", config.vessels_scope,
                         {"filter": f'co(name,"{text}")'})
    await call(client, "Cruise line search by name", "/info/cruiselines", config.vessels_scope,
               {"filter": f'co(name,"{text}")'})

    vessel_id = args.vessel_id
    if not vessel_id and vessels:
        first = (extract_items(vessels) or [{}])[0]
        vessel_id = str(first.get("id") or first.get("vesselId") or "") or None
    if vessel_id:
        base = f"/master/itinerary/vessels/{vessel_id}"
        await call(client, "Voyage by embarkation date", f"{base}/embarkation/date/{ymd}", config.itinerary_scope)
        await call(client, "Voyages containing the date", f"{base}/any/date/{ymd}", config.itinerary_scope)
    else:
        print("\n(no vessel id available: skipping the voyage calls; pass --vessel-id)")

    print("\n=== What our parsers extract")
    found = await client.find_vessels(args.vessel)
    print(f"find_vessels({args.vessel!r}) -> {len(found)} vessel(s)")
    for v in found[:5]:
        print("   ", v)
    if vessel_id:
        print(f"find_voyage({vessel_id!r}, {args.date!r}) ->", await client.find_voyage(vessel_id, args.date))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
