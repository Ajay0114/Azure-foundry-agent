# PC_HomeDelivery_ReturnsDocumentFail  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_ReturnsDocumentFail",
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
    s.returnsFailedFieldsDisplay ||
    "Unknown validation error";

// Build internal note
var noteBody =
    "<b>RETURNS DOCUMENT VALIDATION FAILED</b><br>" +
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
    "Returns Validation note payload: " +
    context.validationNotePayload
);
```
