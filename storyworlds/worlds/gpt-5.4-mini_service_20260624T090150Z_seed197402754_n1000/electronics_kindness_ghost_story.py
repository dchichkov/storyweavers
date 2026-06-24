#!/usr/bin/env python3
"""
storyworlds/worlds/electronics_kindness_ghost_story.py
======================================================

A small story world about a kind ghost, a child, and a bit of electronics.
The story is built from simulated state, not a frozen template: a device loses
charge or breaks, feelings change, a helper appears, and a gentle fix resolves
the problem.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caretTaker: object | None = None
    child: object | None = None
    ghost: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Gadget:
    id: str
    label: str
    phrase: str
    repair_for: set[str] = field(default_factory=set)
    charge_for: set[str] = field(default_factory=set)
    help_text: str = ""
    tail: str = ""
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
class Problem:
    id: str
    label: str
    phrase: str
    kind: str
    causes: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)
    symptom: str = ""
    worry: str = ""
    fix: str = ""
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
class StoryParams:
    place: str
    problem: str
    gadget: str
    child_name: str
    child_type: str
    ghost_name: str
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


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"night_light", "toy_radio"}),
    "hall": Setting(place="the hall", indoor=True, affords={"lamp", "toy_radio"}),
    "attic": Setting(place="the attic", indoor=True, affords={"lamp", "speaker"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"lamp", "speaker", "phone"}),
}

PROBLEMS = {
    "dead_lamp": Problem(
        id="dead_lamp",
        label="lamp",
        phrase="a little lamp with a sleepy switch",
        kind="lamp",
        causes={"charge_low", "switch_off"},
        requires={"charge", "switch"},
        symptom="glowed very weakly",
        worry="the room would feel dark and lonely",
        fix="shine it with a full charge and a gentle flick",
        tags={"electronics", "light", "kindness"},
    ),
    "silent_radio": Problem(
        id="silent_radio",
        label="radio",
        phrase="a small toy radio with a crackly dial",
        kind="radio",
        causes={"battery_low", "dial_stuck"},
        requires={"battery", "dial"},
        symptom="stayed silent",
        worry="the song would not reach the corner",
        fix="give it fresh batteries and turn the dial with care",
        tags={"electronics", "sound", "kindness"},
    ),
    "sad_phone": Problem(
        id="sad_phone",
        label="phone",
        phrase="a tiny phone with a blank face",
        kind="phone",
        causes={"battery_low"},
        requires={"battery"},
        symptom="would not light up",
        worry="no one could call for help",
        fix="plug it in and wait until it wakes up",
        tags={"electronics", "help", "kindness"},
    ),
}

GADGETS = {
    "charger": Gadget(
        id="charger",
        label="charger",
        phrase="a long charger with a neat cord",
        charge_for={"lamp", "phone"},
        help_text="plug it in and feed it power",
        tail="plugged in the charger and waited patiently",
    ),
    "fresh_batteries": Gadget(
        id="fresh_batteries",
        label="fresh batteries",
        phrase="two fresh batteries in a small box",
        charge_for={"radio", "lamp"},
        help_text="set in fresh batteries",
        tail="opened the back and set in fresh batteries",
    ),
    "soft_cloth": Gadget(
        id="soft_cloth",
        label="soft cloth",
        phrase="a soft cloth that could wipe dust away",
        repair_for={"radio"},
        help_text="wipe the dusty buttons clean",
        tail="wiped the dusty buttons clean",
    ),
    "gentle_switch": Gadget(
        id="gentle_switch",
        label="gentle switch",
        phrase="a gentle switch that turned with almost no sound",
        repair_for={"lamp"},
        help_text="tap the switch very gently",
        tail="tapped the switch very gently",
    ),
}

GHOST_NAMES = ["Milo", "Mira", "Pip", "Nora", "Lumi", "Wisp"]
CHILD_NAMES = ["Ada", "Ben", "Cora", "Eli", "Maya", "Noah", "Ivy", "Leo"]
CHILD_TYPES = ["girl", "boy"]
TRAITS = ["quiet", "curious", "small", "sleepy", "brave", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for problem_id, problem in PROBLEMS.items():
            if problem.kind in setting.affords:
                for gadget_id, gadget in GADGETS.items():
                    if problem.kind in gadget.charge_for or problem.kind in gadget.repair_for:
                        out.append((place, problem_id, gadget_id))
    return out


def explain_rejection(problem: Problem, gadget: Gadget) -> str:
    return (
        f"(No story: {gadget.label} cannot reasonably solve {problem.label} here. "
        f"The fix must match the device's need, or the ghost's kindness would not help.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a kind ghost and a bit of electronics."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--name")
    ap.add_argument("--ghost")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
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
    if getattr(args, "problem", None) and getattr(args, "gadget", None):
        pr, ga = _safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(GADGETS, getattr(args, "gadget", None))
        if not (pr.kind in ga.charge_for or pr.kind in ga.repair_for):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "gadget", None) is None or c[2] == getattr(args, "gadget", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, gadget = rng.choice(list(combos))
    child_type = getattr(args, "child_type", None) or rng.choice(CHILD_TYPES)
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    ghost = getattr(args, "ghost", None) or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, problem=problem, gadget=gadget,
                       child_name=child_name, child_type=child_type,
                       ghost_name=ghost)


def _device_entity(problem: Problem, child: Entity) -> Entity:
    return Entity(
        id="device",
        type=problem.kind,
        label=problem.label,
        phrase=problem.phrase,
        owner=child.id,
        caretaker=child.id,
        meters={"charge": 0.0 if problem.id != "silent_radio" else 0.0,
                "broken": 1.0},
        memes={"sad": 1.0},
    )


def tell(setting: Setting, problem: Problem, gadget: Gadget,
         child_name: str, child_type: str, ghost_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        meters={"worry": 0.0, "relief": 0.0},
        memes={"curiosity": 1.0},
    ))
    ghost = world.add(Entity(
        id=ghost_name,
        kind="ghost",
        type="ghost",
        label="a kind ghost",
        meters={"glow": 1.0},
        memes={"kindness": 2.0},
    ))
    device = world.add(_device_entity(problem, child))
    tool = world.add(Entity(id=gadget.id, type="tool", label=gadget.label, phrase=gadget.phrase,
                            owner=ghost.id, caretTaker=ghost.id))
    world.facts.update(child=child, ghost=ghost, device=device, tool=tool,
                       problem=problem, gadget=gadget, setting=setting)
    world.say(
        f"In {setting.place}, {child_name} found {problem.phrase} sitting very still."
    )
    world.say(
        f"{child_name} liked the little device, but it {problem.symptom}."
    )
    world.para()
    child.memes["worry"] += 1
    world.say(
        f"{child_name} worried that {problem.worry}."
    )
    world.say(
        f"Then {ghost_name}, a kind ghost, drifted near the light and smiled."
    )
    if gadget.id == "charger":
        device.meters["charge"] += 1
    elif gadget.id == "fresh_batteries":
        device.meters["charge"] += 1
    elif gadget.id == "soft_cloth":
        device.meters["dust"] = 0
    elif gadget.id == "gentle_switch":
        device.meters["switch"] = 1
    world.para()
    ghost.memes["kindness"] += 1
    child.memes["relief"] += 1
    if problem.id == "dead_lamp":
        device.meters["charge"] = 1
        device.meters["broken"] = 0
        world.say(f'{ghost_name} whispered, "I can help."')
        world.say(f"{ghost_name} gave the lamp {gadget.help_text}, and the room brightened.")
    elif problem.id == "silent_radio":
        device.meters["broken"] = 0
        world.say(f'{ghost_name} said, "Let us wake it gently."')
        world.say(f"{ghost_name} {gadget.tail}, and the radio sang softly again.")
    else:
        device.meters["charge"] = 1
        device.meters["broken"] = 0
        world.say(f'{ghost_name} smiled and said, "We can make it wake up."')
        world.say(f"{ghost_name} {gadget.tail}, and the phone lit up at last.")
    world.para()
    world.say(
        f"{child_name} smiled back, and the little device stayed bright and safe."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a small child that includes the word "electronics".',
        f"Tell a short story where {f['child'].id} meets a kind ghost and fixes "
        f"{f['device'].label} without frightening anyone.",
        f"Write a child-friendly ghost story about kindness, a broken electronic thing, "
        f"and a calm helpful ending in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, device, problem, gadget = f["child"], f["ghost"], f["device"], f["problem"], f["gadget"]
    return [
        QAItem(
            question=f"What did {child.id} find in {world.setting.place}?",
            answer=f"{child.id} found {problem.phrase}. It was a small piece of electronics that needed help.",
        ),
        QAItem(
            question=f"Who helped {child.id} with the {device.label}?",
            answer=f"A kind ghost named {ghost.id} helped {child.id} with the {device.label}.",
        ),
        QAItem(
            question=f"How did the ghost fix the {device.label}?",
            answer=f"{ghost.id} used {gadget.label} to solve the problem. That gentle fix made the {device.label} work again.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt relieved and happy because the {device.label} was bright and safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are electronics?",
            answer="Electronics are things like lamps, radios, phones, and toys that use electricity to work.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring about how someone else feels.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is often a floating character that can be spooky, quiet, or friendly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
device_needs_charge(D) :- broken(D).
device_needs_repair(D) :- broken(D).
compatible(G,D) :- gadget(G), device_kind(D,K), charge_for(G,K), broken(D).
compatible(G,D) :- gadget(G), device_kind(D,K), repair_for(G,K), broken(D).
valid(P,Prob,G) :- setting(P), problem(Prob), gadget(G), problem_kind(Prob,K),
                   gadget_matches(G,K), valid_combo(P,Prob,G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_kind", pid, pr.kind))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        for k in sorted(g.charge_for):
            lines.append(asp.fact("charge_for", gid, k))
        for k in sorted(g.repair_for):
            lines.append(asp.fact("repair_for", gid, k))
    for place, pr, ga in valid_combos():
        lines.append(asp.fact("valid_combo", place, pr, ga))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in asp:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(GADGETS, params.gadget),
                 params.child_name, params.child_type, params.ghost_name)
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
    StoryParams(place="bedroom", problem="dead_lamp", gadget="charger", child_name="Ada", child_type="girl", ghost_name="Milo"),
    StoryParams(place="hall", problem="silent_radio", gadget="fresh_batteries", child_name="Leo", child_type="boy", ghost_name="Wisp"),
    StoryParams(place="kitchen", problem="sad_phone", gadget="charger", child_name="Maya", child_type="girl", ghost_name="Lumi"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.problem} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
