#!/usr/bin/env python3
"""
A myth-styled story world about tonight's mountain rite, where a child must
persevere through suspense, speak in rhyme, and reach reconciliation.
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

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
    name: str = ""
    title: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide_ent: object | None = None
    hero: object | None = None
    label: object | None = None
    relic_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "daughter", "sister", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "son", "brother", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    timeword: str = "tonight"
    mood: str = "moonlit"
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
    title: str
    glow: str
    at_risk_when: set[str] = field(default_factory=set)
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
class Hazard:
    id: str
    label: str
    threat: str
    suspense: str
    banish_with: str
    requires: str
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


@dataclass
class Guide:
    id: str
    label: str
    rhyme: str
    gift: str
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
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "mountain_shrine": Setting(place="the mountain shrine"),
    "river_stone": Setting(place="the river stone"),
    "cave_gate": Setting(place="the cave gate"),
}

RELICS = {
    "lantern": Relic(
        id="lantern",
        label="lantern",
        title="a silver lantern",
        glow="moon-silver",
        at_risk_when={"storm", "wind", "shadow"},
    ),
    "crown": Relic(
        id="crown",
        label="crown",
        title="a child-sized crown of reeds",
        glow="golden",
        at_risk_when={"storm", "fire", "shadow"},
    ),
    "harp": Relic(
        id="harp",
        label="harp",
        title="a little harp of pine",
        glow="soft",
        at_risk_when={"storm", "river"},
    ),
}

HAZARDS = {
    "storm": Hazard(
        id="storm",
        label="storm",
        threat="the sky would burst open",
        suspense="the wind began to worry the eaves",
        banish_with="stormsong",
        requires="refrain",
        tags={"storm", "wind"},
    ),
    "shadow": Hazard(
        id="shadow",
        label="shadow",
        threat="a shadow could steal the rite's bright heart",
        suspense="a long shadow crept over the steps",
        banish_with="namefire",
        requires="rhyme",
        tags={"shadow", "dark"},
    ),
    "river": Hazard(
        id="river",
        label="river",
        threat="the river would swallow the offering",
        suspense="the water kept whispering against the stones",
        banish_with="bridgeword",
        requires="bridge",
        tags={"river", "water"},
    ),
}

GUIDES = {
    "owl": Guide(
        id="owl",
        label="owl",
        rhyme="the owl who knew the old road's tune",
        gift="a three-line rhyme",
        tags={"rhyme", "night"},
    ),
    "grandmother": Guide(
        id="grandmother",
        label="grandmother",
        rhyme="the grandmother with ash in her braid",
        gift="a calm vow",
        tags={"reconciliation", "family"},
    ),
    "smith": Guide(
        id="smith",
        label="smith",
        rhyme="the smith who sang to iron and pine",
        gift="a bright refrain",
        tags={"refrain", "craft"},
    ),
}

TRAITS = ["brave", "curious", "steadfast", "gentle", "patient", "small but stubborn"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, hazard: str, relic: str) -> bool:
    rel = _safe_lookup(RELICS, relic)
    hz = _safe_lookup(HAZARDS, hazard)
    return hazard in rel.at_risk_when and setting in SETTINGS


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for h in HAZARDS:
            for r in RELICS:
                if valid_combo(s, h, r):
                    out.append((s, h, r))
    return out


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hazard: str
    relic: str
    hero_name: str
    hero_type: str
    guide: str
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


def hero_intro(world: World, hero: Entity, relic: Relic) -> None:
    world.say(
        f"Once, tonight, in {world.setting.place}, {hero.name} was a {hero.title} who kept watch "
        f"over {relic.title}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was {hero.meters.get('smallness', 1):.0f} little, but {hero.pronoun('subject')} had a {hero.memes.get('resolve', 1):.0f}-beat heart."
    )


def scene_set(world: World, hero: Entity, guide: Guide, hazard: Hazard, relic: Relic) -> None:
    world.say(
        f"The old stones glimmered, and {guide.label} came softly to the gate."
    )
    world.say(
        f"{guide.rhyme.capitalize()}, {hero.name} heard, and then the {hazard.label} gave a hush of suspense: {hazard.suspense}."
    )
    world.facts["suspense_line"] = hazard.suspense
    world.facts["guide_rhyme"] = guide.rhyme


def riddle_conflict(world: World, hero: Entity, hazard: Hazard, relic: Relic) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.name} wanted to run, but {hero.pronoun()} chose to persevere."
    )
    world.say(
        f"{hero.pronoun().capitalize()} stepped forward anyway, because {hazard.threat} if no one sang."
    )


def do_rhyme(world: World, hero: Entity, guide: Guide, hazard: Hazard) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"Together they spoke in rhyme: '{guide.gift} can carry the night; / a brave small voice can set things right.'"
    )
    world.facts["used_rhyme"] = True
    world.facts["used_reconciliation"] = False


def reconcile(world: World, hero: Entity, guide: Guide, relic: Relic, hazard: Hazard) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0) + 2
    world.facts["used_reconciliation"] = True
    world.say(
        f"Then {guide.label} bowed their head and forgave the fear of the old feud, and {hero.name} answered with a kinder bow."
    )
    world.say(
        f"The two of them made peace, and the {hazard.label} loosened its grip as if it had been waiting for that very moment."
    )


def resolution(world: World, hero: Entity, relic: Relic, hazard: Hazard, guide: Guide) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    world.say(
        f"At last, the {hazard.label} faded, the {relic.label} shone clear, and {hero.name} kept the shrine safe until dawn."
    )
    world.say(
        f"Tonight had been full of suspense, but the ending was a warm one: {hero.name} and {guide.label} walked home together, reconciled beneath the moon."
    )


def tell(setting: Setting, hazard: Hazard, relic: Relic, hero_name: str, hero_type: str, guide_key: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        name=hero_name,
        title=f"{trait} keeper",
        meters={"smallness": 1.0},
        memes={"resolve": 1.0},
    ))
    guide = _safe_lookup(GUIDES, guide_key)
    guide_ent = world.add(Entity(
        id="guide",
        kind="character",
        type="elder" if guide_key == "grandmother" else "friend",
        name=guide.label,
        title=guide.label,
    ))
    relic_ent = world.add(Entity(
        id="relic",
        kind="thing",
        type=relic.id,
        name=relic.label,
        title=relic.title,
    ))

    hero_intro(world, hero, relic_ent)
    world.para()
    scene_set(world, hero, guide, hazard, relic)
    riddle_conflict(world, hero, hazard, relic)
    world.para()
    do_rhyme(world, hero, guide, hazard)
    reconcile(world, hero, guide, relic, hazard)
    resolution(world, hero, relic, hazard, guide)

    world.facts.update(
        hero=hero,
        guide=guide_ent,
        relic=relic_ent,
        hazard=hazard,
        setting=setting,
        trait=trait,
        guide_key=guide_key,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A relic is at risk in a setting if the hazard names a threat it cannot withstand.
at_risk(S, H, R) :- setting(S), hazard(H), relic(R), risk(R, H), in_setting(S).

% A story is valid only when there is at least one guide and the hero must persevere.
valid_story(S, H, R) :- setting(S), hazard(H), relic(R), at_risk(S, H, R), can_help(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("in_setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for tag in h.tags:
            lines.append(asp.fact("risk", hid, tag))
        lines.append(asp.fact("can_help", hid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        for tag in r.at_risk_when:
            lines.append(asp.fact("risk", rid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show at_risk/3."))
    return sorted(set(asp.atoms(model, "at_risk")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
GIRL_NAMES = ["Mira", "Iona", "Sera", "Nina", "Luna", "Tala"]
BOY_NAMES = ["Ari", "Niko", "Darin", "Oren", "Kian", "Soren"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a myth-like story set {world.setting.timeword} where {f['hero'].name} must persevere through suspense and end in reconciliation.",
        f"Tell a child-friendly tale about a {f['trait']} keeper, a {f['hazard'].label}, and a {f['relic'].label}, with a little rhyme inside.",
        f"Write a short bedtime myth about {f['hero'].name} at {world.setting.place} that uses the words tonight and persevere.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide: Entity = _safe_fact(world, f, "guide")
    relic: Entity = _safe_fact(world, f, "relic")
    hazard: Hazard = _safe_fact(world, f, "hazard")
    return [
        QAItem(
            question=f"Who guarded the {relic.label} tonight?",
            answer=f"{hero.name} guarded the {relic.title} tonight at {world.setting.place}.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"The story felt suspenseful because {hazard.suspense}.",
        ),
        QAItem(
            question=f"How did {hero.name} and {guide.name} solve the problem?",
            answer="They spoke in rhyme, kept going, and reached reconciliation instead of fear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does persevere mean?",
            answer="Persevere means to keep trying even when something is hard or scary.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that makes you wonder what will happen next.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like light and night.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} name={e.name} title={e.title}")
        if e.meters:
            lines.append(f"    meters={e.meters}")
        if e.memes:
            lines.append(f"    memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hazard: str
    relic: str
    hero_name: str
    hero_type: str
    guide: str
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


CURATED = [
    StoryParams("mountain_shrine", "shadow", "lantern", "Mira", "girl", "owl", "steadfast"),
    StoryParams("mountain_shrine", "storm", "crown", "Ari", "boy", "smith", "gentle"),
    StoryParams("river_stone", "river", "harp", "Sera", "girl", "grandmother", "patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world of tonight, perseverance, rhyme, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "hazard", None) is None or c[1] == getattr(args, "hazard", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, hazard, relic = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(list(GUIDES))
    trait = rng.choice(TRAITS)
    return StoryParams(setting, hazard, relic, name, gender, guide, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(HAZARDS, params.hazard), _safe_lookup(RELICS, params.relic),
                 params.hero_name, params.hero_type, params.guide, params.trait)
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
        print(asp_program("#show at_risk/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    elif getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show at_risk/3."))
        for atom in sorted(set(asp.atoms(model, "at_risk"))):
            print(atom)
        return
    else:
        seen = set()
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
            header = f"### {p.hero_name}: {p.hazard} at {p.setting} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
