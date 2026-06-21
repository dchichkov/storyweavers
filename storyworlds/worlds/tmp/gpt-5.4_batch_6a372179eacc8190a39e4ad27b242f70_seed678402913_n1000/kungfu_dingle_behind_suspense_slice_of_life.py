#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kungfu_dingle_behind_suspense_slice_of_life.py
=========================================================================

A small suspenseful slice-of-life storyworld about a child practicing kungfu,
hearing a strange dingle from behind something nearby, and deciding how to
check it safely.

The core world model is simple and state-driven:

- A child is practicing a careful, playful routine.
- A hidden source makes a small "dingle" sound behind a barrier.
- The child feels suspense and considers what might be there.
- A checking method changes risk and calm.
- The reveal proves what changed in the ordinary little world.

Reasonableness constraint:
- Only sources that can plausibly make a little bell-like dingle are allowed.
- Only barriers that fit the setting and can plausibly hide the source are allowed.
- Only sensible checking methods are accepted for generation.

ASP twin:
- An inline declarative reasoner mirrors the valid-combo gate and outcome model.
- `--verify` checks Python/ASP parity and runs smoke-generation tests.

Run it:
    python storyworlds/worlds/gpt-5.4/kungfu_dingle_behind_suspense_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/kungfu_dingle_behind_suspense_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/kungfu_dingle_behind_suspense_slice_of_life.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/kungfu_dingle_behind_suspense_slice_of_life.py --qa
    python storyworlds/worlds/gpt-5.4/kungfu_dingle_behind_suspense_slice_of_life.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    barrier_ids: set[str]
    source_ids: set[str]
    practice_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Barrier:
    id: str
    label: str
    phrase: str
    place_hint: str
    hides: bool = True
    outdoors: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    sound: str
    safe: bool = True
    mobile: bool = False
    bell_like: bool = True
    reveal_text: str = ""
    calm_end: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    noise: int
    care: int
    with_helper: bool = False
    text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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


def _r_hidden_sound(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    barrier = world.get("barrier")
    source = world.get("source")
    if barrier.meters["between"] >= THRESHOLD and source.meters["dingled"] >= THRESHOLD:
        sig = ("hidden_sound", barrier.id, source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["suspense"] += 1
            hero.memes["curiosity"] += 1
            out.append("__suspense__")
    return out


def _r_risky_rush(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    method = world.get("method")
    if method.attrs.get("noise", 0) >= 2 and hero.memes["suspense"] >= THRESHOLD:
        sig = ("risky_rush", method.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["stumble_risk"] += 1
            out.append("__risk__")
    return out


def _r_helper_calms(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.entities.get("helper")
    method = world.get("method")
    if helper and method.attrs.get("with_helper") and hero.memes["suspense"] >= THRESHOLD:
        sig = ("helper_calms", helper.id, method.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["calm"] += 1
            hero.memes["suspense"] = max(0.0, hero.memes["suspense"] - 0.5)
            out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="hidden_sound", tag="social", apply=_r_hidden_sound),
    Rule(name="risky_rush", tag="physical", apply=_r_risky_rush),
    Rule(name="helper_calms", tag="social", apply=_r_helper_calms),
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
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "hallway": Setting(
        id="hallway",
        place="the hallway outside the apartment kitchen",
        barrier_ids={"curtain", "closet_door"},
        source_ids={"bike", "cat", "keys"},
        practice_detail="The floor was smooth enough for careful steps and turns.",
        tags={"home"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the little courtyard behind the building",
        barrier_ids={"gate", "hedge"},
        source_ids={"bike", "cat", "wind_chime"},
        practice_detail="A patch of warm stone made a tiny practice square in the sun.",
        tags={"home", "outdoor"},
    ),
    "laundry_room": Setting(
        id="laundry_room",
        place="the shared laundry room at the end of the hall",
        barrier_ids={"sheet", "closet_door"},
        source_ids={"cat", "keys", "wind_chime"},
        practice_detail="The hum of the machines made the room feel busy and ordinary.",
        tags={"home"},
    ),
}

BARRIERS = {
    "curtain": Barrier(
        id="curtain",
        label="curtain",
        phrase="the long curtain",
        place_hint="near the window",
        hides=True,
        outdoors=False,
        tags={"soft", "inside"},
    ),
    "closet_door": Barrier(
        id="closet_door",
        label="closet door",
        phrase="the narrow closet door",
        place_hint="by the wall",
        hides=True,
        outdoors=False,
        tags={"door", "inside"},
    ),
    "gate": Barrier(
        id="gate",
        label="gate",
        phrase="the wooden gate",
        place_hint="at the far end of the courtyard",
        hides=True,
        outdoors=True,
        tags={"outside", "door"},
    ),
    "hedge": Barrier(
        id="hedge",
        label="hedge",
        phrase="the thick hedge",
        place_hint="along the bricks",
        hides=True,
        outdoors=True,
        tags={"outside", "plants"},
    ),
    "sheet": Barrier(
        id="sheet",
        label="sheet",
        phrase="the hanging sheet",
        place_hint="on the drying line",
        hides=True,
        outdoors=False,
        tags={"laundry", "inside"},
    ),
}

SOURCES = {
    "bike": Source(
        id="bike",
        label="bicycle",
        phrase="a bicycle with a shiny bell",
        sound="dingle",
        safe=True,
        mobile=False,
        bell_like=True,
        reveal_text="leaning there was a bicycle, and the little bell gave one last dingle as it settled",
        calm_end="Soon the place did not feel mysterious at all, only small and familiar again.",
        tags={"bike", "bell"},
    ),
    "cat": Source(
        id="cat",
        label="cat",
        phrase="the neighbor's striped cat with a collar bell",
        sound="dingle",
        safe=True,
        mobile=True,
        bell_like=True,
        reveal_text="out slipped the neighbor's striped cat, its collar giving a tiny dingle as it brushed past",
        calm_end="The cat rubbed against their legs as if it had been part of the afternoon all along.",
        tags={"cat", "bell", "pet"},
    ),
    "keys": Source(
        id="keys",
        label="keys",
        phrase="a ring of keys hanging from a hook",
        sound="dingle",
        safe=True,
        mobile=False,
        bell_like=True,
        reveal_text="there was only a ring of keys tapping softly against a hook, making a shy dingle each time they swung",
        calm_end="Nothing dangerous had been waiting there, only a small household sound.",
        tags={"keys", "metal"},
    ),
    "wind_chime": Source(
        id="wind_chime",
        label="wind chime",
        phrase="a little wind chime",
        sound="dingle",
        safe=True,
        mobile=True,
        bell_like=True,
        reveal_text="a little wind chime moved in the breeze, and its pieces touched with a silver dingle",
        calm_end="The sound turned from spooky to pretty as soon as they knew what it was.",
        tags={"wind", "chime"},
    ),
}

METHODS = {
    "call_and_peek": Method(
        id="call_and_peek",
        label="call out and peek slowly",
        sense=3,
        noise=0,
        care=3,
        with_helper=False,
        text='stood still first, then called, "Hello?" before peeking slowly',
        tags={"careful"},
    ),
    "ask_helper": Method(
        id="ask_helper",
        label="ask a grown-up to check together",
        sense=3,
        noise=0,
        care=3,
        with_helper=True,
        text="went to get a grown-up and came back together to look",
        tags={"help", "careful"},
    ),
    "slide_open": Method(
        id="slide_open",
        label="slide it open carefully",
        sense=2,
        noise=1,
        care=2,
        with_helper=False,
        text="took a breath and slid it open carefully",
        tags={"careful"},
    ),
    "rush": Method(
        id="rush",
        label="rush over and yank it aside",
        sense=1,
        noise=2,
        care=0,
        with_helper=False,
        text="rushed over and yanked it aside at once",
        tags={"impulsive"},
    ),
}


def source_fits_setting(setting: Setting, source: Source) -> bool:
    return source.id in setting.source_ids and source.bell_like


def barrier_fits_setting(setting: Setting, barrier: Barrier) -> bool:
    return barrier.id in setting.barrier_ids and barrier.hides


def valid_combo(setting_id: str, barrier_id: str, source_id: str) -> bool:
    setting = SETTINGS[setting_id]
    barrier = BARRIERS[barrier_id]
    source = SOURCES[source_id]
    return barrier_fits_setting(setting, barrier) and source_fits_setting(setting, source)


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def best_method() -> Method:
    return max(METHODS.values(), key=lambda m: m.sense)


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    if method.sense < SENSE_MIN:
        return "startled"
    if method.with_helper:
        return "shared"
    return "calm"


def predict_check(setting: Setting, barrier: Barrier, source: Source, method: Method) -> dict:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params_gender_default(), role="hero"))
    world.add(Entity(id="barrier", type="barrier", label=barrier.label))
    world.add(Entity(id="source", type="source", label=source.label))
    world.add(Entity(id="method", type="method", label=method.label, attrs={"noise": method.noise, "with_helper": method.with_helper}))
    world.get("barrier").meters["between"] += 1
    world.get("source").meters["dingled"] += 1
    if method.with_helper:
        world.add(Entity(id="helper", kind="character", type="mother", role="helper"))
    propagate(world, narrate=False)
    return {
        "suspense": hero.memes["suspense"],
        "stumble_risk": hero.meters["stumble_risk"],
        "calm": hero.memes["calm"],
    }


def params_gender_default() -> str:
    return "girl"


def introduce(world: World, hero: Entity, setting: Setting, practice: str) -> None:
    hero.memes["focus"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"After the day's chores were done, {hero.id} found a little patch of space in {setting.place} to practice {practice}."
    )
    world.say(setting.practice_detail)
    world.say(
        f"{hero.pronoun().capitalize()} moved through the steps slowly, pretending each careful block and turn belonged to a real kungfu hero."
    )


def sound_appears(world: World, hero: Entity, barrier_ent: Entity, source_ent: Entity, barrier: Barrier) -> None:
    barrier_ent.meters["between"] += 1
    source_ent.meters["dingled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, from behind {barrier.phrase} {barrier.place_hint}, came a small sound: dingle."
    )
    world.say(
        f"{hero.id} stopped with one foot in the air. The hallway that had felt ordinary a moment ago suddenly seemed to be holding its breath."
        if world.facts["setting"].id != "courtyard"
        else f"{hero.id} stopped with one foot in the air. The sunny courtyard suddenly seemed very still around that one bright dingle."
    )


def imagine(world: World, hero: Entity, barrier: Barrier) -> None:
    hero.memes["imagination"] += 1
    if barrier.id in {"curtain", "sheet"}:
        world.say(
            f"The cloth hardly moved, which somehow made it stranger. Something was there behind it, but {hero.id} could not tell what."
        )
    elif barrier.id == "hedge":
        world.say(
            f"The leaves gave no answer. They only made a green wall, hiding whatever was behind them."
        )
    else:
        world.say(
            f"{hero.id} stared at it and listened. Whatever was behind it did not show itself right away."
        )


def choose_method(world: World, hero: Entity, helper: Optional[Entity], method: Method) -> None:
    method_ent = world.add(
        Entity(
            id="method",
            type="method",
            label=method.label,
            attrs={"noise": method.noise, "with_helper": method.with_helper, "care": method.care},
        )
    )
    if helper is not None:
        world.entities["helper"] = helper
    propagate(world, narrate=False)
    if method.with_helper and helper is not None:
        world.say(
            f"Instead of hurrying, {hero.id} {method.text}. {helper.label_word.capitalize()} kept a hand on the latch and smiled the small smile that meant slow was smart."
        )
    else:
        world.say(
            f"Instead of leaping back into the practice kicks, {hero.id} {method.text}."
        )
    world.facts["predicted"] = {
        "stumble_risk": hero.meters["stumble_risk"],
        "calm": hero.memes["calm"],
        "suspense": hero.memes["suspense"],
    }
    world.facts["method_ent"] = method_ent


def reveal(world: World, hero: Entity, source: Source, method: Method) -> None:
    source_ent = world.get("source")
    source_ent.meters["revealed"] += 1
    hero.memes["relief"] += 1
    hero.memes["calm"] += 1
    if method.sense < SENSE_MIN:
        hero.meters["startled"] += 1
        world.say(
            f"For one quick second, {hero.id}'s heart jumped. Then the mystery broke open: {source.reveal_text}."
        )
    else:
        world.say(
            f"And then the mystery opened into something simple: {source.reveal_text}."
        )


def ending(world: World, hero: Entity, helper: Optional[Entity], source: Source, practice: str, method: Method) -> None:
    if method.with_helper and helper is not None:
        hero.memes["love"] += 1
        world.say(
            f"{helper.label_word.capitalize()} gave a soft laugh, and {hero.id} laughed too, a little embarrassed and a lot relieved."
        )
    elif method.sense < SENSE_MIN:
        world.say(
            f"{hero.id} pressed a hand to {hero.pronoun('possessive')} chest, then grinned once the surprise was over."
        )
    else:
        world.say(
            f"{hero.id} let out the breath {hero.pronoun()} had been saving."
        )
    world.say(source.calm_end)
    world.say(
        f"After that, {hero.id} went back to {practice}, but the next moves were steadier. The world had not turned into anything dangerous after all."
    )


def tell(
    setting: Setting,
    barrier: Barrier,
    source: Source,
    method: Method,
    hero_name: str,
    hero_gender: str,
    helper_type: str,
    practice: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, role="hero", label=hero_name))
    hero.id = hero_name
    world.entities[hero_name] = world.entities.pop("hero")
    hero = world.get(hero_name)
    barrier_ent = world.add(Entity(id="barrier", type="barrier", label=barrier.label, phrase=barrier.phrase))
    source_ent = world.add(Entity(id="source", type="source", label=source.label, phrase=source.phrase))
    helper = None
    if method.with_helper:
        helper = world.add(Entity(id="helper", kind="character", type=helper_type, role="helper", label="the helper"))
    world.facts.update(
        setting=setting,
        barrier=barrier,
        source_cfg=source,
        method=method,
        hero=hero,
        helper=helper,
        practice=practice,
    )

    introduce(world, hero, setting, practice)
    world.para()
    sound_appears(world, hero, barrier_ent, source_ent, barrier)
    imagine(world, hero, barrier)
    world.para()
    choose_method(world, hero, helper, method)
    reveal(world, hero, source, method)
    ending(world, hero, helper, source, practice, method)

    world.facts.update(
        barrier_ent=barrier_ent,
        source_ent=source_ent,
        outcome=outcome_of(
            StoryParams(
                setting=setting.id,
                barrier=barrier.id,
                source=source.id,
                method=method.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                helper=helper_type,
                practice=practice,
            )
        ),
        suspense=hero.memes["suspense"],
        relief=hero.memes["relief"],
        startled=hero.meters["startled"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for barrier_id in BARRIERS:
            for source_id in SOURCES:
                if valid_combo(setting_id, barrier_id, source_id):
                    combos.append((setting_id, barrier_id, source_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    barrier: str
    source: str
    method: str
    hero_name: str
    hero_gender: str
    helper: str
    practice: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "kungfu": [
        (
            "What is kungfu practice?",
            "Kungfu practice is a set of careful moves like stances, blocks, and kicks. People do it slowly at first so they can stay balanced and in control.",
        )
    ],
    "bell": [
        (
            "What does a bell sound like?",
            "A small bell often makes a clear ringing sound, like dingle or ding. The sound can seem mysterious when you hear it before you see what made it.",
        )
    ],
    "curiosity": [
        (
            "What can you do when a strange sound makes you curious?",
            "You can stop, listen, and check carefully instead of rushing. Going slowly helps you learn what the sound is without startling yourself.",
        )
    ],
    "help": [
        (
            "When should a child ask a grown-up to help check something unknown?",
            "A child should ask a grown-up when something feels uncertain or a little scary. Checking together can make the situation calmer and safer.",
        )
    ],
    "bike": [
        (
            "Why might a bicycle make a little dingle sound?",
            "A bicycle can have a bell on the handlebars. If the bell is bumped or the bike settles against something, it can ring softly.",
        )
    ],
    "cat": [
        (
            "Why might a cat make a dingle sound?",
            "Some cats wear collars with tiny bells. When they walk or brush past things, the bell can make a small ringing sound.",
        )
    ],
    "keys": [
        (
            "Why do hanging keys make noise?",
            "Keys are made of metal, so when they tap together or hit a hook they can make a light clinking sound. In a quiet place, that sound can stand out a lot.",
        )
    ],
    "wind": [
        (
            "What is a wind chime?",
            "A wind chime is something that hangs up and makes soft ringing sounds when the air moves it. It can sound surprising if you hear it before you see it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["kungfu", "bell", "curiosity", "help", "bike", "cat", "keys", "wind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    barrier = f["barrier"]
    practice = f["practice"]
    source = f["source_cfg"]
    return [
        f'Write a suspenseful slice-of-life story for a 3-to-5-year-old that includes the words "kungfu", "dingle", and "behind".',
        f"Tell a gentle everyday story where {hero.id} is practicing {practice} in {setting.place}, hears a dingle from behind {barrier.phrase}, and slowly discovers what made it.",
        f"Write a small suspense story with a calm ending where an ordinary hidden sound turns out to be {source.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    barrier = f["barrier"]
    source = f["source_cfg"]
    method = f["method"]
    helper = f["helper"]
    practice = f["practice"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was practicing {practice}. The story stays close to one ordinary afternoon and one surprising sound.",
        ),
        (
            f"What made the afternoon feel suspenseful?",
            f"{hero.id} heard a small dingle from behind {barrier.phrase} in {setting.place} and could not see what caused it. The sound changed the mood because it came from a hidden place all at once.",
        ),
        (
            f"What was {hero.id} doing before the sound?",
            f"{hero.id} was practicing {practice} and trying to move like a kungfu hero. That calm practice made the sudden dingle stand out even more.",
        ),
        (
            f"How did {hero.id} check what was behind {barrier.phrase}?",
            f"{hero.id} chose to {method.label}. That mattered because going slowly kept the mystery from turning into a bigger scare.",
        ),
        (
            "What was really making the dingle sound?",
            f"It was {source.phrase}. Once it was revealed, the strange sound became part of the ordinary day again.",
        ),
    ]
    if helper is not None:
        qa.append(
            (
                f"Why did {hero.id} get help?",
                f"{hero.id} asked {helper.label_word} to come along because the hidden sound felt uncertain. Checking together made the moment calmer, and {hero.id} could borrow the grown-up's steady feeling.",
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} feel at the end?",
                f"{hero.id} felt relieved and steadier. Knowing what had been there behind {barrier.phrase} made the place feel normal again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kungfu", "bell", "curiosity"}
    method = world.facts["method"]
    source = world.facts["source_cfg"]
    if method.with_helper:
        tags.add("help")
    if source.id == "bike":
        tags.add("bike")
    elif source.id == "cat":
        tags.add("cat")
    elif source.id == "keys":
        tags.add("keys")
    elif source.id == "wind_chime":
        tags.add("wind")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="hallway",
        barrier="curtain",
        source="keys",
        method="call_and_peek",
        hero_name="Mia",
        hero_gender="girl",
        helper="mother",
        practice="a kungfu stepping pattern",
    ),
    StoryParams(
        setting="courtyard",
        barrier="gate",
        source="bike",
        method="ask_helper",
        hero_name="Ben",
        hero_gender="boy",
        helper="father",
        practice="a kungfu balance drill",
    ),
    StoryParams(
        setting="courtyard",
        barrier="hedge",
        source="cat",
        method="slide_open",
        hero_name="Lily",
        hero_gender="girl",
        helper="mother",
        practice="a kungfu kick-and-block game",
    ),
    StoryParams(
        setting="laundry_room",
        barrier="sheet",
        source="cat",
        method="call_and_peek",
        hero_name="Noah",
        hero_gender="boy",
        helper="father",
        practice="a kungfu tiger pose",
    ),
    StoryParams(
        setting="courtyard",
        barrier="hedge",
        source="wind_chime",
        method="ask_helper",
        hero_name="Zoe",
        hero_gender="girl",
        helper="mother",
        practice="a kungfu breathing routine",
    ),
]


def explain_combo_rejection(setting_id: str, barrier_id: str, source_id: str) -> str:
    setting = SETTINGS.get(setting_id)
    barrier = BARRIERS.get(barrier_id)
    source = SOURCES.get(source_id)
    if setting is None or barrier is None or source is None:
        return "(No story: one of the requested options is unknown.)"
    if barrier.id not in setting.barrier_ids:
        return (
            f"(No story: {barrier.phrase} does not fit naturally in {setting.place}. "
            f"Pick a barrier the setting can actually contain.)"
        )
    if source.id not in setting.source_ids:
        return (
            f"(No story: {source.phrase} is not a natural hidden source in {setting.place}. "
            f"Pick a source that plausibly belongs there.)"
        )
    if not source.bell_like:
        return (
            f"(No story: {source.phrase} would not make a little dingle sound, so the suspense premise does not work.)"
        )
    return "(No story: this setting, barrier, and source do not make a reasonable hidden-sound story.)"


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). This world prefers slow, careful checking. "
        f"Try: {better}.)"
    )


ASP_RULES = r"""
barrier_fits(S, B) :- setting(S), barrier(B), allows_barrier(S, B), hides(B).
source_fits(S, Src) :- setting(S), source(Src), allows_source(S, Src), bell_like(Src).
valid(S, B, Src) :- barrier_fits(S, B), source_fits(S, Src).

sensible(M) :- method(M), sense(M, V), sense_min(Min), V >= Min.

outcome(shared) :- chosen_method(M), helper_method(M), sensible(M).
outcome(calm) :- chosen_method(M), sensible(M), not helper_method(M).
outcome(startled) :- chosen_method(M), method(M), not sensible(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for barrier_id in sorted(setting.barrier_ids):
            lines.append(asp.fact("allows_barrier", setting_id, barrier_id))
        for source_id in sorted(setting.source_ids):
            lines.append(asp.fact("allows_source", setting_id, source_id))
    for barrier_id, barrier in BARRIERS.items():
        lines.append(asp.fact("barrier", barrier_id))
        if barrier.hides:
            lines.append(asp.fact("hides", barrier_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.bell_like:
            lines.append(asp.fact("bell_like", source_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.with_helper:
            lines.append(asp.fact("helper_method", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_method", params.method)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_methods = {m.id for m in sensible_methods()}
    asp_methods = set(asp_sensible_methods())
    if py_methods == asp_methods:
        print(f"OK: sensible methods match ({sorted(py_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(asp_methods)} python={sorted(py_methods)}")

    cases = list(CURATED)
    rng = random.Random(17)
    parser = build_parser()
    for _ in range(20):
        try:
            cases.append(resolve_params(parser.parse_args([]), rng))
        except StoryError:
            pass

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Finn", "Max", "Theo", "Sam", "Eli"]
PRACTICES = [
    "a kungfu stepping pattern",
    "a kungfu balance drill",
    "a kungfu tiger pose",
    "a kungfu kick-and-block game",
    "a kungfu breathing routine",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child practicing kungfu hears a dingle from behind something hidden."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--barrier", choices=BARRIERS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--practice")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))
    if args.setting and args.barrier and args.source:
        if not valid_combo(args.setting, args.barrier, args.source):
            raise StoryError(explain_combo_rejection(args.setting, args.barrier, args.source))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.barrier is None or combo[1] == args.barrier)
        and (args.source is None or combo[2] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, barrier_id, source_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    practice = args.practice or rng.choice(PRACTICES)
    return StoryParams(
        setting=setting_id,
        barrier=barrier_id,
        source=source_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper=helper,
        practice=practice,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.barrier not in BARRIERS:
        raise StoryError(f"(Unknown barrier: {params.barrier})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if not valid_combo(params.setting, params.barrier, params.source):
        raise StoryError(explain_combo_rejection(params.setting, params.barrier, params.source))
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.helper not in {"mother", "father"}:
        raise StoryError(f"(Unknown helper: {params.helper})")

    world = tell(
        setting=SETTINGS[params.setting],
        barrier=BARRIERS[params.barrier],
        source=SOURCES[params.source],
        method=METHODS[params.method],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper,
        practice=params.practice,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        methods = asp_sensible_methods()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (setting, barrier, source) combos:\n")
        for setting_id, barrier_id, source_id in combos:
            print(f"  {setting_id:12} {barrier_id:12} {source_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.source} behind {p.barrier} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
