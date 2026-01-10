# OpenAI Tool Runner

## Setup

1. Create `.env` from `.env.example`:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (optional, default `gpt-4.1-mini`)

2. Install dependencies:

```
pip install -r requirements.txt
```

## Generate Tools

```
python -m adapters.openai.toolgen
```

## Run Tool-Calling Loop

```
python -m adapters.openai.runner --message "Normalize this markdown: hello  \nworld"
```

Use `--regen-tools` to regenerate tool JSON before running.
