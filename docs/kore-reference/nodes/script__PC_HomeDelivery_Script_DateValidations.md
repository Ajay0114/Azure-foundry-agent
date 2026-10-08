# PC_HomeDelivery_Script_DateValidations  (script)

## Config
```json
{
  "name": "PC_HomeDelivery_Script_DateValidations",
  "type": "script"
}
```

## script
```
// =================================================================
// 1. INITIALIZATION & SESSION SETUP
// =================================================================
var rawDate = null;
var lastUserMsg = "";

if (!context.session) { context.session = {}; }
if (!context.session.BotUserSession) { context.session.BotUserSession = {}; }
var s = context.session.BotUserSession;

if (typeof context.dateRetryCount === "undefined") {
    context.dateRetryCount = 0;
}

// =================================================================
// 2. PARSE LAST USER MESSAGE
// =================================================================
try {
    lastUserMsg = (
        s.lastMessage &&
        s.lastMessage.messagePayload &&
        s.lastMessage.messagePayload.message &&
        s.lastMessage.messagePayload.message.body
    ) || "";
    lastUserMsg = String(lastUserMsg).toLowerCase().trim();
} catch (e) {
    koreDebugger.log("ERROR parsing lastUserMsg: " + e.message);
}

// =================================================================
// 3. EXIT SCENARIO DETECTION
// =================================================================
var pureExitPhrases = [
    "i do not want to continue this anymore",
    "i don't want to continue this anymore",
    "i dont want to continue this anymore",
    "i don't want to continue",
    "i dont want to continue",
    "i don't need this anymore",
    "i dont need this anymore",
    "stop the process",
    "end the conversation",
    "end this conversation",
    "end this request",
    "end this",
    "cancel this request",
    "cancel this",
    "stop this",
    "i want to cancel",
    "i want to exit",
    "i want to discard",
    "i want to stop"
];

function isStandaloneExitCommand(msg) {
    var cleanedMsg = msg.replace(/[.!?,]/g, "").trim();
    return ["exit", "cancel", "quit", "discard", "terminate"].indexOf(cleanedMsg) !== -1;
}

var isPureExit = pureExitPhrases.some(function(phrase) {
    return lastUserMsg.indexOf(phrase) !== -1;
}) || isStandaloneExitCommand(lastUserMsg);

if (isPureExit) {
    koreDebugger.log("EXIT SCENARIO TRIGGERED");
    context.purchaseDateFormatted = null;
    context.dateValidation = "exit_requested";
    context.policyWindow = "exit_requested";
    context.exitReason = "exit_requested";
    return;
}

// =================================================================
// 4. RETRIEVE PURCHASED DATE (HYBRID DEFENSIVE FALLBACK)
// =================================================================
var agentNode = context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs.PC_HomeDelivery_Agent_PurchasedDate;

if (context.entities && context.entities.PC_HomeDelivery_Entity_PurchasedDate) {
    rawDate = context.entities.PC_HomeDelivery_Entity_PurchasedDate;
} else if (context.entities && context.entities.PurchasedDate) {
    rawDate = context.entities.PurchasedDate;
} else if (s && (s.PurchasedDate || s.PCAgentPurchasedDate)) {
    rawDate = s.PurchasedDate || s.PCAgentPurchasedDate;
} else if (agentNode && agentNode.entities) {
    if (Array.isArray(agentNode.entities) && agentNode.entities.length > 0) {
        var firstEnt = agentNode.entities[0];
        rawDate = firstEnt.PurchasedDate || firstEnt.value || firstEnt;
    } else if (typeof agentNode.entities === "object" && agentNode.entities.PurchasedDate) {
        rawDate = agentNode.entities.PurchasedDate;
    }
}

var cruiseStartDate = s.usr_start_date || s.start_date;
var cruiseEndDate = s.usr_end_date || s.end_date;

if (rawDate && String(rawDate).toLowerCase() === "unknown") {
    context.dateValidation = "unknown";
    context.policyWindow = "unknown";
    s.purchaseDateFormatted = null;
    return;
}

// =================================================================
// 5. REPEAT REJECTION CHECK
// =================================================================
var lastRejectedDate = s.lastRejectedPurchaseDate || null;
if (rawDate && lastRejectedDate && String(rawDate) === String(lastRejectedDate)) {
    koreDebugger.log("REPEAT DETECTION | Same rejected date re-entered: " + rawDate);
    context.dateValidation = "unknown";
    context.policyWindow = "unknown";
    s.purchaseDateFormatted = null;
    s.isWithinReturnPolicyPeriod = false;
    s.purchaseDateAPI = null;
    return;
}

// =================================================================
// 6. DATE VALIDATION & CRUISE RANGE EVALUATION
// =================================================================
if (!rawDate) {
    context.dateRetryCount++;
    context.dateValidation = context.dateRetryCount >= 4 ? "unknown" : "invalid";
    context.policyWindow = "unknown";
} else {
    var cleanRawDate = String(rawDate).replace(/(\d+)(st|nd|rd|th)/gi, "$1").trim();
    var has4DigitYear = /\b(19|20)\d{2}\b/.test(cleanRawDate);

    if (!has4DigitYear) {
        koreDebugger.log("VALIDATION | Rejecting date without 4-digit year: " + cleanRawDate);
        context.dateRetryCount++;
        context.dateValidation = context.dateRetryCount >= 4 ? "unknown" : "invalid";
        context.policyWindow = "unknown";
    } else {
        var parsedYear, parsedMonth, parsedDay;
        var mmddyyyyMatch = cleanRawDate.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
        var yyyymmddMatch = cleanRawDate.match(/^(\d{4})[\-\/](\d{1,2})[\-\/](\d{1,2})$/);

        if (mmddyyyyMatch) {
            parsedMonth = parseInt(mmddyyyyMatch[1], 10) - 1;
            parsedDay = parseInt(mmddyyyyMatch[2], 10);
            parsedYear = parseInt(mmddyyyyMatch[3], 10);
        } else if (yyyymmddMatch) {
            parsedYear = parseInt(yyyymmddMatch[1], 10);
            parsedMonth = parseInt(yyyymmddMatch[2], 10) - 1;
            parsedDay = parseInt(yyyymmddMatch[3], 10);
        } else {
            var dObj = new Date(cleanRawDate);
            if (!isNaN(dObj.getTime())) {
                parsedYear = dObj.getFullYear();
                parsedMonth = dObj.getMonth();
                parsedDay = dObj.getDate();
            }
        }

        if (parsedYear === undefined || isNaN(parsedYear)) {
            context.dateRetryCount++;
            context.dateValidation = context.dateRetryCount >= 4 ? "unknown" : "invalid";
            context.policyWindow = "unknown";
        } else {
            var enteredUTC = Date.UTC(parsedYear, parsedMonth, parsedDay);
            var now = new Date();
            var todayUTC = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());

            var mm = String(parsedMonth + 1).padStart(2, "0");
            var dd = String(parsedDay).padStart(2, "0");
            var formattedDate = parsedYear + "-" + mm + "-" + dd;

            var isWithinCruiseRange = true;
            if (cruiseStartDate && cruiseEndDate) {
                var cStartObj = new Date(cruiseStartDate);
                var cEndObj = new Date(cruiseEndDate);

                if (!isNaN(cStartObj.getTime()) && !isNaN(cEndObj.getTime())) {
                    var cStartUTC = Date.UTC(cStartObj.getFullYear(), cStartObj.getMonth(), cStartObj.getDate());
                    var cEndUTC = Date.UTC(cEndObj.getFullYear(), cEndObj.getMonth(), cEndObj.getDate());

                    if (enteredUTC < cStartUTC || enteredUTC > cEndUTC) {
                        isWithinCruiseRange = false;
                    }
                }
            }

            if (enteredUTC > todayUTC) {
                context.dateRetryCount++;
                context.dateValidation = context.dateRetryCount >= 4 ? "unknown" : "future";
                context.policyWindow = "unknown";
                s.lastRejectedPurchaseDate = rawDate;
            } else if (!isWithinCruiseRange) {
                context.dateRetryCount++;
                context.dateValidation = context.dateRetryCount >= 4 ? "unknown" : "outside_cruise_range";
                context.policyWindow = "unknown";
                s.lastRejectedPurchaseDate = rawDate;
            } else {
                var diffTime = todayUTC - enteredUTC;
                var diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

                context.dateRetryCount = 0;
                s.lastRejectedPurchaseDate = null;
                context.dateValidation = "valid";
                context.policyWindow = diffDays <= 60 ? "within_policy" : "outside_policy";

                s.purchaseDateFormatted = formattedDate;
                koreDebugger.log("DATE SAVED: " + formattedDate);
            }
        }
    }
}

// =================================================================
// 7. CLEANUP & FINAL MAPPING
// =================================================================
if (context.dateValidation !== "valid") {
    s.purchaseDateFormatted = null;
    s.isWithinReturnPolicyPeriod = false;
    s.purchaseDateAPI = null;
}

s.isWithinReturnPolicyPeriod = (context.policyWindow === "within_policy");
s.lastEnteredDate = s.purchaseDateFormatted || null;
s.purchaseDateAPI = s.purchaseDateFormatted || null;
```
