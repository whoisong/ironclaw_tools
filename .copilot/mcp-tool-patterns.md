# MCP Tool Patterns

## Add a New MCP Tool

1. Implement core logic in `agent_service/skills/*.py`.
2. Register schema in `tools_manifest()` in `agent_service/mcp.py`.
3. Route execution in `handle_mcp_request()` for `tools/call`.
4. Add/adjust tests in `tests/test_mcp_protocol.py`.
5. Add user-facing usage snippet to `README.md`.

## Result Shape

- Prefer structured JSON payloads.
- For list results, use explicit keys:
  - `title`
  - `link`
  - `description`

## Long-Running / Human-in-the-Loop Tools

- Return explicit state:
  - `manual_verification_required`
  - `manual_verification_timeout`
  - `completed`
- Use persisted session tokens for resume operations.
