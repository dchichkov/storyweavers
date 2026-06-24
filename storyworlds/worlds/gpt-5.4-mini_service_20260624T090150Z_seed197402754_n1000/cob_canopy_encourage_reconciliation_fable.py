#!/usr/bin/env python3
"""
A small fable-like story world about a shared cob, a canopy, and reconciliation.

Premise:
- Two small neighbors want the same cozy spot under a canopy.
- A corn cob becomes the cause of a split.
- A gentle helper encourages them to talk, share, and mend the hurt.

The world model tracks physical state in meters and feelings in memes so the
story prose is driven by simulated change rather than a frozen template.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "squirrel", "mouse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    type: str = "thing"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
    "meadow": Setting(place="the meadow", affords={"rest", "talk", "share"}),
    "orchard": Setting(place="the orchard", affords={"rest", "talk", "share"}),
    "lane": Setting(place="the sunny lane", affords={"rest", "talk", "share"}),
}

HEROES = {
    "fox": {"type": "fox", "label": "fox"},
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "squirrel": {"type": "squirrel", "label": "squirrel"},
    "mouse": {"type": "mouse", "label": "mouse"},
}

FRIENDS = {
    "crow": {"type": "crow", "label": "crow"},
    "hare": {"type": "hare", "label": "hare"},
    "mole": {"type": "mole", "label": "mole"},
    "robin": {"type": "robin", "label": "robin"},
}

HELPERS = {
    "turtle": {"type": "turtle", "label": "turtle"},
    "deer": {"type": "deer", "label": "deer"},
    "owl": {"type": "owl", "label": "owl"},
}

THINGS = {
    "cob": Thing(
        id="cob",
        label="cob",
        phrase="a golden corn cob",
    ),
    "canopy": Thing(
        id="canopy",
        label="canopy",
        phrase="a cool green canopy of leaves",
    ),
}

CURATED = [
    StoryParams(place="meadow", hero="fox", friend="crow", helper="owl"),
    StoryParams(place="orchard", hero="rabbit", friend="hare", helper="deer"),
    StoryParams(place="lane", hero="mouse", friend="mole", helper="turtle"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A reconciliation story is valid when a place supports sharing and talking.
valid_place(P) :- place(P), affords(P, talk), affords(P, share).

% The cob is the shared object that can cause a split.
shared_object(cob).

% The canopy is the shaded place where the argument starts.
shared_place(canopy).

% Encourage is the helper action that leads to reconciliation.
help_word(encourage).

valid_story(P, H, F, U) :-
    valid_place(P),
    hero(H),
    friend(F),
    helper(U).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import per contract

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    for uid in HELPERS:
        lines.append(asp.fact("helper", uid))
    lines.append(asp.fact("shared_object", "cob"))
    lines.append(asp.fact("shared_place", "canopy"))
    lines.append(asp.fact("help_word", "encourage"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, h, f, u) for p in SETTINGS for h in HEROES for f in FRIENDS for u in HELPERS)
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python registry cartesian product ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero_cfg = HEROES[params.hero]
    friend_cfg = FRIENDS[params.friend]
    helper_cfg = HELPERS[params.helper]

    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg["type"], label=hero_cfg["label"]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_cfg["type"], label=friend_cfg["label"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg["type"], label=helper_cfg["label"]))
    cob = world.add(Entity(id="cob", label="cob", phrase="a golden corn cob"))
    canopy = world.add(Entity(id="canopy", label="canopy", phrase="a cool green canopy of leaves"))

    world.facts.update(hero=hero, friend=friend, helper=helper, cob=cob, canopy=canopy)
    return world


def open_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    canopy: Entity = world.facts["canopy"]
    cob: Entity = world.facts["cob"]

    world.say(
        f"In {world.setting.place}, a little {hero.label} and a little {friend.label} "
        f"liked to rest beneath the {canopy.label}."
    )
    world.say(
        f"They found a bright {cob.label} there one warm morning, and both of them "
        f"wanted to keep it."
    )


def start_argument(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    cob: Entity = world.facts["cob"]

    hero.memes["want"] = 1
    friend.memes["want"] = 1
    hero.memes["stubborn"] = 1
    friend.memes["stubborn"] = 1
    hero.memes["hurt"] = 1
    friend.memes["hurt"] = 1

    world.para()
    world.say(
        f"{hero.label} reached for the {cob.label}, and {friend.label} reached too. "
        f"Each small friend thought the cob should be theirs."
    )
    world.say(
        f"Their voices grew sharp, and the shade under the canopy felt less peaceful."
    )


def encourage(world: World) -> None:
    helper: Entity = world.facts["helper"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    cob: Entity = world.facts["cob"]

    helper.memes["kind"] = 1
    world.para()
    world.say(
        f"Then {helper.label} came by and said, \"Please, children, choose a kinder way. "
        f"Sharing can make a small thing grow sweet.\""
    )
    world.say(
        f"{helper.label} encouraged them to sit together, breathe slowly, and look at the {cob.label} again."
    )


def reconcile(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    cob: Entity = world.facts["cob"]
    canopy: Entity = world.facts["canopy"]

    if "reconciled" in world.fired:
        return
    world.fired.add("reconciled")

    hero.memes["hurt"] = 0
    friend.memes["hurt"] = 0
    hero.memes["peace"] = 1
    friend.memes["peace"] = 1
    cob.owner = "shared"

    world.para()
    world.say(
        f"The two friends listened. They decided to split the {cob.label} and share it kindly."
    )
    world.say(
        f"After that, they sat side by side under the {canopy.label}, and the day felt gentle again."
    )


def tell(world: World) -> None:
    open_story(world)
    start_argument(world)
    encourage(world)
    reconcile(world)
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fable about a cob, a canopy, and a gentle reconciliation.',
        f"Tell a child-friendly story in {world.setting.place} where two small animals argue over a cob, then encourage them to make peace.",
        "Write a simple moral tale that uses the words cob, canopy, and encourage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    helper: Entity = world.facts["helper"]
    cob: Entity = world.facts["cob"]
    canopy: Entity = world.facts["canopy"]

    return [
        QAItem(
            question=f"Who were the little friends in the story?",
            answer=f"The little friends were the {hero.label} and the {friend.label}. They met under the {canopy.label} in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the two friends want at the same time?",
            answer=f"They both wanted the {cob.label}. That is why their small argument began.",
        ),
        QAItem(
            question=f"Who helped them calm down?",
            answer=f"The {helper.label} helped them calm down and encouraged them to share kindly.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the friends made peace and shared the {cob.label}, so they could rest happily together under the {canopy.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canopy?",
            answer="A canopy is a covering over something. In a forest or orchard, the leaves high above can make a shady canopy.",
        ),
        QAItem(
            question="What is a cob?",
            answer="A cob is the hard middle part of an ear of corn. People can hold the cob after the kernels are taken off.",
        ),
        QAItem(
            question="What does encourage mean?",
            answer="To encourage someone means to help them feel braver, kinder, or ready to try a good choice.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement and becoming friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(parts)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about cob, canopy, and reconciliation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    place = args.place or rng.choice(sorted(SETTINGS))
    hero = args.hero or rng.choice(sorted(HEROES))
    friend = args.friend or rng.choice(sorted(FRIENDS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    if friend == helper:
        helper = rng.choice([h for h in sorted(HELPERS) if h != friend])
    if hero == friend:
        friend = rng.choice([f for f in sorted(FRIENDS) if f != hero])
    return StoryParams(place=place, hero=hero, friend=friend, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for t in stories:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
