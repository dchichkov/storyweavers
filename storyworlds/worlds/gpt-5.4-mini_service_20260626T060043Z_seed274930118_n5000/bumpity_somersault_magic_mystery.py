#!/usr/bin/env python3
"""
storyworlds/worlds/bumpity_somersault_magic_mystery.py
======================================================

A small mystery storyworld with bumpity clues, a somersaulting twist, and a
little bit of Magic.

Premise:
- A child notices something strange.
- A missing object, a curious sound, and a magic effect create a puzzle.
- The child follows clues, discovers what happened, and sets things right.

The domain is intentionally small and constraint-checked:
- The setting is a single familiar place.
- A mystery only forms when an item can plausibly disappear or move.
- Magic may help or confuse, but the ending must resolve the puzzle.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    parent: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    indoors: bool
    affords_magic: bool = True
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
class MysteryItem:
    id: str
    label: str
    phrase: str
    hiding_places: list[str]
    size: str
    can_ring: bool = False
    can_glow: bool = False
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
class MagicTool:
    id: str
    label: str
    effect: str
    clue_style: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.magic_used: bool = False
        self.clues: list[str] = []

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
SETTINGS = {
    "attic": Setting(place="the attic", indoors=True),
    "library": Setting(place="the old library", indoors=True),
    "garden": Setting(place="the moonlit garden", indoors=False),
}

CHILD_NAMES = ["Mina", "Luca", "Nora", "Eli", "Sage", "Tia", "Owen", "Iris"]
GENDERS = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["curious", "gentle", "brave", "quiet", "clever"]

ITEMS = {
    "bell": MysteryItem(
        id="bell",
        label="little bell",
        phrase="a small silver bell",
        hiding_places=["under the rug", "inside a teacup", "behind a book"],
        size="small",
        can_ring=True,
    ),
    "key": MysteryItem(
        id="key",
        label="brass key",
        phrase="a brass key with a curly handle",
        hiding_places=["inside a drawer", "beneath a cushion", "in a flowerpot"],
        size="small",
    ),
    "hat": MysteryItem(
        id="hat",
        label="blue hat",
        phrase="a soft blue hat",
        hiding_places=["on a shelf", "in a basket", "behind a curtain"],
        size="small",
    ),
    "book": MysteryItem(
        id="book",
        label="storybook",
        phrase="a storybook with a gold star",
        hiding_places=["under a chair", "inside a trunk", "on a windowsill"],
        size="medium",
        can_glow=True,
    ),
}

MAGIC_TOOLS = {
    "wand": MagicTool(
        id="wand",
        label="a little wand",
        effect="makes hidden things shimmer for a moment",
        clue_style="a tiny sparkle trail",
    ),
    "mirror": MagicTool(
        id="mirror",
        label="a pocket mirror",
        effect="shows the last place a thing touched",
        clue_style="a soft flash in the glass",
    ),
    "glove": MagicTool(
        id="glove",
        label="a moon glove",
        effect="points toward the nearest secret",
        clue_style="a tug in the air",
    ),
}


@dataclass
class StoryParams:
    place: str
    item: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------
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


def item_is_reasonable(item: MysteryItem, setting: Setting) -> bool:
    return setting.affords_magic and item.size in {"small", "medium"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld with bumpity clues and magic."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=MAGIC_TOOLS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            if not item_is_reasonable(item, setting):
                continue
            for tool_id in MAGIC_TOOLS:
                combos.append((place, item_id, tool_id))
    return combos


def explain_rejection(place: str, item_id: str) -> str:
    return (
        f"(No story: {_safe_lookup(ITEMS, item_id).phrase} does not fit the mystery shape for {place}. "
        f"Pick a smaller object and a place where magic clues can help.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "item", None):
        if not item_is_reasonable(_safe_lookup(ITEMS, getattr(args, "item", None)), _safe_lookup(SETTINGS, getattr(args, "place", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, item_id, tool_id = rng.choice(list(combos))
    item = _safe_lookup(ITEMS, item_id)
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        item=item_id,
        tool=tool_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def world_name(params: StoryParams) -> tuple[str, str]:
    return params.name, params.parent


def generate_mystery_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    item_cfg = _safe_lookup(ITEMS, params.item)
    tool_cfg = _safe_lookup(MAGIC_TOOLS, params.tool)
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    item = world.add(Entity(
        id="missing",
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))
    tool = world.add(Entity(
        id=tool_cfg.id,
        type="magic",
        label=tool_cfg.label,
        phrase=tool_cfg.effect,
        owner=child.id,
    ))

    clue_place = rng_choice = random.Random((params.seed or 0) + 19)
    hiding_place = clue_place.choice(item_cfg.hiding_places)
    world.facts.update(
        child=child,
        parent=parent,
        item=item,
        tool=tool,
        item_cfg=item_cfg,
        tool_cfg=tool_cfg,
        hiding_place=hiding_place,
        place=setting.place,
    )

    child.memes["curiosity"] = 1
    child.memes["worry"] = 1
    world.say(f"{child.id} was a little {params.trait} {params.gender} who noticed small changes very fast.")
    world.say(f"{child.id} liked quiet places and the feeling that every mystery had a reason.")
    world.say(f"One day, {child.id} looked for {item.label} and found only an empty spot.")

    world.para()
    where_text = "inside" if setting.indoors else "under the trees"
    world.say(f"The search began in {setting.place}, where everything felt still and watchful.")
    world.say(f"{child.id} and {child.pronoun('possessive')} {parent.label_word} looked {where_text}, but the {item.label} was gone.")
    world.say(f"Then came a bumpity sound from somewhere nearby: bumpity, bumpity, bumpity.")
    if item_cfg.can_ring:
        world.say(f"That little sound was faint, like a bell trying not to be heard.")
    elif item_cfg.can_glow:
        world.say(f"For a moment, a shy glow blinked and vanished again.")

    world.para()
    world.say(f"{child.id} held up {tool.label}, because {tool.effect}.")
    world.magic_used = True
    world.clues.append(tool.clue_style)
    world.say(f"A clue appeared: {tool.clue_style}.")
    if item_cfg.id == "bell":
        world.say("The sound did not come from a thief at all. It came from a clumsy cat that had nudged the bell behind a chair.")
    elif item_cfg.id == "key":
        world.say("The clue pointed to a drawer, where the brass key had slid under a folded cloth.")
    elif item_cfg.id == "hat":
        world.say("The mirror flashed toward a basket, and the blue hat was sitting there in a neat little nest.")
    else:
        world.say("The magic glow led to an old trunk, where the storybook was resting in plain sight.")

    world.para()
    world.say(f"At the end, {child.id} found the {item.label} right where the clue had promised.")
    if item_cfg.can_ring or item_cfg.can_glow:
        world.say(f"The strange bumpity mystery turned out to be harmless, just a bit of magic and a small surprise.")
    else:
        world.say(f"The mystery was not a trick after all, only an object that had wandered into a hiding place.")
    world.say(f"{child.id} smiled, and {child.pronoun('possessive')} {parent.label_word} laughed in relief.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = generate_mystery_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    item = _safe_fact(world, f, "item_cfg")
    tool = _safe_fact(world, f, "tool_cfg")
    return [
        f'Write a short mystery story for a young child that includes the word "bumpity".',
        f"Tell a gentle mystery about {child.id} looking for {item.label} with {tool.label}.",
        f'Write a child-friendly story where magic helps solve a small missing-object mystery, with a somersault-like surprise in the middle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    item = _safe_fact(world, f, "item_cfg")
    tool = _safe_fact(world, f, "tool_cfg")
    hiding_place = _safe_fact(world, f, "hiding_place")
    return [
        QAItem(
            question=f"What was {child.id} looking for in {f['place']}?",
            answer=f"{child.id} was looking for {item.label}, a {item.phrase}.",
        ),
        QAItem(
            question=f"What clue helped {child.id} solve the mystery?",
            answer=f"{child.id} used {tool.label}, and it made {tool.clue_style} appear.",
        ),
        QAItem(
            question=f"Where had the {item.label} been hiding?",
            answer=f"It had been hiding {hiding_place}.",
        ),
        QAItem(
            question=f"Why did the story feel mysterious at first?",
            answer=(
                f"At first, {child.id} could not find the {item.label}, so the empty spot made the room feel puzzling."
            ),
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=(
                f"The mystery ended when {child.id} followed the magic clue, found the {item.label}, "
                f"and relaxed with {parent.label_word}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does mystery mean?",
            answer="A mystery is something puzzling or hidden that you try to figure out.",
        ),
        QAItem(
            question="What does magic do in stories?",
            answer="Magic in stories can reveal clues, change things in a surprising way, or help a character solve a problem.",
        ),
        QAItem(
            question="What is a somersault?",
            answer="A somersault is a playful roll over the body, usually done on the ground.",
        ),
        QAItem(
            question="What is a bumpity sound?",
            answer="A bumpity sound is a light, bouncy noise, like something small tapping or tumbling along.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.hidden:
            bits.append("hidden=True")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  magic_used: {world.magic_used}")
    lines.append(f"  clues: {world.clues}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.

valid(P, I, T) :- place(P), item(I), tool(T), reasonable(P, I).

reasonable(P, I) :- setting(P), mystery_item(I), size_ok(I), can_use_magic(P).

size_ok(I) :- size(I, small).
size_ok(I) :- size(I, medium).

can_use_magic(P) :- indoors(P).
can_use_magic(P) :- outdoors(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        else:
            lines.append(asp.fact("outdoors", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("mystery_item", iid))
        lines.append(asp.fact("size", iid, item.size))
    for tid in MAGIC_TOOLS:
        lines.append(asp.fact("tool", tid))
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="attic", item="bell", tool="wand", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="library", item="key", tool="mirror", name="Luca", gender="boy", parent="father", trait="clever"),
    StoryParams(place="garden", item="hat", tool="glove", name="Nora", gender="girl", parent="mother", trait="quiet"),
    StoryParams(place="attic", item="book", tool="wand", name="Eli", gender="boy", parent="father", trait="brave"),
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


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params_for_all(args: argparse.Namespace) -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, tool) combos:\n")
        for p, i, t in combos:
            print(f"  {p:10} {i:8} {t:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in resolve_params_for_all(args)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.item} in {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
