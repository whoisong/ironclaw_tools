from __future__ import annotations

import subprocess
from pathlib import Path


def test_real_ironclaw_binary_runs() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    binary = workspace_root / "repos" / "ironclaw" / "target" / "release" / "ironclaw.exe"
    assert binary.exists(), f"Expected binary at {binary}"

    version = subprocess.run(
        [str(binary), "--version"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert version.returncode == 0, version.stderr
    assert "ironclaw" in version.stdout.lower()

    status = subprocess.run(
        [str(binary), "status", "--no-db", "--no-onboard", "--cli-only"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert status.returncode == 0, status.stderr
    assert "IronClaw Status" in status.stdout

