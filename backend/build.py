"""
File Path: /backend/build.py
Description: PyInstaller build entry for the packaged AIIS-PMMS backend.
Main Features:
    - Build the production FastAPI entry on Windows or host-local environments
    - Bundle Alembic migrations and sample Excel resources
    - Prepare editable site configuration and storage directories in dist
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


APP_NAME = "aiis-pmms-backend"
BACKEND_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_ROOT.parent
DIST_ROOT = BACKEND_ROOT / "dist"
BUILD_ROOT = BACKEND_ROOT / "build"
DIST_APP_DIR = DIST_ROOT / APP_NAME
BUILD_APP_DIR = BUILD_ROOT / APP_NAME


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _remove_previous_output() -> None:
    for path, parent in ((DIST_APP_DIR, DIST_ROOT), (BUILD_APP_DIR, BUILD_ROOT)):
        if path.exists():
            if not _is_within(path, parent):
                raise RuntimeError(f"Refusing to remove path outside {parent}: {path}")
            shutil.rmtree(path)


def _add_data(source: Path, target: str) -> str:
    return f"{source}{os.pathsep}{target}"


def _run_pyinstaller() -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        APP_NAME,
        "--distpath",
        str(DIST_ROOT),
        "--workpath",
        str(BUILD_ROOT),
        "--specpath",
        str(BUILD_ROOT),
        "--add-data",
        _add_data(BACKEND_ROOT / "alembic.ini", "."),
        "--add-data",
        _add_data(BACKEND_ROOT / "alembic", "alembic"),
        "--add-data",
        _add_data(PROJECT_ROOT / "resources" / "Template.xlsx", "resources"),
        "--hidden-import",
        "pyodbc",
        "--hidden-import",
        "aioodbc",
        "--hidden-import",
        "aiosqlite",
        str(BACKEND_ROOT / "main.py"),
    ]
    subprocess.run(command, cwd=BACKEND_ROOT, check=True)


def _prepare_site_files(*, include_env: bool) -> None:
    DIST_APP_DIR.mkdir(parents=True, exist_ok=True)
    (DIST_APP_DIR / "storage" / "exports" / "templates").mkdir(parents=True, exist_ok=True)

    if include_env:
        source = BACKEND_ROOT / ".env"
        if not source.exists():
            raise FileNotFoundError("backend/.env does not exist; omit --include-env or create it first.")
        shutil.copy2(source, DIST_APP_DIR / ".env")
    else:
        shutil.copy2(BACKEND_ROOT / ".env.example", DIST_APP_DIR / ".env.example")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the AIIS-PMMS backend executable.")
    parser.add_argument(
        "--include-env",
        action="store_true",
        help="Copy backend/.env into dist. Use only for a controlled site package.",
    )
    args = parser.parse_args()

    os.chdir(BACKEND_ROOT)
    _remove_previous_output()
    _run_pyinstaller()
    _prepare_site_files(include_env=args.include_env)

    config_hint = ".env" if args.include_env else ".env.example"
    executable = DIST_APP_DIR / (f"{APP_NAME}.exe" if os.name == "nt" else APP_NAME)
    print(f"Build completed: {DIST_APP_DIR}")
    print(f"Executable: {executable}")
    print(f"Configuration template: {DIST_APP_DIR / config_hint}")
    print(f"Run command: {executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
