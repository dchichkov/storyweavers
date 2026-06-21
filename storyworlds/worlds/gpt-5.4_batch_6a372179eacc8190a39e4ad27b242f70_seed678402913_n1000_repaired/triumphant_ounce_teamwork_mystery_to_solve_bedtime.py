#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/triumphant_ounce_teamwork_mystery_to_solve_bedtime.py
=================================================================================

A standalone storyworld for a gentle bedtime mystery: a child cannot settle down
because a beloved bedtime thing has gone missing, and two children work together
to solve the mystery before sleep.

The domain is deliberately small and constraint-checked:

- a missing bedtime item
- one plausible hiding spot
- one clue that honestly points toward that spot and item
- one search tool that actually helps with that spot
- a teamwork outcome: either the children solve it together, or a calm grown-up
  helps once the children get too flustered

The rendered story is driven by simulated state: worry rises when the item is
missing, hope rises when a clue is found, and the ending depends on whether the
children stay calm enough to finish the search together.

Run it
------
    python storyworlds/worlds/gpt-5.4/triumphant_ounce_teamwork_mystery_to_solve_bedtime.py
    python storyworlds/worlds/gpt-5.4/triumphant_ounce_teamwork_mystery_to_solve_bedtime.py --item bunny --spot under_bed
    python storyworlds/worlds/gpt-5.4/triumphant_ounce_teamwork_mystery_to_solve_bedtime.py --tool stool --spot under_bed
    python storyworlds/worlds/gpt-5.4/triumphant_ounce_teamwork_mystery_to_solve_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/triumphant_ounce_teamwork_mystery_to_solve_bedtime.py --qa --json
    python storyworlds/worlds/gpt-5.4/triumphant_ounce_teamwork_mystery_to_solve_bedtime.py --verify
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
class BedItem:
    id: str
    label: str
    phrase: str
    soft: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    preposition: str
    dark: bool = False
    high: bool = False
    clue_here: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_dark: bool = False
    helps_high: bool = False
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"seeker", "helper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    room = world.get("room")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["mystery"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return []


def _r_clue_hope(world: World) -> list[str]:
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["hope"] += 1
            # no narration here; the screenplay narrates the clue beat
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["triumph"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="clue_hope", tag="emotion", apply=_r_clue_hope),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


ITEMS = {
    "bunny": BedItem(
        id="bunny",
        label="bunny",
        phrase="a velvety bunny with one sleepy ear",
        soft=True,
        tags={"bunny", "bedtime_item"},
    ),
    "blanket": BedItem(
        id="blanket",
        label="blanket",
        phrase="a little moon-pattern blanket",
        soft=True,
        tags={"blanket", "bedtime_item"},
    ),
    "storybook": BedItem(
        id="storybook",
        label="storybook",
        phrase="a small blue storybook",
        soft=False,
        tags={"book", "bedtime_item"},
    ),
}

SPOTS = {
    "under_bed": Spot(
        id="under_bed",
        label="under the bed",
        phrase="the dark space under the bed",
        preposition="under",
        dark=True,
        high=False,
        clue_here="dust",
        tags={"under_bed", "dark"},
    ),
    "bookshelf": Spot(
        id="bookshelf",
        label="on the top bookshelf",
        phrase="the top shelf beside the moon lamp",
        preposition="on",
        dark=False,
        high=True,
        clue_here="paper",
        tags={"bookshelf", "high"},
    ),
    "laundry_basket": Spot(
        id="laundry_basket",
        label="in the laundry basket",
        phrase="the warm basket of folded pajamas and socks",
        preposition="in",
        dark=False,
        high=False,
        clue_here="lavender",
        tags={"laundry", "basket"},
    ),
    "window_seat": Spot(
        id="window_seat",
        label="behind the window cushion",
        phrase="the soft window seat by the curtains",
        preposition="behind",
        dark=False,
        high=False,
        clue_here="ribbon",
        tags={"window", "seat"},
    ),
}

CLUES = {
    "dust": Clue(
        id="dust",
        label="dust bunny",
        phrase="a tiny dust bunny",
        text="A tiny dust bunny clung to the floor, right where small hands had been peeking.",
        tags={"dust", "under_bed"},
    ),
    "paper": Clue(
        id="paper",
        label="paper corner",
        phrase="a peeking paper corner",
        text="A neat paper corner peeked out high above their heads near the moon lamp.",
        tags={"paper", "bookshelf"},
    ),
    "lavender": Clue(
        id="lavender",
        label="lavender smell",
        phrase="a sleepy lavender smell",
        text="A sleepy lavender smell drifted from the basket of clean things.",
        tags={"lavender", "laundry"},
    ),
    "ribbon": Clue(
        id="ribbon",
        label="silver ribbon",
        phrase="a silver ribbon thread",
        text="A silver ribbon thread shimmered beside the window cushion.",
        tags={"ribbon", "window"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        helps_dark=True,
        helps_high=False,
        tags={"flashlight", "light"},
    ),
    "stool": Tool(
        id="stool",
        label="stool",
        phrase="a little wooden stool",
        helps_dark=False,
        helps_high=True,
        tags={"stool", "reach"},
    ),
    "basket_hands": Tool(
        id="basket_hands",
        label="careful hands",
        phrase="their careful hands",
        helps_dark=False,
        helps_high=False,
        tags={"hands", "careful"},
    ),
}

ITEM_SPOTS = {
    "bunny": {"under_bed", "window_seat"},
    "blanket": {"laundry_basket", "window_seat"},
    "storybook": {"bookshelf", "laundry_basket"},
}

ITEM_CLUES = {
    "bunny": {"dust", "ribbon"},
    "blanket": {"lavender", "ribbon"},
    "storybook": {"paper", "lavender"},
}

CLUE_SPOTS = {
    "dust": {"under_bed"},
    "paper": {"bookshelf"},
    "lavender": {"laundry_basket"},
    "ribbon": {"window_seat"},
}


def clue_matches(item_id: str, clue_id: str, spot_id: str) -> bool:
    return (
        clue_id in ITEM_CLUES[item_id]
        and spot_id in ITEM_SPOTS[item_id]
        and spot_id in CLUE_SPOTS[clue_id]
    )


def tool_works(tool: Tool, spot: Spot) -> bool:
    if spot.dark and not tool.helps_dark:
        return False
    if spot.high and not tool.helps_high:
        return False
    if not spot.dark and not spot.high and tool.id != "basket_hands":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for item_id in sorted(ITEMS):
        for spot_id in sorted(SPOTS):
            for clue_id in sorted(CLUES):
                if not clue_matches(item_id, clue_id, spot_id):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_works(tool, SPOTS[spot_id]):
                        combos.append((item_id, spot_id, clue_id, tool_id))
    return combos


@dataclass
class StoryParams:
    item: str
    spot: str
    clue: str
    tool: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
    parent: str
    relation: str = "siblings"
    calm: int = 2
    teamwork: int = 2
    seed: Optional[int] = None


def introduce_room(world: World, seeker: Entity, helper: Entity, parent: Entity, item: BedItem) -> None:
    item_ent = world.get("item")
    item_ent.meters["missing"] = 1
    propagate(world)
    world.say(
        f"The house had gone soft and dim, and {seeker.id}'s {parent.label_word} was already turning down the hall light."
    )
    world.say(
        f"{seeker.id} climbed into bed, reached for {item.phrase}, and found only a cool wrinkle in the sheet."
    )
    world.say(
        f'"My {item.label} is gone," {seeker.id} whispered. At once, {helper.id} sat up too, with not an ounce of sleepiness left.'
    )


def decide_to_help(world: World, seeker: Entity, helper: Entity, relation: str) -> None:
    helper.memes["care"] += 1
    seeker.memes["trust"] += 1
    pair_word = "sister" if relation == "siblings" and helper.type == "girl" else ""
    if relation == "siblings" and helper.type == "boy":
        pair_word = "brother"
    if pair_word:
        world.say(
            f'"Then we will solve it together," said {helper.id}, sounding very much like a brave big {pair_word}.'
        )
    else:
        world.say(f'"Then we will solve it together," said {helper.id}.')
    world.say("The room felt like a small mystery waiting for kind eyes and quiet feet.")


def notice_clue(world: World, seeker: Entity, helper: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] = 1
    propagate(world)
    world.say(
        f"They looked slowly instead of wildly, and soon {helper.id} noticed {clue.phrase}."
    )
    world.say(clue.text)


def choose_tool(world: World, seeker: Entity, helper: Entity, tool: Tool, spot: Spot) -> None:
    if tool.id == "flashlight":
        world.say(
            f'{seeker.id} held {tool.phrase}, and its little beam slid into {spot.phrase}.'
        )
    elif tool.id == "stool":
        world.say(
            f"{helper.id} steadied {tool.phrase} while {seeker.id} climbed up one careful step at a time."
        )
    else:
        world.say(
            f"{seeker.id} and {helper.id} used {tool.phrase}, lifting and peeking gently so nothing tumbled."
        )


def mystery_difficulty(spot: Spot) -> int:
    return 2 + int(spot.dark) + int(spot.high)


def team_score(params: StoryParams) -> int:
    return params.calm + params.teamwork


def outcome_of(params: StoryParams) -> str:
    if team_score(params) >= mystery_difficulty(SPOTS[params.spot]):
        return "team_found"
    return "parent_helped"


def search_together(world: World, seeker: Entity, helper: Entity, item: BedItem, spot: Spot) -> None:
    item_ent = world.get("item")
    item_ent.meters["found"] = 1
    item_ent.meters["missing"] = 0
    propagate(world)
    if spot.id == "under_bed":
        world.say(
            f"There, under a sleepy stripe of shadow, lay the {item.label}, waiting as quietly as a mouse."
        )
    elif spot.id == "bookshelf":
        world.say(
            f"At the very top, tucked beside other books, rested the {item.label} as if it had climbed up for one more story."
        )
    elif spot.id == "laundry_basket":
        world.say(
            f"Folded between pajamas, they found the {item.label}, warm and sweet-smelling from the clean clothes."
        )
    else:
        world.say(
            f"Behind the window cushion, they found the {item.label}, hiding where moonlight touched the fabric."
        )
    world.say(
        f'{seeker.id} hugged it close, and {helper.id} gave a small triumphant grin.'
    )


def parent_finishes(world: World, seeker: Entity, helper: Entity, parent: Entity, item: BedItem, spot: Spot) -> None:
    parent.memes["calm"] += 1
    world.say(
        f"But the mystery felt bigger the faster they hurried, and soon {seeker.id}'s eyes were shining with tired tears."
    )
    world.say(
        f"{parent.label_word.capitalize()} came in on soft feet, listened to both clues, and knelt beside them."
    )
    item_ent = world.get("item")
    item_ent.meters["found"] = 1
    item_ent.meters["missing"] = 0
    propagate(world)
    world.say(
        f'"You already found the right trail," {parent.pronoun()} said. "Now let us finish it slowly."'
    )
    if spot.id == "under_bed":
        world.say(
            f"With the light held steady, they reached into the dark space and drew out the {item.label}."
        )
    elif spot.id == "bookshelf":
        world.say(
            f"With one steady lift, {parent.label_word} reached the top shelf and brought down the {item.label}."
        )
    elif spot.id == "laundry_basket":
        world.say(
            f"Together they turned down the top towel and uncovered the {item.label} in the laundry basket."
        )
    else:
        world.say(
            f"Together they eased back the window cushion and discovered the {item.label} there in the moonlight."
        )
    world.say(
        f"The children had started the mystery together, and together with {parent.label_word} they ended it."
    )


def bedtime_close(world: World, seeker: Entity, helper: Entity, parent: Entity, item: BedItem, outcome: str) -> None:
    seeker.memes["sleepy"] += 1
    helper.memes["sleepy"] += 1
    if outcome == "team_found":
        world.say(
            f"Soon {seeker.id} was tucked in again with the {item.label} under one arm, while {helper.id} curled nearby feeling proud and peaceful."
        )
        world.say(
            f"{parent.label_word.capitalize()} kissed both foreheads and said the room was full of excellent detectives."
        )
    else:
        world.say(
            f"Soon {seeker.id} was tucked in again with the {item.label} safe and warm, while {helper.id} leaned against the pillow, proud that the clues had mattered."
        )
        world.say(
            f"{parent.label_word.capitalize()} kissed both foreheads and said that the best mysteries are solved by calm hearts working together."
        )
    world.say(
        "Outside, the night stayed quiet, and inside the small room the mystery was gone at last."
    )


def tell(
    item: BedItem,
    spot: Spot,
    clue: Clue,
    tool: Tool,
    seeker_name: str,
    seeker_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
    relation: str,
    calm: int,
    teamwork: int,
) -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="bedroom", label="bedroom"))
    item_ent = world.add(Entity(id="item", type="bed_item", label=item.label, phrase=item.phrase, tags=set(item.tags)))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label, phrase=clue.phrase, tags=set(clue.tags)))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))
    spot_ent = world.add(Entity(id="spot", type="spot", label=spot.label, phrase=spot.phrase, tags=set(spot.tags)))

    seeker.memes["calm"] = float(calm)
    helper.memes["calm"] = float(calm)
    seeker.memes["teamwork"] = float(teamwork)
    helper.memes["teamwork"] = float(teamwork)
    room.meters["night"] = 1
    spot_ent.meters["dark"] = 1.0 if spot.dark else 0.0
    spot_ent.meters["high"] = 1.0 if spot.high else 0.0

    introduce_room(world, seeker, helper, parent, item)
    world.para()
    decide_to_help(world, seeker, helper, relation)
    notice_clue(world, seeker, helper, clue)
    choose_tool(world, seeker, helper, tool, spot)
    world.para()

    outcome = "team_found" if calm + teamwork >= mystery_difficulty(spot) else "parent_helped"
    if outcome == "team_found":
        search_together(world, seeker, helper, item, spot)
    else:
        parent_finishes(world, seeker, helper, parent, item, spot)

    world.para()
    bedtime_close(world, seeker, helper, parent, item, outcome)
    world.facts.update(
        seeker=seeker,
        helper=helper,
        parent=parent,
        room=room,
        item_cfg=item,
        spot_cfg=spot,
        clue_cfg=clue,
        tool_cfg=tool,
        outcome=outcome,
        relation=relation,
        calm=calm,
        teamwork=teamwork,
        difficulty=mystery_difficulty(spot),
    )
    return world


KNOWLEDGE = {
    "bedtime_item": [
        (
            "Why do children sometimes want a special bedtime thing?",
            "A special bedtime thing can feel familiar and cozy. It helps bedtime feel safe and calm."
        )
    ],
    "bunny": [
        (
            "Why can a stuffed bunny help at bedtime?",
            "A stuffed bunny is soft to hold, and that can help a child feel comforted. Familiar touch can make it easier to settle down."
        )
    ],
    "blanket": [
        (
            "Why does a little blanket feel comforting?",
            "A blanket feels warm and soft, and its familiar smell can help a child relax. Cozy things often make bedtime gentler."
        )
    ],
    "book": [
        (
            "Why do storybooks belong near bedtime?",
            "Storybooks help slow the day down with quiet words and pictures. A calm story can help sleepy feelings arrive."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight good for?",
            "A flashlight helps you see in dark places. It lets you look carefully without turning the whole room bright."
        )
    ],
    "stool": [
        (
            "What is a stool for?",
            "A stool helps someone reach a high place safely. It is useful when something is up on a shelf."
        )
    ],
    "laundry": [
        (
            "Why do clean clothes sometimes smell nice?",
            "Clean clothes may smell nice because of soap or laundry spray. That smell can make a basket easier to notice."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery calmly?",
            "You slow down, look for clues, and share what you notice. Calm teamwork helps people think clearly."
        )
    ],
    "teamwork": [
        (
            "What does teamwork mean?",
            "Teamwork means people help one another instead of trying to do everything alone. One person may notice a clue that another person misses."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "teamwork",
    "mystery",
    "bunny",
    "blanket",
    "book",
    "flashlight",
    "stool",
    "laundry",
    "bedtime_item",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    item = f["item_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a bedtime story for a 3-to-5-year-old about a missing {item.label}, a clue, and teamwork. '
        f'Include the words "triumphant" and "ounce".'
    )
    if outcome == "team_found":
        return [
            base,
            f"Tell a gentle mystery where {seeker.id} and {helper.id} stay calm, follow a clue, and find the missing {item.label} together before bed.",
            f"Write a cozy story about two children solving a small bedtime mystery with teamwork and ending in a peaceful tucked-in scene.",
        ]
    return [
        base,
        f"Tell a gentle bedtime mystery where {seeker.id} and {helper.id} begin the search together, but a calm grown-up helps them finish once they get tired.",
        f"Write a cozy story where clues matter, teamwork matters, and the ending teaches that slowing down helps solve bedtime problems.",
    ]


def pair_noun(seeker: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if seeker.type == "girl" and helper.type == "girl":
            return "two sisters"
        if seeker.type == "boy" and helper.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    parent = f["parent"]
    item = f["item_cfg"]
    clue = f["clue_cfg"]
    spot = f["spot_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    pair = pair_noun(seeker, helper, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {seeker.id} and {helper.id}, during a small bedtime mystery. {seeker.id}'s {item.label} went missing, and they tried to solve it together."
        ),
        (
            f"Why was {seeker.id} upset at bedtime?",
            f"{seeker.id} reached for the {item.label} and could not find it in bed. That made bedtime feel wrong, because the missing {item.label} was part of feeling cozy and ready for sleep."
        ),
        (
            "What clue did the children find?",
            f"They found {clue.phrase}. The clue mattered because it pointed them toward {spot.label}."
        ),
        (
            f"How did they work together?",
            f"They did not rush wildly. One child noticed the clue, and together they used {tool.phrase} to keep searching in a careful way."
        ),
    ]
    if outcome == "team_found":
        qa.append(
            (
                "How was the mystery solved?",
                f"The children solved it themselves and found the {item.label} {spot.label}. They could do that because they stayed calm enough to follow the clue all the way to the hiding place."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a triumphant but peaceful feeling. {seeker.id} was tucked in again with the {item.label}, and the room felt calm instead of worried."
            )
        )
    else:
        qa.append(
            (
                f"Did the children solve the mystery all by themselves?",
                f"Not quite. They found the right clue first, but they grew too tired to finish, so {pw} helped with the last step. Their teamwork still mattered because it led the grown-up to the right place."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely and softly, with the {item.label} found and bedtime restored. The mystery was solved when calm hearts and helping hands worked together."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"teamwork", "mystery", "bedtime_item"}
    tags |= set(f["item_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
    tags |= set(f["spot_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="bunny",
        spot="under_bed",
        clue="dust",
        tool="flashlight",
        seeker="Lila",
        seeker_gender="girl",
        helper="Ben",
        helper_gender="boy",
        parent="mother",
        relation="siblings",
        calm=2,
        teamwork=2,
    ),
    StoryParams(
        item="storybook",
        spot="bookshelf",
        clue="paper",
        tool="stool",
        seeker="Noah",
        seeker_gender="boy",
        helper="Maya",
        helper_gender="girl",
        parent="father",
        relation="friends",
        calm=1,
        teamwork=1,
    ),
    StoryParams(
        item="blanket",
        spot="laundry_basket",
        clue="lavender",
        tool="basket_hands",
        seeker="Ava",
        seeker_gender="girl",
        helper="Zoe",
        helper_gender="girl",
        parent="mother",
        relation="siblings",
        calm=2,
        teamwork=1,
    ),
    StoryParams(
        item="bunny",
        spot="window_seat",
        clue="ribbon",
        tool="basket_hands",
        seeker="Eli",
        seeker_gender="boy",
        helper="Finn",
        helper_gender="boy",
        parent="father",
        relation="siblings",
        calm=1,
        teamwork=2,
    ),
]


GIRL_NAMES = ["Lila", "Maya", "Nora", "Ava", "Zoe", "Ella", "Lucy", "Ruby"]
BOY_NAMES = ["Ben", "Noah", "Eli", "Finn", "Sam", "Theo", "Leo", "Owen"]


def explain_combo(item_id: str, spot_id: str, clue_id: str, tool_id: str) -> str:
    if spot_id not in ITEM_SPOTS[item_id]:
        return (
            f"(No story: a {ITEMS[item_id].label} does not plausibly go missing at {SPOTS[spot_id].label} in this world.)"
        )
    if clue_id not in ITEM_CLUES[item_id] or spot_id not in CLUE_SPOTS[clue_id]:
        return (
            f"(No story: the clue '{clue_id}' does not honestly point from the {ITEMS[item_id].label} to {SPOTS[spot_id].label}.)"
        )
    if not tool_works(TOOLS[tool_id], SPOTS[spot_id]):
        return (
            f"(No story: {TOOLS[tool_id].label} does not actually help with searching {SPOTS[spot_id].label}. Pick a tool that fits the spot.)"
        )
    return "(No story: this bedtime mystery is unreasonable.)"


ASP_RULES = r"""
possible_item_spot(I,S) :- item(I), spot(S), item_can_hide(I,S).
possible_clue(I,C) :- item(I), clue(C), item_can_leave_clue(I,C).
matching_clue_spot(C,S) :- clue(C), spot(S), clue_points_to(C,S).
usable_tool(T,S) :- tool(T), spot(S), spot_dark(S), tool_dark(T).
usable_tool(T,S) :- tool(T), spot(S), spot_high(S), tool_high(T).
usable_tool(T,S) :- tool(T), spot(S), not spot_dark(S), not spot_high(S), base_tool(T).

valid(I,S,C,T) :- possible_item_spot(I,S), possible_clue(I,C), matching_clue_spot(C,S), usable_tool(T,S).

difficulty(S,2) :- spot(S), not spot_dark(S), not spot_high(S).
difficulty(S,3) :- spot(S), spot_dark(S), not spot_high(S).
difficulty(S,3) :- spot(S), not spot_dark(S), spot_high(S).
difficulty(S,4) :- spot(S), spot_dark(S), spot_high(S).

score(V) :- calm(C), teamwork(T), V = C + T.

outcome(team_found) :- chosen_spot(S), difficulty(S,D), score(V), V >= D.
outcome(parent_helped) :- chosen_spot(S), difficulty(S,D), score(V), V < D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id in sorted(ITEMS):
        lines.append(asp.fact("item", item_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.dark:
            lines.append(asp.fact("spot_dark", spot_id))
        if spot.high:
            lines.append(asp.fact("spot_high", spot_id))
    for clue_id in sorted(CLUES):
        lines.append(asp.fact("clue", clue_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.helps_dark:
            lines.append(asp.fact("tool_dark", tool_id))
        if tool.helps_high:
            lines.append(asp.fact("tool_high", tool_id))
        if tool.id == "basket_hands":
            lines.append(asp.fact("base_tool", tool_id))
    for item_id, spots in ITEM_SPOTS.items():
        for spot_id in sorted(spots):
            lines.append(asp.fact("item_can_hide", item_id, spot_id))
    for item_id, clues in ITEM_CLUES.items():
        for clue_id in sorted(clues):
            lines.append(asp.fact("item_can_leave_clue", item_id, clue_id))
    for clue_id, spots in CLUE_SPOTS.items():
        for spot_id in sorted(spots):
            lines.append(asp.fact("clue_points_to", clue_id, spot_id))
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
            asp.fact("chosen_spot", params.spot),
            asp.fact("calm", params.calm),
            asp.fact("teamwork", params.teamwork),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime mystery solved with teamwork."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--calm", type=int, choices=[1, 2, 3])
    ap.add_argument("--teamwork", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [name for name in pool if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.spot and args.clue:
        if not clue_matches(args.item, args.clue, args.spot):
            tool_id = args.tool or "basket_hands"
            raise StoryError(explain_combo(args.item, args.spot, args.clue, tool_id))
    if args.spot and args.tool:
        if not tool_works(TOOLS[args.tool], SPOTS[args.spot]):
            item_id = args.item or next(iter(ITEMS))
            clue_id = args.clue or next(iter(CLUES))
            raise StoryError(explain_combo(item_id, args.spot, clue_id, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.spot is None or combo[1] == args.spot)
        and (args.clue is None or combo[2] == args.clue)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, spot_id, clue_id, tool_id = rng.choice(sorted(combos))
    seeker_name, seeker_gender = _pick_kid(rng)
    helper_name, helper_gender = _pick_kid(rng, avoid=seeker_name)
    return StoryParams(
        item=item_id,
        spot=spot_id,
        clue=clue_id,
        tool=tool_id,
        seeker=seeker_name,
        seeker_gender=seeker_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        relation=args.relation or rng.choice(["siblings", "friends"]),
        calm=args.calm if args.calm is not None else rng.choice([1, 2, 3]),
        teamwork=args.teamwork if args.teamwork is not None else rng.choice([1, 2, 3]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if not clue_matches(params.item, params.clue, params.spot):
        raise StoryError(explain_combo(params.item, params.spot, params.clue, params.tool))
    if not tool_works(TOOLS[params.tool], SPOTS[params.spot]):
        raise StoryError(explain_combo(params.item, params.spot, params.clue, params.tool))

    world = tell(
        item=ITEMS[params.item],
        spot=SPOTS[params.spot],
        clue=CLUES[params.clue],
        tool=TOOLS[params.tool],
        seeker_name=params.seeker,
        seeker_gender=params.seeker_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        relation=params.relation,
        calm=params.calm,
        teamwork=params.teamwork,
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

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            mismatches.append((params, py, asp))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")
        for params, py, asp in mismatches[:5]:
            print(" ", params, py, asp)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, spot, clue, tool) combos:\n")
        for item_id, spot_id, clue_id, tool_id in combos:
            print(f"  {item_id:10} {spot_id:15} {clue_id:10} {tool_id}")
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
            header = f"### {p.seeker} & {p.helper}: {p.item} at {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
