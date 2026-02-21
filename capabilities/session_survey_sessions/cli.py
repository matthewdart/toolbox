#!/usr/bin/env python3
"""CLI wrapper for session.survey_sessions capability.

Human-readable report to stderr, JSON to stdout.
"""
import argparse
import json
import os
import sys

from capabilities.session_survey_sessions.implementation import (
    survey_sessions,
    DEFAULT_EXPORT_DIR,
)


def _print_report(sessions):
    """Print a human-readable summary to stderr."""
    cli = [s for s in sessions if s["source"] == "cli"]
    web = [s for s in sessions if s["source"] == "web"]
    chat = [s for s in sessions if s["source"] == "chat"]

    print("\n=== Claude Session Survey ===\n", file=sys.stderr)

    if chat:
        print(f"Chat conversations: {len(chat)} total", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        for s in sorted(chat, key=lambda x: x.get("updated_at") or "", reverse=True):
            title = (s["title"] or "Untitled")[:60]
            updated = (s["updated_at"] or "")[:10]
            model = s.get("model") or ""
            print(f"  \U0001f4ac {title:<60s} {updated}  {model}", file=sys.stderr)
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
            status_icon = {"active": "\U0001f7e2", "idle": "\U0001f7e1", "archived": "\u26ab"}.get(s["status"], "\u2753")
            title = (s["title"] or "Untitled")[:60]
            updated = (s["updated_at"] or "")[:10]
            print(f"  {status_icon} [{s['status']:8s}] {title:<60s} {updated}  {s.get('model', '')}", file=sys.stderr)
        print(file=sys.stderr)

    if cli:
        projects = {}
        for s in cli:
            projects.setdefault(s["project"], []).append(s)
        print(f"Local CLI sessions: {len(cli)} total across {len(projects)} projects", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        for project, sess in sorted(projects.items()):
            print(f"\n  \U0001f4c1 {project}", file=sys.stderr)
            for s in sorted(sess, key=lambda x: x.get("updated_at") or "", reverse=True):
                title = (s["title"] or "Untitled")[:55]
                title = title.split("\n")[0]
                updated = (s["updated_at"] or "")[:10]
                msgs = s.get("message_count", 0)
                size = s.get("size_mb", 0)
                branch = s.get("branch", "")
                print(f"     {title:<55s} {updated}  {msgs:>4d} msgs  {size:>5.1f}MB  {branch}", file=sys.stderr)
        print(file=sys.stderr)

    print(f"\nTotal: {len(sessions)} sessions ({len(chat)} chat, {len(web)} code, {len(cli)} CLI)\n", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Survey all Claude sessions (CLI + web + chat)")
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
    parser.add_argument("--export", action="store_true",
                        help="Export full conversations for all matched sessions")
    parser.add_argument("--export-dir", default=DEFAULT_EXPORT_DIR,
                        help=f"Directory to write exported conversations (default: {DEFAULT_EXPORT_DIR})")
    parser.add_argument("--session-id",
                        help="Filter to a specific session by ID (partial match supported)")
    args = parser.parse_args()

    # Map CLI flags to sources list
    if args.local_only:
        sources = ["cli"]
    elif args.web_only:
        sources = ["code"]
    elif args.chat_only:
        sources = ["chat"]
    else:
        sources = ["cli", "code", "chat"]

    result = survey_sessions(
        sources=sources,
        org_id=args.org_id,
        cookie=args.cookie,
        status_filter=args.status if args.status != "all" else None,
        session_id=args.session_id,
        export=args.export,
        export_dir=args.export_dir,
    )

    for w in result.get("warnings", []):
        print(f"[warn] {w}", file=sys.stderr)

    if args.export:
        exported = result.get("exported_files") or []
        print(f"\nExported {len(exported)} conversation(s) to {args.export_dir}\n", file=sys.stderr)
        for f in exported:
            print(f"  {f}", file=sys.stderr)
    else:
        if not args.json_only:
            _print_report(result["sessions"])
        json.dump(result["sessions"], sys.stdout, indent=2, default=str)
        print(file=sys.stdout)


if __name__ == "__main__":
    main()
