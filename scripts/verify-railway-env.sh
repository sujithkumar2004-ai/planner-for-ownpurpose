#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-}"

if [[ -n "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Env file not found: $ENV_FILE" >&2
    exit 1
  fi
  while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" =~ ^# ]] && continue
    key="${key%%[[:space:]]*}"
    value="${value%$'\r'}"
    export "$key=$value"
  done < "$ENV_FILE"
fi

required=(
  DATABASE_URL
  DIRECT_URL
  REDIS_URL
  JWT_SECRET
  CORS_ORIGINS
  RESEND_API_KEY
  EMAIL_FROM
  EMAIL_TO
  SENTRY_DSN
)

missing=()
for key in "${required[@]}"; do
  if [[ -z "${!key:-}" ]]; then
    missing+=("$key")
  elif [[ "${!key}" == *"<"* || "${!key}" == *">"* ]]; then
    missing+=("$key has placeholder value")
  fi
done

if (( ${#missing[@]} > 0 )); then
  printf 'Missing required Railway env vars:\n' >&2
  printf ' - %s\n' "${missing[@]}" >&2
  exit 1
fi

case "$DATABASE_URL" in
  postgresql+psycopg://*) ;;
  *) echo "DATABASE_URL must use postgresql+psycopg:// for this backend." >&2; exit 1 ;;
esac

case "$DIRECT_URL" in
  postgresql+psycopg://*) ;;
  *) echo "DIRECT_URL must use postgresql+psycopg:// for Alembic migrations." >&2; exit 1 ;;
esac

case "$REDIS_URL" in
  redis://*|rediss://*) ;;
  *) echo "REDIS_URL must start with redis:// or rediss://." >&2; exit 1 ;;
esac

echo "Railway environment shape looks valid."
