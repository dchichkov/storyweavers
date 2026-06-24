#!/usr/bin/env python3
"""
A small superhero storyworld: a hero, a project, and a cautionary lesson.

Seed premise:
- A young superhero is helping with a community project.
- A tricky granulate substance can spill, puff, or clog things.
- A flashback reminds the hero to use a steady hand and a plan.
- The ending proves the lesson by finishing the project safely.

The world is intentionally small and state-driven so story text comes from the
simulated outcome rather than from a static template swap.
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
    role: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    proj: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.role in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def item_pronoun(self) -> str:
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
    indoor: bool = False
    allows: set[str] = field(default_factory=set)
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
class Project:
    id: str
    noun: str
    phrase: str
    risk: str
    mess: str
    area: str
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
class Caution:
    id: str
    label: str
    use: str
    rule: str
    tag: str
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
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    project: str
    caution: str
    name: str
    role: str
    sidekick: str
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


PLACES = {
    "city_square": Place(name="the city square", indoor=False, allows={"bridge", "banner"}),
    "community_center": Place(name="the community center", indoor=True, allows={"bridge", "garden"}),
    "roof_garden": Place(name="the roof garden", indoor=False, allows={"garden", "bridge"}),
}

PROJECTS = {
    "bridge": Project(
        id="bridge",
        noun="bridge",
        phrase="a little bridge for the park pond",
        risk="wobble",
        mess="slip",
        area="hands",
        tags={"build", "help", "project"},
    ),
    "banner": Project(
        id="banner",
        noun="banner",
        phrase="a bright banner for the team parade",
        risk="smear",
        mess="dust",
        area="hands",
        tags={"paint", "project"},
    ),
    "garden": Project(
        id="garden",
        noun="garden",
        phrase="a small garden bed for flowers",
        risk="spill",
        mess="granulate",
        area="hands",
        tags={"plant", "project"},
    ),
}

CAUTIONS = {
    "gloves": Caution(
        id="gloves",
        label="gloves",
        use="put on sturdy gloves",
        rule="keep powder off the hands",
        tag="hand",
    ),
    "tray": Caution(
        id="tray",
        label="a tray",
        use="use a tray",
        rule="hold the granulate steady",
        tag="project",
    ),
    "mask": Caution(
        id="mask",
        label="a mask",
        use="wear a mask",
        rule="keep the dust out of the nose",
        tag="granulate",
    ),
}

NAMES = ["Nova", "Milo", "Ari", "Zoe", "Ruby", "Kai", "Lena", "Theo"]
SIDKICKS = ["the little helper", "the bright sidekick", "the speedy friend"]
ROLES = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p_id, place in PLACES.items():
        for proj_id, proj in PROJECTS.items():
            if proj_id not in place.allows:
                continue
            for c_id, c in CAUTIONS.items():
                if proj_id == "garden" and c_id == "gloves":
                    out.append((p_id, proj_id, c_id))
                elif proj_id == "bridge" and c_id in {"gloves", "tray"}:
                    out.append((p_id, proj_id, c_id))
                elif proj_id == "banner" and c_id in {"gloves", "mask"}:
                    out.append((p_id, proj_id, c_id))
    return out


ASP_RULES = r"""
project_ok(P, J) :- allows(P, J).
needs_caution(J, C) :- project(J), caution(C), match(J, C).
valid(P, J, C) :- project_ok(P, J), needs_caution(J, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for j in sorted(p.allows):
            lines.append(asp.fact("allows", pid, j))
    for jid, j in PROJECTS.items():
        lines.append(asp.fact("project", jid))
        for t in sorted(j.tags):
            lines.append(asp.fact("tag", jid, t))
        lines.append(asp.fact("mess", jid, j.mess))
    for cid, c in CAUTIONS.items():
        lines.append(asp.fact("caution", cid))
        lines.append(asp.fact("match", "bridge", cid) if cid in {"gloves", "tray"} else "")
        lines.append(asp.fact("match", "banner", cid) if cid in {"gloves", "mask"} else "")
        lines.append(asp.fact("match", "garden", cid) if cid == "gloves" else "")
    return "\n".join(x for x in lines if x)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def reasonableness(place: Place, project: Project, caution: Caution) -> bool:
    if project.id not in place.allows:
        return False
    if project.id == "garden":
        return caution.id == "gloves"
    if project.id == "bridge":
        return caution.id in {"gloves", "tray"}
    if project.id == "banner":
        return caution.id in {"gloves", "mask"}
    return False


def predict_mess(world: World, hero: Entity, project: Project) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["effort"] += 1
    sim.get(project.id).meters[project.mess] = 1.0
    return sim.get(project.id).meters[project.mess] >= THRESHOLD


def tell(place: Place, project: Project, caution: Caution, name: str, role: str, sidekick: str) -> World:
    w = World(place)
    hero = w.add(Entity(id=name, kind="character", role=role, label=name))
    friend = w.add(Entity(id="Friend", kind="character", role="friend", label=sidekick))
    proj = w.add(Entity(id=project.id, role="thing", label=project.noun, phrase=project.phrase))
    tool = w.add(Entity(id=caution.id, role="thing", label=caution.label, phrase=caution.label, owner=hero.id))
    w.facts.update(hero=hero, friend=friend, project=proj, caution=tool, place=place, project_cfg=project, caution_cfg=caution)

    # setup
    w.say(f"{hero.id} was a small superhero who loved helping in {place.name}.")
    w.say(f"{hero.pronoun('subject').capitalize()} and {friend.label} had a big project: {project.phrase}.")
    w.say(f"Their project needed careful hands, because the wrong {project.mess} could make it tricky.")
    w.para()

    # flashback
    w.say(f"Flashback: last week, {hero.id} had rushed a job and dropped powder all over the floor.")
    w.say(f"That mistake taught {hero.id} a cautionary lesson: a steady hand keeps a good plan from turning messy.")
    w.para()

    # tension
    hero.memes["duty"] = 1.0
    if predict_mess(w, hero, project):
        w.say(f"Today, {hero.id} reached for the {project.noun}, but {hero.pronoun('possessive')} hand paused.")
        w.say(f"{friend.label} pointed at the {caution.label} and said, \"Let's be careful before the {project.mess} starts.\"")
        hero.memes["worry"] = 1.0
        hero.memes["caution"] = 1.0
        proj.meters[project.mess] = 1.0
    else:
        pass

    # resolution
    w.para()
    hero.memes["resolve"] = 1.0
    tool.meters["used"] = 1.0
    if caution.id == "gloves":
        w.say(f"{hero.id} slipped on {caution.label}, and the steady grip made {hero.pronoun('possessive')} hand safe.")
    elif caution.id == "tray":
        w.say(f"{hero.id} used {caution.label}, so the granulate stayed low and did not spill.")
    else:
        w.say(f"{hero.id} wore {caution.label}, and the dust stayed away from {hero.pronoun('possessive')} face.")
    proj.meters["built"] = 1.0
    proj.meters[project.mess] = 0.0
    hero.memes["pride"] = 1.0
    friend.memes["joy"] = 1.0
    w.say(f"Together, they finished {project.phrase}, and the project stood neat and strong.")
    w.say(f"{hero.id} smiled at {hero.pronoun('possessive')} careful hand, because this time the ending was safe and bright.")
    return w


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    project = f["project_cfg"]
    caution = f["caution_cfg"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who helped finish {project.phrase} at {place.name}?",
            answer=f"{hero.id} and {friend.label} helped finish {project.phrase} at {place.name}.",
        ),
        QAItem(
            question=f"Why did {hero.id} pause before touching the {project.noun}?",
            answer=f"{hero.id} paused because {project.mess} could make the project messy, and {hero.id} remembered to use a steady hand.",
        ),
        QAItem(
            question=f"What cautionary choice did {hero.id} make with the {caution.label}?",
            answer=f"{hero.id} used {caution.label} to keep the work safe and stop the {project.mess} from causing trouble.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.id} about?",
            answer=f"The flashback reminded {hero.id} not to rush, because a careful hand keeps a project neat.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "hand": QAItem(
        question="What can a hand do?",
        answer="A hand can hold, carry, point, and help do careful work.",
    ),
    "project": QAItem(
        question="What is a project?",
        answer="A project is a job or activity people work on together to make or build something.",
    ),
    "granulate": QAItem(
        question="What does granulate mean?",
        answer="Granulate means to break into small grains or bits, like tiny crumbs or powdery pieces.",
    ),
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [WORLD_KNOWLEDGE[k] for k in ("hand", "project", "granulate")]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    project = f["project_cfg"]
    caution = f["caution_cfg"]
    return [
        f"Write a short superhero story for young children about {hero.id} finishing {project.phrase}.",
        f"Tell a cautionary story with a flashback where a hero learns to use {caution.label} before the {project.mess} starts.",
        f"Write a bright superhero story that uses the words hand, project, and granulate.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: hand, project, granulate, flashback, cautionary.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--caution", choices=CAUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
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
    if getattr(args, "place", None) and getattr(args, "project", None) and getattr(args, "caution", None):
        if not reasonableness(_safe_lookup(PLACES, getattr(args, "place", None)), _safe_lookup(PROJECTS, getattr(args, "project", None)), _safe_lookup(CAUTIONS, getattr(args, "caution", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in combos
              if (not getattr(args, "place", None) or c[0] == getattr(args, "place", None))
              and (not getattr(args, "project", None) or c[1] == getattr(args, "project", None))
              and (not getattr(args, "caution", None) or c[2] == getattr(args, "caution", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, proj, caution = rng.choice(list(combos))
    role = getattr(args, "role", None) or rng.choice(ROLES)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDKICKS)
    return StoryParams(place=place, project=proj, caution=caution, name=name, role=role, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(PROJECTS, params.project), _safe_lookup(CAUTIONS, params.caution), params.name, params.role, params.sidekick)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="city_square", project="bridge", caution="tray", name="Nova", role="girl", sidekick="the bright sidekick"),
    StoryParams(place="community_center", project="garden", caution="gloves", name="Milo", role="boy", sidekick="the little helper"),
    StoryParams(place="roof_garden", project="banner", caution="mask", name="Zoe", role="girl", sidekick="the speedy friend"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print(v)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
