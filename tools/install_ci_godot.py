#!/usr/bin/env python3
"""Install the pinned Linux editor from the official release; verify its published digest."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / ".godot-version").read_text().strip()
DEST = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/alien-survivor-godot").resolve()


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "AlienSurvivor-build-check"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def main() -> None:
    if not re.fullmatch(r"4\.\d+\.\d+", VERSION):
        raise RuntimeError("Unexpected version string")
    metadata = json.loads(get(f"https://api.github.com/repos/godotengine/godot-builds/releases/tags/{VERSION}-stable"))
    name = f"Godot_v{VERSION}-stable_linux.x86_64.zip"
    assets = {asset["name"]: asset for asset in metadata["assets"]}
    if name not in assets:
        raise RuntimeError(f"Pinned release lacks {name}; do not silently change the engine")
    payload = get(assets[name]["browser_download_url"])
    digest = assets[name].get("digest") or ""
    if digest.startswith("sha256:"):
        if hashlib.sha256(payload).hexdigest() != digest.split(":", 1)[1]:
            raise RuntimeError("Editor SHA-256 mismatch")
    else:
        manifest_asset = assets.get("SHA512-SUMS.txt")
        if not manifest_asset:
            raise RuntimeError("No published digest found; refusing an unchecked installation")
        lines = get(manifest_asset["browser_download_url"]).decode().splitlines()
        checksums = {parts[-1].lstrip("*"): parts[0] for line in lines if len(parts := line.split()) == 2}
        if hashlib.sha512(payload).hexdigest() != checksums.get(name):
            raise RuntimeError("Editor SHA-512 mismatch")
    DEST.mkdir(parents=True, exist_ok=True)
    archive = DEST / "editor.zip"
    archive.write_bytes(payload)
    binary_name = name.removesuffix(".zip")
    with zipfile.ZipFile(archive) as package:
        # Extract exactly one known file; never trust archive traversal paths.
        (DEST / "godot").write_bytes(package.read(binary_name))
    (DEST / "godot").chmod(0o755)
    print(f"Verified Godot {VERSION}: {DEST / 'godot'}")

if __name__ == "__main__":
    main()
