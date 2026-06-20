#!/usr/bin/env python3
"""Create gzip tar archives of local storyworld Batch artifacts.

The raw Batch JSONL files are intentionally ignored by git because they are
large and frequently regenerated. This script bundles one Batch run at a time
into an archive that can be tracked with Git LFS when we want a durable
snapshot.
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
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--batch-id",
        help="OpenAI Batch id to archive, e.g. batch_...",
    )
    scope.add_argument(
        "--manifest",
        type=Path,
        help="manifest JSON for the Batch run to archive",
    )
    scope.add_argument(
        "--all-batches",
        action="store_true",
        help="legacy mode: archive every direct file under --batch-dir",
    )
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


def collect_all_batch_files(batch_dir: Path, extras: list[Path]) -> list[Path]:
    files: list[Path] = []
    if batch_dir.exists():
        files.extend(path for path in sorted(batch_dir.iterdir()) if path.is_file())
    files.extend(path for path in extras if path.exists() and path.is_file())
    return unique_paths(files)


def unique_paths(files: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"Manifest is not a JSON object: {path}")
    if "jobs" not in data:
        raise SystemExit(f"Manifest does not look like a Batch manifest: {path}")
    return data


def find_manifest_for_batch(batch_dir: Path, batch_id: str) -> tuple[Path, dict]:
    matches: list[tuple[Path, dict]] = []
    for path in sorted(batch_dir.glob("*.manifest.json")):
        try:
            manifest = load_manifest(path)
        except (OSError, json.JSONDecodeError, SystemExit):
            continue
        if manifest.get("batch_id") == batch_id:
            matches.append((path.resolve(), manifest))
    if not matches:
        raise SystemExit(f"No manifest under {batch_dir} has batch_id={batch_id!r}")
    if len(matches) > 1:
        names = ", ".join(rel(path) for path, _ in matches)
        raise SystemExit(f"Multiple manifests matched {batch_id!r}: {names}")
    return matches[0]


def manifest_input_path(batch_dir: Path, manifest: dict) -> Path | None:
    jsonl_path = manifest.get("jsonl_path")
    if not jsonl_path:
        return None
    path = Path(jsonl_path)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def collect_one_batch_files(
    batch_dir: Path,
    manifest_path: Path,
    manifest: dict,
    extras: list[Path],
) -> list[Path]:
    files: list[Path] = [manifest_path.resolve()]

    input_path = manifest_input_path(batch_dir, manifest)
    if input_path and input_path.exists():
        files.append(input_path)

    batch_id = manifest.get("batch_id")
    if batch_id:
        files.extend(path.resolve() for path in sorted(batch_dir.glob(f"{batch_id}*")) if path.is_file())
        files.extend(path.resolve() for path in sorted(batch_dir.glob(f"*{batch_id}*")) if path.is_file())

    stem = manifest_path.name.removesuffix(".manifest.json")
    files.extend(path.resolve() for path in sorted(batch_dir.glob(f"{stem}*")) if path.is_file())

    files.extend(path.resolve() for path in extras if path.exists() and path.is_file())
    return unique_paths(files)


def default_archive_path(archive_dir: Path, manifest_path: Path | None = None, batch_id: str | None = None) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if manifest_path is not None:
        stem = manifest_path.name.removesuffix(".manifest.json")
        suffix = f"_{batch_id}" if batch_id else ""
        return archive_dir / f"{stem}{suffix}_{stamp}.tar.gz"
    return archive_dir / f"storyworld_batches_all_{stamp}.tar.gz"


def main() -> int:
    args = build_parser().parse_args()
    batch_dir = args.batch_dir.resolve()
    extras = [] if args.no_default_extras else list(DEFAULT_EXTRA_FILES)
    extras.extend(path if path.is_absolute() else ROOT / path for path in args.extra_file)

    manifest_path: Path | None = None
    manifest: dict | None = None
    batch_id: str | None = None
    archive_kind = "all_batches" if args.all_batches else "single_batch"

    if args.all_batches:
        files = collect_all_batch_files(batch_dir, extras)
    else:
        if args.manifest:
            manifest_path = (args.manifest if args.manifest.is_absolute() else ROOT / args.manifest).resolve()
            manifest = load_manifest(manifest_path)
            batch_id = manifest.get("batch_id")
        else:
            batch_id = args.batch_id
            manifest_path, manifest = find_manifest_for_batch(batch_dir, batch_id)
        files = collect_one_batch_files(batch_dir, manifest_path, manifest, extras)

    archive_path = (
        args.out.resolve()
        if args.out
        else default_archive_path(args.archive_dir, manifest_path=manifest_path, batch_id=batch_id)
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    if not files:
        raise SystemExit(f"No files found under {batch_dir}")

    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "created_at": created_at,
        "root": str(ROOT),
        "batch_dir": rel(batch_dir),
        "archive_kind": archive_kind,
        "batch_id": batch_id,
        "batch_manifest": rel(manifest_path) if manifest_path else None,
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
