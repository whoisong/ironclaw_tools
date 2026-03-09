from __future__ import annotations

from agent_service.controller.desktop import DesktopController
from agent_service.vision.fara_client import FaraClient


def read_screen(question: str) -> dict[str, str | bool]:
    controller = DesktopController()
    vision = FaraClient()
    screenshot_b64 = controller.capture_screen_png_b64()
    description = vision.describe_screen(question=question, screenshot_b64=screenshot_b64)
    return {
        "question": question,
        "screenshot_captured": bool(screenshot_b64),
        "description": description,
    }

