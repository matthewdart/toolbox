# infra.deploy_compose

## Description

Deploy Docker Compose services on a remote host via SSH. Connects to the target host, pulls the latest images, and optionally brings services up with `docker compose up -d`.

## Non-goals

- Managing Docker Compose files or configuration
- Building images locally or remotely
- Managing SSH keys or authentication
- Orchestrating multi-host deployments

## Deterministic behavior

Given the same host, compose directory, and service list, the capability executes the same SSH command sequence. The outcome depends on remote state (image registry, running containers) and is therefore not fully deterministic.
