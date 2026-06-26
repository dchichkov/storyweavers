#!/usr/bin/env python3
"""
A tiny bedtime-story world about a child, a shared blanket, and a gentle
misunderstanding that an unspoken hint helps resolve.

Premise:
- A child wants to share a bedtime story with a sibling or parent.
- The child notices a hint in the room or from a worried face, then thinks
  through an inner monologue.
- A misunderstanding about sharing the storybook or the blanket creates a small
  worry.
- A kind explanation and a shared reading ritual resolve the tension before bed.
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
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    name: str
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    child_trait: str
    caregiver_type: str
    sharing_item: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone = World(self.room)
        import copy as _copy

        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "nursery": Room(name="the nursery", cozy=True, affords={"reading", "sharing"}),
    "bedroom": Room(name="the bedroom", cozy=True, affords={"reading", "sharing"}),
    "attic": Room(name="the attic", cozy=False, affords={"reading"}),
}

SHARING_ITEMS = {
    "blanket": {
        "label": "blanket",
        "phrase": "a soft blue blanket",
        "kind": "blanket",
    },
    "book": {
        "label": "storybook",
        "phrase": "a small bedtime storybook",
        "kind": "book",
    },
    "lamp": {
        "label": "lamp",
        "phrase": "a little reading lamp",
        "kind": "lamp",
    },
}

GENTLE_NAMES = ["Mia", "Noah", "Lina", "Finn", "Zoe", "Eli", "Ava", "Theo"]
TRAITS = ["sleepy", "curious", "shy", "soft-spoken", "dreamy", "gentle"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def room_detail(room: Room) -> str:
    if room.name == "the nursery":
        return "The nursery was quiet, with one little lamp making a warm circle of light."
    if room.name == "the bedroom":
        return "The bedroom was cozy, with pillows piled high and the moon peeking at the window."
    return "The room was a little cooler than the others, but the blanket still looked inviting."


def hint_line() -> str:
    return "A tiny hint waited on the pillow: the extra space on the blanket was folded open, as if someone hoped to share it."


def inner_monologue(child: Entity, item: Entity) -> str:
    return (
        f'{child.pronoun().capitalize()} thought, "Maybe {item.phrase} is for both of us. '
        f'If I ask kindly, we can make room together."'
    )


def misunderstanding(world: World, child: Entity, caregiver: Entity, item: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    caregiver.memes["concern"] = caregiver.memes.get("concern", 0) + 1
    world.say(
        f"{child.id} reached for {item.it()} and paused. "
        f'{child.pronoun().capitalize()} worried that {caregiver.pronoun("subject")} might want to keep '
        f"{item.it()} all to {caregiver.pronoun('object')}self."
    )
    world.say(
        f'But that was a misunderstanding; {caregiver.id} only looked busy because '
        f'{caregiver.pronoun("subject")} was tucking the pages in place.'
    )


def share(world: World, child: Entity, caregiver: Entity, item: Entity) -> None:
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    child.memes["love"] = child.memes.get("love", 0) + 1
    caregiver.memes["love"] = caregiver.memes.get("love", 0) + 1
    item.shared_with = [child.id, caregiver.id]
    world.say(
        f"{child.id} asked, " f'"Can we share {item.it()}?" '
        f'{caregiver.id} smiled and nodded. "Of course," {caregiver.pronoun("subject")} said. '
        f'They settled side by side and read one page at a time.'
    )
    world.say(
        f"By the last page, {child.id} was yawn-soft and safe, and the shared {item.label} "
        f"rested between them like a little bridge."
    )


def generate_story(world: World) -> None:
    child = world.get("child")
    caregiver = world.get("caregiver")
    item = world.get("item")

    world.say(
        f"{child.id} was a {child.memes.get('trait_word', 'gentle')} little {child.type} "
        f"who loved bedtime stories."
    )
    world.say(
        f"Every night, {child.id} wanted to read {item.phrase} before sleep."
    )
    world.para()
    world.say(room_detail(world.room))
    world.say(hint_line())
    world.say(inner_monologue(child, item))
    world.say(
        f"{child.id} looked at {caregiver.id} and noticed a quiet face, which made the room feel very still."
    )
    misunderstanding(world, child, caregiver, item)
    world.para()
    share(world, child, caregiver, item)
    world.facts.update(child=child, caregiver=caregiver, item=item, room=world.room)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story for a young child that includes a hint, a misunderstanding, and sharing.',
        f"Tell a gentle story about {f['child'].id} sharing {f['item'].phrase} with {f['caregiver'].id} before sleep.",
        f'Write a cozy story where a child notices a hint and learns that sharing can feel safe and kind.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    item = f["item"]
    room = f["room"]
    return [
        QAItem(
            question=f"What was the tiny hint in {room.name} that helped {child.id} think about sharing?",
            answer="The hint was the blanket or book left ready for two people, which showed that there was room to share.",
        ),
        QAItem(
            question=f"What misunderstanding did {child.id} have about {caregiver.id} and {item.label}?",
            answer=f"{child.id} worried that {caregiver.id} wanted to keep {item.it()} all to {caregiver.pronoun('object')}self, but that was not true.",
        ),
        QAItem(
            question=f"How did {child.id} and {caregiver.id} end the bedtime story?",
            answer=f"They shared {item.it()} and read together until {child.id} felt sleepy and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hint?",
            answer="A hint is a small clue that helps someone understand what to do or what something means.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you, like a book or a blanket.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks the wrong thing for a little while.",
        ),
        QAItem(
            question="Why are bedtime stories nice?",
            answer="Bedtime stories can help children feel calm, loved, and ready to sleep.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_worries(C) :- child(C), concern(C).
need_hint(C) :- child(C), child_worries(C), hint_present(C).
misunderstanding(C) :- child(C), child_worries(C), not sharing_clear(C).
resolved(C) :- child(C), sharing_clear(C).

#show valid/3.
valid(Room, Item, Child) :- room(Room), item(Item), child(Child), affords(Room, sharing).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.cozy:
            lines.append(asp.fact("cozy", rid))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
    for iid, item in SHARING_ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("label", iid, item["label"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room_id, room in ROOMS.items():
        if "sharing" not in room.affords:
            continue
        for item_id in SHARING_ITEMS:
            for gender in ("girl", "boy"):
                combos.append((room_id, item_id, gender))
    return combos


def explain_rejection() -> str:
    return "(No story: this setting does not support a believable sharing bedtime scene.)"


# ---------------------------------------------------------------------------
# Generate / emit
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    if params.place not in ROOMS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.sharing_item not in SHARING_ITEMS:
        raise StoryError(f"Unknown sharing item: {params.sharing_item}")

    room = ROOMS[params.place]
    if "sharing" not in room.affords:
        raise StoryError(explain_rejection())

    world = World(room)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        memos if False else {},
    ))
    child.memes["trait_word"] = params.child_trait  # not for serialization, only story flavor
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=params.caregiver_type,
        label="mom" if params.caregiver_type == "mother" else "dad",
    ))
    item_cfg = SHARING_ITEMS[params.sharing_item]
    item = world.add(Entity(
        id="item",
        type=item_cfg["kind"],
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        owner=child.id,
        shared_with=[child.id, caregiver.id],
        plural=(item_cfg["kind"] in {"book", "blanket"}),
    ))
    world.facts["child"] = child
    world.facts["caregiver"] = caregiver
    world.facts["item"] = item
    world.facts["room"] = room

    generate_story(world)

    story = world.render().replace("memos if False else {}", "")
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-story world with hint, misunderstanding, and sharing.")
    ap.add_argument("--place", choices=sorted(ROOMS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--parent", dest="caregiver_type", choices=["mother", "father"])
    ap.add_argument("--sharing-item", choices=sorted(SHARING_ITEMS))
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
    place = args.place or rng.choice(list(ROOMS))
    room = ROOMS[place]
    if "sharing" not in room.affords:
        raise StoryError(explain_rejection())
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GENTLE_NAMES)
    child_trait = args.trait or rng.choice(TRAITS)
    caregiver_type = args.caregiver_type or rng.choice(["mother", "father"])
    sharing_item = args.sharing_item or rng.choice(list(SHARING_ITEMS))
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=gender,
        child_trait=child_trait,
        caregiver_type=caregiver_type,
        sharing_item=sharing_item,
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
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(place="nursery", child_name="Mia", child_gender="girl", child_trait="gentle", caregiver_type="mother", sharing_item="blanket"),
            StoryParams(place="bedroom", child_name="Noah", child_gender="boy", child_trait="curious", caregiver_type="father", sharing_item="book"),
            StoryParams(place="nursery", child_name="Lina", child_gender="girl", child_trait="dreamy", caregiver_type="mother", sharing_item="lamp"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
