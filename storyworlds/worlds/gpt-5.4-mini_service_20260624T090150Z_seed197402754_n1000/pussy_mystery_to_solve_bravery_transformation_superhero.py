#!/usr/bin/env python3
"""
Storyworld: pussy mystery, bravery, transformation, superhero style.

A small classical story domain where a little pussycat discovers a mystery,
gathers bravery, and transforms into a tiny superhero to solve the problem.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "cat", "kitten", "pussycat"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "Moonbeam City"
    detail: str = "glowing rooftops and silver alleys"


@dataclass
class Mystery:
    id: str
    clue: str
    source: str
    hidden_from: str
    solved_by: str


@dataclass
class Costume:
    id: str
    label: str
    phrase: str
    power: str
    transformation: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "moonbeam": Setting(place="Moonbeam City", detail="glowing rooftops and silver alleys"),
    "harbor": Setting(place="Star Harbor", detail="boats, bridges, and bright water"),
    "garden": Setting(place="Lantern Garden", detail="flower paths and moonlit leaves"),
}

MYSTERIES = {
    "missing_gong": Mystery(
        id="missing_gong",
        clue="a shiny bell-shaped mark on a rooftop tile",
        source="the city tower",
        hidden_from="everyone",
        solved_by="listening to the wind",
    ),
    "stolen_star_map": Mystery(
        id="stolen_star_map",
        clue="tiny dust sparkles by the library window",
        source="the old library",
        hidden_from="the night watch",
        solved_by="following glittery tracks",
    ),
    "silent_fountain": Mystery(
        id="silent_fountain",
        clue="a wet pawprint leading behind the fountain",
        source="the garden fountain",
        hidden_from="the gardeners",
        solved_by="checking the bushes",
    ),
}

COSTUMES = {
    "cape": Costume(
        id="cape",
        label="a bright cape",
        phrase="a bright cape with a star on it",
        power="fly above the rooftops",
        transformation="The cape snapped open and turned the little pussycat into a superhero.",
    ),
    "mask": Costume(
        id="mask",
        label="a silver mask",
        phrase="a silver mask with a tiny moon",
        power="see secret clues",
        transformation="The mask made the little pussycat look bold and mysterious.",
    ),
    "boots": Costume(
        id="boots",
        label="red boots",
        phrase="red boots with springy soles",
        power="leap across the city",
        transformation="The boots gave the little pussycat superhero steps.",
    ),
}

NAMES = ["Poppy", "Mimi", "Luna", "Nina", "Tilly", "Coco", "Mochi", "Zuzu"]
TRAITS = ["curious", "small", "gentle", "brave", "quick", "bright"]


# ---------------------------------------------------------------------------
# Contract helpers
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    costume: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about a pussycat who solves a mystery with bravery and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--name", choices=NAMES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for mystery in MYSTERIES:
            for costume in COSTUMES:
                out.append((place, mystery, costume))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.costume:
        combos = [c for c in combos if c[2] == args.costume]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mystery, costume = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, mystery=mystery, costume=costume, name=name)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _hero_title(hero: Entity) -> str:
    return f"little pussycat {hero.id}"


def _setup(world: World, hero: Entity, mystery: Mystery, costume: Costume) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was a {_hero_title(hero)} who loved moonlit rooftops and quiet mysteries."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had heard about {mystery.source}, but the strange clue had no answer yet."
    )
    world.say(
        f"One evening, {hero.id} found {mystery.clue} and felt a flutter of wonder in {hero.pronoun('possessive')} chest."
    )


def _turn(world: World, hero: Entity, mystery: Mystery, costume: Costume) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.para()
    world.say(
        f"{hero.id} knew the clue was important, but the shadows looked tall and the path looked wide."
    )
    world.say(
        f"{hero.pronoun().capitalize()} took a deep breath and chose bravery instead of hiding."
    )
    hero.memes["bravery"] += 1
    world.say(
        f"Then {hero.id} put on {costume.phrase}. {costume.transformation}"
    )
    hero.wears = costume.id
    hero.traits.append("superhero")
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 2


def _solve(world: World, hero: Entity, mystery: Mystery, costume: Costume) -> None:
    world.para()
    if costume.id == "cape":
        world.say(
            f"With {costume.label}, {hero.id} could {costume.power}, so {hero.pronoun()} flew over the bright roofs to follow the clue."
        )
    elif costume.id == "mask":
        world.say(
            f"With {costume.label}, {hero.id} could {costume.power}, so {hero.pronoun()} noticed the secret clue near the window."
        )
    else:
        world.say(
            f"With {costume.label}, {hero.id} could {costume.power}, so {hero.pronoun()} bounded from ledge to ledge."
        )
    world.say(
        f"The clue led {hero.id} to the place where the mystery had been hiding."
    )
    world.say(
        f"At last, {hero.id} solved the mystery by {mystery.solved_by}."
    )
    world.say(
        f"The city felt safe again, and {hero.id} stood tall, a tiny superhero under the stars."
    )


def tell(setting: Setting, mystery: Mystery, costume: Costume, hero_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="pussycat", traits=["small", "curious"]))
    world.facts.update(hero=hero, mystery=mystery, costume=costume, setting=setting)
    _setup(world, hero, mystery, costume)
    _turn(world, hero, mystery, costume)
    _solve(world, hero, mystery, costume)
    world.facts["transformed"] = True
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    costume: Costume = f["costume"]  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a child about a pussycat named {hero.id} who solves the {mystery.id} mystery.',
        f"Tell a gentle story where {hero.id} finds a clue, shows bravery, and transforms with {costume.label}.",
        f"Write a simple Moonbeam City adventure with a brave pussycat, a mystery, and a happy transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    costume: Costume = f["costume"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little pussycat who became a superhero.",
        ),
        QAItem(
            question=f"What mystery did {hero.id} find first?",
            answer=f"{hero.id} found the clue for the {mystery.id} mystery in {world.setting.place}.",
        ),
        QAItem(
            question=f"What helped {hero.id} transform into a superhero?",
            answer=f"{hero.id} transformed by putting on {costume.phrase}.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the mystery?",
            answer=f"{hero.id} solved it by {mystery.solved_by} and following the clue to the answer.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels scared but still does the helpful thing.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people try to understand or solve.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special powers or gear to help others.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing into a new form or becoming different in a big way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.wears:
            bits.append(f"wears={e.wears}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- mystery_id(M).
costume(C) :- costume_id(C).

can_start(P,M,C) :- place(P), mystery(M), costume(C).
solves(M) :- mystery_id(M).
transforms(C) :- costume_id(C).
brave_story(P,M,C) :- can_start(P,M,C), solves(M), transforms(C).
#show brave_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_id", mid))
    for cid in COSTUMES:
        lines.append(asp.fact("costume_id", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show brave_story/3."))
    return sorted(set(asp.atoms(model, "brave_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Generation / emission
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], COSTUMES[params.costume], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="moonbeam", mystery="missing_gong", costume="cape", name="Poppy"),
    StoryParams(place="harbor", mystery="stolen_star_map", costume="mask", name="Luna"),
    StoryParams(place="garden", mystery="silent_fountain", costume="boots", name="Mimi"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show brave_story/3."))
        print(sorted(set(asp.atoms(model, "brave_story"))))
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = rng_base + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
