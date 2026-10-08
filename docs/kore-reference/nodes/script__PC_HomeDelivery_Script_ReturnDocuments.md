# PC_HomeDelivery_Script_ReturnDocuments  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_ReturnDocuments",
  "type": "script"
}
```

## script
```
context.session.BotUserSession.TicketId = context.PC_HomeDelivery_Service_CreateTicket.response.body.ticket.id;

//cabin number for transactions
context.session.BotUserSession.cabinNumber = context.session.BotUserSession.CabinNumber;

//-------------------------------------------------
// Get products from session
//-------------------------------------------------

var products = context.session.BotUserSession.products || [];

//-------------------------------------------------
// Condition mapping
//-------------------------------------------------

var conditionMap = {
    "new": "unused",
    "unopened": "unused",
    "sealed": "unused",
    "unused": "unused",
    "wrong product": "unused",
    "used": "used",
    "opened": "used",
    "damaged": "unused",
};

//-------------------------------------------------
// Build productsToReturn array
//-------------------------------------------------

var productsToReturn = [];

for (var j = 0; j < products.length; j++) {
    var p = products[j];
    var conditionRaw     = (p.condition || "").toString().toLowerCase().trim();
    var productCondition = conditionMap[conditionRaw];
    if (productCondition === undefined) productCondition = "used";
    productsToReturn.push({
        productName:      (p.product_name || "").toString(),
        quantity:         parseInt(p.quantity) || 0,
        productCondition: productCondition
    });
}

//-------------------------------------------------
// Reason handling
//-------------------------------------------------

var returnReasonMapped = context.session.BotUserSession.returnReasonMapped || "";
var otherReturnReason  = context.session.BotUserSession.otherReturnReason  || "";
var isOther             = returnReasonMapped === "other";

//-------------------------------------------------
// Optional fields (non-PII only — creditcard stays in template for detokenization)
//-------------------------------------------------

var bookingNumber = context.session.BotUserSession.bookingNumber || null;

//-------------------------------------------------
// Pre-formatted values for the service node template
//-------------------------------------------------

// productsToReturn -> pre-stringified for template
context.session.BotUserSession.productsToReturnString = JSON.stringify(productsToReturn);


context.session.BotUserSession.otherReturnReasonLine =
    isOther ? ',"otherReturnReason":' + JSON.stringify(otherReturnReason) : "";

context.session.BotUserSession.bookingNumberLine =
    bookingNumber ? ',"bookingNumber":' + JSON.stringify(String(bookingNumber)) : "";
```
