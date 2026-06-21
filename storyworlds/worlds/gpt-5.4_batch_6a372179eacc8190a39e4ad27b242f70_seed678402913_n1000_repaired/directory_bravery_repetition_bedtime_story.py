#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/directory_bravery_repetition_bedtime_story.py
=======================================================================

A standalone storyworld for a bedtime-sized tale about a child who finds
something that belongs to a neighbor, studies the building directory, and
gathers enough courage to walk a sleepy hallway and return it.

The world is deliberately small and classical:

- typed entities with physical meters and emotional memes
- a short causal rule layer
- a reasonableness gate over which item can belong to which recipient and
  whether a place's directory can actually list that recipient
- a repeated brave refrain that changes courage state
- two good outcomes:
    * solo_delivery   -- the child walks the hall alone, bravely
    * together_delivery -- the child asks for company and walks with a parent

The prose stays close to bedtime-story style: soft, concrete, and calm.

Run it
------
python storyworlds/worlds/gpt-5.4/directory_bravery_repetition_bedtime_story.py
python storyworlds/worlds/gpt-5.4/directory_bravery_repetition_bedtime_story.py --all
python storyworlds/worlds/gpt-5.4/directory_bravery_repetition_bedtime_story.py --seed 7 -n 5
python storyworlds/worlds/gpt-5.4/directory_bravery_repetition_bedtime_story.py --qa
python storyworlds/worlds/gpt-5.4/directory_bravery_repetition_bedtime_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
REPETITIONS = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "gentleman"}
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
    label: str
    directory_phrase: str
    hallway_phrase: str
    light_phrase: str
    difficulty: int
    floors: int = 1
    listed: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    pronoun_word: str
    belongs_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return self.pronoun_word


@dataclass
class Recipient:
    id: str
    name: str
    title: str
    apartment: str
    kind: str
    expects: set[str] = field(default_factory=set)
    gives_back: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    phrase: str
    bonus: int
    sense: int
    accompanies: bool = False
    use_line: str = ""
    qa_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Refrain:
    id: str
    line: str
    gain: int
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dim_hall_fear(world: World) -> list[str]:
    child = world.get("child")
    hall = world.get("hall")
    if hall.meters["dim"] < THRESHOLD:
        return []
    sig = ("dim_fear", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    return ["__fear__"]


def _r_directory_clarity(world: World) -> list[str]:
    board = world.get("directory")
    child = world.get("child")
    if board.meters["read"] < THRESHOLD:
        return []
    sig = ("clarity", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["certainty"] += 1
    return []


def _r_support_courage(world: World) -> list[str]:
    child = world.get("child")
    support = world.get("support")
    if support.meters["active"] < THRESHOLD:
        return []
    sig = ("support", child.id, support.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["courage"] += support.attrs.get("bonus", 0)
    child.memes["comfort"] += 1
    return []


def _r_refrain_courage(world: World) -> list[str]:
    child = world.get("child")
    count = int(child.meters["refrain_count"])
    if count <= 0:
        return []
    sig = ("refrain", child.id, count)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gain = world.facts["refrain_gain"]
    child.memes["courage"] += gain
    child.memes["calm"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="dim_hall_fear", tag="emotional", apply=_r_dim_hall_fear),
    Rule(name="directory_clarity", tag="cognitive", apply=_r_directory_clarity),
    Rule(name="support_courage", tag="emotional", apply=_r_support_courage),
    Rule(name="refrain_courage", tag="emotional", apply=_r_refrain_courage),
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


def is_listed(place: Place, recipient: Recipient) -> bool:
    return recipient.id in place.listed


def item_matches(item: Item, recipient: Recipient) -> bool:
    return item.id in recipient.expects and recipient.id in item.belongs_to


def sensible_supports() -> list[Support]:
    return [s for s in SUPPORTS.values() if s.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    support = SUPPORTS[params.support]
    place = PLACES[params.place]
    refrain = REFRAINS[params.refrain]
    total = support.bonus + refrain.gain * REPETITIONS + 1
    if support.accompanies:
        return "together_delivery"
    if total >= place.difficulty:
        return "solo_delivery"
    return "together_delivery"


def explain_rejection(place: Place, item: Item, recipient: Recipient) -> str:
    if not is_listed(place, recipient):
        return (
            f"(No story: {recipient.name} is not listed in the {place.label}'s directory, "
            f"so the child would have no honest way to find the right door.)"
        )
    return (
        f"(No story: {item.phrase} does not belong to {recipient.name}, so there is no "
        f"clear bedtime errand to carry down the hall.)"
    )


def explain_support(support_id: str) -> str:
    support = SUPPORTS[support_id]
    better = ", ".join(sorted(s.id for s in sensible_supports()))
    return (
        f"(Refusing support '{support_id}': it scores too low on common sense "
        f"(sense={support.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_walk(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    sim.get("directory").meters["read"] += 1
    sim.get("support").meters["active"] += 1
    propagate(sim, narrate=False)
    for _ in range(REPETITIONS):
        child.meters["refrain_count"] += 1
        propagate(sim, narrate=False)
    difficulty = sim.facts["difficulty"]
    courage = child.memes["courage"] + child.memes["certainty"]
    return {
        "courage": courage,
        "fear": child.memes["fear"],
        "difficulty": difficulty,
        "solo": (not sim.get("support").attrs.get("accompanies")) and courage >= difficulty,
    }


def bedtime_opening(world: World, child: Entity, parent: Entity, item_ent: Entity, place: Place) -> None:
    world.say(
        f"It was bedtime in {place.label}. {child.id} was already in soft pajamas, "
        f"and {parent.label_word} had tucked the blanket smooth under {child.pronoun('possessive')} chin."
    )
    world.say(
        f"Then {child.id} noticed {item_ent.phrase} resting beside the pillow, where it did not belong."
    )


def discover_task(world: World, child: Entity, item_ent: Entity, recipient: Recipient) -> None:
    child.memes["kindness"] += 1
    world.say(
        f'"Oh," whispered {child.id}, lifting {item_ent.label} carefully. '
        f'"This belongs to {recipient.name} in {recipient.apartment}."'
    )


def notice_hall(world: World, child: Entity, place: Place) -> None:
    hall = world.get("hall")
    hall.meters["dim"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Outside the door, {place.hallway_phrase}. {place.light_phrase}, and the sleepy quiet made the hall seem bigger than it really was."
    )
    if child.memes["fear"] >= THRESHOLD:
        world.say(f"{child.id} gave a small gulp and tucked {child.pronoun('possessive')} toes under the blanket.")


def read_directory(world: World, child: Entity, place: Place, recipient: Recipient) -> None:
    board = world.get("directory")
    board.meters["read"] += 1
    propagate(world, narrate=False)
    world.say(
        f"By the elevator hung {place.directory_phrase}. {child.id} looked at the directory and found {recipient.name}, {recipient.apartment}."
    )


def parent_offer(world: World, child: Entity, parent: Entity, support: Support) -> None:
    support_ent = world.get("support")
    support_ent.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{parent.label_word.capitalize()} knelt beside the bed and said, "{support.use_line}"'
    )
    world.say(
        f"{child.id} took {support.phrase} and felt the frightened part inside grow a little quieter."
    )


def repeat_refrain(world: World, child: Entity, refrain: Refrain) -> None:
    for n in range(1, REPETITIONS + 1):
        child.meters["refrain_count"] += 1
        propagate(world, narrate=False)
        world.say(f'"{refrain.line}" {child.id} said for the {ordinal(n)} time.')
    world.say("The words did not make the hallway smaller, but they made the child feel steadier inside.")


def solo_walk(world: World, child: Entity, parent: Entity, place: Place, recipient: Recipient) -> None:
    child.meters["steps"] += place.difficulty
    child.memes["pride"] += 1
    world.say(
        f"{child.id} opened the door, took one quiet step, then another, then another. "
        f"{parent.label_word.capitalize()} stayed by the doorway, smiling, while {child.id} carried the brave little errand down the hall."
    )
    world.say(
        f"At {recipient.apartment}, {child.pronoun()} knocked softly with one knuckle."
    )


def together_walk(world: World, child: Entity, parent: Entity, place: Place, recipient: Recipient) -> None:
    child.meters["steps"] += place.difficulty
    child.memes["honesty"] += 1
    child.memes["pride"] += 1
    world.say(
        f'{child.id} looked up and whispered, "I want to do it, but I do not want to do it alone."'
    )
    world.say(
        f'{parent.label_word.capitalize()} nodded at once. "That is brave too," {parent.pronoun()} said.'
    )
    world.say(
        f"So they walked together, hand in hand, all the way to {recipient.apartment}, with the sleepy hallway no longer quite so large."
    )


def return_item(world: World, child: Entity, recipient: Recipient, item_ent: Entity) -> None:
    child.meters["delivered"] += 1
    child.memes["relief"] += 1
    world.say(
        f"The door opened just a crack, and {recipient.name} smiled in the warm light. "
        f'"My, my," {recipient.title} said softly. "You found {item_ent.label}."'
    )
    world.say(
        f"{child.id} held it out with both hands, and {recipient.name} thanked {child.pronoun('object')} in the kind, quiet voice people use when the building is settling down for the night."
    )


def bedtime_return(world: World, child: Entity, parent: Entity, recipient: Recipient, place: Place) -> None:
    token = recipient.gives_back
    child.memes["love"] += 1
    child.memes["fear"] = 0.0
    child.memes["sleepy"] += 1
    world.say(
        f"Then {recipient.name} tucked {token} into {child.pronoun('possessive')} hand."
    )
    world.say(
        f'"For your brave walk," {recipient.title} whispered.'
    )
    world.say(
        f"When {child.id} climbed back into bed, {place.label} felt soft and safe again. "
        f"{child.pronoun().capitalize()} closed {child.pronoun('possessive')} fingers around {token} and thought of the directory, the hallway, and the three brave sentences that had carried {child.pronoun('object')} there and back."
    )


def ordinal(n: int) -> str:
    return {1: "first", 2: "second", 3: "third"}.get(n, f"{n}th")


def tell(
    place: Place,
    item: Item,
    recipient: Recipient,
    support: Support,
    refrain: Refrain,
    child_name: str = "Mina",
    child_type: str = "girl",
    parent_type: str = "mother",
    comfort: str = "",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    child.id = child_name
    child.attrs["comfort"] = comfort
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    parent.id = "Parent"
    hall = world.add(Entity(id="hall", type="hallway", label="hallway"))
    board = world.add(Entity(id="directory", type="directory", label="directory"))
    item_ent = world.add(Entity(id="item", type="item", label=item.label, phrase=item.phrase))
    support_ent = world.add(
        Entity(
            id="support",
            type="support",
            label=support.label,
            phrase=support.phrase,
            attrs={"bonus": support.bonus, "accompanies": support.accompanies},
        )
    )

    world.facts.update(
        place=place,
        item_cfg=item,
        recipient=recipient,
        support_cfg=support,
        refrain_cfg=refrain,
        difficulty=place.difficulty,
        comfort=comfort,
        child=child,
        parent=parent,
    )

    bedtime_opening(world, child, parent, item_ent, place)
    discover_task(world, child, item_ent, recipient)

    world.para()
    notice_hall(world, child, place)
    read_directory(world, child, place, recipient)
    parent_offer(world, child, parent, support)
    repeat_refrain(world, child, refrain)

    world.para()
    pred = predict_walk(world)
    world.facts["predicted_courage"] = pred["courage"]
    world.facts["predicted_fear"] = pred["fear"]
    if pred["solo"]:
        solo_walk(world, child, parent, place, recipient)
        outcome = "solo_delivery"
    else:
        together_walk(world, child, parent, place, recipient)
        outcome = "together_delivery"
    return_item(world, child, recipient, item_ent)

    world.para()
    bedtime_return(world, child, parent, recipient, place)
    if comfort:
        world.say(f"Under the blanket, {child.id} pulled {child.pronoun('possessive')} {comfort} close and smiled once more.")

    world.facts.update(
        outcome=outcome,
        delivered=child.meters["delivered"] >= THRESHOLD,
        solo=(outcome == "solo_delivery"),
        repeated=REPETITIONS,
        final_courage=child.memes["courage"] + child.memes["certainty"],
        child_name=child.id,
    )
    return world


PLACES = {
    "apartment": Place(
        id="apartment",
        label="a tall apartment building",
        directory_phrase="a brass directory with tiny black letters",
        hallway_phrase="the carpeted hallway stretched in a long gold stripe",
        light_phrase="only one lamp near the elevator was still glowing",
        difficulty=5,
        floors=8,
        listed={"mrs_dove", "mr_reed", "auntie_jo"},
        tags={"building", "directory"},
    ),
    "inn": Place(
        id="inn",
        label="a little seaside inn",
        directory_phrase="a wooden directory with room numbers painted in blue",
        hallway_phrase="the upstairs hall curved past a row of sleepy doors",
        light_phrase="the wall lamps were low and honey-colored",
        difficulty=4,
        floors=2,
        listed={"mrs_dove", "mr_reed"},
        tags={"building", "directory"},
    ),
    "guesthouse": Place(
        id="guesthouse",
        label="a family guesthouse",
        directory_phrase="a paper directory pinned beside the stairs",
        hallway_phrase="the narrow hall ran past framed pictures and quiet rugs",
        light_phrase="a small night bulb shone at the far end",
        difficulty=3,
        floors=2,
        listed={"auntie_jo", "mr_reed"},
        tags={"building", "directory"},
    ),
}

ITEMS = {
    "storybook": Item(
        id="storybook",
        label="the little storybook",
        phrase="the little storybook with moon stars on the cover",
        pronoun_word="it",
        belongs_to={"mrs_dove"},
        tags={"book", "bedtime"},
    ),
    "bunny": Item(
        id="bunny",
        label="the floppy bunny",
        phrase="the floppy bunny with one velvety ear",
        pronoun_word="it",
        belongs_to={"auntie_jo"},
        tags={"toy", "bedtime"},
    ),
    "scarf": Item(
        id="scarf",
        label="the blue scarf",
        phrase="the blue scarf that smelled faintly of soap",
        pronoun_word="it",
        belongs_to={"mr_reed"},
        tags={"clothing"},
    ),
}

RECIPIENTS = {
    "mrs_dove": Recipient(
        id="mrs_dove",
        name="Mrs. Dove",
        title="Mrs. Dove",
        apartment="4B",
        kind="lady",
        expects={"storybook"},
        gives_back="a silver star sticker",
        tags={"neighbor", "book"},
    ),
    "mr_reed": Recipient(
        id="mr_reed",
        name="Mr. Reed",
        title="Mr. Reed",
        apartment="2A",
        kind="gentleman",
        expects={"scarf"},
        gives_back="a smooth blue marble",
        tags={"neighbor", "scarf"},
    ),
    "auntie_jo": Recipient(
        id="auntie_jo",
        name="Auntie Jo",
        title="Auntie Jo",
        apartment="1C",
        kind="lady",
        expects={"bunny"},
        gives_back="a paper moon bookmark",
        tags={"family", "toy"},
    ),
}

SUPPORTS = {
    "nightlight": Support(
        id="nightlight",
        label="night-light",
        phrase="the little night-light shaped like a pearly moon",
        bonus=2,
        sense=3,
        accompanies=False,
        use_line="Take this moon night-light. Small lights can make long halls feel friendlier.",
        qa_line="used a small night-light to soften the dark",
        tags={"light", "nightlight"},
    ),
    "flashlight": Support(
        id="flashlight",
        label="flashlight",
        phrase="the tiny flashlight from the bedside drawer",
        bonus=2,
        sense=3,
        accompanies=False,
        use_line="Here is the tiny flashlight. Shine it on the floor and on the numbers, and the way will look clearer.",
        qa_line="carried a tiny flashlight to see the floor and room numbers",
        tags={"light", "flashlight"},
    ),
    "parent_hand": Support(
        id="parent_hand",
        label="parent hand",
        phrase="Parent's warm hand",
        bonus=1,
        sense=3,
        accompanies=True,
        use_line="You may hold my hand if you want. Brave does not have to mean lonely.",
        qa_line="walked beside a parent and held a warm hand",
        tags={"help", "bravery"},
    ),
    "shut_eyes": Support(
        id="shut_eyes",
        label="shut eyes",
        phrase="nothing at all",
        bonus=0,
        sense=1,
        accompanies=False,
        use_line="Just close your eyes and hurry down the hall.",
        qa_line="closed their eyes and hurried",
        tags={"unsafe"},
    ),
}

REFRAINS = {
    "step_by_step": Refrain(
        id="step_by_step",
        line="Step by step, I can be brave.",
        gain=1,
        tags={"bravery", "repetition"},
    ),
    "soft_and_sure": Refrain(
        id="soft_and_sure",
        line="Soft feet, slow breath, brave heart.",
        gain=1,
        tags={"bravery", "repetition", "breathing"},
    ),
    "door_to_door": Refrain(
        id="door_to_door",
        line="Door to door, I know my way.",
        gain=1,
        tags={"bravery", "repetition", "directory"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Eva", "Ruby", "Ivy", "June"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Sam", "Eli", "Ben", "Noah", "Leo"]
COMFORTS = ["stuffed fox", "small quilt", "cotton lamb", "fuzzy bear", "little pillow"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for rec_id, recipient in RECIPIENTS.items():
                if is_listed(place, recipient) and item_matches(item, recipient):
                    out.append((place_id, item_id, rec_id))
    return out


@dataclass
class StoryParams:
    place: str
    item: str
    recipient: str
    support: str
    refrain: str
    child_name: str
    child_gender: str
    parent: str
    comfort: str = ""
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    item = f["item_cfg"]
    recipient = f["recipient"]
    refrain = f["refrain_cfg"]
    outcome = f["outcome"]
    if outcome == "solo_delivery":
        return [
            'Write a bedtime story for a 3-to-5-year-old that includes the word "directory".',
            f"Tell a gentle story where {child.id} finds {item.label}, reads a directory, repeats '{refrain.line}', and bravely walks a hallway alone to return it to {recipient.name}.",
            f"Write a soft, sleepy story set in {place.label} where a child grows brave by saying the same comforting words again and again.",
        ]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the word "directory".',
        f"Tell a gentle story where {child.id} finds {item.label}, reads a directory, repeats '{refrain.line}', and discovers that asking for company can be part of being brave.",
        f"Write a soft bedtime story in which a child returns something to {recipient.name} and the repeated brave line helps turn fear into calm.",
    ]


KNOWLEDGE = {
    "directory": [
        (
            "What is a directory?",
            "A directory is a list that tells you where people or rooms are. In a building, it can help you find the right door."
        )
    ],
    "nightlight": [
        (
            "What is a night-light?",
            "A night-light is a small lamp that glows softly in the dark. It helps a room or hallway feel less shadowy without being too bright."
        )
    ],
    "flashlight": [
        (
            "What does a flashlight do?",
            "A flashlight makes a bright beam you can point where you need to see. It helps you find your way in dim places."
        )
    ],
    "bravery": [
        (
            "What can bravery look like?",
            "Bravery can look like taking one careful step even when you feel nervous. It can also mean telling the truth and asking for help."
        )
    ],
    "repetition": [
        (
            "Why do repeated words sometimes help at bedtime?",
            "Repeated words can feel steady and familiar. Saying the same calm line again can help your breathing and your feelings slow down."
        )
    ],
    "neighbors": [
        (
            "Why is it kind to return something that belongs to someone else?",
            "Returning a lost thing helps the owner feel better and keeps the thing from staying missing. It is one way to be thoughtful and helpful."
        )
    ],
}

KNOWLEDGE_ORDER = ["directory", "nightlight", "flashlight", "bravery", "repetition", "neighbors"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    place = f["place"]
    item = f["item_cfg"]
    recipient = f["recipient"]
    support = f["support_cfg"]
    refrain = f["refrain_cfg"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child getting ready for bed, and {child.pronoun('possessive')} {parent.label_word} who helps with a small nighttime errand."
        ),
        (
            f"What did {child.id} find at bedtime?",
            f"{child.id} found {item.phrase}. It belonged to {recipient.name}, so the child wanted to return it before sleep."
        ),
        (
            "How did the directory help?",
            f"The directory showed which room belonged to {recipient.name}. That mattered because the hallway felt big and sleepy, and knowing the right door made the task clearer."
        ),
        (
            f"Why did {child.id} say '{refrain.line}' more than once?",
            f"{child.id} repeated the line three times to feel steadier. The same words came back again and again, and each repetition helped fear loosen a little."
        ),
    ]
    if outcome == "solo_delivery":
        qa.append(
            (
                f"How was {child.id} brave?",
                f"{child.id} felt nervous about the dim hallway but still walked to {recipient.apartment} alone. The child used {support.qa_line} and the repeated brave sentence to keep going step by step."
            )
        )
    else:
        qa.append(
            (
                f"How was {child.id} brave?",
                f"{child.id} was brave by saying the errand mattered and by admitting not wanting to do it alone. Then the child walked with {parent.label_word}, which turned help into part of the courage."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"{recipient.name} thanked {child.id}, and the child came back to bed with {recipient.gives_back} in hand. The ending image shows that the hallway no longer felt so large once kindness and courage had carried the child through it."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"directory", "bravery", "repetition", "neighbors"}
    support = f["support_cfg"]
    if "nightlight" in support.tags:
        tags.add("nightlight")
    if "flashlight" in support.tags:
        tags.add("flashlight")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="apartment",
        item="storybook",
        recipient="mrs_dove",
        support="nightlight",
        refrain="step_by_step",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        comfort="stuffed fox",
    ),
    StoryParams(
        place="guesthouse",
        item="bunny",
        recipient="auntie_jo",
        support="flashlight",
        refrain="door_to_door",
        child_name="Owen",
        child_gender="boy",
        parent="father",
        comfort="small quilt",
    ),
    StoryParams(
        place="inn",
        item="scarf",
        recipient="mr_reed",
        support="parent_hand",
        refrain="soft_and_sure",
        child_name="Ruby",
        child_gender="girl",
        parent="mother",
        comfort="cotton lamb",
    ),
]


ASP_RULES = r"""
% Reasonable story triples
valid(P, I, R) :- place(P), item(I), recipient(R), listed(P, R), belongs_to(I, R).

% Sensible supports only
sensible(S) :- support(S), sense(S, V), sense_min(M), V >= M.

% Outcome model
refrain_total(T) :- chosen_refrain(R), gain(R, G), repetitions(N), T = G * N.
courage_total(B + T + 1) :- chosen_support(S), bonus(S, B), refrain_total(T).
solo_delivery :- chosen_place(P), courage_total(C), difficulty(P, D), C >= D,
                 chosen_support(S), not accompanies(S).
together_delivery :- chosen_support(S), accompanies(S).
together_delivery :- chosen_place(P), chosen_support(S), not accompanies(S),
                     courage_total(C), difficulty(P, D), C < D.

outcome(solo_delivery) :- solo_delivery.
outcome(together_delivery) :- together_delivery.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("difficulty", place_id, place.difficulty))
        for rec in sorted(place.listed):
            lines.append(asp.fact("listed", place_id, rec))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for rec in sorted(item.belongs_to):
            lines.append(asp.fact("belongs_to", item_id, rec))
    for rec_id in RECIPIENTS:
        lines.append(asp.fact("recipient", rec_id))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("bonus", support_id, support.bonus))
        lines.append(asp.fact("sense", support_id, support.sense))
        if support.accompanies:
            lines.append(asp.fact("accompanies", support_id))
    for ref_id, ref in REFRAINS.items():
        lines.append(asp.fact("refrain", ref_id))
        lines.append(asp.fact("gain", ref_id, ref.gain))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("repetitions", REPETITIONS))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_supports() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_support", params.support),
            asp.fact("chosen_refrain", params.refrain),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_supports = set(asp_sensible_supports())
    python_supports = {s.id for s in sensible_supports()}
    if clingo_supports == python_supports:
        print(f"OK: sensible supports match ({sorted(clingo_supports)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible supports: clingo={sorted(clingo_supports)} "
            f"python={sorted(python_supports)}"
        )

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        with redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a child reads a directory, repeats a brave line, and returns a neighbor's lost thing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--refrain", choices=REFRAINS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.support and SUPPORTS[args.support].sense < SENSE_MIN:
        raise StoryError(explain_support(args.support))
    if args.place and args.item and args.recipient:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        recipient = RECIPIENTS[args.recipient]
        if not (is_listed(place, recipient) and item_matches(item, recipient)):
            raise StoryError(explain_rejection(place, item, recipient))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.recipient is None or combo[2] == args.recipient)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, recipient_id = rng.choice(sorted(combos))
    support_id = args.support or rng.choice(sorted(s.id for s in sensible_supports()))
    refrain_id = args.refrain or rng.choice(sorted(REFRAINS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    comfort = rng.choice(COMFORTS + ["", ""])
    return StoryParams(
        place=place_id,
        item=item_id,
        recipient=recipient_id,
        support=support_id,
        refrain=refrain_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        comfort=comfort,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        item = ITEMS[params.item]
        recipient = RECIPIENTS[params.recipient]
        support = SUPPORTS[params.support]
        refrain = REFRAINS[params.refrain]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter choice: {err})") from err

    if support.sense < SENSE_MIN:
        raise StoryError(explain_support(params.support))
    if not (is_listed(place, recipient) and item_matches(item, recipient)):
        raise StoryError(explain_rejection(place, item, recipient))

    world = tell(
        place=place,
        item=item,
        recipient=recipient,
        support=support,
        refrain=refrain,
        child_name=params.child_name,
        child_type=params.child_gender,
        parent_type=params.parent,
        comfort=params.comfort,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible supports: {', '.join(asp_sensible_supports())}\n")
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, item, recipient) combos:\n")
        for place, item, recipient in triples:
            print(f"  {place:10} {item:10} {recipient}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.item} to {p.recipient} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
