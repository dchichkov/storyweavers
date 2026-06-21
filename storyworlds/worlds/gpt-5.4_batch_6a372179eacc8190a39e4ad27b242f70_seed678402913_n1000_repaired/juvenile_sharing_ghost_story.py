#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/juvenile_sharing_ghost_story.py
==========================================================

A standalone story world for a gentle ghost story about sharing.

This tiny domain rebuilds a small seed premise into a stateful simulation:
two children hear a strange sound in a dim old room, imagine a ghost, and
discover that the ghost is only lonely and hungry for company. The key
constraint is not "any snack + any ending", but whether the food can honestly
be shared among the children and the ghost. The world tracks physical meters
(portions, warmth, light) and emotional memes (fear, hunger, trust, relief,
belonging). The prose follows those state changes.

The required seed word "juvenile" appears in-story as the children's phrase for
the little ghost they meet: a "juvenile ghost" -- not a grown, booming spirit,
but a shy little one.

Run it
------
    python storyworlds/worlds/gpt-5.4/juvenile_sharing_ghost_story.py
    python storyworlds/worlds/gpt-5.4/juvenile_sharing_ghost_story.py --room attic --snack moon_cake
    python storyworlds/worlds/gpt-5.4/juvenile_sharing_ghost_story.py --snack single_plum
    python storyworlds/worlds/gpt-5.4/juvenile_sharing_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/juvenile_sharing_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/juvenile_sharing_ghost_story.py --verify
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

# Make the shared result containers importable when this script is run directly:
# add storyworlds/ to sys.path regardless of the nested gpt-5.4/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"         # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Room:
    id: str
    label: str
    phrase: str
    hiding_spot: str
    sound: str
    moonline: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    portions: int
    divisible: bool
    cut_phrase: str
    shared_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"holder", "friend"}]

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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear_of_dark(world: World) -> list[str]:
    room = world.entities.get("room")
    if room is None or room.meters["dim"] < THRESHOLD:
        return []
    out: list[str] = []
    for kid in world.kids():
        sig = ("dark_fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__dim__")
    return out


def _r_hungry_ghost_revealed(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    snack = world.entities.get("snack")
    if ghost is None or snack is None:
        return []
    if ghost.memes["noticed_snack"] < THRESHOLD:
        return []
    sig = ("ghost_hungry", ghost.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["hunger"] += 1
    ghost.memes["hope"] += 1
    return ["__ghost_hungry__"]


def _r_light_calms(world: World) -> list[str]:
    lamp = world.entities.get("light")
    if lamp is None or lamp.meters["on"] < THRESHOLD:
        return []
    out: list[str] = []
    for ent in world.kids() + [world.get("ghost")]:
        sig = ("lit_calm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.memes["fear"] > 0:
            ent.memes["fear"] -= 1
        ent.memes["calm"] += 1
        out.append("__light__")
    room = world.get("room")
    room.meters["dim"] = 0.0
    room.meters["warm_glow"] += 1
    return out


def _r_share_relief(world: World) -> list[str]:
    ghost = world.get("ghost")
    snack = world.get("snack")
    if ghost.memes["included"] < THRESHOLD:
        return []
    sig = ("share_relief", ghost.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if ghost.memes["hunger"] > 0:
        ghost.memes["hunger"] -= 1
    ghost.memes["belonging"] += 1
    for kid in world.kids():
        if kid.memes["fear"] > 0:
            kid.memes["fear"] -= 1
        kid.memes["kindness"] += 1
        kid.memes["relief"] += 1
    snack.meters["shared"] += 1
    return ["__shared__"]


CAUSAL_RULES = [
    Rule(name="fear_of_dark", tag="emotion", apply=_r_fear_of_dark),
    Rule(name="hungry_ghost_revealed", tag="emotion", apply=_r_hungry_ghost_revealed),
    Rule(name="light_calms", tag="physical", apply=_r_light_calms),
    Rule(name="share_relief", tag="social", apply=_r_share_relief),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def share_possible(snack: Snack, people: int = 3) -> bool:
    if snack.portions >= people:
        return True
    if snack.divisible and snack.portions >= 2:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id in ROOMS:
        for snack_id, snack in SNACKS.items():
            for light_id in LIGHTS:
                if share_possible(snack, 3):
                    combos.append((room_id, snack_id, light_id))
    return combos


def explain_rejection(snack: Snack) -> str:
    return (
        f"(No story: {snack.phrase} cannot honestly be shared among two children "
        f"and a lonely little ghost. This world only tells sharing stories when "
        f"there is enough food, or when the snack can sensibly be divided.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_approach(world: World) -> dict:
    sim = world.copy()
    ghost = sim.get("ghost")
    light = sim.get("light")
    snack = sim.get("snack")
    ghost.memes["noticed_snack"] += 1
    light.meters["on"] += 1
    propagate(sim, narrate=False)
    return {
        "ghost_hungry": ghost.memes["hunger"] >= THRESHOLD,
        "fear_after_light": sum(k.memes["fear"] for k in sim.kids()),
        "room_warm": sim.get("room").meters["warm_glow"] >= THRESHOLD,
        "share_possible": share_possible(SNACKS[sim.facts["snack_cfg"].id], 3),
        "snack_seen": snack.label,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup_evening(world: World, room_cfg: Room, holder: Entity, friend: Entity, snack_cfg: Snack) -> None:
    room = world.get("room")
    room.meters["dim"] += 1
    world.get("snack").meters["whole"] += 1
    for kid in (holder, friend):
        kid.memes["cozy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"On a windy evening, {holder.id} and {friend.id} padded into {room_cfg.phrase}. "
        f"A thin line of moonlight lay across the floor, and the corners looked soft and far away."
    )
    world.say(
        f"{holder.id} carried {snack_cfg.phrase} on a plate, and the sweet smell followed them into the room."
    )
    world.say(
        f"From {room_cfg.hiding_spot} came {room_cfg.sound}, so small and strange that both children stopped walking."
    )


def name_the_fear(world: World, holder: Entity, friend: Entity) -> None:
    ghost = world.get("ghost")
    world.say(
        f'"Did you hear that?" whispered {friend.id}. {holder.id} squeezed the plate with both hands.'
    )
    if sum(k.memes["fear"] for k in world.kids()) >= 2:
        world.say(
            f'"Maybe it is a ghost," {holder.id} murmured. "{ghost.attrs["nickname"]} kind of ghost."'
        )


def peek_and_predict(world: World, holder: Entity, friend: Entity, light_cfg: Light) -> None:
    pred = predict_approach(world)
    world.facts["predicted_ghost_hungry"] = pred["ghost_hungry"]
    world.facts["predicted_fear_after_light"] = pred["fear_after_light"]
    world.say(
        f'{friend.id} reached for {light_cfg.phrase}. "If we use {light_cfg.label}, we can see before we run," {friend.pronoun()} said.'
    )


def reveal_ghost(world: World, holder: Entity, friend: Entity, light_cfg: Light) -> None:
    ghost = world.get("ghost")
    light = world.get("light")
    ghost.memes["noticed_snack"] += 1
    light.meters["on"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{holder.id} clicked {light_cfg.effect}, and the shadows stepped back."
    )
    world.say(
        f"There, in {world.facts['room_cfg'].hiding_spot}, sat not a tall, roaring spirit but a juvenile ghost -- "
        f"a little pale child-shape with round eyes and knees tucked up to its chest."
    )
    world.say(
        f'"Please do not run," the ghost whispered. "I only smelled your {world.facts["snack_cfg"].label} and wished I had someone to sit with."'
    )


def choose_kindness(world: World, holder: Entity, friend: Entity, snack_cfg: Snack) -> None:
    ghost = world.get("ghost")
    world.say(
        f"{friend.id} looked at the tiny ghost, then at the plate. The room still felt spooky, but not mean."
    )
    if snack_cfg.portions >= 3:
        world.say(
            f'"We can share," {friend.id} said. "There is enough for all of us."'
        )
    else:
        world.say(
            f'"We can still share," {holder.id} said. "We just have to divide it carefully."'
        )
    ghost.memes["trust"] += 1


def share_snack(world: World, holder: Entity, friend: Entity, snack_cfg: Snack) -> None:
    snack = world.get("snack")
    ghost = world.get("ghost")
    if snack_cfg.portions >= 3:
        snack.meters["pieces"] = float(snack_cfg.portions)
        used_method = "ready_portions"
        world.say(
            f"{holder.id} set the plate down between them. {snack_cfg.shared_phrase.capitalize()}, and one was left for the little ghost."
        )
    else:
        snack.meters["pieces"] = 3.0
        used_method = "cut"
        world.say(
            f"{holder.id} {snack_cfg.cut_phrase}, making three careful pieces on the plate."
        )
    ghost.memes["included"] += 1
    propagate(world, narrate=False)
    world.facts["share_method"] = used_method
    world.say(
        f"The ghost lifted its piece in both misty hands. It did not really bite, but the color came back to its face as if kindness itself were a meal."
    )


def ending(world: World, holder: Entity, friend: Entity, room_cfg: Room, light_cfg: Light, snack_cfg: Snack) -> None:
    ghost = world.get("ghost")
    ghost.memes["joy"] += 1
    ghost.memes["fear"] = 0.0
    for kid in (holder, friend):
        kid.memes["joy"] += 1
    world.say(
        f'Soon {holder.id}, {friend.id}, and the little ghost were sitting in a neat row under {room_cfg.moonline}, passing the plate back and forth.'
    )
    world.say(
        f'"I was trying to sound scary so nobody would notice I was lonely," the ghost admitted.'
    )
    world.say(
        f'"Next time, just ask," said {friend.id}. "{light_cfg.label.capitalize()} and sharing work better than hiding."'
    )
    world.say(
        f"When they left the room, it no longer felt haunted. It felt like a place where one small light and one shared {snack_cfg.label} had made space for one more friend."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    room_cfg: Room,
    snack_cfg: Snack,
    light_cfg: Light,
    holder_name: str = "Mina",
    holder_gender: str = "girl",
    friend_name: str = "Owen",
    friend_gender: str = "boy",
    trait: str = "gentle",
) -> World:
    world = World()
    holder = world.add(Entity(id=holder_name, kind="character", type=holder_gender, role="holder", traits=[trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", traits=["careful"]))
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label="little ghost",
            attrs={"nickname": "juvenile"},
            tags={"ghost", "sharing"},
        )
    )
    room = world.add(Entity(id="room", type="room", label=room_cfg.label, phrase=room_cfg.phrase, tags=set(room_cfg.tags)))
    snack = world.add(Entity(id="snack", type="snack", label=snack_cfg.label, phrase=snack_cfg.phrase, tags=set(snack_cfg.tags)))
    light = world.add(Entity(id="light", type="light", label=light_cfg.label, phrase=light_cfg.phrase, tags=set(light_cfg.tags)))

    setup_evening(world, room_cfg, holder, friend, snack_cfg)
    name_the_fear(world, holder, friend)

    world.para()
    peek_and_predict(world, holder, friend, light_cfg)
    reveal_ghost(world, holder, friend, light_cfg)

    world.para()
    choose_kindness(world, holder, friend, snack_cfg)
    share_snack(world, holder, friend, snack_cfg)

    world.para()
    ending(world, holder, friend, room_cfg, light_cfg, snack_cfg)

    world.facts.update(
        holder=holder,
        friend=friend,
        ghost=ghost,
        room_cfg=room_cfg,
        snack_cfg=snack_cfg,
        light_cfg=light_cfg,
        shared=world.get("snack").meters["shared"] >= THRESHOLD,
        room_bright=world.get("room").meters["warm_glow"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "attic": Room(
        id="attic",
        label="attic",
        phrase="the old attic at the top of the stairs",
        hiding_spot="a cedar trunk under the sloping roof",
        sound="a tiny rustly sigh",
        moonline="the silver moonbeam",
        tags={"attic", "ghost"},
    ),
    "nursery": Room(
        id="nursery",
        label="nursery",
        phrase="the quiet nursery at the end of the hall",
        hiding_spot="the rocking chair by the curtain",
        sound="a shaky little hum",
        moonline="the pale patch of moonlight",
        tags={"nursery", "ghost"},
    ),
    "parlor": Room(
        id="parlor",
        label="parlor",
        phrase="the old parlor with the covered piano",
        hiding_spot="the stool beside the piano",
        sound="the softest plink-plink note",
        moonline="the long moon stripe",
        tags={"parlor", "ghost"},
    ),
}

SNACKS = {
    "moon_cake": Snack(
        id="moon_cake",
        label="moon cake",
        phrase="a round moon cake",
        portions=2,
        divisible=True,
        cut_phrase="carefully cut the moon cake into thirds",
        shared_phrase="Two neat slices were already marked",
        tags={"cake", "sharing", "food"},
    ),
    "apple_tarts": Snack(
        id="apple_tarts",
        label="apple tarts",
        phrase="three tiny apple tarts",
        portions=3,
        divisible=False,
        cut_phrase="set the little tarts in a row",
        shared_phrase="Three little tarts waited there",
        tags={"tarts", "sharing", "food"},
    ),
    "ginger_cookies": Snack(
        id="ginger_cookies",
        label="ginger cookies",
        phrase="a plate of three ginger cookies",
        portions=3,
        divisible=False,
        cut_phrase="lined the cookies up side by side",
        shared_phrase="Three warm cookies sat on the plate",
        tags={"cookies", "sharing", "food"},
    ),
    "single_plum": Snack(
        id="single_plum",
        label="plum",
        phrase="one small plum",
        portions=1,
        divisible=False,
        cut_phrase="cut the plum into three pieces",
        shared_phrase="The plum sat alone on the plate",
        tags={"fruit", "food"},
    ),
}

LIGHTS = {
    "candle_lantern": Light(
        id="candle_lantern",
        label="the lantern",
        phrase="the brass lantern",
        effect="the brass lantern alive with a warm bead of light",
        tags={"lantern", "light"},
    ),
    "flashlight": Light(
        id="flashlight",
        label="the flashlight",
        phrase="the little flashlight",
        effect="the little flashlight on",
        tags={"flashlight", "light"},
    ),
    "night_lamp": Light(
        id="night_lamp",
        label="the night-lamp",
        phrase="the blue night-lamp",
        effect="the blue night-lamp glowing",
        tags={"lamp", "light"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tess", "Ruby", "Ella", "June"]
BOY_NAMES = ["Owen", "Theo", "Sam", "Ben", "Finn", "Max", "Eli", "Leo"]
TRAITS = ["gentle", "brave", "kind", "curious", "quiet"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    room: str
    snack: str
    light: str
    holder_name: str
    holder_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with a spooky feeling and something mysterious in it. In a gentle ghost story, the scary part often turns out to be sad or lonely instead of truly mean."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else have part of what you have. It can make other people feel included and cared for."
        )
    ],
    "light": [
        (
            "Why does a light help when a room feels scary?",
            "A light helps you see what is really there. When you can see clearly, your mind does not have to guess in the dark."
        )
    ],
    "lonely": [
        (
            "What does lonely mean?",
            "Lonely means wishing you had company or a friend nearby. Someone can feel lonely even in a quiet, beautiful place."
        )
    ],
    "food": [
        (
            "Why is it kind to share food?",
            "Sharing food can help when someone is hungry or left out. It tells them they belong with you."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "sharing", "light", "lonely", "food"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    room_cfg = f["room_cfg"]
    snack_cfg = f["snack_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the word "juvenile" and centers on sharing.',
        f"Tell a soft spooky story where two children hear a sound in {room_cfg.phrase} and discover that a juvenile ghost only wants company and a share of {snack_cfg.phrase}.",
        f"Write a child-facing story with shadows, a small light, and a lonely ghost, ending with the children sharing {snack_cfg.label} instead of running away.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    friend = f["friend"]
    room_cfg = f["room_cfg"]
    snack_cfg = f["snack_cfg"]
    light_cfg = f["light_cfg"]
    share_method = world.facts.get("share_method", "")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {holder.id} and {friend.id}, and a little ghost hiding in {room_cfg.label}. The ghost seems spooky at first, but it turns out to be lonely."
        ),
        (
            f"Why did {holder.id} and {friend.id} think the room was haunted?",
            f"They heard {room_cfg.sound} coming from {room_cfg.hiding_spot} in a dim room. Because they could not see clearly yet, the strange sound made their fear grow."
        ),
        (
            "What did the children find when they turned on the light?",
            f"They found a juvenile ghost, which means a little young ghost instead of a big frightening one. Seeing it clearly changed the mystery from scary to sad."
        ),
        (
            "Why did the ghost come closer?",
            f"The ghost smelled {snack_cfg.phrase} and hoped someone might share. It was trying to hide its loneliness by sounding spooky."
        ),
    ]
    if f.get("shared"):
        if share_method == "cut":
            answer = (
                f"{holder.id} divided the {snack_cfg.label} into three pieces so everyone could have some. That careful sharing turned fear into friendship because the ghost felt included."
            )
        else:
            answer = (
                f"The children shared the pieces already on the plate so the ghost could have one too. Because there was enough for all three, the ghost stopped feeling left out."
            )
        qa.append(("How did the children solve the problem?", answer))
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children and the little ghost sitting together under the moonlight and passing the plate back and forth. The room no longer felt haunted, because kindness had changed what the room meant."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "sharing", "light", "lonely", "food"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
share_possible(S) :- snack(S), portions(S,P), need(N), P >= N.
share_possible(S) :- snack(S), divisible(S), portions(S,P), P >= 2.

valid(R,S,L) :- room(R), snack(S), light(L), share_possible(S).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("need", 3)]
    for room_id in ROOMS:
        lines.append(asp.fact("room", room_id))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        lines.append(asp.fact("portions", snack_id, snack.portions))
        if snack.divisible:
            lines.append(asp.fact("divisible", snack_id))
    for light_id in LIGHTS:
        lines.append(asp.fact("light", light_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification safety
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        room="attic",
        snack="moon_cake",
        light="candle_lantern",
        holder_name="Mina",
        holder_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        trait="gentle",
    ),
    StoryParams(
        room="nursery",
        snack="ginger_cookies",
        light="night_lamp",
        holder_name="Ruby",
        holder_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        trait="kind",
    ),
    StoryParams(
        room="parlor",
        snack="apple_tarts",
        light="flashlight",
        holder_name="Sam",
        holder_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        trait="curious",
    ),
]


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a lonely juvenile ghost and a shared snack."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--holder-name")
    ap.add_argument("--holder-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack:
        snack = SNACKS[args.snack]
        if not share_possible(snack, 3):
            raise StoryError(explain_rejection(snack))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.snack is None or combo[1] == args.snack)
        and (args.light is None or combo[2] == args.light)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, snack_id, light_id = rng.choice(sorted(combos))
    holder_gender = args.holder_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    holder_name = args.holder_name or _pick_name(rng, holder_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=holder_name)
    trait = rng.choice(TRAITS)
    return StoryParams(
        room=room_id,
        snack=snack_id,
        light=light_id,
        holder_name=holder_name,
        holder_gender=holder_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Invalid room: {params.room})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Invalid snack: {params.snack})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Invalid light: {params.light})")
    if not share_possible(SNACKS[params.snack], 3):
        raise StoryError(explain_rejection(SNACKS[params.snack]))

    world = tell(
        room_cfg=ROOMS[params.room],
        snack_cfg=SNACKS[params.snack],
        light_cfg=LIGHTS[params.light],
        holder_name=params.holder_name,
        holder_gender=params.holder_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        trait=params.trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, snack, light) combos:\n")
        for room_id, snack_id, light_id in combos:
            print(f"  {room_id:8} {snack_id:15} {light_id}")
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
            header = f"### {p.holder_name} & {p.friend_name}: {p.snack} in the {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
