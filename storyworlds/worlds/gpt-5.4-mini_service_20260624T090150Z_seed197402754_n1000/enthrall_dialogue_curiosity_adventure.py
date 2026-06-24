#!/usr/bin/env python3
"""
storyworlds/worlds/enthrall_dialogue_curiosity_adventure.py
===========================================================

A small adventure storyworld about a curious child, a tempting mystery, and a
dialogue that turns risk into a safer path.

The core premise:
- A child is enthralled by a strange clue in a small adventure setting.
- Curiosity pushes toward a risky choice.
- A companion or parent answers with calm dialogue.
- The world turns on a practical fix: a lantern, a rope, a map, a bridge, or
  another simple aid that keeps the adventure going safely.

This is a standalone storyworld script under the Storyweavers contract.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    aid: object | None = None
    hero: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "dark": 0.0, "lost": 0.0, "wet": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "joy": 0.0, "fear": 0.0, "trust": 0.0, "enthralled": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    outdoor: bool = True
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
class Adventure:
    id: str
    clue: str
    lure: str
    rush: str
    hazard: str
    risk: str
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
class Aid:
    id: str
    label: str
    covers: set[str]
    protects: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        for adv in world.facts.get("adventures", []):
            if actor.meters[adv.hazard] < THRESHOLD:
                continue
            if actor.meters["risk"] < THRESHOLD:
                continue
            sig = ("risk", actor.id, adv.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["fear"] += 1
            out.append(f"The path ahead looked risky.")
    return out


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        sig = ("wet", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        out.append(f"Cold drops clung to {actor.pronoun('possessive')} clothes.")
    return out


CAUSAL_RULES = [
    _r_risk,
    _r_wet,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def adventure_at_risk(adventure: Adventure) -> bool:
    return bool(adventure.zone)


def select_aid(adventure: Adventure) -> Optional[Aid]:
    for aid in AIDS:
        if adventure.hazard in aid.protects and adventure.zone & aid.covers:
            return aid
    return None


def predict_danger(world: World, actor: Entity, adventure: Adventure) -> dict:
    sim = world.copy()
    _do_adventure(sim, sim.get(actor.id), adventure, narrate=False)
    return {
        "risk": sim.get(actor.id).meters["risk"],
        "fear": sim.get(actor.id).memes["fear"],
    }


def _do_adventure(world: World, actor: Entity, adventure: Adventure, narrate: bool = True) -> None:
    if adventure.id not in world.setting.affords:
        return
    world.zone = set(adventure.zone)
    actor.meters["risk"] += 1
    actor.meters[adventure.hazard] += 1
    actor.memes["curiosity"] += 1
    actor.memes["enthralled"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, adventure: Adventure) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'curious')} {hero.type} "
        f"who loved adventure stories and every new clue."
    )
    world.say(
        f"One tiny clue could enthrall {hero.pronoun('object')} faster than a singing bird: {adventure.clue}."
    )


def desire(world: World, hero: Entity, adventure: Adventure) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["enthralled"] += 1
    world.say(
        f"{hero.id} wanted to follow the clue right away, because curiosity kept tugging at {hero.pronoun('possessive')} sleeves."
    )


def dialogue_warning(world: World, parent: Entity, hero: Entity, adventure: Adventure, danger_word: str) -> bool:
    pred = predict_danger(world, hero, adventure)
    if pred["risk"] < THRESHOLD and pred["fear"] < THRESHOLD:
        return False
    world.facts["predicted_danger"] = danger_word
    world.say(
        f'"Wait," {parent.id} said. "That path looks like it could end in {danger_word}. Let\'s think first."'
    )
    return True


def impulsive_step(world: World, hero: Entity, adventure: Adventure) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["fear"] += 0.5
    world.say(f"{hero.id} still peered forward and tried to {adventure.rush}.")
    if adventure.hazard == "dark":
        world.say("The shade ahead made the trail feel longer than it was.")


def guide_dialogue(world: World, parent: Entity, hero: Entity, adventure: Adventure) -> None:
    hero.memes["trust"] += 1
    world.say(
        f'But {parent.id} stepped beside {hero.pronoun("object")} and said, '
        f'"You can be curious and still be safe. We can take a better way."'
    )


def compromise(world: World, parent: Entity, hero: Entity, adventure: Adventure) -> Optional[Aid]:
    aid_def = select_aid(adventure)
    if aid_def is None:
        return None
    aid = world.add(Entity(
        id=aid_def.id,
        type="aid",
        label=aid_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(aid_def.covers),
        plural=aid_def.plural,
    ))
    aid.worn_by = hero.id
    if predict_danger(world, hero, adventure)["risk"] >= THRESHOLD and adventure.hazard not in aid_def.protects:
        aid.worn_by = None
        del world.entities[aid.id]
        return None
    world.say(
        f'{parent.id} picked up {aid_def.label} and said, "{aid_def.prep} first, then we can keep going."'
    )
    return aid_def


def resolution(world: World, parent: Entity, hero: Entity, adventure: Adventure, aid_def: Aid) -> None:
    hero.memes["joy"] += 1
    hero.memes["fear"] = 0.0
    world.say(
        f"{hero.id} nodded, and soon {hero.id} was safe enough to keep the adventure going."
    )
    world.say(
        f"They {aid_def.tail}. In the end, {hero.id} was still enthralled, but now the clue led to a brave little finish."
    )


def tell(
    setting: Setting,
    adventure: Adventure,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious", "brave"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.facts["adventures"] = [adventure]

    opening(world, hero, adventure)
    world.para()
    desire(world, hero, adventure)
    dialogue_warning(world, parent, hero, adventure, adventure.risk)
    impulsive_step(world, hero, adventure)
    guide_dialogue(world, parent, hero, adventure)
    world.para()
    aid_def = compromise(world, parent, hero, adventure)
    if aid_def:
        resolution(world, parent, hero, adventure, aid_def)

    world.facts.update(hero=hero, parent=parent, adventure=adventure, aid=aid_def)
    return world


SETTINGS = {
    "wood": Setting(place="the wood trail", outdoor=True, affords={"glow", "bridge", "cave"}),
    "river": Setting(place="the river path", outdoor=True, affords={"bridge", "glow"}),
    "garden": Setting(place="the garden gate", outdoor=True, affords={"glow"}),
    "attic": Setting(place="the attic stairs", outdoor=False, affords={"box"}),
}

ADVENTURES = {
    "glow": Adventure(
        id="glow",
        clue="a glowing pebble near the path",
        lure="follow the glow",
        rush="run toward the glow",
        hazard="dark",
        risk="darkness",
        zone={"eyes", "feet"},
        keyword="glow",
        tags={"dark", "light", "curiosity"},
    ),
    "bridge": Adventure(
        id="bridge",
        clue="a wobbly little bridge over the stream",
        lure="cross the bridge",
        rush="dash across the bridge",
        hazard="wet",
        risk="the water",
        zone={"feet", "legs"},
        keyword="bridge",
        tags={"water", "wet", "adventure"},
    ),
    "cave": Adventure(
        id="cave",
        clue="a cave opening shaped like a sleeping mouth",
        lure="peek into the cave",
        rush="sneak into the cave",
        hazard="dark",
        risk="getting lost in the dark",
        zone={"eyes", "feet"},
        keyword="cave",
        tags={"dark", "echo", "curiosity"},
    ),
    "box": Adventure(
        id="box",
        clue="a dusty box with a gold latch",
        lure="open the box",
        rush="pull open the box",
        hazard="dusty",
        risk="a dusty sneeze",
        zone={"hands", "nose"},
        keyword="box",
        tags={"dust", "secret", "curiosity"},
    ),
}

AIDS = [
    Aid(
        id="lantern",
        label="a little lantern",
        covers={"eyes", "feet"},
        protects={"dark"},
        prep="take a little lantern",
        tail="walked on with the lantern glowing warmly",
    ),
    Aid(
        id="boots",
        label="rain boots",
        covers={"feet", "legs"},
        protects={"wet"},
        prep="put on rain boots",
        tail="crossed the wet patch with dry feet",
        plural=True,
    ),
    Aid(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        protects={"dusty"},
        prep="wear soft gloves",
        tail="opened the box without getting dusty hands",
        plural=True,
    ),
]

TRAITS = ["curious", "spirited", "cheerful", "bold", "lively"]
GIRL_NAMES = ["Mina", "Lila", "Zoe", "Nora", "Ava"]
BOY_NAMES = ["Timo", "Noel", "Ben", "Leo", "Max"]


@dataclass
class StoryParams:
    place: str
    adventure: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for adv_id in setting.affords:
            if select_aid(_safe_lookup(ADVENTURES, adv_id)) is not None:
                combos.append((place, adv_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, adv = f["hero"], f["parent"], f["adventure"]
    return [
        f'Write a short adventure story for a young child using the word "enthrall" and a gentle dialogue scene.',
        f"Tell a curious adventure where {hero.id} wants to {adv.lure} but {parent.id} speaks up and helps with a safer plan.",
        f"Write a child-friendly story with a clue, a warning, and a brave helper at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, adv = f["hero"], f["parent"], f["adventure"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type} who loves curiosity, dialogue, and adventure.",
        ),
        QAItem(
            question=f"What clue tried to enthrall {hero.id}?",
            answer=f"The clue was {adv.clue}. It made {hero.id} want to follow it right away.",
        ),
        QAItem(
            question=f"What did {parent.id} say when the path looked risky?",
            answer=f"{parent.id} said to wait, think first, and choose a safer way before going farther.",
        ),
    ]
    if f.get("aid"):
        aid = _safe_fact(world, f, "aid")
        qa.append(
            QAItem(
                question=f"How did {aid.label} help the adventure?",
                answer=f"{aid.label.capitalize()} helped by protecting the risky part of the adventure so {hero.id} could keep going safely.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt happy and still enthralled, because the adventure stayed exciting but became safe enough to finish.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["adventure"].tags)
    if f.get("aid"):
        tags.add(f["aid"].id)
    out: list[QAItem] = []
    knowledge = {
        "curiosity": [
            ("What is curiosity?", "Curiosity is the wish to learn about something new or interesting."),
        ],
        "dark": [
            ("Why can the dark feel scary?", "The dark can feel scary because it is harder to see what is around you."),
        ],
        "light": [
            ("What does a lantern do?", "A lantern gives off light so people can see in the dark."),
        ],
        "water": [
            ("Why do rain boots help on wet ground?", "Rain boots help because they keep feet dry on wet ground."),
        ],
        "dust": [
            ("Why wear gloves when something is dusty?", "Gloves help keep dust off your hands when you touch old things."),
        ],
        "adventure": [
            ("What is an adventure?", "An adventure is an exciting trip or experience, often with a new place to explore."),
        ],
        "secret": [
            ("What is a secret box?", "A secret box is a box that keeps something hidden until someone opens it."),
        ],
    }
    for tag, items in knowledge.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="wood", adventure="glow", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="river", adventure="bridge", name="Leo", gender="boy", parent="father", trait="bold"),
    StoryParams(place="wood", adventure="cave", name="Ava", gender="girl", parent="mother", trait="spirited"),
]


def explain_rejection(adventure: Adventure) -> str:
    return f"(No story: {adventure.lure} does not have a matching safe aid in this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with curiosity, dialogue, and a gentle turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--adventure", choices=ADVENTURES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "adventure", None):
        adv = _safe_lookup(ADVENTURES, getattr(args, "adventure", None))
        if getattr(args, "place", None) not in SETTINGS or getattr(args, "adventure", None) not in _safe_lookup(SETTINGS, getattr(args, "place", None)).affords:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "adventure", None) is None or c[1] == getattr(args, "adventure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, adventure = rng.choice(list(combos))
    adv = _safe_lookup(ADVENTURES, adventure)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, adventure=adventure, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ADVENTURES, params.adventure), params.name, params.gender, [params.trait], params.parent)
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


ASP_RULES = r"""
adventure_place(P,A) :- affords(P,A).
safe_aid(Aid,A) :- adventure(A), hazard_of(A,H), protects(Aid,H), covers(Aid,R), zone_of(A,R).
valid_story(P,A) :- adventure_place(P,A), safe_aid(_,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ADVENTURES.items():
        lines.append(asp.fact("adventure", aid))
        lines.append(asp.fact("hazard_of", aid, a.hazard))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone_of", aid, r))
    for g in AIDS:
        lines.append(asp.fact("aid", g.id))
        for h in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, h))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(p, a) for p, a in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, adventure) combos:")
        for p, a in triples:
            print(f"  {p:8} {a}")
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
            header = f"### {p.name}: {p.adventure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
