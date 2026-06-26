#!/usr/bin/env python3
"""
Standalone storyworld: dandruff, bravery, and bedtime.

A small bedtime-story simulation about a child who feels shy about flakes in
their hair, finds the courage to ask for help, and ends the night feeling clean
and calm.
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
# Domain model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

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
class Room:
    name: str = "bedroom"
    bedtime: bool = True
    light: str = "soft"
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
    phrase: str
    action: str
    clears: set[str]
    comfort: float = 0.0
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
    name: str
    gender: str
    parent: str
    room: str
    tool: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
ROOMS = {
    "bedroom": Room(name="bedroom", bedtime=True, light="soft"),
    "bathroom": Room(name="bathroom", bedtime=True, light="bright"),
}

TOOLS = {
    "brush": Tool(
        id="brush",
        label="soft brush",
        phrase="a soft brush",
        action="brush out the flakes",
        clears={"flakes"},
        comfort=0.6,
    ),
    "shampoo": Tool(
        id="shampoo",
        label="gentle shampoo",
        phrase="a gentle shampoo",
        action="wash the hair gently",
        clears={"flakes"},
        comfort=0.8,
    ),
    "hat": Tool(
        id="hat",
        label="sleep cap",
        phrase="a sleep cap",
        action="cover the hair for the night",
        clears=set(),
        comfort=0.2,
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Ella", "Nora"]
BOY_NAMES = ["Theo", "Noah", "Leo", "Finn", "Owen"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def bed_time_notice(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"At bedtime, {child.id} was tucked into {child.pronoun('possessive')} "
        f"quiet room, with the lamp glowing like a small moon."
    )
    world.say(
        f"{child.id} loved the calm part of the night, but {child.pronoun('possessive')} "
        f"scalp had been itchy all day."
    )


def reveal_flakes(world: World, child: Entity) -> None:
    child.memes["shy"] += 1
    child.meters["flakes"] += 1
    world.say(
        f"When {child.id} patted {child.pronoun('possessive')} hair, a few tiny dandruff "
        f"flakes drifted onto the pillow."
    )
    world.say(
        f"{child.id} felt embarrassed and wanted to hide under the blanket."
    )


def ask_for_help(world: World, child: Entity, parent: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"Then {child.id} took a brave breath and called softly, "
        f'"{parent.id}, my head feels itchy. Can you help me?"'
    )
    world.say(
        f"{parent.id} smiled, because speaking up was a brave thing to do."
    )


def choose_tool(world: World, parent: Entity, tool: Tool, child: Entity) -> None:
    if tool.id == "hat":
        pass
    world.say(
        f"{parent.id} brought out {tool.phrase} and sat beside the bed."
    )
    if tool.id == "shampoo":
        world.say(
            f'"Let us {tool.action}," {parent.id} said. "That should help your scalp feel better."'
        )
    else:
        world.say(
            f'"Let me {tool.action}," {parent.id} said, careful and gentle.'
        )


def help_child(world: World, child: Entity, parent: Entity, tool: Tool) -> None:
    child.meters["flakes"] = max(0.0, child.meters.get("flakes", 0.0) - 1.0)
    child.memes["shy"] = max(0.0, child.memes.get("shy", 0.0) - 1.0)
    child.memes["comfort"] += tool.comfort
    parent.memes["tenderness"] += 1.0
    world.say(
        f"They worked slowly, and the tiny flakes did not seem so big anymore."
    )
    if tool.id == "shampoo":
        world.say(
            f"After the gentle wash, {child.id}'s hair felt clean and soft."
        )
    else:
        world.say(
            f"After the careful brushing, the pillow looked much tidier."
        )


def resolve_bravery(world: World, child: Entity, parent: Entity) -> None:
    child.memes["bravery"] += 1
    child.memes["peace"] += 1
    world.say(
        f"{child.id} hugged {parent.pronoun('object')} and smiled."
    )
    world.say(
        f'"I was nervous," {child.id} said, "but I was brave and asked for help."'
    )
    world.say(
        f"Soon {child.id} was ready for sleep, with a calm head and a brave heart."
    )


def tell(room: Room, tool: Tool, name: str, gender: str, parent_type: str) -> World:
    world = World(room)
    child = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id=parent_type.capitalize(), kind="character", type=parent_type))

    bed_time_notice(world, child, parent)
    world.para()
    reveal_flakes(world, child)
    ask_for_help(world, child, parent)
    choose_tool(world, parent, tool, child)
    help_child(world, child, parent, tool)
    world.para()
    resolve_bravery(world, child, parent)

    world.facts = {
        "child": child,
        "parent": parent,
        "tool": tool,
        "room": room,
    }
    return world


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combo(room: str, tool: str) -> bool:
    return room in ROOMS and tool in {"brush", "shampoo"}


def explain_rejection(room: str, tool: str) -> str:
    if tool == "hat":
        return "(No story: a sleep cap can hide hair, but it does not really solve dandruff.)"
    return "(No story: that combination does not make sense for this small bedtime problem.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(T) :- tool(T), clears(T, flakes).
valid(R, T) :- room(R), tool(T), at_risk(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(t.clears):
            lines.append(asp.fact("clears", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(r, t) for r in ROOMS for t in TOOLS if valid_combo(r, t)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, tool = f["child"], f["parent"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        "Write a short bedtime story for a young child whose hair has dandruff, "
        "and who finds the courage to ask for help.",
        f"Tell a gentle story about {child.id}, {parent.id}, and {tool.label} at bedtime.",
        "Write a child-friendly story where bravery helps solve a small itchy problem before sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, tool = f["child"], f["parent"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Why did {child.id} feel shy near the pillow?",
            answer=f"{child.id} felt shy because dandruff flakes drifted onto the pillow and made the problem feel noticeable.",
        ),
        QAItem(
            question=f"What brave thing did {child.id} do?",
            answer=f"{child.id} took a brave breath and asked {parent.id} for help instead of hiding under the blanket.",
        ),
        QAItem(
            question=f"What helped {child.id} feel better before sleep?",
            answer=f"{parent.id} used {tool.phrase} to help clean up the flakes, and that made bedtime feel calmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is dandruff?",
            answer="Dandruff is made of tiny dry flakes that can come off a person's scalp and fall onto hair or clothes.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary, like asking for help, even when you feel nervous.",
        ),
        QAItem(
            question="Why do people brush or wash their hair?",
            answer="People brush or wash their hair to keep it clean, smooth, and comfortable.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Serialization / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about dandruff and bravery.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    room = getattr(args, "room", None) or rng.choice(list(ROOMS))
    tool = getattr(args, "tool", None) or rng.choice(["brush", "shampoo"])
    if not valid_combo(room, tool):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, room=room, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(ROOMS, params.room), _safe_lookup(TOOLS, params.tool), params.name, params.gender, params.parent)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible room/tool combos:")
        for room, tool in combos:
            print(f"  {room:8} {tool}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for room in ROOMS:
            for tool in TOOLS:
                if valid_combo(room, tool):
                    params = StoryParams(
                        name="Mia",
                        gender="girl",
                        parent="mother",
                        room=room,
                        tool=tool,
                    )
                    samples.append(generate(params))
    else:
        seen = set()
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
