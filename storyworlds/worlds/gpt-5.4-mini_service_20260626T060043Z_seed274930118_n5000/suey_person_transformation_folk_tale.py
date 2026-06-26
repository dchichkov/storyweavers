#!/usr/bin/env python3
"""
storyworlds/worlds/suey_person_transformation_folk_tale.py
=========================================================

A small folk-tale storyworld about a person, a strange suey transformation,
and the kind of change that can only be undone by a better heart.

This world keeps a classical folk-tale shape:
- a person wants something
- a warning or folly leads to a transformation
- a humble turn of feeling changes the path
- the ending proves the person is different

The seed words are "suey" and "person"; the core feature is Transformation.
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
    form: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    trait: object | None = None
    elder: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"woman", "girl", "mother", "queen", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"man", "boy", "father", "king"}:
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
    kind: str
    has_well: bool = False
    has_market: bool = False
    has_woods: bool = False
    has_hall: bool = False
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
class Curse:
    id: str
    trigger: str
    form: str
    body: str
    sound: str
    undo_hint: str
    closes: str
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
class StoryParams:
    setting: str
    curse: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    days: int = 0

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
        clone.days = self.days
        return clone
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
    "village": Setting(place="the village green", kind="village", has_market=True),
    "woods": Setting(place="the old woods", kind="woods", has_woods=True, has_well=True),
    "cottage": Setting(place="the little cottage", kind="cottage", has_well=True),
    "hall": Setting(place="the bright hall", kind="hall", has_hall=True, has_market=True),
}

CURSES = {
    "suey": Curse(
        id="suey",
        trigger="boasted and snatched from others",
        form="suey",
        body="a round pink snout, curly tail, and hooves",
        sound="squeal",
        undo_hint="share from the heart and make one true apology",
        closes="left behind a soft snort in the straw",
    ),
    "hog": Curse(
        id="hog",
        trigger="laughed at a poor traveler",
        form="hog",
        body="a bristly back, a muddy nose, and little ears",
        sound="grunt",
        undo_hint="wash the mud from their hands and offer a meal",
        closes="snuffled at the doorway",
    ),
}

TRAITS = ["proud", "stubborn", "curious", "kind", "swift", "cheerful"]
GIRL_NAMES = ["Mira", "Nina", "Elsa", "Mabel", "Lena", "Greta"]
BOY_NAMES = ["Oren", "Tomas", "Ivo", "Rafi", "Pavel", "Milo"]


def _make_person(name: str, gender: str, trait: str) -> Entity:
    return Entity(
        id=name,
        kind="character",
        type="girl" if gender == "girl" else "boy",
        label=name,
        trait=trait,
        meters={"body": 0.0, "dirty": 0.0, "smallness": 0.0},
        memes={"pride": 0.0, "fear": 0.0, "kindness": 0.0, "regret": 0.0, "hope": 0.0},
    )


def _make_other(eid: str, kind: str, label: str, type_: str) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, meters={}, memes={})


def build_story_state(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    curse = _safe_lookup(CURSES, params.curse)
    world = World(setting)

    hero = world.add(_make_person(params.name, params.gender, params.trait))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type="woman",
        label="the old woman",
        meters={"dignity": 1.0},
        memes={"knows": 1.0},
    ))
    if setting.has_market:
        market = world.add(_make_other("Market", "place", "the market", "market"))
        market.meters["crowd"] = 1.0
    if setting.has_well:
        world.add(_make_other("Well", "thing", "the well", "well"))
    if setting.has_woods:
        world.add(_make_other("Woods", "place", "the woods", "woods"))

    world.facts.update(hero=hero, elder=elder, curse=curse, setting=setting)

    hero.memes["pride"] += 1
    world.say(
        f"{hero.label} was a {params.trait} person who lived near {setting.place}. "
        f"{hero.pronoun('subject').capitalize()} liked to walk as if the whole lane belonged to {hero.pronoun('object')}."
    )
    world.say(
        f"At the edge of the road stood {elder.label}, who was older than the crows and quieter than the moss."
    )
    world.say(
        f"One day, {hero.label} saw a shining basket and wanted it at once. "
        f"{hero.pronoun('subject').capitalize()} reached too fast and forgot to ask."
    )

    world.para()
    world.say(
        f"{elder.label} looked up and said, 'A person who takes without asking may lose more than a basket.'"
    )
    world.say(
        f"But {hero.label} only huffed, and that little huff was enough for the old magic to wake."
    )
    hero.memes["pride"] += 1
    hero.memes["fear"] += 1
    hero.meters["body"] += 1
    hero.meters["smallness"] += 1
    hero.form = curse.form
    hero.type = curse.form
    hero.label = f"{params.name}, the {curse.form}"
    hero.meters["dirty"] += 1
    world.say(
        f"With a puff of wind and a twist of moonlight, {hero.pronoun('object')} changed into {curse.form}: "
        f"{curse.body}. {hero.pronoun('subject').capitalize()} let out a startled {curse.sound}."
    )

    world.para()
    if setting.has_woods:
        world.say(
            f"{hero.label} ran into {setting.place}, {hero.pronoun('subject')} but the new hooves made each step clumsy."
        )
    else:
        world.say(
            f"{hero.label} hid near the doorway, too embarrassed to show {hero.pronoun('possessive')} new shape."
        )
    world.say(
        f"The old woman did not laugh. She only said, 'Magic can make a person strange, but kindness can make one whole.'"
    )
    hero.memes["regret"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{hero.label} listened. {hero.pronoun('subject').capitalize()} brought the basket back, bowed low, and said sorry with a shaking voice."
    )
    world.say(
        f"That was the true work of the tale, because a sorry said plainly is often the first key in a folk story."
    )

    world.para()
    hero.memes["kindness"] += 1
    hero.memes["pride"] = 0.0
    hero.memes["fear"] = 0.0
    hero.meters["dirty"] = 0.0
    hero.form = "person"
    hero.type = "girl" if params.gender == "girl" else "boy"
    hero.label = params.name
    world.say(
        f"When {hero.label} helped the old woman carry water from the well, the snout faded and the curly tail went still."
    )
    world.say(
        f"Before sunset, {hero.label} stood again as a person, but now {hero.pronoun('subject')} walked with gentle feet and a soft face."
    )
    world.say(
        f"By nightfall, the lane was calm, the basket was returned, and the only trace of the spell was {curse.closes}."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    curse = _safe_fact(world, f, "curse")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a folk tale for a young child about a {hero.type} who becomes a {curse.form} in {setting.place}.',
        f"Tell a short transformation story where {hero.label} learns that pride can turn a person into a {curse.form}.",
        f'Write a gentle story using the word "suey" and ending with a person becoming kind again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    curse = _safe_fact(world, f, "curse")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a {hero.type} who lives near {setting.place}.",
        ),
        QAItem(
            question=f"What happened after {hero.label} acted too proudly?",
            answer=f"{hero.label} was changed into a {curse.form} with {curse.body}.",
        ),
        QAItem(
            question=f"How did {hero.label} change back?",
            answer=(
                f"{hero.label} apologized, returned what was taken, and helped the old woman. "
                f"That kindness broke the spell and made {hero.label} a person again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    curse = _safe_fact(world, f, "curse")
    return [
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old story that people tell again and again, often about magic, cleverness, and lessons.",
        ),
        QAItem(
            question="What can an apology do?",
            answer="An apology can help fix hurt feelings and show that someone wants to do better.",
        ),
        QAItem(
            question="What is a curse in a story?",
            answer="A curse is a magical trouble that changes what happens to a person or place.",
        ),
        QAItem(
            question="What kind of animal does the word suey suggest?",
            answer="Suey sounds like the sort of word people use for a pig or a pig-like creature.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means treating others gently, fairly, and with care.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.form:
            bits.append(f"form={e.form}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CURSES]


def explain_rejection(setting: str, curse: str) -> str:
    return f"(No story: setting={setting!r}, curse={curse!r} is not a supported combination.)"


@dataclass
class ASPStub:
    pass
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


ASP_RULES = r"""
setting(village; woods; cottage; hall).
curse(suey; hog).

valid(S,C) :- setting(S), curse(C).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CURSES:
        lines.append(asp.fact("curse", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale transformation storyworld about a person and a suey spell.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--curse", choices=CURSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "curse", None) and getattr(args, "curse", None) not in CURSES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "setting", None) and getattr(args, "curse", None):
        if (getattr(args, "setting", None), getattr(args, "curse", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    curse = getattr(args, "curse", None) or rng.choice(list(CURSES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, curse=curse, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story_state(params)
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
        print(asp_program("#show valid/2."))
        return

    if getattr(args, "all", None):
        samples = [
            generate(StoryParams(setting=s, curse=c, name="Mira", gender="girl", trait="curious"))
            for s, c in valid_combos()
        ]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
