#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cognitive_lass_dim_math_rhyme_conflict_dialogue.py
=============================================================================

A standalone story world for a tiny child-facing mystery about a missing
classroom object, a nonsense code word, and a pair of children who must solve a
rhyming math clue instead of guessing. The seed words "cognitive", "lass-dim",
and "math" are rebuilt as part of the world's state: a teacher's note for a
"cognitive math mystery" uses the odd code word "lass-dim" as a playful secret.

The world model focuses on one strong problem/fix pattern:

    a special object is missing
    -> a rhyme clue points to a number
    -> one child wants to rush / accuse / grab
    -> the other child insists on counting carefully
    -> they solve the clue, find the object, and repair the social tension

The reasonableness gate refuses combinations where the clue number does not fit
the chosen hiding place, or where the requested solving method is too weak to be
a sensible mystery-solving move.

Run it
------
    python storyworlds/worlds/gpt-5.4/cognitive_lass_dim_math_rhyme_conflict_dialogue.py
    python storyworlds/worlds/gpt-5.4/cognitive_lass_dim_math_rhyme_conflict_dialogue.py --place classroom --item bell
    python storyworlds/worlds/gpt-5.4/cognitive_lass_dim_math_rhyme_conflict_dialogue.py --method guess
    python storyworlds/worlds/gpt-5.4/cognitive_lass_dim_math_rhyme_conflict_dialogue.py --all
    python storyworlds/worlds/gpt-5.4/cognitive_lass_dim_math_rhyme_conflict_dialogue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cognitive_lass_dim_math_rhyme_conflict_dialogue.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives one level deeper than most worlds:
# storyworlds/worlds/gpt-5.4/<file>.py  -> add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"        # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    # Two numeric dimensions, treated uniformly.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"teacher_f", "teacher_m"}:
            return "teacher"
        return self.type


@dataclass
class Place:
    id: str
    scene: str
    room_word: str
    adult_label: str
    adult_type: str
    surface: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    shine: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingSpot:
    id: str
    label: str
    phrase: str
    count_noun: str
    count_total: int
    clue_number: int
    found_line: str
    tags: set[str] = field(default_factory=set)

    def ordinal(self) -> str:
        return ordinal_word(self.clue_number)


@dataclass
class Method:
    id: str
    sense: int
    success: str
    failure: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictMode:
    id: str
    impulse: str
    warning: str
    repair: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_conflict(world: World) -> list[str]:
    seeker = world.get("seeker")
    partner = world.get("partner")
    if seeker.memes["rush"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["friction"] += 1
    partner.memes["friction"] += 1
    return ["__conflict__"]


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for role in ("seeker", "partner", "adult"):
        world.get(role).memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("found_relief", "social", _r_found_relief),
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
        for s in produced:
            world.say(s)
    return produced


def ordinal_word(n: int) -> str:
    return {
        1: "first",
        2: "second",
        3: "third",
        4: "fourth",
        5: "fifth",
        6: "sixth",
    }[n]


def rhyme_for_spot(spot: HidingSpot) -> str:
    noun = spot.count_noun
    num = spot.clue_number
    ordw = spot.ordinal()
    return (
        f'"One, two, three, do the math with me. '
        f'Past each {noun}, quiet and slim, seek the {ordw} one for lass-dim."'
    )


def place_supports(place: Place, spot: HidingSpot) -> bool:
    return spot.count_total >= spot.clue_number


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combo(place_id: str, item_id: str, spot_id: str) -> bool:
    return place_supports(PLACES[place_id], SPOTS[spot_id])


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for item_id in ITEMS:
            for spot_id in SPOTS:
                if valid_combo(place_id, item_id, spot_id):
                    combos.append((place_id, item_id, spot_id))
    return combos


def explain_rejection(place: Place, spot: HidingSpot) -> str:
    return (
        f"(No story: {place.scene} does not give enough {spot.count_noun} for the "
        f"clue number {spot.clue_number}. A fair mystery needs a hiding place the "
        f"children can really count to.)"
    )


def explain_method(method_id: str) -> str:
    m = METHODS[method_id]
    better = " / ".join(sorted(x.id for x in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={m.sense} < {SENSE_MIN}). A mystery should be solved with a fair, "
        f"checkable method. Try: {better}.)"
    )


def solve_possible(method: Method, place: Place, spot: HidingSpot) -> bool:
    return method.sense >= SENSE_MIN and place_supports(place, spot)


def predict_success(world: World, method: Method) -> dict:
    sim = world.copy()
    place = sim.facts["place"]
    spot = sim.facts["spot"]
    success = solve_possible(method, place, spot)
    if success:
        sim.get("item").meters["found"] += 1
        propagate(sim, narrate=False)
    return {"success": success, "relief": sim.get("seeker").memes["relief"]}


def introduce(world: World, seeker: Entity, partner: Entity, adult: Entity,
              place: Place, item: MissingItem) -> None:
    seeker.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"In {place.scene}, {adult.id} set down {item.phrase} on {place.surface} "
        f"and smiled at {seeker.id} and {partner.id}."
    )
    world.say(
        f'"Today\'s cognitive math mystery begins now," {adult.id} said. '
        f'"Listen closely. The finder of {item.label} may ring it when the puzzle is done."'
    )


def vanish(world: World, adult: Entity, item: MissingItem) -> None:
    world.get("item").meters["missing"] += 1
    world.say(
        f"But when the class looked again, {item.phrase} was gone. Only a folded note "
        f"remained where it had been."
    )
    world.say(
        f'{adult.id} opened the note and read, "If you want the {item.label}, '
        f'solve the rhyme, not just the time."'
    )


def present_rhyme(world: World, adult: Entity, spot: HidingSpot) -> None:
    world.say(f'"Here is the clue," {adult.id} said, and {adult.pronoun()} read: {rhyme_for_spot(spot)}')
    world.say(
        'The odd little code word made everyone blink. "Lass-dim?" '
        f'{world.get("partner").id} whispered. "That sounds like a secret name."'
    )


def conflict(world: World, seeker: Entity, partner: Entity, mode: ConflictMode,
             item: MissingItem) -> None:
    seeker.memes["rush"] += 1
    propagate(world, narrate=False)
    world.say(f'"{mode.impulse}" {seeker.id} said.')
    world.say(
        f'{partner.id} shook {partner.pronoun("possessive")} head. "{mode.warning}"'
    )
    if mode.id == "accuse":
        world.say(
            f'"Nobody took {item.label} to be mean," {partner.id} added. '
            '"A fair clue means we should think first."'
        )


def inspect(world: World, seeker: Entity, partner: Entity, adult: Entity,
            method: Method, place: Place, spot: HidingSpot) -> None:
    pred = predict_success(world, method)
    world.facts["predicted_success"] = pred["success"]
    world.say(
        f'{adult.id} crouched beside them. "Mysteries like this need calm eyes and math," '
        f'{adult.pronoun()} said.'
    )
    if method.id == "count":
        world.say(
            f'{partner.id} tapped the note. "The rhyme tells us to count the {spot.count_noun}," '
            f'{partner.pronoun()} said. "{method.success}"'
        )
    else:
        world.say(f'"{method.success}" {partner.id} said.')
    seeker.memes["thinking"] += 1
    partner.memes["thinking"] += 1


def solve(world: World, seeker: Entity, partner: Entity, adult: Entity,
          item: MissingItem, spot: HidingSpot, method: Method, conflict_mode: ConflictMode) -> None:
    item_ent = world.get("item")
    if solve_possible(method, world.facts["place"], spot):
        item_ent.meters["found"] += 1
        item_ent.meters["missing"] = 0.0
        seeker.memes["wonder"] += 1
        partner.memes["wonder"] += 1
        propagate(world, narrate=False)
        world.say(
            f"So they counted together: one {spot.count_noun}, two {spot.count_noun}, "
            f"three {spot.count_noun}..."
        )
        if spot.clue_number > 3:
            world.say(
                f"When they reached the {spot.ordinal()} {spot.count_noun}, "
                f"{partner.id} pointed and gasped."
            )
        else:
            world.say(
                f"At the {spot.ordinal()} {spot.count_noun}, {seeker.id} stopped short."
            )
        world.say(spot.found_line.format(item=item.label))
        world.say(
            f'"There it is!" {seeker.id} cried. {adult.id} laughed softly as '
            f'{item.phrase} gave a small, happy sound.'
        )
        world.say(
            f'{partner.id} smiled at {seeker.id}. "{conflict_mode.repair}"'
        )
    else:
        item_ent.meters["still_lost"] += 1
        world.say(method.failure)
        world.say(
            f'{adult.id} folded the note again. "A good mystery has an answer we can prove," '
            f'{adult.pronoun()} said.'
        )


def ending(world: World, seeker: Entity, partner: Entity, adult: Entity,
           item: MissingItem, place: Place) -> None:
    if world.get("item").meters["found"] >= THRESHOLD:
        seeker.memes["friendship"] += 1
        partner.memes["friendship"] += 1
        seeker.memes["friction"] = 0.0
        partner.memes["friction"] = 0.0
        world.say(
            f'{adult.id} handed {item.phrase} to both children together. '
            f'"The mystery is solved," {adult.pronoun()} said. '
            f'"You used dialogue, patience, and math."'
        )
        world.say(
            f'The room no longer felt hush-hush and strange. It felt bright again, '
            f'with {item.shine} proving that careful thinking had won.'
        )


def tell(place: Place, item: MissingItem, spot: HidingSpot, method: Method,
         conflict_mode: ConflictMode, seeker_name: str = "Mira",
         seeker_type: str = "girl", partner_name: str = "Owen",
         partner_type: str = "boy") -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_type,
                              role="seeker", traits=["curious"]))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type,
                               role="partner", traits=["patient"]))
    adult = world.add(Entity(id=place.adult_label, kind="character",
                             type=place.adult_type, role="adult", label="the teacher"))
    item_ent = world.add(Entity(id="item", type="item", label=item.label, movable=True))
    world.facts.update(place=place, item_cfg=item, spot=spot, method=method,
                       conflict_mode=conflict_mode)

    introduce(world, seeker, partner, adult, place, item)
    vanish(world, adult, item)

    world.para()
    present_rhyme(world, adult, spot)
    conflict(world, seeker, partner, conflict_mode, item)

    world.para()
    inspect(world, seeker, partner, adult, method, place, spot)
    solve(world, seeker, partner, adult, item, spot, method, conflict_mode)

    world.para()
    ending(world, seeker, partner, adult, item, place)

    world.facts.update(
        seeker=seeker,
        partner=partner,
        adult=adult,
        item=item_ent,
        solved=item_ent.meters["found"] >= THRESHOLD,
        place=place,
        item_cfg=item,
        spot=spot,
        method=method,
        conflict_mode=conflict_mode,
    )
    return world


PLACES = {
    "classroom": Place(
        "classroom",
        "the little classroom at the end of the hall",
        "classroom",
        "Ms. June",
        "teacher_f",
        "the counting table",
        tags={"school"},
    ),
    "library": Place(
        "library",
        "the library corner beside the tall windows",
        "library",
        "Mr. Reed",
        "teacher_m",
        "the puzzle shelf",
        tags={"library"},
    ),
    "art_room": Place(
        "art_room",
        "the art room with paper stars hanging overhead",
        "art room",
        "Ms. June",
        "teacher_f",
        "the clean blue stool",
        tags={"school", "art"},
    ),
}

ITEMS = {
    "bell": MissingItem(
        "bell",
        "silver bell",
        "the silver bell",
        "a silver gleam under the light",
        "ring it to end the puzzle",
        tags={"bell"},
    ),
    "stamp": MissingItem(
        "stamp",
        "gold star stamp",
        "the gold star stamp",
        "a bright gold flash on the teacher's palm",
        "stamp the solved page",
        tags={"stamp"},
    ),
    "key": MissingItem(
        "key",
        "brass key",
        "the brass key",
        "a warm brass wink between small fingers",
        "open the prize box",
        tags={"key"},
    ),
}

SPOTS = {
    "cubbies": HidingSpot(
        "cubbies",
        "cubbies",
        "the row of cubbies",
        "cubby",
        count_total=6,
        clue_number=4,
        found_line="Behind the fourth cubby sat the {item}, tucked beside a folded paper moon.",
        tags={"counting", "cubbies"},
    ),
    "books": HidingSpot(
        "books",
        "books",
        "the stack of storybooks",
        "book",
        count_total=5,
        clue_number=3,
        found_line="Inside the third book, safe between two pages, rested the {item}.",
        tags={"counting", "books"},
    ),
    "jars": HidingSpot(
        "jars",
        "paint jars",
        "the line of paint jars",
        "jar",
        count_total=4,
        clue_number=2,
        found_line="Under the second jar lay the {item}, hidden on a tiny square of felt.",
        tags={"counting", "jars"},
    ),
}

METHODS = {
    "count": Method(
        "count",
        3,
        "If the rhyme says a number, we should count and check.",
        "They guessed and peered around, but nothing felt certain and the mystery stayed fuzzy.",
        "counted the places named in the rhyme until they reached the right one",
        tags={"math", "count"},
    ),
    "line_up": Method(
        "line_up",
        2,
        "Let's line the places up in order and follow the clue one by one.",
        "They tried to look everywhere at once, and the clue slipped away from them.",
        "lined the places up in order and followed the clue carefully",
        tags={"math", "order"},
    ),
    "guess": Method(
        "guess",
        1,
        "Maybe we can just pick the first place and hope.",
        "They grabbed at a random place, but a mystery note cannot be solved by hoping.",
        "guessed",
        tags={"guess"},
    ),
}

CONFLICTS = {
    "grab": ConflictMode(
        "grab",
        "Maybe I should just open every cubby really fast!",
        "If we snatch at everything, we will miss the clue.",
        "You were right to hurry for the bell, but counting helped us find it kindly.",
        tags={"conflict"},
    ),
    "accuse": ConflictMode(
        "accuse",
        "I think somebody hid it just to trick us!",
        "We should not blame anyone before we know.",
        "I am glad we solved the puzzle instead of blaming someone.",
        tags={"conflict"},
    ),
    "boast": ConflictMode(
        "boast",
        "I do not need the rhyme. I can solve this all by myself!",
        "Even detectives listen before they leap.",
        "It was better when we solved it together.",
        tags={"conflict"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Nora", "Tess", "Ruby", "Clara", "Ivy", "Poppy"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Milo", "Jude", "Evan", "Theo", "Ben"]


@dataclass
class StoryParams:
    place: str
    item: str
    spot: str
    method: str
    conflict: str
    seeker: str
    seeker_gender: str
    partner: str
    partner_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "math": [
        (
            "What does math help you do in a mystery?",
            "Math helps you count, compare, and check things in order. That makes a mystery fair because you can prove why an answer is right."
        )
    ],
    "count": [
        (
            "Why is counting useful?",
            "Counting helps you keep track of how many things there are and which one comes next. It stops you from mixing the first thing up with the fourth thing."
        )
    ],
    "order": [
        (
            "What does putting things in order mean?",
            "Putting things in order means arranging them first, second, third, and so on. It helps your brain follow a clue step by step."
        )
    ],
    "bell": [
        (
            "What is a bell?",
            "A bell is an object that makes a clear ringing sound when you shake or tap it. People use bells to signal that it is time to listen or come together."
        )
    ],
    "stamp": [
        (
            "What does a stamp do?",
            "A stamp presses a little picture or mark onto paper. Teachers sometimes use a star stamp to show that a page is finished or well done."
        )
    ],
    "key": [
        (
            "What is a key for?",
            "A key is used to open something that is locked, like a box or a door. A key has to match the lock to work."
        )
    ],
    "books": [
        (
            "Why do libraries have many books in rows?",
            "Books are kept in rows so people can find them again. Order makes it easier to search without losing track."
        )
    ],
    "cubbies": [
        (
            "What is a cubby?",
            "A cubby is a small open space used to hold school things like bags, papers, or shoes. Children can count cubbies one by one."
        )
    ],
    "jars": [
        (
            "Why should paint jars stay closed and lined up?",
            "Closed paint jars are less likely to spill, and lining them up helps people find the color they want. Neat rows also make counting easier."
        )
    ],
    "conflict": [
        (
            "What is conflict in a story?",
            "Conflict is the part where characters want different things or disagree about what to do. It gives the story a problem that needs to be worked out."
        )
    ],
    "dialogue": [
        (
            "What is dialogue?",
            "Dialogue is when characters speak to each other in a story. Their words can show clues, feelings, and how they solve a problem together."
        )
    ],
}
KNOWLEDGE_ORDER = ["math", "count", "order", "bell", "stamp", "key", "books", "cubbies", "jars", "conflict", "dialogue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    partner = f["partner"]
    item = f["item_cfg"]
    spot = f["spot"]
    conflict = f["conflict_mode"]
    place = f["place"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "cognitive", "lass-dim", and "math". Use rhyme, conflict, and dialogue.',
        f"Tell a gentle mystery where {seeker.id} and {partner.id} must use a rhyming number clue to find {item.phrase} in {place.room_word}, even though they disagree at first.",
        f'Write a child-facing mystery in which a strange clue says "lass-dim," one child wants to {conflict.id}, and the solution comes from counting to the {spot.ordinal()} {spot.count_noun}.',
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    partner = f["partner"]
    adult = f["adult"]
    item = f["item_cfg"]
    spot = f["spot"]
    method = f["method"]
    conflict = f["conflict_mode"]
    pair = pair_noun(seeker, partner)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {seeker.id} and {partner.id}, and {adult.id}, who gives them the mystery note. They work together to find {item.phrase}."
        ),
        (
            f"What was missing?",
            f"The missing object was {item.phrase}. The whole mystery begins when the children see that it is gone and only the note is left behind."
        ),
        (
            "What did the rhyme clue tell them to do?",
            f"The rhyme told them to use math and look for the {spot.ordinal()} {spot.count_noun}. The silly word 'lass-dim' was part of the secret code in the note."
        ),
        (
            f"What was the conflict?",
            f"The conflict was that {seeker.id} wanted to {conflict.id if conflict.id != 'boast' else 'rush ahead alone'}, while {partner.id} wanted to follow the clue carefully. Their disagreement matters because a fair mystery can only be solved by checking the clue."
        ),
    ]
    if f["solved"]:
        qa.extend([
            (
                f"How did they find the {item.label}?",
                f"They used {method.qa_text}. Because they counted in order instead of guessing, they reached the correct place and found {item.phrase}."
            ),
            (
                "Where was the missing thing hidden?",
                f"It was hidden at {spot.phrase}. The clue number matched that spot, so the children could prove they had the right answer."
            ),
            (
                f"How did the story end?",
                f"It ended happily with the mystery solved and the children feeling calm again. The shining {item.label} showed that careful dialogue and math had changed the room from puzzling to bright."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"dialogue", "conflict"}
    tags |= set(f["method"].tags)
    tags |= set(f["item_cfg"].tags)
    tags |= set(f["spot"].tags)
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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("classroom", "bell", "cubbies", "count", "grab", "Mira", "girl", "Owen", "boy"),
    StoryParams("library", "stamp", "books", "line_up", "accuse", "Ruby", "girl", "Finn", "boy"),
    StoryParams("art_room", "key", "jars", "count", "boast", "Nora", "girl", "Theo", "boy"),
]


def outcome_of(params: StoryParams) -> str:
    return "solved" if solve_possible(METHODS[params.method], PLACES[params.place], SPOTS[params.spot]) else "stuck"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P, I, S) :- place(P), item(I), spot(S), total(S, T), clue(S, C), T >= C.
sensible(M)    :- method(M), sense(M, V), sense_min(N), V >= N.

% --- outcome model ---------------------------------------------------------
can_solve      :- chosen_place(P), chosen_spot(S), chosen_method(M),
                  total(S, T), clue(S, C), T >= C,
                  sense(M, V), sense_min(N), V >= N.
outcome(solved) :- can_solve.
outcome(stuck)  :- not can_solve.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for sid, s in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("total", sid, s.count_total))
        lines.append(asp.fact("clue", sid, s.clue_number))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, m.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {m.id for m in sensible_methods()}
    if c_sens == p_sens:
        print(f"OK: sensible methods match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle mystery solved by rhyme, dialogue, and math."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--conflict", choices=CONFLICTS)
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.spot:
        if not place_supports(PLACES[args.place], SPOTS[args.spot]):
            raise StoryError(explain_rejection(PLACES[args.place], SPOTS[args.spot]))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.spot is None or c[2] == args.spot)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, spot = rng.choice(sorted(combos))
    method = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    conflict = args.conflict or rng.choice(sorted(CONFLICTS))
    seeker, sg = _pick_kid(rng)
    partner, pg = _pick_kid(rng, avoid=seeker)
    return StoryParams(place, item, spot, method, conflict, seeker, sg, partner, pg)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ITEMS[params.item],
        SPOTS[params.spot],
        METHODS[params.method],
        CONFLICTS[params.conflict],
        params.seeker,
        params.seeker_gender,
        params.partner,
        params.partner_gender,
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
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, item, spot) combos:\n")
        for place, item, spot in combos:
            print(f"  {place:10} {item:8} {spot}")
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
            header = f"### {p.seeker} & {p.partner}: {p.item} in {p.place} ({p.spot}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
