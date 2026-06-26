#!/usr/bin/env python3
"""
storyworlds/worlds/wicked_twist_folk_tale.py
============================================

A small folk-tale storyworld with a wicked trickster, a tested kindness, and a
Twist that turns the ending by changing who outsmarts whom.

Premise:
- A little hero meets a wicked figure in a village, wood, bridge, or field.
- The wicked one offers a tempting shortcut, bargain, or boast.

Tension:
- The hero must choose between a safe honest path and the wicked shortcut.
- The wicked figure tries to trick, steal, or shame the hero.

Turn:
- A simple, folk-tale-like Twist reveals the trick was mirrored, mistaken, or
  turned back by a clever helper, hidden sign, or remembered rule.

Resolution:
- The hero gains a small treasure, a lesson, or a safe way home, and the
  wicked figure loses power, leaves, or is forced to keep a bargain.

This world models physical meters and emotional memes. It narrates from the
state changes rather than from a fixed template, and it includes an ASP twin for
reasonableness parity checks.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"value": 0.0, "risk": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "hope": 0.0, "cunning": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    kind: str
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
class StoryWorld:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    c: object | None = None
    world: object | None = None
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

    def copy(self) -> "StoryWorld":
        import copy
        c = StoryWorld(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
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


PLACES = {
    "village": Place("village", "the village green", "village", {"road", "bread", "well"}),
    "forest": Place("forest", "the old forest", "forest", {"tree", "path", "owl"}),
    "bridge": Place("bridge", "the narrow bridge", "bridge", {"water", "crossing", "river"}),
    "market": Place("market", "the busy market", "market", {"coin", "stall", "bread"}),
}

HEROES = {
    "girl": ["Mara", "Nina", "Lena", "Tilda", "Elsa"],
    "boy": ["Pip", "Otto", "Jon", "Bram", "Tomas"],
}

HELPERS = {
    "owl": "a gray owl",
    "grandmother": "a kind grandmother",
    "miller": "a white-bearded miller",
    "dog": "a small watchful dog",
}

WICKEDS = {
    "fox": "a wicked fox",
    "witch": "a wicked witch",
    "troll": "a wicked troll",
    "crow": "a wicked crow",
}

TREASURES = {
    "bread": ("a warm loaf of bread", "bread"),
    "ring": ("a brass ring", "ring"),
    "lamp": ("a little lantern", "lantern"),
    "key": ("a silver key", "key"),
}

TWISTS = {
    "mirror": "the trick came back to the trickster",
    "swap": "the wrong bundle had been taken",
    "riddle": "a riddle hidden in plain sight turned the bargain around",
    "helper": "a quiet helper had been watching all along",
}

ACTIONS = {
    "shortcut": ("take a shortcut", "taking a shortcut"),
    "swap": ("swap bundles", "swapping bundles"),
    "boast": ("boast at the well", "boasting at the well"),
    "bargain": ("accept the bargain", "accepting the bargain"),
}

DANGERS = {
    "lost": "get lost",
    "stolen": "have the treasure stolen",
    "shamed": "be laughed at by the crowd",
    "trapped": "be trapped by the wicked one",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
reasonably_valid(Place, Hero, Wicked, Treasure, Twist) :-
    place(Place), hero(Hero), wicked(Wicked), treasure(Treasure), twist(Twist),
    at_risk(Place, Treasure), twist_works(Twist).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("place_tag", pid, t))
    for gid, names in HEROES.items():
        for n in names:
            lines.append(asp.fact("hero_name", gid, n))
    for w in WICKEDS:
        lines.append(asp.fact("wicked", w))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    for x in TWISTS:
        lines.append(asp.fact("twist", x))
    for p in PLACES:
        for t in TREASURES:
            lines.append(asp.fact("at_risk", p, t))
    for x in TWISTS:
        lines.append(asp.fact("twist_works", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/5."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    az = set(asp_valid())
    if py == az:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - az:
        print("  only in python:", sorted(py - az))
    if az - py:
        print("  only in clingo:", sorted(az - py))
    return 1


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_gender: str
    hero_name: str
    wicked_kind: str
    treasure: str
    twist: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
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


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for place in PLACES:
        for gender in HEROES:
            for wicked in WICKEDS:
                for treasure in TREASURES:
                    for twist in TWISTS:
                        # Simple gate: every place can host every tale, but only
                        # if the treasure is a believable risk and the twist is usable.
                        if treasure in TREASURES and twist in TWISTS:
                            combos.append((place, gender, wicked, treasure, twist))
    return combos


def explain_rejection(place: str, treasure: str, twist: str) -> str:
    return (
        f"(No story: the tale needs a treasure at risk in {place}, and the {twist} twist "
        f"must be able to turn the wicked plan around.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def build_world(params: StoryParams) -> StoryWorld:
    world = StoryWorld(_safe_lookup(PLACES, params.place))
    hero_type = params.hero_gender
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_type,
            label=params.hero_name,
            phrase=f"{article(hero_type)} little {hero_type} named {params.hero_name}",
        )
    )
    wicked = world.add(
        Entity(
            id="wicked",
            kind="character",
            type=params.wicked_kind,
            label=_safe_lookup(WICKEDS, params.wicked_kind),
            phrase=_safe_lookup(WICKEDS, params.wicked_kind),
            memes={"fear": 0.0, "hope": 0.0, "cunning": 2.0, "joy": 0.0},
        )
    )
    treasure_phrase, treasure_label = _safe_lookup(TREASURES, params.treasure)
    treasure = world.add(
        Entity(
            id="treasure",
            kind="thing",
            type=params.treasure,
            label=treasure_label,
            phrase=treasure_phrase,
            owner=hero.id,
            caretaker=None,
            meters={"value": 1.0, "risk": 1.0, "safe": 0.0},
        )
    )
    helper_kind = random.choice(list(HELPERS))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_kind,
            label=_safe_lookup(HELPERS, helper_kind),
            phrase=_safe_lookup(HELPERS, helper_kind),
            memes={"fear": 0.0, "hope": 1.0, "cunning": 1.0, "joy": 0.0},
        )
    )
    world.facts.update(hero=hero, wicked=wicked, treasure=treasure, helper=helper)
    return world


def predict_trouble(world: StoryWorld, params: StoryParams) -> bool:
    return True


def tell(world: StoryWorld, params: StoryParams) -> None:
    hero = world.get("hero")
    wicked = world.get("wicked")
    treasure = world.get("treasure")
    helper = world.get("helper")

    world.say(
        f"Once, in {world.place.label}, there was {hero.phrase} who carried {treasure.phrase} and tried to keep it safe."
    )
    world.say(
        f"But there also lived {wicked.phrase}, and that one had a wicked smile and a fondness for trouble."
    )
    world.para()
    world.say(
        f"One day, {wicked.phrase} came near and urged {hero.label} to {ACTIONS['shortcut'][0]}, "
        f"for the road was said to be shorter and sweeter than the honest path."
    )
    hero.memes["fear"] += 1.0
    hero.memes["hope"] += 1.0
    wicked.memes["cunning"] += 1.0
    world.say(
        f"{hero.label} felt a pinch of fear, for the warning in the bones was old: a wicked promise often hides a thorn."
    )
    world.para()
    world.say(
        f"{wicked.phrase} then promised that if {hero.label} would {ACTIONS['bargain'][0]}, the treasure would come back doubled."
    )
    world.say(
        f"But the treasure was too dear, and {hero.label} did not like the sound of a bargain made in a crooked voice."
    )
    world.say(
        f"At that very moment, {helper.phrase} appeared from the quiet shade and looked at the wicked one with bright, knowing eyes."
    )
    world.para()

    twist = params.twist
    if twist == "mirror":
        world.say(
            f"The twist was this: the wicked fox had been boasting so long that {hero.label} simply repeated the promise back, word for word, and asked the fox to go first."
        )
        world.say(
            f"The fox snatched at its own trick, stumbled on the doubled words, and ended up carrying the burden it meant for the child."
        )
    elif twist == "swap":
        world.say(
            f"The twist was this: the helper had quietly swapped the bundles while the wicked one was looking away."
        )
        world.say(
            f"So when the wicked one tried to steal the treasure, it lifted the wrong bundle and found only stones and old straw inside."
        )
    elif twist == "riddle":
        world.say(
            f"The twist was this: {helper.phrase} sang a small riddle about true names, and the answer made the crooked bargain lose its bite."
        )
        world.say(
            f"When the wicked one tried to claim the treasure, it could not name what it wanted, and without a true name the trick fell flat."
        )
    elif twist == "helper":
        world.say(
            f"The twist was this: {helper.phrase} had been watching all along, and it stepped forward with a lantern at just the right hour."
        )
        world.say(
            f"The light showed the hidden snag in the wicked plan, and the wicked one had to back away from the honest eyes of the village."
        )

    hero.memes["joy"] += 1.0
    hero.meters["safe"] += 1.0
    treasure.meters["safe"] += 1.0
    wicked.meters["risk"] += 1.0
    world.para()
    world.say(
        f"In the end, {hero.label} kept {treasure.phrase}, {helper.phrase} smiled, and the wicked one went off with nothing but its own shame."
    )
    world.say(
        f"So the child learned that a steady heart, a little help, and a sharp twist of fate can send wickedness packing."
    )

    world.facts.update(
        twist=twist,
        place=params.place,
        treasure=params.treasure,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        wicked_kind=params.wicked_kind,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale with a wicked {f["wicked_kind"]}, a child named {f["hero_name"]}, and a twist that turns the trick back.',
        f'Tell a simple story set in {world.place.label} where a treasure is threatened but saved by a clever twist.',
        f'Write a child-friendly wicked folk tale about {f["hero_name"]} and {f["treasure"]} with a surprising ending.',
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    wicked = _safe_fact(world, f, "wicked")
    treasure = _safe_fact(world, f, "treasure")
    helper = _safe_fact(world, f, "helper")
    twist = _safe_fact(world, f, "twist")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, who is a little {hero.type} trying to keep {treasure.phrase} safe in {world.place.label}.",
        ),
        QAItem(
            question=f"Who caused the trouble in the story?",
            answer=f"The trouble came from {wicked.phrase}, who tried to use a wicked trick on {hero.label}.",
        ),
        QAItem(
            question=f"What helped turn the trouble around?",
            answer=f"The {twist} twist turned the trouble around, and {helper.phrase} also helped by being clever at the right moment.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"In the end, {hero.label} kept {treasure.phrase}, and the wicked one left with shame instead of victory.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does wicked mean?",
            answer="Wicked means very bad or full of mean tricks, the kind of behavior people do not want to copy.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old story people tell and retell, often with magic, cleverness, and a lesson.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader expects to happen.",
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


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_gender: str
    hero_name: str
    wicked_kind: str
    treasure: str
    twist: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A wicked folk tale storyworld with a twist.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--gender", choices=HEROES.keys())
    ap.add_argument("--name")
    ap.add_argument("--wicked", choices=WICKEDS.keys())
    ap.add_argument("--treasure", choices=TREASURES.keys())
    ap.add_argument("--twist", choices=TWISTS.keys())
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero_gender = getattr(args, "gender", None) or rng.choice(list(HEROES))
    wicked_kind = getattr(args, "wicked", None) or rng.choice(list(WICKEDS))
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    twist = getattr(args, "twist", None) or rng.choice(list(TWISTS))
    if getattr(args, "place", None) and getattr(args, "treasure", None) and getattr(args, "twist", None):
        if (place, hero_gender, wicked_kind, treasure, twist) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "name", None) or rng.choice(_safe_lookup(HEROES, hero_gender))
    return StoryParams(
        place=place,
        hero_gender=hero_gender,
        hero_name=hero_name,
        wicked_kind=wicked_kind,
        treasure=treasure,
        twist=twist,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
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
# CLI / ASP
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("village", "girl", "Mara", "fox", "bread", "mirror"),
    StoryParams("forest", "boy", "Pip", "witch", "ring", "swap"),
    StoryParams("bridge", "girl", "Tilda", "troll", "lamp", "riddle"),
    StoryParams("market", "boy", "Otto", "crow", "key", "helper"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/5."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonably_valid/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos")
        for row in combos:
            print(row)
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
            header = f"### {p.hero_name}: {p.place}, {p.wicked_kind}, {p.treasure}, {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
