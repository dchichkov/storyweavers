#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/resistant_hunch_dialogue_mystery_to_solve_sharing.py
==============================================================================

A standalone story world for a tiny child-facing whodunit: a shared object goes
missing, one child has a hunch, another is resistant to blaming anyone too
quickly, and the mystery is solved through kind dialogue and sharing.

The domain is deliberately small and constraint-checked. A story is only valid
when:
- the chosen place can host the borrower's helpful task,
- the missing item actually fits that task,
- the clue really points toward that item, and
- the chosen approach is courteous enough for a child-facing solution.

The stories are not about punishment or tricking a culprit. The "whodunit"
feeling comes from a missing object, a clue, a careful hunch, and a gentle
reveal that turns worry into cooperative sharing.

Run it
------
    python storyworlds/worlds/gpt-5.4/resistant_hunch_dialogue_mystery_to_solve_sharing.py
    python storyworlds/worlds/gpt-5.4/resistant_hunch_dialogue_mystery_to_solve_sharing.py --place classroom --item marker --need welcome_sign
    python storyworlds/worlds/gpt-5.4/resistant_hunch_dialogue_mystery_to_solve_sharing.py --approach corner_everyone
    python storyworlds/worlds/gpt-5.4/resistant_hunch_dialogue_mystery_to_solve_sharing.py --all
    python storyworlds/worlds/gpt-5.4/resistant_hunch_dialogue_mystery_to_solve_sharing.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/resistant_hunch_dialogue_mystery_to_solve_sharing.py --trace
    python storyworlds/worlds/gpt-5.4/resistant_hunch_dialogue_mystery_to_solve_sharing.py --verify
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
COURTESY_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "teacher_f"}
        male = {"boy", "father", "dad", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher_f": "teacher",
            "teacher_m": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    intro: str
    hide_spot: str
    afford_need: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    shared_use: str
    texture: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    item: str
    places: set[str]
    borrower_goal: str
    reveal_text: str
    sharing_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    item: str
    notice_text: str
    hint_spot: str
    clue_object: str
    strength: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    courtesy: int
    patience: int
    ask_line: str
    follow_line: str
    qa_text: str
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


def _r_missing_makes_mystery(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("sleuth").memes["mystery"] += 1
    world.get("friend").memes["mystery"] += 1
    world.get("teacher").memes["worry"] += 1
    return ["__mystery__"]


def _r_clue_feeds_hunch(world: World) -> list[str]:
    item = world.entities.get("item")
    clue = world.entities.get("clue")
    if item is None or clue is None:
        return []
    if item.meters["missing"] < THRESHOLD or clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("hunch", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("sleuth").memes["hunch"] += 1
    return ["__hunch__"]


def _r_return_solves(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["missing"] >= THRESHOLD:
        return []
    if item.meters["returned"] < THRESHOLD:
        return []
    sig = ("solved", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("sleuth", "friend", "borrower", "teacher"):
        world.get(eid).memes["relief"] += 1
    world.get("sleuth").memes["trust"] += 1
    world.get("friend").memes["trust"] += 1
    world.get("borrower").memes["belonging"] += 1
    world.get("teacher").memes["pride"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="missing_makes_mystery", tag="social", apply=_r_missing_makes_mystery),
    Rule(name="clue_feeds_hunch", tag="social", apply=_r_clue_feeds_hunch),
    Rule(name="return_solves", tag="social", apply=_r_return_solves),
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
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(place_id: str, item_id: str, need_id: str, clue_id: str) -> bool:
    place = PLACES[place_id]
    need = NEEDS[need_id]
    clue = CLUES[clue_id]
    return (
        need.item == item_id
        and clue.item == item_id
        and place_id in need.places
        and need_id in place.afford_need
    )


def sensible_approaches() -> list[Approach]:
    return [a for a in APPROACHES.values() if a.courtesy >= COURTESY_MIN]


def outcome_of(params: "StoryParams") -> str:
    approach = APPROACHES[params.approach]
    return "quick_confession" if approach.courtesy >= 3 else "trail_then_talk"


def explain_combo_rejection(place_id: str, item_id: str, need_id: str, clue_id: str) -> str:
    place = PLACES[place_id]
    item = ITEMS[item_id]
    need = NEEDS[need_id]
    clue = CLUES[clue_id]
    if need.item != item_id:
        good = ITEMS[need.item].label
        return (
            f"(No story: the need '{need_id}' calls for {good}, not {item.label}. "
            f"The borrowed item must really help with the borrower's task.)"
        )
    if clue.item != item_id:
        good = ITEMS[clue.item].label
        return (
            f"(No story: the clue '{clue_id}' points toward {good}, not {item.label}. "
            f"The mystery clue must honestly fit the missing item.)"
        )
    if place_id not in need.places or need_id not in place.afford_need:
        return (
            f"(No story: {need.borrower_goal} does not fit naturally in {place.label}. "
            f"Pick a place that really affords that helpful task.)"
        )
    return "(No story: this combination does not form a reasonable mystery.)"


def explain_approach_rejection(approach_id: str) -> str:
    approach = APPROACHES[approach_id]
    better = ", ".join(sorted(a.id for a in sensible_approaches()))
    return (
        f"(Refusing approach '{approach_id}': it is too harsh for this world "
        f"(courtesy={approach.courtesy} < {COURTESY_MIN}). Try: {better}.)"
    )


def predict_resolution(world: World, approach: Approach) -> dict:
    sim = world.copy()
    if approach.courtesy >= 3:
        sim.get("borrower").memes["heard_kindness"] += 1
        return {"outcome": "quick_confession", "solved": True}
    sim.get("clue").meters["followed"] += 1
    return {"outcome": "trail_then_talk", "solved": True}


def scene_setup(world: World, place: Place, item_cfg: Item, teacher: Entity,
                sleuth: Entity, friend: Entity) -> None:
    world.say(
        f"It was sharing time in {place.label}. {place.intro} On the middle table "
        f"rested {item_cfg.phrase}, {item_cfg.texture}, for everyone to use."
    )
    world.say(
        f'{teacher.id} smiled at {sleuth.id} and {friend.id}. '
        f'"Today we will take turns and help one another," {teacher.pronoun()} said.'
    )


def discover_missing(world: World, item: Entity, item_cfg: Item, sleuth: Entity,
                     friend: Entity, teacher: Entity) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {sleuth.id} reached for {item_cfg.label}, it was gone."
    )
    world.say(
        f'"The {item_cfg.label} was right here," {friend.id} whispered. '
        f'"Now it is missing."'
    )
    world.say(
        f'{teacher.id} looked over the table. "Then we have a small mystery to solve," '
        f'{teacher.pronoun()} said.'
    )


def notice_clue(world: World, clue_cfg: Clue, sleuth: Entity, friend: Entity) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(clue_cfg.notice_text)
    world.say(
        f'"I have a hunch," {sleuth.id} said softly. '
        f'"Maybe the clue is trying to tell us something."'
    )
    world.say(
        f'"Maybe," said {friend.id}, "but I am resistant to blaming anyone before we ask kindly."'
    )


def plan_talk(world: World, approach: Approach, sleuth: Entity, friend: Entity,
              teacher: Entity, prediction: dict) -> None:
    friend.memes["fairness"] += 1
    sleuth.memes["care"] += 1
    world.say(
        f'{teacher.id} nodded. "{approach.ask_line}"'
    )
    if prediction["outcome"] == "quick_confession":
        world.say(
            f'{sleuth.id} held the clue carefully instead of waving it around. '
            f'{friend.id} stayed beside {sleuth.pronoun("object")} so the mystery would stay gentle.'
        )
    else:
        world.say(
            f'{sleuth.id} whispered, "{approach.follow_line}" '
            f'and {friend.id} agreed to look first and speak second.'
        )


def quick_confession(world: World, place: Place, item_cfg: Item, need: Need,
                     borrower: Entity, sleuth: Entity, friend: Entity) -> None:
    borrower.memes["heard_kindness"] += 1
    borrower.memes["apology"] += 1
    world.say(
        f'From {place.hide_spot}, {borrower.id} stepped out with {item_cfg.phrase} in both hands. '
        f'"I borrowed it," {borrower.pronoun()} admitted. "I heard you talking kindly, so I wanted to answer right away."'
    )
    world.say(need.reveal_text)


def follow_trail(world: World, place: Place, clue_cfg: Clue, item_cfg: Item,
                 need: Need, borrower: Entity, sleuth: Entity, friend: Entity) -> None:
    clue = world.get("clue")
    clue.meters["followed"] += 1
    borrower.memes["apology"] += 1
    world.say(
        f'The two children followed the clue toward {clue_cfg.hint_spot}. '
        f'There they found {borrower.id}, kneeling beside {clue_cfg.clue_object}, with {item_cfg.phrase} tucked near {borrower.pronoun("possessive")} elbow.'
    )
    world.say(
        f'"We are not here to scold," {friend.id} said. "We just want to understand."'
    )
    world.say(need.reveal_text)


def return_and_share(world: World, item: Entity, item_cfg: Item, need: Need,
                     borrower: Entity, teacher: Entity, sleuth: Entity, friend: Entity) -> None:
    item.meters["missing"] = 0.0
    item.meters["returned"] += 1
    item.meters["shared"] += 1
    borrower.memes["generous"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{borrower.id} set the {item_cfg.label} back on the table and looked at everyone. '
        f'"I should have told you first," {borrower.pronoun()} said.'
    )
    world.say(
        need.sharing_text
    )
    world.say(
        f'{teacher.id} smiled. "That is how a mystery should end here," {teacher.pronoun()} said. '
        f'"With honest words and sharing."'
    )
    world.say(
        f'Soon {sleuth.id}, {friend.id}, and {borrower.id} were using {item_cfg.phrase} together, '
        f'and the room no longer felt puzzled at all.'
    )


def tell(place: Place, item_cfg: Item, need: Need, clue_cfg: Clue, approach: Approach,
         sleuth_name: str = "Nora", sleuth_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         borrower_name: str = "Mia", borrower_gender: str = "girl",
         teacher_type: str = "teacher_f") -> World:
    world = World()
    sleuth = world.add(Entity(id=sleuth_name, kind="character", type=sleuth_gender, role="sleuth"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    borrower = world.add(Entity(id=borrower_name, kind="character", type=borrower_gender, role="borrower"))
    teacher_name = "Ms. Reed" if teacher_type == "teacher_f" else "Mr. Dale"
    teacher = world.add(
        Entity(id=teacher_name, kind="character", type=teacher_type, role="teacher", label="the teacher")
    )
    item = world.add(
        Entity(id="item", kind="thing", type="item", label=item_cfg.label, phrase=item_cfg.phrase, tags=set(item_cfg.tags))
    )
    world.add(
        Entity(id="clue", kind="thing", type="clue", label=clue_cfg.clue_object, tags=set(clue_cfg.tags))
    )

    scene_setup(world, place, item_cfg, teacher, sleuth, friend)
    world.para()
    discover_missing(world, item, item_cfg, sleuth, friend, teacher)
    notice_clue(world, clue_cfg, sleuth, friend)

    world.para()
    prediction = predict_resolution(world, approach)
    plan_talk(world, approach, sleuth, friend, teacher, prediction)

    if prediction["outcome"] == "quick_confession":
        quick_confession(world, place, item_cfg, need, borrower, sleuth, friend)
    else:
        follow_trail(world, place, clue_cfg, item_cfg, need, borrower, sleuth, friend)

    world.para()
    return_and_share(world, item, item_cfg, need, borrower, teacher, sleuth, friend)

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        need=need,
        clue_cfg=clue_cfg,
        approach=approach,
        teacher=teacher,
        sleuth=sleuth,
        friend=friend,
        borrower=borrower,
        item=item,
        outcome=prediction["outcome"],
        solved=item.meters["returned"] >= THRESHOLD,
    )
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom",
        intro="Paper moons hung in the windows, and a big round rug waited for the children",
        hide_spot="the reading nook",
        afford_need={"welcome_sign", "treat_bags", "lost_button"},
    ),
    "library_corner": Place(
        id="library_corner",
        label="the library corner",
        intro="Low shelves curved around a soft carpet, and picture books made little walls of color",
        hide_spot="the beanbag corner",
        afford_need={"welcome_sign", "lost_button"},
    ),
    "garden_table": Place(
        id="garden_table",
        label="the garden table",
        intro="The wooden table stood under bright leaves, with seed cups and paper stacked in neat piles",
        hide_spot="the potting bench",
        afford_need={"welcome_sign", "treat_bags"},
    ),
}

ITEMS = {
    "marker": Item(
        id="marker",
        label="red marker",
        phrase="the shared red marker",
        shared_use="drawing thick red letters",
        texture="bright as a cherry stripe",
        tags={"marker", "sharing", "art"},
    ),
    "magnifier": Item(
        id="magnifier",
        label="magnifying glass",
        phrase="the shared magnifying glass",
        shared_use="looking closely at tiny things",
        texture="smooth in its wooden handle",
        tags={"magnifying_glass", "mystery", "sharing"},
    ),
    "ribbon": Item(
        id="ribbon",
        label="blue ribbon spool",
        phrase="the shared blue ribbon spool",
        shared_use="tying soft bows",
        texture="cool and shiny as a stream",
        tags={"ribbon", "sharing", "craft"},
    ),
}

NEEDS = {
    "welcome_sign": Need(
        id="welcome_sign",
        item="marker",
        places={"classroom", "library_corner", "garden_table"},
        borrower_goal="making a welcome sign for everyone",
        reveal_text='"I took it to make a welcome sign for the new child," the borrower explained. "I wanted the letters to be big and easy to see."',
        sharing_text='"Let us finish the sign together," the borrower said, sliding the marker into the middle. "Then the whole class can welcome our new friend."',
        tags={"welcome", "sharing"},
    ),
    "lost_button": Need(
        id="lost_button",
        item="magnifier",
        places={"classroom", "library_corner"},
        borrower_goal="searching for a tiny lost button for a younger child",
        reveal_text='"I borrowed it to help Eli find the tiny button that fell off his puppet coat," the borrower explained. "I did not want him to cry."',
        sharing_text='"Now that the button is found, we can all use the magnifying glass for the mystery table," the borrower said. "Helping first can still end in sharing."',
        tags={"helping", "sharing", "mystery"},
    ),
    "treat_bags": Need(
        id="treat_bags",
        item="ribbon",
        places={"classroom", "garden_table"},
        borrower_goal="tying treat bags to share with everyone",
        reveal_text='"I borrowed it to tie the little treat bags so none of the orange slices would spill," the borrower explained. "I wanted everyone to get one."',
        sharing_text='"Come tie bows with me," the borrower said, setting the ribbon spool where every hand could reach. "The bags will be for all of us."',
        tags={"sharing", "gift"},
    ),
}

CLUES = {
    "red_swoosh": Clue(
        id="red_swoosh",
        item="marker",
        notice_text="Near the chair legs, a fresh red swoosh curved across a scrap of paper.",
        hint_spot="a stack of drawing paper by the window",
        clue_object="the paper scraps",
        strength=2,
        tags={"marker", "clue"},
    ),
    "glass_circle": Clue(
        id="glass_circle",
        item="magnifier",
        notice_text="On the rug lay a bright round patch of light, as if a glass lens had just kissed the sun.",
        hint_spot="the low puppet basket",
        clue_object="the puppet basket",
        strength=2,
        tags={"magnifying_glass", "clue"},
    ),
    "blue_curl": Clue(
        id="blue_curl",
        item="ribbon",
        notice_text="By one table leg rested a curled strip of blue ribbon, no longer than a finger.",
        hint_spot="the basket of paper bags",
        clue_object="the paper bag basket",
        strength=2,
        tags={"ribbon", "clue"},
    ),
}

APPROACHES = {
    "ask_kindly": Approach(
        id="ask_kindly",
        courtesy=3,
        patience=1,
        ask_line="We will use calm voices and ask what happened.",
        follow_line="Let us ask first before the clue grows bigger than the truth.",
        qa_text="They solved it by speaking kindly right away, which made the borrower feel safe enough to answer honestly.",
        tags={"dialogue", "kindness"},
    ),
    "follow_then_ask": Approach(
        id="follow_then_ask",
        courtesy=2,
        patience=2,
        ask_line="We can follow the clue carefully, then ask a gentle question when we know more.",
        follow_line="Let us see where this clue leads, and then we can talk kindly.",
        qa_text="They solved it by following the clue first and then asking a gentle question, so the mystery stayed fair instead of mean.",
        tags={"dialogue", "mystery"},
    ),
    "corner_everyone": Approach(
        id="corner_everyone",
        courtesy=1,
        patience=1,
        ask_line="We should demand to know who took it right now.",
        follow_line="Point at everyone until someone admits it.",
        qa_text="This approach is too harsh for the world.",
        tags={"harsh"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Noah", "Eli", "Jack", "Theo"]


@dataclass
class StoryParams:
    place: str
    item: str
    need: str
    clue: str
    approach: str
    sleuth_name: str
    sleuth_gender: str
    friend_name: str
    friend_gender: str
    borrower_name: str
    borrower_gender: str
    teacher_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "marker": [
        (
            "What is a marker?",
            "A marker is a pen with thick colored ink for drawing or writing bold lines. Shared markers work best when children take turns and put the cap back on.",
        )
    ],
    "magnifying_glass": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes tiny things look bigger, so it helps you see small details. People often use one when they are searching carefully.",
        )
    ],
    "ribbon": [
        (
            "What is ribbon used for?",
            "Ribbon is a long soft strip used for tying, wrapping, or making bows. It can help turn plain bags or boxes into something special to share.",
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful in a classroom?",
            "Sharing lets more people use the same good thing, so everyone gets a turn. It also helps a group feel fair and friendly.",
        )
    ],
    "dialogue": [
        (
            "Why is calm dialogue good for solving problems?",
            "Calm dialogue means talking and listening with kind words. It helps people tell the truth without feeling scared.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle with something hidden or not yet explained. You solve it by noticing clues and asking careful questions.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Good clues point toward the truth instead of making a wild guess.",
        )
    ],
    "helping": [
        (
            "Why might someone borrow something to help another child?",
            "Sometimes a child borrows a tool because another child needs help right away. The kind thing is to tell others and then share it back.",
        )
    ],
    "welcome": [
        (
            "What is a welcome sign for?",
            "A welcome sign shows a new person that they are wanted and included. Making one together can help everyone feel ready to share.",
        )
    ],
    "gift": [
        (
            "Why do children tie treat bags or little gifts?",
            "They tie them so the food or gift stays neat and can be given fairly. It is one way of getting something ready to share with others.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "mystery",
    "clue",
    "dialogue",
    "sharing",
    "marker",
    "magnifying_glass",
    "ribbon",
    "helping",
    "welcome",
    "gift",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sleuth = f["sleuth"]
    friend = f["friend"]
    item_cfg = f["item_cfg"]
    need = f["need"]
    place = f["place"]
    outcome = f["outcome"]
    tail = (
        "The borrower should confess quickly after hearing kind voices."
        if outcome == "quick_confession"
        else "The children should follow the clue first, then solve the mystery with gentle dialogue."
    )
    return [
        (
            f'Write a short child-facing whodunit set in {place.label} where a shared '
            f'{item_cfg.label} goes missing, a child has a hunch, and another child is resistant '
            f'to blaming anyone too fast.'
        ),
        (
            f"Tell a mystery-to-solve story with dialogue where {sleuth.id} and {friend.id} "
            f"discover a clue, learn that the missing item was borrowed for {need.borrower_goal}, "
            f"and end with sharing."
        ),
        (
            f'Write a gentle mystery story that includes the words "resistant" and "hunch". '
            f'{tail}'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    friend = f["friend"]
    borrower = f["borrower"]
    teacher = f["teacher"]
    item_cfg = f["item_cfg"]
    need = f["need"]
    clue_cfg = f["clue_cfg"]
    approach = f["approach"]
    place = f["place"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that the shared {item_cfg.label} disappeared from the table during sharing time in {place.label}. That missing object gave the children a real puzzle to solve.",
        ),
        (
            f"What clue did {sleuth.id} and {friend.id} notice?",
            f"They noticed {clue_cfg.notice_text[0].lower() + clue_cfg.notice_text[1:]} The clue mattered because it honestly matched the missing {item_cfg.label}.",
        ),
        (
            f"Why did {friend.id} say {friend.pronoun()} was resistant to blaming anyone?",
            f"{friend.id} did not want the clue to turn into a mean guess. {friend.pronoun().capitalize()} wanted the children to ask kindly and learn the truth before pointing at someone.",
        ),
        (
            f"What was {sleuth.id}'s hunch?",
            f"{sleuth.id}'s hunch was that the clue showed where the missing {item_cfg.label} had gone. The hunch was not wild, because it came from something the children truly noticed.",
        ),
    ]
    if outcome == "quick_confession":
        qa.append(
            (
                "How was the mystery solved?",
                f"It was solved when the borrower heard the calm plan and stepped forward to explain. {approach.qa_text}",
            )
        )
    else:
        qa.append(
            (
                "How was the mystery solved?",
                f"It was solved after the children followed the clue to {clue_cfg.hint_spot} and then asked a gentle question. {approach.qa_text}",
            )
        )
    qa.append(
        (
            f"Why had {borrower.id} borrowed the {item_cfg.label}?",
            f"{borrower.id} had borrowed it for {need.borrower_goal}. The borrowing was meant to help or include others, even though {borrower.pronoun()} should have told the group first.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children putting the mystery behind them and using the {item_cfg.label} together. The final image proves what changed: worry turned into sharing.",
        )
    )
    qa.append(
        (
            f"How did {teacher.id} help solve the problem?",
            f"{teacher.id} guided the children toward calm dialogue instead of sharp blame. That made it easier for the truth to come out and for everyone to feel safe again.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "clue", "dialogue", "sharing"}
    tags |= set(f["item_cfg"].tags)
    tags |= set(f["need"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:14} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        item="marker",
        need="welcome_sign",
        clue="red_swoosh",
        approach="ask_kindly",
        sleuth_name="Nora",
        sleuth_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        borrower_name="Mia",
        borrower_gender="girl",
        teacher_type="teacher_f",
    ),
    StoryParams(
        place="library_corner",
        item="magnifier",
        need="lost_button",
        clue="glass_circle",
        approach="follow_then_ask",
        sleuth_name="Leo",
        sleuth_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        borrower_name="Eli",
        borrower_gender="boy",
        teacher_type="teacher_m",
    ),
    StoryParams(
        place="garden_table",
        item="ribbon",
        need="treat_bags",
        clue="blue_curl",
        approach="ask_kindly",
        sleuth_name="Ruby",
        sleuth_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        borrower_name="Anna",
        borrower_gender="girl",
        teacher_type="teacher_f",
    ),
    StoryParams(
        place="classroom",
        item="ribbon",
        need="treat_bags",
        clue="blue_curl",
        approach="follow_then_ask",
        sleuth_name="Theo",
        sleuth_gender="boy",
        friend_name="Lily",
        friend_gender="girl",
        borrower_name="Zoe",
        borrower_gender="girl",
        teacher_type="teacher_f",
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for item_id in ITEMS:
            for need_id in NEEDS:
                for clue_id in CLUES:
                    if valid_combo(place_id, item_id, need_id, clue_id):
                        combos.append((place_id, item_id, need_id, clue_id))
    return combos


ASP_RULES = r"""
valid(P, I, N, C) :-
    place(P), item(I), need(N), clue(C),
    need_item(N, I),
    clue_item(C, I),
    need_place(N, P),
    place_affords(P, N).

sensible(A) :-
    approach(A),
    courtesy(A, V),
    courtesy_min(M),
    V >= M.

quick_confession :-
    chosen_approach(A),
    courtesy(A, V),
    V >= 3.

trail_then_talk :-
    chosen_approach(A),
    sensible(A),
    courtesy(A, 2).

outcome(quick_confession) :- quick_confession.
outcome(trail_then_talk) :- not quick_confession, trail_then_talk.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for need_id in sorted(place.afford_need):
            lines.append(asp.fact("place_affords", place_id, need_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        lines.append(asp.fact("need_item", need_id, need.item))
        for place_id in sorted(need.places):
            lines.append(asp.fact("need_place", need_id, place_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_item", clue_id, clue.item))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("courtesy", approach_id, approach.courtesy))
    lines.append(asp.fact("courtesy_min", COURTESY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_approach", params.approach)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {a.id for a in sensible_approaches()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible approaches match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible approaches: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            rc = 1
            print(f"MISMATCH in outcome for {case}: asp={asp_outcome(case)} python={outcome_of(case)}")
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle whodunit with dialogue, a hunch, and sharing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--teacher-type", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.approach and APPROACHES[args.approach].courtesy < COURTESY_MIN:
        raise StoryError(explain_approach_rejection(args.approach))

    explicit = [args.place, args.item, args.need, args.clue]
    if all(value is not None for value in explicit):
        if not valid_combo(args.place, args.item, args.need, args.clue):
            raise StoryError(explain_combo_rejection(args.place, args.item, args.need, args.clue))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.need is None or combo[2] == args.need)
        and (args.clue is None or combo[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, need_id, clue_id = rng.choice(sorted(combos))
    approach_id = args.approach or rng.choice(sorted(a.id for a in sensible_approaches()))
    sleuth_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    borrower_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    sleuth_name = _pick_name(rng, sleuth_gender, used)
    used.add(sleuth_name)
    friend_name = _pick_name(rng, friend_gender, used)
    used.add(friend_name)
    borrower_name = _pick_name(rng, borrower_gender, used)
    teacher_type = args.teacher_type or rng.choice(["teacher_f", "teacher_m"])

    return StoryParams(
        place=place_id,
        item=item_id,
        need=need_id,
        clue=clue_id,
        approach=approach_id,
        sleuth_name=sleuth_name,
        sleuth_gender=sleuth_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        borrower_name=borrower_name,
        borrower_gender=borrower_gender,
        teacher_type=teacher_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")
    if APPROACHES[params.approach].courtesy < COURTESY_MIN:
        raise StoryError(explain_approach_rejection(params.approach))
    if not valid_combo(params.place, params.item, params.need, params.clue):
        raise StoryError(explain_combo_rejection(params.place, params.item, params.need, params.clue))

    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        need=NEEDS[params.need],
        clue_cfg=CLUES[params.clue],
        approach=APPROACHES[params.approach],
        sleuth_name=params.sleuth_name,
        sleuth_gender=params.sleuth_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        borrower_name=params.borrower_name,
        borrower_gender=params.borrower_gender,
        teacher_type=params.teacher_type,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible approaches: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, item, need, clue) combos:\n")
        for place_id, item_id, need_id, clue_id in combos:
            print(f"  {place_id:14} {item_id:10} {need_id:13} {clue_id}")
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
            header = (
                f"### {p.sleuth_name}, {p.friend_name}, and {p.borrower_name}: "
                f"{p.item} / {p.need} / {p.approach}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
