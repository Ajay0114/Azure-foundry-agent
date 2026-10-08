# PC_Common_1_Script_InitialUserMessage  (script)

## Config
```json
{
  "name": "PC_Common_1_Script_InitialUserMessage",
  "type": "script"
}
```

## script
```
// Store initial user message once

if (!context.session.BotUserSession.initialMessage) {
    context.session.BotUserSession.initialMessage =
        context.session.BotUserSession.lastMessage.messagePayload.message.body;
}

koreDebugger.log(
    "Initial Message: " +
    context.session.BotUserSession.initialMessage
);
```
