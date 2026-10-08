# PC_HomeDelivery_Script_ProductCount  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_ProductCount",
  "type": "script"
}
```

## script
```
try {
    var AGENT_NODE = "PC_HomeDelivery_Agent_ProductCount";

    context.entities = context.entities || {};
    context.session  = context.session  || {};
    var s = context.session.BotUserSession = context.session.BotUserSession || {};

    function isResolved(v) {
        return v !== undefined && v !== null && v !== "" &&
               v !== "null" && v !== "UNKNOWN" && v !== "NOT PROVIDED";
    }

    var aiData = context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs[AGENT_NODE];
    if (!aiData) {
        koreDebugger.log("SCRIPT | No AI data for " + AGENT_NODE + " — skipping, not this agent's turn");
    } else if (s.exitReason === "exit_requested") {
        context.exitReason = "exit_requested";
        s.exitReason = null;
        koreDebugger.log("SCRIPT | " + AGENT_NODE + " → Routing to Cancel_Mid_Workflow");
    } else {
        context.exitReason = null;
        s.exitReason = null;

        if (!isResolved(context.entities.ProductCount) && isResolved(s.ProductCount)) {
            context.entities.ProductCount = s.ProductCount;
        }

        s.productCountCompleted = isResolved(context.entities.ProductCount) || s.ProductCountUnknown === true;
        s.returnDetailsCompleted = (s.countryCompleted === true) && (s.productCountCompleted === true);

        koreDebugger.log("SCRIPT | " + AGENT_NODE + " | ProductCount: " + context.entities.ProductCount +
                         " | completed: " + s.productCountCompleted +
                         " | returnDetailsCompleted: " + s.returnDetailsCompleted);
    }

} catch (e) {
    koreDebugger.log("SCRIPT AFTER ERROR: " + e.message);
}
```
