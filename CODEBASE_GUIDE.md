# Codebase guide

A reference for anyone reading or extending the Marina bot: where the AI model is used, where the outside services are
called, what each file does, where the conversation variables live, and how the Zendesk ticket and the two documents are
built from them. For setup and the end-to-end flow, see [README.md](README.md).

All paths are under `src/marina-bot/`.

## 1. The picture in one minute

- Foundry hosts the bot and sends **one request per customer message**. The bot keeps nothing in memory between messages.
- Each message runs a **workflow graph** once. State (two dictionaries, `session` and `entities`) is **loaded at the start
  and saved at the end** of every message.
- A step that needs an answer asks its question and records its own id (`session["dialog_step"]`). The next message resumes
  at exactly that step.
- Dialog control is ordinary Python. The **AI model** is used in six places (section 2) and only ever **reads** text into
  typed fields; code decides what happens next. **Outside services** are called from four client files (section 3).
- The conversation runs from the first message to a Zendesk ticket with its attachments and two documents:
  intake, ship, cruise dates, purchase details, products, "anything else?", file upload, ticket, documents, thank-you.

## 2. Where the AI model is used

Six places, all using the **same Foundry model deployment** through one client built in `main.py`.

| # | Where | What it does | Style |
|---|---|---|---|
| 1 | `orchestrator.py`, `IntentClassifier` | Reads the customer's message and answers `PRODUCT_RETURN` or `OTHER`. Runs only when no dialog is active | One-shot call |
| 2 | `shared/flow.py`, `PromptNode`, used by the `pr_extract` step | Pulls ship, cruise line and dates out of the **first message**, using `prompts/extract_cruise_entities.md` | One-shot call, JSON text |
| 3 | `shared/agent_node.py`, `FoundryAgentRunner`, used by the `pr_vessel_agent` step | The vessel agent: calls the ship-lookup tool and asks the customer questions across several messages. Prompts: `prompts/vessel_identification.md`, `prompts/vessel_step0.md` | Model with tools |
| 4 | `shared/llm_dates.py`, `FoundryDateReader` | Fallback for dates the code parser cannot read. Returns day, month and year as separate typed fields; code validates them | Structured output |
| 5 | `shared/flow.py`, `PromptNode`, used by the `pd_extract` step | Pulls cabin number, purchase date, phone, country, product count and products out of the **first message**, using `prompts/extract_return_details.md`. `return_extraction.py` validates every value | One-shot call, JSON text |
| 6 | `shared/llm_products.py`, `FoundryProductReader`, used by `pd_ask_product_count` and `pd_ask_products` | Reads **one reply** about the products: names, quantities, conditions, the expected product, "that's all". It never decides what to ask next; `product_details.py` does. A bare number or a condition word is read by code without calling it | Structured output |

`main.py` builds the helpers from one `FoundryChatClient`: `make_prompt_runner` (for 1, 2 and 5), `FoundryAgentRunner`
(for 3), `FoundryDateReader` (for 4) and `FoundryProductReader` (for 6). Calls 1, 2 and 5 are stateless one-shot calls; the
conversation history is put into the prompt text where needed. Nothing the model returns is trusted: every value is
validated by code before it is stored.

## 3. Where the outside services are

The dialogs never make HTTP calls themselves. Every call lives in one of four client files, and each client keeps secrets out
of its error messages (status code only).

| Call | Purpose | Client | Used by |
|---|---|---|---|
| `POST {OSW_TOKEN_URL}` | OAuth client-credentials login, cached per API until a minute before expiry | `shared/osw.py` | every OSW call below |
| `GET /info/vessels?filter=co(name,"…")` | Search vessels by name (case-insensitive) | `shared/osw.py` | vessel agent's lookup tool (`vessel.py`) |
| `GET /info/cruiselines?filter=co(name,"…")` | Find a cruise line when the customer gave only a line | `shared/osw.py` | same tool |
| `GET /info/cruiselines/{id}/vessels` | List a cruise line's ships | `shared/osw.py` | same tool |
| `GET /info/cruiselines/{id}` | Look up a cruise line name when a vessel record has only its id | `shared/osw.py` | same tool |
| `GET /master/itinerary/vessels/{id}/embarkation/date/{yyyymmdd}` | A voyage that **started** on the date | `shared/osw.py` | `cruise_dates.py`, step `cd_validate` |
| `GET /master/itinerary/vessels/{id}/any/date/{yyyymmdd}` | Voyages that **contain** the date; the nearest one is chosen | `shared/osw.py` | same step, only if there is no exact match |
| `POST {ATTACHMENT_API_URL}/api/upload` | Scan the customer's file(s) for malware and file type, stage them in Zendesk; returns upload tokens | `shared/attachments.py` | `ticket.py`, step `pd_ask_upload` |
| `POST {ZENDESK_BASE_URL}/api/v2/tickets.json` | Create the return ticket (never retried blindly) | `shared/zendesk.py` | `ticket.py`, step `pd_create_ticket` |
| `GET {ZENDESK_BASE_URL}/api/v2/tickets.json?external_id=…` | Look for a ticket this request already created, before a retry | `shared/zendesk.py` | same step |
| `PUT {ZENDESK_BASE_URL}/api/v2/tickets/{id}.json` | Add a private comment: the transcript, the attachments, a validation or API-error note | `shared/zendesk.py` | `pd_create_ticket`, `pd_finalise_request` |
| `POST {DOCUMENT_API_URL}/cscbot/post-voyage/products-return/documents/requests` | Request the products-return document for the ticket (OAuth, returns scope) | `shared/documents.py` | `ticket.py`, step `pd_finalise_request` |
| `POST {DOCUMENT_API_URL}/cscbot/post-voyage/transactions/documents/requests` | Request the transactions document for the ticket (OAuth, transactions scope) | `shared/documents.py` | same step |

The vessels and itinerary APIs use **different OAuth scopes**, and so do the two document requests, so each client keeps one
token per scope. A `401` triggers one token refresh and retry; a `404` on the voyage endpoints means "no match". The
Zendesk and attachment calls use a static credential from the environment.

The only other external store is the conversation state (section 5): Azure Blob Storage when hosted.

## 4. File by file

### Top level

| File | What it does |
|---|---|
| `main.py` | Start-up. Builds the Foundry client and the model helpers, the OSW, Zendesk, attachment and document clients, and the `Deps` bundle (any missing setting stops start-up with the names). `parse_response` turns each request into a `TurnInput`: the message text, the state keys, and any `input_file` / `input_image` items that carry an https link. A fresh workflow is built for every request. Sets the checkpoint allowlist (`models:TurnInput`, `models:Turn`) and starts the server on port 8088 |
| `models.py` | `TurnInput`: the raw message, the keys to load and save state, and the attached files. `Turn`: the envelope passed between steps. It holds `text`, `session`, `entities`, `route` (the next step), `resuming` (true when `text` answers the question asked last turn), `replies` (the bot's lines) and `attachments` (`[{url, name}]`, plus a count of unusable ones) |
| `orchestrator.py` | The top-level workflow. `TurnEntry` loads the state and picks the route (active dialog, or the classifier). `IntentClassifier` is model call #1. `Fallback` answers non-return topics. `Persist` appends the exchange to the short history and to the full transcript, saves the state and returns the reply |
| `chat.py` | A terminal client for local testing, with `/new`, `/attach <https-url>` and `/quit`. Not part of the deployed bot |
| `ui.py` | Local backend-for-frontend (standard library). Serves `web/`, forwards each chat message to the bot (`BOT_URL`, default :8088; `BOT_AUTH=azure` sends an Entra token so it can call the deployed agent) and returns the reply plus the suggested buttons read from the saved state. With `UI_DEBUG=true` it also serves `/dev` and `/api/debug` (trace + variables). 127.0.0.1 only, no login. Not part of the deployed bot |
| `web/widget.js`, `web/widget.css` | The embeddable chat widget in the style of the Kore/Serena web chat: launcher, teaser bubbles, header, name + time labels, button chips, footer. Plain JavaScript, no debug code. `MarinaChat.init({api, name, color, container, ...})` (options at the top of the file) |
| `web/demo.html`, `web/dev.html` | `demo.html`: a host page with the floating widget. `dev.html` (only with `UI_DEBUG`): Kore dev-tool style page, Debug Logs and Session Context & Variables tabs beside the chat |
| `shared/trace.py` | The execution trace behind the debug panel. Off unless `DEBUG_TRACE=true`. Records turn start, node transitions, waits, model calls and API calls with timings and error type/status (never the error text), and the variables each message changed; keeps the last 40 messages in the saved state. Buttons offered by a question (`Turn.suggest`) are saved as `session["suggestions"]` whether or not tracing is on |
| `.env.example` | Every setting, with the sandbox Zendesk ids filled in. Copy to `.env` |
| `Dockerfile`, `.dockerignore`, `.azdignore` | How the Foundry hosted agent is built (uv, Python 3.13, port 8088) and which local-only files (`chat.py`, `ui.py`, `.env`) stay out of it |

### `dialogs/product_return/`: the Product Return dialog

| File | What it does |
|---|---|
| `workflow.py` | The dialog's flowchart. `ProductReturnEntry` decides "start fresh (and start a new transcript) or resume the paused step". Wires every step and every allowed transition |
| `intake_scripts.py` | Plain-Python clerk work: remember the first message once, and clean the extraction output (ignore vague words such as "the ship", normalise dates, keep a date with no year as typed so the date step can ask for the year) |
| `vessel.py` | The vessel agent: a pre-step that syncs the notes, the prompt builder, the lookup tool (calls OSW; returns nothing, one vessel, or a list), and a post-step that sets the vessel id, name and cruise line, counts failed lookups, and after the second miss accepts the customer's value. Also `save_cruise_entities`, which copies the results into the long-lived `usr_*` notes |
| `cruise_dates.py` | The date nodes (`cd_start`, `cd_ask_start`, `cd_validate`, `cd_confirm_nearest`, `cd_ask_end`, `cd_finish`) and a typed `CruiseDatesState` stored under `session["cruiseDates"]`. `cd_finish` publishes `start_date`, `end_date`, `usr_start_date`, `usr_end_date` and `dateCompleted` |
| `purchase_details.py` | The purchase-details nodes (`pd_*`): purchaser name, second extraction, cabin number, policy note, purchase date, delivery type, return reason (and the "Other" description), country, phone number and cancel. `QuestionNode` is the shared base for every question in the dialog's later stages. A typed `PurchaseDetailsState` (ask and failure counters, partial dates, the last rejected date, the product-question bookkeeping) is stored under `session["purchaseDetails"]`. `start_purchase_details` clears the previous answers of this stage (including the ticket and document results) so a second return starts clean |
| `product_details.py` | Product count and product details (`pd_ask_product_count`, `pd_ask_products`, `pd_confirm_products`, `pd_reset_products`, `pd_save_products`). The decision logic is a set of small pure functions (`next_question`, `apply_reading`, `is_complete`) that fill product slots from what the model read; `save_products` builds `productsToReturn` in the shape Kore's ticket script expects |
| `ticket.py` | "Anything else to add?" (`pd_ask_additional`), the file upload question (`pd_ask_upload`), the ticket step (`pd_create_ticket`) and the closing step (`pd_finalise_request`: attachment note, both documents, thank-you). `build_ticket_payload` and `build_description` are pure functions (Kore's `PrepareZendeskData`); `build_private_note` builds the transcript comment. Customer text is HTML-escaped |
| `return_documents.py` | Pure functions: which fields each document needs (`validate_documents`, Kore's `ValidationScript`), the two document payloads, the private notes for a missing field or an API error, and the failure tags |
| `return_extraction.py` | Port of Kore's `SaveEntities` script: validates the second extraction's output and stores cabin, raw purchase date, country, phone, product count, products, and "customer doesn't know" flags |
| `prompts/` | The prompt texts copied from Kore, one `.md` per prompt, with `{{placeholders}}` |

### `shared/`: building blocks used by every dialog

| File | What it does |
|---|---|
| `flow.py` | The node types: `ScriptNode`, `MessageNode`, `PromptNode` (model calls #2 and #5), `SlotNode` (ask and validate, retry with an error text), `ConfirmNode` (yes/no). The routing helpers `goto`, `pause` and `finish`. Every edge in the graph is gated on `turn.route == target id` |
| `agent_node.py` | `AgentNode`: pre-step, model call with tools, then "done, so continue" or "say the model's question and pause". `FoundryAgentRunner` is model call #3. The `end_orchestration` tool is checked when it is called, not when it is built |
| `cancel.py` | `is_cancel_request`: recognises "cancel", "stop this", "I don't want to continue" and similar, but not "cancel my subscription". Used by every question from the purchase details onwards |
| `dates.py` | The date parser. Formats, ranges, partial dates, bare years, skip phrases, yes/no, impossible dates, and the "not in the future" rule (one day of tolerance). Never calls a model |
| `validators.py` | Name, email, purchaser name, cabin number, phone, delivery type, return reason (the five reasons with their Zendesk and API values), quantity, condition and "that's all" parsers |
| `countries.py` | Country names and aliases; turns "I live in the UK" into "United Kingdom" |
| `llm_dates.py` | Model call #4 and the validation of its typed answer |
| `llm_products.py` | Model call #6 and the validation of its typed answer (`ProductReading`) |
| `osw.py` | The OneSpaWorld vessel and voyage API client and all response parsing (section 3) |
| `zendesk.py` | The Zendesk client and its settings (`ZendeskConfig.from_env`, including the ticket form, brand, group and field ids): create ticket, private note (with optional upload tokens), find by external id. Errors carry the status code, never the response body |
| `attachments.py` | `extract_attachments` (files with https links from the request items), `AttachmentClient` (the scan-and-stage function), its settings, and the `AttachmentBlocked` / `AttachmentError` outcomes |
| `documents.py` | `DocumentClient`: OAuth client credentials (one token per scope, one refresh on a 401) and the two document requests; `error_detail` follows Kore's error-text order |
| `htmltext.py` | `esc`: HTML-escapes customer and API text before it goes into a ticket |
| `deps.py` | One bundle of outside connections: the one-shot model call, the agent runner, the OSW, Zendesk, attachment and document clients, the clock, and the optional date and product readers |
| `transcript.py` | The conversation transcript: `record_turn` keeps one timed row per message in the session, `to_csv` renders Kore's transcript columns, `mask_text` replaces names, e-mails and phone numbers, `blob_path` names the file (`transcripts/<yyyy-mm-dd>/<conversation>.csv`). Settings: `TranscriptConfig` (`TRANSCRIPT_*`) |
| `state_store.py` | Loads and saves the conversation state and the transcript file (section 5): `BlobStateStore` (Azure Blob Storage, used when `STATE_BLOB_ACCOUNT_URL` is set, with the identity; or when `STATE_BLOB_CONNECTION_STRING` is set, a shared-key stopgap that wins over the identity and logs a warning), `FileStateStore` (local files), and `make_state_store()` which picks one. The methods are synchronous; the orchestrator calls them through `asyncio.to_thread` |
| `session.py` | `DialogContext`: the `session` and `entities` dictionaries, using Kore's key names |
| `prompts.py` | Fills `{{placeholders}}` in prompt files by plain text replacement (the prompts contain literal JSON braces, so Python formatting cannot be used) |

## 5. Where the session variables are stored

There are two layers:

1. **In memory during a message:** `turn.session` and `turn.entities`, two dictionaries that every step reads and edits in place.
2. **In storage between messages:** one JSON document per key. In Foundry (`STATE_BLOB_ACCOUNT_URL` set) it is a blob
   `state/<key>.json` in the container `STATE_BLOB_CONTAINER`, read and written with the agent's own identity; locally it is a file
   in `~/marina_state` (override with `MARINA_STATE_DIR`).
   `TurnEntry` (`orchestrator.py`) loads it; `Persist` (`orchestrator.py`) saves it. Nothing else touches storage.

**Which document:** a conversation has ONE key: the `conversation_id` when the client uses conversations, otherwise the platform's
session id (`request.scope.session_id`, the same for every message of a session). `parse_response` loads from that key (and from
the client's `previous_response_id` too, so state saved by an earlier version is found) and saves to that key only, so the state is
one document overwritten on each message. A failed message saves nothing, so the next try starts from the last good state.

**The transcript file** is a second document per conversation, `transcripts/<yyyy-mm-dd>/<key>.csv`, rewritten by `Persist`
after the state is saved (see `shared/transcript.py`). It is built from `session["transcript_rows"]` (raw text with a time) and
masked when written. Failing to write it is logged, never shown to the customer.

**Not saved:** the per-message flags in `Turn` (`route`, `resuming`, `replies`, `attachments`). They are rebuilt every time.
A file's upload tokens are saved (`zd_tokens_combined`), not the file.

### What is in the store, and who writes it

| Variable | Written by |
|---|---|
| `entities`: `PC_Common_1_Entity_Name`, `PC_Common_1_Entity_Emailid` | `pr_name`, `pr_email` |
| `session.piiEntities.name`, `.emailId` | `pr_redact_name`, `pr_redact_email` |
| `session.initialMessage` | `pr_initial_message` |
| `session.nodeOutputs` (raw extraction text) | `pr_extract`, `pd_extract` |
| `entities` and `session`: `ship_name`, `cruise_line`, `vessel_id`, plus the vessel counters and flags (`vesselLookupFailCount`, `lastVesselAttempt`, `lastCountedVesselValue`, `vesselSkippedFields`, `vesselForceContinue`, `vesselLookupInvoked`, `vesselCompleted`, `conversationState`) | `process_extracted_entities` (intake) and the vessel agent |
| `session.usr_ship_name`, `usr_cruise_line`, `usr_vessel_id` | `pr_cruise_entities` |
| `session.cruiseDates`, `usr_start_date`, `usr_end_date`, `dateCompleted`; `entities.start_date`, `end_date` | the `cd_*` nodes |
| `session.spa_record_name`, `piiEntities.sparecordname`, `piiEntities.nameAsPerSpa`; `entities.SpaRecordName` | `pd_ask_spa_name` |
| `session.CabinNumber` (text), `CabinNumbers` (list), `CabinNumberUnknown`; `entities.CabinNumber` | `pd_save_extraction`, `pd_ask_cabin` |
| `session.PurchasedDate` (MM/DD/YYYY or `unknown`), `purchaseDateFormatted`, `purchaseDateAPI`, `lastEnteredDate` (ISO), `isWithinReturnPolicyPeriod`, `requestedDate`; `entities.PurchasedDate` | `pd_set_request_date`, `pd_ask_purchase_date` |
| `session.deliveryType`; `entities.PC_HomeDelivery_Entity_DeliveryType` | `pd_ask_delivery` |
| `session.reasonDisplay`, `returnReason` (Zendesk value), `returnReasonMapped` (document API value), `otherReturnReason`; `entities.PC_HomeDelivery_Entity_IssueReasonButtons`, `…_Reason` | `pd_ask_reason`, `pd_ask_reason_text` |
| `session.Country`, `CountryUnknown`, `countryCompleted`; `entities.Country` | `pd_save_extraction`, `pd_ask_country` |
| `session.piiEntities.phoneNumber`, `PhoneNumberUnknown` | `pd_save_extraction`, `pd_ask_phone` |
| `session.ProductCount`, `ProductCountUnknown`, `productCountCompleted`; `entities.ProductCount` | `pd_save_extraction`, `pd_ask_product_count` |
| `session.products` (name, quantity, condition, expected product), `ProductsCollected`, `remainingQuantity`, `partialReturn`, `agentNodeExitPath`; `entities.ProductsCollected`, `AllProductsCaptured` | `pd_ask_products` (first filled by `pd_save_extraction`) |
| `session.productsToReturn`, `productsToReturnJSON`, `all_products_summary`, `collectedUnits`, `countMismatch`, `collectionOutcome`, `returnDetailsCompleted`, `productDataAnomaly` | `pd_save_products` |
| `session.extractionStatus`, other `…Unknown` flags | `pd_save_extraction` |
| `session.customerName`, `customerEmail`, `purchaseDetails` | `pd_vars` and the `pd_*` nodes |
| `entities.PC_Common_Entity_AdditionalDescription` | `pd_ask_additional` |
| `session.zd_tokens_combined` (upload tokens) | `pd_ask_upload` |
| `session.returnsValidationStatus`, `transactionValidationStatus`, `returnsFailedFieldsDisplay`, `transactionFailedFieldsDisplay`, `documentFailTags` | `pd_create_ticket` |
| `session.TicketId`, `ticketExternalId`, `ticketError`, `privateNoteFailed` | `pd_create_ticket` |
| `session.returnsDocumentStatus`, `transactionsDocumentStatus` (`created`, `failed`, `not_requested` or `skipped`) | `pd_finalise_request` |
| `session.transcript` (the whole request as text lines for the ticket's private note, last 400; cleared when a new request starts) | `Persist`, and the entry step |
| `session.transcript_rows` (one timed row per message, last 600) and `started_at`: what the transcript CSV is built from | `Persist` |
| `session.active_dialog`, `dialog_step` | the classifier, and any step that pauses |
| `session.conversationHistoryString` (last 10 lines), `session.messages` (last 20) | `Persist` |

## 6. How the ticket and the documents are built from the variables

Kore's Zendesk and document steps read the **same session keys** this bot stores, so the ported builders stay close to the
originals. All of them are pure functions over `session` and `entities` (in `ticket.py` and `return_documents.py`), so each
payload can be read on its own.

### The ticket (`build_ticket_payload`, `build_description`)

| Ticket part | Comes from |
|---|---|
| Requester name and email | `piiEntities.name`, `piiEntities.emailId` (fallbacks `Guest`, `guest@onespaworld.com`) |
| Body: request details | `initialMessage` |
| Body: phone, country, delivery type | `piiEntities.phoneNumber`, `Country`, `deliveryType` |
| Body: cruise line, ship, sail date | `usr_cruise_line`, `usr_ship_name`, `usr_start_date` |
| Body: spa guest name, cabin | `spa_record_name`, `CabinNumber` |
| Body: purchase date, request date | `purchaseDateFormatted`, `requestedDate` |
| Body: return reason (and "additional reason details") | `reasonDisplay` (`otherReturnReason` for Other) |
| Body: product count and products | `ProductCount`, `products` (incomplete ones show `N/A`) |
| Body: additional information | `entities.PC_Common_Entity_AdditionalDescription` |
| Body: booking number, card last four | always `N/A` (not asked) |
| Form, brand, group, tags, custom-field ids | `ZENDESK_*` settings (`TicketSettings`) |
| Custom fields | inquiry type `osw_product_return`; category from `deliveryType`; product reason from `returnReason`; return status `osw_return_requested`; created by `chatbot`; cruise line, ship, sail date (only a valid `YYYY-MM-DD`) |
| Tags | `ZENDESK_TAGS` (default `kore_ai,tag_website`) plus `documentFailTags` |
| `external_id` | `ticketExternalId`, made once per request |

### The two documents (`validate_documents`, `build_returns_payload`, `build_transactions_payload`)

| Document | Needs (all must be present, and not "unknown", "not provided" and similar) | Sent as |
|---|---|---|
| Returns | `spa_record_name`, `piiEntities.emailId`, `phoneNumber`, `Country`, `usr_cruise_line`, `usr_ship_name`, `CabinNumber`, `usr_start_date`, `purchaseDateAPI`, `requestedDate`, and at least one product with a name and a quantity | `referenceId` = ticket id; `guestFullname`, `eMail`, `phone`, `countryName`, `cruiseLineName`, `vesselName`, `cabinNumber`, `embarkationDate`, `purchaseDate`, `returnRequestDate`, `isWithinReturnPolicyPeriod`, `returnReasons` (+ `otherReturnReason`), `productsToReturn` (condition mapped to `unused` / `used`) |
| Transactions | `usr_vessel_id`, `usr_start_date`, `usr_end_date`, `spa_record_name`, `CabinNumber` | `referenceId` = ticket id; `vesselId`, `startDate`, `endDate`, `guestsFullNames`, `cabins` (a list) |

A document whose needs are not met is not requested: a private note on the ticket lists what is missing and the ticket
gets that document's failure tag. If the API refuses a request, a private note carries the API's error text.

### Settings, not session variables

The Zendesk base URL, credential, form, brand, group and field ids, the attachment function address and key, and the document
API address, client and scopes are **environment variables** (Kore's `env.*` settings), never stored in the session. See the
table in the README and `.env.example`.

### How a new downstream step would use them

Read from `turn.session` (for example `session["piiEntities"]["emailId"]`, `session["TicketId"]`), call a new client in
`shared/` built like `zendesk.py` or `documents.py` (settings from the environment, errors carrying a status only, a
protocol class in `deps.py` so tests can supply a fake), write the result back to the session, and let the next step read it.

## 7. Open decisions and gaps

1. **Booking number and credit card.** Not asked, so the ticket shows `N/A` and the documents omit them. If they are added
   later, decide first how to hold a card: the state files are plain, unencrypted JSON, so a full card must not be stored
   there (mask it, keep only the last digits, or hold it encrypted).
2. **The state store.** Blob Storage (encrypted at rest by Azure) replaces local files when hosted. Still to decide: a lifecycle rule
   that deletes old conversations (it holds the whole chat, name, email and phone), and whether Cosmos DB is needed for
   concurrency. `shared/state_store.py` has two methods, so it is a contained swap.
3. **Clearing variables between requests.** Starting a purchase stage clears the purchase answers, products, ticket and
   document results, and a new request starts a new transcript. The name, email, vessel and cruise dates are kept, so a
   second return in the same conversation skips those questions. Kore's `ClearData` step is not ported.
4. **The document API's exact contract.** The payloads follow Kore's templates, with the differences listed in the README.
   They have not been run against the real service, so the first live request may show a field the API wants differently
   (for example `clientMetadata`). Each is a small change in `return_documents.py`.
5. **Where files come from.** The attachment function needs an https link. A front end that lets the customer pick a file
   from their device has to upload it somewhere the function can fetch it, then send the link. The function must also
   restrict which hosts it downloads from.
6. **Feedback survey.** Kore's `HomeDelivery_FeedBackSurvey` after the thank-you is not ported.
7. **Secrets.** When hosted they are plain environment variables of the agent. Move them to Key Vault before production.
8. **Deployment.** The files exist but have not been run against the real subscription: see `DEPLOYMENT.md`.
9. **Tests.** The repo has none. The development suite (parsers, every conversation path, the four HTTP clients against mock
   servers) lives outside the repo and can be added back.
