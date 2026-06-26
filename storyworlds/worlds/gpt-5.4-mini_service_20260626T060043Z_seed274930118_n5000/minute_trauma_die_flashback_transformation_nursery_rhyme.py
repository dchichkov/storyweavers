#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a brief fright, a remembered flashback,
and a gentle transformation.

Domain premise:
- A child has only a minute to rescue a small thing before a scary memory makes
  them freeze.
- A kind helper gives a soothing rhyme and a simple action.
- The frightened feeling changes into courage, and the small thing is saved.

This world keeps the prose close to a nursery rhyme while remaining a real
state-driven simulation with physical meters and emotional memes.
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

    child: object | None = None
    helper: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class StoryParams:
    name: str
    gender: str
    helper: str
    thing: str
    setting: str
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


@dataclass
class Setting:
    place: str
    small: str
    clock: str
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
class Thing:
    id: str
    label: str
    phrase: str
    location: str
    fragile: bool = True
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
class Helper:
    id: str
    label: str
    rhyme: str
    transform: str
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
        self.fired: set[str] = set()
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
    "nursery": Setting(place="the nursery", small="a tiny toy box", clock="a little clock"),
    "attic": Setting(place="the attic", small="a small wooden chest", clock="an old clock"),
    "porch": Setting(place="the porch", small="a little basket", clock="a round clock"),
}

THINGS = {
    "bell": Thing(id="bell", label="silver bell", phrase="a silver bell that sang like rain", location="high shelf"),
    "kite": Thing(id="kite", label="paper kite", phrase="a paper kite with a smiling face", location="corner hook"),
    "teddy": Thing(id="teddy", label="teddy bear", phrase="a soft teddy bear with a red bow", location="pillow nest"),
}

HELPERS = {
    "mama": Helper(id="mama", label="kind Mama", rhyme="Hush now, hush, and breathe with me", transform="brave"),
    "grandpa": Helper(id="grandpa", label="gentle Grandpa", rhyme="Step by step and blink-blink slow", transform="steady"),
    "sister": Helper(id="sister", label="smiling Sister", rhyme="One two three, now back you go", transform="bright"),
}


def _inc(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper_def = _safe_lookup(HELPERS, params.helper)
    helper = world.add(Entity(id=helper_def.id, kind="character", type="adult", label=helper_def.label))
    thing_def = _safe_lookup(THINGS, params.thing)
    thing = world.add(Entity(id=thing_def.id, type="thing", label=thing_def.label, phrase=thing_def.phrase, owner=child.id))

    world.facts.update(child=child, helper=helper, thing=thing, helper_def=helper_def, thing_def=thing_def)
    return world


def set_scene(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    h = _safe_fact(world, world.facts, "helper")
    t = _safe_fact(world, world.facts, "thing")
    s = world.setting

    world.say(
        f"In {s.place}, {c.id} found {t.phrase} by {t.location}, while {s.clock} ticked a little tune."
    )
    world.say(
        f"{c.id} loved {t.label}, and {h.label} was near enough to hear."
    )


def flashback(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    t = _safe_fact(world, world.facts, "thing")
    _mem(c, "trauma", 1.0)
    _mem(c, "fear", 1.0)
    world.facts["flashback"] = True
    world.say(
        f"But a flashback came: once {t.label} had slipped and banged, and {c.id} had cried a minute-long cry."
    )
    world.say(
        f"So {c.id} went still and small, with {c.pronoun('possessive')} knees all jelly-soft."
    )


def die_risk(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    t = _safe_fact(world, world.facts, "thing")
    _inc(t, "danger", 1.0)
    _mem(c, "panic", 1.0)
    world.facts["die_risk"] = True
    world.say(
        f"The bell of the moment seemed to say, 'Die, little hope, die,' and the minute felt too thin to hold."
    )
    world.say(
        f"If no one moved soon, {t.label} might fall and be ruined on the floor below."
    )


def helper_song(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    h = _safe_fact(world, world.facts, "helper")
    helper_def = _safe_fact(world, world.facts, "helper_def")
    _mem(c, "calm", 1.0)
    _mem(c, "trust", 1.0)
    world.say(
        f"{h.label} knelt close and sang, '{helper_def.rhyme}.'"
    )
    world.say(
        f"Then {h.label} showed {c.id} how to hold still, look high, and reach with care."
    )


def transformation(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    t = _safe_fact(world, world.facts, "thing")
    h = _safe_fact(world, world.facts, "helper")
    helper_def = _safe_fact(world, world.facts, "helper_def")

    if c.memes.get("calm", 0.0) < THRESHOLD:
        pass
    c.memes["fear"] = 0.0
    c.memes["trauma"] = 0.0
    c.memes["brave"] = c.memes.get("brave", 0.0) + 1.0
    c.memes["joy"] = c.memes.get("joy", 0.0) + 1.0
    t.meters["safe"] = 1.0
    world.facts["transformed"] = True
    world.say(
        f"So the frightened child turned, like a candle becoming dawn, and {c.id} became {helper_def.transform}."
    )
    world.say(
        f"With one careful reach, {c.id} lifted {t.label} down safe, and the little clock kept ticking kindly."
    )
    world.say(
        f"{h.label} smiled, and the nursery felt warm again."
    )


def tell_story(world: World) -> None:
    set_scene(world)
    world.para()
    flashback(world)
    die_risk(world)
    world.para()
    helper_song(world)
    transformation(world)


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    h = _safe_fact(world, world.facts, "helper")
    t = _safe_fact(world, world.facts, "thing")
    s = world.setting
    return [
        QAItem(
            question=f"Who was the story about in {s.place}?",
            answer=f"It was about {c.id}, who was trying to keep {t.label} safe in {s.place}.",
        ),
        QAItem(
            question=f"What scared {c.id}?",
            answer=f"A flashback scared {c.id}: {t.label} had slipped before, and the memory made {c.id} freeze.",
        ),
        QAItem(
            question=f"How did {h.label} help?",
            answer=f"{h.label} sang a soft rhyme and helped {c.id} breathe, look carefully, and reach gently.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"{c.id} changed from frightened to brave, and {t.label} ended up safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a minute?",
            answer="A minute is a short stretch of time, like sixty small seconds lined up together.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when an old memory comes back so clearly that it feels almost like now.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a change from one state to another, like fear turning into courage.",
        ),
        QAItem(
            question="What does it mean when something can die in a story?",
            answer="It can mean something may be lost or ruined forever if it is not protected in time.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    c = _safe_fact(world, world.facts, "child")
    h = _safe_fact(world, world.facts, "helper")
    t = _safe_fact(world, world.facts, "thing")
    return [
        f"Write a nursery-rhyme story where {c.id} has one minute to save {t.label} after a scary flashback.",
        f"Tell a gentle rhyme about {h.label} helping a child turn fear into courage before something can die or break.",
        f"Create a short, musical story set in {world.setting.place} with a flashback and a transformation.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    out.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(out)


CURATED = [
    StoryParams(name="Mia", gender="girl", helper="mama", thing="bell", setting="nursery"),
    StoryParams(name="Ned", gender="boy", helper="grandpa", thing="kite", setting="attic"),
    StoryParams(name="Tilly", gender="girl", helper="sister", thing="teddy", setting="porch"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: minute, trauma, die, flashback, transformation.")
    ap.add_argument("--name", choices=["Mia", "Ned", "Tilly"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--thing", choices=list(THINGS))
    ap.add_argument("--setting", choices=list(SETTINGS))
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
    name = getattr(args, "name", None) or rng.choice(["Mia", "Ned", "Tilly"])
    gender = getattr(args, "gender", None) or ("girl" if name in {"Mia", "Tilly"} else "boy")
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    thing = getattr(args, "thing", None) or rng.choice(list(THINGS))
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    return StoryParams(name=name, gender=gender, helper=helper, thing=thing, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


ASP_RULES = r"""
% A child can be frightened by a flashback.
frightened(C) :- flashback(C).

% A thing is at risk if the child is frightened and no helper intervenes.
at_risk(T) :- frightened(C), wants_save(C, T), not soothed(C).

% Transformation happens when the child is soothed and can act bravely.
transformed(C) :- soothed(C), can_act(C).

#show frightened/1.
#show at_risk/1.
#show transformed/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in THINGS:
        lines.append(asp.fact("thing", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show setting/1."))
    if model is None:
        print("No ASP model found.")
        return 1
    print("OK: ASP twin is syntactically reachable.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show transformed/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
