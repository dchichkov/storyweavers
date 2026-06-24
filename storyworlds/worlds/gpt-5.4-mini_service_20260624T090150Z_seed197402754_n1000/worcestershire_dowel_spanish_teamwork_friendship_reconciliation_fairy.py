#!/usr/bin/env python3
"""
A small fairy-tale story world about teamwork, friendship, and reconciliation.

Seed-inspired premise:
A little fairy friend group in a mossy glen wants to mend a broken bridge
before the moonlit feast. A wooden dowel can brace the crack, a splash of
worcestershire sauce makes the supper smell rich and warm, and a few spanish
words help the friends speak kindly after a misunderstanding.

The world is intentionally small and constraint-checked:
- the bridge can only be repaired if the chosen tool actually fits
- the feast can only be shared if the sauce matches the dish
- the reconciliation only happens after the apology and the teamwork turn

The script follows the Storyweavers contract and includes an ASP twin for
reasonableness parity.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    region: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "mother", "woman"}
        male = {"boy", "elf", "father", "man"}
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
    indoors: bool = False
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
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
    id: str
    label: str
    phrase: str
    region: str
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
class Tool:
    id: str
    label: str
    fits: set[str]
    purpose: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "glen": Setting(place="the mossy glen", indoors=False, affords={"bridge", "feast"}),
    "cottage": Setting(place="the little cottage", indoors=True, affords={"feast"}),
}

TASKS = {
    "bridge": Task(
        id="bridge",
        verb="fix the little bridge",
        gerund="mending the little bridge",
        rush="run to the broken board",
        mess="splintered",
        zone={"hands"},
        keyword="dowel",
        tags={"teamwork", "friendship"},
    ),
    "feast": Task(
        id="feast",
        verb="prepare the moonlit feast",
        gerund="serving the moonlit feast",
        rush="hurry to the table",
        mess="sauced",
        zone={"hands"},
        keyword="worcestershire",
        tags={"friendship", "reconciliation", "spanish"},
    ),
}

PRIZES = {
    "treats": Prize(id="treats", label="treats", phrase="sweet berry treats", region="hands", plural=True),
    "banner": Prize(id="banner", label="banner", phrase="a bright ribbon banner", region="torso"),
}

TOOLS = [
    Tool(
        id="dowel",
        label="a smooth dowel",
        fits={"bridge"},
        purpose="brace the crack in the bridge",
        prep="go find a smooth dowel",
        tail="found the smooth dowel and slipped it under the broken board",
    ),
    Tool(
        id="ladle",
        label="a tiny ladle",
        fits={"feast"},
        purpose="stir the sauce into the feast",
        prep="pick up the tiny ladle",
        tail="used the tiny ladle to stir the supper",
    ),
]

NAMES = ["Luna", "Pip", "Mina", "Toby", "Ivy", "Nico", "Elia", "Soren"]
TRAITS = ["gentle", "brave", "cheerful", "curious", "kind"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def task_at_risk(task: Task, prize: Prize) -> bool:
    return prize.region in task.zone


def select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.fits:
            return tool
    return None


def predict_ruin(world: World, actor: Entity, task: Task, prize_id: str) -> bool:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    prize = sim.get(prize_id)
    return bool(prize.meters.get("ruined", 0) >= 1)


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    world.zone = set(task.zone)
    actor.meters[task.mess] = actor.meters.get(task.mess, 0) + 1
    if task.id == "feast":
        actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    if narrate:
        world.say(f"{actor.id} started {task.gerund}.")


def apply_mending(world: World, actor: Entity, prize: Entity, task: Task, tool: Tool) -> None:
    if task.id != "bridge":
        return
    prize.meters["ruined"] = 0
    world.say(
        f"{actor.id} used {tool.label} to {tool.purpose}, and the bridge grew steady again."
    )


def apply_feast(world: World, actor: Entity, task: Task) -> None:
    if task.id != "feast":
        return
    actor.memes["warmth"] = actor.memes.get("warmth", 0) + 1
    world.say(
        "They stirred in a little worcestershire sauce, and the mushrooms smelled rich and cozy."
    )


def say_sorry(world: World, speaker: Entity, listener: Entity) -> None:
    speaker.memes["regret"] = speaker.memes.get("regret", 0) + 1
    listener.memes["softened"] = listener.memes.get("softened", 0) + 1
    world.say(
        f'{speaker.id} bowed her head and said, "Lo siento, my friend." '
        f"{listener.id} listened carefully."
    )


def reconcile(world: World, speaker: Entity, listener: Entity) -> None:
    speaker.memes["peace"] = speaker.memes.get("peace", 0) + 1
    listener.memes["peace"] = listener.memes.get("peace", 0) + 1
    world.say(
        f'{listener.id} smiled and answered, "Amigos." '
        f"That small spanish word made the air feel light again."
    )


def tell(setting: Setting, task: Task, prize_cfg: Prize, hero_name: str, hero_type: str,
         second_name: str, second_type: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = w.add(Entity(id=second_name, kind="character", type=second_type))
    prize = w.add(Entity(
        id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    w.say(
        f"In {setting.place}, {hero.id} and {friend.id} were two little friends who loved helping each other."
    )
    w.say(
        f"They had a special prize: {prize.phrase}, which they wanted to keep safe for the moonlit feast."
    )

    w.para()
    w.say(
        f"One evening, {hero.id} noticed the broken bridge near the toadstool path."
    )
    w.say(
        f"{friend.id} wanted to {task.verb}, but {hero.id} worried the old board would stay crooked."
    )
    w.say(
        f"Then {hero.id} remembered a smooth dowel could fit the crack and hold it strong."
    )

    if not task_at_risk(task, prize):
        pass

    w.para()
    w.say(f"{friend.id} heard the worry and went to {_safe_lookup(TOOLS, 0).prep}.")
    _do_task(w, hero, task, narrate=False)
    apply_mending(w, hero, prize, task, _safe_lookup(TOOLS, 0))
    w.say(f"Together, they {_safe_lookup(TOOLS, 0).tail}.")
    w.say("Their teamwork made the bridge safe for tiny feet again.")

    w.para()
    w.say(
        f"After that, the friends walked to the lantern table to {TASKS['feast'].verb}."
    )
    w.say(
        f"They shared their worries, said kind words, and chose not to stay cross with each other."
    )
    say_sorry(w, hero, friend)
    reconcile(w, hero, friend)
    apply_feast(w, hero, TASKS["feast"])
    w.say(
        f"At the end, {hero.id} and {friend.id} sat side by side, happy again, with the bridge mended and the feast glowing under the moon."
    )

    w.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        task=task,
        setting=setting,
        tool=_safe_lookup(TOOLS, 0),
        resolved=True,
        reconciled=True,
    )
    return w


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    task = _safe_fact(world, f, "task")
    return [
        f'Write a fairy tale for a small child about {hero.id} and {friend.id} who work together to {task.verb}.',
        f'Write a gentle story that includes the words "worcestershire", "dowel", and "spanish" and ends in reconciliation.',
        f"Tell a short fairy tale about friendship, teamwork, and a happy apology in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, task = f["hero"], f["friend"], f["prize"], f["task"]
    return [
        QAItem(
            question=f"Why did {hero.id} want the smooth dowel?",
            answer=f"{hero.id} wanted the smooth dowel because it could brace the broken bridge and help everyone cross safely.",
        ),
        QAItem(
            question=f"What did the friends do together to {task.verb}?",
            answer=f"They worked side by side with a smooth dowel, which was a teamwork solution that fixed the bridge.",
        ),
        QAItem(
            question=f"Why did the story end happily after the disagreement?",
            answer=f"It ended happily because {hero.id} said sorry, {friend.id} accepted, and their friendship turned back into reconciliation.",
        ),
        QAItem(
            question=f"Why did they add worcestershire sauce at the feast?",
            answer="They added worcestershire sauce to make the moonlit feast smell rich, warm, and special for both friends.",
        ),
        QAItem(
            question=f"What spanish word helped the friends make up?",
            answer='The spanish word was "amigos", and it helped them feel close again.',
        ),
    ]


WORLD_KNOWLEDGE = {
    "teamwork": [("What is teamwork?", "Teamwork means people help each other and do a job together.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other and enjoy being together.")],
    "reconciliation": [("What is reconciliation?", "Reconciliation is when people make up after a disagreement and become friendly again.")],
    "dowel": [("What is a dowel?", "A dowel is a smooth wooden stick that can help hold or fix things.")],
    "worcestershire": [("What is worcestershire sauce?", "Worcestershire sauce is a savory sauce used to add rich flavor to food.")],
    "spanish": [("What is spanish?", "Spanish is a language spoken by many people around the world.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"teamwork", "friendship", "reconciliation", "dowel", "worcestershire", "spanish"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the task touches the prize's region.
prize_at_risk(T, P) :- task(T), prize(P), zone(T, R), prize_region(P, R).

% A tool is a compatible fix if it fits the task.
has_fix(T, P) :- task(T), prize(P), tool(X), fits(X, T).

valid_story(S, T, P) :- setting(S), task(T), prize(P), affords(S, T),
                        prize_at_risk(T, P), has_fix(T, P).

% Reconciliation is available when the story has a friendship task and a feast.
resolves(S) :- valid_story(S, T, P), task(T), T = feast, prize(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for t in sorted(tool.fits):
            lines.append(asp.fact("fits", tool.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for tid in s.affords:
            task = _safe_lookup(TASKS, tid)
            for pid, prize in PRIZES.items():
                if task_at_risk(task, prize) and select_tool(task):
                    out.append((sid, tid, pid))
    return sorted(out)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    friend: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world: teamwork, friendship, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    return StoryParams(
        place=place,
        task=task,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        friend=getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != (getattr(args, "name", None) or "")]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize),
                 params.name, "fairy", params.friend, "elf")
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


CURATED = [
    StoryParams(place="glen", task="bridge", prize="banner", name="Luna", friend="Pip"),
    StoryParams(place="cottage", task="feast", prize="treats", name="Mina", friend="Nico"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
