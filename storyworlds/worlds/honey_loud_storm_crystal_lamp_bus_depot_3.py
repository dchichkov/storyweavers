#!/usr/bin/env python3
"""
storyworlds/worlds/honey_loud_storm_crystal_lamp_bus_depot_3.py
================================================================

A standalone TinyStories-style storyworld for this seed:

    Words: honey, loud storm, crystal lamp
    Setting: bus depot
    Features: Dialogue
    Style: Folk Tale

Internal source tale behind the simulation:
    In a village bus depot, a child waits through a loud storm with a crock of
    honey. The hanging crystal lamp above the timetable begins to flare and
    clatter, and everyone thinks the weather has woken a depot omen. In truth,
    a rain-soaked queen bee has climbed into the warm lamp crown and her small
    swarm circles after her. The child notices that the bees keep turning
    toward the honey, speaks with an older helper, and lays a shining honey
    trail to a dry shelter shelf. When the helper shields the path from the
    wind, the queen leaves the lamp, the swarm follows, and the depot grows
    still enough for the bus to depart.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
STORYWORLDS = Path(__file__).resolve().parents[1]
for base in (ROOT, STORYWORLDS):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

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
    wait_spot: str
    storm_line: str
    ending_image: str


@dataclass(frozen=True)
class Storm:
    id: str
    phrase: str
    loud: bool
    gusty: bool
    roof_line: str
    draft_line: str


@dataclass(frozen=True)
class Lamp:
    id: str
    phrase: str
    crystal: bool
    hanging: bool
    color: str
    flare_line: str


@dataclass(frozen=True)
class Swarm:
    id: str
    queen_phrase: str
    workers_phrase: str
    likes_honey: bool
    shelter_line: str
    buzz_line: str


@dataclass(frozen=True)
class HoneyRoute:
    id: str
    support: str
    bait: str
    shelter_spot: str
    setup_line: str
    helper_task: str
    success_line: str


@dataclass(frozen=True)
class HelperRole:
    id: str
    title: str
    intro_line: str
    counsel_line: str


@dataclass
class StoryParams:
    depot: str
    storm: str
    lamp: str
    swarm: str
    route: str
    helper_role: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: int | None = None


class World:
    def __init__(self, depot: Depot) -> None:
        self.depot = depot
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.history: list[dict[str, str]] = []

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

    def remember(self, kind: str, summary: str, **data: str) -> None:
        item = {"kind": kind, "summary": summary}
        item.update({k: str(v) for k, v in data.items()})
        self.history.append(item)

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)

    def copy(self) -> "World":
        clone = World(self.depot)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.history = copy.deepcopy(self.history)
        return clone


def role(world: World, name: str) -> Optional[Entity]:
    return next((ent for ent in world.entities.values() if ent.role == name), None)


def _sentence(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


DEPOTS = {
    "cedar_hollow": Depot(
        id="cedar_hollow",
        place="the Cedar Hollow bus depot",
        village="Cedar Hollow",
        supports=frozenset({"timetable_shelf", "parcel_rail"}),
        wait_spot="the long bench beneath the timetable",
        storm_line="rain stitched silver threads across the open yard",
        ending_image="the last bus rolled away while the lamp rested clear as a drop of morning ice",
    ),
    "reed_crossing": Depot(
        id="reed_crossing",
        place="the Reed Crossing bus depot",
        village="Reed Crossing",
        supports=frozenset({"window_ledge", "parcel_rail"}),
        wait_spot="the painted bench beside the fare window",
        storm_line="the muddy yard shone whenever lightning opened its white eye",
        ending_image="the waiting road took back its quiet while the lamp poured warm gold over the tickets",
    ),
    "hill_market": Depot(
        id="hill_market",
        place="the Hill Market bus depot",
        village="Hill Market",
        supports=frozenset({"timetable_shelf", "window_ledge"}),
        wait_spot="the high bench near the market gate",
        storm_line="water drummed in the barrel by the gate and ran in little rivers between the stones",
        ending_image="the bus groaned into motion while the crystal light stood still like a patient star",
    ),
}

STORMS = {
    "thunder_drum": Storm(
        id="thunder_drum",
        phrase="a loud thunderstorm",
        loud=True,
        gusty=True,
        roof_line="The loud storm beat on the depot roof like a giant hand on a drum.",
        draft_line="Each gust came under the eaves and tugged at sleeves, ticket slips, and loose thoughts.",
    ),
    "hail_clatter": Storm(
        id="hail_clatter",
        phrase="a loud hail storm",
        loud=True,
        gusty=True,
        roof_line="The loud storm flung hail on the roof until the whole depot rang like a kettle lid.",
        draft_line="Cold drafts skipped through the doorframe and made the waiting people tuck in close.",
    ),
    "river_squall": Storm(
        id="river_squall",
        phrase="a loud river squall",
        loud=True,
        gusty=True,
        roof_line="The loud storm came up from the river road and boomed around the depot posts.",
        draft_line="Wet wind curled under the roof and worried everything that could sway.",
    ),
    "soft_rain": Storm(
        id="soft_rain",
        phrase="a soft rain",
        loud=False,
        gusty=False,
        roof_line="Soft rain only tapped at the roof with patient fingers.",
        draft_line="The air stayed calm enough for old papers to lie flat.",
    ),
}

LAMPS = {
    "amber_teardrop": Lamp(
        id="amber_teardrop",
        phrase="an amber crystal lamp",
        crystal=True,
        hanging=True,
        color="amber",
        flare_line="The amber crystal lamp shook on its chain and threw honey-colored sparks over the wet floorboards.",
    ),
    "blue_prism": Lamp(
        id="blue_prism",
        phrase="a blue crystal lamp",
        crystal=True,
        hanging=True,
        color="blue",
        flare_line="The blue crystal lamp flashed in broken blue pieces, as if someone had scattered twilight into the depot.",
    ),
    "star_cut": Lamp(
        id="star_cut",
        phrase="a star-cut crystal lamp",
        crystal=True,
        hanging=True,
        color="silver",
        flare_line="The star-cut crystal lamp rattled and scattered little star-points over the bus signs.",
    ),
    "plain_lantern": Lamp(
        id="plain_lantern",
        phrase="a plain station lantern",
        crystal=False,
        hanging=False,
        color="plain",
        flare_line="The plain station lantern gave one steady pool of light.",
    ),
}

SWARMS = {
    "meadow_queen": Swarm(
        id="meadow_queen",
        queen_phrase="a rain-soaked queen bee",
        workers_phrase="a small ring of worker bees",
        likes_honey=True,
        shelter_line="A rain-soaked queen bee had climbed into the warm lamp crown, and a small ring of worker bees circled after her.",
        buzz_line="Their joined buzzing sounded like a tiny spindle turning inside the glass.",
    ),
    "orchard_queen": Swarm(
        id="orchard_queen",
        queen_phrase="an orchard queen bee",
        workers_phrase="a careful cloud of worker bees",
        likes_honey=True,
        shelter_line="An orchard queen bee had tucked herself into the lamp where the wind could not strike her wings, and a careful cloud of workers followed close.",
        buzz_line="Their steady buzzing hummed through the crystals like a hidden song.",
    ),
    "heather_queen": Swarm(
        id="heather_queen",
        queen_phrase="a heather queen bee",
        workers_phrase="a trembling cluster of worker bees",
        likes_honey=True,
        shelter_line="A heather queen bee had taken the lamp for a sudden palace against the rain, and a trembling cluster of workers swirled around the chain.",
        buzz_line="Their buzzing rose and fell with the swinging lamp until even the benches seemed to listen.",
    ),
    "paper_wasps": Swarm(
        id="paper_wasps",
        queen_phrase="a paper wasp queen",
        workers_phrase="a sharp little knot of wasps",
        likes_honey=False,
        shelter_line="A paper wasp queen had settled near the chain.",
        buzz_line="Their dry whirr cut the air like paper being torn.",
    ),
}

ROUTES = {
    "timetable_ribbon": HoneyRoute(
        id="timetable_ribbon",
        support="timetable_shelf",
        bait="a shining ribbon of honey along the timetable shelf",
        shelter_spot="the dry timetable shelf",
        setup_line="drew a narrow ribbon of honey along the timetable shelf until it reached a dry corner beneath the notices",
        helper_task="stand by the lamp with an umbrella cloth and keep the wind from slapping the bees back into the glass",
        success_line="The queen crept down the chain, tasted the honey, and crossed to the dry shelf; the workers drifted after her like soft brown stitches.",
    ),
    "window_ledge_drop": HoneyRoute(
        id="window_ledge_drop",
        support="window_ledge",
        bait="a round drop of honey on the window ledge",
        shelter_spot="the warm window ledge",
        setup_line="placed a bright round drop of honey on the window ledge where the storm could not wash it away",
        helper_task="open the cracked window just enough to make a still pocket of air",
        success_line="The queen found the honey on the ledge, and the worker bees settled around her where the pane kept out the hardest rain.",
    ),
    "parcel_rail_trail": HoneyRoute(
        id="parcel_rail_trail",
        support="parcel_rail",
        bait="a honey trail along the parcel rail",
        shelter_spot="the parcel rail above the sacks",
        setup_line="traced a fine line of honey along the parcel rail above the mail sacks",
        helper_task="hold the sack curtain steady so the bees would meet dry canvas instead of wild wind",
        success_line="The queen stepped from the lamp to the honey trail on the rail, and the worker bees gathered over the mail sacks in a quiet golden knot.",
    ),
}

HELPER_ROLES = {
    "porter": HelperRole(
        id="porter",
        title="the depot porter",
        intro_line="the depot porter watched the waiting trunks and knew which corners stayed dry in every season",
        counsel_line="When frightened creatures find a road, they leave trouble behind them.",
    ),
    "ticket_keeper": HelperRole(
        id="ticket_keeper",
        title="the ticket keeper",
        intro_line="the ticket keeper kept the brass stamp warm in one palm and missed very little",
        counsel_line="Sweetness and stillness do work that shouting never can.",
    ),
    "bun_seller": HelperRole(
        id="bun_seller",
        title="the bun seller",
        intro_line="the bun seller guarded a basket that smelled of flour, cloth, and evening warmth",
        counsel_line="If you guide one small heart gently, many others will follow.",
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tala", "Rina", "Asha", "Sela"]
BOY_NAMES = ["Ivo", "Milan", "Pavel", "Niko", "Oren", "Sami"]
TRAITS = ["careful", "brave", "patient", "kind", "sharp-eyed"]


def storm_valid(storm: Storm) -> bool:
    return storm.loud and storm.gusty


def lamp_valid(lamp: Lamp) -> bool:
    return lamp.crystal and lamp.hanging


def swarm_valid(swarm: Swarm) -> bool:
    return swarm.likes_honey


def route_fits(depot: Depot, route: HoneyRoute) -> bool:
    return route.support in depot.supports


def valid_combo(depot: Depot, storm: Storm, lamp: Lamp, swarm: Swarm, route: HoneyRoute) -> bool:
    return storm_valid(storm) and lamp_valid(lamp) and swarm_valid(swarm) and route_fits(depot, route)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for depot_id, depot in DEPOTS.items():
        for storm_id, storm in STORMS.items():
            for lamp_id, lamp in LAMPS.items():
                for swarm_id, swarm in SWARMS.items():
                    for route_id, route in ROUTES.items():
                        if valid_combo(depot, storm, lamp, swarm, route):
                            combos.append((depot_id, storm_id, lamp_id, swarm_id, route_id))
    return sorted(combos)


def explain_rejection(depot: Depot, storm: Storm, lamp: Lamp, swarm: Swarm, route: HoneyRoute) -> str:
    if not storm_valid(storm):
        return f"No story: {storm.phrase} is not a loud enough storm to turn the lamp into a real bus-depot omen."
    if not lamp_valid(lamp):
        return f"No story: {lamp.phrase} is not a hanging crystal lamp, so it cannot flash like the folk-tale sign."
    if not swarm_valid(swarm):
        return f"No story: {swarm.workers_phrase} would not follow honey, so the chosen turn would not make sense."
    return f"No story: {depot.place} has no {route.support.replace('_', ' ')} for that honey route."


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def introduce(world: World, hero: Entity, helper: Entity, helper_role: HelperRole, storm: Storm, lamp: Lamp) -> None:
    world.say(
        f"In {world.depot.village}, old people still speak of the night when {hero.id}, a {hero.traits[0]} child, waited at {world.depot.place} with a crock of honey wrapped in cloth."
    )
    world.say(
        f"Beside {hero.id} stood {helper.id}, for {helper_role.intro_line}. Above {world.depot.wait_spot} hung {lamp.phrase}."
    )
    world.say(_sentence(world.depot.storm_line) + ".")
    world.say(storm.roof_line)
    world.say(storm.draft_line)
    world.remember("beginning", "The child waited with honey at the depot during a loud storm.", place=world.depot.place)


def awaken_world(world: World, storm: Storm, lamp: Lamp, swarm: Swarm) -> None:
    storm_ent = world.get("storm")
    lamp_ent = world.get("lamp")
    swarm_ent = world.get("swarm")
    storm_ent.meters["arrived"] += 1
    if storm.gusty:
        storm_ent.meters["gusts"] += 1
    if lamp.hanging:
        lamp_ent.meters["hanging"] += 1
    lamp_ent.meters["warm"] += 1
    swarm_ent.meters["shelter_seeking"] += 1
    world.say(lamp.flare_line)
    world.say(swarm.shelter_line)
    world.say(swarm.buzz_line)
    world.remember("premise", "The storm and the bees turned the crystal lamp into a troubling sign.", storm=storm.phrase, lamp=lamp.phrase)


def _r_storm_shakes_lamp(world: World) -> list[str]:
    storm = world.entities.get("storm")
    lamp = world.entities.get("lamp")
    if not storm or not lamp:
        return []
    if storm.meters["arrived"] < THRESHOLD or storm.meters["gusts"] < THRESHOLD:
        return []
    if lamp.meters["hanging"] < THRESHOLD:
        return []
    sig = ("storm_shakes_lamp", storm.id, lamp.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lamp.meters["swaying"] += 1
    lamp.memes["alarm"] += 1
    world.remember("physical", "The loud storm shook the hanging lamp.", storm=storm.id, lamp=lamp.id)
    return ["storm_shakes_lamp"]


def _r_queen_hides_in_crown(world: World) -> list[str]:
    lamp = world.entities.get("lamp")
    swarm = world.entities.get("swarm")
    if not lamp or not swarm:
        return []
    if lamp.meters["warm"] < THRESHOLD or swarm.meters["shelter_seeking"] < THRESHOLD:
        return []
    sig = ("queen_hides_in_crown", lamp.id, swarm.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    swarm.meters["queen_in_lamp"] += 1
    swarm.meters["workers_circling"] += 1
    lamp.meters["sparkles_broken"] += 1
    world.remember("physical", "The queen bee climbed into the lamp crown and the workers circled after her.", lamp=lamp.id, swarm=swarm.id)
    return ["queen_hides_in_crown"]


def _r_false_omen(world: World) -> list[str]:
    hero = role(world, "hero")
    helper = role(world, "helper")
    depot = world.entities.get("depot")
    lamp = world.entities.get("lamp")
    swarm = world.entities.get("swarm")
    bus = world.entities.get("bus")
    if not hero or not helper or not depot or not lamp or not swarm or not bus:
        return []
    if lamp.meters["swaying"] < THRESHOLD or swarm.meters["queen_in_lamp"] < THRESHOLD:
        return []
    sig = ("false_omen", depot.id, lamp.id, swarm.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["wonder"] += 1
    helper.memes["concern"] += 1
    depot.memes["rumor"] += 1
    bus.meters["waiting"] += 1
    world.remember("tension", "The flashing lamp looked like an omen, so the bus stayed waiting.", lamp=lamp.id, bus=bus.id)
    return ["false_omen"]


def _r_honey_route_resolves(world: World) -> list[str]:
    hero = role(world, "hero")
    helper = role(world, "helper")
    depot = world.entities.get("depot")
    lamp = world.entities.get("lamp")
    swarm = world.entities.get("swarm")
    honey = world.entities.get("honey")
    bus = world.entities.get("bus")
    if not hero or not helper or not depot or not lamp or not swarm or not honey or not bus:
        return []
    if swarm.meters["queen_in_lamp"] < THRESHOLD:
        return []
    if honey.meters["offered"] < THRESHOLD:
        return []
    if depot.meters["dry_shelter_ready"] < THRESHOLD:
        return []
    if helper.meters["shielding_path"] < THRESHOLD:
        return []
    sig = ("honey_route_resolves", swarm.id, honey.id, depot.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    swarm.meters["queen_in_lamp"] = 0.0
    swarm.meters["workers_circling"] = 0.0
    swarm.meters["at_shelter"] += 1
    lamp.meters["swaying"] = 0.0
    lamp.meters["sparkles_broken"] = 0.0
    lamp.memes["alarm"] = 0.0
    depot.memes["rumor"] = 0.0
    depot.meters["peace"] += 1
    hero.memes["courage"] += 1
    hero.memes["care"] += 1
    helper.memes["relief"] += 1
    bus.meters["waiting"] = 0.0
    bus.meters["departing"] += 1
    world.remember("resolution", "The queen followed the honey route, the swarm left the lamp, and the bus could go.", support=str(world.facts["route_cfg"].support))
    return ["honey_route_resolves"]


CAUSAL_RULES = [
    _r_storm_shakes_lamp,
    _r_queen_hides_in_crown,
    _r_false_omen,
    _r_honey_route_resolves,
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule(world)
            if len(world.fired) > before:
                changed = True


def omen_scene(world: World, hero: Entity, helper: Entity) -> None:
    propagate(world)
    if world.get("depot").memes["rumor"] < THRESHOLD:
        return
    world.say(
        f'{hero.id} drew closer to the bench and whispered, "Has the loud storm woken a sign in the lamp?"'
    )
    world.say(
        f'{helper.id} listened to the hidden buzzing and answered, "No omen hums with wings. Something living is asking for shelter."'
    )
    world.say(
        "The waiting passengers pulled their coats tight, and even the driver kept one foot off the step until the strange flashing could be explained."
    )
    world.remember("dialogue", "The hero and helper named the fear and began to look for the true cause.")


def turn_scene(world: World, hero: Entity, helper: Entity, route: HoneyRoute, helper_role: HelperRole) -> None:
    honey = world.get("honey")
    depot = world.get("depot")
    helper.meters["shielding_path"] += 1
    honey.meters["offered"] += 1
    depot.meters["dry_shelter_ready"] += 1
    world.say(
        f'{hero.id} lifted the crock and said, "The bees keep leaning toward my honey. Let me make them a kinder road than the lamp."'
    )
    world.say(
        f'{helper.id} nodded. "{helper_role.counsel_line}" So {hero.id} {route.setup_line}, and {helper.id} would {route.helper_task}.'
    )
    world.remember("turn", "The child and helper turned fear into a plan by making a honey route to a dry shelter.", support=route.support)


def resolve_scene(world: World, hero: Entity, helper: Entity, route: HoneyRoute) -> None:
    propagate(world)
    if world.get("bus").meters["departing"] < THRESHOLD:
        return
    world.say(route.success_line)
    world.say(
        f'The lamp steadied at once, and {hero.id} breathed out. "There now," {hero.pronoun()} said, "the storm was loud, but the heart inside the trouble was only afraid."'
    )
    world.say(
        f"{helper.id} smiled and lowered {helper.pronoun('possessive')} hands. The depot boards stopped trembling with rumor and only listened to the rain."
    )


def finish(world: World, hero: Entity, helper: Entity, route: HoneyRoute, swarm: Swarm) -> None:
    world.say(
        f"Soon the departure call rang out, the passengers climbed aboard, and {world.depot.ending_image}."
    )
    world.say(
        f"{hero.id} kept the honey crock on {hero.pronoun('possessive')} lap and watched {swarm.workers_phrase} settle around {route.shelter_spot} instead of the lamp."
    )
    world.say(
        "That is why the old people say that when a loud storm makes a bright thing look wild, one gentle thought may be wiser than ten frightened guesses."
    )
    world.remember("ending", "The depot ended in calm light, and the bus departed after the bees moved to shelter.")


def tell(
    depot: Depot,
    storm: Storm,
    lamp: Lamp,
    swarm: Swarm,
    route: HoneyRoute,
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
    world.add(Entity("swarm", "animal", "bee swarm", label=swarm.workers_phrase))
    world.add(Entity("honey", "thing", "honey", label="honey"))
    world.add(Entity("bus", "thing", "bus", label="bus"))
    world.facts.update(
        depot_cfg=depot,
        storm_cfg=storm,
        lamp_cfg=lamp,
        swarm_cfg=swarm,
        route_cfg=route,
        helper_role_cfg=helper_role,
        hero=hero,
        helper=helper,
    )

    introduce(world, hero, helper, helper_role, storm, lamp)
    awaken_world(world, storm, lamp, swarm)

    world.para()
    omen_scene(world, hero, helper)

    world.para()
    turn_scene(world, hero, helper, route, helper_role)
    resolve_scene(world, hero, helper, route)
    finish(world, hero, helper, route, swarm)

    world.facts["resolved"] = world.get("depot").meters["peace"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    depot = world.facts["depot_cfg"]
    storm = world.facts["storm_cfg"]
    lamp = world.facts["lamp_cfg"]
    return [
        f"Write a folk tale for children set at {depot.place} that includes honey, a loud storm, and {lamp.phrase}.",
        f"Tell a gentle depot story where {hero.id} and {helper.id} solve a frightening mystery through dialogue and careful observation.",
        f"Write a village tale in which a child turns a storm omen into a kindness by using honey near a crystal lamp.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    depot: Depot = world.facts["depot_cfg"]
    storm: Storm = world.facts["storm_cfg"]
    lamp: Lamp = world.facts["lamp_cfg"]
    swarm: Swarm = world.facts["swarm_cfg"]
    route: HoneyRoute = world.facts["route_cfg"]
    return [
        (
            "Who solved the trouble at the depot?",
            f"{hero.id} and {helper.id} solved it together at {depot.place}. The child noticed what the bees wanted, and the helper made the path safe enough for the plan to work.",
        ),
        (
            "Why did the crystal lamp look like an omen?",
            f"{storm.phrase.capitalize()} shook the hanging lamp while {swarm.queen_phrase} sheltered inside its crown. The swinging crystals and circling bees made the light flash in a frightening way.",
        ),
        (
            "How did honey change the story?",
            f"{hero.id} used {route.bait} to lead the queen away from the lamp. Once the bees had a dry place to gather, the false omen disappeared and the depot calmed down.",
        ),
        (
            "Why did the bus wait before leaving?",
            f"The passengers and driver did not want to leave while the lamp still looked wild and unexplained. The bus only departed after the real cause was understood and the bees were moved safely.",
        ),
        (
            "Where did the bees end up at the end?",
            f"They settled around {route.shelter_spot} instead of circling the lamp. That new resting place mattered because it was dry and away from the swinging light.",
        ),
        (
            "What lesson does the ending image prove?",
            f"The ending shows that calm thinking can change a frightening scene into an ordinary one again. The still lamp and departing bus prove that kindness and attention solved the problem better than panic.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "honey": [
        (
            "Why might honey help guide bees?",
            "Honey has a strong sweet smell that bees can notice. In a careful situation, that scent can draw them toward a safer resting place.",
        )
    ],
    "storm": [
        (
            "Why can a loud storm make a hanging lamp look strange?",
            "Wind can shake the lamp while thunder changes how people feel about every flash. When light moves suddenly, ordinary things can seem magical or scary.",
        )
    ],
    "crystal": [
        (
            "What does crystal do in a lamp?",
            "Crystal breaks one steady light into many bright pieces. That is why a moving crystal lamp can throw dancing sparks across walls and floors.",
        )
    ],
    "depot": [
        (
            "What is a bus depot?",
            "A bus depot is a place where buses stop, wait, and gather passengers. It often has benches, tickets, parcels, and people watching the road together.",
        )
    ],
    "dialogue": [
        (
            "Why is dialogue useful in a folk tale problem?",
            "Dialogue lets characters share fear, wisdom, and plans in their own voices. That makes the turn feel earned because the solution grows out of what they notice and say.",
        )
    ],
}
WORLD_KNOWLEDGE_ORDER = ["honey", "storm", "crystal", "depot", "dialogue"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    del world
    items: list[tuple[str, str]] = []
    for tag in WORLD_KNOWLEDGE_ORDER:
        items.extend(WORLD_KNOWLEDGE[tag])
    return items


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {key: value for key, value in ent.meters.items() if value}
        memes = {key: value for key, value in ent.memes.items() if value}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.traits:
            parts.append(f"traits={ent.traits}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    lines.append("  history:")
    for idx, item in enumerate(world.history, 1):
        lines.append(f"    {idx}. {item['kind']}: {item['summary']}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts"]
    for idx, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{idx}. {prompt}")
    lines.extend(["", "== (2) Story questions"])
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.extend(["", "== (3) World-knowledge questions"])
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cedar_hollow", "thunder_drum", "amber_teardrop", "meadow_queen", "timetable_ribbon", "ticket_keeper", "Mira", "girl", "Pavel", "boy", "careful"),
    StoryParams("reed_crossing", "hail_clatter", "blue_prism", "orchard_queen", "window_ledge_drop", "porter", "Niko", "boy", "Lina", "girl", "brave"),
    StoryParams("hill_market", "river_squall", "star_cut", "heather_queen", "timetable_ribbon", "bun_seller", "Asha", "girl", "Oren", "boy", "patient"),
]


ASP_RULES = r"""
usable_storm(S) :- storm(S), loud(S), gusty(S).
usable_lamp(L) :- lamp(L), crystal(L), hanging(L).
usable_swarm(W) :- swarm(W), likes_honey(W).
usable_route(D,R) :- depot(D), route(R), supports(D,Loc), route_support(R,Loc).

valid(D,S,L,W,R) :-
    depot(D), storm(S), lamp(L), swarm(W), route(R),
    usable_storm(S),
    usable_lamp(L),
    usable_swarm(W),
    usable_route(D,R).
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for depot_id, depot in DEPOTS.items():
        rows.append(asp.fact("depot", depot_id))
        for support in sorted(depot.supports):
            rows.append(asp.fact("supports", depot_id, support))
    for storm_id, storm in STORMS.items():
        rows.append(asp.fact("storm", storm_id))
        if storm.loud:
            rows.append(asp.fact("loud", storm_id))
        if storm.gusty:
            rows.append(asp.fact("gusty", storm_id))
    for lamp_id, lamp in LAMPS.items():
        rows.append(asp.fact("lamp", lamp_id))
        if lamp.crystal:
            rows.append(asp.fact("crystal", lamp_id))
        if lamp.hanging:
            rows.append(asp.fact("hanging", lamp_id))
    for swarm_id, swarm in SWARMS.items():
        rows.append(asp.fact("swarm", swarm_id))
        if swarm.likes_honey:
            rows.append(asp.fact("likes_honey", swarm_id))
    for route_id, route in ROUTES.items():
        rows.append(asp.fact("route", route_id))
        rows.append(asp.fact("route_support", route_id, route.support))
    for helper_id in HELPER_ROLES:
        rows.append(asp.fact("helper_role", helper_id))
    return "\n".join(rows)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def _exercise_story(sample: StorySample) -> None:
    text = sample.story
    lower = text.lower()
    if "honey" not in lower:
        raise StoryError("Generated story lost the honey motif.")
    if "loud storm" not in lower and "loud thunderstorm" not in lower and "loud hail storm" not in lower and "loud river squall" not in lower:
        raise StoryError("Generated story lost the loud storm motif.")
    if "crystal lamp" not in lower:
        raise StoryError("Generated story lost the crystal lamp motif.")
    if "bus depot" not in lower:
        raise StoryError("Generated story lost the bus depot setting.")
    if '"' not in text:
        raise StoryError("Generated story lost dialogue.")
    if "{'" in text or "}" in text:
        raise StoryError("Generated story leaked unresolved formatting.")
    if len(sample.story_qa) < 5 or len(sample.world_qa) < 4:
        raise StoryError("Generated QA output is too thin.")
    if sample.world is None or not sample.world.facts.get("resolved"):
        raise StoryError("Generated story did not reach a grounded resolution.")


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    status = 0
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        print("ASP/Python mismatch:")
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))
        status = 1

    try:
        for params in CURATED:
            _exercise_story(generate(params))
        for depot_id, storm_id, lamp_id, swarm_id, route_id in valid_combos()[:12]:
            sample = generate(
                StoryParams(
                    depot_id,
                    storm_id,
                    lamp_id,
                    swarm_id,
                    route_id,
                    "ticket_keeper",
                    "Mira",
                    "girl",
                    "Pavel",
                    "boy",
                    "careful",
                )
            )
            _exercise_story(sample)
        print("OK: exercised curated and sampled valid stories.")
    except StoryError as err:
        print(f"VERIFY FAILED: {err}")
        status = 1
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Storyworld: honey, loud storm, crystal lamp, bus depot.")
    parser.add_argument("--depot", choices=sorted(DEPOTS))
    parser.add_argument("--storm", choices=sorted(STORMS))
    parser.add_argument("--lamp", choices=sorted(LAMPS))
    parser.add_argument("--swarm", choices=sorted(SWARMS))
    parser.add_argument("--route", choices=sorted(ROUTES))
    parser.add_argument("--helper-role", choices=sorted(HELPER_ROLES))
    parser.add_argument("--hero")
    parser.add_argument("--hero-gender", choices=["girl", "boy"])
    parser.add_argument("--helper")
    parser.add_argument("--helper-gender", choices=["girl", "boy"])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    if args.depot and args.storm and args.lamp and args.swarm and args.route:
        depot = DEPOTS[args.depot]
        storm = STORMS[args.storm]
        lamp = LAMPS[args.lamp]
        swarm = SWARMS[args.swarm]
        route = ROUTES[args.route]
        if not valid_combo(depot, storm, lamp, swarm, route):
            raise StoryError(explain_rejection(depot, storm, lamp, swarm, route))

    combos = [
        combo
        for combo in valid_combos()
        if (args.depot is None or combo[0] == args.depot)
        and (args.storm is None or combo[1] == args.storm)
        and (args.lamp is None or combo[2] == args.lamp)
        and (args.swarm is None or combo[3] == args.swarm)
        and (args.route is None or combo[4] == args.route)
    ]
    if not combos:
        raise StoryError("No valid bus-depot folk tale matches the requested options.")

    depot_id, storm_id, lamp_id, swarm_id, route_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=hero)
    helper_role = args.helper_role or rng.choice(sorted(HELPER_ROLES))
    return StoryParams(
        depot=depot_id,
        storm=storm_id,
        lamp=lamp_id,
        swarm=swarm_id,
        route=route_id,
        helper_role=helper_role,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        trait=rng.choice(TRAITS),
        seed=(args.seed or 1000) + index,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        DEPOTS[params.depot],
        STORMS[params.storm],
        LAMPS[params.lamp],
        SWARMS[params.swarm],
        ROUTES[params.route],
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
        story_qa=[QAItem(question, answer) for question, answer in story_qa(world)],
        world_qa=[QAItem(question, answer) for question, answer in world_knowledge_qa(world)],
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


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed or 7
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos(), start=1):
        params = StoryParams(
            *combo,
            helper_role=(args.helper_role or "ticket_keeper"),
            hero=(args.hero or "Mira"),
            hero_gender=(args.hero_gender or "girl"),
            helper=(args.helper or "Pavel"),
            helper_gender=(args.helper_gender or "boy"),
            trait="careful",
            seed=base_seed + index,
        )
        samples.append(generate(params))
    return samples


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)

    try:
        if args.all:
            samples = _sample_all(args)
        else:
            samples: list[StorySample] = []
            seen: set[str] = set()
            i = 0
            while len(samples) < args.n and i < args.n * 80:
                params = resolve_params(args, random.Random(base_seed + i), index=i)
                sample = generate(params)
                i += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not generate enough unique stories with this constraint set.")

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for idx, sample in enumerate(samples):
            header = ""
            if args.all:
                params = sample.params
                header = (
                    f"### depot={params.depot} storm={params.storm} lamp={params.lamp} "
                    f"swarm={params.swarm} route={params.route}"
                )
            elif len(samples) > 1:
                header = f"### variant {idx + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if idx < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
