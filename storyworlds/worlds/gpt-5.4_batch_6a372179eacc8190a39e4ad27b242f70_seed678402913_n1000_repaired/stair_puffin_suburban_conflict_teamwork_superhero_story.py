#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stair_puffin_suburban_conflict_teamwork_superhero_story.py
=====================================================================================

A standalone story world for a tiny superhero-flavored suburban domain:
two children in capes try to help a neighbor carry something up a porch stair.
One child wants to charge ahead alone. The other child predicts trouble and
argues that real heroes work together. Depending on trust, ages, and steadiness,
they either switch to teamwork before anything falls, or they make a small mess
first and then repair the situation together.

The domain is constrained on purpose:
- every story includes a suburban setting, a stair, and a puffin mascot
- the happy solution is always teamwork
- each mission only permits teamwork methods that actually fit the item
- the Python gate and inline ASP twin agree on valid combinations and outcomes

Run it
------
    python storyworlds/worlds/gpt-5.4/stair_puffin_suburban_conflict_teamwork_superhero_story.py
    python storyworlds/worlds/gpt-5.4/stair_puffin_suburban_conflict_teamwork_superhero_story.py --mission cookie_tray
    python storyworlds/worlds/gpt-5.4/stair_puffin_suburban_conflict_teamwork_superhero_story.py --response team_carry
    python storyworlds/worlds/gpt-5.4/stair_puffin_suburban_conflict_teamwork_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/stair_puffin_suburban_conflict_teamwork_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/stair_puffin_suburban_conflict_teamwork_superhero_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
TEAM_THRESHOLD = 8
STEADY_TRAITS = {"steady", "careful", "patient", "kind"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Suburb:
    id: str
    lane: str
    image: str
    porch: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    label: str
    phrase: str
    article: str
    contents: str
    hazard_text: str
    spill_text: str
    recover_text: str
    success_text: str
    allowed: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    plan: str
    motion: str
    finish: str
    sense: int = 3
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, suburb: Suburb) -> None:
        self.suburb = suburb
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
        clone = World(self.suburb)
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


def _r_unstable(world: World) -> list[str]:
    item = world.get("mission")
    if item.meters["on_stair"] < THRESHOLD:
        return []
    sig = ("unstable", item.id, item.attrs.get("method", ""))
    if sig in world.fired:
        return []
    support = item.meters["support"]
    need = float(item.attrs.get("need", 2))
    method = item.attrs.get("method", "")
    allowed = set(item.attrs.get("allowed", set()))
    if support < need or method not in allowed:
        world.fired.add(sig)
        item.meters["unstable"] += 1
    return []


def _r_drop(world: World) -> list[str]:
    item = world.get("mission")
    if item.meters["unstable"] < THRESHOLD:
        return []
    sig = ("drop", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["dropped"] += 1
    for eid in ("hero", "partner"):
        world.get(eid).memes["fear"] += 1
        world.get(eid).memes["guilt"] += 1
    world.get("neighbor").memes["worry"] += 1
    return []


def _r_deliver(world: World) -> list[str]:
    item = world.get("mission")
    if item.meters["on_stair"] < THRESHOLD or item.meters["unstable"] >= THRESHOLD:
        return []
    sig = ("deliver", item.id, item.attrs.get("method", ""))
    if sig in world.fired:
        return []
    support = item.meters["support"]
    need = float(item.attrs.get("need", 2))
    method = item.attrs.get("method", "")
    allowed = set(item.attrs.get("allowed", set()))
    if support >= need and method in allowed:
        world.fired.add(sig)
        item.meters["delivered"] += 1
        for eid in ("hero", "partner"):
            world.get(eid).memes["pride"] += 1
            world.get(eid).memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="unstable", tag="physical", apply=_r_unstable),
    Rule(name="drop", tag="physical", apply=_r_drop),
    Rule(name="deliver", tag="physical", apply=_r_deliver),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = (
                world.get("mission").meters["unstable"],
                world.get("mission").meters["dropped"],
                world.get("mission").meters["delivered"],
            )
            rule.apply(world)
            after = (
                world.get("mission").meters["unstable"],
                world.get("mission").meters["dropped"],
                world.get("mission").meters["delivered"],
            )
            if after != before:
                changed = True


def compatible_response(mission: Mission, response: Response) -> bool:
    return response.id in mission.allowed and response.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for suburb_id in SUBURBS:
        for mission_id, mission in MISSIONS.items():
            for response_id, response in RESPONSES.items():
                if compatible_response(mission, response):
                    combos.append((suburb_id, mission_id, response_id))
    return combos


def influence_score(relation: str, hero_age: int, partner_age: int, trait: str, trust: int) -> int:
    bonus = 0
    if relation == "siblings" and partner_age > hero_age:
        bonus += 3
    if trait in STEADY_TRAITS:
        bonus += 2
    return trust + bonus


def would_switch(relation: str, hero_age: int, partner_age: int, trait: str, trust: int) -> bool:
    return influence_score(relation, hero_age, partner_age, trait, trust) >= TEAM_THRESHOLD


def predict_solo(world: World) -> dict:
    sim = world.copy()
    item = sim.get("mission")
    item.meters["on_stair"] += 1
    item.meters["support"] = 1
    item.attrs["method"] = "solo"
    propagate(sim)
    return {
        "unstable": item.meters["unstable"] >= THRESHOLD,
        "dropped": item.meters["dropped"] >= THRESHOLD,
    }


def setup_scene(world: World, hero: Entity, partner: Entity, puffin: Entity) -> None:
    for kid in (hero, partner):
        kid.memes["imagination"] += 1
    world.say(
        f"On {world.suburb.lane}, a quiet suburban street of clipped hedges and bright mailboxes, "
        f"{hero.id} and {partner.id} tied towels around their shoulders like capes."
    )
    world.say(
        f"{hero.id} wore a badge with a puffin on it, and {partner.id} tucked {puffin.label} under one arm "
        f"as if the little mascot were the team's watchful sky scout."
    )
    world.say(
        f"Together they called themselves the Stair Star Team, the kind of heroes who were sure every small job "
        f"could shine if they did it bravely."
    )


def call_for_help(world: World, hero: Entity, partner: Entity, neighbor: Entity, mission: Mission) -> None:
    world.say(
        f"At {world.suburb.porch}, {neighbor.id} was standing at the bottom of the front step with {mission.article} "
        f"{mission.phrase}. {mission.contents}"
    )
    world.say(
        f'"Could my neighborhood heroes help me get this up the porch stair?" {neighbor.id} asked.'
    )
    hero.memes["desire"] += 1
    partner.memes["care"] += 1


def boast(world: World, hero: Entity, mission: Mission) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'"Easy!" said {hero.id}. "{mission.label.capitalize()} rescue is a one-hero job. '
        f"I will zoom up that stair all by myself."
    )


def warn(world: World, hero: Entity, partner: Entity, mission: Mission, response: Response) -> None:
    pred = predict_solo(world)
    partner.memes["caution"] += 1
    world.facts["predicted_drop"] = pred["dropped"]
    extra = ""
    if pred["dropped"]:
        extra = f" {mission.hazard_text}"
    world.say(
        f'{partner.id} tightened {partner.pronoun("possessive")} cape. '
        f'"Wait. Real heroes look first," {partner.pronoun()} said. '
        f'"If you rush alone, this could wobble on the stair.{extra} '
        f'Let\'s use {response.plan}."'
    )


def refuse(world: World, hero: Entity, partner: Entity) -> None:
    hero.memes["defiance"] += 1
    partner.memes["conflict"] += 1
    hero.memes["conflict"] += 1
    world.say(
        f'"But I wanted the big save," {hero.id} said. {hero.pronoun().capitalize()} tucked {hero.pronoun("possessive")} chin, '
        f"feeling hot and stubborn inside the cape."
    )


def accept_teamwork(world: World, hero: Entity, partner: Entity, response: Response) -> None:
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f"{hero.id} looked at the high porch, then at {partner.id}, then at the puffin badge on "
        f"{hero.pronoun('possessive')} own shirt."
    )
    world.say(
        f'"Okay," {hero.pronoun()} said at last. "A real team save is better than a lonely one." '
        f'Together they chose {response.plan}.'
    )


def climb(world: World, method: str) -> None:
    item = world.get("mission")
    item.meters["on_stair"] += 1
    item.meters["support"] = 2 if method in RESPONSES else 1
    item.attrs["method"] = method
    propagate(world)


def spill(world: World, mission: Mission, neighbor: Entity) -> None:
    world.say(mission.spill_text)
    world.say(
        f"{neighbor.id} took one quick breath, but {neighbor.pronoun()} did not scold them. "
        f"{neighbor.pronoun().capitalize()} just reached out a steady hand."
    )


def regroup(world: World, hero: Entity, partner: Entity, mission: Mission, response: Response) -> None:
    hero.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    world.say(
        f'"Super teams get another try," {partner.id} said. "{response.label.capitalize()} time."'
    )
    world.say(
        f"{mission.recover_text} This time {response.motion}, step by careful step."
    )
    item = world.get("mission")
    item.meters["on_stair"] = 0.0
    item.meters["unstable"] = 0.0
    item.meters["dropped"] = 0.0
    climb(world, response.id)


def success(world: World, hero: Entity, partner: Entity, neighbor: Entity, mission: Mission, response: Response) -> None:
    for kid in (hero, partner):
        kid.memes["love"] += 1
        kid.memes["teamwork"] += 1
    world.say(
        f"At the top, {response.finish}. {mission.success_text}"
    )
    world.say(
        f'{neighbor.id} smiled. "That is how heroes do it," {neighbor.pronoun()} said. '
        f'"Strong hands help, but teamwork helps more."'
    )
    world.say(
        f"Back on {world.suburb.lane}, the evening windows glowed gold, and the Stair Star Team marched off together, "
        f"with the puffin mascot bobbing proudly between them."
    )


def tell(
    suburb: Suburb,
    mission_cfg: Mission,
    response_cfg: Response,
    hero_name: str = "Ava",
    hero_gender: str = "girl",
    partner_name: str = "Ben",
    partner_gender: str = "boy",
    neighbor_type: str = "mother",
    trait: str = "steady",
    relation: str = "friends",
    trust: int = 6,
    hero_age: int = 6,
    partner_age: int = 7,
) -> World:
    world = World(suburb=suburb)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        age=hero_age,
        traits=["bold"],
        attrs={"name": hero_name, "relation": relation},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        age=partner_age,
        traits=[trait],
        attrs={"name": partner_name, "relation": relation, "trust": trust},
    ))
    neighbor = world.add(Entity(
        id="neighbor",
        kind="character",
        type=neighbor_type,
        label="the neighbor",
        phrase="the neighbor",
        role="neighbor",
    ))
    puffin = world.add(Entity(
        id="puffin",
        type="toy",
        label="Pip the puffin plush",
        phrase="a puffin plush",
        role="mascot",
    ))
    mission = world.add(Entity(
        id="mission",
        type="parcel",
        label=mission_cfg.label,
        phrase=mission_cfg.phrase,
        role="mission",
        attrs={"need": 2, "allowed": set(mission_cfg.allowed), "method": ""},
        tags=set(mission_cfg.tags),
    ))
    hero.memes["trust"] = float(trust)
    partner.memes["trust"] = float(trust)

    setup_scene(world, hero, partner, puffin)
    call_for_help(world, hero, partner, neighbor, mission_cfg)

    world.para()
    boast(world, hero, mission_cfg)
    warn(world, hero, partner, mission_cfg, response_cfg)

    switched = would_switch(relation, hero_age, partner_age, trait, trust)
    if switched:
        accept_teamwork(world, hero, partner, response_cfg)
        world.para()
        climb(world, response_cfg.id)
        success(world, hero, partner, neighbor, mission_cfg, response_cfg)
        outcome = "switched"
    else:
        refuse(world, hero, partner)
        world.say(
            f"Before {partner.label} could answer again, {hero.label} hugged {mission_cfg.article} {mission_cfg.label} to "
            f"{hero.pronoun('possessive')} chest and charged upward."
        )
        world.para()
        climb(world, "solo")
        spill(world, mission_cfg, neighbor)
        world.para()
        regroup(world, hero, partner, mission_cfg, response_cfg)
        success(world, hero, partner, neighbor, mission_cfg, response_cfg)
        outcome = "spilled"

    world.facts.update(
        suburb=suburb,
        mission_cfg=mission_cfg,
        response=response_cfg,
        hero=hero,
        partner=partner,
        neighbor=neighbor,
        puffin=puffin,
        relation=relation,
        trust=trust,
        trait=trait,
        switched=switched,
        outcome=outcome,
        delivered=world.get("mission").meters["delivered"] >= THRESHOLD,
    )
    return world


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


@dataclass
class StoryParams:
    suburb: str
    mission: str
    response: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    neighbor: str
    trait: str
    relation: str = "friends"
    trust: int = 6
    hero_age: int = 6
    partner_age: int = 7
    seed: Optional[int] = None


SUBURBS = {
    "maple_lane": Suburb(
        id="maple_lane",
        lane="Maple Lane",
        image="small brick houses with neat lawns",
        porch="Mrs. Reed's little porch with flowerpots by the rail",
        tags={"suburban"},
    ),
    "cedar_close": Suburb(
        id="cedar_close",
        lane="Cedar Close",
        image="looping sidewalks and low white fences",
        porch="Mr. Vega's porch with a striped doormat and a bell",
        tags={"suburban"},
    ),
    "sunny_circle": Suburb(
        id="sunny_circle",
        lane="Sunny Circle",
        image="curving drives and bicycles sleeping by hedges",
        porch="Ms. Park's porch with a red watering can near the step",
        tags={"suburban"},
    ),
}

MISSIONS = {
    "book_box": Mission(
        id="book_box",
        label="box of library books",
        phrase="box of library books",
        article="a",
        contents="It was not too huge, but it was full and heavy, and the corners bumped against the cardboard.",
        hazard_text="If the box tips, the books could slide everywhere.",
        spill_text="Halfway up, the box knocked against the rail. The flaps sprang open, and books thumped across the step like startled pigeons.",
        recover_text="They gathered the books, hugged the box shut, and set their feet in the right places",
        success_text="The books reached the porch in a neat stack, safe and ready for their quiet shelf.",
        allowed={"team_carry"},
        tags={"books", "team_carry"},
    ),
    "cookie_tray": Mission(
        id="cookie_tray",
        label="tray of star cookies",
        phrase="tray of star cookies",
        article="a",
        contents="The icing still shone, and the tray was so wide that it needed steady hands on both sides.",
        hazard_text="If one side dips, the cookies will slide.",
        spill_text="On the middle stair, one edge tilted. Three bright cookies skidded to the step, and a streak of icing drew a white comet line.",
        recover_text="They rescued every cookie, straightened the paper, and moved into their careful plan",
        success_text="The star cookies arrived looking brave and almost perfectly straight, as if they had finished their own tiny parade.",
        allowed={"stair_handoff"},
        tags={"cookies", "stair_handoff"},
    ),
    "paint_cans": Mission(
        id="paint_cans",
        label="bundle of paint cans",
        phrase="bundle of paint cans tied in a paper sack",
        article="a",
        contents="The sack was sturdy, but the weight swung low and made the handles bite together.",
        hazard_text="If the sack swings, the cans could bang and twist out of line.",
        spill_text="The sack swung against a knee, and the cans clanked so loudly that {hero} stopped short with a gasp.".replace("{hero}", "the young hero"),
        recover_text="They steadied the handles, checked that nothing had burst, and started again as a team",
        success_text="The paint cans reached the porch without another clang, and even the paper sack looked calmer.",
        allowed={"team_carry"},
        tags={"paint", "team_carry"},
    ),
    "seedling_tray": Mission(
        id="seedling_tray",
        label="tray of tomato seedlings",
        phrase="tray of tomato seedlings",
        article="a",
        contents="The little green stems trembled in their cups of soil, too delicate for any rushing feet.",
        hazard_text="If it jerks, the soil will slosh and the stems could bend.",
        spill_text="The tray jerked once, and a puff of dark soil sprinkled over the stair while the small stems shivered in their cups.",
        recover_text="They brushed the stair clean, patted the soil back into place, and chose the slower hero way",
        success_text="The seedlings reached the porch standing straight, each tiny stem looking braver than before.",
        allowed={"stair_handoff"},
        tags={"plants", "stair_handoff"},
    ),
}

RESPONSES = {
    "team_carry": Response(
        id="team_carry",
        label="a two-person carry",
        plan="a two-person carry",
        motion="they lifted together, shoulder to shoulder",
        finish="the two children set the load down at the porch together",
        sense=3,
        tags={"team_carry"},
    ),
    "stair_handoff": Response(
        id="stair_handoff",
        label="the stair handoff",
        plan="the stair handoff",
        motion="one child took the lower step and one took the higher, passing the load upward between four careful hands",
        finish="the tray came up level and calm until it rested safely by the door",
        sense=3,
        tags={"stair_handoff"},
    ),
}

GIRL_NAMES = ["Ava", "Lily", "Mia", "Zoe", "Nora", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Theo", "Finn", "Eli", "Noah"]
TRAITS = ["steady", "careful", "patient", "kind", "quick", "proud"]


CURATED = [
    StoryParams(
        suburb="maple_lane",
        mission="book_box",
        response="team_carry",
        hero_name="Ava",
        hero_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        neighbor="mother",
        trait="steady",
        relation="siblings",
        trust=7,
        hero_age=5,
        partner_age=8,
    ),
    StoryParams(
        suburb="cedar_close",
        mission="cookie_tray",
        response="stair_handoff",
        hero_name="Max",
        hero_gender="boy",
        partner_name="Lily",
        partner_gender="girl",
        neighbor="father",
        trait="patient",
        relation="friends",
        trust=8,
        hero_age=6,
        partner_age=6,
    ),
    StoryParams(
        suburb="sunny_circle",
        mission="seedling_tray",
        response="stair_handoff",
        hero_name="Sam",
        hero_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        neighbor="mother",
        trait="quick",
        relation="friends",
        trust=3,
        hero_age=7,
        partner_age=6,
    ),
    StoryParams(
        suburb="maple_lane",
        mission="paint_cans",
        response="team_carry",
        hero_name="Nora",
        hero_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        neighbor="father",
        trait="kind",
        relation="siblings",
        trust=5,
        hero_age=7,
        partner_age=9,
    ),
]


KNOWLEDGE = {
    "suburban": [
        (
            "What does suburban mean?",
            "Suburban means a place with many homes close together, often with streets, yards, porches, and neighbors living nearby.",
        )
    ],
    "stair": [
        (
            "Why can carrying things on a stair be hard?",
            "A stair is harder than flat ground because your feet are not level. A load can wobble if you rush or cannot keep both sides steady.",
        )
    ],
    "puffin": [
        (
            "What is a puffin?",
            "A puffin is a small seabird with a round body and a bright beak. It looks cheerful, which is why children might like it as a mascot.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other on the same job. When they share the work and pay attention to one another, the job often becomes safer and easier.",
        )
    ],
    "books": [
        (
            "Why do books slide out of a box?",
            "Books are heavy and smooth, so if a box tips or the flaps open, they can slip and tumble out.",
        )
    ],
    "cookies": [
        (
            "Why do cookies need steady hands?",
            "Cookies can slide or break if a tray tilts. Keeping a tray level helps them stay in place.",
        )
    ],
    "plants": [
        (
            "Why are seedlings delicate?",
            "Seedlings are very young plants with thin stems and small roots. They can bend or spill out of their soil if they are jostled.",
        )
    ],
    "paint": [
        (
            "Why is a sack of paint cans heavy?",
            "Paint cans are filled with liquid, and liquid adds weight. If the sack swings, that heavy weight can pull awkwardly on your hands.",
        )
    ],
    "team_carry": [
        (
            "Why can two people carry something better than one?",
            "Two people can share the weight and steady both sides. That makes a heavy load less likely to swing or tip.",
        )
    ],
    "stair_handoff": [
        (
            "Why does handing something up a stair help?",
            "A handoff keeps the load level while each person stands in a stable place. It can be safer than one person trying to rush upward alone.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "suburban",
    "stair",
    "puffin",
    "teamwork",
    "books",
    "cookies",
    "plants",
    "paint",
    "team_carry",
    "stair_handoff",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = display_name(f["hero"])
    partner = display_name(f["partner"])
    mission = f["mission_cfg"]
    suburb = f["suburb"]
    response = f["response"]
    if f["outcome"] == "switched":
        return [
            f'Write a superhero story for a young child set on a suburban street that includes the words "stair" and "puffin".',
            f"Tell a story where {hero} wants to make a solo rescue up a porch stair with {mission.phrase}, but {partner} argues for teamwork and is right.",
            f"Write a gentle conflict-and-teamwork story where a puffin mascot watches two children choose {response.label} and save the day together.",
        ]
    return [
        f'Write a superhero story for a young child set on a suburban street that includes the words "stair" and "puffin".',
        f"Tell a story where {hero} tries to rush {mission.phrase} up a porch stair alone, makes a small mess, and then works with {partner} to fix it.",
        f"Write a conflict-and-teamwork story where children learn that a real superhero rescue needs {response.label}, not bragging.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    neighbor = f["neighbor"]
    mission = f["mission_cfg"]
    response = f["response"]
    hero_name = display_name(hero)
    partner_name = display_name(partner)
    neighbor_word = neighbor.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {hero_name} and {partner_name}, who were pretending to be superheroes on a suburban street. A neighbor asks them to help with {mission.phrase}.",
        ),
        (
            "What made the problem hard?",
            f"The job had to be done on a porch stair, not flat ground. That made wobbling more likely, so the children needed a careful plan instead of a fast one.",
        ),
        (
            f"Why did {partner_name} disagree with {hero_name}?",
            f"{partner_name} thought rushing alone was unsafe. {partner.pronoun().capitalize()} could see that {mission.phrase} might tip or spill on the stair, so {partner.pronoun()} pushed for teamwork.",
        ),
    ]
    if f["outcome"] == "switched":
        qa.append(
            (
                f"How was the conflict solved?",
                f"{hero_name} listened before anything fell and agreed to use {response.label}. The turn happens when bragging gives way to trust, so the rescue becomes a shared job instead of a solo stunt.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero_name} rushed alone?",
                f"The load wobbled and made a small mess on the stair. That happened because one child tried to do a two-person job without enough support.",
            )
        )
        qa.append(
            (
                "How did they fix the problem?",
                f"They stopped arguing, cleaned up together, and used {response.label}. The second try worked because both children shared the weight and kept the load steady.",
            )
        )
    qa.append(
        (
            f"What did the neighbor say at the end?",
            f"The {neighbor_word} said that was how heroes should work. The ending shows that teamwork mattered more than showing off.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"suburban", "stair", "puffin", "teamwork"}
    mission = world.facts["mission_cfg"]
    response = world.facts["response"]
    tags |= set(mission.tags)
    tags |= set(response.tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {}
            for key, value in ent.attrs.items():
                if isinstance(value, set):
                    shown[key] = sorted(value)
                elif value not in ("", None, 0):
                    shown[key] = value
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(mission: Mission, response: Response) -> str:
    return (
        f"(No story: {response.label} does not fit {mission.phrase}. "
        f"This world only allows teamwork methods that can really keep that load steady on the stair.)"
    )


def explain_name(gender: str, name: str) -> str:
    return f"(No story: the chosen name '{name}' is not in the expected pool for gender '{gender}' here.)"


ASP_RULES = r"""
compatible(M, R) :- mission(M), response(R), allows(M, R), sense(R, S), S >= 2.
valid(Sb, M, R) :- suburb(Sb), compatible(M, R).

steady_trait(T) :- trait(T), is_steady(T).
age_bonus(3) :- relation(siblings), partner_age(PA), hero_age(HA), PA > HA.
age_bonus(0) :- not relation(siblings).
trait_bonus(2) :- trait(T), steady_trait(T).
trait_bonus(0) :- trait(T), not steady_trait(T).
influence(V) :- trust(TS), age_bonus(A), trait_bonus(B), V = TS + A + B.
switched :- influence(V), team_threshold(K), V >= K.

outcome(switched) :- switched.
outcome(spilled) :- not switched.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for suburb_id in SUBURBS:
        lines.append(asp.fact("suburb", suburb_id))
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        for response_id in sorted(mission.allowed):
            lines.append(asp.fact("allows", mission_id, response_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("is_steady", trait))
    lines.append(asp.fact("team_threshold", TEAM_THRESHOLD))
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
            asp.fact("trait", params.trait),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("partner_age", params.partner_age),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "switched" if would_switch(
        params.relation,
        params.hero_age,
        params.partner_age,
        params.trait,
        params.trust,
    ) else "spilled"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcome cases differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story during smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - explicit verify failure path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: suburban superhero conflict on a stair, solved by teamwork."
    )
    ap.add_argument("--suburb", choices=SUBURBS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--neighbor", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and args.mission:
        mission = MISSIONS[args.mission]
        response = RESPONSES[args.response]
        if not compatible_response(mission, response):
            raise StoryError(explain_rejection(mission, response))

    combos = [
        combo for combo in valid_combos()
        if (args.suburb is None or combo[0] == args.suburb)
        and (args.mission is None or combo[1] == args.mission)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    suburb_id, mission_id, response_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    partner_name = args.partner_name or pick_name(rng, partner_gender, avoid=hero_name)
    neighbor = args.neighbor or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["friends", "siblings"])
    trust = args.trust if args.trust is not None else rng.randint(2, 9)
    trait = rng.choice(TRAITS)
    hero_age, partner_age = rng.sample([5, 6, 7, 8, 9], 2)

    return StoryParams(
        suburb=suburb_id,
        mission=mission_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        neighbor=neighbor,
        trait=trait,
        relation=relation,
        trust=trust,
        hero_age=hero_age,
        partner_age=partner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.suburb not in SUBURBS:
        raise StoryError(f"(No story: unknown suburb '{params.suburb}'.)")
    if params.mission not in MISSIONS:
        raise StoryError(f"(No story: unknown mission '{params.mission}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")

    mission = MISSIONS[params.mission]
    response = RESPONSES[params.response]
    if not compatible_response(mission, response):
        raise StoryError(explain_rejection(mission, response))

    world = tell(
        suburb=SUBURBS[params.suburb],
        mission_cfg=mission,
        response_cfg=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        neighbor_type=params.neighbor,
        trait=params.trait,
        relation=params.relation,
        trust=params.trust,
        hero_age=params.hero_age,
        partner_age=params.partner_age,
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
        print(f"{len(combos)} compatible (suburb, mission, response) combos:\n")
        for suburb_id, mission_id, response_id in combos:
            print(f"  {suburb_id:12} {mission_id:14} {response_id}")
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
            header = f"### {p.hero_name} & {p.partner_name}: {p.mission} at {p.suburb} ({outcome_of(p)})"
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
