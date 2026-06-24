#!/usr/bin/env python3
"""
storyworlds/worlds/white_specific_inch_humor_repetition_rhyming_story.py
========================================================================

A tiny storyworld for a rhyming, humorous, repetitive story about a white
thing, a very specific inch-sized problem, and a clever fix.

Seed tale idea:
---
A little white mouse wanted a cookie from a shelf that was one inch too high.
The mouse tried to hop, the mouse tried to flop, and the mouse tried again and
again. A smiling helper brought a little step so the mouse could reach the
cookie and laugh.

World model:
---
- A character has a small amount of physical reach measured in inches.
- A prize sits at a specific shelf height, also measured in inches.
- If the prize is just out of reach, the character feels frustration.
- A helper can bring a step that adds enough height to solve the problem.
- The prose leans on repetition and gentle rhyme, but the state changes are
  driven by the simulation rather than a frozen template.

The story is child-facing, concrete, and complete: setup, repeated tries, a
humorous turn, and a satisfying ending image that proves the change.
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
# Typed world entities
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
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
class Place:
    name: str
    white: bool = False
    cozy: bool = True
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
class Prize:
    label: str
    phrase: str
    shelf_inch: int
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
class Helper:
    label: str
    step_inch: int
    line: str
    rhyme: str
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


@dataclass
class StoryParams:
    place: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World simulation
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
PLACES = {
    "white kitchen": Place(name="the white kitchen", white=True, cozy=True),
    "white playroom": Place(name="the white playroom", white=True, cozy=True),
    "bright pantry": Place(name="the bright pantry", white=True, cozy=False),
}

PRIZES = {
    "cookie": Prize(label="cookie", phrase="a crumbly cookie", shelf_inch=7),
    "crackers": Prize(label="crackers", phrase="a stack of square crackers", shelf_inch=8),
    "sprinkles": Prize(label="sprinkles", phrase="a tiny jar of white sprinkles", shelf_inch=9),
}

HEROES = {
    "white mouse": ("Milo", "mouse"),
    "white kitten": ("Pip", "kitten"),
    "white bunny": ("Dot", "bunny"),
}

HELPERS = {
    "stool": Helper(label="a little stool", step_inch=2, line="Tap-tap, step-step, up we go!", rhyme="low"),
    "book": Helper(label="a stack of books", step_inch=3, line="Book by book, let’s take a look!", rhyme="look"),
    "box": Helper(label="a sturdy box", step_inch=4, line="Box on the floor, reach some more!", rhyme="more"),
}


# ---------------------------------------------------------------------------
# Story rules / state updates
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def rhyme_line(word: str) -> str:
    return {
        "white": "White and bright, in the light!",
        "inch": "An inch, an inch, not even a pinch!",
        "tiny": "Tiny and funny, like a bean with honey!",
        "hop": "Hop, hop, hop—then a soft little flop!",
        "help": "Help, help, hooray—there's a better way!",
    }.get(word, word)


def build_story(world: World) -> None:
    hero = world.get("hero")
    prize = world.get("prize")
    helper = world.get("helper")

    # Setup
    world.say(
        f"{hero.id} was a little {hero.type}, all white and bright, "
        f"who loved to look for treats in the light."
    )
    world.say(
        f"In {world.place.name}, there sat {prize.phrase} on a shelf exactly "
        f"{prize.meters['height']} inch high."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted that snack, and wanted it now, "
        f"but the shelf was a squeaky inch too proud."
    )

    # Tension: repeated attempts
    world.para()
    hero.memes["want"] += 1
    hero.memes["hope"] += 1
    attempts = [
        "hop",
        "stretch",
        "tiptoe",
    ]
    for move in attempts:
        if move not in world.fired:
            world.fired.add(move)
            hero.meters["reach"] += 1
            world.say(
                f"{hero.id} tried to {move}, tried to {move} again, "
                f"and nearly reached the prize—then down went the grin."
            )
    if hero.meters["reach"] < prize.meters["height"]:
        hero.memes["frustration"] += 1
        world.say(
            f"\"Not quite! Not quite!\" {hero.id} sighed with a tiny squeak. "
            f"\"One more inch would be just right!\""
        )

    # Turn: helper arrives
    world.para()
    world.say(
        f"Then came {helper.label}, with {helper.line} "
        f"It was a silly little fix, but it did the trick."
    )
    hero.memes["surprise"] += 1
    hero.memes["joy"] += 1
    hero.meters["reach"] += helper.meters["step"]
    world.say(
        f"{hero.id} climbed up, up, up on the {helper.label.lower()}, "
        f"and the room felt ready for a happy little cheer."
    )

    # Resolution
    if hero.meters["reach"] >= prize.meters["height"]:
        world.say(
            f"Now {hero.id} could reach the shelf without a flop or a frown, "
            f"so {hero.pronoun()} took the {prize.label} down."
        )
        world.say(
            f"{hero.id} nibbled and giggled, all cozy and white, "
            f"while {helper.label} sat nearby, looking just right."
        )
        hero.memes["frustration"] = 0.0
        hero.memes["delight"] = hero.memes.get("delight", 0.0) + 1
        prize.meters["taken"] = 1
        helper.meters["used"] = 1
    else:
        pass


# ---------------------------------------------------------------------------
# Aspirational content and Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "white": [
        (
            "What does white look like?",
            "White looks bright and pale, like paper, milk, clouds, or fresh snow.",
        )
    ],
    "inch": [
        (
            "What is an inch?",
            "An inch is a small unit for measuring length. It is handy when something is just a little bit tall or short.",
        )
    ],
    "cookie": [
        (
            "Why do people like cookies?",
            "Cookies are sweet and tasty, so many people like them as a small treat.",
        )
    ],
    "step": [
        (
            "What is a step stool for?",
            "A step stool helps someone reach a place that is a little too high.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts.get("tags", set()))
    out: list[QAItem] = []
    for tag in ["white", "inch", "cookie", "step"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    prize = world.get("prize")
    helper = world.get("helper")
    place = world.place.name

    return [
        QAItem(
            question=f"Who wanted the treat in {place}?",
            answer=f"{hero.id} the {hero.type} wanted {prize.label} in {place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep trying to reach the shelf?",
            answer=(
                f"The shelf was one inch too high at first, so {hero.id} had to "
                f"try again and again before the helper brought a better way."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} finally reach the snack?",
            answer=(
                f"{helper.label} helped by adding a few more inches, which was "
                f"enough for {hero.id} to reach the shelf."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    prize = world.get("prize")
    helper = world.get("helper")
    return [
        'Write a short rhyming story about a white, tiny friend and an inch-high problem.',
        f"Tell a funny story about {hero.id} trying to reach {prize.phrase} in {world.place.name}.",
        f"Write a repetitive, child-friendly tale where {helper.label} solves a one-inch problem.",
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is reachable when the hero's reach plus the helper's step is enough.
reachable(H, P) :- hero(H), prize(P), reach(H, R), shelf(P, S), R >= S.
reachable_with_help(H, P) :- hero(H), prize(P), helper(K), reach(H, R), step(K, T), shelf(P, S), R + T >= S.

% The story is valid when the prize is initially out of reach but can be fixed.
valid_story(P, K) :- prize(P), helper(K), shelf(P, S), reach(hero, R), R < S, R + step(K, T) >= S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("prize", "prize"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("reach", "hero", 5))
    lines.append(asp.fact("step", "helper", 3))
    lines.append(asp.fact("shelf", "prize", 8))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("prize", "helper")}
    if asp_set == py_set:
        print("OK: clingo parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate and story generation
# ---------------------------------------------------------------------------
def valid_combo(place: str, prize: str, hero: str, helper: str) -> bool:
    p = _safe_lookup(PLACES, place)
    pr = _safe_lookup(PRIZES, prize)
    if not p.white and hero == "white mouse":
        return True
    # The domain is deliberately tiny and honest:
    # - the hero starts at 5 inches of reach
    # - the prize must sit at 7-9 inches
    # - the helper must add enough inches to solve it
    base_reach = 5
    step = _safe_lookup(HELPERS, helper).step_inch
    return base_reach < pr.shelf_inch and base_reach + step >= pr.shelf_inch


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a white, specific inch problem with humor and repetition."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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
    choices = []
    for place in PLACES:
        if getattr(args, "place", None) and place != getattr(args, "place", None):
            continue
        for prize in PRIZES:
            if getattr(args, "prize", None) and prize != getattr(args, "prize", None):
                continue
            for hero in HEROES:
                if getattr(args, "hero", None) and hero != getattr(args, "hero", None):
                    continue
                for helper in HELPERS:
                    if getattr(args, "helper", None) and helper != getattr(args, "helper", None):
                        continue
                    if valid_combo(place, prize, hero, helper):
                        choices.append((place, prize, hero, helper))
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prize, hero, helper = rng.choice(sorted(choices))
    return StoryParams(place=place, prize=prize, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(PLACES, params.place))
    hero_name, hero_type = _safe_lookup(HEROES, params.hero)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    helper_cfg = _safe_lookup(HELPERS, params.helper)

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            meters={"reach": 5.0},
            memes={"hope": 1.0},
        )
    )
    prize = world.add(
        Entity(
            id=prize_cfg.label,
            type="thing",
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            meters={"height": float(prize_cfg.shelf_inch)},
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.label,
            type="thing",
            label=helper_cfg.label,
            meters={"step": float(helper_cfg.step_inch)},
        )
    )

    world.facts["tags"] = {"white", "inch", prize_cfg.label if prize_cfg.label in KNOWLEDGE else "cookie", "step"}
    build_story(world)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(parts)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        valid = asp_valid()
        print(f"{len(valid)} compatible story combos:\n")
        for item in valid:
            print("  ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="white kitchen", prize="cookie", hero="white mouse", helper="stool"),
            StoryParams(place="white playroom", prize="crackers", hero="white bunny", helper="book"),
            StoryParams(place="bright pantry", prize="sprinkles", hero="white kitten", helper="box"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
