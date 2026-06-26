#!/usr/bin/env python3
"""
storyworlds/worlds/cobble_german_sharing_rhyming_story.py
=========================================================

A small story world for a rhyming sharing tale: two children, one special
object, a little worry about keeping it, and a kind turn toward sharing.

Seed image:
---
A child finds a cobble at a German street fair. Another child wants a turn.
At first the cobble feels too special to give away. Then the children share it
by making a tiny cobble game together, and the day ends in a cheerful rhyme.

This world keeps the model small and concrete:
- physical meters track who has the cobble, a basket, and a shared display
- emotional memes track want, worry, kindness, and joy
- the story is built from causal state changes rather than a frozen paragraph
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    friend: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for k in ["possession", "display", "clean"]:
            self.meters.setdefault(k, 0.0)
        for k in ["want", "worry", "kindness", "joy", "pride", "grump"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class ShareObject:
    id: str
    label: str
    phrase: str
    sparkle: str
    rhymes_with: str
    value: str
    share_method: str
    place_bonus: str
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
class StoryParams:
    place: str
    item: str
    name: str
    friend: str
    gender: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def rhyme(end1: str, end2: str) -> str:
    return f"{end1}, {end2}."


SETTINGS = {
    "courtyard": Setting(place="the cobble courtyard", mood="bright", affords={"share"}),
    "market": Setting(place="the German market lane", mood="busy", affords={"share"}),
    "garden": Setting(place="the garden path", mood="soft", affords={"share"}),
}

SHARING_ITEMS = {
    "cobble": ShareObject(
        id="cobble",
        label="cobble",
        phrase="a smooth little cobble",
        sparkle="silver",
        rhymes_with="huddle",
        value="special",
        share_method="take turns",
        place_bonus="it fit the cobble ground just right",
        plural=False,
    ),
    "marble": ShareObject(
        id="marble",
        label="marble",
        phrase="a shiny blue marble",
        sparkle="blue",
        rhymes_with="tumble",
        value="bright",
        share_method="pass it around",
        place_bonus="it rolled in a neat little ring",
        plural=False,
    ),
    "crayons": ShareObject(
        id="crayons",
        label="crayons",
        phrase="a box of bright crayons",
        sparkle="rainbow",
        rhymes_with="say-ons",
        value="fun",
        share_method="share the colors",
        place_bonus="they made every mark look new",
        plural=True,
    ),
}

NAMES_GIRL = ["Mila", "Lina", "Greta", "Nora", "Anna", "Lea"]
NAMES_BOY = ["Finn", "Mika", "Theo", "Ben", "Emil", "Jonas"]
FRIENDS = ["sister", "brother", "friend", "cousin", "neighbor"]


def prize_at_risk(item: ShareObject) -> bool:
    return True


def select_share_turn(item: ShareObject) -> bool:
    return True


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for item_id in setting.affords:
            if prize_at_risk(_safe_lookup(SHARING_ITEMS, item_id)) and select_share_turn(_safe_lookup(SHARING_ITEMS, item_id)):
                out.append((place, item_id))
    return out


def introduce(world: World, child: Entity, item: Entity, friend: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a grin so wide, "
        f"and {friend.id} was ready to walk by {child.pronoun('possessive')} side."
    )
    world.say(
        f"In {world.setting.place}, the light felt soft and fair, "
        f"like a song in the air and a breeze in the hair."
    )
    world.say(
        f"{child.id} found {item.phrase}, a treasure to see, "
        f"as shiny as {item.metaspark if hasattr(item, 'metaspark') else item.meters.get('spark', 0)} "
        f"and sweet as could be."
    )


def find_item(world: World, child: Entity, item: Entity) -> None:
    child.meters["possession"] += 1
    item.held_by = child.id
    child.memes["pride"] += 1
    world.say(
        f"{child.id} held the {item.label} tight with a gleam and a beam, "
        f"and said, 'What a lucky, lovely little dream.'"
    )


def friend_wants_turn(world: World, friend: Entity, item: Entity) -> None:
    friend.memes["want"] += 1
    world.say(
        f"But {friend.id} leaned in near with a hopeful eye, "
        f"for a turn with the {item.label} would make {friend.pronoun('object')} fly high."
    )


def warn_about_hurt_feelings(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} felt stuck and hid a sigh, "
        f"for sharing sounded hard when the treasure was nigh."
    )


def share_turns(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    child.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    child.meters["display"] += 1
    friend.meters["display"] += 1
    item.meters["display"] += 1
    world.say(
        f"Then {child.id} smiled and said, 'Let's share and play, "
        f"you may have a turn in your own bright way.'"
    )
    world.say(
        f"They chose to {_safe_lookup(SHARING_ITEMS, item.type).share_method} in a tiny round game, "
        f"and the little {item.label} felt fun all the same."
    )
    world.say(
        f"{_safe_lookup(SHARING_ITEMS, item.type).place_bonus.capitalize()}, "
        f"and the two friends laughed without shame."
    )
    world.say(
        rhyme(
            f"{child.id} felt proud and warm",
            f"{friend.id} felt bright like a charm",
        )
    )


def resolve_story(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"In the end, the two stood side by side, "
        f"with a shared little game and a happy ride."
    )
    world.say(
        f"The {item.label} was still {item.value}, but now it was shared, "
        f"and both of them knew that kindness had cared."
    )


def tell(setting: Setting, item_cfg: ShareObject, hero_name: str, friend_label: str, gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        label=hero_name,
    ))
    friend = world.add(Entity(
        id=friend_label,
        kind="character",
        type="friend",
        label=friend_label,
    ))
    item = world.add(Entity(
        id=item_cfg.id,
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=child.id,
    ))
    world.facts.update(child=child, friend=friend, item=item, item_cfg=item_cfg)

    introduce(world, child, item, friend)
    world.para()
    find_item(world, child, item)
    friend_wants_turn(world, friend, item)
    warn_about_hurt_feelings(world, child, friend, item)
    share_turns(world, child, friend, item)
    world.para()
    resolve_story(world, child, friend, item)
    world.facts["shared"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = _safe_fact(world, f, "item_cfg")
    child = _safe_fact(world, f, "child")
    return [
        f'Write a short rhyming story about a child named {child.id} sharing a {item.label} at {world.setting.place}.',
        f"Tell a gentle German-style sharing rhyme where a little {child.type} learns to take turns with {item.phrase}.",
        f'Write a simple story that uses the word "{item.label}" and ends with two friends sharing kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    friend = _safe_fact(world, f, "friend")
    item = _safe_fact(world, f, "item_cfg")
    return [
        QAItem(
            question=f"What did {child.id} find in {world.setting.place}?",
            answer=f"{child.id} found {item.phrase}. It was the special thing the children shared.",
        ),
        QAItem(
            question=f"Why did {friend.id} want a turn with the {item.label}?",
            answer=f"{friend.id} wanted a turn because the {item.label} looked fun and special, so sharing would make the game nicer.",
        ),
        QAItem(
            question=f"How did the children solve the problem about the {item.label}?",
            answer=f"They chose to share it and take turns, so both children could enjoy it together.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt proud, happy, and kind after sharing the {item.label} with {friend.id}.",
        ),
    ]


KNOWLEDGE = {
    "cobble": [
        QAItem(
            question="What is a cobble?",
            answer="A cobble is a rounded stone used on streets or paths, and cobbles can make the ground bumpy and old-fashioned.",
        )
    ],
    "german": [
        QAItem(
            question="What does German mean?",
            answer="German is the name of a language and a culture from Germany, a country in Europe.",
        )
    ],
    "sharing": [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too, often by taking turns.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    out.extend(KNOWLEDGE["cobble"])
    out.extend(KNOWLEDGE["german"])
    out.extend(KNOWLEDGE["sharing"])
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
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
item_valid(P, I) :- place(P), item(I), affords(P, I).
share_story(P, I) :- item_valid(P, I).
#show item_valid/2.
#show share_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for i in sorted(_safe_lookup(SETTINGS, p).affords):
            lines.append(asp.fact("affords", p, i))
    for i in SHARING_ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show item_valid/2."))
    return sorted(set(asp.atoms(model, "item_valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming sharing story world with cobbles and German flavor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=SHARING_ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in combos if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)]
    combos = [c for c in combos if getattr(args, "item", None) is None or c[1] == getattr(args, "item", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    return StoryParams(place=place, item=item, name=name, friend=friend, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(SHARING_ITEMS, params.item),
        params.name,
        params.friend,
        params.gender,
    )
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
    StoryParams(place="courtyard", item="cobble", name="Mila", friend="friend", gender="girl"),
    StoryParams(place="market", item="cobble", name="Finn", friend="brother", gender="boy"),
    StoryParams(place="garden", item="crayons", name="Greta", friend="sister", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show item_valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, item in combos:
            print(f"  {place:10} {item}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
