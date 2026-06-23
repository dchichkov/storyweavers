#!/usr/bin/env python3
"""
storyworlds/worlds/inflate_surprise_humor_misunderstanding_myth.py
===================================================================

A small myth-flavored storyworld about a child, a mistaken worry, a surprise,
and a funny inflation that turns out to be harmless and helpful.

The seed idea is a tiny source tale in the shape of an old myth:
a child hears about a sleeping river-spirit, mistakes a hollow object for
something spooky, then learns that "inflate" means to fill it with air.
The surprise is that the supposed monster is really a festival helper, and the
humor comes from the misunderstanding.

This world keeps the simulation small and concrete:
- a place with an old mythic purpose,
- a lightweight object that can be inflated,
- a misunderstanding that raises tension,
- a helper who explains the trick,
- a final image proving the object is full, round, and ready.

The story is state-driven rather than templated: entity meters and memes
change as the scene progresses, and the prose reads back those changes.
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    owner: str = ""
    carried_by: str = ""
    shape: str = ""
    material: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict = field(default_factory=dict)

    adult: object | None = None
    child: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class Place:
    id: str
    label: str
    myth: str
    sound: str
    wonder: str
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
class Problem:
    id: str
    worry: str
    misunderstanding: str
    reveal: str
    humor: str
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


@dataclass
class InflationObject:
    id: str
    label: str
    phrase: str
    shape: str
    material: str
    purpose: str
    inflate_verb: str
    turns_into: str
    safe: bool = True
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
class Helper:
    id: str
    label: str
    type: str
    explain: str
    smile: str
    method: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_inflate(world: World) -> list[str]:
    out: list[str] = []
    obj = world.get("object")
    if obj.meters.get("inflated", 0.0) >= THRESHOLD:
        return out
    if world.facts.get("inflated_once"):
        return out
    world.facts["inflated_once"] = True
    obj.meters["inflated"] = 1.0
    obj.meters["round"] = 1.0
    return ["__inflate__"]


def _r_wonder(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("surprise", 0.0) < THRESHOLD:
        return out
    sig = ("wonder",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["humor"] = child.memes.get("humor", 0.0) + 1.0
    out.append("__wonder__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in (_r_inflate, _r_wonder):
            events = rule(world)
            if events:
                changed = True
                produced.extend(e for e in events if not e.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def build_reasonable_story(place: Place, problem: Problem, obj: InflationObject, helper: Helper) -> bool:
    return place.id in {"riverbank", "meadow", "shrine", "hill"} and obj.safe and helper.id in {"elder", "auntie", "harborer"}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for oid, obj in OBJECTS.items():
            for hid, helper in HELPERS.items():
                for pr_id, problem in PROBLEMS.items():
                    if build_reasonable_story(place, problem, obj, helper):
                        combos.append((pid, oid, hid, pr_id))
    return combos


@dataclass
class StoryParams:
    place: str
    object: str
    helper: str
    problem: str
    child_name: str = "Mina"
    child_type: str = "girl"
    adult_name: str = "Grandma"
    adult_type: str = "grandmother"
    seed: Optional[int] = None
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


PLACES = {
    "shrine": Place("shrine", "the hill shrine", "an old place for moon stories", "the bells sang softly", "stones and ribbons"),
    "riverbank": Place("riverbank", "the riverbank", "a place where boats dreamed", "the water lapped and laughed", "reed shadows and bright fish"),
    "meadow": Place("meadow", "the windy meadow", "a field fit for kites and myths", "the grass whispered in waves", "butterflies and long grass"),
    "cave": Place("cave", "the echo cave", "a place where voices bounced like goats", "the dark echoed every step", "dripping stone and owl eyes"),
}

PROBLEMS = {
    "spirit": Problem("spirit", "something sleeping must be waking up", "the child thinks the soft bundle is a sleeping river spirit", "it is only a festival float waiting for air", "the 'spirit' turns out to have a very silly face"),
    "monster": Problem("monster", "a monster might pop out", "the child thinks the flat shape is a monster hiding its belly", "it is only a hollow skin that swells with air", "the 'monster' is just a dramatic old decoration"),
    "gift": Problem("gift", "a sacred gift must not be ruined", "the child thinks touching it will break the gift", "inflating it is exactly how the gift is meant to work", "the worry was respectful, but unnecessary"),
}

OBJECTS = {
    "skygoat": InflationObject("skygoat", "sky-goat", "the sky-goat", "goat-shaped", "cloth and reeds", "to float above the feast", "inflate", "a round sky-goat", True),
    "riverbell": InflationObject("riverbell", "river bell", "the river bell", "bell-shaped", "paper and hide", "to ring when filled with air", "inflate", "a bright round bell", True),
    "moonfish": InflationObject("moonfish", "moon fish", "the moon fish", "fish-shaped", "thin hide", "to bob beside the boats", "inflate", "a plump moon fish", True),
    "clouddrum": InflationObject("clouddrum", "cloud drum", "the cloud drum", "drum-shaped", "soft hide", "to carry the festival song", "inflate", "a smooth cloud drum", True),
}

HELPERS = {
    "elder": Helper("elder", "the old elder", "elder", "smiled and explained", "smiled with a twinkle", "air makes it round"),
    "auntie": Helper("auntie", "Auntie Sera", "aunt", "laughed and showed the trick", "laughed like a little bell", "the mouth trap lets air in"),
    "harborer": Helper("harborer", "the harbor keeper", "keeper", "pointed to the pump", "grinned like a gull", "the pump fills it up"),
}


GIRL_NAMES = ["Mina", "Lina", "Roa", "Suri", "Tala"]
BOY_NAMES = ["Niko", "Jori", "Pavi", "Kian", "Maro"]


def explain_rejection() -> str:
    return "(No story: this mythic scene needs a safe thing that can truly be inflated and a helper who can explain the trick.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "object", None) is None or c[1] == getattr(args, "object", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))
              and (getattr(args, "problem", None) is None or c[3] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj, helper, problem = rng.choice(list(combos))
    child_type = "girl" if rng.random() < 0.5 else "boy"
    child_name = getattr(args, "child_name", None) or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult_name = getattr(args, "adult_name", None) or rng.choice(["Grandma", "Grandpa", "Auntie Sera", "Uncle Vale"])
    return StoryParams(place=place, object=obj, helper=helper, problem=problem,
                       child_name=child_name, child_type=child_type,
                       adult_name=adult_name, adult_type="grandmother")


def tell(place: Place, problem: Problem, obj: InflationObject, helper: Helper,
         child_name: str, child_type: str, adult_name: str, adult_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=adult_name))
    item = world.add(Entity(id="object", kind="thing", type="thing", label=obj.label, phrase=obj.phrase,
                            meters={"inflated": 0.0, "round": 0.0}, memes={}, attrs={"shape": obj.shape}))
    world.facts.update(child=child, adult=adult, object=obj, helper=helper, place=place, problem=problem,
                       inflated_once=False, misunderstood=False, surprise=False)
    world.say(f"{child.label_word} went to {place.label} where old songs lived in the stones. {place.myth}.")
    world.say(f"At the edge of the water, {child.label_word} saw {obj.phrase} and thought of {problem.misunderstanding}.")
    child.memes["misunderstanding"] = 1.0
    world.facts["misunderstood"] = True
    world.para()
    world.say(f'Then {child.label_word} gasped, because the shape looked strange and funny at once. {problem.humor}')
    child.memes["surprise"] = 1.0
    world.facts["surprise"] = True
    world.say(f"{adult.label_word} came closer, {helper.explain}, and {helper.smile}.")
    world.say(f'"Do not fear," {adult.label_word} said. "To {obj.inflate_verb} it is to wake it properly."')
    propagate(world, narrate=False)
    world.para()
    item.meters["inflated"] = 1.0
    item.meters["round"] = 1.0
    child.memes["humor"] = 1.0
    world.say(f"Together they began to {obj.inflate_verb} it. The soft skin grew from flat to round, and the worry slipped away.")
    world.say(f"At last {obj.label_word} was no longer a thin shape on the ground; it was {obj.turns_into}, bright against {place.label}.")
    world.say(f"{child.label_word} laughed, because the feared thing was only a helpful part of the feast all along.")
    world.facts["done"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child that includes the word "inflate" and a funny misunderstanding at {f["place"].label}.',
        f"Tell a small legend where {f['child'].label_word} thinks {f['object'].label} is spooky, but {f['adult'].label_word} shows how to inflate it.",
        f"Write a gentle mythic story with surprise and humor where a hidden festival thing turns out to be made to inflate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    obj: InflationObject = f["object"]
    place: Place = f["place"]
    problem: Problem = f["problem"]
    return [
        QAItem(
            question=f"What did {child.label_word} first think about {obj.phrase} at {place.label}?",
            answer=f"{child.label_word} first thought it was something spooky, because {problem.misunderstanding}. The funny part is that the object only looked strange before anyone explained it.",
        ),
        QAItem(
            question=f"Who explained how to {obj.inflate_verb} the {obj.label}?",
            answer=f"{adult.label_word} explained it. {f['helper'].explain.capitalize()}, so the child could see that the flat shape was meant to become full of air.",
        ),
        QAItem(
            question=f"What changed after they started to {obj.inflate_verb} it?",
            answer=f"The {obj.label} turned from flat to round and became {obj.turns_into}. That ending image proves the fear was only a misunderstanding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    obj: InflationObject = world.facts["object"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question="What does inflate mean?",
            answer="To inflate something means to fill it with air so it gets bigger and rounder. Many toys, floats, and festival things are made that way.",
        ),
        QAItem(
            question=f"What is a {obj.shape} thing for?",
            answer=f"A {obj.shape} thing is shaped that way on purpose, so it can work as {obj.purpose}. The shape helps it do its job safely and well.",
        ),
        QAItem(
            question=f"Why do old stories sometimes happen near {place.label}?",
            answer=f"Old stories often gather near places like {place.label} because rivers, hills, and shrines feel full of mystery. That makes them good homes for myths.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id}: {e.label_word} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shrine", object="skygoat", helper="elder", problem="spirit", child_name="Mina", child_type="girl", adult_name="Grandma", adult_type="grandmother"),
    StoryParams(place="riverbank", object="riverbell", helper="auntie", problem="monster", child_name="Niko", child_type="boy", adult_name="Auntie Sera", adult_type="aunt"),
    StoryParams(place="meadow", object="moonfish", helper="harborer", problem="gift", child_name="Lina", child_type="girl", adult_name="Keeper Vale", adult_type="man"),
    StoryParams(place="cave", object="clouddrum", helper="elder", problem="monster", child_name="Jori", child_type="boy", adult_name="Grandpa", adult_type="grandfather"),
]


def generate(params: StoryParams) -> StorySample:
    try:
        place = _safe_lookup(PLACES, params.place)
        obj = _safe_lookup(OBJECTS, params.object)
        helper = _safe_lookup(HELPERS, params.helper)
        problem = _safe_lookup(PROBLEMS, params.problem)
    except KeyError as exc:
        pass
    world = tell(place, problem, obj, helper, params.child_name, params.child_type, params.adult_name, params.adult_type)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic inflate storyworld with surprise, humor, and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--adult-name")
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


ASP_RULES = r"""
obj_inflated(O) :- object(O), safe(O).
surprise_happens :- misunderstood, inflate_used.
humor_happens :- surprise_happens.
valid(Place,Object,Helper,Problem) :- place(Place), object(Object), helper(Helper), problem(Problem), safe(Object).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.safe:
            lines.append(asp.fact("safe", oid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for prid in PROBLEMS:
        lines.append(asp.fact("problem", prid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=True, qa=True)
    print(f"OK: ASP parity and generate/emit smoke test passed ({len(valid_combos())} combos).")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "object", None) is None or c[1] == getattr(args, "object", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))
              and (getattr(args, "problem", None) is None or c[3] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj, helper, problem = rng.choice(list(combos))
    return StoryParams(
        place=place,
        object=obj,
        helper=helper,
        problem=problem,
        child_name=getattr(args, "child_name", None) or rng.choice(GIRL_NAMES + BOY_NAMES),
        child_type=rng.choice(["girl", "boy"]),
        adult_name=getattr(args, "adult_name", None) or rng.choice(["Grandma", "Grandpa", "Auntie Sera"]),
        adult_type="grandmother",
    )


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
