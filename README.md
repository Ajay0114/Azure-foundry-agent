# Marina bot on Microsoft Foundry: Product Return POC

A proof of concept that rebuilds part of **Marina**, OneSpaWorld's customer-service bot, on **Microsoft Foundry**.
The bot currently runs on Kore.ai. This repo recreates its **Product Return** conversation (the Kore dialog task
`PC_HomeDelivery`) as a Foundry hosted agent built with **Microsoft Agent Framework workflows**, from the first message to a
Zendesk ticket with its attachments and the two return documents.

It uses the same kinds of building blocks Kore has (script, message, question, yes/no, prompt, tool-calling agent and service
nodes), but where Kore leans on the model and then repairs its mistakes with long scripts, this bot lets the model **read**
customer text into typed fields and lets ordinary code **decide** what happens next. Each place this differs from Kore is
called out below.

It runs locally against a real Foundry model deployment and OneSpaWorld's real vessel, voyage, Zendesk, attachment and
document APIs. There is no built-in fake data, so the settings below are required.

For a file-by-file guide, where the AI model and the APIs are used, and where each session variable lives, see
[CODEBASE_GUIDE.md](CODEBASE_GUIDE.md). To run it in Foundry, follow [DEPLOYMENT.md](DEPLOYMENT.md).

## Status

The whole conversation is ported except the booking-number and credit-card questions (Kore asks them only in some
conversations, so they are left out). About 55 of the dialog's 92 Kore nodes are ported.

| Done | Not done yet |
|---|---|
| Intake: greeting, name, email with confirmation and retry | Booking number and credit card last four |
| Entity extraction from the first message (Kore prompts, verbatim) | Feedback survey after the thank-you |
| Vessel lookup agent on the real OSW vessel API | Clearing the name, email and ship between two requests in one chat |
| Cruise dates: parser, voyage API validation, nearest-voyage confirmation | Running it in Foundry: the files and the step-by-step runbook are ready, but it has not been deployed yet |
| Purchase details: purchaser (spa record) name, cabin, purchase date, delivery type, return reason, country, phone, cancel at any question | Secrets in Key Vault, and a concurrency-safe state store (Cosmos DB) for heavy traffic |
| Product count and product details, read back for confirmation | Automated tests in the repo |
| "Anything else to add?" and end-of-cruise statement upload (scanned, attached to the ticket) | |
| The Zendesk ticket (created once, retry on failure) with a private note holding the whole conversation | |
| The returns and transactions documents requested for the ticket, with a private note on any failure | |
| The complete conversation as a CSV in Kore's transcript layout, one file per conversation, names, e-mails and phone numbers masked | |
| Terminal chat client (`chat.py`) and a small web chat page (`ui.py`) for local testing | |
| Deployment files for a Foundry hosted agent (`azure.yaml`, `Dockerfile`, `scripts/set-azd-env.sh`) and conversation state in Azure Blob Storage | |

**Verified live** (real model and APIs, by chatting): intake, vessel lookup, cruise dates, purchase details, product
details and the Zendesk ticket (sandbox). **Not yet run against the real service:** the attachment function and the
document API; they have only been exercised against fakes and mock servers.

## Quick start

Everything runs from `src/marina-bot` (Python 3.13 with [uv](https://docs.astral.sh/uv/); developed on WSL).

```bash
cd src/marina-bot
uv sync --python 3.13                 # install dependencies
az login                              # DefaultAzureCredential uses this to reach Foundry
```

Copy `src/marina-bot/.env.example` to `src/marina-bot/.env` (git-ignored) and fill it in. Never commit `.env`. The example
already holds the sandbox Zendesk form, brand, group and field ids.

| Variable | Needed | Meaning |
|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | yes | `https://<account>.services.ai.azure.com/api/projects/<project>` |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | yes | Name of the chat model deployment |
| `OSW_TOKEN_URL` | yes | OAuth token endpoint (Azure Entra ID, client credentials) |
| `OSW_CLIENT_ID` | yes | OAuth client id |
| `OSW_CLIENT_SECRET` | yes | OAuth client secret. A secret: keep it in `.env` or Key Vault only |
| `OSW_VESSELS_SCOPE` | yes | `api://<id>/.default` for the vessels API |
| `OSW_ITINERARY_SCOPE` | yes | `api://<id>/.default` for the itinerary API |
| `ZENDESK_BASE_URL` | yes | `https://<subdomain>.zendesk.com` |
| `ZENDESK_AUTHORIZATION` | yes | The value after `Basic ` in Kore's `ZendeskAuthorization` (base64 of `email/token:api_token`). A secret. Or set `ZENDESK_EMAIL` and `ZENDESK_API_TOKEN` and it is built for you |
| `ZENDESK_FORM_ID`, `ZENDESK_BRAND_ID`, `ZENDESK_RETURN_GROUP_ID` | yes | Ticket form, brand and the returns group |
| `ZENDESK_FIELD_INQUIRY_TYPE`, `…_CATEGORY`, `…_PRODUCT_REASON`, `…_RETURN_STATUS`, `…_CREATED_BY`, `…_CRUISE_LINE`, `…_CRUISE_SHIP`, `…_PRIORITY`, `…_SAIL_DATE` | yes | Ids of the custom ticket fields (Kore's `Zendesk_*_ID` settings) |
| `ATTACHMENT_API_URL`, `ATTACHMENT_API_KEY` | yes | The Azure Function that scans an uploaded file and stages it in Zendesk (Kore: `AzureFileAttachmentUrl`, `AzureFunctionKey`). The key is a secret |
| `DOCUMENT_API_URL`, `DOCUMENT_CLIENT_ID`, `DOCUMENT_CLIENT_SECRET`, `DOCUMENT_RETURNS_SCOPE`, `DOCUMENT_TRANSACTIONS_SCOPE` | yes | The document-creation API and its OAuth client (Kore: `Document_Creation`, `DocumentCreationClientID`, `ReturnScope`, `TransactionScope`). The client secret is a secret |
| `DOCUMENT_TOKEN_URL` | optional | Defaults to `OSW_TOKEN_URL` (same tenant) |
| `ZENDESK_TAGS` | optional | Comma separated. Defaults to `kore_ai,tag_website`, what Kore sent, so existing Zendesk triggers keep working |
| `OSW_BASE_URL` | optional | Defaults to `https://oswbus-dev.onespaworld.com` |
| `STATE_BLOB_ACCOUNT_URL`, `STATE_BLOB_CONTAINER` | when hosted | Keep conversation state in Azure Blob Storage (for this project `https://oswdevpoc.blob.core.windows.net`; container default `marina-state-ai-foundry`) with the agent's own identity. Leave unset locally |
| `STATE_BLOB_CONNECTION_STRING` | optional stopgap | The storage account's connection string, used instead of the identity while a role is pending. It is a **master key** for the whole account: sandbox only, rotate it afterwards (see [DEPLOYMENT.md](DEPLOYMENT.md)) |
| `TRANSCRIPT_ENABLED`, `TRANSCRIPT_MASK_PII`, `TRANSCRIPT_BOT_NAME`, `TRANSCRIPT_CHANNEL` | optional | The transcript CSV: write it (default `true`), mask names, e-mails and phone numbers (default `true`), and the "Bot Name" (default `Marina`) and "Channel" (default `Foundry`) columns. When hosted, add a variable to `azure.yaml` as well to change it |
| `MARINA_STATE_DIR` | optional | Where local state files go when Blob Storage is not configured. Defaults to `~/marina_state` |

If a required `OSW_*`, `ZENDESK_*`, `ATTACHMENT_*` or `DOCUMENT_*` value is missing, the bot stops at start-up with a message
naming the missing settings. **The bot creates real tickets in the Zendesk it is pointed at.** Use a sandbox while testing.

```bash
uv run --no-sync python main.py        # terminal 1: start the bot on http://localhost:8088 and leave it running
python3 chat.py                        # terminal 2: talk to it (/new, /attach <https-url>, /quit)
python3 ui.py                          # or a small web chat page on http://localhost:8000 (UI_PORT=8010 for another port)
```

At the upload question, type `skip`, or attach a file **link** (`/attach https://…` in `chat.py`, the 📎 box in `ui.py`).

## Repository layout

```
.
├── README.md, CODEBASE_GUIDE.md, DEPLOYMENT.md
├── azure.yaml              Foundry hosted-agent deployment manifest (azd)
├── scripts/set-azd-env.sh  Copies the settings from .env into the azd environment
├── .gitignore
└── src/marina-bot/
    ├── main.py                 Entry point: connects to Foundry, builds the dependencies, starts the server
    ├── orchestrator.py         Top-level workflow: load state, classify intent, run a dialog, save state, reply
    ├── models.py               TurnInput (from the host) and Turn (the envelope passed between nodes)
    ├── chat.py                 Terminal chat client for local testing (not part of the deployed bot)
    ├── ui.py                   Small local web chat page (stdlib only); forwards messages to the bot
    ├── .env.example            Every setting, with the sandbox Zendesk ids filled in; copy to .env
    ├── Dockerfile, .dockerignore, .azdignore    How the agent is built and what is left out of the package
    ├── pyproject.toml, uv.lock, uv.toml    Dependencies, pinned versions, corporate-certificate setting
    ├── dialogs/
    │   └── product_return/     The Product Return dialog (Kore: PC_HomeDelivery)
    │       ├── workflow.py         The dialog's node graph; intake, entry and resume routing
    │       ├── intake_scripts.py   Script nodes: remember the first message, clean the extraction output
    │       ├── vessel.py           Vessel agent: pre/post-processing, prompt, lookup tool, failure cap
    │       ├── cruise_dates.py     Cruise start/end date collection and voyage validation
    │       ├── purchase_details.py Purchaser name, cabin, purchase date, delivery type, return reason, country, phone, cancel
    │       ├── product_details.py  Product count, product list (slots and questions), confirmation, saving for the ticket
    │       ├── ticket.py           "Anything else?", file upload, ticket creation, private notes, documents, thank-you
    │       ├── return_documents.py Document validation, the two document payloads, the failure notes (pure functions)
    │       ├── return_extraction.py  Reads the second extraction (cabin, date, phone, country, products) into the notes
    │       └── prompts/            Prompt text copied from Kore, one .md per prompt node
    └── shared/                 Building blocks used by every dialog
        ├── flow.py                 Node types (script, message, prompt, question, yes/no) and routing helpers
        ├── agent_node.py           The "model with tools" node and its Foundry runner
        ├── cancel.py               Recognises "cancel / stop this" at any question
        ├── dates.py                Deterministic date parser and date rules
        ├── validators.py           Name, email, purchaser name, cabin, phone, delivery type, return reason, quantity, condition parsers
        ├── countries.py            Country names and aliases ("UK" becomes "United Kingdom")
        ├── llm_dates.py            Model fallback for dates the parser cannot read (typed structured output)
        ├── llm_products.py         Model reader for one reply in the product questions (typed structured output)
        ├── osw.py                  Real OneSpaWorld vessel and voyage API client (OAuth, search, nearest voyage)
        ├── zendesk.py              Zendesk client: create ticket, private note, find by external id
        ├── attachments.py          Reads files from the request; calls the scan-and-stage function
        ├── documents.py            Document-creation API client (OAuth, returns and transactions requests)
        ├── htmltext.py             HTML-escaping helper for ticket text
        ├── deps.py                 One bundle of outside connections (model, agent runner, OSW, Zendesk, attachments, documents, clock)
        ├── state_store.py          Saves and loads conversation state between messages (Azure Blob Storage, or local JSON files)
        ├── transcript.py           Builds the conversation transcript CSV (Kore's columns) and masks personal details
        ├── session.py              DialogContext: the session/entities dictionaries, Kore's key names
        └── prompts.py              Fills {{placeholders}} in prompt files
```

## How a message is processed

Foundry hosts the bot as a **Responses-protocol** server. Every customer message is a separate request, so the bot
keeps no conversation in memory. Instead, **one message is one run of a workflow graph**, and the conversation state
is saved between runs.

```
customer message (text, and any file links)
      │
      ▼
main.py ── parse_response: the text, any attached https file links, and which saved state to load and where to save
      │
      ▼
 orchestrator workflow (a fresh graph for every request)
      │
 turn_entry ──(dialog already active)──────────────────────────────┐
      │                                                            │
      └─(new topic)─► intent_classifier ─(PRODUCT_RETURN)─► product_return (sub-workflow) ─► persist ─► reply
                            │                                                                  ▲
                            └─(anything else)─► fallback ──────────────────────────────────────┘
```

- **turn_entry** loads the saved state, or starts empty.
- **intent_classifier** is one model call that returns `PRODUCT_RETURN` or `OTHER`. It only runs when no dialog is active.
- **product_return** is the dialog, built as its own sub-workflow.
- **fallback** answers "I can only help with product returns right now."
- **persist** appends the exchange to the history and to the full transcript, saves the state, and returns the text.

## The Product Return flow

Node ids are in `workflow.py`, `cruise_dates.py`, `purchase_details.py`, `product_details.py` and `ticket.py`. The right-hand
column is the Kore node each one replaces.

| Node id | Kind | What it does | Kore node |
|---|---|---|---|
| `pr_initial_message` | script | Remembers the first message (once) | `PC_Common_1_Script_InitialUserMessage` |
| `pr_greeting` | message | "Thanks for reaching out…" | `PC_Common_1_Msg_Display` |
| `pr_name` | question | Asks the full name; two to five words | `PC_Common_1_Entity_Name` |
| `pr_redact_name` | script | Copies the name to the private notes | `PC_Common_1_Script_redactionName` |
| `pr_email` | question | Asks the email | `PC_Common_1_Entity_Emailid` |
| `pr_redact_email` | script | Copies the email to the private notes | `PC_Common_1_Script_redactEmail` |
| `pr_email_confirm` | yes/no | "Is this the best email?" No goes to `pr_delete_email`, then back to `pr_email` | `PC_Common_1_Confirmation_EmailConfirmation` |
| `pr_extract` | prompt | Model reads ship, cruise line and dates from the first message | `PC_ExtractCruiseEntitiesFromInitialUserMessage` |
| `pr_process_extracted` | script | Validates and normalises that output | `PC_Script_ProcessExtractedEntities` |
| `pr_vessel_agent` | agent | Finds the ship (see below) | `HD_VesselLookupAgent` |
| `pr_cruise_entities` | script | Copies ship details to the long-lived `usr_*` notes | `PC_Cruise_Entities` |
| `cd_*` | dates | Cruise start and end dates (see below) | `HD_CruiseDateOrchestrator`, `PC_CruiseDate_Entities` |
| `pd_vars` | script | Starts the stage: clears earlier purchase answers, sets `customerName` and `customerEmail` | `PC_HomeDelivery_Script_Variables` |
| `pd_intro`, `pd_ask_spa_name` | message, question | Intro, then "What is the name of the purchaser?" | `PC_HomeDelivery_Agent_SpaRecordName` |
| `pd_extract`, `pd_save_extraction` | prompt, script | Model reads cabin, purchase date, phone, country and products from the first message (Kore prompt, verbatim); code validates and stores them | `PC_HomeDelivery_PromptNode`, `…_SaveEntities` |
| `pd_ask_cabin` | question | Cabin number(s), skipped if already known | `PC_Home_Delivery_Agent_CabinNumber` |
| `pd_policy_info` | message | 60-day return policy note | - |
| `pd_set_request_date` | script | Stores today's date as `requestedDate` | `PC_HomeDelivery_SetRequestDate` |
| `pd_ask_purchase_date` | question | Purchase date, checked against the cruise dates | `PC_HomeDelivery_Agent_PurchasedDate` |
| `pd_ask_delivery` | question | "Bought on the ship, or a Home Delivery order?" | `PC_HomeDelivery_Entity_DeliveryType` |
| `pd_ask_reason` | question | The five return reasons, answered by number, title or keyword; maps each to its Zendesk and API values | `PC_HomeDelivery_Entity_IssueReasonButtons`, `…_IssueResonButtonsValidations` |
| `pd_ask_reason_text` | question | Only for "Other": "Please briefly describe the reason" | `PC_HomeDelivery_Entity_Reason` |
| `pd_ask_country` | question | Country, normalised ("UK" becomes "United Kingdom"); skipped if known | `PC_HomeDelivery_Agent2_ReturnDetails` |
| `pd_ask_phone` | question | Phone number, skipped if already known | `PC_HomeDelivery_Entity_PhoneNumber` |
| `pd_cancel` | script | Ends the dialog when the customer asks to cancel at any question | `Cancel_Mid_Workflow` |
| `pd_ask_product_count` | question | "How many items in total?" A number is read directly; a list of products is added up by the model | `PC_HomeDelivery_Agent_ProductCount`, `…_Script_ProductCount` |
| `pd_ask_products` | question, loops | Name, quantity and condition of each product (and the expected product for a wrong item) until the count is reached | `PC_HomeDelivery_Agent_ProductDetails` |
| `pd_confirm_products` | yes/no | Reads the list back; No starts the list again | Kore asks to confirm but never reads the answer |
| `pd_reset_products`, `pd_save_products` | script | Clear the list / build the ticket list (`productsToReturn`, summary, outcome) | `PC_HomeDelivery_Script_SavingAgentData` |
| `pd_ask_additional` | question | "Is there anything else you'd like to add?" (optional free text) | `PC_Common_Entity_AdditionalDescription` |
| `pd_ask_upload` | question | "Upload your end-of-cruise statement or type Skip"; a file is scanned and staged by the attachment service. A blocked type, malware or an upload error asks again (three tries) | `HomeDelivery_Entity_Upload`, `…_Script_PrepareAzureData`, `…_Service_ScanUpload`, `…_Script_HandleScanResult`, the three upload error messages |
| `pd_create_ticket` | service | Validates the documents' fields, builds the payload, creates the Zendesk ticket, adds the private transcript. On failure offers a retry | `PC_HomeDelivery_ValidationScript`, `…_Script_PrepareZendeskData`, `…_Service_CreateTicket`, `…_ConversationPrivateNote`, `…_Message_TicketFailed` |
| `pd_finalise_request` | service | Adds the attachments to the ticket, requests the returns and transactions documents, notes any failure on the ticket, thanks the customer with the ticket number | `…_Service_PrivateNoteAttachmentAPI`, `…_Script_ReturnDocuments`, `DocumentCreation_Service_Returns`, `…_Transcations`, the error and validation-fail scripts, `…_ThanksMessage` |

### Vessel lookup (`vessel.py`, `pr_vessel_agent`)

A model with two tools, `VesselLookupTool` and `end_orchestration`, runs over one or more messages.

- The ship or cruise line already known from the first message is looked up straight away.
- One match resolves the vessel (id, name, cruise line). Several matches are listed and the customer picks one.
  A cruise line alone lists its ships.
- No match counts as a failed lookup. After **two** failed lookups the customer's value is accepted as the ship name
  and the flow moves on, so the bot never asks a third time.
- `end_orchestration` is refused while nothing is known and the customer has not been asked yet.

### Cruise dates (`cruise_dates.py`)

Explicit graph nodes, not a prompted state machine. Pause points are marked ⏸ (the bot asks, the turn ends, and the
next message resumes there).

```
cd_start ──► ⏸ cd_ask_start ──► cd_validate ──┬─ exact voyage ─────────────────► cd_finish
   │              │                            ├─ nearest voyage ─► ⏸ cd_confirm_nearest ─► cd_finish
   │              │                            │                         └─ other date ───► cd_validate
   │              └─ skipped / no vessel ──────┴─ none, or API down ─► ⏸ cd_ask_end ──────► cd_finish
   └─ dates already known from the first message skip straight ahead
```

- **Reading dates** (`shared/dates.py`): "January 11 2026", `7/19/26`, `2026-01-11`, ranges such as "Jan 11-18, 2026",
  "13-20 July 2026" and "Dec 28 to Jan 4 2026", and dates inside sentences. A date without a year makes the bot ask only
  for the year. Impossible dates (30 February) are never accepted. A reply that is not a date is handed to the model
  fallback (`shared/llm_dates.py`), which returns day, month and year as separate typed fields. Code validates them, so
  the model cannot create an invalid date.
- **Validating** (`shared/osw.py`): the voyage API is asked for a voyage that **embarked** on the date. If there is one,
  its end date is used. Otherwise the any-date API is asked, and the voyage containing the date, or the closest one, is
  offered with Kore's "closest cruise itinerary" YES/NO message. A different date from the customer is validated again.
- **Rules**: a future start date is rejected; an end date before the start is rejected; "I don't know" skips a field; after
  three unreadable replies a field is given up; an API outage logs the error and the bot asks for the end date instead.

### Purchase details (`purchase_details.py`)

Every question is its own pause point, and every one accepts a cancel request ("cancel", "stop this"; not "cancel my
subscription"). Every question also has a retry cap, after which the bot continues without that value.

- **Purchaser name.** One to six words of letters (hyphens and apostrophes allowed). Two names joined by "or" or "and" are
  not accepted; the bot asks which one. "I don't know" stores `Not provided`.
- **Second extraction.** One model call over the first message. Anything it finds is validated by code and not asked again;
  a field the customer said they do not know is not asked either.
- **Cabin number.** Letters and digits with at least one digit (`4201`, `A9202`, `TC03`), several allowed. Two cabins joined
  by a symbol (`294@TC03`) get Kore's "separate with commas" message. Asked twice, then the bot continues without it.
- **Purchase date.** Read by `shared/dates.py`. A missing year or day is asked for on its own; several dates are asked to be
  narrowed to one. Future dates and dates outside the cruise are rejected with the cruise dates shown. After four tries, or
  when a rejected date is repeated, it is recorded as unknown. `isWithinReturnPolicyPeriod` is true up to 60 days.
- **Delivery type.** "Onboard Purchase" or "Home Delivery", by number, Kore's wording or similar phrases ("bought on the
  ship", "delivered to my house"). A reply that fits both or neither is asked again; after three tries it is `Not Provided`.
- **Return reason.** Kore's five buttons are shown as a numbered list. Answer by number, title or a clear keyword
  ("broken", "allergic", "billed twice"); a reply that fits two reasons is asked again. After three tries it counts as
  Other. Other asks for a short description (`otherReturnReason`). Stored: `reasonDisplay`, `returnReason` (Zendesk value),
  `returnReasonMapped` (document API value).
- **Country.** Matched against a country list with aliases; asked once more with an explanation if the customer says they
  do not know, then accepted as unknown. Three unrecognised replies continue without it.
- **Phone number.** 7 to 15 digits; "I don't have one" is accepted. Three invalid replies continue without it.

### Product count and product details (`product_details.py`)

Kore lets the model run this conversation and then repairs its mistakes with a long script. Here the model only **reads
one reply** (`shared/llm_products.py`, typed output: name, quantity, condition, expected product, "that's all") and code
decides everything else.

- **Count.** A bare number or number word ("3", "two") is read without the model. A list ("2 gels and 2 creams") is added
  up. Names without quantities are not guessed: the bot asks for the total. "I don't know" is accepted, and then the list
  ends only when the customer says "that's all" (Kore silently assumes 1).
- **Slots.** Each product has a name, quantity, condition and, for a wrong item, the expected product. Kore's questions are
  asked in Kore's order for the first thing missing. A different product name always gets its own slot, so a product the
  customer named is never dropped or overwritten. "1 new and 1 used cleanser" makes two slots. "They are all new" fills
  every condition still empty.
- **Conditions** are `new`, `used`, `damaged` or `wrong product`, mapped from Kore's synonym lists. A bare quantity or a
  condition word is read by code and never reaches the model.
- **Finishing.** The list ends when the quantities reach the count. If the count is unknown, or the customer says "that's
  all" early, an incomplete product is asked about once and then left out. Over the count, everything is kept and flagged.
  Five replies with nothing usable end the step with what exists. "I don't know the expected product" is recorded as
  `Not provided`, not dropped.
- **Confirmation.** The list is read back and a yes/no is asked; No starts the list again. (Kore asks to confirm but never
  reads the answer, so the next node would take "yes" as a booking number.)
- **Saved** (`pd_save_products`, Kore's `SavingAgentData`): `productsToReturn` (name, quantity, condition code 1 or 2,
  expected product), `all_products_summary`, `collectedUnits`, `countMismatch` and `collectionOutcome` (`clean`,
  `partial_review` or `nothing_submittable`).

### The Zendesk ticket (`ticket.py`, `shared/zendesk.py`)

- **Payload.** One plain function, `build_ticket_payload`, replaces Kore's six string fragments and service-node tokens:
  subject, requester, HTML body (customer, voyage, spa record, return, products, additional information), form, brand,
  group, `urgent` priority, tags, and the custom fields (inquiry type, category from the delivery type, return reason,
  return status `osw_return_requested`, created by, cruise line, ship, sail date). A custom field with no value is left out,
  not sent blank.
- **Everything the customer typed is HTML-escaped** before it goes into the ticket. Kore pastes it in raw.
- **One ticket per request.** Each ticket carries an `external_id`. A create is never retried blindly: before a retry the bot
  looks for a ticket with that id, so a timeout that actually created the ticket does not produce a duplicate.
- **Failure.** The customer keeps their answers and is offered a retry (three attempts), then told nothing was submitted.
  Kore ends the dialog and loses everything.
- **Private note.** The whole conversation of this request (`session["transcript"]`, started fresh with every new request)
  is added as a private comment. If the note fails the ticket still stands and the customer is thanked.
- **Result.** `session["TicketId"]`, used as the `referenceId` of both documents.

### File upload and the two documents (`ticket.py`, `return_documents.py`, `shared/attachments.py`, `shared/documents.py`)

- **Upload.** The customer attaches a file in the chat client, which sends it with the message as an `input_file` or
  `input_image` item. Only items with an **https link** are used, because the scan function downloads the file itself;
  inline data or a stored-file id cannot be passed on and is treated as an upload error. The function (Kore's
  `/api/upload`) scans for malware and file type, uploads to Zendesk and returns tokens, which are attached to the ticket
  as a private note. Up to five files. The function decides which hosts it will download from.
- **Validation** (Kore's `ValidationScript`): each document lists the fields it needs (guest name, email, phone, country,
  cruise line, ship, cabin, embarkation, purchase and request dates, products for the returns document; vessel id,
  start and end date, guest name, cabin for the transactions document). Unknown or placeholder values count as missing.
- **Documents.** The returns document and the transactions document are requested separately, each with the ticket id as
  `referenceId`. A document whose fields are incomplete is not requested; a private note on the ticket says what is
  missing, and the ticket gets the tag `returns_documentcreaterequestfailed` or `transactions_documentcreaterequestfailed`
  (Kore adds both whenever either fails). If the API refuses a request, a private note carries its error text. Neither
  failure stops the other document or the thank-you.
- **Differences from Kore's payloads:** the transactions document gets the cabins as a real list; only products with a name
  and a quantity are sent; `clientMetadata` holds one `source` entry instead of Kore's `Key1/Value1` placeholders; booking
  number and credit card last four are not sent. If the document API insists on the old shape, that is a few lines in
  `return_documents.py`.

## Conversation state and variables

State has two dictionaries, with Kore's names:

| Dictionary | Kore equivalent | Holds |
|---|---|---|
| `session` | `context.session.BotUserSession` | Which dialog is active, the paused step (`dialog_step`), the first message, history and full transcript, vessel and date results, private copies (`piiEntities`), per-stage state (`cruiseDates`, `purchaseDetails`), `usr_*` results, every purchase answer, the products, the ticket id and the document results |
| `entities` | `context.entities` | Values collected in the dialog: name, email, ship, vessel id, start and end date, `SpaRecordName`, `CabinNumber`, `PurchasedDate`, `Country`, `ProductCount`, delivery type, return reason, additional information |

Per message: `turn_entry` loads the state, nodes read and edit the dictionaries in place, and `persist` saves them once at the
end (so a failed turn saves nothing). State lives in one JSON document per key: a blob in Azure Blob Storage when `STATE_BLOB_ACCOUNT_URL` is set (Foundry), otherwise a file under `MARINA_STATE_DIR`. A conversation has **one key**: the
`conversation_id` when the client uses conversations, otherwise the platform's session id (the same for every message of a
session), so the state is one file that is overwritten on each message, not a new file per message. The full list of
variables and who writes each one is in [CODEBASE_GUIDE.md](CODEBASE_GUIDE.md).

### The conversation transcript

After every message the bot also rewrites `transcripts/<yyyy-mm-dd>/<conversation>.csv` in the same container (or
folder), so every conversation of a day sits in that day's folder, for example `transcripts/2026-10-09/`: the whole conversation so far, in the columns of Kore's transcript export (`Bot Name, User, Channel, Language, Bot Message,
User Message, Timestamp, emailData`), one row per message, with a file the customer sent shown as "Attachment uploaded". It
is rewritten rather than written at the end, so it is complete even when the customer walks away half-way. Names, e-mails and
phone numbers are masked (`#*#NAME#*#`, `#*#EMAIL#*#`, `#*#PHONE#*#`) as Kore's export masks them; the unmasked text stays only in the
conversation state, which the Zendesk ticket needs. Times are UTC. A conversation stays in the folder of the day it started, even if it runs past midnight. A failure to write it is logged and never shown to the customer.

## Key mechanisms

- **Routing.** Every node sets `turn.route` to the id of the next node, and every edge is gated on `route == target id`.
  The graph shows the allowed transitions; each node's Python picks one.
- **Pause and resume.** A node that needs an answer asks its question, stores its own id in `session["dialog_step"]`, and ends
  the turn. On the next message the dialog's entry node jumps straight back to that node with `turn.resuming = True`, and the
  node treats the text as its answer and clears the flag. This is why a "yes" meant for one question can never be taken as
  the answer to another.
- **Node types** (`shared/flow.py`, `shared/agent_node.py`): `ScriptNode`, `MessageNode`, `PromptNode`, `SlotNode` (ask and
  validate, retry with an error text), `ConfirmNode` (yes/no) and `AgentNode` (model with tools).
- **Model use.** Dialog control is ordinary code. The model reads the first message twice (ship and dates; purchase
  details), drives the vessel agent through tools, reads each reply in the product questions, and is a fallback for unusual
  date wording. Its output is always validated by code, and a bare number or a plain word never reaches it.
- **The SDK's built-in pause and resume (`request_info`) is not used.** It surfaces a pause as a tool call that the client
  must answer with a tool result, which does not suit a plain-text chat channel.

## Hosting notes

- `main.py` uses native workflow hosting (`ResponsesHostServer(workflow=…, parse_response=…)`).
- **Stable workflow names** (`marina-bot`, `product-return`) are required: the host refuses to continue a conversation if the
  rebuilt graph has a different name.
- **Checkpoint allowlist.** The host checkpoints each turn's messages and restores only types allowed by name, so `main.py`
  lists `models:TurnInput` and `models:Turn`. Any new class sent between nodes as a message must be added there.
- **Foundry.** The platform injects `FOUNDRY_PROJECT_ENDPOINT` and the Application Insights connection string; see
  [DEPLOYMENT.md](DEPLOYMENT.md).
- **Local sessions.** Locally a request needs an `agent_session_id` so successive turns share a scope; `chat.py` and `ui.py`
  echo the one the server returns. In a hosted deployment the platform supplies it.
- **Files.** `parse_response` reads the request's input items (`get_input_items`) and keeps the `input_file` and
  `input_image` items that carry an https link.
- The hosting package is a **beta** release, so expect API changes when upgrading.

## Known limitations

- **No automated tests in the repo.** The earlier suite and its fake-data stub were removed to keep the code simple. During
  development the later stages were checked with a larger suite (parsers, every conversation path, all four HTTP clients
  against mock servers) that lives outside the repo; it can be added back if wanted. The bot itself needs the real Foundry
  model and the real APIs to run.
- **State store.** Local files have no expiry and no sharing between instances, so use Blob Storage when hosted (set
  `STATE_BLOB_ACCOUNT_URL`; add a lifecycle rule to expire old conversations, see [DEPLOYMENT.md](DEPLOYMENT.md)). Name, email, phone
  and the whole conversation are stored as clear JSON in either store, and two simultaneous messages from one customer
  can overwrite each other (last write wins). Cosmos DB is the next step if that matters: `shared/state_store.py` has
  two methods.
- **No full cleanup between requests.** Starting a new purchase stage clears the purchase answers, the products, the ticket
  and the document results, and a new request starts a new transcript. But the name, email, vessel and cruise dates are kept,
  so a second return in the same conversation skips those questions. Kore's `ClearData` step is not ported.
- **Attachments need a link.** A file sent as inline base64 or a stored-file id cannot be scanned by the Azure Function; the
  chat front end must send an https link (Kore's channel did).
- **Not live-tested:** the attachment service and the document API (see Status).
- **Ticket fields.** Booking number and card last four are not asked, so the ticket shows "N/A". Zendesk field ids and the
  form must match the Zendesk you point at; a wrong id is rejected by Zendesk and shows up as a failed create in the log
  (status code only).
- **Simplified checks.** Name, email, purchaser name, cabin, phone, delivery type and return reason validation are plain
  rules standing in for Kore's built-in entity types and agent-node prompts. The delivery-type and return-reason keyword
  lists are my own; a reply that fits none gets a "please choose" message rather than a guess. The empathy check node has no
  configuration in the Kore export and was skipped.
- **Models.** Prompts run on the deployed model, not Kore's `gpt-5.1`, and Kore's temperature and token settings are not
  applied.
- **Not deployed yet.** The deployment files follow the Foundry sample `05-workflows` and the steps are in
  [DEPLOYMENT.md](DEPLOYMENT.md), but they have not been run against the real subscription. `azd` prompts may differ slightly.
- **Secrets as plain environment variables.** In Foundry the secrets are passed as the agent's environment variables
  (and sit in `.azure/` on the deploying machine). Move them to Key Vault before production.

## Security

- Credentials are read from environment variables only. `.env` and the azd environment (`.azure/`) are git-ignored;
  `.env.example` holds no secrets. In Foundry the agent reaches Blob Storage and the model with its own Microsoft Entra
  identity, with no keys.
- The OAuth client secret appeared in plain text in the Postman collections the OSW APIs were taken from. Rotate it and keep
  the new value out of the repo.
- The Zendesk credential, the attachment function key and the document client secret are also read from the environment
  only. Use an API token for a dedicated Zendesk user with the least access that can create tickets and add comments.
- Logs contain dates, vessel ids, node names and HTTP status codes, never tokens, secrets or customer details. Error
  messages from the Zendesk, attachment and document clients carry the status code only.
- Customer text is HTML-escaped before it goes into a ticket.
- The conversation transcript, name, email and phone are stored in the state files in clear text (see the state-store
  limitation) and sent to Zendesk, where they belong. Tickets are created in whichever Zendesk `ZENDESK_BASE_URL` names.
- `ui.py` listens on 127.0.0.1 only and has no login: it is for local testing.
- The attachment function downloads whatever https link it is given, so it must restrict the hosts it will fetch from.
