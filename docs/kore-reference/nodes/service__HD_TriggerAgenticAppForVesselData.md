# HD_TriggerAgenticAppForVesselData  (service)

## Config
```json
{
  "name": "HD_TriggerAgenticAppForVesselData",
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
{"sessionIdentity":[{"type":"userReference","value":"{{context.ccId}}"},{"type":"sessionReference","value":"{{context.contextId}}"}],"input":[{"type":"text","content":"{{context.AI_Assisted_Dialogs.HD_VesselLookupAgent.active_tool_args.input}}"}],"stream":{"enable":false},"debug":{"enable":false}}
```

## postProcessor
```
try {
    if (
        context.HD_TriggerAgenticAppForVesselData &&
        context.HD_TriggerAgenticAppForVesselData.response &&
        context.HD_TriggerAgenticAppForVesselData.response.body &&
        context.HD_TriggerAgenticAppForVesselData.response.body.output &&
        context.HD_TriggerAgenticAppForVesselData.response.body.output.length > 0
    ) {
        context.toolPayload = context.HD_TriggerAgenticAppForVesselData.response.body.output[0].content;
        koreDebugger.log("toolPayload set: " + context.toolPayload);
    } else {
        context.toolPayload = "No vessel data found.";
        koreDebugger.log("No output from service node");
    }
} catch (e) {
    koreDebugger.log("Service Post-Processor Error: " + e);
    context.toolPayload = "No vessel data found.";
}
```
