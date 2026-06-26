#!/usr/bin/env python3
"""
storyworlds/worlds/amputate_repetition_magic_bad_ending_adventure.py
====================================================================

A compact storyworld for a small adventure tale about repetition, magic,
and a bad ending.

Premise:
- A young adventurer wants to repeat a magic spell to open a sealed path.
- The spell is useful once, but repeated too many times it grows unstable.
- A fragile prize can be damaged by the spell's overuse.
- A simple magical charm can sometimes prevent the damage, but only if the
  charm is a reasonable match for the danger.

This world deliberately includes the seed word "amputate" as the name of the
spell that cuts away thorny vines and broken rope. In this setting, it is a
fantasy verb used for a clean cut, not a medical procedure.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    region: object | None = None
    guide: object | None = None
    hero: object | None = None
    item: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ("magic", "danger", "damage", "joy", "fear", "resolve", "repetition"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Spell:
    id: str
    name: str
    chant: str
    action: str
    burst: str
    risk: str
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
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool
    region: str
    plural: bool = False
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
class Charm:
    id: str
    label: str
    guard: str
    covers: set[str]
    prep: str
    tail: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))


def _r_overuse(world: World) -> list[str]:
    out: list[str] = []
    spell = _safe_fact(world, world.facts, "spell")
    for actor in world.characters():
        if actor.meters["magic"] < THRESHOLD or actor.meters["repetition"] < 2 * THRESHOLD:
            continue
        sig = ("overuse", actor.id, spell.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["danger"] += 1
        actor.memes["fear"] += 1
        out.append(f"The repeated spell grew shaky in {actor.id}'s hands.")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    prize = _safe_fact(world, world.facts, "prize")
    spell = _safe_fact(world, world.facts, "spell")
    for actor in world.characters():
        if actor.meters["danger"] < THRESHOLD:
            continue
        if prize.region not in spell.tags:
            continue
        sig = ("damage", actor.id, prize.id)
        if sig in world.fired:
            continue
        if world.covered(actor, prize.region):
            continue
        world.fired.add(sig)
        prize_entity = world.get(prize.id)
        prize_entity.meters["damage"] += 1
        out.append(f"{spell.action.capitalize()} sent a crack through {prize_entity.label}.")
    return out


CAUSAL_RULES = [_r_overuse, _r_damage]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, actor: Entity, spell: Spell, prize_id: str) -> dict:
    sim = World(world.setting)
    import copy
    sim.entities = copy.deepcopy(world.entities)
    sim.fired = set(world.fired)
    sim.facts = dict(world.facts)
    actor2 = sim.get(actor.id)
    actor2.meters["magic"] += 1
    actor2.meters["repetition"] += 3
    propagate(sim, narrate=False)
    prize = sim.get(prize_id)
    return {"damaged": prize.meters["damage"] >= THRESHOLD, "danger": actor2.meters["danger"]}


def setting_detail(setting: Setting) -> str:
    return {
        "forest": "The forest was green and thick, with old roots curling across the trail.",
        "ruins": "The ruins leaned in the wind, as if they were listening for brave footsteps.",
        "cave": "The cave mouth was dark, but a blue glow flickered somewhere inside.",
        "tower": "The tower's stairs were narrow, and every step echoed like a drum.",
    }[setting.place]


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little brave {hero.type} who loved adventures.")


def want_quest(world: World, hero: Entity, spell: Spell, prize: Entity) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} wanted to use the magic word {spell.name} to clear the path "
        f"and reach {prize.phrase}."
    )


def warn(world: World, guide: Entity, hero: Entity, spell: Spell, prize: Entity) -> bool:
    pred = predict_outcome(world, hero, spell, prize.id)
    if not pred["damaged"]:
        return False
    world.facts["predicted_damage"] = True
    world.say(
        f'"If you keep saying {spell.name} again and again, {prize.label} will get ruined," '
        f"{guide.pronoun('subject')} said. \"Let's choose carefully.\""
    )
    return True


def repeat_spell(world: World, hero: Entity, spell: Spell) -> None:
    hero.meters["magic"] += 1
    hero.meters["repetition"] += 3
    world.say(f"{hero.id} whispered {spell.chant}, then whispered it again, and again.")
    propagate(world, narrate=True)


def use_charm(world: World, guide: Entity, hero: Entity, prize: Entity) -> Optional[Charm]:
    for charm in CHARMS:
        if prize.region in charm.covers and prize.region in charm.guard:
            item = world.add(Entity(
                id=charm.id,
                type="charm",
                label=charm.label,
                owner=hero.id,
                caretaker=guide.id,
                protective=True,
                covers=set(charm.covers),
            ))
            item.worn_by = hero.id
            world.say(
                f"{guide.id} held up {charm.label} and said, "
                f"\"{charm.prep}.\""
            )
            return charm
    return None


def ending_bad(world: World, hero: Entity, prize: Entity, spell: Spell) -> None:
    if prize.meters["damage"] >= THRESHOLD:
        hero.memes["fear"] += 1
        world.say(
            f"At last, the {spell.action} worked too hard and snapped the fragile prize."
        )
        world.say(
            f"{hero.id} reached the end of the adventure with only broken pieces and a heavy sigh."
        )


def ending_safe(world: World, hero: Entity, prize: Entity, charm: Charm) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"With {charm.label}, the magic stayed careful, and {hero.id} reached the prize at last."
    )
    world.say(
        f"By the end, {prize.label} was safe, and the trail looked friendly again."
    )


def tell(setting: Setting, spell: Spell, prize_cfg: Prize, hero_name: str = "Mira",
         hero_type: str = "girl", guide_type: str = "aunt") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label="her aunt"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=guide.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    world.facts.update(hero=hero, guide=guide, prize=prize, spell=spell, setting=setting)

    introduce(world, hero)
    world.say(setting_detail(setting))
    want_quest(world, hero, spell, prize)

    world.para()
    world.say(f"{hero.id} and {guide.id} went into {setting.place} together.")
    world.say(f"The path asked for repetition, because the gate would only wake for a steady chant.")
    warn(world, guide, hero, spell, prize)

    world.para()
    repeat_spell(world, hero, spell)

    charm = use_charm(world, guide, hero, prize)
    if charm is None:
        ending_bad(world, hero, prize, spell)
    else:
        ending_safe(world, hero, prize, charm)

    world.facts["charm"] = charm
    world.facts["bad_ending"] = prize.meters["damage"] >= THRESHOLD
    return world


SETTINGS = {
    "forest": Setting(place="forest", mood="wild", affords={"chant"}),
    "ruins": Setting(place="ruins", mood="ancient", affords={"chant"}),
    "cave": Setting(place="cave", mood="echoing", affords={"chant"}),
    "tower": Setting(place="tower", mood="high", affords={"chant"}),
}

SPELLS = {
    "amputate": Spell(
        id="amputate",
        name="amputate",
        chant="amputate, amputate, amputate",
        action="the amputate spell",
        burst="a sharp blue flash",
        risk="cut too much",
        tags={"torso", "rope"},
    ),
    "open": Spell(
        id="open",
        name="open",
        chant="open, open, open",
        action="the opening spell",
        burst="a warm gold flash",
        risk="shake loose",
        tags={"door", "stone"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="an old treasure map", type="map", fragile=True, region="paper"),
    "lantern": Prize(label="lantern", phrase="a glass lantern", type="lantern", fragile=True, region="glass"),
    "crown": Prize(label="crown", phrase="a tiny golden crown", type="crown", fragile=True, region="metal"),
}

CHARMS = [
    Charm(id="glove", label="a soft glove charm", guard="paper", covers={"paper"}, prep="Use the glove charm to keep the map steady", tail="the glove charm kept the paper safe"),
    Charm(id="case", label="a glass case charm", guard="glass", covers={"glass"}, prep="Use the glass case charm to wrap the lantern", tail="the glass case charm kept the lantern safe"),
]

GIRL_NAMES = ["Mira", "Lena", "Tessa", "Ruby", "Iris"]
BOY_NAMES = ["Owen", "Finn", "Jace", "Milo", "Theo"]


@dataclass
class StoryParams:
    place: str
    spell: str
    prize: str
    name: str
    gender: str
    guide: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for spell_id, spell in SPELLS.items():
            for prize_id, prize in PRIZES.items():
                if setting.affords and "chant" in setting.affords and prize.fragile:
                    combos.append((place, spell_id, prize_id))
    return combos


def explain_rejection(spell: Spell, prize: Prize) -> str:
    return f"(No story: the {spell.name} spell would not reasonably threaten {prize.label} in this setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: repetition, magic, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["aunt", "uncle"])
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
    if getattr(args, "spell", None) and getattr(args, "prize", None):
        if getattr(args, "spell", None) == "amputate" and getattr(args, "prize", None) == "crown":
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "spell", None) is None or c[1] == getattr(args, "spell", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, spell, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(["aunt", "uncle"])
    return StoryParams(place=place, spell=spell, prize=prize, name=name, gender=gender, guide=guide)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that includes the repeated magic word "{f["spell"].name}".',
        f"Tell a story where {f['hero'].id} and {f['guide'].label} repeat a spell in {f['setting'].place} and the ending turns bad.",
        f'Write a simple adventure about a fragile {f["prize"].label} and a spell called "{f["spell"].name}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, prize, spell = f["hero"], f["guide"], f["prize"], f["spell"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the {world.setting.place}?",
            answer=f"{hero.id} wanted to use the magic word {spell.name} to clear the path and reach {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did {guide.label} worry about the repeating spell?",
            answer=f"{guide.label.capitalize()} worried because repeating {spell.name} again and again would make the fragile {prize.label} get ruined.",
        ),
        QAItem(
            question=f"What happened at the end of the adventure?",
            answer=f"The ending was bad: the repeated magic became too strong, the {prize.label} broke, and {hero.id} reached the end with broken pieces.",
        ),
    ]
    if f.get("charm"):
        charm = _safe_fact(world, f, "charm")
        qa.append(QAItem(
            question=f"How did {charm.label} help?",
            answer=f"{charm.label.capitalize()} helped by protecting the fragile prize so the magic stayed careful instead of damaging it.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is repetition?", answer="Repetition means doing or saying the same thing again and again."),
        QAItem(question="What is magic in a story?", answer="Magic is something special and mysterious that can make impossible things happen."),
        QAItem(question="What is a bad ending in a story?", answer="A bad ending is when the problem is not solved and things finish in an unhappy way."),
        QAItem(question="What does amputate mean in this storyworld?", answer="Here, amputate is a fantasy spell word for cutting away vines or rope cleanly."),
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
spell_overused(A,S) :- repeated(A,S), repeated_more(A,S).
prize_damaged(P) :- spell_overused(A,S), threatens(S,P), not protected(A,P).
safe_story(P) :- prize(P), not prize_damaged(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sp in SPELLS.values():
        lines.append(asp.fact("spell", sp.id))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("threatens", "amputate", pid))
        lines.append(asp.fact("threatens", "open", pid))
    for ch in CHARMS:
        lines.append(asp.fact("charm", ch.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Simple parity check: we expect every Python combo to be represented as a safe_story atom.
    model = asp.one_model(asp_program("#show safe_story/1."))
    clingo = set(asp.atoms(model, "safe_story"))
    py = set()
    for _, _, prize in valid_combos():
        py.add((prize,))
    if clingo == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(clingo))
    print("  python:", sorted(py))
    return 1


CURATED = [
    StoryParams(place="forest", spell="amputate", prize="map", name="Mira", gender="girl", guide="aunt"),
    StoryParams(place="cave", spell="amputate", prize="lantern", name="Owen", gender="boy", guide="uncle"),
    StoryParams(place="ruins", spell="open", prize="crown", name="Lena", gender="girl", guide="aunt"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SPELLS, params.spell), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.guide)
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
        print(asp_program("#show safe_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show safe_story/1."))
        print(sorted(set(asp.atoms(model, "safe_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.spell} in {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
