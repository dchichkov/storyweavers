#!/usr/bin/env python3
"""
Storyworld: eagle_quest_repetition_space_adventure

A small, self-contained TinyStories-style world about a space quest with an
eagle companion, a repeating signal, and a child-friendly adventure among the
stars.

Premise:
- A young pilot wants to fly a small ship to deliver a glowing star seed.
- An eagle companion spots a distant moon-cave marked by a repeating beacon.

Tension:
- The beacon loops in the same pattern, and the pilot keeps missing the right
  path.
- A drifting dust ring can knock the ship off course if they rush.

Turn:
- The eagle notices the repetition has a rhythm and counts it aloud.
- The pilot follows the beat, which reveals the safe route through the stars.

Resolution:
- They reach the moon-cave, place the star seed in a nest of light, and the
  repeating beacon becomes a guiding song instead of a puzzle.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "pilot"}
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
    is_space: bool = True
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
    keyword: str
    rhythm: str
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
    label: str
    phrase: str
    type: str
    location: str
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
class Guide:
    id: str
    label: str
    clue: str
    method: str
    helps: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.threat: str = ""

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
        clone.threat = self.threat
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

SETTINGS = {
    "orbital_station": Setting(place="the orbital station", affords={"quest"}),
    "moon_outpost": Setting(place="the moon outpost", affords={"quest"}),
    "starlit_cave": Setting(place="the starlit cave", affords={"quest"}),
}

QUESTS = {
    "signal": Quest(
        id="signal",
        verb="follow the beacon",
        gerund="following the beacon",
        rush="dash toward the beacon",
        keyword="beacon",
        rhythm="beep-beep, beep-beep",
        tags={"beacon", "repeat"},
    ),
    "trail": Quest(
        id="trail",
        verb="track the comet trail",
        gerund="tracking the comet trail",
        rush="chase the trail",
        keyword="trail",
        rhythm="whoosh, whoosh, whoosh",
        tags={"trail", "repeat"},
    ),
}

PRIZES = {
    "star_seed": Prize(
        label="star seed",
        phrase="a glowing star seed",
        type="seed",
        location="satchel",
    ),
    "map_chip": Prize(
        label="map chip",
        phrase="a silver map chip",
        type="chip",
        location="pocket",
    ),
}

GUIDES = {
    "eagle": Guide(
        id="eagle",
        label="eagle",
        clue="an eagle made of bright feathers and engine light",
        method="count the repeating signal",
        helps={"signal", "trail"},
    ),
}

NAMES = ["Ari", "Mina", "Tavi", "Lio", "Nora", "Eli"]
TRAITS = ["brave", "curious", "careful", "bright", "patient"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning
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


def quest_is_reasonable(quest: Quest, prize: Prize) -> bool:
    return quest.id == "signal" and prize.label == "star seed" or quest.id == "trail" and prize.label == "map chip"


def quest_needs_guide(quest: Quest) -> bool:
    return True


def select_guide(quest: Quest) -> Optional[Guide]:
    for g in GUIDES.values():
        if quest.id in g.helps:
            return g
    return None


def predict(world: World, hero: Entity, quest: Quest, prize: Entity) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    danger = sim.facts.get("drift", False)
    lost = sim.facts.get("lost", False)
    return {"danger": danger, "lost": lost, "repeated": True}


# ---------------------------------------------------------------------------
# Narrative actions
# ---------------------------------------------------------------------------

def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    world.facts["repeated"] = world.facts.get("repeated", 0) + 1
    if world.facts["repeated"] >= 2:
        world.facts["lost"] = True
    if quest.id == "signal":
        hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    else:
        hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    if narrate:
        world.say(f"The ship went on, and the {quest.keyword} kept repeating: {quest.rhythm}.")


def introduce(world: World, hero: Entity, guide: Guide) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'curious')} pilot "
        f"who loved space and listened for strange lights."
    )
    world.say(
        f"By the window, a bright {guide.label} circled the hull like a watchful friend."
    )


def begin_quest(world: World, hero: Entity, prize: Entity, quest: Quest) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"One night, {hero.id} tucked {hero.pronoun('possessive')} {prize.label} close and wanted to {quest.verb}."
    )


def setting_arrival(world: World, hero: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} flew from {world.setting.place} into a lane of soft blue stars."
    )


def warn(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"Again and again the beacon blinked, and the path looked the same every time."
    )
    world.facts["drift"] = True
    world.say(
        f"{hero.id} tried to {quest.rush}, but the ship slipped toward a dust ring."
    )


def guide_turn(world: World, hero: Entity, guide: Guide, quest: Quest) -> None:
    world.say(
        f"Then the {guide.label} spread its wings and said, as if singing, "
        f'"Listen for the pattern. {guide.method}."'
    )
    world.say(
        f"It counted softly: {quest.rhythm}."
    )
    world.facts["lost"] = False


def resolve(world: World, hero: Entity, prize: Entity, quest: Quest, guide: Guide) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    world.para()
    world.say(
        f"{hero.id} followed the beat, and the ship slipped through the dust ring at the right moment."
    )
    world.say(
        f"At last they reached the moon cave, where {hero.pronoun('possessive')} {prize.label} could rest in a nest of light."
    )
    world.say(
        f"The repeating beacon did not feel confusing anymore. It sounded like a song that had finally found its home."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="pilot",
        traits=["little", trait],
    ))
    guide = world.add(Entity(
        id="Eagle",
        kind="character",
        type="eagle",
        label="eagle",
        traits=["bright", "watchful"],
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        location=prize_cfg.location,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero, guide)
    begin_quest(world, hero, prize, quest)
    setting_arrival(world, hero)
    warn(world, hero, quest)
    guide_turn(world, hero, guide, quest)
    resolve(world, hero, prize, quest, guide)

    world.facts.update(hero=hero, guide=guide, prize=prize, quest=quest, setting=setting, resolved=True)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    return [
        f'Write a short space adventure for a young child about {hero.id}, an eagle helper, and a repeating {quest.keyword}.',
        f"Tell a gentle story where {hero.id} has to {quest.verb} and learns to follow a pattern in space.",
        f"Write a child-friendly quest story with an eagle, a starry ship, and a clue that repeats more than once.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    prize = _safe_fact(world, f, "prize")
    quest = _safe_fact(world, f, "quest")
    return [
        QAItem(
            question=f"Who went on the space quest with the eagle?",
            answer=f"{hero.id} went on the quest with the eagle.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {quest.verb} while keeping the {prize.label} safe.",
        ),
        QAItem(
            question=f"What helped {hero.id} stop getting lost?",
            answer=f"The eagle helped by counting the repeating {quest.keyword} and showing the rhythm.",
        ),
        QAItem(
            question=f"Why was the path hard at first?",
            answer=f"The beacon kept repeating, so the path looked the same and the ship drifted toward danger.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"{hero.id} followed the pattern, reached the moon cave, and the repeating signal became a song instead of a puzzle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an eagle?",
            answer="An eagle is a large bird with strong wings and a sharp beak.",
        ),
        QAItem(
            question="What does repeating mean?",
            answer="Repeating means doing the same thing again and again.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something, help someone, or finish an important task.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registries / parameters
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="orbital_station", quest="signal", prize="star_seed", name="Ari", trait="brave"),
    StoryParams(place="moon_outpost", quest="signal", prize="star_seed", name="Mina", trait="curious"),
    StoryParams(place="starlit_cave", quest="trail", prize="map_chip", name="Tavi", trait="patient"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "quest", None) and getattr(args, "prize", None):
        q = _safe_lookup(QUESTS, getattr(args, "quest", None))
        p = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not quest_is_reasonable(q, p):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = []
    for place, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for pid, prize in PRIZES.items():
                if quest_is_reasonable(quest, prize):
                    if getattr(args, "place", None) and place != getattr(args, "place", None):
                        continue
                    if getattr(args, "quest", None) and qid != getattr(args, "quest", None):
                        continue
                    if getattr(args, "prize", None) and pid != getattr(args, "prize", None):
                        continue
                    combos.append((place, qid, pid))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, qid, pid = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=qid, prize=pid, name=name, trait=trait, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(PRIZES, params.prize), params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
setting(orbital_station; moon_outpost; starlit_cave).
quest(signal; trail).
prize(star_seed; map_chip).

reasonably_valid(signal, star_seed).
reasonably_valid(trail, map_chip).

valid(Place, Q, P) :- setting(Place), quest(Q), prize(P), reasonably_valid(Q, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    lines.append(asp.fact("reasonably_valid", "signal", "star_seed"))
    lines.append(asp.fact("reasonably_valid", "trail", "map_chip"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, qid, pid)
        for place in SETTINGS
        for qid, quest in QUESTS.items()
        for pid, prize in PRIZES.items()
        if quest_is_reasonable(quest, prize)
    ]


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:7}) meters={e.meters} memes={e.memes}")
    lines.append(f"  repeated count: {world.facts.get('repeated', 0)}")
    lines.append(f"  lost: {world.facts.get('lost', False)}")
    lines.append(f"  drift: {world.facts.get('drift', False)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with an eagle and a repeating quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
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
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid space quest combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
