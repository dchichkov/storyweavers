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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run", "check"))
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    with api.campaign_lock(HERE):
        if args.phase == "prepare":
            prepare()
        elif args.phase == "run":
            api.run(ARM, args.api_key_file.read_text().strip())
        else:
            api.check(ARM)
