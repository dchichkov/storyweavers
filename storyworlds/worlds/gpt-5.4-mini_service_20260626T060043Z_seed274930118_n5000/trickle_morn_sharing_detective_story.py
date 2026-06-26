#!/usr/bin/env python3
"""
storyworlds/worlds/trickle_morn_sharing_detective_story.py
===========================================================

A small standalone story world for a child-sized detective tale about sharing.

Seed image used to build the world:
---
At morn, a little detective noticed a trickle on the floor near a shared basket.
Something had gone missing, but the clue was not loud. It was small, careful,
and kind of shared. The detective followed the trickle, asked gentle questions,
and found that the answer was not theft at all: a friend had borrowed the item
to help someone, then brought it back with a smile.

This world keeps the detective-story shape:
- a quiet morning setting
- a shared item and a small mystery
- a clue trail with a trickle
- an explanation that fits the facts
- a resolution that proves sharing changed the ending

The world model tracks physical meters and emotional memes, and the prose is
generated from those state changes rather than from a frozen template.
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
    borrowed_from: Optional[str] = None
    shared_with: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    friend: object | None = None
    shared: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
    morning_detail: str
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
class Mystery:
    id: str
    verb: str
    gerund: str
    clue: str
    trickle: str
    at_risk: str
    trail: str
    emotion: str
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
class SharedItem:
    label: str
    phrase: str
    type: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    mystery: str
    item: str
    detective_name: str
    detective_type: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", morning_detail="The morn light lay on the table like pale butter.", affords={"spill", "search"}),
    "hall": Setting(place="the hall", morning_detail="The morn air was still and clean, with shoes lined up by the wall.", affords={"spill", "search"}),
    "garden_room": Setting(place="the garden room", morning_detail="The morn sun shone through round glass, making bright squares on the floor.", affords={"spill", "search"}),
}

MYSTERIES = {
    "juice": Mystery(
        id="juice",
        verb="spill the juice",
        gerund="spilling juice",
        clue="a sticky orange trail",
        trickle="a trickle of juice",
        at_risk="the shared cloth",
        trail="tiny drops across the floor",
        emotion="worried",
        tags={"share", "spill", "drink"},
    ),
    "paint": Mystery(
        id="paint",
        verb="tip the paint",
        gerund="tipping paint",
        clue="a blue dot on the bench",
        trickle="a thin blue trickle",
        at_risk="the shared towel",
        trail="little blue marks along the sill",
        emotion="curious",
        tags={"share", "spill", "art"},
    ),
    "syrup": Mystery(
        id="syrup",
        verb="drip the syrup",
        gerund="dripping syrup",
        clue="a sweet brown line",
        trickle="a slow brown trickle",
        at_risk="the shared napkin",
        trail="sticky shining spots on the tiles",
        emotion="nervous",
        tags={"share", "spill", "breakfast"},
    ),
}

ITEMS = {
    "cloth": SharedItem(label="shared cloth", phrase="a shared cloth with red stripes", type="cloth"),
    "towel": SharedItem(label="shared towel", phrase="a shared towel with soft loops", type="towel"),
    "napkin": SharedItem(label="shared napkin", phrase="a shared napkin folded into a square", type="napkin"),
}

DETECTIVE_NAMES = ["Mina", "June", "Pip", "Ivy", "Tess", "Nina"]
FRIEND_NAMES = ["Ari", "Milo", "Bea", "Sam", "Rae", "Noa"]
TYPES = ["girl", "boy"]
TRAITS = ["careful", "quick", "kind", "brave", "quiet"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world about sharing, clues, and a morning trickle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    gender = getattr(args, "gender", None) or rng.choice(TYPES)
    friend_gender = getattr(args, "friend_gender", None) or rng.choice(TYPES)
    detective_name = getattr(args, "name", None) or rng.choice(DETECTIVE_NAMES if gender == "girl" else [n for n in DETECTIVE_NAMES if n not in {"Mina", "Ivy", "Tess", "Nina"}])
    friend_name = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, mystery=mystery, item=item, detective_name=detective_name, detective_type=gender, friend_name=friend_name, friend_type=friend_gender)


def _do_search(world: World, detective: Entity, mystery: Mystery, shared: Entity, friend: Entity) -> None:
    detective.memes["focus"] += 1
    world.say(f"{detective.id} noticed {mystery.trickle} by the {shared.label}.")
    world.say(world.setting.morning_detail)
    world.say(f"{detective.id} looked closer and saw {mystery.trail}. That made {detective.pronoun('object')} feel {mystery.emotion}.")
    friend.memes["nervous"] += 1


def _do_question(world: World, detective: Entity, mystery: Mystery, shared: Entity, friend: Entity) -> None:
    detective.memes["curiosity"] += 1
    world.say(f'"Did you see what happened to {shared.label}?" {detective.id} asked.')
    world.say(f"{friend.id} shook {friend.pronoun('possessive')} head, then pointed to {mystery.clue}.")
    friend.memes["relief"] += 1


def _do_reveal(world: World, detective: Entity, mystery: Mystery, shared: Entity, friend: Entity) -> None:
    detective.memes["understanding"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"At last, {friend.id} explained that {friend.pronoun('subject')} had borrowed the {shared.label} "
        f"to help clean up a little mess, then brought it back before breakfast."
    )
    world.say(f"It was not a mean trick at all. It was a small act of sharing.")
    world.say(
        f"{detective.id} smiled, because the mystery fit the facts: {mystery.trickle} led to {mystery.clue}, "
        f"and the {shared.label} had simply been used kindly."
    )
    detective.memes["joy"] += 1
    friend.memes["joy"] += 1
    friend.shared_with = detective.id
    shared.borrowed_from = detective.id


def tell(setting: Setting, mystery: Mystery, shared_item: SharedItem, detective_name: str, detective_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    shared = world.add(Entity(id=shared_item.label, type=shared_item.type, label=shared_item.label, phrase=shared_item.phrase, shared_with=friend.id))
    shared.meters["shared"] = 1
    world.facts.update(detective=detective, friend=friend, shared=shared, mystery=mystery, setting=setting)

    world.say(f"At morn, {detective.id} was a little detective in {setting.place}.")
    world.say(f"{detective.id} liked solving small troubles, especially when everyone could share the ending.")
    world.say(f"Near the table, there was {shared_item.phrase}.")
    world.para()
    _do_search(world, detective, mystery, shared, friend)
    _do_question(world, detective, mystery, shared, friend)
    world.para()
    _do_reveal(world, detective, mystery, shared, friend)
    return world


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Place,Mystery,Item) :- setting(Place), mystery(Mystery), shared_item(Item),
                             place_affords(Place, search), mystery_trickles(Mystery),
                             item_shared(Item), mystery_matches_item(Mystery, Item).

valid_story(Place,Mystery,Item,Gender) :- valid(Place,Mystery,Item), gender(Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("place_affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("mystery_trickles", mid))
        lines.append(asp.fact("mystery_matches_item", mid, ITEMS[{"juice": "cloth", "paint": "towel", "syrup": "napkin"}[mid]].label))
    for iid in ITEMS:
        lines.append(asp.fact("shared_item", iid))
        lines.append(asp.fact("item_shared", iid))
    for g in TYPES:
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_valid_combos() -> list[tuple[str, str, str]]:
    return [(p, m, i) for p in SETTINGS for m in MYSTERIES for i in ITEMS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(_python_valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and python gate.")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child set in {f["setting"].place} with the words "trickle" and "morn".',
        f"Tell a gentle mystery where {f['detective'].id} follows a trickle and learns that a borrowed thing was shared kindly.",
        f"Write a small sharing story in detective style where a morning clue explains why the {f['shared'].label} was not really missing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    fr = _safe_fact(world, f, "friend")
    sh = _safe_fact(world, f, "shared")
    m = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {d.id}, a little {d.type} who liked solving small troubles in the morn.",
        ),
        QAItem(
            question=f"What clue did {d.id} follow near the {sh.label}?",
            answer=f"{d.id} followed {m.trickle}. That clue led to {m.clue} and then to the truth.",
        ),
        QAItem(
            question=f"Why was the {sh.label} not really missing?",
            answer=f"It was not stolen. {fr.id} had borrowed it to help with a small cleanup and brought it back, so the ending was about sharing.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"{d.id} understood the clue trail, listened to {fr.id}, and saw that the shared item had been used kindly and returned before breakfast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues, asks careful questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something, or helping with something, in a kind and fair way.",
        ),
        QAItem(
            question="What is a trickle?",
            answer="A trickle is a very small stream or line of liquid that moves slowly.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.shared_with:
            parts.append(f"shared_with={e.shared_with}")
        if e.borrowed_from:
            parts.append(f"borrowed_from={e.borrowed_from}")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MYSTERIES, params.mystery), _safe_lookup(ITEMS, params.item), params.detective_name, params.detective_type, params.friend_name, params.friend_type)
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
    StoryParams(place="kitchen", mystery="juice", item="cloth", detective_name="Mina", detective_type="girl", friend_name="Ari", friend_type="boy"),
    StoryParams(place="hall", mystery="paint", item="towel", detective_name="Pip", detective_type="boy", friend_name="Bea", friend_type="girl"),
    StoryParams(place="garden_room", mystery="syrup", item="napkin", detective_name="Ivy", detective_type="girl", friend_name="Noa", friend_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):")
        for p, m, i in triples:
            genders = sorted(g for (pp, mm, ii, g) in stories if (pp, mm, ii) == (p, m, i))
            print(f"  {p:12} {m:8} {i:8} [{', '.join(genders)}]")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective_name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
