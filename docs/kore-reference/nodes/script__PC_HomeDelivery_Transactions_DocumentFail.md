# PC_HomeDelivery_Transactions_DocumentFail  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Transactions_DocumentFail",
  "type": "script"
}
```

## script
```
context.session = context.session || {};
context.session.BotUserSession = context.session.BotUserSession || {};

var s = context.session.BotUserSession;

// Store Ticket ID
s.TicketId =
    context.PC_HomeDelivery_Service_CreateTicket.response.body.ticket.id;

// Get failed validation fields
var failedText =
    s.transactionFailedFieldsDisplay ||
    context.validation_failed_fields ||
    "Unknown validation error";

// Build internal note
var noteBody =
    "<b>TRANSACTION DOCUMENT VALIDATION FAILED</b><br>" +
    "---------------------<br>" +
    "<b>Missing or invalid:</b> " +
    failedText;

// Create payload for Zendesk internal note
context.validationNotePayload = JSON.stringify({
    ticket: {
        comment: {
            html_body: noteBody,
            public: false
        }
    }
});

// Debug log
koreDebugger.log(
    "Transaction Validation note payload: " +
    context.validationNotePayload
);
```
