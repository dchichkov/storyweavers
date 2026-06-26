#!/usr/bin/env python3
"""
storyworlds/worlds/see_edge_kindness_nursery_rhyme.py
======================================================

A small nursery-rhyme storyworld about seeing the edge, choosing kindness,
and finding a safe way to play.

Seed-tale idea:
A little child sees the edge of a stream and wants to step closer. A caring
grown-up worries that the bank is slippery. A kind friend offers a safer
game, and everyone ends with smiles by the water.

The simulated world keeps two kinds of state:
- meters: physical things such as closeness, wetness, and safety
- memes: emotional things such as curiosity, worry, and kindness

The prose is intended to feel like a gentle nursery rhyme: concrete, simple,
and lightly musical, while still being driven by the simulation.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self) -> None:
        for k in ["near_edge", "wet", "safe", "balance", "work"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "kindness", "joy", "fear"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "bunny"}
        male = {"boy", "father", "dad", "man", "fox", "bear"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    edge_kind: str
    has_water: bool = True


@dataclass
class Thing:
    label: str
    phrase: str
    region: str
    safe_gear: bool = False
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    child_type: str
    child_name: str
    parent_type: str
    friend_type: str
    thing: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "brook": Place(name="the brook", edge_kind="bank", has_water=True),
    "pond": Place(name="the pond", edge_kind="rim", has_water=True),
    "garden": Place(name="the garden", edge_kind="bed", has_water=False),
}

THINGS = {
    "boots": Thing(label="boots", phrase="little red boots", region="feet", safe_gear=True, plural=True),
    "cloak": Thing(label="cloak", phrase="a warm cloak", region="torso", safe_gear=True),
    "basket": Thing(label="basket", phrase="a woven basket", region="hands"),
    "ribbon": Thing(label="ribbon", phrase="a bright ribbon", region="hair"),
}

CHILDREN = {
    "girl": ["Mina", "Lily", "Nora", "Mabel"],
    "boy": ["Theo", "Robin", "Peter", "Finn"],
}

FRIEND_TYPES = ["rabbit", "duck", "mouse", "bird"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, thing) for place in SETTINGS for thing in THINGS if place in {"brook", "pond"} or thing != "boots"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.thing and args.thing not in THINGS:
        raise StoryError("Unknown thing.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.thing is None or c[1] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, thing = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILDREN[child_type])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    return StoryParams(
        place=place,
        child_type=child_type,
        child_name=child_name,
        parent_type=parent_type,
        friend_type=friend_type,
        thing=thing,
    )


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="grown-up"))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label="friend"))
    item = world.add(Entity(id="thing", type="thing", label=THINGS[params.thing].label, phrase=THINGS[params.thing].phrase))
    item.worn_by = child.id
    child.memes["curiosity"] += 1
    child.memes["kindness"] += 1
    world.facts.update(child=child, parent=parent, friend=friend, item=item, place=place, params=params)
    return world


def predict_mess(world: World, child: Entity) -> bool:
    return child.meters["near_edge"] >= THRESHOLD and world.place.has_water


def tell(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    friend = world.facts["friend"]
    item = world.facts["item"]
    place = world.place

    world.say(
        f"Little {child.id} went a-walk in {place.name}, with {item.phrase held tight."
    )
    world.say(
        f"{child.id} could see the {place.edge_kind} of the water, where the reeds swayed bright."
    )
    child.meters["near_edge"] += 1
    child.memes["curiosity"] += 1

    if predict_mess(world, child):
        world.say(
            f'"Oh, child," said the {parent.type}, "that edge may slip if feet go near the wet."'  # nursery-rhyme voice
        )
        parent.memes["worry"] += 1
        child.memes["worry"] += 1
        child.memes["fear"] += 1
        child.meters["safe"] += 0.0

    world.para()
    world.say(
        f"But {child.id} wished to see the water sparkle, and step just once, and yet..."
    )
    child.meters["near_edge"] += 1
    child.memes["curiosity"] += 1

    friend.memes["kindness"] += 1
    world.say(
        f"{friend.pronoun().capitalize()} came with a kind idea: " 
        f'"Let us play at the edge, but not on the slick wet side."'
    )
    world.say(
        f'They set {item.it()} by a stone and made a game of counting ripples instead.'
    )
    child.memes["kindness"] += 1
    child.memes["joy"] += 1
    parent.memes["worry"] = max(0.0, parent.memes["worry"] - 1)
    child.meters["safe"] += 1
    child.meters["near_edge"] = 0.0

    world.para()
    world.say(
        f"So {child.id} laughed, and the {parent.type} laughed too, and the little friend did grin."
    )
    world.say(
        f"{child.id} could still see the {place.edge_kind} of the water, but stayed safe beside the shin."
    )

    world.facts["resolved"] = True
    world.facts["kindness"] = child.memes["kindness"]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short nursery-rhyme story for a small child with the word "see" and the word "edge".',
        f"Tell a gentle story where {p.child_name} sees the edge of {world.place.name} and learns a kind, safe way to play.",
        f"Write a rhyme-like tale about kindness at the edge of the water, with a grown-up and a friend helping the child.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    friend = world.facts["friend"]
    item = world.facts["item"]
    place = world.place
    return [
        QAItem(
            question=f"What did {p.child_name} see near {place.name}?",
            answer=f"{p.child_name} saw the {place.edge_kind} of the water near {place.name}.",
        ),
        QAItem(
            question=f"Why did the {parent.type} worry when {p.child_name} moved close to the edge?",
            answer=f"The {parent.type} worried because the edge could be slippery and not safe to step on.",
        ),
        QAItem(
            question=f"How did the friend help {p.child_name} in a kind way?",
            answer=f"The friend offered a kinder game and suggested staying by the safe side of the edge instead of stepping into the slick water.",
        ),
        QAItem(
            question=f"What did {p.child_name} do with {item.phrase} at the end?",
            answer=f"{p.child_name} set {item.it()} by a stone and played a counting game beside the water.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an edge?",
            answer="An edge is the outer line or border of something, like the side of a pond or a table.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about how someone else feels.",
        ),
        QAItem(
            question="Why do people stay back from a slippery bank?",
            answer="People stay back from a slippery bank so they do not fall into the water.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story q&a ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world q&a ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 0.0}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 0.0}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.worn_by:
            parts.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for place, p in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if p.has_water:
            lines.append(asp.fact("has_water", place))
        lines.append(asp.fact("edge_kind", place, p.edge_kind))
    for thing, t in THINGS.items():
        lines.append(asp.fact("thing", thing))
        lines.append(asp.fact("region", thing, t.region))
        if t.safe_gear:
            lines.append(asp.fact("safe_gear", thing))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Thing) :- place(Place), thing(Thing), has_water(Place).
valid(Place, Thing) :- place(Place), thing(Thing), not safe_gear(Thing).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if p - a:
        print("  only in python:", sorted(p - a))
    if a - p:
        print("  only in clingo:", sorted(a - p))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about see, edge, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="brook", child_type="girl", child_name="Mina", parent_type="mother", friend_type="rabbit", thing="boots"),
            StoryParams(place="pond", child_type="boy", child_name="Theo", parent_type="father", friend_type="duck", thing="cloak"),
            StoryParams(place="garden", child_type="girl", child_name="Lily", parent_type="mother", friend_type="mouse", thing="basket"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
