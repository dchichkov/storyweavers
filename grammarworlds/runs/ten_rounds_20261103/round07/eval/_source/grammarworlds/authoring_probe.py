"""Post-hoc diagnostics applied equally to both authored music packs.

These do not replace the predeclared test counts or alter judge samples.
"""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grammarworlds.pack_runtime import sample
from grammarworlds.world import Frame


def main():
    spec = importlib.util.spec_from_file_location("authored_pack", Path("pack.py").resolve())
    pack = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = pack
    spec.loader.exec_module(pack)
    failures, checks, grammar_counts = [], Counter(), Counter()
    for seed in range(1000, 1060):
        row = sample(pack, seed)
        story = row["story"]
        for phrase in ("hoped a duet", "Mateo choice stayed his", "the room quiet sounds", "Nia program"):
            if phrase in story:
                grammar_counts[phrase] += 1
        world = pack.make_world(seed, partner_willing=None)
        for sentence in row["sentences"]:
            for _, candidate in pack.candidates(world):
                if candidate.kind == "join":
                    for label in ("join_with_absent_hero", "join_without_hero_drum"):
                        changed = world.clone()
                        if label == "join_with_absent_hero":
                            changed.entities["hero"].location = "outside"
                        else:
                            changed.entities["drum"].location = "shelf"
                        checks[label] += 1
                        if any(f.kind == "join" for _, f in pack.candidates(changed)):
                            failures.append(dict(kind=label, seed=seed, after_events=len(world.history),
                                                 candidate=dict(kind=candidate.kind, actor=candidate.actor)))
            frame = Frame(**{**sentence["frame"], "cause_ids": tuple(sentence["frame"]["cause_ids"])})
            pack.commit(world, frame, sentence["text"])
            if "both instruments back" in sentence["text"]:
                checks["both_instruments_returned_claim"] += 1
                if any(world.entities[name].location != "shelf" for name in ("drum", "spare")):
                    failures.append(dict(kind="premature_both_returned_claim", seed=seed,
                        after_events=len(world.history), sentence=sentence["text"],
                        locations={name: world.entities[name].location for name in ("drum", "spare")}))
    result = dict(scope="post-hoc diagnostics, same probes and same 60 seeds for both authors",
        checks=dict(checks), failure_counts=dict(Counter(f["kind"] for f in failures)),
        failures=failures, grammatical_error_story_counts=dict(grammar_counts))
    Path("probe.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != "failures"}, indent=2))


if __name__ == "__main__":
    main()
