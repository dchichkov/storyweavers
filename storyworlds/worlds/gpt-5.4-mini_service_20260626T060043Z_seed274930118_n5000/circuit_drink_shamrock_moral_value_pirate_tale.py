#!/usr/bin/env python3
"""
storyworlds/worlds/circuit_drink_shamrock_moral_value_pirate_tale.py
=====================================================================

A standalone story world for a pirate-tale domain with a small simulated moral
choice: a child pirate wants a drink, a shamrock charm matters, and a circuit
device can help or fail depending on how it is used.

The story model is built from a short seed-tale premise:

A young pirate aboard a little ship finds a lucky shamrock charm and a tin cup
of drink. When the ship's lantern circuit shorts out, the crew can either grab
the drink for themselves or share it to help cool and clean the warm contacts.
The pirate chooses the fair, careful path, and the ship lights again.

World dynamics:
- Physical meters: spill, heat, soot, charge, thirst
- Emotional memes: greed, worry, trust, pride, relief, gratitude
- Moral value is tracked as a concrete score that rises when the pirate shares,
  tells the truth, or helps the crew, and falls when the pirate hides, hoards,
  or ignores a duty.

The domain keeps the "pirate tale" tone: ship, deck, lantern, captain, cabin,
and treasure-like charm vocabulary appear in the prose, but the story remains
child-facing and grounded in state changes.
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
    kind: str = "thing"  # character | thing
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
    tags: set[str] = field(default_factory=set)

    region: object | None = None
    captain: object | None = None
    drink: object | None = None
    hero: object | None = None
    lantern: object | None = None
    prize: object | None = None
    shamrock: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "captain"}
        if self.type in female and self.type not in {"pirate"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male or self.type == "pirate":
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
class ShipSetting:
    place: str = "the little ship"
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
class Activity:
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


@dataclass
class Prize:
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


class World:
    def __init__(self, setting: ShipSetting) -> None:
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in getattr(e, "covers", set()) for e in self.worn_items(actor))

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


def _entity_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _entity_memes(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _r_leak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if _entity_meter(actor, "spill") < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.owner != actor.id:
                continue
            if item.label in {"cloak", "coat"} and "torso" not in world.zone:
                continue
            sig = ("leak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["soot"] = item.meters.get("soot", 0.0) + 1
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got damp from the spill.")
    return out


def _r_moral(world: World) -> list[str]:
    out = []
    pirate = world.get("hero")
    if pirate.memes.get("share", 0.0) >= THRESHOLD and pirate.memes.get("truth", 0.0) >= THRESHOLD:
        sig = ("moral_up", pirate.id)
        if sig not in world.fired:
            world.fired.add(sig)
            pirate.meters["moral"] = pirate.meters.get("moral", 0.0) + 2
            pirate.memes["trust"] = pirate.memes.get("trust", 0.0) + 1
            out.append("The crew could see the good choice growing strong.")
    if pirate.memes.get("greed", 0.0) >= THRESHOLD:
        sig = ("moral_down", pirate.id)
        if sig not in world.fired:
            world.fired.add(sig)
            pirate.meters["moral"] = pirate.meters.get("moral", 0.0) - 1
            pirate.memes["worry"] = pirate.memes.get("worry", 0.0) + 1
            out.append("The pirate's selfish thought made the air feel heavy.")
    return out


def _r_charge(world: World) -> list[str]:
    lantern = world.get("lantern")
    if lantern.meters.get("charge", 0.0) >= THRESHOLD and lantern.meters.get("heat", 0.0) < 1:
        sig = ("bright",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["lantern_lit"] = True
            return ["The lantern glowed bright again."]
    return []


CAUSAL_RULES = [
    _r_leak,
    _r_moral,
    _r_charge,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("wet", 0.0) >= THRESHOLD),
        "moral": sim.get("hero").meters.get("moral", 0.0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    if activity.id == "drink":
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    if activity.id == "circuit":
        actor.meters["charge"] = actor.meters.get("charge", 0.0) + 1
        actor.meters["heat"] = actor.meters.get("heat", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.label.capitalize()} was a little pirate who liked shiny things, tidy decks, and brave promises."
    )


def loves_things(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to {activity.verb} when the sea wind was soft."
    )


def arrive(world: World, hero: Entity, captain: Entity, setting: ShipSetting) -> None:
    world.say(
        f"One dusk, {hero.label} and {hero.pronoun('possessive')} {captain.label} stood on {setting.place} by the lantern cabin."
    )


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.label} wanted to {activity.verb}, but {hero.pronoun('possessive')} eyes kept drifting to {prize.phrase}."
    )


def warn(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted"] = "wet and sticky"
    world.say(
        f'"If ye go at that circuit now, the {prize.label} may get {activity.soil}," '
        f"{captain.label} said. \"And the lantern may fail.\""
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["greed"] = hero.memes.get("greed", 0.0) + 1
    world.say(f"Still, {hero.label} reached for the {activity.keyword} gear with a stubborn grin.")


def choice(world: World, hero: Entity, captain: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["truth"] = hero.memes.get("truth", 0.0) + 1
    hero.memes["share"] = hero.memes.get("share", 0.0) + 1
    hero.meters["moral"] = hero.meters.get("moral", 0.0) + 2
    world.say(
        f"{hero.label} admitted {hero.pronoun('possessive')} mistake and offered to share the drink with the crew."
    )
    world.say(
        f"That kind act cooled the hot circuit, and the {prize.label} stayed safe."
    )


def resolve(world: World, hero: Entity, captain: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    captain.memes["gratitude"] = captain.memes.get("gratitude", 0.0) + 1
    world.say(
        f"At last the lantern blinked awake, the deck shone soft gold, and the shamrock charm bobbed at {hero.pronoun('possessive')} neck like a tiny green flag."
    )


def tell(setting: ShipSetting, activity: Activity, prize_cfg: Prize, hero_name: str = "Pip", hero_type: str = "pirate",
         parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    captain = world.add(Entity(id="captain", kind="character", type=parent_type, label="Captain Moira"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=captain.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", protective=False))
    shamrock = world.add(Entity(id="shamrock", type="charm", label="shamrock charm", phrase="a little shamrock charm"))
    drink = world.add(Entity(id="drink", type="cup", label="drink cup", phrase="a tin cup of sweet drink"))

    shamrock.worn_by = hero.id
    drink.owner = hero.id

    introduce(world, hero)
    loves_things(world, hero, activity)
    world.say(f"{hero.label} wore a shamrock charm and guarded a small drink for later.")
    world.say(f"The ship's lantern circuit hummed in the dark like a sleepy snake.")
    world.para()
    arrive(world, hero, captain, setting)
    wants(world, hero, activity, prize)
    warn(world, captain, hero, activity, prize)
    defies(world, hero, activity)
    world.say(f"{hero.label} looked at the circuit again, then at the drink, and finally at {captain.label}.")
    world.para()
    choice(world, hero, captain, activity, prize)
    activity_res = _do_activity(world, hero, activity, narrate=True)
    world.facts.update(
        hero=hero,
        captain=captain,
        prize=prize,
        activity=activity,
        setting=setting,
        shamrock=shamrock,
        drink=drink,
        lantern=lantern,
    )
    resolve(world, hero, captain, activity, prize)
    world.facts["moral_value"] = hero.meters.get("moral", 0.0)
    world.facts["activity_result"] = activity_res
    return world


SETTINGS = {
    "ship": ShipSetting(place="the little ship", affords={"circuit", "drink"}),
    "harbor": ShipSetting(place="the harbor dock", affords={"drink", "circuit"}),
    "cabin": ShipSetting(place="the lantern cabin", affords={"circuit", "drink"}),
}

ACTIVITIES = {
    "circuit": Activity(
        id="circuit",
        verb="fix the circuit",
        gerund="fixing the circuit",
        rush="dash at the lantern wires",
        mess="heat",
        soil="warm and smoky",
        zone={"torso"},
        keyword="circuit",
        tags={"circuit", "light"},
    ),
    "drink": Activity(
        id="drink",
        verb="sip the drink",
        gerund="drinking sweet juice",
        rush="grab the cup",
        mess="spill",
        soil="spilled",
        zone={"torso"},
        keyword="drink",
        tags={"drink", "share"},
    ),
}

PRIZES = {
    "coat": Prize(
        label="coat",
        phrase="a captain's coat with brass buttons",
        type="coat",
        region="torso",
    ),
    "map": Prize(
        label="map",
        phrase="a folded treasure map",
        type="map",
        region="torso",
    ),
    "hat": Prize(
        label="hat",
        phrase="a floppy pirate hat",
        type="hat",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="cloth",
        label="a clean cloth",
        covers={"torso"},
        guards={"spill", "heat"},
        prep="wrap the warm wires with a clean cloth",
        tail="wrapped the wires with a clean cloth",
    ),
    Gear(
        id="cup",
        label="a covered cup",
        covers={"torso"},
        guards={"spill"},
        prep="carry the drink in a covered cup",
        tail="carried the drink in a covered cup",
    ),
    Gear(
        id="shamrock_wrap",
        label="a shamrock-wrapped pad",
        covers={"torso"},
        guards={"heat", "spill"},
        prep="use the shamrock-wrapped pad on the hot part",
        tail="used the shamrock-wrapped pad",
    ),
]

GIRL_NAMES = ["Moira", "Nell", "Mina", "Ruth", "Ivy"]
BOY_NAMES = ["Pip", "Ned", "Finn", "Jory", "Tad"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, captain, act, prize = f["hero"], f["captain"], f["activity"], f["prize"]
    return [
        f'Write a short pirate tale for a child about a {hero.type} named {hero.label} who sees a {f["shamrock"].label} and a {f["drink"].label}.',
        f"Tell a story where {hero.label} wants to {act.verb} on {f['setting'].place} but {captain.label} worries about {prize.phrase}.",
        f'Write a moral-value pirate story that includes the words "circuit", "drink", and "shamrock" and ends with a kind choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, act, prize = f["hero"], f["captain"], f["activity"], f["prize"]
    qa = [
        QAItem(
            question=f"What did {hero.label} want to do with the {act.keyword} on the ship?",
            answer=f"{hero.label} wanted to {act.verb}, but the lantern circuit was too hot and needed care first.",
        ),
        QAItem(
            question=f"Why did {captain.label} worry about the {prize.label}?",
            answer=f"{captain.label} worried because the {prize.label} could get {act.soil} if {hero.label} rushed in without thinking.",
        ),
        QAItem(
            question=f"What did {hero.label} carry that reminded the crew of luck?",
            answer=f"{hero.label} carried a shamrock charm, which looked like a tiny green sign of good luck.",
        ),
        QAItem(
            question="What moral choice did the pirate make?",
            answer=f"The pirate chose to share the drink, tell the truth, and help the crew instead of acting greedy.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shamrock?",
            answer="A shamrock is a small green plant with three leaflets. People often think of it as a lucky sign.",
        ),
        QAItem(
            question="What does a circuit do?",
            answer="A circuit is a path that lets electricity move so a light or machine can work.",
        ),
        QAItem(
            question="Why should people share a drink on a hot day?",
            answer="Sharing a drink can help everyone feel better and keeps one person from taking all of it.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", activity="circuit", prize="coat", name="Pip", gender="boy", parent="captain"),
    StoryParams(place="cabin", activity="drink", prize="map", name="Moira", gender="girl", parent="captain"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.region}, so the prize would not truly be at risk.)"
    return f"(No story: no gear in this world reasonably protects the {prize.label} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} isn't a typical {gender} item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with circuit, drink, and shamrock.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent="captain")


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
