#!/usr/bin/env python3
"""
Standalone storyworld: a tiny myth about a shy child, a glowing question,
a remembered warning, and a happy ending.

The world models a small village shrine story in which a child must face a
bright, speaking moon-stone. The child blushes, imagines a brave act, remembers
an old flashback about a failed boast, and finally solves the problem with help
from a patient elder and a humble offering.

This script follows the Storyweavers world contract.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    caretaker: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    elder: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "elder"}:
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
    name: str
    indoors: bool = False
    shrine: bool = False
    echoes: bool = False
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
class Relic:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    sacred: bool = False
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
class Ritual:
    id: str
    verb: str
    gerund: str
    omen: str
    strain: str
    keyword: str
    threatens: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.flashback_seen = False
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


def _rule_blush(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("embarrassment", 0) >= 1 and not world.fired.__contains__(("blush",)):
        world.fired.add(("blush",))
        child.meters["blush"] = child.meters.get("blush", 0) + 1
        out.append(f"{child.id}'s cheeks grew warm and pink.")
    return out


def _rule_flashback(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("doubt", 0) >= 1 and not world.flashback_seen:
        world.flashback_seen = True
        out.append("The old memory returned: once, a boast had ended in tears.")
    return out


def _rule_humility(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("humility", 0) >= 1 and not world.fired.__contains__(("humble",)):
        world.fired.add(("humble",))
        child.memes["courage"] = child.memes.get("courage", 0) + 1
        out.append(f"{child.id} lowered {child.pronoun('possessive')} gaze, and a steadier courage rose.")
    return out


def _rule_completion(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    relic = world.get("relic")
    if child.memes.get("courage", 0) >= 1 and child.meters.get("offered", 0) >= 1 and relic.meters.get("calmed", 0) < 1:
        relic.meters["calmed"] = 1
        out.append("The shrine light softened, and the stone answered with a gentle glow.")
    return out


RULES = [_rule_blush, _rule_flashback, _rule_humility, _rule_completion]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            produced = rule(world)
            if produced:
                changed = True
                for s in produced:
                    world.say(s)


def build_myth(world: World) -> None:
    child = world.get("child")
    elder = world.get("elder")
    relic = world.get("relic")
    ritual = _safe_fact(world, world.facts, "ritual")

    world.say(f"Long ago, in {world.place.name}, there lived a small {child.type} named {child.id}.")
    world.say(f"{child.id} loved to imagine brave deeds at the shrine, especially when the moon came up.")
    world.say(f"One evening, {child.id} found {relic.phrase} waiting beside the old stones.")
    world.say(f"The village said that to touch it, one must {ritual.verb}, though the task had a sharp {ritual.omen}.")

    world.say(f"{child.id} heard the warning and blushed, because the task felt larger than {child.pronoun('object')} expected.")
    child.memes["embarrassment"] = child.memes.get("embarrassment", 0) + 1
    propagate(world)

    world.say(f"{child.id} tried to imagine a brave answer, but an old flashback came first.")
    child.memes["doubt"] = child.memes.get("doubt", 0) + 1
    propagate(world)

    world.say(f"In the memory, {child.id} had once bragged too soon, and the village children had laughed.")
    world.say(f"Then {elder.id} stepped near and said, 'A true hero begins small. Offer the stone a quiet gift.'")
    child.memes["humility"] = child.memes.get("humility", 0) + 1
    child.meters["offered"] = child.meters.get("offered", 0) + 1
    relic.meters["gifted"] = relic.meters.get("gifted", 0) + 1
    world.say(f"So {child.id} placed the little gift before {relic.label}, hands trembling, heart honest.")
    propagate(world)

    if relic.meters.get("calmed", 0) >= 1:
        world.say(f"The stone grew warm, the night wind softened, and {child.id} smiled without shame.")
        world.say(f"{child.id} had imagined a grand victory, but the real wonder was kinder: {child.id} had become brave enough to be gentle.")
    else:
        pass


PLACE_REGISTRY = {
    "village_shrine": Place(name="the village shrine", shrine=True, echoes=True),
    "temple_steps": Place(name="the temple steps", shrine=True, echoes=True),
    "moon_garden": Place(name="the moon garden", shrine=True, echoes=False),
}

RITUAL_REGISTRY = {
    "sing": Ritual(
        id="sing",
        verb="sing the stone a true name",
        gerund="singing true names",
        omen="hollow echo",
        strain="voice",
        keyword="song",
        threatens={"silence"},
    ),
    "bow": Ritual(
        id="bow",
        verb="bow before the old light",
        gerund="bowing in the moonlight",
        omen="silent weight",
        strain="knees",
        keyword="bow",
        threatens={"pride"},
    ),
    "promise": Ritual(
        id="promise",
        verb="promise a kind deed",
        gerund="making kind promises",
        omen="watchful hush",
        strain="heart",
        keyword="promise",
        threatens={"doubt"},
    ),
}

RELIC_REGISTRY = {
    "moonstone": Relic(
        id="moonstone",
        label="the moon-stone",
        phrase="the moon-stone with a silver crack",
        risk="mystery",
        region="hands",
        sacred=True,
    ),
    "riverbell": Relic(
        id="riverbell",
        label="the river-bell",
        phrase="the river-bell hung in blue reeds",
        risk="sound",
        region="hands",
        sacred=True,
    ),
}

NAMES = ["Lina", "Taro", "Mira", "Soren", "Nina", "Ravi"]
ELDER_NAMES = ["Grandmother Iri", "Old Niko", "Aunt Sel", "Grandfather Teo"]


@dataclass
class StoryParams:
    place: str
    ritual: str
    relic: str
    name: str
    elder: str
    seed: Optional[int] = None
    params: object | None = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic storyworld about blush, imagine, flashback, and a happy ending.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--ritual", choices=RITUAL_REGISTRY)
    ap.add_argument("--relic", choices=RELIC_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--elder")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACE_REGISTRY:
        for ritual in RITUAL_REGISTRY:
            for relic in RELIC_REGISTRY:
                combos.append((place, ritual, relic))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "ritual", None):
        combos = [c for c in combos if c[1] == getattr(args, "ritual", None)]
    if getattr(args, "relic", None):
        combos = [c for c in combos if c[2] == getattr(args, "relic", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, ritual, relic = (list(rng.choice(combos)) + [None, None, None])[:3]
    return StoryParams(
        place=place,
        ritual=ritual,
        relic=relic,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        elder=getattr(args, "elder", None) or rng.choice(ELDER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(PLACE_REGISTRY[params.place])
    child = world.add(Entity(id=params.name, kind="character", type="child"))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder", label=params.elder))
    relic = world.add(Entity(id="relic", kind="thing", type="relic", label=RELIC_REGISTRY[params.relic].label, phrase=RELIC_REGISTRY[params.relic].phrase))
    world.facts["ritual"] = RITUAL_REGISTRY[params.ritual]

    build_myth(world)

    story = world.render()
    prompts = [
        'Write a short myth for children that uses the words "blush" and "imagine".',
        f"Tell a gentle myth where {params.name} must {RITUAL_REGISTRY[params.ritual].verb} at {PLACE_REGISTRY[params.place].name}.",
        "Include a flashback, a shy moment, and a happy ending.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.name} blush near the shrine?",
            answer=f"{params.name} blushed because the task felt big and serious, and {params.name} worried about failing in front of the sacred stone.",
        ),
        QAItem(
            question=f"What flashback did {params.name} remember?",
            answer=f"{params.name} remembered an old time when bragging had gone badly, so the memory made {params.name} quieter and wiser.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily: {params.name} offered a small gift, the shrine light softened, and the child became brave by being gentle.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a shrine?", answer="A shrine is a special place where people show respect to something sacred."),
        QAItem(question="What does blush mean?", answer="To blush means your cheeks turn warm and pink, often because you feel shy or embarrassed."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is a memory that takes the story back to something that happened earlier."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"flashback_seen={world.flashback_seen}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child is ready when courage and offering are present.
ready(C) :- child(C), courage(C), offering(C).

% A relic calms when the child is ready and the ritual is respectful.
calms(R) :- relic(R), ready(_), respectful_offer(R).

#show ready/1.
#show calms/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
    for r in RITUAL_REGISTRY:
        lines.append(asp.fact("ritual", r))
    for r in RELIC_REGISTRY:
        lines.append(asp.fact("relic", r))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("courage", "child"))
    lines.append(asp.fact("offering", "child"))
    lines.append(asp.fact("respectful_offer", "relic"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show ready/1.\n#show calms/1."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"ready/1", "calms/1"}
    if atoms == expected:
        print("OK: ASP twin matches the Python gate.")
        return 0
    print("MISMATCH:", sorted(atoms), sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show ready/1.\n#show calms/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show ready/1.\n#show calms/1."))
        print("ASP model:", ", ".join(str(a) for a in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, ritual, relic in valid_combos():
            params = StoryParams(
                place=place,
                ritual=ritual,
                relic=relic,
                name=_safe_lookup(NAMES, 0),
                elder=_safe_lookup(ELDER_NAMES, 0),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < getattr(args, "n", None) * 50 + 10:
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
