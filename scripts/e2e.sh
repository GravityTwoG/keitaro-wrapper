#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Run e2e in an isolated compose project with its own ports and volume, so a
# developer's demo stack and data are never touched.
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-keitaro-wrapper-e2e}"
export FRONTEND_PORT="${E2E_FRONTEND_PORT:-18080}"
export BACKEND_PORT="${E2E_BACKEND_PORT:-18000}"
export MOCK_KEITARO_PORT="${E2E_MOCK_PORT:-18001}"
export POSTGRES_PORT="${E2E_POSTGRES_PORT:-15433}"
export E2E_BASE_URL="${E2E_BASE_URL:-http://127.0.0.1:${FRONTEND_PORT}}"

# docker-compose.e2e.yml hardcodes the mock and is merged over the base file,
# so values from a local .env can never point tests at a real tracker.

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.e2e.yml)

cleanup() {
  "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

"${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
"${COMPOSE[@]}" up -d --build --wait

npm --prefix e2e test -- "$@"
