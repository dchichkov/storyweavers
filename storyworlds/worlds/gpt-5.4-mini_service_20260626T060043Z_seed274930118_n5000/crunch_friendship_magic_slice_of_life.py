#!/usr/bin/env python3
"""
A small Slice-of-Life storyworld about Friendship and gentle Magic, with a
single crunchy problem that can be solved in a reasonable way.

Premise:
- Two friends share a cozy afternoon.
- A little magic makes a crunchy snack or craft extra special.
- The first idea is a bit too loud, messy, or unkind.
- The friends fix it together and end with a warm, happy image.

This world is designed so the story is driven by a live state model rather than
a frozen paragraph template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    partner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    hero: object | None = None
    pal: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
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
    indoors: bool
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
    makes: str
    can_fix: set[str]
    can_cover: set[str] = field(default_factory=set)
    quiet: bool = False
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
    crunch_kind: str
    risk: str
    zone: set[str]
    keyword: str
    mood: str
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
        self.magic_items: dict[str, MagicItem] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_magic(self, item: MagicItem) -> MagicItem:
        self.magic_items[item.id] = item
        return item

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.magic_items = copy.deepcopy(self.magic_items)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


THRESHOLD = 1.0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle friendship-and-magic slice-of-life storyworld.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--item", choices=sorted(MAGIC_ITEMS))
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if getattr(args, "activity", None) and getattr(args, "item", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        item = _safe_lookup(MAGIC_ITEMS, getattr(args, "item", None))
        if act.crunch_kind not in item.can_fix:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "name", None) is None:
        pass
    choices = valid_choices()
    choices = [
        c for c in choices
        if (getattr(args, "place", None) is None or c.place == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c.activity == getattr(args, "activity", None))
        and (getattr(args, "item", None) is None or c.item == getattr(args, "item", None))
        and (getattr(args, "gender", None) is None or c.gender == getattr(args, "gender", None))
    ]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return rng.choice(choices)


@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    name: str
    friend: str
    gender: str
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


def valid_choices() -> list["StoryParams"]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for item_id, item in MAGIC_ITEMS.items():
                if act.crunch_kind in item.can_fix:
                    for gender in ["girl", "boy"]:
                        if gender == "girl":
                            names = GIRL_NAMES
                            friend_names = FRIEND_NAMES
                        else:
                            names = BOY_NAMES
                            friend_names = FRIEND_NAMES
                        for name in names:
                            for friend in friend_names:
                                if friend != name:
                                    out.append(StoryParams(place, act_id, item_id, name, friend, gender))
    return out


SETTINGS = {
    "kitchen": Setting("the kitchen", True, {"crackers", "cookies", "tea"}),
    "sunroom": Setting("the sunroom", True, {"crackers", "cookies", "cards"}),
    "backyard": Setting("the backyard", False, {"leaves", "twigs"}),
}

ACTIVITIES = {
    "crackers": Activity(
        id="crackers",
        verb="make crunchy crackers",
        gerund="making crunchy crackers",
        crunch_kind="crunch",
        risk="too loud and crumbly",
        zone={"table"},
        keyword="crunch",
        mood="cozy",
    ),
    "leaves": Activity(
        id="leaves",
        verb="jump on the leaves",
        gerund="jumping on leaves",
        crunch_kind="crunch",
        risk="too loud and scattered",
        zone={"ground"},
        keyword="crunch",
        mood="playful",
    ),
    "cookies": Activity(
        id="cookies",
        verb="bake little cookies",
        gerund="baking little cookies",
        crunch_kind="crunch",
        risk="too hard and dry",
        zone={"table"},
        keyword="crunch",
        mood="warm",
    ),
}

MAGIC_ITEMS = {
    "sparkle_spoon": MagicItem(
        id="sparkle_spoon",
        label="a sparkle spoon",
        phrase="a little sparkle spoon with a blue handle",
        effect="it could stir in a tiny shine",
        makes="soft",
        can_fix={"crunch"},
        can_cover={"table"},
    ),
    "hush_jar": MagicItem(
        id="hush_jar",
        label="a hush jar",
        phrase="a round hush jar with a gold lid",
        effect="it could calm a noisy mess",
        makes="quiet",
        can_fix={"crunch"},
        can_cover={"table", "ground"},
        quiet=True,
    ),
    "share_bell": MagicItem(
        id="share_bell",
        label="a share bell",
        phrase="a small share bell that rang once",
        effect="it helped friends take turns",
        makes="kind",
        can_fix={"crunch"},
        can_cover={"table", "ground"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ruby", "Tia", "Vera"]
BOY_NAMES = ["Owen", "Eli", "Milo", "Finn", "Theo", "Noah"]
FRIEND_NAMES = ["Sage", "Pip", "June", "Rowan", "Iris", "Benny"]


def select_valid_item(act: Activity) -> list[MagicItem]:
    return [i for i in MAGIC_ITEMS.values() if act.crunch_kind in i.can_fix]


def tell(setting: Setting, activity: Activity, item: MagicItem, name: str, friend: str, gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["kind", "curious"]))
    pal = world.add(Entity(id=friend, kind="character", type="friend", traits=["friendly"]))
    snack = world.add(Entity(id="snack", type="thing", label=activity.verb, phrase=activity.gerund))
    magic = world.add_magic(item)
    hero.partner = pal.id
    pal.partner = hero.id
    hero.memes["joy"] = 0
    pal.memes["joy"] = 0
    snack.meters["crunch"] = 0
    world.facts = {
        "hero": hero,
        "pal": pal,
        "snack": snack,
        "magic": magic,
        "activity": activity,
        "setting": setting,
    }

    world.say(f"{hero.id} and {pal.id} were having a quiet afternoon in {setting.place}.")
    world.say(f"They wanted to {activity.verb}, because {activity.mood} afternoons felt nice when shared.")
    world.para()

    if setting.indoors:
        world.say(f"{hero.id} brought out {magic.phrase}, and it seemed to make the room glow a little.")
    else:
        world.say(f"{hero.id} held up {magic.phrase}, and even the air seemed to wait for the trick.")
    world.say(f"It was a little magic that could {magic.effect}.")
    world.say(f"{hero.id} hoped it would make the {activity.keyword} feel special.")

    world.para()
    hero.memes["hope"] = 1
    pal.memes["hope"] = 1
    hero.meters["curiosity"] = 1

    if activity.id == "crackers":
        world.say(f"They started to make crunchy crackers, but the first batch came out {activity.risk}.")
    elif activity.id == "cookies":
        world.say(f"They started to bake little cookies, but the dough turned out {activity.risk}.")
    else:
        world.say(f"They started to jump on the leaves, but the pile became {activity.risk}.")
    snack.meters["crunch"] += 1
    hero.memes["worry"] = 1
    pal.memes["worry"] = 1

    if magic.quiet:
        world.say(f"{pal.id} covered {pal.pronoun('possessive')} ears and said the sound was too big.")
        hero.memes["sad"] = 1
        pal.memes["sad"] = 1
    else:
        world.say(f"{pal.id} frowned a little because the plan was fun, but not very kind yet.")

    world.para()
    world.say(f"Then {hero.id} remembered that {magic.label} was really for helping friends, not for winning.")
    hero.memes["kindness"] = 1
    pal.memes["trust"] = 1
    world.say(f'{hero.id} said, "Let’s make it softer and share it."')
    hero.memes["friendship"] = 1
    pal.memes["friendship"] = 1

    if activity.id == "crackers":
        world.say(f"They used {magic.label} to stir the batter until the crackers became light and golden instead of rough.")
    elif activity.id == "cookies":
        world.say(f"They used {magic.label} to smooth the dough until the cookies baked tender and sweet.")
    else:
        world.say(f"They used {magic.label} to settle the leaf pile into a neat path for both of them to hop along.")
    snack.meters["calm"] = 1
    hero.memes["joy"] += 1
    pal.memes["joy"] += 1

    world.para()
    world.say(f"In the end, {hero.id} and {pal.id} sat together with the finished {activity.keyword} and laughed.")
    world.say(f"The small magic stayed with them, and the afternoon felt easy, friendly, and just right.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(MAGIC_ITEMS, params.item), params.name, params.friend, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    pal = _safe_fact(world, f, "pal")
    act = _safe_fact(world, f, "activity")
    item = _safe_fact(world, f, "magic")
    return [
        f"Write a short slice-of-life story about {hero.id} and {pal.id} using the word crunch.",
        f"Tell a gentle friendship story where {hero.id} and {pal.id} try {act.verb} with {item.label}.",
        f"Write a cozy story for a child about magic helping friends fix a crunchy problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    pal = _safe_fact(world, f, "pal")
    act = _safe_fact(world, f, "activity")
    item = _safe_fact(world, f, "magic")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who were the story's friends?",
            answer=f"The story was about {hero.id} and {pal.id}, two friends spending a cozy afternoon together.",
        ),
        QAItem(
            question=f"What did they want to do in {setting.place}?",
            answer=f"They wanted to {act.verb}, because they wanted a small, happy moment to share.",
        ),
        QAItem(
            question=f"What magical thing helped them?",
            answer=f"{item.phrase} helped them fix the crunchy problem and make the plan work better.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the crunchy problem was softened or settled, and the friends were happy together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means people care about each other, share time together, and try to help when something goes wrong.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something impossible in real life that can help characters, change things, or make ordinary moments feel special.",
        ),
        QAItem(
            question="What does crunch mean?",
            answer="Crunch means a sharp, crisp sound or feeling, like stepping on leaves or biting a crunchy snack.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    for k, v in world.magic_items.items():
        lines.append(f"{k}: fix={sorted(v.can_fix)} cover={sorted(v.can_cover)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the magical item can reasonably fix the crunchy problem.
valid(Place, Act, Item) :- affords(Place, Act), crunch_problem(Act), fixable(Item, crunch).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("crunch_problem", aid))
    for iid, i in MAGIC_ITEMS.items():
        lines.append(asp.fact("item", iid))
        for c in sorted(i.can_fix):
            lines.append(asp.fact("fixable", iid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            for iid, item in MAGIC_ITEMS.items():
                if _safe_lookup(ACTIVITIES, aid).crunch_kind in item.can_fix:
                    out.append((place, aid, iid))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
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


def explain_rejection(act: Activity, item: MagicItem) -> str:
    return f"(No story: {item.label} does not reasonably fix {act.gerund}.)"


CURATED = [
    StoryParams("kitchen", "crackers", "sparkle_spoon", "Mia", "Sage", "girl"),
    StoryParams("sunroom", "cookies", "share_bell", "Owen", "June", "boy"),
    StoryParams("backyard", "leaves", "hush_jar", "Lina", "Pip", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                if getattr(args, "place", None) or getattr(args, "activity", None) or getattr(args, "item", None) or getattr(args, "gender", None) or getattr(args, "name", None) or getattr(args, "friend", None):
                    params = resolve_params(args, rng)
                    params.seed = base_seed + i
                else:
                    params = rng.choice(valid_choices())
                    params.seed = base_seed + i
            except StoryError:
                continue
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

    for idx, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
