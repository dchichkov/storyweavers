#!/usr/bin/env python3
"""
storyworlds/worlds/tuition_cautionary_humor_animal_story.py
============================================================

A small animal-story world about a child, a tuition bill, a tempting splurge,
and a parent who helps turn a silly mistake into a safe choice.

Seed tale premise:
- A young animal wants to spend money on something funny and unnecessary.
- A parent reminds the child that tuition must be paid first.
- The child learns to be careful with coins, laughs at the silly temptation,
  and ends up doing the responsible thing.

The story world is intentionally tiny and state-driven:
- physical meters track money, bills, and purchased goods
- emotional memes track worry, mischief, caution, relief, and pride
- the narrative is assembled from those state changes rather than from a fixed
  paragraph with swapped nouns
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    price: int = 0
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    teacher: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
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
    place: str
    indoors: bool = False
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
class Temptation:
    id: str
    label: str
    phrase: str
    price: int
    humor: str
    warning: str
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
class TuitionPlan:
    id: str
    label: str
    fee: int
    lesson: str
    place: str
    gentle_risk: str
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
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    child_kind: str
    child_name: str
    parent_kind: str
    tuition: str
    temptation: str
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


SETTINGS = {
    "school_lane": Setting(place="the school lane"),
    "market_square": Setting(place="the market square"),
    "river_dock": Setting(place="the river dock"),
}

CHILD_KINDS = {
    "rabbit": "rabbit",
    "fox": "fox",
    "otter": "otter",
    "bear": "bear",
    "panda": "panda",
}

PARENT_KINDS = {
    "mother": "mother",
    "father": "father",
    "aunt": "aunt",
}

TUITION_PLANS = {
    "music": TuitionPlan(
        id="music",
        label="music tuition",
        fee=5,
        lesson="take music lessons",
        place="the music school",
        gentle_risk="the lesson could not start if the tuition was unpaid",
    ),
    "art": TuitionPlan(
        id="art",
        label="art tuition",
        fee=4,
        lesson="join art class",
        place="the little art room",
        gentle_risk="the crayons would wait while the tuition stayed unpaid",
    ),
    "reading": TuitionPlan(
        id="reading",
        label="reading tuition",
        fee=3,
        lesson="go to reading club",
        place="the reading nook",
        gentle_risk="the story time would not begin until the tuition was paid",
    ),
}

TEMPTATIONS = {
    "honeybun": Temptation(
        id="honeybun",
        label="honey bun",
        phrase="a sticky honey bun",
        price=2,
        humor="it smelled so sweet that even the bees would have nodded politely",
        warning="the bun was funny, but it was not more important than school",
    ),
    "marbles": Temptation(
        id="marbles",
        label="bag of marbles",
        phrase="a tiny bag of shiny marbles",
        price=3,
        humor="they sparkled like three little moons rolling in a sock",
        warning="the marbles jingled, but tuition needed the coins first",
    ),
    "toy_mouse": Temptation(
        id="toy_mouse",
        label="wind-up mouse",
        phrase="a squeaky wind-up mouse",
        price=4,
        humor="its nose twitched like it had just told a joke to itself",
        warning="the toy looked silly, but the school bill had to be paid before fun things",
    ),
}

NAMES = {
    "rabbit": ["Ruby", "Nibbles", "Momo", "Poppy"],
    "fox": ["Finn", "Toby", "Milo", "Rusty"],
    "otter": ["Ollie", "Tilly", "Nori", "Pip"],
    "bear": ["Bruno", "Benny", "Mina", "Bram"],
    "panda": ["Panda", "Penny", "Mimi", "Pao"],
}

TRAITS = ["careful", "curious", "silly", "bright", "bouncy", "chatty"]


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def tuition_at_risk(plan: TuitionPlan, budget: int, temptation: Temptation) -> bool:
    return budget >= plan.fee and budget - temptation.price < plan.fee


def select_fix(plan: TuitionPlan, budget: int, temptation: Temptation) -> bool:
    return budget >= plan.fee


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for t in TUITION_PLANS:
            for x in TEMPTATIONS:
                plan = _safe_lookup(TUITION_PLANS, t)
                temp = _safe_lookup(TEMPTATIONS, x)
                if select_fix(plan, 6, temp) and tuition_at_risk(plan, 6, temp):
                    combos.append((place, t, x))
    return combos


def predict(world: World, child: Entity, plan: TuitionPlan, temp: Temptation) -> dict[str, object]:
    sim = world.copy()
    child_sim = sim.get(child.id)
    child_sim.meters["coins"] -= temp.price
    child_sim.memes["mischief"] += 1
    return {
        "can_pay": child_sim.meters["coins"] >= plan.fee,
        "coins_left": child_sim.meters["coins"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def _introduce(world: World, child: Entity, parent: Entity, plan: TuitionPlan, temp: Temptation) -> None:
    trait = next((t for t in child.memes.get("traits", []) if t != "little"), "careful")
    world.say(
        f"{child.id} was a little {trait} {child.type} who loved walking beside "
        f"{parent.pronoun('possessive')} {parent.type} through {world.setting.place}."
    )
    world.say(
        f"{child.pronoun().capitalize()} had {plan.label} to think about, and "
        f"{temp.humor}."
    )


def _prepare(world: World, child: Entity, parent: Entity, plan: TuitionPlan) -> None:
    child.memes["hope"] += 1
    child.meters["coins"] += 6
    parent.meters["pouch"] += 1
    world.say(
        f"That morning, {parent.id} counted out six bright coins for {child.id}. "
        f"Three would not do; {plan.label} cost {plan.fee} coins."
    )


def _want_splurge(world: World, child: Entity, temp: Temptation) -> None:
    child.memes["want"] += 1
    child.memes["mischief"] += 1
    world.say(
        f"{child.id} spotted {temp.phrase} at a stall and wanted it right away. "
        f"{temp.warning.capitalize()}."
    )


def _warn(world: World, parent: Entity, child: Entity, plan: TuitionPlan, temp: Temptation) -> None:
    pred = predict(world, child, plan, temp)
    world.facts["predicted_can_pay"] = pred["can_pay"]
    world.facts["predicted_coins_left"] = pred["coins_left"]
    if not pred["can_pay"]:
        pass
    if child.meters["coins"] - temp.price < plan.fee:
        world.say(
            f'"No, {child.id}," said {parent.id}. "If you spend those coins, there will not be enough left for {plan.label}."'
        )
    else:
        world.say(
            f'"Careful," said {parent.id}. "That little treat is funny, but {plan.label} comes first."'
        )


def _pause(world: World, child: Entity, temp: Temptation) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} held the coins up to the light and made a tiny face. "
        f"The {temp.label} looked sillier each time {child.id} imagined carrying it home."
    )


def _choose_tuition(world: World, child: Entity, parent: Entity, plan: TuitionPlan, temp: Temptation) -> None:
    child.memes["caution"] += 1
    child.memes["relief"] += 1
    child.meters["coins"] -= plan.fee
    child.meters["paid_tuition"] += plan.fee
    world.say(
        f"Then {child.id} laughed and said, \"The school bill is the important one.\" "
        f"{child.pronoun().capitalize()} gave the coins to the teacher for {plan.label}."
    )
    world.say(
        f"The funny little {temp.label} stayed at the stall, and {child.id} still had "
        f"{child.meters['coins']:.0f} coin{'s' if child.meters['coins'] != 1 else ''} left for later."
    )


def _resolution(world: World, child: Entity, parent: Entity, plan: TuitionPlan) -> None:
    child.memes["pride"] += 1
    child.memes["worry"] = 0
    world.say(
        f"After that, {child.id} could {plan.lesson} at {plan.place}. "
        f"{parent.id} smiled, and {child.id} walked along with a neat empty pocket and a very responsible grin."
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def tell(setting: Setting, child_kind: str, child_name: str, parent_kind: str, plan: TuitionPlan, temp: Temptation) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_kind))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_kind))
    teacher = world.add(Entity(id="Teacher", kind="character", type="teacher"))

    child.memes["traits"] = ["little", random.choice(TRAITS)]

    _introduce(world, child, parent, plan, temp)
    world.para()
    _prepare(world, child, parent, plan)
    _want_splurge(world, child, temp)
    _warn(world, parent, child, plan, temp)
    _pause(world, child, temp)
    _choose_tuition(world, child, parent, plan, temp)
    world.para()
    _resolution(world, child, parent, plan)

    world.facts.update(
        child=child,
        parent=parent,
        teacher=teacher,
        plan=plan,
        temptation=temp,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    plan: TuitionPlan = _safe_fact(world, f, "plan")
    temp: Temptation = _safe_fact(world, f, "temptation")
    return [
        f'Write a short animal story for a child who almost spends tuition money on {temp.phrase}.',
        f"Tell a cautionary, funny story where {child.id} must remember that {plan.label} comes first.",
        f'Write a gentle story about an animal child, a tempting purchase, and paying tuition on time.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    plan: TuitionPlan = _safe_fact(world, f, "plan")
    temp: Temptation = _safe_fact(world, f, "temptation")
    qa = [
        QAItem(
            question=f"What did {child.id} almost buy instead of paying for {plan.label}?",
            answer=f"{child.id} almost bought {temp.phrase}, but that would have been a silly splurge before school.",
        ),
        QAItem(
            question=f"Why did {parent.id} tell {child.id} to be careful with the coins?",
            answer=f"{parent.id} knew the coins had to pay for {plan.label} first, so the fun little treat had to wait.",
        ),
        QAItem(
            question=f"What did {child.id} do at the end?",
            answer=f"{child.id} laughed, paid for {plan.label}, and kept the rest of the coins safe for later.",
        ),
        QAItem(
            question=f"How did {child.id} feel after making the careful choice?",
            answer=f"{child.id} felt relieved and proud, because the responsible choice worked and the story ended happily.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "tuition": [
        (
            "What is tuition?",
            "Tuition is the money paid for lessons or school, so a child can learn there.",
        )
    ],
    "coins": [
        (
            "What are coins for?",
            "Coins are small pieces of money that people can save, count, and spend carefully.",
        )
    ],
    "honey bun": [
        (
            "Why can a honey bun be a treat?",
            "A honey bun is a sweet snack, so it is a treat and not an everyday school need.",
        )
    ],
    "marbles": [
        (
            "Why are marbles fun to look at?",
            "Marbles can be shiny and colorful, so they look playful even when they are tiny.",
        )
    ],
    "mouse": [
        (
            "Why is a wind-up toy funny?",
            "A wind-up toy can wobble and squeak in a silly way, which often makes children laugh.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    temp: Temptation = _safe_fact(world, f, "temptation")
    out = [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["tuition"]]
    out.append(QAItem(question="Why do careful animals count their coins before spending them?", answer="Because once the coins are gone, they cannot be used for more important things like tuition."))
    if temp.id == "honeybun":
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["honey bun"])
    elif temp.id == "marbles":
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["marbles"])
    else:
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["mouse"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
tuition_option(P,T,X) :- place(P), tuition(T), temptation(X), fee(T,F), price(X,XP), budget(B), B >= F, B - XP >= F.
valid_story(P,T,X) :- tuition_option(P,T,X).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for tid, plan in TUITION_PLANS.items():
        lines.append(asp.fact("tuition", tid))
        lines.append(asp.fact("fee", tid, plan.fee))
    for xid, temp in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", xid))
        lines.append(asp.fact("price", xid, temp.price))
    lines.append(asp.fact("budget", 6))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about tuition, caution, and a funny temptation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child-kind", choices=CHILD_KINDS)
    ap.add_argument("--parent-kind", choices=PARENT_KINDS)
    ap.add_argument("--tuition", choices=TUITION_PLANS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--name")
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
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "tuition", None) is None or c[1] == getattr(args, "tuition", None))
        and (getattr(args, "temptation", None) is None or c[2] == getattr(args, "temptation", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tuition, temptation = rng.choice(list(combos))
    child_kind = getattr(args, "child_kind", None) or rng.choice(list(CHILD_KINDS))
    parent_kind = getattr(args, "parent_kind", None) or rng.choice(list(PARENT_KINDS))
    child_name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, child_kind))
    return StoryParams(
        place=place,
        child_kind=child_kind,
        child_name=child_name,
        parent_kind=parent_kind,
        tuition=tuition,
        temptation=temptation,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        params.child_kind,
        params.child_name,
        params.parent_kind,
        _safe_lookup(TUITION_PLANS, params.tuition),
        _safe_lookup(TEMPTATIONS, params.temptation),
    )
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
    StoryParams(place="school_lane", child_kind="rabbit", child_name="Ruby", parent_kind="mother", tuition="music", temptation="honeybun"),
    StoryParams(place="market_square", child_kind="otter", child_name="Ollie", parent_kind="father", tuition="art", temptation="marbles"),
    StoryParams(place="river_dock", child_kind="fox", child_name="Finn", parent_kind="aunt", tuition="reading", temptation="toy_mouse"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.child_name}: {p.tuition} vs {p.temptation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
