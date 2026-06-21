#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/icicle_bizarre_heel_farmyard_cautionary_suspense_happy.py
=====================================================================================

A standalone storyworld for a winter farmyard adventure: two children hurry
toward a small goal, notice a strange hanging icicle, and face a cautionary
choice about whether to rush past it or meddle with it. The model keeps both
physical meters and emotional memes, uses a tiny forward-chaining rule engine,
includes a Python reasonableness gate plus an ASP twin, and renders complete
TinyStories-style tales with suspense and a happy ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/icicle_bizarre_heel_farmyard_cautionary_suspense_happy.py
    python storyworlds/worlds/gpt-5.4/icicle_bizarre_heel_farmyard_cautionary_suspense_happy.py --goal egg_basket --hazard coop_eave
    python storyworlds/worlds/gpt-5.4/icicle_bizarre_heel_farmyard_cautionary_suspense_happy.py --goal red_wagon --hazard coop_eave
    python storyworlds/worlds/gpt-5.4/icicle_bizarre_heel_farmyard_cautionary_suspense_happy.py --response grab_by_hand
    python storyworlds/worlds/gpt-5.4/icicle_bizarre_heel_farmyard_cautionary_suspense_happy.py --all
    python storyworlds/worlds/gpt-5.4/icicle_bizarre_heel_farmyard_cautionary_suspense_happy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/icicle_bizarre_heel_farmyard_cautionary_suspense_happy.py --verify
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
# This file lives one level deeper than most worlds (storyworlds/worlds/gpt-5.4/),
# so we add storyworlds/ itself to the import path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
NERVE_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Goal:
    id: str
    label: str
    phrase: str
    place: str
    route_site: str
    adventure_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    the: str
    site: str
    where: str
    size: int
    weird: str
    base_danger: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    mild_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "friend"}]

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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    lead = world.get("lead")
    yard = world.get("yard")
    if lead.meters["rushing"] < THRESHOLD:
        return out
    if yard.meters["slick"] < THRESHOLD:
        return out
    sig = ("slip", "lead")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lead.meters["slipped"] += 1
    lead.meters["under_hazard"] += 1
    lead.meters["heel_scuff"] += 1
    lead.memes["fear"] += 1
    yard.meters["danger"] += 1
    out.append("__slip__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    hazard = world.get("hazard")
    lead = world.get("lead")
    if hazard.meters["cracked"] < THRESHOLD:
        return out
    sig = ("fall", "hazard")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hazard.meters["falling"] += 1
    world.get("yard").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    if lead.meters["under_hazard"] >= THRESHOLD:
        lead.meters["close_call"] += 1
    out.append("__fall__")
    return out


CAUSAL_RULES = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="fall", tag="physical", apply=_r_fall),
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
        for sent in produced:
            world.say(sent)
    return produced


GOALS = {
    "egg_basket": Goal(
        id="egg_basket",
        label="egg basket",
        phrase="a little basket for the morning eggs",
        place="the coop door",
        route_site="coop",
        adventure_line="They called it the winter egg mission.",
        ending_line="Soon they were carrying the eggs back carefully, as proud as explorers.",
        tags={"eggs", "farmyard"},
    ),
    "red_wagon": Goal(
        id="red_wagon",
        label="red wagon",
        phrase="their red wagon with one rattly wheel",
        place="the barn door",
        route_site="barn",
        adventure_line="They said they were rescuing a wagon before the snow gobbled it up.",
        ending_line="A minute later the wagon bumped along the path behind them, safe and bright.",
        tags={"wagon", "farmyard"},
    ),
    "hay_scarf": Goal(
        id="hay_scarf",
        label="striped scarf",
        phrase="a striped scarf that had blown into the hay loft",
        place="the loft ladder",
        route_site="loft",
        adventure_line="They whispered that it was a hill-climbing rescue mission.",
        ending_line="Soon the striped scarf fluttered from a pocket, rescued at last.",
        tags={"scarf", "farmyard"},
    ),
}

HAZARDS = {
    "coop_eave": Hazard(
        id="coop_eave",
        label="icicle",
        the="the icicle",
        site="coop",
        where="above the coop door",
        size=2,
        weird="long and a little bizarre, with blue light folded inside it",
        base_danger=2,
        tags={"icicle", "ice", "farmyard"},
    ),
    "barn_eave": Hazard(
        id="barn_eave",
        label="icicle",
        the="the icicle",
        site="barn",
        where="from the barn roof",
        size=3,
        weird="thick and bizarre, like a glass horn hanging over the path",
        base_danger=3,
        tags={"icicle", "ice", "farmyard"},
    ),
    "loft_eave": Hazard(
        id="loft_eave",
        label="icicle",
        the="the icicle",
        site="loft",
        where="beside the loft ladder",
        size=2,
        weird="crooked and bizarre, with three sharp points like frozen fingers",
        base_danger=2,
        tags={"icicle", "ice", "farmyard"},
    ),
}

RESPONSES = {
    "hook_pole": Response(
        id="hook_pole",
        sense=3,
        power=4,
        text="snatched up the long hook pole, swept the child back, and knocked the icicle down into a soft hay pile from the side",
        mild_text="used the long hook pole from the side and brought the icicle down safely into the hay",
        qa_text="used the long hook pole from the side and knocked the icicle safely into the hay",
        tags={"hook_pole", "call_adult", "ice"},
    ),
    "grain_shovel": Response(
        id="grain_shovel",
        sense=2,
        power=3,
        text="pulled the child by the coat and tipped the falling ice aside with a grain shovel so it shattered away from small boots",
        mild_text="kept everyone back and used a grain shovel to tip the ice away from the path",
        qa_text="pulled the child back and tipped the falling ice away with a grain shovel",
        tags={"grain_shovel", "call_adult", "ice"},
    ),
    "grab_by_hand": Response(
        id="grab_by_hand",
        sense=1,
        power=1,
        text="reached with bare hands for the falling ice",
        mild_text="tried to snatch the ice with bare hands",
        qa_text="tried to catch the falling ice with bare hands",
        tags={"call_adult"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "steady", "curious", "brave", "sensible"]
PETS = ["the calf", "the little goat", "the farm dog", "the pony"]


@dataclass
class StoryParams:
    goal: str
    hazard: str
    response: str
    lead: str
    lead_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    delay: int = 0
    lead_age: int = 6
    friend_age: int = 5
    relation: str = "siblings"
    trust: int = 6
    pet: str = ""
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        goal="egg_basket",
        hazard="coop_eave",
        response="hook_pole",
        lead="Tom",
        lead_gender="boy",
        friend="Lily",
        friend_gender="girl",
        parent="father",
        trait="careful",
        delay=0,
        lead_age=5,
        friend_age=7,
        relation="siblings",
        trust=4,
        pet="the little goat",
    ),
    StoryParams(
        goal="red_wagon",
        hazard="barn_eave",
        response="grain_shovel",
        lead="Mia",
        lead_gender="girl",
        friend="Ben",
        friend_gender="boy",
        parent="mother",
        trait="curious",
        delay=0,
        lead_age=6,
        friend_age=6,
        relation="friends",
        trust=5,
        pet="the farm dog",
    ),
    StoryParams(
        goal="hay_scarf",
        hazard="loft_eave",
        response="hook_pole",
        lead="Sam",
        lead_gender="boy",
        friend="Zoe",
        friend_gender="girl",
        parent="father",
        trait="steady",
        delay=1,
        lead_age=7,
        friend_age=5,
        relation="siblings",
        trust=7,
        pet="the pony",
    ),
    StoryParams(
        goal="red_wagon",
        hazard="barn_eave",
        response="hook_pole",
        lead="Ava",
        lead_gender="girl",
        friend="Ella",
        friend_gender="girl",
        parent="mother",
        trait="cautious",
        delay=0,
        lead_age=5,
        friend_age=8,
        relation="siblings",
        trust=3,
        pet="the calf",
    ),
]


def route_matches(goal: Goal, hazard: Hazard) -> bool:
    return goal.route_site == hazard.site


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, lead_age: int, friend_age: int, trait: str) -> bool:
    older_friend = relation == "siblings" and friend_age > lead_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older_friend else 0.0)
    return older_friend and authority > NERVE_INIT


def danger_score(hazard: Hazard, delay: int) -> int:
    return hazard.base_danger + delay


def is_strong_enough(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= danger_score(hazard, delay)


def explain_rejection(goal: Goal, hazard: Hazard) -> str:
    return (
        f"(No story: {goal.phrase} is reached by the {goal.route_site} path, "
        f"but {hazard.the} hangs at the {hazard.site} path. The danger must sit "
        f"on the same route as the goal, or the warning would not make sense.)"
    )


def explain_response(rid: str) -> str:
    resp = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={resp.sense} < {SENSE_MIN}). Try a safer farmyard response like {better}.)"
    )


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for goal_id, goal in GOALS.items():
        for hazard_id, hazard in HAZARDS.items():
            if route_matches(goal, hazard):
                combos.append((goal_id, hazard_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.lead_age, params.friend_age, params.trait):
        return "averted"
    response = RESPONSES[params.response]
    hazard = HAZARDS[params.hazard]
    return "rescued" if is_strong_enough(response, hazard, params.delay) else "startled"


def predict_danger(world: World) -> dict:
    sim = world.copy()
    lead = sim.get("lead")
    hazard = sim.get("hazard")
    lead.meters["rushing"] += 1
    lead.meters["under_hazard"] += 1
    hazard.meters["cracked"] += 1
    propagate(sim, narrate=False)
    return {
        "falling": hazard.meters["falling"] >= THRESHOLD,
        "danger": sim.get("yard").meters["danger"],
        "close_call": lead.meters["close_call"] >= THRESHOLD,
    }


def introduce(world: World, lead: Entity, friend: Entity, goal: Goal) -> None:
    for kid in (lead, friend):
        kid.memes["joy"] += 1
        kid.memes["adventure"] += 1
    world.say(
        f"On a bright winter morning, {lead.id} and {friend.id} ran into the farmyard as if it were a map full of secret places."
    )
    world.say(goal.adventure_line)
    world.say(
        f"They wanted to reach {goal.phrase} by {goal.place}, and the frost on the fences made the whole yard sparkle."
    )


def spot_hazard(world: World, hazard: Hazard, pet: str) -> None:
    extra = f" Even {pet} stopped and stared." if pet else ""
    world.say(
        f"But hanging {hazard.where} was {hazard.weird}, a giant icicle that looked lovely and dangerous all at once.{extra}"
    )


def tempt(world: World, lead: Entity, goal: Goal, hazard: Hazard) -> None:
    lead.memes["bravado"] += 1
    world.say(
        f'"If I hurry, I can slip past {hazard.the} and get the {goal.label} first," {lead.id} said.'
    )
    world.say("For one breath, the quick way felt more exciting than the safe way.")


def warn(world: World, friend: Entity, lead: Entity, hazard: Hazard, parent: Entity) -> None:
    pred = predict_danger(world)
    friend.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["close_call"]:
        extra = " The thought of it made the path feel suddenly sharp and narrow."
    world.say(
        f'{friend.id} looked up at {hazard.the} and shook {friend.pronoun("possessive")} head. '
        f'"No, {lead.id}. That icicle could crack and fall. Let\'s call {parent.label_word} instead."{extra}'
    )


def back_down(world: World, lead: Entity, friend: Entity, parent: Entity, hazard: Hazard, response: Response) -> None:
    lead.memes["relief"] += 1
    friend.memes["relief"] += 1
    lead.memes["lesson"] += 1
    world.say(
        f'{lead.id} looked at the ice again, then at {friend.id}, and the brave face slid away. "You\'re right," {lead.pronoun()} said.'
    )
    world.say(
        f"{parent.label_word.capitalize()} came over, {response.mild_text}, and waved the children to the side path."
    )
    world.get("hazard").meters["fallen_safe"] += 1
    world.get("yard").meters["danger"] = 0.0


def rush(world: World, lead: Entity) -> None:
    lead.meters["rushing"] += 1
    propagate(world, narrate=False)
    if lead.meters["slipped"] >= THRESHOLD:
        world.say(
            f"But the frozen ground was slick. {lead.id}'s boot heel skidded, and {lead.pronoun()} slid right under the hanging ice."
        )
    else:
        world.say(f"{lead.id} darted forward across the crunchy ground.")


def poke(world: World, lead: Entity, hazard: Hazard) -> None:
    lead.meters["under_hazard"] += 1
    hazard_ent = world.get("hazard")
    hazard_ent.meters["cracked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{lead.id} reached up with a stick and tapped {hazard.the}. A tiny crack whispered through the ice."
    )


def crack_and_fall(world: World, hazard: Hazard) -> None:
    hazard_ent = world.get("hazard")
    if hazard_ent.meters["cracked"] < THRESHOLD:
        hazard_ent.meters["cracked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came a brittle sound -- tick... tick... crack! {hazard.The} broke loose and dropped."
    )


def alarm(world: World, friend: Entity, lead: Entity, parent: Entity) -> None:
    world.say(f'"{lead.id}, move!" {friend.id} cried.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, hazard: Hazard, lead: Entity) -> None:
    world.get("yard").meters["danger"] = 0.0
    world.get("hazard").meters["falling"] = 0.0
    world.get("hazard").meters["fallen_safe"] += 1
    lead.meters["under_hazard"] = 0.0
    lead.memes["relief"] += 1
    world.say(f"{parent.label_word.capitalize()} came running and {response.text}.")
    world.say(
        "The ice burst in a glittering crash, but not one sharp piece touched the children."
    )


def startled_escape(world: World, parent: Entity, response: Response, hazard: Hazard, lead: Entity) -> None:
    world.get("yard").meters["danger"] = 0.0
    world.get("hazard").meters["falling"] = 0.0
    world.get("hazard").meters["fallen_safe"] += 1
    lead.meters["under_hazard"] = 0.0
    lead.meters["slush_splashed"] += 1
    lead.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} lunged for {lead.id} while the ice smashed down so close that slush jumped over {lead.pronoun('possessive')} boots."
    )
    world.say(
        f"It missed, though only by a little. {response.mild_text}, and everyone backed away with shaking knees."
    )


def lesson(world: World, parent: Entity, lead: Entity, friend: Entity) -> None:
    for kid in (lead, friend):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} knelt in the straw and hugged them both. "
        f'"Beautiful things can still be dangerous," {parent.pronoun()} said softly. '
        f'"When ice hangs low, you stop, step back, and call a grown-up."'
    )


def safe_finish(world: World, lead: Entity, friend: Entity, parent: Entity, goal: Goal, pet: str) -> None:
    for kid in (lead, friend):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    pet_line = f" {pet.capitalize()} trotted after them." if pet else ""
    world.say(
        f"Then they took the long path together, with {parent.label_word} leading and the dangerous spot behind them.{pet_line}"
    )
    world.say(goal.ending_line)


def tell(
    goal: Goal,
    hazard: Hazard,
    response: Response,
    lead_name: str = "Tom",
    lead_gender: str = "boy",
    friend_name: str = "Lily",
    friend_gender: str = "girl",
    parent_type: str = "father",
    trait: str = "careful",
    delay: int = 0,
    lead_age: int = 6,
    friend_age: int = 5,
    relation: str = "siblings",
    trust: int = 6,
    pet: str = "",
) -> World:
    world = World()
    lead = world.add(
        Entity(
            id="lead",
            kind="character",
            type=lead_gender,
            label=lead_name,
            phrase=lead_name,
            role="lead",
            age=lead_age,
            attrs={"name": lead_name, "relation": relation},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type=friend_gender,
            label=friend_name,
            phrase=friend_name,
            role="friend",
            age=friend_age,
            traits=[trait],
            attrs={"name": friend_name, "relation": relation, "trust": trust},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            phrase="the parent",
            role="parent",
        )
    )
    world.add(Entity(id="yard", type="yard", label="farmyard"))
    hz = world.add(
        Entity(
            id="hazard",
            type="icicle",
            label=hazard.label,
            phrase=hazard.the,
            tags=set(hazard.tags),
        )
    )
    lead.memes["nerve"] = NERVE_INIT
    friend.memes["caution"] = initial_caution(trait)
    friend.memes["trust"] = float(trust)
    world.get("yard").meters["slick"] = 1.0

    world.facts["pet"] = pet
    world.facts["relation"] = relation
    world.facts["delay"] = delay

    introduce(world, lead, friend, goal)
    spot_hazard(world, hazard, pet)

    world.para()
    tempt(world, lead, goal, hazard)
    warn(world, friend, lead, hazard, parent)

    averted = would_avert(relation, lead_age, friend_age, trait)
    if averted:
        back_down(world, lead, friend, parent, hazard, response)
        world.para()
        lesson(world, parent, lead, friend)
        safe_finish(world, lead, friend, parent, goal, pet)
        outcome = "averted"
    else:
        world.say(
            f'"I\'ll be quick," {lead_name} said, and before anyone could stop {lead.pronoun("object")}, {lead.pronoun()} moved.'
        )
        world.para()
        if goal.route_site == "barn":
            rush(world, lead)
        else:
            poke(world, lead, hazard)
        if delay > 0:
            world.get("hazard").meters["cracked"] += 1
        crack_and_fall(world, hazard)
        alarm(world, friend, lead, parent)

        world.para()
        if is_strong_enough(response, hazard, delay):
            rescue(world, parent, response, hazard, lead)
            outcome = "rescued"
        else:
            startled_escape(world, parent, response, hazard, lead)
            outcome = "startled"
        lesson(world, parent, lead, friend)

        world.para()
        safe_finish(world, lead, friend, parent, goal, pet)

    world.facts.update(
        goal=goal,
        hazard_cfg=hazard,
        response=response,
        lead=lead,
        friend=friend,
        parent=parent,
        lead_name=lead_name,
        friend_name=friend_name,
        outcome=outcome,
        close_call=lead.meters["close_call"] >= THRESHOLD or lead.meters["slipped"] >= THRESHOLD,
        slipped=lead.meters["slipped"] >= THRESHOLD,
        heel_scuff=lead.meters["heel_scuff"] >= THRESHOLD,
        pet=pet,
    )
    return world


KNOWLEDGE = {
    "icicle": [
        (
            "What is an icicle?",
            "An icicle is a long piece of ice that forms when dripping water freezes. It can look pretty, but a big one can be heavy and dangerous."
        )
    ],
    "ice": [
        (
            "Why can icy ground be slippery?",
            "A thin layer of ice is smooth, so shoes cannot grip it well. That is why feet or heels can slide suddenly."
        )
    ],
    "heel": [
        (
            "What is the heel of a boot?",
            "The heel is the back bottom part of a boot or shoe. If the heel slides on ice, a person can lose balance."
        )
    ],
    "call_adult": [
        (
            "What should a child do near a dangerous hanging thing?",
            "Step back and call a grown-up right away. A grown-up can decide the safest way to move it or go around it."
        )
    ],
    "farmyard": [
        (
            "What is a farmyard?",
            "A farmyard is the open space around barns, coops, and sheds on a farm. Animals, wagons, and tools are often nearby."
        )
    ],
    "hook_pole": [
        (
            "What is a hook pole used for on a farm?",
            "A hook pole is a long tool that lets a grown-up reach something from a safer distance. Using a long tool can keep hands and faces farther from danger."
        )
    ],
    "grain_shovel": [
        (
            "What is a grain shovel?",
            "A grain shovel is a broad farm shovel used for moving grain, straw, or other loose things. A grown-up can sometimes use a long shovel to push danger away from a path."
        )
    ],
    "eggs": [
        (
            "Why do farmers carry egg baskets carefully?",
            "Eggs have thin shells, so they crack easily. Carrying them carefully keeps them from breaking."
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon helps carry things from one place to another. On a farm, it can haul feed, straw, or tools."
        )
    ],
    "scarf": [
        (
            "Why might a scarf blow away on a windy day?",
            "A scarf is light cloth, so wind can catch it and lift it. That is why scarves sometimes flutter into fences or high places."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "farmyard",
    "icicle",
    "ice",
    "heel",
    "call_adult",
    "hook_pole",
    "grain_shovel",
    "eggs",
    "wagon",
    "scarf",
]


def pair_noun(lead: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if lead.type == "boy" and friend.type == "boy":
            return "two brothers"
        if lead.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    goal = f["goal"]
    hazard = f["hazard_cfg"]
    lead_name = f["lead_name"]
    friend_name = f["friend_name"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a short adventure story for a 3-to-5-year-old set in a farmyard that includes the words "icicle", "bizarre", and "heel".',
            f"Tell a suspenseful but gentle story where {lead_name} wants to hurry past a hanging icicle to reach {goal.phrase}, but {friend_name} stops the risk before anyone gets hurt.",
            f"Write a cautionary winter farm story with a happy ending where a bizarre icicle hangs {hazard.where}, a child listens in time, and the family chooses the long safe path.",
        ]
    return [
        'Write a short adventure story for a 3-to-5-year-old set in a farmyard that includes the words "icicle", "bizarre", and "heel".',
        f"Tell a cautionary story where {lead_name} makes a risky move near a hanging icicle while trying to reach {goal.phrase}, and a grown-up must help quickly.",
        f"Write a suspenseful farmyard story with a happy ending where a bizarre icicle cracks, someone cries out, and the children learn to step back and call for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    parent = f["parent"]
    goal = f["goal"]
    hazard = f["hazard_cfg"]
    response = f["response"]
    relation = f.get("relation", "friends")
    pair = pair_noun(lead, friend, relation)
    lead_name = f["lead_name"]
    friend_name = f["friend_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {lead_name} and {friend_name}, in a winter farmyard. {parent.label_word.capitalize()} helps them when the danger shows itself."
        ),
        (
            "What were they trying to reach?",
            f"They were trying to reach {goal.phrase} by {goal.place}. That small farmyard mission is what made the quick path feel tempting."
        ),
        (
            "Why did the path become dangerous?",
            f"The path was dangerous because a big hanging icicle was right over it. It looked beautiful in a bizarre way, but it could crack and fall."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"Why did {lead_name} stop before going under the icicle?",
                f"{friend_name} warned that the icicle could fall, and {lead_name} listened. That choice changed the whole story, because the danger stayed only a warning instead of becoming an accident."
            )
        )
    else:
        move_answer = f"{lead_name} made a risky move near the ice, and then the suspense became real."
        if f.get("slipped"):
            move_answer += f" {lead_name}'s boot heel skidded on the icy ground, which put {lead.pronoun('object')} right under the hanging danger."
        else:
            move_answer += f" {lead_name} tapped the icicle, and that little poke helped crack it loose."
        qa.append((f"What made the scary moment start?", move_answer))
        if f["outcome"] == "rescued":
            qa.append(
                (
                    f"How did {parent.label_word} help?",
                    f"{parent.label_word.capitalize()} {response.qa_text}. That fast, sensible action turned a falling danger into a safe ending."
                )
            )
        else:
            qa.append(
                (
                    f"Did the icicle hit anyone?",
                    f"No, but it came down very close. Slush splashed near the boots, which scared everyone and showed how narrow the miss had been."
                )
            )
    qa.append(
        (
            "What did they learn at the end?",
            "They learned that something pretty can still be dangerous. When they see hanging ice, they should stop, step back, and call a grown-up."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily: they took the longer safe path together and still finished their little adventure. The ending image proves what changed, because they reached the goal without rushing into danger."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["goal"].tags) | set(f["hazard_cfg"].tags) | {"heel", "call_adult"}
    if f["response"].id in {"hook_pole", "grain_shovel"}:
        tags.add(f["response"].id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(G, H) :- goal(G), hazard(H), route(G, S), site(H, S).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_friend :- relation(siblings), lead_age(LA), friend_age(FA), FA > LA.
bonus(4) :- older_friend.
bonus(0) :- not older_friend.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_friend, authority(A), nerve_init(N), A > N.

danger(D) :- chosen_hazard(H), base_danger(H, B), delay(X), D = B + X.
rescued :- chosen_response(R), power(R, P), danger(D), P >= D.

outcome(averted) :- averted.
outcome(rescued) :- not averted, rescued.
outcome(startled) :- not averted, not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("route", gid, goal.route_site))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("site", hid, hazard.site))
        lines.append(asp.fact("base_danger", hid, hazard.base_danger))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("nerve_init", int(NERVE_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("lead_age", params.lead_age),
            asp.fact("friend_age", params.friend_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sens, python_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    # Smoke-test ordinary generation and serialization.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story during verify")
        sample.to_json()
        print("OK: smoke test generated a normal story and JSON output.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a winter farmyard adventure with a hanging icicle, suspense, and a happy ending."
    )
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the danger gets before the grown-up reaches it")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and args.hazard:
        goal = GOALS[args.goal]
        hazard = HAZARDS[args.hazard]
        if not route_matches(goal, hazard):
            raise StoryError(explain_rejection(goal, hazard))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.goal is None or combo[0] == args.goal)
        and (args.hazard is None or combo[1] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goal_id, hazard_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    lead_name, lead_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=lead_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    lead_age, friend_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(0, 10)
    pet = rng.choice(PETS + ["", ""])

    return StoryParams(
        goal=goal_id,
        hazard=hazard_id,
        response=response_id,
        lead=lead_name,
        lead_gender=lead_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        lead_age=lead_age,
        friend_age=friend_age,
        relation=relation,
        trust=trust,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        goal = GOALS[params.goal]
        hazard = HAZARDS[params.hazard]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not route_matches(goal, hazard):
        raise StoryError(explain_rejection(goal, hazard))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        goal=goal,
        hazard=hazard,
        response=response,
        lead_name=params.lead,
        lead_gender=params.lead_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        lead_age=params.lead_age,
        friend_age=params.friend_age,
        relation=params.relation,
        trust=params.trust,
        pet=params.pet,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (goal, hazard) combos:\n")
        for goal_id, hazard_id in combos:
            print(f"  {goal_id:11} {hazard_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.lead} & {p.friend}: {p.goal} by {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
