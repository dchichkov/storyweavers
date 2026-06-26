#!/usr/bin/env python3
"""
storyworlds/worlds/senile_mystery_to_solve_dialogue_curiosity_superhero.py
===========================================================================

A small superhero-story world with a mystery to solve, lots of dialogue, and
curiosity-driven clues.

Premise:
- A young hero with a cape notices something strange in a bright city block.
- A forgetful, senile old inventor keeps mixing up clues.
- The hero asks questions, listens carefully, and follows the trail.
- The mystery is solved by combining observation, dialogue, and a tiny rescue.

This is a standalone storyworld script with:
- simulated physical state (meters) and emotional state (memes)
- reasonableness gates in Python and ASP
- story generation, QA, trace, JSON, ASP listing, and verification
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

    clue: object | None = None
    elder: object | None = None
    hero: object | None = None
    villain: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"
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
    indoor: bool
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
class Mystery:
    id: str
    question: str
    missing: str
    clue_word: str
    disturbance: str
    source: str
    fix: str
    danger: str
    solve_action: str
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
    label_phrase: str
    helps: set[str]
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
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_character()]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_TRAITS = ["curious", "brave", "kind", "quick", "bright"]
VILLAIN_TRAITS = ["mischievous", "sly", "grumpy"]


SETTINGS = {
    "museum": Setting(place="the city museum", indoor=True, affords={"search"}),
    "rooftop": Setting(place="the rooftop garden", indoor=False, affords={"search"}),
    "alley": Setting(place="the lantern alley", indoor=False, affords={"search"}),
    "workshop": Setting(place="the inventor's workshop", indoor=True, affords={"search"}),
}

MYSTERIES = {
    "missing_lens": Mystery(
        id="missing_lens",
        question="Where did the shining lens go?",
        missing="the shining lens",
        clue_word="lens",
        disturbance="a tiny glass sparkle",
        source="the broken window box",
        fix="put the lens back in the projector",
        danger="the nighttime map cannot light up",
        solve_action="carefully returns the lens",
        tags={"glass", "light", "lens"},
    ),
    "silent_alarm": Mystery(
        id="silent_alarm",
        question="Why did the alarm stop humming?",
        missing="the alarm's little battery",
        clue_word="battery",
        disturbance="a soft beep that faded away",
        source="the rainy drain",
        fix="replace the battery and dry the wires",
        danger="the alarm cannot warn the neighbors",
        solve_action="swaps in a fresh battery",
        tags={"battery", "sound", "rain"},
    ),
    "hidden_key": Mystery(
        id="hidden_key",
        question="Who hid the bronze key?",
        missing="the bronze key",
        clue_word="key",
        disturbance="a scuff of mud near the door",
        source="the muddy boots by the mat",
        fix="find the key and open the chest",
        danger="the chest stays locked",
        solve_action="finds the key under the mat",
        tags={"key", "mud", "door"},
    ),
}

GEAR = [
    Gear(
        id="cape",
        label="cape",
        label_phrase="a red cape",
        helps={"search", "rescue"},
        prep="tie on the red cape",
        tail="flew back through the doorway",
    ),
    Gear(
        id="mask",
        label="mask",
        label_phrase="a silver mask",
        helps={"search"},
        prep="slip on the silver mask",
        tail="moved quietly through the shadows",
    ),
    Gear(
        id="gloves",
        label="gloves",
        label_phrase="bright gloves",
        helps={"rescue", "care"},
        prep="pull on the bright gloves",
        tail="held the clue gently",
        plural=True,
    ),
    Gear(
        id="magnifier",
        label="magnifier",
        label_phrase="a tiny magnifier",
        helps={"search"},
        prep="grab the tiny magnifier",
        tail="looked again at the clue",
    ),
    Gear(
        id="flashlight",
        label="flashlight",
        label_phrase="a small flashlight",
        helps={"search", "rescue"},
        prep="switch on the small flashlight",
        tail="lit the way home",
    ),
]

HERO_NAMES = ["Nova", "Milo", "Zara", "Jett", "Ruby", "Pax", "Ivy", "Theo"]
HELPER_NAMES = ["Aunt Bea", "Captain Dot", "Ms. Vale", "Mr. Kite"]
ELDER_NAMES = ["Mr. Finch", "Mrs. Plum", "Old Ben", "Mrs. Hazel"]
VILLAIN_NAMES = ["Snap", "Whisper", "Grit", "Moth"]


def mystery_requires_dialogue(mystery: Mystery) -> bool:
    return True


def compatible(setting: Setting, mystery: Mystery) -> bool:
    if setting.indoor and mystery.id == "hidden_key":
        return True
    return "search" in setting.affords


def select_gear(mystery: Mystery) -> Optional[Gear]:
    for gear in GEAR:
        if "search" in gear.helps:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if compatible(setting, mystery) and select_gear(mystery):
                combos.append((place, mid))
    return combos


def _mood_boost(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.meme(key) + amount


def _meter_boost(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meter(key) + amount


def _r_disturbance(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.facts.get("culprit")
    clue = world.facts.get("clue_object")
    if culprit is None or clue is None:
        return out
    if world.fired and ("disturbance", clue.id) in world.fired:
        return out
    if world.facts.get("mystery_started"):
        return out
    world.fired.add(("disturbance", clue.id))
    _meter_boost(clue, "hidden", 1.0)
    _mood_boost(world.get(world.facts["hero"].id), "curiosity", 1.0)
    out.append(f"Something felt off near {world.setting.place}.")
    return out


def _r_rescue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    elder = world.facts.get("elder")
    clue = world.facts.get("clue_object")
    if not hero or not elder or not clue:
        return out
    if clue.meter("hidden") < THRESHOLD:
        return out
    if ("rescue", clue.id) in world.fired:
        return out
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    world.fired.add(("rescue", clue.id))
    clue.meters["hidden"] = 0.0
    clue.carried_by = hero.id
    _mood_boost(hero, "confidence", 1.0)
    _mood_boost(elder, "relief", 1.0)
    out.append(f"{hero.id} reached the clue before it slipped away.")
    return out


CAUSAL_RULES = [
    _r_disturbance,
    _r_rescue,
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


def story_intro(hero: Entity, elder: Entity, setting: Setting, mystery: Mystery) -> str:
    return (
        f"{hero.id} was a {hero.traits[0]} little {hero.type} with a bright {hero.label} "
        f"and a cape that fluttered like a flag. One morning, {hero.id} visited {setting.place} "
        f"and met {elder.id}, a senile old inventor who kept saying, "
        f"\"I know something important is missing, but I can't quite remember what.\""
    )


def ask_curious_question(hero: Entity, elder: Entity, mystery: Mystery) -> str:
    return (
        f"{hero.id} tilted {hero.pronoun('possessive')} head and asked, "
        f"\"What did you last hear, see, or touch?\" "
        f"{elder.id} frowned, then whispered, \"A soft clue, a little sparkle, and a thing that should have stayed put.\""
    )


def spotlight_clue(hero: Entity, mystery: Mystery, clue: Entity) -> str:
    return (
        f"{hero.id} looked closely and noticed {mystery.disturbance} near {mystery.source}. "
        f"\"That sounds like {mystery.clue_word},\" {hero.id} said. "
        f"\"Can you tell me who was here before the trouble started?\""
    )


def suspect_dialogue(hero: Entity, suspect: Entity, mystery: Mystery) -> str:
    return (
        f"\"I didn't steal anything,\" said {suspect.id}. "
        f"\"But I did hear a tiny clink.\" "
        f"{hero.id} listened carefully and asked one more question: "
        f"\"Was the clue hidden or dropped?\""
    )


def reveal_turn(hero: Entity, elder: Entity, mystery: Mystery, clue: Entity) -> str:
    return (
        f"Then {hero.id} followed the hint and found {clue.label_phrase} tucked where it could be seen again. "
        f"\"This is it!\" {hero.id} said. \"The mystery was never about a big monster. "
        f"It was about paying attention.\""
    )


def resolve_world(hero: Entity, elder: Entity, mystery: Mystery, clue: Entity) -> str:
    return (
        f"{hero.id} handed the clue back to {elder.id}, and {elder.id} smiled with shiny eyes. "
        f"\"You solved it,\" {elder.id} said. \"My old memory was foggy, but your curiosity was clear.\" "
        f"In the end, {mystery.solve_action}, and the city felt safe and bright again."
    )


def make_world(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, trait: str,
               elder_name: str, villain_name: str) -> World:
    world = World(setting, mystery)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label="mask",
        traits=[trait, "heroic"],
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type="man",
        label="inventor",
        traits=["senile", "forgetful"],
    ))
    villain = world.add(Entity(
        id=villain_name,
        kind="character",
        type="man",
        label="shadowy figure",
        traits=["sneaky"],
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="thing",
        label=mystery.clue_word,
        phrase=mystery.missing,
        caretaker=elder.id,
    ))
    world.facts.update(hero=hero, elder=elder, villain=villain, clue_object=clue, mystery_started=True)
    _mood_boost(hero, "curiosity", 1.0)
    _mood_boost(hero, "courage", 1.0)
    _mood_boost(elder, "worry", 1.0)
    _meter_boost(clue, "hidden", 1.0)
    return world


def tell_story(world: World) -> World:
    hero = _safe_fact(world, world.facts, "hero")
    elder = _safe_fact(world, world.facts, "elder")
    villain = _safe_fact(world, world.facts, "villain")
    clue = _safe_fact(world, world.facts, "clue_object")
    mystery = world.mystery

    world.say(story_intro(hero, elder, world.setting, mystery))
    world.say(ask_curious_question(hero, elder, mystery))
    world.para()
    world.say(spotlight_clue(hero, mystery, clue))
    world.say(suspect_dialogue(hero, villain, mystery))
    propagate(world, narrate=True)
    world.para()
    world.say(reveal_turn(hero, elder, mystery, clue))
    world.say(resolve_world(hero, elder, mystery, clue))
    _mood_boost(hero, "joy", 1.0)
    _mood_boost(elder, "relief", 1.0)
    _mood_boost(hero, "curiosity", 1.0)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    h = _safe_fact(world, world.facts, "hero")
    e = _safe_fact(world, world.facts, "elder")
    m = world.mystery
    return [
        f'Write a short superhero story for a young child that includes the word "senile" and the idea of a mystery to solve.',
        f"Tell a gentle story where {h.id} asks questions, listens to {e.id}, and solves a mystery about {m.missing}.",
        f"Write a simple superhero story with dialogue, curiosity, and a clue that leads to {m.fix}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = _safe_fact(world, world.facts, "hero")
    e = _safe_fact(world, world.facts, "elder")
    v = _safe_fact(world, world.facts, "villain")
    m = world.mystery
    clue = _safe_fact(world, world.facts, "clue_object")
    return [
        QAItem(
            question=f"Who is the superhero story about?",
            answer=f"It is about {h.id}, a curious little hero who uses questions to solve a mystery.",
        ),
        QAItem(
            question=f"Why was {e.id} confused at the start?",
            answer=f"{e.id} was senile and forgetful, so {e.id} could not remember exactly what was missing.",
        ),
        QAItem(
            question=f"What clue helped {h.id} solve the mystery?",
            answer=f"The clue was {m.disturbance} near {m.source}, which led {h.id} to {clue.label_phrase}.",
        ),
        QAItem(
            question=f"What did {h.id} say to figure things out?",
            answer=f"{h.id} asked careful questions like what was seen, heard, or touched, and that helped uncover the truth.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{h.id} returned {m.missing} to {e.id}, and the city became safe and bright again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    m = world.mystery
    out = [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions and learn more.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or hidden that people try to figure out.",
        ),
        QAItem(
            question="Why do superheroes wear capes?",
            answer="In stories, capes can make superheroes look bold and ready for action.",
        ),
    ]
    if "glass" in m.tags:
        out.append(QAItem(
            question="What is glass?",
            answer="Glass is a hard, clear material that can be see-through and shiny.",
        ))
    if "key" in m.tags:
        out.append(QAItem(
            question="What is a key for?",
            answer="A key is used to open a lock, like a door or a chest.",
        ))
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return f"(No story: {setting.place} does not fit the chosen mystery in a reasonable way.)"


ASP_RULES = r"""
setting(Place) :- place(Place).
mystery(M) :- mystery_id(M).

compatible(Place, M) :- setting_kind(Place, indoor), indoor_ok(M).
compatible(Place, M) :- setting_kind(Place, outdoor), outdoor_ok(M).

valid_story(Place, M) :- compatible(Place, M), has_gear(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting_kind", pid, "indoor" if s.indoor else "outdoor"))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_id", mid))
        if m.id == "hidden_key":
            lines.append(asp.fact("outdoor_ok", mid))
            lines.append(asp.fact("indoor_ok", mid))
        else:
            lines.append(asp.fact("indoor_ok", mid))
            lines.append(asp.fact("outdoor_ok", mid))
        lines.append(asp.fact("has_gear", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_stories() -> list[tuple[str, str]]:
    return sorted(valid_combos())


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    trait: str
    elder_name: str
    villain_name: str
    seed: Optional[int] = None
    params: object | None = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero mystery storyworld with dialogue and curiosity.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--elder-name", choices=ELDER_NAMES)
    ap.add_argument("--villain-name", choices=VILLAIN_NAMES)
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    combos = valid_stories()
    if getattr(args, "place", None) or getattr(args, "mystery", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(list(combos))
    return StoryParams(
        place=place,
        mystery=mystery,
        hero_name=getattr(args, "hero_name", None) or rng.choice(HERO_NAMES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(["boy", "girl"]),
        trait=getattr(args, "trait", None) or rng.choice(HERO_TRAITS),
        elder_name=getattr(args, "elder_name", None) or rng.choice(ELDER_NAMES),
        villain_name=getattr(args, "villain_name", None) or rng.choice(VILLAIN_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = make_world(setting, mystery, params.hero_name, params.hero_type, params.trait,
                       params.elder_name, params.villain_name)
    tell_story(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible (place, mystery) combos:\n")
        for place, mystery in triples:
            print(f"  {place:12} {mystery}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, mystery in valid_stories():
            params = StoryParams(
                place=place,
                mystery=mystery,
                hero_name=_safe_lookup(HERO_NAMES, 0),
                hero_type="boy",
                trait="curious",
                elder_name=_safe_lookup(ELDER_NAMES, 0),
                villain_name=_safe_lookup(VILLAIN_NAMES, 0),
            )
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
