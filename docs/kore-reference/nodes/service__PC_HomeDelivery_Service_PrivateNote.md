# PC_HomeDelivery_Service_PrivateNote  (service)

## Config
```json
{
  "name": "PC_HomeDelivery_Service_PrivateNote",
  "endPoint": {
    "path": "{{env.ZendeskBaseUrl}}/api/v2/tickets/{{context.session.BotUserSession.TicketId}}",
    "method": "patch",
    "connectorEnabled": false
  },
  "authRequired": false,
  "payload": {
    "type": "raw",
    "value": "{{context.validationNotePayload}}"
  },
  "headers": {
    "type": "raw",
    "value": "{\"Authorization\":\"Basic {{env.ZendeskAuthorization}}\",\"Content-Type\":\"application/json\"}"
  },
  "serviceType": "rest",
  "idp": "none",
  "type": "service",
  "timeOutError": {
    "closeConversation": true
  },
  "serviceAPITimeout": 20,
  "isClientCertEnabled": true
}
```

## postProcessor
```
koreDebugger.log("Customer: " + context.session.BotUserSession.piiEntities.name);
koreDebugger.log("Email: " + context.session.BotUserSession.piiEntities.emailId);
```
