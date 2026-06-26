#!/usr/bin/env python3
"""
storyworlds/worlds/slot_feel_misunderstanding_humor_space_adventure.py
======================================================================

A small space-adventure storyworld about a crew member, a confusing "slot",
and a funny misunderstanding that gets cleared up by the end.

Premise:
- A young space traveler wants to place a special item into a slot on a ship or station.
- Another character misunderstands what the slot is for, causing a gentle conflict.
- The misunderstanding is resolved with a simple explanation and a humorous reveal.

This world keeps a child-facing, concrete style with a short beginning, middle
turn, and ending image. The physical world tracks meters; emotions track memes.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Core entities and world model
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"open": 0.0, "jammed": 0.0, "placed": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "confusion": 0.0, "amusement": 0.0,
                          "worry": 0.0, "relief": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Station:
    place: str = "the star station"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Slot:
    id: str
    label: str
    purpose: str
    location: str
    fits: set[str] = field(default_factory=set)
    signal: str = ""
    humor: str = ""


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    size: str = "small"
    color: str = "silver"
    slot: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    station: Station
    entities: dict[str, Entity] = field(default_factory=dict)
    slots: dict[str, Slot] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.station)
        clone.entities = copy.deepcopy(self.entities)
        clone.slots = copy.deepcopy(self.slots)
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
STATIONS = {
    "hub": Station(place="the star station hub", indoors=True, affords={"dock", "panel"}),
    "ship": Station(place="the little cargo ship", indoors=True, affords={"dock", "panel"}),
    "moonbase": Station(place="the moonbase hallway", indoors=True, affords={"dock", "panel"}),
}

SLOTS = {
    "seat_slot": Slot(
        id="seat_slot",
        label="seat slot",
        purpose="hold a tiny badge",
        location="a wall panel by the window",
        fits={"badge"},
        signal="beeps twice",
        humor="looks like a mouth waiting for a snack",
    ),
    "tool_slot": Slot(
        id="tool_slot",
        label="tool slot",
        purpose="store a screwdriver",
        location="the cargo bay desk",
        fits={"tool"},
        signal="clicks with a neat snap",
        humor="looks like a pocket on a robot apron",
    ),
    "snack_slot": Slot(
        id="snack_slot",
        label="snack slot",
        purpose="hold a sealed snack tube",
        location="the tiny galley",
        fits={"snack"},
        signal="pings cheerfully",
        humor="looks like a toothy grin in the counter",
    ),
}

ITEMS = {
    "badge": Item(
        id="badge",
        label="badge",
        phrase="a shiny badge with a blue star",
        type="badge",
        size="tiny",
        color="blue",
        slot="seat_slot",
        tags={"badge", "metal", "signal"},
    ),
    "tool": Item(
        id="tool",
        label="screwdriver",
        phrase="a little screwdriver with a red handle",
        type="tool",
        size="small",
        color="red",
        slot="tool_slot",
        tags={"tool", "metal", "repair"},
    ),
    "snack": Item(
        id="snack",
        label="snack tube",
        phrase="a sealed snack tube of berry paste",
        type="snack",
        size="small",
        color="purple",
        slot="snack_slot",
        tags={"snack", "food", "silly"},
    ),
}

HERO_NAMES = ["Nova", "Pip", "Juno", "Miko", "Tali", "Rin"]
CREW_NAMES = ["Captain", "Aunt Bea", "Pilot Sol", "Engineer Jax"]
TRAITS = ["curious", "brave", "bouncy", "careful", "cheerful", "silly"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    slot: str
    item: str
    name: str
    companion: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def slot_wants_item(slot: Slot, item: Item) -> bool:
    return item.type in slot.fits


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, slot in SLOTS.items():
        for iid, item in ITEMS.items():
            if slot_wants_item(slot, item):
                combos.append((sid, iid))
    return combos


def explain_rejection(slot: Slot, item: Item) -> str:
    return (
        f"(No story: the {slot.label} is made for a {slot.purpose}, "
        f"but a {item.label} is not the right thing for that slot. "
        f"Try a matching item that really fits.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'curious')} space traveler "
        f"who loved exploring {world.station.place}."
    )


def love_space(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved the humming lights, the soft boots-on-metal sound, "
        f"and the feeling that every hallway might lead to a surprise."
    )


def show_item(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"One day {hero.id} held {hero.pronoun('possessive')} {item.label} and grinned. "
        f"{hero.pronoun().capitalize()} wanted to place {item.it()} into the {world.facts['slot'].label}."
    )


def misunderstanding(world: World, companion: Entity, hero: Entity) -> None:
    companion.memes["confusion"] += 1
    companion.memes["worry"] += 1
    world.say(
        f"{companion.id} looked at the slot and blinked. "
        f'"Wait," {companion.pronoun()} said, "is that a snack slot? '
        f'It looks like it wants a bite!"'
    )
    hero.memes["confusion"] += 1
    world.say(
        f"{hero.id} felt puzzled for a moment, because the slot was funny-looking and did almost look hungry."
    )


def explain(world: World, hero: Entity, companion: Entity, slot: Slot, item: Item) -> None:
    companion.memes["amusement"] += 1
    companion.memes["relief"] += 1
    world.say(
        f"{hero.id} pointed to the label and said, "
        f'"Nope. This {slot.label} is for {slot.purpose}." '
        f'{companion.id} laughed when {slot.signal}, '
        f"because the slot really did seem to make a cheerful face."
    )
    world.say(
        f"Then {hero.id} set {hero.pronoun('possessive')} {item.label} in the slot, and it fit with a neat little click."
    )
    item_ent = world.get(item.id)
    item_ent.meters["placed"] += 1
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1


def ending_image(world: World, hero: Entity, companion: Entity, slot: Slot, item: Item) -> None:
    world.say(
        f"After that, {hero.id} and {companion.id} laughed at the slot's silly grin-like shape. "
        f"The {slot.label} {slot.signal}, the {item.label} stayed in place, and the crew moved on feeling lighter."
    )


def build_world(params: StoryParams) -> World:
    world = World(STATIONS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Pip", "Miko", "Rin"} else "girl"))
    hero.memes["trait"] = 0.0
    hero.memes["trait_name"] = 0.0
    companion = world.add(Entity(id=params.companion, kind="character", type="adult"))
    slot = copy.deepcopy(SLOTS[params.slot])
    item = copy.deepcopy(ITEMS[params.item])
    world.slots[slot.id] = slot
    world.items[item.id] = item
    world.facts.update(hero=hero, companion=companion, slot=slot, item=item, params=params)

    item_ent = world.add(Entity(
        id=item.id, kind="thing", type=item.type, label=item.label, phrase=item.phrase
    ))
    hero.memes["curiosity"] += 0.0

    # Act 1
    world.say(f"{hero.id} was visiting {world.station.place}.")
    world.say(
        f"{hero.id} loved how the ship felt calm and bright, like a tiny town floating in space."
    )
    show_item(world, hero, item_ent)

    # Act 2
    world.para()
    world.say(
        f"At a panel near {slot.location}, the {slot.label} waited. It {slot.humor}."
    )
    misunderstanding(world, companion, hero)

    # Act 3
    world.para()
    explain(world, hero, companion, slot, item_ent)
    ending_image(world, hero, companion, slot, item)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a child about a "{f["slot"].label}" and a funny misunderstanding.',
        f"Tell a gentle story where {f['hero'].id} wants to use a {f['item'].label} and {f['companion'].id} thinks the slot means something else.",
        f'Write a playful story that includes the words "slot" and "feel" and ends with a clear explanation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    slot: Slot = f["slot"]
    item: Item = f["item"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label}?",
            answer=f"{hero.id} wanted to place the {item.label} into the {slot.label}."
        ),
        QAItem(
            question=f"Why did {companion.id} get confused about the slot?",
            answer=(
                f"{companion.id} thought the {slot.label} might be for something funny, like a snack, "
                f"because it looked a little like a hungry face."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} fix the misunderstanding?",
            answer=(
                f"{hero.id} explained what the {slot.label} was really for, then put the {item.label} in it so it clicked in place."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "slot": [
        QAItem(
            question="What is a slot?",
            answer="A slot is an opening made to hold a certain thing, like a card, a key, or a tool."
        )
    ],
    "feel": [
        QAItem(
            question="What does it mean to feel curious?",
            answer="To feel curious means to want to know more and ask questions about something new."
        )
    ],
    "space": [
        QAItem(
            question="Why do ships and stations make humming sounds?",
            answer="Machines, lights, and air systems can make a steady hum when they are running in space."
        )
    ],
    "humor": [
        QAItem(
            question="What makes a misunderstanding funny?",
            answer="A misunderstanding can be funny when someone guesses the wrong thing and then the real answer is surprising but harmless."
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        qa for key, items in WORLD_KNOWLEDGE.items()
        if key in {"slot", "feel", "space", "humor"}
        for qa in items
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
slot_fit(S, I) :- slot(S), item(I), fits(S, T), item_type(I, T).
valid_story(Setting, S, I) :- setting(Setting), slot(S), item(I), slot_fit(S, I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, slot in SLOTS.items():
        lines.append(asp.fact("slot", sid))
        lines.append(asp.fact("slot_label", sid, slot.label))
        lines.append(asp.fact("purpose", sid, slot.purpose))
        for t in sorted(slot.fits):
            lines.append(asp.fact("fits", sid, t))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_type", iid, item.type))
    for sid in STATIONS:
        lines.append(asp.fact("setting", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show slot_fit/2.\n#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(STATIONS[s].place if False else setting, sid, iid) for sid, iid in valid_combos() for setting in STATIONS}
    clingo_set = set(asp_valid_combos())
    if clingo_set:
        # We only need parity on the slot/item compatibility; setting is generic here.
        clingo_pairs = {(sid, iid) for (_, sid, iid) in clingo_set}
    else:
        clingo_pairs = set()
    py_pairs = set(valid_combos())
    if clingo_pairs == py_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(py_pairs)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_pairs - py_pairs:
        print("  only in clingo:", sorted(clingo_pairs - py_pairs))
    if py_pairs - clingo_pairs:
        print("  only in python:", sorted(py_pairs - clingo_pairs))
    return 1


# ---------------------------------------------------------------------------
# Q&A / emit / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="hub", slot="seat_slot", item="badge", name="Nova", companion="Captain", trait="curious"),
    StoryParams(setting="ship", slot="tool_slot", item="tool", name="Pip", companion="Engineer Jax", trait="silly"),
    StoryParams(setting="moonbase", slot="snack_slot", item="snack", name="Juno", companion="Pilot Sol", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a slot misunderstanding.")
    ap.add_argument("--setting", choices=STATIONS)
    ap.add_argument("--slot", choices=SLOTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--companion", choices=CREW_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.slot and args.item and (args.slot, args.item) not in combos:
        raise StoryError(explain_rejection(SLOTS[args.slot], ITEMS[args.item]))
    if args.slot:
        combos = [c for c in combos if c[0] == args.slot]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if not combos:
        raise StoryError("(No valid slot/item combination matches the given options.)")
    slot, item = rng.choice(sorted(combos))
    return StoryParams(
        setting=args.setting or rng.choice(list(STATIONS)),
        slot=slot,
        item=item,
        name=args.name or rng.choice(HERO_NAMES),
        companion=args.companion or rng.choice(CREW_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible slot/item pairs:\n")
        for sid, iid in combos:
            print(f"  {sid:10} {iid:10}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.slot} + {p.item} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
