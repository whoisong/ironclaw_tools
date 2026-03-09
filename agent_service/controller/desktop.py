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
        captures = self.capture_all_screens_png_b64()
        if not captures:
            return ""
        return str(captures[0]["screenshot_b64"])

    def capture_all_screens_png_b64(self) -> list[dict[str, Any]]:
        if self._mss is None:
            return []

        with self._mss.mss() as sct:
            from mss import tools  # type: ignore

            captures: list[dict[str, Any]] = []
            for monitor_index, monitor in enumerate(sct.monitors[1:], start=1):
                shot = sct.grab(monitor)
                png_bytes = tools.to_png(shot.rgb, shot.size)
                captures.append(
                    {
                        "monitor_index": monitor_index,
                        "left": int(monitor.get("left", 0)),
                        "top": int(monitor.get("top", 0)),
                        "width": int(monitor.get("width", shot.size[0])),
                        "height": int(monitor.get("height", shot.size[1])),
                        "screenshot_b64": base64.b64encode(png_bytes).decode("ascii"),
                    }
                )
            return captures

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
