from __future__ import annotations

import base64
from typing import Any


class DesktopController:
    def __init__(self) -> None:
        self._mss = None
        self._pyautogui = None
        try:
            import mss  # type: ignore

            self._mss = mss
        except Exception:
            self._mss = None
        try:
            import pyautogui  # type: ignore

            self._pyautogui = pyautogui
        except Exception:
            self._pyautogui = None

    def capture_screen_png_b64(self) -> str:
        if self._mss is None:
            return ""

        with self._mss.mss() as sct:
            from mss import tools  # type: ignore

            monitor = sct.monitors[1]
            shot = sct.grab(monitor)
            png_bytes = tools.to_png(shot.rgb, shot.size)
            return base64.b64encode(png_bytes).decode("ascii")

    def execute_action(self, action: dict[str, Any]) -> dict[str, Any]:
        if self._pyautogui is None:
            return {"executed": False, "reason": "pyautogui not installed"}

        action_type = str(action.get("action", "")).lower()
        x = int(action.get("x", 0))
        y = int(action.get("y", 0))

        if action_type == "click":
            self._pyautogui.click(x=x, y=y)
            return {"executed": True, "action": "click", "x": x, "y": y}
        if action_type == "type":
            text = str(action.get("text", ""))
            self._pyautogui.typewrite(text)
            return {"executed": True, "action": "type", "text": text}
        return {"executed": False, "reason": f"unsupported action: {action_type}"}
