#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/oriental_suspense_curiosity_lesson_learned_detective_story.py
=========================================================================================

A standalone storyworld about a small child-scale detective mystery: a keepsake
goes missing in a room with an oriental rug, suspicion rises, clues matter, and
the children learn to search carefully before blaming anyone.

Run it
------
python storyworlds/worlds/gpt-5.4/oriental_suspense_curiosity_lesson_learned_detective_story.py
python storyworlds/worlds/gpt-5.4/oriental_suspense_curiosity_lesson_learned_detective_story.py --item bell_charm --hide inside_slipper
python storyworlds/worlds/gpt-5.4/oriental_suspense_curiosity_lesson_learned_detective_story.py --method check_books
python storyworlds/worlds/gpt-5.4/oriental_suspense_curiosity_lesson_learned_detective_story.py --all --qa
python storyworlds/worlds/gpt-5.4/oriental_suspense_curiosity_lesson_learned_detective_story.py --verify
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
CAREFUL_TRAITS = {"patient", "careful", "observant", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    room: str
    oriental_feature: str
    weather_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    owner_line: str
    tiny: bool = True
    noisy: bool = False
    flat: bool = False
    rolling: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    place_line: str
    allows_tiny: bool = True
    needs_noisy: bool = False
    needs_flat: bool = False
    needs_rolling: bool = False
    visible_low: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SearchMethod:
    id: str
    label: str
    sense: int
    action_line: str
    success_line: str
    fail_line: str
    checks_noisy: bool = False
    checks_low: bool = False
    checks_books: bool = False
    checks_slipper: bool = False
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


def _r_missing_stirs_feelings(world: World) -> list[str]:
    if not world.facts.get("item_missing"):
        return []
    seeker = world.get("seeker")
    sig = ("missing_feelings",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["curiosity"] += 1
    seeker.memes["worry"] += 1
    return ["__missing__"]


def _r_accusation_hurts(world: World) -> list[str]:
    if not world.facts.get("accusation_spoken"):
        return []
    helper = world.get("helper")
    sig = ("accusation_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["hurt"] += 1
    helper.memes["trust_drop"] += 1
    return ["__accusation__"]


def _r_found_brings_relief(world: World) -> list[str]:
    if not world.facts.get("item_found"):
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for role in ("seeker", "helper", "adult"):
        ent = world.get(role)
        ent.memes["relief"] += 1
        ent.memes["calm"] += 1
    world.get("seeker").memes["worry"] = 0.0
    return ["__found__"]


CAUSAL_RULES = [
    Rule(name="missing_stirs_feelings", tag="emotion", apply=_r_missing_stirs_feelings),
    Rule(name="accusation_hurts", tag="social", apply=_r_accusation_hurts),
    Rule(name="found_brings_relief", tag="emotion", apply=_r_found_brings_relief),
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


def hide_is_plausible(item: MissingItem, hiding: HidingPlace) -> bool:
    if not item.tiny and hiding.allows_tiny:
        return False
    if hiding.needs_noisy and not item.noisy:
        return False
    if hiding.needs_flat and not item.flat:
        return False
    if hiding.needs_rolling and not item.rolling:
        return False
    return True


def sensible_methods() -> list[SearchMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_fits(hiding: HidingPlace, method: SearchMethod) -> bool:
    if hiding.id == "between_book_pages":
        return method.checks_books
    if hiding.id == "inside_slipper":
        return method.checks_slipper or method.checks_noisy
    if hiding.id in {"under_cabinet", "rug_fold"}:
        return method.checks_low
    return False


def prediction(world: World, item: MissingItem, hiding: HidingPlace, method: SearchMethod) -> dict:
    sim = world.copy()
    found = method_fits(hiding, method) and hide_is_plausible(item, hiding)
    sim.facts["item_found"] = found
    if found:
        propagate(sim, narrate=False)
    return {"found": found}


def would_accuse(relation: str, trait: str, trust: int) -> bool:
    careful = trait in CAREFUL_TRAITS
    if relation == "siblings":
        return not careful and trust <= 4
    return not careful and trust <= 3


def explain_rejection(item: MissingItem, hiding: HidingPlace) -> str:
    if hiding.needs_noisy and not item.noisy:
        return (
            f"(No story: {item.label} makes no little sound, so it would not make sense "
            f"for it to vanish into {hiding.phrase} in this world.)"
        )
    if hiding.needs_flat and not item.flat:
        return (
            f"(No story: {item.label} is not flat enough to hide {hiding.phrase}. "
            f"Pick a flatter missing thing.)"
        )
    if hiding.needs_rolling and not item.rolling:
        return (
            f"(No story: {item.label} would not roll {hiding.phrase}. "
            f"Pick a rounder missing thing.)"
        )
    return "(No story: that item and hiding place do not make a believable mystery.)"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id, item in ITEMS.items():
            for hide_id, hiding in HIDING_PLACES.items():
                if hide_is_plausible(item, hiding):
                    combos.append((setting_id, item_id, hide_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if would_accuse(params.relation, params.trait, params.trust):
        if method_fits(HIDING_PLACES[params.hide], METHODS[params.method]):
            return "apology_found"
        return "adult_hint"
    if method_fits(HIDING_PLACES[params.hide], METHODS[params.method]):
        return "careful_found"
    return "adult_hint"


def introduce(world: World, seeker: Entity, helper: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"Rain tapped softly at the windows while {seeker.id}, {helper.id}, and "
        f"{adult.label_word} sat in {setting.room}. An {setting.oriental_feature} "
        f"lay across the floor and made the whole room feel like a place where clues might hide."
    )
    world.say(setting.weather_line)


def treasure_setup(world: World, seeker: Entity, item: MissingItem) -> None:
    seeker.memes["love"] += 1
    world.say(
        f"{seeker.id} had been carrying {item.phrase}. {item.owner_line}"
    )


def disappearance(world: World, seeker: Entity, item: MissingItem) -> None:
    world.facts["item_missing"] = True
    propagate(world, narrate=False)
    world.say(
        f"But when {seeker.id} reached for {item.label} again, it was gone."
    )
    world.say(
        f"{seeker.id} stared at the empty place in {seeker.pronoun('possessive')} hand. "
        f"The little mystery made {seeker.pronoun('object')} curious and a bit shaky all at once."
    )


def detective_vow(world: World, seeker: Entity, helper: Entity) -> None:
    seeker.memes["resolve"] += 1
    helper.memes["resolve"] += 1
    world.say(
        f'"Do not move," {seeker.id} whispered. "This is a detective case."'
    )
    world.say(
        f"{helper.id} nodded and crouched beside {seeker.pronoun('object')}, ready to help."
    )


def accuse_or_pause(world: World, seeker: Entity, helper: Entity, adult: Entity) -> None:
    world.facts["accusation_spoken"] = True
    propagate(world, narrate=False)
    world.say(
        f'Then a worried idea burst out. "{helper.id}, did you take it?" {seeker.id} asked.'
    )
    world.say(
        f"{helper.id}'s eyes widened. {adult.label_word.capitalize()} raised a calm finger and said, "
        f'"Real detectives do not blame first. They look for clues first."'
    )


def careful_rule(world: World, seeker: Entity, adult: Entity) -> None:
    world.say(
        f'{adult.label_word.capitalize()} spoke so softly that the room grew still. '
        f'"Use your eyes, your ears, and your memory, {seeker.id}. Curious minds work best when they are calm."'
    )


def method_attempt(world: World, seeker: Entity, helper: Entity, item: MissingItem,
                   hiding: HidingPlace, method: SearchMethod) -> bool:
    pred = prediction(world, item, hiding, method)
    world.facts["predicted_found"] = pred["found"]
    world.say(method.action_line.format(seeker=seeker.id, helper=helper.id))
    if pred["found"]:
        world.facts["item_found"] = True
        world.facts["found_by"] = method.id
        propagate(world, narrate=False)
        world.say(method.success_line.format(item=item.label, place=hiding.phrase))
        return True
    world.say(method.fail_line.format(item=item.label))
    return False


def adult_hint(world: World, adult: Entity, seeker: Entity, helper: Entity,
               hiding: HidingPlace, item: MissingItem) -> None:
    world.say(
        f'{adult.label_word.capitalize()} looked around once and asked, '
        f'"Where was it last safe?"'
    )
    if hiding.id == "between_book_pages":
        hint = "The answer sent their eyes to the stack of picture books."
    elif hiding.id == "inside_slipper":
        hint = "That made them all glance toward the row of slippers by the door."
    elif hiding.id == "under_cabinet":
        hint = "That made them kneel by the low cabinet where shadows gathered."
    else:
        hint = "That made them look closely at the edge of the oriental rug."
    world.say(hint)
    world.facts["item_found"] = True
    world.facts["found_by"] = "adult_hint"
    propagate(world, narrate=False)
    world.say(
        f"In another breath they found {item.phrase} {hiding.phrase}."
    )


def reunion(world: World, seeker: Entity, helper: Entity, item: MissingItem, hiding: HidingPlace) -> None:
    seeker.meters["holding_item"] += 1
    world.say(
        f"{seeker.id} picked up {item.label} from {hiding.phrase} and let out the long breath "
        f"{seeker.pronoun()} had been keeping inside."
    )
    if hiding.id == "rug_fold":
        world.say("A tiny wrinkle in the rug had held the clue the whole time.")
    elif hiding.id == "under_cabinet":
        world.say("The dark space under the cabinet had looked frightening, but the mystery there was only small and dusty.")
    elif hiding.id == "inside_slipper":
        world.say("The slipper gave one last tiny bump, as if the room itself had giggled at the answer.")
    else:
        world.say("The pages opened like a little secret door, and the mystery was over.")


def apology_and_lesson(world: World, seeker: Entity, helper: Entity, adult: Entity,
                       item: MissingItem, accused: bool) -> None:
    seeker.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    if accused:
        seeker.memes["shame"] += 1
        seeker.memes["trust_repair"] += 1
        helper.memes["trust_repair"] += 1
        world.say(
            f'"I am sorry I blamed you," {seeker.id} said to {helper.id}. '
            f'"The clue was hiding, not you."'
        )
        world.say(
            f"{helper.id} nodded and squeezed {seeker.pronoun('possessive')} hand. "
            f'"Next time we can be detectives together."'
        )
    world.say(
        f'{adult.label_word.capitalize()} smiled. "That is the lesson," {adult.pronoun()} said. '
        f'"Curiosity is good, but it must walk beside kindness. A fast guess can hurt faster than a lost {item.label}."'
    )


def closing_image(world: World, seeker: Entity, helper: Entity, setting: Setting, item: MissingItem) -> None:
    world.say(
        f"Soon the rain sounded gentler. {seeker.id} placed {item.label} safely on the table, "
        f"and {helper.id} sat beside {seeker.pronoun('object')} on the edge of the oriental room."
    )
    world.say(
        "The mystery had ended not with a shout, but with two quiet children, one found clue, and a wiser way to ask questions."
    )


def tell(setting: Setting, item: MissingItem, hiding: HidingPlace, method: SearchMethod,
         seeker_name: str = "Mina", seeker_gender: str = "girl",
         helper_name: str = "Jun", helper_gender: str = "boy",
         adult_type: str = "grandmother", trait: str = "patient",
         relation: str = "siblings", trust: int = 7) -> World:
    world = World(setting)
    seeker = world.add(Entity(
        id="seeker",
        kind="character",
        type=seeker_gender,
        label=seeker_name,
        role="seeker",
        traits=[trait],
        attrs={"name": seeker_name, "relation": relation},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        attrs={"name": helper_name, "relation": relation},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label="the elder",
        role="adult",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=setting.room,
        tags=set(setting.tags),
    ))

    seeker.attrs["display"] = seeker_name
    helper.attrs["display"] = helper_name
    adult.attrs["display"] = adult.label_word.capitalize()
    seeker.memes["trust"] = float(trust)
    helper.memes["trust"] = float(trust)

    introduce(world, seeker, helper, adult, setting)
    treasure_setup(world, seeker, item)

    world.para()
    disappearance(world, seeker, item)
    detective_vow(world, seeker, helper)

    accused = would_accuse(relation, trait, trust)
    world.facts["accused"] = accused
    if accused:
        accuse_or_pause(world, seeker, helper, adult)
    else:
        careful_rule(world, seeker, adult)

    world.para()
    found = method_attempt(world, seeker, helper, item, hiding, method)
    if not found:
        adult_hint(world, adult, seeker, helper, hiding, item)

    world.para()
    reunion(world, seeker, helper, item, hiding)
    apology_and_lesson(world, seeker, helper, adult, item, accused=accused)
    closing_image(world, seeker, helper, setting, item)

    world.facts.update(
        seeker=seeker,
        helper=helper,
        adult=adult,
        room=room,
        setting=setting,
        item_cfg=item,
        hiding_cfg=hiding,
        method_cfg=method,
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            item=item.id,
            hide=hiding.id,
            method=method.id,
            seeker_name=seeker_name,
            seeker_gender=seeker_gender,
            helper_name=helper_name,
            helper_gender=helper_gender,
            adult=adult_type,
            trait=trait,
            relation=relation,
            trust=trust,
            seed=None,
        )),
        item_found=world.facts.get("item_found", False),
    )
    return world


SETTINGS = {
    "tea_room": Setting(
        id="tea_room",
        room="grandma's tea room",
        oriental_feature="oriental rug with deep blue flowers",
        weather_line="Steam curled from a teapot, and the room felt warm enough for secrets.",
        tags={"oriental", "room"},
    ),
    "music_room": Setting(
        id="music_room",
        room="the music room",
        oriental_feature="oriental runner beneath the piano bench",
        weather_line="The last note from the piano had faded, but suspense still seemed to hum in the corners.",
        tags={"oriental", "music"},
    ),
    "study": Setting(
        id="study",
        room="grandpa's study",
        oriental_feature="oriental carpet under a low cabinet",
        weather_line="Books lined the walls, and every shelf looked as if it might be keeping a clue.",
        tags={"oriental", "books"},
    ),
}

ITEMS = {
    "bell_charm": MissingItem(
        id="bell_charm",
        label="the tiny bell charm",
        phrase="a tiny bell charm",
        owner_line="It gave the softest jingle whenever it moved, and that made it feel lucky.",
        tiny=True,
        noisy=True,
        flat=False,
        rolling=False,
        tags={"bell", "sound"},
    ),
    "jade_bead": MissingItem(
        id="jade_bead",
        label="the jade bead",
        phrase="a polished jade bead",
        owner_line="It was smooth and cool and liked to slip through small fingers like a secret.",
        tiny=True,
        noisy=False,
        flat=False,
        rolling=True,
        tags={"jade", "rolling"},
    ),
    "paper_token": MissingItem(
        id="paper_token",
        label="the paper token",
        phrase="a paper token painted with a little moon",
        owner_line="It was thin and light, and it always looked as if one breeze might carry it into a story.",
        tiny=True,
        noisy=False,
        flat=True,
        rolling=False,
        tags={"paper", "flat"},
    ),
}

HIDING_PLACES = {
    "rug_fold": HidingPlace(
        id="rug_fold",
        label="rug fold",
        phrase="in a folded edge of the rug",
        place_line="near the edge of the oriental rug",
        allows_tiny=True,
        visible_low=True,
        tags={"rug", "low"},
    ),
    "under_cabinet": HidingPlace(
        id="under_cabinet",
        label="under cabinet",
        phrase="under the low cabinet",
        place_line="beneath the cabinet where dust bunnies slept",
        allows_tiny=True,
        needs_rolling=True,
        visible_low=True,
        tags={"cabinet", "low"},
    ),
    "inside_slipper": HidingPlace(
        id="inside_slipper",
        label="inside slipper",
        phrase="inside a house slipper by the door",
        place_line="with the slippers by the door",
        allows_tiny=True,
        needs_noisy=False,
        visible_low=False,
        tags={"slipper", "door"},
    ),
    "between_book_pages": HidingPlace(
        id="between_book_pages",
        label="between pages",
        phrase="between two fat picture-book pages",
        place_line="inside the reading basket",
        allows_tiny=True,
        needs_flat=True,
        visible_low=False,
        tags={"books", "flat"},
    ),
}

METHODS = {
    "listen": SearchMethod(
        id="listen",
        label="listen for a sound",
        sense=3,
        action_line="{seeker} held very still while {helper} tapped the room softly and listened for the smallest clue.",
        success_line="A faint sound answered, and there was {item} {place}.",
        fail_line="They listened until even the rain seemed to hold its breath, but {item} stayed silent.",
        checks_noisy=True,
        tags={"listen", "detective"},
    ),
    "look_low": SearchMethod(
        id="look_low",
        label="kneel and scan low places",
        sense=3,
        action_line="{seeker} and {helper} knelt on the floor and searched every shadow near their knees.",
        success_line="At last a careful glance found {item} {place}.",
        fail_line="They searched every low shadow they could see, but {item} was not there.",
        checks_low=True,
        tags={"search", "floor"},
    ),
    "check_books": SearchMethod(
        id="check_books",
        label="check the books",
        sense=2,
        action_line="{helper} opened the books one by one while {seeker} watched each page like a real detective.",
        success_line="Between two pages, there was {item} {place}.",
        fail_line="Only pictures and paper rustles answered them. {item} was somewhere else.",
        checks_books=True,
        tags={"books", "detective"},
    ),
    "shake_slipper": SearchMethod(
        id="shake_slipper",
        label="check the slippers",
        sense=2,
        action_line="{seeker} lifted each slipper carefully while {helper} peered inside.",
        success_line="Something small slid forward, and there was {item} {place}.",
        fail_line="The slippers were empty except for warm shadows. {item} was still missing.",
        checks_slipper=True,
        tags={"slipper", "search"},
    ),
    "guess": SearchMethod(
        id="guess",
        label="just guess",
        sense=1,
        action_line="{seeker} pointed at a random corner and hoped the mystery would solve itself.",
        success_line="By pure luck there was {item} {place}.",
        fail_line="But hoping is not the same as searching, and {item} did not appear.",
        tags={"guess"},
    ),
}

GIRL_NAMES = ["Mina", "Lian", "Asha", "Rina", "Nora", "Mei", "Tara", "Anya"]
BOY_NAMES = ["Jun", "Kai", "Ravi", "Leo", "Omar", "Tao", "Milo", "Eli"]
TRAITS = ["patient", "careful", "observant", "steady", "hasty", "impulsive"]
RELATIONS = ["siblings", "friends"]


@dataclass
class StoryParams:
    setting: str
    item: str
    hide: str
    method: str
    seeker_name: str
    seeker_gender: str
    helper_name: str
    helper_gender: str
    adult: str
    trait: str
    relation: str
    trust: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="tea_room",
        item="bell_charm",
        hide="inside_slipper",
        method="listen",
        seeker_name="Mina",
        seeker_gender="girl",
        helper_name="Jun",
        helper_gender="boy",
        adult="grandmother",
        trait="hasty",
        relation="siblings",
        trust=3,
        seed=None,
    ),
    StoryParams(
        setting="study",
        item="jade_bead",
        hide="under_cabinet",
        method="look_low",
        seeker_name="Kai",
        seeker_gender="boy",
        helper_name="Lian",
        helper_gender="girl",
        adult="grandfather",
        trait="patient",
        relation="friends",
        trust=7,
        seed=None,
    ),
    StoryParams(
        setting="music_room",
        item="paper_token",
        hide="between_book_pages",
        method="check_books",
        seeker_name="Mei",
        seeker_gender="girl",
        helper_name="Tao",
        helper_gender="boy",
        adult="grandmother",
        trait="observant",
        relation="siblings",
        trust=8,
        seed=None,
    ),
    StoryParams(
        setting="tea_room",
        item="jade_bead",
        hide="rug_fold",
        method="check_books",
        seeker_name="Ravi",
        seeker_gender="boy",
        helper_name="Asha",
        helper_gender="girl",
        adult="grandfather",
        trait="careful",
        relation="friends",
        trust=6,
        seed=None,
    ),
    StoryParams(
        setting="study",
        item="paper_token",
        hide="between_book_pages",
        method="listen",
        seeker_name="Nora",
        seeker_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        adult="grandmother",
        trait="impulsive",
        relation="siblings",
        trust=2,
        seed=None,
    ),
]


KNOWLEDGE = {
    "oriental": [(
        "What is an oriental rug?",
        "An oriental rug is a patterned rug made to spread on the floor. It often has detailed shapes and colors, so children may notice its lines and edges when they look for clues."
    )],
    "detective": [(
        "What does a detective do?",
        "A detective looks for clues and asks careful questions to solve a mystery. Good detectives do not rush to blame people without proof."
    )],
    "bell": [(
        "Why can a little bell be easier to find?",
        "A little bell can make a tiny sound when it moves. That sound can become a clue if the room is quiet enough."
    )],
    "jade": [(
        "Why can a round bead roll away?",
        "A round bead can move across the floor if it slips from your hand. That is why people often check low places when something small and smooth goes missing."
    )],
    "paper": [(
        "Why can paper hide inside a book?",
        "Thin paper can slide between pages because it is flat and light. A page can close over it and make it hard to see."
    )],
    "books": [(
        "Why do detectives retrace their steps?",
        "Retracing your steps means thinking about where you have just been and what you just touched. It helps you search in the places that make the most sense first."
    )],
    "kindness": [(
        "Why is it important not to blame too quickly?",
        "Quick blame can hurt someone's feelings before you know the truth. It is kinder and smarter to look for clues first."
    )],
    "slipper": [(
        "Why might a small thing end up in a slipper?",
        "Small things can drop into open slippers near the floor, especially by a door where people pause and turn around."
    )],
}
KNOWLEDGE_ORDER = ["oriental", "detective", "bell", "jade", "paper", "books", "slipper", "kindness"]


def pair_noun(seeker: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if seeker.type == "girl" and helper.type == "girl":
            return "two sisters"
        if seeker.type == "boy" and helper.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = display_name(f["seeker"])
    helper = display_name(f["helper"])
    item = f["item_cfg"]
    hiding = f["hiding_cfg"]
    outcome = f["outcome"]
    lines = [
        'Write a short detective story for a 3-to-5-year-old that includes the word "oriental".',
        f"Tell a suspenseful but gentle mystery where {seeker} loses {item.phrase} and must follow clues in a room with an oriental rug.",
    ]
    if outcome == "adult_hint":
        lines.append(
            f"Write a story about curiosity and a lesson learned where children try one wrong search first, then solve the case after an elder asks where the missing object was last seen."
        )
    elif outcome == "apology_found":
        lines.append(
            f"Write a detective story where {seeker} blurts out blame, then feels sorry and learns to be kinder after finding {item.label} {hiding.phrase}."
        )
    else:
        lines.append(
            f"Write a quiet detective story where {seeker} and {helper} stay calm, use a careful clue, and find {item.label} {hiding.phrase}."
        )
    return lines


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    adult = f["adult"]
    item = f["item_cfg"]
    hiding = f["hiding_cfg"]
    method = f["method_cfg"]
    relation = seeker.attrs.get("relation", "friends")
    pair = pair_noun(seeker, helper, relation)
    seeker_name = display_name(seeker)
    helper_name = display_name(helper)
    adult_name = adult.label_word
    qa = [
        (
            "Who is the story about?",
            f"It is about {pair}, {seeker_name} and {helper_name}, and their {adult_name} who helps them think like detectives."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item.phrase}. It mattered to {seeker_name}, so the loss felt mysterious and important."
        ),
        (
            "Why did the room feel suspenseful?",
            f"The rain was tapping outside, and the room had an oriental rug and quiet corners that made every little clue feel important. That made the search feel tense even though everyone stayed safe."
        ),
        (
            f"How did they solve the mystery?",
            f"They used {method.label} and followed the clue that fit the room. That led them to {item.label} {hiding.phrase}."
            if f["outcome"] != "adult_hint"
            else f"They first tried {method.label}, but it did not solve the case. Then {adult_name} asked where the item had last been, and that clue led them to {item.label} {hiding.phrase}."
        ),
    ]
    if f.get("accused"):
        qa.append((
            f"Why did {seeker_name} say sorry?",
            f"{seeker_name} had blamed {helper_name} before the clues were clear. After the item was found, {seeker.pronoun('subject')} understood that a fast guess can hurt someone who did nothing wrong."
        ))
    else:
        qa.append((
            f"What lesson did {seeker_name} learn?",
            f"{seeker_name} learned that curiosity works best with calm thinking and kindness. Looking for clues first helped solve the mystery without hurting anyone's feelings."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"oriental", "detective", "kindness"}
    item = world.facts["item_cfg"]
    hiding = world.facts["hiding_cfg"]
    if item.id == "bell_charm":
        tags.add("bell")
    if item.id == "jade_bead":
        tags.add("jade")
    if item.id == "paper_token":
        tags |= {"paper", "books"}
    if hiding.id == "inside_slipper":
        tags.add("slipper")
    if hiding.id == "between_book_pages":
        tags.add("books")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} accused={world.facts.get('accused')} item_found={world.facts.get('item_found')}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- plausibility gate ------------------------------------------------------
plausible(Item, Hide) :- item(Item), hide(Hide), tiny(Item), allows_tiny(Hide),
                         not needs_noisy(Hide), not needs_flat(Hide), not needs_rolling(Hide).
plausible(Item, Hide) :- item(Item), hide(Hide), tiny(Item), allows_tiny(Hide),
                         needs_noisy(Hide), noisy(Item).
plausible(Item, Hide) :- item(Item), hide(Hide), tiny(Item), allows_tiny(Hide),
                         needs_flat(Hide), flat(Item).
plausible(Item, Hide) :- item(Item), hide(Hide), tiny(Item), allows_tiny(Hide),
                         needs_rolling(Hide), rolling(Item).

invalid(Item, Hide) :- needs_noisy(Hide), not noisy(Item).
invalid(Item, Hide) :- needs_flat(Hide), not flat(Item).
invalid(Item, Hide) :- needs_rolling(Hide), not rolling(Item).

valid(Setting, Item, Hide) :- setting(Setting), plausible(Item, Hide), not invalid(Item, Hide).

% --- method fit -------------------------------------------------------------
fits(Hide, Method) :- hide_low(Hide), checks_low(Method).
fits(Hide, Method) :- hide_books(Hide), checks_books(Method).
fits(Hide, Method) :- hide_slipper(Hide), checks_slipper(Method).
fits(inside_slipper, Method) :- checks_noisy(Method).

% --- social / ending model --------------------------------------------------
careful_trait(T) :- trait_name(T), is_careful(T).
would_accuse :- relation(siblings), chosen_trait(T), not is_careful(T), trust(V), V <= 4.
would_accuse :- relation(friends), chosen_trait(T), not is_careful(T), trust(V), V <= 3.

outcome(apology_found) :- would_accuse, chosen_hide(H), chosen_method(M), fits(H, M).
outcome(adult_hint) :- would_accuse, chosen_hide(H), chosen_method(M), not fits(H, M).
outcome(careful_found) :- not would_accuse, chosen_hide(H), chosen_method(M), fits(H, M).
outcome(adult_hint) :- not would_accuse, chosen_hide(H), chosen_method(M), not fits(H, M).

sensible(Method) :- method(Method), sense(Method, S), sense_min(Min), S >= Min.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.tiny:
            lines.append(asp.fact("tiny", item_id))
        if item.noisy:
            lines.append(asp.fact("noisy", item_id))
        if item.flat:
            lines.append(asp.fact("flat", item_id))
        if item.rolling:
            lines.append(asp.fact("rolling", item_id))
    for hide_id, hide in HIDING_PLACES.items():
        lines.append(asp.fact("hide", hide_id))
        if hide.allows_tiny:
            lines.append(asp.fact("allows_tiny", hide_id))
        if hide.needs_noisy:
            lines.append(asp.fact("needs_noisy", hide_id))
        if hide.needs_flat:
            lines.append(asp.fact("needs_flat", hide_id))
        if hide.needs_rolling:
            lines.append(asp.fact("needs_rolling", hide_id))
        if hide.visible_low:
            lines.append(asp.fact("hide_low", hide_id))
        if hide.id == "between_book_pages":
            lines.append(asp.fact("hide_books", hide_id))
        if hide.id == "inside_slipper":
            lines.append(asp.fact("hide_slipper", hide_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.checks_noisy:
            lines.append(asp.fact("checks_noisy", method_id))
        if method.checks_low:
            lines.append(asp.fact("checks_low", method_id))
        if method.checks_books:
            lines.append(asp.fact("checks_books", method_id))
        if method.checks_slipper:
            lines.append(asp.fact("checks_slipper", method_id))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
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
        asp.fact("chosen_hide", params.hide),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_trait", params.trait),
        asp.fact("relation", params.relation),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    with io.StringIO() as buf, redirect_stdout(buf):
        emit(sample, trace=True, qa=True, header="### smoke")
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: generated empty story.)")


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    python_methods = {m.id for m in sensible_methods()}
    clingo_methods = set(asp_sensible())
    if python_methods == clingo_methods:
        print(f"OK: sensible methods match ({sorted(python_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={sorted(python_methods)} clingo={sorted(clingo_methods)}")

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child-scale detective mystery in a room with an oriental rug."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hide", choices=HIDING_PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--adult", choices=["grandmother", "grandfather"])
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three QA sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.hide:
        item = ITEMS[args.item]
        hiding = HIDING_PLACES[args.hide]
        if not hide_is_plausible(item, hiding):
            raise StoryError(explain_rejection(item, hiding))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.hide is None or combo[2] == args.hide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, hide_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    seeker_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    seeker_name = _pick_name(rng, seeker_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=seeker_name)
    adult = args.adult or rng.choice(["grandmother", "grandfather"])
    relation = args.relation or rng.choice(RELATIONS)
    trait = args.trait or rng.choice(TRAITS)
    trust = rng.randint(2, 8)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        hide=hide_id,
        method=method_id,
        seeker_name=seeker_name,
        seeker_gender=seeker_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult=adult,
        trait=trait,
        relation=relation,
        trust=trust,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item})")
    if params.hide not in HIDING_PLACES:
        raise StoryError(f"(Invalid hide: {params.hide})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))
    if not hide_is_plausible(ITEMS[params.item], HIDING_PLACES[params.hide]):
        raise StoryError(explain_rejection(ITEMS[params.item], HIDING_PLACES[params.hide]))

    world = tell(
        SETTINGS[params.setting],
        ITEMS[params.item],
        HIDING_PLACES[params.hide],
        METHODS[params.method],
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        trait=params.trait,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        methods = asp_sensible()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (setting, item, hide) combos:\n")
        for setting_id, item_id, hide_id in combos:
            print(f"  {setting_id:10} {item_id:12} {hide_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.seeker_name}: {p.item} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
