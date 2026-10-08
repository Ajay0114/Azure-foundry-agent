# PC_Script_ProcessExtractedEntities  (script)

## Config
```json
{
  "name": "PC_Script_ProcessExtractedEntities",
  "type": "script"
}
```

## script
```
try {
    context.entities = context.entities || {};
    context.session = context.session || {};
    context.session.BotUserSession = context.session.BotUserSession || {};
    const raw = context.GenerativeAINode?.PC_ExtractCruiseEntitiesFromInitialUserMessage?.text;
    if (!raw) {
        koreDebugger.log("Script Node 2: No prompt output found, skipping extraction.");
        return;
    }
    const clean = raw.replace(/```json|```/gi, "").trim();
    let parsed;
    try {
        parsed = JSON.parse(clean);
    } catch (e) {
        koreDebugger.log("Script Node 2 JSON Parse Error: " + e);
        return;
    }

    const SENTINEL_VALUES = new Set([
        "unknown", "not sure", "i don't know", "i dont know", "dont know",
        "don't know", "no idea", "n/a", "na", "none", "not applicable",
        "ship", "boat", "cruise", "vessel", "the ship", "a ship"
    ]);
    function isValidEntityValue(val) {
        if (val === null || val === undefined) return false;
        const str = String(val).trim();
        if (str === "") return false;
        if (SENTINEL_VALUES.has(str.toLowerCase())) return false;
        return true;
    }
    const unknownFields = Array.isArray(parsed.unknown_indicated_fields)
        ? parsed.unknown_indicated_fields
        : [];
    if (unknownFields.length > 0) {
        context.session.BotUserSession.unknownIndicatedFields = unknownFields;
        koreDebugger.log("Script Node 2 — Unknown indicated fields: " + JSON.stringify(unknownFields));
    }
    if (isValidEntityValue(parsed.ship_name_candidate)) {
        context.entities.ship_name = parsed.ship_name_candidate;
        context.session.BotUserSession.ship_name = parsed.ship_name_candidate;
        koreDebugger.log("ship_name stored: " + parsed.ship_name_candidate);
    }
    if (isValidEntityValue(parsed.cruise_line_candidate)) {
        context.entities.cruise_line = parsed.cruise_line_candidate;
        context.session.BotUserSession.cruise_line = parsed.cruise_line_candidate;
        koreDebugger.log("cruise_line stored: " + parsed.cruise_line_candidate);
    }

    // Day present? (full date, or day+month partial). Month-only / year-only → false.
    function hasDay(raw) {
        if (!raw) return false;
        const s = String(raw).trim();
        if (/^\d{4}[\/.\-]\d{1,2}[\/.\-]\d{1,2}$/.test(s)) return true;
        if (/^\d{1,2}[\/.\-]\d{1,2}[\/.\-]\d{4}$/.test(s)) return true;
        const stripped = s
            .replace(/\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b/gi, "")
            .replace(/\b(last|next|this|the)\b/gi, "")
            .replace(/\b(20\d{2}|19\d{2})\b/g, "")
            .replace(/\b(st|nd|rd|th)\b/gi, "")
            .replace(/[^0-9]/g, " ")
            .trim();
        return /\d+/.test(stripped);
    }

    // Normalise any supported format to ISO (YYYY-MM-DD); null if not a complete, valid date.
    function normalizeDate(str) {
        if (!str) return null;
        str = String(str).trim()
            .replace(/(\d{1,2})(st|nd|rd|th)\b/gi, "$1")
            .replace(/,/g, " ")
            .replace(/\s+/g, " ")
            .trim();
        const months = { jan:"01",feb:"02",mar:"03",apr:"04",may:"05",jun:"06",
                         jul:"07",aug:"08",sep:"09",oct:"10",nov:"11",dec:"12" };
        function build(y, mo, d) {
            const yy = parseInt(y,10), mm = parseInt(mo,10), dd = parseInt(d,10);
            if (isNaN(yy)||isNaN(mm)||isNaN(dd)||mm<1||mm>12||dd<1||dd>31) return null;
            const dt = new Date(Date.UTC(yy, mm-1, dd));   // reject impossible days (e.g. Feb 30)
            if (dt.getUTCFullYear()!==yy||dt.getUTCMonth()!==mm-1||dt.getUTCDate()!==dd) return null;
            return yy + "-" + ("0"+mm).slice(-2) + "-" + ("0"+dd).slice(-2);
        }
        // year-first (strict ISO order): 2026-04-20, 2026/4/20
        let m = str.match(/^(\d{4})[\/.\-](\d{1,2})[\/.\-](\d{1,2})$/);
        if (m) return build(m[1], m[2], m[3]);
        // numeric day/month + 4-digit year — resolve order by value
        m = str.match(/^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{4})$/);
        if (m) {
            const a = parseInt(m[1],10), b = parseInt(m[2],10);
            if (a > 12 && b <= 12) return build(m[3], b, a);   // DD-MM-YYYY (a can only be a day)
            if (b > 12 && a <= 12) return build(m[3], a, b);   // MM-DD-YYYY (b can only be a day)
            return build(m[3], a, b);                          // both ≤12 → month-first (default)
        }
        // month name in ANY order: "March 10 2026", "10 March 2026", "March 2026 10"
        const moHit = str.toLowerCase().match(/\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/);
        if (moHit) {
            const year = str.match(/\b(\d{4})\b/);
            const rest = str.replace(/\b\d{4}\b/, " ");
            const day  = rest.match(/\b(\d{1,2})\b/);
            if (year && day) return build(year[1], months[moHit[1]], day[1]);
        }
        return null;
    }

    function storeDate(field, rawVal) {
        if (!isValidEntityValue(rawVal)) return;
        if (!hasDay(rawVal)) {
            koreDebugger.log(field + " rejected (no day component): " + rawVal);
            return;
        }
        const iso = normalizeDate(rawVal);
        if (iso) {
            context.entities[field] = iso;
            context.session.BotUserSession[field] = iso;
            koreDebugger.log(field + " stored: " + iso + " (normalised)");
            return;
        }
        // Has a 4-digit year but won't parse → malformed. Reject; do NOT store raw.
        if (/\b(?:19|20)\d{2}\b/.test(String(rawVal))) {
            koreDebugger.log(field + " rejected (unparseable/invalid date): " + rawVal);
            return;
        }
        // Partial like "mar 10" (no year) → keep raw so the orchestrator asks for the year.
        const partial = String(rawVal).trim();
        context.entities[field] = partial;
        context.session.BotUserSession[field] = partial;
        koreDebugger.log(field + " stored: " + partial + " (partial, awaiting year)");
    }

    storeDate("start_date",   parsed.start_date_raw);
    storeDate("end_date",     parsed.end_date_raw);
    storeDate("service_date", parsed.service_date_raw);

    koreDebugger.log("===== Script Node 2 — Final Entities =====");
    koreDebugger.log(context.entities);
} catch (e) {
    koreDebugger.log("Script Node 2 Error: " + e);
}
```
