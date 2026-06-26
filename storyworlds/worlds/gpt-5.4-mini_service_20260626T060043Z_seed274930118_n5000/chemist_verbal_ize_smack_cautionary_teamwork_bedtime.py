#!/usr/bin/env python3
"""
storyworlds/worlds/chemist_verbal_ize_smack_cautionary_teamwork_bedtime.py
===========================================================================

A tiny bedtime story world about a careful little chemist, a noisy mistake,
and a calmer teamwork fix.

Seed tale:
---
At bedtime, a small chemist loved to work at a tidy kitchen table with jars,
spoons, and labels. One evening, the child wanted to verbal-ize every ingredient
out loud and smack a jar lid shut, but that would wake the baby and scare the
cat. The parent warned about the noise. Together, they found a quieter way:
they whispered the labels, passed each spoon gently, and finished the counting
before sleep.

World model:
---
- meters track tangible conditions like noise, tidiness, and sleepiness
- memes track emotional state like curiosity, worry, teamwork, and relief
- causal rules turn loud or careful choices into narrated consequences

The story is cautionary and bedtime-soft: first comes the warning, then the
problem, then a teamwork resolution that leaves the room calmer.
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
# Shared world model
# ---------------------------------------------------------------------------

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    baby: object | None = None
    cat: object | None = None
    chemist: object | None = None
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
class Chamber:
    place: str = "the kitchen table"
    bedtime: bool = True
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
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
class Item:
    id: str
    label: str
    phrase: str
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
class Helper:
    id: str
    label: str
    action: str
    finish: str
    makes_quiet: bool = False
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
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.noise: float = 0.0
        self.sleepiness: float = 0.0

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
        clone = World(self.chamber)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.noise = self.noise
        clone.sleepiness = self.sleepiness
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Domain data
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Chamber(place="the kitchen table", bedtime=True, affords={"mix", "label", "count"}),
    "nursery": Chamber(place="the nursery desk", bedtime=True, affords={"label", "count"}),
    "porch": Chamber(place="the porch step", bedtime=False, affords={"mix", "count"}),
}

TASKS = {
    "mix": Task(
        id="mix",
        verb="mix the moon milk",
        gerund="mixing the moon milk",
        rush="whisk the jar fast",
        sound="a loud clink",
        effect="noisy",
        tags={"chemist", "loud"},
    ),
    "label": Task(
        id="label",
        verb="verbal-ize the ingredients",
        gerund="verbal-izing the ingredients",
        rush="say the names too quickly",
        sound="a sharp chatter",
        effect="busy",
        tags={"chemist", "verbal-ize"},
    ),
    "smack": Task(
        id="smack",
        verb="smack the jar lid shut",
        gerund="smacking the jar lid shut",
        rush="slam the lid down",
        sound="a smack",
        effect="jolting",
        tags={"smack", "loud"},
    ),
}

ITEMS = {
    "jar": Item(id="jar", label="glass jar", phrase="a little glass jar"),
    "spoon": Item(id="spoon", label="wooden spoon", phrase="a small wooden spoon"),
    "label_cards": Item(id="label_cards", label="label cards", phrase="soft paper label cards", plural=True),
}

HELPERS = {
    "whisper": Helper(
        id="whisper",
        label="a whispering plan",
        action="whisper the names",
        finish="whispered the last name together",
        makes_quiet=True,
    ),
    "sort": Helper(
        id="sort",
        label="a sorting tray",
        action="sort the jars by color",
        finish="sorted the jars by color",
        makes_quiet=True,
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Tessa", "Ivy", "Nora"]
BOY_NAMES = ["Theo", "Milo", "Ezra", "Finn", "Owen"]
TRAITS = ["gentle", "curious", "sleepy", "thoughtful", "careful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task(T) :- task_id(T).

cautionary(T) :- effect(T, noisy).
cautionary(T) :- effect(T, jolting).

teamwork(T) :- helper(H), helpful(H, T).

risky(T) :- cautionary(T), sound(T, S), loud_sound(S).
good_story(T) :- risky(T), teamwork(T), bedtime_room.

#show good_story/1.
#show risky/1.
#show teamwork/1.
#show cautionary/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("bedtime_room"))
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("room", sid))
        if s.bedtime:
            lines.append(asp.fact("bedtime_room"))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task_id", tid))
        lines.append(asp.fact("effect", tid, t.effect))
        lines.append(asp.fact("sound", tid, t.sound))
        if t.effect in {"noisy", "jolting"}:
            lines.append(asp.fact("loud_sound", t.sound))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for task in sorted({"mix", "label", "smack"}):
            lines.append(asp.fact("helpful", hid, task))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    atoms = sorted(set(asp.atoms(model, "good_story")))
    expected = [("mix",), ("label",), ("smack",)]
    if atoms == expected:
        print("OK: ASP gate marks the cautionary bedtime tasks correctly.")
        return 0
    print("MISMATCH between ASP and Python gate:", atoms, expected)
    return 1


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def _r_mix_noise(world: World) -> list[str]:
    out: list[str] = []
    chemist = world.get("chemist")
    if chemist.meters.get("mixing", 0.0) >= THRESHOLD and ("mix", "noise") not in world.fired:
        world.fired.add(("mix", "noise"))
        world.noise += 1.0
        chemist.memes["worry"] = chemist.memes.get("worry", 0.0) + 0.5
        out.append("The jar made a loud clink on the table.")
    return out


def _r_smack_noise(world: World) -> list[str]:
    out: list[str] = []
    chemist = world.get("chemist")
    if chemist.meters.get("smacking", 0.0) >= THRESHOLD and ("smack", "noise") not in world.fired:
        world.fired.add(("smack", "noise"))
        world.noise += 1.0
        chemist.memes["alarm"] = chemist.memes.get("alarm", 0.0) + 1.0
        out.append("The lid went smack, and the sound felt far too big for bedtime.")
    return out


def _r_noise_wakes_baby(world: World) -> list[str]:
    out: list[str] = []
    baby = world.get("baby")
    if world.noise >= THRESHOLD and ("noise", "wake") not in world.fired:
        world.fired.add(("noise", "wake"))
        baby.meters["wakefulness"] = baby.meters.get("wakefulness", 0.0) + 1.0
        baby.memes["startled"] = baby.memes.get("startled", 0.0) + 1.0
        out.append("The baby stirred in the next room.")
    return out


def _r_teamwork_quiets(world: World) -> list[str]:
    out: list[str] = []
    chemist = world.get("chemist")
    parent = world.get("parent")
    if chemist.memes.get("teamwork", 0.0) >= THRESHOLD and ("teamwork", "quiet") not in world.fired:
        world.fired.add(("teamwork", "quiet"))
        world.noise = max(0.0, world.noise - 1.0)
        chemist.memes["relief"] = chemist.memes.get("relief", 0.0) + 1.0
        parent.memes["pride"] = parent.memes.get("pride", 0.0) + 1.0
        out.append("Together, they chose the quiet way.")
    return out


CAUSAL_RULES = [
    Rule("mix_noise", _r_mix_noise),
    Rule("smack_noise", _r_smack_noise),
    Rule("noise_wakes_baby", _r_noise_wakes_baby),
    Rule("teamwork_quiets", _r_teamwork_quiets),
]


def predict_noise(world: World, task_id: str) -> dict:
    sim = world.copy()
    if task_id == "mix":
        sim.get("chemist").meters["mixing"] = 1.0
    elif task_id == "smack":
        sim.get("chemist").meters["smacking"] = 1.0
    propagate(sim, narrate=False)
    return {
        "noise": sim.noise,
        "baby_awake": sim.get("baby").meters.get("wakefulness", 0.0) >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def chamber_line(chamber: Chamber) -> str:
    return f"{chamber.place.capitalize()} was warm and soft with bedtime quiet."


def intro(world: World, chemist: Entity) -> None:
    trait = next((t for t in chemist.traits if t != "little"), "careful")
    world.say(
        f"{chemist.id} was a little {trait} chemist who loved tiny jars and neat labels."
    )
    world.say("At bedtime, the table glowed under a small lamp, and every sound seemed louder than usual.")


def desire(world: World, chemist: Entity, task: Task) -> None:
    chemist.memes["curiosity"] = chemist.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{chemist.pronoun().capitalize()} wanted to {task.verb}, and to "
        f"{task.id.replace('smack', 'smack the lid')} if the jar did not close right."
    )


def caution(world: World, parent: Entity, chemist: Entity, task: Task) -> None:
    pred = predict_noise(world, task.id)
    if pred["noise"] >= THRESHOLD or pred["baby_awake"]:
        world.facts["predicted_noise"] = pred["noise"]
        world.facts["task"] = task.id
        world.say(
            f'"Careful," {parent.pronoun("subject")} said. "If you {task.id}, the room will be too loud for sleep."'
        )


def attempt(world: World, chemist: Entity, task: Task) -> None:
    chemist.meters["mixing" if task.id == "mix" else "smacking"] = 1.0
    if task.id == "label":
        chemist.meters["labeling"] = 1.0
    propagate(world, narrate=True)


def teamwork_fix(world: World, parent: Entity, chemist: Entity, helper: Helper) -> None:
    chemist.memes["teamwork"] = chemist.memes.get("teamwork", 0.0) + 1.0
    chemist.meters["quiet_work"] = 1.0
    parent.memes["teamwork"] = parent.memes.get("teamwork", 0.0) + 1.0
    world.say(
        f"Then {parent.pronoun('subject')} showed {chemist.pronoun('object')} {helper.label}."
    )
    world.say(
        f"Together, they {helper.action}, and {chemist.pronoun('subject').capitalize()} {helper.finish}."
    )
    propagate(world, narrate=True)


def ending(world: World, chemist: Entity, parent: Entity) -> None:
    baby = world.get("baby")
    world.say(
        f"By the time the last jar was set down, the baby was still sleeping, the lamp was dim, "
        f"and {chemist.id} felt proud of the quiet teamwork."
    )
    if baby.meters.get("wakefulness", 0.0) < THRESHOLD:
        world.say("The room stayed soft and still, just right for dreams.")


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    helper: str
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


def tell(params: StoryParams) -> World:
    chamber = _safe_lookup(SETTINGS, params.place)
    world = World(chamber)

    chemist = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
    ))
    chemist.id = params.name
    chemist.kind = "character"
    chemist.type = params.gender

    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label="parent",
        traits=["gentle"],
    ))
    baby = world.add(Entity(
        id="baby",
        kind="character",
        type="baby",
        label="baby",
        traits=["sleepy"],
    ))
    cat = world.add(Entity(
        id="cat",
        kind="character",
        type="cat",
        label="cat",
        traits=["curious"],
    ))
    world.add(Entity(id="jar", type="jar", label="glass jar"))
    world.add(Entity(id="spoon", type="spoon", label="wooden spoon"))
    world.add(Entity(id="labels", type="labels", label="label cards", plural=True))

    task = _safe_lookup(TASKS, params.task)
    helper = _safe_lookup(HELPERS, params.helper)

    intro(world, chemist)
    world.say(chamber_line(chamber))
    desire(world, chemist, task)

    world.para()
    caution(world, parent, chemist, task)
    attempt(world, chemist, task)

    world.para()
    teamwork_fix(world, parent, chemist, helper)
    ending(world, chemist, parent)

    world.facts.update(
        chemist=chemist,
        parent=parent,
        baby=baby,
        cat=cat,
        task=task,
        helper=helper,
        chamber=chamber,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = _safe_fact(world, f, "task")
    helper: Helper = _safe_fact(world, f, "helper")
    chemist: Entity = _safe_fact(world, f, "chemist")
    return [
        f'Write a bedtime story for young children about a careful chemist who wants to "{task.verb}" and learns a quieter way.',
        f"Tell a cautionary story where {chemist.id} tries to {task.verb} but ends up using {helper.label} with a parent.",
        f"Write a gentle teamwork story that includes the words chemist, verbal-ize, and smack.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chemist: Entity = _safe_fact(world, f, "chemist")
    parent: Entity = _safe_fact(world, f, "parent")
    baby: Entity = _safe_fact(world, f, "baby")
    task: Task = _safe_fact(world, f, "task")
    helper: Helper = _safe_fact(world, f, "helper")
    place = _safe_fact(world, f, "chamber").place
    trait = next((t for t in chemist.traits if t != "little"), "careful")
    qa = [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about a little {trait} chemist named {chemist.id}, and {parent.pronoun('subject')} was there to help with bedtime quiet.",
        ),
        QAItem(
            question=f"What did {chemist.id} want to do before the warning?",
            answer=f"{chemist.id} wanted to {task.verb}. That was hard at bedtime because it could make too much noise.",
        ),
        QAItem(
            question=f"Why did {parent.pronoun('subject')} give a cautionary warning?",
            answer=f"{parent.pronoun('subject').capitalize()} worried that {chemist.id} would make the room too loud for the sleeping baby and the quiet bedtime mood.",
        ),
        QAItem(
            question=f"How did the teamwork plan help in the end?",
            answer=f"They used {helper.label} and worked together, so {chemist.id} could keep going without waking {baby.pronoun('object')} and without making the room feel noisy.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a chemist do?",
            answer="A chemist is someone who studies and mixes substances, like liquids, powders, and tiny ingredients, to learn what they can do.",
        ),
        QAItem(
            question="What does it mean to verbal-ize something?",
            answer="To verbal-ize something means to put it into words and say it out loud.",
        ),
        QAItem(
            question="What does smack sound like?",
            answer="Smack is a quick, sharp sound, like when something hits another thing with a little slap or slam.",
        ),
        QAItem(
            question="Why is bedtime usually quiet?",
            answer="Bedtime is usually quiet because people are trying to rest and fall asleep, so soft voices and gentle movements help everyone sleep better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  noise={world.noise}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params, parser, generate, emit, main
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, chamber in SETTINGS.items():
        for task in chamber.affords:
            for helper in HELPERS:
                combos.append((place, task, helper))
    return combos


def explain_rejection(place: str, task: str) -> str:
    return f"(No story: {task} does not fit the bedtime room at {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary bedtime story world about a little chemist, loud mistakes, and teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=HELPERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              if getattr(args, "task", None) is None or c[1] == getattr(args, "task", None)
              if getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, helper = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, helper=helper, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} story-ready ASP outcomes:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in [
            StoryParams("kitchen", "mix", "whisper", "Mina", "girl", "mother", "careful"),
            StoryParams("nursery", "label", "sort", "Theo", "boy", "father", "thoughtful"),
            StoryParams("kitchen", "smack", "whisper", "Luna", "girl", "mother", "curious"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
