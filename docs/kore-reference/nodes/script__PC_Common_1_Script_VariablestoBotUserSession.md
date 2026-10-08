# PC_Common_1_Script_VariablestoBotUserSession  (script)

## Config
```json
{
  "name": "PC_Common_1_Script_VariablestoBotUserSession",
  "type": "script"
}
```

## script
```
context.session.BotUserSession.customerName = context.entities.PC_Common_1_Entity_Name;


context.session.BotUserSession.customerEmail = context.entities.PC_Common_1_Entity_Emailid




    koreDebugger.log(
        "EMailPII123 " +
        context.session.BotUserSession.piiEntities.PC_Common_1_Entity_Emailid
    );

    koreDebugger.log(
        "assigned " +
        context.session.BotUserSession.customerEmail
    );
```
