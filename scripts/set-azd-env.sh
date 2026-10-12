#!/usr/bin/env bash
# Copies the settings the deployed agent needs from src/marina-bot/.env into the azd environment, where azure.yaml
# reads them as ${NAME}. Run it from the repo root after `azd ai agent init`, and again whenever a value changes.
#
#   bash scripts/set-azd-env.sh [path-to-env-file]
#
# It prints the NAMES it sets and the names that are empty, never the values (several are secrets).
# The azd environment (.azure/) holds those secrets in plain text on this machine: it is git-ignored, keep it that way.
set -euo pipefail

export AZD_SKIP_UPDATE_CHECK=1          # no "update available" notice after every azd call
ENV_FILE="${1:-src/marina-bot/.env}"
[ -f "$ENV_FILE" ] || { echo "Cannot find $ENV_FILE" >&2; exit 1; }
command -v azd >/dev/null || { echo "azd is not installed or not on PATH" >&2; exit 1; }

# Foundry injects FOUNDRY_PROJECT_ENDPOINT itself; AZURE_AI_MODEL_DEPLOYMENT_NAME is set by `azd ai agent init`
# (it is only copied from .env when azd does not have it yet).
NAMES=(
  AZURE_AI_MODEL_DEPLOYMENT_NAME STATE_BLOB_ACCOUNT_URL STATE_BLOB_CONTAINER
  OSW_BASE_URL OSW_TOKEN_URL OSW_CLIENT_ID OSW_CLIENT_SECRET OSW_VESSELS_SCOPE OSW_ITINERARY_SCOPE
  ZENDESK_BASE_URL ZENDESK_AUTHORIZATION ZENDESK_FORM_ID ZENDESK_BRAND_ID ZENDESK_RETURN_GROUP_ID
  ZENDESK_FIELD_CREATED_BY ZENDESK_FIELD_PRIORITY ZENDESK_FIELD_INQUIRY_TYPE ZENDESK_FIELD_CATEGORY
  ZENDESK_FIELD_CRUISE_LINE ZENDESK_FIELD_CRUISE_SHIP ZENDESK_FIELD_SAIL_DATE ZENDESK_FIELD_PRODUCT_REASON
  ZENDESK_FIELD_RETURN_STATUS
  ATTACHMENT_API_URL ATTACHMENT_API_KEY
  DOCUMENT_API_URL DOCUMENT_CLIENT_ID DOCUMENT_CLIENT_SECRET DOCUMENT_RETURNS_SCOPE DOCUMENT_TRANSACTIONS_SCOPE
)

# Optional: always set (to the value in .env, else to the bot's own default, else to empty) so that `azd ai agent doctor` does
# not report them as missing. Never reported as missing here: an empty value means "use the default".
OPTIONAL=(STATE_BLOB_CONNECTION_STRING ZENDESK_TAGS DOCUMENT_TOKEN_URL ZENDESK_FIELD_SPA_MANAGER_EMAIL CALLBACK_SPA_MANAGER_EMAIL_OVERRIDE CALLBACK_UPLOAD_API_URL CALLBACK_UPLOAD_API_KEY REDRIVE_API_URL REDRIVE_API_KEY DEBUG_TRACE TRANSCRIPT_ENABLED TRANSCRIPT_MASK_PII TRANSCRIPT_BOT_NAME TRANSCRIPT_CHANNEL)
declare -A DEFAULTS=([ZENDESK_TAGS]="kore_ai,tag_website" [DEBUG_TRACE]="false" [TRANSCRIPT_ENABLED]="true" [TRANSCRIPT_MASK_PII]="true"
                     [TRANSCRIPT_BOT_NAME]="Marina" [TRANSCRIPT_CHANNEL]="Foundry")

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

DEFAULTS[DOCUMENT_TOKEN_URL]="${OSW_TOKEN_URL:-}"            # same tenant as the OSW token endpoint unless told otherwise
for name in "${OPTIONAL[@]}"; do
  value="${!name:-}"
  [ -n "$value" ] || value="${DEFAULTS[$name]:-}"
  azd env set "$name" "$value" >/dev/null
  if [ -n "$value" ]; then echo "set    $name (optional)"; else echo "set    $name (optional, empty)"; fi
done

missing=()
for name in "${NAMES[@]}"; do
  value="${!name:-}"
  if [ -z "$value" ]; then
    missing+=("$name")
    continue
  fi
  if [ "$name" = "AZURE_AI_MODEL_DEPLOYMENT_NAME" ] && azd env get-value "$name" >/dev/null 2>&1; then
    echo "kept   $name (already set by azd)"
    continue
  fi
  azd env set "$name" "$value" >/dev/null
  echo "set    $name"
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo
  echo "Empty in $ENV_FILE (the agent will refuse to start without the required ones):"
  printf '  %s\n' "${missing[@]}"
fi
