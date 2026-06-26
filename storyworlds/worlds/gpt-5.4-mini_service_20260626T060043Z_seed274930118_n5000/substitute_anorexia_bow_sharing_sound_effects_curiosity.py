#!/usr/bin/env python3
"""
storyworlds/worlds/substitute_anorexia_bow_sharing_sound_effects_curiosity.py
=============================================================================

A standalone comedy-leaning story world about a substitute day, a curious class,
a bow-shaped surprise, and a very silly sound-effects box.

Seed tale idea:
---
A class arrived to find a substitute teacher at the front of the room. On the
desk sat a shiny bow, a sharing basket, and a card with a strange long word:
"anorexia." The children became curious at once. They wanted to know what the
word meant, what the bow was for, and why the substitute kept making tiny sound
effects instead of simply saying "good morning."

The class tried to share the sound-effects cards, but everyone wanted to be the
one to pick the loudest one. After a few comic squeaks, the substitute teacher
showed them a gentler rule: share the cards one at a time, take turns with the
bow, and use curiosity to ask questions before the whole room turned into a
noisy noodle factory.

Causal state updates:
---
    curiosity about a strange word   -> child.memes["curiosity"] += 1
    shared prop moved hand-to-hand    -> owner mismatch may create mild tension
    sound-effects card used           -> room.meters["noise"] += 1, child.joy += 1
    turn-taking compromise accepted   -> conflict clears, sharing rises, laughter rises
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
# World model
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    prop_ent: object | None = None
    substitute: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the classroom"
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
class Prop:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    noisy: bool = False
    shareable: bool = True
    plural: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
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


SETTINGS = {
    "classroom": Setting(place="the classroom", affords={"sharing", "sound_effects", "curiosity"}),
    "library_corner": Setting(place="the library corner", affords={"sharing", "curiosity"}),
    "music_room": Setting(place="the music room", affords={"sound_effects", "sharing", "curiosity"}),
}

PROPS = {
    "bow": Prop(
        id="bow",
        label="a shiny bow",
        phrase="a shiny bow with ribbon tails",
        tags={"bow", "sharing"},
        shareable=True,
    ),
    "cards": Prop(
        id="cards",
        label="sound-effects cards",
        phrase="a stack of sound-effects cards",
        tags={"sound effects", "sound_effects"},
        noisy=True,
        shareable=True,
        plural=True,
    ),
    "wordcard": Prop(
        id="wordcard",
        label="a strange word card",
        phrase="a card with a very long word on it",
        tags={"anorexia", "curiosity"},
        shareable=True,
    ),
}

NAMES = ["Maya", "Nina", "Leo", "Pip", "Tia", "Owen", "Zara", "Ben", "Ivy", "Noah"]
TRAITS = ["curious", "bouncy", "sensible", "silly", "cheerful", "tiny"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, prop_id: str) -> bool:
    prop = _safe_lookup(PROPS, prop_id)
    if "curiosity" in prop.tags:
        return True
    if place == "library_corner" and prop.noisy:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for prop_id in PROPS:
            if valid_combo(place, prop_id):
                out.append((place, prop_id))
    return out


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, Prop) :- setting(Place), prop(Prop), allowed(Place, Prop).
curiosity_prop(Prop) :- prop(Prop), tag(Prop, curiosity).
allowed(Place, Prop) :- curiosity_prop(Prop).
allowed(Place, Prop) :- setting(Place), prop(Prop), not noisy_prop(Prop).
noisy_prop(Prop) :- tag(Prop, sound_effects).
invalid(Place, Prop) :- setting(Place), prop(Prop), noisy_prop(Prop), place(Place, library_corner).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.noisy:
            lines.append(asp.fact("noisy_prop", pid))
        if p.shareable:
            lines.append(asp.fact("shareable", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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
# Story logic
# ---------------------------------------------------------------------------
def _curiosity_boost(world: World, child: Entity, prop: Prop) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{child.id} leaned closer to the card, because {prop.label} looked like it was hiding a joke."
    )


def _sound_effect(world: World, child: Entity, prop: Prop) -> None:
    child.meters["noise"] = child.meters.get("noise", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"{child.id} pressed {(getattr(prop, 'it')() if callable(getattr(prop, 'it', None)) else getattr(prop, 'it', 'it'))} and made a tiny sound like 'boing!'"
    )


def _sharing_turn(world: World, child: Entity, prop: Prop, other: Entity) -> None:
    child.memes["sharing"] = child.memes.get("sharing", 0.0) + 1
    world.say(
        f"{child.id} passed {(getattr(prop, 'it')() if callable(getattr(prop, 'it', None)) else getattr(prop, 'it', 'it'))} to {other.id} and tried not to snatch it back."
    )


def _resolve(world: World, teacher: Entity, child: Entity, prop: Prop) -> None:
    child.memes["conflict"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"{teacher.id} smiled and said, 'Curiosity can take turns too.' "
        f"That sounded so wise that the room went quiet for exactly one silly second."
    )
    world.say(
        f"{child.id} laughed, shared {(getattr(prop, 'it')() if callable(getattr(prop, 'it', None)) else getattr(prop, 'it', 'it'))} properly, and the whole class made one final polite 'plink'."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, prop_id: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    substitute = world.add(Entity(id="Sub", kind="character", type="teacher", label="the substitute"))
    friend = world.add(Entity(id="Pal", kind="character", type="boy", label="the class helper"))

    prop = _safe_lookup(PROPS, prop_id)
    prop_ent = world.add(Entity(
        id=prop_id,
        kind="thing",
        type=prop_id,
        label=prop.label,
        phrase=prop.phrase,
        plural=prop.plural,
        owner="Sub" if prop_id != "bow" else hero.id,
    ))

    # Act 1
    world.say(
        f"On a bright school morning, {hero.id} found {setting.place} full of surprises, "
        f"because {substitute.label} had come in as a substitute."
    )
    world.say(
        f"On the desk sat {prop.phrase}, and beside it was a card with the strange word 'anorexia' printed very neatly."
    )
    world.say(
        f"{hero.id} was so {trait} that {hero.pronoun('subject')} wanted to inspect everything twice."
    )

    # Act 2
    world.para()
    _curiosity_boost(world, hero, prop)
    world.say(
        f"{hero.id} asked, 'Why does the bow look like it is ready for a parade, and why does the word card look so serious?'"
    )
    if prop_id == "cards":
        _sound_effect(world, hero, prop)
        _sound_effect(world, friend, prop)
        world.say(
            f"Then {friend.id} wanted a turn, and suddenly the room was full of squeaks, peeps, and one heroic 'meep'."
        )
    else:
        _sharing_turn(world, hero, prop, friend)
        world.say(
            f"The substitute said they would share the bow with the whole class, one careful turn at a time."
        )
    hero.memes["conflict"] = 1.0

    # Act 3
    world.para()
    _resolve(world, substitute, hero, prop_ent)
    world.say(
        f"By the end, the bow still sparkled, the sound-effects card stayed in one piece, and the strange word card had become a clue instead of a mystery."
    )

    world.facts.update(
        hero=hero,
        substitute=substitute,
        friend=friend,
        prop=prop_ent,
        prop_cfg=prop,
        setting=setting,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prop = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prop_cfg")
    return [
        f'Write a short funny story for a child about a substitute, curiosity, and a "{prop.label}" in a classroom.',
        f"Tell a comedy story where {hero.id} wants to inspect {prop.phrase} while a substitute teacher keeps the class calm.",
        f'Write a simple school story that includes the words "substitute", "anorexia", and "{prop.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sub, prop = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "substitute"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prop")
    prop_cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prop_cfg")
    trait = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trait")
    qas = [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {hero.id}, a little {trait} child, and {sub.label}, the substitute who had a funny surprise ready.",
        ),
        QAItem(
            question=f"What did {hero.id} notice on the desk?",
            answer=f"{hero.id} noticed {prop_cfg.phrase} and a word card with the word 'anorexia' on it.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep looking at {prop.label}?",
            answer=f"{hero.id} was curious and wanted to see what {prop.label} could do, because it looked like it might make a funny sound or start a parade.",
        ),
    ]
    if prop_cfg.noisy:
        qas.append(
            QAItem(
                question=f"What happened when the sound-effects cards were used?",
                answer=f"The room filled with little noises like 'boing' and 'meep', and everyone got very cheerful very quickly.",
            )
        )
    qas.append(
        QAItem(
            question=f"How did the substitute solve the problem?",
            answer=f"{sub.label} told the class to take turns and share carefully, so {hero.id} could enjoy the surprise without turning the room into a noise contest.",
        )
    )
    return qas


KNOWLEDGE = {
    "substitute": [(
        "What is a substitute teacher?",
        "A substitute teacher is an adult who teaches the class for a day when the regular teacher is away.",
    )],
    "curiosity": [(
        "What does curiosity mean?",
        "Curiosity means wanting to know more about something new or surprising.",
    )],
    "sharing": [(
        "What does sharing mean?",
        "Sharing means letting other people use something too, often by taking turns.",
    )],
    "sound effects": [(
        "What are sound effects?",
        "Sound effects are extra noises, like boings or pops, that make a story or game more fun.",
    )],
    "bow": [(
        "What is a bow?",
        "A bow can be a ribbon tied into a pretty shape, often used on gifts or clothes.",
    )],
    "anorexia": [(
        "What is a word card?",
        "A word card is a card with a word written on it, which can help children read, spell, or learn new vocabulary.",
    )],
}
KNOWLEDGE_ORDER = ["substitute", "curiosity", "sharing", "sound effects", "bow", "anorexia"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "prop_cfg").tags) | {"substitute"}
    if _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "prop_cfg").noisy:
        tags.add("sound effects")
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generate / emit / CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    prop: str
    name: str
    gender: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


CURATED = [
    StoryParams(place="classroom", prop="bow", name="Maya", gender="girl", trait="curious"),
    StoryParams(place="music_room", prop="cards", name="Leo", gender="boy", trait="silly"),
    StoryParams(place="classroom", prop="wordcard", name="Ivy", gender="girl", trait="cheerful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld: a substitute day with sharing, sound effects, and curiosity."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if getattr(args, "place", None) and getattr(args, "prop", None) and not valid_combo(getattr(args, "place", None), getattr(args, "prop", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        (place, prop_id)
        for place, prop_id in valid_combos()
        if (getattr(args, "place", None) is None or place == getattr(args, "place", None))
        and (getattr(args, "prop", None) is None or prop_id == getattr(args, "prop", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prop_id = rng.choice(list(combos))
    prop = _safe_lookup(PROPS, prop_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, prop=prop_id, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.name, params.gender, params.prop, params.trait)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, prop) combos:\n")
        for place, prop in combos:
            print(f"  {place:15} {prop}")
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
            header = f"### {p.name}: {p.prop} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
