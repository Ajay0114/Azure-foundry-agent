#!/usr/bin/env bash
# Copies the settings the deployed agent needs from src/marina-bot/.env into the azd environment, where azure.yaml
# reads them as ${NAME}. Run it from the repo root after `azd ai agent init`, and again whenever a value changes.
#
#   bash scripts/set-azd-env.sh [path-to-env-file]
#
# It prints the NAMES it sets and the names that are empty, never the values (several are secrets).
# The azd environment (.azure/) holds those secrets in plain text on this machine: it is git-ignored, keep it that way.
set -euo pipefail

ENV_FILE="${1:-src/marina-bot/.env}"
[ -f "$ENV_FILE" ] || { echo "Cannot find $ENV_FILE" >&2; exit 1; }
command -v azd >/dev/null || { echo "azd is not installed or not on PATH" >&2; exit 1; }

# Foundry injects FOUNDRY_PROJECT_ENDPOINT itself; AZURE_AI_MODEL_DEPLOYMENT_NAME is set by `azd ai agent init`
# (it is only copied from .env when azd does not have it yet).
NAMES=(
  AZURE_AI_MODEL_DEPLOYMENT_NAME STATE_BLOB_ACCOUNT_URL STATE_BLOB_CONTAINER STATE_BLOB_CONNECTION_STRING
  OSW_BASE_URL OSW_TOKEN_URL OSW_CLIENT_ID OSW_CLIENT_SECRET OSW_VESSELS_SCOPE OSW_ITINERARY_SCOPE
  ZENDESK_BASE_URL ZENDESK_AUTHORIZATION ZENDESK_FORM_ID ZENDESK_BRAND_ID ZENDESK_RETURN_GROUP_ID
  ZENDESK_FIELD_CREATED_BY ZENDESK_FIELD_PRIORITY ZENDESK_FIELD_INQUIRY_TYPE ZENDESK_FIELD_CATEGORY
  ZENDESK_FIELD_CRUISE_LINE ZENDESK_FIELD_CRUISE_SHIP ZENDESK_FIELD_SAIL_DATE ZENDESK_FIELD_PRODUCT_REASON
  ZENDESK_FIELD_RETURN_STATUS
  ATTACHMENT_API_URL ATTACHMENT_API_KEY
  DOCUMENT_API_URL DOCUMENT_CLIENT_ID DOCUMENT_CLIENT_SECRET DOCUMENT_RETURNS_SCOPE DOCUMENT_TRANSACTIONS_SCOPE
)

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

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
