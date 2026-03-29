#!/usr/bin/env bash
set -euo pipefail

# Required env vars — set these before running
: "${HCLOUD_TOKEN:?}"


# Optional
SERVER_NAME="${SERVER_NAME:-traccar}"
SERVER_TYPE="${SERVER_TYPE:-cx22}"
LOCATION="${LOCATION:-nbg1}"
SSH_KEY="${SSH_KEY:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Inject credentials into cloud-init
USER_DATA=$("${SCRIPT_DIR}/cloud-init.yml")

# Build hcloud command
HCLOUD_ARGS=(
  server create
  --name "$SERVER_NAME"
  --type "$SERVER_TYPE"
  --image "docker-ce"
  --location "$LOCATION"
  --user-data-from-file <(echo "$USER_DATA")
)

if [[ -n "$SSH_KEY" ]]; then
  HCLOUD_ARGS+=(--ssh-key "$SSH_KEY")
fi

hcloud "${HCLOUD_ARGS[@]}"

echo ""
echo "Server '$SERVER_NAME' created. Traccar will be up in ~1-2 minutes."
echo "Point your Cloudflare DNS A record to the server IP shown above (port 8082)."
