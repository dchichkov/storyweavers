#!/usr/bin/env python3
"""
storyworlds/worlds/first_crowded_market_bad_ending_twist_fairy.py
==================================================================

A standalone story world for a small fairy-tale market scene with a twist and
a bad ending.

Premise:
- A little child visits a crowded market for the first time.
- The child wants a small prize that feels special.
- The market is busy enough that a trick can happen.

Turn:
- The guardian notices danger and warns the child.
- The child reaches for the prize anyway.
- A market trickster causes a twist that changes what the child thought was
  happening.

Resolution:
- The story ends in a bad ending: the prize is lost, and the child leaves with
  only a small, strange souvenir and a disappointed heart.

This file follows the Storyweavers storyworld contract:
- self-contained stdlib script
- shared results import eagerly
- inline ASP rules + reasonableness gate
- story, QA, trace, json, verify, and show-asp modes
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    trick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the crowded market"
    crowded: bool = True
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
class Prize:
    label: str
    phrase: str
    type: str
    value: str
    gendered: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Trick:
    id: str
    label: str
    method: str
    twist: str
    clue: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "market": Setting(place="the crowded market", crowded=True, affords={"buy"}),
}

PRIZES = {
    "apple": Prize(
        label="apple",
        phrase="a shiny red apple",
        type="apple",
        value="sweet and bright",
        gendered={"girl", "boy"},
    ),
    "ribbon": Prize(
        label="ribbon",
        phrase="a blue ribbon for her hair",
        type="ribbon",
        value="pretty and light",
        gendered={"girl"},
    ),
    "toy": Prize(
        label="toy",
        phrase="a small wooden toy horse",
        type="toy",
        value="carefully carved",
        gendered={"girl", "boy"},
    ),
}

TRICKS = {
    "fox": Trick(
        id="fox",
        label="a fox in a market shawl",
        method="distract",
        twist="the fox was not trying to steal from the child, but from the stall",
        clue="its tail was tucked under the shawl",
    ),
    "sparrow": Trick(
        id="sparrow",
        label="a sparrow with bright ribbon scraps",
        method="dart",
        twist="the sparrow was carrying away shiny bits for its nest",
        clue="its beak was full of scraps",
    ),
    "fairy": Trick(
        id="fairy",
        label="a tiny fairy with flour on her hands",
        method="glimmer",
        twist="the fairy was only trading little favors for crumbs",
        clue="her pockets were stuffed with crumbs",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Tara", "Miri", "Nora", "Lily"]
BOY_NAMES = ["Finn", "Owen", "Pip", "Jory", "Theo", "Ben"]
TRAITS = ["curious", "small", "brave", "careful", "hopeful"]


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    trick: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale market story with a twist and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trick", choices=TRICKS)
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


def prize_at_risk(prize: Prize) -> bool:
    return True


def select_trick(prize: Prize, trick: Trick) -> bool:
    return True


def explain_rejection() -> str:
    return "(No story: this world needs a prize and a trick to make a real market twist.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "prize", None) and getattr(args, "trick", None):
        if not select_trick(_safe_lookup(PRIZES, getattr(args, "prize", None)), _safe_lookup(TRICKS, getattr(args, "trick", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [("market", p, t) for p in PRIZES for t in TRICKS]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[1] == getattr(args, "prize", None)]
    if getattr(args, "trick", None):
        combos = [c for c in combos if c[2] == getattr(args, "trick", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prize_id, trick_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.gendered))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize_id, name=name, gender=gender, parent=parent,
                       trait=trait, trick=trick_id)


def make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    prize = world.add(Entity(id="Prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label,
                             phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=hero.id, caretaker=parent.id))
    trick = world.add(Entity(id="Trick", kind="character", type="fairy" if params.trick == "fairy" else "thing",
                             label=_safe_lookup(TRICKS, params.trick).label))
    return world


def story_text(world: World, params: StoryParams) -> None:
    hero = world.get(params.name)
    parent = world.get("Parent")
    prize = world.get("Prize")
    trick = _safe_lookup(TRICKS, params.trick)

    world.say(
        f"On the first day {hero.id} went to {world.setting.place}, {hero.id} felt as if the whole world had opened its bright little hand."
    )
    world.say(
        f"{hero.id} was a {params.trait} {params.gender} who had never been to the market before, and {hero.pronoun('possessive')} {parent.type} said to stay close in the crowd."
    )
    world.say(
        f"At a stall of apples and bread, {hero.id} saw {prize.phrase} and wanted it at once."
    )
    world.say(
        f"{hero.id}'s {parent.type} frowned kindly and said, \"The market is busy today, and your {prize.label} could vanish in all this pushing and waving.\""
    )
    world.para()
    world.say(
        f"But {hero.id} kept looking at the prize, because {prize.value} things always seemed to shine a little brighter on the first visit."
    )
    world.say(
        f"Then {trick.label} slipped near the stall and began to {trick.method} the sellers with a quick little turn."
    )
    world.say(
        f"The crowd gasped, baskets tipped, and {trick.clue} flashed for one blink of a second."
    )
    world.say(
        f"That was the twist: {trick.twist}."
    )
    world.para()
    world.say(
        f"While everyone looked the other way, the apple rolled under a cart and the stallkeeper lifted the price of the last one. {hero.id} did not get the shiny prize."
    )
    world.say(
        f"{hero.id} went home with empty hands, a sticky thumb from one fallen crumb, and a sad little knot in {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"Still, the first market trip ended with {hero.id} peeking back at the crowd, where the lanterns blinked like tiny gold eyes in the dusk."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy-tale story about the first visit to {world.setting.place} that includes the word "first".',
        f"Tell a gentle crowded-market story where {f['name']} wants {f['prize_phrase']} but a twist changes the day.",
        f"Write a story for a child that ends sadly, with a surprise in the market and a child going home empty-handed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did {f['name']} go for the first time?",
            answer=f"{f['name']} went to {world.setting.place} for the first time.",
        ),
        QAItem(
            question=f"What did {f['name']} want from the market stall?",
            answer=f"{f['name']} wanted {f['prize_phrase']}.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                f"The ending was bad because the crowd caused a twist, the prize was lost, "
                f"and {f['name']} went home empty-handed."
            ),
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {f['twist_text']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crowded market?",
            answer="A crowded market is a place with many people, stalls, voices, and things to buy all at once.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the story turn in a new direction.",
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a story with a magical or old-time feeling, often with talking animals, kind helpers, or strange surprises.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(P) :- prize(P).
trick_possible(T) :- trick(T).
valid_story(Place, Prize, Trick) :- setting(Place), prize(Prize), trick(Trick), prize_at_risk(Prize), trick_possible(Trick).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = {("market", p, t) for p in PRIZES for t in TRICKS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    story_text(world, params)
    world.facts = {
        "name": params.name,
        "prize_phrase": _safe_lookup(PRIZES, params.prize).phrase,
        "twist_text": _safe_lookup(TRICKS, params.trick).twist,
    }
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
    StoryParams(place="market", prize="apple", name="Mina", gender="girl", parent="mother", trait="curious", trick="fox"),
    StoryParams(place="market", prize="ribbon", name="Lily", gender="girl", parent="mother", trait="hopeful", trick="sparrow"),
    StoryParams(place="market", prize="toy", name="Finn", gender="boy", parent="father", trait="careful", trick="fairy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, prize, trick in stories:
            print(f"  {place:8} {prize:8} {trick:8}")
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
            header = f"### {p.name}: first visit to {p.place} (prize: {p.prize}, trick: {p.trick})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
