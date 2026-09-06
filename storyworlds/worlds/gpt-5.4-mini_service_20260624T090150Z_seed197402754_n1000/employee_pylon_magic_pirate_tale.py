#!/usr/bin/env python3
"""
A small storyworld for a pirate tale with an employee, a pylon, and a touch of magic.
The premise is a harbor worker who wants to use a magic trick near a pylon, but the
boss worries the spell may damage the worksite. The turn is a careful warning and
a surprising safer method; the ending shows the job done and the pylon shining.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    boss: object | None = None
    employee: object | None = None
    pylon: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "spark": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "magic": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "captain", "boss"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "employee", "sailor"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the harbor"
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
class MagicMove:
    id: str
    verb: str
    gerund: str
    risk: str
    fix: str
    zone: set[str]
    keyword: str = "magic"
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
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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


@dataclass(frozen=True)
class StoryArc:
    id: str
    move: str
    need: str
    danger: str
    warning: str
    plan: str
    result: str
    celebration: str
    cause_answer: str
    action_answer: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"glow", "sparkle", "float"}),
    "dock": Setting(place="the dock", affords={"glow", "sparkle", "float"}),
    "shipyard": Setting(place="the shipyard", affords={"glow", "sparkle", "float"}),
}

MOVES = {
    "glow": MagicMove(
        id="glow",
        verb="make the lantern glow",
        gerund="making lanterns glow",
        risk="bright sparks",
        fix="a brass lantern cover",
        zone={"air", "hands"},
        keyword="magic",
    ),
    "sparkle": MagicMove(
        id="sparkle",
        verb="make the rope sparkle",
        gerund="making rope sparkle",
        risk="glitter dust",
        fix="a sailor's cloth wrap",
        zone={"hands", "rope"},
        keyword="magic",
    ),
    "float": MagicMove(
        id="float",
        verb="make a crate float",
        gerund="making crates float",
        risk="wandering waves",
        fix="a tied cargo net",
        zone={"crate", "water"},
        keyword="magic",
    ),
}

TOOLS = [
    Tool(
        id="lantern_cover",
        label="a brass lantern cover",
        covers={"air"},
        guards={"spark"},
        prep="put a brass cover over the lantern first",
        tail="slipped the brass cover back on the lantern",
    ),
    Tool(
        id="cloth_wrap",
        label="a sailor's cloth wrap",
        covers={"hands", "rope"},
        guards={"dust"},
        prep="wrap the rope in a sailor's cloth first",
        tail="tied the cloth wrap around the rope",
    ),
    Tool(
        id="cargo_net",
        label="a cargo net",
        covers={"crate", "water"},
        guards={"damage"},
        prep="tie the crate in a cargo net first",
        tail="fastened the cargo net around the crate",
    ),
]

EMPLOYEE_NAMES = ["Nina", "Milo", "Tess", "Jory", "Pia", "Finn"]
BOSS_NAMES = ["Captain Reed", "Boss Marla", "First Mate June"]
TRAITS = ["brave", "clever", "cheerful", "stubborn", "lively"]

ARCS = {
    "fog_signal": StoryArc(
        id="fog_signal",
        move="glow",
        need="a pea-soup fog hid a family skiff from the pier",
        danger="loose sparks could scorch the pylon's signal pennant",
        warning='"A bright idea still needs a careful hand," {boss} warned.',
        plan="shield the lantern, then blink it three times toward the channel",
        result="the skiff followed the three golden blinks safely home",
        celebration="the rescued family rang a tiny brass bell",
        cause_answer="A thick fog hid a family skiff from the pier.",
        action_answer="They covered the lantern and flashed three safe signals.",
    ),
    "night_delivery": StoryArc(
        id="night_delivery",
        move="glow",
        need="the harbor healer needed a medicine parcel before moonrise",
        danger="an uncovered flare could startle the pony waiting beside the pylon",
        warning='"Let us make a useful light, not a frightening one," said {boss}.',
        plan="hood the lantern and carry its gentle glow along the painted path",
        result="the employee found the healer's blue door and delivered the parcel",
        celebration="the healer hung a paper star where the soft light had guided them",
        cause_answer="The harbor healer needed a medicine parcel before moonrise.",
        action_answer="They hooded the lantern and followed its gentle light to the healer.",
    ),
    "lost_bell": StoryArc(
        id="lost_bell",
        move="glow",
        need="the tide bell had fallen among the dark rocks below the quay",
        danger="wild sparks could burn the old seaweed ropes tied to the pylon",
        warning='"Search slowly, matey; the tide is quicker than it looks," {boss} said.',
        plan="cover the lantern and sweep its glow across one rock at a time",
        result="a green glint revealed the bell before the rising tide reached it",
        celebration="the repaired bell chimed once for every worker on the quay",
        cause_answer="The tide bell had fallen among the rocks below the quay.",
        action_answer="They shielded the lantern and searched the rocks one by one.",
    ),
    "tangled_rigging": StoryArc(
        id="tangled_rigging",
        move="sparkle",
        need="a training ship's rigging had twisted into a dangerous knot",
        danger="flying glitter dust could hide the colored safety marks on the pylon",
        warning='"No pirate cuts a knot before learning what it holds," {boss} said.',
        plan="wrap the rope, make only the trapped strand sparkle, and loosen it by hand",
        result="the bright strand showed exactly which loop to free",
        celebration="the young deckhands raised a patchwork sail without a single snap",
        cause_answer="The training ship's rigging had twisted into a dangerous knot.",
        action_answer="They wrapped the rope and made only the trapped strand sparkle.",
    ),
    "hidden_mooring": StoryArc(
        id="hidden_mooring",
        move="sparkle",
        need="storm foam had hidden the rope that held a little ferry",
        danger="sparkling dust could make the wet pylon too slippery to climb near",
        warning='"Feet on the boards and eyes on the rope," {boss} called.',
        plan="bind the rope in cloth and send one silver shimmer along its length",
        result="the shimmer traced the rope to a loose mooring ring",
        celebration="the ferry captain painted a silver stripe around the repaired ring",
        cause_answer="Storm foam had hidden the ferry's mooring rope.",
        action_answer="They wrapped the rope and traced it with one silver shimmer.",
    ),
    "crab_rescue": StoryArc(
        id="crab_rescue",
        move="sparkle",
        need="a crab had backed into a maze of discarded fishing line",
        danger="a cloud of glitter could confuse the crab and coat the pylon steps",
        warning='"Small sailors need calm seas too," {boss} whispered.',
        plan="cover the line and make each safe strand twinkle before lifting it away",
        result="the crab followed the clear path back to a tide pool",
        celebration="the crab raised one claw beside the clean pylon as if waving goodbye",
        cause_answer="A crab was trapped in discarded fishing line.",
        action_answer="They made the safe strands twinkle and lifted the line away.",
    ),
    "medicine_crate": StoryArc(
        id="medicine_crate",
        move="float",
        need="a medicine crate had slipped from a visiting ship into the water",
        danger="an untethered floating crate could ram the pylon with the tide",
        warning='"Give every floating thing a line home," {boss} ordered.',
        plan="fasten the net to the pier before lifting the crate on a small magic wave",
        result="the net guided the dry crate between the pilings and onto the dock",
        celebration="the ship's cook shared warm apple buns with the whole crew",
        cause_answer="A medicine crate had fallen from a visiting ship.",
        action_answer="They tethered a cargo net before floating the crate to the dock.",
    ),
    "duckling_crossing": StoryArc(
        id="duckling_crossing",
        move="float",
        need="three ducklings were stranded on a low board as the tide rose",
        danger="a wandering magic wave could bump their board against the pylon",
        warning='"The gentlest rescue begins with a strong knot," {boss} said.',
        plan="net the board loosely, then float it across the quiet side of the pier",
        result="the mother duck met all three ducklings in the sheltered cove",
        celebration="four neat wakes shone copper in the sunset beside the pylon",
        cause_answer="Three ducklings were stranded while the tide was rising.",
        action_answer="They netted the board and floated it through the quiet water.",
    ),
    "festival_cargo": StoryArc(
        id="festival_cargo",
        move="float",
        need="the children's pirate festival was missing its chest of paper crowns",
        danger="the chest could drift into the pylon and soak every crown",
        warning='"Treasure is no fun when it becomes harbor litter," {boss} said.',
        plan="lace a cargo net around the chest and pull while the magic held it level",
        result="the chest skimmed safely under the bunting and reached the festival",
        celebration="each child wore a paper crown while the pylon flew a red flag",
        cause_answer="The pirate festival needed its chest of paper crowns.",
        action_answer="They netted the chest and floated it level to the festival.",
    ),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A move is risky when it touches the at-risk zone.
risky(M) :- move(M), zone(M, Z), tool_target(T, Z).

% A tool is a compatible fix when it covers the risky zone and guards the risk kind.
fix(M, T) :- risky(M), move(M), tool(T), zone(M, Z), covers(T, Z), risk_kind(M, R), guards(T, R).

has_fix(M) :- fix(M, _).
valid_story(S, M) :- setting(S), affords(S, M), has_fix(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("risk_kind", mid, "spark" if mid == "glow" else ("dust" if mid == "sparkle" else "damage")))
        for z in sorted(m.zone):
            lines.append(asp.fact("zone", mid, z))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
    for z in {"air", "hands", "rope", "crate", "water"}:
        lines.append(asp.fact("tool_target", "x", z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid in sorted(setting.affords):
            move = _safe_lookup(MOVES, mid)
            if any(t for t in TOOLS if move_risk_kind(move) in t.guards and move_zone(move) & t.covers):
                combos.append((sid, mid))
    return combos


def move_zone(move: MagicMove) -> set[str]:
    return set(move.zone)


def move_risk_kind(move: MagicMove) -> str:
    return {"glow": "spark", "sparkle": "dust", "float": "damage"}[move.id]


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    move: str
    name: str
    boss: str
    trait: str
    arc: str = "fog_signal"
    opening: int = 0
    turn: int = 0
    ending: int = 0
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


def _do_magic(world: World, employee: Entity, move: MagicMove, narrate: bool = True) -> None:
    employee.memes["magic"] += 1
    if move.id == "glow":
        world.zone = {"air", "hands"}
        world.get("pylon").meters["spark"] += 1
    elif move.id == "sparkle":
        world.zone = {"hands", "rope"}
        world.get("pylon").meters["dust"] += 1
    else:
        world.zone = {"crate", "water"}
        world.get("pylon").meters["damage"] += 1
    employee.memes["joy"] += 1


def predict(world: World, employee: Entity, move: MagicMove) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get(employee.id), move, narrate=False)
    pylon = sim.get("pylon")
    return {"harm": pylon.meters["damage"] > 0 or pylon.meters["spark"] > 0 or pylon.meters["dust"] > 0}


def select_tool(move: MagicMove) -> Optional[Tool]:
    for tool in TOOLS:
        if move_risk_kind(move) in tool.guards and move.zone & tool.covers:
            return tool
    return None


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    employee = world.add(Entity(id=params.name, kind="character", type="employee"))
    boss = world.add(Entity(id="boss", kind="character", type="boss", label=params.boss))
    pylon = world.add(Entity(id="pylon", kind="thing", type="pylon", label="the pylon"))
    pylon.meters["spark"] = 0.0
    pylon.meters["dust"] = 0.0
    pylon.meters["damage"] = 0.0

    move = _safe_lookup(MOVES, params.move)
    tool = select_tool(move)
    compatible_arcs = [arc for arc in ARCS.values() if arc.move == move.id]
    arc = ARCS.get(params.arc)
    if arc not in compatible_arcs:
        arc = compatible_arcs[0]
    if tool is None:
        raise ValueError(f"No safety tool is available for {move.id}")

    fmt = {
        "name": employee.id,
        "boss": boss.label,
        "place": world.setting.place,
        "trait": params.trait,
        "move": move.verb,
        "need": arc.need,
        "danger": arc.danger,
        "plan": arc.plan,
        "tool": tool.label,
    }
    openings = [
        "{name} was the {trait} employee of a small pirate crew at {place}. While other pirates polished spyglasses, {name} practiced gentle magic beside the pylon.",
        '"All hands to the pylon!" called {boss}. {name}, a {trait} pirate employee at {place}, tucked away a magic charm and hurried over.',
        "The pylon at {place} had weathered a hundred tides. Its newest pirate helper was {name}, a {trait} employee who knew a little useful magic.",
        "On the pirate crew's busiest morning, {name} checked ropes, counted crates, and swept the boards around the pylon. The {trait} employee kept one magic trick for emergencies.",
    ]
    turn_leads = [
        "Instead of rushing, {name} asked what the magic might touch.",
        '"Then we make the magic smaller and the safety bigger," {name} decided.',
        "The employee took one slow breath, studied the wind and water, and changed the plan.",
        "A good pirate solves the danger before chasing the treasure, so {name} fetched {tool}.",
    ]
    ending_frames = [
        "That evening, {celebration}. The pylon stood unharmed beneath the first star, and {name} knew careful magic was the bravest kind.",
        '"Job done, matey," {boss} said as {celebration}. Beside them, the clean pylon cast a long stripe across the evening water.',
        "By sunset, {celebration}. {name} coiled the last rope at the foot of the pylon, proud that the safest plan had also been the cleverest.",
        "Soon, {celebration}. The crew sailed home past the pylon, where one quiet reflection shimmered like a silver coin.",
    ]

    world.say(openings[params.opening % len(openings)].format(**fmt))
    if params.opening % 2 == 0:
        world.say(f"Then trouble arrived: {arc.need}.")
    world.para()

    if params.opening % 2:
        world.say(f"The day's trouble was plain: {arc.need}.")
        world.say(f"{employee.id} offered to {move.verb}, but {arc.danger}.")
    else:
        world.say(f"{employee.id} reached for magic and offered to {move.verb}.")
        world.say(f"{boss.label} stopped the crew because {arc.danger}.")
    if predict(world, employee, move)["harm"]:
        world.say(arc.warning.format(**fmt))
        employee.memes["worry"] += 1

    world.para()
    world.say(turn_leads[params.turn % len(turn_leads)].format(**fmt))
    if params.turn % 2 == 0:
        world.say(f"Together, the two pirates chose to {arc.plan}. They checked {tool.label} twice before beginning.")
    else:
        world.say(f"Their new plan was to {arc.plan}. {boss.label} tested the knot while {employee.id} watched the pylon.")
    _do_magic(world, employee, move)
    employee.memes["pride"] += 1
    if params.turn % 3 == 0:
        world.say(f"At {employee.id}'s signal, the magic answered, and {arc.result}.")
    elif params.turn % 3 == 1:
        world.say(f"A pinch of magic did its work without touching the pylon, and {arc.result}.")
    else:
        world.say(f'"Steady now," said {employee.id}. The careful spell held, so {arc.result}.')

    world.para()
    world.say(
        ending_frames[params.ending % len(ending_frames)].format(
            **fmt,
            celebration=arc.celebration,
        )
    )

    world.facts.update(employee=employee, boss=boss, pylon=pylon, move=move, tool=tool, arc=arc)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    emp = _safe_fact(world, f, "employee")
    move = _safe_fact(world, f, "move")
    arc = f["arc"]
    return [
        f'Write a child-friendly pirate tale about an employee who uses "{move.keyword}" near a pylon when {arc.need}.',
        f"Tell a gentle sea adventure where {emp.id} must {arc.plan} without damaging a pylon.",
        f"Write a pirate story about teamwork, a safer choice, a pylon, and a little magic by the sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    emp, boss, move, tool, arc = f["employee"], f["boss"], f["move"], f["tool"], f["arc"]
    return [
        QAItem(
            question="What problem did the pirate crew need to solve?",
            answer=arc.cause_answer,
        ),
        QAItem(
            question=f"Why did {boss.label} worry about the pylon?",
            answer=f"{boss.label} worried because {arc.danger}.",
        ),
        QAItem(
            question=f"How did {emp.id} and {boss.label} use the magic safely?",
            answer=arc.action_answer,
        ),
        QAItem(
            question="What proved that their careful plan worked?",
            answer=f"Their plan worked because {arc.result}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pylon?",
            answer="A pylon is a tall post or support that can stand near water, roads, or docks.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something surprising or enchanted happens, like a glow, a sparkle, or a floating crate.",
        ),
        QAItem(
            question="What is a harbor?",
            answer="A harbor is a safe place near the water where boats can stop.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with an employee, a pylon, and magic.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--move", choices=MOVES.keys())
    ap.add_argument("--name")
    ap.add_argument("--boss", choices=BOSS_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--arc", choices=ARCS.keys())
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
    combos = valid_combos()
    requested_arc = getattr(args, "arc", None)
    requested_move = getattr(args, "move", None)
    if requested_arc and (not requested_move or ARCS[requested_arc].move == requested_move):
        combos = [c for c in combos if c[1] == ARCS[requested_arc].move]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if requested_move:
        combos = [c for c in combos if c[1] == requested_move]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, move = rng.choice(list(combos))
    arc_choices = [arc.id for arc in ARCS.values() if arc.move == move]
    arc = requested_arc if requested_arc in arc_choices else rng.choice(arc_choices)
    return StoryParams(
        place=place,
        move=move,
        name=getattr(args, "name", None) or rng.choice(EMPLOYEE_NAMES),
        boss=getattr(args, "boss", None) or rng.choice(BOSS_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
        arc=arc,
        opening=rng.randrange(4),
        turn=rng.randrange(4),
        ending=rng.randrange(4),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("Mismatch between ASP and Python:")
    print("Only Python:", sorted(py - cl))
    print("Only ASP:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="harbor", move="glow", name="Nina", boss="Captain Reed", trait="clever", arc="fog_signal"),
    StoryParams(place="dock", move="sparkle", name="Milo", boss="Boss Marla", trait="brave", arc="tangled_rigging", opening=1, turn=1, ending=1),
    StoryParams(place="shipyard", move="float", name="Tess", boss="First Mate June", trait="lively", arc="duckling_crossing", opening=2, turn=2, ending=2),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
