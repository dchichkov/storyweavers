#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/marriage_apparel_suspense_magic_bad_ending_pirate.py
=============================================================================================================

A small pirate-tale story world about a wedding, fancy apparel, and a magic
misstep that ends badly.

Premise:
- A pirate wants to marry at a windy seaside place.
- The pirate treasures special apparel for the wedding.
- A spell promises a dazzling change, but it also threatens the outfit.
- Suspense builds as the warning grows clearer.
- The magic goes wrong, the apparel is ruined, and the day ends in sorrow.

The world is built as a tiny simulation with:
- typed entities
- physical meters
- emotional memes
- forward-chained causal rules
- a Python reasonableness gate plus an ASP twin

This file is standalone and uses only the stdlib plus the shared
storyworlds/results.py container module. ASP helpers are imported lazily.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    apparel: object | None = None
    hero: object | None = None
    partner: object | None = None
    def _m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def _e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "bride", "girl", "mother"}
        male = {"man", "groom", "boy", "father", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def title(self) -> str:
        return self.label or self.type
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
class Apparel:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"woman", "man"})
    at_risk_of: set[str] = field(default_factory=set)
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
    verb: str
    warning: str
    effect: str
    risk: str
    splash: str
    can_ruin: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _has_threshold(ent: Entity, key: str) -> bool:
    return ent.meters.get(key, 0.0) >= THRESHOLD or ent.memes.get(key, 0.0) >= THRESHOLD


def _covered(world: World, actor: Entity, region: str) -> bool:
    return any(g.protective and region in g.covers for g in world.worn_items(actor))


def _magic_burn(world: World) -> list[str]:
    out: list[str] = []
    magic: Magic = _safe_fact(world, world.facts, "magic")
    for actor in world.characters():
        if actor.memes.get("spellcast", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in magic.can_ruin:
                continue
            if _covered(world, actor, item.region):
                continue
            sig = ("burn", actor.id, item.id, magic.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _add_meter(item, "ruined", 1.0)
            _add_meter(item, "torn", 1.0)
            _add_mem(actor, "heartache", 1.0)
            out.append(f"{item.title} came apart under the spell.")
    return out


def _witness_dread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("heartache", 0.0) < THRESHOLD:
            continue
        sig = ("dread", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_mem(actor, "dread", 1.0)
        out.append(f"{actor.title} felt a cold knot in {actor.pronoun('possessive')} chest.")
    return out


def _marriage_fails(world: World) -> list[str]:
    out: list[str] = []
    bride = _safe_fact(world, world.facts, "bride")
    groom = _safe_fact(world, world.facts, "groom")
    apparel = _safe_fact(world, world.facts, "apparel")
    if _has_threshold(apparel, "ruined") and ("fail", bride.id, groom.id) not in world.fired:
        world.fired.add(("fail", bride.id, groom.id))
        bride.memes["marriage"] = 0.0
        groom.memes["marriage"] = 0.0
        out.append("__bad_ending__")
    return out


CAUSAL_RULES = [_magic_burn, _witness_dread, _marriage_fails]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__bad_ending__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(setting: Setting, apparel: Apparel, magic: Magic) -> bool:
    return (
        "marriage" in setting.affords
        and apparel.region in magic.can_ruin
        and apparel.label in {"wedding coat", "lace sash", "silk hat", "bride's veil"}
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid, s in SETTINGS.items():
        for aid, a in APPAREL.items():
            for mid, m in MAGICS.items():
                if valid_combo(s, a, m):
                    out.append((sid, aid, mid))
    return out


def fear_story(world: World, hero: Entity, partner: Entity, apparel: Entity, magic: Magic) -> None:
    _add_mem(hero, "suspense", 1.0)
    _add_mem(partner, "suspense", 1.0)
    world.say(
        f"On the salt wind, {hero.title} and {partner.title} stood with a wedding to make."
    )
    world.say(
        f"{hero.title} loved {hero.pronoun('possessive')} {apparel.label}, because it was the sort of apparel that made a pirate feel bold."
    )
    world.say(
        f"But the old {magic.label} promised a brighter look than any lantern could give."
    )


def warn_story(world: World, hero: Entity, partner: Entity, apparel: Entity, magic: Magic) -> None:
    _add_mem(hero, "worry", 1.0)
    _add_mem(partner, "worry", 1.0)
    world.say(
        f'"{magic.warning}," {partner.title} said. "It may leave the {apparel.label} in tatters."'
    )


def cast_story(world: World, caster: Entity, apparel: Entity, magic: Magic) -> None:
    _add_mem(caster, "spellcast", 1.0)
    _add_meter(caster, "magic", 1.0)
    world.say(
        f"Still, {caster.title} lifted the charm and cast it with a shiver of hope."
    )
    world.say(
        f"The spell swirled with {magic.splash}, and the {apparel.label} flashed like a star on the sea."
    )
    propagate(world, narrate=True)


def bad_ending(world: World, hero: Entity, partner: Entity, apparel: Entity) -> None:
    _add_mem(hero, "dread", 1.0)
    _add_mem(partner, "dread", 1.0)
    world.say(
        f"When the glow faded, the {apparel.label} was torn and ruined, and the wedding could not go on."
    )
    world.say(
        f"{hero.title} stood very still by the mast while {partner.title} gathered the broken cloth against {partner.pronoun('possessive')} heart."
    )
    world.say(
        f"The ship creaked on through the dusk, and the happy day sailed away with the tide."
    )


def tell(world: World) -> World:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    partner: Entity = _safe_fact(world, world.facts, "partner")
    apparel: Entity = _safe_fact(world, world.facts, "apparel")
    magic: Magic = _safe_fact(world, world.facts, "magic")

    fear_story(world, hero, partner, apparel, magic)
    world.para()
    warn_story(world, hero, partner, apparel, magic)
    world.say(
        f"{hero.title} looked at {partner.title}, at the moonlit deck, and at the {apparel.label}."
    )
    world.say(
        f"Then {hero.title} chose the spell anyway, because the glitter of magic was hard to refuse."
    )
    world.para()
    cast_story(world, hero, apparel, magic)
    if apparel.meters.get("ruined", 0.0) >= THRESHOLD:
        world.para()
        bad_ending(world, hero, partner, apparel)
    world.facts["resolved_badly"] = apparel.meters.get("ruined", 0.0) >= THRESHOLD
    return world


SETTINGS = {
    "deck": Setting(place="the deck of a small pirate ship", affords={"marriage"}),
    "cove": Setting(place="a moonlit cove", affords={"marriage"}),
    "harbor": Setting(place="the lantern harbor", affords={"marriage"}),
}

APPAREL = {
    "coat": Apparel(
        id="coat",
        label="wedding coat",
        phrase="a fine wedding coat with brass buttons",
        region="torso",
        genders={"man"},
        at_risk_of={"spark"},
    ),
    "veil": Apparel(
        id="veil",
        label="bride's veil",
        phrase="a pale bride's veil stitched with sea-foam lace",
        region="head",
        genders={"woman"},
        at_risk_of={"spark"},
    ),
    "sash": Apparel(
        id="sash",
        label="lace sash",
        phrase="a lace sash tied with a silver knot",
        region="torso",
        genders={"woman"},
        at_risk_of={"spark"},
    ),
    "hat": Apparel(
        id="hat",
        label="silk hat",
        phrase="a silk hat with a bright feather",
        region="head",
        at_risk_of={"spark"},
    ),
}

MAGICS = {
    "glitter": Magic(
        id="glitter",
        label="glitter spell",
        verb="make the clothes shine",
        warning="A glitter spell can glitter too hard and burn the fine cloth",
        effect="brightened",
        risk="burn",
        splash="gold sparks",
        can_ruin={"torso", "head"},
        tags={"magic", "spark"},
    ),
    "moonwash": Magic(
        id="moonwash",
        label="moonwash charm",
        verb="wash the cloth in moonlight",
        warning="A moonwash charm can strip the dye and weaken the stitches",
        effect="washed",
        risk="fray",
        splash="silver mist",
        can_ruin={"torso", "head"},
        tags={"magic", "spell"},
    ),
}

SETTLEMENT_NAMES = ["Mira", "Nell", "Rosa", "Ivy", "Pearl", "Ada", "June", "Luna"]
PIRATE_NAMES = ["Crow", "Black Finn", "Red Jack", "Salt Tom", "Moss Ben", "One-Eye Ned"]


@dataclass
class StoryParams:
    setting: str
    apparel: str
    magic: str
    hero: str
    partner: str
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
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with marriage, apparel, suspense, magic, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--apparel", choices=APPAREL)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--hero")
    ap.add_argument("--partner")
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
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "apparel", None) is None or c[1] == getattr(args, "apparel", None))
        and (getattr(args, "magic", None) is None or c[2] == getattr(args, "magic", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_id, apparel_id, magic_id = rng.choice(list(filtered))
    apparel = APPAREL[apparel_id]
    hero = getattr(args, "hero", None) or rng.choice(PIRATE_NAMES)
    partner = getattr(args, "partner", None) or rng.choice(SETTLEMENT_NAMES)
    return StoryParams(setting=setting_id, apparel=apparel_id, magic=magic_id, hero=hero, partner=partner)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    apparel_cfg = APPAREL[params.apparel]
    magic = _safe_lookup(MAGICS, params.magic)

    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="pirate", label=params.hero))
    partner = world.add(Entity(id="partner", kind="character", type="woman", label=params.partner))
    apparel = world.add(Entity(
        id="apparel",
        type="apparel",
        label=apparel_cfg.label,
        phrase=apparel_cfg.phrase,
        owner=hero.id,
        caretaker=partner.id,
        region=apparel_cfg.region,
        plural=apparel_cfg.plural,
    ))
    apparel.worn_by = hero.id

    world.facts.update(hero=hero, partner=partner, apparel=apparel, magic=magic, setting=setting)

    tell(world)

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
        "Write a short pirate tale about a wedding, fancy apparel, and a magic mistake that ends badly.",
        f"Tell a suspenseful pirate story where {f['hero'].label} wants marriage at {f['setting'].place} and worries about the {f['apparel'].label}.",
        f"Write a child-facing pirate story that includes {f['apparel'].label} and {f['magic'].label}, then ends with a ruined wedding day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, apparel, magic = f["hero"], f["partner"], f["apparel"], f["magic"]
    return [
        QAItem(
            question=f"Who wanted the marriage in this pirate story?",
            answer=f"{hero.label} wanted the marriage, and {partner.label} was the one standing beside {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"Why was the {apparel.label} important?",
            answer=f"It was the wedding apparel, so {hero.label} wanted it to stay fine and bright for the marriage.",
        ),
        QAItem(
            question=f"What made the story suspenseful?",
            answer=f"The suspense came from the warning that {magic.label} could hurt the {apparel.label}, so everyone feared what the spell might do.",
        ),
    ] + (
        [
            QAItem(
                question="What happened at the end?",
                answer=f"The spell ruined the {apparel.label}, and the wedding ended badly instead of happily.",
            )
        ] if world.facts.get("resolved_badly") else []
    )


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is marriage?",
            answer="Marriage is when two people make a promise to be partners and share a life together.",
        ),
        QAItem(
            question="What is apparel?",
            answer="Apparel means clothes or things you wear, like a coat, hat, or dress.",
        ),
        QAItem(
            question="Why can magic be risky in a story?",
            answer="Magic can be risky because a spell may do more than the caster wanted, and that can cause trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(deck). setting(cove). setting(harbor).
affords(deck, marriage). affords(cove, marriage). affords(harbor, marriage).

apparel(coat). apparel(veil). apparel(sash). apparel(hat).
worn_on(coat, torso). worn_on(sash, torso). worn_on(veil, head). worn_on(hat, head).

magic(glitter). magic(moonwash).
can_ruin(glitter, torso). can_ruin(glitter, head).
can_ruin(moonwash, torso). can_ruin(moonwash, head).

valid(Place, Apparel, Magic) :-
    affords(Place, marriage),
    worn_on(Apparel, Region),
    can_ruin(Magic, Region).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, "marriage"))
    for aid, a in APPAREL.items():
        lines.append(asp.fact("apparel", aid))
        lines.append(asp.fact("worn_on", aid, a.region))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        for region in sorted(m.can_ruin):
            lines.append(asp.fact("can_ruin", mid, region))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(setting: Setting, apparel: Apparel, magic: Magic) -> str:
    if "marriage" not in setting.affords:
        return "(No story: that place does not support a marriage scene.)"
    if apparel.region not in magic.can_ruin:
        return f"(No story: {magic.label} cannot reasonably threaten the {apparel.label}.)"
    return "(No story: this combination is not a good fit for the pirate wedding premise.)"


def valid_or_raise(args: argparse.Namespace) -> None:
    if getattr(args, "setting", None) and getattr(args, "apparel", None) and getattr(args, "magic", None):
        if not valid_combo(_safe_lookup(SETTINGS, getattr(args, "setting", None)), APPAREL[getattr(args, "apparel", None)], _safe_lookup(MAGICS, getattr(args, "magic", None))):
            pass


CURATED = [
    StoryParams(setting="deck", apparel="coat", magic="glitter", hero="Crow", partner="Mira"),
    StoryParams(setting="cove", apparel="veil", magic="moonwash", hero="Red Jack", partner="Pearl"),
]


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, apparel, magic) combos:\n")
        for place, apparel, magic in combos:
            print(f"  {place:8} {apparel:8} {magic:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                valid_or_raise(args)
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
            header = f"### {p.hero} and {p.partner} at {p.setting} with {p.apparel}/{p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
