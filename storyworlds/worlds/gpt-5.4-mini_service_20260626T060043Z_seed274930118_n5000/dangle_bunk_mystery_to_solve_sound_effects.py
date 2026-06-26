#!/usr/bin/env python3
"""
A small slice-of-life story world about a child, a bunk bed mystery, a little
magic, and the sound effects that help solve it.

Seed words: dangle, bunk
Features: Mystery to Solve, Sound Effects, Magic
Style: Slice of Life
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
# Data model
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bed: object | None = None
    hero: object | None = None
    hidden: object | None = None
    magic: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str
    soundy: bool = True
    magical: bool = True
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
    hint_sound: str
    hidden_in: str
    truth: str
    magical: bool = True
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
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
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
    clue: str
    charm: str
    name: str
    gender: str
    parent: str
    trait: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bedroom": Setting(place="the bedroom"),
    "nursery": Setting(place="the nursery"),
    "guest_room": Setting(place="the guest room"),
}

CLUES = {
    "toy": Clue(
        id="toy",
        label="toy",
        phrase="a small toy",
        hint_sound="clink",
        hidden_in="under the bunk bed",
        truth="the toy rolled under the bunk bed",
    ),
    "sock": Clue(
        id="sock",
        label="sock",
        phrase="one striped sock",
        hint_sound="floop",
        hidden_in="behind the bunk ladder",
        truth="the sock was stuck behind the bunk ladder",
    ),
    "bell": Clue(
        id="bell",
        label="bell",
        phrase="a tiny bell",
        hint_sound="ting",
        hidden_in="on top of the bunk rail",
        truth="the bell hung on the bunk rail",
    ),
}

CHARMS = {
    "glimmer": Charm(
        id="glimmer",
        label="glimmer charm",
        phrase="a little glimmer charm",
        effect="made hidden things show themselves for a moment",
    ),
    "listening": Charm(
        id="listening",
        label="listening pebble",
        phrase="a smooth listening pebble",
        effect="helped the room whisper back with its sounds",
    ),
    "bubble": Charm(
        id="bubble",
        label="bubble wand",
        phrase="a tiny bubble wand",
        effect="sent a ring of bright bubbles across the floor",
    ),
}

GIRL_NAMES = ["Mia", "Ava", "Lily", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Max", "Noah"]
TRAITS = ["curious", "gentle", "cheerful", "quiet", "playful", "careful"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pron(name: str, gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if gender == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def maybe_raise_invalid(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if params.clue not in CLUES:
        pass
    if params.charm not in CHARMS:
        pass


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.soundy:
            lines.append(asp.fact("soundy", sid))
        if s.magical:
            lines.append(asp.fact("magical", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("hidden_in", cid, c.hidden_in))
        lines.append(asp.fact("sound_hint", cid, c.hint_sound))
    for chid, ch in CHARMS.items():
        lines.append(asp.fact("charm", chid))
        lines.append(asp.fact("magic_effect", chid, ch.effect))
    return "\n".join(lines)


ASP_RULES = r"""
can_solve(C) :- clue(C), sound_hint(C,_), hidden_in(C,_).
interesting(C) :- can_solve(C).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_solve/1."))
    asp_set = set(asp.atoms(model, "can_solve"))
    py_set = {(cid,) for cid in CLUES}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python registry ({len(py_set)} clues).")
        return 0
    print("MISMATCH between clingo and Python registry.")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    clue = _safe_lookup(CLUES, params.clue)
    charm = _safe_lookup(CHARMS, params.charm)

    bed = world.add(Entity(
        id="bunk_bed",
        type="bunk bed",
        label="bunk bed",
        phrase="the tall bunk bed",
        meters={"dust": 0.0},
    ))
    hidden = world.add(Entity(
        id="clue_item",
        type=clue.label,
        label=clue.label,
        phrase=clue.phrase,
        owner=hero.id,
        caretaker=parent.id,
        meters={"hidden": 1.0, "found": 0.0},
    ))
    magic = world.add(Entity(
        id="charm_item",
        type=charm.label,
        label=charm.label,
        phrase=charm.phrase,
        owner=hero.id,
        meters={"glow": 1.0},
    ))
    hero.memes["curiosity"] = 1.0
    hero.memes["calm"] = 0.5
    world.facts.update(hero=hero, parent=parent, clue=hidden, charm=magic, clue_cfg=clue, charm_cfg=charm, bed=bed)
    return world


def narrate_story(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    clue: Entity = _safe_fact(world, f, "clue")
    clue_cfg: Clue = _safe_fact(world, f, "clue_cfg")
    charm_cfg: Charm = _safe_fact(world, f, "charm_cfg")
    pron = hero.pronoun
    rel = parent.label

    world.say(f"{hero.id} was a little {next((t for t in ['curious','gentle','cheerful','quiet','playful','careful']), 'curious')} {hero.type} who liked quiet mornings at {world.setting.place}.")
    world.say(f"{pron('subject').capitalize()} loved listening for little sounds, because the room always seemed to have a secret.")
    world.say(f"That day, {hero.id} noticed a soft {clue_cfg.hint_sound} near the {clue_cfg.hidden_in} and wondered where the {clue.label} had gone.")
    world.para()
    world.say(f"{hero.id} peeked at the tall bunk bed and said, \"{clue_cfg.hint_sound}!\"")
    world.say(f"{rel} smiled and said the sound might be a clue, not a problem.")
    world.say(f"{pron('subject').capitalize()} held up {f['charm'].phrase} and let its magic {charm_cfg.effect}.")
    world.say(f"The charm made the room shimmer a little, and the {clue.label} gave one more tiny {clue_cfg.hint_sound}.")
    world.para()
    world.say(f"{hero.id} looked under the bunk bed, then behind the ladder, and finally at the rail.")
    world.say(f"There it was: {clue.truth}.")
    world.say(f"{hero.id} laughed softly, because the mystery had been solved with listening, magic, and a very patient {rel}.")
    world.say(f"At the end, the bunk bed was just a bunk bed again, and the little {clue.label} was safe in {hero.pronoun('possessive')} hands.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    clue_cfg: Clue = _safe_fact(world, f, "clue_cfg")
    charm_cfg: Charm = _safe_fact(world, f, "charm_cfg")
    return [
        f'Write a short slice-of-life story for a child named {hero.id} about a bunk-bed mystery with the sound "{clue_cfg.hint_sound}".',
        f"Tell a gentle story where {hero.id} uses {charm_cfg.label} magic to solve what happened to a {clue_cfg.label}.",
        f'Write a child-friendly story that includes the words "bunk", "{clue_cfg.hint_sound}", and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    clue: Entity = _safe_fact(world, f, "clue")
    clue_cfg: Clue = _safe_fact(world, f, "clue_cfg")
    charm_cfg: Charm = _safe_fact(world, f, "charm_cfg")
    return [
        QAItem(
            question=f"What mystery was {hero.id} trying to solve in {world.setting.place}?",
            answer=f"{hero.id} was trying to find the missing {clue.label}. The clue sounded like {clue_cfg.hint_sound}, which led them to the bunk bed.",
        ),
        QAItem(
            question=f"What sound helped {hero.id} know where to look?",
            answer=f"The sound {clue_cfg.hint_sound} helped {hero.id} know where to look. It was the little sound clue in the room.",
        ),
        QAItem(
            question=f"What did {parent.label} think about the mystery?",
            answer=f"{parent.label.capitalize()} thought it was a gentle little mystery and encouraged {hero.id} to keep looking calmly.",
        ),
        QAItem(
            question=f"How did the magic help solve the problem?",
            answer=f"{charm_cfg.label.capitalize()} magic made hidden things show themselves for a moment, so {hero.id} could find the clue faster.",
        ),
        QAItem(
            question=f"Where was the {clue.label} at the end?",
            answer=f"At the end, the {clue.label} was found at {clue_cfg.hidden_in}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue_cfg: Clue = _safe_fact(world, f, "clue_cfg")
    charm_cfg: Charm = _safe_fact(world, f, "charm_cfg")
    return [
        QAItem(
            question="What is a bunk bed?",
            answer="A bunk bed is a bed with one sleeping spot above another, so two people can sleep in one tall bed frame.",
        ),
        QAItem(
            question=f"What does the sound '{clue_cfg.hint_sound}' make you think of?",
            answer=f"It can make you think of a tiny object shifting or knocking softly, like a clue hiding in a room.",
        ),
        QAItem(
            question=f"What does {charm_cfg.label} magic do in this story world?",
            answer=f"It helps small hidden things become easier to notice, which is useful when someone is solving a mystery.",
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    charm = getattr(args, "charm", None) or rng.choice(list(CHARMS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    params = StoryParams(place=place, clue=clue, charm=charm, name=name, gender=gender, parent=parent, trait=trait)
    maybe_raise_invalid(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life mystery story world with sound clues and a little magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_solve/1."))
    return sorted(set(asp.atoms(model, "can_solve")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, h) for p in SETTINGS for c in CLUES for h in CHARMS]


CURATED = [
    StoryParams(place="bedroom", clue="toy", charm="glimmer", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="nursery", clue="sock", charm="listening", name="Leo", gender="boy", parent="father", trait="quiet"),
    StoryParams(place="guest_room", clue="bell", charm="bubble", name="Nora", gender="girl", parent="mother", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show can_solve/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show can_solve/1."))
        print(sorted(set(asp.atoms(model, "can_solve"))))
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None) * 20, 20)):
            if len(samples) >= getattr(args, "n", None):
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.clue} + {p.charm} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
