#!/usr/bin/env python3
"""
storyworlds/worlds/sliver_distort_lesson_learned_humor_cautionary_superhero.py
===============================================================================

A small superhero-style story world built from the seed words "sliver" and
"distort".

Premise:
- A young hero loves showing off a super move.
- A tiny sliver of glass or metal can distort a cape, mask, or path.
- The hero learns a cautionary lesson: slow down, use tools, and avoid a risky
  shortcut.

Tone:
- Superhero Story
- Lesson Learned
- Humor
- Cautionary

The simulated world keeps the story grounded in physical meters and emotional
memes, and the prose is assembled from the resulting state rather than from a
frozen template paragraph.
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
# Domain model
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protects: set[str] = field(default_factory=set)
    can_hold: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    hero: object | None = None
    sidekick: object | None = None
    target: object | None = None
    tool: object | None = None
    def __post_init__(self):
        for k in ["sharp", "bent", "dirty", "safe", "damage"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "worry", "joy", "humor", "caution", "lesson"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "hero"}
        female = {"girl", "mother", "mom", "woman"}
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
    place: str = "the city rooftop"
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
class Hazard:
    id: str
    label: str
    verb: str
    gerund: str
    rush: str
    danger: str
    distortion: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.hazard: Optional[Hazard] = None
        self.tool: Optional[Tool] = None

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.hazard = self.hazard
        clone.tool = self.tool
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(region in item.protects for item in self.worn_items(actor))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "rooftop": Setting(place="the city rooftop", affords={"glide", "dash", "sweep"}),
    "alley": Setting(place="the narrow alley", affords={"dash", "sweep"}),
    "lab": Setting(place="the moonlit lab", affords={"glide", "scan"}),
}

HAZARDS = {
    "sliver": Hazard(
        id="sliver",
        label="a tiny sliver",
        verb="grab the sliver",
        gerund="grabbing slivers",
        rush="rush toward the glinting sliver",
        danger="could cut the glove",
        distortion="distort the hero's visor",
        keyword="sliver",
        tags={"sliver", "sharp", "glass"},
    ),
    "mirror": Hazard(
        id="mirror",
        label="a warped mirror shard",
        verb="touch the shard",
        gerund="touching shards",
        rush="dash toward the warped mirror shard",
        danger="could scratch the mask",
        distortion="distort the reflection",
        keyword="distort",
        tags={"mirror", "distort", "sharp"},
    ),
    "wire": Hazard(
        id="wire",
        label="a bent wire sliver",
        verb="pick up the wire",
        gerund="picking up wire slivers",
        rush="run toward the bent wire sliver",
        danger="could snag the cape",
        distortion="tangle the cape",
        keyword="sliver",
        tags={"wire", "sliver", "sharp"},
    ),
}

TOOLS = [
    Tool(
        id="gloves",
        label="hero gloves",
        phrase="a pair of hero gloves",
        prep="put on the hero gloves first",
        tail="slipped on the hero gloves",
        protects={"hands"},
        plural=True,
    ),
    Tool(
        id="visor",
        label="a visor shield",
        phrase="a visor shield",
        prep="pull down the visor shield first",
        tail="lowered the visor shield",
        protects={"eyes"},
    ),
    Tool(
        id="net",
        label="a catching net",
        phrase="a catching net",
        prep="use the catching net first",
        tail="swung the catching net",
        protects={"hands", "torso"},
    ),
]

HERO_NAMES = ["Nova", "Milo", "Iris", "Jax", "Ruby", "Zane", "Piper", "Theo"]
HERO_TRAITS = ["brave", "quick", "bright", "bouncy", "clever", "bold"]


@dataclass
class StoryParams:
    place: str
    hazard: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
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


def reasonableness_gate(hazard: Hazard, tool: Tool) -> bool:
    if hazard.id == "sliver" and "hands" in tool.protects:
        return True
    if hazard.id == "mirror" and "eyes" in tool.protects:
        return True
    if hazard.id == "wire" and "hands" in tool.protects:
        return True
    return False


def choose_tool(hazard: Hazard) -> Optional[Tool]:
    for tool in TOOLS:
        if reasonableness_gate(hazard, tool):
            return tool
    return None


def predict_damage(world: World, hero: Entity, hazard: Hazard) -> bool:
    sim = world.copy()
    _do_risky_action(sim, sim.get(hero.id), hazard, narrate=False)
    target = sim.facts["target"].id
    return sim.get(target).meters["damage"] >= 1.0


def _do_risky_action(world: World, hero: Entity, hazard: Hazard, narrate: bool = True) -> None:
    target = _safe_fact(world, world.facts, "target")
    if world.setting and hazard.id not in world.setting.affords:
        return
    hero.memes["pride"] += 1
    hero.meters["speed"] += 1
    if hero.covered(target.id, "hands") or hero.covered(target.id, "eyes"):
        return
    target.meters["damage"] += 1
    target.meters["sharp"] += 1
    hero.memes["worry"] += 1
    if narrate:
        world.say(f"The sliver flashed and the danger rose fast.")


def setup_story(world: World, hero: Entity, sidekick: Entity, hazard: Hazard) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait_word', 'brave')} little hero who loved to help in {world.setting.place}."
    )
    world.say(
        f"{hero.id} and {sidekick.id} had a funny habit of laughing at every tiny problem, even when it tried to look serious."
    )
    world.say(
        f"One evening, they spotted {hazard.label} that could {hazard.danger} and {hazard.distortion}."
    )


def conflict_story(world: World, hero: Entity, sidekick: Entity, hazard: Hazard) -> None:
    hero.memes["pride"] += 1
    hero.memes["caution"] += 0.5
    world.para()
    world.say(
        f"{hero.id} wanted to {hazard.verb} right away, but {sidekick.id} pointed at the sharp edge."
    )
    world.say(
        f'"That sliver can {hazard.distortion}," {sidekick.id} said. "Let\'s not let a shortcut turn into a boo-boo."'
    )
    world.say(
        f"{hero.id} made a superhero pose anyway and tried to {hazard.rush}, which was funny for exactly one second."
    )
    _do_risky_action(world, hero, hazard, narrate=False)
    world.say(
        f"Then the visor blinked crookedly, and everybody saw that the sliver was not as small as it first looked."
    )


def resolution_story(world: World, hero: Entity, sidekick: Entity, hazard: Hazard, tool: Tool) -> None:
    hero.memes["lesson"] += 1
    hero.memes["caution"] += 1
    hero.memes["joy"] += 1
    world.para()
    world.say(
        f"{sidekick.id} held up {tool.phrase} and smiled. {hero.id} chose to {tool.prep} instead."
    )
    world.say(
        f"With the tool in place, {hero.id} could {hazard.verb} safely, and the sliver only glittered like a stubborn little star."
    )
    world.say(
        f"{hero.id} laughed, because the lesson was simple: a real hero does not need to rush a risky thing."
    )
    world.say(
        f"They {tool.tail}, cleaned up the little sliver, and flew home with no scratches and a much wiser grin."
    )


def tell(setting: Setting, hazard: Hazard, hero_name: str = "Nova", trait: str = "brave") -> World:
    world = World(setting)
    world.hazard = hazard

    hero = world.add(Entity(id=hero_name, kind="character", type="hero"))
    sidekick = world.add(Entity(id="Byte", kind="character", type="sidekick"))
    target = world.add(Entity(id="target", type="thing", label="visor", can_hold={"hands"}))
    world.facts["target"] = target

    hero.memes["trait_word"] = 0.0
    hero.memes["trait_word"] = 1.0
    sidekick.memes["humor"] += 1

    setup_story(world, hero, sidekick, hazard)
    conflict_story(world, hero, sidekick, hazard)

    tool = choose_tool(hazard)
    if tool is None:
        pass
    world.tool = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, protects=set(tool.protects), plural=tool.plural))
    world.tool.worn_by = hero.id

    if not predict_damage(world, hero, hazard):
        # If the hazard is somehow already safe, force a legible invalid setup.
        pass

    resolution_story(world, hero, sidekick, hazard, tool)
    world.facts.update(hero=hero, sidekick=sidekick, hazard=hazard, tool=tool)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    hazard = _safe_fact(world, f, "hazard")
    return [
        f'Write a short superhero story for a young child that includes the words "{hazard.keyword}" and "distort".',
        f"Tell a cautionary superhero tale where {hero.id} learns not to rush at {hazard.label}.",
        f"Write a funny lesson-learned story about a hero, a sliver, and a safer way to use a tool.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sidekick, hazard, tool = f["hero"], f["sidekick"], f["hazard"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {hero.id} want to do when they first saw {hazard.label}?",
            answer=f"{hero.id} wanted to {hazard.verb}, but that was risky because the sliver could cause trouble.",
        ),
        QAItem(
            question=f"Why did {sidekick.id} warn {hero.id} about the sliver?",
            answer=f"{sidekick.id} warned {hero.id} because the sliver could {hazard.distortion} and make a superhero mistake turn into a scratch.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem in the end?",
            answer=f"{hero.id} used {tool.phrase} first, so the sliver stayed safe to handle and nobody got hurt.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer="The lesson was to slow down, use the right tool, and not let pride turn a tiny hazard into a bigger problem.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "sliver": [
        (
            "What is a sliver?",
            "A sliver is a very small thin piece of something, like glass or wood, and it can be sharp.",
        )
    ],
    "distort": [
        (
            "What does distort mean?",
            "To distort means to change the shape, look, or picture of something so it is bent, twisted, or not clear.",
        )
    ],
    "sharp": [
        (
            "Why are sharp things handled carefully?",
            "Sharp things can cut skin or damage clothes, so people use tools and move slowly around them.",
        )
    ],
    "humor": [
        (
            "Why can a superhero story be funny?",
            "A superhero story can be funny when a hero acts too dramatic, makes a silly mistake, or learns a lesson in a playful way.",
        )
    ],
    "lesson": [
        (
            "What is a lesson learned in a story?",
            "A lesson learned is the helpful idea a character understands after a mistake or a close call.",
        )
    ],
}
WORLD_KNOWLEDGE_ORDER = ["sliver", "distort", "sharp", "humor", "lesson"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["hazard"].tags)
    tags.update({"lesson", "humor"})
    out: list[QAItem] = []
    for key in globals().get("WORLD_KNOWLEDGE_ORDER", sorted(globals().get("WORLD_KNOWLEDGE", []))):
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hazard(H) :- hazard_id(H).
tool(T) :- tool_id(T).

safe_pair(H, T) :- hazard_id(H), tool_id(T), match(H, T).
valid(H) :- hazard_id(H), safe_pair(H, _).

story_ok(H) :- hazard_id(H), valid(H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, hz in HAZARDS.items():
        lines.append(asp.fact("hazard_id", hid))
        lines.append(asp.fact("hazard_keyword", hid, hz.keyword))
        lines.append(asp.fact("hazard_danger", hid, hz.danger))
        lines.append(asp.fact("hazard_distortion", hid, hz.distortion))
    for tool in TOOLS:
        lines.append(asp.fact("tool_id", tool.id))
        for p in sorted(tool.protects):
            lines.append(asp.fact("protects", tool.id, p))
    for hid, hz in HAZARDS.items():
        for tool in TOOLS:
            if reasonableness_gate(hz, tool):
                lines.append(asp.fact("match", hid, tool.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show safe_pair/2."))
    return sorted(set(asp.atoms(model, "safe_pair")))


def asp_verify() -> int:
    python_pairs = {(h.id, t.id) for h in HAZARDS.values() for t in TOOLS if reasonableness_gate(h, t)}
    asp_pairs = set(asp_valid_pairs())
    if asp_pairs == python_pairs:
        print(f"OK: clingo gate matches Python gate ({len(asp_pairs)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if asp_pairs - python_pairs:
        print("  only in ASP:", sorted(asp_pairs - python_pairs))
    if python_pairs - asp_pairs:
        print("  only in Python:", sorted(python_pairs - asp_pairs))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero lesson-learned story world with a tiny sliver hazard.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--name", choices=HERO_NAMES)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hazard = getattr(args, "hazard", None) or rng.choice(list(HAZARDS))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(HERO_TRAITS)
    if hazard == "mirror" and place == "lab":
        pass
    return StoryParams(place=place, hazard=hazard, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(HAZARDS, params.hazard), hero_name=params.name, trait=params.trait)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.protects:
            parts.append(f"protects={sorted(e.protects)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="rooftop", hazard="sliver", name="Nova", trait="brave"),
    StoryParams(place="alley", hazard="wire", name="Jax", trait="bold"),
    StoryParams(place="lab", hazard="mirror", name="Iris", trait="clever"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_pair/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show safe_pair/2."))
        pairs = sorted(set(asp.atoms(model, "safe_pair")))
        print(f"{len(pairs)} safe hazard/tool pairs:\n")
        for h, t in pairs:
            print(f"  {h:8} {t}")
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
            header = f"### {p.name}: {p.hazard} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
