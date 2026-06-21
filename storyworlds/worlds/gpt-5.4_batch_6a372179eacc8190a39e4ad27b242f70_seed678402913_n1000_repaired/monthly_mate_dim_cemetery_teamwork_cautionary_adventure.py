#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/monthly_mate_dim_cemetery_teamwork_cautionary_adventure.py
=====================================================================================

A standalone story world about two children on a monthly cemetery adventure walk.
A gust of wind carries an important item into a risky corner of the cemetery.
One child is tempted to hurry in alone, but the pair's safety rule -- "mate-dim"
for places too dim for one mate to enter alone -- turns the adventure toward
teamwork, caution, and a safer ending.

The world varies over:
- a monthly mission
- the risky cemetery spot where the item lands
- the sensible teamwork method used to recover it

The reasonableness gate is simple and strict:
- each hazard has exactly one sensible recovery method
- an explicit mismatched or low-sense method is rejected
- the outcome varies between a near-miss ("averted") and a brief trouble beat
  ("guided"), depending on whether the buddy successfully stops the dash

Run it
------
python storyworlds/worlds/gpt-5.4/monthly_mate_dim_cemetery_teamwork_cautionary_adventure.py
python storyworlds/worlds/gpt-5.4/monthly_mate_dim_cemetery_teamwork_cautionary_adventure.py --hazard shadow_steps
python storyworlds/worlds/gpt-5.4/monthly_mate_dim_cemetery_teamwork_cautionary_adventure.py --method hop_fence
python storyworlds/worlds/gpt-5.4/monthly_mate_dim_cemetery_teamwork_cautionary_adventure.py --all
python storyworlds/worlds/gpt-5.4/monthly_mate_dim_cemetery_teamwork_cautionary_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/monthly_mate_dim_cemetery_teamwork_cautionary_adventure.py --verify
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
SENSE_MIN = 2
IMPULSE_INIT = 5.0
STEADY_TRAITS = {"careful", "steady", "thoughtful", "calm", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
    age: int = 0
    traits: list[str] = field(default_factory=list)
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
class Mission:
    id: str
    opening: str
    task: str
    item_label: str
    item_phrase: str
    loss_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    place_text: str
    dark_text: str
    warning_text: str
    trouble_text: str
    resolution_need: str
    method_id: str
    risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    works_on: set[str] = field(default_factory=set)
    arrival_text: str = ""
    action_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    mission: str
    hazard: str
    method: str
    scout_name: str
    scout_gender: str
    buddy_name: str
    buddy_gender: str
    keeper_type: str
    buddy_trait: str
    relation: str = "friends"
    scout_age: int = 6
    buddy_age: int = 7
    trust: int = 6
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


def _r_alone_in_risk(world: World) -> list[str]:
    scout = world.entities.get("scout")
    spot = world.entities.get("spot")
    if scout is None or spot is None:
        return []
    if scout.meters["in_risk"] < THRESHOLD:
        return []
    sig = ("alone_in_risk", spot.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    scout.memes["fear"] += 1
    spot.meters["danger"] += float(world.facts.get("hazard_cfg").risk)
    return []


def _r_alarm_calls_help(world: World) -> list[str]:
    buddy = world.entities.get("buddy")
    keeper = world.entities.get("keeper")
    if buddy is None or keeper is None:
        return []
    if buddy.memes["alarm"] < THRESHOLD:
        return []
    sig = ("alarm_calls_help", keeper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keeper.memes["urgency"] += 1
    return []


RULES = [
    Rule(name="alone_in_risk", apply=_r_alone_in_risk),
    Rule(name="alarm_calls_help", apply=_r_alarm_calls_help),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


MISSIONS = {
    "flowers": Mission(
        id="flowers",
        opening="a monthly lantern walk through the quiet cemetery garden",
        task="leave fresh flowers at Grandmother May's stone and read the names softly together",
        item_label="flower list",
        item_phrase="their folded flower list",
        loss_text="A cheeky wind tugged the folded flower list from their hands and sent it skipping away.",
        ending_image="they laid the flowers down neatly, and the list rested under a smooth pebble while their lantern made a warm gold circle",
        tags={"flowers", "monthly"},
    ),
    "map": Mission(
        id="map",
        opening="their monthly adventure map walk beside the old cemetery",
        task="copy the shape of the angel stones into a paper map for their club",
        item_label="map",
        item_phrase="their paper map",
        loss_text="A wind swirled through the gate and lifted the paper map like a pale bird.",
        ending_image="they tucked the map back into its satchel and marched on between the stones like careful explorers",
        tags={"map", "monthly"},
    ),
    "ribbon": Mission(
        id="ribbon",
        opening="the monthly kindness round at the cemetery",
        task="tie a blue memory ribbon on the little bench by the willow tree",
        item_label="ribbon",
        item_phrase="their blue ribbon",
        loss_text="The ribbon slipped free, fluttered once, and sailed beyond the path.",
        ending_image="the blue ribbon fluttered safely on the bench, and the children stood shoulder to shoulder smiling at their finished work",
        tags={"ribbon", "monthly"},
    ),
}

HAZARDS = {
    "thorn_patch": Hazard(
        id="thorn_patch",
        label="thorn patch",
        place_text="into a thorn patch just inside the old iron fence",
        dark_text="The place looked narrow and shadowy, with twisty stems hiding the ground.",
        warning_text="Thorns can grab sleeves and knees before you know it.",
        trouble_text="The thorns caught at the child's sleeve, and the brave hurry suddenly felt much less brave.",
        resolution_need="something long enough to reach in without anybody squeezing between the thorns",
        method_id="reacher",
        risk=2,
        tags={"thorn", "cemetery"},
    ),
    "muddy_hollow": Hazard(
        id="muddy_hollow",
        label="muddy hollow",
        place_text="down in a muddy hollow beside the leaning stones",
        dark_text="The hollow looked shiny and soft, and the earth there could gulp at shoes.",
        warning_text="Soft mud can trap a foot and make a fast trip turn wobbly.",
        trouble_text="One shoe sank with a squish, and the child flung out both arms to keep from tumbling.",
        resolution_need="a steady way across the mud so nobody has to hop and guess",
        method_id="board_path",
        risk=2,
        tags={"mud", "cemetery"},
    ),
    "shadow_steps": Hazard(
        id="shadow_steps",
        label="shadow steps",
        place_text="onto the shadow steps of the old locked crypt",
        dark_text="The steps were dim and uneven, with black corners where feet could miss.",
        warning_text="Dim steps are not for guessing games.",
        trouble_text="A loose pebble rolled, and the child froze halfway up, all at once aware of how dark the steps were.",
        resolution_need="a bright light and a grown-up on the proper path",
        method_id="lantern_path",
        risk=3,
        tags={"steps", "cemetery", "dark"},
    ),
}

METHODS = {
    "reacher": Method(
        id="reacher",
        label="long grabber",
        sense=3,
        works_on={"thorn_patch"},
        arrival_text="came back with the long litter grabber from the shed",
        action_text="stood on the path while the children held the lantern steady, then pinched the lost thing gently from the thorns without anyone crawling in",
        qa_text="used the long grabber from the path while the children held the light steady",
        tags={"tool", "teamwork"},
    ),
    "board_path": Method(
        id="board_path",
        label="garden board",
        sense=3,
        works_on={"muddy_hollow"},
        arrival_text="fetched a flat garden board and set it over the mud",
        action_text="held one child's hand while the other child held the lantern, and together they crossed the safe little bridge and picked up the lost thing",
        qa_text="made a safe little bridge with a garden board and crossed together",
        tags={"bridge", "teamwork"},
    ),
    "lantern_path": Method(
        id="lantern_path",
        label="lantern path",
        sense=3,
        works_on={"shadow_steps"},
        arrival_text="unhooked the bright path lantern and opened the proper gate",
        action_text="led them the long way round on the real path, with the children holding each other's sleeves, until the lost thing was in reach",
        qa_text="used the proper path with a bright lantern and kept the children together",
        tags={"lantern", "teamwork", "dark"},
    ),
    "hop_fence": Method(
        id="hop_fence",
        label="hop the fence",
        sense=1,
        works_on=set(),
        arrival_text="",
        action_text="",
        qa_text="",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "steady", "thoughtful", "calm", "sensible", "curious"]


def initial_steady(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def select_method(hazard_id: str) -> Optional[Method]:
    hazard = HAZARDS.get(hazard_id)
    if hazard is None:
        return None
    method = METHODS.get(hazard.method_id)
    if method is None:
        return None
    if hazard_id not in method.works_on or method.sense < SENSE_MIN:
        return None
    return method


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for hazard_id in HAZARDS:
            method = select_method(hazard_id)
            if method is not None:
                combos.append((mission_id, hazard_id, method.id))
    return combos


def would_avert(relation: str, scout_age: int, buddy_age: int, buddy_trait: str, trust: int) -> bool:
    older = relation == "siblings" and buddy_age > scout_age
    authority = initial_steady(buddy_trait) + (2.0 if older else 0.0) + (1.0 if trust >= 6 else 0.0)
    return authority > IMPULSE_INIT


def predict_risk(world: World) -> dict:
    sim = world.copy()
    scout = sim.get("scout")
    scout.meters["in_risk"] += 1
    propagate(sim)
    spot = sim.get("spot")
    return {
        "fear": scout.memes["fear"],
        "danger": spot.meters["danger"],
    }


def club_setup(world: World, scout: Entity, buddy: Entity, keeper: Entity, mission: Mission) -> None:
    scout.memes["wonder"] += 1
    buddy.memes["wonder"] += 1
    world.say(
        f"Once every month, {scout.id}, {buddy.id}, and {keeper.label_word} Rowan took {mission.opening}."
    )
    world.say(
        f"That afternoon they had come to {mission.task}."
    )
    world.say(
        'The children had even made a club safety word for places too dim for one mate alone: "mate-dim."'
    )


def lose_item(world: World, scout: Entity, buddy: Entity, mission: Mission, hazard: Hazard) -> None:
    world.say(mission.loss_text)
    world.say(
        f"It skittered {hazard.place_text}. {hazard.dark_text}"
    )
    scout.memes["desire"] += 1
    world.say(
        f'"I can get the {mission.item_label} fast," {scout.id} said, already leaning forward.'
    )


def warn(world: World, buddy: Entity, scout: Entity, keeper: Entity, hazard: Hazard) -> None:
    pred = predict_risk(world)
    buddy.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{buddy.id} caught {scout.id}\'s sleeve. "Wait. That is mate-dim," {buddy.pronoun()} said. '
        f'"{hazard.warning_text} Let\'s get {keeper.label_word} Rowan and do it together."'
    )


def back_down(world: World, scout: Entity, buddy: Entity) -> None:
    scout.memes["relief"] += 1
    buddy.memes["relief"] += 1
    scout.memes["impulse"] = 0.0
    world.say(
        f"{scout.id} took one breath, looked again at the dark corner, and stepped back onto the path."
    )
    world.say(
        f'"You\'re right," {scout.pronoun()} said. "Mate-dim means no racing ahead."'
    )


def dash_in(world: World, scout: Entity, hazard: Hazard) -> None:
    scout.memes["impulse"] += 1
    scout.meters["in_risk"] += 1
    propagate(world)
    world.say(
        f"But adventure tugged hard. {scout.id} slipped off the path and hurried toward the {hazard.label}."
    )
    world.say(hazard.trouble_text)


def call_help(world: World, buddy: Entity, keeper: Entity) -> None:
    buddy.memes["alarm"] += 1
    propagate(world)
    world.say(
        f'"Rowan!" {buddy.id} called. "{buddy.pronoun("subject").capitalize()} needs help on the path!"'
    )
    world.say(
        f"{keeper.label_word.capitalize()} Rowan was already coming, boots quick and eyes calm."
    )


def teamwork_recover(world: World, scout: Entity, buddy: Entity, keeper: Entity, mission: Mission,
                     hazard: Hazard, method: Method) -> None:
    item = world.get("item")
    keeper.memes["care"] += 1
    scout.memes["trust"] += 1
    buddy.memes["trust"] += 1
    item.meters["found"] += 1
    scout.meters["in_risk"] = 0.0
    world.say(
        f'{keeper.label_word.capitalize()} Rowan {method.arrival_text}. "Adventures stay brave when the team stays together," {keeper.pronoun()} said.'
    )
    world.say(
        f"Then {keeper.pronoun()} {method.action_text}."
    )
    world.say(
        f"Soon the {mission.item_label} was safe again, and all three of them were back where the path was wide and sure."
    )


def lesson(world: World, scout: Entity, buddy: Entity, keeper: Entity, mission: Mission, outcome: str) -> None:
    scout.memes["lesson"] += 1
    buddy.memes["lesson"] += 1
    if outcome == "averted":
        opener = "Nothing bad had happened, and that was exactly the point."
    else:
        opener = "The scare was small, but it felt big enough to remember."
    world.say(opener)
    world.say(
        f'{keeper.label_word.capitalize()} Rowan knelt beside them. "A cemetery can be quiet and beautiful," {keeper.pronoun()} said, '
        f'"but quiet places still need careful feet. When a corner turns mate-dim, call the team."'
    )
    world.say(
        f"{scout.id} nodded, {buddy.id} nodded too, and this time they said the club word together with a smile."
    )
    world.say(
        f"Before they went home, {mission.ending_image}."
    )


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def tell(mission: Mission, hazard: Hazard, method: Method,
         scout_name: str, scout_gender: str, buddy_name: str, buddy_gender: str,
         keeper_type: str, buddy_trait: str, relation: str, scout_age: int,
         buddy_age: int, trust: int) -> World:
    world = World()
    scout = world.add(Entity(
        id="scout",
        kind="character",
        type=scout_gender,
        label=scout_name,
        role="scout",
        age=scout_age,
        traits=["bold"],
        attrs={"display": scout_name, "relation": relation},
    ))
    buddy = world.add(Entity(
        id="buddy",
        kind="character",
        type=buddy_gender,
        label=buddy_name,
        role="buddy",
        age=buddy_age,
        traits=[buddy_trait],
        attrs={"display": buddy_name, "relation": relation},
    ))
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type=keeper_type,
        label="the groundskeeper",
        role="keeper",
        attrs={"display": "Rowan"},
    ))
    item = world.add(Entity(
        id="item",
        type="item",
        label=mission.item_label,
        phrase=mission.item_phrase,
    ))
    spot = world.add(Entity(
        id="spot",
        type="spot",
        label=hazard.label,
        tags=set(hazard.tags),
    ))

    scout.attrs["display"] = scout_name
    buddy.attrs["display"] = buddy_name
    scout.memes["impulse"] = IMPULSE_INIT
    buddy.memes["steady"] = initial_steady(buddy_trait)
    buddy.memes["trust"] = float(trust)

    club_setup(world, scout, buddy, keeper, mission)

    world.para()
    lose_item(world, scout, buddy, mission, hazard)
    warn(world, buddy, scout, keeper, hazard)

    averted = would_avert(relation, scout_age, buddy_age, buddy_trait, trust)

    world.para()
    if averted:
        back_down(world, scout, buddy)
    else:
        dash_in(world, scout, hazard)
        call_help(world, buddy, keeper)

    world.para()
    teamwork_recover(world, scout, buddy, keeper, mission, hazard, method)

    world.para()
    outcome = "averted" if averted else "guided"
    lesson(world, scout, buddy, keeper, mission, outcome)

    world.facts.update(
        mission=mission,
        hazard_cfg=hazard,
        method=method,
        scout=scout,
        buddy=buddy,
        keeper=keeper,
        item=item,
        relation=relation,
        outcome=outcome,
        averted=averted,
        trouble=(not averted),
        recovered=item.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "monthly": [
        (
            "What does monthly mean?",
            "Monthly means something happens once each month. If a walk is monthly, the people do it every month."
        )
    ],
    "cemetery": [
        (
            "What is a cemetery?",
            "A cemetery is a quiet place where people remember loved ones who have died. People usually walk gently there and speak softly."
        )
    ],
    "mate-dim": [
        (
            "What could the made-up safety word mate-dim mean in this story?",
            "It means a place is too dim for one friend to enter alone. The word reminds the team to stop, stay together, and ask for help."
        )
    ],
    "thorn": [
        (
            "Why can thorny plants be tricky?",
            "Thorns are sharp little points on some plants. They can catch clothes or scratch skin if you push in too fast."
        )
    ],
    "mud": [
        (
            "Why is deep mud hard to walk in?",
            "Soft mud can grab at your shoes and make your feet slip. That is why people move slowly or find a safer path."
        )
    ],
    "steps": [
        (
            "Why are dark steps risky?",
            "Dark steps are hard to see clearly, so a foot can miss an edge. Bright light and slow walking make steps safer."
        )
    ],
    "lantern": [
        (
            "What does a lantern help with?",
            "A lantern helps people see where they are going in dim places. Good light makes it easier to notice steps, stones, and paths."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help one another do a job together. A team can be safer and smarter than one person rushing alone."
        )
    ],
}
KNOWLEDGE_ORDER = ["monthly", "cemetery", "mate-dim", "thorn", "mud", "steps", "lantern", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scout = f["scout"]
    buddy = f["buddy"]
    mission = f["mission"]
    hazard = f["hazard_cfg"]
    outcome = f["outcome"]
    display_scout = scout.attrs["display"]
    display_buddy = buddy.attrs["display"]
    if outcome == "averted":
        return [
            'Write a short adventure story for a 3-to-5-year-old that includes the words "monthly", "mate-dim", and "cemetery". Make it cautionary but gentle, and end with teamwork.',
            f"Tell a cemetery adventure where {display_scout} wants to hurry after a lost {mission.item_label}, but {display_buddy} uses the safety word mate-dim and stops the dash before anything worse happens.",
            f"Write a child-facing story about a monthly walk, a dim risky corner, and a team choosing help instead of rushing alone near a {hazard.label}.",
        ]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "monthly", "mate-dim", and "cemetery". Make it cautionary but end safely through teamwork.',
        f"Tell a cemetery adventure where {display_scout} slips off the path toward a {hazard.label}, then a calm helper and a brave buddy solve the problem together.",
        f"Write a gentle cautionary story about a monthly mission, a child who nearly gets into trouble in a mate-dim place, and a team that brings everyone back safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scout = f["scout"]
    buddy = f["buddy"]
    keeper = f["keeper"]
    mission = f["mission"]
    hazard = f["hazard_cfg"]
    method = f["method"]
    display_scout = scout.attrs["display"]
    display_buddy = buddy.attrs["display"]
    pair = pair_noun(scout, buddy, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {display_scout} and {display_buddy}, on a monthly walk with groundskeeper Rowan. They were trying to finish {mission.task}."
        ),
        (
            "What was lost?",
            f"They lost the {mission.item_label} when the wind snatched it away. That is what pulled the adventure toward the risky part of the cemetery."
        ),
        (
            "What did mate-dim mean to the children?",
            "Mate-dim was their club word for a place too dim for one child to enter alone. It reminded them that a brave team should stop and think before rushing."
        ),
        (
            f"Why was the {hazard.label} a problem?",
            f"It was dangerous because {hazard.warning_text.lower()} {hazard.dark_text} That made speed a bad idea."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {display_scout} do after {display_buddy} gave the warning?",
                f"{display_scout} stopped on the path and listened. That choice kept the trouble from getting bigger before Rowan came to help."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {display_scout} hurried in alone?",
                f"{hazard.trouble_text} {display_scout} felt the danger more clearly once the path was behind {scout.pronoun('object')}."
            )
        )
    qa.append(
        (
            "How did the team get the lost thing back?",
            f"Rowan {method.qa_text}. The children helped too, so the recovery worked because the whole team stayed together."
        )
    )
    qa.append(
        (
            "What did the story teach?",
            "It taught that adventures can still be exciting without being reckless. When a place turns mate-dim, the safest brave choice is to call the team and use the proper help."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"monthly", "cemetery", "mate-dim", "teamwork"}
    hazard = world.facts["hazard_cfg"]
    method = world.facts["method"]
    if "thorn" in hazard.tags:
        tags.add("thorn")
    if "mud" in hazard.tags:
        tags.add("mud")
    if "steps" in hazard.tags or "dark" in hazard.tags:
        tags.add("steps")
    if "lantern" in method.tags or "dark" in method.tags:
        tags.add("lantern")
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
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {eid:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="flowers",
        hazard="thorn_patch",
        method="reacher",
        scout_name="Tom",
        scout_gender="boy",
        buddy_name="Lily",
        buddy_gender="girl",
        keeper_type="mother",
        buddy_trait="careful",
        relation="friends",
        scout_age=6,
        buddy_age=7,
        trust=7,
    ),
    StoryParams(
        mission="map",
        hazard="muddy_hollow",
        method="board_path",
        scout_name="Mia",
        scout_gender="girl",
        buddy_name="Ben",
        buddy_gender="boy",
        keeper_type="father",
        buddy_trait="curious",
        relation="siblings",
        scout_age=7,
        buddy_age=6,
        trust=4,
    ),
    StoryParams(
        mission="ribbon",
        hazard="shadow_steps",
        method="lantern_path",
        scout_name="Leo",
        scout_gender="boy",
        buddy_name="Nora",
        buddy_gender="girl",
        keeper_type="mother",
        buddy_trait="steady",
        relation="siblings",
        scout_age=5,
        buddy_age=7,
        trust=8,
    ),
]


def explain_method_rejection(method_id: str, hazard_id: Optional[str] = None) -> str:
    method = METHODS[method_id]
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method_id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). A cemetery adventure should choose a safer teamwork method.)"
        )
    if hazard_id is not None:
        hazard = HAZARDS[hazard_id]
        right = select_method(hazard_id)
        right_id = right.id if right is not None else "none"
        return (
            f"(Refusing method '{method_id}' for hazard '{hazard_id}': the sensible recovery for "
            f"{hazard.label} is '{right_id}', because the team needs {hazard.resolution_need}.)"
        )
    return "(Refusing method: it does not fit this story.)"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(
        params.relation, params.scout_age, params.buddy_age, params.buddy_trait, params.trust
    ) else "guided"


ASP_RULES = r"""
% --- method fit ------------------------------------------------------------
select_method(H, M) :- hazard(H), method(M), best_for(H, M), sense(M, S), sense_min(Min), S >= Min.
valid(Mission, H, M) :- mission(Mission), hazard(H), select_method(H, M).

% --- outcome model ---------------------------------------------------------
steady_now(T) :- trait(T), steady_trait(T).
steady_base(5) :- trait(T), steady_now(T).
steady_base(3) :- trait(T), not steady_now(T).
older_bonus(2) :- relation(siblings), scout_age(SA), buddy_age(BA), BA > SA.
older_bonus(0) :- not relation(siblings).
trust_bonus(1) :- trust(T), T >= 6.
trust_bonus(0) :- trust(T), T < 6.
authority(B + O + T) :- steady_base(B), older_bonus(O), trust_bonus(T).
averted :- authority(A), impulse_init(I), A > I.
outcome(averted) :- averted.
outcome(guided) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("best_for", hazard_id, hazard.method_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("steady_trait", trait))
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
            asp.fact("trait", params.buddy_trait),
            asp.fact("relation", params.relation),
            asp.fact("scout_age", params.scout_age),
            asp.fact("buddy_age", params.buddy_age),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = []
    for params in cases:
        a = asp_outcome(params)
        b = outcome_of(params)
        if a != b:
            bad.append((params, a, b))
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")
        for params, a, b in bad[:5]:
            print(f"  {params} asp={a} python={b}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a monthly cemetery adventure, a mate-dim warning, and teamwork."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--keeper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and select_method(args.hazard) is None:
        raise StoryError("(No sensible recovery exists for that hazard.)")
    if args.method:
        if METHODS[args.method].sense < SENSE_MIN:
            raise StoryError(explain_method_rejection(args.method))
        if args.hazard:
            expected = select_method(args.hazard)
            if expected is None or expected.id != args.method:
                raise StoryError(explain_method_rejection(args.method, args.hazard))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, hazard_id, method_id = rng.choice(sorted(combos))
    scout_name, scout_gender = _pick_name(rng)
    buddy_name, buddy_gender = _pick_name(rng, avoid=scout_name)
    relation = rng.choice(["friends", "siblings"])
    scout_age, buddy_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(2, 9)
    buddy_trait = rng.choice(TRAITS)
    keeper_type = args.keeper or rng.choice(["mother", "father"])

    return StoryParams(
        mission=mission_id,
        hazard=hazard_id,
        method=method_id,
        scout_name=scout_name,
        scout_gender=scout_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        keeper_type=keeper_type,
        buddy_trait=buddy_trait,
        relation=relation,
        scout_age=scout_age,
        buddy_age=buddy_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    expected = select_method(params.hazard)
    if expected is None or expected.id != params.method:
        raise StoryError(explain_method_rejection(params.method, params.hazard))

    world = tell(
        mission=MISSIONS[params.mission],
        hazard=HAZARDS[params.hazard],
        method=METHODS[params.method],
        scout_name=params.scout_name,
        scout_gender=params.scout_gender,
        buddy_name=params.buddy_name,
        buddy_gender=params.buddy_gender,
        keeper_type=params.keeper_type,
        buddy_trait=params.buddy_trait,
        relation=params.relation,
        scout_age=params.scout_age,
        buddy_age=params.buddy_age,
        trust=params.trust,
    )

    story = world.render()
    display_map = {
        "scout": params.scout_name,
        "buddy": params.buddy_name,
    }
    for internal, external in display_map.items():
        story = story.replace(internal, external)

    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (mission, hazard, method) combos:\n")
        for mission_id, hazard_id, method_id in combos:
            print(f"  {mission_id:8} {hazard_id:13} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.scout_name} & {p.buddy_name}: {p.mission} / {p.hazard} / {outcome_of(p)}"
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
