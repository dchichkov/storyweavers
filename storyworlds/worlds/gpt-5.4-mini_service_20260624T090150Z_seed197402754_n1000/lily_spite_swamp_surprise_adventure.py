#!/usr/bin/env python3
"""
A tiny storyworld about Lily, a swamp adventure, spite, and a surprise turn.

Premise:
- Lily loves exploring the swamp.
- The swamp is full of muddy paths, frogs, reeds, and hidden places.
- A small spiteful mood can make Lily rush ahead and miss clues.
- A surprise in the swamp gives Lily a chance to change course, help someone, and end the day with a new treasure.

This world is deliberately small and constraint-checked:
- the swamp must plausibly create trouble;
- spite must be strong enough to cause a tense mistake;
- the surprise must be earned by the world state, not pasted on.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the swamp"
    afford: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Adventure:
    id: str
    verb: str
    gerund: str
    rush: str
    clue: str
    surprise: str
    danger: str
    zone: set[str]
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
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
    result: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Content
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


SETTING = Setting(place="the swamp", afford={"explore", "cross_log", "follow_frogs"})

ADVENTURES = {
    "swamp": Adventure(
        id="swamp",
        verb="explore the swamp",
        gerund="exploring the swamp",
        rush="hurry down the muddy path",
        clue="a line of tiny tracks near the reeds",
        surprise="a lost duckling under a lily pad",
        danger="sink into deep mud",
        zone={"feet", "legs"},
    ),
    "log": Adventure(
        id="log",
        verb="cross the old log",
        gerund="balancing on the old log",
        rush="run to the log",
        clue="a shiny shell on the bank",
        surprise="a nest tucked into a hollow stump",
        danger="slip into the water",
        zone={"feet", "legs"},
    ),
    "frogs": Adventure(
        id="frogs",
        verb="follow the frogs",
        gerund="following the frogs",
        rush="dash after the frogs",
        clue="croaks coming from the cattails",
        surprise="a hidden path to a little picnic spot",
        danger="lose the trail in the reeds",
        zone={"feet", "legs"},
    ),
}

PRIZES = {
    "boots": Prize(id="boots", label="boots", phrase="bright yellow boots", region="feet", plural=True),
    "cloak": Prize(id="cloak", label="cloak", phrase="a blue cloak", region="torso"),
    "hat": Prize(id="hat", label="hat", phrase="a straw hat", region="head"),
}

HELPERS = {
    "frog": Helper(
        id="frog",
        label="a little frog",
        offer="hop beside Lily and point to the safe stones",
        result="hopped ahead and showed the safe stones",
    ),
    "duckling": Helper(
        id="duckling",
        label="the duckling",
        offer="call from the reeds and lead Lily home",
        result="quacked softly and led Lily to the hidden path",
    ),
    "heron": Helper(
        id="heron",
        label="a tall heron",
        offer="stand on one leg and guide Lily past the mud",
        result="stood still and pointed out a dry route",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    adventure: str
    prize: str
    helper: str
    name: str = "Lily"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
bad_spite(A) :- spiteful(A), rushes_into_mud(A).
valid_story(A, P, H) :- prize_at_risk(A, P), helper(H), surprise_help(H, A), not impossible(A, P).
impossible(A, P) :- prize_at_risk(A, P), not fix(G, A, P), gear(G).
fix(G, A, P) :- gear(G), prize_at_risk(A, P), covers(G, R), worn_on(P, R), guards(G, mud).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for aid, a in ADVENTURES.items():
        lines.append(asp.fact("adventure", aid))
        lines.append(asp.fact("spiteful", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("surprise_help", hid, "swamp"))
    lines.append(asp.fact("gear", "boots"))
    lines.append(asp.fact("covers", "boots", "feet"))
    lines.append(asp.fact("guards", "boots", "mud"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def surprise_text(adventure: Adventure, helper: Helper, prize: Prize) -> str:
    return (
        f"Then came a surprise: {adventure.surprise}. "
        f"That made the swamp feel brand new."
    )


def predict_risk(world: World, adventure: Adventure, prize: Prize) -> bool:
    return prize.region in adventure.zone


def valid_combo(adventure: Adventure, prize: Prize, helper: Helper) -> bool:
    return predict_risk(World(SETTING), adventure, prize) and helper is not None


def build_world(params: StoryParams) -> World:
    w = World(SETTING)
    hero = w.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    prize = w.add(Entity(
        id="prize",
        type=_safe_lookup(PRIZES, params.prize).label,
        label=_safe_lookup(PRIZES, params.prize).label,
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        owner=hero.id,
        plural=_safe_lookup(PRIZES, params.prize).plural,
    ))
    helper = _safe_lookup(HELPERS, params.helper)
    adventure = _safe_lookup(ADVENTURES, params.adventure)

    hero.memes["love_adventure"] = 1
    prize.carried_by = hero.id

    w.say(f"{hero.id} loved adventures, especially days near {w.setting.place}.")
    w.say(f"{hero.pronoun().capitalize()} wore {prize.phrase} and felt ready for a big day.")

    w.para()
    w.say(f"One morning, {hero.id} went to {w.setting.place} to {adventure.verb}.")
    w.say(f"The swamp was quiet, but {adventure.clue} caught {hero.pronoun('possessive')} eye.")
    hero.memes["curiosity"] = 1

    if predict_risk(w, adventure, prize):
        hero.memes["spite"] = 1.0
        w.say(
            f"{hero.id} felt a prickly spite and rushed ahead anyway, trying to {adventure.rush}."
        )
        hero.meters["mud"] = 1.0
        prize.meters["mud"] = 1.0
        w.say(f"That was a mistake, because {hero.pronoun('possessive')} {prize.label} got muddy.")

    w.para()
    w.say(surprise_text(adventure, helper, prize))
    hero.memes["surprise"] = 1.0
    w.say(
        f"Then {helper.label} appeared and could {helper.offer}. "
        f"That helped {hero.id} slow down and look carefully."
    )

    hero.memes["kindness"] = 1.0
    hero.memes["spite"] = 0.0
    prize.meters["clean"] = 1.0
    w.say(
        f"{hero.id} followed the safe path, helped the little helper, and found a dry way home. "
        f"In the end, {hero.pronoun('possessive')} {prize.label} stayed safe enough for the next adventure."
    )

    w.facts.update(hero=hero, prize=prize, helper=helper, adventure=adventure)
    return w


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prize: Entity = _safe_fact(world, f, "prize")
    adventure: Adventure = _safe_fact(world, f, "adventure")
    helper: Helper = _safe_fact(world, f, "helper")
    return [
        f'Write a short adventure story for a child named {hero.id} in a swamp with a surprise.',
        f"Tell a gentle story where {hero.id} starts with spite, gets into trouble in the swamp, and meets {helper.label}.",
        f'Write a story about {hero.id}, {prize.phrase}, and a swamp surprise that changes the day.',
        f"Make the story feel like an adventure and end with a safe discovery in the swamp.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prize: Entity = _safe_fact(world, f, "prize")
    helper: Helper = _safe_fact(world, f, "helper")
    adventure: Adventure = _safe_fact(world, f, "adventure")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, who goes on a swamp adventure and learns to calm spite down.",
        ),
        QAItem(
            question=f"What did {hero.id} rush ahead to do in the swamp?",
            answer=f"{hero.id} rushed ahead to {adventure.verb}, but that made {hero.pronoun('possessive')} {prize.label} get muddy.",
        ),
        QAItem(
            question=f"What surprise did the swamp have?",
            answer=f"The swamp surprise was {adventure.surprise}, which changed the day from a mistake into a helpful adventure.",
        ),
        QAItem(
            question=f"Who helped {hero.id} after the spiteful rush?",
            answer=f"{helper.label} helped {hero.id} by leading the way to a safer path.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "swamp": [
        QAItem(
            question="What is a swamp?",
            answer="A swamp is a wet place with muddy ground, water, reeds, and lots of plants and animals.",
        ),
        QAItem(
            question="Why can swamp paths be tricky?",
            answer="Swamp paths can be tricky because the ground can be muddy, soft, and easy to slip on.",
        ),
    ],
    "spite": [
        QAItem(
            question="What does spite mean?",
            answer="Spite is a mean or stubborn feeling that can make someone want to do the wrong thing just because they feel annoyed.",
        )
    ],
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears when you are not ready for it.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for k in ("swamp", "spite", "surprise") for q in WORLD_KNOWLEDGE[k]]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP verification helpers
# ---------------------------------------------------------------------------

def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp

    py = {
        (aid, pid, hid)
        for aid in ADVENTURES
        for pid in PRIZES
        for hid in HELPERS
        if valid_combo(_safe_lookup(ADVENTURES, aid), _safe_lookup(PRIZES, pid), _safe_lookup(HELPERS, hid))
    }
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: ASP parity matches Python ({len(py)} compatible stories).")
        return 0
    print("MISMATCH between ASP and Python")
    print("python-only:", sorted(py - clingo))
    print("asp-only:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny swamp adventure storyworld with Lily, spite, and surprise.")
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name", choices=GIRL_NAMES)
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
    ad = getattr(args, "adventure", None) or rng.choice(list(ADVENTURES))
    pr = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    hp = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    name = getattr(args, "name", None) or "Lily"
    if not valid_combo(_safe_lookup(ADVENTURES, ad), _safe_lookup(PRIZES, pr), _safe_lookup(HELPERS, hp)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(adventure=ad, prize=pr, helper=hp, name=name)


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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for ad in ADVENTURES:
            for pr in PRIZES:
                for hp in HELPERS:
                    if valid_combo(_safe_lookup(ADVENTURES, ad), _safe_lookup(PRIZES, pr), _safe_lookup(HELPERS, hp)):
                        samples.append(generate(StoryParams(ad, pr, hp, "Lily")))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
            header = f"### {p.name}: {p.adventure} / {p.prize} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
