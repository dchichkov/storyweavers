#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero-style children's museum tale.

Premise:
- A young hero hurries through a children's museum.
- A rhyme causes a misunderstanding about what is safe.
- The misunderstanding leads to a bad ending that still feels complete.

The simulation keeps typed entities with physical meters and emotional memes,
and the prose is driven by the changing world state.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    region: object | None = None
    hero: object | None = None
    prize: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "heroine"}
        male = {"boy", "father", "man", "hero"}
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
    indoor: bool = True
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
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
    label: str
    phrase: str
    type: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "children_museum": Place(
        name="the children's museum",
        indoor=True,
        affords={"rhyme", "hurry", "mixup"},
    )
}

ACTIONS = {
    "hurry": Action(
        id="hurry",
        verb="hurry to the next exhibit",
        gerund="hurrying from room to room",
        rush="dash to the giant moon wheel",
        mess="bump",
        soil="jostled and upset",
        zone={"hands", "feet"},
        keyword="hurry",
    ),
    "rhyme": Action(
        id="rhyme",
        verb="sing a rhyme",
        gerund="rhyming loudly",
        rush="hurry along to the rhyme door",
        mess="confuse",
        soil="mixed up",
        zone={"head"},
        keyword="rhyme",
    ),
}

PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a shiny red cape",
        type="cape",
        region="back",
    ),
    "badge": Prize(
        label="badge",
        phrase="a bright hero badge",
        type="badge",
        region="chest",
    ),
}

GEAR = [
    Gear(
        id="earmuffs",
        label="earmuffs",
        covers={"ears"},
        guards={"confuse"},
        prep="put on the earmuffs",
        tail="walked back to the quiet corner",
    ),
    Gear(
        id="guidebook",
        label="a museum guidebook",
        covers={"hands"},
        guards={"bump"},
        prep="carry the guidebook instead",
        tail="slowed down to read the signs",
    ),
]

HERO_NAMES = ["Maya", "Leo", "Jules", "Nina", "Pip"]
SIDEKICKS = ["Spark", "Comet", "Zing"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    hero: str
    sidekick: str
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


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone or action.id == "rhyme"


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.mess in gear.guards:
            return gear
    return None


def explain_invalid(action: Action, prize: Prize) -> str:
    return (
        f"(No story: the chosen rhyme would not plausibly affect {prize.label}, "
        f"so the misunderstanding cannot meaningfully change the ending.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))

    hero = world.add(Entity(id=params.hero, kind="character", type="hero"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="sidekick"))
    prize = world.add(Entity(
        id="prize",
        type=_safe_lookup(PRIZES, params.prize).type,
        label=_safe_lookup(PRIZES, params.prize).label,
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        owner=hero.id,
        caretaker=hero.id,
        region=_safe_lookup(PRIZES, params.prize).region,
        plural=_safe_lookup(PRIZES, params.prize).plural,
    ))
    hero.memes["pride"] = 1.0
    hero.memes["hope"] = 1.0
    sidekick.memes["trust"] = 1.0

    # Act 1: setup.
    world.say(
        f"{hero.id} was a small superhero who loved {_safe_lookup(ACTIONS, params.action).gerund} "
        f"through {world.place.name}."
    )
    world.say(
        f"{hero.id} wore {prize.phrase} and felt ready to save the day."
    )
    world.para()

    # Act 2: the rhyme and misunderstanding.
    action = _safe_lookup(ACTIONS, params.action)
    if action.id == "hurry":
        hero.meters["speed"] = 2.0
        hero.meters["bump"] = 1.0
        world.say(
            f"At the children's museum, {hero.id} saw the moon wheel and began to hurry."
        )
        world.say(
            f'{hero.id} called, "When you see a shiny sign, take a speedy spin!"'
        )
        world.say(
            f"{params.sidekick} heard the rhyme and thought it meant the spinning room was a game room."
        )
        sidekick.memes["confusion"] = 1.0
    else:
        world.say(
            f"{hero.id} sang a rhyme about a bright door and a brave tour."
        )
        world.say(
            f"{params.sidekick} misunderstood the rhyme and thought the closed exhibit was open."
        )
        sidekick.memes["confusion"] = 1.0

    world.para()

    # Bad ending: the misunderstanding turns small and sour.
    gear = select_gear(action, prize)
    if gear:
        world.say(
            f"{params.sidekick} tried to help, but the plan was already slipping."
        )
        world.say(
            f"{hero.id} could have used {gear.label}, yet the hurry left no time."
        )
    hero.memes["worry"] = 1.0
    hero.memes["sadness"] = 2.0
    sidekick.memes["apology"] = 1.0
    prize.meters["safe"] = 0.0
    prize.meters["dropped"] = 1.0

    world.say(
        f"The misunderstanding made everything worse. {hero.id} slipped, and {prize.label} "
        f"fell to the floor with a soft thud."
    )
    world.say(
        f"The museum helper picked up the {prize.label}, but the shiny part was scuffed."
    )
    world.say(
        f"{hero.id} felt bad because the day ended with a mess instead of a rescue."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        prize=prize,
        action=action,
        gear=gear,
        place=world.place,
        bad_ending=True,
        misunderstanding=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short superhero story set in a children\'s museum that includes a hurry, a rhyme, and a misunderstanding.',
        f"Tell a kid-friendly story where {f['hero'].id} hurries through {f['place'].name} and a rhyme goes wrong.",
        "Write a tiny story that ends with a bad ending after a mistaken rhyme at the children's museum.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    prize = _safe_fact(world, f, "prize")
    action = _safe_fact(world, f, "action")
    return [
        QAItem(
            question=f"Where did {hero.id} hurry while wearing {prize.phrase}?",
            answer=f"{hero.id} hurried through {world.place.name}, which is a children's museum.",
        ),
        QAItem(
            question=f"What did {hero.id} do that caused the misunderstanding?",
            answer=f"{hero.id} made a rhyme while hurrying, and {sidekick.id} misunderstood it.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {prize.label}?",
            answer=f"It ended badly: the {prize.label} fell, got scuffed, and {hero.id} felt sad.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The hurry and the rhyme created a misunderstanding, and the wrong move caused a fall.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a children's museum?",
            answer="A children's museum is a place with playful exhibits where kids can learn by touching, moving, and exploring.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a playful sound pattern where words end with the same or similar sounds.",
        ),
        QAItem(
            question="What does it mean to hurry?",
            answer="To hurry means to move or act quickly, often because someone is in a rush.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts describe places, actions, prizes, and gear.
% A prize is at risk when the action can plausibly affect its region.
prize_at_risk(A,P) :- action(A), prize(P), action_zone(A,R), prize_region(P,R).
prize_at_risk(rhyme,P) :- action(rhyme), prize(P).

% A gear choice is reasonable if it addresses the mess created by the action.
good_gear(A,G) :- action(A), gear(G), action_mess(A,M), gear_guards(G,M).

valid_story(Place,A,P) :- place(Place), action(A), prize(P), prize_at_risk(A,P), good_gear(A,_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_mess", aid, action.mess))
        for r in sorted(action.zone):
            lines.append(asp.fact("action_zone", aid, r))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("prize_region", prid, prize.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("gear_guards", gear.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def py_valid() -> list[tuple]:
    out = []
    for pid in PLACES:
        for aid, action in ACTIONS.items():
            if aid not in _safe_lookup(PLACES, pid).affords:
                continue
            for prid, prize in PRIZES.items():
                if prize_at_risk(action, prize) and select_gear(action, prize):
                    out.append((pid, aid, prid))
    return sorted(set(out))


def asp_verify() -> int:
    a, p = set(asp_valid()), set(py_valid())
    if a == p:
        print(f"OK: ASP matches Python gate ({len(a)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if a - p:
        print("Only in ASP:", sorted(a - p))
    if p - a:
        print("Only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style children's museum storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    action = getattr(args, "action", None) or rng.choice(list(_safe_lookup(PLACES, place).affords))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if getattr(args, "action", None) and getattr(args, "prize", None):
        act = _safe_lookup(ACTIONS, getattr(args, "action", None))
        pr = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not prize_at_risk(act, pr) or not select_gear(act, pr):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    return StoryParams(place=place, action=action, prize=prize, hero=name, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid()
        print(f"{len(stories)} valid stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        params_list = [
            StoryParams("children_museum", "hurry", "cape", "Maya", "Spark"),
            StoryParams("children_museum", "rhyme", "badge", "Leo", "Comet"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
