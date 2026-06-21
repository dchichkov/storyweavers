#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/payment_russian_emu_twist_myth.py
============================================================

A small myth-shaped storyworld about a village that leaves a fearful payment for
a supposed russian spirit at the edge of the fields. A child follows the signs,
finds the feared visitor, and discovers the twist: the monster is really an emu
in trouble. The ending depends on whether the child brings the kind of help the
creature actually needs, and whether that help comes in time.

Run it
------
python storyworlds/worlds/gpt-5.4/payment_russian_emu_twist_myth.py
python storyworlds/worlds/gpt-5.4/payment_russian_emu_twist_myth.py --need hungry --help grain_bowl
python storyworlds/worlds/gpt-5.4/payment_russian_emu_twist_myth.py --sign hoofprints
python storyworlds/worlds/gpt-5.4/payment_russian_emu_twist_myth.py --all
python storyworlds/worlds/gpt-5.4/payment_russian_emu_twist_myth.py --qa --json
python storyworlds/worlds/gpt-5.4/payment_russian_emu_twist_myth.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    ending: str
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
class Rumor:
    id: str
    title: str
    whisper: str
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
class Sign:
    id: str
    label: str
    clue: str
    reveals_emu: bool
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
class Need:
    id: str
    state: str
    hint: str
    remedy: str
    failure: str
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
class Help:
    id: str
    label: str
    phrase: str
    fixes: str
    action: str
    fail_action: str
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
class Payment:
    id: str
    label: str
    phrase: str
    gleam: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
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


def _r_distress_fear(world: World) -> list[str]:
    emu = world.get("emu")
    child = world.get("child")
    if emu.meters["distress"] < THRESHOLD:
        return []
    sig = ("fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    return []


def _r_help_soothes(world: World) -> list[str]:
    emu = world.get("emu")
    child = world.get("child")
    if emu.meters["comfort"] < THRESHOLD:
        return []
    sig = ("soothe",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    emu.meters["distress"] = 0.0
    emu.memes["trust"] += 1
    child.memes["wonder"] += 1
    return []


RULES = [
    Rule(name="distress_fear", apply=_r_distress_fear),
    Rule(name="help_soothes", apply=_r_help_soothes),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
    if narrate:
        for line in out:
            world.say(line)
    return out


def sign_matches_emu(sign: Sign) -> bool:
    return sign.reveals_emu


def help_matches_need(need: Need, help_item: Help) -> bool:
    return need.id == help_item.fixes


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for rumor_id in RUMORS:
            for sign_id, sign in SIGNS.items():
                if not sign_matches_emu(sign):
                    continue
                for need_id, need in NEEDS.items():
                    for help_id, help_item in HELPS.items():
                        if help_matches_need(need, help_item):
                            combos.append((place_id, rumor_id, sign_id, need_id, help_id))
    return combos


def explain_sign(sign: Sign) -> str:
    return (
        f"(No story: {sign.label} do not point to an emu, so the twist cannot land. "
        f"Pick a sign such as tracks, feathers, or a booming cry.)"
    )


def explain_help(need: Need, help_item: Help) -> str:
    return (
        f"(No story: {help_item.label} would not truly help a creature that is {need.state}. "
        f"The child needs the right kind of care, not just any brave gesture.)"
    )


def outcome_of(params: "StoryParams") -> str:
    if params.delay >= 2:
        return "departed"
    return "soothed" if help_matches_need(NEEDS[params.need], HELPS[params.help]) else "departed"


def discover_truth(world: World) -> None:
    emu = world.get("emu")
    rumor = world.facts["rumor"]
    sign = world.facts["sign"]
    child = world.get("child")
    child.memes["wonder"] += 1
    world.say(
        f"When {child.id} came close enough to see clearly, the feared {rumor.title.lower()} "
        f"was not a spirit at all. It was an emu, tall as a barley sheaf, with {sign.clue} "
        f"and a strip of blue cloth from an old russian trader's cart caught around one leg."
    )
    emu.memes["revealed"] += 1


def introduce(world: World, place: Place, rumor: Rumor, payment: Payment, child: Entity, elder: Entity) -> None:
    child.memes["duty"] += 1
    world.say(
        f"In the old days, when stories still slept in stones, the people of the valley feared "
        f"{rumor.whisper}. At each new moon they carried a payment to {place.phrase}, lest the night "
        f"guest cross the fields."
    )
    world.say(
        f"One dusk {elder.label_word} placed {payment.phrase} in {child.id}'s hands. "
        f"The {payment.label} gave off {payment.gleam}, and the child felt both proud and small."
    )


def path_sign(world: World, child: Entity, place: Place, sign: Sign) -> None:
    world.say(
        f"{child.id} climbed toward {place.phrase}, where the wind moved slowly and every sound felt older "
        f"than daylight. There {child.pronoun()} found {sign.clue}, and the old fear of the village stirred again."
    )


def predict_need(world: World, need: Need) -> None:
    world.facts["predicted_need"] = need.id
    world.say(
        f"But beneath the fear, another truth peeped through. The creature did not wait like a collector of coins; "
        f"it looked {need.state}, and the air around it seemed to ask for {need.remedy}."
    )


def offer_payment(world: World, child: Entity, payment: Payment) -> None:
    child.memes["fear"] += 1
    world.say(
        f"{child.id} held out the payment first, because that was what the grown-ups had always done. "
        f"The {payment.label} shone in {child.pronoun('possessive')} palm, but the creature did not reach for it."
    )


def help_creature(world: World, help_item: Help) -> None:
    emu = world.get("emu")
    emu.meters["comfort"] += 1
    world.say(help_item.action)


def fail_help(world: World, help_item: Help, need: Need) -> None:
    emu = world.get("emu")
    emu.meters["distress"] += 1
    world.say(
        f"{help_item.fail_action} Yet it was the wrong gift for a creature that was {need.state}, "
        f"and the emu's great eyes stayed troubled."
    )


def ending_soothed(world: World, place: Place, payment: Payment, help_item: Help, elder: Entity) -> None:
    child = world.get("child")
    emu = world.get("emu")
    world.say(
        f"Then the emu lowered its long neck and accepted {help_item.phrase}. Its harsh, hollow cry softened, "
        f"and the valley's fear broke like thin ice in spring."
    )
    world.say(
        f"{child.id} carried the untouched payment home. From that night on, {elder.label_word} taught that tribute "
        f"belongs to cruel kings, but hungry or thirsty creatures ask for kindness. {place.ending}"
    )
    world.facts["lesson"] = "care_over_payment"
    emu.meters["calm"] += 1


def ending_departed(world: World, place: Place, need: Need, elder: Entity) -> None:
    child = world.get("child")
    emu = world.get("emu")
    emu.meters["distance"] += 1
    world.say(
        f"With a drumming of feet, the emu turned away and ran into the dark reeds before anyone could mend the mistake. "
        f"{need.failure}"
    )
    world.say(
        f"{child.id} went back with empty hands and a heavier heart. After that, {elder.label_word} said that fear can make "
        f"people call every stranger a monster, and payment is a poor answer when a living thing needs care."
    )
    world.facts["lesson"] = "fear_blinds"


def tell(
    *,
    place: Place,
    rumor: Rumor,
    sign: Sign,
    need: Need,
    help_item: Help,
    payment: Payment,
    child_name: str,
    child_gender: str,
    elder_type: str,
    delay: int,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder"))
    emu = world.add(Entity(id="emu", kind="thing", type="emu", label="the emu"))
    emu.meters["distress"] = 1.0
    child.memes["fear"] = 0.0
    child.memes["wonder"] = 0.0
    world.facts.update(
        place=place,
        rumor=rumor,
        sign=sign,
        need=need,
        help=help_item,
        payment=payment,
        delay=delay,
        child=child,
        elder=elder,
        emu=emu,
    )
    propagate(world, narrate=False)

    introduce(world, place, rumor, payment, child, elder)
    world.para()
    path_sign(world, child, place, sign)
    discover_truth(world)
    predict_need(world, need)
    world.para()
    offer_payment(world, child, payment)

    if delay >= 2:
        fail_help(world, help_item, need)
        ending_departed(world, place, need, elder)
        world.facts["outcome"] = "departed"
        return world

    if help_matches_need(need, help_item):
        help_creature(world, help_item)
        propagate(world, narrate=False)
        world.para()
        ending_soothed(world, place, payment, help_item, elder)
        world.facts["outcome"] = "soothed"
    else:
        fail_help(world, help_item, need)
        world.para()
        ending_departed(world, place, need, elder)
        world.facts["outcome"] = "departed"
    return world


KNOWLEDGE = {
    "emu": [
        (
            "What is an emu?",
            "An emu is a very large bird with long legs and a long neck. It cannot fly, but it can run very fast."
        )
    ],
    "payment": [
        (
            "What is a payment?",
            "A payment is something given to settle a debt or buy something. In stories, people sometimes wrongly treat it like a magic answer to fear."
        )
    ],
    "russian": [
        (
            "What does russian mean in this story?",
            "Russian means something connected to Russia or to people from there. Here it is part of an old rumor the villagers repeat."
        )
    ],
    "grain": [
        (
            "Why would grain help a bird?",
            "Many birds eat seeds and grain for food. Giving food can help a hungry bird regain strength."
        )
    ],
    "water": [
        (
            "Why does water help a thirsty animal?",
            "Water helps a thirsty body work properly again. Animals need it to stay alive and strong."
        )
    ],
    "blanket": [
        (
            "How can a blanket help a cold creature?",
            "A blanket can trap warmth around a body. That helps a cold creature stop losing heat so fast."
        )
    ],
}
KNOWLEDGE_ORDER = ["payment", "russian", "emu", "grain", "water", "blanket"]


PLACES = {
    "ford": Place(
        id="ford",
        label="ford",
        phrase="the moonlit ford",
        ending="At the moonlit ford, people now left bowls of water for birds and grain for small creatures, and no one bowed to shadows there again.",
        tags={"water"},
    ),
    "hill": Place(
        id="hill",
        label="hill shrine",
        phrase="the hill shrine of white stones",
        ending="On the hill shrine, children began tying bright ribbons instead of fear-knots, and the place sounded more like laughter than prayer.",
        tags={"blanket"},
    ),
    "reedbank": Place(
        id="reedbank",
        label="reedbank",
        phrase="the reedbank by the slow river",
        ending="By the reedbank, elders taught the names of tracks and feathers, so guessing gave way to seeing.",
        tags={"water"},
    ),
}

RUMORS = {
    "collector": Rumor(
        id="collector",
        title="Russian Collector of the Marsh",
        whisper="a russian collector who came for moon-payments",
        tags={"russian", "payment"},
    ),
    "rider": Rumor(
        id="rider",
        title="Russian Rider of the Reeds",
        whisper="a russian rider with iron steps and a taxman's shadow",
        tags={"russian"},
    ),
    "duke": Rumor(
        id="duke",
        title="Russian Duke of the Night Path",
        whisper="a russian duke who counted every barn and field",
        tags={"russian"},
    ),
}

SIGNS = {
    "tracks": Sign(
        id="tracks",
        label="three-toed tracks",
        clue="three-toed tracks pressed deep into the mud",
        reveals_emu=True,
        tags={"emu"},
    ),
    "feathers": Sign(
        id="feathers",
        label="big gray feathers",
        clue="big gray feathers caught in the thornbushes",
        reveals_emu=True,
        tags={"emu"},
    ),
    "cry": Sign(
        id="cry",
        label="booming cry",
        clue="a booming cry that sounded more lonely than wicked",
        reveals_emu=True,
        tags={"emu"},
    ),
    "hoofprints": Sign(
        id="hoofprints",
        label="hoofprints",
        clue="sharp hoofprints cut in dry dust",
        reveals_emu=False,
        tags=set(),
    ),
}

NEEDS = {
    "hungry": Need(
        id="hungry",
        state="hungry",
        hint="a pecking beak and slow, unsteady steps",
        remedy="food",
        failure="For many nights the villagers wondered whether they had frightened away a starving traveler.",
        tags={"grain", "emu"},
    ),
    "thirsty": Need(
        id="thirsty",
        state="thirsty",
        hint="a dry tongue and panting breath",
        remedy="water",
        failure="By dawn only the marks of quick feet remained, and the river seemed sadder for it.",
        tags={"water", "emu"},
    ),
    "cold": Need(
        id="cold",
        state="cold",
        hint="shivering feathers and a tucked neck",
        remedy="warmth",
        failure="The reeds hissed in the night wind, and the child kept hearing how small a warm chance can be once it is missed.",
        tags={"blanket", "emu"},
    ),
}

HELPS = {
    "grain_bowl": Help(
        id="grain_bowl",
        label="grain bowl",
        phrase="the grain from the clay bowl",
        fixes="hungry",
        action="Instead of setting the coins down, the child knelt and poured out a grain bowl before the bird.",
        fail_action="The child set down a grain bowl beside the bird.",
        tags={"grain"},
    ),
    "water_jug": Help(
        id="water_jug",
        label="water jug",
        phrase="cool water from the jug",
        fixes="thirsty",
        action="Instead of murmuring the old tribute words, the child tipped a water jug into a shallow stone hollow.",
        fail_action="The child poured out a little water into a stone hollow.",
        tags={"water"},
    ),
    "wool_cloak": Help(
        id="wool_cloak",
        label="wool cloak",
        phrase="the wool cloak around its shoulders",
        fixes="cold",
        action="Instead of leaving a fearful offering, the child stepped close and laid a wool cloak over the bird's trembling back.",
        fail_action="The child draped a wool cloak over the bird's back.",
        tags={"blanket"},
    ),
}

PAYMENTS = {
    "coins": Payment(
        id="coins",
        label="coins",
        phrase="a little payment of copper coins",
        gleam="a sunset-colored gleam",
        tags={"payment"},
    ),
    "amber": Payment(
        id="amber",
        label="amber bead",
        phrase="a little payment of one amber bead on string",
        gleam="a honey glow",
        tags={"payment"},
    ),
    "ring": Payment(
        id="ring",
        label="silver ring",
        phrase="a little payment of a silver ring",
        gleam="a pale moon gleam",
        tags={"payment"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Talia", "Nora", "Sima", "Vera"]
BOY_NAMES = ["Ivo", "Milan", "Pavel", "Tarin", "Lev", "Soren"]


@dataclass
class StoryParams:
    place: str
    rumor: str
    sign: str
    need: str
    help: str
    payment: str
    child_name: str
    child_gender: str
    elder_type: str
    delay: int = 0
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
    f = world.facts
    child = f["child"]
    rumor = f["rumor"]
    need = f["need"]
    return [
        f'Write a myth-like story for a young child that includes the words "payment", "russian", and "emu", and ends with a twist.',
        f"Tell a gentle myth in which {child.label} carries a fearful payment to meet {rumor.title}, then discovers the visitor is really an emu in need of help.",
        f"Write a small legend where a child learns that a frightening rumor hides a creature that is only {need.state}, and kindness matters more than tribute.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    rumor = f["rumor"]
    need = f["need"]
    help_item = f["help"]
    payment = f["payment"]
    place = f["place"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child from the valley, and {child.pronoun('possessive')} {elder.label_word}. It is also about the strange visitor at {place.phrase}."
        ),
        (
            "What did the villagers think they were doing?",
            f"They thought they were leaving a payment for {rumor.title} so the fields would stay safe. That belief came from an old fear the village kept repeating."
        ),
        (
            "What was the twist in the story?",
            f"The feared russian visitor was not a spirit or tax collector at all. It was really an emu, and the signs made sense once the child looked carefully."
        ),
        (
            f"Why did the payment not solve the problem?",
            f"The creature did not want coins or a bead. It was {need.state}, so what it truly needed was {need.remedy}."
        ),
    ]
    if outcome == "soothed":
        qa.append(
            (
                f"How did {child.label} help the emu?",
                f"{child.label} chose {help_item.label} instead of the old payment. That worked because the emu was {need.state}, so the right help matched the real need."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the emu calming down and the child carrying the untouched payment home. After that, the villagers learned to look closely before turning fear into a ritual."
            )
        )
    else:
        qa.append(
            (
                "Why did the emu run away?",
                f"It ran away because the help came too late or did not fit what it needed. Fear delayed true kindness, and the creature stayed troubled."
            )
        )
        qa.append(
            (
                "What did the child learn at the end?",
                f"{child.label} learned that payment is a poor answer when a living thing needs care. The lesson was to see clearly before obeying an old rumor."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"payment", "russian", "emu"}
    tags |= set(world.facts["need"].tags)
    tags |= set(world.facts["help"].tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sign_matches(S) :- sign(S), reveals_emu(S).
help_matches(N,H) :- need(N), help(H), fixes(H,N).
valid(P,R,S,N,H) :- place(P), rumor(R), sign_matches(S), help_matches(N,H).

late :- delay(D), D >= 2.
outcome(departed) :- late.
outcome(soothed) :- not late, chosen_need(N), chosen_help(H), help_matches(N,H).
outcome(departed) :- not late, chosen_need(N), chosen_help(H), not help_matches(N,H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid in RUMORS:
        lines.append(asp.fact("rumor", rid))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        if sign.reveals_emu:
            lines.append(asp.fact("reveals_emu", sid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for hid, help_item in HELPS.items():
        lines.append(asp.fact("help", hid))
        lines.append(asp.fact("fixes", hid, help_item.fixes))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_need", params.need),
            asp.fact("chosen_help", params.help),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        place="ford",
        rumor="collector",
        sign="tracks",
        need="hungry",
        help="grain_bowl",
        payment="coins",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        delay=0,
    ),
    StoryParams(
        place="hill",
        rumor="rider",
        sign="feathers",
        need="thirsty",
        help="water_jug",
        payment="amber",
        child_name="Pavel",
        child_gender="boy",
        elder_type="grandfather",
        delay=0,
    ),
    StoryParams(
        place="reedbank",
        rumor="duke",
        sign="cry",
        need="cold",
        help="wool_cloak",
        payment="ring",
        child_name="Anya",
        child_gender="girl",
        elder_type="mother",
        delay=0,
    ),
    StoryParams(
        place="ford",
        rumor="collector",
        sign="tracks",
        need="hungry",
        help="water_jug",
        payment="coins",
        child_name="Lev",
        child_gender="boy",
        elder_type="father",
        delay=0,
    ),
    StoryParams(
        place="reedbank",
        rumor="rider",
        sign="feathers",
        need="thirsty",
        help="water_jug",
        payment="amber",
        child_name="Sima",
        child_gender="girl",
        elder_type="grandmother",
        delay=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth storyworld: a fearful payment, a russian rumor, an emu twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--help", choices=HELPS)
    ap.add_argument("--payment", choices=PAYMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.sign and not sign_matches_emu(SIGNS[args.sign]):
        raise StoryError(explain_sign(SIGNS[args.sign]))
    if args.need and args.help:
        if not help_matches_need(NEEDS[args.need], HELPS[args.help]):
            raise StoryError(explain_help(NEEDS[args.need], HELPS[args.help]))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.rumor is None or c[1] == args.rumor)
        and (args.sign is None or c[2] == args.sign)
        and (args.need is None or c[3] == args.need)
        and (args.help is None or c[4] == args.help)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, rumor, sign, need, help_id = rng.choice(sorted(combos))
    payment = args.payment or rng.choice(sorted(PAYMENTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father", "grandmother", "grandfather"])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])
    return StoryParams(
        place=place,
        rumor=rumor,
        sign=sign,
        need=need,
        help=help_id,
        payment=payment,
        child_name=name,
        child_gender=gender,
        elder_type=elder,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        rumor = RUMORS[params.rumor]
        sign = SIGNS[params.sign]
        need = NEEDS[params.need]
        help_item = HELPS[params.help]
        payment = PAYMENTS[params.payment]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not sign_matches_emu(sign):
        raise StoryError(explain_sign(sign))
    world = tell(
        place=place,
        rumor=rumor,
        sign=sign,
        need=need,
        help_item=help_item,
        payment=payment,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        delay=params.delay,
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
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, rumor, sign, need, help) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:10}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place}, {p.need}, {p.help} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
