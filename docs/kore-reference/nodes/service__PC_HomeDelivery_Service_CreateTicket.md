# PC_HomeDelivery_Service_CreateTicket  (service)

## Config
```json
{
  "name": "PC_HomeDelivery_Service_CreateTicket",
  "endPoint": {
    "path": "{{env.ZendeskBaseUrl}}/api/v2/tickets.json",
    "method": "post",
    "connectorEnabled": false
  },
  "authRequired": false,
  "payload": {
    "type": "raw"
  },
  "headers": {
    "type": "raw",
    "value": "{\"Content-Type\":\"application/json\",\"Accept\":\"application/json\",\"Authorization\":\"Basic {{env.ZendeskAuthorization}}\"}"
  },
  "serviceType": "rest",
  "idp": "none",
  "type": "service",
  "timeOutError": {
    "closeConversation": true
  },
  "serviceAPITimeout": 20,
  "subType": "createTicketService",
  "integrationId": "zendesk",
  "isClientCertEnabled": true
}
```

## payload.value
```
{
  "ticket": {
    "subject": "{{context.SubjectText}}",
    "comment": {
      "html_body": "{{context.zd_desc_p1}}{{context.session.BotUserSession.piiEntities.name}}{{context.zd_name_fallback}}{{context.zd_desc_p2}}{{context.session.BotUserSession.piiEntities.emailId}}{{context.zd_email_fallback}}{{context.zd_desc_p3}}{{context.session.BotUserSession.piiEntities.phoneNumber}}{{context.zd_phone_fallback}}{{context.zd_desc_p4}}{{context.zd_desc_p5}}{{context.session.BotUserSession.piiEntities.creditcard}}{{context.zd_creditcard_fallback}}{{context.zd_desc_p6}}"
    },
    "requester": {
      "name": "{{context.session.BotUserSession.piiEntities.name}}{{context.zd_name_fallback}}",
      "email": "{{context.session.BotUserSession.piiEntities.emailId}}{{context.zd_email_fallback}}"
    },
    "ticket_form_id": "{{env.Zendesk_Form_ID}}",
    "brand_id": "{{env.Zendesk_Brand_ID}}",
    "group_id": "{{env.Zendesk_Return_Group_ID}}",
    "priority": "{{context.PriorityValue}}",
    "tags": {{context.zd_tags_json}},
    "custom_fields": [
      { "id": "{{env.Zendesk_InquiryType_ID}}", "value": "{{context.zd_inquiry}}" },
      { "id": "{{env.Zendesk_Category_ID}}", "value": "{{context.zd_category}}" },
      { "id": "{{env.Zendesk_ProductReason_ID}}", "value": "{{context.zd_reason_tag}}" },
      { "id": "{{env.Zendesk_ReturnStatus_ID}}", "value": "return_requested" },
      { "id": "{{env.Zendesk_CreatedBy_ID}}", "value": "chatbot" },
      { "id": "{{env.Zendesk_CruiseLine_ID}}", "value": "{{context.zd_cruise_line}}" },
      { "id": "{{env.Zendesk_CruiseShip_ID}}", "value": "{{context.zd_ship_name}}" },
      { "id": "{{env.Zendesk_Priority_ID}}", "value": "{{context.PriorityValue}}" }{{context.zd_sail_date_fragment}}
    ]
  }
}
```

## postProcessor
```
koreDebugger.log("Customer: " + context.session.BotUserSession.piiEntities.name);
koreDebugger.log("Email: " + context.session.BotUserSession.piiEntities.emailId);
```
