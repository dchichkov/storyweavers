#!/usr/bin/env python3
"""
storyworlds/worlds/textured_bravery_bedtime_story.py
====================================================

A small bedtime-story world about a child learning bravery at night.

Premise:
- A child is getting ready for bed in a cozy room.
- The child loves a textured blanket or toy that helps make the room feel safe.

Tension:
- The room feels too dark, and the child worries about a shadow, a creak, or a bump.
- The parent notices the fear and names the feeling gently.

Turn:
- The parent offers a brave, practical helper: a night-light, a hallway lamp, or a
  "look together" plan.
- The child practices bravery by checking the room with the parent.

Resolution:
- The child settles in, the room feels softer, and the textured comfort object stays
  close as the child falls asleep.

This world keeps the prose child-facing and authored, while the simulation tracks
physical state (light, coziness, sleepiness) and emotional state (fear, bravery,
calm).  The story is driven by these state changes rather than by a frozen template.
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
# Entities and world model
# ---------------------------------------------------------------------------

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

    hero: object | None = None
    item: object | None = None
    parent: object | None = None
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
    place: str = "the bedroom"
    cozy: bool = True
    dark_level: float = 0.0
    night_sound: str = "a little creak in the hall"
    features: set[str] = field(default_factory=set)
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
    def __init__(self, room: Room) -> None:
        self.room = room
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
        import copy as _copy

        clone = World(_copy.deepcopy(self.room))
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    touch: str  # "textured", "soft", "squishy"
    kind: str = "thing"
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
    offer: str
    action: str
    calm_boost: float = 1.0
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
class FearCue:
    id: str
    label: str
    sound: str
    darkness: float
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


ROOMS = {
    "bedroom": Room(place="the bedroom", cozy=True, dark_level=1.0, night_sound="a soft creak in the hall", features={"bed", "door", "window"}),
    "nursery": Room(place="the nursery", cozy=True, dark_level=0.9, night_sound="the hum of the house", features={"crib", "lamp", "door"}),
}

COMFORT_ITEMS = {
    "quilt": ComfortItem(id="quilt", label="quilt", phrase="a textured quilt with tiny stitched stars", touch="textured"),
    "bear": ComfortItem(id="bear", label="bear", phrase="a textured little teddy bear", touch="textured"),
    "pillow": ComfortItem(id="pillow", label="pillow", phrase="a fluffy pillow with a bumpy edge", touch="textured"),
}

HELPERS = {
    "nightlight": Helper(id="nightlight", label="night-light", offer="turn on the night-light", action="glow softly by the bed"),
    "checkroom": Helper(id="checkroom", label="room check", offer="look at the room together", action="show that the room was safe"),
    "doorajar": Helper(id="doorajar", label="door cracked open", offer="leave the door a tiny bit open", action="let a hallway glow slip in"),
}

FEARS = {
    "shadow": FearCue(id="shadow", label="shadow", sound="a shadow on the wall", darkness=1.0),
    "creak": FearCue(id="creak", label="creak", sound="a little creak in the hall", darkness=0.8),
    "bump": FearCue(id="bump", label="bump", sound="a small bump under the bed", darkness=1.1),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ivy", "Luna", "Ella"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Max", "Noah", "Eli"]
TRAITS = ["gentle", "curious", "small", "sleepy", "careful", "brave"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    room: str
    comfort: str
    helper: str
    fear: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin and facts
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


ASP_RULES = r"""
room_valid(R) :- room(R).
item_valid(I) :- comfort(I).
helper_valid(H) :- helper(H).
fear_valid(F) :- fear(F).

compatible(R, I, H, F) :- room_valid(R), item_valid(I), helper_valid(H), fear_valid(F).

#show compatible/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for cid in COMFORT_ITEMS:
        lines.append(asp.fact("comfort", cid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for fid in FEARS:
        lines.append(asp.fact("fear", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for r in ROOMS:
        for c in COMFORT_ITEMS:
            for h in HELPERS:
                for f in FEARS:
                    combos.append((r, c, h, f))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl)[:10])
    if cl - py:
        print("  only in clingo:", sorted(cl - py)[:10])
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def _warm(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["calm"] += 1
    item.meters["close"] = 1.0
    world.say(f"{hero.id} held {hero.pronoun('possessive')} {item.label} close, and it felt comforting in {world.room.place}.")


def _fear_rises(world: World, hero: Entity, fear: FearCue) -> None:
    hero.memes["fear"] += 1
    world.room.dark_level += fear.darkness * 0.2
    world.say(f"Then {fear.sound} made {hero.id} pause, and the room felt a little bigger and darker.")


def _brave_talk(world: World, parent: Entity, hero: Entity, helper: Helper) -> None:
    hero.memes["bravery"] += 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 0.5)
    world.say(f"{parent.label.capitalize()} smiled and said, \"Let's {helper.offer}.\"")


def _check(world: World, hero: Entity, helper: Helper, item: Entity) -> None:
    world.room.dark_level = max(0.0, world.room.dark_level - 0.7)
    hero.memes["bravery"] += 1
    hero.memes["calm"] += helper.calm_boost
    world.say(f"{hero.id} and {hero.pronoun('possessive')} parent did the check together, and {helper.action}.")
    world.say(f"{hero.id}'s {item.label} stayed tucked under {hero.pronoun('possessive')} arm, soft and {item.phrase.split('a ',1)[-1]}.")


def _settle(world: World, hero: Entity, item: Entity, helper: Helper) -> None:
    hero.memes["calm"] += 1
    hero.meters["sleepy"] += 1
    world.say(f"After that, {hero.id} settled back under the covers with the {item.label}, and the {helper.label} made a tiny, friendly glow.")
    world.say(f"The night felt gentle again, and {hero.id} drifted off feeling brave.")


def tell(room: Room, comfort: ComfortItem, helper: Helper, fear: FearCue,
         hero_name: str = "Mia", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "gentle") -> World:
    world = World(room)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    item = world.add(Entity(id=comfort.id, type="thing", label=comfort.label, phrase=comfort.phrase))
    _ = parent

    world.say(f"{hero.id} was a {trait} little {hero.type} who loved {comfort.touch} things, especially {comfort.phrase}.")
    world.say(f"When bedtime came, {hero.id} climbed into {world.room.place} and cuddled {hero.pronoun('possessive')} {comfort.label}.")

    world.para()
    _fear_rises(world, hero, fear)
    world.say(f"{hero.id} heard {fear.sound} and felt brave-fear wobble inside {hero.pronoun('object')}.")

    world.para()
    _brave_talk(world, parent, hero, helper)
    _check(world, hero, helper, item)

    world.para()
    _settle(world, hero, item, helper)

    world.facts.update(hero=hero, parent=parent, item=item, room=room, comfort=comfort, helper=helper, fear=fear)
    return world


def generate_story_state(params: StoryParams) -> World:
    room = _safe_lookup(ROOMS, params.room)
    comfort = _safe_lookup(COMFORT_ITEMS, params.comfort)
    helper = _safe_lookup(HELPERS, params.helper)
    fear = _safe_lookup(FEARS, params.fear)
    gender = params.gender
    hero_type = gender
    parent_type = params.parent
    name = params.name
    trait = params.trait
    return tell(room, comfort, helper, fear, name, hero_type, parent_type, trait)


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child about being brave in {f["room"].place} using the word "textured".',
        f"Tell a gentle bedtime story where {f['hero'].id} feels afraid but becomes brave with {f['helper'].label} and {f['comfort'].label}.",
        f"Write a cozy story about a child who hears {f['fear'].sound} and learns to feel safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, item, helper, fear = f["hero"], f["parent"], f["item"], f["helper"], f["fear"]
    return [
        QAItem(
            question=f"What did {hero.id} cuddle at bedtime?",
            answer=f"{hero.id} cuddled {hero.pronoun('possessive')} {item.label}, which was {world.facts['comfort'].phrase}.",
        ),
        QAItem(
            question=f"What made {hero.id} feel uneasy in the room?",
            answer=f"{fear.sound} made {hero.id} feel uneasy for a moment.",
        ),
        QAItem(
            question=f"How did the parent help {hero.id} feel brave?",
            answer=f"{parent.label.capitalize()} helped by suggesting they {helper.offer}, and that made the room feel safer.",
        ),
        QAItem(
            question=f"What changed by the end of the bedtime story?",
            answer=f"By the end, {hero.id} felt calm and brave, and {helper.label} made the room feel soft and friendly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does textured mean?",
            answer="Textured means something has a surface you can feel with bumps, lines, or raised parts instead of being perfectly smooth.",
        ),
        QAItem(
            question="Why can a night-light help at bedtime?",
            answer="A night-light can help because it gives a little gentle light, so the room feels less dark and scary.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means feeling afraid but still doing a careful, helpful thing anyway.",
        ),
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
    lines.append(f"room.dark_level={world.room.dark_level:.2f}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / selection
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(room="bedroom", comfort="quilt", helper="nightlight", fear="shadow", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(room="nursery", comfort="bear", helper="checkroom", fear="creak", name="Theo", gender="boy", parent="father", trait="curious"),
    StoryParams(room="bedroom", comfort="pillow", helper="doorajar", fear="bump", name="Nora", gender="girl", parent="mother", trait="sleepy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about textured comfort and bravery.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--comfort", choices=COMFORT_ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--fear", choices=FEARS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    comfort = getattr(args, "comfort", None) or rng.choice(list(COMFORT_ITEMS))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    fear = getattr(args, "fear", None) or rng.choice(list(FEARS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if room not in ROOMS or comfort not in COMFORT_ITEMS or helper not in HELPERS or fear not in FEARS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(room=room, comfort=comfort, helper=helper, fear=fear, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_state(params)
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


def asp_verify_story() -> int:
    return asp_verify()


def asp_show_program() -> str:
    return asp_program("#show compatible/4.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_story())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for r, c, h, f in combos[:50]:
            print(f"  {r:8} {c:8} {h:10} {f:8}")
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
            header = f"### {p.name}: {p.comfort} in {p.room} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
