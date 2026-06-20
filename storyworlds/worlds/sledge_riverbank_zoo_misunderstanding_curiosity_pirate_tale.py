#!/usr/bin/env python3
"""
storyworlds/worlds/sledge_riverbank_zoo_misunderstanding_curiosity_pirate_tale.py
=================================================================================

A standalone storyworld for a seed prompt:

    Words: sledge, riverbank
    Setting: zoo
    Features: Misunderstanding, Curiosity
    Style: Pirate Tale

Internal source tale
--------------------
At a zoo riverbank during pirate morning, two children help a keeper pull a
painted breakfast sledge to the animals. A clue on the sledge seems to match one
child's clothes, so the other child wrongly thinks the friend wandered off to
play captain alone. The keeper pushes them toward curiosity instead of blame.
When they inspect the whole trail, they find the true cause, fix the sledge, and
finish the breakfast run together.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    phrase: str
    animal_plural: str
    lookout: str
    final_image: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    mark: str
    item: str
    clue: str
    accusation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    mark: str
    need: str
    actor: str
    event: str
    discovery: str
    danger: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    need: str
    offer: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_blame_delays_breakfast(world: World) -> list[str]:
    hero = world.get("Hero")
    friend = world.get("Friend")
    sledge = world.get("Sledge")
    animals = world.get("Animals")
    if hero.memes["accusing"] < THRESHOLD or friend.memes["hurt"] < THRESHOLD:
        return []
    sig = ("delay", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sledge.meters["delayed"] += 1
    sledge.meters["crooked"] += 1
    animals.memes["waiting"] += 1
    return [
        f"The breakfast run stalled, and the {world.place.animal_plural} watched from "
        f"{world.place.lookout} while the little sledge leaned toward the reeds."
    ]


def _r_curiosity_reveals_truth(world: World) -> list[str]:
    hero = world.get("Hero")
    friend = world.get("Friend")
    sledge = world.get("Sledge")
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    if hero.memes["curiosity"] < THRESHOLD or sledge.meters["checked"] < THRESHOLD:
        return []
    sig = ("truth", cause.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sledge.meters["truth_found"] += 1
    hero.memes["misunderstanding"] = 0.0
    friend.memes["relief"] += 1
    return [f"Curiosity uncovered the truth: {cause.discovery}"]


def _r_repair_restores_trust(world: World) -> list[str]:
    hero = world.get("Hero")
    friend = world.get("Friend")
    sledge = world.get("Sledge")
    animals = world.get("Animals")
    if hero.memes["apology"] < THRESHOLD or sledge.meters["repaired"] < THRESHOLD:
        return []
    sig = ("restored", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    friend.memes["hurt"] = 0.0
    sledge.meters["ready"] += 1
    sledge.meters["crooked"] = 0.0
    sledge.meters["delayed"] = 0.0
    animals.memes["waiting"] = 0.0
    return [
        "The wheels lined up again, and the sharp feeling between the two deckhands softened."
    ]


CAUSAL_RULES = [
    Rule("blame_delays_breakfast", _r_blame_delays_breakfast),
    Rule("curiosity_reveals_truth", _r_curiosity_reveals_truth),
    Rule("repair_restores_trust", _r_repair_restores_trust),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def place_allows(place: Place, cause: Cause) -> bool:
    return cause.id in place.affords


def clue_can_mislead(sign: Sign, cause: Cause) -> bool:
    return sign.mark == cause.mark


def remedy_fits(cause: Cause, remedy: Remedy) -> bool:
    return cause.need == remedy.need


def valid_story(place: Place, sign: Sign, cause: Cause, remedy: Remedy) -> bool:
    return (
        place_allows(place, cause)
        and clue_can_mislead(sign, cause)
        and remedy_fits(cause, remedy)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for sign_id, sign in SIGNS.items():
            for cause_id, cause in CAUSES.items():
                for remedy_id, remedy in REMEDIES.items():
                    if valid_story(place, sign, cause, remedy):
                        combos.append((place_id, sign_id, cause_id, remedy_id))
    return sorted(combos)


def remedy_phrase(remedy: Remedy) -> str:
    return {
        "retie_strap": "a firm river knot",
        "rebalance_load": "a scoop and a steadying rope",
        "free_wheel": "careful hands on the axle and pennant",
    }.get(remedy.id, remedy.id.replace("_", " "))


def predict_delay(world: World) -> dict[str, float]:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "delayed": sim.get("Sledge").meters["delayed"],
        "waiting": sim.get("Animals").memes["waiting"],
    }


def introduce(world: World, hero: Entity, friend: Entity, keeper: Entity) -> None:
    hero.memes["curious_heart"] += 1
    friend.memes["trust"] += 1
    sledge = world.get("Sledge")
    sledge.meters["loaded"] += 1
    world.say(
        f"At {world.place.phrase}, {hero.label} and {friend.label} marched beside "
        f"{keeper.label} like two tiny pirate deckhands."
    )
    world.say(
        f"Their painted sledge carried breakfast buckets along the riverbank for the "
        f"{world.place.animal_plural}, and the children loved the squeak of its little wheels."
    )


def notice_and_misunderstand(world: World, hero: Entity, friend: Entity,
                             sign: Sign) -> None:
    hero.memes["misunderstanding"] += 1
    hero.memes["accusing"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"When {hero.label} came back from the water pump, the sledge had slipped from its chalk mark."
    )
    world.say(
        f"{sign.clue.capitalize()} on the handle, and {friend.label} was wearing "
        f"{sign.item}. {hero.label} thought {friend.label} {sign.accusation}."
    )
    propagate(world, narrate=True)


def keeper_warning(world: World, keeper: Entity) -> None:
    risk = predict_delay(world)
    if risk["delayed"] >= THRESHOLD:
        world.say(
            f'"Easy, mateys," {keeper.label} said. "If we only guess, breakfast stays late for the '
            f'{world.place.animal_plural}."'
        )


def choose_curiosity(world: World, hero: Entity, friend: Entity, keeper: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'"A captain asks questions before pointing a finger," {keeper.label} said. '
        f'That made {hero.label} curious instead of cross.'
    )
    world.say(
        f"{hero.label} and {friend.label} knelt together beside the wheel track and followed it "
        f"along the riverbank, peeking under rails and around reeds."
    )
    world.get("Sledge").meters["checked"] += 1
    propagate(world, narrate=True)


def fix_sledge(world: World, hero: Entity, friend: Entity, keeper: Entity,
               remedy: Remedy) -> None:
    sledge = world.get("Sledge")
    world.say(remedy.offer.format(keeper=keeper.label))
    world.say(remedy.action.format(hero=hero.label, friend=friend.label))
    sledge.meters["repaired"] += 1
    hero.memes["apology"] += 1
    world.say(
        f'"I was wrong to blame you so fast," {hero.label} told {friend.label}. '
        f'"Next time I will be curious first."'
    )
    propagate(world, narrate=True)


def finish_story(world: World, hero: Entity, friend: Entity) -> None:
    place = world.place
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    world.say(
        f"Soon the little sledge rattled down the riverbank again toward the {place.animal_plural}."
    )
    world.say(
        f"{cause.ending} {place.final_image} {hero.label} grinned at {friend.label}, "
        "and the morning felt more like a happy voyage than a quarrel."
    )
    world.facts["ready"] = world.get("Sledge").meters["ready"] >= THRESHOLD
    world.facts["reconciled"] = world.get("Friend").memes["hurt"] == 0.0


def tell(place: Place, sign: Sign, cause: Cause, remedy: Remedy,
         hero_name: str, hero_gender: str, friend_name: str,
         friend_gender: str, keeper_name: str, keeper_gender: str) -> World:
    if not valid_story(place, sign, cause, remedy):
        raise StoryError(explain_rejection(place, sign, cause, remedy))

    world = World(place)
    hero = world.add(Entity("Hero", kind="character", type=hero_gender, label=hero_name))
    friend = world.add(Entity("Friend", kind="character", type=friend_gender, label=friend_name))
    keeper = world.add(Entity("Keeper", kind="character", type=keeper_gender, label=keeper_name))
    world.add(Entity("Sledge", kind="object", type="sledge", label="the painted sledge"))
    world.add(Entity("Animals", kind="animal_group", type="animals", label=place.animal_plural))
    world.facts.update(
        place=place,
        sign=sign,
        cause=cause,
        remedy=remedy,
        hero=hero,
        friend=friend,
        keeper=keeper,
    )

    introduce(world, hero, friend, keeper)
    world.para()
    notice_and_misunderstand(world, hero, friend, sign)
    keeper_warning(world, keeper)
    world.para()
    choose_curiosity(world, hero, friend, keeper)
    world.para()
    fix_sledge(world, hero, friend, keeper, remedy)
    finish_story(world, hero, friend)
    return world


PLACES = {
    "otter_wharf": Place(
        "otter_wharf",
        "the zoo riverbank at Otter Wharf",
        "otters",
        "the reedy wharf rail",
        "The otters popped up in a row like laughing pirates waiting for breakfast.",
        {"otter_bucket", "wind_pennant"},
        {"zoo", "riverbank", "otter", "sledge"},
    ),
    "monkey_landing": Place(
        "monkey_landing",
        "the zoo riverbank below Monkey Landing",
        "squirrel monkeys",
        "the rope-bridge rail",
        "The monkeys bounced above the bridge and chittered as if cheering the repaired crew.",
        {"monkey_strap", "wind_pennant"},
        {"zoo", "riverbank", "monkey", "sledge", "knot"},
    ),
    "pelican_pier": Place(
        "pelican_pier",
        "the zoo riverbank at Pelican Pier",
        "pelicans",
        "the low fish rail",
        "The pelicans clacked their beaks and stretched tall as the buckets finally arrived.",
        {"pelican_bucket", "wind_pennant"},
        {"zoo", "riverbank", "pelican", "sledge"},
    ),
}

SIGNS = {
    "red_stripe": Sign(
        "red_stripe",
        "red_stripe",
        "a red striped sash on the vest",
        "A red striped thread was caught",
        "had tugged the sledge away to play captain alone",
        {"misunderstanding", "pirate"},
    ),
    "silver_scale": Sign(
        "silver_scale",
        "silver_scale",
        "a silver scale badge on the hat",
        "A silver fish scale glittered",
        "had sneaked the sledge aside to peek at the breakfast buckets first",
        {"misunderstanding", "zoo"},
    ),
    "blue_ribbon": Sign(
        "blue_ribbon",
        "blue_ribbon",
        "a blue ribbon tied around the sleeve",
        "A blue ribbon fluttered",
        "had dragged the sledge off for a windy pirate race",
        {"misunderstanding", "wind"},
    ),
}

CAUSES = {
    "monkey_strap": Cause(
        "monkey_strap",
        "red_stripe",
        "retie_strap",
        "a squirrel monkey",
        "had worried the cargo strap loose while reaching for fruit smells",
        "above them a squirrel monkey was swinging the loosened red strap like a prize ribbon.",
        "Without the strap, the load could slide into the reeds",
        "The strap sat snug again, and the fruit bucket stopped wobbling.",
        {"monkey", "zoo", "knot"},
    ),
    "otter_bucket": Cause(
        "otter_bucket",
        "silver_scale",
        "rebalance_load",
        "an otter pup",
        "had nosed at a fish bucket until the load tipped",
        "an otter pup had nudged a fish bucket, and silver scales flashed where the breakfast had spilled.",
        "The crooked load could dump breakfast in the mud",
        "The fish buckets rode level again, and the river smell made the otters paddle in circles.",
        {"otter", "zoo", "fish"},
    ),
    "pelican_bucket": Cause(
        "pelican_bucket",
        "silver_scale",
        "rebalance_load",
        "a young pelican",
        "had pecked at a fish bucket until the load tipped",
        "a young pelican had pecked at the fish bucket, and silver scales still shone on the plank.",
        "The crooked load could spill before the sledge reached the rail",
        "The buckets sat square again, and the fish smell drifted neatly toward the pier.",
        {"pelican", "zoo", "fish"},
    ),
    "wind_pennant": Cause(
        "wind_pennant",
        "blue_ribbon",
        "free_wheel",
        "a gust off the water",
        "had wrapped a blue parade pennant around one wheel",
        "the blue pennant had wound tight around the wheel, snapping in the wind like a tiny sail.",
        "The wheel could not turn cleanly while the pennant held it fast",
        "The freed wheel rolled smoothly, and the pennant fluttered from the rail instead of the axle.",
        {"wind", "riverbank", "zoo"},
    ),
}

REMEDIES = {
    "retie_strap": Remedy(
        "retie_strap",
        "retie_strap",
        "{keeper} showed them a snug river knot.",
        "{hero} and {friend} pulled the strap tight, tucked the fruit bucket in place, and straightened the painted sledge together.",
        "They fixed the loose strap with a firm knot so the load could stay steady.",
        {"knot", "sledge"},
    ),
    "rebalance_load": Remedy(
        "rebalance_load",
        "rebalance_load",
        "{keeper} handed them a scoop and a steadying rope.",
        "{hero} scooped the spilled fish back while {friend} held the bucket steady, and together they balanced the sledge again.",
        "They rebalanced the tipped bucket so the sledge could carry breakfast safely.",
        {"fish", "sledge"},
    ),
    "free_wheel": Remedy(
        "free_wheel",
        "free_wheel",
        "{keeper} showed them how to lift the axle just enough.",
        "{friend} unwound the pennant while {hero} held the handle still, and the wheel came free with a cheerful squeak.",
        "They unwound the pennant and freed the stuck wheel so the sledge could roll again.",
        {"wind", "sledge"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nia", "Tess", "Ruby", "Ava"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Jude", "Ben", "Kai"]
KEEPER_WOMEN = ["Keeper Maris", "Keeper June", "Keeper Poppy"]
KEEPER_MEN = ["Keeper Bram", "Keeper Ellis", "Keeper Rowan"]


@dataclass
class StoryParams:
    place: str
    sign: str
    cause: str
    remedy: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    keeper: str
    keeper_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "riverbank": [
        ("Why should children walk carefully on a riverbank?",
         "Riverbanks can be muddy or slippery, so careful steps help children stay safe near the water."),
    ],
    "sledge": [
        ("What is a sledge used for?",
         "A sledge helps people pull supplies from one place to another, especially when the load is heavy."),
    ],
    "knot": [
        ("Why does a good knot matter when carrying food?",
         "A good knot keeps straps from coming loose, so the load stays steady instead of tipping."),
    ],
    "otter": [
        ("What do otters often like to do in water?",
         "Otters often swim, float, and use their paws to investigate interesting things in the water."),
    ],
    "monkey": [
        ("Why are monkeys always touching and testing things?",
         "Many monkeys are curious and active, so they explore new objects with quick hands and eyes."),
    ],
    "pelican": [
        ("What makes a pelican easy to notice at feeding time?",
         "A pelican has a long bill and often waits close to the water when it expects fish."),
    ],
    "curiosity": [
        ("Why can curiosity solve a misunderstanding?",
         "Curiosity helps people ask questions and look for evidence before deciding what happened."),
    ],
}
KNOWLEDGE_ORDER = ["riverbank", "sledge", "knot", "otter", "monkey", "pelican", "curiosity"]


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    return [
        'Write a child-facing pirate tale set at a zoo that includes the words "sledge" and "riverbank".',
        f"Tell a story where {hero.label} misunderstands {friend.label} after spotting a clue near a breakfast sledge.",
        f"Make curiosity solve the trouble by revealing that {cause.actor} {cause.event}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    keeper: Entity = world.facts["keeper"]  # type: ignore[assignment]
    sign: Sign = world.facts["sign"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    remedy: Remedy = world.facts["remedy"]  # type: ignore[assignment]
    return [
        ("Where does the story happen?",
         f"The story happens at {world.place.phrase}. The children are helping with breakfast for the {world.place.animal_plural}."),
        (f"Why did {hero.label} blame {friend.label} at first?",
         f"{hero.label} saw that {sign.clue.lower()} on the sledge, and {friend.label} was wearing {sign.item}. "
         "That clue seemed to point at the friend, even though it did not tell the whole truth."),
        ("What did curiosity reveal?",
         f"Curiosity revealed that {cause.actor} {cause.event}. "
         f"When the children followed the tracks instead of arguing, they discovered that {cause.discovery}"),
        ("How was the sledge fixed?",
         f"They used {remedy_phrase(remedy)} to solve the real problem. {remedy.result}"),
        (f"What did {hero.label} learn?",
         f"{hero.label} learned to ask questions before blaming a friend. "
         f"{keeper.label}'s advice helped turn a misunderstanding into a shared rescue."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    place: Place = world.facts["place"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    tags = set(place.tags) | set(cause.tags) | {"curiosity"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for idx, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{idx}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("otter_wharf", "silver_scale", "otter_bucket", "rebalance_load",
                "Lina", "girl", "Finn", "boy", "Keeper Maris", "woman"),
    StoryParams("monkey_landing", "red_stripe", "monkey_strap", "retie_strap",
                "Theo", "boy", "Mara", "girl", "Keeper June", "woman"),
    StoryParams("pelican_pier", "silver_scale", "pelican_bucket", "rebalance_load",
                "Ruby", "girl", "Kai", "boy", "Keeper Bram", "man"),
    StoryParams("otter_wharf", "blue_ribbon", "wind_pennant", "free_wheel",
                "Milo", "boy", "Ava", "girl", "Keeper Rowan", "man"),
]


def explain_rejection(place: Place, sign: Sign, cause: Cause, remedy: Remedy) -> str:
    if not place_allows(place, cause):
        return (
            f"(No story: {place.phrase} does not support the cause '{cause.id}', "
            "so the riverbank trouble would not happen there.)"
        )
    if not clue_can_mislead(sign, cause):
        return (
            f"(No story: clue '{sign.id}' carries mark '{sign.mark}', but cause "
            f"'{cause.id}' leaves mark '{cause.mark}'. The misunderstanding would not be fair.)"
        )
    return (
        f"(No story: remedy '{remedy.id}' fixes '{remedy.need}', but cause "
        f"'{cause.id}' needs '{cause.need}'. The repair must match the real problem.)"
    )


ASP_RULES = r"""
fair_clue(Sign, Cause) :- sign(Sign), cause(Cause), sign_mark(Sign, M), cause_mark(Cause, M).
effective(Cause, Remedy) :- cause(Cause), remedy(Remedy), cause_need(Cause, N), remedy_need(Remedy, N).
valid(Place, Sign, Cause, Remedy) :- affords(Place, Cause), fair_clue(Sign, Cause), effective(Cause, Remedy).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for cause_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, cause_id))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        lines.append(asp.fact("sign_mark", sign_id, sign.mark))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_mark", cause_id, cause.mark))
        lines.append(asp.fact("cause_need", cause_id, cause.need))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("remedy_need", remedy_id, remedy.need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set != asp_set:
        print("MISMATCH between clingo and valid_combos():")
        if asp_set - python_set:
            print("  only in clingo:", sorted(asp_set - python_set))
        if python_set - asp_set:
            print("  only in python:", sorted(python_set - asp_set))
        return 1

    exercised = 0
    for idx, combo in enumerate(sorted(python_set), start=1):
        params = StoryParams(
            place=combo[0],
            sign=combo[1],
            cause=combo[2],
            remedy=combo[3],
            hero="Lina" if idx % 2 else "Theo",
            hero_gender="girl" if idx % 2 else "boy",
            friend="Finn" if idx % 2 else "Mara",
            friend_gender="boy" if idx % 2 else "girl",
            keeper="Keeper Maris" if idx % 2 else "Keeper Bram",
            keeper_gender="woman" if idx % 2 else "man",
            seed=9_000 + idx,
        )
        sample = generate(params)
        if not sample.story.strip():
            print("VERIFY FAILED: empty story for", combo)
            return 1
        if "sledge" not in sample.story or "riverbank" not in sample.story:
            print("VERIFY FAILED: required seed words missing for", combo)
            return 1
        if not sample.story_qa or not sample.world_qa or not sample.prompts:
            print("VERIFY FAILED: missing prompt or QA set for", combo)
            return 1
        if "{" in sample.story or "}" in sample.story:
            print("VERIFY FAILED: unresolved template text for", combo)
            return 1
        if not sample.world.facts.get("ready") or not sample.world.facts.get("reconciled"):
            print("VERIFY FAILED: story did not reach a repaired ending for", combo)
            return 1
        exercised += 1

    print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    print(f"OK: exercised generation for {exercised} valid zoo riverbank pirate stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "Storyworld: zoo riverbank pirate tale with a sledge, misunderstanding, "
            "and curiosity. Unspecified choices are randomized."
        )
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper")
    ap.add_argument("--keeper-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and exercise generated stories")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def _pick_keeper(rng: random.Random, gender: str) -> str:
    return rng.choice(KEEPER_WOMEN if gender == "woman" else KEEPER_MEN)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause and not place_allows(PLACES[args.place], CAUSES[args.cause]):
        sign = SIGNS[args.sign] if args.sign else next(iter(SIGNS.values()))
        remedy = REMEDIES[args.remedy] if args.remedy else next(iter(REMEDIES.values()))
        raise StoryError(explain_rejection(PLACES[args.place], sign, CAUSES[args.cause], remedy))
    if args.sign and args.cause and not clue_can_mislead(SIGNS[args.sign], CAUSES[args.cause]):
        place = PLACES[args.place] if args.place else next(
            p for p in PLACES.values() if CAUSES[args.cause].id in p.affords
        )
        remedy = REMEDIES[args.remedy] if args.remedy else next(iter(REMEDIES.values()))
        raise StoryError(explain_rejection(place, SIGNS[args.sign], CAUSES[args.cause], remedy))
    if args.cause and args.remedy and not remedy_fits(CAUSES[args.cause], REMEDIES[args.remedy]):
        place = PLACES[args.place] if args.place else next(
            p for p in PLACES.values() if CAUSES[args.cause].id in p.affords
        )
        sign = SIGNS[args.sign] if args.sign else next(
            s for s in SIGNS.values() if s.mark == CAUSES[args.cause].mark
        )
        raise StoryError(explain_rejection(place, sign, CAUSES[args.cause], REMEDIES[args.remedy]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sign is None or combo[1] == args.sign)
        and (args.cause is None or combo[2] == args.cause)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, sign, cause, remedy = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    keeper_gender = args.keeper_gender or rng.choice(["woman", "man"])
    keeper = args.keeper or _pick_keeper(rng, keeper_gender)
    return StoryParams(
        place=place,
        sign=sign,
        cause=cause,
        remedy=remedy,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        keeper=keeper,
        keeper_gender=keeper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        SIGNS[params.sign],
        CAUSES[params.cause],
        REMEDIES[params.remedy],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.keeper,
        params.keeper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sign, cause, remedy) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 80, 80):
            seed = base_seed + attempts
            attempts += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place}: {p.sign} / {p.cause} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
