#!/usr/bin/env python3
"""
storyworlds/worlds/initiative_turret_compliment_kindness_nursery_rhyme.py
========================================================================

A tiny nursery-rhyme storyworld about initiative, a turret, and a compliment.

Seed tale:
---
A little child felt shy at the castle yard. The child saw a lonely turret
watching the wind and wanted to help. The child took initiative, climbed a safe
stair, and brushed moss from the stone. Then the child gave the turret a warm
compliment for standing so tall and keeping watch. The castle keeper smiled,
because kindness made the whole yard feel bright.

This world simulates:
- a child making an initiative to do a helpful task,
- a turret that can be dusty, lonely, or proud,
- a compliment that raises the turret's cheer,
- kindness that turns the first shy feeling into a gentle ending.

The style is kept close to a nursery rhyme: soft rhythm, concrete images, and a
small repeating arc from concern to helpful action to happy result.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    feature: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    boosts: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _narrate_kindness(world: World, child: Entity, turret: Entity) -> None:
    child.memes["kindness"] += 1
    turret.memes["cheer"] += 1
    turret.memes["lonely"] = max(0.0, turret.memes.get("lonely", 0.0) - 1.0)
    world.say(
        f"{child.id} showed kindness with a small, steady hand, and the turret seemed less lonely."
    )


def _apply_initiative(world: World, child: Entity, act: Act) -> None:
    child.memes["initiative"] += 1
    child.meters[act.mess] = child.meters.get(act.mess, 0.0) + 1.0
    world.say(
        f"{child.id} took initiative and {act.verb}, light as a lark in the castle yard."
    )


def _apply_compliment(world: World, child: Entity, turret: Entity) -> None:
    child.memes["warmth"] += 1
    turret.memes["cheer"] = turret.memes.get("cheer", 0.0) + 1.0
    world.say(
        f"{child.id} gave the turret a compliment, saying it stood so tall and brave in the sun."
    )


def _apply_turn(world: World, child: Entity, turret: Entity) -> None:
    if child.memes.get("initiative", 0.0) >= THRESHOLD and child.meters.get("dust", 0.0) >= THRESHOLD:
        sig = ("turn", child.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        world.say(
            f"The dust began to lift, and the turret looked glad that someone had come to help."
        )


def _apply_resolution(world: World, child: Entity, turret: Entity) -> None:
    if child.memes.get("warmth", 0.0) >= THRESHOLD and turret.memes.get("cheer", 0.0) >= THRESHOLD:
        sig = ("resolve", child.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        world.say(
            f"Then the yard grew bright and kind, and {child.id} walked home with a happy heart."
        )


def propagate(world: World) -> None:
    child = next(e for e in world.characters() if e.type in {"girl", "boy"})
    turret = next(e for e in world.entities.values() if e.type == "turret")
    _apply_turn(world, child, turret)
    _apply_resolution(world, child, turret)


SETTINGS = {
    "castle_yard": Setting(place="the castle yard", feature="a small turret"),
    "stone_path": Setting(place="the stone path", feature="a round turret"),
    "garden_gate": Setting(place="the garden gate", feature="a high turret"),
}

ACTS = {
    "brush_dust": Act(
        id="brush_dust",
        verb="brushed the dust away",
        gerund="brushing dust",
        mess="dust",
        soil="a little dusty",
        risk="dusty stone",
        keyword="dust",
        tags={"dust", "turret"},
    ),
    "gather_flowers": Act(
        id="gather_flowers",
        verb="gathered little flowers",
        gerund="gathering flowers",
        mess="pollen",
        soil="soft with pollen",
        risk="pollen on stone",
        keyword="flowers",
        tags={"flowers", "kindness"},
    ),
    "carry_water": Act(
        id="carry_water",
        verb="carried a cup of water",
        gerund="carrying water",
        mess="drip",
        soil="a bit damp",
        risk="water drip on stone",
        keyword="water",
        tags={"water", "care"},
    ),
}

PRIZES = {
    "turret": Prize(label="turret", phrase="the old turret", type="turret"),
}

REMEDIES = {
    "compliment": Remedy(
        id="compliment",
        label="a warm compliment",
        prep="speak a gentle compliment to the turret",
        tail="said it stood brave and bright",
        boosts={"cheer": 1.0, "kindness": 1.0},
    ),
}

NAMES_GIRL = ["Mia", "Lily", "Nora", "Rose", "Ava", "Poppy"]
NAMES_BOY = ["Leo", "Finn", "Theo", "Max", "Ben", "Sam"]
TRAITS = ["tiny", "gentle", "cheery", "quiet", "spry"]


@dataclass
class StoryParams:
    setting: str
    act: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: initiative, turret, compliment, kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    act = args.act or rng.choice(list(ACTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, act=act, name=name, gender=gender, trait=trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.act not in ACTS:
        raise StoryError("Unknown act.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")


def tell(setting: Setting, act: Act, hero_name: str, gender: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=gender, memes={"kindness": 0.0, "initiative": 0.0, "warmth": 0.0}))
    keeper = world.add(Entity(id="Keeper", kind="character", type="mother", label="the keeper"))
    turret = world.add(Entity(id="Turret", type="turret", label="the turret", memes={"cheer": 0.0, "lonely": 1.0}))
    world.add(Entity(id="Compliment", type="compliment", label="compliment"))
    world.add(Entity(id="Kindness", type="kindness", label="kindness"))

    world.say(f"{hero_name} was a {trait} little {gender} who loved to help in {setting.place}.")
    world.say(f"There stood {setting.feature}, and the turret watched the breeze go by.")
    world.say(f"{hero_name} felt a spark of initiative and wished to do one small kind deed.")
    world.para()
    world.say(f"One day in {setting.place}, {hero_name} {act.verb} near the turret.")
    _apply_initiative(world, child, act)
    if act.id == "brush_dust":
        turret.meters["clean"] = turret.meters.get("clean", 0.0) + 1.0
        world.say(f"The little brush made the turret shine where the gray dust had been.")
    elif act.id == "gather_flowers":
        world.say(f"Little flowers nodded like bells, and the turret smelled sweet and fair.")
    else:
        world.say(f"A tiny cup of water flashed in the light, and the stones felt fresh again.")
    _narrate_kindness(world, child, turret)
    _apply_compliment(world, child, turret)
    world.para()
    world.say(f"{hero_name} looked up and said, 'Dear turret, you stand so tall and true.'")
    world.say(f"The turret seemed to smile, for a compliment is a warm little quilt.")
    propagate(world)
    world.say(f"{keeper.label if keeper.label else 'The keeper'} smiled too, because kindness had brightened the yard.")
    return world


def valid_combos() -> list[tuple[str, str]]:
    return sorted((s, a) for s in SETTINGS for a in ACTS)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
act(A) :- act_fact(A).
valid(S,A) :- setting(S), act(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for a in ACTS:
        lines.append(asp.fact("act_fact", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short nursery-rhyme story about {f['hero']} taking initiative near a turret and giving a compliment.",
        f"Tell a gentle story where kindness helps a child and a turret feel bright again.",
        f"Write a simple rhyme about a little helper, a castle turret, and a warm compliment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    act = f["act"]
    return [
        QAItem(
            question=f"What did {hero} do near the turret?",
            answer=f"{hero} took initiative and {act.verb}. That helpful choice made the turret feel less lonely.",
        ),
        QAItem(
            question=f"Why did the turret feel happier in the end?",
            answer="The child was kind, did the helpful job, and gave the turret a warm compliment.",
        ),
        QAItem(
            question=f"What kind of feeling was important in the story?",
            answer="Kindness was important. It helped turn a shy beginning into a bright ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a turret?",
            answer="A turret is a tall round tower, often part of a castle or strong old building.",
        ),
        QAItem(
            question="What is a compliment?",
            answer="A compliment is kind words that say something nice about a person or thing.",
        ),
        QAItem(
            question="What does initiative mean?",
            answer="Initiative means starting to do something helpful without being told first.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
    ]


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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(SETTINGS[params.setting], ACTS[params.act], params.name, params.gender, params.trait)
    world.facts = {"hero": params.name, "act": ACTS[params.act], "setting": SETTINGS[params.setting]}
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
    StoryParams(setting="castle_yard", act="brush_dust", name="Mia", gender="girl", trait="gentle"),
    StoryParams(setting="stone_path", act="gather_flowers", name="Leo", gender="boy", trait="cheery"),
    StoryParams(setting="garden_gate", act="carry_water", name="Nora", gender="girl", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, a in combos:
            print(f"  {s:12} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
