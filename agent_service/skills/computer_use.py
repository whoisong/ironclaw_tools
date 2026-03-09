from __future__ import annotations

import time
from typing import Any

from agent_service.controller.desktop import DesktopController
from agent_service.skills.session_state import create_session, load_session, update_session
from agent_service.vision.fara_client import FaraClient


def _is_actionable(action: dict[str, Any]) -> bool:
    action_name = str(action.get("action", "")).lower()
    return action_name not in {"", "none", "done", "finish", "stop"}


def _apply_monitor_offset(action: dict[str, Any], screen: dict[str, Any]) -> dict[str, Any]:
    if "x" not in action or "y" not in action:
        return action
    adjusted = dict(action)
    adjusted["x"] = int(adjusted.get("x", 0)) + int(screen.get("left", 0))
    adjusted["y"] = int(adjusted.get("y", 0)) + int(screen.get("top", 0))
    adjusted["monitor_index"] = screen.get("monitor_index")
    return adjusted


def computer_use(goal: str, execute: bool = False) -> dict[str, Any]:
    controller = DesktopController()
    vision = FaraClient()
    screens = controller.capture_all_screens_png_b64()
    analyzed_screens: list[dict[str, Any]] = []
    selected_screen: dict[str, Any] | None = None
    selected_action: dict[str, Any] = {"action": "none", "reason": "no-screen-capture"}

    for screen in screens:
        screenshot_b64 = str(screen.get("screenshot_b64", ""))
        action = vision.predict_action(
            goal=f"{goal}. Analyze monitor {screen.get('monitor_index')}.",
            screenshot_b64=screenshot_b64,
        )
        analyzed_screens.append(
            {
                "monitor_index": screen.get("monitor_index"),
                "left": screen.get("left"),
                "top": screen.get("top"),
                "width": screen.get("width"),
                "height": screen.get("height"),
                "predicted_action": action,
            }
        )
        if selected_screen is None and _is_actionable(action):
            selected_screen = screen
            selected_action = _apply_monitor_offset(action, screen)

    if selected_screen is None and analyzed_screens:
        selected_screen = screens[0]
        selected_action = _apply_monitor_offset(analyzed_screens[0]["predicted_action"], screens[0])

    execution = {"executed": False, "reason": "dry-run"}
    if execute and _is_actionable(selected_action):
        execution = controller.execute_action(selected_action)
    return {
        "goal": goal,
        "screens_captured": len(screens),
        "selected_monitor_index": selected_screen.get("monitor_index") if selected_screen else None,
        "predicted_action": selected_action,
        "screen_analysis": analyzed_screens,
        "execution": execution,
    }


def fara_gui_task(
    task: str,
    max_steps: int = 5,
    execute: bool = False,
    step_delay_ms: int = 500,
) -> dict[str, Any]:
    controller = DesktopController()
    vision = FaraClient()
    steps: list[dict[str, Any]] = []

    for idx in range(max_steps):
        step_num = idx + 1
        screens = controller.capture_all_screens_png_b64()
        analyzed_screens: list[dict[str, Any]] = []
        selected_screen: dict[str, Any] | None = None
        action: dict[str, Any] = {"action": "none", "reason": "no-screen-capture"}

        for screen in screens:
            candidate = vision.predict_action(
                goal=f"Task: {task}. Step {step_num}/{max_steps}. Analyze monitor {screen.get('monitor_index')} and decide next GUI action.",
                screenshot_b64=str(screen.get("screenshot_b64", "")),
            )
            analyzed_screens.append(
                {
                    "monitor_index": screen.get("monitor_index"),
                    "left": screen.get("left"),
                    "top": screen.get("top"),
                    "width": screen.get("width"),
                    "height": screen.get("height"),
                    "predicted_action": candidate,
                }
            )
            if selected_screen is None and _is_actionable(candidate):
                selected_screen = screen
                action = _apply_monitor_offset(candidate, screen)

        if selected_screen is None and analyzed_screens:
            selected_screen = screens[0]
            action = _apply_monitor_offset(analyzed_screens[0]["predicted_action"], screens[0])

        action_name = str(action.get("action", "")).lower()
        should_stop = action_name in {"none", "done", "finish", "stop"}

        execution = {"executed": False, "reason": "dry-run"}
        if execute and not should_stop:
            execution = controller.execute_action(action)

        step_record = {
            "step": step_num,
            "screens_captured": len(screens),
            "selected_monitor_index": selected_screen.get("monitor_index") if selected_screen else None,
            "predicted_action": action,
            "screen_analysis": analyzed_screens,
            "execution": execution,
        }
        steps.append(step_record)

        if should_stop:
            break
        if execute and step_delay_ms > 0:
            time.sleep(step_delay_ms / 1000.0)

    return {
        "ok": True,
        "task": task,
        "execute": execute,
        "max_steps": max_steps,
        "steps_taken": len(steps),
        "steps": steps,
    }


def fara_gui_task_start(
    task: str,
    max_steps: int = 5,
    preview_steps: int = 2,
) -> dict[str, Any]:
    preview = fara_gui_task(
        task=task,
        max_steps=max(1, preview_steps),
        execute=False,
        step_delay_ms=250,
    )
    token = create_session(
        {
            "type": "fara_gui_task",
            "status": "manual_verification_required",
            "task": task,
            "max_steps": max_steps,
            "preview_steps": preview_steps,
            "preview": preview,
        }
    )
    return {
        "ok": True,
        "state": "manual_verification_required",
        "resume_token": token,
        "instructions": (
            "Complete any manual checks (for example CAPTCHA/verification) in your browser, "
            "then call fara_gui_task_resume with this resume_token."
        ),
        "preview": preview,
    }


def fara_gui_task_resume(
    resume_token: str,
    execute: bool = False,
    step_delay_ms: int = 500,
) -> dict[str, Any]:
    session = load_session(resume_token)
    if session is None:
        return {"ok": False, "error": "invalid resume_token"}

    if session.get("status") == "completed":
        return {"ok": True, "state": "completed", "result": session.get("result"), "resume_token": resume_token}

    task = str(session.get("task", ""))
    max_steps = int(session.get("max_steps", 5))
    preview_steps = int(session.get("preview_steps", 2))
    remaining_steps = max(1, max_steps - max(1, preview_steps))

    result = fara_gui_task(
        task=task,
        max_steps=remaining_steps,
        execute=execute,
        step_delay_ms=step_delay_ms,
    )
    update_session(
        resume_token,
        {
            "status": "completed",
            "result": result,
        },
    )
    return {"ok": True, "state": "completed", "resume_token": resume_token, "result": result}
