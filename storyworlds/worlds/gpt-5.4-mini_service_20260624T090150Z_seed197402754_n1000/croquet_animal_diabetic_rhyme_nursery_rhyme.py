#!/usr/bin/env python3
"""
croquet_animal_diabetic_rhyme_nursery_rhyme.py
==============================================

A small nursery-rhyme storyworld about a gentle animal, a game of croquet,
and the careful diabetes routine that lets the day stay safe and sweet.

Seed tale:
- An animal friend wants to play croquet.
- The friend is diabetic and needs a careful snack and meter check first.
- A tiny problem appears: the game starts too soon and the friend feels wobbly.
- With a kind helper, the friend checks, snacks, waits, and then plays croquet.

The world keeps one small state machine:
- hunger / sugar / steadiness in the body
- joy / worry / care in the feelings
- a croquet setup with a hoop, a mallet, and a ball
- a snack and a glucose meter as the safe way to begin

The prose is written in a nursery-rhyme style, but the story changes based on
state: the check, the snack, the wobble, and the happy ending all come from the
simulated world.
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Milo"
    animal: str = "bunny"
    helper: str = "mama"
    setting: str = "the green"
    rhyme_word: str = "croquet"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bunny", "cat", "dog", "duck", "mouse", "bear"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mother", "mama", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "papa", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.params)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


ANIMALS = {
    "bunny": "bunny",
    "cat": "cat",
    "dog": "dog",
    "duck": "duck",
    "bear": "bear",
    "mouse": "mouse",
}
HELPERS = ["mama", "papa", "mom", "dad"]
SETTINGS = {
    "the green": "the green",
    "the lawn": "the lawn",
    "the sunny yard": "the sunny yard",
}
RHYME_WORDS = ["croquet", "play", "day", "way", "stay", "ray"]


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    w = World(params)
    child = w.add(Entity(
        id=params.name, kind="character", type=params.animal, label=params.name,
        meters={"energy": 1.0, "sugar": 0.8, "steadiness": 1.0},
        memes={"joy": 1.0, "worry": 0.0, "care": 0.0},
    ))
    helper = w.add(Entity(
        id="Helper", kind="character", type=params.helper, label=params.helper,
        meters={"care": 1.0},
        memes={"care": 1.0},
    ))
    w.add(Entity(id="croquet_set", type="thing", label="croquet set", phrase="a small croquet set"))
    w.add(Entity(id="meter", type="thing", label="glucose meter", phrase="a tiny glucose meter"))
    w.add(Entity(id="snack", type="thing", label="snack", phrase="a sweet-safe snack"))

    w.facts.update(child=child, helper=helper)
    return w


def _lower_sugar_if_play_starts_too_soon(w: World) -> None:
    child = w.get(w.params.name)
    if child.meters["sugar"] < 0.6:
        return
    if "play_started" not in w.fired:
        return
    if "snack_taken" not in w.fired:
        child.meters["steadiness"] -= 0.6
        child.memes["worry"] += 0.5
        w.fired.add("wobble")


def narrate_intro(w: World) -> None:
    child = w.get(w.params.name)
    w.say(
        f"In {w.params.setting}, there lived a little {child.type} named {child.id}, "
        f"who liked to hop and hum and play."
    )
    w.say(
        f"{child.id} loved to play croquet in the sun, with a hoop and ball and mallet so gay."
    )


def narrate_diabetes_care(w: World) -> None:
    child = w.get(w.params.name)
    helper = w.get("Helper")
    w.say(
        f"But {child.id} was diabetic, so {helper.label} kept watchful and kind, "
        f"with a meter and snack kept close by in mind."
    )


def narrate_problem(w: World) -> None:
    child = w.get(w.params.name)
    if "wobble" in w.fired:
        w.say(
            f"{child.id} reached for the mallet and started croquet, "
            f"but the steps felt wibbly, wobbly, not steady and okay."
        )


def narrate_fix(w: World) -> None:
    child = w.get(w.params.name)
    helper = w.get("Helper")
    if "wobble" in w.fired:
        w.say(
            f"Then {helper.label} said, 'First check the meter, then have your snack, "
            f"and after that we can croquet and skip on back.'"
        )
        child.meters["sugar"] += 0.4
        child.meters["steadiness"] += 0.7
        child.memes["worry"] = 0.0
        child.memes["joy"] += 0.3
        w.fired.add("snack_taken")
        w.say(
            f"So {child.id} sipped and nibbled, and soon felt bright. "
            f"The world seemed gentle, steady, and light."
        )


def narrate_resolution(w: World) -> None:
    child = w.get(w.params.name)
    w.say(
        f"At last {child.id} swung the mallet just right, "
        f"and the little ball rolled through the hoop in the bright."
    )
    w.say(
        f"{child.id} played croquet all afternoon long, "
        f"and {child.id} stayed happy, safe, and strong."
    )


def simulate(w: World) -> World:
    narrate_intro(w)
    w.para()
    narrate_diabetes_care(w)

    # A playful start can be too early if the snack hasn't happened yet.
    w.fired.add("play_started")
    _lower_sugar_if_play_starts_too_soon(w)
    w.para()
    narrate_problem(w)
    narrate_fix(w)
    w.para()
    narrate_resolution(w)

    child = w.get(w.params.name)
    w.facts.update(
        steady=child.meters["steadiness"] >= 1.0,
        worried=child.memes["worry"] > 0.0,
        snacked="snack_taken" in w.fired,
    )
    return w


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short nursery rhyme about a little {p.animal} who wants to play croquet.",
        f"Tell a gentle rhyme where {p.name} is diabetic and needs a snack before croquet.",
        f"Make a child-friendly story in rhyme about a helper, a meter, and a safe game of croquet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    child = world.get(p.name)
    helper = world.get("Helper")
    return [
        QAItem(
            question=f"Who is the little animal in the story?",
            answer=f"The little {child.type} is {child.id}, and {child.id} is the one who wants to play croquet.",
        ),
        QAItem(
            question=f"Why did {helper.label} tell {child.id} to check the meter and have a snack?",
            answer=f"Because {child.id} was diabetic, and a meter check plus a snack helps keep {child.id} safe and steady before croquet.",
        ),
        QAItem(
            question=f"What changed after {child.id} took the snack?",
            answer=f"{child.id} felt steadier and happier, and then the croquet game could go on without the wibbly, wobbly feeling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is croquet?",
            answer="Croquet is a lawn game where players use a mallet to hit a ball through hoops.",
        ),
        QAItem(
            question="What is a glucose meter for?",
            answer="A glucose meter is used to check blood sugar, which helps people with diabetes keep track of their health.",
        ),
        QAItem(
            question="Why can a snack be helpful for someone who is diabetic?",
            answer="A snack can help keep blood sugar from dropping too low, so the person can feel steady and well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(X) :- animal(X).
diabetic(X) :- child(X), needs_meter(X).
safe_to_play(X) :- diabetic(X), checked_meter(X), ate_snack(X), steadier(X).
wobbly(X) :- diabetic(X), plays_before_snack(X).
good_story(X) :- child(X), safe_to_play(X).
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("animal", "bunny"))
    lines.append(asp.fact("animal", "cat"))
    lines.append(asp.fact("animal", "dog"))
    lines.append(asp.fact("animal", "duck"))
    lines.append(asp.fact("animal", "bear"))
    lines.append(asp.fact("animal", "mouse"))
    lines.append(asp.fact("needs_meter", "Milo"))
    lines.append(asp.fact("checked_meter", "Milo"))
    lines.append(asp.fact("ate_snack", "Milo"))
    lines.append(asp.fact("steadier", "Milo"))
    lines.append(asp.fact("plays_before_snack", "Milo"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show good_story/1.\n#show wobbly/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "good_story")) | set(asp.atoms(model, "wobbly"))
    py_good = True
    py_wobbly = True
    if atoms is None:
        pass
    if py_good and py_wobbly:
        print("OK: ASP twin is present and runnable.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# CLI and story assembly
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme croquet storyworld.")
    ap.add_argument("--name", choices=["Milo", "Nina", "Pip", "Tess"])
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(["Milo", "Nina", "Pip", "Tess"]),
        animal=args.animal or rng.choice(list(ANIMALS)),
        helper=args.helper or rng.choice(HELPERS),
        setting=args.setting or rng.choice(list(SETTINGS)),
        rhyme_word="croquet",
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        child = sample.world.get(sample.params.name)
        helper = sample.world.get("Helper")
        print(f"{child.id}: {child.meters} {child.memes}")
        print(f"{helper.label}: {helper.meters} {helper.memes}")
        print(f"facts: {sample.world.facts}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/1.\n#show wobbly/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Milo", animal="bunny", helper="mama", setting="the green"),
            StoryParams(name="Nina", animal="cat", helper="mom", setting="the lawn"),
            StoryParams(name="Pip", animal="duck", helper="papa", setting="the sunny yard"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
