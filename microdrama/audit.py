"""Reproduce examples and exhaustive finite-grid evidence: python3 -m microdrama.audit."""
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import random

from .engine import digest
from .palace import Parameters
from .qa import Conversation, questions
from .runtime import generate
from .test_microdrama import check_story, combinations


ROOT = Path(__file__).parent
RECIPES = {
    "library": Parameters(),
    "night_school": Parameters(work="separate", attention=2),
    "locked": Parameters(access="locked"),
    "interrupted": Parameters(attention=4),
    "without_mentor": Parameters(attention=2, mentor=False),
    "with_mentor": Parameters(attention=2),
    "witness": Parameters(witness=True),
}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_story(story, directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "story.txt").write_text(story.text, encoding="utf-8")
    write_json(directory / "trace.json", story.bundle())
    write_json(directory / "qa.json", [asdict(a) for a in questions(story)])
    conversation = Conversation(story, "reader")
    followups = [conversation.ask(q) for q in ("Did Mira's drain work?", "Why?", "What happened next?",
                                               "Who took the cheese?", "Who did the pigs blame for the cheese theft?",
                                               "What became of the palace?", "What happened next?")]
    write_json(directory / "conversation.json", [asdict(a) for a in followups])


def main():
    configurations = list(combinations())
    rows = []
    outcomes = Counter()
    paths = set()
    words = []
    answer_count = 0
    for p in configurations:
        for seed in range(5):
            story = generate(p, seed)
            answer_count += check_story(story)
            outcome = story.world.state["palace.outcome"]
            outcomes[outcome] += 1
            path = [ep.id for ep in story.episodes]
            paths.add(tuple(path))
            words.append(len(story.text.split()))
            rows.append({"parameters": asdict(p), "seed": seed, "outcome": outcome,
                         "state_hash": digest(story.world.state), "text_hash": digest(story.text),
                         "path": path, "qa_count": len(questions(story))})
    recipes = {}
    for name, p in RECIPES.items():
        story = generate(p)
        save_story(story, ROOT / "examples" / name)
        recipes[name] = story
    # This sequence is fixed in advance. No filtering, retrying, or seed search.
    rng = random.Random(777)
    samples = []
    for seed in range(5):
        p = rng.choice(configurations)
        story = generate(p, seed)
        save_story(story, ROOT / "samples" / f"seed{seed}")
        samples.append({"directory": f"samples/seed{seed}", "parameters": asdict(p), "seed": seed,
                        "outcome": story.world.state["palace.outcome"],
                        "path": [ep.id for ep in story.episodes]})
    comparisons = []
    for left, right in (("library", "locked"), ("with_mentor", "night_school"),
                        ("with_mentor", "without_mentor"), ("library", "interrupted"),
                        ("library", "witness")):
        a, b = recipes[left], recipes[right]
        pa, pb = asdict(a.params), asdict(b.params)
        changed = [k for k in pa if pa[k] != pb[k]]
        assert len(changed) == 1
        state_diff = {k: {left: a.world.state[k], right: b.world.state[k]}
                      for k in a.world.state if a.world.state[k] != b.world.state[k]}
        comparisons.append({"left": left, "right": right, "changed_parameter": changed[0],
                            "left_outcome": a.world.state["palace.outcome"],
                            "right_outcome": b.world.state["palace.outcome"], "state_differences": state_diff})
    result = {"scope": "All 48 declared parameter combinations at seeds 0..4; one authored fable",
              "all_passed": True, "source_hash": recipes["library"].bundle()["source_hash"],
              "configurations": len(configurations), "runs": len(rows), "qa_answers_checked": answer_count,
              "outcomes": dict(outcomes), "distinct_paths": len(paths),
              "path_warning": "Order and optional encounters are not new plots",
              "words_min": min(words), "words_max": max(words),
              "counterfactuals": comparisons, "unfiltered_samples": samples, "runs_checked": rows}
    write_json(ROOT / "audit.json", result)
    print(json.dumps({k: result[k] for k in ("all_passed", "configurations", "runs", "qa_answers_checked", "outcomes", "distinct_paths", "words_min", "words_max")}, indent=2))


if __name__ == "__main__":
    main()
