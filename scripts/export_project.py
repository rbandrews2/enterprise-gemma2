#!/usr/bin/env python3
"""Export this project into a local working folder without deleting local files."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".idea",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}

SKIP_FILES = {
    ".env",
    ".env.local",
    ".DS_Store",
}


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in rel.parts):
        return True
    return path.name in SKIP_FILES


def copy_project(destination: Path) -> list[Path]:
    destination = destination.expanduser().resolve()
    copied: list[Path] = []

    if destination == ROOT:
        raise SystemExit("Destination is the project root; choose another folder.")

    destination.mkdir(parents=True, exist_ok=True)

    for source in ROOT.rglob("*"):
        if should_skip(source):
            continue

        target = destination / source.relative_to(ROOT)
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(target)

    ensure_env_local(destination)
    write_readme(destination)
    return copied


def ensure_env_local(destination: Path) -> None:
    env_local = destination / ".env.local"
    if env_local.exists():
        return

    env_example = destination / ".env.example"
    if env_example.exists():
        shutil.copy2(env_example, env_local)
    else:
        env_local.write_text(
            "# Local environment values for Google Cloud deployment.\n"
            "# Keep this file out of git and fill values before running locally.\n",
            encoding="utf-8",
        )


def write_readme(destination: Path) -> None:
    (destination / "README_LOCAL_SYNC.txt").write_text(
        "Local project export created by scripts/export_project.py.\n"
        "Existing .env and .env.local files are preserved.\n"
        "Runtime folders such as .git, __pycache__, and node_modules are skipped.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy this project to a local folder without deleting destination-only files."
    )
    parser.add_argument("destination", help="Destination folder, for example C:\\Users\\ray\\enterprise-gemma2")
    args = parser.parse_args()

    copied = copy_project(Path(args.destination))
    print(f"Copied {len(copied)} files into {Path(args.destination).expanduser().resolve()}")


if __name__ == "__main__":
    main()
