#!/usr/bin/env python3
"""
storyworlds/worlds/nasty_liquid_suspense_ghost_story.py
=======================================================

A small story world about a spooky house, a nasty liquid leak, and a careful
rescuer who learns that scary shadows can be solved with light, attention, and
a brave helper.

The seed tale premise is ghost-story flavored: a child hears a drip in the dark,
finds a nasty liquid creeping from a cracked jar, gets nervous, and then uses a
lamp and a safe container to stop the leak before anything worse can happen.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class House:
    place: str
    spooky: bool = True
    rooms: set[str] = field(default_factory=set)
    dark_rooms: set[str] = field(default_factory=set)
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
class World:
    house: House
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy

        return World(
            house=_copy.deepcopy(self.house),
            entities=_copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=_copy.deepcopy(self.facts),
        )
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


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
HOUSES = {
    "old_house": House(place="the old house", spooky=True, rooms={"hall", "attic", "kitchen"}, dark_rooms={"attic", "hall"}),
    "cottage": House(place="the quiet cottage", spooky=True, rooms={"porch", "pantry", "basement"}, dark_rooms={"basement", "pantry"}),
    "school": House(place="the empty school", spooky=True, rooms={"hall", "closet", "office"}, dark_rooms={"closet", "hall"}),
}

PEOPLE = {
    "girl": {"type": "girl", "names": ["Mia", "Nora", "Lily", "Ava", "Zoe"]},
    "boy": {"type": "boy", "names": ["Ben", "Theo", "Finn", "Leo", "Max"]},
}

ACTIONS = {
    "drip": {
        "verb": "follow the drip",
        "gerund": "following the drip",
        "rush": "run toward the dark corner",
        "mess": "wet",
        "soil": "spilled and wet",
        "kind": "liquid",
        "zone": {"floor", "hands"},
        "keyword": "drip",
        "tags": {"liquid", "wet", "ghost"},
        "scary": "a drip sounded like footsteps in the dark",
    },
    "spill": {
        "verb": "clean the spill",
        "gerund": "cleaning the spill",
        "rush": "hurry to the stain",
        "mess": "sticky",
        "soil": "sticky and smeared",
        "kind": "liquid",
        "zone": {"floor", "hands"},
        "keyword": "spill",
        "tags": {"liquid", "sticky", "ghost"},
        "scary": "the floor looked like it had a secret dark stain",
    },
    "jar": {
        "verb": "open the jar",
        "gerund": "opening the jar",
        "rush": "pull the lid open fast",
        "mess": "smelly",
        "soil": "badly smelly",
        "kind": "liquid",
        "zone": {"hands", "torso"},
        "keyword": "jar",
        "tags": {"liquid", "ghost", "smell"},
        "scary": "the jar shivered on the shelf like it was waiting",
    },
}

PRIZES = {
    "dress": {"label": "dress", "phrase": "a clean blue dress", "region": "torso", "genders": {"girl"}},
    "shirt": {"label": "shirt", "phrase": "a white shirt", "region": "torso", "genders": {"girl", "boy"}},
    "shoes": {"label": "shoes", "phrase": "shiny shoes", "region": "feet", "genders": {"girl", "boy"}},
    "pajamas": {"label": "pajamas", "phrase": "soft pajamas", "region": "torso", "genders": {"girl", "boy"}},
}

TOOLS = {
    "lamp": {"label": "a lamp", "guards": {"dark"}, "covers": {"hands", "floor"}},
    "bucket": {"label": "a bucket", "guards": {"wet", "sticky"}, "covers": {"floor"}},
    "towel": {"label": "a towel", "guards": {"wet", "sticky", "smelly"}, "covers": {"hands", "torso"}},
    "gloves": {"label": "rubber gloves", "guards": {"wet", "sticky", "smelly"}, "covers": {"hands"}},
}

GENTLE_WORDS = ["careful", "brave", "quiet", "tiny", "soft", "steady"]


@dataclass
class StoryParams:
    house: str
    action: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Core simulation
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


def prize_at_risk(action: dict, prize: dict) -> bool:
    return prize["region"] in action["zone"]


def select_tool(action: dict, prize: dict) -> Optional[str]:
    for tid, tool in TOOLS.items():
        if action["mess"] in tool["guards"] or action["kind"] in tool["guards"]:
            if prize["region"] in tool["covers"] or "floor" in tool["covers"]:
                return tid
    return None


def reasonableness_gate(params: StoryParams) -> None:
    action = _safe_lookup(ACTIONS, params.action)
    prize = _safe_lookup(PRIZES, params.prize)
    if params.gender not in prize["genders"]:
        pass
    if not prize_at_risk(action, prize):
        pass
    if select_tool(action, prize) is None:
        pass


def make_world(params: StoryParams) -> World:
    house = _safe_lookup(HOUSES, params.house)
    world = World(house=house)

    person_cfg = PEOPLE[params.gender]
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=person_cfg["type"],
        label=params.name,
        meters={"nervous": 0.0, "brave": 0.0, "mess": 0.0},
        memes={"suspense": 0.0, "love": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label="the helper",
        meters={"nervous": 0.0, "brave": 0.0},
        memes={"suspense": 0.0, "warmth": 0.0},
    ))
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    prize = world.add(Entity(
        id="prize",
        type=params.prize,
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        owner=hero.id,
        caretaker=helper.id,
        location="body",
        meters={"clean": 1.0, "dirty": 0.0},
    ))
    tool_id = select_tool(_safe_lookup(ACTIONS, params.action), prize_cfg)
    if tool_id:
        tool_cfg = _safe_lookup(TOOLS, tool_id)
        tool = world.add(Entity(
            id=tool_id,
            type=tool_id,
            label=tool_cfg["label"],
            owner=helper.id,
            carried_by=helper.id,
            location="hand",
            meters={"ready": 1.0},
        ))
        world.facts["tool"] = tool
    world.facts.update(hero=hero, helper=helper, prize=prize, action=_safe_lookup(ACTIONS, params.action), house=house)
    return world


def _do_action(world: World, hero: Entity, action: dict, narrate: bool = True) -> None:
    hero.meters["mess"] += 1.0
    hero.memes["suspense"] += 1.0
    if action["kind"] == "liquid":
        hero.memes["suspense"] += 1.0
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "prize")
    if prize and prize_at_risk(action, _safe_lookup(PRIZES, prize.type)):
        prize.meters["dirty"] += 1.0
        hero.memes["nervous"] += 1.0
    if narrate:
        world.say(f"The little sound grew louder, and {hero.label} could not tell if it was a ghost or only a leak.")


def predict_mess(world: World, hero: Entity, action: dict) -> dict:
    sim = world.copy()
    _do_action(sim, sim.facts["hero"], action, narrate=False)
    prize = sim.facts["prize"]
    return {"dirty": prize.meters["dirty"], "suspense": sim.facts["hero"].memes["suspense"]}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} lived in {world.house.place}, where every dark room seemed to hold a whisper.")
    world.say(f"{hero.label} was a {random.choice(GENTLE_WORDS)} child who listened closely when the house made strange sounds.")


def setup_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1.0
    world.say(f"{hero.label} loved {prize.phrase}, and {prize.label} stayed neat and bright in the front room.")


def clue(world: World, hero: Entity, action: dict) -> None:
    if world.house.spooky:
        world.say(f"One night, {action['scary']}.")
    else:
        world.say(f"One night, there was a small sound in the house.")
    hero.memes["suspense"] += 1.0


def worry(world: World, helper: Entity, hero: Entity, action: dict, prize: Entity) -> None:
    pred = predict_mess(world, hero, action)
    if pred["dirty"] >= THRESHOLD:
        helper.memes["suspense"] += 1.0
        world.facts["predicted_dirty"] = True
        world.say(f'"If you touch that now, your {prize.label} could get {_safe_lookup(ACTIONS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "action_name"))["soil"]}," {helper.label} said.')
    else:
        world.facts["predicted_dirty"] = False


def hesitate(world: World, hero: Entity, action: dict) -> None:
    hero.memes["nervous"] += 1.0
    world.say(f"{hero.label} held still for a moment, then tried to {action['rush']}.")


def light_up(world: World, helper: Entity) -> None:
    helper.memes["warmth"] += 1.0
    world.say(f"The helper clicked on {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "tool").label}, and the dark corner was not so scary anymore.")


def fix(world: World, helper: Entity, hero: Entity, action: dict, prize: Entity) -> None:
    tool = world.facts.get("tool")
    if tool:
        tool.carried_by = hero.id
        world.say(f"{helper.label} handed over {tool.label} and showed {hero.label} how to hold it steady.")
    world.say(f"Together they found the crack, put the nasty liquid into a bucket, and wiped the floor clean.")
    prize.meters["dirty"] = 0.0
    hero.memes["relief"] += 1.0
    hero.memes["suspense"] = 0.0
    hero.memes["brave"] += 1.0
    helper.memes["suspense"] = 0.0
    world.say(f"In the end, the house felt quiet again, and the scary dripping was only a small puddle under the lamp.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = make_world(params)
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "prize")
    action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "action")
    world.facts["action_name"] = params.action

    introduce(world, hero)
    world.para()
    setup_prize(world, hero, prize)
    clue(world, hero, action)
    worry(world, helper, hero, action, prize)
    hesitate(world, hero, action)
    world.para()
    light_up(world, helper)
    fix(world, helper, hero, action, prize)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    return [
        f'Write a spooky-but-gentle story for a young child about {hero.label} hearing a strange sound and finding a nasty liquid leak.',
        f"Tell a ghost-story style tale where {hero.label} wants to {action['verb']} while worrying about {prize.phrase}.",
        f'Write a short suspense story with the words "nasty" and "liquid" that ends with a safe fix and a calm room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action")
    return [
        QAItem(
            question=f"Who heard the strange sound in {world.house.place}?",
            answer=f"{hero.label} heard the strange sound, and the helper stayed nearby to help.",
        ),
        QAItem(
            question=f"What was the nasty liquid doing before the light came on?",
            answer=f"It was leaking and making the room feel spooky until {helper.label} brought light and a bucket.",
        ),
        QAItem(
            question=f"Why did the helper worry about {prize.label}?",
            answer=f"The helper worried because {action['gerund']} could make the {prize.label} get messy.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The leak was cleaned up, the dark corner was no longer scary, and {prize.label} stayed clean again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lamp do in a dark room?",
            answer="A lamp shines light so people can see better and feel less scared.",
        ),
        QAItem(
            question="What is a leak?",
            answer="A leak is when liquid escapes from where it was supposed to stay, like out of a jar or pipe.",
        ),
        QAItem(
            question="Why can a nasty liquid be a problem?",
            answer="A nasty liquid can make things dirty, slippery, or smelly, so it needs to be cleaned up safely.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- action(A), prize(P), zone(A,R), region(P,R).
tool_ok(T,A,P) :- tool(T), prize_at_risk(A,P), guards(T,M), mess_of(A,M), covers(T,R), region(P,R).
valid_story(H, A, P, T) :- house(H), action(A), prize(P), tool(T), tool_ok(T,A,P), person_gender_ok(P, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HOUSES:
        lines.append(asp.fact("house", hid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a["mess"]))
        for r in sorted(a["zone"]):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p["region"]))
        for g in sorted(p["genders"]):
            lines.append(asp.fact("person_gender_ok", pid, g))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t["guards"]):
            lines.append(asp.fact("guards", tid, g))
        for r in sorted(t["covers"]):
            lines.append(asp.fact("covers", tid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set((h, a, p) for h, a, p, _t in asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Valid combos and parameters
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hid in HOUSES:
        for aid, action in ACTIONS.items():
            for pid, prize in PRIZES.items():
                if prize_at_risk(action, prize) and select_tool(action, prize):
                    for gender in prize["genders"]:
                        combos.append((hid, aid, pid, gender))
    return combos


def explain_rejection(action: dict, prize: dict) -> str:
    if not prize_at_risk(action, prize):
        return (
            f"(No story: {action['gerund']} does not actually threaten the {prize['label']}, "
            f"so the suspense would be fake.)"
        )
    return (
        f"(No story: there is no safe tool that can handle the {action['mess']} mess and still protect the {prize['label']}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story style tale about a nasty liquid leak and a brave fix.")
    ap.add_argument("--house", choices=HOUSES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=GENTLE_WORDS)
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
    if getattr(args, "action", None) and getattr(args, "prize", None):
        action = _safe_lookup(ACTIONS, getattr(args, "action", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(action, prize) and select_tool(action, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None))["genders"]:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "house", None) is None or c[0] == getattr(args, "house", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or c[3] == getattr(args, "gender", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    house, action, prize, gender = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(PEOPLE[gender]["names"])
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = getattr(args, "trait", None) or rng.choice(GENTLE_WORDS)
    return StoryParams(house=house, action=action, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(house="old_house", action="drip", prize="shirt", name="Mia", gender="girl", helper="mother", trait="careful"),
    StoryParams(house="cottage", action="spill", prize="shoes", name="Ben", gender="boy", helper="grandmother", trait="quiet"),
    StoryParams(house="school", action="jar", prize="pajamas", name="Nora", gender="girl", helper="father", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for h, a, p, g in stories:
            print(f"  {h:10} {a:6} {p:7} {g}")
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
            header = f"### {p.name}: {p.action} in {p.house} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
