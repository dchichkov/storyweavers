#!/usr/bin/env python3
"""
storyworlds/worlds/prospector_remind_session_foreshadowing_teamwork_adventure.py
================================================================================

A small adventure storyworld about a prospector, a reminder session, and a
careful teamwork turn that pays off a foreshadowed challenge.

Premise:
- A prospector is preparing for a short session at an old mine.
- A teammate reminds the prospector about a clue from earlier signs.
- The warning matters because the mine hides a simple but real obstacle.
- Teamwork turns the risky outing into a successful little adventure.

This world is intentionally compact: the simulated state tracks the prospector's
gear, the hint from the reminder session, the mine's condition, and whether the
team solves the obstacle together.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ally: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"man", "boy", "father", "dad", "prospector"}
        female = {"woman", "girl", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str
    indoors: bool = False
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
class Challenge:
    id: str
    noun: str
    verb: str
    warning: str
    clue: str
    obstacle: str
    risk: str
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
class Gear:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    tail: str
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
class StoryParams:
    setting: str
    challenge: str
    gear: str
    name: str
    partner: str
    trait: str
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


def _r_obstacle(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.meters.get("alert", 0.0) < THRESHOLD:
            continue
        if e.meters.get("prepared", 0.0) < THRESHOLD:
            continue
        if e.meters.get("helped", 0.0) < THRESHOLD:
            continue
        sig = ("obstacle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["obstacle_solved"] = 1.0
        out.append("The warning helped them solve the obstacle before it could trap them.")
    return out


CAUSAL_RULES = [
    _r_obstacle,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "mine": Setting(place="the old mine", indoors=False, affords={"dig", "explore"}),
    "canyon": Setting(place="the narrow canyon", indoors=False, affords={"explore"}),
    "camp": Setting(place="the camp edge", indoors=False, affords={"explore", "dig"}),
}

CHALLENGES = {
    "cave_in": Challenge(
        id="cave_in",
        noun="loose stones",
        verb="explore the tunnel",
        warning="The tunnel may shed stones from above",
        clue="a crack in the ceiling and dust on the floor",
        obstacle="a shelf of loose stones blocking the path",
        risk="one bump could start a small cave-in",
        tags={"stones", "mine", "warning"},
    ),
    "river_crossing": Challenge(
        id="river_crossing",
        noun="fast water",
        verb="cross the stream",
        warning="The water is faster than it looks",
        clue="wet grass and a crooked branch downstream",
        obstacle="a slippery crossing with strong water",
        risk="a wrong step could send boots skidding",
        tags={"water", "river", "warning"},
    ),
    "dark_turn": Challenge(
        id="dark_turn",
        noun="dark corners",
        verb="walk deeper in",
        warning="Dark corners can hide a wrong turn",
        clue="a faded sign and old chalk marks",
        obstacle="a fork where the path is easy to miss",
        risk="getting turned around before anyone notices",
        tags={"dark", "path", "warning"},
    ),
}

GEAR = [
    Gear(
        id="lantern",
        label="a lantern",
        phrase="a bright lantern",
        helps={"dark"},
        prep="carry the lantern up front",
        tail="kept the lantern swinging where the path was darkest",
    ),
    Gear(
        id="rope",
        label="a rope",
        phrase="a sturdy rope",
        helps={"stones", "water"},
        prep="tie the rope to the pack",
        tail="used the rope to stay together when the ground shifted",
    ),
    Gear(
        id="boots",
        label="mud boots",
        phrase="mud boots",
        helps={"water"},
        prep="lace on the mud boots",
        tail="splashed on without losing a step",
        plural=True,
    ),
    Gear(
        id="chalk",
        label="a chalk stick",
        phrase="a chalk stick",
        helps={"path"},
        prep="slide the chalk stick into a pocket",
        tail="left chalk marks so they could find the way back",
    ),
]

NAMES = ["Ada", "Milo", "Tess", "Nico", "Rae", "Lena", "Owen", "Iris"]
TRAITS = ["curious", "steady", "brave", "clever", "careful", "lively"]
PARTNERS = ["friend", "sister", "brother", "guide", "helper"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        for cid, chal in CHALLENGES.items():
            if cid == "cave_in":
                gear_ok = "rope"
            elif cid == "river_crossing":
                gear_ok = "boots"
            else:
                gear_ok = "lantern"
            combos.append((sname, cid, gear_ok))
    return combos


def describe_setting(setting: Setting, challenge: Challenge) -> str:
    if setting.place == "the old mine":
        return "The mine mouth yawned ahead, and a thin dust line sat on the stones."
    if setting.place == "the narrow canyon":
        return "The canyon walls leaned in close, and the path looked like a ribbon."
    return "The camp edge was quiet, with tracks and tools resting near the fire ring."


def predict_risk(world: World, hero: Entity, challenge: Challenge, gear: Gear) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["prepared"] = 1.0
    if any(tag in gear.helps for tag in challenge.tags):
        sim.get(hero.id).meters["helped"] = 1.0
    sim.get(hero.id).meters["alert"] = 1.0
    propagate(sim, narrate=False)
    return sim.get(hero.id).meters.get("obstacle_solved", 0.0) >= THRESHOLD


def build_world(setting: Setting, challenge: Challenge, gear: Gear, name: str,
                partner: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type="prospector",
        traits=["small", trait],
    ))
    ally = world.add(Entity(
        id="Ally",
        kind="character",
        type=partner,
        label=f"the {partner}",
        traits=["patient", "helpful"],
    ))
    item = world.add(Entity(
        id="gear",
        type=gear.id,
        label=gear.label,
        phrase=gear.phrase,
        owner=hero.id,
        carried_by=hero.id,
        plural=gear.plural,
    ))

    world.say(f"{hero.id} was a {trait} prospector who loved looking for signs of old treasure.")
    world.say(
        f"{hero.pronoun().capitalize()} and {ally.label} had planned a short session at "
        f"{world.setting.place}."
    )
    world.say(f"Before they left, {hero.id} had noticed {challenge.clue}, and that clue stayed in mind.")

    world.para()
    world.say(describe_setting(setting, challenge))
    world.say(f"It was a good place to {challenge.verb}, but {challenge.warning.lower()}.")

    world.say(
        f"{ally.label.capitalize()} reminded {hero.id} about the clue: {challenge.warning.lower()}."
    )
    hero.meters["alert"] += 1
    hero.memes["foreshadowing"] = hero.memes.get("foreshadowing", 0.0) + 1
    world.say(
        f"{hero.id} listened carefully, because the earlier clue matched the way the ground felt now."
    )

    world.para()
    hero.meters["prepared"] += 1
    world.say(f"{hero.id} chose {gear.phrase} and got ready to go.")
    if any(tag in gear.helps for tag in challenge.tags):
        hero.meters["helped"] += 1
        world.say(
            f"The gear fit the danger well, so the two of them could face {challenge.obstacle} together."
        )
    else:
        pass

    if challenge.id == "cave_in":
        world.say(
            f"When they reached the tunnel, a little slide of stones answered the warning exactly."
        )
    elif challenge.id == "river_crossing":
        world.say(
            f"When they reached the stream, the water pulled at the bank just as the reminder had suggested."
        )
    else:
        world.say(
            f"When they rounded the bend, the dark path hid a choice that looked smaller than it was."
        )

    if predict_risk(world, hero, challenge, gear):
        world.say(
            f"{hero.id} and {ally.label} worked side by side, and they solved the problem before it grew worse."
        )
        world.say(
            f"They used {gear.label} {gear.tail}, and the path opened again."
        )
        world.say(
            f"At the end of the session, the prospector smiled at the saved route and the useful reminder."
        )

    world.facts.update(hero=hero, ally=ally, gear=item, challenge=challenge, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    challenge = _safe_fact(world, f, "challenge")
    return [
        f'Write a short adventure story for a young child about a prospector named {hero.id}, a reminder session, and a team that solves {challenge.noun}.',
        f'Tell a gentle adventure where a prospector remembers a warning, listens to a partner, and uses teamwork to deal with {challenge.obstacle}.',
        f'Write a child-friendly story that includes the words "prospector", "remind", and "session", and ends with a brave little problem being solved together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ally = _safe_fact(world, f, "ally")
    challenge = _safe_fact(world, f, "challenge")
    gear = _safe_fact(world, f, "gear")
    place = _safe_fact(world, f, "setting").place
    trait = next((t for t in hero.traits if t not in {"small"}), "curious")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {trait} prospector, and {ally.label}, who helped with the plan at {place}.",
        ),
        QAItem(
            question=f"What did {ally.label} remind {hero.id} about?",
            answer=f"{ally.label.capitalize()} reminded {hero.id} about the clue that {challenge.warning.lower()}, and that foreshadowed the danger ahead.",
        ),
        QAItem(
            question=f"How did teamwork help at {place}?",
            answer=f"{hero.id} and {ally.label} used {gear.label} together, stayed calm, and solved {challenge.obstacle} before the trouble grew bigger.",
        ),
        QAItem(
            question=f"What was the end of the short session like?",
            answer=f"The session ended with the path open again, the danger handled, and {hero.id} feeling proud of the teamwork.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prospector?",
            answer="A prospector is a person who looks for valuable things in the ground, like gold, rocks, or old clues from the earth.",
        ),
        QAItem(
            question="What does remind mean?",
            answer="To remind someone means to help them remember something important they may have forgotten.",
        ),
        QAItem(
            question="What is a session?",
            answer="A session is a short time set aside to do one activity, like a practice, visit, or job.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and work together to finish a job or solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

valid(Setting, Challenge, Gear) :- setting(Setting), challenge(Challenge), gear(Gear),
                                   compatible(Challenge, Gear).

compatible(cave_in, rope).
compatible(river_crossing, boots).
compatible(dark_turn, lantern).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a prospector, a reminder session, and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gear", choices={g.id for g in GEAR})
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=PARTNERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "challenge", None):
        combos = [c for c in combos if c[1] == getattr(args, "challenge", None)]
    if getattr(args, "gear", None):
        combos = [c for c in combos if c[2] == getattr(args, "gear", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, challenge, gear = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        challenge=challenge,
        gear=gear,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        partner=getattr(args, "partner", None) or rng.choice(PARTNERS),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(CHALLENGES, params.challenge),
        next(g for g in GEAR if g.id == params.gear),
        params.name,
        params.partner,
        params.trait,
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
    StoryParams(setting="mine", challenge="cave_in", gear="rope", name="Ada", partner="guide", trait="careful"),
    StoryParams(setting="canyon", challenge="dark_turn", gear="lantern", name="Milo", partner="friend", trait="curious"),
    StoryParams(setting="camp", challenge="river_crossing", gear="boots", name="Tess", partner="sister", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} compatible combos:")
        for t in asp.atoms(model, "valid"):
            print(" ", t)
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
            header = f"### {p.name}: {p.challenge} at {p.setting} (gear: {p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
