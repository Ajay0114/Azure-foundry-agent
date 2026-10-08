# PC_HomeDelivery_Agent_PurchasedDate  (aiassist)

## Config
```json
{
  "name": "PC_HomeDelivery_Agent_PurchasedDate",
  "type": "aiassist",
  "generativeAI": {
    "dynamicEntityConfig": {
      "dynamicEntities": [
        {
          "name": "PurchasedDate",
          "type": "date"
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
        "nodeId": "nd-scr-3d967c2e-41e4-4423-9603-583c86988b61"
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
You are extracting the purchase date (PurchasedDate) from the user message.

-----------------------------------
CURRENT VALUE
-----------------------------------

PurchasedDate: {{context.session.BotUserSession.resolvedPurchasedDate}}

-----------------------------------
CURRENT VALUE HANDLING (HIGHEST PRIORITY)
-----------------------------------

If CURRENT VALUE is a FULL STRICT DATE (e.g., "02/14/2026") or "unknown":
1. Ignore the current user message completely.
2. Return the existing PurchasedDate value.
3. Set conv_status to "ended".
4. Set bot to "".
5. Return immediately.

-----------------------------------
VALID SOURCES & STRICT RULES
-----------------------------------

1. Extract PurchasedDate ONLY from the CURRENT USER MESSAGE or combine with CURRENT VALUE.
2. NEVER extract from conversation history, cruise dates, or service dates.
3. NEVER assume or fill missing years/days automatically.

-----------------------------------
EXTRACTION & PARTIAL PROMPTING RULES
-----------------------------------

Case 1: Full Date Provided (Month, Day, and 4-digit Year)
- Combine with existing partial value if necessary.
- Normalize strictly to MM/DD/YYYY format.
- Set conv_status = "ended"
- Set bot = ""

Case 2: Partial Date - Missing Year (e.g., "July 10th", "10/07")
- PurchasedDate = Extracted partial date string (e.g. "July 10th")
- Set conv_status = "ongoing"
- Set bot = "Could you please specify which year you made the purchase?"

Case 3: Partial Date - Missing Day (e.g., "feb 2026", "02/2026")
- PurchasedDate = Extracted partial date string (e.g. "feb 2026")
- Set conv_status = "ongoing"
- Set bot = "Could you please share the specific day of the month you made the purchase?"

Case 4: User responds with JUST a day or year (e.g., "14" or "2026") when CURRENT VALUE exists
- Combine CURRENT VALUE with new input.
- If result forms a full date -&gt; normalize to MM/DD/YYYY, set conv_status = "ended", bot = "".

-----------------------------------
UNKNOWN INTENT
-----------------------------------

If CURRENT USER MESSAGE indicates "don't know", "not sure", "cannot remember":
- PurchasedDate = "unknown"
- conv_status = "ended"
- bot = ""

-----------------------------------
NO DATE FOUND
-----------------------------------

If CURRENT VALUE == NOT_YET_PROVIDED AND current message contains no date:
- PurchasedDate = null
- conv_status = "ongoing"
- bot = "Please share the date when you purchased the item."

-----------------------------------
OUTPUT FORMAT
-----------------------------------

Return STRICTLY valid JSON with no markdown block wrappers:

{
  "bot": "...",
  "conv_status": "ongoing|ended",
  "entities": {
      "PurchasedDate": "MM/DD/YYYY | unknown | raw partial text | null"
  }
}
```

## generativeAI.preProcessorScript
```
try {
    context.entities = context.entities || {};
    context.session  = context.session || {};
    context.session.BotUserSession = context.session.BotUserSession || {};

    var s = context.session.BotUserSession;

    function isResolved(v) {
        if (v === undefined || v === null) return false;
        var str = String(v).trim().toUpperCase();
        return str !== "" && str !== "NOT_YET_PROVIDED" && str !== "NULL" && str !== "UNDEFINED";
    }

    // Scrub cruise/service dates to avoid prompt/memory bleed
    var cruiseKeys = [
        "usr_start_date", "usr_end_date", "usr_date_of_the_service",
        "start_date", "end_date", "service_date", "requestedDate",
        "lastUserStartDate", "suggestedStartDate", "suggestedEndDate",
        "partial_start_date", "lastEnteredDate"
    ];

    cruiseKeys.forEach(function(k) {
        if (context.entities) { delete context.entities[k]; }
    });

    // Synchronize session date with context.entities
    var existingDate = (context.entities && context.entities.PurchasedDate) || 
                       s.PurchasedDate || 
                       s.PCAgentPurchasedDate || null;

    if (existingDate && String(existingDate).toLowerCase() !== "unknown") {
        context.entities.PurchasedDate = String(existingDate).trim();
    }

    // Set single source of truth for System Prompt
    s.resolvedPurchasedDate = isResolved(context.entities.PurchasedDate)
        ? String(context.entities.PurchasedDate).trim()
        : "NOT_YET_PROVIDED";

    // Only set AllDetailsCaptured to true if it is a COMPLETE date (MM/DD/YYYY)
    var isStrictComplete = /^\d{2}\/\d{2}\/\d{4}$/.test(s.resolvedPurchasedDate) || s.resolvedPurchasedDate.toLowerCase() === "unknown";
    context.entities.AllDetailsCaptured = isStrictComplete;

    koreDebugger.log("=== PC_HomeDelivery_Agent_PurchasedDate PRE ===");
    koreDebugger.log("PurchasedDate Memory: " + s.resolvedPurchasedDate);
    koreDebugger.log("AllDetailsCaptured: " + context.entities.AllDetailsCaptured);

} catch(e) {
    koreDebugger.log("PRE ERROR: " + e.message);
}
```

## generativeAI.postProcessorScript
```
try {
    var node   = context.currentNodeName;
    var aiData = context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs[node];

    if (!aiData) {
        koreDebugger.log("POST: No AI data found for node: " + node);
        return;
    }

    var rawEnt = aiData.entities || {};
    var ent = {};

    if (Array.isArray(rawEnt)) {
        rawEnt.forEach(function(e) {
            if (typeof e === 'object' && e !== null) {
                Object.assign(ent, e);
            }
        });
    } else if (typeof rawEnt === 'object' && rawEnt !== null) {
        ent = Object.assign({}, rawEnt);
    }


    context.entities = context.entities || {};
    context.session  = context.session || {};
    var s = context.session.BotUserSession = context.session.BotUserSession || {};

    var newExtracted = (ent.PurchasedDate && String(ent.PurchasedDate).trim() !== "") 
                        ? String(ent.PurchasedDate).trim() 
                        : null;

    var existingDate = s.PurchasedDate || context.entities.PurchasedDate || null;
    var combinedDateStr = "";

// 0. MULTI-DATE SAFETY NET — don't trust the LLM to always resist guessing
function hasMultipleDateMentions(text) {
    if (!text) return false;
    var monthRegex = /(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*\d{1,2}(st|nd|rd|th)?(\s*,?\s*\d{4})?/gi;
    var numericRegex = /\b\d{1,2}[\/\-]\d{1,2}([\/\-]\d{2,4})?\b/g;
    var monthMatches = text.match(monthRegex) || [];
    var numericMatches = text.match(numericRegex) || [];
    return (monthMatches.length + numericMatches.length) >= 2;
}

var rawUserMsg = s.lastRawUserMessage || "";
if (hasMultipleDateMentions(rawUserMsg)) {
    koreDebugger.log("POST | BLOCKED: multiple date mentions detected in \"" + rawUserMsg + "\" — refusing to guess.");

    // Do not overwrite any existing resolved date with a guess
    aiData.entities = aiData.entities || {};
    aiData.bot = "I noticed a couple of different dates in your message — could you confirm the single, exact date you purchased the item?";
    aiData.conv_status = "ongoing";
    context.AllDetailsCaptured = false;
    s.AllDetailsCaptured = false;

    return; // stop here — skip the rest of the merge/normalize logic below
}


    // 1. MERGE PARTIAL DATES ACROSS TURNS

    function isCompleteDate(str) {
        if (!str) return false;
        var cleaned = String(str).replace(/(\d+)(st|nd|rd|th)/gi, "$1").trim();
        var hasYear = /\b(19|20)\d{2}\b/.test(cleaned);
        if (!hasYear) return false;

        // must have day/month info left over besides just the bare year
        var withoutYear = cleaned.replace(/\b(19|20)\d{2}\b/, '').trim();
        var hasDayOrMonth = /[a-zA-Z]{3,}/.test(withoutYear) || /\d{1,2}/.test(withoutYear);
        if (!hasDayOrMonth) return false;

        return !isNaN(Date.parse(cleaned));
    }

    if (isCompleteDate(newExtracted)) {
        // this turn's value is already a full, parseable date (LLM already combined it) — trust it, don't re-merge with the stale fragment
        combinedDateStr = newExtracted;
    }
    else if (existingDate && newExtracted && existingDate.toLowerCase() !== "unknown" && existingDate !== newExtracted) {
        if (!/\b(0?[1-9]|[12][0-9]|3[01])\b/.test(existingDate.replace(/\b(19|20)\d{2}\b/, '')) && /^\d{1,2}(st|nd|rd|th)?$/i.test(newExtracted)) {
            combinedDateStr = newExtracted + " " + existingDate;
        } 
        else if (!/\b(19|20)\d{2}\b/.test(existingDate) && /\b(19|20)\d{2}\b/.test(newExtracted)) {
            combinedDateStr = existingDate + " " + newExtracted;
        } 
        else {
            combinedDateStr = newExtracted;
        }
    } else {
        combinedDateStr = newExtracted || existingDate;
    }


    // 2. CRUISE DATE BLEED PROTECTION
   
    var blockedDates = [
        s.usr_start_date, s.usr_end_date, s.usr_date_of_the_service,
        s.start_date, s.end_date, s.service_date, s.requestedDate,
        s.lastUserStartDate, s.suggestedStartDate, s.suggestedEndDate,
        s.partial_start_date, s.lastEnteredDate
    ].filter(Boolean).map(function(d) { return String(d).trim(); });

    if (combinedDateStr && blockedDates.some(function(d) { return d === combinedDateStr; })) {
        koreDebugger.log("POST | BLOCKED cruise date bleed: " + combinedDateStr);
        combinedDateStr = null;
    }

   
    // 3. NORMALIZE TO MM/DD/YYYY IF ALL PARTS ARE PRESENT
    
    var finalDate = combinedDateStr;

    if (combinedDateStr && combinedDateStr.toLowerCase() !== "unknown") {
        var parsedTimestamp = Date.parse(combinedDateStr);
        var hasYear = /\b(19|20)\d{2}\b/.test(combinedDateStr);
        
     
        if (!isNaN(parsedTimestamp) && hasYear) {
            var d = new Date(parsedTimestamp);
            var mm = String(d.getMonth() + 1).padStart(2, '0');
            var dd = String(d.getDate()).padStart(2, '0');
            var yyyy = d.getFullYear();
            finalDate = mm + "/" + dd + "/" + yyyy;
        }
    }

    
    // 4. PERSIST VARIABLES & CONTROL CONVERSATION STATE

    if (finalDate) {
        context.entities.PurchasedDate = finalDate;
        s.PurchasedDate                = finalDate;
        s.PCAgentPurchasedDate         = finalDate;
    } else {
        delete context.entities.PurchasedDate;
        s.PurchasedDate = null;
        s.PCAgentPurchasedDate = null;
    }

    var isStrictComplete = finalDate && (/^\d{2}\/\d{2}\/\d{4}$/.test(finalDate) || finalDate.toLowerCase() === "unknown");

    if (isStrictComplete) {
        aiData.conv_status         = "ended";
        context.AllDetailsCaptured = true;
        s.AllDetailsCaptured       = true;
        koreDebugger.log("POST | Full Date resolved: " + finalDate);
    } else {
        aiData.conv_status         = "ongoing";
        context.AllDetailsCaptured = false;
        s.AllDetailsCaptured       = false;
        koreDebugger.log("POST | Partial Date preserved: " + finalDate + " — waiting for remaining details.");
    }

} catch (e) {
    koreDebugger.log("POST ERROR: " + e.message);
}
```
