"""Remove every artefact created by setup_demo.py."""

from __future__ import annotations

import shutil
from pathlib import Path

DEMO_ROOT: Path = Path.home() / "wbc-sandbox-demo"


def main() -> int:
    injected = Path(__file__).resolve().parent / "vendor-docs" / "UPGRADE_NOTES.md"
    if injected.exists():
        injected.unlink()
        print(f"  removed  {injected}")

    if DEMO_ROOT.exists():
        shutil.rmtree(DEMO_ROOT)
        print(f"  removed  {DEMO_ROOT}")
    else:
        print(f"  nothing to remove at {DEMO_ROOT}")

    print("\nDemo artefacts cleaned up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
