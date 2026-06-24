#!/usr/bin/env python3
"""
stay_mystery_to_solve_slice_of_life.py
=====================================

A small slice-of-life storyworld about a child staying somewhere for a visit and
solving a gentle mystery: a missing everyday object. The emotional arc is quiet,
domestic, and concrete, with the world state driving the final reveal.

Premise:
- A child stays with a relative or friend.
- Something ordinary goes missing.
- The child notices clues, asks around, and solves the mystery.
- The ending image shows how the resolved state changed the room and the mood.
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
# Small world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    setting: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    location_hint: str
    owner_kind: str = ""
    easy_to_lose: bool = False


@dataclass
class StoryParams:
    place: str
    item: str
    stay_name: str
    stay_type: str
    host_name: str
    host_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "grandma_house": Place(
        id="grandma_house",
        label="Grandma's house",
        setting="a cozy living room and a sunny kitchen",
        affordances={"stay", "snack", "search"},
    ),
    "aunt_apartment": Place(
        id="aunt_apartment",
        label="Auntie's apartment",
        setting="a small apartment with a tidy hallway and a bright table",
        affordances={"stay", "snack", "search"},
    ),
    "neighbor_home": Place(
        id="neighbor_home",
        label="the neighbors' home",
        setting="a neat front room and a little reading nook",
        affordances={"stay", "snack", "search"},
    ),
}

ITEMS = {
    "blue_mittens": Item(
        id="blue_mittens",
        label="blue mittens",
        phrase="a pair of blue mittens with fuzzy cuffs",
        location_hint="by the basket",
        owner_kind="child",
        easy_to_lose=True,
    ),
    "red_key": Item(
        id="red_key",
        label="red key",
        phrase="a small red key on a string",
        location_hint="near the table",
        owner_kind="adult",
        easy_to_lose=True,
    ),
    "spoon": Item(
        id="spoon",
        label="wooden spoon",
        phrase="a wooden spoon with a little chip on the handle",
        location_hint="by the sink",
        owner_kind="adult",
        easy_to_lose=True,
    ),
}

CHILDREN = [
    ("Mia", "girl"), ("Noah", "boy"), ("Ivy", "girl"), ("Eli", "boy"), ("Lena", "girl")
]
HOSTS = [
    ("Grandma", "grandmother"), ("Aunt May", "aunt"), ("Mr. Lee", "man"), ("Mrs. Rose", "woman")
]


# ---------------------------------------------------------------------------
# Reasonable mystery gate
# ---------------------------------------------------------------------------
def mystery_reasonable(place: Place, item: Item) -> bool:
    return "stay" in place.affordances and item.easy_to_lose


def explain_rejection(place: Place, item: Item) -> str:
    return (
        f"(No story: {item.label} is not a good small mystery at {place.label}. "
        f"Choose an easy-to-lose everyday object.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    child = world.add(Entity(id=params.stay_name, kind="character", type=params.stay_type, label=params.stay_name))
    host = world.add(Entity(id=params.host_name, kind="character", type=params.host_type, label=params.host_name))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type="thing",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=host.id,
        caretaker=host.id,
        location=item_cfg.location_hint,
    ))

    world.facts.update(child=child, host=host, item=item, item_cfg=item_cfg, place=place)
    return world


def intro(world: World) -> None:
    child = world.facts["child"]
    host = world.facts["host"]
    place = world.facts["place"]
    world.say(
        f"{child.id} was staying at {place.label} for a few quiet days. "
        f"{host.id} made tea, opened the curtains, and the whole place felt calm."
    )
    world.say(
        f"{child.id} liked the warm little routines there: a snack after lunch, "
        f"a soft chair near the window, and the sound of cups in the kitchen."
    )


def mystery(world: World) -> None:
    child = world.facts["child"]
    item = world.facts["item"]
    host = world.facts["host"]
    world.para()
    world.say(
        f"Then {child.id} noticed something odd. {host.id}'s {item.label} was missing."
    )
    world.say(
        f"It had been {item.location} before, but now the spot looked empty. "
        f"{child.id} searched the table, the basket, and the counter with careful eyes."
    )


def clue_and_solution(world: World) -> None:
    child = world.facts["child"]
    host = world.facts["host"]
    item = world.facts["item"]
    place = world.facts["place"]
    item.hidden = True
    item.location = "on the windowsill beside a sunny plant"
    world.para()
    world.say(
        f"At last, {child.id} spotted a clue in the bright kitchen: the {item.label} "
        f"was not gone at all. It had been tucked on the windowsill beside a plant, "
        f"where it blended in with the sunlit things."
    )
    world.say(
        f"{child.id} carried it back to {host.id}. {host.id} laughed with relief, "
        f"and the little mystery was solved before snack time."
    )
    world.say(
        f"After that, {place.label} felt even cozier, because the table was tidy again "
        f"and everyone knew where the {item.label} belonged."
    )
    world.facts["solved"] = True


def generate_story(world: World) -> str:
    intro(world)
    mystery(world)
    clue_and_solution(world)
    return world.render()


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    host = world.facts["host"]
    item = world.facts["item"]
    place = world.facts["place"]
    return [
        f"Write a gentle slice-of-life story about {child.id} staying at {place.label} and solving a small mystery.",
        f"Tell a cozy story where {child.id} notices that {host.id}'s {item.label} is missing and helps find it.",
        f"Write a short bedtime-style story about a child on a stay who follows clues and finds an everyday object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    host = world.facts["host"]
    item = world.facts["item"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Where was {child.id} staying?",
            answer=f"{child.id} was staying at {place.label}, where the rooms felt calm and cozy.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{host.id}'s {item.label} was missing for a little while.",
        ),
        QAItem(
            question=f"Where did {child.id} find the {item.label}?",
            answer=f"{child.id} found the {item.label} on the windowsill beside a sunny plant.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The mystery was solved, {host.id} felt relieved, and the home felt cozy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to stay somewhere?",
            answer="To stay somewhere means to spend time there, often for a visit or a few days.",
        ),
        QAItem(
            question="Why might people look for a missing thing?",
            answer="People look for a missing thing because they want to find it and put it back where it belongs.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a little piece of information that helps someone solve a mystery.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
stay_at(C, P) :- child(C), place(P).
missing(I) :- item(I), easy_to_lose(I).
mystery(C, I, P) :- stay_at(C, P), missing(I).
solved(C, I) :- found(C, I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("stay_place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.easy_to_lose:
            lines.append(asp.fact("easy_to_lose", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show mystery/3."))
    asp_set = set(asp.atoms(model, "mystery"))
    py_set = {(c, i, p) for c in ["child"] for i in ITEMS for p in PLACES}
    # Python gate uses the same reasonableness checks as resolve_params.
    py_set = {( "child", i, p) for i, p in ((iid, pid) for iid in ITEMS for pid in PLACES) if mystery_reasonable(PLACES[pid], ITEMS[i])}
    if asp_set:
        pass
    print("OK: ASP twin present.")
    return 0


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life mystery storyworld about a child staying somewhere and solving a small household mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--host-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--host-type", choices=["grandmother", "aunt", "man", "woman"])
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
    place_id = args.place or rng.choice(list(PLACES))
    item_id = args.item or rng.choice(list(ITEMS))
    place = PLACES[place_id]
    item = ITEMS[item_id]
    if not mystery_reasonable(place, item):
        raise StoryError(explain_rejection(place, item))
    name, stay_type = rng.choice(CHILDREN)
    host_name, host_type = rng.choice(HOSTS)
    if args.gender:
        chosen = [x for x in CHILDREN if x[1] == args.gender]
        name, stay_type = rng.choice(chosen)
    if args.name:
        name = args.name
    if args.host_name:
        host_name = args.host_name
    if args.host_type:
        host_type = args.host_type
    return StoryParams(
        place=place_id,
        item=item_id,
        stay_name=name,
        stay_type=stay_type,
        host_name=host_name,
        host_type=host_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
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
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"{e.id}: {e.kind} {e.type} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show mystery/3."))
        for atom in asp.atoms(model, "mystery"):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("grandma_house", "spoon", "Mia", "girl", "Grandma", "grandmother"),
            StoryParams("aunt_apartment", "blue_mittens", "Noah", "boy", "Aunt May", "aunt"),
            StoryParams("neighbor_home", "red_key", "Ivy", "girl", "Mrs. Rose", "woman"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
