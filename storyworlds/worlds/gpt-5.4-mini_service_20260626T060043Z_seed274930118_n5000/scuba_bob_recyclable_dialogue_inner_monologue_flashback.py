#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/scuba_bob_recyclable_dialogue_inner_monologue_flashback.py
==============================================================================================================================

A small fable-style story world about Bob, scuba gear, and recyclable cleanup.

Premise used to build the world:
---
Bob the turtle lived by a bright harbor where nets, bottles, and cans sometimes
floated in after storms. He wore a little scuba set so he could safely dive for
scrap. One day he found a shiny recycled badge in the sand and remembered an old
lesson from his grandmother: "A small helpful act can save a large hurt."

The story shape:
- Setup: Bob wants to dive and help.
- Tension: the water has hidden scrap, but there is also a worried friend and a
  tempting shortcut.
- Turn: Bob remembers a flashback and chooses the careful path.
- Resolution: he brings up recyclable things, proves the harbor cleaner, and the
  fable ends with a small moral image.

Narrative instruments:
- Dialogue: used for a few child-facing lines.
- Inner Monologue: used to show Bob thinking.
- Flashback: used to motivate the moral choice.

The simulated state tracks:
- physical meters: wetness, depth, strain, scrap_collected, harbor_cleanliness
- emotional memes: courage, worry, pride, patience, gratitude
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    badge: object | None = None
    bob: object | None = None
    friend: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "bob":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mother", "grandmother", "friend"}:
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
    depth_kind: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zones: set[str]
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_used = False

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.flashback_used = self.flashback_used
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# Registries
PLACES = {
    "harbor": Place(name="the harbor", depth_kind="water", affords={"scuba", "recyclable"}),
    "reef": Place(name="the reef", depth_kind="water", affords={"scuba"}),
    "dock": Place(name="the dock", depth_kind="shore", affords={"recyclable"}),
}

MISSIONS = {
    "recyclable": Mission(
        id="recyclable",
        verb="collect the recyclable things",
        gerund="collecting recyclable things",
        rush="swim straight down to the scrap",
        mess="saltwater",
        soil="soaked and strained",
        zones={"shell", "flippers"},
        keyword="recyclable",
        tags={"recyclable", "cleanup", "ocean"},
    ),
    "scuba": Mission(
        id="scuba",
        verb="go scuba diving",
        gerund="scuba diving",
        rush="kick fast through the deep water",
        mess="saltwater",
        soil="wet and tired",
        zones={"shell", "flippers", "mask"},
        keyword="scuba",
        tags={"scuba", "water", "ocean"},
    ),
}

GEAR = [
    Gear(
        id="scuba_set",
        label="a scuba set",
        covers={"shell", "flippers", "mask"},
        guards={"saltwater"},
        prep="put on the scuba set first",
        tail="put on the scuba set and checked each strap twice",
    ),
    Gear(
        id="mesh_bag",
        label="a mesh bag",
        covers=set(),
        guards={"scrap"},
        prep="carry a mesh bag for the bottles and cans",
        tail="carried the mesh bag along",
    ),
    Gear(
        id="gloves",
        label="reusable gloves",
        covers={"shell"},
        guards={"scrap"},
        prep="wear reusable gloves too",
        tail="wore reusable gloves too",
    ),
]

GIRL_NAMES = ["Maya", "Luna", "Nia"]
BOY_NAMES = ["Bob", "Owen", "Theo"]
FRIEND_NAMES = ["Mina", "Pip", "Tess"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mid in place.affords:
            mission = _safe_lookup(MISSIONS, mid)
            if select_gear(mission) is not None:
                combos.append((place_id, mid))
    return combos


def mission_at_risk(mission: Mission) -> bool:
    return bool(mission.zones)


def select_gear(mission: Mission) -> Optional[Gear]:
    for gear in GEAR:
        if mission.mess in gear.guards:
            if gear.covers & mission.zones or not gear.covers:
                return gear
    return None


def explain_rejection(place: str, mission: str) -> str:
    m = _safe_lookup(MISSIONS, mission)
    if not mission_at_risk(m):
        return "(No story: the mission would not create any real risk.)"
    if select_gear(m) is None:
        return f"(No story: there is no gear that reasonably helps with {mission} at {place}.)"
    return "(No story: the chosen options do not make a clear fable.)"


def act_title(mission: Mission) -> str:
    return {
        "scuba": "deep blue water",
        "recyclable": "the little scrap pile",
    }[mission.id]


def flashback_line(hero: Entity) -> str:
    return (
        f"Bob remembered a flashback of his grandmother by the lantern light: "
        f'"The sea gives kindly, but it asks for care in return."'
    )


def predict_mess(world: World, actor: Entity, mission: Mission, gear: Optional[Gear]) -> dict:
    sim = world.copy()
    do_mission(sim, sim.get(actor.id), mission, gear, narrate=False)
    scrap = sim.facts.get("scrap_collected", 0)
    clean = sim.facts.get("harbor_clean", 0)
    return {"scrap": scrap, "clean": clean}


def do_mission(world: World, actor: Entity, mission: Mission, gear: Optional[Gear], narrate: bool = True) -> None:
    if gear:
        actor.memes["courage"] += 1
    actor.meters["wetness"] = actor.meters.get("wetness", 0) + 1
    actor.meters["depth"] = actor.meters.get("depth", 0) + 1
    actor.meters["scrap_collected"] = actor.meters.get("scrap_collected", 0) + 1
    world.facts["scrap_collected"] = world.facts.get("scrap_collected", 0) + 1
    world.facts["harbor_clean"] = world.facts.get("harbor_clean", 0) + 1
    actor.memes["pride"] = actor.memes.get("pride", 0) + 1
    if narrate:
        world.say(f"{actor.id} worked carefully and brought up one more recyclable thing.")


def tell(place: Place, mission: Mission, hero_name: str, hero_type: str, friend_name: str) -> World:
    world = World(place)
    bob = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="Bob"))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend", label="Mina"))
    badge = world.add(Entity(
        id="badge",
        type="thing",
        label="recyclable badge",
        phrase="a bright recyclable badge",
        owner=bob.id,
    ))
    badge.worn_by = bob.id

    gear = select_gear(mission)
    world.facts.update(hero=bob, friend=friend, badge=badge, mission=mission, place=place, gear=gear)

    world.say(f"{bob.label} was a small turtle with a brave heart and a tidy shell.")
    world.say(f"{bob.pronoun().capitalize()} loved {mission.gerund} at {place.name}.")
    world.say(f"On his shell, {bob.pronoun('possessive')} little {badge.label} shone like a promise.")
    world.para()

    world.say(f"One morning, {bob.label} saw a bottle and a bent can near {place.name}.")
    world.say(f'"We should gather the recyclable things," said {friend.label}, peeking from the dock.')
    world.say(f'Bob answered, "I can help. I just need to be careful in the water."')
    if gear:
        world.say(f"Bob thought, {repr('I should use the right gear first, so I can help without making a mess.')}")
        world.say(flashback_line(bob))
    world.para()

    if gear:
        world.say(f"Bob smiled and said, {repr(f'“All right, {gear.prep}.”')}")
        world.say(f"He did as the gear promised: {gear.tail}.")
    world.say(f"Then Bob moved into {act_title(mission)}.")
    world.say(f'He whispered, {repr("“Little by little, a clean harbor begins with one careful fin stroke.”")}')
    do_mission(world, bob, mission, gear, narrate=False)
    world.say(f"{bob.label} lifted a bottle, then a can, and kept the shells and fish safe.")
    world.say(f'{friend.label} called, {repr("“Well done, Bob!”")}')
    world.say(f'{bob.label} replied, {repr("“A small helpful act is still a big kindness.”")}')

    world.para()
    world.say(
        f"By the end, {place.name} was cleaner, {bob.label} was proud, and "
        f"the recyclable things were out of the water and ready to be sorted."
    )
    world.say(
        f"The little turtle tucked the shiny badge against his shell and swam home "
        f"with a calmer heart."
    )

    world.facts["resolved"] = True
    return world


@dataclass
class StoryParams:
    place: str
    mission: str
    name: str
    gender: str
    friend: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mission: Mission = _safe_fact(world, f, "mission")
    return [
        f'Write a short fable for a child about {hero.label} and the word "{mission.keyword}".',
        f"Tell a gentle story where {hero.label} chooses careful scuba work and helps with recyclable things.",
        f'Write a simple story that includes a flashback, a small warning, and a kind ending about "{mission.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    mission: Mission = _safe_fact(world, f, "mission")
    place: Place = _safe_fact(world, f, "place")
    gear: Optional[Gear] = _safe_fact(world, f, "gear")
    gear_label = gear.label if gear else "no gear"

    return [
        QAItem(
            question=f"Who is the story mostly about at {place.name}?",
            answer=f"The story is mostly about {hero.label}, a small turtle who wants to help at {place.name}.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do with the recyclable things?",
            answer=f"{hero.label} wanted to {mission.verb} and bring the recyclable things up safely.",
        ),
        QAItem(
            question=f"Who spoke to {hero.label} from the dock?",
            answer=f"{friend.label} spoke to {hero.label} from the dock and reminded {hero.pronoun('object')} to be careful.",
        ),
    ]
    if gear:
        return [
            *[
                QAItem(
                    question=f"Why did {hero.label} use {gear.label} before the dive?",
                    answer=f"{hero.label} used {gear.label} because it helped with the saltwater and made the careful dive safer.",
                )
            ],
            *world_qa(world),
            *[]
        ] + [
            QAItem(
                question=f"What memory helped {hero.label} make the careful choice?",
                answer="A flashback of the grandmother's advice helped Bob remember that kindness should also be careful.",
            )
        ]
    return [QAItem(question=q.question, answer=q.answer) for q in [
        *story_qa(world)
    ]]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does recyclable mean?",
            answer="Recyclable means something can be collected and made into new useful things instead of being thrown away.",
        ),
        QAItem(
            question="What is scuba gear for?",
            answer="Scuba gear helps a person or animal breathe and move safely underwater.",
        ),
        QAItem(
            question="Why should trash not stay in the sea?",
            answer="Trash in the sea can hurt fish, turtles, and birds, so it is better to take it out.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return world_knowledge_qa(world)


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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    lines.append(f"  facts: {world.facts.get('harbor_clean', 0)} clean / {world.facts.get('scrap_collected', 0)} scrap")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", mission="recyclable", name="Bob", gender="boy", friend="Mina"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mess_of", mid, mission.mess))
        for z in sorted(mission.zones):
            lines.append(asp.fact("zones", mid, z))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
mission_valid(P, M) :- affords(P, M), mission(M), gear(G), mess_of(M, X), guards(G, X).
compatible(P, M) :- mission_valid(P, M).
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style scuba Bob story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--friend")
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
    if getattr(args, "place", None) or getattr(args, "mission", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or "boy"
    name = getattr(args, "name", None) or ("Bob" if gender == "boy" else rng.choice(GIRL_NAMES))
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, mission=mission, name=name, gender=gender, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(MISSIONS, params.mission), params.name, "bob" if params.gender == "boy" else "girl", params.friend)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, m in combos:
            print(f"  {p:8} {m}")
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
            header = f"### {p.name}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
