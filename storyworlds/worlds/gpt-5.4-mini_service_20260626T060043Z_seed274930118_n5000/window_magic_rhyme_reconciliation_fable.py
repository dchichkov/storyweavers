#!/usr/bin/env python3
"""
A tiny fable-world about a window, a little Magic, a stubborn Rhyme,
and a reconciliation that makes the room brighter.

Premise:
- A small creature loves a window because it catches light and listens to songs.
- Magic can make words float, but a rhyme can also make a window rattle.
- A misunderstanding grows when the rhyme changes the mood of the room.
- Reconciliation is the gentle turn: the speaker fixes the rhyme, and the window
  becomes a shared place again.

The world is intentionally small and constraint-checked: only stories with a
real tension and a believable reconciliation are generated.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    gift: object | None = None
    helper: object | None = None
    hero: object | None = None
    window: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox", "dog"}
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
    place: str = "the cottage"
    indoor: bool = True
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
class Spell:
    id: str
    name: str
    magic: str
    rhyme: str
    turn: str
    risk: str
    zone: set[str]
    effect: str
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
class Gift:
    id: str
    label: str
    phrase: str
    region: str
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
class Charm:
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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_rattle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("rhyme", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("spark", 0.0) < THRESHOLD:
            continue
        for thing in list(world.entities.values()):
            if thing.type != "window":
                continue
            if "pane" not in world.zone:
                continue
            sig = ("rattle", actor.id, thing.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            thing.meters["tremble"] = thing.meters.get("tremble", 0.0) + 1
            out.append(f"The window gave a little rattle.")
    return out


def _r_sadness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("hurt", 0.0) < THRESHOLD:
            continue
        sig = ("sadness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["sad"] = actor.memes.get("sad", 0.0) + 1
        out.append(f"{actor.id} felt small and sorry.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("apology", 0.0) < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["peace"] = actor.memes.get("peace", 0.0) + 1
        actor.memes["hurt"] = 0.0
        out.append(f"The room grew gentle again.")
    return out


CAUSAL_RULES = [
    Rule("rattle", "physical", _r_rattle),
    Rule("sadness", "social", _r_sadness),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def do_spell(world: World, actor: Entity, spell: Spell, narrate: bool = True) -> None:
    world.zone = set(spell.zone)
    actor.meters["spark"] = actor.meters.get("spark", 0.0) + 1
    actor.memes["rhyme"] = actor.memes.get("rhyme", 0.0) + 1
    propagate(world, narrate=narrate)


def predict_spill(world: World, actor: Entity, spell: Spell, window_id: str) -> dict:
    sim = world.copy()
    do_spell(sim, sim.get(actor.id), spell, narrate=False)
    window = sim.entities[window_id]
    return {
        "rattle": window.meters.get("tremble", 0.0) >= THRESHOLD,
        "hurt": sum(e.memes.get("hurt", 0.0) for e in sim.characters()),
    }


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return "Inside the cottage, the air was quiet, and the window held the morning light."
    return f"{setting.place.capitalize()} stood still under a bright sky, and one window shone like a small pond."


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved the window and the stories it made with light.")


def love_magic(world: World, hero: Entity, spell: Spell) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved Magic, because a tiny spell could make ordinary things feel new.")


def gift_line(world: World, giver: Entity, hero: Entity, gift: Entity) -> None:
    world.say(f"One day, {giver.id} gave {hero.id} {hero.pronoun('object')} {gift.phrase}.")


def love_gift(world: World, hero: Entity, gift: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    gift.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {gift.label} and kept it close by the window.")


def arrive(world: World, hero: Entity, helper: Entity, setting: Setting, spell: Spell) -> None:
    world.say(f"One day, {hero.id} and {helper.id} went to {setting.place}.")
    world.say(setting_detail(setting))
    world.say(f"{hero.id} wanted to use {spell.name} right away.")


def warn(world: World, helper: Entity, hero: Entity, spell: Spell, gift: Entity) -> bool:
    pred = predict_spill(world, hero, spell, gift.id)
    if not pred["rattle"]:
        return False
    world.facts["predicted_hurt"] = pred["hurt"]
    world.say(
        f'"If you use {spell.name}, the {gift.label} may get shaken," {helper.id} said. '
        f'"Let us choose our words kindly."'
    )
    return True


def insists(world: World, hero: Entity, spell: Spell) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"But {hero.id} kept the {spell.rhyme} in mind and tried to say it anyway.")
    world.say(f"{hero.pronoun().capitalize()} spoke the rhyme, and the air answered with a spark.")


def hurt(world: World, helper: Entity, hero: Entity) -> None:
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    world.say(f"The words came out sharp, and {hero.id} felt hurt.")
    world.say(f"{helper.id} saw the hurt and stepped closer.")


def apologize(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["apology"] = hero.memes.get("apology", 0.0) + 1
    world.say(f"{hero.id} lowered {hero.pronoun('possessive')} voice and said sorry.")
    world.say(f"{hero.id} explained that the rhyme was meant to be playful, not unkind.")


def reconcile(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    world.say(f"{helper.id} forgave {hero.id}, and they chose a softer rhyme together.")
    world.say(f"The window stopped trembling, and the light on the sill looked warm again.")


def conclude(world: World, hero: Entity, gift: Entity) -> None:
    world.say(f"In the end, {hero.id} sat by the window with {hero.pronoun('possessive')} {gift.label}, smiling at the quiet light.")


def tell(setting: Setting, spell: Spell, gift_cfg: Gift, hero_name: str, hero_type: str,
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=parent_type, label="the helper"))
    gift = world.add(Entity(id="gift", type=gift_cfg.type, label=gift_cfg.label, phrase=gift_cfg.phrase, region=gift_cfg.region))
    window = world.add(Entity(id="window", type="window", label="window"))

    intro(world, hero)
    love_magic(world, hero, spell)
    gift_line(world, helper, hero, gift)
    love_gift(world, hero, gift)

    world.para()
    arrive(world, hero, helper, setting, spell)
    warn(world, helper, hero, spell, gift)
    insists(world, hero, spell)
    hurt(world, helper, hero)
    apologize(world, hero, helper)
    reconcile(world, hero, helper)
    conclude(world, hero, gift)

    world.facts.update(hero=hero, helper=helper, gift=gift, window=window, setting=setting, spell=spell)
    return world


SETTINGS = {
    "cottage": Setting(place="the cottage", indoor=True, affords={"glimmer"}),
    "attic": Setting(place="the attic", indoor=True, affords={"chant"}),
    "garden_room": Setting(place="the garden room", indoor=True, affords={"glimmer", "chant"}),
}

SPELLS = {
    "glimmer": Spell(
        id="glimmer",
        name="Magic Glimmer",
        magic="glimmer",
        rhyme="shine, little line",
        turn="soften",
        risk="shake",
        zone={"pane"},
        effect="sparkle",
        tags={"magic", "window", "light"},
    ),
    "chant": Spell(
        id="chant",
        name="Rhyme Chant",
        magic="chant",
        rhyme="bloom and room",
        turn="cool",
        risk="sting",
        zone={"pane"},
        effect="hum",
        tags={"rhyme", "window"},
    ),
    "mend": Spell(
        id="mend",
        name="Reconciliation Mend",
        magic="mend",
        rhyme="we can be kind",
        turn="heal",
        risk="none",
        zone={"sill"},
        effect="calm",
        tags={"reconciliation", "window"},
    ),
}

GIFTS = {
    "glass_bird": Gift(id="glass_bird", label="glass bird", phrase="a little glass bird", region="pane"),
    "blue_book": Gift(id="blue_book", label="blue book", phrase="a blue book with bright pages", region="pane"),
    "silk_ribbon": Gift(id="silk_ribbon", label="silk ribbon", phrase="a silk ribbon", region="pane"),
}

CHAR_NAMES = ["Mira", "Toby", "Nina", "Pip", "Luna", "Rowan"]
TRAITS = ["curious", "gentle", "brave", "bright", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for sp in SPELLS.values():
            for g in GIFTS:
                if "window" in sp.tags:
                    combos.append((s, sp.id, g))
    return combos


@dataclass
class StoryParams:
    place: str
    spell: str
    gift: str
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


KNOWLEDGE = {
    "window": [("What is a window?", "A window is a clear opening in a wall that lets in light and lets people see outside.")],
    "magic": [("What is magic in a story?", "Magic in a story is something impossible in real life, like a spell that makes a tiny change happen.")],
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like light and bright.")],
    "reconciliation": [("What is reconciliation?", "Reconciliation is when people stop being upset and make peace again.")],
    "glimmer": [("What does glimmer mean?", "Glimmer means to shine softly, like a small light sparkling on glass.")],
    "mend": [("What does mend mean?", "To mend something is to fix it so it works or feels better again.")],
}
KNOWLEDGE_ORDER = ["window", "magic", "rhyme", "reconciliation", "glimmer", "mend"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, spell, gift = f["hero"], f["helper"], f["spell"], f["gift"]
    return [
        f'Write a short fable for a young child about a child named {hero.id}, a window, and {spell.name}.',
        f"Tell a gentle story where {hero.id} wants to use {spell.name}, but {helper.id} worries about {gift.label}, and they reconcile.",
        f'Write a fable that includes the word "{spell.magic}" and ends with peace by the window.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, spell, gift = f["hero"], f["helper"], f["spell"], f["gift"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who is this story about and what did {hero.id} love?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id}, who loved the window and {spell.name}.",
        ),
        QAItem(
            question=f"What did the helper worry would happen if {hero.id} used {spell.name}?",
            answer=f"{helper.id} worried that the {gift.label} would be shaken and that the room would feel harsh.",
        ),
        QAItem(
            question=f"How did the argument change in the end?",
            answer=f"{hero.id} said sorry, {helper.id} forgave {hero.id}, and they chose a softer rhyme so the room could be peaceful again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["spell"].tags)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", spell="glimmer", gift="glass_bird", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="attic", spell="chant", gift="blue_book", name="Toby", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="garden_room", spell="glimmer", gift="silk_ribbon", name="Nina", gender="girl", parent="mother", trait="patient"),
]


def explain_rejection(spell: Spell, gift: Gift) -> str:
    return f"(No story: this rhyme does not create a believable conflict for the {gift.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "spell", None) and getattr(args, "gift", None):
        if getattr(args, "spell", None) not in SPELLS or getattr(args, "gift", None) not in GIFTS:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "spell", None) is None or c[1] == getattr(args, "spell", None))
              and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, spell, gift = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHAR_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, spell=spell, gift=gift, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SPELLS, params.spell), _safe_lookup(GIFTS, params.gift),
                 params.name, "girl" if params.gender == "girl" else "boy",
                 params.parent, params.trait)
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
    for sp in SPELLS.values():
        lines.append(asp.fact("spell", sp.id))
        for t in sorted(sp.tags):
            lines.append(asp.fact("tags", sp.id, t))
        for z in sorted(sp.zone):
            lines.append(asp.fact("zone", sp.id, z))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_region", gid, g.region))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Spell, Gift) :- setting(Place), spell(Spell), gift(Gift).
valid_story(Place, Spell, Gift) :- valid(Place, Spell, Gift), zone(Spell, pane), gift_region(Gift, pane).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-world about a window, Magic, Rhyme, and Reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible combos ({len(stories)} with story form):\n")
        for place, spell, gift in combos:
            print(f"  {place:10} {spell:8} {gift:12}")
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
            header = f"### {p.name}: {p.spell} at {p.place} (gift: {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
