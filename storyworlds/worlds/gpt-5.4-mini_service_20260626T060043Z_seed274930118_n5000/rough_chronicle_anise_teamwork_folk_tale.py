#!/usr/bin/env python3
"""
storyworlds/worlds/rough_chronicle_anise_teamwork_folk_tale.py
===============================================================

A small folk-tale story world about a rough road, an anise bundle, and a village
chronicle that can only be completed through teamwork.

Seed tale:
---
In a little hill village, Old Mara kept a chronicle of every winter storm and
every shared meal. One autumn, the path to the herb garden turned rough after
the rain, and the villagers needed anise for a warming tea. But the chronicle
was unfinished, and the ink would smear if anyone carried it alone through the
wind.

So the villagers worked together: one held the lantern, one steadied the basket,
one carried the chronicle, and one gathered the anise. By sharing the load, they
kept the pages safe, brought home the herbs, and added one more kind line to the
book before the fire went low.

World model:
---
- physical meters: path roughness, wind, wetness, basket fullness, page safety
- emotional memes: worry, trust, pride, relief, togetherness
- teamwork is not decorative; it changes who can carry what, whether the ink
  stays dry, and whether the chronicle gains a new entry
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
    elder: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    path: str
    affords: set[str] = field(default_factory=set)
    folk_detail: str = ""
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
    risk: str
    zone: set[str]
    keyword: str
    result_phrase: str
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
    genders: set[str] = field(default_factory=lambda: {"woman", "man"})
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
class Aid:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        return clone


SETTINGS = {
    "hill_village": Setting(
        place="the hill village",
        path="the rough path to the herb garden",
        affords={"collect_anise", "carry_chronicle"},
        folk_detail="The chimneys breathed smoke over the low roofs, and the lane curled uphill like a ribbon.",
    ),
    "riverside_hamlet": Setting(
        place="the riverside hamlet",
        path="the rough stones by the riverbank",
        affords={"collect_anise", "carry_chronicle"},
        folk_detail="The river sang under the bridge, and the stones shone after the rain.",
    ),
}

TASKS = {
    "anise": Task(
        id="anise",
        verb="gather the anise",
        gerund="gathering anise",
        risk="the basket could spill",
        zone={"hands"},
        keyword="anise",
        result_phrase="brought home the anise for warm tea",
        tags={"anise", "herb"},
    ),
    "chronicle": Task(
        id="chronicle",
        verb="carry the chronicle",
        gerund="carrying the chronicle",
        risk="the pages could smear",
        zone={"hands", "torso"},
        keyword="chronicle",
        result_phrase="added a new page to the village chronicle",
        tags={"chronicle", "book"},
    ),
}

PRIZES = {
    "basket": Prize(
        id="basket",
        label="basket of anise",
        phrase="a basket of fresh anise sprigs",
        region="hands",
        plural=False,
        genders={"woman", "man"},
    ),
    "book": Prize(
        id="book",
        label="chronicle",
        phrase="the village chronicle with its soft paper pages",
        region="torso",
        plural=False,
        genders={"woman", "man"},
    ),
}

AIDS = [
    Aid(
        id="lantern",
        label="a lantern",
        covers={"path"},
        guards={"dark"},
        prep="hold the lantern high together",
        tail="held the lantern between them",
    ),
    Aid(
        id="cloth",
        label="a waxed cloth",
        covers={"hands", "torso"},
        guards={"wet", "smear"},
        prep="wrap the book in a waxed cloth first",
        tail="wrapped the chronicle in waxed cloth",
    ),
    Aid(
        id="rope",
        label="a rope sling",
        covers={"hands"},
        guards={"drop"},
        prep="use a rope sling for the book",
        tail="kept the chronicle in a rope sling",
    ),
]

NAMES = ["Mara", "Ivo", "Lina", "Bram", "Nessa", "Tomas", "Alma", "Jon", "Sera", "Oren"]
KINDS = ["woman", "man"]
TRAITS = ["steady", "kind", "patient", "brave", "quiet", "bright"]


def prize_at_risk(task: Task, prize: Prize) -> bool:
    return prize.region in task.zone


def select_aid(task: Task, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if prize.region in aid.covers and (task.id == "chronicle" and "smear" in aid.guards or task.id == "anise" and "drop" in aid.guards):
            return aid
    return None


ASP_RULES = r"""
task_risk(T, P) :- task(T), prize(P), zone(T, R), region(P, R).
aid_fits(A, T, P) :- aid(A), task_risk(T, P), covers(A, R), region(P, R),
                     task_id(T, chronicle), guards(A, smear).
aid_fits(A, T, P) :- aid(A), task_risk(T, P), covers(A, R), region(P, R),
                     task_id(T, anise), guards(A, drop).
valid(Place, T, P) :- affords(Place, T), task_risk(T, P), aid_fits(_, T, P).
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
        lines.append(asp.fact("task_id", tid, t.id))
        for z in sorted(t.zone):
            lines.append(asp.fact("zone", tid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, c))
        for g in sorted(aid.guards):
            lines.append(asp.fact("guards", aid.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for t in s.affords:
            task = _safe_lookup(TASKS, t)
            for p in PRIZES.values():
                if prize_at_risk(task, p) and select_aid(task, p):
                    combos.append((place, t, p.id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def _apply_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    actor.meters[task.id] = actor.meters.get(task.id, 0.0) + 1.0
    actor.memes["effort"] = actor.memes.get("effort", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} began {task.gerund} on the rough road.")


def predict(world: World, actor: Entity, task: Task, prize_id: str) -> dict:
    sim = world.copy()
    _apply_task(sim, sim.get(actor.id), task, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "ruined": task.id == "chronicle" and prize.meters.get("smear", 0.0) >= THRESHOLD,
        "basket_spilled": task.id == "anise" and prize.meters.get("spill", 0.0) >= THRESHOLD,
    }


def opening(world: World, elder: Entity, task: Task, prize: Prize) -> None:
    world.say(
        f"In {world.setting.place}, {elder.id} kept a chronicle of storms, bread, and birthdays."
    )
    world.say(
        f"{world.setting.folk_detail} Everyone knew that {task.verb} on {world.setting.path} was hard on small hands."
    )
    world.say(
        f"{elder.pronoun().capitalize()} especially wanted to {task.verb} before the lantern went low."
    )
    world.say(
        f"The village also needed {prize.phrase}, because the old folk liked warm tea with a sweet, sharp smell."
    )


def worry(world: World, elder: Entity, child: Entity, task: Task, prize: Prize) -> None:
    world.say(
        f"{child.id} looked at the rough path and sighed. '{task.risk.capitalize()},' {child.pronoun()} said."
    )
    world.say(
        f"But {elder.id} feared a lonely choice would leave the job slow and the pages unsafe."
    )
    elder.memes["worry"] = elder.memes.get("worry", 0.0) + 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0


def teamwork(world: World, team: list[Entity], task: Task, prize: Prize) -> Optional[Aid]:
    aid = select_aid(task, prize)
    if not aid:
        return None
    if task.id == "chronicle":
        world.say(
            f"Then they chose teamwork: one held {aid.label}, one walked ahead, and one steadied the book."
        )
    else:
        world.say(
            f"Then they chose teamwork: one held {aid.label}, one filled the basket, and one watched the stones."
        )
    return aid


def resolve(world: World, elder: Entity, child: Entity, task: Task, prize: Prize, aid: Aid) -> None:
    elder.memes["trust"] = elder.memes.get("trust", 0.0) + 1.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    elder.memes["relief"] = elder.memes.get("relief", 0.0) + 1.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    world.say(
        f"{aid.tail}, and the rough road felt shorter because no one carried the whole burden alone."
    )
    if task.id == "chronicle":
        world.say(
            f"The waxed cloth kept the pages dry, so the chronicle stayed clean even in the wind."
        )
        world.say(
            f"At the fire, {elder.id} wrote the new line at last: {task.result_phrase}."
        )
    else:
        world.say(
            f"The basket stayed steady, so {elder.id} and {child.id} {task.result_phrase}."
        )
        world.say(
            f"By the time the kettle sang, the house smelled of anise and safe hands."
        )


def tell(setting: Setting, task: Task, prize: Prize, elder_name: str, child_name: str, trait: str) -> World:
    world = World(setting)
    elder = world.add(Entity(id=elder_name, kind="character", type="woman", label="the elder"))
    child = world.add(Entity(id=child_name, kind="character", type="man", label="the helper"))
    opening(world, elder, task, prize)
    world.para()
    worry(world, elder, child, task, prize)
    aid = teamwork(world, [elder, child], task, prize)
    if aid is None:
        pass
    world.para()
    resolve(world, elder, child, task, prize, aid)
    world.facts.update(
        elder=elder,
        child=child,
        task=task,
        prize=prize,
        aid=aid,
        setting=setting,
        trait=trait,
        resolved=True,
    )
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about {f["elder"].id} and {f["child"].id} using teamwork on a rough road.',
        f'Tell a gentle story where a village chronicle and anise tea both matter, and the helpers keep working together.',
        f'Write a child-friendly tale that includes the words "rough", "chronicle", and "anise".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    elder, child, task, prize, aid = f["elder"], f["child"], f["task"], f["prize"], f["aid"]
    return [
        QAItem(
            question=f"What did {elder.id} need to do on the rough path?",
            answer=f"{elder.id} needed to {task.verb}, and the villagers did it together so the job would be safe.",
        ),
        QAItem(
            question=f"Why did they need teamwork?",
            answer=(
                f"They needed teamwork because the rough road and the wind made the job harder, "
                f"and {aid.label} helped keep the load steady."
            ),
        ),
        QAItem(
            question=f"What happened to the {prize.label} by the end?",
            answer=(
                f"The {prize.label} stayed safe. The group used {aid.label} and carried it together "
                f"so nothing was ruined."
            ),
        ),
        QAItem(
            question=f"What new thing did the story add to the chronicle?",
            answer=(
                f"It added a new page about the village working as one, and that is how the chronicle grew."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does anise smell like?",
            answer="Anise has a sweet, sharp smell, a little like licorice, and people often use it to flavor tea or bread.",
        ),
        QAItem(
            question="What is a chronicle?",
            answer="A chronicle is a book or record that tells what happened over time.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share the work and help one another so a hard job becomes easier.",
        ),
    ]


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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    elder: str
    child: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world of rough paths, anise, and a village chronicle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--elder")
    ap.add_argument("--child")
    ap.add_argument("--trait")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        task=task,
        prize=prize,
        elder=getattr(args, "elder", None) or rng.choice(NAMES),
        child=getattr(args, "child", None) or rng.choice(NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), params.elder, params.child, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
    StoryParams(place="hill_village", task="chronicle", prize="book", elder="Mara", child="Ivo", trait="steady"),
    StoryParams(place="riverside_hamlet", task="anise", prize="basket", elder="Lina", child="Bram", trait="kind"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, task, prize) combos:\n")
        for place, task, prize in triples:
            print(f"  {place:18} {task:10} {prize}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
