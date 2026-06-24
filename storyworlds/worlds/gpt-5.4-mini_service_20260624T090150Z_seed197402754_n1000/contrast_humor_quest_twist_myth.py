#!/usr/bin/env python3
"""
A small myth-style story world with contrast, humor, quest, and twist.

A child hears an epic-sounding quest, but the treasure turns out to be tiny
and funny in a way that still feels magical. The world model tracks physical
objects, locations, and emotional beats so the prose can change with state.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
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
    id: str
    label: str
    kind: str
    lends: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    title: str
    ask: str
    object_label: str
    object_phrase: str
    object_kind: str
    object_region: str
    place: str
    absurd_detail: str
    truth: str
    reward: str
    tags: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    kind: str
    region: str
    precious: bool = True
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


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


PLACES = {
    "hill": Place(id="hill", label="the moonlit hill", kind="hill", lends={"quest", "echo", "wind"}),
    "grove": Place(id="grove", label="the whispering grove", kind="grove", lends={"quest", "birdsong", "moss"}),
    "bridge": Place(id="bridge", label="the old stone bridge", kind="bridge", lends={"quest", "river", "stone"}),
}

HEROES = {
    "child": ("girl", ["small", "bright-eyed"]),
    "boy": ("boy", ["small", "brave"]),
}

QUESTS = {
    "bell": Quest(
        id="bell",
        title="the quest for the missing bell",
        ask="recover the sacred bell",
        object_label="bell",
        object_phrase="a tiny silver bell that rang like a laugh",
        object_kind="bell",
        object_region="hand",
        place="hill",
        absurd_detail="it was tied to the back of a very sleepy goat",
        truth="the bell was not stolen by a dragon at all",
        reward="the hill would ring again",
        tags={"contrast", "humor", "quest", "twist", "myth"},
    ),
    "crown": Quest(
        id="crown",
        title="the quest for the missing crown",
        ask="return the royal crown",
        object_label="crown",
        object_phrase="a small gold crown with one bent star",
        object_kind="crown",
        object_region="head",
        place="grove",
        absurd_detail="it was being used as a shiny bowl for berries",
        truth="the crown had not vanished into the sky",
        reward="the queen could smile again",
        tags={"contrast", "humor", "quest", "twist", "myth"},
    ),
    "key": Quest(
        id="key",
        title="the quest for the hidden key",
        ask="find the temple key",
        object_label="key",
        object_phrase="a bronze key warm from the sun",
        object_kind="key",
        object_region="hand",
        place="bridge",
        absurd_detail="it was hanging from a fishhook in a carp's mouth",
        truth="the key was waiting in an unexpected place",
        reward="the door to the old shrine would open",
        tags={"contrast", "humor", "quest", "twist", "myth"},
    ),
}

RELICS = {
    "bell": Relic(id="bell", label="bell", phrase="a tiny silver bell", kind="bell", region="hand"),
    "crown": Relic(id="crown", label="crown", phrase="a small gold crown", kind="crown", region="head"),
    "key": Relic(id="key", label="key", phrase="a bronze key", kind="key", region="hand"),
}

NAMES = ["Mira", "Oren", "Lio", "Nia", "Tavi", "Sera", "Bren", "Ari"]
EPITHETS = ["the careful", "the curious", "the earnest", "the tiny", "the quick", "the bright"]

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_kind: str
    epithet: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, q) for p in PLACES for q in QUESTS if q in _safe_lookup(PLACES, p).lends]


def quest_is_reasonable(place: Place, quest: Quest) -> bool:
    return quest.id in place.lends


def explain_rejection(place: Place, quest: Quest) -> str:
    return (
        f"(No story: {quest.title} does not belong at {place.label}. "
        f"The place cannot support that sort of quest, so the mythic twist would feel false.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_def(Q).
reasonable(P,Q) :- lends(P,Q).
valid(P,Q) :- place(P), quest(Q), reasonable(P,Q).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(p.lends):
            lines.append(asp.fact("lends", pid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest_def", qid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    world = World(place)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_kind))
    guide = world.add(Entity(id="Guide", kind="character", type="woman", label="the old guide"))
    relic = world.add(Entity(
        id=quest.object_kind,
        kind="relic",
        type=quest.object_kind,
        label=quest.object_label,
        phrase=quest.object_phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, guide=guide, quest=quest, relic=relic, place=place)

    # Act I: contrast between tiny hero and grand quest
    world.say(f"On a night when the stars looked like spilled salt, {hero.id} stood at {place.label}.")
    world.say(f"{hero.id} was {params.epithet}, yet {hero.pronoun('subject')} had been chosen for {quest.title}.")
    world.say(f"The old guide bowed and said, \"Only {hero.id} can {quest.ask}.\"")
    world.say(f"It sounded grand, but the task came with a strange joke of fate: {quest.absurd_detail}.")

    # Act II: the quest and the false expectation
    world.para()
    world.say(f"{hero.id} followed the path through {place.label}, listening for thunder and riddles.")
    world.say(f"Instead, {hero.id} found clues that made the quest feel both serious and silly.")
    world.say(f"Every sign pointed away from dragons and toward a very ordinary problem.")

    # Twist: reveal the mundane but magical truth
    world.para()
    if quest.id == "bell":
        world.say("At the ridge, a sleepy goat wore the bell on a fraying ribbon and chewed grass like a king.")
        world.say(f"{hero.id} laughed so hard that {hero.pronoun('possessive')} knees shook.")
        world.say(f"Then {hero.id} gently untied the ribbon and held up {relic.phrase}.")
    elif quest.id == "crown":
        world.say("In the grove, the crown sat in a berry bush, sparkling like a toy sun.")
        world.say(f"{hero.id} smiled at the sight, because the royal treasure looked oddly like a snack bowl.")
        world.say(f"Then {hero.id} lifted {relic.phrase} from the leaves.")
    else:
        world.say("Under the bridge, a fish flashed silver and nearly winked.")
        world.say(f"{hero.id} found the bronze key where nobody expected it: hanging from a fishhook.")
        world.say(f"With a careful tug, {hero.id} freed {relic.phrase} from the water's joke.")

    # Resolution
    world.para()
    world.say(f"{hero.id} carried the treasure back to the guide, and the whole place seemed to breathe easier.")
    world.say(f"The guide laughed kindly and said, \"A true quest often hides in a plain corner.\"")
    world.say(f"In the end, {quest.reward}, and {hero.id} walked home smaller in size but larger in heart.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    q: Quest = _safe_fact(world, world.facts, "quest")
    h: Entity = _safe_fact(world, world.facts, "hero")
    return [
        f'Write a short myth for children about a tiny hero on {q.title}.',
        f"Tell a humorous quest story where {h.id} seems small for the task, but the ending is surprising.",
        f'Write a gentle mythic tale that includes the word "contrast" and ends with a twist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    q: Quest = _safe_fact(world, world.facts, "quest")
    h: Entity = _safe_fact(world, world.facts, "hero")
    place: Place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"Who goes on the quest at {place.label}?",
            answer=f"{h.id} goes on the quest there. {h.pronoun('subject').capitalize()} is small, but the story treats {h.pronoun('object')} like a hero.",
        ),
        QAItem(
            question=f"What made the quest feel funny as well as serious?",
            answer=f"It sounded grand, but {q.absurd_detail}. That contrast made the story funny without making the quest feel unimportant.",
        ),
        QAItem(
            question=f"What did {h.id} bring back in the end?",
            answer=f"{h.id} brought back {q.object_phrase}. It turned out to be the treasure everyone wanted, even though it was hidden in an unexpected place.",
        ),
        QAItem(
            question=f"How did the story end for {h.id}?",
            answer=f"{h.id} returned home after the quest, and {q.reward}. The ending shows that a small hero can finish a big story well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    q: Quest = _safe_fact(world, world.facts, "quest")
    if q.id == "bell":
        return [QAItem(
            question="What is a bell?",
            answer="A bell is a small object that rings when it is shaken or struck.",
        )]
    if q.id == "crown":
        return [QAItem(
            question="What is a crown?",
            answer="A crown is a special head украшение worn by a king or queen as a sign of rule.",
        )]
    return [QAItem(
        question="What is a key for?",
        answer="A key is used to open a lock or a door that needs the right shape to turn it.",
    )]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic quest story world with contrast, humor, and twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=["girl", "boy"], dest="hero_kind")
    ap.add_argument("--epithet")
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
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest = rng.choice(list(combos))
    hero_kind = getattr(args, "hero_kind", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    epithet = getattr(args, "epithet", None) or rng.choice(EPITHETS)
    return StoryParams(place=place, quest=quest, hero_name=name, hero_kind=hero_kind, epithet=epithet)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    StoryParams(place="hill", quest="bell", hero_name="Mira", hero_kind="girl", epithet="tiny"),
    StoryParams(place="grove", quest="crown", hero_name="Oren", hero_kind="boy", epithet="curious"),
    StoryParams(place="bridge", quest="key", hero_name="Nia", hero_kind="girl", epithet="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:")
        for p, q in vals:
            print(f"  {p:6} {q}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
