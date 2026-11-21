"""Unfiltered short-story, dialogue, physical replay and reading-QA audit."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

from ..portable.audit import interventions
from ..portable.runtime import generate as full_generate
from ..portable_authoring_check import guards
from ..world import Frame
from .runtime import SCENARIOS, generate, replay, setup
from .qa import questions

ROOT = Path(__file__).resolve().parents[2]


def run(out, count=60):
    if count < 1 or count > 60:
        raise ValueError("comparison has saved authored baselines for seeds 0–59")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    summary, samples = {}, []
    with (out / "stories_qa.jsonl").open("w") as sink:
        for scenario in SCENARIOS:
            baseline = {}
            if scenario in {"library", "pottery"}:
                source = ROOT / "grammarworlds/runs/terra_portable_worlds_20261103" / scenario / "round2/stories.jsonl"
                baseline = {(r["seed"], r["tense"]): r["story"] for r in map(json.loads, source.read_text().splitlines())}
            words, old_words, kinds, qa_count, guard_count, visible, internal, text_set = [], [], Counter(), 0, 0, [], [], set()
            for tense in ("past", "present"):
                for seed in range(count):
                    row = generate(scenario, seed, tense=tense)
                    replay(row)
                    qa = questions(row)
                    assert len(qa) >= 5 and len({q["question"] for q in qa}) == len(qa)
                    assert len({q["kind"] for q in qa}) >= 3
                    assert all(q["answer"].count(".") >= 2 for q in qa)
                    assert len({p for s in row["scenes"] for p in s["speakers"]}) >= 2
                    assert row["story"].count("“") == row["story"].count("”") >= 2
                    for q in qa:
                        assert q["event_ids"] and q["entity_ids"] and q["evidence"]
                        for e in q["evidence"]:
                            assert row["story"][e["start"]:e["end"]] == e["text"]
                    pack, world = setup(scenario, seed)
                    for event in row["final_world"]["history"]:
                        f = Frame(**{**event["frame"], "cause_ids": tuple(event["frame"]["cause_ids"])})
                        if scenario in {"library", "pottery"}:
                            guard_count += guards(pack, world, f, scenario)
                        else:
                            guard_count += interventions(pack, world, f)
                        record = pack.commit(world, f, event["sentence"])
                        for key in ("referents", "speakers", "narrated"):
                            record[key] = event[key]
                    assert world.to_dict() == row["final_world"]
                    old = baseline[(seed, tense)] if baseline else full_generate(
                        "heldout" if scenario == "greenhouse" else scenario, seed, tense=tense)["story"]
                    words.append(len(row["story"].split())); old_words.append(len(old.split()))
                    kinds.update(q["kind"] for q in qa); qa_count += len(qa)
                    visible.append(len(row["scenes"])); internal.append(len(row["trace"]) - len(row["scenes"]))
                    text_set.add(row["story"])
                    compact = {k: row[k] for k in ("scenario", "seed", "tense", "story", "text_sha256", "scenes")}
                    compact.update(qa=qa, original_generated_story=old,
                                   final_state=world.snapshot(), frames=[e["frame"] for e in row["final_world"]["history"]])
                    sink.write(json.dumps(compact) + "\n")
                    if seed == 7 and tense == "past":
                        samples.append(compact)
                        (out / f"{scenario}_trace.json").write_text(json.dumps(row, indent=2))
            summary[scenario] = dict(stories=len(words), mean_words=statistics.mean(words),
                old_mean_words=statistics.mean(old_words), reduction=1-sum(words)/sum(old_words),
                min_words=min(words), max_words=max(words), qa_pairs=qa_count, question_kinds=dict(kinds),
                guard_checks=guard_count, distinct_texts=len(text_set),
                mean_visible_events=statistics.mean(visible), mean_internal_events=statistics.mean(internal))
            print(scenario, json.dumps(summary[scenario]), flush=True)
    freeze = json.loads((ROOT / "grammarworlds/portable/sources/pre_holdout_freeze.json").read_text())
    assert all(hashlib.sha256((ROOT / "grammarworlds/portable" / p).read_bytes()).hexdigest() == h
               for p, h in freeze["sha256"].items())
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    lines = ["# Short stories with dialogue and text-evidenced QA", "",
             "Unfiltered seed 7 from every current world. Generation and QA use no models.", ""]
    for row in samples:
        lines += ["## " + row["scenario"].title(), "", row["story"], ""]
        for q in row["qa"]:
            lines += ["**Q: " + q["question"] + "**", "", q["answer"], "",
                      "> Evidence: " + " ".join(e["text"] for e in q["evidence"]), ""]
    (out / "samples.md").write_text("\n".join(lines))
    lines = ["# Short narration and QA audit", "",
        "All seven worlds, seeds 0–59, past and present. No sample filtering. "
        "Original generated versions are stored alongside each new story and QA set.", "",
        "| World | Stories | Old mean words | New mean words | Reduction | QA pairs | Guard checks |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, s in summary.items():
        lines.append(f"| {name} | {s['stories']} | {s['old_mean_words']:.1f} | {s['mean_words']:.1f} | "
                     f"{s['reduction']:.0%} | {s['qa_pairs']} | {s['guard_checks']} |")
    lines += ["", "Every sample completed and replayed, contains at least two physical speakers, "
        "and supplies at least five distinct QA pairs covering at least three question kinds. "
        "Every answer has at least two full sentences and an exact text span tied to a narrated event. "
        "Word probabilities normalize and telescope to surface probability during generation.", "",
        "The underlying event guards and effects are preserved. Routine physical steps may have empty "
        "surfaces; they still execute and appear in the trace. Later narration summarizes only completed "
        "events (e.g. pottery firings). Speech uses typed present-tense clauses inside past/present reporting. "
        "The frozen GF/Codeco-derived grammar modules are unchanged; new speech constructions sit above them.", "",
        "QA is for these generated texts, using authored semantic-to-text alignments. It is not a parser "
        "for arbitrary uploaded stories. Modified text fails closed. Full answers may paraphrase or make "
        "simple local inferences; there is no automatic proof of every English entailment. "
        "The templates and representative samples have been read manually; no new model-judge rating is claimed.", "",
        "Known limits: repeated character names, narrow plot families, a small set of QA templates, "
        "and dialogue that remains direct and simple. Shorter prose is not evidence of increased plot diversity. "
        "These are symbolic rule programs; source bytes/tokens are not neural parameter counts.", "",
        "[Read all seven sample stories with QA and evidence](samples.md).", ""]
    (out / "REPORT.md").write_text("\n".join(lines))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--count", type=int, default=60)
    args = p.parse_args()
    run(args.out, args.count)
