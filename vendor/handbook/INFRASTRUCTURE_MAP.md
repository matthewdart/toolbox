# End-to-End Infrastructure Architecture Map

This document provides a comprehensive map of every component, flow, data store, and interaction in the production infrastructure. It covers the full path from code push to running service, and from client request to response.

---

## 1. Physical Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                 │
│                                                                 │
│  Clients (Claude Code, browsers, API consumers)                 │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────────────┐                       │
│  │         CLOUDFLARE EDGE              │                       │
│  │  DNS, TLS termination, Zero Trust,   │                       │
│  │  MCP Portal, Tunnel routing          │                       │
│  └──────────┬───────────────────────────┘                       │
│             │ (outbound tunnels from VM — no inbound ports)     │
└─────────────┼───────────────────────────────────────────────────┘
              │
    ┌─────────▼──────────────────────────────────────────────┐
    │            ORACLE CLOUD ARM VM                          │
    │         matthews-oracle-instance                        │
    │         Ubuntu 22.04.5 LTS (aarch64)                   │
    │                                                        │
    │  ┌─────────────────────────────────────────────────┐   │
    │  │              HOST SERVICES                       │   │
    │  │  tailscaled, cloudflared (systemd), docker, ssh  │   │
    │  └─────────────────────────────────────────────────┘   │
    │                                                        │
    │  ┌─────────────────────────────────────────────────┐   │
    │  │              DOCKER ENGINE                       │   │
    │  │                                                  │   │
    │  │  ┌──────────────────────────────────────────┐   │   │
    │  │  │  remarkable-pipeline  (host network)      │   │   │
    │  │  │  remarkable-pipeline-tunnel (host network) │   │   │
    │  │  └──────────────────────────────────────────┘   │   │
    │  │                                                  │   │
    │  │  ┌──────────────────────────────────────────┐   │   │
    │  │  │  health-ledger  (bridge: health-ledger_  │   │   │
    │  │  │                         default)          │   │   │
    │  │  │  health-ledger-tunnel (shares health-     │   │   │
    │  │  │                        ledger network)    │   │   │
    │  │  └──────────────────────────────────────────┘   │   │
    │  │                                                  │   │
    │  │  ┌──────────────────────────────────────────┐   │   │
    │  │  │  archi-mcp-bridge (bridge: archi-mcp-    │   │   │
    │  │  │                     bridge_default)       │   │   │
    │  │  │  archi-mcp-bridge-tunnel (shares archi-   │   │   │
    │  │  │                    mcp-bridge network)    │   │   │
    │  │  └──────────────────────────────────────────┘   │   │
    │  │                                                  │   │
    │  └─────────────────────────────────────────────────┘   │
    │                                                        │
    │  ┌──────────────────────────────┐                      │
    │  │   TAILSCALE MESH (100.x.x.x) │                     │
    │  │   ◄──────────────────────────►│                     │
    │  │   matthews-macbook-air         │                     │
    │  │   matthews-remarkable          │                     │
    │  └──────────────────────────────┘                      │
    └────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────┐
    │                     GITHUB                              │
    │  Repos, Actions CI/CD, GHCR image registry             │
    └────────────────────────────────────────────────────────┘
```

---

## 2. Cloudflare — All Components

### 2.1 DNS

All public hostnames live under `matthewdart.name` (Cloudflare-managed zone). Each MCP service gets a subdomain:

| Hostname | Routes to | Status |
|---|---|---|
| `remarkable-pipeline-mcp.matthewdart.name` | remarkable-pipeline-mcp (port 8766) | Active |
| `remarkable-mcp.matthewdart.name` | remarkable-pipeline-mcp (port 8766) | Active (alias) |
| `health-ledger.matthewdart.name` | health-ledger MCP (port 8765) | Active |
| `archi-mcp-bridge.matthewdart.name` | archi-mcp-bridge (port 3177) | Active |
| `pptx-mcp-bridge.matthewdart.name` | pptx-mcp-bridge (port 8769) | Not deployed |

DNS records are CNAME entries pointing to Cloudflare Tunnel UUIDs. No A records — the VM has no public IP exposure.

### 2.2 Tunnels

Six tunnels are registered in Cloudflare. Each tunnel maintains persistent outbound connections from the VM to the Cloudflare edge — no inbound firewall ports required.

| Tunnel name | Created | Connections | Role |
|---|---|---|---|
| `remarkable-mcp` | 2026-02-08 | 8 active | Per-service sidecar for remarkable-pipeline |
| `health-ledger-sql-gateway` | 2026-01-22 | 4 active | Per-service sidecar for health-ledger |
| `archi-mcp-bridge` | 2026-01-25 | 4 active | Per-service sidecar for archi-mcp-bridge |
| `matthews-oracle-instance` | 2026-01-09 | 4 active | Host-level systemd service (see §2.4) |
| `pptx-mcp-bridge` | 2026-02-01 | 0 | Created but never deployed |
| `jellyfin-matthews-compute-stick` | 2023-08-07 | 0 | Legacy — different host, inactive |

Each per-service tunnel has its hostname routing configured in the **Cloudflare dashboard** (not in local config files). A `TUNNEL_TOKEN` is generated from the dashboard and injected into the container's `.env` file as `CF_TUNNEL_TOKEN`.

### 2.3 MCP Portal (Zero Trust)

The Cloudflare MCP Portal aggregates all MCP servers behind a single endpoint URL. Configured in Cloudflare One → Access → AI Controls.

- **Portal URL**: Single endpoint that Claude Code (and other MCP clients) connects to
- **Per-service registration**: Each MCP server is registered in the portal with access policies
- **Portal assignment**: Servers must be **explicitly assigned** to a portal after registration — adding a server does not auto-assign it to any portal
- **Access Applications**: Each registered MCP server gets an auto-created Access Application (`type: mcp`) with access policies
- **Access control**: Zero Trust policies (identity, device posture) applied at the portal layer
- Clients never connect directly to per-service tunnel URLs in production

See [toolbox docs/mcp-portal-pattern.md](https://github.com/matthewdart/toolbox/blob/main/docs/mcp-portal-pattern.md) for the full 5-layer setup checklist and common failure modes.

### 2.4 Host-Level Cloudflared (systemd)

A separate `cloudflared` instance runs on the VM host as a systemd service (not in Docker). This is the `matthews-oracle-instance` tunnel with 4 active connections.

**Role**: Provides general-purpose tunnel access to the VM itself. Its routing rules are configured in the Cloudflare dashboard separately from the per-service tunnels.

**Relationship to per-service tunnels**: Independent. The host tunnel and per-service container tunnels are separate Cloudflare tunnels with separate tokens, separate routing, and separate lifecycles.

---

## 3. Oracle Cloud ARM VM

### 3.1 Host Identity

| Property | Value |
|---|---|
| Hostname | `matthews-oracle-instance` |
| OS | Ubuntu 22.04.5 LTS |
| Architecture | aarch64 (ARM64) |
| Kernel | 6.8.0-1041-oracle |
| Docker | 29.2.1 |
| Docker Compose | v5.0.2 |
| Tailscale IP | 100.82.193.89 |

### 3.2 Host Services

Four system services run directly on the VM host (not in containers):

| Service | Role | Port(s) |
|---|---|---|
| **tailscaled** | Tailscale mesh VPN daemon. Provides private connectivity to other devices. | 44179 (Tailscale coordination) |
| **cloudflared** | Host-level Cloudflare tunnel (`matthews-oracle-instance`). | 20241-20244 (metrics/internal) |
| **dockerd** | Docker engine running all containerised services. | Unix socket |
| **sshd** | SSH access. Used by GitHub Actions deployment and direct access via Tailscale. | 22 |

### 3.3 Directory Structure

```
/opt/
├── remarkable-pipeline/
│   ├── docker-compose.yml
│   ├── .env                    (CF_TUNNEL_TOKEN, REMARKABLE_*)
│   └── data/                   (bind-mounted into container)
│       └── ...                 (174 MB — OCR data, notebook cache)
│
├── health-ledger/
│   ├── docker-compose.yml
│   ├── .env                    (CF_TUNNEL_TOKEN, HEALTH_LEDGER_*, HLSG_API_KEY)
│   └── data/                   (bind-mounted into container)
│       └── ...                 (829 MB — SQLite databases, health exports)
│
├── archi-mcp-bridge/
│   ├── docker-compose.yml
│   ├── .env                    (CF_TUNNEL_TOKEN, ARCHI_MCP_*)
│   └── data/                   (bind-mounted into container)
│       └── ...                 (672 KB — ArchiMate model files)
│
└── mcp/                        (228 KB — legacy, from old central compose model. Inert.)
```

### 3.4 Listening Ports

| Port | Process | Scope |
|---|---|---|
| 22 | sshd | 0.0.0.0 (SSH) |
| 111 | rpcbind | 0.0.0.0 (NFS/RPC — likely OS default) |
| 8462 | (unidentified) | Likely Tailscale-related |
| 20241-20244 | cloudflared | 127.0.0.1 (metrics/internal) |
| 44179 | tailscaled | 0.0.0.0 (Tailscale coordination) |

Note: Container ports (8766, 8765, 8787, 3177) are either host-networked (remarkable-pipeline) or bridge-networked (health-ledger, archi-mcp-bridge) and only exposed to localhost or their respective cloudflared sidecars.

---

## 4. Docker Containers — Detailed

### 4.1 remarkable-pipeline

**Compose project**: `/opt/remarkable-pipeline/`
**Network mode**: `host` (both app and cloudflared use the host network stack)

| Container | Image | Role |
|---|---|---|
| `remarkable-pipeline-mcp` | `ghcr.io/matthewdart/remarkable-pipeline-mcp:latest` | MCP server — reMarkable tablet data pipeline (ingestion, PDF rendering, OCR, search) |
| `remarkable-pipeline-tunnel` | `cloudflare/cloudflared:latest` | Cloudflare tunnel sidecar — routes `remarkable-mcp.matthewdart.name` to port 8766 |

**Why host networking**: The app needs to reach the reMarkable tablet via the host's Tailscale interface (`matthews-remarkable` at 100.93.180.128 via SSH).

**Environment variables**:
- `CF_TUNNEL_TOKEN` — Cloudflare tunnel token for `remarkable-mcp` tunnel
- `REMARKABLE_TRANSPORT=ssh` — connection method to reMarkable device
- `REMARKABLE_HOST=matthews-remarkable` — Tailscale hostname of reMarkable

**Data stored** (`./data:/app/data`):
- Notebook metadata and page cache
- Rendered PNG images of pages
- OCR text output
- Pipeline state (last sync timestamps)
- Total: ~174 MB

**Port**: 8766 (MCP streamable HTTP) — bound to host network

---

### 4.2 health-ledger

**Compose project**: `/opt/health-ledger/`
**Network mode**: Bridge (`health-ledger_default`)

| Container | Image | Role |
|---|---|---|
| `health-ledger` | `ghcr.io/matthewdart/health-ledger:latest` | MCP + REST server — Apple Health data ingestion, SQL analytics |
| `health-ledger-tunnel` | `cloudflare/cloudflared:latest` | Cloudflare tunnel sidecar — shares app's network namespace |

**Networking detail**: The cloudflared container uses `network_mode: "service:health-ledger"`, which makes it share the `health-ledger` container's network namespace. This means cloudflared can reach the app on `localhost:8765` and `localhost:8787` without Docker network routing.

**Environment variables**:
- `CF_TUNNEL_TOKEN` — Cloudflare tunnel token for `health-ledger-sql-gateway` tunnel
- `HEALTH_LEDGER_TRANSPORT=mcp` — server transport mode
- `HLSG_API_KEY` — API authentication key

**Data stored** (`./data:/app/data`):
- SQLite databases with ingested Apple Health data
- Processed health export files
- Total: ~829 MB

**Ports**:
- 8765 (MCP streamable HTTP) — `127.0.0.1:8765:8765`
- 8787 (REST/FastAPI) — `127.0.0.1:8787:8787`

**Cloudflare route**: `health-ledger.matthewdart.name` → port 8765

---

### 4.3 archi-mcp-bridge

**Compose project**: `/opt/archi-mcp-bridge/`
**Network mode**: Bridge (`archi-mcp-bridge_default`)

| Container | Image | Role |
|---|---|---|
| `archi-mcp-bridge` | `ghcr.io/matthewdart/archi-mcp-bridge:latest` | MCP server — ArchiMate modelling bridge via headless jArchi |
| `archi-mcp-bridge-tunnel` | `cloudflare/cloudflared:latest` | Cloudflare tunnel sidecar — shares app's network namespace |

**Networking detail**: Same shared-namespace pattern as health-ledger. Cloudflared uses `network_mode: "service:archi-mcp-bridge"`.

**Environment variables**:
- `CF_TUNNEL_TOKEN` — Cloudflare tunnel token for `archi-mcp-bridge` tunnel
- `ARCHI_MCP_API_KEY` — API authentication key
- `ARCHI_MCP_FIXTURE_MODEL` — path to default ArchiMate model file
- `ARCHI_MCP_HOST` — binding host
- `ARCHI_MCP_PORT` — binding port
- `ARCHI_MCP_AUTH_ENABLED` — whether auth is enforced
- `ARCHI_MCP_WORKSPACE` — Archi workspace path

**Data stored** (`./data:/data`):
- ArchiMate `.archimate` model files
- Total: ~672 KB

**Port**: 3177 (HTTP) — `127.0.0.1:3177:3177`

**Cloudflare route**: `archi-mcp.matthewdart.name` → port 3177

**Special build note**: The Dockerfile is complex multi-stage — runs an ARM64 JVM (Eclipse Temurin 21) with x86_64 multiarch support via QEMU/binfmt for the Archi binary (which is only distributed as x86_64).

---

### 4.4 pptx-mcp-bridge (not deployed)

No directory at `/opt/pptx-mcp-bridge/`. A Cloudflare tunnel exists (`pptx-mcp-bridge`, created 2026-02-01) but has zero connections. The repo exists on GitHub with a Dockerfile but is not currently deployed to the VM.

---

## 5. Docker Networking

```
┌─────────────────────────────────────────────────────────────┐
│  HOST NETWORK (network_mode: host)                          │
│                                                             │
│   remarkable-pipeline-mcp (:8766)                           │
│   remarkable-pipeline-tunnel                                │
│   (can reach Tailscale IPs: 100.x.x.x)                     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  BRIDGE: health-ledger_default                              │
│                                                             │
│   health-ledger (:8765, :8787)                              │
│   health-ledger-tunnel (shares health-ledger namespace)     │
│   ├── localhost:8765 → MCP                                  │
│   └── localhost:8787 → REST API                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  BRIDGE: archi-mcp-bridge_default                           │
│                                                             │
│   archi-mcp-bridge (:3177)                                  │
│   archi-mcp-bridge-tunnel (shares archi-mcp-bridge ns)      │
│   └── localhost:3177 → HTTP                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘

No cross-service Docker networking. Services are fully isolated.
Inter-service communication (if needed) goes through Tailscale.
```

---

## 6. Tailscale Mesh Network

### 6.1 Active Devices

| Device | Tailscale IP | OS | Role |
|---|---|---|---|
| `matthews-oracle-instance` | 100.82.193.89 | Linux (ARM64) | Production VM — hosts all services |
| `matthews-macbook-air` | 100.98.196.19 | macOS | Development machine — direct connection to VM |
| `matthews-remarkable` | 100.93.180.128 | Linux | reMarkable tablet — data source for remarkable-pipeline |

### 6.2 Inactive / Offline Devices

| Device | Tailscale IP | Last seen | Notes |
|---|---|---|---|
| `win-npl6dtjs46k` | 100.71.133.70 | 6 days ago | Windows machine |
| Various Apple devices | 100.x.x.x | Weeks-months | Apple TV, iPads, iPhones, compute stick |

### 6.3 Tailscale Roles in the Infrastructure

1. **GitHub Actions → VM deployment**: The `deploy-stack.yml` workflow joins Tailscale (ephemeral key), then SSHes to `matthews-oracle-instance` to deploy
2. **remarkable-pipeline → reMarkable tablet**: SSH over Tailscale to `matthews-remarkable` for data ingestion
3. **Developer SSH access**: `matthews-macbook-air` → `matthews-oracle-instance` for debugging/administration
4. **Offers exit node**: The Oracle VM is configured as a Tailscale exit node

---

## 7. GitHub — All Components

### 7.1 GHCR (Container Registry)

All container images are stored in GitHub Container Registry under `ghcr.io/matthewdart/`:

| Image | Built from | Architecture |
|---|---|---|
| `remarkable-pipeline-mcp:latest` | `remarkable-pipeline/Dockerfile` | `linux/arm64` |
| `health-ledger:latest` | `health-ledger/Dockerfile` | `linux/arm64` |
| `archi-mcp-bridge:latest` | `archi-mcp-bridge/Dockerfile` | `linux/arm64` |
| `pptx-mcp-bridge:latest` | `pptx-mcp-bridge/Dockerfile` | `linux/arm64` |

All images are built for `linux/arm64` only — matching the Oracle ARM VM.

### 7.2 GitHub Actions — Reusable Workflows (in toolbox)

Two reusable workflows in `matthewdart/toolbox/.github/workflows/`:

#### `build-arm-image.yml`
Builds and pushes ARM64 Docker images to GHCR.

```
Trigger: workflow_call from project repos
Steps:
  1. Checkout calling repo
  2. Set up QEMU (ARM64 emulation on x86 runner)
  3. Set up Docker Buildx
  4. Login to GHCR (GITHUB_TOKEN)
  5. Extract Docker metadata (tags, labels)
  6. Build and push (platform: linux/arm64, GHA cache)
```

#### `deploy-stack.yml`
Deploys a service to the Oracle VM via Tailscale SSH.

```
Trigger: workflow_call from project repos
Steps:
  1. Checkout calling repo
  2. Connect to Tailscale (ephemeral auth key)
  3. SSH: mkdir -p /opt/<service>/ on VM
  4. SCP: docker-compose.yml → /opt/<service>/docker-compose.yml
  5. SSH: cd /opt/<service>/ && docker compose pull && docker compose up -d
  6. SSH: docker compose ps (verify)
```

### 7.3 Per-Repo Workflows

| Repo | Workflow | Trigger | Jobs |
|---|---|---|---|
| `remarkable-pipeline` | `ci.yml` | PR to main | pytest |
| `remarkable-pipeline` | `docker.yml` | Push to main | build-arm-image → deploy-stack |
| `remarkable-pipeline` | `codex-issue-assigned.yml` | Issue labeled | Codex research → plan → implement → draft PR |
| `health-ledger` | `docker.yml` | Push to main | build-arm-image → deploy-stack |
| `archi-mcp-bridge` | `docker.yml` | Push to main | build-arm-image → deploy-stack |
| `obsidian-copilot` | `node.js.yml` | Push/PR | npm ci → lint → build → test → integration |
| `obsidian-atlas` | `node.js.yml` | Push/PR | npm ci → lint → build → test → integration |
| `mcp-infra` | `deploy.yml` | Manual/dispatch | deploy-stack (to /opt/mcp — **obsolete**) |

### 7.4 Secrets (GitHub Actions)

| Secret | Used by | Purpose |
|---|---|---|
| `TAILSCALE_AUTHKEY` | deploy-stack.yml | Ephemeral Tailscale key for CI runner to SSH to VM |
| `GITHUB_TOKEN` | build-arm-image.yml | Auto-provided; authenticates to GHCR |

---

## 8. Data Flow: Code Push to Running Service

```
Developer pushes to main
       │
       ▼
GitHub Actions triggers docker.yml
       │
       ├──► Job 1: build-arm-image
       │         │
       │         ├── Checkout code
       │         ├── QEMU setup (ARM emulation)
       │         ├── Docker Buildx
       │         ├── Build linux/arm64 image
       │         └── Push to ghcr.io/matthewdart/<image>:latest
       │
       └──► Job 2: deploy-stack (depends on Job 1)
                 │
                 ├── Checkout code (for docker-compose.yml)
                 ├── Join Tailscale mesh (ephemeral key)
                 ├── SSH to matthews-oracle-instance:
                 │     mkdir -p /opt/<service>/
                 ├── SCP docker-compose.yml to /opt/<service>/
                 ├── SSH: docker compose pull
                 │     (pulls new image from GHCR)
                 ├── SSH: docker compose up -d
                 │     (recreates containers with new image)
                 └── SSH: docker compose ps
                       (verify containers are running)
```

---

## 9. Data Flow: Client Request to Service Response

```
Client (e.g. Claude Code with MCP)
       │
       │  HTTPS request to *.matthewdart.name
       ▼
Cloudflare Edge
       │
       ├── DNS resolution (CNAME → tunnel UUID)
       ├── TLS termination
       ├── Zero Trust policy evaluation (MCP Portal)
       │
       ▼
Cloudflare Tunnel (outbound connection from VM)
       │
       │  Per-service tunnel token identifies which tunnel
       │  Dashboard routing maps hostname → origin service
       ▼
cloudflared sidecar container (on VM)
       │
       │  For shared-namespace services:
       │    localhost:<port> → app container
       │  For host-network services:
       │    host network → app listens on port
       ▼
Application container
       │
       ├── Processes request
       ├── Reads/writes to bind-mounted ./data/
       ├── (remarkable-pipeline only) SSHes to reMarkable via Tailscale
       │
       ▼
Response back through tunnel → Cloudflare → Client
```

---

## 10. Data Stores

### 10.1 Persistent Data (Bind Mounts)

| Service | Host path | Container path | Size | Contents |
|---|---|---|---|---|
| remarkable-pipeline | `/opt/remarkable-pipeline/data/` | `/app/data` | 174 MB | Notebook cache, rendered PNGs, OCR text, pipeline state |
| health-ledger | `/opt/health-ledger/data/` | `/app/data` | 829 MB | SQLite databases, ingested Apple Health exports |
| archi-mcp-bridge | `/opt/archi-mcp-bridge/data/` | `/data` | 672 KB | ArchiMate model files (.archimate) |

All data uses bind mounts (not Docker named volumes) for inspectability and direct shell access.

### 10.2 Ephemeral Data

- Docker image layers (~6.4 GB cached, 38 images total, 4 actively used)
- Container logs (Docker default, not persisted to host files)
- Tailscale state (`/var/lib/tailscale/` on host)

### 10.3 Configuration Data

| Location | Contents |
|---|---|
| `/opt/<service>/.env` | Runtime secrets and config (tunnel tokens, API keys, transport settings) |
| `/opt/<service>/docker-compose.yml` | Service composition (SCP'd from repo on each deploy) |
| Cloudflare Dashboard | Tunnel routing rules, DNS records, Zero Trust policies, MCP Portal config |
| GitHub Secrets | `TAILSCALE_AUTHKEY` (per-repo) |

---

## 11. Service Inventory Summary

| # | Component | Type | Location | Network | Purpose |
|---|---|---|---|---|---|
| 1 | tailscaled | Host service | VM | UDP 44179 | Mesh VPN — device connectivity |
| 2 | cloudflared (host) | Host service | VM | 20241-20244 | Host-level Cloudflare tunnel |
| 3 | dockerd | Host service | VM | Unix socket | Container runtime |
| 4 | sshd | Host service | VM | TCP 22 | Remote access and CI deployment |
| 5 | remarkable-pipeline-mcp | Docker container | VM (host net) | TCP 8766 | reMarkable data pipeline MCP server |
| 6 | remarkable-pipeline-tunnel | Docker container | VM (host net) | — | Cloudflare tunnel for remarkable-pipeline |
| 7 | health-ledger | Docker container | VM (bridge) | TCP 8765, 8787 | Health data MCP + REST server |
| 8 | health-ledger-tunnel | Docker container | VM (shared ns) | — | Cloudflare tunnel for health-ledger |
| 9 | archi-mcp-bridge | Docker container | VM (bridge) | TCP 3177 | ArchiMate MCP bridge |
| 10 | archi-mcp-bridge-tunnel | Docker container | VM (shared ns) | — | Cloudflare tunnel for archi-mcp-bridge |
| 11 | Cloudflare Edge | SaaS | Cloudflare | HTTPS 443 | DNS, TLS, Zero Trust, tunnels, MCP Portal |
| 12 | GitHub Actions | SaaS | GitHub | — | CI/CD pipeline |
| 13 | GHCR | SaaS | GitHub | — | Container image registry |

---

## 12. Anomalies and Cleanup Items

| Item | Description | Recommended Action |
|---|---|---|
| Host cloudflared systemd | Separate tunnel (`matthews-oracle-instance`) with 4 active connections. Routing rules unclear. | Audit dashboard routing rules. Determine if still needed or redundant with per-service tunnels. |
| `/opt/mcp/` directory | Legacy 228 KB. From old centralised compose model (mcp-infra). No active compose project. | Delete directory. |
| `mcp-infra` GitHub repo | Contains obsolete central `docker-compose.yml` and deploy workflow targeting `/opt/mcp`. | Delete repo. |
| `pptx-mcp-bridge` tunnel | Registered in Cloudflare (2026-02-01) but never deployed to VM. 0 connections. | Deploy or delete tunnel. |
| `jellyfin-matthews-compute-stick` tunnel | Legacy tunnel from 2023. Different host. 0 connections. | Delete from Cloudflare. |
| 34 unused Docker images | 6.4 GB cached, only 4 actively used. | `docker image prune -a` |
| Port 111 (rpcbind) | Listening on 0.0.0.0. Likely Ubuntu default. Not needed for this infrastructure. | Disable rpcbind service. |

---

## 13. Security Model Summary

| Layer | Mechanism |
|---|---|
| **No public IP ports** | VM has no inbound ports open to the internet. All public access is through Cloudflare Tunnels (outbound connections from VM). |
| **SSH access** | Only via Tailscale mesh (private IPs). GitHub Actions joins Tailscale with ephemeral keys. |
| **Cloudflare Zero Trust** | MCP Portal enforces identity and device posture checks before routing to tunnels. |
| **Per-service isolation** | Each service has its own Docker network. No cross-service Docker networking. |
| **Secrets injection** | Runtime env vars in `.env` files on VM. Never in repos or images. |
| **Image provenance** | All images built by GitHub Actions from repo Dockerfiles, pushed to GHCR with `GITHUB_TOKEN`. |
