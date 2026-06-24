#!/usr/bin/env python3
"""
storyworlds/worlds/appetizer_flashback_surprise_quest_ghost_story.py
====================================================================

A small ghost-story world about a child, an appetizer, a flashback, a surprise,
and a quest through a spooky house.

Premise:
- A hungry child wants an appetizer before dinner.
- A harmless ghost lives near the kitchen and remembers a clue from long ago.
- A surprise sends the child on a little quest.
- The quest leads to a gentle ending where the appetizer is found and shared.

The world is intentionally tiny and classical: a few entities, a few state
changes, and prose that follows from simulation rather than a frozen template.
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
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    appetizer: object | None = None
    child: object | None = None
    ghost: object | None = None
    parent: object | None = None
    recipe_card: object | None = None
    def pronoun(self, case: str = "subject") -> str:
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
class Room:
    id: str
    label: str
    spooky: int = 0
    hides: set[str] = field(default_factory=set)
    connects: set[str] = field(default_factory=set)
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
class StoryParams:
    setting: str
    appetizer: str
    child_name: str
    child_type: str
    parent_type: str
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


class World:
    def __init__(self, setting: Room) -> None:
        self.setting = setting
        self.rooms: dict[str, Room] = {}
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_room(self, room: Room) -> Room:
        self.rooms[room.id] = room
        return room

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
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "kitchen": Room(
        id="kitchen",
        label="the kitchen",
        spooky=0,
        hides={"crumbs"},
        connects={"hall"},
    ),
    "hall": Room(
        id="hall",
        label="the hall",
        spooky=1,
        hides={"door", "footsteps"},
        connects={"kitchen", "attic", "parlor"},
    ),
    "attic": Room(
        id="attic",
        label="the attic",
        spooky=3,
        hides={"old box", "recipe card"},
        connects={"hall"},
    ),
    "parlor": Room(
        id="parlor",
        label="the parlor",
        spooky=2,
        hides={"candlestick", "tray"},
        connects={"hall"},
    ),
}

APPETIZERS = {
    "toast": {
        "label": "toast triangles",
        "phrase": "warm toast triangles with butter",
        "scent": "buttery",
        "crumbs": True,
    },
    "soup": {
        "label": "a small cup of soup",
        "phrase": "a small cup of tomato soup",
        "scent": "savory",
        "crumbs": False,
    },
    "apple": {
        "label": "apple slices",
        "phrase": "apple slices with a tiny dip",
        "scent": "sweet",
        "crumbs": False,
    },
    "crackers": {
        "label": "buttery crackers",
        "phrase": "buttery crackers on a blue plate",
        "scent": "toasty",
        "crumbs": True,
    },
}

GHOSTS = {
    "Milo": "gentle",
    "Mina": "gentle",
    "Nora": "quiet",
    "Pip": "curious",
}

CHILD_NAMES = ["Leo", "Mia", "Nora", "Eli", "Zoe", "Ava", "Ben", "Lily"]
TRAITS = ["brave", "curious", "sleepy", "patient", "shy", "lively"]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.setting not in ROOMS:
        pass
    if params.appetizer not in APPETIZERS:
        pass

    world = World(setting=_safe_lookup(ROOMS, params.setting))
    for room in ROOMS.values():
        world.add_room(Room(room.id, room.label, room.spooky, set(room.hides), set(room.connects)))

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
        room=params.setting,
        meters={"hunger": 1.0, "courage": 0.5},
        memes={"wonder": 1.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        room=params.setting,
        meters={"patience": 1.0},
        memes={"care": 1.0},
    ))
    ghost = world.add(Entity(
        id=params.ghost_name,
        kind="character",
        type="ghost",
        label=params.ghost_name,
        room="hall",
        meters={"mist": 1.0},
        memes={"memory": 1.0, "kindness": 1.0},
    ))
    appetizer = world.add(Entity(
        id="appetizer",
        kind="thing",
        type="food",
        label=_safe_lookup(APPETIZERS, params.appetizer)["label"],
        phrase=_safe_lookup(APPETIZERS, params.appetizer)["phrase"],
        room="parlor",
        owner=parent.id,
    ))
    recipe_card = world.add(Entity(
        id="recipe_card",
        kind="thing",
        type="card",
        label="an old recipe card",
        phrase="an old recipe card with a tiny note on the back",
        room="attic",
    ))

    # Act 1: setup
    world.say(
        f"Late one evening, {child.label} was still awake in {world.setting.label}, "
        f"thinking about {appetizer.phrase}."
    )
    world.say(
        f"{child.label} loved the smell of supper, but {appetizer.label} sounded even better."
    )
    world.para()

    # Act 2: flashback + surprise
    world.say(
        f"A soft sigh drifted from the hall, and {ghost.label} floated in with a moon-pale smile."
    )
    world.say(
        f'"I remember this house," {ghost.label} whispered. "Long ago, a little note was hidden for a hungry child."'
    )
    world.say(
        f"That was the flashback: years before, the same family had once tucked a recipe card away so no one would forget the favorite snack."
    )
    world.facts["flashback"] = True

    world.para()
    world.say(
        f"Then came the surprise. The kitchen lamp blinked once, and the air felt chilly."
    )
    world.say(
        f"{parent.label.capitalize()} opened the empty platter and gasped. {appetizer.label} was gone."
    )
    world.say(
        f"{child.label} hugged close to the doorway, while {ghost.label} pointed toward the hall."
    )
    world.facts["surprise"] = True

    # Act 3: quest
    world.para()
    child.memes["quest"] = 1.0
    world.say(
        f'"If we follow the old clue," {ghost.label} said, "we can find the lost appetizer."'
    )
    world.say(
        f"So {child.label}, {parent.label}, and {ghost.label} began a small quest through {world.rooms["hall"].label}."
    )
    world.say(
        f"They crossed the hall to the parlor, where a silver tray waited in the dark."
    )
    world.say(
        f"Under the tray was the recipe card, and beneath that was the missing {appetizer.label}."
    )
    world.say(
        f"{parent.label.capitalize()} laughed softly, not from fear now, but from relief."
    )

    # Resolution: state updates
    appetizer.room = params.setting
    child.meters["hunger"] = 0.0
    child.memes["wonder"] += 1.0
    parent.memes["care"] = 2.0
    ghost.memes["memory"] = 0.0
    world.facts["resolved"] = True

    world.para()
    world.say(
        f"Back in {world.setting.label}, {child.label} ate the {appetizer.label} at last."
    )
    world.say(
        f"The little ghost smiled because the house felt warm again, and the recipe card had found its way home."
    )

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        appetizer=appetizer,
        recipe_card=recipe_card,
        setting=params.setting,
        appetizer_kind=params.appetizer,
    )
    return world


# ---------------------------------------------------------------------------
# QA / prose helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly ghost story that includes a flashback, a surprise, and a quest for an appetizer.',
        f"Tell a spooky-but-kind story where {f['child'].label} wants {f['appetizer'].phrase} and a ghost helps find it.",
        f"Write a short story set in {world.setting.label} where a hidden snack is found after a mysterious clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    ghost = _safe_fact(world, f, "ghost")
    appetizer = _safe_fact(world, f, "appetizer")
    setting = world.setting.label

    return [
        QAItem(
            question=f"Who wanted the appetizer in {setting}?",
            answer=f"{child.label} wanted the appetizer, and the smell of supper made it feel even more tempting.",
        ),
        QAItem(
            question="What was the flashback in the story about?",
            answer="The flashback was about an old recipe card being hidden long ago so the family would remember the favorite snack.",
        ),
        QAItem(
            question="What surprise happened in the story?",
            answer=f"The surprise was that {appetizer.label} had gone missing from the kitchen platter.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"{child.label}, {parent.label}, and {ghost.label} followed the clue to the parlor and found the missing appetizer, then shared it back in the kitchen.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "ghost": [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is often a spooky-looking figure made from imagination, and it can be friendly, lonely, or mysterious.",
        )
    ],
    "appetizer": [
        QAItem(
            question="What is an appetizer?",
            answer="An appetizer is a small first food served before the main meal, so people can taste something little while they wait.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something from the past, as if the story takes a little step backward in time.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something, solve a problem, or finish an important task.",
        )
    ],
    "surprise": [
        QAItem(
            question="What makes a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters thought would happen.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["ghost"],
        *WORLD_KNOWLEDGE["appetizer"],
        *WORLD_KNOWLEDGE["flashback"],
        *WORLD_KNOWLEDGE["quest"],
        *WORLD_KNOWLEDGE["surprise"],
    ]


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
        bits = []
        if e.room:
            bits.append(f"room={e.room}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
appetizer(appetizer).
ghost(ghost).
child(child).

setting(kitchen).
setting(hall).
setting(attic).
setting(parlor).

quest_ok(S) :- setting(S), flashback, surprise.
found(Thing) :- appetizer(Thing), quest_ok(_).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for nxt in sorted(room.connects):
            lines.append(asp.fact("connects", rid, nxt))
        for hid in sorted(room.hides):
            lines.append(asp.fact("hides", rid, hid))
    for aid in APPETIZERS:
        lines.append(asp.fact("appetizer", aid))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("flashback"))
    lines.append(asp.fact("surprise"))
    lines.append(asp.fact("quest"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show found/1."))
    atoms = set(asp.atoms(model, "found"))
    ok = ("appetizer",) in atoms
    if ok:
        print("OK: ASP twin recognizes the quest and the found appetizer.")
        return 0
    print("MISMATCH: ASP twin did not derive found(appetizer).")
    return 1


# ---------------------------------------------------------------------------
# Parameterization and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    appetizer: str
    child_name: str
    child_type: str
    parent_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small ghost story world with an appetizer, flashback, surprise, and quest."
    )
    ap.add_argument("--setting", choices=sorted(ROOMS))
    ap.add_argument("--appetizer", choices=sorted(APPETIZERS))
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--ghost-name", choices=sorted(GHOSTS))
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
    setting = getattr(args, "setting", None) or rng.choice(sorted(ROOMS))
    appetizer = getattr(args, "appetizer", None) or rng.choice(sorted(APPETIZERS))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    parent_type = getattr(args, "parent_type", None) or rng.choice(["mother", "father"])
    ghost_name = getattr(args, "ghost_name", None) or rng.choice(sorted(GHOSTS))
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    if setting == "attic" and appetizer == "soup":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        setting=setting,
        appetizer=appetizer,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        ghost_name=ghost_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
# Main / CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="kitchen", appetizer="toast", child_name="Mia", child_type="girl", parent_type="mother", ghost_name="Milo"),
    StoryParams(setting="parlor", appetizer="crackers", child_name="Leo", child_type="boy", parent_type="father", ghost_name="Nora"),
    StoryParams(setting="hall", appetizer="apple", child_name="Ava", child_type="girl", parent_type="mother", ghost_name="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show found/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show found/1."))
        print(sorted(asp.atoms(model, "found")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.child_name}: appetizer={p.appetizer} setting={p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
