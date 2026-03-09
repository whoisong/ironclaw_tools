# ironclaw_tools

`ironclaw_tools` is a local MCP tool server for [IronClaw](https://github.com/nearai/ironclaw).
It adds browser automation, GUI understanding, and local utility tools while keeping IronClaw's main LLM backend unchanged.

## Features

- MCP endpoint: `POST /mcp`
- Browser tools:
  - `browser_google_search`
  - `browser_google_collect_results` (collect organic results from up to first 3 pages)
  - `browser_use`
- GUI tools:
  - `read_screen`
  - `computer_use`
  - `fara_gui_task`
  - `fara_gui_task_start`
  - `fara_gui_task_resume`
- Utility tools:
  - `run_code`
  - `search_web`

## Safety Notes

- This project does not bypass CAPTCHA or anti-bot protections.
- If verification pages are detected, tools can pause for manual completion and then resume.

## Requirements

- Python 3.11+
- IronClaw binary (`ironclaw.exe`) available
- Optional for browser automation:
  - Playwright + Chromium
- Optional for GUI automation:
  - `mss`
  - `pyautogui`
- Optional for local vision:
  - Ollama + Fara model

## Installation

```powershell
cd C:\Users\nutty\Documents\workspace\AI\ironclaw_tool
pip install -e .[dev]
```

Optional automation stack:

```powershell
pip install -e .[automation]
python -m playwright install chromium
```

## Run Server

```powershell
cd C:\Users\nutty\Documents\workspace\AI\ironclaw_tool
python -m uvicorn agent_service.main:app --host 127.0.0.1 --port 8000
```

## Register in IronClaw

```powershell
cd C:\Users\nutty\Documents\workspace\AI\repos\ironclaw
.\target\release\ironclaw.exe mcp add ironclaw_tool http://127.0.0.1:8000/mcp
.\target\release\ironclaw.exe mcp test ironclaw_tool
```

## Example Prompt in IronClaw

```text
Use tool ironclaw_tool_browser_google_collect_results with:
query="OpenAI",
pages=3,
headless=false,
wait_for_user_on_verification=true,
manual_wait_timeout_sec=900,
verification_poll_interval_sec=5
Return a JSON list of title, link, description.
```

## Development

Run tests:

```powershell
cd C:\Users\nutty\Documents\workspace\AI\ironclaw_tool
python -m pytest -q
```

Real IronClaw integration tests:

```powershell
python -m pytest -q tests\test_integration_real_ironclaw.py
python -m pytest -q tests\test_integration_ironclaw_mcp.py
```

## Project Structure

```text
agent_service/
  main.py
  mcp.py
  skills/
  controller/
  vision/
tests/
config/
docs/
scripts/
.copilot/
```

## License

Apache-2.0
