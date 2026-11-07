"""Tests for the guarded data-project environment access."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from guesser_evaluation import data_environment


def completed(returncode: int, stderr: str = "") -> SimpleNamespace:
    """Report an environment probe outcome the way subprocess.run does."""
    return SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)


def test_probe_stays_read_only_and_targets_the_data_project(tmp_path: Path) -> None:
    """Check the installation without syncing or updating the lockfile."""
    with patch.object(
        data_environment.subprocess, "run", return_value=completed(0)
    ) as run:
        data_environment.require_data_environment(tmp_path, cwd=tmp_path)

    command = run.call_args.args[0]
    assert command[:3] == ["uv", "run", "--project"]
    assert command[3] == str(tmp_path)
    assert "--no-sync" in command
    assert "--frozen" in command
    assert command[-1] == "import guesser_data"
    assert run.call_args.kwargs["cwd"] == str(tmp_path)
    assert run.call_args.kwargs["capture_output"] is True


def test_unsynced_environment_names_the_sync_command(tmp_path: Path) -> None:
    """Turn uv's spawn error into the documented one-time setup step."""
    failure = completed(
        1,
        "error: Failed to spawn: guesser-data\n"
        "  cause: No such file or directory (os error 2)",
    )
    with (
        patch.object(data_environment.subprocess, "run", return_value=failure),
        pytest.raises(RuntimeError) as caught,
    ):
        data_environment.require_data_environment(tmp_path, cwd=tmp_path)

    message = str(caught.value)
    assert data_environment.SYNC_COMMAND in message
    assert str(tmp_path) in message
    # Keep the probe's own diagnosis available for cases the hint does not cover.
    assert "Failed to spawn: guesser-data" in message
