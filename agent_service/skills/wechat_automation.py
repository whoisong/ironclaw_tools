from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any


def _capture(path: Path) -> str:
    try:
        import mss  # type: ignore
        import mss.tools  # type: ignore

        with mss.mss() as sct:
            mon = sct.monitors[1]
            shot = sct.grab(mon)
            mss.tools.to_png(shot.rgb, shot.size, output=str(path))
        return str(path)
    except Exception as exc:
        return f"capture_failed:{exc}"


def wechat_send_message(
    chat_name: str,
    message: str,
    dry_run: bool = True,
    open_if_needed: bool = True,
    send: bool = False,
    capture_evidence: bool = True,
    strict_focus: bool = True,
    verify_input: bool = True,
) -> dict[str, Any]:
    evidence_dir = Path(r"C:\Users\nutty\Documents\workspace\AI\ironclaw_tool\test")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    steps: list[dict[str, Any]] = []

    def record(step: str, ok: bool, detail: str = "") -> None:
        steps.append({"step": step, "ok": ok, "detail": detail})

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "chat_name": chat_name,
            "message": message,
            "plan": [
                "Activate or launch WeChat",
                "Use Ctrl+F to search target chat",
                "Open the chat and focus message input",
                "Type message text",
                "Optionally send (Enter)",
            ],
            "send": send,
        }

    try:
        import pyautogui  # type: ignore
        import pyperclip  # type: ignore
        import pygetwindow as gw  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": f"Missing automation dependency: {exc}"}

    pyautogui.PAUSE = 0.25
    pyautogui.FAILSAFE = True

    if capture_evidence:
        record("capture_initial", True, _capture(evidence_dir / f"wechat_{stamp}_01_initial.png"))

    # Try to bring WeChat to front via Win search.
    if open_if_needed:
        try:
            pyautogui.press("win")
            time.sleep(0.7)
            pyautogui.typewrite("WeChat", interval=0.03)
            pyautogui.press("enter")
            time.sleep(2.5)
            record("open_wechat", True, "Triggered from Start menu search")
        except Exception as exc:
            record("open_wechat", False, str(exc))

    if capture_evidence:
        record("capture_after_open", True, _capture(evidence_dir / f"wechat_{stamp}_02_after_open.png"))

    # Search for target chat in WeChat.
    try:
        # Try to leave embedded pages/popups and return to chat panel first.
        pyautogui.press("esc")
        time.sleep(0.2)
        pyautogui.press("esc")
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "1")
        time.sleep(0.5)
        record("switch_to_chat_panel", True, "Esc x2 + Ctrl+1")

        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.6)
        pyperclip.copy(chat_name)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.9)
        pyautogui.press("enter")
        time.sleep(1.1)
        record("search_chat", True, f"searched:{chat_name}")
    except Exception as exc:
        record("search_chat", False, str(exc))
        return {"ok": False, "error": "Failed while searching chat", "steps": steps}

    if capture_evidence:
        record("capture_after_search", True, _capture(evidence_dir / f"wechat_{stamp}_03_after_search.png"))

    # Re-focus WeChat window before typing to avoid typing into wrong app.
    wechat_window = None
    try:
        candidates = [w for w in gw.getAllWindows() if w and w.title and ("微信" in w.title or "WeChat" in w.title)]
        if candidates:
            wechat_window = candidates[0]
            try:
                wechat_window.activate()
            except Exception:
                pass
            time.sleep(0.6)
            record("refocus_wechat_window", True, wechat_window.title)
        else:
            record("refocus_wechat_window", False, "No titled WeChat window found")
    except Exception as exc:
        record("refocus_wechat_window", False, str(exc))

    # Verify active window title before typing.
    try:
        active = gw.getActiveWindow()
        active_title = active.title if active else ""
        is_wechat_active = ("微信" in active_title) or ("WeChat" in active_title)
        record("active_window_check", is_wechat_active, active_title)
        if strict_focus and not is_wechat_active:
            if capture_evidence:
                record("capture_focus_mismatch", True, _capture(evidence_dir / f"wechat_{stamp}_focus_mismatch.png"))
            return {
                "ok": False,
                "error": "Active window is not WeChat; aborting to avoid typing into wrong app.",
                "steps": steps,
            }
    except Exception as exc:
        record("active_window_check", False, str(exc))
        if strict_focus:
            return {"ok": False, "error": "Failed to verify active window", "steps": steps}

    # Focus message input area using WeChat-window relative coordinates.
    try:
        if wechat_window is not None:
            x = int(wechat_window.left + max(40, wechat_window.width * 0.65))
            y = int(wechat_window.top + max(40, wechat_window.height * 0.88))
        else:
            screen_size = pyautogui.size()
            x = int(screen_size.width * 0.70)
            y = int(screen_size.height * 0.88)
        pyautogui.click(x, y)
        time.sleep(0.4)
        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            old_clipboard = ""
        pyperclip.copy(message)
        pyautogui.hotkey("ctrl", "v")
        record("type_message", True, f"typed_len:{len(message)} at ({x},{y})")

        if verify_input:
            time.sleep(0.35)
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.15)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.2)
            pasted_back = pyperclip.paste() or ""
            matched = message.strip() in pasted_back.strip()
            record("verify_typed_message", matched, f"clipboard_len:{len(pasted_back)}")
            try:
                pyperclip.copy(old_clipboard)
            except Exception:
                pass
            if not matched:
                if capture_evidence:
                    record("capture_verify_failed", True, _capture(evidence_dir / f"wechat_{stamp}_verify_failed.png"))
                return {
                    "ok": False,
                    "error": "Input verification failed: typed text not found in message box.",
                    "steps": steps,
                }
    except Exception as exc:
        record("type_message", False, str(exc))
        return {"ok": False, "error": "Failed while typing message", "steps": steps}

    if capture_evidence:
        record("capture_after_type", True, _capture(evidence_dir / f"wechat_{stamp}_04_after_type.png"))

    if send:
        try:
            pyautogui.press("enter")
            record("send_message", True, "pressed Enter")
        except Exception as exc:
            record("send_message", False, str(exc))
            return {"ok": False, "error": "Failed while sending message", "steps": steps}
    else:
        record("send_message", True, "skipped (send=false)")

    return {
        "ok": True,
        "chat_name": chat_name,
        "message": message,
        "send": send,
        "dry_run": False,
        "steps": steps,
    }
