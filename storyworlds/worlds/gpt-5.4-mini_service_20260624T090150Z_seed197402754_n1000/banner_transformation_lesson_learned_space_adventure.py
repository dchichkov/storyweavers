#!/usr/bin/env python3
"""
Story world: a tiny space-adventure about a banner, a transformation, and a
lesson learned.

A child on a small ship wants to celebrate a big star crossing with a banner.
The banner cannot stay put in space until the crew changes it into a proper
mission banner with clips and glow tape, and the child learns to plan for the
vacuum instead of fighting it.
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
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Ship:
    name: str
    deck: str = "the bright observation deck"
    outside: str = "the airlock window"
    space: str = "the quiet dark of space"


@dataclass
class StoryParams:
    ship: str = "Comet Lantern"
    hero_name: str = "Milo"
    helper_name: str = "Ari"
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SHIP_REGISTRY = {
    "Comet Lantern": Ship(name="Comet Lantern"),
    "Star Finch": Ship(name="Star Finch"),
    "Aurora Kite": Ship(name="Aurora Kite"),
}

HERO_NAMES = ["Milo", "Nia", "Tao", "Luna", "Remy"]
HELPER_NAMES = ["Ari", "Zia", "Juno", "Pax", "Kira"]

ASP_RULES = r"""
ship(S) :- ship_name(S).
banner(B) :- banner_name(B).
lesson(L) :- lesson_name(L).
transformed(B) :- banner_state(B, transformed).
ready(B) :- banner_state(B, ready).
lesson_learned(H) :- hero(H), learned(H).
safe_hang(B) :- ready(B), clipped(B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ship_name in SHIP_REGISTRY:
        lines.append(asp.fact("ship_name", ship_name))
    lines.append(asp.fact("banner_name", "mission_banner"))
    lines.append(asp.fact("lesson_name", "use_space_tools"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("banner_state", "mission_banner", "plain"))
    lines.append(asp.fact("banner_state", "mission_banner", "transformed"))
    lines.append(asp.fact("clipped", "mission_banner"))
    lines.append(asp.fact("learned", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show safe_hang/1.\n#show lesson_learned/1.\n#show transformed/1."))
    atoms = set((sym.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments)) for sym in model)
    want = {("safe_hang", ("mission_banner",)), ("lesson_learned", ("hero",)), ("transformed", ("mission_banner",))}
    if atoms == want:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(want))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure story world about a banner and a lesson learned.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    ship = args.ship or rng.choice(list(SHIP_REGISTRY))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != name])
    if helper == name:
        raise StoryError("The helper should be a different crew member from the hero.")
    return StoryParams(ship=ship, hero_name=name, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    ship = SHIP_REGISTRY[params.ship]
    world = World(ship)

    hero = world.add(Entity(id="hero", kind="character", label=params.hero_name, type="child"))
    helper = world.add(Entity(id="helper", kind="character", label=params.helper_name, type="crew"))
    banner = world.add(Entity(
        id="banner",
        kind="thing",
        label="banner",
        phrase="a long celebration banner with silver paint",
        type="banner",
        owner=hero.id,
        meters={"flutter": 0.0, "tear": 0.0, "glow": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "pride": 0.0},
    ))

    world.say(f"On the ship {ship.name}, {params.hero_name} found a banner in the supply drawer.")
    world.say(f"It was {banner.phrase}, made for a celebration under {ship.space}.")
    world.say(f"{params.hero_name} wanted to hang the banner by {ship.outside} so everyone could see it.")
    world.say(f"But when {params.hero_name} tried, the thin cloth puffed and twisted in the airless gap.")

    banner.meters["flutter"] += 1.0
    banner.meters["tear"] += 1.0
    banner.memes["worry"] += 1.0
    hero.memes["disappointment"] = 1.0
    world.say("The banner would not stay flat, and one corner began to fray near the clip.")

    world.say(f"{params.helper_name} floated over and smiled. “Space needs a different kind of banner,” {params.helper_name} said.")
    world.say(f"Together they took the banner back inside to the work table on {ship.deck}.")

    # Transformation
    banner.label = "mission banner"
    banner.phrase = "a mission banner with shiny clips and glow tape"
    banner.meters["tear"] = 0.0
    banner.meters["flutter"] = 0.0
    banner.meters["glow"] = 1.0
    banner.memes["pride"] += 1.0
    hero.memes["hope"] = 1.0
    hero.memes["lesson"] = 1.0
    world.say(f"They gave the banner shiny clips, glow tape, and a stronger edge.")
    world.say(f"The plain cloth changed into {banner.phrase}, ready for the cold window and the drifting dark.")

    # Lesson learned
    world.say(f"{params.hero_name} learned that in space, a good idea must fit the place where it will live.")
    world.say(f"At last they fastened the mission banner beside {ship.outside}, and it shone like a small sunrise against the black.")

    world.facts.update(
        hero=hero,
        helper=helper,
        banner=banner,
        ship=ship,
        transformed=True,
        lesson=True,
    )

    prompts = [
        "Write a gentle space-adventure story about a child who wants to hang a banner in space and learns a better way.",
        f"Tell a short story where {params.hero_name} and {params.helper_name} transform a banner for life on a spaceship.",
        "Write a child-facing story with a clear problem, a transformation, and a lesson learned on a starship.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {params.hero_name} want to do with the banner at first?",
            answer=f"{params.hero_name} wanted to hang the banner outside by the airlock window so the whole ship could see it.",
        ),
        QAItem(
            question="Why did the banner need to change?",
            answer="It needed to change because the thin cloth fluttered and frayed in the airless gap, so it was not ready for space.",
        ),
        QAItem(
            question=f"What did {params.helper_name} help {params.hero_name} learn?",
            answer=f"{params.helper_name} helped {params.hero_name} learn that in space, a banner must be prepared for the place where it will hang.",
        ),
        QAItem(
            question="How did the banner end up at the end of the story?",
            answer="It became a mission banner with shiny clips and glow tape, and it shone safely beside the airlock window.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a banner?",
            answer="A banner is a long piece of cloth or paper with words or decorations on it, often used for celebrations.",
        ),
        QAItem(
            question="Why do things need clips in space?",
            answer="Clips help hold things in place when there is no windless, heavy air to keep them still.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful thing someone understands after trying, making a mistake, and then choosing a better way.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, ent in sample.world.entities.items():
            print(f"{key}: {ent.label} meters={ent.meters} memes={ent.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_hang/1.\n#show lesson_learned/1.\n#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for ship_name in SHIP_REGISTRY:
            params = StoryParams(ship=ship_name, hero_name=HERO_NAMES[0], helper_name=HELPER_NAMES[0])
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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
