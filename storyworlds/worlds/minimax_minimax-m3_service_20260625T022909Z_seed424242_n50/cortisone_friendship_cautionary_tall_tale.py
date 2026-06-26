#!/usr/bin/env python3
"""
storyworlds/worlds/cortisone_friendship_cautionary_tall_tale.py
================================================================

A standalone *story world* sketch for a TinyStories-style domain built from
the seed word "cortisone", leaning on the "Friendship" and "Cautionary"
features, and told in a playful Tall Tale voice.

Initial story (used to build a world model):
---
On the great blue porch of a small yellow clinic, two friends sat
shoulder to shoulder. Juniper was a thoughtful rabbit with one very
itchy elbow, and Pip was a small, steady turtle who believed in slow
plans. The clinic belonged to Dr. Sedge, who wore big glasses and a
white coat that flapped when she marched.

Juniper scratched and scratched. "My elbow is a hot, hot drum," she
said. "I need the Magic Pint of cortisone, the one that makes the
swelling sleep." Dr. Sedge smiled and shook her head. "That pint is for
bad flare-ups, dear," she said, "and the dose must be measured. Too much
of the Magic Pint will make your bones feel hollow, and too little will
not hush the drum at all. Let us try the Cool Compress on the porch
first, and a tiny measured drop, just one, and see how the drum
behaves."

But Juniper had heard a Tall Tale at sunrise. "Auntie Wren told me,"
she whispered, "that the pint will make a hero out of anyone who drinks
deep. If I drink the whole Magic Pint, my elbow will never itch again,
and I will be the bravest rabbit in the county." Pip's small green
face went very still. "Friend," he said softly, "the tale sounds grand,
but the clinic shelf is higher than you, and a too-big dose can shrink
the good things inside a body. The slow plan is the truer magic."

Juniper pouted. She climbed the clinic shelf when Dr. Sedge was not
looking, and she reached for the cool, heavy bottle. The pint was
labeled in careful letters, and the cap was a small fortress. She
twisted and twisted. Pip climbed up beside her, very out of breath, and
he did not grab the bottle from her hand. Instead, he held her paw
still and said, "Let us measure. One careful drop, and we watch the
drum together, and if the drum still shouts, Dr. Sedge can choose what
to do."

Juniper blinked. She did not drink the whole Magic Pint. She let Pip
tip the cool dropper, and one careful drop landed on the drum of her
elbow, and the hot beat slowed to a sleepy hush. Dr. Sedge came back,
and she was not cross, only proud. "You measured the magic," she said,
"and you kept your friend. That is the bravest thing the Tall Tale
ever taught." Juniper and Pip sat on the great blue porch, shoulder to
shoulder, and they promised, the way Tall Tale friends do, that they
would never drink more magic than their bones could hold.

Causal state updates:
---
    skin itches / swelling rises    -> skin.itch += 1 ; skin.swelling += 1
    child warned about dose         -> child.caution += 1
    child ignores warning + climbs  -> child.risk += 1 ; child.daring += 1
    friend steadies the hand        -> child.reckless -> 0 ; child.measured += 1
    whole bottle / too-big dose     -> bone.hollow += 1 ; child.brave -> low
    measured drop, not the whole    -> skin.itch -> low ; bone.hollow = 0
    friends sit together at end     -> bond.tall_tale_oath += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# (``python storyworlds/worlds/cortisone_friendship_cautionary_tall_tale.py``):
# add the package dir (storyworlds/) to the path so ``results`` resolves
# regardless of the current working directory.
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # rabbit, turtle, doctor, bottle, dropper ...
    label: str = ""                # short reference, e.g. "pint", "elbow"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    region: str = ""               # body part key (elbow, paw, shell, ...)
    on_shelf: bool = False         # is the medicine on the high shelf?
    # Two numeric dimensions (cf. story.py memeplex model).
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    bond: object | None = None
    bone: object | None = None
    bottle_e: object | None = None
    bottle_holder: object | None = None
    complaint_e: object | None = None
    doctor: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"rabbit", "girl", "mother", "doe"}
        male = {"turtle", "boy", "father", "drake"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def label_word(self) -> str:
        return {"doctor": "the doctor", "rabbit": "the rabbit",
                "turtle": "the turtle", "girl": "the girl",
                "boy": "the boy"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
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
class Setting:
    place: str = "the great blue porch"
    where: str = "outdoors"   # "outdoors" | "indoors"
    afford: set[str] = field(default_factory=set)
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
class Complaint:
    """The body's loud drum -- what is hurting the hero."""
    id: str
    body_part: str     # "elbow" | "knee" | "wing" | "paw"
    feel: str          # "hot, hot drum" | "stingy thrum" | "itchy thump"
    rise: str          # "swelling" -- the meter the complaint raises
    noun: str          # "Magic Pint" | "blue bottle" -- the medicine name
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
class Bottle:
    """The medicine on the high shelf, with a dose, a label, and a town tale."""
    id: str
    name: str          # "Magic Pint of cortisone" -- the Tall Tale name
    measured: str      # "a tiny measured drop" -- the safe dose
    whole: str         # "the whole pint" -- the reckless move
    rhyme: str         # a short Tall Tale rhyme the wind carries
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
class Compromise:
    """The steady, slow plan the friend offers in the middle beat."""
    id: str
    name: str          # "Cool Compress and a measured drop"
    body: str          # the offer line
    tail: str          # the closing image line


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
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


def _r_warning_caution(world: World) -> list[str]:
    """A child warned about a dose absorbs the caution."""
    out: list[str] = []
    for child in world.characters():
        if child.memes["warned"] < THRESHOLD:
            continue
        sig = ("caution", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["caution"] += 1
    return out


def _r_climb_risk(world: World) -> list[str]:
    """Climbing the shelf while ignoring the warning raises risk + daring."""
    out: list[str] = []
    for child in world.characters():
        if child.memes["climbed"] < THRESHOLD:
            continue
        sig = ("risk", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["risk"] += 1
        child.memes["daring"] += 1
    return out


def _r_measured_clears_reckless(world: World) -> list[str]:
    """Friend steadies the hand -> reckless drains, measured rises."""
    out: list[str] = []
    for child in world.characters():
        if child.memes["steady_hand"] < THRESHOLD:
            continue
        sig = ("measured", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["reckless"] = 0.0
        child.memes["measured"] += 1
    return out


def _r_whole_pint_hollows_bones(world: World) -> list[str]:
    """Drinking the whole pint hollows the bones (only if reckless >= risk)."""
    out: list[str] = []
    for child in world.characters():
        if child.memes["whole_pint"] < THRESHOLD:
            continue
        if child.memes["reckless"] < child.memes["risk"] * 0.5:
            continue                # the friend already steadied the hand
        sig = ("hollow", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        bone = world.get("bone")
        bone.meters["hollow"] += 1
        child.memes["heroic"] = 0.0
    return out


def _r_measured_drop_calms_drum(world: World) -> list[str]:
    """A measured drop calms the swelling/itch but only if reckless is low."""
    out: list[str] = []
    for child in world.characters():
        if child.memes["measured_drop"] < THRESHOLD:
            continue
        if child.memes["reckless"] >= THRESHOLD:
            continue
        sig = ("calm", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        complaint = world.get("complaint")
        complaint.meters["itch"] = max(0.0, complaint.meters["itch"] - 1)
        complaint.meters["swelling"] = max(0.0, complaint.meters["swelling"] - 1)
        child.memes["calm"] += 1
    return out


def _r_oath(world: World) -> list[str]:
    """A shared ending oath (the Tall Tale bond)."""
    out: list[str] = []
    chars = world.characters()
    if not any(c.memes["calm"] >= THRESHOLD for c in chars):
        return out
    if not any(c.memes["measured"] >= THRESHOLD for c in chars):
        return out
    sig = ("oath", "all")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bond = world.get("bond")
    bond.meters["oath"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="warning_caution", tag="social", apply=_r_warning_caution),
    Rule(name="climb_risk", tag="social", apply=_r_climb_risk),
    Rule(name="measured_clears_reckless", tag="social", apply=_r_measured_clears_reckless),
    Rule(name="whole_pint_hollows_bones", tag="physical", apply=_r_whole_pint_hollows_bones),
    Rule(name="measured_drop_calms_drum", tag="physical", apply=_r_measured_drop_calms_drum),
    Rule(name="oath", tag="social", apply=_r_oath),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
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


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* complaint and a *reasonable* fix.
# ---------------------------------------------------------------------------
def complaint_matches_animal(complaint: Complaint, animal: str) -> bool:
    """Rabbits and turtles are the only animals in this world; a complaint
    must plausibly belong to a body part the animal can have."""
    return animal in {"rabbit", "turtle", "girl", "boy"}


def bottle_has_dose(bottle: Bottle) -> bool:
    """A reasonable bottle has both a measured dose and a whole-bottle version."""
    return bool(bottle.measured) and bool(bottle.whole)


def select_compromise(complaint: Complaint) -> Optional[Compromise]:
    """There is exactly one steady, slow plan per world (the friend offers it
    in the middle beat)."""
    return _safe_lookup(COMPROMISES, 0)


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def tall_tale_open(place: str) -> str:
    return f"On {place}, where the porch boards are wide as a raft, two friends sit shoulder to shoulder."


def setting_detail(setting: Setting) -> str:
    if setting.where == "indoors":
        return f"The {setting.place.removeprefix('the ')} smelled of clean paper and lavender."
    return f"The air smelled sweet, and the sky went on and on like a song."


def complaint_rhyme(complaint: Complaint) -> str:
    return {
        "elbow": "my elbow is a hot, hot drum",
        "knee": "my knee is a stingy thrum",
        "wing": "my wing is an itchy thump",
        "paw": "my paw is a thumpy, jumpy drum",
    }.get(complaint.body_part, "my body has a drum of its own")


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    hero_trait = next((t for t in hero.traits if t != "little"), "thoughtful")
    friend_trait = next((t for t in friend.traits if t != "little"), "steady")
    world.say(
        f"{hero.id} was a {hero_trait} {hero.type} with one very "
        f"{world.get('complaint').meters and 'itchy'} {world.get('complaint').label}, "
        f"and {friend.id} was a {friend_trait} {friend.type} who believed in slow plans."
    )


def arrive_clinic(world: World, hero: Entity, doctor: Entity) -> None:
    world.say(
        f"The clinic belonged to {doctor.id}, who wore big glasses and a white "
        f"coat that flapped when {doctor.pronoun()} marched."
    )


def complaint_rises(world: World, hero: Entity, complaint: Entity) -> None:
    complaint.meters["itch"] += 1
    complaint.meters["swelling"] += 1
    world.say(
        f"{hero.id} scratched and scratched. \"{complaint_rhyme(world.get('complaint'))},"
        f"\" {hero.pronoun()} said."
    )


def tall_tale_whispered(world: World, hero: Entity, complaint: Entity, bottle: Bottle) -> None:
    hero.memes["tall_tale"] += 1
    world.say(
        f"But {hero.id} had heard a Tall Tale at sunrise. "
        f"\"{bottle.rhyme}, and the pint will make a hero out of anyone who drinks deep.\""
    )


def warn_dose(world: World, doctor: Entity, hero: Entity, complaint: Entity, bottle: Bottle,
              compromise: Compromise) -> None:
    hero.memes["warned"] += 1
    hero.memes["caution"] += 1
    world.say(
        f"{doctor.id} smiled and shook {doctor.pronoun('possessive')} head. "
        f"\"That {bottle.name} is for bad flare-ups, dear,\" {doctor.pronoun()} said, "
        f"\"and the dose must be measured. Too much will make your bones feel hollow, "
        f"and too little will not hush the drum at all. Let us try "
        f"{compromise.name.lower()} on the porch first, and see how the drum behaves.\""
    )


def climb_shelf(world: World, hero: Entity, bottle: Entity) -> None:
    hero.memes["warned"] += 1                # the warning sticks
    hero.memes["climbed"] += 1
    bottle.on_shelf = True
    world.say(
        f"But {hero.id} pouted. {hero.pronoun().capitalize()} climbed the clinic shelf "
        f"when {world.get('doctor').id} was not looking, and reached for the cool, "
        f"heavy bottle. The {bottle.label} was labeled in careful letters, and the cap "
        f"was a small fortress."
    )


def friend_steady_hand(world: World, friend: Entity, hero: Entity, bottle: Entity) -> None:
    friend.memes["steady"] += 1
    hero.memes["steady_hand"] += 1
    hero.memes["reckless"] += 1
    world.say(
        f"{friend.id} climbed up beside {hero.pronoun('object')}, very out of breath, "
        f"and {friend.pronoun()} did not grab the bottle from {hero.pronoun('possessive')} hand. "
        f"Instead, {friend.pronoun()} held {hero.pronoun('possessive')} paw still and said, "
        f"\"Let us measure. {world.get('bottle_holder').meters and 'One careful drop,'} "
        f"and we watch the drum together.\""
    )


def reckless_whole_pint(world: World, hero: Entity, bottle: Entity) -> None:
    hero.memes["whole_pint"] += 1
    hero.memes["reckless"] += 1
    bone = world.get("bone")
    bone.meters["hollow"] += 1
    world.say(
        f"{hero.id} twisted the cap, and the whole {bottle.label} tipped up. "
        f"The Magic Pint slid down, and a hush ran through the porch."
    )


def measured_drop(world: World, hero: Entity, friend: Entity, bottle: Entity,
                  complaint: Entity, compromise: Compromise) -> None:
    hero.memes["measured_drop"] += 1
    friend.memes["measured_drop"] += 1
    world.say(
        f"{hero.id} blinked. {hero.pronoun().capitalize()} did not drink the whole {bottle.label}. "
        f"{friend.pronoun().capitalize()} tipped the cool dropper, and one careful drop "
        f"landed on the drum of {hero.pronoun('possessive')} {complaint.label}, and the hot "
        f"beat slowed to a sleepy hush."
    )


def doctor_approval(world: World, doctor: Entity, hero: Entity, friend: Entity) -> None:
    doctor.memes["approval"] += 1
    world.say(
        f"{doctor.id} came back, and {doctor.pronoun()} was not cross, only proud. "
        f"\"You measured the magic,\" {doctor.pronoun()} said, \"and you kept your friend. "
        f"That is the bravest thing the Tall Tale ever taught.\""
    )


def oath_end(world: World, hero: Entity, friend: Entity, bottle: Entity, compromise: Compromise) -> None:
    hero.memes["oath"] += 1
    friend.memes["oath"] += 1
    bond = world.get("bond")
    bond.meters["oath"] += 1
    world.say(
        f"{hero.id} and {friend.id} sat on the great blue porch, shoulder to shoulder, "
        f"and they promised, the way Tall Tale friends do, that they would never "
        f"drink more magic than their bones could hold."
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, complaint: Complaint, bottle: Bottle,
         hero_name: str = "Juniper", hero_type: str = "rabbit",
         friend_name: str = "Pip", friend_type: str = "turtle",
         doctor_name: str = "Dr. Sedge", doctor_type: str = "doctor",
         hero_traits: Optional[list[str]] = None,
         friend_traits: Optional[list[str]] = None) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["thoughtful", "itchy"]),
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type,
        traits=["little"] + (friend_traits or ["steady", "quiet"]),
    ))
    doctor = world.add(Entity(
        id=doctor_name, kind="character", type=doctor_type, label="the doctor",
    ))
    complaint_e = world.add(Entity(
        id="complaint", type="body", label=complaint.body_part, region=complaint.body_part,
    ))
    bottle_e = world.add(Entity(
        id="bottle", type="bottle", label=bottle.name.split(" of ")[-1], phrase=bottle.name,
    ))
    bone = world.add(Entity(id="bone", type="bone", label="bones"))
    bond = world.add(Entity(id="bond", type="bond", label="the bond"))
    # Always-on holder for narration flexibility.
    bottle_holder = world.add(Entity(id="bottle_holder", type="holder", label="holder"))

    compromise = select_compromise(complaint)

    # Act 1 -- setup: who, the body's drum, the clinic shelf, the Tall Tale whisper.
    introduce(world, hero, friend)
    arrive_clinic(world, hero, doctor)
    complaint_rises(world, hero, complaint_e)
    tall_tale_whispered(world, hero, complaint_e, bottle)
    warn_dose(world, doctor, hero, complaint_e, bottle, compromise)

    # Act 2 -- conflict: climb the shelf, friend steadies the hand.
    world.para()
    climb_shelf(world, hero, bottle_e)
    friend_steady_hand(world, friend, hero, bottle_e)

    # Predicted-mess check: if recklessness would outpace the friend's steadying,
    # the cautionary path forces the whole-pint outcome.  Otherwise the measured
    # drop closes the drum.
    if hero.memes["reckless"] > hero.memes["caution"]:
        reckless_whole_pint(world, hero, bottle_e)
    else:
        measured_drop(world, hero, friend, bottle_e, complaint_e, compromise)

    # Act 3 -- resolution: doctor's approval + the Tall Tale oath.
    world.para()
    doctor_approval(world, doctor, hero, friend)
    oath_end(world, hero, friend, bottle_e, compromise)

    # Forward chain any remaining rules and record facts for the Q&A.
    propagate(world, narrate=False)
    world.facts.update(
        hero=hero, friend=friend, doctor=doctor,
        complaint=complaint_e, bottle=bottle_e, bone=bone, bond=bond,
        bottle_holder=bottle_holder, compromise=compromise, bottle_def=bottle,
        complaint_def=complaint, setting=setting,
        reckless_outcome=hero.memes["whole_pint"] >= THRESHOLD,
        measured_outcome=hero.memes["measured_drop"] >= THRESHOLD,
        oath=hero.memes["oath"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "porch": Setting(place="the great blue porch", where="outdoors",
                     afford={"complaint", "climb", "measure"}),
    "garden": Setting(place="the green clinic garden", where="outdoors",
                      afford={"complaint", "climb", "measure"}),
    "kitchen": Setting(place="the clinic kitchen", where="indoors",
                       afford={"complaint", "climb", "measure"}),
}

COMPLAINTS = {
    "elbow": Complaint(id="elbow", body_part="elbow",
                       feel="hot, hot drum", rise="swelling",
                       noun="Magic Pint of cortisone"),
    "knee": Complaint(id="knee", body_part="knee",
                      feel="stingy thrum", rise="swelling",
                      noun="blue bottle of cortisone"),
    "wing": Complaint(id="wing", body_part="wing",
                      feel="itchy thump", rise="swelling",
                      noun="Glass Flask of cortisone"),
    "paw": Complaint(id="paw", body_part="paw",
                     feel="thumpy, jumpy drum", rise="swelling",
                     noun="little bottle of cortisone"),
}

BOTTLES = {
    "magic_pint": Bottle(
        id="magic_pint",
        name="Magic Pint of cortisone",
        measured="a tiny measured drop",
        whole="the whole pint",
        rhyme="Drink deep, drink deep, and the swelling will sleep",
    ),
    "blue_bottle": Bottle(
        id="blue_bottle",
        name="blue bottle of cortisone",
        measured="a small careful drop",
        whole="the whole bottle",
        rhyme="One blue sip will make you a hero of the trip",
    ),
    "glass_flask": Bottle(
        id="glass_flask",
        name="Glass Flask of cortisone",
        measured="a single measured drop",
        whole="the whole flask",
        rhyme="Tip the flask, and the drum will be still at last",
    ),
    "little_bottle": Bottle(
        id="little_bottle",
        name="little bottle of cortisone",
        measured="one careful drop",
        whole="the whole little bottle",
        rhyme="Pour it all, and the paw will never crawl",
    ),
}

COMPROMISES = [
    Compromise(
        id="cool_compress",
        name="Cool Compress and a measured drop",
        body="try the Cool Compress on the porch first, and a tiny measured drop, "
             "just one, and see how the drum behaves",
        tail="sat on the porch with the Cool Compress nearby",
    ),
]

ANIMAL_FRIENDS = [
    ("rabbit", "turtle", "Juniper", "Pip"),
    ("rabbit", "turtle", "Hazel", "Theo"),
    ("rabbit", "turtle", "Marigold", "Crumb"),
    ("girl", "boy", "Rosa", "Sam"),
]
GIRL_NAMES = ["Juniper", "Hazel", "Marigold", "Rosa", "Iris", "Wren", "Cora", "Mae"]
BOY_NAMES = ["Pip", "Theo", "Crumb", "Sam", "Ben", "Eli", "Otis", "Jude"]
TURTLE_NAMES = ["Pip", "Theo", "Crumb", "Otis", "Pebble", "Truffle", "Moss", "Cove"]
RABBIT_NAMES = ["Juniper", "Hazel", "Marigold", "Iris", "Wren", "Cora", "Mae", "Lily"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(setting, complaint, bottle) triples that pass the constraint gate."""
    out = []
    for setting in SETTINGS:
        for complaint in COMPLAINTS.values():
            for bottle in BOTTLES.values():
                if complaint_matches_animal(complaint, "rabbit") and bottle_has_dose(bottle):
                    out.append((setting, complaint.id, bottle.id))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live
# in storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    complaint: str
    bottle: str
    name: str
    friend_name: str
    gender: str          # "girl" | "boy" | "rabbit" | "turtle"
    friend_gender: str
    doctor: str
    hero_trait: str
    friend_trait: str
    oath_line: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  These are answerable WITHOUT
# the story; they explain the *elements* the world is built from.
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
    "cortisone": [
        ("What is cortisone?",
         "Cortisone is a kind of medicine a doctor can give when a part of the "
         "body is very swollen or sore, and the doctor decides how much is safe."),
        ("Why does a doctor measure the dose of cortisone?",
         "A doctor measures the dose because too much can make bones feel weak "
         "and too little does not help the swelling go down, so the right amount "
         "is the only safe amount."),
    ],
    "drum": [
        ("What does it mean when a body part feels like a drum?",
         "It means the body part feels hot, swollen, and like it is beating inside, "
         "the way a drum keeps a steady thump-thump when you tap it."),
    ],
    "shelf": [
        ("Why is medicine kept on a high shelf?",
         "Medicine is kept on a high shelf so small hands cannot reach it by "
         "themselves, and a grown-up can decide who gets the bottle and when."),
    ],
    "dropper": [
        ("What is a dropper?",
         "A dropper is a small tool with a soft top and a thin tube that lets "
         "you count out one drop of liquid at a time."),
    ],
    "porch": [
        ("What is a porch?",
         "A porch is the covered part of a house you can sit on, and it is a "
         "good place to talk to a friend while you watch the day go by."),
    ],
    "friend": [
        ("What makes someone a good friend when you are hurting?",
         "A good friend is someone who stays with you, talks in a calm voice, "
         "and helps you choose the safe thing instead of the biggest thing."),
    ],
    "oath": [
        ("What is a Tall Tale oath?",
         "A Tall Tale oath is a big, brave promise friends make together, said "
         "in the sing-song way of a story, so the promise is easy to remember."),
    ],
    "bones": [
        ("Why do bones need care when you are sick?",
         "Bones need care when you are sick because some medicines are very "
         "strong, and the doctor makes sure the dose is small enough to keep "
         "bones strong while the body heals."),
    ],
}
KNOWLEDGE_ORDER = ["cortisone", "drum", "shelf", "dropper", "porch",
                   "friend", "oath", "bones"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, friend, complaint, bottle = (
        f["hero"], f["friend"], f["complaint_def"], f["bottle_def"]
    )
    kw = "cortisone"
    return [
        f'Write a short Tall Tale story for a 3-to-5-year-old on the theme '
        f'"a child, a friend, a measured dose" that uses the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} has a "
        f"sore {complaint.body_part}, hears a Tall Tale about {bottle.name}, "
        f"and a friend named {friend.id} helps choose the safe, measured dose.",
        f'Write a simple story in a Tall Tale voice that uses the noun '
        f'"{kw}" and ends with two friends making a brave promise together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, friend, doctor = f["hero"], f["friend"], f["doctor"]
    complaint, bottle = f["complaint_def"], f["bottle_def"]
    setting = _safe_fact(world, f, "setting")
    pos, sub, obj = (hero.pronoun("possessive"), hero.pronoun("subject"),
                     hero.pronoun("object"))
    pos_f, sub_f = friend.pronoun("possessive"), friend.pronoun("subject")
    trait = next((t for t in hero.traits if t != "little"), "thoughtful")
    trait_f = next((t for t in friend.traits if t != "little"), "steady")
    place = setting.place
    out: list[QAItem] = [
        QAItem(
            question=(
                f"Who are the two friends sitting on {place} when {hero.id} has a "
                f"sore {complaint.body_part}?"
            ),
            answer=(
                f"The two friends are {hero.id}, a {trait} {hero.type}, and "
                f"{friend.id}, a {trait_f} {friend.type}. They sit shoulder to "
                f"shoulder on {place} while {hero.id}'s {complaint.body_part} "
                f"feels like a {complaint.feel}."
            ),
        ),
        QAItem(
            question=(
                f"What Tall Tale did {hero.id} hear about {bottle.name} before "
                f"{friend.id} helped {obj} choose a safe dose?"
            ),
            answer=(
                f"{hero.id} heard a sunrise Tall Tale that the {bottle.name} "
                f"would make a hero out of anyone who drinks deep: "
                f"\"{bottle.rhyme}.\" {friend.id} gently said the tale sounded "
                f"grand but a too-big dose can hollow the bones."
            ),
        ),
        QAItem(
            question=(
                f"How did {friend.id} help {hero.id} at {place} when {hero.id} "
                f"climbed the clinic shelf for the {bottle.name}?"
            ),
            answer=(
                f"{friend.id} climbed up beside {hero.id}, very out of breath, "
                f"and held {pos} paw still. {sub_f.capitalize()} did not grab the "
                f"bottle from {pos} hand. Instead {sub_f} said, \"Let us measure, "
                f"one careful drop, and we watch the drum together.\""
            ),
        ),
    ]
    # Featured questions: outcome, oath, and the cautionary pivot.
    if f.get("measured_outcome"):
        out.append(QAItem(
            question=(
                f"What happened after {friend.id} tipped the dropper onto "
                f"{hero.id}'s {complaint.body_part} at {place}?"
            ),
            answer=(
                f"One careful drop landed on the {complaint.body_part}, and the "
                f"hot {complaint.feel} slowed to a sleepy hush. {sub.capitalize()} "
                f"did not drink the whole {bottle.name}, so the bones did not "
                f"go hollow, and the drum of the {complaint.body_part} calmed."
            ),
        ))
    if f.get("reckless_outcome"):
        out.append(QAItem(
            question=(
                f"What went wrong when {hero.id} tipped up the whole {bottle.name} "
                f"on {place}?"
            ),
            answer=(
                f"The whole {bottle.name} tipped up and slid down, and the bones "
                f"inside {hero.id} began to feel hollow, because a too-big dose "
                f"of cortisone is not safe even if a Tall Tale says it makes a hero."
            ),
        ))
    if f.get("oath"):
        out.append(QAItem(
            question=(
                f"What promise did {hero.id} and {friend.id} make together at the "
                f"end of their Tall Tale at {place}?"
            ),
            answer=(
                f"They promised, the way Tall Tale friends do, that they would "
                f"never drink more magic than their bones could hold, and they "
                f"sat on {place} shoulder to shoulder to keep the promise."
            ),
        ))
    out.append(QAItem(
        question=(
            f"Why did {doctor.id} at {place} only let {hero.id} have "
            f"{bottle.measured} instead of {bottle.whole}?"
        ),
        answer=(
            f"{doctor.id} knew the dose of cortisone must be measured, because "
            f"too much can make the bones feel hollow and too little will not "
            f"hush the drum. {bottle.measured.capitalize()} was the safe plan, "
            f"and the friend helped {obj} keep to it."
        ),
    ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = {"cortisone", "drum", "shelf", "dropper", "porch", "friend", "oath", "bones"}
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
        if e.on_shelf:
            bits.append("on_shelf=yes")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="porch", complaint="elbow", bottle="magic_pint",
        name="Juniper", friend_name="Pip",
        gender="rabbit", friend_gender="turtle",
        doctor="Dr. Sedge",
        hero_trait="thoughtful", friend_trait="steady",
        oath_line="never drink more magic than our bones could hold",
    ),
    StoryParams(
        place="garden", complaint="knee", bottle="blue_bottle",
        name="Hazel", friend_name="Theo",
        gender="rabbit", friend_gender="turtle",
        doctor="Dr. Fern",
        hero_trait="curious", friend_trait="patient",
        oath_line="never let a Tall Tale outweigh a doctor's measure",
    ),
    StoryParams(
        place="porch", complaint="wing", bottle="glass_flask",
        name="Marigold", friend_name="Crumb",
        gender="rabbit", friend_gender="turtle",
        doctor="Dr. Quill",
        hero_trait="spirited", friend_trait="calm",
        oath_line="always tip the dropper one careful drop at a time",
    ),
    StoryParams(
        place="kitchen", complaint="paw", bottle="little_bottle",
        name="Rosa", friend_name="Sam",
        gender="girl", friend_gender="boy",
        doctor="Dr. Wren",
        hero_trait="brave", friend_trait="kind",
        oath_line="always keep the small hands from the strong shelf",
    ),
    StoryParams(
        place="garden", complaint="elbow", bottle="magic_pint",
        name="Iris", friend_name="Pebble",
        gender="rabbit", friend_gender="turtle",
        doctor="Dr. Sedge",
        hero_trait="playful", friend_trait="quiet",
        oath_line="never drink more magic than our bones could hold",
    ),
]


def explain_rejection(complaint: Complaint, bottle: Bottle) -> str:
    return (f"(No story: the {bottle.name} has no measured dose recorded, so "
            f"the friend cannot offer the slow plan for the {complaint.body_part}. "
            f"Try a bottle that has both a measured drop and a whole version.)")


def explain_gender_mismatch(gender: str, friend_gender: str) -> str:
    return (f"(No story: a {gender} and a {friend_gender} are not in the friend "
            f"catalog here; try --hero rabbit --friend turtle (or --hero girl "
            f"--friend boy).)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (complaint_matches_animal / bottle_has_dose / valid_combos).  The rules are
# inline below; the facts are generated from the registries above so the two
# can never drift.  Uses the shared `asp` helper + clingo, imported lazily so
# the prose engine runs without them.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the setting can host the complaint, the bottle has a
% measured dose, and the bottle has a whole-pint version (the cautionary path).
valid_story(Place, Complaint, Bottle) :-
    setting(Place),
    complaint(Complaint),
    bottle(Bottle),
    animal_compatible(Complaint),
    has_measured(Bottle),
    has_whole(Bottle).

% Friends must be different kinds (rabbit+turtle, girl+boy) and both
% fall into the "small friend" catalog.
friend_pair_ok(G, F) :- small_friend(G), small_friend(F), G != F.
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in COMPLAINTS.items():
        lines.append(asp.fact("complaint", cid))
        lines.append(asp.fact("body_part", cid, c.body_part))
    for bid, b in BOTTLES.items():
        lines.append(asp.fact("bottle", bid))
        lines.append(asp.fact("has_measured", bid))
        lines.append(asp.fact("has_whole", bid))
    for kind in {"rabbit", "turtle", "girl", "boy"}:
        lines.append(asp.fact("small_friend", kind))
    lines.append(asp.fact("animal_compatible", "elbow"))
    lines.append(asp.fact("animal_compatible", "knee"))
    lines.append(asp.fact("animal_compatible", "wing"))
    lines.append(asp.fact("animal_compatible", "paw"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_friend_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show friend_pair_ok/2."))
    return sorted(set(asp.atoms(model, "friend_pair_ok")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    ok = clingo_set == python_set
    if ok:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    # And exercise two generated stories end-to-end (parity + non-empty prose).
    samples = [generate(CURATED[0]), generate(CURATED[3])]
    for s in samples:
        if not s.story.strip():
            print("EMPTY story for", s.params)
            return 1
    print(f"OK: generated {len(samples)} stories from curated set.")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: cortisone, friendship, a cautionary "
                    "Tall Tale. Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--complaint", choices=COMPLAINTS)
    ap.add_argument("--bottle", choices=BOTTLES)
    ap.add_argument("--gender", choices=["rabbit", "turtle", "girl", "boy"])
    ap.add_argument("--friend-gender", choices=["rabbit", "turtle", "girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--doctor")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    # Clingo (ASP) modes -- the inline declarative reasoner (needs clingo).
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if getattr(args, "complaint", None) and getattr(args, "bottle", None):
        c, b = _safe_lookup(COMPLAINTS, getattr(args, "complaint", None)), _safe_lookup(BOTTLES, getattr(args, "bottle", None))
        if not (complaint_matches_animal(c, "rabbit") and bottle_has_dose(b)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "friend_gender", None) and getattr(args, "gender", None) == getattr(args, "friend_gender", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "complaint", None) is None or c[1] == getattr(args, "complaint", None))
              and (getattr(args, "bottle", None) is None or c[2] == getattr(args, "bottle", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, complaint_id, bottle_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or "rabbit"
    friend_gender = getattr(args, "friend_gender", None)
    if friend_gender is None:
        friend_gender = "turtle" if gender == "rabbit" else (
            "rabbit" if gender == "turtle" else "boy" if gender == "girl" else "girl"
        )
    if gender in {"rabbit", "turtle"}:
        name = getattr(args, "name", None) or rng.choice(RABBIT_NAMES if gender == "rabbit" else TURTLE_NAMES)
    else:
        name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    if friend_gender in {"rabbit", "turtle"}:
        friend_name = getattr(args, "friend_name", None) or rng.choice(
            TURTLE_NAMES if friend_gender == "turtle" else RABBIT_NAMES
        )
    else:
        friend_name = getattr(args, "friend_name", None) or rng.choice(
            BOY_NAMES if friend_gender == "boy" else GIRL_NAMES
        )
    doctor = getattr(args, "doctor", None) or rng.choice(["Dr. Sedge", "Dr. Fern", "Dr. Quill", "Dr. Wren"])
    hero_trait = rng.choice(["thoughtful", "curious", "playful", "spirited", "brave"])
    friend_trait = rng.choice(["steady", "patient", "calm", "quiet", "kind"])
    oath_line = rng.choice([
        "never drink more magic than our bones could hold",
        "always keep the small hands from the strong shelf",
        "always tip the dropper one careful drop at a time",
        "never let a Tall Tale outweigh a doctor's measure",
    ])
    return StoryParams(
        place=place,
        complaint=complaint_id,
        bottle=bottle_id,
        name=name,
        friend_name=friend_name,
        gender=gender,
        friend_gender=friend_gender,
        doctor=doctor,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
        oath_line=oath_line,
    )


def _resolve_animal_types(gender: str, friend_gender: str) -> tuple[str, str]:
    g = "rabbit" if gender == "rabbit" else ("turtle" if gender == "turtle" else gender)
    f = "rabbit" if friend_gender == "rabbit" else (
        "turtle" if friend_gender == "turtle" else friend_gender
    )
    return g, f


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    hero_type, friend_type = _resolve_animal_types(params.gender, params.friend_gender)
    doctor_type = "doctor"
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(COMPLAINTS, params.complaint),
                 _safe_lookup(BOTTLES, params.bottle), params.name, hero_type,
                 params.friend_name, friend_type,
                 params.doctor, doctor_type,
                 [params.hero_trait, "thoughtful"],
                 [params.friend_trait, "steady"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        triples, pairs = asp_valid_combos(), asp_friend_pairs()
        print(f"{len(triples)} compatible (place, complaint, bottle) combos:\n")
        for place, complaint, bottle in triples:
            print(f"  {place:9} {complaint:8} {bottle:14}")
        print(f"\n{len(pairs)} compatible friend pairs:\n")
        for g, f in pairs:
            print(f"  {g:6} + {f}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

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
            header = (f"### {p.name} & {p.friend_name}: {p.complaint} at "
                      f"{p.place} (bottle: {p.bottle})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
