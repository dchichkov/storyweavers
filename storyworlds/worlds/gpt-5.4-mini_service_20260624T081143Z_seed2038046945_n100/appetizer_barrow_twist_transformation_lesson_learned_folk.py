#!/usr/bin/env python3
"""
storyworlds/worlds/appetizer_barrow_twist_transformation_lesson_learned_folk.py
===============================================================================

A small folk-tale storyworld about a humble appetizer, a barrow, a twist,
a transformation, and a lesson learned.

The domain is intentionally tiny: a child or villager wants to carry a special
appetizer to a gathering using a barrow, but a magical twist changes the food,
the carrier, or both. The story then resolves through a transformation that
teaches a clear lesson learned.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- shared results containers imported eagerly
- lazy ASP import inside helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    transformed_from: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    mood: str
    path: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    kind: str = "thing"
    plural: bool = False
    edible: bool = True
    transformed_into: Optional[str] = None


@dataclass
class Twist:
    id: str
    name: str
    effect: str
    transformation: str
    lesson: str
    target: str


@dataclass
class StoryParams:
    place: str
    appetizer: str
    barrow: str
    twist: str
    name: str
    role: str
    seed: Optional[int] = None


PLACES = {
    "village_lane": Place(
        name="the village lane",
        mood="warm",
        path="a crooked stone path",
        affords={"carry", "travel", "gather"},
    ),
    "orchard": Place(
        name="the orchard",
        mood="golden",
        path="a soft dirt path",
        affords={"carry", "travel", "gather"},
    ),
    "market": Place(
        name="the market square",
        mood="busy",
        path="a wide cobbled path",
        affords={"carry", "travel", "gather"},
    ),
}

APPETIZERS = {
    "honey_bun": Item(
        id="honey_bun",
        label="honey bun",
        phrase="a warm honey bun",
        type="bun",
    ),
    "seed_cake": Item(
        id="seed_cake",
        label="seed cake",
        phrase="a small seed cake",
        type="cake",
    ),
    "berry_tart": Item(
        id="berry_tart",
        label="berry tart",
        phrase="a berry tart with a shiny top",
        type="tart",
    ),
}

BARROWS = {
    "wooden_barrow": Item(
        id="wooden_barrow",
        label="barrow",
        phrase="a small wooden barrow",
        type="barrow",
        edible=False,
    ),
    "garden_barrow": Item(
        id="garden_barrow",
        label="barrow",
        phrase="a green garden barrow",
        type="barrow",
        edible=False,
    ),
}

TWISTS = {
    "wind_twist": Twist(
        id="wind_twist",
        name="wind twist",
        effect="the wind flipped the cover and scattered the crumbs",
        transformation="the appetizer became a new kind of snack",
        lesson="careful hands keep good things safe",
        target="appetizer",
    ),
    "spell_twist": Twist(
        id="spell_twist",
        name="spell twist",
        effect="a stray spell gave the barrow a squeaky little voice",
        transformation="the barrow became helpful and kindly",
        lesson="even useful tools can change when treated with care",
        target="barrow",
    ),
    "fox_twist": Twist(
        id="fox_twist",
        name="fox twist",
        effect="a clever fox nudged the wheel, and the journey went sideways",
        transformation="the traveler learned a wiser way to share the food",
        lesson="a mistake can teach a better path",
        target="journey",
    ),
}

ROLES = ["boy", "girl", "child", "village child", "small traveler"]
NAMES = ["Milo", "Nina", "Tomas", "Rosa", "Pip", "Lena", "Ivo", "Mara"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)

    def trace(self) -> str:
        out = ["--- world model state ---"]
        for ent in self.entities.values():
            bits = []
            if ent.owner:
                bits.append(f"owner={ent.owner}")
            if ent.carried_by:
                bits.append(f"carried_by={ent.carried_by}")
            if ent.transformed_from:
                bits.append(f"transformed_from={ent.transformed_from}")
            if ent.meters:
                bits.append(f"meters={ent.meters}")
            if ent.memes:
                bits.append(f"memes={ent.memes}")
            out.append(f"  {ent.id:16} ({ent.type:10}) {' '.join(bits)}")
        return "\n".join(out)


def _pronoun(role: str, case: str = "subject") -> str:
    if role in {"girl"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if role in {"boy"}:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _can_transform(app: Item, twist: Twist, barrow: Item) -> bool:
    return app.type in {"bun", "cake", "tart"} and barrow.type == "barrow" and twist.id in TWISTS


def _turn(world: World, child: Entity, app: Entity, barrow: Entity, twist: Twist) -> None:
    if twist.id == "wind_twist":
        app.meters["crumbled"] = app.meters.get("crumbled", 0) + 1
        world.say(
            f"Then a wind twist came along. It lifted the cloth, and the {app.label} "
            f"lost some of its neatness."
        )
        world.say(
            f"{twist.effect}. The child had to stop and think before going on."
        )
        return
    if twist.id == "spell_twist":
        barrow.memes["voice"] = barrow.memes.get("voice", 0) + 1
        world.say(
            f"Then a spell twist came along. The {barrow.label} gave one tiny squeak "
            f"and the little traveler blinked in surprise."
        )
        world.say(f"{twist.effect}.")
        return
    if twist.id == "fox_twist":
        child.memes["shocked"] = child.memes.get("shocked", 0) + 1
        world.say(
            "Then a fox twist came along. A fox darted past, and the barrow tipped "
            "just enough to wobble the whole plan."
        )
        world.say(f"{twist.effect}.")
        return


def tell(place: Place, appetizer: Item, barrow: Item, twist: Twist, name: str, role: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=role, label=name))
    app = world.add(Entity(id=appetizer.id, type=appetizer.type, label=appetizer.label, phrase=appetizer.phrase))
    row = world.add(Entity(id=barrow.id, type=barrow.type, label=barrow.label, phrase=barrow.phrase))

    world.say(
        f"In {place.name}, there lived a little {role} named {name} who liked to carry "
        f"{app.phrase} in {row.phrase}."
    )
    world.say(
        f"{_pronoun(role).capitalize()} said it was the best way to bring a tasty "
        f"{app.label} to the gathering at the end of the lane."
    )
    world.say(
        f"Each morning, {name} pushed the {row.label} along {place.path}, and the wheels "
        f"made a soft singing sound."
    )

    world.facts.update(
        child=child,
        appetizer=app,
        barrow=row,
        twist=twist,
        place=place,
        role=role,
    )

    world.say("")
    world.say(
        f"But the road was not always kind, and that is where the {twist.name} waited."
    )
    _turn(world, child, app, row, twist)

    # Transformation and lesson learned.
    if twist.id == "wind_twist":
        app.transformed_from = app.id
        app.label = "crumbly sweet bites"
        app.phrase = "crumbly sweet bites"
        world.say(
            f"So {name} changed the plan. {_pronoun(role).capitalize()} broke the {appetizer.label} "
            f"into small pieces and shared them carefully."
        )
        world.say(
            f"By the time {name} reached the gathering, the food had transformed into "
            f"something new, and {twist.lesson}."
        )
    elif twist.id == "spell_twist":
        row.transformed_from = row.id
        row.label = "kindly barrow"
        row.phrase = "a kindly barrow with a cheerful squeak"
        world.say(
            f"So {name} patted the barrow and thanked it for helping. The little voice "
            f"grew gentle, and the barrow transformed into a kinder helper."
        )
        world.say(
            f"At the end, {name} learned that patience can turn a strange moment into "
            f"a friendly one, and {twist.lesson}."
        )
    else:
        child.transformed_from = child.id
        child.memes["wisdom"] = child.memes.get("wisdom", 0) + 1
        world.say(
            f"So {name} slowed down, lifted the appetizer with both hands, and walked "
            f"beside the barrow instead of racing it."
        )
        world.say(
            f"That twist changed the traveler more than the road: {name} became wiser, "
            f"and {twist.lesson}."
        )

    world.say(
        f"At last, {name} arrived at the gathering with a quiet smile, and the ending "
        f"looked brighter than the beginning."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child that includes the words "appetizer", "barrow", and "twist".',
        f"Tell a simple story about {f['child'].label} carrying {f['appetizer'].phrase} in a barrow and meeting a twist.",
        f"Create a gentle transformation story in a village lane where a small traveler learns a lesson after a twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    app = f["appetizer"]
    barrow = f["barrow"]
    twist = f["twist"]
    role = f["role"]
    return [
        QAItem(
            question=f"Who carried the {app.label} in the story?",
            answer=f"{child.label} carried the {app.label} in the {barrow.label} through {world.place.name}.",
        ),
        QAItem(
            question=f"What did the twist do to the story?",
            answer=f"The {twist.name} changed the journey, and the story ended with a transformation and a lesson learned.",
        ),
        QAItem(
            question=f"What did {child.label} learn by the end?",
            answer=f"{child.label} learned that {twist.lesson}. That was the lesson learned after the trouble on the road.",
        ),
        QAItem(
            question=f"What kind of character was {child.label}?",
            answer=f"{child.label} was a little {role} who tried to bring a treat to a gathering.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barrow?",
            answer="A barrow is a small wheeled cart or wheelbarrow used to carry things from one place to another.",
        ),
        QAItem(
            question="What is an appetizer?",
            answer="An appetizer is a small dish or snack served before a bigger meal.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story go in a new direction.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important that helps you make better choices later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for aff in sorted(place.affords):
            lines.append(asp.fact("affords", pid, aff))
    for aid in APPETIZERS:
        lines.append(asp.fact("appetizer", aid))
    for bid in BARROWS:
        lines.append(asp.fact("barrow", bid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    lines.append(asp.fact("transformation", "appetizer"))
    lines.append(asp.fact("transformation", "barrow"))
    lines.append(asp.fact("lesson_learned"))
    return "\n".join(lines)


ASP_RULES = r"""
story(Place, App, Barrow, Twist) :-
    afford_story(Place, App, Barrow, Twist).

afford_story(Place, App, Barrow, Twist) :-
    affords(Place, carry),
    appetizer(App),
    barrow(Barrow),
    twist(Twist).

has_transformation(Twist) :- twist(Twist).
has_lesson(Twist) :- twist(Twist), lesson_learned.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show afford_story/4."))
    return sorted(set(asp.atoms(model, "afford_story")))


def asp_verify() -> int:
    python_set = {
        (place, app, barrow, twist)
        for place in PLACES
        for app in APPETIZERS
        for barrow in BARROWS
        for twist in TWISTS
    }
    clingo_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python registry combos ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python registry combos:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: appetizer, barrow, and twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--appetizer", choices=APPETIZERS)
    ap.add_argument("--barrow", choices=BARROWS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    appetizer = args.appetizer or rng.choice(list(APPETIZERS))
    barrow = args.barrow or rng.choice(list(BARROWS))
    twist = args.twist or rng.choice(list(TWISTS))
    role = args.role or rng.choice(ROLES)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, appetizer=appetizer, barrow=barrow, twist=twist, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    appetizer = APPETIZERS[params.appetizer]
    barrow = BARROWS[params.barrow]
    twist = TWISTS[params.twist]
    world = tell(place, appetizer, barrow, twist, params.name, params.role)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="village_lane", appetizer="honey_bun", barrow="wooden_barrow", twist="wind_twist", name="Milo", role="boy"),
    StoryParams(place="orchard", appetizer="seed_cake", barrow="garden_barrow", twist="spell_twist", name="Rosa", role="girl"),
    StoryParams(place="market", appetizer="berry_tart", barrow="wooden_barrow", twist="fox_twist", name="Pip", role="child"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show afford_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.appetizer} / {p.barrow} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
