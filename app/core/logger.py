from __future__ import annotations

import datetime as _dt
from typing import Any


LEVEL_INFO = "INFO"
LEVEL_ERROR = "ERROR"


def _ts() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def log_info(message: str, **kwargs: Any) -> None:
    if kwargs:
        print(f"[{_ts()}] {LEVEL_INFO}: {message} | {kwargs}")
    else:
        print(f"[{_ts()}] {LEVEL_INFO}: {message}")


def log_error(message: str, **kwargs: Any) -> None:
    if kwargs:
        print(f"[{_ts()}] {LEVEL_ERROR}: {message} | {kwargs}")
    else:
        print(f"[{_ts()}] {LEVEL_ERROR}: {message}")
