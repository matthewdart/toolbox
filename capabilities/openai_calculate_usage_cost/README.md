# openai.calculate_usage_cost

## Description

Summarize OpenAI usage from a JSONL log and optionally calculate estimated costs using a user-supplied pricing table.

## Non-goals

- Fetching usage data from OpenAI APIs
- Real-time cost monitoring
- Budget enforcement or alerting

## Deterministic behavior

Given the same JSONL log and pricing table, the output is fully deterministic. No external dependencies or network calls.
