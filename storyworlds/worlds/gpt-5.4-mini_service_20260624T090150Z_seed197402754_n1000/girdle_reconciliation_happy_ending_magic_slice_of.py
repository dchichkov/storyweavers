#!/usr/bin/env python3
"""
girdle_reconciliation_happy_ending_magic_slice_of.py
====================================================

A small slice-of-life storyworld about a child, a cherished girdle, a small
misunderstanding, a little magic, and a reconciliation that ends happily.

Seed tale:
---
Mina liked to help her grandmother in the morning. Her grandmother wore a soft
embroidered girdle when she baked bread because it held her dress neatly in
place. One day Mina found the girdle hanging on a chair and tried to use it as a
magic ribbon for pretend play. The ribbon slipped, a button jar tipped, and
Grandmother looked sad.

Mina felt bad. She said sorry, fixed the jar, and helped fold the laundry.
Grandmother smiled, made the girdle sparkle with a tiny charm for the doll tea
party, and Mina and Grandmother shared sweet bread together.

World model:
---
- characters and objects have physical meters and emotional memes
- magic can briefly transform a mundane object, but only in a gentle, domestic
  way
- tension is caused by an object being borrowed without asking
- reconciliation requires apology, repair, and a mutual small gift of trust
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    borrowed_from: Optional[str] = None
    worn_by: Optional[str] = None
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"order": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "guilt": 0.0, "warmth": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    cozy: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    special: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    effect: str
    sparkle: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.magic_on: bool = False
        self.trace_events: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.magic_on = self.magic_on
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    elder_name: str
    elder_type: str
    item: str
    magic: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting("the kitchen"),
    "laundry_room": Setting("the laundry room"),
    "garden_table": Setting("the garden table"),
    "sunroom": Setting("the sunroom"),
}

ITEMS = {
    "girdle": Item(
        id="girdle",
        label="girdle",
        phrase="a soft embroidered girdle",
        kind="cloth",
        special="held the dress neatly in place",
        tags={"home", "cloth", "family"},
    ),
    "ribbon": Item(
        id="ribbon",
        label="ribbon",
        phrase="a bright ribbon",
        kind="cloth",
        special="looked nice tied in a bow",
        tags={"play", "cloth"},
    ),
    "apron_tie": Item(
        id="apron_tie",
        label="apron tie",
        phrase="a long apron tie",
        kind="cloth",
        special="kept the apron snug",
        tags={"home", "cloth"},
    ),
}

MAGICS = {
    "sparkle": Magic("sparkle", "a tiny sparkle charm", "made the item glow softly", "sparkled"),
    "flower": Magic("flower", "a flower charm", "made the cloth smell like spring", "bloomed"),
    "glimmer": Magic("glimmer", "a glimmer charm", "made a small trail of light", "glimmered"),
}

CHILD_NAMES = ["Mina", "Tia", "Nora", "Lena", "Ari", "Ivy"]
ELDER_NAMES = ["Grandma Rose", "Grandma June", "Nana Belle", "Grandma Pearl"]
CHILD_TYPES = ["girl", "boy"]
ELDER_TYPES = ["grandmother", "grandfather"]
TRAITS = ["kind", "curious", "helpful", "gentle", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, i, m) for p in SETTINGS for i in ITEMS for m in MAGICS if i == "girdle"]


def reasonableness_gate(place: str, item: str, magic: str) -> bool:
    return item == "girdle" and place in SETTINGS and magic in MAGICS


def explain_rejection(place: str, item: str, magic: str) -> str:
    return (
        f"(No story: this world is built around a family girdle being borrowed, "
        f"mended, and gently charmed. The combination {place!r}, {item!r}, {magic!r} "
        f"doesn't fit that slice-of-life premise.)"
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"order": 0.0, "clean": 0.0},
        memes={"joy": 1.0, "worry": 0.0, "guilt": 0.0, "warmth": 0.0},
    ))
    elder = world.add(Entity(
        id=params.elder_name,
        kind="character",
        type=params.elder_type,
        meters={"order": 0.0, "clean": 0.0},
        memes={"joy": 1.0, "worry": 0.0, "guilt": 0.0, "warmth": 0.0},
    ))
    item = ITEMS[params.item]
    girdle = world.add(Entity(
        id=item.id,
        type=item.kind,
        label=item.label,
        phrase=item.phrase,
        owner=elder.id,
        caretaker=elder.id,
        worn_by=elder.id,
        meters={"order": 1.0, "clean": 1.0},
        memes={"joy": 0.0, "worry": 0.0, "guilt": 0.0, "warmth": 0.0},
    ))
    magic = MAGICS[params.magic]
    charm = world.add(Entity(
        id=magic.id,
        type="charm",
        label=magic.label,
        phrase=magic.effect,
        magical=True,
        meters={"order": 0.0, "clean": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "guilt": 0.0, "warmth": 0.0},
    ))

    # Act 1
    world.say(
        f"{child.id} liked helping {elder.id} in {world.setting.place}, especially on quiet mornings."
    )
    world.say(
        f"{elder.id} wore {elder.pronoun('possessive')} {girdle.label} because it {item.special}."
    )
    world.say(
        f"{child.id} thought the little charm on the table looked like a toy for pretend play."
    )

    # Act 2
    world.para()
    child.memes["worry"] += 0.5
    world.say(
        f"While {elder.id} turned to the bread dough, {child.id} lifted the {girdle.label} and tried to make it magical."
    )
    child.memes["joy"] += 0.5
    world.magic_on = True
    world.trace_events.append("magic_started")
    if params.magic == "sparkle":
        world.say(f"A tiny light danced over the cloth, and the {girdle.label} softly sparkled.")
    elif params.magic == "flower":
        world.say(f"One sweet puff of magic drifted up, and the {girdle.label} smelled like spring flowers.")
    else:
        world.say(f"A thin trail of light curled around the cloth, and the {girdle.label} glimmered like morning dew.")
    # accident
    child.memes["guilt"] += 1.0
    elder.memes["worry"] += 1.0
    world.say(
        f"But the charm snagged on a bowl, the flour jar tipped, and a little white cloud puffed across the table."
    )
    world.say(f"{elder.id} looked sad, because the room had become messy and the girdle was out of place.")

    # Act 3 reconciliation
    world.para()
    child.memes["warmth"] += 1.0
    world.say(
        f"{child.id} felt the pinch in {child.pronoun('possessive')} chest, took a breath, and said sorry right away."
    )
    child.memes["guilt"] = 0.0
    elder.memes["worry"] = 0.0
    world.say(f"{child.id} wiped the table, picked up the jar, and helped fold the cloth napkins.")
    girdle.worn_by = elder.id
    girdle.meters["clean"] += 0.5
    world.say(
        f"{elder.id} smiled again and set the {girdle.label} back where it belonged."
    )
    world.say(
        f"Then {elder.id} used the tiny charm to give the {girdle.label} a soft, safe shine for their doll tea party."
    )
    elder.memes["joy"] += 1.0
    child.memes["joy"] += 1.0
    world.say(
        f"By the end, {child.id} and {elder.id} shared sweet bread at the garden table, and the room felt warm and neat again."
    )

    world.facts = {
        "child": child,
        "elder": elder,
        "item": girdle,
        "magic": magic,
        "place": params.place,
        "resolved": True,
        "mishap": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    item = f["item"]
    magic = f["magic"]
    return [
        f'Write a gentle slice-of-life story about {child.id} borrowing a {item.label} and making a small mess.',
        f"Tell a happy story where {child.id} says sorry to {elder.id} after trying a little magic with {item.label}.",
        f"Write a short child-friendly story with the word '{item.label}' and a warm magical reconciliation.",
        f"Create a cozy story ending where {child.id} and {elder.id} feel close again after a mishap involving {magic.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    item = f["item"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} try to use while {elder.id} was baking?",
            answer=f"{child.id} tried to use the {item.label} as a little magic ribbon while {elder.id} was busy baking in {place}.",
        ),
        QAItem(
            question=f"Why did {elder.id} feel sad after the magic try?",
            answer=f"{elder.id} felt sad because the cloth got out of place and the table became messy, so the peaceful morning was interrupted.",
        ),
        QAItem(
            question=f"How did {child.id} help make things better?",
            answer=f"{child.id} said sorry, wiped the table, picked up the jar, and helped fold the napkins so the room could be calm again.",
        ),
        QAItem(
            question=f"What was special about the ending?",
            answer=f"The ending was special because {child.id} and {elder.id} reconciled, the {item.label} got a gentle magical shine, and they shared sweet bread happily together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a girdle?",
            answer="A girdle is a narrow band of cloth or material that can help hold a dress or skirt neatly in place.",
        ),
        QAItem(
            question="What does it mean to apologize?",
            answer="To apologize means to say sorry when you know you hurt, upset, or bothered someone.",
        ),
        QAItem(
            question="What is a charm in a magic story?",
            answer="A charm is a small magical object or spell that can make something glow, sparkle, or feel special.",
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
        if e.magical:
            bits.append("magical=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  magic_on={world.magic_on}")
    lines.append(f"  fired rules={sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A girdle story is valid when the child borrows the girdle, a small mishap
% happens, and the ending restores harmony with a gentle magical action.

borrows(child, item) :- character(child), item(item), item_kind(item, cloth).
mishap(child, item) :- borrows(child, item), magic_used(m), m != none.
reconciles(child, elder) :- sorry(child, elder), repair(child), shared_food(child, elder).

happy_ending(child, elder, item) :- borrows(child, item), mishap(child, item), reconciles(child, elder).

valid_story(place, child, elder, item, magic) :-
    setting(place), character(child), character(elder), item(item), magic(magic),
    item_name(item, girdle), gentle(magic), cozy(place).

#show valid_story/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
        lines.append(asp.fact("cozy", place))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_name", iid, it.label))
        lines.append(asp.fact("item_kind", iid, it.kind))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("gentle", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, "child", "elder", "girdle", m) for p in SETTINGS for m in MAGICS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life girdle reconciliation storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--magic", choices=MAGICS)
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
    place = args.place or rng.choice(list(SETTINGS))
    item = args.item or "girdle"
    magic = args.magic or rng.choice(list(MAGICS))
    if not reasonableness_gate(place, item, magic):
        raise StoryError(explain_rejection(place, item, magic))
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    return StoryParams(place=place, child_name=child_name, child_type=child_type,
                       elder_name=elder_name, elder_type=elder_type, item=item, magic=magic)


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


CURATED = [
    StoryParams("kitchen", "Mina", "girl", "Grandma Rose", "grandmother", "girdle", "sparkle"),
    StoryParams("sunroom", "Tia", "girl", "Nana Belle", "grandmother", "girdle", "flower"),
    StoryParams("garden_table", "Ari", "boy", "Grandma June", "grandmother", "girdle", "glimmer"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(f"{len(asp_valid_stories())} compatible stories found by clingo.")
        for row in asp_valid_stories():
            print(" ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
