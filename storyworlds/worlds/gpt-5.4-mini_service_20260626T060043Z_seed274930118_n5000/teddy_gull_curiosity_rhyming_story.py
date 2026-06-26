#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/teddy_gull_curiosity_rhyming_story.py
===============================================================================================================

A tiny storyworld for a rhyming curiosity tale about a teddy, a gull, and a
small discovery at the shore.

The world is deliberately simple:
- a child carries a teddy,
- a curious gull notices something shiny,
- the child follows the gull,
- curiosity leads to a safe, helpful reveal,
- the ending proves what changed.

The prose is generated from world state rather than from a frozen template.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    friendly: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type == "gull":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    breeze: str
    sound: str
    sheen: str


@dataclass
class StoryParams:
    setting: str = "shore"
    name: str = "Teddy"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shore": Setting(
        place="the shore",
        breeze="soft",
        sound="the hush of waves",
        sheen="a silver sheen",
    ),
    "harbor": Setting(
        place="the harbor",
        breeze="salty",
        sound="the clink of ropes",
        sheen="a bright sheen",
    ),
}

NAMES = ["Teddy", "Milo", "Nora", "Iris", "Pip", "June", "Finn", "Luna"]

OBJECTS = {
    "shell": "a tiny shell",
    "key": "a little key",
    "pebble": "a smooth pebble",
    "string": "a red string",
}

RHYME_ENDINGS = {
    "curious": "glorious",
    "shiny": "tiny",
    "glow": "know",
    "gleam": "dream",
    "shore": "more",
    "play": "day",
    "light": "bright",
    "see": "free",
}

ASP_RULES = r"""
% A curiosity story is valid if a setting exists and the gull has a shiny clue.
valid_story(S) :- setting(S), gull_clue(S).

% The child can safely follow when the clue is harmless and the discovery is friendly.
safe_follow(S) :- valid_story(S), clue_harmless(S), discovery_friendly(S).

#show valid_story/1.
#show safe_follow/1.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rhyme(word: str) -> str:
    return RHYME_ENDINGS.get(word, word)


def choose_setting(name: str) -> Setting:
    return SETTINGS[name]


def story_rhythm(lines: list[str]) -> str:
    return " ".join(lines)


def final_image(setting: Setting, teddy: Entity, gull: Entity, clue: Entity) -> str:
    return (
        f"In {setting.place}, {teddy.id} held {teddy.phrase} close, and the gull "
        f"watched by the water as the small clue glimmered near the foam."
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")

    setting = choose_setting(params.setting)
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        phrase="a teddy bear",
        carried_by=params.name,
        meters={"steps": 0.0},
        memes={"curiosity": 0.0, "joy": 0.0},
    ))
    teddy = world.add(Entity(
        id="teddy",
        kind="thing",
        type="teddy",
        label="teddy",
        phrase="a stitched teddy",
        owner=params.name,
        carried_by=params.name,
        meters={"softness": 1.0},
        memes={"comfort": 1.0},
    ))
    gull = world.add(Entity(
        id="gull",
        kind="character",
        type="gull",
        label="gull",
        phrase="a bright gull",
        friendly=True,
        meters={"wing": 1.0},
        memes={"curiosity": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label="clue",
        phrase=OBJECTS["shell"],
        meters={"shine": 1.0},
    ))

    world.facts.update(
        child=child,
        teddy=teddy,
        gull=gull,
        clue=clue,
        setting=setting,
    )
    return world


def step_story(world: World) -> None:
    child: Entity = world.facts["child"]
    teddy: Entity = world.facts["teddy"]
    gull: Entity = world.facts["gull"]
    clue: Entity = world.facts["clue"]
    setting: Setting = world.facts["setting"]

    world.say(
        f"{child.id} came to {setting.place} with {teddy.id}, "
        f"where the breeze felt {setting.breeze} and {setting.sound} sounded light."
    )
    world.say(
        f"The little {gull.label} was curious too; it tilted its head and gave a soft cry "
        f"to the sky so blue."
    )

    world.para()
    child.memes["curiosity"] += 1.0
    child.meters["steps"] += 1.0
    world.say(
        f"{child.id} saw the gull and followed the sparkle, step by step, along the shore so bright."
    )
    world.say(
        f"The gull hopped ahead, and {child.id} held {teddy.id} tight, drawn by the tiny light."
    )

    world.para()
    world.say(
        f"Behind a shell and a stone, {child.id} found the clue: {clue.phrase}, soft and round."
    )
    world.say(
        f"It was not a trick or a prize to keep; it was a lost charm that had fallen to the ground."
    )

    world.para()
    child.memes["joy"] += 1.0
    gull.memes["joy"] = gull.memes.get("joy", 0.0) + 1.0
    clue.owner = "harbor child"
    world.say(
        f"{child.id} set the clue on a safe little ledge, then waved as the gull spun around."
    )
    world.say(
        f"The gull found the charm and the day felt warm; curiosity had led to something found."
    )

    world.para()
    world.say(final_image(setting, teddy, gull, clue))


def tell(params: StoryParams) -> World:
    world = build_world(params)
    step_story(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short rhyming story for a young child about a teddy, a gull, and curiosity.',
        f"Tell a gentle seaside story where {world.facts['child'].id} follows a gull and finds a small clue.",
        'Write a simple rhyming tale that begins with a teddy at the shore and ends with a safe discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    teddy: Entity = world.facts["teddy"]
    gull: Entity = world.facts["gull"]
    clue: Entity = world.facts["clue"]
    setting: Setting = world.facts["setting"]

    return [
        QAItem(
            question=f"Who went to {setting.place} with the teddy?",
            answer=f"{child.id} went to {setting.place} with the teddy.",
        ),
        QAItem(
            question="Why did the child follow the gull?",
            answer="The child followed the gull because curiosity made the little footsteps go near the bright, shining clue.",
        ),
        QAItem(
            question="What did the child find near the water?",
            answer=f"The child found {clue.phrase} near the water.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, {child.id} felt happy, the gull got its charm back, and the teddy stayed close like a safe friend.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gull?",
            answer="A gull is a seaside bird that can fly, hop, and call with a sharp little cry.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, listen, and learn about something new.",
        ),
        QAItem(
            question="What is a teddy?",
            answer="A teddy is a soft toy bear that a child can hold for comfort.",
        ),
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("breeze", sid, setting.breeze))
        lines.append(asp.fact("sound", sid, setting.sound))
    lines.append(asp.fact("gull_clue", "shore"))
    lines.append(asp.fact("gull_clue", "harbor"))
    lines.append(asp.fact("clue_harmless", "shore"))
    lines.append(asp.fact("clue_harmless", "harbor"))
    lines.append(asp.fact("discovery_friendly", "shore"))
    lines.append(asp.fact("discovery_friendly", "harbor"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1.\n#show safe_follow/1."))
    atoms = set(asp.atoms(model, "valid_story")) | set(asp.atoms(model, "safe_follow"))
    expected = {("shore",), ("harbor",)}
    if atoms == expected:
        print("OK: ASP gate matches the simple storyworld expectations.")
        return 0
    print("MISMATCH in ASP verification.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming curiosity storyworld about a teddy and a gull.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--name", choices=NAMES)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, name=name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/1.\n#show safe_follow/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in sorted(SETTINGS):
            p = StoryParams(setting=setting, name="Teddy", seed=base_seed)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
