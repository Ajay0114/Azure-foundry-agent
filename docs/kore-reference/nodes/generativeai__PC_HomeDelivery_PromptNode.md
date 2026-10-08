# PC_HomeDelivery_PromptNode  (generativeai)

## Config
```json
{
  "name": "PC_HomeDelivery_PromptNode",
  "type": "generativeai",
  "generativeAI": {
    "settings": {
      "enabled": true,
      "model": "gpt-5.1",
      "icon": "https://platform.kore.ai/assets/integrations/32/customllm.png",
      "displayName": "Azure-OpenAI-GPT5.1 - gpt-5.1",
      "integrationName": "Azure-OpenAI-GPT5.1",
      "temperature": 0.5,
      "max_tokens": 2500,
      "Noofprevioususerinputs": 5,
      "promptId": "d5db8780-9685-5da0-b491-b9cf2f5a3f2e",
      "promptName": "prompt_Node_GPT_5.1",
      "isCustom": true,
      "isSysIntAndCustomPrompt": false,
      "isStreaming": false,
      "validatePath": "choices[0].message.content",
      "promptFilterBasedOnModel": [
        {
          "name": "prompt_Node_GPT_5.1",
          "displayName": "Azure-OpenAI-GPT5.1-gpt-5.1",
          "featureKey": "generativeai",
          "featureName": "Prompt Node",
          "integration": "Azure-OpenAI-GPT5.1",
          "defaultModel": "gpt-5.1",
          "isDefault": false,
          "state": "configured",
          "status": 1,
          "configuration": {
            "scriptType": "JSON",
            "endPoint": {
              "host": "osw-openai4.cognitiveservices.azure.com",
              "path": "/openai/deployments/gpt-5.1/chat/completions?api-version=2024-12-01-preview",
              "protocol": "https:",
              "method": "POST"
            },
            "payloadFields": {
              "messages": [
                {
                  "role": "system"
                }
              ],
              "temperature": 0.1,
              "max_completion_tokens": 500,
              "top_p": 1
            },
            "parameters": [
              {
                "key": "User_Input",
                "value": "The latest input by the end-user.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History_String",
                "value": "This specifies the targeted Large Language Model for generating responses from the given request prompt.",
                "isMandatory": false
              },
              {
                "key": "Language",
                "value": "The language in which the LLM will respond to the users",
                "isMandatory": false
              },
              {
                "key": "Model",
                "value": "This specifies the targeted Large Language Model for generating responses from the given request prompt.",
                "isMandatory": false
              },
              {
                "key": "prompt",
                "isMandatory": true
              },
              {
                "key": "system_context",
                "value": "For the instructions that the user provides, the LLM should be able to process the instructions",
                "isMandatory": false
              }
            ],
            "headerFields": {
              "api-key": "<REDACTED>",
              "Content-Type": "application/json"
            },
            "sso_type": "none",
            "idp": "none",
            "timeout": 300000
          },
          "res": {
            "choices": [
              {
                "content_filter_results": {
                  "hate": {
                    "filtered": false,
                    "severity": "safe"
                  },
                  "protected_material_code": {
                    "detected": false,
                    "filtered": false
                  },
                  "protected_material_text": {
                    "detected": false,
                    "filtered": false
                  },
                  "self_harm": {
                    "filtered": false,
                    "severity": "safe"
                  },
                  "sexual": {
                    "filtered": false,
                    "severity": "safe"
                  },
                  "violence": {
                    "filtered": false,
                    "severity": "safe"
                  }
                },
                "finish_reason": "stop",
                "index": 0,
                "message": {
                  "role": "assistant"
                }
              }
            ],
            "created": 1778233098,
            "id": "chatcmpl-DdBwwdJ0O1FOZtRlf7705Ht8FRkrH",
            "model": "gpt-5.1-2025-11-13",
            "object": "chat.completion",
            "prompt_filter_results": [
              {
                "prompt_index": 0
              }
            ],
            "service_tier": "default",
            "usage": {
              "completion_tokens": 330,
              "completion_tokens_details": {
                "accepted_prediction_tokens": 0,
                "audio_tokens": 0,
                "reasoning_tokens": 0,
                "rejected_prediction_tokens": 0
              },
              "latency_checkpoint": {
                "engine_tbt_ms": 10,
                "engine_ttft_ms": 43,
                "engine_ttlt_ms": 3231,
                "pre_inference_ms": 65,
                "service_tbt_ms": 10,
                "service_ttft_ms": 482,
                "service_ttlt_ms": 3674,
                "total_duration_ms": 3613,
                "user_visible_ttft_ms": 417
              },
              "prompt_tokens": 65,
              "prompt_tokens_details": {
                "audio_tokens": 0,
                "cached_tokens": 0
              },
              "total_tokens": 395
            }
          },
          "sId": "st-b48d57c9-613f-5522-b434-1f70bb0a6fe1",
          "uId": "u-a354dad2-d3d9-5cd7-ab31-bb92844b350f",
          "validatePath": "choices[0].message.content",
          "dynamicVariable": [
            {
              "key": "prompt",
              "displayProperty": "prompt"
            },
            {
              "key": "system_context",
              "displayProperty": "system_context"
            },
            {
              "key": "Language",
              "displayProperty": "Language"
            }
          ],
          "isSysIntAndCustomPrompt": false,
          "promptVersion": "v1",
          "version": 1,
          "isStreaming": false,
          "model_response_parsing": false,
          "lastUpdated": "Fri Jul 24 2026 19:03:18 GMT+0000 (Coordinated Universal Time)",
          "modifiedOn": "2026-07-24T18:58:50.616Z",
          "createdOn": "2026-07-24T18:58:50.616Z",
          "__v": 0
        }
      ]
    }
  },
  "serviceAPITimeout": 10
}
```

## generativeAI.settings.promptFilterBasedOnModel.0.configuration.payloadFields.messages.0.content
```
{{prompt}}
;Context:{{system_context}};
process the prompt and provide the response in {{Language}}
```

## generativeAI.settings.promptFilterBasedOnModel.0.configuration.parameters.4.value
```
Input used to generate content or responses using LLMs. These prompts are designed to elicit specific types of output from the model, often tailored to a particular application or task. They are used to guide the generation process and influence the content produced by the AI system.
```

## generativeAI.settings.promptFilterBasedOnModel.0.res.choices.0.message.content
```
To help with your cruise booking or any post-booking changes, I’ll need a few details.

Please share:
1. What you want to do  
   - Book a new cruise / Change existing booking / Cancel / Add services (excursions, dining, Wi‑Fi, etc.)

2. If you already have a booking  
   - Cruise line:  
   - Ship name (if known):  
   - Sailing date:  
   - Reservation/booking number:  
   - Full name on the booking:  
   - Date of birth (for verification, if needed):  

3. If you want to book a new cruise  
   - Departure month(s) and year:  
   - Length of cruise (e.g., 3–5 nights, 7 nights, etc.):  
   - Departure port(s) you prefer:  
   - Destination(s) (e.g., Caribbean, Mediterranean, Alaska, Bahamas):  
   - Number of guests and ages (especially any under 21):  
   - Cabin type: Interior / Oceanview / Balcony / Suite / No preference  
   - Budget range per person (or total):  

4. Any preferences or needs  
   - Dining preference (early/late/anytime):  
   - Bed setup (single beds / one large bed):  
   - Accessibility needs:  
   - Travel with children or elderly guests:  
   - Need flights or hotel as well?  

Reply with the information you know (you can leave anything blank or approximate), and I’ll guide you to the best options or next steps.
```

## generativeAI.prompt
```
EXTRACT ORDER RETURN ENTITY VALUES FROM USER INPUT

INSTRUCTIONS:
1. Extract only what is explicitly mentioned or strongly implied
2. Use conversation history to resolve references ("it", "this", "that")
3. Do NOT guess missing values - EXCEPT condition inference
4. Do NOT validate correctness of values
5. Do NOT normalize or convert dates
6. Keep all values exactly as written by user
7. If input too short/ambiguous with no info - return nulls and mark as failure
8. If user says they don't know a value - leave the field null and list it in unknown_indicated_fields (see UNKNOWN SENTINEL)
9. Do NOT add explanations - JSON ONLY
10. Always return strict JSON only

---

ENTITIES TO EXTRACT:

cabin_number
  - Explicit cabin/room/stateroom/deck number(s) mentioned
  - If ONE number mentioned - return as a single string, e.g. "8393"
  - If MULTIPLE numbers mentioned - return as a comma-separated string in the
    order mentioned, e.g. "8393,8394"
  - Signals for multiple: "and", "&", "," between numbers, "2 cabins/decks",
    "both cabins"
  - Do NOT create a separate array field for this - always use this single
    field, comma-joined when there's more than one
  - Return null if not mentioned

purchase_date_raw
  - Date exactly as written by user - do NOT reformat
  - Valid: "12 April 2026", "02/22/2026", "2026-04-12"
  - Invalid: "last week", "yesterday", "recently", "my recent cruise"
  - Return null if no real calendar date

country
  - Country explicitly mentioned (e.g., "I am in US", "from Germany")
  - Do NOT infer from phone number or email
  - Return null if not mentioned

phone_number
  - Phone number exactly as written (e.g., "+1 555 123 4567", "044-1234567")
  - Return null if not mentioned

product_count
  - TOTAL UNITS being returned (see PRODUCT COUNT RULE)
  - Extract as string
  - Return null if no count stated or derivable

products (array)
  - Each product object contains:
    * product_name: Real product noun (null if not mentioned)
    * quantity: Units as string (default "1" if product_name present)
    * condition: Use CONDITION INFERENCE RULES below (null if no match)
    * expected_product_name: Only when condition = "wrong product" (null otherwise)

---

UNKNOWN SENTINEL:

If user says "I don't know", "not sure", "no idea", "can't find it" for a specific field:
  → Leave that field null
  → Add the field name to the unknown_indicated_fields array
  → Example: user doesn't know their cabin → cabin_number: null,
    unknown_indicated_fields: ["cabin_number"]

---

PURCHASE DATE RULES:

Valid formats:
  - "12 April 2026" / "April 12 2026" / "02/22/2026" / "2026-04-12" / "12/04/2026"

Invalid (return null):
  - "last week", "last month", "yesterday", "today", "a few days ago"
  - "recently", "my recent cruise", "during my cruise", "on the ship"

Keep exactly as written - no reformatting

---

PRODUCT COUNT RULE:

product_count = TOTAL UNITS being returned, not distinct product names.
  Example: "2 procollagen cream and 1 vitamin c serum" → product_count = "3"
  Example: "2 elemis cream - used one, other sealed" → product_count = "2"

If user explicitly states a total AND also names products with quantities:
  → Use whichever is HIGHER.
  → Reason: user may state the total upfront but only detail some items.
  Example: "3 products... its 2 procollagen cream and 1 vitamin c serum"
           → explicit total = 3, detailed units = 3 → product_count = "3"

If user says "2 products" but names none → product_count = "2"
Vague quantifiers ("a few", "some") with no number → null

Extract as string

---

BULK PRODUCT DETECTION:

BEFORE extracting individual fields, check if the user mentioned MULTIPLE PRODUCTS.

Signals of bulk enumeration:
  - "[number] [product] and [number] [product]" (e.g., "2 procollagen cream and 1 vitamin c serum")
  - "both [product]" / "both the same"
  - "one is [condition] and another is [condition]"
  - "another product" / "the other product"
  - Multiple product names separated by: "and", ",", "plus"
  - "I have X, Y, and Z"

IF BULK DETECTED:
  Extract EACH product as a separate object in the products array.
  Apply the SPLIT BY CONDITION RULE if the same product is mentioned with different conditions.
  Set product_count to the TOTAL UNITS across all products.

---

PRODUCT EXTRACTION:

If multiple products - extract EACH as separate object
quantity = units of that specific product as string
If product mentioned without quantity - default to "1"
Convert word-form: "two face creams" → quantity "2"

Generic words NEVER valid as product_name:
  "product", "item", "thing", "it", "them", "stuff", "this", "that", "order",
  "purchase", "skincare", "haircare", "bodycare", "wellness", "supplement",
  "beauty", "cosmetic", "treatment", "products", "items"

Category nouns (generic product types) are NOT valid product names:
  - "skincare", "haircare", "bodycare", "beauty products", "wellness products"
  - These describe a category, not a specific returnable item
  - If user says "skincare products" with no specific names → product_name = null

---

SKELETON OBJECT RULE:

Create product object whenever ANY of these is known:
  - product_name, quantity, OR condition

If product_name missing but condition OR quantity known:
  - Create skeleton with known fields filled, unknown as null

If product_count known AND condition known BUT no product names:
  - Create N skeleton objects (N = product_count)
  - Each with condition set, product_name null, quantity null

If product_count known BUT NO condition AND NO product names:
  - Leave products as empty array []

NEVER leave extractable information out of products array
NEVER copy product_count into quantity field

---

SPLIT BY CONDITION RULE:

If same product mentioned with different units having different conditions:
  - Split into SEPARATE objects with same product_name but different condition/quantity
  - Quantities across split objects must add up to total stated
  - product_count = total units across the split objects

Example: "2 elemis cream - used one, other sealed"
  Object 1: { "product_name": "elemis cream", "quantity": "1", "condition": "used" }
  Object 2: { "product_name": "elemis cream", "quantity": "1", "condition": "new" }
  product_count = "2"

---

WRONG ITEM RECEIVED RULE:

If user says they received a wrong/incorrect item OR ordered X but received Y:
  - Extract ONLY the received item as product to return (if named)
  - If no product name given — create skeleton object with condition only
  - Condition = "wrong product"
  - product_count = total units of wrong items received (usually "1")
  - If user mentions what they ordered — set expected_product_name to that item
  - If user only says wrong product with no names — set expected_product_name to null

Trigger phrases: "received wrong", "wrong product", "wrong item",
"incorrect item", "not what I ordered", "instead of", "but received",
"but got", "sent wrong"

→ If triggered: set condition = "wrong product" immediately.
  Do NOT infer any other condition alongside it.

---

CONDITION INFERENCE RULES:

Condition = "new" when:
  EXPLICIT: never used, unused, not used, unopened, not opened, never opened, brand new,
            sealed, still sealed, unopened box, original packaging, tags still on,
            intact, mint condition, straight from box, just arrived, never touched
  INTENT-BASED: arrived late, late delivery, no longer needed, don't need anymore,
                ordered by mistake, changed my mind

Condition = "used" when:
  used it, have been using, already used, opened, have opened, not satisfied,
  dissatisfied, not happy, didn't work, doesn't work, not effective, no results,
  tried it, worn, second hand, partially used, used a few times, been using it

Condition = "damaged" when:
  damaged, broken, cracked, defective, not working, stopped working, received damaged,
  arrived damaged, came damaged, not working properly, stopped functioning,
  malfunctioning, fell apart, leaking, broken piece, doesnt work, doesn't work,
  faulty, torn, scratched, not working properly

Condition = "wrong product" when:
  wrong item, wrong product, received wrong, incorrect item, not what I ordered,
  sent wrong, instead of, but received, but got
  → Apply WRONG ITEM RECEIVED RULE (see above)

Contradictory conditions:
  "opened" overrides "never used" → condition "used"
  "stopped working" overrides "barely used" → condition "damaged"
  Prefer more specific/recent action.

If NONE match → condition = null for all products.

---

EXAMPLES:

Example 1 - Multiple products with condition:
Input: "I want to return 2 procollagen cream and 1 vitamin c serum. It arrived late."
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "3",
  "products": [
    { "product_name": "procollagen cream", "quantity": "2", "condition": "new", "expected_product_name": null },
    { "product_name": "vitamin c serum", "quantity": "1", "condition": "new", "expected_product_name": null }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "3 total units across 2 products. Condition inferred as new from arrived late."
}

Example 2 - Count + condition, no product names (skeleton objects):
Input: "I want to return 2 products. They are brand new, never used."
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "2",
  "products": [
    { "product_name": null, "quantity": null, "condition": "new", "expected_product_name": null },
    { "product_name": null, "quantity": null, "condition": "new", "expected_product_name": null }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "Skeleton objects created. Condition inferred as new."
}

Example 3 - Count only, no condition or product names:
Input: "I want to return 2 products"
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "2",
  "products": [],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "Count stated but no product names or condition. Empty array returned."
}

Example 4 - Same product split by different conditions:
Input: "I have 2 elemis cream. Used one, the other is sealed."
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "2",
  "products": [
    { "product_name": "elemis cream", "quantity": "1", "condition": "used", "expected_product_name": null },
    { "product_name": "elemis cream", "quantity": "1", "condition": "new", "expected_product_name": null }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "Same product split by different conditions. 2 total units, so product_count is 2."
}

Example 5 - Contradictory conditions:
Input: "I never used it but I opened it to check. Want to return the serum."
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "1",
  "products": [
    { "product_name": "serum", "quantity": "1", "condition": "used", "expected_product_name": null }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "'opened' overrides 'never used'. Condition set to used."
}

Example 6 - Condition only, no product name:
Input: "Received a damaged product"
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": null,
  "products": [
    { "product_name": null, "quantity": null, "condition": "damaged", "expected_product_name": null }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "Condition inferred as damaged. Skeleton object created."
}

Example 7 - All entities collected:
Input: "I'm in cabin 4201. Returning a serum (never opened) and face cream (stopped working). From Germany. Reach me at +49 1234 567890. Bought on 05/10/2026."
Output:
{
  "cabin_number": "4201",
  "purchase_date_raw": "05/10/2026",
  "country": "Germany",
  "phone_number": "+49 1234 567890",
  "product_count": "2",
  "products": [
    { "product_name": "serum", "quantity": "1", "condition": "new", "expected_product_name": null },
    { "product_name": "face cream", "quantity": "1", "condition": "damaged", "expected_product_name": null }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "All entities extracted. 2 total units. Different conditions per product."
}

Example 8 - Wrong item received, no product name:
Input: "I have received a wrong product"
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "1",
  "products": [
    { "product_name": null, "quantity": null, "condition": "wrong product", "expected_product_name": null }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "Wrong item scenario. No product names given. Skeleton object created with condition wrong product."
}

Example 9 - Wrong item received, with product names:
Input: "I ordered a face cream but received a shampoo instead."
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "1",
  "products": [
    { "product_name": "shampoo", "quantity": "1", "condition": "wrong product", "expected_product_name": "face cream" }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "Wrong item scenario. Only received item (shampoo) extracted. Ordered item (face cream) saved as expected_product_name."
}

Example 10 - Category noun, no specific product names:
Input: "I purchased several skincare products onboard and would like to return them."
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": null,
  "products": [],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "'skincare products' is a category noun, not a specific product name. No extractable product names. Empty array returned."
}

Example 11 - UNKNOWN sentinel:
Input: "I don't know my cabin number. Returning a vitamin c serum, it's brand new."
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "1",
  "products": [
    { "product_name": "vitamin c serum", "quantity": "1", "condition": "new", "expected_product_name": null }
  ],
  "unknown_indicated_fields": ["cabin_number"],
  "extractionSuccessful": "success",
  "reason": "User indicated they don't know cabin number. Left null and listed in unknown_indicated_fields. Product and condition extracted."
}

Example 12 - Bulk signals (both / one is X another is Y):
Input: "I have both the eye cream and the toner. One is used, the other is sealed."
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "2",
  "products": [
    { "product_name": "eye cream", "quantity": "1", "condition": "used", "expected_product_name": null },
    { "product_name": "toner", "quantity": "1", "condition": "new", "expected_product_name": null }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "Bulk detected via 'both'. 2 total units. Conditions assigned per context."
}

Example 13 - Explicit count higher than detailed units:
Input: "i want to return 3 products. its 2 procollagen cream and 1 vitamin c serum. it arrived late, and i no longer need them"
Output:
{
  "cabin_number": null,
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": "3",
  "products": [
    { "product_name": "procollagen cream", "quantity": "2", "condition": "new", "expected_product_name": null },
    { "product_name": "vitamin c serum", "quantity": "1", "condition": "new", "expected_product_name": null }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "Explicit total 3 and detailed units 3 agree. Condition inferred as new from 'arrived late' and 'no longer need them'."
}

Example 14 - Multiple cabin numbers:
Input: "we were in 2 decks with number 8393 and 8394"
Output:
{
  "cabin_number": "8393,8394",
  "purchase_date_raw": null,
  "country": null,
  "phone_number": null,
  "product_count": null,
  "products": [],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success",
  "reason": "Two cabin numbers detected via 'and'. Comma-joined into single cabin_number field."
}

---

OUTPUT FORMAT (STRICT JSON):

{
  "cabin_number": null | string,
  "purchase_date_raw": null | string,
  "country": null | string,
  "phone_number": null | string,
  "product_count": null | string,
  "products": [
    {
      "product_name": null | string,
      "quantity": null | string,
      "condition": null | string,
      "expected_product_name": null | string
    }
  ],
  "unknown_indicated_fields": [],
  "extractionSuccessful": "success" | "failure",
  "reason": "&lt;short reason&gt;"
}

---

Conversation History:
{{context.session.BotUserSession.conversationHistoryString}}

User Input:
{{context.session.BotUserSession.initialMessage}}
```
