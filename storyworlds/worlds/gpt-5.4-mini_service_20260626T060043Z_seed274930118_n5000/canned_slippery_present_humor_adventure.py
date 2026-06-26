#!/usr/bin/env python3
"""
storyworlds/worlds/canned_slippery_present_humor_adventure.py
=============================================================

A small adventure world about a canned present, a slippery floor, and a
humorous delivery gone right.

Premise:
- A child wants to bring a present to someone special.
- A stack of canned food tips, making the path slippery.
- The child must choose a careful, funny way forward.

The world is intentionally tiny and state-driven:
physical meters track wetness, slipperiness, balance, and damage;
emotional memes track excitement, worry, laughter, and relief.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wet", "slippery", "damaged", "heavy", "balanced"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "laugh", "pride", "relief", "care"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    slippery: bool = False
    can_hold_present: bool = True


@dataclass
class PresentSpec:
    label: str
    phrase: str
    region: str = "hands"


@dataclass
class GearSpec:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    room: str
    present: str
    hero_name: str
    hero_type: str
    caretaker_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


ROOMS = {
    "kitchen": Room("the kitchen", slippery=False, can_hold_present=True),
    "hall": Room("the hall", slippery=True, can_hold_present=True),
    "porch": Room("the porch", slippery=True, can_hold_present=True),
    "market": Room("the market", slippery=False, can_hold_present=False),
}

PRESENTS = {
    "canned_fish": PresentSpec("canned fish", "a shiny present wrapped around a can of fish"),
    "canned_cookies": PresentSpec("canned cookies", "a funny present wrapped around a can of cookies"),
    "canned_soup": PresentSpec("canned soup", "a cheerful present wrapped around a can of soup"),
}

GEAR = [
    GearSpec(
        id="grip_shoes",
        label="grip shoes",
        covers={"feet"},
        guards={"slippery"},
        prep="put on the grip shoes first",
        tail="tied the grip shoes tight",
        plural=True,
    ),
    GearSpec(
        id="tray",
        label="a sturdy tray",
        covers={"hands"},
        guards={"heavy"},
        prep="hold the present on a sturdy tray",
        tail="balanced the tray with both hands",
    ),
    GearSpec(
        id="towel",
        label="a dry towel",
        covers={"hands"},
        guards={"wet"},
        prep="wrap the box in a dry towel",
        tail="kept the box snug in the towel",
    ),
]

HERO_NAMES = ["Milo", "Pia", "Nia", "Toby", "Lena", "Owen", "Zuri", "Bea"]
GROWNUPS = ["mother", "father", "aunt", "uncle"]
TRAITS = ["brave", "curious", "silly", "cheery", "bright"]


def _supporting_gear(room: Room) -> Optional[GearSpec]:
    if room.slippery:
        return GEAR[0]
    return GEAR[1]


def _predict(world: World, actor: Entity, present: Entity) -> dict:
    sim = world.copy()
    hero = sim.get(actor.id)
    pres = sim.get(present.id)
    hero.meters["balanced"] += 1
    if sim.room.slippery and not any(g.label == "grip shoes" for g in sim.worn_items(hero)):
        hero.meters["balanced"] -= 1
    if sim.room.slippery:
        hero.meters["slippery"] += 1
    return {
        "drop": hero.meters["balanced"] < THRESHOLD,
        "damage": pres.meters["damaged"] >= THRESHOLD,
    }


def maybe_spill(world: World, hero: Entity) -> None:
    if not world.room.slippery:
        return
    sig = "spill"
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["slippery"] += 1
    world.say("The floor was so slippery that even the shadows seemed to tiptoe.")


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next((t for t in hero.memes if False), 'adventurer') if False else 'adventurer'} with a grin for trouble.")
    world.say(f"{hero.id} loved little errands that felt like quests, especially when they had a funny surprise.")


def set_premise(world: World, hero: Entity, present: Entity, caretaker: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"One day, {hero.id} found {present.phrase} and wanted to carry {present.it()} "
        f"to {caretaker.pronoun('object')} as a present."
    )
    world.say(f"{hero.id} smiled because a present felt like a tiny adventure with ribbon on top.")


def enter_room(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} hurried into {world.room.name}, where the path looked simple at first.")


def warn_and_laugh(world: World, caretaker: Entity, hero: Entity, present: Entity) -> None:
    pred = _predict(world, hero, present)
    caretaker.memes["worry"] += 1
    world.facts["predicted_drop"] = pred["drop"]
    if pred["drop"]:
        world.say(
            f'"Careful," {caretaker.pronoun("subject").capitalize()} said with a smile, '
            f'"the floor is slippery, and I do not want your present to do a silly slide."'
        )
    else:
        world.say(f'"Careful," {caretaker.pronoun("subject").capitalize()} said, watching the present with a fond eye.')


def slip_attempt(world: World, hero: Entity, present: Entity) -> None:
    hero.memes["worry"] += 1
    maybe_spill(world, hero)
    hero.meters["balanced"] += 0.5
    world.say(
        f"{hero.id} tried to dash ahead, but their feet skated in a very funny little wiggle."
    )
    world.say(f"{hero.id} laughed even while trying not to wobble, because the wobble was impossible to ignore.")


def clever_fix(world: World, caretaker: Entity, hero: Entity, present: Entity) -> Optional[GearSpec]:
    gear = _supporting_gear(world.room)
    if gear is None:
        return None
    if gear.id == "grip_shoes":
        world.say(
            f"{caretaker.id} pointed to the door and said, "
            f'"How about you {gear.prep}?"'
        )
    else:
        world.say(
            f"{caretaker.id} lifted {gear.label} and said, "
            f'"How about you {gear.prep}?"'
        )
    if gear.id == "grip_shoes":
        shoes = Entity(id="shoes", type="gear", label="grip shoes", protective=True, covers={"feet"})
        shoes.worn_by = hero.id
        world.add(shoes)
    else:
        tray = Entity(id="tray", type="gear", label="a sturdy tray", protective=True, covers={"hands"})
        tray.worn_by = hero.id
        world.add(tray)
    return gear


def resolve(world: World, hero: Entity, caretaker: Entity, present: Entity, gear: GearSpec) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id}'s eyes lit up. They followed the plan, {gear.tail}, and the wobble turned into a careful march."
    )
    present.meters["damaged"] = 0.0
    world.say(
        f"In the end, {hero.id} reached {caretaker.id} with {present.label} safe and sound, "
        f"and the whole trip felt like a joke that ended in a hug."
    )
    world.say(
        f"{caretaker.id} laughed, {hero.id} beamed, and the slippery floor had only helped make the story memorable."
    )


def tell(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=params.caretaker_type))
    present = world.add(Entity(
        id="present",
        type="thing",
        label=PRESENTS[params.present].label,
        phrase=PRESENTS[params.present].phrase,
        owner=hero.id,
        caretaker=caretaker.id,
    ))
    world.facts.update(hero=hero, caretaker=caretaker, present=present, params=params)

    introduce(world, hero)
    set_premise(world, hero, present, caretaker)
    world.para()
    enter_room(world, hero)
    warn_and_laugh(world, caretaker, hero, present)
    slip_attempt(world, hero, present)
    world.para()
    gear = clever_fix(world, caretaker, hero, present)
    if gear:
        resolve(world, hero, caretaker, present, gear)
    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    present = f["present"]
    room = world.room.name
    return [
        f'Write a short humorous adventure about {hero.id} carrying {present.label} across {room}.',
        f"Tell a child-friendly story where a slippery floor causes a funny problem, but a present still gets delivered.",
        f'Write a tiny adventure story with the words "canned", "slippery", and "present".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    present = f["present"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to carry?",
            answer=f"{hero.id} was carrying {present.label} as a present for {caretaker.id}.",
        ),
        QAItem(
            question=f"Why did the trip get tricky in {world.room.name}?",
            answer=f"The trip got tricky because the floor was slippery, so {hero.id} had to slow down and be careful.",
        ),
        QAItem(
            question=f"How did the story stay funny?",
            answer=f"It stayed funny because {hero.id} nearly skated, laughed at the wobble, and then found a safer way to keep going.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"What helped {hero.id} finish the adventure safely?",
                answer=f"{gear.label} helped {hero.id} finish safely, so the present stayed safe on the way to {caretaker.id}.",
            )
        )
    return qa


KNOWLEDGE = {
    "canned": [
        QAItem(
            question="What is a canned food?",
            answer="Canned food is food kept in a strong metal container so it lasts a long time.",
        ),
    ],
    "slippery": [
        QAItem(
            question="Why is a slippery floor dangerous?",
            answer="A slippery floor is dangerous because feet can slide without warning and make someone lose balance.",
        ),
    ],
    "present": [
        QAItem(
            question="What is a present?",
            answer="A present is a gift you give to someone to show you care about them.",
        ),
    ],
    "humor": [
        QAItem(
            question="What makes a story humorous?",
            answer="A humorous story includes a funny surprise, a silly mistake, or a playful moment that makes people smile.",
        ),
    ],
    "adventure": [
        QAItem(
            question="What makes a story feel like an adventure?",
            answer="An adventure story feels exciting because a character sets out, meets a problem, and finds a brave way through it.",
        ),
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["canned"])
    out.extend(KNOWLEDGE["slippery"])
    out.extend(KNOWLEDGE["present"])
    out.extend(KNOWLEDGE["humor"])
    out.extend(KNOWLEDGE["adventure"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"room: {world.room.name} slippery={world.room.slippery}")
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

slippery_room(hall).
slippery_room(porch).

present_kind(canned_fish).
present_kind(canned_cookies).
present_kind(canned_soup).

gear(grip_shoes).
gear(tray).
gear(towel).

guards(grip_shoes, slippery).
guards(tray, heavy).
guards(towel, wet).

covers(grip_shoes, feet).
covers(tray, hands).
covers(towel, hands).

present_at_risk(P) :- present_kind(P).
compatible(P, G) :- present_at_risk(P), gear(G), guards(G, slippery), covers(G, feet).
compatible(P, G) :- present_kind(P), gear(G), guards(G, heavy), covers(G, hands).
valid(Room, P, G) :- (Room = hall; Room = porch), present_kind(P), compatible(P, G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
        if ROOMS[r].slippery:
            lines.append(asp.fact("slippery_room", r))
    for p in PRESENTS:
        lines.append(asp.fact("present_kind", p))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gk in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room_id, room in ROOMS.items():
        for present_id in PRESENTS:
            if room.slippery:
                combos.append((room_id, present_id, "grip_shoes"))
            else:
                combos.append((room_id, present_id, "tray"))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny humorous adventure about a canned present and a slippery floor.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--present", choices=PRESENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=GROWNUPS)
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
    room = args.room or rng.choice(list(ROOMS))
    present = args.present or rng.choice(list(PRESENTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    caretaker = args.caretaker or rng.choice(GROWNUPS)
    return StoryParams(room=room, present=present, hero_name=name, hero_type=gender, caretaker_type=caretaker)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(room="hall", present="canned_fish", hero_name="Milo", hero_type="boy", caretaker_type="mother"),
    StoryParams(room="porch", present="canned_cookies", hero_name="Pia", hero_type="girl", caretaker_type="father"),
    StoryParams(room="kitchen", present="canned_soup", hero_name="Zuri", hero_type="girl", caretaker_type="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.hero_name}: {p.present} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
