#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/zoologic_delay_monarch_happy_ending_conflict_myth.py
================================================================================

A standalone story world about a small animal envoy in a mythic beast-kingdom.

Every story uses the words "zoologic", "delay", and "monarch" naturally:
the animals live under the Zoologic Oath, a journey suffers a delay, and a
forest monarch waits at the end.

Domain premise
--------------
In the old animal kingdoms, a young envoy must carry a dawn gift to a monarch
before the Feast of First Light begins. A rival scoffs. An obstacle causes a
delay. The envoy chooses a fitting aid instead of anger, reaches the court, and
the monarch turns the conflict into peace.

The world model keeps:
- typed entities with physical meters and emotional memes,
- a small causal rule engine,
- a reasonableness gate over which aid can solve which obstacle,
- an inline ASP twin for the same gate and for the happy-ending outcome.

Run it
------
python storyworlds/worlds/gpt-5.4/zoologic_delay_monarch_happy_ending_conflict_myth.py
python storyworlds/worlds/gpt-5.4/zoologic_delay_monarch_happy_ending_conflict_myth.py --monarch butterfly_queen --obstacle fog_arch --aid firefly_lantern
python storyworlds/worlds/gpt-5.4/zoologic_delay_monarch_happy_ending_conflict_myth.py --all
python storyworlds/worlds/gpt-5.4/zoologic_delay_monarch_happy_ending_conflict_myth.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/zoologic_delay_monarch_happy_ending_conflict_myth.py --trace
python storyworlds/worlds/gpt-5.4/zoologic_delay_monarch_happy_ending_conflict_myth.py --verify
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
        female = {"queen", "hen", "doe", "ewe", "girl"}
        male = {"king", "stag", "lion", "fox", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Court:
    id: str
    title: str
    monarch_type: str
    monarch_name: str
    realm: str
    realm_image: str
    seat: str
    decree: str
    gift_label: str
    gift_phrase: str
    ending_blessing: str
    obstacle_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    cause: str
    delay_text: str
    severity: int
    solved_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    method: str
    power: int
    solves: set[str] = field(default_factory=set)
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_delay_fear(world: World) -> list[str]:
    hero = world.entities.get("hero")
    rival = world.entities.get("rival")
    if hero is None or hero.meters["delayed"] < THRESHOLD:
        return []
    sig = ("delay_fear", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    if rival is not None:
        rival.memes["scorn"] += 1
    return []


def _r_patience_softens(world: World) -> list[str]:
    hero = world.entities.get("hero")
    rival = world.entities.get("rival")
    if hero is None or rival is None:
        return []
    if hero.memes["patience"] < THRESHOLD or hero.meters["path_clear"] < THRESHOLD:
        return []
    sig = ("patience_softens", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rival.memes["doubt"] = 0.0
    rival.memes["shame"] += 1
    rival.memes["respect"] += 1
    return []


def _r_delivery_blessing(world: World) -> list[str]:
    hero = world.entities.get("hero")
    monarch = world.entities.get("monarch")
    realm = world.entities.get("realm")
    if hero is None or monarch is None or realm is None:
        return []
    if hero.meters["delivered"] < THRESHOLD:
        return []
    sig = ("delivery_blessing", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    monarch.memes["joy"] += 1
    realm.meters["blessing"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="delay_fear", tag="emotion", apply=_r_delay_fear),
    Rule(name="patience_softens", tag="social", apply=_r_patience_softens),
    Rule(name="delivery_blessing", tag="mythic", apply=_r_delivery_blessing),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PATIENT_TRAITS = {"patient", "gentle", "wise"}


def aid_matches(obstacle_id: str, aid_id: str) -> bool:
    if obstacle_id not in OBSTACLES or aid_id not in AIDS:
        return False
    obstacle = OBSTACLES[obstacle_id]
    aid = AIDS[aid_id]
    return obstacle_id in aid.solves and aid_id in obstacle.solved_by and aid.power >= obstacle.severity


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for court_id, court in COURTS.items():
        for obstacle_id in sorted(court.obstacle_ids):
            for aid_id in sorted(AIDS):
                if aid_matches(obstacle_id, aid_id):
                    out.append((court_id, obstacle_id, aid_id))
    return out


def ending_of(params: "StoryParams") -> str:
    if params.trait in PATIENT_TRAITS:
        return "reconciled"
    return "respected"


def predict_clearance(world: World, obstacle_id: str, aid_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["delayed"] += OBSTACLES[obstacle_id].severity
    propagate(sim, narrate=False)
    if aid_matches(obstacle_id, aid_id):
        hero.meters["path_clear"] += 1
        hero.meters["delayed"] = 0.0
        if hero.attrs.get("trait") in PATIENT_TRAITS:
            hero.memes["patience"] += 1
        propagate(sim, narrate=False)
    return {
        "clears": hero.meters["path_clear"] >= THRESHOLD,
        "worry": hero.memes["worry"],
    }


def introduce(world: World, hero: Entity, rival: Entity, monarch: Entity, court: Court) -> None:
    hero.memes["duty"] += 1
    rival.memes["doubt"] += 1
    world.say(
        f"In the elder age, when beasts still kept the Zoologic Oath beneath the stars, "
        f"{court.realm} listened for the word of its monarch, {monarch.label}."
    )
    world.say(
        f"On the morning of the Feast of First Light, {hero.label}, a small {hero.type}, "
        f"was chosen to carry {court.gift_phrase} to {court.seat}."
    )
    world.say(
        f"{rival.label}, a young {rival.type} who had hoped for the honor, walked beside "
        f"{hero.pronoun('object')} with a restless tail and an unkind heart."
    )


def charge(world: World, monarch: Entity, hero: Entity, court: Court) -> None:
    world.say(
        f'Before the climb began, {monarch.label} had said, "{court.decree} Bring me '
        f'{court.gift_label} before the sun touches the high stone."'
    )


def taunt(world: World, rival: Entity, hero: Entity) -> None:
    world.say(
        f'"A small {hero.type} makes a small messenger," {rival.label} said. '
        f'"You will bring only delay."'
    )


def obstacle_strikes(world: World, hero: Entity, rival: Entity, obstacle: Obstacle) -> None:
    hero.meters["delayed"] += obstacle.severity
    hero.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But halfway to the throne-place, {obstacle.phrase}. {obstacle.cause} "
        f"{obstacle.delay_text}"
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.label}'s heart beat fast. The gift was safe in {hero.pronoun('possessive')} "
            f"paws, but the path was not."
        )
    if rival.memes["scorn"] >= THRESHOLD:
        world.say(
            f'"Look," said {rival.label}, "the road itself agrees with me."'
        )


def seek_aid(world: World, hero: Entity, aid: Aid, obstacle: Obstacle) -> None:
    pred = predict_clearance(world, obstacle.id, aid.id)
    world.facts["predicted_clear"] = pred["clears"]
    world.say(
        f"Yet {hero.label} remembered the old zoologic teaching that anger blinds, "
        f"while a fitting tool opens the way. Near the stones lay {aid.phrase}."
    )


def use_aid(world: World, hero: Entity, rival: Entity, aid: Aid, obstacle: Obstacle) -> None:
    if hero.attrs.get("trait") in PATIENT_TRAITS:
        hero.memes["patience"] += 1
    else:
        hero.memes["resolve"] += 1
    hero.meters["path_clear"] += 1
    hero.meters["blocked"] = 0.0
    hero.meters["delayed"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.label} did not answer the insult. {hero.pronoun().capitalize()} took up "
        f"{aid.label} and {aid.method}"
    )
    if hero.attrs.get("trait") in PATIENT_TRAITS:
        world.say(
            f"{hero.pronoun().capitalize()} moved slowly enough to be sure, and that calmness "
            f"was stronger than haste."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} moved with steady courage, caring more for the gift "
            f"than for winning the last word."
        )
    if rival.memes["shame"] >= THRESHOLD:
        world.say(
            f"{rival.label} lowered {rival.pronoun('possessive')} ears. The mocking voice "
            f"grew small."
        )


def apology_or_awe(world: World, hero: Entity, rival: Entity) -> None:
    if hero.attrs.get("trait") in PATIENT_TRAITS:
        rival.memes["peace"] += 1
        world.say(
            f'"I was cruel," {rival.label} murmured. "{hero.label}, you were wiser than I was."'
        )
        world.say(
            f"{hero.label} nodded and made room on the path, so the two young beasts finished "
            f"the climb together."
        )
    else:
        rival.memes["awe"] += 1
        world.say(
            f"{rival.label} said nothing more. From then on, {rival.pronoun()} watched "
            f"{hero.label} with wide-eyed respect."
        )


def arrival(world: World, hero: Entity, rival: Entity, monarch: Entity, court: Court) -> None:
    hero.meters["delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When they reached {court.seat}, the last edge of sunlight still rested on the stone. "
        f"{hero.label} bowed and set {court.gift_label} before the monarch."
    )
    world.say(
        f'{monarch.label} lifted {monarch.pronoun("possessive")} gaze and said, '
        f'"The feast was delayed, but not defeated. Faithful feet have saved the morning."'
    )


def blessing(world: World, hero: Entity, rival: Entity, monarch: Entity, court: Court) -> None:
    world.say(
        f"Then {monarch.label} touched the gift, and {court.ending_blessing}. A warm hush "
        f"passed over the leaves as if the whole realm had breathed out at once."
    )
    if hero.attrs.get("trait") in PATIENT_TRAITS:
        world.say(
            f'{monarch.label} beckoned {rival.label} nearer. "Let no tongue scorn the small," '
            f'{monarch.pronoun()} said. "In the true zoologic order, patience is royal."'
        )
    else:
        world.say(
            f'{monarch.label} looked from {hero.label} to {rival.label}. "Strength is not loud," '
            f'{monarch.pronoun()} said. "The sure heart reaches me before the proud one."'
        )
    world.say(
        f"That evening the feast began at last, and {hero.label} sat near the fire while "
        f"{rival.label} kept close, no longer an enemy."
    )


def tell(court: Court, obstacle: Obstacle, aid: Aid,
         hero_name: str, hero_type: str, rival_name: str, rival_type: str,
         trait: str, parentless_title: str = "") -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={"trait": trait},
        tags={"envoy"},
    ))
    rival = world.add(Entity(
        id="rival",
        kind="character",
        type=rival_type,
        label=rival_name,
        role="rival",
        traits=["jealous"],
        tags={"conflict"},
    ))
    monarch = world.add(Entity(
        id="monarch",
        kind="character",
        type=court.monarch_type,
        label=court.monarch_name,
        role="monarch",
        tags=set(court.tags),
    ))
    realm = world.add(Entity(
        id="realm",
        kind="thing",
        type="realm",
        label=court.realm,
        phrase=court.realm_image,
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=court.gift_label,
        phrase=court.gift_phrase,
    ))
    aid_ent = world.add(Entity(
        id="aid",
        kind="thing",
        type="aid",
        label=aid.label,
        phrase=aid.phrase,
        tags=set(aid.tags),
    ))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
        phrase=obstacle.phrase,
        tags=set(obstacle.tags),
    ))

    introduce(world, hero, rival, monarch, court)
    charge(world, monarch, hero, court)

    world.para()
    taunt(world, rival, hero)
    obstacle_strikes(world, hero, rival, obstacle)

    world.para()
    seek_aid(world, hero, aid, obstacle)
    use_aid(world, hero, rival, aid, obstacle)
    apology_or_awe(world, hero, rival)

    world.para()
    arrival(world, hero, rival, monarch, court)
    blessing(world, hero, rival, monarch, court)

    outcome = ending_of(StoryParams(
        monarch=court.id,
        obstacle=obstacle.id,
        aid=aid.id,
        hero_name=hero_name,
        hero_type=hero_type,
        rival_name=rival_name,
        rival_type=rival_type,
        trait=trait,
        seed=None,
    ))
    world.facts.update(
        court=court,
        obstacle_cfg=obstacle,
        aid_cfg=aid,
        hero=hero,
        rival=rival,
        monarch_ent=monarch,
        realm=realm,
        gift=gift,
        obstacle_ent=obstacle_ent,
        aid_ent=aid_ent,
        outcome=outcome,
        delayed=True,
        delivered=hero.meters["delivered"] >= THRESHOLD,
        reconciled=outcome == "reconciled",
    )
    return world


COURTS = {
    "lion_king": Court(
        id="lion_king",
        title="the Golden Mane",
        monarch_type="lion",
        monarch_name="King Aurion",
        realm="Sunstep Ridge",
        realm_image="red cliffs and lion-grass above a gold river",
        seat="the basalt throne above the gold river",
        decree="Let the first bright thing of morning be laid in my hall, so the day may wake kindly.",
        gift_label="the sunseed acorn",
        gift_phrase="the sunseed acorn, wrapped in a leaf of amber fern",
        ending_blessing="the river flashed like a long sheet of fire and the grass bent in shining waves",
        obstacle_ids={"thorn_gate", "dust_whirl"},
        tags={"lion", "sun"},
    ),
    "owl_queen": Court(
        id="owl_queen",
        title="the Cedar-Crowned",
        monarch_type="queen",
        monarch_name="Queen Noctis",
        realm="Cedar Hollow",
        realm_image="blue woods where even noon held a little moonlight",
        seat="the cedar root throne in the moonlit hollow",
        decree="Bring me the dawn gift before the high branch brightens, and the forest will keep its wise peace.",
        gift_label="the dew pearl",
        gift_phrase="the dew pearl resting in a cup of bark",
        ending_blessing="silver light flowed through the cedar boughs and every nest grew quiet and safe",
        obstacle_ids={"fog_arch", "fallen_bough"},
        tags={"owl", "moon"},
    ),
    "butterfly_queen": Court(
        id="butterfly_queen",
        title="the Meadow Flame",
        monarch_type="queen",
        monarch_name="Queen Maris",
        realm="Petal Mere",
        realm_image="wide flowers, reed pools, and bright wings over the water",
        seat="the lily throne beside the shining mere",
        decree="Set the dawn token before me before the lilies open fully, and the meadow shall bloom without fear.",
        gift_label="the saffron lily-cup",
        gift_phrase="the saffron lily-cup filled with first light",
        ending_blessing="the flowers opened all at once and monarch wings turned the air into living gold",
        obstacle_ids={"fog_arch", "reed_flood"},
        tags={"butterfly", "meadow"},
    ),
}

OBSTACLES = {
    "fog_arch": Obstacle(
        id="fog_arch",
        label="the fog arch",
        phrase="a white arch of fog rose across the path",
        cause="It swallowed the trail markers and made every turning look the same, so a true delay fell over the journey.",
        delay_text="For a moment even the brave forgot which way led upward.",
        severity=2,
        solved_by={"firefly_lantern"},
        tags={"fog"},
    ),
    "thorn_gate": Obstacle(
        id="thorn_gate",
        label="the thorn gate",
        phrase="a woven gate of thorn-vines had folded shut across the stones",
        cause="Its hooked branches caught at fur and leaf-wrapping alike, and the road could not be rushed.",
        delay_text="The higher path stood still as a locked door.",
        severity=2,
        solved_by={"antler_hook"},
        tags={"thorn"},
    ),
    "reed_flood": Obstacle(
        id="reed_flood",
        label="the reed flood",
        phrase="the narrow reed-crossing lay under bright, rushing water",
        cause="The stream had climbed out of its banks in the night, and stepping in would sweep the gift away.",
        delay_text="The little bridge had become a singing strip of river.",
        severity=3,
        solved_by={"reed_skiff"},
        tags={"water"},
    ),
    "fallen_bough": Obstacle(
        id="fallen_bough",
        label="the fallen bough",
        phrase="a storm-thrown cedar bough sprawled over the hollow path",
        cause="It was too wide to crawl beneath and too prickly to shove aside with bare paws.",
        delay_text="The old wood made a dark wall between the envoy and the throne.",
        severity=2,
        solved_by={"antler_hook"},
        tags={"wood"},
    ),
    "dust_whirl": Obstacle(
        id="dust_whirl",
        label="the dust whirl",
        phrase="a little whirlwind of red dust began to dance across the ridge",
        cause="It spun grit into eyes and nose, and one blind step near the cliff would have been foolish.",
        delay_text="Even quick feet had to wait for a wiser moment.",
        severity=1,
        solved_by={"firefly_lantern"},
        tags={"dust"},
    ),
}

AIDS = {
    "firefly_lantern": Aid(
        id="firefly_lantern",
        label="the firefly lantern",
        phrase="a clear shell lantern where patient fireflies glowed like tiny stars",
        method="held its green-gold light before the mist until hidden marks shone out again.",
        power=2,
        solves={"fog_arch", "dust_whirl"},
        tags={"light"},
    ),
    "antler_hook": Aid(
        id="antler_hook",
        label="the antler hook",
        phrase="an old antler hook left by the keepers of the ridge",
        method="caught the woven branches and drew them back bit by bit until a safe gap opened.",
        power=2,
        solves={"thorn_gate", "fallen_bough"},
        tags={"tool"},
    ),
    "reed_skiff": Aid(
        id="reed_skiff",
        label="the reed skiff",
        phrase="a tiny reed skiff tied beneath a willow root",
        method="set the gift in the middle and poled across the flood with careful strokes.",
        power=3,
        solves={"reed_flood"},
        tags={"boat"},
    ),
}

HERO_TYPES = ["mouse", "hare", "wren", "squirrel", "fox"]
RIVAL_TYPES = ["fox", "rook", "weasel", "young stag", "hare"]
TRAITS = ["patient", "gentle", "wise", "brave", "steadfast"]
NAMES = {
    "mouse": ["Pip", "Miri", "Thim", "Nettle"],
    "hare": ["Lark", "Tavin", "Sable", "Moss"],
    "wren": ["Wisp", "Tila", "Reed", "Flit"],
    "squirrel": ["Hazel", "Fir", "Bran", "Poppy"],
    "fox": ["Rowan", "Ember", "Rill", "Sorrel"],
    "rook": ["Kett", "Onyx", "Crowl", "Shade"],
    "weasel": ["Nim", "Brisk", "Tarn", "Sedge"],
    "young stag": ["Ash", "Bram", "Vale", "Cedar"],
}


@dataclass
class StoryParams:
    monarch: str
    obstacle: str
    aid: str
    hero_name: str
    hero_type: str
    rival_name: str
    rival_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "monarch": [
        (
            "What is a monarch?",
            "A monarch is a king or queen who rules a kingdom. In old tales, the monarch is the one other creatures come to for judgment and blessing.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old story told in a grand, magical way. Myths often explain why people or animals follow certain rules or remember certain lessons.",
        )
    ],
    "fog": [
        (
            "What is fog?",
            "Fog is a cloud very close to the ground. It makes it hard to see the path in front of you.",
        )
    ],
    "thorn": [
        (
            "Why are thorns hard to walk through?",
            "Thorns are sharp parts of some plants. They can scratch fur, skin, and cloth, so you have to move carefully around them.",
        )
    ],
    "water": [
        (
            "Why can rushing water be dangerous?",
            "Rushing water pushes hard and moves fast. It can knock small animals off their feet or carry things away.",
        )
    ],
    "light": [
        (
            "Why does a lantern help in the dark or fog?",
            "A lantern makes light where your eyes cannot see well. Good light helps you notice safe steps and hidden markers.",
        )
    ],
    "tool": [
        (
            "What is a tool?",
            "A tool is an object used to help with a job. It makes a hard task safer or easier to do.",
        )
    ],
    "boat": [
        (
            "What does a little boat do?",
            "A little boat helps you float on water instead of stepping into it. That can keep you and what you carry dry and safe.",
        )
    ],
    "patience": [
        (
            "What is patience?",
            "Patience is staying calm while something takes time. It helps you choose a good way instead of a quick, careless one.",
        )
    ],
    "envoy": [
        (
            "What is an envoy?",
            "An envoy is a messenger sent to carry words or gifts for someone important. An envoy has to be careful because the message is not only for them.",
        )
    ],
}
KNOWLEDGE_ORDER = ["monarch", "myth", "fog", "thorn", "water", "light", "tool", "boat", "patience", "envoy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    court = f["court"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    hero = f["hero"]
    rival = f["rival"]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the words "zoologic", "delay", and "monarch".',
        f"Tell a mythic animal story where {hero.label}, a little {hero.type}, carries {court.gift_label} to {court.monarch_name}, but {obstacle.label} causes a delay and {rival.label} mocks {hero.pronoun('object')}.",
        f"Write a happy-ending conflict story where a small envoy solves a journey problem with {aid.label} and reaches the monarch in time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    court = f["court"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    hero = f["hero"]
    rival = f["rival"]
    monarch = f["monarch_ent"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a small {hero.type} chosen as an envoy, {rival.label}, who spoke unkindly out of jealousy, and {monarch.label}, the monarch waiting at the end of the road.",
        ),
        (
            f"What was {hero.label} carrying?",
            f"{hero.label} was carrying {court.gift_label} to {court.seat}. The gift mattered because the feast could not begin until it reached the monarch.",
        ),
        (
            "What caused the delay?",
            f"The delay came when {obstacle.phrase}. That obstacle blocked the road and made hurrying dangerous, so {hero.label} had to solve the problem instead of just running ahead.",
        ),
        (
            f"Why was {rival.label} mean to {hero.label}?",
            f"{rival.label} had hoped for the honor of carrying the gift and felt jealous when {hero.label} was chosen instead. The delay made that jealousy come out as mocking words.",
        ),
        (
            f"How did {hero.label} get past the obstacle?",
            f"{hero.label} used {aid.label} and {aid.method} That worked because it was the right help for that kind of obstacle, not just a random object.",
        ),
    ]
    if f["outcome"] == "reconciled":
        qa.append(
            (
                "How did the conflict end?",
                f"The conflict ended with an apology. Because {hero.label} stayed patient instead of angry, {rival.label} felt ashamed and finished the climb beside {hero.pronoun('object')}.",
            )
        )
    else:
        qa.append(
            (
                "How did the conflict change by the end?",
                f"{rival.label} stopped mocking {hero.label} and began to respect {hero.pronoun('object')}. Seeing the gift delivered made it clear that quiet courage was stronger than boasting.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"{hero.label} reached {court.seat}, gave {court.gift_label} to {monarch.label}, and the realm was blessed. The ending image shows peace returning because the hard journey was finished well.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"monarch", "myth", "patience", "envoy"}
    tags |= set(f["obstacle_cfg"].tags)
    tags |= set(f["aid_cfg"].tags)
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        monarch="butterfly_queen",
        obstacle="fog_arch",
        aid="firefly_lantern",
        hero_name="Miri",
        hero_type="mouse",
        rival_name="Rowan",
        rival_type="fox",
        trait="patient",
        seed=101,
    ),
    StoryParams(
        monarch="lion_king",
        obstacle="thorn_gate",
        aid="antler_hook",
        hero_name="Hazel",
        hero_type="squirrel",
        rival_name="Kett",
        rival_type="rook",
        trait="wise",
        seed=102,
    ),
    StoryParams(
        monarch="owl_queen",
        obstacle="fallen_bough",
        aid="antler_hook",
        hero_name="Wisp",
        hero_type="wren",
        rival_name="Nim",
        rival_type="weasel",
        trait="brave",
        seed=103,
    ),
    StoryParams(
        monarch="butterfly_queen",
        obstacle="reed_flood",
        aid="reed_skiff",
        hero_name="Lark",
        hero_type="hare",
        rival_name="Ash",
        rival_type="young stag",
        trait="gentle",
        seed=104,
    ),
]


def explain_rejection(monarch_id: str, obstacle_id: str, aid_id: str) -> str:
    if monarch_id not in COURTS:
        return "(No story: unknown monarch.)"
    if obstacle_id not in OBSTACLES:
        return "(No story: unknown obstacle.)"
    if aid_id not in AIDS:
        return "(No story: unknown aid.)"
    court = COURTS[monarch_id]
    obstacle = OBSTACLES[obstacle_id]
    aid = AIDS[aid_id]
    if obstacle_id not in court.obstacle_ids:
        return (
            f"(No story: {obstacle.label} does not belong on the road to {court.monarch_name}. "
            f"Pick an obstacle that fits that monarch's realm.)"
        )
    if aid_id not in obstacle.solved_by:
        return (
            f"(No story: {aid.label} does not sensibly solve {obstacle.label}. "
            f"This world only tells quests where the chosen help actually clears the delay.)"
        )
    if aid.power < obstacle.severity:
        return (
            f"(No story: {aid.label} is too weak for {obstacle.label}. "
            f"The aid must be strong enough for the obstacle.)"
        )
    return "(No story: that combination is unreasonable.)"


ASP_RULES = r"""
valid(M, O, A) :- court(M), court_obstacle(M, O), obstacle(O), aid(A),
                  solves(A, O), solved_by(O, A), power(A, P), severity(O, S), P >= S.

patient_trait(T) :- trait_name(T), patient(T).

ending(reconciled) :- chosen_trait(T), patient_trait(T).
ending(respected)  :- chosen_trait(T), not patient_trait(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for court_id, court in COURTS.items():
        lines.append(asp.fact("court", court_id))
        for obstacle_id in sorted(court.obstacle_ids):
            lines.append(asp.fact("court_obstacle", court_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("severity", obstacle_id, obstacle.severity))
        for aid_id in sorted(obstacle.solved_by):
            lines.append(asp.fact("solved_by", obstacle_id, aid_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("power", aid_id, aid.power))
        for obstacle_id in sorted(aid.solves):
            lines.append(asp.fact("solves", aid_id, obstacle_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(PATIENT_TRAITS):
        lines.append(asp.fact("patient", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_ending(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show ending/1."))
    atoms = asp.atoms(model, "ending")
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
    for params in cases:
        if asp_ending(params) != ending_of(params):
            rc = 1
            print(f"MISMATCH in ending for {params}: asp={asp_ending(params)} py={ending_of(params)}")

    if rc == 0:
        print(f"OK: ending model matches on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "monarch" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story text missing or malformed.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a mythic animal envoy, a delay, and a monarch."
    )
    ap.add_argument("--monarch", choices=COURTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--hero-name")
    ap.add_argument("--rival-type", choices=RIVAL_TYPES)
    ap.add_argument("--rival-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, animal_type: str, avoid: str = "") -> str:
    pool = [name for name in NAMES[animal_type] if name != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.monarch and args.obstacle and args.aid:
        if not aid_matches(args.obstacle, args.aid) or args.obstacle not in COURTS[args.monarch].obstacle_ids:
            raise StoryError(explain_rejection(args.monarch, args.obstacle, args.aid))

    combos = [
        combo for combo in valid_combos()
        if (args.monarch is None or combo[0] == args.monarch)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        if args.monarch and args.obstacle and args.aid:
            raise StoryError(explain_rejection(args.monarch, args.obstacle, args.aid))
        raise StoryError("(No valid combination matches the given options.)")

    monarch_id, obstacle_id, aid_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(sorted(HERO_TYPES))
    rival_type = args.rival_type or rng.choice(sorted(RIVAL_TYPES))
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    rival_name = args.rival_name or _pick_name(rng, rival_type, avoid=hero_name)
    trait = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        monarch=monarch_id,
        obstacle=obstacle_id,
        aid=aid_id,
        hero_name=hero_name,
        hero_type=hero_type,
        rival_name=rival_name,
        rival_type=rival_type,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.monarch not in COURTS:
        raise StoryError(f"(No story: unknown monarch '{params.monarch}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.aid not in AIDS:
        raise StoryError(f"(No story: unknown aid '{params.aid}'.)")
    if params.hero_type not in HERO_TYPES:
        raise StoryError(f"(No story: unknown hero type '{params.hero_type}'.)")
    if params.rival_type not in RIVAL_TYPES:
        raise StoryError(f"(No story: unknown rival type '{params.rival_type}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(No story: unknown trait '{params.trait}'.)")
    if not aid_matches(params.obstacle, params.aid) or params.obstacle not in COURTS[params.monarch].obstacle_ids:
        raise StoryError(explain_rejection(params.monarch, params.obstacle, params.aid))

    world = tell(
        court=COURTS[params.monarch],
        obstacle=OBSTACLES[params.obstacle],
        aid=AIDS[params.aid],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        rival_name=params.rival_name,
        rival_type=params.rival_type,
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
        print(asp_program("", "#show valid/3.\n#show ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (monarch, obstacle, aid) combos:\n")
        for monarch_id, obstacle_id, aid_id in combos:
            print(f"  {monarch_id:16} {obstacle_id:12} {aid_id}")
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
            header = f"### {p.hero_name}: {p.monarch} / {p.obstacle} / {p.aid} ({ending_of(p)})"
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
