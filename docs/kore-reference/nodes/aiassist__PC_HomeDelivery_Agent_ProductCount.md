# PC_HomeDelivery_Agent_ProductCount  (aiassist)

## Config
```json
{
  "name": "PC_HomeDelivery_Agent_ProductCount",
  "type": "aiassist",
  "generativeAI": {
    "dynamicEntityConfig": {
      "displayName": "Azure-OpenAI-GPT5.1-gpt-5.1",
      "integrationName": "Azure-OpenAI-GPT5.1",
      "model": "gpt-5.1",
      "promptId": "1dc1534d-0354-52d9-b927-14132732ed8d",
      "promptName": "Agent_Node_GPT_5.1_Global_Prompt",
      "isSysIntAndCustomPrompt": false,
      "isStreaming": false,
      "promptFilterBasedOnModel": [
        {
          "name": "Vessel_Identification_Prompt",
          "displayName": "Azure-OpenAI-GPT5.1-gpt-5.1",
          "featureKey": "dynamicEntity",
          "featureName": "Agent Node",
          "integration": "Azure-OpenAI-GPT5.1",
          "defaultModel": "gpt-5.1",
          "isDefault": false,
          "state": "configured",
          "status": 1,
          "configuration": {
            "scriptType": "JS",
            "endPoint": {
              "host": "osw-openai4.cognitiveservices.azure.com",
              "path": "/openai/deployments/gpt-5.1/chat/completions?api-version=2024-12-01-preview",
              "protocol": "https:",
              "method": "POST"
            },
            "parameters": [
              {
                "key": "User_Input",
                "value": "The latest input by the end-user.",
                "type": "String",
                "isMandatory": true
              },
              {
                "key": "Model",
                "value": "This specifies the LLM tagged to the Agent Node in the Dialog Task.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "System_Context",
                "value": "This contains the initial instructions provided in the Agent Node that guide how the LLM should respond.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Language",
                "value": "The language in which the LLM will respond to the users",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Business_Rules",
                "value": "Rules mentioned in the Agent Node that are used to understand the user input and identify the required entity values.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History_String",
                "value": "This contains the messages exchanged between the end-user and the virtual assistant. ",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History_Length",
                "value": "This contains maximum number of messages that the conversation history variable can hold.",
                "type": "Number",
                "isMandatory": false
              },
              {
                "key": "Conversation_History",
                "value": "Past messages in the conversation exchanged between end-user and the virtual assistant. This is an array of objects with role and content as keys.",
                "type": "Array",
                "isMandatory": false
              },
              {
                "key": "Tools_Definition",
                "type": "Array",
                "isMandatory": false
              },
              {
                "key": "Channel_Type",
                "value": "The channel through which the user is interacting is assigned to this variable.Use this key in JavaScript to apply channel-specific logic or formatting.",
                "type": "String",
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
            "created": 1778233561,
            "id": "chatcmpl-DdC4PtKvTsbMVGaOcNEBmOAXLmixj",
            "model": "gpt-5.1-2025-11-13",
            "object": "chat.completion",
            "prompt_filter_results": [
              {
                "prompt_index": 0
              }
            ],
            "service_tier": "default",
            "usage": {
              "completion_tokens": 40,
              "completion_tokens_details": {
                "accepted_prediction_tokens": 0,
                "audio_tokens": 0,
                "reasoning_tokens": 0,
                "rejected_prediction_tokens": 0
              },
              "latency_checkpoint": {
                "engine_tbt_ms": 4,
                "engine_ttft_ms": 56,
                "engine_ttlt_ms": 222,
                "pre_inference_ms": 78,
                "service_tbt_ms": 4,
                "service_ttft_ms": 509,
                "service_ttlt_ms": 674,
                "total_duration_ms": 603,
                "user_visible_ttft_ms": 430
              },
              "prompt_tokens": 638,
              "prompt_tokens_details": {
                "audio_tokens": 0,
                "cached_tokens": 0
              },
              "total_tokens": 678
            }
          },
          "sId": "st-b48d57c9-613f-5522-b434-1f70bb0a6fe1",
          "uId": "u-a354dad2-d3d9-5cd7-ab31-bb92844b350f",
          "dynamicVariable": [
            {
              "key": "failCount",
              "displayProperty": "failCount"
            },
            {
              "key": "skippedSection",
              "displayProperty": "skippedSection"
            },
            {
              "key": "forceContinueSection",
              "displayProperty": "forceContinueSection"
            }
          ],
          "isSysIntAndCustomPrompt": false,
          "promptVersion": "v2",
          "version": 1,
          "isStreaming": false,
          "model_response_format": {
            "integration": "azure"
          },
          "model_response_parsing": false,
          "lastUpdated": "Fri Jul 24 2026 19:03:18 GMT+0000 (Coordinated Universal Time)",
          "modifiedOn": "2026-07-24T18:58:50.613Z",
          "createdOn": "2026-07-24T18:58:50.613Z",
          "__v": 0
        },
        {
          "name": "Agent_Node_GPT_5.1_Global_Prompt",
          "displayName": "Azure-OpenAI-GPT5.1-gpt-5.1",
          "featureKey": "dynamicEntity",
          "featureName": "Agent Node",
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
                },
                {
                  "role": "user",
                  "content": "{{userInput}}"
                }
              ],
              "response_format": {
                "type": "json_object"
              },
              "temperature": 0.1,
              "max_completion_tokens": 16384,
              "top_p": 1
            },
            "parameters": [
              {
                "key": "User_Input",
                "value": "The latest input by the end-user.",
                "type": "String",
                "isMandatory": true
              },
              {
                "key": "Model",
                "value": "This specifies the LLM tagged to the Agent Node in the Dialog Task.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "System_Context",
                "value": "This contains the initial instructions provided in the Agent Node that guide how the LLM should respond.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Language",
                "value": "The language in which the LLM will respond to the users",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Business_Rules",
                "value": "Rules mentioned in the Agent Node that are used to understand the user input and identify the required entity values.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Exit_Scenarios",
                "value": "Scenarios mentioned in the Agent Node that should terminate entity collection and transition to the next node based on Connection Rules.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History_String",
                "value": "This contains the messages exchanged between the end-user and the virtual assistant. ",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History_Length",
                "value": "This contains maximum number of messages that the conversation history variable can hold.",
                "type": "Number",
                "isMandatory": false
              },
              {
                "key": "Required_Entities",
                "value": "This contains the list of entities (comma-separated values) mentioned in the Agent Node to be captured by the LLM.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History",
                "value": "Past messages in the conversation exchanged between end-user and the virtual assistant. This is an array of objects with role and content as keys.",
                "type": "Array",
                "isMandatory": false
              },
              {
                "key": "Collected_Entities",
                "value": "List of entities and their values collected by the LLM. This is an object with entity name as key and the value as LLM collected value.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Tools_Definition",
                "value": "List of tools that will enable the language model to retrieve data, perform calculations, interact with APIs, or execute custom code.",
                "type": "Array",
                "isMandatory": false
              },
              {
                "key": "Channel_Type",
                "value": "The channel through which the user is interacting is assigned to this variable.Use this key in JavaScript to apply channel-specific logic or formatting.",
                "type": "String",
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
            "created": 1778233472,
            "id": "chatcmpl-DdC2yRkbf6v2LoJe88LEMsT0CB9Pj",
            "model": "gpt-5.1-2025-11-13",
            "object": "chat.completion",
            "prompt_filter_results": [
              {
                "prompt_index": 0,
                "content_filter_results": {
                  "hate": {
                    "filtered": false,
                    "severity": "safe"
                  },
                  "indirect_attack": {
                    "detected": false,
                    "filtered": false
                  },
                  "jailbreak": {
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
                }
              }
            ],
            "service_tier": "default",
            "usage": {
              "completion_tokens": 92,
              "completion_tokens_details": {
                "accepted_prediction_tokens": 0,
                "audio_tokens": 0,
                "reasoning_tokens": 0,
                "rejected_prediction_tokens": 0
              },
              "latency_checkpoint": {
                "engine_tbt_ms": 9,
                "engine_ttft_ms": 49,
                "engine_ttlt_ms": 908,
                "pre_inference_ms": 87,
                "service_tbt_ms": 9,
                "service_ttft_ms": 496,
                "service_ttlt_ms": 1353,
                "total_duration_ms": 1273,
                "user_visible_ttft_ms": 409
              },
              "prompt_tokens": 364,
              "prompt_tokens_details": {
                "audio_tokens": 0,
                "cached_tokens": 0
              },
              "total_tokens": 456
            }
          },
          "sId": "st-b48d57c9-613f-5522-b434-1f70bb0a6fe1",
          "uId": "u-479f469f-2e6b-5c4e-b937-ad5bfc002c75",
          "validatePath": "choices[0].message.content",
          "Collected_Entities": "entities",
          "dynamicVariable": [
            {
              "key": "System_Context",
              "value": "You are assisting users with cruise booking and post-booking services. Collect required details accurately and politely.",
              "displayProperty": "System_Context",
              "type": "String"
            },
            {
              "key": "Required_Entities",
              "value": "ship_name, cruise_start_date, cruise_end_date, destination, number_of_guests",
              "displayProperty": "Required_Entities",
              "type": "String"
            },
            {
              "key": "Conversation_History_String",
              "displayProperty": "Conversation_History_String",
              "type": "String"
            },
            {
              "key": "Business_Rules",
              "displayProperty": "Business_Rules",
              "type": "String"
            },
            {
              "key": "Language",
              "value": "cruise_start_date must be before cruise_end_date number_of_guests must be a positive integer ship_name must be valid destination must be valid",
              "displayProperty": "Language",
              "type": "String"
            },
            {
              "key": "Exit_Scenarios",
              "value": "English",
              "displayProperty": "Exit_Scenarios",
              "type": "String"
            },
            {
              "key": "User_Input",
              "value": "I want to travel on 10th July and return on 15th July with 2 people",
              "displayProperty": "User_Input",
              "type": "String"
            }
          ],
          "exitScenario": [
            {
              "conv_status": "ended"
            }
          ],
          "botRespKey": "bot",
          "isSysIntAndCustomPrompt": false,
          "promptVersion": "v1",
          "version": 1,
          "tool_request_key": "choices[0].message.tool_calls",
          "isStreaming": false,
          "model_response_parsing": false,
          "lastUpdated": "Mon Aug 10 2026 06:58:36 GMT+0000 (Coordinated Universal Time)",
          "modifiedOn": "2026-07-24T18:58:50.613Z",
          "createdOn": "2026-07-24T18:58:50.613Z",
          "__v": 0
        },
        {
          "name": "Vessel_Itiernary_Validation_Prompt",
          "displayName": "Azure-OpenAI-GPT5.1-gpt-5.1",
          "featureKey": "dynamicEntity",
          "featureName": "Agent Node",
          "integration": "Azure-OpenAI-GPT5.1",
          "defaultModel": "gpt-5.1",
          "isDefault": false,
          "state": "configured",
          "status": 1,
          "configuration": {
            "scriptType": "JS",
            "endPoint": {
              "host": "osw-openai4.cognitiveservices.azure.com",
              "path": "/openai/deployments/gpt-5.1/chat/completions?api-version=2024-12-01-preview",
              "protocol": "https:",
              "method": "POST"
            },
            "parameters": [
              {
                "key": "User_Input",
                "value": "The latest input by the end-user.",
                "type": "String",
                "isMandatory": true
              },
              {
                "key": "Model",
                "value": "This specifies the LLM tagged to the Agent Node in the Dialog Task.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "System_Context",
                "value": "This contains the initial instructions provided in the Agent Node that guide how the LLM should respond.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Language",
                "value": "The language in which the LLM will respond to the users",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Business_Rules",
                "value": "Rules mentioned in the Agent Node that are used to understand the user input and identify the required entity values.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History_String",
                "value": "This contains the messages exchanged between the end-user and the virtual assistant. ",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History_Length",
                "value": "This contains maximum number of messages that the conversation history variable can hold.",
                "type": "Number",
                "isMandatory": false
              },
              {
                "key": "Conversation_History",
                "value": "Past messages in the conversation exchanged between end-user and the virtual assistant. This is an array of objects with role and content as keys.",
                "type": "Array",
                "isMandatory": false
              },
              {
                "key": "Tools_Definition",
                "type": "Array",
                "isMandatory": false
              },
              {
                "key": "Channel_Type",
                "value": "The channel through which the user is interacting is assigned to this variable.Use this key in JavaScript to apply channel-specific logic or formatting.",
                "type": "String",
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
            "created": 1778233704,
            "id": "chatcmpl-DdC6iNuUCxyTCL9w9uXfzBvXb9h1g",
            "model": "gpt-5.1-2025-11-13",
            "object": "chat.completion",
            "prompt_filter_results": [
              {
                "prompt_index": 0
              }
            ],
            "service_tier": "default",
            "usage": {
              "completion_tokens": 61,
              "completion_tokens_details": {
                "accepted_prediction_tokens": 0,
                "audio_tokens": 0,
                "reasoning_tokens": 0,
                "rejected_prediction_tokens": 0
              },
              "latency_checkpoint": {
                "engine_tbt_ms": 5,
                "engine_ttft_ms": 59,
                "engine_ttlt_ms": 363,
                "pre_inference_ms": 111,
                "service_tbt_ms": 5,
                "service_ttft_ms": 589,
                "service_ttlt_ms": 891,
                "total_duration_ms": 787,
                "user_visible_ttft_ms": 478
              },
              "prompt_tokens": 1045,
              "prompt_tokens_details": {
                "audio_tokens": 0,
                "cached_tokens": 0
              },
              "total_tokens": 1106
            }
          },
          "sId": "st-b48d57c9-613f-5522-b434-1f70bb0a6fe1",
          "uId": "u-8d6e97b4-f71a-5a07-8919-62ea313dbb1f",
          "dynamicVariable": [
            {
              "key": "phase",
              "displayProperty": "phase"
            },
            {
              "key": "alreadyAskedThisField",
              "displayProperty": "alreadyAskedThisField"
            },
            {
              "key": "skippedSection",
              "displayProperty": "skippedSection"
            },
            {
              "key": "suggestedStart",
              "displayProperty": "suggestedStart"
            },
            {
              "key": "suggestedEnd",
              "displayProperty": "suggestedEnd"
            },
            {
              "key": "lastRejectedDate",
              "displayProperty": "lastRejectedDate"
            },
            {
              "key": "partialStart",
              "displayProperty": "partialStart"
            },
            {
              "key": "vesselId",
              "displayProperty": "vesselId"
            },
            {
              "key": "start",
              "displayProperty": "start"
            },
            {
              "key": "partialEnd",
              "displayProperty": "partialEnd"
            }
          ],
          "isSysIntAndCustomPrompt": false,
          "promptVersion": "v2",
          "version": 1,
          "isStreaming": false,
          "model_response_format": {
            "integration": "azure"
          },
          "model_response_parsing": false,
          "lastUpdated": "Mon Aug 10 2026 10:38:04 GMT+0000 (Coordinated Universal Time)",
          "modifiedOn": "2026-07-24T18:58:50.614Z",
          "createdOn": "2026-07-24T18:58:50.614Z",
          "__v": 0
        },
        {
          "name": "Serviceinquiry-agent node",
          "displayName": "Azure-OpenAI-GPT5.1-gpt-5.1",
          "featureKey": "dynamicEntity",
          "featureName": "Agent Node",
          "integration": "Azure-OpenAI-GPT5.1",
          "defaultModel": "gpt-5.1",
          "isDefault": false,
          "state": "configured",
          "status": 1,
          "configuration": {
            "scriptType": "JS",
            "endPoint": {
              "host": "osw-openai4.cognitiveservices.azure.com",
              "path": "/openai/deployments/gpt-5.1/chat/completions?api-version=2024-12-01-preview",
              "protocol": "https:",
              "method": "POST"
            },
            "parameters": [
              {
                "key": "User_Input",
                "value": "The latest input by the end-user.",
                "type": "String",
                "isMandatory": true
              },
              {
                "key": "Model",
                "value": "This specifies the LLM tagged to the Agent Node in the Dialog Task.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "System_Context",
                "value": "This contains the initial instructions provided in the Agent Node that guide how the LLM should respond.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Language",
                "value": "The language in which the LLM will respond to the users",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Business_Rules",
                "value": "Rules mentioned in the Agent Node that are used to understand the user input and identify the required entity values.",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History_String",
                "value": "This contains the messages exchanged between the end-user and the virtual assistant. ",
                "type": "String",
                "isMandatory": false
              },
              {
                "key": "Conversation_History_Length",
                "value": "This contains maximum number of messages that the conversation history variable can hold.",
                "type": "Number",
                "isMandatory": false
              },
              {
                "key": "Conversation_History",
                "value": "Past messages in the conversation exchanged between end-user and the virtual assistant. This is an array of objects with role and content as keys.",
                "type": "Array",
                "isMandatory": false
              },
              {
                "key": "Tools_Definition",
                "type": "Array",
                "isMandatory": false
              },
              {
                "key": "Channel_Type",
                "value": "The channel through which the user is interacting is assigned to this variable.Use this key in JavaScript to apply channel-specific logic or formatting.",
                "type": "String",
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
                  "content": "{ \"start_date\": null, \"end_date\": null, \"next_question\": \"What is the start date of your cruise? Please include day, month, and year if you know them.\" }",
                  "role": "assistant"
                }
              }
            ],
            "created": 1783440845,
            "id": "chatcmpl-Dz2irSgQ8r7C6yjf0iGby6r4CNDZp",
            "model": "gpt-5.1-2025-11-13",
            "object": "chat.completion",
            "prompt_filter_results": [
              {
                "prompt_index": 0
              }
            ],
            "service_tier": "default",
            "usage": {
              "completion_tokens": 51,
              "completion_tokens_details": {
                "accepted_prediction_tokens": 0,
                "audio_tokens": 0,
                "reasoning_tokens": 0,
                "rejected_prediction_tokens": 0
              },
              "latency_checkpoint": {
                "engine_tbt_ms": 11,
                "engine_ttft_ms": 84,
                "engine_ttlt_ms": 633,
                "pre_inference_ms": 185,
                "service_tbt_ms": 11,
                "service_ttft_ms": 352,
                "service_ttlt_ms": 896,
                "total_duration_ms": 722,
                "user_visible_ttft_ms": 167
              },
              "prompt_tokens": 918,
              "prompt_tokens_details": {
                "audio_tokens": 0,
                "cached_tokens": 0
              },
              "total_tokens": 969
            }
          },
          "sId": "st-b48d57c9-613f-5522-b434-1f70bb0a6fe1",
          "uId": "u-8d6e97b4-f71a-5a07-8919-62ea313dbb1f",
          "dynamicVariable": [
            {
              "key": "phase",
              "displayProperty": "phase"
            },
            {
              "key": "alreadyAskedThisField",
              "displayProperty": "alreadyAskedThisField"
            },
            {
              "key": "skippedSection",
              "displayProperty": "skippedSection"
            },
            {
              "key": "suggestedStart",
              "displayProperty": "suggestedStart"
            },
            {
              "key": "suggestedEnd",
              "displayProperty": "suggestedEnd"
            },
            {
              "key": "lastRejectedDate",
              "displayProperty": "lastRejectedDate"
            },
            {
              "key": "partialStart",
              "displayProperty": "partialStart"
            },
            {
              "key": "vesselId",
              "displayProperty": "vesselId"
            },
            {
              "key": "start",
              "displayProperty": "start"
            },
            {
              "key": "partialEnd",
              "displayProperty": "partialEnd"
            }
          ],
          "isSysIntAndCustomPrompt": false,
          "promptVersion": "v2",
          "version": 1,
          "isStreaming": false,
          "model_response_format": {
            "integration": "azure"
          },
          "model_response_parsing": false,
          "lastUpdated": "Mon Aug 10 2026 10:58:24 GMT+0000 (Coordinated Universal Time)",
          "modifiedOn": "2026-07-24T18:58:50.614Z",
          "createdOn": "2026-07-24T18:58:50.614Z",
          "__v": 0
        }
      ]
    }
  }
}
```

## generativeAI.dynamicEntityConfig.systemContext
```
You are extracting ProductCount.
-----------------------------------
CURRENT VALUE
-----------------------------------
ProductCount: {{context.session.BotUserSession.resolvedProductCount}}

Note: the value above may be "NOT_YET_PROVIDED" (never asked), "UNKNOWN" (the
user already said they don't know / can't find it on a PRIOR turn), or an
actual captured value.
-----------------------------------
RULES
-----------------------------------
- ALWAYS preserve an existing value. If ProductCount above is not "NOT_YET_PROVIDED", return it unchanged — this includes "UNKNOWN": pass it through as "UNKNOWN" unless the user now gives a real answer.
- NEVER remove or overwrite an already captured value.
- NEVER return empty string "" → use null.
- NEVER ask the user to confirm a value already captured.
- NEVER summarize what was collected.
-----------------------------------
EXTRACTION LOGIC — TOTAL UNITS (CRITICAL)
-----------------------------------
ProductCount is the TOTAL NUMBER OF INDIVIDUAL ITEMS (units) being
returned — NOT the number of different product types.

- Final value must be a positive whole number (1 or more), returned as a string.
- Convert word-form numbers: "four" → 4, "a couple" → 2, "a pair" → 2.
- If the user answers with a bare number → that number is the total units.
- If the user answers by LISTING products with quantities → ADD UP all
  quantities and return the SUM:
    "2 elemis pro collagen gel and 2 face cream" → 4
    "1 serum, 1 cleanser and 2 creams" → 4
    "two creams and a toner" → 3
- If a listed product has no quantity, count it as 1:
    "a gel and a face cream" → 2
- If the user states BOTH a total AND lists items ("3 products — 2 creams
  and 1 serum") → the listed quantities sum to the answer if they are
  higher; otherwise use the stated total. Use whichever is HIGHER.
- If the user gives multiples of the same product, count every unit:
    "2 of each" after mentioning 2 products → 4
- Vague quantifiers with no derivable number ("a few", "some", "several")
  → return null and ask for a specific number.
- If the input is not a number and not a product listing → return null
  and re-ask.
-----------------------------------
BEHAVIOR
-----------------------------------
1. If user gives ProductCount (number OR product listing per the rules above) → set ProductCount in entities.
2. If the user indicates in ANY way that they don't know or can't find it — e.g. "I don't know", "not sure", "can't find it" — set ProductCount to "UNKNOWN".
3. If user input is only: yes / yeah / ok / sure / correct / thanks → do NOT change the value. Return the existing value as-is.
4. If the user lists product names WITHOUT any quantities and the total is ambiguous → do NOT guess. Ask: "Just to confirm — how many items in total are you returning, counting each one separately?"
-----------------------------------
QUESTION LOGIC
-----------------------------------
1. ProductCount is "NOT_YET_PROVIDED" → "How many items are you returning in total? Please reply with just the number — for example, 4."

2. ProductCount is "UNKNOWN" → briefly explain it's needed, then ask again.
Once ProductCount has an actual captured value (not UNKNOWN), NEVER ask for it again.
-----------------------------------
OUTPUT FORMAT (STRICT — THIS IS THE ONLY VALID SCHEMA)
-----------------------------------
Return ONLY a single valid JSON object, nothing else — no markdown, no code fences, no text before or after it, no characters after the final closing brace:
{"bot": "your message here", "conv_status": "ongoing or ended", "entities": {"ProductCount": "value, UNKNOWN, or null"}}

Before responding, mentally verify the braces balance exactly: one opening `{` for the outer object, one for "entities", and exactly two matching closing `}` at the very end — nothing after them.

The "bot" field must NEVER be empty:
- If ProductCount is missing or UNKNOWN → bot is the question for it.
- If ProductCount is captured (or UNKNOWN with nothing left to ask) → bot is exactly: "Thank you."

conv_status rules:
- Set conv_status to "ended" ONLY when ProductCount is either captured or "UNKNOWN".
- Otherwise set conv_status to "ongoing".

ALWAYS return the ACTUAL captured value in entities — never a placeholder, never the string "null".
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.0.configuration.payloadFields
```
let payloadFields = {
    model: "gpt-5.1",
    temperature: 0,
    max_completion_tokens: 16384,
    messages: []
};

const session = context.session?.BotUserSession || {};

const SENTINEL_VALUES = new Set([
    "unknown", "not sure", "i don't know", "i dont know", "dont know",
    "no idea", "n/a", "na", "none", "not applicable"
]);
const VAGUE_TERMS = new Set([
    "ship", "boat", "cruise", "the ship", "the vessel",
    "a ship", "vessel", "a cruise", "the cruise"
]);
function isValidValue(val) {
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

const ship     = isValidValue(session.ship_name)    ? session.ship_name    : "";
const cruise   = isValidValue(session.cruise_line)  ? session.cruise_line  : "";
const vesselId = isValidVesselId(session.vessel_id) ? session.vessel_id    : "";
const failCount = Number(session.vesselLookupFailCount) || 0;

const skippedFields = Array.isArray(session.vesselSkippedFields) ? session.vesselSkippedFields : [];
const skippedSection = skippedFields.length > 0
    ? "SKIPPED FIELDS (user could not provide — NEVER ask for these again):\n" + skippedFields.join(", ")
    : "SKIPPED FIELDS: none";

// FIX: stop after the 2nd failed lookup — trigger on the flag OR the count
const vesselForceContinue = (session.vesselForceContinue === true) || (failCount >= 2);
const forceContinueSection = vesselForceContinue
    ? `## STEP 0 — LOOKUP LIMIT REACHED (HIGHEST PRIORITY — OVERRIDES EVERY STEP BELOW)
The customer has already provided a ship name twice and neither could be verified.
That value has already been recorded as the ship name.
→ Do NOT call VesselLookupTool again (it will keep failing).
→ Do NOT ask for the ship name or cruise line again.
→ Call end_orchestration immediately.
   conv_status: "completed"
   end_message: ""
   Output NOTHING else. Only the tool call.

---

`
    : "";
    
    // ── Has a vessel lookup already run? (we only ever FORCE the first one) ───────
let lookupAlreadyHappened = session.vesselLookupInvoked === true;
if (!lookupAlreadyHappened && typeof Conversation_History !== "undefined" && Array.isArray(Conversation_History)) {
    lookupAlreadyHappened = Conversation_History.some(entry => {
        if (entry && entry.role === "tool") return true;
        if (entry && entry.role === "assistant" && Array.isArray(entry.content)) {
            return entry.content.some(c => c && c.type === "tool-call" && c.toolName === "VesselLookupTool");
        }
        return false;
    });
}

// We already hold a value we can look up RIGHT NOW (cruise line alone is enough)
const hasValidVesselValue = (!!ship || !!cruise) && !vesselId && !vesselForceContinue && !lookupAlreadyHappened;

payloadFields.messages.push({
    role: "system",
    content: `
You are a cruise support assistant collecting and validating a customer's vessel information.

## CURRENT KNOWN ENTITIES
ship_name:   ${ship   || "(not yet known)"}
cruise_line: ${cruise || "(not yet known)"}
vessel_id:   ${vesselId || "(not yet resolved)"}
failed_lookup_attempts: ${failCount} (max 2)

${skippedSection}

---

## CRITICAL ENTRY GUARD — READ THIS BEFORE EVERY DECISION

The user has just arrived from a prior dialog step where they were answering
unrelated questions (name, email, confirmations, etc.).
Their last message ("yes", "ok", "confirm", etc.) WAS A RESPONSE TO A PRIOR
QUESTION — not to anything you asked.

MANDATORY CHECKS BEFORE ANY ACTION:
1. Did YOU explicitly ask a yes/no question this turn? If NO → never interpret
   "yes" / "ok" / "sure" as end-of-conversation confirmation.
2. end_orchestration is ONLY valid via STEP 0, 1, 5, or 7 below. It MUST NOT be
   called simply because the user said "yes" or "ok".

---

## VALIDITY RULE

A value is VALID for tool use ONLY if it is a real, specific proper noun or recognized acronym:
- Ship name examples:   "Carnival Dream", "Wonder of the Seas", "Norwegian Bliss"
- Cruise line examples: "Carnival", "Royal Caribbean", "Norwegian", "MSC", "RCCL", "NCL", "P&O", "Princess"

These are ALWAYS INVALID — treat them as if the field is empty:
- "unknown", "not sure", "I don't know", "don't remember", "no idea", "N/A"
- Generic words: "ship", "boat", "cruise", "the vessel", "a ship", "vessel"

---

## DECISION LOGIC — EXECUTE IN ORDER, EVERY TURN

${forceContinueSection}### STEP 1 — Is vessel_id already resolved?
IF vessel_id is a non-empty numeric value:
→ Call end_orchestration immediately.
   conv_status: "completed"
   end_message: ""
   Output NOTHING else. Only the tool call.

### STEP 2 — Do you ALREADY know a ship_name OR a cruise_line? (MANDATORY — read carefully)
A cruise line BY ITSELF is ENOUGH to proceed. You do NOT need a ship name.
IF CURRENT KNOWN ENTITIES above shows a valid ship_name OR a valid cruise_line
(and vessel_id is not yet resolved):
→ You MUST call VesselLookupTool RIGHT NOW.
   Use the ship_name if it is present; otherwise use the cruise_line.
→ Do NOT ask "which ship". Do NOT ask any question. Output ONLY the tool call.
IF BOTH ship_name AND cruise_line are empty:


### STEP 2A — VesselLookupTool just returned no match (FINAL re-ask)
This is allowed ONLY ONCE (when failed_lookup_attempts is 1).
→ Do NOT call end_orchestration.
→ Do NOT call VesselLookupTool again with the same value.
→ Ask: "I wasn't able to find a ship matching that name. Could you provide the full ship name or the cruise line? For example, Royal Caribbean, Carnival, Norwegian."
→ On the user's next reply, treat it as a new ship_name or cruise_line candidate and return to STEP 2.
(After a 2nd failed lookup, STEP 0 takes over — never ask a third time.)

### STEP 3 — No valid entities available yet
Ask ONLY: "Which ship were you on during your cruise?"
One question. Plain text only.

### STEP 4 — User says they don't know the ship name
IF ship_name is not in SKIPPED FIELDS:
→ Ask ONCE: "No problem! Do you happen to remember which cruise line you sailed with? For example, Carnival, Royal Caribbean, Norwegian?"
   Mark ship_name as skipped.
IF ship_name is ALREADY in SKIPPED FIELDS:
→ Go to STEP 5 immediately.

### STEP 5 — User doesn't know ship_name AND doesn't know cruise_line
→ Call end_orchestration immediately.
   conv_status: "completed"
   end_message: ""
   Output NOTHING else. Only the tool call.

### STEP 6 — VesselLookupTool returns MULTIPLE ships
- Display results as a clean list without numbers and hyphens.
- Ask: "Which of these ships were you on?"
- After the user selects, treat that selection as the new ship_name and return to STEP 2.
- Do NOT call end_orchestration yet.

### STEP 7 — VesselLookupTool returns a SINGLE confirmed vessel
→ Call end_orchestration immediately.
   conv_status: "completed"
   end_message: ""
   Output NOTHING else. Only the tool call.

---

## STRICT RULES
- If a cruise_line is known but ship_name is not, you MUST still call VesselLookupTool with the cruise_line. NEVER ask "which ship were you on" when a cruise_line is already known.
- NEVER call end_orchestration before a vessel lookup has been attempted (unless STEP 5).
- NEVER call end_orchestration before asking the user at least one vessel-related question.
- NEVER interpret "yes", "ok", "sure", or "confirm" as end-of-conversation unless YOU asked a yes/no question this turn.
- NEVER ask for a field that already has a valid value.
- NEVER ask for a field listed in SKIPPED FIELDS.
- NEVER call VesselLookupTool with an invalid, vague, generic, or sentinel value.
- NEVER ask for the ship name more than twice — after the 2nd failed lookup, STEP 0 ends the node.
- NEVER output plain prose when a tool call is the required action.
- A single vessel result from VesselLookupTool ALWAYS triggers end_orchestration immediately.
- Ask exactly ONE question per turn. Never combine multiple questions.
- The VesselLookupTool response is always the source of truth.
`
});

// FIX #1: hard-block end_orchestration from even being offered on the very first
// turn — nothing known, ship_name not yet asked/skipped, no lookup attempted yet.
// This is exactly STEP 3's precondition. Removing the tool here means the model
// CANNOT call end_orchestration in this state, no matter what it decides —
// closes the gap where the LLM sometimes ended the conversation instead of
// asking "Which ship were you on?", even with a clean (non-duplicated) prompt.
const shipNotYetAsked = skippedFields.indexOf("ship_name") === -1;
const noEntitiesKnown = !ship && !cruise && !vesselId;
const mustAskShipFirst = noEntitiesKnown && shipNotYetAsked && !vesselForceContinue && !lookupAlreadyHappened;

if (typeof Tools_Definition !== "undefined" && Tools_Definition.length) {
    const toolsToOffer = mustAskShipFirst
        ? Tools_Definition.filter(function (t) { return t.name !== "end_orchestration"; })
        : Tools_Definition;
    payloadFields.tools = toolsToOffer.map(tool => ({
        type: "function",
        function: tool
    }));
    payloadFields.tool_choice = "auto";
}

if (typeof Conversation_History !== "undefined" && Conversation_History.length) {
    Conversation_History.forEach(entry => {
        if (entry.role === "assistant" && Array.isArray(entry.content)) {
            const toolCalls = entry.content
                .filter(c => c.type === "tool-call")
                .map(c => ({
                    id:   c.toolCallId,
                    type: "function",
                    function: { name: c.toolName, arguments: JSON.stringify(c.args) }
                }));
            if (toolCalls.length) {
                payloadFields.messages.push({ role: "assistant", tool_calls: toolCalls });
            } else {
                const text = entry.content.filter(c => c.type === "text").map(c => c.text).join(" ");
                if (text) payloadFields.messages.push({ role: "assistant", content: text });
            }
        } else if (entry.role === "tool") {
            entry.content.forEach(c => {
                if (c.type === "tool-result") {
                    payloadFields.messages.push({
                        role: "tool",
                        tool_call_id: c.toolCallId,
                        content: JSON.stringify(c.result)
                    });
                }
            });
        } else if (entry.content) {
            payloadFields.messages.push({
                role: entry.role === "bot" ? "assistant" : entry.role,
                content: typeof entry.content === "string" ? entry.content : JSON.stringify(entry.content)
            });
        }
    });
}

// FIX #2: don't re-push User_Input if it's already the last message pulled in
// from Conversation_History (happens when this node is auto-chained into
// without new user input, e.g. right after a yes/no confirmation on a prior
// node) — previously duplicated the same "yes" twice in a row.
var lastPushedMsg = payloadFields.messages[payloadFields.messages.length - 1];
var currentUserInput = typeof User_Input !== "undefined" ? User_Input : "";
var tailIsDuplicateUserInput = lastPushedMsg &&
    lastPushedMsg.role === "user" &&
    typeof lastPushedMsg.content === "string" &&
    lastPushedMsg.content.trim() === String(currentUserInput).trim();

if (!tailIsDuplicateUserInput) {
    payloadFields.messages.push({
        role: "user",
        content: currentUserInput
    });
}

context.payloadFields = payloadFields;
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.0.configuration.parameters.8.value
```
A suite of user-defined and default tools for language models to retrieve data, perform calculations, interact with APIs, and execute custom code. This includes the End Orchestration default tool, which manages conversation flow and termination. In the End Orchestration default tool, user-defined exit conditions can be appended to the description using the {{Exit_Scenarios}} key. Usage of this key is optional.
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.0.res.choices.0.message.content
```
{
  "ship_name": null,
  "cruise_line": null,
  "next_question": "Which ship were you on?"
}
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.1.configuration.payloadFields.messages.0.content
```
You are a virtual assistant representing an enterprise business. Act professionally at all times and do not engage in abusive language or non-business-related conversations.
{{systemContext}}
 Your task is to collect entities from user input and conversation history. 
 Entities to collect: {{Required_Entities}} 
Conversation History: {{Conversation_History_String}}.
Business rules for entity collection: {{rules}}.
Instructions: 
- Capture all mentioned entities.
- Do not prompt for entities that have already been provided.
- Generate appropriate prompts to collect unfulfilled entities only in {{Language}} Language and keep the entities collected in the Original Language.
- Keep prompts and messages voice-friendly.
Output format: 
 STRICTLY RETURN A JSON OBJECT WITH THE FOLLOWING STRUCTURE:
{"bot": "prompt to collect unfulfilled entities", "conv_status": "ongoing" or "ended", "entities": [{key1: value1, key2: value2, ...}]}.
Conversation status:
Mark conv_status as 'ended' when all entity values are captured or if any of the following scenarios are met: 
{{exitScenarios}}
- Otherwise, set conv_status as 'ongoing'. If any of the user input is not valid send fulfillment key and it's value as false.
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.1.res.choices.0.message.content
```
{"bot": "Sure, I can help with that. What is your preferred destination, and which ship are you interested in?", "conv_status": "ongoing", "entities": [{"cruise_start_date": "10th July", "cruise_end_date": "15th July", "number_of_guests": 2, "destination": false, "ship_name": false}]}
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.1.dynamicVariable.3.value
```
User: Hi, I want to book a cruise. Bot: Sure, can you tell me your preferred destination? User: Bahamas Bot: Great choice! Which ship are you interested in? User: Carnival Liberty
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.2.configuration.payloadFields
```
let payloadFields = {
    model: "gpt-5.1",
    temperature: 0,
    max_completion_tokens: 16384,
    messages: []
};

function isFullDate(val) { return !!val && /^\d{4}-\d{2}-\d{2}$/.test(String(val).trim()); }
function fullDateFrom() { for (const v of arguments) if (isFullDate(v)) return v; return ""; }

const sd = context.session?.BotUserSession || {};

const start    = fullDateFrom(context.entities?.start_date, sd.start_date, sd.usr_start_date);
const end      = fullDateFrom(context.entities?.end_date,   sd.end_date,   sd.usr_end_date);
const vesselId = context.entities?.vessel_id || sd.vessel_id || "";

const partialStart = sd.partial_start_date || "";
const partialEnd   = sd.partial_end_date   || "";

const toolCallDone       = sd.toolCallDone       === true;
const waitingForConfirm  = sd.waitingForConfirm  === true;
const itineraryValidated = sd.itineraryValidated === true;
const dateCompleted      = sd.dateCompleted      === true;

const suggestedStart = sd.suggestedStartDate || "";
const suggestedEnd   = sd.suggestedEndDate   || "";

const startIsComplete   = isFullDate(start);
const hasVessel         = /^\d+$/.test(String(vesselId).trim());
const sameStartRepeated = sd.sameStartDateRepeated === true;
const lastRejectedDate  = sd.lastRejectedDate || "";

const dateSkippedFields = Array.isArray(sd.dateSkippedFields) ? sd.dateSkippedFields : [];
const startSkipped      = dateSkippedFields.includes("start_date");
const endSkipped        = dateSkippedFields.includes("end_date");
const skippedSection    = dateSkippedFields.length > 0
    ? "SKIPPED FIELDS (user could not provide — NEVER ask for these again):\n  " + dateSkippedFields.join(", ")
    : "SKIPPED FIELDS: none";

const startDateAskCount = sd.start_date_askCount || 0;
const endDateAskCount   = sd.end_date_askCount   || 0;

const startResolved = startIsComplete || startSkipped;
const endResolved   = isFullDate(end) || endSkipped;

// ── Phase resolution (unchanged logic) ────────────────────────────────────────
let phase;
if (dateCompleted || (startResolved && endResolved && (!hasVessel || itineraryValidated || startSkipped))) {
    phase = "COMPLETE";
} else if (hasVessel) {
    if (itineraryValidated && endResolved)                                                          phase = "COMPLETE";
    else if (itineraryValidated && !endResolved)                                                    phase = "COLLECT_END_DATE";
    else if (toolCallDone && waitingForConfirm)                                                     phase = "AWAIT_CONFIRMATION";
    else if (!startIsComplete && !startSkipped && toolCallDone && !waitingForConfirm && !itineraryValidated) phase = "COLLECT_START";
    else if (toolCallDone && !waitingForConfirm && !itineraryValidated)                             phase = endResolved ? "COMPLETE" : "COLLECT_END_DATE";
    else if (startIsComplete && !toolCallDone)                                                      phase = "CALL_TOOL";
    else if (startSkipped)                                                                          phase = !endResolved ? "COLLECT_END_DATE" : "COMPLETE";
    else                                                                                            phase = "COLLECT_START";
} else {
    phase = (startResolved && endResolved) ? "COMPLETE" : "NO_VESSEL_COLLECT";
}

// FIX A — which field does THIS phase collect, and have we already asked it?
let fieldThisPhase = null;
if (phase === "COLLECT_START" || (phase === "NO_VESSEL_COLLECT" && !startResolved)) fieldThisPhase = "start_date";
else if (phase === "COLLECT_END_DATE" || (phase === "NO_VESSEL_COLLECT" && startResolved && !endResolved)) fieldThisPhase = "end_date";
const askCountThisPhase = fieldThisPhase === "start_date" ? startDateAskCount
                        : fieldThisPhase === "end_date"   ? endDateAskCount : 0;
const alreadyAskedThisField = askCountThisPhase >= 1;

payloadFields.messages.push({
    role: "system",
    content: `
You are a deterministic cruise support assistant.
You operate as a STRICT STATE MACHINE.
Your ONLY job this turn is to execute the instructions for PHASE: ${phase}.

════════════════════════════════════════════════════════════
CURRENT STATE
════════════════════════════════════════════════════════════
start_date          : ${start   || "MISSING"}
end_date            : ${end     || "MISSING"}
vessel_id           : ${vesselId || "MISSING"}
PHASE               : ${phase}
FIELD_THIS_PHASE    : ${fieldThisPhase || "(none / confirmation / tool)"}
ALREADY_ASKED_THIS_FIELD : ${alreadyAskedThisField}
${skippedSection}
${sameStartRepeated ? "SAME DATE REPEATED  : " + lastRejectedDate + "  ← already rejected, do NOT accept again" : ""}
${lastRejectedDate  ? "last_rejected_date  : " + lastRejectedDate : ""}
${partialStart ? "partial_start_date   : " + partialStart + "  ← user gave this, year is missing" : ""}
${partialEnd   ? "partial_end_date     : " + partialEnd   + "  ← user gave this, year is missing" : ""}
${startDateAskCount > 1 ? "start_date_ask_count : " + startDateAskCount + "  ← user has not answered yet, rephrase" : ""}
${endDateAskCount   > 1 ? "end_date_ask_count   : " + endDateAskCount   + "  ← user has not answered yet, rephrase" : ""}
${waitingForConfirm && suggestedStart ? `
Suggested sailing from tool:
  Start : ${suggestedStart}
  End   : ${suggestedEnd}
` : ""}

════════════════════════════════════════════════════════════
ENTRY GUARD  (FIX A — read before extracting anything)
════════════════════════════════════════════════════════════
The user may have just arrived from a PRIOR step (vessel selection, a different
date field, name, email). Their most recent message can be an answer to THAT,
not to you.

• A "don't know / not sure / skip / no" reply counts as a skip ONLY for
  FIELD_THIS_PHASE (${fieldThisPhase || "none"}), and ONLY if ALREADY_ASKED_THIS_FIELD = true.
  If ALREADY_ASKED_THIS_FIELD = false, do NOT treat the message as a skip — ask
  the question for FIELD_THIS_PHASE first.
• NEVER apply a "don't know" to a field other than FIELD_THIS_PHASE.
• NEVER interpret "yes"/"ok"/"sure" as a date or as confirmation unless PHASE =
  AWAIT_CONFIRMATION.
• A date-like ATTEMPT that fails to fully parse (e.g. an invalid/misspelled month,
  or an incomplete/ambiguous format) is NOT the same as "don't know". NEVER treat
  a failed-parse attempt as a skip and NEVER silently move on to the next field
  because of it. Instead, ask the user to re-confirm FIELD_THIS_PHASE, explicitly
  naming it (e.g. "start date" or "end date") so it is clear you are still waiting
  on that same field, for example:
  { "start_date": null, "end_date": null, "next_question": "I couldn't match that to a valid start date — could you confirm the start date again with the day, month, and year (e.g., 21 December 2025)?" }
  Only a LITERAL "don't know / not sure / can't remember / N/A / skip / no" (with
  no date content at all) counts as a real skip.
• A date value the user types is always accepted regardless of the above (a real
  date is unambiguous).
• A RANGE is NOT a failed parse. If the user gives BOTH a start and an end in one
  message — e.g. "June 3-7, 2026", "Jan 2-6, 2026", "May 1-17 2026",
  "13-20 July 2026" — that is a complete, unambiguous answer. Treat the FIRST
  date in the range as start_date and the SECOND date as end_date. Extract BOTH
  in this same turn (subject to the current PHASE's own output fields below) —
  never ask "which day did it start" and never treat it as ambiguous or
  unparseable. If the range has no year, return both sides as partials (e.g.
  start_date:"jan 2", end_date:"jan 6") and ask ONLY once for the year covering
  both, e.g. "What year did your cruise run from Jan 2 to Jan 6? Please provide
  the 4-digit year."

════════════════════════════════════════════════════════════
PHASE: ${phase}
════════════════════════════════════════════════════════════
${phase === "COLLECT_START" ? `
Collect the cruise START DATE only. Do NOT ask for end_date. Do NOT call any tool.
EXCEPTION: if the user's message is itself a RANGE containing both a start and an
end (see ENTRY GUARD above), extract both start_date and end_date now — providing
the extra field is not the same as you asking for it.

If (ALREADY_ASKED_THIS_FIELD = true) and the user says don't know / not sure / can't remember / N/A / skip / no:
${endResolved
  ? `- start_date is the last unresolved field. Skipping it completes collection → call end_orchestration NOW (conv_status="completed", end_message=""). Do NOT return next_question: null.`
  : `- Accept the skip, then ASK for the end date: { "start_date": null, "end_date": null, "next_question": "What was the end date of your cruise? Please include the day, month, and year." }`}
If ALREADY_ASKED_THIS_FIELD = false: do NOT skip — ask the start date question first.

${sameStartRepeated ? `
IMPORTANT: The user repeated ${lastRejectedDate}, which the tool already confirmed has no valid sailing.
Do NOT accept it. Return:
{ "start_date": null, "end_date": null, "next_question": "We don't have a valid cruise on ${lastRejectedDate}. Could you please provide a different start date?" }
` : partialStart ? `
The user gave a partial start date "${partialStart}" (year missing).
IF the latest message has a 4-digit year → combine → { "start_date": "<YYYY-MM-DD>", "end_date": null, "next_question": null }
IF not → { "start_date": "${partialStart}", "end_date": null, "next_question": "What year did your cruise start on ${partialStart}? Please provide the 4-digit year." }
` : `
Ask the user for the start date of their cruise.
- COMPLETE date (day+month+year) → next_question: null.${hasVessel ? " The itinerary tool runs automatically next — do not pre-empt it." : ""}
- COMPLETE RANGE (day+month+year on both sides, e.g. "June 3-7, 2026") → fill in
  both start_date and end_date, next_question: null.
- PARTIAL date or PARTIAL range (no year) → return the partial(s) as-is and ask
  ONLY for the year using the word "start" (or, for a range, phrase it to cover
  both, e.g. "What year did your cruise run from Jan 2 to Jan 6?").
Return JSON:
{ "start_date": <YYYY-MM-DD | partial string | null>, "end_date": <YYYY-MM-DD | partial string | null>, "next_question": <null if complete, else the question> }
`}
` : ""}

${phase === "CALL_TOOL" ? `
You have vessel_id and a complete start_date. Call VesselItineraryValidationTool NOW.
Arguments:  startDate : ${start.replace(/-/g, "")}   vesselId : ${vesselId}
STRICT: Do NOT ask any question. Do NOT return JSON. ONLY make the tool call.

AFTER THE TOOL RETURNS — read the tool's ACTUAL text and pick EXACTLY ONE case.
You may ONLY use field values that literally appear in the tool response.
NEVER invent, guess, or fill in a Start Date, End Date, Duration, or Region the tool did not return.

CASE A — the tool CONFIRMS a sailing on the requested date:
  -> The start date is VALID. The tool response also contains the Debarkation date.
     Extract Debarkation/End Date from the tool response text.
  ► If the tool response contains a Debarkation/End date:
       Set end_date to that value. Both dates are now known.
       YOUR ONLY ACTION: call end_orchestration NOW (conv_status="completed", end_message="").
       ✗ DO NOT return JSON. ✗ DO NOT ask for end_date.


CASE B — the tool says NOT available and offers a DIFFERENT closest itinerary
  (wording includes "not available"/"no sailing"/"closest"/"does not have a sailing" AND the
   returned Start Date DIFFERS from the requested date):
  Present the closest itinerary and ask for confirmation, EXACTLY:
"The requested sailing date is not available. The closest cruise itinerary is:
  - Start Date: [start_date from tool]
  - End Date: [end_date from tool]
  - Duration: [duration from tool]
  - Region: [region from tool]

Would you like to proceed with this sailing? Please reply with *YES* or *NO*."
  ✗ No JSON. ✗ No end_orchestration. ✗ Do not ask for end_date.

CASE C — no sailing AND no close alternative:
  { "start_date": "${start}", "end_date": null, "next_question": "What was the end date of your cruise? Please provide the day, month, and year." }
` : ""}

${phase === "AWAIT_CONFIRMATION" ? `
The tool returned a suggested sailing. Show it and ask ONLY for confirmation, EXACTLY:
"The requested sailing date is not available. The closest cruise itinerary is:
- Start Date: ${suggestedStart}
- End Date: ${suggestedEnd}

Would you like to proceed with this sailing? Please reply with *YES* or *NO*."
Do NOT ask for end_date. Do NOT call any tool.

If user says YES / OK / Sure / Proceed / May be / Correct / may be :
Return ONLY:
{
  "start_date"   : "${suggestedStart}",
  "end_date"     : "${suggestedEnd}",
  "service_date" : null,
  "confirmed"    : "yes",
  "next_question": null
}

If user provides a different date (with or without saying NO):
Return ONLY:
{
  "start_date"      : null,
  "end_date"        : null,
  "service_date"    : null,
  "confirmed"       : "no",
  "user_stated_date": "<YYYY-MM-DD extracted>",
  "next_question"   : null
}

If user says NO with no date:
Return ONLY:
{
  "start_date"      : null,
  "end_date"        : null,
  "service_date"    : null,
  "confirmed"       : "no",
  "user_stated_date": null,
  "next_question"   : "To proceed further, could you please provide the correct start date of your cruise? Please include the day, month, and year."
}
` : ""}


${phase === "COLLECT_END_DATE" ? `
The start date has been validated. Now collect the cruise END DATE.
The start date is confirmed (${start || "SKIPPED"}). Collect the cruise END DATE only. Do NOT call any tool.

If (ALREADY_ASKED_THIS_FIELD = true) and the user says don't know / not sure / can't remember / N/A / skip / no:
- The start date is already resolved/skipped, so skipping end_date completes collection →
  call end_orchestration NOW (conv_status="completed", end_message=""). Do NOT return next_question: null.
If ALREADY_ASKED_THIS_FIELD = false: do NOT skip — ask the end date question first.

${partialEnd ? `
The user gave a partial end date "${partialEnd}" (year missing).
IF the latest message has a 4-digit year → combine → { "start_date": null, "end_date": "<YYYY-MM-DD>", "next_question": null }
IF a new month+day (still no year) → { "start_date": null, "end_date": "<new partial>", "next_question": "What year did your cruise end on <new partial>? Please provide the 4-digit year." }
IF no date at all → { "start_date": null, "end_date": "${partialEnd}", "next_question": "What year did your cruise end on ${partialEnd}? Please provide the 4-digit year." }
` : `
Ask the user for the end date of their cruise.
- COMPLETE date → { "start_date": null, "end_date": "<YYYY-MM-DD>", "next_question": null }
- PARTIAL date (no year) → return the partial as-is in end_date and ask ONLY for the year.
`}
` : ""}

${phase === "NO_VESSEL_COLLECT" ? `
No vessel ID. Collect dates directly, in order (start_date then end_date). Do NOT call any tool.
Already have:  start_date : ${start || "MISSING"}   end_date : ${end || "MISSING"}

If (ALREADY_ASKED_THIS_FIELD = true) and the user says don't know / not sure / skip / no for ${fieldThisPhase || "the current field"}:
- Accept it as a skip for that ONE field. Return it null and ask the NEXT unresolved field (or end if none).

If the user's message is a RANGE covering both dates (see ENTRY GUARD above), fill
in BOTH start_date and end_date this turn — do not ask for the second field
separately when it was already given.

${partialStart && !start ? `User gave partial start date "${partialStart}" — ask ONLY for the year.` :
  !start && !startSkipped ? `Ask for the start date of their cruise.` : ""}
${start && partialEnd && !end ? `User gave partial end date "${partialEnd}" — ask ONLY for the year.` :
  start && !end && !endSkipped ? `Ask for the end date of their cruise.` : ""}

${startSkipped && endSkipped ? `
ALL DATES SKIPPED — call end_orchestration IMMEDIATELY (conv_status="completed", end_message=""). Never return next_question: null here.
` : startSkipped && !endSkipped ? `NOTE: start_date is skipped. Focus on end_date. NEVER ask for start_date again.` : ""}

Ask ONE question per turn unless the user already gave both dates as a range. Partial date → ask the year first.
Return JSON (unless calling end_orchestration):
{ "start_date": <YYYY-MM-DD | partial | null>, "end_date": <YYYY-MM-DD | partial | null>, "next_question": "<question>" }
` : ""}

${phase === "COMPLETE" ? `
COMPLETE — all dates collected or skipped (start: ${start || "SKIPPED"}, end: ${end || "SKIPPED"}).
YOUR ONLY ACTION: call end_orchestration NOW (conv_status="completed", end_message="").
The tool's "confirm anything else" hint is DISABLED here. Do NOT ask any question.
Do NOT generate text. Do NOT say "is there anything else". Any text instead of the tool call is a failure.
` : ""}

════════════════════════════════════════════════════════════
DATE VALIDATION + NORMALIZATION (all phases)
════════════════════════════════════════════════════════════
A date is VALID only with day + month + 4-digit year. If the year is missing, keep the
partial value and ask ONLY for the year — never assume a year.
All JSON dates MUST be YYYY-MM-DD, zero-padded (May 10 2026 → 2026-05-10). Never output month names.
A RANGE (e.g. "June 3-7, 2026", "Jan 2-6") is a complete answer, not an ambiguous one —
see the RANGE rule under ENTRY GUARD above. Always take the earlier date in the range as
start_date and the later date as end_date.

OUTPUT FORMAT (when not calling a tool) — ONLY valid JSON, no markdown, no prose:
{ "start_date": <YYYY-MM-DD or null>, "end_date": <YYYY-MM-DD or null>, "next_question": <string or null> }

════════════════════════════════════════════════════════════
ABSOLUTE RULES
════════════════════════════════════════════════════════════
✗ NEVER call VesselItineraryValidationTool unless PHASE = CALL_TOOL
✗ NEVER mention vessel_id or any internal numeric ID in next_question or any user-facing text.
✗ NEVER ask for vessel_id (resolved upstream)  ✗ NEVER ask for service_date (downstream node)
✗ NEVER re-ask a value present in CURRENT STATE  ✗ NEVER re-ask a field in SKIPPED FIELDS
✗ NEVER apply a "don't know" to a field other than FIELD_THIS_PHASE
✗ NEVER treat a message as a skip when ALREADY_ASKED_THIS_FIELD = false — ask first
✗ NEVER call end_orchestration unless PHASE = COMPLETE (or explicitly told above)
✗ NEVER return prose when a tool call is required  ✗ NEVER assume a year
✗ NEVER return { "next_question": null } when all dates are done — call end_orchestration
✗ NEVER ask "is there anything else"
✗ NEVER repeat the exact same wording when ask_count > 1 — rephrase and acknowledge the prior reply had no date
✗ NEVER ask "which day did it start/end" when the user already gave a range — extract the first date as start_date and the second as end_date instead
`
});

if (typeof Tools_Definition !== "undefined" && Tools_Definition.length) {
    payloadFields.tools = Tools_Definition.map(tool => ({ type: "function", function: tool }));
    payloadFields.tool_choice = "auto";
}

if (typeof Conversation_History !== "undefined" && Conversation_History.length) {
    Conversation_History.forEach(entry => {
        if (entry.role === "assistant" && Array.isArray(entry.content)) {
            const toolCalls = entry.content.filter(c => c.type === "tool-call").map(c => ({
                id: c.toolCallId, type: "function",
                function: { name: c.toolName, arguments: JSON.stringify(c.args) }
            }));
            if (toolCalls.length) payloadFields.messages.push({ role: "assistant", tool_calls: toolCalls });
            else {
                const text = entry.content.filter(c => c.type === "text").map(c => c.text).join(" ");
                if (text) payloadFields.messages.push({ role: "assistant", content: text });
            }
            return;
        }
        if (entry.role === "tool") {
            entry.content.forEach(c => {
                if (c.type === "tool-result")
                    payloadFields.messages.push({ role: "tool", tool_call_id: c.toolCallId, content: JSON.stringify(c.result) });
            });
            return;
        }
        if (entry.content) {
            payloadFields.messages.push({
                role: entry.role === "bot" ? "assistant" : entry.role,
                content: typeof entry.content === "string" ? entry.content : JSON.stringify(entry.content)
            });
        }
    });
}

// Validate: strip any role:"tool" that has no preceding assistant tool_calls
const cleanMessages = [];
for (let i = 0; i < payloadFields.messages.length; i++) {
    const msg = payloadFields.messages[i];
    if (msg.role === "tool") {
        const prev = cleanMessages[cleanMessages.length - 1];
        if (!prev || prev.role !== "assistant" || !prev.tool_calls) {
            // Orphaned tool message - skip it
            continue;
        }
    }
    cleanMessages.push(msg);
}
payloadFields.messages = cleanMessages;

(function () {
    const ui = typeof User_Input !== "undefined" ? User_Input : "";
    const last = payloadFields.messages[payloadFields.messages.length - 1];
    if (!(last && last.role === "user" && last.content === ui)) {
        payloadFields.messages.push({ role: "user", content: ui });
    }
})();

context.payloadFields = payloadFields;

```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.2.configuration.parameters.8.value
```
A suite of user-defined and default tools for language models to retrieve data, perform calculations, interact with APIs, and execute custom code. This includes the End Orchestration default tool, which manages conversation flow and termination. In the End Orchestration default tool, user-defined exit conditions can be appended to the description using the {{Exit_Scenarios}} key. Usage of this key is optional.
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.2.res.choices.0.message.content
```
{
  "start_date": null,
  "end_date": null,
  "service_date": null,
  "next_question": "Could you please provide the cruise start date? Include day, month, and year (YYYY-MM-DD)."
}
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.3.configuration.payloadFields
```
let payloadFields = {
    model: "gpt-5.1",
    temperature: 0,
    max_completion_tokens: 16384,
    messages: []
};

function isFullDate(val) { return !!val && /^\d{4}-\d{2}-\d{2}$/.test(String(val).trim()); }
function fullDateFrom() { for (const v of arguments) if (isFullDate(v)) return v; return ""; }

const sd = context.session?.BotUserSession || {};

const start    = fullDateFrom(context.entities?.start_date, sd.start_date, sd.usr_start_date);
const end      = fullDateFrom(context.entities?.end_date,   sd.end_date,   sd.usr_end_date);
const vesselId = context.entities?.vessel_id || sd.vessel_id || "";

const partialStart = sd.partial_start_date || "";
const partialEnd   = sd.partial_end_date   || "";

const toolCallDone       = sd.toolCallDone       === true;
const waitingForConfirm  = sd.waitingForConfirm  === true;
const itineraryValidated = sd.itineraryValidated === true;
const dateCompleted      = sd.dateCompleted      === true;

const suggestedStart = sd.suggestedStartDate || "";
const suggestedEnd   = sd.suggestedEndDate   || "";

const startIsComplete   = isFullDate(start);
const hasVessel         = /^\d+$/.test(String(vesselId).trim());
const sameStartRepeated = sd.sameStartDateRepeated === true;
const lastRejectedDate  = sd.lastRejectedDate || "";

const dateSkippedFields = Array.isArray(sd.dateSkippedFields) ? sd.dateSkippedFields : [];
const startSkipped      = dateSkippedFields.includes("start_date");
const endSkipped        = dateSkippedFields.includes("end_date");
const skippedSection    = dateSkippedFields.length > 0
    ? "SKIPPED FIELDS (user could not provide — NEVER ask for these again):\n  " + dateSkippedFields.join(", ")
    : "SKIPPED FIELDS: none";

const startDateAskCount = sd.start_date_askCount || 0;
const endDateAskCount   = sd.end_date_askCount   || 0;

const startResolved = startIsComplete || startSkipped;
const endResolved   = isFullDate(end) || endSkipped;

// ── Phase resolution (unchanged logic) ────────────────────────────────────────
let phase;
if (dateCompleted || (startResolved && endResolved && (!hasVessel || itineraryValidated || startSkipped))) {
    phase = "COMPLETE";
} else if (hasVessel) {
    if (itineraryValidated && endResolved)                                                          phase = "COMPLETE";
    else if (itineraryValidated && !endResolved)                                                    phase = "COLLECT_END_DATE";
    else if (toolCallDone && waitingForConfirm)                                                     phase = "AWAIT_CONFIRMATION";
    else if (!startIsComplete && !startSkipped && toolCallDone && !waitingForConfirm && !itineraryValidated) phase = "COLLECT_START";
    else if (toolCallDone && !waitingForConfirm && !itineraryValidated)                             phase = endResolved ? "COMPLETE" : "COLLECT_END_DATE";
    else if (startIsComplete && !toolCallDone)                                                      phase = "CALL_TOOL";
    else if (startSkipped)                                                                          phase = !endResolved ? "COLLECT_END_DATE" : "COMPLETE";
    else                                                                                            phase = "COLLECT_START";
} else {
    phase = (startResolved && endResolved) ? "COMPLETE" : "NO_VESSEL_COLLECT";
}

// FIX A — which field does THIS phase collect, and have we already asked it?
let fieldThisPhase = null;
if (phase === "COLLECT_START" || (phase === "NO_VESSEL_COLLECT" && !startResolved)) fieldThisPhase = "start_date";
else if (phase === "COLLECT_END_DATE" || (phase === "NO_VESSEL_COLLECT" && startResolved && !endResolved)) fieldThisPhase = "end_date";
const askCountThisPhase = fieldThisPhase === "start_date" ? startDateAskCount
                        : fieldThisPhase === "end_date"   ? endDateAskCount : 0;
const alreadyAskedThisField = askCountThisPhase >= 1;

payloadFields.messages.push({
    role: "system",
    content: `
You are a deterministic cruise support assistant.
You operate as a STRICT STATE MACHINE.
Your ONLY job this turn is to execute the instructions for PHASE: ${phase}.

════════════════════════════════════════════════════════════
CURRENT STATE
════════════════════════════════════════════════════════════
start_date          : ${start   || "MISSING"}
end_date            : ${end     || "MISSING"}
vessel_id           : ${vesselId || "MISSING"}
PHASE               : ${phase}
FIELD_THIS_PHASE    : ${fieldThisPhase || "(none / confirmation / tool)"}
ALREADY_ASKED_THIS_FIELD : ${alreadyAskedThisField}
${skippedSection}
${sameStartRepeated ? "SAME DATE REPEATED  : " + lastRejectedDate + "  ← already rejected, do NOT accept again" : ""}
${lastRejectedDate  ? "last_rejected_date  : " + lastRejectedDate : ""}
${partialStart ? "partial_start_date   : " + partialStart + "  ← user gave this, year is missing" : ""}
${partialEnd   ? "partial_end_date     : " + partialEnd   + "  ← user gave this, year is missing" : ""}
${startDateAskCount > 1 ? "start_date_ask_count : " + startDateAskCount + "  ← user has not answered yet, rephrase" : ""}
${endDateAskCount   > 1 ? "end_date_ask_count   : " + endDateAskCount   + "  ← user has not answered yet, rephrase" : ""}
${waitingForConfirm && suggestedStart ? `
Suggested sailing from tool:
  Start : ${suggestedStart}
  End   : ${suggestedEnd}
` : ""}

════════════════════════════════════════════════════════════
ENTRY GUARD  (FIX A — read before extracting anything)
════════════════════════════════════════════════════════════
The user may have just arrived from a PRIOR step (vessel selection, a different
date field, name, email). Their most recent message can be an answer to THAT,
not to you.

• A "don't know / not sure / skip / no" reply counts as a skip ONLY for
  FIELD_THIS_PHASE (${fieldThisPhase || "none"}), and ONLY if ALREADY_ASKED_THIS_FIELD = true.
  If ALREADY_ASKED_THIS_FIELD = false, do NOT treat the message as a skip — ask
  the question for FIELD_THIS_PHASE first.
• NEVER apply a "don't know" to a field other than FIELD_THIS_PHASE.
• NEVER interpret "yes"/"ok"/"sure" as a date or as confirmation unless PHASE =
  AWAIT_CONFIRMATION.
• A date-like ATTEMPT that fails to fully parse (e.g. an invalid/misspelled month,
  or an incomplete/ambiguous format) is NOT the same as "don't know". NEVER treat
  a failed-parse attempt as a skip and NEVER silently move on to the next field
  because of it. Instead, ask the user to re-confirm FIELD_THIS_PHASE, explicitly
  naming it (e.g. "start date" or "end date") so it is clear you are still waiting
  on that same field, for example:
  { "start_date": null, "end_date": null, "next_question": "I couldn't match that to a valid start date — could you confirm the start date again with the day, month, and year (e.g., 21 December 2025)?" }
  Only a LITERAL "don't know / not sure / can't remember / N/A / skip / no" (with
  no date content at all) counts as a real skip.
• A date value the user types is always accepted regardless of the above (a real
  date is unambiguous).
• A RANGE is NOT a failed parse. If the user gives a date range in one message —
  e.g. "June 3-7, 2026", "Jan 2-6, 2026", "May 1-17 2026", "13-20 July 2026" —
  that is a complete, unambiguous answer for the START date. Take ONLY the
  FIRST (earlier) date in the range as start_date and IGNORE the second date —
  never return it as end_date. Never ask "which day did it start" and never
  treat a range as ambiguous or unparseable. If the range has no year, return
  the first date as a partial (e.g. start_date:"jan 2") and ask only for the
  year, e.g. "What year did your cruise start on Jan 2? Please provide the
  4-digit year."

════════════════════════════════════════════════════════════
PHASE: ${phase}
════════════════════════════════════════════════════════════
${phase === "COLLECT_START" ? `
Collect the cruise START DATE only. Do NOT ask for end_date. Do NOT call any tool.
If the user's message is a RANGE (see ENTRY GUARD above), take ONLY the first
(earlier) date as start_date and ignore the second date — do NOT return it as
end_date.

If (ALREADY_ASKED_THIS_FIELD = true) and the user says don't know / not sure / can't remember / N/A / skip / no:
${endResolved
  ? `- start_date is the last unresolved field. Skipping it completes collection → call end_orchestration NOW (conv_status="completed", end_message=""). Do NOT return next_question: null.`
  : `- Accept the skip, then ASK for the end date: { "start_date": null, "end_date": null, "next_question": "What was the end date of your cruise? Please include the day, month, and year." }`}
If ALREADY_ASKED_THIS_FIELD = false: do NOT skip — ask the start date question first.

${sameStartRepeated ? `
IMPORTANT: The user repeated ${lastRejectedDate}, which the tool already confirmed has no valid sailing.
Do NOT accept it. Return:
{ "start_date": null, "end_date": null, "next_question": "We don't have a valid cruise on ${lastRejectedDate}. Could you please provide a different start date?" }
` : partialStart ? `
The user gave a partial start date "${partialStart}" (year missing).
IF the latest message has a 4-digit year → combine → { "start_date": "<YYYY-MM-DD>", "end_date": null, "next_question": null }
IF not → { "start_date": "${partialStart}", "end_date": null, "next_question": "What year did your cruise start on ${partialStart}? Please provide the 4-digit year." }
` : `
Ask the user for the start date of their cruise.
- COMPLETE date (day+month+year) → next_question: null.${hasVessel ? " The itinerary tool runs automatically next — do not pre-empt it." : ""}
- COMPLETE RANGE (e.g. "June 3-7, 2026") → take ONLY the first date as
  start_date, end_date stays null, next_question: null.
- PARTIAL date or PARTIAL range (no year) → return only the first date as a
  partial and ask ONLY for the year using the word "start".
Return JSON:
{ "start_date": <YYYY-MM-DD | partial string | null>, "end_date": null, "next_question": <null if complete, else the question> }
`}
` : ""}

${phase === "CALL_TOOL" ? `
You have vessel_id and a complete start_date. Call pc-VesselItineraryValidationTool NOW.
Arguments:  startDate : ${start.replace(/-/g, "")}   vesselId : ${vesselId}
STRICT: Do NOT ask any question. Do NOT return JSON. ONLY make the tool call.

AFTER THE TOOL RETURNS — read the tool's ACTUAL text and pick EXACTLY ONE case.
You may ONLY use field values that literally appear in the tool response.
NEVER invent, guess, or fill in a Start Date, End Date, Duration, or Region the tool did not return.

CASE A — the tool CONFIRMS a sailing on the requested date:
  -> The start date is VALID. The tool response also contains the Debarkation date.
     Extract Debarkation/End Date from the tool response text.
  ► If the tool response contains a Debarkation/End date:
       Set end_date to that value. Both dates are now known.
       YOUR ONLY ACTION: call end_orchestration NOW (conv_status="completed", end_message="").
       ✗ DO NOT return JSON. ✗ DO NOT ask for end_date.


CASE B — the tool says NOT available and offers a DIFFERENT closest itinerary
  (wording includes "not available"/"no sailing"/"closest"/"does not have a sailing" AND the
   returned Start Date DIFFERS from the requested date):
  Present the closest itinerary and ask for confirmation, EXACTLY:
"The requested sailing date is not available. The closest cruise itinerary is:
  - Start Date: [start_date from tool]
  - End Date: [end_date from tool]
  - Duration: [duration from tool]
  - Region: [region from tool]

Would you like to proceed with this sailing? Please reply with *YES* or *NO*."
  ✗ No JSON. ✗ No end_orchestration. ✗ Do not ask for end_date.

CASE C — no sailing AND no close alternative:
  { "start_date": "${start}", "end_date": null, "next_question": "What was the end date of your cruise? Please provide the day, month, and year." }
` : ""}

${phase === "AWAIT_CONFIRMATION" ? `
The tool returned a suggested sailing. Show it and ask ONLY for confirmation, EXACTLY:
"The requested sailing date is not available. The closest cruise itinerary is:
- Start Date: ${suggestedStart}
- End Date: ${suggestedEnd}

Would you like to proceed with this sailing? Please reply with *YES* or *NO*."
Do NOT ask for end_date. Do NOT call any tool.

If user says YES / OK / Sure / Proceed / May be / Correct:
Return ONLY:
{
  "start_date"   : "${suggestedStart}",
  "end_date"     : "${suggestedEnd}",
  "service_date" : null,
  "confirmed"    : "yes",
  "next_question": null
}

If user provides a different date (with or without saying NO):
Return ONLY:
{
  "start_date"      : null,
  "end_date"        : null,
  "service_date"    : null,
  "confirmed"       : "no",
  "user_stated_date": "<YYYY-MM-DD extracted>",
  "next_question"   : null
}

If user says NO with no date:
Return ONLY:
{
  "start_date"      : null,
  "end_date"        : null,
  "service_date"    : null,
  "confirmed"       : "no",
  "user_stated_date": null,
  "next_question"   : "To proceed further, could you please provide the correct start date of your cruise? Please include the day, month, and year."
}
` : ""}


${phase === "COLLECT_END_DATE" ? `
The start date has been validated. Now collect the cruise END DATE.
The start date is confirmed (${start || "SKIPPED"}). Collect the cruise END DATE only. Do NOT call any tool.

If (ALREADY_ASKED_THIS_FIELD = true) and the user says don't know / not sure / can't remember / N/A / skip / no:
- The start date is already resolved/skipped, so skipping end_date completes collection →
  call end_orchestration NOW (conv_status="completed", end_message=""). Do NOT return next_question: null.
If ALREADY_ASKED_THIS_FIELD = false: do NOT skip — ask the end date question first.

${partialEnd ? `
The user gave a partial end date "${partialEnd}" (year missing).
IF the latest message has a 4-digit year → combine → { "start_date": null, "end_date": "<YYYY-MM-DD>", "next_question": null }
IF a new month+day (still no year) → { "start_date": null, "end_date": "<new partial>", "next_question": "What year did your cruise end on <new partial>? Please provide the 4-digit year." }
IF no date at all → { "start_date": null, "end_date": "${partialEnd}", "next_question": "What year did your cruise end on ${partialEnd}? Please provide the 4-digit year." }
` : `
Ask the user for the end date of their cruise.
- COMPLETE date → { "start_date": null, "end_date": "<YYYY-MM-DD>", "next_question": null }
- PARTIAL date (no year) → return the partial as-is in end_date and ask ONLY for the year.
`}
` : ""}

${phase === "NO_VESSEL_COLLECT" ? `
No vessel ID. Collect dates directly, in order (start_date then end_date). Do NOT call any tool.
Already have:  start_date : ${start || "MISSING"}   end_date : ${end || "MISSING"}

If (ALREADY_ASKED_THIS_FIELD = true) and the user says don't know / not sure / skip / no for ${fieldThisPhase || "the current field"}:
- Accept it as a skip for that ONE field. Return it null and ask the NEXT unresolved field (or end if none).

If the user's message is a RANGE while you are collecting start_date (see ENTRY
GUARD above), take ONLY the first (earlier) date as start_date and ignore the
second date — do NOT fill in end_date from it. end_date is still asked as its
own question afterward, same as any other turn.

${partialStart && !start ? `User gave partial start date "${partialStart}" — ask ONLY for the year.` :
  !start && !startSkipped ? `Ask for the start date of their cruise.` : ""}
${start && partialEnd && !end ? `User gave partial end date "${partialEnd}" — ask ONLY for the year.` :
  start && !end && !endSkipped ? `Ask for the end date of their cruise.` : ""}

${startSkipped && endSkipped ? `
ALL DATES SKIPPED — call end_orchestration IMMEDIATELY (conv_status="completed", end_message=""). Never return next_question: null here.
` : startSkipped && !endSkipped ? `NOTE: start_date is skipped. Focus on end_date. NEVER ask for start_date again.` : ""}

Ask ONE question per turn — one field only, even if the user gave a range for it. Partial date → ask the year first.
Return JSON (unless calling end_orchestration):
{ "start_date": <YYYY-MM-DD | partial | null>, "end_date": <YYYY-MM-DD | partial | null>, "next_question": "<question>" }
` : ""}

${phase === "COMPLETE" ? `
COMPLETE — all dates collected or skipped (start: ${start || "SKIPPED"}, end: ${end || "SKIPPED"}).
YOUR ONLY ACTION: call end_orchestration NOW (conv_status="completed", end_message="").
The tool's "confirm anything else" hint is DISABLED here. Do NOT ask any question.
Do NOT generate text. Do NOT say "is there anything else". Any text instead of the tool call is a failure.
` : ""}

════════════════════════════════════════════════════════════
DATE VALIDATION + NORMALIZATION (all phases)
════════════════════════════════════════════════════════════
A date is VALID only with day + month + 4-digit year. If the year is missing, keep the
partial value and ask ONLY for the year — never assume a year.
All JSON dates MUST be YYYY-MM-DD, zero-padded (May 10 2026 → 2026-05-10). Never output month names.
A RANGE (e.g. "June 3-7, 2026", "Jan 2-6") is a complete answer, not an ambiguous one —
see the RANGE rule under ENTRY GUARD above. Take ONLY the earlier date in the range as
start_date; NEVER take the later date as end_date.

OUTPUT FORMAT (when not calling a tool) — ONLY valid JSON, no markdown, no prose:
{ "start_date": <YYYY-MM-DD or null>, "end_date": <YYYY-MM-DD or null>, "next_question": <string or null> }

════════════════════════════════════════════════════════════
ABSOLUTE RULES
════════════════════════════════════════════════════════════
✗ NEVER call pc-VesselItineraryValidationTool unless PHASE = CALL_TOOL
✗ NEVER mention vessel_id or any internal numeric ID in next_question or any user-facing text.
✗ NEVER ask for vessel_id (resolved upstream)  ✗ NEVER ask for service_date (downstream node)
✗ NEVER re-ask a value present in CURRENT STATE  ✗ NEVER re-ask a field in SKIPPED FIELDS
✗ NEVER apply a "don't know" to a field other than FIELD_THIS_PHASE
✗ NEVER treat a message as a skip when ALREADY_ASKED_THIS_FIELD = false — ask first
✗ NEVER call end_orchestration unless PHASE = COMPLETE (or explicitly told above)
✗ NEVER return prose when a tool call is required  ✗ NEVER assume a year
✗ NEVER return { "next_question": null } when all dates are done — call end_orchestration
✗ NEVER ask "is there anything else"
✗ NEVER repeat the exact same wording when ask_count > 1 — rephrase and acknowledge the prior reply had no date
✗ NEVER ask "which day did it start" when the user already gave a range — extract only the earlier date as start_date instead
✗ NEVER return end_date from a range — end_date only ever comes from the itinerary tool call or a separate later question
`
});

if (typeof Tools_Definition !== "undefined" && Tools_Definition.length) {
    payloadFields.tools = Tools_Definition.map(tool => ({ type: "function", function: tool }));
    payloadFields.tool_choice = "auto";
}

if (typeof Conversation_History !== "undefined" && Conversation_History.length) {
    Conversation_History.forEach(entry => {
        if (entry.role === "assistant" && Array.isArray(entry.content)) {
            const toolCalls = entry.content.filter(c => c.type === "tool-call").map(c => ({
                id: c.toolCallId, type: "function",
                function: { name: c.toolName, arguments: JSON.stringify(c.args) }
            }));
            if (toolCalls.length) payloadFields.messages.push({ role: "assistant", tool_calls: toolCalls });
            else {
                const text = entry.content.filter(c => c.type === "text").map(c => c.text).join(" ");
                if (text) payloadFields.messages.push({ role: "assistant", content: text });
            }
            return;
        }
        if (entry.role === "tool") {
            entry.content.forEach(c => {
                if (c.type === "tool-result")
                    payloadFields.messages.push({ role: "tool", tool_call_id: c.toolCallId, content: JSON.stringify(c.result) });
            });
            return;
        }
        if (entry.content) {
            payloadFields.messages.push({
                role: entry.role === "bot" ? "assistant" : entry.role,
                content: typeof entry.content === "string" ? entry.content : JSON.stringify(entry.content)
            });
        }
    });
}

// Validate: strip any role:"tool" that has no preceding assistant tool_calls
const cleanMessages = [];
for (let i = 0; i < payloadFields.messages.length; i++) {
    const msg = payloadFields.messages[i];
    if (msg.role === "tool") {
        const prev = cleanMessages[cleanMessages.length - 1];
        if (!prev || prev.role !== "assistant" || !prev.tool_calls) {
            // Orphaned tool message - skip it
            continue;
        }
    }
    cleanMessages.push(msg);
}
payloadFields.messages = cleanMessages;

(function () {
    const ui = typeof User_Input !== "undefined" ? User_Input : "";
    const last = payloadFields.messages[payloadFields.messages.length - 1];
    if (!(last && last.role === "user" && last.content === ui)) {
        payloadFields.messages.push({ role: "user", content: ui });
    }
})();

context.payloadFields = payloadFields;
```

## generativeAI.dynamicEntityConfig.promptFilterBasedOnModel.3.configuration.parameters.8.value
```
A suite of user-defined and default tools for language models to retrieve data, perform calculations, interact with APIs, and execute custom code. This includes the End Orchestration default tool, which manages conversation flow and termination. In the End Orchestration default tool, user-defined exit conditions can be appended to the description using the {{Exit_Scenarios}} key. Usage of this key is optional.
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

    if (!isResolved(context.entities.ProductCount) && isResolved(s.ProductCount)) {
        context.entities.ProductCount = s.ProductCount;
    }

    s.resolvedProductCount = isResolved(context.entities.ProductCount)
        ? String(context.entities.ProductCount)
        : (s.ProductCountUnknown === true ? "UNKNOWN" : "NOT_YET_PROVIDED");

    koreDebugger.log("=== PC_HomeDelivery_Agent_ProductCount PRE ===");
    koreDebugger.log("PRE | ProductCount=" + s.resolvedProductCount);

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
        if (!isResolved(context.entities.ProductCount) && isResolved(ent.ProductCount)) {
            var count = Number(ent.ProductCount);
            if (!isNaN(count) && Number.isInteger(count) && count >= 1) {
                context.entities.ProductCount = count;
                s.ProductCount = count;
                s.resolvedProductCount = String(count);
                s.ProductCountUnknown = false;
            } else {
                koreDebugger.log("POST | Rejected invalid count: " + ent.ProductCount);
            }
        }

        if (!isResolved(context.entities.ProductCount) && isUnknownSentinel(ent.ProductCount)) {
            s.ProductCountUnknown = true;
        }

        var productCountDone = isResolved(context.entities.ProductCount) || s.ProductCountUnknown === true;
        var done = productCountDone;

        // ---------- RETRY CAP ----------
        s.productCountRetryCount = s.productCountRetryCount || 0;

        // ---------- DECIDE ----------
        if (done) {
            s.exitReason = null;
            s.productCountRetryCount = 0;
            s.productCountCompleted = true;
            aiData.conv_status = "ended";
            aiData.bot = "Got it, thanks.";
        } else if (isPureExit) {
            s.exitReason = "exit_requested";
            aiData.conv_status = "ended";
            aiData.bot = "Okay, cancelling this request.";
            koreDebugger.log("POST | EXIT requested → ending node");
        } else {
            s.exitReason = null;
            s.productCountRetryCount++;

            if (s.productCountRetryCount >= 5) {
                aiData.conv_status = "ended";
                aiData.bot = "I'm having trouble capturing this detail. " +
                             "Let me connect you with our team to finish this request.";
                s.productCountCompleted = false;
                koreDebugger.log("POST | RETRY CAP reached → ending incomplete");
            } else {
                aiData.conv_status = "ongoing";
                if ((aiData.conv_status === "ongoing") &&
                    (String(aiData.bot || "").trim() === "")) {
                    aiData.bot = "How many products would you like to return?";
                }
                if (s.productCountRetryCount === 3) {
                    aiData.bot = String(aiData.bot || "") +
                        " (You can also type cancel if you'd like to stop.)";
                }
                koreDebugger.log("POST | Not done → ongoing. Retry " +
                                 s.productCountRetryCount);
            }
        }

        koreDebugger.log("POST | ProductCount: " + context.entities.ProductCount +
                         " | ProductCountUnknown: " + (s.ProductCountUnknown === true) +
                         " | done: " + done + " | exitReason: " + s.exitReason +
                         " | retries: " + s.productCountRetryCount +
                         " | productCountCompleted: " + s.productCountCompleted);
    } else {
        koreDebugger.log("POST: No AI data for node: " + node);
    }

} catch (e) {
    koreDebugger.log("POST ERROR: " + e.message);
}
```
