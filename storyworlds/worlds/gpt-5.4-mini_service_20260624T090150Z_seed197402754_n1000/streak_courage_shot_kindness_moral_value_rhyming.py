#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/streak_courage_shot_kindness_moral_value_rhyming.py
==============================================================================================================================

A small rhyming storyworld about a child, a streak, a shot, and the kindness
that helps courage grow.

The seed tale behind this world is simple:
A child is on a streak of missed shots and feels small. A kind friend or coach
offers a gentle word and a fair turn. With courage, the child takes one more
shot, and it finally goes in. The ending image proves the change: the child
smiles, the streak changes, and kindness feels like the moral value that made
the brave moment possible.

This world is built as a compact classical simulation:
- typed entities with meters and memes
- state changes drive the prose
- a reasonableness gate rejects invalid pairings
- an inline ASP twin mirrors the Python gate
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    surface: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    streak_kind: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


THRESHOLD = 1.0

SETTINGS = {
    "gym": Setting(place="the gym", surface="court", affords={"basket"}),
    "yard": Setting(place="the school yard", surface="painted ground", affords={"basket"}),
    "park": Setting(place="the park court", surface="blacktop", affords={"basket"}),
}

ACTIONS = {
    "basket": {
        "verb": "take a shot",
        "gerund": "taking a shot",
        "miss": "miss another shot",
        "reward": "the ball swish through the hoop",
        "risk": "misses kept piling up",
    }
}

STREAKS = {
    "misses": {
        "label": "miss streak",
        "start": 3,
        "end": 0,
        "moral": "kindness can help courage grow",
    }
}

HELPERS = {
    "coach": "the coach",
    "friend": "a friend",
    "sibling": "an older sibling",
}

GIRL_NAMES = ["Mia", "Nora", "Lila", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Max", "Finn", "Noah", "Eli", "Theo"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- setting(P).
action_ok(A) :- action(A).
streak_ok(S) :- streak(S).

valid(P, A, S) :- place_ok(P), action_ok(A), streak_ok(S), can_play(P, A), can_have_streak(S).

% A reasonable story is one where the action can happen at the place and the
% streak is a real streak of misses.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("surface", pid, s.surface))
        for a in sorted(s.affords):
            lines.append(asp.fact("can_play", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for sid in STREAKS:
        lines.append(asp.fact("streak", sid))
        lines.append(asp.fact("can_have_streak", sid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for streak in STREAKS:
                combos.append((place, act, streak))
    return combos


def explain_rejection(place: str, activity: str, streak_kind: str) -> str:
    return (
        f"(No story: {activity} does not fit {place}, or the streak idea is not reasonable here.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"

def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"streak": float(STREAKS[params.streak_kind]["start"]), "shots": 0.0},
        memes={"courage": 0.0, "joy": 0.0, "shame": 1.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=HELPERS[params.helper],
        meters={"kindness": 1.0},
        memes={"warmth": 1.0},
    ))
    ball = world.add(Entity(
        id="Ball",
        kind="thing",
        type="ball",
        label="basketball",
        phrase="a small orange basketball",
        owner=hero.id,
    ))

    action = ACTIONS[params.activity]
    moral = STREAKS[params.streak_kind]["moral"]

    # Act 1
    world.say(f"At {setting.place}, {hero.id} felt low and blue,")
    world.say(f"{hero.pronoun().capitalize()} had a miss streak—three misses, not two.")
    world.say(f"The ball was round, and the hoop stood tall,")
    world.say(f"But {hero.id} feared one more miss would hurt at all.")

    world.para()

    # Act 2
    world.say(f"{helper.label} came near with a gentle grin,")
    world.say(f'"Try once more," {helper.pronoun()} said, "you may still win."')
    hero.memes["courage"] += 1.0
    helper.memes["warmth"] += 1.0
    hero.meters["streak"] += 1.0
    hero.meters["shots"] += 1.0
    world.say(f"That kind small word made courage appear,")
    world.say(f"And {hero.id} stood straighter, no longer in fear.")

    world.para()

    # Act 3
    world.say(f"{hero.id} took a breath and sent the ball high,")
    world.say(f"It spun in a swirl through the bright blue sky.")
    hero.meters["streak"] = 0.0
    hero.memes["joy"] += 2.0
    hero.memes["shame"] = 0.0
    world.say(f"Then swish went the shot, and the crowd gave a cheer,")
    world.say(f"The miss streak was gone, and the ending was clear.")
    world.say(f"Kindness was the lesson, a moral value true,")
    world.say(f"For brave little hearts can do brave things too.")

    world.facts.update(
        hero=hero,
        helper=helper,
        ball=ball,
        action=action,
        moral=moral,
        setting=setting,
        params=params,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short rhyming story for a child named {hero.id} who needs courage for one more shot.',
        f"Tell a gentle rhyming story where kindness helps {hero.id} end a miss streak.",
        f'Write a simple rhyming tale about a {hero.type} named {hero.id}, a shot, and the moral value of kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} try to take the shot?",
            answer=f"{hero.id} tried to take the shot at {setting.place}.",
        ),
        QAItem(
            question=f"How many misses did {hero.id} have before the kind words helped?",
            answer=f"{hero.id} had three misses before the kind words helped courage grow.",
        ),
        QAItem(
            question=f"What did {helper.label} say that helped {hero.id}?",
            answer=f"{helper.label} told {hero.id} to try once more, and that gentle kindness helped.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The miss streak ended, the shot went in, and the child felt brave and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward another person.",
        ),
        QAItem(
            question="What does courage mean?",
            answer="Courage means trying something hard even when you feel nervous.",
        ),
        QAItem(
            question="What is a shot in a game?",
            answer="A shot is when you try to send the ball toward the hoop or target.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: streak, courage, shot, kindness, moral value."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--streak-kind", dest="streak_kind", choices=STREAKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.streak_kind is None or c[2] == args.streak_kind)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, streak_kind = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(
        place=place,
        activity=activity,
        streak_kind=streak_kind,
        name=name,
        gender=gender,
        helper=helper,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, streak) combos:\n")
        for c in combos:
            print(f"  {c[0]:10} {c[1]:10} {c[2]:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="gym", activity="basket", streak_kind="misses", name="Mia", gender="girl", helper="friend"),
            StoryParams(place="park", activity="basket", streak_kind="misses", name="Leo", gender="boy", helper="coach"),
            StoryParams(place="yard", activity="basket", streak_kind="misses", name="Nora", gender="girl", helper="sibling"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
