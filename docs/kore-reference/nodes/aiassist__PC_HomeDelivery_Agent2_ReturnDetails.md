# PC_HomeDelivery_Agent2_ReturnDetails  (aiassist)

## Config
```json
{
  "name": "PC_HomeDelivery_Agent2_ReturnDetails",
  "type": "aiassist",
  "generativeAI": {
    "dynamicEntityConfig": {
      "dynamicEntities": [
        {
          "name": "Country",
          "type": "country"
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
      "fallbackBehavior": {
        "id": "dynamicEntity",
        "onLLMFail": "skipEvent",
        "nodeId": "nd-scr-9412ca75-d609-4183-8352-5b2e16309e3d"
      }
    }
  }
}
```

## generativeAI.dynamicEntityConfig.systemContext
```
You are extracting Country.
-----------------------------------
CURRENT VALUE
-----------------------------------
Country: {{context.session.BotUserSession.resolvedCountry}}

Note: the value above may be "NOT_YET_PROVIDED" (never asked), "UNKNOWN" (the
user already said they don't know / can't find it on a PRIOR turn), or an
actual captured value.
-----------------------------------
RULES
-----------------------------------
- ALWAYS preserve an existing value. If Country above is not "NOT_YET_PROVIDED", return it unchanged — this includes "UNKNOWN": pass it through as "UNKNOWN" unless the user now gives a real answer.
- NEVER remove or overwrite an already captured value.
- NEVER return empty string "" → use null.
- NEVER ask the user to confirm a value already captured.
- NEVER summarize what was collected.
-----------------------------------
EXTRACTION LOGIC
-----------------------------------
COUNTRY MAPPING (normalize common variants; accept any country):
  US / USA / United States / America → "United States"
  UK / Britain / England → "United Kingdom"
  UAE / Dubai → "United Arab Emirates"
  India / Bharat → "India"
  Germany / Deutschland → "Germany"
  Any other country → use its standard English name.
-----------------------------------
BEHAVIOR
-----------------------------------
1. If user gives Country → set Country in entities.
2. If the user indicates in ANY way that they don't know or can't find it — e.g. "I don't know", "not sure", "can't find it" — set Country to "UNKNOWN".
3. If user input is only: yes / yeah / ok / sure / correct / thanks → do NOT change the value. Return the existing value as-is.
-----------------------------------
QUESTION LOGIC
-----------------------------------
1. Country is "NOT_YET_PROVIDED" → "Could you please share the country you are located in?"
2. Country is "UNKNOWN" → briefly explain it's needed to process the return, then ask again, e.g.: "I understand — I do need your country to process the return, though. Could you share it?"
Once Country has an actual captured value (not UNKNOWN), NEVER ask for it again.
-----------------------------------
OUTPUT FORMAT (STRICT — THIS IS THE ONLY VALID SCHEMA)
-----------------------------------
Return ONLY a single valid JSON object, nothing else — no markdown, no code fences, no text before or after it, no characters after the final closing brace:
{"bot": "your message here", "conv_status": "ongoing or ended", "entities": {"Country": "value, UNKNOWN, or null"}}

Before responding, mentally verify the braces balance exactly: one opening `{` for the outer object, one for "entities", and exactly two matching closing `}` at the very end — nothing after them.

The "bot" field must NEVER be empty:
- If Country is missing or UNKNOWN → bot is the question for it.
- If Country is captured (or UNKNOWN with nothing left to ask) → bot is exactly: "Thank you."

conv_status rules:
- Set conv_status to "ended" ONLY when Country is either captured or "UNKNOWN".
- Otherwise set conv_status to "ongoing".

ALWAYS return the ACTUAL captured value in entities — never a placeholder, never the string "null".
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

    if (!isResolved(context.entities.Country) && isResolved(s.Country)) {
        context.entities.Country = s.Country;
    }

    s.resolvedCountry = isResolved(context.entities.Country)
        ? String(context.entities.Country)
        : (s.CountryUnknown === true ? "UNKNOWN" : "NOT_YET_PROVIDED");

    koreDebugger.log("=== PC_HomeDelivery_Agent_Country PRE ===");
    koreDebugger.log("PRE | Country=" + s.resolvedCountry);

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

        function isUnknownSentinel(v) {
            return String(v || "").trim().toUpperCase() === "UNKNOWN";
        }

        // ---------- EXIT DETECTION (every turn) ----------
        var lastUserMsg = "";
        try {
            lastUserMsg = String(
                (s.lastMessage && s.lastMessage.messagePayload &&
                 s.lastMessage.messagePayload.message &&
                 s.lastMessage.messagePayload.message.body) || ""
            ).toLowerCase().trim();
        } catch (e2) {}

        var pureExitPhrases = [
            "i do not want to continue this anymore",
            "i don't want to continue this anymore",
            "i dont want to continue this anymore",
            "i don't want to continue", "i dont want to continue",
            "i don't need this anymore", "i dont need this anymore",
            "stop the process",
            "end the conversation", "end this conversation",
            "end this request", "end this",
            "cancel this request", "cancel this", "stop this",
            "i want to cancel", "i want to exit",
            "i want to discard", "i want to stop"
        ];

        var pureExitWords = ["discard", "cancel", "exit", "quit", "terminate"];

        var exclusionPhrases = [
            "cancel that", "cancel that thought", "cancel the", "cancel my",
            "cancel your", "cancel their", "cancel it", "cancel a ", "cancel my subscription",
            "cancelled", "cancellation", "canceling", "cancelling",
            "stop me if", "stop the", "stop my", "stop charging",
            "end of", "end the", "end my", "by the end", "toward the end",
            "at the end", "close to", "quite",
            "exiting", "exit the", "exit a ", "discarded", "discarding"
        ];

        function matchesWordBoundary(word, str) {
            var escaped = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            var pattern = new RegExp('(^|[^a-zA-Z])' + escaped + '([^a-zA-Z]|$)', 'i');
            return pattern.test(str);
        }

        var isExcluded = exclusionPhrases.some(function(p) {
            return lastUserMsg.indexOf(p) !== -1;
        });
        var isPureExit = pureExitPhrases.some(function(p) {
            return lastUserMsg.indexOf(p) !== -1;
        });
        if (!isPureExit && !isExcluded) {
            isPureExit = pureExitWords.some(function(w) {
                return matchesWordBoundary(w, lastUserMsg);
            });
        }

        koreDebugger.log("POST | AI Returned: " + JSON.stringify(ent) +
                         " | LLM conv_status: " + aiData.conv_status +
                         " | isPureExit: " + isPureExit);

        // ---------- ENTITY CAPTURE ----------
        if (!isResolved(context.entities.Country) && isResolved(ent.Country)) {
            var country = String(ent.Country).trim();
            if (country.length >= 2 && /^[a-zA-Z\s\-'.]+$/.test(country)) {
                context.entities.Country = country;
                s.Country = country;
                s.resolvedCountry = country;
                s.CountryUnknown = false;
            } else {
                koreDebugger.log("POST | Rejected invalid country: " + country);
            }
        }

        if (!isResolved(context.entities.Country) && isUnknownSentinel(ent.Country)) {
            s.CountryUnknown = true;
        }

        var countryDone = isResolved(context.entities.Country) || s.CountryUnknown === true;
        var done = countryDone;

        // ---------- RETRY CAP ----------
        s.countryRetryCount = s.countryRetryCount || 0;

        // ---------- DECIDE ----------
        if (done) {
            s.exitReason = null;
            s.countryRetryCount = 0;
            s.countryCompleted = true;
            aiData.conv_status = "ended";
            aiData.bot = "Got it, thanks.";
        } else if (isPureExit) {
            s.exitReason = "exit_requested";
            aiData.conv_status = "ended";
            aiData.bot = "Okay, cancelling this request.";
            koreDebugger.log("POST | EXIT requested → ending node");
        } else {
            s.exitReason = null;
            s.countryRetryCount++;

            if (s.countryRetryCount >= 5) {
                aiData.conv_status = "ended";
                aiData.bot = "I'm having trouble capturing this detail. " +
                             "Let me connect you with our team to finish this request.";
                s.countryCompleted = false;
                koreDebugger.log("POST | RETRY CAP reached → ending incomplete");
            } else {
                aiData.conv_status = "ongoing";
                if ((aiData.conv_status === "ongoing") &&
                    (String(aiData.bot || "").trim() === "")) {
                    aiData.bot = "Could you please share the country you are located in?";
                }
                if (s.countryRetryCount === 3) {
                    aiData.bot = String(aiData.bot || "") +
                        " (You can also type cancel if you'd like to stop.)";
                }
                koreDebugger.log("POST | Not done → ongoing. Retry " +
                                 s.countryRetryCount);
            }
        }

        koreDebugger.log("POST | Country: " + context.entities.Country +
                         " | CountryUnknown: " + (s.CountryUnknown === true) +
                         " | done: " + done + " | exitReason: " + s.exitReason +
                         " | retries: " + s.countryRetryCount +
                         " | countryCompleted: " + s.countryCompleted);
    } else {
        koreDebugger.log("POST: No AI data for node: " + node);
    }

} catch (e) {
    koreDebugger.log("POST ERROR: " + e.message);
}
```
