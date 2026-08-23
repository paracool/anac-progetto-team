from __future__ import annotations

import json
import os
import stat
import shutil
import time
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rmtree_onerror(func, target_path, exc_info) -> None:
    # On Windows/OneDrive some entries can be read-only during sync.
    if isinstance(exc_info[1], PermissionError):
        try:
            os.chmod(target_path, stat.S_IWRITE)
            func(target_path)
            return
        except OSError:
            pass
    raise exc_info[1]


def reset_dir(path: Path) -> Path:
    if path.exists():
        for attempt in range(3):
            try:
                shutil.rmtree(path, onerror=_rmtree_onerror)
                break
            except PermissionError:
                if attempt == 2:
                    raise
                time.sleep(0.2 * (attempt + 1))
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_text(path: Path, encoding: str = "utf-8") -> str:
    return path.read_text(encoding=encoding)


def write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    ensure_dir(path.parent)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding=encoding)
    temp.replace(path)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, data: Any, *, indent: int = 2) -> None:
    ensure_dir(path.parent)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=indent, default=str)
        stream.write("\n")
    temp.replace(path)


def copy_file(source: Path, destination: Path) -> None:
    ensure_dir(destination.parent)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path) -> None:
    if source.exists():
        shutil.copytree(source, destination, dirs_exist_ok=True)
