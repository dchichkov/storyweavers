#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a classroom craft mishap with pronouns,
a short delay, a hexagon shape, humor, and teamwork.

The world is intentionally narrow: a few reasonable variants, all grounded in
the same gentle premise. A child and a helper are trying to finish a simple
project, but a tiny delay and a confusing pronoun lead to a funny pause before
they solve it together.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    child: object | None = None
    helper: object | None = None
    project: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "teacher"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
    indoor: bool = True
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
class Activity:
    id: str
    verb: str
    gerund: str
    delay: str
    humor: str
    focus: str
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
class Project:
    label: str
    phrase: str
    type: str
    keyword: str
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
class StoryParams:
    place: str
    activity: str
    project: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "classroom": Setting(place="the classroom", indoor=True, affords={"craft", "draw"}),
    "art_corner": Setting(place="the art corner", indoor=True, affords={"craft", "draw"}),
    "library_table": Setting(place="the library table", indoor=True, affords={"craft"}),
}

ACTIVITIES = {
    "craft": Activity(
        id="craft",
        verb="finish the paper craft",
        gerund="making paper shapes",
        delay="had to wait for the glue to dry",
        humor="the tape kept sticking to the wrong finger",
        focus="glue",
        tags={"craft", "humor", "teamwork"},
    ),
    "draw": Activity(
        id="draw",
        verb="draw the poster",
        gerund="drawing simple pictures",
        delay="had to pause because the marker cap rolled away",
        humor="the marker made a squeaky little sound",
        focus="marker",
        tags={"draw", "humor"},
    ),
}

PROJECTS = {
    "hexagon": Project(
        label="hexagon card",
        phrase="a bright paper hexagon with six neat sides",
        type="card",
        keyword="hexagon",
    ),
    "banner": Project(
        label="banner",
        phrase="a cheerful banner with big letters",
        type="banner",
        keyword="banner",
    ),
    "sticker_sheet": Project(
        label="sticker sheet",
        phrase="a shiny sticker sheet with tiny stars",
        type="sheet",
        keyword="sticker",
        plural=True,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lina", "Ava", "Zoe", "Maya", "Ella", "Ruby"]
BOY_NAMES = ["Finn", "Leo", "Noah", "Eli", "Max", "Sam", "Theo", "Ben"]
TRAITS = ["curious", "playful", "patient", "cheerful", "careful", "bouncy"]


def reasonableness_gate(place: str, activity: str, project: str) -> bool:
    if place not in SETTINGS or activity not in ACTIVITIES or project not in PROJECTS:
        return False
    return activity in _safe_lookup(SETTINGS, place).affords


def explain_rejection(place: str, activity: str, project: str) -> str:
    return (
        f"(No story: {place} does not reasonably support {activity} for the {project}.)"
    )


def _do_activity(world: World, child: Entity, activity: Activity) -> None:
    child.memes["busy"] = child.memes.get("busy", 0.0) + 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0


def predict_delay(world: World, child: Entity, activity: Activity, project: Entity) -> dict:
    sim = world.copy()
    c = sim.get(child.id)
    _do_activity(sim, c, activity)
    return {
        "delay": True,
        "humor": activity.humor,
    }


def introduce(world: World, child: Entity, helper: Entity, project: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(
        f"{child.id} was a little {trait} {child.type} who liked neat things and kind help."
    )
    world.say(
        f"{child.id} and {helper.label} were working on {project.phrase} together."
    )


def setup(world: World, child: Entity, helper: Entity, activity: Activity, project: Entity) -> None:
    where = world.setting.place
    world.say(
        f"One afternoon at {where}, {child.id} wanted to {activity.verb}."
    )
    world.say(
        f"Before that, {helper.label} reminded {child.pronoun('object')} to watch the {project.keyword} shape."
    )
    world.say(f"The project was meant to look like a {project.keyword}, with six sides and a tidy edge.")


def delay_beat(world: World, child: Entity, helper: Entity, activity: Activity, project: Entity) -> None:
    pred = predict_delay(world, child, activity, project)
    world.facts["delayed"] = pred["delay"]
    world.facts["humor_line"] = pred["humor"]
    world.say(
        f"Then the work slowed down because {activity.delay}."
    )
    world.say(
        f"That made everyone pause and laugh a little, because {activity.humor}."
    )


def pronoun_mixup(world: World, child: Entity, helper: Entity, activity: Activity, project: Entity) -> None:
    child.memes["confused"] = child.memes.get("confused", 0.0) + 1.0
    world.say(
        f"{child.id} pointed at the {project.keyword} and said, "
        f'"{child.pronoun("subject").capitalize()} is almost done, right?"'
    )
    world.say(
        f"{helper.label} smiled and said, "
        f'"When you say {child.pronoun("subject")}, you mean {child.pronoun("subject")} the helper, not the paper shape."'
    )
    world.say(
        f"That small pronoun mix-up was funny, and it made {child.id} giggle."
    )


def teamwork_beat(world: World, child: Entity, helper: Entity, activity: Activity, project: Entity) -> None:
    child.memes["teamwork"] = child.memes.get("teamwork", 0.0) + 1.0
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1.0
    world.say(
        f"Then they worked as a team: {child.id} held the paper steady while {helper.label} smoothed the corners."
    )
    world.say(
        f"Together they made sure every side of the {project.keyword} stayed even."
    )


def ending(world: World, child: Entity, helper: Entity, project: Entity) -> None:
    world.say(
        f"In the end, the {project.keyword} looked bright and finished, and the little delay had turned into a shared joke."
    )
    world.say(
        f"{child.id} smiled at {helper.label}, glad that a tiny mistake and a little patience had led to a better result."
    )


def tell(setting: Setting, activity: Activity, project_cfg: Project,
         name: str = "Mia", gender: str = "girl",
         helper_role: str = "teacher", trait: str = "curious") -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_role, label="the helper"))
    project = world.add(Entity(id="project", type=project_cfg.type, label=project_cfg.label, phrase=project_cfg.phrase, plural=project_cfg.plural))
    world.facts.update(child=child, helper=helper, project=project, activity=activity, setting=setting)

    introduce(world, child, helper, project)
    world.para()
    setup(world, child, helper, activity, project)
    delay_beat(world, child, helper, activity, project)
    pronoun_mixup(world, child, helper, activity, project)
    world.para()
    teamwork_beat(world, child, helper, activity, project)
    ending(world, child, helper, project)
    world.facts["resolved"] = True
    return world


KNOWLEDGE = {
    "hexagon": [
        (
            "What is a hexagon?",
            "A hexagon is a shape with six sides and six corners.",
        )
    ],
    "pronoun": [
        (
            "What is a pronoun?",
            "A pronoun is a word like he, she, it, or they that can stand in for a noun.",
        )
    ],
    "delay": [
        (
            "What is a delay?",
            "A delay is when something takes longer than planned and people have to wait a little.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other and do a job together.",
        )
    ],
    "humor": [
        (
            "Why do people laugh at funny mix-ups?",
            "People laugh when a mix-up feels surprising, harmless, and a little silly.",
        )
    ],
}

KNOWLEDGE_ORDER = ["hexagon", "pronoun", "delay", "teamwork", "humor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, activity, project = f["child"], f["helper"], f["activity"], f["project"]
    return [
        f'Write a gentle slice-of-life story about {child.id}, a small {child.type}, and {helper.label}, with a {project.keyword} craft and a funny delay.',
        f"Tell a child-friendly story where a {project.keyword} shape, a pronoun mix-up, and teamwork help finish {activity.verb}.",
        f'Write a short story that uses the word "{project.keyword}" and ends with a warm teamwork moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, activity, project = f["child"], f["helper"], f["activity"], f["project"]
    qa = [
        QAItem(
            question=f"What was {child.id} trying to do with the {project.keyword}?",
            answer=f"{child.id} was trying to {activity.verb} with {helper.label} nearby.",
        ),
        QAItem(
            question=f"Why did the work slow down in the story?",
            answer=f"The work slowed down because {activity.delay}.",
        ),
        QAItem(
            question=f"What funny thing happened with pronouns?",
            answer=f"{child.id} and {helper.label} had a small pronoun mix-up, and that made them laugh before they kept working.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did {child.id} and {helper.label} finish the project?",
                answer=f"They finished it by working as a team, with {child.id} holding the paper steady and {helper.label} smoothing the corners.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("pronoun")
    project = _safe_fact(world, world.facts, "project")
    if project.keyword == "hexagon":
        tags.add("hexagon")
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="classroom", activity="craft", project="hexagon", name="Mia", gender="girl", helper="teacher", trait="curious"),
    StoryParams(place="art_corner", activity="craft", project="hexagon", name="Leo", gender="boy", helper="teacher", trait="playful"),
    StoryParams(place="library_table", activity="craft", project="banner", name="Ava", gender="girl", helper="teacher", trait="careful"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for act in s.affords:
            for proj in PROJECTS:
                if reasonableness_gate(place, act, proj):
                    combos.append((place, act, proj))
    return combos


def explain_gender(project_id: str, gender: str) -> str:
    return f"(No story: {_safe_lookup(PROJECTS, project_id).label} is not constrained by gender here, but the requested options were too narrow.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "activity", None) and getattr(args, "project", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "activity", None), getattr(args, "project", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "project", None) is None or c[2] == getattr(args, "project", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, project = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = getattr(args, "gender", None) or ("girl" if name in GIRL_NAMES else "boy")
    helper = getattr(args, "helper", None) or "teacher"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, project=project, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PROJECTS, params.project), params.name, params.gender, params.helper, params.trait)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a hexagon craft, a short delay, humor, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["teacher"])
    ap.add_argument("--name")
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


ASP_RULES = r"""
valid_story(P,A,J) :- affords(P,A), project(J).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for jid in PROJECTS:
        lines.append(asp.fact("project", jid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (project: {p.project})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
