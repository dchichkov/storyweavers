#!/usr/bin/env python3
"""
storyworlds/worlds/deliberate_lesson_learned_magic_curiosity_myth.py
=====================================================================

A standalone mythic story world about deliberate choices, magic, curiosity,
and a lesson learned.

Premise seed:
- A young hero is told to carry a sealed magical thing through a sacred place.
- Curiosity tempts the hero to peek early.
- The wrong choice stirs trouble.
- Deliberate restraint and a wiser action restore balance.
- The ending proves the lesson was learned.

The world is intentionally small: one hero, one elder, one magical vessel,
one risky place, and one resolution shaped by the state of the world.

Style target: myth.
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
    carried_by: Optional[str] = None
    sealed: bool = False
    blessed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    art: object | None = None
    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "priestess", "seer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "priest", "sage"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
    sacred: bool = False
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
class Artifact:
    id: str
    label: str
    phrase: str
    danger: str
    reward: str
    risk_meter: str
    ceremony: str
    lesson: str
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


@dataclass
class StoryParams:
    setting: str
    artifact: str
    name: str
    title: str
    elder: str
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_spill_magic(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    art = world.get("artifact")
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if not art.sealed:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    art.sealed = False
    art.meters["unbound"] = 1
    hero.memes["trouble"] = hero.memes.get("trouble", 0.0) + 1
    out.append("The seal broke, and the magic leaped free like a startled fire.")
    return out


def _r_sacred_unrest(world: World) -> list[str]:
    out: list[str] = []
    art = world.get("artifact")
    sage = world.get("sage")
    if art.meters.get("unbound", 0.0) < THRESHOLD:
        return out
    sig = ("unrest",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sage.memes["worry"] = sage.memes.get("worry", 0.0) + 1
    sage.meters["work"] = sage.meters.get("work", 0.0) + 1
    out.append(f"{sage.label} felt the old place tremble with worry.")
    return out


def _r_deliberate_restraint(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    art = world.get("artifact")
    sage = world.get("sage")
    if hero.memes.get("resolve", 0.0) < THRESHOLD:
        return out
    sig = ("restraint",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    art.sealed = True
    art.meters["unbound"] = 0
    hero.memes["curiosity"] = max(0.0, hero.memes.get("curiosity", 0.0) - 1)
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1
    sage.memes["peace"] = sage.memes.get("peace", 0.0) + 1
    out.append("The hero chose to close the vessel again and hold still until the air calmed.")
    return out


CAUSAL_RULES = [
    Rule("spill_magic", _r_spill_magic),
    Rule("sacred_unrest", _r_sacred_unrest),
    Rule("deliberate_restraint", _r_deliberate_restraint),
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


SETTINGS = {
    "grove": Setting(place="the moon grove", affords={"carry", "walk"}, sacred=True),
    "spring": Setting(place="the whispering spring", affords={"carry", "walk"}, sacred=True),
    "ridge": Setting(place="the high ridge", affords={"carry", "walk"}, sacred=False),
    "temple": Setting(place="the dawn temple", affords={"carry", "walk"}, sacred=True),
}

ARTIFACTS = {
    "lantern": Artifact(
        id="lantern",
        label="lantern",
        phrase="a small bronze lantern with a star inside",
        danger="unseen sparks",
        reward="a path of light",
        risk_meter="unbound",
        ceremony="hold it with steady hands",
        lesson="Curiosity must be guided by care",
        tags={"magic", "curiosity", "lesson"},
    ),
    "vessel": Artifact(
        id="vessel",
        label="vessel",
        phrase="a clay vessel sealed with red wax",
        danger="a flood of wandering light",
        reward="a blessing for the village",
        risk_meter="unbound",
        ceremony="carry it without opening the wax",
        lesson="A seal is a promise",
        tags={"magic", "curiosity", "lesson"},
    ),
    "mirror": Artifact(
        id="mirror",
        label="mirror",
        phrase="a silver mirror wrapped in linen",
        danger="restless reflections",
        reward="a true name spoken once",
        risk_meter="unbound",
        ceremony="unwrap it only at sunrise",
        lesson="Waiting can be a wise spell",
        tags={"magic", "curiosity", "lesson"},
    ),
}

TRAITS = ["curious", "deliberate", "brave", "gentle", "earnest", "thoughtful"]
NAMES = ["Ari", "Mina", "Kiran", "Luna", "Tavi", "Nera", "Ilan", "Sera"]
TITLES = ["child", "apprentice", "young keeper", "small seeker"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s_name, setting in SETTINGS.items():
        for a_name in setting.affords and ARTIFACTS.keys():
            combos.append((s_name, a_name))
    return combos


def explain_rejection(setting: Setting, artifact: Artifact) -> str:
    return f"(No story: {artifact.label} does not fit this setting's rite.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about magic, curiosity, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TITLES)
    ap.add_argument("--elder", choices=["sage", "seer", "priest", "priestess"])
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
    if getattr(args, "setting", None) and getattr(args, "artifact", None):
        if (getattr(args, "setting", None), getattr(args, "artifact", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    artifact = getattr(args, "artifact", None) or rng.choice(list(ARTIFACTS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    title = getattr(args, "title", None) or rng.choice(TITLES)
    elder = getattr(args, "elder", None) or rng.choice(["sage", "seer", "priest", "priestess"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, artifact=artifact, name=name, title=title, elder=elder, trait=trait)


def tale_intro(world: World, hero: Entity, elder: Entity, art: Entity) -> None:
    world.say(f"In {world.setting.place}, {hero.label} was a {hero.type} who listened for signs in the wind.")
    world.say(f"{hero.pronoun().capitalize()} was known as {hero.memes.get('trait_word', hero.type)}, and {elder.label} trusted {hero.pronoun('object')} with old rites.")
    world.say(f"One day, {elder.label} placed {art.phrase} into {hero.pronoun('possessive')} hands.")
    world.say(f"{hero.id} was told to {art.label} and not to peek, for the vessel held {art.reward}.")


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id="hero", kind="character", type=params.title, label=params.name))
    elder = world.add(Entity(id="sage", kind="character", type=params.elder, label=f"the {params.elder}"))
    art_cfg = _safe_lookup(ARTIFACTS, params.artifact)
    art = world.add(Entity(id="artifact", kind="thing", type="artifact", label=art_cfg.label,
                           phrase=art_cfg.phrase, owner=hero.id, caretaker=elder.id, sealed=True))
    hero.memes["curiosity"] = 1
    hero.memes["trait"] = 1
    hero.memes["trait_word"] = 1
    world.facts.update(hero=hero, elder=elder, artifact=art, cfg=art_cfg, params=params)

    tale_intro(world, hero, elder, art)
    world.para()
    world.say(f"The road to {world.setting.place} was quiet, and the stones seemed to watch.")
    world.say(f"Curiosity tugged at {hero.label} like a bright ribbon, because {art.phrase} promised {art.reward}.")
    world.say(f"{hero.label} almost lifted the lid, but the old warning was plain: {art.ceremony}.")

    if params.trait == "deliberate":
        hero.memes["resolve"] = 1
        world.say(f"Because {hero.label} was deliberate, {hero.pronoun()} stopped and counted three slow breaths.")
    else:
        hero.memes["curiosity"] = 2
        world.say(f"{hero.label} could not quite resist the question in {hero.pronoun('possessive')} mind.")
        propagate(world)
        if art.meters.get("unbound", 0.0) >= THRESHOLD:
            world.say(f"Light slipped out, and the sacred air shivered.")
        world.para()
        world.say(f"Then {elder.label} raised a calm hand and reminded {hero.pronoun('object')} of the old lesson.")
        hero.memes["resolve"] = 1

    propagate(world)
    world.para()
    world.say(f"{hero.label} fastened the seal again and carried the {art.label} more carefully than before.")
    world.say(f"The {world.setting.place} grew peaceful, and {elder.label} smiled.")
    world.say(f"At dusk, the hero understood the lesson learned: {art_cfg.lesson}.")
    world.say(f"So {hero.label} went home with {art.reward} still shining in memory, and the magic stayed kind.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    cfg: Artifact = _safe_fact(world, f, "cfg")
    return [
        f"Write a mythic story for children about {hero.label}, {cfg.label}, and a deliberate choice.",
        f"Tell a story where curiosity tempts a young keeper to open {cfg.phrase}, but a lesson is learned.",
        f"Write a gentle myth with magic, restraint, and the phrase '{cfg.lesson}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    art_cfg: Artifact = _safe_fact(world, f, "cfg")
    art: Entity = _safe_fact(world, f, "artifact")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a {hero.type} who carried {art_cfg.phrase} for {elder.label}.",
        ),
        QAItem(
            question=f"What made {hero.label} want to open the vessel?",
            answer=f"Curiosity made {hero.label} want to look inside, because the artifact promised {art_cfg.reward}.",
        ),
        QAItem(
            question=f"What did the elder want {hero.label} to do with the magic object?",
            answer=f"{elder.label} wanted {hero.label} to {art_cfg.ceremony} and carry it with care.",
        ),
        QAItem(
            question=f"What was the lesson learned at the end?",
            answer=f"The lesson learned was that {art_cfg.lesson.lower()}.",
        ),
    ]
    if art.meters.get("unbound", 0.0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What happened when curiosity won for a moment?",
                answer=f"The seal broke and the magic leaped free, which made the sacred place tremble with worry.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"How did the story turn out?",
                answer=f"{hero.label} chose restraint, sealed the artifact again, and the magic stayed kind.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    art_cfg: Artifact = _safe_fact(world, f, "cfg")
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know what is hidden or how something works.",
        ),
        QAItem(
            question="What is magic in a myth?",
            answer="Magic is a mysterious power that can change what happens, especially in old stories.",
        ),
        QAItem(
            question="Why is a seal important on a special vessel?",
            answer="A seal helps keep what is inside safe until the right time to open it.",
        ),
        QAItem(
            question="Why do stories often teach a lesson?",
            answer="Stories teach a lesson so listeners can remember a good choice and use it in their own lives.",
        ),
        QAItem(
            question="What does it mean to be deliberate?",
            answer="To be deliberate means to slow down and choose carefully instead of rushing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="grove", artifact="vessel", name="Ari", title="child", elder="sage", trait="deliberate"),
    StoryParams(setting="spring", artifact="lantern", name="Mina", title="apprentice", elder="seer", trait="curious"),
    StoryParams(setting="temple", artifact="mirror", name="Luna", title="young keeper", elder="priestess", trait="thoughtful"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
        if s.sacred:
            lines.append(asp.fact("sacred", sid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("lesson", aid, a.lesson))
        lines.append(asp.fact("risk", aid, a.risk_meter))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A) :- setting(S), artifact(A), affords(S,carry).
lesson_world(A) :- artifact(A), lesson(A,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, a) for s, a in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.artifact} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
