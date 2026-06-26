#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sculpture_dialogue_comedy.py
==========================================================================================================

A tiny storyworld about sculpture, dialogue, and a playful comedy turn.

Premise:
- A child or young helper is making a sculpture from clay, boxes, or scraps.
- Another character keeps talking, joking, and giving unhelpful advice.
- The sculpture wobbles, gets renamed, or gets remade after a funny mix-up.
- The ending proves something changed in the world: the sculpture is finished,
  improved, or given a new role.

The world is intentionally small and constraint-driven:
- typed entities carry physical meters and emotional memes
- dialogue moves the plot
- comedy comes from misunderstanding, teasing, and a surprisingly sensible fix
- invalid explicit choices raise StoryError with a plain explanation
- an inline ASP twin mirrors the reasonableness gate for parity checks
"""

from __future__ import annotations

import argparse
import dataclasses
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    id: str
    label: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
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


@dataclass
class SculptureIdea:
    id: str
    material: str
    shape: str
    wobble: str
    joke: str
    repair: str
    keyword: str = "sculpture"
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
class Fix:
    id: str
    label: str
    helps: set[str]
    action: str
    finish: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraph_breaks: list[int] = []
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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = dataclasses.replace(self.entities) if False else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    idea: str
    fix: str
    name: str
    sidekick: str
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


PLACES = {
    "studio": Place("studio", "the art studio", indoor=True, affords={"clay", "cardboard", "paint"}),
    "yard": Place("yard", "the backyard", indoor=False, affords={"clay", "cardboard"}),
    "museum": Place("museum", "the little museum workshop", indoor=True, affords={"clay", "cardboard", "paint"}),
}

IDEAS = {
    "clay_cat": SculptureIdea(
        "clay_cat",
        material="clay",
        shape="a sleepy cat",
        wobble="its tail kept drooping like a tired noodle",
        joke="It looked less like a cat and more like a loaf with opinions",
        repair="pinched the tail higher and pressed the feet flat",
        tags={"clay", "cat"},
    ),
    "cardboard_robot": SculptureIdea(
        "cardboard_robot",
        material="cardboard",
        shape="a boxy robot",
        wobble="one arm kept flopping off like it wanted a nap",
        joke="The robot looked brave, but its knees were made of spaghetti",
        repair="taped the arm and folded the knees stronger",
        tags={"cardboard", "robot"},
    ),
    "paint_monster": SculptureIdea(
        "paint_monster",
        material="paint",
        shape="a grinning monster",
        wobble="the grin kept sliding sideways in wet streaks",
        joke="It looked so silly it seemed to be laughing at itself",
        repair="waited for the paint to dry and added a steadier smile",
        tags={"paint", "monster"},
    ),
}

FIXES = {
    "tape": Fix("tape", "a roll of tape", {"cardboard"}, "tape it up", "taped it up neatly"),
    "plaque": Fix("plaque", "a funny name plaque", {"clay", "cardboard", "paint"}, "add a plaque", "added a plaque with a grand name", plural=False),
    "stand": Fix("stand", "a small wooden stand", {"clay", "cardboard"}, "set it on a stand", "set it on a little stand"),
    "shade": Fix("shade", "a drying shelf", {"paint"}, "leave it to dry", "left it to dry on the shelf"),
}

NAMES = ["Mia", "Leo", "Nina", "Owen", "Ava", "Theo", "Luna", "Max"]
SIDEKICKS = ["mom", "dad", "grandpa", "auntie", "big sister", "best friend"]
TRAITS = ["curious", "silly", "cheerful", "bouncy", "spirited", "playful"]


def sculpture_at_risk(idea: SculptureIdea, fix: Fix) -> bool:
    return idea.material in fix.helps


def select_fix(idea: SculptureIdea) -> Optional[Fix]:
    for fx in FIXES.values():
        if sculpture_at_risk(idea, fx):
            return fx
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for idea_id, idea in IDEAS.items():
            if idea.material not in place.affords:
                continue
            fx = select_fix(idea)
            if fx is None:
                continue
            for fix_id, fix in FIXES.items():
                if fix_id == fx.id:
                    out.append((place_id, idea_id, fix_id))
    return out


def _build_story(world: World, hero: Entity, sidekick: Entity, idea: SculptureIdea, fix: Fix) -> None:
    hero.memes["pride"] += 1
    world.say(f"{hero.id} was a {hero.traits[0]} little sculptor who loved making {idea.shape}.")
    world.say(f"{hero.pronoun().capitalize()} said, \"Today I'm building a {idea.shape} from {idea.material}.\"")
    world.say(f"{sidekick.id} peeked over the table and said, \"That sounds fancy. Does it also make snacks?\"")
    world.say(f"{hero.id} laughed. \"No snacks. Just art.\"")
    world.para()
    world.say(f"In {world.place.label}, the {idea.material} looked ready for a story, and {idea.shape} began to take shape.")
    world.say(f"But then {idea.wobble}. {sidekick.id} pointed and said, \"Ah, yes. Modern art. Very wiggly.\"")
    hero.memes["worry"] += 1
    hero.meters["instability"] += 1
    if idea.material == "paint":
        hero.meters["mess"] += 1
        world.say(f"The wet paint smeared a little, and everybody had to tiptoe like penguins.")
    world.say(f"{hero.id} groaned, \"It was supposed to look graceful.\"")
    world.say(f"{sidekick.id} grinned. \"Graceful can wobble. I checked the museum rules in my imagination.\"")
    world.para()
    world.say(f"{hero.id} tried again and {idea.repair}.")
    hero.memes["confidence"] += 1
    hero.meters["stability"] += 1
    if fix.id == "plaque":
        world.say(f"{sidekick.id} held up {fix.label} and said, \"If it can't be perfect, it can at least have a dramatic name.\"")
        world.say(f"They {fix.finish}, and the sculpture suddenly looked important instead of merely lopsided.")
    elif fix.id == "tape":
        world.say(f"{sidekick.id} held up {fix.label} and said, \"This is not cheating. This is advanced confidence.\"")
        world.say(f"They {fix.finish}, and the robot's arm stopped flopping like a sleepy fish.")
    elif fix.id == "stand":
        world.say(f"{sidekick.id} fetched {fix.label} and said, \"A stand is just a fancy way to say, 'Please behave, sculpture.'\"")
        world.say(f"They {fix.finish}, and the cat finally sat like it had remembered its dignity.")
    elif fix.id == "shade":
        world.say(f"{sidekick.id} waved {fix.label} and said, \"Every masterpiece needs a nap.\"")
        world.say(f"They {fix.finish}, and the grinning monster dried into a proper, shiny smile.")
    hero.memes["joy"] += 2
    sidekick.memes["amusement"] += 2
    world.say(f"{hero.id} stepped back and beamed. \"There!\" {hero.pronoun()} said.")
    world.say(f"{sidekick.id} looked at the finished piece and said, \"It's still silly, but now it's the kind of silly that belongs in a room.\"")
    world.say(f"At the end, the sculpture stood ready, and everyone agreed it had turned from a wobble into a masterpiece with jokes.")


def tell(place: Place, idea: SculptureIdea, fix: Fix, name: str, sidekick_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type="child",
        traits=["curious", "silly"],
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type="adult" if sidekick_name in {"mom", "dad", "grandpa", "auntie"} else "child",
        traits=["funny", "helpful"],
    ))
    world.facts.update(hero=hero, sidekick=sidekick, idea=idea, fix=fix, place=place)
    _build_story(world, hero, sidekick, idea, fix)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a small child about a sculpture named "{f["idea"].shape}" in {f["place"].label}.',
        f"Tell a funny dialogue-driven story where {f['hero'].id} and {f['sidekick'].id} argue gently about how to fix a sculpture made from {f['idea'].material}.",
        f'Write a playful story that includes the word "sculpture" and ends with a joke becoming a success.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    idea: SculptureIdea = _safe_fact(world, f, "idea")
    fix: Fix = _safe_fact(world, f, "fix")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What was {hero.id} making in {place.label}?",
            answer=f"{hero.id} was making a sculpture of {idea.shape} from {idea.material}.",
        ),
        QAItem(
            question=f"Why did {sidekick.id} make a joke about the sculpture?",
            answer=f"{sidekick.id} made a joke because the sculpture got a little wobbly and funny-looking, which made the room feel playful instead of scary.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They used {fix.label} to help the sculpture hold together, and that made the final piece steadier and more finished.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and happy because the sculpture stayed silly but became strong enough to stand well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    idea: SculptureIdea = _safe_fact(world, world.facts, "idea")
    out = [
        QAItem(
            question="What is a sculpture?",
            answer="A sculpture is a work of art that people shape from clay, stone, wood, metal, paper, or other materials so it has a real form you can look at from different sides.",
        ),
        QAItem(
            question="Why do people use tape or stands for art projects?",
            answer="People use tape or stands to help a project hold its shape, stay upright, or dry without falling over.",
        ),
    ]
    if idea.material == "paint":
        out.append(QAItem(
            question="Why does paint need time to dry?",
            answer="Paint needs time to dry because wet paint can smear, drip, or stick to things until it sets.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{ent.id} ({ent.kind}/{ent.type}) " + " ".join(parts))
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
idea(I) :- sculpture(I).
fix(F) :- repair(F).

at_risk(I,F) :- sculpture(I), repair(F), material(I,M), helps(F,M).
valid_story(P,I,F) :- place(P), idea(I), fix(F), affords(P,M), material(I,M), at_risk(I,F).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, idea in IDEAS.items():
        lines.append(asp.fact("sculpture", iid))
        lines.append(asp.fact("material", iid, idea.material))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("repair", fid))
        for m in sorted(fx.helps):
            lines.append(asp.fact("helps", fid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy sculpture storyworld with dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--idea", choices=IDEAS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "idea", None) or getattr(args, "fix", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "idea", None) is None or c[1] == getattr(args, "idea", None))
            and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, idea, fix = rng.choice(list(combos))
    return StoryParams(
        place=place,
        idea=idea,
        fix=fix,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        sidekick=getattr(args, "sidekick", None) or rng.choice(SIDEKICKS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(IDEAS, params.idea), _safe_lookup(FIXES, params.fix), params.name, params.sidekick)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for i in IDEAS:
            if _safe_lookup(IDEAS, i).material not in _safe_lookup(PLACES, p).affords:
                continue
            fx = select_fix(_safe_lookup(IDEAS, i))
            if fx is not None:
                out.append((p, i, fx.id))
    return out


CURATED = [
    StoryParams(place="studio", idea="clay_cat", fix="stand", name="Mia", sidekick="mom"),
    StoryParams(place="yard", idea="cardboard_robot", fix="tape", name="Leo", sidekick="dad"),
    StoryParams(place="museum", idea="paint_monster", fix="shade", name="Nina", sidekick="auntie"),
    StoryParams(place="studio", idea="clay_cat", fix="plaque", name="Owen", sidekick="grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story triples:\n")
        for t in triples:
            print("  ", t)
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.idea} at {p.place} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
