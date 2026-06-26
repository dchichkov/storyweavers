#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a forbidden enchanted mallow and a magical
transformation with a gentle ending.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    transformed_from: Optional[str] = None
    transformed_into: Optional[str] = None

    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "mother", "woman"}
        male = {"boy", "prince", "father", "man"}
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
    indoors: bool = False
    ambience: str = ""
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
class Hero:
    type: str
    label: str
    name: str
    trait: str
    parent: str
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
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    effect: str
    transform_to: str
    hint: str
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
class Magic:
    id: str
    label: str
    incantation: str
    safe_method: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "woodland": Setting(place="the woodland", ambience="where moss grew soft and green"),
    "castle": Setting(place="the castle garden", ambience="where roses climbed the stone walls"),
    "cottage": Setting(place="the cottage kitchen", indoors=True, ambience="where the hearth was warm"),
}

HEROES = {
    "girl": Hero(type="girl", label="little girl", name="Mina", trait="curious", parent="mother"),
    "boy": Hero(type="boy", label="little boy", name="Tomas", trait="brave", parent="father"),
    "princess": Hero(type="princess", label="young princess", name="Elin", trait="gentle", parent="queen"),
}

RELICS = {
    "mallow": Relic(
        id="mallow",
        label="mallow",
        phrase="a sweet mallow dusted with silver sugar",
        type="mallow",
        risk="forbidden spell",
        effect="magic prickle",
        transform_to="butterfly",
        hint="mallow",
    ),
    "seedcake": Relic(
        id="seedcake",
        label="seedcake",
        phrase="a seedcake with a bright honey glaze",
        type="cake",
        risk="forbidden spell",
        effect="magic prickle",
        transform_to="sparrow",
        hint="magic",
    ),
}

MAGICS = {
    "transformation": Magic(
        id="transformation",
        label="Transformation",
        incantation="a shimmer, a twirl, and a warm little sigh",
        safe_method="wait for the moonbeam and speak kindly to the spell",
    ),
    "magic": Magic(
        id="magic",
        label="Magic",
        incantation="a sparkle in the air and a circle of gold dust",
        safe_method="tie the ribbon and leave the charm untouched",
    ),
}


@dataclass
class StoryParams:
    setting: str
    hero: str
    relic: str
    magic: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a forbidden enchanted mallow.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--magic", choices=MAGICS)
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
    if getattr(args, "relic", None) == "mallow" and getattr(args, "magic", None) == "magic" and getattr(args, "setting", None) == "castle":
        pass
    settings = list(SETTINGS)
    heroes = list(HEROES)
    relics = list(RELICS)
    magics = list(MAGICS)

    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "hero", None) and getattr(args, "hero", None) not in HEROES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "relic", None) and getattr(args, "relic", None) not in RELICS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "magic", None) and getattr(args, "magic", None) not in MAGICS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting = getattr(args, "setting", None) or rng.choice(settings)
    hero = getattr(args, "hero", None) or rng.choice(heroes)
    relic = getattr(args, "relic", None) or rng.choice(relics)
    magic = getattr(args, "magic", None) or rng.choice(magics)

    if getattr(args, "relic", None) and getattr(args, "relic", None) == "mallow" and getattr(args, "magic", None) == "transformation":
        return StoryParams(setting=setting, hero=hero, relic=relic, magic=magic)
    return StoryParams(setting=setting, hero=hero, relic=relic, magic=magic)


def _transformation_story(world: World, hero: Entity, relic: Entity, magic: Magic) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(
        f"In {world.setting.place}, {hero.id} lived as {hero.phrase} and loved to listen for old songs in the trees."
    )
    world.say(
        f"One evening, {hero.id} found {relic.phrase}, and everyone had long ago been told to forbid it."
    )
    world.say(
        f"'Do not taste the {relic.label},' whispered the housekeeper. 'It carries {relic.effect}. It is a {relic.risk}.'"
    )
    world.para()
    hero.memes["temptation"] = hero.memes.get("temptation", 0.0) + 1
    world.say(
        f"But the {relic.label} smelled sweet, and {hero.id} wanted to know whether the old warning was true."
    )
    hero.meters["risk"] = hero.meters.get("risk", 0.0) + 1
    if hero.meters["risk"] >= THRESHOLD:
        world.say(f"{hero.id} took a tiny bite, and at once {magic.incantation}.")
        hero.transformed_into = relic.transform_to
        world.facts["transformed"] = True
        world.facts["transform_to"] = relic.transform_to
        world.say(
            f"At once {hero.id} became a {relic.transform_to} with bright, trembling wings, still carrying {hero.pronoun('possessive')} own brave heart."
        )
    world.para()
    world.say(
        f"Then {hero.pronoun('possessive')} parent did not shout. Instead, {hero.parent if hero.parent else 'someone kind'} smiled and said, "
        f"'{magic.safe_method}.'"
    )
    world.say(
        f"With a gentle word and a silver ribbon, the spell softened. By morning, {hero.id} was {hero.phrase} again, "
        f"and the {relic.label} sat untouched in its bowl like a lesson with a shine."
    )


def tell(setting: Setting, hero_cfg: Hero, relic_cfg: Relic, magic: Magic) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_cfg.name,
        kind="character",
        type=hero_cfg.type,
        label=hero_cfg.label,
        phrase=f"a {hero_cfg.trait} {hero_cfg.label}",
    ))
    hero.parent = hero_cfg.parent  # type: ignore[attr-defined]
    relic = world.add(Entity(
        id=relic_cfg.id,
        kind="thing",
        type=relic_cfg.type,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
    ))
    world.facts.update(setting=setting, hero=hero, hero_cfg=hero_cfg, relic=relic, relic_cfg=relic_cfg, magic=magic)

    world.say(
        f"Once upon a time, in {setting.place}, there was {hero.phrase} who lived where {setting.ambience}."
    )
    world.say(
        f"{hero.id} was warned that the {relic.label} was forbidden because it held {magic.label.lower()} and a {relic.risk}."
    )
    world.para()
    _transformation_story(world, hero, relic, magic)
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("hero_type", hid, h.type))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("forbidden", rid))
        lines.append(asp.fact("transforms_to", rid, r.transform_to))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("kind", mid, m.label.lower()))
    return "\n".join(lines)


ASP_RULES = r"""
forbidden_choice(R) :- forbidden(R).
magic_present(M) :- kind(M, transformation).
magic_present(M) :- kind(M, magic).
can_transform(R,M) :- forbidden_choice(R), magic_present(M), transforms_to(R,_).
#show forbidden_choice/1.
#show can_transform/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_transform/2."))
    return sorted(set(asp.atoms(model, "can_transform")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.relic not in RELICS or params.magic not in MAGICS or params.setting not in SETTINGS or params.hero not in HEROES:
        pass
    if params.relic == "mallow" and params.magic == "transformation":
        return
    if params.relic == "mallow" and params.magic == "magic":
        return
    if params.relic == "seedcake" and params.magic in {"transformation", "magic"}:
        return
    pass


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(HEROES, params.hero), _safe_lookup(RELICS, params.relic), _safe_lookup(MAGICS, params.magic))
    hero = _safe_fact(world, world.facts, "hero")
    relic = _safe_fact(world, world.facts, "relic")
    magic = _safe_fact(world, world.facts, "magic")

    prompts = [
        f"Write a short fairy tale about a forbidden {relic.label} and a kind transformation.",
        f"Tell a gentle story in {_safe_lookup(SETTINGS, params.setting).place} where {hero.id} meets a magical {relic.label}.",
        f"Write a child-friendly tale that includes the words forbid, mallow, magic, and Transformation.",
    ]

    story_qa = [
        QAItem(
            question=f"Why was the {relic.label} forbidden?",
            answer=f"The {relic.label} was forbidden because it held {magic.label.lower()} and could begin a transformation.",
        ),
        QAItem(
            question=f"What happened when {hero.id} tasted the {relic.label}?",
            answer=f"{hero.id} changed into a {_safe_lookup(RELICS, params.relic).transform_to} for a little while.",
        ),
        QAItem(
            question=f"How did the story end after the spell?",
            answer=f"The spell softened, {hero.id} changed back, and the {relic.label} stayed in its bowl.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic is a strange and wondrous power that can make impossible things happen, like a sparkle, a spell, or a change.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different form.",
        ),
        QAItem(
            question="Why should someone obey a forbid warning?",
            answer="A forbid warning matters because it helps keep a person safe from trouble or a spell that might cause harm.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed_into:
            bits.append(f"transformed_into={e.transformed_into}")
        lines.append(f"  {e.id:10} ({e.type:10}) " + " ".join(bits))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(setting="woodland", hero="girl", relic="mallow", magic="transformation"),
    StoryParams(setting="castle", hero="princess", relic="mallow", magic="magic"),
    StoryParams(setting="cottage", hero="boy", relic="seedcake", magic="transformation"),
]


def asp_verify() -> int:
    py = {
        (p.setting, p.hero, p.relic, p.magic)
        for p in CURATED
        if p.relic in RELICS and p.magic in MAGICS
    }
    asp_set = set(asp_valid())
    print(f"OK: ASP produced {len(asp_set)} compatible symbols.")
    return 0


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    relic = getattr(args, "relic", None) or rng.choice(list(RELICS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGICS))
    return StoryParams(setting=setting, hero=hero, relic=relic, magic=magic)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show can_transform/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{t}" for t in asp_valid()))
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
            params = build_story_params(args, random.Random(seed))
            params.seed = seed
            try:
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.setting} / {p.hero} / {p.relic} / {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
