#!/usr/bin/env python3
"""
Scaffold an offline deployment bundle for Astra Linux 1.7 from Windows.

- Creates folders and EMPTY placeholder files (no content).
- Targets air-gapped install: Docker .deb packages, saved images, compose stack, app files.
- Safe to run on Windows (PyCharm). Uses pathlib, no external deps.

Usage:
    python scaffold_offline_bundle.py [BUNDLE_NAME] [--force]

Example:
    python scaffold_offline_bundle.py airgap-siem
"""

from __future__ import annotations
import argparse
import datetime as dt
import os
from pathlib import Path
import sys
from typing import Iterable

# ----------------------------- config ---------------------------------

# Directory layout
DIRS: list[str] = [
    "images",
    "images/base-os-images",
    "packages/deb/docker",
    "packages/keys",
    "compose",
    "compose/overrides",
    "app/bin",
    "app/config",
    "app/service",
    "app/health",
    "app/files",
    "docs",
    "support/checksums",
    "support/license",
    "test",
    "tools",
    "local-apt-repo/dists/stable/main/binary-amd64",
    "local-apt-repo/dists/stable/main/binary-arm64",
    "local-apt-repo/pool/main/d/docker",
    "tmp",
]

# Plain empty files
FILES: list[str] = [
    # top-level
    "manifest.yaml",
    "Makefile",
    ".gitignore",
    "VERSION",

    # packages
    "packages/deb/docker/containerd.io_VERSION_arch.deb",
    "packages/deb/docker/docker-ce_VERSION_arch.deb",
    "packages/deb/docker/docker-ce-cli_VERSION_arch.deb",
    "packages/deb/docker/docker-buildx-plugin_VERSION_arch.deb",
    "packages/deb/docker/docker-compose-plugin_VERSION_arch.deb",
    "packages/keys/docker.gpg",
    "packages/keys/astra.gpg",

    # images
    "images/siem-astra-agent.tar",
    "images/base-os-images/ubuntu_base_optional.tar",

    # compose
    "compose/docker-compose.yml",
    "compose/.env",
    "compose/overrides/docker-compose.offline.yml",

    # app
    "app/service/siem-astra-agent.service",
    "app/config/config.yaml",
    "app/config/.env.sample",
    "app/files/Dockerfile",
    "app/files/agent.py",
    "app/files/requirements.txt",
    "app/files/README.md",

    # docs
    "docs/OFFLINE_INSTALL.md",
    "docs/AIRGAP_CHECKLIST.md",
    "docs/RECOVERY.md",
    "docs/SECURITY_NOTES.md",

    # support
    "support/checksums/SHA256SUMS",
    "support/checksums/SHA256SUMS.sig",
    "support/license/LICENSE",
    "support/license/THIRD_PARTY_NOTICES.txt",

    # test
    "test/sandbox.env",

    # local apt repo metadata
    "local-apt-repo/Release",
    "local-apt-repo/dists/stable/Release",
    "local-apt-repo/dists/stable/main/binary-amd64/Packages.gz",
    "local-apt-repo/dists/stable/main/binary-arm64/Packages.gz",

    # tmp
    "tmp/.keep",
]

# Files that should be executable on Linux (we still create them EMPTY on Windows)
EXECUTABLES: list[str] = [
    "app/bin/install.sh",
    "app/bin/uninstall.sh",
    "app/bin/preflight.sh",
    "app/bin/postinstall.sh",
    "app/bin/load-images.sh",
    "app/bin/install-docker.sh",
    "app/bin/configure-systemd.sh",
    "app/bin/verify.sh",
    "app/health/healthcheck.sh",
    "test/smoke.sh",
    "tools/seed-apt-repo.sh",
    "tools/verify-checksums.sh",
]

# -------------------------- helpers -----------------------------------

def make_dirs(base: Path, dirs: Iterable[str]) -> int:
    created = 0
    for d in dirs:
        p = (base / d).resolve()
        p.mkdir(parents=True, exist_ok=True)
        created += 1
    return created

def touch_empty(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Create empty file; avoid overwriting timestamps unnecessarily
    if not path.exists():
        path.touch()
    else:
        # Ensure it's a regular file (not directory)
        if path.is_dir():
            raise IsADirectoryError(str(path))

def make_files(base: Path, files: Iterable[str]) -> int:
    created = 0
    for f in files:
        p = (base / f).resolve()
        touch_empty(p)
        created += 1
    return created

def make_execs(base: Path, files: Iterable[str]) -> int:
    """Create empty files and (best-effort) mark as executable for Linux."""
    created = 0
    for f in files:
        p = (base / f).resolve()
        touch_empty(p)
        try:
            # On Windows this is best-effort; real +x will be effective after extraction on Linux
            os.chmod(p, 0o755)
        except Exception:
            # Ignore permission quirks on Windows
            pass
        created += 1
    return created

# --------------------------- main -------------------------------------

def parse_args() -> argparse.Namespace:
    default_name = f"bundle-{dt.datetime.now().strftime('%Y%m%d')}"
    ap = argparse.ArgumentParser(
        description="Create an offline scaffold for Astra Linux 1.7 deployment (from Windows)."
    )
    ap.add_argument("bundle_name", nargs="?", default=default_name,
                    help="Name of the output folder to create (default: %(default)s)")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite target folder if it exists (files will be created/kept, never deleted).")
    return ap.parse_args()

def main() -> int:
    args = parse_args()
    base = Path.cwd() / args.bundle_name

    if base.exists() and not args.force:
        # If exists and not empty, warn the user
        if any(base.iterdir()):
            print(f"✋ Target folder exists and is not empty: {base}\n"
                  f"   Re-run with --force to proceed anyway.", file=sys.stderr)
            return 2

    base.mkdir(parents=True, exist_ok=True)

    n_dirs = make_dirs(base, DIRS)
    n_execs = make_execs(base, EXECUTABLES)
    n_files = make_files(base, FILES)

    print("✓ Scaffold created")
    print(f"  Base:   {base}")
    print(f"  Dirs:   {n_dirs}")
    print(f"  Files:  {n_files} + Exec stubs: {n_execs}")
    print("\nNext steps (on your online workstation):")
    print("  1) Put Astra Linux 1.7 compatible Docker .deb packages into packages/deb/docker/")
    print("  2) Put docker saved images into images/ (e.g., siem-astra-agent.tar)")
    print("  3) Fill compose/docker-compose.yml, app/config/config.yaml, and .env")
    print("  4) (Optional) Build a local APT repo in local-apt-repo/ and generate Packages.gz")
    print("  5) Archive the whole folder and transfer to the air-gapped host.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
