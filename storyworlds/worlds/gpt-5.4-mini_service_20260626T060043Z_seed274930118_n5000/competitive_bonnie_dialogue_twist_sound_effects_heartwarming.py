#!/usr/bin/env python3
"""
storyworlds/worlds/competitive_bonnie_dialogue_twist_sound_effects_heartwarming.py
===================================================================================

A tiny heartwarming storyworld about a competitive little bonnie creature
trying to win a small contest, only to discover that helping can feel better
than winning.

Premise:
- A child or small character is excited about a friendly competition.
- The competition includes dialogue, sound effects, and a twist.
- The ending stays warm and gentle: the character learns something kind.

World model:
- Characters have physical meters and emotional memes.
- The competition can create stress, pride, disappointment, and delight.
- A twist can reveal that the most important prize is not the medal but the
  friendship, the applause, or the shared success.

The story is generated from simulated state rather than from a frozen template.
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
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "speed": 0.0,
                "shine": 0.0,
                "tired": 0.0,
                "mess": 0.0,
            }
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "pride": 0.0,
                "worry": 0.0,
                "kindness": 0.0,
                "competition": 0.0,
                "surprise": 0.0,
                "love": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "bonnie"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Contest:
    name: str
    activity: str
    sound: str
    prize: str
    twist: str


@dataclass
class World:
    contest: Contest
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    contest: str
    hero_name: str
    hero_type: str
    rival_name: str
    rival_type: str
    seed: Optional[int] = None


CONTESTS = {
    "cake": Contest(
        name="the berry cake contest",
        activity="decorate cakes with berries and cream",
        sound="squelch",
        prize="a glittery ribbon",
        twist="the rival's cake cracked, so the hero offered their berries",
    ),
    "choir": Contest(
        name="the little choir contest",
        activity="sing the loudest and clearest note",
        sound="la-la-LA",
        prize="a gold star pin",
        twist="the hero forgot a line, but the rival whispered it kindly",
    ),
    "kite": Contest(
        name="the kite contest",
        activity="fly the brightest kite",
        sound="whoooosh",
        prize="a blue wind medal",
        twist="the wind tangled both kites together, and they flew best as a pair",
    ),
    "seedlings": Contest(
        name="the sunflower seedling contest",
        activity="grow the straightest little sunflower",
        sound="sprinkle",
        prize="a tiny silver cup",
        twist="the hero's seedling leaned over, and the rival shared a sturdy stick",
    ),
}

HERO_NAMES = ["Bonnie", "Nora", "Mina", "Tilly", "Pippa", "Lulu", "Cora"]
RIVAL_NAMES = ["Jules", "Ivy", "Milo", "Otis", "Bea", "Robin", "Sunny"]
HERO_TYPES = ["girl", "bonnie"]
RIVAL_TYPES = ["girl", "boy", "bonnie"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def _feel_competitive(world: World) -> None:
    hero = world.get("hero")
    hero.memes["competition"] += 1
    hero.memes["pride"] += 0.5


def _excited_noise(world: World, sound: str) -> None:
    world.facts["sound"] = sound


def _twist(world: World) -> None:
    hero = world.get("hero")
    rival = world.get("rival")
    hero.memes["surprise"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    hero.memes["kindness"] += 1
    rival.memes["kindness"] += 1


def _resolve(world: World) -> None:
    hero = world.get("hero")
    rival = world.get("rival")
    hero.memes["joy"] += 2
    hero.memes["love"] += 1
    rival.memes["joy"] += 1
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(contest: Contest, hero_name: str, hero_type: str, rival_name: str, rival_type: str) -> World:
    world = World(contest=contest)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=["competitive", "bonnie"]))
    rival = world.add(Entity(id="rival", kind="character", type=rival_type, label=rival_name, traits=["kind"]))
    world.facts.update(hero=hero, rival=rival, contest=contest)

    # Act 1: setup
    world.say(
        f"{hero.label} was a competitive bonnie little {hero.type} who loved {contest.name}."
    )
    world.say(
        f"{hero.label} wanted to {contest.activity}, and {hero.pronoun()} practiced with a serious face."
    )
    world.say(
        f'"I can win this!" {hero.label} said. "{contest.sound}!"'
    )
    _feel_competitive(world)
    _excited_noise(world, contest.sound)

    # Act 2: tension
    world.para()
    world.say(
        f"At the contest table, {hero.label} and {rival.label} stood side by side."
    )
    world.say(
        f'"Ready?" asked {rival.label}. "Ready!" said {hero.label}.'
    )
    world.say(
        f'Then came the cheerful sound effect: {contest.sound}! It made {hero.label} grin, but also made {hero.pronoun("possessive")} tummy flutter.'
    )
    hero.memes["worry"] += 1
    hero.meters["tired"] += 0.5

    # Twist
    world.para()
    world.say(
        f"Twist: {contest.twist}."
    )
    _twist(world)
    if "shared" in contest.twist or "offered" in contest.twist or "whispered" in contest.twist:
        world.say(
            f'"Oh!" said {hero.label}. "You helped me."'
        )
    else:
        world.say(
            f'"Oh!" said {hero.label}. "We can do this together."'
        )

    # Act 3: warm ending
    world.para()
    world.say(
        f"{hero.label} took a breath, smiled at {rival.label}, and shared the prize feeling instead of grabbing it."
    )
    world.say(
        f"Together they finished the contest, and the judges clapped: {contest.sound}!"
    )
    _resolve(world)
    world.say(
        f"{hero.label} left with {contest.prize}, but the nicest part was how warm {hero.pronoun()} felt inside."
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    c = world.facts["contest"]
    hero = world.facts["hero"]
    rival = world.facts["rival"]
    return [
        f"Write a heartwarming story about {hero.label}, a competitive bonnie little {hero.type}, at {c.name}.",
        f"Tell a child-friendly story with dialogue, a sound effect, and a twist where {hero.label} learns kindness from {rival.label}.",
        f"Write a gentle contest story where the sound '{c.sound}' helps two children become friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["contest"]
    hero = world.facts["hero"]
    rival = world.facts["rival"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is about {hero.label}, a competitive bonnie little {hero.type}."
        ),
        QAItem(
            question=f"What contest did {hero.label} enter?",
            answer=f"{hero.label} entered {c.name}, where the goal was to {c.activity}."
        ),
        QAItem(
            question=f"What sound effect was heard during the contest?",
            answer=f"The story used the sound effect '{c.sound}'."
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {c.twist}."
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt warm, happy, and kinder after sharing the moment with {rival.label}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be competitive?",
            answer="Being competitive means wanting to do well and sometimes wanting to win."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the story go in a new direction."
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to make moments feel lively, funny, or exciting."
        ),
        QAItem(
            question="What does heartwarming mean?",
            answer="Heartwarming means it makes you feel soft, kind, and happy inside."
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% contest(C), hero(H), rival(R), sound(C,S), twist(C,T), competitive(H), bonnie(H)

competitive(H) :- hero(H).
bonnie(H) :- hero(H).

excited(H) :- competitive(H).
surprised(H) :- twist_seen(C), hero(H), contest(C).

heartwarming(H) :- hero(H), kind_end(H), shared_prize(H).

kind_end(H) :- twist_helped(H).
twist_helped(H) :- twist_type(shared_help).
twist_helped(H) :- twist_type(whisper_help).
twist_helped(H) :- twist_type(teamwork).

acceptable_story(H) :- competitive(H), bonnie(H), excited(H), surprised(H), heartwarming(H).

#show acceptable_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("rival", "rival"),
        asp.fact("contest", "contest"),
        asp.fact("twist_type", "shared_help"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show acceptable_story/1."))
    ok = bool(asp.atoms(model, "acceptable_story"))
    if ok:
        print("OK: ASP twin accepts the heartwarming competitive bonnie story shape.")
        return 0
    print("MISMATCH: ASP twin rejected the generated story shape.")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming competitive bonnie contest storyworld.")
    ap.add_argument("--contest", choices=sorted(CONTESTS))
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--rival-name", choices=RIVAL_NAMES)
    ap.add_argument("--rival-type", choices=RIVAL_TYPES)
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
    contest = args.contest or rng.choice(sorted(CONTESTS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    rival_name = args.rival_name or rng.choice([n for n in RIVAL_NAMES if n != hero_name])
    rival_type = args.rival_type or rng.choice(RIVAL_TYPES)
    if hero_name == rival_name:
        raise StoryError("The hero and rival need different names.")
    if hero_type not in HERO_TYPES:
        raise StoryError("Invalid hero type.")
    return StoryParams(
        contest=contest,
        hero_name=hero_name,
        hero_type=hero_type,
        rival_name=rival_name,
        rival_type=rival_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CONTESTS[params.contest],
        params.hero_name,
        params.hero_type,
        params.rival_name,
        params.rival_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:5} ({e.type:7}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        print(asp_program("#show acceptable_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        print(asp_program("#show acceptable_story/1."))
        return

    samples: list[StorySample] = []
    if args.all:
        for contest in sorted(CONTESTS):
            params = StoryParams(
                contest=contest,
                hero_name=HERO_NAMES[0],
                hero_type="bonnie",
                rival_name=RIVAL_NAMES[0],
                rival_type="girl",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
