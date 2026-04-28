#!/usr/bin/env python3
"""
AnythingLLM MCP Server for Hermes Agent
Connects Hermes to the local AnythingLLM database (SQLite).
Exposes 8 tools for querying documents and chat history.

Compatible with: Linux, macOS, Windows
Requires: mcp package (installed in Hermes venv)
"""

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP


def find_db() -> str:
    """Locate the AnythingLLM SQLite database across platforms."""
    candidates = []

    # Linux / macOS — XDG or AppData
    if sys.platform != "win32":
        candidates += [
            Path.home() / ".config" / "anythingllm-desktop" / "storage" / "anythingllm.db",
            Path.home() / "Library" / "Application Support" / "anythingllm-desktop" / "storage" / "anythingllm.db",
        ]
    else:
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        candidates += [
            Path(appdata) / "anythingllm-desktop" / "storage" / "anythingllm.db",
            Path(localappdata) / "anythingllm-desktop" / "storage" / "anythingllm.db",
        ]

    # Explicit override via env var
    env_path = os.environ.get("ANYTHINGLLM_DB_PATH")
    if env_path:
        return env_path

    for p in candidates:
        if p.exists():
            return str(p)

    raise FileNotFoundError(
        "AnythingLLM database not found. Set ANYTHINGLLM_DB_PATH env var to its location."
    )


DB_PATH = find_db()
mcp = FastMCP("AnythingLLM")

STOPWORDS = {
    "me", "te", "se", "le", "la", "lo", "el", "un", "una", "los", "las",
    "de", "en", "que", "por", "con", "para", "del", "al", "es", "son",
    "fue", "hay", "si", "no", "mi", "tu", "su", "yo", "the", "and", "or",
    "a", "e", "i", "o", "u",
}


def _build_search_terms(query: str) -> list[str]:
    """
    Split query into individual search terms with basic Spanish stemming.
    Words ≥ 6 chars are reduced to their first 5 chars so that e.g.
    'peliculas' (prefix 'pelic') matches 'pelis', 'película', etc.
    """
    raw = re.split(r"[,;:\s]+", query.lower())
    raw = [w.strip() for w in raw if len(w.strip()) >= 3 and w.strip() not in STOPWORDS]
    seen: set[str] = set()
    terms: list[str] = []
    for w in raw:
        key = w[:5] if len(w) >= 6 else w
        if key not in seen:
            seen.add(key)
            terms.append(key)
    return terms or [query.lower()[:20]]


def _parse_response(raw: str) -> str:
    """Extract plain text from AnythingLLM JSON response blob."""
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            return d.get("text", raw)
    except Exception:
        pass
    return raw


@mcp.tool()
def get_anythingllm_documents():
    """
    List documents stored in AnythingLLM with their titles, paths and workspace.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT d.id, d.docId, d.filename, d.docpath, d.metadata, d.createdAt,
                   w.name AS workspace_name
            FROM workspace_documents d
            LEFT JOIN workspaces w ON d.workspaceId = w.id
            ORDER BY d.createdAt DESC LIMIT 50
        """)
        docs = []
        for row in c.fetchall():
            meta = {}
            try:
                meta = json.loads(row[4]) if row[4] else {}
            except Exception:
                pass
            docs.append({
                "id": str(row[0]), "docId": row[1] or "",
                "filename": row[2] or "", "docpath": row[3] or "",
                "created_at": row[5] or "", "workspace": row[6] or "",
                "title": meta.get("title", row[2] or ""),
            })
        conn.close()
        return {"success": True, "count": len(docs), "documents": docs}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_anythingllm_documents(query: str):
    """
    Search AnythingLLM documents by filename, path or metadata.
    Parameters:
        query: search terms (comma/space separated, basic Spanish stemming applied)
    """
    try:
        terms = _build_search_terms(query)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        cond = " OR ".join(
            ["(LOWER(d.filename) LIKE ? OR LOWER(d.docpath) LIKE ? OR LOWER(d.metadata) LIKE ?)"]
            * len(terms)
        )
        params = [p for t in terms for p in [f"%{t}%", f"%{t}%", f"%{t}%"]]
        c.execute(f"""
            SELECT d.id, d.docId, d.filename, d.docpath, d.metadata, d.createdAt,
                   w.name AS workspace_name
            FROM workspace_documents d
            LEFT JOIN workspaces w ON d.workspaceId = w.id
            WHERE {cond}
            ORDER BY d.createdAt DESC LIMIT 30
        """, params)
        docs = []
        for row in c.fetchall():
            meta = {}
            try:
                meta = json.loads(row[4]) if row[4] else {}
            except Exception:
                pass
            docs.append({
                "id": str(row[0]), "docId": row[1] or "",
                "filename": row[2] or "", "docpath": row[3] or "",
                "created_at": row[5] or "", "workspace": row[6] or "",
                "title": meta.get("title", row[2] or ""),
                "description": meta.get("description", ""),
            })
        conn.close()
        return {"success": True, "query": query, "terms_searched": terms,
                "count": len(docs), "documents": docs}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def search_anythingllm_chats(query: str, limit: int = 20):
    """
    Search AnythingLLM chat history by content.
    Use this to recover facts or preferences the user mentioned in past conversations.
    Parameters:
        query: search terms — comma/space separated. Each term searched independently.
               Basic Spanish stemming: 'peliculas' matches 'pelis', 'película', etc.
        limit: max results (default 20)
    """
    try:
        terms = _build_search_terms(query)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        cond = " OR ".join(
            ["(LOWER(wc.prompt) LIKE ? OR LOWER(wc.response) LIKE ?)"] * len(terms)
        )
        params = [p for t in terms for p in [f"%{t}%", f"%{t}%"]] + [limit]
        c.execute(f"""
            SELECT wc.id, wc.prompt, wc.response, wc.createdAt, w.name AS workspace_name
            FROM workspace_chats wc
            LEFT JOIN workspaces w ON wc.workspaceId = w.id
            WHERE {cond}
            ORDER BY wc.createdAt DESC LIMIT ?
        """, params)
        chats = []
        for row in c.fetchall():
            chats.append({
                "id": str(row[0]),
                "prompt": row[1] or "",
                "response": _parse_response(row[2] or "")[:500],
                "date": row[3] or "",
                "workspace": row[4] or "",
            })
        conn.close()
        return {"success": True, "query": query, "terms_searched": terms,
                "count": len(chats), "chats": chats}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_anythingllm_chats(workspace_id: str = None):
    """
    Get workspaces and their recent chats.
    Parameters:
        workspace_id: workspace ID to filter (optional, returns all if omitted)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if workspace_id:
            c.execute("SELECT id, name, slug, createdAt, lastUpdatedAt FROM workspaces WHERE id=?",
                      (workspace_id,))
        else:
            c.execute("SELECT id, name, slug, createdAt, lastUpdatedAt FROM workspaces LIMIT 10")
        workspaces = []
        for row in c.fetchall():
            c2 = conn.cursor()
            c2.execute("""SELECT prompt, response, createdAt FROM workspace_chats
                          WHERE workspaceId=? ORDER BY createdAt DESC LIMIT 3""", (row[0],))
            chats = [{"prompt": r[0], "response": _parse_response(r[1] or "")[:200], "date": r[2]}
                     for r in c2.fetchall()]
            workspaces.append({
                "id": str(row[0]), "name": row[1] or "", "slug": row[2] or "",
                "created_at": str(row[3]) if row[3] else "",
                "last_updated": str(row[4]) if row[4] else "",
                "recent_chats": chats,
            })
        conn.close()
        return {"success": True, "count": len(workspaces), "workspaces": workspaces}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_system_settings():
    """Get AnythingLLM system stats: document count, workspaces, chats, embed configs."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM workspace_documents"); docs = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM workspaces");          ws   = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM workspace_chats");     chat = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM embed_configs WHERE enabled=1"); emb = c.fetchone()[0]
        c.execute("SELECT label, value FROM system_settings LIMIT 20")
        settings = {r[0]: r[1] for r in c.fetchall()}
        conn.close()
        return {"success": True,
                "stats": {"documents": docs, "workspaces": ws, "chats": chat,
                           "active_embed_configs": emb},
                "system_settings": settings}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_event_logs(limit: int = 10):
    """
    Get recent AnythingLLM event logs.
    Parameters:
        limit: max events to return (default 10)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, event, metadata, occurredAt FROM event_logs ORDER BY occurredAt DESC LIMIT ?",
                  (limit,))
        events = [{"id": str(r[0]), "event": r[1] or "", "metadata": r[2] or "",
                   "occurred_at": r[3] or ""} for r in c.fetchall()]
        conn.close()
        return {"success": True, "count": len(events), "events": events}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_document_content(document_id: str):
    """
    Get full metadata of a specific document.
    Parameters:
        document_id: numeric document ID
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT d.id, d.docId, d.filename, d.docpath, d.metadata,
                   d.createdAt, d.lastUpdatedAt, d.pinned, w.name
            FROM workspace_documents d
            LEFT JOIN workspaces w ON d.workspaceId = w.id
            WHERE d.id=?
        """, (document_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {"success": False, "error": f"Document {document_id} not found."}
        meta = {}
        try:
            meta = json.loads(row[4]) if row[4] else {}
        except Exception:
            pass
        return {"success": True, "document": {
            "id": str(row[0]), "docId": row[1] or "", "filename": row[2] or "",
            "docpath": row[3] or "", "metadata": meta, "created_at": row[5] or "",
            "last_updated": row[6] or "", "pinned": bool(row[7]), "workspace": row[8] or "",
        }}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_workspace_documents(workspace_id: str = None):
    """
    Get documents from a specific workspace.
    Parameters:
        workspace_id: workspace ID (optional, returns all if omitted)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if workspace_id:
            c.execute("""
                SELECT d.id, d.docId, d.filename, d.docpath, d.metadata, d.createdAt, w.name
                FROM workspace_documents d LEFT JOIN workspaces w ON d.workspaceId=w.id
                WHERE d.workspaceId=? ORDER BY d.createdAt DESC LIMIT 20
            """, (workspace_id,))
        else:
            c.execute("""
                SELECT d.id, d.docId, d.filename, d.docpath, d.metadata, d.createdAt, w.name
                FROM workspace_documents d LEFT JOIN workspaces w ON d.workspaceId=w.id
                ORDER BY d.createdAt DESC LIMIT 20
            """)
        docs = []
        for row in c.fetchall():
            meta = {}
            try:
                meta = json.loads(row[4]) if row[4] else {}
            except Exception:
                pass
            docs.append({
                "id": str(row[0]), "docId": row[1] or "", "filename": row[2] or "",
                "docpath": row[3] or "", "created_at": row[5] or "", "workspace": row[6] or "",
                "title": meta.get("title", row[2] or ""),
            })
        conn.close()
        return {"success": True, "count": len(docs), "documents": docs}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()
