#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/meym_gentle_toe_pl_dim_friendship_bedtime.py
=======================================================================

A standalone story world for a bedtime friendship tale: one child feels uneasy
during a sleepover, a friend notices, and the room is changed in a small,
reasonable way until bedtime feels safe again.

This world is built around a narrow common-sense constraint: the comfort method
must actually match the kind of bedtime worry.

- Shadow worries need a little light or a curtain fix.
- Creak worries need checking and understanding the sound.
- Thunder worries need weather-soothing company.

The stories are gentle, bedtime-shaped, and state-driven. They also include the
seed words "meym", "gentle", and "toe-pl-dim" as natural parts of the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/meym_gentle_toe_pl_dim_friendship_bedtime.py
    python storyworlds/worlds/gpt-5.4/meym_gentle_toe_pl_dim_friendship_bedtime.py --place moon_room --worry branch_shadow --comfort nightlight
    python storyworlds/worlds/gpt-5.4/meym_gentle_toe_pl_dim_friendship_bedtime.py --worry thunder --comfort nightlight
    python storyworlds/worlds/gpt-5.4/meym_gentle_toe_pl_dim_friendship_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/meym_gentle_toe_pl_dim_friendship_bedtime.py --qa --json
    python storyworlds/worlds/gpt-5.4/meym_gentle_toe_pl_dim_friendship_bedtime.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    opening: str
    bed_detail: str
    window_detail: str
    sounds: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Worry:
    id: str
    label: str
    cause: str
    starter: str
    image: str
    reason: str
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
class Comfort:
    id: str
    label: str
    soothes: set[str]
    action: str
    effect: str
    qa_text: str
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


def _r_worry_swells(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    guest = world.get("guest")
    host = world.get("host")
    worry = world.get("worry")
    if worry.meters["active"] < THRESHOLD:
        return out
    cause = worry.attrs.get("cause", "")
    if cause == "shadow" and room.meters["darkness"] >= THRESHOLD:
        sig = ("worry_swells", cause)
        if sig not in world.fired:
            world.fired.add(sig)
            guest.memes["fear"] += 1
            host.memes["care"] += 1
            out.append("__worry__")
    if cause == "sound" and room.meters["mystery_sound"] >= THRESHOLD:
        sig = ("worry_swells", cause)
        if sig not in world.fired:
            world.fired.add(sig)
            guest.memes["fear"] += 1
            host.memes["care"] += 1
            out.append("__worry__")
    if cause == "weather" and room.meters["storm_noise"] >= THRESHOLD:
        sig = ("worry_swells", cause)
        if sig not in world.fired:
            world.fired.add(sig)
            guest.memes["fear"] += 1
            host.memes["care"] += 1
            out.append("__worry__")
    return out


def _r_friendship_steadies(world: World) -> list[str]:
    out: list[str] = []
    guest = world.get("guest")
    host = world.get("host")
    comfort = world.get("comfort")
    worry = world.get("worry")
    if comfort.meters["used"] < THRESHOLD:
        return out
    if worry.meters["settled"] < THRESHOLD:
        return out
    sig = ("friendship_steadies", comfort.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guest.memes["calm"] += 1
    guest.memes["trust"] += 1
    host.memes["warmth"] += 1
    host.memes["pride"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="worry_swells", tag="emotional", apply=_r_worry_swells),
    Rule(name="friendship_steadies", tag="emotional", apply=_r_friendship_steadies),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def comfort_works(worry: Worry, comfort: Comfort) -> bool:
    return worry.cause in comfort.soothes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for worry_id in sorted(place.affords):
            worry = WORRIES[worry_id]
            for comfort_id, comfort in COMFORTS.items():
                if comfort_works(worry, comfort):
                    combos.append((place_id, worry_id, comfort_id))
    return combos


def explain_rejection(place: Place, worry: Worry, comfort: Comfort) -> str:
    if worry.id not in place.affords:
        return (
            f"(No story: {place.label} does not naturally support the worry "
            f"'{worry.label}'. Pick a worry that fits this room's bedtime details.)"
        )
    return (
        f"(No story: {comfort.label} does not honestly settle {worry.label}. "
        f"This world only allows bedtime comforts that match the real cause of the worry.)"
    )


def predict_settle(world: World, comfort: Comfort) -> dict:
    sim = world.copy()
    apply_comfort(sim, comfort, narrate=False)
    guest = sim.get("guest")
    worry = sim.get("worry")
    room = sim.get("room")
    return {
        "settled": worry.meters["settled"] >= THRESHOLD,
        "fear": guest.memes["fear"],
        "darkness": room.meters["darkness"],
        "mystery_sound": room.meters["mystery_sound"],
        "storm_noise": room.meters["storm_noise"],
    }


def introduce(world: World, guest: Entity, host: Entity, parent: Entity, place: Place) -> None:
    guest.memes["glad"] += 1
    host.memes["glad"] += 1
    world.say(
        f"It was sleepover night, and {guest.id} had come to stay with {host.id}. "
        f"{place.opening} {place.bed_detail}"
    )
    world.say(
        f"{host.id}'s {parent.label_word} tucked the two friends in, smoothed the quilt, "
        f"and wished them good night."
    )


def settle_in(world: World, guest: Entity, host: Entity, place: Place) -> None:
    world.say(
        f"For a little while they whispered about clouds, rabbits, and what shapes the moon might be making "
        f"outside the window. {place.window_detail}"
    )
    world.say(
        f"Then the room grew quiet in a gentle, bedtime way, with only {place.sounds}."
    )


def stir_worry(world: World, guest: Entity, worry: Worry) -> None:
    worry_ent = world.get("worry")
    worry_ent.meters["active"] = 1.0
    propagate(world, narrate=False)
    guest.memes["uneasy"] += 1
    world.say(
        f"But then {worry.starter} {worry.image} {guest.id} pulled the quilt up to {guest.pronoun('possessive')} chin."
    )
    world.say(
        f'"That looks a little strange," {guest.pronoun()} whispered.'
    )


def notice_friend(world: World, host: Entity, guest: Entity, worry: Worry) -> None:
    pred = predict_settle(world, COMFORTS[world.facts["comfort_cfg"].id])
    world.facts["predicted_settled"] = pred["settled"]
    host.memes["kindness"] += 1
    world.say(
        f"{host.id} heard the tremble in {guest.id}'s voice and scooted closer. "
        f'"It is all right," {host.pronoun()} said in a gentle voice. "{worry.reason}"'
    )


def invent_meym(world: World, guest: Entity, host: Entity) -> None:
    guest.memes["bond"] += 1
    host.memes["bond"] += 1
    world.say(
        f'To make the room feel friendlier, the two of them made up a tiny sleepover word: "meym." '
        f'In their game, meym meant, "I am here with you."'
    )


def offer_comfort(world: World, host: Entity, comfort: Comfort) -> None:
    world.say(
        f'"Let us try {comfort.action}," {host.id} whispered.'
    )


def apply_comfort(world: World, comfort: Comfort, narrate: bool = True) -> None:
    room = world.get("room")
    worry = world.get("worry")
    comfort_ent = world.get("comfort")
    comfort_ent.meters["used"] = 1.0
    cause = worry.attrs.get("cause", "")
    if comfort.id == "nightlight":
        room.meters["darkness"] = 0.0
        room.meters["warm_light"] += 1
        worry.meters["settled"] = 1.0 if cause == "shadow" else 0.0
    elif comfort.id == "check_corner":
        room.meters["mystery_sound"] = 0.0
        room.meters["understood_sound"] += 1
        worry.meters["settled"] = 1.0 if cause == "sound" else 0.0
    elif comfort.id == "count_together":
        room.meters["storm_noise"] = 0.0
        room.meters["shared_rhythm"] += 1
        worry.meters["settled"] = 1.0 if cause == "weather" else 0.0
    if worry.meters["settled"] >= THRESHOLD:
        worry.meters["active"] = 0.0
    propagate(world, narrate=False)
    if narrate:
        world.say(comfort.effect)


def sleep_end(world: World, guest: Entity, host: Entity, comfort: Comfort) -> None:
    guest.memes["sleepy"] += 1
    host.memes["sleepy"] += 1
    world.say(
        f"Soon the room felt smaller and softer, as if bedtime had tucked itself around the two friends."
    )
    world.say(
        f"{guest.id} whispered, \"meym,\" and {host.id} whispered it back."
    )
    if comfort.id == "nightlight":
        world.say(
            "The lamp stayed on its toe-pl-dim setting, a little warm glow by the bed, until both children's eyes drifted closed."
        )
    elif comfort.id == "check_corner":
        world.say(
            "Only the easy house-sounds remained, and the moon laid a pale strip on the rug while both children fell asleep."
        )
    else:
        world.say(
            "The last far-away rumble faded, and the blanket rose and fell with their slow, sleepy breaths."
        )


def tell(
    place: Place,
    worry_cfg: Worry,
    comfort_cfg: Comfort,
    *,
    guest_name: str = "Lina",
    guest_gender: str = "girl",
    host_name: str = "Milo",
    host_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(place)
    guest = world.add(Entity(id=guest_name, kind="character", type=guest_gender, role="guest"))
    host = world.add(Entity(id=host_name, kind="character", type=host_gender, role="host"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    worry = world.add(
        Entity(
            id="worry",
            kind="thing",
            type="worry",
            label=worry_cfg.label,
            attrs={"cause": worry_cfg.cause},
            tags=set(worry_cfg.tags),
        )
    )
    comfort = world.add(
        Entity(
            id="comfort",
            kind="thing",
            type="comfort",
            label=comfort_cfg.label,
            attrs={"soothes": sorted(comfort_cfg.soothes)},
            tags=set(comfort_cfg.tags),
        )
    )

    room.meters["darkness"] = 1.0 if worry_cfg.cause == "shadow" else 0.0
    room.meters["mystery_sound"] = 1.0 if worry_cfg.cause == "sound" else 0.0
    room.meters["storm_noise"] = 1.0 if worry_cfg.cause == "weather" else 0.0
    room.meters["warm_light"] = 0.0
    room.meters["understood_sound"] = 0.0
    room.meters["shared_rhythm"] = 0.0
    worry.meters["active"] = 0.0
    worry.meters["settled"] = 0.0
    comfort.meters["used"] = 0.0
    guest.memes["fear"] = 0.0
    guest.memes["calm"] = 0.0
    guest.memes["trust"] = 0.0
    host.memes["care"] = 0.0
    host.memes["warmth"] = 0.0
    host.memes["pride"] = 0.0

    world.facts.update(
        place=place,
        worry_cfg=worry_cfg,
        comfort_cfg=comfort_cfg,
        guest=guest,
        host=host,
        parent=parent,
    )

    introduce(world, guest, host, parent, place)
    settle_in(world, guest, host, place)

    world.para()
    stir_worry(world, guest, worry_cfg)
    notice_friend(world, host, guest, worry_cfg)
    invent_meym(world, guest, host)
    offer_comfort(world, host, comfort_cfg)

    world.para()
    apply_comfort(world, comfort_cfg, narrate=True)
    sleep_end(world, guest, host, comfort_cfg)

    world.facts.update(
        room=room,
        worry=worry,
        comfort=comfort,
        settled=worry.meters["settled"] >= THRESHOLD,
        meym_used=True,
    )
    return world


PLACES = {
    "moon_room": Place(
        id="moon_room",
        label="the moon room",
        opening="A moon-shaped lamp sat on the dresser, and star stickers shimmered faintly on the ceiling.",
        bed_detail="Two small beds stood side by side, with one soft quilt stretched across them like a bridge.",
        window_detail="Outside, a branch moved every now and then beside the curtain.",
        sounds="the quiet house and a leafish tap at the window",
        affords={"branch_shadow", "hallway_creak"},
    ),
    "hall_room": Place(
        id="hall_room",
        label="the hall room",
        opening="A row of books leaned against the wall, and a tiny rug curled at the corner near the door.",
        bed_detail="The pillows smelled clean, and the blankets were smooth and cool at first.",
        window_detail="The hallway beyond the door held a narrow line of golden light.",
        sounds="the old house settling and the soft hush of the hallway",
        affords={"hallway_creak", "branch_shadow"},
    ),
    "rain_room": Place(
        id="rain_room",
        label="the rain room",
        opening="A round night table stood between the beds, with a lamp that could glow warm and low.",
        bed_detail="The blankets were thick enough to make a little cave of cozy shadows.",
        window_detail="Raindrops tapped the glass, and the curtain puffed a little when the wind breathed.",
        sounds="rain on the window and the roof answering back",
        affords={"thunder", "branch_shadow"},
    ),
}

WORRIES = {
    "branch_shadow": Worry(
        id="branch_shadow",
        label="a branch shadow",
        cause="shadow",
        starter="a long shadow slid over the wall, and for one blinking moment it looked like a giant bent rabbit",
        image="The shape wobbled whenever the branch outside moved.",
        reason="It is only the branch and the curtain making moon-pictures.",
        tags={"shadow", "dark"},
    ),
    "hallway_creak": Worry(
        id="hallway_creak",
        label="a hallway creak",
        cause="sound",
        starter="the floor in the hallway gave a slow creak, and it sounded bigger in the dark than it really was",
        image="The little noise seemed to wait by the door.",
        reason="Old boards talk at night, but they are only boards.",
        tags={"sound", "night"},
    ),
    "thunder": Worry(
        id="thunder",
        label="thunder",
        cause="weather",
        starter="a rumble rolled across the sky and under the window",
        image="The room seemed to hold its breath until the sound passed.",
        reason="Thunder is loud, but it stays in the sky and keeps moving along.",
        tags={"thunder", "weather"},
    ),
}

COMFORTS = {
    "nightlight": Comfort(
        id="nightlight",
        label="the night-light",
        soothes={"shadow"},
        action="the lamp on its toe-pl-dim setting",
        effect="Host reached over and turned on the lamp at its toe-pl-dim setting. The small amber glow showed the shadow for what it was: only a branch, a curtain, and some moonlight being busy together.",
        qa_text="turned on the night-light at its toe-pl-dim setting so the shadow could be seen clearly",
        tags={"nightlight", "lamp"},
    ),
    "check_corner": Comfort(
        id="check_corner",
        label="checking the room together",
        soothes={"sound"},
        action="checking the room together",
        effect="Together they sat up, listened, and heard the creak once more. Then Host padded to the door, touched it gently, and when the latch settled, the strange noise stopped sounding mysterious.",
        qa_text="checked the room together and found the small sound's harmless cause",
        tags={"check", "sound"},
    ),
    "count_together": Comfort(
        id="count_together",
        label="counting between rumbles",
        soothes={"weather"},
        action="counting between the rumbles under the blanket",
        effect="The friends tucked themselves under the quilt, held the blanket edge, and counted softly between the rumbles. With each number the thunder seemed farther away, and the room felt steadier.",
        qa_text="counted softly together under the blanket until the thunder felt farther away",
        tags={"counting", "thunder"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Zoe", "Ivy", "Lucy", "Anna"]
BOY_NAMES = ["Milo", "Theo", "Owen", "Eli", "Finn", "Noah", "Ben", "Sam"]


@dataclass
class StoryParams:
    place: str
    worry: str
    comfort: str
    guest_name: str
    guest_gender: str
    host_name: str
    host_gender: str
    parent: str
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


KNOWLEDGE = {
    "shadow": [
        (
            "What makes a shadow on the wall at night?",
            "A shadow happens when something blocks light. At night, moonlight or lamp light can make curtains and branches cast shapes on the wall."
        )
    ],
    "dark": [
        (
            "Why can things look different in the dark?",
            "When there is less light, your eyes get less information. A small shape can seem bigger or stranger until you see it clearly."
        )
    ],
    "sound": [
        (
            "Why do little house sounds seem bigger at bedtime?",
            "When everything else is quiet, tiny sounds stand out more. Your ears notice them sharply, and your imagination can make them feel larger."
        )
    ],
    "night": [
        (
            "What can help when night sounds feel scary?",
            "Listening with a calm friend or grown-up can help you understand the sound. Once you know what it is, it usually feels less scary."
        )
    ],
    "thunder": [
        (
            "What is thunder?",
            "Thunder is the loud sound that comes after lightning heats the air very fast. It can sound big, but it stays outside in the sky."
        )
    ],
    "weather": [
        (
            "Why does counting slowly help during a storm?",
            "Counting gives your mind a steady job to do. A calm rhythm can help your body feel safer and slower too."
        )
    ],
    "nightlight": [
        (
            "What is a night-light for?",
            "A night-light gives a small soft glow so a room is not fully dark. It can help you see that ordinary things are only ordinary things."
        )
    ],
    "lamp": [
        (
            "What does toe-pl-dim mean in this story?",
            "Toe-pl-dim is the friends' silly name for the lamp's very lowest warm setting. It means the light is tiny and soft, just enough for bedtime."
        )
    ],
    "check": [
        (
            "Why does checking a room sometimes help at bedtime?",
            "Checking helps you learn what a sound or shape really is. Knowing the cause can turn a mystery back into something ordinary."
        )
    ],
    "counting": [
        (
            "Why can a friend help you feel brave at bedtime?",
            "A kind friend can stay close, listen, and do the calm thing with you. Sharing the moment can make a worry feel smaller."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "shadow",
    "dark",
    "sound",
    "night",
    "thunder",
    "weather",
    "nightlight",
    "lamp",
    "check",
    "counting",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    guest = f["guest"]
    host = f["host"]
    worry = f["worry_cfg"]
    comfort = f["comfort_cfg"]
    place = f["place"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old about friendship that includes the words "meym", "gentle", and "toe-pl-dim".',
        f"Tell a soft sleepover story where {guest.id} feels uneasy because of {worry.label} in {place.label}, and {host.id} helps using {comfort.label}.",
        f"Write a child-facing bedtime tale in which two friends invent a tiny word meaning 'I am here with you' and use it to make a room feel safe."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    guest = f["guest"]
    host = f["host"]
    parent = f["parent"]
    place = f["place"]
    worry_cfg = f["worry_cfg"]
    comfort_cfg = f["comfort_cfg"]
    settled = f.get("settled", False)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {guest.id} and {host.id}, having a bedtime sleepover. {host.id}'s {parent.label_word} helps settle them in at the start."
        ),
        (
            "What made bedtime feel strange?",
            f"Bedtime felt strange because of {worry_cfg.label}. {worry_cfg.reason} was true, but at first the room did not feel that simple to {guest.id}."
        ),
        (
            f"What did the word meym mean to {guest.id} and {host.id}?",
            f'Meym was the tiny word they invented to mean, "I am here with you." It turned their friendship into something {guest.id} could almost hear and hold.'
        ),
    ]
    if settled:
        qa.append(
            (
                f"How did {host.id} help {guest.id} feel calm again?",
                f"{host.id} {comfort_cfg.qa_text}. That worked because it matched the real cause of the worry instead of only telling {guest.id} not to be afraid."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly, with the room feeling soft and safe again. The ending image shows the change: the worry had settled, and the two friends fell asleep together."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["worry_cfg"].tags) | set(world.facts["comfort_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_room",
        worry="branch_shadow",
        comfort="nightlight",
        guest_name="Lina",
        guest_gender="girl",
        host_name="Milo",
        host_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="hall_room",
        worry="hallway_creak",
        comfort="check_corner",
        guest_name="Nora",
        guest_gender="girl",
        host_name="Theo",
        host_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="rain_room",
        worry="thunder",
        comfort="count_together",
        guest_name="Ella",
        guest_gender="girl",
        host_name="Finn",
        host_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="rain_room",
        worry="branch_shadow",
        comfort="nightlight",
        guest_name="Lucy",
        guest_gender="girl",
        host_name="Eli",
        host_gender="boy",
        parent="father",
    ),
]


ASP_RULES = r"""
fits_place(P, W) :- place(P), worry(W), affords(P, W).
works(W, C) :- worry(W), comfort(C), cause(W, K), soothes(C, K).
valid(P, W, C) :- fits_place(P, W), works(W, C).

settled(P, W, C) :- valid(P, W, C).
outcome(P, W, C, settled) :- settled(P, W, C).

#show valid/3.
#show outcome/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for worry_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, worry_id))
    for worry_id, worry in WORRIES.items():
        lines.append(asp.fact("worry", worry_id))
        lines.append(asp.fact("cause", worry_id, worry.cause))
    for comfort_id, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", comfort_id))
        for cause in sorted(comfort.soothes):
            lines.append(asp.fact("soothes", comfort_id, cause))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcomes() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "outcome")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos() matches ASP ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    expected_outcomes = {(p, w, c, "settled") for (p, w, c) in valid_combos()}
    actual_outcomes = set(asp_outcomes())
    if expected_outcomes == actual_outcomes:
        print(f"OK: outcome model matches ({len(actual_outcomes)} settled outcomes).")
    else:
        rc = 1
        print("MISMATCH in outcomes.")
        if expected_outcomes - actual_outcomes:
            print("  missing in asp:", sorted(expected_outcomes - actual_outcomes))
        if actual_outcomes - expected_outcomes:
            print("  extra in asp:", sorted(actual_outcomes - expected_outcomes))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime friendship worry soothed the sensible way."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--guest-name")
    ap.add_argument("--guest-gender", choices=["girl", "boy"])
    ap.add_argument("--host-name")
    ap.add_argument("--host-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.worry and args.comfort:
        place = PLACES[args.place]
        worry = WORRIES[args.worry]
        comfort = COMFORTS[args.comfort]
        if (args.place, args.worry, args.comfort) not in valid_combos():
            raise StoryError(explain_rejection(place, worry, comfort))
    elif args.place and args.worry and args.worry not in PLACES[args.place].affords:
        place = PLACES[args.place]
        worry = WORRIES[args.worry]
        comfort = COMFORTS[args.comfort] if args.comfort else next(iter(COMFORTS.values()))
        raise StoryError(explain_rejection(place, worry, comfort))
    elif args.worry and args.comfort and not comfort_works(WORRIES[args.worry], COMFORTS[args.comfort]):
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        raise StoryError(explain_rejection(place, WORRIES[args.worry], COMFORTS[args.comfort]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.worry is None or combo[1] == args.worry)
        and (args.comfort is None or combo[2] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, worry_id, comfort_id = rng.choice(sorted(combos))
    guest_gender = args.guest_gender or rng.choice(["girl", "boy"])
    host_gender = args.host_gender or rng.choice(["girl", "boy"])
    guest_name = args.guest_name or _pick_name(rng, guest_gender)
    host_name = args.host_name or _pick_name(rng, host_gender, avoid=guest_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        worry=worry_id,
        comfort=comfort_id,
        guest_name=guest_name,
        guest_gender=guest_gender,
        host_name=host_name,
        host_gender=host_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.worry not in WORRIES:
        raise StoryError(f"(Unknown worry: {params.worry})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")
    place = PLACES[params.place]
    worry = WORRIES[params.worry]
    comfort = COMFORTS[params.comfort]
    if (params.place, params.worry, params.comfort) not in valid_combos():
        raise StoryError(explain_rejection(place, worry, comfort))

    world = tell(
        place,
        worry,
        comfort,
        guest_name=params.guest_name,
        guest_gender=params.guest_gender,
        host_name=params.host_name,
        host_gender=params.host_gender,
        parent_type=params.parent,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, worry, comfort) combos:\n")
        for place, worry, comfort in combos:
            print(f"  {place:10} {worry:14} {comfort}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.place}: {p.worry} -> {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
