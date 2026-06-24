#!/usr/bin/env python3
"""
A tiny mythic story world about a shishkebab, an ice spirit, and a fluid
offering that tests friendship and kindness.
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


@dataclass
class StoryParams:
    setting: str = "the cold valley"
    hero: str = "Ari"
    friend: str = "Mira"
    giver: str = "the river spirit"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]


SETTING_REGISTRY = {
    "the cold valley": {
        "tags": {"ice", "fluid", "myth"},
        "mood": "quiet and pale",
    },
    "the moonlit spring": {
        "tags": {"fluid", "myth"},
        "mood": "silver and still",
    },
    "the frozen grove": {
        "tags": {"ice", "myth"},
        "mood": "blue and secret",
    },
}

# Inline ASP twin: a simple parity-checkable rule set.
ASP_RULES = r"""
setting(cold_valley).
setting(moonlit_spring).
setting(frozen_grove).

feature(friendship).
feature(kindness).

can_tell_story(S) :- setting(S).
can_tell_story(S) :- setting(S), feature(friendship), feature(kindness).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTING_REGISTRY:
        key = s.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.append(asp.fact("feature", "friendship"))
    lines.append(asp.fact("feature", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic shishkebab, ice, and fluid story world.")
    ap.add_argument("--setting", choices=list(SETTING_REGISTRY))
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--giver")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Ari", "Nima", "Oren", "Ilo", "Sera"])
    friend = args.friend or rng.choice(["Mira", "Tavi", "Luma", "Rin", "Kio"])
    giver = args.giver or rng.choice(["the river spirit", "the frost elder", "the spring nymph"])
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(setting=setting, hero=hero, friend=friend, giver=giver)


def _story_lines(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    giver = f["giver"]
    setting = f["setting"]
    lines = []
    lines.append(f"In {setting}, {hero} and {friend} walked where the stone was old and the wind was thin.")
    lines.append(f"They carried a shishkebab, warm from the fire, because even in myth, small meals can make brave hearts.")
    lines.append(f"Near a bright pool of ice, {giver} rose with a bowl of fluid and said, \"Only the kind may drink.\"")
    lines.append(f"{hero} reached first, but {friend} saw the shiver in the pool and gently shared the shishkebab instead.")
    lines.append(f"That kindness softened the air; the ice stopped biting, the fluid stayed clear, and {giver} smiled on both friends.")
    lines.append(f"By dusk, they sat side by side, and the shishkebab was finished while the valley felt warmer than before.")
    return lines


def generate(params: StoryParams) -> StorySample:
    world = World(setting=params.setting)
    hero = world.add(Entity(params.hero, "character", memes={"friendship": 1.0}))
    friend = world.add(Entity(params.friend, "character", memes={"kindness": 1.0}))
    giver = world.add(Entity(params.giver, "spirit", meters={"fluid": 1.0}, memes={"judgment": 1.0}))
    world.facts.update(
        hero=hero.name,
        friend=friend.name,
        giver=giver.name,
        setting=params.setting,
        theme="shishkebab, ice, fluid",
    )
    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a short myth about {params.hero}, {params.friend}, and a shishkebab in {params.setting}.",
        f"Tell a gentle legend where ice and fluid test friendship and kindness.",
        "Write a child-facing myth in which sharing food changes a cold place.",
    ]
    story_qa = [
        QAItem(
            question="Who shared the shishkebab when the spirit demanded kindness?",
            answer=f"{params.friend} shared the shishkebab, and that act helped both friends."
        ),
        QAItem(
            question="What changed the mood of the icy place?",
            answer="Kindness changed the mood; after the friends shared, the ice stopped feeling harsh."
        ),
        QAItem(
            question=f"Where did {params.hero} and {params.friend} meet the spirit?",
            answer=f"They met the spirit in {params.setting}."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, share, or be gentle with others."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between people who help and enjoy each other."
        ),
        QAItem(
            question="What is ice?",
            answer="Ice is frozen water, and it can feel very cold and hard."
        ),
        QAItem(
            question="What is fluid?",
            answer="A fluid is something that can flow, like water or other liquids."
        ),
        QAItem(
            question="What is a shishkebab?",
            answer="A shishkebab is food cooked on a skewer, often with small pieces of meat or vegetables."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.name}: kind={e.kind}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    py = {(s,) for s in _valid_python()}
    cl = set(_asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def generation_prompts(sample: StorySample) -> list[str]:
    return sample.prompts


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            params = StoryParams(setting=setting, hero="Ari", friend="Mira", giver="the river spirit")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = build_story_params(args, rng)
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
