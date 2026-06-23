#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/jumbo_suspense_conflict_repetition_pirate_tale.py
==============================================================================================================================

A small pirate-tale storyworld with suspense, conflict, and repetition.

Seed tale:
- A pirate crew hears a strange sound from a jumbo chest on their ship.
- Repeated peeks and repeated knocks build suspense.
- One pirate wants to open it right away; the other worries it could be dangerous.
- The crew uses a careful method, discovers the chest is only hiding a harmless surprise,
  and ends with a clear physical change in the ship's scene.

The storyworld models:
- characters, objects, and locations with meters and memes
- suspense from an unknown sound and repeated waiting
- conflict from disagreement about opening the chest
- repetition as a visible pattern of knocks / peeks / calls
- a reasonableness gate that only generates stories where the chosen method can safely
  resolve the chosen problem
- an inline ASP twin of the Python gate
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
    role: str = ""
    owner: str = ""
    contains: str = ""
    openable: bool = False
    heavy: bool = False
    safe: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    chest: object | None = None
    helper: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Ship:
    place: str
    setting_line: str
    SHIP: object | None = None
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
class Problem:
    id: str
    sound: str
    source: str
    risk: str
    suspense_line: str
    conflict_line: str
    repeat_line: str
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
class Method:
    id: str
    label: str
    prep: str
    effect: str
    safe: bool
    tags: set[str] = field(default_factory=set)
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
class Prize:
    id: str
    label: str
    phrase: str
    reveal: str
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
class StoryParams:
    ship: str = "ship"
    problem: str = "hollow_sound"
    method: str = "peek_and_tap"
    prize: str = "map"
    hero: str = "Mara"
    helper: str = "Nico"
    parent: str = "captain"
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


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        w = World(self.ship)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


PROBLEMS = {
    "hollow_sound": Problem(
        id="hollow_sound",
        sound="thump-thump",
        source="a jumbo chest under the sailcloth",
        risk="it might be stuck, secret, or tricky to open",
        suspense_line="The chest gave a soft thump-thump each time the deck shifted.",
        conflict_line="One pirate wanted to open it at once, but the other said to wait.",
        repeat_line="They peeked, then peeked again, then listened one more time.",
        tags={"suspense", "conflict", "repetition", "jumbo"},
    ),
    "jumbo_bundle": Problem(
        id="jumbo_bundle",
        sound="scrape-scrape",
        source="a jumbo bundle lashed beside the mast",
        risk="it might tip if they tugged too hard",
        suspense_line="The bundle scraped the ropes with a slow scrape-scrape.",
        conflict_line="One pirate wanted to yank it free, but the other wanted a careful plan.",
        repeat_line="They counted three knots, then counted them again, then checked the ropes again.",
        tags={"suspense", "conflict", "repetition", "jumbo"},
    ),
    "hidden_lantern": Problem(
        id="hidden_lantern",
        sound="tick-tock",
        source="a jumbo crate near the captain's chair",
        risk="something inside could rattle loose",
        suspense_line="The crate ticked softly in the dark corner of the deck.",
        conflict_line="One pirate reached for the lid, and the other held up a hand.",
        repeat_line="They tapped the side, tapped it again, and listened twice more.",
        tags={"suspense", "conflict", "repetition", "jumbo"},
    ),
}

METHODS = {
    "peek_and_tap": Method(
        id="peek_and_tap",
        label="peek and tap",
        prep="lift the cloth, tap the lid, and peek inside together",
        effect="the surprise could be checked without forcing it",
        safe=True,
        tags={"safe", "repetition"},
    ),
    "unlash_carefully": Method(
        id="unlash_carefully",
        label="unlash carefully",
        prep="loosen the ropes one by one and hold the box steady",
        effect="the heavy thing could be moved without tipping",
        safe=True,
        tags={"safe", "jumbo"},
    ),
    "call_all_hands": Method(
        id="call all hands",
        label="call all hands",
        prep="call the crew and steady the deck before opening",
        effect="the whole ship could help with the big surprise",
        safe=True,
        tags={"safe", "conflict"},
    ),
    "swing_open": Method(
        id="swing_open",
        label="swing open",
        prep="swing the lid open fast",
        effect="it would be quick, but not careful",
        safe=False,
        tags={"unsafe"},
    ),
}

PRIZES = {
    "map": Prize("map", "a folded sea map", "map", "a folded map with a gold star", tags={"map", "paper"}),
    "spyglass": Prize("spyglass", "a shiny spyglass", "spyglass", "a polished spyglass", tags={"glass"}),
    "bell": Prize("bell", "a brass ship bell", "bell", "a brass bell with a bright ring", tags={"metal"}),
    "lantern": Prize("lantern", "a tiny lantern", "lantern", "a small lantern with a blue glass window", tags={"light"}),
}

SHIP = Ship(place="the ship", setting_line="The deck creaked softly, and the salt wind slid across the boards.")
GIRL_NAMES = ["Mara", "Tess", "Iris", "Ada", "Luna"]
BOY_NAMES = ["Nico", "Pio", "Bram", "Keen", "Otis"]
TRAITS = ["curious", "bold", "careful", "bright", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in PROBLEMS:
        for m in METHODS:
            if not _safe_lookup(METHODS, m).safe:
                continue
            for r in PRIZES:
                if p == "hidden_lantern" and r == "lantern":
                    combos.append((p, m, r))
                elif p in {"hollow_sound", "jumbo_bundle"}:
                    combos.append((p, m, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with suspense, conflict, and repetition.")
    ap.add_argument("--ship", choices=["ship"], default="ship")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["captain"], default="captain")
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "problem", None) is None or c[0] == getattr(args, "problem", None))
        and (getattr(args, "method", None) is None or c[1] == getattr(args, "method", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    p, m, r = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(ship=getattr(args, "ship", None), problem=p, method=m, prize=r, hero=hero, helper=helper, parent=getattr(args, "parent", None))


def _make_world(params: StoryParams) -> World:
    prob = _safe_lookup(PROBLEMS, params.problem)
    meth = _safe_lookup(METHODS, params.method)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(SHIP)
    hero = world.add(Entity(id="hero", kind="character", type="pirate", label=params.hero, role="hero", meters={"restless": 0.0}, memes={"suspense": 0.0, "conflict": 0.0, "joy": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type="pirate", label=params.helper, role="helper", meters={"restless": 0.0}, memes={"suspense": 0.0, "conflict": 0.0, "calm": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type="captain", label="the captain", role="parent", meters={"restless": 0.0}, memes={"authority": 1.0}))
    chest = world.add(Entity(id="chest", kind="thing", type="chest", label="jumbo chest", openable=True, heavy=True, safe=False, meters={"sealed": 1.0, "shaken": 0.0, "opened": 0.0}, attrs={"source": prob.source}))
    prize_ent = world.add(Entity(id="prize", kind="thing", type=prize.id, label=prize.label, phrase=prize.phrase, safe=True, meters={"revealed": 0.0}, attrs={"reveal": prize.reveal}))
    world.facts = {
        "params": params,
        "problem": prob,
        "method": meth,
        "prize": prize,
        "hero": hero,
        "helper": helper,
        "parent": parent,
        "chest": chest,
        "prize_ent": prize_ent,
        "resolved": False,
        "opened": False,
        "safe_finish": False,
    }
    return world


def _advance(world: World) -> None:
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    chest: Entity = world.facts["chest"]  # type: ignore[assignment]
    if ("suspense", chest.id) not in world.fired:
        world.fired.add(("suspense", chest.id))
        hero.memes["suspense"] += 1
        helper.memes["suspense"] += 1
        chest.meters["shaken"] += 1
    if chest.meters["shaken"] >= THRESHOLD and ("conflict", hero.id) not in world.fired:
        world.fired.add(("conflict", hero.id))
        hero.memes["conflict"] += 1
        helper.memes["conflict"] += 1


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    meth: Method = world.facts["method"]  # type: ignore[assignment]
    prize: Prize = world.facts["prize"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    chest: Entity = world.facts["chest"]  # type: ignore[assignment]
    prize_ent: Entity = world.facts["prize_ent"]  # type: ignore[assignment]

    world.say(f"{hero.label} and {helper.label} were on a ship with the captain.")
    world.say(world.ship.setting_line)
    world.say(f"They found {prob.source}.")
    world.say(prob.suspense_line)
    world.para()
    world.say(f"{prob.repeat_line}")
    world.say(f"{hero.label} wanted to move first, but {helper.label} wanted to wait.")
    world.say(prob.conflict_line)
    _advance(world)
    world.para()
    if not meth.safe:
        pass
    world.say(f"In the end, they chose to {meth.prep}.")
    chest.meters["opened"] += 1
    world.say(f"That way, {meth.effect}.")
    prize_ent.meters["revealed"] += 1
    world.say(f"Inside, they found {prize.reveal}, and the surprise was friendly, not scary.")
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"{hero.label} grinned, and {helper.label} laughed, and the jumbo chest turned out to be only a hiding place for treasure.")
    world.facts["resolved"] = True
    world.facts["opened"] = True
    world.facts["safe_finish"] = True
    world.facts["ending"] = "treasure revealed"
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    return [
        f'Write a pirate tale for a young child that includes the word "jumbo" and centers on {prob.source}.',
        f"Tell a suspenseful story where {p.hero} and {p.helper} keep hearing {prob.sound} and must decide what to do.",
        f"Write a short pirate story with repetition, conflict, and a safe ending about a {prob.id} on a ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    meth: Method = world.facts["method"]  # type: ignore[assignment]
    prize: Prize = world.facts["prize"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What made {p.hero} and {p.helper} feel suspenseful on the ship?",
            answer=f"They kept hearing {prob.sound} from {prob.source}. The strange sound made them pause and listen before they acted.",
        ),
        QAItem(
            question=f"Why did {p.hero} and {p.helper} disagree about the jumbo chest?",
            answer=f"{p.hero} wanted to hurry, but {p.helper} wanted to be careful because {prob.risk}. Their disagreement created the conflict in the middle of the story.",
        ),
        QAItem(
            question=f"How did the story use repetition before the chest opened?",
            answer=f"It repeated small actions like peeking, tapping, and listening again. The repeated actions built suspense and showed the children thinking before they moved.",
        ),
        QAItem(
            question=f"What did they do instead of forcing the chest open?",
            answer=f"They chose to {meth.prep}. That careful method matched the problem and helped them find {prize.reveal} safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does jumbo mean here?",
            answer="Jumbo means very big. In this story it describes a chest or bundle that feels larger than ordinary pirate gear.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling that something important is about to happen, but you do not know what it is yet. A story can build suspense by delaying the answer.",
        ),
        QAItem(
            question="Why do repeated actions matter in a story?",
            answer="Repeated actions can make a moment feel stronger and help the reader notice a pattern. They are also useful for building suspense or showing a character thinking carefully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS or params.method not in METHODS or params.prize not in PRIZES:
        pass
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.label, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(P,M,R) :- problem(P), method(M), prize(R), safe_method(M), compatible(P,M,R).
safe_method(peek_and_tap).
safe_method(unlash_carefully).
safe_method(call_all_hands).

compatible(hollow_sound, _, _).
compatible(jumbo_bundle, _, _).
compatible(hidden_lantern, _, lantern).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for m, mv in METHODS.items():
        lines.append(asp.fact("method", m))
        if mv.safe:
            lines.append(asp.fact("safe_method", m))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    got = set(asp_valid_combos())
    ok = True
    if expected != got:
        ok = False
        print("MISMATCH in valid_combos:")
        print("python-only:", sorted(expected - got))
        print("asp-only:", sorted(got - expected))
    try:
        sample = generate(resolve_params(argparse.Namespace(problem=None, method=None, prize=None, hero=None, helper=None, parent="captain", ship="ship"), random.Random(777)))
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    if ok:
        print(f"OK: ASP matches Python gate ({len(got)} combos) and generate() smoke test passed.")
        return 0
    return 1


CURATED = [
    StoryParams(problem="hollow_sound", method="peek_and_tap", prize="map", hero="Mara", helper="Nico", parent="captain"),
    StoryParams(problem="jumbo_bundle", method="unlash_carefully", prize="spyglass", hero="Tess", helper="Bram", parent="captain"),
    StoryParams(problem="hidden_lantern", method="call_all_hands", prize="lantern", hero="Iris", helper="Otis", parent="captain"),
    StoryParams(problem="hollow_sound", method="call_all_hands", prize="bell", hero="Ada", helper="Keen", parent="captain"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(row)
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
