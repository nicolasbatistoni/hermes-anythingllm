#!/usr/bin/env python3
"""
Sync Hermes sessions to AnythingLLM as searchable RAG documents.

Each Hermes session is uploaded to AnythingLLM via its REST API, vectorized,
and made available for semantic search — giving Hermes persistent memory
that survives context resets.

Usage:
    python3 sync_sessions_to_anythingllm.py [--all] [--dry-run]

    --all      re-sync all sessions (ignores state file)
    --dry-run  show what would be synced without uploading

Configuration (via environment variables or auto-detected):
    ANYTHINGLLM_URL        AnythingLLM server URL  (default: http://localhost:3001)
    ANYTHINGLLM_API_KEY    AnythingLLM API key     (required)
    ANYTHINGLLM_WORKSPACE  Workspace slug          (default: auto-detected)
    HERMES_HOME            Hermes home directory   (default: ~/.hermes)

Compatible with: Linux, macOS, Windows
"""

import json
import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path


# ── Paths ────────────────────────────────────────────────────────────────────

def get_hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    return Path.home() / ".hermes"


HERMES_HOME  = get_hermes_home()
SESSIONS_DIR = HERMES_HOME / "sessions"
SCRIPTS_DIR  = HERMES_HOME / "scripts"
STATE_FILE   = SCRIPTS_DIR / ".sync_state.json"
LOG_DIR      = HERMES_HOME / "logs"

# ── AnythingLLM connection ────────────────────────────────────────────────────

ANYTHINGLLM_URL = os.environ.get("ANYTHINGLLM_URL", "http://localhost:3001")
ANYTHINGLLM_KEY = os.environ.get("ANYTHINGLLM_API_KEY", "")
WORKSPACE_SLUG  = os.environ.get("ANYTHINGLLM_WORKSPACE", "")

MIN_MESSAGES = 2   # skip accidental/empty sessions


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"synced": []}


def save_state(state: dict):
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def api_headers() -> dict:
    return {
        "Authorization": f"Bearer {ANYTHINGLLM_KEY}",
        "Content-Type": "application/json",
    }


def check_connection() -> bool:
    try:
        r = requests.get(f"{ANYTHINGLLM_URL}/api/v1/auth",
                         headers=api_headers(), timeout=5)
        return r.json().get("authenticated", False)
    except Exception:
        return False


def get_default_workspace() -> str:
    """Return the slug of the first available workspace."""
    try:
        r = requests.get(f"{ANYTHINGLLM_URL}/api/v1/workspaces",
                         headers=api_headers(), timeout=10)
        workspaces = r.json().get("workspaces", [])
        if workspaces:
            return workspaces[0]["slug"]
    except Exception:
        pass
    return ""


def session_to_text(session: dict) -> str:
    """Convert a Hermes session JSON into readable plain text."""
    session_id = session.get("session_id", "unknown")
    model      = session.get("model", "unknown")
    started    = session.get("session_start", "")
    messages   = session.get("messages", [])

    try:
        if isinstance(started, (int, float)):
            dt = datetime.fromtimestamp(started / 1000)
        else:
            dt = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        date_str = str(started)

    lines = [
        f"# Hermes Session — {date_str}",
        f"Session ID: {session_id}",
        f"Model: {model}",
        "",
    ]

    for msg in messages:
        role    = msg.get("role", "")
        content = msg.get("content", "")

        # content can be a list (multimodal) or a string
        if isinstance(content, list):
            parts = [b.get("text", "") for b in content
                     if isinstance(b, dict) and b.get("type") == "text"]
            content = "\n".join(parts)

        content = str(content).strip()
        if not content:
            continue
        if role in ("system", "tool"):
            continue

        prefix = "Usuario" if role == "user" else "Hermes"
        lines.append(f"**{prefix}:** {content}\n")

    return "\n".join(lines)


def upload_document(title: str, text: str) -> str | None:
    """Upload text to AnythingLLM. Returns document location path or None."""
    payload = {
        "textContent": text,
        "metadata": {
            "title": title,
            "docAuthor": "Hermes Agent",
            "description": f"Hermes Agent session: {title}",
        },
    }
    try:
        r = requests.post(f"{ANYTHINGLLM_URL}/api/v1/document/raw-text",
                          headers=api_headers(), json=payload, timeout=30)
        r.raise_for_status()
        docs = r.json().get("documents", [])
        return docs[0]["location"] if docs else None
    except Exception as e:
        print(f"  ✗ Upload failed: {e}")
        return None


def embed_in_workspace(location: str, workspace_slug: str) -> bool:
    """Add an uploaded document to the workspace for vector indexing."""
    try:
        r = requests.post(
            f"{ANYTHINGLLM_URL}/api/v1/workspace/{workspace_slug}/update-embeddings",
            headers=api_headers(),
            json={"adds": [location], "deletes": []},
            timeout=60,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"  ✗ Embed failed: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    dry_run  = "--dry-run" in sys.argv
    sync_all = "--all" in sys.argv

    # Validate API key
    if not ANYTHINGLLM_KEY:
        print("✗ ANYTHINGLLM_API_KEY not set.")
        print("  Set it in your environment or in ~/.hermes/.env:")
        print("  ANYTHINGLLM_API_KEY=your-key-here")
        sys.exit(1)

    if not check_connection():
        print(f"✗ AnythingLLM not reachable at {ANYTHINGLLM_URL}")
        print("  Start AnythingLLM Desktop and try again.")
        sys.exit(0)  # exit 0 so cron doesn't spam errors when app is closed

    workspace = WORKSPACE_SLUG or get_default_workspace()
    if not workspace:
        print("✗ No workspace found. Create one in AnythingLLM first.")
        sys.exit(1)

    print(f"✓ Connected to {ANYTHINGLLM_URL} | workspace: {workspace}")

    state         = load_state()
    already_synced = set(state.get("synced", []))
    session_files  = sorted(SESSIONS_DIR.glob("session_*.json"))
    pending        = [f for f in session_files
                      if sync_all or f.name not in already_synced]

    print(f"Sessions found: {len(session_files)} | Pending: {len(pending)}")
    if not pending:
        print("✓ All sessions already synced.")
        return

    synced_count = 0
    for path in pending:
        try:
            session = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ✗ Cannot read {path.name}: {e}")
            continue

        msg_count = session.get("message_count", 0)
        if msg_count < MIN_MESSAGES:
            already_synced.add(path.name)
            continue

        sid = session.get("session_id", path.stem)
        try:
            parts = sid.split("_")
            d, t  = parts[0], parts[1]
            title = f"Hermes Session {d[:4]}-{d[4:6]}-{d[6:]} {t[:2]}:{t[2:4]}"
        except Exception:
            title = f"Hermes Session {sid}"

        text = session_to_text(session)
        print(f"\n  → {title} ({msg_count} msgs, ~{len(text.split())} words)")

        if dry_run:
            print("     [dry-run] skipped")
            continue

        location = upload_document(title, text)
        if not location:
            continue
        print(f"     ✓ Uploaded → {location}")

        time.sleep(0.5)  # avoid overwhelming AnythingLLM on rapid syncs

        if embed_in_workspace(location, workspace):
            print("     ✓ Embedded in workspace")
            synced_count += 1
            already_synced.add(path.name)

    if not dry_run:
        state["synced"] = list(already_synced)
        save_state(state)
        print(f"\n✓ {synced_count} session(s) synced this run.")


if __name__ == "__main__":
    main()
