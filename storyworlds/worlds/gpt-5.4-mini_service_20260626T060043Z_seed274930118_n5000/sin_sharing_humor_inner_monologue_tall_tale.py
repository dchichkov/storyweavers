#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about a boastful mistake, a little shared burden,
and a humorous turn that softens the sin.

Premise:
- A character does a sinful, selfish act in a big, windy frontier setting.
- The act creates a shared mess or shared trouble.
- The character's inner monologue shows pride, worry, and then remorse.
- Humor and sharing lead to a repair that leaves everyone lighter.

This script models:
- physical meters: dust, hunger, embarrassment, relief, distance
- emotional memes: pride, guilt, worry, laughter, generosity, apology

The story stays child-facing and tall-tale flavored: oversized comparisons,
big skies, comical exaggeration, and a moral ending image.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    actor: object | None = None
    friend: object | None = None
    def __post_init__(self):
        for k in ["dust", "hunger", "embarrassment", "relief", "distance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "guilt", "worry", "laughter", "generosity", "apology"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cowgirl"}
        male = {"boy", "father", "dad", "man", "cowboy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the prairie"
    sky: str = "wide"
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
class SinAct:
    id: str
    verb: str
    gerund: str
    rush: str
    stain: str
    trouble: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class SharedThing:
    label: str
    phrase: str
    type: str
    kind: str
    plural: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for giver in world.characters():
        if giver.memes["generosity"] < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != giver.id:
                continue
            for other in world.characters():
                if other.id == giver.id:
                    continue
                sig = ("share", item.id, other.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.shared_with.add(other.id)
                giver.memes["relief"] += 1
                other.memes["relief"] += 1
                out.append(f"{giver.id} shared {item.label} with {other.id}.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["laughter"] < THRESHOLD:
            continue
        sig = ("laugh", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["embarrassment"] = max(0.0, actor.meters["embarrassment"] - 1)
        out.append(f"{actor.id} laughed so hard the dust seemed to bounce.")
    return out


def _r_guilt(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dust"] < THRESHOLD:
            continue
        if actor.memes["guilt"] >= THRESHOLD:
            continue
        sig = ("guilt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["guilt"] += 1
        actor.meters["embarrassment"] += 1
        out.append(f"{actor.id} felt a hot prick of shame under the big sky.")
    return out


CAUSAL_RULES = [_r_guilt, _r_share, _r_laugh]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell_plain(world: World, actor: Entity, friend: Entity, thing: SharedThing, act: SinAct) -> None:
    world.say(
        f"Out on the prairie where the grass waved like a green sea, {actor.id} was a "
        f"little {actor.type} with a great big grin and an even bigger opinion of {actor.pronoun('possessive')} own cleverness."
    )
    world.say(
        f"{actor.id} had a bad habit: {actor.pronoun().capitalize()} liked to {act.verb} and call it a joke."
    )
    world.say(
        f"That morning {actor.id} found {thing.phrase} sitting where it should not have been, and the thought of it made {actor.pronoun('possessive')} boots itch with mischief."
    )
    world.para()
    world.say(
        f"{actor.id} thought, “If I take it, nobody will know.” But the prairie has a long memory and a louder echo than a trumpet on a wagon roof."
    )
    actor.memes["pride"] += 1
    actor.meters["distance"] += 1
    actor.meters["dust"] += 1
    actor.memes["worry"] += 1
    world.say(
        f"So {actor.id} did the sinful thing and {act.rush}, while the wind carried off the last brave excuse."
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"Then {friend.id} came along, squinting at the trouble as if it were a tiny cloud over a giant sunset."
    )
    friend.memes["worry"] += 1
    world.say(
        f'"Well now," {friend.id} said, "that is a fine-sized mess for one pair of boots."'
    )
    world.say(
        f"{actor.id} wanted to laugh it off, but inside {actor.pronoun('possessive')} own head a small voice muttered, "
        f'"That was not brave. That was just mean."'
    )
    actor.memes["guilt"] += 1
    actor.memes["apology"] += 1
    world.say(
        f"{actor.id} swallowed hard and said sorry so plainly it sounded like a barn door finally latched in a storm."
    )
    world.say(
        f"Then {actor.id} shared {thing.label} back with {friend.id}, and the two of them split the work of fixing the trouble."
    )
    actor.memes["generosity"] += 1
    friend.memes["generosity"] += 1
    friend.memes["laughter"] += 1
    actor.memes["laughter"] += 1
    propagate(world, narrate=True)
    world.say(
        f"By sundown the prairie was wide and bright again, and {actor.id} had learned that a joke that hurts is not a joke at all."
    )
    world.say(
        f"But a joke shared kindly, with apology and help, can turn a sinful hour into a story folks tell with a smile."
    )


SETTINGS = {
    "prairie": Setting(place="the prairie", sky="wide", affords={"theft"}),
    "town": Setting(place="the little town", sky="busy", affords={"theft"}),
    "barnyard": Setting(place="the barnyard", sky="windy", affords={"theft"}),
}

ACTIVITIES = {
    "theft": SinAct(
        id="theft",
        verb="snatch something that did not belong to {self}",
        gerund="snatching things that were not his to take",
        rush="ran off with the prize",
        stain="dusty and guilty",
        trouble="trouble for everyone nearby",
        keyword="sin",
        tags={"sin", "sharing", "humor"},
    )
}

SHARED_THINGS = {
    "pie": SharedThing(label="pie", phrase="a pie cooling on a windowsill", type="pie", kind="food"),
    "rope": SharedThing(label="rope", phrase="a coiled rope by the hitching post", type="rope", kind="tool"),
    "jam": SharedThing(label="jam", phrase="a jar of berry jam on the porch", type="jam", kind="food"),
}

NAMES = ["Hank", "Milo", "Josie", "Etta", "Bram", "Nell"]
FRIEND_NAMES = ["Pip", "June", "Otis", "Lulu"]
TRAITS = ["brash", "curious", "spunky", "hasty"]


@dataclass
class StoryParams:
    place: str
    act: str
    thing: str
    name: str
    friend: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story about sin, sharing, and humor set at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")}.',
        f"Tell a story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "name")} makes a selfish choice, hears an inner monologue, then shares and makes it right.",
        f"Write a child-facing tall tale that includes a funny mistake, a sorry, and a shared fix with {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "thing_label")}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    actor: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "actor")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    thing: SharedThing = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "thing")
    return [
        QAItem(
            question=f"What sinful thing did {actor.id} do?",
            answer=f"{actor.id} {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "act").verb.replace('{self}', actor.id)} and took {thing.phrase} even though it was not {actor.pronoun('possessive')} to take.",
        ),
        QAItem(
            question=f"What did {actor.id} think in {actor.pronoun('possessive')} own head before the trouble got bigger?",
            answer=f"{actor.id} thought, \"If I take it, nobody will know.\" But then {actor.id} realized that was just a sneaky excuse.",
        ),
        QAItem(
            question=f"How did {actor.id} and {friend.id} fix the mistake?",
            answer=f"{actor.id} said sorry, shared {thing.label} back, and {actor.id} and {friend.id} split the work of fixing the trouble together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sin?",
            answer="A sin is a bad choice that hurts trust, fairness, or kindness.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use, enjoy, or have part of something with you.",
        ),
        QAItem(
            question="Why can humor help after a mistake?",
            answer="Humor can help people relax and talk kindly, as long as it does not hide the harm that needs fixing.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private talking a person does inside their own head.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for tid, t in SHARED_THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("thing_kind", tid, t.kind))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when the setting affords the sinful act.
valid_story(S, A, T) :- affords(S, A), activity(A), thing(T).

% The thematic trio is present when the act touches sin, sharing, and humor.
thematic(A) :- tag(A, sin), tag(A, sharing), tag(A, humor).

#show valid_story/3.
#show thematic/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return sorted((s, a, t) for s in SETTINGS for a in ACTIVITIES for t in SHARED_THINGS)


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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about sin, sharing, humor, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--thing", choices=SHARED_THINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
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
    act = getattr(args, "activity", None) or "theft"
    thing = getattr(args, "thing", None) or rng.choice(list(SHARED_THINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if act not in ACTIVITIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if thing not in SHARED_THINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, act=act, thing=thing, name=name, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    actor = world.add(Entity(id=params.name, kind="character", type="boy", traits=["little", params.trait]))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl", traits=["sharp-eyed", "kind"]))
    thing = _safe_lookup(SHARED_THINGS, params.thing)
    act = _safe_lookup(ACTIVITIES, params.act)

    world.facts.update(place=params.place, thing_label=thing.label, actor=actor, friend=friend, thing=thing, act=act)

    tell_plain(world, actor, friend, thing, act)

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
    StoryParams(place="prairie", act="theft", thing="pie", name="Hank", friend="Pip", trait="brash"),
    StoryParams(place="town", act="theft", thing="jam", name="Josie", friend="June", trait="hasty"),
    StoryParams(place="barnyard", act="theft", thing="rope", name="Bram", friend="Otis", trait="curious"),
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
        print(f"{len(triples)} compatible combos:\n")
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
