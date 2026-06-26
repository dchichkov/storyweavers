#!/usr/bin/env python3
"""
storyworlds/worlds/consume_murder_moisten_happy_ending_bedtime_story.py
=======================================================================

A small bedtime-story world about a child, a cozy night, a tiny worry, and a
gentle happy ending.

Premise:
- A child is trying to fall asleep.
- Something feels too dry, too scratchy, or too worrying.
- A parent helps with a simple bedtime fix: moisten, consume, and settle down.
- The story ends with warmth, safety, and sleep.

The seed words ``consume``, ``murder``, and ``moisten`` are included as part of
the world vocabulary and the QA/generation prompts, while the narrated story
stays child-facing and gentle.
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
    room: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    cozy: bool = True


@dataclass
class ItemSpec:
    label: str
    phrase: str
    room: str
    purpose: str


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        paras: list[list[str]] = [[]]
        for line in self.events:
            if line == "__para__":
                if paras[-1]:
                    paras.append([])
            else:
                paras[-1].append(line)
        return "\n\n".join(" ".join(p) for p in paras if p)

    def para(self) -> None:
        self.say("__para__")

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "bedroom": Place("the bedroom", cozy=True),
    "nursery": Place("the nursery", cozy=True),
    "hallway": Place("the hallway", cozy=True),
}

ITEMS = {
    "milk": ItemSpec(
        label="warm milk",
        phrase="a small cup of warm milk",
        room="bedroom",
        purpose="drink",
    ),
    "blanket": ItemSpec(
        label="blanket",
        phrase="a soft blanket",
        room="bedroom",
        purpose="cover",
    ),
    "cloth": ItemSpec(
        label="cloth",
        phrase="a soft cloth",
        room="bathroom",
        purpose="moisten",
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Ruby", "Nina", "Poppy", "Ada"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Milo", "Ben", "Noah"]


def reasonableness_gate(place: str, item: str) -> bool:
    return place in PLACES and item in ITEMS


ASP_RULES = r"""
place(P) :- setting(P).
item(I) :- good_item(I).

valid(P, I) :- place(P), item(I).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for i in ITEMS:
        lines.append(asp.fact("good_item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, i) for p in PLACES for i in ITEMS if reasonableness_gate(p, i)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world with a gentle happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [(p, i) for p in PLACES for i in ITEMS if reasonableness_gate(p, i)]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if not combos:
        raise StoryError("(No valid bedtime-story combination matches the given options.)")
    place, item = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, item=item, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    item = world.add(Entity(
        id="comfort_item",
        type=params.item,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=hero.id,
        caretaker=parent.id,
        room=ITEMS[params.item].room,
    ))
    hero.memes["sleepy"] = 1.0
    world.say(f"{hero.id} was a little {params.gender} who lived in {world.place.name}.")
    world.say(f"At bedtime, {hero.id} liked to have {item.phrase} nearby.")
    world.say(f"One night, {hero.id} could not settle down because {item.label} felt too dry and scratchy.")
    world.para()
    if params.item == "cloth":
        world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} helped moisten the cloth just a little.")
        world.say(f"The soft dampness made it gentle again, and {hero.id} tucked it close.")
    elif params.item == "milk":
        world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} brought a little cup so {hero.id} could consume warm milk.")
        world.say(f"The warm sip made the dry feeling fade, and {hero.id} gave a tiny yawn.")
    else:
        world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} tucked the blanket in and smoothed the corners.")
        world.say(f"Then {hero.id} held still and listened to the quiet room until sleep grew near.")
    world.para()
    world.say("Outside, the night stayed calm.")
    world.say(f"Inside, {hero.id} finally curled up and smiled, because the little problem had turned kind.")
    world.say(f"Before sleep, {hero.id} asked what the word murder meant.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} answered that sometimes it can mean a flock of crows, and that tonight there was only one kind of ending: a happy one.")
    world.facts.update(hero=hero, parent=parent, item=item, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    return [
        f'Write a cozy bedtime story for a young child that includes the words "consume", "moisten", and "murder".',
        f"Tell a gentle bedtime story where {hero.id} cannot sleep until a parent helps with {item.label}.",
        f"Write a short bedtime story with a happy ending about a child, a soft room, and a tiny nighttime worry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    item = f["item"]
    return [
        QAItem(
            question=f"Why could {hero.id} not settle down at bedtime?",
            answer=f"{hero.id} could not settle down because {item.label} felt too dry and scratchy.",
        ),
        QAItem(
            question=f"How did {hero.pronoun('possessive')} {parent.label} help with {item.label}?",
            answer=(
                f"{hero.pronoun('possessive').capitalize()} {parent.label} helped in a gentle way so the bedtime problem got better."
            ) if item.id != "cloth" else f"{hero.pronoun('possessive').capitalize()} {parent.label} helped moisten the cloth just a little.",
        ),
        QAItem(
            question="What kind of ending did the story have?",
            answer="It ended happily, with the child calm, cozy, and ready for sleep.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to consume something?",
            answer="To consume something means to eat it or drink it up.",
        ),
        QAItem(
            question="What does moisten mean?",
            answer="To moisten something means to make it a little wet.",
        ),
        QAItem(
            question="What is a murder of crows?",
            answer="A murder of crows is the name for a group of crows.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
    StoryParams(place="bedroom", item="milk", name="Maya", gender="girl", parent="mother"),
    StoryParams(place="nursery", item="cloth", name="Theo", gender="boy", parent="father"),
    StoryParams(place="hallway", item="blanket", name="Ruby", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        valid = asp_valid()
        print(f"{len(valid)} valid combinations:")
        for p, i in valid:
            print(f"  {p} {i}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
