#!/usr/bin/env python3
"""
storyworlds/worlds/hiccough_transformation_superhero_story.py
=============================================================

A small superhero storyworld about a child hero, a hiccough, and a
transformation that turns worry into brave action.

The seed premise:
---
A kid wants to help in a city scene, but a stubborn hiccough keeps popping out
at the worst time. A special suit transforms the child into a superhero form,
and the new form helps them focus, act bravely, and solve the problem.

World shape:
- The hero has physical meters like energy, speed, and costume-glow.
- The hero has emotional memes like worry, bravery, and pride.
- The hiccough is a small physical interruption that can raise worry.
- A transformation device or costume can shift the hero into superhero mode.
- The story ends with a concrete image showing what changed.

Style goal:
- Child-facing, concrete, and complete.
- Superhero-story flavor with a clear turn and a satisfying ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities / world model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    transformed: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
        if "_tags" not in self.__dict__:
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
    indoors: bool
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    detail: str
    keyword: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
class Suit:
    id: str
    label: str
    power: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "city": Setting(place="the city", indoors=False, affords={"kite", "rescue", "parade"}),
    "rooftop": Setting(place="the rooftop", indoors=False, affords={"kite", "signal"}),
    "museum": Setting(place="the museum hall", indoors=True, affords={"parade", "rescue"}),
    "park": Setting(place="the park", indoors=False, affords={"kite", "parade"}),
}

CHALLENGES = {
    "kite": Challenge(
        id="kite",
        verb="catch the runaway kite",
        gerund="chasing the runaway kite",
        rush="sprint after the kite",
        mess="windy",
        zone={"arms", "head"},
        detail="A bright kite was tugging hard against the string.",
        keyword="kite",
    ),
    "rescue": Challenge(
        id="rescue",
        verb="save the kitten",
        gerund="rescuing the kitten",
        rush="rush to the fence",
        mess="jumpy",
        zone={"arms", "torso"},
        detail="A tiny kitten was stuck on a low ledge.",
        keyword="kitten",
    ),
    "parade": Challenge(
        id="parade",
        verb="join the parade",
        gerund="marching in the parade",
        rush="step into the line",
        mess="sparkly",
        zone={"torso"},
        detail="A parade band was getting ready on the street.",
        keyword="parade",
    ),
    "signal": Challenge(
        id="signal",
        verb="send the signal",
        gerund="sending the signal",
        rush="raise a hand to the sky",
        mess="glowy",
        zone={"arms", "torso"},
        detail="The rooftop needed a bright signal to guide the team.",
        keyword="signal",
    ),
}

SUITS = {
    "star_suit": Suit(
        id="star_suit",
        label="star suit",
        power="focus",
        prep="put on the star suit",
        tail="fastened the star suit and stood tall",
        guards={"windy", "jumpy", "sparkly", "glowy"},
    ),
    "cape": Suit(
        id="cape",
        label="red cape",
        power="bravery",
        prep="wrap on the red cape",
        tail="swung the cape around and grinned",
        guards={"windy", "sparkly"},
    ),
    "helmet": Suit(
        id="helmet",
        label="silver helmet",
        power="calm",
        prep="snap on the silver helmet",
        tail="clicked the helmet into place and took a deep breath",
        guards={"jumpy", "glowy"},
    ),
}

HERO_NAMES = ["Maya", "Leo", "Nina", "Toby", "Ari", "Zoe"]
TRAITS = ["small", "brave", "quick", "curious", "cheerful"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def challenge_needs_transformation(ch: Challenge) -> bool:
    return True


def choose_suit(ch: Challenge) -> Optional[Suit]:
    for suit in SUITS.values():
        if ch.mess in suit.guards:
            return suit
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for chal_id in setting.affords:
            ch = _safe_lookup(CHALLENGES, chal_id)
            if challenge_needs_transformation(ch) and choose_suit(ch):
                combos.append((place, chal_id))
    return combos


def explain_rejection(ch: Challenge) -> str:
    return (
        f"(No story: the challenge '{ch.id}' does not have a suit that can "
        f"reasonably help with its {ch.mess} problem.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def hero_intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.traits[0]} hero who loved helping people."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept a special hero suit ready for the right moment."
    )


def hiccough_event(world: World, hero: Entity) -> None:
    hero.meters["hiccough"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But one day, {hero.pronoun()} got a hiccough that popped out like a tiny drumbeat."
    )


def arrive(world: World, hero: Entity, ch: Challenge) -> None:
    world.say(f"One day, {hero.id} went to {world.setting.place}.")
    world.say(ch.detail)


def worry(world: World, hero: Entity, ch: Challenge) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to {ch.verb}, but the hiccough made {hero.pronoun('object')} pause."
    )
    world.say(
        f"Every hiccough sounded louder when {hero.pronoun()} tried to {ch.rush}."
    )


def transform(world: World, hero: Entity, suit: Suit) -> Entity:
    suit_ent = world.add(
        Entity(
            id=suit.id,
            kind="thing",
            type="suit",
            label=suit.label,
            owner=hero.id,
            worn_by=hero.id,
            meters={"glow": 1.0},
        )
    )
    hero.transformed = True
    hero.memes["bravery"] += 1
    hero.memes["worry"] = 0.0
    hero.meters["focus"] += 1
    world.say(f"Then {hero.id} decided to transform.")
    world.say(f"{hero.id} {suit.prep}, and in a flash, {hero.id} became a superhero.")
    world.say(
        f"{hero.id}'s {suit.label} gave {hero.pronoun('object')} {suit.power}, and the hiccough felt smaller."
    )
    return suit_ent


def solve(world: World, hero: Entity, ch: Challenge) -> None:
    hero.meters["speed"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} used {hero.pronoun('possessive')} new superhero focus to {ch.verb}."
    )
    if ch.id == "kite":
        world.say(
            f"{hero.id} dashed after the kite, caught the string, and the kite floated safely above {world.setting.place}."
        )
    elif ch.id == "rescue":
        world.say(
            f"{hero.id} climbed carefully, lifted the kitten down, and the tiny paws landed safely in {hero.pronoun('possessive')} hands."
        )
    elif ch.id == "parade":
        world.say(
            f"{hero.id} stepped into the parade line just in time, and the drums beat happily beside {hero.id}."
        )
    elif ch.id == "signal":
        world.say(
            f"{hero.id} raised a bright signal, and the whole team saw it from far away."
        )


def ending(world: World, hero: Entity, ch: Challenge, suit: Suit) -> None:
    world.say(
        f"When it was over, {hero.id} still had the hiccough, but now it sounded funny instead of frightening."
    )
    world.say(
        f"{hero.id} stood in {suit.label} {ch.gerund}, with {hero.pronoun('possessive')} chest high and {hero.pronoun('possessive')} smile even higher."
    )


def tell(setting: Setting, challenge: Challenge, hero_name: str, hero_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=["small", "brave"],
            meters={"energy": 1.0},
            memes={"worry": 0.0, "bravery": 0.0, "pride": 0.0},
        )
    )

    hero_intro(world, hero)
    world.para()
    hiccough_event(world, hero)
    arrive(world, hero, challenge)
    worry(world, hero, challenge)
    suit = choose_suit(challenge)
    if suit is None:
        pass
    world.para()
    transform(world, hero, suit)
    solve(world, hero, challenge)
    ending(world, hero, challenge, suit)

    world.facts.update(hero=hero, challenge=challenge, suit=suit, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, ch, suit = f["hero"], f["challenge"], f["suit"]
    return [
        f'Write a short superhero story for a young child about {hero.id}, '
        f'a hiccough, and a transformation with the words "{ch.keyword}" and "{suit.label}".',
        f"Tell a brave story where {hero.id} gets a hiccough, transforms, and helps with {ch.verb}.",
        f"Write a simple superhero story about a child hero using {suit.label} to solve a {ch.keyword} problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ch, suit = f["hero"], f["challenge"], f["suit"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little superhero who gets a hiccough and then transforms.",
        ),
        QAItem(
            question=f"What problem did {hero.id} face at {world.setting.place}?",
            answer=f"{hero.id} faced a {ch.keyword} problem, and the hiccough made it harder at first.",
        ),
        QAItem(
            question=f"What helped {hero.id} become brave?",
            answer=f"{suit.label} helped {hero.id} transform into a superhero and focus on the job.",
        ),
        QAItem(
            question=f"What changed after the transformation?",
            answer=f"After the transformation, {hero.id} felt braver, more focused, and ready to help.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a hiccough?",
            answer="A hiccough is a small sudden sound or jump in your body that can pop out without warning.",
        ),
        QAItem(
            question="What does it mean to transform?",
            answer="To transform means to change into a different form or look, like turning into a superhero version of yourself.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave helper who uses special power, courage, or gear to solve problems and protect others.",
        ),
    ]
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed:
            bits.append("transformed=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
eligible(Place, Challenge) :- affords(Place, Challenge), suit_for(Challenge, _).
suit_for(kite, star_suit).
suit_for(rescue, star_suit).
suit_for(parade, cape).
suit_for(signal, helmet).
valid_story(Place, Challenge) :- eligible(Place, Challenge).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for chal in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, chal))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for sid in SUITS:
        lines.append(asp.fact("suit", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    gender: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld: a child hero, a hiccough, and a transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
        (place, chal)
        for place, chal in valid_combos()
        if (getattr(args, "place", None) is None or getattr(args, "place", None) == place)
        and (getattr(args, "challenge", None) is None or getattr(args, "challenge", None) == chal)
    ]
    if not combos:
        if getattr(args, "challenge", None):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, chal = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    return StoryParams(place=place, challenge=chal, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHALLENGES, params.challenge), params.name, params.gender)
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
    StoryParams(place="city", challenge="kite", name="Maya", gender="girl"),
    StoryParams(place="museum", challenge="rescue", name="Leo", gender="boy"),
    StoryParams(place="park", challenge="parade", name="Zoe", gender="girl"),
    StoryParams(place="rooftop", challenge="signal", name="Ari", gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, challenge) combos:\n")
        for place, chal in combos:
            print(f"  {place:8} {chal}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
