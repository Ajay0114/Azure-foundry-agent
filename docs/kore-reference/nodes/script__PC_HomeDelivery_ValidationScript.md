# PC_HomeDelivery_ValidationScript  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_ValidationScript",
  "type": "script"
}
```

## script
```
try {

    // ── Treat placeholder strings as missing ──
    function isEffectivelyEmpty(val) {
        if (!val) return true;
        var normalized = String(val).trim().toLowerCase();
        return normalized === "" ||
               normalized === "null" ||
               normalized === "n/a" ||
               normalized === "not provided" ||
               normalized === "not specified" ||
               normalized === "unknown" ||
               normalized === "undefined";
    }

    var returnsPassedFields = [];
    var returnsFailedFields = [];

    var transactionPassedFields = [];
    var transactionFailedFields = [];

    //-------------------------------------------------
    // RETURN DOCUMENT VALIDATION
    //-------------------------------------------------

    var guestName        =  context.session.BotUserSession.spa_record_name;
    var email            = context.session.BotUserSession.piiEntities.emailId;
    var phone            = context.session.BotUserSession.piiEntities.phoneNumber;
    var embarkationDate  = context.session.BotUserSession.usr_start_date;
    var country          = context.session.BotUserSession.Country;
    var cruiseLine       = context.session.BotUserSession.usr_cruise_line;
    var shipName         = context.session.BotUserSession.usr_ship_name;
    var cabinNumber      = context.session.BotUserSession.CabinNumber;
    var purchaseDate     = context.session.BotUserSession.purchaseDateAPI;
    var requestDate      = context.session.BotUserSession.requestedDate;
    var products         = context.session.BotUserSession.products || [];

    if (!isEffectivelyEmpty(guestName)) {
        returnsPassedFields.push("spa_record_name");
    } else {
        returnsFailedFields.push("spa_record_name");
    }

    if (!isEffectivelyEmpty(email)) {
        returnsPassedFields.push("customerEmail");
    } else {
        returnsFailedFields.push("customerEmail");
    }

    if (!isEffectivelyEmpty(phone)) {
        returnsPassedFields.push("PhoneNumber");
    } else {
        returnsFailedFields.push("PhoneNumber");
    }

    if (!isEffectivelyEmpty(country)) {
        returnsPassedFields.push("Country");
    } else {
        returnsFailedFields.push("Country");
    }

    if (!isEffectivelyEmpty(cruiseLine)) {
        returnsPassedFields.push("usr_cruise_line");
    } else {
        returnsFailedFields.push("usr_cruise_line");
    }

    if (!isEffectivelyEmpty(shipName)) {
        returnsPassedFields.push("usr_ship_name");
    } else {
        returnsFailedFields.push("usr_ship_name");
    }

    if (!isEffectivelyEmpty(cabinNumber)) {
        returnsPassedFields.push("CabinNumber");
    } else {
        returnsFailedFields.push("CabinNumber");
    }

    if (!isEffectivelyEmpty(embarkationDate)) {
        returnsPassedFields.push("embarkationDate");
    } else {
        returnsFailedFields.push("embarkationDate");
    }

    if (!isEffectivelyEmpty(purchaseDate)) {
        returnsPassedFields.push("purchaseDateAPI");
    } else {
        returnsFailedFields.push("purchaseDateAPI");
    }

    if (!isEffectivelyEmpty(requestDate)) {
        returnsPassedFields.push("requestedDate");
    } else {
        returnsFailedFields.push("requestedDate");
    }

    if (products.length > 0) {
        returnsPassedFields.push("products");
    } else {
        returnsFailedFields.push("products");
    }

    if (products.length > 0) {
        var emptyProductName = false;

        for (var i = 0; i < products.length; i++) {
            if (isEffectivelyEmpty(products[i].product_name)) {
                emptyProductName = true;
                break;
            }
        }

        if (emptyProductName) {
            returnsFailedFields.push("products[].productName");
        } else {
            returnsPassedFields.push("products[].productName");
        }
    }

    //-------------------------------------------------
    // TRANSACTION DOCUMENT VALIDATION
    //-------------------------------------------------

    var vesselId    = context.session.BotUserSession.usr_vessel_id;
    var startDate   = context.session.BotUserSession.usr_start_date;
    var endDate     = context.session.BotUserSession.usr_end_date;

    if (!isEffectivelyEmpty(vesselId)) {
        transactionPassedFields.push("usr_vessel_id");
    } else {
        transactionFailedFields.push("usr_vessel_id");
    }

    if (!isEffectivelyEmpty(startDate)) {
        transactionPassedFields.push("usr_start_date");
    } else {
        transactionFailedFields.push("usr_start_date");
    }

    if (!isEffectivelyEmpty(endDate)) {
        transactionPassedFields.push("usr_end_date");
    } else {
        transactionFailedFields.push("usr_end_date");
    }

    var guestNameForTransaction  =  context.session.BotUserSession.spa_record_name;
    var cabinNumberForTransaction = context.session.BotUserSession.CabinNumber;

    if (!isEffectivelyEmpty(guestNameForTransaction)) {
        transactionPassedFields.push("spa_record_name");
    } else {
        transactionFailedFields.push("spa_record_name");
    }

    if (!isEffectivelyEmpty(cabinNumberForTransaction)) {
        transactionPassedFields.push("CabinNumber");
    } else {
        transactionFailedFields.push("CabinNumber");
    }

    //-------------------------------------------------
    // SAVE RESULTS
    //-------------------------------------------------

    context.session.BotUserSession.returnsValidationStatus =
        returnsFailedFields.length === 0 ? "PASS" : "FAIL";

    context.session.BotUserSession.transactionValidationStatus =
        transactionFailedFields.length === 0 ? "PASS" : "FAIL";

    context.session.BotUserSession.returnsFailedFields =
        returnsFailedFields.join(", ");

    context.session.BotUserSession.transactionFailedFields =
        transactionFailedFields.join(", ");

    var passedFields = returnsPassedFields.concat(transactionPassedFields);
    var failedFields = returnsFailedFields.concat(transactionFailedFields);

    context.validation_status =
        failedFields.length === 0 ? "PASS" : "FAIL";

    context.validation_passed_fields = passedFields.join(", ");
    context.validation_failed_fields = failedFields.join(", ");

    koreDebugger.log("Returns Status: "     + context.session.BotUserSession.returnsValidationStatus);
    koreDebugger.log("Transaction Status: " + context.session.BotUserSession.transactionValidationStatus);
    koreDebugger.log("Status: "             + context.validation_status);
    koreDebugger.log("Passed: "             + context.validation_passed_fields);
    koreDebugger.log("Failed: "             + context.validation_failed_fields);
    koreDebugger.log("failedFields: "       + JSON.stringify(failedFields));

    context.session.BotUserSession.validation_status = context.validation_status;

} catch (e) {

    context.validation_status          = "FAIL";
    context.validation_failed_fields   = "Validation Error";

    context.session.BotUserSession.returnsValidationStatus      = "FAIL";
    context.session.BotUserSession.transactionValidationStatus  = "FAIL";

    koreDebugger.log("Validation Error: " + e);
}

//-------------------------------------------------
// DISPLAY LABELS
//-------------------------------------------------

var status = context.validation_status;

context.session.BotUserSession.statusCheck = context.validation_status;

var failedFields = context.validation_failed_fields
    ? context.validation_failed_fields.split(", ")
    : [];

var fieldLabels = {
    "spa_record_name"       : "Guest Name",
    "customerEmail"         : "Email",
    "PhoneNumber"           : "Phone Number",
    "Country"               : "Country",
    "usr_cruise_line"       : "Cruise Line",
    "usr_ship_name"         : "Vessel Name",
    "CabinNumber"           : "Cabin Number",
    "embarkationDate"       : "Embarkation Date",
    "purchaseDateAPI"       : "Purchase Date",
    "requestedDate"         : "Return Request Date",
    "products"              : "Products",
    "products[].productName": "Product Name",
    "usr_vessel_id"         : "Vessel Id",
    "usr_start_date"        : "Start Date",
    "usr_end_date"          : "End Date",
    "customerName"          : "Customer Name"
};

// Returns display fields
var returnsFailedFields = context.session.BotUserSession.returnsFailedFields
    ? context.session.BotUserSession.returnsFailedFields.split(", ")
    : [];

var returnsDisplayFields = returnsFailedFields.map(function(field) {
    return fieldLabels[field] || field;
});

context.session.BotUserSession.returnsFailedFieldsDisplay =
    returnsDisplayFields.join(", ");

// Transaction display fields
var transactionFailedFields = context.session.BotUserSession.transactionFailedFields
    ? context.session.BotUserSession.transactionFailedFields.split(", ")
    : [];

var transactionDisplayFields = transactionFailedFields.map(function(field) {
    return fieldLabels[field] || field;
});

context.session.BotUserSession.transactionFailedFieldsDisplay =
    transactionDisplayFields.join(", ");

var displayFields = failedFields.map(function(field) {
    return fieldLabels[field] || field;
});

koreDebugger.log("Actual Failed Fields: " + JSON.stringify(failedFields));
koreDebugger.log("Display Fields: "       + JSON.stringify(displayFields));

var documentCreationDisplay = status === "FAIL"
    ? displayFields.join(", ")
    : "";

context.session.BotUserSession.documentCreationDisplay = documentCreationDisplay;

koreDebugger.log("documentCreationDisplay set to: " +
    context.session.BotUserSession.documentCreationDisplay);

var documentFailMessage = status === "FAIL"
    ? "returns_documentcreaterequestfailed,transactions_documentcreaterequestfailed"
    : "";

context.session.BotUserSession.documentFailMessageDisplay = documentFailMessage;
```
