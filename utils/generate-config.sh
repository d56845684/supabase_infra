#!/usr/bin/env bash
set -euo pipefail

# Generate supabase/config.toml from a .env file.
# Usage: ./utils/generate-config.sh [path/to/.env]

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${1:-${ROOT_DIR}/.env}"
CONFIG_DIR="${ROOT_DIR}/supabase"
CONFIG_FILE="${CONFIG_DIR}/config.toml"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing env file: ${ENV_FILE}" >&2
  exit 1
fi

declare -A ENV_VARS
while IFS= read -r line; do
  [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue

  # Strip a leading "export " if present.
  if [[ ${line} =~ ^[[:space:]]*export[[:space:]]+(.*)$ ]]; then
    line=${BASH_REMATCH[1]}
  fi

  key=${line%%=*}
  value=${line#*=}

  key=${key//[[:space:]]/}
  value=${value#${value%%[![:space:]]*}}
  ENV_VARS["${key}"]=${value}
done < "${ENV_FILE}"

for key in "${!ENV_VARS[@]}"; do
  export "${key}=${ENV_VARS[${key}]}"
done

POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_DB=${POSTGRES_DB:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_HOST=${POSTGRES_HOST:-db}

# Avoid set -u aborts when POSTGRES_PASSWORD is missing so we can print
# a clearer error message for the user.
POSTGRES_PASSWORD=${POSTGRES_PASSWORD-}
if [[ -z "${POSTGRES_PASSWORD}" ]]; then
  echo "POSTGRES_PASSWORD is required in ${ENV_FILE}" >&2
  exit 1
fi

REF=${SUPABASE_PROJECT_REF:-local}
API_HOST=${SUPABASE_API_HOST:-kong}
KONG_HTTP_PORT=${KONG_HTTP_PORT:-8000}
API_URL=${SUPABASE_API_URL:-"http://${API_HOST}:${KONG_HTTP_PORT}"}

DEFAULT_SCHEMAS=${PGRST_DB_SCHEMAS:-"public,storage,graphql_public"}
MIGRATION_SCHEMAS=${SUPABASE_MIGRATION_SCHEMAS:-"${DEFAULT_SCHEMAS},extensions"}

CONNECTION="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

mkdir -p "${CONFIG_DIR}"

cat > "${CONFIG_FILE}" <<EOF
[project]
ref = "${REF}"

[api]
url = "${API_URL}"

[db]
connection = "${CONNECTION}"
shadow_connection = "${CONNECTION}"

[migrations]
schema = "${MIGRATION_SCHEMAS}"
EOF

echo "Wrote ${CONFIG_FILE} using ${ENV_FILE}"
