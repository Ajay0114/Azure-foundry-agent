# PC_HomeDelivery_BookingClassifier  (generativeai)

## Config
```json
{
  "name": "PC_HomeDelivery_BookingClassifier",
  "type": "generativeai",
  "generativeAI": {
    "settings": {
      "model": "gpt-5.1",
      "integrationName": "Azure-OpenAI-GPT5.1",
      "displayName": "Azure-OpenAI-GPT5.1-gpt-5.1",
      "promptId": "d5db8780-9685-5da0-b491-b9cf2f5a3f2e",
      "isCustom": true,
      "isSysIntAndCustomPrompt": false,
      "promptName": "prompt_Node_GPT_5.1",
      "Noofprevioususerinputs": 5,
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
          "__v": 0,
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
              "key": "Model",
              "value": "This specifies the targeted Large Language Model for generating responses from the given request prompt.",
              "isMandatory": false
            },
            {
              "key": "language",
              "value": "The language in which the LLM will respond to the users",
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
          "promptName": "prompt_Node_GPT_5.1"
        }
      ]
    }
  }
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

## generativeAI.settings.promptFilterBasedOnModel.0.parameters.4.value
```
Input used to generate content or responses using LLMs. These prompts are designed to elicit specific types of output from the model, often tailored to a particular application or task. They are used to guide the generation process and influence the content produced by the AI system.
```

## generativeAI.prompt
```
CLASSIFY A USER'S RESPONSE TO A BOOKING NUMBER REQUEST

CONTEXT:
The user was asked for their cruise booking number (also called
reservation number, booking reference, or record locator). Classify
their reply so the bot can decide whether to accept it, ask again,
or continue without it.

INSTRUCTIONS:
1. Classify into exactly one category below
2. Extract the booking value EXACTLY as typed if one is present
3. Do NOT validate, normalize, uppercase, or strip characters
4. Do NOT guess a value that was not typed
5. Do NOT add explanations outside the JSON
6. Return strict JSON only

---

CATEGORIES:

"valid"
  User supplied something that reads as a booking reference.
  Cruise booking references vary by line: pure digits, pure letters,
  or mixed alphanumeric. Length is typically 5 to 12 characters.
  Accept any of these shapes. Ignore surrounding words.
  Examples: "4599290", "it's X8K2M9", "ABC1234", "booking is 8FK2LM"
  → booking_number = the identifier only, exactly as typed

"unknown"
  User indicates they do not know, do not have, or cannot find it.
  Examples: "I don't know", "not sure", "no idea", "I don't have it
  with me", "can't find it", "left it at home", "skip"
  → booking_number = null

"wrong_identifier"
  User supplied an identifier but named it as something other than a
  booking or reservation number.
  Examples: "my loyalty number is 88231", "is my cabin number 4201 ok?",
  "I have my Captain's Club number"
  → booking_number = null
  → identifier_given = what the user called it

"unclear"
  Anything else: off-topic, a question back to the bot, gibberish,
  empty, or a reply containing no identifier and no refusal.
  Examples: "what is that?", "hello", "asdkjh", "why do you need it"
  → booking_number = null

---

RULES:

- If the user gives BOTH a refusal and a value, prefer "valid".
  Example: "not sure but I think it's 4599290" → valid
- If the user gives a value AND names it as a loyalty or membership
  number, classify "wrong_identifier", not "valid".
- If the user gives a value while ASKING whether it is correct,
  classify "valid" if they call it a booking or reservation number,
  otherwise "wrong_identifier".
- Never treat a cabin number as a booking number.
- Conversational filler with no identifier is "unclear", not "unknown".
  Reserve "unknown" for an actual inability to supply the number.
- Preserve the value exactly as typed, including lowercase letters,
  spaces and hyphens inside the identifier.

---

EXAMPLES:

Input: "4599290"
{ "category": "valid", "booking_number": "4599290", "identifier_given": null,
  "reason": "Numeric booking reference supplied." }

Input: "my booking ref is 8fk2lm"
{ "category": "valid", "booking_number": "8fk2lm", "identifier_given": null,
  "reason": "Alphanumeric reference supplied, kept as typed." }

Input: "i dont have it on me right now"
{ "category": "unknown", "booking_number": null, "identifier_given": null,
  "reason": "User cannot supply the number." }

Input: "will my loyalty number work? 88231"
{ "category": "wrong_identifier", "booking_number": null,
  "identifier_given": "loyalty number",
  "reason": "User named a loyalty number, not a booking reference." }

Input: "what do you mean"
{ "category": "unclear", "booking_number": null, "identifier_given": null,
  "reason": "User asked a clarifying question, no value supplied." }

---

OUTPUT FORMAT (STRICT JSON):

{
  "category": "valid" | "unknown" | "wrong_identifier" | "unclear",
  "booking_number": null | string,
  "identifier_given": null | string,
  "reason": "&lt;short reason&gt;"
}

---

User Input:
{{context.entities.PC_HomeDelivery_Entity_BookingNumber}}
```
