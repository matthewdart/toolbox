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


def _resolve_account_id(account_id: Optional[str]) -> str:
    """Resolve account ID from parameter or CLOUDFLARE_ACCOUNT_ID env var."""
    resolved = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not resolved:
        raise ValidationError(
            "account_id is required (pass it or set CLOUDFLARE_ACCOUNT_ID)."
        )
    return resolved


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


def _cmd_get_portal(account_id: str, portal_id: str) -> Dict[str, Any]:
    """Get portal detail including assigned server list."""
    resp = _request("GET", f"/accounts/{account_id}/access/ai-controls/mcp/portals/{portal_id}")
    result = resp.get("result", resp)
    return {"command": "get_portal", "account_id": account_id, "result": result}


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


def _cmd_update_server(
    account_id: str,
    server_id: str,
    name: Optional[str] = None,
    url: Optional[str] = None,
    auth_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing MCP server's properties."""
    body: Dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if url is not None:
        body["hostname"] = url
    if auth_type is not None:
        body["auth_type"] = auth_type
    if not body:
        raise ValidationError("update_server requires at least one of: name, url, auth_type")
    resp = _request(
        "PUT",
        f"/accounts/{account_id}/access/ai-controls/mcp/servers/{server_id}",
        body,
    )
    result = resp.get("result", resp)
    return {"command": "update_server", "account_id": account_id, "result": result}


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


def _cmd_update_portal_servers(
    account_id: str,
    portal_id: str,
    server_ids: List[str],
) -> Dict[str, Any]:
    """Replace the portal's server list."""
    body = {"servers": [{"server_id": sid} for sid in server_ids]}
    resp = _request(
        "PUT",
        f"/accounts/{account_id}/access/ai-controls/mcp/portals/{portal_id}",
        body,
    )
    result = resp.get("result", resp)
    return {"command": "update_portal_servers", "account_id": account_id, "result": result}


def _probe_url(url: str, *, method: str = "GET", timeout: int = 10) -> Dict[str, Any]:
    """HTTP probe a URL. Returns status code and any error."""
    ctx = _ssl_context()
    req = urllib.request.Request(url, method=method)
    req.add_header("User-Agent", "toolbox-mcp-portal-verify/1.0")
    if method == "POST":
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return {"status": resp.status, "ok": True, "error": None}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "ok": False, "error": f"HTTP {exc.code}"}
    except Exception as exc:
        return {"status": None, "ok": False, "error": str(exc)}


def _cmd_verify_portal(account_id: str, portal_id: str) -> Dict[str, Any]:
    """Verify end-to-end health of a portal and all its servers.

    Checks performed per server:
      1. Server registration status (Cloudflare API)
      2. Portal assignment (server present in portal's server list)
      3. Health endpoint probe (GET <hostname>/health via public URL)
      4. MCP endpoint probe (POST <hostname>/mcp via public URL)
    """
    # Fetch portal detail (includes server list).
    portal_resp = _request(
        "GET", f"/accounts/{account_id}/access/ai-controls/mcp/portals/{portal_id}"
    )
    portal = portal_resp.get("result", {})
    portal_servers = portal.get("servers", [])
    portal_server_ids = {s.get("id") for s in portal_servers}

    # Fetch all registered servers.
    servers_resp = _request(
        "GET", f"/accounts/{account_id}/access/ai-controls/mcp/servers"
    )
    all_servers = servers_resp.get("result", [])

    checks: List[Dict[str, Any]] = []
    all_ok = True

    for server in all_servers:
        sid = server.get("id", "")
        hostname = server.get("hostname", "")
        status = server.get("status", "unknown")
        in_portal = sid in portal_server_ids

        server_check: Dict[str, Any] = {
            "server_id": sid,
            "hostname": hostname,
            "registration_status": status,
            "in_portal": in_portal,
            "checks": [],
        }

        # Check 1: registration status.
        reg_ok = status == "ready"
        server_check["checks"].append({
            "name": "registration",
            "ok": reg_ok,
            "detail": f"status={status}",
        })

        # Check 2: portal assignment.
        server_check["checks"].append({
            "name": "portal_assignment",
            "ok": in_portal,
            "detail": f"in portal {portal_id}" if in_portal else f"NOT in portal {portal_id}",
        })

        # Derive base URL from hostname (strip /mcp suffix for health probe).
        base_url = hostname.rstrip("/")
        if base_url.endswith("/mcp"):
            base_url = base_url[:-4]

        # Check 3: health endpoint.
        health_probe = _probe_url(f"{base_url}/health")
        server_check["checks"].append({
            "name": "health_endpoint",
            "ok": health_probe["ok"],
            "detail": f"GET {base_url}/health → {health_probe.get('status') or health_probe.get('error')}",
        })

        # Check 4: MCP endpoint (POST triggers initialize handshake expectation).
        mcp_probe = _probe_url(f"{base_url}/mcp", method="POST")
        # MCP endpoint returning any response (even 4xx like 406 "Not Acceptable")
        # means the server is reachable. Only connection/timeout errors indicate failure.
        mcp_reachable = mcp_probe["status"] is not None
        server_check["checks"].append({
            "name": "mcp_endpoint",
            "ok": mcp_reachable,
            "detail": f"POST {base_url}/mcp → {mcp_probe.get('status') or mcp_probe.get('error')}",
        })

        server_ok = all(c["ok"] for c in server_check["checks"])
        server_check["ok"] = server_ok
        if not server_ok:
            all_ok = False
        checks.append(server_check)

    return {
        "command": "verify_portal",
        "account_id": account_id,
        "result": {
            "portal_id": portal_id,
            "portal_name": portal.get("name", portal_id),
            "all_ok": all_ok,
            "server_count": len(all_servers),
            "portal_server_count": len(portal_server_ids),
            "servers": checks,
        },
    }


# -- Entry point -------------------------------------------------------------


_COMMANDS = {
    "list_servers": lambda kw: _cmd_list_servers(kw["account_id"]),
    "list_portals": lambda kw: _cmd_list_portals(kw["account_id"]),
    "get_portal": lambda kw: _cmd_get_portal(
        account_id=kw["account_id"],
        portal_id=kw["portal_id"],
    ),
    "add_server": lambda kw: _cmd_add_server(
        account_id=kw["account_id"],
        name=kw["name"],
        url=kw["url"],
        auth_type=kw.get("auth_type", "unauthenticated"),
        server_id=kw.get("server_id"),
    ),
    "update_server": lambda kw: _cmd_update_server(
        account_id=kw["account_id"],
        server_id=kw["server_id"],
        name=kw.get("name"),
        url=kw.get("url"),
        auth_type=kw.get("auth_type"),
    ),
    "sync_server": lambda kw: _cmd_sync_server(
        account_id=kw["account_id"],
        server_id=kw["server_id"],
    ),
    "remove_server": lambda kw: _cmd_remove_server(
        account_id=kw["account_id"],
        server_id=kw["server_id"],
    ),
    "update_portal_servers": lambda kw: _cmd_update_portal_servers(
        account_id=kw["account_id"],
        portal_id=kw["portal_id"],
        server_ids=kw["server_ids"],
    ),
    "verify_portal": lambda kw: _cmd_verify_portal(
        account_id=kw["account_id"],
        portal_id=kw["portal_id"],
    ),
}


def setup_mcp_portal(**kwargs: Any) -> Dict[str, Any]:
    """Manage Cloudflare MCP Portal servers and portals.

    Args:
        command: One of list_servers, list_portals, get_portal, add_server,
                 update_server, sync_server, remove_server, update_portal_servers,
                 verify_portal.
        account_id: Cloudflare account ID. Defaults to CLOUDFLARE_ACCOUNT_ID env var.
        name: Server display name (add_server, update_server).
        url: Server URL (add_server required, update_server optional).
        auth_type: Auth type (add_server, update_server; default: unauthenticated).
        server_id: Server ID (sync_server/remove_server/update_server required,
                   add_server optional — defaults to name).
        portal_id: Portal ID (get_portal, update_portal_servers).
        server_ids: List of server IDs (update_portal_servers).

    Returns:
        Dict with command, account_id, result, and optionally count or error.

    Raises:
        ValidationError: Missing or invalid parameters.
        AuthError: Cloudflare credentials not found.
        APIError: Cloudflare API returned an error.
    """
    command: Optional[str] = kwargs.get("command")
    account_id = _resolve_account_id(kwargs.get("account_id"))

    if not command:
        raise ValidationError("command is required")
    if command not in _COMMANDS:
        raise ValidationError(
            f"Unknown command: {command}. "
            f"Valid commands: {', '.join(sorted(_COMMANDS))}"
        )

    # Inject resolved account_id back so command handlers can use it.
    kwargs["account_id"] = account_id

    # Validate command-specific required parameters.
    if command == "add_server":
        if not kwargs.get("name"):
            raise ValidationError("name is required for add_server")
        if not kwargs.get("url"):
            raise ValidationError("url is required for add_server")
    elif command in ("sync_server", "remove_server", "update_server"):
        if not kwargs.get("server_id"):
            raise ValidationError(f"server_id is required for {command}")
    elif command in ("get_portal", "update_portal_servers", "verify_portal"):
        if not kwargs.get("portal_id"):
            raise ValidationError(f"portal_id is required for {command}")
    if command == "update_portal_servers":
        if not kwargs.get("server_ids"):
            raise ValidationError("server_ids is required for update_portal_servers")

    return _COMMANDS[command](kwargs)
