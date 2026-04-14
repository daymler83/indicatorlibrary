#!/usr/bin/env sh
set -eu

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
ROOT_PATH="${ROOT_PATH:-/indicator-library}"

exec uvicorn main:app \
  --host "${HOST}" \
  --port "${PORT}" \
  --root-path "${ROOT_PATH}" \
  --proxy-headers
