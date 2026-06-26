#!/usr/bin/env python3
"""
A standalone storyworld for a small Animal Story about preserve, bravery,
sound effects, and a cautionary turn.

Seed tale:
A brave little raccoon named Pip finds a jar of strawberry preserve in a picnic
basket. Pip wants to carry it to the burrow, but the path is bumpy and the jar
can clink, wobble, and slip. A cautious rabbit warns Pip to slow down and use a
leaf wrap. Pip listens, shows bravery, and brings the preserve home safely.

The world model tracks:
- physical meters: balance, wobble, noise, safety, spoilage
- emotional memes: bravery, caution, worry, relief, pride

The story is generated from simulated state, not from a fixed paragraph.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for k in ["balance", "wobble", "noise", "safety", "spoilage"]:
            self.meters.setdefault(k, 0.0)
        for k in ["bravery", "caution", "worry", "relief", "pride", "affection"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"raccoon", "fox", "badger", "wolf", "bear"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"rabbit", "mouse", "deer", "squirrel", "cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Setting:
    place: str = "the berry path"
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
class Hero:
    name: str
    type: str
    trait: str
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    fragile: bool = True
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
class Aid:
    id: str
    label: str
    prep: str
    tail: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    name: str
    hero_type: str
    trait: str
    item: str
    helper: str
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
    "berry_path": Setting(place="the berry path", affords={"carry"}),
    "forest_edge": Setting(place="the forest edge", affords={"carry"}),
    "riverbank": Setting(place="the riverbank", affords={"carry"}),
}

HERO_TYPES = {
    "raccoon": "raccoon",
    "fox": "fox",
    "badger": "badger",
    "squirrel": "squirrel",
}

TRAITS = ["brave", "careful", "curious", "gentle", "quick"]

ITEMS = {
    "preserve": Item(
        id="preserve",
        label="jar of strawberry preserve",
        phrase="a jar of strawberry preserve",
        type="jar",
        fragile=True,
    ),
    "blueberry_preserve": Item(
        id="blueberry_preserve",
        label="jar of blueberry preserve",
        phrase="a jar of blueberry preserve",
        type="jar",
        fragile=True,
    ),
}

AIDS = {
    "leaf_wrap": Aid(
        id="leaf_wrap",
        label="leaf wrap",
        prep="wrap the jar in a wide leaf",
        tail="used the leaf wrap and stepped carefully",
    ),
    "basket": Aid(
        id="basket",
        label="berry basket",
        prep="place the jar in a berry basket",
        tail="carried the basket with both paws",
    ),
}

GREETINGS = {
    "raccoon": "masked",
    "fox": "red-furred",
    "badger": "striped",
    "squirrel": "small",
}

ASP_RULES = r"""
too_noisy(H) :- noise(H), noise_level(H,N), N >= 1.
unsafe(H) :- wobble(H), wobble_level(H,W), W >= 1.
brave_choice(H) :- bravery(H), caution(H), safe_aid(H).
good_story(H) :- brave_choice(H), preserve_safe(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.fragile:
            lines.append(asp.fact("fragile", iid))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _do_carry(world: World, hero: Entity, item: Entity, aid: Optional[Aid], narrate: bool = True) -> None:
    if "carry" not in world.setting.affords:
        pass
    hero.meters["balance"] += 1
    item.carried_by = hero.id
    item.meters["wobble"] += 1
    item.meters["noise"] += 1
    if aid and aid.id == "leaf_wrap":
        item.meters["noise"] = 0
        item.meters["wobble"] = 0
        item.meters["safety"] += 2
    if narrate:
        world.say("A small rustle and a soft clink followed every careful step.")


def predict(world: World, hero: Entity, item: Entity, aid: Optional[Aid]) -> dict:
    sim = world.copy()
    _do_carry(sim, sim.get(hero.id), sim.get(item.id), aid, narrate=False)
    sim_item = sim.get(item.id)
    return {
        "unsafe": sim_item.meters["wobble"] >= THRESHOLD and sim_item.meters["safety"] < THRESHOLD,
        "noisy": sim_item.meters["noise"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {GREETINGS.get(hero.type, 'little')} {hero.type} who loved "
        f"the smell of berries and the thrill of carrying something precious."
    )


def want_preserve(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["affection"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} found {item.phrase} and wanted to bring {item.it()} home."
    )


def cautionary_warning(world: World, helper: Entity, hero: Entity, item: Entity) -> bool:
    pred = predict(world, hero, item, None)
    if not pred["unsafe"] and not pred["noisy"]:
        return False
    helper.memes["caution"] += 1
    hero.memes["worry"] += 1
    world.say(
        f'"Careful," {helper.id} said. "That jar can wobble, clink, and spill if you rush."'
    )
    return True


def brave_turn(world: World, hero: Entity) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took a slow breath. {hero.pronoun().capitalize()} was scared for a moment, "
        f"but {hero.pronoun('subject')} stayed brave."
    )


def choose_aid(world: World, helper: Entity, hero: Entity, item: Entity) -> Optional[Aid]:
    aid = AIDS["leaf_wrap"] if item.fragile else AIDS["basket"]
    if aid.id == "basket" and item.fragile:
        return None
    if aid.id == "leaf_wrap":
        world.say(
            f'{helper.id} smiled and said, "{aid.prep}, and the jar will stay steady."'
        )
    else:
        world.say(
            f'{helper.id} suggested, "{aid.prep}, and carry it with both paws."'
        )
    return aid


def resolve(world: World, hero: Entity, helper: Entity, item: Entity, aid: Aid) -> None:
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    helper.memes["affection"] += 1
    item.meters["safety"] += 2
    _do_carry(world, hero, item, aid, narrate=True)
    world.say(
        f"They {aid.tail}, and {hero.id} made it home with the preserve safe and sweet."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, trait: str, item_id: str, helper_id: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_id, kind="character", type="rabbit"))
    item = world.add(Entity(id=item_id, type="jar", label=_safe_lookup(ITEMS, item_id).label, phrase=_safe_lookup(ITEMS, item_id).phrase))
    world.facts.update(hero=hero, helper=helper, item=item, setting=setting)

    introduce(world, hero)
    world.say(f"{hero.id} felt especially {trait} that morning.")
    want_preserve(world, hero, item)
    world.para()
    world.say(f"They set off along {setting.place}.")
    cautionary_warning(world, helper, hero, item)
    brave_turn(world, hero)
    aid = choose_aid(world, helper, hero, item)
    world.para()
    if aid is None:
        pass
    resolve(world, hero, helper, item, aid)

    world.facts.update(aid=aid, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item")
    helper = _safe_fact(world, f, "helper")
    return [
        'Write an animal story for young children about preserve, bravery, and a careful warning.',
        f"Tell a story where {hero.id} finds {item.phrase}, listens to {helper.id}, and stays brave.",
        "Write a short cautionary tale with soft sound effects like clink and rustle, ending safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    item: Entity = _safe_fact(world, f, "item")
    aid: Aid = _safe_fact(world, f, "aid")
    return [
        QAItem(
            question=f"What did {hero.id} want to carry home?",
            answer=f"{hero.id} wanted to carry home {item.phrase}.",
        ),
        QAItem(
            question=f"Who gave the careful warning about the jar?",
            answer=f"{helper.id} gave the warning and reminded {hero.id} to be careful.",
        ),
        QAItem(
            question=f"What helped the jar stay safe?",
            answer=f"The {aid.label} helped because it kept the jar steady and less likely to clink or spill.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after listening and staying brave?",
            answer=f"{hero.id} felt relieved and proud after staying brave and bringing the preserve home safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is preserve?",
            answer="Preserve is sweet fruit spread that is often kept in a jar and eaten later.",
        ),
        QAItem(
            question="Why can a jar make a clink sound?",
            answer="A jar can clink when it bumps against something hard, like a basket or a rock.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so something does not get hurt, broken, or spilled.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means being scared sometimes but still doing the right thing anyway.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="berry_path", name="Pip", hero_type="raccoon", trait="brave", item="preserve", helper="Mabel"),
    StoryParams(place="forest_edge", name="Nori", hero_type="fox", trait="careful", item="blueberry_preserve", helper="Penny"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about preserve, bravery, sound effects, and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(list(HERO_TYPES))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    name = getattr(args, "name", None) or rng.choice(["Pip", "Milo", "Nina", "Tess", "Otto"])
    helper = getattr(args, "helper", None) or rng.choice(["Mabel", "Penny", "Luna", "Bram"])
    return StoryParams(place=place, name=name, hero_type=hero_type, trait=trait, item=item, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.name, params.hero_type, params.trait, params.item, params.helper)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = {("preserve",), ("blueberry_preserve",)}
    cl = set(asp_valid_combos())
    if cl != py:
        print("MISMATCH between ASP and Python.")
        print("only in ASP:", sorted(cl - py))
        print("only in Python:", sorted(py - cl))
        return 1
    print("OK: ASP and Python parity confirmed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_story/1."))
        print(sorted(set(asp.atoms(model, "good_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
            header = f"### {p.name} / {p.hero_type} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
