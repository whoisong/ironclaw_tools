# AI Change Strategy

## 1) Scope First

- Identify user-visible behavior change.
- List touched modules before editing.
- Prefer minimal surface-area changes.

## 2) Safe Editing Rules

- Keep tool schemas backward compatible when possible.
- If schema must change, update:
  - `agent_service/mcp.py`
  - tests
  - README examples

## 3) Runtime Discipline

- After code changes, restart:
  - MCP backend (`uvicorn`)
  - IronClaw runtime (`ironclaw run`)
- Re-verify `ironclaw mcp test ironclaw_tool`.

## 4) Security and Compliance

- Do not implement CAPTCHA bypass.
- Use manual verification checkpoints and resume flow.
- Never log or commit secrets/tokens.
