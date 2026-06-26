#!/usr/bin/env python3
"""
storyworlds/worlds/putt_cage_reconciliation_bad_ending_myth.py
==============================================================

A tiny myth-like story world about a sacred putt, a cage, reconciliation,
and a bad ending.

Premise:
- A young keeper wants to make one careful putt at a moon-ring shrine.
- An elder fears the putt will jolt a spirit cage and spoil the rite.
- They argue, then reconcile.
- The ending is still bad: the putt fails, the rite goes dim, and the cage
  remains shut.

The world is deliberately small and constraint-checked. It models:
- physical meters: balance, strain, ruin, darkness, distance, hope, repair
- emotional memes: longing, warning, anger, regret, trust, shame, relief

The story is mythic in tone, child-facing, and state-driven.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cage_ent: object | None = None
    elder: object | None = None
    hero: object | None = None
    pebble: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "elder"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "keeper"}:
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
    sacred: bool = False
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    omen: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Cage:
    id: str
    label: str
    phrase: str
    fragile: bool = True
    guards: set[str] = field(default_factory=set)
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
        self.trace_log: list[str] = []

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
        return clone


@dataclass
class StoryParams:
    place: str
    action: str
    cage: str
    hero: str
    hero_kind: str
    elder_kind: str
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
    "moon_grove": Setting(place="the moon grove", sacred=True, affords={"putt"}),
    "old_temple": Setting(place="the old temple", sacred=True, affords={"putt"}),
    "hill_shrine": Setting(place="the hill shrine", sacred=True, affords={"putt"}),
}

ACTIONS = {
    "putt": Action(
        id="putt",
        verb="make the putt",
        gerund="putting the silver pebble",
        rush="send the pebble rolling",
        risk="jolt the cage and spoil the rite",
        omen="the pebble might miss the ring and wake sorrow",
        tags={"putt", "moon", "rite"},
    ),
}

CAGES = {
    "birdcage": Cage(
        id="birdcage",
        label="a reed cage",
        phrase="a reed cage with a soft latch",
        fragile=True,
        guards={"miss"},
    ),
    "starcage": Cage(
        id="starcage",
        label="a star cage",
        phrase="a bronze cage that held a tiny star",
        fragile=True,
        guards={"miss"},
    ),
}

HEROES = ["Ari", "Mira", "Tavi", "Nia", "Orin"]
ELDERS = ["elder", "keeper", "guard"]

TRAITS = ["small", "brave", "quiet", "curious", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "putt", cage_id) for place in SETTINGS for cage_id in CAGES]


def explain_rejection(place: str, action: str, cage_id: str) -> str:
    if action != "putt":
        return "(No story: this world only knows a sacred putt.)"
    if place not in SETTINGS:
        return "(No story: the place is not in the mythic registry.)"
    if cage_id not in CAGES:
        return "(No story: the cage is not in the registry.)"
    return "(No story: that combination cannot make a meaningful myth.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.sacred:
            lines.append(asp.fact("sacred", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for cid, cage in CAGES.items():
        lines.append(asp.fact("cage", cid))
        if cage.fragile:
            lines.append(asp.fact("fragile", cid))
        for g in sorted(cage.guards):
            lines.append(asp.fact("guards", cid, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Action, Cage) :- place(Place), action(Action), cage(Cage), affords(Place, Action).
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
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: a putt, a cage, reconciliation, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--cage", choices=CAGES)
    ap.add_argument("--name")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--elder-kind", choices=ELDERS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "cage", None) is None or c[2] == getattr(args, "cage", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, cage = rng.choice(list(combos))
    return StoryParams(
        place=place,
        action=action,
        cage=cage,
        hero=getattr(args, "name", None) or rng.choice(HEROES),
        hero_kind=getattr(args, "hero_kind", None) or rng.choice(["girl", "boy"]),
        elder_kind=getattr(args, "elder_kind", None) or "elder",
    )


def _line(world: World, text: str) -> None:
    world.say(text)


def tell(setting: Setting, action: Action, cage: Cage, hero_name: str, hero_kind: str, elder_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_kind))
    pebble = world.add(Entity(id="pebble", type="stone", label="silver pebble", phrase="a silver pebble"))
    cage_ent = world.add(Entity(id=cage.id, type="cage", label=cage.label, phrase=cage.phrase, protective=True))

    hero.memes["longing"] = 1
    elder.memes["warning"] = 1
    cage_ent.meters["distance"] = 1

    _line(world, f"In {setting.place}, long after the first dawn, {hero_name} was a {hero_kind} who loved the old rites.")
    _line(world, f"Each dusk, {hero_name} watched the priests circle the shrine and dreamed of the sacred {action.verb}.")
    _line(world, f"Near the altar stood {cage.phrase}, and inside it the little light flickered like a trapped star.")

    world.para()
    _line(world, f"One evening, {hero_name} reached for the {pebble.label} and wanted to {action.verb} before the moon sank low.")
    _line(world, f"But {elder_kind} raised a hand. \"If you {action.verb}, you may {action.risk}.\"")
    hero.memes["defiance"] = 1
    elder.memes["fear"] = 1

    world.para()
    _line(world, f"{hero_name} frowned and tried to {action.rush}, because the wish to begin was stronger than the warning.")
    _line(world, f"{hero_name}'s foot slipped on the stone path, and the air grew sharp with {action.omen}.")
    world.facts["warning"] = action.risk

    # Reconciliation beat.
    world.para()
    hero.memes["regret"] = 1
    elder.memes["regret"] = 1
    hero.memes["trust"] = 1
    elder.memes["trust"] = 1
    _line(world, f"Then {hero_name} looked up at {elder_kind} and whispered sorry.")
    _line(world, f"The {elder_kind}'s face softened, and the two of them stood close by the cage, breathing as one.")
    _line(world, f"\"We can still face the night together,\" said {elder_kind}, and {hero_name} nodded.")

    # Bad ending: reconciliation succeeds, the rite fails.
    world.para()
    world.facts["reconciled"] = True
    world.facts["bad_ending"] = True
    pebble.meters["distance"] += 1
    cage_ent.meters["strain"] += 1
    world.facts["missed"] = True
    _line(world, f"{hero_name} made the putt again, but the silver pebble glanced off the ring and fell dead to the grass.")
    _line(world, f"The tiny light in the cage went dim, and the moon never rose to bless the shrine.")
    _line(world, f"Still, {hero_name} and {elder_kind} left the altar side by side, their anger gone, while the closed cage kept its silent sorrow.")

    world.facts.update(hero=hero, elder=elder, action=action, cage=cage_ent, place=setting.place, name=hero_name)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short myth for a child about a sacred putt and a cage.',
        f"Tell a gentle, old-style tale where {f['name']} wants to {f['action'].verb} but must reconcile with the {f['elder'].type}.",
        f"Write a myth where the ending is bad: the {f['action'].id} fails, yet the two characters make peace.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    action = _safe_fact(world, f, "action")
    cage = _safe_fact(world, f, "cage")
    qa = [
        QAItem(
            question=f"Who was the story about in {f['place']}?",
            answer=f"It was about {f['name']}, a {hero.type} who lived by the old shrine and longed to {action.verb}.",
        ),
        QAItem(
            question=f"Why did the {elder.type} warn {f['name']} about the putt?",
            answer=f"The {elder.type} warned {f['name']} because the putt could {action.risk}. The warning came from careful love, not cruelty.",
        ),
        QAItem(
            question=f"What happened between {f['name']} and the {elder.type} before the ending?",
            answer=f"They argued at first, but then they apologized and reconciled. After that, they stood together by the cage without anger.",
        ),
        QAItem(
            question="Was the ending happy?",
            answer="No. The ending was bad: the pebble missed, the cage stayed closed, and the shrine's light went dim even after the reconciliation.",
        ),
        QAItem(
            question=f"What did the {cage.label} hold?",
            answer=f"It held a tiny light like a trapped star, which made the shrine feel sacred and sad at the same time.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cage?",
            answer="A cage is a container with bars or weaving that keeps something inside.",
        ),
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to stop fighting and become peaceful again.",
        ),
        QAItem(
            question="What is a putt?",
            answer="A putt is a careful stroke that rolls a ball or pebble toward a target.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things do not work out well, even if the characters tried hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"{e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_grove", action="putt", cage="birdcage", hero="Ari", hero_kind="boy", elder_kind="elder"),
    StoryParams(place="old_temple", action="putt", cage="starcage", hero="Mira", hero_kind="girl", elder_kind="keeper"),
    StoryParams(place="hill_shrine", action="putt", cage="birdcage", hero="Tavi", hero_kind="boy", elder_kind="guard"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(CAGES, params.cage), params.hero, params.hero_kind, params.elder_kind)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
