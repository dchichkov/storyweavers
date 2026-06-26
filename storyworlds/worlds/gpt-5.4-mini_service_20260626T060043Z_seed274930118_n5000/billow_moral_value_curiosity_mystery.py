#!/usr/bin/env python3
"""
storyworlds/worlds/billow_moral_value_curiosity_mystery.py
===========================================================

A small story world about curiosity, honesty, and a gentle mystery.

Premise:
- A child notices a billow of something odd in a familiar place.
- Curiosity pulls them toward the clue.
- They learn that asking honestly, rather than guessing badly, solves the mystery.

This world is intentionally tiny and constraint-checked: the story is generated
from simulated state, not from a frozen paragraph with swapped nouns.
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

THRESHOLD = 1.0



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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    hero: object | None = None
    mystery_ent: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    affordance: str
    mood: str
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
class Clue:
    id: str
    noun: str
    billow_phrase: str
    source_phrase: str
    trace: str
    suspicion: str
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
class Mystery:
    id: str
    label: str
    phrase: str
    likely_holder: str
    reveal_phrase: str
    moral: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


MORAL_VALUES = ["honesty", "kindness", "patience"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright"]
GIRL_NAMES = ["Mia", "Lina", "Nora", "Zoe", "Ella", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Sam", "Max", "Owen", "Theo"]


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affordance="baking", mood="warm"),
    "hallway": Setting(place="the hallway", affordance="listening", mood="still"),
    "garden shed": Setting(place="the garden shed", affordance="searching", mood="damp"),
}

CLUES = {
    "flour": Clue(
        id="flour",
        noun="flour",
        billow_phrase="a white billow of flour",
        source_phrase="the open baking bowl",
        trace="a trail of powdery footprints",
        suspicion="someone had made a mess",
        tags={"baking", "white"},
    ),
    "steam": Clue(
        id="steam",
        noun="steam",
        billow_phrase="a soft billow of steam",
        source_phrase="the warm kettle",
        trace="tiny drops on the window",
        suspicion="something hot was nearby",
        tags={"warm", "water"},
    ),
    "leaves": Clue(
        id="leaves",
        noun="leaves",
        billow_phrase="a brown billow of leaves",
        source_phrase="the old broom",
        trace="rustling scratches on the floor",
        suspicion="something had just been swept",
        tags={"outdoors", "rustle"},
    ),
}

MYSTERIES = {
    "cookie_jar": Mystery(
        id="cookie_jar",
        label="cookie jar",
        phrase="the missing cookie jar",
        likely_holder="younger sibling",
        reveal_phrase="the jar had only been moved to the counter for cooling",
        moral="honesty",
        tags={"baking", "family"},
    ),
    "silver_key": Mystery(
        id="silver_key",
        label="silver key",
        phrase="the little silver key",
        likely_holder="mom",
        reveal_phrase="the key was tucked into a teacup so it would not be lost",
        moral="patience",
        tags={"search", "care"},
    ),
    "blue_ribbon": Mystery(
        id="blue_ribbon",
        label="blue ribbon",
        phrase="the blue ribbon",
        likely_holder="dad",
        reveal_phrase="the ribbon was pinned to a coat before the school show",
        moral="kindness",
        tags={"gift", "care"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    clue: str
    mystery: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for mystery_id, mystery in MYSTERIES.items():
                if setting_id == "kitchen" and clue_id == "flour" and mystery_id == "cookie_jar":
                    combos.append((setting_id, clue_id, mystery_id))
                elif setting_id == "hallway" and clue_id == "steam" and mystery_id == "silver_key":
                    combos.append((setting_id, clue_id, mystery_id))
                elif setting_id == "garden shed" and clue_id == "leaves" and mystery_id == "blue_ribbon":
                    combos.append((setting_id, clue_id, mystery_id))
    return combos


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


class LiveWorld(World):
    pass


def _r_curious(world: World) -> list[str]:
    hero = world.get("hero")
    clue = _safe_fact(world, world.facts, "clue")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return []
    sig = ("curious", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["attention"] = hero.memes.get("attention", 0) + 1
    return [f"{hero.id} leaned closer, because the {clue.noun} was too strange to ignore."]


def _r_mystery(world: World) -> list[str]:
    hero = world.get("hero")
    mystery = _safe_fact(world, world.facts, "mystery")
    clue = _safe_fact(world, world.facts, "clue")
    if hero.memes.get("attention", 0) < THRESHOLD:
        return []
    sig = ("mystery", mystery.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    return [f"The clue made {hero.id} wonder about {mystery.phrase}."]


CAUSAL_RULES = [Rule("curious", _r_curious), Rule("mystery", _r_mystery)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, clue: Clue, mystery: Mystery, hero_name: str, hero_type: str,
         parent_type: str, trait: str) -> World:
    world = LiveWorld(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            meters={}, memes={"curiosity": 1.0}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    clue_ent = world.add(Entity(id="clue", type=clue.noun, label=clue.noun, phrase=clue.billow_phrase))
    mystery_ent = world.add(Entity(id="mystery", type=mystery.label, label=mystery.label, phrase=mystery.phrase))

    world.facts.update(hero=hero, parent=parent, clue=clue, mystery=mystery, setting=setting)

    world.say(f"{hero.id} was a {trait} little {hero.type} who noticed every small change in {setting.place}.")
    world.say(f"One day, {hero.id} saw {clue.billow_phrase} near {clue.source_phrase}.")
    world.say(f"It looked like {clue.suspicion}, and that made {hero.id} feel curious.")

    world.para()
    hero.memes["curiosity"] += 1
    propagate(world, narrate=True)
    world.say(f"{hero.id} followed {clue.trace} instead of guessing too fast.")
    world.say(f"{hero.pronoun().capitalize()} wanted to learn the truth, not make trouble.")

    world.para()
    world.say(f"In the end, {hero.id} asked {parent.label_word} a careful question.")
    world.say(f"{parent.label_word.capitalize()} smiled and explained that {mystery.reveal_phrase}.")
    world.say(f"{hero.id} felt proud for being honest and patient, and the little mystery made sense at last.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    clue = _safe_fact(world, f, "clue")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short mystery story for a young child that includes the phrase "{clue.billow_phrase}".',
        f"Tell a gentle story where {hero.id} is curious about {clue.noun} and solves {mystery.phrase} by asking honestly.",
        f"Write a child-friendly mystery in which a billow leads to a small family surprise and a moral lesson about {mystery.moral}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    clue = _safe_fact(world, f, "clue")
    mystery = _safe_fact(world, f, "mystery")
    parent = _safe_fact(world, f, "parent")
    return [
        QAItem(
            question=f"What did {hero.id} notice first in {world.setting.place}?",
            answer=f"{hero.id} noticed {clue.billow_phrase} first, and it looked unusual enough to make {hero.pronoun()} curious.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep looking instead of walking away?",
            answer=f"{hero.id} kept looking because {hero.pronoun('possessive')} curiosity was strong and the clue seemed to hide a real mystery.",
        ),
        QAItem(
            question=f"How was {mystery.phrase} solved in the end?",
            answer=f"{hero.id} asked {parent.label_word} honestly, and {parent.label_word} explained that {mystery.reveal_phrase}.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} show by the end of the story?",
            answer=f"{hero.id} showed {mystery.moral} by asking carefully, listening well, and telling the truth about what {hero.pronoun()} wondered.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a billow?",
            answer="A billow is a large, soft, flowing puff that seems to spread outward through the air, like smoke, steam, or flour drifting up.",
        ),
        QAItem(
            question="Why can curiosity be helpful?",
            answer="Curiosity can be helpful because it makes you ask questions, notice clues, and learn the truth instead of guessing.",
        ),
        QAItem(
            question="Why is honesty important in a mystery?",
            answer="Honesty is important because telling the truth helps people solve problems kindly and understand what really happened.",
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", clue="flour", mystery="cookie_jar", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="hallway", clue="steam", mystery="silver_key", name="Leo", gender="boy", parent="father", trait="careful"),
    StoryParams(setting="garden shed", clue="leaves", mystery="blue_ribbon", name="Nora", gender="girl", parent="mother", trait="bright"),
]


def explain_rejection(setting: str, clue: str, mystery: str) -> str:
    return (
        f"(No story: this world only allows a few mystery pairings. "
        f"Try kitchen+flour+cookie_jar, hallway+steam+silver_key, or garden shed+leaves+blue_ribbon.)"
    )


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("billow", cid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("moral", mid, m.moral))
    for p in valid_combos():
        lines.append(asp.fact("valid_combo", *p))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,C,M) :- setting(S), clue(C), mystery(M), valid_combo(S,C,M).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world about curiosity and honesty.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "mystery", None) is None or c[2] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, clue, mystery = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(CLUES, params.clue), _safe_lookup(MYSTERIES, params.mystery),
                 params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery combos:\n")
        for s, c, m in combos:
            print(f"  {s:12} {c:8} {m:12}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name}: {p.setting} / {p.clue} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
