from fastapi.testclient import TestClient

from agent_service.main import app


client = TestClient(app)


def test_mcp_initialize_and_list_tools() -> None:
    init = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert init.status_code == 200
    init_json = init.json()
    assert init_json["result"]["protocolVersion"] == "2024-11-05"

    tools = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert tools.status_code == 200
    names = [t["name"] for t in tools.json()["result"]["tools"]]
    assert "browser_google_search" in names
    assert "browser_google_collect_results" in names
    assert "read_screen" in names
    assert "fara_gui_task" in names
    assert "fara_gui_task_start" in names
    assert "fara_gui_task_resume" in names


def test_mcp_call_search_web() -> None:
    call = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "search_web", "arguments": {"query": "ironclaw", "max_results": 2}},
        },
    )
    assert call.status_code == 200
    payload = call.json()["result"]
    assert "content" in payload
    assert payload["content"][0]["type"] == "text"


def test_mcp_call_fara_gui_task_dry_run() -> None:
    call = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "fara_gui_task",
                "arguments": {"task": "Open browser and search for weather", "max_steps": 2, "execute": False},
            },
        },
    )
    assert call.status_code == 200
    payload = call.json()["result"]
    assert payload["content"][0]["type"] == "text"


def test_mcp_call_fara_gui_task_start_and_resume() -> None:
    start = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "fara_gui_task_start",
                "arguments": {"task": "Search weather in browser", "max_steps": 4, "preview_steps": 2},
            },
        },
    )
    assert start.status_code == 200
    start_text = start.json()["result"]["content"][0]["text"]
    import json as _json

    start_payload = _json.loads(start_text)
    token = start_payload["resume_token"]
    assert token

    resume = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "fara_gui_task_resume",
                "arguments": {"resume_token": token, "execute": False},
            },
        },
    )
    assert resume.status_code == 200
    resume_payload = _json.loads(resume.json()["result"]["content"][0]["text"])
    assert resume_payload["state"] == "completed"
