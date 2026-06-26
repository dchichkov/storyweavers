#!/usr/bin/env python3
"""
storyworlds/worlds/lasso_ratchet_sound_effects_bedtime_story.py
===============================================================

A small bedtime-story world about a child, a gentle nighttime problem,
and two useful tools: a lasso and a ratchet.

Seed tale:
---
At bedtime, a little child loved to play with a cowboy lasso and a toy
ratchet set. One night, a dangling kite string got tangled on the porch
hook, and every tiny tug made a squeaky sound: "eeek-eeek." The child
wanted to keep playing, but the grown-up warned that loud tugging would
wake the baby and make the porch messier.

So the child used the lasso to loop the string, then used the ratchet
to turn the hook slowly: click-clack, click-clack. The string slipped
free, the baby kept sleeping, and the child climbed into bed smiling.
---

The story model tracks:
- physical meters: tangle, noise, tiredness, neatness, sleepiness
- emotional memes: worry, patience, pride, comfort, delight

The plot is intentionally tiny and classical:
1. setup: bedtime, toys, and a small snag
2. tension: noisy tugging might wake the baby
3. turn: lasso + ratchet solve the snag quietly
4. resolution: the room is calm, and everyone goes back to sleep

Sound effects are part of the narration and driven by state changes.
"""

from __future__ import annotations

import argparse
import copy
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    baby: object | None = None
    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
    place: str = "the porch"
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
class Problem:
    id: str
    verb: str
    gerund: str
    risk_sound: str
    mess: str
    fix_sounds: list[str]
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    guards: set[str]
    handles: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


PROBLEMS = {
    "kite_string": Problem(
        id="kite_string",
        verb="pull the kite string loose",
        gerund="pulling at the kite string",
        risk_sound="eeek-eeek",
        mess="tangle",
        fix_sounds=["click-clack", "snip-snip"],
        keyword="string",
        tags={"string", "knot"},
    ),
    "curtain_cord": Problem(
        id="curtain_cord",
        verb="untwist the curtain cord",
        gerund="straightening the curtain cord",
        risk_sound="scriiitch",
        mess="snag",
        fix_sounds=["click-clack", "tap-tap"],
        keyword="cord",
        tags={"cord", "knot"},
    ),
    "toy_rope": Problem(
        id="toy_rope",
        verb="free the toy rope from the porch hook",
        gerund="wiggling the toy rope",
        risk_sound="scrape-scrape",
        mess="snarl",
        fix_sounds=["click-clack", "twirl"],
        keyword="rope",
        tags={"rope", "hook"},
    ),
}

TOOLS = {
    "lasso": Tool(
        id="lasso",
        label="lasso",
        phrase="a soft toy lasso",
        action="loop the string with the lasso",
        guards={"tangle", "snag", "snarl"},
        handles={"string", "cord", "rope"},
    ),
    "ratchet": Tool(
        id="ratchet",
        label="ratchet",
        phrase="a little ratchet tool",
        action="turn the hook with the ratchet",
        guards={"tangle", "snag", "snarl"},
        handles={"hook", "bolt", "twist"},
    ),
}

SETTINGS = {
    "porch": Setting(place="the porch", indoors=False, affords={"kite_string", "toy_rope"}),
    "nursery": Setting(place="the nursery", indoors=True, affords={"curtain_cord"}),
}

CHILD_NAMES = ["Milo", "Nina", "Theo", "Luna", "Poppy", "Arlo", "Ivy", "Owen"]
TRAITS = ["sleepy", "gentle", "curious", "brave", "kind"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
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


ASP_RULES = r"""
problem_at_risk(P) :- problem(P).
tool_fits(T, P) :- problem(P), handles(T, H), needs(P, H), guards(T, G), risk(P, G).
valid_story(Place, P, T) :- affords(Place, P), problem_at_risk(P), tool_fits(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, p.keyword))
        for tag in sorted(p.tags):
            lines.append(asp.fact("risk", pid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.handles):
            lines.append(asp.fact("handles", tid, h))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for p in setting.affords:
            problem = _safe_lookup(PROBLEMS, p)
            if any(t.handles & {problem.keyword} and t.guards & {problem.tags} for t in TOOLS.values()):
                combos.append((place, p))
    return combos


def reasonableness_check(problem: Problem, tool: Tool) -> bool:
    return problem.keyword in tool.handles and bool(problem.tags & tool.guards)


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in [TOOLS["lasso"], TOOLS["ratchet"]]:
        if reasonableness_check(problem, tool):
            return tool
    return None


def predict(world: World, child: Entity, problem: Problem, tool: Tool) -> dict:
    sim = world.copy()
    child2 = sim.get(child.id)
    child2.meters["noise"] += 1
    if not reasonableness_check(problem, tool):
        return {"fixed": False, "woke_baby": True}
    return {"fixed": True, "woke_baby": False}


def setup(world: World, child: Entity, parent: Entity, baby: Entity, problem: Problem) -> None:
    world.say(
        f"At bedtime, {child.id} was a {child.pronoun('possessive')} {child.memes.get('trait', 'gentle')} little {child.type}, "
        f"holding {problem.gerund} in the quiet light."
    )
    world.say(
        f"{parent.pronoun().capitalize()} watched the porch and whispered that the baby was already sleepy."
    )


def tension(world: World, child: Entity, parent: Entity, baby: Entity, problem: Problem) -> None:
    child.meters["noise"] += 1
    child.memes["wanting"] += 1
    world.say(
        f"Then the {problem.keyword} snag made a tiny {problem.risk_sound}: {problem.risk_sound}. "
        f"{child.id} wanted to keep tugging."
    )
    world.say(
        f"But {parent.pronoun('possessive')} voice stayed soft: if the tugging got louder, it might wake the baby."
    )


def use_lasso(world: World, child: Entity, problem: Problem) -> None:
    child.meters["skill"] += 1
    child.meters["noise"] += 0.25
    world.say(f"{child.id} took a breath and used the lasso. Swish, swish, loop.")
    world.say(f"The soft loop slid around the {problem.keyword}, gentle as a hug.")


def use_ratchet(world: World, child: Entity, problem: Problem) -> None:
    child.meters["skill"] += 1
    child.memes["pride"] += 1
    world.say(f"Next came the ratchet: click-clack, click-clack, nice and slow.")
    world.say(f"The little tool turned the hook without a shout.")


def resolve(world: World, child: Entity, parent: Entity, baby: Entity, problem: Problem) -> None:
    child.meters["noise"] = 0
    child.meters["neatness"] += 1
    child.memes["comfort"] += 1
    child.memes["delight"] += 1
    baby.meters["sleep"] += 1
    world.say(
        f"At last, the {problem.keyword} slipped free with one last soft flick. The porch went still."
    )
    world.say(
        f"{child.id} smiled, tucked the tools away, and climbed into bed while {parent.pronoun('possessive')} {parent.type} smiled back."
    )
    world.say("The baby kept sleeping, and the night stayed as quiet as a blanket.")


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type="child"))
    child.memes["trait"] = params.trait
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label="mom"))
    baby = world.add(Entity(id="Baby", kind="character", type="baby"))
    problem = _safe_lookup(PROBLEMS, params.problem)
    tool = select_tool(problem)
    if tool is None:
        pass
    world.facts.update(child=child, parent=parent, baby=baby, problem=problem, tool=tool)
    setup(world, child, parent, baby, problem)
    world.para()
    tension(world, child, parent, baby, problem)
    use_lasso(world, child, problem)
    use_ratchet(world, child, problem)
    world.para()
    resolve(world, child, parent, baby, problem)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, problem = f["child"], f["problem"]
    return [
        f'Write a gentle bedtime story for a preschooler that includes the words "lasso" and "ratchet".',
        f"Tell a short story where {child.id} uses a lasso and a ratchet to fix a small nighttime problem without waking the baby.",
        f"Write a cozy bedtime story with quiet sound effects like {problem.risk_sound} and click-clack.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, baby, problem, tool = f["child"], f["parent"], f["baby"], f["problem"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {child.id} use first to help with the {problem.keyword}?",
            answer=f"{child.id} used the lasso first, because it could make a soft loop around the {problem.keyword}.",
        ),
        QAItem(
            question=f"Why did {parent.label} want the work to stay quiet?",
            answer="Because the baby was sleepy, and loud tugging might have woken the baby up.",
        ),
        QAItem(
            question=f"How did the ratchet help at the end?",
            answer=f"The ratchet turned slowly with a click-clack sound, so the hook could move without making a fuss.",
        ),
        QAItem(
            question=f"What changed after the problem was fixed?",
            answer=f"The {problem.keyword} came free, the porch got calm again, and {child.id} could go to bed smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lasso?",
            answer="A lasso is a looped rope used to catch or guide something gently.",
        ),
        QAItem(
            question="What is a ratchet?",
            answer="A ratchet is a tool that turns in small steps, often making a click-clack sound.",
        ),
        QAItem(
            question="Why do people try to be quiet at bedtime?",
            answer="People try to be quiet at bedtime so everyone can rest and fall asleep.",
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect helps the reader imagine what something sounds like, like a soft swish or a click-clack.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((place, problem, tool.id) for place, problem in valid_combos() for tool in TOOLS.values() if reasonableness_check(_safe_lookup(PROBLEMS, problem), tool))
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python-only:", sorted(py - clingo_set))
    print("asp-only:", sorted(clingo_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with lasso, ratchet, and soft sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = []
    for place, setting in SETTINGS.items():
        if getattr(args, "place", None) and place != getattr(args, "place", None):
            continue
        for problem_id in setting.affords:
            if getattr(args, "problem", None) and problem_id != getattr(args, "problem", None):
                continue
            combos.append((place, problem_id))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="porch", problem="kite_string", name="Milo", trait="gentle"),
    StoryParams(place="nursery", problem="curtain_cord", name="Luna", trait="sleepy"),
    StoryParams(place="porch", problem="toy_rope", name="Ivy", trait="curious"),
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
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible bedtime stories:\n")
        for item in stories:
            print("  ", item)
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
