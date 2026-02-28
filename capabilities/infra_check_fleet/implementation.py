"""Core capability: verify health of all MCP services across local and tunnel surfaces."""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from capabilities._infra_common import run_cmd, run_shell


class FleetHealthError(Exception):
    """Base error for fleet health failures."""


class DependencyError(FleetHealthError):
    """Raised when required external dependencies are missing."""


# ── Service Registry ──────────────────────────────────────────────────

SERVICES = [
    {
        "name": "remarkable-pipeline",
        "compose_dir": "/opt/remarkable-pipeline",
        "port": 8766,
        "smoke_tool": "remarkable_status",
        "smoke_args": {"detail": "summary"},
        "hostname": "remarkable-pipeline-mcp.matthewdart.name",
        "mcp_transport": "streamable-http",
    },
    {
        "name": "health-ledger",
        "compose_dir": "/opt/health-ledger",
        "port": 8765,
        "smoke_tool": "list_assets",
        "smoke_args": {},
        "hostname": "health-ledger.matthewdart.name",
        "mcp_transport": "streamable-http",
    },
    {
        "name": "archi-mcp-bridge",
        "compose_dir": "/opt/archi-mcp-bridge",
        "port": 8767,
        "smoke_tool": "jarchi_catalog",
        "smoke_args": {},
        "hostname": "archi-mcp-bridge.matthewdart.name",
        "mcp_transport": "custom-http",
    },
]


# ── Local checks ─────────────────────────────────────────────────────

def _check_container(svc: Dict[str, Any]) -> Dict[str, Any]:
    """Check container status via docker compose ps."""
    try:
        proc = run_shell(f"cd {svc['compose_dir']} && docker compose ps --format json", timeout=15)
        if proc.returncode != 0:
            return {"running": False, "error": proc.stderr.strip()[:200]}
        containers = []
        for line in proc.stdout.strip().splitlines():
            try:
                containers.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        running = any(
            (c.get("State", "").lower() == "running" or c.get("status", "").startswith("Up"))
            for c in containers
        )
        health = "unknown"
        for c in containers:
            h = c.get("Health", c.get("health", ""))
            if h:
                health = h
                break
        return {"running": running, "health": health, "container_count": len(containers)}
    except subprocess.TimeoutExpired:
        return {"running": False, "error": "timeout"}
    except Exception as exc:
        return {"running": False, "error": str(exc)[:200]}


def _check_health_endpoint(svc: Dict[str, Any]) -> Dict[str, Any]:
    """Probe localhost:<port>/health."""
    port = svc["port"]
    try:
        proc = run_cmd(["curl", "-fsS", "--max-time", "10", f"http://localhost:{port}/health"], timeout=15)
        if proc.returncode != 0:
            return {"status": "unreachable", "http_status": None, "error": proc.stderr.strip()[:200]}
        try:
            body = json.loads(proc.stdout)
            return {
                "status": body.get("status", "unknown"),
                "http_status": 200,
                "checks": body.get("checks", {}),
            }
        except json.JSONDecodeError:
            return {"status": "unknown", "http_status": 200, "raw": proc.stdout[:200]}
    except subprocess.TimeoutExpired:
        return {"status": "unreachable", "http_status": None, "error": "timeout"}
    except Exception as exc:
        return {"status": "unreachable", "http_status": None, "error": str(exc)[:200]}


def _mcp_session_curl(port: int, tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Build a shell script that performs a full MCP Streamable HTTP session.

    MCP SDK v1.26+ requires: initialize → notifications/initialized → tools/call.
    Responses are SSE streams; we extract the JSON-RPC result from the data: lines.
    """
    call_payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": tool_args},
    }).replace("'", "'\\''")

    # Shell script that runs the 3-step handshake and extracts the result.
    # Headers are inlined in each curl call to avoid shell quoting issues.
    return f"""\
set -e
BASE="http://localhost:{port}/mcp"
CT="Content-Type: application/json"
AC="Accept: application/json, text/event-stream"

# Step 1: initialize — capture session ID from response header
INIT_RESP=$(curl -sS --max-time 10 -D /dev/stderr -X POST -H "$CT" -H "$AC" \
  -d '{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2024-11-05","capabilities":{{}},"clientInfo":{{"name":"fleet-health","version":"0.1"}}}}}}' \
  "$BASE" 2>&1 1>/dev/null || true)
SID=$(echo "$INIT_RESP" | grep -i 'mcp-session-id' | head -1 | sed 's/.*: *//' | tr -d '\\r\\n')

if [ -z "$SID" ]; then
  echo '{{"ok":false,"error":"no session id from initialize"}}'
  exit 0
fi

# Step 2: notifications/initialized
curl -sS --max-time 5 -X POST -H "$CT" -H "$AC" -H "Mcp-Session-Id: $SID" \
  -d '{{"jsonrpc":"2.0","method":"notifications/initialized"}}' \
  "$BASE" >/dev/null 2>&1 || true

# Step 3: tools/call — capture SSE data lines
RESULT=$(curl -sS -N --max-time 15 -X POST -H "$CT" -H "$AC" -H "Mcp-Session-Id: $SID" \
  -d '{call_payload}' \
  "$BASE" 2>/dev/null | grep '^data: ' | head -1 | sed 's/^data: //')

if [ -n "$RESULT" ]; then
  echo "$RESULT"
else
  echo '{{"ok":false,"error":"no data in SSE response"}}'
fi
"""


def _check_smoke_test(svc: Dict[str, Any]) -> Dict[str, Any]:
    """Send a real MCP tools/call request.

    For MCP SDK Streamable HTTP services: performs full session handshake
    (initialize → initialized → tools/call) and parses SSE response.
    For custom HTTP services: sends a plain JSON-RPC POST.
    """
    port = svc["port"]
    tool_name = svc["smoke_tool"]
    tool_args = svc["smoke_args"]
    transport = svc.get("mcp_transport", "custom-http")

    if transport == "streamable-http":
        script = _mcp_session_curl(port, tool_name, tool_args)
        try:
            proc = run_shell(script, timeout=50)
            output = proc.stdout.strip()
            if proc.returncode != 0 or not output:
                return {"tool": tool_name, "ok": False, "error": (proc.stderr or "empty response").strip()[:200]}
            try:
                body = json.loads(output)
                if "error" in body and body.get("ok") is False:
                    return {"tool": tool_name, "ok": False, "error": body["error"][:200]}
                ok = "result" in body
                return {"tool": tool_name, "ok": ok, "result_preview": output[:300]}
            except json.JSONDecodeError:
                return {"tool": tool_name, "ok": False, "error": f"bad json: {output[:200]}"}
        except subprocess.TimeoutExpired:
            return {"tool": tool_name, "ok": False, "error": "timeout"}
        except Exception as exc:
            return {"tool": tool_name, "ok": False, "error": str(exc)[:200]}
    else:
        # Custom HTTP: plain JSON-RPC POST
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": tool_args},
        })
        try:
            proc = run_cmd(
                ["curl", "-fsS", "--max-time", "15",
                 "-H", "Content-Type: application/json",
                 "-X", "POST",
                 "-d", payload,
                 f"http://localhost:{port}/mcp"],
                timeout=25,
            )
            if proc.returncode != 0:
                return {"tool": tool_name, "ok": False, "error": proc.stderr.strip()[:200]}
            ok = "result" in proc.stdout and "error" not in proc.stdout[:100]
            preview = proc.stdout[:300] if ok else proc.stdout[:200]
            return {"tool": tool_name, "ok": ok, "result_preview": preview}
        except subprocess.TimeoutExpired:
            return {"tool": tool_name, "ok": False, "error": "timeout"}
        except Exception as exc:
            return {"tool": tool_name, "ok": False, "error": str(exc)[:200]}


def _check_local(svc: Dict[str, Any]) -> Dict[str, Any]:
    """Run all local checks for a service (short-circuits on critical failure)."""
    result: Dict[str, Any] = {}

    container = _check_container(svc)
    result["container"] = container
    if not container.get("running"):
        return result

    health = _check_health_endpoint(svc)
    result["health_endpoint"] = health
    if health.get("status") == "error":
        return result

    smoke = _check_smoke_test(svc)
    result["smoke_test"] = smoke

    return result


# ── Tunnel checks (Cloudflare HTTPS) ─────────────────────────────────

def _check_tunnel_health(svc: Dict[str, Any]) -> Dict[str, Any]:
    """Probe health endpoint via Cloudflare tunnel."""
    hostname = svc["hostname"]
    try:
        proc = run_cmd(
            ["curl", "-fsS", "--max-time", "10", f"https://{hostname}/health"],
            timeout=15,
        )
        if proc.returncode != 0:
            return {"ok": False, "status_code": None, "error": proc.stderr.strip()[:200]}
        try:
            body = json.loads(proc.stdout)
            return {"ok": True, "status_code": 200, "status": body.get("status", "unknown")}
        except json.JSONDecodeError:
            return {"ok": True, "status_code": 200, "raw": proc.stdout[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "status_code": None, "error": "timeout"}
    except Exception as exc:
        return {"ok": False, "status_code": None, "error": str(exc)[:200]}


def _check_tunnel_mcp(svc: Dict[str, Any]) -> Dict[str, Any]:
    """Probe MCP endpoint via Cloudflare tunnel (checks reachability).

    Sends proper headers so MCP SDK services don't reject with 406.
    Any HTTP response (even 400/422) proves the tunnel is connected.
    """
    hostname = svc["hostname"]
    try:
        proc = run_cmd(
            [
                "curl", "-sS", "--max-time", "10",
                "-X", "POST",
                "-H", "Content-Type: application/json",
                "-H", "Accept: application/json, text/event-stream",
                "-d", "{}",
                "-o", "/dev/null",
                "-w", "%{http_code}",
                f"https://{hostname}/mcp",
            ],
            timeout=15,
        )
        status_code = int(proc.stdout.strip()) if proc.stdout.strip().isdigit() else 0
        return {"ok": status_code > 0, "status_code": status_code}
    except subprocess.TimeoutExpired:
        return {"ok": False, "status_code": None, "error": "timeout"}
    except Exception as exc:
        return {"ok": False, "status_code": None, "error": str(exc)[:200]}


def _check_tunnel(svc: Dict[str, Any]) -> Dict[str, Any]:
    """Run all tunnel checks for a service."""
    return {
        "health_probe": _check_tunnel_health(svc),
        "mcp_probe": _check_tunnel_mcp(svc),
    }


# ── Status aggregation ────────────────────────────────────────────────

def _derive_service_status(local: Optional[Dict], tunnel: Optional[Dict]) -> str:
    """Derive overall status for a single service from local and tunnel results."""
    statuses: List[str] = []

    if local:
        container = local.get("container", {})
        if not container.get("running"):
            return "error"
        health = local.get("health_endpoint", {})
        h_status = health.get("status", "unknown")
        if h_status == "error" or h_status == "unreachable":
            return "error"
        if h_status == "degraded":
            statuses.append("degraded")
        smoke = local.get("smoke_test", {})
        if smoke and not smoke.get("ok"):
            statuses.append("degraded")

    if tunnel:
        health_probe = tunnel.get("health_probe", {})
        if not health_probe.get("ok"):
            statuses.append("degraded")
        mcp_probe = tunnel.get("mcp_probe", {})
        if not mcp_probe.get("ok"):
            statuses.append("degraded")

    if "degraded" in statuses:
        return "degraded"
    return "ok"


def _derive_fleet_status(service_results: List[Dict[str, Any]]) -> str:
    """Aggregate fleet status from individual service statuses."""
    statuses = [s["status"] for s in service_results]
    if any(s == "error" for s in statuses):
        return "error"
    if any(s == "degraded" for s in statuses):
        return "degraded"
    return "ok"


# ── Entry point ───────────────────────────────────────────────────────

def check_fleet(
    *,
    scope: str = "full",
    services: Optional[List[str]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Verify health of all MCP services across local and tunnel surfaces.

    Args:
        scope: 'local', 'tunnel', or 'full' (both).
        services: Specific service names to check. If None, checks all.

    Returns:
        Fleet health report with per-service status and check details.

    Raises:
        DependencyError: If docker or curl not found in PATH.
    """
    if scope in ("local", "full") and not shutil.which("docker"):
        raise DependencyError("docker not found in PATH")
    if not shutil.which("curl"):
        raise DependencyError("curl not found in PATH")

    registry = SERVICES
    if services:
        filter_set = set(services)
        registry = [s for s in registry if s["name"] in filter_set]

    results: List[Dict[str, Any]] = []
    for svc in registry:
        entry: Dict[str, Any] = {"name": svc["name"]}

        local_result = None
        tunnel_result = None

        if scope in ("local", "full"):
            local_result = _check_local(svc)
            entry["local"] = local_result

        if scope in ("tunnel", "full"):
            tunnel_result = _check_tunnel(svc)
            entry["tunnel"] = tunnel_result

        entry["status"] = _derive_service_status(local_result, tunnel_result)
        results.append(entry)

    return {
        "fleet_status": _derive_fleet_status(results),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "services": results,
    }
