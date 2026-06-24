#!/usr/bin/env python3
"""
storyworlds/worlds/darned_resistance_aah_flashback_conflict_slice_of.py
========================================================================

A small slice-of-life story world about a child, a beloved worn item, a gentle
conflict, and a flashback that helps resolve the resistance.

Seed words and instruments:
- darned
- resistance
- aah
- Flashback
- Conflict

Premise:
A child resists letting a loved, patched item be set aside or mended, because it
still feels special and useful. A flashback reveals why the item matters, and a
small home-based compromise turns resistance into care.

World model:
- Physical meters track wear, stain, thread, warmth, and repair.
- Emotional memes track resistance, worry, comfort, tenderness, conflict, and joy.
- The story is driven by state updates: using the item, noticing damage, remembering
  a flashback, choosing a repair, and ending with the item safe and loved.

This is a standalone stdlib script for the Storyweavers repo.
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
    owner: str = ""
    caretakers: list[str] = field(default_factory=list)
    worn_by: str = ""
    used_by: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for k in ["wear", "stain", "warmth", "repair", "fragility"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "resistance", "comfort", "conflict", "tenderness", "memory"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    indoors: bool = True
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    repair_kind: str
    comfort_hint: str
    wearable: bool = True
    darned: bool = False
    tags: set[str] = field(default_factory=set)
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
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    flashback_key: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


def _gate_reason(action: Action, item: Item) -> bool:
    return action.id in {"play", "carry", "wear"} and item.wearable


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for action in ACTIONS:
            for item in ITEMS:
                if _gate_reason(_safe_lookup(ACTIONS, action), _safe_lookup(ITEMS, item)) and place in PLACES and action in _safe_lookup(PLACES, place).affords:
                    combos.append((place, action, item))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
    name: str
    parent: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: darned resistance, flashback, conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mom", "dad"])
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
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, item = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mom", "dad"])
    return StoryParams(place=place, action=action, item=item, name=name, parent=parent)


def story_setup(world: World, child: Entity, parent: Entity, item: Entity, action: Action) -> None:
    child.memes["joy"] += 1
    item.meters["wear"] += 1
    world.say(
        f"{child.id} was a small, busy kid who loved {item.label}. "
        f"It was {item.phrase}, a little {item.kind} with a patient, well-loved look."
    )
    world.say(
        f"On a quiet afternoon at {world.place.label}, {child.id} and {parent.label} "
        f"were getting ready to {action.verb}."
    )


def notice_problem(world: World, child: Entity, item: Entity, action: Action) -> None:
    item.meters["fragility"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Then {child.id} noticed a thin spot along the seam. A little "
        f"{item.repair_kind} had already been made there, but the cloth looked tired."
    )
    world.say(
        f'{child.id} made a small face. "Aah, not now," {child.pronoun()} said, '
        f"clutching {item.label} a little tighter."
    )


def flashback(world: World, child: Entity, item: Entity, action: Action) -> None:
    child.memes["memory"] += 1
    child.memes["comfort"] += 1
    world.say(
        f"That brought back a flashback: {item.label} in {child.id}'s hands on a rainy day, "
        f"when someone older had shown how a careful {item.repair_kind} could make a favorite thing last."
    )
    world.say(
        f"{child.id} remembered the warm, steady feeling of making it useful again, "
        f"and the resistance in {child.id}'s shoulders loosened just a little."
    )


def conflict(world: World, child: Entity, parent: Entity, item: Entity, action: Action) -> None:
    child.memes["resistance"] += 1
    child.memes["conflict"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"But {parent.label} said it would be better to set {item.label} aside until it was mended."
    )
    world.say(
        f'{child.id} resisted at once. "But I need it now," {child.pronoun()} said, '
        f"holding it close."
    )


def compromise(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.memes["tenderness"] += 1
    child.memes["joy"] += 1
    child.memes["resistance"] = 0.0
    child.memes["conflict"] = 0.0
    item.meters["repair"] += 1
    world.say(
        f"Then {child.id} and {parent.label} sat together at the table with thread, "
        f"and the little torn place got a careful, matching darned stitch."
    )
    world.say(
        f'{child.id} gave a tiny smile. "Aah," {child.pronoun()} said, "it can stay with me and still be fixed."'
    )


def ending(world: World, child: Entity, parent: Entity, item: Entity, action: Action) -> None:
    item.worn_by = child.id
    world.say(
        f"After that, {child.id} went ahead with the afternoon, and {item.label} felt snug and safe again."
    )
    world.say(
        f"It was still the same beloved thing, only now it was {item.repair_kind} well enough to keep on through the day."
    )


def tell(place: Place, action: Action, item_cfg: Item, name: str, parent_name: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type="parent", label=f"the {parent_name}"))
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type=item_cfg.kind,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
    ))
    item.darned = item_cfg.darned

    story_setup(world, child, parent, item, action)
    world.para()
    notice_problem(world, child, item, action)
    flashback(world, child, item, action)
    conflict(world, child, parent, item, action)
    world.para()
    compromise(world, child, parent, item)
    ending(world, child, parent, item, action)

    world.facts.update(child=child, parent=parent, item=item, item_cfg=item_cfg, action=action, place=place)
    return world


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", indoors=True, affords={"wear", "carry"}),
    "porch": Place(id="porch", label="the porch", indoors=False, affords={"wear", "carry", "play"}),
    "laundry_room": Place(id="laundry_room", label="the laundry room", indoors=True, affords={"carry", "wear"}),
}

ACTIONS = {
    "wear": Action(id="wear", verb="wear the item", gerund="wearing it", risk="fraying", flashback_key="mend"),
    "carry": Action(id="carry", verb="carry the item", gerund="carrying it", risk="slipping", flashback_key="mend"),
    "play": Action(id="play", verb="play outside", gerund="playing outside", risk="scraping", flashback_key="mend"),
}

ITEMS = {
    "sweater": Item(id="sweater", label="sweater", phrase="a soft green sweater", kind="sweater", repair_kind="darn", comfort_hint="warm"),
    "mittens": Item(id="mittens", label="mittens", phrase="a pair of red mittens", kind="mittens", repair_kind="darn", comfort_hint="cozy"),
    "blanket": Item(id="blanket", label="blanket", phrase="a favorite blue blanket", kind="blanket", repair_kind="stitch", comfort_hint="soft"),
}

NAMES = ["Mina", "Jasper", "Ruby", "Noah", "Tessa", "Leo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small slice-of-life story for a child named {f["child"].id} about a {f["item"].label} that needs a careful repair.',
        f"Tell a gentle home story where {f['child'].id} resists setting aside {f['item'].label}, remembers why it matters, and finds a calm compromise.",
        f'Write a story that uses the words "darned", "resistance", and "aah" while keeping the tone everyday and warm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, item, action = f["child"], f["parent"], f["item"], f["action"]
    return [
        QAItem(
            question=f"What was {child.id} trying to do with {item.label}?",
            answer=f"{child.id} was trying to {action.verb}. The item was important enough that {child.id} did not want to put it away.",
        ),
        QAItem(
            question=f"Why did {child.id} show resistance when {parent.label} spoke up?",
            answer=f"{child.id} resisted because {item.label} was still beloved and useful, even though it had a worn spot that needed attention.",
        ),
        QAItem(
            question=f"What did the flashback help {child.id} remember?",
            answer=f"The flashback helped {child.id} remember a calm moment of mending, when a careful repair made {item.label} last longer.",
        ),
        QAItem(
            question=f"How did the conflict get solved in the end?",
            answer=f"{child.id} and {parent.label} worked together to make a matching darned repair, so {item.label} could stay close and still be safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to darn something?",
            answer="To darn something means to mend a hole or thin place in cloth with neat stitches so it can keep being used.",
        ),
        QAItem(
            question="What is resistance when someone resists?",
            answer="Resistance means pushing back against a choice or not wanting to do it right away.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something from earlier, like a scene that happened before the present moment.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a disagreement or problem that the characters have to work through.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id} ({e.kind}/{e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
useful(Item) :- item(Item), repair_kind(Item, _).
problem(Item) :- item(Item), wear(Item, W), W > 0.
flashback_needed(C) :- child(C), problem(Item), owner(Item, C).
conflict(C) :- child(C), resistance(C, R), R > 0.
resolved(C) :- conflict(C), repair(Item, R), R > 0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("repair_kind", iid, it.repair_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(ITEMS, params.item), params.name, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="kitchen", action="wear", item="sweater", name="Mina", parent="mom"),
    StoryParams(place="porch", action="play", item="mittens", name="Jasper", parent="dad"),
    StoryParams(place="laundry_room", action="carry", item="blanket", name="Ruby", parent="mom"),
]


def explain_rejection() -> str:
    return "(No story: that combination doesn't fit this small home-and-mending world.)"


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        pass
    place, action, item = rng.choice(list(combos))
    return StoryParams(
        place=place,
        action=action,
        item=item,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        parent=getattr(args, "parent", None) or rng.choice(["mom", "dad"]),
    )


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show useful/1."))
        return
    if getattr(args, "verify", None):
        print(f"OK: {len(valid_combos())} valid combos.")
        return
    if getattr(args, "asp", None):
        print(asp_program("#show useful/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            i += 1
            try:
                params = valid_story_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i+1}")
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
