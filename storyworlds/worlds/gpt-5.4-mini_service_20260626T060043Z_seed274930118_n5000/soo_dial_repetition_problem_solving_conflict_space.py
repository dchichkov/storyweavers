#!/usr/bin/env python3
"""
Standalone storyworld: a tiny space-adventure about a ship, a stubborn dial,
and a crew that learns to solve problems without losing hope.

Premise seed:
---
A small crew on a quiet ship keeps trying the same radio call. The signal never
comes through. One child on board notices the dial is stuck on "low," and the
grown-up is too worried to stop and look. The child keeps saying, "Sooo..."
because the next try matters, and the word "dial" becomes part of the plan.

This world turns that seed into a simulated story model with:
- physical meters: signal strength, battery, heat, distance, repair progress
- emotional memes: hope, worry, conflict, patience, relief

The story shape is:
1) a hopeful space trip
2) repetition that does not yet work
3) a conflict when the dial refuses to cooperate
4) a problem-solving turn that fixes the dial
5) a resolved ending with a clear change in state
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

SPACEWORD = "soo"
DIALWORD = "dial"
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    child: object | None = None
    dial: object | None = None
    radio: object | None = None
    def __post_init__(self):
        for k in ["signal", "battery", "heat", "distance", "repair", "damage"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "conflict", "patience", "relief", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Ship:
    name: str
    setting: str
    crew_name: str
    child_name: str
    captain_name: str
    dial_stickiness: float
    signal_target: str
    radio_channel: str
    repeated_attempts: int = 0
    repaired: bool = False
    heard_response: bool = False
    facts: dict = field(default_factory=dict)
    ship: object | None = None
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
    ship_name: str
    setting: str
    child_name: str
    captain_name: str
    signal_target: str
    radio_channel: str
    dial_stickiness: float
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


SETTINGS = {
    "orbital_post": "a small orbital post above a blue planet",
    "dust_route": "a dust-colored route between two moons",
    "quiet_station": "a quiet station at the edge of a ringed world",
}

CHILD_NAMES = ["Mira", "Jori", "Tavi", "Nia", "Rin", "Pico"]
CAPTAIN_NAMES = ["Captain Sol", "Commander Vega", "Pilot Arin", "Navigator Cora"]
SHIPS = ["Star Dot", "Little Comet", "Moon Tap", "Echo Seed"]
TARGETS = ["the home harbor", "a sister ship", "base camp", "the rescue beacon"]
CHANNELS = ["7", "12", "19", "soo"]
DIAL_STICKINESS = [0.6, 0.8, 1.0, 1.2]


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.ship = Ship(
            name=params.ship_name,
            setting=params.setting,
            crew_name="crew",
            child_name=params.child_name,
            captain_name=params.captain_name,
            dial_stickiness=params.dial_stickiness,
            signal_target=params.signal_target,
            radio_channel=params.radio_channel,
        )

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.params)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.ship = copy.deepcopy(self.ship)
        return w
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]


def _signal_from_attempts(attempts: int, repaired: bool, dial_stickiness: float) -> float:
    base = 0.3 * attempts
    if repaired:
        base += 1.4
    penalty = max(0.0, dial_stickiness - 0.9) * 0.6
    return max(0.0, base - penalty)


def _do_attempt(world: World, narrate: bool = True) -> None:
    ship = world.ship
    ship.repeated_attempts += 1

    child = world.get("child")
    captain = world.get("captain")
    dial = world.get("dial")

    child.memes["hope"] += 0.4
    captain.memes["worry"] += 0.2
    dial.meters["damage"] += 0.1

    if narrate:
        world.say(
            f"{child.id} leaned toward the radio and said, \"{SPACEWORD}... {SPACEWORD}... maybe this time.\""
        )
        world.say(
            f"The {DIALWORD} clicked, but the ship still heard only a whisper."
        )

    signal = _signal_from_attempts(ship.repeated_attempts, ship.repaired, ship.dial_stickiness)
    world.facts["signal"] = signal
    world.facts["attempts"] = ship.repeated_attempts
    if signal >= THRESHOLD:
        ship.heard_response = True
        child.memes["relief"] += 0.5


def _conflict(world: World) -> None:
    child = world.get("child")
    captain = world.get("captain")
    dial = world.get("dial")
    if world.facts.get("signal", 0.0) >= THRESHOLD:
        return
    child.memes["conflict"] += 0.5
    captain.memes["worry"] += 0.4
    dial.meters["damage"] += 0.2
    world.say(
        f"{captain.id} said they should keep trying, but the {DIALWORD} stayed stuck and the room grew tense."
    )
    world.say(
        f"{child.id} frowned, because repeating the call again and again felt like talking to the stars without an answer."
    )


def _problem_solve(world: World) -> None:
    ship = world.ship
    child = world.get("child")
    captain = world.get("captain")
    dial = world.get("dial")

    if ship.heard_response:
        return

    dial.meters["repair"] += 1.0
    ship.repaired = True
    child.memes["patience"] += 0.6
    captain.memes["worry"] = max(0.0, captain.memes["worry"] - 0.2)
    world.say(
        f"{child.id} noticed the {DIALWORD} was set too low. \"What if we turn it gently?\" they asked."
    )
    world.say(
        f"Together they loosened the panel, cleared the sticky dust, and nudged the {DIALWORD} until it could move."
    )
    world.say(
        f"The captain tried one more call, but this time the ship was ready to listen."
    )
    _do_attempt(world, narrate=False)
    if ship.heard_response:
        child.memes["relief"] += 0.7
        captain.memes["pride"] += 0.6
        world.say(
            f"The radio finally answered, and the little ship filled with a bright, steady voice."
        )


def tell(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity(id=params.child_name, kind="character", type="child", label=params.child_name))
    captain = world.add(Entity(id=params.captain_name, kind="character", type="captain", label=params.captain_name))
    dial = world.add(Entity(id="dial", kind="thing", type="radio_dial", label="radio dial"))
    radio = world.add(Entity(id="radio", kind="thing", type="radio", label="radio set"))

    world.say(
        f"On {_safe_lookup(SETTINGS, params.setting)}, the ship {params.ship_name} floated like a tiny bright kite."
    )
    world.say(
        f"{child.id} loved listening for signals, and {captain.id} hoped the radio would reach {params.signal_target}."
    )
    world.say(
        f"But the {DIALWORD} on the radio was sticky, and every call sounded too small."
    )

    world.para()
    _do_attempt(world)
    _do_attempt(world)
    if not world.ship.heard_response:
        _conflict(world)
    _problem_solve(world)

    world.para()
    if world.ship.heard_response:
        world.say(
            f"In the end, {child.id} smiled at the shining screen while the ship drifted calmly through the dark."
        )
        world.say(
            f"The {DIALWORD} stayed fixed, the signal stayed strong, and the crew did not need to say {SPACEWORD} twice anymore."
        )
    else:
        world.say(
            f"The ship kept waiting, but the stars remained quiet."
        )

    world.facts.update(
        child=child,
        captain=captain,
        dial=dial,
        radio=radio,
        ship=world.ship,
        setting=params.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short space-adventure story for a young child that includes the repeated word '{SPACEWORD}' and a stubborn {DIALWORD}.",
        f"Tell a gentle story about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").id} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "captain").id} on {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")} where a radio call keeps failing until they solve the problem.",
        f"Write a child-friendly science-fiction story about repetition, conflict, and problem solving on a tiny ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    captain: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "captain")
    ship: Ship = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ship")
    dial: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "dial")

    return [
        QAItem(
            question=f"Why did {child.id} keep saying '{SPACEWORD}' near the radio?",
            answer=(
                f"{child.id} kept repeating '{SPACEWORD}' because they were trying again and again to make the signal reach {ship.signal_target}. "
                f"The first calls were too weak, so the repetition showed hope and patience."
            ),
        ),
        QAItem(
            question=f"What was wrong with the {DIALWORD} on the ship?",
            answer=(
                f"The {DIALWORD} was sticky and set too low, so the radio calls came through as whispers instead of a clear message."
            ),
        ),
        QAItem(
            question=f"How did {child.id} and {captain.id} solve the problem?",
            answer=(
                f"They opened the radio panel, cleared the sticky dust, and turned the {DIALWORD} gently until it moved properly. "
                f"After that, the next call worked."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"At the end, the ship had a strong signal, the {DIALWORD} was fixed, and {child.id} felt relieved instead of frustrated."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dial?",
            answer=(
                "A dial is a round control you turn to change a setting, like volume, speed, or radio strength."
            ),
        ),
        QAItem(
            question="Why do spaceships use radios?",
            answer=(
                "Spaceships use radios to send voices and signals across big distances where people cannot shout to each other."
            ),
        ),
        QAItem(
            question="What does repetition mean?",
            answer=(
                "Repetition means doing or saying something again and again. In a story, it can show trying, waiting, or practice."
            ),
        ),
        QAItem(
            question="What is problem solving?",
            answer=(
                "Problem solving means noticing what is wrong, thinking of a fix, and trying a useful plan to make things work better."
            ),
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(
        f"  ship: attempts={world.ship.repeated_attempts}, repaired={world.ship.repaired}, heard_response={world.ship.heard_response}"
    )
    return "\n".join(lines)


def explain_rejection(args) -> str:
    return "(No story: the requested options do not describe a sensible radio-and-dial conflict.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for ship in SHIPS:
        lines.append(asp.fact("ship", ship))
    for name in CHILD_NAMES:
        lines.append(asp.fact("child_name", name))
    for name in CAPTAIN_NAMES:
        lines.append(asp.fact("captain_name", name))
    for target in TARGETS:
        lines.append(asp.fact("target", target))
    for ch in CHANNELS:
        lines.append(asp.fact("channel", ch))
    for d in DIAL_STICKINESS:
        lines.append(asp.fact("stickiness", int(d * 10)))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, C, Cap, T, Ch, D) :- setting(T), child_name(C), captain_name(Cap), ship(S), target(T), channel(Ch), stick(D).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/6."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Simple parity check: all generated parameter combinations must be within the declarative set.
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str, str, str, float]]:
    combos = []
    for s in SHIPS:
        for setting in SETTINGS:
            for child in CHILD_NAMES:
                for cap in CAPTAIN_NAMES:
                    for target in TARGETS:
                        for ch in CHANNELS:
                            for d in DIAL_STICKINESS:
                                combos.append((s, setting, child, cap, target, ch, d))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world: repetition, conflict, problem solving.")
    ap.add_argument("--ship-name", choices=SHIPS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--captain-name", choices=CAPTAIN_NAMES)
    ap.add_argument("--signal-target", choices=TARGETS)
    ap.add_argument("--radio-channel", choices=CHANNELS)
    ap.add_argument("--dial-stickiness", type=float, choices=DIAL_STICKINESS)
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
    ship_name = getattr(args, "ship_name", None) or rng.choice(SHIPS)
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    captain_name = getattr(args, "captain_name", None) or rng.choice(CAPTAIN_NAMES)
    signal_target = getattr(args, "signal_target", None) or rng.choice(TARGETS)
    radio_channel = getattr(args, "radio_channel", None) or rng.choice(CHANNELS)
    dial_stickiness = getattr(args, "dial_stickiness", None) or rng.choice(DIAL_STICKINESS)
    if dial_stickiness < 0.6 or dial_stickiness > 1.2:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        ship_name=ship_name,
        setting=setting,
        child_name=child_name,
        captain_name=captain_name,
        signal_target=signal_target,
        radio_channel=radio_channel,
        dial_stickiness=dial_stickiness,
    )


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
    StoryParams(
        ship_name="Star Dot",
        setting="orbital_post",
        child_name="Mira",
        captain_name="Captain Sol",
        signal_target="the home harbor",
        radio_channel="soo",
        dial_stickiness=1.0,
    ),
    StoryParams(
        ship_name="Little Comet",
        setting="dust_route",
        child_name="Jori",
        captain_name="Navigator Cora",
        signal_target="a sister ship",
        radio_channel="12",
        dial_stickiness=1.2,
    ),
    StoryParams(
        ship_name="Echo Seed",
        setting="quiet_station",
        child_name="Nia",
        captain_name="Commander Vega",
        signal_target="base camp",
        radio_channel="19",
        dial_stickiness=0.8,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/6."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/6."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
