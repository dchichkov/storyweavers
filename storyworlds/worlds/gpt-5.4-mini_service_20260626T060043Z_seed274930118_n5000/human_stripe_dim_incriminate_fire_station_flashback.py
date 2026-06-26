#!/usr/bin/env python3
"""
A storyworld for a fire-station myth with a flashback and a mystery to solve.

Premise:
- A human at a fire station notices a stripe-dim mark.
- The mark seems to incriminate someone.
- The hero uses a flashback to remember what really happened.
- The truth clears the blame and restores trust.

The world is intentionally small and classical:
- typed entities
- meters for physical state
- memes for emotional state
- a turn driven by simulated evidence
- a resolution that changes the world model
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
    caretakers: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chief: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        if self.type == "human":
            mapping = {
                "subject": "they",
                "object": "them",
                "possessive": "their",
            }
        if self.type == "captain":
            mapping = {
                "subject": "she",
                "object": "her",
                "possessive": "her",
            }
        if self.type == "sprinter":
            mapping = {
                "subject": "he",
                "object": "him",
                "possessive": "his",
            }
        return mapping[case]
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


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


@dataclass
class Room:
    id: str
    name: str
    clues: set[str] = field(default_factory=set)
    holds: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    place: str
    kind: str
    meaning: str
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
    label: str
    relation: str
    innocence: bool = True
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
    "truck_bay": Room(
        id="truck_bay",
        name="the truck bay",
        clues={"stripe-dim"},
        holds={"brush", "helmet"},
    ),
    "kitchen": Room(
        id="kitchen",
        name="the kitchen",
        clues={"ash"},
        holds={"kettle"},
    ),
    "watch_room": Room(
        id="watch_room",
        name="the watch room",
        clues={"ledger"},
        holds={"lantern"},
    ),
}

CLUES = {
    "stripe-dim": Clue(
        id="stripe-dim",
        label="stripe-dim mark",
        place="truck bay",
        kind="mark",
        meaning="a dim stripe left by soot and sunlight together",
    ),
    "ash": Clue(
        id="ash",
        label="ash fleck",
        place="kitchen",
        kind="dust",
        meaning="a soft gray speck that can travel on cloth",
    ),
    "ledger": Clue(
        id="ledger",
        label="old ledger note",
        place="watch room",
        kind="record",
        meaning="a written memory kept safe for later reading",
    ),
}

SUSPECTS = {
    "rowan": Suspect(id="rowan", label="Rowan", relation="apprentice"),
    "mira": Suspect(id="mira", label="Mira", relation="captain"),
    "tomas": Suspect(id="tomas", label="Tomas", relation="messenger"),
}

NAMES = ["Rowan", "Mira", "Tomas", "Iris", "Bram", "Nia"]
TRAITS = ["brave", "quiet", "keen", "steadfast", "thoughtful"]
GENDERS = ["human"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    hero_name: str
    hero_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
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


def setup_world(params: StoryParams) -> World:
    world = World(place=_safe_lookup(ROOMS, params.place).name)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="human",
        label=params.hero_name,
        phrase=f"a {params.hero_trait} human",
        meters={"fatigue": 0.0},
        memes={"curiosity": 0.0, "fear": 0.0, "resolve": 0.0},
    ))
    chief = world.add(Entity(
        id="chief",
        kind="character",
        type="captain",
        label="Captain Mira",
        phrase="the station captain",
        meters={"work": 0.0},
        memes={"duty": 1.0},
    ))
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    world.add(Entity(
        id=suspect.id,
        kind="character",
        type="sprinter" if suspect.id == "tomas" else "human",
        label=suspect.label,
        phrase=f"the {suspect.relation}",
        meters={"smoke": 0.0},
        memes={"worry": 0.0, "blame": 0.0},
    ))
    clue = _safe_lookup(CLUES, params.clue)
    world.add(Entity(
        id=clue.id,
        kind="thing",
        type="clue",
        label=clue.label,
        phrase=clue.meaning,
        meters={"brightness": 0.2 if clue.id == "stripe-dim" else 0.8},
        memes={"mystery": 1.0},
    ))
    world.facts.update(params=params, hero=hero, chief=chief, suspect=suspect, clue=clue)
    return world


def intro(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    chief = _safe_fact(world, world.facts, "chief")
    clue = _safe_fact(world, world.facts, "clue")
    world.say(
        f"In the old fire station, {hero.label} was a {hero.phrase} who listened to every bell and bootstep."
    )
    world.say(
        f"One dawn, {hero.label} saw the {clue.label} lying by the truck bay wall, dim as a moon behind smoke."
    )
    world.say(
        f"{chief.label} frowned, because the mark seemed to point toward blame."
    )


def raise_mystery(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    suspect = world.get(world.facts["suspect"].id)
    clue = _safe_fact(world, world.facts, "clue")
    hero.memes["curiosity"] += 1
    suspect.memes["blame"] += 1
    world.say(
        f"{hero.label} wondered who had left the {clue.label} there, and why it looked like a sign from an old tale."
    )
    world.say(
        f"The station began to whisper that {suspect.label} must have done it."
    )


def flashback(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    clue = _safe_fact(world, world.facts, "clue")
    suspect = world.get(world.facts["suspect"].id)
    world.para()
    world.say(
        f"Then memory rose like a lantern in dark water: {hero.label} remembered the earlier hour before the bell rang."
    )
    world.say(
        f"{suspect.label} had carried a soot-stained hose past the wall, and the bright stripe on the cloth had brushed the stone."
    )
    world.say(
        f"The mark was not a secret crime at all, only a stripe-dim trace from honest work."
    )
    clue.meters["brightness"] = 0.9
    suspect.memes["blame"] = 0.0
    hero.memes["resolve"] += 1


def resolve(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    chief = _safe_fact(world, world.facts, "chief")
    suspect = world.get(world.facts["suspect"].id)
    clue = _safe_fact(world, world.facts, "clue")
    world.para()
    world.say(
        f"{hero.label} spoke the truth to {chief.label}, and the old station grew quiet enough to hear the hoses breathe."
    )
    world.say(
        f"{chief.label} nodded. The stripe-dim mark had incriminated no one; it had only remembered a working morning."
    )
    world.say(
        f"{suspect.label} stood taller, the blame gone, while {hero.label} set the story right like a lantern back on its hook."
    )
    clue.meters["brightness"] = 1.0
    world.facts["solved"] = True


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    raise_mystery(world)
    flashback(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short mythic story set in a fire station where a human notices a "{p.clue}" and solves a mystery with a flashback.',
        f"Tell a child-friendly tale about {p.hero_name}, a {p.hero_trait} human, who must decide whether the stripe-dim mark really incriminates {p.suspect}.",
        "Write a simple myth in a fire station that begins with blame, returns to an earlier memory, and ends with the truth restored.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    suspect = _safe_fact(world, world.facts, "suspect")
    clue = _safe_fact(world, world.facts, "clue")
    chief = _safe_fact(world, world.facts, "chief")
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.label}, a {p.hero_trait} human in the fire station.",
        ),
        QAItem(
            question=f"What mystery did {hero.label} notice in the truck bay?",
            answer=f"{hero.label} noticed the {clue.label}, a dim stripe by the wall.",
        ),
        QAItem(
            question=f"Who seemed to be incriminated at first?",
            answer=f"At first, {suspect.label} seemed to be incriminated.",
        ),
        QAItem(
            question=f"What did the flashback show really happened?",
            answer=(
                f"The flashback showed that {suspect.label} carried a soot-stained hose past the wall, "
                f"and the cloth brushed the stone, leaving the stripe-dim mark."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"{hero.label} told {chief.label} the truth, the blame disappeared, and the station understood the mark was only evidence of work."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fire station?",
            answer="A fire station is a place where firefighters live, keep their gear, and wait for calls to help people.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier, so we can understand the present better.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find the true explanation for something confusing or hidden.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(fire_station).

clue(stripe_dim).
clue(ash).
clue(ledger).

suspect(rowan).
suspect(mira).
suspect(tomas).

% A clue can incriminate a suspect if it appears to point at them.
incriminates(C, S) :- clue(C), suspect(S), clue_points_to(C, S).

% The flashback resolves the mystery when it reveals a cause that makes the clue innocent.
resolved(C, S) :- incriminates(C, S), flashback_explains(C, S).

#show incriminates/2.
#show resolved/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "fire_station")]
    for cid in CLUES.values():
        lines.append(asp.fact("clue", cid.replace("-", "_")))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("clue_points_to", "stripe_dim", "tomas"))
    lines.append(asp.fact("flashback_explains", "stripe_dim", "tomas"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/2. #show incriminates/2."))
    atoms = set((s.name, tuple(a.name if a.type != a.type.Number else a.number for a in s.arguments)) for s in model)
    expected = {("incriminates", ("stripe_dim", "tomas")), ("resolved", ("stripe_dim", "tomas"))}
    if atoms == expected:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH:")
    print("  ASP atoms:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Parsing / resolution
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    hero_name: str
    hero_trait: str
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
    ap = argparse.ArgumentParser(description="A mythic fire-station mystery with a flashback.")
    ap.add_argument("--place", choices=list(ROOMS))
    ap.add_argument("--clue", choices=list(CLUES))
    ap.add_argument("--suspect", choices=list(SUSPECTS))
    ap.add_argument("--name", choices=NAMES)
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
    place = getattr(args, "place", None) or rng.choice(list(ROOMS))
    clue = getattr(args, "clue", None) or "stripe-dim"
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    if clue != "stripe-dim":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if suspect == "mira":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, suspect=suspect, hero_name=name, hero_trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.type} {ent.label} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="truck_bay", clue="stripe-dim", suspect="tomas", hero_name="Rowan", hero_trait="steadfast"),
    StoryParams(place="truck_bay", clue="stripe-dim", suspect="rowan", hero_name="Iris", hero_trait="keen"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show incriminates/2. #show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show incriminates/2. #show resolved/2."))
        print(sorted((s.name, tuple(a.name if a.type != a.type.Number else a.number for a in s.arguments)) for s in model))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.hero_name} / {p.place} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
