"""Matched xhigh follow-up; preserve raw output and reuse the campaign checks."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import uuid

import luna_high_trial as previous
import judge_stories as judge

api = previous.api
HERE = previous.HERE
BASE = previous.ARM
ARM = HERE / "gpt-6-luna_xhigh_oneshot"


def prepare():
    settings = json.loads((BASE / "settings.json").read_text())
    if api.digest((BASE / "request.json").read_bytes()) != settings["request_sha256"]:
        raise ValueError("Control request changed")
    for name, expected in settings["source_hashes"].items():
        if api.digest((BASE / "input" / name).read_bytes()) != expected:
            raise ValueError(f"Control input changed: {name}")
    original = json.loads((BASE / "request.json").read_text())
    if original["model"] != "gpt-6-luna" or original["reasoning"] != {"effort": "high"}:
        raise ValueError("Unexpected control")
    request = deepcopy(original)
    request["reasoning"] = {"effort": "xhigh"}
    ARM.mkdir(exist_ok=False)
    shutil.copytree(BASE / "input", ARM / "input")
    api.save(ARM / "request.json", request)
    settings.update(reasoning="xhigh", parent_arm=BASE.name,
                    idempotency_key=str(uuid.uuid4()),
                    request_sha256=api.digest((ARM / "request.json").read_bytes()))
    api.save(ARM / "settings.json", settings)
    api.save(ARM / "comparison.json", dict(
        changed_request_fields=[k for k in original if original[k] != request[k]],
        source_hashes_identical=True, task_and_context_identical=request["input"] == original["input"],
        note="Only high -> xhigh; same 64k ceiling, no prior outputs or repair feedback."))
    for source in (Path(__file__), Path(api.__file__)):
        shutil.copyfile(source, ARM / source.name)
    print(ARM)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run", "check", "prepare-judge", "judge"))
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    with api.campaign_lock(HERE):
        if args.phase == "prepare":
            prepare()
        elif args.phase == "run":
            api.run(ARM, args.api_key_file.read_text().strip())
        elif args.phase == "check":
            api.check(ARM)
        elif args.phase == "prepare-judge":
            judge.prepare(source=ARM / "check.json", out=ARM / "quality", label=ARM.name + "_kite")
        else:
            judge.judge(args.api_key_file.read_text().strip(), source=ARM / "check.json",
                        out=ARM / "quality", ledger_arm="luna_xhigh_oneshot_standard_judge_v1")
