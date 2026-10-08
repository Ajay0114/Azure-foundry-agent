# PC_HomeDelivery_Entity_CreditCardInfo  (entity)

## Config
```json
{
  "name": "PC_HomeDelivery_Entity_CreditCardInfo",
  "type": "entity",
  "entityType": "number",
  "generativeAI": {
    "rephrase": {
      "isSysIntAndCustomPrompt": false
    }
  },
  "regexPattern": "^\\d{4}$",
  "message": [
    {
      "channel": "default"
    }
  ],
  "errorMessage": [
    {
      "channel": "default"
    }
  ],
  "isArray": false,
  "sensitive_pattern": {
    "display": {
      "type": "redaction"
    }
  }
}
```
