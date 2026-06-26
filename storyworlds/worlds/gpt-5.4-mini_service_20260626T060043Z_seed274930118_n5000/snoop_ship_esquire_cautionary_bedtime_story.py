#!/usr/bin/env python3
"""
storyworlds/worlds/snoop_ship_esquire_cautionary_bedtime_story.py
=================================================================

A small cautionary bedtime-story world about a curious snoop, a ship,
and an esquire who knows how to warn before trouble grows.

Seed tale inspiration:
- A child-like snoop keeps peeking into a moored ship at bedtime.
- An esquire notices the danger, because the ship is not a toy and the
  harbor is slippery, dark, and easy to disturb.
- The warning turns into a gentler, safer choice: look, listen, and leave
  the ship alone before a mistake wakes everyone up.

This world keeps the domain tiny and classical:
- one child explorer,
- one ship with tempting things aboard,
- one careful esquire helper,
- one cautionary turn,
- one bedtime-safe resolution.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    esquire: object | None = None
    prize: object | None = None
    ship: object | None = None
    snoop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
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
class Harbor:
    place: str = "the harbor"
    bedtime: bool = True
    docked: bool = True
    quiet: bool = True
    affordances: set[str] = field(default_factory=set)
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
class Prompt:
    id: str
    verb: str
    sneak: str
    danger: str
    risk: str
    shift: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    reason: str = ""
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    offer: str
    ending: str
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
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
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

        clone = World(self.harbor)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("snoop", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.kind != "thing" or item.worn_by != actor.id:
                continue
            if item.region not in world.zone:
                continue
            sig = ("damage", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["touched"] = item.meters.get("touched", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dusty and out of place.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.kind != "thing" or item.meters.get("dirty", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would trouble {carer.label}.")
    return out


def _r_alarm(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("alarm", 0.0) < THRESHOLD:
            continue
        sig = ("alarm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        return ["__alarm__"]
    return []


CAUSAL_RULES = [
    _r_damage,
    _r_worry,
    _r_alarm,
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
                produced.extend(s for s in sents if s != "__alarm__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(harbor: Harbor, prompt: Prompt) -> str:
    if harbor.bedtime:
        return f"The harbor was hushed, and the moon put silver on the water."
    if prompt.id == "ship":
        return "The ship waited at the dock with ropes snug and sails tucked away."
    return f"{harbor.place.capitalize()} felt still and watchful."


def build_alert(world: World, snoop: Entity, esquire: Entity, prompt: Prompt, prize: Prize) -> bool:
    sim = world.copy()
    sim.get(snoop.id).meters["snoop"] = 1.0
    sim.zone = set(prompt.risk.split(","))
    propagate(sim, narrate=False)
    if not any(e.meters.get("dirty", 0.0) >= THRESHOLD for e in sim.entities.values() if e.id == prize.id):
        return False
    world.facts["predicted"] = prize.reason
    world.say(
        f'"If you keep peeking at the {prompt.keyword}, you may get {prize.label} {prize.reason}," '
        f"{esquire.pronoun('possessive')} esquire said softly."
    )
    snoop.memes["alarm"] = snoop.memes.get("alarm", 0.0) + 1
    return True


def start_story(world: World, snoop: Entity, prompt: Prompt) -> None:
    world.say(
        f"{snoop.id} was a little {', '.join(t for t in snoop.traits if t != 'little')} {snoop.type} "
        f"who liked to {prompt.verb}."
    )
    world.say(
        f"{snoop.pronoun().capitalize()} loved the quiet night air and the shiny things near the dock."
    )


def introduce_ship(world: World, ship: Entity, prompt: Prompt) -> None:
    ship.memes["tempting"] = ship.memes.get("tempting", 0.0) + 1
    world.say(
        f"At the harbor, {ship.label} sat still under the stars, and {prompt.keyword} looked very tempting."
    )


def introduce_esquire(world: World, esquire: Entity) -> None:
    world.say(
        f"{esquire.id} was an esquire with a careful heart and a neat coat."
    )


def snoop_looks(world: World, snoop: Entity, prompt: Prompt) -> None:
    snoop.meters["snoop"] = snoop.meters.get("snoop", 0.0) + 1
    world.zone = set(prompt.risk.split(","))
    world.say(
        f"{snoop.id} wanted to {prompt.sneak}, even though {prompt.danger} by the ship was not safe."
    )
    propagate(world, narrate=True)


def warn_and_pause(world: World, esquire: Entity, snoop: Entity, prompt: Prompt, prize: Prize) -> None:
    if not build_alert(world, snoop, esquire, prompt, prize):
        return
    world.say(
        f"{snoop.id} stopped and listened, because the warning sounded true."
    )


def choose_safer_way(world: World, esquire: Entity, snoop: Entity, prompt: Prompt) -> None:
    snoop.memes["curiosity"] = max(snoop.memes.get("curiosity", 0.0), 1.0)
    snoop.memes["calm"] = snoop.memes.get("calm", 0.0) + 1
    world.say(
        f"{esquire.id} pointed to the moonlit bench and said they could watch the ship from far away instead."
    )
    world.say(
        f"{snoop.id} followed along, and the restless wanting began to quiet down."
    )


def finish(world: World, snoop: Entity, esquire: Entity, prompt: Prompt, prize: Prize) -> None:
    snoop.memes["alarm"] = 0.0
    snoop.memes["safe"] = snoop.memes.get("safe", 0.0) + 1
    world.say(
        f"In the end, {snoop.id} did not climb aboard."
    )
    world.say(
        f"{snoop.id} watched {prompt.keyword} from the bench, {prize.label} stayed safe, and the harbor grew sleepy again."
    )


def tell(harbor: Harbor, prompt: Prompt, prize_cfg: Prize,
         snoop_name: str = "Pip", snoop_type: str = "boy",
         snoop_traits: Optional[list[str]] = None) -> World:
    world = World(harbor)
    snoop = world.add(Entity(
        id=snoop_name,
        kind="character",
        type=snoop_type,
        traits=["little"] + (snoop_traits or ["curious", "restless"]),
    ))
    esquire = world.add(Entity(
        id="Esquire",
        kind="character",
        type="man",
        label="the esquire",
        traits=["calm", "careful"],
    ))
    ship = world.add(Entity(
        id="Ship",
        type="ship",
        label="the ship",
        phrase="a quiet little ship",
        owner=None,
        caretaker=esquire.id,
    ))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type="thing",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=ship.id,
        caretaker=esquire.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    start_story(world, snoop, prompt)
    introduce_ship(world, ship, prompt)
    introduce_esquire(world, esquire)
    world.para()
    snoop_looks(world, snoop, prompt)
    warn_and_pause(world, esquire, snoop, prompt, prize)
    world.para()
    choose_safer_way(world, esquire, snoop, prompt)
    finish(world, snoop, esquire, prompt, prize)

    world.facts.update(
        snoop=snoop,
        esquire=esquire,
        ship=ship,
        prize=prize,
        prompt=prompt,
        harbor=harbor,
    )
    return world


HARBORS = {
    "dock": Harbor(place="the dock", bedtime=True, affordances={"snoop", "ship"}),
    "harbor": Harbor(place="the harbor", bedtime=True, affordances={"snoop", "ship"}),
    "quay": Harbor(place="the quay", bedtime=True, affordances={"snoop", "ship"}),
}

PROMPTS = {
    "lantern": Prompt(
        id="lantern",
        verb="snoop around the lanterns",
        sneak="sneak under the rope",
        danger="the wet boards",
        risk="feet,legs",
        shift="look from the bench",
        keyword="lanterns",
        tags={"light", "night"},
    ),
    "cargo": Prompt(
        id="cargo",
        verb="peek at the cargo crates",
        sneak="slip closer to the cargo hold",
        danger="the stacked crates",
        risk="feet,legs",
        shift="watch from the bench",
        keyword="cargo",
        tags={"boxes", "night"},
    ),
    "chart": Prompt(
        id="chart",
        verb="snoop on the captain's chart",
        sneak="tiptoe toward the cabin door",
        danger="the sleeping deck",
        risk="feet,legs",
        shift="stay near the rail",
        keyword="chart",
        tags={"paper", "night"},
    ),
}

PRIZES = {
    "boots": Prize(
        id="boots",
        label="boots",
        phrase="little deck boots",
        region="feet",
        plural=True,
        reason="slippery and muddy",
    ),
    "cloak": Prize(
        id="cloak",
        label="cloak",
        phrase="a dark wool cloak",
        region="torso",
        plural=False,
        reason="damp and wrinkled",
    ),
    "gloves": Prize(
        id="gloves",
        label="gloves",
        phrase="soft captain's gloves",
        region="hands",
        plural=True,
        reason="touched and dusty",
    ),
}

GEAR = [
    Gear(
        id="bench",
        label="the bench",
        covers={"feet", "legs"},
        guards={"snoop"},
        offer="sit on the bench and watch",
        ending="sat on the bench and watched the ship sleep",
        plural=False,
    ),
    Gear(
        id="blanket",
        label="a blanket",
        covers={"torso"},
        guards={"cold", "night"},
        offer="wrap up in a blanket and listen",
        ending="wrapped up in a blanket and listened to the waves",
        plural=False,
    ),
    Gear(
        id="lamp",
        label="a small lamp",
        covers={"hands"},
        guards={"dark"},
        offer="carry a small lamp and stay back",
        ending="carried a small lamp and stayed back from the dock",
        plural=False,
    ),
]

NAMES = ["Pip", "Toby", "Milo", "Nina", "Lula", "Hugo", "Etta", "June"]
TRAITS = ["curious", "brave", "sleepy", "thoughtful", "mischievous", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, harbor in HARBORS.items():
        for prompt in PROMPTS:
            for prize_id, prize in PRIZES.items():
                if harbor.bedtime and prompt in {"lantern", "cargo", "chart"} and prize.region in {"feet", "torso", "hands"}:
                    combos.append((place, prompt, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    prompt: str
    prize: str
    name: str
    gender: str
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


KNOWLEDGE = {
    "ship": [("What is a ship?", "A ship is a big boat that can carry people and things over water.")],
    "harbor": [("What is a harbor?", "A harbor is a safe place where boats and ships can rest near land.")],
    "lantern": [("What is a lantern?", "A lantern is a light you can carry or hang up so you can see in the dark.")],
    "cargo": [("What is cargo?", "Cargo is the things a ship carries, like boxes, bags, or supplies.")],
    "chart": [("What is a chart?", "A chart is a map for the water that helps sailors find their way.")],
    "bedtime": [("Why is bedtime a quiet time?", "Bedtime is quiet so bodies and minds can rest and get ready to sleep.")],
    "snoop": [("What does it mean to snoop?", "To snoop means to look around in a nosy way when you should be careful or keep out.")],
    "esquire": [("What is an esquire?", "An esquire is a polite title for a careful gentleman, often someone who helps and speaks with good manners.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snoop = _safe_fact(world, f, "snoop")
    prompt = _safe_fact(world, f, "prompt")
    return [
        f'Write a gentle bedtime cautionary story about {snoop.id} the {snoop.type}, a ship, and an esquire.',
        f"Tell a short story for a young child where {snoop.id} wants to {prompt.verb} but a careful esquire helps {snoop.id} choose a safer way.",
        f'Write a bedtime story that includes the words "snoop", "ship", and "esquire" and ends calmly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    snoop = _safe_fact(world, f, "snoop")
    esquire = _safe_fact(world, f, "esquire")
    prompt = _safe_fact(world, f, "prompt")
    prize = _safe_fact(world, f, "prize")
    harbor = _safe_fact(world, f, "harbor")
    qa = [
        QAItem(
            question=f"Who was the story about at {harbor.place}?",
            answer=f"It was about {snoop.id}, a little {snoop.type}, and the careful esquire who watched over the ship.",
        ),
        QAItem(
            question=f"What did {snoop.id} want to do near the ship?",
            answer=f"{snoop.id} wanted to {prompt.verb}, even though that was not safe at bedtime.",
        ),
        QAItem(
            question=f"Why did the esquire warn {snoop.id}?",
            answer=f"The esquire warned {snoop.id} because the {prompt.keyword} and the dark dock could lead to trouble, and {prize.label} might get {prize.reason}.",
        ),
        QAItem(
            question=f"What safer choice did the esquire offer?",
            answer=f"The esquire offered a calmer choice: watch from the bench instead of sneaking onto the ship.",
        ),
        QAItem(
            question=f"How did the story end for {snoop.id} and the ship?",
            answer=f"It ended quietly, with {snoop.id} staying off the ship, the {prize.label} staying safe, and the harbor getting sleepy again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["prompt"].tags)
    tags.add("ship")
    tags.add("esquire")
    tags.add("bedtime")
    out: list[QAItem] = []
    for key in ["ship", "harbor", "lantern", "cargo", "chart", "bedtime", "snoop", "esquire"]:
        if key in tags or key in {"ship", "harbor", "bedtime", "snoop", "esquire"}:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        parts = [f"type={e.type}"]
        if e.label:
            parts.append(f"label={e.label}")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: " + " ".join(parts))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="dock", prompt="lantern", prize="boots", name="Pip", gender="boy", trait="curious"),
    StoryParams(place="harbor", prompt="cargo", prize="cloak", name="Nina", gender="girl", trait="sleepy"),
    StoryParams(place="quay", prompt="chart", prize="gloves", name="Milo", gender="boy", trait="mischievous"),
]


ASP_RULES = r"""
% Facts provide place/prompt/prize registries.
% A story is valid when the prompt is a bedtime cautionary snoop at a ship,
% and the prize at risk is something the warning can honestly mention.

at_risk(P, S) :- prompt(P), prize(S), region(S, feet), risk_zone(P, feet).
at_risk(P, S) :- prompt(P), prize(S), region(S, legs), risk_zone(P, legs).
at_risk(P, S) :- prompt(P), prize(S), region(S, torso), risk_zone(P, torso).
at_risk(P, S) :- prompt(P), prize(S), region(S, hands), risk_zone(P, hands).

valid_story(Place, Prompt, Prize) :- harbor(Place), bedtime(Place), prompt(Prompt), prize(Prize), at_risk(Prompt, Prize).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, h in HARBORS.items():
        lines.append(asp.fact("harbor", pid))
        if h.bedtime:
            lines.append(asp.fact("bedtime", pid))
        for a in sorted(h.affordances):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PROMPTS.items():
        lines.append(asp.fact("prompt", pid))
        lines.append(asp.fact("keyword", pid, p.keyword))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
        for region in sorted({x.strip() for x in p.risk.split(",")}):
            lines.append(asp.fact("risk_zone", pid, region))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("plural", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="Cautionary bedtime story world about snooping near a ship.")
    ap.add_argument("--place", choices=HARBORS)
    ap.add_argument("--prompt", choices=PROMPTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "prompt", None) is None or c[1] == getattr(args, "prompt", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prompt, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, prompt=prompt, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(HARBORS, params.place), _safe_lookup(PROMPTS, params.prompt), _safe_lookup(PRIZES, params.prize), params.name, params.gender, [params.trait, "little"])
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, prompt, prize) combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.prompt} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
