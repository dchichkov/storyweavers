#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lack_consecutive_mitten_humor_mystery.py
===================================================================

A tiny storyworld about a child solving a silly mitten mystery.

The source tale imagined from the seed is simple:
for several consecutive mornings, one mitten keeps going missing. The child
feels the lack of it in the cold, starts a playful investigation, follows
physical clues, and discovers a funny culprit and hiding spot. The mystery ends
with a found mitten and a changed routine that prevents the problem next time.

Run it
------
    python storyworlds/worlds/gpt-5.4/lack_consecutive_mitten_humor_mystery.py
    python storyworlds/worlds/gpt-5.4/lack_consecutive_mitten_humor_mystery.py --place hallway --culprit puppy --spot boot
    python storyworlds/worlds/gpt-5.4/lack_consecutive_mitten_humor_mystery.py --culprit wind --spot soup_pot   # rejected
    python storyworlds/worlds/gpt-5.4/lack_consecutive_mitten_humor_mystery.py --all
    python storyworlds/worlds/gpt-5.4/lack_consecutive_mitten_humor_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lack_consecutive_mitten_humor_mystery.py --verify
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

# Make shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CLUE_GOAL = 2


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    draft: str
    search_line: str
    ending_image: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    kind: str
    clue: str
    clue_name: str
    motive: str
    reveal: str
    prevention: str
    spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    found_line: str
    silly_image: str
    holders: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    phrase: str
    method: str
    notice: str
    closing: str
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_lack_chill(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    mitten = world.entities.get("mitten")
    if hero is None or mitten is None:
        return out
    if mitten.meters["missing"] < THRESHOLD:
        return out
    sig = ("lack_chill", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["cold_hand"] += 1
    hero.memes["annoyance"] += 1
    out.append("__cold__")
    return out


def _r_clue_suspicion(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("hero")
    if detective is None:
        return out
    if detective.meters["clues"] < THRESHOLD:
        return out
    sig = ("clue_suspicion", detective.id, int(detective.meters["clues"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["curiosity"] += 1
    detective.memes["confidence"] += 1
    out.append("__suspect__")
    return out


def _r_solution_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    mitten = world.entities.get("mitten")
    if hero is None or mitten is None:
        return out
    if mitten.meters["found"] < THRESHOLD:
        return out
    sig = ("solution_relief", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["cold_hand"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="lack_chill", tag="physical", apply=_r_lack_chill),
    Rule(name="clue_suspicion", tag="social", apply=_r_clue_suspicion),
    Rule(name="solution_relief", tag="social", apply=_r_solution_relief),
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


PLACES = {
    "hallway": Place(
        id="hallway",
        label="hallway",
        opening="the little front hallway with a crooked rug and a row of winter hooks",
        draft="A chilly ribbon of air slipped under the front door whenever it opened.",
        search_line="The hallway was full of shoes, scarves, and suspicious corners.",
        ending_image="The mitten sat clipped beside its partner on the hook, looking as if it had finally confessed.",
        affords={"puppy", "wind", "magpie"},
        tags={"winter", "hallway"},
    ),
    "mudroom": Place(
        id="mudroom",
        label="mudroom",
        opening="the busy mudroom where boots thumped and coats puffed on pegs",
        draft="The room smelled like snow, soap, and wet rubber boots.",
        search_line="Every shelf in the mudroom looked like it might be hiding a clue.",
        ending_image="Both mittens rested in the basket together, fluffy and innocent again.",
        affords={"puppy", "dryer", "wind"},
        tags={"winter", "mudroom"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        opening="the glass porch where sunlight made bright squares on the floor",
        draft="Even with the sun, the air near the door had a cold bite.",
        search_line="The porch had plants, boots, and enough odd shadows for a very small mystery.",
        ending_image="The mitten hung warm on the rail, and nobody could walk past without grinning.",
        affords={"magpie", "wind", "puppy"},
        tags={"winter", "porch"},
    ),
}

CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        label="puppy",
        phrase="the round-bellied puppy",
        kind="animal",
        clue="a trail of tiny paw prints",
        clue_name="paw prints",
        motive="it thought the mitten smelled like the hero and also like adventure",
        reveal="The puppy had been proudly rescuing the mitten and carrying it off like treasure.",
        prevention="After that, the mitten basket lived on a high shelf where puppy noses could not reach.",
        spots={"boot", "laundry_basket"},
        tags={"puppy", "animal", "paw_prints"},
    ),
    "wind": Culprit(
        id="wind",
        label="wind",
        phrase="the sneaky hallway wind",
        kind="weather",
        clue="a strip of paper fluttering under the door",
        clue_name="fluttering paper",
        motive="it kept whisking loose things into corners whenever the door opened",
        reveal="It was not a thief with feet at all. It was the wind, doing quiet little swoops through the crack by the door.",
        prevention="After that, they shut the basket lid and tucked the mittens in before opening the door.",
        spots={"umbrella_stand", "coat_sleeve"},
        tags={"wind", "weather", "draft"},
    ),
    "magpie": Culprit(
        id="magpie",
        label="magpie",
        phrase="a shiny-eyed magpie",
        kind="bird",
        clue="one black feather on the sill",
        clue_name="feather",
        motive="it liked soft things and anything that looked interesting from the window",
        reveal="The magpie had slipped in through the cracked window and dragged the mitten away in triumph.",
        prevention="After that, they kept the window latched and laughed every time the bird strutted past outside.",
        spots={"flowerpot", "umbrella_stand"},
        tags={"bird", "feather", "magpie"},
    ),
    "dryer": Culprit(
        id="dryer",
        label="dryer",
        phrase="the rumbling dryer",
        kind="machine",
        clue="a warm thump from behind the laundry door",
        clue_name="warm thump",
        motive="it had gulped the mitten into a hidden lip beside the drum",
        reveal="The dryer had not eaten the mitten on purpose, but it had certainly kept it prisoner.",
        prevention="After that, everyone checked the rubber edge of the dryer before declaring a mitten gone.",
        spots={"dryer_lip", "laundry_basket"},
        tags={"dryer", "laundry", "machine"},
    ),
}

SPOTS = {
    "boot": Spot(
        id="boot",
        label="boot",
        phrase="inside a giant rain boot",
        found_line="The mitten was tucked deep inside a boot like a sleepy red mouse.",
        silly_image="When it came out, the puppy barked at it as if the mitten had just returned from sea.",
        holders={"puppy"},
        tags={"boot"},
    ),
    "laundry_basket": Spot(
        id="laundry_basket",
        label="laundry basket",
        phrase="under a heap of warm laundry",
        found_line="The mitten was hiding under socks and pajamas, squashed but perfectly fine.",
        silly_image="A sock fell on the helper's head, which made the detective laugh so hard the mystery nearly solved itself.",
        holders={"puppy", "dryer"},
        tags={"laundry"},
    ),
    "umbrella_stand": Spot(
        id="umbrella_stand",
        label="umbrella stand",
        phrase="in the tall umbrella stand",
        found_line="The mitten had slipped all the way into the umbrella stand and was peeking out between two umbrellas.",
        silly_image="It looked so serious there that the helper saluted it before pulling it free.",
        holders={"wind", "magpie"},
        tags={"umbrella"},
    ),
    "coat_sleeve": Spot(
        id="coat_sleeve",
        label="coat sleeve",
        phrase="up the long sleeve of a winter coat",
        found_line="The mitten had sailed up a coat sleeve and lodged near the elbow.",
        silly_image="When the coat was lifted, the mitten plopped out onto the rug like a tiny, fuzzy suspect.",
        holders={"wind"},
        tags={"coat"},
    ),
    "flowerpot": Spot(
        id="flowerpot",
        label="flowerpot",
        phrase="behind the biggest flowerpot",
        found_line="The mitten was crumpled behind the flowerpot, half hidden under a fallen leaf.",
        silly_image="The magpie glared from the railing as if it wanted the case reopened.",
        holders={"magpie"},
        tags={"flowerpot"},
    ),
    "dryer_lip": Spot(
        id="dryer_lip",
        label="dryer lip",
        phrase="caught in the rubber lip of the dryer",
        found_line="The mitten was pinched in the dryer's rubber edge, warm and embarrassed.",
        silly_image="When it slid free, everyone agreed that even a dryer could look guilty.",
        holders={"dryer"},
        tags={"dryer"},
    ),
}

HELPERS = {
    "mother": Helper(
        id="mother",
        label="mom",
        type="mother",
        phrase="Mom",
        method="knelt down and suggested making a real detective list before anyone blamed the furniture",
        notice="Mom was good at noticing small things that other people stepped right past",
        closing='Mom said, "A mystery is smaller when you look in the silliest place first."',
        tags={"parent"},
    ),
    "father": Helper(
        id="father",
        label="dad",
        type="father",
        phrase="Dad",
        method="rubbed his chin and announced himself assistant detective, even though he was wearing toast crumbs on his sweater",
        notice="Dad liked to make deep detective noises while he searched, but he did notice useful clues",
        closing='Dad said, "Case closed, and nobody even had to question the lamp."',
        tags={"parent"},
    ),
    "grandma": Helper(
        id="grandma",
        label="grandma",
        type="woman",
        phrase="Grandma",
        method="put on her reading glasses and declared that every great mystery deserved careful peeking under ridiculous objects",
        notice="Grandma noticed odd details, especially ones near baskets, boots, and coat hems",
        closing='Grandma chuckled and said, "The mitten was not lost. It was simply living a dramatic life."',
        tags={"family"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Clara"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Noah", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "curious", "bouncy", "thoughtful", "cheerful", "nosy"]


def culprit_fits(place: Place, culprit: Culprit) -> bool:
    return culprit.id in place.affords


def spot_fits(culprit: Culprit, spot: Spot) -> bool:
    return culprit.id in spot.holders and spot.id in culprit.spots


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for culprit_id, culprit in CULPRITS.items():
            if not culprit_fits(place, culprit):
                continue
            for spot_id, spot in SPOTS.items():
                if spot_fits(culprit, spot):
                    combos.append((place_id, culprit_id, spot_id))
    return combos


def predict_case(place: Place, culprit: Culprit, spot: Spot) -> dict:
    return {
        "plausible": culprit_fits(place, culprit) and spot_fits(culprit, spot),
        "clues": 2 if culprit_fits(place, culprit) and spot_fits(culprit, spot) else 0,
        "solveable": culprit_fits(place, culprit) and spot_fits(culprit, spot),
    }


def introduce(world: World, hero: Entity, helper: Entity, mitten: Entity, place: Place,
              days_missing: int) -> None:
    hero.memes["love"] += 1
    world.say(
        f"For {days_missing} consecutive mornings, {hero.id} had hurried into {place.opening} and found a strange lack: one warm mitten was there, and the other was gone."
    )
    world.say(place.draft)
    world.say(
        f"{helper.attrs['title']} watched {hero.id} pat pockets, peek under the scarf basket, and make the same surprised face each day."
    )
    world.say(
        f"{hero.id} loved that striped mitten pair, and the cold always found the hand with the missing one."
    )
    mitten.meters["missing"] += 1
    propagate(world, narrate=False)


def cold_problem(world: World, hero: Entity) -> None:
    if hero.meters["cold_hand"] >= THRESHOLD:
        world.say(
            f'"This is not just a lost mitten," {hero.id} said. "This is a case." One hand stayed cozy, but the other felt chilly and offended.'
        )


def recruit_helper(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f'{helper.attrs["title"]} {helper.attrs["method"]}.'
    )
    world.say(
        f"{helper.attrs['title']} promised to help, because {helper.pronoun('subject')} knew the mystery had happened too many times to be an accident."
    )


def first_clue(world: World, hero: Entity, helper: Entity, culprit: Culprit, place: Place) -> None:
    hero.meters["clues"] += 1
    propagate(world, narrate=False)
    world.say(place.search_line)
    world.say(
        f"Then {hero.id} spotted {culprit.clue}."
    )
    world.say(
        f"{helper.attrs['title']} bent close. {helper.attrs['notice']}, and this clue did not belong there by chance."
    )


def second_clue(world: World, hero: Entity, culprit: Culprit, spot: Spot) -> None:
    hero.meters["clues"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That made two clues in a row, and after two clues the case no longer felt like guessing."
    )
    world.say(
        f"{hero.id} followed the trail toward {spot.phrase}, because the clue seemed to point that way."
    )


def accuse_with_humor(world: World, hero: Entity, culprit: Culprit) -> None:
    confidence = world.get("hero").memes["confidence"]
    if confidence >= THRESHOLD:
        world.say(
            f'"Aha," whispered {hero.id}. "Our suspect is {culprit.phrase}." Saying it out loud sounded so silly that even {hero.pronoun("subject")} had to grin.'
        )


def reveal(world: World, hero: Entity, helper: Entity, mitten: Entity,
           culprit: Culprit, spot: Spot) -> None:
    mitten.meters["found"] += 1
    mitten.meters["missing"] = 0.0
    hero.meters["clues"] += 1
    propagate(world, narrate=False)
    world.say(spot.found_line)
    world.say(culprit.reveal)
    world.say(spot.silly_image)
    world.say(
        f"{hero.id} held the mitten up high, and the whole mystery suddenly looked more funny than frightening."
    )


def resolution(world: World, hero: Entity, helper: Entity, culprit: Culprit, place: Place) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f'{helper.attrs["closing"]}'
    )
    world.say(
        f"{culprit.prevention}"
    )
    world.say(
        f"On the next morning, both mittens were waiting together, and {hero.id} marched out with two warm hands and a detective smile."
    )
    world.say(place.ending_image)


def tell(place: Place, culprit: Culprit, spot: Spot, helper_cfg: Helper,
         hero_name: str = "Lily", hero_type: str = "girl", trait: str = "curious",
         days_missing: int = 3) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={
            "title": helper_cfg.phrase,
            "method": helper_cfg.method,
            "notice": helper_cfg.notice,
            "closing": helper_cfg.closing,
        },
    ))
    mitten = world.add(Entity(
        id="mitten",
        kind="thing",
        type="mitten",
        label="mitten",
        phrase="the missing striped mitten",
        role="missing_item",
    ))
    culprit_ent = world.add(Entity(
        id="culprit",
        kind="thing",
        type=culprit.kind,
        label=culprit.label,
        phrase=culprit.phrase,
        role="culprit",
        tags=set(culprit.tags),
    ))
    spot_ent = world.add(Entity(
        id="spot",
        kind="thing",
        type="spot",
        label=spot.label,
        phrase=spot.phrase,
        role="spot",
        tags=set(spot.tags),
    ))

    introduce(world, hero, helper, mitten, place, days_missing)
    cold_problem(world, hero)

    world.para()
    recruit_helper(world, hero, helper)
    first_clue(world, hero, helper, culprit, place)
    second_clue(world, hero, culprit, spot)
    accuse_with_humor(world, hero, culprit)

    world.para()
    reveal(world, hero, helper, mitten, culprit, spot)
    resolution(world, hero, helper, culprit, place)

    world.facts.update(
        hero=hero,
        helper=helper,
        helper_cfg=helper_cfg,
        mitten=mitten,
        culprit=culprit,
        culprit_ent=culprit_ent,
        spot=spot,
        spot_ent=spot_ent,
        place=place,
        days_missing=days_missing,
        clues=int(hero.meters["clues"]),
        solved=mitten.meters["found"] >= THRESHOLD,
        cold_start=hero.meters["cold_hand"] == 0.0,
    )
    return world


@dataclass
class StoryParams:
    place: str
    culprit: str
    spot: str
    helper: str
    name: str
    gender: str
    trait: str
    days_missing: int = 3
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="hallway",
        culprit="puppy",
        spot="boot",
        helper="father",
        name="Leo",
        gender="boy",
        trait="curious",
        days_missing=3,
    ),
    StoryParams(
        place="mudroom",
        culprit="dryer",
        spot="dryer_lip",
        helper="mother",
        name="Mia",
        gender="girl",
        trait="thoughtful",
        days_missing=4,
    ),
    StoryParams(
        place="porch",
        culprit="magpie",
        spot="flowerpot",
        helper="grandma",
        name="Nora",
        gender="girl",
        trait="careful",
        days_missing=3,
    ),
    StoryParams(
        place="hallway",
        culprit="wind",
        spot="coat_sleeve",
        helper="mother",
        name="Ben",
        gender="boy",
        trait="bouncy",
        days_missing=2,
    ),
]


KNOWLEDGE = {
    "mitten": [
        (
            "What is a mitten?",
            "A mitten is a warm hand covering that keeps fingers together inside one soft pocket. Mittens help hands stay warm in cold weather."
        )
    ],
    "winter": [
        (
            "Why do hands feel cold faster without a mitten?",
            "Hands lose heat quickly because they are small and out in the cold air. A mitten traps warmth around the hand."
        )
    ],
    "paw_prints": [
        (
            "What can paw prints tell you?",
            "Paw prints can show that an animal walked through a place. They can also point toward where the animal went next."
        )
    ],
    "draft": [
        (
            "What is a draft by a door?",
            "A draft is a little stream of moving air that slips in through a crack. Light things can flutter or slide when a draft passes."
        )
    ],
    "feather": [
        (
            "Why might a feather be a clue?",
            "A feather can show that a bird was nearby. If a feather turns up in an odd place, it can help explain what happened."
        )
    ],
    "dryer": [
        (
            "Why do small clothes sometimes get stuck near a dryer door?",
            "Soft clothes can catch in the rubber edge or fold near the opening. That can make them seem lost until someone checks carefully."
        )
    ],
}
KNOWLEDGE_ORDER = ["mitten", "winter", "paw_prints", "draft", "feather", "dryer"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper_cfg"]
    culprit = f["culprit"]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the words "lack", "consecutive", and "mitten", with a funny ending.',
        f"Tell a gentle mystery where a child named {hero.label} notices one mitten missing for several consecutive mornings and solves the case with {helper.phrase}.",
        f"Write a playful detective story in which the culprit turns out to be {culprit.phrase}, so the mystery ends with laughter instead of fear.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper_cfg"]
    culprit = f["culprit"]
    spot = f["spot"]
    place = f["place"]
    days = f["days_missing"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who keeps losing one mitten, and {helper.phrase}, who helps solve the mystery. Together they treat the missing mitten like a real case."
        ),
        (
            "What was the mystery?",
            f"For {days} consecutive mornings, one mitten kept disappearing in the {place.label}. That repeated lack of the mitten is what made {hero.label} sure something strange was going on."
        ),
        (
            "Why did the missing mitten matter?",
            f"It mattered because one of {hero.label}'s hands kept getting cold. The problem was small, but it happened again and again, so it felt worth solving."
        ),
        (
            "What clues helped solve the case?",
            f"They found {culprit.clue} and then followed the trail toward {spot.phrase}. Two clear clues in a row made the mystery feel less like guessing and more like real detective work."
        ),
        (
            "Where was the mitten found?",
            f"The mitten was found {spot.phrase}. That hiding place matched the clues they had already noticed."
        ),
        (
            "Who was really taking the mitten, and why?",
            f"It was {culprit.phrase}. {culprit.motive}."
        ),
        (
            "Why is the ending funny instead of scary?",
            f"It is funny because the culprit and hiding place are silly, not dangerous. Once the mitten is found, everyone can laugh at how serious the tiny mystery had seemed."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mitten"} | set(world.place.tags) | set(world.facts["culprit"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Optional[Place], culprit: Optional[Culprit], spot: Optional[Spot]) -> str:
    if place is not None and culprit is not None and not culprit_fits(place, culprit):
        return (
            f"(No story: {culprit.label} is not a reasonable mitten thief in the {place.label}. "
            f"Pick a culprit that fits that place.)"
        )
    if culprit is not None and spot is not None and not spot_fits(culprit, spot):
        return (
            f"(No story: {culprit.label} would not plausibly hide a mitten {spot.phrase}. "
            f"Pick a hiding spot that matches the culprit.)"
        )
    return "(No story: this combination does not make a sensible mitten mystery.)"


ASP_RULES = r"""
fits_place(P, C) :- place(P), culprit(C), affords(P, C).
fits_spot(C, S)  :- culprit(C), spot(S), holds(S, C), prefers(C, S).
valid(P, C, S)   :- fits_place(P, C), fits_spot(C, S).

clues(2)         :- valid_case.
solved           :- valid_case, clues(N), clue_goal(G), N >= G.

valid_case       :- chosen_place(P), chosen_culprit(C), chosen_spot(S), valid(P, C, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for cid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, cid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for sid in sorted(culprit.spots):
            lines.append(asp.fact("prefers", cid, sid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        for cid in sorted(spot.holders):
            lines.append(asp.fact("holds", sid, cid))
    lines.append(asp.fact("clue_goal", CLUE_GOAL))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_spot", params.spot),
    ])
    model = asp.one_model(asp_program(extra, "#show solved/0."))
    return bool(asp.atoms(model, "solved"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        params = resolve_params(default_args, random.Random(123))
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print("Default resolve failed during verify:", err)

    for params in smoke_cases:
        try:
            solved_py = (params.place, params.culprit, params.spot) in py
            solved_asp = asp_solved(params)
            if solved_py != solved_asp:
                rc = 1
                print(
                    f"MISMATCH solved parity for {(params.place, params.culprit, params.spot)}: "
                    f"python={solved_py} asp={solved_asp}"
                )
            sample = generate(params)
            if not sample.story or "mitten" not in sample.story.lower():
                rc = 1
                print("Smoke test failed: story missing or does not mention mitten.")
            _ = sample.to_dict()
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"Smoke generation failed for {params}: {err}")
    if rc == 0:
        print(f"OK: smoke-generated {len(smoke_cases)} stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a funny mitten mystery. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--days-missing", type=int, choices=[2, 3, 4])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.culprit:
        place = PLACES[args.place]
        culprit = CULPRITS[args.culprit]
        if not culprit_fits(place, culprit):
            raise StoryError(explain_rejection(place, culprit, None))
    if args.culprit and args.spot:
        culprit = CULPRITS[args.culprit]
        spot = SPOTS[args.spot]
        if not spot_fits(culprit, spot):
            raise StoryError(explain_rejection(None, culprit, spot))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, culprit_id, spot_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    days_missing = args.days_missing if args.days_missing is not None else rng.choice([2, 3, 4])

    return StoryParams(
        place=place_id,
        culprit=culprit_id,
        spot=spot_id,
        helper=helper_id,
        name=name,
        gender=gender,
        trait=trait,
        days_missing=days_missing,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    place = PLACES[params.place]
    culprit = CULPRITS[params.culprit]
    spot = SPOTS[params.spot]
    helper = HELPERS[params.helper]
    if not culprit_fits(place, culprit) or not spot_fits(culprit, spot):
        raise StoryError(explain_rejection(place, culprit, spot))

    world = tell(
        place=place,
        culprit=culprit,
        spot=spot,
        helper_cfg=helper,
        hero_name=params.name,
        hero_type=params.gender,
        trait=params.trait,
        days_missing=params.days_missing,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a.replace("hero", params.name)) for q, a in story_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, culprit, spot) combos:\n")
        for place, culprit, spot in combos:
            print(f"  {place:8} {culprit:8} {spot}")
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
            header = f"### {p.name}: {p.culprit} in {p.place} hiding the mitten at {p.spot}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
