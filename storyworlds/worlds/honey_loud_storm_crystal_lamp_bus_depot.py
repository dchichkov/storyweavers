#!/usr/bin/env python3
"""
storyworlds/worlds/honey_loud_storm_crystal_lamp_bus_depot.py
==============================================================

A standalone story world for a TinyStories-style prompt:

    Words: honey, loud storm, crystal lamp
    Setting: bus depot
    Features: Dialogue
    Style: Folk Tale

Source tale behind the simulation:
    On a stormy evening at a village bus depot, a child carrying honey sees a
    crystal lamp flash and shiver above the benches. A tired bee has hidden in
    the lamp from the weather, so the moving light looks like a storm spirit.
    The child and an older helper use honey to lure the bee safely to an open
    ledge, the lamp grows calm again, and the waiting bus can leave.

The world model keeps that tale physical: storm + hanging lamp + trapped bee
create the frightening sign, and the honey plan only works when the depot has a
reachable ledge for the lure.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Depot:
    id: str
    place: str
    village: str
    supports: frozenset[str]
    opening: str
    waiting_place: str
    ending_image: str


@dataclass(frozen=True)
class Storm:
    id: str
    phrase: str
    loud: bool
    gusty: bool
    roof_sound: str
    window_line: str


@dataclass(frozen=True)
class Lamp:
    id: str
    phrase: str
    crystal: bool
    hanging: bool
    color: str
    flare_line: str


@dataclass(frozen=True)
class Bee:
    id: str
    phrase: str
    likes_honey: bool
    sound: str
    shelter_line: str


@dataclass(frozen=True)
class HoneyPlan:
    id: str
    perch: str
    bait: str
    setup_line: str
    helper_job: str
    success_line: str


@dataclass(frozen=True)
class HelperRole:
    id: str
    title: str
    intro_line: str
    wisdom_line: str


class World:
    def __init__(self, depot: Depot) -> None:
        self.depot = depot
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.depot)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def role(world: World, name: str) -> Optional[Entity]:
    return next((e for e in world.entities.values() if e.role == name), None)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_storm_rattles_lamp(world: World) -> list[str]:
    storm = world.entities.get("storm")
    lamp = world.entities.get("lamp")
    if not storm or not lamp:
        return []
    if storm.meters["arrived"] < THRESHOLD:
        return []
    if lamp.meters["hanging"] < THRESHOLD:
        return []
    if storm.meters["gusts"] < THRESHOLD:
        return []
    sig = ("rattle", storm.id, lamp.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lamp.meters["swinging"] += 1
    lamp.memes["unease"] += 1
    return ["rattle"]


def _r_bee_hides_in_lamp(world: World) -> list[str]:
    storm = world.entities.get("storm")
    lamp = world.entities.get("lamp")
    bee = world.entities.get("bee")
    if not storm or not lamp or not bee:
        return []
    if storm.meters["arrived"] < THRESHOLD:
        return []
    if lamp.meters["warm"] < THRESHOLD:
        return []
    if bee.meters["shelter_seeking"] < THRESHOLD:
        return []
    sig = ("bee_hides", storm.id, lamp.id, bee.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bee.meters["inside_lamp"] += 1
    lamp.meters["glittering_strangely"] += 1
    return ["bee_hides"]


def _r_false_spirit(world: World) -> list[str]:
    hero = role(world, "hero")
    helper = role(world, "helper")
    lamp = world.entities.get("lamp")
    bee = world.entities.get("bee")
    depot = world.entities.get("depot")
    bus = world.entities.get("bus")
    if not hero or not helper or not lamp or not bee or not depot or not bus:
        return []
    if lamp.meters["swinging"] < THRESHOLD or bee.meters["inside_lamp"] < THRESHOLD:
        return []
    sig = ("false_spirit", lamp.id, bee.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["wonder"] += 1
    helper.memes["concern"] += 1
    depot.memes["rumor"] += 1
    bus.meters["waiting"] += 1
    return ["false_spirit"]


def _r_honey_lure(world: World) -> list[str]:
    hero = role(world, "hero")
    helper = role(world, "helper")
    bee = world.entities.get("bee")
    honey = world.entities.get("honey")
    lamp = world.entities.get("lamp")
    depot = world.entities.get("depot")
    bus = world.entities.get("bus")
    if not hero or not helper or not bee or not honey or not lamp or not depot or not bus:
        return []
    if bee.meters["inside_lamp"] < THRESHOLD:
        return []
    if honey.meters["offered"] < THRESHOLD:
        return []
    if depot.meters["perch_ready"] < THRESHOLD:
        return []
    if helper.meters["steadying_lamp"] < THRESHOLD:
        return []
    sig = ("honey_lure", bee.id, honey.id, depot.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bee.meters["inside_lamp"] = 0.0
    bee.meters["at_honey"] += 1
    lamp.meters["swinging"] = 0.0
    lamp.meters["glittering_strangely"] = 0.0
    lamp.memes["unease"] = 0.0
    depot.memes["rumor"] = 0.0
    depot.meters["peace"] += 1
    hero.memes["courage"] += 1
    hero.memes["care"] += 1
    helper.memes["relief"] += 1
    bus.meters["waiting"] = 0.0
    bus.meters["departing"] += 1
    return ["honey_lure"]


CAUSAL_RULES = [
    Rule("storm_rattles_lamp", "physical", _r_storm_rattles_lamp),
    Rule("bee_hides_in_lamp", "physical", _r_bee_hides_in_lamp),
    Rule("false_spirit", "social", _r_false_spirit),
    Rule("honey_lure", "resolution", _r_honey_lure),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) > before:
                changed = True


DEPOTS = {
    "cedar": Depot(
        "cedar",
        "the Cedar Bus Depot",
        "Cedar Hollow",
        frozenset({"window_sill", "door_latch"}),
        "rainwater dripped from the eaves into a crooked barrel",
        "the long wooden bench",
        "the bus rolled out while the lamp shone clear as a winter drop",
    ),
    "river": Depot(
        "river",
        "the River Reed Bus Depot",
        "River Reed",
        frozenset({"bench_corner", "door_latch"}),
        "puddles on the floor held small trembling moons",
        "the painted bench by the timetable",
        "the bus rolled away while the wet road kept a ribbon of golden light",
    ),
    "hill": Depot(
        "hill",
        "the Hilltop Bus Depot",
        "Hilltop",
        frozenset({"window_sill", "bench_corner"}),
        "wind combed the prayer flags tied beside the roof posts",
        "the high bench near the ticket window",
        "the bus groaned into motion while the clear lamp rested like a tame star",
    ),
}

STORMS = {
    "thunder": Storm(
        "thunder",
        "a loud thunderstorm",
        True,
        True,
        "The loud storm drummed on the depot roof as if a hundred hands were asking to come in.",
        "The windowpanes trembled each time thunder rolled across the village.",
    ),
    "hail": Storm(
        "hail",
        "a loud hail storm",
        True,
        True,
        "The loud storm flung hard beads of hail against the roof until the whole depot rang.",
        "The glass shook and clicked beneath the noisy gusts.",
    ),
    "sea_squall": Storm(
        "sea_squall",
        "a loud sea-wind storm",
        True,
        True,
        "The loud storm came up from the marsh road and boomed around the depot like a drum.",
        "The shutters snapped and the wet air rushed through the cracks.",
    ),
    "soft_rain": Storm(
        "soft_rain",
        "a soft rain",
        False,
        False,
        "Soft rain tapped politely at the roof.",
        "The windows only hummed a little.",
    ),
}

LAMPS = {
    "blue_crystal": Lamp(
        "blue_crystal",
        "a blue crystal lamp",
        True,
        True,
        "blue",
        "The blue crystal lamp swung and scattered broken bits of sky-colored light across the floor.",
    ),
    "amber_crystal": Lamp(
        "amber_crystal",
        "an amber crystal lamp",
        True,
        True,
        "amber",
        "The amber crystal lamp shivered overhead and tossed honey-colored sparks from wall to wall.",
    ),
    "star_cut_crystal": Lamp(
        "star_cut_crystal",
        "a star-cut crystal lamp",
        True,
        True,
        "silver",
        "The star-cut crystal lamp rattled in its chain and flashed so quickly that even the timetable seemed alive.",
    ),
    "plain_lantern": Lamp(
        "plain_lantern",
        "a plain station lantern",
        False,
        False,
        "plain",
        "The plain station lantern glowed in one steady puddle of light.",
    ),
}

BEES = {
    "honeybee": Bee(
        "honeybee",
        "a small honeybee",
        True,
        "a thin golden buzz",
        "A small honeybee had tucked itself inside the warm glass to escape the rain.",
    ),
    "bumblebee": Bee(
        "bumblebee",
        "a round bumblebee",
        True,
        "a velvet little hum",
        "A round bumblebee had blundered into the lamp for shelter from the weather.",
    ),
    "orchard_bee": Bee(
        "orchard_bee",
        "an orchard bee",
        True,
        "a quick bright hum",
        "An orchard bee had hidden in the lamp where the storm could not soak its wings.",
    ),
    "paper_wasp": Bee(
        "paper_wasp",
        "a paper wasp",
        False,
        "a sharp dry whirr",
        "A paper wasp had flown too close to the chain.",
    ),
}

PLANS = {
    "sill_saucer": HoneyPlan(
        "sill_saucer",
        "window_sill",
        "a saucer of honey on the window sill",
        "set a little saucer of honey on the window sill",
        "hold the lamp chain still with both steady hands",
        "The bee turned from the lamp, tasted the sweet scent, and flew to the sill where the rain had gentled.",
    ),
    "door_spoon": HoneyPlan(
        "door_spoon",
        "door_latch",
        "a spoon of honey by the depot door",
        "rest a spoon of honey by the open depot door",
        "cup the crystal lamp so it could stop swinging",
        "The bee followed the honey smell to the open door and slipped into the bright wet evening.",
    ),
    "bench_crust": HoneyPlan(
        "bench_crust",
        "bench_corner",
        "a bread crust brushed with honey on the bench corner",
        "brush honey on a bread crust and place it on the bench corner",
        "steady the lamp while the bench stayed dry beneath it",
        "The bee crawled to the honeyed crust, then lifted itself into the calmer air above the bench.",
    ),
}

HELPER_ROLES = {
    "keeper": HelperRole(
        "keeper",
        "the ticket keeper",
        "the ticket keeper kept the copper key box and knew every timetable by heart",
        "Old hands should hold what shakes, and young eyes should watch what moves.",
    ),
    "driver": HelperRole(
        "driver",
        "the night bus driver",
        "the night bus driver had one boot on the step and one on the wet stones",
        "A road clears faster when two people mind one trouble together.",
    ),
    "seller": HelperRole(
        "seller",
        "the bun seller",
        "the bun seller watched over a basket that smelled of warm flour and rain",
        "Sweetness can guide a frightened creature more gently than fear can.",
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tala", "Nora", "Asha", "Ruth"]
BOY_NAMES = ["Ivo", "Milan", "Pavel", "Niko", "Oren", "Sami"]
TRAITS = ["patient", "brave", "careful", "kind", "quick-eyed"]


def storm_valid(storm: Storm) -> bool:
    return storm.loud and storm.gusty


def lamp_valid(lamp: Lamp) -> bool:
    return lamp.crystal and lamp.hanging


def bee_valid(bee: Bee) -> bool:
    return bee.likes_honey


def plan_fits(depot: Depot, plan: HoneyPlan) -> bool:
    return plan.perch in depot.supports


def valid_combo(depot: Depot, storm: Storm, lamp: Lamp, bee: Bee, plan: HoneyPlan) -> bool:
    return (
        storm_valid(storm)
        and lamp_valid(lamp)
        and bee_valid(bee)
        and plan_fits(depot, plan)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for depot_id, depot in DEPOTS.items():
        for storm_id, storm in STORMS.items():
            for lamp_id, lamp in LAMPS.items():
                for bee_id, bee in BEES.items():
                    for plan_id, plan in PLANS.items():
                        if valid_combo(depot, storm, lamp, bee, plan):
                            combos.append((depot_id, storm_id, lamp_id, bee_id, plan_id))
    return sorted(combos)


def _sentence(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


@dataclass
class StoryParams:
    depot: str
    storm: str
    lamp: str
    bee: str
    plan: str
    helper_role: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


def introduce(
    world: World,
    hero: Entity,
    helper: Entity,
    storm: Storm,
    lamp: Lamp,
    helper_role: HelperRole,
) -> None:
    world.say(
        f"In {world.depot.village}, people still tell of the evening when {hero.id}, "
        f"a {hero.traits[0]} child, waited at {world.depot.place} with a jar of honey."
    )
    world.say(
        f"Beside {hero.id} stood {helper.id}, and {helper_role.intro_line}. "
        f"Above {world.depot.waiting_place} hung {lamp.phrase}."
    )
    world.say(_sentence(world.depot.opening) + ".")
    world.say(storm.roof_sound)
    world.say(storm.window_line)


def awaken_world(world: World, storm: Storm, lamp: Lamp, bee: Bee) -> None:
    storm_ent = world.get("storm")
    lamp_ent = world.get("lamp")
    bee_ent = world.get("bee")
    storm_ent.meters["arrived"] += 1
    if storm.gusty:
        storm_ent.meters["gusts"] += 1
    if lamp.hanging:
        lamp_ent.meters["hanging"] += 1
    lamp_ent.meters["warm"] += 1
    bee_ent.meters["shelter_seeking"] += 1
    propagate(world)
    world.say(lamp.flare_line)
    world.say(bee.shelter_line)


def fear_scene(world: World, hero: Entity, helper: Entity, bee: Bee) -> None:
    propagate(world)
    if world.get("depot").memes["rumor"] < THRESHOLD:
        return
    world.say(
        f'{hero.id} clutched the honey jar and whispered, "Did the storm put a spirit in the lamp?"'
    )
    world.say(
        f"{helper.id} listened to {bee.sound} and answered, "
        f'"No spirit I know buzzes like that, but something small is afraid."'
    )
    world.say(
        f"The waiting bus stayed at the platform while the strange light hopped over the benches."
    )


def plan_scene(
    world: World,
    hero: Entity,
    helper: Entity,
    plan: HoneyPlan,
    helper_role: HelperRole,
) -> None:
    honey = world.get("honey")
    depot = world.get("depot")
    helper.meters["steadying_lamp"] += 1
    honey.meters["offered"] += 1
    depot.meters["perch_ready"] += 1
    world.say(
        f'Then {hero.id} said, "If it is only a frightened creature, let us lead it with sweetness."'
    )
    world.say(
        f'{helper.id} nodded. "{helper_role.wisdom_line}" {hero.id} would {plan.setup_line}, '
        f"and {helper.id} would {plan.helper_job}."
    )


def resolve_scene(world: World, hero: Entity, helper: Entity, plan: HoneyPlan) -> None:
    propagate(world)
    if world.get("bus").meters["departing"] < THRESHOLD:
        return
    world.say(plan.success_line)
    world.say(
        f'The crystal lamp grew quiet at once, and {hero.id} laughed. "Look," '
        f"{hero.pronoun()} said, \"the storm spirit was only a guest with wet wings.\""
    )
    world.say(
        f"{helper.id} opened {helper.pronoun('possessive')} hand, and the whole depot seemed to breathe again."
    )


def finish(world: World, hero: Entity, helper: Entity, bee: Bee) -> None:
    world.say(
        f"Soon the depot bell rang, the passengers climbed aboard, and {world.depot.ending_image}."
    )
    world.say(
        f"{hero.id} kept the empty honey jar on {hero.pronoun('possessive')} lap and watched {bee.phrase} "
        f"vanish into the washed night."
    )
    world.say(
        f"That is why the old ones say that in a loud storm, a calm hand and a little honey can brighten a whole depot."
    )


def tell(
    depot: Depot,
    storm: Storm,
    lamp: Lamp,
    bee: Bee,
    plan: HoneyPlan,
    helper_role: HelperRole,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    trait: str,
) -> World:
    world = World(depot)
    hero = world.add(Entity(hero_name, "character", hero_gender, role="hero", traits=[trait]))
    helper = world.add(Entity(helper_name, "character", helper_gender, role="helper"))
    world.add(Entity("depot", "place", "bus depot", label=depot.place))
    world.add(Entity("storm", "weather", "storm", label=storm.phrase))
    world.add(Entity("lamp", "thing", "lamp", label=lamp.phrase))
    world.add(Entity("bee", "animal", "bee", label=bee.phrase))
    world.add(Entity("honey", "thing", "honey", label="honey"))
    world.add(Entity("bus", "thing", "bus", label="bus"))
    world.facts.update(
        depot_cfg=depot,
        storm_cfg=storm,
        lamp_cfg=lamp,
        bee_cfg=bee,
        plan_cfg=plan,
        helper_role_cfg=helper_role,
        hero=hero,
        helper=helper,
    )

    introduce(world, hero, helper, storm, lamp, helper_role)
    awaken_world(world, storm, lamp, bee)

    world.para()
    fear_scene(world, hero, helper, bee)

    world.para()
    plan_scene(world, hero, helper, plan, helper_role)
    resolve_scene(world, hero, helper, plan)
    finish(world, hero, helper, bee)
    world.facts["resolved"] = world.get("depot").meters["peace"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "honey": [
        (
            "Why might honey help with a bee?",
            "Honey smells sweet to many bees, so it can guide them gently toward a safe place.",
        )
    ],
    "storm": [
        (
            "Why can a loud storm change how a lamp looks?",
            "Strong wind can shake a hanging lamp, and moving light makes bright patterns jump around.",
        )
    ],
    "crystal": [
        (
            "What does crystal do in a lamp?",
            "Crystal bends and scatters light, so one steady flame can sparkle in many little flashes.",
        )
    ],
    "bus_depot": [
        (
            "What is a bus depot?",
            "A bus depot is a place where buses stop, wait, and collect passengers before traveling on.",
        )
    ],
    "dialogue": [
        (
            "Why do people talk during a problem in a story?",
            "Dialogue lets characters share what they fear, guess, and decide, so the solution can happen together.",
        )
    ],
}
KNOWLEDGE_ORDER = ["honey", "storm", "crystal", "bus_depot", "dialogue"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    depot = world.facts["depot_cfg"]
    lamp = world.facts["lamp_cfg"]
    storm = world.facts["storm_cfg"]
    return [
        f'Write a folk tale for children set in a bus depot that includes honey, a loud storm, and {lamp.phrase}.',
        f"Tell a story in which {hero.id} and {helper.id} face {storm.phrase} at {depot.place} and solve the trouble through dialogue.",
        f"Write a gentle village tale where a child uses honey to calm a fearful mystery beneath a crystal lamp.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    storm = world.facts["storm_cfg"]
    lamp = world.facts["lamp_cfg"]
    bee = world.facts["bee_cfg"]
    plan = world.facts["plan_cfg"]
    depot = world.facts["depot_cfg"]
    qa = [
        (
            "Who are the main people in the story?",
            f"The story centers on {hero.id} and {helper.id} at {depot.place}. They face the trouble together while the passengers wait.",
        ),
        (
            "Why did the crystal lamp seem haunted?",
            f"{storm.phrase.capitalize()} shook the hanging lamp, and {bee.phrase} was hiding inside it. The moving bee and the shaking light made the lamp look ghostly.",
        ),
        (
            "How did honey help solve the problem?",
            f"{hero.id} used {plan.bait} to guide the bee out of the lamp. Once the bee followed the sweetness, the light stopped jumping and the depot grew calm.",
        ),
        (
            "Why was the bus delayed for a moment?",
            f"The bus waited because the strange flashing light frightened everyone at the depot. No one wanted to leave until they understood what the storm had stirred up.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            (
                "What changed at the end?",
                f"The bee left the lamp, the rumor faded, and the bus could finally depart. The ending proves the change because the lamp shines quietly instead of dancing in fear.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    for tag in KNOWLEDGE_ORDER:
        out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story ==")
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cedar", "thunder", "amber_crystal", "honeybee", "sill_saucer", "keeper", "Mira", "girl", "Pavel", "boy", "careful"),
    StoryParams("river", "hail", "blue_crystal", "bumblebee", "door_spoon", "seller", "Niko", "boy", "Lina", "girl", "kind"),
    StoryParams("hill", "sea_squall", "star_cut_crystal", "orchard_bee", "bench_crust", "driver", "Asha", "girl", "Oren", "boy", "brave"),
]


def explain_rejection(depot: Depot, storm: Storm, lamp: Lamp, bee: Bee, plan: HoneyPlan) -> str:
    if not storm_valid(storm):
        return f"(No story: {storm.phrase} is not loud enough to rattle the lamp into a real bus-depot scare.)"
    if not lamp_valid(lamp):
        return f"(No story: {lamp.phrase} is not a hanging crystal lamp, so it cannot make the folk-tale sign.)"
    if not bee_valid(bee):
        return f"(No story: {bee.phrase} would not be guided by honey, so the chosen resolution would not make sense.)"
    return f"(No story: {depot.place} has no {plan.perch.replace('_', ' ')} for the honey plan.)"


ASP_RULES = r"""
usable_storm(S) :- loud(S), gusty(S).
usable_lamp(L)  :- crystal(L), hanging(L).
usable_bee(B)   :- likes_honey(B).
usable_plan(D,P) :- supports(D,Loc), plan_perch(P,Loc).
valid(D,S,L,B,P) :- depot(D), storm(S), lamp(L), bee(B), plan(P),
                    usable_storm(S), usable_lamp(L), usable_bee(B), usable_plan(D,P).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for depot_id, depot in DEPOTS.items():
        lines.append(asp.fact("depot", depot_id))
        for support in sorted(depot.supports):
            lines.append(asp.fact("supports", depot_id, support))
    for storm_id, storm in STORMS.items():
        lines.append(asp.fact("storm", storm_id))
        if storm.loud:
            lines.append(asp.fact("loud", storm_id))
        if storm.gusty:
            lines.append(asp.fact("gusty", storm_id))
    for lamp_id, lamp in LAMPS.items():
        lines.append(asp.fact("lamp", lamp_id))
        if lamp.crystal:
            lines.append(asp.fact("crystal", lamp_id))
        if lamp.hanging:
            lines.append(asp.fact("hanging", lamp_id))
    for bee_id, bee in BEES.items():
        lines.append(asp.fact("bee", bee_id))
        if bee.likes_honey:
            lines.append(asp.fact("likes_honey", bee_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("plan_perch", plan_id, plan.perch))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def _exercise_story(sample: StorySample) -> None:
    text = sample.story
    lower = text.lower()
    if "honey" not in lower:
        raise StoryError("Generated story lost the honey motif.")
    if "storm" not in lower:
        raise StoryError("Generated story lost the storm motif.")
    if "crystal lamp" not in lower:
        raise StoryError("Generated story lost the crystal lamp motif.")
    if "bus depot" not in lower:
        raise StoryError("Generated story lost the bus depot setting.")
    if '"' not in text:
        raise StoryError("Generated story lost dialogue.")
    if "{'" in text or "}" in text:
        raise StoryError("Generated story leaked unresolved formatting.")
    if len(sample.story_qa) < 4 or len(sample.world_qa) < 4:
        raise StoryError("Generated QA output is too thin.")
    if not getattr(sample.world, "facts", {}).get("resolved"):
        raise StoryError("Generated story did not reach resolution.")


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    status = 0
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        print("MISMATCH between clingo and Python gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        status = 1

    try:
        for params in CURATED:
            _exercise_story(generate(params))
        for depot_id, storm_id, lamp_id, bee_id, plan_id in valid_combos()[:12]:
            params = StoryParams(
                depot_id,
                storm_id,
                lamp_id,
                bee_id,
                plan_id,
                "keeper",
                "Mira",
                "girl",
                "Pavel",
                "boy",
                "careful",
            )
            _exercise_story(generate(params))
        print("OK: exercised curated and sampled valid stories.")
    except StoryError as err:
        print(f"VERIFY FAILED: {err}")
        status = 1
    return status


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: honey, loud storm, crystal lamp, bus depot.")
    ap.add_argument("--depot", choices=DEPOTS)
    ap.add_argument("--storm", choices=STORMS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--bee", choices=BEES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper-role", choices=HELPER_ROLES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.depot and args.storm and args.lamp and args.bee and args.plan:
        depot = DEPOTS[args.depot]
        storm = STORMS[args.storm]
        lamp = LAMPS[args.lamp]
        bee = BEES[args.bee]
        plan = PLANS[args.plan]
        if not valid_combo(depot, storm, lamp, bee, plan):
            raise StoryError(explain_rejection(depot, storm, lamp, bee, plan))

    combos = [
        combo
        for combo in valid_combos()
        if (args.depot is None or combo[0] == args.depot)
        and (args.storm is None or combo[1] == args.storm)
        and (args.lamp is None or combo[2] == args.lamp)
        and (args.bee is None or combo[3] == args.bee)
        and (args.plan is None or combo[4] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid honey-and-lamp bus-depot folk tale matches the given options.)")

    depot_id, storm_id, lamp_id, bee_id, plan_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=hero)
    helper_role = args.helper_role or rng.choice(sorted(HELPER_ROLES))
    return StoryParams(
        depot=depot_id,
        storm=storm_id,
        lamp=lamp_id,
        bee=bee_id,
        plan=plan_id,
        helper_role=helper_role,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        DEPOTS[params.depot],
        STORMS[params.storm],
        LAMPS[params.lamp],
        BEES[params.bee],
        PLANS[params.plan],
        HELPER_ROLES[params.helper_role],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (depot, storm, lamp, bee, plan) combos:\n")
        for row in combos:
            print("  " + " ".join(f"{item:15}" for item in row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 80):
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

    for idx, sample in enumerate(samples):
        params = sample.params
        header = ""
        if args.all:
            header = f"### {params.hero} & {params.helper}: {params.storm}, {params.lamp}, {params.plan}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
