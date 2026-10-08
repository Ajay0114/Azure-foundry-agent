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
| Intake: greeting, name, email with confirmation and retry | Spa-record name, product details, product count, purchase date, cabin and return-details agents |
| Entity extraction from the first message (Kore prompt, verbatim) | Validation layer |
| Vessel lookup agent on the real OSW vessel API | Document creation, Zendesk ticket and private notes, file scan and upload |
| Cruise dates: parser, voyage API validation, nearest-voyage confirmation | Error handling, cancel and feedback paths, clearing variables between dialogs |
| Terminal chat client for local runs | Deployment to Foundry, a production state store, automated tests |

About 14 of the dialog's 92 Kore nodes are ported. `pr_next` in the flow below is a placeholder that stands in for
the rest.

## Quick start

Everything runs from `src/marina-bot` (Python 3.13 with [uv](https://docs.astral.sh/uv/); developed on WSL).

```bash
cd src/marina-bot
uv sync --python 3.13                 # install dependencies
az login                              # DefaultAzureCredential uses this to reach Foundry
```

Create `src/marina-bot/.env` (it is git-ignored). Never commit it.

| Variable | Needed | Meaning |
|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | yes | `https://<account>.services.ai.azure.com/api/projects/<project>` |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | yes | Name of the chat model deployment (for example `gpt-5.4-mini`) |
| `OSW_TOKEN_URL` | yes | OAuth token endpoint (Azure Entra ID, client credentials) |
| `OSW_CLIENT_ID` | yes | OAuth client id |
| `OSW_CLIENT_SECRET` | yes | OAuth client secret. A secret: keep it in `.env` or Key Vault only |
| `OSW_VESSELS_SCOPE` | yes | `api://<id>/.default` for the vessels API |
| `OSW_ITINERARY_SCOPE` | yes | `api://<id>/.default` for the itinerary API |
| `OSW_BASE_URL` | optional | Defaults to `https://oswbus-dev.onespaworld.com` |
| `MARINA_STATE_DIR` | optional | Where conversation state files go. Defaults to `~/marina_state` |

If a required `OSW_*` value is missing, the bot stops at start-up with a message naming the missing settings.

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
    │       └── prompts/            Prompt text copied from Kore, one .md per prompt node
    ├── shared/                 Building blocks used by every dialog
    │   ├── flow.py                 Node types (script, message, prompt, question, yes/no) and routing helpers
    │   ├── agent_node.py           The "model with tools" node and its Foundry runner
    │   ├── dates.py                Deterministic date parser and date rules
    │   ├── llm_dates.py            Model fallback for dates the parser cannot read (typed structured output)
    │   ├── osw.py                  Real OneSpaWorld vessel and voyage API client (OAuth, search, nearest voyage)
    │   ├── deps.py                 One bundle of outside connections (model, agent runner, OSW, clock)
    │   ├── state_store.py          Saves and loads conversation state between messages (JSON files)
    │   ├── session.py              DialogContext: the session/entities dictionaries, Kore's key names
    │   ├── prompts.py              Fills {{placeholders}} in prompt files
    │   └── validators.py           Name and email parsers
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

Node ids are in `workflow.py` and `cruise_dates.py`. The right-hand column is the Kore node each one replaces.

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
| `pr_next` | placeholder | Prints what was captured; stands in for the unported nodes | - |

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

## Conversation state and variables

State has two dictionaries, with Kore's names:

| Dictionary | Kore equivalent | Holds |
|---|---|---|
| `session` | `context.session.BotUserSession` | Which dialog is active, the paused step (`dialog_step`), the first message, history, vessel and date results, private copies (`piiEntities`), `cruiseDates`, `usr_*` results |
| `entities` | `context.entities` | Values collected in the dialog: name, email, ship, vessel id, start and end date |

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
  and acts as a fallback for unusual date wording. Its output is always validated by code.
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
- **No cleanup between dialogs.** Ending a dialog clears only `active_dialog` and `dialog_step`. Vessel flags and `vessel_id`
  persist, so a second return in the same conversation would skip the ship question. Kore's `ClearData` step is not ported.
- **Simplified checks.** Name and email validation are plain rules standing in for Kore's built-in entity types. The empathy
  check node has no configuration in the Kore export and was skipped.
- **Models.** Prompts run on the deployed model (for example `gpt-5.4-mini`), not Kore's `gpt-5.1`, and Kore's temperature and
  token settings are not applied.
- **Not deployed.** There is no `azure.yaml` or Dockerfile yet. Use the Foundry samples (`05-workflows`) as the template.

## Security

- Credentials are read from environment variables only. `.env` is git-ignored.
- The OAuth client secret appeared in plain text in the Postman collections the APIs were taken from. Rotate it and keep the
  new value out of the repo.
- Logs contain dates, vessel ids and node names, never tokens or the client secret.
