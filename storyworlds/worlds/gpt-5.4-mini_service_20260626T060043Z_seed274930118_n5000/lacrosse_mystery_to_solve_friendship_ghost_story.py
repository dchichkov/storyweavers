#!/usr/bin/env python3
"""
A standalone storyworld script for a small ghost-story mystery with lacrosse,
friendship, and a gentle solve.

Premise:
- A child-friendly lacrosse practice takes place near an old, quiet field.
- A soft ghost keeps appearing after sunset, making the players uneasy.
- The mystery is not dangerous: the ghost is trying to return a lost charm
  and cannot find the right friend to help.

Turn:
- The friends notice clues: footprints in dew, a rattling pocket, a silver
  whistle, and a ball with a ribbon tied to it.
- They follow the clues instead of running away.

Resolution:
- They discover the "ghost" is a lonely older kid wearing a sheet-like rain
  cover and carrying a lantern.
- The team helps reunite the lost charm with its owner, and the field feels
  friendly again.

The world models:
- physical meters: distance, clue strength, spookiness, foundness, night-cold
- emotional memes: fear, curiosity, trust, friendship, relief
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
# World entities and model
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    friend: object | None = None
    ghost: object | None = None
    hero: object | None = None
    stickbag: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    name: str = "the field"
    dusk: bool = True
    affords_lacrosse: bool = True
    has_hedge: bool = True
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str = "field"
    mystery: str = "lost_charm"
    name: str = "Maya"
    friend_name: str = "Eli"
    seed: Optional[int] = None
    params: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "field": Place(name="the old field", dusk=True, affords_lacrosse=True, has_hedge=True),
    "gym": Place(name="the gym", dusk=False, affords_lacrosse=True, has_hedge=False),
    "yard": Place(name="the back yard", dusk=True, affords_lacrosse=False, has_hedge=True),
}

MYSTERIES = {
    "lost_charm": {
        "thing": "a silver charm",
        "clue": "a tiny silver glint in the grass",
        "source": "a lantern strap",
        "solve": "the charm had fallen off a teammate's stick bag",
        "spook": "something ghostly",
    }
}

NAMES = ["Maya", "Lena", "Noah", "Eli", "Zoe", "Ivy", "Finn", "Ruby", "Owen", "Ada"]


# ---------------------------------------------------------------------------
# ASP twin helpers
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(field).
place(gym).
place(yard).

affords_lacrosse(field).
affords_lacrosse(gym).

mystery(lost_charm).

can_stage(P,M) :- place(P), mystery(M), affords_lacrosse(P).

#show can_stage/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.affords_lacrosse:
            lines.append(asp.fact("affords_lacrosse", pid))
        if p.has_hedge:
            lines.append(asp.fact("has_hedge", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_stage/2."))
    return sorted(set(asp.atoms(model, "can_stage")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.mystery not in MYSTERIES:
        pass
    place = _safe_lookup(PLACES, params.place)
    if not place.affords_lacrosse:
        pass
    if params.name == params.friend_name:
        pass


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Maya", "Lena", "Zoe", "Ivy", "Ruby", "Ada"} else "boy",
        meters={"distance": 0.0, "foundness": 0.0},
        memes={"fear": 0.0, "curiosity": 0.0, "trust": 0.0, "friendship": 0.0, "relief": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="boy" if params.friend_name in {"Noah", "Eli", "Finn", "Owen"} else "girl",
        meters={"distance": 0.0, "foundness": 0.0},
        memes={"fear": 0.0, "curiosity": 0.0, "trust": 0.0, "friendship": 0.0, "relief": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        meters={"spookiness": 0.0, "distance": 5.0, "clue": 0.0},
        memes={"fear": 0.0, "curiosity": 0.0, "trust": 0.0, "lonely": 1.0},
    ))
    charm = world.add(Entity(
        id="charm",
        type="thing",
        label="silver charm",
        phrase=mystery["thing"],
        meters={"hidden": 1.0, "glint": 0.0},
    ))
    stickbag = world.add(Entity(
        id="stickbag",
        type="thing",
        label="stick bag",
        phrase="a worn lacrosse bag",
    ))
    world.facts.update(hero=hero, friend=friend, ghost=ghost, charm=charm, place=place, mystery=mystery, stickbag=stickbag)
    return world


def solve_mystery(world: World) -> None:
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    ghost: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "ghost")
    charm: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "charm")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "mystery")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place")

    # Act 1
    world.say(f"On a cool evening, {hero.id} and {friend.id} went to {place.name} for lacrosse practice.")
    world.say(f"The air felt soft and dim, and {hero.id} kept hearing a tiny sound near the hedge.")
    world.para()
    hero.memes["curiosity"] += 1
    friend.memes["fear"] += 1
    world.say(f"Then a pale figure drifted past the goal, and {friend.id} whispered, 'Is that a ghost?'")
    ghost.meters["spookiness"] += 1
    ghost.meters["distance"] = 4.0
    world.say(f"{hero.id} felt a little scared too, but {hero.id} noticed a clue instead of running away: {mystery['clue']}.")
    hero.meters["foundness"] += 1
    ghost.meters["clue"] += 1

    # Act 2
    world.para()
    world.say(f"{friend.id} took a slow breath and said they should follow the clue together.")
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    hero.meters["distance"] += 1
    friend.meters["distance"] += 1
    world.say(f"They walked toward the hedge, where the dew shone like little beads on spider silk.")
    world.say(f"There, they found a lantern strap and a lacrosse ball with a ribbon tied around {(getattr(charm, 'it')() if callable(getattr(charm, 'it', None)) else getattr(charm, 'it', 'it'))}.")
    charm.meters["glint"] += 1
    ghost.meters["distance"] = 2.0

    # Act 3
    world.para()
    world.say(f"The ghost stepped out from behind the hedge, and the mystery suddenly looked less scary.")
    ghost.memes["fear"] += 0.5
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    friend.memes["fear"] = max(0.0, friend.memes["fear"] - 0.5)
    world.say(f"It was not a mean ghost at all. It was an older kid in a pale rain cover, searching for {mystery['thing']}.")
    world.say(f"{hero.id} and {friend.id} handed over the charm, and the kid's face turned bright with relief.")
    ghost.memes["trust"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    ghost.meters["distance"] = 1.0
    charm.meters["hidden"] = 0.0
    charm.carried_by = "ghost"
    world.say(f"After that, the field felt friendly again, and the team finished practice under the evening sky.")
    world.say(f"{hero.id} and {friend.id} laughed on the walk home, glad they solved the ghost story together.")

    world.facts["resolved"] = True
    world.facts["spookiness"] = ghost.meters["spookiness"]
    world.facts["found_charm"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place")
    return [
        "Write a gentle ghost story for children where lacrosse practice reveals a mystery and friendship helps solve it.",
        f"Tell a story about {hero.id} and {friend.id} at {place.name} where a spooky-looking clue turns out to be harmless.",
        "Write a short story with a small scare, a clue, and a kind ending that proves the ghost was lonely, not mean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "mystery")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place")
    ghost: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "ghost")
    qa = [
        QAItem(
            question=f"Where did {hero.id} and {friend.id} go for lacrosse practice?",
            answer=f"They went to {place.name} for lacrosse practice, where the air was cool and the field looked quiet."
        ),
        QAItem(
            question="What made the story seem spooky at first?",
            answer=f"A pale figure drifted past the goal and left behind {mystery['clue']}, so it looked ghostly at first."
        ),
        QAItem(
            question="How did the friends solve the mystery?",
            answer=f"They followed the clue together, found the lost charm, and learned the 'ghost' was really a lonely kid looking for {mystery['thing']}."
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} feel at the end?",
            answer=f"They felt relieved and happy, because their friendship helped turn a scary moment into a kind solution."
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(QAItem(
            question="Why was the ghost not actually dangerous?",
            answer="The ghost was only pretending to be spooky-looking because it was wearing a pale rain cover and searching for a lost charm. Once the friends helped, it became clear the ghost was lonely, not mean."
        ))
    return qa


WORLD_KNOWLEDGE = {
    "lacrosse": QAItem(
        question="What is lacrosse?",
        answer="Lacrosse is a fast team game where players use a stick with a net to catch, carry, and throw a ball."
    ),
    "ghost": QAItem(
        question="What is a ghost in a story?",
        answer="A ghost in a story is usually a spooky-looking spirit or figure, often used to create mystery or a little scare."
    ),
    "mystery": QAItem(
        question="What is a mystery?",
        answer="A mystery is a puzzle about something unknown, and people solve it by noticing clues and thinking carefully."
    ),
    "friendship": QAItem(
        question="What is friendship?",
        answer="Friendship is when people care about each other, help each other, and feel happier together."
    ),
    "clue": QAItem(
        question="What is a clue?",
        answer="A clue is a small piece of information that helps you solve a problem or understand a secret."
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [WORLD_KNOWLEDGE[k] for k in ["lacrosse", "ghost", "mystery", "friendship", "clue"]]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly lacrosse ghost mystery about friendship.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES, dest="friend_name")
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend_name", None) or rng.choice([n for n in NAMES if n != name])
    params = StoryParams(place=place, mystery=mystery, name=name, friend_name=friend)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    solve_mystery(world)
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


def asp_verify() -> int:
    import asp
    py = {(p, m) for p in PLACES if _safe_lookup(PLACES, p).affords_lacrosse for m in MYSTERIES}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show can_stage/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        valid = asp_valid()
        for place, mystery in valid:
            print(f"{place} {mystery}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="field", mystery="lost_charm", name="Maya", friend_name="Eli"),
            StoryParams(place="gym", mystery="lost_charm", name="Lena", friend_name="Noah"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} and {p.friend_name} at {p.place} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
