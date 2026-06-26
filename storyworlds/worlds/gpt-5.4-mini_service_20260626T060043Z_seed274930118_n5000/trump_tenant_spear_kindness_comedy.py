#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/trump_tenant_spear_kindness_comedy.py
===============================================================================================================

A small comedic storyworld about a tenant, a trumpet-like trump, and a spear,
where kindness turns an awkward mix-up into a funny happy ending.

The seed words are intentionally baked into the world:
- trump
- tenant
- spear

The story premise is simple:
A tenant wants to join a silly building talent show with a loud trump, but a
pointy spear prop threatens the fun. A kind choice turns the problem into a
gentle joke and leaves the room safer than before.

This script follows the Storyweavers contract:
- self-contained stdlib world script
- physical meters and emotional memes
- inline ASP twin
- reasonableness gate
- full CLI support and verification
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    place: str = "the hallway"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ItemDef:
    id: str
    label: str
    phrase: str
    mess: str
    risk: str
    response: str


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.room)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


ROOMS = {
    "hallway": Room(place="the hallway", indoors=True, affords={"trump", "spear"}),
    "lobby": Room(place="the lobby", indoors=True, affords={"trump", "spear"}),
    "courtyard": Room(place="the courtyard", indoors=False, affords={"trump", "spear"}),
}

ITEMS = {
    "trump": ItemDef(
        id="trump",
        label="trump",
        phrase="a shiny little trump",
        mess="noise",
        risk="noise",
        response="mute the trump with a cloth sock",
    ),
    "spear": ItemDef(
        id="spear",
        label="spear",
        phrase="a toy spear with a bright tip",
        mess="poke",
        risk="poke",
        response="wrap the spear in a foam sleeve",
    ),
}

NAMES = ["Mia", "Leo", "Noah", "Ava", "Zoe", "Ben", "Luna", "Max"]
TRAITS = ["cheerful", "curious", "silly", "kind", "bouncy"]


class ReasonableFix:
    def __init__(self, item_id: str, helper: str, cover: str, reduce_mess: str) -> None:
        self.item_id = item_id
        self.helper = helper
        self.cover = cover
        self.reduce_mess = reduce_mess


FIXES = {
    "trump": ReasonableFix("trump", "cloth sock", "mouthpiece", "noise"),
    "spear": ReasonableFix("spear", "foam sleeve", "tip", "poke"),
}


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, room in ROOMS.items():
        for item_id in room.affords:
            out.append((place, item_id))
    return out


def reasonableness_gate(place: str, item_id: str) -> bool:
    return (place, item_id) in valid_combos()


def _maybe_bad_choice(place: str, item_id: str) -> str:
    if not reasonableness_gate(place, item_id):
        return f"(No story: {item_id} does not fit {place} in this tiny comedy world.)"
    return ""


def ask_kinder(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.id} took a breath and chose kindness. "
        f"{hero.pronoun().capitalize()} did not laugh at the mess; {hero.pronoun()} fixed it."
    )


def tell(world: World, hero: Entity, tenant: Entity, item_def: ItemDef) -> World:
    item = world.add(Entity(id=item_def.id, type=item_def.id, label=item_def.label, phrase=item_def.phrase))
    hero.memes["delight"] = 1.0
    tenant.memes["worry"] = 1.0

    world.say(
        f"{hero.id} was a little {next(t for t in hero.memes.keys() if t == 'kindness' or True) and 'tenant'} "
        f"who lived in {world.room.place}."
    )
    world.say(
        f"{hero.id} loved the silly building talent show, especially the bright trump."
    )
    world.say(
        f"The {tenant.label} carried {item.phrase} for the show and nearly bonked a lamp."
    )

    world.para()
    world.say(
        f"One evening, {hero.id} and the {tenant.label} met in {world.room.place}."
    )
    world.say(
        f"{hero.id} wanted to use the trump, but the trump was so loud it made the neighbors blink."
    )
    world.say(
        f"Then the spear showed up as a prop, and its point made everyone step back a little."
    )

    item.meters[item_def.mess] = 1.0
    tenant.memes["embarrassment"] = 1.0
    hero.memes["surprise"] = 1.0
    world.facts["item"] = item_def.id
    world.facts["place"] = world.room.place

    world.para()
    fix = FIXES[item_def.id]
    world.say(
        f"{hero.id} smiled and offered a {fix.helper}."
    )
    world.say(
        f'That small kindness turned the problem into a joke: "{item_def.response}."'
    )
    world.say(
        f"With the {fix.helper} in place, the trump was softer, the spear was safe, "
        f"and the {tenant.label} could finish the show without trouble."
    )
    hero.memes["joy"] = 1.0
    tenant.memes["relief"] = 1.0
    item.meters["safe"] = 1.0
    world.facts["fix"] = fix.helper
    return world


def generation_prompts(world: World) -> list[str]:
    item = world.facts["item"]
    place = world.facts["place"]
    return [
        f"Write a short comedic story for children about a tenant, a trump, and a spear in {place}.",
        f"Tell a tiny story where kindness solves an awkward problem with a {item}.",
        "Write a funny, gentle story that ends with someone choosing kindness instead of scolding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    item = world.facts["item"]
    fix = world.facts["fix"]
    return [
        QAItem(
            question="Who helped make the problem smaller?",
            answer="The kind tenant helped make the problem smaller by choosing a gentle fix instead of getting mad.",
        ),
        QAItem(
            question=f"What item caused the awkward moment in the story?",
            answer=f"The {item} caused the awkward moment because it was either too loud or too pointy for the room.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with kindness, a safer setup, and a funny little performance that worked better after the {fix}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
        QAItem(
            question="What is a tenant?",
            answer="A tenant is a person who rents and lives in a home or room owned by someone else.",
        ),
        QAItem(
            question="What is a spear?",
            answer="A spear is a long stick with a sharp point at the end, often used as a tool or prop in stories.",
        ),
        QAItem(
            question="What is a trump in this world?",
            answer="A trump is a tiny brass instrument that can make a loud, bright sound.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(hallway). place(lobby). place(courtyard).
affords(hallway,trump). affords(hallway,spear).
affords(lobby,trump). affords(lobby,spear).
affords(courtyard,trump). affords(courtyard,spear).

fix(trump,sock).
fix(spear,foam).

valid(P,I) :- affords(P,I), fix(I,_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place, room in ROOMS.items():
        lines.append(asp.fact("place", place))
        for item in sorted(room.affords):
            lines.append(asp.fact("affords", place, item))
    for item_id, fix in FIXES.items():
        lines.append(asp.fact("fix", item_id, fix.helper))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedic tenant/trump/spear storyworld with kindness.")
    ap.add_argument("--place", choices=ROOMS.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, item=item, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    room = ROOMS[params.place]
    world = World(room)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    tenant = world.add(Entity(id="tenant", kind="character", type="tenant", label="tenant"))
    item_def = ITEMS[params.item]
    world = tell(world, hero, tenant, item_def)
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
    StoryParams(place="hallway", item="trump", name="Mia", gender="girl"),
    StoryParams(place="lobby", item="spear", name="Leo", gender="boy"),
    StoryParams(place="courtyard", item="trump", name="Ava", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, item) combos:")
        for p, i in triples:
            print(f"  {p:10} {i}")
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
            header = f"### {p.name}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
