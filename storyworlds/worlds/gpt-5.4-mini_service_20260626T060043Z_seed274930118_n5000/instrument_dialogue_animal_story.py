#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/instrument_dialogue_animal_story.py
==============================================================================================================

A small, self-contained storyworld for gentle animal stories with dialogue and
one important instrument. The domain models a child animal, a cherished
instrument, a tempting place to play, and a reasonable compromise that keeps
the instrument safe.

The story shape is classical:
- setup: who loves the instrument
- tension: the place or weather could damage it
- turn: a caretaker or friend speaks up
- resolution: a fitting protective choice lets play continue

The simulated world uses both physical meters and emotional memes, and the
prose is driven by those state changes.
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
    carried_by: Optional[str] = None
    protected: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    hero: object | None = None
    instrument: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for key in ("dusty", "wet", "scratched", "noisy", "safe"):
            self.meters.setdefault(key, 0.0)
        for key in ("joy", "worry", "love", "desire", "pride", "calm"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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
    indoor: bool = False
    windy: bool = False
    damp: bool = False
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
class Instrument:
    id: str
    label: str
    phrase: str
    kind: str
    care: str
    risky_in: set[str]
    use_verb: str
    sound: str
    tags: set[str] = field(default_factory=set)
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
class Accessory:
    id: str
    label: str
    phrase: str
    protects_against: set[str]
    covers: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id or e.carried_by == actor.id]


@dataclass
class StoryParams:
    place: str
    instrument: str
    accessory: str
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


SETTINGS = {
    "porch": Setting(place="the porch", indoor=False, windy=True, damp=False, affords={"play"}),
    "barn": Setting(place="the barn", indoor=True, windy=False, damp=False, affords={"play"}),
    "garden": Setting(place="the garden", indoor=False, windy=False, damp=True, affords={"play"}),
    "meadow": Setting(place="the meadow", indoor=False, windy=True, damp=False, affords={"play"}),
}

INSTRUMENTS = {
    "flute": Instrument(
        id="flute",
        label="flute",
        phrase="a shiny little flute",
        kind="wind",
        care="keep it dry and clean",
        risky_in={"damp", "rain"},
        use_verb="play the flute",
        sound="a bright, breathy trill",
        tags={"music", "wind", "instrument"},
    ),
    "drum": Instrument(
        id="drum",
        label="drum",
        phrase="a round drum with a soft strap",
        kind="beat",
        care="keep the skin tight and clean",
        risky_in={"damp"},
        use_verb="tap the drum",
        sound="a warm boom-boom beat",
        tags={"music", "beat", "instrument"},
    ),
    "violin": Instrument(
        id="violin",
        label="violin",
        phrase="a tiny violin with a brown bow",
        kind="string",
        care="keep the wood and strings safe",
        risky_in={"damp", "wind"},
        use_verb="play the violin",
        sound="a sweet singing note",
        tags={"music", "string", "instrument"},
    ),
    "horn": Instrument(
        id="horn",
        label="horn",
        phrase="a little horn that shone like gold",
        kind="brass",
        care="keep the mouthpiece clean and dry",
        risky_in={"damp", "dust"},
        use_verb="blow the horn",
        sound="a clear, cheerful toot",
        tags={"music", "instrument", "brass"},
    ),
}

ACCESSORIES = {
    "case": Accessory(
        id="case",
        label="a padded case",
        phrase="a soft padded case",
        protects_against={"damp", "dust"},
        covers={"instrument"},
        prep="put the instrument in a padded case first",
        tail="carefully packed the instrument in the padded case",
    ),
    "cloth": Accessory(
        id="cloth",
        label="a clean cloth",
        phrase="a clean cloth wrap",
        protects_against={"damp", "dust"},
        covers={"instrument"},
        prep="wrap the instrument in a clean cloth first",
        tail="wrapped the instrument in the clean cloth",
    ),
    "roof": Accessory(
        id="roof",
        label="the roofed porch",
        phrase="the roofed porch",
        protects_against={"damp", "wind"},
        covers={"place"},
        prep="move to the roofed porch first",
        tail="moved under the roofed porch",
    ),
}

TRAITS = ["curious", "cheerful", "gentle", "brave", "playful"]
GIRL_NAMES = ["Mina", "Luna", "Ruby", "Pippa", "Tilly", "Nora"]
BOY_NAMES = ["Otto", "Milo", "Benny", "Arlo", "Toby", "Finn"]


def instrument_at_risk(setting: Setting, instrument: Instrument) -> bool:
    if setting.damp and "damp" in instrument.risky_in:
        return True
    if setting.windy and "wind" in instrument.risky_in:
        return True
    return False


def select_accessory(setting: Setting, instrument: Instrument) -> Optional[Accessory]:
    for acc in ACCESSORIES.values():
        if "place" in acc.covers:
            if (setting.damp and "damp" in acc.protects_against) or (setting.windy and "wind" in acc.protects_against):
                return acc
        if "instrument" in acc.covers:
            if any(r in acc.protects_against for r in instrument.risky_in):
                return acc
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for inst_id, inst in INSTRUMENTS.items():
            if instrument_at_risk(setting, inst) and select_accessory(setting, inst):
                for acc_id, acc in ACCESSORIES.items():
                    if ("instrument" in acc.covers and any(r in acc.protects_against for r in inst.risky_in)) or (
                        "place" in acc.covers and ((setting.damp and "damp" in acc.protects_against) or (setting.windy and "wind" in acc.protects_against))
                    ):
                        out.append((place, inst_id, acc_id))
    return sorted(set(out))


def apply_risk(world: World) -> list[str]:
    out = []
    setting = world.setting
    for actor in world.characters():
        instrument = next((e for e in world.entities.values() if e.owner == actor.id and e.kind == "instrument"), None)
        if instrument is None:
            continue
        if setting.damp and "damp" in instrument.meters and instrument.meters["wet"] >= THRESHOLD:
            continue
        if setting.windy and instrument.meters["dusty"] < THRESHOLD and "wind" in _safe_lookup(INSTRUMENTS, instrument.type).risky_in:
            sig = ("wind", actor.id, instrument.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            instrument.meters["dusty"] += 1
            actor.memes["worry"] += 1
            out.append(f"The wind made {actor.id}'s {instrument.label} feel unsafe.")
    return out


def apply_safe_choice(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protected and item.meters["safe"] < THRESHOLD:
                sig = ("safe", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["safe"] += 1
                actor.memes["calm"] += 1
                out.append(f"That helped keep things calm.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (apply_risk, apply_safe_choice):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, actor: Entity, instrument: Instrument) -> bool:
    sim = world.copy()
    sim_inst = sim.get(instrument.id)
    if sim.setting.damp and "damp" in instrument.risky_in:
        sim_inst.meters["wet"] += 1
    if sim.setting.windy and "wind" in instrument.risky_in:
        sim_inst.meters["dusty"] += 1
    return sim_inst.meters["wet"] >= THRESHOLD or sim_inst.meters["dusty"] >= THRESHOLD


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved every song the day could hold.")


def loves_instrument(world: World, hero: Entity, instrument: Entity, inst_def: Instrument) -> None:
    hero.memes["love"] += 1
    instrument.owner = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {instrument.label} and listened for its {inst_def.sound}.")


def wants_to_play(world: World, hero: Entity, instrument: Entity, inst_def: Instrument) -> None:
    hero.memes["desire"] += 1
    world.say(f'{hero.id} wanted to {inst_def.use_verb}, so {hero.pronoun()} picked up the {instrument.label}.')
    world.say(f'"I want to hear it sing," {hero.pronoun()} whispered.')


def warn(world: World, parent: Entity, hero: Entity, instrument: Entity, inst_def: Instrument) -> bool:
    if not predict_risk(world, hero, inst_def):
        return False
    parent.memes["worry"] += 1
    world.say(f'"Wait a little," {parent.id} said. "Your {instrument.label} needs to {inst_def.care}."')
    return True


def reply(world: World, hero: Entity, parent: Entity, instrument: Entity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f'"But I really want to play now," {hero.id} said, hugging the {instrument.label} close.')


def offer_fix(world: World, parent: Entity, hero: Entity, instrument: Entity, acc_def: Accessory) -> None:
    world.say(f'"How about we {acc_def.prep}?" {parent.id} asked.')
    world.say(f'"Then you can still play, and the {instrument.label} stays safe."')


def accept_fix(world: World, hero: Entity, parent: Entity, instrument: Entity, inst_def: Instrument, acc_def: Accessory) -> None:
    hero.memes["joy"] += 1
    hero.memes["calm"] += 1
    parent.memes["calm"] += 1
    instrument.protected = True
    if acc_def.covers == {"place"}:
        world.say(f'{hero.id} nodded. "Okay," {hero.pronoun()} said. "Let’s go there together."')
    else:
        world.say(f'{hero.id} nodded. "Okay," {hero.pronoun()} said. "That will keep my {instrument.label} safe."')
    world.say(f"They {acc_def.tail}, and soon {hero.id} was ready to {inst_def.use_verb}.")
    world.say(f'The {instrument.label} made {inst_def.sound}, and {hero.id} smiled at the happy sound.')


def tell(setting: Setting, inst_def: Instrument, acc_def: Accessory, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    instrument = world.add(Entity(id="Instrument", kind="instrument", type=inst_def.id, label=inst_def.label, phrase=inst_def.phrase, owner=hero.id))
    hero.memes["joy"] += 0.5

    introduce(world, hero)
    world.say(f'{hero.id} had {instrument.phrase}, and it was {trait} to carry.')
    loves_instrument(world, hero, instrument, inst_def)

    world.para()
    if setting.place:
        world.say(f"One day, {hero.id} went to {setting.place} with {hero.pronoun('possessive')} {instrument.label}.")
    wants_to_play(world, hero, instrument, inst_def)
    warn(world, parent, hero, instrument, inst_def)
    reply(world, hero, parent, instrument)

    world.para()
    offer_fix(world, parent, hero, instrument, acc_def)
    accept_fix(world, hero, parent, instrument, inst_def, acc_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        instrument=instrument,
        instrument_def=inst_def,
        accessory_def=acc_def,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    inst = _safe_fact(world, f, "instrument_def")
    return [
        f'Write a short animal story with dialogue about {hero.id} and a {inst.label}.',
        f'Tell a gentle story where a {hero.type} named {hero.id} wants to {inst.use_verb}.',
        f'Write a child-friendly story about an instrument, a worried parent, and a safe compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    inst = _safe_fact(world, f, "instrument_def")
    acc = _safe_fact(world, f, "accessory_def")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {inst.label}?",
            answer=f"{hero.id} wanted to {inst.use_verb} at {setting.place}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {inst.label}?",
            answer=f"{parent.id} worried because the {setting.place} was a place where the {inst.label} could get {('damp' if setting.damp else 'windy' if setting.windy else 'messy')}, and it needed to {inst.care}.",
        ),
        QAItem(
            question=f"What helped keep the {inst.label} safe?",
            answer=f"{acc.phrase} helped keep the {inst.label} safe so {hero.id} could still play.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} happily making {inst.sound} while everyone felt calm.",
        ),
    ]


KNOWLEDGE = {
    "instrument": [
        ("What is an instrument?", "An instrument is something people use to make music, like a drum, flute, violin, or horn."),
    ],
    "music": [
        ("What is music?", "Music is a pattern of sounds that people and animals can enjoy, hum, or dance to."),
    ],
    "wind": [
        ("What can wind do?", "Wind can blow papers around, ruffle fur, and make loose things move."),
    ],
    "damp": [
        ("Why should wood stay dry?", "Wood can swell or get damaged if it stays wet for too long."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["instrument_def"].tags)
    if world.facts["setting"].windy:
        tags.add("wind")
    if world.facts["setting"].damp:
        tags.add("damp")
    out = []
    for tag in ("instrument", "music", "wind", "damp"):
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
        if e.kind == "instrument":
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the setting makes the instrument risky and there is
% at least one accessory that can really protect it.
risk(Place, I) :- setting(Place), instrument(I), windy(Place), risky(I, wind).
risk(Place, I) :- setting(Place), instrument(I), damp(Place), risky(I, damp).

protects(A, I) :- accessory(A), instrument(I), covers(A, instrument), risky(I, R), shields(A, R).
protects(A, I) :- accessory(A), covers(A, place), risky(I, R), shields(A, R).

valid(Place, I, A) :- risk(Place, I), protects(A, I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        if s.windy:
            lines.append(asp.fact("windy", pid))
        if s.damp:
            lines.append(asp.fact("damp", pid))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        for r in sorted(inst.risky_in):
            lines.append(asp.fact("risky", iid, r))
    for aid, acc in ACCESSORIES.items():
        lines.append(asp.fact("accessory", aid))
        for c in sorted(acc.covers):
            lines.append(asp.fact("covers", aid, c))
        for p in sorted(acc.protects_against):
            lines.append(asp.fact("shields", aid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with dialogue and one instrument.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--accessory", choices=ACCESSORIES)
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


def explain_rejection(place: str, instrument: str) -> str:
    return f"(No story: the {place} does not make the {instrument} risky enough for a real dialogue-driven fix.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "instrument", None):
        combos = [c for c in combos if c[1] == getattr(args, "instrument", None)]
    if getattr(args, "accessory", None):
        combos = [c for c in combos if c[2] == getattr(args, "accessory", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, instrument, accessory = (list(rng.choice(combos)) + [None, None, None])[:3]
    inst = _safe_lookup(INSTRUMENTS, instrument)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, instrument=instrument, accessory=accessory, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(INSTRUMENTS, params.instrument),
        _safe_lookup(ACCESSORIES, params.accessory),
        params.name,
        {"girl": "girl", "boy": "boy"}[params.gender],
        params.parent,
        params.trait,
    )
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
    StoryParams(place="meadow", instrument="flute", accessory="case", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="garden", instrument="drum", accessory="cloth", name="Otto", gender="boy", parent="father", trait="playful"),
    StoryParams(place="porch", instrument="violin", accessory="roof", name="Luna", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="meadow", instrument="horn", accessory="roof", name="Milo", gender="boy", parent="father", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, instrument, accessory) combos:\n")
        for place, inst, acc in triples:
            print(f"  {place:8} {inst:10} {acc}")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.instrument} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
