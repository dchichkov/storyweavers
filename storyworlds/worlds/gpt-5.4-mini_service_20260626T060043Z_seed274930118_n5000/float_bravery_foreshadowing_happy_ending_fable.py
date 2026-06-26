#!/usr/bin/env python3
"""
A tiny fable-like storyworld about bravery, foreshadowing, and a happy ending.

Seed premise:
- A small creature must cross a river.
- A floating object offers a way across, but it is not enough for the whole problem.
- A wise hint early on foreshadows the later success.
- Bravery means trying the careful path anyway, with help.
- The ending should feel warm, clear, and earned.
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
# Core world data
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    afloat: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sheep"}
        male = {"boy", "father", "man", "fox", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the river bank"
    current: str = "gentle"
    afford_crossing: bool = True


@dataclass
class Challenge:
    id: str
    verb: str
    noun: str
    foreshadow: str
    risk: str
    danger: str
    resolved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    help_text: str
    floaty: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bank": Setting(place="the river bank", current="gentle", afford_crossing=True),
    "meadow": Setting(place="the meadow by the river", current="gentle", afford_crossing=True),
    "woods": Setting(place="the woods by the river", current="swift", afford_crossing=True),
}

CHALLENGES = {
    "brook": Challenge(
        id="brook",
        verb="cross the brook",
        noun="brook",
        foreshadow="a floating leaf",
        risk="the water looked too wide for small feet",
        danger="the current could pull a little traveler off balance",
        resolved_by="a floating log and a steady helper",
        tags={"float", "river", "bravery"},
    ),
    "ferry": Challenge(
        id="ferry",
        verb="reach the far path",
        noun="far path",
        foreshadow="a drifting branch",
        risk="the path across was only a promise in the water",
        danger="the ripples made the crossing feel unsure",
        resolved_by="a floating raft and brave teamwork",
        tags={"float", "river", "bravery"},
    ),
    "island": Challenge(
        id="island",
        verb="visit the little island",
        noun="little island",
        foreshadow="a bobbing reed",
        risk="the middle of the river sat far away",
        danger="the water was deeper than a hop",
        resolved_by="a floating boat and a kind guide",
        tags={"float", "river", "bravery"},
    ),
}

TOOLS = {
    "leaf": Tool(
        id="leaf",
        label="leaf",
        phrase="a leaf that floated like a tiny boat",
        help_text="It showed that light things could ride on the water.",
        floaty=True,
        tags={"float", "foreshadowing"},
    ),
    "log": Tool(
        id="log",
        label="log",
        phrase="a smooth log",
        help_text="It could float and carry a careful traveler part of the way.",
        floaty=True,
        tags={"float", "river"},
    ),
    "raft": Tool(
        id="raft",
        label="raft",
        phrase="a small raft tied with rope",
        help_text="It could float and hold more than one traveler.",
        floaty=True,
        tags={"float", "river"},
    ),
    "boat": Tool(
        id="boat",
        label="boat",
        phrase="a little boat",
        help_text="It could float people to the other side.",
        floaty=True,
        tags={"float", "river"},
    ),
}

NAMES = ["Milo", "Mina", "Rory", "Lena", "Tavi", "Pip", "Nora", "Bram"]
KINDS = ["mouse", "hare", "fox", "goat", "bird"]
TRAITS = ["small", "kind", "curious", "brave", "gentle", "careful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    challenge: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

valid(C, T) :- challenge(C), tool(T), resolves(T, C).
valid_story(S, C, T) :- setting(S), valid(C, T), affords(S, C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_crossing:
            lines.append(asp.fact("affords", sid, "crossing"))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for tag in sorted(c.tags):
            lines.append(asp.fact("tag", cid, tag))
        for tid in sorted(TOOLS):
            pass
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.floaty:
            lines.append(asp.fact("floaty", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag_tool", tid, tag))
    # explicit resolution facts
    lines.append(asp.fact("resolves", "log", "brook"))
    lines.append(asp.fact("resolves", "raft", "ferry"))
    lines.append(asp.fact("resolves", "boat", "island"))
    lines.append(asp.fact("resolves", "leaf", "brook"))
    lines.append(asp.fact("resolves", "leaf", "ferry"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_story() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_choices() -> list[tuple[str, str]]:
    out = []
    for c in CHALLENGES:
        for t in TOOLS:
            if is_reasonable(c, t):
                out.append((c, t))
    return out


def is_reasonable(challenge_id: str, tool_id: str) -> bool:
    c = CHALLENGES[challenge_id]
    t = TOOLS[tool_id]
    if challenge_id == "brook":
        return tool_id in {"leaf", "log"}
    if challenge_id == "ferry":
        return tool_id in {"leaf", "raft"}
    if challenge_id == "island":
        return tool_id in {"boat", "raft"}
    return False


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def explain_rejection(challenge: Challenge, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not honestly solve {challenge.noun}. "
        f"The fable needs a floating helper that can really carry the hero across.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.tool:
        if not is_reasonable(args.challenge, args.tool):
            raise StoryError(explain_rejection(CHALLENGES[args.challenge], TOOLS[args.tool]))

    choices = valid_choices()
    if args.setting:
        choices = [(c, t) for c, t in choices if args.setting in SETTINGS]
    if args.challenge:
        choices = [(c, t) for c, t in choices if c == args.challenge]
    if args.tool:
        choices = [(c, t) for c, t in choices if t == args.tool]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")

    challenge_id, tool_id = rng.choice(sorted(choices))
    hero_name = args.name or rng.choice(NAMES)
    hero_type = args.hero_type or rng.choice(KINDS)
    trait = args.trait or rng.choice(TRAITS)
    setting = args.setting or rng.choice(sorted(SETTINGS))
    return StoryParams(
        setting=setting,
        challenge=challenge_id,
        hero_name=hero_name,
        hero_type=hero_type,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"fear": 0.0, "distance": 0.0},
        memes={"bravery": 0.0, "hope": 0.0, "joy": 0.0},
    ))
    challenge = CHALLENGES[params.challenge]
    tool_id = next(t for t in TOOLS if is_reasonable(params.challenge, t))
    # choose a fitting tool deterministically by challenge
    if params.challenge == "brook":
        tool_id = "leaf" if params.trait in {"curious", "gentle"} else "log"
    elif params.challenge == "ferry":
        tool_id = "raft"
    elif params.challenge == "island":
        tool_id = "boat"

    tool = world.add(Entity(
        id=tool_id,
        kind="thing",
        type="thing",
        label=TOOLS[tool_id].label,
        phrase=TOOLS[tool_id].phrase,
        afloat=True,
    ))
    helper = world.add(Entity(
        id="Guide",
        kind="character",
        type="hare",
        label="the guide",
        meters={"calm": 1.0},
        memes={"wisdom": 1.0},
    ))
    world.facts.update(hero=hero, tool=tool, helper=helper, challenge=challenge, params=params)
    return world


def narrate(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    tool: Entity = f["tool"]
    helper: Entity = f["helper"]
    challenge: Challenge = f["challenge"]
    params: StoryParams = f["params"]

    world.say(
        f"Once, in a little fable, {hero.label} was a {params.trait} {hero.type} who lived near {world.setting.place}."
    )
    world.say(
        f"{hero.label.capitalize()} liked to explore, but {challenge.risk}. "
        f"Still, {hero.pronoun().capitalize()} kept watching the water with brave eyes."
    )
    world.say(
        f"One morning, {hero.label} noticed {tool.phrase}; {challenge.foreshadow} drifted by first, "
        f"as if the river were leaving a clue."
    )
    world.say(
        f"{helper.label.capitalize()} pointed and said, \"When something can float, it can show the way.\""
    )
    hero.memes["hope"] += 1.0
    hero.memes["bravery"] += 1.0
    hero.meters["fear"] += 1.0
    world.say(
        f"{hero.label} took a small breath, stepped forward, and tried the careful path. "
        f"{challenge.danger}, so {hero.label} did not rush."
    )
    if tool.id == "leaf":
        world.say(
            f"First, the leaf drifted ahead, and then the log followed it like a promise. "
            f"The foreshadowing had been true."
        )
    elif tool.id == "raft":
        world.say(
            f"The raft bobbed beside the bank, and {helper.label} tied the rope tight. "
            f"It floated steadily, just as the river had hinted."
        )
    else:
        world.say(
            f"The little boat rocked once, then settled. {helper.label} steadied it, and the water gave way."
        )
    hero.meters["distance"] += 1.0
    hero.memes["joy"] += 1.0
    world.say(
        f"At last, {hero.label} reached the far side and smiled. {challenge.resolved_by} had carried the day, "
        f"and the river no longer felt like a problem."
    )
    world.say(
        f"So the brave little traveler went home with dry paws and a bright heart, "
        f"and the whole fable ended happily."
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    c = world.facts["challenge"]
    return [
        f"Write a short fable about a {p.trait} {p.hero_type} named {p.hero_name} who must {c.verb} and learns bravery.",
        f"Tell a child-friendly story where a floating object gives an early hint and helps a little hero cross water safely.",
        f"Make a gentle fable with foreshadowing, bravery, and a happy ending near {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    c = world.facts["challenge"]
    hero: Entity = world.facts["hero"]
    tool: Entity = world.facts["tool"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {p.hero_name}, a {p.trait} {p.hero_type} who lived near {world.setting.place}.",
        ),
        QAItem(
            question=f"What problem did {p.hero_name} face?",
            answer=f"{p.hero_name} needed to {c.verb}, but the water looked risky and hard to cross alone.",
        ),
        QAItem(
            question=f"What object floated and hinted at the solution?",
            answer=f"{tool.phrase.capitalize()} floated on the water and hinted that a careful crossing would work.",
        ),
        QAItem(
            question=f"Who helped {p.hero_name} feel brave?",
            answer=f"{helper.label.capitalize()} helped by pointing out the floating clue and steadying the crossing.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.label} reached the far side safely, felt joyful, and the fable ended happily.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something floats?",
            answer="When something floats, it stays on top of the water instead of sinking.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint near the beginning that helps you guess what will matter later.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary while still being careful and trying your best.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} afloat={e.afloat} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable about float, bravery, and a happy ending.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--challenge", choices=sorted(CHALLENGES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=sorted(set(KINDS)))
    ap.add_argument("--trait", choices=sorted(set(TRAITS)))
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


def asp_verify() -> int:
    py = set(valid_choices())
    asp_set = set(asp_valid())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("Only in python:", sorted(py - asp_set))
    print("Only in clingo:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(setting="bank", challenge="brook", hero_name="Milo", hero_type="mouse", trait="brave"),
    StoryParams(setting="meadow", challenge="ferry", hero_name="Lena", hero_type="hare", trait="curious"),
    StoryParams(setting="woods", challenge="island", hero_name="Bram", hero_type="goat", trait="gentle"),
]


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
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
            header = f"### {p.hero_name}: {p.challenge} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
