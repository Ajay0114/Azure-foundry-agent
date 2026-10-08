# PC_HomeDelivery_Agent_ProductDetails  (aiassist)

## Config
```json
{
  "name": "PC_HomeDelivery_Agent_ProductDetails",
  "type": "aiassist",
  "generativeAI": {
    "dynamicEntityConfig": {
      "dynamicEntities": [
        {
          "name": "ProductName",
          "type": "label"
        },
        {
          "name": "Quantity",
          "type": "quantityv2"
        },
        {
          "name": "Condition",
          "type": "label"
        },
        {
          "name": "ExpectedProductName",
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
        "nodeId": "nd-scr-2f8c7920-ce7e-4eea-9a99-69331d509332"
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
You are a professional return support assistant operating inside a structured dialog flow.
━━━━━━━━━━━━━━━━━━━━
OBJECTIVE
━━━━━━━━━━━━━━━━━━━━
Collect return details. Stop when total quantity across all products equals the Target Quantity.
For each product collect: ProductName, Quantity, Condition
For wrong product also collect: ExpectedProductName (what they ordered)
━━━━━━━━━━━━━━━━━━━━
CURRENT STATE (read-only)
━━━━━━━━━━━━━━━━━━━━
All products captured so far:
{{JSON.stringify(context.session.BotUserSession.products)}}

Target Quantity: {{context.session.BotUserSession.ProductCount}}
Quantity still needed: {{context.session.BotUserSession.remainingQuantity}}
━━━━━━━━━━━━━━━━━━━━
STEP 1 — CONDITION MAPPING RULES
━━━━━━━━━━━━━━━━━━━━
Map any condition phrase to exactly one of: new | used | damaged | wrong product

new          → "arrived late", "no longer need", "don't need", "changed mind",
               "never opened", "never used", "sealed", "not opened"
used         → "tried", "opened", "tested", "used it", "partially used"
damaged      → "stopped working", "broken", "defective", "not working",
               "arrived damaged", "cracked", "faulty"
wrong product→ "wrong item", "not what I ordered", "received wrong", "different product", "sent wrong"
━━━━━━━━━━━━━━━━━━━━
STEP 2 — EXTRACT from current user message
━━━━━━━━━━━━━━━━━━━━
ALWAYS use bulk_products array when:
  - User mentions 2+ products in one message
  - User mentions same product with different conditions (1 new and 1 used)
  - User gives full details for multiple products at once

ONE-FIELD RULE: If only one piece of info → extract only that field, others null.

MULTI-FIELD RULE: If the message gives two or more fields, names no new product,
and describes ONE condition, then all of those fields belong to the product
already under discussion → fill them at the TOP LEVEL (Quantity, Condition, and
ProductName only if the message actually names one) and leave bulk_products null.
Do NOT invent or copy a ProductName for these — the product is already in
CURRENT STATE and the MERGE RULE in STEP 4 attaches the fields to it.

EXCEPTION: Use bulk_products when the message involves 2+ different products, the
same product split across different conditions, or a single product supplied with
ALL of its details at once (see SINGLE PRODUCT FULL DETAILS in STEP 3). The
difference from the MULTI-FIELD RULE above is whether the message NAMES a product:
if it names one, it can start a bulk entry; if it names none, the fields belong to
the product already under discussion and stay at the top level.

ONE-FIELD EXAMPLES (the most common inputs — NEVER return all-nulls for these):
User: "Foot Cream" → ProductName="Foot Cream", everything else null
User: "marine cream" → ProductName="marine cream", everything else null
User: "3" → Quantity="3", everything else null
User: "used" → Condition="used", everything else null
A bare product name in answer to a product question is ALWAYS an extraction.

COMBINED-ANSWER EXAMPLES (answering one question that asked for two fields):
User: "1, new" → Quantity="1", Condition="new", everything else null
User: "2 used" → Quantity="2", Condition="used", everything else null
User: "3, they are damaged" → Quantity="3", Condition="damaged", everything else null
User: "just 1 and it's still sealed" → Quantity="1", Condition="new", everything else null
These are the product already under discussion. NEVER return all-nulls for them,
never route them to bulk_products, and never attach a ProductName they did not say.
Contrast — these DO use bulk_products, because they split across conditions:
User: "1 new and 1 used" → two bulk_products entries, product_name null in both

ProductName: Product noun only. Strip filler words: product, item, unit, thing, units.
  EXTRACT ONLY FROM THE CURRENT USER MESSAGE. Never take a product name from
  the conversation history, from the customer's opening request, or from the
  reason-for-return description. Those mention products the customer has NOT
  yet been asked to confirm, and using them puts a product on the return that
  the customer never listed.
  If the current message names a product, use THAT name — even when it differs
  from a product mentioned earlier in the conversation.
  [D15] If your previous question asked what the customer ORDERED or EXPECTED
  instead, the product they name in reply is the EXPECTED item — set
  ExpectedProductName and leave ProductName null. It is NOT a product being
  returned: the customer never received it, so it must never become a new entry.
  If confirmation only (yes/ok/sure/correct) → null.
  If "that's all", "only X", "no more", "done", "nope", "nothing else" → ProductName="EXIT_SIGNAL"

Quantity: Integer 1–999 as string.
  An exact count is REQUIRED to process a return. If the user does not know
  the quantity, do NOT guess and do NOT use any placeholder value — set
  Quantity to null and politely explain that an exact count is needed; they
  can check the package and tell you, or say "that's all" to finish with only
  the products already provided.
  NEVER use the Target Quantity as a product Quantity — they are different things.

Condition: Apply mapping from STEP 1.
  EXTRACT ONLY FROM THE CURRENT USER MESSAGE. Do NOT infer a condition from
  the customer's opening request or the reason-for-return description — for
  example "after trying them out" or "did not meet expectations" earlier in the
  conversation must NOT become a condition. Wait until the customer states the
  condition in answer to the condition question, and return null until then.
  A condition phrase applies to ALL products mentioned in the same message
  unless a product has its own specific condition.

ExpectedProductName: What the customer ordered/expected instead — the item they
  should have received. Set it whenever your previous question asked what they
  ordered instead, EVEN THOUGH this message contains no condition. Do not wait
  for Condition="wrong product" to appear in the same message: it never does,
  because the condition was given on an earlier turn.
  Example — Bot: "What did you order instead of the Elemis body oil?"
            User: "Elemis body scrub"
            → ExpectedProductName="Elemis body scrub", ProductName null
━━━━━━━━━━━━━━━━━━━━
STEP 3 — BULK EXTRACTION FORMAT
━━━━━━━━━━━━━━━━━━━━
Use bulk_products for multiple products OR split conditions.
CRITICAL: Always start index at 0 — the postprocessor handles real positioning.

{"bulk_products": [
  {"index":0,"product_name":"...","quantity":"...","condition":"...","expected_product_name":null},
  {"index":1,"product_name":"...","quantity":"...","condition":"...","expected_product_name":null}
]}

SHARED CONDITION EXAMPLE:
User: "2 procollagen cream and 1 vitamin c serum, arrived late, no longer need"
→ Both products get condition: "new"

SPLIT CONDITION EXAMPLE:
User: "1 new and 1 used cleanse"
→ Two entries, same product_name "cleanse", different conditions

FULL DETAILS IN ONE MESSAGE EXAMPLE:
User: "marine cream qty 1 new and cleanser qty 1 used"
→ Two entries with all fields filled

SINGLE PRODUCT FULL DETAILS:
User: "1 marine cream new"
→ [{"index":0,"product_name":"marine cream","quantity":"1","condition":"new","expected_product_name":null}]
━━━━━━━━━━━━━━━━━━━━
STEP 4 — DECIDE conv_status (do this EVERY turn, AFTER extraction)
━━━━━━━━━━━━━━━━━━━━
MERGE RULE (critical):
Values you extract from THIS message FILL the incomplete products in
CURRENT STATE — they do not create duplicates.
- If CURRENT STATE has a product missing its name or condition, and your
  extraction provides the name/condition/quantity for that same product,
  that product is now COMPLETE. Do NOT count its quantity twice.
- Only count a quantity as NEW if it belongs to a product not already
  represented in CURRENT STATE.

Then compute:
  TotalQuantity = sum of quantities in CURRENT STATE
                + quantities of genuinely NEW products from this message.

Set conv_status to "ended" when ANY of these is true:
  1. TotalQuantity is greater than or equal to Target Quantity, AND (after
     applying the MERGE RULE) every product has a product_name and a
     condition, AND every product with condition "wrong product" has an
     expected_product_name.
  2. Quantity still needed is 0 AND every product in CURRENT STATE already
     has a product_name and condition (and expected_product_name where
     condition is "wrong product") — end immediately, even if you extracted
     nothing this turn.
  3. You extracted ProductName="EXIT_SIGNAL" (user said that's all / no
     more / done).

When conv_status is "ended" → bot is exactly:
"I have collected all the return details. Please confirm if everything looks correct."

Otherwise conv_status is "ongoing" → continue to STEP 5.
━━━━━━━━━━━━━━━━━━━━
STEP 5 — ASK NEXT MISSING FIELD
━━━━━━━━━━━━━━━━━━━━
Never confirm or summarize what was captured. Never ask user to verify.
Look at CURRENT STATE products array plus what you just extracted.
Find the first product missing a field.

ASK ONLY FOR FIELDS THAT ARE STILL MISSING. Before asking anything, check
CURRENT STATE plus what you extracted THIS turn. Never ask for a field that is
already filled — if the customer supplied quantity or condition themselves, that
field is done, no matter which question they were answering at the time.

QUESTION PRIORITY ORDER — take the FIRST branch that applies, and use the
wording given. Substitute the real product name for &lt;ProductName&gt;.

1. ProductName missing:
   "Thanks. Please tell me the name of the product you are returning."

2. Condition="wrong product" and ExpectedProductName missing:
   "Thanks. What product did you expect to receive instead?"

3. Quantity AND Condition both missing:
   "Thanks. How many of the &lt;ProductName&gt; are you returning, and what condition
    are they in? You can say new, used, damaged, or wrong product."
   NOTE (measured 2026-08-26, 8 live runs): when Target Quantity is 1 the model
   asks branch 5 instead, treating the single-item total as the quantity. An
   explicit instruction here NOT to do that was tried and had no effect, so it
   was removed rather than left as dead text. Harmless — the customer is still
   asked for the quantity on the following turn (branch 4) — but it means the
   combined question is not guaranteed on single-item returns.

4. Only Quantity missing:
   "Thanks. How many of the &lt;ProductName&gt; are you returning? Please reply with
    just the number."

5. Only Condition missing:
   "Thanks. What condition is the &lt;ProductName&gt; in? You can say new, used,
    damaged, or wrong product."

Never offer a condition option outside these four: new, used, damaged, wrong
product. Do not suggest "arrived late", "never delivered", "missing parts" or
any other phrase as an option — they cannot be recorded.

When a product is complete and more quantity is still needed:
"Got it. Please provide the name of the next product."
━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (STRICT)
━━━━━━━━━━━━━━━━━━━━
Return ONLY a valid JSON object, nothing else:
{"bot": "your message here", "conv_status": "ongoing or ended", "entities": {"ProductName": "value or null", "Quantity": "value or null", "Condition": "value or null", "ExpectedProductName": "value or null", "bulk_products": "array or null"}}

The "bot" field must NEVER be empty.
Never use empty string "" for entity values. Always use null.
The entities block is always present.
ALWAYS return the ACTUAL extracted values — never placeholders.

```

## generativeAI.preProcessorScript
```
try {
    context.session = context.session || {};
    context.entities = context.entities || {};
    var s = context.session.BotUserSession = context.session.BotUserSession || {};

    // Clear stale per-node signals from any previous agent node
    if (context.AI_Assisted_Dialogs) {
        delete context.AI_Assisted_Dialogs.exit_scenario;
        delete context.AI_Assisted_Dialogs.bot_response;
    }

    if (!s._returnDetailsInitialized) {
        s.ProductCount = parseInt(s.ProductCount || context.entities.ProductCount || 1);
        s.remainingQuantity = s.ProductCount;
        if (Array.isArray(s.products) && s.products.length > 0) {
            s.products = s.products.map(function(p) {
                return {
                    product_name: p.product_name || null,
                    quantity: p.quantity || null,
                    condition: p.condition || null,
                    expected_product_name: p.expected_product_name || null
                };
            });
            koreDebugger.log("PRE | Ported " + s.products.length + " products from prompt node");
        } else {
            s.products = [];
            koreDebugger.log("PRE | Starting fresh");
        }

        s._returnDetailsInitialized = true;
        // [A4 Stale-Zero] First invocation of this node fires on the transition,
        // so User_Input is the PREVIOUS node's answer (e.g. a phone number or
        // count). Mark this turn so the post-processor discards any extraction
        // from that stale input instead of relying on the model to ignore it.
        s._bootstrapTurn = true;
        koreDebugger.log("PRE | INITIALIZED: ProductCount=" + s.ProductCount);
    } else {
        s._bootstrapTurn = false;
    }

    // Clear per-turn extraction slots
    context.entities.ProductName = null;
    context.entities.Quantity = null;
    context.entities.Condition = null;
    context.entities.ExpectedProductName = null;
    context.entities.bulk_products = null;

} catch (e) {
    koreDebugger.log("PRE | ERROR: " + e.message);
}

```

## generativeAI.postProcessorScript
```
try {
    var node = context.currentNodeName;
    var aiData = context.AI_Assisted_Dialogs && context.AI_Assisted_Dialogs[node];

    koreDebugger.log("POST | pipeline check — aiData present: " + !!aiData +
                     " | entities present: " + !!(aiData && aiData.entities) +
                     " | raw conv_status: " + (aiData ? aiData.conv_status : "n/a"));

    if (aiData) {
        // [A1 Mangled-Status] Platform rewrites conv_status; never trust it.
        var llmReportedStatus = aiData.conv_status;
        aiData.conv_status = "ongoing";

        var ent = aiData.entities || {};
        if (Array.isArray(ent)) ent = ent[0] || {};

        context.session = context.session || {};
        context.entities = context.entities || {};
        var s = context.session.BotUserSession = context.session.BotUserSession || {};

        if (!Array.isArray(s.products)) s.products = [];
        if (!Array.isArray(s.conversationHistory)) s.conversationHistory = [];
        // [D2] Provenance runs parallel to products so it never leaks into the
        // CURRENT STATE blob injected into the prompt.
        if (!Array.isArray(s._provenance)) s._provenance = [];

        var maxProducts = parseInt(s.ProductCount) || parseInt(context.entities.ProductCount) || 1;

        function isEmpty(val) {
            return !val || String(val).trim() === "" || val === "null" || val === "undefined";
        }

        function sanitize(name) {
            if (!name) return name;
            var n = String(name).trim();
            n = n.replace(/\b(product|products|item|items|unit|units|thing|things)\b/gi, "").trim();
            n = n.replace(/\s+/g, " ");
            return n;
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
            "cancel your", "cancel their", "cancel it", "cancel a ",
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

        var isExcluded = exclusionPhrases.some(function(p) { return lastUserMsg.indexOf(p) !== -1; });
        var isPureExit = pureExitPhrases.some(function(p) { return lastUserMsg.indexOf(p) !== -1; });
        if (!isPureExit && !isExcluded) {
            isPureExit = pureExitWords.some(function(w) { return matchesWordBoundary(w, lastUserMsg); });
        }

        if (lastUserMsg === "") {
            koreDebugger.log("POST | WARN: exit-check input EMPTY — phrase tripwire BLIND this turn");
        }

        var isExitSignal = (ent.ProductName === "EXIT_SIGNAL");

        // [A4 Stale-Zero] Bootstrap turn = node's first invocation; User_Input is
        // the PREVIOUS node's answer. We no longer discard it (that lost whole
        // product lists — TC-04/TC-16); instead everything captured on this turn
        // is marked INFERRED so a later stated value can correct it.
        var isBootstrapTurn = (s._bootstrapTurn === true);
        if (isBootstrapTurn) s._bootstrapTurn = false; // pre-processor runs once per node entry

        // ================================================================
        // [D2] PROVENANCE — "stated beats inferred"
        // ================================================================
        // The model frequently derives values from the intent utterance or
        // conversation history rather than the current message (observed:
        // product name "scarf" from the opening line; condition "used" from
        // "after trying them out"). Those guesses used to land first and could
        // never be corrected, because writes were guarded by isEmpty().
        // Now every write records whether the value was STATED by the customer
        // in THIS message or INFERRED from elsewhere, and a stated value is
        // allowed to overwrite an inferred one.
        var CONDITION_SYNONYMS = {
            "new": ["new", "unopened", "sealed", "unused", "never opened", "never used",
                    "not opened", "arrived late", "no longer need", "don't need",
                    "dont need", "changed mind", "brand new"],
            "used": ["used", "tried", "opened", "tested", "partially used", "use it"],
            "damaged": ["damaged", "broken", "defective", "not working", "stopped working",
                        "cracked", "faulty", "missing"],
            "wrong product": ["wrong", "not what i ordered", "received wrong",
                              "different product", "sent wrong", "incorrect"]
        };
        var NUMBER_WORDS = {1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",
                            7:"seven",8:"eight",9:"nine",10:"ten"};

        function normalizeText(str) {
            return String(str || "").toLowerCase()
                     .replace(/[^a-z0-9 ]/g, " ")
                     .replace(/\s+/g, " ").trim();
        }

        // Did the customer actually say this value in the current message?
        function statedByUser(kind, value) {
            var msg = normalizeText(lastUserMsg);
            var val = normalizeText(value);
            if (msg === "" || val === "") return false;

            if (kind === "condition") {
                var syns = CONDITION_SYNONYMS[String(value).toLowerCase().trim()] || [value];
                return syns.some(function(w) { return msg.indexOf(normalizeText(w)) !== -1; });
            }
            if (kind === "quantity") {
                var n = Number(value);
                if (isNaN(n)) return false;
                if (msg.indexOf(String(n)) !== -1) return true;
                return !!(NUMBER_WORDS[n] && msg.indexOf(NUMBER_WORDS[n]) !== -1);
            }
            // names: any distinctive token present is enough ("foot cream" vs "cream")
            var tokens = val.split(" ").filter(function(t) { return t.length >= 3; });
            if (tokens.length === 0) return msg.indexOf(val) !== -1;
            return tokens.some(function(t) { return msg.indexOf(t) !== -1; });
        }

        function provFor(idx) {
            while (s._provenance.length <= idx) s._provenance.push({});
            return s._provenance[idx];
        }

        /**
         * Write a field with provenance rules.
         *  - empty slot field           → write
         *  - existing INFERRED + STATED → overwrite (the correction we were missing)
         *  - otherwise                  → keep
         */
        function writeField(idx, field, value, kind) {
            var slot = s.products[idx];
            var prov = provFor(idx);
            // [D14] Provenance is decided by whether the customer actually said the
            // value, on the bootstrap turn as much as any other. The old rule forced
            // "inferred" for EVERYTHING captured on the bootstrap turn, which is wrong
            // whenever that turn's input is the customer's own product list: answering
            // the count question with "2 damaged gels and 1 new cream" states both
            // conditions plainly, yet both were marked inferred, both were challenged,
            // allFields went false, the node refused to finish, and the platform
            // force-exited it — shipping a correct ticket stamped partial_review with
            // the confirmation question never asked (dev app trace 2026-08-13, PT-2).
            // The blanket rule was A4's blunt instrument; the dangerous bootstrap cases
            // are now covered precisely by the L1 quantity bleed guard and the D13
            // condition bleed guard, so statedByUser can be trusted on its own.
            var src = statedByUser(kind, value) ? "stated" : "inferred";
            var current = slot[field];

            if (isEmpty(current)) {
                slot[field] = value;
                prov[field] = src;
                return true;
            }
            if (String(current) === String(value)) {
                if (src === "stated") prov[field] = "stated"; // confirmed by the customer
                return false;
            }
            if (prov[field] !== "stated" && src === "stated") {
                koreDebugger.log("POST | CORRECTION [" + idx + "." + field + "] inferred '" +
                                 current + "' → stated '" + value + "'");
                slot[field] = value;
                prov[field] = src;
                return true;
            }
            koreDebugger.log("POST | KEPT [" + idx + "." + field + "] '" + current +
                             "' (" + (prov[field] || "unknown") + ") over '" + value + "' (" + src + ")");
            return false;
        }

        function newSlot() {
            s.products.push({product_name: null, quantity: null, condition: null, expected_product_name: null});
            s._provenance.push({});
            return s.products.length - 1;
        }

        function validCondition(v) {
            var c = String(v).toLowerCase().trim();
            return ["new", "used", "damaged", "wrong product"].indexOf(c) !== -1 ? c : null;
        }

        function validQuantity(v) {
            var n = Number(v);
            if (isNaN(n) || n <= 0 || n > 999) return null;
            return String(n);
        }

        // [D7] EXIT_SIGNAL on an empty basket ends the node with nothing (TC-04:
        // the bot offered "say that's all" before any product existed, and the
        // customer's compliance produced an empty ticket). Never honour it until
        // at least one product has been captured.
        if (isExitSignal && s.products.length === 0) {
            koreDebugger.log("POST | EXIT_SIGNAL IGNORED — no products captured yet (D7 guard)");
            isExitSignal = false;
            s._exitSignalSuppressed = true;
        }

        // [D7b] "That's all" while a product is still missing a field means the
        // customer believes their list is complete when it is not — the missing
        // product would be dropped by the downstream completeness guard without
        // anyone telling them. Ask once for the gap; if they say it again, honour
        // it and let the partial flags carry the truth. (Observed live: "that's
        // all" with 'long inserts' still lacking a quantity.)
        if (isExitSignal && s.products.length > 0 && !s._exitChallenged) {
            var incompleteNames = [];
            for (var qi = 0; qi < s.products.length; qi++) {
                var qp = s.products[qi];
                if (isEmpty(qp.product_name) || isEmpty(qp.quantity) || isEmpty(qp.condition) ||
                    (qp.condition === "wrong product" && isEmpty(qp.expected_product_name))) {
                    incompleteNames.push(qp.product_name || "an unnamed product");
                }
            }
            if (incompleteNames.length > 0) {
                s._exitChallenged = true;
                s._exitChallengeNames = incompleteNames.join(", ");
                isExitSignal = false;
                s._exitSignalSuppressed = true;
                koreDebugger.log("POST | EXIT_SIGNAL CHALLENGED — incomplete: " + s._exitChallengeNames);
            }
        }

        // [B3 Double-Speak detector]
        if (ent.bulk_products && Array.isArray(ent.bulk_products) && ent.bulk_products.length > 0) {
            var b0 = ent.bulk_products[0] || {};
            var dsMismatch = [];
            if (!isEmpty(ent.ProductName) && !isEmpty(b0.product_name) &&
                String(ent.ProductName).toLowerCase().trim() !== String(b0.product_name).toLowerCase().trim()) dsMismatch.push("ProductName");
            if (!isEmpty(ent.Quantity) && !isEmpty(b0.quantity) &&
                String(ent.Quantity).trim() !== String(b0.quantity).trim()) dsMismatch.push("Quantity");
            if (!isEmpty(ent.Condition) && !isEmpty(b0.condition) &&
                String(ent.Condition).toLowerCase().trim() !== String(b0.condition).toLowerCase().trim()) dsMismatch.push("Condition");
            if (dsMismatch.length) {
                koreDebugger.log("POST | WARN Double-Speak MISMATCH (singles vs bulk[0]) on: " + dsMismatch.join(", "));
            }
        }

        koreDebugger.log("POST | ent=" + JSON.stringify(ent) +
                         " | isBootstrap: " + isBootstrapTurn +
                         " | isPureExit: " + isPureExit +
                         " | isExitSignal: " + isExitSignal +
                         " | products.length=" + s.products.length);

        // [D13 Phantom-Condition] The bootstrap turn's User_Input is the PREVIOUS
        // node's answer, so a Condition arriving with no product attached was never
        // stated about anything — the model inferred it from the intent utterance
        // sitting in history ("i want to return 4 product with the condition new",
        // dev ticket #7153; measured 10/10 live runs). Left alone it seeds a
        // NAMELESS slot, which the next turn's product name then adopts, so the
        // first product carries a condition before the customer was ever asked.
        // D2's correction only rescues that when the customer's wording is
        // recognised by CONDITION_SYNONYMS — a typo loses to the phantom.
        // Same shape as the L1 quantity bleed guard. A condition that DOES arrive
        // with a product name (a list given at the count step — TC-04/TC-16) is
        // about a product the customer really named, so it is kept.
        if (isBootstrapTurn && !isEmpty(ent.Condition) && isEmpty(ent.ProductName) &&
            !(ent.bulk_products && Array.isArray(ent.bulk_products) && ent.bulk_products.length > 0)) {
            koreDebugger.log("POST | Condition '" + ent.Condition +
                             "' REJECTED — bleed guard (bootstrap turn, no product named)");
            ent.Condition = null;
        }

        // ================================================================
        // ENTITY CAPTURE
        // ================================================================
        if (!isPureExit && !isExitSignal) {

            // ── BULK ──
            if (ent.bulk_products && Array.isArray(ent.bulk_products) && ent.bulk_products.length > 0) {

                var bulk = ent.bulk_products;
                var claimed = {}; // slots already taken by THIS bulk batch

                for (var b = 0; b < bulk.length; b++) {
                    var bp = bulk[b] || {};
                    var bpName = isEmpty(bp.product_name) ? null : sanitize(String(bp.product_name).trim());
                    if (bpName !== null && (bpName === "" || /^\d+$/.test(bpName))) bpName = null;

                    // Target slot: prefer an existing slot with the same name, else
                    // the first incomplete slot, else a new one. Each entry in this
                    // batch claims a distinct slot — several entries collapsing onto
                    // one slot is how multi-product messages used to lose products.
                    var tIdx = -1;
                    if (bpName) {
                        tIdx = s.products.findIndex(function(p, pi) {
                            return !claimed[pi] && !isEmpty(p.product_name) &&
                                   normalizeText(p.product_name) === normalizeText(bpName) &&
                                   (isEmpty(p.quantity) || isEmpty(p.condition));
                        });
                    }
                    if (tIdx === -1) {
                        tIdx = s.products.findIndex(function(p, pi) {
                            if (claimed[pi]) return false;
                            var prov = s._provenance[pi] || {};
                            // an incomplete slot, or one whose name is only inferred
                            return isEmpty(p.product_name) || isEmpty(p.quantity) ||
                                   isEmpty(p.condition) || prov.product_name === "inferred";
                        });
                    }
                    if (tIdx === -1) tIdx = newSlot();
                    claimed[tIdx] = true;

                    if (bpName) writeField(tIdx, "product_name", bpName, "name");

                    var bQty = validQuantity(bp.quantity);
                    if (bQty) writeField(tIdx, "quantity", bQty, "quantity");
                    else if (!isEmpty(bp.quantity)) {
                        koreDebugger.log("POST | WARN: bulk quantity '" + bp.quantity + "' rejected");
                    }

                    var bCond = isEmpty(bp.condition) ? null : validCondition(bp.condition);
                    if (bCond) writeField(tIdx, "condition", bCond, "condition");

                    if (!isEmpty(bp.expected_product_name)) {
                        var expB = sanitize(String(bp.expected_product_name).trim());
                        if (expB !== "") writeField(tIdx, "expected_product_name",
                            bp.expected_product_name === "UNKNOWN" ? "UNKNOWN" : expB, "name");
                    }
                }
                koreDebugger.log("POST | Bulk processed (" + bulk.length + " entries)");

            // ── SINGLE ──
            } else {

                var cIdx = s.products.findIndex(function(p) { return isEmpty(p.quantity); });
                if (cIdx === -1) cIdx = s.products.findIndex(function(p) { return isEmpty(p.product_name); });
                if (cIdx === -1) cIdx = s.products.findIndex(function(p) { return isEmpty(p.condition); });
                // [D16] Only route to a wrong-product slot when THIS turn actually
                // carries an expected product name. The gap is otherwise unfillable,
                // and an unfillable gap matches on every later turn — pinning cIdx
                // here forever. Every subsequent answer then lands on this slot and
                // is (correctly) refused by the provenance guard, so the customer's
                // NEXT product is silently discarded and the node burns turns until
                // the platform force-exits it. Measured on the 2026-08-26 ticket:
                // "Elemis body mask" lost entirely, ticket shipped with 2 of 3
                // products. See tests/expected_name_traps_slot.json.
                if (cIdx === -1 && !isEmpty(ent.ExpectedProductName)) {
                    cIdx = s.products.findIndex(function(p) {
                        return p.condition === "wrong product" && isEmpty(p.expected_product_name);
                    });
                }
                // [D2] A field filled only by inference is still open for correction —
                // without this the customer's answer has nowhere to land and is dropped.
                if (cIdx === -1 && !isEmpty(ent.Condition)) {
                    cIdx = s.products.findIndex(function(p, pi) {
                        return (s._provenance[pi] || {}).condition === "inferred";
                    });
                }
                if (cIdx === -1 && !isEmpty(ent.ProductName)) {
                    cIdx = s.products.findIndex(function(p, pi) {
                        return (s._provenance[pi] || {}).product_name === "inferred";
                    });
                }

                var somethingExtracted = !isEmpty(ent.ProductName) || !isEmpty(ent.Quantity) ||
                                         !isEmpty(ent.Condition) || !isEmpty(ent.ExpectedProductName);

                if (cIdx === -1 && somethingExtracted) {
                    var totalFilled = 0;
                    for (var x = 0; x < s.products.length; x++) {
                        if (!isEmpty(s.products[x].quantity)) totalFilled += parseInt(s.products[x].quantity) || 0;
                    }
                    if (totalFilled < maxProducts) {
                        cIdx = newSlot();
                        koreDebugger.log("POST | New slot appended at index " + cIdx);
                    }
                }

                // [D17] NEVER DROP A NAMED PRODUCT. D8/D9 claimed this guarantee but
                // the code never had it: if the routed slot already holds a DIFFERENT
                // name the customer stated, writeField refuses the write (correctly —
                // stated must not clobber stated) and the new product is discarded
                // with only a KEPT line to show for it. A differing stated name is a
                // NEW product, not a correction, so give it its own slot.
                // No maxProducts cap here on purpose: overshoot is recorded via
                // countMismatch, never by silently deleting what the customer said.
                if (cIdx !== -1 && !isEmpty(ent.ProductName) && ent.ProductName !== "EXIT_SIGNAL") {
                    var incName = sanitize(String(ent.ProductName).trim());
                    var routedSlot = s.products[cIdx];
                    var routedProv = s._provenance[cIdx] || {};
                    if (incName !== "" && !/^\d+$/.test(incName) &&
                        !isEmpty(routedSlot.product_name) &&
                        routedProv.product_name === "stated" &&
                        normalizeText(routedSlot.product_name) !== normalizeText(incName)) {
                        koreDebugger.log("POST | NEW PRODUCT '" + incName + "' would have been discarded on slot " +
                                         cIdx + " ('" + routedSlot.product_name + "') — allocating its own slot");
                        cIdx = newSlot();
                    }
                }

                if (cIdx === -1) {
                    koreDebugger.log("POST | No incomplete slot — skipping");
                } else {
                    // name first so the bleed guard sees the right context
                    if (!isEmpty(ent.ProductName) && ent.ProductName !== "EXIT_SIGNAL") {
                        var pnS = sanitize(String(ent.ProductName).trim());
                        if (pnS !== "" && !/^\d+$/.test(pnS)) {
                            writeField(cIdx, "product_name",
                                ent.ProductName === "UNKNOWN" ? "UNKNOWN" : pnS, "name");
                        }
                    }

                    if (!isEmpty(ent.Quantity)) {
                        var qtyS = validQuantity(ent.Quantity);
                        if (qtyS === null) {
                            koreDebugger.log("POST | WARN: Quantity '" + ent.Quantity + "' rejected (non-numeric/out of range)");
                        } else {
                            // Bleed guard: a quantity equal to the target, on a nameless
                            // slot, that the customer never actually said, is the
                            // ProductCount leaking in. On the bootstrap turn the input
                            // IS the count answer, so it never counts as "stated".
                            // Bleed guard. On the BOOTSTRAP turn the input is the
                            // previous node's answer (the item count), so a quantity
                            // with no product name attached is never a real product
                            // quantity — reject it regardless of value. Observed live:
                            // seed "8" with a stale ProductCount of 6 slipped past the
                            // old equality check, created a nameless slot holding 8,
                            // and the next bulk entry inherited it (short inserts = 8
                            // when the customer said 4).
                            var namelessSlot = isEmpty(s.products[cIdx].product_name);
                            var bleed = (isBootstrapTurn && namelessSlot) ||
                                        (Number(qtyS) === maxProducts && namelessSlot &&
                                         !statedByUser("quantity", qtyS));
                            if (bleed) {
                                koreDebugger.log("POST | Quantity '" + qtyS + "' REJECTED — bleed guard (" +
                                                 (isBootstrapTurn ? "bootstrap turn, no product name" : "equals ProductCount") + ")");
                            } else {
                                writeField(cIdx, "quantity", qtyS, "quantity");
                            }
                        }
                    }

                    if (!isEmpty(ent.Condition)) {
                        var condS = validCondition(ent.Condition);
                        if (condS) {
                            writeField(cIdx, "condition", condS, "condition");

                            // [D11] A single condition answer covers every product still
                            // awaiting one ("they're all new" — TC-15/TC-16). Only applies
                            // when the customer stated it in this message.
                            if (statedByUser("condition", condS)) {
                                for (var sc = 0; sc < s.products.length; sc++) {
                                    if (sc !== cIdx && isEmpty(s.products[sc].condition)) {
                                        writeField(sc, "condition", condS, "condition");
                                        koreDebugger.log("POST | Shared condition '" + condS + "' applied to slot " + sc);
                                    }
                                }
                            }
                        }
                    }

                    if (!isEmpty(ent.ExpectedProductName)) {
                        var exp = sanitize(String(ent.ExpectedProductName).trim());
                        if (exp !== "") {
                            var wpTarget = s.products.findIndex(function(p) {
                                return p.condition === "wrong product" && isEmpty(p.expected_product_name);
                            });
                            if (wpTarget === -1) wpTarget = cIdx;
                            writeField(wpTarget, "expected_product_name",
                                ent.ExpectedProductName === "UNKNOWN" ? "UNKNOWN" : exp, "name");
                        }
                    }
                }
            }
        }

        // ================================================================
        // [D18] ENTITY WRITE-BACK — Ghost-Referee starvation
        // ================================================================
        // The platform tracks whether a turn "identified an entity value" using
        // its OWN configured entity list (ProductName, Quantity, Condition), and
        // it force-exits the node to Fallback Behavior after consecutive turns
        // where nothing is identified (behaviour #3). pre.js nulls all five
        // context.entities every turn and NOTHING ever wrote them back — so from
        // the platform's point of view this node may never identify anything.
        //
        // Observed 2026-08-26: force-exit (platform_fallback → partial_review)
        // on the turn whose only extraction was ExpectedProductName, with both
        // the model and this script reporting "ongoing". Before D15 the model
        // wrongly returned that answer as ProductName, which fed the tracker and
        // accidentally kept the node alive — fixing D15 removed the crutch.
        //
        // Mirror what we accepted so the platform sees what the node sees.
        // NOTE: ExpectedProductName must also be added to the node's Entities
        // list in the platform UI, or the platform ignores the key entirely.
        try {
            var wroteBack = [];
            var bp0 = (ent.bulk_products && Array.isArray(ent.bulk_products) && ent.bulk_products.length > 0)
                      ? (ent.bulk_products[0] || {}) : {};

            var wbName = !isEmpty(ent.ProductName) && ent.ProductName !== "EXIT_SIGNAL"
                         ? sanitize(String(ent.ProductName).trim())
                         : (!isEmpty(bp0.product_name) ? sanitize(String(bp0.product_name).trim()) : null);
            if (wbName && wbName !== "" && !/^\d+$/.test(wbName)) {
                context.entities.ProductName = wbName; wroteBack.push("ProductName");
            }

            var wbQty = validQuantity(!isEmpty(ent.Quantity) ? ent.Quantity : bp0.quantity);
            if (wbQty) { context.entities.Quantity = wbQty; wroteBack.push("Quantity"); }

            var wbCond = validCondition(!isEmpty(ent.Condition) ? ent.Condition : bp0.condition);
            if (wbCond) { context.entities.Condition = wbCond; wroteBack.push("Condition"); }

            var wbExp = !isEmpty(ent.ExpectedProductName) ? ent.ExpectedProductName : bp0.expected_product_name;
            if (!isEmpty(wbExp)) {
                context.entities.ExpectedProductName = sanitize(String(wbExp).trim());
                wroteBack.push("ExpectedProductName");
            }

            koreDebugger.log("POST | Entity write-back: " +
                             (wroteBack.length ? wroteBack.join(", ") : "NOTHING — platform sees no entity this turn"));
        } catch (eWB) {
            koreDebugger.log("POST | Entity write-back ERROR: " + eWB.message);
        }

        // ================================================================
        // TOTALS & COMPLETION
        // ================================================================
        function recomputeTotal() {
            var t = 0;
            for (var i = 0; i < s.products.length; i++) {
                if (!isEmpty(s.products[i].quantity)) t += parseInt(s.products[i].quantity) || 0;
            }
            return t;
        }

        // [D9] Only drop slots that are COMPLETELY empty. A product the customer
        // named is never discarded, even when the total overshoots the target
        // (TC-09 silently dropped MuscleEase Oil this way).
        var beforePrune = s.products.length;
        var keptProducts = [];
        var keptProv = [];
        for (var pi = 0; pi < s.products.length; pi++) {
            var p = s.products[pi];
            var blank = isEmpty(p.product_name) && isEmpty(p.quantity) &&
                        isEmpty(p.condition) && isEmpty(p.expected_product_name);
            if (!blank) {
                keptProducts.push(p);
                keptProv.push(s._provenance[pi] || {});
            }
        }
        s.products = keptProducts;
        s._provenance = keptProv;
        if (s.products.length !== beforePrune) {
            koreDebugger.log("POST | Pruned " + (beforePrune - s.products.length) + " empty slot(s)");
        }

        var totalQuantity = recomputeTotal();

        context.entities.ProductsCollected = totalQuantity;
        s.ProductsCollected = totalQuantity;
        s.remainingQuantity = Math.max(0, maxProducts - totalQuantity);

        // [D8] Record the count/collected relationship instead of silently
        // reshaping data to match the target.
        s.countMismatch = (totalQuantity !== maxProducts);
        if (totalQuantity > maxProducts) {
            koreDebugger.log("POST | NOTE: collected " + totalQuantity + " exceeds target " +
                             maxProducts + " — keeping all products, flagged for review");
        }

        var baseComplete = s.products.length > 0 && s.products.every(function(p) {
            if (isEmpty(p.product_name)) return false;
            if (isEmpty(p.quantity)) return false;
            if (isEmpty(p.condition)) return false;
            if (p.condition === "wrong product") return !isEmpty(p.expected_product_name);
            return true;
        });

        // [D2] A condition the model INFERRED (from the opening narrative or
        // history) must not silently complete a product — that is exactly how
        // TC-06/TC-12 shipped 'used' for goods the customer called 'New': the
        // inferred value filled the slot, the node declared itself done, and the
        // condition question was never asked. At the moment collection would
        // otherwise finish, we challenge inferred conditions ONCE, forcing the
        // question. If the reply still yields nothing stated, the inferred value
        // is accepted rather than looping forever.
        var challengedThisTurn = false;
        if (baseComplete && totalQuantity >= maxProducts) {
            for (var ci = 0; ci < s.products.length; ci++) {
                var cprov = s._provenance[ci] || {};
                if (cprov.condition === "inferred" && !cprov.conditionChallenged) {
                    cprov.conditionChallenged = true;
                    challengedThisTurn = true;
                    koreDebugger.log("POST | Condition on slot " + ci + " is INFERRED ('" +
                                     s.products[ci].condition + "') — confirming with the customer before finishing");
                }
            }
        }

        var allFieldsCaptured = baseComplete && !challengedThisTurn;

        var done = (totalQuantity >= maxProducts && allFieldsCaptured);
        var llmSaidEnded = (llmReportedStatus === "ended");

        // ---------- DECIDE ----------
        if (isPureExit) {
            s.exitReason = "exit_requested";
            s.agentNodeExitPath = "user_cancelled";
            context.entities.AllProductsCaptured = false;
            aiData.conv_status = "ended";
            aiData.bot = "Okay, cancelling this request.";
            koreDebugger.log("POST | EXIT requested → ending node");
        } else if (isExitSignal) {
            s.exitReason = null;
            context.entities.AllProductsCaptured = true;
            s.partialReturn = (totalQuantity < maxProducts);
            s.agentNodeExitPath = "thats_all";
            aiData.conv_status = "ended";
            aiData.bot = "I have collected all the return details. Please confirm if everything looks correct.";
            koreDebugger.log("POST | EXIT_SIGNAL → ending with " + totalQuantity + "/" + maxProducts);
        } else if (done) {
            s.exitReason = null;
            context.entities.AllProductsCaptured = true;
            s.partialReturn = false;
            s.agentNodeExitPath = "completed";
            aiData.conv_status = "ended";
            aiData.bot = "I have collected all the return details. Please confirm if everything looks correct.";
            koreDebugger.log("POST | COMPLETE — all products captured");
        } else {
            s.exitReason = null;
            context.entities.AllProductsCaptured = false;
            aiData.conv_status = "ongoing";
            if (llmSaidEnded) {
                koreDebugger.log("POST | VETO: LLM said ended but validation failed (qty " +
                                 totalQuantity + "/" + maxProducts + ", allFields=" + allFieldsCaptured + ")");
            }

            // [D7b] Ask for the gap the customer's "that's all" would have skipped.
            if (s._exitChallengeNames) {
                aiData.bot = "Before I submit this, I still need a few details for " +
                             s._exitChallengeNames +
                             ". Could you give me the missing quantity or condition? " +
                             "If you'd rather finish without it, just say \"that's all\" again.";
                s._exitChallengeNames = null;
                s._exitSignalSuppressed = false;
            } else if (s._exitSignalSuppressed) {
                // [D7] empty basket
                s._exitSignalSuppressed = false;
                aiData.bot = "Before I can submit this, I need the details of at least one product. " +
                             "Please tell me the name of the first product you are returning.";
            } else if (!aiData.bot || String(aiData.bot).trim() === "") {
                aiData.bot = "Could you tell me more about the products you'd like to return?";
            } else {
                // [VETO-MSG] The model frequently emits the completion message while
                // the JS validation is still refusing to end (observed live twice in
                // one session). Showing "I have collected all the return details"
                // during an ongoing collection tells the customer the opposite of
                // the truth, so replace it with the next real question.
                var lowerBot = String(aiData.bot).toLowerCase();
                if (lowerBot.indexOf("collected all the return details") !== -1) {
                    var gapName = null, gapField = null;
                    for (var gi = 0; gi < s.products.length && !gapField; gi++) {
                        var gp = s.products[gi];
                        if (isEmpty(gp.product_name)) { gapName = "this product"; gapField = "name"; }
                        else if (isEmpty(gp.quantity)) { gapName = gp.product_name; gapField = "quantity"; }
                        else if (isEmpty(gp.condition)) { gapName = gp.product_name; gapField = "condition"; }
                        else if (gp.condition === "wrong product" && isEmpty(gp.expected_product_name)) {
                            gapName = gp.product_name; gapField = "expected product";
                        }
                    }
                    if (gapField === "name") {
                        aiData.bot = "Please tell me the name of the product you are returning.";
                    } else if (gapField === "quantity") {
                        aiData.bot = "How many " + gapName + " are you returning? Please reply with just the number.";
                    } else if (gapField === "condition") {
                        aiData.bot = "What is the condition of the " + gapName +
                                     "? For example, new, used, damaged, or wrong product.";
                    } else if (gapField === "expected product") {
                        aiData.bot = "What was the product you actually ordered instead of the " + gapName + "?";
                    } else {
                        aiData.bot = "Please provide the name of the next product you are returning.";
                    }
                    koreDebugger.log("POST | VETO-MSG: replaced premature completion message with: " + aiData.bot);
                }
            }
        }

        koreDebugger.log("POST | TotalQty: " + totalQuantity + "/" + maxProducts +
                         " | allFields: " + allFieldsCaptured +
                         " | countMismatch: " + s.countMismatch +
                         " | products=" + JSON.stringify(s.products));

        // ---------- CONVERSATION HISTORY ----------
        appendConversationHistory();

        function appendConversationHistory() {
            var history = s.conversationHistory;
            var userMsg = "";
            try {
                userMsg = (
                    s.lastMessage &&
                    s.lastMessage.messagePayload &&
                    s.lastMessage.messagePayload.message &&
                    s.lastMessage.messagePayload.message.body
                ) || "";
                userMsg = String(userMsg).replace(/\n/g, " ").replace(/\s+/g, " ").trim();
            } catch (e) {}

            var botMsg = String(
                (context.AI_Assisted_Dialogs &&
                 context.AI_Assisted_Dialogs.bot_response &&
                 context.AI_Assisted_Dialogs.bot_response.bot) ||
                aiData.bot || ""
            ).replace(/\n/g, " ").replace(/\s+/g, " ").trim();

            var excludedBotMessages = [
                "i have collected all the return details. please confirm if everything looks correct."
            ];
            var lowerBotMsg = botMsg.toLowerCase().trim();
            var isExcludedBotMsg =
                botMsg && excludedBotMessages.some(function(phrase) {
                    return lowerBotMsg.indexOf(phrase) !== -1;
                });

            if (!s.agentNodeStarted) {
                s.agentNodeStarted = true;
                if (botMsg && !isExcludedBotMsg) {
                    history.push("<b>Marina :  </b>" + botMsg);
                }
                koreDebugger.log("POST | First turn — pushed Marina opening message only");
            } else {
                if (userMsg) history.push("<b>Customer :  </b>" + userMsg);
                if (botMsg && !isExcludedBotMsg) {
                    history.push("<b>Marina :  </b>" + botMsg);
                } else if (isExcludedBotMsg) {
                    koreDebugger.log("POST | Excluded bot message from history: " + botMsg);
                }
            }

            if (history.length > 20) history = history.slice(-20);
            s.conversationHistory = history;
            s.conversationHistoryString = history.join("<br>");

            koreDebugger.log("POST | ConversationHistory: " + s.conversationHistoryString);
        }

    } else {
        koreDebugger.log("POST: No AI data for node: " + node);
    }

} catch (e) {
    koreDebugger.log("POST | ERROR: " + e.message);
}

```
