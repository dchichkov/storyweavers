#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crew_flexible_pilot_kindness_suspense_animal_story.py
================================================================================

A standalone storyworld for a gentle animal tale with **crew**, **flexible**,
and **pilot** built into the simulated domain.

Premise
-------
Two small animals make themselves the berry-boat crew so they can carry a gift
across the water to a friend on the far bank. One child is the pilot. The trip
turns suspenseful when the little craft wobbles and drifts, and a kind grown
animal helps in a physically sensible way. Some stories end with a neat rescue;
some end with the children safe but the gift lost to the water.

The world is deliberately small and reasoned:
- A craft has only so much stability.
- A waterway has only so much roughness.
- A response has only so much rescue power.
- Wildly unreasonable craft/water pairings are rejected up front.
- Low-common-sense responses are known to the world but refused.

Run it
------
python storyworlds/worlds/gpt-5.4/crew_flexible_pilot_kindness_suspense_animal_story.py
python storyworlds/worlds/gpt-5.4/crew_flexible_pilot_kindness_suspense_animal_story.py --all
python storyworlds/worlds/gpt-5.4/crew_flexible_pilot_kindness_suspense_animal_story.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/crew_flexible_pilot_kindness_suspense_animal_story.py --asp
python storyworlds/worlds/gpt-5.4/crew_flexible_pilot_kindness_suspense_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "hen", "doe", "sister"}
        male = {"boy", "father", "uncle", "buck", "brother"}
        if self.type in female or self.attrs.get("gender") == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male or self.attrs.get("gender") == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Waterway:
    id: str
    label: str
    phrase: str
    roughness: int
    drift_to: str
    sound: str
    bank: str
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
class Craft:
    id: str
    label: str
    phrase: str
    stability: int
    seat_line: str
    launch_line: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    for_friend: str
    spoil_line: str
    saved_line: str
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
class Response:
    id: str
    sense: int
    power: int
    helper_species: str
    helper_title: str
    text: str
    fail: str
    qa_text: str
    lesson: str
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
        return [e for e in self.entities.values() if e.role in {"pilot", "crew"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def water_rough_enough(craft: Craft, waterway: Waterway) -> bool:
    return waterway.roughness - craft.stability <= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def trip_severity(craft: Craft, waterway: Waterway, delay: int) -> int:
    return max(1, waterway.roughness - craft.stability + delay + 1)


def is_rescued(response: Response, craft: Craft, waterway: Waterway, delay: int) -> bool:
    return response.power >= trip_severity(craft, waterway, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for water_id, waterway in WATERWAYS.items():
        for craft_id, craft in CRAFTS.items():
            for cargo_id in CARGOS:
                if water_rough_enough(craft, waterway):
                    combos.append((water_id, craft_id, cargo_id))
    return combos


def explain_rejection(craft: Craft, waterway: Waterway) -> str:
    return (
        f"(No story: {craft.phrase} is too flimsy for {waterway.phrase}. "
        f"The water is rough enough to make it tip at once, so there is no "
        f"plausible suspenseful crossing to tell. Pick a steadier craft or "
        f"gentler water.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the safer responses: "
        f"{better}.)"
    )


def propagate(world: World) -> None:
    craft = world.get("craft")
    water = world.get("water")
    danger = world.get("danger")
    if craft.meters["launched"] >= THRESHOLD and craft.meters["drifting"] < THRESHOLD:
        sig = ("drift",)
        if sig not in world.fired:
            world.fired.add(sig)
            craft.meters["drifting"] += 1
            danger.meters["risk"] += 1
            for kid in world.kids():
                kid.memes["fear"] += 1
                kid.memes["together"] += 1

    if craft.meters["drifting"] >= THRESHOLD and danger.meters["risk"] >= THRESHOLD:
        sig = ("alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["danger_seen"] = True


def introduce(world: World, pilot: Entity, crew: Entity, cargo: Cargo, waterway: Waterway, craft: Craft) -> None:
    pilot.memes["kindness"] += 1
    crew.memes["kindness"] += 1
    pilot.memes["pride"] += 1
    crew.memes["joy"] += 1
    world.say(
        f"On a soft morning beside {waterway.phrase}, {pilot.id} the {pilot.attrs['species']} "
        f"and {crew.id} the {crew.attrs['species']} had a plan. Their friend on the far bank "
        f"was resting with a sniffly nose, so the two little animals wanted to carry over "
        f"{cargo.phrase}."
    )
    world.say(
        f'They called themselves the Willow Crew. "{pilot.id} is the pilot," '
        f'{crew.id} said proudly, "and I am the whole deck crew."'
    )
    world.say(craft.seat_line)


def launch(world: World, pilot: Entity, crew: Entity, cargo: Cargo, craft: Craft, waterway: Waterway) -> None:
    craft_ent = world.get("craft")
    craft_ent.meters["launched"] += 1
    world.say(
        f"They tucked {cargo.label} into the middle, gave the little craft a push, "
        f"and climbed in together. {craft.launch_line}"
    )
    world.say(
        f"For a few strokes, everything felt grand. The water made {waterway.sound}, "
        f"and the tiny crew smiled at one another."
    )
    propagate(world)


def suspense(world: World, pilot: Entity, crew: Entity, waterway: Waterway, craft: Craft) -> None:
    craft_ent = world.get("craft")
    if craft_ent.meters["drifting"] < THRESHOLD:
        return
    world.say(
        f"Then the water changed its mind. A stronger tug caught the little {craft.label}, "
        f"turned its nose sideways, and began to pull it toward {waterway.drift_to}."
    )
    world.say(
        f'{crew.id} grabbed the rim. "{pilot.id}," {crew.pronoun()} whispered, '
        f'"the boat is not listening."'
    )
    world.say(
        f"{pilot.id} tried to stay brave because a pilot was supposed to be calm, "
        f"but {pilot.pronoun()} could feel the wobble right through {pilot.pronoun('possessive')} paws."
    )


def call_for_help(world: World, pilot: Entity, crew: Entity) -> None:
    for kid in world.kids():
        kid.memes["trust"] += 1
    world.say(
        f'"Help!" called {pilot.id}. "{crew.id} and I are drifting!"'
    )


def rescue(world: World, helper: Entity, response: Response, cargo: Cargo, waterway: Waterway) -> None:
    craft = world.get("craft")
    danger = world.get("danger")
    craft.meters["drifting"] = 0.0
    craft.meters["safe"] += 1
    danger.meters["risk"] = 0.0
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} the {helper.attrs['species']} was already hurrying along {waterway.bank}. "
        f"{helper.pronoun().capitalize()} {response.text}"
    )
    world.say(
        f"Soon the little craft bumped back against the bank, and {cargo.saved_line}"
    )


def rescue_fail(world: World, helper: Entity, response: Response, cargo: Cargo, waterway: Waterway) -> None:
    craft = world.get("craft")
    danger = world.get("danger")
    craft.meters["drifting"] += 1
    craft.meters["tipped"] += 1
    craft.meters["safe"] += 1
    danger.meters["risk"] = 0.0
    helper.memes["kindness"] += 1
    cargo_ent = world.get("cargo")
    cargo_ent.meters["lost"] += 1
    world.say(
        f"{helper.id} the {helper.attrs['species']} came racing along {waterway.bank} and "
        f"{response.fail}"
    )
    world.say(
        f"The children were scooped safely onto shore, but {cargo.spoil_line}"
    )


def comfort(world: World, helper: Entity, pilot: Entity, crew: Entity, response: Response, saved: bool) -> None:
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["lesson"] += 1
    helper.memes["kindness"] += 1
    if saved:
        world.say(
            f'{helper.id} wrapped them in a dry reed mat and said, '
            f'"A brave crew still asks for help when the water grows tricky."'
        )
    else:
        world.say(
            f'{helper.id} wrapped them in a dry reed mat and said, '
            f'"The gift is gone, but you two are safe, and that is the biggest thing."'
        )
    world.say(
        f"{response.lesson} {pilot.id} leaned close to {crew.id}, and the two little friends "
        f"held paws until their shivers stopped."
    )


def changed_ending(world: World, pilot: Entity, crew: Entity, cargo: Cargo, craft: Craft, saved: bool) -> None:
    pilot.memes["joy"] += 1
    crew.memes["joy"] += 1
    if saved:
        world.say(
            f"Later that day they crossed again the slower way, with a grown-up beside them, "
            f"and their friend received {cargo.label} with a smile. After that, the Willow Crew "
            f"kept a flexible vine tied to their little {craft.label} whenever they played near water."
        )
        world.say(
            f"Now when {pilot.id} said, \"Pilot ready,\" {crew.id} always answered, "
            f"\"Crew ready, and kindness first.\""
        )
    else:
        world.say(
            f"That evening, {helper_phrase(world)} shared warm clover tea with them instead, "
            f"so their friend still had a treat after all. After that, the Willow Crew never launched "
            f"without a grown-up and a flexible vine ready on the bank."
        )
        world.say(
            f"When {pilot.id} looked at the darkening water, {pilot.pronoun()} no longer thought only about adventure. "
            f"{pilot.pronoun().capitalize()} thought about coming home safe together."
        )


def helper_phrase(world: World) -> str:
    helper = world.get("helper")
    return f"{helper.id} the {helper.attrs['species']}"


def tell(
    waterway: Waterway,
    craft: Craft,
    cargo: Cargo,
    response: Response,
    pilot_name: str,
    pilot_gender: str,
    pilot_species: str,
    crew_name: str,
    crew_gender: str,
    crew_species: str,
    helper_name: str,
    delay: int,
) -> World:
    world = World()
    pilot = world.add(Entity(
        id=pilot_name,
        kind="character",
        type="animal",
        role="pilot",
        attrs={"gender": pilot_gender, "species": pilot_species},
    ))
    crew = world.add(Entity(
        id=crew_name,
        kind="character",
        type="animal",
        role="crew",
        attrs={"gender": crew_gender, "species": crew_species},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="animal",
        role="helper",
        attrs={"species": response.helper_species, "title": response.helper_title},
    ))
    water_ent = world.add(Entity(id="water", type="waterway", label=waterway.label))
    craft_ent = world.add(Entity(id="craft", type="craft", label=craft.label))
    cargo_ent = world.add(Entity(id="cargo", type="cargo", label=cargo.label))
    danger = world.add(Entity(id="danger", type="danger", label="the risky water"))

    water_ent.meters["roughness"] = float(waterway.roughness)
    craft_ent.meters["stability"] = float(craft.stability)
    cargo_ent.meters["secure"] = 1.0
    danger.meters["risk"] = 0.0
    pilot.memes["fear"] = 0.0
    crew.memes["fear"] = 0.0

    world.facts.update(
        waterway=waterway,
        craft_cfg=craft,
        cargo_cfg=cargo,
        response=response,
        severity=trip_severity(craft, waterway, delay),
        delay=delay,
    )

    introduce(world, pilot, crew, cargo, waterway, craft)
    world.para()
    launch(world, pilot, crew, cargo, craft, waterway)
    suspense(world, pilot, crew, waterway, craft)
    call_for_help(world, pilot, crew)

    world.para()
    saved = is_rescued(response, craft, waterway, delay)
    if saved:
        rescue(world, helper, response, cargo, waterway)
    else:
        rescue_fail(world, helper, response, cargo, waterway)
    comfort(world, helper, pilot, crew, response, saved)

    world.para()
    changed_ending(world, pilot, crew, cargo, craft, saved)

    world.facts.update(
        pilot=pilot,
        crew=crew,
        helper=helper,
        water=water_ent,
        craft=craft_ent,
        cargo=cargo_ent,
        outcome="rescued" if saved else "spilled",
        danger_seen=world.facts.get("danger_seen", False),
        gift_lost=cargo_ent.meters["lost"] >= THRESHOLD,
    )
    return world


WATERWAYS = {
    "brook": Waterway(
        id="brook",
        label="brook",
        phrase="the brook under the willow roots",
        roughness=1,
        drift_to="a patch of tall reeds",
        sound="a silver plip-plip against the stones",
        bank="the soft muddy bank",
        tags={"brook", "water"},
    ),
    "stream": Waterway(
        id="stream",
        label="stream",
        phrase="the bright stream by the fern hill",
        roughness=2,
        drift_to="a bend where the water hurried past dark stones",
        sound="quick whispery laps",
        bank="the grassy bank",
        tags={"stream", "water"},
    ),
    "creek": Waterway(
        id="creek",
        label="creek",
        phrase="the chilly creek at the edge of the meadow",
        roughness=3,
        drift_to="a noisy place where roots poked out of the bank",
        sound="busy splashes and hurrying swirls",
        bank="the pebbly bank",
        tags={"creek", "water"},
    ),
}

CRAFTS = {
    "bark_boat": Craft(
        id="bark_boat",
        label="bark boat",
        phrase="a bark boat",
        stability=2,
        seat_line="They had made a bark boat with acorn-cap seats and a clover-stem flag.",
        launch_line="The bark boat slid out straight and proud.",
        tags={"boat", "bark"},
    ),
    "reed_raft": Craft(
        id="reed_raft",
        label="reed raft",
        phrase="a reed raft",
        stability=3,
        seat_line="They had tied a reed raft together, wide enough for two small bottoms and one careful gift.",
        launch_line="The reed raft rode low but steady.",
        tags={"raft", "reed"},
    ),
    "walnut_shell": Craft(
        id="walnut_shell",
        label="walnut-shell boat",
        phrase="a walnut-shell boat",
        stability=1,
        seat_line="They had found a walnut shell, lined it with moss, and decided it was a perfect tiny boat.",
        launch_line="The walnut-shell boat bobbed like a brave little cup.",
        tags={"boat", "walnut"},
    ),
}

CARGOS = {
    "berries": Cargo(
        id="berries",
        label="a basket of berries",
        phrase="a basket of berries wrapped in dock leaves",
        for_friend="berries",
        spoil_line="the berries scattered in the water and spun away like red beads",
        saved_line="the berries stayed dry and snug in their dock-leaf wrap",
        tags={"berries", "gift"},
    ),
    "soup": Cargo(
        id="soup",
        label="a thimble of clover soup",
        phrase="a thimble of warm clover soup with a leaf over the top",
        for_friend="soup",
        spoil_line="the little thimble tipped, and the warm soup disappeared into the stream",
        saved_line="the little soup thimble stayed upright, still warm under its leaf lid",
        tags={"soup", "gift"},
    ),
    "cake": Cargo(
        id="cake",
        label="an acorn cake",
        phrase="an acorn cake tied with grass ribbon",
        for_friend="cake",
        spoil_line="the acorn cake went soggy and sank into a swirl of brown water",
        saved_line="the acorn cake stayed dry, and even the grass ribbon kept its bow",
        tags={"cake", "gift"},
    ),
}

RESPONSES = {
    "flexible_vine": Response(
        id="flexible_vine",
        sense=3,
        power=2,
        helper_species="otter",
        helper_title="bank watcher",
        text="caught up with them, flung a flexible vine across the bow, and towed the little craft back before it struck the reeds.",
        fail="threw a flexible vine toward them, but the water gave one hard twist, tipped the little craft, and splashed the gift away before the vine could hold.",
        qa_text="used a flexible vine to tow the little craft back to shore",
        lesson="Then with a gentle voice, the grown otter explained that kind hearts still need careful plans.",
        tags={"vine", "rescue", "otter"},
    ),
    "long_pole": Response(
        id="long_pole",
        sense=3,
        power=1,
        helper_species="beaver",
        helper_title="shore helper",
        text="reached out with a long willow pole and nudged the little craft back toward shore, inch by inch.",
        fail="reached with a long willow pole, but the current shoved the little craft past the tip of it, and the gift splashed out while the children were pulled to shore.",
        qa_text="used a long willow pole to push the little craft back toward shore",
        lesson="The old beaver told them that being small was no problem, but pretending a river was smaller than it really was could be.",
        tags={"pole", "rescue", "beaver"},
    ),
    "back_ride": Response(
        id="back_ride",
        sense=3,
        power=4,
        helper_species="otter",
        helper_title="swift swimmer",
        text="slid straight into the water, tucked the craft against one paw, and ferried the whole little crew safely back on a warm, steady back.",
        fail="slid into the water and gathered them up; even so, the gift was gone before anyone could catch it.",
        qa_text="swam out and ferried the little crew back on a steady back",
        lesson="The strong otter reminded them that courage means caring for every member of the crew, including yourself.",
        tags={"swim", "rescue", "otter"},
    ),
    "shout_only": Response(
        id="shout_only",
        sense=1,
        power=0,
        helper_species="heron",
        helper_title="watcher",
        text="only shouted directions from the bank",
        fail="only shouted directions from the bank, which was not enough to stop the drift",
        qa_text="only shouted from the bank",
        lesson="The bank watcher wished help had come in a better shape.",
        tags={"watching"},
    ),
}

NAME_POOLS = {
    "girl": ["Mira", "Pip", "Daisy", "Nell", "Tansy", "Lulu", "Wren", "Poppy"],
    "boy": ["Moss", "Toby", "Bram", "Nico", "Rowan", "Ollie", "Finn", "Pico"],
}
SPECIES = ["mouse", "rabbit", "squirrel", "mole", "hedgehog"]


@dataclass
class StoryParams:
    waterway: str
    craft: str
    cargo: str
    response: str
    pilot_name: str
    pilot_gender: str
    pilot_species: str
    crew_name: str
    crew_gender: str
    crew_species: str
    helper_name: str
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


KNOWLEDGE = {
    "brook": [(
        "What is a brook?",
        "A brook is a small stream of moving water. Even a small brook can tug hard on a tiny boat."
    )],
    "stream": [(
        "Why can a stream be tricky for a little boat?",
        "A stream keeps moving, so it can turn and push a small boat even when the water looks pretty. Tiny boats need calm water and careful help."
    )],
    "creek": [(
        "Why is a creek stronger than it looks?",
        "A creek can have fast water near rocks and roots. The moving water can pull little things sideways very quickly."
    )],
    "boat": [(
        "What does a pilot do?",
        "A pilot is the one guiding a boat or another vehicle. A good pilot watches where they are going and asks for help when needed."
    )],
    "crew": [(
        "What is a crew?",
        "A crew is a team working together on the same job. Being a good crew means helping one another and staying together."
    )],
    "vine": [(
        "What is a vine?",
        "A vine is a long plant stem that can bend and curl as it grows. A flexible vine can bend without snapping, which can make it useful for pulling something light."
    )],
    "pole": [(
        "Why can a long pole help near water?",
        "A long pole lets someone reach farther from the bank. That can help push or pull a small boat without climbing into the water first."
    )],
    "otter": [(
        "Why are otters good swimmers?",
        "Otters have strong bodies and are very good at moving through water. They can swim quickly and stay steady where little animals would wobble."
    )],
    "beaver": [(
        "What are beavers good at near a river or stream?",
        "Beavers are good at working with wood and water. They understand banks, sticks, and how moving water behaves."
    )],
    "gift": [(
        "Why did the little animals want to cross the water?",
        "They wanted to bring something kind to a friend. Kindness often means doing a little work to help someone else feel better."
    )],
}
KNOWLEDGE_ORDER = ["gift", "brook", "stream", "creek", "boat", "crew", "vine", "pole", "otter", "beaver"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pilot = f["pilot"]
    crew = f["crew"]
    cargo = f["cargo_cfg"]
    waterway = f["waterway"]
    outcome = f["outcome"]
    if outcome == "rescued":
        return [
            'Write an animal story for a young child using the words "crew", "flexible", and "pilot".',
            f"Tell a gentle suspense story where {pilot.id} and {crew.id} become a tiny crew, drift on {waterway.label}, and are saved by a kind grown animal.",
            f"Write a story where small animals try to deliver {cargo.label} across the water, the trip becomes scary, and kindness brings them safely home."
        ]
    return [
        'Write an animal story for a young child using the words "crew", "flexible", and "pilot".',
        f"Tell a suspenseful but tender story where {pilot.id} is the pilot of a tiny crew on {waterway.label}, and a grown animal saves the children even though the gift is lost.",
        f"Write a story about small animals trying to carry {cargo.label} to a friend, learning that kindness matters more than finishing the trip."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    pilot = f["pilot"]
    crew = f["crew"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    waterway = f["waterway"]
    craft = f["craft_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two little animal friends, {pilot.id} the {pilot.attrs['species']} and {crew.id} the {crew.attrs['species']}. They made themselves a tiny crew so they could carry {cargo.label} across the water."
        ),
        (
            f"Why did {pilot.id} and {crew.id} go onto {waterway.label}?",
            f"They wanted to bring {cargo.label} to a friend on the far bank. The trip began as an act of kindness before it turned scary."
        ),
        (
            f"Why was {pilot.id} called the pilot?",
            f"{pilot.id} was the one guiding the little {craft.label}. Calling {pilot.pronoun('object')} the pilot showed that the children were pretending to be a real little boat crew."
        ),
        (
            "What made the story suspenseful?",
            f"The water suddenly pulled the little {craft.label} sideways and began to carry it toward {waterway.drift_to}. That change made the children afraid because they could feel they were no longer in control."
        ),
    ]
    if outcome == "rescued":
        qa.append((
            f"How did {helper.id} help the children?",
            f"{helper.id} {response.qa_text}. The help worked because it matched the moving water and reached the little craft in time."
        ))
        qa.append((
            "How did kindness change the ending?",
            f"The story ended happily because the children were rescued and their gift stayed safe. Kindness showed up twice: first when the children tried to help a friend, and again when {helper.id} hurried to help them."
        ))
    else:
        qa.append((
            f"Did the children stay safe, and what was lost?",
            f"Yes, the children were saved and brought back to shore. But {cargo.spoil_line}, so the gift did not make it across."
        ))
        qa.append((
            "What did the children learn at the end?",
            f"They learned that being kind does not mean taking careless risks. They also learned that coming home safe together matters more than finishing a brave-looking plan."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["waterway"].tags) | set(f["craft_cfg"].tags) | set(f["cargo_cfg"].tags)
    tags |= set(f["response"].tags)
    tags.add("gift")
    out: list[tuple[str, str]] = []
    mapping = {
        "bark": "boat",
        "reed": "crew",
        "raft": "crew",
        "walnut": "boat",
        "rescue": None,
        "swim": "otter",
        "watching": None,
    }
    expanded = set(tags)
    for tag in list(tags):
        if tag in mapping and mapping[tag]:
            expanded.add(mapping[tag])
    for key in KNOWLEDGE_ORDER:
        if key in expanded and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        waterway="brook",
        craft="walnut_shell",
        cargo="berries",
        response="flexible_vine",
        pilot_name="Mira",
        pilot_gender="girl",
        pilot_species="mouse",
        crew_name="Moss",
        crew_gender="boy",
        crew_species="mole",
        helper_name="Auntie Oat",
        delay=0,
    ),
    StoryParams(
        waterway="stream",
        craft="bark_boat",
        cargo="soup",
        response="back_ride",
        pilot_name="Toby",
        pilot_gender="boy",
        pilot_species="rabbit",
        crew_name="Poppy",
        crew_gender="girl",
        crew_species="squirrel",
        helper_name="Old Ripple",
        delay=1,
    ),
    StoryParams(
        waterway="stream",
        craft="walnut_shell",
        cargo="cake",
        response="long_pole",
        pilot_name="Nell",
        pilot_gender="girl",
        pilot_species="hedgehog",
        crew_name="Finn",
        crew_gender="boy",
        crew_species="mouse",
        helper_name="Master Dam",
        delay=1,
    ),
    StoryParams(
        waterway="creek",
        craft="reed_raft",
        cargo="berries",
        response="back_ride",
        pilot_name="Lulu",
        pilot_gender="girl",
        pilot_species="rabbit",
        crew_name="Rowan",
        crew_gender="boy",
        crew_species="mole",
        helper_name="River Otter",
        delay=1,
    ),
    StoryParams(
        waterway="brook",
        craft="bark_boat",
        cargo="cake",
        response="long_pole",
        pilot_name="Bram",
        pilot_gender="boy",
        pilot_species="squirrel",
        crew_name="Daisy",
        crew_gender="girl",
        crew_species="mouse",
        helper_name="Willow Beard",
        delay=0,
    ),
]


ASP_RULES = r"""
valid(W,C,G) :- waterway(W), craft(C), cargo(G), roughness(W,R), stability(C,S), R - S <= 1.
sensible(Rp) :- response(Rp), sense(Rp,S), sense_min(M), S >= M.

severity(V) :- chosen_waterway(W), chosen_craft(C), delay(D),
               roughness(W,R), stability(C,S), V = R - S + D + 1, V >= 1.
severity(1) :- chosen_waterway(W), chosen_craft(C), delay(D),
               roughness(W,R), stability(C,S), R - S + D + 1 < 1.

rescued :- chosen_response(Rp), power(Rp,P), severity(V), P >= V.
outcome(rescued) :- rescued.
outcome(spilled) :- not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid, w in WATERWAYS.items():
        lines.append(asp.fact("waterway", wid))
        lines.append(asp.fact("roughness", wid, w.roughness))
    for cid, c in CRAFTS.items():
        lines.append(asp.fact("craft", cid))
        lines.append(asp.fact("stability", cid, c.stability))
    for gid in CARGOS:
        lines.append(asp.fact("cargo", gid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_waterway", params.waterway),
        asp.fact("chosen_craft", params.craft),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "rescued" if is_rescued(RESPONSES[params.response], CRAFTS[params.craft], WATERWAYS[params.waterway], params.delay) else "spilled"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: a tiny crew, a pilot, suspenseful water, and kindness."
    )
    ap.add_argument("--waterway", choices=WATERWAYS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time before help fully reaches them")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in NAME_POOLS[gender] if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.craft and args.waterway:
        craft = CRAFTS[args.craft]
        waterway = WATERWAYS[args.waterway]
        if not water_rough_enough(craft, waterway):
            raise StoryError(explain_rejection(craft, waterway))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.waterway is None or c[0] == args.waterway)
        and (args.craft is None or c[1] == args.craft)
        and (args.cargo is None or c[2] == args.cargo)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    waterway, craft, cargo = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    pilot_gender = rng.choice(["girl", "boy"])
    crew_gender = rng.choice(["girl", "boy"])
    pilot_name = pick_name(rng, pilot_gender)
    crew_name = pick_name(rng, crew_gender, avoid=pilot_name)
    pilot_species = rng.choice(SPECIES)
    crew_species = rng.choice([s for s in SPECIES if s != pilot_species] or SPECIES)
    helper_name = rng.choice(["Old Ripple", "Auntie Oat", "Master Dam", "River Reed", "Mossback", "Willow Beard"])

    return StoryParams(
        waterway=waterway,
        craft=craft,
        cargo=cargo,
        response=response,
        pilot_name=pilot_name,
        pilot_gender=pilot_gender,
        pilot_species=pilot_species,
        crew_name=crew_name,
        crew_gender=crew_gender,
        crew_species=crew_species,
        helper_name=helper_name,
        delay=delay,
    )


def validate_params(params: StoryParams) -> None:
    if params.waterway not in WATERWAYS:
        raise StoryError(f"(Unknown waterway: {params.waterway})")
    if params.craft not in CRAFTS:
        raise StoryError(f"(Unknown craft: {params.craft})")
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not water_rough_enough(CRAFTS[params.craft], WATERWAYS[params.waterway]):
        raise StoryError(explain_rejection(CRAFTS[params.craft], WATERWAYS[params.waterway]))


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        waterway=WATERWAYS[params.waterway],
        craft=CRAFTS[params.craft],
        cargo=CARGOS[params.cargo],
        response=RESPONSES[params.response],
        pilot_name=params.pilot_name,
        pilot_gender=params.pilot_gender,
        pilot_species=params.pilot_species,
        crew_name=params.crew_name,
        crew_gender=params.crew_gender,
        crew_species=params.crew_species,
        helper_name=params.helper_name,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (waterway, craft, cargo) combos:\n")
        for waterway, craft, cargo in combos:
            print(f"  {waterway:8} {craft:13} {cargo}")
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
            header = f"### {p.pilot_name} & {p.crew_name}: {p.craft} on {p.waterway} carrying {p.cargo} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
