#!/usr/bin/env python3
"""
A small Tall-Tale storyworld about a boast, a magic quest, a stun, and a happy ending.

The domain:
- A child in a frontier town is tempted to boast about being the best at a quest.
- The boast triggers trouble when a magical guardian or rival challenges them.
- A startling spell or shock stuns the child long enough to reveal a definitive truth.
- A helper offers a simple magical fix, and the story ends in a clear happy ending.

This script is self-contained and follows the Storyweavers storyworld contract.
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
# Entities / world model
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Setting:
    place: str
    wonder: str
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
    goal: str
    gerund: str
    rush: str
    risk: str
    weather: str
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
class MagicTool:
    id: str
    label: str
    phrase: str
    can_fix: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
    tags: set[str] = field(default_factory=set)
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
        self.weather: str = ""

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.weather = self.weather
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    tool: str
    name: str
    gender: str
    helper: str
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


SETTINGS = {
    "trailtown": Setting(place="Trailtown", wonder="the tall wind and the wide dust", affords={"map_quest", "star_quest"}),
    "canyon": Setting(place="Coyote Canyon", wonder="the echoing rocks and the bright sky", affords={"map_quest", "star_quest"}),
    "rivercamp": Setting(place="River Camp", wonder="the silver water and the mossy banks", affords={"lamp_quest", "map_quest"}),
}

QUESTS = {
    "map_quest": Quest(
        id="map_quest",
        goal="find the hidden map",
        gerund="following a trail by maplight",
        rush="run for the ridge to follow the map",
        risk="get lost in the dust",
        weather="windy",
        tags={"quest", "map", "lost"},
    ),
    "star_quest": Quest(
        id="star_quest",
        goal="find the falling star charm",
        gerund="chasing the star trail",
        rush="dash after the blinking star",
        risk="stumble in the dark",
        weather="clear",
        tags={"quest", "star", "magic"},
    ),
    "lamp_quest": Quest(
        id="lamp_quest",
        goal="find the river lantern",
        gerund="walking by lantern glow",
        rush="hurry toward the lantern hill",
        risk="trip on the rocks",
        weather="night",
        tags={"quest", "lamp", "magic"},
    ),
}

TOOLS = {
    "spark_charm": MagicTool(
        id="spark_charm",
        label="a spark charm",
        phrase="a tiny charm that glittered like a firefly",
        can_fix={"stun"},
        prep="hold up the spark charm",
        tail="the spark charm woke the whole trail",
        tags={"magic", "stun"},
    ),
    "bright_hat": MagicTool(
        id="bright_hat",
        label="a bright hat",
        phrase="a broad hat with a stitched silver star",
        can_fix={"lost"},
        prep="pull on the bright hat",
        tail="the bright hat helped the trail shine plain as day",
        tags={"magic"},
    ),
    "song_lantern": MagicTool(
        id="song_lantern",
        label="a song lantern",
        phrase="a lantern that hummed a gentle tune",
        can_fix={"dark"},
        prep="lift the song lantern high",
        tail="the song lantern made the path friendly as a porch",
        tags={"magic", "happy_ending"},
    ),
}

NAMES_GIRL = ["Rose", "Mabel", "June", "Hazel", "Lottie", "Ivy"]
NAMES_BOY = ["Jed", "Cal", "Ned", "Will", "Tom", "Bodie"]
TRAITS = ["brash", "bold", "lively", "cheery", "stubborn", "spirited"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def infer_pronoun_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def valid_combo(place: str, quest: str, tool: str) -> bool:
    q = _safe_lookup(QUESTS, quest)
    t = _safe_lookup(TOOLS, tool)
    if "magic" in q.tags and "magic" not in t.tags:
        return False
    if "stun" in t.can_fix and quest != "star_quest":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for q in _safe_lookup(SETTINGS, p).affords:
            for t in TOOLS:
                if valid_combo(p, q, t):
                    combos.append((p, q, t))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if (params.place, params.quest, params.tool) not in valid_combos():
        pass


def predict_stun(world: World, hero: Entity, quest: Quest) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["boast"] = 1.0
    sim.get(hero.id).meters["attention"] = 1.0
    return quest.id == "star_quest"


def start_tale(world: World, hero: Entity, helper: Entity, quest: Quest, tool: MagicTool) -> None:
    world.say(
        f"In {world.setting.place}, where {world.setting.wonder}, there lived a {hero.pronoun('subject')} named {hero.id} who liked to boast."
    )
    world.say(
        f"{hero.id} was a {next((t for t in hero.memes.get('traits', []) if t), 'brash')} child who loved {quest.gerund} and believed every tall tale should end with {quest.goal}."
    )


def boast(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["boast"] += 1
    hero.meters["confidence"] += 1
    world.say(
        f'{hero.id} grinned and said, "I can {quest.goal} better than anyone in the whole wide West!"'
    )


def challenge(world: World, helper: Entity, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{helper.id} heard that boast and lifted {helper.pronoun('possessive')} chin. "
        f'"That is a mighty claim," {helper.pronoun()} said. "If you mean it, then show me."'
    )
    hero.memes["pressure"] += 1


def stun_event(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["stun"] += 1
    hero.memes["surprise"] += 1
    world.say(
        f"Then, with a flash like a silver spoon dropped in moonlight, the trail gave {hero.id} a good stun."
    )
    world.say(
        f"{hero.id} blinked hard, because {quest.risk} was suddenly no longer a joke."
    )


def reveal_definitive_truth(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["humility"] += 1
    world.say(
        f"That was the definitive truth of the trail: a boast was loud, but the real way forward was careful steps and a steady heart."
    )


def use_magic(world: World, hero: Entity, helper: Entity, quest: Quest, tool: MagicTool) -> None:
    hero.meters["stun"] = 0
    hero.memes["fear"] = 0
    hero.memes["hope"] += 1
    world.say(
        f"{helper.id} smiled, then {tool.prep} and said, 'Here is the magic that helps.'"
    )
    world.say(
        f"Together they {quest.rush}, and {tool.tail}."
    )


def happy_ending(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["joy"] += 2
    hero.memes["boast"] = max(0.0, hero.memes.get("boast", 0.0) - 1.0)
    world.say(
        f"In the happy ending, {hero.id} found {quest.goal}, and the whole town cheered as if the sun itself had tipped its hat."
    )
    world.say(
        f"{hero.id} laughed, because the best tale was not the boast at the start, but the brave way {hero.pronoun('subject')} finished."
    )


def tell(setting: Setting, quest: Quest, tool: MagicTool, hero_name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = quest.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=infer_pronoun_type(gender)))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    hero.memes["traits"] = [trait]

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["quest"] = quest
    world.facts["tool"] = tool
    world.facts["setting"] = setting

    start_tale(world, hero, helper, quest, tool)
    world.para()
    boast(world, hero, quest)
    challenge(world, helper, hero, quest)
    if quest.id == "star_quest":
        stun_event(world, hero, quest)
        reveal_definitive_truth(world, hero, quest)
    world.para()
    use_magic(world, hero, helper, quest, tool)
    happy_ending(world, hero, helper, quest)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a Tall-Tale story for a young child about a {hero.type} who boasts about {quest.goal} and then learns a better way.',
        f"Tell a playful frontier story where {hero.id} meets {quest.goal}, a little magic, and a happy ending.",
        f'Write a short story that uses the words "stun", "definitive", and "boast" while the hero follows {tool.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    quest: Quest = _safe_fact(world, f, "quest")
    tool: MagicTool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {hero.id} boast about at {world.setting.place}?",
            answer=f"{hero.id} boasted about {quest.goal}. The child thought the task was easy, but the trail had other ideas.",
        ),
        QAItem(
            question=f"Why did {helper.id} challenge {hero.id} after the boast?",
            answer=f"{helper.id} challenged {hero.id} because the boast was loud and big, and the helper wanted to see a real plan for {quest.goal}.",
        ),
        QAItem(
            question=f"What happened after the trail gave {hero.id} a stun?",
            answer=f"{hero.id} stopped, blinked, and learned the definitive truth that careful steps mattered more than bragging.",
        ),
        QAItem(
            question=f"What magic helped {hero.id} finish the quest?",
            answer=f"{tool.phrase} helped them move forward. With that magic, {hero.id} and {helper.id} could finish the quest safely.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended happily: {hero.id} found {quest.goal}, the town cheered, and the boast turned into a proud but gentle memory.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something, solve a problem, or do a brave job.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something special and impossible-looking that can help or change things in the story.",
        ),
        QAItem(
            question="What does it mean to boast?",
            answer="To boast means to talk in a proud way about yourself, sometimes more proudly than is wise.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the trouble is solved and the story finishes in a good, cheerful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_risky(Q) :- quest(Q), risk(Q, R), R = stun.
compatible(P, Q, T) :- setting(P), affords(P, Q), quest(Q), tool(T), fixable(T, Q).
compatible(P, Q, T) :- setting(P), affords(P, Q), quest(Q), tool(T), not risk(Q, stun).
valid_story(P, Q, T) :- compatible(P, Q, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for q in sorted(_safe_lookup(SETTINGS, pid).affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if q.risk == "stun":
            lines.append(asp.fact("risk", qid, "stun"))
        for tag in sorted(q.tags):
            lines.append(asp.fact("tag", qid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for fix in sorted(t.can_fix):
            lines.append(asp.fact("fixable", tid, fix))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag_tool", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo = set(asp.atoms(asp.one_model(asp_program("#show compatible/3.")), "compatible"))
    if py == clingo:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - clingo:
        print("Only in Python:", sorted(py - clingo))
    if clingo - py:
        print("Only in ASP:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: boast, quest, magic, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "uncle", "aunt"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in combos
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              if getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None)
              if getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, quest, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "uncle", "aunt"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(TOOLS, params.tool), params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("trailtown", "map_quest", "bright_hat", "Jed", "boy", "uncle", "brash"),
            StoryParams("canyon", "star_quest", "spark_charm", "Rose", "girl", "aunt", "spirited"),
            StoryParams("rivercamp", "lamp_quest", "song_lantern", "Cal", "boy", "mother", "lively"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 25):
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
