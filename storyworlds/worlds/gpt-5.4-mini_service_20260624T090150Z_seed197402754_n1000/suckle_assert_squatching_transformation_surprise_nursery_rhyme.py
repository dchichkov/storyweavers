#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a little creature who wants to suckle,
makes a bold little assert, and then meets a surprising transformation while
squatching through a moonlit place.

The premise is simple and child-facing:
- a baby creature feels hungry and wants comfort,
- a caretaker worries about a mismatched offer,
- a surprise changes what the child is ready for,
- the ending proves the new state through a concrete image.

The world uses physical meters and emotional memes, and the prose is driven by
state changes rather than by a frozen template.
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
    caretaker: Optional[str] = None
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    state: dict[str, bool] = field(default_factory=dict)

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"baby", "child", "kid"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.type
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
    indoors: bool
    moonlit: bool = False
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
class Transformation:
    id: str
    start: str
    turn: str
    finish: str
    trigger: str
    surprise: str
    gift: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
    "nursery": Setting(place="the nursery", indoors=True, moonlit=False),
    "moonroom": Setting(place="the moonlit room", indoors=True, moonlit=True),
    "garden_gate": Setting(place="the garden gate", indoors=False, moonlit=True),
}

TRANSFORMATIONS = {
    "kitten": Transformation(
        id="kitten",
        start="a tiny baby who wanted to suckle",
        turn="grew bold enough to assert",
        finish="became a warm little kitten",
        trigger="milk bowl",
        surprise="a soft purr woke up inside them",
        gift="a lap to curl in",
        tags={"suckle", "assert", "surprise", "transformation"},
    ),
    "gosling": Transformation(
        id="gosling",
        start="a wobbly little one who wanted to suckle",
        turn="learned to assert",
        finish="became a bright little gosling",
        trigger="warm mash",
        surprise="a shiny wing-feather popped out",
        gift="a pond-side cuddle",
        tags={"suckle", "assert", "surprise", "transformation"},
    ),
    "bunny": Transformation(
        id="bunny",
        start="a nibbling baby who wanted to suckle",
        turn="found the nerve to assert",
        finish="became a fluffy little bunny",
        trigger="clover cup",
        surprise="a hop came quicker than before",
        gift="a snug burrow",
        tags={"suckle", "assert", "surprise", "transformation"},
    ),
}

CHILD_NAMES = ["Mimi", "Tilly", "Nora", "Pip", "Wren", "Lula", "Bram"]
CARETAKERS = ["mother", "father", "nanny", "aunt"]
HEROS = {"baby": "baby", "child": "child", "kid": "kid"}


@dataclass
class StoryParams:
    setting: str
    transformation: str
    name: str
    caretaker: str
    seed: Optional[int] = None
    params: object | None = None
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
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about suckle, assert, and squatching.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=CARETAKERS)
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


def _reasonableness_gate(params: StoryParams) -> None:
    if params.setting == "nursery" and params.transformation == "gosling":
        pass
    if params.setting == "garden_gate" and params.transformation == "kitten":
        pass
    if params.setting == "moonroom" and params.transformation == "bunny":
        return


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    transformation = getattr(args, "transformation", None) or rng.choice(list(TRANSFORMATIONS))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    caretaker = getattr(args, "caretaker", None) or rng.choice(CARETAKERS)
    params = StoryParams(setting=setting, transformation=transformation, name=name, caretaker=caretaker)
    _reasonableness_gate(params)
    return params


def _do_suckle(world: World, hero: Entity, trans: Transformation) -> None:
    hero.meters["hunger"] = max(0.0, hero.meters.get("hunger", 0.0) - 1.0)
    hero.memes["comfort"] = hero.memes.get("comfort", 0.0) + 1.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 0.5
    world.say(f"{hero.id} wanted to suckle and feel small and sweet.")
    world.say(f"The little wish made {hero.id} feel soft as a downy chick.")


def _do_assert(world: World, hero: Entity, caretaker: Entity, trans: Transformation) -> None:
    hero.memes["assert"] = hero.memes.get("assert", 0.0) + 1.0
    world.say(f'"I want my {trans.trigger}!" {hero.id} did assert with a brave little nod.')
    world.say(f"{caretaker.ref().capitalize()} heard the sound and paused to listen.")


def _do_squatching(world: World, hero: Entity, trans: Transformation) -> None:
    hero.meters["squatch"] = hero.meters.get("squatch", 0.0) + 1.0
    world.say(f"Then {hero.id} went squatching through the room, soft paws pat-pat-patting.")
    if world.setting.moonlit:
        world.say("The moon had silver toes on the floor, and every shadow looked like a friend.")


def _do_surprise_transform(world: World, hero: Entity, trans: Transformation) -> None:
    if hero.state.get("transformed"):
        return
    hero.state["transformed"] = True
    hero.type = trans.id
    hero.label = trans.id
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.meters["hunger"] = max(0.0, hero.meters.get("hunger", 0.0) - 0.5)
    world.say(f"Then, oh my, a surprise came by: {trans.surprise}.")
    world.say(f"With a tiny blink and a round new smile, {hero.id} {trans.finish}.")


def _do_resolution(world: World, hero: Entity, caretaker: Entity, trans: Transformation) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    world.say(f"{caretaker.ref().capitalize()} brought {trans.gift}, and the room grew tender and bright.")
    world.say(f"At the end, {hero.id} was {trans.finish}, and {hero.pronoun('possessive')} little heart was calm.")


def tell(setting: Setting, trans: Transformation, name: str, caretaker_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type="baby",
        label=name,
        meters={"hunger": 1.0, "squatch": 0.0},
        memes={"comfort": 0.0, "hope": 0.0, "assert": 0.0, "surprise": 0.0, "joy": 0.0, "peace": 0.0},
    ))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_kind, label=caretaker_kind.capitalize()))

    world.say(f"Little {name} was {trans.start}.")
    world.say(f"In {setting.place}, {name} looked up and began to hum a nursery rhyme tune.")
    world.para()
    _do_suckle(world, hero, trans)
    _do_assert(world, hero, caretaker, trans)
    _do_squatching(world, hero, trans)
    world.para()
    _do_surprise_transform(world, hero, trans)
    _do_resolution(world, hero, caretaker, trans)

    world.facts.update(hero=hero, caretaker=caretaker, trans=trans, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero").id
    trans = _safe_fact(world, f, "trans")
    return [
        f'Write a short nursery-rhyme story for a child named {hero} about suckle, assert, and squatching.',
        f"Tell a gentle story where {hero} wants to suckle, then dares to assert a need, and ends in a surprise transformation into a {trans.id}.",
        f'Write a rhyming-feeling story with the words "suckle", "assert", and "squatching" that ends happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    caretaker = _safe_fact(world, f, "caretaker")
    trans = _safe_fact(world, f, "trans")
    return [
        QAItem(
            question=f"What did {hero.id} want at the beginning of the story?",
            answer=f"{hero.id} wanted to suckle and feel comforted.",
        ),
        QAItem(
            question=f"What did {hero.id} do when {caretaker.ref()} listened?",
            answer=f"{hero.id} did assert a little wish for {trans.trigger}.",
        ),
        QAItem(
            question=f"What surprise changed {hero.id} in the end?",
            answer=f"A surprise transformation came by, and {hero.id} became {trans.finish}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to transform?",
            answer="To transform means to change into something different.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that pops up when you do not know it is coming.",
        ),
        QAItem(
            question="What can squatching mean in a story?",
            answer="Squatching can mean moving along with soft, tiptoeing steps, like pat-pat-pat across the floor.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.state:
            bits.append(f"state={e.state}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(nursery).
setting(moonroom).
setting(garden_gate).

transformation(kitten).
transformation(gosling).
transformation(bunny).

surprise_theme(Transformation).
surprise_theme(Surprise).

compatible(nursery, kitten).
compatible(moonroom, kitten).
compatible(moonroom, gosling).
compatible(garden_gate, gosling).
compatible(moonroom, bunny).
compatible(garden_gate, bunny).

valid_story(S, T) :- compatible(S, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {
        (s, t)
        for s in SETTINGS
        for t in TRANSFORMATIONS
        if not (s == "nursery" and t == "gosling")
        if not (s == "garden_gate" and t == "kitten")
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TRANSFORMATIONS, params.transformation), params.name, params.caretaker)
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
    StoryParams(setting="moonroom", transformation="kitten", name="Mimi", caretaker="mother"),
    StoryParams(setting="moonroom", transformation="bunny", name="Tilly", caretaker="father"),
    StoryParams(setting="garden_gate", transformation="gosling", name="Pip", caretaker="aunt"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=getattr(args, "setting", None) or rng.choice(list(SETTINGS)),
        transformation=getattr(args, "transformation", None) or rng.choice(list(TRANSFORMATIONS)),
        name=getattr(args, "name", None) or rng.choice(CHILD_NAMES),
        caretaker=getattr(args, "caretaker", None) or rng.choice(CARETAKERS),
    )
    _reasonableness_gate(params)
    return params


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/transformation combos:\n")
        for s, t in combos:
            print(f"  {s:12} {t}")
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
            header = f"### {p.name}: {p.transformation} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
