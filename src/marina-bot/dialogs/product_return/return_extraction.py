"""Second extraction of the customer's first message: what they said about the purchase.

Ports two Kore nodes:
  PC_HomeDelivery_PromptNode      (generativeai)  -> the prompt in prompts/extract_return_details.md, run by a PromptNode
  PC_HomeDelivery_Script_SaveEntities (script)    -> process_return_extraction below

The model returns cabin number(s), a purchase date as written, country, phone, and the products being returned.
Everything is validated here and stored under Kore's names so later steps can skip questions already answered:

  entities / session : CabinNumber, CabinNumbers, PurchasedDate (raw text), Country, ProductCount
  session            : products (list of {product_name, quantity, condition, expected_product_name}),
                       piiEntities.phoneNumber, the *Unknown flags, extractionStatus
"""

import json
import logging
import re
from typing import Any

from models import Turn
from shared.countries import parse_country
from shared.validators import parse_cabins, parse_phone

log = logging.getLogger(__name__)

EXTRACT_NODE = "PC_HomeDelivery_PromptNode"
CONDITIONS = ("new", "used", "damaged", "wrong product")
UNKNOWN_FLAGS = {                       # unknown_indicated_fields entry -> session flag
    "cabin_number": "CabinNumberUnknown",
    "purchase_date_raw": "PurchasedDateUnknown",
    "country": "CountryUnknown",
    "phone_number": "PhoneNumberUnknown",
    "product_count": "ProductCountUnknown",
}


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() not in ("", "null", "UNKNOWN")


def _parse_json(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        parsed = json.loads(re.sub(r"```json|```", "", text, flags=re.I).strip())
    except json.JSONDecodeError as exc:
        log.info("return extraction: JSON parse error: %s", exc)
        return None
    return parsed if isinstance(parsed, dict) else None


def _clean_product(raw: Any) -> dict[str, str | None] | None:
    if not isinstance(raw, dict):
        return None
    slot: dict[str, str | None] = {"product_name": None, "quantity": None, "condition": None,
                                   "expected_product_name": None}
    name = raw.get("product_name")
    if _present(name) and not re.fullmatch(r"\d+", str(name).strip()):
        slot["product_name"] = str(name).strip()
    if _present(raw.get("quantity")):
        try:
            quantity = int(str(raw["quantity"]).strip())
        except ValueError:
            quantity = 0
        if 1 <= quantity <= 999:
            slot["quantity"] = str(quantity)
    if _present(raw.get("condition")) and str(raw["condition"]).lower().strip() in CONDITIONS:
        slot["condition"] = str(raw["condition"]).lower().strip()
    if _present(raw.get("expected_product_name")):
        slot["expected_product_name"] = str(raw["expected_product_name"]).strip()
    # keep a slot only if it carries something real
    return slot if (slot["product_name"] or slot["quantity"] or slot["condition"]) else None


def process_return_extraction(turn: Turn) -> None:
    """Validate the model's JSON and store each value that passes. Never raises; bad output changes nothing."""
    s, e = turn.session, turn.entities
    parsed = _parse_json(s.get("nodeOutputs", {}).get(EXTRACT_NODE))
    if parsed is None:
        log.info("return extraction: no usable output")
        return
    pii = s.setdefault("piiEntities", {})

    if _present(parsed.get("cabin_number")):
        cabins = parse_cabins(str(parsed["cabin_number"])).cabins
        if cabins:
            e["CabinNumber"] = s["CabinNumber"] = s["resolvedCabinNumber"] = ", ".join(cabins)
            e["CabinNumbers"] = s["CabinNumbers"] = cabins

    if _present(parsed.get("purchase_date_raw")):
        raw = str(parsed["purchase_date_raw"]).strip()
        if re.search(r"\d", raw) and 6 <= len(raw) <= 30:           # real date validation happens when we ask
            e["PurchasedDate"] = s["PurchasedDate"] = raw

    if _present(parsed.get("country")):
        country = parse_country(str(parsed["country"]))
        if country:
            e["Country"] = s["Country"] = s["resolvedCountry"] = country

    if _present(parsed.get("phone_number")):
        phone = parse_phone(str(parsed["phone_number"]))
        if phone:
            pii["phoneNumber"] = phone

    if _present(parsed.get("product_count")):
        try:
            count = int(str(parsed["product_count"]).strip())
        except ValueError:
            count = 0
        if 1 <= count <= 999:                                        # a count is never defaulted
            e["ProductCount"] = s["ProductCount"] = count
            s["resolvedProductCount"] = str(count)

    products = parsed.get("products")
    if isinstance(products, list):
        cleaned = [slot for slot in map(_clean_product, products) if slot]
        if cleaned:
            s["products"] = cleaned

    unknown = parsed.get("unknown_indicated_fields")
    for field_name in unknown if isinstance(unknown, list) else []:
        if field_name in UNKNOWN_FLAGS:
            s[UNKNOWN_FLAGS[field_name]] = True
    s["extractionStatus"] = parsed.get("extractionSuccessful") or "processed"
    log.info("return extraction: cabin=%s purchase_date=%s country=%s phone=%s count=%s products=%d unknown=%s",
             e.get("CabinNumber"), "PurchasedDate" in e, e.get("Country"), "phoneNumber" in pii,
             e.get("ProductCount"), len(s.get("products", [])), unknown)
