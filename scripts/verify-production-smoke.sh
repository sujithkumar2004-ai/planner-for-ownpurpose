#!/usr/bin/env bash
set -euo pipefail

: "${BACKEND_URL:?Set BACKEND_URL, e.g. https://finalplanner-backend.up.railway.app}"
: "${FRONTEND_URL:?Set FRONTEND_URL, e.g. https://finalplanner.vercel.app}"

BACKEND_URL="${BACKEND_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"

echo "Checking backend health..."
curl -fsS "$BACKEND_URL/health"
echo

echo "Checking frontend HTML..."
curl -fsSI "$FRONTEND_URL" | grep -Ei 'HTTP/|content-type|cache-control' || true

echo "Checking PWA manifest..."
curl -fsS "$FRONTEND_URL/manifest.json" | grep -q '"name"'

echo "Production smoke checks passed."

