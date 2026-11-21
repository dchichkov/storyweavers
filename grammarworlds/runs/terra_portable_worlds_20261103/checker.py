"""Isolated independent checks for the library/pottery authoring experiment."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import ast
import importlib.util
import json
from pathlib import Path
import random
import statistics
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grammarworlds.world import Frame, World
from grammarworlds.portable.language import load_lexicon
from grammarworlds.portable.runtime import sample_sentence


def blocked(pack, w, f, change):
    altered = w.clone()
    change(altered)
    assert f not in [frame for _, frame in pack.candidates(altered)], f"unguarded {f.kind}: {change}"
    before = altered.to_dict()
    try:
        pack.commit(altered, f, "This should never be committed.")
    except ValueError:
        pass
    else:
        raise AssertionError(f"commit accepted blocked {f.kind}")
    assert before == altered.to_dict(), "rejected commit mutated state"


def invariants(w, scenario, *, ending=False):
    e = w.entities
    if scenario == "library":
        assert not {"atlas_reserved", "atlas_released"} <= w.flags
        if "checked_out" in e["book"].state:
            assert e["book"].location == "friend"
        if ending:
            assert e["book"].location == "friend" and "checked_out" in e["book"].state
            assert e["tool"].location == "station" and e["ladder"].location == "store"
            assert (("atlas_released" in w.flags and e["atlas"].location == "display") or
                    ("atlas_reserved" in w.flags and e["atlas"].location == "hero" and "checked_out" in e["atlas"].state))
    else:
        cup = e["cup"]
        assert not {"thumb_design", "smooth_design"} <= w.flags
        if "tea" in cup.state:
            assert "fired" in cup.state and cup.location == "grandpa"
        if ending:
            assert {"tea", "fired", "safe_edges", "stable", "wide_handle"} <= cup.state
            assert cup.location == "grandpa"
            assert e["tool"].location == "helper" and e["sponge"].location == "bench"
            assert (("thumb_design" in w.flags and "thumb_rest" in cup.state) or
                    ("smooth_design" in w.flags and "smoothed" in cup.state))


def guards(pack, w, f, scenario):
    checks = 0
    def block(change):
        nonlocal checks
        blocked(pack, w, f, change)
        checks += 1
    if f.actor in w.entities and w.entities[f.actor].kind == "person":
        block(lambda x: setattr(x.entities[f.actor], "location", "__absent__"))
    if f.instrument:
        block(lambda x: setattr(x.entities[f.instrument], "location", "__absent__"))
    if scenario == "library":
        if f.kind == "retrieve":
            assert f.actor == "helper" and w.entities["book"].location == "high_shelf"
            assert "clue" in w.flags and {"atlas_reserved", "atlas_released"} & w.flags
            for entity in ("hero", "friend", "ladder"):
                block(lambda x, key=entity: setattr(x.entities[key], "location", "__absent__"))
            block(lambda x: x.flags.discard("clue"))
        if f.kind == "checkout":
            assert f.actor == "helper" and w.entities["book"].location == "helper"
            block(lambda x: setattr(x.entities["book"], "location", "high_shelf"))
            block(lambda x: setattr(x.entities["friend"], "location", "__absent__"))
        if f.kind == "ending":
            invariants(w, scenario, ending=True)
            for entity in ("tool", "ladder", "book", "atlas"):
                block(lambda x, key=entity: setattr(x.entities[key], "location", "__absent__"))
    else:
        required = {"slip": {"wet"}, "dry": {"wall_checked"}, "bisque": {"dry"},
                    "glaze": {"bisque"}, "fire": {"glazed"},
                    "give": {"fired", "safe_edges", "stable", "wide_handle"}, "use": {"fired"}}
        for state in required.get(f.kind, ()):
            assert state in w.entities["cup"].state, f"{f.kind} lacks {state}"
            block(lambda x, state=state: x.entities["cup"].state.discard(state))
        if f.kind in {"bisque", "fire"}:
            assert f.actor == "helper"
            block(lambda x: setattr(x.entities["kiln"], "location", "__absent__"))
        if f.kind == "give":
            block(lambda x: setattr(x.entities["grandpa"], "location", "__absent__"))
        if f.kind == "use":
            assert w.entities["cup"].location == "grandpa"
            block(lambda x: setattr(x.entities["cup"], "location", "bench"))
        if f.kind == "ending":
            invariants(w, scenario, ending=True)
            for entity in ("tool", "sponge", "cup"):
                block(lambda x, key=entity: setattr(x.entities[key], "location", "__absent__"))
            block(lambda x: x.entities["cup"].state.discard("tea"))
    return checks


def sample(pack, scenario, seed, tense):
    w = pack.make_world(seed)
    assert isinstance(w, World) and w.scenario == scenario
    assert not w.finished and not w.history
    initial = deepcopy(w.to_dict())
    before = deepcopy(w.to_dict())
    try:
        pack.commit(w, Frame("__forged__", "hero"), "Invalid.")
    except ValueError:
        pass
    else:
        raise AssertionError("forged frame accepted")
    assert before == w.to_dict()
    rows, checks, rng = [], 0, random.Random(seed)
    for _ in range(24):
        if w.finished:
            break
        before = deepcopy(w.to_dict())
        candidates = pack.candidates(w)
        assert before == w.to_dict() and candidates, "mutation or dead end"
        fact_ids = {f.id for f in w.facts_for_attention()}
        for k, f in candidates:
            assert k.requires <= w.flags and not k.excludes & w.flags
            assert set(f.cause_ids) <= fact_ids, "ungrounded frame causes"
            checks += guards(pack, w, f, scenario)
        before_snapshot = w.snapshot()
        row = sample_sentence(pack, w, rng, tense=tense)
        event = w.history[-1]
        assert len(w.history) == len(rows) + 1
        assert event["before"] == before_snapshot and event["after"] == w.snapshot()
        assert event["frame"] == row["frame"] and event["sentence"] == row["text"]
        f = row["frame"]
        if scenario == "library":
            if before_snapshot["entities"]["book"]["location"] == "high_shelf" and w.entities["book"].location != "high_shelf":
                assert f["kind"] == "retrieve" and f["actor"] == "helper"
        else:
            if before_snapshot["entities"]["cup"]["location"] != "grandpa" and w.entities["cup"].location == "grandpa":
                assert f["kind"] == "give"
            if "tea" not in before_snapshot["entities"]["cup"]["state"] and "tea" in w.entities["cup"].state:
                assert f["kind"] == "use"
        invariants(w, scenario)
        rows.append(row)
    assert w.finished and not pack.candidates(w), "no ending within 24 events"
    invariants(w, scenario, ending=True)
    replay = pack.make_world(seed)
    assert replay.to_dict() == initial
    for event in w.history:
        f = Frame(**{**event["frame"], "cause_ids": tuple(event["frame"]["cause_ids"])})
        assert replay.snapshot() == event["before"]
        record = pack.commit(replay, f, event["sentence"])
        record["referents"] = event["referents"]
        assert replay.snapshot() == event["after"]
    assert replay.to_dict() == w.to_dict(), "replay drift"
    return dict(seed=seed, tense=tense, scenario=scenario, story=" ".join(r["text"] for r in rows),
                frames=[r["frame"] for r in rows], initial_world=initial, final_world=w.to_dict(),
                guard_checks=checks, sentences=rows)


def main():
    scenario = sys.argv[1]
    results, failures, samples = [], [], []
    try:
        tree = ast.parse(Path("pack.py").read_text())
        allowed = {"__future__", "dataclasses", "copy", "random", "math", "grammarworlds.world",
                   "grammarworlds.portable.language", "grammarworlds.portable.features"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(x.name in allowed for x in node.names), "unsupported import"
            elif isinstance(node, ast.ImportFrom):
                assert node.module in allowed and node.level == 0, "unsupported import"
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "open", "__import__", "compile"}, "forbidden code execution/I/O"
        spec = importlib.util.spec_from_file_location("authored_pack", Path("pack.py"))
        pack = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = pack
        spec.loader.exec_module(pack)
        base = deepcopy(load_lexicon())
        for category, entries in pack.LEXICON.items():
            assert isinstance(entries, dict)
            assert not set(entries) & set(base[category]), f"duplicate lexicon in {category}"
    except Exception:
        Path("check.json").write_text(json.dumps(dict(passed=0, requested=120, errors=[traceback.format_exc()])))
        return
    with Path("stories.jsonl").open("w") as sink:
        for tense in ("past", "present"):
            for seed in range(60):
                try:
                    row = sample(pack, scenario, seed, tense)
                    assert base == load_lexicon(), "shared lexicon mutated"
                    if seed == 0 and tense == "past":
                        assert row == sample(pack, scenario, seed, tense), "non-deterministic generation"
                        Path("word_trace.json").write_text(json.dumps(row["sentences"], indent=2))
                    row["used_rules"] = sorted({r for s in row["sentences"] for r in s["rules"]})
                    row["branching_steps"] = sum(len(p["choices"]) > 1 for s in row["sentences"] for p in s["word_trace"])
                    del row["sentences"]
                    sink.write(json.dumps(row) + "\n")
                    results.append(row)
                    if seed < 5:
                        samples.append(f"## {scenario} — seed {seed}, {tense}\n\n{row['story']}")
                except Exception:
                    failures.append(dict(seed=seed, tense=tense, error=traceback.format_exc()))
    flags = ("atlas_reserved", "atlas_released") if scenario == "library" else ("thumb_design", "smooth_design")
    outcomes = Counter(next((f for f in flags if f in r["final_world"]["flags"]), "missing") for r in results)
    summary = dict(passed=len(results), requested=120, failed=len(failures),
        errors=failures[:5], failure_classes=dict(Counter(f["error"].splitlines()[-1] for f in failures)),
        guard_checks=sum(r["guard_checks"] for r in results),
        unique_texts=len({r["story"] for r in results}),
        unique_event_paths=len({tuple(f["kind"] for f in r["frames"]) for r in results}),
        outcomes=dict(outcomes), both_branches_observed=all(outcomes[f] for f in flags),
        mean_words=statistics.mean(len(r["story"].split()) for r in results) if results else 0,
        kernels=len(pack.KERNELS), new_lexicon_entries=sum(map(len, pack.LEXICON.values())),
        branching_steps=sum(r["branching_steps"] for r in results))
    Path("check.json").write_text(json.dumps(summary, indent=2))
    Path("samples.md").write_text("# Unfiltered first five seeds per tense\n\n" + "\n\n".join(samples))


if __name__ == "__main__":
    main()
