#!/usr/bin/env python3
"""
storyworlds/worlds/parachute_flashback_sound_effects_superhero_story.py
=======================================================================

A small superhero storyworld with a parachute, a flashback beat, and vivid
sound effects.

The seed premise:
- A little superhero wants to leap into action.
- The city mission is too high for a normal jump.
- A remembered training scene shows how a parachute works.
- The hero uses the parachute, lands safely, and saves the day with style.

The world is intentionally tiny and classical:
- one hero
- one sidekick
- one place
- one mission
- one useful gear choice
- one brief flashback

The story is driven by world state, not by a frozen paragraph.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    gear: object | None = None
    hero: object | None = None
    mentor: object | None = None
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
    place: str
    height: str
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
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    sound: str
    height_needed: str
    keyword: str = "parachute"
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
    protects_against: set[str]
    needed_for: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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


def _hero_name(hero: Entity) -> str:
    return hero.id


def _title_case(name: str) -> str:
    return name


def _do_jump(world: World, hero: Entity, mission: Mission, narrate: bool = True) -> None:
    hero.meters["high"] += 1
    hero.memes["brave"] += 1
    if narrate:
        world.say(f"{hero.id} took a deep breath and looked down at the city street below.")


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    mission = world.facts.get("mission")
    gear = world.facts.get("gear")
    if not hero or not mission:
        return out
    h = world.get(hero.id)
    if h.meters["high"] < THRESHOLD:
        return out
    if gear and world.get(gear.id).worn_by == h.id:
        sig = ("fall", h.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        h.meters["safe"] += 1
        out.append(f"WHOOOSH! The parachute opened like a bright flower.")
    else:
        sig = ("crash", h.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        h.meters["hurt"] += 1
        out.append("THUMP! The leap was too big without the parachute.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    h = world.get(hero.id)
    if h.meters["safe"] >= THRESHOLD and ("relief", h.id) not in world.fired:
        world.fired.add(("relief", h.id))
        h.memes["joy"] += 1
        out.append(f"{h.id} grinned as the wind slowed to a gentle hum.")
    return out


CAUSAL_RULES = [_r_fall, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict(world: World, hero: Entity, mission: Mission, gear: Optional[Entity]) -> dict:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    if gear is not None:
        sim.get(gear.id).worn_by = sim_hero.id
    _do_jump(sim, sim_hero, mission, narrate=False)
    propagate(sim, narrate=False)
    return {
        "safe": bool(sim_hero.meters.get("safe", 0) >= THRESHOLD),
        "hurt": bool(sim_hero.meters.get("hurt", 0) >= THRESHOLD),
    }


def setup_flashback(world: World, hero: Entity, mentor: Entity, gear: Entity, mission: Mission) -> None:
    world.para()
    world.say(
        f"Flashback: yesterday, {hero.id} and {mentor.id} practiced on the school hill."
    )
    world.say(
        f"ZIP! The small {gear.label} snapped open in the breeze, and {mentor.id} said, "
        f'"A parachute catches air when you need a soft landing."'
    )
    world.say(
        f"{hero.id} remembered that lesson whenever the sky looked extra big."
    )


def tell(world: World, hero: Entity, mentor: Entity, gear: Entity, mission: Mission) -> World:
    world.facts["hero"] = hero
    world.facts["mentor"] = mentor
    world.facts["gear"] = gear
    world.facts["mission"] = mission

    world.say(
        f"{hero.id} was a little superhero who loved {mission.gerund} and helping the city."
    )
    world.say(
        f"On windy days, {hero.id} always listened for the sound of trouble: {mission.sound}."
    )
    world.say(
        f"That morning, {hero.id} spotted {mission.danger} near {world.setting.place}."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {mission.verb} right away, but the mission was high above the ground."
    )
    world.say(
        f"{hero.id} grabbed the {gear.label} and heard the little buckle go click."
    )

    setup_flashback(world, hero, mentor, gear, mission)

    world.para()
    world.say(
        f"Then {hero.id} climbed up, while the wind went {mission.sound} {mission.sound} {mission.sound}."
    )
    if hero.meters.get("high", 0) < THRESHOLD:
        _do_jump(world, hero, mission, narrate=False)
    gear.worn_by = hero.id
    world.say(
        f"{hero.id} whispered, 'Ready for takeoff!' and leaped from the ledge."
    )
    propagate(world, narrate=True)

    if hero.meters.get("safe", 0) >= THRESHOLD:
        world.para()
        world.say(
            f"Softly, {hero.id} floated down, landed with a tiny pat, and fixed {mission.danger} in a blink."
        )
        world.say(
            f"The city cheered, and {mentor.id} waved from below while the parachute fluttered like a flag."
        )
    else:
        world.para()
        world.say(
            f"{hero.id} needed help after the big leap, and {mentor.id} ran over fast."
        )

    world.facts["resolved"] = hero.meters.get("safe", 0) >= THRESHOLD
    return world


SETTINGS = {
    "rooftop": Setting(place="the tallest rooftop", height="high", affords={"jump"}),
    "tower": Setting(place="the clock tower", height="very high", affords={"jump"}),
    "bridge": Setting(place="the bridge overlook", height="high", affords={"jump"}),
}

MISSIONS = {
    "rescue": Mission(
        id="rescue",
        verb="save the kite",
        gerund="saving the kite",
        rush="zip toward the rooftop",
        danger="a tangled kite string",
        sound="whirr",
        height_needed="high",
        tags={"kite", "wind", "parachute"},
    ),
    "signal": Mission(
        id="signal",
        verb="reach the signal light",
        gerund="watching the signal light",
        rush="dash to the edge",
        danger="a blinking warning lamp",
        sound="whooo",
        height_needed="high",
        tags={"light", "wind", "parachute"},
    ),
}

GEAR = {
    "parachute": Gear(
        id="parachute",
        label="parachute",
        phrase="a bright parachute with red straps",
        protects_against={"fall"},
        needed_for={"jump"},
        prep="strap on the parachute first",
        tail="floated down as gently as a feather",
    ),
}

HERO_NAMES = ["Nova", "Bolt", "Skye", "Milo", "Zara", "Echo"]
MENTOR_NAMES = ["Captain Ray", "Aunt Star", "Coach Comet", "Guard Bright"]
TRAITS = ["brave", "quick", "cheerful", "curious", "steady"]


@dataclass
class StoryParams:
    place: str
    mission: str
    hero: str
    mentor: str
    trait: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for mission in MISSIONS:
            combos.append((place, mission))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a parachute and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--hero")
    ap.add_argument("--mentor")
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
    if getattr(args, "place", None) and getattr(args, "mission", None):
        if (getattr(args, "place", None), getattr(args, "mission", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission = rng.choice(choices)
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    mentor = getattr(args, "mentor", None) or rng.choice(MENTOR_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, hero=hero, mentor=mentor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type="boy" if params.hero in {"Bolt", "Milo"} else "girl"))
    hero.traits = [params.trait, "heroic"]
    mentor = world.add(Entity(id=params.mentor, kind="character", type="adult"))
    gear = world.add(Entity(id="parachute", type="parachute", label="parachute", phrase=GEAR["parachute"].phrase))
    mission = _safe_lookup(MISSIONS, params.mission)
    tell(world, hero, mentor, gear, mission)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mission = _safe_fact(world, f, "mission")
    return [
        f'Write a short superhero story for a young child that includes the word "{mission.keyword}".',
        f"Tell a bright story where {hero.id} remembers a lesson and uses a parachute to finish a high mission.",
        f"Write a story with a flashback, sound effects, and a happy landing for {hero.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mentor = _safe_fact(world, f, "mentor")
    mission = _safe_fact(world, f, "mission")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Why did {hero.id} need the parachute for this mission?",
            answer=f"{hero.id} needed the parachute because the mission was very high above the ground, and a normal jump would have been too risky.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered practicing on a hill with {mentor.id}, who explained that a parachute catches air and makes landing softer.",
        ),
        QAItem(
            question=f"What sound effects were heard when {hero.id} jumped?",
            answer=f"The story used sounds like {mission.sound} and WHOOOSH to show the windy jump and the parachute opening.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} landed safely, fixed the trouble, and ended the story feeling brave and happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parachute for?",
            answer="A parachute helps a person float down more slowly through the air so the landing is soft and safe.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that jumps back to something that happened earlier.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to make action feel lively, like wind rushing or gear clicking shut.",
        ),
    ]


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
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place(rooftop).
place(tower).
place(bridge).

mission(rescue).
mission(signal).

combo(P,M) :- place(P), mission(M).

#show combo/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MISSIONS:
        lines.append(asp.fact("mission", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/2."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="rooftop", mission="rescue", hero="Nova", mentor="Captain Ray", trait="brave"),
    StoryParams(place="tower", mission="signal", hero="Skye", mentor="Aunt Star", trait="steady"),
]


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
        print(asp_program("#show combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
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
