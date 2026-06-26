#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/downward_bike_lane_dialogue_quest_mystery_to.py
================================================================================

A small pirate-tale storyworld set in a bike lane, built around a dialogue-led
quest and a mystery that must be solved.

Premise:
- A little pirate and a helper are traveling beside a bike lane.
- Something precious has slipped downward along the slope.
- The pirate must ask questions, follow clues, and solve the mystery.

Narrative instruments:
- Dialogue
- Quest
- Mystery to Solve

Seed word:
- downward

Style:
- Pirate tale, child-facing, concrete, and state-driven
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "captain_girl", "pirate_girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "captain_boy", "pirate_boy"}:
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
class Setting:
    place: str = "the bike lane"
    slope: str = "downward"
    affordance: str = "rolling"
    setting: object | None = None
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    target: str
    clue: str
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
class HelperDef:
    id: str
    label: str
    role: str
    voice: str
    knows: str
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
    object: str
    helper: str
    name: str
    gender: str
    role: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


OBJECTS = {
    "key": ObjectDef(
        id="key",
        label="golden key",
        phrase="a little golden key for the treasure chest",
        target="gutter",
        clue="a tiny clink near the drain",
    ),
    "map": ObjectDef(
        id="map",
        label="rolled map",
        phrase="a rolled-up map with a red ribbon",
        target="curb",
        clue="a scrap of ribbon by the lane edge",
    ),
    "spyglass": ObjectDef(
        id="spyglass",
        label="spyglass",
        phrase="a brass spyglass with a blue cord",
        target="bush",
        clue="a blue cord caught on a post",
    ),
}

HELPERS = {
    "sailor": HelperDef(
        id="sailor",
        label="old sailor",
        role="sailor",
        voice="gruff but kind",
        knows="the lane slopes downward and loose things roll with it",
    ),
    "rider": HelperDef(
        id="rider",
        label="bicycle rider",
        role="rider",
        voice="bright and careful",
        knows="the shiny thing must have rolled toward the low side",
    ),
    "dockmate": HelperDef(
        id="dockmate",
        label="dock mate",
        role="mate",
        voice="cheery",
        knows="clues hide where the wheels never stop",
    ),
}

NAMES = {
    "girl": ["Mira", "Nina", "Tess", "Ruby", "Lina"],
    "boy": ["Finn", "Otis", "Jace", "Nico", "Theo"],
}
ROLES = ["captain", "first mate", "deckhand"]


def _make_pronoun_type(gender: str, role: str) -> str:
    if gender == "girl":
        return f"{role}_girl"
    return f"{role}_boy"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale in a bike lane with a downward mystery.")
    ap.add_argument("--setting", choices=["bike_lane"], default="bike_lane")
    ap.add_argument("--object", choices=OBJECTS, default=None)
    ap.add_argument("--helper", choices=HELPERS, default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--role", choices=ROLES, default=None)
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
    obj = getattr(args, "object", None) or rng.choice(sorted(OBJECTS))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    role = getattr(args, "role", None) or rng.choice(ROLES)
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    return StoryParams(
        setting="bike_lane",
        object=obj,
        helper=helper,
        name=name,
        gender=gender,
        role=role,
    )


def _do_roll(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.meters["seek"] = hero.meters.get("seek", 0) + 1
    obj.meters["downward"] = obj.meters.get("downward", 0) + 1
    obj.meters["distance"] = obj.meters.get("distance", 0) + 3
    world.facts["lost"] = True


def _predict_find(world: World, obj: Entity) -> bool:
    sim = world.copy()
    sim_obj = sim.get(obj.id)
    sim_obj.meters["distance"] = sim_obj.meters.get("distance", 0) + 3
    return sim_obj.meters["distance"] >= 3


def generate_story(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('role', 'pirate')} with a sharp eye for trouble."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the {world.setting.place}, where the wind and wheels made a merry racket."
    )
    world.say(
        f"One day, {hero.id} saw {obj.phrase} beside the {world.setting.place}, and the path sloped {world.setting.slope}."
    )
    world.para()
    world.say(
        f'"Have ye seen me {obj.label}?" {hero.id} asked.'
    )
    world.say(
        f'"Arrr, not yet," said the {helper.label}. "{helper.knows.capitalize()}."'
    )
    world.say(
        f"{hero.id} pointed at the lane edge. '{obj.clue},' {hero.pronoun()} whispered."
    )
    _do_roll(world, hero, obj)
    world.say(
        f"The little pirate followed the clue and walked {world.setting.slope} along the lane."
    )
    world.para()
    if _predict_find(world, obj):
        world.say(
            f'"If it rolled that way, it may be hiding by the {obj.target}," said the {helper.label}.'
        )
        world.say(
            f'"Then let us search the low side!" said {hero.id}.'
        )
        world.say(
            f"At last, {hero.id} found the {obj.label} where the lane dipped low, just as the helper guessed."
        )
        world.say(
            f"{hero.id} grinned, tucked {obj.it()} safely away, and said, 'The mystery be solved!'"
        )
    else:
        world.say(
            f"The clue led nowhere, and the pirate had to keep looking."
        )
    world.say(
        f"By the end, the {obj.label} was back in {hero.pronoun('possessive')} hand, and the {world.setting.place} felt calm again."
    )


def tell(setting: Setting, obj_def: ObjectDef, helper_def: HelperDef, name: str, gender: str, role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=_make_pronoun_type(gender, role),
        memes={"role": role, "joy": 0.0, "worry": 0.0, "curiosity": 1.0},
        meters={"seek": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_def.label,
        kind="character",
        type="sailor" if helper_def.id == "sailor" else "rider",
        label=helper_def.label,
        memes={"helpful": 1.0},
    ))
    obj = world.add(Entity(
        id=obj_def.id,
        kind="thing",
        type="treasure",
        label=obj_def.label,
        phrase=obj_def.phrase,
        owner=hero.id,
        meters={"distance": 0.0, "downward": 0.0},
    ))
    generate_story(world, hero, helper, obj)
    world.facts.update(hero=hero, helper=helper, obj=obj, obj_def=obj_def, helper_def=helper_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    obj_def = _safe_fact(world, f, "obj_def")
    return [
        f"Write a pirate tale about {hero.id} solving a mystery in the bike lane.",
        f"Tell a short story where a little pirate asks questions and finds the {obj_def.label}.",
        f"Write a child-friendly dialogue story about something that rolls downward beside a bike lane.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    obj_def = _safe_fact(world, f, "obj_def")
    helper_def = _safe_fact(world, f, "helper_def")
    return [
        QAItem(
            question=f"What did {hero.id} have to solve in the bike lane?",
            answer=f"{hero.id} had to solve the mystery of the missing {obj_def.label}.",
        ),
        QAItem(
            question=f"Who gave {hero.id} a clue about where the {obj_def.label} went?",
            answer=f"The {helper_def.label} gave {hero.id} a clue and helped think through the mystery.",
        ),
        QAItem(
            question=f"Why did the {obj_def.label} go downward?",
            answer=f"It went downward because the bike lane sloped downward, so the loose treasure rolled toward the low side.",
        ),
        QAItem(
            question=f"Where did {hero.id} find the {obj_def.label} at the end?",
            answer=f"{hero.id} found it by the low side of the bike lane, near the place named for its hiding spot.",
        ),
    ]


KNOWLEDGE = {
    "downward": [
        QAItem(
            question="What does downward mean?",
            answer="Downward means going toward a lower place.",
        )
    ],
    "bike_lane": [
        QAItem(
            question="What is a bike lane for?",
            answer="A bike lane is a marked part of the road where bicycles are meant to ride safely.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not known yet, so people look for clues to solve it.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters talk to each other in a story.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    return [
        *KNOWLEDGE["downward"],
        *KNOWLEDGE["bike_lane"],
        *KNOWLEDGE["mystery"],
        *KNOWLEDGE["quest"],
        *KNOWLEDGE["dialogue"],
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
setting(bike_lane).
object(key).
object(map).
object(spyglass).
helper(sailor).
helper(rider).
helper(dockmate).
valid(S, O, H) :- setting(S), object(O), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "bike_lane")]
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {("bike_lane", o, h) for o in OBJECTS for h in HELPERS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bike_lane", o, h) for o in OBJECTS for h in HELPERS]


def explain_rejection() -> str:
    return "(No story: this world only supports the bike lane, a lost object, and a helper.)"


def generate(params: StoryParams) -> StorySample:
    setting = Setting()
    world = tell(setting, _safe_lookup(OBJECTS, params.object), _safe_lookup(HELPERS, params.helper), params.name, params.gender, params.role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="bike_lane", object="key", helper="sailor", name="Mira", gender="girl", role="captain"),
    StoryParams(setting="bike_lane", object="map", helper="rider", name="Finn", gender="boy", role="first mate"),
    StoryParams(setting="bike_lane", object="spyglass", helper="dockmate", name="Ruby", gender="girl", role="deckhand"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible combinations:\n")
        for s, o, h in combos:
            print(f"  {s:10} {o:10} {h}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.object} with {p.helper} in the bike lane"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
