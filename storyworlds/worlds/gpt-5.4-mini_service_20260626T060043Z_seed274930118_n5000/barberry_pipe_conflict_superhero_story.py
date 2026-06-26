#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/barberry_pipe_conflict_superhero_story.py
===============================================================================================================

A standalone storyworld for a small superhero-style conflict tale.

Premise:
- A young superhero hears that a barberry bush has tangled itself around a pipe.
- The pipe matters because it carries water to a little neighborhood.
- The hero wants to solve the problem fast, but the thorny bush resists.

The world model tracks:
- physical meters: damage, blockage, danger, progress
- emotional memes: confidence, fear, conflict, relief, pride

The story is generated from simulated state, not from a frozen template.
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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    vibe: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    seed: Optional[int] = None


SETTINGS = {
    "city_lane": Setting(place="the little city lane", vibe="busy"),
    "rooftop": Setting(place="the rooftop garden", vibe="windy"),
    "courtyard": Setting(place="the sunny courtyard", vibe="quiet"),
}

HERO_TYPES = ["boy", "girl"]
HERO_NAMES = ["Nova", "Spark", "Pip", "Mira", "Jett", "Luna"]
SIDEKICK_NAMES = ["Patch", "Moss", "Zing", "Comet"]
TRAITS = ["brave", "quick", "kind", "bold"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.setting)
        import copy

        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"progress": 0.0, "damage": 0.0},
        memes={"confidence": 1.0, "conflict": 0.0, "pride": 1.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type="sidekick",
        label=params.sidekick_name,
        meters={"help": 0.0},
        memes={"trust": 1.0},
    ))
    barberry = world.add(Entity(
        id="barberry",
        kind="thing",
        type="barberry",
        label="barberry bush",
        meters={"thorns": 3.0, "tangle": 2.0, "damage": 0.0},
        memes={"stubborn": 1.0},
    ))
    pipe = world.add(Entity(
        id="pipe",
        kind="thing",
        type="pipe",
        label="pipe",
        meters={"blockage": 2.0, "leak": 0.0, "clean": 0.0},
        caretaker="town",
    ))
    town = world.add(Entity(
        id="town",
        kind="thing",
        type="town",
        label="the town",
        meters={"thirst": 2.0},
        memes={"worry": 1.0},
    ))
    world.facts.update(hero=hero, sidekick=sidekick, barberry=barberry, pipe=pipe, town=town)
    return world


def _narrate_conflict(world: World, hero: Entity, barberry: Entity, pipe: Entity) -> None:
    if hero.memes.get("conflict", 0.0) < THRESHOLD:
        hero.memes["conflict"] = 1.0
    world.say(
        f"{hero.id} flew to {world.setting.place} when a barberry bush wrapped its thorny arms around a pipe."
    )
    world.say(
        f"The pipe had to stay clear, because it carried water for the little town, and the town was already feeling thirsty."
    )
    world.say(
        f"{hero.id} wanted to pull the bush free at once, but the thorns looked sharp enough to scratch a cape."
    )
    world.say(
        f"That made the mission feel bigger than a quick snap-and-go rescue."
    )


def _apply_tension(world: World, hero: Entity, barberry: Entity, pipe: Entity, sidekick: Entity) -> None:
    hero.memes["confidence"] = max(0.0, hero.memes.get("confidence", 0.0) - 0.25)
    barberry.meters["damage"] += 0.0
    pipe.meters["blockage"] += 1.0
    sidekick.meters["help"] += 1.0
    world.say(
        f"{sidekick.id} pointed to the tight tangle and said it would be smarter to use a tool than bare hands."
    )
    world.say(
        f"{hero.id} nodded. {hero.pronoun('subject').capitalize()} could feel the thorny conflict, but {hero.pronoun('subject')} also knew a superhero uses a plan."
    )


def _resolve(world: World, hero: Entity, barberry: Entity, pipe: Entity, sidekick: Entity) -> None:
    pipe.meters["blockage"] = max(0.0, pipe.meters.get("blockage", 0.0) - 2.0)
    pipe.meters["clean"] = 1.0
    hero.meters["progress"] = 1.0
    hero.memes["conflict"] = 0.0
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    barberry.meters["tangle"] = 0.0
    world.say(
        f"{hero.id} used a long hooked tool to lift the barberry vines away, one careful twist at a time."
    )
    world.say(
        f"{sidekick.id} held the lamp steady while the last thorn slid off the pipe without a scrape."
    )
    world.say(
        f"At last, water rushed through the pipe again, and the town could breathe easier."
    )
    world.say(
        f"{hero.id} smiled under the cape as the barberry bush settled back into the soil, no longer wrapped around the pipe."
    )


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    barberry: Entity = world.facts["barberry"]  # type: ignore[assignment]
    pipe: Entity = world.facts["pipe"]  # type: ignore[assignment]

    world.say(
        f"On a {world.setting.vibe} day in {world.setting.place}, {hero.id} was flying patrol with {sidekick.id}."
    )
    world.say(
        f"{hero.id} was a {params.hero_type} superhero who liked helping small places with big problems."
    )
    world.para()

    _narrate_conflict(world, hero, barberry, pipe)
    world.para()

    _apply_tension(world, hero, barberry, pipe, sidekick)
    world.para()

    _resolve(world, hero, barberry, pipe, sidekick)

    world.facts["resolved"] = True
    return world


def asp_facts() -> str:
    import asp

    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for sk in SIDEKICK_NAMES:
        lines.append(asp.fact("sidekick_name", sk))
    lines.append(asp.fact("thing", "barberry"))
    lines.append(asp.fact("thing", "pipe"))
    lines.append(asp.fact("conflict_theme", "barberry", "pipe"))
    return "\n".join(lines)


ASP_RULES = r"""
% A valid superhero conflict story needs both a barberry and a pipe.
needs_conflict(barberry, pipe).

valid_story(P) :- place(P), needs_conflict(barberry, pipe).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted({args[0] for args in asp.atoms(model, "valid_story")})


def asp_verify() -> int:
    py = set(SETTINGS.keys())
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid places.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(cl - py))
    print("  only in Python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f'Write a superhero story for a child that includes the words "barberry" and "pipe".',
        f"Tell a short story about {hero.id} solving a conflict at {world.setting.place} with a barberry bush and a pipe.",
        f"Write a brave rescue story where a superhero uses patience instead of rushing into a thorny problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    barberry: Entity = world.facts["barberry"]  # type: ignore[assignment]
    pipe: Entity = world.facts["pipe"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a superhero who worked with {sidekick.id}."
        ),
        QAItem(
            question=f"What caused the conflict in the story?",
            answer=f"A thorny {barberry.label} got tangled around the {pipe.label} and blocked the water."
        ),
        QAItem(
            question=f"How did the hero solve the problem?",
            answer=f"{hero.id} used a careful hooked tool and {sidekick.id} helped hold the light until the pipe was clear."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barberry?",
            answer="A barberry is a shrub with small leaves and sharp thorns on its branches."
        ),
        QAItem(
            question="What does a pipe do?",
            answer="A pipe can carry water or air from one place to another."
        ),
        QAItem(
            question="Why do superheroes use tools sometimes?",
            answer="Superheroes use tools when a problem is too risky to solve with bare hands."
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


def valid_places() -> list[str]:
    return list(SETTINGS.keys())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with a barberry-pipe conflict.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    sidekick_name = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    if hero_name == sidekick_name:
        raise StoryError("Hero and sidekick must have different names.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_valid_places()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        combos = [
            StoryParams(place=p, hero_name=h, hero_type=t, sidekick_name=s)
            for p in SETTINGS
            for h in HERO_NAMES[:2]
            for t in HERO_TYPES
            for s in SIDEKICK_NAMES[:2]
            if h != s
        ]
        samples = [generate(p) for p in combos[: max(1, args.n)]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
