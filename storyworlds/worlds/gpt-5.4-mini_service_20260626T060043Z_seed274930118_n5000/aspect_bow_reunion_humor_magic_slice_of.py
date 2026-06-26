#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/aspect_bow_reunion_humor_magic_slice_of.py
===============================================================================================================

A small slice-of-life storyworld about a neighborhood reunion, a funny
misunderstanding, and a little bit of magic around an important bow.

Premise:
- A child wants to look right for a family reunion at the community garden.
- A magical bow is part of the outfit, but its "aspect" changes depending on
  how it is tied and worn.
- The child worries the bow looks silly; the parent sees that the reunion is
  really about being together, not about perfect accessories.
- Humor comes from the bow's dramatic behavior, but the story resolves gently
  when the child learns the bow only needed a tiny adjustment.

World model:
- Physical meters track the state of the bow, outfit, and setting details.
- Emotional memes track worry, pride, delight, and social ease.
- Magic is represented as a tiny lawful effect: when the bow is tied with
  care, it reveals a bright "aspect" that fits the reunion.

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of results.py containers
- lazy import of asp.py inside ASP helpers
- build_parser, resolve_params, generate, emit, main
- Python gate + inline ASP_RULES twin
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    bow: object | None = None
    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    place: str
    indoor: bool = False
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
class Event:
    id: str
    verb: str
    gerund: str
    worry: str
    hum: str
    aspect: str
    magic: bool = False
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
class Bow:
    id: str
    label: str
    phrase: str
    aspect: str
    worn_region: str = "hair"
    magical: bool = True
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _event_blossom(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    bow = _safe_fact(world, world.facts, "bow")
    if child.memes.get("care", 0) >= THRESHOLD and bow.meters.get("tied", 0) >= THRESHOLD:
        sig = ("blossom", bow.id)
        if sig not in world.fired:
            world.fired.add(sig)
            bow.meters["shine"] = 1
            bow.meters["aspect"] = 1
            out.append("The bow settled into a bright new aspect.")
    return out


def _event_laugh(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    parent = _safe_fact(world, world.facts, "parent")
    bow = _safe_fact(world, world.facts, "bow")
    if child.memes.get("worry", 0) >= THRESHOLD and parent.memes.get("warmth", 0) >= THRESHOLD:
        sig = ("laugh", bow.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] = 0
            child.memes["delight"] = 1
            out.append("That funny little bow made them both laugh.")
    return out


RULES = [
    _event_blossom,
    _event_laugh,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def child_name_options() -> list[str]:
    return ["Mina", "Ari", "Noah", "Lina", "Theo", "June", "Iris", "Otto"]


def build_story(setting: Setting, event: Event, bow_cfg: Bow, child_name: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl" if child_name in {"Mina", "Lina", "June", "Iris"} else "boy"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    bow = world.add(Entity(
        id="bow",
        type="bow",
        label=bow_cfg.label,
        phrase=bow_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
        worn_by=child.id,
    ))
    child.traits = [trait, "sensitive"]

    # state setup
    child.memes["worry"] = 1
    child.memes["care"] = 1
    parent.memes["warmth"] = 1

    world.say(f"{child.id} was a {trait} child who liked getting ready carefully for family days.")
    world.say(f"{child.id} had a {bow.label} that looked extra fancy, and {child.pronoun('possessive')} {parent.label} called it a little magic bow.")
    world.say(f"That afternoon, everyone was going to a reunion at {setting.place}.")

    world.para()
    world.say(f"{child.id} wanted to {event.verb}, but the {bow.label} seemed to change its {event.aspect} every time it was touched.")
    world.say(f"{child.pronoun().capitalize()} held still and tried to fix the ribbon, yet the bow kept looking a bit too big, a bit too shiny, and a bit too funny.")

    propagate(world, narrate=True)

    world.para()
    world.say(f"{parent.pronoun().capitalize()} smiled and said, \"Try one careful knot, then see what happens.\"")
    bow.meters["tied"] = 1
    child.memes["care"] = 2
    propagate(world, narrate=True)
    world.say(f"{child.id} looked in the mirror and giggled. The bow was still bright, but now it matched the reunion perfectly.")
    world.say(f"At {setting.place}, everyone noticed the lovely bow, and the day felt warm, simple, and just right.")

    world.facts.update(
        child=child,
        parent=parent,
        bow=bow,
        event=event,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = {
    "garden": Setting(place="the community garden", indoor=False, affords={"reunion"}),
    "yard": Setting(place="the back yard", indoor=False, affords={"reunion"}),
    "hall": Setting(place="the little hall", indoor=True, affords={"reunion"}),
}

EVENTS = {
    "reunion": Event(
        id="reunion",
        verb="wear the bow for the reunion",
        gerund="getting ready for the reunion",
        worry="looking too silly",
        hum="a funny wobble",
        aspect="aspect",
        magic=True,
        tags={"reunion", "bow", "magic", "humor"},
    )
}

BOWS = {
    "red": Bow(id="red", label="red bow", phrase="a bright red bow", aspect="sparkly"),
    "blue": Bow(id="blue", label="blue bow", phrase="a soft blue bow", aspect="shimmering"),
    "gold": Bow(id="gold", label="gold bow", phrase="a tiny gold bow", aspect="glowing"),
}

TRAITS = ["careful", "cheerful", "thoughtful", "shy", "bright", "patient"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    event: str
    bow: str
    name: str
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
    for place, setting in SETTINGS.items():
        for event_id in setting.affords:
            for bow_id in BOWS:
                combos.append((place, event_id, bow_id))
    return combos


def explain_rejection() -> str:
    return "(No story: this world only supports a reunion scene with a bow that can be gently adjusted.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life reunion storyworld with a magical bow.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--bow", choices=BOWS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
              and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
              and (getattr(args, "bow", None) is None or c[2] == getattr(args, "bow", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event, bow = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(child_name_options())
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, bow=bow, name=name, parent=parent, trait=trait)


def tell(setting: Setting, event: Event, bow_cfg: Bow, name: str, parent_type: str, trait: str) -> World:
    return build_story(setting, event, bow_cfg, name, parent_type, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, event, bow, setting = f["child"], f["event"], f["bow"], f["setting"]
    return [
        f'Write a short slice-of-life story about a child named {child.id} getting ready for a reunion at {setting.place} with a magical bow.',
        f"Tell a gentle story where {child.id} worries about {bow.label}, but the family reunion still turns out happy.",
        f'Write a humorous, child-friendly story that includes the words "aspect", "bow", and "reunion".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, bow, event = f["child"], f["parent"], f["bow"], f["event"]
    return [
        QAItem(
            question=f"Who was getting ready for the reunion?",
            answer=f"{child.id} was getting ready for the reunion with {parent.label} nearby.",
        ),
        QAItem(
            question=f"What was funny about the bow?",
            answer=f"The bow kept changing its aspect and looked a little dramatic until it was tied carefully.",
        ),
        QAItem(
            question=f"How did the family fix the bow?",
            answer=f"They tried one careful knot, and then the magical bow settled into a bright, neat shape.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and giggly, because the bow looked just right for the reunion.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reunion?",
            answer="A reunion is a time when people who care about each other come together again and share time, food, and conversation.",
        ),
        QAItem(
            question="What is a bow?",
            answer="A bow is a ribbon tied into a shape with loops and ends, and people often wear it in hair or use it to decorate things.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something surprising can happen in a special way that feels impossible in real life, like a bow that changes its look when it is tied carefully.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A reunion scene is valid when the place affords the event and the bow exists.
valid(Place, Event, Bow) :- affords(Place, Event), bow(Bow).

% A bow is ready when it can be tied and reveals a bright aspect.
ready(Bow) :- bow(Bow), tied(Bow).
magic_aspect(Bow) :- ready(Bow), bright(Bow).
valid_story(Place, Event, Bow) :- valid(Place, Event, Bow), magic_aspect(Bow).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for ev in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, ev))
    for eid in EVENTS:
        lines.append(asp.fact("event", eid))
    for bid, bow in BOWS.items():
        lines.append(asp.fact("bow", bid))
        lines.append(asp.fact("bright", bid))
        lines.append(asp.fact("tied", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(EVENTS, params.event), _safe_lookup(BOWS, params.bow), params.name, params.parent, params.trait)
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
    StoryParams(place="garden", event="reunion", bow="red", name="Mina", parent="mother", trait="careful"),
    StoryParams(place="yard", event="reunion", bow="blue", name="Theo", parent="father", trait="cheerful"),
    StoryParams(place="hall", event="reunion", bow="gold", name="June", parent="mother", trait="thoughtful"),
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
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, event, bow) combos ({len(stories)} with readiness):\n")
        for place, event, bow in triples:
            print(f"  {place:8} {event:10} {bow:6}")
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
            header = f"### {p.name}: {p.event} at {p.place} (bow: {p.bow})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
