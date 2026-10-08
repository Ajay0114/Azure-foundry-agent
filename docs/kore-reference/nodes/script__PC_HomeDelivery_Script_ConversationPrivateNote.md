# PC_HomeDelivery_Script_ConversationPrivateNote  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_ConversationPrivateNote",
  "type": "script"
}
```

## script
```
context.TicketNumber =
    context.PC_HomeDelivery_Service_CreateTicket.response.body.ticket.id;

context.session = context.session || {};
context.session.BotUserSession = context.session.BotUserSession || {};

var s = context.session.BotUserSession;

// Get conversation history
var conversation = "No conversation";

if (
    s.conversationHistory &&
    s.conversationHistory.length > 0
) {
    conversation = s.conversationHistory.join("<br><br>").trim();

    if (!conversation) {
        conversation = "No conversation";
    }
}

// Create separate private note payload for conversation
var conversationPayload = {
    "ticket": {
        "comment": {
            "html_body":
                "<b>Conversation Transcript - Product Details : </b><br>" +
                "------------------------------------------<br><br>" +
                conversation,
            "public": false
        }
    }
};

// Store in a different context variable
context.conversationPayload = JSON.stringify(conversationPayload);

// Debug logs
koreDebugger.log("Ticket ID: " + context.TicketNumber);
koreDebugger.log("Conversation Payload: " + context.conversationPayload);
```
