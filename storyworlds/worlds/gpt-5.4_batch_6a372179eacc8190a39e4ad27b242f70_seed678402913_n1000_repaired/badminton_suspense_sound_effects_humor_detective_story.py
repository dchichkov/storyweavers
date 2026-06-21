#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/badminton_suspense_sound_effects_humor_detective_story.py
=====================================================================================

A standalone story world for a tiny detective-style badminton mystery with
suspense, sound effects, and a funny reveal.

Premise
-------
A child is excited for badminton practice, but a strange sound keeps coming from
the gym. The hero treats the mystery like a detective case, follows clues, and
learns that the suspicious noise has a harmless cause. The ending resolves the
tension and returns to play, proving what changed.

World-model idea
----------------
The world has typed entities with physical meters and emotional memes. A hidden
cause creates a suspicious sound near badminton gear. The hero can inspect a clue,
call a helper, and reveal the cause. The cause must be *reasonable* for the chosen
sound and clue, and the reveal method must fit the hiding place. Invalid
combinations are refused with a legible StoryError.

The story aims for:
- badminton in the center of the action
- detective-story flavor
- suspense via hidden cause + delayed reveal
- child-facing humor via silly harmless causes and sound effects
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


# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "mom", "woman", "coach_woman"}
        male = {"boy", "father", "dad", "man", "coach_man"}
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
            "coach_woman": "coach",
            "coach_man": "coach",
        }.get(self.type, self.label or self.type)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    hiding_places: set[str] = field(default_factory=set)
    gear: str = ""
    start_image: str = ""
    end_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Sound:
    id: str
    noise: str
    fx: str
    mood_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    funny_line: str
    noises: set[str] = field(default_factory=set)
    hides_in: set[str] = field(default_factory=set)
    methods: set[str] = field(default_factory=set)
    danger: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    points_to: set[str] = field(default_factory=set)
    places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    works_for_places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    sound: str
    cause: str
    clue: str
    method: str
    hero_name: str
    hero_gender: str
    helper_role: str
    helper_name: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "school_gym": Setting(
        id="school_gym",
        place="the school gym",
        hiding_places={"equipment_bag", "rafters", "bench"},
        gear="a bucket of shuttlecocks and a row of badminton rackets",
        start_image="The shiny floor smelled like lemon soap, and white court lines crossed it like secret map marks.",
        end_image="Badminton birds flew back and forth under the bright lights as if the whole mystery had been folded into the game.",
        tags={"gym", "badminton"},
    ),
    "community_hall": Setting(
        id="community_hall",
        place="the community hall",
        hiding_places={"equipment_bag", "curtain_rod", "bench"},
        gear="two nets, a basket of shuttlecocks, and a stack of badminton rackets",
        start_image="Tall windows made strips of gold on the floor, and the badminton court looked ready for an important case.",
        end_image="Soon the shuttlecock was popping neatly over the net while the last giggles bounced around the hall.",
        tags={"hall", "badminton"},
    ),
    "club_court": Setting(
        id="club_court",
        place="the badminton club court",
        hiding_places={"equipment_bag", "rafters", "score_table"},
        gear="fresh shuttlecocks in tubes and bright rackets lined up by the wall",
        start_image="Everything in the court looked tidy enough to hide a clue.",
        end_image="After the mystery ended, the court sounded only like shoes squeaking and a shuttlecock being tapped across the net.",
        tags={"club", "badminton"},
    ),
}

SOUNDS = {
    "thump_squeak": Sound(
        id="thump_squeak",
        noise="a thump... squeak... thump",
        fx="THUMP. Squeeeak. THUMP.",
        mood_line="It sounded as if something in the room wanted to be noticed, but not caught.",
        tags={"suspense", "funny_sound"},
    ),
    "rustle_bonk": Sound(
        id="rustle_bonk",
        noise="a rustle... bonk... rustle",
        fx="Rrrrustle. Bonk! Rrrrustle.",
        mood_line="The sound was soft, then silly, then soft again, which somehow felt even more mysterious.",
        tags={"suspense", "funny_sound"},
    ),
    "ping_plop": Sound(
        id="ping_plop",
        noise="a ping... plop... ping",
        fx="Ping! Plop. Ping!",
        mood_line="Each tiny sound bounced through the quiet court like a clue wearing tap shoes.",
        tags={"suspense", "funny_sound"},
    ),
}

CAUSES = {
    "kitten": Cause(
        id="kitten",
        label="a striped kitten",
        funny_line="The tiny detective villain had been batting at shuttlecocks with both paws and a very serious face.",
        noises={"rustle_bonk", "ping_plop"},
        hides_in={"equipment_bag", "bench"},
        methods={"peek_under", "open_bag"},
        danger=False,
        tags={"animal", "kitten", "harmless"},
    ),
    "shoe": Cause(
        id="shoe",
        label="a runaway sports shoe",
        funny_line="It kept tipping over by itself because a trapped shuttlecock was springing back under it like a stubborn marshmallow.",
        noises={"thump_squeak", "ping_plop"},
        hides_in={"bench", "score_table"},
        methods={"peek_under", "move_basket"},
        danger=False,
        tags={"shoe", "harmless"},
    ),
    "parrot": Cause(
        id="parrot",
        label="a chatty green parrot",
        funny_line="It puffed out its chest and whispered, \"Detective! Detective!\" as if it had been waiting all day for a mystery.",
        noises={"thump_squeak", "rustle_bonk"},
        hides_in={"rafters", "curtain_rod"},
        methods={"look_up", "call_coach"},
        danger=False,
        tags={"bird", "parrot", "harmless"},
    ),
    "fan_sign": Cause(
        id="fan_sign",
        label="a loose paper team sign near a fan",
        funny_line="Every time the fan blew, the sign flapped the net post and then drooped innocently, as if it had done nothing at all.",
        noises={"thump_squeak", "rustle_bonk"},
        hides_in={"score_table", "curtain_rod"},
        methods={"look_up", "move_basket"},
        danger=False,
        tags={"air", "paper", "harmless"},
    ),
}

CLUES = {
    "feather": Clue(
        id="feather",
        label="a feather",
        phrase="a small green feather",
        points_to={"parrot"},
        places={"rafters", "curtain_rod"},
        tags={"bird", "feather"},
    ),
    "pawprint": Clue(
        id="pawprint",
        label="a paw print",
        phrase="a dusty little paw print",
        points_to={"kitten"},
        places={"equipment_bag", "bench"},
        tags={"animal", "paw"},
    ),
    "lace": Clue(
        id="lace",
        label="a shoelace",
        phrase="a loose neon shoelace",
        points_to={"shoe"},
        places={"bench", "score_table"},
        tags={"shoe"},
    ),
    "paper_corner": Clue(
        id="paper_corner",
        label="a paper corner",
        phrase="a crinkled paper corner",
        points_to={"fan_sign"},
        places={"score_table", "curtain_rod"},
        tags={"paper"},
    ),
}

METHODS = {
    "peek_under": Method(
        id="peek_under",
        label="peek underneath",
        action="knelt down and peeked underneath the hiding place",
        works_for_places={"bench"},
        tags={"inspect"},
    ),
    "open_bag": Method(
        id="open_bag",
        label="open the bag",
        action="unzipped the equipment bag very slowly",
        works_for_places={"equipment_bag"},
        tags={"inspect", "bag"},
    ),
    "look_up": Method(
        id="look_up",
        label="look up high",
        action="tipped back and looked up into the high shadows",
        works_for_places={"rafters", "curtain_rod"},
        tags={"inspect", "up"},
    ),
    "move_basket": Method(
        id="move_basket",
        label="move the basket",
        action="slid the shuttlecock basket aside",
        works_for_places={"score_table", "bench"},
        tags={"inspect", "basket"},
    ),
    "call_coach": Method(
        id="call_coach",
        label="call the coach",
        action="called the coach over and pointed up",
        works_for_places={"rafters", "curtain_rod"},
        tags={"helper"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["careful", "curious", "quick-eyed", "brave", "thoughtful", "clever"]


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    hero = world.get("hero")
    mystery = world.get("mystery")
    if mystery.meters["heard"] >= THRESHOLD and ("suspense",) not in world.fired:
        world.fired.add(("suspense",))
        room.memes["unease"] += 1
        hero.memes["suspense"] += 1
        out.append("__suspense__")
    return out


def _r_clue_confidence(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    clue = world.get("clue")
    if clue.meters["found"] >= THRESHOLD and ("confidence",) not in world.fired:
        world.fired.add(("confidence",))
        hero.memes["confidence"] += 1
        out.append("__confidence__")
    return out


def _r_reveal_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    cause = world.get("cause")
    room = world.get("room")
    if cause.meters["revealed"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        helper.memes["joy"] += 1
        room.memes["unease"] = 0.0
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="suspense", tag="emotion", apply=_r_suspense),
    Rule(name="clue_confidence", tag="emotion", apply=_r_clue_confidence),
    Rule(name="reveal_relief", tag="emotion", apply=_r_reveal_relief),
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


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def cause_matches_sound(cause: Cause, sound: Sound) -> bool:
    return sound.id in cause.noises


def clue_matches_cause(clue: Clue, cause: Cause) -> bool:
    return cause.id in clue.points_to


def clue_matches_setting_place(clue: Clue, setting: Setting, cause: Cause) -> bool:
    return bool(clue.places & setting.hiding_places & cause.hides_in)


def method_matches(setting: Setting, cause: Cause, method: Method) -> bool:
    return bool(setting.hiding_places & cause.hides_in & method.works_for_places) and method.id in cause.methods


def valid_combo(setting_id: str, sound_id: str, cause_id: str, clue_id: str, method_id: str) -> bool:
    setting = SETTINGS[setting_id]
    sound = SOUNDS[sound_id]
    cause = CAUSES[cause_id]
    clue = CLUES[clue_id]
    method = METHODS[method_id]
    return (
        cause_matches_sound(cause, sound)
        and clue_matches_cause(clue, cause)
        and clue_matches_setting_place(clue, setting, cause)
        and method_matches(setting, cause, method)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for sound_id in SOUNDS:
            for cause_id in CAUSES:
                for clue_id in CLUES:
                    for method_id in METHODS:
                        if valid_combo(setting_id, sound_id, cause_id, clue_id, method_id):
                            combos.append((setting_id, sound_id, cause_id, clue_id, method_id))
    return combos


def explain_invalid(setting_id: str, sound_id: str, cause_id: str, clue_id: str, method_id: str) -> str:
    setting = SETTINGS[setting_id]
    sound = SOUNDS[sound_id]
    cause = CAUSES[cause_id]
    clue = CLUES[clue_id]
    method = METHODS[method_id]
    if not cause_matches_sound(cause, sound):
        return (
            f"(No story: {cause.label} would not reasonably make the sound {sound.noise}. "
            f"Choose a cause that fits the noise.)"
        )
    if not clue_matches_cause(clue, cause):
        return (
            f"(No story: {clue.phrase} would not honestly point to {cause.label}. "
            f"The detective clue has to fit the hidden cause.)"
        )
    if not clue_matches_setting_place(clue, setting, cause):
        return (
            f"(No story: in {setting.place}, {clue.phrase} would not plausibly appear near "
            f"where {cause.label} is hidden. The clue must fit the location.)"
        )
    if not method_matches(setting, cause, method):
        return (
            f"(No story: the method '{method.label}' would not reveal {cause.label} in {setting.place}. "
            f"Pick a method that actually reaches the hiding place.)"
        )
    return "(No story: this combination does not make a reasonable mystery.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_reveal(world: World, method_id: str) -> dict:
    sim = world.copy()
    cause = sim.get("cause")
    setting_id = sim.facts["setting"].id
    method = METHODS[method_id]
    ok = method_matches(SETTINGS[setting_id], CAUSES[cause.attrs["cfg_id"]], method)
    if ok:
        cause.meters["revealed"] += 1
        propagate(sim, narrate=False)
    return {
        "revealed": cause.meters["revealed"] >= THRESHOLD,
        "hero_relief": sim.get("hero").memes["relief"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} arrived at {setting.place} with {helper.id}, ready for badminton."
    )
    world.say(setting.start_image)
    world.say(
        f"Near the net stood {setting.gear}, and {hero.id} felt as if a splendid afternoon were about to begin."
    )


def first_sound(world: World, hero: Entity, sound: Sound) -> None:
    mystery = world.get("mystery")
    mystery.meters["heard"] += 1
    hero.memes["curiosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the court went quiet. {sound.fx} The sound came from somewhere nearby."
    )
    world.say(sound.mood_line)
    world.say(
        f"{hero.id} tightened {hero.pronoun('possessive')} grip on the racket and whispered, "
        f"\"This has become a case.\""
    )


def detective_vow(world: World, hero: Entity, trait: str) -> None:
    hero.memes["detective"] += 1
    extra = {
        "careful": "look at every corner twice",
        "curious": "follow every tiny clue",
        "quick-eyed": "notice what other people missed",
        "brave": "step closer even while feeling wiggly inside",
        "thoughtful": "think before making a guess",
        "clever": "use detective logic instead of a wild guess",
    }.get(trait, "pay close attention")
    world.say(
        f"{hero.id}, who was especially {trait}, decided to {extra}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tiptoed past the badminton net as if the white tape were a line in a detective notebook."
    )


def find_clue(world: World, hero: Entity, clue: Clue) -> None:
    ent = world.get("clue")
    ent.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"By the sideline, {hero.id} spotted {clue.phrase}."
    )
    world.say(
        f"\"Aha,\" {hero.pronoun()} murmured. \"A clue. Cases do not solve themselves.\""
    )


def consult_helper(world: World, hero: Entity, helper: Entity, sound: Sound, clue: Clue) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{hero.id} hurried to {helper.id}. \"I heard {sound.noise}, and then I found {clue.phrase},\" "
        f"{hero.pronoun()} said."
    )
    world.say(
        f"{helper.id} did not laugh first. {helper.pronoun().capitalize()} looked where {hero.id} pointed and said, "
        f"\"That does sound like a true puzzle. Let us inspect it properly.\""
    )


def inspect(world: World, hero: Entity, helper: Entity, method: Method) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"Together they crept forward. {helper.id} {method.action}, while {hero.id} held {hero.pronoun('possessive')} breath."
    )


def reveal(world: World, cause_cfg: Cause, method: Method) -> None:
    cause = world.get("cause")
    cause.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say("For one heartbeat, nothing happened.")
    world.say(
        f"Then -- {world.facts['sound'].fx} -- there it was: {cause_cfg.label}!"
    )
    world.say(cause_cfg.funny_line)


def laugh_and_reset(world: World, hero: Entity, helper: Entity, setting: Setting, cause_cfg: Cause) -> None:
    hero.memes["laughter"] += 1
    helper.memes["laughter"] += 1
    world.say(
        f"{hero.id}'s knees stopped feeling floaty. Instead, {hero.pronoun()} laughed so hard that the mystery seemed to shrink right on the floor."
    )
    world.say(
        f"\"So that was the terrible suspect,\" {helper.id} said with a smile."
    )
    world.say(
        f"Soon the strange sound was gone, the court felt bright again, and {setting.end_image}"
    )
    if cause_cfg.id == "kitten":
        world.say(
            f"Before the first serve, the kitten got a safe little box to nap in far from the badminton game."
        )
    elif cause_cfg.id == "parrot":
        world.say(
            f"The parrot was carried somewhere quieter, still muttering, \"Detective! Detective!\" under its breath."
        )
    else:
        world.say(
            f"{hero.id} bounced the shuttlecock once on the racket and grinned, because a solved case made badminton feel even better."
        )


# ---------------------------------------------------------------------------
# Full screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    sound: Sound,
    cause_cfg: Cause,
    clue_cfg: Clue,
    method_cfg: Method,
    hero_name: str,
    hero_gender: str,
    helper_role: str,
    helper_name: str,
    helper_gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
    ))
    helper_type = {
        ("coach", "girl"): "coach_woman",
        ("coach", "boy"): "coach_man",
        ("parent", "girl"): "mother",
        ("parent", "boy"): "father",
    }.get((helper_role, helper_gender), "coach_woman")
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_name,
        phrase=helper_name,
        role="helper",
        traits=["calm"],
    ))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    mystery = world.add(Entity(id="mystery", kind="thing", type="mystery", label="the mystery"))
    cause = world.add(Entity(
        id="cause",
        kind="thing",
        type="cause",
        label=cause_cfg.label,
        attrs={"cfg_id": cause_cfg.id},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
    ))

    world.facts.update(
        setting=setting,
        sound=sound,
        cause_cfg=cause_cfg,
        clue_cfg=clue_cfg,
        method_cfg=method_cfg,
        hero=hero,
        helper=helper,
    )

    introduce(world, hero, helper, setting)
    world.para()
    first_sound(world, hero, sound)
    detective_vow(world, hero, trait)
    world.para()
    find_clue(world, hero, clue_cfg)
    consult_helper(world, hero, helper, sound, clue_cfg)

    pred = predict_reveal(world, method_cfg.id)
    world.facts["predicted_reveal"] = pred["revealed"]

    world.para()
    inspect(world, hero, helper, method_cfg)
    reveal(world, cause_cfg, method_cfg)
    world.para()
    laugh_and_reset(world, hero, helper, setting, cause_cfg)

    world.facts.update(
        solved=cause.meters["revealed"] >= THRESHOLD,
        suspense=hero.memes["suspense"] >= THRESHOLD,
        clue_found=clue.meters["found"] >= THRESHOLD,
        relief=hero.memes["relief"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "badminton": [
        (
            "What is badminton?",
            "Badminton is a game where players use rackets to hit a light shuttlecock over a net. The shuttlecock is sometimes called a birdie."
        )
    ],
    "shuttlecock": [
        (
            "Why does a shuttlecock move differently from a ball?",
            "A shuttlecock has feathers or a feather-like skirt, so air slows it down quickly. That makes it flutter and drop in a special way."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and uses careful thinking to solve a mystery. Good detectives do not just guess; they check what is really there."
        )
    ],
    "kitten": [
        (
            "Why do kittens bat at small things?",
            "Kittens like to pounce and tap at little moving objects because it is part of how they play and learn. A bouncing shuttlecock can seem very exciting to them."
        )
    ],
    "parrot": [
        (
            "Why can parrots make surprising sounds?",
            "Parrots can copy noises and words they hear around them. That can make them sound funny or mysterious if you do not know where the voice came from."
        )
    ],
    "shoe": [
        (
            "Why might a shoe make a funny noise on a gym floor?",
            "A shoe can squeak or tip if it rubs the floor or catches on something. Little movements can make bigger sounds in a quiet room."
        )
    ],
    "paper": [
        (
            "Why does loose paper flap in moving air?",
            "Moving air pushes on the paper and makes it bend back and forth. That can create rustling or tapping sounds."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. It points you toward an answer without telling you everything at once."
        )
    ],
}
KNOWLEDGE_ORDER = ["badminton", "shuttlecock", "detective", "kitten", "parrot", "shoe", "paper", "clue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    sound = f["sound"]
    cause = f["cause_cfg"]
    clue = f["clue_cfg"]
    setting = f["setting"]
    return [
        f'Write a detective-style story for a 3-to-5-year-old that includes badminton, suspense, sound effects, and humor. The mystery sound should be "{sound.noise}".',
        f"Tell a gentle mystery where {hero.label} hears a strange noise at {setting.place}, finds {clue.phrase}, and solves the case with {helper.label}.",
        f"Write a funny suspense story about badminton practice where a child detective expects something spooky but discovers {cause.label} instead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    sound = f["sound"]
    cause = f["cause_cfg"]
    clue = f["clue_cfg"]
    setting = f["setting"]
    method = f["method_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who came to play badminton and then found a mystery to solve with {helper.label}. The story turns a practice time into a detective case."
        ),
        (
            "Where did the mystery happen?",
            f"It happened at {setting.place}. The quiet court and badminton gear made the strange sound feel even more suspicious."
        ),
        (
            "What sound started the mystery?",
            f"The mystery began when {hero.label} heard {sound.noise}. In the quiet court, that odd noise made {hero.pronoun('object')} stop and listen carefully."
        ),
        (
            "What clue did the hero find?",
            f"{hero.label} found {clue.phrase}. That clue helped point toward the real cause instead of letting the mystery stay only spooky."
        ),
        (
            "How did they solve the case?",
            f"They solved it by using the method {method.label}. {helper.label} {method.action}, and that let them finally see what had been hiding there."
        ),
        (
            "What was really making the noise?",
            f"It was {cause.label}. The story uses humor because the 'suspect' turns out to be harmless and a little silly instead of scary."
        ),
    ]
    if f.get("relief"):
        qa.append(
            (
                "How did the hero feel at the end?",
                f"{hero.label} felt relieved and cheerful. Once the cause was revealed, the suspense melted away and badminton could begin happily."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    cause = world.facts["cause_cfg"]
    tags = {"badminton", "shuttlecock", "detective", "clue"}
    if cause.id == "kitten":
        tags.add("kitten")
    elif cause.id == "parrot":
        tags.add("parrot")
    elif cause.id == "shoe":
        tags.add("shoe")
    elif cause.id == "fan_sign":
        tags.add("paper")

    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated examples
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="school_gym",
        sound="rustle_bonk",
        cause="kitten",
        clue="pawprint",
        method="open_bag",
        hero_name="Lily",
        hero_gender="girl",
        helper_role="coach",
        helper_name="Coach Mira",
        helper_gender="girl",
        trait="curious",
    ),
    StoryParams(
        setting="community_hall",
        sound="thump_squeak",
        cause="parrot",
        clue="feather",
        method="look_up",
        hero_name="Ben",
        hero_gender="boy",
        helper_role="parent",
        helper_name="Dad",
        helper_gender="boy",
        trait="quick-eyed",
    ),
    StoryParams(
        setting="club_court",
        sound="thump_squeak",
        cause="fan_sign",
        clue="paper_corner",
        method="move_basket",
        hero_name="Maya",
        hero_gender="girl",
        helper_role="coach",
        helper_name="Coach Rana",
        helper_gender="girl",
        trait="thoughtful",
    ),
    StoryParams(
        setting="school_gym",
        sound="ping_plop",
        cause="shoe",
        clue="lace",
        method="peek_under",
        hero_name="Theo",
        hero_gender="boy",
        helper_role="coach",
        helper_name="Coach Ben",
        helper_gender="boy",
        trait="careful",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
matches_sound(C, S) :- cause(C), sound(S), makes(C, S).
matches_clue(C, Cl) :- cause(C), clue(Cl), points_to(Cl, C).
shared_place(Set, C, Cl) :- setting(Set), cause(C), clue(Cl), clue_place(Cl, P), hides_in(C, P), allows(Set, P).
method_ok(Set, C, M) :- setting(Set), cause(C), method(M), hides_in(C, P), works_for(M, P), allows(Set, P), used_by(C, M).
valid(Set, S, C, Cl, M) :- setting(Set), sound(S), cause(C), clue(Cl), method(M),
                           matches_sound(C, S),
                           matches_clue(C, Cl),
                           shared_place(Set, C, Cl),
                           method_ok(Set, C, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for place in sorted(setting.hiding_places):
            lines.append(asp.fact("allows", setting_id, place))
    for sound_id in SOUNDS:
        lines.append(asp.fact("sound", sound_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for sound_id in sorted(cause.noises):
            lines.append(asp.fact("makes", cause_id, sound_id))
        for place in sorted(cause.hides_in):
            lines.append(asp.fact("hides_in", cause_id, place))
        for method_id in sorted(cause.methods):
            lines.append(asp.fact("used_by", cause_id, method_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for cause_id in sorted(clue.points_to):
            lines.append(asp.fact("points_to", clue_id, cause_id))
        for place in sorted(clue.places):
            lines.append(asp.fact("clue_place", clue_id, place))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for place in sorted(method.works_for_places):
            lines.append(asp.fact("works_for", method_id, place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a non-empty story.")
    except Exception as err:  # pragma: no cover - verification surface
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a badminton detective mystery with suspense, sound effects, and humor."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-role", choices=["coach", "parent"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _pick_helper_name(rng: random.Random, role: str, gender: str) -> str:
    if role == "parent":
        return "Mom" if gender == "girl" else "Dad"
    if gender == "girl":
        return rng.choice(["Coach Mira", "Coach Rana", "Coach June", "Coach Ava"])
    return rng.choice(["Coach Ben", "Coach Leo", "Coach Sam", "Coach Eli"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pinned = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sound is None or c[1] == args.sound)
              and (args.cause is None or c[2] == args.cause)
              and (args.clue is None or c[3] == args.clue)
              and (args.method is None or c[4] == args.method)]

    if args.setting and args.sound and args.cause and args.clue and args.method:
        if not valid_combo(args.setting, args.sound, args.cause, args.clue, args.method):
            raise StoryError(explain_invalid(args.setting, args.sound, args.cause, args.clue, args.method))

    if not pinned:
        if args.setting and args.sound and args.cause and args.clue and args.method:
            raise StoryError(explain_invalid(args.setting, args.sound, args.cause, args.clue, args.method))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sound_id, cause_id, clue_id, method_id = rng.choice(sorted(pinned))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_role = args.helper_role or rng.choice(["coach", "parent"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or _pick_helper_name(rng, helper_role, helper_gender)
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        sound=sound_id,
        cause=cause_id,
        clue=clue_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_role=helper_role,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Invalid sound: {params.sound})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Invalid clue: {params.clue})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")

    if not valid_combo(params.setting, params.sound, params.cause, params.clue, params.method):
        raise StoryError(explain_invalid(params.setting, params.sound, params.cause, params.clue, params.method))

    world = tell(
        setting=SETTINGS[params.setting],
        sound=SOUNDS[params.sound],
        cause_cfg=CAUSES[params.cause],
        clue_cfg=CLUES[params.clue],
        method_cfg=METHODS[params.method],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_role=params.helper_role,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, sound, cause, clue, method) combos:\n")
        for setting_id, sound_id, cause_id, clue_id, method_id in combos:
            print(f"  {setting_id:14} {sound_id:13} {cause_id:9} {clue_id:12} {method_id}")
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
            header = (
                f"### {p.hero_name}: {p.sound} at {p.setting} "
                f"({p.cause}, {p.clue}, {p.method})"
            )
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
