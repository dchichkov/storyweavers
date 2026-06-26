#!/usr/bin/env python3
"""
storyworlds/worlds/scape_suspense_bravery_magic_rhyming_story.py
=================================================================

A small, constraint-checked story world for a rhyming tale of suspense,
bravery, and magic.

The seed image is a tiny scene in a scape: a child sees a far-off glow,
walks into a hush of suspense, finds brave courage, and uses a little magic
to bring something safe home.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    charm_ent: object | None = None
    hero: object | None = None
    parent: object | None = None
    treasure_ent: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "sister"}
        male = {"boy", "father", "dad", "man", "king", "brother"}
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
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
    scape: str = ""
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
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    glow: str
    keyword: str
    zone: set[str]
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


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class MagicCharm:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    protects: set[str]
    plural: bool = False
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _r_spook(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("fear", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("spook", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["resolve"] = actor.memes.get("resolve", 0.0) + 1
        out.append(f"The hush grew deep, yet {actor.id} stood bright and brave.")
    return out


def _r_magic_glow(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("magic", 0.0) < THRESHOLD:
            continue
        sig = ("magic_glow", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["light"] = actor.meters.get("light", 0.0) + 1
        out.append(f"A little glow followed {actor.id}, soft as a snowflake's show.")
    return out


CAUSAL_RULES = [
    ("spook", _r_spook),
    ("magic_glow", _r_magic_glow),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_charm(quest: Quest, treasure: Treasure) -> Optional[MagicCharm]:
    for charm in CHARMS:
        if quest.danger in charm.protects and treasure.region in charm.covers:
            return charm
    return None


def predict(world: World, actor: Entity, quest: Quest, treasure_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(actor.id), quest, narrate=False)
    treasure = sim.entities.get(treasure_id)
    return {"safe": bool(treasure and treasure.meters.get("safe", 0.0) >= THRESHOLD)}


def _do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    actor.meters[quest.danger] = actor.meters.get(quest.danger, 0.0) + 1
    actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1
    world.zone = set(quest.zone)
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type}, keen on the night-lit way.")


def setting_line(world: World, quest: Quest) -> None:
    world.say(
        f"In {world.setting.place}, the {world.setting.scape} gleamed; "
        f"{world.setting.mood} and still, it seemed."
    )
    world.say(
        f"{quest.keyword.capitalize()} hummed nearby, a glimmer in the air, "
        f"and {quest.glow} waited there."
    )


def desire_line(world: World, hero: Entity, quest: Quest, treasure: Treasure) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {quest.verb}, to see what sparkled through the night, "
        f"and fetch {hero.pronoun('possessive')} {treasure.label} home by light."
    )


def suspense_line(world: World, hero: Entity, quest: Quest, treasure: Treasure) -> None:
    world.say(
        f"But shadows swayed and whispers played; the path grew narrow, long, and gray, "
        f"so {hero.id} paused a beat, then chose to stay."
    )
    world.say(
        f'"If I go on," {hero.pronoun()} said, "I may feel fear, '
        f'but I can still walk near and near."'
    )
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1


def warn_line(world: World, hero: Entity, quest: Quest, treasure: Treasure) -> bool:
    pred = predict(world, hero, quest, treasure.id)
    if not pred["safe"]:
        world.say(
            f"{hero.id} saw that the quest could start a fright, "
            f"and {hero.pronoun('possessive')} heart beat quick with might."
        )
        return True
    return False


def brave_line(world: World, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(
        f"{hero.id} took a breath and held it deep, then stepped ahead without a peep."
    )


def charm_line(world: World, hero: Entity, charm: MagicCharm, quest: Quest, treasure: Treasure) -> None:
    charm_ent = world.add(Entity(
        id=charm.id,
        type="charm",
        label=charm.label,
        owner=hero.id,
        protective=True,
        covers=set(charm.covers),
    ))
    charm_ent.worn_by = hero.id
    hero.memes["magic"] = hero.memes.get("magic", 0.0) + 1
    world.say(
        f'{hero.id} found {charm.label}, a shimmer spell that could {charm.prep}. '
        f'Its gentle gleam would {quest.keyword} clear the way.'
    )


def resolve_line(world: World, hero: Entity, quest: Quest, treasure: Treasure, charm: MagicCharm) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["fear"] = 0.0
    world.say(
        f"With {charm.label}, {hero.id} went on and on; the dark was not so mean. "
        f"{hero.pronoun().capitalize()} brought {hero.pronoun('possessive')} {treasure.label} home safe and clean."
    )
    world.say(
        f"The suspense was gone, the brave song sung, and magic lit the night; "
        f"{hero.id} smiled wide beneath the moon's small light."
    )


def tell(setting: Setting, quest: Quest, treasure: Treasure,
         hero_name: str = "Mira", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    treasure_ent = world.add(Entity(
        id="treasure",
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=treasure.region,
        plural=treasure.plural,
    ))

    intro(world, hero)
    setting_line(world, quest)
    world.say(f"{hero.id}'s {parent.label} had given {hero.pronoun('object')} a {treasure.phrase}.")
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {treasure.label} as if it were a tiny star.")
    world.para()
    desire_line(world, hero, quest, treasure)
    suspense_line(world, hero, quest, treasure)
    warn_line(world, hero, quest, treasure)
    brave_line(world, hero)
    charm = select_charm(quest, treasure)
    if charm is None:
        pass
    charm_line(world, hero, charm, quest, treasure)
    if predict(world, hero, quest, treasure.id)["safe"]:
        resolve_line(world, hero, quest, treasure, charm)
    world.facts.update(hero=hero, parent=parent, treasure=treasure_ent, quest=quest, setting=setting, charm=charm)
    return world


SETTINGS = {
    "moon_scape": Setting(place="the moon meadow", mood="soft and silvery", scape="moon scape", affords={"starlight", "lantern"}),
    "forest_scape": Setting(place="the pine wood", mood="dark and hushy", scape="forest scape", affords={"lantern", "starlight"}),
    "harbor_scape": Setting(place="the harbor path", mood="salt-bright and windy", scape="harbor scape", affords={"lantern", "tide"}),
    "garden_scape": Setting(place="the garden gate", mood="green and quiet", scape="garden scape", affords={"lantern", "bloom"}),
}

QUESTS = {
    "starlight": Quest(
        id="starlight",
        verb="follow the starlight",
        gerund="following starlight",
        rush="dash for the glow",
        danger="fear",
        glow="a star was shining",
        keyword="starlight",
        zone={"torso"},
        mood="night",
    ),
    "lantern": Quest(
        id="lantern",
        verb="cross the lantern bridge",
        gerund="crossing the lantern bridge",
        rush="step onto the bridge",
        danger="wobble",
        glow="a lantern was burning",
        keyword="lantern",
        zone={"feet", "legs"},
        mood="twilight",
    ),
    "tide": Quest(
        id="tide",
        verb="walk by the tide",
        gerund="walking by the tide",
        rush="run to the shore",
        danger="splash",
        glow="the tide was silver",
        keyword="tide",
        zone={"feet"},
        mood="dusk",
    ),
    "bloom": Quest(
        id="bloom",
        verb="pick the moon bloom",
        gerund="picking moon bloom",
        rush="reach for the flower",
        danger="thorn",
        glow="the blossoms glowed",
        keyword="bloom",
        zone={"hands", "torso"},
        mood="night",
    ),
}

TREASURES = {
    "cape": Treasure(label="cape", phrase="a starry cape", type="cape", region="torso"),
    "boots": Treasure(label="boots", phrase="tiny brave boots", type="boots", region="feet", plural=True),
    "lantern": Treasure(label="lantern", phrase="a little lantern", type="lantern", region="hands"),
    "crown": Treasure(label="crown", phrase="a moon crown", type="crown", region="head"),
}

CHARMS = [
    MagicCharm(id="glow_cloak", label="a glow cloak", prep="wrap the dark in gold", tail="wrapped the dark in gold", covers={"torso"}, protects={"fear"}),
    MagicCharm(id="lantern_sash", label="a lantern sash", prep="shine a path", tail="shone a path", covers={"feet", "legs"}, protects={"wobble", "splash"}),
    MagicCharm(id="moon_glove", label="a moon glove", prep="steady little hands", tail="steadied little hands", covers={"hands"}, protects={"thorn"}),
]

GIRL_NAMES = ["Mira", "Luna", "Nina", "Tessa", "Aria", "Ruby", "Ivy", "Sage"]
BOY_NAMES = ["Finn", "Noel", "Theo", "Owen", "Ezra", "Jasper", "Milo", "Pax"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = _safe_lookup(QUESTS, qid)
            for tid, treasure in TREASURES.items():
                if quest.zone == {"torso"} and treasure.region == "torso":
                    combos.append((sid, qid, tid))
                elif quest.zone == {"feet", "legs"} and treasure.region in {"feet"}:
                    combos.append((sid, qid, tid))
                elif quest.zone == {"feet"} and treasure.region == "feet":
                    combos.append((sid, qid, tid))
                elif quest.zone == {"hands", "torso"} and treasure.region == "hands":
                    combos.append((sid, qid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    quest: str
    treasure: str
    name: str
    gender: str
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


KNOWLEDGE = {
    "moon": [("What is the moon?", "The moon is a round rock in the sky that shines at night because it reflects sunlight.")],
    "lantern": [("What does a lantern do?", "A lantern gives off light, so people can see better in the dark.")],
    "starlight": [("What is starlight?", "Starlight is the light that reaches us from stars far away.")],
    "courage": [("What is courage?", "Courage is doing a hard thing even when you feel a little scared.")],
    "magic": [("What is magic in a story?", "Magic is a made-up force in stories that can do special things, like glow or float.")],
    "cape": [("What is a cape?", "A cape is a piece of clothing that hangs over your shoulders and back.")],
    "boots": [("What are boots for?", "Boots help protect your feet and keep them dry or safe.")],
}

KNOWLEDGE_ORDER = ["moon", "lantern", "starlight", "courage", "magic", "cape", "boots"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story about {f["hero"].id} in {f["setting"].scape} with suspense, bravery, and magic.',
        f"Tell a short tale where {f['hero'].id} must {f['quest'].verb} to bring home {f['treasure'].phrase}.",
        f'Write a child-friendly rhyming story that uses the word "{f["quest"].keyword}" and ends in a bright, brave way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    quest = _safe_fact(world, f, "quest")
    treasure = _safe_fact(world, f, "treasure")
    charm = _safe_fact(world, f, "charm")
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the {f['setting'].scape}?",
            answer=f"{hero.id} wanted to {quest.verb}, because {quest.glow} and the path looked like a tiny adventure.",
        ),
        QAItem(
            question=f"Why was the story a little suspenseful for {hero.id}?",
            answer=f"It was suspenseful because the path felt dark and unsure, and {hero.id} had to keep going even with a fluttery feeling in the chest.",
        ),
        QAItem(
            question=f"How did {charm.label} help {hero.id}?",
            answer=f"{charm.label} helped by making the way steadier and safer, so {hero.id} could keep going and bring home {treasure.phrase}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {parent.label}?",
            answer=f"It ended happily, with {hero.id} home safe, {treasure.label} kept clean, and {parent.label} smiling at the brave finish.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["quest"].keyword, "courage", "magic", world.facts["treasure"].label}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in [(n, None) for n in world.fired])}")
    return "\n".join(lines)


def explain_rejection(quest: Quest, treasure: Treasure) -> str:
    return f"(No story: {quest.verb} does not reasonably match {treasure.label} in this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "quest", None) and getattr(args, "treasure", None):
        q, t = _safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(TREASURES, getattr(args, "treasure", None))
        if (getattr(args, "quest", None), getattr(args, "treasure", None)) not in {(qid, tid) for _, qid, tid in valid_combos()}:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest, treasure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, quest=quest, treasure=treasure, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(QUESTS, params.quest), _safe_lookup(TREASURES, params.treasure), params.name, params.gender, params.parent)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("keyword", qid, q.keyword))
        for r in sorted(q.zone):
            lines.append(asp.fact("zone", qid, r))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("worn_on", tid, t.region))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
        for d in sorted(c.protects):
            lines.append(asp.fact("protects", c.id, d))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(Q, T) :- zone(Q, R), worn_on(T, R).
has_fix(Q, T) :- at_risk(Q, T), charm(C), protects(C, D), danger_of(Q, D), worn_on(T, R), covers(C, R).
valid_story(S, Q, T) :- affords(S, Q), at_risk(Q, T), has_fix(Q, T).
"""


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world of suspense, bravery, and magic in a scape.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


CURATED = [
    StoryParams(setting="moon_scape", quest="starlight", treasure="cape", name="Mira", gender="girl", parent="mother"),
    StoryParams(setting="forest_scape", quest="lantern", treasure="boots", name="Finn", gender="boy", parent="father"),
    StoryParams(setting="harbor_scape", quest="tide", treasure="boots", name="Luna", gender="girl", parent="mother"),
    StoryParams(setting="garden_scape", quest="bloom", treasure="lantern", name="Theo", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(asp.atoms(model, "valid_story"))
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
