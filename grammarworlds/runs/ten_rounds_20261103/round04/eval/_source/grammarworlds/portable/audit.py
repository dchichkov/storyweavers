"""Reproducible, unfiltered transfer/guard audit; no models or GF dependencies."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

from ..world import Frame
from .catalog import RULES, context
from .language import ROOT, load_lexicon
from .runtime import SCENARIOS, generate, setup


def interventions(pack, world, frame):
    checks = 0
    def block(change, predicate):
        nonlocal checks
        altered = world.clone()
        change(altered)
        if any(predicate(f) for _, f in pack.candidates(altered)):
            raise AssertionError(f"guard intervention failed: {world.scenario}/{frame.kind}")
        checks += 1
    if world.scenario in {"rescue", "kite", "key"} and frame.kind == "solve":
        block(lambda w: setattr(w.entities[w.tool], "location", "elsewhere"), lambda f: f.kind == "solve")
    if world.scenario == "music":
        if frame.kind == "join":
            for entity in ("hero", "partner"):
                block(lambda w, e=entity: setattr(w.entities[e], "location", "outside"), lambda f: f.kind == "join")
            for entity in ("drum", "spare"):
                block(lambda w, e=entity: setattr(w.entities[e], "location", "shelf"), lambda f: f.kind == "join")
            block(lambda w: w.entities["partner"].state.discard("consented"), lambda f: f.kind == "join")
        if frame.kind == "ending":
            for entity in ("drum", "spare"):
                block(lambda w, e=entity: setattr(w.entities[e], "location", "hero"), lambda f: f.kind == "ending")
    if world.scenario == "greenhouse":
        if frame.kind == "fill":
            block(lambda w: w.entities[frame.patient].state.clear(), lambda f: f == frame)
        if frame.kind == "water":
            block(lambda w: w.entities["can"].state.clear(), lambda f: f.kind == "water")
        if frame.kind == "close_umbrella":
            block(lambda w: w.entities["cloth"].state.clear(), lambda f: f.kind == "close_umbrella")
    return checks


def run(out, count=100, seed=0):
    if count < 1:
        raise ValueError("count must be positive")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    freeze = json.loads((ROOT / "sources/pre_holdout_freeze.json").read_text())
    unchanged = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in freeze["sha256"].items())
    if not unchanged:
        raise AssertionError("shared rules changed after the held-out boundary")
    summary, samples = {}, []
    with (out / "stories.jsonl").open("w") as sink:
        for scenario in (*SCENARIOS, "heldout"):
            texts, paths, used = [], set(), set()
            guards = steps = branching = 0
            for tense in ("past", "present"):
                for position in range(count):
                    row = generate(scenario, seed + position, tense=tense)
                    pack, world = setup(scenario, row["seed"])
                    for sentence in row["sentences"]:
                        f = Frame(**{**sentence["frame"], "cause_ids": tuple(sentence["frame"]["cause_ids"])})
                        guards += interventions(pack, world, f)
                        event = pack.commit(world, f, sentence["text"])
                        event["referents"] = sentence["referents"]
                        used.update(r for r in sentence["rules"] if r in RULES)
                        steps += len(sentence["word_trace"])
                        branching += sum(len(p["choices"]) > 1 for p in sentence["word_trace"])
                    if world.to_dict() != row["final_world"]:
                        raise AssertionError("world trace did not replay")
                    texts.append(row["story"])
                    paths.add(tuple(s["frame"]["kind"] for s in row["sentences"]))
                    compact = {k: row[k] for k in ("scenario", "seed", "tense", "story")}
                    compact["frames"] = [s["frame"] for s in row["sentences"]]
                    compact["final_state"] = world.snapshot()
                    sink.write(json.dumps(compact) + "\n")
                    if tense == "past" and position < 4:
                        samples.append(compact)
                    if tense == "past" and position == 0:
                        (out / f"{scenario}_trace.json").write_text(json.dumps(row, indent=2) + "\n")
            summary[scenario] = {"stories": len(texts), "completed": len(texts), "replayed": len(texts),
                                 "exact_unique_texts": len(set(texts)), "event_paths": len(paths),
                                 "guard_interventions": guards, "word_steps": steps,
                                 "branching_word_steps": branching, "trace_rule_ids": sorted(used)}
    source = Path("storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/03_greenhouse/story.txt")
    added = json.loads((ROOT / "lexicon/greenhouse.json").read_text())
    report = {"scope": "mechanical transfer, not literary quality or genuine plot diversity",
              "seeds": [seed, seed + count - 1], "tenses": ["past", "present"],
              "shared_rules_unchanged": unchanged, "new_shared_rules_for_heldout": 0,
              "catalog_entries": len(RULES), "rule_origins": dict(Counter(k.split(".")[0] for k in RULES)),
              "heldout_new_lexical_entries": {k: len(v) for k, v in added.items()},
              "heldout_source": str(source), "heldout_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "author_context": context("complement hope invitation", budget=3000),
              "results": summary, "elapsed_seconds": round(time.monotonic() - started, 3)}
    (out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "samples.md").write_text("# First four past-tense seeds per world, unfiltered\n\n" +
        "\n\n".join(f"## {r['scenario']} — seed {r['seed']}\n\n{r['story']}" for r in samples) + "\n")
    sources = list(ROOT.rglob("*.py")) + list((ROOT / "lexicon").glob("*.json"))
    (out / "source_hashes.json").write_text(json.dumps({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                                       for p in sorted(sources)}, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--count", type=int, default=100, help="per world per tense")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(run(args.out, args.count, args.seed), indent=2))
