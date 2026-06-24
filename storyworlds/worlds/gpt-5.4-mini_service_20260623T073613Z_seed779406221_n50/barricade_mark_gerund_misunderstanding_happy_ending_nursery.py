#!/usr/bin/env python3
"""
storyworlds/worlds/barricade_mark_gerund_misunderstanding_happy_ending_nursery.py
=================================================================================

A tiny nursery-rhyme storyworld about a child, a misunderstood mark, a little
barricade, and a happy ending.

Seed image:
---
A child leaves a mark on a note. A grown-up thinks it is a warning, then
realizes it is only a mark-gerund clue. A small barricade keeps a rolling toy
out of trouble, and everybody laughs at the mix-up.

This world keeps the prose child-facing and rhythmic, but the state machine is
still concrete:
- a mark appears on a note or sign,
- a misunderstanding starts when the mark is read the wrong way,
- a barricade protects a fragile or rolling thing,
- the mix-up clears,
- the ending image proves the change.

The world model tracks physical meters and emotional memes on typed entities.
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mark:
    id: str
    label: str
    phrase: str
    verb: str
    meaning: str
    on: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    rolling: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Barricade:
    id: str
    label: str
    phrase: str
    covers: set[str]
    protects: set[str]
    build: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.path_clear = True
        self.marked_on: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.path_clear = self.path_clear
        w.marked_on = self.marked_on
        return w


@dataclass
class StoryParams:
    place: str
    mark: str
    thing: str
    barricade: str
    child_name: str
    child_type: str
    adult_name: str
    adult_type: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"mark", "barricade"}),
    "hall": Setting(place="the hallway", affords={"mark", "barricade"}),
    "playroom": Setting(place="the playroom", affords={"mark", "barricade"}),
    "garden_gate": Setting(place="the garden gate", affords={"mark", "barricade"}),
}

MARKS = {
    "paint": Mark(
        id="paint",
        label="paint mark",
        phrase="a bright paint mark",
        verb="mark the note",
        meaning="a painty clue",
        on="the paper note",
        tags={"paint", "mark", "clue"},
    ),
    "smudge": Mark(
        id="smudge",
        label="smudge mark",
        phrase="a dark smudge mark",
        verb="mark the sign",
        meaning="a smudgy clue",
        on="the wooden sign",
        tags={"smudge", "mark", "clue"},
    ),
    "sticker": Mark(
        id="sticker",
        label="sticker mark",
        phrase="a round sticker mark",
        verb="mark the card",
        meaning="a sticker clue",
        on="the notice card",
        tags={"sticker", "mark", "clue"},
    ),
}

THINGS = {
    "ball": Thing(id="ball", label="ball", phrase="a red rolling ball", rolling=True, tags={"rolling"}),
    "egg": Thing(id="egg", label="egg", phrase="a tiny egg in a nest", fragile=True, tags={"fragile"}),
    "vase": Thing(id="vase", label="vase", phrase="a little blue vase", fragile=True, tags={"fragile"}),
}

BARRICADES = {
    "boxes": Barricade(
        id="boxes",
        label="box barricade",
        phrase="a little barricade of boxes",
        covers={"path"},
        protects={"rolling"},
        build="stack the boxes up low and neat",
        result="the ball stayed on the safe side",
        tags={"barricade", "boxes"},
    ),
    "pillow": Barricade(
        id="pillow",
        label="pillow barricade",
        phrase="a soft barricade of pillows",
        covers={"nest"},
        protects={"fragile"},
        build="pile the pillows up soft and slow",
        result="the egg stayed snug and still",
        tags={"barricade", "pillow"},
    ),
    "chairs": Barricade(
        id="chairs",
        label="chair barricade",
        phrase="a neat barricade of chairs",
        covers={"corner"},
        protects={"fragile", "rolling"},
        build="turn the chairs so they make a tiny wall",
        result="the thing behind them stayed quite safe",
        tags={"barricade", "chairs"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lila", "Pia", "Mira", "Tess"]
BOY_NAMES = ["Owen", "Finn", "Beau", "Leo", "Theo", "Max"]
ADULT_NAMES = ["Mama", "Papa", "Nan", "Grandpa"]
TRAITS = ["curious", "cheerful", "gentle", "spry", "bright"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid, mark in MARKS.items():
            for tid, thing in THINGS.items():
                for bid, barricade in BARRICADES.items():
                    if thing.rolling and "rolling" in barricade.protects:
                        out.append((place, mid, tid, bid))
                    elif thing.fragile and "fragile" in barricade.protects:
                        out.append((place, mid, tid, bid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: a mark, a misunderstanding, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mark", choices=MARKS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--barricade", choices=BARRICADES)
    ap.add_argument("--name")
    ap.add_argument("--adult")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father", "grandmother", "grandfather"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mark is None or c[1] == args.mark)
              and (args.thing is None or c[2] == args.thing)
              and (args.barricade is None or c[3] == args.barricade)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mark, thing, barricade = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult_type = args.adult_type or rng.choice(["mother", "father"])
    adult_name = args.adult or rng.choice(ADULT_NAMES)
    return StoryParams(place, mark, thing, barricade, child_name, child_type, adult_name, adult_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MARKS[params.mark], THINGS[params.thing], BARRICADES[params.barricade], params.child_name, params.child_type, params.adult_name, params.adult_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def ask_mark(world: World, mark: Mark) -> None:
    world.say(f"{mark.phrase} sat {mark.on} and looked like a little rhyme clue.")
    world.say(f"The child meant to {mark.verb}, but the grown-up first read it as a warning.")


def misunderstanding(world: World, child: Entity, adult: Entity, mark: Mark) -> None:
    adult.memes["worry"] = adult.memes.get("worry", 0.0) + 1
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1
    world.say(
        f"{adult.id} pointed and said, “Oh my, that {mark.label_word if hasattr(mark, 'label_word') else mark.label} looks serious!”"
        f" But {child.id} shook {child.pronoun('possessive')} head. "
        f"“No, no, {mark.meaning},” {child.id} sang."
    )


def build_barricade(world: World, child: Entity, barricade: Barricade, thing: Entity) -> None:
    world.path_clear = False
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    world.say(
        f"{child.id} {barricade.build}, and soon there was {barricade.phrase}."
    )
    world.say(f"It made a safe little stop for {thing.phrase}.")


def resolve_mixup(world: World, child: Entity, adult: Entity, mark: Mark, thing: Entity, barricade: Barricade) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    adult.memes["relief"] = adult.memes.get("relief", 0.0) + 1
    world.say(
        f"Then {adult.id} laughed and clapped. “Why, that mark was only a {mark.meaning}!”"
    )
    world.say(
        f"{child.id} smiled, and {thing.id} stayed safe behind the {barricade.label}."
    )


def ending_image(world: World, child: Entity, adult: Entity, thing: Entity, barricade: Barricade) -> None:
    world.say(
        f"At the end, {child.id} and {adult.id} stood by the {barricade.label}, "
        f"and {thing.phrase} was tucked up safe and sound."
    )
    world.say("The little mix-up was mended, and everyone went home to tea with a grin.")


def tell(setting: Setting, mark: Mark, thing_cfg: Thing, barricade_cfg: Barricade,
         child_name: str, child_type: str, adult_name: str, adult_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_type, label=adult_name))
    thing = world.add(Entity(id=thing_cfg.id, type=thing_cfg.label, label=thing_cfg.label, phrase=thing_cfg.phrase, plural=thing_cfg.rolling))
    world.add(Entity(id=mark.id, type="mark", label=mark.label, phrase=mark.phrase))
    ask_mark(world, mark)
    world.para()
    misunderstanding(world, child, adult, mark)
    world.para()
    build_barricade(world, child, barricade_cfg, thing)
    world.para()
    resolve_mixup(world, child, adult, mark, thing, barricade_cfg)
    world.para()
    ending_image(world, child, adult, thing, barricade_cfg)
    world.facts.update(child=child, adult=adult, thing=thing, mark=mark, barricade=barricade_cfg, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story for a child named {f["child"].id} about a mark on a note, a misunderstanding, and a happy ending.',
        f"Tell a gentle story where {f['child'].id} leaves a {f['mark'].label} and {f['adult'].id} first thinks it means trouble, but it turns out to be a clue.",
        f"Write a rhyme-like story where a small barricade keeps {f['thing'].phrase} safe after a simple mix-up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, mark, thing, barricade = f["child"], f["adult"], f["mark"], f["thing"], f["barricade"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id} and {adult.id}, who had a small mix-up and then fixed it together.",
        ),
        QAItem(
            question=f"What did {child.id} make that caused the misunderstanding?",
            answer=f"{child.id} made {mark.phrase}. {adult.id} first thought it meant trouble, but it was only a little clue mark.",
        ),
        QAItem(
            question=f"What did {child.id} build to keep {thing.phrase} safe?",
            answer=f"{child.id} built {barricade.phrase} so {thing.phrase} would stay safe and in place.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily. The mix-up was cleared up, the barricade did its job, and everyone smiled.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is a barricade?",
            answer="A barricade is a small barrier built to block a path or keep something safe.",
        ),
        QAItem(
            question="What is a mark?",
            answer="A mark is a sign, spot, or trace left on something.",
        ),
        QAItem(
            question="What should you do if someone misunderstands your note?",
            answer="You can explain kindly and show what you meant so everyone can understand.",
        ),
    ]


ASP_RULES = r"""
thing_kind(rolling, ball).
thing_kind(fragile, egg).
thing_kind(fragile, vase).

barricade_protects(boxes, rolling).
barricade_protects(pillow, fragile).
barricade_protects(chairs, rolling).
barricade_protects(chairs, fragile).

valid(Place, Mark, Thing, Barr) :- place(Place), mark(Mark), thing(Thing), barricade(Barr),
    thing_kind(K, Thing), barricade_protects(Barr, K).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for mid in MARKS:
        lines.append(asp.fact("mark", mid))
    for tid in THINGS:
        lines.append(asp.fact("thing", tid))
    for bid in BARRICADES:
        lines.append(asp.fact("barricade", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "paint", "ball", "boxes", "Mina", "girl", "Mama", "mother"),
    StoryParams("hall", "smudge", "egg", "pillow", "Owen", "boy", "Papa", "father"),
    StoryParams("playroom", "sticker", "vase", "chairs", "Lila", "girl", "Nan", "grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.asp:
        print(asp_program("#show valid/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        print(s.story)
        if args.trace and s.world:
            print(dump_trace(s.world))
        if args.qa:
            print()
            print(format_qa(s))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
