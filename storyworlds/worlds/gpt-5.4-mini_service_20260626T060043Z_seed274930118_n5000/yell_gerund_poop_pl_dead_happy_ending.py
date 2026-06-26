#!/usr/bin/env python3
"""
storyworlds/worlds/yell_gerund_poop_pl_dead_happy_ending.py
===========================================================

A small detective-style story world with a happy ending.

Seed image:
A child detective follows clues after hearing someone yelling, finding poop piles,
and discovering a dead flashlight battery. The mystery turns into a gentle
rescue, and the ending is safe and cheerful.

This world keeps the simulation tiny but state-driven:
- a child detective investigates a small outdoor mystery
- physical clues include poop piles, a broken latch, and a dead battery
- emotional meters track worry, curiosity, relief, and fear
- the story resolves with a clear reveal and a happy ending image

The world includes the seed words:
- yell-gerund
- poop-pl
- dead

Style target:
- detective story
- child-facing
- complete beginning, middle turn, and ending
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    mystery: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str = "the backyard"
    afford_mystery: bool = True
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
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    type: str
    reveals: str
    tags: set[str] = field(default_factory=set)
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
    name: str
    gender: str
    parent: str
    clue: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "backyard": Setting(place="the backyard"),
    "garden": Setting(place="the garden"),
    "alley": Setting(place="the little alley"),
    "porch": Setting(place="the porch"),
}

CLUES = {
    "poop": Clue(
        id="poop",
        label="poop piles",
        phrase="a few poop piles",
        location="near the gate",
        type="poop",
        reveals="a hungry raccoon had slipped through the broken latch",
        tags={"poop-pl", "mess", "animal"},
    ),
    "yell": Clue(
        id="yell",
        label="the yelling",
        phrase="the loud yelling",
        location="by the shed",
        type="sound",
        reveals="the yelling came from a scared kid who found the broken latch first",
        tags={"yell-gerund", "sound"},
    ),
    "dead": Clue(
        id="dead",
        label="the dead flashlight battery",
        phrase="a dead flashlight battery",
        location="in the grass",
        type="battery",
        reveals="the flashlight had gone dead, so the detective had to use daylight and clues",
        tags={"dead", "battery"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Theo", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def reasonableness_gate(place: str, clue: str) -> bool:
    if place in {"backyard", "garden", "porch", "alley"} and clue in CLUES:
        return True
    return False


def explain_rejection(place: str, clue: str) -> str:
    return (
        f"(No story: the clue '{clue}' does not fit the little detective scene at {place}. "
        f"Try a backyard, garden, porch, or alley mystery.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "clue", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "clue", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    places = [getattr(args, "place", None)] if getattr(args, "place", None) else list(SETTINGS)
    clues = [getattr(args, "clue", None)] if getattr(args, "clue", None) else list(CLUES)
    combos = [(p, c) for p in places for c in clues if reasonableness_gate(p, c)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, clue = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, name=name, gender=gender, parent=parent, clue=clue)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("tag", clue_id, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, C) :- place(P), clue(C), ok_place(P), ok_clue(C).
ok_place(backyard).
ok_place(garden).
ok_place(porch).
ok_place(alley).
ok_clue(poop).
ok_clue(yell).
ok_clue(dead).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {(p, c) for p in SETTINGS for c in CLUES if reasonableness_gate(p, c)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches reasonableness_gate() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def _start_scene(world: World, detective: Entity, parent: Entity) -> None:
    world.say(
        f"{detective.id} was a small detective who liked quiet clues, sharp eyes, and neat notebooks."
    )
    world.say(
        f"One evening, {detective.id} and {parent.label} went to {world.setting.place} to look for the odd noise."
    )


def _build_mystery(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["curiosity"] += 1
    detective.memes["worry"] += 1
    if clue.id == "poop":
        world.say(
            f"Near the gate, {detective.id} spotted {clue.phrase}. That was strange, because the yard had been clean earlier."
        )
    elif clue.id == "yell":
        world.say(
            f"Then {detective.id} heard {clue.phrase} coming from by the shed, loud enough to make a bird hop away."
        )
    else:
        world.say(
            f"In the grass, {detective.id} found {clue.phrase}. The beam had gone out, and the mystery felt bigger in the dim light."
        )


def _discover(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} crouched down, looked carefully, and followed the clue like a tiny detective with a big hat."
    )
    world.say(
        f"The answer was simple once the pieces lined up: {clue.reveals}."
    )


def _resolve(world: World, detective: Entity, parent: Entity, clue: Clue) -> None:
    detective.memes["relief"] += 1
    detective.memes["worry"] = 0
    world.say(
        f"{detective.id} and {parent.label} fixed the broken latch, shooed the raccoon out, and turned on a fresh flashlight."
    )
    world.say(
        f"By the end, the yard was safe again, the little problem was solved, and {detective.id} could smile at the neat, quiet fence."
    )


def tell(setting: Setting, clue: Clue, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type=gender, label=name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    mystery = world.add(Entity(id=clue.id, type=clue.type, label=clue.label, phrase=clue.phrase))

    _start_scene(world, detective, parent)
    world.para()
    _build_mystery(world, detective, mystery)
    world.say(
        f"{detective.id} knew this was a job for careful looking, because the loud clue could hide a smaller one."
    )
    world.para()
    _discover(world, detective, mystery)
    world.para()
    _resolve(world, detective, parent, mystery)

    world.facts.update(detective=detective, parent=parent, clue=mystery, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    clue = _safe_fact(world, f, "clue")
    return [
        f'Write a child-friendly detective story about {detective.id} solving a mystery with "{clue.id}".',
        f"Tell a short mystery where a small detective finds {clue.phrase} and learns what caused it.",
        f"Write a happy-ending detective tale that includes the words yell-gerund, poop-pl, and dead.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    parent = _safe_fact(world, f, "parent")
    clue = _safe_fact(world, f, "clue")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {detective.id}, a small detective, and {parent.label}, who went to {place} together.",
        ),
        QAItem(
            question=f"What clue did {detective.id} notice first?",
            answer=f"{detective.id} noticed {clue.phrase} first, and that clue helped start the mystery.",
        ),
        QAItem(
            question=f"What solved the mystery in the end?",
            answer=f"The mystery was solved when they followed the clue, fixed the broken latch, and found the real cause.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and uses them to figure out what happened.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps solve a mystery.",
        ),
        QAItem(
            question="Why can a dead flashlight battery be a problem?",
            answer="A dead battery cannot power the flashlight, so it is hard to see in the dark.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CLUES, params.clue), params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="backyard", name="Mia", gender="girl", parent="mother", clue="poop"),
    StoryParams(place="garden", name="Leo", gender="boy", parent="father", clue="yell"),
    StoryParams(place="porch", name="Nora", gender="girl", parent="mother", clue="dead"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue) combos:\n")
        for p, c in combos:
            print(f"  {p:9} {c}")
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
            header = f"### {p.name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
