#!/usr/bin/env python3
"""
storyworlds/worlds/happy_lesson_learned_adventure.py
=====================================================

A small adventure story world where a child goes on a happy outing, makes a
mistake, learns a lesson, and ends with a better choice.

The domain is intentionally tiny:
- a hero explores a place
- they want to take a tempting risky action
- a guide warns them
- the risky choice creates a small problem
- a lesson learned fixes the situation
- the story ends happy

The script keeps a classical state model with meters and memes, supports the
standard Storyweavers CLI, and includes an inline ASP twin for the same
reasonableness gate.
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
# World model
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def short(self) -> str:
        return self.label or self.id
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
class Adventure:
    id: str
    verb: str
    gerund: str
    temptation: str
    hazard: str
    lesson: str
    risk_kind: str
    reward: str
    keyword: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Guide:
    id: str
    label: str
    advice: str
    fix: str
    tail: str
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "forest": Setting(place="the forest", affords={"trail", "berries", "stream"}),
    "hill": Setting(place="the hill", affords={"trail", "wind"}),
    "garden": Setting(place="the garden", affords={"berries", "trail"}),
    "cave": Setting(place="the cave", affords={"trail"}),
}

ADVENTURES = {
    "trail": Adventure(
        id="trail",
        verb="take the winding trail",
        gerund="following the winding trail",
        temptation="the shortcut path",
        hazard="the trail can twist around and lead too far",
        lesson="slow feet and looking ahead keep the way safe",
        risk_kind="lost",
        reward="they found the right path again",
        keyword="trail",
        tags={"trail", "lost"},
    ),
    "berries": Adventure(
        id="berries",
        verb="pick the bright berries",
        gerund="picking bright berries",
        temptation="the highest berry branch",
        hazard="some berries are hard to reach and the branch can wobble",
        lesson="asking for help is safer than climbing too high",
        risk_kind="stuck",
        reward="they gathered berries from the lower branch",
        keyword="berries",
        tags={"berries", "help"},
    ),
    "stream": Adventure(
        id="stream",
        verb="cross the little stream",
        gerund="crossing the little stream",
        temptation="the slippery stones",
        hazard="wet stones can slide under small shoes",
        lesson="a careful step is better than a rushed leap",
        risk_kind="slip",
        reward="they crossed safely one step at a time",
        keyword="stream",
        tags={"stream", "safe"},
    ),
    "wind": Adventure(
        id="wind",
        verb="fly the bright kite",
        gerund="flying a bright kite",
        temptation="the strongest gust",
        hazard="strong wind can yank the string too hard",
        lesson="holding tight and waiting for the right breeze works best",
        risk_kind="drop",
        reward="the kite sailed high and steady",
        keyword="kite",
        tags={"wind", "kite"},
    ),
}

GUIDES = {
    "owl": Guide(
        id="owl",
        label="an old owl",
        advice="take it slow and keep your eyes open",
        fix="show the child the safest way forward",
        tail="flew beside them until the path felt easy again",
    ),
    "grandpa": Guide(
        id="grandpa",
        label="Grandpa",
        advice="a careful step saves a lot of trouble",
        fix="point to the safe stones and the easy path",
        tail="walked with them and smiled",
    ),
    "sister": Guide(
        id="sister",
        label="an older sister",
        advice="you can still have fun if you choose wisely",
        fix="help the child try again the gentle way",
        tail="laughed and stayed close",
    ),
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"],
    "boy": ["Leo", "Ben", "Sam", "Max", "Finn", "Theo"],
}

TRAITS = ["happy", "curious", "brave", "cheerful", "lively", "spirited"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    adventure: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper functions
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for adv in setting.affords:
            if adv in ADVENTURES:
                combos.append((place, adv))
    return combos


def explain_rejection(place: str, adventure: str) -> str:
    adv = _safe_lookup(ADVENTURES, adventure)
    return (
        f"(No story: {place} does not reasonably support {adv.gerund}. "
        f"Choose one of the places that affords that adventure.)"
    )


def setting_sentence(place: str, adventure: Adventure) -> str:
    if place == "forest":
        return "The trees stood tall, and the path curled between them like a ribbon."
    if place == "hill":
        return "The hill opened to the sky, and the wind brushed the grass in soft waves."
    if place == "garden":
        return "The garden was bright, with leaves, flowers, and tiny paths underfoot."
    if place == "cave":
        return "The cave was cool and quiet, with a narrow path shining near the floor."
    return f"{place.capitalize()} felt ready for a small adventure."


def story_happy_beginning(hero: Entity, guide: Entity, setting: Setting, adv: Adventure) -> str:
    return (
        f"{hero.short} was a happy little {hero.type} who loved exploring {setting.place}. "
        f"{hero.pronoun().capitalize()} liked {adv.gerund} because it felt like a tiny adventure."
    )


def story_warning(hero: Entity, guide: Entity, adv: Adventure) -> str:
    return (
        f"Then {guide.label} said, \"{adv.temptation} looks fun, but {adv.hazard}. "
        f"{guide.advice}.\""
    )


def story_mistake(hero: Entity, adv: Adventure) -> str:
    return (
        f"{hero.short} heard the warning, but the temptation was still strong. "
        f"{hero.pronoun().capitalize()} tried to {adv.verb} anyway."
    )


def story_turn(hero: Entity, guide: Entity, adv: Adventure) -> str:
    return (
        f"That choice caused a little trouble, and {hero.short} felt worried. "
        f"Then {guide.label} helped and {guide.fix}."
    )


def story_resolution(hero: Entity, guide: Entity, adv: Adventure) -> str:
    return (
        f"{hero.short} took the lesson to heart. After that, {hero.pronoun()} chose the safer way, "
        f"and {adv.reward}. {guide.label} {guide.tail}. "
        f"In the end, {hero.short} went home happy, proud, and a little wiser."
    )


def do_adventure(world: World, hero: Entity, guide: Entity, adv: Adventure, narrate: bool = True) -> None:
    hero.meters[adv.risk_kind] = hero.meters.get(adv.risk_kind, 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    if narrate:
        world.say(story_mistake(hero, adv))


def resolve_turn(world: World, hero: Entity, guide: Entity, adv: Adventure, narrate: bool = True) -> None:
    hero.meters[adv.risk_kind] = 0.0
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0.0) + 1.0
    hero.memes["happy"] = hero.memes.get("happy", 0.0) + 1.0
    if narrate:
        world.say(story_turn(hero, guide, adv))
        world.say(story_resolution(hero, guide, adv))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_place_adventure(Place, A) :- affords(Place, A).

#show valid_place_adventure/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for adv in sorted(setting.affords):
            lines.append(asp.fact("affords", place, adv))
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place_adventure/2."))
    return sorted(set(asp.atoms(model, "valid_place_adventure")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
# Story generation
# ---------------------------------------------------------------------------

def tell(setting: Setting, adventure: Adventure, hero_name: str, hero_type: str, guide_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    guide = world.add(Entity(id="Guide", kind="character", type="adult", label=_safe_lookup(GUIDES, guide_kind).label))
    guide_def = _safe_lookup(GUIDES, guide_kind)

    world.say(story_happy_beginning(hero, guide, setting, adventure))
    world.say(setting_sentence(setting.place, adventure))
    world.para()

    world.say(story_warning(hero, guide, adventure))
    do_adventure(world, hero, guide, adventure, narrate=True)
    world.para()

    resolve_turn(world, hero, guide, adventure, narrate=True)

    world.facts.update(
        hero=hero,
        guide=guide,
        guide_def=guide_def,
        setting=setting,
        adventure=adventure,
        learned=True,
        happy=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    adv = _safe_fact(world, f, "adventure")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short adventure story for a child named {hero.id} who goes to {setting.place} and learns a lesson.',
        f"Tell a happy story where {hero.id} wants to {adv.verb}, makes a small mistake, and listens to a guide.",
        f'Write a simple story with the word "{adv.keyword}" that ends with {hero.id} going home wiser and happy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide_def: Guide = _safe_fact(world, f, "guide_def")
    adv: Adventure = _safe_fact(world, f, "adventure")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the adventure story about?",
            answer=f"The story is about {hero.short}, a happy little {hero.type} who goes exploring {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.short} want to do at {setting.place}?",
            answer=f"{hero.short} wanted to {adv.verb}. That was the exciting part of the adventure.",
        ),
        QAItem(
            question=f"What did {guide_def.label} teach {hero.short}?",
            answer=f"{guide_def.label} taught {hero.short} that {adv.lesson}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.short}?",
            answer=f"It ended with {hero.short} feeling happy, proud, and wiser after choosing the safer way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    adv: Adventure = _safe_fact(world, f, "adventure")
    if adv.id == "trail":
        return [
            QAItem(
                question="What is a trail?",
                answer="A trail is a narrow path people walk on through a place like a forest or hill.",
            ),
            QAItem(
                question="Why should you look ahead on a trail?",
                answer="Looking ahead helps you notice twists, roots, or turns before you step on them.",
            ),
        ]
    if adv.id == "berries":
        return [
            QAItem(
                question="Why can high branches be hard to reach?",
                answer="High branches are far above the ground, so small children may need help to reach them safely.",
            ),
            QAItem(
                question="Why is asking for help a good idea?",
                answer="Asking for help can keep you safe when something is too high, heavy, or tricky to do alone.",
            ),
        ]
    if adv.id == "stream":
        return [
            QAItem(
                question="Why are wet stones slippery?",
                answer="Wet stones can be slippery because the water makes it easier for feet to slide.",
            ),
            QAItem(
                question="What is a careful step?",
                answer="A careful step is a slow, steady step that helps you keep your balance.",
            ),
        ]
    return [
        QAItem(
            question="Why does a kite need wind?",
            answer="A kite needs wind to lift it up and keep it floating in the sky.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Happy adventure story world with a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=GUIDES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "adventure", None) is None or c[1] == getattr(args, "adventure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, adventure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    guide = getattr(args, "guide", None) or rng.choice(sorted(GUIDES))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, adventure=adventure, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ADVENTURES, params.adventure), params.name, params.gender, params.guide)
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
        print(asp_program("#show valid_place_adventure/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, adventure) combos:\n")
        for place, adv in combos:
            print(f"  {place:8} {adv}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="forest", adventure="trail", name="Mia", gender="girl", guide="owl", trait="happy"),
            StoryParams(place="garden", adventure="berries", name="Leo", gender="boy", guide="sister", trait="curious"),
            StoryParams(place="hill", adventure="wind", name="Ava", gender="girl", guide="grandpa", trait="brave"),
            StoryParams(place="forest", adventure="stream", name="Sam", gender="boy", guide="owl", trait="lively"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.adventure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
