#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/heck_morale_bad_ending_lesson_learned_twist.py
=========================================================================

A standalone story world for a child-facing detective tale with a twist:
two junior detectives rush to blame the wrong helper for a missing event item,
the real cause turns out to be an innocent accident, and they learn the hard way
that quick guesses can hurt people and spoil a special day.

Seed goals carried into the world:
- include the words "heck" and "morale"
- feature a Bad Ending, a Lesson Learned, and a Twist
- keep the style close to a Detective Story

Run it
------
    python storyworlds/worlds/gpt-5.4/heck_morale_bad_ending_lesson_learned_twist.py
    python storyworlds/worlds/gpt-5.4/heck_morale_bad_ending_lesson_learned_twist.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/heck_morale_bad_ending_lesson_learned_twist.py --all --qa
    python storyworlds/worlds/gpt-5.4/heck_morale_bad_ending_lesson_learned_twist.py --trace --seed 19
    python storyworlds/worlds/gpt-5.4/heck_morale_bad_ending_lesson_learned_twist.py --json
    python storyworlds/worlds/gpt-5.4/heck_morale_bad_ending_lesson_learned_twist.py --verify
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
    role: str = ""
    phrase: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str = ""
    place: str = ""
    event: str = ""
    crowd: str = ""
    opening: str = ""
    ending_loss: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str = ""
    label: str = ""
    phrase: str = ""
    purpose: str = ""
    hiding_place: str = ""
    movable_by: set[str] = field(default_factory=set)
    settings: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str = ""
    label: str = ""
    found_at: str = ""
    suspect_ids: set[str] = field(default_factory=set)
    cause_ids: set[str] = field(default_factory=set)
    inference: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str = ""
    label: str = ""
    phrase: str = ""
    job: str = ""
    denial: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str = ""
    label: str = ""
    phrase: str = ""
    verb: str = ""
    reveal: str = ""
    recovery: str = ""
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


def _r_missing_hurts_morale(world: World) -> list[str]:
    if "item" not in world.entities or "crowd" not in world.entities:
        return []
    item = world.get("item")
    crowd = world.get("crowd")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_hurts_morale",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.memes["morale_low"] += 1
    return ["__morale__"]


def _r_false_accusation_stings(world: World) -> list[str]:
    if "suspect" not in world.entities:
        return []
    suspect = world.get("suspect")
    if suspect.memes["wrongly_accused"] < THRESHOLD:
        return []
    sig = ("false_accusation_stings",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    world.get("detective1").memes["guilt"] += 1
    world.get("detective2").memes["guilt"] += 1
    if "crowd" in world.entities:
        world.get("crowd").memos = getattr(world.get("crowd"), "memos", None)
        world.get("crowd").memes["morale_low"] += 1
    return ["__accusation__"]


def _r_truth_gives_lesson(world: World) -> list[str]:
    if "case" not in world.entities:
        return []
    case = world.get("case")
    if case.meters["truth_found"] < THRESHOLD:
        return []
    sig = ("truth_gives_lesson",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("detective1", "detective2"):
        world.get(eid).memes["lesson"] += 1
    return []


def _r_late_find_fails_event(world: World) -> list[str]:
    if "case" not in world.entities:
        return []
    case = world.get("case")
    if case.meters["late"] < THRESHOLD or case.meters["truth_found"] < THRESHOLD:
        return []
    sig = ("late_find_fails_event",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("event").meters["failed"] += 1
    return ["__bad_end__"]


CAUSAL_RULES = [
    Rule(name="missing_hurts_morale", tag="social", apply=_r_missing_hurts_morale),
    Rule(name="false_accusation_stings", tag="social", apply=_r_false_accusation_stings),
    Rule(name="truth_gives_lesson", tag="social", apply=_r_truth_gives_lesson),
    Rule(name="late_find_fails_event", tag="social", apply=_r_late_find_fails_event),
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


SETTINGS = {
    "schoolyard": Setting(
        id="schoolyard",
        place="the schoolyard",
        event="the spring fair",
        crowd="children and teachers",
        opening="Bright paper streamers bobbed above the schoolyard, and the detective club had promised to help before the spring fair began.",
        ending_loss="By the time the banner came back, the fair gates were already open, and the opening cheer had gone ahead without it.",
        tags={"school", "fair", "detective"},
    ),
    "bandstand": Setting(
        id="bandstand",
        place="the town bandstand",
        event="the little parade",
        crowd="neighbors in folding chairs",
        opening="Chairs lined the bandstand path, and the detective club had been asked to keep watch before the little parade stepped off.",
        ending_loss="By the time the whistle came back, the parade had already rounded the corner without its clean bright start.",
        tags={"town", "parade", "detective"},
    ),
    "field": Setting(
        id="field",
        place="the community field",
        event="sports day",
        crowd="families on the grass",
        opening="Flags flicked over the community field, and the detective club was trying to look very official before sports day began.",
        ending_loss="By the time the medal box came back, the first race prizes had been handed out with paper stars instead.",
        tags={"field", "sports", "detective"},
    ),
}

ITEMS = {
    "banner": MissingItem(
        id="banner",
        label="banner",
        phrase="the welcome banner",
        purpose="to hang over the gate",
        hiding_place="behind the hedge by the side path",
        movable_by={"puppy"},
        settings={"schoolyard"},
        tags={"banner", "fair"},
    ),
    "whistle": MissingItem(
        id="whistle",
        label="whistle",
        phrase="the silver parade whistle",
        purpose="to start the first marching song",
        hiding_place="under a park bench near the duck pond",
        movable_by={"wagon"},
        settings={"bandstand"},
        tags={"whistle", "parade"},
    ),
    "medal_box": MissingItem(
        id="medal_box",
        label="medal box",
        phrase="the blue medal box",
        purpose="to hold the shiny race medals",
        hiding_place="inside the open shed by the cone stack",
        movable_by={"cat"},
        settings={"field"},
        tags={"medals", "sports"},
    ),
}

CLUES = {
    "muddy_prints": Clue(
        id="muddy_prints",
        label="muddy prints",
        found_at="little muddy prints on the path beside the missing pole hooks",
        suspect_ids={"gardener"},
        cause_ids={"puppy"},
        inference="The prints looked as if they had come from the flower beds, which made the gardeners seem like the obvious answer.",
        tags={"prints", "mud"},
    ),
    "wheel_marks": Clue(
        id="wheel_marks",
        label="wheel marks",
        found_at="thin wheel marks crossing the path beside the music stand",
        suspect_ids={"janitor"},
        cause_ids={"wagon"},
        inference="The lines looked so neat that they seemed to belong to a grown-up cart.",
        tags={"wheels"},
    ),
    "flour_paw": Clue(
        id="flour_paw",
        label="floury paw marks",
        found_at="small white paw marks dusted across the grass near the prize table",
        suspect_ids={"baker"},
        cause_ids={"cat"},
        inference="The white dust looked like bakery flour, so the baking tent seemed to point the finger.",
        tags={"flour", "paw"},
    ),
}

SUSPECTS = {
    "gardener": Suspect(
        id="gardener",
        label="Mr. Reed",
        phrase="Mr. Reed the gardener",
        job="gardener",
        denial='"I only moved the watering can," Mr. Reed said. "I would never hide the fair banner."',
        tags={"gardener"},
    ),
    "janitor": Suspect(
        id="janitor",
        label="Ms. Bell",
        phrase="Ms. Bell the janitor",
        job="janitor",
        denial='"I rolled a broom cart earlier," Ms. Bell said, "but I did not touch the parade whistle."',
        tags={"janitor"},
    ),
    "baker": Suspect(
        id="baker",
        label="Mrs. Crumb",
        phrase="Mrs. Crumb from the bake table",
        job="baker",
        denial='"I have been icing buns all morning," Mrs. Crumb said. "I did not carry off the medal box."',
        tags={"baker"},
    ),
}

CAUSES = {
    "puppy": Cause(
        id="puppy",
        label="a puppy",
        phrase="the mayor's bouncy puppy",
        verb="dragged",
        reveal="the mayor's puppy trotted out from the hedge, proud as anything, with a corner of cloth caught on its collar",
        recovery="The children followed the wagging tail and found the banner rumpled behind the hedge.",
        tags={"animal", "puppy"},
    ),
    "wagon": Cause(
        id="wagon",
        label="a runaway wagon",
        phrase="a little red wagon with one wobbly wheel",
        verb="bumped",
        reveal="a gust nudged a little red wagon downhill, and it bumped the whistle under the bench with a bright tinny clink",
        recovery="The detectives crouched by the bench and pulled the whistle from the dust just as the last marchers were leaving.",
        tags={"wagon", "accident"},
    ),
    "cat": Cause(
        id="cat",
        label="a floury cat",
        phrase="the baker's sneaky gray cat",
        verb="nudged",
        reveal="the baker's gray cat slipped from the tent flap with white paws and a ribbon in its mouth, and the open shed door told the rest of the story",
        recovery="Inside the shed, the detectives found the medal box pushed behind a stack of orange cones.",
        tags={"animal", "cat"},
    ),
}


def item_fits_setting(item: MissingItem, setting: Setting) -> bool:
    return setting.id in item.settings


def cause_can_move_item(cause: Cause, item: MissingItem) -> bool:
    return cause.id in item.movable_by


def clue_points_to_pair(clue: Clue, suspect: Suspect, cause: Cause) -> bool:
    return suspect.id in clue.suspect_ids and cause.id in clue.cause_ids


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            if not item_fits_setting(item, setting):
                continue
            for clue_id, clue in CLUES.items():
                for suspect_id, suspect in SUSPECTS.items():
                    for cause_id, cause in CAUSES.items():
                        if clue_points_to_pair(clue, suspect, cause) and cause_can_move_item(cause, item):
                            combos.append((setting_id, item_id, clue_id, suspect_id, cause_id))
    return sorted(combos)


@dataclass
class StoryParams:
    setting: str = ""
    item: str = ""
    clue: str = ""
    suspect: str = ""
    cause: str = ""
    detective1: str = ""
    detective1_gender: str = ""
    detective2: str = ""
    detective2_gender: str = ""
    leader_trait: str = ""
    seed: Optional[int] = None


GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Lucy", "Zoe", "Ella", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]
TRAITS = ["careful", "eager", "sharp-eyed", "bold", "quick-thinking", "serious"]


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options), gender


def explain_rejection(setting_id: str, item_id: str, clue_id: str, suspect_id: str, cause_id: str) -> str:
    parts = []
    if setting_id and item_id:
        if setting_id in SETTINGS and item_id in ITEMS and not item_fits_setting(ITEMS[item_id], SETTINGS[setting_id]):
            parts.append(f"{ITEMS[item_id].phrase} does not belong in {SETTINGS[setting_id].event}")
    if cause_id and item_id:
        if cause_id in CAUSES and item_id in ITEMS and not cause_can_move_item(CAUSES[cause_id], ITEMS[item_id]):
            parts.append(f"{CAUSES[cause_id].label} would not reasonably move {ITEMS[item_id].phrase}")
    if clue_id and suspect_id and cause_id:
        if clue_id in CLUES and suspect_id in SUSPECTS and cause_id in CAUSES:
            if not clue_points_to_pair(CLUES[clue_id], SUSPECTS[suspect_id], CAUSES[cause_id]):
                parts.append("the clue would not honestly point to both the false suspect and the true cause")
    if not parts:
        parts.append("the requested detective setup is not a reasonable story in this world")
    return "(No story: " + "; ".join(parts) + ".)"


def setup_scene(world: World, d1: Entity, d2: Entity, setting: Setting, item: MissingItem) -> None:
    d1.memes["curiosity"] += 1
    d2.memes["curiosity"] += 1
    world.say(setting.opening)
    world.say(
        f'{d1.id} and {d2.id} wore paper detective badges and promised to watch {item.phrase}, '
        f"which was needed {item.purpose}."
    )


def discover_missing(world: World, d1: Entity, d2: Entity, item_ent: Entity, crowd: Entity, setting: Setting) -> None:
    item_ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when the club reached the stand in {setting.place}, {item_ent.label_word} was gone. "
        f"A worried hush spread through {crowd.label}, and the morale of the whole place sank."
    )
    world.say(
        f'"What the heck?" {d1.id} whispered. {d2.id} opened the little notebook even faster.'
    )


def inspect_clue(world: World, d1: Entity, d2: Entity, clue: Clue) -> None:
    world.say(
        f"They knelt down and found {clue.found_at}. {clue.inference}"
    )
    d1.memes["certainty"] += 1


def accuse(world: World, d1: Entity, d2: Entity, suspect_ent: Entity, suspect: Suspect, clue: Clue) -> None:
    suspect_ent.memes["wrongly_accused"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{d1.id} tapped the clue and said, "Case closed. It must have been {suspect.label}." '
        f'{d2.id} followed along, because the clue seemed to fit.'
    )
    world.say(suspect.denial)
    if suspect_ent.memes["hurt"] >= THRESHOLD:
        world.say(
            f"The words landed heavily. {suspect.label} looked more sad than angry, and that made the young detectives feel odd inside."
        )


def twist_reveal(world: World, cause: Cause, item: MissingItem) -> None:
    world.get("case").meters["truth_found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the twist: {cause.reveal}. Nobody had stolen anything at all."
    )
    world.say(cause.recovery)


def late_failure(world: World, setting: Setting) -> None:
    world.get("case").meters["late"] += 1
    propagate(world, narrate=False)
    world.say(setting.ending_loss)
    world.say(
        "The mystery was solved, but too late to save the moment it had been meant for."
    )


def apology_and_lesson(world: World, d1: Entity, d2: Entity, suspect: Suspect) -> None:
    world.say(
        f'{d1.id} and {d2.id} hurried back to {suspect.label} and said sorry for blaming {suspect.pronoun("object")} before they knew the truth.'
    )
    world.say(
        f'{suspect.label} gave a small nod. "A clue is a beginning, not the end," {suspect.pronoun()} said.'
    )
    world.say(
        f"The detectives wrote that line in their notebook and underlined it twice. "
        f"They had cracked the case, but they had also learned that a fast answer can hurt people and leave a whole crowd disappointed."
    )


def ending_image(world: World, d1: Entity, d2: Entity, item: MissingItem, setting: Setting) -> None:
    world.say(
        f"At sunset, {item.phrase} was back where it belonged, but the lost cheer of {setting.event} could not be pasted together again."
    )
    world.say(
        f"{d1.id} and {d2.id} tucked away their badges and stood quietly beside the gate, determined that next time they would follow every clue before speaking."
    )


def tell(
    setting: Setting,
    item_cfg: MissingItem,
    clue: Clue,
    suspect_cfg: Suspect,
    cause: Cause,
    detective1: str,
    detective1_gender: str,
    detective2: str,
    detective2_gender: str,
    leader_trait: str,
) -> World:
    world = World()
    d1 = world.add(Entity(
        id=detective1,
        kind="character",
        type=detective1_gender,
        label=detective1,
        role="detective",
        attrs={"trait": leader_trait},
    ))
    d2 = world.add(Entity(
        id=detective2,
        kind="character",
        type=detective2_gender,
        label=detective2,
        role="detective",
        attrs={"trait": "loyal"},
    ))
    suspect_ent = world.add(Entity(
        id="suspect",
        kind="character",
        type="person",
        label=suspect_cfg.label,
        role="suspect",
        attrs={"job": suspect_cfg.job},
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="group",
        type="group",
        label=setting.crowd,
        role="crowd",
    ))
    event = world.add(Entity(
        id="event",
        kind="thing",
        type="event",
        label=setting.event,
        role="event",
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="missing_item",
    ))
    world.add(Entity(
        id="case",
        kind="thing",
        type="case",
        label="the case",
        role="case",
    ))

    setup_scene(world, d1, d2, setting, item_cfg)
    world.para()
    discover_missing(world, d1, d2, item_ent, crowd, setting)
    inspect_clue(world, d1, d2, clue)
    accuse(world, d1, d2, suspect_ent, suspect_cfg, clue)
    world.para()
    twist_reveal(world, cause, item_cfg)
    late_failure(world, setting)
    world.para()
    apology_and_lesson(world, d1, d2, suspect_ent)
    ending_image(world, d1, d2, item_cfg, setting)

    world.facts.update(
        setting=setting,
        item_cfg=item_cfg,
        clue=clue,
        suspect_cfg=suspect_cfg,
        cause=cause,
        detective1=d1,
        detective2=d2,
        suspect=suspect_ent,
        crowd=crowd,
        item=item_ent,
        event=event,
        morale_low=crowd.memes["morale_low"] >= THRESHOLD,
        wrong_accusation=suspect_ent.memes["wrongly_accused"] >= THRESHOLD,
        truth_found=world.get("case").meters["truth_found"] >= THRESHOLD,
        event_failed=event.meters["failed"] >= THRESHOLD,
        lesson_learned=d1.memes["lesson"] >= THRESHOLD and d2.memes["lesson"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d1 = f["detective1"]
    d2 = f["detective2"]
    item = f["item_cfg"]
    setting = f["setting"]
    suspect = f["suspect_cfg"]
    return [
        'Write a detective story for a young child that includes the words "heck" and "morale" and ends with a sad lesson.',
        f"Tell a junior-detective story where {d1.id} and {d2.id} rush to blame {suspect.label} for a missing {item.label}, then discover an innocent twist too late to save {setting.event}.",
        f"Write a small mystery set at {setting.place} where a missing {item.label} lowers everyone's morale, the detectives make a wrong accusation, and the ending teaches them to check clues more carefully.",
    ]


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks careful questions to figure out what really happened. Good detectives do not decide too early."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you solve a mystery. One clue can help, but it should be checked with other clues before you blame someone."
        )
    ],
    "morale": [
        (
            "What does morale mean?",
            "Morale is how hopeful and cheerful a group feels. When something goes wrong, morale can drop and everyone may feel less brave or happy."
        )
    ],
    "apology": [
        (
            "Why is it important to say sorry after a wrong accusation?",
            "Saying sorry shows that you understand you hurt someone. It helps repair trust, even if the mistake cannot be undone."
        )
    ],
    "puppy": [
        (
            "Why do puppies make trouble by accident?",
            "Puppies are curious and playful, so they grab and drag things without meaning to be naughty. That is why grown-ups keep a close eye on important objects around them."
        )
    ],
    "wagon": [
        (
            "Why can a wagon roll away?",
            "A wagon can roll away if it is left on a slope or gets nudged. Wheels keep moving unless someone stops them."
        )
    ],
    "cat": [
        (
            "Why do cats sneak into places?",
            "Cats like to explore warm, quiet, or interesting places. They can push or nudge things while they are nosing around."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "clue", "morale", "apology", "puppy", "wagon", "cat"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d1 = f["detective1"]
    d2 = f["detective2"]
    item = f["item_cfg"]
    setting = f["setting"]
    clue = f["clue"]
    suspect = f["suspect_cfg"]
    cause = f["cause"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the main characters?",
            f"The story is about two young detectives, {d1.id} and {d2.id}, and {suspect.label}, the helper they blamed by mistake. It also turns on {cause.label}, which caused the trouble without meaning to."
        ),
        (
            f"What was missing, and why did it matter?",
            f"{item.phrase.capitalize()} was missing, and it was needed {item.purpose}. Without it, the start of {setting.event} felt shaky, so the crowd's morale dropped right away."
        ),
        (
            "What clue did the detectives find?",
            f"They found {clue.found_at}. That clue looked convincing at first, which is why they made a quick guess instead of slowing down."
        ),
        (
            f"Why did {d1.id} and {d2.id} blame {suspect.label}?",
            f"They thought the clue pointed straight to {suspect.label}. The clue seemed to match {suspect.pronoun('possessive')} work, so they treated one sign like final proof."
        ),
        (
            "What was the twist in the mystery?",
            f"The twist was that nobody had stolen the missing thing at all. {cause.reveal.capitalize()}, so the item had only been moved by accident."
        ),
        (
            "Why is the ending a bad ending, even though the case is solved?",
            f"The detectives did find the truth, but they found it too late. {setting.ending_loss} That means the answer came after the special moment was already gone."
        ),
        (
            "What lesson did the detectives learn?",
            f"They learned that a clue is only a beginning, not the whole answer. Because they blamed someone too fast, they hurt feelings and lost time they needed to save the event."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "clue", "morale", "apology"}
    cause = world.facts["cause"]
    if cause.id == "puppy":
        tags.add("puppy")
    if cause.id == "wagon":
        tags.add("wagon")
    if cause.id == "cat":
        tags.add("cat")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="schoolyard",
        item="banner",
        clue="muddy_prints",
        suspect="gardener",
        cause="puppy",
        detective1="Nora",
        detective1_gender="girl",
        detective2="Ben",
        detective2_gender="boy",
        leader_trait="serious",
    ),
    StoryParams(
        setting="bandstand",
        item="whistle",
        clue="wheel_marks",
        suspect="janitor",
        cause="wagon",
        detective1="Tom",
        detective1_gender="boy",
        detective2="Mia",
        detective2_gender="girl",
        leader_trait="bold",
    ),
    StoryParams(
        setting="field",
        item="medal_box",
        clue="flour_paw",
        suspect="baker",
        cause="cat",
        detective1="Lucy",
        detective1_gender="girl",
        detective2="Max",
        detective2_gender="boy",
        leader_trait="quick-thinking",
    ),
]


ASP_RULES = r"""
fits_setting(I, S) :- item_allowed(I, S).
good_clue(C, Su, Ca) :- clue_points_suspect(C, Su), clue_points_cause(C, Ca).
can_move(Ca, I) :- cause_moves(Ca, I).
valid(S, I, C, Su, Ca) :- setting(S), item(I), clue(C), suspect(Su), cause(Ca),
                          fits_setting(I, S), good_clue(C, Su, Ca), can_move(Ca, I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for setting_id in sorted(item.settings):
            lines.append(asp.fact("item_allowed", item_id, setting_id))
        for cause_id in sorted(item.movable_by):
            lines.append(asp.fact("cause_moves", cause_id, item_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for suspect_id in sorted(clue.suspect_ids):
            lines.append(asp.fact("clue_points_suspect", clue_id, suspect_id))
        for cause_id in sorted(clue.cause_ids):
            lines.append(asp.fact("clue_points_cause", clue_id, cause_id))
    for suspect_id in SUSPECTS:
        lines.append(asp.fact("suspect", suspect_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: junior detectives make a wrong accusation, discover a twist, and learn a sad lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible detective setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item:
        if args.setting in SETTINGS and args.item in ITEMS:
            if not item_fits_setting(ITEMS[args.item], SETTINGS[args.setting]):
                raise StoryError(explain_rejection(args.setting, args.item, args.clue or "", args.suspect or "", args.cause or ""))
    if args.cause and args.item:
        if args.cause in CAUSES and args.item in ITEMS:
            if not cause_can_move_item(CAUSES[args.cause], ITEMS[args.item]):
                raise StoryError(explain_rejection(args.setting or "", args.item, args.clue or "", args.suspect or "", args.cause))
    if args.clue and args.suspect and args.cause:
        if args.clue in CLUES and args.suspect in SUSPECTS and args.cause in CAUSES:
            if not clue_points_to_pair(CLUES[args.clue], SUSPECTS[args.suspect], CAUSES[args.cause]):
                raise StoryError(explain_rejection(args.setting or "", args.item or "", args.clue, args.suspect, args.cause))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.clue is None or combo[2] == args.clue)
        and (args.suspect is None or combo[3] == args.suspect)
        and (args.cause is None or combo[4] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, clue_id, suspect_id, cause_id = rng.choice(combos)
    d1, d1g = _pick_name(rng)
    d2, d2g = _pick_name(rng, avoid=d1)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        clue=clue_id,
        suspect=suspect_id,
        cause=cause_id,
        detective1=d1,
        detective1_gender=d1g,
        detective2=d2,
        detective2_gender=d2g,
        leader_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting}.)")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item}.)")
    if params.clue not in CLUES:
        raise StoryError(f"(Invalid clue: {params.clue}.)")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Invalid suspect: {params.suspect}.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause}.)")
    if not item_fits_setting(ITEMS[params.item], SETTINGS[params.setting]):
        raise StoryError(explain_rejection(params.setting, params.item, params.clue, params.suspect, params.cause))
    if not cause_can_move_item(CAUSES[params.cause], ITEMS[params.item]):
        raise StoryError(explain_rejection(params.setting, params.item, params.clue, params.suspect, params.cause))
    if not clue_points_to_pair(CLUES[params.clue], SUSPECTS[params.suspect], CAUSES[params.cause]):
        raise StoryError(explain_rejection(params.setting, params.item, params.clue, params.suspect, params.cause))

    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        clue=CLUES[params.clue],
        suspect_cfg=SUSPECTS[params.suspect],
        cause=CAUSES[params.cause],
        detective1=params.detective1,
        detective1_gender=params.detective1_gender,
        detective2=params.detective2,
        detective2_gender=params.detective2_gender,
        leader_trait=params.leader_trait,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid detective setups:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "heck" not in sample.story.lower() or "morale" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story text missing required seed words.)")
        print("OK: smoke generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story:
            raise StoryError("(Random generation produced an empty story.)")
        print("OK: random generate() succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"RANDOM GENERATION FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, clue, suspect, cause) combos:\n")
        for setting_id, item_id, clue_id, suspect_id, cause_id in combos:
            print(f"  {setting_id:10} {item_id:10} {clue_id:12} {suspect_id:10} {cause_id}")
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
            header = f"### {p.detective1} & {p.detective2}: {p.item} at {p.setting} ({p.clue}, {p.suspect}, {p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
