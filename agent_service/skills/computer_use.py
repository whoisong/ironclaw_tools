from __future__ import annotations

import time
from typing import Any

from agent_service.controller.desktop import DesktopController
from agent_service.skills.session_state import create_session, load_session, update_session
from agent_service.vision.fara_client import FaraClient


def computer_use(goal: str, execute: bool = False) -> dict[str, Any]:
    controller = DesktopController()
    vision = FaraClient()
    screenshot_b64 = controller.capture_screen_png_b64()
    action = vision.predict_action(goal=goal, screenshot_b64=screenshot_b64)
    execution = {"executed": False, "reason": "dry-run"}
    if execute:
        execution = controller.execute_action(action)
    return {
        "goal": goal,
        "screenshot_captured": bool(screenshot_b64),
        "predicted_action": action,
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
        screenshot_b64 = controller.capture_screen_png_b64()
        action = vision.predict_action(
            goal=f"Task: {task}. Step {step_num}/{max_steps}. Decide the next GUI action.",
            screenshot_b64=screenshot_b64,
        )

        action_name = str(action.get("action", "")).lower()
        should_stop = action_name in {"none", "done", "finish", "stop"}

        execution = {"executed": False, "reason": "dry-run"}
        if execute and not should_stop:
            execution = controller.execute_action(action)

        step_record = {
            "step": step_num,
            "screenshot_captured": bool(screenshot_b64),
            "predicted_action": action,
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
