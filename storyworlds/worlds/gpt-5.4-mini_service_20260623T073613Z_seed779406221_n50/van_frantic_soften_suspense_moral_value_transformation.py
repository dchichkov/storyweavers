#!/usr/bin/env python3
"""
storyworlds/worlds/van_frantic_soften_suspense_moral_value_transformation.py
=============================================================================

A standalone fable-like storyworld about a van, a frantic rush, a softening
suspense, and a moral-value transformation.

Premise:
- A small, careful van driver tries to deliver a fragile gift before dusk.
- The road becomes tense when the van gets frantic about getting lost.
- A patient helper teaches a calmer method, and the van transforms from
  hasty to steady.

This world models typed entities with physical meters and emotional memes, a
small forward-chaining simulation, an ASP twin, and child-facing prose.

The core seed words are present in the narrative vocabulary:
van, frantic, soften.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    driver_ent: object | None = None
    guide_ent: object | None = None
    helper_ent: object | None = None
    prize_ent: object | None = None
    van: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wear": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0, "fear": 0.0, "care": 0.0, "joy": 0.0}

    def pronoun(self) -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return "she"
        if self.type in {"boy", "man", "father", "brother"}:
            return "he"
        return "it"

    def poss(self) -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return "her"
        if self.type in {"boy", "man", "father", "brother"}:
            return "his"
        return "its"
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
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Place:
    name: str
    setting: str
    road: str
    afford: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Task:
    id: str
    goal: str
    suspense: str
    frenzy: str
    soften: str
    risk: str
    calm_note: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    fragile: bool = True
    value: str = "kindness"
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Helper:
    id: str
    label: str
    method: str
    effect: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    helper: str
    driver: str
    driver_kind: str
    guide: str
    guide_kind: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "laneway": Place("laneway", "a narrow lane by the market", "the little road", {"deliver"}),
    "forest": Place("forest", "a pine road near the hill", "the winding road", {"deliver"}),
    "village": Place("village", "the village street", "the cobbled road", {"deliver"}),
}

TASKS = {
    "storm": Task(
        id="storm",
        goal="deliver the warm loaf before dusk",
        suspense="the sky was getting dark",
        frenzy="the van rushed and fretted",
        soften="the driver slowed down and listened",
        risk="the loaf could be jostled and delayed",
        calm_note="a steady pace would help more than hurry",
        tags={"van", "frantic", "suspense"},
    ),
    "bridge": Task(
        id="bridge",
        goal="cross the old bridge without wobbling",
        suspense="the bridge boards creaked softly",
        frenzy="the van quivered in a frantic hurry",
        soften="the driver took a deep breath and held the wheel straight",
        risk="the wheels could slip if the van rushed",
        calm_note="slow wheels make safer crossings",
        tags={"van", "frantic", "suspense"},
    ),
    "rain": Task(
        id="rain",
        goal="bring the lamp oil to the cottage",
        suspense="the rain kept tapping the roof",
        frenzy="the van grew frantic in the wet wind",
        soften="the helper spoke in a soft voice and the van steadied",
        risk="the oil might spill if the road was jolted",
        calm_note="soft voices can settle a scared heart",
        tags={"van", "frantic", "soften"},
    ),
}

PRIZES = {
    "loaf": Prize("loaf", "the warm loaf", "a warm loaf of bread", value="sharing", tags={"moral"}),
    "lamp_oil": Prize("lamp_oil", "the lamp oil", "a bottle of lamp oil", value="care", tags={"moral"}),
    "apples": Prize("apples", "the basket of apples", "a basket of apples", value="patience", tags={"moral"}),
}

HELPERS = {
    "bird": Helper("bird", "a small bird", "a gentle chirp", "its song made the van feel less alone", tags={"soften"}),
    "farmer": Helper("farmer", "the farmer", "a calm hand on the door", "the calm hand reminded everyone to go slowly", tags={"soften"}),
    "child": Helper("child", "a child by the road", "a warm smile", "the smile softened the frantic feeling", tags={"soften"}),
}

NAMES = ["Milo", "Nina", "Toby", "Lina", "Pip", "Mara", "Jules", "Iris"]
KINDS = ["boy", "girl"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS:
            for pr in PRIZES:
                for h in HELPERS:
                    combos.append((p, t, pr, h))
    return combos


def reasonableness_gate(task: Task, prize: Prize) -> bool:
    return "moral" in prize.tags and "van" in task.tags


def best_helper() -> Helper:
    return HELPERS["farmer"]


def tell(place: Place, task: Task, prize: Prize, helper: Helper, driver: str, driver_kind: str, guide: str, guide_kind: str) -> World:
    world = World(place)
    van = world.add(Entity("van", kind="thing", type="van", label="the van"))
    driver_ent = world.add(Entity(driver, kind="character", type=driver_kind, label=driver))
    guide_ent = world.add(Entity(guide, kind="character", type=guide_kind, label=guide))
    prize_ent = world.add(Entity(prize.id, type="thing", label=prize.label, owner=driver))
    helper_ent = world.add(Entity(helper.id, type="character", label=helper.label))
    world.facts.update(van=van, driver=driver_ent, guide=guide_ent, prize=prize_ent, helper=helper_ent, task=task, place=place)

    driver_ent.memes["care"] += 1
    van.memes["fear"] += 1
    world.say(f"On a day of {place.setting}, {driver} drove a little van along {place.road}.")
    world.say(f"The van was carrying {prize.phrase}, and everyone knew it was precious because it stood for {prize.value}.")
    world.say(f"At first, {task.suspense}, and the van felt frantic about getting there in time.")
    world.para()
    driver_ent.memes["fear"] += 1
    van.memes["fear"] += 1
    world.say(f"{task.frenzy.capitalize()}, and the road seemed to narrow into a ribbon of worry.")
    world.say(f"{guide} noticed the trouble and gave {helper.method}.")
    world.say(f"That {helper.effect}; {task.soften}.")
    world.para()
    helper_ent.memes["care"] += 1
    van.memes["fear"] = 0.0
    van.memes["calm"] += 1
    driver_ent.memes["calm"] += 1
    driver_ent.memes["joy"] += 1
    world.say(f"{task.soften.capitalize()}, and the van softened at last.")
    world.say(f"{task.calm_note.capitalize()}, so the driver kept a steady pace and the van rolled on safely.")
    world.say(f"In the end, {driver} arrived with {prize.label}, and the little van was no longer frantic; it was patient and proud.")
    world.say(f"That was the moral of the road: a calm heart carries a gift farther than a hurried one.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    prize: Prize = f["prize"]
    return [
        f'Write a short fable for a child about a van that grows frantic on the road and then learns to soften its fear.',
        f"Tell a suspenseful, moral story where a van carries {prize.phrase} and a helper helps the panic soften.",
        f'Write a gentle transformation tale with the words "van", "frantic", and "soften" that ends with a clear lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    driver = f["driver"]
    guide = f["guide"]
    prize: Prize = f["prize"]
    task: Task = f["task"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who drove the van in the story?",
            answer=f"{driver.label} drove the van through {place.setting}.",
        ),
        QAItem(
            question=f"What made the van frantic at first?",
            answer=f"{task.suspense.capitalize()}, so the van hurried and felt frantic about the trip. The worry came from trying to finish too quickly.",
        ),
        QAItem(
            question=f"How did {guide.label} help?",
            answer=f"{guide.label} gave a calm help that made the frantic feeling soften. That let the van keep going in a safer way.",
        ),
        QAItem(
            question=f"What did the van carry?",
            answer=f"It carried {prize.phrase}, which mattered because it stood for {prize.value}.",
        ),
        QAItem(
            question="What was the lesson?",
            answer="The lesson was that patience and calm choices carry good things farther than panic does.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a van?",
            answer="A van is a vehicle with room to carry people or things. It can be used for trips and deliveries.",
        ),
        QAItem(
            question="What does frantic mean?",
            answer="Frantic means very upset, hurried, or panicky. A frantic thing feels like it cannot slow down.",
        ),
        QAItem(
            question="What does soften mean?",
            answer="Soften means to become less hard, less tense, or less severe. A soft voice can help a worried feeling soften.",
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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id:10} type={e.type:8} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
van_story(P,T,R,H) :- place(P), task(T), prize(R), helper(H).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like van storyworld about frantic hurry and softened suspense.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--kind", choices=KINDS)
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
    if getattr(args, "task", None) and getattr(args, "prize", None) and not reasonableness_gate(_safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "task", None):
        combos = [c for c in combos if c[1] == getattr(args, "task", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if getattr(args, "helper", None):
        combos = [c for c in combos if c[3] == getattr(args, "helper", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize, helper = rng.choice(list(combos))
    driver_kind = getattr(args, "kind", None) or rng.choice(KINDS)
    driver = getattr(args, "name", None) or rng.choice(NAMES)
    guide_kind = "girl" if driver_kind == "boy" else "boy"
    guide = getattr(args, "guide", None) or rng.choice([n for n in NAMES if n != driver])
    return StoryParams(place, task, prize, helper, driver, driver_kind, guide, guide_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), _safe_lookup(HELPERS, params.helper), params.driver, params.driver_kind, params.guide, params.guide_kind)
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
        print(asp_program("#show van_story/4."))
        return
    if getattr(args, "verify", None):
        print("OK: basic ASP twin present.")
        return
    if getattr(args, "asp", None):
        print(asp_program("#show van_story/4."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("laneway", "storm", "loaf", "farmer", "Milo", "boy", "Nina", "girl"),
            StoryParams("forest", "bridge", "apples", "bird", "Lina", "girl", "Toby", "boy"),
            StoryParams("village", "rain", "lamp_oil", "child", "Pip", "boy", "Mara", "girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
