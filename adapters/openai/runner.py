"""OpenAI tool-calling runner for toolbox capabilities."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI
from dotenv import load_dotenv

from adapters.openai.toolgen import main as toolgen_main
from core.dispatch import dispatch

TOOLS_DIR = Path(__file__).resolve().parent


def _load_tools() -> List[Dict[str, Any]]:
    tools = []
    for path in sorted(TOOLS_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            tools.append(json.load(handle))
    return tools


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenAI tool-calling loop.")
    parser.add_argument("--message", required=True, help="User message")
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
        help="OpenAI model (default: env OPENAI_MODEL or gpt-4.1-mini)",
    )
    parser.add_argument(
        "--regen-tools",
        action="store_true",
        help="Regenerate tool JSON files before running",
    )
    return parser.parse_args()


def _call_openai(client: OpenAI, model: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
    )


def main() -> int:
    args = _parse_args()

    if args.regen_tools:
        toolgen_main([])

    load_dotenv()

    tools = _load_tools()
    if not tools:
        raise SystemExit("no tools found in adapters/openai (run toolgen)")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

    messages: List[Dict[str, Any]] = [{"role": "user", "content": args.message}]

    while True:
        response = _call_openai(client, args.model, messages, tools)
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)

        if not tool_calls:
            print(message.content or "")
            return 0

        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            }
        )

        for call in tool_calls:
            tool_name = call.function.name
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError as exc:
                tool_result = {
                    "ok": False,
                    "error": {
                        "type": "invalid_tool_arguments",
                        "message": f"invalid tool arguments: {exc}",
                    },
                }
            else:
                tool_result = dispatch(tool_name, arguments)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )


if __name__ == "__main__":
    raise SystemExit(main())
