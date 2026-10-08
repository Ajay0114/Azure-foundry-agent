# PC_HomeDelivery_DocumentCreation_Service_Transcations  (service)

## Config
```json
{
  "name": "PC_HomeDelivery_DocumentCreation_Service_Transcations",
  "endPoint": {
    "path": "{{env.Document_Creation}}/cscbot/post-voyage/transactions/documents/requests",
    "method": "post",
    "connectorEnabled": false
  },
  "authRequired": true,
  "payload": {
    "type": "raw"
  },
  "headers": {
    "type": "raw",
    "value": "{\"Content-Type\":\"application/json\"}"
  },
  "serviceType": "rest",
  "preProcessor": "koreDebugger.log(\"NameasperSPA: \" + context.session.BotUserSession.piiEntities.nameAsPerSpa);",
  "idp": "Transaction1780516436264",
  "type": "service",
  "timeOutError": {
    "closeConversation": true
  },
  "serviceAPITimeout": 20,
  "isClientCertEnabled": true
}
```

## payload.value
```
{"referenceId":"{{context.session.BotUserSession.TicketId}}","parameters":{"vesselId":"{{context.session.BotUserSession.usr_vessel_id}}","startDate":"{{context.session.BotUserSession.usr_start_date}}","endDate":"{{context.session.BotUserSession.usr_end_date}}","guestsFullNames":["{{context.session.BotUserSession.piiEntities.sparecordname}}"],"cabins":["{{context.session.BotUserSession.CabinNumber}}"]}}
```

## postProcessor
```
koreDebugger.log("Customer: " + context.session.BotUserSession.piiEntities.name);
koreDebugger.log("Email: " + context.session.BotUserSession.piiEntities.emailId);
```
