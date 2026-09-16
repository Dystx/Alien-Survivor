#!/usr/bin/env python3
"""Validate the source, then run the pinned Godot engine. Never fake a skipped pass."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
VERSION = (ROOT / ".godot-version").read_text().strip()


def static_check() -> None:
    required = [GAME / "project.godot", GAME / "scenes/main.tscn", GAME / "tests/run_tests.gd"]
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Missing required file: {path}")
    references: set[str] = set()
    for path in GAME.rglob("*"):
        if not path.is_file() or ".godot" in path.parts:
            continue
        if path.suffix in {".gd", ".tscn", ".tres", ".godot"}:
            text = path.read_text(encoding="utf-8")
            if "\r" in text or "\x00" in text:
                raise RuntimeError(f"Invalid line ending or NUL in {path}")
            for reference in re.findall(r'res://[^"\s)]+', text):
                references.add(reference)
            for number, line in enumerate(text.splitlines(), 1):
                if re.match(r"^( +\t|\t+ +\S)", line):
                    raise RuntimeError(f"Mixed indentation at {path}:{number}")
    for reference in sorted(references):
        if not (GAME / reference.removeprefix("res://")).is_file():
            raise RuntimeError(f"Broken resource reference: {reference}")
    if not re.fullmatch(r"4\.\d+\.\d+", VERSION):
        raise RuntimeError("Invalid engine pin")
    print(f"STATIC PASS: {len(references)} resource references resolve; required files and text checks pass.")
    print("Static checks are NOT a GDScript parser, engine test, or performance test.")


def run(command: list[str], marker: str | None = None, expected_code: int = 0) -> None:
    print("RUN:", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=120, check=False)
    print(result.stdout, end="", flush=True)
    if result.returncode != expected_code:
        raise RuntimeError(f"Unexpected exit status {result.returncode}, expected {expected_code}")
    if re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:", result.stdout, re.MULTILINE):
        raise RuntimeError("Godot reported an engine/script error, even if its exit code was zero")
    if marker and marker not in result.stdout:
        raise RuntimeError(f"Expected completion marker was absent: {marker}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", default="godot")
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    try:
        static_check()
        if args.static_only:
            print("ENGINE IMPORT / TESTS / EXPORT: NOT RUN (--static-only).")
            return 0
        executable = shutil.which(args.godot)
        if not executable:
            print(f"BLOCKED: Godot {VERSION} not found. Install the standard editor and rerun.", file=sys.stderr)
            return 2
        actual = subprocess.check_output([executable, "--version"], text=True).strip()
        if not actual.startswith(VERSION + "."):
            raise RuntimeError(f"Wrong engine: {actual}; required {VERSION}")
        prefix = [executable, "--headless", "--path", str(GAME)]
        run(prefix + ["--editor", "--import", "--quit"])
        run(prefix + ["--script", "res://tests/run_tests.gd"], "ALIEN_SURVIVOR_TESTS:")
        run(prefix + ["--script", "res://tests/run_tests.gd", "--", "--self-test-failure"],
            "[FAIL] intentional runner self-check", expected_code=1)
        run(prefix + ["--verbose", "--fixed-fps", "60", "--", "--smoke"], "SCENE_SMOKE_PASS")
        print("ENGINE CHECKS PASS. Graphics, sound listening, controller and physical phones still need manual testing.")
        return 0
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"CHECK FAILED: {error}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
