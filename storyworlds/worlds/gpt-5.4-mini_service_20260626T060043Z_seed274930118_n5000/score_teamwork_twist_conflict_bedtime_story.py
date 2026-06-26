#!/usr/bin/env python3
"""
storyworlds/worlds/score_teamwork_twist_conflict_bedtime_story.py
=================================================================

A small bedtime-story world about a child, a gentle conflict, a teamwork
solution, and a tiny twist that turns into a cozy ending.

Core premise:
- A child is trying to get ready for bed.
- Something about bedtime is not going smoothly.
- A helper and child work together.
- A twist changes what they expected.
- The story ends with calm, safe, sleepy relief.

The world tracks both physical state in meters and emotional state in memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

WORLD_NAME = "bedtime_score_teamwork_twist_conflict"

BEDTIME_HINTS = {
    "star": "The room had a little star sticker on the wall that glowed softly.",
    "lamp": "A small lamp made a warm circle of light beside the bed.",
    "book": "A picture book waited on the pillow for one last story.",
    "blanket": "A soft blanket lay folded at the foot of the bed.",
}

TASKS = {
    "tidy": {
        "verb": "tidy the room",
        "help_verb": "put away the toys together",
        "result": "neat",
        "item": "toys",
        "score_gain": 2,
        "twist": "a toy had rolled under the bed",
    },
    "pajamas": {
        "verb": "find the pajamas",
        "help_verb": "search together for the pajamas",
        "result": "ready for bed",
        "item": "pajamas",
        "score_gain": 2,
        "twist": "the pajamas were inside the blanket fort",
    },
    "teeth": {
        "verb": "brush teeth",
        "help_verb": "brush together at the sink",
        "result": "fresh",
        "item": "toothbrush",
        "score_gain": 1,
        "twist": "the toothbrush was behind the cup",
    },
    "stuffed": {
        "verb": "find the stuffed bunny",
        "help_verb": "look together for the stuffed bunny",
        "result": "safe and snuggly",
        "item": "stuffed bunny",
        "score_gain": 3,
        "twist": "the bunny was tucked under a pillow",
    },
}

PLACES = {
    "bedroom": "the bedroom",
    "hall": "the hallway",
    "bathroom": "the bathroom",
    "stair": "the stairs landing",
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ella", "Ivy", "Maya"]
BOY_NAMES = ["Leo", "Noah", "Eli", "Theo", "Finn", "Max"]
HELPER_NAMES = ["Mom", "Dad", "Grandma", "Grandpa"]

TRAITS = ["sleepy", "curious", "gentle", "stubborn", "hopeful", "playful"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    worn_by: Optional[str] = None
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    info: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with score, teamwork, twist, and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["Mom", "Dad", "Grandma", "Grandpa"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _random_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    task = args.task or rng.choice(list(TASKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _random_name(gender, rng)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, name=name, gender=gender, helper=helper, trait=trait)


def _is_reasonable(params: StoryParams) -> bool:
    return params.place in PLACES and params.task in TASKS


def _maybe_raise_invalid(params: StoryParams) -> None:
    if not _is_reasonable(params):
        raise StoryError("The bedtime story choices do not form a reasonable little scene.")


def _task(params: StoryParams) -> dict:
    return TASKS[params.task]


def generate(params: StoryParams) -> StorySample:
    _maybe_raise_invalid(params)
    task = _task(params)
    world = World()

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"sleepy": 0.0, "calm": 0.0, "score": 0.0, "conflict": 0.0},
        memes={"hope": 0.0, "worry": 0.0, "love": 0.0},
        info={"trait": params.trait},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="mother" if params.helper in {"Mom", "Grandma"} else "father",
        meters={"calm": 0.0, "score": 0.0},
        memes={"care": 1.0},
    ))
    item = world.add(Entity(
        id=task["item"],
        kind="thing",
        type="thing",
        label=task["item"],
        owner=child.id,
        caretaker=helper.id,
        meters={"missing": 1.0, "found": 0.0},
    ))

    world.say(f"At {PLACES[params.place]}, {params.name} was a {params.trait} little {params.gender} getting ready for bed.")
    world.say(f"{params.helper} came to help with {task['verb']}, because bedtime went easier when they worked as a team.")
    world.say(random.choice(list(BEDTIME_HINTS.values())))

    world.para()
    child.memes["worry"] += 1
    child.meters["conflict"] += 1
    world.say(f"But there was a small conflict: {params.name} could not settle down until {task['item']} was found.")
    world.say(f"{params.name} wanted to {task['verb']}, but the room felt too puzzly and too dark.")

    world.para()
    child.meters["score"] += task["score_gain"]
    helper.meters["score"] += task["score_gain"]
    child.memes["love"] += 1
    helper.memes["care"] += 1
    world.say(f"So they made a teamwork plan. {params.name} looked under the bed while {params.helper} checked the pillow pile.")
    world.say(f"That teamwork gave them a little score: {task['score_gain']} points each, and the search became a game instead of a worry.")

    world.para()
    item.meters["missing"] = 0.0
    item.meters["found"] = 1.0
    child.meters["conflict"] = 0.0
    child.meters["calm"] = 1.0
    helper.meters["calm"] = 1.0
    child.meters["score"] += 1
    helper.meters["score"] += 1
    world.say(f"Then came the twist: the {task['item']} was in a funny hiding place, right where nobody first thought to look.")
    world.say(f"They laughed softly, because the twist turned the conflict into a cozy surprise.")
    world.say(f"At last {params.name} was {task['result']}, and {params.helper} tucked the blanket up just right.")
    world.say(f"The room grew quiet, the score was enough, and {params.name} drifted toward sleep with a happy little sigh.")

    world.facts.update(
        child=child,
        helper=helper,
        item=item,
        params=params,
        task=task,
        score=child.meters["score"],
        resolved=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    task = world.facts["task"]
    return [
        f"Write a gentle bedtime story about {p.name}, {p.helper}, and {task['item']} with teamwork and a small twist.",
        f"Tell a bedtime story where a child named {p.name} has a conflict before bed, then scores points by helping with {task['verb']}.",
        f"Create a cozy story for a little child about {task['item']} being found after teamwork solves a bedtime problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    task = world.facts["task"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about {p.name}, a {p.trait} little {p.gender}, and {p.helper} helping at bedtime.",
        ),
        QAItem(
            question=f"What problem caused the conflict before sleep?",
            answer=f"{p.name} could not settle down until the {task['item']} was found, so bedtime felt stuck for a moment.",
        ),
        QAItem(
            question=f"How did the teamwork help?",
            answer=f"{p.name} and {p.helper} searched together, earned a little score, and turned the problem into a game.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the {task['item']} was hiding in a funny place, so the conflict became a cozy surprise instead of a big worry.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {p.name} calm, {p.helper} tucking in the blanket, and everyone ready for sleep.",
        ),
        QAItem(
            question=f"How many score points did the teamwork give them?",
            answer=f"The teamwork gave them a small score boost, and {p.name} also earned an extra point when the {task['item']} was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together instead of alone.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what the characters expected.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes things hard for a moment.",
        ),
        QAItem(
            question="Why are bedtime stories usually calm?",
            answer="Bedtime stories are usually calm because they help children feel safe, quiet, and ready to sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} info={dict(e.info)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show compatible/2.
compatible(Place,Task) :- place(Place), task(Task).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {(p, t) for p in PLACES for t in TASKS if True}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in ASP:", sorted(cl - py))
    print("Only in Python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(place="bedroom", task="stuffed", name="Mia", gender="girl", helper="Mom", trait="sleepy"),
    StoryParams(place="hall", task="pajamas", name="Leo", gender="boy", helper="Dad", trait="curious"),
    StoryParams(place="bathroom", task="teeth", name="Nora", gender="girl", helper="Grandma", trait="gentle"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible bedtime combinations")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
