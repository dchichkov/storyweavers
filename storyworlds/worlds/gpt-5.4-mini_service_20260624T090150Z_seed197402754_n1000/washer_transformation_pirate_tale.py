#!/usr/bin/env python3
"""
A small pirate story world about a washer that can transform grimy treasure
into something bright and ready for the next voyage.

Seed tale:
---
A young pirate found a washer on a quiet dock. The washer was no ordinary machine.
When the pirate placed dirty clothes inside and pulled the lever, the washer hummed,
swirled, and transformed the cloth from salty and stained into clean and bright.
The pirate wanted to use it to prepare for a celebration, but a crab tide had
splashed mud over the deck and the captain's coat was ruined. The pirate worried
the washer might be too slow, yet the crew worked together, fed in the dirty coat,
and watched it come out fresh and shining. Then the pirate wore the coat proudly
to the feast.

Domain shape:
- One small setting with a dock, a ship, or a cove.
- A hero pirate with a treasured item that can become dirty or salty.
- A washer that can clean one or more items and may also transform their state.
- A tension beat where the hero needs the item cleaned before an event.
- A resolution where the washer changes the item and the crew can continue.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    item: object | None = None
    washer: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother", "captain-girl"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father", "captain-boy"}:
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
    has_waves: bool = False
    has_dock: bool = False
    has_cave: bool = False
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
class Item:
    id: str
    label: str
    phrase: str
    region: str
    clean_state: str
    dirty_state: str
    splashable: set[str] = field(default_factory=set)
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    answer: object | None = None
    question: object | None = None
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
class Washer:
    id: str
    label: str
    place_hint: str
    input_state: str = "dirty"
    output_state: str = "clean"
    can_transform: bool = True
    can_clean: bool = True
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.weather: str = "sea-breeze"

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


SETTINGS = {
    "dock": Setting(place="the dock", has_waves=True, has_dock=True),
    "ship": Setting(place="the ship", has_waves=True),
    "cove": Setting(place="the cove", has_waves=True, has_dock=False),
}

HEROES = [
    ("Mira", "girl", "captain-girl"),
    ("Finn", "boy", "captain-boy"),
    ("Nell", "girl", "captain-girl"),
    ("Jory", "boy", "captain-boy"),
]

TRAITS = ["brave", "quick", "cheerful", "spirited", "stubborn"]
EVENTS = ["feast", "parade", "dance", "harbor song", "ship launch"]

ITEMS = {
    "coat": Item(
        id="coat",
        label="captain's coat",
        phrase="a fine captain's coat",
        region="torso",
        clean_state="bright",
        dirty_state="muddy",
        splashable={"mud", "salt"},
        genders={"girl", "boy"},
    ),
    "hat": Item(
        id="hat",
        label="pirate hat",
        phrase="a tall pirate hat",
        region="head",
        clean_state="straight",
        dirty_state="crooked",
        splashable={"mud", "salt"},
    ),
    "flag": Item(
        id="flag",
        label="ship flag",
        phrase="a red ship flag",
        region="pole",
        clean_state="flapping",
        dirty_state="stained",
        splashable={"mud", "salt"},
    ),
}

WASHERS = {
    "washer": Washer(
        id="washer",
        label="the washer",
        place_hint="near the dock",
        can_transform=True,
        can_clean=True,
    ),
    "sea_washer": Washer(
        id="sea_washer",
        label="the sea washer",
        place_hint="inside the ship's laundry nook",
        can_transform=True,
        can_clean=True,
    ),
}

CURATED = [
    ("dock", "coat", "washer"),
    ("ship", "hat", "sea_washer"),
    ("cove", "flag", "washer"),
]


@dataclass
class StoryParams:
    setting: str
    item: str
    washer: str
    name: str
    gender: str
    trait: str
    event: str
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
    ap = argparse.ArgumentParser(
        description="A pirate story world about a washer that transforms dirty gear."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--washer", choices=WASHERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--event", choices=EVENTS)
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


def prize_at_risk(item: Item) -> bool:
    return True


def select_washer(item: Item) -> Optional[Washer]:
    return WASHERS["washer"] if item.id in {"coat", "hat", "flag"} else None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for item in ITEMS:
            for washer in WASHERS:
                if select_washer(_safe_lookup(ITEMS, item)) is not None:
                    out.append((s, item, washer))
    return out


def explain_rejection(item: Item) -> str:
    return f"(No story: the washer cannot reasonably transform {item.label} in this tiny pirate tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "item", None) and getattr(args, "item", None) not in ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
              and (getattr(args, "washer", None) is None or c[2] == getattr(args, "washer", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, item, washer = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice([h[0] for h in HEROES if h[1] == gender])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    event = getattr(args, "event", None) or rng.choice(EVENTS)
    return StoryParams(setting=setting, item=item, washer=washer, name=hero_name, gender=gender, trait=trait, event=event)


def transform_item(world: World, hero: Entity, item: Entity, washer: Washer) -> None:
    item.meters["dirty"] = 0
    item.meters["clean"] = 1
    item.memes["sparkle"] = 1
    world.say(
        f"The {washer.label} hummed and whirled, and {item.phrase} came out bright again."
    )


def generate_story(world: World, params: StoryParams) -> World:
    setting = world.setting
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    item_cfg = _safe_lookup(ITEMS, params.item)
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type=item_cfg.label,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
        caretaker=hero.id,
    ))
    washer_cfg = _safe_lookup(WASHERS, params.washer)
    washer = world.add(Entity(id=washer_cfg.id, kind="thing", type="washer", label=washer_cfg.label))

    world.say(f"On {setting.place}, little {params.trait} {hero.id} found {washer.label}.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved the sight of {washer.label} because it could change dirty things into shiny ones.")
    world.para()
    world.say(f"One day, a rough splash of mud and salt left {item.phrase} looking {item_cfg.dirty_state}.")
    world.say(f"The crew needed it for the {params.event}, but the coat could not go out like that.")
    world.say(f"{hero.id} frowned and said, \"Oh no, {item.label} needs the washer before the {params.event}!\"")
    world.para()
    world.say(f"{hero.id} carried {item.it()} to {washer.label} {washer.place_hint}.")
    world.say(f"The washer swirled like a tiny storm at sea.")
    transform_item(world, hero, item, washer_cfg)
    world.say(f"At last, {item.label} was ready, and the pirate crew cheered for the shining gear.")
    world.say(f"{hero.id} wore {item.it()} proudly and marched to the {params.event} with a grin.")
    world.facts.update(hero=hero, item=item, item_cfg=item_cfg, washer=washer_cfg, event=params.event, setting=setting)
    return world


KNOWLEDGE = {
    "washer": [(
        "What does a washer do?",
        "A washer spins water and soap around clothes to clean them, so dirty cloth can come out fresh again.",
    )],
    "pirate": [(
        "What is a pirate?",
        "A pirate is a seafaring character who sails ships, looks for treasure, and often wears bold clothes and hats.",
    )],
    "salt": [(
        "Why does salt water leave a mark?",
        "Salt water can dry into crusty spots that make clothes feel rough and look messy until they are washed.",
    )],
    "mud": [(
        "What happens when mud dries on cloth?",
        "Mud dries into a dirty stain, and washing helps lift it off the fabric.",
    )],
    "transform": [(
        "What does transform mean?",
        "Transform means to change something into a different state or look, like turning dirty cloth into clean cloth.",
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate story for a child that includes the word "washer" and a magical change.',
        f"Tell a tale where {f['hero'].id} uses {f['washer'].label} to help before the {f['event']}.",
        f"Write a gentle pirate story about dirty {f['item'].label} becoming bright again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    item: Entity = _safe_fact(world, f, "item")
    washer: Washer = _safe_fact(world, f, "washer")
    event = _safe_fact(world, f, "event")
    return [
        QAItem(
            question=f"What did {hero.id} find near the dock in the story?",
            answer=f"{hero.id} found {washer.label}, a machine that could wash and transform dirty pirate things.",
        ),
        QAItem(
            question=f"Why did {hero.id} use {washer.label}?",
            answer=f"{hero.id} used {washer.label} because {item.label} had gotten dirty and needed to be clean before the {event}.",
        ),
        QAItem(
            question=f"What changed after the washer hummed and whirled?",
            answer=f"{item.phrase} changed from dirty to bright again, so it was ready for the {event}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["washer"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["pirate"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["salt"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["transform"])
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
item(I) :- item_fact(I).
washer(W) :- washer_fact(W).

valid(S,I,W) :- setting(S), item(I), washer(W), transformable(I).
transformable(coat).
transformable(hat).
transformable(flag).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for i in ITEMS:
        lines.append(asp.fact("item_fact", i))
    for w in WASHERS:
        lines.append(asp.fact("washer_fact", w))
    for i in ("coat", "hat", "flag"):
        lines.append(asp.fact("transformable", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, washer) combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, (setting, item, washer) in enumerate(CURATED):
            params = StoryParams(
                setting=setting,
                item=item,
                washer=washer,
                name=random.choice([h[0] for h in HEROES]),
                gender=random.choice(["girl", "boy"]),
                trait=random.choice(TRAITS),
                event=random.choice(EVENTS),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
              and (getattr(args, "washer", None) is None or c[2] == getattr(args, "washer", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, item, washer = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice([h[0] for h in HEROES if h[1] == (getattr(args, "gender", None) or h[1])])
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    event = getattr(args, "event", None) or rng.choice(EVENTS)
    return StoryParams(setting=setting, item=item, washer=washer, name=hero_name, gender=gender, trait=trait, event=event)


if __name__ == "__main__":
    main()
