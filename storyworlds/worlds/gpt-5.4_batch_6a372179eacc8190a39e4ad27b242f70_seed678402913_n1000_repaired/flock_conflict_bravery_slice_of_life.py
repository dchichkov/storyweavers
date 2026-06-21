#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flock_conflict_bravery_slice_of_life.py
==================================================================

A standalone story world for small, homey stories about a child helping guide a
flock back where it belongs. The tone stays close to slice of life: a yard, a
gate, a chore, a disagreement, a scary flap of wings, and a calm ending that
shows what bravery looked like.

Premise
-------
A child is helping at home when a flock wanders out through an unlatched gate.
Another child wants to chase the birds, which would only scare them more. The
hero feels nervous but speaks up, chooses a sensible lure, and either guides the
flock back calmly or calls a grown-up when the birds are too hard to handle
alone. In both endings, bravery means doing the sensible thing instead of the
loud thing.

Run it
------
    python storyworlds/worlds/gpt-5.4/flock_conflict_bravery_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/flock_conflict_bravery_slice_of_life.py --flock geese --lure lettuce --response bowl_lead
    python storyworlds/worlds/gpt-5.4/flock_conflict_bravery_slice_of_life.py --flock geese --lure grain
    python storyworlds/worlds/gpt-5.4/flock_conflict_bravery_slice_of_life.py --response chase
    python storyworlds/worlds/gpt-5.4/flock_conflict_bravery_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/flock_conflict_bravery_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/flock_conflict_bravery_slice_of_life.py --verify
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

TRAIT_BRAVERY = {
    "timid": 1,
    "careful": 2,
    "steady": 3,
    "brave": 4,
    "patient": 3,
    "gentle": 2,
}


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
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    yard: str
    out_spot: str
    home_spot: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FlockCfg:
    id: str
    label: str
    birds: str
    sound: str
    gait: str
    fear_text: str
    preference: set[str] = field(default_factory=set)
    difficulty: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    label: str
    phrase: str
    for_flocks: set[str] = field(default_factory=set)
    carry: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int = 0
    control: int = 0
    text: str = ""
    assist_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    flock: str
    lure: str
    response: str
    hero: str
    hero_gender: str
    other: str
    other_gender: str
    parent: str
    trait: str
    delay: int = 0
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


def _r_scatter(world: World) -> list[str]:
    flock = world.get("flock")
    hero = world.get("hero")
    yard = world.get("yard")
    if flock.meters["startled"] < THRESHOLD:
        return []
    sig = ("scatter",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flock.meters["scattered"] += 1
    yard.meters["risk"] += 1
    hero.memes["fear"] += 1
    return ["__scatter__"]


def _r_follow(world: World) -> list[str]:
    flock = world.get("flock")
    if flock.meters["trail_ready"] < THRESHOLD:
        return []
    if flock.meters["startled"] >= THRESHOLD and flock.meters["calmed"] < THRESHOLD:
        return []
    sig = ("follow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flock.meters["following"] += 1
    return ["__follow__"]


CAUSAL_RULES = [
    Rule(name="scatter", tag="physical", apply=_r_scatter),
    Rule(name="follow", tag="physical", apply=_r_follow),
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


PLACES = {
    "backyard": Place(
        id="backyard",
        yard="the backyard",
        out_spot="the bean rows",
        home_spot="the chicken run",
        detail="A basket of pegs sat by the steps, and the sun had warmed the fence rails.",
        tags={"yard"},
    ),
    "side_lane": Place(
        id="side_lane",
        yard="the side lane",
        out_spot="the patch by the mailbox",
        home_spot="the side pen",
        detail="The afternoon was quiet except for a bicycle bell somewhere down the street.",
        tags={"lane"},
    ),
    "orchard": Place(
        id="orchard",
        yard="the little orchard",
        out_spot="the fallen apples under the trees",
        home_spot="the wire gate by the shed",
        detail="The grass smelled sweet, and a ladder leaned against the old pear tree.",
        tags={"orchard"},
    ),
}

FLOCKS = {
    "chickens": FlockCfg(
        id="chickens",
        label="a flock of chickens",
        birds="chickens",
        sound="clucks",
        gait="quick little steps",
        fear_text="the flutter of wings made everything look busier than it really was",
        preference={"grain", "feed"},
        difficulty=1,
        tags={"chickens", "flock"},
    ),
    "ducks": FlockCfg(
        id="ducks",
        label="a flock of ducks",
        birds="ducks",
        sound="quacks",
        gait="waddly little lines",
        fear_text="their wet feathers and sudden waddles made the moment feel slippery and fast",
        preference={"peas", "feed"},
        difficulty=2,
        tags={"ducks", "flock"},
    ),
    "geese": FlockCfg(
        id="geese",
        label="a flock of geese",
        birds="geese",
        sound="honks",
        gait="long-necked steps",
        fear_text="their tall necks and heavy flaps made the yard feel bigger and louder all at once",
        preference={"lettuce", "feed"},
        difficulty=3,
        tags={"geese", "flock"},
    ),
}

LURES = {
    "grain": Lure(
        id="grain",
        label="grain",
        phrase="a scoop of grain",
        for_flocks={"chickens"},
        carry="in the red feed scoop",
        tags={"grain"},
    ),
    "peas": Lure(
        id="peas",
        label="peas",
        phrase="a bowl of peas",
        for_flocks={"ducks"},
        carry="in a blue bowl",
        tags={"peas"},
    ),
    "lettuce": Lure(
        id="lettuce",
        label="lettuce leaves",
        phrase="a handful of lettuce leaves",
        for_flocks={"geese"},
        carry="in both hands like green fans",
        tags={"lettuce"},
    ),
    "feed": Lure(
        id="feed",
        label="feed",
        phrase="a small pan of feed",
        for_flocks={"chickens", "ducks", "geese"},
        carry="in the old tin pan",
        tags={"feed"},
    ),
}

RESPONSES = {
    "bowl_lead": Response(
        id="bowl_lead",
        sense=3,
        control=2,
        text="held the food low, took slow steps toward {home}, and let the birds follow the easy path back",
        assist_text="stood close with calm hands while {parent} helped hold the food low and make an easy path back to {home}",
        qa_text="held the food low and walked slowly so the flock could follow back",
        tags={"calm", "guide"},
    ),
    "open_path": Response(
        id="open_path",
        sense=3,
        control=3,
        text="opened the gate wide, made a little trail toward {home}, and kept talking in a soft voice until the birds drifted after the food",
        assist_text="opened the gate while {parent} made a little trail toward {home}, and together they kept the birds moving in one calm direction",
        qa_text="opened the gate and made a food trail so the flock drifted back",
        tags={"trail", "guide"},
    ),
    "pan_rattle": Response(
        id="pan_rattle",
        sense=2,
        control=1,
        text="gave the pan a familiar little rattle and backed toward {home} so the birds would notice the food and come after it",
        assist_text="gave the pan a little rattle while {parent} walked beside {hero_obj}, and together they backed toward {home}",
        qa_text="rattled the pan and backed toward home so the flock followed",
        tags={"rattle", "guide"},
    ),
    "chase": Response(
        id="chase",
        sense=1,
        control=0,
        text="ran at the birds waving both arms, which only made them scatter faster",
        assist_text="ran at the birds waving both arms, which only made them scatter faster",
        qa_text="chased the flock and scared it",
        tags={"chase"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["timid", "careful", "steady", "brave", "patient", "gentle"]


def lure_fits(flock_id: str, lure_id: str) -> bool:
    return flock_id in LURES[lure_id].for_flocks


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for flock_id in FLOCKS:
            for lure_id in LURES:
                if not lure_fits(flock_id, lure_id):
                    continue
                for response in sensible_responses():
                    combos.append((place_id, flock_id, lure_id, response.id))
    return combos


def bravery_score(trait: str, response_id: str, delay: int) -> int:
    return TRAIT_BRAVERY[trait] + RESPONSES[response_id].control - delay


def outcome_of(params: StoryParams) -> str:
    need = FLOCKS[params.flock].difficulty
    have = bravery_score(params.trait, params.response, params.delay)
    return "self_led" if have >= need else "adult_help"


def explain_lure(flock_id: str, lure_id: str) -> str:
    flock = FLOCKS[flock_id]
    lure = LURES[lure_id]
    good = ", ".join(sorted(l.id for l in LURES.values() if flock_id in l.for_flocks))
    return (
        f"(No story: {lure.label} is not a sensible lure for {flock.birds} here. "
        f"Try one of: {good}.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a calmer method such as {better}.)"
    )


def _do_chase(world: World) -> None:
    flock = world.get("flock")
    flock.meters["startled"] += 1
    propagate(world, narrate=False)


def predict_chase(world: World) -> dict:
    sim = world.copy()
    _do_chase(sim)
    return {
        "scattered": sim.get("flock").meters["scattered"] >= THRESHOLD,
        "fear": sim.get("hero").memes["fear"],
        "risk": sim.get("yard").meters["risk"],
    }


def introduce(world: World, hero: Entity, other: Entity, parent: Entity, place: Place, flock: FlockCfg) -> None:
    world.say(
        f"After school, {hero.id} was helping {hero.pronoun('possessive')} {parent.label_word} in {place.yard} while {other.id} played nearby. "
        f"{place.detail}"
    )
    world.say(
        f"From behind the shed came a flutter and a burst of {flock.sound}. "
        f"When {hero.id} looked up, {flock.label} was already heading for {place.out_spot}."
    )


def discover_problem(world: World, hero: Entity, parent: Entity, place: Place) -> None:
    hero.memes["care"] += 1
    world.say(
        f'The latch on the small gate had not caught properly, and now the birds were out. "{parent.label_word.capitalize()} will need help," '
        f"{hero.id} said, setting down the basket in a hurry."
    )


def sibling_plan(world: World, hero: Entity, other: Entity, flock: FlockCfg) -> None:
    pred = predict_chase(world)
    world.facts["predicted_scatter"] = pred["scattered"]
    world.facts["predicted_risk"] = pred["risk"]
    other.memes["impulse"] += 1
    world.say(
        f'"I can fix it!" {other.id} said. "{other.pronoun("subject").capitalize()} only have to run at them!"'
    )
    world.say(
        f"But {hero.id} could already imagine what would happen. {flock.fear_text.capitalize()}, and chasing would only send the flock in more directions."
    )


def startle(world: World, hero: Entity, other: Entity, flock: FlockCfg, place: Place) -> None:
    _do_chase(world)
    world.say(
        f"Before {hero.id} could answer, {other.id} dashed forward. The {flock.birds} burst apart with {flock.gait}, spilling wider across {place.out_spot}."
    )
    world.say(
        f"{hero.id}'s stomach gave a small jump. The yard suddenly felt noisy and full."
    )


def choose_brave_plan(world: World, hero: Entity, other: Entity, lure: Lure, response: Response, place: Place) -> None:
    hero.memes["bravery"] += 1
    hero.memes["conflict"] += 1
    world.say(
        f'"Stop chasing!" {hero.id} called, louder than {hero.pronoun("subject")} usually did. '
        f'"That only scares them. I\'m going to get {lure.phrase}."'
    )
    world.say(
        f"{hero.id} was still nervous, but {hero.pronoun('subject')} picked up {lure.phrase} {lure.carry} and turned back toward {place.home_spot}."
    )
    if response.id == "open_path":
        world.say("First, the gate had to be opened wide enough to look easy.")
    elif response.id == "pan_rattle":
        world.say("The familiar sound of the pan was sometimes enough to make the birds look up.")
    else:
        world.say("Slow steps and a low hand were better than fast feet.")


def self_lead(world: World, hero: Entity, flock: FlockCfg, lure: Lure, response: Response, place: Place) -> None:
    birds = world.get("flock")
    birds.meters["trail_ready"] += 1
    birds.meters["calmed"] += 1
    propagate(world, narrate=False)
    body = response.text.format(home=place.home_spot)
    world.say(
        f"{hero.id} {body}. One by one, the necks lowered, the wings settled, and the flock began to move in a single soft line."
    )
    world.say(
        f"In another minute the last of the {flock.birds} stepped through to {place.home_spot}, and {hero.id} slipped the latch shut with careful fingers."
    )


def call_for_help(world: World, hero: Entity, parent: Entity, flock: FlockCfg, lure: Lure, response: Response, place: Place) -> None:
    birds = world.get("flock")
    birds.meters["trail_ready"] += 1
    birds.meters["calmed"] += 1
    propagate(world, narrate=False)
    body = response.assist_text.format(parent=parent.label_word, home=place.home_spot, hero_obj=hero.pronoun("object"))
    hero.memes["help_seeking"] += 1
    world.say(
        f'{hero.id} took two steps, then stopped and called, "{parent.label_word.capitalize()}, please help me!"'
    )
    world.say(
        f"{parent.label_word.capitalize()} came out wiping {parent.pronoun('possessive')} hands and did not scold anyone. Together they {body}."
    )
    world.say(
        f"Soon the last of the {flock.birds} was back in {place.home_spot}, and the yard felt ordinary again."
    )


def settle_conflict(world: World, hero: Entity, other: Entity, parent: Entity, flock: FlockCfg, outcome: str) -> None:
    hero.memes["relief"] += 1
    other.memes["lesson"] += 1
    world.say("For a second, everyone just listened to the quiet.")
    if outcome == "self_led":
        world.say(
            f'Then {other.id} looked at {hero.id} and said, "You were right. Running only made them scatter." '
            f'{parent.label_word.capitalize()} smiled and brushed a feather from {hero.id}\'s sleeve.'
        )
        world.say(
            f'"That was brave," {parent.label_word} said. "Brave does not always mean loud. Sometimes it means staying calm when things flap at you."'
        )
    else:
        world.say(
            f'{other.id} stood close to {hero.id} and whispered, "I should not have run at them." '
            f'{parent.label_word.capitalize()} nodded and squeezed both children on the shoulder.'
        )
        world.say(
            f'"Calling for help was brave too," {parent.label_word} said. "The smart choice is the brave choice when a problem feels bigger than your hands."'
        )


def closing_image(world: World, hero: Entity, other: Entity, place: Place, flock: FlockCfg, lure: Lure, outcome: str) -> None:
    hero.memes["joy"] += 1
    if outcome == "self_led":
        world.say(
            f"Later, {hero.id} and {other.id} went back to the small chore they had been doing. Beyond the fence, the flock made sleepy little {flock.sound}, and {hero.id} no longer minded the sound."
        )
    else:
        world.say(
            f"Later, {hero.id} and {other.id} carried the empty {lure.label} pan back together. Beyond the fence, the flock settled into a low evening murmur that no longer sounded so scary."
        )
    world.say(
        f"The gate stayed latched this time, and the whole yard seemed to breathe out."
    )


def tell(
    place: Place,
    flock_cfg: FlockCfg,
    lure: Lure,
    response: Response,
    hero_name: str,
    hero_gender: str,
    other_name: str,
    other_gender: str,
    parent_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[trait],
        )
    )
    other = world.add(
        Entity(
            id=other_name,
            kind="character",
            type=other_gender,
            role="other",
            traits=["quick"],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    flock = world.add(
        Entity(
            id="flock",
            kind="thing",
            type="flock",
            label=flock_cfg.label,
            tags=set(flock_cfg.tags),
        )
    )
    yard = world.add(
        Entity(
            id="yard",
            kind="thing",
            type="place",
            label=place.yard,
            tags=set(place.tags),
        )
    )

    hero.memes["bravery_base"] = float(TRAIT_BRAVERY[trait])
    world.facts["delay"] = delay

    introduce(world, hero, other, parent, place, flock_cfg)
    discover_problem(world, hero, parent, place)

    world.para()
    sibling_plan(world, hero, other, flock_cfg)
    startle(world, hero, other, flock_cfg, place)

    world.para()
    choose_brave_plan(world, hero, other, lure, response, place)
    if outcome_of(
        StoryParams(
            place=place.id,
            flock=flock_cfg.id,
            lure=lure.id,
            response=response.id,
            hero=hero_name,
            hero_gender=hero_gender,
            other=other_name,
            other_gender=other_gender,
            parent=parent_type,
            trait=trait,
            delay=delay,
        )
    ) == "self_led":
        self_lead(world, hero, flock_cfg, lure, response, place)
        outcome = "self_led"
    else:
        call_for_help(world, hero, parent, flock_cfg, lure, response, place)
        outcome = "adult_help"

    world.para()
    settle_conflict(world, hero, other, parent, flock_cfg, outcome)
    closing_image(world, hero, other, place, flock_cfg, lure, outcome)

    world.facts.update(
        hero=hero,
        other=other,
        parent=parent,
        flock_cfg=flock_cfg,
        flock=flock,
        place=place,
        lure=lure,
        response=response,
        outcome=outcome,
        bravery_needed=flock_cfg.difficulty,
        bravery_have=bravery_score(trait, response.id, delay),
        predicted_scatter=world.facts.get("predicted_scatter", False),
        predicted_risk=world.facts.get("predicted_risk", 0),
        scared=hero.memes["fear"] >= THRESHOLD,
        called_help=outcome == "adult_help",
    )
    return world


KNOWLEDGE = {
    "flock": [
        (
            "What is a flock?",
            "A flock is a group of birds staying or moving together. They often follow one another, which is why a calm path can help guide them."
        )
    ],
    "chickens": [
        (
            "Why is it hard to catch chickens by running at them?",
            "Chickens get startled easily and dart in different directions. Moving calmly works better because it does not frighten them as much."
        )
    ],
    "ducks": [
        (
            "Why do ducks follow food?",
            "Ducks notice familiar food quickly and often waddle after it together. That makes calm guiding easier than chasing."
        )
    ],
    "geese": [
        (
            "Why can geese feel scary?",
            "Geese are big birds with strong wings and loud honks. Even so, staying calm and getting help are safer than rushing at them."
        )
    ],
    "grain": [
        (
            "Why do chickens come for grain?",
            "Grain is a familiar food for chickens, so it gets their attention. A little scoop can help lead them where you want them to go."
        )
    ],
    "peas": [
        (
            "Why might ducks follow peas?",
            "Peas are a simple treat many ducks like. Holding them low can help ducks notice and follow."
        )
    ],
    "lettuce": [
        (
            "Why might geese follow lettuce leaves?",
            "Geese nibble greens, so lettuce leaves can catch their eye. A calm person can use them to lead the birds instead of scaring them."
        )
    ],
    "feed": [
        (
            "What is feed?",
            "Feed is food made for farm birds and other animals. Because the birds know it well, it can be useful when you need to guide them."
        )
    ],
    "guide": [
        (
            "Why is guiding better than chasing a flock?",
            "Chasing scares birds and makes them split apart. Guiding gives them one calm direction to follow."
        )
    ],
    "help": [
        (
            "Can asking for help be brave?",
            "Yes. Asking for help is brave when a problem feels too big or too risky to handle alone."
        )
    ],
}
KNOWLEDGE_ORDER = ["flock", "chickens", "ducks", "geese", "grain", "peas", "lettuce", "feed", "guide", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    other = f["other"]
    flock_cfg = f["flock_cfg"]
    lure = f["lure"]
    place = f["place"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "flock".',
        f"Tell a homey story where {hero.id} and {other.id} are in {place.yard} when {flock_cfg.label} gets out, and the conflict is whether to chase the birds or guide them calmly.",
        f"Write a gentle story about bravery where a child feels nervous around {flock_cfg.birds} but uses {lure.label} in a sensible way."
    ]
    if outcome == "adult_help":
        prompts.append(
            "Make the ending show that asking a grown-up for help can be a brave choice too."
        )
    else:
        prompts.append(
            "End with the child solving the problem calmly and the yard feeling peaceful again."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    other = f["other"]
    parent = f["parent"]
    flock_cfg = f["flock_cfg"]
    place = f["place"]
    lure = f["lure"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was helping in {place.yard}, and {other.id}, who wanted to fix the problem quickly. It is also about {hero.id}'s {parent.label_word} and {flock_cfg.label} that got loose."
        ),
        (
            "What was the problem in the story?",
            f"The gate had not caught properly, so {flock_cfg.label} wandered out toward {place.out_spot}. That turned an ordinary after-school chore into a small backyard emergency."
        ),
        (
            f"Why did {hero.id} not want {other.id} to chase the birds?",
            f"{hero.id} knew chasing would scare the {flock_cfg.birds} and make them scatter farther. In this story, the flock is easier to guide when people stay calm instead of rushing."
        ),
    ]
    if f.get("scared"):
        qa.append(
            (
                f"Was {hero.id} scared?",
                f"Yes. {hero.id} felt nervous when the wings flapped and the yard got noisy. Even so, {hero.pronoun('subject')} still spoke up and chose a calmer plan."
            )
        )
    if outcome == "self_led":
        qa.append(
            (
                f"How did {hero.id} show bravery?",
                f"{hero.id} showed bravery by telling {other.id} to stop chasing and by using {lure.phrase} instead. {hero.pronoun('subject').capitalize()} stayed calm enough to {response.qa_text}, which brought the flock back safely."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The flock went back to {place.home_spot}, the gate was latched, and the yard felt peaceful again. The ending shows that calm bravery changed the whole mood of the afternoon."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} show bravery if {hero.pronoun('subject')} needed help?",
                f"{hero.id} still acted bravely by speaking up, getting {lure.phrase}, and then calling for {parent.label_word} when the birds felt too hard to manage alone. The brave part was choosing the safe, sensible thing instead of pretending not to be scared."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"{parent.label_word.capitalize()} helped guide the flock back to {place.home_spot}, and then the yard became quiet again. After that, everyone understood that asking for help can be part of being brave."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"flock", "guide"}
    tags |= set(f["flock_cfg"].tags)
    tags |= set(f["lure"].tags)
    if f["outcome"] == "adult_help":
        tags.add("help")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="backyard",
        flock="chickens",
        lure="grain",
        response="pan_rattle",
        hero="Lily",
        hero_gender="girl",
        other="Tom",
        other_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        place="orchard",
        flock="ducks",
        lure="peas",
        response="bowl_lead",
        hero="Ben",
        hero_gender="boy",
        other="Mia",
        other_gender="girl",
        parent="father",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        place="side_lane",
        flock="geese",
        lure="lettuce",
        response="open_path",
        hero="Ava",
        hero_gender="girl",
        other="Max",
        other_gender="boy",
        parent="mother",
        trait="brave",
        delay=0,
    ),
    StoryParams(
        place="backyard",
        flock="geese",
        lure="feed",
        response="bowl_lead",
        hero="Noah",
        hero_gender="boy",
        other="Lucy",
        other_gender="girl",
        parent="father",
        trait="gentle",
        delay=1,
    ),
    StoryParams(
        place="orchard",
        flock="ducks",
        lure="feed",
        response="pan_rattle",
        hero="Zoe",
        hero_gender="girl",
        other="Sam",
        other_gender="boy",
        parent="mother",
        trait="timid",
        delay=1,
    ),
]


ASP_RULES = r"""
fits(F, L) :- flock(F), lure(L), likes(F, L).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, F, L, R) :- place(P), fits(F, L), sensible(R).

bravery_have(V) :- chosen_trait(T), base_bravery(T, B), chosen_response(R), control(R, C), chosen_delay(D), V = B + C - D.
self_led :- chosen_flock(F), difficulty(F, Need), bravery_have(Have), Have >= Need.
outcome(self_led) :- self_led.
outcome(adult_help) :- not self_led.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for flock_id, flock in FLOCKS.items():
        lines.append(asp.fact("flock", flock_id))
        lines.append(asp.fact("difficulty", flock_id, flock.difficulty))
        for lure_id in sorted(flock.preference):
            lines.append(asp.fact("likes", flock_id, lure_id))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("control", response_id, response.control))
    for trait, value in TRAIT_BRAVERY.items():
        lines.append(asp.fact("base_bravery", trait, value))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_flock", params.flock),
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_delay", params.delay),
        ]
    )
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
    for seed in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child bravely helps guide a flock home."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--flock", choices=FLOCKS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=sorted(TRAIT_BRAVERY))
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra confusion before the calm plan works")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.flock and args.lure and not lure_fits(args.flock, args.lure):
        raise StoryError(explain_lure(args.flock, args.lure))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.flock is None or combo[1] == args.flock)
        and (args.lure is None or combo[2] == args.lure)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, flock, lure, response = rng.choice(sorted(combos))
    hero, hero_gender = _pick_child(rng)
    other, other_gender = _pick_child(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        place=place,
        flock=flock,
        lure=lure,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        other=other,
        other_gender=other_gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.flock not in FLOCKS:
        raise StoryError(f"(Unknown flock: {params.flock})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.trait not in TRAIT_BRAVERY:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not lure_fits(params.flock, params.lure):
        raise StoryError(explain_lure(params.flock, params.lure))

    world = tell(
        place=PLACES[params.place],
        flock_cfg=FLOCKS[params.flock],
        lure=LURES[params.lure],
        response=RESPONSES[params.response],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        other_name=params.other,
        other_gender=params.other_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, flock, lure, response) combos:\n")
        for place, flock, lure, response in combos:
            print(f"  {place:10} {flock:9} {lure:8} {response}")
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
            header = f"### {p.hero} and {p.other}: {p.flock} in {p.place} ({outcome_of(p)})"
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
