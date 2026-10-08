# PC_HomeDelivery_Entity_PhoneNumber  (entity)

## Config
```json
{
  "name": "PC_HomeDelivery_Entity_PhoneNumber",
  "type": "entity",
  "entityType": "phone_number",
  "generativeAI": {
    "rephrase": {
      "isSysIntAndCustomPrompt": false
    }
  },
  "regexPattern": "^\\+?[0-9][0-9\\s()-]{6,}$",
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
  "isArray": false
}
```
