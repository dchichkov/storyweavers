#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/service_quest_sound_effects_mystery_to_solve.py
=================================================================================================

A small folk-tale story world about a village service, a quest, and a mystery
revealed through sound effects.

Premise:
- A kind helper offers a village service.
- A strange sound is heard each dawn.
- A child sets out on a quest to solve the mystery.
- The answer changes the service for everyone.

This world is intentionally small and constraint-checked: the mystery must be
plausible, the quest must have a clear turn, and the ending must prove that the
world changed.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    service_name: str
    daily_task: str
    sound: str
    mystery_source: str
    clue_place: str


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    "mill": Setting(
        place="the old mill",
        service_name="water service",
        daily_task="carry water",
        sound="swish-swish",
        mystery_source="the mill wheel",
        clue_place="by the river stones",
    ),
    "bakery": Setting(
        place="the village bakery",
        service_name="bread service",
        daily_task="carry warm loaves",
        sound="thump-thump",
        mystery_source="the flour sack room",
        clue_place="behind the oven",
    ),
    "well": Setting(
        place="the village well",
        service_name="bucket service",
        daily_task="lift pails",
        sound="clang-clink",
        mystery_source="the pulley rope",
        clue_place="on the well lid",
    ),
    "barn": Setting(
        place="the red barn",
        service_name="feed service",
        daily_task="carry oats",
        sound="rustle-rustle",
        mystery_source="the hay loft",
        clue_place="under the hay cart",
    ),
}

HEROES = [
    ("Mira", "girl"),
    ("Niko", "boy"),
    ("Tala", "girl"),
    ("Oren", "boy"),
    ("Pip", "boy"),
    ("Lina", "girl"),
]

HELPERS = [
    ("Grandma Brin", "woman"),
    ("Old Jory", "man"),
    ("Aunt Sela", "woman"),
    ("Uncle Bram", "man"),
]

TRAITS = ["kind", "curious", "brave", "gentle", "quick"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def hero_desc(hero: Entity) -> str:
    trait = next((t for t in hero.meters.get("traits", []) if t), "")
    return f"little {trait} {hero.type}" if trait else f"little {hero.type}"


def opening(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there lived {hero.id}, "
        f"a small child who liked to help with the {world.setting.service_name}."
    )
    world.say(
        f"{helper.id} kept the service going each morning, and the whole village "
        f"knew {helper.pronoun('subject')} could be trusted."
    )


def service_and_sound(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["helpful"] = hero.memes.get("helpful", 0) + 1
    world.say(
        f"Each dawn, the work began with {world.setting.daily_task}, and the air "
        f"would fill with {world.setting.sound}."
    )
    world.say(
        f"But one morning, the sound came again and again, even after the work had stopped."
    )


def mystery_call(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} listened hard. \"What makes that {world.setting.sound} sound?\" "
        f"{hero.pronoun('subject')} asked."
    )
    world.say(
        f"The villagers only shook their heads, so {hero.id} set out on a quest to solve the mystery."
    )


def quest_steps(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} followed the sound to {world.setting.clue_place}, where the crumbs of the day had gathered."
    )
    world.say(
        f"There {hero.pronoun('subject')} found a small sign: the trouble came from {world.setting.mystery_source}."
    )


def reveal(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    world.say(
        f"{hero.id} peered closer and saw the truth at last: the {world.setting.mystery_source} "
        f"was rubbing against the wood and making the {world.setting.sound} sound."
    )
    world.say(
        f"{helper.id} smiled, because now the village knew what had been hiding in plain sight."
    )


def fix_service(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.meters["work_done"] = helper.meters.get("work_done", 0) + 1
    world.say(
        f"Together, they wrapped the noisy part with a soft cloth and set it right."
    )
    world.say(
        f"After that, the service could continue, and the morning sounded calm again."
    )


def ending(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"From then on, {world.setting.place} woke to a gentle hush, and {hero.id} was known "
        f"as the child who found the answer by following the sound."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    hero.meters["traits"] = [random.choice(TRAITS)]
    helper.meters["service"] = 1

    opening(world, hero, helper)
    world.para()
    service_and_sound(world, hero, helper)
    mystery_call(world, hero)
    world.para()
    quest_steps(world, hero)
    reveal(world, hero, helper)
    fix_service(world, hero, helper)
    world.para()
    ending(world, hero, helper)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "setting": setting,
        "sound": setting.sound,
        "source": setting.mystery_source,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk tale about {f['setting'].place} where a child hears {f['sound']} and goes on a quest.",
        f"Tell a gentle mystery story set at {f['setting'].place} about the village {f['setting'].service_name}.",
        f"Write a short story for children in which a sound effect leads to a mystery being solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What was the child trying to do at {setting.place}?",
            answer=f"{hero.id} was helping with the {setting.service_name} by {setting.daily_task}.",
        ),
        QAItem(
            question=f"What strange sound kept happening?",
            answer=f"The strange sound was {setting.sound}.",
        ),
        QAItem(
            question=f"What was the mystery really about?",
            answer=f"The mystery was caused by {setting.mystery_source}, which was rubbing and making the noise.",
        ),
        QAItem(
            question=f"How did {hero.id} help solve the problem?",
            answer=f"{hero.id} followed the clue, found the noisy part, and helped fix it with {helper.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    setting: Setting = world.facts["setting"]
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to find something, solve a problem, or learn an answer.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises, like swishes or clangs, that help tell what is happening.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people want to figure out.",
        ),
        QAItem(
            question=f"Why do people at {setting.place} need a service?",
            answer=f"They need the {setting.service_name} so useful work gets done for the village.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- place(S).
hero(H) :- person(H).
helper(K) :- person(K).

mystery(M) :- sound_source(M).
quest(Q) :- quest_word(Q).

solved(S, H) :- setting(S), hero(H), sound(SN), source(M), follows_clue(H, M), fixes(H, M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        lines.append(asp.fact("sound", setting.sound))
        lines.append(asp.fact("sound_source", setting.mystery_source))
        lines.append(asp.fact("quest_word", "quest"))
        lines.append(asp.fact("service", setting.service_name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import as required
    import asp
    # This world's Python gate is simple: every registered setting yields one
    # story because each has a sound source and a fix.
    py = set(SETTINGS)
    model = asp.one_model(asp_program("#show place/1."))
    cl = set(a[0] for a in asp.atoms(model, "place"))
    if py == cl:
        print(f"OK: clingo gate matches settings registry ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and python registries:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale story world: service, quest, sound effects, mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero_name, hero_type = (args.name, "girl") if args.name else rng.choice(HEROES)
    helper_name, helper_type = (args.helper, "woman") if args.helper else rng.choice(HELPERS)
    return StoryParams(
        setting=setting,
        hero_name=hero_name or rng.choice([n for n, _ in HEROES]),
        hero_type=hero_type,
        helper_name=helper_name or rng.choice([n for n, _ in HELPERS]),
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:12} ({e.type}) meters={e.meters} memes={e.memes}")
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
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show place/1."))
        places = sorted(set(asp.atoms(model, "place")))
        for p in places:
            print(p[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = []
        for i, setting in enumerate(SETTINGS):
            params = StoryParams(
                setting=setting,
                hero_name=HEROES[i % len(HEROES)][0],
                hero_type=HEROES[i % len(HEROES)][1],
                helper_name=HELPERS[i % len(HELPERS)][0],
                helper_type=HELPERS[i % len(HELPERS)][1],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.setting} / {p.hero_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
