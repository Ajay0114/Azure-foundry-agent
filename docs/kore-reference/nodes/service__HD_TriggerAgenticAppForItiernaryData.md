# HD_TriggerAgenticAppForItiernaryData  (service)

## Config
```json
{
  "name": "HD_TriggerAgenticAppForItiernaryData",
  "endPoint": {
    "path": "{{env.PostCruiseServiceOrchestrationEngine}}",
    "method": "post",
    "connectorEnabled": false
  },
  "authRequired": false,
  "payload": {
    "type": "raw"
  },
  "headers": {
    "type": "raw",
    "value": "{\"x-api-key\":\"{{env.PostCruiseServiceOrchestrationEngine_Api_key}}\",\"Content-Type\":\"application/json\"}"
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

## payload.value
```
{"sessionIdentity":[{"type":"userReference","value":"{{context.ccId}}"},{"type":"sessionReference","value":"{{context.contextId}}"}],"input":[{"type":"text","content":"Validate vessel {{context.AI_Assisted_Dialogs.HD_CruiseDateOrchestrator.active_tool_args.vesselId}} on {{context.AI_Assisted_Dialogs.HD_CruiseDateOrchestrator.active_tool_args.startDate.replace(/-/g,'')}}"}],"stream":{"enable":false},"debug":{"enable":false}}
```

## postProcessor
```
var res = context.
HD_TriggerAgenticAppForItiernaryData;

if (res?.response?.body?.output?.length > 0) {
    context.toolPayload = res.response.body.output[0].content;
}
else if (res?.body?.output?.length > 0) {
    context.toolPayload = res.body.output[0].content;
}
else {
    context.toolPayload = "No vessel data found.";
}
```
