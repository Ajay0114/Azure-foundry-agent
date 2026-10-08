# Marina bot on Microsoft Foundry: architecture

This repo rebuilds the Marina (OneSpaWorld) bot, currently a Kore.ai bot, as a hosted agent on
Microsoft Foundry using Microsoft Agent Framework workflows. The POC target is the **Product Return**
dialog, which is the Kore dialog task `PC_HomeDelivery`. Its source is the Kore export in
`docs/kore-reference/`.

Status: the intake stage runs end to end on a live model. The remaining stages are not ported yet (see
[Status](#status)).

## 1. The core idea

Kore keeps a dialog open and waits for the user's answer. A Foundry hosted agent does not: every user
message arrives as a separate request. The repo therefore works like this:

1. **One chat message = one run of a workflow graph.**
2. At the end of each run the **dialog state is saved** (who the user is, which dialog is active, which
   question was just asked).
3. On the next message the graph **resumes at the node that asked the question**, and treats the message
   as its answer.

We do not use the framework's pause/resume feature (`request_info`). It surfaces a pause as a tool call
that the client must answer with a tool result, which suits programmatic clients but not a chat channel
where the user just types text.

## 2. Kore concept to Agent Framework mapping

| Kore | Here | Where |
|---|---|---|
| Dialog task (intent) | One sub-workflow (`WorkflowExecutor`) | `dialogs/<name>/workflow.py` |
| Intent detection | `IntentClassifier` (one LLM call returns a label) | `orchestrator.py` |
| Script node (JS) | `ScriptNode` over plain Python | `shared/flow.py`, `dialogs/*/…_scripts.py` |
| Message node | `MessageNode` | `shared/flow.py` |
| Entity node (ask and validate) | `SlotNode` | `shared/flow.py` |
| Dialog act yes/no node | `ConfirmNode` | `shared/flow.py` |
| Prompt node (generativeai) | `PromptNode` + a prompt file | `shared/flow.py`, `dialogs/*/prompts/` |
| Agent node (aiassist) | *not ported yet* | |
| Service node (REST) | *not ported yet* | |
| Logic node / transition conditions | Python in the node, then `turn.route` | node code |
| `context.session.BotUserSession` | `Turn.session` (persisted) | `models.py`, `shared/session.py` |
| `context.entities` | `Turn.entities` (persisted) | `models.py` |
| Kore `{{context…}}` in prompts | `{{name}}` placeholders, filled by `shared/prompts.py` | `dialogs/*/prompts/` |

Kore names (`piiEntities`, `initialMessage`, `PC_Common_1_Entity_Name`) are kept as they are, so any
ported node can be compared line by line with `docs/kore-reference/nodes/`.

## 3. Repository layout

```
docs/
  ARCHITECTURE.md             this file
  kore-reference/             read-only reference extracted from the Kore export (not run)
    extract.js                regenerates the files below from appDefinition.json
    flow.md                   the 94-node graph in execution order, with conditions
    index.md                  table of all nodes by type
    nodes/                    one file per Kore node: config, prompts, scripts, message texts
src/marina-bot/
  main.py                     entry point: Foundry client, hosting options, starts the server
  orchestrator.py             top-level workflow: load state, route, run a dialog, save state
  models.py                   TurnInput (from the host) and Turn (passed between nodes)
  dialogs/
    product_return/
      workflow.py             the dialog's node graph (sub-workflow)
      intake_scripts.py       ported Kore script nodes, plain Python, no framework imports
      prompts/                prompt text copied from Kore, one .md per prompt node
  shared/                     building blocks used by every dialog
    flow.py                   node classes and routing helpers
    state_store.py            saves and loads dialog state between turns
    session.py                DialogContext: stand-in for Kore's BotUserSession / entities
    prompts.py                loads a prompt file and fills its {{placeholders}}
    validators.py             name, email and yes/no parsing
  tests/                      unit and multi-turn tests, no Azure needed
  chat.py                     terminal chat client for local testing only
  pyproject.toml, uv.lock, uv.toml   dependencies (the lock file pins exact versions)
  .env                        FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME (git-ignored)
```

Rules of thumb:
- `dialogs/` grows with the project, one folder per Kore dialog. `shared/` should stay small.
- Logic that needs no framework (parsing, validation, date handling) lives in plain functions such as
  `intake_scripts.py`, so it can be unit tested quickly.
- Prompts live in `.md` files, not in code, so they can be reviewed and diffed on their own.

## 4. How one message is processed

```
client ──POST /responses──► ResponsesHostServer            (Foundry hosting library, main.py)
                              │ parse_response(): message text, keys to load / save state
                              ▼
                      build a fresh workflow graph            (orchestrator.py)
                              ▼
 turn_entry ─[no active dialog]─► intent_classifier ─┬─► product_return ─► persist ─► reply
      │                          (LLM call)           └─► fallback ───────► persist
      └────────[dialog active]──────────────────────────► product_return
```

Inside `product_return` (`dialogs/product_return/workflow.py`), edges match the Kore transitions:

```
pr_entry ─► pr_initial_message ─► pr_greeting ─► pr_name ─► pr_redact_name ─► pr_email
                                                                                │
          pr_delete_email ◄──[no]── pr_email_confirm ◄── pr_redact_email ◄──────┘
                │                          └──[yes]──► pr_extract (LLM) ─► pr_process_extracted ─► pr_next
                └────► pr_email
```

### The executors

| Executor | Does |
|---|---|
| `TurnEntry` | Loads saved state by key, builds the `Turn`, routes to the active dialog or to the classifier |
| `IntentClassifier` | One LLM call returning `PRODUCT_RETURN` or `OTHER`; marks the dialog active |
| `product_return` | The sub-workflow; its first node is `pr_entry` |
| `Fallback` | Reply for anything else |
| `Persist` | Appends the exchange to `conversationHistoryString` (last 10 lines), saves state, returns the reply text |

## 5. The four mechanisms

1. **Routing.** Every node sets `turn.route` to the id of the node that runs next. Every edge is added
   with `connect()`, which makes it fire only when `route == target id`. The graph documents the allowed
   transitions, and each node's Python decides which one to take.
2. **Pausing.** A node that needs an answer says its question, writes its own id to
   `session["dialog_step"]`, and ends the turn (`pause()`).
3. **Resuming.** `pr_entry` reads `dialog_step`, sets `turn.resuming = True`, and routes straight to
   that node. The node sees `resuming` and treats `turn.text` as the answer. A node clears `resuming`
   once it has consumed the answer.
4. **State.** `TurnEntry` loads and `Persist` saves one JSON document per conversation:
   `session` (active dialog, dialog step, `initialMessage`, `piiEntities`, history, node outputs) and
   `entities`.

Related behaviours:
- A `SlotNode` is **skipped** when its entity is already in `entities` (Kore's reuse behaviour). The
  email "No" path deletes the entity first so the question is asked again.
- Once a dialog is active, later messages **skip the classifier**. `finish()` clears the active dialog.

## 6. Hosting details that matter

`main.py` uses the native workflow mode: `ResponsesHostServer(workflow=factory, parse_response=...)`.
- **A new graph is built for every request.** The graph keeps no state; all state is in the saved
  document.
- **State keys.** `parse_response` loads state by `conversation_id` or `previous_response_id` and saves
  under `conversation_id` and this `response_id`. A client that chains with `previous_response_id`
  therefore keeps its dialog.
- **Workflow names must be stable** (`marina-bot`, `product-return`). The host refuses to continue a
  conversation if the rebuilt graph has a different name.
- **Checkpoint allowlist.** The host checkpoints each turn's messages and only restores types allowed by
  name, so `main.py` lists `models:TurnInput` and `models:Turn`. Any new class that travels between
  executors as a message must be added there.
- **Local sessions.** Locally, requests need an `agent_session_id` to share a scope, so `chat.py` echoes
  the one the server returns. In a hosted deployment the platform supplies it.
- **Two state systems exist.** The host's checkpoints are required by native hosting, but our resume does
  not depend on them. Dialog state is ours (`shared/state_store.py`).

## 7. Local setup and commands

Run these from `src/marina-bot` (WSL, Python 3.13 through `uv`).

```bash
uv sync --python 3.13                       # install dependencies
az login                                    # DefaultAzureCredential uses this
uv run --no-sync python -m unittest         # tests, no Azure needed
uv run --no-sync python main.py             # serve on http://localhost:8088
python3 chat.py                             # in a second terminal
```

`.env` needs `FOUNDRY_PROJECT_ENDPOINT` and `AZURE_AI_MODEL_DEPLOYMENT_NAME`. Your user needs the
**Foundry User** role on the Foundry resource.

## 8. How to port the next Kore node

1. Find the node in `docs/kore-reference/flow.md`, and its details in `nodes/<type>__<name>.md`.
2. Pick the matching class from the mapping table above.
3. For scripts with real logic, put a plain function in a `*_scripts.py` and add tests that mirror the
   Kore behaviour.
4. For a prompt node, copy the prompt into `prompts/<name>.md`, replacing `{{context…}}` variables with
   short `{{names}}`.
5. Add the executor in `workflow.py`, with an id of the form `pr_<name>`, and add every Kore transition
   as a `connect(builder, from, to)` pair.
6. If the node asks the user something, add its id as an edge from `pr_entry` (a resume point) and list
   it in `output_from`.
7. Add a case to `tests/test_conversation.py` and run the tests.

To add a whole new dialog: create `dialogs/<name>/workflow.py` with its own entry node, wrap it in a
`WorkflowExecutor`, add one label to the classifier prompt, and add edges from `turn_entry`,
`intent_classifier` and to `persist`.

## 9. Status

Ported (Kore `PC_HomeDelivery`, in order): initial message, greeting, name, email with confirmation and
the delete-and-retry loop, cruise-entity extraction prompt, and extracted-entity processing with date
normalization. `pr_next` is a placeholder that prints what was captured.

Not ported yet:
- Agent nodes: `HD_VesselLookupAgent`, `HD_CruiseDateOrchestrator`, `PC_HomeDelivery_Agent_*`
  (ProductDetails, ProductCount, PurchasedDate, CabinNumber, SpaRecordName, ReturnDetails).
- Service nodes: the vessel and itinerary services (`PostCruiseServiceOrchestrationEngine`), Zendesk
  ticket and private notes, document creation, and file scan and upload.
- The remaining prompt nodes, logic branches, error handling, and the cancel and feedback paths.

## 10. Known approximations and risks

- Name and email validation are simple regexes standing in for Kore's built-in entity types.
- Kore's `PC_Common_Empathy_Check` has no configuration in the export and was skipped.
- Prompts run on the deployed `gpt-5.4-mini`, not Kore's `gpt-5.1`, and Kore's temperature and token
  settings are not applied.
- State is JSON files under `~/marina_state` (override with `MARINA_STATE_DIR`). Replace
  `shared/state_store.py` with Cosmos DB or the Foundry state store before production.
- Credentials in the Kore export are `{{env.…}}` placeholders (Zendesk, `AzureFunctionKey`,
  `PostCruiseServiceOrchestrationEngine_Api_key`, and others). They must become environment variables or
  Key Vault references, never values in the repo.
- Deployment files (`azure.yaml`, `Dockerfile`) are not in the repo yet. Use
  `foundry-samples/.../05-workflows` as the template.
- The native workflow hosting API in `agent-framework-foundry-hosting` is a beta release (version
  `1.0.0b…`), so expect API changes when upgrading.
