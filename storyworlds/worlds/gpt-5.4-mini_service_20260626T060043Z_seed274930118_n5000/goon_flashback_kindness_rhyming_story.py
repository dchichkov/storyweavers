#!/usr/bin/env python3
"""
storyworlds/worlds/goon_flashback_kindness_rhyming_story.py
============================================================

A small story world for a rhyming tale about a goon, a flashback, and a
kindness turn.

Premise:
- A little goon wants a cozy treat or keepsake.
- A small snag makes the goon grumpy.
- A flashback reminds the goon of a kindness once received.
- The goon answers with kindness, and the ending proves the change.

The prose is intentionally simple, child-facing, and lightly rhyming.
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
# Core world model
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for key in ("stuck", "worry", "kindness", "joy", "want", "helped", "remember"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
class Place:
    id: str
    name: str
    indoors: bool = True
    rhyme: str = ""
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
class Item:
    id: str
    label: str
    phrase: str
    location: str
    precious: bool = False
    held_by: Optional[str] = None
    clean: bool = True
    prize: object | None = None
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
    place: str
    prize: str
    helper: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.items = copy.deepcopy(self.items)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "nursery": Place("nursery", "the nursery", indoors=True, rhyme="glow"),
    "kitchen": Place("kitchen", "the kitchen", indoors=True, rhyme="spoon"),
    "porch": Place("porch", "the porch", indoors=False, rhyme="breeze"),
    "cubby": Place("cubby", "the cubby", indoors=True, rhyme="nest"),
}

PRIZES = {
    "blanket": Item("blanket", "a soft blue blanket", "a soft blue blanket", "nursery", precious=True),
    "cookie": Item("cookie", "a round honey cookie", "a round honey cookie", "kitchen", precious=True),
    "ball": Item("ball", "a bright red ball", "a bright red ball", "porch", precious=True),
    "kite": Item("kite", "a little paper kite", "a little paper kite", "cubby", precious=True),
}

HELPERS = {
    "mouse": ("mouse", "tiny mouse", "mouse", "small"),
    "bird": ("bird", "yellow bird", "bird", "bright"),
    "cat": ("cat", "striped cat", "cat", "warm"),
    "turtle": ("turtle", "slow turtle", "turtle", "kind"),
}

GON_NAMES = ["Goon", "Moon", "Toon", "June", "Spoon", "Boon"]
HERO_TRAITS = ["silly", "small", "bouncy", "cheery", "wobbly"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def _r_stuck(world: World) -> list[str]:
    hero = world.get("goon")
    prize = world.items["prize"]
    helper = world.get("helper")
    out: list[str] = []
    if hero.meters["want"] >= 1 and not prize.held_by:
        sig = ("stuck", prize.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["worry"] += 1
            out.append(f"The goon frowned and gave a little groan, for the prize was out of reach.")
    if helper.meters["helped"] >= 1 and hero.meters["remember"] >= 1:
        sig = ("kindness_turn",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["kindness"] += 1
            hero.meters["joy"] += 1
            out.append(f"The goon grew gentle and bright as a noon.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _r_stuck(world)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity, prize: Item) -> None:
    world.say(
        f"There once was a goon who was {hero.type if hero.type != 'goon' else 'small'}, "
        f"and loved little things with a tune and a boon."
    )
    world.say(
        f"{hero.id} liked {prize.label}, for it shone in the room, "
        f"and {helper.id} was a friend who could brighten the gloom."
    )
    hero.memes["love"] += 1
    helper.memes["love"] += 1


def want_and_worry(world: World, hero: Entity, prize: Item) -> None:
    hero.meters["want"] += 1
    world.say(
        f"The goon hopped up quick, with a hop and a swoon, "
        f"but the prize was not near, not today, not by noon."
    )
    propagate(world)


def flashback(world: World, hero: Entity, helper: Entity) -> None:
    hero.meters["remember"] += 1
    world.say(
        f"Then a flashback came back, like a soft silver spoon: "
        f"the helper had shared with the goon in a room."
    )
    world.say(
        f"When the goon had been sad, the helper stayed near, "
        f"gave a hug and a snack, and erased the bad tear."
    )


def kindness_choice(world: World, hero: Entity, helper: Entity, prize: Item) -> None:
    hero.memes["kindness"] += 1
    helper.meters["helped"] += 1
    world.say(
        f"So the goon said, 'I'll be kind,' with a smile and a swoon, "
        f"'I will help you first now, before asking for soon.'"
    )
    if prize.location == world.place.id:
        prize.held_by = hero.id
        world.say(
            f"The helper pointed and chirped, and the prize came to view; "
            f"the goon shared it with friends, which was caring and true."
        )
    else:
        world.say(
            f"The goon gave the helper a hand and a cheer, "
            f"and the prize felt much nicer when friends were all near."
        )
    hero.meters["joy"] += 1


def ending(world: World, hero: Entity, helper: Entity, prize: Item) -> None:
    world.para()
    world.say(
        f"Now the goon had a glow, like the moon through a dune, "
        f"for kindness came back and made everyone swoon."
    )
    world.say(
        f"With the helper beside, and the prize safe and fine, "
        f"the day ended sweet, in a warm, happy line."
    )


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add_entity(Entity(
        id="goon",
        kind="character",
        type="goon",
        label="the goon",
    ))
    helper_key = params.helper
    helper_type, helper_label, helper_word, helper_trait = _safe_lookup(HELPERS, helper_key)
    helper = world.add_entity(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_label,
    ))
    prize = world.add_item(Item(
        id="prize",
        label=_safe_lookup(PRIZES, params.prize).label,
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        location=place.id,
        precious=True,
    ))

    world.facts.update(
        place=place,
        hero=hero,
        helper=helper,
        prize=prize,
        helper_trait=helper_trait,
        helper_word=helper_word,
    )

    intro(world, hero, helper, prize)
    world.para()
    want_and_worry(world, hero, prize)
    flashback(world, hero, helper)
    kindness_choice(world, hero, helper, prize)
    ending(world, hero, helper, prize)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper_trait = _safe_fact(world, f, "helper_trait")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short rhyming story for a young child about a goon who remembers kindness and chooses to help.',
        f"Tell a gentle flashback story where the goon meets a {helper_trait} helper and learns to be kind about {prize.label}.",
        f'Write a simple rhyming tale that includes the word "goon" and ends with a kind choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little goon named {hero.id}, and about {helper.label} too.",
        ),
        QAItem(
            question=f"What did the goon want at {place.name}?",
            answer=f"The goon wanted {prize.label}, but it was out of reach at first.",
        ),
        QAItem(
            question="What did the flashback help the goon remember?",
            answer="The flashback helped the goon remember a time when the helper had been kind and shared help.",
        ),
        QAItem(
            question="What did the goon do at the end?",
            answer="The goon chose kindness, helped the helper, and then the ending felt warm and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story pauses to remember something that happened before.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring to someone else.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like moon and spoon.",
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
        lines.append(f"  {e.id}: meters={dict((k, v) for k, v in e.meters.items() if v)} memes={dict((k, v) for k, v in e.memes.items() if v)}")
    for i in world.items.values():
        lines.append(f"  item {i.id}: held_by={i.held_by} clean={i.clean}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the goon has a prize in a place, remembers a kindness,
% and can answer with kindness.
valid_place(P) :- place(P).
valid_prize(I) :- prize(I).
valid_helper(H) :- helper(H).

needs_flashback(P, I, H) :- place(P), prize(I), helper(H).

valid_story(P, I, H) :- valid_place(P), valid_prize(I), valid_helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in PRIZES:
        lines.append(asp.fact("prize", iid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(p, i, h) for p in PLACES for i in PRIZES for h in HELPERS}
    cl = set(asp_valid_stories())
    if cl == py:
        print(f"OK: clingo gate matches Python registry ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and Python registries.")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about a goon, a flashback, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
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
    choices = [
        (p, i, h)
        for p in PLACES
        for i in PRIZES
        for h in HELPERS
        if (getattr(args, "place", None) is None or getattr(args, "place", None) == p)
        and (getattr(args, "prize", None) is None or getattr(args, "prize", None) == i)
        and (getattr(args, "helper", None) is None or getattr(args, "helper", None) == h)
    ]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prize, helper = rng.choice(choices)
    return StoryParams(place=place, prize=prize, helper=helper)


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("nursery", "blanket", "mouse"),
            StoryParams("kitchen", "cookie", "bird"),
            StoryParams("porch", "ball", "cat"),
            StoryParams("cubby", "kite", "turtle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
