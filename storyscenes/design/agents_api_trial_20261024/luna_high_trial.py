"""Luna high-effort follow-up with identical frozen authoring inputs."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from storyscenes import authoring_api as api

BASE = HERE / "gpt-6-luna_oneshot"
ARM = HERE / "gpt-6-luna_high_oneshot"
NORMALIZED = HERE / "gpt-6-luna_high_oneshot_normalized"
REPAIRED = HERE / "gpt-6-luna_high_oneshot_repaired"


def prepare():
    settings = json.loads((BASE / "settings.json").read_text())
    if api.digest((BASE / "request.json").read_bytes()) != settings["request_sha256"]:
        raise ValueError("Original prepared request changed")
    for name, expected in settings["source_hashes"].items():
        if api.digest((BASE / "input" / name).read_bytes()) != expected:
            raise ValueError(f"Original input changed: {name}")
    original = json.loads((BASE / "request.json").read_text())
    if original["model"] != "gpt-6-luna" or original["reasoning"] != {"effort": "low"}:
        raise ValueError("Unexpected control request")
    request = deepcopy(original)
    request["reasoning"] = {"effort": "high"}
    request["max_output_tokens"] = 64000
    ARM.mkdir(exist_ok=False)
    shutil.copytree(BASE / "input", ARM / "input")
    api.save(ARM / "request.json", request)
    settings.update(reasoning="high", max_output_tokens=64000,
        idempotency_key=str(uuid.uuid4()), parent_arm=BASE.name,
        request_sha256=api.digest((ARM / "request.json").read_bytes()))
    api.save(ARM / "settings.json", settings)
    api.save(ARM / "comparison.json", dict(
        changed_request_fields=[k for k in original if original[k] != request[k]],
        source_hashes_identical=True, task_and_context_identical=request["input"] == original["input"],
        note="High reasoning plus 64k output headroom; one task, not a yield estimate."))
    for source in (Path(__file__), Path(api.__file__)):
        shutil.copyfile(source, ARM / source.name)
    print(ARM)


def normalize_identical_duplicates():
    raw = json.loads((ARM / "bundle.json").read_text())
    files, removed = {}, []
    for index, row in enumerate(raw["files"]):
        if set(row) != {"path", "content"}:
            raise ValueError("Unexpected file fields")
        name = row["path"]
        if name in files:
            if files[name] != row["content"]:
                raise ValueError(f"Conflicting duplicate, refusing to choose: {name}")
            removed.append(dict(index=index, path=name, sha256=api.digest(row["content"].encode())))
        else:
            files[name] = row["content"]
    bundle = dict(files=[dict(path=n, content=c) for n, c in files.items()])
    api.validate_bundle(bundle)
    if not removed:
        raise ValueError("No duplicate normalization needed")
    NORMALIZED.mkdir(exist_ok=False)
    shutil.copytree(ARM / "input", NORMALIZED / "input")
    settings = json.loads((ARM / "settings.json").read_text())
    settings.update(derived_from=ARM.name, generation_request_made=False)
    api.save(NORMALIZED / "settings.json", settings)
    api.save(NORMALIZED / "bundle.json", bundle)
    api.save(NORMALIZED / "normalization.json", dict(
        source_bundle_sha256=api.digest((ARM / "bundle.json").read_bytes()),
        removed=removed, remaining_contents_unchanged=True,
        note="Exact duplicate record removal only; original raw bundle remains a strict packaging failure."))
    print(NORMALIZED)


def repair_two_runtime_errors():
    bundle = json.loads((NORMALIZED / "bundle.json").read_text())
    name = "storyscenes/mini_adventures/kite/world.py"
    row = next(row for row in bundle["files"] if row["path"] == name)
    original = row["content"]
    fixes = [
        ('{"story.stage": "invited", "pavel.comfort": 2,',
         '{"story.stage": "invited", "pavel.comfort": x.state["pavel.comfort"],'),
        ('        _act(x, "gather_the_spool", {"reel.location": holder}, {"reel.location": "Nia"})',
         '        if holder != "Nia":\n'
         '            _act(x, "gather_the_spool", {"reel.location": holder}, {"reel.location": "Nia"})'),
    ]
    for before, after in fixes:
        if row["content"].count(before) != 1:
            raise ValueError("Expected exactly one repair target")
        row["content"] = row["content"].replace(before, after)
    api.validate_bundle(bundle)
    REPAIRED.mkdir(exist_ok=False)
    shutil.copytree(NORMALIZED / "input", REPAIRED / "input")
    settings = json.loads((NORMALIZED / "settings.json").read_text())
    settings.update(derived_from=NORMALIZED.name, manually_repaired=True)
    api.save(REPAIRED / "settings.json", settings)
    api.save(REPAIRED / "bundle.json", bundle)
    api.save(REPAIRED / "repair.json", dict(
        source_bundle_sha256=api.digest((NORMALIZED / "bundle.json").read_bytes()),
        changed_file=name, original_sha256=api.digest(original.encode()),
        repaired_sha256=api.digest(row["content"].encode()),
        replacements=[dict(before=a, after=b) for a, b in fixes],
        prose_and_tests_unchanged=True,
        note="Two manual code fixes; not a one-shot success. Scene guard still requires comfort >= 2; skip an already-satisfied transfer."))
    print(REPAIRED)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run", "check", "normalize", "check-normalized", "repair", "check-repaired"))
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    with api.campaign_lock(HERE):
        if args.phase == "prepare":
            prepare()
        elif args.phase == "run":
            api.run(ARM, args.api_key_file.read_text().strip())
        elif args.phase == "normalize":
            normalize_identical_duplicates()
        elif args.phase == "repair":
            repair_two_runtime_errors()
        else:
            api.check(REPAIRED if args.phase == "check-repaired" else
                      NORMALIZED if args.phase == "check-normalized" else ARM)
