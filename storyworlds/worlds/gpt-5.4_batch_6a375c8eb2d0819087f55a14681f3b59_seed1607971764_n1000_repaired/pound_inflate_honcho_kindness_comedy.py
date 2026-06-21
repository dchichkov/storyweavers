#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pound_inflate_honcho_kindness_comedy.py
==================================================================

A standalone storyworld about a silly little kindness parade.

Children build a balloon surprise to cheer someone up. One child appoints
themself the "honcho," gets too bossy, and makes the parade less kind than it
was meant to be. The turn comes when the balloon plan goes wobbly or the helper
looks hurt; the resolution comes when the honcho chooses kindness, shares the
job, and the joke becomes a real gift.

The world model enforces two reasonableness rules:

* the chosen inflator must be strong enough to inflate the chosen balloon
* the parade noise must be gentle enough for the recipient

So this world will refuse a story like "a baby gets cheered up by a booming
drum" or "a giant balloon gets filled by one tiny puff."

Run it
------
    python storyworlds/worlds/gpt-5.4/pound_inflate_honcho_kindness_comedy.py
    python storyworlds/worlds/gpt-5.4/pound_inflate_honcho_kindness_comedy.py --recipient baby --band drum
    python storyworlds/worlds/gpt-5.4/pound_inflate_honcho_kindness_comedy.py --all
    python storyworlds/worlds/gpt-5.4/pound_inflate_honcho_kindness_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pound_inflate_honcho_kindness_comedy.py --json
    python storyworlds/worlds/gpt-5.4/pound_inflate_honcho_kindness_comedy.py --asp
    python storyworlds/worlds/gpt-5.4/pound_inflate_honcho_kindness_comedy.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandma", "woman"}
        male = {"boy", "father", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandpa": "grandpa", "grandma": "grandma"}.get(
            self.type, self.type
        )
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Recipient:
    id: str
    label: str
    kind: str
    place: str
    need: str
    noise_tolerance: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class BalloonSpec:
    id: str
    label: str
    phrase: str
    air_need: int
    safe_max: int
    needs_helper: bool
    ending_pose: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Inflator:
    id: str
    label: str
    phrase: str
    power: int
    style: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class BandItem:
    id: str
    label: str
    phrase: str
    loudness: int
    sound: str
    beat_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class KindAct:
    id: str
    line: str
    repair: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    recipient: str
    balloon: str
    inflator: str
    band: str
    kindness: str
    leader_name: str
    leader_gender: str
    helper_name: str
    helper_gender: str
    grownup: str
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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_bossy(world: World) -> list[str]:
    leader = world.get("leader")
    helper = world.get("helper")
    team = world.get("team")
    if leader.memes["bossy"] < THRESHOLD or team.memes["kind_repair"] >= THRESHOLD:
        return []
    sig = ("bossy",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["small"] += 1
    team.meters["wobble"] += 1
    return ["__bossy__"]


def _r_ready(world: World) -> list[str]:
    balloon = world.get("balloon")
    spec: BalloonSpec = world.facts["balloon_cfg"]
    if balloon.meters["air"] < spec.air_need or balloon.meters["popped"] >= THRESHOLD:
        return []
    sig = ("ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    balloon.meters["ready"] += 1
    return []


def _r_pop(world: World) -> list[str]:
    balloon = world.get("balloon")
    spec: BalloonSpec = world.facts["balloon_cfg"]
    if balloon.meters["air"] <= spec.safe_max:
        return []
    sig = ("pop",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    balloon.meters["popped"] += 1
    balloon.meters["ready"] = 0.0
    world.get("leader").memes["surprise"] += 1
    world.get("helper").memes["surprise"] += 1
    return ["__pop__"]


def _r_pair_need(world: World) -> list[str]:
    balloon = world.get("balloon")
    helper = world.get("helper")
    team = world.get("team")
    spec: BalloonSpec = world.facts["balloon_cfg"]
    if not spec.needs_helper or balloon.meters["air"] < spec.air_need or team.memes["kind_repair"] >= THRESHOLD:
        return []
    if helper.memes["small"] < THRESHOLD:
        return []
    sig = ("slip",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    balloon.meters["escaped"] += 1
    team.meters["wobble"] += 1
    return ["__slip__"]


def _r_cheer(world: World) -> list[str]:
    balloon = world.get("balloon")
    team = world.get("team")
    recipient = world.get("recipient")
    if balloon.meters["ready"] < THRESHOLD or team.memes["kind_repair"] < THRESHOLD:
        return []
    sig = ("cheer",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    recipient.memes["cheered"] += 1
    team.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="bossy", tag="social", apply=_r_bossy),
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="pop", tag="physical", apply=_r_pop),
    Rule(name="pair_need", tag="physical", apply=_r_pair_need),
    Rule(name="cheer", tag="social", apply=_r_cheer),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if sent.startswith("__"):
                continue
            world.say(sent)
    return produced


RECIPIENTS = {
    "baby": Recipient(
        id="baby",
        label="baby Pip",
        kind="baby",
        place="the nursery doorway",
        need="had been trying to nap and had woken up cross",
        noise_tolerance=1,
        tags={"baby", "quiet"},
    ),
    "grandpa": Recipient(
        id="grandpa",
        label="Grandpa Lou",
        kind="grandpa",
        place="the porch swing",
        need="was stuck inside with a rainy-day frown",
        noise_tolerance=2,
        tags={"grandpa", "kindness"},
    ),
    "neighbor": Recipient(
        id="neighbor",
        label="Mrs. Bee next door",
        kind="neighbor",
        place="the front gate",
        need="had dropped her grocery bag and looked glum",
        noise_tolerance=3,
        tags={"neighbor", "kindness"},
    ),
}

BALLOONS = {
    "dog": BalloonSpec(
        id="dog",
        label="balloon dog",
        phrase="a noodle-thin balloon dog",
        air_need=1,
        safe_max=2,
        needs_helper=False,
        ending_pose="trotted over the floor with its noodle tail held high",
        tags={"balloon", "dog"},
    ),
    "giraffe": BalloonSpec(
        id="giraffe",
        label="balloon giraffe",
        phrase="a long-necked balloon giraffe",
        air_need=2,
        safe_max=3,
        needs_helper=True,
        ending_pose="wobbled above their hands with a neck taller than anyone's hat",
        tags={"balloon", "giraffe"},
    ),
    "rocket": BalloonSpec(
        id="rocket",
        label="rocket balloon",
        phrase="a squeaky rocket balloon",
        air_need=3,
        safe_max=4,
        needs_helper=True,
        ending_pose="bobbed in the air like it wanted to zoom straight to the moon",
        tags={"balloon", "rocket"},
    ),
}

INFLATORS = {
    "lungs": Inflator(
        id="lungs",
        label="their own breath",
        phrase="just their own cheeks and breath",
        power=1,
        style="puffed until their cheeks looked like apples",
        tags={"breath"},
    ),
    "hand_pump": Inflator(
        id="hand_pump",
        label="hand pump",
        phrase="a little hand pump",
        power=2,
        style="worked the handle with quick squeak-squeak strokes",
        tags={"pump"},
    ),
    "foot_pump": Inflator(
        id="foot_pump",
        label="foot pump",
        phrase="a stomp-and-wheeze foot pump",
        power=3,
        style="pressed the pedal with one sneaker like a band leader on a mission",
        tags={"pump", "foot_pump"},
    ),
}

BANDS = {
    "bell": BandItem(
        id="bell",
        label="jingle bell",
        phrase="a jingle bell on a ribbon",
        loudness=1,
        sound="ting-ting",
        beat_line="rang the little bell as if even tiny sounds deserved a parade",
        tags={"bell", "quiet"},
    ),
    "kazoo": BandItem(
        id="kazoo",
        label="kazoo",
        phrase="a bright red kazoo",
        loudness=2,
        sound="bzz-waaa",
        beat_line="buzzed the kazoo in proud little zigzags",
        tags={"kazoo"},
    ),
    "drum": BandItem(
        id="drum",
        label="toy drum",
        phrase="a toy drum with a loose strap",
        loudness=3,
        sound="rat-a-tat",
        beat_line="began to pound the toy drum with such serious eyebrows that the whole hall felt official",
        tags={"drum", "loud"},
    ),
}

KIND_ACTS = {
    "share_title": KindAct(
        id="share_title",
        line='"I cannot be the only honcho,"',
        repair="so they drew a second paper badge and pinned it on their helper too",
        ending="From then on, every order turned into a giggly idea shared by two honchos instead of one.",
        tags={"kindness", "sharing"},
    ),
    "apologize": KindAct(
        id="apologize",
        line='"I was acting too bossy,"',
        repair="and they gave the next important job to their helper with both hands and a real apology",
        ending="The apology made the room feel lighter, as if someone had opened a window inside the game.",
        tags={"kindness", "apology"},
    ),
    "hold_nozzle": KindAct(
        id="hold_nozzle",
        line='"Will you help me hold the wiggly part?"',
        repair="and they scooted over so their helper could steady the nozzle and save the silly plan",
        ending="The question itself was kind, and it turned the parade from show-off play into together play.",
        tags={"kindness", "helping"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Zoe", "Ava", "Poppy", "Ella", "June"]
BOY_NAMES = ["Ben", "Milo", "Toby", "Eli", "Leo", "Sam", "Owen", "Finn"]
TRAITS = ["sparky", "cheerful", "bouncy", "busy", "funny", "earnest"]


def valid_combo(recipient: Recipient, balloon: BalloonSpec, inflator: Inflator, band: BandItem) -> bool:
    return inflator.power >= balloon.air_need and band.loudness <= recipient.noise_tolerance


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for rid, recipient in RECIPIENTS.items():
        for bid, balloon in BALLOONS.items():
            for iid, inflator in INFLATORS.items():
                for band_id, band in BANDS.items():
                    if valid_combo(recipient, balloon, inflator, band):
                        combos.append((rid, bid, iid, band_id))
    return combos


def explain_rejection(recipient: Recipient, balloon: BalloonSpec, inflator: Inflator, band: BandItem) -> str:
    if inflator.power < balloon.air_need:
        return (
            f"(No story: {inflator.phrase} is too weak to inflate {balloon.phrase}. "
            f"That balloon needs more air than this tool can give.)"
        )
    if band.loudness > recipient.noise_tolerance:
        return (
            f"(No story: {band.phrase} is too loud for {recipient.label}. "
            f"A kindness parade must be gentle enough for the person it is cheering.)"
        )
    return "(No story: this combination does not make sense in this world.)"


def predict_first_try(world: World) -> dict:
    sim = world.copy()
    balloon = sim.get("balloon")
    spec: BalloonSpec = sim.facts["balloon_cfg"]
    inflator: Inflator = sim.facts["inflator_cfg"]
    balloon.meters["air"] += inflator.power
    propagate(sim, narrate=False)
    return {
        "ready": balloon.meters["ready"] >= THRESHOLD,
        "escaped": balloon.meters["escaped"] >= THRESHOLD,
        "popped": balloon.meters["popped"] >= THRESHOLD,
    }


def introduce(world: World, leader: Entity, helper: Entity, grownup: Entity, recipient: Entity, recipient_cfg: Recipient) -> None:
    trait = leader.traits[0] if leader.traits else "busy"
    world.say(
        f"After lunch, {leader.id} and {helper.id} were in the hallway with a roll of ribbon, "
        f"a paper badge, and a very large plan. {leader.id} was a {trait} little {leader.type} "
        f"who loved any idea that felt one inch bigger than the room."
    )
    world.say(
        f"{grownup.label_word.capitalize()} said that {recipient_cfg.label} {recipient_cfg.need}, "
        f"so the children decided to make a kindness parade."
    )


def mission(world: World, leader: Entity, helper: Entity, recipient_cfg: Recipient, balloon: BalloonSpec, band: BandItem) -> None:
    leader.memes["purpose"] += 1
    helper.memes["purpose"] += 1
    world.say(
        f'"We will cheer up {recipient_cfg.label} at {recipient_cfg.place}," {leader.id} said. '
        f'"We need {balloon.phrase} and {band.phrase}."'
    )
    world.say(
        f"{helper.id} nodded so hard that even the ribbon ends bounced."
    )


def claim_honcho(world: World, leader: Entity, helper: Entity, band: BandItem) -> None:
    leader.memes["bossy"] += 1
    world.say(
        f"Then {leader.id} pinned the paper badge to {leader.pronoun('possessive')} shirt and announced, "
        f'"I am the parade honcho."'
    )
    if band.id == "drum":
        world.say(f"To prove it, {leader.pronoun()} {band.beat_line}.")
    else:
        world.say(
            f"To prove it, {leader.pronoun()} began to pound one sneaker on the floor like a drum and "
            f"{band.beat_line}."
        )
    propagate(world, narrate=False)
    if helper.memes["small"] >= THRESHOLD:
        world.say(
            f"{helper.id} smiled with only half of {helper.pronoun('possessive')} mouth. "
            f"The badge was funny, but being ordered around did not feel funny."
        )


def plan_inflate(world: World, leader: Entity, helper: Entity, balloon: BalloonSpec, inflator: Inflator) -> None:
    world.say(
        f"Next came the hard part: they had to inflate {balloon.phrase} using {inflator.phrase}. "
        f"{leader.id} grabbed it first and {inflator.style}."
    )
    world.facts["prediction"] = predict_first_try(world)
    pred = world.facts["prediction"]
    if pred["escaped"]:
        world.say(
            f"{helper.id} reached for the tail, but {leader.id} was still trying to do every job at once."
        )
    elif pred["ready"]:
        world.say(
            f"For one hopeful second, it looked as if bossy speed might actually work."
        )


def first_try(world: World, leader: Entity, helper: Entity, balloon_cfg: BalloonSpec, inflator: Inflator) -> None:
    balloon = world.get("balloon")
    balloon.meters["air"] += inflator.power
    markers = propagate(world, narrate=False)
    if "__pop__" in markers:
        world.say(
            f"There was a squeal, a tiny pause, and then POP. The balloon smacked {leader.id} on the forehead "
            f"and fell down like a noodle that had lost an argument."
        )
        world.facts["mishap"] = "pop"
        return
    if "__slip__" in markers:
        world.say(
            f"The balloon grew long and proud for half a blink, then the loose end zipped free. "
            f"It whistled around the hallway with a rude little pfffft and booped the wall beside {helper.id}."
        )
        world.facts["mishap"] = "slip"
        return
    if balloon.meters["ready"] >= THRESHOLD:
        world.say(
            f"The balloon held its air, but the room still felt crooked because only one person was being important."
        )
        world.facts["mishap"] = "crooked_feeling"
        return
    world.say(
        f"Nothing terrible happened, but the balloon was still too floppy to be a parade star."
    )
    world.facts["mishap"] = "floppy"


def kindness_turn(world: World, leader: Entity, helper: Entity, act: KindAct) -> None:
    team = world.get("team")
    leader.memes["bossy"] = 0.0
    helper.memes["small"] = 0.0
    team.memes["kind_repair"] += 1
    team.memes["together"] += 1
    helper.memes["brave"] += 1
    world.say(
        f"{leader.id} looked at {helper.id}, looked at the silly badge, and finally understood the problem. "
        f"A kindness parade could not start by making a friend feel small."
    )
    world.say(
        f'{act.line} {leader.id} said, {act.repair}.'
    )
    world.say(act.ending)


def second_try(world: World, leader: Entity, helper: Entity, balloon_cfg: BalloonSpec, inflator: Inflator) -> None:
    balloon = world.get("balloon")
    if balloon.meters["popped"] >= THRESHOLD:
        balloon.meters["air"] = 0.0
        balloon.meters["popped"] = 0.0
        world.fired.discard(("pop",))
        world.say(
            f"{grown_word(world).capitalize()} handed them one spare balloon, because even comedy sometimes needs a second chance."
        )
    if balloon.meters["escaped"] >= THRESHOLD:
        balloon.meters["escaped"] = 0.0
        world.fired.discard(("slip",))
    balloon.meters["air"] = float(balloon_cfg.air_need)
    world.fired.discard(("ready",))
    propagate(world, narrate=False)
    world.say(
        f"This time {leader.id} held, {helper.id} steadied, and together they made room for each puff instead of wrestling it."
    )
    world.say(
        f"Soon the {balloon_cfg.label} was ready."
    )


def parade_end(world: World, leader: Entity, helper: Entity, recipient_cfg: Recipient, band: BandItem, balloon_cfg: BalloonSpec) -> None:
    recipient = world.get("recipient")
    team = world.get("team")
    propagate(world, narrate=False)
    if recipient.memes["cheered"] < THRESHOLD:
        raise StoryError("(Internal story error: the parade never became cheerful.)")
    world.say(
        f"They tiptoed to {recipient_cfg.place}. {helper.id} carried the balloon, {leader.id} kept the beat, "
        f"and this time the sound was meant for smiling, not showing off."
    )
    if band.id == "drum":
        world.say(
            f"{leader.id} gave the drum only the gentlest rat-a-tat, no bigger than a polite knock."
        )
    else:
        world.say(
            f"The {band.label} made a soft {band.sound}, just enough to sound silly and kind at once."
        )
    world.say(
        f"When {recipient_cfg.label} looked up and saw the {balloon_cfg.label}, it {balloon_cfg.ending_pose}. "
        f"{recipient_cfg.label} laughed, and the laugh was the exact size the hallway had been waiting for."
    )
    if team.memes["together"] >= THRESHOLD:
        world.say(
            f"{leader.id} touched the paper badge, then moved it to the middle so both children could hold it. "
            f"Being the honcho turned out to be funniest when kindness was in charge."
        )


def grown_word(world: World) -> str:
    return world.get("grownup").label_word


def tell(
    recipient_cfg: Recipient,
    balloon_cfg: BalloonSpec,
    inflator_cfg: Inflator,
    band_cfg: BandItem,
    act_cfg: KindAct,
    leader_name: str = "Lila",
    leader_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    grownup_type: str = "mother",
    leader_trait: str = "cheerful",
) -> World:
    world = World()
    leader = world.add(
        Entity(
            id="leader",
            kind="character",
            type=leader_gender,
            label=leader_name,
            role="leader",
            traits=[leader_trait],
            attrs={"name": leader_name},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
            traits=["patient"],
            attrs={"name": helper_name},
        )
    )
    grownup = world.add(
        Entity(
            id="grownup",
            kind="character",
            type=grownup_type,
            label="the grown-up",
            role="grownup",
            attrs={},
        )
    )
    recipient_type = "baby" if recipient_cfg.kind == "baby" else ("grandpa" if recipient_cfg.kind == "grandpa" else "woman")
    recipient = world.add(
        Entity(
            id="recipient",
            kind="character",
            type=recipient_type,
            label=recipient_cfg.label,
            role="recipient",
            attrs={},
        )
    )
    balloon = world.add(
        Entity(
            id="balloon",
            kind="thing",
            type="balloon",
            label=balloon_cfg.label,
            role="balloon",
            attrs={"spare_available": 1},
        )
    )
    team = world.add(
        Entity(
            id="team",
            kind="thing",
            type="team",
            label="the team",
            role="team",
            attrs={},
        )
    )
    world.facts.update(
        recipient_cfg=recipient_cfg,
        balloon_cfg=balloon_cfg,
        inflator_cfg=inflator_cfg,
        band_cfg=band_cfg,
        kindness_cfg=act_cfg,
        leader=leader,
        helper=helper,
        grownup=grownup,
        recipient=recipient,
        balloon=balloon,
        team=team,
        leader_name=leader_name,
        helper_name=helper_name,
    )

    introduce(world, leader, helper, grownup, recipient, recipient_cfg)
    mission(world, leader, helper, recipient_cfg, balloon_cfg, band_cfg)

    world.para()
    claim_honcho(world, leader, helper, band_cfg)
    plan_inflate(world, leader, helper, balloon_cfg, inflator_cfg)
    first_try(world, leader, helper, balloon_cfg, inflator_cfg)

    world.para()
    kindness_turn(world, leader, helper, act_cfg)
    second_try(world, leader, helper, balloon_cfg, inflator_cfg)
    world.para()
    parade_end(world, leader, helper, recipient_cfg, band_cfg, balloon_cfg)

    world.facts.update(
        outcome="cheered",
        mishap=world.facts.get("mishap", "none"),
        repaired=team.memes["kind_repair"] >= THRESHOLD,
        recipient_cheered=recipient.memes["cheered"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "pump": [
        (
            "What does a pump do?",
            "A pump pushes air into something. That is how it can inflate a balloon without using only your breath.",
        )
    ],
    "foot_pump": [
        (
            "What is a foot pump?",
            "A foot pump is a pump you press with your foot. It can move a lot of air with each push.",
        )
    ],
    "breath": [
        (
            "How do you blow up a balloon with your breath?",
            "You blow air from your lungs into the balloon. Small balloons are easier because they need less air.",
        )
    ],
    "drum": [
        (
            "Why can a drum be too loud for a baby?",
            "Babies are small and sudden big sounds can startle them. A kind helper chooses a softer sound when someone needs quiet.",
        )
    ],
    "bell": [
        (
            "What is a jingle bell?",
            "A jingle bell is a small bell that makes a light ringing sound. It is often gentler than a drum.",
        )
    ],
    "kazoo": [
        (
            "What does a kazoo sound like?",
            "A kazoo makes a buzzy humming sound when you hum into it. It sounds silly, which is why it can be funny in a parade.",
        )
    ],
    "balloon": [
        (
            "Why do balloons need air?",
            "A balloon is limp until air stretches the rubber and fills it up. The air inside is what gives it shape.",
        )
    ],
    "dog": [
        (
            "What is a balloon dog?",
            "A balloon dog is a balloon twisted to look like a little dog. It is silly because it looks ready to walk even though it is only air.",
        )
    ],
    "giraffe": [
        (
            "Why is a balloon giraffe funny to look at?",
            "Its neck is much taller than a real toy's neck, so it looks wobbly and surprising. The strange shape makes people laugh.",
        )
    ],
    "rocket": [
        (
            "Why do rocket balloons wiggle so much?",
            "Long balloons can twist and pull in different directions as the air spreads inside them. That makes them look eager to zoom away.",
        )
    ],
    "kindness": [
        (
            "What does kindness do in a team?",
            "Kindness helps everyone feel included and brave enough to help. A kind team usually works better because people trust one another.",
        )
    ],
    "sharing": [
        (
            "Why is sharing a good way to lead?",
            "Sharing lets other people matter too. When everyone gets a turn, the job feels fair and happier.",
        )
    ],
    "apology": [
        (
            "Why can an apology fix hurt feelings?",
            "An apology shows that you noticed the hurt and want to do better. That can help another person feel seen and safe again.",
        )
    ],
    "helping": [
        (
            "Why does asking for help sometimes make a job easier?",
            "Some jobs really work better with two people. Asking kindly can turn a hard job into a teamwork job.",
        )
    ],
    "baby": [
        (
            "Why do babies need quiet sometimes?",
            "Babies often need quiet when they are sleepy or upset. Gentle sounds can feel much nicer to them than booming ones.",
        )
    ],
    "grandpa": [
        (
            "How can you cheer up an older person kindly?",
            "You can visit gently, bring a funny surprise, and pay attention to what feels comfortable for them. Kind cheering listens as well as performs.",
        )
    ],
    "neighbor": [
        (
            "What is a neighbor?",
            "A neighbor is someone who lives close to your home. Neighbors can help one another and share small acts of kindness.",
        )
    ],
    "quiet": [
        (
            "Why can a quiet joke still be funny?",
            "Funny things are not only loud things. Sometimes a tiny sound and a very silly sight make people laugh even more.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "baby",
    "grandpa",
    "neighbor",
    "quiet",
    "balloon",
    "dog",
    "giraffe",
    "rocket",
    "pump",
    "foot_pump",
    "breath",
    "drum",
    "bell",
    "kazoo",
    "kindness",
    "sharing",
    "apology",
    "helping",
]


def generation_prompts(world: World) -> list[str]:
    recipient_cfg: Recipient = world.facts["recipient_cfg"]
    balloon_cfg: BalloonSpec = world.facts["balloon_cfg"]
    band_cfg: BandItem = world.facts["band_cfg"]
    leader: Entity = world.facts["leader"]
    helper: Entity = world.facts["helper"]
    return [
        (
            f'Write a funny kindness story for a 3-to-5-year-old where {leader.label} calls {leader.pronoun("object")}self '
            f'the honcho of a tiny parade and tries to inflate {balloon_cfg.phrase} for {recipient_cfg.label}. '
            f'Include the words "pound", "inflate", and "honcho".'
        ),
        (
            f"Tell a comedy story where two children try to cheer up {recipient_cfg.label} with {band_cfg.phrase}, "
            f"but the self-appointed honcho gets too bossy and has to choose kindness before the parade can work."
        ),
        (
            f"Write a gentle story with a silly middle where {helper.label} feels left out, the balloon plan goes wobble-wrong, "
            f"and the ending proves that sharing the job matters more than acting important."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    recipient_cfg: Recipient = world.facts["recipient_cfg"]
    balloon_cfg: BalloonSpec = world.facts["balloon_cfg"]
    inflator_cfg: Inflator = world.facts["inflator_cfg"]
    band_cfg: BandItem = world.facts["band_cfg"]
    act_cfg: KindAct = world.facts["kindness_cfg"]
    leader: Entity = world.facts["leader"]
    helper: Entity = world.facts["helper"]
    mishap = world.facts.get("mishap", "none")

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.label} and {helper.label}, two children making a kindness parade for {recipient_cfg.label}. "
            f"Their plan matters because they are trying to cheer someone up, not just make noise.",
        ),
        (
            f"Why were they making a parade for {recipient_cfg.label}?",
            f"They knew that {recipient_cfg.label} {recipient_cfg.need}, so they wanted to bring a silly surprise. "
            f"The parade began as an act of kindness.",
        ),
        (
            f"What did {leader.label} do when {leader.pronoun('subject')} became the honcho?",
            f"{leader.label} put on the badge, acted very important, and even began to pound out a parade beat. "
            f"That made the game funny, but it also made {helper.label} feel small.",
        ),
    ]
    if mishap == "slip":
        qa.append(
            (
                "What went wrong on the first try with the balloon?",
                f"The balloon slipped loose and zipped around the hallway because the job needed more than one pair of hands. "
                f"{leader.label} was trying to do every part alone while {helper.label} felt left out.",
            )
        )
    elif mishap == "pop":
        qa.append(
            (
                "What went wrong on the first try with the balloon?",
                f"The balloon popped and bonked {leader.label} because the first try turned into flustered comedy instead of careful teamwork. "
                f"After the pop, the children still needed kindness to make the second try work.",
            )
        )
    elif mishap == "crooked_feeling":
        qa.append(
            (
                "Was the first try really a success?",
                f"The balloon held air, but the parade still felt wrong because the friendship part was wobbling. "
                f"A kind surprise is not ready yet if one child feels pushed aside.",
            )
        )
    else:
        qa.append(
            (
                "Why did they need a second try?",
                f"They needed a second try because the first one was too bossy and too messy to feel kind. "
                f"The children had to fix the teamwork before the parade could feel right.",
            )
        )
    qa.append(
        (
            f"How did {leader.label} fix the problem?",
            f"{leader.label} noticed that the kindness parade was not being kind, then changed course. "
            f"{act_cfg.ending}",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They brought the finished {balloon_cfg.label} to {recipient_cfg.label}, used the {band_cfg.label} gently, and got a laugh at last. "
            f"The ending proves the change because {leader.label} stopped acting like the only important person and shared the joy.",
        )
    )
    qa.append(
        (
            f"Why was {inflator_cfg.label} the right way to inflate the balloon?",
            f"It could give the balloon enough air to make the plan work. "
            f"In this story world, the tool has to match the balloon or the parade cannot honestly happen.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    recipient_cfg: Recipient = world.facts["recipient_cfg"]
    balloon_cfg: BalloonSpec = world.facts["balloon_cfg"]
    inflator_cfg: Inflator = world.facts["inflator_cfg"]
    band_cfg: BandItem = world.facts["band_cfg"]
    act_cfg: KindAct = world.facts["kindness_cfg"]

    tags = set(recipient_cfg.tags) | set(balloon_cfg.tags) | set(inflator_cfg.tags) | set(band_cfg.tags) | set(act_cfg.tags)
    tags.add("balloon")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
enough_air(B,I) :- balloon(B), inflator(I), air_need(B,N), power(I,P), P >= N.
gentle_for(R,Bd) :- recipient(R), band(Bd), noise_tolerance(R,T), loudness(Bd,L), L <= T.
valid(R,B,I,Bd) :- enough_air(B,I), gentle_for(R,Bd).

needs_pair(B) :- balloon(B), balloon_needs_helper(B).
easy_solo(B) :- balloon(B), not balloon_needs_helper(B).

#show valid/4.
#show needs_pair/1.
#show easy_solo/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, recipient in RECIPIENTS.items():
        lines.append(asp.fact("recipient", rid))
        lines.append(asp.fact("noise_tolerance", rid, recipient.noise_tolerance))
    for bid, balloon in BALLOONS.items():
        lines.append(asp.fact("balloon", bid))
        lines.append(asp.fact("air_need", bid, balloon.air_need))
        if balloon.needs_helper:
            lines.append(asp.fact("balloon_needs_helper", bid))
    for iid, inflator in INFLATORS.items():
        lines.append(asp.fact("inflator", iid))
        lines.append(asp.fact("power", iid, inflator.power))
    for band_id, band in BANDS.items():
        lines.append(asp.fact("band", band_id))
        lines.append(asp.fact("loudness", band_id, band.loudness))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_pair_flags() -> tuple[set[str], set[str]]:
    import asp

    model = asp.one_model(asp_program())
    needs_pair = {b for (b,) in asp.atoms(model, "needs_pair")}
    easy_solo = {b for (b,) in asp.atoms(model, "easy_solo")}
    return needs_pair, easy_solo


CURATED = [
    StoryParams(
        recipient="grandpa",
        balloon="giraffe",
        inflator="hand_pump",
        band="kazoo",
        kindness="share_title",
        leader_name="Lila",
        leader_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        grownup="mother",
    ),
    StoryParams(
        recipient="baby",
        balloon="dog",
        inflator="lungs",
        band="bell",
        kindness="hold_nozzle",
        leader_name="Milo",
        leader_gender="boy",
        helper_name="June",
        helper_gender="girl",
        grownup="father",
    ),
    StoryParams(
        recipient="neighbor",
        balloon="rocket",
        inflator="foot_pump",
        band="drum",
        kindness="apologize",
        leader_name="Nora",
        leader_gender="girl",
        helper_name="Toby",
        helper_gender="boy",
        grownup="mother",
    ),
    StoryParams(
        recipient="grandpa",
        balloon="rocket",
        inflator="foot_pump",
        band="kazoo",
        kindness="hold_nozzle",
        leader_name="Owen",
        leader_gender="boy",
        helper_name="Poppy",
        helper_gender="girl",
        grownup="father",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a silly kindness parade with a balloon, a honcho, and a better way to lead."
    )
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--balloon", choices=BALLOONS)
    ap.add_argument("--inflator", choices=INFLATORS)
    ap.add_argument("--band", choices=BANDS)
    ap.add_argument("--kindness", choices=KIND_ACTS)
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--leader-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.recipient and args.balloon and args.inflator and args.band:
        recipient = RECIPIENTS[args.recipient]
        balloon = BALLOONS[args.balloon]
        inflator = INFLATORS[args.inflator]
        band = BANDS[args.band]
        if not valid_combo(recipient, balloon, inflator, band):
            raise StoryError(explain_rejection(recipient, balloon, inflator, band))

    combos = [
        combo
        for combo in valid_combos()
        if (args.recipient is None or combo[0] == args.recipient)
        and (args.balloon is None or combo[1] == args.balloon)
        and (args.inflator is None or combo[2] == args.inflator)
        and (args.band is None or combo[3] == args.band)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    recipient, balloon, inflator, band = rng.choice(sorted(combos))
    kindness = args.kindness or rng.choice(sorted(KIND_ACTS))
    leader_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    leader_name = args.leader_name or _pick_name(rng, leader_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=leader_name)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(
        recipient=recipient,
        balloon=balloon,
        inflator=inflator,
        band=band,
        kindness=kindness,
        leader_name=leader_name,
        leader_gender=leader_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    if params.recipient not in RECIPIENTS:
        raise StoryError(f"(Unknown recipient: {params.recipient})")
    if params.balloon not in BALLOONS:
        raise StoryError(f"(Unknown balloon: {params.balloon})")
    if params.inflator not in INFLATORS:
        raise StoryError(f"(Unknown inflator: {params.inflator})")
    if params.band not in BANDS:
        raise StoryError(f"(Unknown band item: {params.band})")
    if params.kindness not in KIND_ACTS:
        raise StoryError(f"(Unknown kindness act: {params.kindness})")

    recipient = RECIPIENTS[params.recipient]
    balloon = BALLOONS[params.balloon]
    inflator = INFLATORS[params.inflator]
    band = BANDS[params.band]
    if not valid_combo(recipient, balloon, inflator, band):
        raise StoryError(explain_rejection(recipient, balloon, inflator, band))

    trait_rng = random.Random((params.seed or 0) + 17)
    world = tell(
        recipient_cfg=recipient,
        balloon_cfg=balloon,
        inflator_cfg=inflator,
        band_cfg=band,
        act_cfg=KIND_ACTS[params.kindness],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        grownup_type=params.grownup,
        leader_trait=trait_rng.choice(TRAITS),
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    asp_pair, asp_solo = asp_pair_flags()
    py_pair = {bid for bid, b in BALLOONS.items() if b.needs_helper}
    py_solo = {bid for bid, b in BALLOONS.items() if not b.needs_helper}
    if asp_pair == py_pair and asp_solo == py_solo:
        print("OK: helper-needed balloon facts match.")
    else:
        rc = 1
        print(f"MISMATCH in helper-needed facts: asp_pair={sorted(asp_pair)} py_pair={sorted(py_pair)}")

    smoke_cases: list[StoryParams] = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        for seed in range(5):
            params = resolve_params(default_args, random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
    except Exception as err:
        print(f"SMOKE setup failed: {err}")
        return 1

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if sample.world is None:
                raise StoryError("missing world")
            if i == 1:
                emit(sample, trace=False, qa=False, header="### smoke test")
        except Exception as err:
            print(f"SMOKE generation failed on case {i}: {err}")
            rc = 1
            break

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (recipient, balloon, inflator, band) combos:\n")
        for recipient, balloon, inflator, band in combos:
            print(f"  {recipient:9} {balloon:8} {inflator:10} {band}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader_name} & {p.helper_name}: {p.balloon} for {p.recipient} ({p.inflator}, {p.band})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
