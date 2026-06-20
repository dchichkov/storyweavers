#!/usr/bin/env python3
"""
storyworlds/worlds/sip_bucket_friend_s_backyard_misunderstanding_nursery_4.py
=============================================================================

A small nursery-rhyme-style storyworld about a misunderstanding in a friend's
backyard.

Internal source tale:
    A visiting child helps a friend water plants in the friend's backyard.
    The visitor takes a sip from a sweet drink in a cup just as the garden
    bucket goes lower. The friend wrongly thinks the visitor sipped from the
    bucket. The children follow a physical clue, discover a thirsty backyard
    animal, make it a proper water place of its own, refill the bucket, and
    end with lifted plants and repaired trust.
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
    visitor_options: tuple[str, ...]
    repair_options: tuple[str, ...]


@dataclass(frozen=True)
class DrinkOption:
    key: str
    label: str
    cup_phrase: str
    sweet_note: str
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
    own_water_place: str
    compatible_repairs: tuple[str, ...]


@dataclass(frozen=True)
class RepairMethod:
    key: str
    label: str
    action_phrase: str
    spot_phrase: str
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
    "sunflower_path": BackyardArea(
        key="sunflower_path",
        label="the sunflower path by the stepping stones",
        opening_image="gold heads nodded over the stepping stones like little bells in a line",
        clue_place="the warm edge of the stepping-stone path",
        plant_name="the sunflowers",
        plant_need="droopy necks from the noon heat",
        visitor_options=("robin", "puppy"),
        repair_options=("fence_saucer", "shade_bowl"),
    ),
    "bean_gate": BackyardArea(
        key="bean_gate",
        label="the bean-vine gate near the back fence",
        opening_image="green bean vines looped into a gate and tickled the air when the breeze passed",
        clue_place="the dusty patch under the bean gate",
        plant_name="the bean vines",
        plant_need="curling leaves that asked for another drink",
        visitor_options=("puppy", "squirrel"),
        repair_options=("shade_bowl", "stump_dish"),
    ),
    "berry_patch": BackyardArea(
        key="berry_patch",
        label="the berry patch beside the old stump",
        opening_image="berry leaves made a low green quilt around the stump and hummed with bees",
        clue_place="the shaded dirt beside the old stump",
        plant_name="the berry bushes",
        plant_need="soft leaves that sagged toward the soil",
        visitor_options=("robin", "squirrel"),
        repair_options=("fence_saucer", "stump_dish"),
    ),
}

DRINKS: dict[str, DrinkOption] = {
    "mint_lemonade": DrinkOption(
        key="mint_lemonade",
        label="mint lemonade",
        cup_phrase="a striped cup of mint lemonade",
        sweet_note="cool and lemony",
        color="pale gold",
    ),
    "apple_juice": DrinkOption(
        key="apple_juice",
        label="apple juice",
        cup_phrase="a little cup of apple juice",
        sweet_note="sweet like orchard apples",
        color="sunny amber",
    ),
    "berry_milk": DrinkOption(
        key="berry_milk",
        label="berry milk",
        cup_phrase="a tiny cup of berry milk",
        sweet_note="sweet like berries and cream",
        color="soft pink",
    ),
}

VISITORS: dict[str, Visitor] = {
    "robin": Visitor(
        key="robin",
        label="robin",
        kind="bird",
        sound="peep-peep",
        proof="a dotted ring of tiny beak taps on the bucket rim",
        trail="three pin-prick bird prints",
        hideout="the fence rail in the sun",
        own_water_place="a neat saucer high and safe from the mud",
        compatible_repairs=("fence_saucer",),
    ),
    "puppy": Visitor(
        key="puppy",
        label="puppy",
        kind="dog",
        sound="ruff-ruff",
        proof="a wet nose mark and four round paw prints beside the bucket",
        trail="four round paw prints",
        hideout="the shady grass by the gate",
        own_water_place="a cool bowl tucked in the shade",
        compatible_repairs=("shade_bowl",),
    ),
    "squirrel": Visitor(
        key="squirrel",
        label="squirrel",
        kind="animal",
        sound="chip-chip",
        proof="an acorn cap and fine scratch marks on the bucket handle",
        trail="comma-shaped squirrel prints",
        hideout="the old stump with a twitching tail behind it",
        own_water_place="a shallow dish on the stump ledge",
        compatible_repairs=("stump_dish",),
    ),
}

REPAIRS: dict[str, RepairMethod] = {
    "fence_saucer": RepairMethod(
        key="fence_saucer",
        label="set a saucer on the fence rail",
        action_phrase="set a saucer on the fence rail and filled it with clean water",
        spot_phrase="the sunny fence rail",
        ending_image="The robin dipped its beak in the saucer and left the bucket shining full below.",
        compatible_areas=("sunflower_path", "berry_patch"),
    ),
    "shade_bowl": RepairMethod(
        key="shade_bowl",
        label="set a bowl in the shady grass",
        action_phrase="set a bowl in the shady grass and filled it with clean water",
        spot_phrase="the shady grass by the gate",
        ending_image="The puppy lapped from the bowl in the shade and stopped nosing at the bucket.",
        compatible_areas=("sunflower_path", "bean_gate"),
    ),
    "stump_dish": RepairMethod(
        key="stump_dish",
        label="set a dish on the stump",
        action_phrase="set a dish on the stump and filled it with clean water",
        spot_phrase="the flat top of the old stump",
        ending_image="The squirrel paused on the stump, drank from the dish, and left the bucket alone.",
        compatible_areas=("bean_gate", "berry_patch"),
    ),
}

CHILD_PAIRS: dict[str, ChildPair] = {
    "ivy_june": ChildPair(
        key="ivy_june",
        hero_name="Ivy",
        hero_kind="girl",
        hero_trait="gentle",
        friend_name="June",
        friend_kind="girl",
        friend_trait="careful",
    ),
    "leo_mara": ChildPair(
        key="leo_mara",
        hero_name="Leo",
        hero_kind="boy",
        hero_trait="bright-eyed",
        friend_name="Mara",
        friend_kind="girl",
        friend_trait="steady",
    ),
    "nina_ollie": ChildPair(
        key="nina_ollie",
        hero_name="Nina",
        hero_kind="girl",
        hero_trait="merry",
        friend_name="Ollie",
        friend_kind="boy",
        friend_trait="earnest",
    ),
    "ravi_tess": ChildPair(
        key="ravi_tess",
        hero_name="Ravi",
        hero_kind="boy",
        hero_trait="patient",
        friend_name="Tess",
        friend_kind="girl",
        friend_trait="watchful",
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
            memes={"trust": 1.0, "care": 1.0, "hurt": 0.0, "relief": 0.0},
        )
    )
    friend = world.add(
        Entity(
            name=pair.friend_name,
            kind=pair.friend_kind,
            role="friend",
            traits=[pair.friend_trait, "garden-proud"],
            meters={"steps": 0.0},
            memes={"trust": 1.0, "care": 1.0, "suspicion": 0.0, "regret": 0.0},
        )
    )
    bucket = world.add(
        Entity(
            name="watering bucket",
            kind="bucket",
            role="bucket",
            traits=["blue", "sloshy"],
            meters={"water": 3.0, "missing": 0.0},
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
            meters={"thirst": 2.0},
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
            memes={"fear": 0.4, "calm": 0.0},
        )
    )

    world.facts.update(
        {
            "setting": f"{friend.name}'s backyard",
            "sip_source": "cup",
            "bucket_source": "watering bucket",
            "misunderstanding": False,
            "clue_found": False,
            "visitor_found": False,
            "repair_done": False,
            "apology_given": False,
            "seed": params.seed if params.seed is not None else "",
        }
    )

    _record(
        world,
        "opening",
        setting=world.facts["setting"],
        area=area.label,
        plants=area.plant_name,
        need=area.plant_need,
    )

    hero.meters["steps"] += 1.0
    friend.meters["steps"] += 1.0
    hero.meters["cup_level"] = cup.meters["drink_level"]

    cup.meters["drink_level"] -= 0.2
    hero.meters["cup_level"] = cup.meters["drink_level"]
    hero.memes["relief"] += 0.2
    world.facts["sip_word"] = "sip"
    _record(
        world,
        "hero_sip",
        actor=hero.name,
        source=drink.cup_phrase,
        taste=drink.sweet_note,
    )

    bucket.meters["water"] -= 0.8
    bucket.meters["missing"] += 0.8
    backyard_visitor.meters["thirst"] -= 0.6
    _record(
        world,
        "visitor_slurp",
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
            wrong_guess="bucket sip",
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
        visitor=visitor.label,
    )

    world.facts["apology_given"] = True
    _record(world, "apology", speaker=friend.name, listener=hero.name)

    if not valid_combo(params.area, params.visitor, params.repair):
        raise StoryError(invalid_reason(params.area, params.visitor, params.repair))

    backyard_visitor.meters["thirst"] = 0.0
    backyard_visitor.memes["calm"] = 1.0
    bucket.meters["water"] = 3.0
    bucket.meters["missing"] = 0.0
    plants.meters["thirst"] = 0.0
    plants.memes["relief"] = 1.0
    hero.memes["relief"] = 1.0
    friend.memes["trust"] = 1.2
    hero.memes["trust"] = 1.3
    world.facts["repair_done"] = True
    _record(
        world,
        "repair",
        action=repair.action_phrase,
        spot=repair.spot_phrase,
        visitor_place=visitor.own_water_place,
    )
    _record(world, "garden_watered", plants=plants.name, bucket_level=str(bucket.meters["water"]))
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

    accusation = (
        f"\"Did you sip from the bucket, {hero.name}?\" cried {friend.name}, "
        "for the water line looked lower all at once."
    )
    clue_line = (
        f"Then they saw {world.visitor.proof} at {area.clue_place}, "
        f"and heard {world.visitor.sound} from {world.visitor.hideout}."
    )
    apology_line = (
        f"{friend.name} felt sorry for the wrong guess and said so at once. "
        f"Together the children {repair.action_phrase}."
    )
    ending_image = (
        f"{repair.ending_image} The bucket stood full again, "
        f"{plants.name} lifted up, and the two friends smiled in {friend.name}'s backyard."
    )
    opening_image = area.opening_image[:1].upper() + area.opening_image[1:]

    paragraphs = [
        (
            f"In {friend.name}'s backyard, by {area.label}, {hero.name} and {friend.name} "
            f"went tiptoe-triptoe with a {bucket.name} between them. {opening_image}, "
            f"and {plants.name} waited with {area.plant_need}."
        ),
        (
            f"{hero.name} carried {cup.name} that smelled {drink.sweet_note}. "
            f"{hero.pronoun('subject').capitalize()} took one small sip from the cup, not from the bucket. "
            f"{accusation}"
        ),
        (
            f"{hero.name} blinked, hurt, because {drink.label} smelled sweet while bucket water smelled of leaves. "
            f"{clue_line}"
        ),
        (
            f"The muddle melted into the truth: the thirsty {visitor.name} had taken a quick drink. "
            f"{apology_line} Then they refilled the bucket and watered {plants.name}."
        ),
        (
            "Sip for the cup, slosh for the pail, that was the right song all along. "
            f"{ending_image}"
        ),
    ]
    return "\n\n".join(paragraphs)


def _prompts(world: World) -> list[str]:
    return [
        "Write a TinyStories-style nursery rhyme set in a friend's backyard.",
        "Include the words sip and bucket in a misunderstanding about watering plants.",
        "Resolve the mix-up with a physical clue, a thirsty backyard visitor, and a gentle apology.",
    ]


def _history_field(world: World, tag: str, field_name: str) -> str:
    for event in world.history:
        if event.get("tag") == tag and field_name in event:
            return event[field_name]
    return ""


def _story_qa(world: World) -> list[QAItem]:
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    area = world.area
    drink = world.drink
    visitor = world.visitor
    repair = world.repair
    return [
        QAItem(
            "Why did the friend think the visiting child drank from the bucket?",
            f"{friend.name} saw the bucket water go lower just after {hero.name} took a sip from {drink.cup_phrase}. "
            f"Because {friend.name} had not yet seen the thirsty {visitor.label}, the missing water and the cup sip looked like the same act.",
        ),
        QAItem(
            "What clue solved the misunderstanding?",
            f"The children found {_history_field(world, 'clue_found', 'proof')} at {area.clue_place}. "
            f"That clue pointed to the {visitor.label}, so it showed that the bucket had been visited by an animal instead of sipped by {hero.name}.",
        ),
        QAItem(
            "How did the children fix both the mix-up and the thirsty yard?",
            f"{friend.name} apologized, and together the children {repair.action_phrase}. "
            f"Then they refilled the bucket and watered {area.plant_name}, so the visitor got a proper drink and the garden got its turn too.",
        ),
        QAItem(
            "What changed in the friendship by the end?",
            f"The suspicion was gone and the apology was spoken out loud. "
            f"By solving the problem together, {hero.name} and {friend.name} ended with stronger trust than they had in the middle of the muddle.",
        ),
        QAItem(
            "What image proves the story is finished well?",
            f"The ending shows a full bucket, calm plants, and the {visitor.label} drinking from {visitor.own_water_place}. "
            "Those details prove that the misunderstanding is cleared up and the backyard is peaceful again.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    visitor = world.visitor
    return [
        QAItem(
            "Why give a backyard animal its own water place instead of letting it nose around a garden bucket?",
            f"A separate water place keeps the animal from confusing a tool that people still need for the plants. "
            f"In this world, that repair works because it gives the {visitor.label} a clear, safer place to drink.",
        ),
        QAItem(
            "Why are marks beside a bucket useful clues?",
            f"Marks stay on the rim, handle, or dirt even when the animal has already moved away. "
            "They connect the missing water to a physical cause, which helps children answer a question without guessing at each other.",
        ),
        QAItem(
            "Why can one sip from a cup and one missing bit of bucket water be confused from far away?",
            "Both changes happen quickly and both make a liquid level drop. "
            "Without a close look at the cup, the bucket, and the ground nearby, a careful child can still reach the wrong conclusion.",
        ),
        QAItem(
            "Why is this a misunderstanding instead of a trick?",
            "The friend makes a mistake because some evidence is missing at first. "
            "Once the real clue appears, the friend apologizes and changes course instead of pretending the wrong guess was true.",
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
    for key in sorted(VISITORS):
        rows.append(fact("visitor", key))
        for repair_key in VISITORS[key].compatible_repairs:
            rows.append(fact("visitor_allows_repair", key, repair_key))
    for key in sorted(REPAIRS):
        rows.append(fact("repair", key))
        for area_key in REPAIRS[key].compatible_areas:
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
        rng = random.Random(10_000 + index)
        sample = generate(_make_params(argparse.Namespace(pair=None, drink=None), rng, combo, 10_000 + index))
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError(f"Verification failed: empty QA surface for combo {combo}.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Verification failed: unresolved template field in combo {combo}.")
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
