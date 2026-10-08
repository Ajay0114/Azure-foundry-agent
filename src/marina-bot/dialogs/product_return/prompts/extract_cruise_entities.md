Extract cruise-related entity values from the user input using the conversation context.

Instructions:
1.  Extract only what is explicitly mentioned or strongly implied as a real, specific proper noun or date value.
2.  Use the conversation history to resolve references like "it", "this", "that".
3.  Do NOT guess or infer missing values.
4.  Do NOT validate correctness of values.
5.  Do NOT normalize or convert dates — keep raw text as written by the user.
6.  If the input is too short, ambiguous, or contains no extractable information (e.g., "yes", "no", "ok", "hi", "hello"), return all nulls and mark extractionSuccessful as "failure".
7.  If the user says they do not know a value ("I don't know", "not sure", "no idea"), set that field to null and add the field name to unknown_indicated_fields. NEVER store the literal word "unknown" or similar strings as an entity value.
8.  ship_name_candidate and cruise_line_candidate MUST be real, specific proper nouns. Generic words like "ship", "boat", "cruise", "vessel", "the ship", or any vague placeholder are NOT valid — set them to null.
9.  Do NOT add explanations or extra text outside the JSON.
10. Always return strict JSON only.

Entities to extract:
- ship_name_candidate   → specific vessel name (e.g., Carnival Dream, Wonder of the Seas)
- cruise_line_candidate → cruise company name (e.g., Carnival, Royal Caribbean, Norwegian)
- start_date_raw        → cruise/voyage/sailing start (embarkation) date, exactly as written
- end_date_raw          → cruise/voyage/sailing end (debarkation) date, exactly as written
- service_date_raw      → date of a specific spa treatment, charge, purchase, or incident that
                          occurred DURING the cruise — must be distinct from the cruise start date

════════════════════════════════════════════════════════════
DATE DISAMBIGUATION RULES (apply these in order):
════════════════════════════════════════════════════════════

RULE 1 — Voyage vs. service date:
  A date is start_date_raw when:
    - It describes when the cruise/voyage/sailing/trip BEGAN or DEPARTED.
    - It follows words like: "sailed", "sailed on", "cruise started", "voyage started",
      "departed", "embarked", "boarded", "cruise began", "trip started", "we left on",
      "cruise was", "I was on a cruise", "sailed from".
    - The sentence is about the cruise itself, not about a charge or incident.

  A date is service_date_raw ONLY when:
    - It is explicitly tied to a SPECIFIC service, charge, purchase, treatment, or
      incident that occurred ON A PARTICULAR DAY during the cruise.
    - It follows words like: "spa on", "treatment on", "charged on", "purchase on",
      "incident on", "the charge was on", "it happened on", "the service was on".

RULE 2 — "Billing/charge started on [date]" pattern:
  When a user says something like "a billing/charge/issue that started on [date]" or
  "billing which started on [date]" or "a dispute that started on [date]", the date
  refers to when their CRUISE/VOYAGE started — NOT a service_date_raw.
  Extract it as start_date_raw.
  Rationale: billing disputes are tied to the voyage, and "started on" in this context
  means the voyage start, not a spa/service appointment date.

RULE 3 — Single date, no cruise dates context:
  If only ONE date is mentioned and the message is about a billing issue, charge dispute,
  or general cruise question with no explicit indication it is a spa/service date,
  default to extracting it as start_date_raw.

RULE 4 — Multiple dates:
  If the user provides multiple dates, use surrounding language to assign each:
    - Earliest date + embarkation language → start_date_raw
    - Latest date + debarkation language → end_date_raw
    - A date tied to a specific service/treatment/charge → service_date_raw

RULE 5 — When in doubt between start_date_raw and service_date_raw:
  If you cannot confidently distinguish, prefer start_date_raw and leave
  service_date_raw as null. It is safer to ask for the service date later
  than to misclassify the voyage start date.

RULE 6 — Compressed date ranges (shared month/year):
  When the user expresses a date range in compressed form such as:
    "January 11 to 18 2026"
    "March 3–10, 2025"
    "Apr 18 to 25"
    "Nov 29 to Dec 6 2025"
  The month (and year, if present) that precedes the range applies to BOTH
  the start date AND the end date unless the end date has its own explicit month.

  Reconstruct the end date by inheriting the missing month/year from the start:
    "January 11 to 18 2026" → start: "January 11 2026", end: "January 18 2026"
    "March 3–10, 2025"      → start: "March 3 2025",    end: "March 10 2025"
    "Apr 18 to 25"          → start: "Apr 18",           end: "Apr 25"
    "Nov 29 to Dec 6 2025"  → start: "Nov 29 2025",      end: "Dec 6 2025"
      (end has its own month Dec, so no carry-over needed)

  IMPORTANT: Do NOT store the raw fragment ("18 2026") — always store the
  fully reconstructed date string ("January 18 2026").

════════════════════════════════════════════════════════════
EXAMPLES:
════════════════════════════════════════════════════════════
  
Input: "I sailed with Carnival and have a billing question about a cruise that started on Mar 17"
→ start_date_raw: "Mar 17", service_date_raw: null
(Reason: "started on" refers to the cruise departure)

Input: "I was on Carnival Panorama Apr 18 to Apr 25 and had a spa treatment on Apr 22"
→ start_date_raw: "Apr 18", end_date_raw: "Apr 25", service_date_raw: "Apr 22"
(Reason: explicit cruise dates + explicit spa treatment date)

Input: "I have a question about a billing which started on Mar 17"
→ start_date_raw: "Mar 17", service_date_raw: null
(Reason: "billing which started on" → voyage start per RULE 2)

Input: "I was charged for a massage on March 22 during my cruise"
→ start_date_raw: null, service_date_raw: "March 22"
(Reason: explicitly tied to a specific service "massage on March 22")

Input: "I cruised in April and was charged for a treatment on April 5"
→ start_date_raw: null, service_date_raw: "April 5"
(Reason: the treatment date is explicit; voyage start is only "April" which is too vague)

Input: "I was on the Harmony of the Seas sailing January 11 to 18 2026"
→ ship_name_candidate: "Harmony of the Seas", start_date_raw: "January 11 2026",
  end_date_raw: "January 18 2026", service_date_raw: null
(Reason: compressed range — "January" carries over to the end date per RULE 6;
 end stored as "January 18 2026", not the raw fragment "18 2026")

Input: "I sailed March 3–10, 2025 on Norwegian Encore"
→ ship_name_candidate: "Norwegian Encore", start_date_raw: "March 3 2025",
  end_date_raw: "March 10 2025", service_date_raw: null
(Reason: compressed range, month and year inherited by end date per RULE 6)

════════════════════════════════════════════════════════════

Conversation History:
{{conversation_history}}

User Input:
{{initial_message}}

Output Format (STRICT JSON ONLY — no markdown, no backticks):
{
  "ship_name_candidate": null | string,
  "cruise_line_candidate": null | string,
  "start_date_raw": null | string,
  "end_date_raw": null | string,
  "service_date_raw": null | string,
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success" | "failure",
  "reason": "<short reason>"
}

