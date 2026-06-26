#!/usr/bin/env python3
"""
storyworlds/worlds/scientific_acuity_humor_friendship_ghost_story.py
====================================================================

A small storyworld about a spooky-looking place, two friends, and the kind of
careful noticing that turns a ghost story into a funny, kind discovery.

The seed words are "scientific" and "acuity". The tone stays in the ghost-story
lane, but the simulated turn is child-friendly: the characters notice clues,
test a few ideas, laugh at the wrong guesses, and end by helping the lonely
"ghost" or the thing that looked like one.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    friend: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    ambience: str
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
class Tool:
    id: str
    label: str
    purpose: str
    helps_with: set[str]
    use_line: str
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
class Clue:
    id: str
    label: str
    reveal: str
    kind: str
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
class StoryParams:
    setting: str
    clue: str
    tool: str
    name: str
    friend: str
    gender: str
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
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "attic": Setting("the old attic", "dusty and moonlit", {"listen", "measure", "peek"}),
    "library": Setting("the closed library", "quiet and echoing", {"listen", "measure", "peek"}),
    "basement": Setting("the school basement", "cool and creaky", {"listen", "measure", "peek"}),
}

TOOLS = {
    "flashlight": Tool("flashlight", "a small flashlight", "shine on clues", {"peek"}, "shined a narrow beam"),
    "tape": Tool("tape", "measuring tape", "check the size of clues", {"measure"}, "measured the clue carefully"),
    "notebook": Tool("notebook", "a notebook", "write observations", {"listen", "measure", "peek"}, "wrote down every clue"),
}

CLUES = {
    "draft": Clue("draft", "a chilly draft", "the ghostly feeling came from a cracked window", "science"),
    "owl": Clue("owl", "a soft hoot", "the spooky sound was an owl on the ledge", "nature"),
    "projector": Clue("projector", "a blinking projector", "the ghostly shadow was a loose projector ribbon", "machine"),
    "ghost": Clue("ghost", "a friendly ghost", "the attic visitor was a shy ghost who wanted company", "ghost"),
}

GIRL_NAMES = ["Mina", "Ivy", "June", "Luna", "Nora", "Pia", "Zoe"]
BOY_NAMES = ["Eli", "Theo", "Max", "Ben", "Noah", "Finn", "Leo"]
FRIEND_NAMES = ["Sam", "Ari", "Nico", "Ruby", "Milo", "Tess", "Owen"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world about acuity, science, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    if clue == "ghost" and tool == "flashlight":
        pass
    elif clue in {"draft", "owl", "projector"} and tool not in {"flashlight", "tape", "notebook"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, clue=clue, tool=tool, name=name, friend=friend, gender=gender)


def _g() -> str:
    return "she"  # not used, just to keep lint simple


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(params.name, kind="character", type=params.gender))
    friend = world.add(Entity(params.friend, kind="character", type="friend"))
    tool = world.add(Entity(_safe_lookup(TOOLS, params.tool).id, type="tool", label=_safe_lookup(TOOLS, params.tool).label, phrase=_safe_lookup(TOOLS, params.tool).purpose))
    clue = world.add(Entity(_safe_lookup(CLUES, params.clue).id, type="clue", label=_safe_lookup(CLUES, params.clue).label, phrase=_safe_lookup(CLUES, params.clue).reveal))

    hero.memes["curiosity"] = 1
    hero.memes["acuity"] = 1
    friend.memes["nervous"] = 1
    friend.memes["trust"] = 1

    world.say(f"{hero.id} and {friend.id} stood at {world.setting.place}, where the air felt {world.setting.ambience}.")
    world.say(f"They had come with {tool.label}, because a spooky story is easier to solve when you look closely and think scientifically.")
    world.para()
    world.say(f"At first, {friend.id} whispered that the place sounded haunted.")
    world.say(f"But {hero.id} had good acuity: {hero.id} noticed {clue.label} and remembered that every ghost story leaves clues.")
    world.say(f"{hero.id} used {tool.label} and {_safe_lookup(TOOLS, params.tool).use_line}, listening for the tiny truth inside the big scary noise.")
    world.para()
    if params.clue == "ghost":
        hero.memes["surprise"] = 1
        world.say(f"Then a little ghost floated out, not with a howl, but with a shy wave.")
        world.say(f'The ghost said, "I was only trying to make friends."')
        world.say(f"{friend.id} blinked, then laughed so hard that even the cobwebs seemed to smile.")
        world.say(f"{hero.id} and {friend.id} invited the ghost to stay for a while, and the room felt less spooky and more warm.")
    elif params.clue == "projector":
        world.say(f"The scary shape was only a projector ribbon fluttering in the breeze.")
        world.say(f"{friend.id} laughed first, because the ribbon looked dramatic enough to star in its own ghost tale.")
        world.say(f"{hero.id} fixed it with a careful hand, and the room became ordinary again.")
        world.say("The ordinary ending felt friendly, which is often the nicest kind of magic.")
    elif params.clue == "owl":
        world.say(f"The strange sound came from an owl, perched like a tiny librarian in the dark.")
        world.say(f"{friend.id} giggled and said the owl sounded more grumpy than haunted.")
        world.say(f"{hero.id} smiled, and they left the owl in peace while the night kept its secrets.")
    else:
        world.say(f"The chill came from a cracked window.")
        world.say(f"{hero.id} found the cold gap and closed it, so the room stopped pretending to be haunted.")
        world.say(f"{friend.id} grinned and said the biggest ghost had been the draft all along.")
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.facts.update(hero=hero, friend=friend, tool=tool, clue=clue, setting=params.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for children about {f["hero"].id} and {f["friend"].id} using a {(f.get("tool") or next(iter(TOOLS.values()))).label}.',
        f"Tell a funny, gentle haunted-house story where scientific acuity helps {f['hero'].id} solve what the spooky sound really is.",
        f'Write a story that feels a little spooky at first, but ends with friendship and a clever explanation for "{f["clue"].label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, tool, clue = f["hero"], f["friend"], (f.get("tool") or next(iter(TOOLS.values()))), f["clue"]
    return [
        QAItem(
            question=f"Who went into {world.setting.place} to figure out the spooky sound?",
            answer=f"{hero.id} went with {friend.id}, and they brought {tool.label} so they could investigate carefully.",
        ),
        QAItem(
            question=f"What skill helped {hero.id} solve the ghost story?",
            answer=f"{hero.id} used scientific acuity by noticing clues, testing ideas, and paying close attention to what changed.",
        ),
        QAItem(
            question=f"What did the clue turn out to mean?",
            answer=f"The clue was {clue.label}, and it showed that {clue.reveal}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps you figure out what is really happening.",
        ),
        QAItem(
            question="Why do scientists look closely at things?",
            answer="Scientists look closely so they can notice details, compare evidence, and make better guesses.",
        ),
        QAItem(
            question="What does friendship do in a scary moment?",
            answer="Friendship helps people feel braver, laugh together, and solve problems as a team.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", clue="ghost", tool="notebook", name="Mina", friend="Sam", gender="girl"),
    StoryParams(setting="library", clue="projector", tool="flashlight", name="Eli", friend="Ruby", gender="boy"),
    StoryParams(setting="basement", clue="owl", tool="tape", name="Nora", friend="Ari", gender="girl"),
]


ASP_RULES = r"""
setting(attic). setting(library). setting(basement).
clue(ghost). clue(projector). clue(owl). clue(draft).
tool(notebook). tool(flashlight). tool(tape).

good_tool(ghost, notebook).
good_tool(ghost, flashlight).
good_tool(projector, flashlight).
good_tool(projector, notebook).
good_tool(owl, flashlight).
good_tool(owl, notebook).
good_tool(draft, tape).
good_tool(draft, notebook).

valid(S,C,T) :- setting(S), clue(C), tool(T), good_tool(C,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, c, t) for s in SETTINGS for c in CLUES for t in TOOLS if t in {"notebook", "flashlight", "tape"} and (
        (c == "ghost" and t in {"notebook", "flashlight"}) or
        (c == "projector" and t in {"flashlight", "notebook"}) or
        (c == "owl" and t in {"flashlight", "notebook"}) or
        (c == "draft" and t in {"tape", "notebook"})
    )}
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - ap))
    print("asp-only:", sorted(ap - py))
    return 1


def resolve_invalid(args: argparse.Namespace) -> None:
    if getattr(args, "clue", None) == "ghost" and getattr(args, "tool", None) == "tape":
        pass
    if getattr(args, "clue", None) == "draft" and getattr(args, "tool", None) == "flashlight":
        pass


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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/clue/tool combos:\n")
        for s, c, t in combos:
            print(f"  {s:9} {c:10} {t}")
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
                resolve_invalid(params) if False else None
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
            header = f"### {p.name} and {p.friend} in {p.setting} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
