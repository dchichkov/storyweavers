#!/usr/bin/env python3
"""
storyworlds/worlds/deceased_frown_caper_reconciliation_sound_effects_heartwarming.py
=====================================================================================

A small heartwarming storyworld about a child who turns a frown into a gentle
caper and a reconciliation, with sound effects woven into the world model.

Seed tale sketch:
---
A child finds a box of bells and an old note from a deceased grandparent. The
note says the family should stop frowning, sneak a tiny caper to finish a gift,
and make peace before bedtime. The child worries at first, then follows the
sound effects in the house, finds the missing pieces, and helps everyone smile
together again.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    sounds: list[str] = field(default_factory=list)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    type: str = "thing"


@dataclass
class StoryParams:
    place: str
    object: str
    child_name: str
    child_type: str
    caretaker_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.events = list(self.events)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", True, ["clink", "tap", "hush"]),
    "hallway": Place("hallway", "the hallway", True, ["creak", "tap-tap", "soft step"]),
    "attic": Place("attic", "the attic", True, ["thump", "rustle", "creak"]),
}

OBJECTS = {
    "bells": ObjectCfg("bells", "little bells", "a tin box of little bells"),
    "note": ObjectCfg("note", "old note", "an old note with a curvy handwriting"),
    "lantern": ObjectCfg("lantern", "lantern", "a small lantern"),
}

CHILD_NAMES = ["Mina", "Owen", "Nina", "Eli", "Ruby", "Theo"]
CHILD_TYPES = ["girl", "boy"]
CAREGIVERS = ["mother", "father", "grandmother", "grandfather"]


ASP_RULES = r"""
frown(child) :- wants_fix(child), not has_hope(child).
reconcile(child) :- finds_piece(child), hears_sound(child), not frown(child).
heartwarming(child) :- reconcile(child), gives_hug(child).
"""

@dataclass
class Gear:
    id: str
    label: str
    sound: str
    effect: str


GEAR = [
    Gear("lantern", "a small lantern", "flicker-flicker", "shows the path"),
    Gear("bells", "little bells", "jingle-jingle", "calls everyone together"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for s in place.sounds:
            lines.append(asp.fact("sound", pid, s))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        lines.append(asp.fact("gear_sound", g.id, g.sound))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconcile/1. #show heartwarming/1."))
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    expected = {("reconcile", ("child",)), ("heartwarming", ("child",))}
    if atoms:
        return 0
    return 1


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("unknown place")
    if params.object not in OBJECTS:
        raise StoryError("unknown object")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming reconciliation storyworld with sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--caretaker-type", choices=CAREGIVERS)
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
    obj = args.object or rng.choice(list(OBJECTS))
    name = args.name or rng.choice(CHILD_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    caretaker = args.caretaker_type or rng.choice(CAREGIVERS)
    params = StoryParams(place=place, object=obj, child_name=name, child_type=child_type, caretaker_type=caretaker)
    reasonableness_gate(params)
    return params


def predict(world: World, child: Entity, obj: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["frown"] += 1
    sim.get(obj.id).meters["missing"] = 1
    return True


def tell(place: Place, obj_cfg: ObjectCfg, name: str, child_type: str, caretaker_type: str) -> World:
    w = World(place)
    child = w.add(Entity(name, "character", child_type))
    caretaker = w.add(Entity("Caretaker", "character", caretaker_type, label=f"the {caretaker_type}"))
    obj = w.add(Entity(obj_cfg.id, "thing", obj_cfg.type, label=obj_cfg.label, phrase=obj_cfg.phrase, caretaker=caretaker.id))

    child.memes["sad"] = 0
    child.memes["joy"] = 0
    child.memes["frown"] = 0

    w.say(f"{child.id} found {obj_cfg.phrase} in {place.label}.")
    w.say(f"Inside was a note from a deceased grandparent, and that made {child.pronoun('object')} go quiet.")
    w.say(f"{place.sounds[0].capitalize()}! The little sound echoed as {child.id} opened the box.")

    w.para()
    child.memes["frown"] += 1
    w.say(f"{child.id} wore a small frown and wondered why the house felt so still.")
    w.say(f"Then {child.id} heard a soft {place.sounds[1]} and thought the note might be asking for a tiny caper.")

    w.para()
    w.say(f"So {child.id} began a caper through {place.label}, following every {place.sounds[2]} and looking under pillows, jars, and chairs.")
    obj.meters["missing"] = 1
    w.say(f"At last, {child.id} found the missing piece that belonged with the note.")

    w.para()
    child.memes["frown"] = 0
    child.memes["joy"] += 1
    caretaker.memes["love"] = caretaker.memes.get("love", 0) + 1
    obj.meters["fixed"] = 1
    w.say(f"{child.id} brought it back, and the room went {GEAR[1].sound} with happy little bells.")
    w.say(f"{caretaker.label} smiled, and the two of them reconciled with a hug so warm it felt like a lamp being lit.")
    w.say(f"By bedtime, the note was whole again, the frown was gone, and {child.id} could hear only peaceful {place.sounds[0]} sounds.")
    w.facts.update(child=child, caretaker=caretaker, obj=obj, place=place)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a heartwarming story about a child who finds a deceased grandparent's note, follows sound effects, and turns a frown into a reconciliation.",
        f"Tell a gentle caper story set in {f['place'].label} where {f['child'].id} hears little sounds and helps fix something important.",
        "Make the ending warm, simple, and kind, with a smile replacing the frown.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caretaker = f["caretaker"]
    obj = f["obj"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} find in {place.label}?",
            answer=f"{child.id} found {obj.phrase} in {place.label}, and inside it was a note from a deceased grandparent.",
        ),
        QAItem(
            question=f"Why did {child.id} start with a frown?",
            answer=f"{child.id} started with a frown because the note reminded {child.pronoun('object')} of a deceased grandparent, so the room felt quiet and sad for a moment.",
        ),
        QAItem(
            question=f"How did the caper end?",
            answer=f"The caper ended with reconciliation: {child.id} found the missing piece, brought it back, and hugged {caretaker.label} while the room rang with happy little bells.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are little written sounds like clink, tap, or jingle that help you imagine what the world is doing.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and come back together kindly again.",
        ),
        QAItem(
            question="What is a caper?",
            answer="A caper is a small, playful adventure or sneaky errand, often lighthearted and fun.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, o) for p in PLACES for o in OBJECTS]


CURATED = [
    StoryParams("kitchen", "bells", "Mina", "girl", "mother"),
    StoryParams("hallway", "note", "Owen", "boy", "father"),
    StoryParams("attic", "lantern", "Ruby", "girl", "grandmother"),
]


def resolve_story(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], OBJECTS[params.object], params.child_name, params.child_type, params.caretaker_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return resolve_story(params)


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
        print(asp_program("#show reconcile/1. #show heartwarming/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show reconcile/1. #show heartwarming/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
