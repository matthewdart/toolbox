"""Dispatch capabilities with contract validation."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict

from jsonschema import ValidationError, validators

from core.registry import REGISTRY

CONTRACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "contracts")


@dataclass
class DispatchError(Exception):
    code: str
    message: str
    details: Any | None = None


def _load_contract(capability_id: str) -> Dict[str, Any]:
    filename = f"{capability_id}.v1.json"
    path = os.path.join(CONTRACTS_DIR, filename)
    if not os.path.isfile(path):
        raise DispatchError("contract_not_found", f"contract not found: {filename}")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _format_validation_error(err: ValidationError) -> Dict[str, Any]:
    return {
        "message": err.message,
        "path": list(err.path),
        "schema_path": list(err.schema_path),
    }


def _validate(schema: Dict[str, Any], payload: Any, error_code: str) -> None:
    validator_cls = validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        details = [_format_validation_error(err) for err in errors]
        raise DispatchError(error_code, "schema validation failed", details)


def dispatch(capability_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if capability_id not in REGISTRY:
        return {
            "ok": False,
            "error": {
                "type": "capability_not_found",
                "message": f"unknown capability: {capability_id}",
            },
        }

    try:
        contract = _load_contract(capability_id)
        input_schema = contract.get("input_schema")
        output_schema = contract.get("output_schema")
        if not input_schema or not output_schema:
            raise DispatchError("contract_invalid", "contract missing input/output schema")

        _validate(input_schema, payload, "validation_error")
        result = REGISTRY[capability_id](**payload)
        _validate(output_schema, result, "output_validation_error")
        return {"ok": True, "result": result}
    except DispatchError as exc:
        return {
            "ok": False,
            "error": {
                "type": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        }
    except Exception as exc:  # pragma: no cover - defensive catch
        return {
            "ok": False,
            "error": {
                "type": "capability_error",
                "message": str(exc),
            },
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dispatch a toolbox capability.")
    parser.add_argument("--capability", required=True, help="Capability id")
    parser.add_argument(
        "--input-json",
        help="Input JSON payload as a string",
    )
    parser.add_argument(
        "--input-file",
        help="Path to a JSON file with the input payload",
    )
    return parser.parse_args()


def _load_payload(args: argparse.Namespace) -> Dict[str, Any]:
    if args.input_json and args.input_file:
        raise SystemExit("provide only one of --input-json or --input-file")
    if args.input_json:
        return json.loads(args.input_json)
    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as handle:
            return json.load(handle)
    raise SystemExit("missing input payload (--input-json or --input-file)")


def main() -> int:
    args = _parse_args()
    payload = _load_payload(args)
    response = dispatch(args.capability, payload)
    json.dump(response, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
