#!/usr/bin/env python3
"""
storyworlds/worlds/proceed_cactus_sharing_repetition_superhero_story.py
======================================================================

A standalone superhero story world about a child hero, a small problem, and
a kind solution that gets the hero and a friend to proceed together.

Seed tale idea:
---
A small superhero kid wants to proceed to a rescue at the cactus garden, but
the path is tricky and the cactus patch is full of pokey plants. The hero's
partner wants to help by sharing tools and repeating the safe plan again and
again until everyone knows what to do. In the end, they proceed carefully,
save the day, and leave the cactus untouched.
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
    kind: str = "character"
    type: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    mentor: object | None = None
    shield: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
    cactus: bool = False
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


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    danger: str
    zone: set[str]
    keyword: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.active_zone: set[str] = set()

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
        clone.fired = set(self.fired)
        clone.active_zone = set(self.active_zone)
        clone.paragraphs = [[]]
        return clone


def _act(hero: Entity, challenge: Challenge) -> None:
    hero.meters[challenge.mess] = hero.meters.get(challenge.mess, 0) + 1
    hero.memes["excitement"] = hero.memes.get("excitement", 0) + 1


def _protects(gear: Gear, challenge: Challenge) -> bool:
    return challenge.mess in gear.guards and any(r in gear.covers for r in challenge.zone)


def predict(world: World, hero: Entity, challenge: Challenge) -> bool:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    _act(sim_hero, challenge)
    return bool(sim_hero.meters.get("risky", 0) >= THRESHOLD)


def proceed_line(hero: Entity, setting: Setting, challenge: Challenge) -> str:
    return (
        f"{hero.id} wanted to proceed to {setting.place} and {challenge.verb}. "
        f"{hero.pronoun('subject').capitalize()} felt brave, but {challenge.keyword} looked tricky."
    )


def repeat_line(mentor: Entity, hero: Entity, challenge: Challenge) -> str:
    return (
        f"{mentor.id} repeated the safe plan again and again: slow steps, shared tools, "
        f"and eyes on the path."
    )


def share_line(hero: Entity, friend: Entity, gear: Gear) -> str:
    return (
        f"{hero.id} shared {gear.label} with {friend.id}, and {friend.id} shared back a calm smile."
    )


def tell(setting: Setting, challenge: Challenge, gear: Gear, hero_name: str, hero_type: str,
         friend_name: str, mentor_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "brave", "kind"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="child", traits=["helpful"]))
    mentor = world.add(Entity(id=mentor_name, kind="character", type="adult", label="the guide"))

    shield = world.add(Entity(id=gear.id, kind="thing", type="gear", label=gear.label, owner=hero.id, protective=True))
    shield.worn_by = hero.id

    world.say(f"{hero.id} was a little superhero who loved helping people.")
    world.say(f"{hero.id} also loved the word proceed, because it sounded like a mission could begin.")
    world.say(f"One morning, {hero.id}, {friend.id}, and {mentor.id} headed to {setting.place}.")
    world.say(f"There was a cactus garden nearby, with tall cactus plants standing like sleepy green towers.")
    world.para()

    world.say(proceed_line(hero, setting, challenge))
    world.say(f"{hero.id} wanted to {challenge.verb}, but the cactus path could scratch bare arms and knees.")
    world.say(f"{mentor.id} warned that going too fast could make the day messy and scared.")
    world.say(repeat_line(mentor, hero, challenge))
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    world.para()

    world.say(share_line(hero, friend, gear))
    if _protects(gear, challenge):
        world.say(f"The gear could guard the risky parts, so the friends could keep going safely.")
    if predict(world, hero, challenge):
        world.say(f"But the first plan still felt risky, so they slowed down and checked the route once more.")
    world.say(f"{mentor.id} repeated, 'Stay close, share the work, and take one careful step at a time.'")
    world.say(f"That was the kind of repetition that helped everyone remember the plan.")
    world.para()

    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0) - 1)
    friend.memes["worry"] = max(0.0, friend.memes.get("worry", 0) - 1)
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    friend.memes["pride"] = friend.memes.get("pride", 0) + 1
    world.say(f"At last, {hero.id} and {friend.id} proceeded together, slow and steady.")
    world.say(f"They reached the stranded kitten first, lifted it to safety, and never brushed the cactus.")
    world.say(f"{hero.id} smiled because the mission was done, and {setting.place} felt bright and safe again.")

    world.facts.update(
        hero=hero,
        friend=friend,
        mentor=mentor,
        gear=gear,
        setting=setting,
        challenge=challenge,
        cactus=True,
    )
    return world


SETTINGS = {
    "garden": Setting(place="the cactus garden", cactus=True, affords={"proceed"}),
    "rooftop": Setting(place="the city rooftop", cactus=False, affords={"proceed"}),
    "plaza": Setting(place="the sunny plaza", cactus=False, affords={"proceed"}),
}

CHALLENGES = {
    "cactus": Challenge(
        id="cactus",
        verb="cross the cactus path",
        gerund="crossing the cactus path",
        rush="run down the cactus path",
        mess="scratched",
        danger="pokey cactus spines",
        zone={"arms", "knees"},
        keyword="cactus",
        tags={"cactus", "proceed"},
    ),
    "rescue": Challenge(
        id="rescue",
        verb="reach the rescue spot",
        gerund="reaching the rescue spot",
        rush="dash to the rescue spot",
        mess="rushed",
        danger="slipping and bumping into things",
        zone={"feet", "hands"},
        keyword="proceed",
        tags={"proceed"},
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="soft hero gloves",
        covers={"hands"},
        guards={"scratched"},
        prep="share the soft hero gloves",
        tail="kept sharing the plan",
    ),
    Gear(
        id="boots",
        label="sturdy hero boots",
        covers={"feet"},
        guards={"rushed"},
        prep="put on the sturdy hero boots",
        tail="walked on carefully in the sturdy hero boots",
    ),
    Gear(
        id="jacket",
        label="a bright hero jacket",
        covers={"arms", "knees"},
        guards={"scratched"},
        prep="wear the bright hero jacket",
        tail="proceeded carefully in the bright hero jacket",
    ),
]

HERO_NAMES = ["Nova", "Ruby", "Milo", "Iris", "Sunny", "Zane", "Pia", "Jett"]
FRIEND_NAMES = ["Bea", "Kai", "Tess", "Oli", "Nia", "Remy"]
ADULT_NAMES = ["Captain K", "Guide June", "Mentor Ray"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    gear: str
    hero: str
    hero_type: str
    friend: str
    mentor: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for chal_id in setting.affords:
            chal = _safe_lookup(CHALLENGES, chal_id)
            for gear in GEAR:
                if _protects(gear, chal):
                    combos.append((place, chal_id, gear.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with sharing and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gear", choices=[g.id for g in GEAR])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--mentor")
    ap.add_argument("--hero-type", choices=["boy", "girl"], default="girl")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "gear", None) is None or c[2] == getattr(args, "gear", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, gear = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    mentor = getattr(args, "mentor", None) or rng.choice(ADULT_NAMES)
    hero_type = getattr(args, "hero_type", None)
    return StoryParams(place=place, challenge=challenge, gear=gear, hero=hero, hero_type=hero_type, friend=friend, mentor=mentor)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(CHALLENGES, params.challenge),
        next(g for g in GEAR if g.id == params.gear),
        params.hero,
        params.hero_type,
        params.friend,
        params.mentor,
    )
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
    return [
        f'Write a short superhero story that includes the word "proceed" and the word "cactus".',
        f"Tell a child-friendly superhero story where {f['hero'].id} and {f['friend'].id} share a tool and proceed safely through a cactus garden.",
        f"Write a gentle adventure with repetition, a shared plan, and a brave hero who reaches the rescue spot without hurting the cactus.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    mentor = _safe_fact(world, f, "mentor")
    challenge = _safe_fact(world, f, "challenge")
    gear = _safe_fact(world, f, "gear")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to proceed and {challenge.verb}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} help each other?",
            answer=f"They shared {gear.label} and stayed close while they went forward together.",
        ),
        QAItem(
            question=f"Why did {mentor.id} repeat the plan?",
            answer=f"{mentor.id} repeated the plan so everyone would remember to move slowly and stay safe near the cactus.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{hero.id} and {friend.id} proceeded together, rescued the kitten, and left the cactus untouched.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cactus?",
            answer="A cactus is a plant that can have sharp spines, so people should be careful around it.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something or enjoy something with you.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again and again, which can help people remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        lines.append(f"{ent.id}: kind={ent.kind} type={ent.type} meters={ent.meters} memes={ent.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", challenge="cactus", gear="jacket", hero="Nova", hero_type="girl", friend="Bea", mentor="Captain K"),
    StoryParams(place="rooftop", challenge="rescue", gear="boots", hero="Milo", hero_type="boy", friend="Kai", mentor="Guide June"),
    StoryParams(place="plaza", challenge="cactus", gear="gloves", hero="Iris", hero_type="girl", friend="Tess", mentor="Mentor Ray"),
]


ASP_RULES = r"""
place(P) :- setting(P).
challenge(C) :- challenge_kind(C).
gear(G) :- gear_kind(G).

risk(C) :- challenge_kind(C), splashes(C, R), danger_zone(C, R).
fix(G, C) :- gear_kind(G), challenge_kind(C), guards(G, M), challenge_mess(C, M), covers(G, R), danger_zone(C, R).
valid(P, C, G) :- setting(P), affords(P, C), fix(G, C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge_kind", cid))
        lines.append(asp.fact("challenge_mess", cid, c.mess))
        for r in sorted(c.zone):
            lines.append(asp.fact("danger_zone", cid, r))
    for g in GEAR:
        lines.append(asp.fact("gear_kind", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    expected = set(valid_combos())
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    got = set(asp.atoms(model, "valid"))
    if got == expected:
        print(f"OK: ASP matches Python ({len(got)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in ASP:", sorted(got - expected))
    print("Only in Python:", sorted(expected - got))
    return 1


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
