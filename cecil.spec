# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for the Cecil single binary.

This spec bundles:
  - The Python CLI entry point (src/cecil/cli/__init__.py)
  - The React frontend build (src/cecil/ui_dist/)
  - NLP model files (Presidio/spaCy) — placeholder for future integration

Build with:
    pyinstaller cecil.spec --noconfirm --clean

Or via the orchestrator:
    python scripts/build.py
"""

from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(SPECPATH)
SRC_DIR = PROJECT_ROOT / "src" / "cecil"
UI_DIST_DIR = SRC_DIR / "ui_dist"


# ── Data files ────────────────────────────────────────────────────────────
# Each tuple is (source, destination_in_bundle).

datas = []

# React frontend bundle — served by the FastAPI static file handler.
if UI_DIST_DIR.exists():
    datas.append((str(UI_DIST_DIR), "ui_dist"))

# NLP models (Presidio / spaCy assets).
# TODO(#future): Uncomment and adjust once Presidio integration is complete.
# These paths will be populated after `python -m spacy download en_core_web_sm`
# or equivalent model installation.
#
# SPACY_MODEL_DIR = PROJECT_ROOT / "models" / "en_core_web_sm"
# if SPACY_MODEL_DIR.exists():
#     datas.append((str(SPACY_MODEL_DIR), "models/en_core_web_sm"))
#
# PRESIDIO_DATA_DIR = PROJECT_ROOT / "models" / "presidio"
# if PRESIDIO_DATA_DIR.exists():
#     datas.append((str(PRESIDIO_DATA_DIR), "models/presidio"))


# ── Hidden imports ────────────────────────────────────────────────────────
# Modules that PyInstaller's static analysis cannot detect automatically.

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    # TODO(#future): Add Presidio / spaCy hidden imports when integrated:
    # "presidio_analyzer",
    # "presidio_anonymizer",
    # "spacy",
]


# ── Excludes ──────────────────────────────────────────────────────────────
# Modules not needed at runtime — reduces binary size.

excludes = [
    "tkinter",
    "unittest",
    "test",
    "xmlrpc",
    "pydoc",
    "doctest",
]


# ── Analysis ──────────────────────────────────────────────────────────────

a = Analysis(
    [str(SRC_DIR / "cli" / "__init__.py")],
    pathex=[str(PROJECT_ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)


# ── Executable ────────────────────────────────────────────────────────────

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="cecil",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,  # Set via environment for macOS signing
    entitlements_file=None,  # Set via environment for macOS notarization
)
