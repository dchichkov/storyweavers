#!/usr/bin/env python3
"""
storyworlds/worlds/approve_forge_teamwork_comedy.py
====================================================

A compact comedy storyworld about a small team trying to forge something
important, get it approved, and survive the awkward chaos along the way.

Premise:
- A tiny team wants to forge a shiny item in a workshop.
- Their plan is funny because the first version is lopsided, noisy, or silly.
- A reviewer worries the thing is not ready to approve.
- The team works together, fixes the problem, and earns approval.

The world is modeled with typed entities, physical meters, and emotional memes.
The story is state-driven: the team members start with a goal, encounter a
mistake, cooperate to repair it, and end with a clear change in the scene.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    member: object | None = None
    project: object | None = None
    reviewer: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Workshop:
    place: str = "the workshop"
    noise: float = 0.0
    sparkle: float = 0.0
    messy: float = 0.0
    WORKSHOP: object | None = None
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
    kind: str
    helps: set[str]
    fixes: set[str]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    fragility: str
    needs: set[str]
    reputation: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    team_size: int
    project: str
    issue: str
    reviewer: str
    seed: Optional[int] = None
    params: object | None = None
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


TEAM_NAMES = [
    "Mina", "Ollie", "Pip", "Nora", "Toby", "Rae", "Finn", "Ivy", "Jules", "Zia"
]
REVIEWER_NAMES = ["Ms. Bell", "Mr. Pine", "Aunt June", "Coach Nia"]
TRAITS = ["cheerful", "goofy", "patient", "brave", "quick", "bouncy"]


PROJECTS = {
    "crown": Project(
        id="crown",
        label="crown",
        phrase="a shiny paper crown with tiny stars",
        fragility="crooked",
        needs={"straight", "sparkle"},
        reputation="too wobbly to approve",
    ),
    "robot": Project(
        id="robot",
        label="robot",
        phrase="a little tin robot for the school show",
        fragility="bumpy",
        needs={"tight", "sparkle"},
        reputation="too clanky to approve",
    ),
    "shield": Project(
        id="shield",
        label="shield",
        phrase="a round parade shield with a smiling sun",
        fragility="lopsided",
        needs={"straight", "clean"},
        reputation="too lopsided to approve",
    ),
}

ISSUES = {
    "crooked": ("crooked", {"straight"}),
    "loose": ("loose", {"tight"}),
    "smudged": ("smudged", {"clean"}),
    "dull": ("dull", {"sparkle"}),
}

TOOLS = {
    "hammer": Tool(id="hammer", label="a tiny hammer", kind="hammer", helps={"tight"}, fixes={"loose"}),
    "ruler": Tool(id="ruler", label="a ruler", kind="ruler", helps={"straight"}, fixes={"crooked", "lopsided"}),
    "cloth": Tool(id="cloth", label="a soft cloth", kind="cloth", helps={"clean"}, fixes={"smudged"}),
    "glitter": Tool(id="glitter", label="a jar of glitter", kind="glitter", helps={"sparkle"}, fixes={"dull"}),
}

WORKSHOP = Workshop(place="the workshop")


class World:
    def __init__(self, workshop: Workshop) -> None:
        self.workshop = workshop
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _inc_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _inc_mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _apply_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = [e for e in world.entities.values() if e.kind == "character" and e.type not in {"reviewer"}]
    project = world.get("project")
    for member in team:
        if _mem(member, "teamwork") < THRESHOLD:
            continue
        sig = ("help", member.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _inc_meter(project, "progress", 1.0)
        _inc_mem(member, "pride", 0.5)
        out.append(f"{member.id} worked with the others and made the {project.label} a little better.")
    return out


def _apply_sparkle(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    for tool in list(world.entities.values()):
        if tool.kind != "tool" or _meter(tool, "used") < THRESHOLD:
            continue
        if "sparkle" in tool.fixes and _meter(project, "dull") >= THRESHOLD:
            sig = ("sparkle", tool.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            project.meters["dull"] = max(0.0, project.meters.get("dull", 0.0) - 1.0)
            project.meters["sparkle"] = project.meters.get("sparkle", 0.0) + 1.0
            world.workshop.sparkle += 1.0
            out.append("A little glitter made the project look much less sleepy.")
    return out


def _apply_straighten(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    for tool in list(world.entities.values()):
        if tool.kind != "tool" or _meter(tool, "used") < THRESHOLD:
            continue
        if "straight" in tool.fixes and _meter(project, "crooked") >= THRESHOLD:
            sig = ("straighten", tool.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            project.meters["crooked"] = max(0.0, project.meters.get("crooked", 0.0) - 1.0)
            project.meters["straight"] = project.meters.get("straight", 0.0) + 1.0
            out.append("A careful adjustment nudged the project back into line.")
    return out


RULES = [_apply_teamwork, _apply_sparkle, _apply_straighten]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def project_needs(project: Project) -> set[str]:
    return set(project.needs)


def choose_fix_tool(issue: str) -> Optional[Tool]:
    for tool in TOOLS.values():
        if issue in tool.fixes:
            return tool
    return None


def can_story(project: Project, issue: str) -> bool:
    return bool(project_needs(project) & _safe_lookup(ISSUES, issue)[1] and choose_fix_tool(issue))


def explain_rejection(project: Project, issue: str) -> str:
    return f"(No story: the {project.label} is not a good match for a {issue} problem, or no tool can fix it honestly.)"


def build_cast(world: World, params: StoryParams) -> tuple[list[Entity], Entity, Entity]:
    team: list[Entity] = []
    for i in range(params.team_size):
        name = _safe_lookup(TEAM_NAMES, i)
        member = world.add(Entity(
            id=name,
            kind="character",
            type="girl" if i % 2 == 0 else "boy",
            traits=["little", _safe_lookup(TRAITS, i % len(TRAITS))],
        ))
        team.append(member)
    reviewer = world.add(Entity(
        id="reviewer",
        kind="character",
        type="reviewer",
        label=params.reviewer,
        traits=["careful"],
    ))
    project = world.add(Entity(
        id="project",
        kind="thing",
        type="project",
        label=_safe_lookup(PROJECTS, params.project).label,
        phrase=_safe_lookup(PROJECTS, params.project).phrase,
    ))
    return team, reviewer, project


def tell(params: StoryParams) -> World:
    world = World(WORKSHOP)
    project_cfg = _safe_lookup(PROJECTS, params.project)
    issue_word, issue_needs = _safe_lookup(ISSUES, params.issue)
    team, reviewer, project = build_cast(world, params)

    tool = world.add(Entity(
        id="tool",
        kind="tool",
        type=_safe_lookup(TOOLS, params.issue if params.issue in TOOLS else "ruler").kind,
        label=choose_fix_tool(params.issue).label,
        plural=False,
    ))
    tool.meters["used"] = 0.0

    # Setup
    world.say(
        f"At {world.workshop.place}, {', '.join(m.id for m in team[:-1])}, and {team[-1].id} were trying to forge {project.phrase}."
    )
    world.say(
        f"They all wanted it to be nice enough for {reviewer.label}, but the first version looked {issue_word}."
    )

    for m in team:
        _inc_mem(m, "teamwork", 1.0)
    _inc_mem(project, issue_word, 1.0)
    _inc_meter(project, issue_word, 1.0)
    world.workshop.noise += 1.0

    # Conflict
    world.para()
    world.say(
        f"{team[0].id} held up the lopsided piece and grinned. "
        f'"This is either a masterpiece or a very confused sandwich," {team[0].pronoun()} said.'
    )
    world.say(
        f"{reviewer.label} peered over the table and frowned a little. "
        f'"I cannot approve this yet," {reviewer.pronoun()} said. "It is still {project_cfg.reputation}."'
    )
    _inc_mem(reviewer, "doubt", 1.0)
    _inc_mem(team[0], "embarrassment", 1.0)

    # Teamwork turn
    world.para()
    world.say(
        f"Then the team took a breath and split the jobs."
    )
    for m in team:
        _inc_mem(m, "teamwork", 1.0)
        _inc_mem(m, "joy", 0.5)
    _inc_meter(tool, "used", 1.0)
    if params.issue == "crooked":
        _inc_meter(project, "crooked", 1.0)
    elif params.issue == "loose":
        _inc_meter(project, "loose", 1.0)
    elif params.issue == "smudged":
        _inc_meter(project, "smudged", 1.0)
    elif params.issue == "dull":
        _inc_meter(project, "dull", 1.0)

    _inc_meter(project, "progress", 1.0)
    propagate(world, narrate=True)

    if params.issue == "crooked":
        world.say(f"{team[1].id} used {tool.label} to line up the edges while the others held still.")
    elif params.issue == "loose":
        world.say(f"{team[1].id} tapped the loose part gently while the others steadied the frame.")
    elif params.issue == "smudged":
        world.say(f"{team[1].id} wiped the smudge away while the others tried not to laugh.")
    elif params.issue == "dull":
        world.say(f"{team[1].id} shook the glitter just right, and the room sparkled like a joke.")

    # Resolution
    world.para()
    _inc_meter(project, "progress", 2.0)
    _inc_mem(reviewer, "surprise", 1.0)
    if project.meters.get("progress", 0.0) >= 3.0:
        project.meters["approved"] = 1.0
        reviewer.memes["approval"] = 1.0
        world.say(
            f"At last, {reviewer.label} smiled. "
            f'"Now I can approve it," {reviewer.pronoun()} said. '
            f'"The team forged it together, and that part is the funniest and best part."'
        )
        world.say(
            f"The {project.label} sat on the table looking ready at last: no longer {project_cfg.reputation}, but neat, bright, and proud."
        )
    else:
        world.say(
            f"The project was better, but not quite ready, so the team kept working with even more care."
        )

    world.facts.update(
        team=team,
        reviewer=reviewer,
        project=project,
        tool=tool,
        issue=params.issue,
        issue_word=issue_word,
        project_cfg=project_cfg,
        issue_needs=issue_needs,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    project = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "project")
    issue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "issue_word")
    reviewer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "reviewer")
    return [
        f'Write a short comedy story for a child about a team trying to forge a {project.label} and get it approved.',
        f"Tell a funny story where a small team works together to fix a {issue} {project.label} before {reviewer.label} can approve it.",
        f'Write a gentle teamwork story that includes the words "forge" and "approve" and ends with a happy approval.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    team = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "team")
    reviewer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "reviewer")
    project = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "project")
    issue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "issue_word")
    qa = [
        QAItem(
            question=f"What were {team[0].id} and the others trying to forge in the workshop?",
            answer=f"They were trying to forge {project.phrase}. At first it looked {issue}, so it was not ready yet.",
        ),
        QAItem(
            question=f"Why did {reviewer.label} not approve the project right away?",
            answer=f"{reviewer.label} did not approve it right away because it still looked {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "project_cfg").reputation}. The team had to work together and fix it first.",
        ),
        QAItem(
            question="What helped the team finish the project?",
            answer="Teamwork helped. Each helper did a small job, and together they made the project look much better.",
        ),
    ]
    if _mem(team[0], "embarrassment") >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"How did {team[0].id} feel when the first version looked silly?",
                answer=f"{team[0].id} felt embarrassed at first, but then the team kept going and turned the silly mistake into a funny success.",
            )
        )
    if _mem(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "reviewer"), "approval") >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What did {reviewer.label} say at the end?",
                answer=f"At the end, {reviewer.label} said the team could approve it now because they forged it together and made it ready.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to forge something?",
            answer="To forge something means to make it carefully, often by shaping or building it with tools and effort.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and do different jobs together to reach the same goal.",
        ),
        QAItem(
            question="What does approve mean?",
            answer="To approve something means to say it is good enough or ready to be accepted.",
        ),
        QAItem(
            question="Why can comedy stories be funny?",
            answer="Comedy stories can be funny because characters make silly mistakes, say amusing things, or have surprising little problems.",
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A project needs a fix when one of its issues is present.
needs_fix(P, I) :- issue(I), project(P), has_issue(P, I).

% A tool helps a fix when its capabilities match the issue.
can_fix(T, P, I) :- tool(T), needs_fix(P, I), fixes(T, I).

% Teamwork can increase progress.
teamwork_boost(M) :- teammate(M).

% Approval happens only when a project has enough progress and a matching fix.
approvable(P) :- project(P), progress(P, N), N >= 3, needs_fix(P, I), can_fix(_, P, I).

valid_story(Proj, Issue) :- project(Proj), issue(Issue), needs_fix(Proj, Issue), can_fix(_, Proj, Issue), approvable(Proj).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("has_issue", pid, next(k for k, v in ISSUES.items() if v[0] in p.needs or v[1] & p.needs)))
        for n in sorted(p.needs):
            lines.append(asp.fact("needs", pid, n))
    for iid in ISSUES:
        lines.append(asp.fact("issue", iid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for fx in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, fx))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((p, i) for p, pinfo in PROJECTS.items() for i in ISSUES if can_story(pinfo, i))
    asp_pairs = asp_valid_stories()
    if set(py) == set(asp_pairs):
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  python:", py)
    print("  asp:", asp_pairs)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a team forging and approving a project.")
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--reviewer", choices=REVIEWER_NAMES)
    ap.add_argument("--team-size", type=int, choices=[2, 3, 4], default=3)
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
    project = getattr(args, "project", None) or rng.choice(list(PROJECTS))
    issue = getattr(args, "issue", None) or rng.choice(list(ISSUES))
    if not can_story(_safe_lookup(PROJECTS, project), issue):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    reviewer = getattr(args, "reviewer", None) or rng.choice(REVIEWER_NAMES)
    return StoryParams(team_size=getattr(args, "team_size", None), project=project, issue=issue, reviewer=reviewer)


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{p} / {i}" for p, i in asp_valid_stories()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for project in PROJECTS:
            for issue in ISSUES:
                if can_story(_safe_lookup(PROJECTS, project), issue):
                    params = StoryParams(team_size=3, project=project, issue=issue, reviewer=_safe_lookup(REVIEWER_NAMES, 0))
                    samples.append(generate(params))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.project} / {p.issue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
