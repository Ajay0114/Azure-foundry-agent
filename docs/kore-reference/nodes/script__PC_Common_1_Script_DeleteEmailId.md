# PC_Common_1_Script_DeleteEmailId  (script)

## Config
```json
{
  "name": "PC_Common_1_Script_DeleteEmailId",
  "type": "script"
}
```

## script
```
delete  context.entities.PC_Common_1_Entity_Emailid;
delete context.session.BotUserSession.piiEntities.emailId;
```
