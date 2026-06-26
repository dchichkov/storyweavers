#!/usr/bin/env python3
"""
storyworlds/worlds/mile_performance_night_sharing_detective_story.py
====================================================================

A small detective-story world about a night performance, a shared clue, and a
mile-long walk that helps solve the case.

Seed premise:
- A child detective notices something strange at a night performance.
- A clue gets shared instead of hidden.
- The evidence points to a mile marker, and the story resolves when the truth
  is pieced together and the missing item is returned.

This world keeps the prose child-facing, concrete, and state-driven, with a
single clear turn: sharing the right clue changes what the detective can prove.
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
    held_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    box: object | None = None
    friend: object | None = None
    hero: object | None = None
    note: object | None = None
    suspect_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    night: bool = True
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
class Clue:
    id: str
    label: str
    phrase: str
    truth: str
    reveals: str
    topic: str
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
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    tell: str
    owns: str
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
class StoryParams:
    place: str
    clue: str
    suspect: str
    hero_name: str
    hero_type: str
    friend_name: str
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "the little theater": Setting(place="the little theater", night=True, affords={"performance"}),
    "the boardwalk": Setting(place="the boardwalk", night=True, affords={"performance", "mile"}),
    "the museum hall": Setting(place="the museum hall", night=True, affords={"performance"}),
}

CLUES = {
    "program": Clue(
        id="program",
        label="show program",
        phrase="a folded show program with a torn corner",
        truth="the torn corner matched the missing page from the safe",
        reveals="it was carried by someone who walked past the mile marker",
        topic="performance",
    ),
    "lantern": Clue(
        id="lantern",
        label="paper lantern",
        phrase="a paper lantern with blue ribbon",
        truth="blue ribbon fibers were stuck to the missing box",
        reveals="it came from the stage cart",
        topic="night",
    ),
    "ticket": Clue(
        id="ticket",
        label="ticket stub",
        phrase="a ticket stub with a smear of jam",
        truth="the jam matched the snack basket beside the stage",
        reveals="someone had hidden the basket near the mile sign",
        topic="mile",
    ),
}

SUSPECTS = {
    "stagehand": Suspect(
        id="stagehand",
        label="the stagehand",
        type="man",
        alibi="he said he was fixing a curtain",
        tell="his gloves were dusty with rope lint",
        owns="the lantern cart",
    ),
    "vendor": Suspect(
        id="vendor",
        label="the vendor",
        type="woman",
        alibi="she said she was serving lemonade",
        tell="her apron had a pocket full of ribbon scraps",
        owns="the snack basket",
    ),
    "actor": Suspect(
        id="actor",
        label="the actor",
        type="man",
        alibi="he said he was on stage the whole time",
        tell="his coat had a fresh tear near the cuff",
        owns="the show program",
    ),
}

HERO_NAMES = ["Mina", "Noah", "Lena", "Toby", "Iris", "Theo", "June", "Owen"]
FRIEND_NAMES = ["Pip", "Milo", "Sage", "Nia", "Rae", "Bea"]


# ---------------------------------------------------------------------------
# Detective-story logic
# ---------------------------------------------------------------------------
def is_reasonable(place: Setting, clue: Clue, suspect: Suspect) -> bool:
    if place.place == "the museum hall" and clue.id == "ticket":
        return False
    return clue.topic in place.affords or clue.topic in {"night", "mile", "performance"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for sus_id, suspect in SUSPECTS.items():
                if is_reasonable(setting, clue, suspect):
                    out.append((place_id, clue_id, sus_id))
    return out


def choose_name(rng: random.Random, hero_type: str) -> str:
    return rng.choice(HERO_NAMES)


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    clue = _safe_lookup(CLUES, params.clue)
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label="detective"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="friend", label="friend"))
    box = world.add(Entity(id="missing_box", type="thing", label="music box", phrase="a small music box", owner=suspect.id))
    note = world.add(Entity(id="note", type="thing", label="note", phrase=clue.phrase, owner=hero.id))
    suspect_ent = world.add(Entity(id=suspect.id, kind="character", type=suspect.type, label=suspect.label_word))

    world.facts.update(
        hero=hero,
        friend=friend,
        clue=clue,
        suspect=suspect_ent,
        box=box,
        note=note,
        place=setting,
    )
    return world


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    clue: Clue = _safe_fact(world, f, "clue")
    suspect: Entity = _safe_fact(world, f, "suspect")
    place: Setting = _safe_fact(world, f, "place")

    world.say(f"{hero.id} was a small detective who liked quiet questions and neat answers.")
    world.say(f"That night, {hero.id} and {friend.id} went to {place.place} for a performance.")
    world.say(f"The lights were low, the music was soft, and everyone watched the stage.")
    world.say(f"Then {hero.id} noticed {clue.phrase} near a chair, and {hero.id} picked it up.")

    world.para()
    world.say(f"{suspect.label_word.capitalize()} smiled too quickly and said, '{suspect_ent_alibi(suspect)}'")
    world.say(f"But {hero.id} saw {suspect.tell}. That made the detective suspicious.")
    world.say(f"{friend.id} did not hide the clue. Instead, {friend.id} shared it with {hero.id}.")
    world.say(f"That small sharing helped {hero.id} compare the clue with the stage, the seats, and the hall.")

    world.para()
    world.say(f"The clue pointed to the mile marker outside, where the missing music box had been tucked away.")
    world.say(f"{hero.id} followed the trail, found the box, and proved that {suspect.label_word} had carried it off.")
    world.say(f"In the end, the box was returned before the performance ended, and the night felt bright again.")

    world.facts["solved"] = True
    world.facts["shared"] = True
    world.facts["mile"] = True


def suspect_ent_alibi(suspect: Entity) -> str:
    mapping = {
        "stagehand": "I was fixing a curtain.",
        "vendor": "I was serving lemonade.",
        "actor": "I was on stage the whole time.",
    }
    return mapping.get(suspect.id, "I was somewhere else.")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    clue: Clue = _safe_fact(world, f, "clue")
    return [
        f'Write a short detective story for a child about a night performance, a shared clue, and a mile marker.',
        f"Tell a simple mystery where {hero.id} shares {clue.label} with a friend and solves what happened at night.",
        f'Write a story that includes the words "mile", "performance", and "night" and ends with the missing item found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    clue: Clue = _safe_fact(world, f, "clue")
    suspect: Entity = _safe_fact(world, f, "suspect")
    place: Setting = _safe_fact(world, f, "place")

    return [
        QAItem(
            question=f"Where did {hero.id} go to watch the performance?",
            answer=f"{hero.id} went to {place.place} at night to watch the performance.",
        ),
        QAItem(
            question=f"What clue did {friend.id} share with {hero.id}?",
            answer=f"{friend.id} shared {clue.phrase}, which helped the detective think more carefully.",
        ),
        QAItem(
            question=f"What did the clue help {hero.id} prove?",
            answer=f"It helped {hero.id} prove that {suspect.label_word} had moved the missing music box.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The missing music box was found near the mile marker and returned before the night was over.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "performance": [
        QAItem(
            question="What is a performance?",
            answer="A performance is a show where people sing, act, dance, or play music for others to watch.",
        )
    ],
    "night": [
        QAItem(
            question="What is night?",
            answer="Night is the dark part of the day when the sun has gone down and people can see stars or lights.",
        )
    ],
    "mile": [
        QAItem(
            question="What is a mile marker?",
            answer="A mile marker is a sign that helps people know how far they have traveled.",
        )
    ],
    "sharing": [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, see, or know about something instead of keeping it all to yourself.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["sharing"])
    out.extend(WORLD_KNOWLEDGE["performance"])
    out.extend(WORLD_KNOWLEDGE["night"])
    out.extend(WORLD_KNOWLEDGE["mile"])
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {e.type:8} {' '.join(bits)}")
    lines.append(f"  solved={world.facts.get('solved', False)} shared={world.facts.get('shared', False)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.

valid(Place, Clue, Suspect) :- setting(Place), clue(Clue), suspect(Suspect), reasonable(Place, Clue, Suspect).

reasonable(Place, Clue, Suspect) :- setting(Place), clue(Clue), suspect(Suspect),
                                    clue_topic(Clue, Topic), place_affords(Place, Topic).

reasonable(Place, Clue, Suspect) :- setting(Place), clue(Clue), suspect(Suspect),
                                    clue_topic(Clue, Topic), Topic = night.

reasonable(Place, Clue, Suspect) :- setting(Place), clue(Clue), suspect(Suspect),
                                    clue_topic(Clue, Topic), Topic = mile.

reasonable(Place, Clue, Suspect) :- setting(Place), clue(Clue), suspect(Suspect),
                                    clue_topic(Clue, Topic), Topic = performance.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for topic in sorted(setting.affords):
            lines.append(asp.fact("place_affords", pid, topic))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_topic", cid, clue.topic))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small detective story world about night, performance, mile, and sharing."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "clue", None):
        combos = [c for c in combos if c[1] == getattr(args, "clue", None)]
    if getattr(args, "suspect", None):
        combos = [c for c in combos if c[2] == getattr(args, "suspect", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, suspect = rng.choice(list(combos))
    hero_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or choose_name(rng, hero_type)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        clue=clue,
        suspect=suspect,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
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
    StoryParams(place="the little theater", clue="program", suspect="actor", hero_name="Mina", hero_type="girl", friend_name="Pip"),
    StoryParams(place="the boardwalk", clue="ticket", suspect="vendor", hero_name="Noah", hero_type="boy", friend_name="Rae"),
    StoryParams(place="the boardwalk", clue="lantern", suspect="stagehand", hero_name="Iris", hero_type="girl", friend_name="Sage"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, clue, suspect) combos:\n")
        for place, clue, suspect in triples:
            print(f"  {place:18} {clue:10} {suspect}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
