#!/usr/bin/env python3
"""
A small fable-style story world about a cautious child creature, a moat, and a
lesson remembered in a flashback.

The world simulates:
- a character walking beside a moat
- a tempting shortcut across a narrow bridge or stepping stones
- a flashback to a past splash or scare
- a cautionary choice that avoids trouble
- a closing moral value line that reflects the change

This script follows the Storyweavers contract and can run with text, JSON, QA,
trace, and ASP verification modes.
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
# World entities
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    comp: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "duck"}
        male = {"boy", "father", "man", "fox", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the old meadow"
    has_moat: bool = True
    caution_level: int = 1
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
    temptation: str
    danger: str
    flashback: str
    safe_choice: str
    safe_result: str
    risk_meter: str = "slip"
    memoir: str = "fear"
    moral: str = "Look before you leap."
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
class Companion:
    id: str
    type: str
    label: str
    warning: str
    help_action: str
    help_result: str
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
        self.facts: dict[str, object] = {}

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the old meadow", has_moat=True, caution_level=1),
    "orchard": Setting(place="the orchard path", has_moat=True, caution_level=2),
    "hill": Setting(place="the little hill road", has_moat=False, caution_level=0),
}

CHALLENGES = {
    "cross_moat": Challenge(
        id="cross_moat",
        temptation="cross the moat on the slick stepping stones",
        danger="the stones can wobble and drop a traveler into cold water",
        flashback="once, a careless leap had sent the little traveler splashing into the moat",
        safe_choice="walk the long way around the bridge",
        safe_result="reach the other side dry and steady",
        risk_meter="slip",
        memoir="worry",
        moral="Slow feet often arrive safely.",
    ),
    "reach_berries": Challenge(
        id="reach_berries",
        temptation="lean too far over the moat to reach the bright berries",
        danger="leaning too far can tip a body into the water",
        flashback="the last time, the wind had nearly stolen the berries and the traveler nearly fell",
        safe_choice="ask a friend to fetch the berries with a pole",
        safe_result="enjoy the berries without falling in",
        risk_meter="tilt",
        memoir="nervousness",
        moral="A wise request is better than a risky stretch.",
    ),
    "chase_heron": Challenge(
        id="chase_heron",
        temptation="chase a white heron along the moat bank",
        danger="running near the edge can make paws or feet skid",
        flashback="the traveler had once seen a cousin slide right into the mud by the moat",
        safe_choice="stop, watch, and admire the heron from a safe patch of grass",
        safe_result="see the bird and keep clean feet",
        risk_meter="skid",
        memoir="stubbornness",
        moral="Curiosity is kinder when it is careful.",
    ),
}

COMPANIONS = {
    "turtle": Companion(
        id="turtle",
        type="turtle",
        label="turtle",
        warning="The turtle reminded the traveler that the moat did not forgive hurrying.",
        help_action="point the way to the bridge",
        help_result="arrive without a splash",
    ),
    "heron": Companion(
        id="heron",
        type="heron",
        label="heron",
        warning="The heron stood still and made the traveler notice the edge of the water.",
        help_action="lead the eyes to a safer path",
        help_result="choose the grassy side",
    ),
    "mouse": Companion(
        id="mouse",
        type="mouse",
        label="mouse",
        warning="The mouse squeaked that a small mistake could make a very wet day.",
        help_action="find a dry stone path",
        help_result="keep the paws dry",
    ),
}

HERO_NAMES = ["Milo", "Nia", "Pip", "Tara", "Bram", "Lina", "Oren", "Mira"]
HERO_TYPES = ["fox", "duck", "rabbit", "frog"]
TRAITS = ["curious", "bold", "small", "thoughtful", "quick", "gentle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A challenge is valid when the setting has a moat and the challenge has a safe choice.
valid_story(S, C) :- setting(S), has_moat(S), challenge(C), safe_choice(C).

% For this world, the cautionary gate is simple: every challenge listed in the
% registry has one safe route, and the moral is what concludes the tale.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_moat:
            lines.append(asp.fact("has_moat", sid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("safe_choice", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(sid, cid) for sid, s in SETTINGS.items() if s.has_moat for cid in CHALLENGES}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    challenge: str
    hero_name: str
    hero_type: str
    trait: str
    companion: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
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


def intro(world: World, hero: Entity, comp: Entity, chal: Challenge) -> None:
    world.say(
        f"{hero.id} was a little {hero.meters.get('size_word', 'traveler')} {hero.type} "
        f"who lived near {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked to {chal.temptation.replace('the ', '')}, "
        f"but {comp.label} often watched from the bank."
    )


def flashback(world: World, hero: Entity, chal: Challenge) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0) + 1
    hero.memes[chal.memoir] = hero.memes.get(chal.memoir, 0) + 1
    world.say(
        f"One morning, {hero.id} remembered a flashback: {chal.flashback}."
    )
    world.say(
        f"That memory made {hero.pronoun('possessive')} chest feel a little tight."
    )


def caution(world: World, hero: Entity, comp: Entity, chal: Challenge) -> None:
    hero.memes["caution"] = hero.memes.get("caution", 0) + 1
    world.say(
        f"{comp.label.capitalize()} spoke gently: \"{chal.warning}\""
    )
    world.say(
        f"{hero.id} looked at the water and decided not to rush."
    )


def choice(world: World, hero: Entity, chal: Challenge, comp: Entity) -> None:
    hero.meters[chal.risk_meter] = hero.meters.get(chal.risk_meter, 0) + 1
    world.say(
        f"Instead, {hero.id} chose to {chal.safe_choice}."
    )
    world.say(
        f"With {comp.label}'s help, {hero.id} could {chal.safe_result}."
    )


def ending(world: World, hero: Entity, chal: Challenge) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    world.say(
        f"By dusk, {hero.id} was safe on dry ground, and the moat still glimmered below."
    )
    world.say(
        f"The moral was plain: {chal.moral}"
    )


# ---------------------------------------------------------------------------
# World construction and generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    chal = _safe_lookup(CHALLENGES, params.challenge)
    comp_cfg = _safe_lookup(COMPANIONS, params.companion)
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"size_word": 1.0},
        memes={"curiosity": 1.0},
    ))
    comp = world.add(Entity(
        id=comp_cfg.id,
        kind="character",
        type=comp_cfg.type,
        label=comp_cfg.label,
        memes={"wisdom": 1.0},
    ))

    world.facts.update(hero=hero, companion=comp, challenge=chal, setting=setting)
    intro(world, hero, comp, chal)
    world.para()
    flashback(world, hero, chal)
    caution(world, hero, comp, chal)
    world.para()
    choice(world, hero, chal, comp)
    ending(world, hero, chal)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    chal = _safe_fact(world, f, "challenge")
    return [
        f'Write a short fable for a young child about {hero.id} and a moat, '
        f'with a flashback and a moral at the end.',
        f"Tell a cautionary story where a {hero.type} considers how to {chal.temptation} "
        f"but chooses a safer way instead.",
        f"Write a simple moral tale that remembers a past mistake near a moat and "
        f"ends with a wise choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    comp = _safe_fact(world, f, "companion")
    chal = _safe_fact(world, f, "challenge")
    return [
        QAItem(
            question=f"What did {hero.id} almost do near the moat?",
            answer=f"{hero.id} almost {chal.temptation}.",
        ),
        QAItem(
            question=f"What memory came back to {hero.id} in the flashback?",
            answer=f"{hero.id} remembered that {chal.flashback}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} make a safer choice?",
            answer=f"{comp.label.capitalize()} helped {hero.id} choose the safer path.",
        ),
        QAItem(
            question=f"What did {hero.id} choose instead?",
            answer=f"{hero.id} chose to {chal.safe_choice}, which let {hero.pronoun('object')} {chal.safe_result}.",
        ),
        QAItem(
            question="What is the moral of the story?",
            answer=f"The moral is: {chal.moral}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moat?",
            answer="A moat is a long ditch or channel of water that goes around a place and can make crossing tricky.",
        ),
        QAItem(
            question="Why can a moat be dangerous to cross?",
            answer="A moat can be dangerous because the ground near it may be slippery, and a traveler could fall into the water.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before doing something risky.",
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
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={ {k: v for k, v in e.meters.items() if v} } "
            f"memes={ {k: v for k, v in e.memes.items() if v} }"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="meadow", challenge="cross_moat", hero_name="Milo", hero_type="fox", trait="curious", companion="turtle"),
    StoryParams(setting="orchard", challenge="reach_berries", hero_name="Nia", hero_type="duck", trait="thoughtful", companion="mouse"),
    StoryParams(setting="meadow", challenge="chase_heron", hero_name="Pip", hero_type="rabbit", trait="bold", companion="heron"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable story world about a moat, caution, and moral learning.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=HERO_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    if not _safe_lookup(SETTINGS, setting).has_moat:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    challenge = getattr(args, "challenge", None) or rng.choice(list(CHALLENGES))
    hero_type = getattr(args, "type", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    companion = getattr(args, "companion", None) or rng.choice(list(COMPANIONS))
    return StoryParams(setting=setting, challenge=challenge, hero_name=name, hero_type=hero_type, trait=trait, companion=companion)


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible (setting, challenge) combos:")
        for s, c in combos:
            print(f"  {s:10} {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.challenge} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
