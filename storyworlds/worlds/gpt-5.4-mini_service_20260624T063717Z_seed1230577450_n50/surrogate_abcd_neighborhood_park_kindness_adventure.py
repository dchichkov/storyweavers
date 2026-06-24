#!/usr/bin/env python3
"""
storyworlds/worlds/surrogate_abcd_neighborhood_park_kindness_adventure.py
=========================================================================

A small standalone storyworld for a neighborhood-park adventure about kindness,
with the seed words "surrogate" and "abcd" woven into the world as prompts and
story texture.

The premise:
- A child visits a neighborhood park with a special task.
- A friend makes a small problem during an adventure.
- Kindness, repair, and a surrogate helper turn the moment into a better ending.

The world model tracks:
- physical meters: distance walked, lost/found objects, carried items, park state
- emotional memes: worry, bravery, kindness, relief, trust

The prose is state-driven: the ending proves what changed in the world.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
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
class Setting:
    place: str = "the neighborhood park"


@dataclass
class Mission:
    id: str
    goal: str
    adventure_verb: str
    challenge: str
    kind_act: str
    keyword: str = ""


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    zone: str
    fixable_by: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "park": Setting(place="the neighborhood park"),
}

MISSIONS = {
    "abcd": Mission(
        id="abcd",
        goal="find the missing kite string",
        adventure_verb="dash after the kite",
        challenge="the string slips into the grass",
        kind_act="help",
        keyword="abcd",
    ),
    "surrogate": Mission(
        id="surrogate",
        goal="bring a spare ribbon to the sandbox tower",
        adventure_verb="race to the sandbox",
        challenge="the ribbon gets snagged on a bench",
        kind_act="share",
        keyword="surrogate",
    ),
}

ITEMS = {
    "kite_string": Item(
        id="kite_string",
        label="kite string",
        phrase="a bright kite string",
        type="string",
        zone="grass",
        fixable_by="help",
    ),
    "ribbon": Item(
        id="ribbon",
        label="ribbon",
        phrase="a soft blue ribbon",
        type="ribbon",
        zone="bench",
        fixable_by="share",
    ),
}

GIRL_NAMES = ["Mia", "Nina", "Ava", "Lily", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Max", "Noah", "Eli"]
TRAITS = ["brave", "kind", "curious", "cheerful"]


@dataclass
class StoryParams:
    place: str
    mission: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A neighborhood park kindness adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def valid_mission(mission: Mission) -> bool:
    return mission.id in MISSIONS


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("kind_act", mid, m.kind_act))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, M) :- setting(P), mission(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    mission_id = args.mission or rng.choice(list(MISSIONS))
    if mission_id not in MISSIONS:
        raise StoryError("Unknown mission.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["a surrogate friend", "a kind parent", "a park ranger"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=args.place or "park", mission=mission_id, name=name, gender=gender, helper=helper, trait=trait)


def scene(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper))
    mission = MISSIONS[params.mission]
    item = ITEMS["kite_string" if params.mission == "abcd" else "ribbon"]
    object_ent = world.add(Entity(id=item.id, kind="thing", type=item.type, label=item.label, phrase=item.phrase))
    world.facts.update(hero=hero, helper=helper, mission=mission, item=object_ent)

    world.say(f"{hero.id} was a {params.trait} child at {world.setting.place}, ready for an adventure.")
    world.say(f"On the path, {hero.pronoun('subject')} noticed {mission.keyword} written on a small sign by the gate, which felt like a secret clue.")
    world.para()
    world.say(f"{hero.id} wanted to {mission.adventure_verb}, but {mission.challenge}.")
    hero.memes["worry"] = 1
    hero.memes["bravery"] = 1
    world.say(f"{hero.pronoun().capitalize()} looked around and called for {params.helper}.")
    helper.memes["kindness"] = 1
    world.say(f"{helper.label_word if hasattr(helper, 'label_word') else helper.label} came with a surrogate fix: a spare loop of string and a gentle smile.")
    world.para()
    hero.memes["kindness"] = 1
    hero.meters["distance"] = 1
    object_ent.carried_by = hero.id
    world.say(f"Together they used kindness first, then the spare help, and soon {hero.id} could continue.")
    world.say(f"In the end, {hero.id} carried {object_ent.label} safely, and the neighborhood park felt like the best place for an adventure.")
    hero.memes["relief"] = 1
    hero.memes["trust"] = 1
    return world


def generate(params: StoryParams) -> StorySample:
    world = scene(World(SETTINGS[params.place]), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a short adventure story in a neighborhood park that includes the word "{MISSIONS[params.mission].keyword}".',
            f"Tell a child-facing story where {params.name} needs a surrogate helper and kindness solves a park problem.",
            f'Create a small, gentle adventure using the word "abcd" or "surrogate" and ending with a helpful finish.',
        ],
        story_qa=[
            QAItem(question=f"Where did {params.name} have the adventure?", answer="The adventure happened in the neighborhood park."),
            QAItem(question=f"What helped the problem get better?", answer="Kindness and a surrogate helper made the problem easier to solve."),
            QAItem(question=f"What did {params.name} carry at the end?", answer=f"{params.name} carried the {MISSIONS[params.mission].goal.split(' ', 1)[-1]} safely at the end."),
        ],
        world_qa=[
            QAItem(question="What is kindness?", answer="Kindness means helping, sharing, and being gentle with others."),
            QAItem(question="What is a surrogate helper?", answer="A surrogate helper is someone who steps in to help when extra support is needed."),
        ],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, dict(e.meters), dict(e.memes))
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {(p, m) for p in SETTINGS for m in MISSIONS}
    if atoms == py:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for m in MISSIONS:
            p = StoryParams(place="park", mission=m, name="Mia", gender="girl", helper="a surrogate friend", trait="kind", seed=base_seed)
            samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        out = samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)
        print(out)
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
