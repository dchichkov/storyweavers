#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/destine_curiosity_flashback_dialogue_fable.py
======================================================================================================

A tiny fable-like story world built from the seed word "destine".

Premise:
- A curious young creature wants to do something before she is ready.
- An older helper remembers a past mistake and warns her.
- Dialogue reveals the warning, and a simple compromise lets the child keep exploring safely.

World model:
- Physical meters track risk, effort, and protective gear.
- Emotional memes track curiosity, worry, courage, and relief.
- A flashback is not just decorative: it is triggered by a remembered prior event in the world model.
- Dialogue is state-driven: it arises when curiosity rises, when warning is needed, and when the compromise is accepted.

Style:
- Fable-like, child-facing, compact, and moralized without being preachy.
- The story ends with a clear image showing what changed.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for k in ("risk", "distance", "dust", "effort"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "relief", "pride", "memory"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "owl"}
        male = {"boy", "father", "man", "fox"}
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
class Place:
    name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    risk_kind: str
    zone: set[str]
    prompt_word: str
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
class Item:
    id: str
    label: str
    phrase: str
    region: str
    guards: set[str]
    covers: set[str]
    plural: bool = False
    protective: bool = True
    answer: str = ""
    question: str = ""
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
class StoryParams:
    place: str
    quest: str
    item: str
    name: str
    gender: str
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def pron_name(entity: Entity) -> str:
    return entity.id


def _rule_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("curiosity", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["distance"] += 1
        actor.meters["risk"] += 1
        out.append(f"{actor.id} crept closer, because curiosity is a small lantern that asks for one more look.")
    return out


def _rule_protect(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if not item.protective:
                continue
            sig = ("protect", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if item.region in {"feet", "paws"}:
                actor.meters["risk"] = max(0.0, actor.meters["risk"] - 1.0)
            out.append(f"{actor.id}'s {item.label} made the little path safer.")
    return out


def _rule_flashback(world: World) -> list[str]:
    out: list[str] = []
    elder = world.facts.get("elder")
    hero = world.facts.get("hero")
    if not elder or not hero:
        return out
    h = world.get(hero.id)
    if h.meters["risk"] < THRESHOLD or h.memes["memory"] >= THRESHOLD:
        return out
    sig = ("flashback", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    h.memes["memory"] += 1
    h.memes["worry"] += 1
    out.append(
        f"{h.id} remembered the last time {h.pronoun('subject')} ran ahead and got lost in the dark."
    )
    return out


CAUSAL_RULES = [
    _rule_curiosity,
    _rule_flashback,
    _rule_protect,
]


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


def predict_risk(world: World, hero: Entity, quest: Quest) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["curiosity"] += 1
    sim.get(hero.id).meters["risk"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get(hero.id).meters["risk"],
        "worry": sim.get(hero.id).memes["worry"],
    }


def choose_item(quest: Quest, item: Item) -> bool:
    return quest.risk_kind in item.guards and quest.zone.issubset(item.covers)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"Once there was a little {trait} {hero.type} named {hero.id}, and {hero.id} loved every unopened door."
    )


def set_scene(world: World, quest: Quest) -> None:
    if world.place.indoors:
        world.say(f"In {world.place.name}, the light stayed soft and the corners seemed full of whispering.")
    else:
        world.say(f"In {world.place.name}, the wind moved lightly, and {quest.prompt_word} waited under the open sky.")


def desire(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} wanted to {quest.verb}, because {quest.prompt_word} looked too interesting to ignore.")


def warn(world: World, elder: Entity, hero: Entity, quest: Quest, item: Entity) -> None:
    pred = predict_risk(world, hero, quest)
    if pred["risk"] < THRESHOLD:
        return
    world.say(
        f'"Careful," said {elder.id}. "A little more of that road may leave {hero.pronoun("object")} with {quest.risk}."'
    )


def flashback(world: World, hero: Entity) -> None:
    if hero.memes["memory"] >= THRESHOLD:
        world.say(
            f"For a moment, {hero.id} saw a flashback of {hero.pronoun("possessive")} small feet slipping in the mud, and {hero.pronoun("subject")} went quiet."
        )


def dialogue_choice(world: World, elder: Entity, hero: Entity, quest: Quest, item: Entity) -> None:
    world.say(f'"What should I do instead?" asked {hero.id}.')
    world.say(
        f'"Wear your {item.label}," said {elder.id}. "Then you may {quest.verb}, and the risk will stay small."'
    )


def accept(world: World, hero: Entity, elder: Entity, quest: Quest, item: Entity) -> None:
    hero.memes["curiosity"] += 0.5
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.meters["risk"] = max(0.0, hero.meters["risk"] - 1.0)
    world.say(
        f"{hero.id} nodded, put on {item.label}, and smiled. Soon {hero.id} was {quest.gerund}, and {elder.id} was smiling too."
    )


def closing(world: World, hero: Entity, elder: Entity, quest: Quest, item: Entity) -> None:
    world.say(
        f"By the end, {hero.id} had {quest.gerund} safely, {item.phrase} stayed useful, and the little fable felt destine to be remembered."
    )


def tell(place: Place, quest: Quest, item_cfg: Item, name: str = "Mira", gender: str = "girl", elder_type: str = "owl", trait: str = "curious") -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    item = world.add(Entity(
        id=item_cfg.id,
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        protective=item_cfg.protective,
        covers=set(item_cfg.covers),
        plural=item_cfg.plural,
        owner=hero.id,
        caretaker=elder.id,
    ))
    item.worn_by = hero.id

    world.facts.update(hero=hero, elder=elder, item=item, quest=quest, place=place)

    intro(world, hero)
    set_scene(world, quest)
    world.para()
    desire(world, hero, quest)
    warn(world, elder, hero, quest, item)
    propagate(world, narrate=True)
    flashback(world, hero)
    dialogue_choice(world, elder, hero, quest, item)
    world.para()
    accept(world, hero, elder, quest, item)
    closing(world, hero, elder, quest, item)
    world.facts["resolved"] = True
    return world


PLACES = {
    "meadow": Place(name="the meadow", affords={"peek", "climb"}),
    "woods": Place(name="the woods", affords={"peek", "follow"}),
    "riverbank": Place(name="the riverbank", affords={"follow", "peek"}),
    "orchard": Place(name="the orchard", affords={"peek", "climb"}),
}

QUESTS = {
    "peek": Quest(
        id="peek",
        verb="peek past the briar gate",
        gerund="peeking past the briar gate",
        risk="scratchy brambles on the paws",
        risk_kind="scratchy",
        zone={"paws"},
        prompt_word="the briar gate",
        tags={"curiosity", "flashback"},
    ),
    "follow": Quest(
        id="follow",
        verb="follow the silver trail",
        gerund="following the silver trail",
        risk="mud on the paws",
        risk_kind="muddy",
        zone={"paws"},
        prompt_word="the silver trail",
        tags={"curiosity"},
    ),
    "climb": Quest(
        id="climb",
        verb="climb the old branch",
        gerund="climbing the old branch",
        risk="a tumble from the high limb",
        risk_kind="rough",
        zone={"paws"},
        prompt_word="the old branch",
        tags={"curiosity", "flashback"},
    ),
}

ITEMS = {
    "gloves": Item(id="gloves", label="soft gloves", phrase="the soft gloves stayed warm and helpful", region="paws", guards={"scratchy", "muddy", "rough"}, covers={"paws"}, plural=True),
    "boots": Item(id="boots", label="little boots", phrase="the little boots stayed dry and steady", region="paws", guards={"muddy", "rough", "scratchy"}, covers={"paws"}, plural=True),
}

GIRL_NAMES = ["Mira", "Lina", "Tess", "Nora"]
BOY_NAMES = ["Finn", "Pip", "Otis", "Jules"]
TRAITS = ["curious", "bold", "gentle", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for q in QUESTS.values():
            for i in ITEMS.values():
                if choose_item(q, i):
                    combos.append((p, q.id, i.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, quest, item = f["hero"], f["elder"], f["quest"], f["item"]
    return [
        f'Write a short fable about a child named {hero.id} who feels curiosity about "{quest.prompt_word}" and learns a safer way.',
        f"Tell a gentle story where {hero.id} wants to {quest.verb}, but {elder.id} remembers a past mistake and speaks in dialogue.",
        f'Write a child-facing fable that includes a flashback, a warning, and the word "destine".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, quest, item = f["hero"], f["elder"], f["quest"], f["item"]
    return [
        QAItem(
            question=f"Why did {hero.id} want to {quest.verb}?",
            answer=f"{hero.id} wanted to {quest.verb} because {quest.prompt_word} looked exciting and {hero.pronoun('subject')} was full of curiosity.",
        ),
        QAItem(
            question=f"What did {elder.id} remember before {hero.id} got too far?",
            answer=f"{elder.id} remembered a flashback of the last time {hero.id} rushed ahead and got into trouble.",
        ),
        QAItem(
            question=f"What did {hero.id} wear so the story could end safely?",
            answer=f"{hero.id} wore {item.label}, which helped keep the risk small while {hero.id} kept exploring.",
        ),
        QAItem(
            question=f"What was the little dialogue answer to {hero.id}'s question?",
            answer=f"{elder.id} told {hero.id} to wear {item.label} and then go on with the plan more safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the feeling that makes someone want to learn, look, or ask more questions."),
        QAItem(question="What is a flashback?", answer="A flashback is a remembered moment from before that comes back into the mind during the story."),
        QAItem(question="What is dialogue?", answer="Dialogue is when characters speak to one another in the story."),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(X) :- curiosity(X).
flashback(X) :- memory(X).
safe(X) :- protective(Item), worn_by(Item,X), covers(Item,paws), risk(X,R), not bad_risk(R).
resolved(X) :- curious(X), flashback(X), safe(X).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for q in sorted(_safe_lookup(PLACES, p).affords):
            lines.append(asp.fact("affords", p, q))
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
        lines.append(asp.fact("risk_kind", q.id, q.risk_kind))
    for i in ITEMS.values():
        lines.append(asp.fact("item", i.id))
        lines.append(asp.fact("protective", i.id))
        lines.append(asp.fact("covers", i.id, "paws"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world of curiosity, flashback, dialogue, and a safer choice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["owl", "fox"])
    ap.add_argument("--name")
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
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["owl", "fox"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, item=item, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(ITEMS, params.item),
                 name=params.name, gender=params.gender, elder_type=params.elder, trait=params.trait)
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
    StoryParams(place="meadow", quest="peek", item="gloves", name="Mira", gender="girl", elder="owl", trait="curious"),
    StoryParams(place="woods", quest="follow", item="boots", name="Finn", gender="boy", elder="fox", trait="bright"),
    StoryParams(place="orchard", quest="climb", item="gloves", name="Tess", gender="girl", elder="owl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(sorted(valid_combos()))
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
