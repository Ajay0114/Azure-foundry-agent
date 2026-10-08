# PC_Home_Delivery_Agent_CabinNumber  (aiassist)

## Config
```json
{
  "name": "PC_Home_Delivery_Agent_CabinNumber",
  "type": "aiassist",
  "generativeAI": {
    "dynamicEntityConfig": {
      "dynamicEntities": [
        {
          "name": "CabinNumber",
          "type": "label"
        }
      ],
      "enabled": true,
      "model": "gpt-5.1",
      "icon": "https://platform.kore.ai/assets/integrations/32/customllm.png",
      "displayName": "Azure-OpenAI-GPT5.1 - gpt-5.1",
      "integrationName": "Azure-OpenAI-GPT5.1",
      "temperature": 0,
      "max_tokens": 0,
      "Noofprevioususerinputs": 10,
      "promptId": "1dc1534d-0354-52d9-b927-14132732ed8d",
      "promptName": "Agent_Node_GPT_5.1_Global_Prompt",
      "isCustom": true,
      "isSysIntAndCustomPrompt": false,
      "isStreaming": false,
      "exitScenarios": [
        null
      ],
      "fallbackBehavior": {
        "id": "dynamicEntity",
        "onLLMFail": "skipEvent",
        "nodeId": "nd-scr-8d5406f2-9805-4f70-b3a7-a7f40cf70012"
      }
    }
  }
}
```

## generativeAI.dynamicEntityConfig.exitScenarios.0
```
Exit when the user explicitly and unambiguously wants to stop, cancel, or discard the current support request — for example: "discard", "exit", "cancel", "quit", 
"stop", "nevermind", "I don't want to continue", "I don't need this anymore", "stop the process", "end the conversation", "end this", or "terminate".

Do NOT exit if the user is simply:
- Expressing uncertainty about a detail ("I think", "I believe", "I'm not sure", 
  "maybe", "probably", "I can't remember exactly")
- Providing an approximate answer ("around that time", "closer to the end")
- Asking a clarifying question
- Explaining context around their answer

Only treat it as an exit request if the user's intent to stop the process is clear and direct, not merely inferred from hedging language.
```

## generativeAI.dynamicEntityConfig.systemContext
```
CURRENT VALUE
-----------------------------------
CabinNumber: {{context.session.BotUserSession.resolvedCabinNumber}}
ATTEMPT NUMBER: {{context.session.BotUserSession.cabinAskCount}}
-----------------------------------
RULES
-----------------------------------
- Your job is ONLY to extract cabin number(s) and choose the correct bot message per ATTEMPT NUMBER below. Do NOT perform any other task, change conversation flow, or call any tool.
- If CURRENT VALUE is not "NOT_YET_PROVIDED", return it unchanged in entities and do not ask again.
- If no cabin number is found in the user message → set CabinNumber to null and CabinNumbers to [].
- NEVER return empty string "" for CabinNumber → use null.
- Do NOT hallucinate values.
-----------------------------------
CABIN NUMBER UNDERSTANDING
-----------------------------------
Extract the COMPLETE cabin number exactly as provided, preserving all letters and digits together:
- "cabin 4201" → "4201"
- "cabin A9202" → "A9202"
- "room 512" → "512"
- "room C1234" → "C1234"
- "my cabin is A1104" → "A1104"
Do NOT extract: order numbers, phone numbers, dates, quantities, or numbers without cabin/room context.
- "my order is 4201" → null
- "call me at 9876543210" → null
Exception: if the bot just asked for the cabin number and the user replies with only a number or alphanumeric code, treat that as the cabin number.

A valid cabin number token contains ONLY letters (A-Z, a-z) and digits (0-9). No spaces, no symbols (@ / # $ % & * ( ) _ + = ! ? ; : .).
- Valid: 449, A13, TS44, 9zi3, C1234
- Invalid: CN@394, TS/4494, 449#B

-----------------------------------
MULTIPLE CABIN NUMBERS
-----------------------------------
Users may give more than one cabin number, connected in natural language, not just commas. Extract ALL of them, in the order mentioned, into "CabinNumbers" as an array. Also set "CabinNumber" to the FIRST one found (for backward compatibility).

Accept these connectors between cabin numbers: comma, "and", "then", "moved to", "also", "or", "&".

Examples:
- "cabin 4201 and cabin 5102" → CabinNumber: "4201", CabinNumbers: ["4201","5102"]
- "cabins A101, B202, C303" → CabinNumber: "A101", CabinNumbers: ["A101","B202","C303"]
- "i was in 294 and then moved to TC03" → CabinNumber: "294", CabinNumbers: ["294","TC03"]
- "started in CN94 then moved to TS44" → CabinNumber: "CN94", CabinNumbers: ["CN94","TS44"]
- "my cabin is A1104" (single) → CabinNumber: "A1104", CabinNumbers: ["A1104"]
- no cabin found → CabinNumber: null, CabinNumbers: []

If the user separates cabin numbers with an invalid symbol instead of a comma or natural-language connector (e.g. "294@TC03", "294/TC03", "294;TC03", "294|TC03"), do NOT guess where one cabin number ends and the next begins. Treat this as unresolved for this turn and use the separator-correction message below instead of the normal "still missing" message, at whichever attempt number applies.

-----------------------------------
IMPORTANT PLATFORM CONSTRAINT
-----------------------------------
This node only gets ONE reply from the user after your question. There is
no third turn. So:
- ATTEMPT NUMBER 0 = this is the FIRST time you are asking. You may ask
  normally and expect a follow-up.
- ATTEMPT NUMBER 1 or higher = this is your LAST chance. Whatever the user
  says next, treat it as final — do not plan on asking again.
-----------------------------------
MESSAGE SELECTION (STRICT — use exact wording)
-----------------------------------
If ATTEMPT NUMBER is 0 and no valid cabin number is found, and the message used an invalid symbol separator:
  bot = "Please separate multiple cabin numbers using commas only. For example: 4201, 5102"
  conv_status = "ongoing"
If ATTEMPT NUMBER is 0 and CabinNumber is still missing (no separator issue):
  bot = "What's your cabin number? You'll find it on your end-of-cruise statement or your booking confirmation."
  conv_status = "ongoing"
If ATTEMPT NUMBER is 1 and no valid cabin number is found, and the message used an invalid symbol separator:
  bot = "Please separate multiple cabin numbers using commas only. For example: 4201, 5102"
  conv_status = "ongoing"
If ATTEMPT NUMBER is 1 and CabinNumber is still missing (no separator issue):
  bot = "I just need your cabin number to find your spa details for this cruise. It's usually a number like 8102 or D228."
  conv_status = "ongoing"
If ATTEMPT NUMBER is more than 1, and no valid cabin number is found in this message (blank, unrelated, or "don't know"/"not sure"):
  Set CabinNumber to "UNKNOWN" and CabinNumbers to []
  bot = "That's all right — I'll continue without it. I've noted your cabin number wasn't available, so our team can look it up when they follow up."
  conv_status = "ended"
If one or more valid cabin numbers ARE found (at any attempt):
  bot = "Thanks, I've noted your cabin number."
  conv_status = "ended"
-----------------------------------
OUTPUT FORMAT (STRICT)
-----------------------------------
Return ONLY a valid JSON object, nothing else:
{"bot": "your message here", "conv_status": "ongoing or ended", "entities": {"CabinNumber": "first extracted value, UNKNOWN, or null", "CabinNumbers": ["array of all cabin numbers found, or empty array"]}}
ALWAYS return the ACTUAL extracted value — never placeholders.
```

## generativeAI.preProcessorScript
```
try {
    context.entities = context.entities || {};
    context.session  = context.session  || {};
    var s = context.session.BotUserSession = context.session.BotUserSession || {};

    function isResolved(v) {
        return v !== undefined && v !== null && v !== "" &&
               v !== "null" && v !== "UNKNOWN" && v !== "NOT PROVIDED";
    }

    if (context.AI_Assisted_Dialogs) {
        delete context.AI_Assisted_Dialogs.exit_scenario;
        delete context.AI_Assisted_Dialogs.bot_response;
    }

    var staleKeys = [
        "usr_start_date", "usr_end_date", "usr_date_of_the_service",
        "start_date", "end_date", "service_date", "requestedDate",
        "lastUserStartDate", "suggestedStartDate", "suggestedEndDate",
        "partial_start_date", "lastEnteredDate"
    ];
    staleKeys.forEach(function(k) { delete context.entities[k]; });

    // Restore the primary comma-separated CabinNumber string from session
    if (!isResolved(context.entities.CabinNumber) && isResolved(s.CabinNumber)) {
        context.entities.CabinNumber = s.CabinNumber;
    }

    // Restore the parallel array too (per-cabin access downstream if ever needed)
    if ((!context.entities.CabinNumbers || !context.entities.CabinNumbers.length) &&
        Array.isArray(s.CabinNumbers) && s.CabinNumbers.length) {
        context.entities.CabinNumbers = s.CabinNumbers;
    }

    // Runs once at node entry only — 0 means this is the FIRST turn the
    // user sees in this node. Since the node force-exits after the
    // NEXT turn no matter what, attempt "1" is effectively the LAST chance.
    if (typeof s.cabinAskCount !== "number") {
        s.cabinAskCount = 0;
    }

    s.resolvedCabinNumber = isResolved(context.entities.CabinNumber)
        ? String(context.entities.CabinNumber)
        : "NOT_YET_PROVIDED";

    koreDebugger.log("=== PC_Home_Delivery_Agent_CabinNumber PRE ===");
    koreDebugger.log("PRE | CabinNumber: " + s.resolvedCabinNumber + " | askCount: " + s.cabinAskCount);

} catch (e) {
    koreDebugger.log("PRE ERROR: " + e.message);
}
```

## generativeAI.postProcessorScript
```
try {
    var node   = context.currentNodeName;
    var aiData = context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs[node];

    if (aiData) {
        var ent = aiData.entities || {};
        if (Array.isArray(ent)) {
            var merged = {};
            ent.forEach(function(e) { if (e) Object.assign(merged, e); });
            ent = merged;
        }

        context.entities = context.entities || {};
        context.session  = context.session  || {};
        var s = context.session.BotUserSession = context.session.BotUserSession || {};

        function isResolved(v) {
            return v !== undefined && v !== null && v !== "" &&
                   v !== "null" && v !== "UNKNOWN" && v !== "NOT PROVIDED";
        }
        function isValidCabinToken(v) {
            var t = String(v).trim();
            return /^[A-Za-z0-9]{1,10}$/.test(t);
        }

        var MSG_FALLBACK = "That's all right — I'll continue without it. I've noted your cabin number wasn't available, so our team can look it up when they follow up.";

        // ---------- EXIT DETECTION (unchanged) ----------
        var lastUserMsg = "";
        try {
            lastUserMsg = String(
                (s.lastMessage && s.lastMessage.messagePayload &&
                 s.lastMessage.messagePayload.message &&
                 s.lastMessage.messagePayload.message.body) || ""
            ).toLowerCase().trim();
        } catch (e2) {}

        var pureExitPhrases = [
            "i do not want to continue this anymore", "i don't want to continue this anymore",
            "i dont want to continue this anymore", "i don't want to continue", "i dont want to continue",
            "i don't need this anymore", "i dont need this anymore", "stop the process",
            "end the conversation", "end this conversation", "end this request", "end this",
            "cancel this request", "cancel this", "stop this", "i want to cancel",
            "i want to exit", "i want to discard", "i want to stop"
        ];
        var pureExitWords = ["discard", "cancel", "exit", "quit", "terminate"];
        var exclusionPhrases = [
            "cancel that", "cancel that thought", "cancel the", "cancel my", "cancel your",
            "cancel their", "cancel it", "cancel a ", "cancel my subscription", "cancelled",
            "cancellation", "canceling", "cancelling", "stop me if", "stop the", "stop my",
            "stop charging", "end of", "end the", "end my", "by the end", "toward the end",
            "at the end", "close to", "quite", "exiting", "exit the", "exit a ", "discarded", "discarding"
        ];
        function matchesWordBoundary(word, str) {
            var escaped = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            return new RegExp('(^|[^a-zA-Z])' + escaped + '([^a-zA-Z]|$)', 'i').test(str);
        }
        var isExcluded = exclusionPhrases.some(function(p) { return lastUserMsg.indexOf(p) !== -1; });
        var isPureExit = pureExitPhrases.some(function(p) { return lastUserMsg.indexOf(p) !== -1; });
        if (!isPureExit && !isExcluded) {
            isPureExit = pureExitWords.some(function(w) { return matchesWordBoundary(w, lastUserMsg); });
        }

        koreDebugger.log("POST | AI Returned: " + JSON.stringify(ent) +
                         " | LLM conv_status: " + aiData.conv_status +
                         " | isPureExit: " + isPureExit +
                         " | askCount: " + s.cabinAskCount);

        // ---------- ENTITY CAPTURE / VALIDATION ----------
        var validCabins = [];

        if (Array.isArray(ent.CabinNumbers) && ent.CabinNumbers.length) {
            ent.CabinNumbers.forEach(function(c) {
                if (c === null || c === undefined) return;
                var cc = String(c).trim().toUpperCase();
                if (isValidCabinToken(cc) && validCabins.indexOf(cc) === -1) {
                    validCabins.push(cc);
                }
            });
        }

        // Fallback: LLM only returned a single CabinNumber, no array
        if (!validCabins.length && isResolved(ent.CabinNumber)) {
            var single = String(ent.CabinNumber).trim().toUpperCase();
            if (isValidCabinToken(single)) {
                validCabins.push(single);
            } else {
                koreDebugger.log("POST | Rejected invalid cabin format: " + single);
            }
        }

        if (validCabins.length && !isResolved(context.entities.CabinNumber)) {
            context.entities.CabinNumber  = validCabins.join(", ");
            context.entities.CabinNumbers = validCabins;
            s.CabinNumber  = context.entities.CabinNumber;
            s.CabinNumbers = validCabins;
            s.resolvedCabinNumber = context.entities.CabinNumber;
        }

        var done = isResolved(context.entities.CabinNumber);
        s.cabinAskCount = (typeof s.cabinAskCount === "number") ? s.cabinAskCount : 0;

        // ---------- DECIDE (guardrail only — LLM already picked wording) ----------
        if (isPureExit) {
            s.exitReason = "exit_requested";
            aiData.conv_status = "ended";
            aiData.bot = "Okay, cancelling this request.";
            koreDebugger.log("POST | EXIT requested → ending node");
        } else if (done) {
            s.exitReason = null;
            aiData.conv_status = "ended";
            if (!aiData.bot) {
                aiData.bot = (validCabins.length > 1)
                    ? "Thanks, I've noted your cabin numbers."
                    : "Thanks, I've noted your cabin number.";
            }
        } else if (s.cabinAskCount >= 2) {
            // Second turn and still unresolved — this node is exiting regardless
            // of what the LLM said, so force the correct final state.
            s.exitReason = null;
            s.CabinNumberUnknown = true;
            aiData.conv_status = "ended";
            aiData.bot = MSG_FALLBACK;
            koreDebugger.log("POST | Second turn unresolved → forcing finalize");
        } else {
            // First turn, still unresolved (missing OR bad separator) — normal ask, count it
            s.exitReason = null;
            aiData.conv_status = "ongoing";
            s.cabinAskCount = 1;
            koreDebugger.log("POST | First ask delivered → askCount=1");
        }

        koreDebugger.log("POST | CabinNumber: " + context.entities.CabinNumber +
                         " | CabinNumbers: " + JSON.stringify(context.entities.CabinNumbers) +
                         " | done: " + done +
                         " | unknown: " + (s.CabinNumberUnknown === true) +
                         " | askCount: " + s.cabinAskCount +
                         " | exitReason: " + s.exitReason);
    } else {
        koreDebugger.log("POST: No AI data for node: " + node);
    }

} catch (e) {
    koreDebugger.log("POST ERROR: " + e.message);
}
```
