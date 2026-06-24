#!/usr/bin/env python3
"""
A small detective-story world with teamwork, dialogue, and a correction beat.

The seed tale behind this world:
- A child detective and a trusted helper search for a missing library stamp.
- They follow clues, but one clue is wrong.
- The helper notices the mistake, the detective corrects the plan, and they solve the case together.
- The ending proves the change by showing the recovered stamp in the right place.

This script models the story as a tiny simulation with physical meters and
emotional memes, plus an ASP twin for the reasonableness gate.
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
# Core model
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

    clue: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the library"
    indoors: bool = True
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
class Mystery:
    id: str
    clue_name: str
    clue_phrase: str
    clue_place: str
    wrong_place: str
    solution_place: str
    wrong_hint: str
    true_hint: str
    emotion: str
    keyword: str = "correction"
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
    helps: set[str]
    use_phrase: str
    reveal_phrase: str
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
        self.trace: list[str] = []

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


def _is_dirtyish(x: str) -> bool:
    return x in {"scuffed", "smudged", "scattered"}


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "library": Setting(place="the library", indoors=True, affords={"search"}),
    "hall": Setting(place="the old hall", indoors=True, affords={"search"}),
    "station": Setting(place="the station office", indoors=True, affords={"search"}),
}

MYSTERIES = {
    "stamp": Mystery(
        id="stamp",
        clue_name="library stamp",
        clue_phrase="a round blue library stamp",
        clue_place="the reading nook",
        wrong_place="the front desk",
        solution_place="the return cart",
        wrong_hint="a muddy footprint by the front desk",
        true_hint="blue ink under the return cart",
        emotion="curious",
        keyword="correction",
        tags={"stamp", "blue", "ink", "library"},
    ),
    "key": Mystery(
        id="key",
        clue_name="brass key",
        clue_phrase="a small brass key",
        clue_place="the coat rack",
        wrong_place="the window ledge",
        solution_place="the coat rack",
        wrong_hint="a shiny coin on the ledge",
        true_hint="a loop of twine on the coat rack",
        emotion="nervous",
        keyword="correction",
        tags={"key", "brass", "metal"},
    ),
    "map": Mystery(
        id="map",
        clue_name="folded map",
        clue_phrase="a folded paper map",
        clue_place="the bulletin board",
        wrong_place="the sink",
        solution_place="the bulletin board",
        wrong_hint="wet drops by the sink",
        true_hint="a pin left in the board",
        emotion="serious",
        keyword="correction",
        tags={"map", "paper", "board"},
    ),
}

TOOLS = [
    Tool(
        id="notebook",
        label="a little notebook",
        helps={"search", "correction"},
        use_phrase="write down each clue",
        reveal_phrase="check the notes again",
    ),
    Tool(
        id="lamp",
        label="a small lamp",
        helps={"search"},
        use_phrase="shine under shelves",
        reveal_phrase="catch the hidden mark",
    ),
    Tool(
        id="magnifier",
        label="a magnifying glass",
        helps={"search", "correction"},
        use_phrase="look at tiny details",
        reveal_phrase="see the clue was wrong",
    ),
]

HERO_NAMES = ["Maya", "Leo", "Nina", "Owen", "Ivy", "Noah", "Ada", "Eli"]
HELPER_NAMES = ["Sage", "Rae", "Milo", "Tess", "June", "Bram"]
TRAITS = ["careful", "brave", "curious", "steady", "sharp", "patient"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World mechanics
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


def clue_is_plausible(mystery: Mystery) -> bool:
    return mystery.clue_place != mystery.wrong_place


def needs_correction(mystery: Mystery) -> bool:
    return True


def choose_tool(mystery: Mystery) -> Optional[Tool]:
    for tool in TOOLS:
        if "correction" in tool.helps:
            return tool
    return None


def predict(world: World, mystery: Mystery, tool: Tool) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    helper = sim.get("helper")
    sim.facts["wrong_lead"] = True
    sim.facts["corrected"] = True
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    helper.memes["support"] = helper.memes.get("support", 0.0) + 1
    return {
        "correction_possible": bool(tool),
        "teamwork": helper.memes["support"] >= THRESHOLD,
    }


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_gender,
        label=params.hero_name,
        meters={"focus": 1.0},
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_gender,
        label=params.helper_name,
        meters={"attention": 1.0},
        memes={"support": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type=mystery.id,
        label=mystery.clue_name,
        phrase=mystery.clue_phrase,
        owner="setting",
        meters={"hidden": 1.0},
    ))
    tool = choose_tool(mystery)
    if tool is None:
        pass

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        tool=tool,
        mystery=mystery,
        setting=setting,
        correction_needed=needs_correction(mystery),
        plausible=clue_is_plausible(mystery),
    )

    # Act 1: setup
    world.say(
        f"{params.hero_name} was a {params.trait} little detective who loved quiet mysteries."
    )
    world.say(
        f"{params.helper_name} was the kind of friend who listened closely and kept notes neat."
    )
    world.say(
        f"One morning at {setting.place}, they began looking for {mystery.clue_phrase}."
    )
    world.para()

    # Act 2: wrong lead
    world.say(
        f"{params.hero_name} pointed at {mystery.wrong_place} and said, "
        f"\"The clue must be there.\""
    )
    world.say(
        f"{params.helper_name} checked the spot, then said, "
        f"\"Wait, that mark looks wrong.\""
    )
    hero.memes["certainty"] = hero.memes.get("certainty", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    helper.memes["doubt"] = helper.memes.get("doubt", 0.0) + 1
    world.facts["wrong_lead"] = True
    world.say(
        f"Their first guess did not fit the evidence, so {params.hero_name} opened "
        f"{tool.label} to {tool.use_phrase}."
    )
    world.say(
        f"\"You're right,\" {params.hero_name} said. \"I need to correct that lead.\""
    )
    world.para()

    # Act 3: correction and teamwork
    helper.memes["support"] += 1
    hero.memes["focus"] += 1
    world.facts["corrected"] = True
    world.say(
        f"Together, they followed the {mystery.true_hint} and moved to {mystery.solution_place}."
    )
    world.say(
        f"\"Let's check here,\" {params.helper_name} said."
    )
    world.say(
        f"\"Good catch,\" {params.hero_name} replied, and they looked again."
    )
    world.say(
        f"Under the right spot, they found {mystery.clue_phrase} at last."
    )
    world.say(
        f"{params.hero_name} smiled. \"We made a mistake, corrected it, and solved it together.\""
    )
    world.say(
        f"By the end, the little detective and the helper walked away with the case complete."
    )

    world.facts["solved"] = True
    world.facts["tool"] = tool
    return world


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def hero_pronoun(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def helper_pronoun(gender: str, case: str = "subject") -> str:
    return hero_pronoun(gender, case)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short detective story for a young child about "{mystery.keyword}" where {hero.label} and {helper.label} work together.',
        f"Tell a story where {hero.label} makes a wrong guess, then corrects it with help from {helper.label}.",
        f"Write a gentle mystery with dialogue, teamwork, and a correction that leads to finding {mystery.clue_phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    mystery = _safe_fact(world, f, "mystery")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who were the detectives in the story?",
            answer=f"The detectives were {hero.label} and {helper.label}. They worked together to solve the case.",
        ),
        QAItem(
            question=f"What mistake did {hero.label} make at first?",
            answer=f"{hero.label} first guessed the clue was at {mystery.wrong_place}, but that turn was wrong.",
        ),
        QAItem(
            question=f"What did {helper.label} say that helped the case?",
            answer=f"{helper.label} said, \"Wait, that mark looks wrong,\" and that helped {hero.label} correct the lead.",
        ),
        QAItem(
            question=f"What tool helped them check the clues more carefully?",
            answer=f"They used {tool.label} to {tool.use_phrase}, which helped them notice the mistake.",
        ),
        QAItem(
            question=f"Where did they finally find {mystery.clue_name}?",
            answer=f"They found it at {mystery.solution_place} after they corrected their first idea.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="Why is teamwork useful in a mystery?",
            answer="Teamwork helps because two people can notice different clues and catch mistakes together.",
        ),
        QAItem(
            question="What does it mean to correct a mistake?",
            answer="To correct a mistake means to fix it after you notice it is wrong.",
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {e.type:10} {e.label:20} {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Place, Mystery, Tool) :- setting(Place), mystery(Mystery), tool(Tool),
    clue_plausible(Mystery), correction_needed(Mystery),
    tool_helps(Tool, correction), tool_helps(Tool, search).

valid_story(Place, Mystery, Tool, Gender) :- valid(Place, Mystery, Tool), hero_gender(Gender), setting(Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_plausible", mid) if clue_is_plausible(m) else f"% no clue_plausible({mid}).")
        lines.append(asp.fact("correction_needed", mid) if needs_correction(m) else f"% no correction_needed({mid}).")
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("tool_helps", t.id, h))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("hero_gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for mystery_id, mystery in MYSTERIES.items():
            if not clue_is_plausible(mystery):
                continue
            if not needs_correction(mystery):
                continue
            for tool in TOOLS:
                if {"search", "correction"}.issubset(tool.helps):
                    combos.append((place, mystery_id, tool.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with teamwork, dialogue, and correction.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery_id, _tool = rng.choice(list(combos))
    mystery = _safe_lookup(MYSTERIES, mystery_id)
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mystery=mystery_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_valid_combos_for_cli() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos_for_cli()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, mystery, tool) combos "
              f"({len(stories)} with gender):\n")
        for place, mystery, tool in triples:
            genders = sorted(g for (p, m, t, g) in stories if (p, m, t) == (place, mystery, tool))
            print(f"  {place:10} {mystery:10} {tool:10}  [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="library", mystery="stamp", hero_name="Maya", hero_gender="girl",
                        helper_name="Sage", helper_gender="boy", trait="careful"),
            StoryParams(place="hall", mystery="key", hero_name="Leo", hero_gender="boy",
                        helper_name="Tess", helper_gender="girl", trait="curious"),
            StoryParams(place="station", mystery="map", hero_name="Ivy", hero_gender="girl",
                        helper_name="Milo", helper_gender="boy", trait="patient"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
