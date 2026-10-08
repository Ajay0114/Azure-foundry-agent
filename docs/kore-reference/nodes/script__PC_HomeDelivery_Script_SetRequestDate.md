# PC_HomeDelivery_Script_SetRequestDate  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_SetRequestDate",
  "type": "script"
}
```

## script
```
// YYYY-MM-DD - today's date
context.PC_HomeDelivery_Script_SetRequestDate = new Date().toISOString().slice(0, 10);

context.session.BotUserSession.requestedDate = context.PC_HomeDelivery_Script_SetRequestDate
```
