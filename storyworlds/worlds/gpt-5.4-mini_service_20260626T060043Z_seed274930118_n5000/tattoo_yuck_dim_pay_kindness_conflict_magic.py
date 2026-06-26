#!/usr/bin/env python3
"""
Standalone story world: tattoo, yuck-dim, pay.
A small comedy domain about a child, a messy-sounding magic tattoo, a payment
mix-up, and a kind resolution after conflict.
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cashier: object | None = None
    helper: object | None = None
    hero: object | None = None
    tattoo: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
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
class Place:
    name: str
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
class InkArt:
    id: str
    adjective: str
    noun: str
    price: int
    magic: bool = False
    yuck_dim: bool = False
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
    place: str
    art: str
    name: str
    gender: str
    helper: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


def _p(name: str) -> str:
    return name[0].upper() + name[1:] if name else name


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: tattoo, yuck-dim, pay.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--art", choices=sorted(ARTS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["friend", "parent", "sibling"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid, art in ARTS.items():
        lines.append(asp.fact("art", aid))
        if art.magic:
            lines.append(asp.fact("magic_art", aid))
        if art.yuck_dim:
            lines.append(asp.fact("yuck_dim_art", aid))
        lines.append(asp.fact("price", aid, art.price))
    for gender in ["girl", "boy"]:
        lines.append(asp.fact("gender", gender))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A) :- place(P), art(A).
funny(A) :- yuck_dim_art(A).
fix(A) :- magic_art(A).
kind(A) :- price(A,N), N > 0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = {(p, a) for p in PLACES for a in ARTS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


PLACES = {
    "mall": Place("the mall"),
    "fair": Place("the fair"),
    "plaza": Place("the plaza"),
    "corner_shop": Place("the corner shop"),
}

ARTS = {
    "tiny_tattoo": InkArt("tiny_tattoo", "tiny", "tattoo", 3, magic=True, yuck_dim=False),
    "yuck_dim_tattoo": InkArt("yuck_dim_tattoo", "yuck-dim", "tattoo", 1, magic=False, yuck_dim=True),
    "sparkle_tattoo": InkArt("sparkle_tattoo", "sparkle", "tattoo", 5, magic=True, yuck_dim=False),
}


GIRL_NAMES = ["Mina", "Luna", "Ivy", "Zoe", "Nia", "Mila"]
BOY_NAMES = ["Owen", "Finn", "Max", "Theo", "Leo", "Ben"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, a) for p in PLACES for a in ARTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "art", None):
        combos = [c for c in combos if c[1] == getattr(args, "art", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, art = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["friend", "parent", "sibling"])
    return StoryParams(place=place, art=art, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def tell(params: StoryParams) -> World:
    art = _safe_lookup(ARTS, params.art)
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper_type = {"friend": "friend", "parent": "mother", "sibling": "sister"}[params.helper]
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {params.helper}"))
    cashier = world.add(Entity(id="Cashier", kind="character", type="person", label="the cashier"))
    tattoo = world.add(Entity(id="tattoo", type="tattoo", label="tattoo", phrase=f"{_article(art.adjective)} {art.adjective} tattoo",
                              owner=hero.id, caretaker=helper.id, region="arm"))
    world.facts.update(hero=hero, helper=helper, cashier=cashier, tattoo=tattoo, art=art, params=params)
    hero.memes["want"] = 1
    world.say(f"{hero.id} was a {_p(params.gender)} child who loved shiny surprises.")
    world.say(f"At {world.place.name}, {hero.id} spotted { _article(art.adjective)} {art.adjective} tattoo booth and grinned.")
    world.say(f"{hero.id} wanted {tattoo.phrase} right away, because it looked funny in the best possible way.")
    world.para()
    world.say(f"The cashier said the tattoo would cost {art.price} coins, so {hero.id} started to pay.")
    if art.yuck_dim:
        hero.memes["conflict"] += 1
        world.say(f"But the sign said yuck-dim, and {hero.id} wrinkled {hero.pronoun('possessive')} nose.")
        world.say(f'"Yuck," {hero.id} said, "that sounds like a sticker that sneezed."')
    if art.magic:
        hero.memes["magic"] += 1
        world.say(f"Then the artist winked and said the tattoo was magic, so it could sparkle only when told a kind joke.")
    world.para()
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} reached for coins, but one bounced under the table and rolled away like a tiny escaped marble.")
    world.say(f"{helper.label} laughed, chased the coin, and said, 'No worries. We can pay the nice way.'")
    hero.memes["kindness"] += 1
    if art.yuck_dim:
        world.say(f"{hero.id} giggled so hard that even the yuck-dim name sounded friendly.")
    world.say(f"Together they paid, and the artist placed the tattoo on {hero.pronoun('possessive')} arm with a flourish.")
    if art.magic:
        world.say(f"The tattoo gave one polite sparkle, then another, as if it had manners.")
    world.say(f"In the end, {hero.id} wore {tattoo.it()} home, happy, and the whole little trip felt like a joke that had learned to be kind.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    art = _safe_fact(world, f, "art")
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a short comedy story for children about a child who wants {art.adjective} tattoo.',
        f"Tell a funny story where {hero.id} tries to pay for a {art.noun} at {world.place.name} and something yuck-dim gets in the way.",
        f"Write a gentle, silly story with kindness, conflict, and magic about a tattoo booth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    art = _safe_fact(world, f, "art")
    tattoo = _safe_fact(world, f, "tattoo")
    return [
        QAItem(
            question=f"What did {hero.id} want at {world.place.name}?",
            answer=f"{hero.id} wanted {tattoo.phrase} from the tattoo booth.",
        ),
        QAItem(
            question=f"Why did {hero.id} make a face when the sign said yuck-dim?",
            answer=f"{hero.id} made a face because the word yuck-dim sounded silly and a little gross.",
        ),
        QAItem(
            question=f"How did {helper.label} help when the coin rolled away?",
            answer=f"{helper.label} chased the coin and helped {hero.id} pay the nice way.",
        ),
        QAItem(
            question=f"What made the tattoo extra special?",
            answer=f"The tattoo was magic, so it could sparkle after kind words and funny jokes.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tattoo?",
            answer="A tattoo is a design made on skin that can look like a tiny picture or pattern.",
        ),
        QAItem(
            question="What does kindness do in a story?",
            answer="Kindness helps characters solve problems without being mean, so the story can end happily.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or worry that makes the characters stop and decide what to do next.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special impossible-sounding power that can make strange or wonderful things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="mall", art="yuck_dim_tattoo", name="Mina", gender="girl", helper="friend"),
    StoryParams(place="fair", art="tiny_tattoo", name="Leo", gender="boy", helper="parent"),
    StoryParams(place="plaza", art="sparkle_tattoo", name="Ivy", gender="girl", helper="sibling"),
]


def asp_valid() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify_gate() -> int:
    import asp
    python_set = set(valid_combos())
    asp_set = set(asp_valid())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_gate())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid story combos:")
        for p, a in vals:
            print(f"  {p:12} {a}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if header:
            print(header)
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
