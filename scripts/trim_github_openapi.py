#!/usr/bin/env python3
import argparse
import sys
import urllib.request
from collections import deque, defaultdict
from pathlib import Path

import yaml

UPSTREAM_URL = "https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.yaml"
DEFAULT_OUTPUT = "docs/openapi/github-micro.yaml"
DEFAULT_CACHE = "vendor/github/rest-api-description/api.github.com.yaml"

ALLOWED_PATHS = {
    "/user/repos": {"get"},
    "/repos/{owner}/{repo}": {"get"},
    "/repos/{owner}/{repo}/issues": {"get", "post"},
    "/repos/{owner}/{repo}/issues/{issue_number}": {"get", "patch"},
    "/repos/{owner}/{repo}/issues/{issue_number}/comments": {"get", "post"},
    "/repos/{owner}/{repo}/tags": {"get"},
    "/repos/{owner}/{repo}/contents/{path}": {"get", "put"},
    "/gists": {"post"},
    "/gists/{gist_id}": {"get", "patch"},
}

HTTP_METHODS = {
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    "trace",
}

OPENAPI_TARGET = "3.1.0"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def download_text(url: str) -> str:
    with urllib.request.urlopen(url) as resp:
        return resp.read().decode("utf-8")


def parse_spec(text: str) -> dict:
    return yaml.safe_load(text)


def decode_pointer(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def parse_component_ref(ref: str):
    if not ref.startswith("#/"):
        raise ValueError(f"External or unsupported $ref: {ref}")
    parts = ref.split("/")
    if len(parts) < 4:
        return None
    if parts[1] != "components":
        return None
    section = decode_pointer(parts[2])
    name = decode_pointer(parts[3])
    return section, name


def collect_refs(node, refs):
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            refs.add(ref)
        for value in node.values():
            collect_refs(value, refs)
    elif isinstance(node, list):
        for item in node:
            collect_refs(item, refs)


def collect_security_scheme_names(spec: dict) -> set[str]:
    names = set()
    root_security = spec.get("security") or []
    for entry in root_security:
        if isinstance(entry, dict):
            names.update(entry.keys())
    paths = spec.get("paths") or {}
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for op in path_item.values():
            if not isinstance(op, dict):
                continue
            security = op.get("security") or []
            for entry in security:
                if isinstance(entry, dict):
                    names.update(entry.keys())
    return names


def normalize_openapi_version(spec: dict) -> dict:
    version = str(spec.get("openapi", "")).strip()
    if version != OPENAPI_TARGET:
        spec["openapi"] = OPENAPI_TARGET
    return spec


def sanitize_operation_id(value: str) -> str:
    out = []
    for ch in value:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append("_")
    sanitized = "".join(out)
    if not sanitized or sanitized[0].isdigit():
        sanitized = f"op_{sanitized}"
    return sanitized


def normalize_operation_ids(spec: dict) -> dict:
    used = {}
    paths = spec.get("paths") or {}
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(op, dict):
                continue
            op_id = op.get("operationId")
            if not isinstance(op_id, str):
                continue
            sanitized = sanitize_operation_id(op_id)
            if sanitized != op_id:
                op.setdefault("x-original-operationId", op_id)
            base = sanitized
            counter = 1
            while sanitized in used and used[sanitized] != op:
                counter += 1
                sanitized = f"{base}_{counter}"
            used[sanitized] = op
            op["operationId"] = sanitized
    return spec


def prune_components(spec: dict) -> dict:
    components = spec.get("components") or {}
    refs = set()

    seed = {"paths": spec.get("paths")}
    if "security" in spec:
        seed["security"] = spec["security"]
    collect_refs(seed, refs)

    needed = defaultdict(set)
    queue = deque(refs)
    seen_refs = set()

    while queue:
        ref = queue.popleft()
        if ref in seen_refs:
            continue
        seen_refs.add(ref)
        component_key = parse_component_ref(ref)
        if component_key is None:
            continue
        section, name = component_key
        if name in needed[section]:
            continue
        needed[section].add(name)
        section_map = components.get(section) or {}
        if name not in section_map:
            raise KeyError(f"Dangling $ref: {ref}")
        obj = section_map[name]
        nested_refs = set()
        collect_refs(obj, nested_refs)
        for nested in nested_refs:
            if nested not in seen_refs:
                queue.append(nested)

    security_names = collect_security_scheme_names(spec)
    if security_names:
        needed["securitySchemes"].update(security_names)

    pruned = {}
    for section, entries in components.items():
        if not isinstance(entries, dict):
            continue
        keep = needed.get(section)
        if not keep:
            continue
        kept_entries = {name: entries[name] for name in keep if name in entries}
        if kept_entries:
            pruned[section] = kept_entries

    spec["components"] = pruned
    return spec


def validate_refs(spec: dict) -> None:
    components = spec.get("components") or {}

    refs = set()
    collect_refs(spec, refs)
    for ref in refs:
        if not ref.startswith("#/"):
            raise ValueError(f"External or unsupported $ref: {ref}")
        component_key = parse_component_ref(ref)
        if component_key is None:
            continue
        section, name = component_key
        section_map = components.get(section) or {}
        if name not in section_map:
            raise KeyError(f"Unresolved $ref: {ref}")


def trim_paths(spec: dict) -> dict:
    paths = spec.get("paths") or {}
    missing = [path for path in ALLOWED_PATHS if path not in paths]
    if missing:
        raise KeyError(f"Missing required paths: {', '.join(missing)}")

    trimmed_paths = {}
    for path, allowed_methods in ALLOWED_PATHS.items():
        path_item = paths[path]
        new_item = {}
        for key, value in path_item.items():
            method = key.lower()
            if method in HTTP_METHODS:
                if method in allowed_methods:
                    new_item[key] = value
            else:
                new_item[key] = value
        present_methods = {k.lower() for k in new_item.keys() if k.lower() in HTTP_METHODS}
        if not present_methods:
            raise KeyError(f"No allowed methods found for path {path}")
        trimmed_paths[path] = new_item

    spec["paths"] = trimmed_paths
    return spec




def strip_top_level_extensions(spec: dict) -> dict:
    for key in list(spec.keys()):
        if key.startswith("x-"):
            spec.pop(key)
    return spec


def normalize_security(spec: dict) -> dict:
    components = spec.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
    }
    spec["security"] = [{"BearerAuth": []}]
    return spec


def build_output(spec: dict) -> dict:
    output = {}
    for key in ("openapi", "info", "servers"):
        if key in spec:
            output[key] = spec[key]
    output["paths"] = spec["paths"]
    if spec.get("components"):
        output["components"] = spec["components"]
    if "security" in spec:
        output["security"] = spec["security"]
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Trim GitHub OpenAPI spec for GPT Actions.")
    parser.add_argument("--input", help="Path to local OpenAPI YAML to use instead of downloading.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output YAML path.")
    parser.add_argument("--cache", action="store_true", help="Write downloaded spec to vendor cache.")
    parser.add_argument("--url", default=UPSTREAM_URL, help="Override upstream spec URL.")
    parser.add_argument("--cache-path", default=DEFAULT_CACHE, help="Vendor cache path.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output_path = root / args.output
    cache_path = root / args.cache_path

    if args.input:
        text = read_text(Path(args.input))
    elif cache_path.exists():
        text = read_text(cache_path)
    else:
        text = download_text(args.url)
        if args.cache:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(text, encoding="utf-8")

    spec = parse_spec(text)
    if not isinstance(spec, dict):
        raise ValueError("Failed to parse OpenAPI document.")

    normalize_openapi_version(spec)
    trim_paths(spec)
    normalize_operation_ids(spec)
    strip_top_level_extensions(spec)
    normalize_security(spec)
    prune_components(spec)

    for key in ("openapi", "info", "paths"):
        if key not in spec:
            raise KeyError(f"Missing required top-level key: {key}")

    validate_refs(spec)

    output = build_output(spec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(output, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    size = output_path.stat().st_size
    if size >= 1_000_000:
        raise ValueError(f"Output file exceeds 1MB: {size} bytes")

    paths_methods = []
    for path, methods in ALLOWED_PATHS.items():
        for method in sorted(methods):
            paths_methods.append(f"{method.upper()} {path}")

    schema_count = len(output.get("components", {}).get("schemas", {}) or {})

    print(f"output: {output_path}")
    print(f"size_bytes: {size}")
    print("paths:")
    for entry in paths_methods:
        print(f"- {entry}")
    print(f"component_schemas: {schema_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
