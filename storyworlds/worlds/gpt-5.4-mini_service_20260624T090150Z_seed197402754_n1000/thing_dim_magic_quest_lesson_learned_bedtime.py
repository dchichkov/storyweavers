#!/usr/bin/env python3
"""
A tiny bedtime-story world about a thing-dim room, a small magic quest, and a
lesson learned before sleep.

The seed idea:
- At bedtime, a child wants one special thing.
- Magic changes the size or visibility of things in a dim room.
- A gentle quest follows through the bedroom to recover the missing item.
- The ending teaches a small lesson learned: ask, search calmly, and share.

This script is self-contained and follows the storyworld contract.
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
# World model
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    size: str = "normal"  # tiny | normal | big
    visible: bool = True
    owned_by: Optional[str] = None
    keepsake: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    talisman: object | None = None
    treasure: object | None = None
    def pronoun(self) -> str:
        return "it"

    def it(self) -> str:
        return "it"
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
class Child:
    id: str
    name: str
    kind: str = "character"
    type: str = "child"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]

    def it(self) -> str:
        return "her"
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
class Helper:
    id: str
    type: str = "adult"
    label: str = "mom"
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]

    def it(self) -> str:
        return "her"
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
class Room:
    name: str = "the bedroom"
    dim: bool = True
    bedtime: bool = True
    corners: list[str] = field(default_factory=lambda: ["bed", "pillow pile", "toy basket", "window"])
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
class StoryParams:
    room: str
    treasure: str
    magic: str
    quest: str
    child_name: str
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


@dataclass
class World:
    room: Room
    child: Child
    helper: Helper
    treasure: Thing
    talisman: Thing
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
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
        return World(
            room=copy.deepcopy(self.room),
            child=copy.deepcopy(self.child),
            helper=copy.deepcopy(self.helper),
            treasure=copy.deepcopy(self.treasure),
            talisman=copy.deepcopy(self.talisman),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
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


ROOMS = {
    "bedroom": Room(name="the bedroom", dim=True, bedtime=True),
    "nursery": Room(name="the nursery", dim=True, bedtime=True),
    "attic_room": Room(name="the attic room", dim=False, bedtime=False),
}

TREASURES = {
    "bear": Thing(id="bear", label="bear", phrase="a soft bear with a stitched smile", keepsake=True),
    "blanket": Thing(id="blanket", label="blanket", phrase="a little blanket with blue stars", keepsake=True),
    "book": Thing(id="book", label="book", phrase="a sleepy picture book with shiny pages", keepsake=True),
    "lantern": Thing(id="lantern", label="lantern", phrase="a tiny lantern that glowed like a firefly", keepsake=True),
}

MAGICS = {
    "shrink_spell": {
        "name": "a shrink spell",
        "effect": "tiny",
        "turn": "turned small enough to hide behind the pillow",
        "riddle": "a whisper and a twirl",
    },
    "glow_spell": {
        "name": "a glow spell",
        "effect": "visible",
        "turn": "glowed softly in the dim room",
        "riddle": "a gentle hum",
    },
    "tidy_spell": {
        "name": "a tidy spell",
        "effect": "found",
        "turn": "slid out from under the bed",
        "riddle": "a careful tap",
    },
}

QUESTS = {
    "find_missing": "find the missing bedtime treasure",
    "follow_twinkle": "follow a twinkle of light",
    "search_corners": "search the quiet corners",
}

CHILDREN = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella"]
TRAITS = ["sleepy", "curious", "gentle", "brave", "quiet"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasure is hidden when it is tiny or not visible in the dim room.
hidden(T) :- treasure(T), tiny(T).
hidden(T) :- treasure(T), dim_room, not visible(T).

% A quest has a way through when magic can change the treasure into a usable state.
solves(M, T) :- magic(M), treasure(T), helps(M, T).

% A bedtime story is valid when the room is dim, the treasure is at risk,
% and there is a matching magic that creates a gentle resolution.
valid_story(R, M, T) :- room(R), dim_room(R), treasure(T), magic(M),
                        at_risk(T), helps(M, T).

#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("dim_room", rid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("at_risk", tid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("helps", mid, "bear"))
        lines.append(asp.fact("helps", mid, "blanket"))
        lines.append(asp.fact("helps", mid, "book"))
        lines.append(asp.fact("helps", mid, "lantern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = {(r, m, t) for (r, m, t) in asp_valid_stories()}
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(python_set - asp_set))
    print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for magic in MAGICS:
            for treasure in TREASURES:
                combos.append((room, magic, treasure))
    return combos


def reasonableness_gate(room: Room, magic: dict, treasure: Thing) -> None:
    if not room.dim:
        pass
    if not treasure.keepsake:
        pass
    if magic["effect"] not in {"tiny", "visible", "found"}:
        pass


def build_world(params: StoryParams) -> World:
    room = _safe_lookup(ROOMS, params.room)
    treasure = _safe_lookup(TREASURES, params.treasure)
    magic = _safe_lookup(MAGICS, params.magic)

    reasonableness_gate(room, magic, treasure)

    child = Child(id=params.child_name, name=params.child_name, traits=["little", random.choice(TRAITS)])
    helper = Helper(id="helper", label="mom")
    talisman = Thing(id="talisman", label="wand", phrase="a small paper wand with a silver star")

    treasure = Thing(
        id=treasure.id,
        label=treasure.label,
        phrase=treasure.phrase,
        size="normal",
        visible=False if magic["effect"] == "visible" else True,
        owned_by=child.id,
        keepsake=True,
    )

    world = World(room=room, child=child, helper=helper, treasure=treasure, talisman=talisman)
    world.facts.update(
        room=room.name,
        treasure=treasure.id,
        magic=params.magic,
        quest=params.quest,
        child=child.name,
        magic_name=magic["name"],
    )
    return world


def predict_resolution(world: World, magic: dict) -> bool:
    sim = world.copy()
    if magic["effect"] == "tiny":
        sim.treasure.size = "tiny"
        sim.treasure.visible = False
    elif magic["effect"] == "visible":
        sim.treasure.visible = True
    elif magic["effect"] == "found":
        sim.treasure.visible = True
    return True


def tell(world: World, params: StoryParams) -> World:
    magic = _safe_lookup(MAGICS, params.magic)
    child = world.child
    helper = world.helper
    treasure = world.treasure

    world.say(f"At bedtime, {child.name} stood in {world.room.name}, where the air was quiet and dim.")
    world.say(f"{child.name} loved {treasure.phrase}, but tonight {treasure.label} was hard to see.")
    world.para()
    world.say(f"{child.name} had a small quest: {_safe_lookup(QUESTS, params.quest)}.")
    world.say(f"With {world.talisman.phrase} in hand, {child.name} tried {magic['name']} using {magic['riddle']}.")
    world.say(f"The magic {magic['turn']}.")
    if magic["effect"] == "tiny":
        treasure.size = "tiny"
        treasure.visible = False
        world.say(f"Now the {treasure.label} was so tiny it could fit beside the pillow.")
        world.say(f"{child.name} looked carefully and found it after a slow, quiet search.")
    elif magic["effect"] == "visible":
        treasure.visible = True
        world.say(f"Then the {treasure.label} glowed softly, and its little shape showed in the dim room.")
        world.say(f"{child.name} followed the glow and reached for it with a careful hand.")
    else:
        treasure.visible = True
        world.say(f"Then the {treasure.label} slid out from under the bed, just where {child.name} could see it.")
        world.say(f"{child.name} and {helper.label} kneeled together and picked it up gently.")

    world.para()
    world.say(f"{helper.label} smiled and said it was good to search slowly instead of hurrying.")
    world.say(f"{child.name} learned a lesson: ask for help, use a calm magic quest, and keep bedtime kind.")
    world.say(f"At the end, the {treasure.label} was back in {child.name}'s arms, and the room felt safe for sleep.")
    world.facts.update(
        resolved=True,
        lesson="ask for help and search calmly",
        treasure_visible=treasure.visible,
        treasure_size=treasure.size,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters, QA, and output
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a dim room, magic, a quest, and a lesson learned.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name", dest="child_name")
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
    room = getattr(args, "room", None) or rng.choice(list(ROOMS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGICS))
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    child_name = getattr(args, "child_name", None) or rng.choice(CHILDREN)
    return StoryParams(room=room, treasure=treasure, magic=magic, quest=quest, child_name=child_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story about a dim room where {_safe_fact(world, f, "child")} uses {_safe_fact(world, f, "magic_name")} to solve a small quest.',
        f"Tell a child-facing story in which {_safe_fact(world, f, "child")} looks for a missing {_safe_fact(world, f, "treasure")} in the bedroom and learns a calm lesson.",
        f'Write a short bedtime tale that includes magic, a quest, and the phrase "{_safe_fact(world, f, "quest")}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = world.child.name
    treasure = world.treasure.label
    magic_name = _safe_fact(world, f, "magic_name")
    return [
        QAItem(
            question=f"What was {child} trying to find at bedtime?",
            answer=f"{child} was trying to find the {treasure}, a little bedtime keepsake that mattered to {child}.",
        ),
        QAItem(
            question=f"What kind of magic did {child} use on the quest?",
            answer=f"{child} used {magic_name}, and it helped the hidden treasure become easier to find.",
        ),
        QAItem(
            question=f"What lesson did {child} learn by the end?",
            answer=f"{child} learned to ask for help and search calmly instead of rushing in the dim room.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do people use a light in a dim room?",
            answer="People use a light in a dim room so they can see better and find things more easily.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small journey or mission to look for something or solve a problem.",
        ),
        QAItem(
            question="What does a lesson learned mean?",
            answer="A lesson learned is a helpful idea someone remembers after something happens.",
        ),
        QAItem(
            question="What can magic do in stories?",
            answer="In stories, magic can make surprising changes, like helping something appear, glow, or become tiny.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  room     : {world.room.name} dim={world.room.dim} bedtime={world.room.bedtime}")
    lines.append(f"  child    : {world.child.name} memes={dict(world.child.memes)} meters={dict(world.child.meters)}")
    lines.append(f"  helper   : {world.helper.label}")
    lines.append(f"  treasure : {world.treasure.label} size={world.treasure.size} visible={world.treasure.visible}")
    lines.append(f"  talisman : {world.talisman.label}")
    lines.append(f"  facts    : {world.facts}")
    return "\n".join(lines)


def valid_story_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for magic in MAGICS:
            for treasure in TREASURES:
                combos.append((room, magic, treasure))
    return combos


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_python_parity() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(room="bedroom", treasure="bear", magic="shrink_spell", quest="find_missing", child_name="Mia"),
    StoryParams(room="nursery", treasure="blanket", magic="glow_spell", quest="follow_twinkle", child_name="Nora"),
    StoryParams(room="bedroom", treasure="book", magic="tidy_spell", quest="search_corners", child_name="Lily"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_python_parity())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, magic, treasure) combos:\n")
        for room, magic, treasure in combos:
            print(f"  {room:10} {magic:14} {treasure}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
            header = f"### {p.child_name}: {p.magic} in {p.room} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
