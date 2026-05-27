#!/usr/bin/env bash
set -euo pipefail

: "${BACKEND_URL:?Set BACKEND_URL, e.g. https://finalplanner-backend.up.railway.app}"
: "${FRONTEND_URL:?Set FRONTEND_URL, e.g. https://finalplanner.vercel.app}"

BACKEND_URL="${BACKEND_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"
SMOKE_RETRIES="${SMOKE_RETRIES:-5}"
SMOKE_RETRY_DELAY_SECONDS="${SMOKE_RETRY_DELAY_SECONDS:-3}"
SMOKE_CONNECT_TIMEOUT_SECONDS="${SMOKE_CONNECT_TIMEOUT_SECONDS:-10}"
SMOKE_MAX_TIME_SECONDS="${SMOKE_MAX_TIME_SECONDS:-30}"
CHECK_CORS="${CHECK_CORS:-1}"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl_retry() {
  curl \
    --fail \
    --show-error \
    --silent \
    --location \
    --retry "$SMOKE_RETRIES" \
    --retry-all-errors \
    --retry-delay "$SMOKE_RETRY_DELAY_SECONDS" \
    --connect-timeout "$SMOKE_CONNECT_TIMEOUT_SECONDS" \
    --max-time "$SMOKE_MAX_TIME_SECONDS" \
    "$@"
}

assert_contains() {
  local file="$1"
  local pattern="$2"
  local message="$3"

  if ! grep -Eq "$pattern" "$file"; then
    echo "Smoke check failed: $message" >&2
    echo "Response excerpt:" >&2
    sed -n '1,40p' "$file" >&2
    exit 1
  fi
}

assert_header_contains() {
  local file="$1"
  local pattern="$2"
  local message="$3"

  if ! grep -Eiq "$pattern" "$file"; then
    echo "Smoke check failed: $message" >&2
    echo "Response headers:" >&2
    sed -n '1,80p' "$file" >&2
    exit 1
  fi
}

echo "Checking backend health..."
backend_health="$tmp_dir/backend-health.json"
curl_retry "$BACKEND_URL/health" > "$backend_health"
assert_contains "$backend_health" '"status"[[:space:]]*:[[:space:]]*"ok"' "backend /health did not return status ok"

echo "Checking frontend HTML..."
frontend_headers="$tmp_dir/frontend.headers"
frontend_html="$tmp_dir/frontend.html"
curl_retry --dump-header "$frontend_headers" --output "$frontend_html" "$FRONTEND_URL/"
assert_header_contains "$frontend_headers" '^content-type:[[:space:]]*text/html' "frontend root did not return HTML"
assert_contains "$frontend_html" '(__next|FinalPlanner|<html)' "frontend root did not look like a rendered Next.js page"

echo "Checking PWA manifest..."
manifest="$tmp_dir/manifest.json"
curl_retry "$FRONTEND_URL/manifest.json" > "$manifest"
assert_contains "$manifest" '"name"[[:space:]]*:[[:space:]]*"FinalPlanner' "manifest is missing the FinalPlanner app name"
assert_contains "$manifest" '"start_url"[[:space:]]*:[[:space:]]*"/dashboard"' "manifest start_url is not /dashboard"

echo "Checking PWA icon..."
icon_headers="$tmp_dir/icon.headers"
curl_retry --dump-header "$icon_headers" --output /dev/null "$FRONTEND_URL/icon.svg"
assert_header_contains "$icon_headers" '^content-type:[[:space:]]*(image/svg\+xml|text/xml|application/octet-stream)' "PWA icon is not reachable"

if [[ "$CHECK_CORS" == "1" ]]; then
  echo "Checking backend CORS for frontend origin..."
  cors_headers="$tmp_dir/cors.headers"
  curl_retry \
    --request OPTIONS \
    --dump-header "$cors_headers" \
    --output /dev/null \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: authorization,content-type" \
    "$BACKEND_URL/dashboard"
  assert_header_contains "$cors_headers" "^access-control-allow-origin:[[:space:]]*$FRONTEND_URL" "backend CORS does not allow $FRONTEND_URL"
fi

echo "Production smoke checks passed."
