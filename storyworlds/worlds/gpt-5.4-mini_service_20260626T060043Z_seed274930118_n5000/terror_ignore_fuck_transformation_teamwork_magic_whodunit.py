#!/usr/bin/env python3
"""
storyworlds/worlds/terror_ignore_fuck_transformation_teamwork_magic_whodunit.py
==============================================================================

A tiny whodunit-style story world about a strange disappearance, a frightened
group, a magical transformation, and the teamwork it takes to solve the case.

The seed tale behind this world:
---
At dusk, three friends found a locked attic and a note that said to ignore the
bangs. They did not ignore the fear. A small magic charm turned one friend into
a cat, then into a mouse, then back again, and the others had to work together
to follow the clues. In the end, they learned the hidden trick behind the note
and found out who had been saying "fuck" under their breath: the grumpy stage
magician who was trying to scare everyone away from his own secret.
---

This script implements a compact, state-driven mystery. The world contains:
- a place with several rooms,
- a cast of typed characters,
- a magical transformation chain,
- a clue trail,
- a culprit,
- and a resolution that only happens if the team works together.

The prose is generated from the simulated world state, not from a frozen template.
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    culprit: object | None = None
    hero: object | None = None
    note: object | None = None
    partner: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
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
    rooms: list[str]
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
class Clue:
    id: str
    label: str
    detail: str
    room: str
    reveals: str
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
class Mystery:
    id: str
    label: str
    quote: str
    effect: str
    terror: str
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
class Transformation:
    id: str
    from_form: str
    to_form: str
    clue: str
    cost: str
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
        self.room: str = setting.rooms[0]
        self.facts: dict = {}
        self.flags: dict[str, bool] = {}

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
        clone.entities = __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.room = self.room
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.flags = dict(self.flags)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "manor": Setting(place="the old manor", rooms=["foyer", "hall", "attic", "library", "stage"], affords={"mystery"}),
    "theater": Setting(place="the quiet theater", rooms=["lobby", "backstage", "stage", "prop room"], affords={"mystery"}),
    "cottage": Setting(place="the moonlit cottage", rooms=["kitchen", "parlor", "cellar", "loft"], affords={"mystery"}),
}

CHARACTER_TYPES = {
    "girl": "girl",
    "boy": "boy",
    "woman": "woman",
    "man": "man",
}

TRANSFORMS = [
    Transformation(id="cat", from_form="child", to_form="cat", clue="pawprints", cost="a sudden flash of blue light"),
    Transformation(id="mouse", from_form="cat", to_form="mouse", clue="gnawed string", cost="the charm flickered again"),
    Transformation(id="back", from_form="mouse", to_form="child", clue="warm gold dust", cost="the last spell broke"),
]

MYSTERIES = {
    "voice_note": Mystery(
        id="voice_note",
        label="a scratchy note",
        quote='“Ignore the bangs,”',
        effect="fear",
        terror="terror",
    ),
    "stage_whisper": Mystery(
        id="stage_whisper",
        label="a hidden voice",
        quote='“fuck,”',
        effect="panic",
        terror="terror",
    ),
}

CLUES = {
    "pawprints": Clue(id="pawprints", label="tiny pawprints", detail="small prints on the dusty floor", room="hall", reveals="cat"),
    "gnawed_string": Clue(id="gnawed_string", label="a gnawed string", detail="a chewed string beside the locked box", room="attic", reveals="mouse"),
    "warm_gold_dust": Clue(id="warm_gold_dust", label="gold dust", detail="warm glitter under the stage curtain", room="stage", reveals="magic"),
    "latch_key": Clue(id="latch_key", label="a brass key", detail="a key hidden inside an old music box", room="library", reveals="culprit"),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lena", "Pia"]
BOY_NAMES = ["Finn", "Eli", "Toby", "Leo", "Milo"]
ADULT_NAMES = ["June", "Cal", "Rae", "Noel"]
TRAITS = ["curious", "brave", "careful", "quiet", "clever"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    partner: str
    partner_type: str
    culprit: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
place(P) :- setting(P).
room(R) :- room_of(_, R).
clue(C) :- clue_of(C, _, _).
transformation(T) :- transform(T, _, _).
mystery(M) :- mystery(M, _, _).

terror(P) :- clue_of(C, _, fearful), room_of(C, P).
ignore_warning(H) :- hears(H, note), not obeys(H, note).
teamwork(H1, H2) :- helps(H1, H2), helps(H2, H1).
resolved :- culprit(C), found(C), teamwork(_, _), transformation(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for r in s.rooms:
            lines.append(asp.fact("room_of", pid, r))
        for a in s.affords:
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_of", cid, c.room, c.reveals))
    for tid, t in enumerate(TRANSFORMS):
        lines.append(asp.fact("transform", f"t{tid}", t.from_form, t.to_form))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid, m.label, m.effect))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show room_of/2. #show clue_of/3. #show transform/3. #show mystery/3."))
    if not model:
        print("MISMATCH: ASP produced no model.")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def choose_name(rng: random.Random, hero_type: str) -> str:
    if hero_type in {"girl", "woman"}:
        return rng.choice(GIRL_NAMES if hero_type == "girl" else ADULT_NAMES)
    if hero_type in {"boy", "man"}:
        return rng.choice(BOY_NAMES if hero_type == "boy" else ADULT_NAMES)
    return rng.choice(GIRL_NAMES + BOY_NAMES + ADULT_NAMES)


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero,
        phrase=params.hero,
        meters={"fear": 0.0, "courage": 0.0, "form": 0.0},
        memes={"terror": 0.0, "curiosity": 0.0, "teamwork": 0.0},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=params.partner_type,
        label=params.partner,
        phrase=params.partner,
        meters={"fear": 0.0, "courage": 0.0},
        memes={"teamwork": 0.0},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type="man",
        label=params.culprit,
        phrase=params.culprit,
        role="stage magician",
        meters={"nervous": 0.0},
        memes={"guilt": 0.0},
    ))
    note = world.add(Entity(id="note", kind="thing", type="note", label="note"))
    charm = world.add(Entity(id="charm", kind="thing", type="charm", label="spell charm"))

    world.facts.update(hero=hero, partner=partner, culprit=culprit, note=note, charm=charm)
    return world


def _say_setup(world: World) -> None:
    h = world.get("hero")
    p = world.get("partner")
    c = world.get("culprit")
    world.say(f"On a dim evening, {h.label} and {p.label} arrived at {world.setting.place}.")
    world.say(f"The place had a locked feel, like it was holding its breath.")
    world.say(f"Near a dusty table, they found a note that said, “Ignore the bangs.”")
    h.memes["terror"] += 1
    p.memes["terror"] += 1
    world.say(f"{h.label} felt a shiver of terror, and {p.label} did too.")
    c.meters["nervous"] += 1

def _apply_transformation(world: World, tf: Transformation) -> None:
    h = world.get("hero")
    sig = ("transform", tf.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if tf.id == "cat":
        h.type = "cat"
        h.label = f"{h.label} the cat"
        h.meters["form"] = 1.0
        world.say(f"A flash of blue light turned {h.label} into a cat.")
    elif tf.id == "mouse":
        h.type = "mouse"
        h.label = f"{h.label} the mouse"
        h.meters["form"] = 2.0
        world.say(f"Then the charm flickered again, and {h.label} became a mouse.")
    else:
        h.type = "girl"
        h.label = world.facts["hero"].label if "hero" in world.facts else "hero"
        h.meters["form"] = 0.0
        world.say(f"At last, the gold dust settled, and {h.label} turned back into a child.")

def _investigate(world: World) -> None:
    h = world.get("hero")
    p = world.get("partner")
    world.para()
    world.say(f"Instead of ignoring the fear, they searched the hall, the attic, and the stage.")
    world.say(f"Each clue made the mystery clearer.")
    h.memes["curiosity"] += 1
    p.memes["teamwork"] += 1
    h.memes["teamwork"] += 1
    world.say(f"{h.label} and {p.label} kept close together, because teamwork felt safer than panic.")

def _reveal(world: World) -> None:
    c = world.get("culprit")
    h = world.get("hero")
    p = world.get("partner")
    world.para()
    world.say(f"At the end, the brass key opened the hidden box in the library.")
    world.say(f"Inside was the trick: {c.label}, the stage magician, had been using a charm to scare everyone away.")
    c.memes["guilt"] += 1
    c.meters["nervous"] += 1
    world.say(f"He had muttered “fuck” under his breath every time he thought someone was getting too close to his secret.")
    world.say(f"{h.label} and {p.label} realized the noise was only a disguise, not a monster.")
    world.say(f"The magician apologized, and the terror drained away.")

def _resolve(world: World) -> None:
    h = world.get("hero")
    p = world.get("partner")
    h.memes["terror"] = 0.0
    p.memes["terror"] = 0.0
    h.memes["teamwork"] += 1
    p.memes["teamwork"] += 1
    world.para()
    world.say(f"In the final quiet, the friends turned the secret spell back on.")
    world.say(f"The charm stopped wobbling, the room felt warm again, and the case was solved together.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    _say_setup(world)
    world.para()
    _apply_transformation(world, _safe_lookup(TRANSFORMS, 0))
    _investigate(world)
    _apply_transformation(world, _safe_lookup(TRANSFORMS, 1))
    world.say("The clues pointed from the attic to the stage, so they followed the trail.")
    world.say("They did not ignore the evidence, even when it looked strange.")
    _apply_transformation(world, _safe_lookup(TRANSFORMS, 2))
    _reveal(world)
    _resolve(world)

    story = world.render()
    prompts = [
        f'Write a short whodunit where {params.hero} and {params.partner} find a magical clue in {world.setting.place}.',
        f'Tell a mystery story with terror, a transformation, and teamwork that begins with a note saying “Ignore the bangs.”',
        f'Write a gentle detective tale where a spell changes someone into a cat and then a mouse before the truth is revealed.',
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.hero} and {params.partner} find first?",
            answer="They found a note that told them to ignore the bangs, but the note only made the fear feel stranger.",
        ),
        QAItem(
            question=f"How did the magical transformation change {params.hero}?",
            answer=f"The charm turned {params.hero} into a cat, then into a mouse, and finally back into a child again.",
        ),
        QAItem(
            question=f"Who was behind the scary trick?",
            answer=f"{params.culprit}, the stage magician, was behind the trick and had been trying to frighten people away from his secret.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer="It was solved because the friends followed the clues together instead of ignoring them, and the hidden box opened to show the truth.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together so a hard job becomes easier.",
        ),
        QAItem(
            question="What does a transformation mean in a story?",
            answer="A transformation is a change from one form into another, like turning into a cat or a mouse in a magic story.",
        ),
        QAItem(
            question="Why can magic feel mysterious?",
            answer="Magic can feel mysterious because it can change what people see and make a normal place feel strange and surprising.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world with terror, transformation, teamwork, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--culprit")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    partner_type = getattr(args, "partner_type", None) or rng.choice(["girl", "boy"])
    if getattr(args, "hero", None) and getattr(args, "hero_type", None) is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "partner", None) and getattr(args, "partner_type", None) is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or choose_name(rng, hero_type)
    partner = getattr(args, "partner", None) or choose_name(rng, partner_type)
    culprit = getattr(args, "culprit", None) or rng.choice(["Mr. Vale", "Silas", "Theo Crane", "Mr. Reed"])
    if hero == partner:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, hero_type=hero_type, partner=partner, partner_type=partner_type, culprit=culprit)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show setting/1. #show room_of/2. #show clue_of/3. #show transform/3. #show mystery/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show setting/1. #show room_of/2. #show clue_of/3. #show transform/3. #show mystery/3."))
        print(f"ASP model atoms: {len(model)}")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        params_list = [
            StoryParams("manor", "Mina", "girl", "Leo", "boy", "Mr. Vale"),
            StoryParams("theater", "Finn", "boy", "Ivy", "girl", "Silas"),
            StoryParams("cottage", "Nora", "girl", "Eli", "boy", "Mr. Reed"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
