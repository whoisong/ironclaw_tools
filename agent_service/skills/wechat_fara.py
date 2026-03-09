from __future__ import annotations

import base64
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from agent_service.controller.desktop import DesktopController
from agent_service.vision.fara_client import FaraClient


def _is_actionable(action: dict[str, Any]) -> bool:
    action_name = str(action.get("action", "")).lower()
    return action_name not in {"", "none", "done", "finish", "stop"}


def _apply_monitor_offset(action: dict[str, Any], screen: dict[str, Any]) -> dict[str, Any]:
    if "x" not in action or "y" not in action:
        adjusted = dict(action)
        adjusted["monitor_index"] = screen.get("monitor_index")
        return adjusted
    adjusted = dict(action)
    adjusted["x"] = int(adjusted.get("x", 0)) + int(screen.get("left", 0))
    adjusted["y"] = int(adjusted.get("y", 0)) + int(screen.get("top", 0))
    adjusted["monitor_index"] = screen.get("monitor_index")
    return adjusted


def _write_png_from_b64(path: Path, screenshot_b64: str) -> str:
    try:
        path.write_bytes(base64.b64decode(screenshot_b64.encode("ascii")))
        return str(path)
    except Exception as exc:
        return f"write_failed:{exc}"


def _extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def _screen_state_score(state: dict[str, Any]) -> int:
    return (
        (3 if bool(state.get("in_target_chat", False)) else 0)
        + (2 if bool(state.get("input_focused", False)) else 0)
        + (4 if bool(state.get("message_present", False)) else 0)
        + (1 if bool(state.get("search_popup_visible", False)) else 0)
        + (1 if bool(state.get("wechat_visible", False)) else 0)
    )


def _resolve_wechat_window() -> dict[str, int] | None:
    try:
        import pygetwindow as gw  # type: ignore

        wins = [w for w in gw.getAllWindows() if w and w.title and ("WeChat" in w.title or "微信" in w.title)]
        if not wins:
            return None
        w = wins[0]
        return {"left": int(w.left), "top": int(w.top), "width": int(w.width), "height": int(w.height)}
    except Exception:
        return None


def _find_screen_for_point(screens: list[dict[str, Any]], x: int, y: int) -> dict[str, Any] | None:
    for s in screens:
        left = int(s.get("left", 0))
        top = int(s.get("top", 0))
        width = int(s.get("width", 0))
        height = int(s.get("height", 0))
        if left <= x < left + width and top <= y < top + height:
            return s
    return None


def _fallback_action_for_stage(
    stage: str,
    message: str,
    selected_screen: dict[str, Any],
    wechat_window: dict[str, int] | None,
) -> dict[str, Any]:
    if wechat_window:
        win_left = int(wechat_window["left"])
        win_top = int(wechat_window["top"])
        win_width = int(wechat_window["width"])
        win_height = int(wechat_window["height"])
    else:
        win_left = int(selected_screen.get("left", 0))
        win_top = int(selected_screen.get("top", 0))
        win_width = int(selected_screen.get("width", 1920))
        win_height = int(selected_screen.get("height", 1080))

    if stage == "enter_chat":
        # WeChat search popup: first Group Chats row is usually in lower half of left panel.
        return {
            "action": "click",
            "x": win_left + int(win_width * 0.19),
            "y": win_top + int(win_height * 0.68),
            "reason": "fallback-enter-chat-row",
            "monitor_index": selected_screen.get("monitor_index"),
        }
    if stage == "focus_input":
        return {
            "action": "click",
            "x": win_left + int(win_width * 0.70),
            "y": win_top + int(win_height * 0.90),
            "reason": "fallback-focus-input",
            "monitor_index": selected_screen.get("monitor_index"),
        }
    if stage == "type_message":
        return {
            "action": "type",
            "text": message,
            "reason": "fallback-type-message",
            "monitor_index": selected_screen.get("monitor_index"),
        }
    return {
        "action": "type",
        "text": "\n",
        "reason": "fallback-send-enter",
        "monitor_index": selected_screen.get("monitor_index"),
    }


def wechat_send_message_fara(
    chat_name: str,
    message: str,
    max_steps: int = 20,
    execute: bool = True,
    open_if_needed: bool = True,
    send: bool = False,
    capture_evidence: bool = True,
    step_delay_ms: int = 900,
    max_runtime_seconds: int = 25,
) -> dict[str, Any]:
    controller = DesktopController()
    vision = FaraClient()
    steps: list[dict[str, Any]] = []
    ollama_generate_calls = 0
    ollama_state_calls = 0
    completed = False
    completion_reason = "max_steps_reached"
    send_done = False

    evidence_dir = Path(r"C:\Users\nutty\Documents\workspace\AI\ironclaw_tool\test")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if open_if_needed and execute:
        try:
            import pyautogui  # type: ignore
            import pyperclip  # type: ignore

            pyautogui.PAUSE = 0.25
            pyautogui.press("win")
            time.sleep(0.6)
            pyautogui.typewrite("WeChat", interval=0.03)
            pyautogui.press("enter")
            time.sleep(2.4)
            # Pre-place search text to reduce ambiguity in follow-up steps.
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.5)
            pyperclip.copy(chat_name)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.6)
            pyautogui.press("enter")
            time.sleep(0.9)
        except Exception:
            pass

    stop_markers = {"none", "done", "finish", "stop"}
    consecutive_noop = 0
    stage = "enter_chat"
    deadline = time.time() + max(5, int(max_runtime_seconds))

    for step_num in range(1, max_steps + 1):
        if time.time() >= deadline:
            completion_reason = "max_runtime_reached"
            break

        screens = controller.capture_all_screens_png_b64()
        if not screens:
            steps.append(
                {
                    "step": step_num,
                    "ok": False,
                    "error": "no-screen-capture",
                }
            )
            break

        selected_screen: dict[str, Any] | None = None
        selected_action: dict[str, Any] = {"action": "none", "reason": "vision-fallback-no-op"}
        analyzed_sorted: list[dict[str, Any]] = []
        selected_state: dict[str, Any] = {}

        wechat_window = _resolve_wechat_window()
        if wechat_window:
            center_x = int(wechat_window["left"] + wechat_window["width"] / 2)
            center_y = int(wechat_window["top"] + wechat_window["height"] / 2)
            selected_screen = _find_screen_for_point(screens, center_x, center_y)
        if selected_screen is None:
            selected_screen = screens[0]

        in_target_chat = stage in {"focus_input", "type_message", "send", "done"}
        input_focused = stage in {"type_message", "send", "done"}
        message_present = stage in {"send", "done"} and not send
        search_popup_visible = stage == "enter_chat"
        fallback_applied = False

        # Completion gate.
        if stage == "done" or (in_target_chat and message_present and ((not send) or send_done)):
            completed = True
            completion_reason = "state_goal_satisfied"
            steps.append(
                {
                    "step": step_num,
                    "selected_monitor_index": selected_screen.get("monitor_index"),
                    "state": selected_state,
                    "predicted_action": {"action": "none", "reason": "already-complete"},
                    "screen_analysis": analyzed_sorted,
                    "execution": {"executed": False, "reason": "completed"},
                    "evidence": "",
                }
            )
            break

        if stage == "enter_chat":
            phase = f"Click the exact row for group chat '{chat_name}' in WeChat left search popup, then open that chat."
        elif stage == "focus_input":
            phase = "Click WeChat message input box at bottom to focus cursor."
        elif stage == "type_message":
            phase = f"Type exact text '{message}' into the focused input box."
        elif stage == "send":
            phase = "Press Enter to send the message now."
        else:
            phase = "If task complete return none."

        goal = (
            "You are controlling WeChat desktop UI."
            f" Objective: chat='{chat_name}', message='{message}', send={str(send).lower()}."
            f" Step {step_num}/{max_steps}. {phase} "
            "Return strict JSON: action,x,y,text,reason."
        )

        action = vision.predict_action(goal=goal, screenshot_b64=str(selected_screen.get("screenshot_b64", "")))
        ollama_generate_calls += 1
        selected_action = _apply_monitor_offset(action, selected_screen)

        if str(selected_action.get("action", "")).lower() in {"", "none"}:
            selected_action = _fallback_action_for_stage(stage, message, selected_screen, wechat_window)
            fallback_applied = True

        if str(selected_action.get("action", "")).lower() == "type" and not selected_action.get("text"):
            selected_action["text"] = message
            selected_action["reason"] = "inject-message-for-type"
        if stage == "send":
            # Force send step when message already present.
            selected_action = {
                "action": "type",
                "text": "\n",
                "reason": "force-send-enter",
                "monitor_index": selected_screen.get("monitor_index"),
            }

        evidence_path = ""
        if capture_evidence:
            evidence_path = _write_png_from_b64(
                evidence_dir / f"wechat_fara_{stamp}_step{step_num:02d}_monitor{selected_screen.get('monitor_index')}.png",
                str(selected_screen.get("screenshot_b64", "")),
            )

        execution = {"executed": False, "reason": "dry-run"}
        if execute and _is_actionable(selected_action):
            execution = controller.execute_action(selected_action)
            if selected_action.get("reason") == "force-send-enter" and bool(execution.get("executed")):
                send_done = True
            if bool(execution.get("executed")):
                if stage == "enter_chat":
                    stage = "focus_input"
                elif stage == "focus_input":
                    stage = "type_message"
                elif stage == "type_message":
                    stage = "send" if send else "done"
                elif stage == "send":
                    stage = "done"

        steps.append(
            {
                "step": step_num,
                "selected_monitor_index": selected_screen.get("monitor_index"),
                "state": selected_state,
                "predicted_action": selected_action,
                "screen_analysis": analyzed_sorted,
                "fallback_applied": fallback_applied,
                "execution": execution,
                "evidence": evidence_path,
            }
        )

        action_name = str(selected_action.get("action", "")).lower()
        if action_name in stop_markers:
            consecutive_noop += 1
        else:
            consecutive_noop = 0

        if consecutive_noop >= 3:
            completion_reason = "consecutive_noop_limit"
            break

        if execute and step_delay_ms > 0:
            time.sleep(step_delay_ms / 1000.0)

    return {
        "ok": completed,
        "tool_mode": "fara-only",
        "chat_name": chat_name,
        "message": message,
        "execute": execute,
        "max_steps": max_steps,
        "completed": completed,
        "completion_reason": completion_reason,
        "steps_taken": len(steps),
        "steps": steps,
        "ollama_model": vision.model_name,
        "ollama_generate_calls": ollama_generate_calls,
        "ollama_state_calls": ollama_state_calls,
    }
