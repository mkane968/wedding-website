#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Running Django system check..."
uv run python manage.py check

echo "Bundling front-end assets..."
npm run build:avatars
npm run build:chapel

echo "Starting Django development server..."
uv run python manage.py runserver --noreload > /tmp/chapel-ci.log 2>&1 &
SERVER_PID=$!
sleep 4

cleanup() {
    echo "Stopping Django server..."
    kill $SERVER_PID >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "Running Playwright regression suite..."
npm run test:playwright

echo "Running Cypress regression suite..."
npm run test:cypress
