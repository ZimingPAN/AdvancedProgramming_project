from __future__ import annotations

from pathlib import Path
import runpy
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python run.py main.py")
        return 1

    target = Path(sys.argv[1]).expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target

    if not target.exists():
        print(f"Target script not found: {target}")
        return 1

    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
