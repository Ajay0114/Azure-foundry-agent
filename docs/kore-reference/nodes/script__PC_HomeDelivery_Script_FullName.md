# PC_HomeDelivery_Script_FullName  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_FullName",
  "type": "script"
}
```

## script
```
context.session = context.session || {};
context.session.BotUserSession = context.session.BotUserSession || {};
var s = context.session.BotUserSession;

var agentData =
    context.AI_Assisted_Dialogs &&
    context.AI_Assisted_Dialogs.PC_HomeDelivery_Agent_SpaRecordName;

koreDebugger.log("SavePrimaryName | agentData: " + JSON.stringify(agentData));

var entityArray = [];
if (agentData && Array.isArray(agentData.entities)) {
    entityArray = agentData.entities;
}

for (var i = 0; i < entityArray.length; i++) {
    var item = entityArray[i];
    if (item && item.SpaRecordName && String(item.SpaRecordName).trim() !== "") {
        s.spa_record_name = String(item.SpaRecordName).trim();
    }
}

koreDebugger.log("SavePrimaryName | Saved spa_record_name: " + s.spa_record_name);

s.piiEntities = s.piiEntities || {};
s.piiEntities.sparecordname = s.spa_record_name;
```
