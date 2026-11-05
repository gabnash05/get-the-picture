import sys

import guesser_evaluation


def test_workspace_uses_supported_python_minor() -> None:
    assert sys.version_info[:2] == (3, 12)


def test_workspace_package_is_importable() -> None:
    assert guesser_evaluation.__file__ is not None
