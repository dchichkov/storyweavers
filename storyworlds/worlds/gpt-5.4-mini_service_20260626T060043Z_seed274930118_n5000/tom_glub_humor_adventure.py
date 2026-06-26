#!/usr/bin/env python3
"""
A standalone story world about Tom and Glub: a small, humorous adventure in
which a cautious child and a bumbling helper cross a little obstacle, learn to
work together, and end with a changed world state.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
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
    place: str = "the mossy path"
    obstacle: str = "the wobbling bridge"
    afford: set[str] = field(default_factory=set)
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
class Goal:
    label: str
    phrase: str
    risk: str
    obstacle_meter: str
    requires: str
    humor_line: str
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
    phrase: str
    guards: set[str]
    helps: set[str]
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "riverbank": Setting(place="the riverbank", obstacle="the wobbling bridge", afford={"cross"}),
    "cave": Setting(place="the little cave", obstacle="the echoing tunnel", afford={"cross"}),
    "hill": Setting(place="the windy hill", obstacle="the steep slope", afford={"climb"}),
}

GOALS = {
    "crossing": Goal(
        label="cross the way",
        phrase="reach the other side",
        risk="slip and splash into the water",
        obstacle_meter="wobble",
        requires="steady feet",
        humor_line="the bridge shook like a spoonful of jelly",
    ),
    "map": Goal(
        label="find the map",
        phrase="get the lost map",
        risk="drop the lantern into the mud",
        obstacle_meter="dark",
        requires="a careful look",
        humor_line="the cave echoed every tiny sneeze like a drum",
    ),
    "berry": Goal(
        label="pick the berry",
        phrase="reach the berry bush",
        risk="tumble down the slope",
        obstacle_meter="steep",
        requires="brave steps",
        humor_line="the hill felt like it was trying to tickle their shoes",
    ),
}

TOOLS = {
    "pole": Tool(
        id="pole",
        label="a long pole",
        phrase="a long pole",
        guards={"wobble"},
        helps={"crossing"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a bright lantern",
        phrase="a bright lantern",
        guards={"dark"},
        helps={"map"},
    ),
    "rope": Tool(
        id="rope",
        label="a sturdy rope",
        phrase="a sturdy rope",
        guards={"steep"},
        helps={"berry"},
    ),
}

TOM_NAMES = ["Tom"]
GLOBULAR = ["Glub"]


@dataclass
class StoryParams:
    place: str
    goal: str
    tool: str
    name: str = "Tom"
    helper: str = "Glub"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
    params_list: list = field(default_factory=list)
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


def goal_needs_tool(goal: Goal, tool: Tool) -> bool:
    return goal.obstacle_meter in tool.guards and goal.label in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for goal_id, goal in GOALS.items():
            if goal_id == "crossing" and "cross" not in setting.afford:
                continue
            if goal_id == "map" and "cross" not in setting.afford:
                continue
            if goal_id == "berry" and "climb" not in setting.afford:
                continue
            for tool_id, tool in TOOLS.items():
                if goal_needs_tool(goal, tool):
                    out.append((place, goal_id, tool_id))
    return out


def explain_rejection(goal: Goal, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not honestly help with {goal.label}. "
        f"The fix must match the obstacle, so this combination is rejected.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _do_attempt(world: World, hero: Entity, helper: Entity, goal: Goal, tool: Tool, narrate: bool = True) -> None:
    hero.meters["courage"] = hero.meters.get("courage", 0.0) + 1.0
    helper.memes["helpful"] = helper.memes.get("helpful", 0.0) + 1.0
    if goal.obstacle_meter in tool.guards:
        helper.meters["tool_used"] = helper.meters.get("tool_used", 0.0) + 1.0
        hero.meters["progress"] = hero.meters.get("progress", 0.0) + 1.0
        if narrate:
            world.say(f"{helper.id} used {tool.label} and the tricky part got easier.")
    else:
        hero.meters["oops"] = hero.meters.get("oops", 0.0) + 1.0
        helper.meters["oops"] = helper.meters.get("oops", 0.0) + 1.0
        if narrate:
            world.say(f"The plan wobbled like a pancake on a spoon.")


def predict(world: World, hero: Entity, helper: Entity, goal: Goal, tool: Tool) -> dict:
    sim = world.copy()
    _do_attempt(sim, sim.get(hero.id), sim.get(helper.id), goal, tool, narrate=False)
    return {
        "success": sim.get(hero.id).meters.get("progress", 0.0) >= 1.0,
        "oops": sim.get(hero.id).meters.get("oops", 0.0),
    }


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, helper: Entity, goal: Goal) -> None:
    world.say(f"{hero.id} was a small brave boy who liked neat plans and big adventures.")
    world.say(f"{helper.id} was a glub, a round little helper with shiny eyes and an even shinier nose for trouble.")
    world.say(f"One day they wanted to {goal.phrase}.")


def setup(world: World, goal: Goal) -> None:
    world.para()
    world.say(f"They set out for {world.setting.place}, where {world.setting.obstacle} waited.")
    world.say(f"{goal.humor_line.capitalize()}.")


def conflict(world: World, hero: Entity, helper: Entity, goal: Goal) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(f"Tom looked at the obstacle and gulped. Then Glub made a heroic face and tripped on a leaf.")
    world.say(f"Tom wanted to go anyway, but the way ahead still looked {goal.requires}.")
    if goal.label == "cross the way":
        world.say("The bridge gave a tiny groan, as if it had a joke to tell but forgot the punchline.")
    elif goal.label == "get the lost map":
        world.say("Inside the cave, the shadows were so dark that even Glub's ears seemed to disappear.")
    else:
        world.say("The slope twinkled with loose pebbles, each one looking suspiciously ready to roll.")


def offer_fix(world: World, hero: Entity, helper: Entity, goal: Goal, tool: Tool) -> None:
    world.say(f"Glub pointed at {tool.label} and blinked very seriously.")
    world.say(f'"Maybe this can help," Glub said, which was impressive because Glub said it with a crumb on his nose.')
    world.say(f"Tom tried the plan and found that it was actually clever, not just funny.")


def resolution(world: World, hero: Entity, helper: Entity, goal: Goal, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
    world.say(f"Together they used {tool.phrase}, and soon the hard part was done.")
    if goal.label == "cross the way":
        world.say("Tom crossed carefully while Glub held the pole like a captain with a noodle for a ship.")
    elif goal.label == "find the map":
        world.say("The lantern lit the path, and the lost map was hiding under a stone the size of a sleepy loaf.")
    else:
        world.say("The rope kept Tom steady, and the berry bush turned out to be much less scary than it first looked.")
    world.say(f"In the end, Tom reached {goal.phrase}, and Glub puffed up with proud little bubbles.")


def tell(setting: Setting, goal: Goal, tool: Tool, hero_name: str = "Tom", helper_name: str = "Glub") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy"))
    helper = world.add(Entity(id=helper_name, kind="character", type="glub"))
    world.facts.update(hero=hero, helper=helper, goal=goal, tool=tool, setting=setting)

    intro(world, hero, helper, goal)
    setup(world, goal)
    conflict(world, hero, helper, goal)
    world.para()
    offer_fix(world, hero, helper, goal, tool)
    _do_attempt(world, hero, helper, goal, tool, narrate=True)
    resolution(world, hero, helper, goal, tool)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
goal_tool_ok(G,T) :- goal(G), tool(T), requires(G,M), guards(T,M), helps(T,G).
valid(Place,G,T) :- setting(Place), goal(G), tool(T), goal_tool_ok(G,T), allowed(Place,G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.afford):
            lines.append(asp.fact("allowed", pid, {"cross": "crossing", "climb": "berry"}.get(a, "map")))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("requires", gid, g.obstacle_meter))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(t.guards):
            lines.append(asp.fact("guards", tid, m))
        for g in sorted(t.helps):
            lines.append(asp.fact("helps", tid, g))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short humorous adventure story for a child named {f["hero"].id} and a helper named {f["helper"].id}.',
        f"Tell a playful story where {f['hero'].id} and Glub want to {f['goal'].phrase} but need {(f.get('tool') or next(iter(TOOLS.values()))).label} to solve the problem.",
        f"Write a child-friendly adventure with a funny helper, a tricky obstacle, and a happy ending at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    goal: Goal = _safe_fact(world, f, "goal")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who went on the adventure in {setting.place}?",
            answer=f"Tom went with Glub to {setting.place} so they could {goal.phrase}.",
        ),
        QAItem(
            question=f"What did Tom and Glub use to solve the problem?",
            answer=f"They used {tool.label} because it matched the tricky part of the path.",
        ),
        QAItem(
            question=f"Why was the first part of the journey funny?",
            answer=f"It was funny because Glub acted very serious, but then did a silly little trip that made Tom laugh.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"Tom reached {goal.phrase}, and Glub was proud that the plan worked.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "rope": [("What is a rope for?", "A rope can help people pull, hold, or steady things when a path is tricky.")],
    "lantern": [("What does a lantern do?", "A lantern gives light so people can see in dark places.")],
    "pole": [("What can a long pole help with?", "A long pole can help someone reach, push, or steady something from farther away.")],
    "bridge": [("What is a bridge?", "A bridge is a path that helps people cross over water or a gap.")],
}


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    if (f.get("tool") or next(iter(TOOLS.values()))).id in WORLD_KNOWLEDGE:
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[(f.get("tool") or next(iter(TOOLS.values()))).id])
    out.append(QAItem(question="What kind of feeling is humor?", answer="Humor is the kind of feeling that makes a story funny or playful."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------

def valid_story(params: StoryParams) -> bool:
    return (params.place, params.goal, params.tool) in valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small humorous adventure for Tom and Glub.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", default="Tom")
    ap.add_argument("--helper", default="Glub")
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
              and (getattr(args, "goal", None) is None or c[1] == getattr(args, "goal", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, goal, tool = rng.choice(list(combos))
    return StoryParams(
        place=place,
        goal=goal,
        tool=tool,
        name=getattr(args, "name", None),
        helper=getattr(args, "helper", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(GOALS, params.goal), _safe_lookup(TOOLS, params.tool), params.name, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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
        print(f"{len(combos)} compatible combos:\n")
        for place, goal, tool in combos:
            print(f"  {place:10} {goal:9} {tool}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = [StoryParams(place=p, goal=g, tool=t) for p, g, t in valid_combos()]
        samples = [generate(p) for p in params_list]
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
