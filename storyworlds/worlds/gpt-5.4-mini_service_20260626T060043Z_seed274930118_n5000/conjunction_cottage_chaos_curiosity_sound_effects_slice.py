#!/usr/bin/env python3
"""
Conjunction Cottage Chaos Curiosity Sound Effects Slice

A small slice-of-life storyworld about a curious child, a cozy cottage, and a
gentle bit of chaos caused by the wrong question at the wrong moment. The story
turns on conjunctions: and / but / so / because / then. Sound effects are part
of the world model and help drive the prose.
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
# Core world model
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    name: str
    cozy: bool = True
    affords: set[str] = field(default_factory=set)
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
class CuriousItem:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    fragile: bool = False
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
class SoundEvent:
    id: str
    onomatopoeia: str
    cause: str
    effect: str
    intensity: float = 1.0
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.sound_log: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def note_sound(self, text: str) -> None:
        self.sound_log.append(text)
        self.say(text)

    def copy(self) -> "World":
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.sound_log = list(self.sound_log)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "cottage": Place(
        name="the cottage",
        cozy=True,
        affords={"tea", "baking", "sorting", "reading"},
    ),
    "garden_room": Place(
        name="the garden room",
        cozy=True,
        affords={"tea", "sorting", "reading"},
    ),
}

CHARACTER_TRAITS = ["curious", "gentle", "bouncy", "quiet", "thoughtful"]
NAMES = ["Mina", "Pip", "Tess", "Jun", "Lina", "Noor", "Otis", "Ivy"]

ITEMS = {
    "jar": CuriousItem(
        id="jar",
        label="glass jar",
        phrase="a little glass jar with a blue lid",
        type="jar",
        region="table",
        fragile=True,
    ),
    "spoons": CuriousItem(
        id="spoons",
        label="stack of spoons",
        phrase="a shiny stack of spoons",
        type="spoons",
        region="table",
        fragile=False,
    ),
    "cloth": CuriousItem(
        id="cloth",
        label="tea cloth",
        phrase="a clean tea cloth",
        type="cloth",
        region="table",
        fragile=False,
    ),
}

SOUNDS = {
    "jar_roll": SoundEvent(
        id="jar_roll",
        onomatopoeia="clink-clink",
        cause="jar rolls",
        effect="it makes the counter sound busy",
        intensity=1.0,
    ),
    "spoons_spill": SoundEvent(
        id="spoons_spill",
        onomatopoeia="ting-ting-ting",
        cause="spoons tip over",
        effect="they scatter across the floor",
        intensity=1.0,
    ),
    "chair_squeak": SoundEvent(
        id="chair_squeak",
        onomatopoeia="eeek",
        cause="someone shifts in a chair",
        effect="the room feels extra awake",
        intensity=0.5,
    ),
    "cloth_rustle": SoundEvent(
        id="cloth_rustle",
        onomatopoeia="shff",
        cause="the cloth is folded",
        effect="the table settles down again",
        intensity=0.4,
    ),
}

CONJUNCTIONS = ["and", "but", "so", "because", "then"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    trait: str
    item: str
    sound: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
% A story is reasonable when a curious child is in a cozy cottage,
% the item is fragile enough to be noticed, and the sound is plausible.
curious_child(H) :- child(H), trait(H, curious).
cozy_place(P) :- place(P), cozy(P).

reasonable(H, P, I, S) :- curious_child(H), cozy_place(P), item(I), sound(S),
                           item_in_place(I, P), sound_matches_item(S, I).

#show reasonable/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.cozy:
            lines.append(asp.fact("cozy", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    for trait in CHARACTER_TRAITS:
        lines.append(asp.fact("trait", trait))
    # Generic facts that support the inline rules.
    lines.append(asp.fact("child", "curious_child"))
    lines.append(asp.fact("trait", "curious_child", "curious"))
    for pid in PLACES:
        for iid in ITEMS:
            lines.append(asp.fact("item_in_place", iid, pid))
    for sid, se in SOUNDS.items():
        for iid in ITEMS:
            if (sid == "jar_roll" and iid == "jar") or (sid == "spoons_spill" and iid == "spoons") or (sid == "cloth_rustle" and iid == "cloth"):
                lines.append(asp.fact("sound_matches_item", sid, iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    python = set(valid_combos())
    clingo = set(asp_reasonable())
    if python == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(python)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if python - clingo:
        print("  only in python:", sorted(python - clingo))
    if clingo - python:
        print("  only in clingo:", sorted(clingo - python))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for hero in ["girl", "boy"]:
            for item in ITEMS:
                for sound in SOUNDS:
                    if reasonableness(place, hero, item, sound):
                        combos.append((place, hero, item))
    return combos


def reasonableness(place: str, hero_type: str, item: str, sound: str) -> bool:
    if place not in PLACES:
        return False
    if item not in ITEMS:
        return False
    if sound not in SOUNDS:
        return False
    # The story should hinge on curiosity and a small mess in a cottage.
    if place != "cottage":
        return False
    if item == "cloth" and sound == "jar_roll":
        return False
    return True


def explain_rejection(place: str, hero_type: str, item: str, sound: str) -> str:
    return (
        f"(No story: a {_safe_lookup(ITEMS, item).label} and the sound {_safe_lookup(SOUNDS, sound).onomatopoeia} "
        f"do not make a neat cottage moment in {_safe_lookup(PLACES, place).name}. "
        f"Try the cottage with a matching sound and a curious child.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def build_story(world: World) -> None:
    hero = world.get("hero")
    item = world.get("item")
    helper = world.get("helper")
    sound = _safe_fact(world, world.facts, "sound")

    world.say(
        f"{hero.id} was a {hero.memes['trait']} child who liked to notice tiny things. "
        f"In {world.place.name}, {hero.pronoun('subject')} could hear every little sound."
    )
    world.say(
        f"That morning, {helper.label} set {item.phrase} on the table for tea."
    )
    world.para()
    world.say(
        f"{hero.id} leaned closer {sound.onomatopoeia}, because curiosity was tugging at {hero.memes['curiosity']}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} asked what the lid was doing, and then {hero.pronoun('subject')} reached out."
    )

    # The turn: curiosity causes a small tumble.
    hero.meters["reach"] += 1
    hero.memes["curiosity"] += 1
    item.meters["wobble"] += 1

    if item.id == "jar":
        world.note_sound(
            f"{sound.onomatopoeia}! The {item.label} rolled a little too far."
        )
        world.note_sound("clink-clink")
        world.say(
            f"It bumped the spoon bowl, and the spoons answered with ting-ting-ting."
        )
        world.fired.add(("spill", item.id))
        world.facts["chaos"] = True
    elif item.id == "spoons":
        world.note_sound("ting-ting-ting")
        world.say(
            f"The stack tipped, and the whole table woke up with a bright little clatter."
        )
        world.fired.add(("spill", item.id))
        world.facts["chaos"] = True
    else:
        world.note_sound("shff")
        world.say(
            f"The cloth slipped only a bit, but it made the jar shiver and the room go quiet."
        )
        world.facts["chaos"] = False

    world.para()
    if world.facts.get("chaos"):
        world.say(
            f"{helper.label} paused, but {helper.pronoun('subject')} did not scold."
        )
        world.say(
            f"Instead, {helper.pronoun('subject')} smiled, because little accidents can happen in a cottage."
        )
        world.say(
            f"So {helper.pronoun('subject')} gathered the pieces, folded the cloth, and set the table right again."
        )
        world.note_sound("shff")
        world.say(
            f"{hero.id} helped too, and that made the mess feel smaller."
        )
    else:
        world.say(
            f"There was no real disaster, only a funny wobble, and {hero.id} laughed softly."
        )
        world.say(
            f"Then {helper.pronoun('subject')} moved the item a little farther back, just in case."
        )

    world.para()
    world.say(
        f"In the end, the cottage was calm again, and the tea could begin."
    )
    world.say(
        f"{hero.id} still wanted to know everything, but now {hero.pronoun('subject')} knew how to be careful too."
    )

    world.facts.update(hero=hero, helper=helper, item=item, sound=sound)


def make_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        label=params.hero,
        meters={},
        memes={"trait": params.trait, "curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        label="the grown-up",
        meters={},
        memes={"patience": 1.0},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=_safe_lookup(ITEMS, params.item).type,
        label=_safe_lookup(ITEMS, params.item).label,
        phrase=_safe_lookup(ITEMS, params.item).phrase,
        caretaker="helper",
        meters={"balance": 1.0},
        memes={},
    ))

    world.facts["sound"] = _safe_lookup(SOUNDS, params.sound)
    build_story(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item")
    sound = _safe_fact(world, f, "sound")
    return [
        f'Write a short slice-of-life story about a curious child in a cottage, using the sound "{sound.onomatopoeia}".',
        f"Tell a gentle story where {hero.id} notices {item.label} in the cottage and curiosity leads to a small mess.",
        f"Write a cozy story that includes a cottage, a little chaos, and a kind grown-up who fixes things with patience.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item")
    sound = _safe_fact(world, f, "sound")
    return [
        QAItem(
            question=f"Who was the curious child in the cottage?",
            answer=f"The curious child was {hero.id}. {hero.id} liked to notice tiny things and listen to every sound.",
        ),
        QAItem(
            question=f"What did {hero.id} get interested in?",
            answer=f"{hero.id} got interested in {item.phrase}. That was the thing sitting on the table.",
        ),
        QAItem(
            question=f"What sound helped show that the little chaos started?",
            answer=f"The story used {sound.onomatopoeia} to show the moment curiosity turned into a small tumble.",
        ),
        QAItem(
            question=f"Who helped make the cottage calm again?",
            answer=f"{helper.label} helped make the cottage calm again by gathering things, folding the cloth, and setting the table right.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cottage?",
            answer="A cottage is a small, cozy house, often with a warm and simple feeling inside.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more about something, so you look closely and ask questions.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special words that imitate a noise, like clink-clink or ting-ting-ting.",
        ),
        QAItem(
            question="Why do people say and, but, so, because, and then in stories?",
            answer="Those words help connect ideas, show reasons, and make the story feel smooth and easy to follow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="cottage", hero="Mina", hero_type="girl", trait="curious", item="jar", sound="jar_roll"),
    StoryParams(place="cottage", hero="Pip", hero_type="boy", trait="thoughtful", item="spoons", sound="spoons_spill"),
    StoryParams(place="cottage", hero="Tess", hero_type="girl", trait="gentle", item="cloth", sound="cloth_rustle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy cottage storyworld about curiosity, chaos, and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=CHARACTER_TRAITS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--sound", choices=SOUNDS)
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
    place = getattr(args, "place", None) or "cottage"
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(CHARACTER_TRAITS)
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    sound = getattr(args, "sound", None) or rng.choice(list(SOUNDS))
    hero = getattr(args, "hero", None) or rng.choice(NAMES)

    if not reasonableness(place, hero_type, item, sound):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(place=place, hero=hero, hero_type=hero_type, trait=trait, item=item, sound=sound)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  sounds: {world.sound_log}")
    lines.append(f"  facts: {sorted(world.fired)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        models = asp_reasonable()
        print(f"{len(models)} compatible stories:")
        for p, h, i, s in models:
            print(f"  {p:8} {h:8} {i:8} {s:16}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
