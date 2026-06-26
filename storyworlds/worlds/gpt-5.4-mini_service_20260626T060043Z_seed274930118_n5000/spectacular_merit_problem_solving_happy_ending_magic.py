#!/usr/bin/env python3
"""
storyworlds/worlds/spectacular_merit_problem_solving_happy_ending_magic.py
===========================================================================

A small storyworld about magical problem solving, a bit of merit, and a
spectacular happy ending, told in a lightly rhyming, child-facing style.

Seed-tale shape:
- A child wants to earn a merit star.
- A tiny magical problem blocks the way.
- The child notices clues, tries a clever fix, and restores the magic.
- The ending proves the change with a cheerful, sparkling reward.

The world is intentionally compact: a few settings, a few magical problems, and
a few tools that can solve them. The prose is state-driven rather than a frozen
template, and the story quality comes from the simulated turn from trouble to
success.
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

    magic: object | None = None
    gear: object | None = None
    guide: object | None = None
    hero: object | None = None
    trinket: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    mood: str
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
class Problem:
    id: str
    title: str
    trouble: str
    clue: str
    fix_hint: str
    mess: str
    risk: str
    feature: str = "magic"
    rhyme_end: str = "light"
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
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    cover: set[str]
    magic: bool = True
    rhyme_end: str = "glow"
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
    problem: str
    tool: str
    name: str
    gender: str
    guide: str
    trait: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


SETTINGS = {
    "lantern_hall": Setting("the lantern hall", "sparkly", {"glow", "flicker"}),
    "rose_garden": Setting("the rose garden", "fragrant", {"thorn", "glow"}),
    "moon_bridge": Setting("the moon bridge", "silvery", {"fog", "glow"}),
}

PROBLEMS = {
    "flicker": Problem(
        id="flicker",
        title="the flicker",
        trouble="the lanterns kept going dim and quick",
        clue="one lantern had a loose silver wick",
        fix_hint="tuck the wick in snug and neat",
        mess="dim",
        risk="the hall would lose its glow",
        rhyme_end="bright",
        tags={"magic", "spectacular"},
    ),
    "thorn_tangle": Problem(
        id="thorn_tangle",
        title="the thorn tangle",
        trouble="rose vines curled in a prickly heap",
        clue="a ribbon caught where the leaves lay deep",
        fix_hint="lift the ribbon, then guide the vine",
        mess="stuck",
        risk="the path would stay blocked for the line",
        rhyme_end="glow",
        tags={"magic", "problem_solving"},
    ),
    "fog_lull": Problem(
        id="fog_lull",
        title="the fog lull",
        trouble="moon fog drifted in, soft and slow",
        clue="the bridge bells rang but gave no show",
        fix_hint="ring the bells and wave the fan",
        mess="hidden",
        risk="nobody could see the span",
        rhyme_end="clear",
        tags={"magic", "happy_ending"},
    ),
}

TOOLS = {
    "silver_needle": Tool(
        id="silver_needle",
        label="a silver needle",
        phrase="a silver needle with a shining thread",
        solves={"flicker", "thorn_tangle"},
        cover={"dim", "stuck"},
        rhyme_end="gleam",
    ),
    "moon_fan": Tool(
        id="moon_fan",
        label="a moon fan",
        phrase="a moon fan with a chilly blue seam",
        solves={"fog_lull"},
        cover={"hidden"},
        rhyme_end="beam",
    ),
    "song_bell": Tool(
        id="song_bell",
        label="a song bell",
        phrase="a small bell that could sing on cue",
        solves={"flicker", "fog_lull"},
        cover={"dim", "hidden"},
        rhyme_end="tune",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Pip", "Tess", "Nora", "Ivy", "Cora", "Ruby"]
BOY_NAMES = ["Finn", "Theo", "Owen", "Jasper", "Eli", "Milo", "Nico", "Rowan"]
TRAITS = ["brave", "gentle", "clever", "cheery", "lively", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for p, problem in PROBLEMS.items():
            if p not in setting.affords:
                continue
            for t, tool in TOOLS.items():
                if p in tool.solves:
                    out.append((s, p, t))
    return out


def _act_phrase(problem: Problem) -> str:
    return problem.trouble


def _resolve_phrase(problem: Problem) -> str:
    return problem.fix_hint


def tell(setting: Setting, problem: Problem, tool: Tool, hero_name: str, hero_type: str,
         guide_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label=f"the {guide_type}"))
    trinket = world.add(Entity(
        id="merit_star",
        type="star",
        label="merit star",
        phrase="a bright merit star",
        owner=hero.id,
        caretaker=guide.id,
    ))
    gear = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
        magic=tool.magic,
    ))
    gear.worn_by = hero.id

    world.say(
        f"{hero.id} was a {trait} little {hero_type} who loved a sparkly quest, "
        f"for magic can shimmer and magic can jest."
    )
    world.say(
        f"At {setting.place}, {hero.pronoun('possessive')} goal was a merit star, bright as could be, "
        f"to earn it with kindness and carefulness free."
    )
    world.say(
        f"{hero.id} liked the glitter and loved the grand light; "
        f"{setting.mood.capitalize()} days felt merry and nearly all right."
    )

    world.para()
    world.say(
        f"But then came {problem.title}: {problem.trouble}, a tricky old plight."
    )
    world.say(
        f"{problem.clue.capitalize()}, and that was the clue in the sight."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    guide.memes["concern"] = guide.memes.get("concern", 0.0) + 1
    world.say(
        f"{hero.id} frowned at the puzzle, but did not lose cheer; "
        f"{hero.pronoun().capitalize()} whispered, 'I can fix this. The answer is near.'"
    )

    world.para()
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    world.say(
        f"{hero.id} looked at {gear.label} and tried it with care, "
        f"{_resolve_phrase(problem)}, with a steady small flare."
    )
    if problem.id == "flicker":
        world.say(
            f"The wick held its place, and the lanterns shone wide; "
            f"the hall lit like sunrise on a gold-twinkling tide."
        )
    elif problem.id == "thorn_tangle":
        world.say(
            f"The ribbon slid loose, and the vines curled aside; "
            f"the roses stood open with room for each stride."
        )
    else:
        world.say(
            f"The fan sent the fog into silver-blue curls; "
            f"the bridge bells rang clear like soft laughter of pearls."
        )

    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    guide.memes["joy"] = guide.memes.get("joy", 0.0) + 1
    trinket.meters["bright"] = 1.0

    world.para()
    world.say(
        f"Then {guide.label} pinned the merit star on {hero.id}'s coat; "
        f"it gleamed like a comet, a shiny small note."
    )
    world.say(
        f"{hero.id} smiled at the sparkle and skipped home with might; "
        f"the trouble was solved, and the ending was bright."
    )
    world.say(
        f"So magic kept dancing, and all felt serene; "
        f"{hero.id} had a merit of help, and the path stayed clean."
    )

    world.facts.update(
        hero=hero,
        guide=guide,
        trinket=trinket,
        gear=gear,
        setting=setting,
        problem=problem,
        tool=tool,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a rhyming story for a young child about "{problem.title}" at {setting.place}.',
        f"Tell a magical story where {hero.id} solves {_act_phrase(problem)} and earns a merit star.",
        f"Write a cheerful problem-solving tale that ends with a spectacular happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    problem = _safe_fact(world, f, "problem")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What problem did {hero.id} notice at {setting.place}?",
            answer=f"{hero.id} noticed {problem.trouble}, and the clue was that {problem.clue}.",
        ),
        QAItem(
            question=f"What helped {hero.id} solve the problem?",
            answer=f"{hero.id} used {tool.phrase} to solve the problem. That was the clever fix that made the magic work again.",
        ),
        QAItem(
            question=f"What did {guide.label} give {hero.id} at the end?",
            answer=f"{guide.label} gave {hero.id} a merit star because {hero.id} used patience and good problem solving.",
        ),
        QAItem(
            question=f"How did the story end after the fix?",
            answer=f"It ended happily: the trouble cleared, the magic shone again, and {hero.id} smiled at the spectacular glow.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something unusual and wonderful that can make surprising things happen in a story.",
        )
    ],
    "spectacular": [
        QAItem(
            question="What does spectacular mean?",
            answer="Spectacular means very impressive, bright, or exciting to look at.",
        )
    ],
    "merit": [
        QAItem(
            question="What is merit?",
            answer="Merit is good worth or value, and in a story it can mean someone earns praise for doing something helpful.",
        )
    ],
    "problem_solving": [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a trouble and thinking carefully until you find a good fix.",
        )
    ],
    "happy_ending": [
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is the end of a story where the trouble gets fixed and the characters feel glad.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags)
    out: list[QAItem] = []
    for tag in ["magic", "spectacular", "merit", "problem_solving", "happy_ending"]:
        if tag in tags or tag in {"magic", "merit", "problem_solving", "happy_ending"}:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(setting: str, problem: str, tool: str) -> str:
    return f"(No story: {tool} cannot solve {problem} in {setting}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "problem", None) and getattr(args, "tool", None):
        if (getattr(args, "setting", None), getattr(args, "problem", None), getattr(args, "tool", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, tool=tool, name=name,
                       gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(TOOLS, params.tool),
                 params.name, params.gender, params.guide, params.trait)
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


ASP_RULES = r"""
problem_in_setting(P, S) :- problem(P), setting(S), affords(S, P).
tool_solves(T, P) :- tool(T), solves(T, P).
valid_story(S, P, T) :- problem_in_setting(P, S), tool_solves(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.solves):
            lines.append(asp.fact("solves", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(python_set - asp_set))
    print(" only in clingo:", sorted(asp_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming magical storyworld about merit and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams("lantern_hall", "flicker", "silver_needle", "Mina", "girl", "mother", "clever"),
    StoryParams("rose_garden", "thorn_tangle", "silver_needle", "Finn", "boy", "father", "kind"),
    StoryParams("moon_bridge", "fog_lull", "moon_fan", "Luna", "girl", "mother", "brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, p, t in combos:
            print(f"  {s:14} {p:14} {t}")
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
            header = f"### {p.name}: {p.problem} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
