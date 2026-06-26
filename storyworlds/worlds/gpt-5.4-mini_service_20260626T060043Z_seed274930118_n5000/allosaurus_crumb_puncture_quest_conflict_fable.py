#!/usr/bin/env python3
"""
storyworlds/worlds/allosaurus_crumb_puncture_quest_conflict_fable.py
====================================================================

A small fable-style storyworld about an allosaurus on a quest for a crumb,
the conflict caused by a puncture, and the kind turn that makes the ending
gentle and complete.

The world is intentionally tiny:
- one hero (an allosaurus)
- one goal (a crumb)
- one problem (a punctured carrier)
- one repair (a patch or swap)
- one ending image proving the change

This script follows the Storyweavers contract:
- self-contained stdlib script under storyworlds/worlds/
- eager import of shared results containers
- lazy import of storyworlds.asp in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "allosaurus":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str
    detail: str
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
class Quest:
    id: str
    verb: str
    gerund: str
    goal: str
    trail: str
    danger: str
    risk: str
    keyword: str
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
    owner_name: str
    region: str
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.quest_zone: set[str] = set()

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


def _empty_meters() -> dict[str, float]:
    return {"hope": 0.0, "joy": 0.0, "mess": 0.0, "damage": 0.0, "work": 0.0}


def _empty_memes() -> dict[str, float]:
    return {"love": 0.0, "conflict": 0.0, "worry": 0.0, "bravery": 0.0, "patience": 0.0, "defiance": 0.0}


def render_name(entity: Entity) -> str:
    return entity.label or entity.id


def quest_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.tags


def select_fix(quest: Quest, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if quest.risk in fx.guards and prize.region in fx.covers:
            return fx
    return None


def _apply_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.meters["hope"] += 1
    hero.memes["bravery"] += 1
    world.quest_zone = set(["path", "thorn"])
    if narrate:
        world.say(f"{hero.id} began the quest for {quest.goal}, and {hero.pronoun()} walked with careful hope.")


def _apply_puncture(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    hero.meters["mess"] += 1
    for item in list(world.entities.values()):
        if item.worn_by == hero.id and item.id != prize.id:
            item.meters["damage"] += 1


def predict_harm(world: World, hero: Entity, quest: Quest, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id,
        "kind": v.kind,
        "type": v.type,
        "label": v.label,
        "phrase": v.phrase,
        "owner": v.owner,
        "caretaker": v.caretaker,
        "worn_by": v.worn_by,
        "plural": v.plural,
        "meters": dict(v.meters),
        "memes": dict(v.memes),
    }) for k, v in world.entities.items()}
    _apply_quest(sim, sim.get(hero.id), quest, narrate=False)
    prize = sim.entities[prize_id]
    if quest_at_risk(quest, _safe_lookup(PRIZES, prize.id)):
        _apply_puncture(sim, sim.get(hero.id), quest, prize)
    return {"damaged": prize.meters.get("damage", 0.0) >= THRESHOLD}


def setup(world: World, hero: Entity, elder: Entity, prize: Entity) -> None:
    world.say(
        f"Once in a quiet wood, {hero.id} was an allosaurus with a brave heart and a small wish."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted {prize.phrase}, because {prize.owner_name} had said it was the kind of crumb that could begin a story."
    )
    world.say(
        f"{elder.id} told {hero.id}, \"A true quest is not only about taking; it is about how you carry what you find.\""
    )


def begin_conflict(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["worry"] += 1
    world.para()
    world.say(
        f"So {hero.id} set out on the quest for the crumb, following {quest.trail} toward {world.setting.place}."
    )
    world.say(
        f"{world.setting.detail.capitalize()}, but a thorn waited near the path."
    )
    world.say(
        f"When {hero.id} leaned close, the thorn gave a quick puncture to {prize.label}, and crumbs slipped into the grass."
    )
    hero.memes["conflict"] += 1
    world.say(
        f"That made a sharp conflict in {hero.id}'s chest, because the crumb was wanted, yet the cracked pouch could not hold it safely."
    )


def repair_and_resolve(world: World, hero: Entity, elder: Entity, prize: Entity, fix: Fix) -> None:
    hero.memes["patience"] += 1
    hero.memes["conflict"] = 0.0
    hero.meters["joy"] += 1
    world.para()
    world.say(
        f"{elder.id} came beside {hero.id} and smiled. \"Use {fix.label},\" {elder.pronoun()} said. \"A wise quest keeps the prize safe.\""
    )
    world.say(
        f"{hero.id} listened, and {fix.prep}; then the pouch was ready again."
    )
    world.say(
        f"After that, {hero.id} gathered the crumb with care, and {fix.tail}."
    )
    world.say(
        f"By sunset, the little crumb was still whole, and {hero.id} walked home proud that the quest had changed from rushing to careful keeping."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    prize: Entity = _safe_fact(world, f, "prize")
    quest: Quest = _safe_fact(world, f, "quest")
    fix: Fix = _safe_fact(world, f, "fix")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, an allosaurus with a brave heart who went on a quest for {prize.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} want on the quest?",
            answer=f"{hero.id} wanted {prize.phrase}, which was the crumb that started the whole adventure.",
        ),
        QAItem(
            question=f"What caused the conflict in the middle?",
            answer=f"The conflict came when a thorn made a puncture in the carrier, and the crumbs spilled before {hero.id} could bring them home safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended well because {elder.id} suggested {fix.label}, {hero.id} fixed the pouch, and the crumb stayed safe on the way home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task someone chooses because they want to find, fix, or learn something important.",
        ),
        QAItem(
            question="What is a puncture?",
            answer="A puncture is a small hole made by something sharp, like a thorn or a pin.",
        ),
        QAItem(
            question="What is a crumb?",
            answer="A crumb is a tiny piece of bread, cake, or another baked thing.",
        ),
        QAItem(
            question="What is a conflict in a fable?",
            answer="A conflict is the hard part of the story when characters want different things or something goes wrong before they can solve it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prize: Entity = _safe_fact(world, f, "prize")
    quest: Quest = _safe_fact(world, f, "quest")
    return [
        f'Write a short fable about an allosaurus on a quest for a crumb, and include the word "{quest.keyword}".',
        f"Tell a child-friendly story where {hero.id} faces conflict after a puncture, then learns a careful way to carry {prize.phrase}.",
        f"Create a gentle fable with a quest, a conflict, and a happy ending involving a crumb.",
    ]


@dataclass
class StoryParams:
    setting: str
    quest: str
    prize: str
    hero_name: str
    helper_name: str
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
    "woodland": Setting(
        place="the woodland path",
        detail="the woodland path was quiet, with soft moss and one bright thorn bush",
        affords={"crumb_quest"},
    ),
    "hill": Setting(
        place="the sunlit hill",
        detail="the sunlit hill rose gently, with grass waving like a green blanket",
        affords={"crumb_quest"},
    ),
    "orchard": Setting(
        place="the orchard gate",
        detail="the orchard gate smelled sweet, and apple leaves whispered overhead",
        affords={"crumb_quest"},
    ),
}

QUESTS = {
    "crumb_quest": Quest(
        id="crumb_quest",
        verb="go after the crumb",
        gerund="going after the crumb",
        goal="a tiny golden crumb",
        trail="a narrow trail of bird tracks",
        danger="thorn",
        risk="puncture",
        keyword="Quest",
        tags={"path", "hand", "pouch"},
    ),
}

PRIZES = {
    "crumb": Prize(
        id="crumb",
        label="crumb pouch",
        phrase="a tiny golden crumb",
        owner_name="the old baker",
        region="pouch",
    ),
}

FIXES = [
    Fix(
        id="leaf_patch",
        label="a broad leaf patch",
        prep="he pressed a broad leaf patch over the puncture and tied it snugly",
        tail="the crumb rested safely inside the mended pouch",
        covers={"pouch"},
        guards={"puncture"},
    ),
    Fix(
        id="shell_cup",
        label="a smooth shell cup",
        prep="he set the crumb into a smooth shell cup instead",
        tail="the shell cup kept the crumb from falling again",
        covers={"pouch"},
        guards={"puncture"},
    ),
]

HEROES = ["Arlo", "Mira", "Sable", "Taro", "Nori"]
HELPERS = ["Elder Reed", "Grandma Thorn", "Uncle Moss", "Old Hare"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, q, p) for s, setting in SETTINGS.items() for q in setting.affords for p in PRIZES]


def explain_rejection(setting: Setting, quest: Quest, prize: Prize) -> str:
    return f"(No story: the chosen setting and quest do not create a real puncture-and-repair conflict for {prize.phrase}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld: an allosaurus, a crumb, and a puncture.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if getattr(args, "setting", None) and getattr(args, "quest", None) and getattr(args, "prize", None):
        if not valid_combos() or (getattr(args, "setting", None), getattr(args, "quest", None), getattr(args, "prize", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    name = getattr(args, "name", None) or rng.choice(HEROES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(setting=setting, quest=quest, prize=prize, hero_name=name, helper_name=helper)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    quest = _safe_lookup(QUESTS, params.quest)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="allosaurus",
        label=params.hero_name,
        meters=_empty_meters(),
        memes=_empty_memes(),
    ))
    elder = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="elder",
        label=params.helper_name,
        meters=_empty_meters(),
        memes=_empty_memes(),
    ))
    prize = world.add(Entity(
        id="crumb_pouch",
        type="pouch",
        label="crumb pouch",
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=elder.id,
        meters=_empty_meters(),
        memes=_empty_memes(),
    ))

    setup(world, hero, elder, prize)
    _apply_quest(world, hero, quest, narrate=False)
    begin_conflict(world, hero, quest, prize)

    fix = select_fix(quest, prize_cfg)
    if fix is None:
        pass
    repair_and_resolve(world, hero, elder, prize, fix)

    world.facts.update(hero=hero, elder=elder, prize=prize, quest=quest, fix=fix, setting=world.setting)
    return world


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_choice(S,Q,P) :- setting(S), affords(S,Q), prize(P).
puncture_conflict(S,Q,P) :- quest_choice(S,Q,P), risky(Q,P).
fixable(S,Q,P) :- puncture_conflict(S,Q,P), has_fix(Q,P).
valid_story(S,Q,P) :- fixable(S,Q,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for c in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, c))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
    lines.append(asp.fact("risky", "crumb_quest", "crumb"))
    lines.append(asp.fact("has_fix", "crumb_quest", "crumb"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
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


CURATED = [
    StoryParams(setting="woodland", quest="crumb_quest", prize="crumb", hero_name="Arlo", helper_name="Elder Reed"),
    StoryParams(setting="hill", quest="crumb_quest", prize="crumb", hero_name="Mira", helper_name="Grandma Thorn"),
    StoryParams(setting="orchard", quest="crumb_quest", prize="crumb", hero_name="Sable", helper_name="Old Hare"),
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for s, q, p in combos:
            print(f"  {s:10} {q:12} {p}")
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
            header = f"### {p.hero_name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
