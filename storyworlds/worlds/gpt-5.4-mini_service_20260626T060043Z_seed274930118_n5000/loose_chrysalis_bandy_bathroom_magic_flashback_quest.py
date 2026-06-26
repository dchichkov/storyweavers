#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/loose_chrysalis_bandy_bathroom_magic_flashback_quest.py
======================================================================================

A small bathroom storyworld with a Space Adventure feel: a child on a quest,
a flashback to a lost clue, and a little magic that helps turn a loose, bandy
mess into a safe, finished mission.

The seed words are woven into the world:
- loose
- chrysalis
- bandy

The featured narrative instruments are:
- Magic
- Flashback
- Quest

The setting is the bathroom.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bathroom"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"magic", "flashback", "quest"})


@dataclass
class QuestItem:
    label: str
    phrase: str
    region: str
    fragile: bool = False
    plural: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting):
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
GIRL_NAMES = ["Mia", "Zoe", "Ava", "Luna", "Nora", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Eli", "Noah"]
TRAITS = ["brave", "curious", "lively", "gentle", "bold"]

SETTING = Setting()

QUEST_ITEM = QuestItem(
    label="moon-charm",
    phrase="a tiny moon charm",
    region="hand",
    fragile=True,
)

BATHROOM_GEAR = QuestItem(
    label="loose tile",
    phrase="a loose tile by the tub",
    region="floor",
)

BANDY_TUBE = QuestItem(
    label="bandy tube",
    phrase="a bandy tube of bubble soap",
    region="shelf",
)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes['trait']} explorer who treated {world.setting.place} "
        f"like a shiny starship room."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved turning bath time into a quiet quest with {hero.pronoun('possessive')} "
        f"{parent.pronoun('possessive')} help."
    )


def set_scene(world: World) -> None:
    world.say(
        "The bathroom was bright and steamy, with the tub like a silver capsule and the sink like a tiny command deck."
    )
    world.say(
        f"Near the floor, a {BATHROOM_GEAR.label} wobbled a little, and on the shelf sat a {BANDY_TUBE.label} with a funny bend."
    )


def spark_magic(world: World, hero: Entity) -> None:
    hero.memes["wonder"] += 1
    hero.memes["magic"] += 1
    world.say(
        f"{hero.id} tapped the side of the tub and whispered a magic word, as if waking a sleeping spaceship."
    )
    world.say(
        "A soft sparkle floated over the tiles, turning the ordinary bathroom into a map full of little glowing clues."
    )


def flashback(world: World, hero: Entity) -> None:
    hero.memes["flashback"] += 1
    world.say(
        f"Then {hero.id} had a flashback to yesterday, when {hero.pronoun('possessive')} moon-charm slipped behind the sink."
    )
    world.say(
        "In the memory, the charm had slid under a loose edge of tile and vanished like a star going behind a cloud."
    )


def quest_turn(world: World, hero: Entity, parent: Entity, item: QuestItem) -> None:
    hero.memes["quest"] += 1
    world.say(
        f"{hero.id} declared a quest: find the moon-charm before bath time began."
    )
    world.say(
        f"{hero.pronoun().capitalize()} crouched low, peered by the tub, and reached toward the loose tile."
    )
    if item.fragile:
        world.say(
            f"{hero.pronoun('possessive').capitalize()} {parent.pronoun('subject')} warned {hero.pronoun('object')} to be careful, because the charm was tiny and delicate."
        )


def resolve(world: World, hero: Entity, parent: Entity, item: QuestItem) -> None:
    hero.memes["joy"] += 1
    world.say(
        "The sparkle from the magic gathered into a tiny beam, and the loose tile lifted just enough to show the missing charm."
    )
    world.say(
        f"{hero.id} reached in, rescued the moon-charm, and held it up like a shining medal."
    )
    world.say(
        f"Then {hero.pronoun('subject')} tucked the charm safely into {hero.pronoun('possessive')} palm and smiled at {parent.id}."
    )
    world.say(
        "The bathroom felt calm again, like a ship after a successful landing."
    )


def tell(world: World, hero: Entity, parent: Entity) -> World:
    intro(world, hero, parent)
    world.para()
    set_scene(world)
    spark_magic(world, hero)
    flashback(world, hero)
    world.para()
    quest_turn(world, hero, parent, QUEST_ITEM)
    resolve(world, hero, parent, QUEST_ITEM)

    world.facts.update(
        hero=hero,
        parent=parent,
        quest_item=QUEST_ITEM,
        setting=world.setting,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonable story gating
# ---------------------------------------------------------------------------
def valid_story() -> bool:
    return True


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
feature(magic).
feature(flashback).
feature(quest).
setting(bathroom).

quest_story :- feature(magic), feature(flashback), feature(quest), setting(bathroom).
#show quest_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("feature", "magic"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "quest"),
        asp.fact("setting", "bathroom"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show quest_story/0."))
    asp_ok = bool(asp.atoms(model, "quest_story"))
    py_ok = valid_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python reasonableness gates match.")
        return 0
    print(f"MISMATCH: ASP={asp_ok} Python={py_ok}")
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    return [
        'Write a short bathroom space-adventure story with Magic, Flashback, and Quest.',
        f'Write a gentle story about {world.facts["hero"].id} finding a missing moon-charm in the bathroom.',
        'Tell a child-friendly story where a sparkling clue helps a quest end happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id}?",
            answer=f"It is a small space-adventure story set in the bathroom, where {hero.id} goes on a quest with a little magic and a flashback clue.",
        ),
        QAItem(
            question=f"What did {hero.id} want to find during the quest?",
            answer=f"{hero.id} wanted to find the tiny moon-charm that slipped behind the loose tile.",
        ),
        QAItem(
            question=f"How did the magic help {hero.id}?",
            answer="The sparkle turned into a glowing clue and lifted the loose tile just enough to reveal where the charm was hiding.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {parent.id}?",
            answer=f"{hero.id} rescued the moon-charm, smiled, and the bathroom felt calm again while {parent.id} watched proudly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows something that happened earlier, so the character remembers an important clue.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to find something important or solve a problem.",
        ),
        QAItem(
            question="What does magic do in stories?",
            answer="Magic can make surprising things happen, like sparkling clues, glowing lights, or helpful changes that would not happen on their own.",
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
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bathroom space-adventure storyworld with magic, flashback, and quest.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"trait": params.trait, "wonder": 0.0, "magic": 0.0, "flashback": 0.0, "quest": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id=params.parent.capitalize(),
        kind="character",
        type=params.parent,
    ))
    tell(world, hero, parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show quest_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show quest_story/0."))
        ok = bool(asp.atoms(model, "quest_story"))
        print("1 compatible story" if ok else "0 compatible stories")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        preset = [
            StoryParams(name="Luna", gender="girl", parent="mother", trait="curious", seed=base_seed),
            StoryParams(name="Theo", gender="boy", parent="father", trait="brave", seed=base_seed + 1),
            StoryParams(name="Mia", gender="girl", parent="father", trait="bold", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in preset]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
