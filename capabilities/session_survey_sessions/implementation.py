"""Core capability: survey and export Claude sessions across CLI, web Code, and chat."""
from __future__ import annotations

import glob
import json
import os
import time
from typing import Any, Dict, List, Optional


CLAUDE_DIR = os.path.expanduser("~/.claude")
PROJECTS_DIR = os.path.join(CLAUDE_DIR, "projects")
DEFAULT_EXPORT_DIR = os.path.join(CLAUDE_DIR, "exports")

# Headers required specifically for the /v1/sessions (Claude Code) API
_CODE_SESSION_HEADERS = {
    "anthropic-beta": "ccr-byoc-2025-07-29",
    "anthropic-client-feature": "ccr",
    "anthropic-client-platform": "web_claude_ai",
    "anthropic-version": "2023-06-01",
}


class SessionSurveyError(Exception):
    """Base error for session survey failures."""


class AuthRequiredError(SessionSurveyError):
    """Raised when web auth credentials are missing but needed."""


# ── Entry point ──────────────────────────────────────────────────────


def survey_sessions(
    sources: Optional[List[str]] = None,
    org_id: Optional[str] = None,
    cookie: Optional[str] = None,
    status_filter: Optional[str] = None,
    session_id: Optional[str] = None,
    export: bool = False,
    export_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Survey and optionally export Claude sessions.

    Returns a dict with 'sessions', 'summary', and optionally 'exported_files'.
    """
    if sources is None:
        sources = ["cli", "code", "chat"]

    org_id = org_id or os.environ.get("CLAUDE_ORG_ID")
    cookie = cookie or os.environ.get("CLAUDE_SESSION_COOKIE")
    export_dir = export_dir or DEFAULT_EXPORT_DIR
    has_web_auth = bool(org_id and cookie)

    all_sessions: List[Dict[str, Any]] = []
    warnings: List[str] = []

    if "cli" in sources:
        all_sessions.extend(_parse_cli_sessions())

    needs_web = "code" in sources or "chat" in sources
    if needs_web and not has_web_auth:
        skipped = [s for s in sources if s in ("code", "chat")]
        warnings.append(
            f"Skipped {', '.join(skipped)}: org_id and cookie required."
        )
    elif needs_web:
        if "code" in sources:
            web_sessions = _fetch_web_sessions(org_id, cookie)
            if status_filter:
                web_sessions = [s for s in web_sessions if s["status"] == status_filter]
            all_sessions.extend(web_sessions)
        if "chat" in sources:
            all_sessions.extend(_fetch_chat_sessions(org_id, cookie))

    if session_id:
        all_sessions = [s for s in all_sessions if session_id in s["session_id"]]

    summary = {
        "cli": len([s for s in all_sessions if s["source"] == "cli"]),
        "code": len([s for s in all_sessions if s["source"] == "web"]),
        "chat": len([s for s in all_sessions if s["source"] == "chat"]),
        "total": len(all_sessions),
    }

    result: Dict[str, Any] = {
        "sessions": all_sessions,
        "summary": summary,
        "exported_files": None,
    }
    if warnings:
        result["warnings"] = warnings

    if export:
        result["exported_files"] = _export_sessions(
            all_sessions, export_dir, org_id=org_id, cookie_header=cookie,
        )

    return result


# ── HTTP helpers ─────────────────────────────────────────────────────


def _make_ssl_context():
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _make_web_request(url, org_id, cookie_header, ssl_ctx, extra_headers=None):
    import urllib.request
    headers = {
        "content-type": "application/json",
        "Cookie": cookie_header,
        "User-Agent": "session-survey/1.0",
    }
    if org_id:
        headers["x-organization-uuid"] = org_id
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
        return json.loads(resp.read().decode())


# ── CLI sessions ─────────────────────────────────────────────────────


def _parse_cli_sessions() -> List[Dict[str, Any]]:
    sessions = []
    for project_dir in sorted(glob.glob(os.path.join(PROJECTS_DIR, "*"))):
        if not os.path.isdir(project_dir):
            continue
        project = os.path.basename(project_dir)
        for jsonl_path in sorted(glob.glob(os.path.join(project_dir, "*.jsonl"))):
            session_id = os.path.basename(jsonl_path).replace(".jsonl", "")
            first_ts = last_ts = branch = slug = cwd = version = title = None
            msg_count = 0
            try:
                with open(jsonl_path) as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        ts = obj.get("timestamp")
                        if ts:
                            if first_ts is None:
                                first_ts = ts
                            last_ts = ts
                        if obj.get("type") in ("user", "assistant"):
                            msg_count += 1
                        if obj.get("type") == "user" and not branch:
                            branch = obj.get("gitBranch")
                            slug = obj.get("slug")
                            cwd = obj.get("cwd")
                            version = obj.get("version")
                        if obj.get("type") == "user" and title is None:
                            msg = obj.get("message", {})
                            content = msg.get("content") if isinstance(msg, dict) else None
                            if isinstance(content, str):
                                title = content[:100]
                            elif isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        title = c["text"][:100]
                                        break
            except Exception:
                pass

            size_mb = os.path.getsize(jsonl_path) / (1024 * 1024)
            sessions.append({
                "source": "cli",
                "session_id": session_id,
                "project": project,
                "title": title,
                "status": "local",
                "model": None,
                "branch": branch,
                "slug": slug,
                "cwd": cwd,
                "repo": None,
                "created_at": first_ts,
                "updated_at": last_ts,
                "message_count": msg_count,
                "size_mb": round(size_mb, 1),
                "version": version,
            })
    return sessions


# ── Web Claude Code sessions ─────────────────────────────────────────


def _fetch_web_sessions(org_id, cookie_header) -> List[Dict[str, Any]]:
    ssl_ctx = _make_ssl_context()
    try:
        data = _make_web_request(
            "https://claude.ai/v1/sessions", org_id, cookie_header, ssl_ctx,
            extra_headers=_CODE_SESSION_HEADERS,
        )
    except Exception:
        return []

    sessions = []
    for s in data.get("data", []):
        ctx = s.get("session_context", {})
        sources = ctx.get("sources", [])
        outcomes = ctx.get("outcomes", [])
        repo = sources[0]["url"].replace("https://github.com/", "") if sources else None
        branch_list = outcomes[0].get("git_info", {}).get("branches", []) if outcomes else []
        sessions.append({
            "source": "web",
            "session_id": s["id"],
            "project": None,
            "title": s.get("title"),
            "status": s.get("session_status", "unknown"),
            "model": ctx.get("model"),
            "branch": branch_list[0] if branch_list else None,
            "slug": None,
            "cwd": None,
            "repo": repo,
            "created_at": s.get("created_at"),
            "updated_at": s.get("updated_at"),
            "message_count": None,
            "size_mb": None,
            "version": None,
        })
    return sessions


def _fetch_session_events(session_id, org_id, cookie_header, ssl_ctx) -> List[Dict]:
    all_events = []
    cursor = None
    page = 0
    while True:
        url = f"https://claude.ai/v1/sessions/{session_id}/events?limit=1000"
        if cursor:
            url += f"&last_id={cursor}"
        try:
            data = _make_web_request(url, org_id, cookie_header, ssl_ctx,
                                     extra_headers=_CODE_SESSION_HEADERS)
        except Exception:
            break
        events = data.get("data", [])
        all_events.extend(events)
        page += 1
        if not data.get("has_more") or not events:
            break
        cursor = events[-1].get("id")
        time.sleep(0.2)
    return all_events


def _parse_conversation_events(events) -> Dict[str, Any]:
    messages = []
    result_summary = None

    for ev in events:
        ev_type = ev.get("type")

        if ev_type == "user":
            content = ev.get("content", {})
            text = ""
            if isinstance(content, str):
                text = content
            elif isinstance(content, dict):
                parts = content.get("content", [])
                if isinstance(parts, str):
                    text = parts
                elif isinstance(parts, list):
                    text_parts = []
                    for p in parts:
                        if isinstance(p, dict) and p.get("type") == "text":
                            text_parts.append(p.get("text", ""))
                    text = "\n".join(text_parts)
            messages.append({
                "role": "user",
                "text": text,
                "timestamp": ev.get("created_at"),
                "id": ev.get("id"),
            })

        elif ev_type == "assistant":
            content = ev.get("content", {})
            text_parts = []
            tool_uses = []
            if isinstance(content, dict):
                for block in content.get("content", []):
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        tool_uses.append({
                            "tool": block.get("name"),
                            "id": block.get("id"),
                            "input_preview": _truncate(json.dumps(block.get("input", {})), 200),
                        })
            messages.append({
                "role": "assistant",
                "text": "\n".join(text_parts),
                "tool_uses": tool_uses if tool_uses else None,
                "timestamp": ev.get("created_at"),
                "id": ev.get("id"),
            })

        elif ev_type == "result":
            content = ev.get("content", {})
            result_summary = {
                "total_cost_usd": content.get("total_cost_usd"),
                "num_turns": content.get("num_turns"),
                "duration_ms": content.get("duration_ms"),
                "session_id": content.get("session_id"),
                "is_error": content.get("is_error"),
                "usage": content.get("usage"),
            }

        elif ev_type == "tool_use_summary":
            content = ev.get("content", {})
            messages.append({
                "role": "tool_result",
                "tool_use_id": content.get("tool_use_id"),
                "tool": content.get("name"),
                "output_preview": _truncate(str(content.get("output", "")), 500),
                "is_error": content.get("is_error", False),
                "timestamp": ev.get("created_at"),
                "id": ev.get("id"),
            })

    return {"messages": messages, "result": result_summary}


# ── Chat conversations ───────────────────────────────────────────────


def _fetch_chat_sessions(org_id, cookie_header) -> List[Dict[str, Any]]:
    ssl_ctx = _make_ssl_context()
    try:
        data = _make_web_request(
            f"https://claude.ai/api/organizations/{org_id}/chat_conversations",
            org_id, cookie_header, ssl_ctx,
        )
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    sessions = []
    for c in data:
        sessions.append({
            "source": "chat",
            "session_id": c["uuid"],
            "project": None,
            "title": c.get("name"),
            "status": "starred" if c.get("is_starred") else "chat",
            "model": c.get("model"),
            "branch": None,
            "slug": None,
            "cwd": None,
            "repo": None,
            "created_at": c.get("created_at"),
            "updated_at": c.get("updated_at"),
            "message_count": None,
            "size_mb": None,
            "version": None,
        })
    return sessions


def _fetch_chat_conversation(conv_id, org_id, cookie_header, ssl_ctx) -> Dict[str, Any]:
    url = f"https://claude.ai/api/organizations/{org_id}/chat_conversations/{conv_id}"
    data = _make_web_request(url, org_id, cookie_header, ssl_ctx)
    messages = []
    for m in data.get("chat_messages", []):
        role = "user" if m.get("sender") == "human" else "assistant"
        messages.append({
            "role": role,
            "text": m.get("text", ""),
            "timestamp": m.get("created_at"),
            "id": m.get("uuid"),
        })
    return {
        "messages": messages,
        "summary": data.get("summary"),
        "model": data.get("model"),
    }


# ── CLI session export ───────────────────────────────────────────────


def _export_cli_session(jsonl_path) -> Dict[str, Any]:
    messages = []
    metadata = {}

    with open(jsonl_path) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            obj_type = obj.get("type")

            if obj_type == "user":
                if not metadata.get("branch"):
                    metadata["branch"] = obj.get("gitBranch")
                    metadata["cwd"] = obj.get("cwd")
                    metadata["version"] = obj.get("version")

                msg = obj.get("message", {})
                text = ""
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list):
                        text_parts = []
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "text":
                                text_parts.append(c.get("text", ""))
                        text = "\n".join(text_parts)

                messages.append({
                    "role": "user",
                    "text": text,
                    "timestamp": obj.get("timestamp"),
                    "id": obj.get("uuid"),
                })

            elif obj_type == "assistant":
                msg = obj.get("message", {})
                text_parts = []
                tool_uses = []
                if isinstance(msg, dict):
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            if block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                            elif block.get("type") == "tool_use":
                                tool_uses.append({
                                    "tool": block.get("name"),
                                    "id": block.get("id"),
                                    "input_preview": _truncate(json.dumps(block.get("input", {})), 200),
                                })
                            elif block.get("type") == "tool_result":
                                messages.append({
                                    "role": "tool_result",
                                    "tool_use_id": block.get("tool_use_id"),
                                    "output_preview": _truncate(str(block.get("content", "")), 500),
                                    "is_error": block.get("is_error", False),
                                    "timestamp": obj.get("timestamp"),
                                })

                messages.append({
                    "role": "assistant",
                    "text": "\n".join(text_parts),
                    "tool_uses": tool_uses if tool_uses else None,
                    "timestamp": obj.get("timestamp"),
                    "id": obj.get("uuid"),
                })

    return {"messages": messages, "metadata": metadata}


# ── Export orchestration ─────────────────────────────────────────────


def _export_sessions(sessions, export_dir, org_id=None, cookie_header=None) -> List[str]:
    ssl_ctx = None
    if org_id and cookie_header:
        ssl_ctx = _make_ssl_context()

    os.makedirs(export_dir, exist_ok=True)
    exported = []

    for s in sessions:
        sid = s["session_id"]
        source = s["source"]
        safe_title = (s.get("title") or "untitled").split("\n")[0][:50]
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in safe_title).strip()

        if source == "web":
            if not org_id or not cookie_header or not ssl_ctx:
                continue
            events = _fetch_session_events(sid, org_id, cookie_header, ssl_ctx)
            if not events:
                continue
            conversation = _parse_conversation_events(events)
            export_data = {
                "source": "web",
                "session_id": sid,
                "title": s.get("title"),
                "status": s.get("status"),
                "model": s.get("model"),
                "repo": s.get("repo"),
                "branch": s.get("branch"),
                "created_at": s.get("created_at"),
                "updated_at": s.get("updated_at"),
                "conversation": conversation["messages"],
                "result_summary": conversation["result"],
                "raw_event_count": len(events),
            }

        elif source == "chat":
            if not org_id or not cookie_header or not ssl_ctx:
                continue
            try:
                parsed = _fetch_chat_conversation(sid, org_id, cookie_header, ssl_ctx)
            except Exception:
                continue
            if not parsed["messages"]:
                continue
            export_data = {
                "source": "chat",
                "session_id": sid,
                "title": s.get("title"),
                "model": s.get("model") or parsed.get("model"),
                "created_at": s.get("created_at"),
                "updated_at": s.get("updated_at"),
                "summary": parsed.get("summary"),
                "conversation": parsed["messages"],
                "result_summary": None,
            }
            time.sleep(0.2)

        elif source == "cli":
            project = s.get("project", "unknown")
            jsonl_path = os.path.join(PROJECTS_DIR, project, f"{sid}.jsonl")
            if not os.path.exists(jsonl_path):
                continue
            parsed = _export_cli_session(jsonl_path)
            export_data = {
                "source": "cli",
                "session_id": sid,
                "project": project,
                "title": s.get("title"),
                "branch": s.get("branch") or parsed["metadata"].get("branch"),
                "cwd": s.get("cwd") or parsed["metadata"].get("cwd"),
                "version": s.get("version") or parsed["metadata"].get("version"),
                "created_at": s.get("created_at"),
                "updated_at": s.get("updated_at"),
                "message_count": s.get("message_count"),
                "conversation": parsed["messages"],
                "result_summary": None,
            }
        else:
            continue

        filename = f"{source}_{sid[:40]}_{safe_title}.json"
        filepath = os.path.join(export_dir, filename)
        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
        exported.append(filepath)

    return exported


# ── Utility ──────────────────────────────────────────────────────────


def _truncate(s, max_len):
    if len(s) <= max_len:
        return s
    return s[:max_len] + "..."
