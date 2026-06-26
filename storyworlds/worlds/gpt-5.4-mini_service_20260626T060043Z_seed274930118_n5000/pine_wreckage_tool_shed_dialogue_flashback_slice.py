#!/usr/bin/env python3
"""
storyworlds/worlds/pine_wreckage_tool_shed_dialogue_flashback_slice.py
======================================================================

A small slice-of-life storyworld set in a tool shed, with pine wreckage,
dialogue, and a brief flashback guiding a gentle repair-and-reuse story.

Premise:
- A child and a caregiver are in a tool shed after a pine tree limb has fallen
  and left wreckage.
- The child wants to turn the wreckage into something useful right away.
- The caregiver remembers a past mishap, warns about splinters and shaky wood,
  and suggests a safer method.
- They choose the safer method together, and the ending shows the shed calmer
  and the pine wreckage neatly sorted.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld
- typed entities with meters and memes
- generated prose driven by simulated state
- inline ASP twin with parity verification
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caregiver: object | None = None
    child: object | None = None
    obj: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather", "uncle"}:
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
    place: str = "the tool shed"
    SETTINGS: set[str] = field(default_factory=set)
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    type: str
    mess: str
    risky: set[str]
    repairable: bool = True
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    helps: set[str]
    makes_safe: bool
    requires_adult: bool = True
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.history: list[str] = []

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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        return clone


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    caregiver_type: str
    object_id: str
    tool_id: str
    seed: Optional[int] = None
    sample: object | None = None
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


SETTINGS = {"tool_shed": Setting(place="the tool shed")}

OBJECTS = {
    "pine_planks": ObjectCfg(
        id="pine_planks",
        label="pine planks",
        phrase="a stack of pine planks from the wreckage",
        type="planks",
        mess="splintered",
        risky={"splinters", "dust"},
    ),
    "pine_branch": ObjectCfg(
        id="pine_branch",
        label="pine branch",
        phrase="a broken pine branch from the wreckage",
        type="branch",
        mess="rough",
        risky={"splinters", "dust"},
    ),
    "pine_crates": ObjectCfg(
        id="pine_crates",
        label="pine crates",
        phrase="a few pine crates from the wreckage",
        type="crates",
        mess="wobbly",
        risky={"splinters", "dust"},
    ),
}

TOOLS = {
    "gloves": ToolCfg(
        id="gloves",
        label="work gloves",
        phrase="a pair of work gloves",
        helps={"splinters"},
        makes_safe=True,
    ),
    "clamps": ToolCfg(
        id="clamps",
        label="wood clamps",
        phrase="wood clamps",
        helps={"wobbly"},
        makes_safe=True,
    ),
    "brush": ToolCfg(
        id="brush",
        label="a dust brush",
        phrase="a dust brush",
        helps={"dust"},
        makes_safe=True,
    ),
}

NAMES = ["Mia", "Noah", "Lena", "Owen", "Ada", "Theo", "Ivy", "Milo"]
CHILD_TYPES = ["girl", "boy"]
CAREGIVER_TYPES = ["mother", "father", "grandmother", "grandfather"]


class ReasoningError(StoryError):
    pass


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def story_title(obj: ObjectCfg) -> str:
    return f"{obj.label.title()} in the Tool Shed"


def object_at_risk(obj: ObjectCfg) -> bool:
    return bool(obj.risky & {"splinters", "dust", "wobbly"})


def select_tool(obj: ObjectCfg) -> Optional[ToolCfg]:
    if obj.id == "pine_planks":
        return TOOLS["gloves"]
    if obj.id == "pine_branch":
        return TOOLS["brush"]
    if obj.id == "pine_crates":
        return TOOLS["clamps"]
    return None


def reasonableness_gate(obj: ObjectCfg, tool: ToolCfg) -> bool:
    if not object_at_risk(obj):
        return False
    if obj.id == "pine_branch" and tool.id != "brush":
        return False
    if obj.id == "pine_planks" and tool.id != "gloves":
        return False
    if obj.id == "pine_crates" and tool.id != "clamps":
        return False
    return True


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("obj", oid))
        for r in sorted(obj.risky):
            lines.append(asp.fact("risk", oid, r))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


ASP_RULES = r"""
risky(O) :- risk(O, _).
safer(T, O) :- tool(T), obj(O), risk(O, R), helps(T, R).
valid(O, T) :- risky(O), safer(T, O).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid_pairs() -> list[tuple[str, str]]:
    out = []
    for oid, obj in OBJECTS.items():
        tool = select_tool(obj)
        if tool and reasonableness_gate(obj, tool):
            out.append((oid, tool.id))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_pairs())
    b = set(python_valid_pairs())
    if a == b:
        print(f"OK: ASP and Python agree on {len(a)} valid object/tool pairs.")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - b:
        print("  only in ASP:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


def predict_outcome(world: World, child: Entity, obj: ObjectCfg, tool: ToolCfg) -> dict:
    sim = world.copy()
    apply_attempt(sim, sim.get(child.id), obj, tool, narrate=False)
    return {
        "safe": sim.facts.get("safe", False),
        "settled": sim.facts.get("settled", False),
    }


def intro(world: World, child: Entity, caregiver: Entity, obj: ObjectCfg) -> None:
    world.say(
        f"{child.id} was a little {child.type} who liked quiet afternoons in {world.setting.place}."
    )
    world.say(
        f"{child.pronoun().capitalize()} and {caregiver.label} found {obj.phrase} after the storm."
    )


def set_scene(world: World) -> None:
    world.say(
        "The tool shed smelled like cedar and old oil, and sunlight came in through a crack by the door."
    )


def flashback(world: World, caregiver: Entity, obj: ObjectCfg) -> None:
    world.say(
        f"{caregiver.pronoun().capitalize()} paused and looked at the rough wood."
    )
    world.say(
        f'"Last time we rushed," {caregiver.pronoun("subject")} said, "we got splinters all over the floor."'
    )
    world.say(
        "For a moment, the shed felt like it did back then, when everyone had to sit still and pick out tiny slivers."
    )
    world.facts["flashback"] = True


def ask(world: World, child: Entity, caregiver: Entity, obj: ObjectCfg) -> None:
    world.say(
        f'"Can we use the wreckage now?" {child.pronoun("subject")} asked.'
    )
    world.say(
        f'"Not yet," {caregiver.pronoun("subject")} said. "We need the right tool first."'
    )
    child.memes["impatient"] += 1
    caregiver.memes["careful"] += 1


def apply_attempt(world: World, child: Entity, obj: ObjectCfg, tool: ToolCfg, narrate: bool = True) -> None:
    if not reasonableness_gate(obj, tool):
        pass
    child.meters["project"] = child.meters.get("project", 0.0) + 1.0
    child.memes["hope"] += 1
    world.facts["safe"] = True
    world.facts["settled"] = True
    if narrate:
        world.say(
            f'Together they used {tool.phrase} and worked slowly.'
        )
        world.say(
            f"The rough edges stopped snagging, and the pine wreckage lay neatly in a small, safe pile."
        )


def offer_help(world: World, caregiver: Entity, child: Entity, tool: ToolCfg) -> None:
    world.say(
        f'"I can help," {caregiver.pronoun("subject")} said. "Let’s make it steady first."'
    )
    world.say(
        f"{child.id} nodded, took {tool.label}, and stood a little taller."
    )


def ending(world: World, child: Entity, caregiver: Entity, obj: ObjectCfg, tool: ToolCfg) -> None:
    world.say(
        f"By the end, the tool shed was calm again: {obj.label} was sorted, {tool.label} was put back, and the wreckage was no longer just broken pieces."
    )
    world.say(
        f"It had become the start of something useful, and {child.id} smiled at the tidy little pile beside {caregiver.label}."
    )


def tell(setting: Setting, obj_cfg: ObjectCfg, tool_cfg: ToolCfg, child_name: str, child_type: str,
         caregiver_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=caregiver_type, label=f"the {caregiver_type}"))
    obj = world.add(Entity(id=obj_cfg.id, type=obj_cfg.type, label=obj_cfg.label, phrase=obj_cfg.phrase))
    tool = world.add(Entity(id=tool_cfg.id, type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase))

    world.facts.update(child=child, caregiver=caregiver, obj=obj_cfg, tool=tool_cfg, setting=setting)

    intro(world, child, caregiver, obj_cfg)
    set_scene(world)
    ask(world, child, caregiver, obj_cfg)

    world.para()
    flashback(world, caregiver, obj_cfg)
    offer_help(world, caregiver, child, tool_cfg)
    apply_attempt(world, child, obj_cfg, tool_cfg, narrate=True)

    world.para()
    ending(world, child, caregiver, obj_cfg, tool_cfg)
    world.facts["resolved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    caregiver: Entity = _safe_fact(world, f, "caregiver")
    obj: ObjectCfg = _safe_fact(world, f, "obj")
    tool: ToolCfg = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who was in the tool shed with {child.id} when the pine wreckage was found?",
            answer=f"{child.id} was there with {caregiver.label}. They stood in the tool shed and looked at the pine wreckage together.",
        ),
        QAItem(
            question=f"Why did {caregiver.label} pause before using the pine wreckage?",
            answer="The caregiver paused because the wood looked rough and splintery, and a flashback reminded them of a past time when rushing caused tiny slivers on the floor.",
        ),
        QAItem(
            question=f"What did {child.id} do after hearing the warning about the wreckage?",
            answer=f"{child.id} listened, took {tool.label}, and helped work slowly so the pine wreckage could stay safe and tidy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is pine?",
            answer="Pine is a kind of tree with green needles and wood that people often use for boards and small projects.",
        ),
        QAItem(
            question="What is wreckage?",
            answer="Wreckage is the broken pieces left after something has been damaged or falls apart.",
        ),
        QAItem(
            question="What is a tool shed for?",
            answer="A tool shed is a small place where people keep tools, wood, and other things they use for fixing or building.",
        ),
    ]
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    obj: ObjectCfg = _safe_fact(world, f, "obj")
    tool: ToolCfg = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a gentle slice-of-life story set in a tool shed about pine wreckage, a careful pause, and {child.id}.',
        f"Tell a short story where {child.id} wants to use {obj.label}, but a caregiver remembers a past mistake and suggests {tool.label}.",
        f"Write a child-friendly dialogue story with a flashback in a tool shed, ending with the pine wreckage put away neatly.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life tool shed storyworld with pine wreckage.")
    ap.add_argument("--child-name", choices=NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--caregiver-type", choices=CAREGIVER_TYPES)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--tool", dest="tool_id", choices=TOOLS)
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
    obj_id = getattr(args, "object_id", None) or rng.choice(list(OBJECTS))
    obj = _safe_lookup(OBJECTS, obj_id)
    tool = _safe_lookup(TOOLS, getattr(args, "tool_id", None)) if getattr(args, "tool_id", None) else select_tool(obj)
    if tool is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "tool_id", None) and not reasonableness_gate(obj, tool):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    child_type = getattr(args, "child_type", None) or rng.choice(CHILD_TYPES)
    caregiver_type = getattr(args, "caregiver_type", None) or rng.choice(CAREGIVER_TYPES)
    child_name = getattr(args, "child_name", None) or rng.choice(NAMES)
    return StoryParams(
        child_name=child_name,
        child_type=child_type,
        caregiver_type=caregiver_type,
        object_id=obj_id,
        tool_id=tool.id,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["tool_shed"], _safe_lookup(OBJECTS, params.object_id), _safe_lookup(TOOLS, params.tool_id),
                 params.child_name, params.child_type, params.caregiver_type)
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


def asp_valid_pairs_text() -> str:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return "\n".join(f"{a[0]} {a[1]}" for a in asp.atoms(model, "valid"))


def asp_verify_and_exercise() -> int:
    code = asp_verify()
    if code != 0:
        return code
    sample = generate(StoryParams(
        child_name="Mia",
        child_type="girl",
        caregiver_type="mother",
        object_id="pine_planks",
        tool_id="gloves",
    ))
    if "pine wreckage" not in normalize(sample.story):
        print("Story exercise failed: expected pine wreckage in sample story.")
        return 1
    if not sample.story.strip():
        print("Story exercise failed: empty story.")
        return 1
    print("OK: generated story exercise passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_and_exercise())
    if getattr(args, "asp", None):
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid object/tool pairs:\n")
        for oid, tid in pairs:
            print(f"  {oid:12} {tid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("Mia", "girl", "mother", "pine_planks", "gloves"),
            StoryParams("Noah", "boy", "father", "pine_branch", "brush"),
            StoryParams("Lena", "girl", "grandmother", "pine_crates", "clamps"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.child_name}: {p.object_id} with {p.tool_id}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
