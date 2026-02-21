# github.push_ghcr

Build a Docker image for a specified platform and push it to GitHub Container Registry (GHCR).

## Capability ID

`github.push_ghcr`

## Lifecycle State

Experimental -- migrated from the `ghcr-push` skill script.

## Inputs

| Parameter    | Type     | Required | Default        | Description                                      |
|-------------|----------|----------|----------------|--------------------------------------------------|
| `repo`      | string   | yes      |                | GitHub repo in `owner/name` format               |
| `context`   | string   | yes      |                | Docker build context path                        |
| `dockerfile`| string   | no       | `Dockerfile`   | Path to the Dockerfile                           |
| `platform`  | string   | no       | `linux/arm64`  | Target platform for the build                    |
| `tags`      | string[] | no       | `["latest"]`   | Image tags to apply                              |
| `dry_run`   | boolean  | no       | `false`        | Return the command without executing it          |

## Output

A dict with the following keys:

- `image` -- full GHCR image path (`ghcr.io/<repo>`)
- `tags` -- tags applied
- `platform` -- target platform used
- `action` -- one of `dry_run`, `pushed`
- `docker_command` -- (dry_run only) the full command array

## Errors

- `DependencyError` -- `docker` binary not found in PATH
- `BuildPushError` -- `docker buildx build --push` exited with a non-zero code

## Side Effects

Builds a Docker image via `docker buildx` and pushes it to GHCR. Requires prior authentication to GHCR (e.g. via `docker login ghcr.io`).

## Example

```python
from capabilities.github_push_ghcr.implementation import push_ghcr

result = ghcr_push(
    repo="matthewdart/myapp",
    context=".",
    platform="linux/arm64",
    tags=["latest", "v1.2.3"],
)
print(result)
# {"image": "ghcr.io/matthewdart/myapp", "tags": ["latest", "v1.2.3"], "platform": "linux/arm64", "action": "pushed"}
```
