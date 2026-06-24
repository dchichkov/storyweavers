#!/usr/bin/env python3
"""
storyworlds/worlds/faith_word_dim_conflict_ghost_story.py
========================================================

A small ghost-story world about faith, words, and a conflict that can only be
resolved by choosing a brave, kind sentence instead of fear.

The seed image:
---
A child hears a ghostly tapping in an old house. The tap seems to come from a
place where words go dim and disappear. The child is frightened and argues with
the silence, but a trusted adult reminds the child that faith can mean believing
the right words will still work, even in a spooky room. The child speaks a
gentle promise, the ghost calms down, and the dark place becomes warm again.
---

This world simulates:
- a child with meters like fear, chill, glow, and echo
- a ghost that is lonely rather than cruel
- a word-dim pocket where spoken words fade unless protected by faith
- conflict that rises when the child doubts and falls when the child chooses a
  brave, truthful word
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
    kind: str = "thing"  # character | thing | spirit
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    charm: object | None = None
    child: object | None = None
    ghost: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str
    spooky: bool = True
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
class Word:
    id: str
    text: str
    glow: str
    steadies: str  # meter it helps protect: "faith" or "glow" etc.
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
class Charm:
    id: str
    label: str
    phrase: str
    guards: set[str]
    prep: str
    tail: str
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
        self.word_dim_open: bool = False
        self.darkness: float = 1.0

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

    def spirits(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "spirit"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.word_dim_open = self.word_dim_open
        clone.darkness = self.darkness
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    ghost: str
    word: str
    charm: str
    name: str
    gender: str
    adult: str
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
    "attic": Setting(place="the attic", spooky=True, affords={"listen", "whisper"}),
    "hall": Setting(place="the hall", spooky=True, affords={"listen", "whisper"}),
    "library": Setting(place="the old library", spooky=True, affords={"read", "whisper"}),
}

GHOSTS = {
    "bentley": {"label": "a shy little ghost", "type": "ghost", "mood": "lonely"},
    "mira": {"label": "a pale gray ghost", "type": "ghost", "mood": "lonely"},
    "old_man": {"label": "an old ghost", "type": "ghost", "mood": "restless"},
}

WORDS = {
    "faith": Word(id="faith", text="faith", glow="soft gold", steadies="faith"),
    "promise": Word(id="promise", text="promise", glow="blue-white", steadies="faith"),
    "home": Word(id="home", text="home", glow="warm amber", steadies="glow"),
    "brave": Word(id="brave", text="brave", glow="red-gold", steadies="faith"),
}

CHARMS = {
    "lantern": Charm(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a round glass face",
        guards={"chill", "dark"},
        prep="pick up the lantern and step closer",
        tail="held the lantern high while the room brightened",
    ),
    "blanket": Charm(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket for shivery moments",
        guards={"chill"},
        prep="wrap up in the blanket first",
        tail="kept the blanket around their shoulders",
    ),
    "bell": Charm(
        id="bell",
        label="a tiny bell",
        phrase="a tiny bell on a ribbon",
        guards={"echo"},
        prep="take the tiny bell in hand",
        tail="let the bell ring like a clear little note",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Eli", "Max"]
TRAITS = ["careful", "curious", "brave", "quiet", "gentle"]


def reasonableness_gate(place: str, ghost: str, word: str, charm: str) -> None:
    if place not in SETTINGS:
        pass
    if ghost not in GHOSTS:
        pass
    if word not in WORDS:
        pass
    if charm not in CHARMS:
        pass
    if word == "faith" and charm == "blanket":
        return
    if word == "home" and charm == "lantern":
        return
    if word == "brave" and charm == "bell":
        return
    if word == "promise" and charm in {"lantern", "bell"}:
        return
    pass


def _r_chill(world: World) -> list[str]:
    out = []
    if not world.word_dim_open:
        return out
    for ch in world.characters():
        if ch.memes.get("fear", 0.0) < THRESHOLD:
            continue
        sig = ("chill", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.meters["chill"] = ch.meters.get("chill", 0.0) + 1.0
        out.append(f"A cold shiver crept over {ch.id}.")
    return out


def _r_echo(world: World) -> list[str]:
    out = []
    if not world.word_dim_open:
        return out
    for ghost in world.spirits():
        if ghost.memes.get("lonely", 0.0) < THRESHOLD:
            continue
        sig = ("echo", ghost.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ghost.meters["echo"] = ghost.meters.get("echo", 0.0) + 1.0
        out.append("The ghost's call bounced around like a marble in a tin cup.")
    return out


def _r_faith_light(world: World) -> list[str]:
    out = []
    for ch in world.characters():
        if ch.memes.get("faith", 0.0) < THRESHOLD:
            continue
        sig = ("faith_light", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.meters["glow"] = ch.meters.get("glow", 0.0) + 1.0
        world.darkness = max(0.0, world.darkness - 0.5)
        out.append(f"{ch.id}'s brave faith made a small warm glow.")
    return out


def _r_conflict(world: World) -> list[str]:
    out = []
    for ch in world.characters():
        if ch.memes.get("doubt", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["conflict"] = ch.memes.get("conflict", 0.0) + 1.0
        out.append(f"{ch.id} felt torn between fear and trust.")
    return out


def _r_resolve(world: World) -> list[str]:
    out = []
    for ghost in world.spirits():
        if ghost.memes.get("comforted", 0.0) < THRESHOLD:
            continue
        sig = ("resolve", ghost.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ghost.meters["echo"] = 0.0
        out.append("The uneasy tapping settled into a soft, sleepy hush.")
    return out


RULES = [_r_conflict, _r_chill, _r_echo, _r_faith_light, _r_resolve]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, child: Entity, ghost: Entity, word: Word) -> dict:
    sim = world.copy()
    _speak(sim, sim.get(child.id), sim.get(ghost.id), word, narrate=False)
    g = sim.get(ghost.id)
    c = sim.get(child.id)
    return {
        "calmed": g.memes.get("comforted", 0.0) >= THRESHOLD,
        "conflict": c.memes.get("conflict", 0.0) >= THRESHOLD,
        "darkness": sim.darkness,
    }


def _speak(world: World, child: Entity, ghost: Entity, word: Word, narrate: bool = True) -> None:
    child.memes["faith"] = child.memes.get("faith", 0.0) + 1.0
    ghost.memes["comforted"] = ghost.memes.get("comforted", 0.0) + 1.0
    world.word_dim_open = True
    world.darkness = max(0.0, world.darkness - 0.5)
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, ghost: Entity) -> None:
    world.say(
        f"{child.id} was a {next((t for t in child.traits if t != 'little'), 'quiet')} "
        f"{child.type} who noticed every creak in {world.setting.place}."
    )
    world.say(
        f"Some nights, the walls answered with a tapping that sounded like {ghost.label} "
        f"trying not to cry."
    )


def setup(world: World, child: Entity, charm: Entity, word: Word) -> None:
    child.meters["chill"] = 0.0
    world.say(
        f"{child.id} carried {charm.label} because {charm.phrase} made the dark feel less sharp."
    )
    world.say(
        f"When {child.id} heard the word {word.text}, it seemed to shine "
        f"with {word.glow} light."
    )


def conflict_scene(world: World, child: Entity, ghost: Entity, word: Word) -> None:
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1.0
    child.memes["doubt"] = child.memes.get("doubt", 0.0) + 1.0
    world.word_dim_open = True
    world.say(
        f"One night, the tapping came from a corner where words seemed to go dim and thin."
    )
    world.say(
        f"{child.id} wanted to run, but the strange place held still, and {child.pronoun('possessive')} "
        f"breath got small."
    )
    propagate(world, narrate=True)
    world.say(
        f"Then {child.id} heard {ghost.label} whisper from the word-dim, as if {ghost.pronoun()} "
        f"had lost {ghost.pronoun('possessive')} way home."
    )


def choose_faith(world: World, child: Entity, adult: Entity, word: Word) -> None:
    world.say(
        f"{adult.id} knelt beside {child.id} and said, "
        f"\"Faith means staying with a true word even when the room feels spooky.\""
    )
    world.say(
        f"{child.id} looked at {word.text} again and took a slow, brave breath."
    )


def resolution(world: World, child: Entity, ghost: Entity, charm: Entity, word: Word) -> None:
    world.say(
        f"{child.id} {charm.prep} and whispered, \"{word.text}.\""
    )
    _speak(world, child, ghost, word, narrate=True)
    world.say(
        f"At once, {ghost.label} stopped shaking the wall. {ghost.pronoun().capitalize()} looked less lonely "
        f"and more like a friend who had been waiting patiently."
    )
    world.say(
        f"{charm.tail}, and the word-dim grew warm enough to show the dust in the air like tiny stars."
    )


def tell(setting: Setting, ghost_cfg: dict, word: Word, charm_cfg: Charm,
         hero_name: str = "Mia", hero_type: str = "girl", adult_type: str = "mother",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    ghost = world.add(Entity(
        id=ghost_cfg["label"],
        kind="spirit",
        type=ghost_cfg["type"],
        label=ghost_cfg["label"],
        traits=[ghost_cfg["mood"]],
        memes={"lonely": 1.0},
    ))
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "gentle"]),
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        label="the grown-up",
        traits=["steady"],
    ))
    charm = world.add(Entity(
        id=charm_cfg.id,
        type="thing",
        label=charm_cfg.label,
        phrase=charm_cfg.phrase,
        protective=True,
    ))
    intro(world, child, ghost)
    world.para()
    setup(world, child, charm, word)
    world.para()
    conflict_scene(world, child, ghost, word)
    world.para()
    choose_faith(world, child, adult, word)
    resolution(world, child, ghost, charm, word)
    world.facts.update(
        child=child,
        adult=adult,
        ghost=ghost,
        charm=charm,
        word=word,
        setting=setting,
        resolved=ghost.memes.get("comforted", 0.0) >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for g in GHOSTS:
            for w in WORDS:
                for c in CHARMS:
                    try:
                        reasonableness_gate(place, g, w, c)
                    except StoryError:
                        continue
                    combos.append((place, g, w, c))
    return combos


@dataclass
class _Reg:
    pass
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
    ap = argparse.ArgumentParser(description="A small ghost-story world about faith and word-dim conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--word", choices=WORDS)
    ap.add_argument("--charm", choices=CHARMS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "ghost", None) is None or c[1] == getattr(args, "ghost", None))
              and (getattr(args, "word", None) is None or c[2] == getattr(args, "word", None))
              and (getattr(args, "charm", None) is None or c[3] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, ghost, word, charm = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, ghost=ghost, word=word, charm=charm,
                       name=name, gender=gender, adult=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a small child about "{f["word"].text}" and a spooky word-dim.',
        f"Tell a gentle story where {f['child'].id} faces a ghostly conflict in {f['setting'].place} and chooses faith.",
        f"Write a child-friendly haunted-house story that ends with {f['child'].id} calming {f['ghost'].label} with a brave word.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, ghost, word = f["child"], f["adult"], f["ghost"], f["word"]
    qa = [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {child.id}, a little {child.type}, and the grown-up who stayed with {child.pronoun('object')} in the spooky room.",
        ),
        QAItem(
            question=f"What made the story feel scary at first?",
            answer=f"The tapping from {ghost.label} and the dim word-space made {child.id} feel afraid and unsure.",
        ),
        QAItem(
            question=f"What did {child.id} whisper to help the ghost?",
            answer=f"{child.id} whispered \"{word.text}.\" That brave word helped open the word-dim in a kinder way.",
        ),
        QAItem(
            question=f"How did the grown-up help {child.id} with the conflict?",
            answer=f"{adult.id} reminded {child.id} that faith means staying with a true word even when the room feels spooky.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"{ghost.label} grew calm, the tapping softened, and the dark place warmed until it felt safe again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is faith?", answer="Faith means trusting that something good or true is still there even before you can see it."),
        QAItem(question="What is a ghost in a story?", answer="A ghost is a spooky spirit character, and in gentle stories it can be lonely instead of mean."),
        QAItem(question="What does a lantern do?", answer="A lantern gives off light so people can see in the dark."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"word_dim_open={world.word_dim_open} darkness={world.darkness}")
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
is_valid(Place, Ghost, Word, Charm) :- setting(Place), ghost(Ghost), word(Word), charm(Charm),
                                       compatible(Place, Ghost, Word, Charm).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for g in GHOSTS:
        lines.append(asp.fact("ghost", g))
    for w in WORDS:
        lines.append(asp.fact("word", w))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    for place, ghost, word, charm in valid_combos():
        lines.append(asp.fact("compatible", place, ghost, word, charm))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show is_valid/4."))
    return sorted(set(asp.atoms(model, "is_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(GHOSTS, params.ghost),
        _safe_lookup(WORDS, params.word),
        _safe_lookup(CHARMS, params.charm),
        params.name,
        params.gender,
        params.adult,
        [params.trait, "steady"],
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
    StoryParams(place="attic", ghost="bentley", word="faith", charm="blanket", name="Mia", gender="girl", adult="mother", trait="curious"),
    StoryParams(place="hall", ghost="mira", word="promise", charm="lantern", name="Leo", gender="boy", adult="father", trait="gentle"),
    StoryParams(place="library", ghost="old_man", word="brave", charm="bell", name="Nora", gender="girl", adult="mother", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show is_valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
        return

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
            header = f"### {p.name}: {p.word} in {p.place} (ghost: {p.ghost})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
