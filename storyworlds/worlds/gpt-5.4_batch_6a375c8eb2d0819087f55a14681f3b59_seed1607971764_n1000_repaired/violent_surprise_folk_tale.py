#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/violent_surprise_folk_tale.py
========================================================

A standalone storyworld for a small folk-tale domain about spring seed, a hill
path, and a violent wind. A child carries seed from a village to an elder on
the hill. The chosen container must actually fit the seed, and loose seed must
travel in something closed. Once the child sets out, the route's exposure and
any delay decide whether the wind leaves the load whole, scatters part of it,
or steals it all.

The world aims for a folk-tale feel:
- a simple task with village stakes,
- a warning from someone wise,
- a violent natural force,
- a turn driven by simulated state,
- and an ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/violent_surprise_folk_tale.py
    python storyworlds/worlds/gpt-5.4/violent_surprise_folk_tale.py --cargo poppy --container basket
    python storyworlds/worlds/gpt-5.4/violent_surprise_folk_tale.py --cargo barley --route ridge --delay 2
    python storyworlds/worlds/gpt-5.4/violent_surprise_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/violent_surprise_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/violent_surprise_folk_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BASE_WIND = 1


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
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    loose: bool
    plant_word: str
    bloom: str
    gift_food: str
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
class Container:
    id: str
    label: str
    phrase: str
    cover: int
    holds_loose: bool
    fits: set[str] = field(default_factory=set)
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
class Route:
    id: str
    label: str
    phrase: str
    exposure: int
    scene: str
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


def severity_of(route: Route, delay: int) -> int:
    return BASE_WIND + route.exposure + delay


def protection_of(cargo: Cargo, container: Container) -> int:
    return cargo.weight + container.cover


def outcome_from_numbers(severity: int, protection: int) -> str:
    if protection > severity:
        return "whole"
    if protection == severity:
        return "partial"
    return "lost"


def fits_container(cargo: Cargo, container: Container) -> bool:
    if cargo.id not in container.fits:
        return False
    if cargo.loose and not container.holds_loose:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cargo_id, cargo in CARGOS.items():
        for container_id, container in CONTAINERS.items():
            if not fits_container(cargo, container):
                continue
            for route_id in ROUTES:
                combos.append((cargo_id, container_id, route_id))
    return combos


def predict_trip(world: World, severity: int, protection: int) -> dict:
    sim = world.copy()
    sim.facts["severity"] = severity
    sim.facts["protection"] = protection
    sim.get("wind").meters["gust"] = float(severity)
    propagate(sim, narrate=False)
    seed = sim.get("seed")
    return {
        "spilled": int(seed.meters["spilled"]),
        "load": int(seed.meters["load"]),
        "outcome": world.facts["outcome_model"](severity, protection),
    }


def _r_scatter(world: World) -> list[str]:
    wind = world.get("wind")
    seed = world.get("seed")
    child = world.get("child")
    road = world.get("road")
    severity = int(world.facts["severity"])
    protection = int(world.facts["protection"])
    if wind.meters["gust"] < THRESHOLD:
        return []
    sig = ("scatter", severity, protection)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if severity <= protection:
        child.memes["courage"] += 1
        return ["__held__"]
    loss = 1 if severity == protection + 1 else 2
    loss = min(loss, int(seed.meters["load"]))
    seed.meters["load"] -= float(loss)
    seed.meters["spilled"] += float(loss)
    road.meters["seed_on_ground"] += float(loss)
    child.memes["fear"] += 1
    child.memes["courage"] += 1
    return ["__scatter__"]


CAUSAL_RULES = [
    Rule(name="scatter", tag="physical", apply=_r_scatter),
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


def introduce(world: World, child: Entity, elder: Entity, cargo: Cargo, container: Container) -> None:
    world.say(
        f"In the old days, when people said even the fields could listen, {child.id} "
        f"lived in a small village at the foot of a hill."
    )
    world.say(
        f"Up on that hill lived {child.pronoun('possessive')} {elder.label_word}, who kept the first "
        f"spring garden for the whole village."
    )
    world.say(
        f"One morning, {child.id} was trusted with {cargo.phrase} tucked inside {container.phrase}, "
        f"to carry up before planting time."
    )


def route_setup(world: World, route: Route) -> None:
    world.say(
        f"The way upward was {route.phrase}, and {route.scene}."
    )


def warning(world: World, child: Entity, cargo: Cargo, container: Container, route: Route, elder: Entity) -> None:
    pred = predict_trip(world, world.facts["severity"], world.facts["protection"])
    world.facts["predicted_spilled"] = pred["spilled"]
    world.facts["predicted_load"] = pred["load"]
    world.facts["predicted_outcome"] = pred["outcome"]
    miller = world.get("miller")
    if pred["spilled"] == 0:
        world.say(
            f'At the mill gate, old {miller.id} looked at the sky and said, '
            f'"Hold {container.label} close. A violent wind is waking, but {container.label} should keep '
            f"the {cargo.label} safe on {route.label}."
        )
    else:
        world.say(
            f'At the mill gate, old {miller.id} looked at the sky and said, '
            f'"A violent wind is waking on {route.label}. Keep {container.label} tight, little one. '
            f"If the gusts grow wild, some of the {cargo.label} may leap away."
        )
    world.say(
        f"{child.id} nodded and thought of {elder.label_word}'s bare garden beds waiting for seed."
    )


def set_out(world: World, child: Entity, route: Route) -> None:
    child.memes["duty"] += 1
    world.say(
        f"So {child.id} set out along {route.label}, walking as carefully as a bell-bearer."
    )


def storm(world: World, child: Entity, cargo: Cargo, container: Container, route: Route) -> None:
    seed = world.get("seed")
    wind = world.get("wind")
    road = world.get("road")
    wind.meters["gust"] = float(world.facts["severity"])
    propagate(world, narrate=False)
    severity = int(world.facts["severity"])
    protection = int(world.facts["protection"])
    if seed.meters["spilled"] >= THRESHOLD:
        spill_n = int(seed.meters["spilled"])
        handful = "a handful" if spill_n == 1 else "two bright handfuls"
        world.say(
            f"Halfway up, the wind came running out of the sky. It was a violent wind, "
            f"hard enough to slap cloaks and bend the reeds beside {route.label}."
        )
        world.say(
            f"{child.id} hugged {container.label} to {child.pronoun('possessive')} chest, but {handful} of "
            f"{cargo.label} flew free and pattered over the ground like tiny beads."
        )
        if seed.meters["load"] > 0:
            world.say(
                f"Still, {child.pronoun().capitalize()} kept hold of what remained and climbed on."
            )
        else:
            world.say(
                f"When the gust passed, {container.label} felt almost empty in {child.pronoun('possessive')} hands."
            )
    else:
        world.say(
            f"Halfway up, the wind came running out of the sky. It was a violent wind, "
            f"hard enough to make the willow leaves turn their pale backs."
        )
        world.say(
            f"But {child.id} bent low, held {container.label} steady, and not a single bit of "
            f"{cargo.label} escaped."
        )
    road.attrs["severity"] = severity
    road.attrs["protection"] = protection


def arrival(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    seed = world.get("seed")
    if seed.meters["load"] > 0:
        seed.meters["delivered"] = seed.meters["load"]
    world.say(
        f"When {child.id} reached the hill cottage, {elder.id} was already standing at the gate, apron "
        f"tied on and spade in hand."
    )
    if seed.meters["load"] > 0:
        world.say(
            f"{child.pronoun('Subject').capitalize() if False else child.id} opened the load and showed "
            f"{elder.pronoun('object')} the {cargo.label} that had made it safely up the hill."
        )
    else:
        world.say(
            f"{child.id} opened {container_phrase(world)} and found almost nothing left inside."
        )


def container_phrase(world: World) -> str:
    return world.facts["container_cfg"].label


def ending_whole(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    elder.memes["gratitude"] += 1
    world.say(
        f'{elder.id} smiled. "Then spring has not lost its way," {elder.pronoun()} said.'
    )
    world.say(
        f"That very evening they pressed the {cargo.label} into the warm earth. Before the sun went down, "
        f"{elder.id} surprised {child.id} with {cargo.gift_food}, saying that brave errands should end with "
        f"something sweet."
    )
    world.say(
        f"People later said the first green points in that garden rose as straight as little candles, because "
        f"{child.id} had carried them with a steady heart."
    )


def ending_partial(world: World, child: Entity, elder: Entity, cargo: Cargo, route: Route) -> None:
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    elder.memes["gratitude"] += 1
    world.say(
        f'{elder.id} counted what remained and nodded. "The hill has enough," {elder.pronoun()} said. '
        f'"The road has taken its share, and perhaps the road will remember."'
    )
    world.say(
        f"They planted what was left before dusk."
    )
    world.say(
        f"Then came the surprise. Weeks later, a bright ribbon of {cargo.bloom} rose all along {route.label}, "
        f"exactly where the wind had scattered the lost seed. From then on, no child climbed that way in spring "
        f"without smiling."
    )


def ending_lost(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    child.memes["sadness"] += 1
    child.memes["wonder"] += 1
    elder.memes["gratitude"] += 1
    village = world.get("village")
    village.meters["shared_seed"] += 1
    world.say(
        f"{child.id}'s eyes filled with tears, but {elder.id} did not scold."
    )
    world.say(
        f'"A wind may be violent," {elder.pronoun()} said softly, "but it is not the strongest thing in a village."'
    )
    world.say(
        f"Then came the surprise. When the church bell rang for supper, neighbors arrived one by one, each with "
        f"a tiny scoop of {cargo.label} saved from winter jars and cupboards, until the old apron was heavy again."
    )
    world.say(
        f"They planted those shared seeds by moonlight, and from that year on people said the hill garden grew so "
        f"well because kindness had been planted there first."
    )
@dataclass
class StoryParams:
    cargo: str
    container: str
    route: str
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
    cargo = world.facts["cargo_cfg"]
    route = world.facts["route_cfg"]
    child = world.facts["child"]
    elder = world.facts["elder"]
    outcome = world.facts["outcome"]
    prompts = [
        f'Write a short folk tale for a 3-to-5-year-old that includes the word "violent" and follows a child carrying {cargo.label} up {route.label}.',
        f"Tell a village tale where {child.id} must bring spring seed to {child.pronoun('possessive')} {elder.label_word} before planting time, and a sudden wind changes the journey.",
    ]
    if outcome == "partial":
        prompts.append(
            f"Write a gentle folk tale with a surprise ending where some seed is lost on the path, and the loss later turns into beauty."
        )
    elif outcome == "lost":
        prompts.append(
            f"Write a folk tale where a violent wind seems to ruin an errand, but the surprise ending shows a whole village helping."
        )
    else:
        prompts.append(
            f"Write a folk tale where a child keeps precious seed safe through a violent wind and is rewarded with a warm surprise at the end."
        )
    return prompts


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    cargo = world.facts["cargo_cfg"]
    container = world.facts["container_cfg"]
    route = world.facts["route_cfg"]
    outcome = world.facts["outcome"]
    spilled = world.facts["spilled_units"]
    delivered = world.facts["delivered_units"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child trusted with spring seed, and {child.pronoun('possessive')} {elder.label_word} on the hill. The errand matters because the elder keeps the first garden for the village.",
        ),
        (
            f"What was {child.id} carrying, and why?",
            f"{child.id} was carrying {cargo.label} in {container.phrase} up to the hill cottage. The seed was needed for the first planting of spring.",
        ),
        (
            f"Why was the trip hard?",
            f"The trip was hard because a violent wind rose while {child.id} was on {route.label}. The wind tested whether {container.label} and {child.pronoun('possessive')} steady hands could protect the seed.",
        ),
    ]
    if outcome == "whole":
        qa.append(
            (
                "What happened when the wind struck?",
                f"Nothing spilled. {child.id} bent low and held the load steady, so all the {cargo.label} reached the hill safely.",
            )
        )
        qa.append(
            (
                "What was the surprise at the end?",
                f"{elder.id} surprised {child.id} with {cargo.gift_food} after they planted the seed. The sweet gift showed that the errand had ended in safety and pride.",
            )
        )
    elif outcome == "partial":
        qa.append(
            (
                "How much was lost, and what changed because of that?",
                f"Some of the seed blew away on the path, but enough still reached the cottage for planting. Weeks later, the lost seed grew into {cargo.bloom} along {route.label}, so the loss turned into a surprise gift for everyone who walked there.",
            )
        )
        qa.append(
            (
                f"Why did {elder.id} say the road would remember?",
                f"{elder.pronoun().capitalize()} said that because the road had caught the spilled seed. Later the flowers proved {elder.pronoun('object')} right by rising exactly where the wind had scattered it.",
            )
        )
    else:
        qa.append(
            (
                "Did the seed make it to the hill?",
                f"No. The wind emptied the load before {child.id} arrived, so there was almost nothing left to plant. That is why {child.id} felt sad at the gate.",
            )
        )
        qa.append(
            (
                "What was the surprise after the loss?",
                f"The neighbors each brought a small scoop of seed from their own homes. Their shared kindness filled the elder's apron and gave the garden a new beginning.",
            )
        )
    qa.append(
        (
            "How did the ending prove that something had changed?",
            (
                "The ending gave the wind an answer. Either the seed reached the hill, or the lost seed became flowers, "
                "or the village turned one child's disappointment into a shared planting."
            ),
        )
    )
    if delivered > 0 and spilled > 0:
        qa.append(
            (
                f"Why could the planting still happen even after the wind?",
                f"Planting could still happen because {child.id} saved part of the load. {delivered} part remained, so the elder still had enough to press into the ground before dark.",
            )
        )
    return qa


KNOWLEDGE = {
    "seed": [
        (
            "What is a seed?",
            "A seed is a tiny beginning for a plant. If it is planted in good soil with water and sun, it can grow into roots, leaves, and flowers or food.",
        )
    ],
    "wind": [
        (
            "What does wind do?",
            "Wind is moving air. It can cool your face, shake leaves, or, if it grows strong, push light things and scatter them.",
        )
    ],
    "poppy": [
        (
            "Why can poppy seed spill easily?",
            "Poppy seed is very small and light. Because the grains are tiny, they can slip through gaps and fly away in a strong gust.",
        )
    ],
    "beans": [
        (
            "Why are bean seeds harder to blow away than tiny seeds?",
            "Bean seeds are bigger and heavier than very tiny seeds. That extra weight makes them easier to keep in place when the wind blows.",
        )
    ],
    "barley": [
        (
            "What is barley?",
            "Barley is a grain plant. People can grind it for food, and farmers also save part of it as seed for the next growing season.",
        )
    ],
    "basket": [
        (
            "What is an open basket good for?",
            "An open basket is good for carrying things that are bigger and easy to see, like beans or apples. It is not the best choice for tiny loose things because they can jump out.",
        )
    ],
    "sack": [
        (
            "Why does a tied sack help?",
            "A tied sack closes around what is inside. That makes it better at keeping seed from spilling when someone walks or when the wind shakes it.",
        )
    ],
    "jar": [
        (
            "Why is a lidded jar safe for small seed?",
            "A lidded jar has firm sides and a top. That helps stop tiny seed from slipping through cracks or blowing out into the air.",
        )
    ],
}
KNOWLEDGE_ORDER = ["seed", "wind", "poppy", "beans", "barley", "basket", "sack", "jar"]


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    cargo = world.facts["cargo_cfg"]
    container = world.facts["container_cfg"]
    route = world.facts["route_cfg"]
    tags = {"seed", "wind"} | set(cargo.tags) | set(container.tags) | set(route.tags)
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(
        f"  severity={world.facts.get('severity')} protection={world.facts.get('protection')} "
        f"outcome={world.facts.get('outcome')}"
    )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cargo="beans",
        container="basket",
        route="willow",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        delay=0,
    ),
    StoryParams(
        cargo="barley",
        container="sack",
        route="market",
        child_name="Ivo",
        child_gender="boy",
        elder_type="grandfather",
        delay=1,
    ),
    StoryParams(
        cargo="poppy",
        container="jar",
        route="ridge",
        child_name="Anya",
        child_gender="girl",
        elder_type="grandmother",
        delay=0,
    ),
    StoryParams(
        cargo="poppy",
        container="sack",
        route="market",
        child_name="Luka",
        child_gender="boy",
        elder_type="grandfather",
        delay=1,
    ),
    StoryParams(
        cargo="poppy",
        container="sack",
        route="ridge",
        child_name="Sela",
        child_gender="girl",
        elder_type="grandmother",
        delay=2,
    ),
]


def explain_rejection(cargo: Cargo, container: Container) -> str:
    if cargo.id not in container.fits:
        return (
            f"(No story: {container.phrase} is not a sensible way to carry {cargo.label} in this world. "
            f"Choose a container that actually fits that seed.)"
        )
    if cargo.loose and not container.holds_loose:
        return (
            f"(No story: {cargo.label} is tiny and loose, but {container.phrase} does not close. "
            f"A violent wind would spill it at once, so the world refuses that carrying method.)"
        )
    return "(No story: this carrying method is not supported.)"


ASP_RULES = r"""
% --- carrying reasonableness -----------------------------------------------
valid(Cg, Ct, Rt) :- cargo(Cg), container(Ct), route(Rt), fits(Ct, Cg), not bad_loose(Cg, Ct).
bad_loose(Cg, Ct) :- loose(Cg), not holds_loose(Ct).

% --- outcome model ----------------------------------------------------------
severity(S)   :- chosen_route(R), exposure(R, E), delay(D), base_wind(B), S = B + E + D.
protection(P) :- chosen_cargo(Cg), chosen_container(Ct), weight(Cg, W), cover(Ct, Cv), P = W + Cv.

outcome(whole)   :- severity(S), protection(P), P > S.
outcome(partial) :- severity(S), protection(P), P = S.
outcome(lost)    :- severity(S), protection(P), P < S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("base_wind", BASE_WIND)]
    for cargo_id, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("weight", cargo_id, cargo.weight))
        if cargo.loose:
            lines.append(asp.fact("loose", cargo_id))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        lines.append(asp.fact("cover", container_id, container.cover))
        if container.holds_loose:
            lines.append(asp.fact("holds_loose", container_id))
        for cargo_id in sorted(container.fits):
            lines.append(asp.fact("fits", container_id, cargo_id))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("exposure", route_id, route.exposure))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_container", params.container),
            asp.fact("chosen_route", params.route),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    cargo = CARGOS[params.cargo]
    container = CONTAINERS[params.container]
    route = ROUTES[params.route]
    return outcome_from_numbers(severity_of(route, params.delay), protection_of(cargo, container))


def asp_verify() -> int:
    rc = 0
    a_set, p_set = set(asp_valid_combos()), set(valid_combos())
    if a_set == p_set:
        print(f"OK: gate matches valid_combos() ({len(a_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_set - p_set:
            print("  only in clingo:", sorted(a_set - p_set))
        if p_set - a_set:
            print("  only in python:", sorted(p_set - a_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
            raise StoryError("empty story from smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: spring seed, a hill path, and a violent wind."
    )
    ap.add_argument("--cargo", choices=sorted(CARGOS))
    ap.add_argument("--container", choices=sorted(CONTAINERS))
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much later the child starts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (cargo, container, route) triples")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.container:
        cargo = CARGOS[args.cargo]
        container = CONTAINERS[args.container]
        if not fits_container(cargo, container):
            raise StoryError(explain_rejection(cargo, container))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.container is None or combo[1] == args.container)
        and (args.route is None or combo[2] == args.route)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, container_id, route_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        cargo=cargo_id,
        container=container_id,
        route=route_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    cargo = CARGOS[params.cargo]
    container = CONTAINERS[params.container]
    route = ROUTES[params.route]
    if not fits_container(cargo, container):
        raise StoryError(explain_rejection(cargo, container))

    world = tell(
        cargo=cargo,
        container=container,
        route=route,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cargo, container, route) triples:\n")
        for cargo, container, route in combos:
            print(f"  {cargo:7} {container:8} {route}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            story_seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(story_seed))
            except StoryError as err:
                print(err)
                return
            params.seed = story_seed
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
            header = (
                f"### {p.child_name}: {p.cargo} in {p.container} by {p.route} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    cargo: Cargo,
    container: Container,
    route: Route,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder_name = "Grandmother" if elder_type == "grandmother" else "Grandfather"
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    miller = world.add(Entity(id="Pavel", kind="character", type="man", role="miller"))
    road = world.add(Entity(id="road", type="road", label=route.label, attrs={"route": route.id}))
    wind = world.add(Entity(id="wind", type="weather", label="the wind"))
    seed = world.add(Entity(id="seed", type="seed", label=cargo.label))
    vessel = world.add(Entity(id="container", type="container", label=container.label))

    seed.meters["load"] = 2.0
    seed.meters["spilled"] = 0.0
    seed.meters["delivered"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["courage"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["sadness"] = 0.0
    elder.memes["gratitude"] = 0.0
    village = world.add(Entity(id="village", type="village", label="the village"))
    village.meters["shared_seed"] = 0.0

    severity = severity_of(route, delay)
    protection = protection_of(cargo, container)
    world.facts["severity"] = severity
    world.facts["protection"] = protection
    world.facts["outcome_model"] = outcome_from_numbers
    world.facts["cargo_cfg"] = cargo
    world.facts["container_cfg"] = container
    world.facts["route_cfg"] = route
    world.facts["delay"] = delay
    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["miller"] = miller
    world.facts["village"] = village

    introduce(world, child, elder, cargo, container)
    route_setup(world, route)

    world.para()
    warning(world, child, cargo, container, route, elder)
    if delay > 0:
        child.memes["worry"] += 1
        world.say(
            f"Yet a late chore at the pump held {child.pronoun('object')} back, and the sky had more time to gather itself."
        )
    set_out(world, child, route)

    world.para()
    storm(world, child, cargo, container, route)
    arrival(world, child, elder, cargo)

    outcome = outcome_from_numbers(severity, protection)
    world.facts["outcome"] = outcome

    world.para()
    if outcome == "whole":
        ending_whole(world, child, elder, cargo)
    elif outcome == "partial":
        ending_partial(world, child, elder, cargo, route)
    else:
        ending_lost(world, child, elder, cargo)

    world.facts["seed"] = seed
    world.facts["road"] = road
    world.facts["wind"] = wind
    world.facts["delivered_units"] = int(seed.meters["delivered"])
    world.facts["spilled_units"] = int(seed.meters["spilled"])
    return world


CARGOS = {
    "beans": Cargo(
        id="beans",
        label="bean seed",
        phrase="a little store of bean seed",
        weight=3,
        loose=False,
        plant_word="beans",
        bloom="white bean blossoms",
        gift_food="a hot honey cake from the hearth",
        tags={"seed", "beans"},
    ),
    "barley": Cargo(
        id="barley",
        label="barley seed",
        phrase="a cloth-wrapped measure of barley seed",
        weight=2,
        loose=False,
        plant_word="barley",
        bloom="soft gold heads of barley",
        gift_food="a warm barley bun glazed with butter",
        tags={"seed", "barley"},
    ),
    "poppy": Cargo(
        id="poppy",
        label="poppy seed",
        phrase="a careful measure of poppy seed",
        weight=1,
        loose=True,
        plant_word="poppies",
        bloom="red poppies",
        gift_food="a poppy bun dusted with sugar",
        tags={"seed", "poppy"},
    ),
}

CONTAINERS = {
    "basket": Container(
        id="basket",
        label="the open basket",
        phrase="an open basket",
        cover=0,
        holds_loose=False,
        fits={"beans", "barley"},
        tags={"basket"},
    ),
    "sack": Container(
        id="sack",
        label="the tied sack",
        phrase="a tied sack",
        cover=1,
        holds_loose=True,
        fits={"beans", "barley", "poppy"},
        tags={"sack"},
    ),
    "jar": Container(
        id="jar",
        label="the clay jar",
        phrase="a clay jar with a lid",
        cover=2,
        holds_loose=True,
        fits={"barley", "poppy"},
        tags={"jar"},
    ),
}

ROUTES = {
    "willow": Route(
        id="willow",
        label="the willow lane",
        phrase="the willow lane under whispering branches",
        exposure=0,
        scene="it bent in and out of shade, with the wind broken by the trees",
        tags={"lane", "wind"},
    ),
    "market": Route(
        id="market",
        label="the market road",
        phrase="the market road between fences and fieldstones",
        exposure=1,
        scene="it was broad and easy, though the wind could find its way there",
        tags={"road", "wind"},
    ),
    "ridge": Route(
        id="ridge",
        label="the ridge path",
        phrase="the ridge path above the reeds",
        exposure=2,
        scene="nothing stood high enough there to hide a traveler from the sky",
        tags={"ridge", "wind"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Toma", "Sela", "Niva", "Rina", "Dora"]
BOY_NAMES = ["Ivo", "Milan", "Petar", "Niko", "Tarin", "Luka", "Borin", "Stefan"]

if __name__ == "__main__":
    main()
