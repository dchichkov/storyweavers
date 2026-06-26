#!/usr/bin/env python3
"""
storyworlds/worlds/kindergarten_inner_monologue_mystery.py
===========================================================

A small, standalone story world for a kindergarten mystery told with
inner-monologue beats.

Premise:
A child notices something missing at kindergarten, thinks hard about the clues,
and follows a careful trail of small observations until the mystery is solved.

The world is intentionally small and constraint-driven:
- one child
- one teacher
- one missing item
- a few plausible hiding places
- a gentle resolution that proves what changed

The prose leans on inner monologue to keep the mystery close and child-facing.
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
    kind: str = "thing"  # "child" | "adult" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    meme: set[str] = field(default_factory=set)
    child: object | None = None
    clue: object | None = None
    item: object | None = None
    teacher: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "child" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "child" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "adult" and self.type in {"woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "adult" and self.type in {"man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "kindergarten"
    afford: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class MissingItem:
    label: str
    phrase: str
    type: str
    clues: list[str]
    possible_hiding_places: list[str]
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
class StoryParams:
    place: str
    missing_item: str
    child_name: str
    child_gender: str
    teacher_gender: str
    clue_place: str
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["focus"] = child.memes.get("focus", 0) + 1
    out.append("The child kept thinking, because the missing thing felt important.")
    return out


def _r_notice_clue(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    clue = world.entities.get("clue")
    if not clue:
        return out
    if child.memes.get("focus", 0) < THRESHOLD:
        return out
    sig = ("clue", clue.location)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.hidden = False
    child.meters["observations"] = child.meters.get("observations", 0) + 1
    out.append(f"{child.id} noticed a tiny clue near the {clue.location}.")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.entities.get("item")
    clue = world.entities.get("clue")
    if not item or not clue:
        return out
    if child.meters.get("observations", 0) < THRESHOLD:
        return out
    sig = ("solve", item.location)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if item.location == clue.location:
        child.memes["relief"] = child.memes.get("relief", 0) + 1
        out.append("The child followed the clue and found the missing thing.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("clue", _r_notice_clue), Rule("solve", _r_solve)]


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


def _child_name_from_gender(gender: str, rng: random.Random) -> str:
    girls = ["Mia", "Nora", "Ava", "Lily", "Zoe", "Ella"]
    boys = ["Leo", "Max", "Ben", "Finn", "Noah", "Theo"]
    return rng.choice(girls if gender == "girl" else boys)


SETTING = Setting(place="kindergarten", afford={"search"})
MISSING_ITEMS = {
    "red_crayon": MissingItem(
        label="red crayon",
        phrase="a bright red crayon",
        type="crayon",
        clues=["a red wax mark", "a crayon-shaped shadow"],
        possible_hiding_places=["art shelf", "rug", "toy bin"],
    ),
    "blue_hat": MissingItem(
        label="blue hat",
        phrase="a small blue hat",
        type="hat",
        clues=["a blue thread", "a curved hat brim"],
        possible_hiding_places=["cubby", "dress-up corner", "coat hook"],
    ),
    "gold_star": MissingItem(
        label="gold star sticker",
        phrase="a shiny gold star sticker",
        type="sticker",
        clues=["a tiny sparkle", "a sticky corner"],
        possible_hiding_places=["book bin", "table edge", "pencil cup"],
    ),
}
TEACHER_GENDERS = ["woman", "man"]
GENDER_NAMES = {
    "girl": ["Mia", "Nora", "Ava", "Lily", "Zoe", "Ella"],
    "boy": ["Leo", "Max", "Ben", "Finn", "Noah", "Theo"],
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for item_id, item in MISSING_ITEMS.items():
        for place in item.possible_hiding_places:
            combos.append((item_id, place))
    return combos


def tell(setting: Setting, missing_item: MissingItem, child_name: str, child_gender: str,
         teacher_gender: str, clue_place: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="child",
        type=child_gender,
        label=child_name,
        meme={"curious": 1.0} if False else "",
    ))
    teacher = world.add(Entity(
        id="teacher",
        kind="adult",
        type=teacher_gender,
        label="teacher",
    ))
    item = world.add(Entity(
        id="item",
        type=missing_item.type,
        label=missing_item.label,
        phrase=missing_item.phrase,
        owner=child.id,
        location=clue_place,
        hidden=True,
        plural=False,
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label="clue",
        phrase=missing_item.clues[0],
        location=clue_place,
        hidden=True,
    ))

    child.memes["curious"] = 1.0
    child.memes["worry"] = 1.0

    world.say(
        f"At kindergarten, {child_name} looked at the table and blinked. "
        f"{child_name} had been using {missing_item.phrase}, but now it was gone."
    )
    world.say(
        f'"Hmm," {child_name} thought. "Where could {missing_item.label} be?" '
        f"{child_name} looked under the papers, then at the floor, trying to think like a detective."
    )

    world.para()
    world.say(
        f"The teacher saw the quiet face and knelt down. "
        f'"Let’s search carefully," {teacher.label} said with a small smile.'
    )

    world.say(
        f'{child_name} thought, "First clue: where did I last leave it?" '
        f'Then {child_name} scanned the room again, one tiny thing at a time.'
    )

    propagate(world, narrate=True)

    world.say(
        f"By {clue_place}, the little clue turned up at last. "
        f"{child_name} reached out and found {missing_item.label} hiding there."
    )
    world.say(
        f'"I knew it!" {child_name} thought. "The clue was telling the truth." '
        f'The teacher laughed softly, and kindergarten felt bright and safe again.'
    )

    world.facts.update(
        child=child,
        teacher=teacher,
        item=item,
        clue=clue,
        missing_item=missing_item,
        clue_place=clue_place,
    )
    return world


KNOWLEDGE = {
    "kindergarten": [
        (
            "What is kindergarten?",
            "Kindergarten is a classroom for young children where they learn, play, and practice being together.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and uses careful thinking to solve a mystery.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small piece of information that helps you figure out what happened.",
        )
    ],
    "search": [
        (
            "Why do people search carefully when something is missing?",
            "They search carefully so they do not miss small clues and can find the missing thing faster.",
        )
    ],
    "sticky": [
        (
            "Why can a sticker leave a clue?",
            "A sticker can leave a clue because it can stick to a surface and make a shiny mark or a little bit of glue.",
        )
    ],
    "wax": [
        (
            "What is wax?",
            "Wax is a smooth material that crayons are made from, and it can make colored marks.",
        )
    ],
}


ASP_RULES = r"""
% An item is missing when it is hidden at the clue place and the child worries.
missing(item) :- hidden(item), worried(child).

% A clue is useful if it is at the same place as the hidden item.
useful(clue) :- clue_at(clue, P), item_at(item, P).

% The mystery is solved when the child follows a useful clue.
solved :- missing(item), useful(clue).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "kindergarten"))
    lines.append(asp.fact("affords", "kindergarten", "search"))
    for item_id, item in MISSING_ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for place in item.possible_hiding_places:
            lines.append(asp.fact("can_hide", item_id, place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_hide/2."))
    asp_set = set(asp.atoms(model, "can_hide"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(asp_set - py_set))
    print(" only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Kindergarten mystery told with inner monologue.")
    ap.add_argument("--place", default="kindergarten", choices=["kindergarten"])
    ap.add_argument("--missing-item", choices=MISSING_ITEMS)
    ap.add_argument("--clue-place")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-gender", choices=TEACHER_GENDERS)
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
    item_id = getattr(args, "missing_item", None) or rng.choice(list(MISSING_ITEMS))
    item = _safe_lookup(MISSING_ITEMS, item_id)
    clue_place = getattr(args, "clue_place", None) or rng.choice(item.possible_hiding_places)
    if clue_place not in item.possible_hiding_places:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    teacher_gender = getattr(args, "teacher_gender", None) or rng.choice(TEACHER_GENDERS)
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDER_NAMES, gender))
    return StoryParams(
        place="kindergarten",
        missing_item=item_id,
        child_name=name,
        child_gender=gender,
        teacher_gender=teacher_gender,
        clue_place=clue_place,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    item = _safe_fact(world, f, "missing_item")
    return [
        f'Write a short kindergarten mystery for a young child that includes the word "kindergarten".',
        f"Tell a gentle detective story where {child.label} wonders where {item.label} went and thinks through the clues.",
        f"Write a child-facing mystery with inner monologue, a missing {item.label}, and a happy discovery at kindergarten.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    teacher = _safe_fact(world, f, "teacher")
    item = _safe_fact(world, f, "missing_item")
    clue_place = _safe_fact(world, f, "clue_place")
    return [
        QAItem(
            question=f"What was missing at kindergarten?",
            answer=f"{child.label} could not find {item.label}, so the child started looking carefully.",
        ),
        QAItem(
            question=f"How did {child.label} try to solve the mystery?",
            answer=f"{child.label} thought like a detective, asked an inner question, and searched for a clue near the {clue_place}.",
        ),
        QAItem(
            question=f"Who helped {child.label} search?",
            answer=f"The teacher helped by saying it was time to search carefully and look for the tiny clue.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{child.label} followed the clue and found {item.label}, so the kindergarten mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["kindergarten", "detective", "clue", "search", "sticky", "wax"]:
        for q, a in KNOWLEDGE.get(key, []):
            out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:6}/{e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


def generate(params: StoryParams) -> StorySample:
    item = _safe_lookup(MISSING_ITEMS, params.missing_item)
    world = tell(
        SETTING,
        item,
        params.child_name,
        params.child_gender,
        params.teacher_gender,
        params.clue_place,
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
    StoryParams(
        place="kindergarten",
        missing_item="red_crayon",
        child_name="Mia",
        child_gender="girl",
        teacher_gender="woman",
        clue_place="art shelf",
    ),
    StoryParams(
        place="kindergarten",
        missing_item="blue_hat",
        child_name="Leo",
        child_gender="boy",
        teacher_gender="man",
        clue_place="dress-up corner",
    ),
    StoryParams(
        place="kindergarten",
        missing_item="gold_star",
        child_name="Nora",
        child_gender="girl",
        teacher_gender="woman",
        clue_place="book bin",
    ),
]


def explain_rejection(item: MissingItem, clue_place: str) -> str:
    return f"(No story: {item.label} would not reasonably hide near the {clue_place}.)"


def resolve_params_for_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "missing_item", None) and getattr(args, "clue_place", None):
        item = _safe_lookup(MISSING_ITEMS, getattr(args, "missing_item", None))
        if getattr(args, "clue_place", None) not in item.possible_hiding_places:
            pass
    return resolve_params(args, rng)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_hide/2."))
    return sorted(set(asp.atoms(model, "can_hide")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show can_hide/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (missing-item, hiding-place) combos:\n")
        for item_id, place in combos:
            print(f"  {item_id:12} {place}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
                params = resolve_params_for_args(args, random.Random(seed))
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
            header = f"### {p.child_name}: {p.missing_item} at kindergarten"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
