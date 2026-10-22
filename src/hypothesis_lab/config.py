"""Load optional local credentials without overriding the process environment."""

import os
from pathlib import Path


def load_environment(path: Path | str = ".env") -> None:
    """Read plain KEY=value entries; never execute shell syntax or expose values."""
    source = Path(path)
    if not source.is_file():
        return
    for line in source.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.removeprefix("export ").split("=", 1)
        name, value = name.strip(), value.strip()
        if not name.isidentifier():
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].rstrip()
        os.environ.setdefault(name, value)


load_environment()
