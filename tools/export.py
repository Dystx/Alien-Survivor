#!/usr/bin/env python3
"""Check first, then export using templates/SDK installed on the local machine."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("platform", choices=["windows", "linux", "android"])
    parser.add_argument("--godot", default="godot")
    args = parser.parse_args()
    godot = shutil.which(args.godot)
    if not godot:
        print("Godot is missing. Install the pinned editor and matching export templates.", file=sys.stderr)
        return 2
    check = subprocess.run([sys.executable, str(ROOT / "tools/check.py"), "--godot", godot], check=False)
    if check.returncode:
        return check.returncode
    preset, filename = {
        "windows": ("Windows Desktop", "AlienSurvivor.exe"),
        "linux": ("Linux", "AlienSurvivor.x86_64"),
        "android": ("Android Debug", "AlienSurvivor-debug.apk"),
    }[args.platform]
    destination = ROOT / "builds" / args.platform / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    option = "--export-debug" if args.platform == "android" else "--export-release"
    result = subprocess.run([godot, "--headless", "--path", str(ROOT / "game"), option, preset, str(destination)], check=False)
    if result.returncode or not destination.is_file() or destination.stat().st_size == 0:
        print("Export failed or did not produce a nonempty artifact.", file=sys.stderr)
        return result.returncode or 1
    print(f"Export created: {destination}\nThis is not proof of testing on the destination device.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
