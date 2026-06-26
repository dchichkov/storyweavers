#!/usr/bin/env python3
"""
attitudinal_cautionary_bedtime_story.py
=======================================

A small, standalone story world about a child at bedtime whose attitude can
turn a gentle evening into a cautionary little lesson.

The seed premise:
- A child wants to keep doing one more thing.
- A careful parent warns that staying up too late makes the next day hard.
- A soft compromise helps the child feel safe, calm, and ready for sleep.

This world models:
- physical meters: sleepiness, darkness, coziness, noise, spill risk
- emotional memes: attitude, worry, grumpiness, trust, calm, relief

The story stays close to bedtime-story style: quiet rooms, soft objects, and
a gentle ending image that proves what changed.
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

# -----------------------------------------------------------------------------
# Core knobs and registries
# -----------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Child:
    id: str
    name: str
    type: str = "child"
    kind: str = "character"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("sleepiness", "coziness", "noise", "spill_risk"):
            self.meters.setdefault(k, 0.0)
        for k in ("attitude", "worry", "grumpiness", "trust", "calm", "relief", "joy"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Parent:
    id: str
    name: str
    type: str = "parent"
    kind: str = "character"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("care", "patience"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "calm", "trust", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Room:
    id: str
    name: str
    kind: str = "place"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("darkness", "softness", "quiet"):
            self.meters.setdefault(k, 0.0)
        for k in ("calm", "cozy"):
            self.memes.setdefault(k, 0.0)


@dataclass
class Object:
    id: str
    name: str
    type: str = "thing"
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    place: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("light", "warmth", "messiness"):
            self.meters.setdefault(k, 0.0)
        for k in ("comfort",):
            self.memes.setdefault(k, 0.0)


@dataclass
class StoryParams:
    child_name: str
    child_trait: str
    parent_label: str
    room: str
    chosen_activity: str
    caution_item: str
    seed: Optional[int] = None


@dataclass
class Activity:
    id: str
    verb: str
    noun: str
    effect_sleep: float
    effect_noise: float
    effect_attitude: float
    risk: str
    warning: str
    ending_image: str


@dataclass
class CautionItem:
    id: str
    label: str
    helps_against: set[str]
    place_phrase: str
    story_offer: str
    story_use: str


@dataclass
class World:
    room: Room
    child: Child
    parent: Parent
    objects: dict[str, Object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.id] = obj
        return obj

    def copy(self) -> "World":
        import copy as _copy

        clone = World(
            room=_copy.deepcopy(self.room),
            child=_copy.deepcopy(self.child),
            parent=_copy.deepcopy(self.parent),
            objects=_copy.deepcopy(self.objects),
            paragraphs=[[]],
            fired=set(self.fired),
            facts=_copy.deepcopy(self.facts),
        )
        return clone


ROOMS = {
    "nursery": Room(id="nursery", name="the nursery"),
    "bedroom": Room(id="bedroom", name="the bedroom"),
    "cozy_room": Room(id="cozy_room", name="the cozy room"),
}

ACTIVITIES = {
    "one_more_book": Activity(
        id="one_more_book",
        verb="read one more book",
        noun="one more book",
        effect_sleep=1.0,
        effect_noise=0.1,
        effect_attitude=0.2,
        risk="night_runs_late",
        warning="If you keep going, the moon will stay up too long and your eyes will get sore",
        ending_image="the book stayed shut on the shelf for tomorrow",
    ),
    "one_more_game": Activity(
        id="one_more_game",
        verb="play one more game",
        noun="one more game",
        effect_sleep=0.2,
        effect_noise=1.0,
        effect_attitude=0.6,
        risk="too_much_noise",
        warning="If you keep playing, your body will feel wiggly when it should be resting",
        ending_image="the toys rested quietly in their basket",
    ),
    "one_more_question": Activity(
        id="one_more_question",
        verb="ask one more question",
        noun="one more question",
        effect_sleep=0.1,
        effect_noise=0.3,
        effect_attitude=0.3,
        risk="mind_spins",
        warning="If you chase one more answer, your thoughts will keep hopping instead of settling",
        ending_image="the question light dimmed beside the bed",
    ),
}

CAUTION_ITEMS = {
    "nightlight": CautionItem(
        id="nightlight",
        label="a little nightlight",
        helps_against={"darkness", "worry"},
        place_phrase="on the shelf by the bed",
        story_offer="turn on the little nightlight",
        story_use="the little nightlight glowed like a tiny star",
    ),
    "blanket": CautionItem(
        id="blanket",
        label="a soft blanket",
        helps_against={"cold", "worry", "grumpiness"},
        place_phrase="at the foot of the bed",
        story_offer="pull up the soft blanket",
        story_use="the soft blanket tucked the child in like a hug",
    ),
    "stuffed_fox": CautionItem(
        id="stuffed_fox",
        label="a stuffed fox",
        helps_against={"worry", "grumpiness"},
        place_phrase="on the pillow",
        story_offer="bring the stuffed fox close",
        story_use="the stuffed fox listened with its button eyes",
    ),
    "warm_milk": CautionItem(
        id="warm_milk",
        label="a mug of warm milk",
        helps_against={"worry", "grumpiness", "noise"},
        place_phrase="on the bedside table",
        story_offer="sip the warm milk slowly",
        story_use="the warm milk made the room feel gentler",
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Ivy", "Nora", "Ada", "Ruby", "Eli", "Maya", "Zoe", "Luna"]
BOY_NAMES = ["Noah", "Theo", "Finn", "Leo", "Ben", "Max", "Owen", "Eli", "Jack", "Sam"]
UNISEX_NAMES = ["Robin", "Sky", "Parker", "Rowan", "Casey"]

TRAITS = ["curious", "stubborn", "gentle", "spirited", "dreamy", "sensitive", "restless"]

# -----------------------------------------------------------------------------
# Story helpers
# -----------------------------------------------------------------------------

def _child_desc(child: Child) -> str:
    return f"little {child.traits[0]} {child.type}"


def _room_phrase(room: Room) -> str:
    return room.name


def _apply_activity(world: World, activity: Activity, narrate: bool = True) -> None:
    c = world.child
    c.meters["sleepiness"] += activity.effect_sleep
    c.meters["noise"] += activity.effect_noise
    c.memes["attitude"] += activity.effect_attitude
    c.memes["joy"] += 0.2
    if activity.id == "one_more_game":
        c.memes["grumpiness"] += 0.4
    if activity.id == "one_more_question":
        c.memes["worry"] += 0.3
    if narrate:
        world.say(f"{c.name} wanted to {activity.verb} instead of going to sleep.")


def _predict_tiredness(world: World, activity: Activity) -> dict:
    sim = world.copy()
    _apply_activity(sim, activity, narrate=False)
    child = sim.child
    return {
        "sleepy": child.meters["sleepiness"] >= THRESHOLD,
        "noisy": child.meters["noise"] >= THRESHOLD,
        "grumpy": child.memes["grumpiness"] >= THRESHOLD,
    }


def _warn(world: World, activity: Activity) -> bool:
    pred = _predict_tiredness(world, activity)
    if not pred["sleepy"] and not pred["noisy"] and not pred["grumpy"]:
        return False
    c = world.child
    p = world.parent
    world.say(f"\"{activity.warning},\" {p.name} said softly.")
    world.facts["predicted"] = pred
    return True


def _escalate(world: World, activity: Activity) -> None:
    c = world.child
    c.memes["attitude"] += 0.8
    c.memes["grumpiness"] += 0.5
    world.say(f"{c.name} crossed {c.pronoun('possessive')} arms and gave a dramatic sigh.")


def _comfort(world: World, item: CautionItem) -> None:
    c = world.child
    p = world.parent
    if "worry" in item.helps_against:
        c.memes["worry"] = max(0.0, c.memes["worry"] - 0.6)
        p.memes["worry"] = max(0.0, p.memes["worry"] - 0.2)
    if "grumpiness" in item.helps_against:
        c.memes["grumpiness"] = max(0.0, c.memes["grumpiness"] - 0.5)
    c.memes["calm"] += 0.8
    p.memes["trust"] += 0.6
    c.memes["trust"] += 0.4
    world.say(f"{p.name} offered {item.story_offer}.")
    world.say(item.story_use + ".")


def _resolution(world: World, activity: Activity, item: CautionItem) -> None:
    c = world.child
    c.memes["relief"] += 1.0
    c.memes["attitude"] = max(0.0, c.memes["attitude"] - 0.4)
    c.memes["grumpiness"] = 0.0
    c.memes["worry"] = max(0.0, c.memes["worry"] - 0.2)
    world.room.meters["darkness"] += 0.8
    world.room.memes["cozy"] += 1.0
    world.room.memes["calm"] += 1.0
    world.say(
        f"At last, {c.name} listened, and the room grew quieter and kinder."
    )
    world.say(
        f"{activity.ending_image.capitalize()}, and {c.name} lay down feeling safe."
    )


def tell(params: StoryParams) -> World:
    room = ROOMS[params.room]
    child = Child(
        id="child",
        name=params.child_name,
        label=params.child_name,
        traits=[params.child_trait, "little"],
    )
    parent = Parent(
        id="parent",
        name=params.parent_label,
        label=params.parent_label,
        traits=["careful", "patient"],
    )
    world = World(room=room, child=child, parent=parent)
    activity = ACTIVITIES[params.chosen_activity]
    item = CAUTION_ITEMS[params.caution_item]
    world.facts.update(activity=activity, item=item, room=room)

    # Act 1: bedtime setup.
    world.say(
        f"It was bedtime in {room.name}, and {child.name} was a {_child_desc(child)} who still had energy in {child.pronoun('possessive')} toes."
    )
    world.say(
        f"{child.name} liked the soft pillow, but {child.pronoun('subject')} kept asking for {activity.noun}."
    )

    # Act 2: the cautionary turn.
    world.para()
    world.say(f"{parent.name} knew a little warning was needed.")
    _apply_activity(world, activity, narrate=True)
    warned = _warn(world, activity)
    _escalate(world, activity)

    # Act 3: a careful comfort and a bedtime ending.
    world.para()
    _comfort(world, item)
    if warned:
        world.say(
            f"Together they chose the safe, sleepy way: no more extra play, only quiet care."
        )
    _resolution(world, activity, item)

    world.facts.update(resolved=True, warned=warned)
    return world

# -----------------------------------------------------------------------------
# Registries and constraints
# -----------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id in ROOMS:
        for act_id in ACTIVITIES:
            for item_id, item in CAUTION_ITEMS.items():
                act = ACTIVITIES[act_id]
                if act.id == "one_more_game" and "noise" in item.helps_against:
                    combos.append((room_id, act_id, item_id))
                elif act.id == "one_more_book" and ("worry" in item.helps_against or "darkness" in item.helps_against):
                    combos.append((room_id, act_id, item_id))
                elif act.id == "one_more_question" and ("worry" in item.helps_against or "grumpiness" in item.helps_against):
                    combos.append((room_id, act_id, item_id))
    return combos


CURATED = [
    StoryParams(child_name="Mia", child_trait="curious", parent_label="Mama", room="bedroom", chosen_activity="one_more_book", caution_item="nightlight"),
    StoryParams(child_name="Leo", child_trait="stubborn", parent_label="Dad", room="nursery", chosen_activity="one_more_game", caution_item="blanket"),
    StoryParams(child_name="Robin", child_trait="dreamy", parent_label="Parent", room="cozy_room", chosen_activity="one_more_question", caution_item="stuffed_fox"),
]

# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, activity, item, room = world.child, world.parent, f["activity"], f["item"], world.room
    return [
        f'Write a short bedtime story for a young child named {child.name} who wants to {activity.verb}.',
        f"Tell a gentle cautionary story where {parent.name} worries that {child.name}'s attitude will make bedtime run too late.",
        f"Write a bedtime story set in {room.name} with a soft ending that uses {item.label} to help {child.name} settle down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, activity, item, room = world.child, world.parent, f["activity"], f["item"], world.room
    return [
        QAItem(
            question=f"What did {child.name} want to do instead of sleeping?",
            answer=f"{child.name} wanted to {activity.verb}, which made bedtime feel a little longer than it should have been.",
        ),
        QAItem(
            question=f"Why did {parent.name} give a warning?",
            answer=f"{parent.name} gave a warning because keeping on with {activity.noun} could make {child.name} too sleepy, too noisy, or too grumpy for a gentle bedtime.",
        ),
        QAItem(
            question=f"What helped {child.name} settle down in the end?",
            answer=f"{item.label} helped, and it made the room feel calmer while {child.name} got ready to sleep.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"The story happened in {room.name}, where the bed, the quiet, and the soft light all belonged to bedtime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    item = world.facts["item"]
    activity = world.facts["activity"]
    out = [
        QAItem(
            question="Why is bedtime important?",
            answer="Bedtime helps a child rest so the next day can begin with more energy, clearer thoughts, and a happier mood.",
        ),
        QAItem(
            question="What does a nightlight do?",
            answer="A nightlight gives a small, gentle glow so a room is not too dark and sleepy children can feel safer.",
        ),
    ]
    if item.id == "blanket":
        out.append(QAItem(
            question="What is a blanket for?",
            answer="A blanket keeps someone warm and can feel comforting when it is time to rest.",
        ))
    if activity.id == "one_more_game":
        out.append(QAItem(
            question="Why can playing late be a problem?",
            answer="Playing late can make it harder for a child to calm down, so sleep arrives more slowly.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)

# -----------------------------------------------------------------------------
# Trace
# -----------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    c, p, r = world.child, world.parent, world.room
    lines = ["--- world model state ---"]
    lines.append(f"child: meters={c.meters} memes={c.memes}")
    lines.append(f"parent: meters={p.meters} memes={p.memes}")
    lines.append(f"room: meters={r.meters} memes={r.memes}")
    for obj in world.objects.values():
        lines.append(f"object {obj.name}: meters={obj.meters} memes={obj.memes}")
    lines.append(f"fired rules: {sorted(world.fired)}")
    return "\n".join(lines)

# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
% A combo is valid when the activity's bedtime risk is softened by the chosen item.
valid(Room, Activity, Item) :- room(Room), activity(Activity), item(Item),
    softens(Item, Activity).

softens(Item, one_more_book) :- helps(Item, darkness).
softens(Item, one_more_book) :- helps(Item, worry).
softens(Item, one_more_game) :- helps(Item, noise).
softens(Item, one_more_question) :- helps(Item, worry).
softens(Item, one_more_question) :- helps(Item, grumpiness).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for iid, item in CAUTION_ITEMS.items():
        lines.append(asp.fact("item", iid))
        for h in sorted(item.helps_against):
            lines.append(asp.fact("helps", iid, h))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary bedtime story world with a child, a warning, and a soft landing.")
    ap.add_argument("--room", choices=ROOMS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--item", choices=CAUTION_ITEMS.keys())
    ap.add_argument("--name")
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
    filtered = [c for c in combos
                if (args.room is None or c[0] == args.room)
                and (args.activity is None or c[1] == args.activity)
                and (args.item is None or c[2] == args.item)]
    if not filtered:
        raise StoryError("(No valid bedtime story matches the given options.)")
    room, act, item = rng.choice(sorted(filtered))
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES + UNISEX_NAMES)
    return StoryParams(
        child_name=name,
        child_trait=trait,
        parent_label="Mama" if rng.random() < 0.5 else "Dad",
        room=room,
        chosen_activity=act,
        caution_item=item,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (room, activity, item) combos:\n")
        for r, a, i in combos:
            print(f"  {r:10} {a:18} {i}")
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
            header = f"### {p.child_name}: {p.chosen_activity} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
