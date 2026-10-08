# PC_HomeDelivery_Script_PrivateNotePayload  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_PrivateNotePayload",
  "type": "script"
}
```

## script
```
context.TicketNumber = context.PC_HomeDelivery_Service_CreateTicket.response.body.ticket.id;


var uploads = Array.isArray(context.zendeskUploadToken)
    ? context.zendeskUploadToken
    : [];
// var uploadToken = JSON.parse(context.zendeskUploadToken);

var privatenotepayload = {
  "ticket": {
    "comment": {
      "html_body": "<b> ATTACHMENT : </b><br>---------------------<br>",
      "public": false,
      "uploads": uploads
    }
  }
};

context.privatenotepayload = JSON.stringify(privatenotepayload);

koreDebugger.log("IsArray: " + Array.isArray(uploads));
koreDebugger.log("Payload: " + JSON.stringify(privatenotepayload));



koreDebugger.log("Ticket ID: " + context.TicketNumber);



koreDebugger.log("payload: " + context.privatenotepayload);
```
