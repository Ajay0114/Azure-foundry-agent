# PC_Cruise_Entities  (script)

## Config
```json
{
  "name": "PC_Cruise_Entities",
  "type": "script"
}
```

## script
```
try {
    context.session = context.session || {};
    context.session.BotUserSession = context.session.BotUserSession || {};
    context.entities = context.entities || {};

    var session = context.session.BotUserSession;
    var ent = context.entities;

    // Save vessel entities to BotUserSession
    // Only set if value exists — never overwrite existing with null
    if (ent.ship_name)   session.usr_ship_name   = ent.ship_name;
    if (ent.cruise_line) session.usr_cruise_line = ent.cruise_line;
    if (ent.vessel_id)   session.usr_vessel_id   = ent.vessel_id;

    koreDebugger.log("VESSEL SCRIPT | usr_ship_name: "   + session.usr_ship_name);
    koreDebugger.log("VESSEL SCRIPT | usr_cruise_line: " + session.usr_cruise_line);
    koreDebugger.log("VESSEL SCRIPT | usr_vessel_id: "   + session.usr_vessel_id);

} catch (e) {
    koreDebugger.log("VESSEL SCRIPT ERROR: " + e);
}
```
