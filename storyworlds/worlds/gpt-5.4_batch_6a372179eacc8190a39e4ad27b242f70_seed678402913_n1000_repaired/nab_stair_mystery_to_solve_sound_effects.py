#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nab_stair_mystery_to_solve_sound_effects.py
======================================================================

A standalone story world for a child-friendly whodunit: something small goes
missing in a house, a strange sound comes from the stair, and a pair of young
detectives follow concrete clues to figure out who nabbed it.

This world models:
- typed entities with physical meters and emotional memes
- a small causal chain: missing object -> clue search -> suspect narrowing
- a reasonableness gate over item / culprit / sound / hiding place
- a matching inline ASP twin for parity checking
- three QA sets grounded in world state, not by parsing the rendered prose

Run it
------
    python storyworlds/worlds/gpt-5.4/nab_stair_mystery_to_solve_sound_effects.py
    python storyworlds/worlds/gpt-5.4/nab_stair_mystery_to_solve_sound_effects.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/nab_stair_mystery_to_solve_sound_effects.py --all --qa
    python storyworlds/worlds/gpt-5.4/nab_stair_mystery_to_solve_sound_effects.py --trace
    python storyworlds/worlds/gpt-5.4/nab_stair_mystery_to_solve_sound_effects.py --json
    python storyworlds/worlds/gpt-5.4/nab_stair_mystery_to_solve_sound_effects.py --verify
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
    traits: tuple = field(default_factory=tuple)
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        animal = {"puppy", "kitten"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class MysteryCase:
    id: str
    opening: str
    place: str
    stair_phrase: str
    ending_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    owner_text: str
    appeal_tags: set[str] = field(default_factory=set)
    sound_tags: set[str] = field(default_factory=set)
    clue_mark: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    type: str
    phrase: str
    motive: str
    likes: set[str] = field(default_factory=set)
    makes: set[str] = field(default_factory=set)
    can_reach: set[str] = field(default_factory=set)
    trail: str = ""
    found_pose: str = ""
    apology_style: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundCue:
    id: str
    text: str
    echo: str
    means: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingSpot:
    id: str
    label: str
    phrase: str
    reachable_by: set[str] = field(default_factory=set)
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_mark_missing(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["taken"] < THRESHOLD:
        return []
    sig = ("missing", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] += 1
    for kid_id in ("detective_a", "detective_b"):
        if kid_id in world.entities:
            world.get(kid_id).memes["concern"] += 1
    return []


def _r_hear_sound(world: World) -> list[str]:
    room = world.get("hall")
    if room.meters["sound_heard"] < THRESHOLD:
        return []
    sig = ("sound", room.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid_id in ("detective_a", "detective_b"):
        if kid_id in world.entities:
            world.get(kid_id).memes["curiosity"] += 1
    return []


def _r_follow_trail(world: World) -> list[str]:
    hall = world.get("hall")
    culprit = world.get("culprit")
    if hall.meters["searching"] < THRESHOLD or culprit.meters["left_trail"] < THRESHOLD:
        return []
    sig = ("trail", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hall.meters["trail_seen"] += 1
    return []


def _r_solve(world: World) -> list[str]:
    hall = world.get("hall")
    if hall.meters["trail_seen"] < THRESHOLD or hall.meters["sound_heard"] < THRESHOLD:
        return []
    sig = ("solved", hall.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hall.meters["solved"] += 1
    for kid_id in ("detective_a", "detective_b"):
        if kid_id in world.entities:
            world.get(kid_id).memes["pride"] += 1
            world.get(kid_id).memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mark_missing", apply=_r_mark_missing),
    Rule(name="hear_sound", apply=_r_hear_sound),
    Rule(name="follow_trail", apply=_r_follow_trail),
    Rule(name="solve", apply=_r_solve),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
        now = len(world.fired)
        if world.facts.get("_last_fired_count") != now:
            changed = changed or (world.facts.get("_last_fired_count") is None)
            world.facts["_last_fired_count"] = now


def item_matches_culprit(item: MissingItem, culprit: Culprit) -> bool:
    return bool(item.appeal_tags & culprit.likes)


def sound_matches(item: MissingItem, culprit: Culprit, sound: SoundCue) -> bool:
    return sound.id in culprit.makes and bool(item.sound_tags & sound.fits)


def spot_matches(culprit: Culprit, spot: HidingSpot) -> bool:
    return spot.id in culprit.can_reach and culprit.id in spot.reachable_by


def valid_combo(item: MissingItem, culprit: Culprit, sound: SoundCue, spot: HidingSpot) -> bool:
    return item_matches_culprit(item, culprit) and sound_matches(item, culprit, sound) and spot_matches(culprit, spot)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for item_id, item in ITEMS.items():
        for culprit_id, culprit in CULPRITS.items():
            for sound_id, sound in SOUNDS.items():
                for spot_id, spot in SPOTS.items():
                    if valid_combo(item, culprit, sound, spot):
                        combos.append((item_id, culprit_id, sound_id, spot_id))
    return combos


def explain_rejection(item: MissingItem, culprit: Culprit, sound: SoundCue, spot: HidingSpot) -> str:
    if not item_matches_culprit(item, culprit):
        return (
            f"(No story: {culprit.label} is not a plausible one to nab {item.phrase}. "
            f"The culprit's motive should fit the missing thing.)"
        )
    if not sound_matches(item, culprit, sound):
        return (
            f"(No story: {sound.text} does not fit both {culprit.label}'s movement "
            f"and the kind of object that vanished.)"
        )
    if not spot_matches(culprit, spot):
        return (
            f"(No story: {culprit.label} cannot sensibly end up at {spot.phrase}. "
            f"Pick a hiding place that culprit could really reach from the stair.)"
        )
    return "(No story: that combination does not make a sensible mystery.)"


def choose_false_suspect(culprit_id: str) -> str:
    options = [s for s in SUSPECT_ORDER if s != culprit_id]
    return options[0]


def do_nab(world: World) -> None:
    item = world.get("item")
    culprit = world.get("culprit")
    hall = world.get("hall")
    item.meters["taken"] += 1
    culprit.meters["has_item"] += 1
    culprit.meters["left_trail"] += 1
    hall.meters["sound_heard"] += 1
    propagate(world)


def opening_beat(world: World, case: MysteryCase, a: Entity, b: Entity, item: MissingItem) -> None:
    world.say(
        f"{case.opening} {a.id} and {b.id} were on the rug in {case.place}, pretending to be famous detectives."
    )
    world.say(
        f"Between them sat {item.owner_text} -- {item.phrase} -- and for a while everything felt tidy and ordinary."
    )


def disappearance_beat(world: World, a: Entity, b: Entity, item: MissingItem, sound: SoundCue, case: MysteryCase) -> None:
    world.say(
        f"Then {b.id} blinked. {item.phrase[0].upper()}{item.phrase[1:]} was gone."
    )
    world.say(
        f'At that exact moment, a sound floated from {case.stair_phrase}: "{sound.text}! {sound.echo}!"'
    )
    world.say(
        f"{a.id} sat up straight. \"A clue,\" {a.pronoun()} whispered. \"Somebody tried to nab it and hurry away.\""
    )


def investigation_beat(
    world: World,
    a: Entity,
    b: Entity,
    culprit: Culprit,
    item: MissingItem,
    sound: SoundCue,
    spot: HidingSpot,
    false_suspect: str,
) -> None:
    hall = world.get("hall")
    hall.meters["searching"] += 1
    propagate(world)
    world.say(
        f"{b.id} put a finger to {b.pronoun('possessive')} lips. \"Let's not guess too fast,\" {b.pronoun()} said. "
        f"\"We need the sound and the trail.\""
    )
    world.say(
        f"Together they tiptoed to the stair and found {culprit.trail}. That made the mystery feel smaller and sharper."
    )
    suspect_label = CULPRITS[false_suspect].label
    world.say(
        f"At first {a.id} wondered if {suspect_label} had done it, but the clue did not fit. "
        f"{sound.means}, and the trail matched {culprit.label} instead."
    )
    world.say(
        f"They followed the little signs all the way to {spot.phrase} near {case_ending_hint(world)}."
    )


def case_ending_hint(world: World) -> str:
    case = world.facts["case"]
    return case.ending_place


def reveal_beat(world: World, a: Entity, b: Entity, culprit: Culprit, item: MissingItem, spot: HidingSpot) -> None:
    hall = world.get("hall")
    hall.meters["reached_spot"] += 1
    propagate(world)
    world.say(
        f"There was the answer: {spot.reveal} {culprit.found_pose}, with {item.phrase} beside {culprit.pronoun('object')}."
    )
    world.say(
        f'"Aha!" said {a.id}. "{culprit.label.capitalize()} is the one who nabbed it."'
    )
    world.say(
        f"{b.id} smiled. \"Not a bad thief,\" {b.pronoun()} said, \"just a {culprit.label} with {culprit.motive}.\""
    )


def resolution_beat(world: World, a: Entity, b: Entity, culprit: Entity, item: Entity, helper: Entity, case: MysteryCase) -> None:
    culprit.meters["has_item"] = 0.0
    item.meters["returned"] += 1
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["concern"] = 0.0
    helper.memes["pleased"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came over, laughed softly, and took the mystery seriously all the same."
    )
    world.say(
        f'{helper.pronoun().capitalize()} helped put {item.phrase} back where it belonged and said, '
        f'"Case closed. The best detectives look, listen, and think before they blame."'
    )
    world.say(
        f"{a.id} and {b.id} stood at the bottom of the stair like tiny whodunit heroes, proud that they had solved it together."
    )


def tell(
    case: MysteryCase,
    item_cfg: MissingItem,
    culprit_cfg: Culprit,
    sound_cfg: SoundCue,
    spot_cfg: HidingSpot,
    detective_a_name: str = "Mina",
    detective_a_gender: str = "girl",
    detective_b_name: str = "Owen",
    detective_b_gender: str = "boy",
    helper_type: str = "mother",
) -> World:
    world = World()
    a = world.add(Entity(id="detective_a", kind="character", type=detective_a_gender, label=detective_a_name, phrase=detective_a_name, role="detective"))
    b = world.add(Entity(id="detective_b", kind="character", type=detective_b_gender, label=detective_b_name, phrase=detective_b_name, role="detective"))
    a.attrs["name"] = detective_a_name
    b.attrs["name"] = detective_b_name
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the parent", phrase="the parent", role="helper"))
    culprit = world.add(Entity(id="culprit", kind="character", type=culprit_cfg.type, label=culprit_cfg.label, phrase=culprit_cfg.phrase, role="culprit", tags=set(culprit_cfg.tags)))
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label, phrase=item_cfg.phrase, role="item", tags=set(item_cfg.tags)))
    hall = world.add(Entity(id="hall", kind="thing", type="hall", label=case.place, phrase=case.place))
    spot = world.add(Entity(id="spot", kind="thing", type="spot", label=spot_cfg.label, phrase=spot_cfg.phrase, tags=set(spot_cfg.tags)))

    a.memes["wonder"] = 1
    b.memes["wonder"] = 1

    opening_beat(world, case, a, b, item_cfg)
    world.para()

    do_nab(world)
    disappearance_beat(world, a, b, item_cfg, sound_cfg, case)
    world.para()

    false_suspect = choose_false_suspect(culprit_cfg.id)
    investigation_beat(world, a, b, culprit_cfg, item_cfg, sound_cfg, spot_cfg, false_suspect)
    world.para()

    reveal_beat(world, a, b, culprit_cfg, item_cfg, spot_cfg)
    world.para()

    resolution_beat(world, a, b, culprit, item, helper, case)

    world.facts.update(
        case=case,
        item_cfg=item_cfg,
        culprit_cfg=culprit_cfg,
        sound_cfg=sound_cfg,
        spot_cfg=spot_cfg,
        detective_a=a,
        detective_b=b,
        helper=helper,
        culprit=culprit,
        item=item,
        spot=spot,
        false_suspect=false_suspect,
        solved=hall.meters["solved"] >= THRESHOLD,
        returned=item.meters["returned"] >= THRESHOLD,
    )
    return world


CASES = {
    "rainy_hall": MysteryCase(
        id="rainy_hall",
        opening="On a drizzly afternoon",
        place="the front hall",
        stair_phrase="the wooden stair",
        ending_place="the coat hooks",
        tags={"mystery", "stair"},
    ),
    "lamp_landing": MysteryCase(
        id="lamp_landing",
        opening="On a quiet evening",
        place="the lamp-lit hallway",
        stair_phrase="the carpeted stair",
        ending_place="the upstairs landing",
        tags={"mystery", "stair"},
    ),
    "sunny_entry": MysteryCase(
        id="sunny_entry",
        opening="On a bright afternoon",
        place="the sunny entry",
        stair_phrase="the narrow stair",
        ending_place="the little window seat",
        tags={"mystery", "stair"},
    ),
}

ITEMS = {
    "jam_tart": MissingItem(
        id="jam_tart",
        label="jam tart",
        phrase="a jam tart on a blue plate",
        owner_text="a snack they had been promised after tidy-up time",
        appeal_tags={"food"},
        sound_tags={"plate", "clatter"},
        clue_mark="a shiny red smear",
        tags={"food", "tart"},
    ),
    "jingle_bell": MissingItem(
        id="jingle_bell",
        label="jingle bell",
        phrase="a tiny silver jingle bell from the craft basket",
        owner_text="their afternoon craft treasure",
        appeal_tags={"shiny", "toy"},
        sound_tags={"jingle", "light"},
        clue_mark="a thread with silver glitter",
        tags={"bell", "craft"},
    ),
    "cookie_ribbon": MissingItem(
        id="cookie_ribbon",
        label="cookie ribbon",
        phrase="a cookie tied with a red ribbon for a surprise gift",
        owner_text="a treat meant for visiting Grandma",
        appeal_tags={"food", "ribbon"},
        sound_tags={"rustle", "light"},
        clue_mark="a twist of red ribbon",
        tags={"cookie", "ribbon"},
    ),
}

CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        label="the puppy",
        type="puppy",
        phrase="the puppy",
        motive="a nose full of snack-smells",
        likes={"food"},
        makes={"clatter", "scrabble"},
        can_reach={"under_bench", "behind_curtain"},
        trail="wet pawprints and one tiny lick-mark",
        found_pose="wagging so hard that its whole back end wriggled",
        apology_style="tail-wag",
        tags={"puppy", "pet"},
    ),
    "kitten": Culprit(
        id="kitten",
        label="the kitten",
        type="kitten",
        phrase="the kitten",
        motive="bright eyes for anything shiny or fluttery",
        likes={"shiny", "toy", "ribbon"},
        makes={"jingle", "rustle"},
        can_reach={"window_seat", "behind_curtain"},
        trail="a curl of fur and a tiny batting mark",
        found_pose="pouncing at shadows with very innocent-looking eyes",
        apology_style="purr",
        tags={"kitten", "pet"},
    ),
    "little_brother": Culprit(
        id="little_brother",
        label="the little brother",
        type="boy",
        phrase="the little brother",
        motive="a wish to copy the big children and join the fun",
        likes={"food", "toy"},
        makes={"thump", "rustle"},
        can_reach={"under_bench", "upstairs_box"},
        trail="crumbs and one sock half on, half off",
        found_pose="trying to look hidden while two toes peeked out",
        apology_style="giggle",
        tags={"sibling", "boy"},
    ),
}

SOUNDS = {
    "clatter": SoundCue(
        id="clatter",
        text="CLATTER",
        echo="skitter-skitter",
        means="A plate had bumped somewhere in a hurry",
        fits={"plate", "clatter"},
        tags={"sound", "plate"},
    ),
    "jingle": SoundCue(
        id="jingle",
        text="JINGLE",
        echo="ting-ting",
        means="Something small and shiny had bounced or swung",
        fits={"jingle", "light"},
        tags={"sound", "bell"},
    ),
    "rustle": SoundCue(
        id="rustle",
        text="RUSTLE",
        echo="swish-swish",
        means="Ribbon or paper had brushed and fluttered while someone moved",
        fits={"rustle", "light"},
        tags={"sound", "ribbon"},
    ),
    "thump": SoundCue(
        id="thump",
        text="THUMP",
        echo="bump-bump",
        means="Little feet had gone up or down the stair in a hurry",
        fits={"light"},
        tags={"sound", "steps"},
    ),
    "scrabble": SoundCue(
        id="scrabble",
        text="SCRABBLE",
        echo="tik-tik-tik",
        means="Quick claws had hurried over wood",
        fits={"plate", "clatter"},
        tags={"sound", "claws"},
    ),
}

SPOTS = {
    "under_bench": HidingSpot(
        id="under_bench",
        label="bench",
        phrase="the bench under the stair",
        reachable_by={"puppy", "little_brother"},
        reveal="Under the bench, in a pocket of shadow,",
        tags={"under", "stair"},
    ),
    "behind_curtain": HidingSpot(
        id="behind_curtain",
        label="curtain",
        phrase="the long hall curtain by the stair",
        reachable_by={"puppy", "kitten"},
        reveal="Behind the curtain, with one edge twitching,",
        tags={"curtain", "stair"},
    ),
    "window_seat": HidingSpot(
        id="window_seat",
        label="window seat",
        phrase="the window seat halfway up the stair landing",
        reachable_by={"kitten"},
        reveal="On the window seat, where the light made everything gleam,",
        tags={"window", "landing"},
    ),
    "upstairs_box": HidingSpot(
        id="upstairs_box",
        label="box",
        phrase="the toy box at the top of the stair",
        reachable_by={"little_brother"},
        reveal="By the toy box at the top step,",
        tags={"box", "stair"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Tess", "Ivy", "Nora", "Poppy", "June", "Ruby"]
BOY_NAMES = ["Owen", "Theo", "Max", "Ben", "Eli", "Finn", "Sam", "Leo"]
SUSPECT_ORDER = ["puppy", "kitten", "little_brother"]


@dataclass
class StoryParams:
    case: str
    item: str
    culprit: str
    sound: str
    spot: str
    detective_a: str
    detective_a_gender: str
    detective_b: str
    detective_b_gender: str
    helper: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bell": [
        (
            "Why does a jingle bell make a bright sound?",
            "A jingle bell has a tiny loose piece inside it. When the bell moves, that piece taps the metal sides and makes a ringing sound.",
        )
    ],
    "puppy": [
        (
            "Why do puppies follow food smells?",
            "Puppies have strong noses, so a good smell can pull them across a room very fast. That is why snacks should be kept where pets cannot reach them.",
        )
    ],
    "kitten": [
        (
            "Why do kittens chase shiny or fluttery things?",
            "Kittens love quick little movements and glints of light, so ribbon and bells can seem extra exciting. They often bat first and think later.",
        )
    ],
    "sibling": [
        (
            "Why might a little child take something without asking?",
            "A little child may want to copy older children or join the game. They still need help learning to ask first.",
        )
    ],
    "sound": [
        (
            "Why can sounds help solve a mystery?",
            "Different sounds come from different actions and materials. If you listen carefully, a sound can tell you what moved and how it moved.",
        )
    ],
    "stair": [
        (
            "Why do stairs make clues easier to hear?",
            "Stairs can creak, thump, or echo when someone goes up or down them. That makes movement easier to notice.",
        )
    ],
    "trail": [
        (
            "What is a trail clue?",
            "A trail clue is a little sign someone leaves behind, like crumbs, fur, or pawprints. Small clues can point the way to a big answer.",
        )
    ],
    "detective": [
        (
            "What does a good detective do first?",
            "A good detective looks, listens, and thinks before blaming anyone. Careful clues are better than wild guesses.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sound", "stair", "trail", "detective", "bell", "puppy", "kitten", "sibling"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["detective_a"].attrs["name"]
    b = f["detective_b"].attrs["name"]
    item = f["item_cfg"]
    case = f["case"]
    culprit = f["culprit_cfg"]
    sound = f["sound_cfg"]
    return [
        f'Write a child-friendly whodunit where two children hear "{sound.text}!" on a stair and solve who tried to nab {item.phrase}.',
        f"Tell a Mystery to Solve story with sound effects in which {a} and {b} follow clues through {case.place} and discover that {culprit.label} took the missing thing.",
        f'Write a gentle detective story for ages 3 to 5 that includes the words "nab" and "stair", uses a sound effect, and ends with the mystery solved kindly.',
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two young detectives"
    if a.type == "boy" and b.type == "boy":
        return "two young detectives"
    return "two young detectives"


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["detective_a"]
    b = f["detective_b"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    culprit_cfg = f["culprit_cfg"]
    sound_cfg = f["sound_cfg"]
    spot_cfg = f["spot_cfg"]
    false_suspect = CULPRITS[f["false_suspect"]]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.attrs['name']} and {b.attrs['name']}, who act like little detectives. {helper.label_word.capitalize()} helps at the end, but the children solve the mystery first.",
        ),
        (
            "What mystery did they have to solve?",
            f"They had to find out who nabbed {item_cfg.phrase}. The mystery began the moment it disappeared and a sound came from the stair.",
        ),
        (
            f'What sound did they hear, and why did it matter?',
            f'They heard "{sound_cfg.text}! {sound_cfg.echo}!" from the stair. That sound mattered because it told them something had moved in a particular way, so they could match the noise to the right suspect.',
        ),
        (
            "Why did they stop blaming the first suspect?",
            f"They first wondered about {false_suspect.label}, but the clues did not fit. {sound_cfg.means}, and the trail they found matched {culprit_cfg.label} instead.",
        ),
        (
            "How did they solve the mystery?",
            f"They listened to the sound, looked for a trail, and followed those clues to {spot_cfg.phrase}. That careful work led them straight to {culprit_cfg.label} and the missing item.",
        ),
        (
            "Was the culprit mean?",
            f"No. {culprit_cfg.label.capitalize()} was not trying to be cruel. The story shows that the culprit acted from {culprit_cfg.motive}, so the ending stays gentle even after the whodunit turn.",
        ),
    ]
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sound", "stair", "trail", "detective"}
    culprit_id = f["culprit_cfg"].id
    item_id = f["item_cfg"].id
    if culprit_id == "puppy":
        tags.add("puppy")
    elif culprit_id == "kitten":
        tags.add("kitten")
    else:
        tags.add("sibling")
    if item_id == "jingle_bell":
        tags.add("bell")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for (name, *_rest) in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        case="rainy_hall",
        item="jam_tart",
        culprit="puppy",
        sound="clatter",
        spot="under_bench",
        detective_a="Mina",
        detective_a_gender="girl",
        detective_b="Owen",
        detective_b_gender="boy",
        helper="mother",
    ),
    StoryParams(
        case="lamp_landing",
        item="jingle_bell",
        culprit="kitten",
        sound="jingle",
        spot="window_seat",
        detective_a="Ruby",
        detective_a_gender="girl",
        detective_b="Theo",
        detective_b_gender="boy",
        helper="father",
    ),
    StoryParams(
        case="sunny_entry",
        item="cookie_ribbon",
        culprit="kitten",
        sound="rustle",
        spot="behind_curtain",
        detective_a="Ivy",
        detective_a_gender="girl",
        detective_b="Ben",
        detective_b_gender="boy",
        helper="mother",
    ),
    StoryParams(
        case="rainy_hall",
        item="cookie_ribbon",
        culprit="little_brother",
        sound="thump",
        spot="upstairs_box",
        detective_a="June",
        detective_a_gender="girl",
        detective_b="Max",
        detective_b_gender="boy",
        helper="father",
    ),
]


ASP_RULES = r"""
likes_item(C, I) :- culprit(C), item(I), appeal(C, T), item_appeal(I, T).
sound_match(C, I, S) :- culprit(C), item(I), sound(S), makes(C, S),
                        item_sound(I, T), sound_fit(S, T).
spot_match(C, P) :- culprit(C), spot(P), can_reach(C, P), spot_reachable(P, C).

valid(I, C, S, P) :- likes_item(C, I), sound_match(C, I, S), spot_match(C, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.appeal_tags):
            lines.append(asp.fact("item_appeal", iid, tag))
        for tag in sorted(item.sound_tags):
            lines.append(asp.fact("item_sound", iid, tag))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for tag in sorted(culprit.likes):
            lines.append(asp.fact("appeal", cid, tag))
        for sound in sorted(culprit.makes):
            lines.append(asp.fact("makes", cid, sound))
        for spot in sorted(culprit.can_reach):
            lines.append(asp.fact("can_reach", cid, spot))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        for tag in sorted(sound.fits):
            lines.append(asp.fact("sound_fit", sid, tag))
    for pid, spot in SPOTS.items():
        lines.append(asp.fact("spot", pid))
        for cid in sorted(spot.reachable_by):
            lines.append(asp.fact("spot_reachable", pid, cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a gentle whodunit with a stair clue and sound effects."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_item = ITEMS.get(args.item) if args.item else None
    explicit_culprit = CULPRITS.get(args.culprit) if args.culprit else None
    explicit_sound = SOUNDS.get(args.sound) if args.sound else None
    explicit_spot = SPOTS.get(args.spot) if args.spot else None

    if explicit_item and explicit_culprit and explicit_sound and explicit_spot:
        if not valid_combo(explicit_item, explicit_culprit, explicit_sound, explicit_spot):
            raise StoryError(explain_rejection(explicit_item, explicit_culprit, explicit_sound, explicit_spot))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.sound is None or combo[2] == args.sound)
        and (args.spot is None or combo[3] == args.spot)
    ]
    if not combos:
        item = explicit_item or next(iter(ITEMS.values()))
        culprit = explicit_culprit or next(iter(CULPRITS.values()))
        sound = explicit_sound or next(iter(SOUNDS.values()))
        spot = explicit_spot or next(iter(SPOTS.values()))
        raise StoryError(explain_rejection(item, culprit, sound, spot))

    item_id, culprit_id, sound_id, spot_id = rng.choice(sorted(combos))
    case_id = args.case or rng.choice(sorted(CASES))
    helper = args.helper or rng.choice(["mother", "father"])

    detective_a_gender = rng.choice(["girl", "boy"])
    detective_b_gender = rng.choice(["girl", "boy"])
    detective_a = _pick_name(rng, detective_a_gender)
    detective_b = _pick_name(rng, detective_b_gender, avoid=detective_a)

    return StoryParams(
        case=case_id,
        item=item_id,
        culprit=culprit_id,
        sound=sound_id,
        spot=spot_id,
        detective_a=detective_a,
        detective_a_gender=detective_a_gender,
        detective_b=detective_b,
        detective_b_gender=detective_b_gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"(Unknown case: {params.case})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Unknown sound: {params.sound})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.helper not in {"mother", "father"}:
        raise StoryError(f"(Unknown helper type: {params.helper})")

    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    sound = SOUNDS[params.sound]
    spot = SPOTS[params.spot]
    if not valid_combo(item, culprit, sound, spot):
        raise StoryError(explain_rejection(item, culprit, sound, spot))

    world = tell(
        case=CASES[params.case],
        item_cfg=item,
        culprit_cfg=culprit,
        sound_cfg=sound,
        spot_cfg=spot,
        detective_a_name=params.detective_a,
        detective_a_gender=params.detective_a_gender,
        detective_b_name=params.detective_b,
        detective_b_gender=params.detective_b_gender,
        helper_type=params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, culprit, sound, spot) combos:\n")
        for item_id, culprit_id, sound_id, spot_id in combos:
            print(f"  {item_id:14} {culprit_id:15} {sound_id:10} {spot_id}")
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
            header = f"### {p.item} / {p.culprit} / {p.sound} / {p.spot}"
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
