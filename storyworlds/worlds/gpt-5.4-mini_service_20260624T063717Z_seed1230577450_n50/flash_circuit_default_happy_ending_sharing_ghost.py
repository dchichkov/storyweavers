#!/usr/bin/env python3
"""
storyworlds/worlds/flash_circuit_default_happy_ending_sharing_ghost.py
=====================================================================

A small Storyweavers storyworld about a gentle ghost, a flashing flashlight,
and a shared fix after a circuit goes dark.

Seed inspirations:
- flash
- circuit
- default

Style target:
- Ghost story
- Happy ending
- Sharing
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
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    can_share: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    circuit: object | None = None
    ghost: object | None = None
    helper: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    place: str
    indoor: bool
    dark: bool = True
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    type: str
    helps: set[str]
    default_mode: str
    shareable: bool = True
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
class StoryParams:
    place: str
    tool: str
    name: str
    helper_name: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def build_worlds() -> dict[str, Setting]:
    return {
        "attic": Setting(place="the attic", indoor=True, dark=True, affords={"flash", "sharing", "circuit"}),
        "hall": Setting(place="the hallway", indoor=True, dark=True, affords={"flash", "sharing", "circuit"}),
        "porch": Setting(place="the porch", indoor=False, dark=False, affords={"flash", "sharing", "circuit"}),
    }


SETTINGS = build_worlds()

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight with a bright beam",
        type="flashlight",
        helps={"flash"},
        default_mode="off",
        shareable=True,
    ),
    "circuit": Tool(
        id="circuit",
        label="circuit box",
        phrase="the old circuit box by the wall",
        type="circuit",
        helps={"circuit"},
        default_mode="off",
        shareable=False,
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a round lantern with a warm glow",
        type="lantern",
        helps={"flash"},
        default_mode="off",
        shareable=True,
    ),
}

CURATED = [
    StoryParams(place="attic", tool="flashlight", name="Mina", helper_name="Nell"),
    StoryParams(place="hall", tool="lantern", name="Ollie", helper_name="Pip"),
]


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_flash(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    tool = world.get("tool")
    if ghost.meters.get("dark", 0) < THRESHOLD:
        return out
    if tool.meters.get("shared", 0) < THRESHOLD:
        return out
    sig = ("flash",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["relief"] = ghost.memes.get("relief", 0) + 1
    out.append(f"The little light flashed, and the dark corners stopped feeling so lonely.")
    return out


def _r_sharing(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    helper = world.get("helper")
    tool = world.get("tool")
    if tool.meters.get("shared", 0) >= THRESHOLD:
        return out
    if ghost.memes.get("asking", 0) < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tool.meters["shared"] = 1
    helper.memes["kind"] = helper.memes.get("kind", 0) + 1
    out.append(f"{helper.label_word if hasattr(helper, 'label_word') else helper.label} shared the light without a fuss.")
    return out


def _r_circuit(world: World) -> list[str]:
    out = []
    circuit = world.get("circuit")
    tool = world.get("tool")
    if not circuit.meters.get("fixed", 0):
        return out
    if tool.meters.get("powered", 0) >= THRESHOLD:
        return out
    sig = ("circuit",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tool.meters["powered"] = 1
    out.append("Once the circuit was reset, the room hummed back to life.")
    return out


RULES = [
    Rule("flash", _r_flash),
    Rule("sharing", _r_sharing),
    Rule("circuit", _r_circuit),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, tool_def: Tool, name: str, helper_name: str) -> World:
    world = World(setting)
    ghost = world.add(Entity(id="ghost", kind="ghost", type="ghost", label=name, meters={"dark": 1}, memes={"longing": 1}))
    helper = world.add(Entity(id="helper", kind="character", type="girl", label=helper_name, memes={"care": 1}))
    tool = world.add(Entity(id="tool", type=tool_def.type, label=tool_def.label, phrase=tool_def.phrase, can_share=tool_def.shareable, meters={"powered": 0, "shared": 0}))
    circuit = world.add(Entity(id="circuit", type="circuit", label="circuit box", phrase="the old circuit box", meters={"fixed": 0}))
    ghost.meters["dark"] = 1 if setting.dark else 0
    world.say(f"{name} was a quiet little ghost who lived in {setting.place}.")
    world.say(f"{name} liked the {tool.label}, because its little flash made the dark corners feel friendly.")
    world.say(f"One evening, the lights went still, and even the hallway felt like it was holding its breath.")
    world.para()
    world.say(f"{name} reached for the {tool.label}, but the {tool.default_mode} little tool needed a kind hand to help it.")
    ghost.memes["asking"] = 1
    world.say(f"{helper_name} listened, smiled, and said they could share the light.")
    tool.meters["shared"] = 1
    circuit.meters["fixed"] = 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"In the end, the {tool.label} shone, the circuit hummed, and {name} floated happily beside {helper_name}, not lonely at all.")
    world.facts.update(ghost=ghost, helper=helper, tool=tool, circuit=circuit, setting=setting, tool_def=tool_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story in {f['setting'].place} about sharing a {(f.get('tool') or next(iter(TOOLS.values()))).label}.",
        f"Tell a happy ending story where {f['ghost'].label} sees a flash of light and a helper shares it.",
        f"Make a child-friendly ghost tale about a dark room, a circuit, and a kind shared flashlight.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    ghost = f["ghost"]
    helper = f["helper"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    setting = f["setting"].place
    return [
        QAItem(
            question=f"Where did {ghost.label} live?",
            answer=f"{ghost.label} lived in {setting}, where the dark corners could feel spooky until the light came on.",
        ),
        QAItem(
            question=f"Who shared the {tool.label} with {ghost.label}?",
            answer=f"{helper.label} shared the {tool.label}, so the little ghost would not have to face the dark alone.",
        ),
        QAItem(
            question="What helped the story end happily?",
            answer=f"The shared {tool.label} and the fixed circuit helped the room brighten, and {ghost.label} felt safe and happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a flashlight do?",
            answer="A flashlight makes a small beam of light so you can see in the dark.",
        ),
        QAItem(
            question="What is a circuit?",
            answer="A circuit is the path that electricity follows to power lights and other things.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something kind and fair.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for tool_id, tool in TOOLS.items():
            if setting.dark and "flash" in tool.helps:
                combos.append((place, tool_id))
    return combos


def explain_rejection(place: str, tool_id: str) -> str:
    return f"(No story: {tool_id} does not fit the mood and mechanics of {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghostly storyworld about flash, circuit, and sharing.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    choices = [(p, t) for p, t in valid_combos()
               if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
               and (getattr(args, "tool", None) is None or t == getattr(args, "tool", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tool = rng.choice(choices)
    return StoryParams(
        place=place,
        tool=tool,
        name=getattr(args, "name", None) or rng.choice(["Mina", "Nora", "Theo", "Pip"]),
        helper_name=getattr(args, "helper_name", None) or rng.choice(["Lia", "Nell", "Owen", "Rue"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TOOLS, params.tool), params.name, params.helper_name)
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
setting_dark(P) :- place(P), dark(P).
compatible(P, T) :- setting_dark(P), tool(T), flashes(T).
happy_ending(P, T) :- compatible(P, T), shares(T), circuit_fixed(P).
#show compatible/2.
#show happy_ending/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        if s.dark:
            lines.append(asp.fact("dark", p))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if "flash" in tool.helps:
            lines.append(asp.fact("flashes", t))
        if tool.shareable:
            lines.append(asp.fact("shares", t))
    for p, s in SETTINGS.items():
        if "circuit" in s.affords:
            lines.append(asp.fact("circuit_fixed", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


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
        print(asp_program("#show compatible/2.\n#show happy_ending/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(sorted(asp_valid_combos()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
