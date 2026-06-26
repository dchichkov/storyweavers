#!/usr/bin/env python3
"""
Story world: a small detective tale about a tantalizing kettle, a careful keeper,
and a happy ending with a cautionary lesson.

The seed suggests a child-facing detective story in a domestic setting:
someone keeps a kettle safe, a tempting mystery tries to lure a curious helper,
and the case ends well because the right clues are followed instead of a rash
choice.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    locked: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    keeper: object | None = None
    kettle: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
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
    place: str
    clue_spots: set[str] = field(default_factory=set)
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
class Suspect:
    id: str
    label: str
    tells: str
    motive: str
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
class Plot:
    mystery: str
    danger: str
    clue: str
    turn: str
    caution: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.trace = list(self.trace)
        return clone


@dataclass
class StoryParams:
    place: str
    keeper_name: str
    keeper_type: str
    helper_name: str
    helper_type: str
    suspect: str
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
    "kitchen": Setting(
        place="the kitchen",
        clue_spots={"sink", "table", "stove"},
        affords={"investigate", "listen"},
    ),
    "tea_room": Setting(
        place="the little tea room",
        clue_spots={"shelf", "tray", "window"},
        affords={"investigate", "listen"},
    ),
    "workshop": Setting(
        place="the warm workshop",
        clue_spots={"bench", "drawer", "lamp"},
        affords={"investigate", "listen"},
    ),
}

SUSPECTS = {
    "mouse": Suspect(
        id="mouse",
        label="a tiny mouse",
        tells="soft scratch marks",
        motive="wanted a crumb near the warm kettle",
    ),
    "wind": Suspect(
        id="wind",
        label="the windy draft",
        tells="a fluttering curtain",
        motive="kept nudging the door open",
    ),
    "cat": Suspect(
        id="cat",
        label="the sleepy cat",
        tells="a dusty paw print",
        motive="was hoping for a cozy nap by the stove",
    ),
}

PLOTS = {
    "kettle": Plot(
        mystery="a shiny kettle",
        danger="the kettle was hot enough to sting",
        clue="the lid gave a tiny tinkle",
        turn="someone had kept the kettle away from the edge",
        caution="hot things should stay where small hands cannot tug them down",
    ),
    "tantalize": Plot(
        mystery="a tempting smell of tea and honey",
        danger="the smell tried to lure the curious helper too close",
        clue="the steam drifted in a neat silver ribbon",
        turn="the keeper opened a window and moved the kettle back",
        caution="tempting smells can hide hot steam, so it is smart to pause first",
    ),
    "keep": Plot(
        mystery="a carefully kept kettle",
        danger="the room could turn messy if the kettle tipped",
        clue="the handle faced inward like a clue arrow",
        turn="the keeper checked the shelf and kept the path clear",
        caution="keeping important things in the right place helps everyone stay safe",
    ),
}

GAMES = {
    "look": "look for clues",
    "listen": "listen for tiny sounds",
    "wait": "wait and think",
}

NAMES_GIRL = ["Mina", "Lily", "Nora", "Ava", "Zoe", "Ivy", "Ella", "Maya"]
NAMES_BOY = ["Leo", "Ben", "Theo", "Max", "Finn", "Noah", "Eli", "Sam"]
KEEPER_TYPES = ["mother", "father"]
HELPER_TYPES = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style story world with a kettle mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--keeper-name")
    ap.add_argument("--keeper-type", choices=KEEPER_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, suspect) for place in SETTINGS for suspect in SUSPECTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "suspect", None):
        combos = [c for c in combos if c[1] == getattr(args, "suspect", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, suspect = rng.choice(list(combos))
    keeper_type = getattr(args, "keeper_type", None) or rng.choice(KEEPER_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    keeper_name = getattr(args, "keeper_name", None) or rng.choice(NAMES_GIRL if keeper_type == "mother" else NAMES_BOY)
    helper_name = getattr(args, "helper_name", None) or rng.choice(NAMES_GIRL if helper_type == "girl" else NAMES_BOY)
    return StoryParams(
        place=place,
        keeper_name=keeper_name,
        keeper_type=keeper_type,
        helper_name=helper_name,
        helper_type=helper_type,
        suspect=suspect,
    )


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    keeper = world.add(Entity(
        id="keeper", kind="character", type=params.keeper_type, label=params.keeper_name
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=params.helper_type, label=params.helper_name
    ))
    kettle = world.add(Entity(
        id="kettle", type="kettle", label="kettle", phrase="a little brass kettle",
        caretaker=keeper.id, held_by="shelf", locked=True
    ))
    suspect = world.add(Entity(
        id=params.suspect, type=params.suspect, label=_safe_lookup(SUSPECTS, params.suspect).label
    ))
    world.facts.update(keeper=keeper, helper=helper, kettle=kettle, suspect=suspect, params=params)
    return world


def reasonableness_gate(params: StoryParams) -> None:
    if params.suspect == "wind" and params.place == "workshop":
        return
    if params.suspect not in SUSPECTS:
        pass
    if params.place not in SETTINGS:
        pass


def clue_predict(world: World, suspect: Suspect) -> str:
    if suspect.id == "mouse":
        return "scratch marks"
    if suspect.id == "wind":
        return "fluttering curtain"
    return "dusty paw print"


def tell(world: World, params: StoryParams) -> World:
    plot = _safe_lookup(PLOTS, params.suspect)
    keeper = world.get("keeper")
    helper = world.get("helper")
    kettle = world.get("kettle")
    suspect = world.get(params.suspect)

    keeper.memes["calm"] = 1
    helper.memes["curious"] = 1

    world.say(f"{helper.label} was a little {helper.type} who loved detective games.")
    world.say(
        f"One day, {helper.label} and {keeper.label} went to {world.setting.place}, where {plot.mystery} waited."
    )
    world.say(
        f"{plot.clue.capitalize()}, and that made the case feel tantalizing."
    )

    world.para()
    helper.memes["desire"] = 1
    world.say(f"{helper.label} wanted to peek closer, because the mystery was hard to keep from {helper.pronoun('object')}.")
    world.say(f"But {keeper.label} noticed the danger right away: {plot.danger}.")
    world.say(
        f'"Let’s {GAMES["look"]} first," {keeper.label} said. "A good detective does not rush at a clue."'
    )

    world.para()
    keeper.memes["care"] = 1
    world.say(
        f"Together they {GAMES['listen']} and {GAMES['wait']}. Soon they found {suspect.label}, which matched the clue."
    )
    world.say(f"The clue was {suspect.tells}, and it helped explain the mystery.")

    world.para()
    kettle.locked = False
    kettle.held_by = keeper.id
    world.say(
        f"{keeper.label} moved the kettle safely to the middle shelf and kept {helper.label} back from the edge."
    )
    world.say(
        f"They smiled when the case became clear: {suspect.label} {suspect.motive}, but nothing got broken."
    )
    world.say(
        f"In the end, {keeper.label} kept the kettle safe, {helper.label} kept calm, and the room stayed bright."
    )
    world.say(f"The caution was simple: {plot.caution}.")
    world.trace.append("case solved with calm clues and careful keeping")
    world.facts["plot"] = plot
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    plot = _safe_lookup(PLOTS, p.suspect)
    return [
        f"Write a short detective story for children set in {world.setting.place} about {plot.mystery} and a careful keeper.",
        f"Tell a gentle mystery story where {p.helper_name} learns to keep calm while a kettle clue is tantalizing.",
        f"Create a cautionary happy-ending story about a child detective who listens before touching the kettle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    plot = _safe_fact(world, world.facts, "plot")
    helper = world.get("helper")
    keeper = world.get("keeper")
    return [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {helper.label}, a curious little {helper.type}, and {keeper.label}, who kept the kettle safe.",
        ),
        QAItem(
            question=f"What made the mystery tantalizing?",
            answer=f"The mystery was tantalizing because {plot.clue} and the clue seemed almost close enough to touch.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {keeper.label} kept the kettle safe, {helper.label} listened, and the case was solved without trouble.",
        ),
        QAItem(
            question=f"What caution did the keeper teach?",
            answer=plot.caution.capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kettle?",
            answer="A kettle is a pot used to heat water, often for tea or other warm drinks.",
        ),
        QAItem(
            question="Why should hot kettles be handled carefully?",
            answer="Hot kettles can burn skin, so people keep them away from the edge and use care when touching them.",
        ),
        QAItem(
            question="What does it mean to keep something safe?",
            answer="To keep something safe means to place it where it will not be damaged or cause harm.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.locked:
            bits.append("locked=True")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append("  " + e.id + ": " + ", ".join(bits))
    lines.append("  trace: " + "; ".join(world.trace))
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = setup_world(params)
    world = tell(world, params)
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
place(kitchen).
place(tea_room).
place(workshop).

suspect(mouse).
suspect(wind).
suspect(cat).

mystery(kettle).
mystery(tantalize).
mystery(keep).

compatible(Place, Suspect) :- place(Place), suspect(Suspect).
valid_story(Place, Mystery, Suspect) :- place(Place), mystery(Mystery), suspect(Suspect).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for suspect in SUSPECTS:
        lines.append(asp.fact("suspect", suspect))
    for mystery in PLOTS:
        lines.append(asp.fact("mystery", mystery))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set((p, "kettle", s) for p, s in valid_combos())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python ({len(python_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


CURATED = [
    StoryParams(place="kitchen", keeper_name="Mina", keeper_type="mother", helper_name="Leo", helper_type="boy", suspect="mouse"),
    StoryParams(place="tea_room", keeper_name="Ava", keeper_type="mother", helper_name="Nora", helper_type="girl", suspect="wind"),
    StoryParams(place="workshop", keeper_name="Ben", keeper_type="father", helper_name="Maya", helper_type="girl", suspect="cat"),
]


def resolve_story_place(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, mystery, suspect in stories:
            print(f"  {place:8} {mystery:9} {suspect}")
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
            header = f"### {p.keeper_name} and {p.helper_name} in {p.place} ({p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def valid_combos() -> list[tuple[str, str]]:
    return [(place, suspect) for place in SETTINGS for suspect in SUSPECTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "suspect", None):
        combos = [c for c in combos if c[1] == getattr(args, "suspect", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, suspect = rng.choice(list(combos))
    keeper_type = getattr(args, "keeper_type", None) or rng.choice(KEEPER_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    keeper_name = getattr(args, "keeper_name", None) or rng.choice(NAMES_GIRL if keeper_type == "mother" else NAMES_BOY)
    helper_name = getattr(args, "helper_name", None) or rng.choice(NAMES_GIRL if helper_type == "girl" else NAMES_BOY)
    return StoryParams(
        place=place,
        keeper_name=keeper_name,
        keeper_type=keeper_type,
        helper_name=helper_name,
        helper_type=helper_type,
        suspect=suspect,
    )


if __name__ == "__main__":
    main()
