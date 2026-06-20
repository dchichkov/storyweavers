#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/detach_participate_float_sharing_problem_solving_curiosity.py
========================================================================================

A standalone story world for a small rhyming tale about a little boat that will
not float until children use curiosity, sharing, and problem solving together.

Seed words
----------
detach, participate, float

Design
------
Three children gather by a bit of water and make a tiny parade boat. The maker
adds a charming but too-heavy decoration, so the boat sinks when they test it.
A generous friend shares a buoyant helper, the children figure out they must
detach the heavy piece, and a watching child finds the courage to participate.
The story ends with the boat floating lightly and the children sharing the joy.

Reasonableness gate
-------------------
A story is only valid when:
* the decoration is detachable,
* the decoration makes the first launch fail,
* and the shared helper is strong enough to make the fixed boat float steadily.

This keeps the domain small and child-plausible: fewer stronger stories are
better than lots of weak combinations.

Run it
------
python storyworlds/worlds/gpt-5.4/detach_participate_float_sharing_problem_solving_curiosity.py
python storyworlds/worlds/gpt-5.4/detach_participate_float_sharing_problem_solving_curiosity.py --all
python storyworlds/worlds/gpt-5.4/detach_participate_float_sharing_problem_solving_curiosity.py --qa
python storyworlds/worlds/gpt-5.4/detach_participate_float_sharing_problem_solving_curiosity.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
PASSENGER_WEIGHT = 2
FLOAT_MARGIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    detachable: bool = False
    buoyant: bool = False
    shared: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    line: str
    shimmer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    buoyancy: int
    material: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Attachment:
    id: str
    label: str
    phrase: str
    weight: int
    fastening: str
    detachable: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    boost: int
    method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_sink(world: World) -> list[str]:
    boat = world.get("boat")
    if boat.meters["tested"] < THRESHOLD:
        return []
    if boat.meters["load"] <= boat.meters["support"]:
        return []
    sig = ("sink", int(boat.meters["load"]), int(boat.meters["support"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["sinking"] += 1
    world.get("maker").memes["frustration"] += 1
    world.get("helper").memes["curiosity"] += 1
    world.get("watcher").memes["hesitation"] += 1
    return ["__sink__"]


def _r_float(world: World) -> list[str]:
    boat = world.get("boat")
    if boat.meters["tested"] < THRESHOLD:
        return []
    if boat.meters["load"] > boat.meters["support"]:
        return []
    sig = ("float", int(boat.meters["load"]), int(boat.meters["support"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["floating"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["belonging"] += 1
    return ["__float__"]


CAUSAL_RULES = [
    Rule("sink", "physical", _r_sink),
    Rule("float", "physical", _r_float),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def initial_load(attachment: Attachment) -> int:
    return PASSENGER_WEIGHT + attachment.weight


def steady_target() -> int:
    return PASSENGER_WEIGHT + FLOAT_MARGIN


def sinks_at_first(vessel: Vessel, attachment: Attachment) -> bool:
    return initial_load(attachment) > vessel.buoyancy


def helper_needed(vessel: Vessel) -> bool:
    return vessel.buoyancy < steady_target()


def stable_after_fix(vessel: Vessel, helper: Helper) -> bool:
    return vessel.buoyancy + helper.boost >= steady_target()


def valid_combo(vessel: Vessel, attachment: Attachment, helper: Helper) -> bool:
    return (
        attachment.detachable
        and sinks_at_first(vessel, attachment)
        and helper_needed(vessel)
        and stable_after_fix(vessel, helper)
    )


def explain_rejection(vessel: Vessel, attachment: Attachment, helper: Helper) -> str:
    if not attachment.detachable:
        return (
            f"(No story: {attachment.phrase} is not something the children can safely "
            f"detach, so there is no simple fix for the sinking boat.)"
        )
    if not sinks_at_first(vessel, attachment):
        return (
            f"(No story: {vessel.phrase} would already float with {attachment.phrase}, "
            f"so there is no real problem to solve.)"
        )
    if not helper_needed(vessel):
        return (
            f"(No story: {vessel.phrase} is already buoyant enough after the heavy bit "
            f"is removed, so sharing {helper.phrase} would not be an essential part of "
            f"the solution.)"
        )
    return (
        f"(No story: even after the children detach {attachment.phrase}, sharing "
        f"{helper.phrase} still would not make the boat float steadily.)"
    )


def predict(world: World) -> dict:
    sim = world.copy()
    boat = sim.get("boat")
    boat.meters["tested"] += 1
    propagate(sim, narrate=False)
    return {
        "sinks": boat.meters["sinking"] >= THRESHOLD,
        "floats": boat.meters["floating"] >= THRESHOLD,
        "load": int(boat.meters["load"]),
        "support": int(boat.meters["support"]),
    }


def open_scene(world: World, maker: Entity, helper_kid: Entity, watcher: Entity, vessel: Vessel) -> None:
    maker.memes["curiosity"] += 1
    helper_kid.memes["generosity"] += 1
    watcher.memes["curiosity"] += 1
    world.say(
        f"By {world.place.label}, where {world.place.shimmer}, {maker.id} bent low with a bright little grin. "
        f"{world.place.line}"
    )
    world.say(
        f"{maker.id} made {vessel.phrase} from {vessel.material} so light and small, "
        f"while {helper_kid.id} and {watcher.id} watched the silver water call."
    )


def decorate(world: World, maker: Entity, attachment: Attachment) -> None:
    world.say(
        f'"What if I tie on {attachment.phrase}?" wondered {maker.id}, with a spark in {maker.pronoun("possessive")} eye. '
        f'"It will make our tiny parade-boat handsome as it passes by."'
    )
    world.say(
        f"So on went {attachment.phrase}, {attachment.fastening}, snug and neat. "
        f"It looked so grand and jingly-sweet."
    )


def invite_watcher(world: World, maker: Entity, helper_kid: Entity, watcher: Entity, join_style: str) -> None:
    if join_style == "eager":
        watcher.memes["courage"] += 1
        world.say(
            f'{watcher.id} clapped at once. "I want to participate too!" {watcher.pronoun()} cried with glee. '
            f'"May I walk beside the boat and cheer it down the water with you three?"'
        )
    else:
        watcher.memes["hesitation"] += 1
        world.say(
            f"{watcher.id} hugged {watcher.pronoun('possessive')} knees and watched the ripples wink and wait. "
            f"{watcher.pronoun().capitalize()} wanted to participate, but shyness made {watcher.pronoun('object')} hesitate."
        )
        world.say(
            f'"Come close if you are ready," sang {helper_kid.id}. "{maker.id} and I will save you a place." '
            f'That gentle line put a warmer look on {watcher.id}\'s face.'
        )


def first_test(world: World, maker: Entity, attachment: Attachment) -> None:
    boat = world.get("boat")
    boat.meters["tested"] += 1
    propagate(world, narrate=False)
    if boat.meters["sinking"] >= THRESHOLD:
        world.say(
            f"They set the little boat upon the water with a hopeful little note, "
            f"but down it tipped and down it dipped instead of learning how to float."
        )
        world.say(
            f'"Oh dear," said {maker.id}. "Our shiny {attachment.label} is lovely to see, '
            f'but something in this bobbing puzzle is too heavy for the boat and me."'
        )
    else:
        world.say("The boat floated at once.")
    world.facts["predicted_before"] = predict(world)


def wonder(world: World, helper_kid: Entity, maker: Entity, vessel: Vessel, attachment: Attachment) -> None:
    helper_kid.memes["curiosity"] += 1
    world.say(
        f'{helper_kid.id} crouched low and asked, "Why did it dip and lean? '
        f'Let us look at what is light and what is not, and see what can be seen."'
    )
    world.say(
        f"{maker.id} touched {vessel.label} and {attachment.label} one by one, not wild, not sore. "
        f"Curiosity opened the stuck-up door."
    )


def share_helper(world: World, helper_kid: Entity, helper_cfg: Helper) -> None:
    helper_ent = world.get("shared_helper")
    helper_ent.shared = True
    helper_kid.memes["generosity"] += 1
    world.say(
        f'"I can share {helper_cfg.phrase}," said {helper_kid.id}. "{helper_cfg.method}." '
        f'"A shared small thing can still be strong when friends decide to think along."'
    )


def detach_piece(world: World, maker: Entity, watcher: Entity, attachment: Attachment) -> None:
    boat = world.get("boat")
    attach = world.get("attachment")
    attach.meters["attached"] = 0.0
    boat.meters["load"] -= attachment.weight
    maker.memes["problem_solving"] += 1
    watcher.memes["courage"] += 1
    world.say(
        f'{maker.id} nodded slowly. "Then we must detach {attachment.phrase}," {maker.pronoun()} said. '
        f'"Pretty is nice, but floating first is wiser instead."'
    )
    world.say(
        f"{watcher.id} held out careful fingers while {maker.id} loosened the {attachment.fastening}. "
        f"Off came the heavy piece, and the plan grew bright and glistening."
    )


def add_helper(world: World, helper_kid: Entity, helper_cfg: Helper) -> None:
    boat = world.get("boat")
    shared_helper = world.get("shared_helper")
    shared_helper.meters["attached"] = 1.0
    boat.meters["support"] += helper_cfg.boost
    helper_kid.memes["problem_solving"] += 1
    world.say(
        f"Then {helper_kid.id} shared {helper_cfg.phrase}, and together they tucked it in place. "
        f"{helper_cfg.method.capitalize()}, giving the little boat a steadier grace."
    )


def watcher_joins(world: World, watcher: Entity, join_style: str) -> None:
    watcher.memes["belonging"] += 1
    if join_style == "eager":
        world.say(
            f"{watcher.id} was already dancing near the shore, ready to do one cheerful part more. "
            f"{watcher.pronoun().capitalize()} placed the tiny seed passenger gently in and beamed from ear to grin."
        )
    else:
        world.say(
            f'Then {watcher.id} took a brave small breath. "Now I can participate," {watcher.pronoun()} said. '
            f'{watcher.pronoun().capitalize()} set the tiny seed passenger in the middle as carefully as thread.'
        )


def second_test(world: World, maker: Entity, helper_kid: Entity, watcher: Entity) -> None:
    boat = world.get("boat")
    boat.meters["tested"] += 1
    propagate(world, narrate=False)
    if boat.meters["floating"] >= THRESHOLD:
        world.say(
            "Back on the water went the boat, where the cloud-lace met the sky. "
            "This time it learned to float, to bob, to gleam, to glide on by."
        )
        world.say(
            f"{maker.id} laughed, {helper_kid.id} clapped, and {watcher.id} skipped beside the shining moat. "
            "Their shared idea had solved the snag and sent a happy little boat afloat."
        )


def close_story(world: World, maker: Entity, helper_kid: Entity, watcher: Entity, attachment: Attachment) -> None:
    world.say(
        f'They left {attachment.label} on the bank and did not mind that it stayed behind. '
        "They had learned that curious hearts can change a plan and still be kind."
    )
    world.say(
        f"So the three small friends shared turns and songs beside the twinkling note, "
        f"and because they asked, they shared, they solved, their tiny parade could float."
    )


def tell(
    place: Place,
    vessel: Vessel,
    attachment: Attachment,
    helper_cfg: Helper,
    maker_name: str = "Lina",
    maker_gender: str = "girl",
    helper_name: str = "Owen",
    helper_gender: str = "boy",
    watcher_name: str = "Mira",
    watcher_gender: str = "girl",
    join_style: str = "shy",
) -> World:
    world = World(place)
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_gender, role="maker", traits=["curious"]))
    helper_kid = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["sharing"]))
    watcher = world.add(Entity(id=watcher_name, kind="character", type=watcher_gender, role="watcher", traits=["quiet"]))
    boat = world.add(Entity(id="boat", type="boat", label=vessel.label, attrs={"material": vessel.material}))
    boat.meters["support"] = float(vessel.buoyancy)
    boat.meters["load"] = float(initial_load(attachment))
    world.add(Entity(id="attachment", type="attachment", label=attachment.label, detachable=attachment.detachable))
    world.get("attachment").meters["attached"] = 1.0
    world.add(Entity(id="shared_helper", type="helper", label=helper_cfg.label, buoyant=True))

    open_scene(world, maker, helper_kid, watcher, vessel)
    decorate(world, maker, attachment)
    world.para()
    invite_watcher(world, maker, helper_kid, watcher, join_style)
    first_test(world, maker, attachment)
    world.para()
    wonder(world, helper_kid, maker, vessel, attachment)
    share_helper(world, helper_kid, helper_cfg)
    detach_piece(world, maker, watcher, attachment)
    add_helper(world, helper_kid, helper_cfg)
    watcher_joins(world, watcher, join_style)
    world.para()
    second_test(world, maker, helper_kid, watcher)
    close_story(world, maker, helper_kid, watcher, attachment)

    world.facts.update(
        place=place,
        vessel=vessel,
        attachment_cfg=attachment,
        helper_cfg=helper_cfg,
        maker=maker,
        helper=helper_kid,
        watcher=watcher,
        join_style=join_style,
        initial_load=initial_load(attachment),
        final_load=int(world.get("boat").meters["load"]),
        initial_support=vessel.buoyancy,
        final_support=int(world.get("boat").meters["support"]),
        detached=world.get("attachment").meters["attached"] < THRESHOLD,
        shared=world.get("shared_helper").shared,
        participated=True,
        floated=world.get("boat").meters["floating"] >= THRESHOLD,
        sank_first=world.get("boat").meters["sinking"] >= THRESHOLD,
    )
    return world


PLACES = {
    "puddle": Place(
        "puddle",
        "the sunlit puddle by the garden stones",
        "the puddle wore a ring of sky",
        "Soft mint leaves nodded, and a bee went humming by.",
        tags={"puddle", "water"},
    ),
    "brook": Place(
        "brook",
        "the calm brook by the stepping logs",
        "the brook made silver commas as it slid",
        "Bright reeds bowed low, and minnows winked where shadows hid.",
        tags={"brook", "water"},
    ),
    "barrel": Place(
        "barrel",
        "the rain barrel under the plum tree",
        "the barrel held a round blue patch of noon",
        "A plum leaf spun like a little green balloon.",
        tags={"rain", "water"},
    ),
}

VESSELS = {
    "leaf": Vessel("leaf", "leaf boat", "a small curled leaf boat", 1, "a curled green leaf", tags={"leaf", "boat"}),
    "bark": Vessel("bark", "bark boat", "a tiny bark boat", 2, "a strip of bark", tags={"bark", "boat"}),
    "shell": Vessel("shell", "walnut-shell boat", "a tiny walnut-shell boat", 2, "half a walnut shell", tags={"shell", "boat"}),
    "sponge": Vessel("sponge", "sponge tray", "a little sponge tray", 3, "a cut square of sponge", tags={"sponge", "boat"}),
}

ATTACHMENTS = {
    "bell": Attachment("bell", "bell charm", "a bright bell charm", 2, "string knot", True, tags={"bell", "heavy"}),
    "pebble": Attachment("pebble", "pebble star", "a painted pebble star", 2, "ribbon loop", True, tags={"pebble", "heavy"}),
    "button": Attachment("button", "button moon", "a shiny button moon", 1, "twine bow", True, tags={"button"}),
    "glued_shell": Attachment("glued_shell", "shell crown", "a glued shell crown", 2, "glue spot", False, tags={"shell", "heavy"}),
}

HELPERS = {
    "cork": Helper("cork", "cork chip", "a cork chip", 1, "It sat under one side like a tiny raft shoe", tags={"cork", "sharing"}),
    "reed": Helper("reed", "reed outrigger", "a reed outrigger", 1, "It stretched along the edge like a balancing arm", tags={"reed", "sharing"}),
    "foam": Helper("foam", "foam strip", "a foam strip", 2, "It hugged the hull with a soft bright lift", tags={"foam", "sharing"}),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Pia", "Tessa", "Lulu", "Ivy", "Rosa", "Ada", "June"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Arlo", "Finn", "Jude", "Max", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in PLACES:
        for vessel_id, vessel in VESSELS.items():
            for attachment_id, attachment in ATTACHMENTS.items():
                for helper_id, helper_cfg in HELPERS.items():
                    if valid_combo(vessel, attachment, helper_cfg):
                        combos.append((place, vessel_id, attachment_id, helper_id))
    return combos


@dataclass
class StoryParams:
    place: str
    vessel: str
    attachment: str
    helper: str
    maker: str
    maker_gender: str
    helper_name: str
    helper_gender: str
    watcher: str
    watcher_gender: str
    join_style: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "boat": [(
        "Why do some tiny boats sink and some float?",
        "A tiny boat floats when it pushes enough water to hold itself up. If it is too heavy for its shape, it sinks lower or tips under."
    )],
    "cork": [(
        "Why does cork help things float?",
        "Cork is light and full of tiny air spaces. Those little spaces help it stay on top of the water."
    )],
    "reed": [(
        "What does an outrigger do?",
        "An outrigger sticks out to the side to help a boat balance. It makes tipping less likely."
    )],
    "foam": [(
        "Why is foam good for floating crafts?",
        "Foam is very light and holds lots of air. That extra lightness helps a little craft stay up on the water."
    )],
    "sharing": [(
        "What does sharing do in a problem?",
        "Sharing lets two or more people use what one person has. Sometimes one shared object becomes the key to solving the whole problem."
    )],
    "curiosity": [(
        "How can curiosity help when something goes wrong?",
        "Curiosity helps you stop and ask why. When you look closely instead of giving up, you can notice what needs to change."
    )],
    "detach": [(
        "What does detach mean?",
        "Detach means to take something off from where it was fastened. You might detach a charm, a sticker, or a lid."
    )],
}
KNOWLEDGE_ORDER = ["boat", "cork", "reed", "foam", "sharing", "curiosity", "detach"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, vessel, attachment, helper_cfg = f["place"], f["vessel"], f["attachment_cfg"], f["helper_cfg"]
    maker, helper_kid, watcher = f["maker"], f["helper"], f["watcher"]
    return [
        'Write a rhyming story for a 3-to-5-year-old that includes the words "detach", "participate", and "float".',
        f"Tell a gentle rhyming story where {maker.id} makes {vessel.phrase} by {place.label}, but {attachment.phrase} makes it sink until a friend shares {helper_cfg.phrase}.",
        f"Write a child-facing poem-story about curiosity, sharing, and problem solving, where {watcher.id} is shy at first but learns to participate after the children fix a tiny boat.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker, helper_kid, watcher = f["maker"], f["helper"], f["watcher"]
    vessel, attachment, helper_cfg = f["vessel"], f["attachment_cfg"], f["helper_cfg"]
    place = f["place"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {maker.id}, {helper_kid.id}, and {watcher.id} by {place.label}. They work together on a tiny boat instead of one child doing everything alone."
        ),
        (
            f"Why did the {vessel.label} sink the first time?",
            f"It sank because {attachment.phrase} was too heavy for {vessel.phrase}. The first test showed that the boat's load was bigger than the support it had on the water."
        ),
        (
            f"What did the children do to solve the problem?",
            f"They used curiosity first and looked closely at what was making the boat dip. Then they detach {attachment.phrase} and added {helper_cfg.phrase}, so the boat became light enough and steady enough to float."
        ),
        (
            f"How did sharing help in the story?",
            f"{helper_kid.id} shared {helper_cfg.phrase} instead of keeping it. That shared piece became part of the fix, so kindness and problem solving worked together."
        ),
        (
            f"How did {watcher.id} begin to participate?",
            f"{watcher.id} joined in after the children made the plan feel safe and clear. Helping with the careful fix gave {watcher.pronoun('object')} the courage to step closer and take part."
        ),
        (
            "How did the story end?",
            f"The boat floated gently, and all three children walked beside it singing. The ending shows what changed: the heavy bit was gone, the shared helper was added, and the shy child felt included."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"boat", "sharing", "curiosity", "detach"}
    tags |= set(f["helper_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.detachable:
            bits.append("detachable=True")
        if ent.shared:
            bits.append("shared=True")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("puddle", "leaf", "button", "foam", "Lina", "girl", "Owen", "boy", "Mira", "girl", "shy"),
    StoryParams("brook", "bark", "button", "reed", "Nora", "girl", "Theo", "boy", "June", "girl", "eager"),
    StoryParams("barrel", "shell", "button", "cork", "Ada", "girl", "Milo", "boy", "Rosa", "girl", "shy"),
    StoryParams("puddle", "bark", "pebble", "cork", "Ivy", "girl", "Finn", "boy", "Pia", "girl", "eager"),
    StoryParams("brook", "leaf", "bell", "foam", "Lulu", "girl", "Arlo", "boy", "Mira", "girl", "shy"),
]


ASP_RULES = r"""
load(A, L) :- attachment(A), weight(A, W), passenger_weight(P), L = W + P.
sinks_first(V, A) :- vessel(V), attachment(A), load(A, L), buoyancy(V, B), L > B.
helper_needed(V) :- vessel(V), buoyancy(V, B), steady_target(T), B < T.
stable_after_fix(V, H) :- vessel(V), helper(H), buoyancy(V, B), boost(H, X), steady_target(T), B + X >= T.
valid(V, A, H) :- vessel(V), attachment(A), helper(H),
                  detachable(A), sinks_first(V, A), helper_needed(V), stable_after_fix(V, H).
valid_story(P, V, A, H) :- place(P), valid(V, A, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        lines.append(asp.fact("buoyancy", vid, vessel.buoyancy))
    for aid, attachment in ATTACHMENTS.items():
        lines.append(asp.fact("attachment", aid))
        lines.append(asp.fact("weight", aid, attachment.weight))
        if attachment.detachable:
            lines.append(asp.fact("detachable", aid))
    for hid, helper_cfg in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("boost", hid, helper_cfg.boost))
    lines.append(asp.fact("passenger_weight", PASSENGER_WEIGHT))
    lines.append(asp.fact("steady_target", steady_target()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    smoke_cases = list(CURATED[:2])
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(7)))
    except StoryError as err:
        rc = 1
        print(f"Smoke-test setup failed: {err}")
        smoke_cases = list(CURATED[:2])

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story or "float" not in sample.story:
                raise StoryError("Generated story is empty or missing the expected ending word 'float'.")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=True, qa=True, header=f"### smoke {idx}")
        except Exception as err:
            rc = 1
            print(f"Smoke-test generation failed for case {idx}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a tiny boat sinks, friends share and solve, then it floats."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--attachment", choices=ATTACHMENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--join-style", choices=["shy", "eager"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from the ASP reasoner")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vessel and args.attachment and args.helper:
        if not valid_combo(VESSELS[args.vessel], ATTACHMENTS[args.attachment], HELPERS[args.helper]):
            raise StoryError(explain_rejection(VESSELS[args.vessel], ATTACHMENTS[args.attachment], HELPERS[args.helper]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.vessel is None or c[1] == args.vessel)
        and (args.attachment is None or c[2] == args.attachment)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        if args.vessel and args.attachment and args.helper:
            raise StoryError(explain_rejection(VESSELS[args.vessel], ATTACHMENTS[args.attachment], HELPERS[args.helper]))
        raise StoryError("(No valid combination matches the given options.)")

    place, vessel, attachment, helper_cfg = rng.choice(sorted(combos))
    maker, maker_gender = _pick_name(rng, set())
    helper_name, helper_gender = _pick_name(rng, {maker})
    watcher, watcher_gender = _pick_name(rng, {maker, helper_name})
    join_style = args.join_style or rng.choice(["shy", "eager"])
    return StoryParams(
        place=place,
        vessel=vessel,
        attachment=attachment,
        helper=helper_cfg,
        maker=maker,
        maker_gender=maker_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        watcher=watcher,
        watcher_gender=watcher_gender,
        join_style=join_style,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        VESSELS[params.vessel],
        ATTACHMENTS[params.attachment],
        HELPERS[params.helper],
        params.maker,
        params.maker_gender,
        params.helper_name,
        params.helper_gender,
        params.watcher,
        params.watcher_gender,
        params.join_style,
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, vessel, attachment, helper) combos:\n")
        for place, vessel, attachment, helper_cfg in combos:
            print(f"  {place:7} {vessel:7} {attachment:11} {helper_cfg}")
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
            header = f"### {p.maker}, {p.helper_name}, and {p.watcher}: {p.vessel} + {p.attachment} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
