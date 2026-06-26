#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pose_torture_lesson_learned_reconciliation_myth.py
===============================================================================================================

A mythic story world about a proud pose, a harsh ordeal, a lesson learned,
and a reconciliation.

The seed tale imagines a small myth:
- A young hero loves striking a grand pose on a hilltop.
- A rival spirit demands an exhausting, uncomfortable "torture" of patience:
  holding still, balancing a shining bowl, and enduring a long wind.
- The hero first resists, then learns the lesson that strength is not only
  standing tall; it is also listening.
- In the end, the hero and the rival reconcile, and the hilltop becomes a
  place of shared honor.

This script turns that premise into a small stateful simulation with meters and
memes, plus a reasonableness gate and an inline ASP twin.
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
# Core constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world state
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
    kind: str = "thing"           # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    hero: object | None = None
    prize: object | None = None
    rival: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "priestess", "woman"}
        male = {"boy", "father", "king", "priest", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the hilltop"
    mood: str = "windy"
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
class Trial:
    id: str
    verb: str
    gerund: str
    rush: str
    strain: str
    lesson: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str = "hands"
    plural: bool = False
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
class Bond:
    id: str
    label: str
    helper: str
    bridge: str
    aftermath: str
    cover: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hilltop": Setting(place="the hilltop", mood="windy", affords={"pose", "ordeal"}),
    "temple": Setting(place="the old temple", mood="quiet", affords={"pose", "ordeal"}),
    "riverbank": Setting(place="the riverbank", mood="bright", affords={"pose", "ordeal"}),
}

TRIALS = {
    "pose": Trial(
        id="pose",
        verb="strike a grand pose",
        gerund="striking a grand pose",
        rush="hold the pose",
        strain="kept still for too long",
        lesson="a proud pose can be lovely, but a hero must also listen",
        tags={"pose", "pride"},
    ),
    "torture": Trial(
        id="torture",
        verb="endure the long torture of stillness",
        gerund="enduring the long torture of stillness",
        rush="complain and move",
        strain="strained under the waiting",
        lesson="endurance grows when pride bows a little",
        tags={"torture", "waiting"},
    ),
}

PRIZES = {
    "crown": Prize(id="crown", label="crown", phrase="a bright bronze crown", region="head"),
    "bowl": Prize(id="bowl", label="bowl", phrase="a silver bowl of water", region="hands"),
    "torch": Prize(id="torch", label="torch", phrase="a torch with a steady flame", region="hands"),
}

BONDS = [
    Bond(
        id="truce",
        label="truce",
        helper="the elder's soft word",
        bridge="bowed to speak kindly",
        aftermath="they shared the hilltop",
        cover={"peace"},
    ),
    Bond(
        id="alliance",
        label="alliance",
        helper="the offering of the bowl",
        bridge="placed the bowl between them",
        aftermath="they watched the dawn together",
        cover={"water"},
    ),
]

HERO_NAMES = ["Ari", "Nela", "Maro", "Ivo", "Sera", "Tali", "Rhea", "Kian"]
RIVAL_NAMES = ["the wind-spirit", "the stone-guardian", "the river-sage", "the dawn-keeper"]
TRAITS = ["proud", "brave", "curious", "steady", "bold", "earnest"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    trial: str
    prize: str
    hero: str
    rival: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------
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


def give_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.owner = hero.id
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} as if the world had crowned {hero.pronoun('object')} already."
    )


def introduce(world: World, hero: Entity, rival: Entity, prize: Entity, trial: Trial) -> None:
    world.say(
        f"{hero.id} was a {next((t for t in hero.traits if t != 'little'), 'young')} {hero.type} who loved a noble {trial.id}."
    )
    world.say(
        f"Near {world.setting.place}, {rival.label} watched the day and asked for a harder test."
    )
    world.say(
        f"{hero.id} wanted to {trial.verb}, and {hero.pronoun('possessive')} heart beat fast for {prize.phrase}."
    )


def begin_trial(world: World, hero: Entity, trial: Trial) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    hero.meters["effort"] = hero.meters.get("effort", 0) + 1
    world.zone = {"head", "hands"}
    world.say(f"The air at {world.setting.place} grew sharp, and {hero.id} began to {trial.verb}.")


def pressure(world: World, hero: Entity, rival: Entity, prize: Entity, trial: Trial) -> None:
    hero.meters["strain"] = hero.meters.get("strain", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"{rival.label} set the hard rule: {hero.id} must {trial.rush} while carrying {prize.phrase}."
    )
    world.say(
        f"That felt like a kind of torture, because the wind would not let {hero.pronoun('object')} relax."
    )


def resist(world: World, hero: Entity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    world.say(f"{hero.id} frowned and tried to stand taller instead of listening.")


def learn_lesson(world: World, hero: Entity, rival: Entity, trial: Trial) -> None:
    hero.memes["humility"] = hero.memes.get("humility", 0) + 1
    hero.memes["lesson_learned"] = 1
    world.say(
        f"At last {hero.id} remembered {trial.lesson}."
    )
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} chin, breathed slowly, and let the lesson settle like rain on stone."
    )


def reconcile(world: World, hero: Entity, rival: Entity, bond: Bond, prize: Entity) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    hero.memes["defiance"] = 0
    hero.memes["conflict"] = 0
    world.say(
        f"Then {bond.helper} came between them, and {hero.id} {bond.bridge}."
    )
    world.say(
        f"{rival.label} softened, and the two of them made a {bond.label}."
    )
    world.say(
        f"In that gentle moment, {bond.aftermath}, and {hero.id}'s {prize.label} shone without fear."
    )


def resolve_story(world: World, hero: Entity, rival: Entity, prize: Entity, trial: Trial) -> Optional[Bond]:
    bond = _safe_lookup(BONDS, 0) if trial.id == "pose" else _safe_lookup(BONDS, 1)
    learn_lesson(world, hero, rival, trial)
    reconcile(world, hero, rival, bond, prize)
    return bond


def tell(setting: Setting, trial: Trial, prize_cfg: Prize, hero_name: str, rival_name: str,
         trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="hero",
        traits=["little", trait, "mythic"],
    ))
    rival = world.add(Entity(
        id=rival_name,
        kind="character",
        type="spirit",
        label=rival_name,
        traits=["ancient", "stern"],
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero, rival, prize, trial)
    world.para()
    give_prize(world, hero, prize)
    begin_trial(world, hero, trial)
    pressure(world, hero, rival, prize, trial)
    resist(world, hero)

    world.para()
    bond = resolve_story(world, hero, rival, prize, trial)

    world.facts.update(
        hero=hero,
        rival=rival,
        prize=prize,
        trial=trial,
        setting=setting,
        bond=bond,
        lesson_learned=bool(hero.memes.get("lesson_learned")),
        reconciled=bond is not None,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
trial_valid(T) :- trial(T).
prize_fit(T, P) :- trial(T), prize(P).
lesson_learned(T) :- trial(T), teaches(T, _).
reconciled(T, B) :- trial(T), bond(B), mends(B, T).
valid_story(Place, T, P) :- affords(Place, T), prize_fit(T, P), lesson_learned(T), reconciled(T, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("teaches", tid, t.lesson))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for b in BONDS:
        lines.append(asp.fact("bond", b.id))
        for c in sorted(b.cover):
            lines.append(asp.fact("mends", b.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for trial in setting.affords:
            for prize in PRIZES:
                combos.append((place, trial, prize))
    return combos


def explain_rejection() -> str:
    return "(No story: this myth needs a place that allows the trial.)"


# ---------------------------------------------------------------------------
# QA and narration
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about "{f["trial"].id}" and a lesson learned.',
        f"Tell a gentle myth where {f['hero'].id} faces {f['rival'].label} at {f['setting'].place} and then makes peace.",
        f'Write a small myth that uses the words "pose" and "torture" but ends in reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    rival: Entity = _safe_fact(world, f, "rival")
    prize: Entity = _safe_fact(world, f, "prize")
    trial: Trial = _safe_fact(world, f, "trial")
    bond: Optional[Bond] = _safe_fact(world, f, "bond")
    return [
        QAItem(
            question=f"Who was the myth mostly about?",
            answer=f"It was mostly about {hero.id}, who wanted to {trial.verb} while carrying {prize.phrase}.",
        ),
        QAItem(
            question=f"What hard thing did {hero.id} have to endure?",
            answer=f"{hero.id} had to endure the long torture of stillness and the sharp wind near {world.setting.place}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{trial.lesson.capitalize()}. {hero.id} learned that being strong also means listening and changing.",
        ),
    ] + (
        [
            QAItem(
                question=f"How did {hero.id} and {rival.label} make peace?",
                answer=f"They reconciled through the {bond.label}, and the feud softened into shared honor.",
            )
        ] if bond else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story about brave people, powerful beings, and big lessons.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting and make peace again.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important that changes how you act next.",
        ),
        QAItem(
            question="What is a pose?",
            answer="A pose is a still way of standing or sitting, often to look proud or important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="hilltop", trial="pose", prize="crown", hero="Ari", rival="the wind-spirit", trait="proud"),
    StoryParams(place="temple", trial="torture", prize="bowl", hero="Nela", rival="the stone-guardian", trait="earnest"),
    StoryParams(place="riverbank", trial="pose", prize="torch", hero="Sera", rival="the river-sage", trait="curious"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "trial", None) is None or c[1] == getattr(args, "trial", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trial, prize = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    rival = getattr(args, "rival", None) or rng.choice(RIVAL_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, trial=trial, prize=prize, hero=hero, rival=rival, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TRIALS, params.trial), _safe_lookup(PRIZES, params.prize),
                 params.hero, params.rival, params.trait)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: pose, torture, lesson learned, reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--rival")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible stories:")
        for t in asp.atoms(model, "valid_story"):
            print("  ", t)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.trial} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
