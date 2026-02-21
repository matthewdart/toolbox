#!/usr/bin/env python3
"""
Unified Claude session survey — combines local CLI sessions, web Claude Code sessions,
and regular claude.ai chat conversations.

Web sessions and chat require a browser session cookie. To obtain one:
  1. Open claude.ai in Chrome
  2. Open DevTools > Application > Cookies
  3. Copy the cookie header string
  4. Pass via --cookie or CLAUDE_SESSION_COOKIE env var

Alternatively, pass --local-only to skip web sessions.

Output: JSON to stdout, human-readable to stderr.
"""

import argparse
import json
import os
import sys
import glob
import time
from datetime import datetime, timezone

CLAUDE_DIR = os.path.expanduser("~/.claude")
PROJECTS_DIR = os.path.join(CLAUDE_DIR, "projects")

DEFAULT_EXPORT_DIR = os.path.join(CLAUDE_DIR, "exports")


def parse_cli_sessions():
    """Parse all local CLI session .jsonl files."""
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
                "status": "local",  # CLI sessions don't have active/idle
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


def fetch_web_sessions(org_id, cookie_header):
    """Fetch web Claude Code sessions via /v1/sessions API."""
    ssl_ctx = _make_ssl_context()

    try:
        data = _make_web_request(
            "https://claude.ai/v1/sessions", org_id, cookie_header, ssl_ctx,
            extra_headers=_CODE_SESSION_HEADERS,
        )
    except Exception as e:
        print(f"[web] Failed to fetch sessions: {e}", file=sys.stderr)
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


def _make_ssl_context():
    """Create an SSL context, using certifi if available."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _make_web_request(url, org_id, cookie_header, ssl_ctx, extra_headers=None):
    """Make an authenticated request to the claude.ai API."""
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


# Headers required specifically for the /v1/sessions (Claude Code) API
_CODE_SESSION_HEADERS = {
    "anthropic-beta": "ccr-byoc-2025-07-29",
    "anthropic-client-feature": "ccr",
    "anthropic-client-platform": "web_claude_ai",
    "anthropic-version": "2023-06-01",
}


def fetch_chat_sessions(org_id, cookie_header):
    """Fetch regular claude.ai chat conversations."""
    ssl_ctx = _make_ssl_context()

    try:
        data = _make_web_request(
            f"https://claude.ai/api/organizations/{org_id}/chat_conversations",
            org_id, cookie_header, ssl_ctx,
        )
    except Exception as e:
        print(f"[chat] Failed to fetch conversations: {e}", file=sys.stderr)
        return []

    if not isinstance(data, list):
        print(f"[chat] Unexpected response format", file=sys.stderr)
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


def fetch_chat_conversation(conv_id, org_id, cookie_header, ssl_ctx):
    """Fetch full chat conversation messages."""
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
        "settings": data.get("settings"),
    }


def fetch_session_events(session_id, org_id, cookie_header, ssl_ctx):
    """Fetch all events for a web session, handling pagination."""
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
        except Exception as e:
            print(f"  [events] Failed page {page}: {e}", file=sys.stderr)
            break

        events = data.get("data", [])
        all_events.extend(events)
        page += 1

        if not data.get("has_more") or not events:
            break
        cursor = events[-1].get("id")
        time.sleep(0.2)  # gentle rate limiting

    return all_events


def parse_conversation_events(events):
    """Parse raw events into a structured conversation with metadata."""
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


def export_cli_session(jsonl_path):
    """Read a CLI session .jsonl and normalize into conversation format."""
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


def _truncate(s, max_len):
    if len(s) <= max_len:
        return s
    return s[:max_len] + "..."


def export_sessions(sessions, export_dir, org_id=None, cookie_header=None):
    """Export full conversations for the given sessions."""
    ssl_ctx = None
    if org_id and cookie_header:
        ssl_ctx = _make_ssl_context()

    os.makedirs(export_dir, exist_ok=True)
    exported = []

    for s in sessions:
        sid = s["session_id"]
        source = s["source"]
        safe_title = (s.get("title") or "untitled").split("\n")[0][:50]
        # Sanitize for filename
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in safe_title).strip()

        if source == "web":
            if not org_id or not cookie_header or not ssl_ctx:
                print(f"  [skip] {sid} — web session but no auth provided", file=sys.stderr)
                continue

            print(f"  [web] Exporting: {safe_title} ({sid[:20]}...)", file=sys.stderr)
            events = fetch_session_events(sid, org_id, cookie_header, ssl_ctx)
            if not events:
                print(f"    No events found", file=sys.stderr)
                continue

            conversation = parse_conversation_events(events)
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
                print(f"  [skip] {sid} — chat session but no auth provided", file=sys.stderr)
                continue

            print(f"  [chat] Exporting: {safe_title} ({sid[:20]}...)", file=sys.stderr)
            try:
                parsed = fetch_chat_conversation(sid, org_id, cookie_header, ssl_ctx)
            except Exception as e:
                print(f"    Failed: {e}", file=sys.stderr)
                continue
            if not parsed["messages"]:
                print(f"    No messages found", file=sys.stderr)
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
            time.sleep(0.2)  # gentle rate limiting

        elif source == "cli":
            project = s.get("project", "unknown")
            jsonl_path = os.path.join(PROJECTS_DIR, project, f"{sid}.jsonl")
            if not os.path.exists(jsonl_path):
                print(f"  [skip] {sid} — file not found", file=sys.stderr)
                continue

            print(f"  [cli] Exporting: {safe_title} ({sid[:20]}...)", file=sys.stderr)
            parsed = export_cli_session(jsonl_path)
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

        msg_count = len([m for m in export_data["conversation"] if m["role"] in ("user", "assistant")])
        print(f"    -> {filepath} ({msg_count} messages)", file=sys.stderr)
        exported.append(filepath)

    return exported


def print_report(all_sessions):
    """Print a human-readable summary to stderr."""
    cli = [s for s in all_sessions if s["source"] == "cli"]
    web = [s for s in all_sessions if s["source"] == "web"]
    chat = [s for s in all_sessions if s["source"] == "chat"]

    print("\n=== Claude Session Survey ===\n", file=sys.stderr)

    if chat:
        print(f"Chat conversations: {len(chat)} total", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        for s in sorted(chat, key=lambda x: x.get("updated_at") or "", reverse=True):
            title = (s["title"] or "Untitled")[:60]
            updated = (s["updated_at"] or "")[:10]
            model = s.get("model") or ""
            print(f"  💬 {title:<60s} {updated}  {model}", file=sys.stderr)
        print(file=sys.stderr)

    if web:
        web_active = [s for s in web if s["status"] == "active"]
        web_idle = [s for s in web if s["status"] == "idle"]
        web_archived = [s for s in web if s["status"] == "archived"]

        print(f"Web Claude Code sessions: {len(web)} total "
              f"({len(web_active)} active, {len(web_idle)} idle, {len(web_archived)} archived)",
              file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        for s in sorted(web, key=lambda x: x.get("updated_at") or "", reverse=True):
            status_icon = {"active": "🟢", "idle": "🟡", "archived": "⚫"}.get(s["status"], "❓")
            title = (s["title"] or "Untitled")[:60]
            updated = (s["updated_at"] or "")[:10]
            print(f"  {status_icon} [{s['status']:8s}] {title:<60s} {updated}  {s.get('model', '')}", file=sys.stderr)
        print(file=sys.stderr)

    if cli:
        # Group by project
        projects = {}
        for s in cli:
            projects.setdefault(s["project"], []).append(s)

        print(f"Local CLI sessions: {len(cli)} total across {len(projects)} projects", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        for project, sess in sorted(projects.items()):
            print(f"\n  📁 {project}", file=sys.stderr)
            for s in sorted(sess, key=lambda x: x.get("updated_at") or "", reverse=True):
                title = (s["title"] or "Untitled")[:55]
                # Clean up multiline titles
                title = title.split("\n")[0]
                updated = (s["updated_at"] or "")[:10]
                msgs = s.get("message_count", 0)
                size = s.get("size_mb", 0)
                branch = s.get("branch", "")
                print(f"     {title:<55s} {updated}  {msgs:>4d} msgs  {size:>5.1f}MB  {branch}", file=sys.stderr)
        print(file=sys.stderr)

    print(f"\nTotal: {len(all_sessions)} sessions ({len(chat)} chat, {len(web)} code, {len(cli)} CLI)\n", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Survey all Claude sessions (CLI + web)")
    parser.add_argument("--org-id", default=os.environ.get("CLAUDE_ORG_ID"),
                        help="Claude organization UUID (or set CLAUDE_ORG_ID)")
    parser.add_argument("--cookie", default=os.environ.get("CLAUDE_SESSION_COOKIE"),
                        help="Browser cookie header for claude.ai auth (or set CLAUDE_SESSION_COOKIE)")
    parser.add_argument("--local-only", action="store_true",
                        help="Only show local CLI sessions, skip web")
    parser.add_argument("--web-only", action="store_true",
                        help="Only show web Claude Code sessions, skip local CLI and chat")
    parser.add_argument("--chat-only", action="store_true",
                        help="Only show claude.ai chat conversations, skip CLI and Code")
    parser.add_argument("--json-only", action="store_true",
                        help="Only output JSON to stdout, no human-readable report")
    parser.add_argument("--status", choices=["active", "idle", "archived", "all"], default="all",
                        help="Filter web Code sessions by status")
    # Export flags
    parser.add_argument("--export", action="store_true",
                        help="Export full conversations for all matched sessions")
    parser.add_argument("--export-dir", default=DEFAULT_EXPORT_DIR,
                        help=f"Directory to write exported conversations (default: {DEFAULT_EXPORT_DIR})")
    parser.add_argument("--session-id",
                        help="Export a specific session by ID (partial match supported)")
    args = parser.parse_args()

    all_sessions = []
    has_web_auth = args.org_id and args.cookie
    # Determine which sources to include
    include_cli = not args.web_only and not args.chat_only
    include_code = not args.local_only and not args.chat_only
    include_chat = not args.local_only and not args.web_only

    if include_cli:
        cli_sessions = parse_cli_sessions()
        all_sessions.extend(cli_sessions)

    if include_code or include_chat:
        if not has_web_auth:
            skipped = []
            if include_code:
                skipped.append("Code sessions")
            if include_chat:
                skipped.append("chat conversations")
            print(f"[web] Skipping {' and '.join(skipped)}: --org-id and --cookie required (or set env vars). "
                  "Use --local-only to suppress this message.", file=sys.stderr)
        else:
            if include_code:
                web_sessions = fetch_web_sessions(args.org_id, args.cookie)
                if args.status != "all":
                    web_sessions = [s for s in web_sessions if s["status"] == args.status]
                all_sessions.extend(web_sessions)
            if include_chat:
                chat_sessions = fetch_chat_sessions(args.org_id, args.cookie)
                all_sessions.extend(chat_sessions)

    # Filter by session ID if specified
    if args.session_id:
        all_sessions = [s for s in all_sessions if args.session_id in s["session_id"]]
        if not all_sessions:
            print(f"No sessions matching '{args.session_id}'", file=sys.stderr)
            sys.exit(1)

    if args.export:
        print(f"\n=== Exporting {len(all_sessions)} session(s) to {args.export_dir} ===\n", file=sys.stderr)
        exported = export_sessions(
            all_sessions, args.export_dir,
            org_id=args.org_id, cookie_header=args.cookie,
        )
        print(f"\nExported {len(exported)} conversation(s)\n", file=sys.stderr)
    else:
        if not args.json_only:
            print_report(all_sessions)
        json.dump(all_sessions, sys.stdout, indent=2, default=str)
        print(file=sys.stdout)


if __name__ == "__main__":
    main()
