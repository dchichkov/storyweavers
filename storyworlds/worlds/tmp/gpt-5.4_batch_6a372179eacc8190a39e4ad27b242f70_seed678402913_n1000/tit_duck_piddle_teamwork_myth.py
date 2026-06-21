#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tit_duck_piddle_teamwork_myth.py
===========================================================

A standalone storyworld about a tiny mythic rescue: when a thirsty sacred plant
begins to fail, Tit and Duck must carry living water together. Tit is small,
quick, and clever with reeds. Duck is steady, buoyant, and brave in water. The
world only permits stories where both animals are genuinely needed, so the
"Teamwork" feature is built into the reasonableness gate itself.

Seed words and instruments
--------------------------
Words: tit, duck, piddle
Feature: Teamwork
Style: Myth

Run it
------
    python storyworlds/worlds/gpt-5.4/tit_duck_piddle_teamwork_myth.py
    python storyworlds/worlds/gpt-5.4/tit_duck_piddle_teamwork_myth.py --source spring --vessel reed_cup --obstacle marsh
    python storyworlds/worlds/gpt-5.4/tit_duck_piddle_teamwork_myth.py --source dew_web
    python storyworlds/worlds/gpt-5.4/tit_duck_piddle_teamwork_myth.py --all
    python storyworlds/worlds/gpt-5.4/tit_duck_piddle_teamwork_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tit_duck_piddle_teamwork_myth.py --verify
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
PLANT_NEED = 2
TIT_SKILL = "tit"
DUCK_SKILL = "duck"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        neut = {"subject": "they", "object": "them", "possessive": "their"}
        return neut[case]


@dataclass
class Source:
    id: str = ""
    label: str = ""
    phrase: str = ""
    myth_line: str = ""
    amount: int = 0
    source_word: str = "water"
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str = ""
    label: str = ""
    phrase: str = ""
    capacity: int = 0
    needs_tit: bool = False
    fix_text: str = ""
    carry_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str = ""
    label: str = ""
    phrase: str = ""
    requires: set[str] = field(default_factory=set)
    risk_text: str = ""
    duck_text: str = ""
    tit_text: str = ""
    together_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SacredPlant:
    id: str = ""
    label: str = ""
    phrase: str = ""
    image: str = ""
    need: int = PLANT_NEED
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    source: str
    vessel: str
    obstacle: str
    plant: str
    tit_name: str
    duck_name: str
    seed: Optional[int] = None


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
    apply: Callable[[World], list[str]]


def _r_wilt(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["water"] >= THRESHOLD:
        return []
    sig = ("wilt", plant.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["wilt"] += 1
    for eid in ("tit", "duck"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    return ["__wilt__"]


def _r_restore(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["water"] < plant.attrs.get("need", PLANT_NEED):
        return []
    sig = ("restore", plant.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["bloom"] += 1
    plant.meters["wilt"] = 0.0
    for eid in ("tit", "duck"):
        if eid in world.entities:
            world.get(eid).memes["joy"] += 1
            world.get(eid).memes["bond"] += 1
    return ["__restore__"]


CAUSAL_RULES = [
    Rule(name="wilt", apply=_r_wilt),
    Rule(name="restore", apply=_r_restore),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


SOURCES = {
    "spring": Source(
        id="spring",
        label="moon spring",
        phrase="the moon spring",
        myth_line="From a crack in the hill came a silver piddle of water, thin as a string and bright as a star.",
        amount=2,
        source_word="piddle",
        tags={"spring", "water"},
    ),
    "rain_stone": Source(
        id="rain_stone",
        label="rain stone",
        phrase="the rain stone",
        myth_line="Under an old stone, last night's rain still waited in a clear little cup.",
        amount=2,
        source_word="rainwater",
        tags={"rain", "water"},
    ),
    "dew_web": Source(
        id="dew_web",
        label="dew web",
        phrase="the dew web",
        myth_line="A spider web held beads of dawn, but only a few trembling drops.",
        amount=1,
        source_word="dew",
        tags={"dew", "water"},
    ),
}

VESSELS = {
    "reed_cup": Vessel(
        id="reed_cup",
        label="reed cup",
        phrase="a hollow reed cup",
        capacity=2,
        needs_tit=True,
        fix_text="Tit braided two grass threads around the reed cup so its split side would hold.",
        carry_text="Duck balanced the reed cup on Duck's broad back and kept it level with slow, careful strokes.",
        tags={"reed", "cup"},
    ),
    "lotus_bowl": Vessel(
        id="lotus_bowl",
        label="lotus bowl",
        phrase="a folded lotus bowl",
        capacity=2,
        needs_tit=True,
        fix_text="Tit pinned the lotus bowl with a thorn and a grass knot so it would not open in the water.",
        carry_text="Duck floated the lotus bowl between Duck's wings and pushed it along like a small green boat.",
        tags={"lotus", "bowl"},
    ),
    "acorn_cap": Vessel(
        id="acorn_cap",
        label="acorn cap",
        phrase="an acorn cap",
        capacity=1,
        needs_tit=False,
        fix_text="",
        carry_text="Duck could carry the little cap, but it held only a sip.",
        tags={"acorn", "cup"},
    ),
}

OBSTACLES = {
    "marsh": Obstacle(
        id="marsh",
        label="reed marsh",
        phrase="the reed marsh",
        requires={TIT_SKILL, DUCK_SKILL},
        risk_text="Between the hill and the plant lay a cold marsh where mud tugged at feet and the water shook every small thing apart.",
        duck_text="Duck knew how to cross the sucking water without sinking.",
        tit_text="Tit knew how to tie and steady what the water would spill.",
        together_text="So Tit worked above the water while Duck worked within it, and the two small helpers made one wise path.",
        tags={"marsh", "waterway"},
    ),
    "brook": Obstacle(
        id="brook",
        label="singing brook",
        phrase="the singing brook",
        requires={DUCK_SKILL},
        risk_text="A fast brook cut the meadow in two and slapped sharp little waves against any cargo.",
        duck_text="Duck could ride the current without fear.",
        tit_text="Tit had quick eyes, but no knot was needed there.",
        together_text="",
        tags={"brook", "waterway"},
    ),
    "wind_bridge": Obstacle(
        id="wind_bridge",
        label="wind bridge",
        phrase="the wind bridge",
        requires={TIT_SKILL},
        risk_text="A narrow root arched over a ditch, and the hill wind liked to toss light things from it.",
        duck_text="Duck was steady, but there was no water there to use Duck's gift.",
        tit_text="Tit could fasten and guide a light vessel through the gusts.",
        together_text="",
        tags={"wind", "bridge"},
    ),
}

PLANTS = {
    "sun_lily": SacredPlant(
        id="sun_lily",
        label="Sun Lily",
        phrase="the Sun Lily",
        image="its gold face had bowed and its bright edges had gone dull",
        need=2,
        tags={"flower", "sun"},
    ),
    "dawn_reed": SacredPlant(
        id="dawn_reed",
        label="Dawn Reed",
        phrase="the Dawn Reed",
        image="its red tassels hung low, as if morning had forgotten them",
        need=2,
        tags={"reed", "dawn"},
    ),
}

TIT_NAMES = ["Tit", "Little Tit", "Ash Tit"]
DUCK_NAMES = ["Duck", "River Duck", "Moss Duck"]


def requires_teamwork(vessel: Vessel, obstacle: Obstacle) -> bool:
    return vessel.needs_tit and TIT_SKILL in obstacle.requires and DUCK_SKILL in obstacle.requires


def enough_water(source: Source, vessel: Vessel, plant: SacredPlant) -> bool:
    return source.amount >= plant.need and vessel.capacity >= plant.need


def valid_combo(source_id: str, vessel_id: str, obstacle_id: str, plant_id: str) -> bool:
    if source_id not in SOURCES or vessel_id not in VESSELS or obstacle_id not in OBSTACLES or plant_id not in PLANTS:
        return False
    source = SOURCES[source_id]
    vessel = VESSELS[vessel_id]
    obstacle = OBSTACLES[obstacle_id]
    plant = PLANTS[plant_id]
    return enough_water(source, vessel, plant) and requires_teamwork(vessel, obstacle)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for source_id in SOURCES:
        for vessel_id in VESSELS:
            for obstacle_id in OBSTACLES:
                for plant_id in PLANTS:
                    if valid_combo(source_id, vessel_id, obstacle_id, plant_id):
                        out.append((source_id, vessel_id, obstacle_id, plant_id))
    return out


def explain_rejection(source: Source, vessel: Vessel, obstacle: Obstacle, plant: SacredPlant) -> str:
    if source.amount < plant.need:
        return (
            f"(No story: {source.phrase} offers only {source.amount} sip"
            f"{'' if source.amount == 1 else 's'}, but {plant.phrase} needs {plant.need}. "
            f"The rescue would fail before the ending.)"
        )
    if vessel.capacity < plant.need:
        return (
            f"(No story: {vessel.phrase} is too small to carry enough water for {plant.phrase}. "
            f"The world prefers a vessel that can truly save the plant.)"
        )
    if not vessel.needs_tit:
        return (
            f"(No story: {vessel.phrase} does not need Tit's knot-work, so the plan would not truly be teamwork.)"
        )
    if DUCK_SKILL not in obstacle.requires:
        return (
            f"(No story: {obstacle.phrase} does not need Duck's water-skill, so the teamwork would be weak.)"
        )
    if TIT_SKILL not in obstacle.requires:
        return (
            f"(No story: {obstacle.phrase} does not need Tit's help, so the rescue would not require both friends.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


def intro(world: World, tit: Entity, duck: Entity, plant: Entity, plant_cfg: SacredPlant) -> None:
    world.say(
        f"In the first mornings, when small creatures still spoke to roots and clouds, "
        f"{tit.id} lived in the reeds and {duck.id} lived on the river bend."
    )
    world.say(
        f"They both loved {plant_cfg.phrase}, because it lit the marsh at dawn, "
        f"yet now {plant_cfg.image}."
    )
    propagate(world, narrate=False)


def omen(world: World, tit: Entity, duck: Entity, obstacle: Obstacle) -> None:
    world.say(
        f'"If {world.get("plant").label} drinks no more today, dawn will come in a poorer color," said {tit.id}.'
    )
    world.say(obstacle.risk_text)


def find_source(world: World, source: Source) -> None:
    world.say(source.myth_line)
    if source.source_word == "piddle":
        world.say("It was only a piddle, but living water in a thirsty hour is never a small thing.")


def plan(world: World, tit: Entity, duck: Entity, vessel: Vessel, obstacle: Obstacle, source: Source) -> None:
    tit.memes["resolve"] += 1
    duck.memes["resolve"] += 1
    world.say(
        f'"We cannot leave this to one pair of wings," said {duck.id}. '
        f'"You have the quick craft, and I have the steady back."'
    )
    world.say(
        f'Together they chose {vessel.phrase} and knelt beside {source.phrase}.'
    )
    world.say(obstacle.duck_text)
    world.say(obstacle.tit_text)


def prepare_vessel(world: World, tit: Entity, vessel: Vessel) -> None:
    if vessel.needs_tit:
        tit.meters["craft"] += 1
        world.say(vessel.fix_text)


def fill_vessel(world: World, source: Source, vessel: Vessel) -> None:
    water = min(source.amount, vessel.capacity)
    world.get("vessel").meters["water"] = float(water)
    world.say(
        f"They caught {water} shining mouthfuls from {source.phrase} in {vessel.phrase}."
    )


def cross_obstacle(world: World, tit: Entity, duck: Entity, vessel: Vessel, obstacle: Obstacle) -> None:
    duck.meters["carry"] += 1
    tit.meters["guide"] += 1
    world.say(vessel.carry_text)
    world.say(obstacle.together_text)
    world.say(
        f"{tit.id} flew just above the ripples, calling the calm way, while {duck.id} moved below with patient strength."
    )
    world.get("vessel").meters["arrived"] += 1
    world.facts["teamwork_used"] = True


def water_plant(world: World, plant_cfg: SacredPlant) -> None:
    vessel = world.get("vessel")
    plant = world.get("plant")
    if vessel.meters["arrived"] < THRESHOLD:
        return
    plant.meters["water"] += vessel.meters["water"]
    vessel.meters["water"] = 0.0
    propagate(world, narrate=False)
    if plant.meters["bloom"] >= THRESHOLD:
        world.say(
            f"They tipped the water at the roots of {plant_cfg.phrase}. "
            f"The earth drank first, then the stem, and then the whole plant lifted itself as if it had remembered its own song."
        )
        world.say(
            f"Soon {plant_cfg.phrase} stood bright again, and the marsh took back its color."
        )


def ending(world: World, tit: Entity, duck: Entity, plant_cfg: SacredPlant) -> None:
    tit.memes["peace"] += 1
    duck.memes["peace"] += 1
    world.say(
        f"After that day, the old creatures said morning was never made by the sun alone."
    )
    world.say(
        f"It was also made by a tit with a clever knot, a duck with a faithful back, "
        f"and the kindness that let two small strengths become one saving deed."
    )
    world.say(
        f"And when children saw {plant_cfg.phrase} shining over the water, they remembered to work together."
    )


def tell(
    source: Source,
    vessel: Vessel,
    obstacle: Obstacle,
    plant_cfg: SacredPlant,
    tit_name: str,
    duck_name: str,
) -> World:
    world = World()
    tit = world.add(Entity(id="tit", kind="character", type="bird", label="tit", phrase=tit_name, role="helper"))
    duck = world.add(Entity(id="duck", kind="character", type="bird", label="duck", phrase=duck_name, role="helper"))
    plant = world.add(
        Entity(
            id="plant",
            kind="thing",
            type="plant",
            label=plant_cfg.label,
            phrase=plant_cfg.phrase,
            attrs={"need": plant_cfg.need},
            tags=set(plant_cfg.tags),
        )
    )
    vessel_ent = world.add(Entity(id="vessel", kind="thing", type="vessel", label=vessel.label, phrase=vessel.phrase))
    tit.id = tit_name
    duck.id = duck_name
    world.entities["tit"] = tit
    world.entities["duck"] = duck

    intro(world, tit, duck, plant, plant_cfg)
    world.para()
    omen(world, tit, duck, obstacle)
    find_source(world, source)
    world.para()
    plan(world, tit, duck, vessel, obstacle, source)
    prepare_vessel(world, tit, vessel)
    fill_vessel(world, source, vessel)
    cross_obstacle(world, tit, duck, vessel, obstacle)
    world.para()
    water_plant(world, plant_cfg)
    ending(world, tit, duck, plant_cfg)

    world.facts.update(
        source=source,
        vessel_cfg=vessel,
        obstacle=obstacle,
        plant_cfg=plant_cfg,
        tit=tit,
        duck=duck,
        vessel=vessel_ent,
        teamwork=bool(world.facts.get("teamwork_used")),
        restored=plant.meters["bloom"] >= THRESHOLD,
        water_delivered=int(plant.meters["water"]),
    )
    return world


KNOWLEDGE = {
    "tit": [
        (
            "What is a tit?",
            "A tit is a very small songbird. It is light and quick, so in stories it often stands for alertness and cleverness.",
        )
    ],
    "duck": [
        (
            "Why is a duck good in water?",
            "A duck's body floats well and its feet paddle strongly. That is why a duck can carry things across water more safely than many other birds.",
        )
    ],
    "piddle": [
        (
            "What does piddle mean in this story?",
            "Here piddle means a very small trickle or tiny bit of water. The story uses it in an old-fashioned, myth-like way.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means two or more friends using different strengths for one job. Each helper does the part they are best at, and together they can do more than either one alone.",
        )
    ],
    "marsh": [
        (
            "What is a marsh?",
            "A marsh is wet ground with shallow water and reeds. It can be soft and tricky to cross because the mud pulls at your feet.",
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that comes up from the ground by itself. People in stories often treat springs as special because they seem to rise like a gift from the earth.",
        )
    ],
    "lotus": [
        (
            "What is a lotus?",
            "A lotus is a water plant with broad leaves and bright flowers. Its leaves can hold drops of water because their surface is smooth and wide.",
        )
    ],
}
KNOWLEDGE_ORDER = ["tit", "duck", "piddle", "teamwork", "marsh", "spring", "lotus"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    source = f["source"]
    vessel = f["vessel_cfg"]
    obstacle = f["obstacle"]
    plant = f["plant_cfg"]
    tit = f["tit"]
    duck = f["duck"]
    return [
        'Write a short child-facing myth that includes the words "tit", "duck", and "piddle".',
        f"Tell a myth where {tit.id} and {duck.id} must save {plant.phrase} by carrying water from {source.phrase} through {obstacle.phrase} using {vessel.phrase}.",
        "Write a teamwork story in a gentle myth style where two small creatures combine different gifts to restore something living.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tit = f["tit"]
    duck = f["duck"]
    source = f["source"]
    vessel = f["vessel_cfg"]
    obstacle = f["obstacle"]
    plant = f["plant_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {tit.id} and {duck.id}, two small friends who tried to save {plant.phrase}. They used different gifts, so the story is really about helping together.",
        ),
        (
            f"Why were {tit.id} and {duck.id} worried?",
            f"They were worried because {plant.phrase} was thirsty and drooping. If it drank no more water that day, the bright dawn-place around it would lose its color.",
        ),
        (
            f"What water did they find?",
            f"They found water at {source.phrase}. In this story it was only a {source.source_word if source.source_word == 'piddle' else 'little store of water'}, which made their careful plan even more important.",
        ),
        (
            f"Why did they need both {tit.id} and {duck.id}?",
            f"They needed {tit.id} to prepare and steady {vessel.phrase}, and they needed {duck.id} to carry it through {obstacle.phrase}. One friend had the craft and the other had the strength for water, so neither could have finished the rescue alone.",
        ),
    ]
    if f.get("restored"):
        qa.append(
            (
                f"How did they save {plant.phrase}?",
                f"They caught enough water in {vessel.phrase}, crossed {obstacle.phrase}, and poured it at the roots of {plant.phrase}. Because the plan held together all the way, the plant could drink and stand bright again.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {plant.phrase} shining again over the water. The ending image proves that teamwork changed the world around the friends, not just their feelings.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"tit", "duck", "teamwork"}
    if f["source"].id == "spring":
        tags.add("spring")
        tags.add("piddle")
    if f["obstacle"].id == "marsh":
        tags.add("marsh")
    if "lotus" in f["vessel_cfg"].tags:
        tags.add("lotus")
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        source="spring",
        vessel="reed_cup",
        obstacle="marsh",
        plant="sun_lily",
        tit_name="Little Tit",
        duck_name="River Duck",
    ),
    StoryParams(
        source="rain_stone",
        vessel="lotus_bowl",
        obstacle="marsh",
        plant="dawn_reed",
        tit_name="Ash Tit",
        duck_name="Moss Duck",
    ),
    StoryParams(
        source="spring",
        vessel="lotus_bowl",
        obstacle="marsh",
        plant="dawn_reed",
        tit_name="Tit",
        duck_name="Duck",
    ),
]


ASP_RULES = r"""
enough_water(S, V, P) :- source(S), vessel(V), plant(P),
                         amount(S, A), capacity(V, C), need(P, N),
                         A >= N, C >= N.

requires_teamwork(V, O) :- vessel(V), obstacle(O),
                           needs_tit(V),
                           requires(O, tit),
                           requires(O, duck).

valid(S, V, O, P) :- source(S), vessel(V), obstacle(O), plant(P),
                     enough_water(S, V, P),
                     requires_teamwork(V, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("amount", sid, source.amount))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        lines.append(asp.fact("capacity", vid, vessel.capacity))
        if vessel.needs_tit:
            lines.append(asp.fact("needs_tit", vid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        for req in sorted(obstacle.requires):
            lines.append(asp.fact("requires", oid, req))
    for pid, plant in PLANTS.items():
        lines.append(asp.fact("plant", pid))
        lines.append(asp.fact("need", pid, plant.need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        params = resolve_params(default_args, random.Random(123))
        smoke_cases.append(params)
    except Exception as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params crashed: {err}")
        smoke_cases = list(CURATED)

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            print(f"OK: smoke story {idx} generated.")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL on story {idx}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic teamwork storyworld with Tit and Duck carrying living water."
    )
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--vessel", choices=sorted(VESSELS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--plant", choices=sorted(PLANTS))
    ap.add_argument("--tit-name")
    ap.add_argument("--duck-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    source_id = args.source
    vessel_id = args.vessel
    obstacle_id = args.obstacle
    plant_id = args.plant

    if all(x is not None for x in (source_id, vessel_id, obstacle_id, plant_id)):
        if not valid_combo(source_id, vessel_id, obstacle_id, plant_id):
            raise StoryError(
                explain_rejection(
                    SOURCES[source_id],
                    VESSELS[vessel_id],
                    OBSTACLES[obstacle_id],
                    PLANTS[plant_id],
                )
            )

    combos = [
        combo
        for combo in valid_combos()
        if (source_id is None or combo[0] == source_id)
        and (vessel_id is None or combo[1] == vessel_id)
        and (obstacle_id is None or combo[2] == obstacle_id)
        and (plant_id is None or combo[3] == plant_id)
    ]
    if not combos:
        src = SOURCES[source_id] if source_id in SOURCES else next(iter(SOURCES.values()))
        ves = VESSELS[vessel_id] if vessel_id in VESSELS else next(iter(VESSELS.values()))
        obs = OBSTACLES[obstacle_id] if obstacle_id in OBSTACLES else next(iter(OBSTACLES.values()))
        pln = PLANTS[plant_id] if plant_id in PLANTS else next(iter(PLANTS.values()))
        raise StoryError(explain_rejection(src, ves, obs, pln))

    chosen_source, chosen_vessel, chosen_obstacle, chosen_plant = rng.choice(sorted(combos))
    tit_name = args.tit_name or rng.choice(TIT_NAMES)
    duck_name = args.duck_name or rng.choice([n for n in DUCK_NAMES if n != tit_name])

    return StoryParams(
        source=chosen_source,
        vessel=chosen_vessel,
        obstacle=chosen_obstacle,
        plant=chosen_plant,
        tit_name=tit_name,
        duck_name=duck_name,
    )


def _validate_params(params: StoryParams) -> None:
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.vessel not in VESSELS:
        raise StoryError(f"(No story: unknown vessel '{params.vessel}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.plant not in PLANTS:
        raise StoryError(f"(No story: unknown plant '{params.plant}'.)")
    if not valid_combo(params.source, params.vessel, params.obstacle, params.plant):
        raise StoryError(
            explain_rejection(
                SOURCES[params.source],
                VESSELS[params.vessel],
                OBSTACLES[params.obstacle],
                PLANTS[params.plant],
            )
        )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        source=SOURCES[params.source],
        vessel=VESSELS[params.vessel],
        obstacle=OBSTACLES[params.obstacle],
        plant_cfg=PLANTS[params.plant],
        tit_name=params.tit_name,
        duck_name=params.duck_name,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (source, vessel, obstacle, plant) combos:\n")
        for source_id, vessel_id, obstacle_id, plant_id in combos:
            print(f"  {source_id:10} {vessel_id:10} {obstacle_id:11} {plant_id}")
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
            header = f"### {p.source}, {p.vessel}, {p.obstacle}, {p.plant}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
