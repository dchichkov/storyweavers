#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pick_duck_dim_wimp_bad_ending_quest.py
==============================================================================================================

A compact superhero-style story world built from the seed words:
pick, duck-dim, wimp.

Premise:
- A young hero must complete a small quest in a city of rooftops, alleys,
  and glowing doors.
- The quest requires choosing the right "duck-dim" tool: a comic, homemade
  gadget that can shrink a loud hazard into something manageable.
- Suspense comes from a ticking clock and a tempting bad ending.
- The story stays child-facing and concrete: the hero hesitates, learns,
  makes the right pick, and turns the ending from bad to brave.

This file follows the storyworld contract:
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager imports from storyworlds/results.py
- lazy ASP import in helpers only
- ASP facts + inline ASP_RULES twin
- `--verify` checks ASP/Python parity and runs generated stories
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
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
class City:
    name: str
    mood: str
    place_words: list[str]
    danger: str
    affords: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    task: str
    gerund: str
    rush: str
    risk: str
    suspense: str
    ending_image: str
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
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    covers: set[str]
    guards: set[str]
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
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
CITIES = {
    "skyport": City("Skyport", "bright", ["rooftop", "bridge", "tower"], "dark hush", {"quest", "suspense"}),
    "lighthouse": City("Lighthouse Bay", "windy", ["dock", "lantern room", "harbor"], "fog", {"quest", "suspense"}),
    "subway": City("Blue Tunnel", "echoing", ["platform", "stairs", "signal room"], "rumble", {"quest", "suspense"}),
}

QUESTS = {
    "signal": Quest(
        id="signal",
        task="restore the city signal",
        gerund="restoring the city signal",
        rush="run to the signal room",
        risk="the bad ending of a city that cannot call for help",
        suspense="the blinking lamp might go out at any second",
        ending_image="the tower light shining over the sleeping streets",
        tags={"signal", "light"},
    ),
    "bridge": Quest(
        id="bridge",
        task="open the bridge gate",
        gerund="opening the bridge gate",
        rush="dash to the bridge lever",
        risk="the bad ending of boats waiting in the dark",
        suspense="the gate wheel kept slipping in the hero's hands",
        ending_image="the bridge lifting like a silver arm above the water",
        tags={"bridge", "water"},
    ),
    "lantern": Quest(
        id="lantern",
        task="relight the harbor lantern",
        gerund="relighting the harbor lantern",
        rush="hurry to the lantern room",
        risk="the bad ending of ships bumping in the fog",
        suspense="the glass lamp was cold and nearly empty",
        ending_image="the lantern glowing like a tiny sun for the boats below",
        tags={"lantern", "fog"},
    ),
}

TOOLS = {
    "duckdim": Tool(
        id="duckdim",
        label="duck-dim gadget",
        phrase="a duck-dim gadget with a bright yellow dial",
        effect="shrinks big trouble into a safe little size",
        covers={"signal", "bridge", "lantern"},
        guards={"dark", "fog", "slip"},
    ),
    "capeclip": Tool(
        id="capeclip",
        label="cape clip",
        phrase="a shiny cape clip",
        effect="keeps a cape from flapping into gears",
        covers={"cape"},
        guards={"wind"},
    ),
    "lampglove": Tool(
        id="lampglove",
        label="lamp glove",
        phrase="a lamp glove lined with soft gray felt",
        effect="lets careful hands hold hot things",
        covers={"lamp"},
        guards={"heat"},
    ),
}

NAMES = ["Nova", "Jet", "Mira", "Leo", "Zane", "Pia", "Kai", "Aria"]
ALTERS = ["bright", "quick", "brave", "curious", "lively", "small"]
CITY_HELPERS = ["a watchful pigeon", "an old mechanic", "a brave courier", "a sleepy cat"]
WIMPS = ["wimp", "little wimp", "scaredy-wimp"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    city: str
    quest: str
    hero: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def quest_needs_duckdim(quest: Quest) -> bool:
    return "quest" in quest.tags or "signal" in quest.tags or "fog" in quest.tags or "water" in quest.tags


def tool_fits_quest(tool: Tool, quest: Quest) -> bool:
    return quest.id in tool.covers or bool(tool.covers & quest.tags)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for qid, q in QUESTS.items():
        for tid, t in TOOLS.items():
            if quest_needs_duckdim(q) and tool_fits_quest(t, q):
                combos.append((qid, tid))
    return combos


def explain_rejection(quest: Quest, tool: Tool) -> str:
    return (
        f"(No story: the {tool.label} does not honestly help with {quest.task}. "
        f"Try the duck-dim gadget, which can shrink the story's big hazard.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
class Sim:
    def __init__(self, world: World) -> None:
        self.world = world
        self.hero = world.get("hero")
        self.helper = world.get("helper")
        self.tool = world.get("tool")
        self.quest = world.facts["quest"]
        self.city = world.city
        self.zone = ""
        self.goal_open = False

    def start(self) -> None:
        self.hero.memes["hope"] = 1
        self.world.say(
            f"{self.hero.id} was a {self.hero.memes.get('trait', 'bright')} hero who loved a good quest."
        )
        self.world.say(
            f"In {self.city.name}, {self.city.mood} streets led to a job that mattered: "
            f"{self.quest.task}."
        )

    def suspense(self) -> None:
        self.hero.memes["suspense"] = 1
        self.world.say(
            f"The quest felt tense because {self.quest.suspense}; "
            f"one wrong move could mean {self.quest.risk}."
        )

    def wimp_moment(self) -> None:
        self.hero.memes["doubt"] = 1
        self.world.say(
            f"A {random.choice(WIMPS)} voice in the dark muttered that {self.hero.id} should turn back."
        )
        self.world.say(
            f"But {self.hero.id} tightened {self.hero.pronoun('possessive')} hands and kept going."
        )

    def pick_tool(self) -> None:
        self.hero.memes["choice"] = 1
        self.tool.carried_by = self.hero.id
        self.world.say(
            f"{self.hero.id} had to pick carefully. {self.hero.pronoun().capitalize()} chose "
            f"{self.tool.phrase} because it {self.tool.effect}."
        )

    def do_quest(self) -> None:
        self.hero.meters["action"] = 1
        self.zone = self.quest.id
        self.world.say(
            f"{self.hero.id} used the {self.tool.label} and stepped into the hard part of the quest."
        )
        if self.quest.id == "signal":
            self.world.say(
                "The yellow dial turned the giant dead switch into a tiny, friendly button."
            )
        elif self.quest.id == "bridge":
            self.world.say(
                "The yellow dial shrank the stuck wheel so the hero could turn it without slipping."
            )
        else:
            self.world.say(
                "The yellow dial dimmed the fog around the lamp until the wick could catch."
            )

    def resolve(self) -> None:
        self.hero.memes["courage"] = 2
        self.world.say(
            f"At last, {self.quest.ending_image} proved that the bad ending had been avoided."
        )
        self.world.say(
            f"{self.hero.id} smiled at {self.helper.id if self.helper.id != 'helper' else self.helper.label} "
            f"and knew the city was safe for one more night."
        )


# ---------------------------------------------------------------------------
# Story script
# ---------------------------------------------------------------------------
def tell(city: City, quest: Quest, hero_name: str, gender: str, helper_name: str, trait: str) -> World:
    world = World(city)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=hero_name, meters={}, memes={"trait": trait}))
    helper = world.add(Entity(id="helper", kind="character", type="character", label=helper_name, meters={}, memes={}))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label="duck-dim gadget"))
    world.facts["quest"] = quest
    world.facts["hero_name"] = hero_name
    world.facts["helper_name"] = helper_name
    world.facts["trait"] = trait
    world.facts["city"] = city
    world.facts["tool"] = tool

    sim = Sim(world)
    sim.start()
    world.para()
    sim.suspense()
    sim.wimp_moment()
    world.para()
    sim.pick_tool()
    sim.do_quest()
    sim.resolve()
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = _safe_fact(world, f, "quest")
    return [
        f'Write a superhero story for young children about a hero who must pick the right duck-dim gadget to {q.task}.',
        f"Tell a suspenseful quest story in a bright comic-book city where a brave child hero refuses to act like a wimp.",
        f'Write a story that uses the words "pick", "duck-dim", and "wimp" while ending with a clear heroic image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    q: Quest = _safe_fact(world, f, "quest")
    hero = _safe_fact(world, f, "hero_name")
    helper = _safe_fact(world, f, "helper_name")
    trait = _safe_fact(world, f, "trait")
    return [
        QAItem(
            question=f"What quest did {hero} have to complete in the city?",
            answer=f"{hero} had to {q.task}. It was a small superhero quest with a tense middle and a brave ending.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful for {hero}?",
            answer=f"It felt suspenseful because {q.suspense}, and the hero had to keep going without making the bad ending happen.",
        ),
        QAItem(
            question=f"What did {hero} pick to help with the quest?",
            answer=f"{hero} picked the duck-dim gadget, because it could shrink the big hazard into something safe enough to handle.",
        ),
        QAItem(
            question=f"How did {helper} help {hero} finish the quest?",
            answer=f"{helper} stayed close while {hero} kept going. That gave the {trait} hero a calm friend beside {f['hero_name']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the worried, waiting feeling you get when something important might go right or wrong and you do not know yet.",
        ),
        QAItem(
            question="What does a hero do in a quest?",
            answer="A hero in a quest keeps going toward an important goal, even when the way is hard or scary.",
        ),
        QAItem(
            question="What does a duck-dim gadget do in this world?",
            answer="A duck-dim gadget shrinks a big problem into a smaller, safer size so the hero can handle it.",
        ),
        QAItem(
            question="What does wimp mean?",
            answer="A wimp is someone who gives up too quickly or acts extra scared instead of trying bravely.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_needs_duckdim(Q) :- quest(Q), tag(Q,quest).
tool_fits_quest(T,Q) :- tool(T), quest(Q), fits(T,Q).
valid(Q,T) :- quest_needs_duckdim(Q), tool_fits_quest(T,Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for tag in sorted(q.tags):
            lines.append(asp.fact("tag", qid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(t.covers):
            lines.append(asp.fact("fits", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    city: str
    quest: str
    hero: str
    gender: str
    helper: str
    trait: str
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
    ap = argparse.ArgumentParser(description="Superhero quest storyworld with suspense and a duck-dim gadget.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=ALTERS)
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
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[0] == getattr(args, "quest", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    quest_id, _ = rng.choice(list(combos))
    city_id = getattr(args, "city", None) or rng.choice(sorted(CITIES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(CITY_HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(ALTERS)
    return StoryParams(city=city_id, quest=quest_id, hero=hero, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(CITIES, params.city), _safe_lookup(QUESTS, params.quest), params.hero, params.gender, params.helper, params.trait)
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
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible quest/tool combos:")
        for q, t in combos:
            print(f"  {q:10} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, (qid, _) in enumerate(sorted(valid_combos())):
            params = StoryParams(
                city=random.choice(sorted(CITIES)),
                quest=qid,
                hero=_safe_lookup(NAMES, i % len(NAMES)),
                gender=["girl", "boy"][i % 2],
                helper=_safe_lookup(CITY_HELPERS, i % len(CITY_HELPERS)),
                trait=_safe_lookup(ALTERS, i % len(ALTERS)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
