# QA Checklist

## Mandatory

1. `python -m pytest -q`
2. `python -m pytest -q tests/test_mcp_protocol.py`
3. Restart backend services after code change:
   - `uvicorn agent_service.main:app`
   - `ironclaw run`
4. `ironclaw mcp test ironclaw_tool`

## Behavior Checks

- Tool appears in MCP list after registration.
- CAPTCHA flow:
  - detects verification page
  - waits for manual solve when configured
  - resumes and extracts results
- Search collector:
  - first 3 pages maximum
  - excludes ad items
  - returns `title/link/description`

## Release Hygiene

- No cache/build/runtime files committed.
- No local logs/screenshots/session dumps in git.
- README reflects current tool list and usage.
