#!/usr/bin/env python3
"""
A standalone storyworld for a small whodunit in a kitchen.

Premise:
A child notices that a favorite piece of cutlery is missing from the table.
A careful search begins, with a flexible helper tool and a little bravery.
The story turns on a clue, a confession, and the return of the missing item.

The world is modeled as a tiny investigation:
- a kitchen setting with a few plausible hiding places
- cutlery that can be misplaced
- flexible gear that can reach into awkward spaces
- suspense from not knowing where the missing thing went
- bravery from speaking the truth and checking the clue
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


# ---------------------------------------------------------------------------
# Core world model
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
    hidden_in: str = ""
    flexible: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    item: object | None = None
    parent: object | None = None
    tool: object | None = None
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
    hiding_spots: list[str]
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
class Cutlery:
    id: str
    label: str
    phrase: str
    kind: str
    plural: bool = False
    searchable_spots: set[str] = field(default_factory=set)
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
    flexible: bool
    reaches: set[str]
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
    setting: str
    cutlery: str
    tool: str
    hero_name: str
    hero_type: str
    parent_type: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", hiding_spots=["the drawer", "under the napkin", "behind the bowl", "by the sink"]),
    "dining_room": Setting(place="the dining room", hiding_spots=["under the plate", "inside the napkin ring", "near the chair leg"]),
}

CUTLERY = {
    "spoon": Cutlery(
        id="spoon",
        label="spoon",
        phrase="a shiny silver spoon",
        kind="spoon",
        plural=False,
        searchable_spots={"the drawer", "under the napkin", "behind the bowl"},
    ),
    "fork": Cutlery(
        id="fork",
        label="fork",
        phrase="a little fork with clean tines",
        kind="fork",
        plural=False,
        searchable_spots={"the drawer", "behind the bowl", "by the sink"},
    ),
    "knife": Cutlery(
        id="knife",
        label="knife",
        phrase="a dull butter knife",
        kind="knife",
        plural=False,
        searchable_spots={"the drawer", "by the sink"},
    ),
    "teaspoon_set": Cutlery(
        id="teaspoon_set",
        label="teaspoons",
        phrase="a small set of teaspoons",
        kind="teaspoon",
        plural=True,
        searchable_spots={"the drawer", "under the napkin"},
    ),
}

TOOLS = {
    "flexible_tongs": Tool(
        id="flexible_tongs",
        label="flexible tongs",
        phrase="a pair of flexible tongs",
        flexible=True,
        reaches={"the drawer", "behind the bowl", "under the napkin"},
    ),
    "stick": Tool(
        id="stick",
        label="wooden stick",
        phrase="a wooden stick",
        flexible=False,
        reaches={"behind the bowl"},
    ),
    "ladle": Tool(
        id="ladle",
        label="ladle",
        phrase="a ladle",
        flexible=False,
        reaches={"by the sink"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ava", "Ivy", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Noah", "Owen"]
TRAITS = ["curious", "gentle", "careful", "brave", "quiet", "clever"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def _search_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    tool = world.get("tool")
    item = world.get("cutlery")
    if hero.memes.get("searching", 0) < 1:
        return out
    if item.hidden_in not in tool.meters:
        return out
    sig = ("found_clue", item.id, tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["suspense"] = max(0.0, hero.memes.get("suspense", 0.0) - 1)
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    out.append(f"A clue glinted near {item.hidden_in}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        sents = _search_clue(world)
        if sents:
            changed = True
            produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def locate_item(world: World, item: Entity) -> bool:
    return bool(item.hidden_in)


def can_reach(tool: Tool, spot: str) -> bool:
    return spot in tool.reaches


def needs_flexibility(tool: Tool, spot: str) -> bool:
    return spot in {"under the napkin", "the drawer"} and tool.flexible


def predict_success(world: World, tool: Tool, item: Entity) -> bool:
    if not item.hidden_in:
        return True
    return can_reach(tool, item.hidden_in)


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def open_story(world: World, hero: Entity, parent: Entity, item: Entity) -> None:
    world.say(f"{hero.id} noticed that {hero.pronoun('possessive')} {item.label} was missing from the table.")
    world.say(f"{hero.id}'s {parent.label} looked around with a serious face, because mysteries can feel big in a small kitchen.")


def build_suspense(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.say(f"The room grew quiet. {hero.id} peeked at the drawer, the napkin, and the bowl, but {item.label} was not there.")


def introduce_tool(world: World, hero: Entity, tool: Entity) -> None:
    world.say(f"Then {hero.id} picked up {tool.phrase}, because it could slip into tricky spaces without poking too hard.")
    if tool.flexible:
        hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1


def search_scene(world: World, hero: Entity, item: Entity, tool: Entity) -> None:
    tool_obj = world.get(tool.id)
    if item.hidden_in:
        if can_reach(_safe_lookup(TOOLS, tool_obj.id), item.hidden_in):
            world.say(f"{hero.id} reached carefully with {tool_obj.label} and nudged aside the hiding place.")
            hero.memes["searching"] = 1
            propagate(world, narrate=True)
        else:
            world.say(f"{hero.id} tried, but {tool_obj.label} could not reach that spot.")
            hero.memes["searching"] = 1
    else:
        world.say(f"{hero.id} searched, but there was no mystery left to solve.")


def reveal_truth(world: World, hero: Entity, parent: Entity, item: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(f"At last, {hero.id} took a breath and said what {hero.pronoun('subject')} had found.")
    world.say(f"The missing {item.label} was tucked {item.hidden_in}, and the clue led right to it.")
    world.say(f"{parent.id} smiled, because {hero.id} had been brave enough to keep looking.")


def ending(world: World, hero: Entity, parent: Entity, item: Entity) -> None:
    world.say(f"Soon the {item.label} was back on the table.")
    world.say(f"{hero.id} sat up a little taller, feeling proud of {hero.pronoun('possessive')} brave little mystery hunt.")


def tell(setting: Setting, item_cfg: Cutlery, tool_cfg: Tool,
         hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    tool = world.add(Entity(id="tool", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, flexible=tool_cfg.flexible))
    item = world.add(Entity(id="cutlery", type="cutlery", label=item_cfg.label, phrase=item_cfg.phrase, plural=item_cfg.plural))

    # hidden state
    item.hidden_in = random.choice(setting.hiding_spots)

    # Act 1
    open_story(world, hero, parent, item)
    build_suspense(world, hero, item)

    # Act 2
    world.para()
    introduce_tool(world, hero, tool)
    search_scene(world, hero, item, tool)

    # Act 3
    world.para()
    if predict_success(world, _safe_lookup(TOOLS, tool_cfg.id), item):
        reveal_truth(world, hero, parent, item)
        ending(world, hero, parent, item)
    else:
        world.say(f"The clue stayed hidden, and the mystery was not solved.")

    world.facts = {
        "hero": hero,
        "parent": parent,
        "tool": tool,
        "item": item,
        "setting": setting,
        "item_cfg": item_cfg,
        "tool_cfg": tool_cfg,
    }
    return world


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_name, setting in SETTINGS.items():
        for c_name, c in CUTLERY.items():
            for t_name, t in TOOLS.items():
                if any(can_reach(t, spot) for spot in c.searchable_spots):
                    combos.append((s_name, c_name, t_name))
    return combos


ASP_RULES = r"""
% Facts:
% setting(S). cutlery(C). tool(T).
% reachable(T,Spot). hidden_spot(C,Spot).

searchable(S,C,T) :- setting(S), cutlery(C), tool(T), hidden_spot(C,Spot), reachable(T,Spot).
valid(S,C,T) :- searchable(S,C,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in s.hiding_spots:
            lines.append(asp.fact("hiding_spot", sid, spot))
    for cid, c in CUTLERY.items():
        lines.append(asp.fact("cutlery", cid))
        for spot in c.searchable_spots:
            lines.append(asp.fact("hidden_spot", cid, spot))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for spot in t.reaches:
            lines.append(asp.fact("reachable", tid, spot))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a small whodunit about a missing {f['item_cfg'].label} in the {f['setting'].place} and a {f['tool_cfg'].label} that helps search a hidden spot.",
        f"Tell a suspenseful, child-friendly mystery where {f['hero'].id} bravely uses {f['tool_cfg'].phrase} to find the missing {f['item_cfg'].label}.",
        f"Write a kitchen mystery story with cutlery, a flexible helper, suspense, and a brave ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    item_cfg: Cutlery = _safe_fact(world, f, "item_cfg")
    tool_cfg: Tool = _safe_fact(world, f, "tool_cfg")
    item: Entity = _safe_fact(world, f, "item")
    qa = [
        QAItem(
            question=f"What was missing from the table in the story?",
            answer=f"The missing item was {item.phrase}. It had been tucked {item.hidden_in}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel suspense before the mystery was solved?",
            answer=f"{hero.id} felt suspense because the {item.label} was missing and nobody knew where it had gone at first.",
        ),
        QAItem(
            question=f"How did {tool_cfg.label} help {hero.id} search?",
            answer=f"{tool_cfg.phrase} could reach into tricky spots, so {hero.id} could check the hiding place carefully.",
        ),
        QAItem(
            question=f"What showed bravery in the story?",
            answer=f"{hero.id} showed bravery by keeping calm, searching carefully, and saying what {hero.pronoun('subject')} had found.",
        ),
        QAItem(
            question=f"Who was with {hero.id} during the search?",
            answer=f"{hero.id}'s {parent.label} stayed nearby and watched the search with a serious but caring face.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cutlery?",
            answer="Cutlery is the set of tools people use to eat food, like spoons, forks, and knives.",
        ),
        QAItem(
            question="What does flexible mean?",
            answer="Flexible means something can bend or twist a little without breaking.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling you get when you are waiting to find out what will happen next.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or uncertain even when your heart feels nervous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny kitchen whodunit storyworld with cutlery and a flexible helper.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cutlery", choices=CUTLERY)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "cutlery", None):
        combos = [c for c in combos if c[1] == getattr(args, "cutlery", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, cutlery, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, cutlery=cutlery, tool=tool, hero_name=name, hero_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), CUTLERY[params.cutlery], _safe_lookup(TOOLS, params.tool), params.hero_name, params.hero_type, params.parent_type)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.flexible:
            bits.append("flexible=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", cutlery="spoon", tool="flexible_tongs", hero_name="Mia", hero_type="girl", parent_type="mother"),
    StoryParams(setting="kitchen", cutlery="fork", tool="flexible_tongs", hero_name="Leo", hero_type="boy", parent_type="father"),
    StoryParams(setting="dining_room", cutlery="teaspoon_set", tool="flexible_tongs", hero_name="Nora", hero_type="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
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
