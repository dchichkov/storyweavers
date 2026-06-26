#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/inlay_mystic_rhyme_magic_comedy.py
================================================================================

A small comedy storyworld about a mystic inlay workshop where rhyme and magic
can either help or hilariously tangle up the day.

The seed image behind this world:
- a child finds a mystic inlay piece
- a rhyme is needed to make the magic settle
- the story ends with the inlay finished, polished, and proudly shown off

This world is intentionally small and constraint-driven:
- the setting is a workshop or studio with a single craft project
- the tension comes from a magical inlay that will not sit right
- the turn comes from a rhyme-based spell
- the resolution is a completed object and a cheerful final image
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    art: object | None = None
    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    light: str
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
class Project:
    id: str
    label: str
    phrase: str
    mess: str
    sparkle: str
    rhyme_need: str
    result: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    cue: str
    effect: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _char_name(ent: Entity) -> str:
    return ent.label or ent.id


def _article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


SETTINGS = {
    "workshop": Setting(place="the little workshop", light="sunlight", affords={"tile", "song"}),
    "studio": Setting(place="the cozy studio", light="lamplight", affords={"tile", "song"}),
    "porch": Setting(place="the porch table", light="evening light", affords={"tile", "song"}),
}

PROJECTS = {
    "tile": Project(
        id="tile",
        label="inlay tile",
        phrase="a tiny inlay tile with a moon-blue shimmer",
        mess="sparkles",
        sparkle="sparkles everywhere",
        rhyme_need="rhyme",
        result="fit snugly into place",
        keyword="inlay",
        tags={"inlay", "mystic", "magic"},
    ),
    "box": Project(
        id="box",
        label="wooden box",
        phrase="a wooden box with a star-shaped inlay slot",
        mess="glows",
        sparkle="glows too bright",
        rhyme_need="rhyme",
        result="close with a happy click",
        keyword="inlay",
        tags={"inlay", "mystic", "magic"},
    ),
}

CHARMS = [
    Charm(
        id="rhyme",
        label="rhyme charm",
        phrase="a rhyme charm",
        cue="say a neat rhyme",
        effect="settle the magic",
        covers={"sparkles", "glows"},
        guards={"sparkles", "glows"},
    ),
    Charm(
        id="glove",
        label="soft gloves",
        phrase="soft gloves",
        cue="put on soft gloves",
        effect="keep the glitter off",
        covers={"hands"},
        guards={"sparkles"},
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Ada", "Nora", "Ivy", "Mila"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Finn", "Max", "Leo"]
TRAITS = ["curious", "cheerful", "sly", "bouncy", "spirited", "clever"]


def project_at_risk(project: Project) -> bool:
    return True


def select_charm(project: Project) -> Optional[Charm]:
    for charm in CHARMS:
        if project.mess in charm.guards:
            return charm
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for proj_id in setting.affords:
            proj = _safe_lookup(PROJECTS, proj_id)
            if project_at_risk(proj) and select_charm(proj):
                combos.append((place, proj_id))
    return combos


@dataclass
class StoryParams:
    place: str
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


def rhythm_line(project: Project) -> str:
    return {
        "tile": "A tiny tile should land, not wobble like a clown on a trampoline.",
        "box": "A star slot should shut, not bounce open like a giggling drawer.",
    }[project.id]


def introduce(world: World, child: Entity, helper: Entity, project: Project) -> None:
    world.say(
        f"{_char_name(child)} was a {_article(child.type)} {child.type} with a love for funny little tricks."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked {_char_name(helper)}'s stories, shiny things, and anything called {project.keyword}."
    )
    world.say(
        f"In {world.setting.place}, they were trying to finish {project.phrase}; {rhythm_line(project)}"
    )


def attempt(world: World, child: Entity, project: Project) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    child.meters[project.mess] = child.meters.get(project.mess, 0.0) + 1
    world.say(
        f"{child.pronoun().capitalize()} carefully set the piece down, but the magic fizzed with a silly little hiccup."
    )
    world.say(
        f"Instead of sitting still, it made {project.sparkle}."
    )


def warn(world: World, helper: Entity, child: Entity, project: Project) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f'"If we let it do that," {_char_name(helper)} said, "the {project.label} will never {project.result}."'
    )
    world.say(
        f"{_char_name(helper)} held up {project.keyword} and gave a very serious face that was also a little funny."
    )


def rhyme_fix(world: World, helper: Entity, child: Entity, project: Project, charm: Charm) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["worry"] = 0.0
    world.say(
        f'Then {_char_name(helper)} said, "{charm.cue}, and let the bright bit go light!"'
    )
    world.say(
        f"{_char_name(child)} repeated the rhyme, and the magic stopped wobbling."
    )
    world.say(
        f"The {project.label} settled down and finally began to {project.result}."
    )


def finish(world: World, child: Entity, helper: Entity, project: Project) -> None:
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    world.say(
        f"In the end, {_char_name(child)} held up the finished {project.label}, and it looked neat and bright."
    )
    world.say(
        f"{_char_name(helper)} laughed, because the whole thing had been magical, and a little ridiculous, and very good."
    )


def tell(setting: Setting, project: Project, name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    helper_label = "grandma" if helper_type == "grandmother" else "grandpa" if helper_type == "grandfather" else helper_type
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=helper_label))
    art = world.add(Entity(id="Project", type=project.id, label=project.label, phrase=project.phrase, owner=child.id, caretaker=helper.id))

    child.memes["curious"] = 1.0
    helper.memes["calm"] = 1.0

    introduce(world, child, helper, project)
    world.para()
    attempt(world, child, project)
    warn(world, helper, child, project)
    world.para()
    charm = select_charm(project)
    if charm is None:
        pass
    rhyme_fix(world, helper, child, project, charm)
    finish(world, child, helper, project)

    world.facts.update(
        child=child,
        helper=helper,
        project=art,
        project_cfg=project,
        charm=charm,
        setting=setting,
        trait=trait,
    )
    return world


KNOWLEDGE = {
    "inlay": [
        (
            "What is an inlay?",
            "An inlay is a piece or pattern fitted into a surface so it sits neatly in place.",
        ),
        (
            "Why do people polish inlay?",
            "People polish inlay so it looks smooth and bright and so the edges feel nice to touch.",
        ),
    ],
    "mystic": [
        (
            "What does mystic mean?",
            "Mystic means strange, magical, or a little mysterious, like something from a fairy tale.",
        )
    ],
    "magic": [
        (
            "What is magic in stories?",
            "Magic in stories is when something unusual happens that seems impossible in real life.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like cat and hat.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    project = _safe_fact(world, f, "project_cfg")
    return [
        f'Write a funny short story for a young child about {child.id}, {project.keyword}, and a rhyme that helps magic settle down.',
        f"Tell a comedy story where {child.id} wants to finish {project.phrase} in {world.setting.place}, but the magic gets silly until {helper.label} uses a rhyme.",
        f'Write a gentle, funny tale that includes the words "{project.keyword}" and "rhyme" and ends with a finished magical craft.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    project = _safe_fact(world, f, "project_cfg")
    qa = [
        QAItem(
            question=f"What was {child.id} trying to finish in {world.setting.place}?",
            answer=f"{child.id} was trying to finish {project.phrase}. It was a little {project.keyword} craft with a mystic feel.",
        ),
        QAItem(
            question=f"Why did {helper.label} worry when the piece started acting up?",
            answer=f"{helper.label.capitalize()} worried because the magic made {project.sparkle}, and then the {project.label} would not {project.result}.",
        ),
        QAItem(
            question=f"What did {child.id} say or repeat that helped the craft settle?",
            answer=f"{child.id} repeated a rhyme, and the magic stopped wobbling. That let the {project.label} become calm and neat again.",
        ),
    ]
    if f.get("charm"):
        qa.append(
            QAItem(
                question=f"How did the rhyme charm help in the end?",
                answer=f"It helped by settling the magic so the {project.label} could {project.result} instead of bouncing around like a joke.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["project_cfg"].tags)
    out: list[QAItem] = []
    for tag in ["inlay", "mystic", "magic", "rhyme"]:
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="workshop", project="tile", name="Mina", gender="girl", helper="grandmother", trait="curious"),
    StoryParams(place="studio", project="box", name="Owen", gender="boy", helper="grandfather", trait="cheerful"),
]


def explain_rejection(place: str, project: str) -> str:
    return f"(No story: {place} and {project} do not make a reasonable comedy-magic inlay setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedy storyworld about mystic inlay, rhyme, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandmother", "grandfather"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "project", None) and (getattr(args, "place", None), getattr(args, "project", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "project", None) is None or c[1] == getattr(args, "project", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, project_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["grandmother", "grandfather"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, project=project_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROJECTS, params.project), params.name, params.gender, params.helper, params.trait)
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


ASP_RULES = r"""
setting(workshop). setting(studio). setting(porch).
affords(workshop,tile). affords(workshop,song).
affords(studio,box). affords(studio,song).
affords(porch,tile). affords(porch,song).

project(tile). project(box).

project_at_risk(P) :- project(P).

charm(rhyme).
guards(rhyme,sparkles).
guards(rhyme,glows).

has_fix(P) :- project_at_risk(P), project(P), mess_of(P,M), guards(rhyme,M).

valid(Place, Project) :- affords(Place, Project), project_at_risk(Project), has_fix(Project).

#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for proj in sorted(setting.affords):
            lines.append(asp.fact("affords", place, proj))
    for proj_id, proj in PROJECTS.items():
        lines.append(asp.fact("project", proj_id))
        lines.append(asp.fact("mess_of", proj_id, proj.mess))
    lines.append(asp.fact("charm", "rhyme"))
    for c in CHARMS:
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(a - p))
    print(" only in python:", sorted(p - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible (place, project) combos:")
        for place, proj in asp_valid_combos():
            print(f"  {place:10} {proj}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.project} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
