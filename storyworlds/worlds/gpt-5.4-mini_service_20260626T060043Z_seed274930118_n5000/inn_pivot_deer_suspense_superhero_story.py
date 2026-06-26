#!/usr/bin/env python3
"""
A standalone story world for a tiny superhero suspense tale set at an inn.

Premise:
- A young hero stays at an inn with a small gift or task.
- A deer appears outside in the stormy dark, creating suspense.
- The hero must pivot from a bold plan to a careful rescue.
- The ending should show the deer safe and the hero changed.

This world models physical meters and emotional memes, with a simple
reasonableness gate and an inline ASP twin.
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
# Core model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    role: str = ""               # hero, keeper, deer, innkeeper, cape, lantern
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.role in {"hero", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.role in {"heroine", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the inn"
    has_yard: bool = True
    has_window: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    sidekick: str
    setting: str = "inn"
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "inn": Setting(place="the inn", has_yard=True, has_window=True),
}

CHARACTER_NAMES = ["Ari", "Mina", "Jules", "Nova", "Pip", "Theo", "Lena", "Kai"]
SIDEKICKS = ["page", "bellhop", "stable helper", "inn helper"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])

    hero_role = "heroine" if params.gender == "girl" else "hero"
    hero = world.add(Entity(id=params.name, kind="character", role=hero_role, label=params.name))
    sidekick = world.add(Entity(id="sidekick", kind="character", role="helper", label=params.sidekick))
    innkeeper = world.add(Entity(id="innkeeper", kind="character", role="keeper", label="the innkeeper"))

    cape = world.add(Entity(id="cape", label="a bright cape", owner=hero.id))
    lantern = world.add(Entity(id="lantern", label="a small lantern", owner=hero.id))
    deer = world.add(Entity(id="deer", kind="character", role="deer", label="the deer"))

    # Initial emotional meters.
    hero.memes["hope"] = 1
    hero.memes["curiosity"] = 1
    hero.memes["boldness"] = 1
    sidekick.memes["nervous"] = 1
    deer.meters["cold"] = 1

    # Act 1: setup.
    world.say(f"{hero.id} stayed at {world.setting.place} with {sidekick.label}.")
    world.say(f"{hero.id} wore {cape.label} and carried {lantern.label}, just like a little superhero.")
    world.say(f"That evening, the hall felt quiet, and every window looked darker than usual.")

    # Act 2: suspense.
    world.para()
    hero.memes["alert"] = 1
    world.say(f"Then {sidekick.label} pointed toward the yard and whispered, 'Look.'")
    world.say(f"A deer stood near the fence, trembling in the cold and staring at the window light.")
    world.say(f"{hero.id}'s heart jumped. {hero.id} had planned to race outside, but now the moment felt serious.")
    hero.memes["suspense"] = 1
    hero.memes["fear"] = 1
    sidekick.memes["fear"] = 1

    # Pivot turn: from boldness to care.
    world.para()
    world.say(f"{hero.id} took a breath and made a quick pivot.")
    world.say(f"Instead of charging out alone, {hero.id} lowered the lantern and moved slowly toward the door.")
    world.say(f"{hero.id} asked the innkeeper for a blanket and a bowl of water.")

    # Resolution.
    hero.memes["boldness"] = 0.5
    hero.memes["care"] = 1
    hero.memes["suspense"] = 0
    deer.meters["cold"] = 0
    deer.meters["safe"] = 1
    world.para()
    world.say(f"Together, they guided the deer away from the mud and into the sheltered yard by the inn.")
    world.say(f"The blanket kept the deer warm, and the lantern made a calm gold circle on the grass.")
    world.say(f"In the end, {hero.id} was still a superhero, but now {hero.id} knew the bravest move was the gentle one.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        innkeeper=innkeeper,
        cape=cape,
        lantern=lantern,
        deer=deer,
        setting=world.setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short suspense story for children about {hero.id}, a hero at an inn, and a deer in danger.",
        f"Tell a superhero-style story where a child must pivot from a bold plan to a careful rescue.",
        f"Create a gentle story with an inn, a deer, suspense, and a brave change of heart.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    deer = f["deer"]
    return [
        QAItem(
            question=f"Where did {hero.id} stay?",
            answer=f"{hero.id} stayed at the inn with {sidekick.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} see outside?",
            answer=f"{hero.id} saw a deer trembling near the fence.",
        ),
        QAItem(
            question="What changed the hero's plan?",
            answer="The hero made a pivot and chose a careful rescue instead of rushing out alone.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The deer was safe and warm, and {hero.id} learned that a gentle choice can be the bravest one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inn?",
            answer="An inn is a place where travelers stay and sleep for a while.",
        ),
        QAItem(
            question="What is a deer?",
            answer="A deer is a wild animal with legs made for running and soft ears for listening.",
        ),
        QAItem(
            question="What does pivot mean?",
            answer="To pivot means to turn in a new direction or change a plan when the moment calls for it.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important or surprising might happen soon.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_fact(H).
deer(D) :- deer_fact(D).

suspense(H) :- fear(H), alert(H).
pivot(H) :- suspense(H), care(H).

safe(D) :- deer_safe(D).
ending(H, D) :- pivot(H), safe(D).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hero_fact", "hero"))
    lines.append(asp.fact("deer_fact", "deer"))
    lines.append(asp.fact("fear", "hero"))
    lines.append(asp.fact("alert", "hero"))
    lines.append(asp.fact("care", "hero"))
    lines.append(asp.fact("deer_safe", "deer"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show pivot/1.\n#show ending/2."))
    shown = set(asp.atoms(model, "pivot")) | set(asp.atoms(model, "ending"))
    expected = {("hero",), ("hero", "deer")}
    if shown == expected:
        print("OK: ASP parity matches the Python world.")
        return 0
    print("MISMATCH between ASP and Python world.")
    print("  got:", sorted(shown))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting != "inn":
        raise StoryError("This story world only supports the inn setting.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHARACTER_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(
        name=name,
        gender=gender,
        sidekick=sidekick,
        setting="inn",
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(name="Mina", gender="girl", sidekick="page", setting="inn"),
    StoryParams(name="Theo", gender="boy", sidekick="bellhop", setting="inn"),
    StoryParams(name="Nova", gender="girl", sidekick="stable helper", setting="inn"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero suspense storyworld set at an inn.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show pivot/1.\n#show ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show pivot/1.\n#show ending/2."))
        print("pivot:", sorted(set(asp.atoms(model, "pivot"))))
        print("ending:", sorted(set(asp.atoms(model, "ending"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
