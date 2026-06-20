#!/usr/bin/env python3
"""
storyworlds/worlds/sip_bucket_friend_s_backyard_misunderstanding_nursery_5.py
=============================================================================

A small nursery-rhyme-style storyworld about a misunderstanding in a friend's
backyard.

Internal source tale:
    A visiting child comes to a friend's backyard to help water a little garden
    patch. The visitor carries a sweet cup and takes a sip while a thirsty
    backyard animal quietly drinks from the bucket. The friend hears the sip
    and sees the bucket grow lighter, so the friend wrongly blames the child.
    The children follow physical clues, find the thirsty animal, make a proper
    water place for it, refill the bucket, and end with watered plants and
    mended trust.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class BackyardArea:
    key: str
    label: str
    opening_image: str
    clue_place: str
    plant_name: str
    plant_need: str
    path_note: str
    visitor_options: tuple[str, ...]
    repair_options: tuple[str, ...]


@dataclass(frozen=True)
class DrinkOption:
    key: str
    label: str
    cup_phrase: str
    taste_note: str
    color: str


@dataclass(frozen=True)
class Visitor:
    key: str
    label: str
    kind: str
    sound: str
    proof: str
    trail: str
    hideout: str
    water_need: str
    own_water_place: str
    compatible_repairs: tuple[str, ...]


@dataclass(frozen=True)
class RepairMethod:
    key: str
    label: str
    action_phrase: str
    place_phrase: str
    ending_image: str
    compatible_areas: tuple[str, ...]


@dataclass(frozen=True)
class ChildPair:
    key: str
    hero_name: str
    hero_kind: str
    hero_trait: str
    friend_name: str
    friend_kind: str
    friend_trait: str


@dataclass
class StoryParams:
    pair: str
    area: str
    drink: str
    visitor: str
    repair: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    role: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "sister"}
        male = {"boy", "father", "man", "uncle", "brother"}
        if self.kind in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    params: StoryParams
    pair: ChildPair
    area: BackyardArea
    drink: DrinkOption
    visitor: Visitor
    repair: RepairMethod
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str | float | bool] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.role] = entity
        return entity

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(
            "  params="
            f"pair:{self.params.pair} area:{self.params.area} drink:{self.params.drink} "
            f"visitor:{self.params.visitor} repair:{self.params.repair} seed:{self.params.seed}"
        )
        for role, entity in self.entities.items():
            rows.append(
                f"  {role}={entity.name}<{entity.kind}> "
                f"traits={entity.traits} meters={entity.meters} memes={entity.memes}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append("  history=")
        for entry in self.history:
            rows.append(f"    {entry}")
        return "\n".join(rows)


AREAS: dict[str, BackyardArea] = {
    "tulip_turn": BackyardArea(
        key="tulip_turn",
        label="the tulip turn by the rain barrel",
        opening_image="red tulips bobbed in a ring while the rain barrel winked in the sun",
        clue_place="the damp brick by the rain barrel",
        plant_name="the tulips",
        plant_need="sleepy heads that leaned for a drink",
        path_note="a curved brick path that clicked under small shoes",
        visitor_options=("duckling", "hedgehog"),
        repair_options=("mint_pan", "stone_saucer"),
    ),
    "pea_patch": BackyardArea(
        key="pea_patch",
        label="the pea patch beside the low bench",
        opening_image="pea vines curled like green ribbons around little sticks",
        clue_place="the dusty patch beside the low bench",
        plant_name="the pea vines",
        plant_need="curled leaves that needed cool water",
        path_note="a neat dirt strip with room for skipping toes",
        visitor_options=("hedgehog", "kitten"),
        repair_options=("stone_saucer", "bench_bowl"),
    ),
    "marigold_gate": BackyardArea(
        key="marigold_gate",
        label="the marigold gate near the back fence",
        opening_image="gold marigolds made a bright little gate in the breeze",
        clue_place="the shady patch under the marigold gate",
        plant_name="the marigolds",
        plant_need="warm petals and thirsty roots after noon",
        path_note="a grassy lane with one flat stepping stone in the middle",
        visitor_options=("duckling", "kitten"),
        repair_options=("mint_pan", "bench_bowl"),
    ),
}


DRINKS: dict[str, DrinkOption] = {
    "pear_tea": DrinkOption(
        key="pear_tea",
        label="pear tea",
        cup_phrase="a little cup of pear tea",
        taste_note="sweet like warm pears",
        color="pale amber",
    ),
    "berry_milk": DrinkOption(
        key="berry_milk",
        label="berry milk",
        cup_phrase="a tiny cup of berry milk",
        taste_note="soft and berry-sweet",
        color="blush pink",
    ),
    "honey_water": DrinkOption(
        key="honey_water",
        label="honey water",
        cup_phrase="a striped cup of honey water",
        taste_note="light and honey-sweet",
        color="golden clear",
    ),
}


VISITORS: dict[str, Visitor] = {
    "duckling": Visitor(
        key="duckling",
        label="duckling",
        kind="bird",
        sound="quack-quick, quack-quick",
        proof="two webbed prints and a bright bead of water on the bucket lip",
        trail="a dab-dab line of webbed prints",
        hideout="the mint tuft by the fence",
        water_need="a shallow place where a small bill can dab",
        own_water_place="a shallow pan under the mint",
        compatible_repairs=("mint_pan",),
    ),
    "hedgehog": Visitor(
        key="hedgehog",
        label="hedgehog",
        kind="animal",
        sound="sniff-sniff",
        proof="tiny nose dots on the rim and prickly leaf bits by the handle",
        trail="small oval prints in the dust",
        hideout="the leaf pile near the stepping stone",
        water_need="a low saucer close to the ground",
        own_water_place="a low saucer beside the warm stone",
        compatible_repairs=("stone_saucer",),
    ),
    "kitten": Visitor(
        key="kitten",
        label="kitten",
        kind="animal",
        sound="mew-mew",
        proof="four neat paw marks and one silver whisker by the bucket handle",
        trail="soft paw prints in a little half-moon trail",
        hideout="the crate tucked under the bench",
        water_need="a quiet bowl where whiskers can bend without fear",
        own_water_place="a quiet bowl under the bench edge",
        compatible_repairs=("bench_bowl",),
    ),
}


REPAIRS: dict[str, RepairMethod] = {
    "mint_pan": RepairMethod(
        key="mint_pan",
        label="set a pan under the mint",
        action_phrase="set a shallow pan under the mint and filled it with clean water",
        place_phrase="under the mint by the fence",
        ending_image="The duckling dabbed from the pan, and the bucket stayed for garden work instead of thirsty pecks.",
        compatible_areas=("tulip_turn", "marigold_gate"),
    ),
    "stone_saucer": RepairMethod(
        key="stone_saucer",
        label="set a saucer by the warm stone",
        action_phrase="set a low saucer by the warm stone and filled it with clean water",
        place_phrase="by the warm stepping stone",
        ending_image="The hedgehog drank from the saucer and left the bucket standing still and full enough for petals and peas.",
        compatible_areas=("tulip_turn", "pea_patch"),
    ),
    "bench_bowl": RepairMethod(
        key="bench_bowl",
        label="set a bowl under the bench",
        action_phrase="set a small bowl under the bench and filled it with clean water",
        place_phrase="under the low bench",
        ending_image="The kitten bent its whiskers to the bowl and stopped padding toward the bucket.",
        compatible_areas=("pea_patch", "marigold_gate"),
    ),
}


CHILD_PAIRS: dict[str, ChildPair] = {
    "ada_finn": ChildPair(
        key="ada_finn",
        hero_name="Ada",
        hero_kind="girl",
        hero_trait="springy",
        friend_name="Finn",
        friend_kind="boy",
        friend_trait="careful",
    ),
    "mila_joel": ChildPair(
        key="mila_joel",
        hero_name="Mila",
        hero_kind="girl",
        hero_trait="sunny",
        friend_name="Joel",
        friend_kind="boy",
        friend_trait="steady",
    ),
    "niko_rosa": ChildPair(
        key="niko_rosa",
        hero_name="Niko",
        hero_kind="boy",
        hero_trait="merry",
        friend_name="Rosa",
        friend_kind="girl",
        friend_trait="watchful",
    ),
    "tara_wes": ChildPair(
        key="tara_wes",
        hero_name="Tara",
        hero_kind="girl",
        hero_trait="gentle",
        friend_name="Wes",
        friend_kind="boy",
        friend_trait="earnest",
    ),
}


def valid_combo(area_key: str, visitor_key: str, repair_key: str) -> bool:
    if area_key not in AREAS or visitor_key not in VISITORS or repair_key not in REPAIRS:
        return False
    area = AREAS[area_key]
    visitor = VISITORS[visitor_key]
    repair = REPAIRS[repair_key]
    return (
        visitor_key in area.visitor_options
        and repair_key in area.repair_options
        and repair_key in visitor.compatible_repairs
        and area_key in repair.compatible_areas
    )


def invalid_reason(area_key: str, visitor_key: str, repair_key: str) -> str:
    if area_key not in AREAS:
        return f"No story: unknown backyard area {area_key!r}."
    if visitor_key not in VISITORS:
        return f"No story: unknown visitor {visitor_key!r}."
    if repair_key not in REPAIRS:
        return f"No story: unknown repair {repair_key!r}."

    area = AREAS[area_key]
    visitor = VISITORS[visitor_key]
    repair = REPAIRS[repair_key]

    if visitor_key not in area.visitor_options:
        return (
            f"No story: {visitor.label} does not fit {area.label}. "
            f"Try one of: {', '.join(area.visitor_options)}."
        )
    if repair_key not in area.repair_options:
        return (
            f"No story: {repair.label} does not fit {area.label}. "
            f"Try one of: {', '.join(area.repair_options)}."
        )
    if repair_key not in visitor.compatible_repairs:
        return (
            f"No story: a {visitor.label} is not reasonably helped by {repair.label}. "
            f"Try one of: {', '.join(visitor.compatible_repairs)}."
        )
    if area_key not in repair.compatible_areas:
        return (
            f"No story: {repair.label} is not placed naturally in {area.label}. "
            f"Try one of: {', '.join(repair.compatible_areas)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for area_key in sorted(AREAS):
        for visitor_key in sorted(VISITORS):
            for repair_key in sorted(REPAIRS):
                if valid_combo(area_key, visitor_key, repair_key):
                    combos.append((area_key, visitor_key, repair_key))
    return combos


def _make_params(
    args: argparse.Namespace,
    rng: random.Random,
    combo: tuple[str, str, str],
    seed: int | None,
) -> StoryParams:
    pair_key = args.pair or rng.choice(sorted(CHILD_PAIRS))
    drink_key = args.drink or rng.choice(sorted(DRINKS))
    area_key, visitor_key, repair_key = combo
    return StoryParams(
        pair=pair_key,
        area=area_key,
        drink=drink_key,
        visitor=visitor_key,
        repair=repair_key,
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.area is None or combo[0] == args.area)
        and (args.visitor is None or combo[1] == args.visitor)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        area_key = args.area or next(iter(AREAS))
        visitor_key = args.visitor or next(iter(VISITORS))
        repair_key = args.repair or next(iter(REPAIRS))
        raise StoryError(invalid_reason(area_key, visitor_key, repair_key))
    story_seed = getattr(rng, "story_seed", None)
    return _make_params(args, rng, rng.choice(combos), story_seed)


def _record(world: World, tag: str, **fields: str) -> None:
    row = {"tag": tag}
    row.update({key: str(value) for key, value in fields.items()})
    world.history.append(row)


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.area, params.visitor, params.repair):
        raise StoryError(invalid_reason(params.area, params.visitor, params.repair))

    pair = CHILD_PAIRS[params.pair]
    area = AREAS[params.area]
    drink = DRINKS[params.drink]
    visitor = VISITORS[params.visitor]
    repair = REPAIRS[params.repair]
    world = World(
        params=params,
        pair=pair,
        area=area,
        drink=drink,
        visitor=visitor,
        repair=repair,
    )

    hero = world.add(
        Entity(
            name=pair.hero_name,
            kind=pair.hero_kind,
            role="hero",
            traits=[pair.hero_trait, "helpful"],
            meters={"steps": 0.0, "cup_level": 1.0},
            memes={"trust": 1.0, "care": 1.1, "hurt": 0.0, "relief": 0.0},
        )
    )
    friend = world.add(
        Entity(
            name=pair.friend_name,
            kind=pair.friend_kind,
            role="friend",
            traits=[pair.friend_trait, "garden-proud"],
            meters={"steps": 0.0},
            memes={"trust": 1.0, "care": 1.1, "suspicion": 0.0, "regret": 0.0},
        )
    )
    bucket = world.add(
        Entity(
            name="watering bucket",
            kind="bucket",
            role="bucket",
            traits=["blue", "tinny"],
            meters={"water": 3.2, "missing": 0.0},
            memes={},
        )
    )
    cup = world.add(
        Entity(
            name=drink.cup_phrase,
            kind="cup",
            role="cup",
            traits=[drink.color],
            meters={"drink_level": 1.0},
            memes={},
        )
    )
    plants = world.add(
        Entity(
            name=area.plant_name,
            kind="plants",
            role="plants",
            traits=["thirsty"],
            meters={"thirst": 2.1},
            memes={"relief": 0.0},
        )
    )
    backyard_visitor = world.add(
        Entity(
            name=visitor.label,
            kind=visitor.kind,
            role="visitor",
            traits=["thirsty", "shy"],
            meters={"thirst": 2.0},
            memes={"fear": 0.5, "calm": 0.0},
        )
    )

    world.facts.update(
        {
            "setting": f"{friend.name}'s backyard",
            "sip_word": "sip",
            "misunderstanding": False,
            "clue_found": False,
            "visitor_found": False,
            "repair_done": False,
            "apology_given": False,
            "garden_watered": False,
            "seed": params.seed if params.seed is not None else "",
        }
    )

    _record(
        world,
        "opening",
        setting=world.facts["setting"],
        area=area.label,
        path=area.path_note,
        plants=area.plant_name,
        need=area.plant_need,
    )

    hero.meters["steps"] += 2.0
    friend.meters["steps"] += 2.0
    _record(
        world,
        "garden_start",
        hero=hero.name,
        friend=friend.name,
        bucket=bucket.name,
        plants=plants.name,
    )

    cup.meters["drink_level"] -= 0.25
    hero.meters["cup_level"] = cup.meters["drink_level"]
    hero.memes["relief"] += 0.2
    _record(
        world,
        "hero_sip",
        actor=hero.name,
        source=drink.cup_phrase,
        taste=drink.taste_note,
    )

    bucket.meters["water"] -= 0.9
    bucket.meters["missing"] += 0.9
    backyard_visitor.meters["thirst"] -= 0.7
    _record(
        world,
        "visitor_drink",
        visitor=backyard_visitor.name,
        proof=visitor.proof,
        trail=visitor.trail,
        hideout=visitor.hideout,
    )

    if cup.meters["drink_level"] < 1.0 and bucket.meters["missing"] > 0.0:
        friend.memes["suspicion"] = 1.1
        friend.memes["trust"] = 0.4
        hero.memes["hurt"] = 0.8
        world.facts["misunderstanding"] = True
        _record(
            world,
            "misunderstanding",
            accuser=friend.name,
            accused=hero.name,
            guess="bucket sip",
        )

    world.facts["clue_found"] = True
    world.facts["visitor_found"] = True
    friend.memes["suspicion"] = 0.0
    friend.memes["regret"] = 1.0
    hero.memes["hurt"] = 0.2
    hero.memes["trust"] = 1.1
    _record(
        world,
        "clue_found",
        proof=visitor.proof,
        place=area.clue_place,
        trail=visitor.trail,
    )
    _record(
        world,
        "visitor_found",
        visitor=visitor.label,
        sound=visitor.sound,
        hideout=visitor.hideout,
    )

    world.facts["apology_given"] = True
    _record(world, "apology", speaker=friend.name, listener=hero.name)

    backyard_visitor.meters["thirst"] = 0.0
    backyard_visitor.memes["fear"] = 0.1
    backyard_visitor.memes["calm"] = 1.0
    bucket.meters["water"] = 3.2
    bucket.meters["missing"] = 0.0
    plants.meters["thirst"] = 0.0
    plants.memes["relief"] = 1.0
    hero.memes["relief"] = 1.0
    hero.memes["trust"] = 1.3
    friend.memes["trust"] = 1.25
    world.facts["repair_done"] = True
    world.facts["garden_watered"] = True
    _record(
        world,
        "repair",
        action=repair.action_phrase,
        place=repair.place_phrase,
        water_place=visitor.own_water_place,
    )
    _record(
        world,
        "garden_finish",
        plants=plants.name,
        bucket_level=str(bucket.meters["water"]),
        ending=repair.ending_image,
    )
    return world


def _render_story(world: World) -> str:
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    bucket = world.entities["bucket"]
    cup = world.entities["cup"]
    plants = world.entities["plants"]
    visitor = world.entities["visitor"]
    area = world.area
    drink = world.drink
    repair = world.repair

    opening = (
        f"In {friend.name}'s backyard, by {area.label}, {hero.name} and {friend.name} "
        f"went step-and-stop along {area.path_note}. {area.opening_image[:1].upper()}"
        f"{area.opening_image[1:]}, and {plants.name} waited with {area.plant_need}."
    )
    sip_scene = (
        f"{hero.name} carried {cup.name} that tasted {drink.taste_note}. "
        f"{hero.pronoun('subject').capitalize()} took one small sip from the cup while "
        f"{friend.name} steadied the {bucket.name}."
    )
    misunderstanding = (
        f"Just then the water line dropped low, and {friend.name} cried, "
        f"\"Was that a bucket sip, {hero.name}?\" The question landed wrong and made "
        f"{hero.name}'s face go still."
    )
    clue_scene = (
        f"But by {area.clue_place} they found {world.visitor.proof}, then followed "
        f"{world.visitor.trail}. From {world.visitor.hideout} came {world.visitor.sound}, "
        f"and the muddle began to melt."
    )
    turn_scene = (
        f"It was the thirsty {visitor.name}, needing {world.visitor.water_need}. "
        f"{friend.name} said sorry right away, and together the children {repair.action_phrase}."
    )
    ending = (
        f"Then they filled the {bucket.name} again and watered {plants.name}. "
        "Sip for the cup, slosh for the bucket, sing it soft and true; "
        f"{repair.ending_image} By the end, the garden stood up bright, and the two friends smiled as if the whole yard knew."
    )
    return "\n\n".join([opening, sip_scene + " " + misunderstanding, clue_scene, turn_scene, ending])


def _prompts(world: World) -> list[str]:
    return [
        "Write a TinyStories-style nursery rhyme in a friend's backyard.",
        "Include the words sip and bucket in a misunderstanding while two children tend a small garden.",
        "Resolve the mix-up with physical clues, a thirsty backyard visitor, an apology, and a final image that proves the garden is calm again.",
    ]


def _history_field(world: World, tag: str, field_name: str) -> str:
    for event in world.history:
        if event.get("tag") == tag and field_name in event:
            return event[field_name]
    return ""


def _story_qa(world: World) -> list[QAItem]:
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    drink = world.drink
    area = world.area
    visitor = world.visitor
    repair = world.repair
    return [
        QAItem(
            "Why did the friend think the visiting child had sipped from the bucket?",
            f"{friend.name} heard the sip from {drink.cup_phrase} and saw the bucket water go down at nearly the same moment. "
            f"Before the clue appeared, those two changes made it look as if {hero.name} had taken the missing water.",
        ),
        QAItem(
            "What clue showed that the friend had made a mistake?",
            f"The children found {_history_field(world, 'clue_found', 'proof')} at {area.clue_place}. "
            f"That evidence pointed away from {hero.name} and toward the thirsty {visitor.label} that had been near the bucket.",
        ),
        QAItem(
            "How was the misunderstanding repaired in the middle of the story?",
            f"{friend.name} apologized as soon as the real cause was clear, and the children {repair.action_phrase}. "
            "That fixed the hurt feeling and also solved the reason the bucket had been disturbed.",
        ),
        QAItem(
            "How did the children help both the animal and the garden?",
            f"They gave the {visitor.label} its own water place and then refilled the bucket for the plants. "
            f"Because each thirsty part of the backyard got the right kind of care, {area.plant_name} and the visitor both ended calm.",
        ),
        QAItem(
            "What ending image proves the story finishes well?",
            f"The ending shows {repair.ending_image.lower()} "
            "It also shows the children smiling with a full bucket and a bright garden, which proves the misunderstanding is over.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    visitor = world.visitor
    return [
        QAItem(
            "Why can a falling water line cause a misunderstanding in a backyard?",
            "A bucket can lose water for more than one reason, and a child may only see the nearest action first. "
            "If someone notices a sip from a cup but misses the animal at the rim, the wrong cause can look true for a moment.",
        ),
        QAItem(
            "Why are footprints, whiskers, or nose marks useful in a garden story?",
            "They are physical clues that stay behind after the animal moves away. "
            "Because they are tied to the place where the water changed, they help children correct a guess with evidence instead of blame.",
        ),
        QAItem(
            "Why give a thirsty backyard animal a separate water place?",
            f"A separate water place meets the {visitor.label}'s need without turning the garden bucket into shared confusion. "
            "That keeps tools for plant care doing one job and lets the animal drink somewhere calmer and more fitting.",
        ),
        QAItem(
            "Why is the apology important after the clue is found?",
            "An apology shows that the friend changed after learning the truth. "
            "In a misunderstanding story, that change matters because the problem is not only the missing water but also the hurt feeling it caused.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = _render_story(world)
    if "sip" not in story.lower():
        raise StoryError("Generated story lost the required word 'sip'.")
    if "bucket" not in story.lower():
        raise StoryError("Generated story lost the required word 'bucket'.")
    if "backyard" not in story.lower():
        raise StoryError("Generated story lost the required backyard setting.")
    return StorySample(
        params=params,
        story=story,
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid_combo(A, V, R) :-
    area(A),
    visitor(V),
    repair(R),
    area_allows_visitor(A, V),
    area_allows_repair(A, R),
    visitor_allows_repair(V, R),
    repair_allows_area(R, A).

ok :- chosen(A, V, R), valid_combo(A, V, R).

#show valid_combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for key, area in sorted(AREAS.items()):
        rows.append(fact("area", key))
        for visitor_key in area.visitor_options:
            rows.append(fact("area_allows_visitor", key, visitor_key))
        for repair_key in area.repair_options:
            rows.append(fact("area_allows_repair", key, repair_key))
    for key, visitor in sorted(VISITORS.items()):
        rows.append(fact("visitor", key))
        for repair_key in visitor.compatible_repairs:
            rows.append(fact("visitor_allows_repair", key, repair_key))
    for key, repair in sorted(REPAIRS.items()):
        rows.append(fact("repair", key))
        for area_key in repair.compatible_areas:
            rows.append(fact("repair_allows_area", key, area_key))
    for key in sorted(CHILD_PAIRS):
        rows.append(fact("pair", key))
    for key in sorted(DRINKS):
        rows.append(fact("drink", key))
    if params is not None:
        rows.append(fact("chosen", params.area, params.visitor, params.repair))
        rows.append(fact("chosen_pair", params.pair))
        rows.append(fact("chosen_drink", params.drink))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "valid_combo"))
    return combos


def verify() -> str:
    python_set = set(valid_combos())
    asp_set = asp_valid_combos()
    if python_set != asp_set:
        only_python = sorted(python_set - asp_set)
        only_asp = sorted(asp_set - python_set)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    checked = 0
    for index, combo in enumerate(sorted(python_set), 1):
        rng = random.Random(20_000 + index)
        params = _make_params(argparse.Namespace(pair=None, drink=None), rng, combo, 20_000 + index)
        sample = generate(params)
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError(f"Verification failed: empty QA surface for combo {combo}.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Verification failed: unresolved template field in combo {combo}.")
        if len(sample.story.split()) < 90:
            raise StoryError(f"Verification failed: story too thin for combo {combo}.")
        checked += 1
    return f"OK: clingo gate matches Python with {checked} valid combos, and all generated stories passed sanity checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate nursery-rhyme backyard misunderstanding storyworld samples."
    )
    parser.add_argument("--pair", choices=sorted(CHILD_PAIRS), default=None)
    parser.add_argument("--area", choices=sorted(AREAS), default=None)
    parser.add_argument("--drink", choices=sorted(DRINKS), default=None)
    parser.add_argument("--visitor", choices=sorted(VISITORS), default=None)
    parser.add_argument("--repair", choices=sorted(REPAIRS), default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _format_qa(sample: StorySample) -> str:
    lines = ["", "== (1) Story prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print(_format_qa(sample))


def _json_dump(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
        return
    print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))


def _samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos()):
        story_seed = (args.seed if args.seed is not None else 1) + index
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        samples.append(generate(_make_params(args, rng, combo, story_seed)))
    return samples


def _samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else 1
    target = max(1, args.n)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempt = 0
    while len(samples) < target and attempt < target * 20:
        story_seed = base_seed + attempt
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        sample = generate(resolve_params(args, rng))
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        attempt += 1
    if len(samples) < target:
        raise StoryError(f"Could only generate {len(samples)} distinct samples for target {target}.")
    return samples


def _emit_asp_listing() -> None:
    for combo in sorted(asp_valid_combos()):
        print("\t".join(combo))


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0

        samples = _samples_for_all(args) if args.all else _samples_for_n(args)
        if args.json:
            _json_dump(samples)
            return 0

        for index, sample in enumerate(samples):
            header = ""
            if args.all:
                header = (
                    f"### {sample.params.area} / {sample.params.visitor} / "
                    f"{sample.params.repair} / {sample.params.pair} / {sample.params.drink}"
                )
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index != len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
