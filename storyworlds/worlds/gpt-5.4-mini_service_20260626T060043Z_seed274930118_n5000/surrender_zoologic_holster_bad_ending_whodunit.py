#!/usr/bin/env python3
"""
Standalone storyworld: a small whodunit with a bad ending.

Premise:
- A child-like investigator follows clues in a zoologic hall.
- A missing holster becomes the center of suspicion.
- The truth is found, but the ending is bad: the culprit is not stopped in time,
  and the holster is surrendered to the wrong hands.

The world is deliberately tiny and state-driven: clues, suspicion, trust,
possession, and a final failed resolution are all represented in meters/memes.
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
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Setting:
    place: str = "the zoologic hall"
    mood: str = "quiet"
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
class Clue:
    id: str
    label: str
    found_at: str
    points_to: str
    certainty: float = 1.0
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
class Suspect:
    id: str
    type: str
    label: str
    alibi: str
    motive: str
    location: str
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
    place: str
    clue: str
    suspect: str
    name: str
    gender: str
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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _py_story_title() -> str:
    return "The Zoologic Holster Surrender"


def introduce(world: World, hero: Entity, place: str) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'curious')} "
        f"{hero.type} who liked mysteries."
    )
    world.say(
        f"One quiet evening at {place}, {hero.id} noticed that something important was gone."
    )


def set_scene(world: World, clue: Clue) -> None:
    world.say(
        f"The lamps were dim in the zoologic hall, and every glass case looked like it was keeping a secret."
    )
    world.say(
        f"Near the reptile display, {clue.found_at} {clue.label} waited like a small message."
    )


def investigate(world: World, hero: Entity, clue: Clue, suspect: Suspect, holster: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0) + clue.certainty
    world.say(
        f"{hero.id} followed the clue and whispered, 'Who would take a holster from a place like this?'"
    )
    world.say(
        f"The clue pointed toward {suspect.label}, but {suspect.alibi} made the answer feel slippery."
    )
    if holster.held_by:
        world.say(
            f"By then, the holster was already in {world.get(holster.held_by).label}'s hands."
        )


def question_suspect(world: World, hero: Entity, suspect: Suspect, holster: Entity) -> None:
    hero.memes["doubt"] = hero.memes.get("doubt", 0) + 1
    world.say(
        f"{hero.id} asked the hard question: 'Why were you near the case when the holster vanished?'"
    )
    world.say(
        f"{suspect.label} only gave {suspect.alibi}, which did not sound as clean as it should have."
    )
    if holster.held_by == suspect.id:
        world.say(
            f"That was the worst part: the holster was already tucked away with {suspect.label}."
        )


def reveal_truth(world: World, hero: Entity, suspect: Suspect, holster: Entity, clue: Clue) -> None:
    world.say(
        f"The clue finally made sense. The missing holster had been moved during the feeding hour, when no one was watching."
    )
    world.say(
        f"{suspect.label} had the best chance to take it, because {suspect.motive} and the door to the case had been left open."
    )
    hero.memes["certainty"] = hero.memes.get("certainty", 0) + 1
    world.facts["truth"] = suspect.id
    world.facts["clue"] = clue.id


def surrender(world: World, hero: Entity, suspect: Suspect, holster: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.say(
        f"{hero.id} reached the final choice and begged, 'Please surrender the holster now.'"
    )
    world.say(
        f"But the night had already tipped the wrong way, and {suspect.label} did not hand it over."
    )
    holster.held_by = suspect.id
    world.facts["bad_end"] = True


def bad_ending(world: World, hero: Entity, suspect: Suspect, holster: Entity) -> None:
    world.say(
        f"When the alarm finally rang, it was too late. The holster was gone again, and the case stood open like a missing tooth."
    )
    world.say(
        f"{hero.id} solved the mystery, but the museum lost the holster anyway, and the zoo-quiet hall stayed empty and sad."
    )
    world.say(
        f"No one cheered. The last light went out over the zoologic hall, and the ending remained unfair."
    )


SETTINGS = {
    "zoologic hall": Setting(place="the zoologic hall", mood="quiet", affords={"mystery"}),
}


CLUES = {
    "feather": Clue(
        id="feather",
        label="a damp feather",
        found_at="by the slatted cage",
        points_to="birdkeeper",
        certainty=1.0,
    ),
    "mud": Clue(
        id="mud",
        label="a brown muddy print",
        found_at="under the bench",
        points_to="keeper",
        certainty=1.0,
    ),
    "seed": Clue(
        id="seed",
        label="a cracked seed pouch",
        found_at="beside the supply shelf",
        points_to="supplyrunner",
        certainty=1.0,
    ),
}

SUSPECTS = {
    "keeper": Suspect(
        id="keeper",
        type="woman",
        label="the keeper",
        alibi="she said she was checking the night lock",
        motive="she wanted the spare tool pouch for the feeding cart",
        location="the lock room",
    ),
    "birdkeeper": Suspect(
        id="birdkeeper",
        type="man",
        label="the birdkeeper",
        alibi="he said he was counting pellets",
        motive="he needed a carrier clip and a free hand",
        location="the aviary side door",
    ),
    "supplyrunner": Suspect(
        id="supplyrunner",
        type="man",
        label="the supply runner",
        alibi="he said he was bringing paper labels",
        motive="he liked to borrow anything that hung from a belt",
        location="the back hallway",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, s) for p in SETTINGS for c in CLUES for s in SUSPECTS]


@dataclass
class WorldState:
    hero: Entity
    suspect: Suspect
    clue: Clue
    holster: Entity
    setting: Setting
    truth_found: bool = False
    bad_end: bool = False
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


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            traits=["little", "curious", "careful"],
        )
    )
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    clue = _safe_lookup(CLUES, params.clue)
    holster = world.add(
        Entity(
            id="holster",
            kind="thing",
            type="holster",
            label="the holster",
            phrase="a small leather holster",
            owner=hero.id,
            held_by=suspect.id,
            location=world.setting.place,
        )
    )

    world.say(f"{_py_story_title()} began with a missing holster.")
    introduce(world, hero, world.setting.place)
    world.para()
    set_scene(world, clue)
    investigate(world, hero, clue, suspect, holster)
    question_suspect(world, hero, suspect, holster)
    world.para()
    reveal_truth(world, hero, suspect, holster, clue)
    surrender(world, hero, suspect, holster)
    world.para()
    bad_ending(world, hero, suspect, holster)

    world.facts.update(
        hero=hero,
        suspect=suspect,
        clue=clue,
        holster=holster,
        setting=world.setting,
        truth_found=True,
        bad_end=True,
    )
    return world


KNOWLEDGE = {
    "holster": [
        (
            "What is a holster?",
            "A holster is a holder for something small, often made to keep an item safe and easy to carry.",
        )
    ],
    "zoologic": [
        (
            "What does zoologic mean?",
            "Zoologic means related to animals and places where animals are studied or kept.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something puzzling that people try to figure out by looking for clues.",
        )
    ],
    "surrender": [
        (
            "What does surrender mean?",
            "To surrender means to give something up or stop fighting for it.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the words "{f["clue"].label}", "zoologic", and "holster".',
        f"Tell a short mystery set in the zoologic hall where {f['hero'].id} tracks a clue and learns who took the holster.",
        f"Write a simple detective story with a bad ending: the truth is found, but the holster is surrendered too late.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    clue: Clue = _safe_fact(world, f, "clue")
    suspect: Suspect = _safe_fact(world, f, "suspect")
    holster: Entity = _safe_fact(world, f, "holster")

    qa = [
        QAItem(
            question=f"What kind of story is this one?",
            answer="It is a little whodunit mystery with clues, a suspect, and a bad ending.",
        ),
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"The missing thing was {holster.label}, which {hero.id} noticed right away.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find in the zoologic hall?",
            answer=f"{hero.id} found {clue.label} near the place where the clue had been left behind.",
        ),
        QAItem(
            question=f"Who did the clue point toward?",
            answer=f"The clue pointed toward {suspect.label}, because the clue fit {suspect.motive.lower()} and the timing was suspicious.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The truth was found, but the holster was surrendered too late, so the ending stayed bad.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    keys = {"mystery", "zoologic", "holster", "surrender"}
    out: list[QAItem] = []
    for k in keys:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[k])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS.values():
        lines.append(asp.fact("setting", place.replace(" ", "_")))
        lines.append(asp.fact("affords", place.replace(" ", "_"), "mystery"))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, clue.points_to))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("item", "holster"))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
valid(P,C,S) :- setting(P), clue(C), suspect(S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - ac))
    print(" only in clingo:", sorted(ac - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "suspect", None):
        combos = [c for c in combos if c[2] == getattr(args, "suspect", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, suspect = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mina", "Ivy", "Nora", "Theo", "Finn", "Ada"])
    return StoryParams(place=place, clue=clue, suspect=suspect, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="the zoologic hall", clue="feather", suspect="keeper", name="Mina", gender="girl"),
    StoryParams(place="the zoologic hall", clue="mud", suspect="birdkeeper", name="Theo", gender="boy"),
    StoryParams(place="the zoologic hall", clue="seed", suspect="supplyrunner", name="Ivy", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
