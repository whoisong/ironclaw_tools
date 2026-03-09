from __future__ import annotations

import json
from typing import Any

from agent_service.skills.browser_use import (
    browser_google_collect_results,
    browser_google_search,
    browser_use,
)
from agent_service.skills.computer_use import (
    computer_use,
    fara_gui_task,
    fara_gui_task_resume,
    fara_gui_task_start,
)
from agent_service.skills.read_screen import read_screen
from agent_service.skills.run_code import run_code
from agent_service.skills.search_web import search_web

PROTOCOL_VERSION = "2024-11-05"


def _response(request_id: int, result: dict[str, Any] | None = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result or {}
    return payload


def _text_result(data: Any, is_error: bool = False) -> dict[str, Any]:
    if isinstance(data, str):
        text = data
    else:
        text = json.dumps(data, ensure_ascii=True)
    return {"content": [{"type": "text", "text": text}], "is_error": is_error}


def tools_manifest() -> list[dict[str, Any]]:
    return [
        {
            "name": "browser_google_search",
            "description": "Open browser, navigate to Google, search query, and return top results.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "url": {"type": "string", "default": "https://www.google.com"},
                    "headless": {"type": "boolean", "default": False},
                    "fallback_engine": {"type": "string", "default": "duckduckgo"},
                    "fallback_on_verification": {"type": "boolean", "default": True},
                    "wait_for_user_on_verification": {"type": "boolean", "default": True},
                    "manual_wait_timeout_sec": {"type": "integer", "default": 300},
                    "verification_poll_interval_sec": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
            "annotations": {"read_only_hint": False, "side_effects_hint": True, "destructive_hint": False},
        },
        {
            "name": "browser_google_collect_results",
            "description": "Collect organic (non-ad) Google search results from the first up to 3 pages.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "pages": {"type": "integer", "default": 3},
                    "headless": {"type": "boolean", "default": False},
                    "wait_for_user_on_verification": {"type": "boolean", "default": True},
                    "manual_wait_timeout_sec": {"type": "integer", "default": 300},
                    "verification_poll_interval_sec": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
            "annotations": {"read_only_hint": True, "side_effects_hint": False, "destructive_hint": False},
        },
        {
            "name": "browser_use",
            "description": "Generic browser action tool: open/click/type/extract.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["open", "click", "type", "extract"]},
                    "url": {"type": "string"},
                    "selector": {"type": "string"},
                    "text": {"type": "string"},
                    "timeout_ms": {"type": "integer", "default": 15000},
                },
                "required": ["action"],
            },
            "annotations": {"read_only_hint": False, "side_effects_hint": True, "destructive_hint": False},
        },
        {
            "name": "read_screen",
            "description": "Capture screen and answer question using local Fara vision model.",
            "inputSchema": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
            "annotations": {"read_only_hint": True, "side_effects_hint": False, "destructive_hint": False},
        },
        {
            "name": "computer_use",
            "description": "Predict and optionally execute a desktop action for a goal.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string"},
                    "execute": {"type": "boolean", "default": False},
                },
                "required": ["goal"],
            },
            "annotations": {"read_only_hint": False, "side_effects_hint": True, "destructive_hint": False},
        },
        {
            "name": "fara_gui_task",
            "description": "Use Fara to iteratively read GUI, decide next action, and optionally execute steps.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "max_steps": {"type": "integer", "default": 5},
                    "execute": {"type": "boolean", "default": False},
                    "step_delay_ms": {"type": "integer", "default": 500},
                },
                "required": ["task"],
            },
            "annotations": {"read_only_hint": False, "side_effects_hint": True, "destructive_hint": False},
        },
        {
            "name": "fara_gui_task_start",
            "description": "Start a Fara GUI task with a manual checkpoint and get a resume token.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "max_steps": {"type": "integer", "default": 5},
                    "preview_steps": {"type": "integer", "default": 2},
                },
                "required": ["task"],
            },
            "annotations": {"read_only_hint": False, "side_effects_hint": True, "destructive_hint": False},
        },
        {
            "name": "fara_gui_task_resume",
            "description": "Resume a started Fara GUI task using a resume token.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "resume_token": {"type": "string"},
                    "execute": {"type": "boolean", "default": False},
                    "step_delay_ms": {"type": "integer", "default": 500},
                },
                "required": ["resume_token"],
            },
            "annotations": {"read_only_hint": False, "side_effects_hint": True, "destructive_hint": False},
        },
        {
            "name": "run_code",
            "description": "Execute local python/bash snippet.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "language": {"type": "string", "enum": ["python", "bash"]},
                    "code": {"type": "string"},
                    "timeout_seconds": {"type": "integer", "default": 15},
                },
                "required": ["language", "code"],
            },
            "annotations": {"read_only_hint": False, "side_effects_hint": True, "destructive_hint": False},
        },
        {
            "name": "search_web",
            "description": "Web search results via DuckDuckGo instant API.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
            "annotations": {"read_only_hint": True, "side_effects_hint": False, "destructive_hint": False},
        },
    ]


def handle_mcp_request(payload: dict[str, Any]) -> dict[str, Any]:
    method = str(payload.get("method", ""))
    request_id = int(payload.get("id", 0))
    params = payload.get("params") or {}

    if method == "initialize":
        return _response(
            request_id,
            result={
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "ironclaw_tool", "version": "0.1.0"},
                "instructions": "Use these tools for browser and local computer automation.",
            },
        )

    if method == "notifications/initialized":
        return _response(request_id, result={})

    if method == "tools/list":
        return _response(request_id, result={"tools": tools_manifest()})

    if method == "tools/call":
        tool_name = str(params.get("name", ""))
        arguments = params.get("arguments") or {}
        try:
            if tool_name == "browser_google_search":
                result = browser_google_search(
                    query=str(arguments.get("query", "")),
                    url=str(arguments.get("url", "https://www.google.com")),
                    headless=bool(arguments.get("headless", False)),
                    fallback_engine=str(arguments.get("fallback_engine", "duckduckgo")),
                    fallback_on_verification=bool(arguments.get("fallback_on_verification", True)),
                    wait_for_user_on_verification=bool(arguments.get("wait_for_user_on_verification", True)),
                    manual_wait_timeout_sec=int(arguments.get("manual_wait_timeout_sec", 300)),
                    verification_poll_interval_sec=int(arguments.get("verification_poll_interval_sec", 5)),
                )
            elif tool_name == "browser_google_collect_results":
                result = browser_google_collect_results(
                    query=str(arguments.get("query", "")),
                    pages=int(arguments.get("pages", 3)),
                    headless=bool(arguments.get("headless", False)),
                    wait_for_user_on_verification=bool(arguments.get("wait_for_user_on_verification", True)),
                    manual_wait_timeout_sec=int(arguments.get("manual_wait_timeout_sec", 300)),
                    verification_poll_interval_sec=int(arguments.get("verification_poll_interval_sec", 5)),
                )
            elif tool_name == "browser_use":
                result = browser_use(
                    action=str(arguments.get("action", "")),
                    url=arguments.get("url"),
                    selector=arguments.get("selector"),
                    text=arguments.get("text"),
                    timeout_ms=int(arguments.get("timeout_ms", 15_000)),
                )
            elif tool_name == "read_screen":
                result = read_screen(question=str(arguments.get("question", "")))
            elif tool_name == "computer_use":
                result = computer_use(
                    goal=str(arguments.get("goal", "")),
                    execute=bool(arguments.get("execute", False)),
                )
            elif tool_name == "fara_gui_task":
                result = fara_gui_task(
                    task=str(arguments.get("task", "")),
                    max_steps=int(arguments.get("max_steps", 5)),
                    execute=bool(arguments.get("execute", False)),
                    step_delay_ms=int(arguments.get("step_delay_ms", 500)),
                )
            elif tool_name == "fara_gui_task_start":
                result = fara_gui_task_start(
                    task=str(arguments.get("task", "")),
                    max_steps=int(arguments.get("max_steps", 5)),
                    preview_steps=int(arguments.get("preview_steps", 2)),
                )
            elif tool_name == "fara_gui_task_resume":
                result = fara_gui_task_resume(
                    resume_token=str(arguments.get("resume_token", "")),
                    execute=bool(arguments.get("execute", False)),
                    step_delay_ms=int(arguments.get("step_delay_ms", 500)),
                )
            elif tool_name == "run_code":
                result = run_code(
                    language=str(arguments.get("language", "")),
                    code=str(arguments.get("code", "")),
                    timeout_seconds=int(arguments.get("timeout_seconds", 15)),
                )
            elif tool_name == "search_web":
                result = search_web(
                    query=str(arguments.get("query", "")),
                    max_results=int(arguments.get("max_results", 5)),
                )
            else:
                return _response(
                    request_id,
                    error={"code": -32601, "message": f"Unknown tool: {tool_name}"},
                )

            return _response(request_id, result=_text_result(result, is_error=not bool(result.get("ok", True))))
        except Exception as exc:
            return _response(request_id, result=_text_result({"error": str(exc)}, is_error=True))

    return _response(request_id, error={"code": -32601, "message": f"Method not found: {method}"})
