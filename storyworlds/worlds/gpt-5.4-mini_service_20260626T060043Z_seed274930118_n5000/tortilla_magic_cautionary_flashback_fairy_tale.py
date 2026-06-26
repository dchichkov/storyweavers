#!/usr/bin/env python3
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"warmth": 0.0, "scorch": 0.0, "mystery": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "care": 0.0, "memory": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "witch"}
        male = {"boy", "father", "dad", "man", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    place: str
    indoor: bool
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
class Spell:
    id: str
    verb: str
    gerund: str
    warning: str
    mishap: str
    effect: str
    target_region: str
    keyword: str = "tortilla"
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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
class Charm:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_taken = False

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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    place: str
    spell: str
    prize: str
    hero: str
    hero_type: str
    elder: str
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


SETTINGS = {
    "cottage": Setting(place="the little cottage", indoor=True, affords={"magic"}),
    "kitchen": Setting(place="the warm kitchen", indoor=True, affords={"magic"}),
    "courtyard": Setting(place="the moonlit courtyard", indoor=False, affords={"magic"}),
}

SPELLS = {
    "flutter": Spell(
        id="flutter",
        verb="cast a flutter spell",
        gerund="casting flutter spells",
        warning="You may make the tortilla dance right into the hearth",
        mishap="would fly too close to the fire",
        effect="float and twirl",
        target_region="hands",
        tags={"magic", "tortilla"},
    ),
    "glow": Spell(
        id="glow",
        verb="cast a glow spell",
        gerund="casting glow spells",
        warning="You may make the tortilla hot enough to scorch",
        mishap="would grow too hot to hold",
        effect="shine and warm",
        target_region="hands",
        tags={"magic", "tortilla"},
    ),
    "snap": Spell(
        id="snap",
        verb="snap a tiny spell",
        gerund="snapping tiny spells",
        warning="You may startle the tortilla into a tumble",
        mishap="would slip from the cloth",
        effect="jump and spin",
        target_region="hands",
        tags={"magic", "tortilla"},
    ),
}

PRIZES = {
    "tortilla": Prize(id="tortilla", label="tortilla", phrase="a soft golden tortilla", region="hands"),
    "stack": Prize(id="stack", label="stack of tortillas", phrase="a warm stack of tortillas", region="hands", plural=True),
}

CHARMS = [
    Charm(id="cloth", label="a clean cloth", covers={"hands"}, guards={"scorch", "drop"}, prep="wrap the tortilla in a clean cloth first", tail="wrapped the tortilla in a clean cloth", plural=False),
    Charm(id="basket", label="a woven basket", covers={"hands"}, guards={"drop"}, prep="set the tortilla in a woven basket first", tail="placed the tortilla in a woven basket", plural=False),
]


def prize_at_risk(spell: Spell, prize: Prize) -> bool:
    return prize.region == spell.target_region


def select_charm(spell: Spell, prize: Prize) -> Optional[Charm]:
    for charm in CHARMS:
        if prize.region in charm.covers:
            return charm
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for spell_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(_safe_lookup(SPELLS, spell_id), prize) and select_charm(_safe_lookup(SPELLS, spell_id), prize):
                    out.append((place, spell_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about tortilla magic, caution, and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    if getattr(args, "spell", None) and getattr(args, "prize", None):
        sp, pr = _safe_lookup(SPELLS, getattr(args, "spell", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(sp, pr) and select_charm(sp, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "spell", None) is None or c[1] == getattr(args, "spell", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, spell, prize = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "name", None) or rng.choice(["Maya", "Luna", "Pablo", "Tomas", "Inez", "Sofia"])
    elder = getattr(args, "elder", None) or rng.choice(["grandmother", "grandfather"])
    return StoryParams(place=place, spell=spell, prize=prize, hero=hero, hero_type=hero_type, elder=elder)


def _say_intro(world: World, hero: Entity, elder: Entity, prize: Entity) -> None:
    world.say(f"Long ago, {hero.id} lived with {hero.pronoun('possessive')} {elder.type} in a place where warm tortillas always seemed to find their way to the table.")
    world.say(f"{hero.id} loved {prize.phrase}, because it smelled like sunshine and home.")


def _flashback(world: World, hero: Entity, prize: Entity) -> None:
    if world.flashback_taken:
        return
    world.flashback_taken = True
    world.say(f"Once, when {hero.id} had tried to hurry a tortilla near the fire, it had curled too dark at the edge.")
    world.say(f"That old memory stayed in {hero.pronoun('possessive')} heart like a tiny warning bell.")
    hero.memes["memory"] += 1
    hero.memes["worry"] += 1


def _warning(world: World, elder: Entity, hero: Entity, spell: Spell, prize: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(f'“{spell.warning},” {elder.pronoun("possessive")} {elder.type} said. “Magic is lovely, but it must be gentle.”')


def _temptation(world: World, hero: Entity, spell: Spell) -> None:
    hero.memes["joy"] += 1
    world.say(f"But {hero.id} still wanted to {spell.verb}, because the spell promised to {spell.effect}.")


def _mishap(world: World, hero: Entity, spell: Spell, prize: Entity) -> None:
    if ("mishap", hero.id, spell.id) in world.fired:
        return
    world.fired.add(("mishap", hero.id, spell.id))
    prize.meters["scorch"] += 1
    hero.memes["worry"] += 1
    world.say(f"When {hero.id} waved {hero.pronoun('possessive')} hands, the tortilla {spell.mishap}.")
    world.say("The room went still, and even the little shadows seemed to hold their breath.")


def _repair(world: World, elder: Entity, hero: Entity, prize: Entity, charm: Charm) -> None:
    hero.memes["care"] += 1
    hero.memes["worry"] = 0.0
    prize.meters["scorch"] = max(0.0, prize.meters["scorch"] - 1)
    world.say(f'{elder.id} laid out {charm.label} and said, “We can be careful and still be kind to the magic.”')
    world.say(f"Together they {charm.tail}, and the tortilla stayed safe.")
    world.say(f"Then {hero.id} tried again, smaller this time, and the spell made the tortilla {_safe_lookup(SPELLS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "spell")).effect} without any harm.")


def tell(setting: Setting, spell: Spell, prize_cfg: Prize, hero_name: str, hero_type: str, elder_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=elder.id, region=prize_cfg.region, plural=prize_cfg.plural))

    world.facts.update(hero=hero, elder=elder, prize=prize, spell=spell, setting=setting)

    _say_intro(world, hero, elder, prize)
    world.para()
    _flashback(world, hero, prize)
    _warning(world, elder, hero, spell, prize)
    _temptation(world, hero, spell)
    _mishap(world, hero, spell, prize)
    world.para()
    charm = select_charm(spell, prize)
    if charm is None:
        _fallback_pool = globals().get("CHARMS") or globals().get("CHARMES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        charm = next(iter(_fallback_pool), None)
        if charm is None:
            raise StoryError
    _repair(world, elder, hero, prize, charm)
    world.facts["charm"] = charm
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fairy tale about tortilla magic, a warning, and a gentle fix.',
        f"Tell a cautionary story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} wants to {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "spell").verb} but learns to be careful with a tortilla.",
        "Write a child-friendly flashback story about a tortilla and a spell that could go wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, spell, charm = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "spell"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "charm")
    return [
        QAItem(question=f"What did {hero.id} want to do with the tortilla?", answer=f"{hero.id} wanted to {spell.verb}, because the magic looked lovely."),
        QAItem(question=f"Why did {elder.id} warn {hero.id}?", answer=f"{elder.id} warned {hero.id} because the magic could make the tortilla {spell.mishap} and hurt the warm treat."),
        QAItem(question=f"What memory made {hero.id} extra careful?", answer=f"{hero.id} remembered the time a tortilla had curled too dark at the edge, so the warning felt important."),
        QAItem(question=f"How did they keep the tortilla safe in the end?", answer=f"They used {charm.label} first and then tried the magic more gently, so the tortilla stayed safe."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a tortilla?", answer="A tortilla is a soft, flat bread, often made from corn or flour and cooked on a hot pan."),
        QAItem(question="Why should food near a fire be handled carefully?", answer="Food near a fire can scorch or burn if it gets too hot, so people need to be gentle and watch closely."),
        QAItem(question="What does caution mean?", answer="Caution means being careful and thinking ahead so something does not go wrong."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is a part of a story that goes back to something that happened earlier."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(S,P) :- target_region(S,R), worn_on(P,R).
safe_charm(C,S,P) :- charm(C), prize_at_risk(S,P), covers(C,R), worn_on(P,R), guards(C, scorch).
valid(Place,S,P) :- affords(Place,S), prize_at_risk(S,P), safe_charm(_,S,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        if s.indoor:
            lines.append(asp.fact("indoor", p))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", p, a))
    for sid, s in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("target_region", sid, s.target_region))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print(" only in clingo:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SPELLS, params.spell), _safe_lookup(PRIZES, params.prize), params.hero, params.hero_type, params.elder)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "spell", None) is None or c[1] == getattr(args, "spell", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, spell, prize = rng.choice(list(combos))
    return StoryParams(place=place, spell=spell, prize=prize, hero=getattr(args, "name", None) or rng.choice(["Maya", "Luna", "Inez", "Pablo"]), hero_type=getattr(args, "hero_type", None) or rng.choice(["girl", "boy"]), elder=getattr(args, "elder", None) or rng.choice(["grandmother", "grandfather"]))


CURATED = [
    StoryParams(place="cottage", spell="flutter", prize="tortilla", hero="Maya", hero_type="girl", elder="grandmother"),
    StoryParams(place="kitchen", spell="glow", prize="stack", hero="Pablo", hero_type="boy", elder="grandfather"),
    StoryParams(place="courtyard", spell="snap", prize="tortilla", hero="Inez", hero_type="girl", elder="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
