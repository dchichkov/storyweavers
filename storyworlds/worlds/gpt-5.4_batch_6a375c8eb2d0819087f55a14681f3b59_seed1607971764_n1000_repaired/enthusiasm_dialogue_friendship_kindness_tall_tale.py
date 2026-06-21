#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/enthusiasm_dialogue_friendship_kindness_tall_tale.py
================================================================================

A standalone story world for a tall-tale flavored friendship story: two friends
notice a lonely child across an outsized bit of country and use cheerful
kindness, practical help, and plenty of dialogue to bring that child into their
day.

This world models:
- physical meters: loaded, moving, delivered, blocked
- emotional memes: enthusiasm, worry, trust, hope, belonging, friendship

The core reasonableness constraint is simple:
a kindness gift can be sent only by a delivery method that actually suits both
the place and the gift's physical needs.

Examples:
    python storyworlds/worlds/gpt-5.4/enthusiasm_dialogue_friendship_kindness_tall_tale.py
    python storyworlds/worlds/gpt-5.4/enthusiasm_dialogue_friendship_kindness_tall_tale.py --place creek --gift pie --method bridge_wagon
    python storyworlds/worlds/gpt-5.4/enthusiasm_dialogue_friendship_kindness_tall_tale.py --gift apple_basket --method kite_basket
    python storyworlds/worlds/gpt-5.4/enthusiasm_dialogue_friendship_kindness_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/enthusiasm_dialogue_friendship_kindness_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/enthusiasm_dialogue_friendship_kindness_tall_tale.py --verify
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    span: str
    detail: str
    approach: str
    meeting_spot: str
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
class Gift:
    id: str
    label: str
    phrase: str
    article: str
    cheer_line: str
    invitation_line: str
    fragile: bool = False
    heavy: bool = False
    upright: bool = False
    soft: bool = False
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
class Method:
    id: str
    label: str
    sense: int
    prep: str
    launch: str
    travel: str
    arrival: str
    reaches: set[str] = field(default_factory=set)
    protects_fragile: bool = False
    handles_heavy: bool = False
    keeps_upright: bool = False
    for_soft_only: bool = False
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return World(
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )
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


def method_fits(place: Place, gift: Gift, method: Method) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if place.id not in method.reaches:
        return False
    if gift.fragile and not method.protects_fragile:
        return False
    if gift.heavy and not method.handles_heavy:
        return False
    if gift.upright and not method.keeps_upright:
        return False
    if method.for_soft_only and not gift.soft:
        return False
    return True


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for gift_id, gift in GIFTS.items():
            for method_id, method in METHODS.items():
                if method_fits(place, gift, method):
                    combos.append((place_id, gift_id, method_id))
    return combos


def best_method_for(place: Place, gift: Gift) -> Optional[Method]:
    options = [m for m in sensible_methods() if method_fits(place, gift, m)]
    if not options:
        return None
    return max(options, key=lambda m: (m.sense, m.protects_fragile, m.handles_heavy, m.keeps_upright))


def _r_depart(world: World) -> list[str]:
    gift = world.get("gift")
    method = world.get("method")
    if gift.meters["loaded"] < THRESHOLD:
        return []
    sig = ("depart",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    method.meters["moving"] += 1
    return []


def _r_arrive(world: World) -> list[str]:
    method = world.get("method")
    gift = world.get("gift")
    if method.meters["moving"] < THRESHOLD:
        return []
    sig = ("arrive",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts.get("compatible"):
        gift.meters["delivered"] += 1
    else:
        gift.meters["blocked"] += 1
    return []


def _r_cheer(world: World) -> list[str]:
    gift = world.get("gift")
    recipient = world.get("recipient")
    starter = world.get("starter")
    helper = world.get("helper")
    if gift.meters["delivered"] < THRESHOLD:
        return []
    sig = ("cheer",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    recipient.memes["hope"] += 1
    recipient.memes["belonging"] += 1
    recipient.memes["friendship"] += 1
    starter.memes["friendship"] += 1
    helper.memes["friendship"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="depart", tag="physical", apply=_r_depart),
    Rule(name="arrive", tag="physical", apply=_r_arrive),
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
            world.say(sent)
    return produced


def predict_delivery(world: World) -> dict[str, bool]:
    sim = world.copy()
    sim.get("gift").meters["loaded"] += 1
    propagate(sim, narrate=False)
    return {
        "delivered": sim.get("gift").meters["delivered"] >= THRESHOLD,
        "blocked": sim.get("gift").meters["blocked"] >= THRESHOLD,
    }


def introduce(world: World, starter: Entity, helper: Entity, place: Place) -> None:
    starter.memes["enthusiasm"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"In a town where fence posts grew so tall they had to duck under the moon, "
        f"{starter.id} and {helper.id} were the sort of friends who could make an ordinary "
        f"afternoon feel as big as a parade."
    )
    world.say(
        f"{starter.id} had enough enthusiasm to shake dust from the church bell, "
        f"and {helper.id} had the calm hands that kept grand ideas from tipping sideways."
    )
    world.say(
        f"That day they were near {place.label}, where {place.detail}"
    )


def spot_lonely(world: World, starter: Entity, helper: Entity, recipient: Entity, place: Place) -> None:
    recipient.memes["lonely"] += 1
    world.say(
        f"Across {place.span}, they spotted {recipient.id}, the new child in town, "
        f"standing alone by {place.approach}."
    )
    world.say(
        f'"Do you see {recipient.pronoun("object")}?" {starter.id} asked. '
        f'"{recipient.id} looks like {recipient.pronoun()} could use a friendly hello."'
    )
    world.say(
        f'"Then let\'s send one that is warm and true," said {helper.id}. '
        f'"Kindness travels farther when two friends carry it together."'
    )


def choose_gift(world: World, starter: Entity, helper: Entity, gift: Gift, recipient: Entity) -> None:
    starter.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f'{starter.id} clapped {starter.pronoun("possessive")} hands. '
        f'"We can send {gift.article} {gift.label}, and a note that says, '
        f'\'{gift.invitation_line}\'"'
    )
    world.say(
        f'"And we should make it feel welcoming," said {helper.id}. '
        f'"{gift.cheer_line}"'
    )
    world.facts["gift_message"] = gift.invitation_line
    world.facts["gift_cheer"] = gift.cheer_line
    world.facts["recipient_seen_alone"] = recipient.id


def plan(world: World, starter: Entity, helper: Entity, place: Place, gift: Gift, method: Method) -> None:
    pred = predict_delivery(world)
    helper.memes["worry"] += 1
    if not pred["delivered"]:
        raise StoryError("(No story: this delivery plan would not get the kindness across.)")
    starter.memes["trust"] += 1
    helper.memes["trust"] += 1
    need_bits: list[str] = []
    if gift.fragile:
        need_bits.append("keep it from bumping")
    if gift.heavy:
        need_bits.append("carry the weight")
    if gift.upright:
        need_bits.append("keep it standing straight")
    if method.for_soft_only:
        need_bits.append("use something light and soft")
    need_text = ""
    if need_bits:
        need_text = " We needed a method that could " + ", ".join(need_bits) + "."
    world.say(
        f'"How do we get it across {place.span}?" asked {starter.id}.'
    )
    world.say(
        f'"With {method.label}," said {helper.id}. "{method.prep}.{need_text} '
        f'This one truly suits {gift.article} {gift.label}."'
    )
    world.facts["predicted_success"] = pred["delivered"]


def prepare(world: World, starter: Entity, helper: Entity, gift: Gift, method: Method) -> None:
    gift_ent = world.get("gift")
    method_ent = world.get("method")
    starter.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"So the two friends worked side by side. {method.prep.capitalize()}, and "
        f"{starter.id} tucked in the note while {helper.id} checked every knot and wheel twice."
    )
    gift_ent.meters["loaded"] += 1
    method_ent.meters["ready"] += 1


def send_kindness(world: World, starter: Entity, helper: Entity, place: Place, method: Method, gift: Gift) -> None:
    propagate(world, narrate=False)
    world.say(
        f'"Ready?" asked {helper.id}.'
    )
    world.say(
        f'"Ready enough to wake the daisies," said {starter.id}.'
    )
    world.say(method.launch)
    world.say(
        f"{method.travel} Across {place.span}, the little gift looked as brave as a lantern in the dusk."
    )
    if world.get("gift").meters["delivered"] < THRESHOLD:
        raise StoryError("(No story: the delivery failed after launch.)")
    world.say(method.arrival)
    world.facts["delivered"] = True


def receive(world: World, recipient: Entity, gift: Gift) -> None:
    recipient.memes["lonely"] = 0.0
    world.say(
        f"{recipient.id} opened the note, looked at {gift.article} {gift.label}, and smiled so wide "
        f"it could have made room for another sunrise."
    )
    world.say(
        f'"For me?" {recipient.pronoun().capitalize()} called. "For me!"'
    )


def invite(world: World, starter: Entity, helper: Entity, recipient: Entity, place: Place) -> None:
    world.say(
        f'"Yes for you!" shouted {starter.id}. "Come meet us at {place.meeting_spot}!"'
    )
    world.say(
        f'"And bring your smile," added {helper.id}. "There is always space for one more friend."'
    )
    recipient.memes["trust"] += 1


def join_and_end(world: World, starter: Entity, helper: Entity, recipient: Entity, gift: Gift, place: Place) -> None:
    starter.memes["joy"] += 1
    helper.memes["joy"] += 1
    recipient.memes["joy"] += 1
    world.say(
        f"Before long, {recipient.id} came hurrying over toward {place.meeting_spot}, holding "
        f"{gift.article} {gift.label} carefully and laughing all the way."
    )
    world.say(
        f"The three children sat together, shared the gift and the note, and talked until the shadows "
        f"grew long enough to tie themselves in knots."
    )
    world.say(
        f"After that, whenever anyone in town felt left out, people would say, "
        f'"Find {starter.id} and {helper.id}. Their friendship can carry kindness across anything."'
    )


def tell(
    place: Place,
    gift: Gift,
    method: Method,
    starter_name: str,
    starter_gender: str,
    helper_name: str,
    helper_gender: str,
    recipient_name: str,
    recipient_gender: str,
) -> World:
    world = World()
    starter = world.add(Entity(id=starter_name, kind="character", type=starter_gender, role="starter"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    recipient = world.add(Entity(id=recipient_name, kind="character", type=recipient_gender, role="recipient"))
    world.add(Entity(id="gift", kind="thing", type="gift", label=gift.label))
    world.add(Entity(id="method", kind="thing", type="method", label=method.label))

    world.facts["compatible"] = method_fits(place, gift, method)
    world.facts["place"] = place
    world.facts["gift_cfg"] = gift
    world.facts["method_cfg"] = method
    world.facts["starter"] = starter
    world.facts["helper"] = helper
    world.facts["recipient"] = recipient

    introduce(world, starter, helper, place)
    spot_lonely(world, starter, helper, recipient, place)

    world.para()
    choose_gift(world, starter, helper, gift, recipient)
    plan(world, starter, helper, place, gift, method)

    world.para()
    prepare(world, starter, helper, gift, method)
    send_kindness(world, starter, helper, place, method, gift)
    receive(world, recipient, gift)
    invite(world, starter, helper, recipient, place)

    world.para()
    join_and_end(world, starter, helper, recipient, gift, place)
    world.facts["outcome"] = "delivered"
    return world


PLACES = {
    "creek": Place(
        id="creek",
        label="the singing creek",
        span="the singing creek",
        detail="the water ran so bright and quick that even the minnows seemed in a hurry",
        approach="a smooth blue stone",
        meeting_spot="the willow bridge",
        tags={"creek"},
    ),
    "windy_field": Place(
        id="windy_field",
        label="the windy field",
        span="the windy field",
        detail="the grass bowed and swayed as if the whole meadow were practicing manners",
        approach="a fence post taller than a wagon",
        meeting_spot="the painted gate",
        tags={"field", "wind"},
    ),
    "snowy_hill": Place(
        id="snowy_hill",
        label="the snowy hill",
        span="the snowy hill",
        detail="the drifts were piled so high they looked like whipped cream for giants",
        approach="a red sled mark in the snow",
        meeting_spot="the warm bakery porch",
        tags={"snow", "hill"},
    ),
}

GIFTS = {
    "pie": Gift(
        id="pie",
        label="berry pie",
        phrase="a berry pie",
        article="a",
        cheer_line="The sweet smell alone might tell someone they are welcome.",
        invitation_line="Please come share the afternoon with us.",
        fragile=True,
        tags={"pie", "food"},
    ),
    "scarf": Gift(
        id="scarf",
        label="red scarf",
        phrase="a red scarf",
        article="a",
        cheer_line="A bright scarf can feel like a hug before you even wrap it on.",
        invitation_line="Please come stand with us and be our friend.",
        soft=True,
        tags={"scarf", "warmth"},
    ),
    "seedling": Gift(
        id="seedling",
        label="sunflower seedling",
        phrase="a sunflower seedling in a little pot",
        article="a",
        cheer_line="A growing thing says tomorrow can be brighter than today.",
        invitation_line="Please come plant this with us and stay awhile.",
        upright=True,
        tags={"flower", "garden"},
    ),
    "apple_basket": Gift(
        id="apple_basket",
        label="basket of apples",
        phrase="a basket of shiny apples",
        article="a",
        cheer_line="A full basket is kinder when more hands reach into it.",
        invitation_line="Please come share these apples with us.",
        heavy=True,
        tags={"apples", "food"},
    ),
}

METHODS = {
    "bridge_wagon": Method(
        id="bridge_wagon",
        label="the bridge wagon",
        sense=3,
        prep="we can roll it over the old plank bridge in the steadiest wagon in town",
        launch="The wagon rolled forward with a creak as proud as a marching band.",
        travel="Its wheels hummed over the boards without a single silly bounce.",
        arrival="It reached the far side neat and safe, as if it had practiced all morning.",
        reaches={"creek", "windy_field"},
        protects_fragile=True,
        handles_heavy=True,
        keeps_upright=True,
        tags={"wagon", "bridge"},
    ),
    "kite_basket": Method(
        id="kite_basket",
        label="the kite basket",
        sense=3,
        prep="we can tie it into the little basket under my giant blue kite",
        launch="Up went the kite, tugging at the sky like it meant to borrow a cloud.",
        travel="The kite sailed high and steady, with the basket dangling below like a careful pocket.",
        arrival="It dipped down beside the waiting child as gently as a leaf settling on a pond.",
        reaches={"creek", "windy_field"},
        for_soft_only=True,
        tags={"kite", "wind"},
    ),
    "sled": Method(
        id="sled",
        label="the cedar sled",
        sense=3,
        prep="we can tuck it onto the cedar sled and guide it down the packed snow path",
        launch="Off slid the cedar sled, smooth and shining, with hardly a wobble to its name.",
        travel="It skimmed over the snow in one long silver whisper.",
        arrival="The sled stopped by the porch as softly as if winter itself had set it there by hand.",
        reaches={"snowy_hill"},
        protects_fragile=True,
        handles_heavy=True,
        keeps_upright=True,
        tags={"sled", "snow"},
    ),
    "slingshot": Method(
        id="slingshot",
        label="the town slingshot",
        sense=1,
        prep="we could never honestly send kindness by flinging it through the air",
        launch="Nobody launched anything, because this was not a sensible plan.",
        travel="",
        arrival="",
        reaches={"creek", "windy_field"},
        tags={"slingshot"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tessa", "Nell", "Ruby", "Ada", "Mabel", "June"]
BOY_NAMES = ["Eli", "Owen", "Finn", "Cal", "Jasper", "Theo", "Milo", "Ben"]
TRAITS = ["cheerful", "steady", "curious", "kind", "brave"]


@dataclass
class StoryParams:
    place: str
    gift: str
    method: str
    starter_name: str
    starter_gender: str
    helper_name: str
    helper_gender: str
    recipient_name: str
    recipient_gender: str
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


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    gift = world.facts["gift_cfg"]
    starter = world.facts["starter"]
    helper = world.facts["helper"]
    return [
        f'Write a tall-tale story for a young child that includes the word "enthusiasm", '
        f'features dialogue, friendship, and kindness, and has two friends sending {gift.phrase} across {place.span}.',
        f"Tell a warm tall tale where {starter.id} and {helper.id} notice a lonely new child and work together to send a kind gift and an invitation.",
        f"Write a playful story with big exaggeration and gentle dialogue, ending with a new friendship formed because kindness traveled farther than expected.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    starter = world.facts["starter"]
    helper = world.facts["helper"]
    recipient = world.facts["recipient"]
    place = world.facts["place"]
    gift = world.facts["gift_cfg"]
    method = world.facts["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the main friends in the story?",
            f"The main friends are {starter.id} and {helper.id}. They worked as a team, because {starter.id} brought bright enthusiasm and {helper.id} helped choose a careful plan.",
        ),
        (
            f"Why did {starter.id} and {helper.id} decide to send {gift.phrase}?",
            f"They saw {recipient.id} standing alone across {place.span}, and they wanted the new child to feel welcome. Their gift was a kind way to say, in action, that there was room for one more friend.",
        ),
        (
            f"Why did they use {method.label}?",
            f"They used {method.label} because it truly suited {gift.article} {gift.label} and the place it had to cross. That careful choice let the gift arrive safely instead of turning kindness into a muddle.",
        ),
        (
            f"What changed for {recipient.id} by the end?",
            f"At first {recipient.id} was alone, but by the end {recipient.pronoun()} was hurrying over to join the other children. The delivered gift and friendly invitation made {recipient.pronoun('object')} feel wanted, so loneliness turned into belonging.",
        ),
        (
            "How does the story show friendship and kindness together?",
            f"It shows them together because the two friends did not only feel sorry for someone far away; they acted together to help. Their shared plan, their dialogue, and their invitation turned kindness into a real friendship.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "creek": [
        (
            "What is a creek?",
            "A creek is a small stream of moving water. If it is too wide or too fast to step across, people need a safe way to carry things over it.",
        )
    ],
    "wind": [
        (
            "What does wind do to light things?",
            "Wind can lift and push light things through the air. That can help when you use something like a kite, but only if the thing hanging below is light and soft enough.",
        )
    ],
    "snow": [
        (
            "Why does a sled work well on snow?",
            "A sled slides over packed snow with very little rubbing. That makes it a good way to carry things downhill smoothly.",
        )
    ],
    "pie": [
        (
            "Why does a pie need careful carrying?",
            "A pie is soft and easy to squash or tip. If it gets bumped too much, the filling can spill and the crust can break.",
        )
    ],
    "scarf": [
        (
            "Why is a scarf easy to send?",
            "A scarf is light and soft, so it can be folded and carried without breaking. That makes it easier to move than something heavy or crumbly.",
        )
    ],
    "flower": [
        (
            "Why does a seedling need to stay upright?",
            "A seedling is a young plant with tender roots and stem. If it tips over too much, the dirt can spill and the plant can get hurt.",
        )
    ],
    "apples": [
        (
            "Why is a basket of apples harder to carry than one scarf?",
            "A basket of apples is much heavier than one scarf because it holds many pieces of fruit at once. Heavy things need a strong, steady way to move them.",
        )
    ],
    "wagon": [
        (
            "What is a wagon good for?",
            "A wagon is good for carrying things along the ground in a steady way. Its wheels help move heavy or delicate things without asking one person to hold all the weight.",
        )
    ],
    "kite": [
        (
            "How can a kite carry something small?",
            "A big kite can lift a very light bundle if the wind is steady and the string is strong. It is only for little, soft things, not for heavy baskets or messy food.",
        )
    ],
    "sled": [
        (
            "What is a sled made to do?",
            "A sled is made to slide over snow. It can carry people or bundles smoothly when the ground is cold and slippery.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, welcome, or comfort someone in a gentle way. Sometimes a small kind act changes how a person feels for the whole day.",
        )
    ],
    "friendship": [
        (
            "How can friendship start?",
            "Friendship can start with a warm welcome, a shared game, or a kind invitation. When people feel safe and wanted, it becomes easier to trust and join in.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "creek",
    "wind",
    "snow",
    "pie",
    "scarf",
    "flower",
    "apples",
    "wagon",
    "kite",
    "sled",
    "kindness",
    "friendship",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    gift = world.facts["gift_cfg"]
    method = world.facts["method_cfg"]
    tags = set(place.tags) | set(gift.tags) | set(method.tags) | {"kindness", "friendship"}
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="creek",
        gift="pie",
        method="bridge_wagon",
        starter_name="Lila",
        starter_gender="girl",
        helper_name="Eli",
        helper_gender="boy",
        recipient_name="Mabel",
        recipient_gender="girl",
    ),
    StoryParams(
        place="windy_field",
        gift="scarf",
        method="kite_basket",
        starter_name="Theo",
        starter_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        recipient_name="Owen",
        recipient_gender="boy",
    ),
    StoryParams(
        place="snowy_hill",
        gift="seedling",
        method="sled",
        starter_name="June",
        starter_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        recipient_name="Ada",
        recipient_gender="girl",
    ),
    StoryParams(
        place="creek",
        gift="apple_basket",
        method="bridge_wagon",
        starter_name="Cal",
        starter_gender="boy",
        helper_name="Nell",
        helper_gender="girl",
        recipient_name="Milo",
        recipient_gender="boy",
    ),
]


def explain_rejection(place: Place, gift: Gift, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it is too foolish for a kindness story. "
            f"A tall tale can be grand, but the helping plan should still make sense.)"
        )
    if place.id not in method.reaches:
        return (
            f"(No story: {method.label} does not suit {place.span}. "
            f"Pick a method that can honestly reach that place.)"
        )
    if gift.fragile and not method.protects_fragile:
        return (
            f"(No story: {gift.phrase} is fragile, and {method.label} would bump or squash it. "
            f"Choose a steadier method.)"
        )
    if gift.heavy and not method.handles_heavy:
        return (
            f"(No story: {gift.phrase} is too heavy for {method.label}. "
            f"Choose something strong enough to carry the weight.)"
        )
    if gift.upright and not method.keeps_upright:
        return (
            f"(No story: {gift.phrase} needs to stay upright, and {method.label} would not keep it straight.)"
        )
    if method.for_soft_only and not gift.soft:
        return (
            f"(No story: {method.label} is only for light, soft gifts, and {gift.phrase} is not one of those.)"
        )
    return "(No story: this place, gift, and method do not make a reasonable combination.)"


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

needs_fragile(G) :- gift(G), fragile(G).
needs_heavy(G) :- gift(G), heavy(G).
needs_upright(G) :- gift(G), upright(G).
needs_soft(G) :- gift(G), soft(G).

fits(P, G, M) :- place(P), gift(G), method(M),
                 sensible_method(M),
                 reaches(M, P),
                 not needs_fragile(G).
fits(P, G, M) :- place(P), gift(G), method(M),
                 sensible_method(M),
                 reaches(M, P),
                 needs_fragile(G), protects_fragile(M),
                 not needs_heavy(G), not needs_upright(G), not needs_soft(G).
fits(P, G, M) :- place(P), gift(G), method(M),
                 sensible_method(M),
                 reaches(M, P),
                 needs_heavy(G), handles_heavy(M),
                 not needs_fragile(G), not needs_upright(G), not needs_soft(G).
fits(P, G, M) :- place(P), gift(G), method(M),
                 sensible_method(M),
                 reaches(M, P),
                 needs_upright(G), keeps_upright(M),
                 not needs_fragile(G), not needs_heavy(G), not needs_soft(G).
fits(P, G, M) :- place(P), gift(G), method(M),
                 sensible_method(M),
                 reaches(M, P),
                 needs_soft(G), soft_only(M),
                 not needs_fragile(G), not needs_heavy(G), not needs_upright(G).

fits(P, G, M) :- place(P), gift(G), method(M),
                 sensible_method(M), reaches(M, P),
                 needs_fragile(G), protects_fragile(M),
                 needs_heavy(G), handles_heavy(M),
                 not needs_upright(G), not needs_soft(G).
fits(P, G, M) :- place(P), gift(G), method(M),
                 sensible_method(M), reaches(M, P),
                 needs_fragile(G), protects_fragile(M),
                 needs_upright(G), keeps_upright(M),
                 not needs_heavy(G), not needs_soft(G).
fits(P, G, M) :- place(P), gift(G), method(M),
                 sensible_method(M), reaches(M, P),
                 needs_heavy(G), handles_heavy(M),
                 needs_upright(G), keeps_upright(M),
                 not needs_fragile(G), not needs_soft(G).

valid(P, G, M) :- fits(P, G, M).
outcome(delivered) :- chosen(P, G, M), valid(P, G, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        if gift.fragile:
            lines.append(asp.fact("fragile", gift_id))
        if gift.heavy:
            lines.append(asp.fact("heavy", gift_id))
        if gift.upright:
            lines.append(asp.fact("upright", gift_id))
        if gift.soft:
            lines.append(asp.fact("soft", gift_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for place_id in sorted(method.reaches):
            lines.append(asp.fact("reaches", method_id, place_id))
        if method.protects_fragile:
            lines.append(asp.fact("protects_fragile", method_id))
        if method.handles_heavy:
            lines.append(asp.fact("handles_heavy", method_id))
        if method.keeps_upright:
            lines.append(asp.fact("keeps_upright", method_id))
        if method.for_soft_only:
            lines.append(asp.fact("soft_only", method_id))
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

    model = asp.one_model(asp_program("", "#show sensible_method/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen", params.place, params.gift, params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: enthusiasm, dialogue, friendship, and kindness carried across a big place."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name not in avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.gift and args.method:
        place = PLACES[args.place]
        gift = GIFTS[args.gift]
        method = METHODS[args.method]
        if not method_fits(place, gift, method):
            raise StoryError(explain_rejection(place, gift, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.gift is None or combo[1] == args.gift)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, gift_id, method_id = rng.choice(sorted(combos))
    starter_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    recipient_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    starter_name = _pick_name(rng, starter_gender, used)
    used.add(starter_name)
    helper_name = _pick_name(rng, helper_gender, used)
    used.add(helper_name)
    recipient_name = _pick_name(rng, recipient_gender, used)
    return StoryParams(
        place=place_id,
        gift=gift_id,
        method=method_id,
        starter_name=starter_name,
        starter_gender=starter_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        recipient_name=recipient_name,
        recipient_gender=recipient_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    place = PLACES[params.place]
    gift = GIFTS[params.gift]
    method = METHODS[params.method]
    if not method_fits(place, gift, method):
        raise StoryError(explain_rejection(place, gift, method))

    world = tell(
        place=place,
        gift=gift,
        method=method,
        starter_name=params.starter_name,
        starter_gender=params.starter_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        recipient_name=params.recipient_name,
        recipient_gender=params.recipient_gender,
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

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_sensible = {m.id for m in sensible_methods()}
    clingo_sensible = set(asp_sensible_methods())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible methods match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  python:", sorted(python_sensible))
        print("  clingo:", sorted(clingo_sensible))

    cases = list(CURATED)
    for seed in range(50):
        params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        asp_result = asp_outcome(params)
        py_result = "delivered" if (params.place, params.gift, params.method) in python_valid else "?"
        if asp_result != py_result:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit ran.")
    except Exception as exc:  # pragma: no cover - verification path only
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_method/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        print(f"{len(combos)} valid (place, gift, method) combos:\n")
        for place_id, gift_id, method_id in combos:
            print(f"  {place_id:12} {gift_id:12} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.starter_name}, {p.helper_name}, and {p.recipient_name}: {p.gift} via {p.method} across {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
