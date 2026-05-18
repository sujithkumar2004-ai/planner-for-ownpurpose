#!/usr/bin/env bash
set -euo pipefail

: "${BACKEND_URL:?Set BACKEND_URL}"
: "${AUTH_TOKEN:?Set AUTH_TOKEN to a JWT from /auth/login}"

BACKEND_URL="${BACKEND_URL%/}"

endpoints=(
  /dashboard
  /daily-plan
  /monk-mode/daily-score
  /monk-mode/recovery-plan
  /weekly-review
  /warnings
  /notifications
  /analytics
)

for endpoint in "${endpoints[@]}"; do
  echo "Checking $endpoint"
  curl -fsS \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    "$BACKEND_URL$endpoint" >/dev/null
done

echo "Authenticated API checks passed."

