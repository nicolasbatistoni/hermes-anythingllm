#!/usr/bin/env bash
# install.sh — Hermes ↔ AnythingLLM integration installer (Linux / macOS)
#
# What this does:
#   1. Copies the MCP server to ~/.hermes/mcp_servers/
#   2. Copies the sync script to ~/.hermes/scripts/
#   3. Registers the MCP server in ~/.hermes/config.yaml
#   4. Appends the AnythingLLM fallback rule to ~/.hermes/SOUL.md
#   5. Sets up a cron job to sync sessions every 30 minutes
#
# Requirements:
#   - Hermes Agent installed at ~/.hermes
#   - AnythingLLM Desktop installed and running at least once
#   - ANYTHINGLLM_API_KEY exported (or prompted below)
#
# Usage:
#   chmod +x install.sh && ./install.sh

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Locate Hermes ─────────────────────────────────────────────────────────────
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
[[ -d "$HERMES_HOME" ]] || fail "Hermes not found at $HERMES_HOME. Set HERMES_HOME or install Hermes first."
ok "Hermes found at $HERMES_HOME"

# ── Locate Hermes venv Python ─────────────────────────────────────────────────
VENV_PYTHON=""
for candidate in \
    "$HERMES_HOME/hermes-agent/venv/bin/python3" \
    "$HERMES_HOME/venv/bin/python3" \
    "$HERMES_HOME/.venv/bin/python3"
do
    if [[ -x "$candidate" ]]; then
        VENV_PYTHON="$candidate"
        break
    fi
done

if [[ -z "$VENV_PYTHON" ]]; then
    warn "Could not auto-detect Hermes venv Python."
    read -rp "Enter full path to Hermes venv python3: " VENV_PYTHON
    [[ -x "$VENV_PYTHON" ]] || fail "Not executable: $VENV_PYTHON"
fi
ok "Python: $VENV_PYTHON"

# Verify mcp package is available
"$VENV_PYTHON" -c "import mcp" 2>/dev/null || \
    fail "mcp package not found in $VENV_PYTHON. Run: $VENV_PYTHON -m pip install mcp"

# ── API key ───────────────────────────────────────────────────────────────────
ANYTHINGLLM_API_KEY="${ANYTHINGLLM_API_KEY:-}"
if [[ -z "$ANYTHINGLLM_API_KEY" ]]; then
    echo ""
    echo "AnythingLLM API key required."
    echo "Find it in AnythingLLM Desktop → Settings → Tools → API key"
    read -rsp "API key: " ANYTHINGLLM_API_KEY
    echo ""
fi
[[ -n "$ANYTHINGLLM_API_KEY" ]] || fail "API key is required."
ok "API key set"

# ── Create directories ────────────────────────────────────────────────────────
mkdir -p "$HERMES_HOME/mcp_servers" "$HERMES_HOME/scripts" "$HERMES_HOME/logs"

# ── Copy MCP server ───────────────────────────────────────────────────────────
MCP_DEST="$HERMES_HOME/mcp_servers/anythingllm-server.py"
cp "$SCRIPT_DIR/mcp/anythingllm-server.py" "$MCP_DEST"
sed -i "1s|.*|#!${VENV_PYTHON}|" "$MCP_DEST"
chmod +x "$MCP_DEST"
ok "MCP server installed → $MCP_DEST"

# ── Copy sync script ──────────────────────────────────────────────────────────
SYNC_DEST="$HERMES_HOME/scripts/sync_sessions_to_anythingllm.py"
cp "$SCRIPT_DIR/scripts/sync_sessions_to_anythingllm.py" "$SYNC_DEST"
sed -i "1s|.*|#!${VENV_PYTHON}|" "$SYNC_DEST"
chmod +x "$SYNC_DEST"
ok "Sync script installed → $SYNC_DEST"

# ── Patch config.yaml ─────────────────────────────────────────────────────────
CONFIG="$HERMES_HOME/config.yaml"
if [[ ! -f "$CONFIG" ]]; then
    warn "config.yaml not found at $CONFIG — skipping MCP registration."
    warn "Add the following manually to $CONFIG:"
    echo ""
    cat "$SCRIPT_DIR/config/mcp_config_snippet.yaml"
    echo ""
else
    if grep -q "anythingllm-data" "$CONFIG"; then
        warn "anythingllm-data already present in config.yaml — updating command path."
        # Update just the command line
        sed -i "/anythingllm-data/,/env:/ s|command:.*|command: ${VENV_PYTHON}|" "$CONFIG"
        # Ensure enabled: true
        sed -i "/anythingllm-data/{n; s/enabled:.*/enabled: true/}" "$CONFIG"
    else
        # Append under mcp_servers section if it exists, else append at end
        if grep -q "^mcp_servers:" "$CONFIG"; then
            python3 - "$CONFIG" "$VENV_PYTHON" "$HERMES_HOME" <<'PYEOF'
import sys, re
config_path, venv_python, hermes_home = sys.argv[1], sys.argv[2], sys.argv[3]
mcp_block = f"""  anythingllm-data:
    enabled: true
    command: {venv_python}
    args:
      - {hermes_home}/mcp_servers/anythingllm-server.py
    env: {{}}
"""
text = open(config_path).read()
# Insert after mcp_servers: line
text = re.sub(r'(^mcp_servers:\s*\n)', r'\1' + mcp_block, text, flags=re.MULTILINE)
open(config_path, 'w').write(text)
PYEOF
        else
            cat >> "$CONFIG" <<YAML

mcp_servers:
  anythingllm-data:
    enabled: true
    command: ${VENV_PYTHON}
    args:
      - ${HERMES_HOME}/mcp_servers/anythingllm-server.py
    env: {}
YAML
        fi
    fi
    ok "config.yaml updated"
fi

# ── Patch SOUL.md ─────────────────────────────────────────────────────────────
SOUL="$HERMES_HOME/SOUL.md"
RULE_MARKER="AnythingLLM fallback"

if [[ -f "$SOUL" ]] && grep -q "$RULE_MARKER" "$SOUL"; then
    warn "SOUL.md already contains AnythingLLM fallback rule — skipping."
else
    SOUL_SNIPPET=$(cat <<'SOULEOF'

**MANDATORY RULE — AnythingLLM fallback:**
When the user asks about personal information (dates, preferences, opinions, past conversations, projects, facts about themselves) and you do NOT find the answer in your built-in memory (USER.md / MEMORY.md), you MUST search AnythingLLM BEFORE responding. Never reply "I don't have that information" without first calling:
1. `search_anythingllm_chats` — to search past conversations
2. `search_anythingllm_documents` — to search stored documents

Only say you don't know after both searches return no relevant results.
SOULEOF
)
    echo "$SOUL_SNIPPET" >> "$SOUL"
    ok "SOUL.md updated with AnythingLLM fallback rule"
fi

# ── Write .env for sync script ────────────────────────────────────────────────
ENV_FILE="$HERMES_HOME/.env"
if [[ -f "$ENV_FILE" ]] && grep -q "ANYTHINGLLM_API_KEY" "$ENV_FILE"; then
    warn ".env already has ANYTHINGLLM_API_KEY — not overwriting."
else
    cat >> "$ENV_FILE" <<ENVEOF

# AnythingLLM integration
ANYTHINGLLM_URL=http://localhost:3001
ANYTHINGLLM_API_KEY=${ANYTHINGLLM_API_KEY}
# ANYTHINGLLM_WORKSPACE=my-workspace  # optional: auto-detected if blank
ENVEOF
    chmod 600 "$ENV_FILE"
    ok ".env updated with AnythingLLM credentials"
fi

# ── Cron job ──────────────────────────────────────────────────────────────────
CRON_CMD="ANYTHINGLLM_API_KEY=${ANYTHINGLLM_API_KEY} HERMES_HOME=${HERMES_HOME} ${VENV_PYTHON} ${SYNC_DEST} >> ${HERMES_HOME}/logs/sync.log 2>&1"
CRON_LINE="*/30 * * * * ${CRON_CMD}"

if crontab -l 2>/dev/null | grep -q "sync_sessions_to_anythingllm"; then
    warn "Cron job already exists — not adding a duplicate."
else
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    ok "Cron job added (runs every 30 minutes)"
fi

# ── Initial sync ──────────────────────────────────────────────────────────────
echo ""
echo "Running initial session sync..."
ANYTHINGLLM_API_KEY="$ANYTHINGLLM_API_KEY" \
HERMES_HOME="$HERMES_HOME" \
"$VENV_PYTHON" "$SYNC_DEST" || warn "Initial sync failed (AnythingLLM may not be running). Re-run manually later."

echo ""
ok "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Restart Hermes Agent (or run: hermes mcp reload)"
echo "  2. Run 'hermes mcp list' to verify anythingllm-data is active"
echo "  3. Ask Hermes something it would only know from past conversations"
echo ""
echo "Manual sync: ANYTHINGLLM_API_KEY=... $VENV_PYTHON $SYNC_DEST"
echo "Re-sync all: ANYTHINGLLM_API_KEY=... $VENV_PYTHON $SYNC_DEST --all"
