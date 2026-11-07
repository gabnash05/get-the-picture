"""Guard access to the data project's separate uv environment."""

from __future__ import annotations

import subprocess
from pathlib import Path

# Documented one-time setup for the data package's Python 3.13 environment.
SYNC_COMMAND = "uv sync --project models/guesser/data --frozen"


def _probe_command(data_project: str | Path) -> list[str]:
    """Build the read-only installation check for the data project's environment."""
    return [
        "uv",
        "run",
        "--project",
        str(data_project),
        "--frozen",
        "--no-sync",
        "python",
        "-c",
        "import guesser_data",
    ]


def require_data_environment(data_project: str | Path, *, cwd: str | Path) -> None:
    """Raise an actionable error unless the data package is installed in its uv environment.

    Notebook helpers call `uv run --no-sync` so they never change the live data
    environment. A never-synced environment therefore looks like a missing module
    or a missing console script, so check the installation first and name the fix
    instead of leaving callers to interpret uv's spawn error.
    """
    # The probe may create an empty environment, so keep its notice out of the output.
    result = subprocess.run(
        _probe_command(data_project),
        capture_output=True,
        check=False,
        cwd=str(cwd),
        text=True,
    )
    if result.returncode == 0:
        return

    detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
    raise RuntimeError(
        "The data project's uv environment does not have guesser_data installed: "
        f"{data_project}\n"
        f"Run `{SYNC_COMMAND}` from the repository root while no data command is "
        "running, then retry.\n"
        "Data helpers use --no-sync by design and never install packages themselves.\n"
        f"Environment probe failed with:\n{detail}"
    )
