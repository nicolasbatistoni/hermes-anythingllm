# hermes-anythingllm

Connects [Hermes Agent](https://github.com/niklasvincent/hermes-agent) to [AnythingLLM Desktop](https://anythingllm.com/) so that Hermes can search its entire history — past conversations and uploaded documents — via semantic search.

## What it does

- **MCP server** (`mcp/anythingllm-server.py`): Exposes 8 tools Hermes can call to query AnythingLLM's SQLite database — list/search documents, search chat history, get workspace info, get event logs.
- **Session sync** (`scripts/sync_sessions_to_anythingllm.py`): Uploads every Hermes session as a plain-text document to AnythingLLM, where it gets vectorized and becomes searchable by meaning — not just keyword.
- **SOUL.md rule**: Instructs Hermes to always search AnythingLLM before answering questions about personal information, preferences, or past conversations.

### Memory architecture

```
Hermes session start
    └── Loads USER.md + MEMORY.md (snapshot, frozen for session)
    └── Loads SOUL.md (re-read each message — live rules)
              └── Rule: search AnythingLLM before saying "I don't know"
                        └── search_anythingllm_chats (keyword + stemming)
                        └── search_anythingllm_documents (metadata search)
                        └── AnythingLLM vector search (via chat interface)

Every 30 min (cron / Scheduled Task)
    └── sync_sessions_to_anythingllm.py
              └── Uploads new sessions as documents
              └── Embeds them in workspace (vectorized via lancedb)
```

## Requirements

- **Hermes Agent** ≥ 0.11 installed at `~/.hermes` (Linux/macOS) or `%USERPROFILE%\.hermes` (Windows)
- **AnythingLLM Desktop** installed and configured with at least one workspace
- An AnythingLLM API key (Settings → Tools → API)
- `mcp` Python package installed in the Hermes venv

## Installation

### Linux / macOS

```bash
git clone https://github.com/nicolasbatistoni/hermes-anythingllm
cd hermes-anythingllm
chmod +x install.sh

# Option A — pass API key as env var
export ANYTHINGLLM_API_KEY=your-key-here
./install.sh

# Option B — installer will prompt for it
./install.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/nicolasbatistoni/hermes-anythingllm
cd hermes-anythingllm

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Option A — pass API key as parameter
.\install.ps1 -ApiKey "your-key-here"

# Option B — installer will prompt for it
.\install.ps1
```

### What the installer does

1. Copies `mcp/anythingllm-server.py` → `~/.hermes/mcp_servers/`
2. Copies `scripts/sync_sessions_to_anythingllm.py` → `~/.hermes/scripts/`
3. Registers the MCP server in `~/.hermes/config.yaml`
4. Appends the AnythingLLM fallback rule to `~/.hermes/SOUL.md`
5. Writes credentials to `~/.hermes/.env`
6. Creates a cron job / Scheduled Task (every 30 min)
7. Runs an initial session sync

## Manual setup (without the installer)

### 1. Install the MCP server

```bash
cp mcp/anythingllm-server.py ~/.hermes/mcp_servers/
```

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  anythingllm-data:
    enabled: true
    command: /path/to/.hermes/hermes-agent/venv/bin/python3
    args:
      - /path/to/.hermes/mcp_servers/anythingllm-server.py
    env: {}
```

### 2. Add SOUL.md rule

Append to `~/.hermes/SOUL.md`:

```markdown
**MANDATORY RULE — AnythingLLM fallback:**
When the user asks about personal information (dates, preferences, opinions, past conversations, projects, facts about themselves) and you do NOT find the answer in your built-in memory (USER.md / MEMORY.md), you MUST search AnythingLLM BEFORE responding. Never reply "I don't have that information" without first calling:
1. `search_anythingllm_chats` — to search past conversations
2. `search_anythingllm_documents` — to search stored documents

Only say you don't know after both searches return no relevant results.
```

### 3. Sync sessions

```bash
export ANYTHINGLLM_API_KEY=your-key-here
python3 scripts/sync_sessions_to_anythingllm.py

# Re-sync everything (e.g. after changing format)
python3 scripts/sync_sessions_to_anythingllm.py --all

# Preview without uploading
python3 scripts/sync_sessions_to_anythingllm.py --dry-run
```

### 4. Add cron (Linux/macOS)

```
*/30 * * * * ANYTHINGLLM_API_KEY=your-key HERMES_HOME=~/.hermes /path/to/venv/python3 ~/.hermes/scripts/sync_sessions_to_anythingllm.py >> ~/.hermes/logs/sync.log 2>&1
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANYTHINGLLM_URL` | `http://localhost:3001` | AnythingLLM server URL |
| `ANYTHINGLLM_API_KEY` | _(required)_ | AnythingLLM API key |
| `ANYTHINGLLM_WORKSPACE` | _(auto-detected)_ | Workspace slug to embed sessions into |
| `ANYTHINGLLM_DB_PATH` | _(auto-detected)_ | Path to AnythingLLM SQLite DB |
| `HERMES_HOME` | `~/.hermes` | Hermes home directory |

## MCP tools

The MCP server exposes these tools to Hermes:

| Tool | Description |
|---|---|
| `get_anythingllm_documents` | List all documents (most recent 50) |
| `search_anythingllm_documents` | Search documents by filename/path/metadata |
| `search_anythingllm_chats` | Search chat history by content (with Spanish stemming) |
| `get_anythingllm_chats` | Get workspaces and their recent chats |
| `get_document_content` | Get full metadata for a specific document |
| `get_workspace_documents` | Get documents from a specific workspace |
| `get_system_settings` | Get system stats (document/workspace/chat counts) |
| `get_event_logs` | Get recent AnythingLLM event logs |

## How session sync works

1. Hermes sessions are stored as JSON files in `~/.hermes/sessions/session_*.json`
2. Each session is converted to readable markdown (user/assistant turns only — system prompts and tool results are stripped)
3. Uploaded to AnythingLLM via `POST /api/v1/document/raw-text`
4. Embedded in the workspace via `POST /api/v1/workspace/{slug}/update-embeddings`
5. AnythingLLM vectorizes the text with lancedb — enabling true semantic search

Sessions with fewer than 2 messages are skipped. Already-synced sessions are tracked in `~/.hermes/scripts/.sync_state.json`.

## Database location

AnythingLLM Desktop stores its SQLite database at:

- **Linux**: `~/.config/anythingllm-desktop/storage/anythingllm.db`
- **macOS**: `~/Library/Application Support/anythingllm-desktop/storage/anythingllm.db`
- **Windows**: `%APPDATA%\anythingllm-desktop\storage\anythingllm.db`

Override with `ANYTHINGLLM_DB_PATH` if your installation differs.

## License

MIT
