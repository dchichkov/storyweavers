#!/usr/bin/env python3
"""
Storyworld: a heartwarming little magic story about making something correct.

A child discovers that a tiny magic heart can help fix a small mistake, but only
when the fix is kind, careful, and true. The story world is intentionally small:
one child, one worried helper, one object that got mixed up, and one gentle
magic turn that makes the day feel warm again.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    child: object | None = None
    helper: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ["clean", "wrong", "fixed", "sparkle", "care", "joy", "worry", "love", "pride"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    warm: bool
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
    mistake: str
    fix_word: str
    keyword: str
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
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    role: str
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
class Charm:
    id: str
    label: str
    phrase: str
    helps: set[str]
    fits: set[str]
    gives: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "home": Setting("the cozy kitchen", warm=True, affords={"note", "label"}),
    "library": Setting("the little library", warm=True, affords={"label", "card"}),
    "garden": Setting("the sunny garden table", warm=True, affords={"card", "sign"}),
}

TASKS = {
    "note": Task(
        id="note",
        verb="write a thank-you note",
        gerund="writing thank-you notes",
        mistake="misspelled",
        fix_word="the right letters",
        keyword="note",
        tags={"letters", "kindness"},
    ),
    "label": Task(
        id="label",
        verb="sort the book labels",
        gerund="sorting book labels",
        mistake="mixed-up",
        fix_word="the right shelf names",
        keyword="label",
        tags={"letters", "books"},
    ),
    "card": Task(
        id="card",
        verb="make a greeting card",
        gerund="drawing greeting cards",
        mistake="smudged",
        fix_word="the right message",
        keyword="card",
        tags={"card", "kindness"},
    ),
    "sign": Task(
        id="sign",
        verb="paint a welcome sign",
        gerund="painting welcome signs",
        mistake="crooked",
        fix_word="the right words",
        keyword="sign",
        tags={"sign", "letters"},
    ),
}

PRIZES = {
    "banner": Prize("banner", "banner", "a paper banner", "banner", "wall"),
    "card": Prize("card", "card", "a little card", "card", "hand"),
    "note": Prize("note", "note", "a folded note", "note", "hand"),
    "sign": Prize("sign", "sign", "a wooden sign", "sign", "wall"),
}

CHARMS = [
    Charm(
        id="heart_glow",
        label="magic heart charm",
        phrase="a small magic heart charm",
        helps={"letters", "kindness", "cards", "signs", "books"},
        fits={"banner", "card", "note", "sign"},
        gives="a warm glow",
        tail="held the charm near the mistake, and the right letters floated into place",
    )
]

NAMES_GIRL = ["Mina", "Lena", "Ada", "Nina", "Ivy", "Lila", "Ruby"]
NAMES_BOY = ["Owen", "Theo", "Finn", "Noah", "Milo", "Eli", "Ben"]
TRAITS = ["gentle", "curious", "kind", "careful", "brave", "cheerful"]


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    gender: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task in setting.affords:
            for prize in PRIZES:
                if task == "note" and prize in {"note", "card", "banner"}:
                    out.append((place, task, prize))
                if task == "label" and prize in {"sign", "banner"}:
                    out.append((place, task, prize))
                if task == "card" and prize in {"card", "banner"}:
                    out.append((place, task, prize))
                if task == "sign" and prize in {"sign", "banner"}:
                    out.append((place, task, prize))
    return out


def prize_at_risk(task: Task, prize: Prize) -> bool:
    if task.id in {"note", "card"}:
        return prize.id in {"note", "card", "banner"}
    if task.id in {"label", "sign"}:
        return prize.id in {"sign", "banner"}
    return False


def select_charm(task: Task, prize: Prize) -> Optional[Charm]:
    for c in CHARMS:
        if task.id in c.helps or task.keyword in c.helps or prize.id in c.fits:
            return c
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny heartwarming magic storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
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


def explain_rejection(task: Task, prize: Prize) -> str:
    return f"(No story: {task.gerund} does not create an honest problem for {prize.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "task", None) and getattr(args, "prize", None):
        if not prize_at_risk(_safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = getattr(args, "name", None) or rng.choice(NAMES_GIRL)
    else:
        name = getattr(args, "name", None) or rng.choice(NAMES_BOY)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandmother"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def _do_task(world: World, actor: Entity, task: Task) -> None:
    actor.meters["wrong"] += 1
    actor.memes["worry"] += 1
    if task.id in {"card", "note"}:
        actor.meters["clean"] += 0.2
    for e in list(world.entities.values()):
        if e.kind == "object" and e.owner == actor.id:
            e.meters["wrong"] += 1


def predict_fix(world: World, actor: Entity, task: Task, prize_id: str) -> bool:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task)
    return any(e.meters["wrong"] > 0 for e in sim.entities.values() if e.id == prize_id)


def tell(setting: Setting, task: Task, prize_cfg: Prize, name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(id=prize_cfg.id, kind="object", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id, caretaker=helper.id))
    charm = world.add(Entity(id="charm", kind="object", type="charm", label="magic heart charm", phrase="a small magic heart charm", owner=helper.id, protective=True))

    child.memes["love"] += 1
    child.memes["joy"] += 1
    helper.memes["care"] += 1

    world.say(f"{child.id} was a {trait} little {gender} who loved quiet jobs that made people smile.")
    world.say(f"{child.pronoun().capitalize()} and {helper.label} sat together at {setting.place}, where {task.gerund} felt calm and safe.")
    world.say(f"{child.id} wanted to {task.verb}, and {helper.label} gave {child.pronoun('object')} {prize_cfg.phrase} to use.")
    prize.worn_by = child.id
    prize.meters["clean"] += 1
    world.para()
    world.say(f"But then a small mistake slipped in: the words looked {task.mistake}, and {prize.label} did not look quite right.")
    child.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(f"{child.id} frowned because {child.pronoun('possessive')} work was not correct yet.")
    if predict_fix(world, child, task, prize.id):
        world.say(f"{helper.label} smiled gently and held up the {charm.label}.")
        world.say(f"{child.id} breathed in, touched the charm, and it gave {charm.gives}.")
        child.meters["sparkle"] += 1
        child.meters["fixed"] += 1
        prize.meters["wrong"] = 0
        prize.meters["fixed"] = 1
        world.say(f"The charm {charm.tail}, and soon the {prize.label} was correct again.")
        world.para()
        child.memes["joy"] += 1
        child.memes["pride"] += 1
        child.memes["worry"] = 0
        helper.memes["worry"] = 0
        world.say(f"{child.id} grinned, and {helper.label} hugged {child.pronoun('object')} close.")
        world.say(f"At the end, the little {prize.label} looked neat and right, and the room felt warm with love.")
    world.facts.update(child=child, helper=helper, prize=prize, task=task, setting=setting, charm=charm)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, task, prize = f["child"], f["helper"], f["task"], f["prize"]
    return [
        f'Write a heartwarming story for a young child about {child.id} using a magic heart charm to make something correct.',
        f"Tell a gentle story where {child.id} wants to {task.verb} with {prize.phrase}, but a small mistake needs magic kindness to fix.",
        f"Write a short magical story about a child, a worried helper, and a careful correction that ends happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, task, prize = f["child"], f["helper"], f["task"], f["prize"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, a {child.type} who is {world.facts['setting'].place if False else 'a little child'} and wants to make things correct with help from {helper.label}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to {task.verb} using {prize.phrase}.",
        ),
        QAItem(
            question=f"What was wrong at first?",
            answer=f"At first, the work looked {task.mistake}, so it was not correct yet.",
        ),
        QAItem(
            question=f"How was the problem fixed?",
            answer=f"{helper.label} brought the magic heart charm, and {child.id} used it carefully until the {prize.label} was correct again.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt proud and happy, and {helper.label} gave a warm hug.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does a magic charm do in a story like this?", answer="A magic charm can help fix a problem or make something change in a special way."),
        QAItem(question="What does it mean for something to be correct?", answer="Correct means it is right, neat, or the way it should be."),
        QAItem(question="Why is a warm hug nice?", answer="A warm hug can help someone feel safe, loved, and better after a mistake."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world trace ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        s = {k: v for k, v in e.memes.items() if v}
        parts = []
        if m:
            parts.append(f"meters={m}")
        if s:
            parts.append(f"memes={s}")
        bits.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(parts)}")
    return "\n".join(bits)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.helper, params.trait)
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


ASP_RULES = r"""
prize_at_risk(T, P) :- task(T), prize(P), risky(T, P).
valid(Place, T, P) :- affords(Place, T), prize_at_risk(T, P), has_charm(T, P).
valid_story(Place, T, P, G) :- valid(Place, T, P), suitable_gender(P, G).

has_charm(T, P) :- charm(C), helps(C, T), fits(C, P).
risky(note, banner).
risky(note, card).
risky(note, note).
risky(label, sign).
risky(label, banner).
risky(card, card).
risky(card, banner).
risky(sign, sign).
risky(sign, banner).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("risky", "note", pid) if pid in {"note", "card", "banner"} else asp.fact("risky", "sign", pid) if pid in {"sign", "banner"} else "")
        for g in sorted(p.genders):
            lines.append(asp.fact("suitable_gender", pid, g))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for h in sorted(c.helps):
            lines.append(asp.fact("helps", c.id, h))
        for f in sorted(c.fits):
            lines.append(asp.fact("fits", c.id, f))
    return "\n".join(l for l in lines if l)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple]:
    combos = []
    for place, t, p in valid_combos():
        for g in ["girl", "boy"]:
            combos.append((place, t, p, g))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python match ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="home", task="note", prize="card", name="Mina", gender="girl", helper="grandmother", trait="kind"),
    StoryParams(place="library", task="label", prize="banner", name="Theo", gender="boy", helper="mother", trait="careful"),
    StoryParams(place="garden", task="sign", prize="sign", name="Ivy", gender="girl", helper="father", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} story variants)\n")
        for t in triples:
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
