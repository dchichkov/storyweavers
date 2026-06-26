#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/maternal_cantina_sweetum_dialogue_rhyming_story.py
=============================================================================================================================

A standalone *story world* for a TinyStories-style domain: a warm little
cantina, a maternal cook, a sweet treat called a "sweetum", and a gentle
dialogue that resolves a small craving-vs-cleanup conflict in rhyming prose.

Initial story (used to seed the world model):
---
Mama Rosa ran the cantina on the corner of Maple and Vine. Every morning
she swept the floor, polished the counter, and set out three little cups
of sweetum on the highest shelf. Sweetum was her special treat -- warm
syrup drizzled over soft bread, dusted with cinnamon -- and the children
of the town knew its sticky, sweet smell from two streets away.

One bright morning, little Mira tiptoed in. She loved sweetum more than
anything, but she had just been given a brand new blue dress with a white
collar, and Mama Rosa shook her head with a worried smile.

"If you sit at the counter, your pretty dress will wear a sticky stripe,
and then I will have to wash it before the town parade," Mama Rosa said.
But Mira did want a sweetum, and so she asked very politely...

From that polite question, a rhyming conversation grew, and the two of
them found a clever way for Mira to enjoy her treat without spoiling the
new dress. The story world below simulates this exchange as a small typed
universe of characters, treats, garments, and a sequence of dialogue
beats, and renders it in a gentle rhyming style for a 3-to-5-year-old.

Causal state updates (meters + memes):
---
    child says please             -> child.memes.politeness += 1
    child promises careful        -> child.memes.promise += 1
    child accepts smock            -> child.memes.joy += 1
    sweetum gets on dress          -> dress.meters.sticky += 1
                                      dress.meters.dirty  += 1
                                      mama.meters.workload += 1     (more wash)
    child wears smock + takes treat-> dress stays clean (smock covers torso)

Dialogue shape (rhyming, two voices):
---
    Mama's lines end in -ight, -ay, -ee, -own, -ime words (gentle open vowels)
    Mira's lines end in -um, -ee, -ain, -ing words (rounded, childlike)
    The two lines share a rhyme word or a rhyme scheme.
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

# Make the shared result containers importable when this script is run directly.
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# A small, kid-friendly rhyme vocabulary. Each entry pairs a rhyme word with
# 2-3 short, rhyming lines (4 to 7 words) for a given speaker. Lines are
# intentionally short -- children can follow them, and the constraints are
# easier to satisfy honestly.
RHYME_A = "time"
RHYME_B = "day"
RHYME_C = "sweet"
RHYME_D = "shine"


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
    type: str = "thing"            # mother, girl, dress, smock ...
    label: str = ""                # short reference, e.g. "dress", "smock"
    phrase: str = ""               # full noun phrase, e.g. "a new blue dress"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""               # feet | legs | torso | ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    garment: object | None = None
    mama: object | None = None
    smock_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mama", "father": "papa"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
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
    name: str
    place_phrase: str
    detail: str
    indoor: bool = True
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
class Treat:
    """The sweet treat the child craves (always a 'sweetum' variant here)."""
    id: str
    label: str              # "sweetum", "little sweetum"
    spill: str              # the mess kind on the dress: "sticky"
    spill_phrase: str       # "sticky syrup drizzles down the front"
    zone: set[str]          # body regions the treat can reach: {"torso"}
    keyword: str = "sweetum"
    tags: set[str] = field(default_factory=set)
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
class Garment:
    """The nice clothing the child wears, that the treat would ruin."""
    label: str
    phrase: str
    type: str               # "dress", "shirt", "apron", "blouse"
    region: str             # torso
    plural: bool = False
    colors: list[str] = field(default_factory=list)
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
class Smock:
    """The protective covering offered as the compromise."""
    id: str
    label: str
    color: str
    covers: set[str]
    guards: set[str]        # mess kinds it neutralises
    prep: str               # the offer body
    tail: str               # the closing narration


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
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
        self.lines: list[str] = []      # story prose, paragraph by paragraph
        self.dialogue: list[tuple[str, str]] = []  # (speaker, line) tuples
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def speak(self, speaker: Entity, line: str) -> None:
        """Record a dialogue line in the world's dialogue log."""
        self.dialogue.append((speaker.id, line))

    def render(self) -> str:
        # Join the prose paragraphs and intersperse the dialogue.
        out: list[str] = []
        # Setup paragraph(s) from self.lines, then dialogue beats.
        chunk: list[str] = []
        for entry in self.lines:
            if entry == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
                out.append("")
            else:
                chunk.append(entry)
        if chunk:
            out.append(" ".join(chunk))
        # Append a dedicated dialogue section so the rhymes are unambiguous.
        if self.dialogue:
            if out and out[-1] != "":
                out.append("")
            out.append('"Let\'s talk it through," Mama Rosa said with a grin.')
            for speaker, line in self.dialogue:
                out.append(f'  {speaker} sang, "{line}"')
        # Drop the first element if it's an empty leading chunk.
        if out and out[0] == "":
            out = out[1:]
        return "\n".join(out).strip()

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        clone.dialogue = list(self.dialogue)
        clone.lines = list(self.lines)
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


def _r_spill(world: World) -> list[str]:
    """Treat messy + worn item in the splash zone & uncovered -> sticky + dirty."""
    out: list[str] = []
    for actor in world.characters():
        for mess in {"sticky", "sugary", "syrupy"}:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("spill", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and dirty."
                )
    return out


def _r_workload(world: World) -> list[str]:
    """A garment that is dirty -> its caretaker has more washing work."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more washing for {carer.label}.")
    return out


def _r_compliance(world: World) -> list[str]:
    """Polite request + smock accepted + joyful -> child compliance embedded."""
    for actor in world.characters():
        if actor.memes["politeness"] < THRESHOLD:
            continue
        if actor.memes["joy"] < THRESHOLD:
            continue
        sig = ("compliance", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["compliance"] += 1
        return []
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="compliance", tag="social", apply=_r_compliance),
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


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def treat_at_risk(treat: Treat, garment: Garment) -> bool:
    """Would this treat actually mess up this garment (right body region)?"""
    return garment.region in treat.zone


def select_smock(treat: Treat, garment: Garment) -> Optional[Smock]:
    """The compatible compromise: a smock that guards the mess AND covers the region."""
    for sm in SMOCKS:
        if treat.spill in sm.guards and garment.region in sm.covers:
            return sm
    return None


def predict_stain(world: World, actor: Entity, treat: Treat, garment_id: str) -> dict:
    sim = world.copy()
    _do_treat(sim, sim.get(actor.id), treat, narrate=False)
    garment = sim.entities.get(garment_id)
    return {
        "stained": bool(garment and garment.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def treat_detail(treat: Treat) -> str:
    return {
        "sweetum": "the sweetum was warm and smelled of cinnamon and rain",
        "little sweetum": "the little sweetum glowed like a soft sunset",
    }.get(treat.id, "the treat smelled warm and sweet")


def setting_detail(setting: Setting) -> str:
    return f'{setting.detail}'


def _do_treat(world: World, actor: Entity, treat: Treat, narrate: bool = True) -> None:
    world.zone = set(treat.zone)
    actor.meters[treat.spill] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, mama: Entity, child: Entity) -> None:
    world.say(
        f"At {world.setting.place_phrase}, {mama.id} was the one who always "
        f"knew the way to make a {child.type} beam."
    )


def loves_treat(world: World, child: Entity, treat: Treat) -> None:
    child.memes["love_treat"] += 1
    world.say(
        f"{child.id} loved {treat.label} more than games, more than songs, "
        f"and {child.pronoun()} thought about it from morning until dusk."
    )
    world.say(treat_detail(treat))


def buys_garment(world: World, mama: Entity, child: Entity, garment: Garment) -> None:
    color = garment.colors[0] if garment.colors else "new"
    world.say(
        f"Last week, {mama.id} had found {child.id} {garment.phrase}, all "
        f"crisp and {color} as a robin's egg."
    )


def loves_garment(world: World, child: Entity, garment: Garment) -> None:
    child.memes["love"] += 1
    garment.worn_by = child.id
    world.say(
        f"{child.id} twirled in {child.pronoun('possessive')} {garment.label} "
        f"and hugged the soft cloth with both small hands."
    )


def arrive(world: World, child: Entity) -> None:
    world.say(
        f"One bright morning, {child.id} tiptoed through the door of the "
        f"{world.setting.name}, where the air smelled of cinnamon and clean wood."
    )
    world.say(setting_detail(world.setting))


def wants(world: World, child: Entity, treat: Treat) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{child.id} peeped up at the counter where the {treat.label} waited, "
        f"and the wanting in {child.pronoun('possessive')} eyes was loud as a drum."
    )


def warn(world: World, mama: Entity, child: Entity, treat: Treat, garment: Garment) -> bool:
    """Mama foresees the mess via the world model and warns about it."""
    pred = predict_stain(world, child, treat, garment.id)
    if not pred["stained"]:
        return False
    world.facts["predicted_stain"] = treat.spill_phrase
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"Your {garment.label} will wear a {treat.spill} stripe"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I will have to wash it"
    world.say(
        f'"{clause}," {mama.id} said kindly. "And I would rather we keep it '
        f'pretty for the parade day."'
    )
    return True


def asks_politely(world: World, child: Entity, mama: Entity, treat: Treat,
                  rhyme: str) -> None:
    child.memes["politeness"] += 1
    line = _rhyme_line(child, ask=True, rhyme=rhyme)
    world.speak(child, line)
    world.say(
        f"{child.id} folded {child.pronoun('possessive')} hands and asked, "
        f"very polite, very small, very sure."
    )


def promises(world: World, child: Entity, treat: Treat, rhyme: str) -> None:
    child.memes["promise"] += 1
    line = _rhyme_line(child, promise=True, rhyme=rhyme)
    world.speak(child, line)
    world.say(
        f"{child.pronoun('subject').capitalize()} promised to be as careful as "
        f"a bee on a petal, with a nod and a half-bow."
    )


def compromise(world: World, mama: Entity, child: Entity, treat: Treat,
               garment: Garment) -> Optional[Smock]:
    sm = select_smock(treat, garment)
    if sm is None:
        return None
    smock_ent = world.add(Entity(
        id=sm.id, type="smock", label=sm.label, owner=child.id, caretaker=mama.id,
        protective=True, covers=set(sm.covers),
    ))
    smock_ent.worn_by = child.id
    if predict_stain(world, child, treat, garment.id)["stained"]:
        # Smock didn't actually help; refuse to claim it.
        smock_ent.worn_by = None
        del world.entities[smock_ent.id]
        return None
    line = _rhyme_line(mama, offer=True, rhyme=treat.keyword)
    world.speak(mama, line)
    world.say(
        f'{mama.id} reached up to the {sm.color} hook by the window and '
        f'brought down {sm.label}, soft as a cloud and ready for work.'
    )
    return sm


def wears_smock(world: World, child: Entity, smock: Smock, rhyme: str) -> None:
    child.memes["acceptance"] += 1
    line = _rhyme_line(child, accept=True, rhyme=rhyme)
    world.speak(child, line)
    world.say(
        f"{child.id} slipped {smock.label} over {child.pronoun('possessive')} "
        f"head and grinned, ready for the morning treat."
    )


def eat(world: World, child: Entity, mama: Entity, treat: Treat, garment: Garment,
        smock: Smock) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    world.facts["joy"] = True
    # The actual treat-time narration -- keeps the garment clean because the
    # smock covers the at-risk region.
    _do_treat(world, child, treat, narrate=False)
    world.say(
        f"Then {child.id} sat on the little stool, held the warm {treat.label} "
        f"with both small hands, and ate every last bite."
    )
    if not garment.meters["dirty"] >= THRESHOLD:
        world.say(
            f"The {smock.label} did its job, and {child.pronoun('possessive')} "
            f"{garment.label} stayed clean and crisp for the parade."
        )
    else:
        world.say(
            f"The {garment.label} wore a {treat.spill} stripe, and {mama.id} "
            f"sighed with a smile -- at least the {treat.label} was loved."
        )


def close(world: World, child: Entity, mama: Entity, rhyme: str) -> None:
    line = _rhyme_line(mama, close=True, rhyme=rhyme)
    world.speak(mama, line)
    line2 = _rhyme_line(child, close=True, rhyme=rhyme)
    world.speak(child, line2)
    world.say(
        f"Outside, the sun climbed high, and the {mama.id} waved {child.id} "
        f"goodbye with a wink and a hum."
    )


# ---------------------------------------------------------------------------
# Rhyme lines -- a tiny, hand-curated library.  The same line is *not* allowed
# to be picked twice within a single story, so each tale has a real mix.
# ---------------------------------------------------------------------------
RHYMES = {
    RHYME_A: {
        "mother_ask": [
            "Would you like a sweetum this rhyme-time?",
            "Shall we share a sweetum at rhyme-time?",
        ],
        "mother_offer": [
            "Slip on this smock, dear, and all will be fine in rhyme-time.",
            "Wear this little smock and we'll manage just fine in rhyme-time.",
        ],
        "mother_close": [
            "Off you go, sweetheart, like a bell at prime-time.",
            "Run along now, little love, like a chime at prime-time.",
        ],
        "girl_ask": [
            "Please may I have a sweetum, just this one time?",
            "Oh Mama, may I taste one, just this one time?",
        ],
        "girl_promise": [
            "I will be careful, and not make a dime of grime this time.",
            "I will eat slow, not a drop of slime this time.",
        ],
        "girl_accept": [
            "I will wear it, Mama, and it will be prime this time.",
            "I will button it up and feel just fine this time.",
        ],
        "girl_close": [
            "Thank you, dear Mama, I will sing like a chime this time.",
            "I love you, Mama, like a bell in its prime this time.",
        ],
    },
    RHYME_B: {
        "mother_ask": [
            "Shall I set a sweetum out for parade day?",
            "Will you sit and have a sweetum on parade day?",
        ],
        "mother_offer": [
            "Wear this little smock and we will make it a bright day.",
            "Try this soft smock and we will turn it just right, day.",
        ],
        "mother_close": [
            "Run along, my darling, and dance in the light of day.",
            "Go play, my dear one, in the soft morning light of day.",
        ],
        "girl_ask": [
            "Please, dear Mama, just a taste today.",
            "May I have a sweetum, just a little taste today?",
        ],
        "girl_promise": [
            "I will not drip, not a single drop, I say, today.",
            "I will eat like a bird, in the gentlest way, today.",
        ],
        "girl_accept": [
            "I will put it on, and we will smile all day.",
            "I will button it up, and we will laugh and play all day.",
        ],
        "girl_close": [
            "Thank you, Mama, I love you more than I can say, today.",
            "I love you, Mama, in my own small way, today.",
        ],
    },
    RHYME_C: {
        "mother_ask": [
            "Would you like a sweetum, my little sweet?",
            "Shall I pour a sweetum for my own little sweet?",
        ],
        "mother_offer": [
            "Tie this little smock and the morning will stay neat and sweet.",
            "Slip on this soft smock and our treat will end neat and sweet.",
        ],
        "mother_close": [
            "Off you go, my dear, with light and loving feet and sweet.",
            "Run along, my love, where the day is warm and sweet.",
        ],
        "girl_ask": [
            "Oh please, dear Mama, may I have a sweet?",
            "Just a little sip, Mama, just a tiny sweet?",
        ],
        "girl_promise": [
            "I will be careful, my hands and my lips discreet and sweet.",
            "I will be slow, Mama, polite and discreet and sweet.",
        ],
        "girl_accept": [
            "I will wear it, Mama, and feel so neat and sweet.",
            "I will button it on and feel so warm and sweet.",
        ],
        "girl_close": [
            "Thank you, Mama, you make my whole world neat and sweet.",
            "I love you, Mama, with both my small feet, sweet.",
        ],
    },
    RHYME_D: {
        "mother_ask": [
            "Would you like a sweetum, my little sunshine?",
            "Shall I pour a sweetum for my morning sunshine?",
        ],
        "mother_offer": [
            "Tie this little smock, dear, and we will both shine.",
            "Slip on this soft smock, love, and the morning will shine.",
        ],
        "mother_close": [
            "Off you go, my darling, like a small bright sign to shine.",
            "Run along, my love, and let your smile shine.",
        ],
        "girl_ask": [
            "Oh please, dear Mama, may I taste a sweet sunshine?",
            "Just one little sweetum, like a soft sunshine?",
        ],
        "girl_promise": [
            "I will be careful, like a small polite sunshine.",
            "I will be still, like a small polite sunshine.",
        ],
        "girl_accept": [
            "I will wear it, Mama, and feel so fine, like sunshine.",
            "I will button it on, and the morning will be fine, like sunshine.",
        ],
        "girl_close": [
            "Thank you, Mama, you make my whole world shine.",
            "I love you, Mama, like a sweet warm shine.",
        ],
    },
}


def _rhyme_line(speaker: Entity, *, ask: bool = False, promise: bool = False,
                accept: bool = False, offer: bool = False, close: bool = False,
                rhyme: str = RHYME_A) -> str:
    """Pick a rhyme line for the speaker. Mark a used rhyme so we don't repeat."""
    is_mama = speaker.type in {"mother", "aunt", "father", "uncle"}
    if ask:
        key = "mother_ask" if is_mama else "girl_ask"
    elif promise:
        key = "girl_promise"
    elif accept:
        key = "girl_accept"
    elif offer:
        key = "mother_offer"
    elif close:
        key = "mother_close" if is_mama else "girl_close"
    else:
        key = "mother_ask" if is_mama else "girl_ask"
    pool = RHYMES.get(rhyme, _safe_lookup(RHYMES, RHYME_A))[key]
    used = speaker.memes.get("_used_rhymes", 0.0) or 0.0
    idx = int(used) % len(pool)
    speaker.memes["_used_rhymes"] = used + 1
    return pool[idx]


# ---------------------------------------------------------------------------
# The screenplay: three acts driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, treat: Treat, garment_cfg: Garment,
         smock: Smock, child_name: str = "Mira", child_type: str = "girl",
         mama_name: str = "Mama Rosa", mama_type: str = "mother",
         rhyme: str = RHYME_A) -> World:
    world = World(setting)

    mama = world.add(Entity(
        id=mama_name, kind="character", type=mama_type,
        label=mama_name.split()[-1].lower() if " " in mama_name else "the cook",
    ))
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type,
        traits=["little", "polite", "hopeful"],
    ))
    garment = world.add(Entity(
        id="garment", type=garment_cfg.type, label=garment_cfg.label,
        phrase=garment_cfg.phrase, owner=child.id, caretaker=mama.id,
        region=garment_cfg.region, plural=garment_cfg.plural,
    ))

    # Act 1 -- setup: who loves the treat, and the new garment to protect.
    introduce(world, mama, child)
    loves_treat(world, child, treat)
    buys_garment(world, mama, child, garment_cfg)
    loves_garment(world, child, garment_cfg)

    # Act 2 -- conflict: desire vs. predicted stain, ending in a polite ask.
    world.para()
    arrive(world, child)
    wants(world, child, treat)
    warn(world, mama, child, treat, garment_cfg)
    asks_politely(world, child, mama, treat, rhyme)
    promises(world, child, treat, rhyme)

    # Act 3 -- resolution: a compatible smock keeps the garment clean.
    world.para()
    sm = compromise(world, mama, child, treat, garment_cfg)
    if sm:
        wears_smock(world, child, sm, rhyme)
        eat(world, child, mama, treat, garment_cfg, sm)
        close(world, child, mama, rhyme)

    # Record facts for the Q&A generators.
    world.facts.update(
        mama=mama, child=child, garment=garment, garment_cfg=garment_cfg,
        treat=treat, smock=sm, rhyme=rhyme, setting=setting,
        conflict=garment.meters["dirty"] < THRESHOLD and not sm,
        resolved=sm is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "cantina": Setting(
        name="cantina",
        place_phrase="Mama Rosa's little cantina on the corner of Maple and Vine",
        detail=("Inside, the floor was scrubbed clean, the counter was polished "
                "warm, and three little cups of sweetum sat on the highest shelf."),
    ),
    "kitchen": Setting(
        name="kitchen",
        place_phrase="the warm kitchen at the back of the house",
        detail=("The kitchen was small and tidy, and a row of copper spoons "
                "hung by the window like a small bright choir."),
    ),
    "bakery": Setting(
        name="bakery",
        place_phrase="the corner bakery with the blue door",
        detail=("The bakery smelled of warm bread and sugar, and a soft bell "
                "jingled every time the door opened wide."),
    ),
}

TREATS = {
    "sweetum": Treat(
        id="sweetum",
        label="sweetum",
        spill="sticky",
        spill_phrase="sticky syrup drizzles down the front",
        zone={"torso"},
        keyword="sweetum",
        tags={"sweetum", "sweet"},
    ),
    "little_sweetum": Treat(
        id="little sweetum",
        label="little sweetum",
        spill="syrupy",
        spill_phrase="a thin ribbon of syrup trails down the front",
        zone={"torso"},
        keyword="sweetum",
        tags={"sweetum", "sweet"},
    ),
}

# Smocks are ordered most-specific first, full-torso fallback last.
SMOCKS = [
    Smock(
        id="bib_smock",
        label="a tiny cotton bib smock",
        color="soft white",
        covers={"torso"},
        guards={"sticky", "syrupy", "sugary"},
        prep="tie this little smock on tight",
        tail="tied on the soft white smock with a quick little bow",
    ),
    Smock(
        id="full_smock",
        label="a long-sleeved smock",
        color="pale blue",
        covers={"torso", "legs"},
        guards={"sticky", "syrupy", "sugary"},
        prep="put on this long-sleeved smock first",
        tail="buttoned up the pale blue smock with care",
    ),
]

GARMENTS = {
    "dress": Garment(
        label="dress",
        phrase="a new blue dress with a white collar",
        type="dress",
        region="torso",
        colors=["blue", "white"],
        genders={"girl"},
    ),
    "blouse": Garment(
        label="blouse",
        phrase="a new white blouse with tiny pearl buttons",
        type="blouse",
        region="torso",
        colors=["white"],
        genders={"girl"},
    ),
    "shirt": Garment(
        label="shirt",
        phrase="a new pale shirt with a small green pocket",
        type="shirt",
        region="torso",
        colors=["pale", "green"],
        genders={"boy", "girl"},
    ),
    "apron_dress": Garment(
        label="apron-dress",
        phrase="a new apron-dress with a stitched hem",
        type="apron-dress",
        region="torso",
        colors=["striped", "soft"],
        genders={"girl"},
    ),
}

GIRL_NAMES = ["Mira", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
MAMA_NAMES = ["Mama Rosa", "Mama Lila", "Mama June", "Mama Belle", "Mama Cora"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(setting, treat, garment) triples that pass the reasonableness constraint."""
    combos = []
    for sid, _ in SETTINGS.items():
        for tid, t in TREATS.items():
            for gid, g in GARMENTS.items():
                if treat_at_risk(t, g) and select_smock(t, g):
                    combos.append((sid, tid, gid))
    return combos


def valid_stories() -> list[tuple[str, str, str, str]]:
    """Gender-aware compatible stories: (setting, treat, garment, gender)."""
    out = []
    for sid, tid, gid in valid_combos():
        for gender in sorted(_safe_lookup(GARMENTS, gid).genders):
            out.append((sid, tid, gid, gender))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    treat: str
    garment: str
    name: str
    gender: str
    mama: str
    rhyme: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
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


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    child, mama, treat = f["child"], f["mama"], f["treat"]
    garment = _safe_fact(world, f, "garment_cfg")
    return [
        f'Write a short rhyming story for a 3-to-5-year-old on the theme "a '
        f'maternal cook, a polite child, a sweet treat" that includes the word '
        f'"{treat.keyword}".',
        f"Tell a gentle rhyming story where {mama.id} serves {child.id} a "
        f"{treat.label} at the {f['setting'].name}, but {mama.id} worries "
        f"about {garment.phrase}. The two of them find a kind compromise in "
        f"tidy rhymes.",
        f'Write a simple story in short rhyming lines that uses the noun '
        f'"{treat.keyword}" and ends with {mama.id} and {child.id} waving '
        f"goodbye from a clean counter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    child, mama, treat = f["child"], f["mama"], f["treat"]
    garment = _safe_fact(world, f, "garment_cfg")
    sub, obj, pos = (child.pronoun("subject"), child.pronoun("object"),
                     child.pronoun("possessive"))
    place = _safe_fact(world, f, "setting").place_phrase
    sm = f.get("smock")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Where does {child.id} go to ask for a {treat.label} on the "
                f"morning {pos} {garment.label} is new?"
            ),
            answer=(
                f"{child.id} tiptoes into {place}, where the air smells of "
                f"cinnamon and clean wood and the {treat.label} waits on the "
                f"highest shelf."
            ),
        ),
        QAItem(
            question=(
                f"What does {child.id} love more than games and songs before "
                f"the polite question at the {f['setting'].name}?"
            ),
            answer=(
                f"{sub.capitalize()} loves the {treat.label} more than games "
                f"and more than songs, and thinks about it from morning until "
                f"dusk."
            ),
        ),
        QAItem(
            question=(
                f"What is the new {garment.label} that {mama.id} found for "
                f"{child.id} last week?"
            ),
            answer=(
                f"It is {garment.phrase}, crisp and {garment.colors[0] if garment.colors else 'new'} "
                f"as a robin's egg, and {child.id} twirled in it before "
                f"walking to the {f['setting'].name}."
            ),
        ),
    ]
    if f.get("conflict") or f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"Why does {mama.id} first say no when {child.id} wants the "
                f"{treat.label}?"
            ),
            answer=(
                f"{mama.id} foresees the mess and worries that {pos} "
                f"{garment.label} would wear a {treat.spill} stripe, which "
                f"would mean more washing for {mama.id} before the parade."
            ),
        ))
    if f.get("resolved") and sm:
        sm_label = sm.label
        if sm_label.startswith(("a ", "an ")):
            sm_label = sm_label.split(" ", 1)[1]
        qa.append(QAItem(
            question=(
                f"How does {sm.label} help {child.id} enjoy the {treat.label} "
                f"without ruining {pos} {garment.label}?"
            ),
            answer=(
                f"{mama.id} offers {sm.label}, and {child.id} ties it on "
                f"before sitting at the counter. The smock covers the "
                f"at-risk region, so {pos} {garment.label} stays clean for "
                f"the parade."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How does {child.id} feel after {mama.id} agrees to the "
                f"smock plan at the {f['setting'].name}?"
            ),
            answer=(
                f"{sub.capitalize()} feels joyful and grateful, and the two "
                f"share a little rhyming goodbye as {sub} heads out into the "
                f"morning."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    return [
        QAItem(
            question="What is a sweetum?",
            answer=(
                "A sweetum is a warm, sweet treat, often soft bread soaked in "
                "syrup and dusted with cinnamon."
            ),
        ),
        QAItem(
            question="What is a cantina?",
            answer=(
                "A cantina is a small, friendly place where someone serves "
                "snacks and simple meals, a bit like a tiny kitchen or cafe."
            ),
        ),
        QAItem(
            question="Why is it helpful to be polite when you ask for a treat?",
            answer=(
                "Being polite makes the grown-up smile, helps them say yes, "
                "and shows that you care about their answer."
            ),
        ),
        QAItem(
            question="What is a smock for?",
            answer=(
                "A smock is a loose cover you wear over your clothes so that "
                "sticky or messy treats do not get on your nice outfit."
            ),
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and not k.startswith("_")}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:14} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  dialogue beats: {len(world.dialogue)}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        setting="cantina",
        treat="sweetum",
        garment="dress",
        name="Mira",
        gender="girl",
        mama="Mama Rosa",
        rhyme=RHYME_A,
    ),
    StoryParams(
        setting="kitchen",
        treat="little_sweetum",
        garment="blouse",
        name="Lily",
        gender="girl",
        mama="Mama Lila",
        rhyme=RHYME_B,
    ),
    StoryParams(
        setting="bakery",
        treat="sweetum",
        garment="shirt",
        name="Ben",
        gender="boy",
        mama="Mama Cora",
        rhyme=RHYME_C,
    ),
    StoryParams(
        setting="cantina",
        treat="sweetum",
        garment="apron_dress",
        name="Zoe",
        gender="girl",
        mama="Mama Belle",
        rhyme=RHYME_D,
    ),
    StoryParams(
        setting="kitchen",
        treat="little_sweetum",
        garment="shirt",
        name="Mia",
        gender="girl",
        mama="Mama June",
        rhyme=RHYME_B,
    ),
]


def explain_rejection(treat: Treat, garment: Garment) -> str:
    if not treat_at_risk(treat, garment):
        return (f"(No story: {treat.label} can only reach the {sorted(treat.zone)}, "
                f"but the {garment.label} sits on the {garment.region} -- it "
                f"wouldn't get {treat.spill}, so the maternal cook has no honest "
                f"warning. Try a garment worn on {sorted(treat.zone)}.)")
    return (f"(No story: nothing in the smock catalog protects the "
            f"{garment.label} ({garment.region}) from a {treat.label}. The "
            f"compromise must actually cover the at-risk item, so this argument "
            f"is rejected.)")


def explain_gender(garment_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(GARMENTS, garment_id).genders))
    return (f"(No story: a {_safe_lookup(GARMENTS, garment_id).label} isn't a typical "
            f"{gender}'s item here; try --gender {ok}.)")


def explain_rhyme(rhyme: str) -> str:
    if rhyme not in RHYMES:
        return (f"(No story: rhyme key '{rhyme}' is not in the rhyming library; "
                f"try one of {sorted(RHYMES)}.)")
    return ""


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A garment is at risk when the treat spills on the region it is worn on.
garment_at_risk(T, G) :- spills(T, R), worn_on(G, R).

% A smock protects the garment only if it both neutralises the spill kind
% AND covers the at-risk region.
protects(S, T, G) :- smock(S), garment_at_risk(T, G),
                     spill_kind(T, K), guards(S, K),
                     covers(S, R), worn_on(G, R).
has_fix(T, G) :- protects(_, T, G).

valid(Setting, T, G) :- place(Setting), garment_at_risk(T, G), has_fix(T, G).
valid_story(Setting, T, G, Gender) :- valid(Setting, T, G), wears(Gender, G).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("spill_kind", tid, t.spill))
        for r in sorted(t.zone):
            lines.append(asp.fact("spills", tid, r))
    for gid, g in GARMENTS.items():
        lines.append(asp.fact("garment", gid))
        lines.append(asp.fact("worn_on", gid, g.region))
        if g.plural:
            lines.append(asp.fact("garment_plural", gid))
        for s in sorted(g.genders):
            lines.append(asp.fact("wears", s, gid))
    for sm in SMOCKS:
        lines.append(asp.fact("smock", sm.id))
        for k in sorted(sm.guards):
            lines.append(asp.fact("guards", sm.id, k))
        for r in sorted(sm.covers):
            lines.append(asp.fact("covers", sm.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md).
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a maternal cook, a sweet treat, a "
                    "polite child, and a rhyming compromise. Unspecified "
                    "choices are picked at random (seeded).")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mama")
    ap.add_argument("--rhyme", choices=sorted(RHYMES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable."""
    if getattr(args, "treat", None) and getattr(args, "garment", None):
        t, g = _safe_lookup(TREATS, getattr(args, "treat", None)), _safe_lookup(GARMENTS, getattr(args, "garment", None))
        if not (treat_at_risk(t, g) and select_smock(t, g)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "garment", None) and getattr(args, "gender", None) not in _safe_lookup(GARMENTS, getattr(args, "garment", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "rhyme", None):
        msg = explain_rhyme(getattr(args, "rhyme", None))
        if msg:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    stories = [s for s in valid_stories()
               if (getattr(args, "setting", None) is None or s[0] == getattr(args, "setting", None))
               and (getattr(args, "treat", None) is None or s[1] == getattr(args, "treat", None))
               and (getattr(args, "garment", None) is None or s[2] == getattr(args, "garment", None))
               and (getattr(args, "gender", None) is None or s[3] == getattr(args, "gender", None))]
    if not stories:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting_id, treat_id, garment_id, gender = rng.choice(sorted(stories))
    garment = _safe_lookup(GARMENTS, garment_id)
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mama = getattr(args, "mama", None) or rng.choice(MAMA_NAMES)
    rhyme = getattr(args, "rhyme", None) or rng.choice(sorted(RHYMES))
    return StoryParams(
        setting=setting_id,
        treat=treat_id,
        garment=garment_id,
        name=name,
        gender=gender,
        mama=mama,
        rhyme=rhyme,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    smock = _safe_lookup(SMOCKS, 0)                                # use the most-specific smock
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TREATS, params.treat),
                 _safe_lookup(GARMENTS, params.garment), smock,
                 child_name=params.name,
                 child_type="girl" if params.gender == "girl" else "boy",
                 mama_name=params.mama, mama_type="mother",
                 rhyme=params.rhyme)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (setting, treat, garment) combos "
              f"({len(stories)} with gender):\n")
        for setting_id, treat_id, garment_id in triples:
            genders = sorted(g for (s, t, gm, g) in stories
                             if (s, t, gm) == (setting_id, treat_id, garment_id))
            print(f"  {setting_id:9} {treat_id:18} {garment_id:14}  "
                  f"[{', '.join(genders)}]")
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
            header = (f"### {p.name}: {p.treat} at the {p.setting} "
                      f"(garment: {p.garment}, rhyme: {p.rhyme})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
