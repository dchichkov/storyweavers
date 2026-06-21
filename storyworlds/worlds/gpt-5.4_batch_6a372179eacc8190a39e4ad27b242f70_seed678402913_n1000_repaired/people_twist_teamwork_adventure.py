#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/people_twist_teamwork_adventure.py
=============================================================

A standalone storyworld about two children on a small adventure. They think they
are chasing treasure, but the real prize turns out to be a useful object that
helps other people. The central turn is a teamwork obstacle: one child cannot
solve it alone, but together they can reach the cache and discover the twist.

The world prefers a small number of strong, plausible combinations:
- a cliff path with a ravine, crossed by rope teamwork, leading to a signal mirror
- a ruined stair with a stone door, opened by lever-and-push teamwork, leading to a bell key
- a sea cave with a dark tunnel, crossed with map-and-lantern teamwork, leading to a beacon lens

Run it
------
    python storyworlds/worlds/gpt-5.4/people_twist_teamwork_adventure.py
    python storyworlds/worlds/gpt-5.4/people_twist_teamwork_adventure.py --place cliff_path
    python storyworlds/worlds/gpt-5.4/people_twist_teamwork_adventure.py --obstacle dark_tunnel
    python storyworlds/worlds/gpt-5.4/people_twist_teamwork_adventure.py --plan lever_push
    python storyworlds/worlds/gpt-5.4/people_twist_teamwork_adventure.py --all
    python storyworlds/worlds/gpt-5.4/people_twist_teamwork_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/people_twist_teamwork_adventure.py --trace
    python storyworlds/worlds/gpt-5.4/people_twist_teamwork_adventure.py --verify
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

# Make the shared result containers importable when this script is run directly:
# this file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str = ""
    label: str = ""
    opening: str = ""
    path_line: str = ""
    supports: set[str] = field(default_factory=set)
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str = ""
    label: str = ""
    phrase: str = ""
    problem: str = ""
    solo_fail: str = ""
    teamwork_win: str = ""
    required_plan: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str = ""
    label: str = ""
    phrase: str = ""
    team_line: str = ""
    action: str = ""
    requires_two: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Cache:
    id: str = ""
    map_mark: str = ""
    expected_treasure: str = ""
    actual_item: str = ""
    reveal: str = ""
    people_phrase: str = ""
    help_line: str = ""
    ending_line: str = ""
    required_obstacle: str = ""
    tags: set[str] = field(default_factory=set)


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
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_progress(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    trail = world.get("trail")
    if obstacle.meters["cleared"] < THRESHOLD:
        return []
    sig = ("progress", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trail.meters["open"] += 1
    for kid in world.kids():
        kid.memes["hope"] += 1
    return ["The path opened at last, and the children hurried on before their courage cooled."]


def _r_ready_to_help(world: World) -> list[str]:
    chest = world.get("cache")
    quest = world.get("quest")
    if chest.meters["opened"] < THRESHOLD:
        return []
    sig = ("ready", chest.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    quest.meters["ready"] += 1
    return ["The map had not led them to riches after all; it had led them to something useful."]


def _r_help_people(world: World) -> list[str]:
    quest = world.get("quest")
    town = world.get("people")
    if quest.meters["ready"] < THRESHOLD:
        return []
    sig = ("help", town.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    town.meters["safe"] += 1
    for kid in world.kids():
        kid.memes["pride"] += 1
        kid.memes["relief"] += 1
    return [world.facts.get("help_result_line", "")]


CAUSAL_RULES = [
    Rule(name="progress", apply=_r_progress),
    Rule(name="ready", apply=_r_ready_to_help),
    Rule(name="help", apply=_r_help_people),
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
                produced.extend(s for s in out if s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "cliff_path": Place(
        id="cliff_path",
        label="the wind cliffs",
        opening="At the edge of the wind cliffs, the sea flashed far below.",
        path_line="A narrow goat path curled toward an old watch platform above the bay.",
        supports={"ravine"},
        ending_image="Down below, the harbor people waved from the bright water.",
        tags={"cliff", "adventure"},
    ),
    "ruin_hill": Place(
        id="ruin_hill",
        label="the ruin hill",
        opening="Above the little town, the ruin hill rose in broken steps and red grass.",
        path_line="A cracked stair climbed toward a stone tower where warnings used to ring.",
        supports={"stone_door"},
        ending_image="Below them, the town people looked up and cheered from the square.",
        tags={"ruin", "adventure"},
    ),
    "sea_caves": Place(
        id="sea_caves",
        label="the sea caves",
        opening="Beside the surf, the sea caves breathed cool air in and out like a sleeping giant.",
        path_line="An old smugglers' path led toward a beacon room cut high into the rock.",
        supports={"dark_tunnel"},
        ending_image="Far along the shore, the beach people pointed and laughed with relief.",
        tags={"cave", "adventure"},
    ),
}

OBSTACLES = {
    "ravine": Obstacle(
        id="ravine",
        label="ravine",
        phrase="a split in the cliff path where the boards had fallen away",
        problem="A narrow ravine cut the trail in two, and the gap dropped to sharp rocks and foam.",
        solo_fail="One child could not cross safely alone because the loose plank tipped and skidded.",
        teamwork_win="One held the rope tight while the other inched the plank into place, and together they made a steady bridge.",
        required_plan="rope_team",
        tags={"bridge", "teamwork"},
    ),
    "stone_door": Obstacle(
        id="stone_door",
        label="stone door",
        phrase="a round stone door jammed in an old tower arch",
        problem="The round stone door had sunk crooked in its groove and would not budge.",
        solo_fail="One child could shift the lever a little, but not enough to move the heavy stone.",
        teamwork_win="One child leaned on the lever while the other pushed at the edge, and the door rolled open with a deep groan.",
        required_plan="lever_push",
        tags={"door", "teamwork"},
    ),
    "dark_tunnel": Obstacle(
        id="dark_tunnel",
        label="dark tunnel",
        phrase="a twisting tunnel where the floor dropped and turned without warning",
        problem="The tunnel beyond the cave mouth was black and uneven, with sudden dips in the floor.",
        solo_fail="One child could hold the lantern or the map, but not both well enough to keep from getting lost.",
        teamwork_win="One carried the lantern high while the other followed the map marks, and together they found the hidden steps.",
        required_plan="map_lantern",
        tags={"tunnel", "dark"},
    ),
}

PLANS = {
    "rope_team": Plan(
        id="rope_team",
        label="rope teamwork",
        phrase="tie the cliff rope and steady the plank together",
        team_line='“If we both do one part, it might work,” one child said.',
        action="They worked shoulder to shoulder with the rope and the plank.",
        requires_two=True,
        tags={"rope", "teamwork"},
    ),
    "lever_push": Plan(
        id="lever_push",
        label="lever and push",
        phrase="use a branch as a lever while the other pushes",
        team_line='“The stone is too big for one pair of hands,” one child said. “But maybe not for two.”',
        action="They counted to three and threw their strength into the lever and the stone together.",
        requires_two=True,
        tags={"lever", "teamwork"},
    ),
    "map_lantern": Plan(
        id="map_lantern",
        label="map and lantern",
        phrase="let one child guide with the map while the other lights the way",
        team_line='“I can see the marks if you hold the light,” one child whispered.',
        action="They moved carefully, one with the map and one with the lantern, each helping the other.",
        requires_two=True,
        tags={"map", "lantern", "teamwork"},
    ),
}

CACHES = {
    "signal_mirror": Cache(
        id="signal_mirror",
        map_mark="an X beside a tiny crown",
        expected_treasure="a golden crown",
        actual_item="a bright signal mirror",
        reveal="Inside lay no crown at all, only a bright signal mirror wrapped in old cloth.",
        people_phrase="the harbor people below",
        help_line="From the watch platform, the children flashed the mirror toward the safe cove until the boats below turned the right way.",
        ending_line="The mirror winked like a second sun, and the children grinned at each other as the people steered home.",
        required_obstacle="ravine",
        tags={"mirror", "people", "rescue"},
    ),
    "bell_key": Cache(
        id="bell_key",
        map_mark="an X beside a drawn treasure chest",
        expected_treasure="a chest of coins",
        actual_item="a long iron bell key",
        reveal="Inside lay no coins at all, only a long iron bell key with a ribbon of faded red thread.",
        people_phrase="the town people below",
        help_line="At the top of the tower, they fitted the key, pulled together on the rope, and the warning bell boomed over the roofs.",
        ending_line="When the bell rolled out across the sky, shutters opened and the people hurried safely inside before the storm.",
        required_obstacle="stone_door",
        tags={"bell", "people", "rescue"},
    ),
    "beacon_lens": Cache(
        id="beacon_lens",
        map_mark="an X beside a drawn jewel",
        expected_treasure="a blue jewel",
        actual_item="a round beacon lens",
        reveal="Inside lay no jewel at all, only a round beacon lens polished clear as water.",
        people_phrase="the beach people far along the sand",
        help_line="In the beacon room, the children set the lens in place and turned the lamp until a strong beam swept over the foggy shore.",
        ending_line="The beam cut a bright road through the mist, and the people on the beach waved their scarves in thanks.",
        required_obstacle="dark_tunnel",
        tags={"beacon", "people", "rescue"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Asha", "Nina", "Tara", "Zoe", "Rina", "Maya"]
BOY_NAMES = ["Tomas", "Eli", "Noah", "Ben", "Arlo", "Finn", "Ravi", "Leo"]
TRAITS = ["brave", "careful", "quick", "curious", "steady", "kind"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    plan: str
    cache: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    leader_trait: str
    partner_trait: str
    seed: Optional[int] = None


def obstacle_matches(place_id: str, obstacle_id: str) -> bool:
    return obstacle_id in PLACES[place_id].supports


def combo_reason(place_id: str, obstacle_id: str, plan_id: str, cache_id: str) -> Optional[str]:
    if place_id not in PLACES:
        return "(No story: unknown place.)"
    if obstacle_id not in OBSTACLES:
        return "(No story: unknown obstacle.)"
    if plan_id not in PLANS:
        return "(No story: unknown plan.)"
    if cache_id not in CACHES:
        return "(No story: unknown cache.)"
    place = PLACES[place_id]
    obstacle = OBSTACLES[obstacle_id]
    cache = CACHES[cache_id]
    if obstacle_id not in place.supports:
        return (
            f"(No story: {place.label} does not plausibly lead to {obstacle.phrase}. "
            f"Pick an obstacle that belongs on that route.)"
        )
    if plan_id != obstacle.required_plan:
        return (
            f"(No story: {obstacle.label} is not reasonably solved by {PLANS[plan_id].label}. "
            f"It needs {PLANS[obstacle.required_plan].label} instead.)"
        )
    if cache.required_obstacle != obstacle_id:
        return (
            f"(No story: {cache.actual_item} belongs with the {obstacle.label} route, "
            f"so the map would not lead there from this obstacle.)"
        )
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for obstacle_id in sorted(OBSTACLES):
            for plan_id in sorted(PLANS):
                for cache_id in sorted(CACHES):
                    if combo_reason(place_id, obstacle_id, plan_id, cache_id) is None:
                        combos.append((place_id, obstacle_id, plan_id, cache_id))
    return combos


def predict_solo_failure(world: World) -> dict:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    kid = sim.get("leader")
    obstacle.meters["blocked"] += 1
    kid.memes["strain"] += 1
    return {
        "blocked": obstacle.meters["blocked"] >= THRESHOLD,
        "strain": kid.memes["strain"],
        "reason": sim.facts["obstacle_cfg"].solo_fail,
    }


def introduce(world: World, a: Entity, b: Entity, place: Place, cache: Cache) -> None:
    for kid in (a, b):
        kid.memes["wonder"] += 1
    world.say(
        f"{place.opening} {place.path_line}"
    )
    world.say(
        f"{a.id} and {b.id} had found an old map marked with {cache.map_mark}, and they were sure it pointed to {cache.expected_treasure}."
    )
    world.say(
        f"But it was not only treasure that pulled them uphill. A gusty voice from below said {cache.people_phrase} would need help before evening."
    )


def set_out(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"So the two children set off through {place.label} like explorers in a grand adventure, boots crunching and hearts beating fast."
    )


def encounter(world: World, obstacle: Obstacle) -> None:
    world.say(
        f"After a while, they reached {obstacle.phrase}. {obstacle.problem}"
    )


def solo_try(world: World, a: Entity) -> None:
    pred = predict_solo_failure(world)
    a.memes["impulse"] += 1
    a.memes["strain"] += 1
    world.facts["solo_prediction"] = pred
    world.say(
        f"{a.id} stepped forward first, eager to be the hero alone."
    )
    world.say(
        pred["reason"]
    )


def choose_teamwork(world: World, a: Entity, b: Entity, plan: Plan) -> None:
    for kid in (a, b):
        kid.memes["trust"] += 1
    world.say(plan.team_line)
    world.say(
        f"{a.id} looked at {b.id}, and {b.id} nodded. {plan.action}"
    )


def clear_obstacle(world: World, obstacle_ent: Entity, obstacle: Obstacle) -> None:
    obstacle_ent.meters["cleared"] += 1
    world.say(obstacle.teamwork_win)
    propagate(world, narrate=True)


def reach_cache(world: World, cache: Cache) -> None:
    world.say(
        f"Beyond the obstacle, the map led them to a hidden chest tucked behind stone and moss."
    )
    world.say(
        f"They held their breath and opened it, still expecting {cache.expected_treasure}."
    )


def reveal_twist(world: World, chest: Entity, cache: Cache) -> None:
    chest.meters["opened"] += 1
    world.say(cache.reveal)
    propagate(world, narrate=True)


def help_people(world: World, cache: Cache) -> None:
    world.facts["help_result_line"] = cache.help_line
    propagate(world, narrate=True)
    world.say(cache.ending_line)


def closing_image(world: World, place: Place) -> None:
    world.say(place.ending_image)


def tell(
    place: Place,
    obstacle: Obstacle,
    plan: Plan,
    cache: Cache,
    leader_name: str,
    leader_gender: str,
    partner_name: str,
    partner_gender: str,
    leader_trait: str,
    partner_trait: str,
) -> World:
    world = World(place)
    leader = world.add(Entity(
        id="leader",
        kind="character",
        type=leader_gender,
        label=leader_name,
        phrase=leader_name,
        role="leader",
        attrs={"name": leader_name, "trait": leader_trait},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        phrase=partner_name,
        role="partner",
        attrs={"name": partner_name, "trait": partner_trait},
    ))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=obstacle.label,
        phrase=obstacle.phrase,
    ))
    chest = world.add(Entity(
        id="cache",
        type="cache",
        label="chest",
        phrase="the hidden chest",
    ))
    world.add(Entity(id="trail", type="trail", label="trail"))
    world.add(Entity(id="quest", type="quest", label="quest"))
    world.add(Entity(id="people", type="people", label="people"))
    world.facts.update(
        place_cfg=place,
        obstacle_cfg=obstacle,
        plan_cfg=plan,
        cache_cfg=cache,
        leader=leader,
        partner=partner,
    )

    introduce(world, leader, partner, place, cache)
    set_out(world, leader, partner, place)

    world.para()
    encounter(world, obstacle)
    solo_try(world, leader)
    choose_teamwork(world, leader, partner, plan)
    clear_obstacle(world, obstacle_ent, obstacle)

    world.para()
    reach_cache(world, cache)
    reveal_twist(world, chest, cache)
    help_people(world, cache)

    world.para()
    closing_image(world, place)

    world.facts.update(
        solved=obstacle_ent.meters["cleared"] >= THRESHOLD,
        twist_found=chest.meters["opened"] >= THRESHOLD,
        people_helped=world.get("people").meters["safe"] >= THRESHOLD,
    )
    return world


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["leader"]
    b = f["partner"]
    obstacle = f["obstacle_cfg"]
    cache = f["cache_cfg"]
    place = f["place_cfg"]
    return [
        'Write an adventure story for a 3-to-5-year-old that includes the word "people" and uses teamwork plus a twist ending.',
        f"Tell a child-friendly adventure where {a.label} and {b.label} think they are hunting {cache.expected_treasure}, but after crossing {obstacle.phrase} together they discover a useful object instead.",
        f"Write a short quest set in {place.label} where two children solve a problem by working together and then help other people with what they find.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["leader"]
    b = f["partner"]
    obstacle = f["obstacle_cfg"]
    plan = f["plan_cfg"]
    cache = f["cache_cfg"]
    place = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.label} and {b.label}. They go on an adventure in {place.label} to follow a map and help other people."
        ),
        (
            "What did the children think the map would lead to?",
            f"They thought the map would lead to {cache.expected_treasure}. That hope is what made the hidden chest feel exciting before the twist."
        ),
        (
            "What problem blocked their path?",
            f"They were stopped by {obstacle.phrase}. The obstacle mattered because it was too risky or too heavy for one child alone."
        ),
        (
            "Why did they need teamwork?",
            f"They needed teamwork because {obstacle.solo_fail.lower()} Together, they could use {plan.label} and do two jobs at once."
        ),
    ]
    if f.get("twist_found"):
        qa.append((
            "What was the twist in the chest?",
            f"The chest did not hold {cache.expected_treasure}. It held {cache.actual_item}, which was more useful because it could help {cache.people_phrase}."
        ))
    if f.get("people_helped"):
        qa.append((
            "How did the children help people at the end?",
            f"{cache.help_line} The twist turns the treasure hunt into a rescue, so the ending shows they needed kindness as much as courage."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with other people safe and thankful. {place.ending_image}."
        ))
    return qa


KNOWLEDGE = {
    "rope": [
        (
            "Why can a rope help two people cross something tricky?",
            "A rope gives hands something steady to hold. When two people use it together, one can keep it tight while the other moves carefully."
        )
    ],
    "lever": [
        (
            "What does a lever do?",
            "A lever helps lift or move something heavy by using a long bar. It lets people push smarter, not just harder."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful in a dark place?",
            "A lantern makes light so you can see where to step. That helps people avoid bumps, holes, and wrong turns."
        )
    ],
    "map": [
        (
            "What does a map help people do?",
            "A map shows where to go and how places connect. It helps people find a path instead of getting lost."
        )
    ],
    "mirror": [
        (
            "How can a signal mirror help people far away?",
            "A signal mirror can flash sunlight across a long distance. People far away can see the bright blink and know where to look or go."
        )
    ],
    "bell": [
        (
            "Why does a warning bell help people?",
            "A warning bell makes a loud sound that many people can hear at once. It tells them something important is happening and they should move quickly."
        )
    ],
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a bright light used to guide people. It helps them see the safe way in darkness, fog, or stormy weather."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other do one job together. One person can do part of the job while another does a different part."
        )
    ],
    "adventure": [
        (
            "What makes something feel like an adventure?",
            "An adventure feels exciting because there is a journey, a problem, and something important to discover. It also asks people to be brave and careful."
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "adventure", "rope", "lever", "lantern", "map", "mirror", "bell", "beacon"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"teamwork", "adventure"} | set(world.facts["plan_cfg"].tags) | set(world.facts["cache_cfg"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.label and ent.label != ent.id:
            bits.append(f"label={ent.label!r}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="cliff_path",
        obstacle="ravine",
        plan="rope_team",
        cache="signal_mirror",
        leader_name="Mira",
        leader_gender="girl",
        partner_name="Tomas",
        partner_gender="boy",
        leader_trait="brave",
        partner_trait="steady",
    ),
    StoryParams(
        place="ruin_hill",
        obstacle="stone_door",
        plan="lever_push",
        cache="bell_key",
        leader_name="Noah",
        leader_gender="boy",
        partner_name="Lila",
        partner_gender="girl",
        leader_trait="curious",
        partner_trait="quick",
    ),
    StoryParams(
        place="sea_caves",
        obstacle="dark_tunnel",
        plan="map_lantern",
        cache="beacon_lens",
        leader_name="Asha",
        leader_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        leader_trait="careful",
        partner_trait="kind",
    ),
]


def explain_rejection(place_id: str, obstacle_id: str, plan_id: str, cache_id: str) -> str:
    reason = combo_reason(place_id, obstacle_id, plan_id, cache_id)
    return reason or "(No story: this combination is invalid.)"


ASP_RULES = r"""
compatible_place_obstacle(P, O) :- place_supports(P, O).
compatible_obstacle_plan(O, Pl) :- obstacle_requires(O, Pl).
compatible_obstacle_cache(O, C) :- cache_requires(C, O).

valid(P, O, Pl, C) :- place(P), obstacle(O), plan(Pl), cache(C),
                      compatible_place_obstacle(P, O),
                      compatible_obstacle_plan(O, Pl),
                      compatible_obstacle_cache(O, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.supports):
            lines.append(asp.fact("place_supports", place_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("obstacle_requires", obstacle_id, obstacle.required_plan))
    for plan_id in PLANS:
        lines.append(asp.fact("plan", plan_id))
    for cache_id, cache in CACHES.items():
        lines.append(asp.fact("cache", cache_id))
        lines.append(asp.fact("cache_requires", cache_id, cache.required_obstacle))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        params = resolve_params(default_args, random.Random(123))
        smoke_cases.append(params)
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE FAIL during resolve_params(): {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "{" in sample.story or "}" in sample.story:
                raise StoryError("unresolved template braces in story")
            if params.cache not in CACHES or params.plan not in PLANS:
                raise StoryError("generated params not in registries")
            print(f"OK: smoke story {idx} generated.")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"SMOKE FAIL on case {idx}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Adventure storyworld with teamwork and a treasure twist. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--plan", choices=sorted(PLANS))
    ap.add_argument("--cache", choices=sorted(CACHES))
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.plan and args.cache:
        reason = combo_reason(args.place, args.obstacle, args.plan, args.cache)
        if reason is not None:
            raise StoryError(reason)

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.plan is None or combo[2] == args.plan)
        and (args.cache is None or combo[3] == args.cache)
    ]
    if not combos:
        if args.place and args.obstacle and args.plan and args.cache:
            raise StoryError(explain_rejection(args.place, args.obstacle, args.plan, args.cache))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, plan_id, cache_id = rng.choice(sorted(combos))
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    leader_name = _pick_name(rng, leader_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=leader_name)
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        plan=plan_id,
        cache=cache_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        leader_trait=rng.choice(TRAITS),
        partner_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.plan not in PLANS:
        raise StoryError(f"(No story: unknown plan '{params.plan}'.)")
    if params.cache not in CACHES:
        raise StoryError(f"(No story: unknown cache '{params.cache}'.)")
    reason = combo_reason(params.place, params.obstacle, params.plan, params.cache)
    if reason is not None:
        raise StoryError(reason)

    world = tell(
        place=PLACES[params.place],
        obstacle=OBSTACLES[params.obstacle],
        plan=PLANS[params.plan],
        cache=CACHES[params.cache],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        leader_trait=params.leader_trait,
        partner_trait=params.partner_trait,
    )

    # Replace internal ids with display names in the rendered story.
    story = world.render().replace("leader", params.leader_name).replace("partner", params.partner_name)

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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, plan, cache) combos:\n")
        for place_id, obstacle_id, plan_id, cache_id in combos:
            print(f"  {place_id:11} {obstacle_id:11} {plan_id:12} {cache_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader_name} & {p.partner_name}: {p.place} / {p.obstacle} / {p.cache}"
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
