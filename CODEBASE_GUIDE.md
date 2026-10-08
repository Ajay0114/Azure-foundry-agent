# Codebase guide

A reference for anyone reading or extending the Marina bot: where the AI model is used, where the APIs are called,
what each file does, where the conversation variables live, and which variables the later steps (Zendesk ticket,
document request) will need. For setup and the end-to-end flow, see [README.md](README.md).

All paths are under `src/marina-bot/`.

## 1. The picture in one minute

- Foundry hosts the bot and sends **one request per customer message**. The bot keeps nothing in memory between messages.
- Each message runs a **workflow graph** once. State (two dictionaries, `session` and `entities`) is **loaded at the start
  and saved at the end** of every message.
- A step that needs an answer asks its question and records its own id (`session["dialog_step"]`). The next message resumes
  at exactly that step.
- Dialog control is ordinary Python. The **AI model** is used in four places (section 2). **Real APIs** are called from one
  file (section 3).

## 2. Where the AI model is used

Four places, all using the **same Foundry model deployment** through one client built in `main.py`.

| # | Where | What it does | Style |
|---|---|---|---|
| 1 | `orchestrator.py`, `IntentClassifier` | Reads the customer's message and answers `PRODUCT_RETURN` or `OTHER`. Runs only when no dialog is active | One-shot call |
| 2 | `shared/flow.py`, `PromptNode`, used by the `pr_extract` step | Pulls ship, cruise line and dates out of the **first message**, using `prompts/extract_cruise_entities.md` | One-shot call, JSON text |
| 3 | `shared/agent_node.py`, `FoundryAgentRunner`, used by the `pr_vessel_agent` step | The vessel agent: calls the ship-lookup tool and asks the customer questions across several messages. Prompts: `prompts/vessel_identification.md`, `prompts/vessel_step0.md` | Model with tools |
| 4 | `shared/llm_dates.py`, `FoundryDateReader` | Fallback for dates the code parser cannot read. Returns day, month and year as separate typed fields; code validates them | Structured output |

`main.py` builds the three helpers from one `FoundryChatClient`: `make_prompt_runner` (for 1 and 2), `FoundryAgentRunner`
(for 3) and `FoundryDateReader` (for 4). Calls 1 and 2 are stateless one-shot calls; the conversation history is put
into the prompt text where needed.

## 3. Where the APIs are

All real HTTP calls live in **`shared/osw.py`**. The dialogs never make HTTP calls themselves.

| Call | Purpose | Used by |
|---|---|---|
| `POST {OSW_TOKEN_URL}` | OAuth client-credentials login, cached per API until a minute before expiry | every call below |
| `GET /info/vessels?filter=co(name,"…")` | Search vessels by name (case-insensitive) | vessel agent's lookup tool (`vessel.py`) |
| `GET /info/cruiselines?filter=co(name,"…")` | Find a cruise line when the customer gave only a line | same tool |
| `GET /info/cruiselines/{id}/vessels` | List a cruise line's ships | same tool |
| `GET /info/cruiselines/{id}` | Look up a cruise line name when a vessel record has only its id | same tool |
| `GET /master/itinerary/vessels/{id}/embarkation/date/{yyyymmdd}` | A voyage that **started** on the date | `cruise_dates.py`, step `cd_validate` |
| `GET /master/itinerary/vessels/{id}/any/date/{yyyymmdd}` | Voyages that **contain** the date; the nearest one is chosen | same step, only if there is no exact match |

The vessels and itinerary APIs use **different OAuth scopes**, so there is one token per scope. A `401` triggers one token
refresh and retry; a `404` on the voyage endpoints means "no match".

**Not built yet:** the Zendesk ticket, private notes, the document-request API, and file scan and upload. The only other
external store is the state file (section 5).

## 4. File by file

### Top level

| File | What it does |
|---|---|
| `main.py` | Start-up. Builds the Foundry client and the model helpers, the OSW client, and the `Deps` bundle. `parse_response` turns each request into a `TurnInput` (message text plus state keys). A fresh workflow is built for every request. Sets the checkpoint allowlist (`models:TurnInput`, `models:Turn`) and starts the server on port 8088 |
| `models.py` | `TurnInput`: the raw message plus the keys to load and save state. `Turn`: the envelope passed between steps. It holds `text`, `session`, `entities`, `route` (the next step), `resuming` (true when `text` answers the question asked last turn) and `replies` (the bot's lines) |
| `orchestrator.py` | The top-level workflow. `TurnEntry` loads the state and picks the route (active dialog, or the classifier). `IntentClassifier` is model call #1. `Fallback` answers non-return topics. `Persist` appends the exchange to the history, saves the state and returns the reply |
| `chat.py` | A terminal client for local testing. It is not part of the deployed bot |

### `dialogs/product_return/`: the Product Return dialog

| File | What it does |
|---|---|
| `workflow.py` | The dialog's flowchart. `ProductReturnEntry` decides "start fresh or resume the paused step". Wires every step and every allowed transition. `pr_next` is a placeholder that prints what was captured |
| `intake_scripts.py` | Plain-Python clerk work: remember the first message once, and clean the extraction output (ignore vague words such as "the ship", normalise dates, keep a date with no year as typed so the date step can ask for the year) |
| `vessel.py` | The vessel agent: a pre-step that syncs the notes, the prompt builder, the lookup tool (calls OSW; returns nothing, one vessel, or a list), and a post-step that sets the vessel id, name and cruise line, counts failed lookups, and after the second miss accepts the customer's value. Also `save_cruise_entities`, which copies the results into the long-lived `usr_*` notes |
| `cruise_dates.py` | The date nodes (`cd_start`, `cd_ask_start`, `cd_validate`, `cd_confirm_nearest`, `cd_ask_end`, `cd_finish`) and a typed `CruiseDatesState` stored under `session["cruiseDates"]`. `cd_finish` publishes `start_date`, `end_date`, `usr_start_date`, `usr_end_date` and `dateCompleted` |
| `prompts/` | The prompt texts copied from Kore, one `.md` per prompt, with `{{placeholders}}` |

### `shared/`: building blocks used by every dialog

| File | What it does |
|---|---|
| `flow.py` | The node types: `ScriptNode`, `MessageNode`, `PromptNode` (model call #2), `SlotNode` (ask and validate, retry with an error text), `ConfirmNode` (yes/no). The routing helpers `goto`, `pause` and `finish`. Every edge in the graph is gated on `turn.route == target id` |
| `agent_node.py` | `AgentNode`: pre-step, model call with tools, then "done, so continue" or "say the model's question and pause". `FoundryAgentRunner` is model call #3. The `end_orchestration` tool is checked when it is called, not when it is built |
| `dates.py` | The date parser. Formats, ranges, partial dates, bare years, skip phrases, yes/no, impossible dates, and the "not in the future" rule (one day of tolerance). Never calls a model |
| `llm_dates.py` | Model call #4 and the validation of its typed answer |
| `osw.py` | The OneSpaWorld API client and all response parsing (section 3) |
| `deps.py` | One bundle of outside connections: the one-shot model call, the agent runner, the OSW client, the clock, and the optional date reader |
| `state_store.py` | Loads and saves the conversation state as JSON files (section 5) |
| `session.py` | `DialogContext`: the `session` and `entities` dictionaries, using Kore's key names |
| `prompts.py` | Fills `{{placeholders}}` in prompt files by plain text replacement (the prompts contain literal JSON braces, so Python formatting cannot be used) |
| `validators.py` | Name and email parsers |

## 5. Where the session variables are stored

There are two layers:

1. **In memory during a message:** `turn.session` and `turn.entities`, two dictionaries that every step reads and edits in place.
2. **On disk between messages:** one JSON file per key in `~/marina_state` (override with `MARINA_STATE_DIR`).
   `TurnEntry` (`orchestrator.py`) loads it; `Persist` (`orchestrator.py`) saves it. Nothing else touches storage.

**Which file:** the load key is the `conversation_id`, or the client's `previous_response_id`. The save keys are the
`conversation_id` and this message's `response_id`. A client that chains with `previous_response_id` therefore produces one
snapshot file per message. A failed message saves nothing, so the next try starts from the last good state.

**Not saved:** the per-message flags in `Turn` (`route`, `resuming`, `replies`). They are rebuilt every time.

### What is in the store today, and who writes it

| Variable | Written by |
|---|---|
| `entities`: `PC_Common_1_Entity_Name`, `PC_Common_1_Entity_Emailid` | `pr_name`, `pr_email` |
| `session.piiEntities.name`, `.emailId` | `pr_redact_name`, `pr_redact_email` |
| `session.initialMessage` | `pr_initial_message` |
| `session.nodeOutputs` (raw extraction text) | `pr_extract` |
| `entities` and `session`: `ship_name`, `cruise_line`, `vessel_id`, plus the vessel counters and flags (`vesselLookupFailCount`, `lastVesselAttempt`, `lastCountedVesselValue`, `vesselSkippedFields`, `vesselForceContinue`, `vesselLookupInvoked`, `vesselCompleted`, `conversationState`) | `process_extracted_entities` (intake) and the vessel agent |
| `session.usr_ship_name`, `usr_cruise_line`, `usr_vessel_id` | `pr_cruise_entities` |
| `session.cruiseDates`, `usr_start_date`, `usr_end_date`, `dateCompleted`; `entities.start_date`, `end_date` | the `cd_*` nodes |
| `session.active_dialog`, `dialog_step` | the classifier, and any step that pauses |
| `session.conversationHistoryString` (last 10 lines), `session.messages` (last 20) | `Persist` |

## 6. What the ticket and document-request steps will need

Kore's Zendesk and document steps read the **same session keys** this bot stores, so ported scripts can stay close to the
originals. The tables below come from Kore's `PC_HomeDelivery_Script_PrepareZendeskData`, the `CreateTicket` service payload,
and the `DocumentCreation_Service_Returns` / `…_Transcations` payloads.

### Already captured

| Variable | Used by |
|---|---|
| `piiEntities.name`, `piiEntities.emailId` | Ticket requester and body, document request, private notes |
| `usr_cruise_line`, `usr_ship_name` | Ticket custom fields and body, document request |
| `usr_vessel_id`, `usr_start_date`, `usr_end_date` | Document request, ticket sail date |
| `initialMessage` | Ticket body |

### Still to be collected, with the Kore step that sets each

| Variable | Set by (Kore node) |
|---|---|
| `piiEntities.phoneNumber` | `PC_HomeDelivery_Entity_PhoneNumber` and its scripts |
| `piiEntities.creditcard` and the card entity | `PC_HomeDelivery_Entity_CreditCardInfo`, `Script0073` |
| `spa_record_name` (name as per spa records) | `PC_HomeDelivery_Agent_SpaRecordName` |
| `CabinNumber` | `PC_Home_Delivery_Agent_CabinNumber` |
| `Country`, `returnReason`, `returnReasonMapped`, `otherReturnReason` | `PC_HomeDelivery_Agent2_ReturnDetails`, `…_IssueResonButtonsValidations` |
| `ProductCount`, `products` (name, quantity, condition, expected product), `productsToReturnString` | `PC_HomeDelivery_Agent_ProductCount`, `PC_HomeDelivery_PromptNode`, `…_ReturnDocuments` |
| `purchaseDateAPI`, `requestedDate`, `isWithinReturnPolicyPeriod` | `PC_HomeDelivery_Agent_PurchasedDate`, `…_SetRequestDate`, `PC_HomeDelivery_ValidationScript` |
| `bookingNumber`, `bookingNumberLine` | `PC_HomeDelivery_Entity_BookingNumber` and its scripts |
| Entities `PC_HomeDelivery_Entity_DeliveryType`, `…_IssueReasonButtons`, `PC_Common_Entity_AdditionalDescription` | their entity nodes |
| **`TicketId`** | Set after the Zendesk create-ticket call; reused by the private notes and the document request |

### Settings, not session variables

The Zendesk base URL and authorisation, all the Zendesk field, form, brand and group ids, and the document API address
(`Document_Creation`) are `env.*` settings in Kore. They will be **environment variables** (like the `OSW_*` ones),
never stored in the session.

### How a downstream step will use them

Read from `turn.session` (for example `session["piiEntities"]["emailId"]`, `session["usr_ship_name"]`), call a new client in
`shared/` built like `osw.py`, write the result back (for example `session["TicketId"]`), and let the next step read it.

## 7. Decisions needed before building those steps

1. **Conversation history.** Kore's ticket script reads `conversationHistory` (the full list). This bot stores `messages` (last
   20 only) and `conversationHistoryString` (last 10 lines). A ticket transcript needs the **full** conversation, so a separate
   full-transcript store is required.
2. **Credit card data.** Kore's ticket and document payloads carry `piiEntities.creditcard`. The state files are plain,
   unencrypted JSON, so storing a card there would be a compliance problem. Decide before porting the card nodes whether to
   mask it, keep only the last digits, or hold it encrypted.
3. **The state store.** It must move from local files to an encrypted store with an expiry (for example Cosmos DB or the
   Foundry state store) before any of this holds real customer data. `shared/state_store.py` has only two methods, so it is
   a contained swap.
4. **Clearing variables between dialogs.** Ending a dialog clears only `active_dialog` and `dialog_step`. Kore's `ClearData`
   step is not ported, so a second return in the same conversation would reuse the old vessel and ticket values.
