#!/usr/bin/env python3
"""
A small detective-story world about a missing clue, a hasty lunge, a multiplying
pattern of suspects, and a handy tool that helps the case get solved.

The story model tracks:
- physical meters: evidence, distance, risk, usefulness
- emotional memes: worry, confidence, suspicion, relief
- a moral value: whether the detective chooses the fair/wise action
- an inner monologue: private thoughts that guide the next move
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    detective: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "detective"}:
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
    place: str = "the old station"
    mood: str = "quiet"
    affords: set[str] = field(default_factory=lambda: {"lunge", "multiply"})
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
class Clue:
    label: str
    phrase: str
    tricky: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    lowers_risk: float = 1.0
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
    place: str
    clue: str
    tool: str
    name: str
    gender: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "station": Setting(place="the old station", mood="quiet", affords={"lunge", "multiply"}),
    "alley": Setting(place="the narrow alley", mood="foggy", affords={"lunge", "multiply"}),
    "archive": Setting(place="the archive room", mood="dusty", affords={"multiply"}),
}

CLUES = {
    "coin": Clue(label="coin", phrase="a shiny coin", tricky=False),
    "note": Clue(label="note", phrase="a folded note", tricky=False),
    "key": Clue(label="key", phrase="a tiny brass key", tricky=True),
    "stamp": Clue(label="stamp", phrase="a stamped scrap of paper", tricky=True),
}

TOOLS = {
    "handy_magnifier": Tool(
        id="handy_magnifier",
        label="a handy magnifier",
        phrase="a handy magnifier",
        helps_with={"lunge", "multiply"},
        lowers_risk=1.0,
    ),
    "handy_notebook": Tool(
        id="handy_notebook",
        label="a handy notebook",
        phrase="a handy notebook",
        helps_with={"multiply"},
        lowers_risk=0.5,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ivy", "Ada", "June", "Pia"]
BOY_NAMES = ["Eli", "Noah", "Milo", "Theo", "Finn", "Ben", "Jace"]
TRAITS = ["careful", "brave", "sharp", "quiet", "patient", "curious"]


# ---------------------------------------------------------------------------
# Reasoning constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for tool_id, tool in TOOLS.items():
                if place == "archive" and clue_id in {"coin", "note"}:
                    continue
                if clue.tricky and "lunge" not in setting.affords:
                    continue
                out.append((place, clue_id, tool_id))
    return out


def explain_rejection(place: str, clue_id: str, tool_id: str) -> str:
    clue = _safe_lookup(CLUES, clue_id)
    tool = _safe_lookup(TOOLS, tool_id)
    if place == "archive" and clue_id in {"coin", "note"}:
        return "(No story: the archive is too tidy for that easy clue. Choose a trickier clue there.)"
    if clue.tricky and "lunge" not in _safe_lookup(SETTINGS, place).affords:
        return "(No story: this place does not support the risky lunge needed for a tricky clue.)"
    if "multiply" not in tool.helps_with and clue.tricky:
        return "(No story: this tool is not handy enough for a clue that keeps multiplying.)"
    return "(No story: that combination is not reasonable.)"


def setting_detail(setting: Setting) -> str:
    return {
        "quiet": f"{setting.place.capitalize()} felt so quiet that every footstep sounded like a question.",
        "foggy": f"The fog hung low around {setting.place}, blurring corners and hiding small things.",
        "dusty": f"Old dust rested on the shelves in {setting.place}, like the room was keeping secrets.",
    }.get(setting.mood, f"{setting.place.capitalize()} was ready for a mystery.")


def clue_behavior(clue: Clue) -> str:
    if clue.tricky:
        return "It seemed to split into extra signs the more the detective looked at it."
    return "It sat there plainly, waiting to be noticed."


def inner_voice(detective: Entity, clue: Clue, tool: Optional[Tool] = None) -> str:
    if clue.tricky and tool:
        return (
            f"{detective.id} thought, \"If I rush, I may miss the real pattern. "
            f"But {tool.label} should help me see what is multiplying.\""
        )
    if clue.tricky:
        return f"{detective.id} thought, \"This clue is slippery. I need to slow down and be fair.\""
    return f"{detective.id} thought, \"Stay calm. The small clue will matter if I pay attention.\""


# ---------------------------------------------------------------------------
# World dynamics
# ---------------------------------------------------------------------------
def predict(world: World, detective: Entity, clue: Clue, tool: Tool) -> dict:
    sim = world.copy()
    _act_lunge(sim, sim.get(detective.id), clue, narrate=False)
    _act_multiply(sim, sim.get(detective.id), clue, narrate=False)
    return {
        "risk": sim.get("clue").meters.get("risk", 0.0),
        "suspicion": sim.get("clue").memes.get("suspicion", 0.0),
    }


def _act_lunge(world: World, detective: Entity, clue: Clue, narrate: bool = True) -> None:
    detective.meters["distance"] = detective.meters.get("distance", 0.0) + 1.0
    detective.memes["urgency"] = detective.memes.get("urgency", 0.0) + 1.0
    clue_ent = world.get("clue")
    clue_ent.meters["risk"] = clue_ent.meters.get("risk", 0.0) + 1.0
    clue_ent.memes["suspicion"] = clue_ent.memes.get("suspicion", 0.0) + 1.0
    if narrate:
        world.say(
            f"{detective.id} made a quick lunge toward {clue.phrase}, and the room felt tense."
        )


def _act_multiply(world: World, detective: Entity, clue: Clue, narrate: bool = True) -> None:
    clue_ent = world.get("clue")
    if clue_ent.meters.get("risk", 0.0) < THRESHOLD:
        return
    sig = ("multiply", clue.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    clue_ent.meters["copies"] = clue_ent.meters.get("copies", 1.0) + 2.0
    clue_ent.memes["confusion"] = clue_ent.memes.get("confusion", 0.0) + 1.0
    detective.memes["worry"] = detective.memes.get("worry", 0.0) + 1.0
    if narrate:
        world.say(
            f"Then the clue seemed to multiply into more marks and more questions."
        )


def _act_handy(world: World, detective: Entity, tool: Tool, clue: Clue, narrate: bool = True) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["risk"] = max(0.0, clue_ent.meters.get("risk", 0.0) - tool.lowers_risk)
    clue_ent.memes["suspicion"] = max(0.0, clue_ent.memes.get("suspicion", 0.0) - 1.0)
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 1.0
    if narrate:
        world.say(f"Luckily, {tool.phrase} was handy, and it helped {detective.id} read the pattern clearly.")


def resolve_moral_value(world: World, detective: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    if clue_ent.meters.get("risk", 0.0) <= 0.0 and detective.memes.get("confidence", 0.0) > 0.0:
        detective.meters["moral_value"] = detective.meters.get("moral_value", 0.0) + 1.0
        detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1.0
        world.say(
            f"{detective.id} chose the fair, patient way, and the case stopped feeling like a trap."
        )


def tell(setting: Setting, clue: Clue, tool: Tool,
         name: str = "Mina", gender: str = "girl", role: str = "detective") -> World:
    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.label, phrase=clue.phrase))
    world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase))

    world.say(f"{detective.id} was a {role} who liked to solve problems without being unfair.")
    world.say(setting_detail(setting))
    world.say(f"One day, {detective.id} found {clue.phrase}. {clue_behavior(clue)}")
    world.say(inner_voice(detective, clue, tool if clue.tricky else None))

    world.para()
    _act_lunge(world, detective, clue)
    world.say(
        f"{detective.id} looked again, because a hasty move can make a clue worse instead of better."
    )
    _act_multiply(world, detective, clue)
    world.say(
        f"{detective.id} noticed that the clue was not just changing; it was multiplying into a bigger pattern."
    )

    world.para()
    _act_handy(world, detective, tool, clue)
    resolve_moral_value(world, detective, clue)
    world.say(
        f"In the end, {detective.id} kept the clue safe, solved the case, and walked out with a clear conscience."
    )

    world.facts.update(
        detective=detective,
        clue=clue_ent,
        tool=tool,
        setting=setting,
        clue_cfg=clue,
        tool_cfg=tool,
        moral_value=detective.meters.get("moral_value", 0.0) >= THRESHOLD,
        resolved=detective.meters.get("moral_value", 0.0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = _safe_fact(world, f, "detective")
    clue = _safe_fact(world, f, "clue_cfg")
    return [
        f'Write a short detective story for a young child that includes the words "{clue.label}" and "handy".',
        f"Tell a mystery where {det.id} must not lunge too fast because the clue keeps multiplying.",
        f"Write a gentle detective story with an inner monologue and a moral choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = _safe_fact(world, f, "detective")
    clue = _safe_fact(world, f, "clue_cfg")
    tool = _safe_fact(world, f, "tool_cfg")
    place = _safe_fact(world, f, "setting").place
    qa = [
        QAItem(
            question=f"Who is the story about at {place}?",
            answer=f"It is about {det.id}, a careful detective who tries to solve a mystery at {place}.",
        ),
        QAItem(
            question=f"What happened to the clue after {det.id} made a lunge?",
            answer=f"The clue got riskier, and then it seemed to multiply into more signs and questions.",
        ),
        QAItem(
            question=f"Why was {tool.label} important in the case?",
            answer=f"It was handy because it helped {det.id} notice the pattern and keep the clue from getting out of control.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did the detective make a good moral choice?",
            answer=(
                f"{det.id} slowed down, used {tool.label}, and chose the fair, patient way instead of acting on a rush."
            ),
        ))
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does a detective do?",
        answer="A detective looks carefully for clues and tries to solve a mystery.",
    ),
    QAItem(
        question="What is an inner monologue?",
        answer="An inner monologue is the quiet thought a character has in their own mind.",
    ),
    QAItem(
        question="What does it mean when something is handy?",
        answer="If something is handy, it is useful and easy to use when you need it.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(station). setting(alley). setting(archive).
affords(station,lunge). affords(station,multiply).
affords(alley,lunge). affords(alley,multiply).
affords(archive,multiply).

clue(coin). clue(note). clue(key). clue(stamp).
tricky(key). tricky(stamp).

tool(handy_magnifier). tool(handy_notebook).
helps_with(handy_magnifier,lunge). helps_with(handy_magnifier,multiply).
helps_with(handy_notebook,multiply).

valid(Place,Clue,Tool) :- setting(Place), clue(Clue), tool(Tool),
    affords(Place,lunge), helps_with(Tool,multiply).
valid(Place,Clue,Tool) :- setting(Place), clue(Clue), tool(Tool),
    affords(Place,multiply), helps_with(Tool,multiply).
valid(archive,Clue,Tool) :- clue(Clue), tool(Tool), tricky(Clue), helps_with(Tool,multiply).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(_safe_lookup(SETTINGS, sid).affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.tricky:
            lines.append(asp.fact("tricky", cid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(t.helps_with):
            lines.append(asp.fact("helps_with", tid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------
@dataclass
class _ArgsMirror:
    place: Optional[str] = None
    clue: Optional[str] = None
    tool: Optional[str] = None
    gender: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False
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


CURATED = [
    StoryParams(place="station", clue="key", tool="handy_magnifier", name="Mina", gender="girl", role="detective"),
    StoryParams(place="alley", clue="stamp", tool="handy_notebook", name="Leo", gender="boy", role="detective"),
    StoryParams(place="archive", clue="stamp", tool="handy_magnifier", name="Iris", gender="girl", role="detective"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: lunge, multiply, handy, moral value, inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--role", default="detective")
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
    if getattr(args, "place", None) and getattr(args, "clue", None) and getattr(args, "tool", None):
        if (getattr(args, "place", None), getattr(args, "clue", None), getattr(args, "tool", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    role = getattr(args, "role", None) or "detective"
    return StoryParams(place=place, clue=clue, tool=tool, name=name, gender=gender, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CLUES, params.clue), _safe_lookup(TOOLS, params.tool),
                 name=params.name, gender=params.gender, role=params.role)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for place, clue, tool in combos:
            print(f"  {place:8} {clue:8} {tool}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
