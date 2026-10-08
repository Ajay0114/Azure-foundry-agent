# DocumentCreation_Service_Returns  (service)

## Config
```json
{
  "name": "DocumentCreation_Service_Returns",
  "endPoint": {
    "path": "{{env.Document_Creation}}/cscbot/post-voyage/products-return/documents/requests",
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
  "idp": "Returns1780516436263",
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
{"referenceId":"{{context.session.BotUserSession.TicketId}}","parameters":{"guestFullname":"{{context.session.BotUserSession.spa_record_name}}","eMail":"{{context.session.BotUserSession.piiEntities.emailId}}","phone":"{{context.session.BotUserSession.piiEntities.phoneNumber}}","countryName":"{{context.session.BotUserSession.Country}}","cruiseLineName":"{{context.session.BotUserSession.usr_cruise_line}}","vesselName":"{{context.session.BotUserSession.usr_ship_name}}","cabinNumber":"{{context.session.BotUserSession.CabinNumber}}","embarkationDate":"{{context.session.BotUserSession.usr_start_date}}","purchaseDate":"{{context.session.BotUserSession.purchaseDateAPI}}","returnRequestDate":"{{context.session.BotUserSession.requestedDate}}","isWithinReturnPolicyPeriod":{{context.session.BotUserSession.isWithinReturnPolicyPeriod}},"returnReasons":["{{context.session.BotUserSession.returnReasonMapped}}"]{{context.session.BotUserSession.otherReturnReasonLine}}{{context.session.BotUserSession.bookingNumberLine}},"creditCardLast4Digits":"{{context.session.BotUserSession.piiEntities.creditcard}}","productsToReturn":{{context.session.BotUserSession.productsToReturnString}}},"clientMetadata":[{"name":"Key1","value":"Value1"},{"name":"Key2","value":"Value2"}]}
```

## postProcessor
```
koreDebugger.log("Customer: " + context.session.BotUserSession.piiEntities.name);
koreDebugger.log("Email: " + context.session.BotUserSession.piiEntities.emailId);
```
