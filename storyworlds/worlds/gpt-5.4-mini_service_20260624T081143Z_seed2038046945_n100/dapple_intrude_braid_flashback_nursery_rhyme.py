#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/dapple_intrude_braid_flashback_nursery_rhyme.py
============================================================================================================================

A small storyworld in a nursery-rhyme style: a gentle creature keeps a braid neat,
a dappled visitor intrudes, and a flashback explains why the braid matters.

This world is intentionally compact and state-driven. The physical layer tracks
light, place, and braid condition; the emotional layer tracks worry, welcome,
and relief. Stories are generated from a short simulated sequence:
setup -> intrusion -> flashback -> repair -> ending image.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    worn_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    soft: bool = True
    dappled: bool = False
    allows_intrude: bool = True


@dataclass
class StoryParams:
    place: str = "nursery"
    hero: str = "Mimi"
    caretaker: str = "gran"
    visitor: str = "sparrow"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "nursery": Place(name="the nursery", soft=True, dappled=False, allows_intrude=True),
    "window": Place(name="the window nook", soft=True, dappled=True, allows_intrude=True),
    "garden": Place(name="the garden", soft=False, dappled=True, allows_intrude=True),
}

HEROES = ["Mimi", "Lulu", "Nina", "Tilly", "Poppy", "Polly", "Molly"]
VISITORS = ["sparrow", "ladybug", "moth", "bee", "kitten"]

KNOBS = {
    "dapple": "dappled light",
    "intrude": "intruded and startled the room",
    "braid": "braid",
    "flashback": "flashback",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- room(P).
dappled(P) :- place(P), has_light(P).
intrusion(V, P) :- visitor(V), place(P), allows_intrude(P).
needs_fix(P) :- braid_scene(P), intrusion(_, P).
resolved(P) :- needs_fix(P), ribbon(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("room", pid))
        if place.dappled:
            lines.append(asp.fact("has_light", pid))
        if place.allows_intrude:
            lines.append(asp.fact("allows_intrude", pid))
    for v in VISITORS:
        lines.append(asp.fact("visitor", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def nursery_flourish(hero: str, visitor: str) -> str:
    return (
        f"{hero} sat in the soft room, and dappled light danced like silver lace. "
        f"The little {visitor} felt lively enough to wander."
    )


def generate_flashback(world: World, hero: Entity, braid: Entity) -> str:
    world.facts["flashback"] = True
    hero.memes["remembering"] = hero.memes.get("remembering", 0.0) + 1
    braid.meters["tidy"] = braid.meters.get("tidy", 0.0) + 1
    return (
        f"Then came a flashback: last market day, {hero.id} had worn the braid "
        f"to look fine and fair, and {hero.pronoun('possessive')} gran had praised "
        f"it with tender care."
    )


def resolve(world: World, hero: Entity, caretaker: Entity, visitor: Entity, braid: Entity) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    braid.meters["tidy"] = braid.meters.get("tidy", 0.0) + 1
    world.say(
        f"So {caretaker.id} tied a bright ribbon and asked the {visitor.type} to stay "
        f"out of the braid. The dappled visitor bobbed politely, and the braid stayed neat."
    )
    world.say(
        f"{hero.id} smiled, the room grew calm, and the little light on the floor "
        f"looked like a warm, happy quilt."
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place for this storyworld.")
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero))
    caretaker = world.add(Entity(id=params.caretaker, kind="character", type="woman", label=params.caretaker))
    visitor = world.add(Entity(id=params.visitor, kind="character", type=params.visitor, label=params.visitor))
    braid = world.add(Entity(id="braid", kind="thing", type="braid", label="braid", owner=hero.id))

    braid.meters["tidy"] = 1.0
    hero.memes["calm"] = 1.0

    world.say(nursery_flourish(hero.id, visitor.type))
    world.say(f"{hero.id} kept a neat braid, and {caretaker.id} watched with a smile.")
    world.para()

    if place.allows_intrude:
        world.say(
            f"Without a knock, the {visitor.type} could intrude on the hush, flitting close "
            f"to the braid and making {hero.id} start."
        )
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        braid.meters["tidy"] = 0.0
    else:
        world.say(
            f"The {visitor.type} did not intrude there, and the braid stayed quiet as a mouse."
        )

    world.para()
    world.say(generate_flashback(world, hero, braid))
    world.say(
        f"That memory reminded {hero.id} why the braid mattered: it was part of a dear "
        f"little song of getting ready."
    )

    world.para()
    resolve(world, hero, caretaker, visitor, braid)

    world.facts.update(
        hero=hero,
        caretaker=caretaker,
        visitor=visitor,
        braid=braid,
        place=place,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme style story that includes "{KNOBS["dapple"]}" and "{KNOBS["braid"]}".',
        f"Tell a gentle story where a {f['visitor'].type} tries to intrude, then a flashback helps calm the scene.",
        f"Write a tiny story in which {f['hero'].id} keeps a braid neat in {f['place'].name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    caretaker: Entity = f["caretaker"]
    visitor: Entity = f["visitor"]
    place: Place = f["place"]
    braid: Entity = f["braid"]
    return [
        QAItem(
            question=f"Where did {hero.id} keep the braid?",
            answer=f"{hero.id} kept the braid in {place.name}, where the room was soft and quiet.",
        ),
        QAItem(
            question=f"Who tried to intrude on the calm little scene?",
            answer=f"The {visitor.type} intruded close to the braid and startled {hero.id} for a moment.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.id} of?",
            answer=f"It reminded {hero.id} that the braid had been carefully worn before, and {caretaker.id} had praised it with tender care.",
        ),
        QAItem(
            question=f"How did the story end for the braid?",
            answer=f"The braid stayed neat, and the room ended calm with {hero.id} smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dappled light?",
            answer="Dappled light is sunlight or lamplight that falls in little patches, like spots or soft pieces on the floor.",
        ),
        QAItem(
            question="What does intrude mean?",
            answer="To intrude means to come in where you are not wanted or to disturb a quiet moment.",
        ),
        QAItem(
            question="What is a braid?",
            answer="A braid is hair or string woven together in a neat, twisted line.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that remembers something from earlier time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    resolved = set(asp.atoms(model, "resolved"))
    if resolved == {("nursery",)} or resolved == {("window",)} or resolved == {("garden",)}:
        print("OK: ASP gate produced a resolved story shape.")
        return 0
    print("MISMATCH: ASP gate did not produce the expected resolution fact.")
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with dapple, intrude, braid, and flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--caretaker")
    ap.add_argument("--visitor", choices=VISITORS)
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(HEROES)
    caretaker = args.caretaker or "gran"
    visitor = args.visitor or rng.choice(VISITORS)
    return StoryParams(place=place, hero=hero, caretaker=caretaker, visitor=visitor)


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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place=p, hero=h, caretaker="gran", visitor=v))
                   for p in PLACES for h in HEROES[:2] for v in VISITORS[:2]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
