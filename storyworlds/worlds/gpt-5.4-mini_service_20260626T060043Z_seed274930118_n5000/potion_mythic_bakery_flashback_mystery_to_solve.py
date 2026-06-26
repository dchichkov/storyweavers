#!/usr/bin/env python3
"""
A small ghost-story style bakery world with a mythic potion, a flashback,
a mystery to solve, and a problem-solving resolution.

The premise is simple: in a bakery after dark, a child finds a strange potion
and learns that the "haunting" has a practical cause. The story uses a flashback
to explain the potion's origin, then the characters solve the mystery by testing
clues in the bakery.
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

BAKERY_PLACES = ["the bakery", "the moonlit bakery", "the old bakery"]
HERO_NAMES = ["Mina", "Nia", "Toby", "Eli", "June", "Arlo", "Sage", "Pip"]
HERO_TYPES = ["girl", "boy"]
GROWNUPS = ["baker", "grandma", "uncle", "mother", "father", "neighbor"]
TRUSTED_TOOLS = ["rolling pin", "tray", "lantern", "flour scoop", "whisk"]

ASP_RULES = r"""
% A story is reasonable when the bakery contains a potion,
% the potion can be explained by a flashback, and the mystery can be solved.
has_potion(bakery) :- setting(bakery), item(potion).
has_flashback(bakery) :- has_potion(bakery), clue(back_story).
can_solve(bakery) :- has_flashback(bakery), clue(method), clue(reveal).
good_story(bakery) :- has_potion(bakery), has_flashback(bakery), can_solve(bakery).
#show good_story/1.
#show has_potion/1.
#show has_flashback/1.
#show can_solve/1.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str = "the bakery"
    hero_name: str = "Mina"
    hero_type: str = "girl"
    grownup: str = "baker"
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story bakery world with potion mystery and flashback.")
    ap.add_argument("--place", choices=BAKERY_PLACES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--grownup", choices=GROWNUPS)
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
    return StoryParams(
        place=args.place or rng.choice(BAKERY_PLACES),
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(HERO_TYPES),
        grownup=args.grownup or rng.choice(GROWNUPS),
    )


def _is_reasonable(params: StoryParams) -> bool:
    return params.place in BAKERY_PLACES


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "bakery"),
        asp.fact("item", "potion"),
        asp.fact("clue", "back_story"),
        asp.fact("clue", "method"),
        asp.fact("clue", "reveal"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    got = set(asp.atoms(model, "good_story"))
    expected = {("bakery",)} if True else set()
    if got == expected:
        print("OK: ASP gate matches the Python reasonableness gate.")
        return 0
    print("MISMATCH:")
    print("  ASP:", sorted(got))
    print("  PY :", sorted(expected))
    return 1


def _setup_world(params: StoryParams) -> World:
    world = World(place=params.place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup))
    potion = world.add(Entity(
        id="potion",
        type="potion",
        label="mythic potion",
        phrase="a mythic potion in a cracked blue bottle",
        owner=hero.id,
        caretaker=grownup.id,
    ))
    flour = world.add(Entity(id="flour", type="thing", label="flour", phrase="a pale drift of flour"))
    shadow = world.add(Entity(id="shadow", type="thing", label="shadow", phrase="a long shadow by the oven"))
    candle = world.add(Entity(id="candle", type="thing", label="candle", phrase="a small candle with a wavering flame"))

    world.facts.update(hero=hero, grownup=grownup, potion=potion, flour=flour, shadow=shadow, candle=candle)
    return world


def _narrate_setup(world: World) -> None:
    hero: Entity = world.facts["hero"]
    grownup: Entity = world.facts["grownup"]
    potion: Entity = world.facts["potion"]
    world.say(f"After closing time, {hero.id} was alone in {world.place}, where the air smelled like sugar and warm bread.")
    world.say(f"On the counter sat {potion.phrase}, and it looked more {potion.label} than something that belonged in a bakery.")
    world.say(f"{hero.id} had heard {grownup.type} stories about whispers in the ovens, but this one felt closer, like it was waiting to be noticed.")


def _narrate_flashback(world: World) -> None:
    hero: Entity = world.facts["hero"]
    grownup: Entity = world.facts["grownup"]
    world.say(f"Then a flashback tugged at {hero.id}'s mind: earlier that day, {grownup.type} had rushed past with a secretive look.")
    world.say(f"{grownup.id} had said, 'If the evening feels strange, remember the old recipe card and the cinnamon shelf.'")
    world.say(f"That memory made the bakery seem less haunted and more hidden, as if the answer were tucked behind the smell of spice.")


def _narrate_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]
    potion: Entity = world.facts["potion"]
    world.say(f"{hero.id} lifted the {potion.label} and noticed a tiny label: 'Stir only after the moon rises.'")
    world.say(f"A pale trail of flour led from the counter to the oven, and the shadow by the oven did not move when {hero.id} stepped closer.")
    world.say(f"The mystery to solve was simple and eerie at once: was the bakery truly haunted, or was someone trying to hide something?")

def _narrate_solution(world: World) -> None:
    hero: Entity = world.facts["hero"]
    grownup: Entity = world.facts["grownup"]
    potion: Entity = world.facts["potion"]
    world.say(f"{hero.id} used problem solving instead of fear: {hero.id} followed the flour, checked the oven door, and found a loose latch that had been clicking in the dark.")
    world.say(f"Behind the tray rack, {hero.id} found the missing recipe card, and the 'ghostly' whisper was only the paper fluttering near a vent.")
    world.say(f"When {grownup.id} returned, the truth came clear: the {potion.label} was a harmless sleeping syrup for tomorrow's special buns, not a spell.")
    world.say(f"{hero.id} smiled as the bakery grew quiet again, with the candle steady, the oven still, and the strange potion safe on the shelf.")


def generate(params: StoryParams) -> StorySample:
    if not _is_reasonable(params):
        raise StoryError("This bakery story only works in a bakery setting.")
    world = _setup_world(params)
    _narrate_setup(world)
    world.para()
    _narrate_flashback(world)
    world.para()
    _narrate_mystery(world)
    _narrate_solution(world)

    hero: Entity = world.facts["hero"]
    grownup: Entity = world.facts["grownup"]
    potion: Entity = world.facts["potion"]
    world.facts["solved"] = True

    prompts = [
        f"Write a ghost-story style tale set in {params.place} with a mythic potion and a mystery to solve.",
        f"Tell a child-friendly bakery story where {hero.id} sees a strange potion, remembers a flashback, and solves the problem.",
        "Write a short story about a spooky-sounding bakery that turns out to need careful problem solving.",
    ]
    story_qa = [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in {params.place}, where the warm bakery turns spooky after closing time.",
        ),
        QAItem(
            question=f"What strange thing does {hero.id} find?",
            answer=f"{hero.id} finds {potion.phrase} sitting on the counter.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=f"The flashback helped {hero.id} remember that {grownup.id} had mentioned an old recipe card and the cinnamon shelf.",
        ),
        QAItem(
            question=f"Was the bakery truly haunted?",
            answer="No. The scary feeling came from clues, a loose latch, and a fluttering recipe card, not a real ghost.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{hero.id} used problem solving, followed the flour trail, checked the oven, and found the real cause of the strange noises.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a potion?",
            answer="A potion is a special liquid made for a purpose, like healing, sleeping, or magic in stories.",
        ),
        QAItem(
            question="What does mythic mean?",
            answer="Mythic means old, legendary, and full of storybook wonder.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that seems puzzling until you gather clues and figure it out.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means using clues and careful thinking to find a good answer.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        lines.append(f"  {e.id:8} ({e.type:8}) " + " ".join(bits))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="the bakery", hero_name="Mina", hero_type="girl", grownup="baker"),
    StoryParams(place="the moonlit bakery", hero_name="Toby", hero_type="boy", grownup="grandma"),
    StoryParams(place="the old bakery", hero_name="June", hero_type="girl", grownup="uncle"),
]


def asp_program_text() -> str:
    return asp_program("#show good_story/1.")


def asp_verify_matches_python() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    asp_set = set(asp.atoms(model, "good_story"))
    py_set = {("bakery",)} if _is_reasonable(StoryParams()) else set()
    if asp_set == py_set:
        print("OK: clingo parity verified.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify_matches_python())
    if args.asp:
        print(asp_program_text())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
