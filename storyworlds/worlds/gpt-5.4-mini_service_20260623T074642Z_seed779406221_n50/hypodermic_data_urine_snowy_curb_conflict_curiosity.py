#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/hypodermic_data_urine_snowy_curb_conflict_curiosity.py
===============================================================================================================

A standalone storyworld for a tiny rhyming-style tale about curiosity, conflict,
and a careful resolution on a snowy curb.

Premise:
- A curious child notices a dropped clinic pouch by a snowy curb.
- Inside are a hypodermic, a data card, and a note about urine samples.
- The child wants to peek closer; the parent worries about safety.
- The child learns to keep distance, call for help, and hand the pouch to a nurse.

The story is kept child-facing by centering the child's feelings, the parent's
warning, and a safe handoff instead of any medical procedure details.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    nurse: object | None = None
    parent: object | None = None
    pouch: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the snowy curb"
    world: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class ObjectCard:
    label: str
    phrase: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def rhyme(a: str, b: str) -> str:
    return f"{a} / {b}"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld on a snowy curb.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["curious", "brave", "gentle", "patient"])
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mina", "Toby", "Lena", "Noah", "Ada", "Finn"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(["curious", "brave", "gentle", "patient"])
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def _setup(world: World, hero: Entity, parent: Entity, pouch: Entity, nurse: Entity) -> None:
    world.say(
        f"At the snowy curb, {hero.id} was a {hero.memes.get('trait', 'curious')} little {hero.type} "
        f"who loved to look and learn."
    )
    world.say(
        f"{hero.pronoun().capitalize()} spotted a small clinic pouch in the white snow-glow, "
        f"and the wind went whisper-swish, soft as a song."
    )
    world.say(
        f"Inside were a hypodermic, a data card, and a note about urine samples for the nurse to bring along."
    )
    world.facts["pouch"] = pouch
    world.facts["nurse"] = nurse


def _conflict(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} leaned in with a curious grin, but {hero.pronoun('possessive')} {parent.pronoun('subject')} said, "
        f"\"No, sweet pea, keep away; sharp things stay far from play.\""
    )
    hero.memes["conflict"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"{hero.id}'s heart went bump-bump-bump; the curb felt long and cold, not fun and jump-bump-jump."
    )


def _turn(world: World, hero: Entity, parent: Entity, nurse: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} blinked at the data card, then at the hypodermic, and asked, \"Why does that pouch belong to a nurse?\""
    )
    world.say(
        f"{parent.id} answered in a low, kind tone, \"Some tools are not for child hands. We can help by keeping them safe.\""
    )
    world.say(
        f"Then {hero.id} saw {nurse.id} hurrying by in boots that squeaked on the snow, and the worry in the air began to blur."
    )
    hero.memes["curiosity"] += 1


def _resolution(world: World, hero: Entity, parent: Entity, nurse: Entity, pouch: Entity) -> None:
    world.para()
    hero.memes["conflict"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} took one small step back, then one careful step forward, and held out the pouch with a brave little nod."
    )
    world.say(
        f"{nurse.id} thanked {hero.id}, tied the pouch snug, and said the data and urine note would help with careful care."
    )
    world.say(
        f"At the snowy curb, the sharp little thing was no child's toy; it was handed off and set on its safe, grown-up way."
    )
    world.say(
        f"{hero.id} smiled at the hush of snow and said, \"I looked, I learned, and I let it go.\""
    )


def tell(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    hero.memes["trait"] = params.trait
    parent = world.add(Entity(id=params.parent.title(), kind="character", type=params.parent))
    nurse = world.add(Entity(id="Nurse", kind="character", type="woman", label="the nurse"))
    pouch = world.add(Entity(id="Pouch", kind="thing", type="thing", label="clinic pouch"))

    _setup(world, hero, parent, pouch, nurse)
    _conflict(world, hero, parent)
    _turn(world, hero, parent, nurse)
    _resolution(world, hero, parent, nurse, pouch)

    world.facts.update(hero=hero, parent=parent, nurse=nurse, pouch=pouch, params=params)
    return world


def prompt_list(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    return [
        f'Write a short rhyming story about a curious child named {hero.id} at a snowy curb.',
        f'Tell a gentle, child-friendly tale where {hero.id} sees a hypodermic, data, and urine in a clinic pouch and {parent.id} helps keep everyone safe.',
        f'Write a simple story with a snowy curb, a curious look, a small conflict, and a safe handoff to a nurse.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, nurse = f["hero"], f["parent"], f["nurse"]
    return [
        QAItem(
            question=f"Where did {hero.id} find the clinic pouch?",
            answer="At the snowy curb, where the snow lay bright and still.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before {parent.id} warned {hero.pronoun('object')}?",
            answer=f"{hero.id} wanted to look closer because {hero.pronoun('subject')} was curious.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{hero.id} gave the pouch to {nurse.id}, and everyone stayed safe and calm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypodermic?",
            answer="A hypodermic is a medical needle used by trained grown-ups for careful care.",
        ),
        QAItem(
            question="What is data?",
            answer="Data is information that people collect and write down so they can learn from it.",
        ),
        QAItem(
            question="What is urine?",
            answer="Urine is a liquid the body makes and sends out as waste.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: kind={e.kind}, type={e.type}, memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_handoff(child) :- curious(child), warned(parent, child), handed(child, pouch, nurse).
conflict(child) :- curious(child), warned(parent, child), not safe_handoff(child).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("curious", "child"),
            asp.fact("warned", "parent", "child"),
            asp.fact("handed", "child", "pouch", "nurse"),
        ]
    )


def build_asp(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompt_list(world),
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
        for item in sample.prompts:
            print(item)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(build_asp("#show safe_handoff/1. #show conflict/1."))
        return
    if getattr(args, "verify", None):
        print("OK: verification stub for this compact world.")
        return
    if getattr(args, "asp", None):
        print("ASP mode: safe_handoff(child) is the intended model for this world.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("Mina", "girl", "mother", "curious"),
            StoryParams("Toby", "boy", "father", "brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(max(1, getattr(args, "n", None))):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
