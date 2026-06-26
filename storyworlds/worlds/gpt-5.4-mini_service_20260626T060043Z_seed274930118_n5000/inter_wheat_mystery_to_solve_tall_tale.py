#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about an interloper, a wheat field, and a mystery to solve.

Premise:
- A small crew notices strange tracks and missing kernels in a wheat field.
- They follow clues, question the wind, and solve the mystery.
- The ending proves what changed in the field.

This script is self-contained and follows the Storyweavers storyworld contract.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    details: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    culprit: str
    effect: str
    solved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "wheatfield": Place(
        name="the wheat field",
        details="The wheat stood tall as a barn roof, gold as sunrise and whispering in the breeze.",
        affords={"search", "listen", "follow"},
    ),
    "millroad": Place(
        name="the road by the mill",
        details="The road ran past the mill, where dust danced like tiny ghosts.",
        affords={"search", "listen", "follow"},
    ),
    "barnyard": Place(
        name="the barnyard",
        details="The barnyard was broad and windy, with straw underfoot and crows overhead.",
        affords={"search", "listen", "follow"},
    ),
}

MYSTERIES = {
    "missing_kernels": Mystery(
        id="missing_kernels",
        clue="little empty patches in the wheat",
        culprit="a flock of sparrows",
        effect="pecked kernels from the heads of wheat",
        solved_by="watching the birds at dawn",
        tags={"wheat", "bird", "clue"},
    ),
    "odd_tracks": Mystery(
        id="odd_tracks",
        clue="tiny tracks winding between the rows",
        culprit="a lost raccoon",
        effect="sniffed for grubs and slipped through the stalks",
        solved_by="following the tracks to a creek",
        tags={"track", "animal", "clue"},
    ),
    "whispering_stalks": Mystery(
        id="whispering_stalks",
        clue="the wheat bowed in circles as if someone had danced there",
        culprit="the wind",
        effect="whirled through the field and bent the stalks in rings",
        solved_by="waiting for the gusts to return",
        tags={"wind", "clue"},
    ),
}

GIRL_NAMES = ["Mara", "June", "Nina", "Lila", "Ada", "Ruby", "Ivy", "Wren"]
BOY_NAMES = ["Cal", "Otis", "Tom", "Eli", "Jasper", "Reed", "Beau", "Finn"]
TRAITS = ["brave", "curious", "sharp-eyed", "quick-footed", "steady", "merry"]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _hero_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _intro(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"{hero.id} was a little {world.facts['trait']} {hero.type} with a hat too big for the wind, "
        f"and {companion.pronoun('subject')} was a {companion.type} who liked a good mystery."
    )
    world.say(
        f"They lived near {world.place.name}, where the wheat rose so high it looked like a sea made of gold."
    )
    world.say(
        f"One morning, the field had a strange puzzle in it: {world.mystery.clue}."
    )


def _investigate(world: World, hero: Entity, companion: Entity) -> None:
    mystery = world.mystery
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} and {companion.id} stepped between the rows and bent low."
    )
    world.say(
        f"They found {mystery.clue}, and {companion.id} said, "
        f"\"Well, I'll be outdanced by a barn cat if that isn't a clue.\""
    )
    world.say(
        f"{hero.id} touched the broken stalks and noticed the trail led {mystery.solved_by.split(' ')[0]} by the far edge of the field."
    )
    world.facts["clue"] = mystery.clue
    world.facts["effect"] = mystery.effect


def _twist(world: World, hero: Entity, companion: Entity) -> None:
    mystery = world.mystery
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"At first, the tracks looked mighty serious, as if a giant had come tiptoeing through the wheat."
    )
    world.say(
        f"But {companion.id} knelt, smiled, and said the prints were small enough for a hungry little nose."
    )
    world.say(
        f"Then the sky brightened, and the birds came back in a fluttering cloud, just as the field had been waiting for."
    )
    world.facts["culprit"] = mystery.culprit


def _solve(world: World, hero: Entity, companion: Entity) -> None:
    mystery = world.mystery
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"By following {mystery.solved_by}, they solved the puzzle at last."
    )
    world.say(
        f"The culprit was {mystery.culprit}, and the answer was simple as a seed in a palm."
    )
    world.say(
        f"The sparrows were not mean; they were only hungry, and the wheat had been offering them breakfast."
        if mystery.id == "missing_kernels" else
        f"The raccoon was not lost on purpose; it had only wandered where the creek ran cool."
        if mystery.id == "odd_tracks" else
        f"The wind had done nothing wrong at all; it had merely spun through the field like an invisible dancer."
    )
    world.say(
        f"So the mystery ended with a laugh, and the field looked plain again, except now everyone knew its secret."
    )


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place, mystery)
    world.facts.update(place=place, mystery=mystery, trait=params.trait)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
    ))
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type="father" if params.companion == "dad" else "mother",
        label=params.companion,
    ))

    _intro(world, hero, companion)
    world.para()
    world.say(place.details)
    _investigate(world, hero, companion)
    world.para()
    _twist(world, hero, companion)
    _solve(world, hero, companion)

    world.facts["hero"] = hero
    world.facts["companion"] = companion
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short tall tale for children about a wheat field mystery and a clever clue.',
        f"Tell a gentle mystery story set at {world.place.name} that includes wheat, a strange clue, and a happy solution.",
        f"Write a small tall tale where {world.facts['hero'].id} and {world.facts['companion'].id} solve a mystery in wheat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    trait = world.facts["trait"]

    return [
        QAItem(
            question=f"Who solved the mystery in {place.name}?",
            answer=f"{hero.id} and {companion.id} solved it together after they followed the clue through the wheat field.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice in the wheat?",
            answer=f"{hero.id} noticed {mystery.clue}, which helped point them toward the answer.",
        ),
        QAItem(
            question="What was the mystery really about?",
            answer=f"It was about {mystery.culprit}, which caused {mystery.effect}.",
        ),
        QAItem(
            question=f"How did {trait} {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and brave because the mystery was solved and the field made sense again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is wheat?",
            answer="Wheat is a grain plant that grows in tall golden stalks and can be made into flour for bread.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or unknown thing that people try to understand by looking for clues.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find the answer and explain what really happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  place={world.place.name}")
    lines.append(f"  mystery={world.mystery.id}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- mystery_id(M).
solved(P,M) :- clue_seen(P,M), clue_followed(P,M), culprit_known(P,M).
#show solved/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_id", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show setting/1."))
    if not model:
        print("MISMATCH: no ASP model produced.")
        return 1
    print("OK: ASP program is loadable.")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mystery storyworld with wheat and an interloper clue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["mom", "dad"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _hero_name(gender, rng)
    companion = args.companion or rng.choice(["mom", "dad"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show solved/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="wheatfield", mystery="missing_kernels", name="Mara", gender="girl", companion="dad", trait="curious"),
            StoryParams(place="millroad", mystery="odd_tracks", name="Cal", gender="boy", companion="mom", trait="sharp-eyed"),
            StoryParams(place="barnyard", mystery="whispering_stalks", name="Ivy", gender="girl", companion="dad", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
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
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
