# HomeDelivery_Service_ScanUpload  (service)

## Config
```json
{
  "name": "HomeDelivery_Service_ScanUpload",
  "endPoint": {
    "path": "{{env.AzureFileAttachmentUrl}}/api/upload",
    "method": "post",
    "connectorEnabled": false
  },
  "authRequired": false,
  "payload": {
    "type": "raw",
    "value": "{{context.azurePayloadString}}"
  },
  "headers": {
    "type": "raw"
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

## headers.value
```
{"Content-Type":"application/json","x-functions-key":"{{env.AzureFunctionKey}}","x-bot-id":"marina","x-session-id":"{{context.session.BotUserSession.conversationSessionId}}","x-customer-email":"{{context.session.BotUserSession.customerEmail}}"}
```
