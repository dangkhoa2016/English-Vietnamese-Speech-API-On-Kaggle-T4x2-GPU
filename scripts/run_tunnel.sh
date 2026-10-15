#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENABLE_CLOUDFLARE_TUNNEL="${ENABLE_CLOUDFLARE_TUNNEL:-false}"
API_AUTH_REQUIRED="${API_AUTH_REQUIRED:-false}"

is_true() {
  case "${1,,}" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

if ! is_true "$ENABLE_CLOUDFLARE_TUNNEL"; then
  echo "Cloudflare tunnel is disabled. Set ENABLE_CLOUDFLARE_TUNNEL=true to opt in." >&2
  exit 2
fi
if ! is_true "$API_AUTH_REQUIRED"; then
  echo "Refusing public tunnel while API_AUTH_REQUIRED is disabled." >&2
  exit 3
fi
if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed or not on PATH." >&2
  exit 4
fi

exec cloudflared tunnel --url http://127.0.0.1:8090
