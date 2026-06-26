#!/usr/bin/env python3
"""
storyworlds/worlds/effort_rhyme_friendship_reconciliation_fairy_tale.py
========================================================================

A small fairy-tale storyworld about effort, rhyme, friendship, and reconciliation.

Premise:
- A young fairy and a friend share a lovely little object in a magical setting.
- A mistake or misunderstanding makes the friendship feel strained.
- The hero puts in effort, uses a rhyme or gentle song, and makes amends.
- The story ends with reconciliation: the friendship is repaired and shown in a
  concrete final image.

This world is intentionally compact and classical: a few settings, a few objects,
one main emotional arc, and a clear ending image.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "queen", "princess", "woman"}
        male = {"boy", "knight", "king", "prince", "man"}
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
    mood: str
    affords: set[str] = field(default_factory=set)
    rhyme_word: str = ""
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    repairable: bool = True
    lovely: bool = True
    answer: str = ""
    question: str = ""
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
class TaleAction:
    id: str
    verb: str
    gerund: str
    risk: str
    repair: str
    theme: str
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
class StoryParams:
    place: str
    action: str
    item: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_effort(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters.get("effort", 0.0) < THRESHOLD:
        return out
    sig = ("effort",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    out.append("With steady effort, the little one kept going, even when the moon path felt long.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    hero = world.get("hero")
    friend = world.get("friend")
    if item.meters.get("broken", 0.0) < THRESHOLD:
        return out
    if hero.meters.get("effort", 0.0) < THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["broken"] = 0.0
    item.meters["mended"] = 1.0
    friend.memes["hurt"] = max(0.0, friend.memes.get("hurt", 0.0) - 1)
    out.append(f"After a patient little fix, the {item.label} was whole again.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("item")
    if hero.memes.get("apology", 0.0) < THRESHOLD:
        return out
    if item.meters.get("mended", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    out.append("Soon the two friends were smiling again, their friendship warmer than before.")
    return out


RULES = [
    Rule("effort", _r_effort),
    Rule("repair", _r_repair),
    Rule("reconcile", _r_reconcile),
]


def settings() -> dict[str, Setting]:
    return {
        "wood": Setting(place="the moonlit wood", mood="soft and silvery", affords={"rhyme", "search"}),
        "brook": Setting(place="the silver brook", mood="bright and whispery", affords={"rhyme", "search"}),
        "tower": Setting(place="the ivy tower", mood="high and echoing", affords={"rhyme", "search"}),
        "meadow": Setting(place="the flower meadow", mood="golden and gentle", affords={"rhyme", "search"}),
    }


def items() -> dict[str, Item]:
    return {
        "lantern": Item("lantern", "lantern", "a little lantern with a golden handle", "lantern", risk="broke"),
        "crown": Item("crown", "crown", "a tiny flower crown", "crown", risk="crushed"),
        "ribbon": Item("ribbon", "ribbon", "a bright blue ribbon", "ribbon", risk="torn"),
        "bell": Item("bell", "bell", "a small silver bell", "bell", risk="lost"),
    }


def actions() -> dict[str, TaleAction]:
    return {
        "rhyme": TaleAction(
            id="rhyme",
            verb="sing a rhyme",
            gerund="singing a rhyme",
            risk="hurt feelings",
            repair="apology",
            theme="Rhyme",
            keyword="rhyme",
        ),
        "search": TaleAction(
            id="search",
            verb="search carefully",
            gerund="searching carefully",
            risk="worry",
            repair="finding",
            theme="effort",
            keyword="effort",
        ),
    }


HERO_NAMES = ["Luna", "Elin", "Mira", "Poppy", "Clover", "Nia", "Wren", "Faye"]
FRIEND_NAMES = ["Pip", "Toby", "Jun", "Fern", "Moss", "Bea", "Gus", "Iris"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, s in settings().items():
        for a in s.affords:
            for i in items():
                out.append((p, a, i))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about effort, rhyme, friendship, and reconciliation.")
    ap.add_argument("--place", choices=sorted(settings()))
    ap.add_argument("--action", choices=sorted(actions()))
    ap.add_argument("--item", choices=sorted(items()))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["fairy", "girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["fairy", "girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, item = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["fairy", "girl"])
    friend_type = getattr(args, "friend_type", None) or rng.choice(["boy", "fairy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    if hero_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(place=place, action=action, item=item,
                       hero_name=hero_name, hero_type=hero_type,
                       friend_name=friend_name, friend_type=friend_type)


def intro(world: World, hero: Entity, friend: Entity, item: Entity, action: TaleAction) -> None:
    world.say(
        f"Once upon a time, in {world.setting.place}, there lived a little {hero.type} named {hero.id} "
        f"and a dear friend named {friend.id}."
    )
    world.say(
        f"They loved {action.gerund} in {world.setting.mood} days, and they kept {item.phrase} close by "
        f"because it made their play feel like a fairy tale."
    )


def conflict(world: World, hero: Entity, friend: Entity, item: Entity, action: TaleAction) -> None:
    world.para()
    item.meters["broken"] = 1.0
    friend.memes["hurt"] = 1.0
    hero.memes["guilt"] = 1.0
    world.say(
        f"But one twilight, {hero.id} made a mistake with {item.phrase}, and {friend.id} looked hurt."
    )
    world.say(
        f"The {item.label} became {item.risk}, and the laughter between them went quiet."
    )
    world.say(
        f"{hero.id} felt the friendship wobble, so {hero.id} decided to make real effort to mend it."
    )
    hero.meters["effort"] = 1.0
    propagate(world, narrate=True)


def reconciliation(world: World, hero: Entity, friend: Entity, item: Entity, action: TaleAction) -> None:
    world.para()
    hero.memes["apology"] = 1.0
    world.say(
        f"{hero.id} went to {friend.id} and bowed their head. \"I am sorry,\" {hero.id} said, "
        f"\"and I will work hard to make this right.\""
    )
    world.say(
        f"Then {hero.id} sang a tiny rhyme, as gentle as a candle flame, and kept at the repair with careful hands."
    )
    propagate(world, narrate=True)
    world.say(
        f"At last, {friend.id} smiled, and the two friends sat together again beside {world.setting.place}, "
        f"with {item.phrase} shining as proof that friendship can return after a hurt."
    )


def build_world(params: StoryParams) -> World:
    st = settings()[params.place]
    act = actions()[params.action]
    item_cfg = items()[params.item]
    world = World(st)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label=params.friend_name))
    item = world.add(Entity(id="item", kind="thing", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase))

    world.facts.update(hero=hero, friend=friend, item=item, action=act, setting=st)
    intro(world, hero, friend, item, act)
    conflict(world, hero, friend, item, act)
    reconciliation(world, hero, friend, item, act)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about {f["hero"].label} and {f["friend"].label} that includes the word "effort".',
        f"Tell a gentle story where {f['hero'].label} must use rhyme and effort to repair friendship after a mistake.",
        f"Write a child-friendly fairy tale ending in reconciliation beside {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, item, act = f["hero"], f["friend"], f["item"], f["action"]
    return [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {hero.label} and {friend.label}, who live a fairy-tale day in {f['setting'].place}.",
        ),
        QAItem(
            question=f"What went wrong with {item.label}?",
            answer=f"The {item.label} became {item.risk}, and that hurt the feeling of friendship between the two friends.",
        ),
        QAItem(
            question=f"What did {hero.label} do to make things better?",
            answer=f"{hero.label} showed effort, apologized, and sang a little rhyme while fixing the problem.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with reconciliation: {friend.label} smiled again, and their friendship felt warm and whole.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a rhyme?", answer="A rhyme is a little song or line where the ending sounds match and it can be fun to say aloud."),
        QAItem(question="What is friendship?", answer="Friendship is the caring bond between friends who help, listen, and play together."),
        QAItem(question="What is reconciliation?", answer="Reconciliation is when people who were upset make peace and become friendly again."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:6} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="wood", action="rhyme", item="bell", hero_name="Luna", hero_type="fairy", friend_name="Pip", friend_type="boy"),
    StoryParams(place="brook", action="search", item="ribbon", hero_name="Mira", hero_type="girl", friend_name="Fern", friend_type="fairy"),
    StoryParams(place="tower", action="rhyme", item="crown", hero_name="Faye", hero_type="fairy", friend_name="Toby", friend_type="boy"),
    StoryParams(place="meadow", action="search", item="lantern", hero_name="Clover", hero_type="fairy", friend_name="Iris", friend_type="girl"),
]


ASP_RULES = r"""
place(P) :- setting(P).
act(A) :- action(A).
obj(I) :- item(I).

valid_story(P,A,I) :- setting(P), action(A), item(I), affords(P,A).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in settings().items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in actions():
        lines.append(asp.fact("action", aid))
    for iid in items():
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_valid_combos(params: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = [c for c in valid_combos()
              if (params.place is None or c[0] == params.place)
              and (params.action is None or c[1] == params.action)
              and (params.item is None or c[2] == params.item)]
    return combos


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, a, i in combos:
            print(f"  {p:8} {a:8} {i:8}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.action} at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "hero_name", None) and getattr(args, "friend_name", None) and getattr(args, "hero_name", None) == getattr(args, "friend_name", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        **vars(_resolve(args, rng))
    )


def _resolve(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        **{
            "place": None,
            "action": None,
            "item": None,
            "hero_name": None,
            "hero_type": None,
            "friend_name": None,
            "friend_type": None,
            "seed": None,
        }
    )


# Override with actual resolver after helper definition.
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, item = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["fairy", "girl"])
    friend_type = getattr(args, "friend_type", None) or rng.choice(["boy", "fairy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        action=action,
        item=item,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


if __name__ == "__main__":
    main()
