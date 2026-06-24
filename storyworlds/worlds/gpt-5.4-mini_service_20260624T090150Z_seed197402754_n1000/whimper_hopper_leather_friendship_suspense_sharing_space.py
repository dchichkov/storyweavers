#!/usr/bin/env python3
"""
A small space-adventure story world about friendship, suspense, and sharing space.

The seed words are woven into the domain:
- whimper: a tiny sound when a character gets nervous
- hopper: a little moon-hopping craft
- leather: a worn but trusted seat strap / glove material

The story premise:
A child astronaut and a friend ride a hopper to a quiet moon outpost.
A leather item becomes a source of tension when one friend wants to keep it,
but the other needs it to stay safe. They share it, calm down, and finish the trip
together.

This module follows the Storyweavers storyworld contract.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    name: str = "the moon base"
    place_detail: str = "the silver landing pad"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    suspense: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    risk: str
    protects: str
    wearable: bool = False
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
SETTINGS = {
    "moonbase": Setting(
        name="the moon base",
        place_detail="the silver landing pad",
        affords={"hopper"},
    ),
    "orbit": Setting(
        name="the quiet station orbiting Mars",
        place_detail="the docking ring",
        affords={"hopper"},
    ),
    "asteroid": Setting(
        name="the asteroid camp",
        place_detail="the bright tunnel gate",
        affords={"hopper"},
    ),
}

MISSIONS = {
    "hopper": Mission(
        id="hopper",
        verb="hop to the far relay",
        gerund="hopping between moon stones",
        rush="hurry into the hopper",
        keyword="hopper",
        suspense="a tiny whimper of worry",
        tags={"space", "travel", "suspense"},
    ),
}

ITEMS = {
    "leather_strap": Item(
        id="leather_strap",
        label="leather strap",
        phrase="a soft leather strap",
        risk="could snap loose in a jolt",
        protects="keeps a pack steady",
        wearable=False,
    ),
    "leather_gloves": Item(
        id="leather_gloves",
        label="leather gloves",
        phrase="a pair of leather gloves",
        risk="could make a climb safer",
        protects="keep hands warm and steady",
        wearable=True,
        plural=True,
    ),
    "seat_belt": Item(
        id="seat_belt",
        label="seat belt",
        phrase="a snug seat belt with a leather patch",
        risk="could leave someone unsteady",
        protects="keeps a rider safe",
        wearable=True,
    ),
}

CHARACTER_NAMES = ["Nova", "Milo", "Iris", "Juno", "Tala", "Pip"]
CHARACTER_TYPES = ["girl", "boy"]
TRAITS = ["brave", "gentle", "curious", "careful", "friendly"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def item_at_risk(mission: Mission, item: Item) -> bool:
    return mission.id == "hopper" and item.id in {"leather_strap", "leather_gloves", "seat_belt"}


def select_sharing_item(mission: Mission, item: Item) -> Optional[Item]:
    if mission.id != "hopper":
        return None
    return item


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for mission_id, mission in MISSIONS.items():
            for item_id, item in ITEMS.items():
                if item_at_risk(mission, item):
                    combos.append((place, mission_id, item_id))
    return combos


def explain_rejection(mission: Mission, item: Item) -> str:
    return (
        f"(No story: the {mission.keyword} mission does not make sense with {item.label} "
        f"for this shared-space setup.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    mission = MISSIONS[params.mission]
    item = ITEMS[params.item]
    world = World(setting=setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"joy": 0.0},
        memes={"friendship": 0.0, "suspense": 0.0, "sharing": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_type,
        label=params.friend_name,
        meters={"joy": 0.0},
        memes={"friendship": 0.0, "suspense": 0.0, "sharing": 0.0},
    ))
    gear = world.add(Entity(
        id=item.id,
        kind="thing",
        type="gear",
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
        carried_by=hero.id,
        meters={"clean": 1.0},
    ))
    hopper = world.add(Entity(
        id="hopper",
        kind="thing",
        type="craft",
        label="hopper",
        phrase="a little moon-hopping craft",
        owner=hero.id,
        meters={"fuel": 1.0},
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        gear=gear,
        hopper=hopper,
        mission=mission,
        item=item,
        setting=setting,
        params=params,
    )

    # Act 1: setup
    world.say(f"{hero.id} and {friend.label} stood at {setting.place_detail} near the hopper.")
    world.say(
        f"They were ready for a {mission.keyword} mission, and {hero.id} loved the way the stars "
        f"looked like tiny pins on a dark blanket."
    )
    world.say(
        f"{hero.id} carried {item.phrase}, because {item.protects} and felt safe in the cold."
    )

    # Act 2: suspense builds
    world.para()
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"When the hatch blinked open, {friend.label} gave a little whimper and looked at the deep black space."
    )
    world.say(
        f"{hero.id} smiled and said they could go slowly. That made the air feel less heavy."
    )

    # Conflicting need over the item
    world.para()
    hero.memes["suspense"] += 1
    friend.memes["suspense"] += 1
    world.say(
        f"But when it was time to climb in, both children reached for {item.label} at once."
    )
    world.say(
        f"{friend.label} wanted to hold it tight, yet {hero.id} needed it for the ride, and that made the moment tense."
    )

    # Resolution through sharing
    world.para()
    world.say(
        f"{hero.id} took a breath and suggested sharing space: one would wear it first, then pass it over after launch."
    )
    world.say(
        f"{friend.label} nodded, and the hopper hummed softly as they traded places without fighting."
    )
    world.say(
        f"Together they flew past the moon ridge, and the shared {item.label} stayed useful the whole trip."
    )

    hero.memes["sharing"] += 2
    friend.memes["sharing"] += 2
    hero.memes["suspense"] = 0.0
    friend.memes["suspense"] = 0.0
    hero.meters["joy"] += 1
    friend.meters["joy"] += 1
    hopper.meters["fuel"] -= 0.2

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mission: str
    item: str
    name: str
    gender: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA and prose helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    mission = f["mission"]
    item = f["item"]
    return [
        f'Write a short space-adventure story for a young child about friendship, suspense, and sharing using the word "{mission.keyword}".',
        f"Tell a gentle story where {p.name} and {p.friend_name} go to {f['setting'].name} and have to share {item.label} on a hopper ride.",
        f'Write a child-friendly story that includes a small whimper, a hopper, and a leather item, then ends with the friends smiling together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    mission = f["mission"]
    item = f["item"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        QAItem(
            question=f"Who went on the mission with {p.name}?",
            answer=f"{p.name} went with {p.friend_name}, and they traveled together as friends.",
        ),
        QAItem(
            question=f"What did {p.name} and {p.friend_name} need to share?",
            answer=f"They needed to share {item.phrase} so the hopper trip could stay safe and calm.",
        ),
        QAItem(
            question=f"What sound showed that the trip felt a little scary at first?",
            answer="There was a tiny whimper, which showed that the space trip felt scary for a moment.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.label}?",
            answer=f"They ended the story smiling together, because they shared space and worked as friends.",
        ),
        QAItem(
            question=f"Why was the hopper ride tense before the friends shared?",
            answer=(
                f"It was tense because both children reached for {item.label} at once, and they had to decide "
                f"who would use it first on the {mission.keyword} mission."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "space": [
        QAItem(
            question="What is space?",
            answer="Space is the huge area beyond Earth where stars, planets, and moons are found.",
        )
    ],
    "hopper": [
        QAItem(
            question="What is a hopper in a space story?",
            answer="A hopper is a small craft that can move from one place to another, like hopping across a moon.",
        )
    ],
    "leather": [
        QAItem(
            question="What is leather?",
            answer="Leather is a tough material made from animal skin, and people use it for straps, gloves, and shoes.",
        )
    ],
    "sharing": [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too, instead of keeping it all to yourself.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other and help each other.",
        )
    ],
    "suspense": [
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of nervous waiting when you are not sure what will happen next.",
        )
    ],
    "whimper": [
        QAItem(
            question="What is a whimper?",
            answer="A whimper is a small, quiet sound someone makes when they feel worried, sad, or afraid.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["space"])
    out.extend(WORLD_KNOWLEDGE["hopper"])
    out.extend(WORLD_KNOWLEDGE["leather"])
    out.extend(WORLD_KNOWLEDGE["sharing"])
    out.extend(WORLD_KNOWLEDGE["friendship"])
    out.extend(WORLD_KNOWLEDGE["suspense"])
    out.extend(WORLD_KNOWLEDGE["whimper"])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: type={e.type}, kind={e.kind}, meters={dict(e.meters)}, memes={dict(e.memes)}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
mission(M) :- task(M).
item(I) :- gear(I).

compatible(P,M,I) :- place(P), mission(M), item(I), mission_keyword(M,"hopper"), item_kind(I,"leather").

safe_share(P,M,I) :- compatible(P,M,I).
#show compatible/3.
#show safe_share/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("task", mid))
        lines.append(asp.fact("mission_keyword", mid, m.keyword))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("gear", iid))
        lines.append(asp.fact("item_kind", iid, "leather" if "leather" in item.phrase or item.id.startswith("leather") else "other"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about friendship and sharing.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mission", choices=MISSIONS.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=CHARACTER_TYPES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=CHARACTER_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.mission and args.item:
        mission = MISSIONS[args.mission]
        item = ITEMS[args.item]
        if not item_at_risk(mission, item):
            raise StoryError(explain_rejection(mission, item))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mission_id, item_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHARACTER_NAMES)
    gender = args.gender or rng.choice(CHARACTER_TYPES)
    friend_name = args.friend_name or rng.choice([n for n in CHARACTER_NAMES if n != name])
    friend_type = args.friend_type or rng.choice(CHARACTER_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mission=mission_id,
        item=item_id,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(
        place="moonbase",
        mission="hopper",
        item="leather_strap",
        name="Nova",
        gender="girl",
        friend_name="Pip",
        friend_type="boy",
        trait="curious",
    ),
    StoryParams(
        place="orbit",
        mission="hopper",
        item="leather_gloves",
        name="Milo",
        gender="boy",
        friend_name="Iris",
        friend_type="girl",
        trait="friendly",
    ),
    StoryParams(
        place="asteroid",
        mission="hopper",
        item="seat_belt",
        name="Tala",
        gender="girl",
        friend_name="Juno",
        friend_type="boy",
        trait="careful",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3.\n#show safe_share/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
