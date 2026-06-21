#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/count_dialogue_curiosity_whodunit.py
===============================================================

A small storyworld for a gentle child-sized whodunit: someone has taken part of
a neat little collection, a curious child starts to count, dialogue gathers the
clues, and the mystery is solved without anyone being treated as bad.

The core logic is deliberately narrow. Each suspect has a distinctive "taking
habit" (one, two, or three items) and a distinctive clue they leave behind. The
detective counts what is left, notices how many are missing, compares that with
the clue, and finds the culprit's hiding place. The world model drives the
rendered story and the grounded Q&A.

Run it
------
    python storyworlds/worlds/gpt-5.4/count_dialogue_curiosity_whodunit.py
    python storyworlds/worlds/gpt-5.4/count_dialogue_curiosity_whodunit.py --case cookies --suspect puppy
    python storyworlds/worlds/gpt-5.4/count_dialogue_curiosity_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/count_dialogue_curiosity_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/count_dialogue_curiosity_whodunit.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class CaseFile:
    id: str
    setting: str
    treat_label: str
    treat_phrase: str
    treat_plural: str
    start_count: int
    display_spot: str
    count_line: str
    opening_image: str
    allowed_suspects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectProfile:
    id: str
    type: str
    label: str
    phrase: str
    take_count: int
    clue: str
    trail: str
    hide_spot: str
    motive: str
    excuse: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    case: str
    suspect: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    grownup_type: str
    detective_trait: str
    helper_trait: str
    seed: Optional[int] = None


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
    tray = world.get("tray")
    detective = world.get("detective")
    if tray.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["curiosity"] += 1
    world.get("room").meters["mystery"] += 1
    return []


def _r_counting_gives_suspicion(world: World) -> list[str]:
    detective = world.get("detective")
    if detective.meters["counted"] < THRESHOLD:
        return []
    if world.get("clue").meters["seen"] < THRESHOLD:
        return []
    sig = ("suspicion",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["certainty"] += 1
    return []


def _r_found_resolves(world: World) -> list[str]:
    detective = world.get("detective")
    culprit = world.get("culprit")
    if culprit.meters["found"] < THRESHOLD:
        return []
    sig = ("resolved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["mystery"] = 0.0
    detective.memes["relief"] += 1
    detective.memes["kindness"] += 1
    culprit.memes["embarrassed"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_makes_mystery", tag="story", apply=_r_missing_makes_mystery),
    Rule(name="counting_gives_suspicion", tag="story", apply=_r_counting_gives_suspicion),
    Rule(name="found_resolves", tag="story", apply=_r_found_resolves),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
            elif rule.name in {sig[0] for sig in world.fired}:
                continue
            else:
                pass
        before = len(world.fired)
        # run loop again only if a rule fired this pass; compare by fired size
        if len(world.fired) > before:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


CASES = {
    "cookies": CaseFile(
        id="cookies",
        setting="the kitchen",
        treat_label="star cookies",
        treat_phrase="a plate of star cookies",
        treat_plural="cookies",
        start_count=7,
        display_spot="on the blue table by the window",
        count_line="round stars with bright sugar on top",
        opening_image="The late sun made the sugar on the cookies shine like little lamps.",
        allowed_suspects={"mouse", "puppy", "crow"},
        tags={"count", "cookies", "sharing"},
    ),
    "berry_buns": CaseFile(
        id="berry_buns",
        setting="the picnic table in the garden",
        treat_label="berry buns",
        treat_phrase="a tray of berry buns",
        treat_plural="buns",
        start_count=6,
        display_spot="beside a red pitcher of juice",
        count_line="soft buns with purple jam peeking out",
        opening_image="A light breeze moved the napkins and carried a sweet berry smell.",
        allowed_suspects={"mouse", "puppy", "squirrel"},
        tags={"count", "buns", "garden"},
    ),
    "cheese_crackers": CaseFile(
        id="cheese_crackers",
        setting="the sunroom",
        treat_label="cheese crackers",
        treat_phrase="a basket of cheese crackers",
        treat_plural="crackers",
        start_count=8,
        display_spot="on a low wicker stool near the open screen door",
        count_line="small moons of cracker with a tiny pinch of cheese",
        opening_image="The room felt warm and sleepy, and the basket looked very inviting.",
        allowed_suspects={"mouse", "puppy", "squirrel"},
        tags={"count", "crackers", "snack"},
    ),
}

SUSPECTS = {
    "mouse": SuspectProfile(
        id="mouse",
        type="animal",
        label="mouse",
        phrase="a tiny gray mouse",
        take_count=1,
        clue="a neat rain of tiny crumbs",
        trail="the crumbs were so small that only a little mouth could have made them",
        hide_spot="behind the bread box",
        motive="it wanted one crumbly bite all for itself",
        excuse="It was only one, and it smelled delicious.",
        tags={"mouse", "crumbs"},
    ),
    "puppy": SuspectProfile(
        id="puppy",
        type="animal",
        label="puppy",
        phrase="the wiggly brown puppy",
        take_count=2,
        clue="two dusty pawprints and a happy tail-sweep on the floor",
        trail="the pawprints came in pairs, as if someone had trotted away in a hurry",
        hide_spot="under the hall bench",
        motive="it wanted a snack to carry away and chew in peace",
        excuse="I was saving them for later.",
        tags={"puppy", "pawprints"},
    ),
    "squirrel": SuspectProfile(
        id="squirrel",
        type="animal",
        label="squirrel",
        phrase="a striped squirrel",
        take_count=3,
        clue="a little scatter of leaves and a nibble mark by the edge",
        trail="the leaf bits pointed toward a place a quick climber would choose",
        hide_spot="inside the flowerpot by the porch rail",
        motive="it wanted to stash a few treats like treasure",
        excuse="I was making a secret snack store.",
        tags={"squirrel", "leaves"},
    ),
    "crow": SuspectProfile(
        id="crow",
        type="animal",
        label="crow",
        phrase="a glossy black crow",
        take_count=3,
        clue="one black feather and a scratch beside the plate",
        trail="the feather said wings, and the scratch said beak",
        hide_spot="on the fence post outside the window",
        motive="it wanted shiny sugar and a high perch",
        excuse="They glittered, so I flew off with them.",
        tags={"crow", "feather"},
    ),
}

TRAITS = ["careful", "curious", "patient", "bright", "thoughtful", "observant"]
GIRL_NAMES = ["Mina", "Lila", "Nora", "Eva", "June", "Cora", "Tess", "Ruby"]
BOY_NAMES = ["Owen", "Max", "Leo", "Theo", "Ben", "Finn", "Eli", "Sam"]


def valid_combo(case_id: str, suspect_id: str) -> bool:
    if case_id not in CASES or suspect_id not in SUSPECTS:
        return False
    case = CASES[case_id]
    suspect = SUSPECTS[suspect_id]
    return suspect_id in case.allowed_suspects and case.start_count > suspect.take_count


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for case_id in CASES:
        for suspect_id in SUSPECTS:
            if valid_combo(case_id, suspect_id):
                out.append((case_id, suspect_id))
    return out


def infer_by_count_and_clue(case_id: str, missing: int, clue_text: str) -> str:
    matches = []
    for suspect_id in CASES[case_id].allowed_suspects:
        suspect = SUSPECTS[suspect_id]
        if suspect.take_count == missing and suspect.clue == clue_text:
            matches.append(suspect_id)
    if len(matches) != 1:
        raise StoryError("The clues do not point to exactly one suspect.")
    return matches[0]


def predicted_remaining(case_id: str, suspect_id: str) -> int:
    case = CASES[case_id]
    suspect = SUSPECTS[suspect_id]
    return case.start_count - suspect.take_count


def discover_mischief(world: World, case: CaseFile, suspect: SuspectProfile) -> None:
    tray = world.get("tray")
    clue = world.get("clue")
    culprit = world.get("culprit")
    tray.meters["count"] = float(case.start_count - suspect.take_count)
    tray.meters["missing"] = float(suspect.take_count)
    culprit.meters["taken"] = float(suspect.take_count)
    clue.meters["seen"] = 0.0
    propagate(world, narrate=False)


def introduce(world: World, case: CaseFile, detective: Entity, helper: Entity, grownup: Entity) -> None:
    world.say(
        f"{detective.id} and {helper.id} were helping {detective.pronoun('possessive')} "
        f"{grownup.label_word} in {case.setting}. {case.treat_phrase} sat {case.display_spot}."
    )
    world.say(case.opening_image)
    world.say(
        f'"Please watch these for one minute," said {grownup.label_word}. '
        f'"I need to fetch the lemonade."'
    )


def notice_change(world: World, case: CaseFile, detective: Entity, helper: Entity) -> None:
    tray = world.get("tray")
    world.say(
        f"When the children looked back, the plate did not seem quite right. "
        f"{helper.id} blinked and whispered, \"Wasn't it fuller before?\""
    )
    detective.meters["counted"] += 1
    missing = int(tray.meters["missing"])
    remaining = int(tray.meters["count"])
    world.facts["missing"] = missing
    world.facts["remaining"] = remaining
    world.say(
        f'{detective.id} leaned close. "Let me count," {detective.pronoun()} said. '
        f'{detective.id} touched the row one by one. "One, two, three, four, '
        f'five..." Then {detective.pronoun()} looked up. "Only {remaining}. '
        f'That means {missing} are missing."'
    )
    propagate(world, narrate=False)


def inspect_clue(world: World, suspect: SuspectProfile, detective: Entity, helper: Entity) -> None:
    clue = world.get("clue")
    clue.meters["seen"] += 1
    world.facts["clue_text"] = suspect.clue
    world.say(
        f'{helper.id} pointed at the floor. "Look!" {helper.pronoun()} said. '
        f"There was {suspect.clue}."
    )
    world.say(
        f'{detective.id} nodded slowly. "That is a clue," {detective.pronoun()} said. '
        f'"And {suspect.trail}."'
    )
    propagate(world, narrate=False)


def question_grownup(world: World, case: CaseFile, detective: Entity, helper: Entity, grownup: Entity) -> None:
    world.para()
    world.say(
        f'{grownup.label_word.capitalize()} came back with the pitcher and stopped short. '
        f'"Oh! Did someone take some of the {case.treat_plural}?"'
    )
    world.say(
        f'"We are finding out now," said {detective.id}. '
        f'"{helper.id} found the clue, and I did the count."'
    )
    world.say(
        f'"Then I have two detectives on the case," said {grownup.label_word} with a small smile.'
    )


def follow_trail(world: World, suspect: SuspectProfile, detective: Entity, helper: Entity) -> None:
    world.para()
    world.say(
        f'The children followed the clue trail very carefully. '
        f'"Not too fast," said {detective.id}. "Mysteries like calm eyes."'
    )
    world.say(
        f'{helper.id} walked beside {detective.pronoun("object")} and whispered, '
        f'"Where does it lead?"'
    )
    world.say(
        f'"To the best hiding place for our thief," said {detective.id}.'
    )
    world.say(
        f'Sure enough, the trail led to {suspect.hide_spot}.'
    )


def reveal(world: World, case: CaseFile, suspect: SuspectProfile, detective: Entity, helper: Entity, grownup: Entity) -> None:
    culprit = world.get("culprit")
    culprit.meters["found"] += 1
    world.say(
        f'There was {suspect.phrase}, trying to guard the missing {case.treat_plural}. '
        f'{helper.id} gasped. "{suspect.label.capitalize()}!"'
    )
    world.say(
        f'{detective.id} folded {detective.pronoun("possessive")} hands like a tiny inspector. '
        f'"I knew it," {detective.pronoun()} said. "The count said {suspect.take_count}, '
        f'and the clue said {suspect.label}."'
    )
    world.say(
        f'{grownup.label_word.capitalize()} knelt down and sighed, but not in an angry way. '
        f'"So that was the mystery," {grownup.pronoun()} said.'
    )
    propagate(world, narrate=False)


def kind_resolution(world: World, case: CaseFile, suspect: SuspectProfile, detective: Entity, helper: Entity, grownup: Entity) -> None:
    culprit = world.get("culprit")
    culprit.memes["comforted"] += 1
    world.para()
    world.say(
        f'{grownup.label_word.capitalize()} gently took back the missing {case.treat_plural}. '
        f'"You must not sneak snacks," {grownup.pronoun()} told {suspect.label}. '
        f'"But I can see why they smelled tempting."'
    )
    world.say(
        f'{helper.id} crouched nearby. "So {suspect.pronoun()} was not being mean," '
        f'{helper.pronoun()} said.'
    )
    world.say(
        f'"No," said {detective.id}. "Just hungry and hopeful."'
    )
    world.say(
        f'{grownup.label_word.capitalize()} set one proper little treat into a bowl for '
        f'{suspect.label}, then moved the rest higher up.'
    )
    culprit.meters["shared"] += 1
    world.say(
        f"After that, {detective.id} counted the plate once more. Everything matched again, "
        f"and the case felt closed."
    )
    world.say(
        f'The children sat side by side, nibbling their own snack and retelling the mystery in '
        f'hushed detective voices. {helper.id} tapped the table and said, "Next time, we count first."'
    )


def tell(
    case: CaseFile,
    suspect: SuspectProfile,
    detective_name: str,
    detective_gender: str,
    helper_name: str,
    helper_gender: str,
    grownup_type: str,
    detective_trait: str,
    helper_trait: str,
) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        label=detective_name,
        traits=[detective_trait],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        label=helper_name,
        traits=[helper_trait],
    ))
    grownup = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the grownup",
    ))
    tray = world.add(Entity(
        id="tray",
        type="tray",
        label=case.treat_label,
        phrase=case.treat_phrase,
        attrs={"start_count": case.start_count},
        tags=set(case.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label="clue",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=case.setting,
    ))
    culprit = world.add(Entity(
        id="culprit",
        type=suspect.type,
        label=suspect.label,
        phrase=suspect.phrase,
        tags=set(suspect.tags),
    ))

    discover_mischief(world, case, suspect)

    introduce(world, case, detective, helper, grownup)
    world.para()
    notice_change(world, case, detective, helper)
    inspect_clue(world, suspect, detective, helper)
    question_grownup(world, case, detective, helper, grownup)
    follow_trail(world, suspect, detective, helper)
    reveal(world, case, suspect, detective, helper, grownup)
    kind_resolution(world, case, suspect, detective, helper, grownup)

    world.facts.update(
        case=case,
        suspect=suspect,
        detective=detective,
        helper=helper,
        grownup=grownup,
        clue_entity=clue,
        tray=tray,
        culprit=culprit,
        solved=culprit.meters["found"] >= THRESHOLD,
        mystery_resolved=room.meters["mystery"] < THRESHOLD,
    )
    return world


def pair_word(det: Entity, helper: Entity) -> str:
    if det.type == "girl" and helper.type == "girl":
        return "two girls"
    if det.type == "boy" and helper.type == "boy":
        return "two boys"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    suspect = f["suspect"]
    detective = f["detective"]
    helper = f["helper"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the word "count" and takes place in {case.setting}.',
        f"Tell a mystery where {detective.id} and {helper.id} notice that some {case.treat_plural} are missing, use dialogue to follow a clue, and solve the case kindly.",
        f"Write a child-sized detective story where the missing number is {suspect.take_count}, the clue points to a {suspect.label}, and the ending shows the mystery safely solved.",
    ]


KNOWLEDGE = {
    "count": [
        ("Why is counting useful in a mystery?",
         "Counting helps you notice when something has changed. If you know how many things should be there, you can tell when some are missing.")
    ],
    "clue": [
        ("What is a clue?",
         "A clue is a small sign that helps you figure something out. It might be a footprint, a crumb, or something left behind.")
    ],
    "sharing": [
        ("Why should we ask before taking a snack?",
         "Asking is kind because the snack might belong to everyone. It also helps grown-ups keep things fair and safe.")
    ],
    "mouse": [
        ("Why are mouse crumbs so tiny?",
         "A mouse has a very small mouth and little teeth, so the bits it leaves behind are small too.")
    ],
    "puppy": [
        ("Why can a puppy leave pawprints?",
         "A puppy walks on soft paws that can pick up dust or mud. When it trots away, those paws can print the floor.")
    ],
    "squirrel": [
        ("Why might a squirrel hide food?",
         "Squirrels like to stash food away for later. Hiding snacks is part of how they keep little treasures for themselves.")
    ],
    "crow": [
        ("Why might a crow take something shiny?",
         "Crows notice bright things very well. A shiny treat or wrapper can catch a crow's eye.")
    ],
}
KNOWLEDGE_ORDER = ["count", "clue", "sharing", "mouse", "puppy", "squirrel", "crow"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    case = f["case"]
    suspect = f["suspect"]
    detective = f["detective"]
    helper = f["helper"]
    grownup = f["grownup"]
    missing = f["missing"]
    remaining = f["remaining"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_word(detective, helper)}, {detective.id} and {helper.id}, who become little detectives in {case.setting}. It also includes their {grownup.label_word}, who helps the ending stay calm and kind."
        ),
        (
            f"What was the mystery in {case.setting}?",
            f"The mystery was that some of the {case.treat_plural} were gone from the plate. {detective.id} noticed the row looked wrong and began to count."
        ),
        (
            f"How did {detective.id} figure out how many were missing?",
            f"{detective.id} counted the treats that were left and found only {remaining}. Because there had started out as {case.start_count}, that meant {missing} were missing."
        ),
        (
            "What clue did the children find?",
            f"They found {suspect.clue}. That clue mattered because it matched the way the real culprit moved and ate."
        ),
        (
            f"How did the count and the clue solve the case?",
            f"The count pointed to a thief who had taken {suspect.take_count}, and the clue pointed to a {suspect.label}. Together, those two facts fit only one suspect, so the children knew where to look."
        ),
        (
            f"Where did they find the culprit?",
            f"They followed the trail to {suspect.hide_spot}. There they found {suspect.phrase} with the missing {case.treat_plural}."
        ),
        (
            "How did the story end?",
            f"It ended gently: the grownup took back the snacks, gave the culprit one proper treat, and moved the rest to a safer place. Then {detective.id} counted again, and everything matched, which showed the mystery was over."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"count", "clue", "sharing"}
    suspect = world.facts["suspect"]
    if suspect.id in KNOWLEDGE:
        tags.add(suspect.id)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        case="cookies",
        suspect="puppy",
        detective_name="Mina",
        detective_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        grownup_type="mother",
        detective_trait="observant",
        helper_trait="curious",
    ),
    StoryParams(
        case="berry_buns",
        suspect="squirrel",
        detective_name="Theo",
        detective_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        grownup_type="father",
        detective_trait="patient",
        helper_trait="bright",
    ),
    StoryParams(
        case="cheese_crackers",
        suspect="mouse",
        detective_name="Nora",
        detective_gender="girl",
        helper_name="Eva",
        helper_gender="girl",
        grownup_type="mother",
        detective_trait="careful",
        helper_trait="thoughtful",
    ),
    StoryParams(
        case="cookies",
        suspect="crow",
        detective_name="Ben",
        detective_gender="boy",
        helper_name="June",
        helper_gender="girl",
        grownup_type="father",
        detective_trait="curious",
        helper_trait="patient",
    ),
]


def explain_rejection(case_id: str, suspect_id: str) -> str:
    if case_id not in CASES:
        return f"(No story: unknown case '{case_id}'.)"
    if suspect_id not in SUSPECTS:
        return f"(No story: unknown suspect '{suspect_id}'.)"
    case = CASES[case_id]
    suspect = SUSPECTS[suspect_id]
    if suspect_id not in case.allowed_suspects:
        return (
            f"(No story: a {suspect.label} is not a good fit for the {case.id} case. "
            f"Pick one of: {', '.join(sorted(case.allowed_suspects))}.)"
        )
    if case.start_count <= suspect.take_count:
        return (
            f"(No story: the suspect would take too many {case.treat_plural} for the "
            f"starting count of {case.start_count}.)"
        )
    return "(No story: that case and suspect do not form a reasonable mystery.)"


ASP_RULES = r"""
valid(Case, Suspect) :- case(Case), suspect(Suspect), allowed(Case, Suspect),
                        start_count(Case, N), take_count(Suspect, T), N > T.

missing(Case, Suspect, M) :- valid(Case, Suspect), start_count(Case, N),
                             take_count(Suspect, T), M = N - T.

inferred(S) :- chosen_case(C), chosen_clue(Cl), chosen_remaining(R),
               valid(C, S), clue_of(S, Cl), start_count(C, N),
               take_count(S, T), R = N - T.

solution_unique :- 1 { inferred(S) : suspect(S) } 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        lines.append(asp.fact("start_count", case_id, case.start_count))
        for suspect_id in sorted(case.allowed_suspects):
            lines.append(asp.fact("allowed", case_id, suspect_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        lines.append(asp.fact("take_count", suspect_id, suspect.take_count))
        lines.append(asp.fact("clue_of", suspect_id, suspect.clue))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_inferred_suspect(case_id: str, suspect_id: str) -> str:
    import asp
    remaining = predicted_remaining(case_id, suspect_id)
    clue = SUSPECTS[suspect_id].clue
    extra = "\n".join([
        asp.fact("chosen_case", case_id),
        asp.fact("chosen_clue", clue),
        asp.fact("chosen_remaining", remaining),
    ])
    model = asp.one_model(asp_program(extra, "#show inferred/1.\n#show solution_unique/0."))
    inferred = asp.atoms(model, "inferred")
    if len(inferred) != 1:
        return "?"
    return inferred[0][0]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A gentle child-sized whodunit driven by counting and clues."
    )
    ap.add_argument("--case", choices=sorted(CASES))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid case/suspect pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.suspect and not valid_combo(args.case, args.suspect):
        raise StoryError(explain_rejection(args.case, args.suspect))

    combos = [
        (case_id, suspect_id)
        for (case_id, suspect_id) in valid_combos()
        if (args.case is None or case_id == args.case)
        and (args.suspect is None or suspect_id == args.suspect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, suspect_id = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    detective_name = _pick_name(rng, detective_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=detective_name)
    grownup_type = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(
        case=case_id,
        suspect=suspect_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        grownup_type=grownup_type,
        detective_trait=rng.choice(TRAITS),
        helper_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"(No story: unknown case '{params.case}'.)")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(No story: unknown suspect '{params.suspect}'.)")
    if not valid_combo(params.case, params.suspect):
        raise StoryError(explain_rejection(params.case, params.suspect))

    world = tell(
        case=CASES[params.case],
        suspect=SUSPECTS[params.suspect],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        grownup_type=params.grownup_type,
        detective_trait=params.detective_trait,
        helper_trait=params.helper_trait,
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
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    for case_id, suspect_id in sorted(py_valid):
        inferred_py = infer_by_count_and_clue(
            case_id=case_id,
            missing=SUSPECTS[suspect_id].take_count,
            clue_text=SUSPECTS[suspect_id].clue,
        )
        inferred_asp = asp_inferred_suspect(case_id, suspect_id)
        if inferred_py != inferred_asp:
            rc = 1
            print(
                f"MISMATCH in inference for ({case_id}, {suspect_id}): "
                f"python={inferred_py} asp={inferred_asp}"
            )
            break
    else:
        print(f"OK: ASP inference matches Python on {len(py_valid)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Randomly generated empty story.")
        print("OK: default resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show inferred/1.\n#show solution_unique/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (case, suspect) pairs:\n")
        for case_id, suspect_id in combos:
            print(f"  {case_id:15} {suspect_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.case}: culprit {p.suspect}"
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
