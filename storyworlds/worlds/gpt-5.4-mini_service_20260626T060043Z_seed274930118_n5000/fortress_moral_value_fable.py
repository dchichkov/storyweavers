#!/usr/bin/env python3
"""
A small fable-world about a fortress, a shared burden, and a moral turn.

The seed premise:
- A proud fortress keeps a village safe.
- One keeper wants praise and control.
- A wiser helper shows that honesty and shared work protect the fortress better than pride.

This world is intentionally tiny and classical: one setting, a few characters,
one conflict, and a clear moral ending.
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
        gendered = {
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "owl": {"subject": "she", "object": "her", "possessive": "her"},
            "mouse": {"subject": "she", "object": "her", "possessive": "her"},
        }
        return gendered.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class Setting:
    place: str = "the fortress hill"
    affords: set[str] = field(default_factory=lambda: {"keep_watch", "haul_stones"})


@dataclass
class Burden:
    label: str
    phrase: str
    risk: str
    region: str
    moral: str


@dataclass
class Helper:
    label: str
    offer: str
    method: str
    result: str
    moral_gain: str


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    burden: str
    hero: str
    helper: str
    seed: Optional[int] = None


BURDENS = {
    "gate": Burden(
        label="gate",
        phrase="the fortress gate",
        risk="left open",
        region="gate",
        moral="A fortress with an open gate is no fortress at all.",
    ),
    "lamp": Burden(
        label="lamp",
        phrase="the watch lamp",
        risk="left dark",
        region="watchtower",
        moral="A guard who hides the light makes every path harder.",
    ),
    "granary": Burden(
        label="granary",
        phrase="the grain store",
        risk="left untended",
        region="storehouse",
        moral="What is shared and cared for feeds everyone in hard weather.",
    ),
}

HEROES = {
    "fox": "fox",
    "owl": "owl",
    "mouse": "mouse",
}

HELPERS = {
    "owl": Helper(
        label="an owl messenger",
        offer="tell the truth and call the villagers",
        method="flew from the tower to warn everyone",
        result="the gate was fixed before danger came",
        moral_gain="honesty and help make strong walls stronger",
    ),
    "mouse": Helper(
        label="a small mouse",
        offer="share the work instead of boasting",
        method="brought rope and tied the broken beam with careful paws",
        result="the burden was lifted before it could break",
        moral_gain="even small hands can save a great home",
    ),
    "fox": Helper(
        label="a fox scout",
        offer="ask for help instead of pretending to be wise",
        method="ran to gather builders and farmers together",
        result="the storehouse was secured in time",
        moral_gain="pride hides problems, but humility solves them",
    ),
}

HERO_NAMES = {
    "fox": ["Fenn", "Rook", "Tarin"],
    "owl": ["Mira", "Orla", "Nera"],
    "mouse": ["Pip", "Lina", "Suri"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable story world about a fortress and a moral lesson.")
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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
    burden = args.burden or rng.choice(sorted(BURDENS))
    hero = args.hero or rng.choice(sorted(HEROES))
    helper = args.helper or rng.choice(sorted(HELPERS))
    if helper != hero and args.helper and args.hero and helper != hero:
        # explicit mismatch allowed: helper can differ, but must be one of the registry
        pass
    if hero not in HERO_NAMES:
        raise StoryError("Unknown hero.")
    return StoryParams(burden=burden, hero=hero, helper=helper)


def _setup(world: World, params: StoryParams) -> None:
    burden = BURDENS[params.burden]
    hero_type = HEROES[params.hero]
    helper = HELPERS[params.helper]
    hero = world.add(Entity(id="Hero", kind="character", type=hero_type, label=params.hero))
    guide = world.add(Entity(id="Guide", kind="character", type=params.helper, label=helper.label))
    fortress = world.add(Entity(id="Fortress", kind="thing", type="fortress", label="the fortress"))
    burden_ent = world.add(Entity(id="Burden", kind="thing", type=params.burden, label=burden.label, phrase=burden.phrase))
    world.facts.update(hero=hero, guide=guide, fortress=fortress, burden=burden_ent, helper_def=helper, burden_def=burden, params=params)


def _introduce(world: World) -> None:
    hero = world.facts["hero"]
    burden = world.facts["burden_def"]
    world.say(
        f"On a hill stood a stone fortress where {hero.label} lived and listened to the wind."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} loved the fortress because it kept the village safe, "
        f"and yet {hero.pronoun('subject')} wanted praise more than patience."
    )
    world.say(
        f"The worst trouble came when {burden.phrase} was left {burden.risk}."
    )


def _predict(world: World) -> bool:
    return True


def _conflict(world: World) -> None:
    hero = world.facts["hero"]
    burden = world.facts["burden_def"]
    helper = world.facts["helper_def"]
    world.para()
    world.say(
        f"{hero.label} saw the problem but tried to hide it, hoping no one would notice."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"Then {helper.label} arrived and said, \"{helper.offer.capitalize()}.\""
    )
    world.say(
        f"{helper.method.capitalize()}, and the truth spread through the fortress like a bell."
    )
    hero.memes["shame"] = hero.memes.get("shame", 0) + 1


def _resolution(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper_def"]
    burden = world.facts["burden_def"]
    world.para()
    world.say(
        f"{hero.label} finally spoke honestly and asked the others to help."
    )
    world.say(
        f"Together they worked until {helper.result}, and the fortress stood firm again."
    )
    hero.memes["pride"] = 0
    hero.memes["gratitude"] = hero.memes.get("gratitude", 0) + 1
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0) + 1
    world.facts["moral"] = burden.moral
    world.say(
        f"In the end, everyone remembered: {burden.moral}"
    )


def tell(params: StoryParams) -> World:
    world = World(Setting())
    _setup(world, params)
    _introduce(world)
    _conflict(world)
    _resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    b = world.facts["burden_def"]
    return [
        f"Write a short fable about a fortress and {p.hero} learning the value of honesty.",
        f"Tell a child-friendly story where a {p.hero} at a fortress hides a problem with {b.phrase}, then learns a moral lesson.",
        f"Write a simple fable with a fortress, a warning, and a kind helper who turns pride into wisdom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    burden = world.facts["burden_def"]
    hero = world.facts["hero"]
    helper = world.facts["helper_def"]
    return [
        QAItem(
            question=f"What did {p.hero} learn at the fortress?",
            answer=f"{hero.label} learned that honesty and shared work protect the fortress better than pride.",
        ),
        QAItem(
            question=f"What problem put the fortress at risk?",
            answer=f"{burden.phrase.capitalize()} was left {burden.risk}, which created the trouble in the story.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label.capitalize()} urged everyone to tell the truth and then helped bring the right work to the right place.",
        ),
        QAItem(
            question="What was the moral of the fable?",
            answer=world.facts["moral"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fortress?",
            answer="A fortress is a strong place made to protect people and keep danger out.",
        ),
        QAItem(
            question="Why do people build strong walls around a fortress?",
            answer="People build strong walls so the fortress can resist danger and keep the people inside safe.",
        ),
        QAItem(
            question="What is a moral?",
            answer="A moral is the lesson a story teaches about how to act well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
burden_at_risk(B) :- burden(B).
needs_help(B) :- burden_at_risk(B).
moral_story(B) :- needs_help(B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for b in BURDENS:
        lines.append(asp.fact("burden", b))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show burden_at_risk/1. #show needs_help/1. #show moral_story/1."))
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    expected = {
        ("burden_at_risk", ("gate",)),
        ("burden_at_risk", ("lamp",)),
        ("burden_at_risk", ("granary",)),
        ("needs_help", ("gate",)),
        ("needs_help", ("lamp",)),
        ("needs_help", ("granary",)),
        ("moral_story", ("gate",)),
        ("moral_story", ("lamp",)),
        ("moral_story", ("granary",)),
    }
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH")
    print("got:", sorted(atoms))
    print("exp:", sorted(expected))
    return 1


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


CURATED = [
    StoryParams(burden="gate", hero="fox", helper="owl"),
    StoryParams(burden="lamp", hero="owl", helper="mouse"),
    StoryParams(burden="granary", hero="mouse", helper="fox"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show moral_story/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show moral_story/1."))
        print(sorted((a.name, tuple(str(x) for x in a.arguments)) for a in model))
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
            header = f"### {p.hero} / {p.burden} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
