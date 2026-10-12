# Deploying the Marina bot to Microsoft Foundry

A step-by-step runbook for deploying the bot as a **Foundry hosted agent**. It follows the Foundry sample
`samples/python/hosted-agents/agent-framework/responses/05-workflows` and the official guides
([deploy a hosted agent](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/deploy-hosted-agent),
[manage a hosted agent](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/manage-hosted-agent)).
Commands are for bash (WSL). Where an `azd` prompt or output differs from what is described here, trust the tool and
check the official guide: these steps were prepared from the samples and have not been run against your subscription.

## What changes when the bot runs in Foundry

| Local | In Foundry | What was done about it |
|---|---|---|
| `az login` identity | The agent has its **own Microsoft Entra identity** | Roles are granted to that identity (step 4) |
| Settings from `.env` | `.env` is not shipped | Settings are passed as the agent's environment variables from `azure.yaml` (step 3) |
| State in files under `~/marina_state` | Containers restart, scale and expire sessions | State lives in **Azure Blob Storage** (`BlobStateStore`, steps 1 and 4) |
| `FOUNDRY_PROJECT_ENDPOINT` from `.env` | Injected by Foundry | Nothing to set |
| `chat.py`, `ui.py`, `web/` | Not deployed | Test with the Foundry Agent Playground or `azd ai agent invoke` |

Files added for this: `azure.yaml` (repo root), `src/marina-bot/Dockerfile`, `.dockerignore`, `.azdignore`,
`scripts/set-azd-env.sh`, and the Blob state store in `src/marina-bot/shared/state_store.py`.

## Before you start

You need:

- The tools: Azure CLI (`az`), Azure Developer CLI (`azd` 1.27.1 or newer), Python 3.13 and `uv` (already installed for local runs).
- Your Foundry project (`https://marina-poc.services.ai.azure.com/api/projects/proj-default`) and its model deployment.
- A resource group where a storage account can be created.
- **Someone who can assign Azure roles.** Two steps below (4) need `Owner` or `User Access Administrator` on the scope.
  If that is not you, step 4 ends with a message you can send to your admin.
- Your `src/marina-bot/.env` filled in (see the README). The bot refuses to start in Foundry for the same missing
  settings it refuses locally.

**Use the Zendesk sandbox for the first deployment.** The deployed bot creates real tickets in whichever Zendesk
`ZENDESK_BASE_URL` names.

## Step 1. Create the state container (once)

State must outlive a container restart, so the bot stores each conversation as a JSON blob. The storage account
already exists: **`oswdevpoc`**. Only the container is needed: **`marina-state-ai-foundry`**.

```bash
az login
az account set --subscription "<subscription name or id>"

SA="oswdevpoc"
CONTAINER="marina-state-ai-foundry"
RG="<resource group of oswdevpoc>"      # az storage account show --name oswdevpoc --query resourceGroup -o tsv

# Needs a data role for you (Storage Blob Data Contributor on the account); if it is refused, create the container in the
# portal (Storage account > Containers > + Container, private access) or ask your admin.
az storage container create --account-name "$SA" --name "$CONTAINER" --auth-mode login
```

The account is shared, so check two things before relying on it:

- **Network access.** If `oswdevpoc` limits access to selected networks or private endpoints, the hosted agent must be allowed
  in (Storage account > Networking). A refusal shows up as a 403 in the agent log.
- **Public access.** The container must be private (the default). The state holds names, emails and whole conversations.

**Expire old conversations (a lifecycle rule).** They hold personal data, so they should not live forever. **Careful:
`az storage account management-policy create` replaces the account's whole lifecycle policy.** Look at what is there first:

```bash
az storage account management-policy show --account-name "$SA" --resource-group "$RG"
```

If it answers "not found", you can apply the rules below as they are. If it shows rules, **add these to the existing list**
(portal: Storage account > Lifecycle management > Add a rule, or merge the JSON) instead of replacing them. The numbers are
suggestions; choose the retention your policy requires.

The container holds two kinds of files, and they can be kept for different lengths of time:

- `state/<conversation>.json`: the live working state of a conversation (one file per conversation, rewritten each message).
  Short retention is fine: it is only needed while the customer might still reply.
- `transcripts/<yyyy-mm-dd>/<conversation>.csv`: the complete conversation in Kore's transcript layout (one file per
  conversation, rewritten each message, names, e-mails and phone numbers masked). Keep this as long as you need transcripts.

```json
{
  "rules": [
    {
      "enabled": true,
      "name": "expire-marina-state-ai-foundry-state",
      "type": "Lifecycle",
      "definition": {
        "actions": { "baseBlob": { "delete": { "daysAfterModificationGreaterThan": 7 } } },
        "filters": { "blobTypes": ["blockBlob"], "prefixMatch": ["marina-state-ai-foundry/state/"] }
      }
    },
    {
      "enabled": true,
      "name": "expire-marina-state-ai-foundry-transcripts",
      "type": "Lifecycle",
      "definition": {
        "actions": { "baseBlob": { "delete": { "daysAfterModificationGreaterThan": 90 } } },
        "filters": { "blobTypes": ["blockBlob"], "prefixMatch": ["marina-state-ai-foundry/transcripts/"] }
      }
    }
  ]
}
```

**Clean out test files from earlier runs.** Before the stable-key fix, every message saved a new file named
`state/caresp_….json` (the 21 files you saw for one chat). They hold the customers' details from your test chats and are never read
again, so delete them: in the portal select the `state` folder's `caresp_…` files and Delete, or with the CLI (this uses the
account key; use `--auth-mode login` instead once you have the role):

```bash
az storage blob delete-batch --account-name "$SA" --source "$CONTAINER" --pattern "state/caresp_*" --auth-mode key
```

```bash
az storage account management-policy create --account-name "$SA" --resource-group "$RG" --policy @lifecycle-policy.json
```

Add two lines to `src/marina-bot/.env` (they tell the deployed agent to use Blob Storage; locally they are best left out,
or the bot would write your test conversations to the shared account):

```
STATE_BLOB_ACCOUNT_URL="https://oswdevpoc.blob.core.windows.net"
STATE_BLOB_CONTAINER="marina-state-ai-foundry"
```

**Stopgap while the role is pending: the account's connection string.** If nobody has granted the *Storage Blob Data
Contributor* role yet, you can point the bot at the storage with the account's connection string instead
(Azure portal > storage account `oswdevpoc` > Security + networking > Access keys > Connection string). Add one line to
`.env`, with the quotes (the value contains `;` and `=`):

```
STATE_BLOB_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=oswdevpoc;AccountKey=<key>;EndpointSuffix=core.windows.net"
```

When it is set it is used **instead of** the identity-based access, and the bot logs a warning at start-up. Know what it means:

- The key is a **master key for the whole `oswdevpoc` account** (every container, file share and queue), not just this
  container. Treat it like a password: never paste it into chat or commit it, and **rotate it** (Access keys > Rotate key)
  when you stop using it, and at once if it was ever shared.
- Once deployed, it travels as a plain environment variable of the agent (and sits in `.azure/` on your machine).
- The account must allow shared-key access (some accounts disable it by policy). A refusal is reported as
  "refused the account key".
- Replace it with the role-based access (step 4) as soon as the roles exist: remove the line, run
  `bash scripts/set-azd-env.sh`, and redeploy.

## Step 2 (optional but recommended). Try the Blob store from your machine first

Locally the bot uses files unless `STATE_BLOB_ACCOUNT_URL` is set. To test the storage path before deploying, give **your own
user** the same role on the container (or ask your admin), set the variable for one run, and chat:

```bash
SCOPE=$(az storage account show --name "$SA" --resource-group "$RG" --query id -o tsv)/blobServices/default/containers/$CONTAINER
az role assignment create --assignee "<your user principal name>" --role "Storage Blob Data Contributor" --scope "$SCOPE"

cd src/marina-bot
STATE_BLOB_ACCOUNT_URL="https://$SA.blob.core.windows.net" STATE_BLOB_CONTAINER="$CONTAINER" uv run --no-sync python main.py
# in another terminal: python3 chat.py   (then look for blobs under state/ in the container)
az storage blob list --account-name "$SA" --container-name "$CONTAINER" --auth-mode login --query "[].name" -o tsv
```

## Step 3. Connect `azd` to your Foundry project and deploy

```bash
azd auth login
azd ext install microsoft.foundry            # the Foundry extension (provides `azd ai agent ...`)

cd /mnt/d/marina-foundry-bot                 # the repo root, where azure.yaml is
azd ai agent init -m azure.yaml
```

When it asks, choose your **existing** subscription, the **existing** Foundry project (`marina-poc` / `proj-default`) and the
**existing** model deployment (the one in `AZURE_AI_MODEL_DEPLOYMENT_NAME`), and give the azd environment a name such as `marina-dev`.
**Do not run `azd provision`**: the project and model already exist and `provision` could create extra resources.

Copy your settings into the azd environment, then deploy:

```bash
bash scripts/set-azd-env.sh                  # prints names only, never values; lists any that are still empty
azd deploy
```

`azd` packages `src/marina-bot`, builds it, creates the hosted agent `marina-bot` and prints its details. If the build
fails on dependencies, check that `uv.lock` is committed and current (`cd src/marina-bot && uv lock`).

If `azd ai agent init` rewrites `azure.yaml`, compare it with the version in git: keep the `environmentVariables` block
(older extension versions call it `env:`, a name-to-value map; the content is the same).

## Step 4. Give the agent's identity its roles

The deployed agent has its own identity, separate from yours. Find it, then grant the roles. This step needs someone with
permission to assign roles.

```bash
azd ai agent show -o json        # copy instance_identity.principal_id from the output
PRINCIPAL_ID="<the principal_id>"
```

**a. State storage** (required):

```bash
SCOPE=$(az storage account show --name "$SA" --resource-group "$RG" --query id -o tsv)/blobServices/default/containers/$CONTAINER
az role assignment create --assignee-object-id "$PRINCIPAL_ID" --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Contributor" --scope "$SCOPE"
```

**b. The model**, only if the agent answers with a 401 or "permission denied" from Azure OpenAI (often the platform has
already granted it): assign **Azure AI User** and **Cognitive Services OpenAI User** to the same identity on the Foundry
project (or its account).

Role assignments take a minute or two to apply.

> **Message for your admin** (copy and fill in): "Please assign the role *Storage Blob Data Contributor* to the service
> principal with object id `<principal_id>` on the scope `<SCOPE>` (the `marina-state-ai-foundry` container of storage account `oswdevpoc`). It is the
> identity of the Foundry hosted agent `marina-bot`. If the agent later reports a model permission error, also *Azure AI User* and
> *Cognitive Services OpenAI User* on the Foundry project `proj-default`."

## Step 5. Test the deployed agent

1. **Quick check:** `azd ai agent invoke "I want to return a product"` should answer with the greeting and the name question.
2. **A full conversation:** open the agent in the Foundry portal (**Agent Playground**) and run a return end to end: name,
   email, ship, dates, purchase details, products, `skip` at the upload, then check the Zendesk sandbox for the ticket. Each
   message in the Playground continues the same conversation, which is what exercises the Blob state.
3. **State:** `az storage blob list --account-name "$SA" --container-name "$CONTAINER" --auth-mode login -o table` should show
   `state/…json` blobs growing as you chat.
4. **Logs:** the agent's **Logs** tab in the portal (or the Foundry Toolkit in VS Code). Look for `conversation state: Azure Blob
   Storage` at start-up, and for the missing-settings message if it fails to start.

Known limits of the check: the Playground sends text, so test the **upload** with a front end that can send an https file link
(the attachment function downloads the file itself). The attachment function and the document API have not been run against
the real services yet, so watch the first live run closely.

## Redeploying, and going back

- After a code change: `azd deploy` again. Each deploy creates a new agent version.
- After a setting change: edit `.env`, run `bash scripts/set-azd-env.sh`, then `azd deploy` (the environment variables are
  part of the agent version).
- To go back, deploy the previous commit again (or select the earlier version in the portal, per the manage guide).
- Conversations in progress survive a deploy because their state is in Blob Storage, not in the container.

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Agent does not start; log names missing settings | A required `OSW_*`, `ZENDESK_*`, `ATTACHMENT_*` or `DOCUMENT_*` value is empty in the azd environment. Fill `.env`, run `scripts/set-azd-env.sh`, redeploy |
| Chat shows "Native workflow execution failed…" and the server log says "Azure Storage refused access to the state container" | The identity running the bot has no data role on the container. Locally that is **you** (your `az login`): ask for *Storage Blob Data Contributor* on `marina-state-ai-foundry`. To keep working meanwhile, run on local files: `STATE_BLOB_ACCOUNT_URL= uv run --no-sync python main.py` (an empty value overrides the `.env` line). The server also logs "conversation state storage is NOT usable" at start-up |
| `AuthorizationPermissionMismatch` or 403 from Storage in the log | The role in step 4a is missing, on the wrong scope, or not applied yet (wait a few minutes). Confirm with `az role assignment list --assignee "$PRINCIPAL_ID" --all` |
| 401 or "permission denied" from the model | Step 4b |
| Each message starts a new conversation | State is not persisting: check the log line at start-up and that `STATE_BLOB_ACCOUNT_URL` reached the agent (`azd env get-values` shows names; the value is in `.azure/<env>/.env`) |
| A build error about dependencies | `cd src/marina-bot && uv lock`, commit `uv.lock`, redeploy |
| Zendesk answers 401 or 422 in the log | Wrong credential or a field id that does not belong to the form you point at (status codes only are logged) |
| Works in the portal but `chat.py` cannot reach it | `chat.py` talks to `localhost:8088` only; use the Playground or `azd ai agent invoke`. `ui.py` can reach the deployed agent: `BOT_URL=<endpoint>` (the Responses URL from `azd ai agent show`) and `az login`; it sends your Entra token |
| Debug panel is empty | Set `DEBUG_TRACE=true` on the bot (`azd env set DEBUG_TRACE true`, `bash scripts/set-azd-env.sh`, `azd deploy`) and start `ui.py` with `UI_DEBUG=true` and the same `STATE_BLOB_*` settings as the bot. Turn it off again for production: the trace holds customer text |

## Before this serves real customers

This deployment is a **sandbox POC**. Before production:

1. **Secrets.** They are plain environment variables of the agent, readable by anyone who can read the agent definition and
   stored in `.azure/` on your machine. Move them to Azure Key Vault (read at start-up with the agent's identity) and rotate
   the OSW client secret, which appeared in the Postman collections.
2. **State.** Add the retention rule (step 1), decide how long a transcript may be kept, and consider Cosmos DB if many
   customers will chat at once (Blob has no concurrency control: two messages at the same moment from one customer, last write wins).
3. **Zendesk.** Point at production only after the sandbox run, with a dedicated API user.
4. **Network.** Decide whether the storage account, Zendesk and the document API should be reachable only through private
   endpoints, and whether the attachment function restricts the hosts it downloads from.
5. **Front end.** A customer-facing chat must send file links the attachment function can fetch, and must carry the
   conversation ids the Responses protocol uses.
6. **Monitoring.** Application Insights is connected by the platform; add alerts on the ticket-failure and document-failure log lines.
7. **Tests.** Add the development test suite back to the repo and run it in CI before each `azd deploy`.
