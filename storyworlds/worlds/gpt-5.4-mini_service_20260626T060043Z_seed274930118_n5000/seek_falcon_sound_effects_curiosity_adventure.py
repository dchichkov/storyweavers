#!/usr/bin/env python3
"""
Standalone story world: a curious child seeks a falcon, follows sound effects,
and learns how adventure can be brave without being reckless.

This script is self-contained and uses only the stdlib plus the shared
storyworlds/results.py and storyworlds/asp.py helpers.
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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"

    @property
    def role(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    place: str = "the windy ridge"
    contains_echoes: bool = True
    affords: set[str] = field(default_factory=lambda: {"seek"})
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
    sound: str
    clue: str
    risk: str
    mood_boost: str
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
    helps: set[str]
    safe_when: set[str] = field(default_factory=set)
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
        self.trail_clear = True
        self.falcon_seen = False

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
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.trail_clear = self.trail_clear
        c.falcon_seen = self.falcon_seen
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ridge": Setting(place="the windy ridge", contains_echoes=True, affords={"seek"}),
    "canyon": Setting(place="the red canyon", contains_echoes=True, affords={"seek"}),
    "meadow": Setting(place="the quiet meadow", contains_echoes=False, affords={"seek"}),
}

QUESTS = {
    "falcon": Quest(
        id="falcon",
        verb="seek the falcon",
        gerund="seeking the falcon",
        sound="kree-kree",
        clue="a sharp cry circling overhead",
        risk="wander too far from the trail",
        mood_boost="thrilled",
        tags={"falcon", "bird", "sound"},
    ),
    "echo": Quest(
        id="echo",
        verb="follow the echo",
        gerund="following the echo",
        sound="boop-boop",
        clue="a bouncing call that slipped between the rocks",
        risk="lose the path",
        mood_boost="curious",
        tags={"sound"},
    ),
}

TOOLS = {
    "whistle": Tool(
        id="whistle",
        label="a small whistle",
        phrase="a small whistle on a cord",
        helps={"sound"},
        safe_when={"trail"},
    ),
    "trail_map": Tool(
        id="trail_map",
        label="a folded trail map",
        phrase="a folded trail map",
        helps={"trail"},
        safe_when={"trail"},
    ),
    "binoculars": Tool(
        id="binoculars",
        label="binoculars",
        phrase="a pair of binoculars",
        helps={"falcon"},
        safe_when={"falcon"},
    ),
}

NAMES = ["Ari", "Mina", "Toby", "Luca", "Nora", "Ivy"]
TRAITS = ["curious", "brave", "restless", "bright", "eager"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def quest_at_risk(setting: Setting, quest: Quest) -> bool:
    return setting.contains_echoes or quest.id == "falcon"


def select_tool(quest: Quest) -> Optional[Tool]:
    if quest.id == "falcon":
        return TOOLS["binoculars"]
    if quest.id == "echo":
        return TOOLS["whistle"]
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            if quest_at_risk(setting, quest) and select_tool(quest):
                out.append((place, qid))
    return out


def explain_rejection(setting: Setting, quest: Quest) -> str:
    return (
        f"(No story: this setting does not give a good adventure for {quest.gerund}. "
        f"Try the ridge or canyon, where the sound can lead the child somewhere worth seeking.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def _do_seek(world: World, child: Entity, quest: Quest, tool: Optional[Tool], narrate: bool = True) -> None:
    child.memes["curiosity"] += 1
    child.memes["hope"] += 1
    if tool:
        child.meters[tool.id] = 1
    world.falcon_seen = quest.id == "falcon"
    if quest.id == "falcon":
        child.meters["distance"] = 1
    if narrate:
        world.say(f"{child.id} listened for {quest.sound} and kept moving with careful steps.")
        world.say(f"The air answered with {quest.clue}.")
        if tool:
            world.say(f"{child.pronoun('possessive').capitalize()} {tool.label} helped {child.pronoun('object')} look higher and farther.")


def predict_turn(world: World, child: Entity, quest: Quest, tool: Optional[Tool]) -> dict:
    sim = world.copy()
    _do_seek(sim, sim.get(child.id), quest, tool, narrate=False)
    return {
        "falcon_seen": sim.falcon_seen,
        "curiosity": sim.get(child.id).memes.get("curiosity", 0),
    }


def setup(world: World, child: Entity, parent: Entity, quest: Quest) -> None:
    world.say(f"{child.id} was a {child.pronoun('subject').capitalize() if False else ''}".strip())
    world.say(f"{child.id} was a little {child.type} who loved curious adventures.")
    world.say(f"{child.pronoun('subject').capitalize()} wanted to {quest.verb} because {quest.sound} sounded like a mystery.")
    world.say(f"That morning, {child.id} and {child.pronoun('possessive')} {parent.role} went to {world.setting.place}.")


def warn(world: World, parent: Entity, child: Entity, quest: Quest) -> None:
    world.say(
        f'"If you chase the call, you might {quest.risk}," {parent.role} said. '
        f'"Stay where I can see you."'
    )


def answer_adventure(world: World, parent: Entity, child: Entity, quest: Quest, tool: Tool) -> None:
    child.memes["joy"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{child.id} nodded, tucked the {tool.label} in {child.pronoun('possessive')} hand, and chose the safer path."
    )
    world.say(
        f"Together they followed the sound, and at last a brown shape flashed across the blue sky."
    )
    world.say(
        f"It was a falcon, high and fast, turning like an arrow above the ridge."
    )


def finish(world: World, child: Entity, parent: Entity, quest: Quest, tool: Tool) -> None:
    world.say(
        f"{child.id} smiled so wide it felt like sunshine. "
        f"{child.pronoun('subject').capitalize()} had gone seeking with caution, and the adventure felt bigger because it was safe."
    )
    world.say(
        f"On the walk home, {child.id} listened for one last {quest.sound}, "
        f"and the empty sky still felt full of wonder."
    )


# ---------------------------------------------------------------------------
# The world story
# ---------------------------------------------------------------------------
def tell(setting: Setting, quest: Quest, child_name: str = "Ari", gender: str = "boy", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    tool = select_tool(quest)
    if tool is None:
        pass
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=child.id))
    tool_ent.carried_by = child.id

    setup(world, child, parent, quest)
    world.para()
    warn(world, parent, child, quest)
    pred = predict_turn(world, child, quest, tool_ent)
    if not pred["falcon_seen"]:
        pass
    _do_seek(world, child, quest, tool_ent, narrate=True)
    world.para()
    answer_adventure(world, parent, child, quest, tool)
    finish(world, child, parent, quest, tool)

    world.facts.update(child=child, parent=parent, quest=quest, tool=tool, setting=setting, predicted=pred)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, quest, tool = f["child"], f["quest"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a gentle adventure story for a young child who wants to {quest.verb} using sound clues.',
        f'Tell a story where {child.id} follows {quest.sound} and stays safe with help from {tool.label}.',
        f'Write a short adventure about curiosity, a falcon, and a child who listens before acting.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, quest, tool = f["child"], f["parent"], f["quest"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Why did {child.id} want to go to {world.setting.place}?",
            answer=f"{child.id} wanted to {quest.verb} because {quest.sound} sounded like a mystery worth following.",
        ),
        QAItem(
            question=f"What did the {parent.role} worry might happen if {child.id} ran off alone?",
            answer=f"The {parent.role} worried that {child.id} might {quest.risk}.",
        ),
        QAItem(
            question=f"How did {tool.label} help the child in the adventure?",
            answer=f"{tool.label.capitalize()} helped {child.id} keep track of the trail while {child.id} looked and listened for the falcon.",
        ),
        QAItem(
            question=f"What animal did {child.id} finally see?",
            answer="The child finally saw a falcon flying high above the ridge.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a falcon?",
            answer="A falcon is a fast bird of prey that can fly very high and dive very quickly.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to learn, look, and ask questions about something new.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises that help a story, game, or movie feel exciting and real.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"falcon_seen={world.falcon_seen}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(P) :- place(P).
quest(Q) :- quest_id(Q).

compatible(P,Q) :- contains_echoes(P), quest_id(Q), has_tool(Q).
compatible(P,"falcon") :- place(P), quest_id("falcon"), has_tool("falcon").
compatible(P,"echo") :- place(P), quest_id("echo"), has_tool("echo").

valid_story(P,Q) :- compatible(P,Q).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.contains_echoes:
            lines.append(asp.fact("contains_echoes", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid in QUESTS:
        lines.append(asp.fact("quest_id", qid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        if tool.helps:
            for h in sorted(tool.helps):
                lines.append(asp.fact("has_tool", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    parent: str
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


CURATED = [
    StoryParams(place="ridge", quest="falcon", name="Ari", gender="boy", parent="mother", trait="curious"),
    StoryParams(place="canyon", quest="falcon", name="Mina", gender="girl", parent="father", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a curious child seeks a falcon using sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "place", None) or getattr(args, "quest", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) if hasattr(args, "trait") and getattr(args, "trait", None) else rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), params.name, params.gender, params.parent)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for place, quest in combos:
            print(f"  {place:8} {quest}")
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
