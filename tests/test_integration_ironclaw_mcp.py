from __future__ import annotations

import subprocess
import time
from pathlib import Path


def test_real_ironclaw_mcp_registration_and_test() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    ironclaw_bin = workspace_root / "repos" / "ironclaw" / "target" / "release" / "ironclaw.exe"
    assert ironclaw_bin.exists(), f"Expected binary at {ironclaw_bin}"

    service_dir = workspace_root / "ironclaw_tool"
    server_proc = subprocess.Popen(
        [
            "python",
            "-m",
            "uvicorn",
            "agent_service.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=str(service_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(4)
        # Remove if it already exists from prior runs.
        subprocess.run(
            [str(ironclaw_bin), "mcp", "remove", "ironclaw_tool"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        add = subprocess.run(
            [str(ironclaw_bin), "mcp", "add", "ironclaw_tool", "http://127.0.0.1:8000/mcp"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert add.returncode == 0, add.stderr

        test = subprocess.run(
            [str(ironclaw_bin), "mcp", "test", "ironclaw_tool"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert test.returncode == 0, test.stderr
        combined = f"{test.stdout}\n{test.stderr}"
        assert "success" in combined.lower() or "connected" in combined.lower() or "tools" in combined.lower()
    finally:
        subprocess.run(
            [str(ironclaw_bin), "mcp", "remove", "ironclaw_tool"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()

