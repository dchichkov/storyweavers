#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/find_construction_site_lesson_learned_mystery_to.py
==============================================================================

A standalone story world about a child trying to find a missing thing near a
construction site. The story always includes:

- a small mystery to solve
- a moment of conflict over an unsafe idea
- a calm lesson learned
- a rhyming-story style

The world model prefers a sensible, child-safe resolution: the children stay
outside the barrier and ask a worker for help instead of sneaking inside.

Run it
------
    python storyworlds/worlds/gpt-5.4/find_construction_site_lesson_learned_mystery_to.py
    python storyworlds/worlds/gpt-5.4/find_construction_site_lesson_learned_mystery_to.py --item toy_truck
    python storyworlds/worlds/gpt-5.4/find_construction_site_lesson_learned_mystery_to.py --method sneak_gap
    python storyworlds/worlds/gpt-5.4/find_construction_site_lesson_learned_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/find_construction_site_lesson_learned_mystery_to.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/find_construction_site_lesson_learned_mystery_to.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so results.py is three
# directories up in storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
class Site:
    id: str
    label: str
    scene: str
    sounds: str
    barrier: str
    view_spot: str
    zones: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    owner: str
    zone: str
    lost_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    text: str
    points_to: set[str] = field(default_factory=set)
    rhyme: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    call_name: str
    covers: set[str] = field(default_factory=set)
    find_text: str = ""
    lesson_text: str = ""
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "mother"}
        male = {"man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Method:
    id: str
    label: str
    sense: int
    style: str
    ask_line: str
    wait_line: str
    speed: int
    tags: set[str] = field(default_factory=set)


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"seeker", "friend"}]

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


def _r_inside_danger(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.meters["inside_site"] < THRESHOLD:
            continue
        sig = ("inside_danger", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        kid.memes["lesson"] += 1
        if "site" in world.entities:
            world.get("site").meters["danger"] += 1
        out.append("__danger__")
    return out


def _r_conflict(world: World) -> list[str]:
    seeker = world.entities.get("seeker")
    friend = world.entities.get("friend")
    if seeker is None or friend is None:
        return []
    if seeker.memes["desire"] < THRESHOLD or friend.memes["caution"] < THRESHOLD:
        return []
    sig = ("conflict", "seeker_friend")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    return ["__conflict__"]


def _r_found_relief(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    return ["__found__"]


CAUSAL_RULES = [
    Rule(name="inside_danger", tag="physical", apply=_r_inside_danger),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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
        for s in produced:
            world.say(s)
    return produced


def clue_matches(item: MissingItem, clue: Clue) -> bool:
    return item.zone in clue.points_to


def helper_can_reach(item: MissingItem, helper: Helper) -> bool:
    return item.zone in helper.covers


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for site_id, site in SITES.items():
        for item_id, item in ITEMS.items():
            if item.zone not in site.zones:
                continue
            for clue_id, clue in CLUES.items():
                if not clue_matches(item, clue):
                    continue
                for helper_id, helper in HELPERS.items():
                    if not helper_can_reach(item, helper):
                        continue
                    for method_id, method in METHODS.items():
                        if method.sense >= SENSE_MIN:
                            combos.append((site_id, item_id, clue_id, helper_id, method_id))
    return sorted(combos)


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': {method.label} is not a sensible child-safe choice "
        f"at a construction site. Try one of: {better}.)"
    )


def explain_combo_rejection(item: MissingItem, clue: Clue, helper: Helper) -> str:
    if not clue_matches(item, clue):
        return (
            f"(No story: {clue.label} does not honestly point to the missing {item.label}, "
            f"so the mystery would feel fake.)"
        )
    if not helper_can_reach(item, helper):
        return (
            f"(No story: the {helper.label} would not be working near the {item.zone.replace('_', ' ')}, "
            f"so that helper could not plausibly find the {item.label}.)"
        )
    return "(No story: this combination does not form a reasonable construction-site mystery.)"


def outcome_of(params: "StoryParams") -> str:
    return "quick_find" if METHODS[params.method].speed == 1 else "careful_find"


def predict_danger(world: World) -> dict:
    sim = world.copy()
    seeker = sim.get("seeker")
    seeker.meters["inside_site"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("site").meters["danger"],
        "fear": seeker.memes["fear"],
    }


def opening(world: World, site: Site, seeker: Entity, friend: Entity, item: MissingItem) -> None:
    world.say(
        f"By the {site.label}, where hammers beat time, {seeker.id} and {friend.id} "
        f"walked by in the afternoon shine."
    )
    world.say(
        f"{site.scene} {site.sounds} From {site.view_spot}, they peeped with bright eyes "
        f"and small, careful feet."
    )
    seeker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Then {seeker.id} gave a gasp and a little soft whine: "
        f'"Oh no, I cannot {item.lost_line}!"'
    )


def notice_clue(world: World, seeker: Entity, friend: Entity, clue: Clue, item: MissingItem) -> None:
    seeker.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"Near the fence they spotted {clue.text} It looked like a hint, like a trail, like a sign to {clue.rhyme}."
    )
    world.say(
        f'"If we are patient and think before we dash, we might {item.owner} and {item.label} without a crash," '
        f"{friend.id} said in a hush."
    )


def temptation(world: World, seeker: Entity, friend: Entity, site: Site) -> None:
    seeker.memes["desire"] += 1
    friend.memes["caution"] += 1
    propagate(world, narrate=False)
    pred = predict_danger(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'But {seeker.id} saw a gap by the rope and sighed, "If I slip inside, I could look with one stride."'
    )
    extra = ""
    if pred["danger"] >= THRESHOLD:
        extra = (
            f" {friend.id} pictured busy boots, big beams, and loud surprise, "
            f"and shook {friend.pronoun('possessive')} head with wide, worried eyes."
        )
    world.say(
        f'"No, no," said {friend.id}. "This is no place to hide. {site.barrier} '
        f"Heavy things move, and we must stay outside.\"{extra}"
    )


def ask_for_help(world: World, seeker: Entity, friend: Entity, helper_ent: Entity, method: Method, helper: Helper) -> None:
    world.say(
        f"{method.ask_line} Their voices stayed clear, not pushy, not loud, just brave enough to carry above the crowd."
    )
    world.say(
        f'"{helper.call_name}," called {friend.id}, "can you help us find something small?" '
        f"The {helper.label} turned kindly and heard it all."
    )
    seeker.memes["trust"] += 1
    friend.memes["trust"] += 1
    helper_ent.memes["care"] += 1


def helper_search(world: World, helper_ent: Entity, helper: Helper, item_ent: Entity, clue: Clue, item: MissingItem, method: Method) -> None:
    world.say(
        f"The {helper.label} looked at {clue.label}, then nodded with care. "
        f"{helper.find_text}"
    )
    if method.speed == 1:
        world.say(
            f"In hardly a minute, with dust on one glove, {helper_ent.pronoun('subject')} came back with the {item.label} they loved."
        )
    else:
        world.say(
            f"{method.wait_line} After a little while, with a wave and a grin, {helper_ent.pronoun('subject')} came back with the lost thing tucked in."
        )
    item_ent.meters["found"] += 1
    propagate(world, narrate=False)


def return_item(world: World, seeker: Entity, item_ent: Entity, item: MissingItem) -> None:
    world.say(
        f'"I found it!" cried {seeker.id}. "My worry can end. The {item.label} is back, and so is my grin, my dear friend."'
    )
    if item.owner == "my":
        world.say(
            f"{seeker.id} hugged the {item.label} close to {seeker.pronoun('possessive')} chest, "
            f"and the thump in {seeker.pronoun('possessive')} heart settled down to a rest."
        )
    else:
        world.say(
            f"They held the found thing gently, not swinging it high, happy that help had come by instead of a try."
        )


def lesson(world: World, seeker: Entity, friend: Entity, helper_ent: Entity, helper: Helper, site: Site) -> None:
    seeker.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    seeker.memes["shame"] = 0.0
    friend.memes["fear"] = 0.0
    world.say(
        f'Then the {helper.label} smiled and spoke slow, so the lesson could settle and quietly grow. '
        f'"{helper.lesson_text} {site.barrier} Ask first, wait still, and let workers guide."'
    )
    world.say(
        f'{seeker.id} nodded. "{friend.id} was right. To find what is lost, I do not need a dangerous flight."'
    )
    world.say(
        f"So hand in hand, by the fence in the sun, they walked home wiser, and the mystery was done."
    )


def tell(
    site: Site,
    item: MissingItem,
    clue: Clue,
    helper: Helper,
    method: Method,
    seeker_name: str = "Mina",
    seeker_gender: str = "girl",
    friend_name: str = "Toby",
    friend_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    seeker = world.add(Entity(id="seeker", kind="character", type=seeker_gender, label=seeker_name, phrase=seeker_name, role="seeker"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, phrase=friend_name, role="friend"))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper.type, label=helper.label, phrase=helper.label, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", phrase="the parent", role="parent"))
    site_ent = world.add(Entity(id="site", kind="thing", type="site", label=site.label, phrase=site.label, role="site"))
    item_ent = world.add(Entity(id="item", kind="thing", type="item", label=item.label, phrase=item.phrase, role="item"))
    world.facts["names"] = {"seeker": seeker_name, "friend": friend_name}

    opening(world, site, seeker, friend, item)
    notice_clue(world, seeker, friend, clue, item)

    world.para()
    temptation(world, seeker, friend, site)
    ask_for_help(world, seeker, friend, helper_ent, method, helper)

    world.para()
    helper_search(world, helper_ent, helper, item_ent, clue, item, method)
    return_item(world, seeker, item_ent, item)

    world.para()
    lesson(world, seeker, friend, helper_ent, helper, site)

    world.facts.update(
        site=site,
        item_cfg=item,
        clue=clue,
        helper_cfg=helper,
        method=method,
        seeker=seeker,
        friend=friend,
        helper=helper_ent,
        parent=parent,
        item=item_ent,
        found=item_ent.meters["found"] >= THRESHOLD,
        outcome="quick_find" if method.speed == 1 else "careful_find",
    )
    return world


SITES = {
    "crane_yard": Site(
        id="crane_yard",
        label="the crane yard",
        scene="Yellow cranes stretched high like giraffes in the sky.",
        sounds="Metal clinked and engines hummed in a dusty beat.",
        barrier="The orange fence and striped rope mean stop on this side.",
        view_spot="the safe sidewalk",
        zones={"sand_pile", "tool_shed", "blue_table"},
        tags={"construction_site", "fence"},
    ),
    "brick_lane": Site(
        id="brick_lane",
        label="the brick lane build",
        scene="Stacks of bricks sat neat as if lined up for a song.",
        sounds="Trowels tapped softly while wheelbarrows rolled along.",
        barrier="The bright cones and mesh fence mean stop on this side.",
        view_spot="the corner curb",
        zones={"sand_pile", "tool_shed", "blue_table"},
        tags={"construction_site", "fence"},
    ),
    "road_patch": Site(
        id="road_patch",
        label="the road patch site",
        scene="Fresh gravel glittered while signs stood stern and tall.",
        sounds="A roller rumbled low like a drumbeat for them all.",
        barrier="The safety gate and warning signs mean stop on this side.",
        view_spot="the painted lookout line",
        zones={"sand_pile", "tool_shed", "blue_table"},
        tags={"construction_site", "fence"},
    ),
}

ITEMS = {
    "toy_truck": MissingItem(
        id="toy_truck",
        label="toy truck",
        phrase="a small red toy truck",
        owner="my",
        zone="sand_pile",
        lost_line="find my toy truck anywhere in sight",
        tags={"toy", "find"},
    ),
    "lunch_pail": MissingItem(
        id="lunch_pail",
        label="lunch pail",
        phrase="a blue lunch pail",
        owner="the worker's",
        zone="tool_shed",
        lost_line="find that lunch pail from this side of the line",
        tags={"lunch", "find"},
    ),
    "plan_tube": MissingItem(
        id="plan_tube",
        label="plan tube",
        phrase="a rolled-up plan tube",
        owner="the builder's",
        zone="blue_table",
        lost_line="find that plan tube before the papers fly",
        tags={"plans", "find"},
    ),
}

CLUES = {
    "tiny_tracks": Clue(
        id="tiny_tracks",
        label="tiny wheel tracks",
        text="tiny wheel tracks curling toward the sand pile.",
        points_to={"sand_pile"},
        rhyme="where the answer might wait in a pile",
        tags={"tracks", "mystery"},
    ),
    "apple_smell": Clue(
        id="apple_smell",
        label="a sweet apple smell",
        text="a sweet apple smell drifting from the little tool shed.",
        points_to={"tool_shed"},
        rhyme="where lunch might be waiting ahead",
        tags={"smell", "mystery"},
    ),
    "blue_corner": Clue(
        id="blue_corner",
        label="a blue paper corner",
        text="a blue paper corner peeking from the table by the beams.",
        points_to={"blue_table"},
        rhyme="where a plan might be tucked with the dreams",
        tags={"paper", "mystery"},
    ),
}

HELPERS = {
    "operator": Helper(
        id="operator",
        label="crane operator",
        type="man",
        call_name="Mister Operator",
        covers={"sand_pile"},
        find_text="He checked beside the sand pile with long, steady strides, careful to look where the little track hides.",
        lesson_text="A construction site is for working, not wandering wide.",
        tags={"worker", "crane"},
    ),
    "foreman": Helper(
        id="foreman",
        label="foreman",
        type="woman",
        call_name="Ms. Foreman",
        covers={"tool_shed", "blue_table"},
        find_text="She followed the clue with a practiced eye and looked near the busy table and shed nearby.",
        lesson_text="When something is missing near machines and gear, a worker can help far better than a child coming near.",
        tags={"worker", "supervisor"},
    ),
    "mason": Helper(
        id="mason",
        label="mason",
        type="man",
        call_name="Builder Ben",
        covers={"blue_table"},
        find_text="He brushed past the stacked bricks, peered under the blue table, and checked each corner as calmly as able.",
        lesson_text="The safest way to solve a puzzle here is to ask and wait, not slip past the gate.",
        tags={"worker", "bricks"},
    ),
}

METHODS = {
    "ask_gate": Method(
        id="ask_gate",
        label="ask from the gate",
        sense=3,
        style="direct",
        ask_line="So they stayed by the barrier, toes on the mat, and called for a worker instead of all that.",
        wait_line="",
        speed=1,
        tags={"ask_adult", "safe"},
    ),
    "wait_wave": Method(
        id="wait_wave",
        label="wait and wave from outside",
        sense=2,
        style="patient",
        ask_line="So they stayed by the barrier and lifted a hand, waving for help where the workers could understand.",
        wait_line="They waited outside where the striped lines lay, patient as pebbles till the machines paused away.",
        speed=2,
        tags={"ask_adult", "wait", "safe"},
    ),
    "sneak_gap": Method(
        id="sneak_gap",
        label="sneak through the gap in the fence",
        sense=1,
        style="unsafe",
        ask_line="",
        wait_line="",
        speed=0,
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ruby", "Ella", "Tess", "Ava", "Lucy"]
BOY_NAMES = ["Toby", "Finn", "Max", "Owen", "Leo", "Ben", "Eli", "Sam"]
TRAITS = ["curious", "careful", "bright", "patient", "quick-thinking"]


@dataclass
class StoryParams:
    site: str
    item: str
    clue: str
    helper: str
    method: str
    seeker_name: str
    seeker_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seeker_trait: str
    friend_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "construction_site": [
        (
            "Why is a construction site not a good place for children to play?",
            "A construction site has heavy tools, moving machines, and places that are blocked off for safety. Children should stay outside and let workers handle the busy parts."
        )
    ],
    "fence": [
        (
            "Why do construction sites have fences and warning signs?",
            "Fences and warning signs tell people where it is safe to stand and where they must not go. They help keep children and grown-ups away from moving equipment."
        )
    ],
    "worker": [
        (
            "Who should help if something is lost near a work site?",
            "A worker or another grown-up should help. They know the safe paths and can look without stepping into danger."
        )
    ],
    "crane": [
        (
            "What does a crane do?",
            "A crane lifts heavy things high into the air. That is why people must stay well back and let trained workers use it."
        )
    ],
    "bricks": [
        (
            "Why must people be careful around stacks of bricks?",
            "Stacks of bricks are heavy and can hurt someone if they fall or if a person climbs where they should not. It is safest to leave them alone."
        )
    ],
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks can be a clue that shows where something rolled or moved. They help you solve a mystery by pointing to a place."
        )
    ],
    "smell": [
        (
            "How can a smell be a clue?",
            "A smell can tell you what is nearby, like lunch or paint. Sometimes your nose helps your brain solve a little mystery."
        )
    ],
    "paper": [
        (
            "How can a scrap of paper help solve a mystery?",
            "A scrap of paper can show where another paper or object has blown or slid. Small clues can help you think carefully."
        )
    ],
    "ask_adult": [
        (
            "What should a child do instead of sneaking into a dangerous place?",
            "The child should stop, stay in the safe spot, and ask a grown-up for help. Asking is brave because it keeps everyone safer."
        )
    ],
    "wait": [
        (
            "Why can waiting be part of being safe?",
            "Waiting gives workers time to stop machines and check the area. Sometimes the safest choice is to be patient first."
        )
    ],
    "toy": [
        (
            "Why is it okay to wait for help even if your toy is lost?",
            "A toy matters, but your body matters more. A grown-up can help you get the toy in a safer way."
        )
    ],
    "lunch": [
        (
            "What is a lunch pail?",
            "A lunch pail is a little container that carries food for later. Workers often bring one so they can eat during a break."
        )
    ],
    "plans": [
        (
            "What are building plans?",
            "Building plans are drawings that show workers what to build and where to build it. They help a whole team work the same way."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "construction_site",
    "fence",
    "worker",
    "crane",
    "bricks",
    "tracks",
    "smell",
    "paper",
    "ask_adult",
    "wait",
    "toy",
    "lunch",
    "plans",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    friend = f["friend"]
    item = f["item_cfg"]
    site = f["site"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old set at a construction site that includes the word "find".',
        f"Tell a gentle mystery story where {seeker.label} wants to find a lost {item.label} near {site.label}, but a friend stops an unsafe choice and a worker helps.",
        f"Write a child-facing poem-story with conflict, a clue, and a lesson learned: stay outside the barrier, ask for help, and solve the mystery safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    friend = f["friend"]
    helper_ent = f["helper"]
    item = f["item_cfg"]
    clue = f["clue"]
    site = f["site"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.label} and {friend.label}, two children near {site.label}, and a worker who helps them. They face a little mystery and solve it safely."
        ),
        (
            f"What was the mystery to solve?",
            f"The mystery was how to find the lost {item.label}. The children noticed {clue.label}, so the clue gave them a smart place to look."
        ),
        (
            f"Why did {friend.label} tell {seeker.label} not to go inside?",
            f"{friend.label} knew the construction site was busy and not made for children to wander through. The warning mattered because heavy tools and moving machines can turn one quick step into a dangerous one."
        ),
        (
            "How did they solve the problem?",
            f"They stayed outside the barrier and used the safe plan to {method.label}. Then the worker checked the clue's area and brought the {item.label} back."
        ),
        (
            "What lesson did the children learn?",
            f"They learned that being brave does not mean sneaking into danger. It means stopping, thinking, and asking a grown-up for help when a place is not safe."
        ),
    ]
    if f["outcome"] == "quick_find":
        qa.append(
            (
                "Did they find it quickly or after waiting?",
                f"They found it quickly. Their clear call for help let the worker understand the problem and look right away."
            )
        )
    else:
        qa.append(
            (
                "Why did they have to wait a little?",
                f"They waited because being safe sometimes means letting workers pause and check carefully first. The waiting helped keep the children outside the busy area until it was safe for the worker to look."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["site"].tags)
    tags |= set(world.facts["item_cfg"].tags)
    tags |= set(world.facts["clue"].tags)
    tags |= set(world.facts["helper_cfg"].tags)
    tags |= set(world.facts["method"].tags)
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        site="crane_yard",
        item="toy_truck",
        clue="tiny_tracks",
        helper="operator",
        method="ask_gate",
        seeker_name="Mina",
        seeker_gender="girl",
        friend_name="Toby",
        friend_gender="boy",
        parent="mother",
        seeker_trait="curious",
        friend_trait="careful",
    ),
    StoryParams(
        site="brick_lane",
        item="plan_tube",
        clue="blue_corner",
        helper="mason",
        method="wait_wave",
        seeker_name="Finn",
        seeker_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        parent="father",
        seeker_trait="bright",
        friend_trait="patient",
    ),
    StoryParams(
        site="road_patch",
        item="lunch_pail",
        clue="apple_smell",
        helper="foreman",
        method="ask_gate",
        seeker_name="Ella",
        seeker_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
        seeker_trait="quick-thinking",
        friend_trait="careful",
    ),
]


ASP_RULES = r"""
% --- registries and reasonableness -----------------------------------------
match(Item, Clue)    :- item(Item), clue(Clue), zone(Item, Z), points_to(Clue, Z).
reachable(Item, H)   :- item(Item), helper(H), zone(Item, Z), covers(H, Z).
sensible(M)          :- method(M), sense(M, S), sense_min(Min), S >= Min.

valid(Site, Item, Clue, H, M) :-
    site(Site), item(Item), clue(Clue), helper(H), method(M),
    site_zone(Site, Z), zone(Item, Z),
    match(Item, Clue), reachable(Item, H), sensible(M).

% --- simple ending model ----------------------------------------------------
quick_find   :- chosen_method(M), speed(M, 1).
careful_find :- chosen_method(M), speed(M, 2).

outcome(quick_find)   :- quick_find.
outcome(careful_find) :- careful_find.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        for zone in sorted(site.zones):
            lines.append(asp.fact("site_zone", site_id, zone))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("zone", item_id, item.zone))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for zone in sorted(clue.points_to):
            lines.append(asp.fact("points_to", clue_id, zone))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for zone in sorted(helper.covers):
            lines.append(asp.fact("covers", helper_id, zone))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("speed", method_id, method.speed))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_method", params.method)
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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Rhyming construction-site mystery storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--site", choices=sorted(SITES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--seeker-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))

    if args.item and args.clue and args.helper:
        item = ITEMS[args.item]
        clue = CLUES[args.clue]
        helper = HELPERS[args.helper]
        if not clue_matches(item, clue) or not helper_can_reach(item, helper):
            raise StoryError(explain_combo_rejection(item, clue, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.site is None or combo[0] == args.site)
        and (args.item is None or combo[1] == args.item)
        and (args.clue is None or combo[2] == args.clue)
        and (args.helper is None or combo[3] == args.helper)
        and (args.method is None or combo[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site_id, item_id, clue_id, helper_id, method_id = rng.choice(combos)
    seeker_name, seeker_gender = pick_child(rng)
    friend_name, friend_gender = pick_child(rng, avoid=seeker_name)
    return StoryParams(
        site=site_id,
        item=item_id,
        clue=clue_id,
        helper=helper_id,
        method=method_id,
        seeker_name=args.seeker_name or seeker_name,
        seeker_gender=seeker_gender,
        friend_name=args.friend_name or friend_name,
        friend_gender=friend_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        seeker_trait=rng.choice(TRAITS),
        friend_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.site not in SITES:
        raise StoryError(f"(Unknown site: {params.site})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))
    if not clue_matches(ITEMS[params.item], CLUES[params.clue]) or not helper_can_reach(ITEMS[params.item], HELPERS[params.helper]):
        raise StoryError(explain_combo_rejection(ITEMS[params.item], CLUES[params.clue], HELPERS[params.helper]))

    world = tell(
        site=SITES[params.site],
        item=ITEMS[params.item],
        clue=CLUES[params.clue],
        helper=HELPERS[params.helper],
        method=METHODS[params.method],
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
    )
    world.get("seeker").traits.append(params.seeker_trait)
    world.get("friend").traits.append(params.friend_trait)

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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (site, item, clue, helper, method) combos:\n")
        for site_id, item_id, clue_id, helper_id, method_id in combos:
            print(f"  {site_id:11} {item_id:11} {clue_id:12} {helper_id:9} {method_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.seeker_name} and {p.friend_name}: {p.item} at {p.site} "
                f"({p.clue}, {p.helper}, {p.method}, {outcome_of(p)})"
            )
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
