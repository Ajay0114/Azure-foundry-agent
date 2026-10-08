# PC_HomeDelivery_Script_CabinNumber  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_CabinNumber",
  "type": "script"
}
```

## script
```
try {
    context.entities = context.entities || {};
    context.session  = context.session  || {};
    var s = context.session.BotUserSession = context.session.BotUserSession || {};

    function isResolved(v) {
        return v !== undefined && v !== null && v !== "" &&
               v !== "null" && v !== "UNKNOWN" && v !== "NOT PROVIDED";
    }

    if (s.exitReason === "exit_requested") {
        context.exitReason = "exit_requested";   // transition condition reads this
        s.exitReason = null;                     // consume the flag
        koreDebugger.log("SCRIPT | Routing to Cancel_Mid_Workflow");
    } else {
        context.exitReason = null;
        s.exitReason = null;

        // Safety net: restore from session if entity slot was reset
        if (!isResolved(context.entities.CabinNumber) && isResolved(s.CabinNumber)) {
            context.entities.CabinNumber = s.CabinNumber;
        }
        if ((!context.entities.CabinNumbers || !context.entities.CabinNumbers.length) &&
            Array.isArray(s.CabinNumbers) && s.CabinNumbers.length) {
            context.entities.CabinNumbers = s.CabinNumbers;
        }

        s.cabinExtractionCompleted = isResolved(context.entities.CabinNumber);

        koreDebugger.log("SCRIPT | CabinNumber: " + context.entities.CabinNumber +
                         " | CabinNumbers: " + JSON.stringify(context.entities.CabinNumbers) +
                         " | completed: " + s.cabinExtractionCompleted +
                         " | unknown: " + (s.CabinNumberUnknown === true));
    }

} catch (e) {
    koreDebugger.log("SCRIPT AFTER ERROR: " + e.message);
}
```
