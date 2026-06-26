#!/usr/bin/env python3
"""
storyworlds/worlds/efficiency_twist_teamwork_cautionary_heartwarming.py
========================================================================

A small story world about a child trying to do a job efficiently, learning a
cautionary twist, and finishing with teamwork and a warm, helpful ending.

Premise source tale:
---
A child wants to finish a little job quickly and neatly, because everyone is
busy. A grown-up warns that rushing can cause a spill or a mistake. The child
tries a shortcut anyway, and the shortcut backfires in a small, harmless way.
Then a helper joins in, they slow down, divide the work, and finish together.
In the end, the job is done well, the worry is gone, and the child feels proud
that working together was faster than hurrying alone.

World design:
- Physical state tracks supplies, mess, and readiness.
- Emotional state tracks eagerness, worry, embarrassment, relief, and pride.
- The twist is driven by a shortcut that looks efficient but is not careful.
- Teamwork resolves the problem by sharing tasks and restoring order.
- The ending must show the result of cooperation, not just repeat the setup.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    phrase: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    shortcut: str
    mess: str
    risk: str
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
class HelperPlan:
    id: str
    label: str
    prep: str
    tail: str
    roles: tuple[str, str]
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


THRESHOLD = 1.0
MESS_KINDS = {"wet", "sticky", "crumbly"}


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"juice", "snack"}),
    "workroom": Setting(place="the workroom", affords={"craft"}),
    "garden_table": Setting(place="the garden table", affords={"juice", "snack"}),
    "playroom": Setting(place="the playroom", affords={"craft"}),
}

TASKS = {
    "juice": Task(
        id="juice",
        verb="pour the juice cups",
        gerund="pouring juice",
        rush="rush to pour the juice all at once",
        shortcut="pour from the tallest jug without stopping",
        mess="wet",
        risk="spilled juice",
        zone={"table", "hands"},
        keyword="efficiency",
        tags={"juice", "spill", "wet"},
    ),
    "snack": Task(
        id="snack",
        verb="sort the snack plates",
        gerund="sorting snack plates",
        rush="hurry to stack the crackers and grapes",
        shortcut="pile everything into one big bowl",
        mess="crumbly",
        risk="crumbs all over the cloth",
        zone={"table", "hands"},
        keyword="efficiency",
        tags={"snack", "crumbs"},
    ),
    "craft": Task(
        id="craft",
        verb="build the paper lanterns",
        gerund="making paper lanterns",
        rush="fold the lanterns as fast as possible",
        shortcut="skip the drying step and glue too soon",
        mess="sticky",
        risk="glue sticking where it should not",
        zone={"table", "hands"},
        keyword="efficiency",
        tags={"craft", "glue"},
    ),
}

PRIZES = {
    "tablecloth": Prize(id="tablecloth", label="tablecloth", phrase="a clean blue tablecloth", region="table"),
    "shirt": Prize(id="shirt", label="shirt", phrase="a neat white shirt", region="torso"),
    "apron": Prize(id="apron", label="apron", phrase="a bright apron", region="torso"),
}

HELPERS = {
    "sibling": HelperPlan(
        id="sibling",
        label="little sister",
        prep="split the jobs and keep the cups steady",
        tail="set the last cup in place",
        roles=("hold", "count"),
    ),
    "friend": HelperPlan(
        id="friend",
        label="best friend",
        prep="divide the work into two neat parts",
        tail="tucked the final piece into place",
        roles=("carry", "check"),
    ),
    "parent": HelperPlan(
        id="parent",
        label="parent",
        prep="work slowly side by side",
        tail="smiled when the last bit was finished",
        roles=("wipe", "sort"),
    ),
}

NAMES = {
    "girl": ["Mina", "Lily", "Nora", "Ava", "Maya", "Zoe"],
    "boy": ["Leo", "Ben", "Finn", "Noah", "Eli", "Theo"],
}
TRAITS = ["careful", "eager", "quick", "helpful", "proud", "bright"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(task: Task, prize: Prize) -> bool:
    return prize.region in task.zone


def select_help(task: Task, prize: Prize) -> Optional[HelperPlan]:
    if not prize_at_risk(task, prize):
        return None
    return next(iter(HELPERS.values()))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = _safe_lookup(TASKS, task_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(task, prize) and select_help(task, prize):
                    combos.append((place, task_id, prize_id))
    return combos


def explain_rejection(task: Task, prize: Prize) -> str:
    return (
        f"(No story: {task.gerund} would not realistically threaten {prize.label}. "
        f"The cautionary twist needs a prize in the splash zone, so this combination is skipped.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(T, P) :- zone(T, R), region(P, R).
valid(Place, T, P) :- affords(Place, T), prize_at_risk(T, P), has_help(T, P).
has_help(T, P) :- prize_at_risk(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  only python:", sorted(py - cl))
    print("  only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def predict_mess(world: World, hero: Entity, task: Task, prize: Prize) -> bool:
    sim = world.copy()
    sim.zone = set(task.zone)
    if prize.region in sim.zone:
        return True
    return False


def resolve_task(world: World, hero: Entity, helper: Entity, task: Task, prize: Entity) -> None:
    hero.memes["pride"] += 1
    hero.memes["relief"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"{hero.id} and {helper.label} worked side by side. "
        f"They kept the little job neat, and soon {hero.pronoun('possessive')} {prize.label} stayed clean."
    )
    world.say(
        f"Their teamwork turned the busy job into an easy one, and {hero.id} felt proud that careful speed was better than a rushed shortcut."
    )


def tell(setting: Setting, task: Task, prize_cfg: Prize, name: str, gender: str, trait: str, helper_key: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"eagerness": 1.0}))
    helper_plan = _safe_lookup(HELPERS, helper_key)
    helper = world.add(Entity(id="Helper", kind="character", type="parent", label=helper_plan.label, memes={}))
    prize = world.add(Entity(id="Prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))

    # Setup
    world.say(f"{hero.id} was a {trait} little {gender} who liked doing things the efficient way.")
    world.say(f"At {setting.place}, {hero.id} wanted to {task.verb} before everyone got tired.")
    world.say(f"{hero.id}'s helper had brought {prize.phrase}, and it needed to stay neat.")
    prize.owner = hero.id
    world.facts.update(hero=hero, helper=helper, prize=prize, task=task, setting=setting, helper_plan=helper_plan)

    # Warning
    world.para()
    world.say(f"But {helper.label} gave a careful warning: \"If you {task.shortcut}, the {prize.label} could get {task.risk}.\"")
    hero.memes["eagerness"] += 1
    hero.memes["worry"] += 1

    # Twist
    if predict_mess(world, hero, task, prize):
        world.say(f"{hero.id} tried the shortcut anyway, and the twist came quickly.")
        hero.meters[task.mess] = hero.meters.get(task.mess, 0.0) + 1.0
        prize.meters[task.mess] = prize.meters.get(task.mess, 0.0) + 1.0
        hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1.0
        world.say(f"A little {task.mess} mess spread before anyone could stop it, and {hero.id} felt very sorry.")
    else:
        world.say(f"The shortcut did not cause trouble, but that would not make a strong cautionary story.")
    world.para()

    # Teamwork resolution
    helper_entity = helper
    helper_entity.memes["helpfulness"] = helper_entity.memes.get("helpfulness", 0.0) + 1.0
    world.say(f"Then {helper.label} came closer and said, \"Let's {helper_plan.prep}.\"")
    world.say(f"{hero.id} nodded, slowed down, and let the helper do the steady parts.")
    resolve_task(world, hero, helper_entity, task, prize)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task = f["hero"], f["task"]
    return [
        f'Write a warm, child-friendly story about {hero.id} and the word "efficiency" that ends with teamwork.',
        f"Tell a short cautionary story where {hero.id} tries to {task.shortcut} but learns that rushing can cause a mess.",
        f"Write a heartwarming story about doing a busy job quickly, making a small mistake, and fixing it together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, task = f["hero"], f["helper"], f["prize"], f["task"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do efficiently?",
            answer=f"{hero.id} wanted to {task.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What warning did {helper.label} give before the shortcut?",
            answer=f"{helper.label} warned that if {hero.id} rushed, the {prize.label} could get {task.risk}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} tried the shortcut anyway?",
            answer=f"The shortcut caused a small {task.mess} mess, so {hero.id} had to slow down and try again with help.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} and {helper.label} finished together, and the {prize.label} stayed clean.",
        ),
    ]


KNOWLEDGE = {
    "efficiency": [
        QAItem(
            question="What does efficiency mean?",
            answer="Efficiency means doing a job well without wasting time, work, or supplies.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and share the work to finish something together.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story shows a small mistake or warning so readers can learn to be careful.",
        )
    ],
    "heartwarming": [
        QAItem(
            question="What makes a story heartwarming?",
            answer="A heartwarming story leaves you with a kind, happy feeling because people care for one another.",
        )
    ],
    "shortcut": [
        QAItem(
            question="Why can a shortcut be risky?",
            answer="A shortcut can be risky if it skips an important careful step and causes a mistake.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    tags.update({"efficiency", "teamwork", "cautionary", "heartwarming", "shortcut"})
    out: list[QAItem] = []
    for tag in ["efficiency", "teamwork", "cautionary", "heartwarming", "shortcut"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    gender: str
    trait: str
    helper: str
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
    StoryParams("kitchen", "juice", "tablecloth", "Mina", "girl", "careful", "parent"),
    StoryParams("workroom", "craft", "apron", "Leo", "boy", "eager", "sibling"),
    StoryParams("garden_table", "snack", "shirt", "Nora", "girl", "helpful", "friend"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming efficiency story world with a cautionary twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "task", None) and getattr(args, "prize", None):
        task, prize = _safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not prize_at_risk(task, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task_id, prize_id = rng.choice(list(combos))
    task = _safe_lookup(TASKS, task_id)
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, task=task_id, prize=prize_id, name=name, gender=gender, trait=trait, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.trait, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
