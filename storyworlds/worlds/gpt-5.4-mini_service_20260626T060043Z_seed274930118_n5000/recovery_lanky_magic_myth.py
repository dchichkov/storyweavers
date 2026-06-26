#!/usr/bin/env python3
"""
storyworlds/worlds/recovery_lanky_magic_myth.py
===============================================

A small mythic storyworld about a lanky child, a magic loss, and a recovery
that can only happen in a reasonable way.

Seed tale, imagined from the prompt words:
---
Long ago, in a valley watched by stone owls, a lanky child named Pera kept the
lanterns of a shrine bright. One dusk, the shrine's magic river-stone slipped
into a cold hollow beneath the hill. The elder feared the valley would go dim
without it. Pera wanted to recover the stone at once, but the path was narrow,
the drop was deep, and the old rope was frayed.

The elder warned Pera not to climb alone. Pera reached anyway, then paused when
the wind shook the reeds. At last the elder brought a magic reed-ladder, and
together they lowered it into the hollow. Pera recovered the river-stone, the
lanterns glowed again, and the valley remembered its light.

World model:
- A hero is lanky, brave, and tied to a sacred place.
- A magic object is lost, hidden, or dimmed.
- The hero's desire to recover it creates risk.
- A wiser helper provides a matching magical method.
- The ending proves the change by restoring the place's light.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    bound_to: Optional[str] = None
    lost: bool = False
    magic: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    relic: object | None = None
    remedy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "queen"}
        male = {"boy", "man", "father", "brother", "king"}
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
    mood: str
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
class Relic:
    id: str
    label: str
    phrase: str
    power: str
    failure: str
    recover: str
    zone: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Remedy:
    id: str
    label: str
    phrase: str
    method: str
    tail: str
    works_for: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_darken(world: World) -> list[str]:
    out: list[str] = []
    for relic in list(world.entities.values()):
        if not relic.magic or not relic.lost:
            continue
        if relic.meters["light"] >= THRESHOLD:
            continue
        key = ("darken", relic.id)
        if key in world.fired:
            continue
        world.fired.add(key)
        out.append(f"The {relic.label} stayed hidden, and the shrine grew dim.")
    return out


def _r_hope(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["hope"] < THRESHOLD:
            continue
        key = ("hope", hero.id)
        if key in world.fired:
            continue
        world.fired.add(key)
        out.append(f"{hero.id} held hope steady as the dark path waited.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_darken, _r_hope):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} lay under a {setting.mood} sky, and the stones listened."


def noun_phrase(entity: Entity) -> str:
    return entity.phrase or entity.label or entity.id


def predict(world: World, hero: Entity, relic: Entity) -> dict:
    sim = world.copy()
    _do_seek(sim, hero, relic, narrate=False)
    return {
        "recovered": not sim.get(relic.id).lost,
        "danger": sim.get(hero.id).meters["danger"],
    }


def _do_seek(world: World, hero: Entity, relic: Entity, narrate: bool = True) -> None:
    hero.meters["distance"] += 1
    if world.setting.place not in world.setting.affords:
        pass
    if hero.meters["danger"] < THRESHOLD:
        hero.meters["danger"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "hill shrine": Setting(place="the hill shrine", mood="silver", affords={"recovery", "magic"}),
    "river hollow": Setting(place="the river hollow", mood="misty", affords={"recovery", "magic"}),
    "old grove": Setting(place="the old grove", mood="blue", affords={"recovery", "magic"}),
}

RELICS = {
    "river-stone": Relic(
        id="river-stone",
        label="river-stone",
        phrase="a small magic river-stone",
        power="kept the lanterns bright",
        failure="went dim",
        recover="recover the river-stone",
        zone="hollow",
        genders={"girl", "boy"},
    ),
    "star-bell": Relic(
        id="star-bell",
        label="star-bell",
        phrase="a bright magic star-bell",
        power="kept the bells singing",
        failure="fell silent",
        recover="recover the star-bell",
        zone="branches",
        genders={"girl", "boy"},
    ),
    "moon-ember": Relic(
        id="moon-ember",
        label="moon-ember",
        phrase="a warm magic moon-ember",
        power="kept the hearth warm",
        failure="cooled",
        recover="recover the moon-ember",
        zone="cave",
        genders={"girl", "boy"},
    ),
}

REMEDIES = {
    "reed-ladder": Remedy(
        id="reed-ladder",
        label="reed-ladder",
        phrase="a magic reed-ladder",
        method="lower the reed-ladder",
        tail="lowered the reed-ladder into the hollow",
        works_for={"river-stone"},
    ),
    "silver-rope": Remedy(
        id="silver-rope",
        label="silver-rope",
        phrase="a magic silver-rope",
        method="tie the silver-rope to the branch",
        tail="sent the silver-rope up through the branches",
        works_for={"star-bell"},
    ),
    "ember-glove": Remedy(
        id="ember-glove",
        label="ember-glove",
        phrase="a magic ember-glove",
        method="carry the ember-glove with both hands",
        tail="wrapped the ember-glove around the cooled ember",
        works_for={"moon-ember"},
    ),
}

NAMES = ["Pera", "Milo", "Ari", "Nia", "Tavi", "Lena", "Soren", "Dara"]
TRAITS = ["lanky", "gentle", "bold", "quiet", "curious", "steadfast"]


@dataclass
class StoryParams:
    place: str
    relic: str
    remedy: str
    name: str
    gender: str
    elder: str
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


def compatible() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for relic_id, relic in RELICS.items():
            for remedy_id, remedy in REMEDIES.items():
                if relic_id in remedy.works_for:
                    out.append((place, relic_id, remedy_id, "girl"))
                    out.append((place, relic_id, remedy_id, "boy"))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic recovery storyworld with a lanky child and a magic remedy.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["elder", "aunt", "uncle", "mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = []
    for place in SETTINGS:
        if getattr(args, "place", None) and getattr(args, "place", None) != place:
            continue
        for relic_id, relic in RELICS.items():
            if getattr(args, "relic", None) and getattr(args, "relic", None) != relic_id:
                continue
            for remedy_id, remedy in REMEDIES.items():
                if getattr(args, "remedy", None) and getattr(args, "remedy", None) != remedy_id:
                    continue
                if relic_id not in remedy.works_for:
                    continue
                for gender in (["girl", "boy"] if getattr(args, "gender", None) is None else [getattr(args, "gender", None)]):
                    if gender not in relic.genders:
                        continue
                    candidates.append((place, relic_id, remedy_id, gender))
    if not candidates:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, relic, remedy, gender = rng.choice(sorted(candidates))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["elder", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, relic=relic, remedy=remedy, name=name, gender=gender, elder=elder, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "lanky"]))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label=f"the {params.elder}", traits=["wise"]))
    relic_cfg = _safe_lookup(RELICS, params.relic)
    relic = world.add(Entity(
        id=relic_cfg.id,
        type="relic",
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        owner=hero.id,
        caretaker=elder.id,
        lost=True,
        magic=True,
    ))
    remedy_cfg = _safe_lookup(REMEDIES, params.remedy)
    remedy = world.add(Entity(
        id=remedy_cfg.id,
        type="remedy",
        label=remedy_cfg.label,
        phrase=remedy_cfg.phrase,
        owner=elder.id,
        magic=True,
    ))

    world.say(f"Long ago, {hero.id} was a {params.trait} {hero.type} whose limbs were so {params.trait} that the villagers called {hero.pronoun('object')} lanky.")
    world.say(f"{hero.id} served at {world.setting.place} and kept the fires of the shrine awake.")
    world.say(f"Then the {relic.label} {relic.failure}, and the lamps no longer shone as they should.")
    world.para()
    world.say(setting_detail(world.setting))
    world.say(f"{hero.id} wanted to {relic.recover} at once, because {relic.label} {relic.power}.")
    world.say(f"But {elder.label} warned that the way down was narrow, and the dark place could make even a brave heart falter.")
    hero.memes["resolve"] += 1
    hero.memes["hope"] += 1
    hero.memes["fear"] += 1
    propagate(world)
    world.para()
    world.say(f"{hero.id} went toward the hidden place anyway, but when the stones showed their steep edge, {hero.id} stopped and listened.")
    world.say(f"{elder.label} brought {remedy_cfg.phrase}, because only that magic way could {remedy_cfg.method}.")
    if predict(world, hero, relic)["recovered"] is False:
        pass
    relic.lost = False
    relic.meters["light"] = 1.0
    hero.memes["hope"] += 1
    world.para()
    world.say(f"Together they {remedy_cfg.tail}, and {hero.id} reached down with careful hands.")
    world.say(f"At last {hero.id} recovered the {relic.label}, and the shrine glowed again as if dawn had returned.")
    world.say(f"The {relic.label} stayed near the {world.setting.place}, and the people remembered that even a lanky child can carry a holy light home.")
    world.facts.update(hero=hero, elder=elder, relic=relic, remedy=remedy, params=params, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    relic = _safe_fact(world, f, "relic")
    remedy = _safe_fact(world, f, "remedy")
    return [
        f'Write a short myth for a child about a lanky hero who must recover {relic.phrase}.',
        f"Tell a gentle legend where {hero.id} and {f['elder'].label} use {remedy.phrase} to bring back the lost {relic.label}.",
        f'Write a magical recovery story that includes the word "lanky" and ends with the shrine shining again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    relic = _safe_fact(world, f, "relic")
    remedy = _safe_fact(world, f, "remedy")
    elder = _safe_fact(world, f, "elder")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a lanky {hero.type} who served at {world.setting.place}.",
        ),
        QAItem(
            question=f"What had to be recovered?",
            answer=f"They had to recover the {relic.label}, a magic thing that kept the shrine bright.",
        ),
        QAItem(
            question=f"How did {hero.id} and {elder.label} fix the loss?",
            answer=f"They used {remedy.phrase} and worked together so the {relic.label} could be recovered safely.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the shrine glowed again, so the place was no longer dim.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does magic mean in a story like this?",
            answer="In a story like this, magic is a special power that can brighten, protect, or help people do something impossible by ordinary means.",
        ),
        QAItem(
            question="What is a recovery?",
            answer="A recovery is when something lost, broken, or dim comes back again, or when someone gets better after trouble.",
        ),
        QAItem(
            question="What does lanky mean?",
            answer="Lanky means tall and thin, with long arms or legs.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.lost:
            parts.append("lost=True")
        if e.magic:
            parts.append("magic=True")
        if e.traits:
            parts.append(f"traits={e.traits}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
lost(R) :- relic(R), hidden(R).
needs_recovery(R) :- relic(R), lost(R).
compatible(M,R) :- remedy(M), relic(R), fixes(M,R).
valid_story(P,R,M,G) :- place(P), needs_recovery(R), compatible(M,R), gender(G), wears(G,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("hidden", rid))
        for g in sorted(r.genders):
            lines.append(asp.fact("wears", g, rid))
    for mid, m in REMEDIES.items():
        lines.append(asp.fact("remedy", mid))
        for rid in sorted(m.works_for):
            lines.append(asp.fact("fixes", mid, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, r, m, g) for p, r, m, g in compatible())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="hill shrine", relic="river-stone", remedy="reed-ladder", name="Pera", gender="girl", elder="elder", trait="lanky"),
    StoryParams(place="old grove", relic="star-bell", remedy="silver-rope", name="Milo", gender="boy", elder="aunt", trait="curious"),
    StoryParams(place="river hollow", relic="moon-ember", remedy="ember-glove", name="Dara", gender="girl", elder="uncle", trait="steadfast"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} valid stories:")
        for t in triples[:50]:
            print(" ", t)
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
            header = f"### {p.name}: {p.relic} via {p.remedy} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
