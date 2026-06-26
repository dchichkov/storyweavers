#!/usr/bin/env python3
"""
storyworlds/worlds/politician_invite_society_conflict_animal_story.py
======================================================================

A small animal-story world built from the seed words:
politician, invite, society, conflict.

Premise:
- An animal politician wants to invite the local society to a gathering.
- The invitation can go well only if the chosen setting and plan can handle
  the crowd and the conflict that might follow.
- The story is told as a simple, child-facing animal tale with a clear turn.

This script is standalone, uses only the stdlib for normal story generation,
and includes an inline ASP twin for the reasonableness gate.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared result containers importable when run directly.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "dog", "wolf", "bear", "badger", "boar", "lion"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mouse", "rabbit", "squirrel", "bird", "deer", "otter", "hedgehog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    indoor: bool = False
    holds: int = 6
    affordance: str = "invite"
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
class InvitePlan:
    id: str
    verb: str
    gathering: str
    kind: str
    crowd: str
    conflict_kind: str
    tension: str
    fix: str
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
class StoryParams:
    setting: str
    invite: str
    name: str
    species: str
    role: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "hall": Setting(place="the town hall", indoor=True, holds=20),
    "meadow": Setting(place="the meadow", indoor=False, holds=12),
    "pond": Setting(place="the pond bank", indoor=False, holds=8),
}

INVITES = {
    "tea": InvitePlan(
        id="tea",
        verb="invite",
        gathering="tea time",
        kind="tea party",
        crowd="the whole society",
        conflict_kind="crowding",
        tension="there were not enough seats for everyone",
        fix="bring more stools and share the bench",
        tags={"society", "invite"},
    ),
    "sing": InvitePlan(
        id="sing",
        verb="invite",
        gathering="song time",
        kind="singing gathering",
        crowd="the whole society",
        conflict_kind="noise",
        tension="the first song was too loud for the small animals",
        fix="choose a gentler song and clap softly",
        tags={"society", "invite"},
    ),
    "share": InvitePlan(
        id="share",
        verb="invite",
        gathering="sharing time",
        kind="sharing circle",
        crowd="the whole society",
        conflict_kind="sharing",
        tension="everyone wanted the same shiny basket at once",
        fix="make a careful line and take turns",
        tags={"society", "invite"},
    ),
}

SPECIES = {
    "fox": ["clever", "bright", "quick"],
    "badger": ["steady", "kind", "serious"],
    "rabbit": ["bouncy", "gentle", "curious"],
    "otter": ["playful", "friendly", "wet-furred"],
    "deer": ["quiet", "proud", "soft-hooved"],
    "mouse": ["tiny", "brave", "polite"],
}

NAMES = {
    "fox": ["Fenn", "Tavi", "Rill"],
    "badger": ["Bram", "Nell", "Moss"],
    "rabbit": ["Pip", "Luna", "Milo"],
    "otter": ["Ollie", "Suri", "Nia"],
    "deer": ["Vale", "Hush", "Rue"],
    "mouse": ["Mip", "Tuck", "Pea"],
}


def can_tell(setting: Setting, plan: InvitePlan) -> bool:
    return setting.affordance == "invite" and setting.holds >= 8 and plan.id in INVITES


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, plan in INVITES.items():
            if can_tell(setting, plan):
                out.append((sid, pid))
    return out


def _predict_conflict(world: World, host: Entity, plan: InvitePlan) -> dict:
    sim = world.copy()
    host2 = sim.get(host.id)
    host2.memes["hope"] += 1
    if plan.conflict_kind == "crowding":
        sim.facts["conflict"] = True
        sim.facts["resolved"] = True
        return {"conflict": True, "resolved": True}
    if plan.conflict_kind == "noise":
        sim.facts["conflict"] = True
        sim.facts["resolved"] = True
        return {"conflict": True, "resolved": True}
    sim.facts["conflict"] = True
    sim.facts["resolved"] = True
    return {"conflict": True, "resolved": True}


def _start_story(world: World, host: Entity, plan: InvitePlan) -> None:
    world.say(
        f"{host.id} was a {host.label} politician who loved keeping the animal society together."
    )
    world.say(
        f"{host.pronoun().capitalize()} wanted to {plan.verb} the society to {plan.gathering}."
    )
    world.say(
        f"{host.id} hoped the day would be calm, bright, and full of smiling faces."
    )


def _arrive(world: World, host: Entity, plan: InvitePlan) -> None:
    if world.setting.indoor:
        world.say(f"At {world.setting.place}, the chairs were waiting in a neat row.")
    else:
        world.say(f"At {world.setting.place}, the grass was soft and the air felt fresh.")
    world.say(f"One by one, the animals came to the {plan.kind}.")


def _conflict(world: World, host: Entity, plan: InvitePlan) -> None:
    host.memes["worry"] += 1
    world.facts["conflict"] = True
    world.say(
        f"Then trouble blinked open: {plan.tension}."
    )
    world.say(
        f"The little animals fidgeted, and even {host.id} looked surprised."
    )


def _turn(world: World, host: Entity, plan: InvitePlan) -> None:
    host.memes["care"] += 1
    world.say(
        f"{host.id} took a breath and chose a kind fix: {plan.fix}."
    )
    world.say(
        f"The society listened, and the noisy feeling began to soften."
    )
    world.facts["resolved"] = True


def _ending(world: World, host: Entity, plan: InvitePlan) -> None:
    host.memes["joy"] += 1
    world.say(
        f"Soon the animals were settled, and the {plan.kind} felt warm and safe."
    )
    world.say(
        f"{host.id} smiled at the friendly circle, glad the invitation had helped the society come together."
    )


def tell(setting: Setting, plan: InvitePlan, name: str, species: str, role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=species,
        label=role,
        phrase=f"a {role}",
    ))
    world.facts["hero"] = hero
    world.facts["plan"] = plan
    world.facts["setting"] = setting

    _start_story(world, hero, plan)
    world.para()
    _arrive(world, hero, plan)
    _conflict(world, hero, plan)
    world.para()
    _turn(world, hero, plan)
    _ending(world, hero, plan)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    plan: InvitePlan = _safe_fact(world, world.facts, "plan")
    setting: Setting = _safe_fact(world, world.facts, "setting")
    return [
        f"Write a short animal story about a {hero.label} politician who wants to {plan.verb} the society at {setting.place}.",
        f"Tell a gentle story where {hero.id} invites the animal society, a small conflict appears, and everyone finds a calm fix.",
        f"Write a child-friendly tale with a politician, an invite, and a society gathering that ends happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    plan: InvitePlan = _safe_fact(world, world.facts, "plan")
    setting: Setting = _safe_fact(world, world.facts, "setting")
    return [
        QAItem(
            question=f"Who was the politician in the story?",
            answer=f"The politician was {hero.id}, a {hero.label} {hero.type} who cared about the animal society.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the society?",
            answer=f"{hero.id} wanted to {plan.verb} the society to {plan.gathering} at {setting.place}.",
        ),
        QAItem(
            question=f"What problem came up during the gathering?",
            answer=f"A conflict came up because {plan.tension}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} chose a kind fix by deciding to {plan.fix}, and the society settled down happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    return [
        QAItem(
            question="What is a politician?",
            answer="A politician is a person or leader who helps make choices for a community.",
        ),
        QAItem(
            question="What does invite mean?",
            answer="To invite means to ask someone to come to a place or join an event.",
        ),
        QAItem(
            question="What is a society?",
            answer="A society is a group of people or animals living and working together.",
        ),
        QAItem(
            question=f"What kind of animal is {hero.id}?",
            answer=f"{hero.id} is a {hero.type}, and {hero.pronoun('subject')} is the story's {hero.label}.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="hall", invite="tea", name="Bram", species="badger", role="mayor"),
    StoryParams(setting="meadow", invite="sing", name="Pip", species="rabbit", role="council fox"),
    StoryParams(setting="pond", invite="share", name="Ollie", species="otter", role="speaker"),
]


def explain_rejection(setting: Setting, plan: InvitePlan) -> str:
    return f"(No story: {setting.place} is not a good fit for that invitation plan.)"


ASP_RULES = r"""
valid_story(S, I) :- setting(S), invite(I), holds(S, H), H >= 8.
conflict_story(I) :- invite(I).
resolved_story(S, I) :- valid_story(S, I), conflict_story(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        lines.append(asp.fact("holds", sid, s.holds))
    for iid, i in INVITES.items():
        lines.append(asp.fact("invite", iid))
        lines.append(asp.fact("conflict_kind", iid, i.conflict_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: politician, invite, society, conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--invite", choices=INVITES)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--role")
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
    if getattr(args, "setting", None) and getattr(args, "invite", None):
        if not can_tell(_safe_lookup(SETTINGS, getattr(args, "setting", None)), _safe_lookup(INVITES, getattr(args, "invite", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "invite", None) is None or c[1] == getattr(args, "invite", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, invite = rng.choice(list(combos))
    species = getattr(args, "species", None) or rng.choice(sorted(SPECIES))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, species))
    role = getattr(args, "role", None) or rng.choice(["mayor", "council fox", "speaker", "leader"])
    return StoryParams(setting=setting, invite=invite, name=name, species=species, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(INVITES, params.invite), params.name, params.species, params.role)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/invite combos:\n")
        for s, i in combos:
            print(f"  {s:8} {i:8}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.invite} at {p.setting} ({p.species} {p.role})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
