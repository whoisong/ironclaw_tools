from __future__ import annotations

from agent_service.controller.desktop import DesktopController
from agent_service.vision.fara_client import FaraClient


def read_screen(question: str) -> dict[str, str | bool | int | list[dict[str, str | int]]]:
    controller = DesktopController()
    vision = FaraClient()
    screens = controller.capture_all_screens_png_b64()
    per_screen: list[dict[str, str | int]] = []

    for screen in screens:
        description = vision.describe_screen(
            question=f"{question}. Focus only on monitor {screen.get('monitor_index')}.",
            screenshot_b64=str(screen.get("screenshot_b64", "")),
        )
        per_screen.append(
            {
                "monitor_index": int(screen.get("monitor_index", 0)),
                "description": description,
            }
        )

    merged = "\n".join(
        [f"[Monitor {item['monitor_index']}] {item['description']}" for item in per_screen]
    ).strip()
    return {
        "question": question,
        "screens_captured": len(screens),
        "screen_descriptions": per_screen,
        "description": merged or "No description produced.",
    }

