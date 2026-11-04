"""Offline audit, immutable source snapshots, and descriptive corpus diagnostics.

Mechanical checks are deliberately separate from literary judgments. Every
requested position is saved, including failed generation or validation.
"""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, is_dataclass
import hashlib
import json
import lzma
from pathlib import Path
import re
import statistics
import subprocess
import sys

from .inventory import ROOT, check_inventory, load


def json_native(value):
    if is_dataclass(value):
        value = asdict(value)
    return json.loads(json.dumps(value, allow_nan=False))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_row(module, row, seed, count):
    row = json_native(row)
    require(row["seed"] == seed and row["scene_count"] == count, "Requested position changed")
    path, episodes = row["path"], row["episodes"]
    require(count in (7, 8) and len(path) == len(episodes) == count, "Wrong route length")
    require(len(path) == len(set(path)), "Repeated scene")
    require(all(scene in module.SCENES for scene in path), "Unknown scene")
    params = module.Parameters(**row["parameters"])
    state = json_native(module.initial(params))
    module.validate(deepcopy(state))
    for scene_id, episode in zip(path, episodes):
        require(episode["id"] == scene_id, "Episode/path mismatch")
        require(episode["before"] == state, "Broken episode state chain")
        require(module.guard(scene_id, deepcopy(state)), "Scene guard rejected saved path")
        require(isinstance(episode["text"], str) and bool(episode["text"].strip()), "Empty prose")
        require(bool(episode["events"]), "Scene has no enacted action")
        for event in episode["events"]:
            require(bool(event["action"]), "Unnamed action")
            for key, value in event["requires"].items():
                require(key in state and state[key] == value, f"False action precondition: {key}")
            require(bool(event["changes"]), "No-op event")
            for key, change in event["changes"].items():
                require(key in state and state[key] == change["before"], f"False event pre-state: {key}")
                require(change["before"] != change["after"], f"Unchanged event field: {key}")
                state[key] = deepcopy(change["after"])
            module.validate(deepcopy(state))
        require(state == episode["after"], "Unrecorded scene effect")
    require(row["story"] == "\n\n".join(e["text"] for e in episodes), "Story differs from episodes")
    require(row["final_state"] == state, "Final state differs from trace")
    require(state.get("story.ended") is True and bool(state.get("story.outcome")), "Unfinished story")
    replayed = [json_native(e) for e in module.replay(params, path)]
    require(replayed == episodes, "Replay changed state, events, or prose")
    require(json_native(module.generate(seed, count=count, params=params)) == row, "Nondeterministic generation")
    return row


def describe(rows):
    texts = [r["story"] for r in rows]
    raw = "\n\n".join(texts).encode("utf-8")
    words = [len(text.split()) for text in texts]
    scene_words = [len(e["text"].split()) for r in rows for e in r["episodes"]]
    stats = lambda xs: {"min": min(xs), "mean": statistics.mean(xs), "max": max(xs)} if xs else None
    quoted_words = sum(len(q.split()) for text in texts for q in re.findall(r'["\u201c]([^"\u201d\n]+)["\u201d]', text))
    compressed = len(lzma.compress(raw)) if raw else 0
    return {
        "successful": len(rows), "exact_texts": len(set(texts)),
        "distinct_paths": len({tuple(r["path"]) for r in rows}),
        "outcomes": dict(Counter(r["final_state"]["story.outcome"] for r in rows)),
        "scene_frequency": dict(Counter(s for r in rows for s in r["path"])),
        "story_words": stats(words), "scene_words": stats(scene_words),
        "approx_quoted_word_fraction": quoted_words / sum(words) if sum(words) else 0,
        "lzma": {"format": "Python lzma default XZ; stories joined by two newlines in requested order",
                 "raw_bytes": len(raw), "compressed_bytes": compressed,
                 "ratio": compressed / len(raw) if raw else None},
        "warning": "Exact text counts, quote counts, and compression are diagnostics, not literary or semantic-diversity scores.",
    }


def saved_text(attempt):
    row = attempt.get("row")
    if isinstance(row, dict) and isinstance(row.get("story"), str):
        return row["story"]
    return attempt.get("error", "No story text returned")


def source_files(pack):
    package = ROOT.parent
    files = [package / "__init__.py", package / "runtime.py"]
    files += sorted(ROOT.glob("*.py"))
    files += sorted((ROOT / pack).rglob("*.py"))
    files += [ROOT / pack / "reference_story.md", ROOT / pack / "scene_inventory.json"]
    return files


def snapshot(pack, out):
    repo = ROOT.parents[1]
    hashes = {}
    for path in source_files(pack):
        data = path.read_bytes()
        name = path.relative_to(repo).as_posix()
        target = out / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    return hashes


def audit(pack, *, seeds, lengths=(7, 8), out):
    module = load(pack)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    hashes = snapshot(pack, out)
    inventory_error = None
    try:
        inventory = check_inventory(pack, module)
    except (ValueError, KeyError, TypeError) as exc:
        inventory = None
        inventory_error = f"{type(exc).__name__}: {exc}"
    rows, attempts = [], []
    positions = [(seed, count) for count in lengths for seed in seeds]
    for seed, count in positions:
        record = {"seed": seed, "scene_count": count}
        try:
            row = json_native(module.generate(seed, count=count))
            record["row"] = row
            verify_row(module, row, seed, count)
            record["status"] = "passed"
            rows.append(row)
        except Exception as exc:
            record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        attempts.append(record)
    reference = (ROOT / pack / "reference_story.md").read_text(encoding="utf-8")
    reference = re.sub(r'<!--[\s\S]*?-->', '', reference)
    reference = re.sub(r'^#+ .*$', '', reference, flags=re.M)
    current_hashes = {p.relative_to(ROOT.parents[1]).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in source_files(pack)}
    unchanged = current_hashes == hashes
    summary = {"pack": pack, "requested": len(positions), "failures": len(positions) - len(rows),
               "inventory_error": inventory_error,
               "reference_words": len(reference.split()),
               "reference_scene_count": len(inventory["scenes"]) if inventory else None,
               "implemented_scene_count": len(module.SCENES), "source_unchanged": unchanged,
               "all": describe(rows),
               "by_length": {str(n): describe([r for r in rows if r["scene_count"] == n]) for n in lengths}}
    manifest = {"schema": "mini_adventure_audit.v1", "pack": pack,
                "positions": positions, "source_sha256": hashes, "source_unchanged": unchanged,
                "api_calls": 0, "all_requested_positions_preserved": True}
    (out / "attempts.jsonl").write_text("".join(json.dumps(a, ensure_ascii=False) + "\n" for a in attempts), encoding="utf-8")
    (out / "stories.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    # Preserve every generated text, including ones rejected by the mechanical audit.
    (out / "stories.md").write_text("# Unfiltered Generated Stories\n\n" + "\n\n".join(
        f"## Seed {a['seed']}, {a['scene_count']} scenes: {a['status']}\n\n"
        + saved_text(a) for a in attempts) + "\n", encoding="utf-8")
    for name, data in (("manifest.json", manifest), ("summary.json", summary)):
        (out / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def verify_snapshot(out):
    """Replay all saved positions in a fresh interpreter using only frozen code."""
    out = Path(out).resolve()
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["source_sha256"].items():
        path = (out / "source" / name).resolve()
        require(path.is_relative_to(out / "source"), "Unsafe snapshot path")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, f"Changed frozen source: {name}")
    code = '''import json,sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from storyscenes.mini_adventures.inventory import load
from storyscenes.mini_adventures.review import json_native,verify_row
out = Path(sys.argv[2])
manifest = json.loads((out / "manifest.json").read_text())
module = load(manifest["pack"])
attempts = [json.loads(line) for line in (out / "attempts.jsonl").read_text().splitlines()]
assert [(a["seed"],a["scene_count"]) for a in attempts] == [tuple(p) for p in manifest["positions"]]
for attempt in attempts:
    row = None
    try:
        row = json_native(module.generate(attempt["seed"],count=attempt["scene_count"]))
        verify_row(module,row,attempt["seed"],attempt["scene_count"])
        status,error = "passed",None
    except Exception as exc:
        status,error = "failed",f"{type(exc).__name__}: {exc}"
    assert status == attempt["status"], (attempt["seed"],"status changed")
    assert row == attempt.get("row"), (attempt["seed"],"generated row changed")
    assert error == attempt.get("error"), (attempt["seed"],"error changed")
print(json.dumps({"reproduced_positions":len(attempts),"pack":manifest["pack"]}))
'''
    result = subprocess.run([sys.executable, "-I", "-c", code, str(out / "source"), str(out)],
                            cwd=out / "source", check=True, text=True, capture_output=True, timeout=180)
    return json.loads(result.stdout)
