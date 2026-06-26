#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Adventure-style quest.

Seed idea:
- A hero must obtain a decimal clue.
- A twist changes what the clue means.
- The mystery to solve is a missing map-spark hidden in a little quest.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sister", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "brother", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str
    mood: str
    clue_spot: str
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
class QuestItem:
    label: str
    phrase: str
    decimal_value: str
    used_for: str
    surprising_true_meaning: str
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
class Twist:
    label: str
    reveal: str
    effect: str
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
class Mystery:
    label: str
    question: str
    solved_by: str
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
    label: str
    goal: str
    ending_image: str
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": Setting(place="the lantern harbor", mood="salt-bright", clue_spot="the old dock post"),
    "library": Setting(place="the moonlit library", mood="quiet and gold", clue_spot="a dusty atlas shelf"),
    "forest": Setting(place="the pine path", mood="green and whispery", clue_spot="a hollow stump"),
}

HEROES = {
    "girl": ["Mina", "Luna", "Rosa", "Ivy"],
    "boy": ["Tomas", "Eli", "Finn", "Jasper"],
}

QUEST_ITEMS = {
    "decimal": QuestItem(
        label="decimal bead",
        phrase="a tiny decimal bead",
        decimal_value="3.5",
        used_for="showing the way on a treasure chart",
        surprising_true_meaning="half a step after three full steps",
    ),
    "token": QuestItem(
        label="signal token",
        phrase="a small signal token",
        decimal_value="2.4",
        used_for="opening the map box",
        surprising_true_meaning="two steps and a little more",
    ),
    "spark": QuestItem(
        label="glow spark",
        phrase="a glow spark in a glass jar",
        decimal_value="1.2",
        used_for="lighting the path clue",
        surprising_true_meaning="one bright step and a tiny tail of light",
    ),
}

TWISTS = {
    "twist": Twist(
        label="twist",
        reveal="the clue was not a number to race past, but a number to read carefully",
        effect="slowed the hero down just enough to notice the real path",
    ),
    "turn": Twist(
        label="turn",
        reveal="the smallest part of the clue mattered most",
        effect="changed the answer from a guess into a sure step",
    ),
}

MYSTERIES = {
    "mystery": Mystery(
        label="mystery to solve",
        question="where the hidden key had gone",
        solved_by="following the decimal clue exactly",
    ),
    "riddle": Mystery(
        label="mystery to solve",
        question="which door matched the chart",
        solved_by="reading the decimal bead as a careful hint",
    ),
}

QUESTS = {
    "quest": Quest(
        label="quest",
        goal="find the missing map-key and reach the lantern gate",
        ending_image="the lantern gate glowing open beside a smiling hero",
    ),
    "journey": Quest(
        label="quest",
        goal="carry the clue home and solve the path before dusk",
        ending_image="a safe path shining under the last blue light",
    ),
}


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts define a quest with one hero, one item, one twist, one mystery.
quest_ready(H, I, T, M) :- hero(H), item(I), twist(T), mystery(M).
solved(H, I, T, M) :- quest_ready(H, I, T, M), decimal(I), twisty(T), mystery_kind(M).

#show solved/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
    for g in HEROES:
        lines.append(asp.fact("gender", g))
    for iid in QUEST_ITEMS:
        lines.append(asp.fact("item", iid))
    lines.append(asp.fact("decimal", "decimal"))
    lines.append(asp.fact("twisty", "twist"))
    lines.append(asp.fact("mystery_kind", "mystery"))
    lines.append(asp.fact("quest_kind", "quest"))
    lines.append(asp.fact("hero", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/4."))
    atoms = asp.atoms(model, "solved")
    if atoms == [("hero", "decimal", "twist", "mystery")]:
        print("OK: ASP twin recognizes the quest.")
        return 0
    print("MISMATCH: ASP twin did not recognize the quest.")
    print(atoms)
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero_name: str
    gender: str
    item: str
    twist: str
    mystery: str
    quest: str
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


CURATED = [
    StoryParams(setting="harbor", hero_name="Mina", gender="girl", item="decimal", twist="twist", mystery="mystery", quest="quest"),
    StoryParams(setting="library", hero_name="Eli", gender="boy", item="token", twist="turn", mystery="riddle", quest="journey"),
    StoryParams(setting="forest", hero_name="Luna", gender="girl", item="spark", twist="twist", mystery="mystery", quest="quest"),
]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

class StoryState:
    def __init__(self, world: World, hero: Entity, item: Entity, twist: Twist, mystery: Mystery, quest: Quest) -> None:
        self.world = world
        self.hero = hero
        self.item = item
        self.twist = twist
        self.mystery = mystery
        self.quest = quest


def _introduce(state: StoryState) -> None:
    w, h, item = state.world, state.hero, state.item
    w.say(
        f"{h.id} was a brave little {h.type} who loved maps, shiny clues, and big adventures."
    )
    w.say(
        f"One day, {h.id} heard about {state.quest.goal}, so {h.pronoun()} set off into {w.setting.place}."
    )
    w.say(
        f"The air felt {w.setting.mood}, and {h.id} hoped to find {item.phrase} near {w.setting.clue_spot}."
    )


def _seek_clue(state: StoryState) -> None:
    w, h, item = state.world, state.hero, state.item
    h.memes["curiosity"] = h.memes.get("curiosity", 0.0) + 1
    item.carried_by = h.id
    w.say(
        f"After a while, {h.id} found {item.phrase} tucked in a small crack."
    )
    w.say(
        f"On it was the number {item.decimal_value}, and that looked important for the {state.mystery.label}."
    )


def _twist(state: StoryState) -> None:
    w, h, item = state.world, state.hero, state.item
    h.memes["puzzled"] = h.memes.get("puzzled", 0.0) + 1
    h.memes["hope"] = h.memes.get("hope", 0.0) + 1
    w.say(
        f"At first, {h.id} thought the clue meant to hurry past it, but then the {state.twist.label} arrived."
    )
    w.say(
        f"{state.twist.reveal.capitalize()}, and that {state.twist.effect}."
    )
    w.say(
        f"{h.id} held the decimal bead close and whispered, '{item.decimal_value} means {item.surprising_true_meaning}.'"
    )


def _solve(state: StoryState) -> None:
    w, h, item = state.world, state.hero, state.item
    h.memes["joy"] = h.memes.get("joy", 0.0) + 1
    w.say(
        f"That careful thought solved the {state.mystery.label}: the hidden key had been waiting exactly where the clue pointed."
    )
    w.say(
        f"{h.id} used the bead to open the little map box, and inside was the key for the lantern gate."
    )
    w.say(
        f"By the end of the {state.quest.label}, {h.id} reached the gate with the clue safe in {h.pronoun('possessive')} hand."
    )


def _ending(state: StoryState) -> None:
    w, h = state.world, state.hero
    w.para()
    h.memes["pride"] = h.memes.get("pride", 0.0) + 1
    w.say(
        f"{state.quest.ending_image.capitalize()}. {h.id} smiled because the smallest decimal had led to the biggest win."
    )


def tell(setting: Setting, hero_name: str, gender: str, item: QuestItem, twist: Twist, mystery: Mystery, quest: Quest) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    clue = w.add(Entity(id=item.label, type="thing", label=item.label, phrase=item.phrase))
    w.facts.update(hero=hero, item=clue, twist=twist, mystery=mystery, quest=quest, setting=setting)
    state = StoryState(w, hero, clue, twist, mystery, quest)
    _introduce(state)
    w.para()
    _seek_clue(state)
    _twist(state)
    w.para()
    _solve(state)
    _ending(state)
    return w


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, f, "item")  # type: ignore[assignment]
    twist: Twist = _safe_fact(world, f, "twist")  # type: ignore[assignment]
    mystery: Mystery = _safe_fact(world, f, "mystery")  # type: ignore[assignment]
    quest: Quest = _safe_fact(world, f, "quest")  # type: ignore[assignment]
    return [
        f'Write an adventure story for a young child where {hero.id} must obtain a decimal clue and solve a mystery.',
        f"Tell a story with a twist, a mystery to solve, and a quest that includes {item.label} and a careful clue.",
        f"Write a gentle adventure where a small decimal number helps {hero.id} finish a {quest.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, f, "item")  # type: ignore[assignment]
    twist: Twist = _safe_fact(world, f, "twist")  # type: ignore[assignment]
    mystery: Mystery = _safe_fact(world, f, "mystery")  # type: ignore[assignment]
    quest: Quest = _safe_fact(world, f, "quest")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} need to obtain in {setting.place}?",
            answer=f"{hero.id} needed to obtain {item.phrase}, a tiny clue with the decimal number {item.decimal_value}.",
        ),
        QAItem(
            question=f"What was the story's twist?",
            answer=f"The twist was that the decimal clue had to be read carefully; it was not a number to ignore but a hint to solve the mystery.",
        ),
        QAItem(
            question=f"What mystery did {hero.id} solve?",
            answer=f"{hero.id} solved the {mystery.label} of {mystery.question} by following the decimal clue exactly.",
        ),
        QAItem(
            question=f"What did the quest lead to at the end?",
            answer=f"The {quest.label} led to {quest.ending_image}, after {hero.id} used the clue to reach the final gate.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a decimal?",
            answer="A decimal is a way to write a number that can show parts of a whole, like 3.5 or 2.4.",
        ),
        QAItem(
            question="What does it mean to obtain something?",
            answer="To obtain something means to get it or find it and keep it with you.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something unknown that you want to figure out.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to find something, solve something, or reach a goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Resolution / generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style storyworld about obtaining a decimal clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--item", choices=QUEST_ITEMS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--quest", choices=QUESTS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    item = getattr(args, "item", None) or "decimal"
    twist = getattr(args, "twist", None) or "twist"
    mystery = getattr(args, "mystery", None) or "mystery"
    quest = getattr(args, "quest", None) or "quest"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(_safe_lookup(HEROES, gender))
    if item == "decimal" and twist != "twist":
        # still valid, but make the seed words common in the main path
        pass
    return StoryParams(setting=setting, hero_name=hero_name, gender=gender, item=item, twist=twist, mystery=mystery, quest=quest)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        params.hero_name,
        params.gender,
        _safe_lookup(QUEST_ITEMS, params.item),
        _safe_lookup(TWISTS, params.twist),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(QUESTS, params.quest),
    )
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
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


def asp_facts_and_rules(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_facts_and_rules("#show solved/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_facts_and_rules("#show solved/4."))
        print(asp.atoms(model, "solved"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
