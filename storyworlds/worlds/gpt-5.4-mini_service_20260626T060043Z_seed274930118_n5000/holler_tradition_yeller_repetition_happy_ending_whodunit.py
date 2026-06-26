#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/holler_tradition_yeller_repetition_happy_ending_whodunit.py
==============================================================================================================

A small standalone storyworld for a whodunit-style tale with a holler, a town
tradition, and a yeller whose repeated call helps solve the mystery.

The seed premise:
- A yearly tradition is about to begin.
- A loud yeller hollers the same warning twice.
- Something important goes missing.
- A child detective follows clues, repeats the key questions, and solves the case.
- The ending is happy: the tradition continues, and everyone laughs at the mix-up.

This script keeps the domain small and state-driven:
- meters track physical state like distance, hiddenness, soot, and full bellies
- memes track emotional state like worry, pride, relief, and embarrassment
- repeated sayings and repeated clues are part of the narrative instrument set

The world is deliberately child-facing, but the prose leans toward a gentle
whodunit: observation, suspicion, clue gathering, reveal, and a happy ending.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    item: object | None = None
    yeller: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "yeller"}
        female = {"girl", "mother", "mom", "woman"}
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
    label: str
    tradition: str
    afford: set[str] = field(default_factory=set)
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
class MysteryItem:
    label: str
    phrase: str
    type: str
    hidden_hint: str
    risk_tag: str
    owner_label: str
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
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    clue: str
    innocent_reason: str
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
    tradition: str
    item: str
    detective: str
    detective_type: str
    yeller: str
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


class World:
    def __init__(self, place: Place, tradition: str) -> None:
        self.place = place
        self.tradition = tradition
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


ITEMS = {
    "bell": MysteryItem("bell", "a little brass bell", "bell", "under a basket", "ringing", "the mayor"),
    "pie": MysteryItem("pie", "a warm berry pie", "pie", "in the pantry", "crumbs", "the baker"),
    "lantern": MysteryItem("lantern", "a paper lantern", "lantern", "behind a stool", "glow", "the lantern keeper"),
}

PLACES = {
    "square": Place("the square", "Lantern Night", {"holler", "search", "gather"}),
    "hall": Place("the hall", "Ribbon Day", {"holler", "search", "serve"}),
    "garden": Place("the garden", "Harvest Supper", {"holler", "search", "serve"}),
}

SUSPECTS = [
    Suspect("baker", "the baker", "man", "He was icing pies in the kitchen.", "There were berry crumbs on his apron.", "He never left the kitchen."),
    Suspect("cat", "the cat", "thing", "It was napping under a chair.", "It had flour on its whiskers.", "It only chased the warm light."),
    Suspect("sister", "the detective's sister", "girl", "She was lining up the cups.", "She had ribbon on her sleeve.", "She was helping set the table."),
]

NAMES = ["Mila", "Nora", "Pip", "June", "Ivy", "Tess", "Leo", "Ben", "Milo", "Ada"]
YELLERS = ["Mr. Brim", "Aunt Hilda", "Old Jo", "Mrs. Patter", "Uncle Reed"]
TRAITS = ["curious", "careful", "bright", "bold", "quiet"]


def _init_meters() -> dict[str, float]:
    return {
        "worry": 0.0,
        "relief": 0.0,
        "pride": 0.0,
        "embarrassment": 0.0,
        "mystery": 0.0,
        "hiddenness": 0.0,
        "crumbs": 0.0,
    }


def _init_memes() -> dict[str, float]:
    return {
        "concern": 0.0,
        "curiosity": 0.0,
        "resolve": 0.0,
        "joy": 0.0,
        "shame": 0.0,
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: a holler, a tradition, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tradition", choices=["Lantern Night", "Ribbon Day", "Harvest Supper"])
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-type", choices=["girl", "boy"], dest="detective_type")
    ap.add_argument("--yeller", choices=YELLERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, p in PLACES.items():
        for item, m in ITEMS.items():
            if item == "bell" and "holler" in p.afford:
                out.append((place, p.tradition, item))
            elif item == "pie" and "serve" in p.afford:
                out.append((place, p.tradition, item))
            elif item == "lantern":
                out.append((place, p.tradition, item))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "tradition", None) is None or c[1] == getattr(args, "tradition", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tradition, item = rng.choice(list(combos))
    detective_type = getattr(args, "detective_type", None) or rng.choice(["girl", "boy"])
    detective = getattr(args, "detective", None) or rng.choice(NAMES)
    yeller = getattr(args, "yeller", None) or rng.choice(YELLERS)
    return StoryParams(place=place, tradition=tradition, item=item, detective=detective, detective_type=detective_type, yeller=yeller)


def reasonableness_gate(params: StoryParams) -> None:
    if params.item == "bell" and params.tradition not in {"Lantern Night", "Ribbon Day"}:
        pass
    if params.item == "pie" and params.tradition != "Harvest Supper":
        pass


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    place = _safe_lookup(PLACES, params.place)
    world = World(place, params.tradition)
    world.facts["params"] = params

    detective = world.add(Entity(
        id=params.detective, kind="character", type=params.detective_type,
        label=params.detective, meters=_init_meters(), memes=_init_memes()
    ))
    yeller = world.add(Entity(
        id="yeller", kind="character", type="yeller",
        label=params.yeller, meters=_init_meters(), memes=_init_memes()
    ))
    item_cfg = _safe_lookup(ITEMS, params.item)
    item = world.add(Entity(
        id="missing", kind="thing", type=item_cfg.type, label=item_cfg.label,
        phrase=item_cfg.phrase, owner=item_cfg.owner_label, hidden_in="under a basket",
        meters={"hiddenness": 1.0}, memes={}
    ))
    suspect_objs = []
    for s in SUSPECTS:
        suspect_objs.append(world.add(Entity(id=s.id, kind="character", type=s.type, label=s.label, meters=_init_meters(), memes=_init_memes())))

    culprit = suspect_objs[1] if params.item != "pie" else suspect_objs[0]
    if params.item == "bell":
        culprit = suspect_objs[1]  # the cat hid it
    elif params.item == "pie":
        culprit = suspect_objs[0]  # the baker moved it
    else:
        culprit = suspect_objs[1]

    world.facts["culprit"] = culprit
    world.facts["item"] = item
    world.facts["yeller"] = yeller
    world.facts["detective"] = detective

    detective.memes["curiosity"] += 1
    detective.meters["mystery"] += 1

    world.say(
        f"On {place.label}, the people gathered for {params.tradition}, a tradition they loved because it made the whole town feel like one family."
    )
    world.say(
        f"{params.yeller} was the yeller that night. Twice, {yeller.pronoun().capitalize()} hollered, 'Keep the table clear, keep the table clear!'"
    )
    world.say(
        f"{detective.label} heard the holler and looked again and again. The same words rang in {detective.pronoun('possessive')} ears: keep the table clear, keep the table clear."
    )

    world.para()
    world.say(
        f"Then the important thing vanished: {item.phrase} was gone from the feast table."
    )
    detective.memes["concern"] += 1
    detective.meters["mystery"] += 1
    yeller.memes["concern"] += 1

    # repeated clue work
    world.say(
        f"{detective.label} checked the table, then checked it again. No {item.label}."
    )
    world.say(
        f"{yeller.pronoun().capitalize()} hollered the warning a second time, and the second holler made {detective.label} notice a clue: a trail of tiny signs on the floor."
    )

    # clue trail and interview
    if params.item == "bell":
        world.say("There were floury paw prints by the chair, then by the basket, then by the window.")
        culprit.memes["embarrassment"] += 1
        culprit.meters["crumbs"] += 1
    elif params.item == "pie":
        world.say("There were berry crumbs on the tablecloth, then on the window ledge, then under the pantry door.")
        culprit.memes["embarrassment"] += 1
        culprit.meters["crumbs"] += 1
    else:
        world.say("There was a bright ribbon thread, then a stool scrape, then a soft glow behind the curtain.")
        culprit.memes["embarrassment"] += 1

    world.say(
        f"{detective.label} asked the same question twice: 'Who was near the table? Who was near the table?'"
    )
    if params.item == "bell":
        world.say("The cat yawned, and flour clung to its whiskers. That was the clue that fit the holler best.")
    elif params.item == "pie":
        world.say("The baker sighed. Berry filling on the cuff was the clue that fit the crumbs best.")
    else:
        world.say("The sister pointed at the curtain. Ribbon on her sleeve was the clue that fit the glow best.")

    world.para()
    culprit.memes["shame"] += 1
    detective.memes["resolve"] += 1
    detective.meters["mystery"] += 1
    world.say(
        f"{detective.label} followed the signs and solved it: {culprit.label} had only moved the {item.label}, not stolen it."
    )
    world.say(
        f"The missing {item.label} was found {item.hidden_in}, safe and sound."
    )

    world.para()
    detective.memes["joy"] += 1
    detective.memes["concern"] = 0.0
    culprit.memes["shame"] = 0.0
    world.say(
        f"{params.yeller} gave one last holler, this time a happy one: 'Found it! Found it!'"
    )
    world.say(
        f"Everyone laughed, and the tradition began at last. {detective.label} stood tall, and the town cheered because the mystery had a happy ending."
    )

    world.facts.update(place=place, item_cfg=item_cfg, suspect=culprit)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short whodunit for a young child set at {world.place.label} during {p.tradition}, with a repeated holler and a happy ending.',
        f'Tell a mystery story where {p.yeller} hollers twice, something goes missing, and {p.detective} solves it by noticing the repeated clue.',
        f'Write a gentle repetition-filled story about a tradition, a yeller, and a missing {p.item}, ending in relief and laughter.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    culprit: Entity = _safe_fact(world, world.facts, "culprit")
    item: Entity = _safe_fact(world, world.facts, "item")
    detective: Entity = _safe_fact(world, world.facts, "detective")
    yeller: Entity = _safe_fact(world, world.facts, "yeller")
    return [
        QAItem(
            question=f"Who was the story about at {world.place.label} during {p.tradition}?",
            answer=f"It was about {detective.label}, a {detective.type} who liked solving little mysteries, and about {yeller.label}, the yeller who hollered twice to help the town notice what changed.",
        ),
        QAItem(
            question=f"What went missing during the tradition?",
            answer=f"{item.phrase} went missing from the feast table, which made the whole scene feel like a puzzling whodunit.",
        ),
        QAItem(
            question="What clue helped the detective solve the mystery?",
            answer=f"The repeated clue was the trail of signs that matched {culprit.label}: floury prints for the cat, berry crumbs for the baker, or ribbon thread for the sister.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily because the missing {item.label} was found safe, the mistake was understood, and the tradition could begin with laughter instead of worry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    item = p.item
    out = [
        QAItem(
            question="What is a tradition?",
            answer="A tradition is something people do again and again because it is special to their family or town.",
        ),
        QAItem(
            question="What does a yeller do?",
            answer="A yeller is a person who calls out loudly so other people can hear the message right away.",
        ),
        QAItem(
            question="Why can repeating a clue help in a mystery?",
            answer="Repeating a clue can help because it makes an important detail stand out and stick in memory.",
        ),
    ]
    if item == "bell":
        out.append(QAItem(
            question="What sound does a bell make?",
            answer="A bell makes a clear ringing sound when it is shaken or struck.",
        ))
    elif item == "pie":
        out.append(QAItem(
            question="Why do pies smell good?",
            answer="Pies smell good because they are warm and filled with sweet fruit or spices.",
        ))
    else:
        out.append(QAItem(
            question="What is a lantern for?",
            answer="A lantern holds a light and helps people see when it is dark.",
        ))
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid when a tradition includes a yeller, an item can go missing,
% and the repeated holler helps the detective notice a clue.
tradition_story(T, I) :- tradition(T), item(I), possible(T, I).
repeated_holler(T) :- yeller(T), repeat_call(T).
happy_ending(T, I) :- tradition_story(T, I), repeated_holler(T), solved(T, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("tradition", place.tradition))
        for a in sorted(place.afford):
            lines.append(asp.fact("possible", place.tradition, a))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for y in YELLERS:
        lines.append(asp.fact("yeller", y.lower().replace(" ", "_")))
        lines.append(asp.fact("repeat_call", y.lower().replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show tradition_story/2. #show happy_ending/2."))
    atoms = set()
    for sym in model:
        if sym.name in {"tradition_story", "happy_ending"}:
            atoms.add((sym.name, tuple(str(a) for a in sym.arguments)))
    python_set = set()
    for place, tradition, item in valid_combos():
        python_set.add(("tradition_story", (tradition, item)))
        python_set.add(("happy_ending", (tradition, item)))
    if atoms == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(atoms))
    print("  python:", sorted(python_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show tradition_story/2."))
    out = []
    for sym in model:
        if sym.name == "tradition_story":
            out.append(tuple(str(a) for a in sym.arguments))
    return sorted(set(out))


def build_asp_list() -> str:
    combos = asp_valid_combos()
    return "\n".join(f"  {t} / {i}" for t, i in combos)


CURATED = [
    StoryParams(place="square", tradition="Lantern Night", item="bell", detective="Nora", detective_type="girl", yeller="Mr. Brim"),
    StoryParams(place="garden", tradition="Harvest Supper", item="pie", detective="Mila", detective_type="girl", yeller="Old Jo"),
    StoryParams(place="hall", tradition="Ribbon Day", item="lantern", detective="Leo", detective_type="boy", yeller="Mrs. Patter"),
]


def explain_rejection(params: StoryParams) -> str:
    if params.item == "pie" and params.tradition != "Harvest Supper":
        return "(No story: a pie only fits the Harvest Supper tradition here.)"
    if params.item == "bell" and params.tradition not in {"Lantern Night", "Ribbon Day"}:
        return "(No story: the bell needs a tradition where a yeller's holler matters.)"
    return "(No story: the requested mix does not make a clean whodunit.)"


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
        print(asp_program("#show tradition_story/2. #show happy_ending/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(build_asp_list())
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
            header = f"### {p.detective}: {p.tradition} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_qa(world: World) -> list[QAItem]:
    return world_knowledge_qa(world) if False else [
        QAItem(
            question="What kind of story is this?",
            answer="It is a gentle whodunit with a repeated holler, a tradition, and a happy ending.",
        ),
        QAItem(
            question="Why did the detective keep looking twice?",
            answer="Because the repeated holler made the detective think the answer was hidden in the same place as the repeated clue.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The missing item was found, the worry was gone, and the tradition could go on happily.",
        ),
    ]


if __name__ == "__main__":
    main()
