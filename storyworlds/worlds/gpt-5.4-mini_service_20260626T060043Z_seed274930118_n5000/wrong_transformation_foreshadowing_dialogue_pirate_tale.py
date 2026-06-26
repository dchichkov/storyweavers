#!/usr/bin/env python3
"""
storyworlds/worlds/wrong_transformation_foreshadowing_dialogue_pirate_tale.py
==============================================================================

A standalone story world for a tiny pirate tale with a wrong turn, a magical
transformation, foreshadowing, and spoken dialogue.

Seed tale outline:
---
A young pirate wants to open a curious chest aboard a little ship. The captain
warns that the chest answers to the right song, not the wrong one. The child
tries anyway, saying the wrong words. The chest bursts with sea-light and
changes the child's prized hat into a shiny crab-shell cap. The captain had
foreshadowed the danger, and together they calm the magic with the right song
and a bit of saltwater, turning the hat back again.

Design notes:
---
- This world is small and classical: one hero, one cautioning elder, one prized
  object, one hazardous action, one magical transformation, one resolution.
- The model tracks both physical meters and emotional memes.
- Dialogue and foreshadowing are not just style ornaments; they are world-state
  events that drive the turn and the ending.
- The word "wrong" is intentionally part of the story vocabulary and the
  generated text.
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
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self):
        for k in ["shine", "curse", "changed", "salty", "clean"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "warning", "curiosity", "relief", "bond", "conflict", "foreshadow"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captainess"}
        male = {"boy", "father", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Action:
    id: str
    verb: str
    gerund: str
    warning: str
    wrong_words: str
    effect: str
    target_meter: str
    target_value: float
    zone: set[str]
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Remedy:
    id: str
    label: str
    verb: str
    chant: str
    ingredients: str
    fixes: str
    covers: set[str]
    guards: set[str]
    plural: bool = False
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.transformed: bool = False
        self.restored: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    hero_name: str
    hero_gender: str
    elder_role: str
    trait: str
    seed: Optional[int] = None
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


SETTINGS = {
    "ship": Setting(place="the little ship", affords={"chest", "song"}),
    "cove": Setting(place="the moonlit cove", affords={"shell", "song"}),
    "island": Setting(place="the palm island", affords={"idol", "song"}),
    "dock": Setting(place="the windy dock", affords={"bottle", "song"}),
}

ACTIONS = {
    "chest": Action(
        id="chest",
        verb="open the chest",
        gerund="opening the chest",
        warning="Don't use the wrong song on that chest",
        wrong_words="wrong words",
        effect="the chest answered with a flash of sea-light",
        target_meter="changed",
        target_value=1.0,
        zone={"torso", "head"},
        keyword="chest",
        tags={"sea", "gold", "magic"},
    ),
    "shell": Action(
        id="shell",
        verb="turn the shell",
        gerund="turning the shell",
        warning="Don't turn it the wrong way",
        wrong_words="wrong way",
        effect="the shell gave a bright, chilly shimmer",
        target_meter="changed",
        target_value=1.0,
        zone={"head"},
        keyword="shell",
        tags={"sea", "magic"},
    ),
    "idol": Action(
        id="idol",
        verb="touch the idol",
        gerund="touching the idol",
        warning="Don't touch it with a wrong hand",
        wrong_words="wrong hand",
        effect="the idol sent a green sea-glow across the deck",
        target_meter="changed",
        target_value=1.0,
        zone={"torso", "head"},
        keyword="idol",
        tags={"gold", "magic"},
    ),
    "bottle": Action(
        id="bottle",
        verb="sip the bottle",
        gerund="sipping the bottle",
        warning="Don't sip the wrong bottle",
        wrong_words="wrong bottle",
        effect="the bottle burped out a fizz of silver foam",
        target_meter="changed",
        target_value=1.0,
        zone={"head"},
        keyword="bottle",
        tags={"sea", "magic"},
    ),
}

PRIZES = {
    "hat": Prize("hat", "pirate hat", "a bright pirate hat", "head"),
    "boots": Prize("boots", "sea boots", "sturdy sea boots", "feet", plural=True),
    "shirt": Prize("shirt", "striped shirt", "a striped shirt with a golden patch", "torso"),
    "sash": Prize("sash", "red sash", "a red sash with a brass buckle", "torso"),
}

REMEDIES = [
    Remedy("salt_song", "salt song", "sing", "the right song", "saltwater and a soft humming tune", "calm the magic", {"head", "torso"}, {"sea", "magic"}),
    Remedy("brine_rinse", "brine rinse", "rinse", "the proper sea-shanty", "a pail of brine", "wash away the curse", {"head", "feet", "torso"}, {"magic"}),
]


GIRL_NAMES = ["Mara", "Nina", "Tessa", "Lina", "Ivy", "Ruby"]
BOY_NAMES = ["Finn", "Jace", "Oren", "Kai", "Pip", "Niko"]
TRAITS = ["brave", "curious", "merry", "small", "quick", "bold"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    prize = _safe_fact(world, world.facts, "prize")
    action = _safe_fact(world, world.facts, "action")
    if hero.meters[action.target_meter] < THRESHOLD:
        return out
    if world.transformed:
        return out
    world.transformed = True
    sig = ("transform", prize.id, action.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["changed"] += 1
    hero.memes["fear"] += 1
    out.append(f"{action.effect} and {hero.id}'s {prize.label} turned strange and shiny.")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    elder = _safe_fact(world, world.facts, "elder")
    action = _safe_fact(world, world.facts, "action")
    prize = _safe_fact(world, world.facts, "prize")
    sig = ("foreshadow", action.id, prize.id)
    if sig in world.fired:
        return out
    if hero.memes["curiosity"] < THRESHOLD:
        return out
    world.fired.add(sig)
    elder.memes["foreshadow"] += 1
    world.say(f'Before the trouble, {elder.id} had whispered, "{action.warning}."')
    return out


def _r_resolve(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    elder = _safe_fact(world, world.facts, "elder")
    prize = _safe_fact(world, world.facts, "prize")
    remedy = world.facts.get("remedy")
    if not remedy or prize.meters["changed"] < THRESHOLD:
        return out
    sig = ("resolve", prize.id, remedy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["changed"] = 0
    prize.meters["clean"] += 1
    hero.memes["fear"] = 0
    hero.memes["relief"] += 1
    world.restored = True
    out.append(f'{elder.id} held up the {remedy.label} and said, "{remedy.chant}."')
    out.append(f"The magic eased, and {hero.id}'s {prize.label} went back to normal.")
    return out


CAUSAL_RULES = [
    Rule("foreshadow", _r_foreshadow),
    Rule("transformation", _r_transformation),
    Rule("resolve", _r_resolve),
]


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


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_remedy(action: Action, prize: Prize) -> Optional[Remedy]:
    for r in REMEDIES:
        if prize.region in r.covers and action.tags & r.guards:
            return r
    return None


def tell(setting: Setting, action: Action, prize_cfg: Prize,
         hero_name: str, hero_gender: str, elder_role: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    elder = world.add(Entity(id=elder_role, kind="character", type=elder_role, label=f"the {elder_role}"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=elder.id,
                             region=prize_cfg.region, plural=prize_cfg.plural))
    world.facts.update(hero=hero, elder=elder, prize=prize, action=action, remedy=select_remedy(action, prize))

    hero.memes["curiosity"] += 1
    hero.memes["joy"] += 1

    world.say(f"{hero.id} was a little {trait} pirate aboard {setting.place}.")
    world.say(f"{hero.id} loved {action.gerund} and staring at {prize.phrase}.")
    world.say(f"{elder.id} watched over the deck and said, \"Be careful, matey.\"")
    world.say(f"The sea breeze felt lively, and the old ship creaked like a sleepy gull.")

    world.para()
    world.say(f"One gray night, {hero.id} and {elder.id} stood near a curious chest.")
    world.say(f'{hero.id} said, "I can open it myself!"')
    world.say(f'{elder.id} answered, "Only if you use the right song, not the wrong one."')
    hero.memes["warning"] += 1
    hero.memes["curiosity"] += 1
    world.say(f"But {hero.id} wanted to {action.verb} anyway.")
    hero.meters[action.target_meter] += 1
    propagate(world, narrate=True)

    world.para()
    if world.transformed:
        world.say(f'{hero.id} gasped, "My {prize.label}!"')
        world.say(f'{elder.id} said, "I told you, the wrong way wakes the sea-magic."')
        if world.facts["remedy"]:
            remedy = _safe_fact(world, world.facts, "remedy")
            world.say(f'{hero.id} whispered, "Can we fix it?"')
            world.say(f'{elder.id} nodded. "Aye. We can {remedy.verb} it back."')
            propagate(world, narrate=True)
    else:
        world.say(f"{hero.id} opened the chest safely, and the night stayed calm.")

    world.facts["hero"] = hero
    world.facts["elder"] = elder
    world.facts["prize"] = prize
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, action, prize = f["hero"], f["elder"], f["action"], f["prize"]
    return [
        f'Write a short pirate tale for a child where {hero.id} hears a warning about the wrong way to {action.verb}.',
        f"Tell a story with dialogue, foreshadowing, and a magical transformation involving {hero.id}'s {prize.label}.",
        f'Write a sea adventure where a {hero.type} pirate named {hero.id} nearly makes a wrong choice and then fixes it with help from {elder.id}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, action, prize = f["hero"], f["elder"], f["action"], f["prize"]
    qa = [
        QAItem(
            question=f"Who is the pirate child in the story?",
            answer=f"The pirate child is {hero.id}, a little {hero.type} who loves the sea.",
        ),
        QAItem(
            question=f"What did {elder.id} warn {hero.id} about before the trouble?",
            answer=f"{elder.id} warned {hero.id} not to use the wrong way to {action.verb}.",
        ),
        QAItem(
            question=f"What changed when {hero.id} made the wrong choice?",
            answer=f"{hero.id}'s {prize.label} transformed and turned strange and shiny for a while.",
        ),
    ]
    if world.transformed:
        qa.append(
            QAItem(
                question=f"How did the story fix the wrong transformation?",
                answer=f"{elder.id} used the {world.facts['remedy'].label} and the right song to calm the magic and turn the {prize.label} back.",
            )
        )
    return qa


KNOWLEDGE = {
    "ship": [(
        "What is a ship for?",
        "A ship is a boat that carries people across water."
    )],
    "sea": [(
        "What is the sea?",
        "The sea is a very large body of saltwater."
    )],
    "magic": [(
        "What does magical mean?",
        "Magical means something seems to do impossible things, like changing shape in a story."
    )],
    "salt": [(
        "Why is saltwater salty?",
        "Saltwater is salty because it has dissolved salt in it."
    )],
    "gold": [(
        "What is gold?",
        "Gold is a shiny yellow metal that people often think is special."
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    tags.add("ship")
    if world.facts["action"].id in {"chest", "shell", "bottle"}:
        tags.add("magic")
    if "sea" in world.facts["action"].tags:
        tags.add("sea")
    out: list[QAItem] = []
    for t in ["ship", "sea", "magic", "salt", "gold"]:
        if t in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[t])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", action="chest", prize="hat", hero_name="Mara", hero_gender="girl", elder_role="captain", trait="brave"),
    StoryParams(place="cove", action="shell", prize="boots", hero_name="Finn", hero_gender="boy", elder_role="mate", trait="curious"),
    StoryParams(place="island", action="idol", prize="shirt", hero_name="Nina", hero_gender="girl", elder_role="captain", trait="bold"),
    StoryParams(place="dock", action="bottle", prize="sash", hero_name="Kai", hero_gender="boy", elder_role="old sailor", trait="merry"),
]


def explain_rejection(action: Action, prize: Prize) -> str:
    if not prize_at_risk(action, prize):
        return f"(No story: {action.gerund} does not threaten a {prize.label}, so there is no honest transformation to warn about.)"
    return "(No story: no remedy in this tiny world can reasonably undo that exact wrong transformation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale world with wrong transformation, foreshadowing, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["captain", "mate", "old sailor"])
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
    if getattr(args, "action", None) and getattr(args, "prize", None):
        if not prize_at_risk(_safe_lookup(ACTIONS, getattr(args, "action", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = []
    for place, setting in SETTINGS.items():
        if getattr(args, "place", None) and getattr(args, "place", None) != place:
            continue
        for a in setting.affords:
            if getattr(args, "action", None) and getattr(args, "action", None) != a:
                continue
            for p in PRIZES:
                if getattr(args, "prize", None) and getattr(args, "prize", None) != p:
                    continue
                pr = _safe_lookup(PRIZES, p)
                if getattr(args, "gender", None) and getattr(args, "gender", None) not in pr.genders:
                    continue
                if prize_at_risk(_safe_lookup(ACTIONS, a), pr) and select_remedy(_safe_lookup(ACTIONS, a), pr):
                    combos.append((place, a, p))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    pr = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["captain", "mate", "old sailor"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, hero_name=name, hero_gender=gender, elder_role=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize),
                 params.hero_name, params.hero_gender, params.elder_role, params.trait)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("target_meter", aid, a.target_meter))
        lines.append(asp.fact("wrong_words", aid, a.wrong_words))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for rid, r in zip(["salt_song", "brine_rinse"], REMEDIES):
        lines.append(asp.fact("remedy", rid))
        for c in sorted(r.covers):
            lines.append(asp.fact("covers", rid, c))
        for g in sorted(r.guards):
            lines.append(asp.fact("guards", rid, g))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), region(P,R).
has_fix(A,P) :- prize_at_risk(A,P), remedy(R), covers(R,RR), region(P,RR), tag(A,T), guards(R,T).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for a in setting.affords:
            act = _safe_lookup(ACTIONS, a)
            for pid, p in PRIZES.items():
                if prize_at_risk(act, p) and select_remedy(act, p):
                    combos.append((place, a, pid))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible story combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
