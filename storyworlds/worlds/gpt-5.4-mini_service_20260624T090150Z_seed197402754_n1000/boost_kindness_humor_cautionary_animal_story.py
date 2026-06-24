#!/usr/bin/env python3
"""
storyworlds/worlds/boost_kindness_humor_cautionary_animal_story.py
==================================================================

A small animal-story world about kindness, humor, and caution.

Seed tale:
---
A little rabbit named Pip wanted to reach a sweet berry bush beyond a narrow creek.
Pip tried hopping onto a wobbly log to cross, but the log slipped and made a splash.
A helpful turtle named Tessa laughed kindly, then offered a sturdy boost with a rock, so Pip could climb up safely.
Pip took the careful route, crossed without falling, and shared the berries with Tessa.

World model:
---
Animals have meters and memes.
Physical meters track balance, splash, height, berries, and safety.
Emotional memes track worry, kindness, humor, and relief.
The story turns when a risky shortcut is replaced by a safer boosted climb.

This script keeps the premise small and classical: a desire, a mistake, a warning,
a kind fix, and a cheerful ending image.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "rabbit": {"subject": "it", "object": "it", "possessive": "its"},
            "turtle": {"subject": "it", "object": "it", "possessive": "its"},
            "fox": {"subject": "it", "object": "it", "possessive": "its"},
            "deer": {"subject": "it", "object": "it", "possessive": "its"},
            "bird": {"subject": "it", "object": "it", "possessive": "its"},
            "cat": {"subject": "it", "object": "it", "possessive": "its"},
            "dog": {"subject": "it", "object": "it", "possessive": "its"},
        }
        return mapping.get(self.type, mapping["rabbit"])[case]


@dataclass
class Setting:
    name: str = "the creek"
    description: str = "a narrow creek with a berry bush on the far bank"
    affords: set[str] = field(default_factory=set)


@dataclass
class Boost:
    id: str
    label: str
    place: str
    support: str
    careful: bool = True


@dataclass
class Hazard:
    id: str
    label: str
    risk: str
    splash: str
    warning: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    hazard: str
    name: str
    seed: Optional[int] = None


SETTINGS = {
    "creek": Setting(name="the creek", description="a narrow creek with a berry bush on the far bank", affords={"cross"}),
    "hill": Setting(name="the hill", description="a grassy hill with a juicy apple tree nearby", affords={"climb"}),
    "pond": Setting(name="the pond", description="a pond with reeds and a floating lily pad", affords={"cross"}),
}

ANIMALS = {
    "rabbit": {"name": "rabbit", "traits": ["small", "quick"]},
    "turtle": {"name": "turtle", "traits": ["slow", "steady"]},
    "fox": {"name": "fox", "traits": ["bright-eyed", "clever"]},
    "deer": {"name": "deer", "traits": ["gentle", "nimble"]},
    "bird": {"name": "bird", "traits": ["tiny", "cheerful"]},
    "cat": {"name": "cat", "traits": ["soft-footed", "curious"]},
}

BOOSTS = {
    "rock": Boost(id="rock", label="a smooth rock", place="beside the water", support="stand on", careful=True),
    "log": Boost(id="log", label="a sturdy log", place="near the creek", support="step onto", careful=True),
    "stump": Boost(id="stump", label="a little stump", place="by the path", support="climb onto", careful=True),
}

HAZARDS = {
    "splash": Hazard(id="splash", label="a slippery log", risk="slip", splash="splashed", warning="might slip"),
    "mud": Hazard(id="mud", label="a muddy bank", risk="slide", splash="sank", warning="might sink"),
    "drop": Hazard(id="drop", label="a wobbly edge", risk="fall", splash="tumbled", warning="might fall"),
}

NAMES = ["Pip", "Milo", "Nia", "Luna", "Benny", "Tara", "Kiki", "Ollie"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about kindness, humor, and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(ANIMALS))
    helper = args.helper or rng.choice([a for a in ANIMALS if a != hero])
    hazard = args.hazard or rng.choice(list(HAZARDS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, hero=hero, helper=helper, hazard=hazard, name=name)


def _boost_for_place(place: str) -> Boost:
    return BOOSTS["rock"] if place == "creek" else BOOSTS["stump"]


def _hazard_for_place(place: str) -> Hazard:
    return HAZARDS["splash"] if place == "creek" else HAZARDS["drop"]


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero, label=params.name, traits=ANIMALS[params.hero]["traits"]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=ANIMALS[params.helper]["name"], traits=ANIMALS[params.helper]["traits"]))
    boost = world.add(Entity(id="boost", kind="thing", type="boost", label=_boost_for_place(params.place).label))
    hazard = world.add(Entity(id="hazard", kind="thing", type="hazard", label=_hazard_for_place(params.place).label))
    berry = world.add(Entity(id="berry", kind="thing", type="berry", label="a berry bunch"))

    world.facts.update(hero=hero, helper=helper, boost=boost, hazard=hazard, berry=berry, params=params)
    return world


def _risk_check(world: World) -> bool:
    hero = world.get("hero")
    hazard = world.get("hazard")
    return hero.meters.get("balance", 0.0) < THRESHOLD or hazard.label == "a slippery log"


def _do_attempt(world: World) -> None:
    hero = world.get("hero")
    hero.meters["balance"] = hero.meters.get("balance", 0.0) - 0.5
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.meters["splash"] = hero.meters.get("splash", 0.0) + 1.0


def _kind_help(world: World) -> None:
    helper = world.get("helper")
    hero = world.get("hero")
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    helper.memes["humor"] = helper.memes.get("humor", 0.0) + 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    hero.meters["balance"] = hero.meters.get("balance", 0.0) + 2.0


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    hero = world.get("hero")
    helper = world.get("helper")
    boost = world.get("boost")
    hazard = world.get("hazard")
    berry = world.get("berry")

    world.say(f"{hero.label} the {hero.type} lived near {world.setting.name}.")
    world.say(f"{hero.label} loved the sweet berries on the far side, but {hazard.label} was in the way.")

    world.para()
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(f"One day, {hero.label} hurried toward the berries and tried to cross the risky way.")
    if _risk_check(world):
        _do_attempt(world)
        world.say(f"The {hazard.label} made {hero.label} slip, and there was a big splash.")
        world.say(f"{helper.label} saw the splash and gave a small laugh, not to tease, but because it looked so silly.")

    world.para()
    world.say(f"Then {helper.label} pointed to {boost.label} {BOOSTS['rock' if params.place == 'creek' else 'stump'].place}.")
    world.say(f'"{helper.label.capitalize()} said, "Take the careful boost. One steady step is better than one wobbly hop.""')
    _kind_help(world)

    world.para()
    world.say(f"{hero.label} climbed with the boost, kept {hero.pronoun('possessive')} feet steady, and reached the berries safely.")
    world.say(f"{hero.label} shared the berries with {helper.label}, and both animals sat down happily while the creek stayed calm.")

    world.facts["resolved"] = True
    world.facts["story"] = {
        "splash": hero.meters.get("splash", 0.0),
        "kindness": helper.memes.get("kindness", 0.0),
        "humor": helper.memes.get("humor", 0.0),
        "relief": hero.memes.get("relief", 0.0),
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    hero = world.get("hero")
    helper = world.get("helper")
    return [
        f'Write a short animal story for a young child that includes the word "boost".',
        f"Tell a gentle story where {hero.label} the {hero.type} wants the berries at {world.setting.name}, but a safer boost helps.",
        f"Write a cautionary animal story with kindness and humor: {hero.label} should avoid a wobble and choose the careful way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero = world.get("hero")
    helper = world.get("helper")
    return [
        QAItem(
            question=f"Who wanted the berries in this story?",
            answer=f"{hero.label} the {hero.type} wanted the berries across the way.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} helped by offering a careful boost and showing a safer way across.",
        ),
        QAItem(
            question=f"What happened when {hero.label} tried the risky way first?",
            answer=f"{hero.label} slipped and made a splash before choosing the safer boost.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.label} crossed safely, shared the berries, and sat happily with {helper.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a boost?", answer="A boost is a helpful lift or step that makes it easier to reach something safely."),
        QAItem(question="Why should animals be careful near slippery places?", answer="Slippery places can make feet slide, so careful steps help keep everyone safe."),
        QAItem(question="Why can kindness help in a problem?", answer="Kindness helps because a caring helper can make a hard moment feel safer and calmer."),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:6} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_wants_berries.
risky(H) :- hero_wants_berries, hazard(H).
kind_fix(B) :- boost(B).
safe_end :- kind_fix(B), boost(B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("place", key))
    for key in ANIMALS:
        lines.append(asp.fact("animal", key))
    for key in BOOSTS:
        lines.append(asp.fact("boost", key))
    for key in HAZARDS:
        lines.append(asp.fact("hazard", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show safe_end/0."))
    ok = any(sym.name == "safe_end" for sym in model)
    if ok:
        print("OK: ASP rules produce a safe ending.")
        return 0
    print("MISMATCH: ASP rules did not produce expected safe ending.")
    return 1


def build_sample(params: StoryParams) -> StorySample:
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


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def resolve_choices(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(list(ANIMALS)),
        helper=args.helper or rng.choice([k for k in ANIMALS if k != (args.hero or "")]),
        hazard=args.hazard or rng.choice(list(HAZARDS)),
        name=args.name or rng.choice(NAMES),
    )


CURATED = [
    StoryParams(place="creek", hero="rabbit", helper="turtle", hazard="splash", name="Pip"),
    StoryParams(place="hill", hero="deer", helper="fox", hazard="drop", name="Mira"),
    StoryParams(place="pond", hero="cat", helper="bird", hazard="mud", name="Momo"),
]


def build_asp_verify_program() -> str:
    return asp_program("#show safe_end/0.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(ASP_RULES)
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(build_asp_verify_program())
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.hero} with {p.helper} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
