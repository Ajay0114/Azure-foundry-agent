# PC_HomeDelivery_Script_ClearData  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_ClearData",
  "type": "script"
}
```

## script
```
context.entities = context.entities || {};
context.session = context.session || {};
context.session.BotUserSession = context.session.BotUserSession || {};

var s = context.session.BotUserSession;


// --------------------
// Clear dialog entities
// --------------------
context.entities.CabinNumber = null;
context.entities.PurchasedDate = null;
context.entities.Country = null;
context.entities.PhoneNumber = null;
context.entities.ProductCount = null;
context.entities.ProductName = null;
context.entities.Quantity = null;
context.entities.Condition = null;
context.entities.ProductsCollected = 0;
context.entities.AllProductsCaptured = false;
context.entities.PC_HomeDelivery_Entity_PhoneNumber = null;
context.entities.PC_Common_2_Entity_NameAsPerSpaRecords = null;

// --------------------
// Clear session values
// --------------------
s.CabinNumber = null;
s.PurchasedDate = null;
s.Country = null;
s.PhoneNumber = null;
s.ProductCount = null;
s.ProductName = null;
s.Quantity = null;
s.Condition = null;

s.cabinNumber = null;
s.purchaseDateFormatted = null;
s.purchaseDateAPI = null;
s.lastEnteredDate = null;

// --------------------
// Clear additional BotUserSession variables
// --------------------
s.vesselCompleted = null;
s.vessel_id = null;
s.usr_start_date = null;
s.usr_ship_name = null;
s.usr_end_date = null;
s.usr_date_of_the_service = null;
s.usr_cruise_line = null;
s.suggestionRejectCount = null;
s.suggestedStartDate = null;
s.suggestedEndDate = null;
s.start_date = null;
s.ship_name = null;
s.service_date = null;
s.resolvedProductCount = null;
s.resolvedPhoneNumber = null;
s.resolvedCountry = null;
s.requestedDate = null;
s.productsToReturn = null;
s.partial_service_date = null;
s.lastUserStartDate = null;
s.end_date = null;
s.cruise_line = null;

context.session.BotUserSession.empathyMessage =null;
context.session.BotUserSession.creditCardLast4Digits =null;
context.session.BotUserSession.TicketId = null;
context.session.BotUserSession.bookingNumber = null;
context.session.BotUserSession.ProductsCollected = null;
context.session.BotUserSession.PCAgentPurchasedDate = null;


// --------------------
// Clear date orchestrator state
// --------------------
context.entities.start_date = null;
context.entities.end_date = null;
context.entities.service_date = null;
context.entities.ship_name = null;
context.entities.cruise_line = null;
context.entities.vessel_id = null;

s.toolCallDone = null;
s.itineraryValidated = null;
s.dateSkippedFields = null;
s.currentlyAskingField = null;
s.waitingForConfirm = null;

s.start_date_askCount = null;
s.end_date_askCount = null;
s.service_date_askCount = null;

s.partial_start_date = null;
s.partial_end_date = null;
s.partial_service_date = null;

s.lastRejectedDate = null;
s.vesselSkippedFields = null;
s.unknownIndicatedFields = null;

s.usr_vessel_id = null;

// Session-level orchestrator flags
context.session.dateCompleted = null;
context.session.vesselCompleted = null;
context.session.conversationState = null;
context.session.activeConversationAgent = null;
context.session.vessel_id = null;

// --------------------
// Clear stored products array
// --------------------
s.products = [];
s.all_products_summary = null;

// --------------------
// Clear extracted / formatted dates
// --------------------
context.dateValidation = null;
context.policyWindow = null;
context.PC_HomeDelivery_Script_SetRequestDate = null;

// --------------------
// Clear reason / return data
// --------------------
s.returnReason = null;
s.returnReasonMapped = null;
s.returnReasonText = null;
s.reasonDisplay = null;
s.otherReturnReason = null;
s.isWithinReturnPolicyPeriod = null;
s.isReturn24hCC = false;

// --------------------
// Clear conversation memory
// --------------------
s.initialMessage = null;
s.extractionStatus = null;
s.conversationHistory = [];
s.conversationHistoryString = "";
s.dateCompleted = null;

// --------------------
// Reset flags
// --------------------
s.agentNodeStarted = false;
s.isQueryRephrasing = false;

// --------------------
// Clear AI assisted dialog memory
// --------------------
context.AI_Assisted_Dialogs = context.AI_Assisted_Dialogs || {};

if (context.AI_Assisted_Dialogs.PC_Home_Delivery_Agent_CabinNumber) {
    context.AI_Assisted_Dialogs.PC_Home_Delivery_Agent_CabinNumber.entities = [];
}

if (context.AI_Assisted_Dialogs.PC_HomeDelivery_Agent_PurchasedDate) {
    context.AI_Assisted_Dialogs.PC_HomeDelivery_Agent_PurchasedDate.entities = [];
}

if (context.AI_Assisted_Dialogs.PC_HomeDelivery_Agent2_ReturnDetails) {
    context.AI_Assisted_Dialogs.PC_HomeDelivery_Agent2_ReturnDetails.entities = [];
}

if (context.AI_Assisted_Dialogs.PC_HomeDelivery_Agent_ProductDetails) {
    context.AI_Assisted_Dialogs.PC_HomeDelivery_Agent_ProductDetails.entities = {};
}

// --------------------
// Clear generative AI extraction memory
// --------------------
if (context.GenerativeAINode) {
    context.GenerativeAINode.PC_HomeDelivery_PromptNode = null;
}


//----------------------------
//// zendesk upload token 
//-----------------------------

context.session.BotUserSession.zd_tokens_combined = null;
context.zendeskUploadToken = null;
context.privatenotepayload = null;
context.TicketNumber = null;
context.session.BotUserSession.returnsFailedFieldsDisplay =  null;
context.session.BotUserSession.returnsFailedFields = null;
context.session.BotUserSession.productsToReturnJSON = null;
context.session.BotUserSession.lastVesselAttempt = null;
context.session.BotUserSession.lastCountedVesselValue = null;
context.session.BotUserSession.documentFailMessageDisplay = null;
context.session.BotUserSession.documentCreationDisplay = null;
context.session.BotUserSession.dateAmbiguityResolved = null;
context.session.BotUserSession.CurrentProductIndex = null;
context.session.BotUserSession.CurrentField = null;

context.session.BotUserSession.customerEmail = null;
context.session.BotUserSession.customerName =null;
context.entities.PC_Common_2_Entity_NameAsPerSpaRecords = null;
//context.session.BotUserSession.piiEntities = null; 

context.session.BotUserSession.vesselName = null;
context.session.BotUserSession.ticket = null;
context.session.BotUserSession.spa_record_name = null;
context.session.BotUserSession.sailDate = null;
context.session.BotUserSession.reasonTag = null;
context.session.BotUserSession.quantity = null;
context.session.BotUserSession.productsToReturnString = null;
context.session.BotUserSession.phone = null;
context.session.BotUserSession.inquiry = null;
context.session.BotUserSession.emailSubject = null;
context.session.BotUserSession.deliveryType = null;
context.session.BotUserSession.country = null;
context.session.BotUserSession.category = null;
context.session.BotUserSession.bookingNumberLine = null;
//context.session.BotUserSession.piiEntities = null;
context.session.BotUserSession.productsFormatted = null;
context.session.BotUserSession.piiEntities.phoneNumber = null;
context.session.BotUserSession.cabinExtractionCompleted = null;
context.session.BotUserSession.cabinAskCount = null;
context.session.BotUserSession.CabinNumbers = null;
context.session.BotUserSession.resolvedPurchasedDate = null;
context.session.BotUserSession.purchaseDate = null;


context.session.BotUserSession.bookingAttempt = 0;
context.session.BotUserSession.BookingNumberUnknown = false;

```
