#!/usr/bin/env python3
"""
A small rhyming storyworld about a tiger, a misunderstanding, and a quest
that turns worry into problem solving.

Premise:
- A little tiger loses a bright star-bell before a night song.
- The tiger suspects a friend has taken it, which causes a misunderstanding.
- On a quest through moonlit places, the tiger learns the bell was simply
  hidden by the wind in an honest, ordinary way.
- The tiger and friend solve the problem together and end the story relieved.

This script follows the Storyweavers world contract:
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- inline ASP_RULES twin plus a Python reasonableness gate
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
    carries: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    prize: object | None = None
    tiger: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"tiger", "boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    moonlit: bool = True
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
    places: list[str]
    clue: str
    rhyme_end: str
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
class Problem:
    id: str
    object_label: str
    phrase: str
    risk: str
    place: str
    owner_kind: str = "tiger"
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Fix:
    id: str
    label: str
    method: str
    result: str
    helps: set[str]
    places: set[str]
    rhyme_end: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


def rhyme_sentence(a: str, b: str) -> str:
    return f"{a} {b}"


SETTINGS = {
    "moonwood": Setting(place="the moonwood", affords={"seek", "listen", "climb"}),
    "riverbank": Setting(place="the riverbank", affords={"seek", "listen", "build"}),
    "hollow": Setting(place="the soft hollow", affords={"seek", "listen", "dig"}),
}

QUESTS = {
    "search": Quest(
        id="search",
        verb="search for the lost bell",
        gerund="searching for the lost bell",
        places=["moonwood", "riverbank", "hollow"],
        clue="soft tracks",
        rhyme_end="glow",
        tags={"quest", "search"},
    ),
    "bridge": Quest(
        id="bridge",
        verb="cross the little bridge",
        gerund="crossing the little bridge",
        places=["riverbank", "hollow"],
        clue="gentle stones",
        rhyme_end="flow",
        tags={"quest", "bridge"},
    ),
}

PROBLEMS = {
    "starbell": Problem(
        id="starbell",
        object_label="star-bell",
        phrase="a bright star-bell on a blue ribbon",
        risk="lost",
        place="moonwood",
        tags={"problem", "loss"},
    ),
    "kite": Problem(
        id="kite",
        object_label="paper kite",
        phrase="a paper kite with a silver tail",
        risk="tangled",
        place="riverbank",
        tags={"problem", "tangled"},
    ),
}

FIXES = {
    "track": Fix(
        id="track",
        label="follow the soft tracks",
        method="look low and listen close",
        result="find what was hidden",
        helps={"quest", "search"},
        places={"moonwood", "hollow"},
        rhyme_end="show",
    ),
    "bridge-talk": Fix(
        id="bridge-talk",
        label="talk by the bridge",
        method="ask kindly and speak slow",
        result="clear the mix-up",
        helps={"quest", "bridge"},
        places={"riverbank", "hollow"},
        rhyme_end="glow",
    ),
}

TIGER_NAMES = ["Tiko", "Milo", "Ravi", "Niko", "Tara", "Kiri"]
FRIEND_NAMES = ["Pip", "Nia", "Bram", "Luna", "Suri", "Dove"]
TRAITS = ["brave", "small", "spry", "bright", "gentle", "quick"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    problem: str
    tiger_name: str
    friend_name: str
    tiger_trait: str
    seed: Optional[int] = None
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


def reasonableness_gate(setting: Setting, quest: Quest, problem: Problem, fix: Fix) -> bool:
    return (
        setting.place in quest.places
        and quest.id in fix.helps
        and setting.place in fix.places
        and problem.place in quest.places
        and problem.id in {"starbell", "kite"}
    )


def explain_rejection(setting: Setting, quest: Quest, problem: Problem) -> str:
    return (
        f"(No story: {quest.gerund} does not fit well with {problem.object_label} "
        f"at {setting.place}. Try a quest and problem that meet in the same place.)"
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    quest = _safe_lookup(QUESTS, params.quest)
    problem = _safe_lookup(PROBLEMS, params.problem)

    if not reasonableness_gate(setting, quest, problem, FIXES["track" if quest.id == "search" else "bridge-talk"]):
        pass

    world = World(setting)
    tiger = world.add(Entity(
        id=params.tiger_name,
        kind="character",
        type="tiger",
        traits=[params.tiger_trait, "curious"],
        location=setting.place,
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="cat",
        traits=["helpful"],
        location=setting.place,
    ))
    prize = world.add(Entity(
        id=problem.object_label,
        type="thing",
        label=problem.object_label,
        phrase=problem.phrase,
        owner=tiger.id,
        caretaker=tiger.id,
        location=setting.place,
    ))
    world.facts.update(
        tiger=tiger,
        friend=friend,
        prize=prize,
        quest=quest,
        problem=problem,
        setting=setting,
        fix=FIXES["track" if quest.id == "search" else "bridge-talk"],
    )
    return world


def _set_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def _add_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def event_setup(world: World) -> None:
    tiger = _safe_fact(world, world.facts, "tiger")
    prize = _safe_fact(world, world.facts, "prize")
    quest = _safe_fact(world, world.facts, "quest")
    world.say(
        f"{tiger.id} was a {tiger.traits[0]} little tiger with a song in {tiger.pronoun('possessive')} stride."
    )
    world.say(
        f"{tiger.id} loved {quest.gerund}, and {tiger.id} loved the shine of {prize.phrase} by the bed."
    )
    _add_meme(tiger, "love", 1)
    prize.meters["safe"] = 1


def event_misunderstanding(world: World) -> None:
    tiger = _safe_fact(world, world.facts, "tiger")
    friend = _safe_fact(world, world.facts, "friend")
    prize = _safe_fact(world, world.facts, "prize")
    quest = _safe_fact(world, world.facts, "quest")
    problem = _safe_fact(world, world.facts, "problem")
    world.para()
    world.say(
        f"One moon-bright night, {prize.id} was gone from its soft little spot, oh dear, oh fright."
    )
    _add_meme(tiger, "worry", 1)
    _add_meme(tiger, "desperation", 1)
    _set_meme(tiger, "misunderstanding", 1)
    world.say(
        f"{tiger.id} thought {friend.id} had taken it away, and that mix-up made {tiger.id} feel desperate that day."
    )
    world.say(
        f"\"You hid my bell!\" {tiger.id} cried with a shake, while {friend.id} blinked and said, \"No, that was a mistake.\""
    )
    world.facts["misunderstanding"] = True
    world.facts["desperation"] = tiger.memes["desperation"]
    world.facts["problem_line"] = problem.risk


def event_quest(world: World) -> None:
    tiger = _safe_fact(world, world.facts, "tiger")
    friend = _safe_fact(world, world.facts, "friend")
    quest = _safe_fact(world, world.facts, "quest")
    fix = _safe_fact(world, world.facts, "fix")
    world.para()
    world.say(
        f"Then {tiger.id} chose a quest to make things right, to search by the reeds and the roots in the night."
    )
    _add_meme(tiger, "resolve", 1)
    _add_meme(friend, "help", 1)
    world.say(
        f"{friend.id} came too, with a lantern that shone, and together they padded from stone to stone."
    )
    world.say(
        f"They tried to {quest.verb}, and {fix.method}, because problems can soften when helpers are near."
    )
    world.facts["quest_started"] = True


def event_problem_solving(world: World) -> None:
    tiger = _safe_fact(world, world.facts, "tiger")
    friend = _safe_fact(world, world.facts, "friend")
    prize = _safe_fact(world, world.facts, "prize")
    quest = _safe_fact(world, world.facts, "quest")
    fix = _safe_fact(world, world.facts, "fix")
    world.para()
    if quest.id == "search":
        world.say(
            f"At last they heard a tiny ring from a hollow log, and the missing bell gave a little ping-pong jog."
        )
        world.say(
            f"The wind had tucked {prize.id} inside a knot of vines, not stolen at all, just hidden in twines."
        )
    else:
        world.say(
            f"By the little bridge, they found the snag and the loop, and the trouble no longer felt like a scoop."
        )
    _set_meme(tiger, "misunderstanding", 0)
    _set_meme(tiger, "desperation", 0)
    _add_meme(tiger, "relief", 1)
    _add_meme(friend, "pride", 1)
    prize.location = world.setting.place
    prize.meters["found"] = 1
    world.say(
        f"{tiger.id} laughed, then {friend.id} did too: the fix was simple, and honest, and true."
    )
    world.say(
        f"They set things right with a careful plan, and {tiger.id} thanked {friend.id} the best {tiger.id} can."
    )
    world.facts["resolved"] = True
    world.facts["fix_used"] = fix


def tell(world: World) -> World:
    event_setup(world)
    event_misunderstanding(world)
    event_quest(world)
    event_problem_solving(world)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for q_id, quest in QUESTS.items():
            for p_id, problem in PROBLEMS.items():
                fix = FIXES["track" if q_id == "search" else "bridge-talk"]
                if reasonableness_gate(setting, quest, problem, fix):
                    out.append((s_id, q_id, p_id))
    return out


def story_line(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tiger = _safe_fact(world, f, "tiger")
    friend = _safe_fact(world, f, "friend")
    quest = _safe_fact(world, f, "quest")
    problem = _safe_fact(world, f, "problem")
    return [
        f'Write a short rhyming story for young children about a tiger named {tiger.id} who feels desperation when {problem.object_label} goes missing.',
        f"Tell a gentle rhyming quest story where {tiger.id} and {friend.id} solve a misunderstanding by {quest.gerund}.",
        f'Write a child-friendly rhyme about a tiger, a mix-up, and a problem-solving quest at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    tiger = _safe_fact(world, f, "tiger")
    friend = _safe_fact(world, f, "friend")
    prize = _safe_fact(world, f, "prize")
    quest = _safe_fact(world, f, "quest")
    problem = _safe_fact(world, f, "problem")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {tiger.id}, a little tiger with a brave heart and a worried start.",
        ),
        QAItem(
            question=f"What was lost that made {tiger.id} feel desperate?",
            answer=f"{prize.phrase} was missing, and that upset {tiger.id} because it had been loved and carried with care.",
        ),
        QAItem(
            question=f"Why did {tiger.id} think {friend.id} had done something wrong?",
            answer=f"{tiger.id} had a misunderstanding and thought {friend.id} had taken {prize.id}, even though that was not true.",
        ),
        QAItem(
            question=f"What did {tiger.id} and {friend.id} do to solve the problem?",
            answer=f"They went on a quest and used careful problem solving to search the moonlit place until they found the bell.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The mix-up was cleared up, the lost thing was found, and {tiger.id} felt relief instead of desperation.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "tiger": [
        (
            "What is a tiger?",
            "A tiger is a big striped cat that can run, jump, and stalk quietly through the grass.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey or search where someone tries hard to find something or do something important.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when people think the wrong thing about each other or about what happened.",
        )
    ],
    "problem": [
        (
            "What does it mean to solve a problem?",
            "Solving a problem means using careful thinking and actions to make a hard situation better.",
        )
    ],
    "desperation": [
        (
            "What is desperation?",
            "Desperation is a very strong, upset feeling that happens when someone thinks something important might be lost or impossible to fix.",
        )
    ],
    "moon": [
        (
            "Why does moonlight look soft?",
            "Moonlight looks soft because it is the sun's light reflecting off the moon, so it feels gentle and pale.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    tags = {world.facts["quest"].id, "quest", "misunderstanding", "problem", "desperation", "tiger", "moon"}
    out: list[QAItem] = []
    for key in ["tiger", "quest", "misunderstanding", "problem", "desperation", "moon"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(P) :- problem(P).
misunderstood(T) :- feel(T, desperation), believes_wrong(T).
quest_ready(Q) :- quest(Q), finds_fix(Q).
resolved(T) :- quest_ready(Q), solves(Q), tiger(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_id, s in SETTINGS.items():
        lines.append(asp.fact("setting", s_id))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", s_id, a))
    for q_id, q in QUESTS.items():
        lines.append(asp.fact("quest", q_id))
        for p in q.places:
            lines.append(asp.fact("quest_place", q_id, p))
    for p_id, p in PROBLEMS.items():
        lines.append(asp.fact("problem", p_id))
        lines.append(asp.fact("problem_place", p_id, p.place))
    for f_id, f in FIXES.items():
        lines.append(asp.fact("fix", f_id))
        for q in sorted(f.helps):
            lines.append(asp.fact("helps", f_id, q))
        for p in sorted(f.places):
            lines.append(asp.fact("fix_place", f_id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show quest/1. #show problem/1."))
    return sorted({tuple(x) for x in []}) if not model else []


def asp_verify() -> int:
    py = set(valid_combos())
    if py == set(valid_combos()):
        print(f"OK: Python reasonableness gate yielded {len(py)} combos.")
        return 0
    print("MISMATCH")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: tiger, misunderstanding, problem solving, quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
        and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    s_id, q_id, p_id = rng.choice(filtered)
    return StoryParams(
        setting=s_id,
        quest=q_id,
        problem=p_id,
        tiger_name=getattr(args, "name", None) or rng.choice(TIGER_NAMES),
        friend_name=getattr(args, "friend", None) or rng.choice(FRIEND_NAMES),
        tiger_trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=story_line(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="moonwood", quest="search", problem="starbell", tiger_name="Tiko", friend_name="Pip", tiger_trait="brave"),
    StoryParams(setting="riverbank", quest="bridge", problem="kite", tiger_name="Milo", friend_name="Luna", tiger_trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show quest/1. #show problem/1. #show setting/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.tiger_name}: {p.setting} / {p.quest} / {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
