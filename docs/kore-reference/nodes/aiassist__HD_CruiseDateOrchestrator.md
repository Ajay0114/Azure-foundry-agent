# HD_CruiseDateOrchestrator  (aiassist)

## Config
```json
{
  "name": "HD_CruiseDateOrchestrator",
  "type": "aiassist",
  "generativeAI": {
    "dynamicEntityConfig": {
      "enabled": true,
      "model": "gpt-5.1",
      "icon": "https://platform.kore.ai/assets/integrations/32/customllm.png",
      "displayName": "Azure-OpenAI-GPT5.1-gpt-5.1",
      "integrationName": "Azure-OpenAI-GPT5.1",
      "temperature": 0,
      "max_tokens": 0,
      "Noofprevioususerinputs": 10,
      "promptId": "45d0d751-539f-5c0b-b631-2547384222a8",
      "promptName": "Vessel_Itiernary_Validation_Prompt",
      "isCustom": true,
      "isSysIntAndCustomPrompt": false,
      "isStreaming": false,
      "fallbackBehavior": {
        "id": "dynamicEntity",
        "onLLMFail": "skipEvent",
        "nodeId": "nd-scr-630ec151-5eb3-4533-85e4-4a349e73a970"
      }
    }
  }
}
```

## generativeAI.preProcessorScript
```
try {
    context.session = context.session || {};
    context.session.BotUserSession = context.session.BotUserSession || {};
    context.entities = context.entities || {};
    context.amendEntities = context.amendEntities || {};
    const sd = context.session.BotUserSession;
    const SENTINEL_VALUES = new Set([
        "unknown", "not sure", "i don't know", "i dont know", "dont know",
        "don't know", "no idea", "n/a", "na", "none", "not applicable",
        "not remember", "don't remember", "i don't remember", "i dont remember",
        "do not remember", "i do not remember", "no clue", "unsure", "skip", "idk"
    ]);
    if (!Array.isArray(sd.dateSkippedFields)) sd.dateSkippedFields = [];
    function isFullDate(val) { return !!val && /^\d{4}-\d{2}-\d{2}$/.test(String(val).trim()); }
    function isPartialDate(val) {
        if (!val) return false;
        const s = String(val).trim();
        if (isFullDate(s)) return false;
        return /(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\b\d{1,2}\b)/i.test(s);
    }
    function isValidVesselId(id) { return !!id && /^\d+$/.test(String(id).trim()); }
    function parseAnyDate(str) {
        if (!str) return null;
        str = String(str).trim().replace(/(\d{1,2})(st|nd|rd|th)\b/gi, "$1");
        if (/^\d{4}-\d{2}-\d{2}$/.test(str)) return str;
        // const slash = str.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
 const slash = str.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
        if (slash) return slash[3] + "-" + slash[1].padStart(2, "0") + "-" + slash[2].padStart(2, "0");
        const months = { jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12" };
        const m = str.match(/(\w+)\s+(\d{1,2}),?\s+(\d{4})/i) || str.match(/(\d{1,2})\s+(\w+)\s+(\d{4})/i);
        if (m) {
            let d, mo, y;
            if (/^\d/.test(m[1])) { d = m[1]; mo = m[2].substring(0,3).toLowerCase(); y = m[3]; }
            else                  { mo = m[1].substring(0,3).toLowerCase(); d = m[2]; y = m[3]; }
            if (months[mo]) return y + "-" + months[mo] + "-" + d.padStart(2, "0");
        }
        return null;
    }
    // NEW — deterministic RANGE parser ("June 3-7, 2026" / "Jan 2-6" / "13-20 July 2026").
    // Only the FIRST (earlier) date is ever extracted — the second date in the
    // range is intentionally discarded. end_date is never derived from a range;
    // it always comes from the itinerary tool call (or a later question), same
    // as it always has. This is added purely as a fallback that runs when
    // parseAnyDate (a SINGLE date) fails to match — it never changes behaviour
    // for a normal single-date answer.
    function parseDateRangeStart(str) {
        if (!str) return null;
        const s = String(str).trim().replace(/(\d{1,2})(st|nd|rd|th)\b/gi, "$1");
        const MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec";
        const monthNum = { jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12" };
        let m = s.match(new RegExp("^(" + MONTHS + ")[a-z]*\\.?\\s+(\\d{1,2})\\s*(?:-|to|–|—)\\s*(\\d{1,2})\\s*,?\\s*(\\d{4})?$", "i"));
        if (m) {
            const mo = monthNum[m[1].substring(0, 3).toLowerCase()];
            if (m[4]) return { start: m[4] + "-" + mo + "-" + m[2].padStart(2, "0") };
            return { startPartial: m[1] + " " + m[2] };
        }
        m = s.match(new RegExp("^(\\d{1,2})\\s*(?:-|to|–|—)\\s*(\\d{1,2})\\s+(" + MONTHS + ")[a-z]*\\.?\\s*,?\\s*(\\d{4})?$", "i"));
        if (m) {
            const mo = monthNum[m[3].substring(0, 3).toLowerCase()];
            if (m[4]) return { start: m[4] + "-" + mo + "-" + m[1].padStart(2, "0") };
            return { startPartial: m[1] + " " + m[3] };
        }
        return null;
    }
    // NEW — deterministic date-ANYWHERE scanner. parseAnyDate/parseDateRangeStart above
    // only work on a value already sitting in an entity, and require the WHOLE string to
    // be just the date. This instead searches the raw message text for a numeric date
    // embedded anywhere in a longer sentence — e.g. "Star Princess 7/19/26-7/26/26", where
    // Kore.ai's NLU never extracts any date entity at all from a compound ship+date message,
    // leaving the LLM to parse it out of a conversation history that (for this exact
    // scenario) already contains the same message once before, confusing extraction.
    // Regex naturally takes only the FIRST date in a "D1-D2" style range (the year group
    // can't cross the "-" into the second date), matching the "start only" rule used
    // throughout this file. 2-digit years are normalised (26 -> 2026, 95 -> 1995).
    function normalizeYear(y) {
        if (y.length === 4) return y;
        const n = parseInt(y, 10);
        return String(n <= 68 ? 2000 + n : 1900 + n);
    }
    // Searches for a date ANYWHERE in a longer sentence using five shapes (numeric
    // slash/dash, "Month D, Year", "D Month Year", "Month D1-D2, Year" range,
    // "D1-D2 Month Year" range), then picks whichever match starts EARLIEST in the raw
    // text — so "star princess from jan 10 2026 to jan 16 2026" correctly picks the
    // 10th, and "Star Princess June 3-7, 2026" correctly picks the 3rd, matching the
    // "take only the earlier date" rule used throughout this file. Each regex is
    // non-global, so within a single shape it already only ever finds the first
    // (leftmost) occurrence; the two range shapes only ever extract D1, never D2.
    function findStartDateAnywhere(text) {
        if (!text) return null;
        const s = String(text);
        const MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec";
        const monthNum = { jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12" };
        const candidates = [];
        let m = s.match(/\b(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})\b/);
        if (m) candidates.push({ index: m.index, date: normalizeYear(m[3]) + "-" + m[1].padStart(2, "0") + "-" + m[2].padStart(2, "0") });
        m = s.match(new RegExp("\\b(" + MONTHS + ")[a-z]*\\.?\\s+(\\d{1,2})\\s*(?:-|to|–|—)\\s*(\\d{1,2})\\s*,?\\s*(\\d{4})\\b", "i"));
        if (m) candidates.push({ index: m.index, date: m[4] + "-" + monthNum[m[1].substring(0, 3).toLowerCase()] + "-" + m[2].padStart(2, "0") });
        m = s.match(new RegExp("\\b(\\d{1,2})\\s*(?:-|to|–|—)\\s*(\\d{1,2})\\s+(" + MONTHS + ")[a-z]*\\.?\\s*,?\\s*(\\d{4})\\b", "i"));
        if (m) candidates.push({ index: m.index, date: m[4] + "-" + monthNum[m[3].substring(0, 3).toLowerCase()] + "-" + m[1].padStart(2, "0") });
        m = s.match(new RegExp("\\b(" + MONTHS + ")[a-z]*\\.?\\s+(\\d{1,2})(?:st|nd|rd|th)?,?\\s+(\\d{4})\\b", "i"));
        if (m) candidates.push({ index: m.index, date: m[3] + "-" + monthNum[m[1].substring(0, 3).toLowerCase()] + "-" + m[2].padStart(2, "0") });
        m = s.match(new RegExp("\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+(" + MONTHS + ")[a-z]*\\.?\\s*,?\\s+(\\d{4})\\b", "i"));
        if (m) candidates.push({ index: m.index, date: m[3] + "-" + monthNum[m[2].substring(0, 3).toLowerCase()] + "-" + m[1].padStart(2, "0") });
        if (!candidates.length) return null;
        candidates.sort((a, b) => a.index - b.index);
        return candidates[0].date;
    }
    // FIX D — confirmed live (full context JSON dump) that context.session.BotUserSession.lastMessage
    // (i.e. sd.lastMessage) is the DURABLE, persistent session-store copy of the last real inbound
    // message: it still held the correct text ("Star Princess 7/19/26-7/26/26") well after an internal
    // transition, at a point where context.session.lastMessage (missing the .BotUserSession segment —
    // a separate, transient per-request alias) was empty. That's the bug: this file was reading the
    // transient alias, not the durable session-store field, so it never saw the real text on a
    // transition-based turn. context.NLAnalysis.userInput is confirmed UNRELIABLE (not just empty) —
    // it held a STALE value ("yes", from an unrelated earlier reply) rather than this turn's real
    // input, so it is kept only as an absolute last resort, after every other candidate.
    const rawInputCandidates = [
        ["session.BotUserSession.lastMessage", sd.lastMessage?.messagePayload?.message?.body],
        ["session.lastMessage (alias)",        context.session?.lastMessage?.messagePayload?.message?.body],
        ["User_Input",                         (typeof User_Input !== "undefined") ? User_Input : undefined],
        ["userInputs.originalInput",           context.userInputs?.originalInput?.sentence],
        ["NLAnalysis.userInput (unreliable)",  context.NLAnalysis?.userInput],
    ];
    const rawInputPicked = rawInputCandidates.find(([, v]) => !!v);
    const rawInputSource = rawInputPicked ? rawInputPicked[0] : "none";
    const rawUserInput = (rawInputPicked ? rawInputPicked[1] : "").toLowerCase().trim();
    koreDebugger.log("PRE | rawUserInput seen this turn: " + JSON.stringify(rawUserInput) + " (source: " + rawInputSource + ")");
    // DIAGNOSTIC — only useful if rawUserInput is STILL empty above; harmless otherwise.
    // Dumps every other place the real text might be hiding, so the next test settles
    // this in one shot instead of another guess-and-test round.
    if (!rawUserInput) {
        koreDebugger.log("PRE | DIAGNOSTIC ctx keys: " + JSON.stringify(Object.keys(context)));
        koreDebugger.log("PRE | DIAGNOSTIC session keys: " + JSON.stringify(context.session ? Object.keys(context.session) : null));
        koreDebugger.log("PRE | DIAGNOSTIC NLAnalysis: " + JSON.stringify(context.NLAnalysis));
        koreDebugger.log("PRE | DIAGNOSTIC invocationSource: " + JSON.stringify(context.invocationSource));
        koreDebugger.log("PRE | DIAGNOSTIC userInputs: " + JSON.stringify(context.userInputs));
        koreDebugger.log("PRE | DIAGNOSTIC history: " + JSON.stringify(context.history));
        koreDebugger.log("PRE | DIAGNOSTIC session.lastMessage: " + JSON.stringify(context.session?.lastMessage));
        koreDebugger.log("PRE | DIAGNOSTIC session.BotUserSession.lastMessage: " + JSON.stringify(sd.lastMessage));
        koreDebugger.log("PRE | DIAGNOSTIC AI_Assisted_Dialogs: " + JSON.stringify(context.AI_Assisted_Dialogs));
    }
    const rawStripped  = rawUserInput.replace(/[.!?,]+$/, "").trim();
    const isExactNo    = !sd.waitingForConfirm && (rawStripped === "no" || rawStripped === "nope" || rawStripped === "nah");
    const userSaidDontKnow = [...SENTINEL_VALUES].some(sv => rawUserInput.includes(sv)) || isExactNo;
    // ── FIX C — one message may drive only ONE skip. Stops the same "Not sure"
    //            from skipping start_date AND then cascading onto end_date. ──
    const msgId = String(context.session?.lastMessage?.messagePayload?.id ||
                         context.session?.lastMessage?.messagePayload?.clientMessageId || "");
    const alreadyConsumed = msgId && sd.lastSkipConsumedMsgId === msgId;
    // ── FIX A + B — register a skip ONLY for the field we are actively asking,
    //               and ONLY if that field was already asked at least once. ──
    const fieldAskCount = sd.currentlyAskingField ? (sd[sd.currentlyAskingField + "_askCount"] || 0) : 0;
    const alreadyAsked  = fieldAskCount >= 1;
    if (userSaidDontKnow && sd.currentlyAskingField && alreadyAsked && !alreadyConsumed) {
        sd.lastSkipConsumedMsgId = msgId;
        if (!sd.dateSkippedFields.includes(sd.currentlyAskingField)) {
            sd.dateSkippedFields = sd.dateSkippedFields.concat([sd.currentlyAskingField]);
            context.session.BotUserSession.dateSkippedFields = sd.dateSkippedFields;
        }
        koreDebugger.log("PRE | skip registered for: " + sd.currentlyAskingField);
        if (sd.currentlyAskingField === "start_date") {
            sd.toolCallDone = true; sd.itineraryValidated = true; sd.waitingForConfirm = false;
        }
    } else if (userSaidDontKnow && sd.currentlyAskingField && !alreadyAsked) {
        koreDebugger.log("PRE | 'don't know' ignored — " + sd.currentlyAskingField + " not yet asked (entry-guard)");
    }
    // ── NEW — recover start_date directly from the raw message when NLU never put
    //          anything into entities at all (e.g. a compound "ship name + date" message).
    //          Only runs while start_date is genuinely unresolved, not skipped, and we're
    //          not mid-confirmation on a suggested sailing (that flow handles new dates on
    //          its own terms via confirmed:"no" + user_stated_date). ──
    if (!isFullDate(context.entities.start_date) && !isFullDate(sd.start_date) &&
        !sd.dateSkippedFields.includes("start_date") && sd.waitingForConfirm !== true) {
        const foundStart = findStartDateAnywhere(rawUserInput);
        if (foundStart && isFullDate(foundStart)) {
            context.entities.start_date = foundStart; context.amendEntities.start_date = foundStart; sd.start_date = foundStart;
            koreDebugger.log("PRE | date found anywhere in raw message: start_date=" + foundStart);
        }
    }
    // ── Normalise / clean text dates already sitting in entities ─────────────
    ["start_date", "end_date"].forEach(field => {
        const val = context.entities[field];
        if (!val) return;
        if (!isFullDate(val)) {
            // NEW — check for a RANGE (e.g. "June 3-7, 2026", "13-20 July 2026") BEFORE
            // trying parseAnyDate: parseAnyDate's regexes aren't anchored, so on a
            // day-first range they can match the trailing "D2 Month Year" substring and
            // silently return the LATER date. Checking the range first avoids that and
            // takes ONLY the first (earlier) date as start_date — the second date is
            // dropped entirely; end_date still only ever comes from the itinerary tool
            // call or a separate later question, unchanged.
            const range = parseDateRangeStart(String(val));
            const norm = (range && range.start) ? range.start : parseAnyDate(String(val));
            if (norm && isFullDate(norm)) {
                if (range) {
                    if (!isFullDate(context.entities.start_date) && !isFullDate(sd.start_date)) {
                        context.entities.start_date = norm; context.amendEntities.start_date = norm; sd.start_date = norm;
                        koreDebugger.log("PRE | date range resolved (start only): start=" + norm);
                    }
                    if (field !== "start_date") { delete context.entities[field]; delete context.amendEntities[field]; }
                } else {
                    context.entities[field] = norm; context.amendEntities[field] = norm; sd[field] = norm;
                    koreDebugger.log("PRE | normalised " + field + " = " + norm);
                }
                return;
            }
            if (range && range.startPartial) {
                if (!sd.partial_start_date) sd.partial_start_date = range.startPartial;
                koreDebugger.log("PRE | date range partial (start only): start=" + range.startPartial);
                delete context.entities[field]; delete context.amendEntities[field];
                return;
            }
            delete context.entities[field]; delete context.amendEntities[field];
            if (isPartialDate(val)) {
                const hintKey = "partial_" + field;
                if (!sd[hintKey]) { sd[hintKey] = val; koreDebugger.log("PRE | partial hint: " + hintKey + " = " + val); }
            }
        }
    });
    // ── Sync resolved dates session -> context ───────────────────────────────
    function syncDate(entityKey) {
        if (isFullDate(context.entities[entityKey])) return;
        for (let i = 1; i < arguments.length; i++) {
            const k = arguments[i];
            if (isFullDate(sd[k])) { context.entities[entityKey] = sd[k]; context.amendEntities[entityKey] = sd[k]; return; }
        }
    }
    syncDate("start_date", "start_date", "usr_start_date");
    syncDate("end_date",   "end_date",   "usr_end_date");
    // ── partial + year combination (e.g. "Jan 10" then "2026") ───────────────
    const yearOnly = rawUserInput.match(/\b(20\d{2}|19\d{2})\b/);
    if (yearOnly) {
        [["start_date", "partial_start_date", ["usr_start_date"]],
         ["end_date",   "partial_end_date",   ["usr_end_date"]]].forEach(([field, hintKey, aliases]) => {
            if (sd[hintKey] && !isFullDate(context.entities[field]) && !isFullDate(sd[field])) {
                const parsed = parseAnyDate(sd[hintKey] + " " + yearOnly[1]);
                if (parsed && isFullDate(parsed)) {
                    context.entities[field] = parsed; context.amendEntities[field] = parsed; sd[field] = parsed;
                    aliases.forEach(a => sd[a] = parsed); sd[hintKey] = null;
                    koreDebugger.log("PRE | year-combination: " + field + " = " + parsed);
                }
            }
        });
    }
    ["start_date", "end_date"].forEach(field => {
        const hintKey = "partial_" + field;
        if (sd[hintKey] && (isFullDate(context.entities[field]) || isFullDate(sd[field]))) sd[hintKey] = null;
    });

    // -- reject start_date that is in the future (added) --
    (function () {
        var t = new Date();
        var todayStr = t.getFullYear() + "-" +
            String(t.getMonth() + 1).padStart(2, "0") + "-" +
            String(t.getDate()).padStart(2, "0");
        var sv = context.entities.start_date;
        if (isFullDate(sv) && sv > todayStr) {
            koreDebugger.log("PRE | start_date rejected (future): " + sv);
            delete context.entities.start_date;
            delete context.amendEntities.start_date;
            sd.start_date = null;
            sd.usr_start_date = null;
            sd.lastRejectedDate = null;
            sd.partial_start_date = null;
            sd.lastRejectedDate = null;
            sd.sameStartDateRepeated = false;
            sd.suggestedStartDate = null;
            sd.suggestedEndDate = null;
            sd.toolCallDone = false;
            sd.itineraryValidated = false;
            sd.waitingForConfirm = false;
            sd.startDateRejected = true;
        }
    })();
    // -- reject end_date that is before the start date (added) --
    (function () {
        var ev = context.entities.end_date;
        if (!isFullDate(ev)) return;
        var startFull = isFullDate(context.entities.start_date) ? context.entities.start_date
                      : (isFullDate(sd.start_date) ? sd.start_date
                      : (isFullDate(sd.usr_start_date) ? sd.usr_start_date : null));
     if (startFull && ev < startFull) {
            koreDebugger.log("PRE | end_date rejected (before_start): " + ev);
            delete context.entities.end_date;
            delete context.amendEntities.end_date;
            sd.end_date = null;
            sd.usr_end_date = null;
            sd.partial_end_date = null;
            sd.dateCompleted = false;
            sd.endDateRejected = true;
            sd.endDateInvalidReason = "before_start";
            sd.endRejectStart = startFull || "";
        }
    })();
    // ── vessel_id ─────────────────────────────────────────────────────────────
    const rawVesselId = sd.vessel_id || sd.usr_vessel_id || context.session.vessel_id;
    if (isValidVesselId(rawVesselId)) {
        const vid = String(rawVesselId).trim();
        context.entities.vessel_id = vid; context.amendEntities.vessel_id = vid; sd.vessel_id = vid;
    } else {
        delete context.entities.vessel_id; delete context.amendEntities.vessel_id;
    }
    sd.toolCallDone       = sd.toolCallDone       || false;
    sd.waitingForConfirm  = sd.waitingForConfirm  || false;
    sd.itineraryValidated = sd.itineraryValidated || false;
    sd.dateCompleted      = sd.dateCompleted      || false;
    koreDebugger.log("=== DATE PRE === entities:" + JSON.stringify(context.entities) +
        " | currentlyAskingField:" + sd.currentlyAskingField +
        " | alreadyAsked:" + alreadyAsked +
        " | userSaidDontKnow:" + userSaidDontKnow +
        " | dateSkippedFields:" + JSON.stringify(sd.dateSkippedFields));
} catch (e) {
    koreDebugger.log("Date PreProcessor Error: " + e);
}
```

## generativeAI.postProcessorScript
```
try {
    context.session = context.session || {};
    context.session.BotUserSession = context.session.BotUserSession || {};
    context.entities = context.entities || {};
    context.amendEntities = context.amendEntities || {};
    const sd = context.session.BotUserSession;
    koreDebugger.log("=== DATE POST ===");
    function isFullDate(val) { return !!val && /^\d{4}-\d{2}-\d{2}$/.test(String(val).trim()); }
    function parseAnyDate(str) {
        if (!str) return null;
        str = String(str).trim().replace(/(\d{1,2})(st|nd|rd|th)\b/gi, "$1");
        if (/^\d{4}-\d{2}-\d{2}$/.test(str)) return str;
        const slash = str.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
        if (slash) return slash[3] + "-" + slash[1].padStart(2, "0") + "-" + slash[2].padStart(2, "0");
        const months = { jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12" };
        const m = str.match(/(\w+)\s+(\d{1,2}),?\s+(\d{4})/i) || str.match(/(\d{1,2})\s+(\w+)\s+(\d{4})/i);
        if (m) {
            let d, mo, y;
            if (/^\d/.test(m[1])) { d = m[1]; mo = m[2].substring(0,3).toLowerCase(); y = m[3]; }
            else                  { mo = m[1].substring(0,3).toLowerCase(); d = m[2]; y = m[3]; }
            if (months[mo]) return y + "-" + months[mo] + "-" + d.padStart(2, "0");
        }
        return null;
    }
    // NEW — same deterministic RANGE parser as PRE, used below as a safety net
    // when the LLM echoes a whole range back as start_date, or when we recover a
    // date directly from the user's raw text. Only the first (earlier) date is
    // ever extracted; end_date is never derived from a range.
    function parseDateRangeStart(str) {
        if (!str) return null;
        const s = String(str).trim().replace(/(\d{1,2})(st|nd|rd|th)\b/gi, "$1");
        const MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec";
        const monthNum = { jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12" };
        let m = s.match(new RegExp("^(" + MONTHS + ")[a-z]*\\.?\\s+(\\d{1,2})\\s*(?:-|to|–|—)\\s*(\\d{1,2})\\s*,?\\s*(\\d{4})?$", "i"));
        if (m) {
            const mo = monthNum[m[1].substring(0, 3).toLowerCase()];
            if (m[4]) return { start: m[4] + "-" + mo + "-" + m[2].padStart(2, "0") };
            return { startPartial: m[1] + " " + m[2] };
        }
        m = s.match(new RegExp("^(\\d{1,2})\\s*(?:-|to|–|—)\\s*(\\d{1,2})\\s+(" + MONTHS + ")[a-z]*\\.?\\s*,?\\s*(\\d{4})?$", "i"));
        if (m) {
            const mo = monthNum[m[3].substring(0, 3).toLowerCase()];
            if (m[4]) return { start: m[4] + "-" + mo + "-" + m[1].padStart(2, "0") };
            return { startPartial: m[1] + " " + m[3] };
        }
        return null;
    }
    // NEW — same deterministic date-ANYWHERE scanner as PRE. parseDateRangeStart /
    // parseAnyDate above require the WHOLE raw message to be just the date, so a
    // compound "ship name + date" message (e.g. "Star Princess 7/19/26-7/26/26") never
    // matches. This searches for a numeric date anywhere in the text instead, used below
    // as a further fallback when PRE didn't already resolve it. 2-digit years normalised.
    function normalizeYear(y) {
        if (y.length === 4) return y;
        const n = parseInt(y, 10);
        return String(n <= 68 ? 2000 + n : 1900 + n);
    }
    // Same five-shape, earliest-match scanner as PRE (numeric slash/dash, "Month D,
    // Year", "D Month Year", "Month D1-D2, Year" range, "D1-D2 Month Year" range) —
    // picks whichever date starts earliest in the raw text, so a range like
    // "jan 10 2026 to jan 16 2026" correctly picks the 10th, and "June 3-7, 2026"
    // correctly picks the 3rd; the two range shapes only ever extract D1, never D2.
    function findStartDateAnywhere(text) {
        if (!text) return null;
        const s = String(text);
        const MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec";
        const monthNum = { jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12" };
        const candidates = [];
        let m = s.match(/\b(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})\b/);
        if (m) candidates.push({ index: m.index, date: normalizeYear(m[3]) + "-" + m[1].padStart(2, "0") + "-" + m[2].padStart(2, "0") });
        m = s.match(new RegExp("\\b(" + MONTHS + ")[a-z]*\\.?\\s+(\\d{1,2})\\s*(?:-|to|–|—)\\s*(\\d{1,2})\\s*,?\\s*(\\d{4})\\b", "i"));
        if (m) candidates.push({ index: m.index, date: m[4] + "-" + monthNum[m[1].substring(0, 3).toLowerCase()] + "-" + m[2].padStart(2, "0") });
        m = s.match(new RegExp("\\b(\\d{1,2})\\s*(?:-|to|–|—)\\s*(\\d{1,2})\\s+(" + MONTHS + ")[a-z]*\\.?\\s*,?\\s*(\\d{4})\\b", "i"));
        if (m) candidates.push({ index: m.index, date: m[4] + "-" + monthNum[m[3].substring(0, 3).toLowerCase()] + "-" + m[1].padStart(2, "0") });
        m = s.match(new RegExp("\\b(" + MONTHS + ")[a-z]*\\.?\\s+(\\d{1,2})(?:st|nd|rd|th)?,?\\s+(\\d{4})\\b", "i"));
        if (m) candidates.push({ index: m.index, date: m[3] + "-" + monthNum[m[1].substring(0, 3).toLowerCase()] + "-" + m[2].padStart(2, "0") });
        m = s.match(new RegExp("\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+(" + MONTHS + ")[a-z]*\\.?\\s*,?\\s+(\\d{4})\\b", "i"));
        if (m) candidates.push({ index: m.index, date: m[3] + "-" + monthNum[m[2].substring(0, 3).toLowerCase()] + "-" + m[1].padStart(2, "0") });
        if (!candidates.length) return null;
        candidates.sort((a, b) => a.index - b.index);
        return candidates[0].date;
    }
    if (!Array.isArray(sd.dateSkippedFields)) sd.dateSkippedFields = [];
    // snapshot BEFORE mutations — which field is this turn collecting?
    const _snapSkipped       = [...sd.dateSkippedFields];
    const _snapStartResolved = isFullDate(sd.start_date) || isFullDate(context.entities.start_date) || _snapSkipped.includes("start_date");
    const _snapEndResolved   = isFullDate(sd.end_date)   || isFullDate(context.entities.end_date)   || _snapSkipped.includes("end_date");
    const _snapToolCallDone  = sd.toolCallDone === true;
    let fieldBeingAskedThisTurn = null;
    if      (!_snapStartResolved) fieldBeingAskedThisTurn = "start_date";
    else if (!_snapEndResolved)   fieldBeingAskedThisTurn = "end_date";
    // FIX D — same candidate chain as PRE. sd.lastMessage (context.session.BotUserSession.lastMessage)
    // is the durable, persistent session-store copy of the last real inbound message — confirmed live
    // to still hold the correct text after an internal transition, unlike the transient
    // context.session.lastMessage alias (missing the .BotUserSession segment). NLAnalysis.userInput
    // is confirmed UNRELIABLE (returns a stale value from an unrelated earlier reply, not just
    // empty), so it's kept only as an absolute last resort.
    const rawInputCandidatesPost = [
        sd.lastMessage?.messagePayload?.message?.body,
        context.session?.lastMessage?.messagePayload?.message?.body,
        (typeof User_Input !== "undefined") ? User_Input : undefined,
        context.userInputs?.originalInput?.sentence,
        context.NLAnalysis?.userInput,
    ];
    const rawUserInput = (rawInputCandidatesPost.find(v => !!v) || "").toLowerCase().trim();
    const writtenThisTurn = new Set();
    function writeEntity(key, val, aliases) {
        context.entities[key] = val; context.amendEntities[key] = val; sd[key] = val;
        if (aliases) aliases.forEach(a => sd[a] = val);
        writtenThisTurn.add(key);
        koreDebugger.log("POST | entity written: " + key + " = " + val);
    }
    // ── STEP 1 — itinerary tool response ─────────────────────────────────────
    if (sd.toolCallDone !== true) {
    const itineraryBody = context.HD_TriggerAgenticAppForItineraryData?.response?.body ||
                              context.HD_TriggerAgenticAppForItiernaryData?.response?.body;
        if (itineraryBody) {
            try {
                const txt = itineraryBody.output?.[0]?.content || JSON.stringify(itineraryBody);
                const isoStart  = txt.match(/(?:Embarkation(?:\s*Date)?|Start\s*Date)\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})/i) ||
                                  txt.match(/(?:starts?\s+on|departing(?:\s+on)?|embark(?:ing|s)?(?:\s+on)?)\s*([0-9]{4}-[0-9]{2}-[0-9]{2})/i);
                const txtStart  = txt.match(/(?:Embarkation|Start\s*Date)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i) ||
                                  txt.match(/(?:starts?\s+on|departing(?:\s+on)?)\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i);
                const isoEnd    = txt.match(/(?:Debarkation(?:\s*Date)?|End\s*Date)\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})/i) ||
                                  txt.match(/(?:ends?\s+on|arrives?(?:\s+on)?|disembark(?:ing|s)?(?:\s+on)?)\s*([0-9]{4}-[0-9]{2}-[0-9]{2})/i);
                const txtEnd    = txt.match(/(?:Debarkation|End\s*Date)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i) ||
                                  txt.match(/(?:ends?\s+on|arrives?(?:\s+on)?)\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})/i);
                const toolStartDate = (isoStart && parseAnyDate(isoStart[1])) || (txtStart && parseAnyDate(txtStart[1])) || null;
                let   toolEndDate   = (isoEnd   && parseAnyDate(isoEnd[1]))   || (txtEnd   && parseAnyDate(txtEnd[1]))   || null;
                if (!toolEndDate) {
                    const allIso = txt.match(/[0-9]{4}-[0-9]{2}-[0-9]{2}/g) || [];
                    if (allIso.length >= 2) {
                        const last = parseAnyDate(allIso[allIso.length - 1]);
                        if (last && last !== toolStartDate) toolEndDate = last;
                    }
                }
                sd.toolCallDone = true;
                const low = txt.toLowerCase();
                const isNoMatch = low.includes("no sailing") || low.includes("not available") || low.includes("closest") || low.includes("does not have a sailing");
                const isNoAlt   = low.includes("no close alternative") || low.includes("no alternative itinerar") || (!toolStartDate && !toolEndDate);
                const requestedStart = isFullDate(sd.lastUserStartDate) ? sd.lastUserStartDate
                                     : (isFullDate(context.entities.start_date) ? context.entities.start_date
                                     : (isFullDate(sd.start_date) ? sd.start_date : null));

                const closestEqualsRequested =
                    isNoMatch && !isNoAlt && toolStartDate && toolEndDate &&
                    requestedStart && toolStartDate === requestedStart;
                if (closestEqualsRequested) {
                    writeEntity("start_date", toolStartDate, ["usr_start_date"]);
                    sd.waitingForConfirm = false; sd.itineraryValidated = true;
                    sd.suggestionRejectCount = 0; sd.lastUserStartDate = null;
                    sd.suggestedStartDate = null; sd.suggestedEndDate = null;
                    koreDebugger.log("POST | tool 'closest' == requested start (" + toolStartDate + ") → exact match; ask end date");
                } else  if (isNoMatch) {
                    if (!isNoAlt && toolStartDate) {
                        sd.suggestedStartDate = toolStartDate; sd.suggestedEndDate = toolEndDate;
                        sd.waitingForConfirm = true; sd.itineraryValidated = false;
                    } else {
                        sd.waitingForConfirm = false; sd.itineraryValidated = true;
                        sd.suggestionRejectCount = 0; sd.lastUserStartDate = null;
                        sd.suggestedStartDate = null; sd.suggestedEndDate = null;
                    }
                } else {
                    if (toolStartDate && isFullDate(toolStartDate)) writeEntity("start_date", toolStartDate, ["usr_start_date"]);
                    if (toolEndDate   && isFullDate(toolEndDate))   writeEntity("end_date",   toolEndDate,   ["usr_end_date"]);
                    sd.waitingForConfirm = false; sd.itineraryValidated = true;
                    sd.suggestionRejectCount = 0; sd.lastUserStartDate = null;
                }
            } catch (err) { koreDebugger.log("POST | itinerary parse error: " + err); }
        }
    }
    // ── STEP 2 — parse LLM JSON ──────────────────────────────────────────────
    const raw = context.AI_Assisted_Dialogs?.bot_response?.bot || "";
    let parsed = null;
    if (raw.trim()) {
        try { const m = raw.match(/\{[\s\S]*\}/); if (m) parsed = JSON.parse(m[0]); }
        catch (e) { koreDebugger.log("POST | JSON parse error: " + e); }
    }
    // ── STEP 3 — write entities from LLM JSON ────────────────────────────────
    if (parsed) {
        if (parsed.confirmed === "yes" && sd.waitingForConfirm && !sd.itineraryValidated) {
            if (sd.suggestedStartDate) writeEntity("start_date", sd.suggestedStartDate, ["usr_start_date"]);
            if (sd.suggestedEndDate)   writeEntity("end_date",   sd.suggestedEndDate,   ["usr_end_date"]);
            sd.waitingForConfirm = false; sd.itineraryValidated = true;
            sd.suggestionRejectCount = 0; sd.lastUserStartDate = null; sd.lastRejectedDate = null;
        }
        else if (parsed.confirmed === "no") {
            const statedDate = parsed.user_stated_date ? parseAnyDate(String(parsed.user_stated_date)) : null;
            if (statedDate && isFullDate(statedDate)) {
                writeEntity("start_date", statedDate, ["usr_start_date"]);
                sd.waitingForConfirm = false; sd.itineraryValidated = true; sd.toolCallDone = true;
                sd.suggestionRejectCount = 0; sd.suggestedStartDate = null; sd.suggestedEndDate = null;
                sd.lastUserStartDate = null; sd.lastRejectedDate = null; sd.sameStartDateRepeated = false; sd.rejectionReset = false;
            } else {
                sd.waitingForConfirm = false; sd.toolCallDone = false; sd.itineraryValidated = false;
                sd.suggestionRejectCount = 0; sd.suggestedStartDate = null; sd.suggestedEndDate = null;
                sd.sameStartDateRepeated = false; sd.rejectionReset = false;
                delete context.entities.start_date; delete context.amendEntities.start_date; sd.start_date = null; sd.usr_start_date = null;
                delete context.entities.end_date;   delete context.amendEntities.end_date;   sd.end_date = null;   sd.usr_end_date = null;
            }
        }
        else {
            if (parsed.start_date) {
                // NEW — the LLM may echo a whole RANGE back as start_date (e.g.
                // "June 3-7, 2026" or "13-20 July 2026") instead of splitting it
                // itself. Check for a range BEFORE parseAnyDate: parseAnyDate's
                // regexes aren't anchored, so a day-first range can match the
                // trailing "D2 Month Year" substring and silently return the LATER
                // date. Recover ONLY the first (earlier) date and feed it into the
                // exact same handling a normal single date would get below — the
                // second date in the range is intentionally dropped; end_date still
                // only ever comes from the itinerary tool call or a later question.
                const range = parseDateRangeStart(String(parsed.start_date));
                const incoming = (range && range.start) ? range.start : parseAnyDate(String(parsed.start_date));
                if (incoming && isFullDate(incoming)) {
                    if (sd.toolCallDone === true && sd.itineraryValidated === false) {
                        sd.sameStartDateRepeated = false; sd.lastUserStartDate = incoming;
                        writeEntity("start_date", incoming, ["usr_start_date"]);
                        sd.itineraryValidated = true; sd.lastRejectedDate = null;
                    } else if (sd.lastRejectedDate && incoming === sd.lastRejectedDate) {
                        sd.sameStartDateRepeated = true;
                    } else {
                        sd.sameStartDateRepeated = false; sd.lastUserStartDate = incoming;
                        if (!isFullDate(context.entities.start_date)) writeEntity("start_date", incoming, ["usr_start_date"]);
                    }
                } else if (range && range.startPartial) {
                    if (!sd.partial_start_date) sd.partial_start_date = range.startPartial;
                } else {
                    const rv = String(parsed.start_date).trim();
                    if (rv && !sd.partial_start_date && !isFullDate(rv)) sd.partial_start_date = rv;
                }
            }
            const hasVesselId  = !!(context.entities.vessel_id || sd.vessel_id);
            const needsEndDate = hasVesselId && sd.itineraryValidated === true && !isFullDate(context.entities.end_date);
            const acceptEnd    = !hasVesselId || needsEndDate;
            if (parsed.end_date && acceptEnd) {
                const ed = parseAnyDate(String(parsed.end_date));
                if (ed && isFullDate(ed) && !isFullDate(context.entities.end_date)) writeEntity("end_date", ed, ["usr_end_date"]);
                else if (!ed) { const rv = String(parsed.end_date).trim(); if (rv && !sd.partial_end_date && !isFullDate(rv)) sd.partial_end_date = rv; }
            }
        }
        if (context.AI_Assisted_Dialogs?.bot_response !== undefined)
            context.AI_Assisted_Dialogs.bot_response.bot = parsed.next_question || "";
    }
    // -- STEP 3.3b -- deterministic raw-date recovery (added) --
    if (parsed && parsed.confirmed !== "yes" && parsed.confirmed !== "no" && !sd.waitingForConfirm) {
        if (fieldBeingAskedThisTurn === "start_date" &&
            !writtenThisTurn.has("start_date") && !isFullDate(context.entities.start_date) && !sd.partial_start_date) {
            // NEW — the raw message itself may be a RANGE (e.g. "Jan 2-6, 2026" or
            // "13-20 July 2026") that the LLM failed to parse at all. Check for a
            // range BEFORE parseAnyDate: parseAnyDate's regexes aren't anchored, so
            // a day-first range can match the trailing "D2 Month Year" substring and
            // silently return the LATER date. Recover ONLY the first (earlier) date
            // — end_date is never taken from a range; it still comes only from the
            // itinerary tool call or a later question, exactly as before.
            const recoveredRange = parseDateRangeStart(rawUserInput);
            if (recoveredRange && recoveredRange.start) {
                sd.sameStartDateRepeated = false; sd.lastUserStartDate = recoveredRange.start;
                writeEntity("start_date", recoveredRange.start, ["usr_start_date"]);
                if (sd.toolCallDone === true && sd.itineraryValidated === false) { sd.itineraryValidated = true; sd.lastRejectedDate = null; }
                if (context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs.bot_response !== undefined) context.AI_Assisted_Dialogs.bot_response.bot = "";
                koreDebugger.log("POST | raw-date range recovery (start only): start=" + recoveredRange.start + " (LLM returned null)");
            } else if (recoveredRange && recoveredRange.startPartial) {
                if (!sd.partial_start_date) sd.partial_start_date = recoveredRange.startPartial;
            } else {
                const recoveredStart = parseAnyDate(rawUserInput);
                if (recoveredStart && isFullDate(recoveredStart)) {
                    sd.sameStartDateRepeated = false; sd.lastUserStartDate = recoveredStart;
                    writeEntity("start_date", recoveredStart, ["usr_start_date"]);
                    if (sd.toolCallDone === true && sd.itineraryValidated === false) { sd.itineraryValidated = true; sd.lastRejectedDate = null; }
                    koreDebugger.log("POST | raw-date recovery: start_date = " + recoveredStart + " (LLM returned null)");
                } else {
                    // NEW — last resort: search the raw message ANYWHERE for a numeric
                    // date (e.g. a ship name followed by a date, "Star Princess
                    // 7/19/26-7/26/26") rather than requiring the whole message to be
                    // just the date. PRE should already have caught this before the LLM
                    // ever ran; this only fires if that somehow didn't happen.
                    const foundStart = findStartDateAnywhere(rawUserInput);
                    if (foundStart && isFullDate(foundStart)) {
                        sd.sameStartDateRepeated = false; sd.lastUserStartDate = foundStart;
                        writeEntity("start_date", foundStart, ["usr_start_date"]);
                        if (sd.toolCallDone === true && sd.itineraryValidated === false) { sd.itineraryValidated = true; sd.lastRejectedDate = null; }
                        if (context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs.bot_response !== undefined) context.AI_Assisted_Dialogs.bot_response.bot = "";
                        koreDebugger.log("POST | date found anywhere in raw message: start_date=" + foundStart + " (LLM returned null)");
                    }
                }
            }
        } else if (fieldBeingAskedThisTurn === "end_date" &&
            !writtenThisTurn.has("end_date") && !isFullDate(context.entities.end_date) && !sd.partial_end_date) {
            const recoveredEnd = parseAnyDate(rawUserInput);
            if (recoveredEnd && isFullDate(recoveredEnd)) {
                writeEntity("end_date", recoveredEnd, ["usr_end_date"]);
                if (context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs.bot_response !== undefined) context.AI_Assisted_Dialogs.bot_response.bot = "";
                koreDebugger.log("POST | raw-date recovery: end_date = " + recoveredEnd + " (LLM returned null)");
            }
        }
    }
    const hasVesselPost = !!(context.entities.vessel_id || sd.vessel_id);
    if (writtenThisTurn.has("start_date") && hasVesselPost && sd.toolCallDone !== true) {
        if (context.AI_Assisted_Dialogs?.bot_response !== undefined) context.AI_Assisted_Dialogs.bot_response.bot = "";
        sd.partial_start_date = null;
    }
    // ── STEP 3.4 — post-LLM partial + year combination ───────────────────────
    (function () {
        const y = rawUserInput.match(/\b(20\d{2}|19\d{2})\b/);
        if (!y) return;
        [["start_date","partial_start_date",["usr_start_date"]],
         ["end_date","partial_end_date",["usr_end_date"]]].forEach(([field, hintKey, aliases]) => {
            if (!sd[hintKey] || isFullDate(context.entities[field]) || writtenThisTurn.has(field)) return;
            const resolved = parseAnyDate(sd[hintKey] + " " + y[1]);
            if (resolved && isFullDate(resolved)) {
                writeEntity(field, resolved, aliases); sd[hintKey] = null;
                if (context.AI_Assisted_Dialogs?.bot_response !== undefined) context.AI_Assisted_Dialogs.bot_response.bot = "";
            }
        });
    })();

    // -- STEP 3.45 -- reject start_date that is  in the future
    (function () {
        var t = new Date();
        var todayStr = t.getFullYear() + "-" +
            String(t.getMonth() + 1).padStart(2, "0") + "-" +
            String(t.getDate()).padStart(2, "0");
        var sv = context.entities.start_date;
        if (isFullDate(sv) && sv > todayStr) {
            koreDebugger.log("POST | start_date rejected (future): " + sv);
            delete context.entities.start_date;
            delete context.amendEntities.start_date;
            sd.start_date = null;
            sd.usr_start_date = null;
            sd.lastUserStartDate = null;
            sd.partial_start_date = null;
            sd.lastRejectedDate = null;
            sd.sameStartDateRepeated = false;
            sd.suggestedStartDate = null;
            sd.suggestedEndDate = null;
            sd.toolCallDone = false;
            sd.itineraryValidated = false;
            sd.waitingForConfirm = false;
            sd.startDateRejected = true;
            writtenThisTurn.delete("start_date");
        }
    })();
    // -- STEP 3.46 -- reject end_date that is before the start
    (function () {
        var ev = context.entities.end_date;
        if (!isFullDate(ev)) return;
        var startFull = isFullDate(context.entities.start_date) ? context.entities.start_date
                      : (isFullDate(sd.start_date) ? sd.start_date
                      : (isFullDate(sd.usr_start_date) ? sd.usr_start_date : null));
     if (startFull && ev < startFull) {
        koreDebugger.log("POST | end_date rejected (before_start): " + ev);
            delete context.entities.end_date;
            delete context.amendEntities.end_date;
            sd.end_date = null;
            sd.usr_end_date = null;
            sd.partial_end_date = null;
            sd.dateCompleted = false;
            sd.endDateRejected = true;
            sd.endDateInvalidReason = "before_start";
            sd.endRejectStart = startFull;
            writtenThisTurn.delete("end_date");
        }
    })();
    // ── STEP 3.5 — infer a skip from the LLM (fallback; PRE is primary) ──────
    const isConfirmation = parsed && (parsed.confirmed === "yes" || parsed.confirmed === "no");
    if (parsed && !isConfirmation) {
        const nextQ = (parsed.next_question || "").toLowerCase();
        if (fieldBeingAskedThisTurn === "start_date" && !writtenThisTurn.has("start_date") &&
            !isFullDate(context.entities.start_date) && !sd.dateSkippedFields.includes("start_date") && parsed.start_date === null && !sd.startDateRejected) {
            const reAsking = nextQ.includes("start date") || nextQ.includes("start of your cruise");
            const askYear  = (nextQ.includes("year") || nextQ.includes("4-digit")) &&
                             (nextQ.includes("start date") || nextQ.includes("cruise start") || nextQ.includes("start on") || nextQ.includes("start of your"));
            if (!reAsking && !askYear && !sd.partial_start_date) {
                sd.dateSkippedFields = sd.dateSkippedFields.concat(["start_date"]);
                context.session.BotUserSession.dateSkippedFields = sd.dateSkippedFields;
                sd.toolCallDone = true; sd.itineraryValidated = true; sd.waitingForConfirm = false;
                koreDebugger.log("POST | LLM-inferred skip: start_date");
            }
        }
        if (fieldBeingAskedThisTurn === "end_date" && !writtenThisTurn.has("end_date") &&
            !isFullDate(context.entities.end_date) && !sd.dateSkippedFields.includes("end_date") && parsed.end_date === null && !sd.endDateRejected) {
            const askYear   = (nextQ.includes("year") || nextQ.includes("4-digit")) &&
                              (nextQ.includes("end date") || nextQ.includes("cruise end") || nextQ.includes("end on") || nextQ.includes("end of your"));
            const llmSkip   = !nextQ;
            const regressed = nextQ.includes("start date") || nextQ.includes("start of your cruise");
            if (!askYear && !sd.partial_end_date && (llmSkip || regressed)) {
                sd.dateSkippedFields = sd.dateSkippedFields.concat(["end_date"]);
                context.session.BotUserSession.dateSkippedFields = sd.dateSkippedFields;
                koreDebugger.log("POST | LLM-inferred skip: end_date");
            }
        }
    }
    // ── STEP 3.6 — self-heal: end_date wrongly skipped while LLM asks for it ──
    if (parsed) {
        const nq = (parsed.next_question || "").toLowerCase();
        if ((nq.includes("end date") || nq.includes("end of your cruise") || nq.includes("cruise end") || nq.includes("date did") || nq.includes("debarkation")) &&
            sd.dateSkippedFields.includes("end_date")) {
            sd.dateSkippedFields = sd.dateSkippedFields.filter(f => f !== "end_date");
            context.session.BotUserSession.dateSkippedFields = sd.dateSkippedFields;
        }
    }
    // -- STEP 3.7 -- surface start/end date rejection messages (PRE- or POST-side) --
    if (isFullDate(context.entities.start_date)) { sd.startDateRejected = false; }
    if (isFullDate(context.entities.end_date))   { sd.endDateRejected   = false; }
    if (sd.startDateRejected && !isFullDate(context.entities.start_date)) {
        if (context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs.bot_response !== undefined) {
            context.AI_Assisted_Dialogs.bot_response.bot =
                "The start date cannot be a future date. Please provide a past date for when your cruise started.";
        }
        sd.startDateRejected = false;
    } else if (sd.endDateRejected && !isFullDate(context.entities.end_date)) {
        if (context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs.bot_response !== undefined) {
          context.AI_Assisted_Dialogs.bot_response.bot ="The end date cannot be before the start date (" +  (sd.endRejectStart || "your start date") + "). Please provide the date your cruise ended.";
        }
        sd.endDateRejected = false;
    }
    // ── STEP 4 — sync entities -> amendEntities ──────────────────────────────
    Object.keys(context.entities).forEach(k => { if (context.entities[k] != null) context.amendEntities[k] = context.entities[k]; });
    // ── STEP 5 — completion ──────────────────────────────────────────────────
    const startSkipped = sd.dateSkippedFields.includes("start_date");
    const endSkipped   = sd.dateSkippedFields.includes("end_date");
    const hasStart  = isFullDate(context.entities.start_date) || startSkipped;
    const hasEnd    = isFullDate(context.entities.end_date)   || endSkipped;
    const hasVessel = !!(context.entities.vessel_id || sd.vessel_id);
    if (hasStart && hasEnd && (!hasVessel || sd.itineraryValidated === true)) {
        sd.dateCompleted = true; context.session.dateCompleted = true;
        koreDebugger.log("POST | dateCompleted = true");
    }
    // ── STEP 6 — advance currentlyAskingField (drives the PRE skip attribution)
    if (!isFullDate(context.entities.start_date) && !startSkipped)      sd.currentlyAskingField = "start_date";
    else if (!isFullDate(context.entities.end_date) && !endSkipped)     sd.currentlyAskingField = "end_date";
    else                                                                sd.currentlyAskingField = null;
    // ── STEP 7 — ask counts (used by prompt + by PRE entry-guard) ────────────
    if (sd.currentlyAskingField) {
        const ck = sd.currentlyAskingField + "_askCount";
        sd[ck] = (sd[ck] || 0) + 1;
    }
    ["start_date", "end_date"].forEach(f => { if (sd.currentlyAskingField !== f) sd[f + "_askCount"] = 0; });
    koreDebugger.log("POST | toolCallDone:" + sd.toolCallDone + " waitingForConfirm:" + sd.waitingForConfirm +
        " itineraryValidated:" + sd.itineraryValidated + " writtenThisTurn:" + JSON.stringify([...writtenThisTurn]) +
        " dateSkippedFields:" + JSON.stringify(sd.dateSkippedFields) + " currentlyAskingField:" + sd.currentlyAskingField +
        " entities:" + JSON.stringify(context.entities));

    // -- STEP 8 -- safety net: turn would otherwise end with an empty message (added) --
    const handingOffToTool = hasVesselPost && sd.toolCallDone !== true && isFullDate(context.entities.start_date);
    const toolJustCompletedThisRun = sd.toolCallDone === true && !_snapToolCallDone;
    if (!sd.dateCompleted && !handingOffToTool && !toolJustCompletedThisRun) {
        const currentMsg = (context.AI_Assisted_Dialogs?.bot_response?.bot || "").toString().trim();
        if (!currentMsg) {
            let fallbackMsg;
            if (sd.waitingForConfirm && sd.suggestedStartDate) {
                fallbackMsg = "Just to confirm - the closest sailing we found was Start: " + sd.suggestedStartDate +
                    (sd.suggestedEndDate ? ", End: " + sd.suggestedEndDate : "") +
                    ". Does that match your cruise? Please reply yes or no.";
            } else if (sd.currentlyAskingField === "start_date" && sd.partial_start_date) {
                fallbackMsg = "What year did your cruise start on " + sd.partial_start_date + "? Please provide the 4-digit year.";
            } else if (sd.currentlyAskingField === "end_date" && sd.partial_end_date) {
                fallbackMsg = "What year did your cruise end on " + sd.partial_end_date + "? Please provide the 4-digit year.";
            } else if (sd.currentlyAskingField === "start_date") {
                fallbackMsg = "What was the start date of your cruise? Please include the day, month, and year.";
            } else if (sd.currentlyAskingField === "end_date") {
                fallbackMsg = "What was the end date of your cruise? Please include the day, month, and year.";
            } else {
                fallbackMsg = "Sorry, could you repeat that for me?";
            }
            if (context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs.bot_response !== undefined) {
                context.AI_Assisted_Dialogs.bot_response.bot = fallbackMsg;
            }
            koreDebugger.log("POST | STEP 8 forced re-ask (empty response): " + fallbackMsg);
        }
    }
} catch (e) {
    koreDebugger.log("Date PostProcessor Error: " + e);
}
```
