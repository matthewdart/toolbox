"""Core capability: manage Cloudflare MCP Portal servers and portals via the Cloudflare API."""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

_BASE = "https://api.cloudflare.com/client/v4"


class MCPPortalError(Exception):
    """Base error for MCP portal capability failures."""


class AuthError(MCPPortalError):
    """Raised when Cloudflare credentials are missing."""


class ValidationError(MCPPortalError):
    """Raised when required parameters are missing or invalid."""


class APIError(MCPPortalError):
    """Raised when the Cloudflare API returns an error."""


def _ssl_context() -> ssl.SSLContext:
    """Build an SSL context, preferring certifi certs if available."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _auth_headers() -> Dict[str, str]:
    """Build auth headers from environment variables.

    Supports two auth modes:
      - API Token:  CLOUDFLARE_API_TOKEN
      - Global Key: CLOUDFLARE_API_KEY + CLOUDFLARE_EMAIL
    """
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    api_key = os.environ.get("CLOUDFLARE_API_KEY")
    email = os.environ.get("CLOUDFLARE_EMAIL")
    if api_key and email:
        return {"X-Auth-Key": api_key, "X-Auth-Email": email}
    raise AuthError(
        "Set CLOUDFLARE_API_TOKEN or (CLOUDFLARE_API_KEY + CLOUDFLARE_EMAIL)."
    )


def _request(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute an HTTP request against the Cloudflare API."""
    url = f"{_BASE}{path}"
    headers = {
        **_auth_headers(),
        "Content-Type": "application/json",
        "User-Agent": "toolbox-setup-mcp-portal/1.0",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=_ssl_context()) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode()
        try:
            err = json.loads(error_body)
            errors = err.get("errors", [])
            msg = (
                "; ".join(e.get("message", str(e)) for e in errors)
                if errors
                else error_body
            )
        except json.JSONDecodeError:
            msg = error_body
        raise APIError(f"API error ({exc.code}): {msg}") from exc


# -- Command handlers --------------------------------------------------------


def _cmd_list_servers(account_id: str) -> Dict[str, Any]:
    """List all registered MCP servers."""
    resp = _request("GET", f"/accounts/{account_id}/access/ai-controls/mcp/servers")
    items: List[Dict[str, Any]] = resp.get("result", [])
    return {"command": "list_servers", "account_id": account_id, "result": items, "count": len(items)}


def _cmd_list_portals(account_id: str) -> Dict[str, Any]:
    """List all MCP portals."""
    resp = _request("GET", f"/accounts/{account_id}/access/ai-controls/mcp/portals")
    items: List[Dict[str, Any]] = resp.get("result", [])
    return {"command": "list_portals", "account_id": account_id, "result": items, "count": len(items)}


def _cmd_add_server(
    account_id: str,
    name: str,
    url: str,
    auth_type: str = "unauthenticated",
    server_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a new MCP server."""
    body = {
        "id": server_id or name,
        "name": name,
        "hostname": url,
        "auth_type": auth_type,
    }
    resp = _request(
        "POST",
        f"/accounts/{account_id}/access/ai-controls/mcp/servers",
        body,
    )
    result = resp.get("result", resp)
    return {"command": "add_server", "account_id": account_id, "result": result}


def _cmd_sync_server(account_id: str, server_id: str) -> Dict[str, Any]:
    """Trigger a capability sync for a server."""
    resp = _request(
        "POST",
        f"/accounts/{account_id}/access/ai-controls/mcp/servers/{server_id}/sync",
    )
    result = resp.get("result", resp)
    return {"command": "sync_server", "account_id": account_id, "result": result}


def _cmd_remove_server(account_id: str, server_id: str) -> Dict[str, Any]:
    """Delete an MCP server registration."""
    resp = _request(
        "DELETE",
        f"/accounts/{account_id}/access/ai-controls/mcp/servers/{server_id}",
    )
    result = resp.get("result", resp)
    return {"command": "remove_server", "account_id": account_id, "result": result}


# -- Entry point -------------------------------------------------------------


_COMMANDS = {
    "list_servers": lambda kw: _cmd_list_servers(kw["account_id"]),
    "list_portals": lambda kw: _cmd_list_portals(kw["account_id"]),
    "add_server": lambda kw: _cmd_add_server(
        account_id=kw["account_id"],
        name=kw["name"],
        url=kw["url"],
        auth_type=kw.get("auth_type", "unauthenticated"),
        server_id=kw.get("server_id"),
    ),
    "sync_server": lambda kw: _cmd_sync_server(
        account_id=kw["account_id"],
        server_id=kw["server_id"],
    ),
    "remove_server": lambda kw: _cmd_remove_server(
        account_id=kw["account_id"],
        server_id=kw["server_id"],
    ),
}


def setup_mcp_portal(**kwargs: Any) -> Dict[str, Any]:
    """Manage Cloudflare MCP Portal servers and portals.

    Args:
        command: One of list_servers, list_portals, add_server, sync_server, remove_server.
        account_id: Cloudflare account ID.
        name: Server display name (add_server).
        url: Server URL (add_server).
        auth_type: Auth type (add_server, default: unauthenticated).
        server_id: Server ID (add_server optional, sync_server/remove_server required).

    Returns:
        Dict with command, account_id, result, and optionally count or error.

    Raises:
        ValidationError: Missing or invalid parameters.
        AuthError: Cloudflare credentials not found.
        APIError: Cloudflare API returned an error.
    """
    command: Optional[str] = kwargs.get("command")
    account_id: Optional[str] = kwargs.get("account_id")

    if not command:
        raise ValidationError("command is required")
    if not account_id:
        raise ValidationError("account_id is required")
    if command not in _COMMANDS:
        raise ValidationError(
            f"Unknown command: {command}. "
            f"Valid commands: {', '.join(sorted(_COMMANDS))}"
        )

    # Validate command-specific required parameters.
    if command == "add_server":
        if not kwargs.get("name"):
            raise ValidationError("name is required for add_server")
        if not kwargs.get("url"):
            raise ValidationError("url is required for add_server")
    elif command in ("sync_server", "remove_server"):
        if not kwargs.get("server_id"):
            raise ValidationError(f"server_id is required for {command}")

    return _COMMANDS[command](kwargs)
