#!/usr/bin/env python3
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

    cape: object | None = None
    cigarette: object | None = None
    guide: object | None = None
    lord: object | None = None
    mask: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"lord", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"lady", "woman", "girl"}:
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
class Setting:
    place: str
    indoors: bool = False
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
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    protective: bool = False
    plural: bool = False
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
class Event:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraph_breaks: list[int] = []
        self.zone: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        for item in self.worn_items(actor):
            if getattr(item, "protective", False) and region in getattr(item, "covers", set()):
                return True
        return False

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and (not self.paragraph_breaks or self.paragraph_breaks[-1] != len(self.lines)):
            self.paragraph_breaks.append(len(self.lines))

    def render(self) -> str:
        if not self.lines:
            return ""
        breaks = set(self.paragraph_breaks)
        out: list[str] = []
        start = 0
        for i in range(len(self.lines) + 1):
            if i in breaks or i == len(self.lines):
                chunk = " ".join(self.lines[start:i]).strip()
                if chunk:
                    out.append(chunk)
                start = i
        return "\n\n".join(out)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("smoke", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["soot"] = item.meters.get("soot", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got a little sooty.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would give {carer.label} more work.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("blocked", 0.0) < THRESHOLD or actor.memes.get("want", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_r_soil, _r_worry, _r_conflict):
            res = fn(world)
            if res:
                changed = True
                produced.extend([s for s in res if s != "__conflict__"])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_event(world: World, actor: Entity, event: Event, narrate: bool = True) -> None:
    world.zone = set(event.zone)
    actor.meters[event.mess] = actor.meters.get(event.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def predict(world: World, actor: Entity, event: Event, item_id: str) -> dict:
    sim = world.copy()
    _do_event(sim, sim.get(actor.id), event, narrate=False)
    item = sim.entities[item_id]
    return {"soiled": item.meters.get("dirty", 0.0) >= THRESHOLD}


SETTINGS = {
    "starport": Setting(place="the starport"),
    "moon_deck": Setting(place="the moon deck"),
}

EVENTS = {
    "twist": Event(
        id="twist",
        verb="twist the ship around",
        gerund="twisting through the stars",
        rush="spin the ship faster",
        mess="smoke",
        soil="smoky",
        zone={"torso"},
        keyword="Twist",
        tags={"twist", "space"},
    ),
    "quest": Event(
        id="quest",
        verb="go on the quest",
        gerund="questing across the deck",
        rush="dash after the clue",
        mess="smoke",
        soil="smoky",
        zone={"torso"},
        keyword="Quest",
        tags={"quest", "space"},
    ),
    "rhyme": Event(
        id="rhyme",
        verb="chant a rhyme",
        gerund="rhyming in a low sing-song",
        rush="shout the rhyme louder",
        mess="smoke",
        soil="smoky",
        zone={"torso"},
        keyword="Rhyme",
        tags={"rhyme", "space"},
    ),
}

ITEMS = {
    "cape": Item(
        id="cape",
        label="silver cape",
        phrase="a silver cape with a bright clasp",
        region="torso",
        guards={"smoke"},
        covers={"torso"},
        protective=True,
    ),
    "mask": Item(
        id="mask",
        label="breath mask",
        phrase="a small breath mask",
        region="torso",
        guards={"smoke"},
        covers={"torso"},
        protective=True,
    ),
    "case": Item(
        id="case",
        label="cigarette case",
        phrase="a tiny cigarette case",
        region="torso",
        guards=set(),
        covers=set(),
        protective=False,
    ),
}

GALLERY = ["Lord Orion", "Lord Vale", "Lord Nestor", "Lord Paxon"]
TRAITS = ["brave", "curious", "gentle", "cheerful"]


@dataclass
class StoryParams:
    place: str
    event: str
    item: str
    name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with a lord, a challenge, and a cigarette.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def reason_check(event: Event, item: Item) -> bool:
    return item.region in event.zone and "smoke" in event.mess or item.id == "case"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "event", None) and getattr(args, "item", None):
        if not reason_check(_safe_lookup(EVENTS, getattr(args, "event", None)), _safe_lookup(ITEMS, getattr(args, "item", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    places = [p for p in SETTINGS if getattr(args, "place", None) is None or p == getattr(args, "place", None)]
    events = [e for e in EVENTS if getattr(args, "event", None) is None or e == getattr(args, "event", None)]
    items = [i for i in ITEMS if getattr(args, "item", None) is None or i == getattr(args, "item", None)]
    combos = [(p, e, i) for p in places for e in events for i in items if reason_check(_safe_lookup(EVENTS, e), _safe_lookup(ITEMS, i))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event, item = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GALLERY)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, item=item, name=name, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    lord = world.add(Entity(id=params.name, kind="character", type="lord", label=params.name))
    guide = world.add(Entity(id="Guide", kind="character", type="captain", label="the captain"))
    cigarette = world.add(Entity(
        id="cigarette",
        type="cigarette",
        label="cigarette",
        phrase="a small cigarette in a sealed case",
        owner=lord.id,
        caretaker=guide.id,
        worn_by=lord.id,
    ))
    world.facts.update(hero=lord, guide=guide, cigarette=cigarette, event=_safe_lookup(EVENTS, params.event), item=_safe_lookup(ITEMS, params.item), params=params)

    world.say(f"{params.name} was a {params.trait} lord aboard {world.setting.place}.")
    world.say(f"He kept a cigarette in a little case, and the case looked far too important to lose.")

    world.para()
    world.say(f"One day, the ship faced a {params.event.capitalize()} challenge near the stars.")
    world.say(f"{params.name} wanted to {_safe_lookup(EVENTS, params.event).verb}, but a thin puff of smoke curled into the air.")
    if params.item == "case":
        world.say("The cigarette case had slipped open just enough to make the deck smell smoky.")
    else:
        world.say("The cigarette was close enough to the vents that everyone noticed it at once.")
    world.say(f"The captain frowned, because smoky air on a space deck was a real problem.")

    world.para()
    lord.memes["want"] = 1
    lord.memes["blocked"] = 1
    lord.meters["smoke"] = 1
    predict(world, lord, _safe_lookup(EVENTS, params.event), cigarette.id)
    world.say(f"{params.name} tried to {_safe_lookup(EVENTS, params.event).rush}, but the captain raised a hand and said, 'Not with smoke in the air.'")
    world.say(f"{params.name} felt stuck for a moment, then remembered the old {_safe_lookup(EVENTS, params.event).keyword} rhyme the crew used when things went wrong.")
    world.say(f'"First the twist, then the quest, then the rhyme," he whispered.')

    world.para()
    world.say(f"Together they found a silver cape and a breath mask.")
    cape = world.add(Entity(id="cape", type="gear", label="silver cape", phrase="a silver cape", owner=lord.id, caretaker=guide.id, worn_by=lord.id))
    cape.protective = True
    cape.meters["clean"] = 1
    mask = world.add(Entity(id="mask", type="gear", label="breath mask", phrase="a breath mask", owner=lord.id, caretaker=guide.id, worn_by=lord.id))
    mask.protective = True
    mask.meters["clean"] = 1
    world.say(f"{params.name} put on the mask, and the cape kept his chest safe while the crew opened the vents.")
    world.say(f"Then the captain moved the cigarette to a safe case, and the smoky puff drifted away into space.")

    world.para()
    lord.memes["blocked"] = 0
    lord.memes["joy"] = lord.memes.get("joy", 0) + 1
    world.say(f"At last, {params.name} could {_safe_lookup(EVENTS, params.event).gerund} without worry.")
    world.say(f"The starport looked bright again, the cigarette stayed safely packed away, and the lord smiled at the quiet sky.")
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, e, i) for p in SETTINGS for e in EVENTS for i in ITEMS if reason_check(_safe_lookup(EVENTS, e), _safe_lookup(ITEMS, i))]


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    e = _safe_fact(world, world.facts, "event")
    return [
        f"Write a small space adventure story about a lord named {p.name} and a {e.keyword} challenge.",
        f"Tell a child-friendly tale where a cigarette causes trouble on a space deck and the crew finds a safe fix.",
        f"Write a story with Twist, Quest, and Rhyme in it, where a lord learns how to handle a smoky problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    e = _safe_fact(world, world.facts, "event")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.name}, a {p.trait} lord on {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the challenge on the ship?",
            answer=f"The challenge was a smoky space problem caused by the cigarette and the open air on the deck.",
        ),
        QAItem(
            question=f"How did the lord fix the problem?",
            answer=f"He used a silver cape and a breath mask, and the crew safely packed the cigarette away before he continued the {e.keyword} adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to find something important or solve a problem.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words that sound alike at the end, which can make a line easy to remember.",
        ),
        QAItem(
            question="What does a twist mean in a space story?",
            answer="A twist can mean a quick turn or a surprising change in what is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if getattr(e, "protective", False):
            bits.append("protective=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for e in EVENTS.values():
        lines.append(asp.fact("event", e.id))
        lines.append(asp.fact("mess", e.id, e.mess))
        for z in sorted(e.zone):
            lines.append(asp.fact("zone", e.id, z))
    for i in ITEMS.values():
        lines.append(asp.fact("item", i.id))
        lines.append(asp.fact("item_region", i.id, i.region))
        if i.protective:
            lines.append(asp.fact("protective", i.id))
        for c in sorted(i.covers):
            lines.append(asp.fact("covers", i.id, c))
        for g in sorted(i.guards):
            lines.append(asp.fact("guards", i.id, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,E,I) :- setting(P), event(E), item(I), zone(E,R), item_region(I,R), guards(I,smoke).
"""

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
    StoryParams(place="starport", event="twist", item="case", name="Lord Orion", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
