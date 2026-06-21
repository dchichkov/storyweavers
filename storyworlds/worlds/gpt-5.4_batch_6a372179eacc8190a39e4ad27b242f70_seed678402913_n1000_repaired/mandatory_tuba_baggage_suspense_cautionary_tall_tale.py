#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mandatory_tuba_baggage_suspense_cautionary_tall_tale.py
==================================================================================

A standalone storyworld about a child, an enormous tuba, and a dangerous baggage
heap at a depot. The seed words are built into the domain itself: the baggage
check is mandatory, the prized instrument is a tuba, and the central danger
comes from trying to scramble up where baggage is being loaded.

The stories aim for a child-facing tall-tale voice: big images, a little
exaggeration, and a clear cautionary lesson. The tension comes from suspense
around an unstable loading place, and the resolution is state-driven: either a
careful helper solves the problem the sensible way, or the child learns from a
near disaster.

Run it
------
    python storyworlds/worlds/gpt-5.4/mandatory_tuba_baggage_suspense_cautionary_tall_tale.py
    python storyworlds/worlds/gpt-5.4/mandatory_tuba_baggage_suspense_cautionary_tall_tale.py --trip riverboat --perch rolling_cart
    python storyworlds/worlds/gpt-5.4/mandatory_tuba_baggage_suspense_cautionary_tall_tale.py --rescue leap_grab
    python storyworlds/worlds/gpt-5.4/mandatory_tuba_baggage_suspense_cautionary_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/mandatory_tuba_baggage_suspense_cautionary_tall_tale.py --verify
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
NERVE_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "watchful"}


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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "porter", "conductor", "captain", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "porter": "porter",
            "conductor": "conductor",
            "captain": "captain",
        }.get(self.type, self.label or self.type)


@dataclass
class Trip:
    id: str
    depot: str
    vehicle: str
    opening: str
    leaving: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    height_words: str
    wobble_text: str
    fall_text: str
    instability: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
    sense: int
    power: int
    applies: set[str] = field(default_factory=set)
    success_text: str = ""
    fail_text: str = ""
    qa_text: str = ""


@dataclass
class StoryParams:
    trip: str
    perch: str
    rescue: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    helper_type: str
    trait: str
    relation: str = "siblings"
    hero_age: int = 6
    companion_age: int = 5
    delay: int = 0
    case_color: str = "brassy"
    tag_style: str = "red string"
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "companion"}]

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


def _r_wobble_risk(world: World) -> list[str]:
    out: list[str] = []
    perch = world.entities.get("perch")
    if perch is None or perch.meters["wobble"] < THRESHOLD:
        return out
    sig = ("risk", "perch")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    station = world.get("station")
    station.meters["risk"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__risk__")
    return out


def _r_slide(world: World) -> list[str]:
    out: list[str] = []
    perch = world.entities.get("perch")
    if perch is None:
        return out
    if perch.meters["wobble"] < 2.0:
        return out
    sig = ("slide", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    hero.meters["slipping"] += 1
    hero.memes["fear"] += 1
    out.append("__slide__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble_risk", tag="physical", apply=_r_wobble_risk),
    Rule(name="slide", tag="physical", apply=_r_slide),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


TRIPS = {
    "stagecoach": Trip(
        id="stagecoach",
        depot="the dusty stagecoach yard",
        vehicle="the stagecoach",
        opening="The yard was busy enough to make a rooster dizzy, with trunks thumping and harness bells ringing.",
        leaving="By noon the stagecoach rolled off in a cloud so wide it looked like the road had grown its own weather.",
        tags={"wagon", "road"},
    ),
    "riverboat": Trip(
        id="riverboat",
        depot="the river landing",
        vehicle="the riverboat",
        opening="The landing puffed and hissed while the riverboat snorted by the dock like a sleepy iron whale.",
        leaving="At last the riverboat swung away from the dock and the wake curled behind it like a white ribbon.",
        tags={"dock", "water"},
    ),
    "night_train": Trip(
        id="night_train",
        depot="the train platform",
        vehicle="the night train",
        opening="The platform hummed and steamed until the whole place felt like a kettle with wheels.",
        leaving="Soon the night train sang on the rails and pulled the town behind it as neat as thread through cloth.",
        tags={"rails", "steam"},
    ),
}

PERCHES = {
    "baggage_mountain": Perch(
        id="baggage_mountain",
        label="baggage mountain",
        phrase="a mountain of baggage stacked by the loading gate",
        height_words="high as a hay wagon and twice as fussy",
        wobble_text="The pile gave a long, sleepy sway, as if the trunks had all taken one breath together.",
        fall_text="Suitcases slid and bumped down in a clattering wave, and the tuba case bounced like a startled beetle.",
        instability=2,
        tags={"pile", "high"},
    ),
    "rolling_cart": Perch(
        id="rolling_cart",
        label="rolling baggage cart",
        phrase="a rolling baggage cart with tall sides",
        height_words="so rickety it seemed to have been built out of hiccups",
        wobble_text="The cart jerked on its wheels and creaked forward an inch all by itself.",
        fall_text="The cart lurched, trunks popped loose, and the whole load came rattling after it.",
        instability=3,
        tags={"wheels", "moving"},
    ),
    "loading_ramp": Perch(
        id="loading_ramp",
        label="loading ramp",
        phrase="the narrow loading ramp beside the baggage door",
        height_words="steep as a goat path and slick with hurry",
        wobble_text="The ramp shivered under little feet and sent a hollow drumbeat through the boards.",
        fall_text="Bundles skidded sideways, the case slewed around, and the ramp nearly spat both child and baggage onto the ground.",
        instability=2,
        tags={"ramp", "narrow"},
    ),
}

RESCUES = {
    "porter_ladder": Rescue(
        id="porter_ladder",
        label="porter ladder",
        sense=3,
        power=3,
        applies={"pile", "ramp"},
        success_text="fetched a short ladder, climbed up steady as a fence post, and brought both child and tuba case down one careful step at a time",
        fail_text="set a ladder against the mess, but by then the shifting load had grown too wild to tame at once",
        qa_text="used a short ladder and guided the child and the tuba case down carefully",
    ),
    "brake_and_stepstool": Rescue(
        id="brake_and_stepstool",
        label="brake and stepstool",
        sense=3,
        power=4,
        applies={"wheels"},
        success_text="stamped the wheel brake, shoved a stout stepstool into place, and lifted the child down before the cart could roll another inch",
        fail_text="stamped the brake and reached with the stepstool, but the cart had already lunged too hard",
        qa_text="stopped the cart with the brake and lifted the child down with a stepstool",
    ),
    "hook_pole": Rescue(
        id="hook_pole",
        label="hook pole",
        sense=2,
        power=2,
        applies={"pile", "ramp", "wheels"},
        success_text="caught the tuba strap with a long hook pole, steadied the load, and talked the child down slow and sure",
        fail_text="caught at the strap with a hook pole, but the swaying baggage was already too unruly",
        qa_text="used a long hook pole to steady the tuba case and talk the child down",
    ),
    "leap_grab": Rescue(
        id="leap_grab",
        label="leap and grab",
        sense=1,
        power=1,
        applies={"pile", "ramp", "wheels"},
        success_text="jumped for the child and the tuba in one flying snatch",
        fail_text="jumped for the child and the tuba, but the load scattered faster than hands could catch it",
        qa_text="jumped and tried to grab everything at once",
    ),
}

GIRL_NAMES = ["Molly", "Nell", "Ada", "Lucy", "Pearl", "Dora", "Mabel", "Ruby"]
BOY_NAMES = ["Jasper", "Eli", "Tom", "Finn", "Beau", "Cal", "Otis", "Wade"]
TRAITS = ["careful", "curious", "steady", "bold", "sensible", "watchful"]
CASE_COLORS = ["brassy", "sun-yellow", "coppery", "gold-bright"]
TAG_STYLES = ["red string", "blue ribbon", "striped cord"]


def rescue_allowed(perch: Perch, rescue: Rescue) -> bool:
    return bool(perch.tags & rescue.applies)


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for trip_id in TRIPS:
        for perch_id, perch in PERCHES.items():
            for rescue_id, rescue in RESCUES.items():
                if rescue.sense >= SENSE_MIN and rescue_allowed(perch, rescue):
                    combos.append((trip_id, perch_id, rescue_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, companion_age: int, trait: str) -> bool:
    companion_older = relation == "siblings" and companion_age > hero_age
    authority = initial_caution(trait) + 1.0 + (2.0 if companion_older else 0.0)
    return companion_older and authority > NERVE_INIT


def risk_severity(perch: Perch, delay: int) -> int:
    return perch.instability + delay


def is_contained(rescue: Rescue, perch: Perch, delay: int) -> bool:
    return rescue.power >= risk_severity(perch, delay)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    perch = sim.get("perch")
    perch.meters["wobble"] += float(sim.facts["perch_cfg"].instability)
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("station").meters["risk"],
        "slipping": sim.get("hero").meters["slipping"],
    }


def introduce(world: World, trip: Trip, hero: Entity, companion: Entity, tuba: Entity) -> None:
    world.say(
        f"{hero.id} and {companion.id} came to {trip.depot} with a {tuba.label} so large "
        f"it looked fit to swallow a moonbeam whole. {trip.opening}"
    )
    world.say(
        f"They were bound for a band show on {trip.vehicle}, and the tuba case shone {tuba.attrs['case_color']} in the light."
    )


def mandatory_rule(world: World, helper: Entity, trip: Trip, tuba: Entity) -> None:
    world.say(
        f'At the gate, the {helper.label_word} pointed to the loading place and said, '
        f'"Every horn bigger than a fiddle goes in baggage, and the baggage check is mandatory before {trip.vehicle} leaves."'
    )
    world.say(
        f"A paper tag on {tuba.pronoun('possessive')} handle, tied with {tuba.attrs['tag_style']}, fluttered like a little flag of worry."
    )


def worry(world: World, hero: Entity, tuba: Entity, perch: Perch) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} watched the tuba case move toward {perch.phrase} and felt {hero.pronoun('possessive')} stomach do a wagon-wheel flip."
    )
    world.say(
        f'"What if my tuba gets buried under all that baggage?" {hero.pronoun()} asked.'
    )


def warning(world: World, companion: Entity, hero: Entity, perch: Perch) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_risk"] = pred["risk"]
    companion.memes["caution"] += 1
    world.say(
        f'{companion.id} grabbed {hero.pronoun("possessive")} sleeve. "Don\'t climb {perch.phrase}," '
        f'{companion.pronoun()} said. "{perch.height_words.capitalize()}, and one wobble could send baggage every which way."'
    )


def decide_to_climb(world: World, hero: Entity, companion: Entity, perch: Perch) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But {hero.id} was all nerve and hurry. "I only need one peek," {hero.pronoun()} said, and up {perch.phrase} {hero.pronoun()} scrambled.'
    )
    perch_ent = world.get("perch")
    perch_ent.meters["wobble"] += float(world.facts["perch_cfg"].instability)
    propagate(world, narrate=False)
    world.say(perch.wobble_text)
    if world.get("hero").meters["slipping"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s boots skidded, and {hero.pronoun('possessive')} arms pinwheeled so fast they might have churned butter."
        )


def back_down(world: World, hero: Entity, companion: Entity, helper: Entity, tuba: Entity, trip: Trip) -> None:
    hero.memes["relief"] += 1
    companion.memes["relief"] += 1
    world.say(
        f"{hero.id} looked at {companion.id}, who was the older one, and all at once the brave idea shrank to the size of a bean."
    )
    world.say(
        f'"You\'re right," {hero.pronoun()} whispered. {hero.id} kept both boots on the ground and waved for the {helper.label_word} instead.'
    )
    world.para()
    world.say(
        f"The {helper.label_word} set the tuba case on top where the tag could be seen plain as noon, then gave {hero.id} a proper baggage stub to keep."
    )
    world.say(
        f"{trip.leaving} {hero.id} sat by the window, holding the stub in one hand and the lesson in the other."
    )


def rescue_success(world: World, helper: Entity, rescue: Rescue, trip: Trip) -> None:
    world.say(
        f"The {helper.label_word} moved quicker than a clap of thunder and {rescue.success_text}."
    )
    world.say(
        f"When both feet touched the ground again, everyone let out the breath they had been holding."
    )
    world.para()
    world.say(
        f'"In a busy place, you ask for help before you climb where baggage belongs," the {helper.label_word} said. "That is how horns stay shiny and children stay safe."'
    )
    world.say(
        f"{trip.leaving} The tuba rode in baggage, but this time {world.get('hero').id} watched calmly from a seat instead of from a dangerous perch."
    )


def rescue_fail(world: World, helper: Entity, rescue: Rescue, perch: Perch, tuba: Entity, trip: Trip) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    tuba.meters["dented"] += 1
    tuba.meters["spilled"] += 1
    hero.memes["fear"] += 1
    companion.memes["fear"] += 1
    world.say(
        f"The {helper.label_word} rushed in and {rescue.fail_text}. Then {perch.fall_text}"
    )
    world.say(
        f"The child was caught and set down safe, but the tuba case took a bang hard enough to make every grown-up wince."
    )
    world.para()
    world.say(
        f"{hero.id} hugged the case and saw a fresh dent gleaming in the side. It was not a giant dent, but it was big enough to carry a lesson."
    )
    world.say(
        f'"Next time," said the {helper.label_word}, gentler now, "leave climbing to ladders and loading to loaders."'
    )
    world.say(
        f"{trip.leaving} All the way along, {hero.id} kept one hand on the baggage stub and did not once wish to climb again."
    )


def build_world(
    trip: Trip,
    perch: Perch,
    rescue: Rescue,
    hero_name: str,
    hero_gender: str,
    companion_name: str,
    companion_gender: str,
    helper_type: str,
    trait: str,
    relation: str,
    hero_age: int,
    companion_age: int,
    delay: int,
    case_color: str,
    tag_style: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=["little", "musical"],
        age=hero_age,
        attrs={"display": hero_name},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=companion_gender,
        label=companion_name,
        phrase=companion_name,
        role="companion",
        traits=[trait],
        age=companion_age,
        attrs={"display": companion_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=f"the {helper_type}",
        phrase=f"the {helper_type}",
        role="helper",
    ))
    station = world.add(Entity(
        id="station",
        type="place",
        label=trip.depot,
        phrase=trip.depot,
    ))
    tuba = world.add(Entity(
        id="tuba",
        type="instrument",
        label="tuba case",
        phrase="the tuba case",
        attrs={"case_color": case_color, "tag_style": tag_style},
        tags={"tuba", "baggage"},
    ))
    perch_ent = world.add(Entity(
        id="perch",
        type="hazard",
        label=perch.label,
        phrase=perch.phrase,
        tags=set(perch.tags),
    ))

    hero.memes["nerve"] = NERVE_INIT
    companion.memes["caution"] = initial_caution(trait)

    world.facts.update(
        trip=trip,
        perch_cfg=perch,
        rescue=rescue,
        relation=relation,
        hero_name=hero_name,
        companion_name=companion_name,
        helper_type=helper_type,
        delay=delay,
        tuba=tuba,
    )

    introduce(world, trip, hero, companion, tuba)
    mandatory_rule(world, helper, trip, tuba)
    world.para()
    worry(world, hero, tuba, perch)
    warning(world, companion, hero, perch)

    if would_avert(relation, hero_age, companion_age, trait):
        world.facts["outcome"] = "averted"
        world.facts["severity"] = 0
        back_down(world, hero, companion, helper, tuba, trip)
    else:
        world.say(
            "For half a heartbeat the whole depot seemed to stop and listen."
        )
        world.para()
        decide_to_climb(world, hero, companion, perch)
        severity = risk_severity(perch, delay)
        perch_ent.meters["severity"] = float(severity)
        world.facts["severity"] = severity
        world.facts["outcome"] = "contained" if is_contained(rescue, perch, delay) else "spill"

        if is_contained(rescue, perch, delay):
            world.para()
            rescue_success(world, helper, rescue, trip)
        else:
            world.para()
            rescue_fail(world, helper, rescue, perch, tuba, trip)

    world.facts.update(
        hero=hero,
        companion=companion,
        helper=helper,
        station=station,
        tuba_entity=tuba,
        perch_entity=perch_ent,
        used_mandatory=True,
    )
    return world


def hero_name(ent: Entity) -> str:
    return ent.attrs.get("display", ent.label or ent.id)


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young friends"


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    trip = world.facts["trip"]
    perch = world.facts["perch_cfg"]
    outcome = world.facts["outcome"]
    rescue = world.facts["rescue"]
    if outcome == "averted":
        return [
            'Write a tall-tale-flavored cautionary story for a 3-to-5-year-old that includes the words "mandatory", "tuba", and "baggage".',
            f"Tell a suspenseful but gentle story where {hero_name(hero)} worries about a tuba in baggage at {trip.depot} but listens to {hero_name(companion)} and does not climb {perch.phrase}.",
            "Write a child-facing story with big, playful images where a mandatory rule seems annoying at first, but asking a grown-up for help keeps everyone safe.",
        ]
    if outcome == "contained":
        return [
            'Write a suspenseful cautionary tall tale for a 3-to-5-year-old that includes the words "mandatory", "tuba", and "baggage".',
            f"Tell a story where {hero_name(hero)} climbs {perch.phrase} to watch a tuba in baggage, and a grown-up uses {rescue.label} to bring the child down safely.",
            "Write a story with a scary middle turn and a calm ending that shows why children should ask for help instead of climbing in a loading area.",
        ]
    return [
        'Write a cautionary tall tale for a 3-to-5-year-old that includes the words "mandatory", "tuba", and "baggage".',
        f"Tell a suspenseful story where {hero_name(hero)} climbs {perch.phrase} because the baggage check is mandatory, and the tuba case gets dented before the lesson is learned.",
        "Write a story with big tall-tale images and a firm warning about not climbing where heavy baggage is stacked or rolling.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    helper = world.facts["helper"]
    trip = world.facts["trip"]
    perch = world.facts["perch_cfg"]
    rescue = world.facts["rescue"]
    outcome = world.facts["outcome"]
    relation = world.facts["relation"]
    tuba = world.facts["tuba_entity"]
    hname = hero_name(hero)
    cname = hero_name(companion)
    pair = pair_noun(hero, companion, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hname} and {cname}, a tuba bound for {trip.vehicle}, and the grown-up helper at {trip.depot}. The whole problem starts because the tuba has to go with the baggage.",
        ),
        (
            "What was mandatory in the story?",
            f"The baggage check was mandatory before the trip could begin. That rule is what made {hname} worry about losing sight of the tuba case.",
        ),
        (
            f"Why did {hname} want to climb?",
            f"{hname} was afraid the tuba case would disappear under the baggage and wanted one more look at it. The worry made climbing seem quick and clever, even though it was dangerous.",
        ),
        (
            f"Why did {cname} warn {hname}?",
            f"{cname} could see that {perch.phrase} was shaky and unsafe. One wobble there could send heavy baggage sliding and put both the child and the tuba at risk.",
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What did {hname} do after the warning?",
            f"{hname} listened and kept both boots on the ground. Then {hname} asked the {helper.label_word} for help instead of climbing into the loading place."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely. The tuba still rode in baggage, but {hname} watched from a seat and carried a baggage stub instead of a risky idea."
        ))
    elif outcome == "contained":
        qa.append((
            f"How did the {helper.label_word} solve the problem?",
            f"The {helper.label_word} {rescue.qa_text}. That worked because the grown-up used the right tool for that kind of loading place."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{hname} learned to ask for help before climbing where baggage belongs. The scary wobble proved that hurry can turn a small worry into a much bigger problem."
        ))
    else:
        qa.append((
            "What went wrong when help came too late?",
            f"The child was caught safely, but the swaying load spilled and the tuba case was dented. The danger had grown too big because the climbing started on an unstable place full of baggage."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with everyone safe but the tuba case banged up and the lesson learned the hard way. After that, {hname} held onto the baggage stub and stopped wishing to climb."
        ))
    return qa


KNOWLEDGE = {
    "mandatory": [
        ("What does mandatory mean?", "Mandatory means something must be done because it is a rule, not just a choice.")
    ],
    "tuba": [
        ("What is a tuba?", "A tuba is a very large brass instrument that makes deep, booming notes. It is much bigger than a trumpet.")
    ],
    "baggage": [
        ("What is baggage?", "Baggage is the bags, trunks, and cases people bring when they travel. It is carried and loaded before the trip starts.")
    ],
    "porter": [
        ("What does a porter do?", "A porter helps move and load baggage safely. Porters know how to handle heavy things and busy loading places.")
    ],
    "conductor": [
        ("What does a conductor do?", "A conductor helps manage a train trip and keeps things in order. A conductor watches the cars, the passengers, and the rules.")
    ],
    "captain": [
        ("What does a captain do on a boat?", "A captain leads the boat and helps keep the trip safe. The captain makes sure people and cargo are handled properly.")
    ],
    "ladder": [
        ("Why is a ladder safer than climbing baggage?", "A ladder gives your feet steady steps and is meant for climbing. Piles of baggage can shift and slip.")
    ],
    "brake": [
        ("What does a wheel brake do?", "A wheel brake stops a cart from rolling. That keeps the load from moving when someone needs it to stay still.")
    ],
    "loading": [
        ("Why should children stay out of loading areas?", "Loading areas have heavy things that can shift, roll, or fall. A grown-up can get the job done safely without a child climbing there.")
    ],
}

KNOWLEDGE_ORDER = ["mandatory", "tuba", "baggage", "porter", "conductor", "captain", "ladder", "brake", "loading"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    helper = world.facts["helper"]
    rescue = world.facts["rescue"]
    tags = {"mandatory", "tuba", "baggage", "loading"}
    if helper.type == "porter":
        tags.add("porter")
    if helper.type == "conductor":
        tags.add("conductor")
    if helper.type == "captain":
        tags.add("captain")
    if rescue.id == "porter_ladder":
        tags.add("ladder")
    if rescue.id == "brake_and_stepstool":
        tags.add("brake")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_response(rescue_id: str) -> str:
    rescue = RESCUES[rescue_id]
    better = ", ".join(sorted(r.id for r in sensible_rescues()))
    return (
        f"(Refusing rescue '{rescue_id}': it scores too low on common sense "
        f"(sense={rescue.sense} < {SENSE_MIN}). Try a steadier rescue such as {better}.)"
    )


def explain_combo(perch: Perch, rescue: Rescue) -> str:
    return (
        f"(No story: {rescue.label} is not a sensible match for {perch.phrase}. "
        f"Pick a rescue suited to that kind of loading place.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.companion_age, params.trait):
        return "averted"
    perch = PERCHES[params.perch]
    rescue = RESCUES[params.rescue]
    return "contained" if is_contained(rescue, perch, params.delay) else "spill"


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
valid(T, P, R) :- trip(T), perch(P), rescue(R), sensible(R), applies_to(R, Tag), has_tag(P, Tag).

% --- outcome model ----------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), companion_age(CA), hero_age(HA), CA > HA.
bonus(2) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), nerve_init(N), A > N.

severity(I + D) :- chosen_perch(P), instability(P, I), delay(D).
contained :- chosen_rescue(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spill) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for trip_id in TRIPS:
        lines.append(asp.fact("trip", trip_id))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("instability", perch_id, perch.instability))
        for tag in sorted(perch.tags):
            lines.append(asp.fact("has_tag", perch_id, tag))
    for rescue_id, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rescue_id))
        lines.append(asp.fact("sense", rescue_id, rescue.sense))
        lines.append(asp.fact("power", rescue_id, rescue.power))
        for tag in sorted(rescue.applies):
            lines.append(asp.fact("applies_to", rescue_id, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("nerve_init", int(NERVE_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append("sensible(R) :- rescue(R), sense(R, S), sense_min(M), S >= M.")
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
        asp.fact("chosen_perch", params.perch),
        asp.fact("chosen_rescue", params.rescue),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("companion_age", params.companion_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a giant tuba, mandatory baggage, and a risky loading place."
    )
    ap.add_argument("--trip", choices=TRIPS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--helper", choices=["porter", "conductor", "captain"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the danger grows before help reaches the child")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rescue and RESCUES[args.rescue].sense < SENSE_MIN:
        raise StoryError(explain_response(args.rescue))
    if args.perch and args.rescue:
        perch = PERCHES[args.perch]
        rescue = RESCUES[args.rescue]
        if not rescue_allowed(perch, rescue):
            raise StoryError(explain_combo(perch, rescue))

    combos = [
        combo for combo in valid_combos()
        if (args.trip is None or combo[0] == args.trip)
        and (args.perch is None or combo[1] == args.perch)
        and (args.rescue is None or combo[2] == args.rescue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    trip_id, perch_id, rescue_id = rng.choice(sorted(combos))
    hero, hero_gender = _pick_child(rng)
    companion, companion_gender = _pick_child(rng, avoid=hero)
    helper_type = args.helper or rng.choice(["porter", "conductor", "captain"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([4, 5, 6, 7, 8], 2)
    hero_age, companion_age = ages[0], ages[1]
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        trip=trip_id,
        perch=perch_id,
        rescue=rescue_id,
        hero=hero,
        hero_gender=hero_gender,
        companion=companion,
        companion_gender=companion_gender,
        helper_type=helper_type,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        companion_age=companion_age,
        delay=delay,
        case_color=rng.choice(CASE_COLORS),
        tag_style=rng.choice(TAG_STYLES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.trip not in TRIPS:
        raise StoryError(f"(Unknown trip: {params.trip})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")
    if params.helper_type not in {"porter", "conductor", "captain"}:
        raise StoryError(f"(Unknown helper: {params.helper_type})")
    if RESCUES[params.rescue].sense < SENSE_MIN:
        raise StoryError(explain_response(params.rescue))
    if not rescue_allowed(PERCHES[params.perch], RESCUES[params.rescue]):
        raise StoryError(explain_combo(PERCHES[params.perch], RESCUES[params.rescue]))

    world = build_world(
        trip=TRIPS[params.trip],
        perch=PERCHES[params.perch],
        rescue=RESCUES[params.rescue],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        companion_name=params.companion,
        companion_gender=params.companion_gender,
        helper_type=params.helper_type,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        companion_age=params.companion_age,
        delay=params.delay,
        case_color=params.case_color,
        tag_style=params.tag_style,
    )

    text = world.render().replace("  ", " ").strip()
    if "mandatory" not in text or "tuba" not in text or "baggage" not in text:
        raise StoryError("(Story text failed to include the required seed words.)")

    return StorySample(
        params=params,
        story=text,
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


CURATED = [
    StoryParams(
        trip="stagecoach",
        perch="baggage_mountain",
        rescue="porter_ladder",
        hero="Molly",
        hero_gender="girl",
        companion="Eli",
        companion_gender="boy",
        helper_type="porter",
        trait="watchful",
        relation="friends",
        hero_age=6,
        companion_age=6,
        delay=0,
        case_color="brassy",
        tag_style="red string",
    ),
    StoryParams(
        trip="riverboat",
        perch="rolling_cart",
        rescue="brake_and_stepstool",
        hero="Jasper",
        hero_gender="boy",
        companion="Ruby",
        companion_gender="girl",
        helper_type="captain",
        trait="steady",
        relation="siblings",
        hero_age=7,
        companion_age=5,
        delay=1,
        case_color="gold-bright",
        tag_style="blue ribbon",
    ),
    StoryParams(
        trip="night_train",
        perch="loading_ramp",
        rescue="hook_pole",
        hero="Ada",
        hero_gender="girl",
        companion="Mabel",
        companion_gender="girl",
        helper_type="conductor",
        trait="careful",
        relation="siblings",
        hero_age=5,
        companion_age=7,
        delay=0,
        case_color="coppery",
        tag_style="striped cord",
    ),
    StoryParams(
        trip="stagecoach",
        perch="rolling_cart",
        rescue="brake_and_stepstool",
        hero="Finn",
        hero_gender="boy",
        companion="Pearl",
        companion_gender="girl",
        helper_type="porter",
        trait="bold",
        relation="friends",
        hero_age=6,
        companion_age=6,
        delay=2,
        case_color="sun-yellow",
        tag_style="red string",
    ),
]


def asp_verify() -> int:
    rc = 0
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as err:
        print(f"ASP verify failed while computing valid combos: {err}")
        return 1

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
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp_out = asp_outcome(params)
        if py != asp_out:
            bad += 1
            print(f"Outcome mismatch for {params}: python={py} asp={asp_out}")
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"Smoke test failed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (trip, perch, rescue) combos:\n")
        for trip_id, perch_id, rescue_id in combos:
            print(f"  {trip_id:11} {perch_id:17} {rescue_id}")
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
            header = f"### {p.hero} and {p.companion}: {p.trip}, {p.perch}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
