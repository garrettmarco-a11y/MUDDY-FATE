"""Setup smoke tests.

These check the development environment, not gameplay: that the test run uses
a supported Python, that the ``game`` package is installed in the active
environment, and that ``import game`` resolves to this repository's
``src/game`` rather than some other package with the same name.
"""

import importlib.metadata
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_NAME = "new-game-prototype"  # [project].name in pyproject.toml


def test_python_version_is_supported():
    assert sys.version_info >= (3, 11), (
        f"Python 3.11+ is required; tests are running on {sys.version.split()[0]}"
    )


def test_package_is_installed_in_active_environment():
    # pytest's `pythonpath = ["src"]` lets `import game` succeed even without
    # an install, so check the distribution metadata explicitly.
    try:
        importlib.metadata.distribution(DIST_NAME)
    except importlib.metadata.PackageNotFoundError:
        raise AssertionError(
            f"'{DIST_NAME}' is not installed in {sys.prefix}. Activate the "
            'project virtual environment and run: python -m pip install -e ".[dev]"'
        ) from None


def test_game_imports_from_this_repository():
    import game

    expected = PROJECT_ROOT / "src" / "game"
    actual = Path(game.__file__).resolve().parent
    assert actual == expected, f"'game' was imported from {actual}, expected {expected}"
