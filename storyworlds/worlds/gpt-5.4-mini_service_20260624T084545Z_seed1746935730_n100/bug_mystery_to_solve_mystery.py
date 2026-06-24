#!/usr/bin/env python3
"""
storyworlds/worlds/bug_mystery_to_solve_mystery.py
===================================================

A small mystery storyworld about a bug, a missing clue, and a careful solve.

Premise:
- A child has a tiny bug to care for.
- The bug vanishes from its spot.
- The child and a helper search for clues.
- The mystery is solved when they follow the real trace and find the bug safely.

The world is intentionally simple, but state-driven:
- physical meters track things like hidden, found, safe, open, and dusty
- emotional memes track worry, curiosity, calm, and pride

The style aims close to a gentle children's mystery: concrete clues, a clear turn,
and a resolution image that proves what changed.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bug: object | None = None
    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
    indoors: bool
    affordances: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Bug:
    id: str
    label: str
    phrase: str
    kind: str
    size: str
    hides_in: set[str]
    trail: str
    safe_place: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class ClueTool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "garden": Setting("the garden", indoors=False, affordances={"search"}),
    "bedroom": Setting("the bedroom", indoors=True, affordances={"search"}),
    "kitchen": Setting("the kitchen", indoors=True, affordances={"search"}),
}

BUGS = {
    "ladybug": Bug(
        id="ladybug",
        label="ladybug",
        phrase="a tiny red ladybug",
        kind="ladybug",
        size="tiny",
        hides_in={"leaf", "pot", "book"},
        trail="a red speckled trail",
        safe_place="on a leaf",
        tags={"bug", "red", "leaf"},
    ),
    "beetle": Bug(
        id="beetle",
        label="beetle",
        phrase="a shiny black beetle",
        kind="beetle",
        size="small",
        hides_in={"pot", "box", "book"},
        trail="a tiny dark trail",
        safe_place="under a box",
        tags={"bug", "shiny", "dark"},
    ),
    "cricket": Bug(
        id="cricket",
        label="cricket",
        phrase="a little cricket",
        kind="cricket",
        size="small",
        hides_in={"shoe", "box", "plant"},
        trail="a thin scratchy trail",
        safe_place="by a plant",
        tags={"bug", "music", "grass"},
    ),
}

TOOLS = {
    "magnifier": ClueTool(
        id="magnifier",
        label="magnifying glass",
        phrase="a magnifying glass",
        helps_with={"trail", "tiny", "smudge"},
    ),
    "flashlight": ClueTool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        helps_with={"shadow", "dark"},
    ),
    "tweezers": ClueTool(
        id="tweezers",
        label="tweezers",
        phrase="soft tweezers",
        helps_with={"careful", "gentle"},
        plural=True,
    ),
}

NAMES = ["Mia", "Noah", "Luna", "Eli", "Ada", "Owen", "Ivy", "Theo"]
HELPER_NAMES = ["Mom", "Dad", "Aunt June", "Grandpa", "Nina"]
TRAITS = ["curious", "careful", "brave", "patient"]


@dataclass
class StoryParams:
    setting: str
    bug: str
    tool: str
    name: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def bug_at_risk(setting: Setting, bug: Bug) -> bool:
    return setting.affordances and "search" in setting.affordances


def select_reveal_tool(bug: Bug) -> Optional[ClueTool]:
    for tool in TOOLS.values():
        if "tiny" in tool.helps_with or "trail" in tool.helps_with or "careful" in tool.helps_with:
            return tool
    return None


def explain_rejection(setting: Setting, bug: Bug) -> str:
    return (
        f"(No story: the {bug.label} mystery needs a place where clues can be searched, "
        f"but {setting.place} does not support a careful search.)"
    )


class Reasoner:
    def __init__(self, world: World) -> None:
        self.world = world

    def run(self, narrate: bool = True) -> list[str]:
        out: list[str] = []
        changed = True
        while changed:
            changed = False
            for s in self.step():
                changed = True
                out.append(s)
        if narrate:
            for s in out:
                self.world.say(s)
        return out

    def step(self) -> list[str]:
        w = self.world
        out: list[str] = []
        child = next((e for e in w.characters() if e.type in {"girl", "boy"}), None)
        bug = w.get("bug")
        if child and child.memes.get("worry", 0) >= THRESHOLD and not w.fired.__contains__(("clue",)):
            if w.facts.get("clue_seen") and w.facts.get("trail_found"):
                w.fired.add(("clue",))
                child.memes["calm"] = child.memes.get("calm", 0) + 1
                bug.meters["hidden"] = 0
                bug.meters["found"] = 1
                out.append("The clues finally made sense.")
        return out


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    bug_cfg = _safe_lookup(BUGS, params.bug)
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mia", "Luna", "Ada", "Ivy"} else "boy"))
    helper = world.add(Entity(id="helper", kind="character", type="mother", label=params.helper))
    bug = world.add(Entity(id="bug", type=bug_cfg.kind, label=bug_cfg.label, phrase=bug_cfg.phrase))

    bug.meters["hidden"] = 1
    bug.meters["found"] = 0
    bug.meters["safe"] = 1
    child.memes["curiosity"] = 1

    world.facts.update(child=child, helper=helper, bug=bug, bug_cfg=bug_cfg, setting=setting)
    return world


def tell(world: World, params: StoryParams) -> World:
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    bug: Entity = world.facts["bug"]
    bug_cfg: Bug = world.facts["bug_cfg"]

    world.say(
        f"{child.id} was a {params.trait} child who loved little mysteries. "
        f"One morning, {child.pronoun('possessive')} {bug.label} was gone from its spot."
    )
    world.say(
        f"{child.id} had been keeping {bug.phrase} in a clear jar, because {child.pronoun()} liked to watch {bug.it()} crawl."
    )

    world.para()
    world.say(
        f"In {world.setting.place}, {child.id} looked under a leaf, behind a pot, and near a box. "
        f"{helper.label_word} crouched beside {child.pronoun('object')} and said, "
        f"\"Let's solve the mystery one clue at a time.\""
    )
    child.memes["worry"] = 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    bug.meters["hidden"] = 1

    clue_tool = _safe_lookup(TOOLS, params.tool)
    world.say(
        f"{child.id} used {clue_tool.phrase} to look for {bug_cfg.trail}, because the trail was very small."
    )
    if "trail" in clue_tool.helps_with:
        world.facts["trail_found"] = True
        world.say(f"Near a low corner, {child.id} spotted {bug_cfg.trail}.")
    else:
        world.facts["trail_found"] = False

    world.say(
        f"{helper.label_word} pointed to a tiny gap and said, \"A bug this small could hide {bug_cfg.safe_place}.\""
    )
    world.facts["clue_seen"] = True

    Reasoner(world).run(narrate=True)

    world.para()
    if world.facts.get("trail_found"):
        bug.meters["hidden"] = 0
        bug.meters["found"] = 1
        world.say(
            f"{child.id} peeked in the right place and found {bug.phrase} safe and still moving."
        )
        world.say(
            f"{child.id} smiled, gently lifted {bug.it()}, and set {bug.it()} where {bug.safe_place} was soft and bright."
        )
        child.memes["worry"] = 0
        child.memes["pride"] = 1
    else:
        world.say(
            f"The clues stayed blurry, so {helper.label_word} helped {child.id} slow down and look again."
        )
        world.say(
            f"At last, they found {bug.phrase} tucked away where it could rest safely."
        )
        bug.meters["found"] = 1
        child.memes["worry"] = 0
        child.memes["pride"] = 1

    world.say(
        f"By the end, the mystery was solved: the lost {bug.label} had been found, and the jar stayed open and empty."
    )
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    bug_cfg = f["bug_cfg"]
    return [
        f'Write a short mystery story for a young child about a missing {bug_cfg.label}.',
        f"Tell a gentle story where {child.id} follows tiny clues to solve the bug mystery.",
        f'Write a simple mystery that includes a "{bug_cfg.label}" and ends with the bug being found safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    bug = f["bug"]
    bug_cfg = f["bug_cfg"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What mystery did {child.id} need to solve in {setting.place}?",
            answer=f"{child.id} needed to solve the mystery of the missing {bug.label}.",
        ),
        QAItem(
            question=f"What clue helped {child.id} search for the {bug.label}?",
            answer=f"{child.id} looked for {bug_cfg.trail}, which helped point to where the {bug.label} had gone.",
        ),
        QAItem(
            question=f"Who helped {child.id} solve the mystery?",
            answer=f"{helper.label_word} helped {child.id} stay calm, follow clues, and solve the mystery.",
        ),
        QAItem(
            question=f"Where was the {bug.label} found at the end?",
            answer=f"The {bug.label} was found safely {bug_cfg.safe_place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    bug_cfg: Bug = world.facts["bug_cfg"]
    qa = [
        QAItem(
            question="What is a bug?",
            answer="A bug is a tiny living creature, like a beetle, ladybug, or cricket.",
        ),
        QAItem(
            question="Why can a magnifying glass help in a mystery?",
            answer="A magnifying glass makes small clues easier to see.",
        ),
    ]
    if "dark" in bug_cfg.tags:
        qa.append(
            QAItem(
                question="Why can a flashlight help when looking for something small?",
                answer="A flashlight helps light up dark corners so tiny things are easier to find.",
            )
        )
    return qa


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden", bug="ladybug", tool="magnifier", name="Mia", helper="Mom", trait="curious"),
    StoryParams(setting="bedroom", bug="beetle", tool="flashlight", name="Noah", helper="Dad", trait="careful"),
    StoryParams(setting="kitchen", bug="cricket", tool="magnifier", name="Ivy", helper="Grandpa", trait="patient"),
]


@dataclass
class Registry:
    settings: dict[str, Setting]
    bugs: dict[str, Bug]
    tools: dict[str, ClueTool]
    REGISTRY: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


REGISTRY = Registry(settings=SETTINGS, bugs=BUGS, tools=TOOLS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery storyworld about a missing bug.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bug", choices=BUGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for b in BUGS:
            for t in TOOLS:
                combos.append((s, b, t))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "bug", None):
        combos = [c for c in combos if c[1] == getattr(args, "bug", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, bug, tool = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, bug=bug, tool=tool, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    world = tell(world, params)
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
setting(s1). setting(s2). setting(s3).
bug(b1). bug(b2). bug(b3).
tool(t1). tool(t2). tool(t3).

searchable(s1).
searchable(s2).
searchable(s3).

valid_story(S,B,T) :- searchable(S), bug(B), tool(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("searchable", sid))
    for bid in BUGS:
        lines.append(asp.fact("bug", bid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for s, b, t in combos:
            print(f"  {s:8} {b:8} {t:8}")
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
            header = f"### {p.name}: {p.bug} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
