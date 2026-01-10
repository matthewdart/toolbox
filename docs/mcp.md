# MCP Server (stdio)

## Run

```
python -m adapters.mcp.server
```

The server registers each contract in `/contracts` as an MCP tool and also exposes `toolbox.list_capabilities`.

## Notes

- The server uses stdio transport.
- Inputs are validated against the contract schema.
- Outputs are returned as JSON with `{ ok, result|error }`.
