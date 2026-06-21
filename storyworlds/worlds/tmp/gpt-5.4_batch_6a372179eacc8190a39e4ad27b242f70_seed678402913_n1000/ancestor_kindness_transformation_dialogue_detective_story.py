#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ancestor_kindness_transformation_dialogue_detective_story.py
=======================================================================================

A small standalone storyworld for a child-facing detective story about an
ancestor portrait, a missing keepsake, and a kind investigation that changes a
frightening misunderstanding into a warm family memory.

Premise
-------
A child notices that an old ancestor portrait looks stern because a small
keepsake has gone missing from its frame. The child decides to be a detective,
follows clues through the house, and solves the little mystery. The turning
point is not punishment but kindness: the detective understands *why* the
keepsake moved and fixes the problem gently. By the end, the ancestor image and
the room itself feel transformed.

World-model notes
-----------------
- Entities share one representation with physical meters and emotional memes.
- The story is not a frozen template: clue type, suspect, helper, and ending
  all come from simulated state.
- The reasonableness gate only allows culprit/keepsake/setting combinations
  where the culprit could plausibly move that keepsake and where the traced clue
  really supports the solution.
- The ASP twin mirrors the compatibility and outcome logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/ancestor_kindness_transformation_dialogue_detective_story.py
    python storyworlds/worlds/gpt-5.4/ancestor_kindness_transformation_dialogue_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/ancestor_kindness_transformation_dialogue_detective_story.py --culprit cat
    python storyworlds/worlds/gpt-5.4/ancestor_kindness_transformation_dialogue_detective_story.py --verify
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = False
    shiny: bool = False
    soft: bool = False
    fluttery: bool = False
    can_open_window: bool = False
    # two shared numeric dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    room: str
    portrait_spot: str
    hiding_spot: str
    mood: str
    has_window: bool = False
    animal_allowed: bool = True
    shiny_spot: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    attached_to: str
    clue_mark: str
    recovered_from: str
    portable: bool = True
    shiny: bool = False
    soft: bool = False
    fluttery: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    clue: str
    motive: str
    takes_shiny: bool = False
    takes_soft: bool = False
    takes_fluttery: bool = False
    needs_window: bool = False
    animal: bool = False
    childlike: bool = False
    kind_fix: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    dialogue_style: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_missing_changes_mood(world: World) -> list[str]:
    portrait = world.get("portrait")
    keepsake = world.get("keepsake")
    if keepsake.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_changes_mood",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    portrait.memes["stern"] += 1
    portrait.memes["mystery"] += 1
    for eid in ("detective", "helper"):
        if eid in world.entities:
            world.get(eid).memes["concern"] += 1
    return []


def _r_clue_builds_theory(world: World) -> list[str]:
    if world.get("trail").meters["found"] < THRESHOLD:
        return []
    sig = ("clue_builds_theory",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("detective").memes["curiosity"] += 1
    world.get("detective").memes["confidence"] += 1
    return []


def _r_kind_return_transforms(world: World) -> list[str]:
    keepsake = world.get("keepsake")
    portrait = world.get("portrait")
    room = world.get("room")
    if keepsake.meters["returned"] < THRESHOLD:
        return []
    sig = ("kind_return_transforms",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    portrait.memes["stern"] = 0.0
    portrait.memes["warmth"] += 1
    portrait.memes["remembered"] += 1
    room.memes["cozy"] += 1
    room.memes["spooky"] = 0.0
    for eid in ("detective", "helper"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["kindness"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_changes_mood", tag="emotional", apply=_r_missing_changes_mood),
    Rule(name="clue_builds_theory", tag="emotional", apply=_r_clue_builds_theory),
    Rule(name="kind_return_transforms", tag="emotional", apply=_r_kind_return_transforms),
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
                produced.extend(sents)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        current_count = len(world.fired)
        # if any rule fired this loop, treat as changed
        changed = changed or (current_count > 0 and current_count != getattr(propagate, "_last_count", -1))
        propagate._last_count = current_count  # type: ignore[attr-defined]
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def culprit_matches(setting: Setting, keepsake: Keepsake, culprit: Culprit) -> bool:
    if culprit.needs_window and not setting.has_window:
        return False
    if culprit.animal and not setting.animal_allowed:
        return False
    if culprit.takes_shiny and keepsake.shiny:
        return True
    if culprit.takes_soft and keepsake.soft:
        return True
    if culprit.takes_fluttery and keepsake.fluttery:
        return True
    if culprit.childlike:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for kid, keepsake in KEEPSAKES.items():
            for cid, culprit in CULPRITS.items():
                if culprit_matches(setting, keepsake, culprit):
                    combos.append((sid, kid, cid))
    return combos


def predict_case(world: World, culprit: Culprit, keepsake: Keepsake) -> dict:
    sim = world.copy()
    _take_keepsake(sim, culprit, keepsake, narrate=False)
    return {
        "missing": sim.get("keepsake").meters["missing"] >= THRESHOLD,
        "trail_found": sim.get("trail").meters["found"] >= THRESHOLD,
    }


def _take_keepsake(world: World, culprit: Culprit, keepsake: Keepsake, narrate: bool = True) -> None:
    item = world.get("keepsake")
    item.meters["missing"] += 1
    item.meters["moved"] += 1
    world.get("trail").meters["found"] += 1
    world.get("culprit_mark").meters["present"] += 1
    world.facts["culprit_id"] = culprit.id
    propagate(world, narrate=narrate)


def introduce(world: World, detective: Entity, helper: Entity, ancestor: Entity, keepsake: Keepsake) -> None:
    room = world.setting.room
    world.say(
        f"On a soft afternoon, {detective.id} and {helper.label_word} stepped into {room}, "
        f"where the portrait of their ancestor hung {world.setting.portrait_spot}."
    )
    world.say(
        f"The old picture showed {ancestor.label}, and on the frame there should have been "
        f"{keepsake.phrase}. Instead, the frame looked bare on one side."
    )
    world.say(
        f'"That is strange," {detective.id} whispered. "{ancestor.label} looks almost cross."'
    )


def family_memory(world: World, helper: Entity, ancestor: Entity, keepsake: Keepsake) -> None:
    helper.memes["memory"] += 1
    world.say(
        f'{helper.label_word.capitalize()} smiled a little and said, '
        f'"Our ancestor {ancestor.label} was remembered for kindness. '
        f'{keepsake.label.capitalize()} belonged there because it reminded everyone of that."'
    )
    world.say(
        '"Then this is not just a missing thing," the child said. "It is a real case."'
    )


def notice_mystery(world: World, detective: Entity, culprit: Culprit, keepsake: Keepsake) -> None:
    detective.memes["detective"] += 1
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} put on a serious detective face and looked close at the frame."
    )
    world.say(
        f'There was {culprit.clue} near the place where {keepsake.attached_to} had been.'
    )
    world.say(
        f'"A clue," {detective.id} said. "Someone moved {keepsake.label}, and I am going to find out who."'
    )


def helper_warns_gently(world: World, helper: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f'"Remember," {helper.label_word} said, "a detective should be careful with people and gentle with guesses."'
    )


def follow_trail(world: World, detective: Entity, culprit: Culprit, keepsake: Keepsake) -> None:
    detective.memes["confidence"] += 1
    world.say(
        f"So {detective.id} followed the clue through the house, past the stairs and toward "
        f"{world.setting.hiding_spot}."
    )
    world.say(
        f"There, just where the clue seemed to end, lay {keepsake.recovered_from}."
    )
    if culprit.id == "cat":
        world.say(
            f'The family cat blinked at the child and flicked its tail. "{keepsake.label.capitalize()} is here!" '
            f'{detective.id} gasped.'
        )
    elif culprit.id == "wind":
        world.say(
            f'"The window must have puffed it away," {detective.id} said.'
        )
    else:
        world.say(
            f'"I think I know who borrowed it," {detective.id} said softly.'
        )


def reveal(world: World, detective: Entity, helper: Entity, culprit: Culprit, keepsake: Keepsake) -> None:
    if culprit.id == "cat":
        world.say(
            f'"It was not a thief after all," {detective.id} said. "The cat chased the {keepsake.label} because '
            f'it looked {culprit.motive}."'
        )
        world.say(
            f'{helper.label_word.capitalize()} nodded. "Then we will solve the case kindly."'
        )
    elif culprit.id == "wind":
        world.say(
            f'"No bad person did it," {detective.id} said. "The open window lifted the {keepsake.label} and carried '
            f'it away."'
        )
        world.say(
            f'"A puff of wind can make a mystery," {helper.label_word} agreed.'
        )
    else:
        world.say(
            f'"It was Cousin Pip," {detective.id} said, "but not in a mean way. Pip wanted {culprit.motive}."'
        )
        world.say(
            f'{helper.label_word.capitalize()} answered, "Then the kind answer is to help Pip ask before borrowing."'
        )


def kindness_fix(world: World, detective: Entity, helper: Entity, culprit: Culprit, keepsake: Keepsake) -> None:
    keepsake_ent = world.get("keepsake")
    keepsake_ent.meters["returned"] += 1
    keepsake_ent.meters["missing"] = 0.0
    world.get("portrait").meters["mended"] += 1
    propagate(world, narrate=False)
    if culprit.id == "cat":
        world.say(
            f"{detective.id} picked up {keepsake.label} carefully, then set a soft ball beside the cat so it would "
            f"have something better to chase."
        )
    elif culprit.id == "wind":
        world.say(
            f"{detective.id} lifted {keepsake.label} gently, and {helper.label_word} latched the window before "
            f"another puff could whisk it away."
        )
    else:
        world.say(
            f"{detective.id} gave Cousin Pip a kind smile and said, "
            f'"Next time, you can ask. We would have shown it to you."'
        )
    world.say(culprit.kind_fix)
    world.say(
        f"Together they fastened {keepsake.label} back onto the frame where it belonged."
    )


def transformed_ending(world: World, detective: Entity, helper: Entity, ancestor: Entity) -> None:
    room = world.setting.room
    world.say(
        f"At once, {room} did not seem so {world.setting.mood} anymore."
    )
    world.say(
        f"The ancestor in the portrait no longer looked stern to {detective.id}. "
        f"Now the face seemed calm, almost smiling, as if kindness had solved the mystery better than scolding."
    )
    world.say(
        f'"Case closed," {detective.id} said.'
    )
    world.say(
        f'"And lesson learned," {helper.label_word} replied. "A family story can change when we look at it with a gentle heart."'
    )


def tell(
    setting: Setting,
    keepsake: Keepsake,
    culprit: Culprit,
    helper_cfg: Helper,
    detective_name: str = "Mina",
    detective_type: str = "girl",
    ancestor_name: str = "Aunt Elinor",
) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        role="detective",
        label=detective_name,
        attrs={"style": "careful"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.label,
        attrs={"dialogue_style": helper_cfg.dialogue_style},
    ))
    ancestor = world.add(Entity(
        id="ancestor",
        kind="character",
        type="woman" if ancestor_name.startswith(("Aunt", "Grandma", "Lady")) else "man",
        role="ancestor",
        label=ancestor_name,
        attrs={"known_for": "kindness"},
    ))
    portrait = world.add(Entity(
        id="portrait",
        kind="thing",
        type="portrait",
        label="the portrait",
        phrase=f"the portrait of {ancestor_name}",
        attrs={"ancestor": ancestor_name},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=setting.room,
        phrase=setting.room,
    ))
    world.add(Entity(
        id="keepsake",
        kind="thing",
        type="keepsake",
        label=keepsake.label,
        phrase=keepsake.phrase,
        portable=keepsake.portable,
        shiny=keepsake.shiny,
        soft=keepsake.soft,
        fluttery=keepsake.fluttery,
        tags=set(keepsake.tags),
    ))
    world.add(Entity(
        id="trail",
        kind="thing",
        type="clue",
        label="the trail",
        phrase="the trail of clues",
    ))
    world.add(Entity(
        id="culprit_mark",
        kind="thing",
        type="mark",
        label="the clue mark",
        phrase=culprit.clue,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        ancestor=ancestor,
        portrait=portrait,
        room=room,
        keepsake_cfg=keepsake,
        culprit=culprit,
        helper_cfg=helper_cfg,
    )

    introduce(world, detective, helper, ancestor, keepsake)
    family_memory(world, helper, ancestor, keepsake)

    world.para()
    _take_keepsake(world, culprit, keepsake, narrate=False)
    notice_mystery(world, detective, culprit, keepsake)
    helper_warns_gently(world, helper)

    world.para()
    follow_trail(world, detective, culprit, keepsake)
    reveal(world, detective, helper, culprit, keepsake)

    world.para()
    kindness_fix(world, detective, helper, culprit, keepsake)
    transformed_ending(world, detective, helper, ancestor)

    world.facts.update(
        solved=True,
        transformed=world.get("portrait").memes["warmth"] >= THRESHOLD,
        kind_end=world.get("detective").memes["kindness"] >= THRESHOLD,
        clue=culprit.clue,
    )
    return world


SETTINGS = {
    "hall": Setting(
        id="hall",
        room="the front hall",
        portrait_spot="above a narrow wooden table",
        hiding_spot="the umbrella stand by the door",
        mood="shadowy",
        has_window=False,
        animal_allowed=True,
        tags={"house", "hall"},
    ),
    "parlor": Setting(
        id="parlor",
        room="the parlor",
        portrait_spot="beside the family clock",
        hiding_spot="the curtain hem near the window seat",
        mood="hushed",
        has_window=True,
        animal_allowed=True,
        shiny_spot="the brass latch",
        tags={"parlor", "window"},
    ),
    "attic": Setting(
        id="attic",
        room="the attic room",
        portrait_spot="under the sloping roof",
        hiding_spot="an old hatbox near the little round window",
        mood="dusty",
        has_window=True,
        animal_allowed=False,
        shiny_spot="the little round window",
        tags={"attic", "window"},
    ),
}

KEEPSAKES = {
    "ribbon": Keepsake(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon tied to one corner",
        attached_to="the blue ribbon",
        clue_mark="a tiny line of dust and one loose blue thread",
        recovered_from="the blue ribbon tucked beside the skirting board",
        portable=True,
        shiny=False,
        soft=True,
        fluttery=True,
        tags={"ribbon", "cloth"},
    ),
    "flower": Keepsake(
        id="flower",
        label="pressed flower",
        phrase="a pressed flower tucked inside a small glass locket on the frame",
        attached_to="the pressed flower",
        clue_mark="a papery fleck and a little bent hook",
        recovered_from="the pressed flower lying flat under a chair leg",
        portable=True,
        shiny=False,
        soft=False,
        fluttery=True,
        tags={"flower", "memory"},
    ),
    "charm": Keepsake(
        id="charm",
        label="silver key charm",
        phrase="a silver key charm hanging from a red string",
        attached_to="the silver key charm",
        clue_mark="a bright scrape and a twisted bit of string",
        recovered_from="the silver key charm glinting in the corner",
        portable=True,
        shiny=True,
        soft=False,
        fluttery=False,
        tags={"silver", "key"},
    ),
}

CULPRITS = {
    "cat": Culprit(
        id="cat",
        label="the cat",
        phrase="the family cat",
        clue="a soft paw mark in the dust",
        motive="twitchy and fun to bat",
        takes_shiny=False,
        takes_soft=True,
        takes_fluttery=True,
        needs_window=False,
        animal=True,
        childlike=False,
        kind_fix="That was kinder than shooing or shouting, and it made the cat purr instead of dart away.",
        tags={"cat", "pet"},
    ),
    "wind": Culprit(
        id="wind",
        label="the wind",
        phrase="a cool puff from the window",
        clue="a thin stream of dust pointing toward the window",
        motive="light enough to lift",
        takes_shiny=False,
        takes_soft=False,
        takes_fluttery=True,
        needs_window=True,
        animal=False,
        childlike=False,
        kind_fix="Closing the latch gently felt better than blaming the house for creaking and sighing.",
        tags={"wind", "window"},
    ),
    "cousin": Culprit(
        id="cousin",
        label="Cousin Pip",
        phrase="little Cousin Pip",
        clue="one small shoe print and a crayon tucked on the table",
        motive="to look closely at the brave old key and hear the story again",
        takes_shiny=False,
        takes_soft=False,
        takes_fluttery=False,
        needs_window=False,
        animal=False,
        childlike=True,
        kind_fix="Pip nodded, and the mystery ended as a family talk instead of a quarrel.",
        tags={"borrow", "family"},
    ),
}

HELPERS = {
    "grandmother": Helper(
        id="grandmother",
        label="Grandma",
        type="grandmother",
        dialogue_style="calm",
        tags={"grandma", "family"},
    ),
    "grandfather": Helper(
        id="grandfather",
        label="Grandpa",
        type="grandfather",
        dialogue_style="warm",
        tags={"grandpa", "family"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ruby", "Ivy"]
BOY_NAMES = ["Owen", "Jude", "Theo", "Milo", "Finn", "Leo"]
ANCESTOR_NAMES = ["Aunt Elinor", "Uncle Rowan", "Grandma Pearl", "Grandpa Alder"]


@dataclass
class StoryParams:
    setting: str
    keepsake: str
    culprit: str
    helper: str
    detective_name: str
    detective_type: str
    ancestor_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ancestor": [
        (
            "What is an ancestor?",
            "An ancestor is a person in your family who lived before you, like a grandparent from long ago or someone even older in the family line."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues, asks careful questions, and tries to solve a mystery by noticing what happened."
        )
    ],
    "kindness": [
        (
            "Why is kindness helpful when solving a problem?",
            "Kindness helps people stay calm and tell the truth. It can turn a problem into something that can be fixed together."
        )
    ],
    "cat": [
        (
            "Why do cats bat at ribbons or strings?",
            "Cats like things that twitch and dangle because those movements catch their eyes and make them want to pounce."
        )
    ],
    "wind": [
        (
            "How can wind move light things indoors?",
            "If a window is open, a puff of air can slide under a light object and push or lift it to a new place."
        )
    ],
    "borrow": [
        (
            "What should you do before borrowing something that belongs to someone else?",
            "You should ask first. Asking shows respect and helps everyone know where the thing is."
        )
    ],
    "portrait": [
        (
            "What is a portrait?",
            "A portrait is a picture of a person, often painted or drawn to help people remember what that person looked like."
        )
    ],
    "memory": [
        (
            "Why do families keep old keepsakes?",
            "Families keep old keepsakes because small objects can help them remember stories, people, and important feelings from long ago."
        )
    ],
}
KNOWLEDGE_ORDER = ["ancestor", "detective", "portrait", "memory", "kindness", "cat", "wind", "borrow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    keepsake = f["keepsake_cfg"]
    ancestor = f["ancestor"]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the word "ancestor" and ends with kindness.',
        f"Tell a gentle mystery where {detective.id} notices a missing {keepsake.label} on an ancestor portrait, follows clues, and solves the case with help from {f['helper'].label_word}.",
        f"Write a dialogue-rich detective story where what first seems spooky turns warm and changed once the child understands why {culprit.label} moved the keepsake from {ancestor.label}'s portrait.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    ancestor = f["ancestor"]
    keepsake = f["keepsake_cfg"]
    culprit = f["culprit"]
    setting = world.setting
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, and {helper.label_word}, who helps with a family mystery about their ancestor {ancestor.label}. The missing object is {keepsake.label} from the portrait frame."
        ),
        (
            "What was the mystery?",
            f"The mystery was that {keepsake.label} had gone missing from the ancestor portrait in {setting.room}. Because the frame looked bare and there was a clue nearby, {detective.id} knew something in the room had changed."
        ),
        (
            "What clue helped solve the case?",
            f"The child found {culprit.clue}. That clue pointed toward the place where {keepsake.label} had ended up, so it helped the detective make a careful guess instead of a wild one."
        ),
        (
            "How was kindness part of the solution?",
            f"Kindness mattered because nobody yelled or blamed first. {detective.id} and {helper.label_word} tried to understand why the keepsake had moved, and then they fixed the problem gently."
        ),
    ]
    if culprit.id == "cat":
        qa.append(
            (
                "Why did the cat take the keepsake?",
                f"The cat moved it because {keepsake.label} looked twitchy and fun to bat. That made it a pet problem, not a mean one."
            )
        )
    elif culprit.id == "wind":
        qa.append(
            (
                "Why did the wind move the keepsake?",
                f"The keepsake was light enough for a puff from the window to carry it away. Once they noticed the dusty trail toward the window, the mystery stopped feeling spooky and started feeling understandable."
            )
        )
    else:
        qa.append(
            (
                "Why did Cousin Pip borrow the keepsake?",
                f"Cousin Pip wanted to look closely and hear the family story again. The solution was to teach asking first, not to turn the mistake into a quarrel."
            )
        )
    qa.append(
        (
            "What changed at the end of the story?",
            f"At the end, the keepsake was back on the frame, and the room no longer felt so {setting.mood}. The portrait seemed warm instead of stern because the family had repaired both the object and the feeling around it."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ancestor", "detective", "portrait", "kindness"} | set(world.facts["keepsake_cfg"].tags) | set(world.facts["culprit"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.portable:
            flags.append("portable")
        if ent.shiny:
            flags.append("shiny")
        if ent.soft:
            flags.append("soft")
        if ent.fluttery:
            flags.append("fluttery")
        if ent.can_open_window:
            flags.append("can_open_window")
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="hall",
        keepsake="ribbon",
        culprit="cat",
        helper="grandmother",
        detective_name="Mina",
        detective_type="girl",
        ancestor_name="Aunt Elinor",
    ),
    StoryParams(
        setting="parlor",
        keepsake="flower",
        culprit="wind",
        helper="grandfather",
        detective_name="Owen",
        detective_type="boy",
        ancestor_name="Grandma Pearl",
    ),
    StoryParams(
        setting="attic",
        keepsake="charm",
        culprit="cousin",
        helper="grandmother",
        detective_name="Nora",
        detective_type="girl",
        ancestor_name="Grandpa Alder",
    ),
    StoryParams(
        setting="parlor",
        keepsake="ribbon",
        culprit="cousin",
        helper="grandfather",
        detective_name="Theo",
        detective_type="boy",
        ancestor_name="Uncle Rowan",
    ),
]


def explain_rejection(setting: Setting, keepsake: Keepsake, culprit: Culprit) -> str:
    if culprit.needs_window and not setting.has_window:
        return (
            f"(No story: {culprit.label} needs an open window, but {setting.room} has no suitable window in this world. "
            f"Pick the parlor or attic for a wind case.)"
        )
    if culprit.animal and not setting.animal_allowed:
        return (
            f"(No story: animals do not roam freely through {setting.room} in this world, so {culprit.label} would not be a fair culprit there.)"
        )
    return (
        f"(No story: {culprit.label} would not plausibly move {keepsake.label}. "
        f"Choose a culprit whose kind of clue matches the keepsake.)"
    )


ASP_RULES = r"""
% registry facts come from asp_facts()

match(C, K) :- takes_shiny(C), shiny(K).
match(C, K) :- takes_soft(C), soft(K).
match(C, K) :- takes_fluttery(C), fluttery(K).
match(C, K) :- childlike(C).

allowed_place(S, C) :- setting(S), culprit(C), not needs_window(C), not animal(C).
allowed_place(S, C) :- setting(S), needs_window(C), has_window(S), not animal(C).
allowed_place(S, C) :- setting(S), animal(C), animal_allowed(S), not needs_window(C).
allowed_place(S, C) :- setting(S), animal(C), animal_allowed(S), needs_window(C), has_window(S).

valid(S, K, C) :- setting(S), keepsake(K), culprit(C), allowed_place(S, C), match(C, K).

solved(S, K, C) :- valid(S, K, C).
transformed(S, K, C) :- solved(S, K, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.has_window:
            lines.append(asp.fact("has_window", sid))
        if setting.animal_allowed:
            lines.append(asp.fact("animal_allowed", sid))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        if keepsake.shiny:
            lines.append(asp.fact("shiny", kid))
        if keepsake.soft:
            lines.append(asp.fact("soft", kid))
        if keepsake.fluttery:
            lines.append(asp.fact("fluttery", kid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        if culprit.takes_shiny:
            lines.append(asp.fact("takes_shiny", cid))
        if culprit.takes_soft:
            lines.append(asp.fact("takes_soft", cid))
        if culprit.takes_fluttery:
            lines.append(asp.fact("takes_fluttery", cid))
        if culprit.needs_window:
            lines.append(asp.fact("needs_window", cid))
        if culprit.animal:
            lines.append(asp.fact("animal", cid))
        if culprit.childlike:
            lines.append(asp.fact("childlike", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story_qa or not sample.world_qa:
            raise StoryError("generated sample missing QA")
        print("OK: random generation smoke test succeeded.")
    except Exception as err:  # pragma: no cover - explicit verification path
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective solves a family mystery about an ancestor portrait."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ancestor-name")
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
    if args.setting and args.keepsake and args.culprit:
        setting = SETTINGS[args.setting]
        keepsake = KEEPSAKES[args.keepsake]
        culprit = CULPRITS[args.culprit]
        if not culprit_matches(setting, keepsake, culprit):
            raise StoryError(explain_rejection(setting, keepsake, culprit))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, keepsake_id, culprit_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    ancestor_name = args.ancestor_name or rng.choice(ANCESTOR_NAMES)
    return StoryParams(
        setting=setting_id,
        keepsake=keepsake_id,
        culprit=culprit_id,
        helper=helper_id,
        detective_name=name,
        detective_type=gender,
        ancestor_name=ancestor_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Invalid keepsake: {params.keepsake})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Invalid culprit: {params.culprit})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")

    setting = SETTINGS[params.setting]
    keepsake = KEEPSAKES[params.keepsake]
    culprit = CULPRITS[params.culprit]
    if not culprit_matches(setting, keepsake, culprit):
        raise StoryError(explain_rejection(setting, keepsake, culprit))

    world = tell(
        setting=setting,
        keepsake=keepsake,
        culprit=culprit,
        helper_cfg=HELPERS[params.helper],
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        ancestor_name=params.ancestor_name,
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
        print(asp_program("", "#show valid/3.\n#show solved/3.\n#show transformed/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, keepsake, culprit) combos:\n")
        for setting_id, keepsake_id, culprit_id in combos:
            print(f"  {setting_id:8} {keepsake_id:8} {culprit_id}")
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
            header = f"### {p.detective_name}: {p.keepsake} in {p.setting} ({p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
