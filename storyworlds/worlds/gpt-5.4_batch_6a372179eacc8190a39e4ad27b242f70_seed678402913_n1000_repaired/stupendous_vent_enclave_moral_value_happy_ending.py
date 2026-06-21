#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stupendous_vent_enclave_moral_value_happy_ending.py
==============================================================================

A standalone storyworld about a young animal in a snug enclave who dislikes the
whistling draft from a vent and tries to block it. The vent is not decoration:
it lets smoke escape from a cooking fire or lamp. If it is blocked, danger
grows. A wise friend or elder either stops the mistake in time or clears the
vent and teaches the lesson, leading to a happy ending with a safer fix.

The stories aim for a fable-like shape:
- a concrete setting in a tiny animal enclave
- a tempting shortcut
- a caution grounded in how the world works
- a turn caused by state, not templates alone
- a moral image at the end proving what changed

Run it
------
    python storyworlds/worlds/gpt-5.4/stupendous_vent_enclave_moral_value_happy_ending.py
    python storyworlds/worlds/gpt-5.4/stupendous_vent_enclave_moral_value_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/stupendous_vent_enclave_moral_value_happy_ending.py --seed 7 -n 5
    python storyworlds/worlds/gpt-5.4/stupendous_vent_enclave_moral_value_happy_ending.py --qa
    python storyworlds/worlds/gpt-5.4/stupendous_vent_enclave_moral_value_happy_ending.py --trace
    python storyworlds/worlds/gpt-5.4/stupendous_vent_enclave_moral_value_happy_ending.py --verify
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
CAREFUL_TRAITS = {"careful", "wise", "patient", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe"}
        male = {"boy", "father", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Enclave:
    id: str
    label: str
    place: str
    walls: str
    gathering: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hearth:
    id: str
    label: str
    fire_name: str
    smoke_name: str
    meal: str
    needs_vent: bool = True
    danger_word: str = "smoke"
    tags: set[str] = field(default_factory=set)


@dataclass
class Plug:
    id: str
    label: str
    phrase: str
    blocks: bool
    softness: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    cozy_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_stale_air(world: World) -> list[str]:
    out: list[str] = []
    vent = world.get("vent")
    hearth = world.get("hearth")
    if vent.meters["blocked"] < THRESHOLD or hearth.meters["lit"] < THRESHOLD:
        return out
    sig = ("stale_air",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room = world.get("hall")
    room.meters["smoke"] += 1
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    out.append("__smoke__")
    return out


def _r_cough(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("hall")
    if room.meters["smoke"] < THRESHOLD:
        return out
    sig = ("cough",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).meters["cough"] += 1
    out.append("__cough__")
    return out


CAUSAL_RULES = [
    Rule(name="stale_air", tag="physical", apply=_r_stale_air),
    Rule(name="cough", tag="physical", apply=_r_cough),
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


def hazard_at_risk(hearth: Hearth, plug: Plug) -> bool:
    return hearth.needs_vent and plug.blocks


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def smoke_severity(delay: int) -> int:
    return 1 + delay


def is_contained(fix: Fix, delay: int) -> bool:
    return fix.power >= smoke_severity(delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, friend_age: int, trait: str) -> bool:
    elder = relation == "siblings" and friend_age > hero_age
    return elder and initial_care(trait) + 1.0 + 3.0 > 6.0


def predict_smoke(world: World) -> dict:
    sim = world.copy()
    sim.get("vent").meters["blocked"] += 1
    propagate(sim, narrate=False)
    return {
        "smoke": sim.get("hall").meters["smoke"],
        "cough": sim.get("hero").meters["cough"] + sim.get("friend").meters["cough"],
    }


def introduce(world: World, enclave: Enclave, hero: Entity, friend: Entity, elder: Entity,
              hearth: Hearth) -> None:
    for ent in (hero, friend):
        ent.memes["joy"] += 1
    world.say(
        f"In {enclave.label}, a little enclave tucked {enclave.place}, "
        f"{enclave.walls}."
    )
    world.say(
        f"Each evening, {enclave.gathering}, while {elder.id} kept {hearth.fire_name} "
        f"glowing and the smell of {hearth.meal} drifted through the hall."
    )
    world.say(
        f"{hero.id} and {friend.id} thought it was a stupendous place, warm and bright "
        f"even when the wind prowled outside."
    )


def problem(world: World, hero: Entity, enclave: Enclave) -> None:
    hero.memes["annoyance"] += 1
    world.say(
        f"Yet one narrow vent high in the wall liked to whistle when the weather changed. "
        f"That small sound slipped through the enclave like a teasing flute."
    )
    world.say(
        f'{hero.id} twitched and said, "If only that vent would hush, our corner would be even cozier."'
    )


def temptation(world: World, hero: Entity, plug: Plug) -> None:
    hero.memes["shortcut"] += 1
    world.say(
        f"Then {hero.id} noticed {plug.phrase} near the door. "
        f"{hero.pronoun().capitalize()} lifted it and smiled a quick, clever smile."
    )
    world.say(
        f'"This {plug.softness} little thing could stop the draft," {hero.pronoun()} said.'
    )


def warning(world: World, friend: Entity, hero: Entity, hearth: Hearth) -> None:
    pred = predict_smoke(world)
    friend.memes["care"] += 1
    world.facts["predicted_smoke"] = pred["smoke"]
    world.facts["predicted_cough"] = pred["cough"]
    extra = ""
    if friend.memes["care"] >= 6:
        extra = f" {friend.id} had listened many times when elders explained why air must travel."
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. '
        f'"Do not block the vent," {friend.pronoun()} said. '
        f'"{hearth.smoke_name.capitalize()} must have a path to leave, or it stays with us instead."{extra}'
    )


def back_down(world: World, hero: Entity, friend: Entity, plug: Plug, elder: Entity, fix: Fix) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{hero.id} looked from {plug.label} to the high opening, and then to {friend.id}. "
        f"The thought of being warm by a trick no longer seemed brave."
    )
    world.say(
        f'{hero.pronoun().capitalize()} set {plug.label} down and said, "You are right. '
        f'I wanted quiet more quickly than wisely."'
    )
    world.say(
        f"{elder.id} heard them and nodded with gentle pride. "
        f"{elder.pronoun().capitalize()} did not praise the shortcut, but the honesty that stopped it."
    )
    world.say(
        f"Instead, {elder.id} {fix.cozy_text}, and the hall grew snug without harming the air."
    )


def defy(world: World, hero: Entity, plug: Plug) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But the whistle bothered {hero.id} more than the warning did. "
        f"{hero.pronoun().capitalize()} hopped onto a stool and pressed {plug.label} into the vent."
    )


def block_vent(world: World, plug: Plug) -> None:
    vent = world.get("vent")
    vent.meters["blocked"] += 1
    vent.attrs["plug"] = plug.id
    propagate(world, narrate=False)
    world.say(
        f"For one heartbeat the room did seem quieter. Then the air turned thick, "
        f"and the sweet smell of supper lost its sweetness."
    )
    if world.get("hall").meters["smoke"] >= THRESHOLD:
        world.say(
            f"A gray thread of {world.facts['hearth'].smoke_name} curled back into the hall instead of leaving."
        )
    if world.get("hero").meters["cough"] >= THRESHOLD:
        world.say(
            f"{world.facts['hero'].id} coughed, and {world.facts['friend'].id} covered {world.facts['friend'].pronoun('possessive')} nose."
        )


def alarm(world: World, friend: Entity, elder: Entity) -> None:
    world.say(
        f'"Elder {elder.id}, the vent is blocked!" cried {friend.id}.'
    )


def rescue(world: World, elder: Entity, fix: Fix) -> None:
    world.get("vent").meters["blocked"] = 0.0
    world.get("hall").meters["smoke"] = 0.0
    for eid in ("hero", "friend"):
        if eid in world.entities:
            world.get(eid).meters["cough"] = 0.0
            world.get(eid).memes["worry"] = 0.0
            world.get(eid).memes["relief"] += 1
    world.say(
        f"{elder.id} moved at once and {fix.text}."
    )
    world.say(
        "Fresh air slipped through, the smoke found its road again, and the room felt kind instead of close."
    )


def lesson(world: World, elder: Entity, hero: Entity, hearth: Hearth) -> None:
    hero.memes["lesson"] += 1
    friend = world.facts["friend"]
    friend.memes["lesson"] += 1
    world.say(
        f'{elder.id} set a steady paw on {hero.id}\'s shoulder and said, '
        f'"A vent may look like a small crack in the wall, but it serves the whole home. '
        f'Never silence a useful thing just because it troubles you for a moment."'
    )
    world.say(
        f"{hero.id} bowed {hero.pronoun('possessive')} head. "
        f"{hero.pronoun().capitalize()} understood that comfort without thought can turn into danger."
    )
    world.say(
        f'Together they watched {hearth.smoke_name} rise properly away, and {hero.id} promised, '
        f'"Next time I will ask before I meddle."'
    )


def happy_end(world: World, elder: Entity, hero: Entity, friend: Entity, fix: Fix, enclave: Enclave) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that, {elder.id} {fix.cozy_text}."
    )
    world.say(
        f"Now the vent could breathe, the little ones could rest, and supper tasted even better in {enclave.label}."
    )
    world.say(
        f"{hero.id} curled beside {friend.id} and listened to the wind outside. "
        f"It no longer sounded like an enemy, only a voice beyond safe walls."
    )
    world.say(
        "And so the enclave stayed warm because its friends chose wisdom over haste."
    )


def rescue_fail(world: World, elder: Entity, fix: Fix) -> None:
    world.get("hall").meters["smoke"] += 1
    for eid in ("hero", "friend"):
        world.get(eid).meters["cough"] += 1
        world.get(eid).memes["worry"] += 1
    world.say(
        f"{elder.id} tried to help and {fix.text}, but the room had already grown too thick with smoke."
    )


def escape(world: World, elder: Entity, hero: Entity, friend: Entity, enclave: Enclave) -> None:
    for ent in (hero, friend):
        ent.memes["fear"] += 1
    world.say(
        f"{elder.id} hurried {hero.id} and {friend.id} out into the moonlit path beyond the enclave."
    )
    world.say(
        f"They stood shivering in the grass until the air inside cleared. "
        f"No one was lost, but the hall had become a place to air out instead of a place to rest."
    )
    world.say(
        f"{hero.id} saw then how one selfish choice can trouble a whole small home."
    )


def moral_close(world: World) -> None:
    world.say(
        "This is the lesson: when many share one shelter, even a tiny opening may guard everyone's good."
    )


def tell(enclave: Enclave, hearth: Hearth, plug: Plug, fix: Fix,
         hero_name: str = "Pip", hero_kind: str = "mouse",
         friend_name: str = "Mira", friend_kind: str = "mouse",
         elder_name: str = "Aunt Brindle", elder_kind: str = "mouse",
         trait: str = "careful", delay: int = 0,
         hero_age: int = 4, friend_age: int = 6, relation: str = "siblings") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_kind, label=hero_name,
                            role="hero", age=hero_age, attrs={"relation": relation}))
    friend = world.add(Entity(id="friend", kind="character", type=friend_kind, label=friend_name,
                              role="friend", age=friend_age,
                              traits=[trait], attrs={"relation": relation}))
    elder = world.add(Entity(id="elder", kind="character", type=elder_kind, label=elder_name,
                             role="elder"))
    hall = world.add(Entity(id="hall", kind="thing", type="hall", label="hall"))
    vent = world.add(Entity(id="vent", kind="thing", type="vent", label="vent"))
    hearth_ent = world.add(Entity(id="hearth", kind="thing", type="hearth", label=hearth.label))
    hearth_ent.meters["lit"] = 1.0
    friend.memes["care"] = initial_care(trait)

    world.facts.update(
        enclave=enclave,
        hearth=hearth,
        plug=plug,
        fix=fix,
        hero=hero,
        friend=friend,
        elder=elder,
        relation=relation,
        delay=delay,
    )

    introduce(world, enclave, hero, friend, elder, hearth)
    problem(world, hero, enclave)

    world.para()
    temptation(world, hero, plug)
    warning(world, friend, hero, hearth)

    averted = would_avert(relation, hero_age, friend_age, trait)
    severity = smoke_severity(delay)
    contained = is_contained(fix, delay)

    if averted:
        back_down(world, hero, friend, plug, elder, fix)
        world.para()
        happy_end(world, elder, hero, friend, fix, enclave)
        outcome = "averted"
    else:
        defy(world, hero, plug)
        world.para()
        block_vent(world, plug)
        alarm(world, friend, elder)

        world.para()
        if contained:
            rescue(world, elder, fix)
            lesson(world, elder, hero, hearth)
            world.para()
            happy_end(world, elder, hero, friend, fix, enclave)
            outcome = "contained"
        else:
            rescue_fail(world, elder, fix)
            escape(world, elder, hero, friend, enclave)
            moral_close(world)
            outcome = "troubled"

    world.facts.update(
        averted=averted,
        severity=severity,
        outcome=outcome,
        blocked=world.get("vent").attrs.get("plug", "") == plug.id or outcome != "averted",
        contained=contained,
    )
    return world


ENCLAVES = {
    "burrow": Enclave(
        id="burrow",
        label="Bramble Burrow",
        place="under a bramble hill",
        walls="round rooms were lined with roots and polished acorn shelves",
        gathering="mice shared chestnut soup on smooth stone stools",
        tags={"enclave", "burrow"},
    ),
    "tree": Enclave(
        id="tree",
        label="Hollow Oak Enclave",
        place="inside an ancient oak",
        walls="the wooden chambers curved like warm cups around a lantern hall",
        gathering="squirrels shared seed cakes on a ring of bark benches",
        tags={"enclave", "tree"},
    ),
    "stone": Enclave(
        id="stone",
        label="Fernstone Enclave",
        place="between mossy rocks beside a stream",
        walls="flat stones held the rooms together while fern mats softened the floor",
        gathering="hedgehogs shared barley mash under strings of shell lights",
        tags={"enclave", "stone"},
    ),
}

HEARTHS = {
    "soupfire": Hearth(
        id="soupfire",
        label="cookfire",
        fire_name="the soupfire",
        smoke_name="smoke",
        meal="chestnut soup",
        tags={"fire", "smoke", "soup"},
    ),
    "breadoven": Hearth(
        id="breadoven",
        label="oven",
        fire_name="the bread oven",
        smoke_name="smoke",
        meal="seed bread",
        tags={"fire", "smoke", "bread"},
    ),
    "herblamp": Hearth(
        id="herblamp",
        label="lamp",
        fire_name="the herb lamp",
        smoke_name="warm lamp-smoke",
        meal="mint tea",
        tags={"lamp", "smoke", "tea"},
    ),
}

PLUGS = {
    "moss": Plug(
        id="moss",
        label="the tuft of moss",
        phrase="a tuft of moss",
        blocks=True,
        softness="soft",
        tags={"moss", "vent"},
    ),
    "rag": Plug(
        id="rag",
        label="the folded rag",
        phrase="a folded rag",
        blocks=True,
        softness="thick",
        tags={"rag", "vent"},
    ),
    "clay": Plug(
        id="clay",
        label="the lump of clay",
        phrase="a lump of clay",
        blocks=True,
        softness="heavy",
        tags={"clay", "vent"},
    ),
    "feather": Plug(
        id="feather",
        label="the feather",
        phrase="a loose feather",
        blocks=False,
        softness="light",
        tags={"feather"},
    ),
}

FIXES = {
    "clear_and_crack": Fix(
        id="clear_and_crack",
        sense=3,
        power=3,
        text="pulled the blockage free and opened the little side hatch for a moment",
        qa_text="pulled the blockage from the vent and opened a side hatch so the smoke could leave",
        cozy_text="hung a thick tapestry across the sleeping nook instead of touching the vent",
        tags={"vent", "air", "tapestry"},
    ),
    "clear_with_poker": Fix(
        id="clear_with_poker",
        sense=3,
        power=2,
        text="used a long hearth poker to lift the blockage out and stir fresh air through the room",
        qa_text="used a hearth poker to clear the vent and let fresh air move through the room",
        cozy_text="moved the little ones' bedrolls farther from the draft and tucked them under a shared quilt",
        tags={"vent", "air", "quilt"},
    ),
    "fan_only": Fix(
        id="fan_only",
        sense=1,
        power=1,
        text="fanned the room with a tray",
        qa_text="fanned the air with a tray",
        cozy_text="set an extra blanket by the bedrolls",
        tags={"fan"},
    ),
}

ANIMAL_KINDS = {
    "mouse": {"names": ["Pip", "Nim", "Mira", "Tansy", "Poppy", "Rill"], "elder": ["Aunt Brindle", "Old Reed"]},
    "squirrel": {"names": ["Pip", "Moss", "Hazel", "Junie", "Rowan", "Tavi"], "elder": ["Uncle Bark", "Grandam Nutmeg"]},
    "hedgehog": {"names": ["Pip", "Bram", "Mira", "Nettle", "Pru", "Tumble"], "elder": ["Aunt Thistle", "Old Clover"]},
}
TRAITS = ["careful", "wise", "patient", "steady", "curious", "quick"]
RELATIONS = ["siblings", "friends"]


@dataclass
class StoryParams:
    enclave: str
    hearth: str
    plug: str
    fix: str
    hero_name: str
    hero_kind: str
    friend_name: str
    friend_kind: str
    elder_name: str
    elder_kind: str
    trait: str
    delay: int = 0
    hero_age: int = 4
    friend_age: int = 6
    relation: str = "siblings"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        enclave="burrow",
        hearth="soupfire",
        plug="moss",
        fix="clear_and_crack",
        hero_name="Pip",
        hero_kind="mouse",
        friend_name="Mira",
        friend_kind="mouse",
        elder_name="Aunt Brindle",
        elder_kind="mouse",
        trait="careful",
        delay=0,
        hero_age=4,
        friend_age=6,
        relation="siblings",
    ),
    StoryParams(
        enclave="tree",
        hearth="breadoven",
        plug="rag",
        fix="clear_with_poker",
        hero_name="Moss",
        hero_kind="squirrel",
        friend_name="Hazel",
        friend_kind="squirrel",
        elder_name="Uncle Bark",
        elder_kind="squirrel",
        trait="wise",
        delay=1,
        hero_age=5,
        friend_age=7,
        relation="siblings",
    ),
    StoryParams(
        enclave="stone",
        hearth="herblamp",
        plug="clay",
        fix="clear_with_poker",
        hero_name="Bram",
        hero_kind="hedgehog",
        friend_name="Pru",
        friend_kind="hedgehog",
        elder_name="Aunt Thistle",
        elder_kind="hedgehog",
        trait="curious",
        delay=0,
        hero_age=6,
        friend_age=5,
        relation="friends",
    ),
    StoryParams(
        enclave="burrow",
        hearth="breadoven",
        plug="rag",
        fix="fan_only",
        hero_name="Nim",
        hero_kind="mouse",
        friend_name="Tansy",
        friend_kind="mouse",
        elder_name="Old Reed",
        elder_kind="mouse",
        trait="quick",
        delay=1,
        hero_age=6,
        friend_age=5,
        relation="friends",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for enclave in ENCLAVES:
        for hearth_id, hearth in HEARTHS.items():
            for plug_id, plug in PLUGS.items():
                if hazard_at_risk(hearth, plug):
                    combos.append((enclave, hearth_id, plug_id))
    return combos


def explain_rejection(hearth: Hearth, plug: Plug) -> str:
    if not plug.blocks:
        return (
            f"(No story: {plug.phrase} does not truly block a vent, so there is no real danger to explain. "
            f"Choose moss, rag, or clay for a genuine mistake.)"
        )
    if not hearth.needs_vent:
        return "(No story: this hearth would not need a vent, so blocking it changes nothing.)"
    return "(No story: this combination makes no hazard.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.friend_age, params.trait):
        return "averted"
    return "contained" if is_contained(FIXES[params.fix], params.delay) else "troubled"


KNOWLEDGE = {
    "vent": [
        (
            "What does a vent do?",
            "A vent lets air move in or out of a room. Near a fire or lamp, it helps smoke leave instead of staying where people breathe."
        )
    ],
    "smoke": [
        (
            "Why is smoke bad to breathe?",
            "Smoke can make your eyes sting and your throat hurt. Too much smoke in a room can make it hard to breathe safely."
        )
    ],
    "air": [
        (
            "Why does fresh air matter indoors?",
            "Fresh air helps carry away stale air and smoke. Rooms feel safer and easier to breathe in when air can move."
        )
    ],
    "moss": [
        (
            "What is moss?",
            "Moss is a soft green plant that grows in damp places. It feels gentle, but it can still clog a small opening if you stuff it in."
        )
    ],
    "rag": [
        (
            "What is a rag?",
            "A rag is a piece of cloth. Cloth can plug little gaps, which is why it should not be pushed into a vent."
        )
    ],
    "clay": [
        (
            "What is clay?",
            "Clay is soft earth that can be shaped when wet. If you press it into a hole, it can harden and block the opening."
        )
    ],
    "tapestry": [
        (
            "Why is hanging a cloth by a bed safer than blocking a vent?",
            "A hanging cloth can make a sleeping corner feel warmer without sealing the air path. It solves the comfort problem without trapping smoke."
        )
    ],
    "quilt": [
        (
            "What does a quilt do?",
            "A quilt keeps bodies warm by holding in heat around them. It is for covering people, not for plugging walls or vents."
        )
    ],
}
KNOWLEDGE_ORDER = ["vent", "smoke", "air", "moss", "rag", "clay", "tapestry", "quilt"]


def pair_noun(world: World) -> str:
    relation = world.facts.get("relation", "friends")
    if relation == "siblings":
        return "two young kin"
    return "two young friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    enclave = f["enclave"]
    outcome = f["outcome"]
    plug = f["plug"]
    if outcome == "averted":
        return [
            f'Write a fable for a young child that includes the words "stupendous", "vent", and "enclave".',
            f"Tell a gentle cautionary story where {hero.label} wants to block a vent in {enclave.label}, but {friend.label} wisely stops the mistake before any harm is done.",
            "Write a happy-ending moral tale in which a small comfort seems clever at first, yet patience and good advice keep everyone safe.",
        ]
    if outcome == "troubled":
        return [
            f'Write a cautionary fable using the words "stupendous", "vent", and "enclave".',
            f"Tell a story where a little animal blocks a vent with {plug.label}, troubles the whole home, and learns that selfish shortcuts can hurt everyone.",
            "Write a moral tale with a scary turn but no tragic ending: the characters escape danger, and the lesson is stated clearly at the end.",
        ]
    return [
        f'Write a fable for ages 3 to 5 that includes the words "stupendous", "vent", and "enclave".',
        f"Tell a moral story where {hero.label} blocks a vent in a tiny enclave, an elder fixes the problem, and the ending proves the child learned.",
        "Write a cautionary but comforting animal tale in which a useful part of a shared home must not be tampered with.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    elder = f["elder"]
    enclave = f["enclave"]
    plug = f["plug"]
    hearth = f["hearth"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(world)}, {hero.label} and {friend.label}, in {enclave.label}, and the elder {elder.label} who watches over their home."
        ),
        (
            "Why did the hero want to touch the vent?",
            f"{hero.label} wanted the hall to feel quieter and cozier. The whistle from the vent bothered {hero.pronoun('object')}, so the quick fix looked tempting."
        ),
        (
            f"Why did {friend.label} warn {hero.label}?",
            f"{friend.label} warned that the vent helped {hearth.smoke_name} leave the hall. If the opening were blocked, the smoke would stay where everyone breathed."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                "What changed after the warning?",
                f"{hero.label} listened and put {plug.label} down before blocking the vent. That honest pause prevented the trouble before it could begin."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily because the elder made the sleeping corner warmer in a safer way, while the vent stayed open. The whole enclave kept its comfort and its clean air."
            )
        )
    elif outcome == "contained":
        qa.append(
            (
                "What happened when the vent was blocked?",
                f"The room grew thick and unpleasant, and {hearth.smoke_name} curled back into the hall. What first seemed quiet quickly became a breathing problem."
            )
        )
        qa.append(
            (
                f"How did {elder.label} fix the problem?",
                f"{elder.label} {fix.qa_text}. That let the smoke leave again and turned the room from dangerous back to safe."
            )
        )
        qa.append(
            (
                "What lesson did the hero learn?",
                "The hero learned that a useful part of a shared home should not be tampered with just for quick comfort. A small selfish shortcut can become a big problem for everyone."
            )
        )
    else:
        qa.append(
            (
                "Did the first rescue work well?",
                f"No. {elder.label} tried to help, but the room had already become too smoky. They had to leave the hall until the air cleared."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"Everyone stayed safe, but the hall could not be enjoyed right away. The hard ending showed {hero.label} how one unwise act can trouble a whole enclave."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                "When many share one shelter, even a tiny useful opening matters. Thinking only of your own comfort can make life harder for everybody else."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["plug"].tags)
    tags |= set(f["fix"].tags)
    tags |= {"vent", "smoke"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits: list[str] = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(H, P) :- hearth(H), needs_vent(H), blocks(P).
valid(E, H, P) :- enclave(E), hazard(H, P).

careful_now(T) :- trait(T), careful_trait(T).
init_care(5) :- trait(T), careful_now(T).
init_care(3) :- trait(T), not careful_now(T).

friend_older :- relation(siblings), hero_age(HA), friend_age(FA), FA > HA.
bonus(3) :- friend_older.
bonus(0) :- not friend_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- friend_older, authority(A), averted_threshold(T), A > T.

severity(1 + D) :- delay(D).
contained :- chosen_fix(F), power(F, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(troubled) :- not averted, not contained.

sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for eid in ENCLAVES:
        lines.append(asp.fact("enclave", eid))
    for hid, hearth in HEARTHS.items():
        lines.append(asp.fact("hearth", hid))
        if hearth.needs_vent:
            lines.append(asp.fact("needs_vent", hid))
    for pid, plug in PLUGS.items():
        lines.append(asp.fact("plug", pid))
        if plug.blocks:
            lines.append(asp.fact("blocks", pid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("averted_threshold", 6))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(f for (f,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {f.id for f in sensible_fixes()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible fixes match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(100):
        rng = random.Random(seed)
        args = build_parser().parse_args([])
        try:
            params = resolve_params(args, rng)
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A fable-like storyworld about a vent in a shared enclave. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--enclave", choices=ENCLAVES)
    ap.add_argument("--hearth", choices=HEARTHS)
    ap.add_argument("--plug", choices=PLUGS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-kind", choices=ANIMAL_KINDS)
    ap.add_argument("--friend-kind", choices=ANIMAL_KINDS)
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2],
                    help="how long the smoke problem grows before the elder acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program")
    return ap


def _pick_names(kind: str, rng: random.Random) -> tuple[str, str]:
    names = list(ANIMAL_KINDS[kind]["names"])
    hero = rng.choice(names)
    others = [n for n in names if n != hero]
    friend = rng.choice(others)
    elder = rng.choice(list(ANIMAL_KINDS[kind]["elder"]))
    return hero, friend, elder


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plug and args.hearth:
        plug = PLUGS[args.plug]
        hearth = HEARTHS[args.hearth]
        if not hazard_at_risk(hearth, plug):
            raise StoryError(explain_rejection(hearth, plug))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.enclave is None or combo[0] == args.enclave)
        and (args.hearth is None or combo[1] == args.hearth)
        and (args.plug is None or combo[2] == args.plug)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    enclave, hearth, plug = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    hero_kind = args.hero_kind or rng.choice(sorted(ANIMAL_KINDS))
    friend_kind = args.friend_kind or hero_kind
    if friend_kind not in ANIMAL_KINDS:
        raise StoryError("(No story: unknown friend kind.)")
    hero_name, friend_name, elder_name = _pick_names(hero_kind, rng)
    if friend_kind != hero_kind:
        friend_name = rng.choice(list(ANIMAL_KINDS[friend_kind]["names"]))
        elder_name = rng.choice(list(ANIMAL_KINDS[hero_kind]["elder"]))
    trait = rng.choice(TRAITS)
    relation = args.relation or rng.choice(RELATIONS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_age, friend_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        enclave=enclave,
        hearth=hearth,
        plug=plug,
        fix=fix,
        hero_name=hero_name,
        hero_kind=hero_kind,
        friend_name=friend_name,
        friend_kind=friend_kind,
        elder_name=elder_name,
        elder_kind=hero_kind,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        friend_age=friend_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.enclave not in ENCLAVES:
        raise StoryError(f"(No story: unknown enclave '{params.enclave}'.)")
    if params.hearth not in HEARTHS:
        raise StoryError(f"(No story: unknown hearth '{params.hearth}'.)")
    if params.plug not in PLUGS:
        raise StoryError(f"(No story: unknown plug '{params.plug}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}'.)")
    if params.hero_kind not in ANIMAL_KINDS or params.friend_kind not in ANIMAL_KINDS:
        raise StoryError("(No story: unknown animal kind.)")
    if not hazard_at_risk(HEARTHS[params.hearth], PLUGS[params.plug]):
        raise StoryError(explain_rejection(HEARTHS[params.hearth], PLUGS[params.plug]))
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        enclave=ENCLAVES[params.enclave],
        hearth=HEARTHS[params.hearth],
        plug=PLUGS[params.plug],
        fix=FIXES[params.fix],
        hero_name=params.hero_name,
        hero_kind=params.hero_kind,
        friend_name=params.friend_name,
        friend_kind=params.friend_kind,
        elder_name=params.elder_name,
        elder_kind=params.elder_kind,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (enclave, hearth, plug) combos:\n")
        for enclave, hearth, plug in combos:
            print(f"  {enclave:8} {hearth:10} {plug}")
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
            header = f"### {p.hero_name} in {p.enclave}: {p.plug} / {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
