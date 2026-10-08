# HD_VesselLookupAgent  (aiassist)

## Config
```json
{
  "name": "HD_VesselLookupAgent",
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
      "promptId": "005dad21-bd98-5f86-95a8-22d2f49998c5",
      "promptName": "Vessel_Identification_Prompt",
      "isCustom": true,
      "isSysIntAndCustomPrompt": false,
      "isStreaming": false,
      "fallbackBehavior": {
        "id": "dynamicEntity",
        "onLLMFail": "skipEvent",
        "nodeId": "nd-scr-b08a0968-68c7-48a0-b35b-e554c57de008"
      }
    }
  }
}
```

## generativeAI.preProcessorScript
```
try {
    context.session   = context.session  || {};
    context.session.BotUserSession = context.session.BotUserSession || {};
    context.entities  = context.entities  || {};
    context.amendEntities = context.amendEntities  || {};

    const SENTINEL_VALUES = new Set([
        "unknown", "not sure", "i don't know", "i dont know", "dont know",
        "no idea", "n/a", "na", "none", "not applicable"
    ]);
    const VAGUE_TERMS = new Set([
        "ship", "boat", "cruise", "the ship", "the vessel",
        "a ship", "vessel", "a cruise", "the cruise"
    ]);
    function isValidStringValue(val) {
        if (!val) return false;
        const s = String(val).toLowerCase().trim();
        return !SENTINEL_VALUES.has(s) && !VAGUE_TERMS.has(s);
    }
    function isValidVesselId(id) {
        if (!id) return false;
        const str = String(id).toLowerCase().trim();
        if (SENTINEL_VALUES.has(str)) return false;
        return /^\d+$/.test(str);
    }

    const session = context.session.BotUserSession;

    // ── Trackers (init once) ─────────────────────────────────────────────────
    if (!Array.isArray(session.vesselSkippedFields)) session.vesselSkippedFields = [];
    if (typeof session.vesselLookupFailCount !== "number") session.vesselLookupFailCount = 0;
    if (typeof session.lastVesselAttempt === "undefined") session.lastVesselAttempt = "";
    if (typeof session.lastCountedVesselValue === "undefined") session.lastCountedVesselValue = "";
     if (typeof session.vesselLookupInvoked === "undefined") session.vesselLookupInvoked = false;

    // ── Sync string entities: session → context (validated) ──────────────────
    ["ship_name", "cruise_line"].forEach(field => {
        const sessionVal = session[field];
        if (isValidStringValue(sessionVal) && !isValidStringValue(context.entities[field])) {
            context.entities[field]      = sessionVal;
            context.amendEntities[field] = sessionVal;
            koreDebugger.log(field + " synced from session: " + sessionVal);
        }
    });

    // ── Sync vessel_id — numeric only ────────────────────────────────────────
    const candidateId = session.vessel_id || context.session.vessel_id;
    if (isValidVesselId(candidateId)) {
        context.entities.vessel_id      = String(candidateId);
        context.amendEntities.vessel_id = String(candidateId);
        session.vessel_id               = String(candidateId);
        koreDebugger.log("vessel_id synced (valid): " + candidateId);
    } else {
        delete context.entities.vessel_id;
        delete context.amendEntities.vessel_id;
        session.vessel_id = null;
        koreDebugger.log("vessel_id absent or invalid — cleared: " + candidateId);
    }

    koreDebugger.log("===== VESSEL AGENT PRE-PROCESSOR — entities to LLM =====");
    koreDebugger.log(JSON.stringify(context.entities));
    koreDebugger.log("vesselLookupFailCount: " + session.vesselLookupFailCount +
                     " | vesselForceContinue: " + session.vesselForceContinue);
} catch (e) {
    koreDebugger.log("Vessel Agent Pre-Processor Error: " + e);
}
```

## generativeAI.postProcessorScript
```
try {
    context.session   = context.session  || {};
    context.session.BotUserSession = context.session.BotUserSession || {};
    context.entities  = context.entities  || {};
    context.amendEntities = context.amendEntities  || {};

    koreDebugger.log("===== VESSEL AGENT POST-PROCESSOR FIRED =====");
    koreDebugger.log("toolPayload: "       + JSON.stringify(context.toolPayload));
    koreDebugger.log("entities at entry: " + JSON.stringify(context.entities));

    const SENTINEL_VALUES = new Set([
        "unknown", "not sure", "i don't know", "i dont know", "dont know",
        "no idea", "n/a", "na", "none", "not applicable"
    ]);
    const VAGUE_TERMS = new Set([
        "ship", "boat", "cruise", "the ship", "the vessel",
        "a ship", "vessel", "a cruise", "the cruise"
    ]);
    function isValidStringValue(val) {
        if (!val) return false;
        const s = String(val).toLowerCase().trim();
        return !SENTINEL_VALUES.has(s) && !VAGUE_TERMS.has(s);
    }
    function isValidVesselId(id) {
        if (!id) return false;
        const str = String(id).toLowerCase().trim();
        if (SENTINEL_VALUES.has(str)) return false;
        return /^\d+$/.test(str);
    }

    const session = context.session.BotUserSession;
    if (!Array.isArray(session.vesselSkippedFields)) session.vesselSkippedFields = [];
    if (typeof session.vesselLookupFailCount !== "number") session.vesselLookupFailCount = 0;
    if (typeof session.lastVesselAttempt === "undefined") session.lastVesselAttempt = "";
    if (typeof session.lastCountedVesselValue === "undefined") session.lastCountedVesselValue = "";
      if (typeof session.vesselLookupInvoked === "undefined") session.vesselLookupInvoked = false;

    // ── Read tool response ────────────────────────────────────────────────────
    let toolData   = null;
    let toolRawTxt = null;
    let multipleVesselsFound = false;   // FIX: list results are NOT failures

    const agenticBody = context.HD_TriggerAgenticAppForVesselData?.response?.body;
    if (agenticBody?.output?.length) {
        toolRawTxt = agenticBody.output[0].content;
        koreDebugger.log("Tool source: HD_TriggerAgenticAppForVesselData");
    }
    if (!toolRawTxt && context.toolPayload) {
        toolRawTxt = typeof context.toolPayload === "string"
            ? context.toolPayload
            : JSON.stringify(context.toolPayload);
        koreDebugger.log("Tool source: toolPayload");
    }

    if (toolRawTxt) {
        session.vesselLookupInvoked = true;  
        koreDebugger.log("Raw tool response: " + toolRawTxt);
        const jsonMatch = toolRawTxt.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
        if (jsonMatch) {
            try {
                toolData = JSON.parse(jsonMatch[0]);
                koreDebugger.log("Tool response parsed as JSON: " + JSON.stringify(toolData));
            } catch (e) {
                koreDebugger.log("Tool JSON parse failed — falling back to regex: " + e);
            }
        }

        // Single vessel from JSON object
        if (toolData && !Array.isArray(toolData)) {
            const vid   = toolData.vessel_id   || toolData.id          || "";
            const vname = toolData.vessel_name || toolData.ship_name    || "";
            const vcl   = toolData.cruise_line || toolData.fleet        || "";
            if (isValidVesselId(vid)) {
                const v = String(vid);
                context.entities.vessel_id      = v;
                context.session.vessel_id       = v;
                session.vessel_id               = v;
                context.amendEntities.vessel_id = v;
                koreDebugger.log("vessel_id from JSON (single): " + v);
            }
            if (isValidStringValue(vname)) {
                context.entities.ship_name      = vname;
                session.ship_name               = vname;
                context.amendEntities.ship_name = vname;
                koreDebugger.log("ship_name from JSON: " + vname);
            }
            if (isValidStringValue(vcl)) {
                context.entities.cruise_line      = vcl;
                session.cruise_line               = vcl;
                context.amendEntities.cruise_line = vcl;
                koreDebugger.log("cruise_line from JSON: " + vcl);
            }
        }

        // Multiple vessels (JSON array) — await user selection, NOT a failure
        if (Array.isArray(toolData) && toolData.length > 1) {
            multipleVesselsFound = true;
            koreDebugger.log("List response (JSON array) — awaiting selection. Count: " + toolData.length);
        }

        // Fallback: regex extraction if JSON parse failed
        if (!toolData) {
            const idMatches = [
                ...toolRawTxt.matchAll(/Vessel\s*ID[^0-9]*(\d+)/gi),
                ...toolRawTxt.matchAll(/\(ID\s*[:\-]?\s*(\d+)\)/gi),
                ...toolRawTxt.matchAll(/"vessel_id"\s*:\s*"?(\d+)"?/gi)
            ];
            const uniqueIds = [...new Set(idMatches.map(m => m[1]))];
            koreDebugger.log("Regex vessel IDs found: " + JSON.stringify(uniqueIds));
            if (uniqueIds.length === 1 && isValidVesselId(uniqueIds[0])) {
                const v = uniqueIds[0];
                context.entities.vessel_id      = v;
                context.session.vessel_id       = v;
                session.vessel_id               = v;
                context.amendEntities.vessel_id = v;
                koreDebugger.log("vessel_id from regex (single): " + v);
                const shipMatch =
                    toolRawTxt.match(/\*{0,2}Vessel\s*Name\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*\{\}\"]+)/i) ||
                    toolRawTxt.match(/"(?:vessel_name|ship_name)"\s*:\s*"([^"]+)"/i);
                if (shipMatch) {
                    const s = shipMatch[1].trim();
                    if (isValidStringValue(s)) {
                        context.entities.ship_name      = s;
                        session.ship_name               = s;
                        context.amendEntities.ship_name = s;
                    }
                }
                const clMatch =
                    toolRawTxt.match(/\*{0,2}(?:Fleet|Cruise\s*Line)\*{0,2}\s*[:\-]\s*\*{0,2}([^\n\*\{\}\"]+)/i) ||
                    toolRawTxt.match(/"cruise_line"\s*:\s*"([^"]+)"/i);
                if (clMatch) {
                    const cl = clMatch[1].trim();
                    if (isValidStringValue(cl)) {
                        context.entities.cruise_line      = cl;
                        session.cruise_line               = cl;
                        context.amendEntities.cruise_line = cl;
                    }
                }
            } else if (uniqueIds.length > 1) {
                multipleVesselsFound = true;
                koreDebugger.log("Multiple IDs via regex — awaiting selection.");
            }
        }
    }

    // ════════════════════════════════════════════════════════════════════════
    // FIX — Cap vessel lookups at 2 ATTEMPTS, then accept the user's value
    //       and continue to the next node. Never ask a 3rd time.
    //
    //   failed attempt = tool ran  AND  no numeric vessel_id resolved
    //                    AND  not a multi-result list   (wording-independent)
    //   de-duped on the user's input value so one turn can't count twice.
    //   on the 2nd failure: record ship_name + mark the node COMPLETE
    //   deterministically (not only via the LLM) so it always moves on.
    // ════════════════════════════════════════════════════════════════════════
    const vesselIdResolvedNow = isValidVesselId(context.entities.vessel_id);
    const vesselLookupFailed  = !!toolRawTxt && !vesselIdResolvedNow && !multipleVesselsFound;

    if (vesselLookupFailed) {
        // The value the user actually supplied this turn
        let attemptedVessel = String(context.session?.lastMessage?.messagePayload?.message?.body || "").trim();
        if (!attemptedVessel) {
            const m = toolRawTxt.match(/matching\s+['"]?([^'"]+?)['"]?\s+(?:was|were)?\s*(?:not\s+)?found/i);
            if (m && m[1]) attemptedVessel = m[1].trim();
        }

        const dedupeKey      = attemptedVessel.toLowerCase();
        const alreadyCounted = dedupeKey && dedupeKey === String(session.lastCountedVesselValue).toLowerCase();

        if (!alreadyCounted) {
            session.vesselLookupFailCount  = (Number(session.vesselLookupFailCount) || 0) + 1;
            session.lastCountedVesselValue = attemptedVessel;
            if (isValidStringValue(attemptedVessel)) session.lastVesselAttempt = attemptedVessel;
            koreDebugger.log("Vessel lookup failed (#" + session.vesselLookupFailCount + ") for: " + attemptedVessel);
        } else {
            koreDebugger.log("Duplicate failure ignored for: " + attemptedVessel);
        }

        // ── 2nd failed attempt → accept value, complete, continue ────────────
        if (session.vesselLookupFailCount >= 2) {
            const finalShipName = isValidStringValue(session.lastVesselAttempt)
                ? session.lastVesselAttempt
                : (isValidStringValue(attemptedVessel) ? attemptedVessel : "");

            if (finalShipName) {
                context.entities.ship_name      = finalShipName;
                session.ship_name               = finalShipName;
                context.amendEntities.ship_name = finalShipName;
            }
            session.vesselForceContinue = true;

            // Deterministic completion — do NOT rely only on the LLM to stop asking
            context.session.vesselCompleted         = true;
            session.vesselCompleted                 = true;
            context.session.conversationState       = "COMPLETED";
            context.session.activeConversationAgent = null;

            koreDebugger.log("Max vessel attempts (2) reached — accepting '" +
                             finalShipName + "' as ship_name and continuing to next node.");
        }
    }

    // ── Sync all entities into amendEntities ─────────────────────────────────
    Object.keys(context.entities).forEach(key => {
        const val = context.entities[key];
        if (val !== null && val !== undefined && val !== "") {
            context.amendEntities[key] = val;
        }
    });

    // ── Completion check (resolved vessel) ───────────────────────────────────
    const vesselIdResolved = isValidVesselId(context.entities.vessel_id);
    const shipNameValid    = isValidStringValue(context.entities.ship_name);
    const cruiseLineValid  = isValidStringValue(context.entities.cruise_line);

    koreDebugger.log("vessel_id:   " + context.entities.vessel_id + " | resolved: " + vesselIdResolved);
    koreDebugger.log("ship_name:   " + context.entities.ship_name + " | valid: "    + shipNameValid);
    koreDebugger.log("cruise_line: " + context.entities.cruise_line + " | valid: "  + cruiseLineValid);

    if (vesselIdResolved) {
        // Successful resolution clears the attempt trackers
        session.vesselLookupFailCount  = 0;
        session.lastCountedVesselValue = "";
        session.vesselForceContinue    = false;
    }

    if (vesselIdResolved && (shipNameValid || cruiseLineValid)) {
        context.session.vesselCompleted         = true;
        session.vesselCompleted                 = true;
        context.session.conversationState       = "COMPLETED";
        context.session.activeConversationAgent = null;
        koreDebugger.log("===== VESSEL COLLECTION COMPLETE (resolved) =====");
    }

    koreDebugger.log("===== VESSEL AGENT FINAL ENTITIES =====");
    koreDebugger.log(JSON.stringify(context.entities));


} catch (e) {
    koreDebugger.log("Vessel Agent Post-Processor Error: " + e);
}
```
