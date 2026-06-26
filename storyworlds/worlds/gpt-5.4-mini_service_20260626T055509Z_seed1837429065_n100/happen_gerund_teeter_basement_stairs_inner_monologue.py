#!/usr/bin/env python3
"""
A fairy-tale storyworld set on basement stairs, built from the seed words
"happen-gerund" and "teeter".

The world centers on a child, a fragile object, a cautious warning, and a
small mystery that gets solved through careful action rather than a big fix.
The prose uses inner monologue, a cautionary turn, and a final reveal image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    place: str = ""
    secure: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the basement stairs"
    shadowy: bool = True
    affords: set[str] = field(default_factory=lambda: {"teeter", "search", "descend"})


@dataclass
class Activity:
    id: str
    gerund: str
    happen_gerund: str
    risk: str
    clue: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool = True


@dataclass
class Tool:
    id: str
    label: str
    description: str
    solves: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "basement_stairs": Setting(),
}

ACTIVITIES = {
    "teeter": Activity(
        id="teeter",
        gerund="teetering",
        happen_gerund="happening while teetering",
        risk="might fall down the stairs",
        clue="a soft clink from below",
        keyword="teeter",
        tags={"teeter", "stairs", "basement"},
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a little brass lantern",
        type="lantern",
    ),
    "key": Prize(
        label="key",
        phrase="a tiny silver key",
        type="key",
    ),
}

TOOLS = [
    Tool(
        id="lamp",
        label="a candle lamp",
        description="a lamp that can light each stair",
        solves="shine on the steps",
        tags={"light", "stairs"},
    ),
    Tool(
        id="rail",
        label="the handrail",
        description="a steady rail for careful hands",
        solves="steady the climb",
        tags={"steady", "stairs"},
    ),
]

NAMES = ["Elsa", "Mira", "Anya", "Nora", "Lena", "Ivy", "Rowan", "Tamsin"]
PARENTS = ["mother", "father", "grandmother", "guardian"]
TRAITS = ["curious", "gentle", "brave", "careful", "lively"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for act in ACTIVITIES.values():
            for prize in PRIZES:
                combos.append((place, act.id, prize))
    return combos


def predict_risk(world: World, hero: Entity, act: Activity, prize: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] = sim.get(hero.id).memes.get("worry", 0) + 1
    if act.id == "teeter":
        sim.get(prize.id).meters["jostled"] = sim.get(prize.id).meters.get("jostled", 0) + 1
    return True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str,
         hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, label=hero_name,
        meters={"balance": 1.0}, memes={"curiosity": 1.0},
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=parent_type, label=f"the {parent_type}",
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, place=setting.place,
        meters={"hidden": 1.0},
    ))

    hero.memes["love"] = 1.0
    hero.memes["worry"] = 0.0
    prize.meters["mystery"] = 1.0

    world.say(f"Once in a small house, {hero.name_or_label()} was a {hero_traits[0]} little {hero.type} who lived beside {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved the hush of the stairs, where every shadow seemed to hold a secret.")
    world.say(f"One evening, the child noticed {prize.phrase} missing from its resting place, and the loss felt like a tiny mystery.")

    world.para()
    world.say(f"{hero.name_or_label()} stood by the first step and listened. {activity.clue.capitalize()} came from below, and the stairs looked very narrow.")
    world.say(f"{hero.pronoun().capitalize()} thought, 'If I go too fast, I might {activity.risk}.'")
    world.say(f"So {hero.pronoun()} held very still, trying to hear where the secret had gone.")
    world.say(f"Then {parent.label_or_label() if hasattr(parent, 'label_or_label') else parent.label} came near with a lantern and said, 'Careful now, little one. A stair is not a stage for rushing.'")

    world.para()
    tool = next(t for t in TOOLS if t.id == "lamp")
    world.add(Entity(id=tool.id, type="tool", label=tool.label, secure=True))
    hero.memes["worry"] += 1
    world.say(f"{hero.name_or_label()} took the lantern and lit each step, and the dark corners became as plain as bread on a table.")
    world.say(f"Under the lowest stair they found the tiny silver key at last, caught beside a cobweb like a sleeping star.")
    world.say(f"The mystery was solved: the key had rolled when someone had been {activity.happen_gerund} near the rail.")

    world.para()
    world.say(f"{parent.label} smiled, and {hero.name_or_label()} breathed out a quiet laugh.")
    world.say(f"Together they climbed down one careful step at a time, and the key returned safely to its box.")
    world.say(f"In the lantern glow, the basement stairs no longer felt like a worry; they felt like a little road where caution had kept the treasure safe.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        tool=tool,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, activity = f["hero"], f["prize"], f["activity"]
    return [
        f"Write a fairy-tale story for a young child about {hero.name_or_label()} on {world.setting.place} with a tiny mystery to solve.",
        f"Tell a gentle story where {hero.name_or_label()} is worried about {activity.risk} while looking for {prize.phrase}.",
        f"Write a story that uses inner monologue, a cautionary warning, and an ending where a hidden object is found safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.name_or_label()} want to solve on the basement stairs?",
            answer=f"{hero.name_or_label()} wanted to solve the small mystery of where {prize.phrase} had gone.",
        ),
        QAItem(
            question=f"What did {hero.pronoun().capitalize()} think might happen if {hero.pronoun()} hurried on the stairs?",
            answer=f"{hero.pronoun().capitalize()} thought {hero.pronoun('object')} might {activity.risk} if {hero.pronoun()} hurried.",
        ),
        QAItem(
            question=f"Who gave the cautionary warning?",
            answer=f"{parent.label} gave the warning and reminded {hero.name_or_label()} to be careful on the stairs.",
        ),
        QAItem(
            question=f"What was found at the end?",
            answer=f"The tiny silver key was found tucked below the lowest stair, and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a basement stair?",
            answer="Basement stairs are steps that lead down to a lower part of a house, so people should walk carefully on them.",
        ),
        QAItem(
            question="Why do people use a lantern or lamp on dark stairs?",
            answer="People use a lantern or lamp to shine light on dark stairs so they can see each step and avoid slipping.",
        ),
        QAItem(
            question="What does it mean to be cautious?",
            answer="To be cautious means to move slowly and carefully so you do not get hurt or break anything.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
activity(teeter).
setting(basement_stairs).
prize(lantern).
prize(key).

risk(teeter, stair_fall).
clue(teeter, under_stairs_light).

valid_story(P, A, R) :- setting(P), activity(A), prize(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.id))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params, generation, CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld on basement stairs.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")

    place = args.place or "basement_stairs"
    activity = args.activity or "teeter"
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait, "careful"],
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("basement_stairs", "teeter", "lantern", "Mira", "girl", "mother", "curious"),
            StoryParams("basement_stairs", "teeter", "key", "Rowan", "boy", "grandmother", "careful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
