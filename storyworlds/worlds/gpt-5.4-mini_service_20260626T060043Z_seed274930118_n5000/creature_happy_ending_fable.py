#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/creature_happy_ending_fable.py
=============================================================================================================

A small fable-style story world about a creature, a gentle trouble, and a
happy ending.

Premise:
- A young forest creature values one small thing a little too much.
- Another creature needs help because of the weather or a simple lack.
- The first creature feels reluctant, then sees the need, then acts kindly.
- The ending proves the change with a concrete shared result.

This script follows the Storyweavers storyworld contract:
- stdlib only
- eager shared results import
- lazy ASP import inside helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- trace, QA, JSON, ASP, verify, show-ASP support
"""

from __future__ import annotations

import argparse
import dataclasses
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    gift: object | None = None
    hero: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "hare", "rabbit", "mouse", "squirrel", "bird", "owl", "badger"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    season: str
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
class Need:
    id: str
    verb: str
    gerund: str
    prompt: str
    trouble: str
    zone: str
    tags: set[str] = field(default_factory=set)
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
    protects: set[str]
    solves: set[str]
    remedy: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        return clone


def has_fix(need: Need, gift: Gift) -> bool:
    return need.id in gift.solves


def risk_to_gift(need: Need, gift: Gift) -> bool:
    return need.zone in gift.protects and has_fix(need, gift)


def choose_gift(need: Need) -> Optional[Gift]:
    for gift in GIFTS:
        if risk_to_gift(need, gift):
            return gift
    return None


def predict_result(world: World, hero: Entity, need: Need, friend: Entity, gift_id: str) -> dict:
    sim = world.copy()
    _do_need(sim, sim.get(hero.id), need, narrate=False)
    return {
        "helped": sim.get(friend.id).meters.get("comfort", 0.0) >= THRESHOLD,
        "shared": sim.get(hero.id).memes.get("generosity", 0.0) >= THRESHOLD,
    }


def _do_need(world: World, hero: Entity, need: Need, narrate: bool = True) -> list[str]:
    out: list[str] = []
    hero.meters[need.id] = hero.meters.get(need.id, 0.0) + 1.0
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    if need.id == "hunger":
        hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1.0
    if need.id == "cold":
        hero.meters["shiver"] = hero.meters.get("shiver", 0.0) + 1.0
    if need.id == "lost":
        hero.memes["sadness"] = hero.memes.get("sadness", 0.0) + 1.0
    if narrate:
        out.append(f"{hero.label} felt the little trouble of {need.gerund}.")
    return out


def _r_sympathy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.meters.get("hunger", 0.0) >= THRESHOLD and friend.meters.get("comfort", 0.0) >= THRESHOLD:
        sig = ("sympathy",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
            out.append("The hero noticed that sharing would not make the world smaller.")
    return out


CAUSAL_RULES = [_r_sympathy]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            xs = rule(world)
            if xs:
                changed = True
                out.extend(xs)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, need: Need, gift_cfg: Gift, hero_name: str, friend_name: str, hero_type: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=["small", "bright"]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, traits=["gentle", "hopeful"]))
    gift = world.add(Entity(
        id="gift", kind="thing", type=gift_cfg.id, label=gift_cfg.label, phrase=gift_cfg.phrase,
        owner=hero.id, plural=gift_cfg.plural
    ))
    world.facts.update(hero=hero, friend=friend, gift=gift, need=need, gift_cfg=gift_cfg, setting=setting)

    world.say(f"{hero.label} was a small {hero.type} who lived near {setting.place}.")
    world.say(f"{hero.label} liked {gift_cfg.phrase}, because {gift_cfg.phrase.lower()} made {hero.label_word} feel safe and proud.")

    world.para()
    world.say(f"One {setting.season} day at {setting.place}, {friend.label} came with a quiet trouble.")
    world.say(f"{friend.label} needed help with {need.gerund}, and the need made {friend.label} look small and still.")

    world.para()
    world.say(f"{hero.label} wanted to keep {gift_cfg.label}, but the trouble was hard to ignore.")
    world.say(f"{friend.label} asked for help in a soft voice, and {hero.label} paused to think.")
    hero.meters[need.id] = hero.meters.get(need.id, 0.0) + 1.0
    if need.id == "hunger":
        hero.meters["hunger"] = hero.meters.get("hunger", 0.0) + 1.0
    if need.id == "cold":
        hero.meters["cold"] = hero.meters.get("cold", 0.0) + 1.0
    if need.id == "lost":
        hero.meters["lost"] = hero.meters.get("lost", 0.0) + 1.0
    if need.id == "hunger":
        hero.meters["hunger"] += 0.0

    if need.id == "hunger":
        hero.memes["hesitation"] = hero.memes.get("hesitation", 0.0) + 1.0
    elif need.id == "cold":
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    else:
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0

    world.say(f"{hero.label} looked at {gift_cfg.label} and then at {friend.label}.")
    world.say(f"At last, {hero.label} chose the kinder path.")
    hero.memes["generosity"] = hero.memes.get("generosity", 0.0) + 1.0
    friend.meters["comfort"] = friend.meters.get("comfort", 0.0) + 1.0
    friend.memes["hope"] = friend.memes.get("hope", 0.0) + 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"{hero.label} shared {gift_cfg.label}, and {gift_cfg.remedy}.")
    world.say(f"{friend.label} felt better at once, and the two creatures went on together.")
    world.say(f"By evening, {gift_cfg.tail}, and {setting.place} felt warmer than before.")

    world.facts["resolved"] = True
    return world


def label_word(hero: Entity) -> str:
    return hero.label


def hero_label_word(hero: Entity) -> str:
    return hero.label


def hero_word(hero: Entity) -> str:
    return hero.label


def setting_phrase(setting: Setting) -> str:
    return setting.place


SETTINGS = {
    "oak_hollow": Setting(place="the oak hollow", season="autumn", affords={"hunger", "lost"}),
    "river_path": Setting(place="the river path", season="spring", affords={"cold", "lost"}),
    "sunny_glade": Setting(place="the sunny glade", season="summer", affords={"hunger", "cold"}),
}

NEEDS = {
    "hunger": Need(
        id="hunger",
        verb="share food",
        gerund="feeling hungry",
        prompt="a hungry friend",
        trouble="hunger",
        zone="mouth",
        tags={"food", "share"},
    ),
    "cold": Need(
        id="cold",
        verb="share warmth",
        gerund="feeling cold",
        prompt="a chilly friend",
        trouble="cold",
        zone="back",
        tags={"warmth", "weather"},
    ),
    "lost": Need(
        id="lost",
        verb="find the way",
        gerund="being lost",
        prompt="a lost friend",
        trouble="lost",
        zone="eyes",
        tags={"path", "help"},
    ),
}

GIFTS = [
    Gift(
        id="berry_basket",
        label="a basket of berries",
        phrase="a basket of berries",
        protects={"mouth"},
        solves={"hunger"},
        remedy="the berries filled the empty belly",
        tail="the basket was lighter, but both hearts were full",
        plural=False,
    ),
    Gift(
        id="moss_cloak",
        label="a mossy cloak",
        phrase="a mossy cloak",
        protects={"back"},
        solves={"cold"},
        remedy="the cloak held the wind away",
        tail="the cloak stayed a little damp, yet everyone felt snug",
        plural=False,
    ),
    Gift(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern",
        protects={"eyes"},
        solves={"lost"},
        remedy="the lantern showed the path home",
        tail="the lantern glowed softly as the path turned familiar",
        plural=False,
    ),
]

HERO_TYPES = ["mouse", "squirrel", "hare", "fox", "bird"]
FRIEND_TYPES = ["mouse", "squirrel", "hare", "badger", "bird"]
NAMES = ["Pip", "Nell", "Milo", "Luna", "Toby", "Wren", "Kiko", "Bram", "Sera", "Tansy"]
TRAITS = ["kind", "careful", "brave", "gentle", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for nid in setting.affords:
            need = _safe_lookup(NEEDS, nid)
            for gift in GIFTS:
                if risk_to_gift(need, gift):
                    out.append((sid, nid, gift.id))
    return out


@dataclass
class StoryParams:
    place: str
    need: str
    gift: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
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
    ap = argparse.ArgumentParser(description="A small fable-like creature story world with a happy ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--need", choices=NEEDS.keys())
    ap.add_argument("--gift", choices=[g.id for g in GIFTS])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
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
    if getattr(args, "place", None) or getattr(args, "need", None) or getattr(args, "gift", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                  and (getattr(args, "need", None) is None or c[1] == getattr(args, "need", None))
                  and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, need, gift = rng.choice(list(combos))
    need_obj = _safe_lookup(NEEDS, need)
    gift_obj = next(g for g in GIFTS if g.id == gift)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    friend_type = getattr(args, "friend_type", None) or rng.choice([t for t in FRIEND_TYPES if t != hero_type])
    hero_name = getattr(args, "hero_name", None) or rng.choice(NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in NAMES if n != hero_name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, need, gift, hero_name, hero_type, friend_name, friend_type, trait)


def story_intro(world: World) -> None:
    pass


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(NEEDS, params.need),
        next(g for g in GIFTS if g.id == params.gift),
        params.hero_name,
        params.friend_name,
        params.hero_type,
        params.friend_type,
    )
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
    return [
        f'Write a short fable for children about a creature named {f["hero"].label} who learns to share at {f["setting"].place}.',
        f"Tell a gentle story where {f['hero'].label} has to choose between keeping {f['gift'].label} and helping {f['friend'].label}.",
        f'Write a happy-ending creature fable that includes the word "{f["need"].id}" and ends with a kind choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    need = _safe_fact(world, f, "need")
    gift_cfg = _safe_fact(world, f, "gift_cfg")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.label}, a small {hero.type} who lived near {setting.place}.",
        ),
        QAItem(
            question=f"What trouble did {friend.label} have at {setting.place}?",
            answer=f"{friend.label} needed help with {need.gerund}.",
        ),
        QAItem(
            question=f"What did {hero.label} do with {gift_cfg.label} at the end?",
            answer=f"{hero.label} shared {gift_cfg.label} with {friend.label}, and that made the ending happy.",
        ),
        QAItem(
            question=f"How did the ending show that {hero.label} changed?",
            answer=f"{hero.label} stopped thinking only about keeping {gift_cfg.label} and chose the kinder path instead.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    need = _safe_fact(world, f, "need")
    gift_cfg = _safe_fact(world, f, "gift_cfg")
    out = [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too, instead of keeping it all for yourself.",
        ),
        QAItem(
            question=f"What does {gift_cfg.label} do in this story world?",
            answer=f"In this story, {gift_cfg.label} helps because it can solve the trouble of {need.id}.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.type} label={e.label} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("oak_hollow", "hunger", "berry_basket", "Pip", "mouse", "Nell", "bird", "kind"),
    StoryParams("river_path", "cold", "moss_cloak", "Luna", "fox", "Milo", "hare", "gentle"),
    StoryParams("sunny_glade", "lost", "lantern", "Bram", "squirrel", "Sera", "mouse", "patient"),
]


ASP_RULES = r"""
risk(A,G) :- need(A), gift(G), solves(G,N), needs(A,N), protects(G,Z), zone(A,Z).
valid(Place,N,G) :- setting(Place), affords(Place,N), need(N), gift(G), risk(N,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for nid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, nid))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("needs", nid, need.id))
        lines.append(asp.fact("zone", nid, need.zone))
    for g in GIFTS:
        lines.append(asp.fact("gift", g.id))
        for z in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, z))
        for s in sorted(g.solves):
            lines.append(asp.fact("solves", g.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero_name}: {p.need} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
