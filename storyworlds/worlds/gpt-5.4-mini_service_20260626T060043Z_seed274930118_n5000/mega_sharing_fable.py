#!/usr/bin/env python3
"""
storyworlds/worlds/mega_sharing_fable.py
========================================

A small fable world about a mega treat and the choice to share it.

Seed-inspired premise:
- A character finds a mega feast-sized treat.
- Another character wants some too.
- The first character must choose between hoarding and sharing.
- In the end, sharing makes the feast sweeter and the friendship stronger.

The world is intentionally compact and classical: a little premise, a small
tension, a turn, and a moral ending image.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    giver: object | None = None
    receiver: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "dog", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"hare", "rabbit", "mouse", "girl"}:
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
class Treasure:
    label: str
    phrase: str
    type: str
    size: str
    shares_with: int
    keeps: str
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
class StoryParams:
    setting: str
    treasure: str
    giver_type: str
    giver_name: str
    giver_trait: str
    receiver_type: str
    receiver_name: str
    receiver_trait: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "orchard": Setting(
        place="the orchard",
        detail="The orchard was warm, with grass under the trees and sun on the fruit.",
        affords={"share"},
    ),
    "meadow": Setting(
        place="the meadow",
        detail="The meadow was wide, with clover and a soft breeze moving through it.",
        affords={"share"},
    ),
    "riverbank": Setting(
        place="the riverbank",
        detail="The riverbank was bright, with reeds swaying and water singing nearby.",
        affords={"share"},
    ),
}

TREASURES = {
    "mega_berry_pie": Treasure(
        label="mega berry pie",
        phrase="a mega berry pie with a shiny crust",
        type="pie",
        size="mega",
        shares_with=4,
        keeps="big and bright",
    ),
    "mega_apple_cake": Treasure(
        label="mega apple cake",
        phrase="a mega apple cake with cinnamon on top",
        type="cake",
        size="mega",
        shares_with=4,
        keeps="soft and sweet",
    ),
    "mega_honey_loaf": Treasure(
        label="mega honey loaf",
        phrase="a mega honey loaf wrapped in a cloth",
        type="loaf",
        size="mega",
        shares_with=3,
        keeps="golden and warm",
    ),
}

TRAITS = ["kind", "proud", "busy", "gentle", "merry", "curious"]
ANIMALS = {
    "fox": {"names": ["Fenn", "Ruby", "Tao"], "pronoun": "he"},
    "hare": {"names": ["Pip", "Luna", "Mira"], "pronoun": "she"},
    "mouse": {"names": ["Nib", "Suri", "Wren"], "pronoun": "they"},
    "raccoon": {"names": ["Puck", "Nova", "Bram"], "pronoun": "he"},
}

CURATED = [
    StoryParams("orchard", "mega_berry_pie", "fox", "Fenn", "proud", "hare", "Luna", "kind"),
    StoryParams("meadow", "mega_apple_cake", "mouse", "Wren", "curious", "fox", "Tao", "merry"),
    StoryParams("riverbank", "mega_honey_loaf", "raccoon", "Puck", "busy", "hare", "Mira", "gentle"),
]


@dataclass
class SharePlan:
    title: str
    share_count: int
    turns: list[str]
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


ASP_RULES = r"""
% A treasure can be shared when it is mega-sized and the setting affords sharing.
shareable(T) :- treasure(T), mega(T), edible(T).

% A good ending requires at least one receiver and a sharing act.
good_story(S, T) :- setting(S), shareable(T), share(S, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("edible", tid))
        lines.append(asp.fact("mega", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_shareable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shareable/1."))
    return sorted(set(asp.atoms(model, "shareable")))


def asp_verify() -> int:
    py = {tid for tid, t in TREASURES.items() if t.size == "mega"}
    cl = {t[0] for t in asp_shareable()}
    if py == cl:
        print(f"OK: ASP matches Python shareable set ({len(py)} treasures).")
        return 0
    print("MISMATCH between ASP and Python shareable sets:")
    print("  only in ASP:", sorted(cl - py))
    print("  only in Python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about a mega treasure and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--giver-type", choices=sorted(ANIMALS))
    ap.add_argument("--receiver-type", choices=sorted(ANIMALS))
    ap.add_argument("--giver-name")
    ap.add_argument("--receiver-name")
    ap.add_argument("--giver-trait", choices=TRAITS)
    ap.add_argument("--receiver-trait", choices=TRAITS)
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


def reasonable(setting: str, treasure: str) -> bool:
    return "share" in _safe_lookup(SETTINGS, setting).affords and _safe_lookup(TREASURES, treasure).size == "mega"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "treasure", None) and not reasonable(getattr(args, "setting", None), getattr(args, "treasure", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    settings = [getattr(args, "setting", None)] if getattr(args, "setting", None) else list(SETTINGS)
    treasures = [getattr(args, "treasure", None)] if getattr(args, "treasure", None) else list(TREASURES)
    combos = [(s, t) for s in settings for t in treasures if reasonable(s, t)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, treasure = rng.choice(list(combos))

    giver_type = getattr(args, "giver_type", None) or rng.choice(sorted(ANIMALS))
    receiver_type = getattr(args, "receiver_type", None) or rng.choice([t for t in sorted(ANIMALS) if t != giver_type])

    giver_name = getattr(args, "giver_name", None) or rng.choice(_safe_lookup(ANIMALS, giver_type)["names"])
    receiver_name = getattr(args, "receiver_name", None) or rng.choice(_safe_lookup(ANIMALS, receiver_type)["names"])
    giver_trait = getattr(args, "giver_trait", None) or rng.choice(TRAITS)
    receiver_trait = getattr(args, "receiver_trait", None) or rng.choice([t for t in TRAITS if t != giver_trait])

    return StoryParams(
        setting=setting,
        treasure=treasure,
        giver_type=giver_type,
        giver_name=giver_name,
        giver_trait=giver_trait,
        receiver_type=receiver_type,
        receiver_name=receiver_name,
        receiver_trait=receiver_trait,
    )


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    giver = world.add(Entity(
        id="giver",
        kind="character",
        type=params.giver_type,
        label=params.giver_name,
    ))
    receiver = world.add(Entity(
        id="receiver",
        kind="character",
        type=params.receiver_type,
        label=params.receiver_name,
    ))
    treasure = world.add(Entity(
        id="treasure",
        type=_safe_lookup(TREASURES, params.treasure).type,
        label=_safe_lookup(TREASURES, params.treasure).label,
        phrase=_safe_lookup(TREASURES, params.treasure).phrase,
        plural=_safe_lookup(TREASURES, params.treasure).plural,
        owner=giver.id,
    ))
    world.facts.update(giver=giver, receiver=receiver, treasure=treasure, params=params)
    return world


def predicted_contention(world: World) -> bool:
    return world.get("treasure").memes.get("greed", 0.0) >= THRESHOLD and world.get("receiver").memes.get("want", 0.0) >= THRESHOLD


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    giver = world.get("giver")
    receiver = world.get("receiver")
    treasure = world.get("treasure")
    tcfg = _safe_lookup(TREASURES, params.treasure)

    giver.memes["pride"] = 1
    treasure.meters["fullness"] = 1

    world.say(
        f"In {world.setting.place}, {giver.label} was a {params.giver_trait} {giver.type} who found {treasure.phrase}."
    )
    world.say(
        f"It was a {tcfg.keeps} prize, big enough to share with more than one hungry friend."
    )

    world.para()
    receiver.memes["want"] += 1
    world.say(
        f"{receiver.label} came to the clearing and looked at the meal with bright eyes."
    )
    world.say(
        f'"May I have some?" {receiver.label} asked, because the smell of {treasure.label} was hard to ignore.'
    )

    world.para()
    giver.memes["greed"] += 1
    world.say(
        f"At first, {giver.label} hugged the whole {treasure.label} close and thought about keeping it all."
    )
    world.say(
        f"But the fable's heart is small and clear: a meal that big is meant for company, not for lonely paws."
    )

    if giver.memes["greed"] >= THRESHOLD and receiver.memes["want"] >= THRESHOLD:
        world.say(
            f"Then {giver.label} looked at {receiver.label}'s hopeful face and felt a warmer idea grow."
        )
        giver.memes["kindness"] += 1
        giver.memes["greed"] = 0
        receiver.memes["gratitude"] += 1
        treasure.meters["shared_slices"] = float(_safe_lookup(TREASURES, params.treasure).shares_with)
        world.say(
            f'"Yes," said {giver.label}. "We can share the mega feast."'
        )
        world.say(
            f"So {giver.label} cut {treasure.it()} into several pieces, and the two friends ate together under the open sky."
        )

    world.para()
    giver.memes["joy"] += 1
    receiver.memes["joy"] += 1
    world.say(
        f"In the end, the {params.giver_trait} one learned that a shared crumb can feel larger than a guarded loaf."
    )
    world.say(
        f"{giver.label} and {receiver.label} finished the last bite with full bellies and even fuller hearts."
    )

    world.facts.update(shared=True, share_count=_safe_lookup(TREASURES, params.treasure).shares_with)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    treasure = _safe_fact(world, world.facts, "treasure")
    return [
        f"Write a short fable about {p.giver_name} finding {treasure.phrase} and learning to share.",
        f"Tell a child-friendly story in which a {p.giver_trait} {p.giver_type} chooses sharing over keeping a mega treat.",
        f"Write a moral tale set in {world.setting.place} where two animals divide {treasure.label} kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    treasure = _safe_fact(world, world.facts, "treasure")
    giver = _safe_fact(world, world.facts, "giver")
    receiver = _safe_fact(world, world.facts, "receiver")
    return [
        QAItem(
            question=f"What did {p.giver_name} find in {world.setting.place}?",
            answer=f"{p.giver_name} found {treasure.phrase} in {world.setting.place}. It was a mega treat, big enough to share.",
        ),
        QAItem(
            question=f"What did {p.receiver_name} ask when the meal looked so good?",
            answer=f"{p.receiver_name} asked if some could be shared, because {treasure.label} smelled too tasty to keep alone.",
        ),
        QAItem(
            question=f"How did {p.giver_name} change by the end of the story?",
            answer=f"At first {p.giver_name} wanted to keep the treat, but in the end {giver.label} chose kindness and shared it with {receiver.label}.",
        ),
        QAItem(
            question=f"What happened after the sharing choice?",
            answer=f"The friends ate together, and the story ended with both of them happy, full, and glad they had shared.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person have some of what you have, so both of you can enjoy it.",
        ),
        QAItem(
            question="Why is a mega meal easier to share?",
            answer="A mega meal is large enough to divide into parts, so more than one hungry creature can eat.",
        ),
        QAItem(
            question="Why do fables often end with a lesson?",
            answer="Fables often end with a lesson so readers can remember a simple truth about kindness, honesty, or wise choices.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {e.label:12} {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(setting: str, treasure: str) -> str:
    return f"(No story: {setting} and {treasure} do not support the mega-sharing premise.)"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shareable/1."))
    return sorted(set(asp.atoms(model, "shareable")))


def asp_verify_world() -> int:
    py = {tid for tid, t in TREASURES.items() if t.size == "mega"}
    cl = {x[0] for x in asp_valid()}
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} treasures).")
        return 0
    print("MISMATCH:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show shareable/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_world())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} shareable treasures:\n")
        for (tid,) in vals:
            print(f"  {tid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.giver_name} and {p.receiver_name} with {p.treasure} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
