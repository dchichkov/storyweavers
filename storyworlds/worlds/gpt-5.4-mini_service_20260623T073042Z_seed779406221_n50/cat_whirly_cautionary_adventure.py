#!/usr/bin/env python3
"""
storyworlds/worlds/cat_whirly_cautionary_adventure.py
======================================================

A small standalone story world built from the seed words "cat" and "whirly".
It tells a cautionary adventure about a curious cat, a whirly machine, a risky
choice, and a safer ending.

The world is modeled with typed entities, physical meters, emotional memes,
forward causal rules, and a declarative ASP twin for parity checks.
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
SENSIBLE_MIN = 2



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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper_gender: object | None = None
    cat: object | None = None
    helper: object | None = None
    wh_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    id: str
    label: str
    place_kind: str
    affords: set[str] = field(default_factory=set)
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
class Whirly:
    id: str
    label: str
    phrase: str
    sound: str
    motion: str
    risk: str
    safe_tool: str
    safe_tool_phrase: str
    safe_tool_label: str
    safe_plan: str
    tags: set[str] = field(default_factory=set)
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
class OutcomeTool:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    whirly: str
    tool: str
    cat_name: str
    cat_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
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


PLACES = {
    "attic": Place("attic", "the attic", "indoor", {"whirly"}),
    "workshop": Place("workshop", "the workshop", "indoor", {"whirly"}),
    "garden": Place("garden", "the garden", "outdoor", {"whirly"}),
}

WHIRLIES = {
    "fan": Whirly(
        id="fan",
        label="whirly fan",
        phrase="a whirly fan",
        sound="whirrrrr",
        motion="spin the air in circles",
        risk="knock over small things",
        safe_tool="switch",
        safe_tool_phrase="the fan switch",
        safe_tool_label="switch",
        safe_plan="turn the fan off and open the window",
        tags={"whirly", "spin"},
    ),
    "blender": Whirly(
        id="blender",
        label="whirly blender",
        phrase="a whirly blender",
        sound="whirrrrr",
        motion="spin the blades in a hurry",
        risk="splash food and scare the cat",
        safe_tool="lid",
        safe_tool_phrase="the lid and the off button",
        safe_tool_label="lid",
        safe_plan="put the lid on and ask a grown-up to stop it",
        tags={"whirly", "spin"},
    ),
}

TOOLS = {
    "switch": OutcomeTool("switch", "switch", "a switch", SENSIBLE_MIN + 1, 3, {"safe"}),
    "lid": OutcomeTool("lid", "lid", "a lid", SENSIBLE_MIN + 1, 3, {"safe"}),
    "stare": OutcomeTool("stare", "stare", "just staring at it", 1, 0, {"unsafe"}),
}

GIRL_NAMES = ["Mina", "Tia", "Luna", "Ivy", "Nina"]
BOY_NAMES = ["Theo", "Milo", "Kai", "Nico", "Arlo"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, w, _safe_lookup(WHIRLIES, w).safe_tool) for p in PLACES for w in WHIRLIES if w == "fan" or p != "garden"]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for wid, w in WHIRLIES.items():
        lines.append(asp.fact("whirly", wid))
        lines.append(asp.fact("safe_tool", wid, w.safe_tool))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
        lines.append(asp.fact("power", tid, t.power))
    lines.append(asp.fact("sense_min", SENSIBLE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,W,T) :- place(P), whirly(W), tool(T), safe_tool(W,T).
sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
"""


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
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cat and whirly cautionary adventure.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--whirly", choices=WHIRLIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
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
              and (getattr(args, "whirly", None) is None or c[1] == getattr(args, "whirly", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, whirly, tool = rng.choice(list(combos))
    gender = rng.choice(["girl", "boy"])
    cat_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = "girl" if gender == "boy" else "boy"
    helper_name = rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(place, whirly, tool, cat_name, gender, helper_name, helper_gender)


def _story_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    cat = world.add(Entity(params.cat_name, "character", "cat", "the cat", role="hero"))
    helper = world.add(Entity(params.helper_name, "character", "adult" if params.helper_gender == "girl" else "adult", "the helper", role="helper"))
    wh = _safe_lookup(WHIRLIES, params.whirly)
    tool = _safe_lookup(TOOLS, params.tool)
    world.facts.update(cat=cat, helper=helper, whirly=wh, tool=tool, place=world.place)

    cat.meters["curiosity"] = 1.0
    cat.memes["wonder"] = 1.0
    helper.memes["concern"] = 1.0
    wh_ent = world.add(Entity("whirly", "thing", "machine", wh.label))
    wh_ent.meters["spin"] = 1.0
    wh_ent.attrs["risk"] = wh.risk
    helper.meters["care"] = 1.0
    return world


def _warn(world: World) -> None:
    cat = world.get(world.facts["cat"].id)
    helper = world.get(world.facts["helper"].id)
    wh = world.facts["whirly"]
    cat.memes["want"] = 1.0
    world.say(f"{cat.id} found {wh.phrase} in {world.place.label}.")
    world.say(f"It made a bright whirrrr and wanted to {wh.motion}.")
    world.para()
    world.say(f"{cat.id} wanted to get closer, but {helper.id} held up a gentle hand.")
    world.say(f'"That can be tricky," {helper.id} said. "If we rush it, it could {wh.risk}."')


def _risk(world: World) -> None:
    cat = world.get(world.facts["cat"].id)
    wh_ent = world.get("whirly")
    wh_ent.meters["speed"] += 1
    cat.memes["alarm"] += 1
    wh_ent.meters["wobble"] += 1
    world.say(f"{cat.id} ignored the warning and reached anyway.")
    world.say(f"The {wh_ent.label} spun harder, and the room felt shaky.")


def _recovery(world: World, safe: OutcomeTool, wh: Whirly) -> None:
    cat = world.get(world.facts["cat"].id)
    helper = world.get(world.facts["helper"].id)
    cat.memes["relief"] += 1
    cat.memes["learn"] += 1
    helper.memes["pride"] += 1
    world.say(f"Then {helper.id} chose {safe.phrase} and showed {cat.id} how to use it.")
    world.say(f"They followed the safer plan: {wh.safe_plan}.")
    world.say(f"{cat.id} watched the {wh.label} settle down and felt brave for listening.")


def tell(params: StoryParams) -> World:
    world = _story_world(params)
    wh = world.facts["whirly"]
    safe = _safe_lookup(TOOLS, params.tool)
    _warn(world)
    world.para()
    _risk(world)
    world.para()
    _recovery(world, safe, wh)
    world.say(f"By the end, {world.facts['cat'].id} knew the whirly thing was best left to grown-up hands.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short cautionary adventure for a young child about a cat and a {f["whirly"].label}.',
        f"Tell a safe adventure story where {f['cat'].id} wants to touch the {f['whirly'].label}, but the helper warns them and they choose a safer way.",
        f'Write a simple story that includes the word "whirly" and ends with the cat learning a careful lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cat = f["cat"].id
    helper = f["helper"].id
    wh = f["whirly"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {cat}, a curious cat, and {helper}, who helps keep things safe around {wh.label}.",
        ),
        QAItem(
            question=f"What did {cat} want to do with the {wh.label}?",
            answer=f"{cat} wanted to get closer to it, but that would have been risky because it could {wh.risk}.",
        ),
        QAItem(
            question=f"How did the helper keep the adventure safe?",
            answer=f"The helper warned {cat}, then used {wh.safe_tool_phrase} and followed the safer plan.",
        ),
        QAItem(
            question=f"What did {cat} learn at the end?",
            answer=f"{cat} learned to stay careful and let grown-up hands handle the whirly machine.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    wh = world.facts["whirly"]
    out = [
        QAItem("What does whirly mean?", "Whirly means spinning or twirling around very fast."),
        QAItem("Why can a spinning machine be risky?", "A fast spinning machine can bump, wobble, or hurt if someone reaches too close."),
    ]
    if wh.id == "blender":
        out.append(QAItem("Why should a blender be handled carefully?", "A blender has sharp blades inside, so grown-ups should use it carefully with the lid on."))
    else:
        out.append(QAItem("Why should a fan be watched carefully?", "A fan can knock things over or make a mess if it spins too hard and gets touched."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams("attic", "fan", "switch", "Mina", "girl", "Theo", "boy"),
    StoryParams("workshop", "blender", "lid", "Nico", "boy", "Luna", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(0 if set(valid_combos()) == set(asp_valid_combos()) else 1)
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = getattr(args, "seed", None)
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
