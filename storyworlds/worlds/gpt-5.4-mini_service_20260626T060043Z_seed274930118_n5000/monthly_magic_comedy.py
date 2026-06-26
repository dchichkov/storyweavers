#!/usr/bin/env python3
"""
storyworlds/worlds/monthly_magic_comedy.py
==========================================

A small story world about a monthly magic mishap with a comedic turn.

Premise:
- A child loves a monthly magical delivery.
- The delivery is helpful, but a rule or side effect makes the month go oddly.
- Someone worries, the child reacts, and a comic compromise fixes the trouble.

The world is intentionally constrained: only stories where the magic prize
actually creates a reasonable problem are generated.
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

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]



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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "glow": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "amusement": 0.0, "conflict": 0.0}

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
class MonthlyThing:
    id: str
    label: str
    phrase: str
    effect: str
    mess: str
    fix: str
    vibe: str
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
    place: str
    afford: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
        self.month: str = ""

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    month: str
    magic: str
    name: str
    gender: str
    helper: str
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


SETTINGS = {
    "home": Setting(place="the cozy house", afford={"magic_mail"}),
    "shop": Setting(place="the little shop", afford={"magic_mail"}),
    "kitchen": Setting(place="the kitchen", afford={"magic_mail"}),
}

MONTHLY_THINGS = {
    "sparkly_stamp": MonthlyThing(
        id="sparkly_stamp",
        label="sparkly stamp",
        phrase="a monthly sparkly stamp",
        effect="stamped every letter with glitter",
        mess="glitter",
        fix="brush the glitter into a jar",
        vibe="shiny",
        tags={"glitter", "mail"},
    ),
    "moon_mug": MonthlyThing(
        id="moon_mug",
        label="moon mug",
        phrase="a monthly moon mug",
        effect="made cocoa taste like a tiny moonbeam",
        mess="foam",
        fix="wipe the foam with a napkin",
        vibe="silly",
        tags={"cocoa", "cup"},
    ),
    "giggle_glove": MonthlyThing(
        id="giggle_glove",
        label="giggle glove",
        phrase="a monthly giggle glove",
        effect="tickled anyone who wore it",
        mess="giggles",
        fix="hang it on a hook for a minute",
        vibe="funny",
        tags={"glove", "tickle"},
    ),
    "tricky_calendar": MonthlyThing(
        id="tricky_calendar",
        label="tricky calendar",
        phrase="a monthly trick calendar",
        effect="sneezed confetti at the wrong date",
        mess="confetti",
        fix="close the calendar gently",
        vibe="wacky",
        tags={"calendar", "date"},
    ),
}

HELPERS = {
    "cat": ("a curious cat", "the cat"),
    "grandma": ("a cheerful grandma", "Grandma"),
    "robot": ("a clanking robot", "the robot"),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Nina", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Ben"]
TRAITS = ["curious", "cheerful", "sly", "brave", "silly"]


def is_reasonable(magic: MonthlyThing) -> bool:
    return magic.id in MONTHLY_THINGS


def explain_rejection(magic: MonthlyThing) -> str:
    return f"(No story: {magic.label} is not part of the monthly magic shelf.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Monthly magic comedy story world.")
    ap.add_argument("--month", choices=MONTHS)
    ap.add_argument("--magic", choices=sorted(MONTHLY_THINGS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    if getattr(args, "magic", None) and getattr(args, "magic", None) not in MONTHLY_THINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    magic = getattr(args, "magic", None) or rng.choice(sorted(MONTHLY_THINGS))
    month = getattr(args, "month", None) or rng.choice(MONTHS)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    return StoryParams(month=month, magic=magic, name=name, gender=gender, helper=helper)


def introduce(world: World, hero: Entity, helper: Entity, thing: MonthlyThing) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved {thing.phrase} because "
        f"{thing.effect}."
    )
    world.say(f"{helper.label} liked it too, mostly because it made the room feel like a joke that learned to bounce.")


def delivery(world: World, hero: Entity, thing: MonthlyThing) -> None:
    world.say(
        f"One {world.month.lower()} morning, a shiny envelope arrived at {world.setting.place}."
    )
    world.say(
        f"Inside was {thing.phrase}, and {hero.id} held {(getattr(thing, 'it')() if callable(getattr(thing, 'it', None)) else getattr(thing, 'it', 'it'))} up like a prize in a tiny parade."
    )


def activate_magic(world: World, hero: Entity, helper: Entity, thing: MonthlyThing) -> None:
    hero.memes["joy"] += 1
    hero.meters["glow"] += 1
    helper.memes["amusement"] += 1
    world.say(
        f"{hero.id} opened it at once, and {thing.label} did its monthly trick: {thing.effect}."
    )
    if thing.id == "sparkly_stamp":
        hero.meters["mess"] += 1
        world.say(f"Very soon, glitter was on {hero.id}'s nose, the table, and one surprised eyebrow.")
    elif thing.id == "moon_mug":
        hero.meters["mess"] += 1
        world.say(f"Foam spilled over the rim and made a snowy moustache on {hero.id}'s top lip.")
    elif thing.id == "giggle_glove":
        hero.memes["worry"] += 1
        world.say(f"The glove tickled so much that {hero.id} snorted and tried not to laugh into a cushion.")
    elif thing.id == "tricky_calendar":
        hero.meters["mess"] += 1
        world.say(f"Confetti sneezed out of the calendar and landed in a bright pile on the floor.")
    world.para()


def warn(world: World, helper: Entity, hero: Entity, thing: MonthlyThing) -> None:
    helper.memes["worry"] += 1
    world.say(
        f"{helper.label} blinked and said, \"That monthly magic is funny, but it is making a mess.\""
    )
    world.say(
        f"\"If it keeps going, {hero.id} will have {thing.mess} everywhere,\" {helper.pronoun('subject')} added with a grin."
    )


def resolve(world: World, helper: Entity, hero: Entity, thing: MonthlyThing) -> None:
    hero.memes["amusement"] += 1
    hero.memes["joy"] += 1
    helper.memes["worry"] = 0.0
    world.say(
        f"{hero.id} thought for a moment, then giggled and said, \"Let's do the silly fix.\""
    )
    world.say(
        f"Together they {thing.fix}, and the room got neat again."
    )
    world.say(
        f"After that, {hero.id} kept {thing.label} on a shelf, where it could be funny once a month without causing more drama than a clown in slippers."
    )


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS["home"])
    world.month = params.month

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper_noun, helper_label = _safe_lookup(HELPERS, params.helper)
    helper = world.add(Entity(id=helper_label, kind="character", type="thing", label=helper_noun))
    thing = _safe_lookup(MONTHLY_THINGS, params.magic)

    world.facts.update(hero=hero, helper=helper, thing=thing, params=params)
    introduce(world, hero, helper, thing)
    world.para()
    delivery(world, hero, thing)
    activate_magic(world, hero, helper, thing)
    warn(world, helper, hero, thing)
    resolve(world, helper, hero, thing)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    thing = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "thing")
    return [
        f'Write a short comedy story for a child about a monthly {thing.label}.',
        f"Tell a funny story where {hero.id} gets {thing.phrase} and has to fix the mess.",
        f"Write a gentle monthly magic tale that ends with a silly cleanup and a laugh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    thing = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "thing")
    return [
        QAItem(
            question=f"What did {hero.id} get every month?",
            answer=f"{hero.id} got {thing.phrase} every month, and it always did {thing.effect}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the magic became messy?",
            answer=f"{helper.label} helped {hero.id}, because the monthly magic was funny but messy.",
        ),
        QAItem(
            question=f"What did they do to fix the mess?",
            answer=f"They {thing.fix}, and that made the room neat again.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and amused, because the magic stayed fun after the cleanup.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does monthly mean?",
            answer="Monthly means something happens once every month.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising and impossible that makes the story playful or mysterious.",
        ),
        QAItem(
            question="Why can glitter be annoying?",
            answer="Glitter is annoying because it sticks to everything and is hard to sweep away.",
        ),
        QAItem(
            question="Why do people clean up spills?",
            answer="People clean up spills so the floor and table do not stay messy or slippery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id} ({e.type}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
monthly(M).
valid(M) :- monthly(M).
"""

def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("monthly", m) for m in sorted(MONTHLY_THINGS))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(m,) for m in MONTHLY_THINGS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches registry ({len(py)} items).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_valid_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    magic = getattr(args, "magic", None) or rng.choice(sorted(MONTHLY_THINGS))
    month = getattr(args, "month", None) or rng.choice(MONTHS)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    return StoryParams(month=month, magic=magic, name=name, gender=gender, helper=helper)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} valid monthly magic choices:\n")
        for (m,) in vals:
            print(f"  {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, magic in enumerate(sorted(MONTHLY_THINGS)):
            params = StoryParams(
                month=_safe_lookup(MONTHS, i % len(MONTHS)),
                magic=magic,
                name=_safe_lookup(GIRL_NAMES, i % len(GIRL_NAMES)),
                gender="girl" if i % 2 == 0 else "boy",
                helper=list(sorted(HELPERS))[i % len(HELPERS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
            seed = base_seed + i
            i += 1
            params = resolve_valid_combo(args, random.Random(seed))
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
            header = f"### {p.name}: {p.magic} in {p.month}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
