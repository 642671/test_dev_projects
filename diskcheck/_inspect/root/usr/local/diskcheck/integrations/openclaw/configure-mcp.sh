#!/bin/sh
set -eu
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PATH

if ! command -v openclaw >/dev/null 2>&1; then
  echo "OpenClaw is not installed or is not available in PATH." >&2
  exit 1
fi
if [ ! -x /usr/local/diskcheck/bin/diskcheck ]; then
  echo "DiskCheck is not installed." >&2
  exit 1
fi

# Registration is explicit and reversible. DiskCheck never edits OpenClaw's
# configuration file directly and exposes only the reviewed read-only tools.
openclaw mcp unset diskcheck >/dev/null 2>&1 || true
openclaw mcp add diskcheck \
  --command /usr/local/diskcheck/bin/diskcheck \
  --arg mcp \
  --arg=--helper \
  --arg unix:///run/diskcheck/helper.sock \
  --arg=--guardian-state \
  --arg /usr/local/diskcheck/depends/data/guardian.json \
  --include 'diskcheck_*' \
  --parallel
openclaw mcp reload >/dev/null 2>&1 || true
openclaw mcp probe diskcheck

# Enable OpenClaw's documented local webhook endpoint and store the matching
# token in DiskCheck's private data directory. The token is never printed.
# Re-running this script reuses DiskCheck's existing credential. If another
# integration already owns the global OpenClaw hook before DiskCheck has been
# configured, stop instead of silently replacing that integration's token.
gateway_port="$(openclaw config get gateway.port 2>/dev/null || printf '18789')"
agent_config_path=/usr/local/diskcheck/depends/data/agent-webhook.json
token=""
if [ -f "$agent_config_path" ]; then
  token="$(sed -n 's/.*"token":"\([^"]*\)".*/\1/p' "$agent_config_path" | head -n 1)"
fi
if [ -z "$token" ]; then
  if openclaw config get hooks.token >/dev/null 2>&1; then
    echo "OpenClaw already has a webhook token owned by another integration." >&2
    echo "Coordinate the shared hook credential before enabling DiskCheck notifications." >&2
    exit 1
  fi
  token="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
fi
openclaw config set hooks.enabled true --strict-json >/dev/null
openclaw config set hooks.path /hooks >/dev/null
openclaw config set hooks.token "$token" >/dev/null
openclaw config validate >/dev/null
openclaw gateway restart >/dev/null

agent_config="$(mktemp)"
trap 'rm -f -- "$agent_config"' EXIT
umask 077
printf '%s\n' "{\"enabled\":true,\"url\":\"http://127.0.0.1:${gateway_port}/hooks/wake\",\"token\":\"${token}\",\"notify_risk\":true,\"notify_all_results\":false}" > "$agent_config"
cp "$agent_config" "$agent_config_path"
chown diskcheck:diskcheck "$agent_config_path"
chmod 0600 "$agent_config_path"
systemctl restart diskcheck-api.service

# Exercise the exact secured webhook without disclosing its credential.
curl -fsS -H "Authorization: Bearer ${token}" -H 'Content-Type: application/json' \
  -d '{"text":"DiskCheck agent integration connected.","mode":"now"}' \
  "http://127.0.0.1:${gateway_port}/hooks/wake" >/dev/null
echo "DiskCheck MCP tools and local health-event notifications are connected to OpenClaw."
