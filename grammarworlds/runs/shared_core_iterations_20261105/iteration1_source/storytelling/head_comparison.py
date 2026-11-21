"""Matched-seed ablations of symbolic word heads; no runtime/judge model calls."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

from .runtime import SCENARIOS, generate, replay
from .qa import questions

PROFILES = {
    "off": {},
    "seed": dict(symbolic_heads=True, head_profile="seed"),
    "manual": dict(symbolic_heads=True),
    "tool_only": dict(symbolic_heads=True, head_ids=["P023"]),
    "state_only": dict(symbolic_heads=True, head_ids=["P059"]),
}
EXPANDED_PROFILES = {
    "off": {},
    "manual": dict(symbolic_heads=True),
    "expanded_off": dict(continuations="expanded"),
    "expanded_manual": dict(continuations="expanded", symbolic_heads=True),
}
ROOT = Path(__file__).resolve().parents[2]


def measures(row):
    counts = Counter()
    changes = []
    for event in row["trace"]:
        counts["event_steps"] += 1
        counts["grammar_derivations_sum"] += event.get("grammar_derivations", 0)
        counts["grammar_surfaces_sum"] += event.get("grammar_surfaces", 0)
        prefix = []
        for p in event["word_trace"]:
            counts["token_steps"] += 1
            counts["choice_steps"] += len(p["choices"]) > 1
            counts["four_or_more_choices"] += len(p["choices"]) >= 4
            counts["conditional_entropy_sum_bits"] += -sum(c["probability"]*math.log2(c["probability"]) for c in p["choices"])
            for h in p.get("symbolic_heads", []):
                counts[h["head_id"]+"_requested"] += 1
                counts[h["head_id"]+"_active"] += h["status"] == "active"
                deltas = list(h["log_adjustments"].values())
                counts[h["head_id"]+"_effective"] += bool(deltas) and max(deltas)-min(deltas) > 1e-10
            tv = p.get("head_total_variation", 0)
            counts["changed_distribution_steps"] += tv > 1e-10
            counts["total_variation_sum"] += tv
            if tv > 1e-10:
                changes.append(dict(event_id=event["event_id"], prefix=" ".join(prefix),
                    selected=p["selected"], total_variation=tv,
                    choices=[{k:c[k] for k in ("word", "probability", "grammar_probability")} for c in p["choices"]],
                    heads=p["symbolic_heads"]))
            # Direct-action preference is a stylistic proxy, not a quality grade.
            words = {c["word"] for c in p["choices"]}
            use_words = words & {"use", "used", "uses"}
            if use_words and len(words) > len(use_words):
                counts["use_vs_other_opportunities"] += 1
                counts["use_selected"] += p["selected"] in use_words
            if p["selected"] != "<END>":
                prefix.append(p["selected"])
    return counts, changes


def validate(row):
    assert replay(row)
    qa = questions(row)
    assert len(qa) >= 5
    assert len({q["question"] for q in qa}) == len(qa)
    assert len({q["kind"] for q in qa}) >= 3
    assert any(q["answer"].count(".") >= 2 for q in qa)
    assert len({p for s in row["scenes"] for p in s["speakers"]}) >= 2
    for q in qa:
        assert q["event_ids"] and q["entity_ids"]
        assert q["answer"].endswith(".") and len(q["answer"].split()) >= 3
        for e in q["evidence"]:
            assert row["story"][e["start"]:e["end"]] == e["text"]
    for e in row["trace"]:
        assert math.isclose(e["probability"], math.prod(p["selected_probability"] for p in e["word_trace"]), rel_tol=1e-10)
        for p in e["word_trace"]:
            assert math.isclose(sum(c["probability"] for c in p["choices"]), 1)
            assert all(c["probability"] > 0 and c.get("grammar_probability", c["probability"]) > 0 for c in p["choices"])
    return qa


def run(out, *, start=1000, count=20, expanded=False):
    if count < 1:
        raise ValueError("count must be positive")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    profiles = EXPANDED_PROFILES if expanded else PROFILES
    # Freeze source identities before generation, including the unchanged grammar.
    paths = list((ROOT/"grammarworlds/storytelling").glob("*.py"))
    paths += list((ROOT/"grammarworlds/storytelling").glob("*.json"))
    paths += list((ROOT/"grammarworlds/symbolic_heads").rglob("*.py"))
    paths += list((ROOT/"grammarworlds/symbolic_heads/data").glob("*.json"))
    paths += list((ROOT/"grammarworlds/portable").rglob("*.py"))
    paths += [ROOT/"grammarworlds"/f for f in ("grammar.py", "world.py", "engine.py")]
    manifest = dict(start=start, count_per_scenario_tense=count, profiles=profiles,
        sample_seed=start, sample_tense="past",
        source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)})
    (out/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    totals = {profile: Counter() for profile in profiles}
    words = defaultdict(list)
    texts = defaultdict(set)
    paths_seen = defaultdict(Counter)
    samples = []
    with gzip.open(out/"stories_qa.jsonl.gz", "wt") as sink, gzip.open(out/"sample_traces.jsonl.gz", "wt") as trace_sink:
        for scenario in SCENARIOS:
            for tense in ("past", "present"):
                for seed in range(start, start+count):
                    baseline = None
                    baseline_path = None
                    same_grammar_baseline = {}
                    for profile, options in profiles.items():
                        row = generate(scenario, seed, tense=tense, **options)
                        qa = validate(row)
                        metrics, changes = measures(row)
                        path = tuple(e["frame"]["kind"] for e in row["trace"])
                        if profile == "off":
                            baseline, baseline_path = row["story"], path
                        grammar = options.get("continuations", "original")
                        if not options.get("symbolic_heads"):
                            same_grammar_baseline[grammar] = (row["story"], path)
                        ref_text, ref_path = same_grammar_baseline[grammar]
                        metrics.update(stories=1, qa_pairs=len(qa), text_changed=row["story"]!=baseline,
                                       path_changed=path!=baseline_path,
                                       heads_changed_text=row["story"]!=ref_text, heads_changed_path=path!=ref_path)
                        totals[profile].update(metrics)
                        words[profile].append(len(row["story"].split()))
                        texts[profile,scenario,tense].add(row["story"])
                        paths_seen[profile,scenario,tense][path] += 1
                        compact = dict(profile=profile, scenario=scenario, tense=tense, seed=seed,
                            story=row["story"], qa=qa, path=path, metrics=metrics, distribution_changes=changes)
                        sink.write(json.dumps(compact)+"\n")
                        if seed == start and tense == "past" and (expanded or profile in {"off", "manual"}):
                            samples.append(compact)
                            trace_sink.write(json.dumps(dict(profile=profile, **row))+"\n")
            print(f"Completed {scenario}: {count*2*len(profiles)} stories", flush=True)
    summary = {}
    for profile in profiles:
        entropies = []
        for (p,_,_), counts in paths_seen.items():
            if p == profile:
                n = sum(counts.values())
                entropies.append(-sum((v/n)*math.log2(v/n) for v in counts.values()))
        summary[profile] = dict(totals[profile], mean_words=statistics.mean(words[profile]),
            distinct_texts=sum(len(v) for (p,_,_),v in texts.items() if p == profile),
            distinct_paths=sum(len(v) for (p,_,_),v in paths_seen.items() if p == profile),
            mean_path_entropy_bits=statistics.mean(entropies))
    (out/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    lines = ["# Matched samples: symbolic heads off/on", "",
             f"Seed {start}, past tense, chosen before generation. All seven worlds included. No sample selection or prose repair.", ""]
    for row in samples:
        lines += [f"## {row['scenario']} — {row['profile']}", "", row["story"], ""]
        for q in row["qa"]:
            lines += ["Q: "+q["question"], "A: "+q["answer"], ""]
    (out/"samples.md").write_text("\n".join(lines))
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--start", type=int, default=1000)
    p.add_argument("--count", type=int, default=20)
    p.add_argument("--expanded", action="store_true", help="Compare original and expanded grammars, each with heads off/on")
    a = p.parse_args()
    run(a.out, start=a.start, count=a.count, expanded=a.expanded)
