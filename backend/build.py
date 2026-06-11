"""
AIIS-PMMS 后端打包脚本。

打包目标：
    - 使用 PyInstaller 打包生产入口 main.py。
    - 将 Alembic 迁移目录和 Template.xlsx 样例模板打入可执行包。
    - 在 dist 目录准备现场可编辑配置文件和运行期 storage 目录。
"""

from __future__ import annotations

import argparse
import importlib.util
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
REQUIRED_FILES = [
    BACKEND_ROOT / "main.py",
    BACKEND_ROOT / ".env.example",
    BACKEND_ROOT / "alembic.ini",
    BACKEND_ROOT / "alembic",
    PROJECT_ROOT / "resources" / "Template.xlsx",
]
HIDDEN_IMPORTS = [
    "aioodbc",
    "aiosqlite",
    "bcrypt",
    "greenlet",
    "multipart",
    "openpyxl",
    "pyodbc",
    "sqlalchemy.dialects.mssql.aioodbc",
    "sqlalchemy.dialects.mssql.pyodbc",
    "uvicorn.lifespan.on",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto",
]
COLLECT_SUBMODULES = [
    "alembic",
    "sqlalchemy.dialects.mssql",
    "uvicorn.lifespan",
    "uvicorn.protocols",
]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _remove_previous_output() -> None:
    print("步骤 2/5：清理旧的 build/dist 产物...")
    for path, parent in ((DIST_APP_DIR, DIST_ROOT), (BUILD_APP_DIR, BUILD_ROOT)):
        if path.exists():
            if not _is_within(path, parent):
                raise RuntimeError(f"拒绝删除后端目录外的路径：{path}")
            shutil.rmtree(path)


def _add_data(source: Path, target: str) -> str:
    return f"{source}{os.pathsep}{target}"


def _expected_executable() -> Path:
    return DIST_APP_DIR / (f"{APP_NAME}.exe" if os.name == "nt" else APP_NAME)


def _ensure_build_environment(*, include_env: bool) -> None:
    print("步骤 1/5：检查打包环境和必要资源...")

    if importlib.util.find_spec("PyInstaller") is None:
        raise RuntimeError(
            "当前 Python 环境没有 PyInstaller。请在 backend/ 目录执行："
            "uv run --with pyinstaller python build.py"
        )

    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    if include_env and not (BACKEND_ROOT / ".env").exists():
        missing.append(str(BACKEND_ROOT / ".env"))
    if missing:
        raise FileNotFoundError("以下打包必需文件不存在：\n" + "\n".join(missing))


def _run_pyinstaller() -> None:
    print("步骤 3/5：执行 PyInstaller 打包生产入口 main.py...")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--console",
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
    ]
    for module_name in HIDDEN_IMPORTS:
        command.extend(["--hidden-import", module_name])
    for package_name in COLLECT_SUBMODULES:
        command.extend(["--collect-submodules", package_name])
    command.append(str(BACKEND_ROOT / "main.py"))

    print("PyInstaller 命令：")
    print(" ".join(command))
    subprocess.run(command, cwd=BACKEND_ROOT, check=True)


def _prepare_site_files(*, include_env: bool) -> None:
    print("步骤 4/5：整理现场配置文件和运行目录...")
    DIST_APP_DIR.mkdir(parents=True, exist_ok=True)
    (DIST_APP_DIR / "storage" / "exports" / "templates").mkdir(parents=True, exist_ok=True)

    if include_env:
        source = BACKEND_ROOT / ".env"
        if not source.exists():
            raise FileNotFoundError("backend/.env 不存在，请去掉 --include-env 或先创建 .env。")
        shutil.copy2(source, DIST_APP_DIR / ".env")
    else:
        shutil.copy2(BACKEND_ROOT / ".env.example", DIST_APP_DIR / ".env.example")


def _packaged_data_exists(relative_path: str) -> bool:
    candidates = [
        DIST_APP_DIR / relative_path,
        DIST_APP_DIR / "_internal" / relative_path,
    ]
    return any(path.exists() for path in candidates)


def _verify_output(*, include_env: bool) -> None:
    print("步骤 5/5：校验打包产物结构...")

    expected_config = DIST_APP_DIR / (".env" if include_env else ".env.example")
    checks = {
        "可执行文件": _expected_executable(),
        "现场配置文件": expected_config,
        "导出目录": DIST_APP_DIR / "storage" / "exports" / "templates",
    }
    missing = [f"{name}: {path}" for name, path in checks.items() if not path.exists()]

    for relative_path in ("alembic.ini", "alembic", "resources/Template.xlsx"):
        if not _packaged_data_exists(relative_path):
            missing.append(f"包内资源: {relative_path}")

    if missing:
        raise RuntimeError("打包产物缺少以下内容：\n" + "\n".join(missing))


def main() -> int:
    parser = argparse.ArgumentParser(description="打包 AIIS-PMMS 后端可执行文件。")
    parser.add_argument(
        "--include-env",
        action="store_true",
        help="将 backend/.env 复制到 dist。仅用于受控现场交付包。",
    )
    args = parser.parse_args()

    try:
        os.chdir(BACKEND_ROOT)
        print("=== 开始打包 AIIS-PMMS 后端服务 ===")
        _ensure_build_environment(include_env=args.include_env)
        _remove_previous_output()
        _run_pyinstaller()
        _prepare_site_files(include_env=args.include_env)
        _verify_output(include_env=args.include_env)
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("\n打包失败：")
        print(exc)
        return 1

    config_hint = ".env" if args.include_env else ".env.example"
    executable = _expected_executable()
    print("\n打包完成。")
    print(f"产物目录：{DIST_APP_DIR}")
    print(f"可执行文件：{executable}")
    print(f"配置文件：{DIST_APP_DIR / config_hint}")
    print(f"启动命令：{executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
