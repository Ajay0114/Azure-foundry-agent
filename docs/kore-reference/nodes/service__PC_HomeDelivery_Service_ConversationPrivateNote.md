# PC_HomeDelivery_Service_ConversationPrivateNote  (service)

## Config
```json
{
  "name": "PC_HomeDelivery_Service_ConversationPrivateNote",
  "endPoint": {
    "path": "{{env.ZendeskBaseUrl}}/api/v2/tickets/{{context.TicketNumber}}",
    "method": "patch",
    "connectorEnabled": false
  },
  "authRequired": false,
  "payload": {
    "type": "raw",
    "value": "{{context.conversationPayload}}"
  },
  "headers": {
    "type": "raw",
    "value": "{\"Content-Type\":\"application/json\",\"Authorization\":\"Basic {{env.ZendeskAuthorization}}\"}"
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
