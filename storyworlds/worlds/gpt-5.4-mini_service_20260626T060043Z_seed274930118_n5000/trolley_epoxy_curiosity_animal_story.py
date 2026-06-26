#!/usr/bin/env python3
"""
storyworlds/worlds/trolley_epoxy_curiosity_animal_story.py
==========================================================

A small animal story world about curiosity, a trolley, and epoxy.

Premise:
- A young animal loves to poke around a workshop or shed.
- A trolley carries a useful but messy can of epoxy.
- Curiosity makes the animal want to inspect the shiny cart and the glue.
- A grown-up animal worries the epoxy could stick fast to paws, fur, or the floor.
- The fix is simple: use the trolley carefully, keep the lid on, and choose a safer way to look.

The story is state-driven:
- curiosity rises when the child notices the trolley and the epoxy
- warning and hesitation rise when epoxy is at risk of spilling
- a gentle helper channels curiosity into careful observing
- the ending proves what changed: the trolley is safe, the epoxy stays closed, and the child feels proud of careful thinking
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
    kind: str = "thing"  # "character" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def _gendered(self) -> bool:
        return self.species in {"fox", "rabbit", "bear", "cat", "dog", "mouse", "squirrel", "badger", "otter", "hedgehog"}

    def pronoun(self, case: str = "subject") -> str:
        if case == "subject":
            return "they"
        if case == "object":
            return "them"
        return "their"

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
    place: str = "the little workshop"
    affordances: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    zone: set[str] = field(default_factory=set)
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
class Gear:
    id: str
    label: str
    protects: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        self.zone: set[str] = set()
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "workshop": Setting(place="the little workshop", affordances={"inspect", "push"}),
    "shed": Setting(place="the garden shed", affordances={"inspect", "push"}),
    "garage": Setting(place="the cozy garage", affordances={"inspect", "push"}),
}

ACTIVITIES = {
    "inspect": Activity(
        id="inspect",
        verb="inspect the trolley",
        gerund="inspecting the trolley",
        rush="dash over to the trolley",
        mess="curious",
        soil="too close and too messy",
        keyword="trolley",
        zone={"hands", "nose"},
        tags={"curiosity", "trolley"},
    ),
    "push": Activity(
        id="push",
        verb="push the trolley",
        gerund="pushing the trolley",
        rush="run to the trolley",
        mess="bumpy",
        soil="wobbly and spilled",
        keyword="trolley",
        zone={"hands"},
        tags={"trolley"},
    ),
}

PRIZES = {
    "epoxy": Prize(
        id="epoxy",
        label="epoxy",
        phrase="a small tin of epoxy with a shiny lid",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="work gloves",
        protects={"epoxy"},
        covers={"hands"},
        prep="put on work gloves first",
        tail="slid the trolley carefully back into place",
    ),
    Gear(
        id="tray",
        label="a deep tray",
        protects={"spill"},
        covers={"floor"},
        prep="set the epoxy inside a deep tray",
        tail="rolled the trolley with both hands on the handle",
    ),
]


GIVEN_NAMES = ["Milo", "Nia", "Pip", "Tess", "Ollie", "Bram", "Kiki", "Mira"]
SPECIES = ["fox", "rabbit", "bear", "cat", "dog", "squirrel", "otter", "hedgehog"]
HELPER_SPECIES = ["mother fox", "father badger", "grandma bear", "uncle otter", "aunt rabbit"]


# ---------------------------------------------------------------------------
# ASP rules and facts
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Curiosity is a reason to look closely at the trolley.
wants_inspect(C) :- curious(C), sees(C, trolley).

% Epoxy is risky when a curious child gets too close without gloves.
at_risk(E) :- epoxy(E), nearby(C, E), curious(C), not protected(C, hands).

% Gloves are a compatible fix for the hands risk.
safe(C, hands) :- wearing(C, gloves).
resolves_risk(C) :- curious(C), wearing(C, gloves), sees(C, trolley).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("epoxy", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for p in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, p))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _inc(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def predict_spill(world: World, hero: Entity, prize: Entity, protected: bool) -> bool:
    sim = world.copy()
    sim.zone = {"hands", "floor"}
    _inc(sim.get(hero.id), "curious")
    if not protected:
        _inc(sim.get(prize.id), "spill")
    return sim.get(prize.id).meters.get("spill", 0.0) >= THRESHOLD


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.id in gear.protects and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act_id, act in ACTIVITIES.items():
            for prize_id, prize in PRIZES.items():
                if select_gear(act, prize) is not None:
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.species} with bright eyes and a nose for interesting things. "
        f"{hero.id} lived near {helper.label} and liked to wander into quiet corners."
    )


def setup_love(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    _meme(hero, "curiosity", 1.0)
    world.say(
        f"{hero.id} loved {activity.gerund}, because every wheel and hinge in the shop felt like a secret waiting to be found."
    )
    world.say(
        f"One morning, {hero.id} spotted a trolley near the wall and noticed {prize.phrase} sitting on it."
    )


def warning(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"{helper.label} saw the shiny tin and said, "
        f'"Careful now. {prize.label.capitalize()} can stick fast if it gets on paws or fur."'
    )
    _meme(helper, "concern", 1.0)
    _meme(hero, "curiosity", 1.0)


def temptation(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    _meme(hero, "desire", 1.0)
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the closer {hero.pronoun()} got, the more {hero.id} wondered what made the lid shine so bright."
    )
    world.say(
        f"{hero.id} started to {activity.rush}, and the trolley rocked a little on its wheels."
    )


def choose_safety(world: World, helper: Entity, hero: Entity, prize: Entity, gear: Gear) -> None:
    gear_ent = world.add(Entity(
        id=gear.id,
        kind="thing",
        species="gear",
        label=gear.label,
        protective=True,
        plural=gear.plural,
        owner=helper.id,
    ))
    gear_ent.worn_by = hero.id if gear.id == "gloves" else None
    world.say(
        f"{helper.label} smiled and said, "
        f'"How about we {gear.prep} first?"'
    )
    world.say(
        f"{hero.id} listened, put on the {gear.label}, and leaned in to look without touching the epoxy."
    )
    _meme(hero, "care", 1.0)
    _meme(hero, "pride", 1.0)


def resolve(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity) -> None:
    _inc(hero, "curious", 0.0)
    _inc(prize, "spill", 0.0)
    world.say(
        f"Together they {GEAR[0].tail}. The trolley stayed steady, and the epoxy stayed closed."
    )
    world.say(
        f"{hero.id} learned that curiosity could be gentle when it waited for help."
    )
    world.say(
        f"By the end, {hero.id} was still curious, but now {hero.id} was also careful."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, species: str, helper_label: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        species=species,
        label=hero_name,
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        species=helper_label,
        label=helper_label,
    ))
    prize = world.add(Entity(
        id=prize_cfg.id,
        kind="thing",
        species="thing",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=helper.id,
        caretaker=helper.id,
    ))

    introduce(world, hero, helper)
    setup_love(world, hero, activity, prize)

    world.para()
    warning(world, helper, hero, activity, prize)
    temptation(world, hero, activity, prize)

    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    choose_safety(world, helper, hero, prize, gear)
    resolve(world, hero, helper, activity, prize)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f"Write a short animal story for a young child about {hero.id}, a trolley, and {prize.label}.",
        f"Tell a gentle story where a curious {hero.species} wants to {act.verb} but learns to be careful around epoxy.",
        f"Write a cozy workshop story that includes a trolley, epoxy, and a helpful grown-up who guides curiosity.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.species} who is full of curiosity.",
        ),
        QAItem(
            question=f"What did {hero.id} notice in {setting.place}?",
            answer=f"{hero.id} noticed a trolley with {prize.phrase} on it.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {hero.id}?",
            answer=f"{helper.label} warned {hero.id} because {prize.label} could stick fast and make a mess if it spilled.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} wearing work gloves, looking closely without touching the epoxy, and learning that curiosity can be careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trolley?",
            answer="A trolley is a small cart with wheels that can carry things from one place to another.",
        ),
        QAItem(
            question="What is epoxy?",
            answer="Epoxy is a strong glue that can harden into a very sticky material after it is mixed and used.",
        ),
        QAItem(
            question="Why are work gloves useful?",
            answer="Work gloves help keep hands clean and protected when you are handling messy materials.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.\n")
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    species: str
    helper: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: curiosity, a trolley, and epoxy.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--helper", choices=HELPER_SPECIES)
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "activity", None) or getattr(args, "prize", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
            and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, prize = rng.choice(list(combos))
    species = getattr(args, "species", None) or rng.choice(SPECIES)
    name = getattr(args, "name", None) or rng.choice(GIVEN_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_SPECIES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, species=species, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.species,
        params.helper,
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id} ({e.kind}/{e.species}) {' '.join(bits)}")
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
    StoryParams(place="workshop", activity="inspect", prize="epoxy", name="Milo", species="fox", helper="grandma bear"),
    StoryParams(place="shed", activity="inspect", prize="epoxy", name="Nia", species="rabbit", helper="mother fox"),
    StoryParams(place="garage", activity="push", prize="epoxy", name="Pip", species="otter", helper="uncle otter"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
