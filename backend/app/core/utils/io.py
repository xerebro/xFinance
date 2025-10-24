"""I/O helpers for caching and persistence to local storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..db import models


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def dump_json(path: Path, payload: Any, *, indent: int | None = None) -> None:
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=indent, ensure_ascii=False)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


__all__ = ["ensure_directory", "dump_json", "load_json", "models"]
