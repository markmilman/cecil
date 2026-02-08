"""Resource path resolution for PyInstaller and development environments.

Provides ``get_resource_path()`` to resolve bundled assets (UI files, NLP
models) at runtime, transparently handling both development mode and
PyInstaller single-binary distribution.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


logger = logging.getLogger(__name__)

# The source root when running in development (i.e., the ``src/cecil/`` directory).
_DEV_BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Sentinel attribute set by PyInstaller at runtime.
_MEIPASS_ATTR: str = "_MEIPASS"


def is_frozen() -> bool:
    """Check whether the application is running inside a PyInstaller bundle.

    Returns:
        True if running from a frozen PyInstaller executable, False otherwise.
    """
    return getattr(sys, "frozen", False) is True and hasattr(sys, _MEIPASS_ATTR)


def get_base_path() -> Path:
    """Return the base path for resolving bundled resources.

    In a PyInstaller bundle, this is ``sys._MEIPASS`` (the temporary
    extraction directory). In development, this is the ``src/cecil/``
    package directory.

    Returns:
        The base directory from which relative resource paths are resolved.
    """
    if is_frozen():
        meipass: str = getattr(sys, _MEIPASS_ATTR)
        base = Path(meipass)
        logger.debug("Running in frozen mode, base_path=%s", base)
        return base

    logger.debug("Running in development mode, base_path=%s", _DEV_BASE_DIR)
    return _DEV_BASE_DIR


def get_resource_path(relative_path: str) -> Path:
    """Resolve a relative path to a bundled resource.

    In a PyInstaller single-binary, resources are extracted to a temporary
    directory (``sys._MEIPASS``). In development, they live under
    ``src/cecil/``. This function abstracts that difference so callers can
    refer to assets like ``ui_dist/index.html`` without caring about the
    runtime environment.

    Args:
        relative_path: A forward-slash-separated path relative to the
            resource base directory (e.g., ``"ui_dist/index.html"`` or
            ``"models/en_core_web_sm"``).

    Returns:
        An absolute ``Path`` to the resolved resource.

    Raises:
        FileNotFoundError: If the resolved path does not exist on disk.

    Example:
        >>> path = get_resource_path("ui_dist/index.html")
        >>> path.is_file()
        True
    """
    base = get_base_path()
    resolved = base / relative_path
    logger.debug(
        "Resolving resource path, relative=%s, resolved=%s",
        relative_path,
        resolved,
    )
    if not resolved.exists():
        msg = (
            f"Resource not found: {relative_path!r} (resolved to {resolved}, frozen={is_frozen()})"
        )
        raise FileNotFoundError(msg)
    return resolved


def get_ui_dist_path() -> Path:
    """Return the path to the bundled React UI distribution directory.

    This is a convenience wrapper around ``get_resource_path()`` for the
    most common asset lookup: the ``ui_dist/`` directory containing the
    built React frontend.

    Returns:
        The absolute path to the ``ui_dist/`` directory.

    Raises:
        FileNotFoundError: If the ``ui_dist/`` directory does not exist.
    """
    return get_resource_path("ui_dist")
