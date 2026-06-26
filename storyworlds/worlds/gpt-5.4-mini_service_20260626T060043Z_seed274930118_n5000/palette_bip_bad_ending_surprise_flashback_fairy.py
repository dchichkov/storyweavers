#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/palette_bip_bad_ending_surprise_flashback_fairy.py
=============================================================================================================

A small fairy-tale storyworld about a child with a palette, a magical bip,
a surprise, and a flashback that changes the ending.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    item: object | None = None
    spark: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "fairy", "woman", "mother"}
        male = {"boy", "king", "prince", "wizard", "man", "father"}
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
class Realm:
    place: str
    indoors: bool = False
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
class TaleItem:
    label: str
    phrase: str
    type: str
    risk: str
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
class Spark:
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


class World:
    def __init__(self, realm: Realm) -> None:
        self.realm = realm
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        w = World(self.realm)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


REALMS = {
    "lantern_lane": Realm(place="the lantern lane"),
    "willow_glen": Realm(place="the willow glen"),
    "mossy_bridge": Realm(place="the mossy bridge"),
    "castle_garden": Realm(place="the castle garden"),
}

ITEMS = {
    "palette": TaleItem(
        label="palette",
        phrase="a bright paint palette",
        type="palette",
        risk="smeared",
    ),
    "cloak": TaleItem(
        label="cloak",
        phrase="a soft silver cloak",
        type="cloak",
        risk="muddy",
    ),
    "crown": TaleItem(
        label="crown",
        phrase="a little golden crown",
        type="crown",
        risk="dented",
    ),
    "slippers": TaleItem(
        label="slippers",
        phrase="pink velvet slippers",
        type="slippers",
        risk="scuffed",
        plural=True,
    ),
}

SPARKS = {
    "bip": Spark(
        id="bip",
        label="bip",
        phrase="a tiny magic bip",
        effect="glow",
    ),
    "chime": Spark(
        id="chime",
        label="chime",
        phrase="a soft bell chime",
        effect="shine",
    ),
}

CHAR_NAMES = ["Mina", "Lio", "Pippa", "Tavi", "Nora", "Elin", "Bram", "Theo"]
TRAITS = ["curious", "gentle", "brave", "dreamy", "kind", "small"]


@dataclass
class StoryParams:
    place: str
    item: str
    spark: str
    name: str
    gender: str
    companion: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy tale world with a palette, bip, flashback, surprise, and a bad ending."
    )
    ap.add_argument("--place", choices=REALMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spark", choices=SPARKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["fairy", "grandmother", "woodcutter"])
    ap.add_argument("--name")
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


def _item_risk(item: TaleItem, spark: Spark) -> bool:
    return item.label == "palette" and spark.id == "bip"


def _reason_ok(item: TaleItem, spark: Spark) -> bool:
    return _item_risk(item, spark)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "item", None) and getattr(args, "spark", None):
        if not _reason_ok(_safe_lookup(ITEMS, getattr(args, "item", None)), _safe_lookup(SPARKS, getattr(args, "spark", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = []
    for place in REALMS:
        for item in ITEMS:
            for spark in SPARKS:
                if getattr(args, "place", None) and place != getattr(args, "place", None):
                    continue
                if getattr(args, "item", None) and item != getattr(args, "item", None):
                    continue
                if getattr(args, "spark", None) and spark != getattr(args, "spark", None):
                    continue
                if not _reason_ok(_safe_lookup(ITEMS, item), _safe_lookup(SPARKS, spark)):
                    continue
                combos.append((place, item, spark))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item, spark = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHAR_NAMES)
    companion = getattr(args, "companion", None) or rng.choice(["fairy", "grandmother", "woodcutter"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, item=item, spark=spark, name=name, gender=gender, companion=companion, trait=trait)


def _narrate_flashback(world: World, hero: Entity, item: Entity) -> None:
    world.say(
        f"Then the story remembered an earlier day when {hero.id} had painted a moon on {hero.pronoun('possessive')} {item.label}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had laughed so hard that a small stray bip from the magic brush had hopped across the paint."
    )


def _narrate_surprise(world: World, hero: Entity, spark: Entity) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"At once, a surprise came: the bip woke the colors, and the air around {hero.id} shimmered like a lantern behind glass."
    )
    world.say(
        f"{hero.id} blinked because the little bip was not just a sound; it was a key to a hidden memory."
    )


def _narrate_bad_ending(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["sadness"] += 1
    world.say(
        f"But the spell slipped wrong, and the colors ran away like frightened fireflies."
    )
    world.say(
        f"In the end, {hero.id} held the {item.label} with a quiet heart, and the picture on it was gone."
    )


def tell_story(params: StoryParams) -> World:
    realm = _safe_lookup(REALMS, params.place)
    world = World(realm)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"hope": 1.0}, memes={"wonder": 1.0}))
    companion = world.add(Entity(id="Companion", kind="character", type=params.companion))
    item_cfg = _safe_lookup(ITEMS, params.item)
    spark_cfg = _safe_lookup(SPARKS, params.spark)
    item = world.add(Entity(id="Item", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    spark = world.add(Entity(id="Spark", type=spark_cfg.id, label=spark_cfg.label, phrase=spark_cfg.phrase))

    world.say(f"Once in {realm.place}, there lived a {params.trait} little {params.gender} named {hero.id}.")
    world.say(f"{hero.id} loved {item.phrase} and kept it close as if it were a tiny treasure from the sun.")

    world.para()
    world.say(f"One dusk, {hero.id} went to {realm.place} with {hero.pronoun('possessive')} {companion.type}.")
    world.say(f"{hero.id} wanted to keep the {item.label} bright, but a curious {spark.label} trembled in the grass.")

    _narrate_flashback(world, hero, item)
    _narrate_surprise(world, hero, spark)

    world.para()
    world.say(f"That was when the old fear returned: if the bip grew strong, it would smear the {item.label} forever.")
    world.say(f"{hero.id} tried to hush the magic, yet the wind only fanned it brighter.")
    _narrate_bad_ending(world, hero, item)

    world.facts.update(hero=hero, companion=companion, item=item, spark=spark, realm=realm, bad_ending=True)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    item: Entity = _safe_fact(world, f, "item")
    return [
        f'Write a short fairy tale for a small child about {hero.id}, a {item.label}, and a tiny bip.',
        f"Tell a gentle but surprising story in which {hero.id} meets a bip while caring for {item.phrase}.",
        f"Write a fairy tale with a flashback and a bad ending about a child and {item.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    item: Entity = _safe_fact(world, f, "item")
    spark: Entity = _safe_fact(world, f, "spark")
    companion: Entity = _safe_fact(world, f, "companion")
    realm: Realm = _safe_fact(world, f, "realm")
    return [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {hero.id}, who loves {item.phrase} and walks through {realm.place} with a {companion.type}.",
        ),
        QAItem(
            question=f"What surprising thing happened when the bip woke up?",
            answer=f"The bip made the colors shimmer and turned the moment into a surprise that {hero.id} could not ignore.",
        ),
        QAItem(
            question=f"What earlier memory came back in the flashback?",
            answer=f"{hero.id} remembered painting a moon on the {item.label} and hearing a tiny bip from the magic brush.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly, because the spell slipped wrong and the colors ran away from {item.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a palette?",
            answer="A palette is a flat board or tray that holds paint colors for making pictures.",
        ),
        QAItem(
            question="What can a bip mean in a fairy tale?",
            answer="A bip can be a tiny magic sound, like a little signal that something is about to happen.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is a sudden change that the characters did not expect.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lantern_lane", item="palette", spark="bip", name="Mina", gender="girl", companion="fairy", trait="curious"),
    StoryParams(place="willow_glen", item="palette", spark="bip", name="Pippa", gender="girl", companion="grandmother", trait="dreamy"),
    StoryParams(place="castle_garden", item="palette", spark="bip", name="Theo", gender="boy", companion="woodcutter", trait="gentle"),
]


ASP_RULES = r"""
item_risk(palette,bip).
valid(Place,Item,Spark) :- place(Place), item(Item), spark(Spark), item_risk(Item,Spark).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in REALMS:
        lines.append(asp.fact("place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for s in SPARKS:
        lines.append(asp.fact("spark", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, i, s) for p in REALMS for i in ITEMS for s in SPARKS if _reason_ok(_safe_lookup(ITEMS, i), _safe_lookup(SPARKS, s))]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(item: TaleItem, spark: Spark) -> str:
    return f"(No story: {spark.label} does not create a meaningful fairy-tale change for {item.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "item", None) and getattr(args, "spark", None) and not _reason_ok(_safe_lookup(ITEMS, getattr(args, "item", None)), _safe_lookup(SPARKS, getattr(args, "spark", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
              and (getattr(args, "spark", None) is None or c[2] == getattr(args, "spark", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item, spark = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHAR_NAMES)
    companion = getattr(args, "companion", None) or rng.choice(["fairy", "grandmother", "woodcutter"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, item=item, spark=spark, name=name, gender=gender, companion=companion, trait=trait)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, item, spark) combos:\n")
        for p, i, s in triples:
            print(f"  {p:14} {i:10} {s:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
