#!/usr/bin/env python3
"""
storyworlds/worlds/pap_suspense_sharing_tall_tale.py
=====================================================

A tiny tall-tale storyworld about pap, suspense, and sharing.

Seed tale sketch:
---
One night, a big wind came rolling over the hills like a black blanket.
Mina and her pap were in their little house by the river. Pap had baked one giant loaf of sweet cornbread,
and the smell made Mina's tummy growl loud enough to wake the stove.

Then the wind knocked the porch light to blinking, and somebody thumped at the front door.
Pap held up one finger and whispered that the knock might be a lost neighbor, or a raccoon
with manners no one had ever seen. Mina was scared, but she stayed close while pap opened the door.
At the door stood a tiny, shivering boy carrying an empty basket.

Pap did not keep the loaf to themselves. He cut it in thick, warm slices and shared it with the boy,
and then the three of them ate by lantern light while the wind whooped outside.

World model:
---
    need more than one hungry body + one loaf -> suspense about whether to share
    polite knocking at night + storm + dim light -> tension meter rises
    sharing loaf or slices -> hunger falls, trust rises, suspense resolves
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    loaf: object | None = None
    pap: object | None = None
    visitor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man", "pap"}:
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
    label: str = "the little house by the river"
    stormy: bool = True
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
class Feast:
    label: str
    phrase: str
    slices: int
    sweet: bool = True
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
class Visitor:
    id: str
    label: str
    hungry: bool = True
    shy: bool = True
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
class StoryParams:
    place: str
    feast: str
    visitor: str
    name: str
    seed: Optional[int] = None
    cur: list = field(default_factory=list)
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _tension(world: World) -> list[str]:
    out: list[str] = []
    feast = world.get("feast")
    visitor = world.get("visitor")
    pap = world.get("pap")
    if feast.meters.get("pieces", 0) >= THRESHOLD and visitor.meters.get("present", 0) >= THRESHOLD:
        if ("tension",) not in world.fired:
            world.fired.add(("tension",))
            pap.memes["worry"] = pap.memes.get("worry", 0) + 1
            visitor.memes["hope"] = visitor.memes.get("hope", 0) + 1
            out.append("The room went quiet as the big loaf waited on the board.")
    return out


def _share(world: World) -> list[str]:
    out: list[str] = []
    feast = world.get("feast")
    pap = world.get("pap")
    visitor = world.get("visitor")
    if feast.meters.get("pieces", 0) <= 0:
        return out
    if feast.meters.get("shared", 0) >= THRESHOLD:
        return out
    if pap.memes.get("compassion", 0) >= THRESHOLD and visitor.meters.get("present", 0) >= THRESHOLD:
        world.fired.add(("share",))
        feast.meters["shared"] = 1
        feast.meters["pieces"] = max(0, feast.meters.get("pieces", 0) - 1)
        visitor.meters["fed"] = 1
        pap.memes["warmth"] = pap.memes.get("warmth", 0) + 1
        visitor.memes["trust"] = visitor.memes.get("trust", 0) + 1
        out.append("Pap sliced the cornbread wide open and shared it without a speck of fuss.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_tension, _share):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_story(place: Place, feast: Feast, visitor_name: str, hero_name: str) -> World:
    world = World(place)
    pap = world.add(Entity(id="pap", kind="character", type="pap", label="Pap"))
    child = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    visitor = world.add(Entity(id="visitor", kind="character", type="boy", label=visitor_name))
    loaf = world.add(Entity(
        id="feast",
        kind="thing",
        type="loaf",
        label=feast.label,
        phrase=feast.phrase,
    ))
    loaf.meters["pieces"] = float(feast.slices)
    child.meters["present"] = 1
    visitor.meters["present"] = 1
    pap.meters["present"] = 1
    pap.memes["compassion"] = 1
    visitor.meters["hungry"] = 1
    child.memes["curiosity"] = 1

    world.say(f"{hero_name} lived with pap in {place.label}, where the wind could sing through the cracks.")
    world.say(f"Pap had baked {feast.phrase}, and the smell curled around the room like a happy fox.")
    world.para()
    if place.stormy:
        world.say("That night the wind came a-whistling, and the porch light blinked like a sleepy star.")
    world.say(f"Then came a knock so small and careful that even the teacups seemed to listen.")
    world.say(f"{hero_name} clung close to pap, because in a tall storm a tiny knock can feel bigger than a drum.")
    world.say("Pap opened the door and found a shivering visitor with an empty basket and a polite little bow.")
    visitor.meters["present"] = 1
    propagate(world, narrate=True)
    world.para()
    world.say("Pap looked at the loaf, then at the visitor, and then at the child by his elbow.")
    world.say("He did not count the slices like a miser with a cold heart.")
    propagate(world, narrate=True)
    if feast.slices > 0:
        world.say(f"He cut the {feast.label} into warm pieces, one for each hungry belly.")
        world.say(f"{hero_name} and the visitor ate by lantern light while the wind hollered outside the door.")
        pap.memes["joy"] = pap.memes.get("joy", 0) + 1
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        visitor.memes["joy"] = visitor.memes.get("joy", 0) + 1
    world.facts.update(pap=pap, child=child, visitor=visitor, feast=loaf, place=place)
    return world


PACES = {
    "house": Place(label="the little house by the river", stormy=True),
    "cabin": Place(label="the crooked cabin on the hill", stormy=True),
}

FEASTS = {
    "cornbread": Feast(label="cornbread", phrase="one giant loaf of sweet cornbread", slices=4),
    "applepie": Feast(label="apple pie", phrase="one round apple pie with a crust like a golden roof", slices=6),
}

VISITORS = {
    "boy": Visitor(id="visitor", label="a shivering boy"),
    "girl": Visitor(id="visitor", label="a shivering girl"),
}

NAMES = ["Mina", "Lulu", "Tess", "June", "Nell", "Rosa", "Ada", "Mabel"]
VISITOR_NAMES = ["Joey", "Benny", "Otis", "Wes", "Pip", "Eli", "Noel", "Toby"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, f, v) for p in PACES for f in FEASTS for v in VISITORS]


@dataclass
class Reasonable:
    place: str
    feast: str
    visitor: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about pap, suspense, and sharing.")
    ap.add_argument("--place", choices=PACES)
    ap.add_argument("--feast", choices=FEASTS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "feast", None):
        combos = [c for c in combos if c[1] == getattr(args, "feast", None)]
    if getattr(args, "visitor", None):
        combos = [c for c in combos if c[2] == getattr(args, "visitor", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, feast, visitor = (list(rng.choice(combos)) + [None, None, None])[:3]
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, feast=feast, visitor=visitor, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale for a child named {f["child"].id} about pap, a storm, and sharing {f["feast"].label}.',
        f"Tell a suspenseful but gentle story where pap hears a knock in {f['place'].label} and decides to share.",
        f'Write a child-friendly tall tale that includes a hungry visitor, a giant loaf, and the word "pap".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pap = _safe_fact(world, f, "pap")
    child = _safe_fact(world, f, "child")
    visitor = _safe_fact(world, f, "visitor")
    feast = _safe_fact(world, f, "feast")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who lived with pap in {place.label}?",
            answer=f"{child.id} lived with pap in {place.label}.",
        ),
        QAItem(
            question=f"What did pap have on the board before the knock?",
            answer=f"Pap had {feast.phrase} on the board.",
        ),
        QAItem(
            question=f"Who came to the door during the storm?",
            answer=f"{visitor.label.capitalize()} came to the door with an empty basket.",
        ),
        QAItem(
            question=f"What did pap do when he saw the visitor?",
            answer="Pap shared the loaf instead of keeping it all for himself.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storm?",
            answer="A storm is rough weather with strong wind, rain, thunder, or all three together.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have to someone else so more than one person can enjoy it.",
        ),
        QAItem(
            question="Why can a knock at night feel scary?",
            answer="A knock at night can feel scary because it comes when things are dark and quiet, so you do not know who is there yet.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = setup_story(_safe_lookup(PACES, params.place), _safe_lookup(FEASTS, params.feast), _safe_lookup(VISITORS, params.visitor).label, params.name)
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


ASP_RULES = r"""
% A loaf is share-worthy if more than one hungry body is present.
share_needed(P, F, V) :- place(P), feast(F), visitor(V).

% Suspense: a storm, a knock, and a loaf create a tense moment.
tense(P) :- stormy(P).

% Sharing resolves the tension.
resolved(P, F, V) :- share_needed(P, F, V), tense(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PACES.items():
        lines.append(asp.fact("place", pid))
        if p.stormy:
            lines.append(asp.fact("stormy", pid))
    for fid, f in FEASTS.items():
        lines.append(asp.fact("feast", fid))
        lines.append(asp.fact("serves", fid, f.slices))
    for vid in VISITORS:
        lines.append(asp.fact("visitor", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show resolved/3."))
    atoms = set(asp.atoms(model, "resolved"))
    py = {(p, f, v) for p, f, v in valid_combos()}
    if atoms == py:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP only:", sorted(atoms - py))
    print("Python only:", sorted(py - atoms))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/3."))
        vals = sorted(set(asp.atoms(model, "resolved")))
        for item in vals:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        cur = [StoryParams(place=p, feast=f, visitor=v, name=random.choice(NAMES)) for p, f, v in valid_combos()]
        samples = [generate(p) for p in cur]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
