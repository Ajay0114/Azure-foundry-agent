# PC_HomeDelivery_DocumentCreationFail  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_DocumentCreationFail",
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

// Build internal note
var noteBody =
    "<b>DOCUMENT VALIDATION FAILED</b><br>" +
    "---------------------<br>" +
    "<b>Returns Missing or Invalid:</b> " +
    (s.returnsFailedFieldsDisplay || "None") +
    "<br><br>" +
    "<b>Transaction Missing or Invalid:</b> " +
    (s.transactionFailedFieldsDisplay || "None");

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
    "Combined Validation note payload: " +
    context.validationNotePayload
);
```
