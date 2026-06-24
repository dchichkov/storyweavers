#!/usr/bin/env python3
"""
storyworlds/worlds/antler_satellite_kindness_fairy_tale.py
===========================================================

A small fairy-tale storyworld about an antler, a satellite, and kindness.

Seed tale:
---
A little deer found a fallen antler in the moss and wished to hang it high like
a bright star. Nearby, a tiny satellite had drifted down into the forest after
losing its path in the sky. The deer wanted the antler to point the way home,
but the satellite was lonely and afraid. The deer chose kindness: it shared the
antler as a signpost, cared for the satellite, and helped it shine again. In
the end, the forest glowed softly, and both friends found where they belonged.

This script turns that premise into a state-driven story:
- a forest setting
- a deer hero and a satellite friend
- an at-risk antler that may be lost or used
- kindness as the turning force that repairs the satellite and resolves the tale

The world contract requires:
- typed entities with physical meters and emotional memes
- explicit invalid combinations raising StoryError
- inline ASP twin + Python reasonableness gate
- story, prompts, story_qa, world_qa, trace, json, verify, show-asp
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
    location: str = ""
    can_shine: bool = False
    can_carry: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"deer", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moonlit forest"
    mossy: bool = True
    affords: set[str] = field(default_factory=lambda: {"carry", "shine"})


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False
    sacred: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    satellite_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = _copy.deepcopy(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "forest": Setting(place="the moonlit forest", mossy=True, affords={"carry", "shine"}),
    "grove": Setting(place="the quiet grove", mossy=True, affords={"carry", "shine"}),
}

HEROES = {
    "deer": {"type": "deer", "label": "little deer"},
}

SATELLITES = {
    "silver": Thing(id="silver", label="silver satellite", phrase="a small silver satellite", region="sky", fragile=True),
    "starling": Thing(id="starling", label="star satellite", phrase="a tiny star-shaped satellite", region="sky", fragile=True),
}

ANTLERS = {
    "fallen": Thing(id="fallen", label="fallen antler", phrase="a fallen antler with a smooth curve", region="ground", sacred=True),
    "bright": Thing(id="bright", label="bright antler", phrase="a bright antler polished by rain", region="ground", sacred=True),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A tale is reasonable when it contains a hero, a fallen antler, and a
% satellite that can be helped by kindness.
reasonable_story(H, A, S) :- hero(H), antler(A), satellite(S), kind(H, kind_deed).

% A kindness fix exists when the hero can carry the antler and can shine the
% satellite back to safety.
kind_fix(H, A, S) :- hero(H), antler(A), satellite(S),
                     can_carry(H), can_shine(S), kind(H, kind_deed).

valid_story(H, A, S) :- reasonable_story(H, A, S), kind_fix(H, A, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.mossy:
            lines.append(asp.fact("mossy", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for hid, hero in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("type_of", hid, hero["type"]))
    for aid, antler in ANTLERS.items():
        lines.append(asp.fact("antler", aid))
        if antler.sacred:
            lines.append(asp.fact("sacred", aid))
    for sid, sat in SATELLITES.items():
        lines.append(asp.fact("satellite", sid))
        if sat.fragile:
            lines.append(asp.fact("fragile", sid))
        lines.append(asp.fact("can_shine", sid))
    lines.append(asp.fact("can_carry", "deer"))
    lines.append(asp.fact("kind", "deer", "kind_deed"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, antler_id: str, satellite_id: str) -> bool:
    return (
        place in SETTINGS
        and antler_id in ANTLERS
        and satellite_id in SATELLITES
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for a in ANTLERS:
            for s in SATELLITES:
                if valid_combo(place, a, s):
                    combos.append((place, a, s))
    return combos


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label="little deer"))
    sat_cfg = next(v for v in SATELLITES.values() if v.id == "silver" if params.satellite_name == "silver") if False else None
    return world


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label="little deer",
        meters={"kindness": 0.0, "worry": 0.0, "hope": 0.0},
        memes={"kindness": 0.0, "loneliness": 0.0, "joy": 0.0},
    ))
    sat_cfg = SATELLITES[params.satellite_name]
    satellite = world.add(Entity(
        id="satellite",
        kind="thing",
        type="satellite",
        label=sat_cfg.label,
        phrase=sat_cfg.phrase,
        location="moss",
        can_shine=True,
        meters={"dull": 1.0, "lost": 1.0},
        memes={"loneliness": 1.0, "fear": 1.0},
    ))
    antler_cfg = ANTLERS["fallen"]
    antler = world.add(Entity(
        id="antler",
        kind="thing",
        type="antler",
        label=antler_cfg.label,
        phrase=antler_cfg.phrase,
        location="moss",
        can_carry=True,
        meters={"resting": 1.0},
        memes={"value": 1.0},
    ))

    world.say(f"In {world.setting.place}, {hero.label} found {antler.phrase}.")
    world.say(f"Nearby, {satellite.phrase} had drifted down and looked lonely.")

    world.para()
    hero.memes["kindness"] += 1
    hero.meters["kindness"] += 1
    world.say(f"{hero.pronoun().capitalize()} did not hoard the antler for itself.")
    world.say(f"Instead, {hero.pronoun()} lifted {antler.label} like a little sign and shared the path.")

    world.para()
    satellite.memes["fear"] = 0.0
    satellite.memes["loneliness"] = 0.0
    satellite.meters["dull"] = 0.0
    satellite.meters["lit"] = 1.0
    world.say(f"The satellite felt the kindness and began to glow again.")
    world.say(f"With the antler as a guide, it found the sky path home.")

    world.para()
    hero.memes["joy"] += 1
    hero.meters["hope"] += 1
    world.say(f"By dawn, the forest was soft with light, and {hero.label} was smiling under the trees.")
    world.say(f"{satellite.label} shone above, no longer lost, while the antler rested where everyone could see it.")

    world.facts.update(hero=hero, satellite=satellite, antler=antler)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    return [
        'Write a short fairy tale about a deer, a fallen antler, and a lost satellite, with kindness as the turning point.',
        f"Tell a gentle story in {world.setting.place} where a deer shares a fallen antler to help a satellite go home.",
        "Write a child-friendly fairy tale where kindness lights the way back to the sky.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    satellite = world.facts["satellite"]
    antler = world.facts["antler"]
    return [
        QAItem(
            question=f"What did {hero.id} find in the forest?",
            answer=f"{hero.label.capitalize()} found {antler.phrase} in the moss.",
        ),
        QAItem(
            question="What was wrong with the satellite?",
            answer=f"It had drifted down from the sky, and it felt lonely, scared, and a little dull.",
        ),
        QAItem(
            question="What did the deer choose to do?",
            answer="The deer chose kindness. It shared the antler as a signpost and helped the satellite shine again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an antler?",
            answer="An antler is a hard, branched horn that grows on some animals, like deer, and they can shed it and grow a new one later.",
        ),
        QAItem(
            question="What is a satellite?",
            answer="A satellite is a machine that goes around a planet in space and can help send signals or take pictures.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to be gentle, helpful, and caring toward someone else.",
        ),
    ]


# ---------------------------------------------------------------------------
# Generation / emit / CLI
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        for label, items in (("prompts", sample.prompts),):
            print(f"== {label} ==")
            for p in items:
                print(p)
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about an antler, a satellite, and kindness.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--satellite", choices=SATELLITES.keys())
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
    place = args.place or rng.choice(list(SETTINGS))
    satellite_name = args.satellite or rng.choice(list(SATELLITES))
    hero_name = args.name or rng.choice(["Elin", "Rowan", "Mira", "Tobin", "Nia", "Pip"])
    return StoryParams(place=place, hero_name=hero_name, hero_type="deer", satellite_name=satellite_name)


def asp_verify() -> int:
    python_set = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(python_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("python-only:", sorted(python_set - asp_set))
    print("asp-only:", sorted(asp_set - python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for sat in SATELLITES:
                params = StoryParams(place=place, hero_name="Elin", hero_type="deer", satellite_name=sat)
                samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
