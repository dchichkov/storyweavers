#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ceiling_station_kindness_folk_tale.py
================================================================

A standalone story world for a small folk-tale-like domain built around
kindness at a railway station.

Seed cues
---------
Words: ceiling, station
Feature: Kindness
Style: Folk Tale

Premise
-------
At a small old station, a child does one kind thing for someone or something
near the ceiling of the station hall. Later, a traveler's paper ticket is blown
up to the ceiling beams. The earlier kindness changes who is willing to help
and whether the ticket is brought down in time.

The world model prefers a narrow set of plausible kindness/repair pairings:
a porter is helped with food and later reaches the ticket with a hook; a
painter is helped with a paint pail and later climbs a ladder; swallows are
helped when a nestling is lifted back to the ceiling nest, and later they
flutter the ticket loose. The chosen helper's ability, the station height, and
the delay before the train leaves decide the ending.

Run it
------
python storyworlds/worlds/gpt-5.4/ceiling_station_kindness_folk_tale.py
python storyworlds/worlds/gpt-5.4/ceiling_station_kindness_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/ceiling_station_kindness_folk_tale.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/ceiling_station_kindness_folk_tale.py --helper swallows --kindness lift_nestling
python storyworlds/worlds/gpt-5.4/ceiling_station_kindness_folk_tale.py --helper porter --kindness carry_pail
python storyworlds/worlds/gpt-5.4/ceiling_station_kindness_folk_tale.py --qa --json
python storyworlds/worlds/gpt-5.4/ceiling_station_kindness_folk_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "porter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Station:
    id: str
    label: str
    ceiling_desc: str
    platform_desc: str
    wind_desc: str
    closing_image: str
    height: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperConfig:
    id: str
    label: str
    type: str
    need_desc: str
    return_need: str
    method_text: str
    fail_text: str
    qa_text: str
    power: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class KindAct:
    id: str
    text: str
    qa_text: str
    suits: set[str] = field(default_factory=set)
    kindness_gain: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    station: str
    helper: str
    kindness: str
    child_name: str
    child_gender: str
    traveler_name: str
    traveler_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
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
        clone = World(self.station)
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


def _r_gratitude(world: World) -> list[str]:
    helper = world.entities.get("helper")
    ticket = world.entities.get("ticket")
    traveler = world.entities.get("traveler")
    if helper is None or ticket is None or traveler is None:
        return []
    if helper.memes["owed_kindness"] < THRESHOLD or ticket.meters["stuck"] < THRESHOLD:
        return []
    sig = ("gratitude", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["ready_to_help"] += 1
    traveler.memes["hope"] += 1
    return ["__ready__"]


def _r_worry(world: World) -> list[str]:
    traveler = world.entities.get("traveler")
    if traveler is None:
        return []
    if traveler.meters["ticket_lost"] < THRESHOLD:
        return []
    sig = ("worry", traveler.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    traveler.memes["worry"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="gratitude", tag="social", apply=_r_gratitude),
    Rule(name="worry", tag="social", apply=_r_worry),
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
        for line in produced:
            world.say(line)
    return produced


STATIONS = {
    "hill": Station(
        id="hill",
        label="the little hill station",
        ceiling_desc="a ceiling of honey-colored beams where swallows liked to nest",
        platform_desc="a narrow platform with red geraniums in cracked pots",
        wind_desc="a mountain gust that came racing in before the train",
        closing_image="the station lamps shone on the rails like thin golden threads",
        height=1,
        tags={"station", "ceiling", "train"},
    ),
    "river": Station(
        id="river",
        label="the river station",
        ceiling_desc="a blue-painted ceiling crossed by dark rafters",
        platform_desc="a platform that smelled of wet wood and reeds",
        wind_desc="a river wind that slipped under the eaves and whirled the waiting room air",
        closing_image="the river beyond the tracks held the evening light like a mirror",
        height=2,
        tags={"station", "ceiling", "train"},
    ),
    "pine": Station(
        id="pine",
        label="the pine-wood station",
        ceiling_desc="a high wooden ceiling that kept the scent of resin all year long",
        platform_desc="a platform bordered by quiet pines and stacked milk cans",
        wind_desc="a cold breath from the forest that swept in with the whistle",
        closing_image="the dark pines stood around the station as still as old guards",
        height=2,
        tags={"station", "ceiling", "train"},
    ),
    "grand": Station(
        id="grand",
        label="the old grand station",
        ceiling_desc="a very tall ceiling of arches and beams, far above the ticket bench",
        platform_desc="a broad platform where many shoes clicked and hurried",
        wind_desc="a hard draft that rushed through the hall as the engine sighed",
        closing_image="high over the station, the last smoke drifted under the rafters like gray silk",
        height=3,
        tags={"station", "ceiling", "train"},
    ),
}

HELPERS = {
    "porter": HelperConfig(
        id="porter",
        label="the porter",
        type="porter",
        need_desc="the porter had missed his breakfast and his stomach growled while he dragged a trunk cart",
        return_need="a long baggage hook leaning by the trunk cart",
        method_text="remembered the warm roll, caught up the long baggage hook, and gently lifted the paper ticket down from the beam",
        fail_text="caught up the long baggage hook and tried to reach the paper ticket, but the beam was too high and the train bell was already ringing",
        qa_text="used a long baggage hook to lift the ticket down",
        power=4,
        tags={"porter", "hook", "kindness"},
    ),
    "painter": HelperConfig(
        id="painter",
        label="the station painter",
        type="man",
        need_desc="the station painter was wobbling with a heavy paint pail beneath the rafters",
        return_need="his ladder still standing under the rafters",
        method_text="set his ladder beneath the beam, climbed carefully, and pinched the ticket free with paint-spotted fingers",
        fail_text="set his ladder beneath the beam and climbed as fast as he dared, but the train gave its second bell before he could get the ticket loose",
        qa_text="climbed a ladder and freed the ticket with his hand",
        power=3,
        tags={"painter", "ladder", "kindness"},
    ),
    "swallows": HelperConfig(
        id="swallows",
        label="the swallows",
        type="birds",
        need_desc="a swallow chick had tumbled from a nest tucked near the ceiling beam",
        return_need="their little mud nest still trembling high under the beam",
        method_text="darted around the beam in a rush of wings until the loosened ticket came twirling down like a pale leaf",
        fail_text="darted and circled near the beam, but the ticket clung fast while the engine cried out for the last boarding",
        qa_text="fluttered around the beam until the ticket came loose",
        power=2,
        tags={"swallows", "birds", "kindness"},
    ),
}

KINDNESS_ACTS = {
    "share_roll": KindAct(
        id="share_roll",
        text="broke a warm roll in half and gave the softer half away",
        qa_text="shared a warm roll with the hungry porter",
        suits={"porter"},
        kindness_gain=2,
        tags={"food", "sharing", "kindness"},
    ),
    "carry_pail": KindAct(
        id="carry_pail",
        text="took the paint pail with both hands and carried it where the painter needed it",
        qa_text="helped carry the painter's heavy paint pail",
        suits={"painter"},
        kindness_gain=2,
        tags={"helping", "paint", "kindness"},
    ),
    "lift_nestling": KindAct(
        id="lift_nestling",
        text="cupped a fallen swallow chick in gentle hands and set it back in its nest under the ceiling",
        qa_text="lifted a fallen swallow chick back to its nest near the ceiling",
        suits={"swallows"},
        kindness_gain=2,
        tags={"birds", "rescue", "kindness"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Anya", "Tessa", "Rina", "Nora", "Sita", "Mila"]
BOY_NAMES = ["Ivo", "Niko", "Taran", "Milan", "Kiran", "Pavel", "Emil", "Jori"]
TRAVELER_NAMES = ["Grandmother Sava", "Auntie Brina", "Old Tomas", "Mrs. Vale", "Uncle Petru"]
TRAITS = ["kind", "patient", "bright-eyed", "quiet", "careful", "steady"]


def valid_combo(helper_id: str, kindness_id: str) -> bool:
    helper = HELPERS[helper_id]
    kindness = KINDNESS_ACTS[kindness_id]
    return helper.id in kindness.suits


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for station_id in STATIONS:
        for helper_id in HELPERS:
            for kindness_id in KINDNESS_ACTS:
                if valid_combo(helper_id, kindness_id):
                    combos.append((station_id, helper_id, kindness_id))
    return combos


def urgency(station: Station, delay: int) -> int:
    return station.height + delay


def caught_in_time(helper: HelperConfig, station: Station, delay: int) -> bool:
    return helper.power >= urgency(station, delay)


def outcome_of(params: StoryParams) -> str:
    if not valid_combo(params.helper, params.kindness):
        raise StoryError(explain_rejection(params.helper, params.kindness))
    return "caught_train" if caught_in_time(HELPERS[params.helper], STATIONS[params.station], params.delay) else "missed_train"


def explain_rejection(helper_id: str, kindness_id: str) -> str:
    helper = HELPERS[helper_id]
    kindness = KINDNESS_ACTS[kindness_id]
    return (
        f"(No story: {kindness.id.replace('_', ' ')} does not fit {helper.label}. "
        f"In this folk-tale world, kindness must grow naturally into the later rescue.)"
    )


def predict_rescue(world: World) -> dict:
    sim = world.copy()
    helper = sim.get("helper")
    station = sim.station
    ticket = sim.get("ticket")
    ticket.meters["stuck"] += 1
    ticket.meters["ticket_lost"] += 1
    sim.get("traveler").meters["ticket_lost"] += 1
    propagate(sim, narrate=False)
    return {
        "ready": helper.memes["ready_to_help"] >= THRESHOLD,
        "in_time": caught_in_time(HELPERS[sim.facts["helper_cfg"].id], station, sim.facts["delay"]),
    }


def opening(world: World, child: Entity, station: Station) -> None:
    trait = next((t for t in child.traits if t != "little"), "kind")
    world.say(
        f"In the days when every whistle seemed to carry a tale over the hills, there was a little {child.type} "
        f"named {child.id} who worked and wandered at {station.label}. {child.pronoun().capitalize()} was a {trait} child, "
        f"and {station.platform_desc}."
    )
    world.say(
        f"Inside the waiting hall hung {station.ceiling_desc}, so high that even grown-ups often looked up before they spoke."
    )


def show_need(world: World, helper_cfg: HelperConfig) -> None:
    world.say(f"That morning, {helper_cfg.need_desc}.")


def do_kindness(world: World, child: Entity, helper: Entity, kindness: KindAct) -> None:
    child.memes["kindness"] += kindness.kindness_gain
    helper.memes["owed_kindness"] += kindness.kindness_gain
    helper.memes["trust"] += 1
    world.say(
        f"{child.id} saw this and {kindness.text}. No bell commanded it and no one paid for it; "
        f"{child.pronoun()} simply could not pass by a need with a shut heart."
    )


def traveler_arrives(world: World, traveler: Entity, station: Station) -> None:
    world.say(
        f"Before long, {traveler.id} came hurrying into the station, clutching a paper ticket and a little bag. "
        f"{traveler.pronoun().capitalize()} looked tired from the road, and the train was due with scarcely a minute to spare."
    )
    world.say(
        f'"Please let this old ticket stay with me until the train comes," {traveler.pronoun()} murmured.'
    )


def trouble(world: World, traveler: Entity, station: Station) -> None:
    ticket = world.get("ticket")
    ticket.meters["stuck"] += 1
    ticket.meters["ticket_lost"] += 1
    traveler.meters["ticket_lost"] += 1
    traveler.memes["worry"] += 1
    world.say(
        f"Then {station.wind_desc}. The paper jumped from {traveler.pronoun('possessive')} fingers, flew up, and caught on a beam near the ceiling."
    )
    world.say(
        f'"My ticket!" cried {traveler.id}. "Without it, I cannot board at all."'
    )
    propagate(world, narrate=False)


def ask_for_help(world: World, child: Entity, helper: Entity) -> None:
    pred = predict_rescue(world)
    world.facts["predicted_ready"] = pred["ready"]
    world.facts["predicted_in_time"] = pred["in_time"]
    if helper.type == "birds":
        world.say(
            f"{child.id} looked up at the swallows' nest and remembered the small life once cupped in {child.pronoun('possessive')} hands."
        )
    else:
        world.say(
            f"{child.id} remembered the morning kindness and turned at once to {helper.label}."
        )
    if pred["ready"]:
        world.say(
            f'There was no shame in asking. "{helper.label_word.capitalize()}, will you help?" {child.pronoun()} called.'
        )
    else:
        world.say(
            f'{child.id} called for help, but the moment already felt slippery as rain.'
        )


def rescue(world: World, child: Entity, traveler: Entity, helper: Entity, helper_cfg: HelperConfig, station: Station) -> None:
    ticket = world.get("ticket")
    helper.memes["helping"] += 1
    traveler.memes["hope"] += 1
    ticket.meters["stuck"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} {helper_cfg.method_text}. {child.id} caught it before the wind could snatch it again."
    )
    world.say(
        f'{child.pronoun().capitalize()} placed the ticket back in {traveler.id}\'s hand, and {traveler.pronoun("possessive")} face softened like winter snow in sun.'
    )
    world.say(
        f"The guard waved, the train door stayed open one more breath, and {traveler.id} climbed aboard in time."
    )


def blessing(world: World, child: Entity, traveler: Entity, station: Station) -> None:
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    traveler.memes["gratitude"] += 1
    world.say(
        f'Before the carriage rolled away, {traveler.id} leaned from the window and said, '
        f'"A kind hand is longer than any ladder. May help find you whenever you need it."'
    )
    world.say(
        f"And when the train had gone, {station.closing_image}, and {child.id} felt that the whole station had grown warmer under its ceiling."
    )


def fail_rescue(world: World, child: Entity, traveler: Entity, helper: Entity, helper_cfg: HelperConfig, station: Station) -> None:
    helper.memes["helping"] += 1
    world.say(f"{helper.label_word.capitalize()} {helper_cfg.fail_text}.")
    world.say(
        f"The guard had to shut the door. The train pulled away while {traveler.id} stood with empty hands beneath the station ceiling."
    )


def consolation(world: World, child: Entity, traveler: Entity, station: Station) -> None:
    child.memes["kindness"] += 1
    child.memes["lesson"] += 1
    traveler.memes["gratitude"] += 1
    world.say(
        f"{child.id} did not leave {traveler.id} alone. {child.pronoun().capitalize()} shared the bench, fetched a cup of water, "
        f"and stayed until the station master wrote a note for the next train."
    )
    world.say(
        f'Then {traveler.id} touched {child.pronoun("possessive")} shoulder and said, '
        f'"Even when a train is missed, kindness does not miss its road."'
    )
    world.say(
        f"By sunset, {station.closing_image}, and the waiting hall no longer seemed lonely."
    )


def tell(
    station: Station,
    helper_cfg: HelperConfig,
    kindness: KindAct,
    child_name: str = "Mira",
    child_gender: str = "girl",
    traveler_name: str = "Grandmother Sava",
    traveler_type: str = "woman",
    trait: str = "kind",
    delay: int = 0,
) -> World:
    world = World(station)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["little", trait],
    ))
    traveler = world.add(Entity(
        id=traveler_name,
        kind="character",
        type=traveler_type,
        label=traveler_name,
        role="traveler",
    ))
    if helper_cfg.id == "swallows":
        helper_type = "birds"
    else:
        helper_type = helper_cfg.type
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_cfg.label,
        role="helper",
    ))
    ticket = world.add(Entity(
        id="ticket",
        kind="thing",
        type="ticket",
        label="ticket",
        phrase="a paper ticket",
        role="ticket",
    ))
    world.facts["delay"] = delay
    world.facts["helper_cfg"] = helper_cfg

    opening(world, child, station)
    show_need(world, helper_cfg)
    do_kindness(world, child, helper, kindness)

    world.para()
    traveler_arrives(world, traveler, station)
    trouble(world, traveler, station)
    ask_for_help(world, child, helper)

    world.para()
    in_time = caught_in_time(helper_cfg, station, delay)
    if in_time:
        rescue(world, child, traveler, helper, helper_cfg, station)
        world.para()
        blessing(world, child, traveler, station)
        outcome = "caught_train"
    else:
        fail_rescue(world, child, traveler, helper, helper_cfg, station)
        world.para()
        consolation(world, child, traveler, station)
        outcome = "missed_train"

    world.facts.update(
        child=child,
        traveler=traveler,
        helper=helper,
        station=station,
        helper_cfg=helper_cfg,
        kindness=kindness,
        ticket=ticket,
        outcome=outcome,
        in_time=in_time,
        urgency=urgency(station, delay),
    )
    return world


KNOWLEDGE = {
    "station": [
        ("What is a station?", "A station is a place where trains stop so people can get on or off. It often has a platform, benches, and a waiting room.")
    ],
    "ceiling": [
        ("What is a ceiling?", "A ceiling is the inside top part of a room, above your head. In old buildings it may have beams or rafters.")
    ],
    "train": [
        ("Why do trains have stations?", "Trains use stations so passengers can wait safely and board in the right place. The station helps many journeys fit together.")
    ],
    "porter": [
        ("What does a porter do at a station?", "A porter helps move heavy trunks and bags. Porters often know the station very well because they work all through it.")
    ],
    "ladder": [
        ("Why is a ladder useful?", "A ladder helps a person reach something high above the floor. It is useful when hands alone are not long enough.")
    ],
    "birds": [
        ("Why do swallows build nests high up?", "Swallows like high places because they feel safer there. Beams under a roof can protect their nests from weather.")
    ],
    "kindness": [
        ("What is kindness?", "Kindness is choosing to help, comfort, or share even when no one forces you to do it. A kind act can change how a whole day turns out.")
    ],
    "sharing": [
        ("Why is sharing food kind?", "Sharing food is kind because it gives comfort to someone who is hungry. It says, 'Your need matters to me.'")
    ],
    "rescue": [
        ("Why can a small rescue matter later?", "A small rescue can matter later because people and animals remember help. Kindness often opens the door to more kindness.")
    ],
}
KNOWLEDGE_ORDER = ["station", "ceiling", "train", "porter", "ladder", "birds", "kindness", "sharing", "rescue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    station = f["station"]
    helper_cfg = f["helper_cfg"]
    kindness = f["kindness"]
    outcome = f["outcome"]
    base = (
        f'Write a short folk tale for a 3-to-5-year-old set in {station.label} with the words "station" and "ceiling". '
        f'The story should center on kindness.'
    )
    if outcome == "caught_train":
        return [
            base,
            f"Tell a folk tale where {child.id} does one kind deed for {helper_cfg.label}, and later that kindness helps bring a traveler's ticket down from the ceiling in time for the train.",
            f'Write a gentle railway folk tale where a child\'s kindness returns like an echo and saves the day at the station.',
        ]
    return [
        base,
        f"Tell a wistful folk tale where {child.id}'s kindness brings help, but the train is still missed because time runs too fast at the high station ceiling.",
        f'Write a story where kindness cannot stop every loss, yet it keeps a lonely station from feeling cold.',
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    traveler = f["traveler"]
    helper_cfg = f["helper_cfg"]
    kindness = f["kindness"]
    station = f["station"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child at {station.label}, and {traveler.id}, a traveler whose ticket flew up near the ceiling. {helper_cfg.label_word.capitalize()} also mattered, because the earlier kindness shaped the rescue."
        ),
        (
            f"What kind thing did {child.id} do?",
            f"{child.id} {kindness.qa_text}. That act mattered later because kindness made help come back when the trouble began."
        ),
        (
            "What problem happened at the station?",
            f"A gust in the station hall blew the paper ticket up to a beam near the ceiling. Without the ticket, {traveler.id} could not board the train."
        ),
        (
            f"Why did {child.id} ask {helper_cfg.label} for help?",
            f"{child.id} remembered the kind deed from earlier. In this story, the earlier kindness gave {helper_cfg.label} a reason to help quickly when the ticket was stuck high above them."
        ),
    ]
    if outcome == "caught_train":
        qa.append((
            "How was the ticket brought down?",
            f"{helper_cfg.label_word.capitalize()} {helper_cfg.qa_text}. Because the help came fast enough for that station and that moment, the traveler caught the train."
        ))
        qa.append((
            "How did the story end?",
            f"{traveler.id} boarded the train in time and blessed {child.id}. The ending image shows the station feeling warmer, because kindness had changed the whole place."
        ))
    else:
        qa.append((
            "Did the traveler catch the train?",
            f"No. {helper_cfg.label_word.capitalize()} tried to help, but the station was too high and time was too short, so the train left first. Even so, {child.id} stayed with {traveler.id} and showed kindness again afterward."
        ))
        qa.append((
            "What did the child do after the train left?",
            f"{child.id} stayed beside {traveler.id}, shared the bench, and fetched water while the next plan was made. That second kindness turned a sad moment into a gentler one."
        ))
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["station"].tags) | {"kindness"}
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["kindness"].tags)
    if f["helper_cfg"].id == "swallows":
        tags.add("rescue")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        station="hill",
        helper="swallows",
        kindness="lift_nestling",
        child_name="Mira",
        child_gender="girl",
        traveler_name="Grandmother Sava",
        traveler_type="woman",
        trait="kind",
        delay=0,
    ),
    StoryParams(
        station="river",
        helper="painter",
        kindness="carry_pail",
        child_name="Niko",
        child_gender="boy",
        traveler_name="Mrs. Vale",
        traveler_type="woman",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        station="grand",
        helper="painter",
        kindness="carry_pail",
        child_name="Lila",
        child_gender="girl",
        traveler_name="Old Tomas",
        traveler_type="man",
        trait="patient",
        delay=1,
    ),
    StoryParams(
        station="pine",
        helper="porter",
        kindness="share_roll",
        child_name="Emil",
        child_gender="boy",
        traveler_name="Auntie Brina",
        traveler_type="woman",
        trait="quiet",
        delay=0,
    ),
    StoryParams(
        station="river",
        helper="swallows",
        kindness="lift_nestling",
        child_name="Anya",
        child_gender="girl",
        traveler_name="Uncle Petru",
        traveler_type="man",
        trait="bright-eyed",
        delay=1,
    ),
]


ASP_RULES = r"""
% kindness fits helper
valid(H, K) :- helper(H), kindness(K), suits(K, H).

% a full story choice also needs a station
valid_story(S, H, K) :- station(S), valid(H, K).

% outcome
urgency(U) :- chosen_station(S), height(S, H), delay(D), U = H + D.
caught_train :- chosen_helper(H), power(H, P), urgency(U), P >= U.
outcome(caught_train) :- caught_train.
outcome(missed_train) :- not caught_train.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for station_id, station in STATIONS.items():
        lines.append(asp.fact("station", station_id))
        lines.append(asp.fact("height", station_id, station.height))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
    for kindness_id, kindness in KINDNESS_ACTS.items():
        lines.append(asp.fact("kindness", kindness_id))
        for helper_id in sorted(kindness.suits):
            lines.append(asp.fact("suits", kindness_id, helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_station", params.station),
        asp.fact("chosen_helper", params.helper),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    parser = build_parser()
    for seed in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        sample = generate(cases[0])
        if not sample.story or "station" not in sample.story.lower() or "ceiling" not in sample.story.lower():
            raise StoryError("smoke test story missing required content")
        emit(sample, trace=False, qa=False, header="")  # smoke test for ordinary emit
        print("OK: smoke test generation and emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: a kind deed at a station returns when a ticket flies to the ceiling."
    )
    ap.add_argument("--station", choices=STATIONS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--kindness", choices=KINDNESS_ACTS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how many extra beats pass before the train must leave")
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--traveler-name")
    ap.add_argument("--traveler-type", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story choices from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.kindness and not valid_combo(args.helper, args.kindness):
        raise StoryError(explain_rejection(args.helper, args.kindness))

    combos = [
        combo for combo in valid_combos()
        if (args.station is None or combo[0] == args.station)
        and (args.helper is None or combo[1] == args.helper)
        and (args.kindness is None or combo[2] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    station_id, helper_id, kindness_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    traveler_name = args.traveler_name or rng.choice(TRAVELER_NAMES)
    traveler_type = args.traveler_type or ("woman" if any(x in traveler_name for x in ["Grandmother", "Auntie", "Mrs."]) else "man")
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        station=station_id,
        helper=helper_id,
        kindness=kindness_id,
        child_name=child_name,
        child_gender=child_gender,
        traveler_name=traveler_name,
        traveler_type=traveler_type,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.station not in STATIONS:
        raise StoryError(f"(Unknown station: {params.station})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.kindness not in KINDNESS_ACTS:
        raise StoryError(f"(Unknown kindness act: {params.kindness})")
    if not valid_combo(params.helper, params.kindness):
        raise StoryError(explain_rejection(params.helper, params.kindness))

    world = tell(
        station=STATIONS[params.station],
        helper_cfg=HELPERS[params.helper],
        kindness=KINDNESS_ACTS[params.kindness],
        child_name=params.child_name,
        child_gender=params.child_gender,
        traveler_name=params.traveler_name,
        traveler_type=params.traveler_type,
        trait=params.trait,
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
        print(asp_program("", "#show valid_story/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (station, helper, kindness) choices:\n")
        for station_id, helper_id, kindness_id in combos:
            print(f"  {station_id:7} {helper_id:9} {kindness_id}")
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
            header = f"### {p.child_name}: {p.station}, {p.helper}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
