#!/usr/bin/env bash
set -euo pipefail

: "${BACKEND_URL:?Set BACKEND_URL}"
: "${AUTH_TOKEN:?Set AUTH_TOKEN to a JWT from /auth/login}"

BACKEND_URL="${BACKEND_URL%/}"

echo "Triggering daily alert endpoint..."
curl -fsS \
  -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  "$BACKEND_URL/email/daily-alert"
echo

echo "Triggering weekly summary endpoint..."
curl -fsS \
  -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  "$BACKEND_URL/email/weekly-summary"
echo

echo "Email alert endpoints responded. Confirm delivery in Resend logs and inbox."

