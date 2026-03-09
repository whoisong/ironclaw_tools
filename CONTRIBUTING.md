# Contributing

## Setup

```powershell
pip install -e .[dev]
pip install -e .[automation]
python -m playwright install chromium
```

## Before Opening PR

1. Run `python -m pytest -q`
2. If MCP logic changed, run:
   - `python -m pytest -q tests\test_integration_ironclaw_mcp.py`
3. Ensure no runtime artifacts are staged (`test/*.png`, logs, pid files, session dumps).
4. Update README when behavior/tool schema changes.
5. Keep CAPTCHA handling compliant (manual verification only, no bypass logic).

## Commit Style

- Use clear imperative messages:
  - `feat: add browser_google_collect_results tool`
  - `fix: improve captcha polling detection`
