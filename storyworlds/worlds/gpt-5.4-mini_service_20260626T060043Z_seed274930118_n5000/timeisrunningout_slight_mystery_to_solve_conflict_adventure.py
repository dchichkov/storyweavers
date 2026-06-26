#!/usr/bin/env python3
"""
Storyworld: a tiny adventure mystery with a clock, a conflict, and a small clue.

Premise:
A child explorer and a trusted companion are heading out on a short quest when
something important goes missing right as time starts running out. The pair must
solve a slight mystery before dusk, and the tension between them softens once
the clue is found and the path forward becomes clear.

The story is intentionally small and classical:
- a few typed entities
- physical meters and emotional memes
- a state-driven turn from worry to discovery
- a friendly, child-facing ending image
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
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    clue_spot: str
    weather: str = "clear"
    time_limit: str = "sunset"


@dataclass
class Mystery:
    id: str
    missing: str
    missing_label: str
    likely_place: str
    slight: bool = True


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    ally_name: str
    ally_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "forest_path": Setting(place="the forest path", clue_spot="the mossy stump", weather="warm", time_limit="sunset"),
    "harbor": Setting(place="the harbor", clue_spot="the old rope pile", weather="windy", time_limit="tide change"),
    "ruins": Setting(place="the stone ruins", clue_spot="the broken arch", weather="golden", time_limit="dark"),
}

MYSTERIES = {
    "lantern_key": Mystery(
        id="lantern_key",
        missing="a tiny brass key",
        missing_label="tiny brass key",
        likely_place="the old rope pile",
        slight=True,
    ),
    "map_corner": Mystery(
        id="map_corner",
        missing="the torn corner of a map",
        missing_label="torn map corner",
        likely_place="the mossy stump",
        slight=True,
    ),
    "blue_compass": Mystery(
        id="blue_compass",
        missing="a blue compass",
        missing_label="blue compass",
        likely_place="the broken arch",
        slight=True,
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lila", "Arlo", "Nia", "Perry"]
ALLY_NAMES = ["Jo", "Moss", "Pip", "Rae", "Glen", "Suri"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def reasonableness_gate(setting: str, mystery: str) -> None:
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if not MYSTERIES[mystery].slight:
        raise StoryError("The mystery must be slight enough for a short story.")
    if setting == "forest_path" and mystery == "blue_compass":
        return
    if setting == "harbor" and mystery == "lantern_key":
        return
    if setting == "ruins" and mystery == "map_corner":
        return
    # allow all, but keep the pairings modest and story-like
    return


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"time_pressure": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "conflict": 0.0},
    ))
    ally = world.add(Entity(
        id=params.ally_name,
        kind="character",
        type=params.ally_type,
        meters={"time_pressure": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "conflict": 0.0},
    ))
    clue = world.add(Entity(
        id=mystery.id,
        kind="thing",
        type="clue",
        label=mystery.missing_label,
        phrase=mystery.missing,
        owner=hero.id,
        hidden=True,
        meters={"significance": 1.0},
    ))

    world.facts.update(hero=hero, ally=ally, clue=clue, mystery=mystery)
    return world


def _set_tension(world: World, amount: float) -> None:
    for e in world.entities.values():
        if e.kind == "character":
            e.meters["time_pressure"] += amount
            e.memes["worry"] += amount / 2.0


def _start_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    mystery: Mystery = world.facts["mystery"]
    setting = world.setting.place

    world.say(
        f"{hero.id} and {ally.id} set off along {setting} just as the light began to thin."
    )
    world.say(
        f"They were hunting for {mystery.missing}, because without it the little expedition could not move on."
    )
    world.say(
        f"Their bags were ready, but the clock in the sky said time was running out."
    )


def _conflict(world: World) -> None:
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    mystery: Mystery = world.facts["mystery"]

    _set_tension(world, 1.0)
    hero.memes["conflict"] += 1.0
    ally.memes["conflict"] += 1.0
    world.say(
        f"{ally.id} wanted to check the wrong path first, but {hero.id} thought the clue had to be near {world.setting.clue_spot}."
    )
    world.say(
        f"They argued in small voices, and the trail felt narrower with every step."
    )
    world.say(
        f"Then {hero.id} noticed a slight shine near {world.setting.clue_spot}: a bit of {mystery.missing_label} was caught under a leaf."
    )


def _solve(world: World) -> None:
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    clue: Entity = world.facts["clue"]

    clue.hidden = False
    hero.memes["conflict"] = 0.0
    ally.memes["conflict"] = 0.0
    hero.memes["joy"] += 1.0
    ally.memes["joy"] += 1.0
    hero.meters["time_pressure"] = max(0.0, hero.meters["time_pressure"] - 1.0)
    ally.meters["time_pressure"] = max(0.0, ally.meters["time_pressure"] - 1.0)

    world.say(
        f"{hero.id} lifted the leaf, and there it was: {clue.phrase} hiding exactly where the glint had promised."
    )
    world.say(
        f"{ally.id} smiled, because the answer was simple after all, and the little mystery was solved."
    )
    world.say(
        f"With the clue in hand, they hurried forward together, lighter than before, while the sky turned soft and gold."
    )


def tell_story(world: World) -> World:
    _start_story(world)
    world.say("")
    _conflict(world)
    world.say("")
    _solve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        f"Write a short adventure mystery for a child where a tiny clue like {mystery.missing} must be found before sunset.",
        f"Tell a story about two friends who disagree, notice a slight clue, and solve a mystery just in time.",
        f"Write a gentle, exciting tale with timeisrunningout energy and a small mystery to solve in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    mystery: Mystery = world.facts["mystery"]
    setting = world.setting.place
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id} and {ally.id}, two friends on a little adventure at {setting}.",
        ),
        QAItem(
            question=f"What was the mystery to solve?",
            answer=f"They needed to find {mystery.missing} before the day ran out.",
        ),
        QAItem(
            question=f"Why did the two friends argue?",
            answer=f"They disagreed about where the clue would be, which caused a small conflict before they looked carefully and solved it.",
        ),
        QAItem(
            question=f"What showed that time was running out?",
            answer="The sky was getting darker, so they had to solve the slight mystery quickly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="What does it mean when time is running out?",
            answer="It means there is not much time left to finish something.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is when people disagree or want different things.",
        ),
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting trip or experience with something new to do or find.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== Prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} hidden={e.hidden} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


@dataclass
class Resolved:
    params: StoryParams


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny adventure mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--ally-name")
    ap.add_argument("--ally-type", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    reasonableness_gate(setting, mystery)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    ally_type = args.ally_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    ally_name = args.ally_name or rng.choice([n for n in ALLY_NAMES if n != hero_name])
    if hero_name == ally_name:
        ally_name = rng.choice([n for n in ALLY_NAMES if n != hero_name])
    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        ally_name=ally_name,
        ally_type=ally_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


ASP_RULES = r"""
setting(forest_path).
setting(harbor).
setting(ruins).

mystery(lantern_key).
mystery(map_corner).
mystery(blue_compass).

slight(lantern_key).
slight(map_corner).
slight(blue_compass).

compatible(S, M) :- setting(S), mystery(M), slight(M).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
        if MYSTERIES[m].slight:
            lines.append(asp.fact("slight", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(setting="forest_path", mystery="map_corner", hero_name="Mina", hero_type="girl", ally_name="Pip", ally_type="boy"),
    StoryParams(setting="harbor", mystery="lantern_key", hero_name="Toby", hero_type="boy", ally_name="Rae", ally_type="girl"),
    StoryParams(setting="ruins", mystery="blue_compass", hero_name="Lila", hero_type="girl", ally_name="Moss", ally_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/mystery pairs:")
        for s, m in combos:
            print(f"  {s:12} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
