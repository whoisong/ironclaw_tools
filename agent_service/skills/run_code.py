from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any


def run_code(language: str, code: str, timeout_seconds: int = 15) -> dict[str, Any]:
    language = language.lower().strip()
    suffix = ".py" if language == "python" else ".sh"
    if language not in {"python", "bash"}:
        return {"ok": False, "error": "language must be python or bash"}

    with tempfile.TemporaryDirectory(prefix="ironclaw_tool_") as temp_dir:
        script_path = Path(temp_dir) / f"snippet{suffix}"
        script_path.write_text(code, encoding="utf-8")

        if language == "python":
            command = ["python", str(script_path)]
        else:
            command = ["bash", str(script_path)]

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return {
                "ok": completed.returncode == 0,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        except FileNotFoundError:
            return {"ok": False, "error": f"{language} runtime is not available"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "execution timed out"}

