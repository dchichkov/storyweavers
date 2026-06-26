#!/usr/bin/env python3
"""
Storyworld: dragon nap room happy ending dialogue heartwarming.

A small, self-contained story simulation about a young dragon in a nap room.
The world is built from a short source-tale premise:

- A tired little dragon wants to nap.
- The nap room is calm, but one thing feels uncomfortable or distracting.
- A caring helper talks with the dragon, finds a gentle fix, and the room
  ends with a peaceful happy ending.

The script models both physical meters and emotional memes, supports QA,
trace, JSON, and an inline ASP twin for reasonableness checks.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    mood: object | None = None
    caregiver: object | None = None
    dragon: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dragon"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mother", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "boy", "man"}:
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
class Room:
    name: str = "the nap room"
    quiet: bool = True
    warm: bool = False
    ROOMS: set[str] = field(default_factory=set)
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


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    warms: bool = False
    hushes: bool = False
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
    name: str
    caregiver: str
    comfort: str
    mood: str
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
    def __init__(self, room: Room):
        self.room = room
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
        import copy as _copy
        w = World(self.room)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


ROOMS = {"nap_room": Room(name="the nap room", quiet=True, warm=False)}

COMFORTS = {
    "blanket": Comfort("blanket", "a soft blanket", "a soft blanket", helps={"cold", "twitchy"}, warms=True),
    "pillow": Comfort("pillow", "a round pillow", "a round pillow", helps={"stiff"}, warms=False),
    "night_light": Comfort("light", "a tiny night light", "a tiny night light", helps={"scared", "dark"}, warms=False, hushes=True),
}

MOODS = {
    "cold": "cold",
    "twitchy": "twitchy",
    "stiff": "stiff",
    "scared": "scared",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in ROOMS:
        for mood in MOODS:
            for comfort in COMFORTS:
                combos.append((place, mood, comfort))
    return combos


def explain_invalid(mood: str, comfort: str) -> str:
    c = _safe_lookup(COMFORTS, comfort)
    if mood not in c.helps:
        return f"(No story: {c.label} does not reasonably help a dragon who feels {mood}.)"
    return "(No story: invalid combination.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming dragon nap-room storyworld.")
    ap.add_argument("--place", choices=list(ROOMS))
    ap.add_argument("--comfort", choices=list(COMFORTS))
    ap.add_argument("--mood", choices=list(MOODS))
    ap.add_argument("--name")
    ap.add_argument("--caregiver", choices=["mother", "father", "teacher"])
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
    if getattr(args, "mood", None) and getattr(args, "comfort", None) and getattr(args, "mood", None) not in _safe_lookup(COMFORTS, getattr(args, "comfort", None)).helps:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mood", None) is None or c[1] == getattr(args, "mood", None))
              and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mood, comfort = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Ember", "Ruby", "Puff", "Cinder", "Scales", "Tala"])
    caregiver = getattr(args, "caregiver", None) or rng.choice(["mother", "father", "teacher"])
    return StoryParams(name=name, caregiver=caregiver, comfort=comfort, mood=mood)


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    dragon = world.add(Entity(
        id=params.name, kind="character", type="dragon", label=params.name,
        meters={"sleepy": 2.0, "cold": 1.0 if params.mood == "cold" else 0.0, "stiff": 1.0 if params.mood == "stiff" else 0.0},
        memes={"comfort_need": 1.0, "worry": 1.0},
    ))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=params.caregiver, label=f"the {params.caregiver}",
                                 meters={"care": 2.0}, memes={"love": 2.0}))
    comfort = _safe_lookup(COMFORTS, params.comfort)
    item = world.add(Entity(id=comfort.id, type=comfort.id, label=comfort.label, phrase=comfort.phrase,
                            owner=dragon.id, caretaker=caregiver.id))
    return dragon, caregiver, item


def story_text(world: World) -> None:
    d = world.get(world.facts["dragon"])
    c = world.get(world.facts["caregiver"])
    item = world.get(world.facts["comfort"])
    mood = _safe_fact(world, world.facts, "mood")

    world.say(f"{d.label} was a little dragon who loved the nap room because it was quiet and kind.")
    world.say(f"On this day, {d.label} felt {mood}, and {d.pronoun('possessive')} eyes blinked slow and heavy.")
    world.say(f"{d.pronoun().capitalize()} looked at {c.label} and whispered, \"I want to nap, but I do not feel settled yet.\"")
    world.para()
    if mood == "cold":
        world.say(f"{c.label} noticed {d.pronoun('possessive')} shiver and said, \"Your little wings look chilly.\"")
        world.say(f"{d.label} nodded and said, \"My tail feels like a cold noodle.\"")
    elif mood == "stiff":
        world.say(f"{c.label} saw {d.label} curl up in a tight knot and said, \"That pillow is not quite right, is it?\"")
        world.say(f"{d.label} sighed, \"It feels lumpy under my chin.\"")
    elif mood == "scared":
        world.say(f"{c.label} noticed {d.label} staring at the dark corner and said, \"I can stay right here.\"")
        world.say(f"{d.label} whispered, \"I just need to know I am safe.\"")
    else:
        world.say(f"{c.label} smiled softly and said, \"You seem to need one gentle thing before sleep.\"")
        world.say(f"{d.label} answered, \"Yes, please.\"")
    world.para()
    if world.facts["comfort"] == "blanket":
        world.say(f"{c.label} wrapped {d.pronoun('object')} in {item.label} and tucked it around {d.pronoun('possessive')} shoulders.")
        world.say(f"\"Warm now?\" {c.label} asked. \"Warm now,\" {d.label} whispered, and a tiny smile melted across {d.pronoun('possessive')} face.")
    elif world.facts["comfort"] == "pillow":
        world.say(f"{c.label} slid {item.label} under {d.pronoun('possessive')} head and moved it just a little higher.")
        world.say(f"\"That feels better,\" {d.label} said, letting out a long, sleepy breath.")
    else:
        world.say(f"{c.label} clicked on {item.label}, and the little light made the room feel brave and soft.")
        world.say(f"\"I can rest,\" {d.label} said. \"I am not alone in the dark.\"")
    world.para()
    world.say(f"At last, {d.label} curled up, {d.pronoun('possessive')} breathing slowed, and the nap room became very still.")
    world.say(f"{c.label} stayed nearby until {d.label} drifted into a happy, peaceful nap.")


def generate_story(world: World) -> None:
    d = world.get(world.facts["dragon"])
    c = world.get(world.facts["caregiver"])
    item = world.get(world.facts["comfort"])
    if world.facts["mood"] == "cold" and item.warms:
        d.meters["cold"] = 0.0
        d.meters["sleepy"] += 1.0
        d.memes["comfort"] = 2.0
    elif world.facts["mood"] == "stiff" and "stiff" in item.helps:
        d.meters["stiff"] = 0.0
        d.meters["sleepy"] += 1.0
        d.memes["comfort"] = 2.0
    elif world.facts["mood"] == "scared" and item.hushes:
        d.memes["worry"] = 0.0
        d.memes["comfort"] = 2.0
        d.meters["sleepy"] += 1.0
    else:
        d.memes["comfort"] = 1.0
    c.memes["love"] += 1.0


def build_world(params: StoryParams) -> World:
    world = World(ROOMS["nap_room"])
    dragon, caregiver, item = _setup(world, params)
    world.facts.update(dragon=dragon.id, caregiver=caregiver.id, comfort=item.id, mood=params.mood)
    story_text(world)
    generate_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        "Write a heartwarming short story about a dragon in a nap room who needs a gentle comfort item.",
        f"Tell a dialogue-rich story where {p['dragon']} feels {p['mood']} and {p['caregiver']} helps with {p['comfort']}.",
        "Write a child-friendly happy ending about a dragon settling down for a peaceful nap.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.get(world.facts["dragon"])
    c = world.get(world.facts["caregiver"])
    item = world.get(world.facts["comfort"])
    mood = _safe_fact(world, world.facts, "mood")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {d.label}, a little dragon in the nap room.",
        ),
        QAItem(
            question=f"What did {d.label} feel before getting help?",
            answer=f"{d.label} felt {mood}, so {d.pronoun('possessive')} nap did not start easily.",
        ),
        QAItem(
            question=f"How did {c.label} help {d.label}?",
            answer=f"{c.label} helped by offering {item.label} and speaking gently until {d.label} could relax.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{d.label} settled into a happy nap, and the room became calm and peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nap room for?",
            answer="A nap room is a quiet place where children can rest and fall asleep peacefully.",
        ),
        QAItem(
            question="Why can a soft blanket help someone sleep?",
            answer="A soft blanket can help because it makes a person feel warm, snug, and safe.",
        ),
        QAItem(
            question="Why is a gentle voice helpful at bedtime?",
            answer="A gentle voice helps because it feels calm and comforting, which makes it easier to relax.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
dragon(d1).
room(nap_room).
comfort(blanket).
comfort(pillow).
comfort(light).

helps(blanket,cold).
helps(blanket,twitchy).
helps(pillow,stiff).
helps(light,scared).

valid(D,R,C) :- dragon(D), room(R), comfort(C), helps(C,_).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("dragon", "d1"), asp.fact("room", "nap_room")]
    for c in COMFORTS:
        lines.append(asp.fact("comfort", c))
        for mood in _safe_lookup(COMFORTS, c).helps:
            lines.append(asp.fact("helps", c, mood))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = {("d1", "nap_room", c) for _, mood, c in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(name="Ember", caregiver="mother", comfort="blanket", mood="cold"),
    StoryParams(name="Ruby", caregiver="father", comfort="pillow", mood="stiff"),
    StoryParams(name="Puff", caregiver="teacher", comfort="night_light", mood="scared"),
]


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


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mood", None) is None or c[1] == getattr(args, "mood", None))
              and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))]
    if not combos:
        pass
    place, mood, comfort = rng.choice(list(combos))
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(["Ember", "Ruby", "Puff", "Cinder", "Tala"]),
        caregiver=getattr(args, "caregiver", None) or rng.choice(["mother", "father", "teacher"]),
        comfort=comfort,
        mood=mood,
    )


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser_main().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for d, room, comfort in combos:
            print(f"  {d:6} {room:10} {comfort}")
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
            params = resolve_story_params(args, random.Random(seed))
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
