# PC_HomeDelivery_Service_PrivateNoteAttachmentAPI  (service)

## Config
```json
{
  "name": "PC_HomeDelivery_Service_PrivateNoteAttachmentAPI",
  "endPoint": {
    "path": "{{env.ZendeskBaseUrl}}/api/v2/tickets/{{context.TicketNumber}}",
    "method": "patch",
    "connectorEnabled": false
  },
  "authRequired": false,
  "payload": {
    "type": "raw",
    "value": "{{context.privatenotepayload}} "
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
