#!/usr/bin/env python3
"""
storyworlds/worlds/occupy_foreshadowing_inner_monologue_magic_bedtime_story.py
==============================================================================

A small bedtime-story world about a child, a cozy place, and a magical
complication that turns into a gentle resolution.

Premise:
- A child wants to occupy a special cozy spot at bedtime.
- A parent or caretaker notices a foreshadowed problem: the spot is already
  claimed by a tiny magical helper or needs to stay free for magic to work.
- The child narrates an inner monologue about wanting comfort, control, and
  safety.
- A small magic-related compromise lets the child occupy a different cozy place,
  or occupy the spot in a new way, and the ending proves the world changed.

The story is deliberately state-driven: the child's desire, the place's
occupancy, and magical readiness all change as the tale unfolds.
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

BEDTIME_THRESHOLD = 1.0



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
    occupied_by: Optional[str] = None
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    child: object | None = None
    obj: object | None = None
    parent: object | None = None
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
    cozy: str
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
class ObjectDef:
    label: str
    phrase: str
    type: str
    location: str
    comfort: str
    requires_magic: bool = False
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
class MagicDef:
    id: str
    label: str
    prep: str
    outcome: str
    grants: str
    keeps_open: bool = False
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
        self.facts: dict[str, object] = {}
        self.zone: str = ""
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.zone = self.zone
        clone.fired = set(self.fired)
        return clone


def _by_trait(name: str, trait: str) -> str:
    return f"{trait} {name}".strip()


def _article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def _capitalize_pronoun(p: str) -> str:
    return p[:1].upper() + p[1:]


def _occupy_ok(obj: ObjectDef, magic: Optional[MagicDef]) -> bool:
    if not obj.requires_magic:
        return True
    return magic is not None


def _predict(world: World, child: Entity, obj: Entity, magic: Optional[MagicDef]) -> dict:
    sim = world.copy()
    _attempt_occupy(sim, sim.get(child.id), sim.get(obj.id), magic, narrate=False)
    spot = sim.get(obj.id)
    return {
        "occupied": spot.occupied_by == child.id,
        "magic_on": bool(magic),
        "sparkles": child.meters.get("wonder", 0.0),
    }


def _attempt_occupy(world: World, child: Entity, obj: Entity, magic: Optional[MagicDef], narrate: bool = True) -> None:
    if obj.occupied_by and obj.occupied_by != child.id:
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        world.facts["blocked_by"] = obj.occupied_by
        if narrate:
            world.say(f"{child.id} hesitated, because {obj.label} was already occupied.")
        return
    if obj.requires_magic and magic is None:
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        if narrate:
            world.say(f"{child.id} could not settle there yet, because the magic had to stay awake.")
        return
    obj.occupied_by = child.id
    child.meters["cozy"] = child.meters.get("cozy", 0.0) + 1
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    if magic and magic.keeps_open:
        world.facts["magic_kept_open"] = True
    if narrate:
        world.say(f"{child.id} slipped into {obj.label} and made it feel like home.")


def resolve_magic_plan(world: World, child: Entity, obj: Entity, magic: MagicDef) -> None:
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1
    child.meters["wonder"] = child.meters.get("wonder", 0.0) + 1
    world.say(
        f'{child.id} thought, "{child.id} only wants to be warm and safe," '
        f"and that thought made the room feel softer."
    )
    world.say(
        f"{_capitalize_pronoun(child.pronoun())} noticed the little glitter near {obj.label} "
        f"and remembered the quiet foreshadowing from earlier."
    )
    world.say(
        f'Then {magic.prep}, and the tiny spell answered by {magic.outcome}.'
    )


def bedtime_settling(world: World, child: Entity, obj: Entity, magic: Optional[MagicDef]) -> None:
    child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1
    if obj.occupied_by == child.id:
        world.say(
            f"In the end, {child.id} was tucked into {obj.label}, and the night "
            f"kept its gentle promise."
        )
    elif magic is not None and magic.keeps_open:
        world.say(
            f"In the end, the magic stayed open like a soft doorway, and {child.id} "
            f"rested nearby with a happy heart."
        )


SETTINGS = {
    "nursery": Setting(place="the nursery", cozy="the softest room in the house", affords={"bed", "nest", "couch"}),
    "attic": Setting(place="the attic room", cozy="the quiet room under the roof", affords={"nest", "chair"}),
    "cottage": Setting(place="the little cottage bedroom", cozy="the room with warm curtains", affords={"bed", "windowseat"}),
}

OBJECTS = {
    "bed": ObjectDef(
        label="the moon-white bed",
        phrase="a moon-white bed with a stitched blanket",
        type="bed",
        location="nursery",
        comfort="very soft",
        requires_magic=False,
    ),
    "nest": ObjectDef(
        label="the velvet nest",
        phrase="a velvet nest made of pillows",
        type="nest",
        location="attic",
        comfort="extra cozy",
        requires_magic=True,
    ),
    "couch": ObjectDef(
        label="the little couch",
        phrase="a little couch with rounded arms",
        type="couch",
        location="nursery",
        comfort="soft",
        requires_magic=False,
    ),
    "windowseat": ObjectDef(
        label="the window seat",
        phrase="a window seat with a knitted cushion",
        type="windowseat",
        location="cottage",
        comfort="warm",
        requires_magic=True,
    ),
    "chair": ObjectDef(
        label="the rocking chair",
        phrase="a rocking chair with a sleepy creak",
        type="chair",
        location="attic",
        comfort="gentle",
        requires_magic=False,
    ),
}

MAGIC = {
    "lamp": MagicDef(
        id="lamp",
        label="the little lamp spell",
        prep="the child whispered to the lamp and rubbed the tiny star on its side",
        outcome="the lamp glowed in a round and sleepy circle",
        grants="warm light",
        keeps_open=False,
    ),
    "blanket": MagicDef(
        id="blanket",
        label="the whispering blanket charm",
        prep="the caretaker folded the blanket and told it a bedtime secret",
        outcome="the blanket grew warm and snug as toast",
        grants="warmth",
        keeps_open=True,
    ),
    "star": MagicDef(
        id="star",
        label="the star-in-the-pocket trick",
        prep="the child held a pebble shaped like a star and breathed on it twice",
        outcome="the star scattered a few silver sparkles over the pillows",
        grants="sparkles",
        keeps_open=True,
    ),
}

NAMES = ["Mia", "Noah", "Lina", "Theo", "Luna", "Eli", "Pia", "Remy"]
TRAITS = ["sleepy", "gentle", "curious", "careful", "soft-hearted", "brave"]


def choose_combo() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for obj_id in setting.affords:
            obj = _safe_lookup(OBJECTS, obj_id)
            for magic_id, magic in MAGIC.items():
                if _occupy_ok(obj, magic):
                    combos.append((place, obj_id, magic_id))
    return combos


@dataclass
class StoryParams:
    place: str
    object: str
    magic: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about occupy, foreshadowing, inner monologue, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--magic", choices=MAGIC)
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
    combos = [c for c in choose_combo()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "object", None) is None or c[1] == getattr(args, "object", None))
              and (getattr(args, "magic", None) is None or c[2] == getattr(args, "magic", None))]
    if getattr(args, "object", None) and getattr(args, "magic", None) and not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj_id, magic_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, object=obj_id, magic=magic_id, name=name, gender=gender, parent=parent, trait=trait)


def _intro(world: World, child: Entity, parent: Entity, obj: Entity, setting: Setting) -> None:
    world.say(
        f"At bedtime, {child.id} was a {_by_trait(child.id, child.type)} child who loved the hush of {setting.place}."
    )
    world.say(
        f"{_capitalize_pronoun(child.pronoun())} liked {obj.label} because it looked like the kind of place where dreams could land."
    )
    child.memes["love"] = child.memes.get("love", 0.0) + 1


def _foreshadow(world: World, child: Entity, obj: Entity, magic: MagicDef) -> None:
    world.say(
        f"Before the lights went out, a tiny sparkle twinkled near {obj.label}, which felt like a secret waiting to be told."
    )
    if obj.requires_magic:
        world.say(
            f"{child.id} noticed that {obj.label} seemed to need the magic to stay open and kind."
        )
    else:
        world.say(
            f"{child.id} noticed that the room was calm, but the sparkle still hinted that the night had a trick tucked inside."
        )
    world.facts["foreshadowed"] = True


def _inner_monologue(world: World, child: Entity, obj: Entity) -> None:
    world.say(
        f'{child.id} thought, "I want to occupy that cozy place because it looks warm and safe."'
    )
    world.say(
        f'Then {child.id} thought, "But if I rush, I might miss the little clue the room is trying to share."'
    )
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1


def _parent_warning(world: World, parent: Entity, child: Entity, obj: Entity, magic: MagicDef) -> None:
    if obj.requires_magic:
        world.say(
            f'{parent.id} said, "Not yet, dear one. That spot is being held open by {magic.label}."'
        )
    else:
        world.say(
            f'{parent.id} said, "Careful now. The sparkle means we should choose gently."'
        )
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1


def _compromise(world: World, child: Entity, obj: Entity, magic: MagicDef) -> None:
    if obj.requires_magic:
        world.say(
            f"{child.id} took a breath, listened to the tiny magic, and chose to occupy the space beside it instead of pushing in."
        )
        obj.occupied_by = child.id
        child.meters["cozy"] = child.meters.get("cozy", 0.0) + 1
        child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    else:
        world.say(
            f"{child.id} let the magic light the room and then climbed into {obj.label}, careful and slow."
        )
        obj.occupied_by = child.id
        child.meters["cozy"] = child.meters.get("cozy", 0.0) + 1
        child.memes["calm"] = child.memes.get("calm", 0.0) + 1


def _ending(world: World, child: Entity, obj: Entity, magic: MagicDef) -> None:
    if obj.occupied_by == child.id:
        world.say(
            f"In the end, {child.id} was tucked in and the magic stayed kind, so the room felt occupied by warmth instead of worry."
        )
    else:
        world.say(
            f"In the end, {child.id} rested near the glow, and the night was peaceful enough to hold both sleep and sparkle."
        )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    obj_def = _safe_lookup(OBJECTS, params.object)
    magic_def = MAGIC[params.magic]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "sleepy"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    obj = world.add(Entity(
        id="Object",
        type=obj_def.type,
        label=obj_def.label,
        phrase=obj_def.phrase,
        owner=child.id,
        caretaker=parent.id,
        magical=obj_def.requires_magic,
    ))
    world.facts.update(child=child, parent=parent, obj=obj, magic=magic_def, setting=setting, obj_def=obj_def)

    _intro(world, child, parent, obj, setting)
    world.para()
    _foreshadow(world, child, obj, magic_def)
    _inner_monologue(world, child, obj)
    _parent_warning(world, parent, child, obj, magic_def)

    world.para()
    resolve = _predict(world, child, obj, magic_def)
    world.facts["predicted_occupied"] = resolve["occupied"]
    resolve_magic_plan(world, child, obj, magic_def)
    _compromise(world, child, obj, magic_def)
    _ending(world, child, obj, magic_def)
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    obj_def: ObjectDef = _safe_fact(world, f, "obj_def")
    setting: Setting = _safe_fact(world, f, "setting")
    magic: MagicDef = _safe_fact(world, f, "magic")
    return [
        f'Write a bedtime story about a child named {child.id} who wants to occupy {obj_def.label}.',
        f"Tell a gentle story where {child.id} hears a foreshadowing clue and uses {magic.label} to solve a bedtime problem at {setting.place}.",
        f'Write a calm story for a young child that includes the word "occupy" and ends with a cozy night image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    obj: Entity = _safe_fact(world, f, "obj")
    magic: MagicDef = _safe_fact(world, f, "magic")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What did {child.id} want to do with {obj.label}?",
            answer=f"{child.id} wanted to occupy {obj.label} because it looked warm, safe, and perfect for bedtime.",
        ),
        QAItem(
            question=f"Why did {parent.id} pause before {child.id} could settle there?",
            answer=f"{parent.id} paused because the story gave a foreshadowing clue that {magic.label} was keeping the space special.",
        ),
        QAItem(
            question=f"How did {child.id} feel after the magical bedtime choice?",
            answer=f"{child.id} felt calmer and cozier, and the end of the story showed {obj.label} or the nearby space gently occupied for sleep.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {setting.place}, which was described as {setting.cozy}.",
        ),
    ]


KNOWLEDGE = {
    "occupy": [
        (
            "What does it mean to occupy a place?",
            "To occupy a place means to be in it or use it, like sitting on a chair or sleeping in a bed.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is a clue that hints something important may happen later.",
        )
    ],
    "inner": [
        (
            "What is an inner monologue?",
            "An inner monologue is the silent voice in a person's mind when they think to themselves.",
        )
    ],
    "magic": [
        (
            "What is magic in a bedtime story?",
            "Magic in a bedtime story is something wonderful or impossible that helps the story feel gentle and special.",
        )
    ],
    "bed": [
        (
            "Why is bedtime important?",
            "Bedtime helps bodies and minds rest so they can wake up ready for a new day.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE["occupy"] + KNOWLEDGE["foreshadowing"] + KNOWLEDGE["inner"] + KNOWLEDGE["magic"] + KNOWLEDGE["bed"]]


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
        if e.occupied_by:
            bits.append(f"occupied_by={e.occupied_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", object="bed", magic="blanket", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="attic", object="nest", magic="star", name="Theo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="cottage", object="windowseat", magic="lamp", name="Luna", gender="girl", parent="mother", trait="sleepy"),
    StoryParams(place="nursery", object="couch", magic="star", name="Eli", gender="boy", parent="father", trait="careful"),
]


ASP_RULES = r"""
% A cozy place is occupiable when it is part of the setting's bedtime affordances.
occupiable(S,O) :- affords(S,O), object(O).

% A magical object is valid if the story can still resolve by careful occupying.
valid_story(S,O,M) :- occupiable(S,O), magic(M), can_resolve(O,M).

can_resolve(O,M) :- requires_magic(O), magic(M).
can_resolve(O,M) :- not requires_magic(O), magic(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for o in sorted(s.affords):
            lines.append(asp.fact("affords", sid, o))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.requires_magic:
            lines.append(asp.fact("requires_magic", oid))
    for mid, m in MAGIC.items():
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show occupiable/2."))
    return sorted(set(asp.atoms(model, "occupiable")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    return choose_combo()


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((place, obj) for place, obj, _ in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} occupiable pairs).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
        triples = asp_valid_stories()
        print(f"{len(triples)} valid story combinations:\n")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.name}: occupy {p.object} at {p.place} with {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
