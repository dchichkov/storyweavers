#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mammal_vibrant_friendship_surprise_animal_story.py
===================================================================================

A standalone story world sketch for a tiny animal tale shaped by the seed words
"mammal" and "vibrant", with friendship and surprise as the main narrative
instruments.

Premise
-------
A small mammal and a friend are preparing a simple day together in a garden or
meadow. One animal wants to make something vibrant and cheerful; another animal
tries to keep the plan secret so the ending can be a surprise. The story turns on
a small obstacle -- a missing decoration, a shy friend, or a too-heavy gift -- and
resolves in a warm reveal where the friendship becomes visibly brighter.

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results eagerly
- includes StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- uses physical meters and emotional memes
- includes a Python reasonableness gate and inline ASP twin
- generates three Q&A sets from world state

The world is intentionally small: a few animal entities, a few objects, and a
forward-chained story engine with state-driven prose.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""  # "planner" | "helper" | "friend" | "parent"
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    color: str = ""
    edible: bool = False
    decorative: bool = False
    secret: bool = False
    heavy: bool = False
    glows: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "rabbit", "deer", "fox", "squirrel", "mouse", "hedgehog"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    scene: str
    season: str
    light: str
    feels: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Animal:
    id: str
    species: str
    label: str
    gender: str
    size: str
    trait: str
    role: str
    likes: str
    color: str = ""
    notes: list[str] = field(default_factory=list)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    color: str
    kind: str
    decorative: bool = False
    edible: bool = False
    secret: bool = False
    heavy: bool = False
    glows: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
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
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["surprise"] < THRESHOLD:
            continue
        sig = ("surprise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        e.memes["spark"] += 1
        out.append("__surprise__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["friendship"] < THRESHOLD:
            continue
        sig = ("friendship", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["trust"] += 1
        e.memes["warmth"] += 1
        out.append("__friendship__")
    return out


def _r_vibrant(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["vibrant"] < THRESHOLD:
            continue
        sig = ("vibrant", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.kind != "character":
            e.meters["bright"] += 1
            out.append(f"The {e.label_word} looked even more vibrant.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("surprise", "social", _r_surprise),
    Rule("friendship", "social", _r_friendship),
    Rule("vibrant", "physical", _r_vibrant),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(setting: Setting, surprise_obj: ObjectSpec, gift_obj: ObjectSpec) -> bool:
    if not surprise_obj.secret:
        return False
    if not gift_obj.decorative and not gift_obj.edible and not gift_obj.glows:
        return False
    if setting.season == "night" and not gift_obj.glows and not gift_obj.decorative:
        return False
    return True


def could_plan_surprise(friends: tuple[Animal, Animal], gift: ObjectSpec) -> bool:
    a, b = friends
    if a.role != "planner":
        return False
    if b.role != "helper":
        return False
    if "shy" in a.trait and gift.heavy:
        return False
    return True


def predict_reveal(world: World, gift_id: str) -> dict:
    sim = world.copy()
    _unwrap_gift(sim, sim.get(gift_id), narrate=False)
    return {
        "joy": sum(e.memes["joy"] for e in sim.characters()),
        "bright": sim.get(gift_id).meters["bright"],
    }


def _unwrap_gift(world: World, gift: Entity, narrate: bool = True) -> None:
    gift.meters["opened"] += 1
    gift.meters["surprise"] += 1
    gift.meters["vibrant"] += 1
    propagate(world, narrate=narrate)


def _build_scene(world: World, setting: Setting, planner: Entity, helper: Entity,
                 friend: Entity, gift: Entity) -> None:
    planner.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"On a bright {setting.season} morning, {planner.id} the {planner.type} "
        f"met {helper.id} in {setting.place}. {setting.scene}."
    )
    world.say(
        f"{planner.id} loved {planner.attrs.get('likes', 'small surprises')}, "
        f"and {helper.id} loved how a good friend could make a day feel better."
    )
    world.say(
        f"Together they noticed {friend.id}, a little mammal with a {gift.color} "
        f"smile, watching the {setting.light} from the edge of the path."
    )


def _prepare_surprise(world: World, planner: Entity, helper: Entity, gift: Entity,
                      setting: Setting) -> None:
    planner.meters["busy"] += 1
    helper.meters["busy"] += 1
    world.say(
        f"{planner.id} whispered to {helper.id}, \"Let's make something vibrant for "
        f"{gift.label_word}.\""
    )
    if gift.secret:
        world.say(
            f"{helper.id} nodded and covered the {gift.label} with leaves so the "
            f"surprise would stay hidden."
        )
    if gift.decorative:
        world.say(
            f"They tied on ribbons and flowers until the {gift.label_word} looked "
            f"vibrant against {setting.scene.split(',')[0].lower()}."
        )
    elif gift.edible:
        world.say(
            f"They packed the {gift.label} carefully, because the tasty surprise "
            f"needed to stay fresh."
        )
    elif gift.glows:
        world.say(
            f"They waited for the light to fade, then let the {gift.label} glow "
            f"softly like a tiny lantern."
        )


def _hurry_close(world: World, helper: Entity, planner: Entity, friend: Entity, gift: Entity) -> None:
    helper.meters["surprise"] += 1
    planner.memes["nervous"] += 1
    world.say(
        f"{helper.id} almost laughed out loud, because keeping a surprise secret "
        f"was hard when {friend.id} kept sniffing the air nearby."
    )


def _reveal(world: World, planner: Entity, helper: Entity, friend: Entity, gift: Entity) -> None:
    _unwrap_gift(world, gift)
    world.say(
        f"Then {planner.id} shouted, \"Surprise!\" and {helper.id} popped the cover "
        f"off the {gift.label}."
    )
    world.say(
        f"{friend.id} blinked, and their eyes went wide as the {gift.label} flashed "
        f"bright and vibrant in the sun."
    )


def _ending(world: World, planner: Entity, helper: Entity, friend: Entity, gift: Entity) -> None:
    planner.memes["joy"] += 1
    helper.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{friend.id} laughed, hugged both friends, and said it was the best kind "
        f"of surprise -- one made by a mammal who cared and a friend who helped."
    )
    world.say(
        f"By the end of the day, the {gift.label} sat on the grass, bright and vibrant, "
        f"while the three friends sat close together and smiled."
    )


def tell(setting: Setting, planner_spec: Animal, helper_spec: Animal,
         friend_spec: Animal, gift_spec: ObjectSpec) -> World:
    world = World()
    planner = world.add(Entity(
        id=planner_spec.id, kind="character", type=planner_spec.species,
        label=planner_spec.label, role="planner", traits=[planner_spec.trait],
        attrs={"likes": planner_spec.likes, "gender": planner_spec.gender},
        color=planner_spec.color,
    ))
    helper = world.add(Entity(
        id=helper_spec.id, kind="character", type=helper_spec.species,
        label=helper_spec.label, role="helper", traits=[helper_spec.trait],
        attrs={"likes": helper_spec.likes, "gender": helper_spec.gender},
        color=helper_spec.color,
    ))
    friend = world.add(Entity(
        id=friend_spec.id, kind="character", type=friend_spec.species,
        label=friend_spec.label, role="friend", traits=[friend_spec.trait],
        attrs={"likes": friend_spec.likes, "gender": friend_spec.gender},
        color=friend_spec.color,
    ))
    gift = world.add(Entity(
        id=gift_spec.id, kind="thing", type=gift_spec.kind, label=gift_spec.label,
        decorative=gift_spec.decorative, edible=gift_spec.edible, secret=gift_spec.secret,
        heavy=gift_spec.heavy, glows=gift_spec.glows, color=gift_spec.color,
    ))
    _build_scene(world, setting, planner, helper, friend, gift)
    world.para()
    _prepare_surprise(world, planner, helper, gift, setting)
    if gift.heavy:
        _hurry_close(world, helper, planner, friend, gift)
    world.para()
    _reveal(world, planner, helper, friend, gift)
    _ending(world, planner, helper, friend, gift)
    world.facts.update(
        setting=setting,
        planner=planner,
        helper=helper,
        friend=friend,
        gift=gift,
        surprise_obj=gift,
        reveal=True,
        joy=sum(e.memes["joy"] for e in world.characters()),
        friendship=sum(e.memes["friendship"] for e in world.characters()),
    )
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the meadow",
        scene="The grass was soft, and wildflowers bobbed in a breezy line",
        season="morning",
        light="sunlight",
        feels="open",
    ),
    "garden": Setting(
        id="garden",
        place="the garden",
        scene="The hedges made a green tunnel, and bees hummed near the blossoms",
        season="afternoon",
        light="warm light",
        feels="calm",
    ),
    "pond": Setting(
        id="pond",
        place="the pond",
        scene="Reeds leaned over the water, and lily pads floated like little boats",
        season="evening",
        light="golden light",
        feels="quiet",
    ),
}

ANIMALS = {
    "rabbit": Animal("rabbit", "rabbit", "rabbit", "girl", "small", "gentle", "planner", "gather clover"),
    "squirrel": Animal("squirrel", "squirrel", "squirrel", "boy", "small", "quick", "helper", "gather nuts"),
    "deer": Animal("deer", "deer", "deer", "girl", "small", "quiet", "friend", "watch butterflies"),
    "mouse": Animal("mouse", "mouse", "mouse", "boy", "tiny", "shy", "friend", "sing softly"),
    "hedgehog": Animal("hedgehog", "hedgehog", "hedgehog", "girl", "small", "careful", "friend", "carry berries"),
    "fox": Animal("fox", "fox", "fox", "boy", "small", "bright", "helper", "tell stories"),
}

OBJECTS = {
    "basket": ObjectSpec("basket", "basket", "a basket", "vibrant red", "thing", decorative=True, secret=True, tags={"basket", "gift"}),
    "scarf": ObjectSpec("scarf", "scarf", "a scarf", "vibrant blue", "thing", decorative=True, secret=True, tags={"scarf", "gift"}),
    "berries": ObjectSpec("berries", "berries", "a bowl of berries", "bright purple", "thing", edible=True, secret=True, tags={"berries", "gift"}),
    "lantern": ObjectSpec("lantern", "lantern", "a tiny lantern", "gold", "thing", glows=True, secret=True, tags={"lantern", "gift"}),
    "flowers": ObjectSpec("flowers", "flowers", "a garland of flowers", "vibrant yellow", "thing", decorative=True, secret=True, tags={"flowers", "gift"}),
    "ribbon": ObjectSpec("ribbon", "ribbon", "a ribbon bundle", "vibrant pink", "thing", decorative=True, secret=True, tags={"ribbon", "gift"}),
}

GIRL_NAMES = ["Lily", "Mira", "Nina", "Tia", "Fern", "Ivy"]
BOY_NAMES = ["Pip", "Otto", "Finn", "Theo", "Milo", "Jasper"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    planner: str
    helper: str
    friend: str
    gift: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, planner in ANIMALS.items():
            if planner.role != "planner":
                continue
            for hid, helper in ANIMALS.items():
                if helper.role != "helper" or hid == pid:
                    continue
                for fid, friend in ANIMALS.items():
                    if friend.role != "friend" or fid in {pid, hid}:
                        continue
                    for gid, gift in OBJECTS.items():
                        if is_reasonable(setting, gift, gift) and could_plan_surprise((planner, helper), gift):
                            combos.append((sid, pid, hid, fid, gid))
    return combos


def explanation_for_rejection(setting: Setting, gift: ObjectSpec) -> str:
    if not gift.secret:
        return "(No story: the surprise object is not secret, so there is no surprise to build."
    if gift.heavy:
        return "(No story: this gift is too heavy for a small surprise story."
    return "(No story: this combination is too ordinary to make a vivid surprise story.)"


def choose_name(rng: random.Random, species: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if species in {"rabbit", "deer", "hedgehog"} else BOY_NAMES
    pool = [n for n in pool if n not in avoid]
    return rng.choice(pool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: small mammal friends, a vibrant surprise, and a warm reveal."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--planner", choices=ANIMALS)
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--gift", choices=OBJECTS)
    ap.add_argument("--name", choices=[*GIRL_NAMES, *BOY_NAMES])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.planner is None or c[1] == args.planner)
              and (args.helper is None or c[2] == args.helper)
              and (args.friend is None or c[3] == args.friend)
              and (args.gift is None or c[4] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, planner, helper, friend, gift = rng.choice(sorted(combos))
    return StoryParams(setting, planner, helper, friend, gift)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    planner = f["planner"]
    helper = f["helper"]
    friend = f["friend"]
    gift = f["gift"]
    return [
        f'Write an animal story for a young child set in {setting.place} about '
        f'{planner.id} and {helper.id} planning a surprise for {friend.id}. Include '
        f'the words "mammal" and "vibrant".',
        f"Tell a friendship story where {planner.id} and {helper.id} keep a secret "
        f"gift for {friend.id} and the reveal feels warm and happy.",
        f"Write a short animal story with a vibrant surprise, a mammal friend, and "
        f"a gentle ending in {setting.place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    planner = f["planner"]
    helper = f["helper"]
    friend = f["friend"]
    gift = f["gift"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {planner.id}, {helper.id}, and {friend.id}, three animal friends in {setting.place}. "
         f"They work together so the surprise feels kind and close."),
        ("What were they trying to do?",
         f"They were trying to make a surprise for {friend.id}. {planner.id} and {helper.id} wanted it to be "
         f"vibrant, because they hoped the happy color would make the moment feel special."),
        ("Why did they keep whispering?",
         f"They kept whispering because the gift was supposed to stay secret until the reveal. That is what made "
         f"the story a surprise instead of an ordinary gift."),
        ("What does it mean that one friend is a mammal?",
         f"A mammal is an animal that is warm-bodied and that feeds its babies milk when they are little. In this "
         f"story, the friends are mammals, so they are the kind of animals who cuddle, plan, and share food."),
    ]
    if f.get("reveal"):
        qa.append((
            f"What happened when the surprise was opened?",
            f"The cover came off, and {gift.label} looked bright and vibrant. {friend.id} smiled big, because the "
            f"surprise was made with friendship and care."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the three friends sitting together and smiling beside {gift.label}. The bright surprise "
            f"showed that their friendship had grown warm and happy."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mammal", "friendship", "surprise", "vibrant"}
    gift = f["gift"]
    if gift.decorative:
        tags.add("decorative")
    if gift.edible:
        tags.add("edible")
    if gift.glows:
        tags.add("glows")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
        if e.color:
            bits.append(f"color={e.color}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


KNOWLEDGE = {
    "mammal": [(
        "What is a mammal?",
        "A mammal is an animal that has fur or hair, is warm-bodied, and feeds its babies milk when they are little."
    )],
    "friendship": [(
        "What is friendship?",
        "Friendship is when animals or people care about each other, help each other, and enjoy being together."
    )],
    "surprise": [(
        "What is a surprise?",
        "A surprise is something kept secret until the right moment, so the big reveal feels exciting and happy."
    )],
    "vibrant": [(
        "What does vibrant mean?",
        "Vibrant means full of bright life and strong color, like flowers or ribbons that really stand out."
    )],
    "basket": [(
        "What is a basket for?",
        "A basket can carry flowers, fruit, or small gifts, so it helps when friends bring something to share."
    )],
    "scarf": [(
        "What is a scarf for?",
        "A scarf can keep you warm and also add a bright color to your outfit, which makes it feel cheerful."
    )],
    "lantern": [(
        "What does a lantern do?",
        "A lantern gives light so you can see in dim places. A small lantern can also make a celebration glow softly."
    )],
}
KNOWLEDGE_ORDER = ["mammal", "friendship", "surprise", "vibrant", "basket", "scarf", "lantern"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("role", aid, a.role))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("gift", oid))
        if o.secret:
            lines.append(asp.fact("secret", oid))
        if o.decorative:
            lines.append(asp.fact("decorative", oid))
        if o.edible:
            lines.append(asp.fact("edible", oid))
        if o.glows:
            lines.append(asp.fact("glows", oid))
        if o.heavy:
            lines.append(asp.fact("heavy", oid))
    return "\n".join(lines)


ASP_RULES = r"""
% A surprise story needs a planner, helper, and a secret gift.
compatible(S, P, H, F, G) :- setting(S), animal(P), animal(H), animal(F), gift(G),
                             role(P, planner), role(H, helper), role(F, friend),
                             P != H, P != F, H != F,
                             secret(G).

% A story is reasonable when the gift can plausibly be used as a surprise.
reasonable(S, P, H, F, G) :- compatible(S, P, H, F, G).

% Story mood: friendship always contributes; the reveal makes the ending bright.
story_ready(P) :- role(P, planner).
story_ready(H) :- role(H, helper).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/5."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH in the gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def tell(setting: Setting, planner_spec: Animal, helper_spec: Animal,
         friend_spec: Animal, gift_spec: ObjectSpec) -> World:
    world = World()
    planner = world.add(Entity(
        id=planner_spec.id, kind="character", type=planner_spec.species,
        label=planner_spec.label, role="planner", traits=[planner_spec.trait],
        attrs={"likes": planner_spec.likes, "gender": planner_spec.gender},
    ))
    helper = world.add(Entity(
        id=helper_spec.id, kind="character", type=helper_spec.species,
        label=helper_spec.label, role="helper", traits=[helper_spec.trait],
        attrs={"likes": helper_spec.likes, "gender": helper_spec.gender},
    ))
    friend = world.add(Entity(
        id=friend_spec.id, kind="character", type=friend_spec.species,
        label=friend_spec.label, role="friend", traits=[friend_spec.trait],
        attrs={"likes": friend_spec.likes, "gender": friend_spec.gender},
    ))
    gift = world.add(Entity(
        id=gift_spec.id, kind="thing", type=gift_spec.kind, label=gift_spec.label,
        color=gift_spec.color, decorative=gift_spec.decorative, edible=gift_spec.edible,
        secret=gift_spec.secret, heavy=gift_spec.heavy, glows=gift_spec.glows,
    ))

    planner.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"In {setting.place}, {planner.id} the little mammal met {helper.id} and "
        f"{friend.id} under {setting.light}."
    )
    world.say(
        f"The day felt {setting.feels}, and the three animals wanted to share a "
        f"kind friendship story."
    )
    world.para()
    world.say(
        f"{planner.id} whispered that they were making a surprise for {friend.id}, "
        f"and {helper.id} nodded so the secret could stay hidden."
    )
    world.say(
        f"They chose {gift.label_word}, because it could be {gift.color} and vibrant "
        f"without being hard to carry."
    )
    gift.meters["vibrant"] += 1
    gift.meters["surprise"] += 1
    if gift.glows:
        gift.meters["glow"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{helper.id} tucked the surprise behind some leaves while {planner.id} "
        f"kept {friend.id} busy with a story about beetles and clover."
    )
    friend.memes["curious"] += 1
    planner.memes["pride"] += 1
    helper.memes["pride"] += 1

    world.para()
    _unwrap_gift(world, gift)
    world.say(
        f"Then the cover came off, and {gift.label} shone vibrant and bright."
    )
    world.say(
        f"{friend.id} laughed, hopped close, and hugged the other two animals."
    )
    planner.memes["joy"] += 1
    helper.memes["joy"] += 1
    friend.memes["joy"] += 1
    planner.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"By the end, the friends sat together in the grass, and the vibrant gift "
        f"made the whole scene look warmer."
    )

    world.facts.update(
        setting=setting,
        planner=planner,
        helper=helper,
        friend=friend,
        gift=gift,
        reveal=True,
        friendship=True,
    )
    return world


CURATED = [
    StoryParams("meadow", "rabbit", "squirrel", "deer", "basket"),
    StoryParams("garden", "hedgehog", "fox", "mouse", "flowers"),
    StoryParams("pond", "rabbit", "fox", "deer", "lantern"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ANIMALS[params.planner], ANIMALS[params.helper], ANIMALS[params.friend], OBJECTS[params.gift])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def explain_rejection(setting: Setting, gift: ObjectSpec) -> str:
    if not gift.secret:
        return "(No story: the chosen gift is not secret, so there is no surprise to tell.)"
    return "(No story: this combination does not make a plausible friendship surprise story.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show reasonable/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for s, p, h, f, g in combos:
            print(f"  {s:8} {p:10} {h:10} {f:10} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.planner}, {p.helper}, {p.friend} ({p.gift}, {p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
