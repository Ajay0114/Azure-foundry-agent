"""The two documents requested for a return ticket: the products-return document and the transactions document.

Ports Kore's PC_HomeDelivery_ValidationScript, PC_HomeDelivery_Script_ReturnDocuments, the two DocumentCreation service
payloads and the validation / error private-note scripts. Everything here is a pure function over the session, so each
payload and note can be read (and tested) on its own.

How it differs from Kore, on purpose:
  * each document is decided on its own: a document whose fields are all present is requested, one that is not gets a
    private note on the ticket listing what is missing, and the other is not held back;
  * the Zendesk failure tags name only the document that failed (Kore adds both whenever either fails, and as ONE tag with
    a comma in it);
  * the transactions document gets the cabins as a real list; the returns document keeps Kore's single cabin text;
  * only products with a name and a quantity are sent (Kore sends incomplete ones with quantity 0);
  * the API's error text is HTML-escaped before it goes into the private note.

Left out on purpose (not asked in every conversation): booking number and credit card last four.
"""

from dataclasses import dataclass, field
from typing import Any

from shared.htmltext import esc

RETURNS_TAG = "returns_documentcreaterequestfailed"
TRANSACTIONS_TAG = "transactions_documentcreaterequestfailed"
EMPTY_WORDS = {"", "null", "n/a", "not provided", "not specified", "unknown", "undefined", "none"}
CONDITION_TO_DOCUMENT = {"new": "unused", "wrong product": "unused", "damaged": "unused", "used": "used"}   # Kore's map
LABELS = {
    "spa_record_name": "Guest Name", "customerEmail": "Email", "PhoneNumber": "Phone Number", "Country": "Country",
    "usr_cruise_line": "Cruise Line", "usr_ship_name": "Vessel Name", "CabinNumber": "Cabin Number",
    "embarkationDate": "Embarkation Date", "purchaseDateAPI": "Purchase Date", "requestedDate": "Return Request Date",
    "products": "Products", "products[].productName": "Product Name", "usr_vessel_id": "Vessel Id",
    "usr_start_date": "Start Date", "usr_end_date": "End Date",
}


def is_empty(value: Any) -> bool:
    return value is None or str(value).strip().lower() in EMPTY_WORDS


@dataclass
class Validation:
    returns_failed: list[str] = field(default_factory=list)          # display labels
    transaction_failed: list[str] = field(default_factory=list)

    @property
    def returns_ok(self) -> bool:
        return not self.returns_failed

    @property
    def transactions_ok(self) -> bool:
        return not self.transaction_failed

    @property
    def tags(self) -> list[str]:
        return ([] if self.returns_ok else [RETURNS_TAG]) + ([] if self.transactions_ok else [TRANSACTIONS_TAG])


def document_products(session: dict[str, Any]) -> list[dict[str, Any]]:
    """The products that can be sent: a name and a whole quantity of at least 1."""
    out = []
    for p in session.get("products") or []:
        if not isinstance(p, dict) or is_empty(p.get("product_name")):
            continue
        try:
            quantity = int(p.get("quantity"))
        except (TypeError, ValueError):
            continue
        if quantity >= 1:
            out.append({"productName": str(p["product_name"]).strip(), "quantity": quantity,
                        "productCondition": CONDITION_TO_DOCUMENT.get(str(p.get("condition") or "").lower().strip(), "used")})
    return out


def validate_documents(session: dict[str, Any]) -> Validation:
    """Kore's ValidationScript: which fields each document needs, and which are missing."""
    pii = session.get("piiEntities") or {}
    returns = {"spa_record_name": session.get("spa_record_name"), "customerEmail": pii.get("emailId"),
               "PhoneNumber": pii.get("phoneNumber"), "Country": session.get("Country"),
               "usr_cruise_line": session.get("usr_cruise_line"), "usr_ship_name": session.get("usr_ship_name"),
               "CabinNumber": session.get("CabinNumber"), "embarkationDate": session.get("usr_start_date"),
               "purchaseDateAPI": session.get("purchaseDateAPI"), "requestedDate": session.get("requestedDate")}
    failed = [key for key, value in returns.items() if is_empty(value)]
    if not document_products(session):
        failed.append("products" if not (session.get("products") or []) else "products[].productName")
    transactions = {"usr_vessel_id": session.get("usr_vessel_id"), "usr_start_date": session.get("usr_start_date"),
                    "usr_end_date": session.get("usr_end_date"), "spa_record_name": session.get("spa_record_name"),
                    "CabinNumber": session.get("CabinNumber")}
    return Validation([LABELS[k] for k in failed], [LABELS[k] for k, v in transactions.items() if is_empty(v)])


def apply_validation(session: dict[str, Any]) -> Validation:
    """Run the validation and keep Kore's session keys for the later steps and the ticket tags."""
    result = validate_documents(session)
    session["returnsValidationStatus"] = "PASS" if result.returns_ok else "FAIL"
    session["transactionValidationStatus"] = "PASS" if result.transactions_ok else "FAIL"
    session["returnsFailedFieldsDisplay"] = ", ".join(result.returns_failed)
    session["transactionFailedFieldsDisplay"] = ", ".join(result.transaction_failed)
    session["documentFailTags"] = result.tags
    return result


def build_returns_payload(session: dict[str, Any], ticket_id: int) -> dict[str, Any]:
    pii = session.get("piiEntities") or {}
    parameters: dict[str, Any] = {
        "guestFullname": session.get("spa_record_name"), "eMail": pii.get("emailId"), "phone": pii.get("phoneNumber"),
        "countryName": session.get("Country"), "cruiseLineName": session.get("usr_cruise_line"),
        "vesselName": session.get("usr_ship_name"), "cabinNumber": session.get("CabinNumber"),
        "embarkationDate": session.get("usr_start_date"), "purchaseDate": session.get("purchaseDateAPI"),
        "returnRequestDate": session.get("requestedDate"),
        "isWithinReturnPolicyPeriod": bool(session.get("isWithinReturnPolicyPeriod")),
        "returnReasons": [session.get("returnReasonMapped") or "other"],
    }
    if session.get("returnReasonMapped") == "other" and session.get("otherReturnReason"):
        parameters["otherReturnReason"] = session["otherReturnReason"]
    parameters["productsToReturn"] = document_products(session)
    return {"referenceId": str(ticket_id), "parameters": parameters,
            "clientMetadata": [{"name": "source", "value": "marina-bot"}]}


def build_transactions_payload(session: dict[str, Any], ticket_id: int) -> dict[str, Any]:
    pii = session.get("piiEntities") or {}
    cabins = session.get("CabinNumbers") or [session.get("CabinNumber")]
    return {"referenceId": str(ticket_id), "parameters": {
        "vesselId": str(session.get("usr_vessel_id")), "startDate": session.get("usr_start_date"),
        "endDate": session.get("usr_end_date"), "guestsFullNames": [pii.get("sparecordname") or session.get("spa_record_name")],
        "cabins": [str(c) for c in cabins]}}


def _note(title: str, *lines: str) -> str:
    return f"<b>{title}</b><br>---------------------<br>" + "<br>".join(lines)


def validation_notes(result: Validation) -> list[str]:
    """The private notes for documents that cannot be requested (Kore's three ...DocumentFail scripts)."""
    if not result.returns_ok and not result.transactions_ok:
        return [_note("DOCUMENT VALIDATION FAILED", f"<b>Returns Missing or Invalid:</b> {esc(', '.join(result.returns_failed))}",
                      "", f"<b>Transaction Missing or Invalid:</b> {esc(', '.join(result.transaction_failed))}")]
    notes = []
    if not result.returns_ok:
        notes.append(_note("RETURNS DOCUMENT VALIDATION FAILED", f"<b>Missing or invalid:</b> {esc(', '.join(result.returns_failed))}"))
    if not result.transactions_ok:
        notes.append(_note("TRANSACTION DOCUMENT VALIDATION FAILED",
                           f"<b>Missing or invalid:</b> {esc(', '.join(result.transaction_failed))}"))
    return notes


def error_note(kind: str, status: int | None, detail: str) -> str:
    """The private note when the document API refuses a request (Kore: Returns/TransactionsErrorHandling)."""
    name = "RETURNS" if kind == "returns" else "TRANSACTION"
    label = "Returns Document" if kind == "returns" else "Transaction Document"
    where = f"(Status: {status})" if status else "(no response)"
    return (f"<b>{name} DOCUMENT CREATION FAILED</b><br>---------------------<br><br><b>Error Details:</b><br>"
            f"{label} {where}: {esc(detail or 'Unknown Error')}<br><br>As a result, the "
            f"{'returns' if kind == 'returns' else 'transaction'} document creation request could not be processed.")
