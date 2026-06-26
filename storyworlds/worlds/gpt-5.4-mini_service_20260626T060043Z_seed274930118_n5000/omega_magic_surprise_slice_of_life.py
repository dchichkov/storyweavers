#!/usr/bin/env python3
"""
storyworlds/worlds/omega_magic_surprise_slice_of_life.py
=========================================================

A small slice-of-life storyworld about an omega-named child, a little bit of
magic, and one gentle surprise that turns an ordinary day into a warm memory.

The seed idea:
- A quiet everyday errand or home task
- A small magical accident or discovery
- A surprise that first worries someone, then becomes helpful
- A calm ending image showing what changed

The simulation uses physical meters and emotional memes. Magic is modeled as a
real, limited force in the world, not a decorative label.

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


# ---------------------------------------------------------------------------
# Core data model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    magic: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    indoor: bool
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
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    surprise_kind: str
    can_help_with: set[str] = field(default_factory=set)
    location: str = ""
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
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    consequence: str
    zone: set[str]
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


@dataclass
class StoryParams:
    place: str
    activity: str
    magic_item: str
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
        self.zone: set[str] = set()
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
        clone.zone = set(self.zone)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"tea", "baking", "cleanup"}),
    "laundry": Setting(place="the laundry room", indoor=True, affords={"folding", "sorting"}),
    "balcony": Setting(place="the balcony", indoor=False, affords={"watering", "birdwatching"}),
    "garden": Setting(place="the garden", indoor=False, affords={"watering", "picking"}),
    "hallway": Setting(place="the hallway", indoor=True, affords={"painting", "cleanup"}),
}

ACTIVITIES = {
    "tea": Activity(
        id="tea",
        verb="make tea",
        gerund="making tea",
        mess="steam",
        consequence="fogged the window",
        zone={"air"},
        keyword="tea",
        tags={"warm", "drink"},
    ),
    "baking": Activity(
        id="baking",
        verb="bake muffins",
        gerund="baking muffins",
        mess="flour",
        consequence="dusty hands",
        zone={"hands", "nose"},
        keyword="muffins",
        tags={"food", "flour"},
    ),
    "watering": Activity(
        id="watering",
        verb="water the plants",
        gerund="watering the plants",
        mess="water",
        consequence="wet sleeves",
        zone={"hands", "arms"},
        keyword="watering can",
        tags={"plants", "water"},
    ),
    "painting": Activity(
        id="painting",
        verb="paint a little picture",
        gerund="painting a little picture",
        mess="paint",
        consequence="paint flecks",
        zone={"hands", "arms"},
        keyword="paint",
        tags={"art", "color"},
    ),
    "sorting": Activity(
        id="sorting",
        verb="sort laundry",
        gerund="sorting laundry",
        mess="lint",
        consequence="lint on cuffs",
        zone={"hands"},
        keyword="laundry",
        tags={"home", "cloth"},
    ),
    "cleanup": Activity(
        id="cleanup",
        verb="clean the table",
        gerund="cleaning the table",
        mess="soap",
        consequence="slippery fingers",
        zone={"hands"},
        keyword="soap",
        tags={"home", "clean"},
    ),
    "birdwatching": Activity(
        id="birdwatching",
        verb="watch the birds",
        gerund="watching the birds",
        mess="crumbs",
        consequence="tiny crumbs on the sill",
        zone={"hands"},
        keyword="birds",
        tags={"birds", "quiet"},
    ),
    "picking": Activity(
        id="picking",
        verb="pick berries",
        gerund="picking berries",
        mess="juice",
        consequence="sticky fingers",
        zone={"hands"},
        keyword="berries",
        tags={"fruit", "sweet"},
    ),
}

MAGIC_ITEMS = {
    "bell": MagicItem(
        id="bell",
        label="a little silver bell",
        phrase="a little silver bell with a blue ribbon",
        effect="answered with a soft chime",
        surprise_kind="sound",
        can_help_with={"cleanup", "birdwatching"},
        location="the windowsill",
    ),
    "jar": MagicItem(
        id="jar",
        label="a clear magic jar",
        phrase="a clear magic jar that caught sparkles in the air",
        effect="made a tiny light dance inside it",
        surprise_kind="light",
        can_help_with={"painting", "baking"},
        location="the shelf",
    ),
    "spoon": MagicItem(
        id="spoon",
        label="a wooden spoon",
        phrase="an old wooden spoon that hummed when tapped",
        effect="stirred itself once",
        surprise_kind="motion",
        can_help_with={"tea", "baking"},
        location="the mug rack",
    ),
    "ribbon": MagicItem(
        id="ribbon",
        label="a ribbon charm",
        phrase="a ribbon charm tied in a careful bow",
        effect="untangled knots a little bit",
        surprise_kind="help",
        can_help_with={"sorting", "cleanup", "watering"},
        location="the basket",
    ),
}

NAMES = ["Omega", "Milo", "Nia", "June", "Ada", "Theo", "Pip", "Luna"]
PARENTS = ["mother", "father", "grandma", "grandpa"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def can_use_magic(activity: Activity, item: MagicItem) -> bool:
    return activity.id in item.can_help_with


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for item_id, item in MAGIC_ITEMS.items():
                if can_use_magic(act, item):
                    combos.append((place, act_id, item_id))
    return combos


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    if activity.id not in world.setting.affords:
        return
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    world.zone = set(activity.zone)


def predict(world: World, actor: Entity, activity: Activity, item: MagicItem) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity)
    magic = sim.get(item.id)
    return {
        "helpful": can_use_magic(activity, item),
        "mess": actor.meters.get(activity.mess, 0.0),
        "surprise": magic.meters.get("revealed", 0.0) > 0,
    }


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a quiet little {hero.type} who liked ordinary mornings and small routines."
    )


def setup(world: World, hero: Entity, parent: Entity, activity: Activity, item: MagicItem) -> None:
    hero.memes["comfort"] = hero.memes.get("comfort", 0.0) + 1.0
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} were at {world.setting.place}."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, and on the shelf sat {item.phrase}."
    )


def surprise_reveal(world: World, hero: Entity, item: MagicItem) -> None:
    item_ent = world.get(item.id)
    item_ent.meters["revealed"] = item_ent.meters.get("revealed", 0.0) + 1.0
    hero.memes["surprised"] = hero.memes.get("surprised", 0.0) + 1.0
    world.say(
        f"Then, with no warning at all, {item.label} {item.effect}."
    )


def concern(world: World, parent: Entity, hero: Entity, activity: Activity, item: MagicItem) -> None:
    parent.memes["alert"] = parent.memes.get("alert", 0.0) + 1.0
    pred = predict(world, hero, activity, item)
    if pred["helpful"]:
        world.say(
            f"{parent.id} blinked, because the surprise looked strange at first."
        )
    else:
        pass


def use_magic(world: World, hero: Entity, parent: Entity, activity: Activity, item: MagicItem) -> None:
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    parent.memes["relief"] = parent.memes.get("relief", 0.0) + 1.0
    world.say(
        f"{hero.id} tried it, and the little magic turned out to be useful."
    )


def resolution(world: World, hero: Entity, parent: Entity, activity: Activity, item: MagicItem) -> None:
    if activity.id == "cleanup":
        ending = "The table got wiped clean, and the bell sounded once like a pleased smile."
    elif activity.id == "baking":
        ending = "The muffins rose in the oven, and the jar held a warm gold glow by the window."
    elif activity.id == "painting":
        ending = "The picture dried on the counter, and the jar kept one bright sparkle for later."
    elif activity.id == "watering":
        ending = "The plants drank up the water, and the ribbon charm stayed tied around the can."
    elif activity.id == "tea":
        ending = "The tea steamed softly, and the spoon gave one tiny happy hum."
    else:
        ending = "The room felt calmer, and the surprise fit neatly into the rest of the day."
    world.say(
        f"In the end, {hero.id} and {parent.id} laughed together."
    )
    world.say(ending)


def tell(setting: Setting, activity: Activity, item: MagicItem, hero_name: str = "Omega", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    magic = world.add(Entity(id=item.id, kind="thing", type="magic", label=item.label, phrase=item.phrase, location=item.location))
    hero.memes["calm"] = 1.0

    introduce(world, hero)
    setup(world, hero, parent, activity, item)
    world.para()
    concern(world, parent, hero, activity, item)
    surprise_reveal(world, hero, item)
    use_magic(world, hero, parent, activity, item)
    world.para()
    resolution(world, hero, parent, activity, item)

    world.facts.update(hero=hero, parent=parent, activity=activity, item=item, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------
@dataclass
class StoryWorld:
    pass
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    item = _safe_fact(world, f, "item")
    return [
        f'Write a short slice-of-life story for a child named {hero.id} that includes the word "omega" and a small magic surprise.',
        f"Tell a gentle everyday story where {hero.id} wants to {act.verb} and discovers {item.phrase}.",
        f"Write a calm story about a normal day that becomes special when magic helps with {act.gerund}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    act = _safe_fact(world, f, "activity")
    item = _safe_fact(world, f, "item")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a small child whose day starts out ordinary and ends with a gentle surprise.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}. That was the normal part of the day before the magic showed up.",
        ),
        QAItem(
            question=f"What magical thing was waiting nearby?",
            answer=f"{item.phrase} was waiting nearby, and it turned out to be the surprise that helped the day go well.",
        ),
        QAItem(
            question=f"Why did {parent.id} look concerned at first?",
            answer=f"{parent.id} looked concerned because the magic surprise seemed unusual at first, even though it later helped.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {parent.id} laughing together after the magic made the ordinary task easier.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "tea": [("What is tea?", "Tea is a warm drink made by soaking leaves or herbs in hot water.")],
    "baking": [("What does baking mean?", "Baking means cooking food in an oven, like bread, cookies, or muffins.")],
    "watering": [("Why do plants need water?", "Plants need water to stay healthy and grow.")],
    "painting": [("Why can paint be messy?", "Paint can drip and smudge, so people often try to keep it on paper and not on clothes.")],
    "sorting": [("What does sorting mean?", "Sorting means putting things into groups so they are easier to find or fold.")],
    "cleanup": [("Why do people clean tables?", "People clean tables so crumbs and spills do not stay there.")],
    "birdwatching": [("Why do birds matter in a yard?", "Birds are part of nature, and people enjoy watching them because they move and sing.")],
    "picking": [("What are berries?", "Berries are small fruits that can grow on bushes or vines.")],
    "bell": [("What does a bell do?", "A bell makes a ringing sound when it is moved or struck.")],
    "jar": [("What is a jar?", "A jar is a container with a lid that can hold food, small objects, or decorations.")],
    "spoon": [("What is a spoon for?", "A spoon is used for stirring, scooping, and eating soft foods.")],
    "ribbon": [("What is a ribbon used for?", "A ribbon can tie things together or decorate gifts, hair, or small objects.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    for tag in sorted(f["activity"].tags | {f["item"].id}):
        if tag in WORLD_KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An activity and a magic item are compatible if the item can help with it.
compatible(A, I) :- activity(A), item(I), helps(I, A).

valid_story(P, A, I) :- setting(P), affords(P, A), compatible(A, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for iid, item in MAGIC_ITEMS.items():
        lines.append(asp.fact("item", iid))
        for a in sorted(item.can_help_with):
            lines.append(asp.fact("helps", iid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with omega, magic, and a small surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--magic-item", choices=MAGIC_ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    if getattr(args, "place", None) or getattr(args, "activity", None) or getattr(args, "magic_item", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
            and (getattr(args, "magic_item", None) is None or c[2] == getattr(args, "magic_item", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, magic_item = rng.choice(list(combos))
    name = getattr(args, "name", None) or "Omega"
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    return StoryParams(place=place, activity=activity, magic_item=magic_item, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(MAGIC_ITEMS, params.magic_item), params.name, params.parent)
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
    StoryParams(place="kitchen", activity="baking", magic_item="jar", name="Omega", parent="mother"),
    StoryParams(place="balcony", activity="watering", magic_item="ribbon", name="Omega", parent="father"),
    StoryParams(place="hallway", activity="cleanup", magic_item="bell", name="Omega", parent="grandma"),
    StoryParams(place="garden", activity="picking", magic_item="ribbon", name="Omega", parent="mother"),
    StoryParams(place="kitchen", activity="tea", magic_item="spoon", name="Omega", parent="grandpa"),
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
        print(f"{len(triples)} compatible (place, activity, magic_item) combos:\n")
        for place, act, item in triples:
            print(f"  {place:10} {act:12} {item:10}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (magic: {p.magic_item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
