#!/usr/bin/env python3
"""
certain_sync_dance_studio_inner_monologue_humor.py

A small storyworld set in a dance studio, told in a fable-like style with
inner-monologue beats and light humor.

Premise:
A child dancer wants to perform a tricky synchronized routine in a dance studio.
The studio's mirror, metronome, and practice ribbons make timing visible, but a
single miscount can ruin the group sync. A patient teacher helps the child
notice the beat, steady their nerves, and finish in harmony.
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

THEME_WORDS = {"certain", "sync"}
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    teacher: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Studio:
    place: str = "the dance studio"
    mirror: bool = True
    music: bool = True
    affords: set[str] = field(default_factory=lambda: {"count", "turn", "leap"})
    STUDIOS: set[str] = field(default_factory=set)
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
class Move:
    id: str
    name: str
    timing: str
    challenge: str
    mistake: str
    fix: str
    keyword: str
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
class Prop:
    id: str
    label: str
    phrase: str
    helps: set[str]
    mood: str
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
    place: str = "studio"
    move: str = "count"
    prop: str = "metronome"
    name: str = "Milo"
    gender: str = "boy"
    teacher: str = "teacher"
    trait: str = "eager"
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
    def __init__(self, studio: Studio) -> None:
        self.studio = studio
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


MOVES = {
    "count": Move(
        id="count",
        name="count the beat",
        timing="counting the beat",
        challenge="the steps have to land right on the music",
        mistake="her mind may skip ahead of the beat",
        fix="she can count softly and watch the metronome",
        keyword="sync",
        tags={"sync", "beat", "music"},
    ),
    "turn": Move(
        id="turn",
        name="spin in a turn",
        timing="turning on the beat",
        challenge="the body must finish the spin in time",
        mistake="she may wobble and miss the landing",
        fix="she can spot the mirror and keep her shoulders steady",
        keyword="certain",
        tags={"sync", "balance", "mirror"},
    ),
    "leap": Move(
        id="leap",
        name="leap across the floor",
        timing="leaping together",
        challenge="the leap must leave and land with the music",
        mistake="she may jump early and break the pattern",
        fix="she can listen for the drum and match the group",
        keyword="sync",
        tags={"sync", "music", "group"},
    ),
}

PROPS = {
    "metronome": Prop(
        id="metronome",
        label="metronome",
        phrase="a wooden metronome",
        helps={"count", "turn"},
        mood="steady",
    ),
    "ribbon": Prop(
        id="ribbon",
        label="practice ribbon",
        phrase="a bright practice ribbon",
        helps={"turn", "leap"},
        mood="playful",
    ),
    "shoes": Prop(
        id="shoes",
        label="dance shoes",
        phrase="a pair of soft dance shoes",
        helps={"count", "leap"},
        mood="quiet",
    ),
}

STUDIOS = {"studio": Studio(place="the dance studio")}

GIRL_NAMES = ["Ava", "Mina", "Nora", "Lia", "Tia", "Elsa"]
BOY_NAMES = ["Milo", "Nico", "Theo", "Perry", "Arlo", "Jude"]
TRAITS = ["eager", "careful", "brave", "dreamy", "bright", "determined"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in STUDIOS:
        for move_id in MOVES:
            for prop_id, prop in PROPS.items():
                if move_id in prop.helps:
                    combos.append((place, move_id, prop_id))
    return combos


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _counting_desc(move: Move) -> str:
    return {
        "count": "the beat felt like a little drum inside the chest",
        "turn": "the spin felt like a secret circle drawn in the air",
        "leap": "the leap felt like a bird learning the wind",
    }.get(move.id, "the practice felt lively")


def _intro(world: World, hero: Entity, teacher: Entity, move: Move, prop: Prop) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved the dance studio, "
        f"where the mirror shone and the floor kept every brave step."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted {move.name}, because "
        f"{_counting_desc(move)}."
    )
    world.say(
        f"On the shelf sat {prop.phrase}, and {teacher.label} said it would help "
        f"the class stay {move.keyword}."
    )


def _wish(world: World, hero: Entity, move: Move) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(
        f"In {hero.id}'s head, a small voice said, "
        f'"This time I will be {move.keyword} for sure."'
    )


def _warning(world: World, teacher: Entity, hero: Entity, move: Move, prop: Prop) -> None:
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1
    world.say(
        f"{teacher.label} tapped the metronome and smiled. "
        f'"Slow feet first," {teacher.pronoun()} said, "or the music will laugh and run away."'
    )
    world.say(
        f"{hero.id} listened and thought, " + '"What if I am not ready yet?"'
    )
    world.say(
        f"But {hero.pronoun('possessive')} feet already wanted to hurry, "
        f"and that made the timing shaky."
    )


def _misstep(world: World, hero: Entity, move: Move) -> None:
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1
    hero.meters["offbeat"] = hero.meters.get("offbeat", 0.0) + 1
    world.say(
        f"{hero.id} tried to {move.name}, but one step landed before the beat."
    )
    world.say(
        f'{hero.id} thought, "Oh no. My feet are speaking first and my ears are late."'
    )


def _helper(world: World, teacher: Entity, hero: Entity, move: Move, prop: Prop) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{teacher.label} pointed to {prop.label} and said, "
        f'"Let your eyes borrow some calm."'
    )
    world.say(
        f'Then {teacher.id} whispered, "You do not need to be perfect. You only need to be certain of the next beat."'
    )
    world.say(
        f"{hero.id} breathed in, counted under {hero.pronoun('possessive')} breath, "
        f"and tried again."
    )


def _resolution(world: World, hero: Entity, move: Move) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 2
    hero.memes["certainty"] = hero.memes.get("certainty", 0.0) + 1
    hero.meters["offbeat"] = 0.0
    world.say(
        f"This time {hero.id} moved with the music, and the whole line of dancers stayed {move.keyword}."
    )
    world.say(
        f"{hero.id}'s own little voice said, "
        f'"I can be brave one beat at a time," and the mirror seemed to nod.'
    )
    world.say(
        f"At the end, {hero.id} finished in place, smiling, while the metronome clicked like a proud tiny clock."
    )


def tell(studio: Studio, move: Move, prop: Prop, hero_name: str, hero_type: str,
         trait: str, teacher_type: str = "teacher") -> World:
    world = World(studio)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    teacher = world.add(Entity(id="Teacher", kind="character", type=teacher_type, label="the teacher"))
    world.add(Entity(id=prop.id, type=prop.label, label=prop.label, phrase=prop.phrase))
    _intro(world, hero, teacher, move, prop)
    world.para()
    _wish(world, hero, move)
    _warning(world, teacher, hero, move, prop)
    _misstep(world, hero, move)
    world.para()
    _helper(world, teacher, hero, move, prop)
    _resolution(world, hero, move)
    world.facts.update(hero=hero, teacher=teacher, move=move, prop=prop, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    move: Move = _safe_fact(world, f, "move")
    prop: Prop = _safe_fact(world, f, "prop")
    return [
        f'Write a fable-like story for a small child about {hero.id} learning to stay {move.keyword} in a dance studio.',
        f"Tell a gentle story with inner monologue and humor where {hero.id} wants to {move.name} and uses {prop.label} to help.",
        f'Write a short story that includes the words "certain" and "sync" and ends with a happy dance in a studio.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    teacher: Entity = _safe_fact(world, f, "teacher")
    move: Move = _safe_fact(world, f, "move")
    prop: Prop = _safe_fact(world, f, "prop")
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the dance studio?",
            answer=f"{hero.id} wanted to {move.name}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay {move.keyword}?",
            answer=f"{teacher.label} helped {hero.id} by pointing to {prop.label} and reminding {hero.pronoun('object')} to be certain of the next beat.",
        ),
        QAItem(
            question=f"What did {hero.id} think after the first mistake?",
            answer=f"{hero.id} thought that the feet were speaking first and the ears were late.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} finishing the dance in time, smiling in the dance studio while the metronome clicked proudly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a metronome do?",
            answer="A metronome makes steady clicks to help dancers or musicians keep a regular beat.",
        ),
        QAItem(
            question="Why is a mirror useful in a dance studio?",
            answer="A mirror lets dancers watch their posture, shape, and timing so they can improve.",
        ),
        QAItem(
            question="What does it mean to sync with music?",
            answer="To sync with music means to move at the same time as the beat or with the other dancers.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("\n== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
move_help(M, P) :- move(M), prop(P), helps(P, M).
valid(Place, Move, Prop) :- studio(Place), move(Move), prop(Prop), move_help(Move, Prop).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in STUDIOS:
        lines.append(asp.fact("studio", s))
    for m in MOVES:
        lines.append(asp.fact("move", m))
    for p, prop in PROPS.items():
        lines.append(asp.fact("prop", p))
        for mv in sorted(prop.helps):
            lines.append(asp.fact("helps", p, mv))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - asp_set))
    print("only in asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Dance studio fable with sync and certainty.")
    ap.add_argument("--place", choices=STUDIOS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--teacher", choices=["teacher"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "move", None) is None or c[1] == getattr(args, "move", None))
              and (getattr(args, "prop", None) is None or c[2] == getattr(args, "prop", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, move, prop = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, move=move, prop=prop, name=name, gender=gender, teacher="teacher", trait=trait)


def generate(params: StoryParams) -> StorySample:
    move = _safe_lookup(MOVES, params.move)
    prop = _safe_lookup(PROPS, params.prop)
    world = tell(_safe_lookup(STUDIOS, params.place), move, prop, params.name, params.gender, params.trait)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="studio", move="count", prop="metronome", name="Milo", gender="boy", teacher="teacher", trait="eager"),
    StoryParams(place="studio", move="turn", prop="ribbon", name="Ava", gender="girl", teacher="teacher", trait="careful"),
    StoryParams(place="studio", move="leap", prop="shoes", name="Theo", gender="boy", teacher="teacher", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.move} with {p.prop} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
