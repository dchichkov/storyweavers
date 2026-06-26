#!/usr/bin/env python3
"""
Heartwarming storyworld: pompom, peach, hominy, bravery, happy ending.

A small child wants to share a warm bowl of hominy with peaches with someone
who is lonely nearby. The path is a little scary, so the story turns on a
brave walk, a kind helper, and a happy ending with shared food.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    warm: bool = False
    fragile: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    outdoors: bool = False
    safe: bool = True
    breeze: str = "gentle"


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    tastes: list[str] = field(default_factory=list)


@dataclass
class Comfort:
    id: str
    label: str
    help_text: str
    courage: float = 1.0


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    child: str
    parent: str
    gift: str
    comfort: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", outdoors=False, safe=True, breeze="soft"),
    "porch": Place("porch", "the porch", outdoors=True, safe=True, breeze="cool"),
    "path": Place("path", "the front path", outdoors=True, safe=False, breeze="windy"),
}

GIFTS = {
    "peach_bowl": Gift("peach_bowl", "a bowl of peach hominy", "warm peach hominy", tastes=["peach", "hominy"]),
    "peach_slice": Gift("peach_slice", "peach slices", "sweet peach slices", tastes=["peach"]),
    "hominy_pot": Gift("hominy_pot", "a pot of hominy", "warm hominy", tastes=["hominy"]),
}

COMFORTS = {
    "pompom_hat": Comfort("pompom_hat", "a pompom hat", "feel cozy and brave", courage=1.0),
    "lantern": Comfort("lantern", "a little lantern", "light the dark path", courage=1.5),
    "handhold": Comfort("handhold", "a hand to hold", "walk together step by step", courage=2.0),
}

CHILD_NAMES = ["Mina", "Theo", "Luca", "Maya", "Iris", "Noah"]
PARENT_NAMES = ["Mom", "Dad", "Auntie", "Papa"]
TRAITS = ["gentle", "shy", "curious", "kind", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, g, c) for p in PLACES for g in GIFTS for c in COMFORTS if reasonableness(PLACES[p], GIFTS[g], COMFORTS[c])]


def reasonableness(place: Place, gift: Gift, comfort: Comfort) -> bool:
    if place.id == "kitchen":
        return True
    if place.id == "porch":
        return gift.id == "peach_bowl" and comfort.id in {"pompom_hat", "lantern", "handhold"}
    if place.id == "path":
        return gift.id == "peach_bowl" and comfort.id in {"lantern", "handhold"}
    return False


ASP_RULES = r"""
valid(P,G,C) :- place(P), gift(G), comfort(C), safe_combo(P,G,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.outdoors:
            lines.append(asp.fact("outdoors", p.id))
        if p.safe:
            lines.append(asp.fact("safe_place", p.id))
    for g in GIFTS.values():
        lines.append(asp.fact("gift", g.id))
        for t in g.tastes:
            lines.append(asp.fact("taste", g.id, t))
    for c in COMFORTS.values():
        lines.append(asp.fact("comfort", c.id))
    for p, g, c in valid_combos():
        lines.append(asp.fact("safe_combo", p, g, c))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about bravery, pompom, peach, and hominy.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child")
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.gift is None or c[1] == args.gift)
              and (args.comfort is None or c[2] == args.comfort)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, gift, comfort = rng.choice(combos)
    child = args.child or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(place=place, child=child, parent=parent, gift=gift, comfort=comfort)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    gift = GIFTS[params.gift]
    comfort = COMFORTS[params.comfort]
    world = World(place)
    child = world.add(Entity(params.child, kind="character", label=params.child, type="girl" if params.child in {"Mina", "Maya", "Iris"} else "boy"))
    parent = world.add(Entity(params.parent, kind="character", label=params.parent, type="mother" if params.parent in {"Mom", "Auntie"} else "father"))
    present = world.add(Entity("gift", label=gift.label, type="gift", warm=True, fragile=True, owner=child.id))
    gear = world.add(Entity(comfort.id, label=comfort.label, type="comfort", owner=child.id))
    child.memes["love"] = 1
    child.memes["desire"] = 1
    child.memes["fear"] = 1 if place.id != "kitchen" else 0
    child.memes["bravery"] = 0
    parent.memes["care"] = 1
    world.facts.update(child=child, parent=parent, gift=present, comfort=gear, place=place, gift_cfg=gift, comfort_cfg=comfort)
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    gift_cfg: Gift = f["gift_cfg"]
    comfort_cfg: Comfort = f["comfort_cfg"]
    place: Place = f["place"]

    world.say(f"{child.id} had a {comfort_cfg.label} with a soft pompom on top, and it made {child.pronoun('object')} feel cozy.")
    world.say(f"On the table sat {gift_cfg.phrase}, sweet with peach and hominy, waiting for a little sharing.")
    world.para()
    if place.id == "kitchen":
        world.say(f"The kitchen was warm, but {child.id} still wanted to carry the bowl out to the porch so the neighbor could smell it too.")
    else:
        world.say(f"{child.id} and {parent.id} stepped toward {place.label}, where the breeze felt {place.breeze}.")
    world.say(f"{child.id} wanted to bring the bowl anyway, but {child.pronoun('possessive')} tummy fluttered at the thought of the dark path.")
    child.memes["fear"] += 1
    if place.id != "kitchen":
        world.say(f'"I can do it," {child.id} whispered, even though {child.pronoun("possessive")} knees felt wiggly.')
    world.para()
    child.memes["bravery"] += 1
    if comfort_cfg.id == "pompom_hat":
        world.say(f"{parent.id} smiled and adjusted the pompom hat. " 
                  f'"Bravery can be small," {parent.id} said. "You can take one careful step at a time."')
    elif comfort_cfg.id == "lantern":
        world.say(f"{parent.id} lifted the lantern, and a golden circle of light touched the path. " 
                  f'"Bravery is walking with light," {parent.id} said.')
    else:
        world.say(f"{parent.id} held {child.pronoun('possessive')} hand. " 
                  f'"Bravery is not being alone," {parent.id} said.')
    world.say(f"{child.id} took a breath, stood taller, and kept going.")
    world.para()
    child.meters["distance"] = 1
    if place.id == "path":
        world.say(f"The front path looked long, but {child.id} stepped over each shadow and did not stop.")
    elif place.id == "porch":
        world.say(f"The porch creaked a little, but the {comfort_cfg.label} and warm bowl made it feel safe enough.")
    else:
        world.say(f"{child.id} carried the bowl from the kitchen with both hands, careful not to spill a drop.")
    world.say(f"When they arrived, the neighbor's face lit up at the smell of peach hominy.")
    world.say(f"{child.id} set the bowl down with a proud little grin, and {parent.id} gave {child.pronoun('object')} a hug.")
    world.say(f"Together they ate peach slices on top of the hominy, and the evening felt warm all the way through.")
    world.say(f"It was a brave trip, and it ended with everyone smiling.")

    world.facts["happy_ending"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
    return [
        'Write a heartwarming story for a young child that includes pompom, peach, and hominy.',
        f"Tell a gentle story where {f['child'].id} is brave about carrying {f['gift_cfg'].phrase} outside.",
        f"Write a happy-ending story about a child with a {f['comfort_cfg'].label} helping someone with a warm meal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    gift_cfg: Gift = f["gift_cfg"]
    comfort_cfg: Comfort = f["comfort_cfg"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} want to carry to {place.label}?",
            answer=f"{child.id} wanted to carry {gift_cfg.phrase}, a warm bowl that mixed peach and hominy.",
        ),
        QAItem(
            question=f"Why did {child.id} need bravery on the way?",
            answer=f"{child.id} needed bravery because the path felt a little scary and {child.pronoun('possessive')} knees felt wiggly.",
        ),
        QAItem(
            question=f"How did {parent.id} help {child.id} feel brave?",
            answer=f"{parent.id} helped by showing {child.pronoun('object')} {comfort_cfg.help_text}. That made the trip feel safer.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the bowl delivered, peach hominy shared, and everyone smiling in a warm happy ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pompom?",
            answer="A pompom is a fluffy little ball, often tied onto a hat or scarf for a playful look.",
        ),
        QAItem(
            question="What is a peach?",
            answer="A peach is a soft, sweet fruit with fuzzy skin and a juicy inside.",
        ),
        QAItem(
            question="What is hominy?",
            answer="Hominy is soft cooked corn that can be eaten warm in a bowl or mixed into comforting food.",
        ),
    ]


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
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    out.append(f"  place={world.place.label}")
    return "\n".join(out)


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
    StoryParams(place="porch", child="Mina", parent="Mom", gift="peach_bowl", comfort="pompom_hat"),
    StoryParams(place="path", child="Theo", parent="Dad", gift="peach_bowl", comfort="lantern"),
    StoryParams(place="kitchen", child="Maya", parent="Auntie", gift="hominy_pot", comfort="handhold"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_asp_program(show: str) -> str:
    return asp_program(show)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_stories()
        print(f"{len(vals)} compatible combos:")
        for p, g, c in vals:
            print(f"  {p:7} {g:11} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
