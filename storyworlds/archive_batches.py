#!/usr/bin/env python3
"""Create a gzip tar archive of local storyworld Batch artifacts.

The raw Batch JSONL files are intentionally ignored by git because they are
large and frequently regenerated. This script bundles them into a single
archive that can be tracked with Git LFS when we want a durable snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATCH_DIR = ROOT / "storyworlds" / "batches"
DEFAULT_ARCHIVE_DIR = ROOT / "storyworlds" / "batch_archives"
DEFAULT_EXTRA_FILES = [
    ROOT / "storyworlds" / "openai_batch_world_factory.py",
    ROOT / "storyworlds" / "repair_batch_output.py",
    ROOT / "storyworlds" / "archive_batches.py",
    ROOT / "storyworlds" / "README.md",
    ROOT / "storyworlds" / "TODO.md",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-dir",
        type=Path,
        default=DEFAULT_BATCH_DIR,
        help=f"directory containing ignored Batch artifacts; default: {DEFAULT_BATCH_DIR}",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=DEFAULT_ARCHIVE_DIR,
        help=f"where to write archives; default: {DEFAULT_ARCHIVE_DIR}",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="exact archive path; default uses UTC timestamp under --archive-dir",
    )
    parser.add_argument(
        "--extra-file",
        type=Path,
        action="append",
        default=[],
        help="additional file to include; may be repeated",
    )
    parser.add_argument(
        "--no-default-extras",
        action="store_true",
        help="only include batch files plus explicit --extra-file paths",
    )
    return parser


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def collect_files(batch_dir: Path, extras: list[Path]) -> list[Path]:
    files: list[Path] = []
    if batch_dir.exists():
        files.extend(path for path in sorted(batch_dir.iterdir()) if path.is_file())
    files.extend(path for path in extras if path.exists() and path.is_file())
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def default_archive_path(archive_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return archive_dir / f"storyworld_batches_{stamp}.tar.gz"


def main() -> int:
    args = build_parser().parse_args()
    batch_dir = args.batch_dir.resolve()
    archive_path = (args.out.resolve() if args.out else default_archive_path(args.archive_dir))
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    extras = [] if args.no_default_extras else list(DEFAULT_EXTRA_FILES)
    extras.extend(path if path.is_absolute() else ROOT / path for path in args.extra_file)
    files = collect_files(batch_dir, extras)
    if not files:
        raise SystemExit(f"No files found under {batch_dir}")

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "created_at": created_at,
        "root": str(ROOT),
        "batch_dir": rel(batch_dir),
        "archive": archive_path.name,
        "file_count": len(files),
        "files": [
            {
                "path": rel(path),
                "size": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files
        ],
    }

    with tarfile.open(archive_path, "w:gz") as tar:
        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
        info = tarfile.TarInfo("ARCHIVE_MANIFEST.json")
        info.size = len(manifest_bytes)
        info.mtime = int(datetime.now(timezone.utc).timestamp())
        tar.addfile(info, fileobj=__import__("io").BytesIO(manifest_bytes))
        for path in files:
            tar.add(path, arcname=rel(path), recursive=False)

    print(f"Wrote {archive_path}")
    print(f"Archived {len(files)} files")
    print(f"Size: {archive_path.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
