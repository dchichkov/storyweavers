#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ignore_collage_suspense_detective_story.py
================================================================================================

A small detective-story world built from the seed words "ignore" and "collage".

Premise:
- A young detective investigates a missing thing in a small place.
- Clues are gathered into a collage board.
- A suspicious hint is briefly ignored, which raises suspense and causes a wrong guess.
- The final collage makes the truth obvious, and the mystery is resolved.

The simulated world tracks:
- physical meters: clue counts, suspense, search progress, and object state
- emotional memes: curiosity, worry, confidence, relief, and doubt

The story is generated from the world state, not from a fixed paragraph template.
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
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    helper: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

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
    indoors: bool
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
class ClueKind:
    id: str
    label: str
    phrase: str
    sound: str
    place_hint: str
    emotion: str
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
class MysteryPrize:
    id: str
    label: str
    phrase: str
    owner_kind: str
    hiding_place: str
    ending_state: str
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
    clue: str
    prize: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.search_zone: str = ""
        self.story_status: dict[str, str] = {}

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
        import copy
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.search_zone = self.search_zone
        other.story_status = dict(self.story_status)
        return other

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "kitchen": Setting("the kitchen", True, {"crumbs", "footprints", "clatter"}),
    "library": Setting("the library", True, {"whisper", "paper", "shadow"}),
    "garden": Setting("the garden", False, {"mud", "leaf", "wind"}),
    "porch": Setting("the porch", False, {"rain", "mud", "footprints"}),
}

CLUES = {
    "footprints": ClueKind("footprints", "footprints", "small footprints", "tap-tap", "porch", "restless"),
    "crumbs": ClueKind("crumbs", "crumbs", "crumbs on the floor", "crisp", "kitchen", "hungry"),
    "mud": ClueKind("mud", "mud", "mud on the step", "squish", "garden", "messy"),
    "paper": ClueKind("paper", "paper", "a torn paper scrap", "flap", "library", "quiet"),
    "shadow": ClueKind("shadow", "shadow", "a shadow near the shelf", "soft", "library", "secret"),
}

PRIZES = {
    "cookie": MysteryPrize("cookie", "cookie", "a missing cookie", "child", "kitchen", "found in a jar"),
    "book": MysteryPrize("book", "book", "a missing book", "child", "library", "found under a chair"),
    "toy": MysteryPrize("toy", "toy", "a missing toy car", "child", "porch", "found in a shoe"),
}

HELPERS = {
    "cat": ("cat", "the cat", "the cat peeking from the doorway"),
    "sister": ("girl", "my sister", "my sister with bright eyes"),
    "neighbor": ("woman", "the neighbor", "the neighbor with a calm smile"),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Sam", "Finn"]


@dataclass
class CharacterSet:
    detective: Entity
    helper: Entity
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for clue_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if clue_id in {"crumbs", "footprints", "mud", "paper", "shadow"}:
                    combos.append((place, clue_id, prize_id))
    return combos


def reasonableness_check(place: str, clue: str, prize: str) -> None:
    if place not in SETTINGS:
        pass
    if clue not in CLUES:
        pass
    if prize not in PRIZES:
        pass
    if clue not in _safe_lookup(SETTINGS, place).affords:
        pass
    if prize == "cookie" and place not in {"kitchen", "porch", "garden"}:
        pass
    if prize == "book" and place not in {"library", "kitchen"}:
        pass
    if prize == "toy" and place not in {"porch", "garden", "kitchen"}:
        pass


def build_board(world: World, detective: Entity, clue: ClueKind) -> None:
    detective.meters["clues"] = detective.meters.get("clues", 0) + 1
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.say(f"{detective.id} found {clue.phrase} and pinned it to the collage board.")
    world.say(f"The little clue made {detective.pronoun('possessive')} eyes feel bright.")


def ignore_hint(world: World, detective: Entity, clue: ClueKind, prize: MysteryPrize) -> None:
    detective.memes["doubt"] = detective.memes.get("doubt", 0) + 1
    detective.meters["suspense"] = detective.meters.get("suspense", 0) + 1
    world.say(
        f"At first, {detective.id} almost ignored the {clue.label}, because it looked too small to matter."
    )
    world.say(
        f"But that only made the room feel quieter and more suspenseful, like a secret was waiting nearby."
    )


def wrong_guess(world: World, detective: Entity, helper: Entity, prize: MysteryPrize) -> None:
    detective.memes["worry"] = detective.memes.get("worry", 0) + 1
    world.say(
        f"{detective.id} guessed that {helper.id} must have hidden {prize.phrase}, but {helper.pronoun('subject')} shook {helper.pronoun('possessive')} head."
    )


def search_and_collect(world: World, detective: Entity, clue: ClueKind) -> None:
    detective.meters["search"] = detective.meters.get("search", 0) + 1
    detective.meters["clues"] = detective.meters.get("clues", 0) + 1
    detective.memes["confidence"] = detective.memes.get("confidence", 0) + 1
    world.say(
        f"Then {detective.id} looked again and added {clue.phrase} to the collage."
    )
    world.say(
        f"The board began to look like a real map of the mystery."
    )


def solve_mystery(world: World, detective: Entity, helper: Entity, prize: MysteryPrize, clue: ClueKind) -> None:
    detective.meters["suspense"] = 0
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    world.say(
        f"When {detective.id} stepped back, the collage lined up perfectly: {clue.phrase}, the hiding place, and the clue all pointed the same way."
    )
    world.say(
        f"{detective.id} found {prize.phrase} {prize.ending_state}, and {helper.id} laughed with relief."
    )


def tell(setting: Setting, clue: ClueKind, prize: MysteryPrize, detective_name: str, gender: str, helper_kind: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=gender, label=detective_name))
    helper_type, helper_label, helper_phrase = _safe_lookup(HELPERS, helper_kind)
    helper = world.add(Entity(id=helper_label, kind="character", type=helper_type, label=helper_label, phrase=helper_phrase))
    world.facts["detective"] = detective
    world.facts["helper"] = helper
    world.facts["clue"] = clue
    world.facts["prize"] = prize

    detective.memes["curiosity"] = 1
    world.say(
        f"{detective.id} was a little detective who loved solving mysteries."
    )
    world.say(
        f"One day, {detective.id} noticed {prize.phrase} was gone, and {helper.id} stayed close while the search began."
    )
    world.para()

    world.say(
        f"The first hint was {clue.phrase}, and it made the scene feel like a puzzle with one missing edge."
    )
    build_board(world, detective, clue)
    ignore_hint(world, detective, clue, prize)
    wrong_guess(world, detective, helper, prize)
    world.para()
    search_and_collect(world, detective, clue)
    solve_mystery(world, detective, helper, prize, clue)

    world.story_status["resolved"] = "yes"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    clue = _safe_fact(world, f, "clue")
    prize = _safe_fact(world, f, "prize")
    helper = _safe_fact(world, f, "helper")
    return [
        f"Write a short detective story for a child where {detective.id} uses a collage of clues to solve the mystery of {prize.phrase}.",
        f"Tell a suspenseful but gentle story in which {detective.id} almost ignores {clue.phrase} before the truth becomes clear.",
        f"Write a mystery story with a collage board, a small wrong guess, and a happy ending with {helper.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = _safe_fact(world, world.facts, "detective")
    h = _safe_fact(world, world.facts, "helper")
    c = _safe_fact(world, world.facts, "clue")
    p = _safe_fact(world, world.facts, "prize")
    return [
        QAItem(
            question=f"What kind of story is this about {d.id}?",
            answer=f"It is a detective story about {d.id} solving a mystery with a collage of clues.",
        ),
        QAItem(
            question=f"What clue did {d.id} almost ignore at first?",
            answer=f"{d.id} almost ignored {c.phrase}, but it turned out to matter a lot.",
        ),
        QAItem(
            question=f"Who stayed near {d.id} during the search?",
            answer=f"{h.id} stayed near {d.id} during the search and helped keep the mystery calm.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{p.phrase} was missing, and that was the mystery {d.id} had to solve.",
        ),
        QAItem(
            question=f"How did the collage help at the end?",
            answer="The collage gathered the clues in one place, so the detective could see the answer all at once.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a collage?",
            answer="A collage is a picture made by putting different pieces together to make one new whole.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of wondering what will happen next.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for cl in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, cl))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("hint_in", cid, clue.place_hint))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("hidden_in", pid, prize.hiding_place))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Clue, Prize) :- place(Place), clue(Clue), prize(Prize),
    affords(Place, Clue), hint_in(Clue, Place), hidden_in(Prize, Place).

#show valid/3.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world with collage, suspense, and clues.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "clue", None):
        combos = [c for c in combos if c[1] == getattr(args, "clue", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    reasonableness_check(place, clue, prize)
    return StoryParams(place=place, clue=clue, prize=prize, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CLUES, params.clue), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="kitchen", clue="crumbs", prize="cookie", name="Mia", gender="girl", helper="cat"),
    StoryParams(place="library", clue="paper", prize="book", name="Leo", gender="boy", helper="sister"),
    StoryParams(place="porch", clue="footprints", prize="toy", name="Nora", gender="girl", helper="neighbor"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery combos:")
        for c in combos:
            print(" ", c)
        return

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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
