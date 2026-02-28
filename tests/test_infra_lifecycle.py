"""Unit tests for container lifecycle capabilities — validates input handling,
shell command construction, and output schemas without requiring Docker.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.dispatch import dispatch

CAPABILITIES_DIR = Path(__file__).resolve().parents[1] / "capabilities"


class InputValidationTests(unittest.TestCase):
    """Verify that name/project validation rejects unsafe characters."""

    def test_spawn_instance_rejects_shell_metacharacters(self):
        result = dispatch("infra.spawn_instance", {
            "template": "browser; rm -rf /",
            "name": "test",
        })
        self.assertFalse(result["ok"])
        self.assertIn("Invalid template name", result["error"]["message"])

    def test_spawn_instance_rejects_name_with_spaces(self):
        result = dispatch("infra.spawn_instance", {
            "template": "browser",
            "name": "my project",
        })
        self.assertFalse(result["ok"])
        self.assertIn("Invalid instance name", result["error"]["message"])

    def test_deploy_stack_rejects_unsafe_stack_name(self):
        result = dispatch("infra.deploy_stack", {
            "stack": "foo && echo pwned",
        })
        self.assertFalse(result["ok"])
        self.assertIn("Invalid stack name", result["error"]["message"])

    def test_destroy_stack_rejects_unsafe_stack_name(self):
        result = dispatch("infra.destroy_stack", {
            "stack": "foo;bar",
        })
        self.assertFalse(result["ok"])
        self.assertIn("Invalid stack name", result["error"]["message"])

    def test_destroy_instance_rejects_unsafe_project_name(self):
        result = dispatch("infra.destroy_instance", {
            "project": "foo | cat /etc/passwd",
        })
        self.assertFalse(result["ok"])
        self.assertIn("Invalid project name", result["error"]["message"])

    def test_list_instances_rejects_unsafe_template(self):
        result = dispatch("infra.list_instances", {
            "template": "foo;bar",
        })
        self.assertFalse(result["ok"])
        self.assertIn("Invalid template filter", result["error"]["message"])

    def test_spawn_instance_accepts_valid_names(self):
        """Valid names should pass validation (will fail at docker, not validation)."""
        result = dispatch("infra.spawn_instance", {
            "template": "claude-mcp-server",
            "name": "my-repo.v2",
        })
        # Should fail with docker not found, not validation
        self.assertFalse(result["ok"])
        self.assertNotIn("Invalid", result["error"]["message"])

    def test_deploy_stack_dry_run(self):
        """dry_run returns the command without executing."""
        result = dispatch("infra.deploy_stack", {
            "stack": "my-service",
            "dry_run": True,
        })
        self.assertTrue(result["ok"])
        inner = result["result"]
        self.assertEqual(inner["action"], "dry_run")
        self.assertEqual(inner["stack"], "my-service")
        self.assertEqual(inner["compose_dir"], "/opt/my-service")
        self.assertIn("command", inner)


class ShellCommandTests(unittest.TestCase):
    """Verify shell commands are constructed safely."""

    def test_spawn_instance_env_passed_to_run_cmd(self):
        """Env vars (including special characters) are passed to run_cmd."""
        from capabilities.infra_spawn_instance.implementation import spawn_instance

        with patch(
            "capabilities.infra_spawn_instance.implementation.run_cmd"
        ) as mock_run, patch(
            "capabilities.infra_spawn_instance.implementation.shutil.which",
            return_value="/usr/bin/docker",
        ):
            mock_run.return_value = MagicMock(
                returncode=0, stdout="", stderr=""
            )
            spawn_instance(
                template="browser",
                name="test",
                env={"REPO": "https://github.com/foo/bar's repo"},
            )
            call_args = mock_run.call_args
            env_kwarg = call_args[1]["env"]
            # NAME is always set, plus caller-provided vars
            self.assertEqual(env_kwarg["NAME"], "test")
            self.assertEqual(env_kwarg["REPO"], "https://github.com/foo/bar's repo")


class DiscoverStacksOutputTests(unittest.TestCase):
    """Test discover_stacks shell script output parsing."""

    def test_parse_stack_output(self):
        from capabilities.infra_discover_stacks.implementation import discover_stacks

        sample_output = (
            '{"name":"health-ledger","has_override":true,"has_env":true,"has_template":false,"status":"running"}\n'
            '{"name":"toolbox","has_override":false,"has_env":false,"has_template":false,"status":"stopped"}\n'
        )

        with patch(
            "capabilities.infra_discover_stacks.implementation.run_shell"
        ) as mock_shell:
            mock_shell.return_value = MagicMock(
                returncode=0, stdout=sample_output, stderr=""
            )
            result = discover_stacks()

        self.assertEqual(result["stack_count"], 2)
        self.assertEqual(result["stacks"][0]["name"], "health-ledger")
        self.assertTrue(result["stacks"][0]["has_override"])
        self.assertEqual(result["stacks"][1]["status"], "stopped")


class DiscoverTemplatesOutputTests(unittest.TestCase):
    """Test discover_templates output parsing."""

    def test_parse_template_output(self):
        from capabilities.infra_discover_templates.implementation import discover_templates

        sample_output = (
            "===TEMPLATE:browser===\n"
            "services:\n"
            "  chrome:\n"
            "    container_name: browser-${NAME:-default}\n"
            "    environment:\n"
            "      - VNC_PORT=${VNC_PORT:-7900}\n"
            "===TEMPLATE:claude-mcp-server===\n"
            "services:\n"
            "  workspace:\n"
            "    container_name: workspace-${NAME}\n"
            "    environment:\n"
            "      - REPO=${REPO:-}\n"
            "      - BRANCH=${BRANCH:-main}\n"
        )

        with patch(
            "capabilities.infra_discover_templates.implementation.run_shell"
        ) as mock_shell:
            mock_shell.return_value = MagicMock(
                returncode=0, stdout=sample_output, stderr=""
            )
            result = discover_templates()

        self.assertEqual(result["template_count"], 2)
        self.assertEqual(result["templates"][0]["name"], "browser")
        self.assertIn("NAME", result["templates"][0]["env_vars"])
        self.assertIn("VNC_PORT", result["templates"][0]["env_vars"])
        self.assertEqual(result["templates"][1]["name"], "claude-mcp-server")
        self.assertIn("REPO", result["templates"][1]["env_vars"])
        self.assertIn("BRANCH", result["templates"][1]["env_vars"])


class ListInstancesParsingTests(unittest.TestCase):
    """Test docker ps JSON parsing and grouping."""

    def test_group_by_project(self):
        from capabilities.infra_list_instances.implementation import (
            _parse_containers,
            _group_by_project,
        )

        sample = [
            {
                "Names": "browser-test-chrome",
                "State": "running",
                "Image": "selenium/standalone-chrome:latest",
                "Labels": "com.docker.compose.project=browser-test,toolbox.managed=true,toolbox.type=browser",
            },
            {
                "Names": "browser-test-mcp",
                "State": "running",
                "Image": "node:22-slim",
                "Labels": "com.docker.compose.project=browser-test,toolbox.managed=true,toolbox.type=browser,mcp.namespace=browser-test",
            },
        ]

        output = "\n".join(json.dumps(c) for c in sample)
        containers = _parse_containers(output)
        instances = _group_by_project(containers)

        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["project_name"], "browser-test")
        self.assertEqual(instances[0]["type"], "browser")
        self.assertEqual(instances[0]["mcp_namespace"], "browser-test")
        self.assertEqual(len(instances[0]["containers"]), 2)


class LabelConsistencyTests(unittest.TestCase):
    """Verify compose template labels match gateway expectations."""

    def _read_yaml_labels(self, path: Path, service: str) -> dict[str, str]:
        """Crude label extraction from compose YAML (no full parser needed)."""
        import re
        content = path.read_text()
        labels: dict[str, str] = {}
        in_service = False
        in_labels = False
        for line in content.splitlines():
            stripped = line.strip()
            # Simple YAML service detection
            if re.match(rf"^  {service}:", line):
                in_service = True
                in_labels = False
                continue
            if in_service and re.match(r"^  \w", line) and not line.startswith(f"  {service}"):
                in_service = False
                in_labels = False
                continue
            if in_service and stripped == "labels:":
                in_labels = True
                continue
            if in_labels and stripped and not stripped.startswith("#"):
                if ":" in stripped:
                    key, _, val = stripped.partition(":")
                    labels[key.strip()] = val.strip().strip("'\"")
                else:
                    in_labels = False
        return labels

    def test_claude_mcp_template_has_lifecycle(self):
        path = Path(__file__).resolve().parents[1] / ".." / "claude-mcp-server" / "docker-compose.template.yml"
        if not path.exists():
            self.skipTest("claude-mcp-server repo not found")
        labels = self._read_yaml_labels(path, "workspace")
        self.assertEqual(labels.get("mcp.lifecycle"), "persistent",
                         "claude-mcp-server template must set mcp.lifecycle: persistent")
        self.assertEqual(labels.get("toolbox.managed"), "true")
        self.assertIn("mcp.namespace", labels)
        self.assertIn("mcp.stdio.container", labels)
        self.assertIn("mcp.stdio.command", labels)

    def test_browser_template_has_lifecycle(self):
        path = Path(__file__).resolve().parents[1] / "compose" / "browser" / "docker-compose.template.yml"
        labels = self._read_yaml_labels(path, "playwright-mcp")
        self.assertEqual(labels.get("mcp.lifecycle"), "persistent",
                         "browser template playwright-mcp must set mcp.lifecycle: persistent")
        self.assertEqual(labels.get("toolbox.managed"), "true")
        self.assertIn("mcp.namespace", labels)
        self.assertIn("mcp.stdio.container", labels)
        self.assertIn("mcp.stdio.command", labels)


if __name__ == "__main__":
    unittest.main()
