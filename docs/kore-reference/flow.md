# PC_HomeDelivery (Product Return) – flow graph

94 nodes; 92 reachable from intent0 (breadth-first order below); 2 not reachable (interrupt/intent entry points).

## PC_HomeDelivery [intent]
- nodeId: `intent0`
- DEFAULT -> PC_Common_1_Script_InitialUserMessage [script]

## PC_Common_1_Script_InitialUserMessage [script]
- nodeId: `nd-scr-1e65c027-d94e-4e40-a92e-d0fb95e6c74d`
- DEFAULT -> PC_Common_Empathy_Check [intent]

## PC_Common_Empathy_Check [intent]
- nodeId: `nd-int-d8d6aa2a-7a8e-46b1-95c4-66047b7d836f`
- DEFAULT -> PC_Common_1_Msg_Display [message]

## PC_Common_1_Msg_Display [message]
- nodeId: `nd-msg-8f03643a-fba4-4d35-8520-74ea9b7b7fa2`
- DEFAULT -> PC_Common_1_Entity_Name [entity]

## PC_Common_1_Entity_Name [entity]
- nodeId: `nd-ent-caa76663-4837-419e-8e54-4db0cca06748`
- DEFAULT -> PC_Common_1_Script_redactionName [script]

## PC_Common_1_Script_redactionName [script]
- nodeId: `nd-scr-de0535ac-c177-4a88-8cda-6db369a2b5b9`
- DEFAULT -> PC_Common_1_Entity_Emailid [entity]

## PC_Common_1_Entity_Emailid [entity]
- nodeId: `nd-ent-338c7d50-4e62-4502-9734-fa38826b8ea6`
- DEFAULT -> PC_Common_1_Script_redactEmail [script]

## PC_Common_1_Script_redactEmail [script]
- nodeId: `nd-scr-44beb345-57d2-4680-b5e2-ad6946d87397`
- DEFAULT -> PC_Common_1_Confirmation_EmailConfirmation [dialogAct]

## PC_Common_1_Confirmation_EmailConfirmation [dialogAct]
- nodeId: `nd-dac-fec8b2dd-4fc9-467e-a048-f1e3cd0b88e7`
- USER SAYS YES -> PC_ExtractCruiseEntitiesFromInitialUserMessage [generativeai]
- USER SAYS NO -> PC_Common_1_Script_DeleteEmailId [script]

## PC_ExtractCruiseEntitiesFromInitialUserMessage [generativeai]
- nodeId: `nd-gai-06ea9578-fcc1-4d0b-b572-5443dfb30ded`
- DEFAULT -> PC_Script_ProcessExtractedEntities [script]

## PC_Common_1_Script_DeleteEmailId [script]
- nodeId: `nd-scr-1be023f6-1ed2-4495-af87-bfaf64e0b1cc`
- DEFAULT -> PC_Common_1_Entity_Emailid [entity]

## PC_Script_ProcessExtractedEntities [script]
- nodeId: `nd-scr-f48234dd-5c12-4c96-9025-84c8e36cc694`
- DEFAULT -> HD_VesselLookupAgent [aiassist]

## HD_VesselLookupAgent [aiassist]
- nodeId: `nd-ais-82bd606e-9586-4a79-b45a-52af68af59e8`
- DEFAULT -> PC_Cruise_Entities [script]

## PC_Cruise_Entities [script]
- nodeId: `nd-scr-b08a0968-68c7-48a0-b35b-e554c57de008`
- DEFAULT -> HD_CruiseDateOrchestrator [aiassist]

## HD_CruiseDateOrchestrator [aiassist]
- nodeId: `nd-ais-e2902841-bb1a-46ec-85af-d2af5bf271d6`
- DEFAULT -> PC_CruiseDate_Entities [script]

## PC_CruiseDate_Entities [script]
- nodeId: `nd-scr-630ec151-5eb3-4533-85e4-4a349e73a970`
- DEFAULT -> PC_Common_1_Script_VariablestoBotUserSession [script]

## PC_Common_1_Script_VariablestoBotUserSession [script]
- nodeId: `nd-scr-5fde3a24-0818-4eae-b575-f6b33d0be907`
- DEFAULT -> PC_Common_2_Msg_DisplayMsg [message]

## PC_Common_2_Msg_DisplayMsg [message]
- nodeId: `nd-msg-731685b5-ee03-47e1-ad03-49b554a11f34`
- DEFAULT -> PC_Common_2_Entity_NameAsPerSpaRecords [entity]

## PC_Common_2_Entity_NameAsPerSpaRecords [entity]
- nodeId: `nd-ent-09f55a4c-77ea-40ae-b853-aae21537e567`
- DEFAULT -> PC_HomeDelivery_Agent_SpaRecordName [aiassist]

## PC_HomeDelivery_Agent_SpaRecordName [aiassist]
- nodeId: `nd-ais-531b7983-1190-48d8-aeab-c08cea2118b1`
- DEFAULT -> PC_HomeDelivery_Script_FullName [script]

## PC_HomeDelivery_Script_FullName [script]
- nodeId: `nd-scr-cff48c99-9d33-41c7-bc41-e49cdfb90a06`
- DEFAULT -> PC_HomeDelivery_PromptNode [generativeai]

## PC_HomeDelivery_PromptNode [generativeai]
- nodeId: `nd-gai-13ea79b4-8631-4484-a614-f2fa14bbbfcc`
- DEFAULT -> PC_HomeDelivery_Script_SaveEntities [script]

## PC_HomeDelivery_Script_SaveEntities [script]
- nodeId: `nd-scr-aa8ac29c-c44e-4486-a2d5-a35bfd437ba8`
- DEFAULT -> PC_Home_Delivery_Agent_CabinNumber [aiassist]

## PC_Home_Delivery_Agent_CabinNumber [aiassist]
- nodeId: `nd-ais-003c55cd-7682-4906-a3e0-937141a06950`
- DEFAULT -> PC_HomeDelivery_Script_CabinNumber [script]

## PC_HomeDelivery_Script_CabinNumber [script]
- nodeId: `nd-scr-8d5406f2-9805-4f70-b3a7-a7f40cf70012`
- IF  -> Cancel_Mid_Workflow [intent]
- DEFAULT -> PC_HomeDelivery_Msg_ReturnPolicyInfo [message]

## Cancel_Mid_Workflow [intent]
- nodeId: `nd-int-9e168e7d-cf5a-46a2-ba21-65a1992a1024`
- DEFAULT -> end

## PC_HomeDelivery_Msg_ReturnPolicyInfo [message]
- nodeId: `nd-msg-6463409a-60e3-4931-b3ff-71650389a37c`
- DEFAULT -> PC_HomeDelivery_Script_SetRequestDate [script]

## PC_HomeDelivery_Script_SetRequestDate [script]
- nodeId: `nd-scr-b2dbfe14-6333-418c-ba26-766c42011adb`
- DEFAULT -> PC_HomeDelivery_Agent_PurchasedDate [aiassist]

## PC_HomeDelivery_Agent_PurchasedDate [aiassist]
- nodeId: `nd-ais-861f3a98-a658-4774-aa29-18d1a2523f6e`
- DEFAULT -> PC_HomeDelivery_Script_DateValidations [script]

## PC_HomeDelivery_Script_DateValidations [script]
- nodeId: `nd-scr-3d967c2e-41e4-4423-9603-583c86988b61`
- IF  -> PC_HomeDelivery_Msg_FutureDate [message]
- IF  -> Cancel_Mid_Workflow [intent]
- IF  -> Message0075 [message]
- DEFAULT -> PC_HomeDelivery_Entity_DeliveryType [entity]

## PC_HomeDelivery_Msg_FutureDate [message]
- nodeId: `nd-msg-e16be33b-4e2b-4f9e-a902-f896a6946f30`
- DEFAULT -> Script0050 [script]

## Message0075 [message]
- nodeId: `nd-msg-bed7cf80-6249-4d68-b13b-281779dab262`
- DEFAULT -> Script0050 [script]

## PC_HomeDelivery_Entity_DeliveryType [entity]
- nodeId: `nd-ent-e7f9fb85-d683-4223-9df4-9bb5347fdee1`
- DEFAULT -> PC_HomeDelivery_Entity_IssueReasonButtons [entity]

## Script0050 [script]
- nodeId: `nd-scr-772b6a4c-470a-400d-9026-a5b17719b486`
- DEFAULT -> PC_HomeDelivery_Entity_PurchasedDate [entity]

## PC_HomeDelivery_Entity_IssueReasonButtons [entity]
- nodeId: `nd-ent-8e7c1b21-3d68-4c82-a00d-981e3dbcdeac`
- IF  -> PC_HomeDelivery_Entity_Reason [entity]
- DEFAULT -> PC_HomeDelivery_Script_IssueResonButtonsValidations [script]

## PC_HomeDelivery_Entity_PurchasedDate [entity]
- nodeId: `nd-ent-006ce6cf-c4ae-42ac-98b0-e03f38eb2b7a`
- DEFAULT -> PC_HomeDelivery_Script_DateValidations [script]

## PC_HomeDelivery_Entity_Reason [entity]
- nodeId: `nd-ent-d7a494bc-2348-421d-9997-61d1991d9432`
- DEFAULT -> PC_HomeDelivery_Script_IssueResonButtonsValidations [script]

## PC_HomeDelivery_Script_IssueResonButtonsValidations [script]
- nodeId: `nd-scr-a812f4dc-36a1-43d1-a125-42822239f7eb`
- DEFAULT -> PC_HomeDelivery_Agent2_ReturnDetails [aiassist]

## PC_HomeDelivery_Agent2_ReturnDetails [aiassist]
- nodeId: `nd-ais-d330773e-a93f-41c6-94e2-f396b91483a8`
- DEFAULT -> PC_HomeDelivery_Script_AgentNodeDataValidation [script]

## PC_HomeDelivery_Script_AgentNodeDataValidation [script]
- nodeId: `nd-scr-9412ca75-d609-4183-8352-5b2e16309e3d`
- IF  -> Cancel_Mid_Workflow [intent]
- DEFAULT -> Phonenumber_Logic [script]

## Cancel_Mid_Workflow [intent]
- nodeId: `nd-int-d253ec5f-204c-4bf3-a891-e1977c210e76`
- DEFAULT -> end

## Phonenumber_Logic [script]
- nodeId: `nd-scr-29c2165a-c538-49dd-894f-d0d2b0f31e39`
- IF  -> PC_HomeDelivery_Entity_PhoneNumber [entity]
- DEFAULT -> PC_HomeDelivery_Agent_ProductCount [aiassist]

## PC_HomeDelivery_Entity_PhoneNumber [entity]
- nodeId: `nd-ent-eca57b11-320c-45ba-89ff-0589e7bd8143`
- DEFAULT -> Script0084 [script]

## PC_HomeDelivery_Agent_ProductCount [aiassist]
- nodeId: `nd-ais-d6662b7b-1ecb-4551-9442-79842e1c3349`
- DEFAULT -> PC_HomeDelivery_Script_ProductCount [script]

## Script0084 [script]
- nodeId: `nd-scr-775bc82c-083b-41af-8435-6e4788593cd8`
- DEFAULT -> PC_HomeDelivery_Agent_ProductCount [aiassist]

## PC_HomeDelivery_Script_ProductCount [script]
- nodeId: `nd-scr-dd3222a6-7353-4368-8d7a-d1fd60d9f32c`
- DEFAULT -> PC_HomeDelivery_Agent_ProductDetails [aiassist]

## PC_HomeDelivery_Agent_ProductDetails [aiassist]
- nodeId: `nd-ais-1e7bb441-b34a-402a-a8a8-1264d5464f50`
- DEFAULT -> PC_HomeDelivery_Script_SavingAgentData [script]

## PC_HomeDelivery_Script_SavingAgentData [script]
- nodeId: `nd-scr-2f8c7920-ce7e-4eea-9a99-69331d509332`
- IF  -> Cancel_Mid_Workflow [intent]
- DEFAULT -> PC_HomeDelivery_Logic_MoreInfo_RC_and_Celebrity [logic]

## PC_HomeDelivery_Logic_MoreInfo_RC_and_Celebrity [logic]
- nodeId: `nd-lgc-5ca13de3-7862-4b32-bf6a-8724f9ce3713`
- IF context.session.BotUserSession.usr_cruise_line eq "CELEBRITY" or context.session.BotUserSession.usr_cruise_line eq "ROYAL CARIBBEAN INTERNATIONAL" -> PC_HomeDelivery_Entity_BookingNumber [entity]
- IF context.session.BotUserSession.usr_cruise_line neq "CELEBRITY" or context.session.BotUserSession.usr_cruise_line neq "ROYAL CARIBBEAN INTERNATIONAL" -> PC_Common_Entity_AdditionalDescription [entity]
- DEFAULT -> PC_Common_Entity_AdditionalDescription [entity]

## PC_HomeDelivery_Entity_BookingNumber [entity]
- nodeId: `nd-ent-2eac546b-9434-4c31-bf4a-9126dbad1747`
- DEFAULT -> PC_HomeDelivery_BookingClassifier [generativeai]

## PC_Common_Entity_AdditionalDescription [entity]
- nodeId: `nd-ent-a7463f56-ba8c-4577-890f-458d5a5bc538`
- DEFAULT -> PC_Common_3_Message_StartMessage [message]

## PC_HomeDelivery_BookingClassifier [generativeai]
- nodeId: `nd-gai-91181247-19fe-461f-bb8d-31c9d0550f0b`
- DEFAULT -> PC_HomeDelivery_Script_BookingRoute [script]

## PC_Common_3_Message_StartMessage [message]
- nodeId: `nd-msg-7e733ef7-27b6-464f-82e0-fa9a9ac220f0`
- DEFAULT -> HomeDelivery_Entity_Upload [entity]

## PC_HomeDelivery_Script_BookingRoute [script]
- nodeId: `nd-scr-5f2f7636-f91e-41bb-bd8b-5be9bce60ede`
- IF  -> PC_HomeDelivery_Entity_BookingNumber [entity]
- IF  -> PC_HomeDelivery_Msg_BookingNumberFallback [message]
- DEFAULT -> PC_HomeDelivery_Entity_CreditCardInfo [entity]

## HomeDelivery_Entity_Upload [entity]
- nodeId: `nd-ent-173ec335-6d53-4b24-9225-ba7f9ac91bd1`
- DEFAULT -> HomeDelivery_Script_PrepareAzureData [script]

## PC_HomeDelivery_Msg_BookingNumberFallback [message]
- nodeId: `nd-msg-95038e9b-6a8f-4e3f-b1d1-652988783dc4`
- DEFAULT -> PC_HomeDelivery_Entity_CreditCardInfo [entity]

## PC_HomeDelivery_Entity_CreditCardInfo [entity]
- nodeId: `nd-ent-460568bf-b4e2-4782-a7ce-84a2fa831d08`
- DEFAULT -> Script0073 [script]

## HomeDelivery_Script_PrepareAzureData [script]
- nodeId: `nd-scr-af466da0-4688-494c-bff8-929863ef0420`
- IF  -> PC_HomeDelivery_ValidationScript [script]
- DEFAULT -> HomeDelivery_Service_ScanUpload [service]

## Script0073 [script]
- nodeId: `nd-scr-e36da692-72ca-409a-8726-cb99ab701ac0`
- DEFAULT -> PC_HomeDelivery_Script_Booking-and-Credit_Info [script]

## PC_HomeDelivery_ValidationScript [script]
- nodeId: `nd-scr-b92008e1-5ded-47b5-ab0d-2ac216feb264`
- DEFAULT -> PC_HomeDelivery_Script_PrepareZendeskData [script]

## HomeDelivery_Service_ScanUpload [service]
- nodeId: `nd-srv-65614e0e-84d9-4aa2-828e-fcb350413874`
- DEFAULT -> HomeDelivery_Script_HandleScanResult [script]

## PC_HomeDelivery_Script_Booking-and-Credit_Info [script]
- nodeId: `nd-scr-6a3baafa-42d3-49e2-9001-64ec80ce236c`
- DEFAULT -> PC_Common_Entity_AdditionalDescription [entity]

## PC_HomeDelivery_Script_PrepareZendeskData [script]
- nodeId: `nd-scr-4c0e3915-e595-41eb-be64-4ecf76215c81`
- DEFAULT -> PC_HomeDelivery_Service_CreateTicket [service]

## HomeDelivery_Script_HandleScanResult [script]
- nodeId: `nd-scr-6a56bb44-44db-4345-b106-6be84d85596b`
- IF  -> HomeDelivery_Message_MalwareError [message]
- IF  -> HomeDelivery_Message_FileTypeError [message]
- IF  -> HomeDelivery_Message_UploadError [message]
- DEFAULT -> PC_HomeDelivery_ValidationScript [script]

## PC_HomeDelivery_Service_CreateTicket [service]
- nodeId: `nd-srv-2b14f82e-90de-4314-b671-6e79b0dd2fdd`
- IF  -> PC_HomeDelivery_Script_ConversationPrivateNote [script]
- IF  -> PC_HomeDelivery_Message_TicketFailed [message]
- DEFAULT -> end

## HomeDelivery_Message_MalwareError [message]
- nodeId: `nd-msg-f71a442a-6331-43fa-bc63-9ae16129c8ce`
- DEFAULT -> HomeDelivery_Entity_Upload [entity]

## HomeDelivery_Message_FileTypeError [message]
- nodeId: `nd-msg-632e990b-0ec6-4131-b522-dfa0beafd26d`
- DEFAULT -> HomeDelivery_Entity_Upload [entity]

## HomeDelivery_Message_UploadError [message]
- nodeId: `nd-msg-0ce8be58-6ba8-4c6a-b1a0-478592d22e9e`
- DEFAULT -> HomeDelivery_Entity_Upload [entity]

## PC_HomeDelivery_Script_ConversationPrivateNote [script]
- nodeId: `nd-scr-03dacd59-3e9c-4687-ba1a-017a8afdbe62`
- DEFAULT -> PC_HomeDelivery_Service_ConversationPrivateNote [service]

## PC_HomeDelivery_Message_TicketFailed [message]
- nodeId: `nd-msg-579b4a70-566f-4b7c-8102-209737ce2be3`
- DEFAULT -> PC_HomeDelivery_Script_ClearData [script]

## PC_HomeDelivery_Service_ConversationPrivateNote [service]
- nodeId: `nd-srv-73c81f24-9854-4377-b5e5-19128327b6cb`
- DEFAULT -> PC_HomeDelivery_Logic_ForAttachment [logic]

## PC_HomeDelivery_Script_ClearData [script]
- nodeId: `nd-scr-92d9eb9b-773a-4f41-9391-2fd0bfa2524a`
- DEFAULT -> HomeDelivery_FeedBackSurvey [intent]

## PC_HomeDelivery_Logic_ForAttachment [logic]
- nodeId: `nd-lgc-a36af7b6-7cfd-433a-b42d-84705061d63f`
- IF  -> PC_HomeDelivery_Logic_ValidationStatus [logic]
- DEFAULT -> PC_HomeDelivery_Script_PrivateNotePayload [script]

## HomeDelivery_FeedBackSurvey [intent]
- nodeId: `nd-int-6c5e5990-d48a-49dc-8b9d-ee9ae245fb25`
- DEFAULT -> end

## PC_HomeDelivery_Logic_ValidationStatus [logic]
- nodeId: `nd-lgc-0da9038e-3f8f-44df-9f52-cae6e0677ebe`
- IF context.session.BotUserSession.returnsValidationStatus eq "PASS" and context.session.BotUserSession.transactionValidationStatus eq "PASS" -> PC_HomeDelivery_Script_ReturnDocuments [script]
- IF context.session.BotUserSession.returnsValidationStatus eq "PASS" and context.session.BotUserSession.transactionValidationStatus eq "FAIL" -> PC_HomeDelivery_Script_ReturnDocuments [script]
- IF context.session.BotUserSession.returnsValidationStatus eq "FAIL" and context.session.BotUserSession.transactionValidationStatus eq "PASS" -> PC_HomeDelivery_ReturnsDocumentFail [script]
- DEFAULT -> PC_HomeDelivery_DocumentCreationFail [script]

## PC_HomeDelivery_Script_PrivateNotePayload [script]
- nodeId: `nd-scr-00a23fe7-e8f8-4fae-933a-f5af2256bbab`
- DEFAULT -> PC_HomeDelivery_Service_PrivateNoteAttachmentAPI [service]

## PC_HomeDelivery_Script_ReturnDocuments [script]
- nodeId: `nd-scr-78e0a545-a410-4fc5-953d-d9d767089c6a`
- DEFAULT -> DocumentCreation_Service_Returns [service]

## PC_HomeDelivery_ReturnsDocumentFail [script]
- nodeId: `nd-scr-5b8a8e87-0f72-4d5e-94f5-0e3d4a6dcfdb`
- DEFAULT -> PC_HomeDelivery_Service_PrivateNote [service]

## PC_HomeDelivery_DocumentCreationFail [script]
- nodeId: `nd-scr-a9a6f400-9eb2-49af-9b48-4952b5df674c`
- DEFAULT -> PC_HomeDelivery_Service_PrivateNote [service]

## PC_HomeDelivery_Service_PrivateNoteAttachmentAPI [service]
- nodeId: `nd-srv-607807d8-b702-40ac-8b13-0204f85bd97c`
- DEFAULT -> PC_HomeDelivery_Logic_ValidationStatus [logic]

## DocumentCreation_Service_Returns [service]
- nodeId: `nd-srv-8405db9d-4e37-4b68-898e-0b74ab929faa`
- IF  -> PC_HomeDelivery_Logic_TransactionValidationStatus [logic]
- DEFAULT -> PC_HomeDelivery_Script_ReturnsErrorHandling [script]

## PC_HomeDelivery_Service_PrivateNote [service]
- nodeId: `nd-srv-9f842538-11b8-4721-b517-2bd89d6fe07a`
- DEFAULT -> PC_HomeDelivery_Logic_TransactionValidationStatus [logic]

## PC_HomeDelivery_Service_PrivateNote [service]
- nodeId: `nd-srv-a2193aa5-2d2a-439e-9776-55eb8ff176e7`
- DEFAULT -> PC_HomeDelivery_ThanksMessage [message]

## PC_HomeDelivery_Logic_TransactionValidationStatus [logic]
- nodeId: `nd-lgc-2bce8988-69c0-49bc-9915-e963d163a03a`
- IF  -> PC_HomeDelivery_DocumentCreation_Service_Transcations [service]
- DEFAULT -> PC_HomeDelivery_Transactions_DocumentFail [script]

## PC_HomeDelivery_Script_ReturnsErrorHandling [script]
- nodeId: `nd-scr-f18a1227-8133-4a3a-910b-197f273a2627`
- DEFAULT -> PC_HomeDelivery_Service_ErrorInternalNode [service]

## PC_HomeDelivery_ThanksMessage [message]
- nodeId: `nd-msg-b9ffcf51-1f9b-4f6c-962f-c4789acda520`
- DEFAULT -> PC_HomeDelivery_Script_ClearData [script]

## PC_HomeDelivery_DocumentCreation_Service_Transcations [service]
- nodeId: `nd-srv-51251ba2-17e5-452d-bb41-acf8b46700f2`
- IF  -> PC_HomeDelivery_ThanksMessage [message]
- DEFAULT -> PC_HomeDelivery_Script_TransactionsErrorHandling [script]

## PC_HomeDelivery_Transactions_DocumentFail [script]
- nodeId: `nd-scr-aa4e426e-f419-4a9c-a32d-2bc49d6b15a9`
- DEFAULT -> PC_HomeDelivery_Service_PrivateNote [service]

## PC_HomeDelivery_Service_ErrorInternalNode [service]
- nodeId: `nd-srv-71b40a6b-9172-4852-b172-eb560b5e1e6c`
- DEFAULT -> PC_HomeDelivery_Logic_TransactionValidationStatus [logic]

## PC_HomeDelivery_Script_TransactionsErrorHandling [script]
- nodeId: `nd-scr-4378422c-c151-4a25-ae06-929297a71ec0`
- DEFAULT -> PC_HomeDelivery_Service_ErrorInternalNode [service]

## PC_HomeDelivery_Service_PrivateNote [service]
- nodeId: `nd-srv-1da438f6-0d73-4e07-90c2-cedfe8507c4d`
- DEFAULT -> PC_HomeDelivery_ThanksMessage [message]

## PC_HomeDelivery_Service_ErrorInternalNode [service]
- nodeId: `nd-srv-2dea776c-8c0e-4558-9232-712c58a89f8a`
- DEFAULT -> PC_HomeDelivery_ThanksMessage [message]

## Not reachable from intent0
- HD_TriggerAgenticAppForItiernaryData [service] (`nd-srv-3ce65c0b-552c-43d4-bb3f-7e255470bcb2`)
- HD_TriggerAgenticAppForVesselData [service] (`nd-srv-81406f60-d1cd-4d39-aa76-492fe98353c5`)
