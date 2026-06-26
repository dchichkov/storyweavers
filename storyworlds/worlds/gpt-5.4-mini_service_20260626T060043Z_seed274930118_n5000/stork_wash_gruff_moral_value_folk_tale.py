#!/usr/bin/env python3
"""
storyworlds/worlds/stork_wash_gruff_moral_value_folk_tale.py
==============================================================

A small folk-tale story world about a stork, a wash-day problem, and a gruff
character who learns a moral value.

Seed tale:
---
A stork lived by a marsh and kept a tidy white coat. One day, a gruff old miller
splashed muddy water into the path and laughed when the stork got dirty. The
stork quietly washed the mud away, but the miller's own cloak later caught the
same grime. When the miller could not clean it alone, the stork helped wash it
clean. The gruff miller softened, thanked the stork, and learned that kindness
makes a better ending than meanness.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    washed: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"stork"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"miller"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the marsh"
    water: str = "the creek"
    affords: set[str] = field(default_factory=lambda: {"wash"})


@dataclass
class StoryParams:
    place: str
    actor: str
    gruffness: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def _ensure_meter(e: Entity, key: str) -> float:
    return e.meters.setdefault(key, 0.0)


def wash_dirty(world: World, actor: Entity, target: Entity) -> None:
    if _ensure_meter(target, "muddy") < THRESHOLD:
        return
    target.meters["muddy"] = 0.0
    target.washed = True
    actor.memes["helped"] = actor.memes.get("helped", 0.0) + 1
    world.say(f"{actor.pronoun().capitalize()} washed the mud away from {target.label}.")


def tell(setting: Setting, actor_type: str = "stork", gruffness: str = "gruff") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="Stork",
        kind="character",
        type=actor_type,
        label="stork",
        phrase="a white stork with long legs",
        traits=["tidy", "gentle"],
    ))
    gruff = world.add(Entity(
        id="Miller",
        kind="character",
        type="miller",
        label="miller",
        phrase=f"a {gruffness} old miller",
        traits=[gruffness, "proud"],
    ))
    cloak = world.add(Entity(
        id="Cloak",
        kind="thing",
        type="cloak",
        label="cloak",
        phrase="a heavy brown cloak",
        owner=gruff.id,
        meters={"muddy": 0.0},
    ))

    world.say(f"There was once a {hero.label} by {setting.place}, and {hero.pronoun('possessive')} feathers were bright and clean.")
    world.say(f"Near the water lived {gruff.phrase}, who spoke in a {gruffness} voice and liked to laugh at small troubles.")
    world.para()
    world.say(f"One day the miller sloshed through the bank and splashed mud onto the {hero.label}'s wings.")
    hero.meters["muddy"] = 1.0
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    world.say(f"The {hero.label} did not quarrel. {hero.pronoun().capitalize()} went to {setting.water} and washed {hero.pronoun('possessive')} feathers clean.")
    hero.meters["muddy"] = 0.0
    world.para()
    world.say(f"Later the miller's own cloak dragged through the same muck and came home all dirty.")
    cloak.meters["muddy"] = 1.0
    gruff.memes["pride"] = gruff.memes.get("pride", 0.0) + 1
    world.say(f"The gruff miller tried to scrub it alone, but the stain would not come out.")
    world.say(f"Then the {hero.label} returned, dipped {hero.pronoun('object')} beak in the wash water, and helped the miller clean the cloak.")
    wash_dirty(world, hero, cloak)
    gruff.memes["soft"] = gruff.memes.get("soft", 0.0) + 1
    gruff.memes["gratitude"] = gruff.memes.get("gratitude", 0.0) + 1
    world.para()
    world.say(f"The miller looked down at the clean cloak and bowed his head.")
    world.say(f'"I was gruff," he said, "but your kindness washed more than mud from my day."')
    world.say(f"So the {hero.label} flew home, and the miller remembered that a kind hand makes a better friend than a harsh one.")

    world.facts.update(
        hero=hero,
        gruff=gruff,
        cloak=cloak,
        setting=setting,
        moral="kindness",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short folk tale for a child about a stork who must wash off mud and teach a gruff miller a moral value.',
        f"Tell a gentle story set at {world.setting.place} where a stork and a gruff miller learn kindness.",
        "Write a simple moral tale that includes the words stork, wash, and gruff.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    gruff = f["gruff"]
    cloak = f["cloak"]
    setting = f["setting"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about a stork living by {setting.place} and a gruff miller who learns to be kinder.",
        ),
        QAItem(
            question="What happened to the stork first?",
            answer=f"The miller splashed mud onto the stork, and then the stork went to {setting.water} to wash clean.",
        ),
        QAItem(
            question="What did the stork help wash later?",
            answer=f"The stork helped wash the miller's cloak clean after it got muddy.",
        ),
        QAItem(
            question="What moral value does the story teach?",
            answer="It teaches kindness, because helping someone is better than acting gruff and mean.",
        ),
        QAItem(
            question=f"How did the gruff miller feel at the end?",
            answer=f"He felt thankful and softer in spirit after the stork helped clean his cloak.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stork?",
            answer="A stork is a tall bird with long legs and a long beak.",
        ),
        QAItem(
            question="What does wash mean?",
            answer="To wash means to use water, and often soap too, to make something clean.",
        ),
        QAItem(
            question="What does gruff mean?",
            answer="Gruff means rough, stern, or sharp in the way someone speaks.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward others.",
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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "marsh": Setting(place="the marsh", water="the creek", affords={"wash"}),
    "village": Setting(place="the village pond", water="the pond", affords={"wash"}),
    "mill": Setting(place="the old mill stream", water="the stream", affords={"wash"}),
}

CURATED = [
    StoryParams(place="marsh", actor="stork", gruffness="gruff"),
    StoryParams(place="village", actor="stork", gruffness="gruff"),
    StoryParams(place="mill", actor="stork", gruffness="gruff"),
]


ASP_RULES = r"""
dirty(stork) :- mud(stork).
dirty(cloak) :- mud(cloak).
helpful(stork) :- wash(stork, cloak).
kind_moral :- helpful(stork), gruff(miller).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, setting.place))
        lines.append(asp.fact("water_name", sid, setting.water))
    lines.append(asp.fact("actor", "stork"))
    lines.append(asp.fact("actor", "miller"))
    lines.append(asp.fact("trait", "miller", "gruff"))
    lines.append(asp.fact("moral", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale world about a stork, wash-day, and a gruff miller.")
    ap.add_argument("--place", choices=SETTINGS)
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
    place = args.place or rng.choice(list(SETTINGS))
    return StoryParams(place=place, actor="stork", gruffness="gruff")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.actor, params.gruffness)
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


def valid_places() -> list[str]:
    return sorted(SETTINGS)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    asp_set = set(asp.atoms(model, "setting"))
    py_set = {(p,) for p in valid_places()}
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_places() ({len(py_set)} places).")
        return 0
    print("MISMATCH between clingo and valid_places():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_places())} compatible places:\n")
        for (place,) in asp_valid_places():
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
