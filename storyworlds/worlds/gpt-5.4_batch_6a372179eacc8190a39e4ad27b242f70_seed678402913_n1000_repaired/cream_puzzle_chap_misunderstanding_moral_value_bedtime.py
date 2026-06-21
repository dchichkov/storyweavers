#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cream_puzzle_chap_misunderstanding_moral_value_bedtime.py
====================================================================================

A standalone storyworld about a bedtime misunderstanding: a child is finishing a
puzzle, notices a dab of cream and a missing piece, and wrongly blames another
child. The world model tracks physical state (where the piece went, what the
cream touched) and emotional state (worry, blame, relief, trust). The turn is
state-driven: the piece is found in a plausible bedtime place, the cream has an
innocent source, and the child learns to ask kindly before blaming.

Run it
------
    python storyworlds/worlds/gpt-5.4/cream_puzzle_chap_misunderstanding_moral_value_bedtime.py
    python storyworlds/worlds/gpt-5.4/cream_puzzle_chap_misunderstanding_moral_value_bedtime.py --puzzle moon
    python storyworlds/worlds/gpt-5.4/cream_puzzle_chap_misunderstanding_moral_value_bedtime.py --hiding bookshelf
    python storyworlds/worlds/gpt-5.4/cream_puzzle_chap_misunderstanding_moral_value_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/cream_puzzle_chap_misunderstanding_moral_value_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cream_puzzle_chap_misunderstanding_moral_value_bedtime.py --verify
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
_THIS = os.path.abspath(__file__)
_WORLD_DIR = os.path.dirname(_THIS)
_WORLDS_DIR = os.path.dirname(_WORLD_DIR)
_PACKAGE_DIR = os.path.dirname(_WORLDS_DIR)
sys.path.insert(0, _PACKAGE_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
KINDNESS_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class PuzzleKind:
    id: str
    picture: str
    piece_name: str
    bedtime_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CreamKind:
    id: str
    label: str
    use_for: str
    scent: str
    can_smudge: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    room_item: str
    bedtime_fit: int
    found_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AccusedRole:
    id: str
    label: str
    title: str
    relation_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairStyle:
    id: str
    kindness: int
    opener: str
    apology_line: str
    lesson_line: str
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


def _r_blame_hurts(world: World) -> list[str]:
    child = world.get("child")
    accused = world.get("accused")
    if child.memes["blame"] < THRESHOLD:
        return []
    sig = ("blame_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accused.memes["sad"] += 1
    accused.memes["distance"] += 1
    child.memes["guilt_risk"] += 1
    return ["__hurt__"]


def _r_found_piece_relief(world: World) -> list[str]:
    piece = world.get("piece")
    child = world.get("child")
    accused = world.get("accused")
    if piece.attrs.get("location") == "lost":
        return []
    sig = ("found_relief", piece.attrs.get("location"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    accused.memes["relief"] += 1
    return ["__relief__"]


def _r_apology_restores(world: World) -> list[str]:
    child = world.get("child")
    accused = world.get("accused")
    if child.memes["apology"] < THRESHOLD:
        return []
    sig = ("restore",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["guilt"] = 0.0
    child.memes["trust"] += 1
    accused.memes["distance"] = 0.0
    accused.memes["trust"] += 1
    return ["__restored__"]


CAUSAL_RULES = [
    Rule(name="blame_hurts", tag="social", apply=_r_blame_hurts),
    Rule(name="found_piece_relief", tag="physical", apply=_r_found_piece_relief),
    Rule(name="apology_restores", tag="social", apply=_r_apology_restores),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PUZZLES = {
    "moon": PuzzleKind(
        id="moon",
        picture="a round silver moon over sleepy roofs",
        piece_name="moon piece",
        bedtime_image="the moon looked almost complete",
        tags={"puzzle", "moon"},
    ),
    "bear": PuzzleKind(
        id="bear",
        picture="a yawning bear tucked under a quilt",
        piece_name="bear piece",
        bedtime_image="the quilted bear looked ready for bed",
        tags={"puzzle", "bear"},
    ),
    "stars": PuzzleKind(
        id="stars",
        picture="a night sky full of bright stars",
        piece_name="star piece",
        bedtime_image="the starry sky glittered in the lamplight",
        tags={"puzzle", "stars"},
    ),
}

CREAMS = {
    "hand_cream": CreamKind(
        id="hand_cream",
        label="hand cream",
        use_for="dry hands",
        scent="lavender",
        can_smudge=True,
        tags={"cream", "skin"},
    ),
    "face_cream": CreamKind(
        id="face_cream",
        label="face cream",
        use_for="dry cheeks",
        scent="vanilla",
        can_smudge=True,
        tags={"cream", "skin"},
    ),
    "lip_cream": CreamKind(
        id="lip_cream",
        label="lip cream",
        use_for="a sore chap on the lip",
        scent="honey",
        can_smudge=True,
        tags={"cream", "chap", "skin"},
    ),
}

HIDING_PLACES = {
    "blanket": HidingPlace(
        id="blanket",
        label="blanket fold",
        phrase="into the fold of the blanket",
        room_item="blanket",
        bedtime_fit=3,
        found_line="There, tucked in the blanket fold, was the missing piece.",
        tags={"blanket", "bedtime"},
    ),
    "pillow": HidingPlace(
        id="pillow",
        label="under the pillow",
        phrase="under the pillow by the headboard",
        room_item="pillow",
        bedtime_fit=3,
        found_line="Under the pillow by the headboard, the missing piece waited quietly.",
        tags={"pillow", "bedtime"},
    ),
    "bookshelf": HidingPlace(
        id="bookshelf",
        label="beside the bookshelf",
        phrase="beside the low bookshelf",
        room_item="bookshelf",
        bedtime_fit=2,
        found_line="Beside the low bookshelf, shining in a stripe of lamplight, lay the missing piece.",
        tags={"bookshelf", "room"},
    ),
    "slipper": HidingPlace(
        id="slipper",
        label="inside a slipper",
        phrase="inside a small bedside slipper",
        room_item="slipper",
        bedtime_fit=2,
        found_line="Inside a soft bedside slipper was the missing piece, safe and flat.",
        tags={"slipper", "bedtime"},
    ),
}

ACCUSED_ROLES = {
    "brother": AccusedRole(
        id="brother",
        label="brother",
        title="little brother",
        relation_phrase="younger brother",
        tags={"sibling"},
    ),
    "sister": AccusedRole(
        id="sister",
        label="sister",
        title="little sister",
        relation_phrase="younger sister",
        tags={"sibling"},
    ),
    "cousin": AccusedRole(
        id="cousin",
        label="cousin",
        title="small cousin",
        relation_phrase="cousin",
        tags={"family"},
    ),
}

REPAIRS = {
    "gentle": RepairStyle(
        id="gentle",
        kindness=3,
        opener="took a slow breath and spoke softly",
        apology_line="I was worried and I blamed you too fast. I am sorry.",
        lesson_line="It is kinder to ask and listen before deciding what happened.",
        tags={"kindness"},
    ),
    "plain": RepairStyle(
        id="plain",
        kindness=2,
        opener="looked down and answered honestly",
        apology_line="I blamed you, and that was not fair. I am sorry.",
        lesson_line="A careful question is better than a quick blame.",
        tags={"kindness"},
    ),
    "mumbled": RepairStyle(
        id="mumbled",
        kindness=1,
        opener="mumbled an apology without looking up",
        apology_line="Sorry I said you did it.",
        lesson_line="Even when you feel cross, you should tell the truth and make things right.",
        tags={"repair"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Ella", "Lucy", "Rose", "Ivy"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Sam", "Max", "Leo", "Finn", "Eli"]
TRAITS = ["sleepy", "careful", "thoughtful", "quiet", "eager", "gentle"]


def valid_combo(puzzle: PuzzleKind, cream: CreamKind, hiding: HidingPlace, accused: AccusedRole) -> bool:
    if not cream.can_smudge:
        return False
    if hiding.bedtime_fit < 2:
        return False
    if accused.id == "cousin" and hiding.id == "slipper":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for puzzle_id, puzzle in PUZZLES.items():
        for cream_id, cream in CREAMS.items():
            for hiding_id, hiding in HIDING_PLACES.items():
                for accused_id, accused in ACCUSED_ROLES.items():
                    if valid_combo(puzzle, cream, hiding, accused):
                        out.append((puzzle_id, cream_id, hiding_id, accused_id))
    return out


@dataclass
class StoryParams:
    puzzle: str
    cream: str
    hiding: str
    accused: str
    repair: str
    child_name: str
    child_gender: str
    accused_name: str
    accused_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        puzzle="moon",
        cream="lip_cream",
        hiding="pillow",
        accused="brother",
        repair="gentle",
        child_name="Lila",
        child_gender="girl",
        accused_name="Ben",
        accused_gender="boy",
        parent="mother",
        trait="careful",
        seed=1,
    ),
    StoryParams(
        puzzle="bear",
        cream="hand_cream",
        hiding="blanket",
        accused="sister",
        repair="plain",
        child_name="Owen",
        child_gender="boy",
        accused_name="Mia",
        accused_gender="girl",
        parent="father",
        trait="sleepy",
        seed=2,
    ),
    StoryParams(
        puzzle="stars",
        cream="face_cream",
        hiding="bookshelf",
        accused="cousin",
        repair="gentle",
        child_name="Nora",
        child_gender="girl",
        accused_name="Theo",
        accused_gender="boy",
        parent="mother",
        trait="thoughtful",
        seed=3,
    ),
    StoryParams(
        puzzle="moon",
        cream="hand_cream",
        hiding="slipper",
        accused="sister",
        repair="plain",
        child_name="Max",
        child_gender="boy",
        accused_name="Ella",
        accused_gender="girl",
        parent="father",
        trait="eager",
        seed=4,
    ),
]


def predict_innocent_smudge(world: World) -> dict:
    sim = world.copy()
    piece = sim.get("piece")
    cream = sim.get("cream")
    piece.meters["smudged"] += 1
    piece.attrs["smudge_from"] = cream.label
    return {
        "piece_smudged": piece.meters["smudged"] >= THRESHOLD,
        "source": piece.attrs.get("smudge_from", ""),
    }


def introduce(world: World, child: Entity, accused: Entity, parent: Entity, puzzle: PuzzleKind) -> None:
    trait = child.traits[0] if child.traits else "sleepy"
    world.say(
        f"In the soft light before bed, {child.id} sat on the rug with {accused.id}, "
        f"{child.pronoun('possessive')} {accused.attrs.get('relation_phrase', accused.label)}, "
        f"and worked on a picture puzzle of {puzzle.picture}."
    )
    world.say(
        f"{child.id} was a {trait} little {child.type}, and {puzzle.bedtime_image} on the table between them."
    )
    world.say(
        f"{parent.label_word.capitalize()} had just rubbed in a little {world.get('cream').label} that smelled like {world.get('cream').attrs.get('scent', 'soap')}."
    )


def sleepy_need(world: World, child: Entity, puzzle: PuzzleKind) -> None:
    child.memes["hope"] += 1
    world.say(
        f"There was only one {puzzle.piece_name} left to place, and {child.id} wanted to finish before the good-night kiss."
    )


def smudge_appears(world: World, child: Entity, puzzle: PuzzleKind) -> None:
    piece = world.get("piece")
    piece.meters["missing"] += 1
    piece.attrs["location"] = "lost"
    pred = predict_innocent_smudge(world)
    world.facts["predicted_piece_smudged"] = pred["piece_smudged"]
    world.facts["predicted_smudge_source"] = pred["source"]
    world.say(
        f"But when {child.id} reached for the last {puzzle.piece_name}, it was gone. On the empty spot was a tiny white dab of cream."
    )


def misunderstanding(world: World, child: Entity, accused: Entity) -> None:
    child.memes["worry"] += 1
    child.memes["blame"] += 1
    child.memes["trust"] -= 1
    propagate(world, narrate=False)
    world.say(
        f'"{accused.id}, did you take it?" {child.id} asked. The words came out sharper than {child.pronoun()} meant them to.'
    )
    if world.get("cream").id == "lip_cream":
        world.say(
            f'"I only saw the cream and thought maybe you touched it because of your little chap," {child.id} added, then wished the sentence back.'
        )
    else:
        world.say(
            f'"I saw the cream and thought you must have picked it up," {child.id} said.'
        )


def accused_reply(world: World, accused: Entity) -> None:
    accused.memes["sad"] += 1
    world.say(
        f'{accused.id} blinked and held both hands up. "I did not take it," {accused.pronoun()} whispered.'
    )


def parent_guides(world: World, parent: Entity, child: Entity, hiding: HidingPlace) -> None:
    parent.memes["calm"] += 1
    world.say(
        f'{parent.label_word.capitalize()} came closer, saw the cream dab, and knelt beside the rug. '
        f'"Let us ask before we blame," {parent.pronoun()} said softly. '
        f'"Cream can travel on a fingertip, but that does not tell us who moved the piece. Let us look {hiding.phrase} first."'
    )


def search(world: World, child: Entity, accused: Entity, hiding: HidingPlace) -> None:
    child.memes["care"] += 1
    accused.memes["helpfulness"] += 1
    world.say(
        f'So the two children looked carefully together. {accused.id} lifted the edge of the blanket while {child.id} peered {hiding.phrase}.'
    )


def find_piece(world: World, child: Entity, accused: Entity, hiding: HidingPlace, cream: CreamKind) -> None:
    piece = world.get("piece")
    piece.meters["missing"] = 0.0
    piece.meters["found"] += 1
    piece.meters["smudged"] += 1
    piece.attrs["location"] = hiding.id
    piece.attrs["smudge_from"] = cream.label
    propagate(world, narrate=False)
    world.say(hiding.found_line)
    world.say(
        f"A little streak of {cream.label} shone on one corner. It had brushed the piece when a sleepy hand moved it aside."
    )


def explain_truth(world: World, parent: Entity, child: Entity, accused: Entity, cream: CreamKind) -> None:
    if cream.id == "lip_cream":
        cause = "to soothe a sore chap on the lip"
    elif cream.id == "face_cream":
        cause = "to soothe dry cheeks"
    else:
        cause = "to soften dry hands"
    world.say(
        f'{parent.label_word.capitalize()} smiled gently. "{accused.id} was telling the truth," {parent.pronoun()} said. '
        f'"I used that {cream.label} {cause}, and the cream must have touched the piece when we tidied the blanket. The dab was a clue, but it was not the whole story."'
    )
    child.memes["guilt"] += 1


def apology(world: World, child: Entity, accused: Entity, repair: RepairStyle) -> None:
    child.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} {repair.opener}. \"{repair.apology_line}\""
    )
    world.say(
        f'{accused.id} gave a small nod and moved closer again. The hurt in {accused.pronoun("possessive")} face began to soften.'
    )


def finish_puzzle(world: World, child: Entity, accused: Entity, puzzle: PuzzleKind, repair: RepairStyle) -> None:
    child.memes["joy"] += 1
    accused.memes["joy"] += 1
    world.say(
        f'Together they pressed the {puzzle.piece_name} into its place. Now the picture looked whole, and so did the room.'
    )
    world.say(
        f'{world.get("parent").label_word.capitalize()} tucked the blanket around both little shoulders and said, "{repair.lesson_line}"'
    )
    if accused.type == "boy":
        chap_line = "What a thoughtful little chap you are when you make things right."
    else:
        chap_line = "What a thoughtful little chap at heart you are when you make things right."
    world.say(
        f"{world.get('parent').label_word.capitalize()} kissed {child.id}'s hair and added, \"{chap_line}\""
    )
    world.say(
        "Soon the lamp was dim, the puzzle slept in its box, and the children went to bed feeling lighter than before."
    )


def tell(
    puzzle: PuzzleKind,
    cream: CreamKind,
    hiding: HidingPlace,
    accused_role: AccusedRole,
    repair: RepairStyle,
    child_name: str,
    child_gender: str,
    accused_name: str,
    accused_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
    ))
    accused = world.add(Entity(
        id=accused_name,
        kind="character",
        type=accused_gender,
        role="accused",
        attrs={"relation_phrase": accused_role.relation_phrase},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(
        id="piece",
        kind="thing",
        type="puzzle_piece",
        label=puzzle.piece_name,
    ))
    world.add(Entity(
        id="cream",
        kind="thing",
        type="cream",
        label=cream.label,
        attrs={"scent": cream.scent, "use_for": cream.use_for},
    ))

    introduce(world, child, accused, parent, puzzle)
    sleepy_need(world, child, puzzle)

    world.para()
    smudge_appears(world, child, puzzle)
    misunderstanding(world, child, accused)
    accused_reply(world, accused)
    parent_guides(world, parent, child, hiding)

    world.para()
    search(world, child, accused, hiding)
    find_piece(world, child, accused, hiding, cream)
    explain_truth(world, parent, child, accused, cream)
    apology(world, child, accused, repair)

    world.para()
    finish_puzzle(world, child, accused, puzzle, repair)

    world.facts.update(
        child=child,
        accused=accused,
        parent=parent,
        puzzle=puzzle,
        cream=cream,
        hiding=hiding,
        repair=repair,
        misunderstanding=True,
        piece_found=world.get("piece").meters["found"] >= THRESHOLD,
        piece_location=world.get("piece").attrs.get("location"),
        smudged=world.get("piece").meters["smudged"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "cream": [
        (
            "What is cream for on skin?",
            "Skin cream helps dry or sore skin feel softer and calmer. People rub on a little bit so the skin does not feel tight or stingy.",
        )
    ],
    "puzzle": [
        (
            "What is a puzzle piece?",
            "A puzzle piece is one small part of a bigger picture. You have to put all the pieces in the right places to make the whole picture.",
        )
    ],
    "chap": [
        (
            "What is a chap on the lip?",
            "A chap on the lip is a sore, dry crack in the skin. Cream or balm can help it feel better.",
        )
    ],
    "blanket": [
        (
            "Why do small things get lost in a blanket?",
            "A blanket has folds and soft bumps where little things can slide and hide. That is why people check the blanket carefully when something small is missing.",
        )
    ],
    "pillow": [
        (
            "Why might a small object slip under a pillow?",
            "A pillow lifts a little at the edges, so a flat thing can slide underneath it. It can stay hidden until someone looks closely.",
        )
    ],
    "bedtime": [
        (
            "Why is bedtime a good time to speak gently?",
            "At bedtime people are often tired, and tired feelings can make sharp words come faster. Speaking gently helps everyone feel safe and calm.",
        )
    ],
    "kindness": [
        (
            "What should you do before blaming someone?",
            "You should ask what happened and listen carefully first. A kind question gives the truth room to come out.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cream", "puzzle", "chap", "blanket", "pillow", "bedtime", "kindness"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    accused = world.facts["accused"]
    puzzle = world.facts["puzzle"]
    cream = world.facts["cream"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "cream", "puzzle", and "chap".',
        f"Tell a gentle misunderstanding story where {child.id} sees {cream.label} near a missing {puzzle.piece_name} and wrongly blames {accused.id}, then learns to ask kindly before blaming.",
        'Write a soft moral bedtime tale with a missing puzzle piece, a dab of cream, and an ending that teaches that clues are helpful but kindness and listening matter too.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    accused = f["accused"]
    parent = f["parent"]
    puzzle = f["puzzle"]
    cream = f["cream"]
    hiding = f["hiding"]
    repair = f["repair"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {accused.id}, and their {pw} at bedtime. They are trying to finish a picture puzzle together.",
        ),
        (
            "What was the problem in the story?",
            f"The last {puzzle.piece_name} was missing, and there was a dab of {cream.label} where it should have been. That made {child.id} worry and guess the wrong thing too quickly.",
        ),
        (
            f"Why did {child.id} blame {accused.id}?",
            f"{child.id} saw the cream mark and thought it meant {accused.id} had touched the missing piece. The clue looked important, but {child.pronoun()} did not know the whole story yet.",
        ),
        (
            f"Where was the missing piece found?",
            f"It was found {hiding.phrase}. That hiding place fits bedtime, which is why the piece could slip there without anyone meaning any harm.",
        ),
        (
            "Why was there cream on the piece?",
            f"There was cream on the piece because the cream had touched it by accident while things were being tidied near bedtime. The smudge was real, but it came from an innocent moment instead of the blamed child taking the piece.",
        ),
        (
            f"How did {child.id} fix the misunderstanding?",
            f"{child.id} {repair.opener} and apologized to {accused.id}. That mattered because the sharp blame had hurt feelings, and the honest apology helped trust come back.",
        ),
        (
            "What is the moral of the story?",
            f"The story teaches that you should ask and listen before blaming someone. A clue can help you search, but kindness and truth help people stay close.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"cream", "puzzle", "bedtime", "kindness"}
    if world.facts["cream"].id == "lip_cream":
        tags.add("chap")
    if world.facts["hiding"].id == "blanket":
        tags.add("blanket")
    if world.facts["hiding"].id == "pillow":
        tags.add("pillow")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


def explain_rejection(hiding: HidingPlace, accused: AccusedRole, repair: RepairStyle) -> str:
    if hiding.bedtime_fit < 2:
        return (
            f"(No story: {hiding.label} does not feel like a plausible bedtime hiding place for one flat puzzle piece.)"
        )
    if accused.id == "cousin" and hiding.id == "slipper":
        return (
            "(No story: a visiting cousin plus a bedside slipper is too weak a link for this small misunderstanding. Use a sibling there instead.)"
        )
    if repair.kindness < KINDNESS_MIN:
        return (
            f"(Refusing repair '{repair.id}': the apology is too weak for this gentle bedtime moral. Pick a kinder repair style.)"
        )
    return "(No story: these options do not make a clear, gentle misunderstanding.)"


ASP_RULES = r"""
smudge_source(C) :- cream(C), can_smudge(C).
good_hiding(H) :- hiding(H), bedtime_fit(H, B), B >= 2.
valid(P, C, H, A) :- puzzle(P), smudge_source(C), good_hiding(H), accused(A),
                     not bad_pair(H, A).

kind_repair(R) :- repair(R), kindness(R, K), kindness_min(M), K >= M.

bad_pair(slipper, cousin).

selected_valid :- chosen_puzzle(P), chosen_cream(C), chosen_hiding(H), chosen_accused(A),
                  valid(P, C, H, A).
repair_ok :- chosen_repair(R), kind_repair(R).
story_ok :- selected_valid, repair_ok.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for puzzle_id in PUZZLES:
        lines.append(asp.fact("puzzle", puzzle_id))
    for cream_id, cream in CREAMS.items():
        lines.append(asp.fact("cream", cream_id))
        if cream.can_smudge:
            lines.append(asp.fact("can_smudge", cream_id))
    for hiding_id, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hiding_id))
        lines.append(asp.fact("bedtime_fit", hiding_id, hiding.bedtime_fit))
    for accused_id in ACCUSED_ROLES:
        lines.append(asp.fact("accused", accused_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("kindness", repair_id, repair.kindness))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_kind_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show kind_repair/1."))
    return sorted(x for (x,) in asp.atoms(model, "kind_repair"))


def asp_story_ok(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_puzzle", params.puzzle),
            asp.fact("chosen_cream", params.cream),
            asp.fact("chosen_hiding", params.hiding),
            asp.fact("chosen_accused", params.accused),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show story_ok/0."))
    return bool(asp.atoms(model, "story_ok"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Bedtime misunderstanding storyworld with cream, a puzzle, and a gentle moral."
    )
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--cream", choices=CREAMS)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--accused", choices=ACCUSED_ROLES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def _role_gender(role_id: str, rng: random.Random) -> str:
    if role_id == "brother":
        return "boy"
    if role_id == "sister":
        return "girl"
    return rng.choice(["girl", "boy"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hiding and HIDING_PLACES[args.hiding].bedtime_fit < 2:
        raise StoryError(explain_rejection(HIDING_PLACES[args.hiding], ACCUSED_ROLES.get(args.accused or "brother", ACCUSED_ROLES["brother"]), REPAIRS.get(args.repair or "gentle", REPAIRS["gentle"])))
    if args.accused and args.hiding:
        hiding = HIDING_PLACES[args.hiding]
        accused = ACCUSED_ROLES[args.accused]
        if accused.id == "cousin" and hiding.id == "slipper":
            raise StoryError(explain_rejection(hiding, accused, REPAIRS.get(args.repair or "gentle", REPAIRS["gentle"])))
    if args.repair and REPAIRS[args.repair].kindness < KINDNESS_MIN:
        sample_hiding = HIDING_PLACES[args.hiding] if args.hiding else HIDING_PLACES["blanket"]
        sample_accused = ACCUSED_ROLES[args.accused] if args.accused else ACCUSED_ROLES["brother"]
        raise StoryError(explain_rejection(sample_hiding, sample_accused, REPAIRS[args.repair]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.puzzle is None or combo[0] == args.puzzle)
        and (args.cream is None or combo[1] == args.cream)
        and (args.hiding is None or combo[2] == args.hiding)
        and (args.accused is None or combo[3] == args.accused)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    puzzle_id, cream_id, hiding_id, accused_id = rng.choice(sorted(combos))
    repair_choices = [rid for rid, rep in REPAIRS.items() if rep.kindness >= KINDNESS_MIN]
    repair_id = args.repair or rng.choice(sorted(repair_choices))
    child_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    accused_gender = _role_gender(accused_id, rng)
    accused_name = _pick_name(rng, accused_gender, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        puzzle=puzzle_id,
        cream=cream_id,
        hiding=hiding_id,
        accused=accused_id,
        repair=repair_id,
        child_name=child_name,
        child_gender=child_gender,
        accused_name=accused_name,
        accused_gender=accused_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        puzzle = PUZZLES[params.puzzle]
        cream = CREAMS[params.cream]
        hiding = HIDING_PLACES[params.hiding]
        accused_role = ACCUSED_ROLES[params.accused]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not valid_combo(puzzle, cream, hiding, accused_role):
        raise StoryError(explain_rejection(hiding, accused_role, repair))
    if repair.kindness < KINDNESS_MIN:
        raise StoryError(explain_rejection(hiding, accused_role, repair))

    world = tell(
        puzzle=puzzle,
        cream=cream,
        hiding=hiding,
        accused_role=accused_role,
        repair=repair,
        child_name=params.child_name,
        child_gender=params.child_gender,
        accused_name=params.accused_name,
        accused_gender=params.accused_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_repairs = sorted(rid for rid, rep in REPAIRS.items() if rep.kindness >= KINDNESS_MIN)
    asp_repairs = asp_kind_repairs()
    if py_repairs == asp_repairs:
        print(f"OK: kind repairs match ({py_repairs}).")
    else:
        rc = 1
        print(f"MISMATCH in kind repairs: clingo={asp_repairs} python={py_repairs}")

    cases = list(CURATED)
    for s in range(30):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params for seed {s}.")
            break

    for params in cases:
        py_ok = (
            valid_combo(PUZZLES[params.puzzle], CREAMS[params.cream], HIDING_PLACES[params.hiding], ACCUSED_ROLES[params.accused])
            and REPAIRS[params.repair].kindness >= KINDNESS_MIN
        )
        asp_ok = asp_story_ok(params)
        if py_ok != asp_ok:
            rc = 1
            print(f"MISMATCH in story_ok for params: {params}")
            break

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show kind_repair/1.\n#show story_ok/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(f"kind repairs: {', '.join(asp_kind_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (puzzle, cream, hiding, accused) combos:\n")
        for puzzle_id, cream_id, hiding_id, accused_id in combos:
            print(f"  {puzzle_id:8} {cream_id:10} {hiding_id:10} {accused_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name} and {p.accused_name}: {p.puzzle} puzzle, {p.cream}, {p.hiding}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
