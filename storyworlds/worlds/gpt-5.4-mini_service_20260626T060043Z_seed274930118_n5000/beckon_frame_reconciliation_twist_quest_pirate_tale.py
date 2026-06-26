#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260626T060043Z_seed274930118_n5000/beckon_frame_reconciliation_twist_quest_pirate_tale.py
===========================================================================================================

A small pirate-tale storyworld with a quest, a twist, and a reconciliation.

Premise:
- A young pirate wants to chase a treasure quest at sea.
- A cherished frame holds the crew's map, and the captain worries it will be lost or damaged.
- A twist reveals the map is missing from the frame and the quest cannot begin safely.
- The crew resolves the tension by fixing the frame and making peace before sailing.

This world keeps the narrative child-facing and concrete:
- meters track physical state such as damage, seaworthiness, and readiness.
- memes track emotional state such as excitement, worry, stubbornness, and trust.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    map_frame: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "readiness": 0.0, "travel": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "joy": 0.0, "stubborn": 0.0, "trust": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain"}
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
    weather: str
    sea_state: str
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
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    twist: str
    goal: str
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
class Frame:
    id: str
    label: str
    phrase: str
    repair: str
    protective: bool = False
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
    quest: str
    frame: str
    place: str
    name: str
    gender: str
    captain: str
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
        self.facts: dict = {}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _pirate_pronoun(name: str) -> str:
    return name


def _wrap(text: str) -> str:
    return text[0].upper() + text[1:] if text else text


SETTINGS = {
    "harbor": Setting(place="the harbor", weather="windy", sea_state="calm", affords={"mapquest"}),
    "reef": Setting(place="the reef", weather="bright", sea_state="choppy", affords={"mapquest"}),
    "island": Setting(place="the island dock", weather="sunny", sea_state="calm", affords={"mapquest"}),
}

QUESTS = {
    "mapquest": Quest(
        id="mapquest",
        verb="go on the treasure quest",
        gerund="searching for treasure",
        rush="dash to the ship and set sail",
        risk="the sea could shake the frame and scatter the map",
        twist="the map was missing from the frame",
        goal="find the lost pearl",
        keyword="quest",
    ),
    "covequest": Quest(
        id="covequest",
        verb="follow the secret quest",
        gerund="following secret clues",
        rush="hurry to the cove and row out",
        risk="spray could splash the frame and blur the map",
        twist="the frame had been knocked crooked by a wave",
        goal="reach the hidden cove",
        keyword="quest",
    ),
}

FRAMES = {
    "oakframe": Frame(
        id="oakframe",
        label="oak frame",
        phrase="an old oak frame that held the map",
        repair="steady the frame with fresh rope",
    ),
    "brassframe": Frame(
        id="brassframe",
        label="brass frame",
        phrase="a shining brass frame with curled corners",
        repair="polish the frame and tighten its latch",
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Tess", "Ari", "Mina"]
BOY_NAMES = ["Finn", "Jory", "Pax", "Lenn", "Tobin"]
TRAITS = ["brave", "curious", "spirited", "stubborn", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for q in setting.affords:
            for frame_id in FRAMES:
                combos.append((q, frame_id))
    return combos


def explain_rejection(quest: Quest, frame: Frame) -> str:
    return f"(No story: this pirate quest needs a frame and a map to matter, but {frame.label} cannot support the loss or repair that makes the twist believable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with quest, twist, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--frame", choices=FRAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["mother", "father"])
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
    combos = [c for c in combos if getattr(args, "quest", None) is None or c[0] == getattr(args, "quest", None)]
    combos = [c for c in combos if getattr(args, "frame", None) is None or c[1] == getattr(args, "frame", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    quest_id, frame_id = rng.choice(combos)
    quest = _safe_lookup(QUESTS, quest_id)
    frame = _safe_lookup(FRAMES, frame_id)
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = getattr(args, "captain", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(quest=quest_id, frame=frame_id, place=place, name=name, gender=gender, captain=captain, trait=trait)


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    quest = _safe_lookup(QUESTS, params.quest)
    frame = _safe_lookup(FRAMES, params.frame)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"damage": 0.0, "readiness": 0.0, "travel": 0.0}, memes={"worry": 0.0, "joy": 0.0, "stubborn": 0.0, "trust": 0.0, "hope": 0.0}))
    captain = world.add(Entity(id="Captain", kind="character", type=params.captain, label=f"the {params.captain}"))
    map_frame = world.add(Entity(id="Frame", type="frame", label=frame.label, phrase=frame.phrase, caretaker=captain.id))
    map_frame.meters["damage"] = 0.0
    map_frame.meters["readiness"] = 1.0
    world.facts.update(hero=hero, captain=captain, frame=map_frame, quest=quest, params=params)
    return world


def predict_twist(world: World) -> dict:
    quest: Quest = _safe_fact(world, world.facts, "quest")
    frame: Entity = _safe_fact(world, world.facts, "frame")
    return {
        "twist": True,
        "damage": frame.meters["damage"] >= THRESHOLD,
        "missing_map": True,
        "readiness": frame.meters["readiness"] >= THRESHOLD,
        "risk": quest.risk,
    }


def generate_story(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    captain: Entity = _safe_fact(world, f, "captain")
    quest: Quest = _safe_fact(world, f, "quest")
    frame: Entity = _safe_fact(world, f, "frame")
    params: StoryParams = _safe_fact(world, f, "params")

    world.say(f"{hero.id} was a {params.trait} little {params.gender} pirate who loved {quest.gerund}.")
    world.say(f"{hero.id} liked the {frame.label} because it kept the map safe on the cabin wall.")
    world.say(f"One bright day at {world.setting.place}, {hero.id} heard the sea calling like a drum and wanted to {quest.verb}.")

    world.para()
    world.say(f"{hero.id} was ready to {quest.rush}, but {hero.pronoun('possessive')} {params.captain} held up a hand.")
    world.say(f'"{quest.risk}," said {captain.label}. "We should check the {frame.label} first."')

    twist = predict_twist(world)
    world.say(f"Then came the twist: {quest.twist}.")
    if twist["missing_map"]:
        world.say(f"The crew peered closer and saw that the map had slipped loose from the {frame.label}.")

    hero.memes["worry"] += 1
    hero.memes["stubborn"] += 1
    captain.memes["worry"] += 1

    world.para()
    world.say(f"{hero.id} frowned, then beckoned {captain.label} closer and pointed to the loose edge.")
    world.say(f"Together they chose to {frame.repair} before any sail was raised.")
    hero.memes["trust"] += 1
    captain.memes["trust"] += 1

    world.say(f"The captain and {hero.id} fixed the {frame.label}, and the map rested flat and neat again.")
    hero.memes["joy"] += 1
    hero.memes["hope"] += 1
    captain.memes["joy"] += 1
    hero.meters["readiness"] += 1
    frame.meters["damage"] = 0.0
    world.say(f"That made room for reconciliation, because the captain's warning had been kind and {hero.id} could see it now.")

    world.para()
    world.say(f"At last the crew smiled at one another, and {hero.id} was allowed to set off on the quest.")
    world.say(f"{_wrap(hero.id)} climbed aboard, {quest.gerund}, while the repaired {frame.label} stayed safe behind them.")
    world.say(f"The sea glittered ahead, and the little pirate sailed out with a clear heart and a steady map.")

    f["resolved"] = True
    f["twist_seen"] = True
    f["reconciled"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    quest: Quest = _safe_fact(world, f, "quest")
    frame: Entity = _safe_fact(world, f, "frame")
    return [
        f'Write a short pirate story for a child about a {hero.pronoun("subject")} who wants to {quest.verb} but needs a {frame.label}.',
        f'Create a gentle tale with the words "beckon" and "frame" where a pirate quest has a twist and ends in reconciliation.',
        f'Write a simple pirate adventure about {hero.id}, a broken or loose {frame.label}, and a safe way to begin the quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    captain: Entity = _safe_fact(world, f, "captain")
    quest: Quest = _safe_fact(world, f, "quest")
    frame: Entity = _safe_fact(world, f, "frame")
    params: StoryParams = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {quest.verb}. The day felt exciting, but the crew had to check the {frame.label} first.",
        ),
        QAItem(
            question=f"Why did {captain.label} pause the quest?",
            answer=f"{captain.label} paused the quest because {quest.risk}. That was why the captain looked closely at the {frame.label}.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {quest.twist}. Once the crew noticed that, they stopped and fixed the problem together.",
        ),
        QAItem(
            question=f"How did {hero.id} and {captain.label} make peace?",
            answer=f"They made peace by working together to {_safe_lookup(FRAMES, params.frame).repair}. After that, they could smile and begin the quest safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does beckon mean?",
            answer="To beckon means to signal someone with a hand or a nod so they come closer.",
        ),
        QAItem(
            question="What is a frame?",
            answer="A frame is a sturdy border that holds something in place, like a picture or a map.",
        ),
        QAItem(
            question="Why do sailors check their gear before leaving?",
            answer="Sailors check their gear before leaving so they can travel safely and avoid trouble at sea.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were worried or upset make peace and work together again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
quest(Q) :- quest_id(Q).
frame(F) :- frame_id(F).

needs_frame(Q,F) :- quest(Q), frame(F).
twist(Q) :- quest(Q).
reconcile(H,C) :- hero(H), captain(C).
valid_story(Place,Quest,Frame) :- setting(Place), quest(Quest), frame(Frame).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
        for q in _safe_lookup(SETTINGS, place).affords:
            lines.append(asp.fact("affords", place, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest_id", qid))
    for fid in FRAMES:
        lines.append(asp.fact("frame_id", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set((_safe_lookup(SETTINGS, p).place, q, f) for q, f in valid_combos() for p in SETTINGS if q in _safe_lookup(SETTINGS, p).affords)
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    generate_story(world)
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
    StoryParams(quest="mapquest", frame="oakframe", place="harbor", name="Mira", gender="girl", captain="mother", trait="brave"),
    StoryParams(quest="covequest", frame="brassframe", place="reef", name="Finn", gender="boy", captain="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
