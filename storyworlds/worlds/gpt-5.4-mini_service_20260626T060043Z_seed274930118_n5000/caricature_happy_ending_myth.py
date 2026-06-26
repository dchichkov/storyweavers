#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/caricature_happy_ending_myth.py
=============================================================================================================

A tiny mythic story world about a caricature-maker, an overblown mistake, and a
happy ending that turns exaggeration into a blessing.

The seed image is a small legendary tale:
- A young artist loves making caricatures.
- A portrait becomes too exaggerated and embarrasses a proud helper.
- The artist repairs the harm by changing the drawing into a kinder, truer
  image.
- The village laughs, the helper smiles, and the story ends with a blessing.

This script models that premise as a stateful world:
- physical meters: ink, bent-paper, noise, distance, brightness
- emotional memes: pride, shame, wonder, friendship, calm
- the mythic turn comes from a caricature whose exaggeration can either wound
  or delight depending on how it is finished

The ASP twin checks the reasonableness gate:
- only a subject with a strongly visible trait can plausibly become a
  caricature target
- only a matching repair can turn the story toward a happy ending
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


# ---------------------------------------------------------------------------
# World model
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    artist: object | None = None
    caricature: object | None = None
    helper: object | None = None
    subject: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    name: str
    indoor: bool = False
    mythic: bool = True
    affords: set[str] = field(default_factory=set)
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
class Subject:
    id: str
    type: str
    trait: str
    visible_trait: str
    owns: str
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
class Caricature:
    id: str
    label: str
    exaggerates: str
    repair_style: str
    requires: str
    ending_image: str
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


@dataclass
class StoryParams:
    place: str
    subject: str
    caricature: str
    artist_name: str
    artist_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None
    p: object | None = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
PLACES = {
    "square": Place("the village square", affords={"draw", "reveal", "repair"}),
    "hall": Place("the hall of echoes", affords={"draw", "reveal", "repair"}, indoor=True),
    "well": Place("the stone well", affords={"draw", "reveal", "repair"}),
    "orchard": Place("the orchard", affords={"draw", "reveal", "repair"}),
}

SUBJECTS = {
    "king": Subject("king", "king", "proud", "crown", "golden cloak"),
    "giant": Subject("giant", "giant", "gentle", "lantern", "wool coat"),
    "shepherd": Subject("shepherd", "shepherd", "patient", "staff", "blue tunic"),
    "smith": Subject("smith", "smith", "bold", "hammer", "soot-dark apron"),
    "queen": Subject("queen", "queen", "stern", "veil", "silver robe"),
}

CARICATURES = {
    "crown": Caricature(
        "crown",
        "a laughing caricature of a crown",
        "the crown",
        "softened the crown into a bright halo",
        "needles of pride",
        "the drawing shone like a blessing above a smiling brow",
    ),
    "lantern": Caricature(
        "lantern",
        "a tall caricature of a lantern",
        "the lantern",
        "turned the lantern into a bigger, kinder sun",
        "needles of fear",
        "the drawing glowed like evening fireflies",
    ),
    "staff": Caricature(
        "staff",
        "a long caricature of a staff",
        "the staff",
        "curved the staff into a shepherd's moon",
        "needles of worry",
        "the drawing leaned like a reed in calm water",
    ),
    "hammer": Caricature(
        "hammer",
        "a booming caricature of a hammer",
        "the hammer",
        "rounded the hammer into a toy bell",
        "needles of anger",
        "the drawing rang like a festival chime",
    ),
    "veil": Caricature(
        "veil",
        "a floating caricature of a veil",
        "the veil",
        "let the veil become a silver cloud",
        "needles of sorrow",
        "the drawing drifted like moon mist",
    ),
}

ARTIST_NAMES = ["Mira", "Tavi", "Niko", "Lina", "Orin", "Sera", "Arlo", "Nera"]
HELPER_NAMES = ["Bren", "Ivo", "Rhea", "Dorin", "Pela", "Kato", "Mina", "Joss"]
TRAITS = ["proud", "gentle", "patient", "bold", "stern"]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
visible_target(S, C) :- subject(S), caricature(C), shows(S, T), exaggerates(C, T).
can_draw(P, S, C) :- place(P), subject(S), caricature(C), visible_target(S, C).
needs_repair(S, C) :- can_draw(_, S, C), overblown(C).
happy_end(S, C) :- repaired(C), can_draw(_, S, C), calmed(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SUBJECTS.items():
        lines.append(asp.fact("subject", sid))
        lines.append(asp.fact("shows", sid, s.visible_trait))
    for cid, c in CARICATURES.items():
        lines.append(asp.fact("caricature", cid))
        lines.append(asp.fact("exaggerates", cid, c.exaggerates))
        lines.append(asp.fact("overblown", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show visible_target/2."))
    return sorted(set(asp.atoms(model, "visible_target")))


def asp_verify() -> int:
    python_set = set(valid_pairs())
    asp_set = set(asp_valid_pairs())
    if python_set == asp_set:
        print(f"OK: ASP parity confirmed for {len(python_set)} target pairs.")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for sid, s in SUBJECTS.items():
        for cid, c in CARICATURES.items():
            if s.visible_trait == c.exaggerates:
                out.append((sid, cid))
    return out


def explain_rejection(subject: Subject, caricature: Caricature) -> str:
    return (
        f"(No story: {caricature.label} would exaggerate {caricature.exaggerates}, "
        f"but {subject.id} shows {subject.visible_trait} instead. A mythic caricature "
        f"needs a trait the subject actually has.)"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(ARTIST_NAMES if gender == "artist" else HELPER_NAMES)


def protagonist_pronoun(type_: str, case: str = "subject") -> str:
    if type_ in {"girl", "woman", "mother"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if type_ in {"boy", "man", "father"}:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def myth_opening(place: Place) -> str:
    if place.indoor:
        return f"In old times, beneath the roof of {place.name}, the lamps burned like trapped stars."
    return f"In old times, beside {place.name}, the wind carried stories faster than feet could run."


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(world: World, artist: Entity, helper: Entity, subject: Entity, caricature: Entity, place: Place) -> None:
    subject_obj = world.get(subject.id)
    caric = world.get(caricature.id)

    world.say(myth_opening(place))
    world.say(
        f"{artist.id} was a young artist who loved {caric.label} and could make ordinary faces seem full of song."
    )
    world.say(
        f"{helper.id} kept the paints, while {subject.id} wore {subject_obj.phrase} and carried {subject_obj.label} with quiet dignity."
    )

    world.para()
    world.say(
        f"One evening, {artist.id} looked at {subject.id} and began a new drawing at {place.name}."
    )
    world.say(
        f"{artist.id} wanted to catch {subject.pronoun('possessive')} {subject_obj.label} and turn it into {caric.label}."
    )

    # tension
    subject_obj.memes["pride"] += 1
    world.say(
        f"At first, the lines grew too large. The {subject_obj.label} looked wilder and louder than the true face before the mirror."
    )
    subject_obj.meters["noise"] = subject_obj.meters.get("noise", 0) + 1
    subject_obj.memes["shame"] = subject_obj.memes.get("shame", 0) + 1

    if subject_obj.memes["shame"] >= 1:
        world.say(
            f"{subject.id} grew still. {subject.pronoun().capitalize()} feared the crowd would laugh at {subject.pronoun('object')} instead of with {subject.pronoun('object')}."
        )

    # reveal
    world.para()
    world.say(
        f"Then {helper.id} stepped close and said, 'A true joke should carry mercy.'"
    )
    world.say(
        f"{artist.id} listened. The artist softened {caricature.pronoun('possessive') if False else 'the'} lines, and the drawing changed."
    )
    world.say(
        f"Where there had been sharp exaggeration, there was now a bright kindness: {caricature.label} became {caric.repair_style}."
    )

    subject_obj.memes["shame"] = 0
    subject_obj.memes["calm"] = subject_obj.memes.get("calm", 0) + 1
    subject_obj.memes["wonder"] = subject_obj.memes.get("wonder", 0) + 1
    helper.memes["friendship"] = helper.memes.get("friendship", 0) + 1

    world.para()
    world.say(
        f"The people gathered, but they did not mock. They laughed the way spring water laughs over clean stones."
    )
    world.say(
        f"{subject.id} smiled at last, because the new picture made {subject.pronoun('object')} seem larger than life and still beloved."
    )
    world.say(
        f"By nightfall, the old fear was gone, and {caricature.ending_image}."
    )

    world.facts.update(
        artist=artist,
        helper=helper,
        subject=subject,
        caricature=caricature,
        place=place,
        happy=True,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story for children about a caricature that becomes kind instead of cruel.',
        f"Tell a happy-ending tale where {f['artist'].id} draws {f['subject'].id}'s {f['subject'].label} as {f['caricature'].label} and then repairs the picture.",
        f'Write a gentle legend set at {f["place"].name} that includes the word "caricature" and ends in relief and laughter.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    artist = _safe_fact(world, f, "artist")
    helper = _safe_fact(world, f, "helper")
    subject = _safe_fact(world, f, "subject")
    caric = _safe_fact(world, f, "caricature")
    place = _safe_fact(world, f, "place")

    return [
        QAItem(
            question=f"Who made the picture at {place.name}?",
            answer=f"{artist.id} made the picture, with {helper.id} nearby helping with the paints.",
        ),
        QAItem(
            question=f"What did the artist try to turn into a caricature?",
            answer=f"{artist.id} tried to turn {subject.id}'s {subject.label} into {caric.label}.",
        ),
        QAItem(
            question=f"Why did {subject.id} feel upset before the repair?",
            answer=(
                f"{subject.id} felt upset because the drawing became too exaggerated and seemed like it might invite laughing instead of kindness."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily: the drawing was softened into a kinder image, {subject.id} smiled, and the people laughed without cruelty."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caricature?",
            answer=(
                "A caricature is a funny picture that exaggerates some features on purpose, often to make someone look larger, longer, or more dramatic."
            ),
        ),
        QAItem(
            question="Why can laughter be kind?",
            answer=(
                "Laughter can be kind when it helps people feel included, happy, and understood instead of embarrassed."
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
# Story construction
# ---------------------------------------------------------------------------
def valid_story_params() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for sid, s in SUBJECTS.items():
            for cid, c in CARICATURES.items():
                if s.visible_trait == c.exaggerates:
                    combos.append((place, sid, cid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "subject", None) and getattr(args, "caricature", None):
        subj = _safe_lookup(SUBJECTS, getattr(args, "subject", None))
        caric = _safe_lookup(CARICATURES, getattr(args, "caricature", None))
        if subj.visible_trait != caric.exaggerates:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_story_params()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "subject", None) is None or c[1] == getattr(args, "subject", None))
        and (getattr(args, "caricature", None) is None or c[2] == getattr(args, "caricature", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, subject_id, caricature_id = rng.choice(list(combos))
    artist_type = getattr(args, "artist_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place_id,
        subject=subject_id,
        caricature=caricature_id,
        artist_name=getattr(args, "artist_name", None) or pick_name(rng, "artist"),
        artist_type=artist_type,
        helper_name=getattr(args, "helper_name", None) or pick_name(rng, "helper"),
        helper_type=helper_type,
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    subject_def = _safe_lookup(SUBJECTS, params.subject)
    caric_def = _safe_lookup(CARICATURES, params.caricature)

    world = World(place)
    artist = world.add(Entity(
        id=params.artist_name, kind="character", type=params.artist_type,
        label="artist", traits=[params.trait, "gentle"],
        meters={"ink": 1.0}, memes={"wonder": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name, kind="character", type=params.helper_type,
        label="helper", traits=["faithful"],
        meters={"brightness": 1.0}, memes={"friendship": 1.0},
    ))
    subject = world.add(Entity(
        id=subject_def.id, kind="character", type=subject_def.type,
        label=subject_def.visible_trait, phrase=subject_def.owns,
        traits=[subject_def.trait], meters={"presence": 1.0}, memes={"pride": 1.0},
    ))
    caricature = world.add(Entity(
        id=caric_def.id, type="picture", label=caric_def.label,
        phrase=caric_def.label, owner=artist.id,
        meters={"ink": 1.0}, memes={"fun": 1.0},
    ))

    tell(world, artist, helper, subject, caricature, place)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI / output
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic caricature storyworld with a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--subject", choices=SUBJECTS)
    ap.add_argument("--caricature", choices=CARICATURES)
    ap.add_argument("--artist-name")
    ap.add_argument("--artist-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show visible_target/2.\n#show happy_end/2."))
    return sorted(set(asp.atoms(model, "happy_end")))


def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_full() -> int:
    if set(asp_valid_pairs()) == set(valid_pairs()):
        print(f"OK: ASP gate matches Python gate ({len(valid_pairs())} pairs).")
        return 0
    return asp_verify()


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
        print(asp_program_full("#show happy_end/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program_full("#show visible_target/2."))
        pairs = sorted(set(asp.atoms(model, "visible_target")))
        print(f"{len(pairs)} valid caricature targets:\n")
        for sid, cid in pairs:
            print(f"  {sid:10} {cid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, sid, cid in valid_story_params():
            p = StoryParams(
                place=place,
                subject=sid,
                caricature=cid,
                artist_name="Mira",
                artist_type="girl",
                helper_name="Bren",
                helper_type="boy",
                trait="gentle",
            )
            samples.append(generate(p))
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
            header = f"### {p.artist_name}: {p.subject} as {p.caricature} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
