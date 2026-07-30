"""Loading targets and getting their files onto disk.

Proposals need real file paths and real line numbers, which means a real
checkout rather than a fetched URL. Targets are therefore git repositories,
cloned shallow, and gates run against working files.

Benchmark targets are the exception: they exist only to give the scores a
reference point and are fetched, scored, and never proposed against.
"""

from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

import yaml

USER_AGENT = "docs-quality-monitor (+https://github.com/grzetich/docs-quality-monitor)"


def load_config(root: Path) -> dict:
    with open(root / "targets.yml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def clone(repo: str, ref: str, dest: Path, timeout: int = 300) -> tuple[bool, str]:
    """Shallow clone a repository. Returns (ok, message)."""
    if dest.exists():
        shutil.rmtree(dest)
    cmd = [
        "git", "clone", "--depth", "1", "--quiet",
        "--branch", ref, repo, str(dest),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"clone exceeded {timeout}s"
    except FileNotFoundError:
        return False, "git is not installed"
    if proc.returncode != 0:
        return False, f"clone failed: {proc.stderr.strip()[:200]}"
    return True, "cloned"


def head_sha(path: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=30,
        )
        return proc.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def collect_files(root: Path, patterns: list[str], limit: int = 400) -> list[Path]:
    """Return repo files matching any glob, skipping vendored directories."""
    skip_dirs = {".git", "node_modules", "vendor", "dist", "build",
                 ".venv", "venv", "__pycache__", "target"}
    hits: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for name in filenames:
            full = Path(dirpath) / name
            rel = str(full.relative_to(root))
            if any(fnmatch.fnmatch(rel, pat) for pat in patterns):
                hits.append(full)
                if len(hits) >= limit:
                    return sorted(hits)
    return sorted(hits)


def fetch_url(url: str, dest: Path, timeout: int = 60, min_bytes: int = 1024
              ) -> tuple[bool, str]:
    """Download a benchmark artifact. Returns (ok, message)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    except Exception as exc:
        return False, f"fetch failed: {exc}"
    size = dest.stat().st_size
    if size < min_bytes:
        return False, f"fetch returned {size} bytes, below the {min_bytes} floor"
    return True, f"fetched {size:,} bytes"
