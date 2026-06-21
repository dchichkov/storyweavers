#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/might_hiney_antique_dialogue_rhyming_story.py
=========================================================================

A standalone story world for a small rhyming tale about a child who spots an
antique treasure up high, thinks "I might reach it," and must choose whether to
climb or ask for help. The seed words "might", "hiney", and "antique" are built
into the prose, and dialogue drives every variant.

The world model tracks physical state (height, wobble, slipping, bumps) and
emotional state (desire, caution, fear, relief, pride). The ending changes
because the simulated choice changes:

* a grown-up helper can avert the climb entirely;
* an older sibling plus a sturdy stool can lead to a safe reach;
* a shakier plan can end with a gentle bump on the hiney and a wiser finish.

Run it
------
    python storyworlds/worlds/gpt-5.4/might_hiney_antique_dialogue_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/might_hiney_antique_dialogue_rhyming_story.py --antique music_box --perch chair --helper sibling
    python storyworlds/worlds/gpt-5.4/might_hiney_antique_dialogue_rhyming_story.py --perch rolling_chair
    python storyworlds/worlds/gpt-5.4/might_hiney_antique_dialogue_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/might_hiney_antique_dialogue_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
import io
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Room:
    id: str
    place: str
    shelf: str
    glow: str
    rug: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Antique:
    id: str
    label: str
    phrase: str
    sound: str
    reach_need: int
    fragile: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    stability: int
    rolling: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    phrase: str
    support: int
    sense: int
    adult: bool = False
    relation_word: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        clone = World(self.room)
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    perch = world.entities.get("perch")
    if child is None or perch is None:
        return out
    if child.meters["climbing"] < THRESHOLD:
        return out
    if perch.meters["wobble"] < THRESHOLD:
        return out
    sig = ("fear_from_wobble", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    perch = world.entities.get("perch")
    if child is None or perch is None:
        return out
    if child.meters["risk"] < THRESHOLD:
        return out
    sig = ("fall", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["slipped"] += 1
    child.meters["bumped_hiney"] += 1
    child.memes["fear"] += 1
    out.append("__slip__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="fall", tag="physical", apply=_r_fall),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for item in produced:
            world.say(item)
    return produced


def base_reach(perch: Perch, helper: HelperKind) -> int:
    return perch.stability + helper.support


def valid_combo(antique: Antique, perch: Perch, helper: HelperKind) -> bool:
    if helper.sense < SENSE_MIN:
        return False
    if helper.adult:
        return True
    if perch.rolling:
        return False
    return base_reach(perch, helper) >= antique.reach_need


def outcome_of(params: "StoryParams") -> str:
    antique = ANTIQUES[params.antique]
    perch = PERCHES[params.perch]
    helper = HELPERS[params.helper]
    if helper.adult:
        return "averted"
    return "safe" if base_reach(perch, helper) >= antique.reach_need + params.delay else "slip"


def explain_rejection(antique: Antique, perch: Perch, helper: HelperKind) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: asking {helper.label} is too weak a safety plan here "
            f"(sense={helper.sense} < {SENSE_MIN}). Pick a wiser helper.)"
        )
    if helper.adult:
        return "(No story: this combination should have been allowed.)"
    if perch.rolling:
        return (
            f"(No story: {perch.phrase} is too wobbly to climb while reaching for "
            f"{antique.phrase}. The world refuses rolling furniture as a plan.)"
        )
    return (
        f"(No story: {helper.label} plus {perch.label} is not enough to reach "
        f"{antique.phrase} safely. Pick a sturdier perch or a grown-up helper.)"
    )


def predict_attempt(antique: Antique, perch: Perch, helper: HelperKind, delay: int) -> dict:
    score = base_reach(perch, helper)
    return {
        "score": score,
        "need": antique.reach_need,
        "will_slip": score < antique.reach_need + delay,
        "will_wobble": perch.stability <= 1 or delay > 0,
    }


def introduce(world: World, child: Entity, room: Room, antique: Antique) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"In {room.place}, where {room.glow}, {child.id} looked up with bright-eyed delight. "
        f"On {room.shelf} sat {antique.phrase}, quiet and warm in the light."
    )
    world.say(
        f'"Oh, I might hear {antique.sound} if I hold it just right," said {child.id}. '
        f'"That antique treasure would make my game sparkle tonight."'
    )


def spot_perch(world: World, child: Entity, perch: Perch) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{child.pronoun('subject').capitalize()} glanced at {perch.phrase} and gave a small, hopeful blink. "
        f'"If I stand up there for one tiny try, I might be up there quicker than you think."'
    )


def warning(world: World, child: Entity, helper_ent: Entity, helper_kind: HelperKind, antique: Antique, perch: Perch) -> None:
    child.memes["caution_heard"] += 1
    if helper_kind.adult:
        line = (
            f'"Sweet pea, that antique {antique.label} is old and slight. '
            f'Keep your feet and your hiney down low; I will help the safe way tonight."'
        )
    else:
        line = (
            f'"Wait," said {helper_ent.id}. "That {perch.label} may wobble, and that antique {antique.label} is light. '
            f'Keep your brave little toes and your hiney down low, or the room could turn scary tonight."'
        )
    world.say(line)


def ask_first(world: World, child: Entity, parent: Entity, antique: Antique) -> None:
    child.memes["trust"] += 1
    parent.memes["care"] += 1
    world.say(
        f'{child.id} looked up and then back down. "So I might ask first instead of climb?" '
        f'{parent.label_word.capitalize()} smiled. "That is a careful little rhyme."'
    )
    world.say(
        f"{parent.id} stretched up high, brought down {antique.phrase}, and set it on a folded cloth. "
        f"The old thing stayed safe, and the room stayed calm, with no scrape, no crash, no wrath."
    )


def start_climb(world: World, child: Entity, helper_ent: Entity, perch_ent: Entity, perch: Perch, helper_kind: HelperKind) -> None:
    child.meters["climbing"] += 1
    child.memes["bravery"] += 1
    helper_ent.memes["care"] += 1
    if perch.stability <= 1:
        perch_ent.meters["wobble"] += 1
    world.say(
        f'{child.id} set one foot on {perch.phrase}. "{helper_ent.id}, hold still and tight." '
        f'"I only might need one more inch," {child.pronoun()} said, reaching into the light.'
    )
    propagate(world, narrate=False)


def safe_reach(world: World, child: Entity, helper_ent: Entity, antique_ent: Entity, antique: Antique) -> None:
    antique_ent.meters["lowered"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper_ent.memes["pride"] += 1
    world.say(
        f"{helper_ent.id} steadied the perch, and {child.id} moved slow, not fast and flighty. "
        f"Soon {child.pronoun('possessive')} fingers reached {antique.phrase}, gentle, careful, and mighty."
    )
    world.say(
        f'"Got it!" laughed {child.id}. "My feet stayed steady, my hands stayed light." '
        f'"And best of all," said {helper_ent.id}, "your hiney stayed far from a bump tonight."'
    )


def slip_attempt(world: World, child: Entity, helper_ent: Entity, parent: Entity, antique: Antique, perch_ent: Entity) -> None:
    perch_ent.meters["wobble"] += 1
    child.meters["risk"] += 1
    propagate(world, narrate=False)
    child.memes["fear"] += 1
    helper_ent.memes["fear"] += 1
    world.say(
        f"But the perch gave a wiggle and a wriggle beneath the reaching light. "
        f'"Whoa!" cried {child.id}, and down {child.pronoun()} slid before {child.pronoun()} could hold on tight.'
    )
    world.say(
        f"{child.id} landed with a soft little thump on {world.room.rug} and rubbed {child.pronoun('possessive')} hiney. "
        f'Tears shone up fast. "{antique.phrase.capitalize()} is still up there, and now I feel all whiny."'
    )
    parent.memes["care"] += 1
    world.say(
        f'{parent.label_word.capitalize()} hurried in at once. "You are safe, and that is the first delight," '
        f'{parent.pronoun()} said, gathering {child.pronoun("object")} close and upright.'
    )


def after_safe(world: World, child: Entity, helper_ent: Entity, parent: Entity, antique: Antique, helper_kind: HelperKind) -> None:
    parent.memes["care"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} came over smiling. "You moved with care, and care was right. '
        f'Old things last longer when small hands go slowly and ask for help in the light."'
    )
    if helper_kind.adult:
        world.say(
            f'{child.id} nodded. "I might ask first next time too." '
            f'"That is how careful children grow," said {parent.id}, "bright by bright."'
        )
    else:
        world.say(
            f'{helper_ent.id} grinned. "Teamwork helped." {child.id} nodded. '
            f'"I might still play softly," {child.pronoun()} said, "and keep the antique bright."'
        )


def after_slip(world: World, child: Entity, parent: Entity, antique: Antique, antique_ent: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    antique_ent.meters["lowered"] += 1
    world.say(
        f'{parent.id} reached the shelf with grown-up arms and brought down {antique.phrase} the proper way. '
        f'"Looking is lovely," {parent.pronoun()} said, "but climbing in a hurry can spoil the play."'
    )
    world.say(
        f'{child.id} sniffed, then gave a brave small nod. "My hiney says I should not rush so high." '
        f'"That is a smart little lesson," said {parent.id}. "Ask first, and the scary parts pass by."'
    )


def final_image(world: World, child: Entity, antique: Antique, outcome: str) -> None:
    child.memes["joy"] += 1
    if outcome == "slip":
        world.say(
            f"At last {antique.phrase} rested on a cloth where little eyes could spy. "
            f"{child.id} listened to {antique.sound}, feet on the floor, with a wiser, calmer sigh."
        )
    elif outcome == "safe":
        world.say(
            f"Then {child.id} and the others sat by the window, listening to {antique.sound} drift light. "
            f"The antique stayed whole, the rhyme stayed sweet, and the careful ending shone tonight."
        )
    else:
        world.say(
            f"Then {child.id} sat beside the table and listened to {antique.sound} floating low and bright. "
            f"No climb was needed, no hiney was bumped, and the careful choice turned worry into light."
        )


def tell(
    room: Room,
    antique: Antique,
    perch: Perch,
    helper_kind: HelperKind,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_name: str = "Owen",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(room)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
    ))
    child.attrs["display_name"] = child_name
    perch_ent = world.add(Entity(
        id="perch",
        kind="thing",
        type="perch",
        label=perch.label,
        phrase=perch.phrase,
        role="perch",
    ))
    antique_ent = world.add(Entity(
        id="antique",
        kind="thing",
        type="antique",
        label=antique.label,
        phrase=antique.phrase,
        role="antique",
        tags=set(antique.tags),
    ))
    parent_name = "Mom" if parent_type == "mother" else "Dad"
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label=parent_name,
        phrase=parent_name,
        role="parent",
    ))
    if helper_kind.adult:
        helper_ent = parent
        helper_display = parent_name
    else:
        helper_ent = world.add(Entity(
            id="helper",
            kind="character",
            type=helper_gender,
            label=helper_name,
            phrase=helper_name,
            role="helper",
        ))
        helper_ent.attrs["display_name"] = helper_name
        helper_display = helper_name

    child.meters["height_need"] = float(antique.reach_need)
    antique_ent.meters["fragile"] = float(antique.fragile)
    perch_ent.meters["stability"] = float(perch.stability)

    introduce(world, child, room, antique)
    spot_perch(world, child, perch)

    world.para()
    warning(world, child, helper_ent, helper_kind, antique, perch)

    outcome = "averted" if helper_kind.adult else ("safe" if base_reach(perch, helper_kind) >= antique.reach_need + delay else "slip")
    if outcome == "averted":
        ask_first(world, child, parent, antique)
    else:
        start_climb(world, child, helper_ent, perch_ent, perch, helper_kind)
        if outcome == "safe":
            world.para()
            safe_reach(world, child, helper_ent, antique_ent, antique)
            after_safe(world, child, helper_ent, parent, antique, helper_kind)
        else:
            world.para()
            slip_attempt(world, child, helper_ent, parent, antique, perch_ent)
            after_slip(world, child, parent, antique, antique_ent)

    world.para()
    final_image(world, child, antique, outcome)

    world.facts.update(
        room=room,
        antique_cfg=antique,
        perch_cfg=perch,
        helper_kind=helper_kind,
        child=child,
        helper=helper_ent,
        parent=parent,
        antique=antique_ent,
        perch=perch_ent,
        outcome=outcome,
        delay=delay,
        helper_display=helper_display,
        child_display=child_name,
    )
    return world


ROOMS = {
    "parlor": Room(
        id="parlor",
        place="the parlor",
        shelf="a tall walnut shelf",
        glow="afternoon sun made the brass frames glow",
        rug="the braided rug",
        tags={"room", "home"},
    ),
    "nursery": Room(
        id="nursery",
        place="the nursery",
        shelf="a painted shelf above the toy chest",
        glow="golden stripes of sun lay over the floor",
        rug="the patchwork rug",
        tags={"room", "home"},
    ),
    "hall": Room(
        id="hall",
        place="the front hall",
        shelf="a narrow shelf by the mirror",
        glow="window light turned the wood trim honey-bright",
        rug="the long runner rug",
        tags={"room", "home"},
    ),
}

ANTIQUES = {
    "music_box": Antique(
        id="music_box",
        label="music box",
        phrase="an antique music box",
        sound="a tiny silver tune",
        reach_need=2,
        fragile=2,
        tags={"music_box", "antique"},
    ),
    "globe": Antique(
        id="globe",
        label="globe",
        phrase="an antique globe",
        sound="the hush of spinning seas in a make-believe tune",
        reach_need=2,
        fragile=2,
        tags={"globe", "antique"},
    ),
    "lamp": Antique(
        id="lamp",
        label="lamp",
        phrase="an antique lamp",
        sound="the click of its little chain and the hush around its light",
        reach_need=3,
        fragile=3,
        tags={"lamp", "antique"},
    ),
}

PERCHES = {
    "stool": Perch(
        id="stool",
        label="step stool",
        phrase="a stout little step stool",
        stability=2,
        rolling=False,
        tags={"stool"},
    ),
    "chair": Perch(
        id="chair",
        label="chair",
        phrase="a straight-backed chair",
        stability=1,
        rolling=False,
        tags={"chair"},
    ),
    "toy_chest": Perch(
        id="toy_chest",
        label="toy chest",
        phrase="the old toy chest",
        stability=0,
        rolling=False,
        tags={"toy_chest"},
    ),
    "rolling_chair": Perch(
        id="rolling_chair",
        label="rolling chair",
        phrase="a rolling chair with squeaky wheels",
        stability=0,
        rolling=True,
        tags={"rolling_chair"},
    ),
}

HELPERS = {
    "grownup": HelperKind(
        id="grownup",
        label="a grown-up",
        phrase="a grown-up helper",
        support=3,
        sense=3,
        adult=True,
        relation_word="parent",
        tags={"grownup", "ask_first"},
    ),
    "sibling": HelperKind(
        id="sibling",
        label="an older sibling",
        phrase="an older sibling helper",
        support=1,
        sense=2,
        adult=False,
        relation_word="sibling",
        tags={"sibling", "teamwork"},
    ),
    "friend": HelperKind(
        id="friend",
        label="a same-size friend",
        phrase="a same-size friend",
        support=0,
        sense=1,
        adult=False,
        relation_word="friend",
        tags={"friend"},
    ),
}


@dataclass
class StoryParams:
    room: str
    antique: str
    perch: str
    helper: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lila", "Nora", "Eva", "Ruby", "Tess", "Cora", "Ivy"]
BOY_NAMES = ["Owen", "Ben", "Milo", "Theo", "Eli", "Jude", "Finn", "Max"]


CURATED = [
    StoryParams(
        room="parlor",
        antique="music_box",
        perch="chair",
        helper="grownup",
        child_name="Mina",
        child_gender="girl",
        helper_name="Mom",
        helper_gender="girl",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        room="nursery",
        antique="globe",
        perch="stool",
        helper="sibling",
        child_name="Nora",
        child_gender="girl",
        helper_name="Owen",
        helper_gender="boy",
        parent="father",
        delay=0,
    ),
    StoryParams(
        room="hall",
        antique="music_box",
        perch="chair",
        helper="sibling",
        child_name="Ben",
        child_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        room="parlor",
        antique="lamp",
        perch="stool",
        helper="grownup",
        child_name="Ivy",
        child_gender="girl",
        helper_name="Dad",
        helper_gender="boy",
        parent="father",
        delay=0,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for room_id in ROOMS:
        for antique_id, antique in ANTIQUES.items():
            for perch_id, perch in PERCHES.items():
                for helper_id, helper in HELPERS.items():
                    if valid_combo(antique, perch, helper):
                        combos.append((room_id, antique_id, perch_id, helper_id))
    return combos


KNOWLEDGE = {
    "antique": [
        (
            "What does antique mean?",
            "Antique means very old and special. Antique things can be beautiful, but they often need gentle hands and careful help.",
        )
    ],
    "music_box": [
        (
            "What is a music box?",
            "A music box is a small box that plays a tune. Many old ones are delicate, so people turn them softly and keep them safe.",
        )
    ],
    "globe": [
        (
            "What is a globe?",
            "A globe is a round model of the earth. It can spin, showing oceans and lands all around the world.",
        )
    ],
    "lamp": [
        (
            "Why should an old lamp be handled carefully?",
            "An old lamp can be fragile because its glass and metal parts may be worn. Careful hands help keep it from breaking.",
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps you reach something a little higher. It works best when it is steady and a grown-up says it is safe to use.",
        )
    ],
    "chair": [
        (
            "Why is climbing on a chair risky?",
            "A chair can wobble when you stand on it. If it tips, you can fall and get hurt.",
        )
    ],
    "rolling_chair": [
        (
            "Why is a rolling chair a bad thing to climb on?",
            "A rolling chair can move under you all at once. Wheels make it slide when you need it to stay still.",
        )
    ],
    "ask_first": [
        (
            "Why is it smart to ask a grown-up for help reaching something high?",
            "A grown-up is taller and steadier, so they can help without risky climbing. Asking first can stop a fall before it starts.",
        )
    ],
    "teamwork": [
        (
            "How can teamwork make a job safer?",
            "Teamwork can make a job safer when one person steadies and the other moves slowly. Careful teamwork is calmer than rushing alone.",
        )
    ],
    "bump": [
        (
            "What should you do if you fall and bump your hiney?",
            "Stop and sit still for a moment, then tell a grown-up. Even a small bump feels better when someone checks that you are okay.",
        )
    ],
}
KNOWLEDGE_ORDER = ["antique", "music_box", "globe", "lamp", "stool", "chair", "rolling_chair", "ask_first", "teamwork", "bump"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    antique = f["antique_cfg"]
    perch = f["perch_cfg"]
    helper = f["helper_kind"]
    outcome = f["outcome"]
    display = f["child_display"]
    base = (
        f'Write a rhyming story for a 3-to-5-year-old with dialogue, the word "antique", '
        f'the word "might", and the word "hiney". The story should be about {display} wanting '
        f"to reach {antique.phrase} from a high shelf."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle rhyming story where {display} thinks {child.pronoun('subject')} might climb on {perch.phrase}, "
            f"but a grown-up uses dialogue to stop the climb and help safely.",
            f'Write a careful bedtime-style rhyme where a child asks before climbing, keeps a little hiney on the floor, and ends by listening to an antique treasure safely.',
        ]
    if outcome == "safe":
        return [
            base,
            f"Tell a rhyming dialogue story where {display} reaches for {antique.phrase} with help from an older sibling and a steady {perch.label}.",
            f'Write a warm story in verse-like prose where teamwork keeps an antique object safe and even mentions that nobody bumps a hiney.',
        ]
    return [
        base,
        f"Tell a gentle cautionary rhyming story where {display} tries to climb on {perch.phrase}, slips onto {child.pronoun('possessive')} hiney, and then learns to ask first.",
        f'Write a story with child-friendly dialogue where an antique object stays safe, but a rushed plan ends in a soft bump and a wiser ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper = f["helper"]
    antique = f["antique_cfg"]
    perch = f["perch_cfg"]
    helper_kind = f["helper_kind"]
    child_name = f["child_display"]
    helper_name = helper.label if helper.role == "parent" else helper.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, who wanted to reach {antique.phrase} from a high shelf. The story also includes {parent.label_word} and, in some versions, a helper who tries to keep things safe.",
        ),
        (
            f"What did {child_name} want?",
            f"{child_name} wanted to reach {antique.phrase} and listen to {antique.sound}. The old object looked magical, so it made the child feel curious right away.",
        ),
        (
            f"Why did someone warn {child_name}?",
            f"{child_name} was thinking about climbing on {perch.phrase} to reach something high. The warning came because an antique object is fragile, and climbing furniture can make a child fall or make the old thing unsafe.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How was the problem solved?",
                f"The grown-up stopped the climbing before it started and brought the antique item down safely. That kept {child_name}'s feet and hiney on the floor, so there was no bump and no scary moment.",
            )
        )
        qa.append(
            (
                f"How did {child_name} feel at the end?",
                f"{child_name} felt calm, curious, and cared for. The ending feels gentle because the child still got to enjoy the antique treasure without taking a risky climb.",
            )
        )
    elif f["outcome"] == "safe":
        qa.append(
            (
                f"Why did the climb work safely this time?",
                f"It worked because {helper_name} steadied the perch and {child_name} moved slowly. The careful teamwork gave enough support to reach the antique object without wobbling into trouble.",
            )
        )
        qa.append(
            (
                f"What changed by the end of the story?",
                f"At first, the moment felt risky because the shelf was high and the antique thing was delicate. By the end, the object was lower, everyone was relieved, and the story ended with safe listening instead of fear.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child_name} hurried?",
                f"The perch wobbled, and {child_name} slipped onto {child.pronoun('possessive')} hiney. The bump was small, but it proved that rushing upward was not a safe way to reach a fragile antique object.",
            )
        )
        qa.append(
            (
                f"What lesson did {child_name} learn?",
                f"{child_name} learned to ask first instead of climbing in a hurry. The second part of the lesson came from the bump itself, because the sore hiney made the danger feel real and easy to remember.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"antique"}
    tags |= set(f["antique_cfg"].tags)
    tags |= set(f["perch_cfg"].tags)
    tags |= set(f["helper_kind"].tags)
    if f["outcome"] == "slip":
        tags.add("bump")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.label:
            bits.append(f"label={ent.label}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M.

valid(A, P, H) :- antique(A), perch(P), helper(H), sensible(H), adult(H).
valid(A, P, H) :- antique(A), perch(P), helper(H), sensible(H),
                  not adult(H), not rolling(P),
                  reach_need(A, N), stability(P, PS), support(H, HS), PS + HS >= N.

safe_score(PS + HS) :- chosen_perch(P), stability(P, PS), chosen_helper(H), support(H, HS).
averted :- chosen_helper(H), adult(H).
safe :- not averted, chosen_antique(A), reach_need(A, N), chosen_delay(D),
        safe_score(S), S >= N + D.
outcome(averted) :- averted.
outcome(safe) :- not averted, safe.
outcome(slip) :- not averted, not safe.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for aid, antique in ANTIQUES.items():
        lines.append(asp.fact("antique", aid))
        lines.append(asp.fact("reach_need", aid, antique.reach_need))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("stability", pid, perch.stability))
        if perch.rolling:
            lines.append(asp.fact("rolling", pid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("support", hid, helper.support))
        lines.append(asp.fact("sense", hid, helper.sense))
        if helper.adult:
            lines.append(asp.fact("adult", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_antique", params.antique),
        asp.fact("chosen_perch", params.perch),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=True, qa=True, header="### smoke")
    text = buf.getvalue()
    if "smoke" not in text or not sample.story.strip():
        raise StoryError("Smoke emit produced empty output.")


def asp_verify() -> int:
    rc = 0
    python_set = {(a, p, h) for (_, a, p, h) in valid_combos()}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} antique/perch/helper combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    for _ in range(20):
        try:
            params = resolve_params(parser.parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: normal generate/emit smoke test passed.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming dialogue story world: a child, a high antique treasure, and a safer choice."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--antique", choices=ANTIQUES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra hurry or wobble that makes a risky plan more likely to slip")
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible antique/perch/helper combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        helper = HELPERS[args.helper]
        raise StoryError(
            f"(No story: helper '{args.helper}' is too weak on common sense here "
            f"(sense={helper.sense} < {SENSE_MIN}). Try sibling or grownup.)"
        )
    if args.antique and args.perch and args.helper:
        antique = ANTIQUES[args.antique]
        perch = PERCHES[args.perch]
        helper = HELPERS[args.helper]
        if not valid_combo(antique, perch, helper):
            raise StoryError(explain_rejection(antique, perch, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.antique is None or combo[1] == args.antique)
        and (args.perch is None or combo[2] == args.perch)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, antique_id, perch_id, helper_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("girl" if child_gender == "boy" else "boy")
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])

    if helper_id == "grownup":
        helper_name = "Mom" if parent == "mother" else "Dad"
        helper_gender = "girl" if parent == "mother" else "boy"

    return StoryParams(
        room=room_id,
        antique=antique_id,
        perch=perch_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        room = ROOMS[params.room]
        antique = ANTIQUES[params.antique]
        perch = PERCHES[params.perch]
        helper = HELPERS[params.helper]
    except KeyError as exc:
        raise StoryError(f"(Unknown option: {exc.args[0]})") from exc
    if not valid_combo(antique, perch, helper):
        raise StoryError(explain_rejection(antique, perch, helper))

    world = tell(
        room=room,
        antique=antique,
        perch=perch,
        helper_kind=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (antique, perch, helper) combos:\n")
        for antique, perch, helper in combos:
            print(f"  {antique:10} {perch:13} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for idx, params in enumerate(CURATED):
            cp = StoryParams(
                room=params.room,
                antique=params.antique,
                perch=params.perch,
                helper=params.helper,
                child_name=params.child_name,
                child_gender=params.child_gender,
                helper_name=params.helper_name,
                helper_gender=params.helper_gender,
                parent=params.parent,
                delay=params.delay,
                seed=base_seed + idx,
            )
            samples.append(generate(cp))
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
            header = f"### {p.child_name}: {p.antique} from {p.room} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
