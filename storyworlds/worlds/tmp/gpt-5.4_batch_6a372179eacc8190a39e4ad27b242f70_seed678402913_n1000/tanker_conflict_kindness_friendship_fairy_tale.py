#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tanker_conflict_kindness_friendship_fairy_tale.py
============================================================================

A small fairy-tale storyworld about two friends, a magical tanker, and a quarrel
that can only be mended by kindness.

The domain rebuilds a simple shape:

    a thirsty place needs water
    -> two friends are trusted with a magical tanker
    -> they quarrel over honor, credit, or control
    -> kindness changes the friendship and the fate of the journey
    -> the ending image shows whether the place revived, barely recovered, or stayed thirsty

Run it
------
    python storyworlds/worlds/gpt-5.4/tanker_conflict_kindness_friendship_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/tanker_conflict_kindness_friendship_fairy_tale.py --destination duck_pond
    python storyworlds/worlds/gpt-5.4/tanker_conflict_kindness_friendship_fairy_tale.py --tanker acorn_tanker --destination duck_pond
    python storyworlds/worlds/gpt-5.4/tanker_conflict_kindness_friendship_fairy_tale.py --kindness snatch
    python storyworlds/worlds/gpt-5.4/tanker_conflict_kindness_friendship_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/tanker_conflict_kindness_friendship_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tanker_conflict_kindness_friendship_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "woman", "fairy"}
        male = {"boy", "king", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {"queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Realm:
    id: str
    opening: str
    road: str
    ruler_type: str
    ruler_label: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TankerCfg:
    id: str
    label: str
    phrase: str
    puller: str
    capacity: int
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DestinationCfg:
    id: str
    label: str
    phrase: str
    place_line: str
    need: int
    revival: str
    sad_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictCfg:
    id: str
    want: str
    quarrel: str
    hurt: int
    tags: set[str] = field(default_factory=set)


@dataclass
class KindnessCfg:
    id: str
    action: str
    speech: str
    soothe: int
    sense: int
    fits: set[str] = field(default_factory=set)
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    realm: str
    tanker: str
    destination: str
    conflict: str
    kindness: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    ruler: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


REALMS = {
    "silver_glen": Realm(
        id="silver_glen",
        opening="Once, in Silver Glen, the grass had turned pale beneath three rainless weeks.",
        road="the silver road that curved past mushroom rings and mossy stones",
        ruler_type="queen",
        ruler_label="the queen",
        closing="After that day, the whole glen remembered that a kind heart can carry more than a full cart.",
        tags={"fairy_tale"},
    ),
    "amber_hollow": Realm(
        id="amber_hollow",
        opening="Once, in Amber Hollow, even the bees hummed softly because the flowers were thirsty.",
        road="the amber lane beneath lantern pears",
        ruler_type="king",
        ruler_label="the king",
        closing="From then on, the hollow told the tale whenever friends forgot how strong gentleness can be.",
        tags={"fairy_tale"},
    ),
    "moonmeadow": Realm(
        id="moonmeadow",
        opening="Once, in Moonmeadow, dew used to shine every morning, but now the fields woke dry and dull.",
        road="the moonlit path between fern arches and sleepy foxgloves",
        ruler_type="queen",
        ruler_label="the queen",
        closing="And ever since, the meadow folk said friendship is brightest when it is watered with kindness.",
        tags={"fairy_tale"},
    ),
}

TANKERS = {
    "acorn_tanker": TankerCfg(
        id="acorn_tanker",
        label="acorn tanker",
        phrase="a little acorn-shaped tanker",
        puller="a cream pony",
        capacity=1,
        shine="Its copper bands glowed like a chestnut in the sun.",
        tags={"tanker", "water"},
    ),
    "blue_tanker": TankerCfg(
        id="blue_tanker",
        label="blue tanker",
        phrase="a bright blue tanker",
        puller="a dappled pony",
        capacity=2,
        shine="Its round sides shone with painted stars.",
        tags={"tanker", "water"},
    ),
    "moon_tanker": TankerCfg(
        id="moon_tanker",
        label="moon tanker",
        phrase="a silver moon tanker",
        puller="a white pony",
        capacity=3,
        shine="Its silver belly held water clear as glass.",
        tags={"tanker", "water"},
    ),
}

DESTINATIONS = {
    "rose_garden": DestinationCfg(
        id="rose_garden",
        label="rose garden",
        phrase="the rose garden beside the gate",
        place_line="The roses had bowed their heads, and even the red ones looked tired.",
        need=2,
        revival="Soon the roses lifted their faces, and soft red petals opened like little flags of thanks.",
        sad_image="Only a few roses stirred, while the rest stayed drooping in the dusty beds.",
        tags={"flowers", "garden", "water"},
    ),
    "duck_pond": DestinationCfg(
        id="duck_pond",
        label="duck pond",
        phrase="the duck pond at the willow bend",
        place_line="The pond had shrunk to a muddy mirror, and the ducks stood around it in puzzled silence.",
        need=3,
        revival="Water spread beneath the willow roots, and the ducks paddled in grateful circles at once.",
        sad_image="A shallow puddle gleamed at the bottom, but the ducks still had nowhere to swim.",
        tags={"pond", "water", "ducks"},
    ),
    "mill_tree": DestinationCfg(
        id="mill_tree",
        label="mill tree",
        phrase="the old mill tree by the streambed",
        place_line="The great tree's leaves hung limp, and its little paper-winged seeds did not dance.",
        need=2,
        revival="The mill tree drank deeply, and its leaves gave a green shiver all the way to the top.",
        sad_image="The roots darkened a little, but the top branches remained still and thirsty.",
        tags={"tree", "water"},
    ),
    "cloud_tulips": DestinationCfg(
        id="cloud_tulips",
        label="cloud tulips",
        phrase="the cloud tulips on the hill",
        place_line="The tulips that usually looked like bits of sunrise had folded themselves shut.",
        need=1,
        revival="The tulips opened again, and the hill looked as if dawn had come down to sit upon it.",
        sad_image="The hill stayed dim, with only one tired bloom half-open in the wind.",
        tags={"flowers", "hill", "water"},
    ),
}

CONFLICTS = {
    "reins": ConflictCfg(
        id="reins",
        want="both wanted to hold the pony's reins",
        quarrel='"I should lead the tanker," one cried, and the other answered, "No, I should!"',
        hurt=2,
        tags={"conflict", "turns"},
    ),
    "first_pour": ConflictCfg(
        id="first_pour",
        want="both wanted to tip the tanker first",
        quarrel='"I will pour the first silver stream," one said, and the other stamped a foot and said the same.',
        hurt=1,
        tags={"conflict", "turns"},
    ),
    "praise": ConflictCfg(
        id="praise",
        want="both wanted the ruler's praise",
        quarrel='"The queen will thank me most," one boasted, and the other answered, "No, it will be me."',
        hurt=3,
        tags={"conflict", "praise"},
    ),
}

KINDNESSES = {
    "take_turns": KindnessCfg(
        id="take_turns",
        action="stopped, took a breath, and offered to take turns",
        speech='"You guide first, and I will pour first at the end after that," came the gentle offer.',
        soothe=2,
        sense=3,
        fits={"reins", "first_pour"},
        qa_text="offered to take turns so both friends had a fair part",
        tags={"kindness", "sharing", "friendship"},
    ),
    "praise_friend": KindnessCfg(
        id="praise_friend",
        action="lowered proud words and praised the other friend out loud",
        speech='"You are careful with the pony, and I am glad I came with you," came the kind answer.',
        soothe=3,
        sense=3,
        fits={"reins", "first_pour", "praise"},
        qa_text="praised the other friend and gave away some of the credit",
        tags={"kindness", "praise", "friendship"},
    ),
    "hold_hands": KindnessCfg(
        id="hold_hands",
        action="reached for the other's hand and suggested they pull together",
        speech='"Let us do it side by side, because the thirsty place needs both of us," came the soft reply.',
        soothe=2,
        sense=3,
        fits={"reins", "first_pour", "praise"},
        qa_text="reached for a hand and asked to work together",
        tags={"kindness", "friendship", "together"},
    ),
    "quiet_apology": KindnessCfg(
        id="quiet_apology",
        action="looked down, whispered an apology, and stepped back from the argument",
        speech='"I was unkind just then. Let us mend it before more water is lost," came the small brave voice.',
        soothe=1,
        sense=2,
        fits={"reins", "first_pour", "praise"},
        qa_text="whispered an apology and tried to mend the quarrel",
        tags={"kindness", "apology", "friendship"},
    ),
    "snatch": KindnessCfg(
        id="snatch",
        action="grabbed at the reins and tried to win by being quicker",
        speech='"If I am fastest, I should have my way," came the sharp answer.',
        soothe=0,
        sense=1,
        fits={"reins", "first_pour", "praise"},
        qa_text="tried to win by snatching instead of being kind",
        tags={"conflict"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nella", "Tessa", "Elsa", "Poppy", "Wren", "Ivy"]
BOY_NAMES = ["Oren", "Milo", "Finn", "Bram", "Tobin", "Ari", "Nico", "Jules"]
TRAITS = ["gentle", "brave", "careful", "quick", "hopeful", "cheerful"]


def tanker_can_help(tanker: TankerCfg, destination: DestinationCfg) -> bool:
    return tanker.capacity >= destination.need


def kindness_fits(conflict: ConflictCfg, kindness: KindnessCfg) -> bool:
    return conflict.id in kindness.fits and kindness.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for realm_id in REALMS:
        for tanker_id, tanker in TANKERS.items():
            for destination_id, destination in DESTINATIONS.items():
                if not tanker_can_help(tanker, destination):
                    continue
                for conflict_id, conflict in CONFLICTS.items():
                    for kindness_id, kindness in KINDNESSES.items():
                        if kindness_fits(conflict, kindness):
                            combos.append((realm_id, tanker_id, destination_id, conflict_id, kindness_id))
    return combos


def spill_amount(conflict: ConflictCfg, kindness: KindnessCfg) -> int:
    return max(0, conflict.hurt - kindness.soothe)


def outcome_of(params: StoryParams) -> str:
    tanker = TANKERS[params.tanker]
    destination = DESTINATIONS[params.destination]
    conflict = CONFLICTS[params.conflict]
    kindness = KINDNESSES[params.kindness]
    spill = spill_amount(conflict, kindness)
    remaining = tanker.capacity - spill
    if spill == 0:
        return "harmony"
    if remaining >= destination.need:
        return "saved"
    return "wilted"


def explain_tanker(tanker: TankerCfg, destination: DestinationCfg) -> str:
    return (
        f"(No story: {tanker.phrase} holds only {tanker.capacity} silver bucket"
        f"{'' if tanker.capacity == 1 else 's'}, but {destination.phrase} needs {destination.need}. "
        "Pick a larger tanker or a less thirsty place.)"
    )


def explain_kindness(kindness: KindnessCfg, conflict: ConflictCfg) -> str:
    if kindness.sense < SENSE_MIN:
        return (
            f"(Refusing kindness '{kindness.id}': it is not kind at all "
            f"(sense={kindness.sense} < {SENSE_MIN}). This world only tells stories "
            "where gentleness is a real attempt to mend the quarrel.)"
        )
    return (
        f"(No story: {kindness.id} does not fit the conflict '{conflict.id}'. "
        "Choose a kinder answer that can honestly soften that quarrel.)"
    )


def introduce(world: World, realm: Realm, ruler: Entity, a: Entity, b: Entity,
              tanker: Entity, destination: Entity, destination_cfg: DestinationCfg,
              tanker_cfg: TankerCfg) -> None:
    world.say(realm.opening)
    world.say(
        f"{ruler.title_word.capitalize()} {ruler.id} sent for two good friends, {a.id} and {b.id}, "
        f"and trusted them with {tanker_cfg.phrase} pulled by {tanker_cfg.puller}."
    )
    world.say(tanker_cfg.shine)
    world.say(
        f'"Carry this tanker along {realm.road} to {destination_cfg.phrase}," '
        f"{ruler.pronoun()} said. {destination_cfg.place_line}"
    )
    destination.meters["thirst"] = float(destination_cfg.need)
    tanker.meters["water"] = float(tanker_cfg.capacity)
    a.memes["friendship"] = 2.0
    b.memes["friendship"] = 2.0
    a.memes["trust"] = 2.0
    b.memes["trust"] = 2.0


def set_off(world: World, a: Entity, b: Entity, conflict_cfg: ConflictCfg) -> None:
    a.memes["hope"] += 1
    b.memes["hope"] += 1
    world.say(
        f"The two friends started down the road together, but before the first bend {conflict_cfg.want}."
    )
    world.say(conflict_cfg.quarrel)


def quarrel(world: World, a: Entity, b: Entity, tanker: Entity, conflict_cfg: ConflictCfg) -> None:
    hurt = float(conflict_cfg.hurt)
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    a.memes["hurt"] += hurt / 2.0
    b.memes["hurt"] += hurt / 2.0
    a.memes["friendship"] = max(0.0, a.memes["friendship"] - 1.0)
    b.memes["friendship"] = max(0.0, b.memes["friendship"] - 1.0)
    world.say(
        "Their words grew sharp. The pony tossed its head, the wheels bumped a stone, "
        "and the tanker rocked from side to side."
    )


def kindness_turn(world: World, a: Entity, b: Entity, kindness_cfg: KindnessCfg, spill: int) -> None:
    a.memes["kindness"] += float(kindness_cfg.soothe)
    b.memes["relief"] += float(kindness_cfg.soothe)
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"Then {a.id} {kindness_cfg.action}. {kindness_cfg.speech}"
    )
    if spill > 0:
        world.say(
            f"But before peace had fully settled, {spill} silver bucket"
            f"{'' if spill == 1 else 's'} of water sloshed out in sparkling sheets."
        )
    else:
        world.say(
            "The pony quieted at once, and not one shining drop was lost."
        )


def travel_on(world: World, a: Entity, b: Entity, tanker: Entity, destination_cfg: DestinationCfg) -> None:
    world.say(
        f"After that, {a.id} and {b.id} walked more softly. Together they guided the tanker toward {destination_cfg.phrase}."
    )


def pour_and_end(world: World, a: Entity, b: Entity, tanker: Entity,
                 destination: Entity, destination_cfg: DestinationCfg,
                 realm: Realm, outcome: str) -> None:
    need = destination.meters["thirst"]
    water = tanker.meters["water"]
    if water >= need:
        destination.meters["bloom"] += 1
        destination.meters["thirst"] = 0.0
        world.say(
            f"When they arrived, they tipped the tanker carefully and let the clear water run where it was needed most."
        )
        world.say(destination_cfg.revival)
        if outcome == "harmony":
            a.memes["friendship"] += 2
            b.memes["friendship"] += 2
            a.memes["joy"] += 1
            b.memes["joy"] += 1
            world.say(
                f"{r'Queen' if world.facts['ruler'].type == 'queen' else 'King'} {world.facts['ruler'].id} smiled to see them laughing together again."
            )
        else:
            a.memes["friendship"] += 1
            b.memes["friendship"] += 1
            world.say(
                f"The work was done, though the memory of the quarrel still felt tender. Even so, the two friends stood shoulder to shoulder beside the flowing water."
            )
    else:
        destination.meters["thirst"] = max(0.0, need - water)
        tanker.meters["water"] = 0.0
        a.memes["sorrow"] += 1
        b.memes["sorrow"] += 1
        world.say(
            "They poured every drop that remained, but the thirsty place could not drink enough."
        )
        world.say(destination_cfg.sad_image)
        world.say(
            f"{a.id} and {b.id} looked at one another with wet eyes, knowing their quarrel had cost the journey dearly."
        )
    world.say(realm.closing)


def tell(realm_cfg: Realm, tanker_cfg: TankerCfg, destination_cfg: DestinationCfg,
         conflict_cfg: ConflictCfg, kindness_cfg: KindnessCfg,
         friend1: str, friend1_gender: str, friend2: str, friend2_gender: str,
         ruler_name: str, trait1: str, trait2: str) -> World:
    world = World()
    a = world.add(Entity(
        id=friend1,
        kind="character",
        type=friend1_gender,
        role="friend1",
        traits=[trait1],
    ))
    b = world.add(Entity(
        id=friend2,
        kind="character",
        type=friend2_gender,
        role="friend2",
        traits=[trait2],
    ))
    ruler = world.add(Entity(
        id=ruler_name,
        kind="character",
        type=realm_cfg.ruler_type,
        role="ruler",
        label=realm_cfg.ruler_label,
    ))
    tanker = world.add(Entity(
        id="tanker",
        type="tanker",
        label=tanker_cfg.label,
        phrase=tanker_cfg.phrase,
        tags=set(tanker_cfg.tags),
    ))
    destination = world.add(Entity(
        id="destination",
        type="place",
        label=destination_cfg.label,
        phrase=destination_cfg.phrase,
        tags=set(destination_cfg.tags),
    ))

    introduce(world, realm_cfg, ruler, a, b, tanker, destination, destination_cfg, tanker_cfg)
    world.para()
    set_off(world, a, b, conflict_cfg)
    quarrel(world, a, b, tanker, conflict_cfg)

    spill = spill_amount(conflict_cfg, kindness_cfg)
    tanker.meters["spill"] = float(spill)
    tanker.meters["water"] = max(0.0, tanker.meters["water"] - spill)

    world.para()
    kindness_turn(world, a, b, kindness_cfg, spill)
    travel_on(world, a, b, tanker, destination_cfg)

    outcome = "harmony"
    if spill > 0 and tanker.meters["water"] >= destination_cfg.need:
        outcome = "saved"
    elif tanker.meters["water"] < destination_cfg.need:
        outcome = "wilted"

    world.para()
    pour_and_end(world, a, b, tanker, destination, destination_cfg, realm_cfg, outcome)

    world.facts.update(
        realm=realm_cfg,
        tanker_cfg=tanker_cfg,
        destination_cfg=destination_cfg,
        conflict_cfg=conflict_cfg,
        kindness_cfg=kindness_cfg,
        friend1=a,
        friend2=b,
        ruler=ruler,
        tanker=tanker,
        destination=destination,
        spill=spill,
        outcome=outcome,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    tanker_cfg = f["tanker_cfg"]
    destination_cfg = f["destination_cfg"]
    conflict_cfg = f["conflict_cfg"]
    kindness_cfg = f["kindness_cfg"]
    outcome = f["outcome"]
    prompts = [
        'Write a fairy tale for a 3-to-5-year-old that includes the word "tanker" and teaches that kindness can mend conflict between friends.',
        f"Tell a gentle fairy tale where two friends, {a.id} and {b.id}, carry {tanker_cfg.phrase} to {destination_cfg.phrase} but quarrel because {conflict_cfg.want}.",
        f"Write a story in which friendship is tested on a journey, and one child {kindness_cfg.qa_text}.",
    ]
    if outcome == "wilted":
        prompts.append(
            "Let the ending be wistful rather than cruel: the lesson should be that unkind quarrels can hurt more than feelings."
        )
    else:
        prompts.append(
            "End with a clear image showing that the thirsty place was saved and the friends have changed."
        )
    return prompts


KNOWLEDGE = {
    "tanker": [
        (
            "What is a tanker?",
            "A tanker is a big container used to carry liquid from one place to another. In this fairy tale, the tanker carries water."
        )
    ],
    "water": [
        (
            "Why do plants and ponds need water?",
            "Plants need water to stay alive and grow, and ponds need water so animals can live there. When water is missing, living things can droop, dry up, or go away."
        )
    ],
    "friendship": [
        (
            "What helps a friendship after an argument?",
            "A friendship can begin to heal when someone listens, apologizes, shares, or speaks kindly. Kind actions show that the friendship matters more than winning."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing words or actions that help someone feel safe, cared for, or included. It is a gentle way of treating other people."
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology tells someone you know you were hurtful and want to mend the wrong. It cannot erase everything at once, but it can begin to repair trust."
        )
    ],
    "sharing": [
        (
            "Why is taking turns fair?",
            "Taking turns is fair because each person gets a chance. It helps people share something important without fighting over it."
        )
    ],
    "pond": [
        (
            "Why do ducks need a pond?",
            "Ducks like ponds because they can swim, splash, and look for food there. A dry pond is not a comfortable home for them."
        )
    ],
    "tree": [
        (
            "Why does a tree droop when it is thirsty?",
            "A thirsty tree does not have enough water to keep its leaves fresh and firm. Its leaves can hang down and lose their springy look."
        )
    ],
    "flowers": [
        (
            "What happens when flowers get water after a dry spell?",
            "Flowers can lift their heads, open their petals, and look bright again. Water helps them stay alive and healthy."
        )
    ],
}
KNOWLEDGE_ORDER = ["tanker", "water", "kindness", "friendship", "apology", "sharing", "pond", "tree", "flowers"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    ruler = f["ruler"]
    tanker_cfg = f["tanker_cfg"]
    destination_cfg = f["destination_cfg"]
    conflict_cfg = f["conflict_cfg"]
    kindness_cfg = f["kindness_cfg"]
    spill = f["spill"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, and {ruler.label} who trusted them with a magical tanker. The journey matters because a thirsty place needed their help."
        ),
        (
            "What problem needed to be solved?",
            f"{destination_cfg.phrase.capitalize()} needed water because the dry spell had made it weak and sad. That is why the friends were sent out with the tanker."
        ),
        (
            f"Why did {a.id} and {b.id} quarrel?",
            f"They quarreled because {conflict_cfg.want}. The conflict mattered because their proud words shook the journey and put the water at risk."
        ),
        (
            "What act of kindness changed the story?",
            f"One friend {kindness_cfg.qa_text}. That kindness softened the quarrel and changed how the rest of the journey felt."
        ),
    ]
    if spill > 0:
        qa.append(
            (
                "What happened to the water while they were arguing?",
                f"{spill} silver bucket{'' if spill == 1 else 's'} of water spilled from the tanker. The loss happened because the quarrel had not fully settled before they moved on."
            )
        )
    else:
        qa.append(
            (
                "Did they lose any water on the road?",
                "No. The kindness came in time, the pony calmed down, and the tanker kept every shining drop."
            )
        )
    if outcome == "harmony":
        qa.append(
            (
                "How did the story end?",
                f"{destination_cfg.phrase.capitalize()} was saved, and the two friends laughed together again. The ending shows that kindness protected both the water and the friendship."
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                "How did the story end?",
                f"The thirsty place was still saved, but the friends had to work carefully after losing some water. Their friendship mended, though more tenderly, because kindness came after the hurt had already begun."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"They poured what was left, but {destination_cfg.phrase} stayed partly thirsty. The ending teaches that a quarrel can cost something real, even after someone finally tries to be kind."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"tanker", "water", "kindness", "friendship"}
    tags |= set(f["destination_cfg"].tags)
    tags |= set(f["kindness_cfg"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="silver_glen",
        tanker="moon_tanker",
        destination="duck_pond",
        conflict="praise",
        kindness="praise_friend",
        friend1="Lina",
        friend1_gender="girl",
        friend2="Milo",
        friend2_gender="boy",
        ruler="Aurelia",
        trait1="gentle",
        trait2="brave",
    ),
    StoryParams(
        realm="amber_hollow",
        tanker="blue_tanker",
        destination="rose_garden",
        conflict="reins",
        kindness="take_turns",
        friend1="Finn",
        friend1_gender="boy",
        friend2="Poppy",
        friend2_gender="girl",
        ruler="Rowan",
        trait1="quick",
        trait2="careful",
    ),
    StoryParams(
        realm="moonmeadow",
        tanker="blue_tanker",
        destination="rose_garden",
        conflict="praise",
        kindness="quiet_apology",
        friend1="Mira",
        friend1_gender="girl",
        friend2="Oren",
        friend2_gender="boy",
        ruler="Selene",
        trait1="hopeful",
        trait2="cheerful",
    ),
    StoryParams(
        realm="silver_glen",
        tanker="acorn_tanker",
        destination="cloud_tulips",
        conflict="first_pour",
        kindness="hold_hands",
        friend1="Ivy",
        friend1_gender="girl",
        friend2="Ari",
        friend2_gender="boy",
        ruler="Aurelia",
        trait1="careful",
        trait2="gentle",
    ),
    StoryParams(
        realm="amber_hollow",
        tanker="moon_tanker",
        destination="mill_tree",
        conflict="reins",
        kindness="hold_hands",
        friend1="Tobin",
        friend1_gender="boy",
        friend2="Wren",
        friend2_gender="girl",
        ruler="Rowan",
        trait1="brave",
        trait2="gentle",
    ),
]


ASP_RULES = r"""
sensible(K) :- kindness(K), sense(K, S), sense_min(M), S >= M.
valid(R, T, D, C, K) :- realm(R), tanker(T), destination(D), conflict(C), kindness(K),
                        capacity(T, Cap), need(D, Need), Cap >= Need,
                        fits(K, C), sensible(K).

spill(0) :- chosen_conflict(C), hurt(C, H), chosen_kindness(K), soothe(K, S), S >= H.
spill(H-S) :- chosen_conflict(C), hurt(C, H), chosen_kindness(K), soothe(K, S), H > S.

remaining(Cap-Sp) :- chosen_tanker(T), capacity(T, Cap), spill(Sp).

outcome(harmony) :- spill(0).
outcome(saved) :- spill(Sp), Sp > 0, chosen_destination(D), need(D, Need), remaining(R), R >= Need.
outcome(wilted) :- chosen_destination(D), need(D, Need), remaining(R), R < Need.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for tid, tanker in TANKERS.items():
        lines.append(asp.fact("tanker", tid))
        lines.append(asp.fact("capacity", tid, tanker.capacity))
    for did, destination in DESTINATIONS.items():
        lines.append(asp.fact("destination", did))
        lines.append(asp.fact("need", did, destination.need))
    for cid, conflict in CONFLICTS.items():
        lines.append(asp.fact("conflict", cid))
        lines.append(asp.fact("hurt", cid, conflict.hurt))
    for kid, kindness in KINDNESSES.items():
        lines.append(asp.fact("kindness", kid))
        lines.append(asp.fact("sense", kid, kindness.sense))
        lines.append(asp.fact("soothe", kid, kindness.soothe))
        for fit in sorted(kindness.fits):
            lines.append(asp.fact("fits", kid, fit))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(k for (k,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_tanker", params.tanker),
            asp.fact("chosen_destination", params.destination),
            asp.fact("chosen_conflict", params.conflict),
            asp.fact("chosen_kindness", params.kindness),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: two friends, a magical tanker, a quarrel, and kindness."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--tanker", choices=TANKERS)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--ruler")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tanker and args.destination:
        tanker = TANKERS[args.tanker]
        destination = DESTINATIONS[args.destination]
        if not tanker_can_help(tanker, destination):
            raise StoryError(explain_tanker(tanker, destination))
    if args.conflict and args.kindness:
        conflict = CONFLICTS[args.conflict]
        kindness = KINDNESSES[args.kindness]
        if not kindness_fits(conflict, kindness):
            raise StoryError(explain_kindness(kindness, conflict))
    if args.kindness and KINDNESSES[args.kindness].sense < SENSE_MIN:
        raise StoryError(explain_kindness(KINDNESSES[args.kindness], CONFLICTS[args.conflict] if args.conflict else CONFLICTS["reins"]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.tanker is None or combo[1] == args.tanker)
        and (args.destination is None or combo[2] == args.destination)
        and (args.conflict is None or combo[3] == args.conflict)
        and (args.kindness is None or combo[4] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, tanker_id, destination_id, conflict_id, kindness_id = rng.choice(sorted(combos))
    friend1_gender = rng.choice(["girl", "boy"])
    friend2_gender = rng.choice(["girl", "boy"])
    friend1 = _pick_name(rng, friend1_gender)
    friend2 = _pick_name(rng, friend2_gender, avoid=friend1)
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice([t for t in TRAITS if t != trait1] or TRAITS)
    realm_cfg = REALMS[realm_id]
    if args.ruler:
        ruler = args.ruler
    else:
        if realm_cfg.ruler_type == "queen":
            ruler = rng.choice(["Aurelia", "Selene", "Marigold"])
        else:
            ruler = rng.choice(["Rowan", "Cedric", "Elm"])
    return StoryParams(
        realm=realm_id,
        tanker=tanker_id,
        destination=destination_id,
        conflict=conflict_id,
        kindness=kindness_id,
        friend1=friend1,
        friend1_gender=friend1_gender,
        friend2=friend2,
        friend2_gender=friend2_gender,
        ruler=ruler,
        trait1=trait1,
        trait2=trait2,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        realm_cfg = REALMS[params.realm]
        tanker_cfg = TANKERS[params.tanker]
        destination_cfg = DESTINATIONS[params.destination]
        conflict_cfg = CONFLICTS[params.conflict]
        kindness_cfg = KINDNESSES[params.kindness]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc.args[0]})") from None

    if not tanker_can_help(tanker_cfg, destination_cfg):
        raise StoryError(explain_tanker(tanker_cfg, destination_cfg))
    if not kindness_fits(conflict_cfg, kindness_cfg):
        raise StoryError(explain_kindness(kindness_cfg, conflict_cfg))

    world = tell(
        realm_cfg=realm_cfg,
        tanker_cfg=tanker_cfg,
        destination_cfg=destination_cfg,
        conflict_cfg=conflict_cfg,
        kindness_cfg=kindness_cfg,
        friend1=params.friend1,
        friend1_gender=params.friend1_gender,
        friend2=params.friend2,
        friend2_gender=params.friend2_gender,
        ruler_name=params.ruler,
        trait1=params.trait1,
        trait2=params.trait2,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))

    py_sensible = {kid for kid, k in KINDNESSES.items() if k.sense >= SENSE_MIN}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible kindness choices match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible kindness choices:")
        print("  python:", sorted(py_sensible))
        print("  ASP   :", sorted(asp_sens))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
            print(f"MISMATCH outcome for {params}: python={py} asp={asp}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        with io.StringIO() as buf:
            old = sys.stdout
            try:
                sys.stdout = buf
                emit(smoke, trace=True, qa=True, header="### smoke test")
            finally:
                sys.stdout = old
        if not smoke.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generation and emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sens = asp_sensible()
        print(f"sensible kindness choices: {', '.join(sens)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, tanker, destination, conflict, kindness) combos:\n")
        for realm_id, tanker_id, destination_id, conflict_id, kindness_id in combos:
            print(f"  {realm_id:12} {tanker_id:13} {destination_id:12} {conflict_id:10} {kindness_id}")
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
            header = (
                f"### {p.friend1} & {p.friend2}: {p.tanker} to {p.destination} "
                f"({p.conflict}, {p.kindness}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
