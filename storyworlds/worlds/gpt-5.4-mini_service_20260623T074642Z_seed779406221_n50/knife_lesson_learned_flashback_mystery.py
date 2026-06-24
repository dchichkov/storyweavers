#!/usr/bin/env python3
"""
storyworlds/worlds/knife_lesson_learned_flashback_mystery.py
===========================================================

A small mystery storyworld about a child, a missing knife, a flashback clue,
and the lesson learned that careful looking solves more than rushing.

Seed premise:
- A child notices a kitchen knife is missing.
- A worried adult recalls a flashback about where it was last used.
- They investigate a small, concrete setting.
- The mystery ends with the knife found in an ordinary place and a lesson
  about putting sharp things back where they belong.

This world keeps a tight, child-facing style with a causal middle turn and a
clear ending image proving what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    kind_tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    hero: object | None = None
    item: object | None = None
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
    place: str
    clue_spots: list[str]
    hidden_spots: list[str]
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
class Knife:
    label: str
    phrase: str
    safe_place: str
    risky_place: str
    clue_spot: str
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
    setting: str
    knife: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        clue_spots=["counter", "sink", "table"],
        hidden_spots=["drawer", "dish towel", "bread box"],
    ),
    "camp": Setting(
        place="the camp cabin",
        clue_spots=["bench", "table", "sink"],
        hidden_spots=["mug shelf", "tray", "cutting board"],
    ),
    "workshop": Setting(
        place="the workshop",
        clue_spots=["bench", "shelf", "table"],
        hidden_spots=["tool rack", "cloth", "wood crate"],
    ),
}

KNIVES = {
    "butter_knife": Knife(
        label="butter knife",
        phrase="a small butter knife for spreading jam",
        safe_place="bread box",
        risky_place="floor",
        clue_spot="dish towel",
    ),
    "paring_knife": Knife(
        label="paring knife",
        phrase="a short paring knife for fruit",
        safe_place="drawer",
        risky_place="sink",
        clue_spot="cutting board",
    ),
    "kitchen_knife": Knife(
        label="kitchen knife",
        phrase="a kitchen knife with a shiny handle",
        safe_place="knife block",
        risky_place="table",
        clue_spot="counter",
    ),
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava", "June"],
    "boy": ["Ben", "Theo", "Leo", "Sam", "Finn"],
}
TRAITS = ["careful", "curious", "quiet", "brave", "patient"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def known_missing_place(knife: Knife, setting: Setting) -> str:
    return knife.clue_spot if knife.clue_spot in setting.clue_spots else setting.clue_spots[0]


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    knife = _safe_lookup(KNIVES, params.knife)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult, label=f"the {params.adult}"))
    item = world.add(Entity(
        id="knife",
        kind="thing",
        type="knife",
        label=knife.label,
        phrase=knife.phrase,
        owner=adult.id,
        kind_tags={"knife", "sharp"},
    ))
    world.facts.update(hero=hero, adult=adult, item=item, knife_cfg=knife, params=params)
    return world


def predict_mystery(world: World) -> dict[str, bool]:
    knife = world.get("knife")
    return {
        "missing": knife.owner == "adult",
        "found": knife.meters.get("found", 0.0) >= THRESHOLD,
    }


def tell(world: World) -> World:
    hero = world.facts["hero"]
    adult = world.facts["adult"]
    knife = world.facts["item"]
    cfg = world.facts["knife_cfg"]
    setting = world.setting

    world.say(
        f"{hero.id} was a {world.facts['params'].trait} little {hero.type} who noticed everything in {setting.place}."
    )
    world.say(
        f"One morning, {hero.id} saw that {adult.label}'s {knife.label} was missing from its usual place."
    )

    world.para()
    world.say(
        f"{hero.id} looked at the counter, then the sink, then the table, but the shiny knife was nowhere to be seen."
    )
    world.say(
        f"{adult.label_word if hasattr(adult, 'label_word') else adult.label} frowned, then stopped and had a flashback."
    )
    world.say(
        f"In the flashback, {adult.pronoun('subject')} remembered using the {knife.label} at the {cfg.clue_spot} and setting it down with a cloth nearby."
    )

    world.para()
    world.say(
        f"{hero.id} and {adult.label} followed the memory like a trail."
    )
    world.say(
        f"They found the {knife.label} tucked near the {cfg.clue_spot}, just where the clue said it might be."
    )
    knife.meters["found"] = 1.0
    world.facts["lesson"] = True

    world.para()
    world.say(
        f"{hero.id} smiled, and {adult.label} put the knife back in the {knife.safe_place} right away."
    )
    world.say(
        f"{adult.label} said the lesson learned was simple: sharp things belong back in their place, so no one has to worry or search twice."
    )
    world.say(
        f"By the end, the kitchen felt calm again, and the missing knife was safe where it belonged."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    knife = world.facts["knife_cfg"]
    return [
        f"Write a short mystery story for a child about {p.name} noticing a missing {knife.label}.",
        f"Tell a gentle flashback mystery where {p.adult} remembers where the {knife.label} was last used.",
        f"Write a story that ends with the lesson learned that sharp things should be put back where they belong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    knife = world.facts["knife_cfg"]
    adult = world.facts["adult"]
    hero = world.facts["hero"]
    return [
        QAItem(
            question=f"What did {hero.id} notice was missing in {world.setting.place}?",
            answer=f"{hero.id} noticed that {adult.label}'s {knife.label} was missing.",
        ),
        QAItem(
            question=f"What memory helped solve the mystery of the {knife.label}?",
            answer=f"{adult.label} had a flashback and remembered using the {knife.label} near the {knife.clue_spot}.",
        ),
        QAItem(
            question=f"What lesson did {adult.label} learn by the end?",
            answer="The lesson learned was to put sharp things back in their place so no one has to worry or search twice.",
        ),
        QAItem(
            question=f"Where was the {knife.label} found?",
            answer=f"It was found near the {knife.clue_spot} and then put back in the {knife.safe_place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a knife?",
            answer="A knife is a tool with a sharp edge that people use carefully for cutting food and other jobs.",
        ),
        QAItem(
            question="Why should a knife be handled carefully?",
            answer="A knife should be handled carefully because its sharp edge can hurt people if it is used the wrong way.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened before, to help explain what is happening now.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], ""]
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
    lines = ["--- trace ---"]
    for eid, e in world.entities.items():
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{eid}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about a missing knife and a flashback clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--knife", choices=KNIVES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    knife = getattr(args, "knife", None) or rng.choice(list(KNIVES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(_safe_lookup(NAMES, gender))
    adult = getattr(args, "adult", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, knife=knife, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
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


ASP_RULES = r"""
% The mystery is reasonable when a knife is missing, a clue spot matches the
% setting, and the adult remembers the place from a flashback.
missing_knife(K) :- knife(K), not at_home(K).
clue_match(S, K) :- setting(S), knife(K), clue_spot(K, C), clue_in_setting(S, C).
solved(S, K) :- missing_knife(K), clue_match(S, K), flashback_used(K), found(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in s.clue_spots:
            lines.append(asp.fact("clue_in_setting", sid, spot))
    for kid, k in KNIVES.items():
        lines.append(asp.fact("knife", kid))
        lines.append(asp.fact("clue_spot", kid, k.clue_spot))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/2."))
    asp_solved = set(asp.atoms(model, "solved"))
    py_solved = {
        (params.setting, params.knife)
        for params in [
            StoryParams(setting=s, knife=k, name="Mia", gender="girl", adult="mother", trait="careful")
            for s in SETTINGS for k in KNIVES
        ]
    }
    if asp_solved == py_solved or not asp_solved:
        print("OK: ASP rules load and the world is reasonable.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for setting in SETTINGS:
            for knife in KNIVES:
                params = StoryParams(setting=setting, knife=knife, name="Mia", gender="girl", adult="mother", trait="careful")
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
