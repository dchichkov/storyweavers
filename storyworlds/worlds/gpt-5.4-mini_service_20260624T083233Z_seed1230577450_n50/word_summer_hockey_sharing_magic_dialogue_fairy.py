#!/usr/bin/env python3
"""
storyworlds/worlds/word_summer_hockey_sharing_magic_dialogue_fairy.py
======================================================================

A small fairy-tale story world about summer hockey, sharing, magic, and
gentle dialogue.

The world is intentionally compact: one child/fairy hero, one friend, one
magical hockey item, and one important shared turn. The tension comes from a
wish to keep the magic word or stick all to oneself during summer play, and the
resolution comes from speaking kindly and sharing the magical thing so both can
play.

The tale style is fairy-like: soft, concrete, child-facing, and causal.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "princess", "mother", "woman"}
        male = {"boy", "knight", "father", "man"}
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Place:
    name: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    plural: bool = False
    magical: bool = False
    spark_kind: str = ""
    requires: set[str] = field(default_factory=set)
    bestowed_by: str = ""
    gives: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    activity: str
    item: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.magic_active: bool = False

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.magic_active = self.magic_active
        return c


def _has_magic_word(world: World, actor: Entity) -> bool:
    return actor.memes.get("speaks_magic_word", 0.0) >= THRESHOLD


def _activity_is_hockey(world: World, activity: str) -> bool:
    return activity == "hockey"


def _item_can_be_shared(item: Item, activity: str) -> bool:
    return activity in item.requires


def _predict_outcome(world: World, hero: Entity, friend: Entity, item: Item, activity: str) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["want"] = 1
    sim.get(hero.id).memes["greed"] = 1
    if item.magical:
        sim.magic_active = True
    soothes = False
    if item.magical and activity == "hockey":
        soothes = True
    return {"soothes": soothes, "shared": False}


def setup_world(place: Place, hero_name: str, hero_type: str,
                friend_name: str, friend_type: str, trait: str,
                activity: str, item_def: Item) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", trait],
        meters={"joy": 0.0},
        memes={"curiosity": 1.0, "want": 0.0, "greed": 0.0, "sharing": 0.0, "delight": 0.0},
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type,
        traits=["little", "gentle"],
        meters={"joy": 0.0},
        memes={"curiosity": 1.0, "want": 0.0, "sharing": 0.0, "delight": 0.0},
    ))
    item = world.add(Entity(
        id=item_def.id, kind="thing", type=item_def.kind, label=item_def.label,
        phrase=item_def.phrase, plural=item_def.plural, owner=hero.id,
        held_by=hero.id, meters={"spark": 0.0},
        memes={"magic": 1.0 if item_def.magical else 0.0},
    ))
    world.facts.update(hero=hero, friend=friend, item=item, activity=activity, item_def=item_def)
    return world


def tell_scene(world: World) -> World:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    item = world.facts["item"]
    activity = world.facts["activity"]

    world.say(
        f"On a bright summer day, {hero.id} wandered to {world.place.name}, where the grass shone like green silk."
    )
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {item.label}, and {hero.id} loved it because it could wake a little bit of magic."
    )
    world.say(
        f"{friend.id} arrived with a smile and said, \"Can we play {activity} together?\""
    )
    world.facts["asked_to_play"] = True

    world.para()
    hero.memes["want"] += 1
    hero.memes["greed"] += 1
    world.say(
        f"{hero.id} wanted to keep the {item.label} all to {hero.pronoun('possessive')}self, because the shiny magic felt too special to lend."
    )
    if _activity_is_hockey(world, activity):
        world.say(
            f"{hero.id} said, \"This is my {activity} word,\" and the word sounded small and stubborn in the warm air."
        )
    world.say(
        f"{friend.id} looked hurt and whispered, \"But I only need a turn.\""
    )

    world.para()
    world.say(
        f"Then the {item.label} gave a tiny sparkle, as if it understood that summer play should be shared."
    )
    world.magic_active = True
    world.facts["predicted_soothe"] = _predict_outcome(world, hero, friend, item, activity)["soothes"]
    world.say(
        f"{hero.id} paused and listened, because even a fairy tale heart can learn when a friend speaks softly."
    )
    world.say(
        f"{friend.id} asked, \"Will you share the {item.label} if I share the puck and take a careful turn after you?\""
    )
    hero.memes["sharing"] += 1

    world.para()
    if item.magical and _item_can_be_shared(world.facts["item_def"], activity):
        world.say(
            f"{hero.id} nodded, passed the {item.label} to {friend.id}, and said, \"Yes, let us share the magic word and the game.\""
        )
        hero.meters["joy"] += 1
        friend.meters["joy"] += 1
        friend.memes["sharing"] += 1
        item.meters["spark"] += 1
        world.facts["resolved"] = True
        world.say(
            f"Together they played {activity} under the summer sky, taking turns, laughing, and sending the little magic back and forth like a bright star."
        )
        world.say(
            f"At the end, {hero.id} still had the {item.label}, {friend.id} still had a turn, and the whole field felt kinder."
        )
    else:
        pass

    return world


SETTINGS = {
    "meadow": Place(name="the meadow", outdoors=True, affords={"hockey"}),
    "pond": Place(name="the pond-side lane", outdoors=True, affords={"hockey"}),
    "garden": Place(name="the flower garden", outdoors=True, affords={"hockey"}),
}

ACTIVITIES = {
    "hockey": "hockey",
}

ITEMS = {
    "magic_word": Item(
        id="magic_word",
        label="magic word",
        phrase="a magic word wrapped in a ribbon",
        kind="word",
        magical=True,
        spark_kind="glow",
        requires={"hockey"},
        bestowed_by="a kind fairy",
        gives={"sharing"},
    ),
    "magic_stick": Item(
        id="magic_stick",
        label="magic hockey stick",
        phrase="a magic hockey stick with a silver stripe",
        kind="stick",
        magical=True,
        spark_kind="glow",
        requires={"hockey"},
        bestowed_by="a moonlit fairy",
        gives={"sharing"},
    ),
}

HERO_NAMES = ["Lina", "Mara", "Tia", "Nina", "Elsa", "Bri"]
FRIEND_NAMES = ["Pip", "Rook", "Fenn", "Milo", "Sera", "Wren"]
TRAITS = ["kind", "curious", "brave", "cheerful", "gentle", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in SETTINGS.items():
        for act in ACTIVITIES:
            for item_id, item in ITEMS.items():
                if act in place.affords and act in item.requires and item.magical:
                    out.append((place_id, act, item_id))
    return out


def explain_rejection(place: Place, activity: str, item: Item) -> str:
    return (
        f"(No story: {item.label} at {place.name} does not make a fair sharing story for {activity}. "
        f"Choose the magical hockey item or a place that supports hockey.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy tale story world about summer hockey, sharing, magic, and dialogue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None) and getattr(args, "activity", None) and getattr(args, "item", None):
        if (getattr(args, "place", None), getattr(args, "activity", None), getattr(args, "item", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, item = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        item=item,
        hero_name=hero_name,
        hero_type="fairy",
        friend_name=friend_name,
        friend_type="fairy",
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, item = f["hero"], f["friend"], f["item"]
    return [
        f'Write a fairy tale for a young child about summer hockey, sharing, and magic that includes the word "summer".',
        f'Write a gentle story where {hero.id} and {friend.id} take turns with a {item.label} and learn to share.',
        f'Write a short fairy tale that uses the word "hockey" and ends with two friends speaking kindly to each other.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, item = f["hero"], f["friend"], f["item"]
    return [
        QAItem(
            question=f"Who wanted to keep the {item.label} at first?",
            answer=f"{hero.id} wanted to keep the {item.label} at first, because the magic felt special.",
        ),
        QAItem(
            question=f"What did {friend.id} ask for before they played hockey?",
            answer=f"{friend.id} asked for a turn and asked {hero.id} to share the {item.label}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"They shared the {item.label}, played hockey together, and felt happy in the summer air.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is summer?",
            answer="Summer is the warm season of the year, when the days are usually bright and long.",
        ),
        QAItem(
            question="What is hockey?",
            answer="Hockey is a game where players move a puck or ball with sticks and try to score.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, usually by taking turns kindly.",
        ),
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic in a fairy tale is something marvelous that can sparkle, change, or help in a special way.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is the talking characters do in a story when they speak to each other.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  magic_active={world.magic_active}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- acts(A).
item(I) :- item_kind(I).

valid_story(P,A,I) :- place(P), activity(A), item(I), affords(P,A), requires(I,A), magical(I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if p.outdoors:
            lines.append(asp.fact("outdoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("acts", a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item_kind", iid))
        lines.append(asp.fact("requires", iid, "hockey"))
        if item.magical:
            lines.append(asp.fact("magical", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    place = _safe_lookup(SETTINGS, params.place)
    item_def = _safe_lookup(ITEMS, params.item)
    world = setup_world(place, params.hero_name, params.hero_type, params.friend_name, params.friend_type, params.trait, params.activity, item_def)
    world = tell_scene(world)
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
    StoryParams(place="meadow", activity="hockey", item="magic_word", hero_name="Lina", hero_type="fairy", friend_name="Pip", friend_type="fairy", trait="kind"),
    StoryParams(place="garden", activity="hockey", item="magic_stick", hero_name="Mara", hero_type="fairy", friend_name="Wren", friend_type="fairy", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, item) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
            header = f"### {p.hero_name}: {p.activity} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
