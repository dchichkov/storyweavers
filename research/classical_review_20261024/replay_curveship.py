"""Replay inspected Curveship examples without modifying its source.

Download and unpack the official Curveship-py 0.6.01 archive first:
https://nickm.com/curveship/curveship-py-0601.zip

Usage: python3 replay_curveship.py --source PATH --out PATH
The only runtime adaptation fixes terminal dimensions for noninteractive capture.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.out.resolve()
    if not (source / "curveship.py").is_file():
        parser.error("--source must contain the unpacked curveship.py")
    output.mkdir(parents=True, exist_ok=True)
    (source / "logs").mkdir(exist_ok=True)
    adapter = (
        "import random,presenter,curveship,sys; "
        "random.seed(0); "
        "presenter.terminal_size=lambda:(80,25); "
        "sys.exit(curveship.main(sys.argv))"
    )
    cases = [
        ("robbery_default", "fiction/robbery.py", [], "quit\n"),
        ("robbery_guard", "fiction/robbery.py",
         ["spin/told_and_focalized_by_guard.py"], "quit\n"),
        ("robbery_reverse", "fiction/robbery.py", ["spin/retrograde.py"], "quit\n"),
        ("robbery_future", "fiction/robbery.py", ["spin/prophecy.py"], "quit\n"),
        ("artmaking", "fiction/artmaking.py", [],
         "north\nopen box\nexamine sculpture\nkick sculpture\nquit\n"),
    ]
    manifest = {
        "source_url": "https://nickm.com/curveship/curveship-py-0601.zip",
        "version": "0.6.01 (Python 3 port, copyright 2019/2020; design released 2011)",
        "python": sys.version,
        "seed": 0,
        "adaptation": "Override presenter.terminal_size to return (80,25); no source edits.",
        "source_sha256": {
            str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(source.rglob("*.py"))
        },
        "runs": [],
    }
    for name, fiction, spins, commands in cases:
        result = subprocess.run(
            [sys.executable, "-c", adapter, fiction, *spins],
            cwd=source, input=commands, text=True, capture_output=True, timeout=20,
        )
        (output / (name + ".txt")).write_text(result.stdout + result.stderr)
        manifest["runs"].append({
            "id": name, "fiction": fiction, "spins": spins, "input": commands,
            "returncode": result.returncode,
        })
        print(f"{name}: exit {result.returncode}")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if any(run["returncode"] for run in manifest["runs"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
