#!/usr/bin/env python3
"""
storyworlds/worlds/lion_deep_puddle_flashback_transformation_rhyming_story.py
===============================================================================

A small story world about a lion, a deep puddle, a flashback, and a gentle
transformation, told in a rhyming story style.

The premise:
- A lion loves a deep puddle and wants to stomp, splash, and sing.
- A flashback reminds the lion why the puddle once felt scary.
- A calm helper and a brave choice lead to a transformation.
- The ending shows what changed in the lion's body and feelings.

This script follows the Storyweavers world contract:
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager results.py import; lazy asp.py import in ASP helpers
- ASP twin with facts and rules
- story/state/QA driven by the simulated world
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ally: object | None = None
    lion: object | None = None
    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = __import__('collections').defaultdict(float)
        if self.memes is None:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "lion":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str = "the deep puddle"
    deep: bool = True
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
    rush: str
    mess: str
    soil: str
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
class Transformation:
    id: str
    old_state: str
    new_state: str
    trigger: str
    ending_image: str
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
class Helper:
    id: str
    label: str
    advice: str
    gesture: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    action: str
    transformation: str
    name: str
    helper: str
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


SETTINGS = {
    "deep_puddle": Setting(place="the deep puddle", deep=True, affords={"splash", "dance", "sing"}),
}

ACTIONS = {
    "splash": Action(
        id="splash",
        verb="splash in the deep puddle",
        gerund="splashing in the deep puddle",
        rush="rush to the puddle",
        mess="wet",
        soil="soaked and splashed",
        keyword="puddle",
        tags={"puddle", "wet"},
    ),
    "dance": Action(
        id="dance",
        verb="dance at the deep puddle",
        gerund="dancing by the deep puddle",
        rush="tiptoe to the puddle",
        mess="muddy",
        soil="mud-spotted and splashed",
        keyword="puddle",
        tags={"puddle", "mud"},
    ),
    "sing": Action(
        id="sing",
        verb="sing beside the deep puddle",
        gerund="singing beside the deep puddle",
        rush="stride to the puddle",
        mess="echoing",
        soil="loud and bright",
        keyword="puddle",
        tags={"puddle", "sound"},
    ),
}

TRANSFORMATIONS = {
    "brave": Transformation(
        id="brave",
        old_state="shy and stuck",
        new_state="brave and bouncy",
        trigger="a gentle reminder and one tiny step",
        ending_image="a brave lion with a shiny splash of joy",
    ),
    "muddy": Transformation(
        id="muddy",
        old_state="clean and careful",
        new_state="muddy and merry",
        trigger="the first happy splash",
        ending_image="a muddy lion with a laughing mane",
    ),
    "sparkling": Transformation(
        id="sparkling",
        old_state="flat and frowny",
        new_state="sparkling and sunny",
        trigger="a song that made the puddle glow",
        ending_image="a sparkling lion with bright, wet paws",
    ),
}

HELPERS = {
    "duck": Helper(
        id="duck",
        label="a duck",
        advice="Deep puddles are big, but a little splash can still be sweet.",
        gesture="waddled beside him and nodded",
    ),
    "frog": Helper(
        id="frog",
        label="a frog",
        advice="When a puddle feels deep, go slow and keep your paws steady.",
        gesture="blinked and croaked a calm song",
    ),
    "mouse": Helper(
        id="mouse",
        label="a mouse",
        advice="A brave heart can start with one small step.",
        gesture="sat on a stone and smiled softly",
    ),
}

HERO_NAMES = ["Leo", "Milo", "Nico", "Rory", "Theo", "Arlo"]
TRAITS = ["curious", "gentle", "shy", "playful", "brave", "bouncy"]

KNOWLEDGE = {
    "lion": [
        ("What is a lion?",
         "A lion is a big wild cat with a strong voice, furry paws, and a mane on many grown-up lions.")],
    "puddle": [
        ("What is a puddle?",
         "A puddle is a little pool of water on the ground after rain or splashing.")],
    "deep": [
        ("What does deep mean?",
         "Deep means something goes far down, so you cannot see the bottom right away.")],
    "flashback": [
        ("What is a flashback in a story?",
         "A flashback is when the story briefly remembers something that happened before.")],
    "transformation": [
        ("What is a transformation?",
         "A transformation is a change from one state to another, like shy turning into brave.")],
    "rhyming": [
        ("What is a rhyming story?",
         "A rhyming story uses words or lines that sound alike at the ends, like glow and show.")],
}

KNOWLEDGE_ORDER = ["lion", "puddle", "deep", "flashback", "transformation", "rhyming"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming story world about a lion, a deep puddle, a flashback, and a transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    action = getattr(args, "action", None) or rng.choice(sorted(_safe_lookup(SETTINGS, place).affords))
    if action not in _safe_lookup(SETTINGS, place).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    transformation = getattr(args, "transformation", None) or rng.choice(list(TRANSFORMATIONS))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, transformation=transformation, name=name, helper=helper, trait=trait)


def _do_action(world: World, lion: Entity, action: Action) -> None:
    lion.meters[action.mess] = lion.meters.get(action.mess, 0.0) + 1.0
    lion.memes["joy"] = lion.memes.get("joy", 0.0) + 1.0
    if action.id == "splash":
        lion.meters["wet"] = lion.meters.get("wet", 0.0) + 1.0


def tell(setting: Setting, action: Action, trans: Transformation, name: str, helper: Helper, trait: str) -> World:
    world = World(setting)
    lion = world.add(Entity(id=name, kind="character", type="lion", traits=["little", trait]))
    ally = world.add(Entity(id=helper.id, kind="character", type=helper.id, label=helper.label))
    world.facts.update(lion=lion, helper=ally, action=action, trans=trans, setting=setting, helper_cfg=helper)

    world.say(f"{name} was a little {trait} lion, with paws that liked to roam,")
    world.say(f"and {name} loved {action.gerund} near the deep puddle at home.")

    world.say(f"The puddle was deep, with a silver-smooth gleam,")
    world.say(f"it winked like a mirror and wobbled with dream.")

    world.para()
    world.say(f"{name} wanted to {action.verb}, with a hop and a roar,")
    world.say(f"but a flashback came floating from not long before.")

    world.say(f"{name} remembered a day when the puddle looked wide,")
    world.say(f"and {name} had stepped in too fast, with a splash and a slide.")

    world.say(f"That memory made {name} go still for a beat,")
    world.say(f"for deep puddles can shimmer and tickle your feet.")

    world.para()
    world.say(f"Then {helper.label} came near and {helper.gesture},")
    world.say(f"and said, '{helper.advice}'")

    world.say(f"{name} took one small step, then another, so slow,")
    world.say(f"and chose to move gently where soft ripples go.")

    lion.memes["fear"] = 0.0
    lion.memes["courage"] = lion.memes.get("courage", 0.0) + 1.0
    _do_action(world, lion, action)

    world.para()
    lion.meters["changed"] = 1.0
    lion.memes["changed"] = 1.0
    world.say(f"Then came the transformation, so bright to behold:")
    world.say(f"{name} went from {trans.old_state} to {trans.new_state}, bold.")

    world.say(f"{name} splashed and sang, and the deep puddle shone,")
    world.say(f"with {trans.ending_image} to take home and own.")

    world.say(f"At last {name} stood smiling, all shiny and spry,")
    world.say(f"the puddle was friendlier now, and the sky felt nearby.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lion = _safe_fact(world, f, "lion")
    action = _safe_fact(world, f, "action")
    trans = _safe_fact(world, f, "trans")
    return [
        f'Write a rhyming story for a small child about a lion named {lion.id} and a {world.setting.place}.',
        f"Tell a gentle flashback story where {lion.id} wants to {action.verb} but remembers an earlier wobble, then changes with help.",
        f"Create a simple rhyming tale that ends with {trans.ending_image}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lion: Entity = _safe_fact(world, f, "lion")
    helper_cfg: Helper = _safe_fact(world, f, "helper_cfg")
    action: Action = _safe_fact(world, f, "action")
    trans: Transformation = _safe_fact(world, f, "trans")

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little {lion.traits[-1]} lion named {lion.id} near the deep puddle.",
        ),
        QAItem(
            question=f"What did {lion.id} want to do at the deep puddle?",
            answer=f"{lion.id} wanted to {action.verb}, because the puddle looked shiny and fun.",
        ),
        QAItem(
            question=f"What did the flashback remind {lion.id} about?",
            answer=f"The flashback reminded {lion.id} of an earlier time when the puddle felt too wide and made {lion.id} wobble.",
        ),
        QAItem(
            question=f"Who helped {lion.id} feel steady?",
            answer=f"{helper_cfg.label} helped by giving calm advice and a gentle example.",
        ),
        QAItem(
            question=f"What transformation happened by the end?",
            answer=f"{lion.id} changed from {trans.old_state} to {trans.new_state}.",
        ),
        QAItem(
            question=f"What was the ending image?",
            answer=f"The ending showed {trans.ending_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["lion"].type, "puddle", "deep", "flashback", "transformation", "rhyming"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="deep_puddle", action="splash", transformation="brave", name="Leo", helper="duck", trait="shy"),
    StoryParams(place="deep_puddle", action="dance", transformation="muddy", name="Milo", helper="frog", trait="curious"),
    StoryParams(place="deep_puddle", action="sing", transformation="sparkling", name="Nico", helper="mouse", trait="playful"),
]


def explain_rejection(action: Action, setting: Setting) -> str:
    return f"(No story: {action.verb} does not fit the {setting.place} rules.)"


ASP_RULES = r"""
lion(hero).
place(deep_puddle).
action(splash).
action(dance).
action(sing).
transformation(brave).
transformation(muddy).
transformation(sparkling).

valid_story(P,A,T) :- place(P), action(A), transformation(T).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "deep_puddle")]
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t))
    lines.append(asp.fact("lion", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(p, a, t) for p in SETTINGS for a in ACTIONS for t in TRANSFORMATIONS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(TRANSFORMATIONS, params.transformation),
                 params.name, _safe_lookup(HELPERS, params.helper), params.trait)
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


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def resolve_params_old(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for row in stories:
            print("  ", row)
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
            header = f"### {p.name}: {p.action} / {p.transformation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "deep_puddle"
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    action = getattr(args, "action", None) or rng.choice(sorted(_safe_lookup(SETTINGS, place).affords))
    if action not in _safe_lookup(SETTINGS, place).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    transformation = getattr(args, "transformation", None) or rng.choice(list(TRANSFORMATIONS))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, transformation=transformation, name=name, helper=helper, trait=trait)


if __name__ == "__main__":
    main()
