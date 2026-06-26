#!/usr/bin/env python3
"""
A small storyworld for a detective-style sharing tale with frost and cocoon.
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

# Physical and emotional thresholds for narration.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    detective: object | None = None
    partner: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    indoors: bool = True
    world: object | None = None
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
class Case:
    id: str
    clue: str
    miss: str
    reveal: str
    shares: str
    at_risk: str
    theme: str = "sharing"
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


@dataclass
class Tool:
    id: str
    label: str
    protects: set[str]
    helps_with: set[str]
    offer: str
    outcome: str
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


@dataclass
class StoryParams:
    case: str
    tool: str
    name: str
    gender: str
    partner: str
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
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "station": Setting(place="the little station"),
    "library": Setting(place="the quiet library"),
    "porch": Setting(place="the front porch"),
}

CASES = {
    "frost": Case(
        id="frost",
        clue="frost",
        miss="frost",
        reveal="the glass had a pale frost pattern",
        shares="shared the scarf",
        at_risk="window",
        theme="sharing",
    ),
    "cocoon": Case(
        id="cocoon",
        clue="cocoon",
        miss="cocoon",
        reveal="a cocoon was tucked in the tree nook",
        shares="shared the lamp",
        at_risk="tree",
        theme="sharing",
    ),
}

TOOLS = {
    "scarf": Tool(
        id="scarf",
        label="warm scarf",
        protects={"frost"},
        helps_with={"cold"},
        offer="share the warm scarf",
        outcome="wrapped them both warm",
    ),
    "lamp": Tool(
        id="lamp",
        label="small lamp",
        protects={"dark"},
        helps_with={"cocoon"},
        offer="share the small lamp",
        outcome="lit the nook just enough",
    ),
}


class ReasonRule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_cold(world: World) -> list[str]:
    out = []
    detective = world.get("detective")
    case = _safe_fact(world, world.facts, "case")
    if detective.meters.get(case.miss, 0) >= THRESHOLD and ("cold", case.id) not in world.fired:
        world.fired.add(("cold", case.id))
        detective.memes["worry"] = detective.memes.get("worry", 0) + 1
        out.append("The clue looked chilly and strange.")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    detective = world.get("detective")
    partner = world.get("partner")
    tool = _safe_fact(world, world.facts, "tool")
    case = _safe_fact(world, world.facts, "case")
    if detective.memes.get("worry", 0) >= THRESHOLD and ("share", tool.id) not in world.fired:
        world.fired.add(("share", tool.id))
        detective.memes["trust"] = detective.memes.get("trust", 0) + 1
        partner.memes["trust"] = partner.memes.get("trust", 0) + 1
        tool_owner = world.get(tool.id)
        tool_owner.worn_by = detective.id
        out.append(f"They decided to share the {tool.label} instead of arguing.")
        if case.id == "frost":
            out.append("The warm light made the frost easy to read.")
        else:
            out.append("The warm light reached the cocoon hiding in the branches.")
    return out


CAUSAL_RULES = [
    ReasonRule("cold", _r_cold),
    ReasonRule("share", _r_share),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_case_story(world: World, detective: Entity, partner: Entity, case: Case, tool: Tool) -> None:
    detective.meters[case.miss] = detective.meters.get(case.miss, 0) + 1
    world.say(
        f"{detective.id} was a little detective who loved sharing clues with {partner.id}."
    )
    world.say(
        f"At {world.setting.place}, {detective.id} noticed {case.clue} and said it felt like a mystery."
    )
    world.say(
        f"{partner.id} came close and frowned. {case.reveal.capitalize()}, and that meant the clue needed a careful look."
    )
    world.para()
    world.say(
        f"{detective.id} wanted to solve the case right away, but the clue was too chilly to inspect alone."
    )
    propagate(world, narrate=True)
    world.say(
        f"Then {partner.id} offered to {tool.offer}, and {detective.id} nodded."
    )
    detective.meters["solution"] = 1
    partner.meters["solution"] = 1
    world.para()
    world.say(
        f"Together they followed the clue. In the end, the case was solved because they shared the work."
    )
    world.say(
        f"The final answer was simple: {case.reveal}, and the friends left side by side, still sharing the {tool.label}."
    )


KNOWLEDGE = {
    "frost": [
        (
            "What is frost?",
            "Frost is a thin layer of ice that forms on cold surfaces when the air gets very chilly.",
        )
    ],
    "cocoon": [
        (
            "What is a cocoon?",
            "A cocoon is a soft covering some insects make while they change into adults.",
        )
    ],
    "sharing": [
        (
            "What does it mean to share?",
            "To share means to let someone else use something with you or have some of it too.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    case = _safe_fact(world, world.facts, "case")
    tool = _safe_fact(world, world.facts, "tool")
    detective = _safe_fact(world, world.facts, "detective")
    partner = _safe_fact(world, world.facts, "partner")
    return [
        f"Write a short detective story for young children that includes the word '{case.clue}'.",
        f"Tell a gentle mystery where {detective.id} and {partner.id} solve a case by sharing a {tool.label}.",
        f"Make a simple story about a small detective who finds a clue, feels stuck, and then shares something helpful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = _safe_fact(world, world.facts, "case")
    tool = _safe_fact(world, world.facts, "tool")
    detective = _safe_fact(world, world.facts, "detective")
    partner = _safe_fact(world, world.facts, "partner")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {detective.id}, a little detective, and {partner.id}, who helped solve the mystery.",
        ),
        QAItem(
            question=f"What clue did {detective.id} notice?",
            answer=f"{detective.id} noticed {case.clue}, and it turned out to be the start of a real mystery.",
        ),
        QAItem(
            question=f"How did they solve the case?",
            answer=f"They solved it by sharing the {tool.label} and looking at the clue together.",
        ),
    ]
    if case.id == "frost":
        qa.append(QAItem(
            question="Why was the clue hard to inspect?",
            answer="The clue was hard to inspect because the frost made it chilly and unclear at first.",
        ))
    else:
        qa.append(QAItem(
            question="Why did they need a light?",
            answer="They needed a light because the cocoon was hiding in a dim little nook.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("sharing", "detective", world.facts["case"].id):
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(key, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
case_miss(frost,frost).
case_miss(cocoon,cocoon).

tool_helps(scarf,cold).
tool_helps(lamp,cocoon).

need_share(Case,Tool) :- case_miss(Case,Miss), tool_helps(Tool,Miss).
valid(Case,Tool) :- need_share(Case,Tool).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid, case in CASES.items():
        lines.append(asp.fact("case_miss", cid, case.miss))
    for tid, tool in TOOLS.items():
        for h in sorted(tool.helps_with):
            lines.append(asp.fact("tool_helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid, case in CASES.items():
        for tid, tool in TOOLS.items():
            if case.miss in tool.helps_with or case.miss in tool.protects:
                combos.append((cid, tid))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld about frost, cocoon, and sharing.")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--partner")
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
    if getattr(args, "case", None) and getattr(args, "tool", None):
        case = _safe_lookup(CASES, getattr(args, "case", None))
        tool = _safe_lookup(TOOLS, getattr(args, "tool", None))
        if case.miss not in tool.protects and case.miss not in tool.helps_with:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "case", None):
        combos = [c for c in combos if c[0] == getattr(args, "case", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[1] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    case_id, tool_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mina", "Iris", "Toby", "Nico", "Lina", "Eli"])
    partner = getattr(args, "partner", None) or rng.choice(["a friend", "an aunt", "a brother", "a neighbor"])
    return StoryParams(case=case_id, tool=tool_id, name=name, gender=gender, partner=partner)


def generate(params: StoryParams) -> StorySample:
    world = World(Setting(place="the little station"))
    detective = world.add(Entity(id=params.name, kind="character", type=params.gender))
    partner = world.add(Entity(id="partner", kind="character", type="friend", label=params.partner))
    case = _safe_lookup(CASES, params.case)
    tool = _safe_lookup(TOOLS, params.tool)
    world.facts["detective"] = detective
    world.facts["partner"] = partner
    world.facts["case"] = case
    world.facts["tool"] = tool
    build_case_story(world, detective, partner, case, tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(case="frost", tool="scarf", name="Mina", gender="girl", partner="a friend"),
    StoryParams(case="cocoon", tool="lamp", name="Toby", gender="boy", partner="an aunt"),
]


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} valid combinations:\n")
        for case, tool in combos:
            print(f"  {case:8} {tool}")
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
