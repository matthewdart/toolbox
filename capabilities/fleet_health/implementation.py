"""Core capability: verify health of all MCP services across local and tunnel surfaces."""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


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
    },
    {
        "name": "health-ledger",
        "compose_dir": "/opt/health-ledger",
        "port": 8765,
        "smoke_tool": "list_assets",
        "smoke_args": {},
        "hostname": "health-ledger.matthewdart.name",
    },
    {
        "name": "archi-mcp-bridge",
        "compose_dir": "/opt/archi-mcp-bridge",
        "port": 8767,
        "smoke_tool": "jarchi_catalog",
        "smoke_args": {},
        "hostname": "archi-mcp-bridge.matthewdart.name",
    },
]


# ── SSH helpers ───────────────────────────────────────────────────────

def _run_ssh(host: str, remote_cmd: str, timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={timeout}", host, remote_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=timeout + 10,
    )


def _run_local_cmd(cmd: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=timeout,
    )


# ── Local checks (SSH to VM) ─────────────────────────────────────────

def _check_container(host: str, svc: Dict[str, Any]) -> Dict[str, Any]:
    """Check container status via docker compose ps."""
    try:
        proc = _run_ssh(host, f"cd {svc['compose_dir']} && docker compose ps --format json")
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
        return {"running": False, "error": "ssh timeout"}
    except Exception as exc:
        return {"running": False, "error": str(exc)[:200]}


def _check_health_endpoint(host: str, svc: Dict[str, Any]) -> Dict[str, Any]:
    """Probe localhost:<port>/health via SSH."""
    port = svc["port"]
    try:
        proc = _run_ssh(host, f"curl -fsS --max-time 10 http://localhost:{port}/health")
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


def _check_smoke_test(host: str, svc: Dict[str, Any]) -> Dict[str, Any]:
    """Send a real MCP tools/call JSON-RPC request via SSH curl."""
    port = svc["port"]
    tool_name = svc["smoke_tool"]
    tool_args = svc["smoke_args"]

    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": tool_args},
    })

    # Escape single quotes in payload for shell
    escaped = payload.replace("'", "'\\''")
    curl_cmd = (
        f"curl -fsS --max-time 15 "
        f"-H 'Content-Type: application/json' "
        f"-X POST "
        f"-d '{escaped}' "
        f"http://localhost:{port}/mcp"
    )

    try:
        proc = _run_ssh(host, curl_cmd, timeout=25)
        if proc.returncode != 0:
            return {"tool": tool_name, "ok": False, "error": proc.stderr.strip()[:200]}
        # MCP streaming responses may have multiple JSON objects; check for any success
        ok = "result" in proc.stdout and "error" not in proc.stdout[:100]
        preview = proc.stdout[:300] if ok else proc.stdout[:200]
        return {"tool": tool_name, "ok": ok, "result_preview": preview}
    except subprocess.TimeoutExpired:
        return {"tool": tool_name, "ok": False, "error": "timeout"}
    except Exception as exc:
        return {"tool": tool_name, "ok": False, "error": str(exc)[:200]}


def _check_local(host: str, svc: Dict[str, Any]) -> Dict[str, Any]:
    """Run all local checks for a service (short-circuits on critical failure)."""
    result: Dict[str, Any] = {}

    container = _check_container(host, svc)
    result["container"] = container
    if not container.get("running"):
        return result

    health = _check_health_endpoint(host, svc)
    result["health_endpoint"] = health
    if health.get("status") == "error":
        return result

    smoke = _check_smoke_test(host, svc)
    result["smoke_test"] = smoke

    return result


# ── Tunnel checks (Cloudflare HTTPS) ─────────────────────────────────

def _check_tunnel_health(svc: Dict[str, Any]) -> Dict[str, Any]:
    """Probe health endpoint via Cloudflare tunnel."""
    hostname = svc["hostname"]
    try:
        proc = _run_local_cmd(
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
    """Probe MCP endpoint via Cloudflare tunnel (just checks reachability)."""
    hostname = svc["hostname"]
    try:
        proc = _run_local_cmd(
            [
                "curl", "-sS", "--max-time", "10",
                "-X", "POST",
                "-H", "Content-Type: application/json",
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

def fleet_health(
    *,
    scope: str = "full",
    host: str = "ubuntu@matthews-oracle-instance",
    services: Optional[List[str]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Verify health of all MCP services across local and tunnel surfaces.

    Args:
        scope: 'local', 'tunnel', or 'full' (both).
        host: SSH host target for local checks.
        services: Specific service names to check. If None, checks all.

    Returns:
        Fleet health report with per-service status and check details.

    Raises:
        DependencyError: If ssh or curl not found in PATH.
    """
    if scope in ("local", "full") and not shutil.which("ssh"):
        raise DependencyError("ssh not found in PATH")
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
            local_result = _check_local(host, svc)
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
