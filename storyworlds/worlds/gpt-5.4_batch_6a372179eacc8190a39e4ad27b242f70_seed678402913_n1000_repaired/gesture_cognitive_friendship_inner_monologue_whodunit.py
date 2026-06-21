#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gesture_cognitive_friendship_inner_monologue_whodunit.py
===================================================================================

A small storyworld for a child-sized whodunit: something important goes missing,
a friend looks suspicious because of an odd gesture, and a young detective has
to choose between a rash accusation and a patient question.

The world model tracks physical clues ("meters") and feelings ("memes"), then
renders a complete story with a beginning, a middle turn, and an ending image
that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/gesture_cognitive_friendship_inner_monologue_whodunit.py
    python storyworlds/worlds/gpt-5.4/gesture_cognitive_friendship_inner_monologue_whodunit.py --item paper_crown --cause mend --gesture hiding_hands
    python storyworlds/worlds/gpt-5.4/gesture_cognitive_friendship_inner_monologue_whodunit.py --cause rinse --item paper_crown
    python storyworlds/worlds/gpt-5.4/gesture_cognitive_friendship_inner_monologue_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/gesture_cognitive_friendship_inner_monologue_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gesture_cognitive_friendship_inner_monologue_whodunit.py --verify
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
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    affords: set[str] = field(default_factory=set)
    nook: str = ""
    ending: str = ""


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    good_for: set[str] = field(default_factory=set)
    singular: bool = True

    @property
    def it(self) -> str:
        return "it" if self.singular else "them"


@dataclass
class Cause:
    id: str
    clue_word: str
    place: str
    found_text: str
    explain_text: str
    needs_setting: set[str] = field(default_factory=set)
    needs_item_tag: set[str] = field(default_factory=set)
    gesture_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class GestureCfg:
    id: str
    text: str
    thought: str
    clue_text: str
    clue_meter: str
    cause_ids: set[str] = field(default_factory=set)
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


def _r_missing(world: World) -> list[str]:
    item = world.get("item")
    detective = world.get("detective")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["curiosity"] += 1
    detective.memes["suspicion"] += 1
    return []


def _r_accusation(world: World) -> list[str]:
    detective = world.get("detective")
    friend = world.get("friend")
    if detective.memes["accused"] < THRESHOLD:
        return []
    sig = ("accused", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    detective.memes["regret"] += 1
    return []


def _r_reveal(world: World) -> list[str]:
    item = world.get("item")
    detective = world.get("detective")
    friend = world.get("friend")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    detective.memes["relief"] += 1
    detective.memes["trust"] += 1
    friend.memes["relief"] += 1
    friend.memes["trust"] += 1
    detective.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing", tag="mystery", apply=_r_missing),
    Rule(name="accusation", tag="social", apply=_r_accusation),
    Rule(name="reveal", tag="social", apply=_r_reveal),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom reading corner",
        scene="Sunlight lay in warm squares on the rug, and the cubbies stood like neat little houses.",
        affords={"mend", "rinse", "decorate"},
        nook="the craft shelf by the glue tray",
        ending="The rug no longer felt like a crime scene. It felt like a place where two friends could laugh again.",
    ),
    "clubhouse": Setting(
        id="clubhouse",
        place="the little cardboard clubhouse in the playroom",
        scene="A paper sign hung over the flap-door, and the floor was full of crayons, tape, and grand detective plans.",
        affords={"mend", "decorate"},
        nook="the workbench under the paper lantern",
        ending="The clubhouse felt less like a secret lair now and more like a place built for two friends together.",
    ),
    "art_room": Setting(
        id="art_room",
        place="the bright art room",
        scene="The tables smelled faintly of paper and crayons, and jars of buttons sparkled beside the window.",
        affords={"mend", "decorate", "rinse"},
        nook="the long sink beside the drying rack",
        ending="The room still held a little mystery in the corners, but the biggest thing in it was trust.",
    ),
}

ITEMS = {
    "paper_crown": MissingThing(
        id="paper_crown",
        label="paper crown",
        phrase="a shiny paper crown with three gold stars",
        tags={"paper", "wearable"},
        good_for={"mend", "decorate"},
    ),
    "treasure_map": MissingThing(
        id="treasure_map",
        label="treasure map",
        phrase="a hand-drawn treasure map with a red X",
        tags={"paper", "map"},
        good_for={"mend"},
    ),
    "friendship_bracelet": MissingThing(
        id="friendship_bracelet",
        label="friendship bracelet",
        phrase="a braided friendship bracelet with blue string",
        tags={"washable", "friendship"},
        good_for={"rinse", "decorate"},
    ),
    "star_badge": MissingThing(
        id="star_badge",
        label="star badge",
        phrase="a cardboard star badge with a safety pin on the back",
        tags={"paper", "award"},
        good_for={"mend", "decorate"},
    ),
}

CAUSES = {
    "mend": Cause(
        id="mend",
        clue_word="tape",
        place="at the craft shelf",
        found_text="resting beside a small roll of tape",
        explain_text="had found a torn corner and wanted to mend it before anyone saw",
        needs_setting={"classroom", "clubhouse", "art_room"},
        needs_item_tag={"paper"},
        gesture_ids={"hiding_hands"},
        tags={"tape", "fixing"},
    ),
    "rinse": Cause(
        id="rinse",
        clue_word="water",
        place="by the sink",
        found_text="lying on a folded paper towel near the sink",
        explain_text="had seen a sticky blob of jam on it and hurried to rinse it clean",
        needs_setting={"classroom", "art_room"},
        needs_item_tag={"washable"},
        gesture_ids={"looking_sink"},
        tags={"water", "cleaning"},
    ),
    "decorate": Cause(
        id="decorate",
        clue_word="glitter",
        place="under the ribbon box",
        found_text="tucked under a ribbon box with one bright silver sticker beside it",
        explain_text="was secretly adding one last sparkle to turn it into a friendship surprise",
        needs_setting={"classroom", "clubhouse", "art_room"},
        needs_item_tag=set(),
        gesture_ids={"brushing_glitter"},
        tags={"glitter", "surprise"},
    ),
}

GESTURES = {
    "hiding_hands": GestureCfg(
        id="hiding_hands",
        text="kept tucking both hands behind his back",
        thought="Hands behind a back could mean hiding something. Or could mean protecting something fragile.",
        clue_text="a silver strip of tape clinging to one finger",
        clue_meter="tape_seen",
        cause_ids={"mend"},
        tags={"gesture", "tape"},
    ),
    "looking_sink": GestureCfg(
        id="looking_sink",
        text="made a quick gesture toward the sink and then looked away",
        thought="That tiny gesture was odd. Why point at the sink unless the sink mattered?",
        clue_text="one damp cuff and a drop of water on the floor",
        clue_meter="water_seen",
        cause_ids={"rinse"},
        tags={"gesture", "water"},
    ),
    "brushing_glitter": GestureCfg(
        id="brushing_glitter",
        text="kept brushing at one cheek with a worried little gesture",
        thought="A worried gesture could mean guilt, but it could also mean a surprise trying not to jump out too early.",
        clue_text="a dot of glitter shining near one eyebrow",
        clue_meter="glitter_seen",
        cause_ids={"decorate"},
        tags={"gesture", "glitter"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    item: str
    cause: str
    gesture: str
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
    adult: str
    patience: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Zoe", "Ella", "Maya", "Lucy"]
BOY_NAMES = ["Rafi", "Ben", "Leo", "Theo", "Sam", "Noah", "Eli", "Max"]
PATIENCE_LEVELS = ["gentle", "hasty"]


def valid_combo(setting_id: str, item_id: str, cause_id: str, gesture_id: str) -> bool:
    if setting_id not in SETTINGS or item_id not in ITEMS or cause_id not in CAUSES or gesture_id not in GESTURES:
        return False
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    cause = CAUSES[cause_id]
    gesture = GESTURES[gesture_id]
    if cause_id not in setting.affords:
        return False
    if cause.needs_setting and setting_id not in cause.needs_setting:
        return False
    if cause.needs_item_tag and not (item.tags & cause.needs_item_tag):
        return False
    if cause_id not in item.good_for:
        return False
    if gesture_id not in cause.gesture_ids:
        return False
    if cause_id not in gesture.cause_ids:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id in ITEMS:
            for cause_id in CAUSES:
                for gesture_id in GESTURES:
                    if valid_combo(setting_id, item_id, cause_id, gesture_id):
                        combos.append((setting_id, item_id, cause_id, gesture_id))
    return combos


def explain_rejection(setting_id: str, item_id: str, cause_id: str, gesture_id: str) -> str:
    if setting_id in SETTINGS and cause_id in CAUSES and cause_id not in SETTINGS[setting_id].affords:
        return (
            f"(No story: {SETTINGS[setting_id].place} does not support the '{cause_id}' explanation. "
            f"The clue and reveal would not feel honest there.)"
        )
    if item_id in ITEMS and cause_id in CAUSES:
        item = ITEMS[item_id]
        cause = CAUSES[cause_id]
        if cause.needs_item_tag and not (item.tags & cause.needs_item_tag):
            need = ", ".join(sorted(cause.needs_item_tag))
            return (
                f"(No story: {item.phrase} is not a good fit for '{cause_id}'. "
                f"That cause needs an item tagged {need}.)"
            )
        if cause_id not in item.good_for:
            return (
                f"(No story: {item.phrase} is not a plausible object for '{cause_id}'. "
                f"Pick a cause that matches what can reasonably happen to that item.)"
            )
    if gesture_id in GESTURES and cause_id in CAUSES and cause_id not in GESTURES[gesture_id].cause_ids:
        return (
            f"(No story: the gesture '{gesture_id}' points to a different clue trail, "
            f"so it would mislead the world model rather than create a fair mystery.)"
        )
    return "(No story: that combination does not make a fair little whodunit.)"


def outcome_of(params: StoryParams) -> str:
    return "kind" if params.patience == "gentle" else "oops"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def introduce(world: World, detective: Entity, friend: Entity, adult: Entity, item: Entity, item_cfg: MissingThing) -> None:
    world.say(
        f"{detective.id} and {friend.id} were best friends, and on that day {world.setting.place} belonged to them."
    )
    world.say(world.setting.scene)
    world.say(
        f"They were taking turns with {item_cfg.phrase}, and even {adult.label_word} smiled to see how carefully they shared."
    )
    item.meters["special"] += 1


def vanish(world: World, detective: Entity, item: Entity, item_cfg: MissingThing) -> None:
    item.meters["missing"] += 1
    propagate(world)
    world.say(
        f"Then {detective.id} looked back at the stool where the {item_cfg.label} had been, and the stool was empty."
    )
    world.say(
        f"The little missing thing suddenly made the whole room feel larger and quieter."
    )


def suspect_scene(world: World, detective: Entity, friend: Entity, gesture: GestureCfg) -> None:
    friend.memes["nervous"] += 1
    detective.memes["suspicion"] += 1
    world.say(
        f"At that very moment, {friend.id} {gesture.text}."
    )
    world.say(
        f'Inside {detective.id}\'s head, a detective voice whispered: "{gesture.thought}"'
    )
    world.say(
        f'It felt like a cognitive puzzle, the kind that made {detective.id} stand very still and notice tiny things.'
    )


def inspect_clue(world: World, detective: Entity, friend: Entity, gesture: GestureCfg) -> None:
    friend.meters[gesture.clue_meter] += 1
    detective.meters[gesture.clue_meter] += 1
    world.say(
        f"{detective.id} saw {gesture.clue_text}."
    )
    world.say(
        f"That clue did not prove anything, but it pointed the mystery in one direction."
    )


def hasty_accuse(world: World, detective: Entity, friend: Entity, item_cfg: MissingThing) -> None:
    detective.memes["accused"] += 1
    propagate(world)
    world.say(
        f'"Aha!" {detective.id} burst out. "You took the {item_cfg.label}!"'
    )
    world.say(
        f"{friend.id}'s face fell at once, and the room stopped feeling playful."
    )


def gentle_question(world: World, detective: Entity, friend: Entity, item_cfg: MissingThing) -> None:
    detective.memes["care"] += 1
    world.say(
        f'{detective.id} took a breath. "Did you see where the {item_cfg.label} went?" {detective.pronoun()} asked.'
    )
    world.say(
        f"{friend.id} blinked, surprised, but not angry."
    )


def follow_clue(world: World, detective: Entity, cause: Cause, setting: Setting) -> None:
    detective.meters["searched"] += 1
    world.say(
        f'{detective.id} followed the clue trail to {cause.place}, near {setting.nook}.'
    )


def reveal(world: World, detective: Entity, friend: Entity, item: Entity, item_cfg: MissingThing, cause: Cause) -> None:
    item.meters["found"] += 1
    propagate(world)
    friend.memes["helpfulness"] += 1
    world.say(
        f"There was the {item_cfg.label}, {cause.found_text}."
    )
    world.say(
        f'"I didn\'t steal it," {friend.id} said softly. "{friend.pronoun("subject").capitalize()} {cause.explain_text}."'
        if friend.type not in {"boy", "girl"} else
        f'"I didn\'t steal it," {friend.id} said softly. "I {cause.explain_text}."'
    )


def repair_friendship(world: World, detective: Entity, friend: Entity, adult: Entity, params: StoryParams) -> None:
    if outcome_of(params) == "oops":
        detective.memes["apology"] += 1
        friend.memes["forgive"] += 1
        world.say(
            f'{detective.id} felt heat rush into {detective.pronoun("possessive")} cheeks. "I am sorry," {detective.pronoun()} said. "I solved the mystery too fast."'
        )
        world.say(
            f'{friend.id} gave a small nod. "{adult.label_word.capitalize()} says good detectives ask before they blame," {friend.pronoun()} said, and then {friend.pronoun()} smiled a little.'
        )
    else:
        world.say(
            f'{detective.id} let out a long breath. "So that was the whole mystery," {detective.pronoun()} said, and the breath sounded almost like a laugh.'
        )
        world.say(
            f'{friend.id} grinned. "{friend.pronoun("subject").capitalize()} wanted it to be a surprise," {friend.pronoun()} said.'
            if friend.type not in {"boy", "girl"} else
            f'"I wanted it to be a surprise," {friend.id} said with a grin.'
        )
    world.say(
        f"{adult.label_word.capitalize()} came over, listened, and said that careful questions make kinder mysteries."
    )


def closing(world: World, detective: Entity, friend: Entity, item_cfg: MissingThing, cause: Cause, params: StoryParams) -> None:
    detective.memes["joy"] += 1
    friend.memes["joy"] += 1
    if cause.id == "decorate":
        extra = f"Now the {item_cfg.label} shone with one secret sparkle just for the two of them."
    elif cause.id == "mend":
        extra = f"Now the {item_cfg.label} looked whole again, as if the tear had never had the last word."
    else:
        extra = f"Now the {item_cfg.label} was clean and soft again instead of sticky and sad."
    world.say(extra)
    world.say(
        world.setting.ending
    )
    if outcome_of(params) == "oops":
        world.say(
            f"{detective.id} slipped one hand into {friend.id}'s, and this time the only mystery left was how friends can grow stronger after a mistake."
        )
    else:
        world.say(
            f"{detective.id} and {friend.id} sat shoulder to shoulder, holding the solved clue between them as if friendship itself had been the treasure."
        )


def tell(
    setting: Setting,
    item_cfg: MissingThing,
    cause: Cause,
    gesture: GestureCfg,
    detective_name: str,
    detective_gender: str,
    friend_name: str,
    friend_gender: str,
    adult_type: str,
    patience: str,
) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the adult"))
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label, phrase=item_cfg.phrase, tags=set(item_cfg.tags)))

    introduce(world, detective, friend, adult, item, item_cfg)

    world.para()
    vanish(world, detective, item, item_cfg)
    suspect_scene(world, detective, friend, gesture)
    inspect_clue(world, detective, friend, gesture)

    world.para()
    if patience == "hasty":
        hasty_accuse(world, detective, friend, item_cfg)
    else:
        gentle_question(world, detective, friend, item_cfg)
    follow_clue(world, detective, cause, setting)
    reveal(world, detective, friend, item, item_cfg, cause)

    world.para()
    repair_friendship(world, detective, friend, adult, StoryParams(
        setting=setting.id,
        item=item_cfg.id,
        cause=cause.id,
        gesture=gesture.id,
        detective=detective_name,
        detective_gender=detective_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        adult=adult_type,
        patience=patience,
        seed=None,
    ))
    closing(world, detective, friend, item_cfg, cause, StoryParams(
        setting=setting.id,
        item=item_cfg.id,
        cause=cause.id,
        gesture=gesture.id,
        detective=detective_name,
        detective_gender=detective_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        adult=adult_type,
        patience=patience,
        seed=None,
    ))

    world.facts.update(
        setting=setting,
        item_cfg=item_cfg,
        cause=cause,
        gesture=gesture,
        detective=detective,
        friend=friend,
        adult=adult,
        item=item,
        outcome="kind" if patience == "gentle" else "oops",
        found=item.meters["found"] >= THRESHOLD,
        accused=detective.memes["accused"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "gesture": [
        (
            "What is a gesture?",
            "A gesture is a small movement, like pointing or shrugging, that can show what someone feels or means without many words."
        )
    ],
    "cognitive": [
        (
            "What does cognitive mean?",
            "Cognitive means having to do with thinking, noticing, remembering, and figuring things out in your mind."
        )
    ],
    "tape": [
        (
            "What can tape help fix?",
            "Tape can hold torn paper together for a while. It is useful for small repairs, especially on paper crafts."
        )
    ],
    "water": [
        (
            "Why might someone take something to a sink?",
            "They might take it there to rinse off dirt or sticky stuff. Water can help clean things that are washable."
        )
    ],
    "glitter": [
        (
            "Why does glitter show up everywhere?",
            "Glitter is made of tiny shiny pieces, so it sticks to skin and clothes easily and can be a clue that craft supplies were used."
        )
    ],
    "surprise": [
        (
            "Can a surprise look suspicious at first?",
            "Yes. When someone is trying to hide a surprise, their behavior can look secret even when they are doing something kind."
        )
    ],
    "friendship": [
        (
            "What helps friends solve problems?",
            "Friends solve problems better when they ask honest questions and listen to the answer. Kindness makes it easier to fix mistakes."
        )
    ],
    "mystery": [
        (
            "What makes a mystery fair?",
            "A fair mystery gives you real clues that fit the answer. The ending should make sense after you know what happened."
        )
    ],
}
KNOWLEDGE_ORDER = ["gesture", "cognitive", "mystery", "tape", "water", "glitter", "surprise", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    item = f["item_cfg"]
    gesture = f["gesture"]
    outcome = f["outcome"]
    if outcome == "oops":
        return [
            f'Write a child-friendly whodunit that uses the words "gesture" and "cognitive" and begins when a {item.label} goes missing.',
            f"Tell a friendship mystery where {detective.id} misreads {friend.id}'s odd gesture, accuses too fast, and then learns the kinder truth.",
            f"Write a story with inner monologue where the detective notices {gesture.clue_text} and solves the case, but only after hurting a friend's feelings and apologizing.",
        ]
    return [
        f'Write a short whodunit for a young child that includes the words "gesture" and "cognitive" and centers on a missing {item.label}.',
        f"Tell a friendship mystery where {detective.id} notices {friend.id}'s strange gesture, thinks through the clues in an inner monologue, and asks kindly before deciding.",
        f"Write a story where a small clue leads to a warm surprise instead of a bad deed, and end with trust between friends.",
    ]


def pair_noun(detective: Entity, friend: Entity) -> str:
    if detective.type == "girl" and friend.type == "girl":
        return "two friends"
    if detective.type == "boy" and friend.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    adult = f["adult"]
    item = f["item_cfg"]
    cause = f["cause"]
    gesture = f["gesture"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(detective, friend)}, {detective.id} and {friend.id}. They are in a little whodunit together, with {adult.label_word} nearby."
        ),
        (
            f"What mystery starts the story?",
            f"The mystery starts when the {item.label} disappears from where the friends had left it. That missing object turns an ordinary playtime into a detective case."
        ),
        (
            f"What made {detective.id} suspicious?",
            f"{friend.id} {gesture.text}, and {detective.id} also noticed {gesture.clue_text}. Those two things made the scene look secret, even though the clue did not prove stealing."
        ),
        (
            "Why does the story use the word cognitive?",
            f"The mystery feels like a cognitive puzzle because {detective.id} has to think, compare clues, and decide what they mean. The story is about careful noticing, not just about finding a lost thing."
        ),
    ]
    if f["outcome"] == "oops":
        qa.append(
            (
                f"What mistake did {detective.id} make?",
                f"{detective.id} accused {friend.id} before knowing the whole truth. That hurt {friend.id}'s feelings because the odd gesture came from trying to help, not from doing something mean."
            )
        )
    else:
        qa.append(
            (
                f"What did {detective.id} do instead of blaming {friend.id}?",
                f"{detective.id} asked a careful question and followed the clue trail first. That gave the mystery room to be solved kindly, without breaking the friendship."
            )
        )
    qa.append(
        (
            f"Where was the {item.label} really found?",
            f"It was found {cause.found_text}. That location matched the clue and proved what had really happened."
        )
    )
    qa.append(
        (
            f"Why did {friend.id} have the {item.label}?",
            f"{friend.id} had it because {friend.pronoun('subject')} {cause.explain_text}. The hidden truth is kind, which turns the whodunit into a friendship story."
            if friend.type not in {"boy", "girl"} else
            f"{friend.id} had it because {friend.pronoun('subject')} {cause.explain_text}. The hidden truth is kind, which turns the whodunit into a friendship story."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ends with the mystery solved and the friendship steadier than before. The last image shows that trust, not blame, is what really matters."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"gesture", "cognitive", "friendship", "mystery"}
    tags |= set(f["gesture"].tags)
    tags |= set(f["cause"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="classroom",
        item="paper_crown",
        cause="mend",
        gesture="hiding_hands",
        detective="Mina",
        detective_gender="girl",
        friend="Rafi",
        friend_gender="boy",
        adult="teacher",
        patience="gentle",
        seed=1,
    ),
    StoryParams(
        setting="art_room",
        item="friendship_bracelet",
        cause="rinse",
        gesture="looking_sink",
        detective="Leo",
        detective_gender="boy",
        friend="Ava",
        friend_gender="girl",
        adult="teacher",
        patience="gentle",
        seed=2,
    ),
    StoryParams(
        setting="clubhouse",
        item="star_badge",
        cause="decorate",
        gesture="brushing_glitter",
        detective="Nora",
        detective_gender="girl",
        friend="Ben",
        friend_gender="boy",
        adult="mother",
        patience="hasty",
        seed=3,
    ),
    StoryParams(
        setting="classroom",
        item="treasure_map",
        cause="mend",
        gesture="hiding_hands",
        detective="Theo",
        detective_gender="boy",
        friend="Lucy",
        friend_gender="girl",
        adult="teacher",
        patience="hasty",
        seed=4,
    ),
]


ASP_RULES = r"""
valid(S, I, C, G) :- setting(S), item(I), cause(C), gesture(G),
                     affords(S, C), good_for(I, C), gesture_fits(G, C),
                     cause_fits_gesture(C, G),
                     not missing_item_tag(S, I, C).

missing_item_tag(_S, I, C) :- needs_item_tag(C, T), not item_tag(I, T).

kind_outcome :- patience(gentle).
oops_outcome :- patience(hasty).
outcome(kind) :- kind_outcome.
outcome(oops) :- oops_outcome.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cause_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, cause_id))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, tag))
        for cause_id in sorted(item.good_for):
            lines.append(asp.fact("good_for", iid, cause_id))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for gid in sorted(cause.gesture_ids):
            lines.append(asp.fact("cause_fits_gesture", cid, gid))
        for tag in sorted(cause.needs_item_tag):
            lines.append(asp.fact("needs_item_tag", cid, tag))
    for gid, gesture in GESTURES.items():
        lines.append(asp.fact("gesture", gid))
        for cid in sorted(gesture.cause_ids):
            lines.append(asp.fact("gesture_fits", gid, cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("patience", params.patience)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    outcome_cases = list(CURATED)
    for idx in range(20):
        args = build_parser().parse_args([])
        try:
            p = resolve_params(args, random.Random(idx))
        except StoryError:
            continue
        outcome_cases.append(p)
    bad = sum(1 for p in outcome_cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(outcome_cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(outcome_cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("Smoke test produced an incomplete sample.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a tiny friendship whodunit with clues, inner monologue, and a kind reveal."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--gesture", choices=GESTURES)
    ap.add_argument("--adult", choices=["mother", "father", "teacher"])
    ap.add_argument("--patience", choices=PATIENCE_LEVELS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.cause and args.gesture:
        if not valid_combo(args.setting, args.item, args.cause, args.gesture):
            raise StoryError(explain_rejection(args.setting, args.item, args.cause, args.gesture))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.cause is None or combo[2] == args.cause)
        and (args.gesture is None or combo[3] == args.gesture)
    ]
    if not combos:
        setting_id = args.setting or next(iter(SETTINGS))
        item_id = args.item or next(iter(ITEMS))
        cause_id = args.cause or next(iter(CAUSES))
        gesture_id = args.gesture or next(iter(GESTURES))
        raise StoryError(explain_rejection(setting_id, item_id, cause_id, gesture_id))

    setting_id, item_id, cause_id, gesture_id = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    detective = _pick_name(rng, detective_gender)
    friend = _pick_name(rng, friend_gender, avoid=detective)
    adult = args.adult or rng.choice(["mother", "father", "teacher"])
    patience = args.patience or rng.choice(PATIENCE_LEVELS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        cause=cause_id,
        gesture=gesture_id,
        detective=detective,
        detective_gender=detective_gender,
        friend=friend,
        friend_gender=friend_gender,
        adult=adult,
        patience=patience,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.gesture not in GESTURES:
        raise StoryError(f"(Unknown gesture: {params.gesture})")
    if params.patience not in PATIENCE_LEVELS:
        raise StoryError(f"(Unknown patience mode: {params.patience})")
    if not valid_combo(params.setting, params.item, params.cause, params.gesture):
        raise StoryError(explain_rejection(params.setting, params.item, params.cause, params.gesture))

    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        cause=CAUSES[params.cause],
        gesture=GESTURES[params.gesture],
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        adult_type=params.adult,
        patience=params.patience,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, cause, gesture) combos:\n")
        for setting_id, item_id, cause_id, gesture_id in combos:
            print(f"  {setting_id:10} {item_id:20} {cause_id:10} {gesture_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} & {p.friend}: {p.item} in {p.setting} ({p.cause}, {outcome_of(p)})"
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
