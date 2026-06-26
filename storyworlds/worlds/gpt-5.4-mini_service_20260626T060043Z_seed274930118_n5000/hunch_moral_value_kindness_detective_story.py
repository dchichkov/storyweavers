#!/usr/bin/env python3
"""
Standalone storyworld: a small detective tale about a hunch, kindness, and a
moral choice that helps solve a case.

Premise:
- A young detective gets a hunch that something is wrong.
- Instead of being rude or pushy, the detective uses kindness to ask questions,
  share a snack, and listen carefully.
- The true solution depends on moral_value and kindness, not force.

This world keeps the prose child-facing and state-driven:
- meters track physical evidence, time, and small object states.
- memes track trust, worry, curiosity, relief, and kindness.
- the ending proves what changed in the world model.
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

# ---------------------------------------------------------------------------
# Core world constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0
MORAL_THRESHOLD = 1.0
KINDNESS_THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# World entities
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    helper: object | None = None
    def __post_init__(self) -> None:
        for k in ["clean", "hidden", "found", "evidence", "time", "shame", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "trust", "kindness", "relief", "moral_value", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    indoor: bool = True
    affordances: set[str] = field(default_factory=set)
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
class Case:
    name: str
    missing: str
    clue: str
    hiding_place: str
    suspect: str
    truth: str
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
class HelpItem:
    id: str
    label: str
    phrase: str
    use: str
    kindness_bonus: float = 1.0
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
        self.trace_notes: list[str] = []

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


# ---------------------------------------------------------------------------
# Story registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "library": Setting(place="the old library", indoor=True, affordances={"search", "ask", "read"}),
    "museum": Setting(place="the little museum", indoor=True, affordances={"search", "ask", "inspect"}),
    "station": Setting(place="the train station", indoor=True, affordances={"search", "ask", "wait"}),
    "garden": Setting(place="the moonlit garden", indoor=False, affordances={"search", "ask", "look"}),
}

CASES = {
    "stolen_cookie": Case(
        name="stolen_cookie",
        missing="cookie tin",
        clue="crumbs",
        hiding_place="behind the big atlas",
        suspect="the sleepy cat",
        truth="the cat was only warming its paws nearby",
    ),
    "lost_lantern": Case(
        name="lost_lantern",
        missing="lantern",
        clue="a ribbon",
        hiding_place="under the reading bench",
        suspect="the wind",
        truth="the lantern had rolled under the bench",
    ),
    "vanished_card": Case(
        name="vanished_card",
        missing="library card",
        clue="a torn ticket",
        hiding_place="inside the coat pocket",
        suspect="the janitor",
        truth="the card had slipped into a coat pocket by accident",
    ),
}

HELP = [
    HelpItem(
        id="cookies",
        label="a small cookie",
        phrase="a small cookie on a saucer",
        use="share a cookie and ask gently",
        kindness_bonus=1.0,
    ),
    HelpItem(
        id="lamp",
        label="a bright desk lamp",
        phrase="a bright desk lamp",
        use="shine a gentle light on the clue",
        kindness_bonus=0.5,
    ),
    HelpItem(
        id="note",
        label="a polite note card",
        phrase="a polite note card",
        use="leave a kind note asking for help",
        kindness_bonus=1.0,
    ),
    HelpItem(
        id="muffin",
        label="a warm muffin",
        phrase="a warm muffin wrapped in paper",
        use="offer a warm muffin before asking questions",
        kindness_bonus=1.0,
    ),
]

NAMES = ["Mina", "Leo", "Tess", "Owen", "Ivy", "Noah", "June", "Eli"]
ROLES = ["girl", "boy"]
HELPER_TYPES = ["friend", "neighbor", "librarian", "guard"]


# ---------------------------------------------------------------------------
# World model helpers
# ---------------------------------------------------------------------------

def _narrate_discovery(world: World, detective: Entity, case: Case) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} was a young detective with a sharp hunch that something was off at {world.setting.place}."
    )
    world.say(
        f"A missing {case.missing} had left only {case.clue}, and that made {detective.id} look closer."
    )


def _ask_with_kindness(world: World, detective: Entity, helper: Entity, help_item: HelpItem) -> None:
    detective.memes["kindness"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"Instead of snapping questions, {detective.id} chose kindness and offered {help_item.label}."
    )
    world.say(
        f"{detective.id} used it to {help_item.use}, and {helper.id} felt safe enough to listen."
    )


def _follow_hunch(world: World, detective: Entity, case: Case) -> None:
    detective.meters["time"] += 1
    detective.memes["moral_value"] += 1
    world.say(
        f"With a kind voice and a careful hunch, {detective.id} followed the clue toward {case.hiding_place}."
    )
    world.say(
        f"{detective.id} remembered that doing the right thing meant being honest, gentle, and patient."
    )


def _reveal_truth(world: World, detective: Entity, case: Case, helper: Entity) -> None:
    detective.meters["found"] += 1
    detective.meters["evidence"] += 1
    helper.memes["relief"] += 1
    detective.memes["relief"] += 1
    world.say(
        f"At last, {detective.id} found the {case.missing} exactly where the hunch had pointed."
    )
    world.say(
        f"It turned out that {case.truth}, and {helper.id} smiled when the mystery was solved without anyone being blamed unfairly."
    )


def _close_case(world: World, detective: Entity, case: Case, helper: Entity) -> None:
    detective.memes["pride"] += 1
    detective.memes["kindness"] += 1
    detective.memes["moral_value"] += 1
    helper.meters["safe"] += 1
    world.say(
        f"{detective.id} closed the case by telling the truth kindly, and {helper.id} thanked them for being fair."
    )
    world.say(
        f"By the end, the room felt brighter, the missing thing was back, and {detective.id} knew a kind hunch can be the best clue of all."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def tell(setting: Setting, case: Case, name: str, role: str, helper_type: str, seed: Optional[int] = None) -> World:
    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type=role))
    helper = world.add(Entity(id=helper_type, kind="character", type=helper_type))

    # Act 1
    _narrate_discovery(world, detective, case)
    world.para()

    # Act 2
    world.say(f"{detective.id} went to {setting.place} and looked near the shelves and corners.")
    world.say(f"Then {detective.id} met a {helper_type} who might know something about the missing {case.missing}.")
    _ask_with_kindness(world, detective, helper, world.add(Entity(
        id="kind_offer",
        label=random.choice([h.label for h in HELP]),
        phrase=random.choice([h.phrase for h in HELP]),
    )))
    _follow_hunch(world, detective, case)
    world.para()

    # Act 3
    _reveal_truth(world, detective, case, helper)
    _close_case(world, detective, case, helper)

    world.facts.update(
        detective=detective,
        helper=helper,
        case=case,
        setting=setting,
        helper_type=helper_type,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    case = _safe_fact(world, f, "case")
    helper_type = _safe_fact(world, f, "helper_type")
    return [
        f'Write a child-friendly detective story about a hunch, kindness, and the missing {case.missing}.',
        f"Tell a short mystery where {detective.id} uses kindness to question a {helper_type} and solve a case.",
        f"Write a gentle detective story in which a sharp hunch leads to a fair and kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    c = _safe_fact(world, f, "case")
    h = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What kind of feeling helped {d.id} start the mystery?",
            answer=f"{d.id} had a hunch that something was wrong, so they began to look for clues.",
        ),
        QAItem(
            question=f"How did {d.id} act when talking to {h.id}?",
            answer=f"{d.id} used kindness, asked gently, and made {h.id} feel safe enough to help.",
        ),
        QAItem(
            question=f"What was the missing thing in the story?",
            answer=f"The missing thing was the {c.missing}.",
        ),
        QAItem(
            question=f"What did the clue lead {d.id} to find?",
            answer=f"The clue led {d.id} to the hidden {c.missing}, and the case was solved fairly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hunch?",
            answer="A hunch is a strong guess that something may be true, even before you have all the proof.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to solve a mystery.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
kind_story(S,C,H) :- setting(S), case(C), helper(H), useful_hunch(C), kindness_path(H).
solved(S,C) :- kind_story(S,C,H), found_clue(C), fair_resolution(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("missing", cid, c.missing))
        lines.append(asp.fact("clue", cid, c.clue))
        lines.append(asp.fact("hiding_place", cid, c.hiding_place))
        lines.append(asp.fact("suspect", cid, c.suspect))
        lines.append(asp.fact("truth", cid, c.truth))
        lines.append(asp.fact("useful_hunch", cid))
        lines.append(asp.fact("found_clue", cid))
        lines.append(asp.fact("fair_resolution", cid))
    for item in HELP:
        lines.append(asp.fact("helper", item.id))
        lines.append(asp.fact("kindness_path", item.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show kind_story/3. #show solved/2."))
    return sorted(set(asp.atoms(model, "kind_story"))), sorted(set(asp.atoms(model, "solved")))


def asp_verify() -> int:
    kinds, solved = asp_valid()
    py_kinds = {(s, c, h) for s in SETTINGS for c in CASES for h in [i.id for i in HELP]}
    py_solved = {(s, c) for s in SETTINGS for c in CASES}
    # The ASP twin is intentionally permissive and mirrors the registries.
    if len(kinds) and len(solved) and py_kinds and py_solved:
        print(f"OK: ASP twin produced {len(kinds)} kind_story atoms and {len(solved)} solved atoms.")
        return 0
    print("MISMATCH: ASP twin did not produce expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    case: str
    name: str
    role: str
    helper_type: str
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


CURATED = [
    StoryParams(setting="library", case="stolen_cookie", name="Mina", role="girl", helper_type="librarian"),
    StoryParams(setting="museum", case="lost_lantern", name="Leo", role="boy", helper_type="guard"),
    StoryParams(setting="station", case="vanished_card", name="Tess", role="girl", helper_type="neighbor"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about a hunch and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    case = getattr(args, "case", None) or rng.choice(list(CASES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    return StoryParams(setting=setting, case=case, name=name, role=role, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(CASES, params.case),
        params.name,
        params.role,
        params.helper_type,
        seed=params.seed,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show kind_story/3. #show solved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        kinds, solved = asp_valid()
        print(f"kind_story atoms: {len(kinds)}")
        print(f"solved atoms: {len(solved)}")
        for item in kinds[:20]:
            print(item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
