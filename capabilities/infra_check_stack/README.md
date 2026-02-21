# infra.check_stack

Check Docker Compose service status on a remote host via SSH.

## Usage

```python
from capabilities.infra_check_stack.implementation import check_stack

result = check_stack(
    host="user@myserver",
    compose_dir="/opt/myapp",
    services=["web", "db"],  # optional; omit to query all services
)
```

## Inputs

| Parameter     | Type           | Required | Description                                      |
|---------------|----------------|----------|--------------------------------------------------|
| `host`        | `str`          | yes      | SSH host target (e.g. `user@hostname` or alias). |
| `compose_dir` | `str`          | yes      | Absolute path to the compose directory on host.  |
| `services`    | `list[str]`    | no       | Specific service names to query. Default: all.   |

## Output

On success:

```json
{
  "host": "user@myserver",
  "compose_dir": "/opt/myapp",
  "service_count": 2,
  "services": [
    {
      "name": "myapp-web-1",
      "service": "web",
      "status": "running",
      "health": "healthy",
      "ports": "0.0.0.0:8080->80/tcp",
      "image": "nginx:latest"
    }
  ]
}
```

On remote command failure:

```json
{
  "host": "user@myserver",
  "compose_dir": "/opt/myapp",
  "error": "remote command failed",
  "exit_code": 1
}
```

## Errors

| Code               | Description                                     |
|--------------------|-------------------------------------------------|
| `dependency_error` | `ssh` binary not found in PATH.                 |
| `ssh_error`        | SSH connection or remote command execution failed. |

## Side Effects

Runs a read-only `docker compose ps` command on the remote host via SSH. No containers are started, stopped, or modified.
