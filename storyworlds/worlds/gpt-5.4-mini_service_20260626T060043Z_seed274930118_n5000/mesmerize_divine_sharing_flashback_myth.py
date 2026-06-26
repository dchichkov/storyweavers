#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mesmerize_divine_sharing_flashback_myth.py
====================================================================================================================

A standalone myth-story world about a divine gift, a mesmerizing danger,
and the old lesson that sharing makes the light kinder.

The seed impression behind this world:
- a small, classical myth
- a divine object or blessing that can mesmerize
- a turn toward sharing
- a flashback to an older sacred kindness
- an ending that proves the change in the world

The world keeps a live model with meters and memes:
- meters: brightness, distance, hunger, fatigue, carriedness
- memes: awe, greed, trust, fear, wonder, relief, devotion

The story engine does not just swap nouns into a frozen paragraph; it simulates
who holds the sacred thing, who is drawn near by its glow, when someone remembers
an older blessing, and how sharing changes the ending image.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    gift_ent: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "king", "priest"}
        female = {"girl", "woman", "mother", "queen", "priestess"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def item_pronoun(self) -> str:
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
    id: str
    label: str
    sacred: bool = False
    echo: str = ""
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
class Gift:
    id: str
    label: str
    phrase: str
    glow: str
    mesmeric: str
    share_action: str
    shared_image: str
    location: str
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


@dataclass
class StoryParams:
    place: str
    gift: str
    hero_name: str
    hero_type: str
    elder_type: str
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
    def __init__(self, place: Place, gift: Gift) -> None:
        self.place = place
        self.gift = gift
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}
        self.flashback_used = False

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        cur = []
        for line in self.lines:
            if line == "":
                if cur:
                    out.append(" ".join(cur))
                    cur = []
            else:
                cur.append(line)
        if cur:
            out.append(" ".join(cur))
        return "\n\n".join(out)


def _m(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _v(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _w(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def _r_glow_draw(world: World) -> list[str]:
    out: list[str] = []
    gift = world.get("gift")
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.id == gift.held_by:
            continue
        if _m(gift, "brightness") < THRESHOLD:
            continue
        if ent.location != gift.location:
            continue
        sig = ("draw", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _v(ent, "distance_to_gift", 1)
        _w(ent, "awe", 1)
        _w(ent, "wonder", 1)
        out.append(f"{ent.noun().capitalize()} could not look away from the divine glow.")
    return out


def _r_greedy_hold(world: World) -> list[str]:
    out: list[str] = []
    gift = world.get("gift")
    holder = world.get(gift.held_by) if gift.held_by else None
    if holder is None:
        return out
    if _wants_to_keep(holder):
        sig = ("greed", holder.id)
        if sig not in world.fired:
            world.fired.add(sig)
            _w(holder, "greed", 1)
            _w(holder, "fear", 1)
            out.append(f"{holder.noun().capitalize()} clutched the gift as if the light might leave.")
    return out


def _r_sharing_calms(world: World) -> list[str]:
    out: list[str] = []
    gift = world.get("gift")
    holder = world.get(gift.held_by) if gift.held_by else None
    if holder is None:
        return out
    if _m(holder, "shared") < THRESHOLD:
        return out
    sig = ("share", holder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _w(holder, "trust", 1)
    _w(holder, "relief", 1)
    _w(holder, "devotion", 1)
    _w(holder, "greed", -1)
    gift.meters["brightness"] = max(0.0, gift.meters.get("brightness", 0.0) - 0.5)
    out.append("The glow softened when the gift was given to more than one pair of hands.")
    return out


CAUSAL_RULES = [_r_glow_draw, _r_greedy_hold, _r_sharing_calms]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def _wants_to_keep(holder: Entity) -> bool:
    return _m(holder, "greed") >= THRESHOLD and _m(holder, "trust") < THRESHOLD


def flashback(world: World, elder: Entity, hero: Entity, gift: Gift) -> None:
    world.flashback_used = True
    world.say(
        f"{elder.noun().capitalize()} remembered an older night, when a divine flame "
        f"was shared among the first singers so no one stood in the dark."
    )
    world.say(
        f"That memory was like a hidden drumbeat, and {hero.noun()} felt the old kindness "
        f"wake inside {hero.pronoun('possessive')} chest."
    )
    _w(hero, "trust", 1)
    _w(hero, "wonder", 1)


def tell(world: World, hero: Entity, elder: Entity) -> None:
    hero.location = world.place.id
    elder.location = world.place.id
    gift = world.get("gift")
    gift.location = world.place.id

    world.say(
        f"On a dusk-washed hill, {hero.noun()} found the {gift.label}, a {gift.phrase} "
        f"left where the stones still remembered the gods."
    )
    _w(hero, "awe", 1)
    _w(hero, "wonder", 1)
    _v(gift, "brightness", 2)
    world.say(
        f"The {gift.label} shone with {gift.glow}, and its {gift.mesmeric} light "
        f"made every face grow still."
    )

    world.para()
    world.say(
        f"{hero.noun().capitalize()} wanted to keep the {gift.label} close, because the shining "
        f"felt proud and warm in {hero.pronoun('possessive')} hands."
    )
    gift.held_by = hero.id
    _v(hero, "carried", 1)
    _w(hero, "greed", 1)
    _w(hero, "fear", 1)
    propagate(world)

    world.say(
        f"At once, the nearby people leaned closer, as if the whole hill had been pulled by one star."
    )

    world.para()
    world.say(
        f"{elder.noun().capitalize()} stepped nearer and spoke softly: "
        f'"Child, this light was never meant to belong to one heart alone."'
    )
    flashback(world, elder, hero, gift)

    world.say(
        f"{hero.noun().capitalize()} looked again at the hill and understood that the divine thing "
        f"was brightest when it was not trapped."
    )
    _w(hero, "shared", 1)
    gift.held_by = None
    propagate(world)

    world.say(
        f"Then {hero.noun()} began to {gift.share_action}, and the {gift.label} passed from palm to palm."
    )
    gift.held_by = hero.id
    world.say(
        f"{hero.noun().capitalize()} let the others touch it first, and the glow spread out like honey on bread."
    )
    _w(hero, "shared", 1)
    propagate(world)

    world.para()
    world.say(
        f"In the end, the {gift.label} did not vanish. It glimmered in many hands at once, and the hill "
        f"looked like it had caught a small piece of heaven."
    )
    hero.memes["greed"] = max(0.0, hero.memes.get("greed", 0.0) - 1)
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    gift.meters["brightness"] = max(0.0, gift.meters.get("brightness", 0.0) - 0.25)


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(SETTINGS, params.place)
    gift = _safe_lookup(GIFTS, params.gift)
    world = World(place, gift)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        location=place.id,
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=params.elder_type,
        label="the elder",
        location=place.id,
    ))
    gift_ent = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift.label,
        phrase=gift.phrase,
        location=place.id,
        meters={"brightness": 0.0},
        memes={"awe": 0.0},
    ))
    world.facts = {"hero": hero, "elder": elder, "gift": gift_ent, "place": place, "gift_cfg": gift}
    tell(world, hero, elder)
    return world


SETTINGS = {
    "hill": Place(id="hill", label="the moonlit hill", sacred=True, echo="The stones remembered prayers."),
    "grove": Place(id="grove", label="the cedar grove", sacred=True, echo="Leaves held old songs."),
    "shore": Place(id="shore", label="the silver shore", sacred=True, echo="Waves repeated the names of the dawn."),
}

GIFTS = {
    "lantern": Gift(
        id="lantern",
        label="lantern of dawn",
        phrase="divine glass lantern",
        glow="golden dawn-fire",
        mesmeric="mesmerizing",
        share_action="sing the blessing again",
        shared_image="its light spreading through many cupped hands",
        location="hill",
        tags={"divine", "light", "sharing", "flashback", "myth", "mesmerize"},
    ),
    "cup": Gift(
        id="cup",
        label="cup of stars",
        phrase="divine silver cup",
        glow="star-white shimmer",
        mesmeric="mesmerizing",
        share_action="pour a sip for each traveler",
        shared_image="each sip catching a star",
        location="grove",
        tags={"divine", "sharing", "flashback", "myth"},
    ),
    "thread": Gift(
        id="thread",
        label="thread of the sky",
        phrase="divine blue thread",
        glow="blue fire",
        mesmeric="mesmerizing",
        share_action="tie the thread around each wrist",
        shared_image="many wrists shining with one blue line",
        location="shore",
        tags={"divine", "sharing", "flashback", "myth", "mesmerize"},
    ),
}

HERO_NAMES = ["Mira", "Tavi", "Nikos", "Sera", "Iris", "Cleo", "Arin", "Pella"]
HERO_TYPES = ["girl", "boy"]
ELDER_TYPES = ["priestess", "priest", "woman", "man"]


@dataclass
class StoryConfig:
    setting: str
    gift: str
    hero_name: str
    hero_type: str
    elder_type: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, place in SETTINGS.items():
        for gid, gift in GIFTS.items():
            if gift.location == sid and {"divine", "sharing", "flashback", "myth"} <= gift.tags:
                combos.append((sid, gid))
    return combos


def explain_rejection(place: Place, gift: Gift) -> str:
    return f"(No story: the {gift.label} does not belong on {place.label}, so the myth would lose its natural sacred scene.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "gift", None):
        if (getattr(args, "place", None), getattr(args, "gift", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "gift", None) is None or c[1] == getattr(args, "gift", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, gift = rng.choice(filtered)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    elder_type = getattr(args, "elder_type", None) or rng.choice(ELDER_TYPES)
    return StoryParams(place=place, gift=gift, hero_name=hero_name, hero_type=hero_type, elder_type=elder_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    gift = _safe_fact(world, f, "gift_cfg")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short myth for a child about a divine {gift.label} and a lesson about sharing at {place.label}.',
        f"Tell a gentle myth where {hero.label} finds a {gift.phrase} and learns why its {gift.mesmeric} glow should be shared.",
        f'Write a story with a flashback to an older sacred gift, using the words "divine" and "sharing".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    gift = _safe_fact(world, f, "gift")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What did {hero.label} find at {place.label}?",
            answer=f"{hero.label} found the {gift.label}, a {gift.phrase}, on {place.label}.",
        ),
        QAItem(
            question=f"Why did the {gift.label} feel dangerous at first?",
            answer=f"It felt dangerous because its {gift.mesmeric} glow made everyone stare, and {hero.label} wanted to keep it close instead of sharing it.",
        ),
        QAItem(
            question=f"What old memory did {elder.noun()} bring back?",
            answer=f"{elder.noun().capitalize()} remembered an older night when a divine flame was shared among the first singers so no one stood in the dark.",
        ),
        QAItem(
            question=f"How did {hero.label} change by the end?",
            answer=f"{hero.label} stopped clinging to the gift and chose sharing, so the light could live in many hands at once.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does divine mean?",
            answer="Divine means holy, godlike, or coming from the gods.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story remembers something that happened before now.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, hold, or enjoy something too.",
        ),
        QAItem(
            question="What does mesmerize mean?",
            answer="To mesmerize someone is to hold their attention so strongly that they can hardly look away.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:6} ({e.type:9}) loc={e.location} meters={meters} memes={memes}")
    lines.append(f"  flashback_used={world.flashback_used}")
    return "\n".join(lines)


ASP_RULES = r"""
% A gift is mesmerizing when its brightness is high.
mesmerizing(G) :- gift(G), bright(G,B), B >= 1.

% Sharing resolves greed.
resolved(H) :- shared(H), not greedy(H).

% A mythic story is valid when it has a sacred place and a divine gift.
valid(P, G) :- place(P), sacred(P), gift(G), divine(G), shares(G).

#show valid/2.
#show mesmerizing/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.sacred:
            lines.append(asp.fact("sacred", pid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("divine", gid))
        lines.append(asp.fact("shares", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about a divine gift, mesmerized eyes, sharing, and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
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


CURATED = [
    StoryParams(place="hill", gift="lantern", hero_name="Mira", hero_type="girl", elder_type="priestess"),
    StoryParams(place="grove", gift="cup", hero_name="Tavi", hero_type="boy", elder_type="man"),
    StoryParams(place="shore", gift="thread", hero_name="Sera", hero_type="girl", elder_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, gift in combos:
            print(f"  {place:6} {gift}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.gift} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
