# PC_HomeDelivery_Script_PrepareZendeskData  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_PrepareZendeskData",
  "type": "script"
}
```

## script
```
context.session = context.session || {};
context.session.BotUserSession = context.session.BotUserSession || {};
var sessionData = context.session.BotUserSession;
 
// -----------------------------
// Helper: JSON-escape a string WITHOUT surrounding quotes
// -----------------------------
function jsonEscape(v) {
    if (v === undefined || v === null) v = "";
    return JSON.stringify(String(v)).slice(1, -1);
}
 
var documentFailMessage = sessionData.documentFailMessageDisplay || "";
 
// -----------------------------
// USER DATA
// -----------------------------
var pii = sessionData.piiEntities || {};
 
var customerName = pii.name || "";
var email = pii.emailId || "";
var phone = pii.phoneNumber || "Not specified";
 
var cruiseLineName = sessionData.usr_cruise_line || "Not specified";
var vesselName = sessionData.usr_ship_name || "Not specified";
var deliveryType = context.entities.PC_HomeDelivery_Entity_DeliveryType || "Not Provided";
var country = sessionData.Country || "Not specified";
var quantity = sessionData.ProductCount || "0";
var cabinNumber = sessionData.CabinNumber || "Not Provided";
var spaRecordName =  context.session.BotUserSession.spa_record_name || "Not Provided";
var initial = sessionData.initialMessage || "Not provided";

var conversation = "No conversation";

if (
    sessionData.conversationHistory &&
    sessionData.conversationHistory.length > 0
) {
    conversation = sessionData.conversationHistory.join("\n\n").trim();

    if (!conversation) {
        conversation = "No conversation";
    }
}
 
// -----------------------------
// OPTIONAL FIELDS — Booking Number & Credit Card
// value when present, "N/A" when null/empty
// -----------------------------
var bookingNumberRaw = sessionData.bookingNumber;
var bookingNumberLine =
    (bookingNumberRaw && String(bookingNumberRaw).trim() !== "")
        ? bookingNumberRaw
        : "N/A";
 
var creditCardEntity = context.entities.PC_HomeDelivery_Entity_CreditCardInfo;
var creditCardRaw = pii.creditcard;
var creditCardLine =
    (creditCardEntity !== null && creditCardEntity !== undefined && creditCardEntity !== "" &&
     creditCardRaw && String(creditCardRaw).trim() !== "")
        ? creditCardRaw
        : "N/A";
 
// -----------------------------
// REASON HANDLING
// -----------------------------
var reasonDisplay = context.entities.PC_HomeDelivery_Entity_IssueReasonButtons || sessionData.reasonDisplay || "Other";
var reasonTag = sessionData.returnReason || "other-2";
var reasonText = sessionData.otherReturnReason || "";
sessionData.reasonDisplay = reasonDisplay;
 
var additionalDetails = context.entities.PC_Common_Entity_AdditionalDescription || "";
 
// -----------------------------
// DATE
// -----------------------------
var sailDate = sessionData.usr_start_date || "";
var purchaseDate = sessionData.purchaseDateFormatted || "Unkown";
var requestDate = context.PC_HomeDelivery_Script_SetRequestDate || new Date().toISOString().split("T")[0];
var sailDateIsValid = /^\d{4}-\d{2}-\d{2}$/.test(sailDate);
 
// -----------------------------
// CATEGORY
// -----------------------------
var category = "";
if (deliveryType === "Onboard Purchase") {
    category = "osw_onboard_purchase";
} else if (deliveryType === "Home Delivery") {
    category = "osw_home_delivery_hd";
}
 
// -----------------------------
// PRODUCTS
// -----------------------------
var productsFormatted = "";
if (sessionData.products && Array.isArray(sessionData.products) && sessionData.products.length > 0) {
    for (var p = 0; p < sessionData.products.length; p++) {
        var prod = sessionData.products[p];
        productsFormatted +=
            "• <b>Product " + (p + 1) + ":</b> " + (prod.product_name || "N/A") +
            " | <b>Qty:</b> " + (prod.quantity || "N/A") +
            " | <b>Condition:</b> " + (prod.condition || "N/A");
        if (prod.condition === "wrong product" && prod.expected_product_name) {
            productsFormatted += " | <b>Expected:</b> " + prod.expected_product_name;
        }
        productsFormatted += "<br>";
    }
} else {
    productsFormatted = "No product details captured.";
}
 
// -----------------------------
// DESCRIPTION FRAGMENTS
// Split around PII so raw name/email are injected directly
// in the SERVICE NODE body via tokens
// -----------------------------
var descPart1 =
"<b>MARINA BOT  —  PRODUCT RETURN REQUEST | Submitted : " + requestDate + "</b><br><br><br>" +
"<b>CUSTOMER DETAILS :</b><br>-------------------------<br>" +
"<b>Request Details :</b> " + initial + "<br>" +
"<b>Name :</b> ";
 
var descPart2 = "<br><b>Email :</b> ";
 
var descPart3 = "<br><b>Phone :</b> ";
 
var descPart4 =
"<br>" +
"<b>Country :</b> " + country + "<br>" +
"<b>Delivery Type :</b> " + deliveryType + "<br><br>" +
 
"<b>VOYAGE DETAILS:</b><br>-----------------------<br>" +
"<b>Cruise Line :</b> " + cruiseLineName + "<br>" +
"<b>Ship Name :</b> " + vesselName + "<br>" +
"<b>Sail Date :</b> " + sailDate + "<br><br>" +
 
"<b>SPA RECORD DETAILS :</b><br>---------------------------<br>" +
"<b>Spa Guest Name(s) : </b>  "+  spaRecordName;
 
var descPart5 =
"<br>" +
"<b>Cabin Number :</b> " + cabinNumber + "<br><br>" +
 
"<b>RETURN DETAILS:</b><br>-----------------------<br>" +
"<b>Purchase Date :</b> " + purchaseDate + "<br>" +
"<b>Return Request Date :</b> " + requestDate + "<br>" +
"<b>Return Reason :</b> " + reasonDisplay + "<br>" +
(reasonText ? "<b>Additional Reason Details :</b> " + reasonText + "<br>" : "") +
"<b>Product Count :</b> " + quantity + "<br><br>" +
 
"<b>Booking Number :</b> " + bookingNumberLine + "<br>" +
"<b>Credit Card (Last 4) :</b> ";
 
var descPart6 =
"<br><br>" +
"<b>PRODUCTS :</b><br>--------------<br>" +
productsFormatted + "<br><br>" +
 
"<b>ADDITIONAL INFORMATION:</b><br>--------------------------------<br>" +
(additionalDetails ? additionalDetails + "<br><br>" : "N/A<br>") ;

// "<b>Conversation : </b><br>--------------<br>" + conversation + "<br><br>";


context.zd_desc_p1 = jsonEscape(descPart1);
context.zd_desc_p2 = jsonEscape(descPart2);
context.zd_desc_p3 = jsonEscape(descPart3);
context.zd_desc_p4 = jsonEscape(descPart4);
context.zd_desc_p5 = jsonEscape(descPart5);
context.zd_desc_p6 = jsonEscape(descPart6);
 
// -----------------------------
// FALLBACKS for tokens injected directly in payload
// -----------------------------
context.zd_name_fallback = (String(customerName).trim() !== "") ? "" : "Guest";
context.zd_email_fallback = (String(email).trim() !== "") ? "" : "guest@onespaworld.com";
context.zd_phone_fallback = (String(pii.phoneNumber || "").trim() !== "") ? "" : "Not specified";
//context.zd_spaname_fallback = (String(pii.spa_record_name || "").trim() !== "") ? "" : "Not provided";
 
var creditCardEntity = context.entities.PC_HomeDelivery_Entity_CreditCardInfo;
context.zd_creditcard_fallback =
    (creditCardEntity !== null && creditCardEntity !== undefined && creditCardEntity !== "" &&
     pii.creditcard && String(pii.creditcard).trim() !== "")
        ? ""
        : "N/A";
 
// -----------------------------
// ATTACHMENTS
// -----------------------------
var uploads = sessionData.zd_tokens_combined;
if (!uploads || uploads.length === 0) {
    context.Emptyvalue = true;
    koreDebugger.log("No upload tokens found");
}
context.zendeskUploadToken = uploads;
 
// -----------------------------
// PRIORITY & SUBJECT
// -----------------------------
context.PriorityValue = "urgent";
var SubjectText = "Your Product Return Request Has Been Received";
if (sessionData.empathyMessage === "disappointed") {
    SubjectText = "Urgent - Your Product Return Request Has Been Received";
}
context.SubjectText = jsonEscape(SubjectText);
 
// -----------------------------
// TAGS as ready JSON array
// -----------------------------
var tags = ["kore_ai", "tag_website"];
if (documentFailMessage) {
    tags.push(documentFailMessage);
}
context.zd_tags_json = JSON.stringify(tags);
 
// -----------------------------
// PASS-THROUGH VALUES for service node
// -----------------------------
context.zd_cruise_line = jsonEscape(cruiseLineName);
context.zd_ship_name = jsonEscape(vesselName);
context.zd_reason_tag = jsonEscape(reasonTag);
context.zd_category = jsonEscape(category);
context.zd_inquiry = jsonEscape("osw_product_return");
 
context.zd_sail_date_fragment = sailDateIsValid
    ? ',{ "id": "{{env.Zendesk_SailDate_ID}}", "value": "' + jsonEscape(sailDate) + '" }'
    : "";
 
// -----------------------------
// SAVE FOR SERVICE NODE
// -----------------------------
sessionData.requestDate = requestDate;
sessionData.customerName = customerName;
sessionData.customerEmail = email;
sessionData.phone = phone;
sessionData.cruiseLineName = cruiseLineName;
sessionData.vesselName = vesselName;
sessionData.deliveryType = deliveryType;
sessionData.country = country;
sessionData.quantity = quantity;
sessionData.cabinNumber = cabinNumber;
sessionData.bookingNumber = bookingNumberLine;
sessionData.creditCardDisplay = creditCardLine;
sessionData.reasonDisplay = reasonDisplay;
sessionData.reasonTag = reasonTag;
sessionData.reasonText = reasonText;
sessionData.sailDate = sailDate;
sessionData.purchaseDate = purchaseDate;
sessionData.category = category;
sessionData.productsFormatted = productsFormatted;
sessionData.additionalDetails = additionalDetails;
 
koreDebugger.log("Reason Display: " + reasonDisplay);
koreDebugger.log("Reason Tag: " + reasonTag);
koreDebugger.log("Booking Number Line: " + bookingNumberLine);
koreDebugger.log("Credit Card Line: " + creditCardLine);
koreDebugger.log("zd_tags_json: " + context.zd_tags_json);
 
```
