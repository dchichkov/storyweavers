#!/usr/bin/env python3
"""
A small story world about a historic burnous, a spooky misunderstanding, and a
surprise that turns out kind.

The seed tale:
---
In an old historic house, a child finds a burnous hanging on a peg.
At first the child thinks the soft white hood belongs to a ghost.
A sudden breeze makes the cloth lift, and everyone gasps.
Then a grandparent smiles, explains that the burnous is only an old cloak
kept safe from the cold, and the child feels brave enough to wear it.

This world keeps the story tightly constraint-driven:
- a historic place
- a burnous or similar cloak
- a spooky misunderstanding
- a surprise reveal
- a gentle ghost-story atmosphere
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    old: bool = True
    indoors: bool = True
    echoes: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    garment: str
    hero_name: str
    hero_type: str
    elder_type: str
    season: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(self.events)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "old_house": Setting(place="the old historic house", old=True, indoors=True, echoes=True, affords={"gather"}),
    "museum_room": Setting(place="the quiet museum room", old=True, indoors=True, echoes=True, affords={"gather"}),
    "stone_attic": Setting(place="the stone attic", old=True, indoors=True, echoes=True, affords={"gather"}),
}

GARMENTS = {
    "burnous": {
        "label": "burnous",
        "phrase": "a soft white burnous with a deep hood",
        "kind": "cloak",
        "sound": "whispered",
        "look": "soft and ghostly",
        "surprise": "a warm cloak for a cold evening",
    },
    "cloak": {
        "label": "cloak",
        "phrase": "an old wool cloak",
        "kind": "cloak",
        "sound": "rustled",
        "look": "dark and fluttery",
        "surprise": "a blanket-like cloak kept for visitors",
    },
}

HERO_NAMES = ["Mina", "Ilya", "Noor", "Sami", "Rina", "Tariq", "Lina", "Omar"]
ELDER_TYPES = ["grandmother", "grandfather"]
HERO_TYPES = ["girl", "boy"]

SEASONS = {
    "autumn": "autumn",
    "winter": "winter",
    "rainy": "rainy",
}

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _is_spooky(setting: Setting) -> str:
    return "The old rooms held a hush, and every board seemed to remember footsteps."


def _intro(world: World, hero: Entity, elder: Entity, garment: Entity) -> None:
    world.say(
        f"{hero.id} visited {world.setting.place}, where {hero.pronoun('possessive')} "
        f"{elder.type} kept old things safe."
    )
    world.say(
        f"Near a cracked chair, {hero.id} noticed {garment.phrase} hanging on a peg."
    )


def _misunderstanding(world: World, hero: Entity, garment: Entity) -> None:
    hero.memes["startled"] = hero.memes.get("startled", 0.0) + 1.0
    world.say(_is_spooky(world.setting))
    world.say(
        f"Because the hood was pale and still, {hero.id} thought the {garment.label} "
        f"looked like a ghost."
    )
    world.say(
        f'{hero.id} whispered, "Is it watching me?" and took one careful step back.'
    )


def _surprise(world: World, elder: Entity, garment: Entity) -> None:
    garment.meters["lifted"] = garment.meters.get("lifted", 0.0) + 1.0
    world.say(
        f"Then a cool breeze slipped through the hall and made the cloth lift and sway."
    )
    world.say(
        f"{elder.type.capitalize()} laughed softly and opened the window wider."
    )


def _explain(world: World, elder: Entity, hero: Entity, garment: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    world.say(
        f'"It is only {garment.phrase}," {elder.pronoun("subject")} said. '
        f'"This old {garment.label} belongs to the house, and it keeps guests warm."'
    )
    world.say(
        f"{hero.id} blinked, then smiled when the surprise made sense."
    )


def _resolution(world: World, hero: Entity, elder: Entity, garment: Entity) -> None:
    garment.worn_by = hero.id
    hero.memes["brave"] = hero.memes.get("brave", 0.0) + 1.0
    world.say(
        f"{elder.id} helped {hero.id} put on the {garment.label}."
    )
    world.say(
        f"At once, {hero.id} felt cozy instead of afraid."
    )
    world.say(
        f"With the hood around {hero.pronoun('possessive')} face, {hero.id} walked "
        f"through the old house like a tiny, brave ghost of {garment.label} and light."
    )


def tell_story(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.garment not in GARMENTS:
        raise StoryError("Unknown garment.")
    if params.hero_type not in HERO_TYPES:
        raise StoryError("Unknown hero type.")
    if params.elder_type not in ELDER_TYPES:
        raise StoryError("Unknown elder type.")
    if params.season not in SEASONS:
        raise StoryError("Unknown season.")

    setting = SETTINGS[params.place]
    garment_cfg = GARMENTS[params.garment]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"courage": 0.0},
        memes={"curiosity": 1.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=params.elder_type,
        label=f"the {params.elder_type}",
        meters={"care": 1.0},
    ))
    garment = world.add(Entity(
        id="Garment",
        kind="thing",
        type=garment_cfg["kind"],
        label=garment_cfg["label"],
        phrase=garment_cfg["phrase"],
        caretaker=elder.id,
        meters={"still": 1.0},
        props={"sound": garment_cfg["sound"], "look": garment_cfg["look"], "surprise": garment_cfg["surprise"]},
    ))

    world.facts.update(
        hero=hero,
        elder=elder,
        garment=garment,
        season=params.season,
        place=params.place,
        garment_key=params.garment,
    )

    world.say(f"It was {SEASONS[params.season]} at {world.setting.place}.")
    world.say(f"{_is_spooky(world.setting)}")
    _intro(world, hero, elder, garment)
    world.say("")
    _misunderstanding(world, hero, garment)
    _surprise(world, elder, garment)
    _explain(world, elder, hero, garment)
    world.say("")
    _resolution(world, hero, elder, garment)
    return world


# ---------------------------------------------------------------------------
# QA helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    elder: Entity = f["elder"]  # type: ignore[assignment]
    garment: Entity = f["garment"]  # type: ignore[assignment]
    return [
        f'Write a short ghost-story-style tale about {hero.id} finding a {garment.label} in {world.setting.place}.',
        f"Tell a gentle story where {hero.id} mistakes an old {garment.label} for a ghost, then learns the truth from {elder.type}.",
        f"Write a child-friendly spooky story featuring a historic house, a burnous, and a surprise reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    elder: Entity = f["elder"]  # type: ignore[assignment]
    garment: Entity = f["garment"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} first think the {garment.label} was?",
            answer=f"{hero.id} first thought the pale hooded {garment.label} was a ghost.",
        ),
        QAItem(
            question=f"What made the {garment.label} move and cause the surprise?",
            answer="A cool breeze slipped through the old house and made the cloth lift and sway.",
        ),
        QAItem(
            question=f"Who explained the truth about the {garment.label}?",
            answer=f"The {elder.type} explained that it was only a warm old cloak kept safe in the house.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt brave and cozy after wearing the {garment.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    garment: Entity = f["garment"]  # type: ignore[assignment]
    elder: Entity = f["elder"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question="What is a historic house?",
            answer="A historic house is an old building that people keep because it has stories from long ago.",
        ),
        QAItem(
            question="What is a burnous?",
            answer="A burnous is a loose cloak with a hood, often worn to keep warm.",
        ),
        QAItem(
            question="Why can a surprise in a story feel exciting?",
            answer="A surprise feels exciting because something unexpected happens and changes what the characters thought was true.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they do not know the real meaning yet.",
        ),
    ]
    if garment.label == "burnous":
        qa.append(QAItem(
            question="Why might a burnous look ghostly in a dark room?",
            answer="A burnous can look ghostly because its pale cloth and hood may seem like a person or a floating shape in the dim light.",
        ))
    if elder.type == "grandmother":
        qa.append(QAItem(
            question="What does a grandmother often do in a story like this?",
            answer="A grandmother often explains things gently, keeps old things safe, and helps a child feel calm.",
        ))
    return qa


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A garment can feel spooky if it is pale, hooded, and hanging still in an old place.
spooky_thing(G) :- garment(G), pale(G), hooded(G), hangs_still(G).

% A misunderstanding happens when the hero sees a spooky thing and has not yet
% learned what it really is.
misunderstanding(H, G) :- hero(H), spooky_thing(G), sees(H, G), not knows_truth(H, G).

% A surprise is the sudden motion that changes the hero's guess.
surprise(G) :- spooky_thing(G), breeze(G), lifts(G).

% The story is valid when it includes a historic setting, a burnous-like garment,
% a misunderstanding, and a surprise reveal.
valid_story(S, H, G) :- historic(S), hero(H), garment(G), place(S), misunderstanding(H, G), surprise(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if setting.old:
            lines.append(asp.fact("historic", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for gid, g in GARMENTS.items():
        lines.append(asp.fact("garment", gid))
        if "burnous" in gid or g["label"] == "burnous":
            lines.append(asp.fact("burnous", gid))
        if "cloak" in g["kind"]:
            lines.append(asp.fact("cloak", gid))
        if g["label"] == "burnous":
            lines.append(asp.fact("pale", gid))
            lines.append(asp.fact("hooded", gid))
        lines.append(asp.fact("hangs_still", gid))
        lines.append(asp.fact("breeze", gid))
        lines.append(asp.fact("lifts", gid))
    # One generic hero to satisfy the declarative twin.
    lines.append(asp.fact("hero", "child"))
    lines.append(asp.fact("sees", "child", "burnous"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set()
    for sid, setting in SETTINGS.items():
        if not setting.old:
            continue
        for gid, g in GARMENTS.items():
            if g["label"] == "burnous":
                python_set.add((sid, "child", gid))
    asp_set = set(_asp_valid())
    if python_set == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_params(place: str, garment: str) -> bool:
    return place in SETTINGS and garment in GARMENTS and SETTINGS[place].old and garment == "burnous"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a historic burnous misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--garment", choices=GARMENTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDER_TYPES)
    ap.add_argument("--season", choices=SEASONS.keys())
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    garment = args.garment or "burnous"
    if not valid_params(place, garment):
        raise StoryError("This story world needs a historic place and a burnous.")
    gender = args.gender or rng.choice(HERO_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice(ELDER_TYPES)
    season = args.season or rng.choice(list(SEASONS.keys()))
    return StoryParams(
        place=place,
        garment=garment,
        hero_name=hero_name,
        hero_type=gender,
        elder_type=elder,
        season=season,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(json.dumps(
            {
                eid: {
                    "type": e.type,
                    "kind": e.kind,
                    "worn_by": e.worn_by,
                    "meters": e.meters,
                    "memes": e.memes,
                    "props": e.props,
                }
                for eid, e in sample.world.entities.items()
            },
            indent=2,
            ensure_ascii=False,
        ))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="old_house", garment="burnous", hero_name="Mina", hero_type="girl", elder_type="grandmother", season="autumn"),
    StoryParams(place="museum_room", garment="burnous", hero_name="Omar", hero_type="boy", elder_type="grandfather", season="winter"),
    StoryParams(place="stone_attic", garment="burnous", hero_name="Lina", hero_type="girl", elder_type="grandmother", season="rainy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
