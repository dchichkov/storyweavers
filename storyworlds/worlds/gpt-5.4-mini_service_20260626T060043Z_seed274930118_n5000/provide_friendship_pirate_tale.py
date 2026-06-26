#!/usr/bin/env python3
"""
A standalone story world for a small pirate tale about friendship and providing.

Premise:
- A young pirate wants to help a friend in need.
- The ship has a small harbor-side task, a shortage, and a choice between
  keeping treasure or providing it.
- Friendship turns the problem into a generous rescue.

The world simulates:
- physical meters: cargo, hunger, cold, dryness, sparkle, repair
- emotional memes: trust, worry, pride, relief, friendship, generosity

The story is intentionally small and classical: setup, tension, turn, resolution.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    friend: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Harbor:
    place: str
    sea_state: str = "calm"
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
    label: str
    phrase: str
    meter: str
    loss: str
    risk: str
    tag: str
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
class Gift:
    id: str
    label: str
    phrase: str
    helps: set[str]
    reason: str
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
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.harbor)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_support(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        for meter in ("hunger", "cold"):
            if char.meters.get(meter, 0.0) < THRESHOLD:
                continue
            if char.meters.get("provided", 0.0) >= THRESHOLD:
                continue
            sig = ("need", char.id, meter)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            char.memes["worry"] = char.memes.get("worry", 0.0) + 1
            out.append(f"{char.id} needed help.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.meters.get("provided", 0.0) < THRESHOLD:
            continue
        sig = ("relief", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["relief"] = char.memes.get("relief", 0.0) + 1
        char.memes["trust"] = char.memes.get("trust", 0.0) + 1
        out.append(f"{char.id} felt relief.")
    return out


CAUSAL_RULES = [Rule("support", _r_support), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
    if narrate:
        for s in out:
            if s != "__skip__":
                world.say(s)
    return out


@dataclass
class StoryParams:
    name: str
    friend: str
    gift: str
    need: str
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


HARBORS = {
    "dock": Harbor(place="the dock", sea_state="calm", affords={"bread", "blanket", "rope"}),
    "cove": Harbor(place="the cove", sea_state="windy", affords={"bread", "blanket", "rope"}),
    "ship": Harbor(place="the little ship", sea_state="calm", affords={"bread", "blanket", "rope"}),
}

NEEDS = {
    "hunger": Need(
        id="hunger",
        label="hunger",
        phrase="a crust of bread",
        meter="hunger",
        loss="hungry",
        risk="go rumbling",
        tag="bread",
    ),
    "cold": Need(
        id="cold",
        label="cold",
        phrase="a warm blanket",
        meter="cold",
        loss="cold",
        risk="shiver",
        tag="blanket",
    ),
}

GIFTS = {
    "bread": Gift(
        id="bread",
        label="bread",
        phrase="a soft loaf of bread",
        helps={"hunger"},
        reason="it fills an empty belly",
    ),
    "blanket": Gift(
        id="blanket",
        label="blanket",
        phrase="a warm wool blanket",
        helps={"cold"},
        reason="it keeps a shivering body warm",
    ),
    "rope": Gift(
        id="rope",
        label="rope",
        phrase="a sturdy coil of rope",
        helps=set(),
        reason="it helps with sails, not with hunger or cold",
    ),
}

NAMES = ["Mira", "Finn", "Jory", "Tess", "Nell", "Pip", "Rowan", "Sail", "Ari"]
FRIEND_NAMES = ["Bo", "Luna", "Jem", "Nia", "Toby", "Ada", "Milo", "Rae"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate friendship tale about providing help.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--need", choices=NEEDS)
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


def _valid_combo(place: str, need: str, gift: str) -> bool:
    return need in _safe_lookup(GIFTS, gift).helps and gift in _safe_lookup(HARBORS, place).affords


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for place in HARBORS:
        for need in NEEDS:
            for gift in GIFTS:
                if _valid_combo(place, need, gift):
                    if (getattr(args, "need", None) is None or getattr(args, "need", None) == need) and (getattr(args, "gift", None) is None or getattr(args, "gift", None) == gift):
                        combos.append((place, need, gift))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, need, gift = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(name=name, friend=friend, gift=gift, need=need)


def _predict(world: World, hero: Entity, gift: Gift, friend: Entity, need: Need) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["provided"] = 1
    sim.get(friend.id).meters[need.meter] = 0
    propagate(sim, narrate=False)
    return {"relief": sim.get(friend.id).memes.get("relief", 0.0) > 0}


def tell(params: StoryParams) -> World:
    harbor = HARBORS["dock"]
    need = _safe_lookup(NEEDS, params.need)
    gift = _safe_lookup(GIFTS, params.gift)
    world = World(harbor)

    hero = world.add(Entity(id=params.name, kind="character", type="pirate", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="pirate", label=params.friend))
    treasure = world.add(Entity(id="treasure", type="thing", label=gift.label, phrase=gift.phrase, owner=hero.id))

    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1
    friend.meters[need.meter] = 1
    hero.meters["provided"] = 0

    world.say(f"{hero.id} was a small pirate who liked bright mornings at {harbor.place}.")
    world.say(f"{hero.id} and {friend.id} were true friends, and they always shared a grin before the tide turned.")
    world.say(f"One day, {friend.id} had {need.loss}, and {need.phrase} seemed far away.")
    world.para()
    world.say(f"{hero.id} looked at {treasure.label} and remembered how much {friend.id} needed help.")

    world.say(f"The ship could afford {gift.label}, and {gift.phrase} was the right thing to bring.")
    world.say(f"{hero.id} wanted to keep the treasure safe, but friendship tugged harder than pride.")

    if _predict(world, hero, gift, friend, need)["relief"]:
        world.para()
        world.say(f'So {hero.id} said, "A friend comes first. I will provide {gift.label}."')
        hero.meters["provided"] = 1
        friend.meters[need.meter] = 0
        propagate(world)
        world.say(f"{hero.id} handed over {gift.phrase}, and {friend.id} took it with a shaky smile.")
        world.say(f"That choice left the treasure smaller, but the friendship grew bigger and warmer.")
        world.say(f"At the end, {friend.id} was no longer {need.loss}, and the two pirates sailed on together.")
    else:
        pass

    world.facts.update(hero=hero, friend=friend, need=need, gift=gift, treasure=treasure, harbor=harbor)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short pirate story about {f['hero'].id} providing {f['gift'].label} to help a friend.",
        f"Tell a friendship tale where a pirate chooses generosity over treasure at {f['harbor'].place}.",
        f"Write a simple story about {f['friend'].id} needing {f['need'].label} and {f['hero'].id} making things better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, need, gift = f["hero"], f["friend"], f["need"], f["gift"]
    return [
        QAItem(
            question=f"Who was the pirate that decided to provide help?",
            answer=f"{hero.id} was the pirate who chose to provide {gift.label} to a friend.",
        ),
        QAItem(
            question=f"What did {friend.id} need at the start of the story?",
            answer=f"{friend.id} needed {need.label}, so {gift.phrase} was the kind of help that could make things better.",
        ),
        QAItem(
            question=f"Why did {hero.id} give up the treasure?",
            answer=f"{hero.id} cared more about friendship than keeping the treasure safe, so {hero.id} chose to provide {gift.label} instead.",
        ),
        QAItem(
            question=f"How did the story end for {friend.id}?",
            answer=f"{friend.id} was helped, felt relief, and ended the story smiling beside {hero.id}.",
        ),
    ]


KNOWLEDGE = {
    "bread": [("What is bread?", "Bread is a food made from baked dough. People can eat it when they are hungry.")],
    "blanket": [("What is a blanket for?", "A blanket keeps you warm when you are cold or sleepy.")],
    "rope": [("What is rope used for?", "Rope can tie things together or help pull and hold heavy objects.")],
    "hunger": [("What does hunger mean?", "Hunger means your body wants food.")],
    "cold": [("What does it mean to be cold?", "When you are cold, your body feels chilly and may want warmth.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {f["gift"].id, f["need"].id}
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
need_help(C,N) :- character(C), hunger(C), N=hunger.
need_help(C,N) :- character(C), cold(C), N=cold.

can_provide(G,N) :- gift(G), helps(G,N).
good_choice(C,G,N) :- need_help(C,N), can_provide(G,N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in HARBORS:
        lines.append(asp.fact("harbor", name))
        for item in sorted(_safe_lookup(HARBORS, name).affords):
            lines.append(asp.fact("affords", name, item))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("need_tag", nid, need.tag))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for n in sorted(gift.helps):
            lines.append(asp.fact("helps", gid, n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_choice/3."))
    return sorted(set(asp.atoms(model, "good_choice")))


def asp_verify() -> int:
    py = set((place, need, gift) for place in HARBORS for need in NEEDS for gift in GIFTS if _valid_combo(place, need, gift))
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


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


CURATED = [
    StoryParams(name="Mira", friend="Bo", gift="bread", need="hunger"),
    StoryParams(name="Finn", friend="Luna", gift="blanket", need="cold"),
    StoryParams(name="Tess", friend="Jem", gift="bread", need="hunger"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_choice/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible choices:\n")
        for place, need, gift in asp_valid_combos():
            print(f"  {place:6} {need:7} {gift}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name} and {p.friend} -- {p.need} -> {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
