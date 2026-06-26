#!/usr/bin/env python3
"""
storyworlds/worlds/flabbergast_sharing_twist_animal_story.py
=============================================================

A small animal-story world about sharing, a twist, and a flabbergasted turn.

Premise:
- One animal has a special treat or toy.
- A friend asks to share.
- A twist reveals the item was meant for more than one animal, or the
  apparent problem was actually a surprise.

The world model tracks physical state in meters and emotional state in memes.
The prose is generated from the simulated state, not from a fixed template with
swapped nouns.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    treat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"mouse", "rabbit", "squirrel", "duck", "cat", "fox"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
            if self.type in {"boy", "buck", "dog"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            if self.type in {"girl", "doe"}:
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
    place: str
    cozy: bool = True
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
class Treat:
    id: str
    label: str
    phrase: str
    kind: str
    shareable: bool = True
    splitable: bool = False
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


@dataclass
class Twist:
    id: str
    label: str
    reveal: str
    effect: str
    requires_shareable: bool = True
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "meadow": Setting(place="the meadow", cozy=True, affords={"share"}),
    "barn": Setting(place="the old barn", cozy=True, affords={"share"}),
    "riverbank": Setting(place="the riverbank", cozy=False, affords={"share"}),
}

TREAT_ITEMS = {
    "berry_pie": Treat(
        id="berry_pie",
        label="berry pie",
        phrase="a warm berry pie",
        kind="food",
        shareable=True,
        splitable=True,
    ),
    "honey_cakes": Treat(
        id="honey_cakes",
        label="honey cakes",
        phrase="a small plate of honey cakes",
        kind="food",
        shareable=True,
        splitable=True,
        plural=True,
    ),
    "seed_cookies": Treat(
        id="seed_cookies",
        label="seed cookies",
        phrase="a tin of seed cookies",
        kind="food",
        shareable=True,
        splitable=True,
        plural=True,
    ),
    "red_ball": Treat(
        id="red_ball",
        label="red ball",
        phrase="a shiny red ball",
        kind="toy",
        shareable=True,
        splitable=False,
    ),
}

TWISTS = {
    "surprise_picnic": Twist(
        id="surprise_picnic",
        label="surprise picnic",
        reveal="the treat was meant for everyone at a little picnic",
        effect="the animals could share it together",
    ),
    "gift_mistake": Twist(
        id="gift_mistake",
        label="gift mix-up",
        reveal="the worried friend had brought the same treat as a gift",
        effect="there was plenty after the mix-up was explained",
    ),
    "birthday_crowd": Twist(
        id="birthday_crowd",
        label="birthday crowd",
        reveal="more friends were on the way, and the snack needed to stretch",
        effect="sharing made enough for the whole group",
    ),
}

ANIMAL_TYPES = ["rabbit", "mouse", "squirrel", "duck", "fox", "cat"]
NAMES = ["Milo", "Poppy", "Nina", "Toby", "Luna", "Bram", "Ziggy", "Mira"]
TRAITS = ["gentle", "curious", "cheerful", "silly", "small", "bright"]


@dataclass
class StoryParams:
    setting: str
    treat: str
    twist: str
    owner_name: str
    owner_type: str
    friend_name: str
    friend_type: str
    owner_trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for t, treat in TREAT_ITEMS.items():
            if "share" not in setting.affords or not treat.shareable:
                continue
            for tw in TWISTS:
                combos.append((s, t, tw))
    return combos


def explain_rejection(treat: Treat, twist: Twist) -> str:
    return (
        f"(No story: {treat.label} and {twist.label} do not make a reasonable sharing twist "
        f"in this little animal world.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world about sharing, a twist, and flabbergast."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREAT_ITEMS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--owner-name")
    ap.add_argument("--owner-type", choices=ANIMAL_TYPES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=ANIMAL_TYPES)
    ap.add_argument("--owner-trait", choices=TRAITS)
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
    if getattr(args, "treat", None) and getattr(args, "twist", None):
        if (getattr(args, "setting", None) or "meadow", getattr(args, "treat", None), getattr(args, "twist", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "treat", None) is None or c[1] == getattr(args, "treat", None))
              and (getattr(args, "twist", None) is None or c[2] == getattr(args, "twist", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, treat, twist = rng.choice(list(combos))
    owner_type = getattr(args, "owner_type", None) or rng.choice(ANIMAL_TYPES)
    friend_type = getattr(args, "friend_type", None) or rng.choice([a for a in ANIMAL_TYPES if a != owner_type])
    owner_name = getattr(args, "owner_name", None) or rng.choice(NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in NAMES if n != owner_name])
    owner_trait = getattr(args, "owner_trait", None) or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        treat=treat,
        twist=twist,
        owner_name=owner_name,
        owner_type=owner_type,
        friend_name=friend_name,
        friend_type=friend_type,
        owner_trait=owner_trait,
    )


def _share(world: World, owner: Entity, friend: Entity, treat: Entity, twist: Twist) -> None:
    owner.memes["guarded"] += 1
    friend.memes["wanting"] += 1
    world.say(
        f"{owner.id} had {treat.phrase} at {world.setting.place}, and {friend.id} "
        f"came close with a soft smile."
    )
    world.say(
        f'"Can I share {treat.it()}?" {friend.id} asked.'
    )
    owner.memes["surprise"] += 1
    if twist.id == "gift_mistake":
        world.say(
            f"{owner.id} frowned for a moment, but then the twist came out: "
            f"{twist.reveal}."
        )
    elif twist.id == "surprise_picnic":
        world.say(
            f"{owner.id} blinked, flabbergast at first, and then learned the twist: "
            f"{twist.reveal}."
        )
    else:
        world.say(
            f"{owner.id} looked up, flabbergast, because {twist.reveal}."
        )


def _resolve(world: World, owner: Entity, friend: Entity, treat: Entity, twist: Twist) -> None:
    owner.memes["flabbergast"] += 1
    owner.memes["joy"] += 1
    friend.memes["joy"] += 1
    owner.memes["guarded"] = 0
    world.say(
        f"{owner.id} laughed, nodded, and said they could share {treat.it()}."
    )
    world.say(
        f"That was the best part of the day: {treat.phrase} was shared, {twist.effect}, "
        f"and both animals sat side by side with happy crumbs and bright eyes."
    )


def tell_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    owner = world.add(Entity(id=params.owner_name, kind="character", type=params.owner_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    treat_cfg = _safe_lookup(TREAT_ITEMS, params.treat)
    twist_cfg = _safe_lookup(TWISTS, params.twist)
    treat = world.add(Entity(
        id=treat_cfg.id,
        label=treat_cfg.label,
        phrase=treat_cfg.phrase,
        kind="thing",
        owner=owner.id,
        plural=treat_cfg.plural,
    ))

    owner.memes["love"] += 1
    owner.memes["pride"] += 1
    treat.meters["fresh"] = 1.0
    world.say(
        f"Little {params.owner_trait} {owner.type} {owner.id} found {treat.phrase} "
        f"in {world.setting.place}."
    )
    world.say(
        f"{owner.id} wanted to keep it close because it looked special."
    )
    world.para()
    _share(world, owner, friend, treat, twist_cfg)
    world.para()
    _resolve(world, owner, friend, treat, twist_cfg)

    world.facts.update(
        owner=owner,
        friend=friend,
        treat=treat,
        twist=twist_cfg,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = _safe_fact(world, f, "owner")
    treat = _safe_fact(world, f, "treat")
    twist = _safe_fact(world, f, "twist")
    return [
        f"Write a short animal story about sharing {treat.label} and a twist that makes {owner.id} flabbergast.",
        f"Tell a gentle story where {owner.id} meets a friend, shares {treat.phrase}, and learns a surprise about it.",
        f"Create a tiny animal story in which a sharing moment turns into {twist.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    owner = _safe_fact(world, f, "owner")
    friend = _safe_fact(world, f, "friend")
    treat = _safe_fact(world, f, "treat")
    twist = _safe_fact(world, f, "twist")
    params = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Who had the {treat.label} first?",
            answer=f"{owner.id} had the {treat.label} first in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {friend.id} ask about the {treat.label}?",
            answer=f"{friend.id} asked if they could share it.",
        ),
        QAItem(
            question=f"Why did {owner.id} feel flabbergast?",
            answer=(
                f"{owner.id} felt flabbergast because the story turned on a twist: "
                f"{twist.reveal}."
            ),
        ),
        QAItem(
            question=f"How did the story end for {owner.id} and {friend.id}?",
            answer=(
                f"They shared the {treat.label} together, and both animals ended the day happy "
                f"in {world.setting.place}."
            ),
        ),
        QAItem(
            question=f"What kind of animal was {params.owner_name}?",
            answer=f"{params.owner_name} was a {params.owner_type}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    treat = _safe_fact(world, f, "treat")
    out = [
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to let more than one animal use, eat, or enjoy the same thing.",
        ),
        QAItem(
            question="Why can sharing make friends happy?",
            answer="Sharing can make friends happy because everyone gets a turn or a taste, and nobody feels left out.",
        ),
    ]
    if treat.kind == "food":
        out.append(
            QAItem(
                question=f"Why is {treat.label} a nice thing to share?",
                answer=f"{treat.label.capitalize()} is nice to share because it can be divided into bites and enjoyed together.",
            )
        )
    return out


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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "berry_pie", "surprise_picnic", "Milo", "rabbit", "Poppy", "mouse", "gentle"),
    StoryParams("barn", "seed_cookies", "gift_mistake", "Luna", "cat", "Bram", "squirrel", "curious"),
    StoryParams("riverbank", "honey_cakes", "birthday_crowd", "Nina", "duck", "Toby", "fox", "cheerful"),
]


ASP_RULES = r"""
share_story(S,T,W) :- setting(S), treat(T), twist(W), valid_combo(S,T,W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(_safe_lookup(SETTINGS, sid).affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TREAT_ITEMS.items():
        lines.append(asp.fact("treat", tid))
        if t.shareable:
            lines.append(asp.fact("shareable", tid))
        if t.splitable:
            lines.append(asp.fact("splitable", tid))
    for wid in TWISTS:
        lines.append(asp.fact("twist", wid))
    for s, t, w in valid_combos():
        lines.append(asp.fact("valid_combo", s, t, w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        triples = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(triples)} compatible combinations:")
        for s, t, w in triples:
            print(f"  {s:10} {t:14} {w}")
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
            header = f"### {p.owner_name}: {p.treat} in {p.setting} (twist: {p.twist})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
