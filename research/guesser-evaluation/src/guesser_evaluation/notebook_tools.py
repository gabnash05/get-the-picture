'''Portable helpers for targeting the Guesser source package from notebooks.'''

from __future__ import annotations

from pathlib import Path


def module_source_path(filename: str, start: Path | None = None) -> Path:
    '''Return a Python module path inside the workspace's src package.

    The search accepts a starting directory inside either the repository root or
    the Guesser workspace, so notebook kernels can resolve the same source tree
    without hardcoded machine-specific paths.
    '''
    if (
        Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
        or Path(filename).suffix != ".py"
    ):
        raise ValueError("Pass a single .py filename in the package root.")

    current = (start or Path.cwd()).resolve()
    for parent in (current, *current.parents):
        for project_root in (parent, parent / "research" / "guesser-evaluation"):
            package_dir = project_root / "src" / "guesser_evaluation"
            if (project_root / "pyproject.toml").is_file() and package_dir.is_dir():
                return (package_dir / filename).resolve()

    raise FileNotFoundError("Could not locate the Guesser source package from this directory.")
