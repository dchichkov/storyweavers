#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rotten_bad_ending_happy_ending_friendship_adventure.py
=================================================================================

A standalone story world about two friends on a small adventure who meet a
**rotten** crossing on the way to their goal. The world models the physical risk
of a weak bridge / ladder / raft, the emotional pull of hurrying on, and the
repair-or-retreat choices that lead to either a happy ending or a bad ending.

The domain aims for a TinyStories-style shape:
- clear beginning: two friends set out on an adventure
- middle tension: a rotten crossing blocks the path
- turn: they either fix the problem safely or rush and lose the adventure
- ending image: friendship changed by what they chose

Run it
------
    python storyworlds/worlds/gpt-5.4/rotten_bad_ending_happy_ending_friendship_adventure.py
    python storyworlds/worlds/gpt-5.4/rotten_bad_ending_happy_ending_friendship_adventure.py --route bridge --fix rope
    python storyworlds/worlds/gpt-5.4/rotten_bad_ending_happy_ending_friendship_adventure.py --fix hop
    python storyworlds/worlds/gpt-5.4/rotten_bad_ending_happy_ending_friendship_adventure.py --all
    python storyworlds/worlds/gpt-5.4/rotten_bad_ending_happy_ending_friendship_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rotten_bad_ending_happy_ending_friendship_adventure.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so the package dir is three
# levels up from here.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    rotten: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ranger_f", "guide_f"}
        male = {"boy", "father", "man", "ranger_m", "guide_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    quest: str
    afford_routes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    scene: str
    crossing_verb: str
    failure: str
    retreat: str
    success: str
    risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    method: str
    success: str
    fail: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "friend"}]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rotten_gives_way(world: World) -> list[str]:
    route = world.get("route")
    if route.meters["stepped_on"] < THRESHOLD:
        return []
    if not route.rotten:
        return []
    sig = ("break", route.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    route.meters["broken"] += 1
    world.get("pack").meters["dropped"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__break__"]


def _r_safe_fix(world: World) -> list[str]:
    route = world.get("route")
    if route.meters["secured"] < THRESHOLD:
        return []
    sig = ("safe", route.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    route.meters["safe"] += 1
    for kid in world.kids():
        kid.memes["trust"] += 1
    return ["__safe__"]


CAUSAL_RULES = [
    Rule(name="rotten_gives_way", tag="physical", apply=_r_rotten_gives_way),
    Rule(name="safe_fix", tag="physical", apply=_r_safe_fix),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "island": Setting(
        id="island",
        place="a windy little island trail",
        sky="Sea birds wheeled over the water, and the path smelled like salt.",
        quest="the old lookout flag at the far end of the island",
        afford_routes={"bridge", "raft"},
        tags={"island", "adventure"},
    ),
    "forest": Setting(
        id="forest",
        place="a pine forest path",
        sky="Sunlight flickered through the branches, and the needles whispered underfoot.",
        quest="the hidden fern cave beyond the stream",
        afford_routes={"bridge", "ladder"},
        tags={"forest", "adventure"},
    ),
    "cliffs": Setting(
        id="cliffs",
        place="the path below the bright cliffs",
        sky="The wind hummed in the grass, and gulls called from the rocks above.",
        quest="the painted cave high in the cliff wall",
        afford_routes={"ladder", "bridge"},
        tags={"cliff", "adventure"},
    ),
}

ROUTES = {
    "bridge": Route(
        id="bridge",
        label="bridge",
        phrase="a little wooden bridge",
        scene="Across the path lay a little wooden bridge over a chattering stream. Up close, the boards looked dark and rotten.",
        crossing_verb="step onto the bridge",
        failure="The rotten boards cracked, the bridge gave a sickening jerk, and the adventure pack splashed into the water below.",
        retreat="They had to scramble back to the bank and watch the stream carry their map away.",
        success="The bridge held firm enough for careful feet once it was made safe.",
        risk=2,
        tags={"bridge", "rotten", "stream"},
    ),
    "ladder": Route(
        id="ladder",
        label="ladder",
        phrase="an old wooden ladder",
        scene="Leaning against the rock wall was an old wooden ladder. One rung was soft and rotten where the rain had soaked it.",
        crossing_verb="climb the ladder",
        failure="A rotten rung snapped with a pop, and the adventure pack tumbled down the rocks into the brambles.",
        retreat="They climbed back down slowly and could only stare at the torn map caught under the thorny vines.",
        success="The ladder stopped wobbling once the weak rung was made safe.",
        risk=3,
        tags={"ladder", "rotten", "cliff"},
    ),
    "raft": Route(
        id="raft",
        label="raft",
        phrase="a tied-up reed raft",
        scene="At the edge of the water waited a tied-up reed raft. The reeds near the middle smelled rotten and looked mushy.",
        crossing_verb="push out on the raft",
        failure="The rotten middle sagged, cold water rushed in, and the adventure pack bobbed away across the reeds.",
        retreat="They splashed back to shore and watched their chance drift out of reach.",
        success="The raft floated steady once it had been tightened and balanced.",
        risk=2,
        tags={"raft", "rotten", "water"},
    ),
}

PRIZES = {
    "flag": Prize(
        id="flag",
        label="flag",
        phrase="a bright lookout flag",
        ending_image="At the end, the bright lookout flag fluttered above them like a little promise kept.",
        tags={"flag"},
    ),
    "shell": Prize(
        id="shell",
        label="shell",
        phrase="a silver spiral shell",
        ending_image="At the end, the silver spiral shell shone in their joined hands.",
        tags={"shell"},
    ),
    "badge": Prize(
        id="badge",
        label="badge",
        phrase="a round explorer badge",
        ending_image="At the end, the round explorer badge gleamed on the front of their shared map pouch.",
        tags={"badge"},
    ),
}

FIXES = {
    "rope": Fix(
        id="rope",
        label="rope",
        phrase="a coil of rope",
        sense=3,
        power=3,
        method="looped a rope around the safest posts and used it as a steady hand-line",
        success="Together they looped a rope around the strongest parts and crossed one careful step at a time.",
        fail="They tried to use a rope, but the rotten wood was already too weak to trust.",
        qa_text="used a rope to steady the crossing",
        tags={"rope", "safety"},
    ),
    "planks": Fix(
        id="planks",
        label="spare planks",
        phrase="two spare planks",
        sense=3,
        power=4,
        method="laid spare planks over the weakest part and tested each step before moving",
        success="They laid spare planks over the weak place and tested each board before they crossed.",
        fail="They set down spare planks, but the whole rotten crossing shifted underneath them.",
        qa_text="covered the weak place with spare planks and crossed carefully",
        tags={"planks", "safety"},
    ),
    "guide": Fix(
        id="guide",
        label="the park guide",
        phrase="the nearby park guide",
        sense=3,
        power=5,
        method="called the park guide, who showed them the strong way across and held the line",
        success="They called the park guide, who came over smiling, showed them the strong way across, and held the line while they crossed.",
        fail="Even the park guide had to shake a head because the crossing was too far gone to use that day.",
        qa_text="called the park guide for help crossing safely",
        tags={"guide", "adult_help"},
    ),
    "hop": Fix(
        id="hop",
        label="a running hop",
        phrase="a running hop",
        sense=1,
        power=1,
        method="decided to race across before the rotten part noticed",
        success="They raced ahead too fast to notice the danger.",
        fail="They tried to hop fast across it, but speed could not make rotten wood strong.",
        qa_text="tried to hop across quickly",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli"]
TRAITS = ["brave", "careful", "curious", "steady", "thoughtful", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    route: str
    prize: str
    fix: str
    leader: str
    leader_gender: str
    friend: str
    friend_gender: str
    guide_type: str
    leader_trait: str
    friend_trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="forest",
        route="bridge",
        prize="badge",
        fix="rope",
        leader="Max",
        leader_gender="boy",
        friend="Lily",
        friend_gender="girl",
        guide_type="ranger_f",
        leader_trait="curious",
        friend_trait="careful",
        delay=0,
    ),
    StoryParams(
        setting="island",
        route="raft",
        prize="shell",
        fix="guide",
        leader="Ava",
        leader_gender="girl",
        friend="Ben",
        friend_gender="boy",
        guide_type="ranger_m",
        leader_trait="brave",
        friend_trait="steady",
        delay=1,
    ),
    StoryParams(
        setting="cliffs",
        route="ladder",
        prize="flag",
        fix="hop",
        leader="Sam",
        leader_gender="boy",
        friend="Mia",
        friend_gender="girl",
        guide_type="ranger_f",
        leader_trait="brave",
        friend_trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        setting="forest",
        route="ladder",
        prize="badge",
        fix="planks",
        leader="Zoe",
        leader_gender="girl",
        friend="Noah",
        friend_gender="boy",
        guide_type="ranger_m",
        leader_trait="cheerful",
        friend_trait="careful",
        delay=0,
    ),
]


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for rid in sorted(setting.afford_routes):
            for pid in PRIZES:
                combos.append((sid, rid, pid))
    return combos


def route_severity(route: Route, delay: int) -> int:
    return route.risk + delay


def is_success(fix: Fix, route: Route, delay: int) -> bool:
    return fix.power >= route_severity(route, delay)


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try a safer fix like {better}.)"
    )


def explain_route(setting_id: str, route_id: str) -> str:
    return (
        f"(No story: {ROUTES[route_id].label} does not belong in {SETTINGS[setting_id].place}. "
        f"Pick one of {sorted(SETTINGS[setting_id].afford_routes)}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "happy" if is_success(FIXES[params.fix], ROUTES[params.route], params.delay) else "bad"


def introduce(world: World, leader: Entity, friend: Entity, prize: Prize) -> None:
    leader.memes["joy"] += 1
    friend.memes["joy"] += 1
    leader.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{leader.id} and {friend.id} were best friends, and best friends made every path feel like the start of an adventure."
    )
    world.say(
        f"That morning they set out along {world.setting.place}, hoping to find {world.setting.quest} and bring back {prize.phrase}."
    )
    world.say(world.setting.sky)


def discover(world: World, leader: Entity, friend: Entity, route: Route) -> None:
    world.say(route.scene)
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} touched the wood with two careful fingers. "It feels rotten," {friend.pronoun()} said.'
    )
    leader.memes["desire"] += 1
    world.say(
        f'{leader.id} leaned forward to look past it. "Our adventure is right over there," {leader.pronoun()} whispered.'
    )


def predict_break(route: Route) -> bool:
    return route.risk >= 2


def warn(world: World, leader: Entity, friend: Entity, route: Route, fix: Fix) -> None:
    world.facts["predicted_break"] = predict_break(route)
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. "If we just {route.crossing_verb}, it could break," {friend.pronoun()} said.'
    )
    if fix.sense >= SENSE_MIN:
        world.say(
            f'{friend.id} pointed at {fix.phrase}. "We can still be explorers," {friend.pronoun()} added. "We just have to do it the safe way."'
        )
    else:
        world.say(
            f"For one reckless second, even the silly idea of {fix.phrase} sounded quick."
        )


def try_crossing(world: World, leader: Entity, friend: Entity, route: Route) -> None:
    route_ent = world.get("route")
    route_ent.meters["stepped_on"] += 1
    propagate(world, narrate=False)
    leader.memes["defiance"] += 1
    friend.memes["fear"] += 1
    world.say(
        f"But the hurry of the adventure pulled harder than their caution, and they tried to {route.crossing_verb} anyway."
    )
    if route_ent.meters["broken"] >= THRESHOLD:
        world.say(route.failure)


def fail_ending(world: World, leader: Entity, friend: Entity, route: Route, prize: Prize, fix: Fix) -> None:
    pack = world.get("pack")
    pack.meters["lost"] += 1
    leader.memes["sadness"] += 1
    friend.memes["sadness"] += 1
    leader.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(route.retreat)
    world.say(
        f'They did not reach {prize.phrase} that day. "{fix.fail}" {friend.id} said softly, not to blame anyone, only to tell the truth.'
    )
    world.say(
        f"{leader.id} wanted to cry, but {friend.id} took {leader.pronoun('possessive')} hand. They walked home muddy and quiet, still friends, but with their adventure ending early under a gray sky."
    )


def choose_fix(world: World, leader: Entity, friend: Entity, fix: Fix) -> None:
    leader.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{leader.id} let out a long breath. "You are right," {leader.pronoun()} said. "Real explorers look after each other."'
    )
    world.say(
        f"Then the two friends {fix.method}."
    )


def success_ending(world: World, leader: Entity, friend: Entity, route: Route, prize: Prize, fix: Fix) -> None:
    route_ent = world.get("route")
    route_ent.meters["secured"] += 1
    propagate(world, narrate=False)
    leader.memes["relief"] += 1
    friend.memes["relief"] += 1
    leader.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(fix.success)
    world.say(route.success)
    world.say(
        f"On the other side they found {prize.phrase}, and both of them laughed the bright laugh that comes after a scary moment has passed."
    )
    world.say(
        f'{leader.id} said, "We found the treasure because we stayed friends and listened." {friend.id} grinned and tucked close beside {leader.pronoun("object")}.'
    )
    world.say(prize.ending_image)


def tell(
    setting: Setting,
    route: Route,
    prize: Prize,
    fix: Fix,
    leader_name: str = "Lily",
    leader_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    guide_type: str = "ranger_f",
    leader_trait: str = "brave",
    friend_trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World(setting=setting)
    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_gender,
            label=leader_name,
            role="leader",
            traits=[leader_trait],
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            traits=[friend_trait],
        )
    )
    guide = world.add(
        Entity(
            id="Guide",
            kind="character",
            type=guide_type,
            label="guide",
            role="guide",
        )
    )
    route_ent = world.add(
        Entity(
            id="route",
            type=route.label,
            label=route.label,
            phrase=route.phrase,
            rotten=True,
            tags=set(route.tags),
        )
    )
    world.add(
        Entity(
            id="pack",
            type="pack",
            label="adventure pack",
            phrase="their adventure pack",
        )
    )

    introduce(world, leader, friend, prize)
    world.para()
    discover(world, leader, friend, route)
    warn(world, leader, friend, route, fix)
    world.para()

    happy = is_success(fix, route, delay)
    if happy:
        choose_fix(world, leader, friend, fix)
        success_ending(world, leader, friend, route, prize, fix)
    else:
        try_crossing(world, leader, friend, route)
        fail_ending(world, leader, friend, route, prize, fix)

    world.facts.update(
        leader=leader,
        friend=friend,
        guide=guide,
        route_cfg=route,
        route=route_ent,
        prize=prize,
        fix=fix,
        setting=setting,
        outcome="happy" if happy else "bad",
        delay=delay,
        friendship_stronger=leader.memes["friendship"] >= 2,
        pack_lost=world.get("pack").meters["lost"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "rotten": [
        (
            "What does rotten wood mean?",
            "Rotten wood is old, wet, or damaged wood that has gone soft and weak. It can crack or break if someone puts weight on it."
        )
    ],
    "bridge": [
        (
            "Why can an old wooden bridge be dangerous?",
            "An old wooden bridge can be dangerous when boards are loose or rotten. Then it may not hold a person's weight."
        )
    ],
    "ladder": [
        (
            "Why is a rotten ladder unsafe?",
            "A rotten ladder is unsafe because the weak rung can snap while someone is climbing. That can make them fall or drop what they are carrying."
        )
    ],
    "raft": [
        (
            "Why can a rotten raft sink?",
            "A rotten raft can sink because the weak middle parts soak up water and sag. Then the raft cannot hold people or packs safely."
        )
    ],
    "rope": [
        (
            "How can a rope help on a tricky path?",
            "A rope can give your hands something steady to hold. That makes it easier to move slowly and safely."
        )
    ],
    "planks": [
        (
            "Why do strong planks help over a weak spot?",
            "Strong planks spread weight over a safer surface. They can cover a weak place that should not be stepped on directly."
        )
    ],
    "adult_help": [
        (
            "Why is it smart to ask a grown-up for help on an adventure?",
            "A grown-up may know the safe way through a risky place. Asking for help is careful and brave, not babyish."
        )
    ],
    "friendship": [
        (
            "What does a good friend do during a hard moment?",
            "A good friend warns you about danger, stays with you, and helps you make a better choice. Friendship means caring about each other more than winning quickly."
        )
    ],
}
KNOWLEDGE_ORDER = ["rotten", "bridge", "ladder", "raft", "rope", "planks", "adult_help", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    route = f["route_cfg"]
    prize = f["prize"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a 3-to-5-year-old that includes the word "rotten" and centers on friendship.'
    )
    if outcome == "happy":
        return [
            base,
            f"Tell a story where {leader.id} and {friend.id} find a rotten {route.label} on the way to {prize.phrase}, choose a careful fix, and end their adventure happy together.",
            f"Write a gentle adventure where two friends face danger, listen to each other, and prove their friendship by reaching the treasure safely.",
        ]
    return [
        base,
        f"Tell a story where {leader.id} and {friend.id} hurry onto a rotten {route.label}, lose their chance at {prize.phrase}, and walk home sad but still caring for each other.",
        f"Write a cautionary adventure with a bad ending for the treasure hunt but a kind friendship at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    route = f["route_cfg"]
    prize = f["prize"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {leader.id} and {friend.id}, going on a small adventure together. Their friendship matters as much as the treasure they hope to find."
        ),
        (
            "What problem did they find on the path?",
            f"They found a rotten {route.label} blocking the way. It looked weak enough to break if they trusted it without being careful."
        ),
        (
            f"Why did {friend.id} warn {leader.id}?",
            f"{friend.id} warned {leader.id} because the {route.label} looked rotten and unsafe. The warning came from seeing that quick adventure steps could turn into real danger."
        ),
    ]
    if outcome == "happy":
        qa.append(
            (
                "How did they solve the problem?",
                f"They {fix.qa_text}. That let them cross safely instead of rushing onto the rotten {route.label}."
            )
        )
        qa.append(
            (
                "Why is this a happy ending?",
                f"It is a happy ending because they reached {prize.phrase} and nobody got hurt. It is even happier because their friendship grew stronger when they listened to each other."
            )
        )
    else:
        qa.append(
            (
                "What went wrong when they hurried?",
                f"When they hurried, the rotten {route.label} gave way and their adventure pack was lost. That ended the treasure hunt because they could not safely keep going."
            )
        )
        qa.append(
            (
                "Why is this a bad ending, and what stayed good?",
                f"It is a bad ending because they lost their chance to reach {prize.phrase} and had to turn back. What stayed good was their friendship, because {friend.id} still held {leader.id}'s hand and walked home with {leader.pronoun('object')}."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rotten", "friendship"}
    route = world.facts["route_cfg"]
    fix = world.facts["fix"]
    tags |= set(route.tags)
    tags |= set(fix.tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.rotten:
            bits.append("rotten=True")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% route belongs in setting
valid(S, R, P) :- setting(S), route(R), prize(P), affords(S, R).

% common-sense gate for fixes
sensible(F) :- fix(F), sense(F, N), sense_min(M), N >= M.

% outcome model
severity(V) :- chosen_route(R), risk(R, K), delay(D), V = K + D.
happy :- chosen_fix(F), power(F, P), severity(V), P >= V.
bad :- chosen_fix(F), power(F, P), severity(V), P < V.
outcome(happy) :- happy.
outcome(bad) :- bad.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for rid in sorted(setting.afford_routes):
            lines.append(asp.fact("affords", sid, rid))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("risk", rid, route.risk))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {f.id for f in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    # Smoke-test ordinary generation on curated stories.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: two friends, a rotten crossing, and an adventure ending either happily or badly."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra risk before they act")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.route and args.route not in SETTINGS[args.setting].afford_routes:
        raise StoryError(explain_route(args.setting, args.route))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.route is None or combo[1] == args.route)
        and (args.prize is None or combo[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, route_id, prize_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    leader_name, leader_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=leader_name)
    guide_type = rng.choice(["ranger_f", "ranger_m"])
    leader_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        setting=setting_id,
        route=route_id,
        prize=prize_id,
        fix=fix_id,
        leader=leader_name,
        leader_gender=leader_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        guide_type=guide_type,
        leader_trait=leader_trait,
        friend_trait=friend_trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        route = ROUTES[params.route]
        prize = PRIZES[params.prize]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err})") from err

    if params.route not in setting.afford_routes:
        raise StoryError(explain_route(params.setting, params.route))
    if fix.sense < SENSE_MIN and params.fix != "hop":
        raise StoryError(explain_fix(params.fix))

    world = tell(
        setting=setting,
        route=route,
        prize=prize,
        fix=fix,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        guide_type=params.guide_type,
        leader_trait=params.leader_trait,
        friend_trait=params.friend_trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, route, prize) combos:\n")
        for setting_id, route_id, prize_id in combos:
            print(f"  {setting_id:8} {route_id:7} {prize_id}")
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
            header = f"### {p.leader} & {p.friend}: {p.route} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
