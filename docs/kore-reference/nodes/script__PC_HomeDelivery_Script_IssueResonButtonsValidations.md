# PC_HomeDelivery_Script_IssueResonButtonsValidations  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_IssueResonButtonsValidations",
  "type": "script"
}
```

## script
```
context.session = context.session || {};
context.session.BotUserSession = context.session.BotUserSession || {};

var sessionData = context.session.BotUserSession;
var entities = context.entities || {};


// -----------------------------
// NORMALIZE FUNCTION
// -----------------------------
function normalize(text) {
    return (text || "")
        .toLowerCase()
        .replace(/\s*\(\s*s\s*\)/g, "(s)")
        .replace(/\s*,\s*/g, ",")        
        .replace(/,/g, ", ")               
        .replace(/\s+/g, " ")              
        .trim();
}


// -----------------------------
// INPUT VALUES
// -----------------------------
var reasonType = entities.PC_HomeDelivery_Entity_IssueReasonButtons || "";
var reasonText = entities.PC_HomeDelivery_Entity_Reason || "";

var normalizedReason = normalize(reasonType);


// -----------------------------
// EXACT MAP (BASED ON BUTTONS)
// -----------------------------
var map = {

    "item(s) arrived damaged or incorrect": {
        zendesk: "osw_items_damaged_or_incorrect",
        api: "itemsArrivedDamagedOrIncorrect"
    },

    "product(s) did not meet expectations": {
        zendesk: "osw_products_didn’t_meet_expectation",
        api: "productsDidNotMeetExprectations"
    },

    "health or sensitivity concern": {
        zendesk: "osw_health_or_sensitivity_concern",
        api: "healthOrSensitiveConcerns"
    },

    "order, delivery, or billing issue": {
        zendesk: "osw_order_delivery_or_billing_issue",
        api: "orderDeliveryOrBillingIssue"
    },

    "other": {
        zendesk: "osw_other2",
        api: "other"
    }
};


// -----------------------------
// STORE DISPLAY VALUE
// -----------------------------
sessionData.reasonDisplay = reasonType;


// -----------------------------
// MAP VALUES
// -----------------------------
if (map[normalizedReason]) {

    sessionData.returnReason = map[normalizedReason].zendesk;
    sessionData.returnReasonMapped = map[normalizedReason].api;

} else {

    // fallback
    sessionData.returnReason = "osw_other2";
    sessionData.returnReasonMapped = "other";
}

// -----------------------------
// HANDLE OTHER REASON
// -----------------------------
if (sessionData.returnReasonMapped === "other") {
    sessionData.otherReturnReason = reasonText || normalizedReason || "";
} else {
    sessionData.otherReturnReason = "";
}


// -----------------------------
// DEBUG LOGS
// -----------------------------
koreDebugger.log("RAW: " + reasonType);
koreDebugger.log("NORMALIZED: " + normalizedReason);
koreDebugger.log("ZENDESK: " + sessionData.returnReason);
koreDebugger.log("API: " + sessionData.returnReasonMapped);
koreDebugger.log("OTHER_REASON: " + sessionData.otherReturnReason);
```
