# Marina bot on Microsoft Foundry: Product Return POC

A proof of concept that rebuilds part of **Marina**, OneSpaWorld's customer-service bot, on **Microsoft Foundry**.
The bot currently runs on Kore.ai. This repo recreates its **Product Return** conversation (the Kore dialog task
`PC_HomeDelivery`) as a Foundry hosted agent built with **Microsoft Agent Framework workflows**, using the same kinds
of building blocks Kore has: script, message, question, yes/no, prompt, tool-calling agent and service nodes.

It runs locally against a real Foundry model deployment and OneSpaWorld's real vessel and voyage APIs. There is no
built-in fake data, so the OSW settings below are required.

For a file-by-file guide, where the AI model and the APIs are used, and where the session variables live (including what
the ticket and document-request steps will need), see [CODEBASE_GUIDE.md](CODEBASE_GUIDE.md).

## Status

| Done | Not done yet |
|---|---|
| Intake: greeting, name, email with confirmation and retry | Booking number and card nodes, file upload and scan, return documents |
| Entity extraction from the first message (Kore prompt, verbatim) | Validation layer |
| Vessel lookup agent on the real OSW vessel API | Feedback survey and the closing messages after the ticket |
| Cruise dates: parser, voyage API validation, nearest-voyage confirmation | Feedback path, clearing variables between dialogs |
| Purchase details: purchaser (spa record) name, cabin number, purchase date, delivery type, return reason, country, phone number, cancel | Deployment to Foundry, a production state store, automated tests |
| Product count and product details with a read-back confirmation, saved in the shape the ticket needs | |
| "Anything else to add?", then the Zendesk ticket (created once, retry on failure) and the private conversation note | |
| Terminal chat client for local runs | |

About 45 of the dialog's 92 Kore nodes are ported. The dialog now ends with a real Zendesk ticket. Booking number, card
last four and attachments are not asked yet, so those lines show "N/A" in the ticket, as Kore does when they are absent.

## Quick start

Everything runs from `src/marina-bot` (Python 3.13 with [uv](https://docs.astral.sh/uv/); developed on WSL).

```bash
cd src/marina-bot
uv sync --python 3.13                 # install dependencies
az login                              # DefaultAzureCredential uses this to reach Foundry
```

Copy `src/marina-bot/.env.example` to `src/marina-bot/.env` (git-ignored) and fill it in. Never commit `.env`. The example already holds the sandbox Zendesk form, brand, group and field ids.

| Variable | Needed | Meaning |
|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | yes | `https://<account>.services.ai.azure.com/api/projects/<project>` |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | yes | Name of the chat model deployment (for example `gpt-5.4-mini`) |
| `OSW_TOKEN_URL` | yes | OAuth token endpoint (Azure Entra ID, client credentials) |
| `OSW_CLIENT_ID` | yes | OAuth client id |
| `OSW_CLIENT_SECRET` | yes | OAuth client secret. A secret: keep it in `.env` or Key Vault only |
| `OSW_VESSELS_SCOPE` | yes | `api://<id>/.default` for the vessels API |
| `OSW_ITINERARY_SCOPE` | yes | `api://<id>/.default` for the itinerary API |
| `ZENDESK_BASE_URL` | yes | `https://<subdomain>.zendesk.com` |
| `ZENDESK_AUTHORIZATION` | yes | The value after `Basic ` in Kore's `ZendeskAuthorization` (base64 of `email/token:api_token`). A secret. Or set `ZENDESK_EMAIL` and `ZENDESK_API_TOKEN` and it is built for you |
| `ZENDESK_FORM_ID`, `ZENDESK_BRAND_ID`, `ZENDESK_RETURN_GROUP_ID` | yes | Ticket form, brand and the returns group |
| `ZENDESK_FIELD_INQUIRY_TYPE`, `…_CATEGORY`, `…_PRODUCT_REASON`, `…_RETURN_STATUS`, `…_CREATED_BY`, `…_CRUISE_LINE`, `…_CRUISE_SHIP`, `…_PRIORITY`, `…_SAIL_DATE` | yes | Ids of the custom ticket fields (Kore's `Zendesk_*_ID` settings) |
| `ZENDESK_TAGS` | optional | Comma separated. Defaults to `kore_ai,tag_website`, what Kore sent, so existing Zendesk triggers keep working |
| `OSW_BASE_URL` | optional | Defaults to `https://oswbus-dev.onespaworld.com` |
| `MARINA_STATE_DIR` | optional | Where conversation state files go. Defaults to `~/marina_state` |

If a required `OSW_*` or `ZENDESK_*` value is missing, the bot stops at start-up with a message naming the missing settings.
**The bot creates real tickets in the Zendesk it is pointed at.** Use a sandbox while testing.

```bash
uv run --no-sync python main.py        # start the bot on http://localhost:8088
python3 chat.py                        # in a second terminal: talk to it (/new, /quit)
```

## Repository layout

```
.
├── README.md
├── .gitignore
└── src/marina-bot/
    ├── main.py                 Entry point: connects to Foundry, builds the dependencies, starts the server
    ├── orchestrator.py         Top-level workflow: load state, classify intent, run a dialog, save state, reply
    ├── models.py               TurnInput (from the host) and Turn (the envelope passed between nodes)
    ├── chat.py                 Terminal chat client for local testing (not part of the deployed bot)
    ├── pyproject.toml, uv.lock, uv.toml    Dependencies, pinned versions, corporate-certificate setting
    ├── dialogs/
    │   └── product_return/     The Product Return dialog (Kore: PC_HomeDelivery)
    │       ├── workflow.py         The dialog's node graph; intake, entry and resume routing
    │       ├── intake_scripts.py   Script nodes: remember the first message, clean the extraction output
    │       ├── vessel.py           Vessel agent: pre/post-processing, prompt, lookup tool, failure cap
    │       ├── cruise_dates.py     Cruise start/end date collection and voyage validation
    │       ├── purchase_details.py Purchaser name, cabin, purchase date, delivery type, return reason, country, phone, cancel
    │       ├── product_details.py  Product count, product list (slots and questions), confirmation, saving for the ticket
    │       ├── ticket.py           "Anything else?", the Zendesk payload, ticket creation, private note, retry
    │       ├── return_extraction.py  Reads the second extraction (cabin, date, phone, country, products) into the notes
    │       └── prompts/            Prompt text copied from Kore, one .md per prompt node
    ├── shared/                 Building blocks used by every dialog
    │   ├── cancel.py               Recognises "cancel / stop this" at any question
    │   ├── flow.py                 Node types (script, message, prompt, question, yes/no) and routing helpers
    │   ├── agent_node.py           The "model with tools" node and its Foundry runner
    │   ├── dates.py                Deterministic date parser and date rules
    │   ├── llm_dates.py            Model fallback for dates the parser cannot read (typed structured output)
    │   ├── zendesk.py              Zendesk client: create ticket, private note, find by external id (settings from the environment)
    │   ├── llm_products.py         Model reader for one reply in the product questions (typed structured output)
    │   ├── countries.py            Country names and aliases ("UK" becomes "United Kingdom")
    │   ├── osw.py                  Real OneSpaWorld vessel and voyage API client (OAuth, search, nearest voyage)
    │   ├── deps.py                 One bundle of outside connections (model, agent runner, OSW, clock)
    │   ├── state_store.py          Saves and loads conversation state between messages (JSON files)
    │   ├── session.py              DialogContext: the session/entities dictionaries, Kore's key names
    │   ├── prompts.py              Fills {{placeholders}} in prompt files
    │   └── validators.py           Name, email, purchaser name, cabin, phone, delivery type, return reason, quantity and condition parsers
```

## How a message is processed

Foundry hosts the bot as a **Responses-protocol** server. Every customer message is a separate request, so the bot
keeps no conversation in memory. Instead, **one message is one run of a workflow graph**, and the conversation state
is saved between runs.

```
customer message
      │
      ▼
main.py ── parse_response: the message text + which saved state to load and where to save
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
- **persist** appends the exchange to the history, saves the state, and returns the text.

## The Product Return flow

Node ids are in `workflow.py`, `cruise_dates.py`, `purchase_details.py`, `product_details.py` and `ticket.py`. The right-hand column is the Kore node each one replaces.

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
| `pd_create_ticket` | service | Builds the payload, creates the Zendesk ticket, adds the private transcript, thanks the customer with the ticket number. On failure offers a retry | `PC_HomeDelivery_Script_PrepareZendeskData`, `…_Service_CreateTicket`, `…_ConversationPrivateNote`, `…_ThanksMessage`, `…_Message_TicketFailed` |

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

Every question is its own pause point, and every one accepts a cancel request.

- **Purchaser name.** One to six words of letters (hyphens and apostrophes allowed). Two names joined by "or" or "and" are
  not accepted; the bot asks which one. "I don't know" stores `Not provided`; three invalid replies continue without it.
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
  up. Names without quantities are not guessed: the bot asks for the total. "I don't know" is accepted.
- **Slots.** Each product has a name, quantity, condition and, for a wrong item, the expected product. Kore's questions are
  asked in Kore's order for the first thing missing. A different product name always gets its own slot, so a product the
  customer named is never dropped or overwritten. "1 new and 1 used cleanser" makes two slots. "They are all new" fills
  every condition still empty.
- **Conditions** are `new`, `used`, `damaged` or `wrong product`, mapped from Kore's synonym lists. A bare quantity or a
  condition word is read by code and never reaches the model.
- **Finishing.** The list ends when the quantities reach the count. If the count is unknown, or the customer says "that's
  all" early, an incomplete product is asked about once and then left out. Over the count, everything is kept and flagged.
  Five replies with nothing usable end the step with what exists.
- **Confirmation.** The list is read back and a yes/no is asked. Kore asks for confirmation but never reads the answer.
- **Saved** (`pd_save_products`, Kore's `SavingAgentData`): `productsToReturn` (name, quantity, condition code 1 or 2,
  expected product), `all_products_summary`, `collectedUnits`, `countMismatch` and `collectionOutcome` (`clean`,
  `partial_review` or `nothing_submittable`) for the ticket step.

### The Zendesk ticket (`ticket.py`, `shared/zendesk.py`)

- **Payload.** One plain function, `build_ticket_payload`, replaces Kore's six string fragments and service-node tokens:
  subject, requester, HTML body (customer, voyage, spa record, return, products, additional information), form, brand,
  group, `urgent` priority, tags, and the custom fields (inquiry type, category from the delivery type, return reason,
  return status, created by, cruise line, ship, priority, sail date). A custom field with no value is left out, not sent blank.
- **Everything the customer typed is HTML-escaped** before it goes into the ticket. Kore pastes it in raw.
- **One ticket per request.** Each ticket carries an `external_id`. A create is never retried blindly: before a retry the bot
  looks for a ticket with that id, so a timeout that actually created the ticket does not produce a duplicate.
- **Failure.** The customer keeps their answers and is offered a retry (three attempts), then told nothing was submitted.
  Kore ends the dialog and loses everything.
- **Private note.** The whole conversation of this request (`session["transcript"]`, started fresh with every new request)
  is added as a private comment. If the note fails the ticket still stands and the customer is thanked.
- **Result.** `session["TicketId"]` for the later steps (document request).

## Conversation state and variables

State has two dictionaries, with Kore's names:

| Dictionary | Kore equivalent | Holds |
|---|---|---|
| `session` | `context.session.BotUserSession` | Which dialog is active, the paused step (`dialog_step`), the first message, history, vessel and date results, private copies (`piiEntities`), `cruiseDates`, `purchaseDetails`, `usr_*` results, purchase answers (`spa_record_name`, `CabinNumber`, `PurchasedDate`, `purchaseDateAPI`, `isWithinReturnPolicyPeriod`, `requestedDate`, `products`) |
| `entities` | `context.entities` | Values collected in the dialog: name, email, ship, vessel id, start and end date, `SpaRecordName`, `CabinNumber`, `PurchasedDate`, `Country`, `ProductCount` |

Per message: `turn_entry` loads the state, nodes read and edit the dictionaries in place, and `persist` saves them once at the
end (so a failed turn saves nothing). State lives in one JSON file per key under `MARINA_STATE_DIR`. The load key is the
`conversation_id` or the client's `previous_response_id`; the save keys are the `conversation_id` and this
`response_id`, so chaining by `previous_response_id` gives one snapshot file per turn.

## Key mechanisms

- **Routing.** Every node sets `turn.route` to the id of the next node, and every edge is gated on `route == target id`.
  The graph shows the allowed transitions; each node's Python picks one.
- **Pause and resume.** A node that needs an answer asks its question, stores its own id in `session["dialog_step"]`, and ends
  the turn. On the next message the dialog's entry node jumps straight back to that node with `turn.resuming = True`, and the
  node treats the text as its answer and clears the flag. This is why a "yes" meant for one question can never be taken as
  the answer to another.
- **Node types** (`shared/flow.py`, `shared/agent_node.py`): `ScriptNode`, `MessageNode`, `PromptNode`, `SlotNode` (ask and
  validate, retry with an error text), `ConfirmNode` (yes/no) and `AgentNode` (model with tools).
- **Model use.** Dialog control is ordinary code. The model reads the first message, drives the vessel agent through tools,
  reads the purchase details from the first message, and acts as a fallback for unusual date wording. Its output is always validated by code.
- **The SDK's built-in pause and resume (`request_info`) is not used.** It surfaces a pause as a tool call that the client
  must answer with a tool result, which does not suit a plain-text chat channel.

## Hosting notes

- `main.py` uses native workflow hosting (`ResponsesHostServer(workflow=…, parse_response=…)`).
- **Stable workflow names** (`marina-bot`, `product-return`) are required: the host refuses to continue a conversation if the
  rebuilt graph has a different name.
- **Checkpoint allowlist.** The host checkpoints each turn's messages and restores only types allowed by name, so `main.py`
  lists `models:TurnInput` and `models:Turn`. Any new class sent between nodes as a message must be added there.
- **Local sessions.** Locally a request needs an `agent_session_id` so successive turns share a scope; `chat.py` echoes the
  one the server returns. In a hosted deployment the platform supplies it.
- The hosting package is a **beta** release, so expect API changes when upgrading.

## Known limitations

- **No automated tests and no offline mode.** The earlier test suite and its fake-data stub were removed to keep the code
  simple, so changes are verified by running real conversations with `chat.py`. The suite is in git history (commit
  `70084a9`) if it is needed again. The bot needs the real Foundry model and the real OSW APIs to run.
- **State store.** Local JSON files: no expiry, no encryption (name and email are stored in clear text), and simultaneous
  messages from one customer can overwrite each other. Replace `shared/state_store.py` (two methods) with Cosmos DB or the
  Foundry state store before production.
- **Ticket gaps.** The ticket has no booking number, card last four or attachments yet ("N/A"), and the return-document
  API calls that follow the ticket in Kore are not ported. Zendesk field ids and the form must match the Zendesk you
  point at; a wrong id is rejected by Zendesk and shows up as a failed create in the log (status code only).
- **No cleanup between dialogs.** Ending a dialog clears only `active_dialog` and `dialog_step`. Vessel flags and `vessel_id`
  persist, so a second return in the same conversation would skip the ship question. Kore's `ClearData` step is not ported.
- **Simplified checks.** Name, email, purchaser name, cabin, phone, delivery type and return reason validation are plain
  rules standing in for Kore's built-in entity types and agent-node prompts. The delivery-type and return-reason keyword
  lists are my own; a reply that fits none gets a "please choose" message rather than a guess. The empathy
  check node has no configuration in the Kore export and was skipped.
- **Models.** Prompts run on the deployed model (for example `gpt-5.4-mini`), not Kore's `gpt-5.1`, and Kore's temperature and
  token settings are not applied.
- **Not deployed.** There is no `azure.yaml` or Dockerfile yet. Use the Foundry samples (`05-workflows`) as the template.

## Security

- Credentials are read from environment variables only. `.env` is git-ignored.
- The OAuth client secret appeared in plain text in the Postman collections the APIs were taken from. Rotate it and keep the
  new value out of the repo.
- Logs contain dates, vessel ids, node names and Zendesk status codes, never tokens, the client secrets or customer details.
- The Zendesk credential is read from the environment only. Use an API token for a dedicated Zendesk user with the
  least access that can create tickets and add comments.
- The conversation transcript, name, email and phone are stored in the state files in clear text (see the state-store
  limitation above) and sent to Zendesk, where they belong. Tickets are created in whichever Zendesk `ZENDESK_BASE_URL` names.
