#!/usr/bin/env python3
"""
storyworlds/worlds/sip_bucket_friend_s_backyard_misunderstanding_nursery_3.py
=============================================================================

A nursery-rhyme-leaning story world about a misunderstanding in a friend's
backyard. A visiting child takes a proper sip from a cup, the host child sees a
watering bucket go low, and a wrong guess briefly tangles their feelings before
they follow concrete clues to the thirsty backyard creature that really drank
the water.

Internal source tale:
    In a friend's backyard, two children carry a bucket to thirsty plants.
    One child takes a sip from a real drink. The other sees the bucket lower
    and mistakenly thinks the child drank the garden water. They play a clue
    game, discover a thirsty animal visitor, give it its own water, refill the
    bucket, and end with the plants lifted and the friendship mended.
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
from typing import Callable, Iterable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt"}
        male = {"boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Area:
    id: str
    label: str
    opening_image: str
    clue_spot: str
    plants: set[str]
    visitors: set[str]


@dataclass(frozen=True)
class Plant:
    id: str
    label: str
    phrase: str
    thirsty_image: str
    watered_image: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Drink:
    id: str
    label: str
    sip_phrase: str
    lip_mark: str
    cup_label: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Visitor:
    id: str
    label: str
    phrase: str
    clue: str
    sound: str
    hideout: str
    repair: str
    own_water_place: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Repair:
    id: str
    label: str
    guards: set[str]
    action: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ChildPair:
    id: str
    hero_name: str
    hero_type: str
    hero_trait: str
    friend_name: str
    friend_type: str
    friend_trait: str


class World:
    def __init__(self, area: Area) -> None:
        self.area = area
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[dict[str, str]] = []
        self.fired: set[tuple[str, str]] = set()
        self.facts: dict[str, object] = {}

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

    def note(self, tag: str, **fields: str) -> None:
        entry = {"tag": tag}
        entry.update({k: str(v) for k, v in fields.items()})
        self.history.append(entry)

    def render(self) -> str:
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

    def copy(self) -> "World":
        clone = World(self.area)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.history = copy.deepcopy(self.history)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], None]


def _r_misunderstanding(world: World) -> None:
    hero = world.entities.get(world.facts.get("hero_id", ""))
    friend = world.entities.get(world.facts.get("friend_id", ""))
    bucket = world.entities.get("bucket")
    if not hero or not friend or not bucket:
        return
    if friend.memes["alarm"] < THRESHOLD:
        return
    if hero.memes["just_sipped"] < THRESHOLD:
        return
    if bucket.meters["water_missing"] < THRESHOLD:
        return
    sig = ("misunderstanding", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["hurt"] += 1.0
    friend.memes["suspicion"] += 1.0
    world.facts["misunderstanding"] = "friend_thought_hero_sipped_bucket"


def _r_clue_softens(world: World) -> None:
    hero = world.entities.get(world.facts.get("hero_id", ""))
    friend = world.entities.get(world.facts.get("friend_id", ""))
    if not hero or not friend or not world.facts.get("clue_found"):
        return
    if friend.memes["suspicion"] < THRESHOLD:
        return
    sig = ("clue_softens", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    friend.memes["suspicion"] = 0.0
    friend.memes["sorry"] += 1.0
    hero.memes["hope"] += 1.0


def _r_garden_relief(world: World) -> None:
    hero = world.entities.get(world.facts.get("hero_id", ""))
    friend = world.entities.get(world.facts.get("friend_id", ""))
    plant = world.entities.get("plant")
    bucket = world.entities.get("bucket")
    if not hero or not friend or not plant or not bucket:
        return
    if not world.facts.get("repair_done"):
        return
    if bucket.meters["water"] < THRESHOLD:
        return
    if plant.meters["thirst"] > 0.0:
        return
    sig = ("garden_relief", plant.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["relief"] += 1.0
    friend.memes["relief"] += 1.0
    hero.memes["trust"] += 1.0
    friend.memes["trust"] += 1.0


CAUSAL_RULES = [
    Rule("misunderstanding", _r_misunderstanding),
    Rule("clue_softens", _r_clue_softens),
    Rule("garden_relief", _r_garden_relief),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        before = (
            tuple(sorted(world.fired)),
            tuple(sorted((eid, tuple(sorted(ent.meters.items())), tuple(sorted(ent.memes.items())))
                         for eid, ent in world.entities.items())),
            tuple(sorted(world.facts.items(), key=lambda item: item[0])),
        )
        for rule in CAUSAL_RULES:
            rule.apply(world)
        after = (
            tuple(sorted(world.fired)),
            tuple(sorted((eid, tuple(sorted(ent.meters.items())), tuple(sorted(ent.memes.items())))
                         for eid, ent in world.entities.items())),
            tuple(sorted(world.facts.items(), key=lambda item: item[0])),
        )
        changed = before != after


AREAS = {
    "pea_patch": Area(
        "pea_patch",
        "the pea patch by the swing",
        "the swing sang squeak-squeak over the soft dirt",
        "the swing post",
        {"peas"},
        {"puppy", "robin"},
    ),
    "strawberry_row": Area(
        "strawberry_row",
        "the strawberry row by the fence",
        "the fence hummed while leaves hid red little hearts",
        "the fence rose",
        {"strawberries"},
        {"robin", "kitten"},
    ),
    "marigold_corner": Area(
        "marigold_corner",
        "the marigold corner near the sandbox",
        "the sandbox rake leaned nearby like a sleepy fiddle",
        "the sandbox bench",
        {"marigolds"},
        {"puppy", "kitten"},
    ),
}

PLANTS = {
    "peas": Plant(
        "peas",
        "the pea vines",
        "small pea vines with curly green hands",
        "looked droopy as drowsy ribbons",
        "lifted their curly hands and looked ready to dance",
        {"plants", "garden"},
    ),
    "strawberries": Plant(
        "strawberries",
        "the strawberry plants",
        "strawberry plants tucked under bright leaves",
        "hung low like sleepy red lanterns",
        "winked red under the leaves again",
        {"plants", "garden", "fruit"},
    ),
    "marigolds": Plant(
        "marigolds",
        "the marigolds",
        "round marigolds with gold button faces",
        "nodded as if the sunshine had made them yawn",
        "stood up bright and button-proud",
        {"plants", "garden", "flowers"},
    ),
}

DRINKS = {
    "mint_lemonade": Drink(
        "mint_lemonade",
        "mint lemonade",
        "a cool minty sip",
        "a shiny green smile on the lip",
        "a striped cup",
        {"drink", "sharing"},
    ),
    "strawberry_milk": Drink(
        "strawberry_milk",
        "strawberry milk",
        "a sweet berry sip",
        "a pink milk moustache",
        "a polka-dot cup",
        {"drink", "sharing"},
    ),
    "pear_juice": Drink(
        "pear_juice",
        "pear juice",
        "a golden juicy sip",
        "a sun-colored drop on the chin",
        "a yellow cup",
        {"drink", "sharing"},
    ),
}

VISITORS = {
    "puppy": Visitor(
        "puppy",
        "Pip the puppy",
        "a speckled puppy from the next yard",
        "muddy comma paw prints beside the bucket",
        "lap-lap-lap",
        "under the bean stool",
        "dog_bowl",
        "the shady fence corner",
        {"pets", "animals", "dog"},
    ),
    "robin": Visitor(
        "robin",
        "Rory the robin",
        "a plump robin with a bright red bib",
        "a red feather bobbing in the water like a tiny boat",
        "dip-dip-dip",
        "beside the little bird stump",
        "bird_saucer",
        "the bird stump",
        {"birds", "animals"},
    ),
    "kitten": Visitor(
        "kitten",
        "Mimi the kitten",
        "a gray kitten with a bell on the collar",
        "tiny whisker bubbles and a silver bell tinkle by the rim",
        "sip-sip-sip",
        "behind the sandbox bench",
        "kitten_dish",
        "the bench shade",
        {"pets", "animals", "cat"},
    ),
}

REPAIRS = {
    "dog_bowl": Repair(
        "dog_bowl",
        "a blue dog bowl",
        {"puppy"},
        "set a blue dog bowl in the shady fence corner and filled it first",
        "The blue bowl glimmered in the shade while the bucket stayed for the plants",
        {"pets", "care"},
    ),
    "bird_saucer": Repair(
        "bird_saucer",
        "a little bird saucer",
        {"robin"},
        "set a little bird saucer on the stump and filled it with fresh water",
        "The saucer shone on the stump while the bucket waited for the roots",
        {"birds", "care"},
    ),
    "kitten_dish": Repair(
        "kitten_dish",
        "a shallow kitten dish",
        {"kitten"},
        "set a shallow kitten dish in the bench shade and filled it gently",
        "The little dish sat by the bench while the bucket kept its garden job",
        {"pets", "care"},
    ),
}

PAIRS = {
    "mia_nell": ChildPair("mia_nell", "Mia", "girl", "curious", "Nell", "girl", "careful"),
    "leo_tess": ChildPair("leo_tess", "Leo", "boy", "gentle", "Tess", "girl", "thoughtful"),
    "ruby_finn": ChildPair("ruby_finn", "Ruby", "girl", "bright", "Finn", "boy", "helpful"),
    "theo_ivy": ChildPair("theo_ivy", "Theo", "boy", "playful", "Ivy", "girl", "tidy"),
    "nora_sam": ChildPair("nora_sam", "Nora", "girl", "cheerful", "Sam", "boy", "steady"),
}


@dataclass
class StoryParams:
    area: str
    plant: str
    drink: str
    visitor: str
    repair: str
    pair: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "plants": [
        (
            "Why do garden plants need water?",
            "Garden plants need water to keep their stems, leaves, and roots working well. When the soil dries too much, the plant can droop and stop looking lively.",
        )
    ],
    "garden": [
        (
            "Why is a watering bucket not the same as a drinking cup?",
            "A watering bucket has a job in the garden, and its water may not be meant for sipping. Keeping garden water separate helps both children and plants get the right kind of care.",
        )
    ],
    "sharing": [
        (
            "Why can it help to ask a question before blaming a friend?",
            "A quick question can uncover the real cause of a problem before feelings get hurt. That gives friends a chance to solve the trouble together instead of guessing wrong.",
        )
    ],
    "pets": [
        (
            "Why might a pet need its own water dish outside?",
            "A pet can get thirsty while it plays in the yard. An easy-to-find water dish helps it drink without taking water from another job.",
        )
    ],
    "birds": [
        (
            "Why might a bird stop for water in a backyard?",
            "Birds can get hot and thirsty, especially on bright days. A small saucer gives them a safe place to drink without splashing through a garden bucket.",
        )
    ],
    "care": [
        (
            "How can one small fix help both animals and plants?",
            "A good fix gives each living thing what it actually needs. Then the animal gets a drink, and the plant keeps the water meant for its roots.",
        )
    ],
}
KNOWLEDGE_ORDER = ["plants", "garden", "sharing", "pets", "birds", "care"]


def area_supports(area: Area, plant: Plant, visitor: Visitor) -> bool:
    return plant.id in area.plants and visitor.id in area.visitors


def repair_works(visitor: Visitor, repair: Repair) -> bool:
    return visitor.id in repair.guards and visitor.repair == repair.id


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for area_id, area in AREAS.items():
        for plant_id in sorted(area.plants):
            plant = PLANTS[plant_id]
            for visitor_id in sorted(area.visitors):
                visitor = VISITORS[visitor_id]
                for drink_id in sorted(DRINKS):
                    for repair_id, repair in REPAIRS.items():
                        if area_supports(area, plant, visitor) and repair_works(visitor, repair):
                            combos.append((area_id, plant_id, drink_id, visitor_id, repair_id))
    return sorted(combos)


def explain_rejection(
    area: Optional[Area] = None,
    plant: Optional[Plant] = None,
    visitor: Optional[Visitor] = None,
    repair: Optional[Repair] = None,
) -> str:
    if area and plant and visitor and not area_supports(area, plant, visitor):
        return (
            f"(No story: {plant.label} and {visitor.label} do not make a grounded fit in "
            f"{area.label}. The backyard clues would feel arbitrary, so this variant is rejected.)"
        )
    if visitor and repair and not repair_works(visitor, repair):
        return (
            f"(No story: {repair.label} does not solve the thirst problem for {visitor.label}. "
            f"The ending would not truly resolve the misunderstanding.)"
        )
    return "(No story: the requested combination is not registered as a grounded backyard variant.)"


def introduce(
    world: World,
    hero: Entity,
    friend: Entity,
    plant_cfg: Plant,
    drink_cfg: Drink,
) -> None:
    area = world.area
    world.say(
        f"Tip-tap morning skipped across {friend.id}'s backyard, where {area.opening_image}. "
        f"{hero.id} came to help {friend.id} in {area.label}."
    )
    world.say(
        f"There stood a tin bucket for {plant_cfg.label}, and {plant_cfg.phrase} "
        f"{plant_cfg.thirsty_image}."
    )
    world.say(
        f"On a little stool sat {drink_cfg.cup_label} of {drink_cfg.label}. "
        f"{hero.id}, a {hero.traits[0]} {hero.type}, took {drink_cfg.sip_phrase} and wore {drink_cfg.lip_mark}."
    )
    world.note(
        "beginning",
        place=area.label,
        hero=hero.id,
        friend=friend.id,
        plant=plant_cfg.label,
        drink=drink_cfg.label,
    )


def visitor_sips(world: World, visitor: Entity) -> None:
    bucket = world.get("bucket")
    visitor.meters["thirst"] = max(0.0, visitor.meters["thirst"] - 1.0)
    bucket.meters["water"] = max(0.0, bucket.meters["water"] - 1.0)
    bucket.meters["water_missing"] += 1.0
    world.note("visitor_sip", visitor=visitor.id, source="bucket")


def misunderstanding_scene(
    world: World,
    hero: Entity,
    friend: Entity,
    plant_cfg: Plant,
) -> None:
    bucket = world.get("bucket")
    friend.memes["alarm"] += 1.0
    hero.memes["just_sipped"] += 1.0
    propagate(world)
    world.para()
    world.say(
        f"Then {friend.id} peeped into the bucket and gave a tiny gasp. "
        f"The water line had slipped low, and {plant_cfg.label} were still waiting for their drink."
    )
    world.say(
        f'"Oh!" said {friend.id}. "Did you take a sip from the bucket, {hero.id}? '
        f'That water was for the roots."'
    )
    world.say(
        f"{hero.id}'s happy face went still. "
        f'"No," {hero.id} said. "I only sipped my own drink."'
    )
    world.note(
        "misunderstanding",
        guess="friend_blames_hero",
        bucket_water=str(bucket.meters["water"]),
        plant=plant_cfg.label,
    )


def investigate_scene(
    world: World,
    hero: Entity,
    friend: Entity,
    visitor_cfg: Visitor,
) -> None:
    world.say(
        f"{hero.id} did not stomp away, and {friend.id} did not fuss again. "
        f"They played the clue game instead of the blame game."
    )
    world.say(
        f"By {world.area.clue_spot}, they found {visitor_cfg.clue}. "
        f"Then they heard {visitor_cfg.sound} nearby, right {visitor_cfg.hideout}."
    )
    world.facts["clue_found"] = visitor_cfg.clue
    propagate(world)
    world.note("clue_found", clue=visitor_cfg.clue, visitor=visitor_cfg.label)


def reveal_scene(
    world: World,
    friend: Entity,
    visitor: Entity,
    visitor_cfg: Visitor,
) -> None:
    world.say(
        f"Out popped {visitor_cfg.label}, thirsty and bright-eyed. "
        f"{visitor.pronoun().capitalize()} had sipped the bucket water while the children were looking at the cups."
    )
    world.say(
        f'{friend.id} blinked hard. "I guessed the wrong thing," {friend.pronoun()} said. '
        f'"I saw the wet lip and the low bucket, and I mixed the clues all up."'
    )
    world.note("reveal", visitor=visitor_cfg.label, cause="thirsty_visitor")


def repair_scene(
    world: World,
    hero: Entity,
    friend: Entity,
    plant: Entity,
    visitor_cfg: Visitor,
    repair_cfg: Repair,
    plant_cfg: Plant,
) -> None:
    bucket = world.get("bucket")
    world.para()
    friend.memes["care"] += 1.0
    hero.memes["kindness"] += 1.0
    world.say(
        f'{friend.id} said, "I am sorry, {hero.id}. Let us fix it the right way." '
        f"Together they {repair_cfg.action} for {visitor_cfg.label}."
    )
    bucket.meters["water"] += 2.0
    bucket.meters["water_missing"] = 0.0
    plant.meters["thirst"] = 0.0
    world.facts["repair_done"] = True
    world.facts["bucket_refilled"] = True
    world.facts["plant_watered"] = True
    propagate(world)
    world.say(
        f"Then they refilled the bucket, tipped a gentle silver rain onto {plant_cfg.label}, "
        f"and soon the plants {plant_cfg.watered_image}."
    )
    world.say(
        f"{repair_cfg.ending_image}. {hero.id} and {friend.id} clinked their cups for one friendly sip, "
        f"and the misunderstanding blew away like a dandelion puff."
    )
    world.note("repair", repair=repair_cfg.label, visitor=visitor_cfg.label, plant=plant_cfg.label)


def tell(params: StoryParams) -> World:
    area = AREAS[params.area]
    plant_cfg = PLANTS[params.plant]
    drink_cfg = DRINKS[params.drink]
    visitor_cfg = VISITORS[params.visitor]
    repair_cfg = REPAIRS[params.repair]
    pair = PAIRS[params.pair]
    if not area_supports(area, plant_cfg, visitor_cfg):
        raise StoryError(explain_rejection(area, plant_cfg, visitor_cfg, repair_cfg))
    if not repair_works(visitor_cfg, repair_cfg):
        raise StoryError(explain_rejection(area, plant_cfg, visitor_cfg, repair_cfg))

    world = World(area)
    hero = world.add(Entity(pair.hero_name, "character", pair.hero_type, role="hero", traits=[pair.hero_trait]))
    friend = world.add(Entity(pair.friend_name, "character", pair.friend_type, role="friend", traits=[pair.friend_trait]))
    plant = world.add(Entity("plant", "plant", "plant", label=plant_cfg.label, phrase=plant_cfg.phrase, role="plant"))
    bucket = world.add(Entity("bucket", "object", "bucket", label="the tin bucket", role="bucket"))
    visitor = world.add(Entity("visitor", "animal", params.visitor, label=visitor_cfg.label, phrase=visitor_cfg.phrase, role="visitor"))

    plant.meters["thirst"] = 1.0
    bucket.meters["water"] = 2.0
    visitor.meters["thirst"] = 1.0
    hero.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0

    world.facts.update(
        hero_id=hero.id,
        friend_id=friend.id,
        place=f"{friend.id}'s backyard",
        area=area.label,
        plant=plant_cfg.label,
        drink=drink_cfg.label,
        visitor=visitor_cfg.label,
        repair=repair_cfg.label,
    )

    introduce(world, hero, friend, plant_cfg, drink_cfg)
    visitor_sips(world, visitor)
    misunderstanding_scene(world, hero, friend, plant_cfg)
    investigate_scene(world, hero, friend, visitor_cfg)
    reveal_scene(world, friend, visitor, visitor_cfg)
    repair_scene(world, hero, friend, plant, visitor_cfg, repair_cfg, plant_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a nursery-rhyme-style story for ages 3 to 5 about a misunderstanding in a friend's backyard.",
        f'Include the seed words "sip" and "bucket", and make the low bucket lead to a wrong guess before a clue-based reveal.',
        f"Tell a gentle backyard story where {world.facts['visitor']} gets proper water, {world.facts['plant']} get watered, and two friends end with a repaired feeling.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(world.facts["hero_id"])
    friend = world.get(world.facts["friend_id"])
    bucket = world.get("bucket")
    plant_cfg = world.facts["plant"]
    visitor_cfg = world.facts["visitor"]
    repair_cfg = world.facts["repair"]
    clue = str(world.facts.get("clue_found", "the clue"))

    return [
        (
            "Where does the story happen, and what are the children trying to do?",
            f"The story happens in {friend.id}'s backyard, in {world.area.label}. The children are trying to use a bucket of water to help {plant_cfg}.",
        ),
        (
            f"Why did {friend.id} think {hero.id} had done something wrong?",
            f"{friend.id} saw the bucket water go low just after {hero.id} took a sip from a real drink. That made {friend.pronoun('object')} guess, too quickly, that {hero.id} had sipped the garden water.",
        ),
        (
            "What clue showed the real cause of the problem?",
            f"They found {clue} and listened carefully near {world.area.clue_spot}. Those clues pointed to {visitor_cfg}, who had really drunk from the bucket.",
        ),
        (
            "How was the misunderstanding fixed?",
            f"{friend.id} apologized after the clue game showed what truly happened. Then both children gave {visitor_cfg} its own water with {repair_cfg}, refilled the bucket, and watered the plants.",
        ),
        (
            "What proves the ending is different from the middle?",
            f"By the end, the bucket is full again instead of low, and the thirsty plants are watered instead of waiting. The friends also share a calm sip together, which shows their feelings have been mended.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    area = AREAS[world.facts["area_key"]] if "area_key" in world.facts else world.area
    _ = area
    plant_cfg = PLANTS[world.facts["plant_key"]] if "plant_key" in world.facts else None
    visitor_cfg = VISITORS[world.facts["visitor_key"]] if "visitor_key" in world.facts else None
    repair_cfg = REPAIRS[world.facts["repair_key"]] if "repair_key" in world.facts else None
    drink_cfg = DRINKS[world.facts["drink_key"]] if "drink_key" in world.facts else None

    tags: set[str] = {"sharing"}
    if plant_cfg is not None:
        tags.update(plant_cfg.tags)
    if visitor_cfg is not None:
        tags.update(visitor_cfg.tags)
    if repair_cfg is not None:
        tags.update(repair_cfg.tags)
    if drink_cfg is not None:
        tags.update(drink_cfg.tags)

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
    lines.append("== (2) Story questions -- answerable from this story ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, not tied to one telling ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:7}) {' '.join(bits)}")
    lines.append("  history:")
    for item in world.history:
        details = ", ".join(f"{k}={v}" for k, v in item.items() if k != "tag")
        lines.append(f"    - {item['tag']}: {details}")
    lines.append(f"  fired rules: {sorted(name for name, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pea_patch", "peas", "mint_lemonade", "puppy", "dog_bowl", "mia_nell"),
    StoryParams("pea_patch", "peas", "pear_juice", "robin", "bird_saucer", "leo_tess"),
    StoryParams("strawberry_row", "strawberries", "strawberry_milk", "robin", "bird_saucer", "ruby_finn"),
    StoryParams("strawberry_row", "strawberries", "mint_lemonade", "kitten", "kitten_dish", "theo_ivy"),
    StoryParams("marigold_corner", "marigolds", "pear_juice", "puppy", "dog_bowl", "nora_sam"),
    StoryParams("marigold_corner", "marigolds", "strawberry_milk", "kitten", "kitten_dish", "mia_nell"),
]


ASP_RULES = r"""
valid(A,P,D,V,R) :- area_plant(A,P), area_visitor(A,V), drink(D), repair_for(V,R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for area_id, area in AREAS.items():
        lines.append(asp.fact("area", area_id))
        for plant_id in sorted(area.plants):
            lines.append(asp.fact("area_plant", area_id, plant_id))
        for visitor_id in sorted(area.visitors):
            lines.append(asp.fact("area_visitor", area_id, visitor_id))
    for plant_id in sorted(PLANTS):
        lines.append(asp.fact("plant", plant_id))
    for drink_id in sorted(DRINKS):
        lines.append(asp.fact("drink", drink_id))
    for visitor_id, visitor in VISITORS.items():
        lines.append(asp.fact("visitor", visitor_id))
        lines.append(asp.fact("repair_for", visitor_id, visitor.repair))
    for repair_id in sorted(REPAIRS):
        lines.append(asp.fact("repair", repair_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/5.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def verify_story_sample(sample: StorySample) -> None:
    story = sample.story.lower()
    if "bucket" not in story:
        raise StoryError("(Verify failed: story text must include 'bucket'.)")
    if "sip" not in story:
        raise StoryError("(Verify failed: story text must include 'sip'.)")
    if sample.story.count("\n\n") < 2:
        raise StoryError("(Verify failed: story should have a beginning, turn, and ending paragraph.)")
    if len(sample.story_qa) < 4:
        raise StoryError("(Verify failed: story QA is too thin.)")
    if len(sample.world_qa) < 3:
        raise StoryError("(Verify failed: world-knowledge QA is too thin.)")


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set != clingo_set:
        print("MISMATCH between ASP and Python valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in asp:", sorted(clingo_set - python_set))
        return 1

    exercised = 0
    pair_ids = sorted(PAIRS)
    for idx, combo in enumerate(sorted(python_set)):
        params = StoryParams(*combo, pair_ids[idx % len(pair_ids)], seed=idx)
        sample = generate(params)
        verify_story_sample(sample)
        exercised += 1
    print(f"OK: ASP gate matches Python gate ({len(python_set)} combos).")
    print(f"OK: Exercised {exercised} generated stories through the full world model.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a nursery-rhyme misunderstanding with a sip, a bucket, and a friend's backyard."
    )
    ap.add_argument("--area", choices=AREAS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random()
    if args.area and args.plant and args.visitor:
        area = AREAS[args.area]
        plant = PLANTS[args.plant]
        visitor = VISITORS[args.visitor]
        if not area_supports(area, plant, visitor):
            raise StoryError(explain_rejection(area, plant, visitor))
    if args.visitor and args.repair:
        visitor = VISITORS[args.visitor]
        repair = REPAIRS[args.repair]
        if not repair_works(visitor, repair):
            raise StoryError(explain_rejection(visitor=visitor, repair=repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.area is None or combo[0] == args.area)
        and (args.plant is None or combo[1] == args.plant)
        and (args.drink is None or combo[2] == args.drink)
        and (args.visitor is None or combo[3] == args.visitor)
        and (args.repair is None or combo[4] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid backyard combination matches the given options.)")

    area_id, plant_id, drink_id, visitor_id, repair_id = rng.choice(sorted(combos))
    pair_id = args.pair or rng.choice(sorted(PAIRS))
    return StoryParams(area_id, plant_id, drink_id, visitor_id, repair_id, pair_id)


def generate(params: StoryParams) -> StorySample:
    area = AREAS[params.area]
    plant = PLANTS[params.plant]
    visitor = VISITORS[params.visitor]
    repair = REPAIRS[params.repair]
    if not area_supports(area, plant, visitor):
        raise StoryError(explain_rejection(area, plant, visitor, repair))
    if not repair_works(visitor, repair):
        raise StoryError(explain_rejection(area, plant, visitor, repair))

    world = tell(params)
    world.facts["area_key"] = params.area
    world.facts["plant_key"] = params.plant
    world.facts["drink_key"] = params.drink
    world.facts["visitor_key"] = params.visitor
    world.facts["repair_key"] = params.repair
    world.facts["pair_key"] = params.pair
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(dump_trace(sample.world))
    if args.qa:
        print()
        print(format_qa(sample))


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        data = [s.to_dict() for s in samples]
        print(json.dumps(data[0] if len(data) == 1 else data, indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples, 1):
        header = f"--- story {idx} ---" if len(samples) > 1 else None
        emit(sample, args, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StoryError as exc:
        print(exc)
        raise SystemExit(2)
