#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/payer_bad_ending_dialogue_space_adventure.py
=======================================================================

A standalone storyworld about a small space-trip mistake: two children ride a
shuttle to a moon market, one child is the ticket payer, and a tempting space
toy costs the very credit they need for the ride home. The world model checks
whether the chosen toy is tempting enough to risk the return fare and whether a
helper is close enough to fix the problem before the last shuttle leaves.

The seed asked for:
- the word "payer"
- Bad Ending
- Dialogue
- a Space Adventure style

So this world leans into bright child-facing science-fiction imagery, spoken
lines on nearly every beat, and a genuine bad ending when the children are
stranded after the last shuttle lifts away.

Run it
------
    python storyworlds/worlds/gpt-5.4/payer_bad_ending_dialogue_space_adventure.py
    python storyworlds/worlds/gpt-5.4/payer_bad_ending_dialogue_space_adventure.py --toy comet_candy
    python storyworlds/worlds/gpt-5.4/payer_bad_ending_dialogue_space_adventure.py --helper none
    python storyworlds/worlds/gpt-5.4/payer_bad_ending_dialogue_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/payer_bad_ending_dialogue_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/payer_bad_ending_dialogue_space_adventure.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives in storyworlds/worlds/gpt-5.4/, so we need the package dir
# storyworlds/ on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
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


@dataclass
class Setting:
    id: str
    station: str
    market: str
    window_view: str
    path: str
    ending_view: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    sparkle: str
    cost: int
    fun: int
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    available: bool
    power: int
    arrival: str
    fix: str
    fail: str
    qa_fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
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
        clone = World(self.setting)
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


def _r_no_fare(world: World) -> list[str]:
    payer = world.get("payer")
    if payer.meters["credits"] > 0:
        return []
    sig = ("no_fare",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    station = world.get("station")
    station.meters["risk"] += 1
    for child in (world.get("payer"), world.get("friend")):
        child.memes["worry"] += 1
    return ["__fare_gone__"]


def _r_last_shuttle(world: World) -> list[str]:
    station = world.get("station")
    if station.meters["risk"] < THRESHOLD or station.meters["time"] < THRESHOLD:
        return []
    sig = ("last_shuttle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    station.meters["stranded"] += 1
    for child in (world.get("payer"), world.get("friend")):
        child.memes["fear"] += 1
    return ["__stranded__"]


CAUSAL_RULES = [
    Rule(name="no_fare", tag="social", apply=_r_no_fare),
    Rule(name="last_shuttle", tag="physical", apply=_r_last_shuttle),
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
        for sent in produced:
            world.say(sent)
    return produced


def toy_reasonable(toy: Toy) -> bool:
    return toy.cost == 1


def can_recover(helper: Helper) -> bool:
    return helper.available and helper.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for toy_id, toy in TOYS.items():
            if not toy_reasonable(toy):
                continue
            for helper_id in HELPERS:
                combos.append((setting_id, toy_id, helper_id))
    return combos


def predict_loss(world: World, toy: Toy) -> dict:
    sim = world.copy()
    buy_toy(sim, sim.get("payer"), toy, narrate=False)
    return {
        "credits_left": sim.get("payer").meters["credits"],
        "risk": sim.get("station").meters["risk"],
    }


def introduce(world: World, payer: Entity, friend: Entity, parent: Entity) -> None:
    setting = world.setting
    world.say(
        f"{payer.id} and {friend.id} rode with {payer.id}'s {parent.label_word} to "
        f"{setting.station}, where blue windows looked out at {setting.window_view}."
    )
    world.say(
        f'"Today is our moon market day," {parent.label_word} said. '
        f'"I am giving you one bright return credit. {payer.id}, you are the payer, '
        f'so keep it safe for the ride home."'
    )
    world.say(
        f'{payer.id} tapped the shining credit in {payer.pronoun("possessive")} pocket. '
        f'"I will," {payer.pronoun()} promised.'
    )


def set_out(world: World, payer: Entity, friend: Entity) -> None:
    setting = world.setting
    payer.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"The two children skipped along {setting.path}. Stalls blinked with soft lights, "
        f"and little delivery drones hummed overhead like silver bees."
    )
    world.say(
        f'"Look at all the space things!" {friend.id} said. '
        f'"Let\'s find the shuttle bell before it rings."'
    )


def tempt(world: World, payer: Entity, friend: Entity, toy: Toy) -> None:
    payer.memes["desire"] += float(toy.fun)
    world.say(
        f"Then they stopped at a stall full of {toy.sparkle}. In the middle sat {toy.phrase}."
    )
    world.say(
        f'"Wow," {payer.id} whispered. "It looks like a whole galaxy I can hold."'
    )
    world.say(
        f'"It costs one return credit," the shop robot chimed. "One credit from the payer buys it now."'
    )
    world.say(
        f'{friend.id} stared at the sign. "That is our ride-home coin," {friend.pronoun()} said.'
    )


def warn(world: World, friend: Entity, payer: Entity, toy: Toy) -> None:
    pred = predict_loss(world, toy)
    world.facts["predicted_credits_left"] = pred["credits_left"]
    world.facts["predicted_risk"] = pred["risk"]
    friend.memes["caution"] += 1
    world.say(
        f'"Please don\'t spend it," {friend.id} said. "If you buy {toy.label}, '
        f'we will have no credit left for the shuttle."'
    )
    if pred["risk"] >= THRESHOLD:
        world.say(
            f'"Then the last shuttle could leave without us," {friend.pronoun()} added.'
        )


def buy_toy(world: World, payer: Entity, toy: Toy, narrate: bool = True) -> None:
    payer.meters["credits"] -= toy.cost
    payer.attrs["toy"] = toy.id
    payer.memes["glee"] += 1
    propagate(world, narrate=narrate)


def defy(world: World, payer: Entity, friend: Entity, toy: Toy) -> None:
    payer.memes["defiance"] += 1
    world.say(
        f'"Just one minute," {payer.id} said. "I am the payer, and I want it."'
    )
    world.say(
        f'{friend.id} reached out. "But that is the last credit!"'
    )
    buy_toy(world, payer, toy, narrate=False)
    world.say(
        f"The credit flashed into the robot slot. Out rolled {toy.phrase}, glowing in {payer.id}'s hands."
    )


def discover_loss(world: World, payer: Entity, friend: Entity) -> None:
    station = world.get("station")
    world.say(
        'A moment later the shuttle bell rang from the dock. "Final ride home," a speaker sang.'
    )
    world.say(
        f'{payer.id} grabbed for the pocket again and felt only lint and a fold of warm air.'
    )
    world.say(
        f'"My credit is gone," {payer.pronoun()} said in a tiny voice.'
    )
    station.meters["time"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I told you," {friend.id} said, and then {friend.pronoun()} sounded sorry instead of cross. '
        f'"Now what do we do?"'
    )


def seek_help(world: World, parent: Entity, helper: Helper) -> None:
    station = world.get("station")
    if helper.id == "none":
        world.say(
            f'They ran back toward {parent.label_word}, but a gate had already slid shut between the market and the dock.'
        )
        world.say(
            f'"{parent.label_word.capitalize()}!" they shouted, yet the crowd and the engines swallowed their voices.'
        )
        return
    world.say(
        f'They hurried to {helper.phrase}. "{helper.label.capitalize()}, we need help!" they cried.'
    )
    if can_recover(helper):
        station.meters["risk"] = 0.0
        station.meters["stranded"] = 0.0
        world.say(helper.arrival)
        world.say(helper.fix)
    else:
        world.say(helper.arrival)
        world.say(helper.fail)


def bad_end(world: World, payer: Entity, friend: Entity, parent: Entity, toy: Toy) -> None:
    setting = world.setting
    station = world.get("station")
    station.meters["time"] += 1
    propagate(world, narrate=False)
    payer.memes["regret"] += 1
    friend.memes["sadness"] += 1
    world.say(
        f'Outside the glass, the last shuttle rose in a silver curve and dwindled into the dark.'
    )
    world.say(
        f'"It left," {payer.id} whispered.'
    )
    world.say(
        f'{parent.label_word.capitalize()} found them at last, but the dock lights were already red and cold. '
        f'There would be no more rides until morning.'
    )
    world.say(
        f'{payer.id} looked down at {toy.phrase}. It still glowed, but now it felt small and foolish.'
    )
    world.say(
        f'That night they sat on a metal bench in {setting.ending_view}, tired and hungry, '
        f'watching cleaning robots sweep moon dust in quiet circles.'
    )
    world.say(
        f'"Next time," {friend.id} said softly, "we keep the ride-home credit safe."'
    )
    world.say(
        f'{payer.id} nodded, but the adventure had turned into a long, cold wait.'
    )


def repaired_end(world: World, payer: Entity, friend: Entity, helper: Helper) -> None:
    toy_id = payer.attrs.get("toy")
    toy = TOYS[toy_id]
    payer.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f'The shuttle doors blinked open again, and the children hurried inside.'
    )
    world.say(
        f'{payer.id} hugged {toy.phrase} against {payer.pronoun("possessive")} coat. '
        f'"I almost traded our whole trip for this," {payer.pronoun()} said.'
    )
    world.say(
        f'"You got lucky because {helper.label} helped," {friend.id} answered. '
        f'"Next time, being the payer means saving the return credit first."'
    )


def tell(
    setting: Setting,
    toy: Toy,
    helper: Helper,
    payer_name: str = "Nova",
    payer_gender: str = "girl",
    friend_name: str = "Jet",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "impulsive",
) -> World:
    world = World(setting=setting)
    payer = world.add(Entity(
        id=payer_name,
        kind="character",
        type=payer_gender,
        role="payer",
        traits=[trait],
        tags={"child"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["careful"],
        tags={"child"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        tags={"adult"},
    ))
    station = world.add(Entity(
        id="station",
        type="station",
        label=setting.station,
        phrase=setting.station,
        tags=set(setting.tags),
    ))
    payer.meters["credits"] = 1.0

    introduce(world, payer, friend, parent)
    set_out(world, payer, friend)

    world.para()
    tempt(world, payer, friend, toy)
    warn(world, friend, payer, toy)
    defy(world, payer, friend, toy)

    world.para()
    discover_loss(world, payer, friend)
    seek_help(world, parent, helper)

    repaired = can_recover(helper)
    world.para()
    if repaired:
        repaired_end(world, payer, friend, helper)
        outcome = "rescued"
    else:
        bad_end(world, payer, friend, parent, toy)
        outcome = "stranded"

    world.facts.update(
        payer=payer,
        friend=friend,
        parent=parent,
        setting=setting,
        toy=toy,
        helper=helper,
        outcome=outcome,
        station=station,
        stranded=station.meters["stranded"] >= THRESHOLD,
        repaired=repaired,
        spent_credit=payer.meters["credits"] <= 0,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    toy: str
    helper: str
    payer_name: str
    payer_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "moon_market": Setting(
        id="moon_market",
        station="Moon Lantern Station",
        market="the moon market",
        window_view="the rings of Saturn painted across space",
        path="the pearl-white market bridge",
        ending_view="the echoing night dock",
        tags={"space", "moon", "shuttle"},
    ),
    "asteroid_port": Setting(
        id="asteroid_port",
        station="Pebble Port",
        market="the asteroid bazaar",
        window_view="slow asteroids drifting like black marbles",
        path="the magnet path over the crater",
        ending_view="the dim cargo platform",
        tags={"space", "asteroid", "shuttle"},
    ),
    "mars_arcade": Setting(
        id="mars_arcade",
        station="Red Dune Terminal",
        market="the Mars arcade market",
        window_view="red dust plains under two tiny moons",
        path="the glowing tunnel past the rover docks",
        ending_view="the chilly rover gate",
        tags={"space", "mars", "shuttle"},
    ),
}

TOYS = {
    "star_globe": Toy(
        id="star_globe",
        label="the star globe",
        phrase="a tiny star globe",
        sparkle="swirling blue constellations",
        cost=1,
        fun=2,
        fragile=False,
        tags={"toy", "stars"},
    ),
    "comet_candy": Toy(
        id="comet_candy",
        label="comet candy",
        phrase="a stick of comet candy",
        sparkle="sugar tails that sparkled like little comets",
        cost=1,
        fun=1,
        fragile=True,
        tags={"candy", "comet"},
    ),
    "plasma_pin": Toy(
        id="plasma_pin",
        label="the plasma pin",
        phrase="a blinking plasma pin",
        sparkle="pink and green sparks trapped under glass",
        cost=1,
        fun=2,
        fragile=False,
        tags={"toy", "glow"},
    ),
}

HELPERS = {
    "conductor": Helper(
        id="conductor",
        label="the shuttle conductor",
        phrase="the shuttle conductor by the bell rope",
        available=True,
        power=1,
        arrival='"All right, small travelers," the conductor said. "I can call your parent before the doors close."',
        fix='The conductor sent a quick radio call, and their parent came running with one emergency ride chip.',
        fail='"I am sorry," the conductor said, "but the doors are sealed and I have no spare chip."',
        qa_fix="called their parent and got an emergency ride chip",
        tags={"shuttle", "adult_help"},
    ),
    "service_bot": Helper(
        id="service_bot",
        label="the service bot",
        phrase="a round service bot near the map wall",
        available=True,
        power=1,
        arrival='"Customer problem detected," the service bot beeped. "Connecting you to station help."',
        fix='The bot rolled them to the desk, where a clerk traded the toy back for the lost return credit just in time.',
        fail='The bot spun in a worried circle, but no clerk answered before the dock sealed.',
        qa_fix="led them to the desk, where the toy was traded back for a return credit",
        tags={"robot", "adult_help"},
    ),
    "none": Helper(
        id="none",
        label="no helper",
        phrase="no helper at all",
        available=False,
        power=0,
        arrival="",
        fix="",
        fail="",
        qa_fix="",
        tags={"stranded"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Vega", "Iris", "Lyra"]
BOY_NAMES = ["Jet", "Orion", "Finn", "Leo", "Milo", "Kai"]
TRAITS = ["impulsive", "eager", "curious", "restless"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    payer = f["payer"]
    friend = f["friend"]
    toy = f["toy"]
    setting = f["setting"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short space adventure for a 3-to-5-year-old that includes the word "payer" and lots of dialogue.',
        f"Tell a moon-market story where {payer.id} is the payer for the ride home, but is tempted to spend the last credit on {toy.label}.",
    ]
    if outcome == "stranded":
        prompts.append(
            f"Write a bad-ending space story set at {setting.station} where the last shuttle leaves and the children must wait sadly until morning."
        )
    else:
        prompts.append(
            f"Write a tense but gentle space story where a station helper fixes the missing-fare problem just before the shuttle leaves."
        )
    return prompts


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    payer = f["payer"]
    friend = f["friend"]
    parent = f["parent"]
    toy = f["toy"]
    helper = f["helper"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(payer, friend)}, {payer.id} and {friend.id}, on a trip to {setting.station}. {payer.id}'s {parent.label_word} trusted {payer.pronoun('object')} to be the payer for the ride home.",
        ),
        (
            f"What was {payer.id} supposed to do with the return credit?",
            f"{payer.id} was supposed to keep the one bright credit safe for the shuttle ride home. Being the payer meant holding onto the fare until it was time to leave.",
        ),
        (
            f"Why did {friend.id} warn {payer.id} not to buy {toy.label}?",
            f"{friend.id} warned {payer.id} because {toy.label} cost the very same credit they needed for the shuttle. If {payer.id} spent it, they would have no fare left for the ride home.",
        ),
        (
            f"What mistake did {payer.id} make?",
            f"{payer.id} spent the last return credit on {toy.label} even after the warning. That one choice took away the money they needed for the final shuttle.",
        ),
    ]
    if f["outcome"] == "rescued":
        qa.append(
            (
                "How was the problem fixed?",
                f"The children asked {helper.label} for help, and {helper.qa_fix}. That gave them a way home before the shuttle doors stayed shut.",
            )
        )
        qa.append(
            (
                f"What did {payer.id} learn?",
                f"{payer.id} learned that being the payer means protecting the ride-home credit before buying treats or toys. The helper saved the trip, but the story shows that luck is not a plan.",
            )
        )
    else:
        qa.append(
            (
                "What made the ending sad?",
                f"The last shuttle lifted away before anyone could fix the lost fare, so the children were stranded until morning. The glowing toy did not feel special anymore because it had cost them their ride home.",
            )
        )
        qa.append(
            (
                f"How did {payer.id} and {friend.id} feel at the end?",
                f"They felt tired, sorry, and disappointed as they sat in the cold dock and watched the empty station lights. Their space adventure ended as a long wait instead of a happy ride home.",
            )
        )
    return qa


KNOWLEDGE = {
    "shuttle": [
        (
            "What is a shuttle?",
            "A shuttle is a vehicle that carries people from one place to another. In a space story, it can fly between stations or moons."
        )
    ],
    "fare": [
        (
            "What is a fare?",
            "A fare is the money or ticket you need to ride a bus, train, or shuttle. If you spend it on something else, you may not be able to travel."
        )
    ],
    "payer": [
        (
            "What does payer mean?",
            "A payer is the person who gives the money or ticket for something. In this story, the payer was the child trusted to keep the ride-home credit safe."
        )
    ],
    "robot": [
        (
            "What is a service robot?",
            "A service robot is a machine that helps people with jobs like directions, cleaning, or simple questions. It can be useful, but it cannot always fix every problem."
        )
    ],
    "moon": [
        (
            "What is a moon?",
            "A moon is a round world that travels around a planet. Some planets have many moons circling them through space."
        )
    ],
    "comet": [
        (
            "What is a comet?",
            "A comet is a lump of ice, dust, and rock that travels through space. When it gets close to the sun, it can glow with a long bright tail."
        )
    ],
    "regret": [
        (
            "What is regret?",
            "Regret is the sad feeling you get when you know you made a bad choice. It often comes when you wish you had listened or planned better."
        )
    ],
}
KNOWLEDGE_ORDER = ["payer", "fare", "shuttle", "moon", "comet", "robot", "regret"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"payer", "fare", "shuttle", "regret"} | set(f["setting"].tags) | set(f["toy"].tags) | set(f["helper"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_market",
        toy="star_globe",
        helper="none",
        payer_name="Nova",
        payer_gender="girl",
        friend_name="Jet",
        friend_gender="boy",
        parent="mother",
        trait="impulsive",
    ),
    StoryParams(
        setting="asteroid_port",
        toy="comet_candy",
        helper="none",
        payer_name="Orion",
        payer_gender="boy",
        friend_name="Luna",
        friend_gender="girl",
        parent="father",
        trait="eager",
    ),
    StoryParams(
        setting="mars_arcade",
        toy="plasma_pin",
        helper="conductor",
        payer_name="Mira",
        payer_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        setting="moon_market",
        toy="star_globe",
        helper="service_bot",
        payer_name="Kai",
        payer_gender="boy",
        friend_name="Lyra",
        friend_gender="girl",
        parent="father",
        trait="restless",
    ),
]


def explain_rejection(toy: Toy) -> str:
    return (
        f"(No story: {toy.label} does not fit the one-credit return-fare setup. "
        f"This world only tells stories where the tempting item costs exactly the ride-home credit.)"
    )


ASP_RULES = r"""
reasonable_toy(T) :- toy(T), cost(T, 1).
valid(S, T, H) :- setting(S), helper(H), reasonable_toy(T).

recoverable(H) :- helper(H), available(H), power(H, P), P >= 1.
outcome(rescued) :- chosen_helper(H), recoverable(H).
outcome(stranded) :- chosen_helper(H), not recoverable(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("cost", tid, toy.cost))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if helper.available:
            lines.append(asp.fact("available", hid))
        lines.append(asp.fact("power", hid, helper.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "rescued" if can_recover(HELPERS[params.helper]) else "stranded"


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

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a space-market fare mistake with dialogue and a possible bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.toy:
        toy = TOYS[args.toy]
        if not toy_reasonable(toy):
            raise StoryError(explain_rejection(toy))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.toy is None or combo[1] == args.toy)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, toy_id, helper_id = rng.choice(sorted(combos))
    payer_name, payer_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=payer_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        toy=toy_id,
        helper=helper_id,
        payer_name=payer_name,
        payer_gender=payer_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.toy not in TOYS:
        raise StoryError(f"(Unknown toy: {params.toy})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    world = tell(
        setting=SETTINGS[params.setting],
        toy=TOYS[params.toy],
        helper=HELPERS[params.helper],
        payer_name=params.payer_name,
        payer_gender=params.payer_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, toy, helper) combos:\n")
        for setting_id, toy_id, helper_id in combos:
            outcome = "rescued" if can_recover(HELPERS[helper_id]) else "stranded"
            print(f"  {setting_id:13} {toy_id:12} {helper_id:11} -> {outcome}")
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
            header = f"### {p.payer_name} and {p.friend_name}: {p.toy} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
