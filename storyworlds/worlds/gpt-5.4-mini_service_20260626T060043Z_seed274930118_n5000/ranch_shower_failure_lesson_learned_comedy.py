#!/usr/bin/env python3
"""
ranch_shower_failure_lesson_learned_comedy.py
=============================================

A small standalone storyworld about a ranch, a shower, a failure, and a funny
lesson learned.

Premise:
- A child at a ranch tries to use the bathroom shower to clean up a dusty animal
  or gear after a messy ranch chore.
- The attempt goes wrong in a harmless, comedic way.
- A helpful adult points out the better tool, and the child learns a simple
  lesson.

The world is intentionally small:
- physical meters: dust, wet, soap, cleanup, etc.
- emotional memes: pride, embarrassment, laughter, relief, lesson_learned

The story is generated from simulated state, not from a frozen template.
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
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ranch:
    place: str = "the ranch"
    has_shower: bool = True
    has_barn_hose: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    helper: str
    animal: str
    seed: Optional[int] = None


class World:
    def __init__(self, ranch: Ranch) -> None:
        self.ranch = ranch
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
GIRL_NAMES = ["Maya", "Lucy", "Nora", "Ella", "Mia"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Leo", "Sam"]
TRAITS = ["curious", "cheerful", "silly", "stubborn", "brave"]

ANIMALS = {
    "pony": {
        "label": "pony",
        "phrase": "a dusty little pony",
        "mess": "dust",
        "cleaning_tool": "bucket and sponge",
        "reason": "a pony is too big and wiggly for the bathroom shower",
    },
    "dog": {
        "label": "dog",
        "phrase": "a muddy ranch dog",
        "mess": "mud",
        "cleaning_tool": "garden hose",
        "reason": "dogs do better with warm water outside than with a tiny shower",
    },
    "goat": {
        "label": "goat",
        "phrase": "a shaggy goat",
        "mess": "hay",
        "cleaning_tool": "brush",
        "reason": "a brush works better for goat hair than a shower",
    },
}

HELPERS = {
    "mother": "mom",
    "father": "dad",
    "ranch hand": "ranch hand",
    "grandpa": "grandpa",
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A shower failure happens when the child tries to clean a ranch animal with the shower.
failure(S) :- ranch(R), shower(S), animal(A), tries_clean_with_shower(A, S).
lesson_learned :- failure(_), helper_suggests_better_tool.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("ranch", "main"),
        asp.fact("shower", "bathroom"),
    ]
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    lines.append(asp.fact("helper_suggests_better_tool"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show lesson_learned/0."))
    ok = any(sym.name == "lesson_learned" for sym in model)
    if ok:
        print("OK: ASP twin produces lesson_learned.")
        return 0
    print("MISMATCH: ASP twin did not derive lesson_learned.")
    return 1


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(Ranch())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=HELPERS[params.parent]))
    helper = world.add(Entity(id="Helper", kind="character", type="ranch hand", label=HELPERS[params.helper]))
    animal_cfg = ANIMALS[params.animal]
    animal = world.add(Entity(
        id="Animal",
        kind="thing",
        type=params.animal,
        label=animal_cfg["label"],
        phrase=animal_cfg["phrase"],
        caretaker=helper.id,
    ))

    hero.memes["curiosity"] = 1
    hero.memes["pride"] = 1

    # Act 1: setup
    world.say(f"{hero.id} spent the morning at {world.ranch.place} with {hero.pronoun('possessive')} {parent.label}.")
    world.say(f"{hero.id} loved helping with ranch chores, especially when there was something funny to try.")
    world.say(f"That day, {hero.id} noticed {animal.phrase} and thought the bathroom shower could fix everything.")
    world.para()

    # Act 2: attempt and failure
    world.say(f"{hero.id} dragged the {animal.label} toward the shower with a very serious face.")
    world.say(f"The plan was to use the shower like a quick cleanup machine, but it was a silly idea.")
    hero.meters["effort"] = hero.meters.get("effort", 0) + 1
    animal.meters["mess"] = animal.meters.get("mess", 0) + 1
    animal.meters["wet"] = animal.meters.get("wet", 0) + 1
    hero.memes["confidence"] = 1
    hero.memes["failure"] = 1
    world.say(f"The shower sputtered, splashed, and made a bigger mess than before.")
    world.say(f"{hero.id} blinked at the slippery floor and heard {hero.pronoun('possessive')} own giggle echo back.")
    world.para()

    # Act 3: lesson learned
    world.say(f"{helper.label.capitalize()} stepped in, laughing kindly.")
    world.say(f'"That shower is for people," {helper.label} said. "For {animal.label}s, use the {animal_cfg["cleaning_tool"]} instead."')
    world.say(f"{hero.id} grinned, wiped {hero.pronoun('possessive')} hands on {hero.pronoun('possessive')} jeans, and learned a good ranch lesson.")
    world.say(f"After that, {hero.id} helped the right way, and everybody had a better time.")
    hero.memes["embarrassment"] = 1
    hero.memes["relief"] = 1
    hero.memes["lesson_learned"] = 1
    helper.memes["amusement"] = 1
    parent.memes["pride"] = 1
    animal.meters["mess"] = 0
    animal.meters["wet"] = 0

    world.facts.update(
        hero=hero,
        parent=parent,
        helper=helper,
        animal=animal,
        animal_cfg=animal_cfg,
        failure=True,
        lesson_learned=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    animal_cfg = f["animal_cfg"]
    return [
        f'Write a funny short story for a small child about a ranch, a shower, and a mistake that teaches a lesson.',
        f"Tell a comedy story where {hero.id} tries to clean {animal_cfg['phrase']} with a shower and learns what tool works better.",
        f'Write a gentle ranch story that ends with a lesson learned after a shower failure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    helper: Entity = f["helper"]
    animal_cfg = f["animal_cfg"]
    animal: Entity = f["animal"]

    return [
        QAItem(
            question=f"Why did {hero.id} think the shower would help?",
            answer=f"{hero.id} thought the shower would clean {animal_cfg['phrase']} fast, but that was a funny mistake because the shower was the wrong tool.",
        ),
        QAItem(
            question=f"What went wrong when {hero.id} tried to use the shower?",
            answer=f"The shower splashed everywhere, made the floor slippery, and turned the cleanup into a bigger mess instead of a success.",
        ),
        QAItem(
            question=f"Who helped {hero.id} figure out the better way?",
            answer=f"{helper.label.capitalize()} helped by laughing kindly and explaining that {animal_cfg['reason']}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that at the ranch, it matters to use the right tool for the job, even when the first idea sounds funny.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ranch?",
            answer="A ranch is a big place where people care for animals and do outdoor work.",
        ),
        QAItem(
            question="What is a shower for?",
            answer="A shower is for washing people with water and soap.",
        ),
        QAItem(
            question="What does it mean when something fails?",
            answer="When something fails, it does not work the way it should.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something better after an experience, so you can do a wiser thing next time.",
        ),
    ]


# ---------------------------------------------------------------------------
# Parser and sampling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about a ranch shower failure and a lesson learned.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--animal", choices=list(ANIMALS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    helper = args.helper or rng.choice(list(HELPERS))
    animal = args.animal or rng.choice(list(ANIMALS))
    return StoryParams(name=name, gender=gender, parent=parent, helper=helper, animal=animal)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show lesson_learned/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this tiny world, but this seed uses the Python gate directly.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(name="Maya", gender="girl", parent="mother", helper="ranch hand", animal="pony"),
            StoryParams(name="Ben", gender="boy", parent="father", helper="grandpa", animal="dog"),
            StoryParams(name="Lucy", gender="girl", parent="mother", helper="father", animal="goat"),
        ]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
