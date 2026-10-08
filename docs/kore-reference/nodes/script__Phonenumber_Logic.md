# Phonenumber_Logic  (script)

## Config
```json
{
  "name": "Phonenumber_Logic",
  "type": "script"
}
```

## script
```
try {
    context.entities = context.entities || {};
    context.session  = context.session  || {};
    var s = context.session.BotUserSession = context.session.BotUserSession || {};
    s.piiEntities = s.piiEntities || {};

    var phone = s.piiEntities.phoneNumber || null;

    var isMissing = !phone ||
                    String(phone).trim() === "" ||
                    String(phone).toUpperCase() === "UNKNOWN" ||
                    String(phone).toUpperCase() === "NOT PROVIDED";

    context.entities.PhoneNumberMissing = isMissing;

    koreDebugger.log("SCRIPT | PhoneNumber: " + phone +
                     " | PhoneNumberMissing: " + isMissing);

} catch (e) {
    koreDebugger.log("SCRIPT ERROR: " + e.message);
    // Fail safe: if anything blew up, assume missing so we ask rather than skip
    context.entities = context.entities || {};
    context.entities.PhoneNumberMissing = true;
}
```
