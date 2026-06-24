#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T084545Z_seed1746935730_n100/keeper_surprise_sharing_bravery_bedtime_story.py
=========================================================================================================================

A small bedtime-story world about a keeper, a surprise, sharing, and bravery.

The core tale:
- A sleepy child keeps a little bedtime light safe.
- A surprise appears near bedtime and makes the child uneasy.
- The child must show bravery to face the dark.
- Sharing the surprise with a loved one turns worry into comfort.
- The ending proves the change with a peaceful bedtime image.

This file follows the Storyweavers world contract:
- stdlib-only prose engine
- shared results import eagerly
- ASP helper imported lazily
- typed entities with meters and memes
- reasonableness gate + inline ASP twin
- CLI supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    holds: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = True
    dark: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    gentle: bool = True
    hidden: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    kind: str
    size: str
    safe: bool = True
    shared: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.darkness: float = 0.0
        self.held_surprise: Optional[str] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w.darkness = self.darkness
        w.held_surprise = self.held_surprise
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    parent: str
    surprise: str
    comfort: str
    seed: Optional[int] = None


PLACES = {
    "nursery": Place(id="nursery", label="the nursery", cozy=True, dark=True, affords={"bedtime", "sharing"}),
    "bedroom": Place(id="bedroom", label="the bedroom", cozy=True, dark=True, affords={"bedtime", "sharing"}),
    "hall": Place(id="hall", label="the hallway", cozy=False, dark=True, affords={"bedtime"}),
}

SURPRISES = {
    "nightlight": Surprise(
        id="nightlight",
        label="a tiny star-shaped nightlight",
        phrase="a tiny star-shaped nightlight",
        kind="light",
        size="small",
        safe=True,
        tags={"light", "surprise"},
    ),
    "book": Surprise(
        id="book",
        label="a new picture book",
        phrase="a new picture book with shiny pages",
        kind="book",
        size="small",
        safe=True,
        tags={"book", "sharing", "surprise"},
    ),
    "plushie": Surprise(
        id="plushie",
        label="a soft sleep plushie",
        phrase="a soft sleep plushie with kind eyes",
        kind="toy",
        size="small",
        safe=True,
        tags={"soft", "sharing", "surprise"},
    ),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket",
        label="a warm blanket",
        phrase="a warm blanket",
        helps={"cold", "fear"},
        prep="pull the blanket up together",
        tail="pulled the blanket up and snuggled close",
    ),
    "lamp": Comfort(
        id="lamp",
        label="a little lamp",
        phrase="a little lamp with a gentle glow",
        helps={"dark", "fear"},
        prep="turn on the little lamp",
        tail="turned on the little lamp and made the room glow softly",
    ),
    "story": Comfort(
        id="story",
        label="a bedtime story",
        phrase="a bedtime story",
        helps={"fear", "worry"},
        prep="share a bedtime story",
        tail="read the story in soft voices until the room felt safe",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Maya"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Noah", "Ben"]


def reasonableness_gate(place: Place, surprise: Surprise, comfort: Comfort) -> bool:
    return place.dark and surprise.safe and "fear" in comfort.helps


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for sid, s in SURPRISES.items():
            for cid, c in COMFORTS.items():
                if reasonableness_gate(p, s, c):
                    out.append((pid, sid, cid))
    return out


def setting_detail(place: Place, surprise: Surprise) -> str:
    if place.id == "nursery":
        return "The nursery was sleepy and soft, with moonlight on the wall."
    if place.id == "bedroom":
        return "The bedroom waited in hush, with a pillow hill and a quiet quilt."
    return f"{place.label.capitalize()} was dim and echoey, which made bedtime feel a little bigger."
    # surprise may not change line; still world-driven by place and darkness


def predict_worry(world: World, hero: Entity, surprise: Surprise) -> bool:
    sim = world.copy()
    sim.darkness += 1.0
    hero_sim = sim.get(hero.id)
    hero_sim.memes["worry"] = hero_sim.memes.get("worry", 0.0) + 1.0
    return sim.darkness >= THRESHOLD and surprise.safe


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who liked soft pillows, warm covers, and the last story before sleep.")


def bedtime_setup(world: World, hero: Entity, parent: Entity, surprise: Surprise) -> None:
    world.say(
        f"One night, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.place.label}."
    )
    world.say(setting_detail(world.place, surprise))
    world.say(
        f"On the bedside table sat {surprise.phrase}, waiting like a quiet little secret."
    )
    world.facts["surprise_seen"] = surprise.id


def react(world: World, hero: Entity, surprise: Surprise) -> None:
    hero.memes["startle"] = hero.memes.get("startle", 0.0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{hero.id} blinked at the surprise. For a moment, the room felt too dark and too still."
    )


def brave(world: World, hero: Entity, parent: Entity, surprise: Surprise) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.say(
        f"{hero.id} took a slow breath and stood a little taller. "
        f"That was brave, even if {hero.pronoun()} still felt a tingle of worry."
    )


def share(world: World, hero: Entity, parent: Entity, surprise: Surprise, comfort: Comfort) -> None:
    surprise.shared = True
    world.held_surprise = surprise.id
    world.say(
        f"{hero.id} reached for {surprise.phrase} and shared the find with {hero.pronoun('possessive')} {parent.type}."
    )
    world.say(
        f'Together they said, "{comfort.prep}," and that made the secret feel like a gift instead of a shadow.'
    )


def resolve(world: World, hero: Entity, parent: Entity, surprise: Surprise, comfort: Comfort) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    world.say(
        f"Then {parent.id} {comfort.tail}. Soon {hero.id} was smiling again, and the surprise looked lovely instead of lonely."
    )
    world.say(
        f"{hero.id} curled up beside {hero.pronoun('possessive')} {parent.type}, brave enough for the dark and happy to share the night."
    )


def tell(place: Place, surprise: Surprise, comfort: Comfort, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent", meters={}, memes={}))
    world.add(Entity(id=surprise.id, type=surprise.kind, label=surprise.label, phrase=surprise.phrase))

    world.facts.update(hero=hero, parent=parent, surprise=surprise, comfort=comfort, place=place)

    introduce(world, hero)
    world.para()
    bedtime_setup(world, hero, parent, surprise)
    react(world, hero, surprise)
    brave(world, hero, parent, surprise)
    share(world, hero, parent, surprise, comfort)
    world.para()
    resolve(world, hero, parent, surprise, comfort)

    world.facts["resolved"] = True
    world.facts["hero_memes"] = dict(hero.memes)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story for a small child that includes the word "keeper" and shows surprise, sharing, and bravery.',
        f"Tell a cozy story where {f['hero'].id} is a keeper of {f['surprise'].label} at bedtime and learns to share after feeling brave.",
        f'Write a bedtime story about a child, a surprise on the nightstand, and a brave choice that makes the room feel safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    surprise = f["surprise"]
    comfort = f["comfort"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about at {place.label}?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {parent.id}, who helps at bedtime.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find before sleep?",
            answer=f"{hero.id} found {surprise.phrase} waiting near the bed.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery when the room felt dark?",
            answer=f"{hero.id} took a slow breath, stood tall, and kept going even while feeling a little worried.",
        ),
        QAItem(
            question=f"How did sharing help the bedtime surprise?",
            answer=f"{hero.id} shared the surprise with {parent.id}, and together they used {comfort.label} to make the moment feel cozy and safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} felt calm and happy, and the surprise became part of a peaceful bedtime.",
        ),
    ]


KNOWLEDGE = {
    "keeper": [
        ("What is a keeper?", "A keeper is someone who watches over something carefully and keeps it safe."),
    ],
    "surprise": [
        ("What is a surprise?", "A surprise is something you did not expect, so it can make you gasp or smile."),
    ],
    "sharing": [
        ("Why do people share?", "People share to be kind, to include others, and to make good things feel even happier."),
    ],
    "bravery": [
        ("What does bravery mean?", "Bravery means doing something even when you feel a little scared."),
    ],
    "nightlight": [
        ("What does a nightlight do?", "A nightlight gives a small, gentle light to help a room feel less dark."),
    ],
    "book": [
        ("Why are bedtime books nice?", "Bedtime books can help children calm down and feel sleepy and safe."),
    ],
    "blanket": [
        ("What does a blanket do at bedtime?", "A blanket keeps you warm and cozy while you rest."),
    ],
    "lamp": [
        ("Why use a little lamp at night?", "A little lamp gives a soft glow, which can make a dark room feel friendlier."),
    ],
}
KNOWLEDGE_ORDER = ["keeper", "surprise", "sharing", "bravery", "nightlight", "book", "blanket", "lamp"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["surprise"].tags)
    tags.add(world.facts["comfort"].id)
    tags.add("keeper")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  darkness={world.darkness}")
    lines.append(f"  held_surprise={world.held_surprise}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- dark(P).
surprise_ok(S) :- safe(S).
comfort_ok(C) :- helps(C, fear).

valid_story(P,S,C) :- place_ok(P), surprise_ok(S), comfort_ok(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        if s.safe:
            lines.append(asp.fact("safe", sid))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for h in sorted(c.helps):
            lines.append(asp.fact("helps", cid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle bedtime story world about keeper, surprise, sharing, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              and (args.surprise is None or c[1] == args.surprise)
              and (args.comfort is None or c[2] == args.comfort)]
    if not combos:
        raise StoryError("(No valid bedtime story matches the given options.)")
    place, surprise, comfort = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, hero=hero, hero_type=hero_type, parent=parent, surprise=surprise, comfort=comfort)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        SURPRISES[params.surprise],
        COMFORTS[params.comfort],
        params.hero,
        params.hero_type,
        params.parent,
    )
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible bedtime-story combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place, surprise, comfort in valid_combos():
            params = StoryParams(
                place=place,
                hero="Mina",
                hero_type="girl",
                parent="mother",
                surprise=surprise,
                comfort=comfort,
            )
            samples.append(generate(params))
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
