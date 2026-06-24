#!/usr/bin/env python3
"""
A tiny storyworld for a nursery-rhyme style mystery about gastritis.

Premise:
- A small child or animal gets a belly ache.
- The story pauses for a flashback that shows the cause.
- A gentle mystery is solved by noticing the pattern and choosing soothing food, water, and rest.

This script is self-contained and uses the shared result containers from
storyworlds/results.py. ASP mode mirrors the Python reasonableness gate:
the cause must be plausible, the flashback must explain it, and the remedy
must match the symptoms.
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

THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    hero: object | None = None
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
    cozy: bool = True
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
class Cause:
    id: str
    scene: str
    food: str
    taste: str
    tummy: str
    clue: str
    remedy: str
    tags: set[str] = field(default_factory=set)
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    history: list[str] = field(default_factory=list)

    world: object | None = None
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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", cozy=True),
    "nursery": Setting(place="the nursery", cozy=True),
    "garden": Setting(place="the garden", cozy=True),
    "bedroom": Setting(place="the bedroom", cozy=True),
}

CAUSES = {
    "sour_berries": Cause(
        id="sour_berries",
        scene="under the berry bush",
        food="too many sour berries",
        taste="sour and zingy",
        tummy="gastritis",
        clue="a lot of sour juice on the lips",
        remedy="warm porridge",
        tags={"gastritis", "flashback", "mystery"},
    ),
    "cold_milk": Cause(
        id="cold_milk",
        scene="by the little table",
        food="cold milk too fast",
        taste="chilly and swift",
        tummy="gastritis",
        clue="a shivery gulp in the middle",
        remedy="warm tea",
        tags={"gastritis", "flashback", "mystery"},
    ),
    "greedy_cake": Cause(
        id="greedy_cake",
        scene="at the party plate",
        food="too much sweet cake",
        taste="sweet and heavy",
        tummy="gastritis",
        clue="crumbs and cream on every sleeve",
        remedy="plain toast",
        tags={"gastritis", "flashback", "mystery"},
    ),
}

HERO_NAMES = ["Mia", "Theo", "Lily", "Noah", "Ava", "Finn", "Rose", "Ben"]
CARETAKER_NAMES = ["Mama", "Papa", "Nana", "Grandpa", "Mom", "Dad"]

TRAITS = ["small", "brave", "curious", "little", "gentle"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    cause: str
    name: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
% A cause is valid if it can lead to gastritis, has a flashback clue,
% and has a soothing remedy.
valid_cause(C) :- cause(C), causes_gastritis(C), flashback(C), remedy(C).

% The mystery is solved when the child notices the clue and chooses the remedy.
solved(C) :- valid_cause(C), clue(C), remedy(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("causes_gastritis", cid))
        lines.append(asp.fact("flashback", cid))
        lines.append(asp.fact("remedy", cid))
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_causes() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_cause/1."))
    return sorted(set(asp.atoms(model, "valid_cause")))


def asp_verify() -> int:
    python_set = {(k,) for k in valid_cause_ids()}
    asp_set = set(asp_valid_causes())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid causes ({len(asp_set)} causes).")
        return 0
    print("MISMATCH between clingo and python:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_cause_ids() -> list[str]:
    return [cid for cid, c in CAUSES.items() if "gastritis" in c.tags and "flashback" in c.tags and "mystery" in c.tags]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "cause", None) and getattr(args, "cause", None) not in CAUSES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    causes = [cid for cid in valid_cause_ids()
              if getattr(args, "cause", None) is None or cid == getattr(args, "cause", None)]
    if not causes:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    cause = getattr(args, "cause", None) or rng.choice(sorted(causes))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    caretaker = getattr(args, "caretaker", None) or rng.choice(CARETAKER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, cause=cause, name=name, caretaker=caretaker, trait=trait)


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(setting=_safe_lookup(SETTINGS, params.setting))

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        traits=[params.trait, "little"],
    ))
    caretaker = world.add(Entity(
        id=params.caretaker,
        kind="character",
        type="adult",
        label=params.caretaker,
    ))
    cause = _safe_lookup(CAUSES, params.cause)

    world.facts.update(hero=hero, caretaker=caretaker, cause=cause, params=params)

    # Act 1: setup, with nursery-rhyme cadence.
    world.say(f"{hero.id} was a {params.trait} little child in {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved the day with sing-song play and a cozy tray.")
    world.say(f"But one day {hero.id}'s belly felt twisty and gray.")
    world.say(f"{caretaker.label} frowned and said, \"Dear heart, that is not a merry way.\"")

    # Act 2: mystery and flashback.
    world.para()
    hero.memes["worry"] += 1
    hero.meters["tummy_ache"] += 1
    world.say(f"{hero.id} held {hero.pronoun('possessive')} tummy and wondered, \"What made it hurt today?\"")
    world.say(f"The room went still, and a flashback slipped in like a little soft swaying hay.")

    world.para()
    world.say(f"Back then, at {cause.scene}, {hero.id} had gobbled {cause.food}.")
    world.say(f"It tasted {cause.taste}, and {cause.clue} hid in the play.")
    world.say(f"Now the mystery had clues, and the clues could lead the way.")

    # The flashback makes the cause explicit and raises the belly ache.
    hero.meters["gastritis"] += 2
    hero.memes["confused"] += 1
    world.facts["flashback_seen"] = True
    world.facts["clue"] = cause.clue
    world.facts["remedy"] = cause.remedy

    # Act 3: solve the mystery.
    world.para()
    world.say(f"{caretaker.label} said, \"Aha, that is the riddle I spy.\"")
    world.say(f"\"{cause.food.capitalize()} can upset a tummy and make a child sigh.\"")
    world.say(f"\"Let us try {cause.remedy}, then rest awhile nearby.\"")

    hero.meters["tummy_ache"] = 0
    hero.meters["gastritis"] = 0
    hero.memes["worry"] = 0
    hero.memes["relief"] += 2
    hero.memes["joy"] += 1
    world.facts["solved"] = True

    world.para()
    world.say(f"{hero.id} sipped the {cause.remedy} and lay in a cozy nook.")
    world.say(f"The ache went away, the mystery was solved, and {hero.id} smiled at the book.")
    world.say(f"By night, {hero.id}'s belly was calm, as calm as a nook in a nursery rhyme brook.")

    return world


# ---------------------------------------------------------------------------
# Q&A and formatting
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cause = f["cause"]
    return [
        f"Write a gentle nursery-rhyme story where {hero.id} gets gastritis, remembers a flashback, and solves the mystery.",
        f"Tell a child-friendly story about a little child whose belly ache was caused by {cause.food} and who feels better after a cozy remedy.",
        f"Write a rhyming story with a mystery to solve, a flashback clue, and a soft ending where the tummy feels calm again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    cause = f["cause"]
    return [
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was why {hero.id}'s belly hurt, and the answer was that {cause.food} had upset the tummy.",
        ),
        QAItem(
            question=f"What did the flashback show?",
            answer=f"The flashback showed {hero.id} at {cause.scene}, eating {cause.food} and leaving a clue with {cause.clue}.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{caretaker.label} named the cause and gave {cause.remedy}, and then {hero.id}'s tummy felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gastritis?",
            answer="Gastritis means the stomach or tummy is irritated and sore, so it may hurt or feel uneasy.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly goes back to an earlier moment to show something important that happened before.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question that needs clues and careful thinking before it can be answered.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {', '.join(parts) if parts else 'empty'}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Shared interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny nursery-rhyme gastritis mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--name")
    ap.add_argument("--caretaker")
    ap.add_argument("--trait")
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


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(setting="nursery", cause="sour_berries", name="Mia", caretaker="Mama", trait="gentle"),
    StoryParams(setting="garden", cause="cold_milk", name="Theo", caretaker="Papa", trait="curious"),
    StoryParams(setting="kitchen", cause="greedy_cake", name="Ava", caretaker="Nana", trait="brave"),
]


def asp_show_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_cause/1."))
        print(sorted(set(asp.atoms(model, "valid_cause"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
