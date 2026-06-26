#!/usr/bin/env python3
"""
storyworlds/worlds/form_al_sunburned_gumbo_bad_ending_myth.py
==============================================================

A tiny myth-style story world with a bad ending: a formal little quest,
a sunburned hero, and a pot of gumbo that does not survive the day.

Seed inspiration:
- form-al
- sunburned
- gumbo

The world is built as a small simulation with meters and memes:
- heat can burn skin and darken tempers
- travel without shade can make a hero sunburned
- carrying gumbo in the heat can spoil the meal
- the ending is intentionally bad: the feast is lost and the hero returns
  ashamed, hungry, and empty-handed
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    pot: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hero", "boy", "man", "messenger"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str = "the sun-road"
    shade: str = "the cypress shade"
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
class Ritual:
    id: str
    verb: str
    gerund: str
    rush: str
    heat: float
    spoil: str
    keyword: str
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
class Prize:
    label: str
    phrase: str
    type: str
    care_key: str = "spoiled"
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
        self.story: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _hero_name(name: str) -> str:
    return name.replace("-", " ")


@dataclass
class StoryParams:
    setting: str
    ritual: str
    prize: str
    name: str
    title: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "sun-road": Setting(place="the sun-road", shade="the cypress shade", affords={"walk", "march"}),
    "festival-field": Setting(place="the festival field", shade="the reed awning", affords={"procession"}),
    "river-steps": Setting(place="the river steps", shade="the stone arch", affords={"walk"}),
}

RITUALS = {
    "procession": Ritual(
        id="procession",
        verb="carry the holy gumbo to the altar",
        gerund="carrying the holy gumbo",
        rush="hurry toward the altar",
        heat=2.0,
        spoil="turned sour",
        keyword="gumbo",
    ),
    "walk": Ritual(
        id="walk",
        verb="walk the long sun-road",
        gerund="walking the long sun-road",
        rush="run ahead into the light",
        heat=1.5,
        spoil="spoiled in the heat",
        keyword="sun",
    ),
    "march": Ritual(
        id="march",
        verb="march before the bronze doors",
        gerund="marching before the bronze doors",
        rush="push on toward the gates",
        heat=1.8,
        spoil="wilted",
        keyword="form-al",
    ),
}

PRIZES = {
    "gumbo": Prize(label="gumbo", phrase="a pot of gumbo with crab and okra", type="pot"),
    "banner": Prize(label="banner", phrase="a formal red banner", type="banner"),
    "mask": Prize(label="mask", phrase="a sun-painted mask", type="mask"),
}

HEROES = ["Form-al", "Ione", "Tamar", "Belen", "Orin"]
TITLES = ["keeper", "herald", "priest", "messenger", "child"]

KNOWLEDGE = {
    "gumbo": [("What is gumbo?", "Gumbo is a thick, savory stew that is often cooked in a pot and eaten warm.")],
    "sun": [("What does too much sun do?", "Too much sun can make skin hot, dry, and burned.")],
    "form-al": [("What does formal mean?", "Formal means neat, careful, and fit for an important ceremony.")],
    "myth": [("What is a myth?", "A myth is a very old story about powerful people, strange events, and big lessons.")],
    "spoiled": [("What does spoiled food smell like?", "Spoiled food can smell sour or rotten, and it is not safe to eat.")],
}


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_sunburn(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.meters.get("sun", 0.0) < THRESHOLD:
        return out
    if hero.meters.get("burned", 0.0) >= THRESHOLD:
        return out
    hero.meters["burned"] = 1.0
    hero.memes["ache"] = hero.memes.get("ache", 0.0) + 1.0
    out.append(f"{hero.id} felt the fire of the day bite into {hero.pronoun('possessive')} skin.")
    return out


def _r_spoil(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    pot = world.get("prize")
    if hero.meters.get("heat", 0.0) < THRESHOLD:
        return out
    if pot.meters.get("spoiled", 0.0) >= THRESHOLD:
        return out
    pot.meters["spoiled"] = 1.0
    pot.meters["lost"] = 1.0
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1.0
    out.append(f"The gumbo went sour before it could reach the feast.")
    return out


RULES = [Rule("sunburn", _r_sunburn), Rule("spoil", _r_spoil)]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
    for s in out:
        world.say(s)
    return out


def tell(setting: Setting, ritual: Ritual, prize: Prize, hero_name: str, title: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="hero", label=title))
    hero.id = _hero_name(hero_name)
    world.entities.pop("hero")
    world.entities[hero.id] = hero
    pot = world.add(Entity(id="prize", type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id))
    hero.meters["sun"] = 0.0
    hero.meters["heat"] = 0.0
    hero.meters["burned"] = 0.0
    hero.memes["duty"] = 1.0
    pot.meters["spoiled"] = 0.0

    world.say(f"Long ago, in the {setting.place}, there lived a {title} named {hero.id}.")
    world.say(f"{hero.id} was form-al in every step and loved the sound of solemn bells.")
    world.say(f"On that day, {hero.id} was chosen to {ritual.verb}.")

    world.para()
    world.say(f"At dawn, {hero.id} set out from {setting.place} with {prize.phrase}.")
    world.say(f"The way was bright, and the only shade lay under {setting.shade}, far behind.")
    hero.meters["sun"] += ritual.heat
    hero.meters["heat"] += ritual.heat
    world.say(f"{hero.id} would not turn aside, for the duty was older than fear.")
    propagate(world)

    world.para()
    world.say(f"At noon, {hero.id} kept {hero.pronoun('possessive')} face toward the road and hurried on.")
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    hero.meters["heat"] += 1.0
    hero.meters["sun"] += 1.0
    propagate(world)

    world.para()
    if pot.meters.get("spoiled", 0.0) >= THRESHOLD:
        world.say(
            f"When {hero.id} at last reached the altar, the priests lifted the lid and drew back."
        )
        world.say(
            f"The gumbo was sour, the steam had gone weak, and the feast was broken."
        )
        world.say(
            f"{hero.id} stood sunburned and silent beneath the hard sky, while the drums fell quiet."
        )
    else:
        world.say(
            f"But the day was cruel, and even the pot could not be saved."
        )

    world.facts.update(
        hero=hero,
        prize=pot,
        ritual=ritual,
        setting=setting,
        bad_ending=True,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for r_id in setting.affords:
            for p_id in PRIZES:
                if r_id == "procession" and p_id == "gumbo":
                    combos.append((s_id, r_id, p_id))
                elif r_id in {"walk", "march"} and p_id != "gumbo":
                    combos.append((s_id, r_id, p_id))
    return combos


def explain_rejection(setting: str, ritual: str, prize: str) -> str:
    return (
        f"(No story: {ritual} at {setting} with {prize} does not fit the mythic rule. "
        f"Try the holy gumbo on the procession, or a different prize for a walk.)"
    )


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, world.facts, "prize")  # type: ignore[assignment]
    ritual: Ritual = _safe_fact(world, world.facts, "ritual")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, world.facts, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who carried the {prize.label} in the story?",
            answer=f"{hero.id} carried the {prize.label} through {setting.place}, because {hero.pronoun('subject')} was chosen for the solemn task.",
        ),
        QAItem(
            question=f"Why did {hero.id} become sunburned?",
            answer=f"{hero.id} became sunburned because the road was hot and {hero.pronoun('subject')} stayed in the open sun too long.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=f"The ending was bad because the gumbo spoiled before the feast, so the meal was lost and {hero.id} came back ashamed.",
        ),
        QAItem(
            question=f"What was {hero.id} supposed to do?",
            answer=f"{hero.id} was supposed to {ritual.verb}, but the harsh sun ruined the day instead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"myth", "sun", "spoiled", "form-al", "gumbo"}
    out: list[QAItem] = []
    for tag in ["myth", "form-al", "sun", "gumbo", "spoiled"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    ritual: Ritual = _safe_fact(world, world.facts, "ritual")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, world.facts, "prize")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, world.facts, "setting")  # type: ignore[assignment]
    return [
        f"Write a short myth about {hero.id}, a form-al child who must {ritual.verb} at {setting.place}.",
        f"Tell a gentle but tragic myth in which {prize.label} is carried through the sun and ends badly.",
        f"Write a small legend with the words form-al, sunburned, and gumbo.",
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
bad_ending(H) :- sunburned(H), spoiled(P), carries(H,P).
sunburned(H) :- heat(H, X), X >= 2.
spoiled(P) :- heat_on(P), sun(too_hot).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for rid, r in RITUALS.items():
        lines.append(asp.fact("ritual", rid))
        lines.append(asp.fact("heat_on", rid))
        lines.append(asp.fact("verb", rid, r.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    lines.append(asp.fact("sun", "too_hot"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show bad_ending/1."))
    bad = set(asp.atoms(model, "bad_ending"))
    expected = {("hero",)}
    if bad == expected:
        print("OK: ASP parity check passed.")
    else:
        print(f"Mismatch: {bad} != {expected}")
        return 1

    params = StoryParams(setting="festival-field", ritual="procession", prize="gumbo", name="Form-al", title="messenger")
    sample = generate(params)
    if "sour" not in sample.story and "broken" not in sample.story:
        print("Mismatch: generated story does not exercise the bad ending.")
        return 1
    print("OK: generated story exercise passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic story world with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TITLES)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "ritual", None) is None or c[1] == getattr(args, "ritual", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not filtered:
        if getattr(args, "setting", None) and getattr(args, "ritual", None) and getattr(args, "prize", None):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, ritual, prize = rng.choice(list(filtered))
    name = getattr(args, "name", None) or rng.choice(HEROES)
    title = getattr(args, "title", None) or rng.choice(TITLES)
    return StoryParams(setting=setting, ritual=ritual, prize=prize, name=name, title=title)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(RITUALS, params.ritual), _safe_lookup(PRIZES, params.prize), params.name, params.title)
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
    StoryParams(setting="festival-field", ritual="procession", prize="gumbo", name="Form-al", title="messenger"),
    StoryParams(setting="sun-road", ritual="march", prize="banner", name="Ione", title="herald"),
    StoryParams(setting="river-steps", ritual="walk", prize="mask", name="Tamar", title="keeper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_ending/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show bad_ending/1."))
        print(asp.atoms(model, "bad_ending"))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
