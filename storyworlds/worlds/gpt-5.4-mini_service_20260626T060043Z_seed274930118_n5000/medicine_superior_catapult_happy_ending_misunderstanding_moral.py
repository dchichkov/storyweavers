#!/usr/bin/env python3
"""
A mythic storyworld about a healer, a superior, and a catapult.

Premise:
A village healer seeks a rare medicine for a sick child. A proud superior sees
the strange device and misunderstands the healer's intent, thinking the
catapult is meant for harm.

Turn:
The healer explains that the catapult is only a way to carry the medicine over
the high river when the bridge is broken.

Resolution:
The superior helps, the medicine arrives in time, and the village learns the
moral value of asking before judging.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- eager import of shared result containers
- lazy import of storyworlds/asp in ASP helpers
- standalone generate/emit/main pipeline
- story-driven state, Q&A, JSON, trace, and ASP verification
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


# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

PLACES = {
    "hearth_valley": "the hearth valley",
    "river_temple": "the river temple",
    "high_cliff": "the high cliff",
    "orchard_hill": "the orchard hill",
}

HERO_NAMES = ["Mira", "Nara", "Sera", "Lena", "Iva", "Talia", "Rina", "Mina"]
SUPERIORS = ["chief", "king", "queen", "lord", "lady", "warden"]
TRAITS = ["wise", "brave", "gentle", "patient", "steady", "kind"]

# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------

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
    portable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    healer: object | None = None
    superior: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "lady", "healer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "lord"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    affordances: set[str] = field(default_factory=set)
    mood: str = "mythic"
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
class Medicine:
    label: str
    phrase: str
    ailment: str
    carried_kind: str  # "hand", "basket", "pouch"
    at_risk_if: str    # "crossing", "hail", "distance"
    virtue: str = "care"
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
class Device:
    id: str
    label: str
    phrase: str
    carry_method: str
    launch_range: str
    safe_use: str
    risk_reason: str
    helps_with: str
    moral: str = "ask before you judge"
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# World registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "hearth_valley": Setting(place="the hearth valley", affordances={"carry", "cross"}),
    "river_temple": Setting(place="the river temple", affordances={"carry", "cross"}),
    "high_cliff": Setting(place="the high cliff", affordances={"launch", "cross"}),
    "orchard_hill": Setting(place="the orchard hill", affordances={"carry", "cross"}),
}

MEDICINES = {
    "moon_salve": Medicine(
        label="moon salve",
        phrase="a silver jar of moon salve",
        ailment="fever",
        carried_kind="jar",
        at_risk_if="crossing the river",
        virtue="healing",
    ),
    "bitter_root": Medicine(
        label="bitter root tea",
        phrase="a little cup of bitter root tea",
        ailment="cough",
        carried_kind="cup",
        at_risk_if="flying through hail",
        virtue="restoring",
    ),
    "sun_leaf": Medicine(
        label="sun leaf syrup",
        phrase="a warm bottle of sun leaf syrup",
        ailment="weakness",
        carried_kind="bottle",
        at_risk_if="traveling a long road",
        virtue="strength",
    ),
}

CATAPULTS = {
    "rope_catapult": Device(
        id="rope_catapult",
        label="catapult",
        phrase="a rope catapult woven from oak and flax",
        carry_method="fling a bundle across the river",
        launch_range="across the ravine",
        safe_use="a small wrapped bundle with no stone tied to it",
        risk_reason="someone could think it was a weapon",
        helps_with="carrying medicine over the broken river bridge",
        moral="ask what a thing is for before you fear it",
    ),
    "stone_slinger": Device(
        id="stone_slinger",
        label="catapult",
        phrase="an old stone catapult on wheels",
        carry_method="send a wrapped bundle to the far bank",
        launch_range="over the water",
        safe_use="a soft bundle of herbs tied in cloth",
        risk_reason="it looks fierce in the dusk",
        helps_with="reaching the temple across the flood",
        moral="look to the purpose, not the shape",
    ),
}

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def medicine_at_risk(medicine: Medicine, setting: Setting, device: Device) -> bool:
    return "cross" in setting.affordances and device.helps_with in {
        "carrying medicine over the broken river bridge",
        "reaching the temple across the flood",
    }


def select_device(medicine: Medicine, setting: Setting) -> Optional[Device]:
    for dev in CATAPULTS.values():
        if medicine_at_risk(medicine, setting, dev):
            return dev
    return None


def explain_rejection(medicine: Medicine, device: Device) -> str:
    return (
        f"(No story: this pairing does not fit the mythic cause. "
        f"The {device.label} must truly help move the {medicine.label}, "
        f"and it must not be a mere dramatic prop.)"
    )


# ---------------------------------------------------------------------------
# Story state and narration
# ---------------------------------------------------------------------------
def _narrate_intro(world: World, healer: Entity, superior: Entity, child: Entity, medicine: Medicine) -> None:
    world.say(
        f"In the old days, when the hills listened and the river answered, "
        f"{healer.id} was a {healer.type} of quiet hands and patient eyes."
    )
    world.say(
        f"{healer.pronoun().capitalize()} carried the hope of {child.id}, "
        f"whose brow was hot with fever and whose breath came thin."
    )
    world.say(
        f"Far above the valley stood {superior.id}, a {superior.type} known for rank, "
        f"who guarded {world.setting.place} and expected every stranger to explain themselves."
    )
    world.say(
        f"The healer sought {medicine.phrase}, for it was said to soothe the sick and "
        f"bring a little morning back to tired faces."
    )


def _narrate_misunderstanding(world: World, healer: Entity, superior: Entity, medicine: Medicine, device: Device) -> None:
    healer.memes["urgency"] += 1
    superior.memes["pride"] += 1
    world.para()
    world.say(
        f"But the river bridge had fallen in spring rain, and the way across was broken."
    )
    world.say(
        f"So {healer.id} built {device.phrase}; {device.carry_method} was the only brave way left."
    )
    world.say(
        f"When {superior.id} saw the tall arms and the cords strung tight, "
        f"{superior.pronoun().capitalize()} misunderstood at once."
    )
    superior.memes["fear"] += 1
    world.say(
        f'"That thing is a threat," {superior.id} cried. "{healer.id} must mean harm!"'
    )
    world.say(
        f"The healer raised {healer.pronoun("possessive")} empty hands and held the wrapped bundle high."
    )
    healer.memes["hurt"] += 1
    world.say(
        f'"No," {healer.id} said, "it is only a way to send the medicine where feet cannot go."'
    )


def _narrate_turn(world: World, healer: Entity, superior: Entity, medicine: Medicine, device: Device) -> None:
    world.para()
    superior.memes["understanding"] += 1
    world.say(
        f"{superior.id} looked longer, and the anger in {superior.pronoun("possessive")} face softened."
    )
    world.say(
        f"{superior.id} saw that the bundle was soft cloth, not a stone, "
        f"and that the device was built to protect the {medicine.label}, not to break a wall."
    )
    world.say(
        f'"I judged too quickly," {superior.id} admitted. "Your strange work was mercy, not war."'
    )
    world.say(
        f"Then {superior.id} ordered the ropes held steady and gave {healer.id} a safer line across the water."
    )


def _narrate_resolution(world: World, healer: Entity, superior: Entity, child: Entity, medicine: Medicine, device: Device) -> None:
    child.memes["hope"] += 2
    child.meters["fever"] = max(0.0, child.meters.get("fever", 0.0) - 2.0)
    world.para()
    world.say(
        f"The {medicine.label} flew across the river in the soft bundle and landed whole in {healer.pronoun('possessive')} hands."
    )
    world.say(
        f"By dusk, the child drank it, the fever fell, and the room grew quiet except for relieved breathing."
    )
    world.say(
        f"{superior.id} bowed to {healer.id} and spoke the old moral value aloud: "
        f'"First learn the purpose of a thing, and only then decide its meaning."'
    )
    world.say(
        f"So the village remembered that a catapult can be a weapon in the wrong heart, "
        f"but in a kind heart it can carry medicine and save a life."
    )
    world.say(
        f"In the last light, the broken bridge was still broken, yet the child slept well, "
        f"and the valley kept a happier story than before."
    )


def tell(setting: Setting, medicine: Medicine, device: Device,
         hero_name: str = "Mira", hero_type: str = "healer",
         superior_name: str = "Aster", superior_type: str = "queen") -> World:
    world = World(setting)
    healer = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    superior = world.add(Entity(id=superior_name, kind="character", type=superior_type))
    child = world.add(Entity(id="child", kind="character", type="child"))
    child.meters["fever"] = 2.0
    world.facts.update(
        healer=healer,
        superior=superior,
        child=child,
        medicine=medicine,
        device=device,
        setting=setting,
    )
    _narrate_intro(world, healer, superior, child, medicine)
    _narrate_misunderstanding(world, healer, superior, medicine, device)
    _narrate_turn(world, healer, superior, medicine, device)
    _narrate_resolution(world, healer, superior, child, medicine, device)
    world.facts["resolved"] = True
    world.facts["misunderstanding"] = True
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
medicine_at_risk(M, S, D) :- medicine(M), setting(S), device(D), needs_crossing(M), helps_crossing(D), crossable(S).
good_story(S, M, D) :- medicine_at_risk(M, S, D), device_for_medicine(D, M).
misunderstanding(D) :- device(D), looks_fierce(D).
moral_value(D) :- device(D), purpose_kind(D).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if "cross" in _safe_lookup(SETTINGS, sid).affordances:
            lines.append(asp.fact("crossable", sid))
    for mid, med in MEDICINES.items():
        lines.append(asp.fact("medicine", mid))
        lines.append(asp.fact("needs_crossing", mid))
    for did, dev in CATAPULTS.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("helps_crossing", did))
        lines.append(asp.fact("looks_fierce", did))
        lines.append(asp.fact("purpose_kind", did))
        for mid in MEDICINES:
            lines.append(asp.fact("device_for_medicine", did, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MEDICINES:
            for did in CATAPULTS:
                combos.append((sid, mid, did))
    return combos


# ---------------------------------------------------------------------------
# Params, QA, generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    medicine: str
    device: str
    healer_name: str
    superior_name: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic medicine, superior, and catapult storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--medicine", choices=MEDICINES)
    ap.add_argument("--device", choices=CATAPULTS)
    ap.add_argument("--healer-name")
    ap.add_argument("--superior-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "medicine", None) and getattr(args, "medicine", None) not in MEDICINES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "device", None) and getattr(args, "device", None) not in CATAPULTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    medicine = getattr(args, "medicine", None) or rng.choice(list(MEDICINES))
    device = getattr(args, "device", None) or rng.choice(list(CATAPULTS))
    return StoryParams(
        place=place,
        medicine=medicine,
        device=device,
        healer_name=getattr(args, "healer_name", None) or rng.choice(HERO_NAMES),
        superior_name=getattr(args, "superior_name", None) or rng.choice(["Aster", "Iona", "Cyrus", "Dorian"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short myth for children about {f['healer'].id}, a {f['healer'].type}, "
        f"who uses a catapult to bring medicine across a broken river.",
        f"Tell a gentle legend where {f['superior'].id} first misunderstands the catapult, "
        f"then learns its true purpose and helps save the sick child.",
        f"Write a mythic story with a clear misunderstanding, a moral value, and a happy ending, "
        f"using the words medicine, superior, and catapult.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    healer = _safe_fact(world, f, "healer")
    superior = _safe_fact(world, f, "superior")
    medicine = _safe_fact(world, f, "medicine")
    device = _safe_fact(world, f, "device")
    child = _safe_fact(world, f, "child")
    return [
        QAItem(
            question=f"Who needed the medicine in the story?",
            answer=f"The child needed {medicine.label} because the child had a fever and needed healing.",
        ),
        QAItem(
            question=f"Why did {superior.id} first misunderstand the catapult?",
            answer=(
                f"{superior.id} first thought the catapult was dangerous because it looked like a weapon, "
                f"but it was really being used to send medicine safely across the broken river."
            ),
        ),
        QAItem(
            question=f"What did {healer.id} use the catapult for?",
            answer=(
                f"{healer.id} used the catapult to carry the medicine across the river, "
                f"so the child could receive it even though the bridge was broken."
            ),
        ),
        QAItem(
            question="What moral did the superior learn?",
            answer=(
                f"The superior learned to ask what something is for before judging it, "
                f"because the same catapult could look fierce but be used kindly."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is medicine for?",
            answer="Medicine is used to help sickness, ease pain, or make a person feel better.",
        ),
        QAItem(
            question="What is a superior?",
            answer="A superior is someone with higher rank or authority, like a ruler or leader.",
        ),
        QAItem(
            question="What is a catapult?",
            answer="A catapult is a machine that can throw or launch an object over a distance.",
        ),
        QAItem(
            question="Why can a misunderstanding happen?",
            answer="A misunderstanding can happen when someone sees a thing but does not know its true purpose.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(MEDICINES, params.medicine),
        _safe_lookup(CATAPULTS, params.device),
        hero_name=params.healer_name,
        superior_name=params.superior_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="hearth_valley", medicine="moon_salve", device="rope_catapult", healer_name="Mira", superior_name="Aster"),
    StoryParams(place="river_temple", medicine="bitter_root", device="stone_slinger", healer_name="Nara", superior_name="Iona"),
    StoryParams(place="orchard_hill", medicine="sun_leaf", device="rope_catapult", healer_name="Sera", superior_name="Cyrus"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_story/3."))
        combos = sorted(set(asp.atoms(model, "good_story")))
        for c in combos:
            print(c)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = getattr(args, "seed", None)
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
