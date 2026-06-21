#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/advertise_inner_monologue_surprise_repetition_slice_of.py
====================================================================================

A standalone story world about a child who wants to advertise a tiny neighborhood
stand. The story stays close to slice-of-life: a table, a handmade sign, a quiet
street, a worried child, and the surprise of being noticed.

The seed asked for:
- the word "advertise"
- Inner Monologue
- Surprise
- Repetition
- Slice of Life

So this world models a simple everyday tension:

    A child sets up a little stand.
    The spot feels too quiet.
    The child keeps thinking the same worried thought.
    A helper suggests a sensible way to advertise.
    The sign changes the world by increasing visibility.
    An unexpected first visitor appears.
    The ending image proves the child has changed from worried to proud.

The reasonableness gate is small and concrete:
- a way to advertise must physically fit the place (chalk needs ground, poster
  needs a window/wall/fence, banner needs a rail or table front),
- the chosen method must make the place visible enough for anyone to notice,
- the surprise visitor must plausibly pass that place.

Run it
------
    python storyworlds/worlds/gpt-5.4/advertise_inner_monologue_surprise_repetition_slice_of.py
    python storyworlds/worlds/gpt-5.4/advertise_inner_monologue_surprise_repetition_slice_of.py --place stoop --offer lemonade --method chalk_arrows
    python storyworlds/worlds/gpt-5.4/advertise_inner_monologue_surprise_repetition_slice_of.py --place apartment_window --method chalk_arrows
    python storyworlds/worlds/gpt-5.4/advertise_inner_monologue_surprise_repetition_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/advertise_inner_monologue_surprise_repetition_slice_of.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
NOTICE_MIN = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"               # "character" | "thing" | "place"
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
        female = {"girl", "mother", "grandmother", "woman", "teacher", "artist"}
        male = {"boy", "father", "man", "carrier", "guard"}
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
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    detail: str
    surfaces: set[str] = field(default_factory=set)
    traffic: int = 1
    indoor: bool = False
    visitor_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Offer:
    id: str
    label: str
    phrase: str
    display: str
    slogan: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AdMethod:
    id: str
    label: str
    phrase: str
    needs: set[str] = field(default_factory=set)
    boost: int = 1
    action_text: str = ""
    result_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SurpriseVisitor:
    id: str
    label: str
    type: str
    phrase: str
    reason: str
    reaction: str
    spread_bonus: int = 0
    place_tags: set[str] = field(default_factory=set)
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


def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    stand = world.get("stand")
    if stand.meters["visibility"] >= THRESHOLD and ("noticed",) not in world.fired:
        score = int(place.meters["traffic"] + stand.meters["visibility"])
        if score >= NOTICE_MIN:
            world.fired.add(("noticed",))
            stand.meters["noticed"] += 1
            child = world.get("child")
            child.memes["hope"] += 1
            out.append("__noticed__")
    return out


def _r_pride(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    stand = world.get("stand")
    if stand.meters["sales"] >= THRESHOLD and ("pride",) not in world.fired:
        world.fired.add(("pride",))
        child.memes["pride"] += 1
        child.memes["worry"] = 0.0
        out.append("__pride__")
    return out


CAUSAL_RULES = [
    Rule(name="notice", tag="physical", apply=_r_notice),
    Rule(name="pride", tag="emotional", apply=_r_pride),
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
        for s in produced:
            world.say(s)
    return produced


def method_fits(place: Place, method: AdMethod) -> bool:
    return bool(place.surfaces & method.needs)


def visible_enough(place: Place, method: AdMethod) -> bool:
    return place.traffic + method.boost >= NOTICE_MIN


def visitor_fits(place: Place, visitor: SurpriseVisitor) -> bool:
    return bool(place.tags & visitor.place_tags)


def valid_combo(place: Place, method: AdMethod, visitor: SurpriseVisitor) -> bool:
    return method_fits(place, method) and visible_enough(place, method) and visitor_fits(place, visitor)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for offer_id in OFFERS:
            for method_id, method in METHODS.items():
                for visitor_id, visitor in VISITORS.items():
                    if valid_combo(place, method, visitor):
                        combos.append((place_id, offer_id, method_id, visitor_id))
    return combos


def notice_score(place: Place, method: AdMethod, visitor: SurpriseVisitor) -> int:
    return place.traffic + method.boost + visitor.spread_bonus


def outcome_of(params: "StoryParams") -> str:
    place = require_choice(PLACES, params.place, "place")
    method = require_choice(METHODS, params.method, "method")
    visitor = require_choice(VISITORS, params.visitor, "visitor")
    score = notice_score(place, method, visitor)
    return "busy" if score >= 5 else "noticed"


def explain_rejection(place: Place, method: AdMethod, visitor: SurpriseVisitor) -> str:
    if not method_fits(place, method):
        need = " / ".join(sorted(method.needs))
        have = " / ".join(sorted(place.surfaces))
        return (
            f"(No story: {method.label} needs {need}, but {place.label} only offers {have}. "
            f"The child needs a real place to advertise from.)"
        )
    if not visible_enough(place, method):
        return (
            f"(No story: {method.label} would not make {place.label} visible enough for anyone to notice. "
            f"Pick a brighter method or a busier place.)"
        )
    if not visitor_fits(place, visitor):
        return (
            f"(No story: {visitor.label} does not usually pass {place.label}, so the surprise arrival would feel ungrounded.)"
        )
    return "(No story: this combination does not make a reasonable advertise story.)"


def predict_notice(world: World, method: AdMethod, visitor: SurpriseVisitor) -> dict:
    sim = world.copy()
    apply_advertising(sim, method, narrate=False)
    place = sim.get("place")
    stand = sim.get("stand")
    noticed = stand.meters["noticed"] >= THRESHOLD
    score = int(place.meters["traffic"] + stand.meters["visibility"] + visitor.spread_bonus)
    return {"noticed": noticed, "score": score}


def introduce(world: World, child: Entity, helper: Entity, place: Place, offer: Offer) -> None:
    child.memes["hope"] += 1
    stand = world.get("stand")
    stand.meters["stock"] = 3.0
    world.say(
        f"After lunch, {child.id} carried a little folding table to {place.phrase}. "
        f"{place.detail}"
    )
    world.say(
        f"On top, {child.pronoun()} arranged {offer.display}. {helper.id} set the last thing in place and stepped back with a smile."
    )
    world.say(
        f"{child.id} wanted to advertise {offer.label} all by {child.pronoun('object')}self, the way big kids in the neighborhood sometimes did."
    )


def quiet_problem(world: World, child: Entity, place: Place, offer: Offer) -> None:
    child.memes["worry"] += 1
    place_ent = world.get("place")
    place_ent.meters["traffic"] = float(place.traffic)
    world.say(
        f"But {place.label} was quiet. A bicycle rolled by, then nothing at all, and the little table suddenly felt smaller than it had in the kitchen."
    )
    worry = f"What if nobody stops? What if nobody stops?"
    world.facts["repeated_thought"] = worry
    world.say(
        f'Inside, {child.id} thought, "{worry}"'
    )
    world.say(
        f'{child.pronoun().capitalize()} looked at the cups and jars and cards again and thought, "I made {offer.label}. I really did. I just need people to see it."'
    )


def helper_offer(world: World, child: Entity, helper: Entity, method: AdMethod, visitor: SurpriseVisitor) -> None:
    pred = predict_notice(world, method, visitor)
    world.facts["predicted_score"] = pred["score"]
    child.memes["courage"] += 1
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} noticed the tight little wrinkle between {child.id}\'s eyebrows. '
        f'"You do not need to shout," {helper.pronoun()} said. "We can advertise in a kind way."'
    )
    world.say(
        f"{helper.id} pointed to {method.phrase}. The idea was small and ordinary, which made it feel possible."
    )


def apply_advertising(world: World, method: AdMethod, narrate: bool = True) -> None:
    stand = world.get("stand")
    child = world.get("child")
    stand.meters["visibility"] += float(method.boost)
    child.memes["hope"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 0.5)
    propagate(world, narrate=narrate)


def advertise(world: World, child: Entity, helper: Entity, offer: Offer, method: AdMethod) -> None:
    apply_advertising(world, method, narrate=False)
    world.say(
        f"Together they {method.action_text}."
    )
    world.say(
        f"{method.result_text} Across the top, in careful letters, {child.id} wrote: {offer.slogan}"
    )
    world.say(
        f'{child.id} read it once under {child.pronoun("possessive")} breath, then again a little louder: "{offer.slogan} {offer.slogan}"'
    )
    child.memes["courage"] += 1
    world.facts["repeated_slogan"] = f"{offer.slogan} {offer.slogan}"


def surprise_arrival(world: World, child: Entity, visitor_cfg: SurpriseVisitor, offer: Offer) -> None:
    visitor = world.add(
        Entity(
            id="Visitor",
            kind="character",
            type=visitor_cfg.type,
            label=visitor_cfg.label,
            phrase=visitor_cfg.phrase,
            role="visitor",
            tags=set(visitor_cfg.tags),
        )
    )
    child.memes["surprise"] += 1
    stand = world.get("stand")
    stand.meters["sales"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the surprise. {visitor_cfg.phrase} appeared first, {visitor_cfg.reason}"
    )
    world.say(
        f'{visitor.pronoun().capitalize()} slowed down, read the sign, and smiled. "{visitor_cfg.reaction}"'
    )
    world.say(
        f"{visitor.label.capitalize()} chose {offer.phrase}, and just like that, the table was not lonely anymore."
    )
    world.facts["visitor_entity"] = visitor


def busier_turn(world: World, child: Entity, helper: Entity, offer: Offer, visitor_cfg: SurpriseVisitor) -> None:
    stand = world.get("stand")
    stand.meters["sales"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That might have been enough all by itself, but {visitor_cfg.label} turned and told two more people what {child.id} had made."
    )
    world.say(
        f"Soon there were voices, small coins, paper cups, and a line that was only three people long but felt huge to {child.id}."
    )
    world.say(
        f'This time the thought inside {child.pronoun("possessive")} head sounded different: "They came. They really came."'
    )
    world.say(
        f"When the afternoon light softened, {offer.ending_image} and {child.id} did not have to wonder whether the sign had worked."
    )


def quiet_happy_end(world: World, child: Entity, helper: Entity, offer: Offer) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'{child.id} blinked, then laughed in one small puff of surprise. Inside, the worried sentence broke apart and a new one took its place: "Someone saw. Someone saw."'
    )
    world.say(
        f"{helper.id} squeezed {child.pronoun('possessive')} shoulder, and the afternoon went on in a softer way than {child.id} had imagined."
    )
    world.say(
        f"By the time they packed up, {offer.ending_image} and the handmade sign no longer looked shy at all."
    )


def tell(
    place: Place,
    offer: Offer,
    method: AdMethod,
    visitor_cfg: SurpriseVisitor,
    child_name: str = "Lena",
    child_gender: str = "girl",
    helper_name: str = "Mom",
    helper_type: str = "mother",
    child_trait: str = "careful",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[child_trait],
            label=child_name,
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    world.add(
        Entity(
            id="place",
            kind="place",
            type="place",
            label=place.label,
            phrase=place.phrase,
            tags=set(place.tags),
        )
    )
    world.add(
        Entity(
            id="stand",
            kind="thing",
            type="stand",
            label="stand",
            phrase=f"a little stand for {offer.label}",
            tags=set(offer.tags),
        )
    )

    introduce(world, child, helper, place, offer)
    world.para()
    quiet_problem(world, child, place, offer)
    helper_offer(world, child, helper, method, visitor_cfg)
    world.para()
    advertise(world, child, helper, offer, method)
    surprise_arrival(world, child, visitor_cfg, offer)
    world.para()

    outcome = "busy" if notice_score(place, method, visitor_cfg) >= 5 else "noticed"
    if outcome == "busy":
        busier_turn(world, child, helper, offer, visitor_cfg)
    else:
        quiet_happy_end(world, child, helper, offer)

    world.facts.update(
        child=child,
        helper=helper,
        place_cfg=place,
        offer_cfg=offer,
        method_cfg=method,
        visitor_cfg=visitor_cfg,
        outcome=outcome,
        noticed=world.get("stand").meters["noticed"] >= THRESHOLD,
        sold=world.get("stand").meters["sales"] >= THRESHOLD,
    )
    return world


PLACES = {
    "stoop": Place(
        id="stoop",
        label="the front stoop",
        phrase="the front stoop",
        detail="The warm steps still held a little sun, and the street in front of the house was quiet but not empty.",
        surfaces={"ground", "rail"},
        traffic=2,
        indoor=False,
        visitor_tags={"neighbor", "carrier", "teacher"},
        tags={"home", "street"},
    ),
    "park_gate": Place(
        id="park_gate",
        label="the park gate",
        phrase="the park gate",
        detail="Children and grown-ups kept passing the iron fence on their way in and out.",
        surfaces={"fence", "ground"},
        traffic=3,
        indoor=False,
        visitor_tags={"neighbor", "artist", "guard"},
        tags={"park", "street"},
    ),
    "apartment_window": Place(
        id="apartment_window",
        label="the apartment window",
        phrase="the front apartment window",
        detail="The glass looked down over the sidewalk, where people glanced up now and then on their way home.",
        surfaces={"window", "wall"},
        traffic=2,
        indoor=True,
        visitor_tags={"neighbor", "carrier", "teacher"},
        tags={"building", "street"},
    ),
    "hall_table": Place(
        id="hall_table",
        label="the building hall table",
        phrase="the small table by the building hall",
        detail="It was a neat spot near the mailboxes, with soft footsteps and doors opening every few minutes.",
        surfaces={"wall", "tablefront"},
        traffic=2,
        indoor=True,
        visitor_tags={"neighbor", "carrier"},
        tags={"building", "home"},
    ),
}

OFFERS = {
    "lemonade": Offer(
        id="lemonade",
        label="lemonade",
        phrase="a paper cup of lemonade",
        display="a pitcher with lemon slices floating at the top and a row of small paper cups",
        slogan="Cold lemonade today!",
        ending_image="the pitcher stood half-empty with shining drops on the glass",
        tags={"lemonade", "drink"},
    ),
    "bookmarks": Offer(
        id="bookmarks",
        label="hand-painted bookmarks",
        phrase="one hand-painted bookmark",
        display="a fan of painted bookmarks in a jar, with tassels spilling like stringy confetti",
        slogan="Bookmarks made by hand!",
        ending_image="only a few bright bookmarks remained in the jar",
        tags={"bookmarks", "craft"},
    ),
    "seedlings": Offer(
        id="seedlings",
        label="little seedling pots",
        phrase="a tiny basil seedling",
        display="three tiny pots of basil and mint lined up in a bread pan",
        slogan="Little plants need homes!",
        ending_image="two small pots were gone, leaving damp circles in the tray",
        tags={"plants", "garden"},
    ),
}

METHODS = {
    "chalk_arrows": AdMethod(
        id="chalk_arrows",
        label="chalk arrows",
        phrase="a stub of sidewalk chalk by the step",
        needs={"ground"},
        boost=1,
        action_text="drew bright arrows on the ground and wrote the word advertise in a box with little stars around it",
        result_text="The pale pavement suddenly looked like it was pointing somewhere on purpose.",
        tags={"chalk", "sign"},
    ),
    "window_poster": AdMethod(
        id="window_poster",
        label="a window poster",
        phrase="a sheet of poster paper and a thick blue marker",
        needs={"window", "wall", "fence"},
        boost=2,
        action_text="taped up a big poster with thick letters and a border of tiny lemons, books, or leaves",
        result_text="From far away, the colors made the sign easier to notice.",
        tags={"poster", "sign"},
    ),
    "cloth_banner": AdMethod(
        id="cloth_banner",
        label="a cloth banner",
        phrase="an old pillowcase and clothespins",
        needs={"rail", "fence", "tablefront"},
        boost=2,
        action_text="clipped a long cloth banner across the front and painted the words slowly so they would not wobble",
        result_text="The cloth moved in the breeze and kept catching the eye.",
        tags={"banner", "sign"},
    ),
}

VISITORS = {
    "mail_carrier": SurpriseVisitor(
        id="mail_carrier",
        label="the mail carrier",
        type="carrier",
        phrase="the mail carrier with a bag over one shoulder",
        reason="pausing between two houses to sort the last letters",
        reaction="Well, look at this. Someone has been busy.",
        spread_bonus=0,
        place_tags={"street", "building", "home"},
        tags={"carrier"},
    ),
    "piano_teacher": SurpriseVisitor(
        id="piano_teacher",
        label="the piano teacher",
        type="teacher",
        phrase="the piano teacher from three doors down",
        reason="coming early for a lesson nearby",
        reaction="I nearly walked right past, and that would have been a shame.",
        spread_bonus=1,
        place_tags={"street", "building", "home"},
        tags={"teacher"},
    ),
    "crossing_guard": SurpriseVisitor(
        id="crossing_guard",
        label="the crossing guard",
        type="guard",
        phrase="the crossing guard in the bright orange vest",
        reason="taking a slow walk through the park before heading home",
        reaction="A careful sign is a good sign. Show me what you made.",
        spread_bonus=0,
        place_tags={"park"},
        tags={"guard"},
    ),
    "sidewalk_artist": SurpriseVisitor(
        id="sidewalk_artist",
        label="the sidewalk artist",
        type="artist",
        phrase="the sidewalk artist who often sketched near the fountain",
        reason="following the line of color from the sign with curious eyes",
        reaction="Anything made with care deserves to be looked at closely.",
        spread_bonus=1,
        place_tags={"park", "street"},
        tags={"artist"},
    ),
    "upstairs_neighbor": SurpriseVisitor(
        id="upstairs_neighbor",
        label="the upstairs neighbor",
        type="woman",
        phrase="the upstairs neighbor carrying a bag of laundry",
        reason="coming down the hall at just the right moment",
        reaction="I was only going downstairs, and now I have found a little shop.",
        spread_bonus=0,
        place_tags={"building", "home"},
        tags={"neighbor"},
    ),
}

GIRL_NAMES = ["Lena", "Mia", "Ivy", "Nora", "Tess", "Ruby", "Maya", "Ella"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Milo", "Evan", "Theo", "Sam", "Noah"]
TRAITS = ["careful", "hopeful", "quiet", "patient", "earnest", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    offer: str
    method: str
    visitor: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    child_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="stoop",
        offer="lemonade",
        method="cloth_banner",
        visitor="piano_teacher",
        child_name="Lena",
        child_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        child_trait="careful",
    ),
    StoryParams(
        place="park_gate",
        offer="bookmarks",
        method="window_poster",
        visitor="sidewalk_artist",
        child_name="Owen",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
        child_trait="thoughtful",
    ),
    StoryParams(
        place="hall_table",
        offer="seedlings",
        method="cloth_banner",
        visitor="upstairs_neighbor",
        child_name="Mia",
        child_gender="girl",
        helper_name="Grandma",
        helper_type="grandmother",
        child_trait="patient",
    ),
    StoryParams(
        place="apartment_window",
        offer="lemonade",
        method="window_poster",
        visitor="mail_carrier",
        child_name="Ben",
        child_gender="boy",
        helper_name="Mom",
        helper_type="mother",
        child_trait="quiet",
    ),
]


KNOWLEDGE = {
    "advertise": [
        (
            "What does advertise mean?",
            "To advertise means to help people notice something by telling them about it or showing a sign. It is a way of saying, 'Look over here.'",
        )
    ],
    "chalk": [
        (
            "What is sidewalk chalk?",
            "Sidewalk chalk is a soft stick for drawing on pavement. It makes bright marks, and rain can wash them away.",
        )
    ],
    "poster": [
        (
            "What is a poster?",
            "A poster is a big sign with words or pictures on it. People make posters so others can notice important information from farther away.",
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a long sign made from cloth or paper. Because it stretches out, it can be easier to see than a tiny note.",
        )
    ],
    "lemonade": [
        (
            "What is lemonade?",
            "Lemonade is a drink made with lemon juice, water, and usually a little sugar. People often serve it cold on warm days.",
        )
    ],
    "bookmarks": [
        (
            "What is a bookmark for?",
            "A bookmark helps you keep your place in a book. You slide it between the pages so you can come back later.",
        )
    ],
    "plants": [
        (
            "What is a seedling?",
            "A seedling is a very young plant. It is small and tender because it has only just begun to grow.",
        )
    ],
    "neighbor": [
        (
            "Who is a neighbor?",
            "A neighbor is someone who lives nearby. Neighbors may live next door, upstairs, or a few houses away.",
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you were not expecting. It can make your thoughts change very quickly in one happy moment.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "advertise",
    "chalk",
    "poster",
    "banner",
    "lemonade",
    "bookmarks",
    "plants",
    "neighbor",
    "surprise",
]


def require_choice(registry: dict, key: str, label: str):
    if key not in registry:
        raise StoryError(f"(Unknown {label}: {key})")
    return registry[key]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place_cfg"]
    offer = f["offer_cfg"]
    method = f["method_cfg"]
    visitor = f["visitor_cfg"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "advertise".',
        f"Tell a gentle story where a {child.type} named {child.id} tries to advertise {offer.label} at {place.label}, keeps repeating a worried thought inside {child.pronoun('possessive')} head, and then gets a happy surprise.",
        f"Write a neighborhood story with inner monologue, a repeated line, and a surprise first customer, using {method.label} and {visitor.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    offer = f["offer_cfg"]
    method = f["method_cfg"]
    visitor = f["visitor_cfg"]
    outcome = f["outcome"]
    repeated_thought = f.get("repeated_thought", "What if nobody stops?")
    repeated_slogan = f.get("repeated_slogan", offer.slogan)

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who set up a small stand at {place.label}, and {helper.id}, who helped in a calm way.",
        ),
        (
            f"Why was {child.id} worried?",
            f"{child.id} was worried because the place felt quiet and no one was stopping to look. Inside, {child.pronoun()} kept thinking, \"{repeated_thought}\"",
        ),
        (
            f"How did they advertise {offer.label}?",
            f"They used {method.label} to make the stand easier to notice. That changed the world outside the table, because people could finally see where to look.",
        ),
        (
            "What line was repeated in the story?",
            f'The worried thought was repeated inside {child.id}\'s head, and later the sign words were repeated too: "{repeated_slogan}" The repetition showed how the feeling changed from worry to courage.',
        ),
        (
            f"Why was the first visitor a surprise?",
            f"{visitor.label.capitalize()} was not the person {child.id} expected to see first. The surprise mattered because one kind stop broke the lonely feeling around the stand.",
        ),
    ]
    if outcome == "busy":
        qa.append(
            (
                "What changed after the surprise visitor arrived?",
                f"After the first visitor stopped, more people came too, so the stand felt lively instead of lonely. The surprise visitor's notice helped turn one small moment into a busier afternoon.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and happily, with the sign working and {child.id} feeling seen. The stand did not need a crowd; one real customer was enough to change the whole afternoon.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"advertise", "surprise"}
    offer = f["offer_cfg"]
    method = f["method_cfg"]
    visitor = f["visitor_cfg"]
    tags |= set(offer.tags)
    tags |= set(method.tags)
    tags |= set(visitor.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(P, M) :- place(P), method(M), needs(M, S), surface(P, S).
visible(P, M) :- traffic(P, T), boost(M, B), notice_min(N), T + B >= N.
visitor_ok(P, V) :- place(P), visitor(V), place_tag(P, Tag), visitor_place(V, Tag).

valid(P, O, M, V) :- place(P), offer(O), method(M), visitor(V),
                     fits(P, M), visible(P, M), visitor_ok(P, V).

score(P, M, V, T + B + S) :- traffic(P, T), boost(M, B), spread_bonus(V, S).
busy(P, M, V) :- score(P, M, V, N), N >= 5.
outcome(P, M, V, busy) :- valid(P, _, M, V), busy(P, M, V).
outcome(P, M, V, noticed) :- valid(P, _, M, V), not busy(P, M, V).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("traffic", place_id, place.traffic))
        for surface in sorted(place.surfaces):
            lines.append(asp.fact("surface", place_id, surface))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", place_id, tag))
    for offer_id in OFFERS:
        lines.append(asp.fact("offer", offer_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("boost", method_id, method.boost))
        for need in sorted(method.needs):
            lines.append(asp.fact("needs", method_id, need))
    for visitor_id, visitor in VISITORS.items():
        lines.append(asp.fact("visitor", visitor_id))
        lines.append(asp.fact("spread_bonus", visitor_id, visitor.spread_bonus))
        for tag in sorted(visitor.place_tags):
            lines.append(asp.fact("visitor_place", visitor_id, tag))
    lines.append(asp.fact("notice_min", NOTICE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(place_id: str, method_id: str, visitor_id: str) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", place_id),
            asp.fact("chosen_method", method_id),
            asp.fact("chosen_visitor", visitor_id),
            "valid_choice :- valid(P, _, M, V), chosen_place(P), chosen_method(M), chosen_visitor(V).",
            "chosen_outcome(O) :- valid_choice, outcome(P, M, V, O), chosen_place(P), chosen_method(M), chosen_visitor(V).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show chosen_outcome/1."))
    atoms = asp.atoms(model, "chosen_outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(50):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params.place, params.method, params.visitor)
        if py != cl:
            mismatches += 1
            print(
                f"MISMATCH outcome for {params.place}/{params.method}/{params.visitor}: python={py} asp={cl}"
            )
    if mismatches == 0:
        print(f"OK: ASP outcomes match outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.prompts:
            raise StoryError("(Smoke test failed: generated sample was missing story text or prompts.)")
        print("OK: smoke test generated a normal story sample.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a child uses a simple sign to advertise a tiny stand and is surprised when someone notices."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother"])
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP reasoner")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def choose_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def default_helper_name(helper_type: str) -> str:
    return {"mother": "Mom", "father": "Dad", "grandmother": "Grandma"}[helper_type]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None:
        require_choice(PLACES, args.place, "place")
    if args.offer is not None:
        require_choice(OFFERS, args.offer, "offer")
    if args.method is not None:
        require_choice(METHODS, args.method, "method")
    if args.visitor is not None:
        require_choice(VISITORS, args.visitor, "visitor")

    if args.place and args.method and args.visitor:
        place = PLACES[args.place]
        method = METHODS[args.method]
        visitor = VISITORS[args.visitor]
        if not valid_combo(place, method, visitor):
            raise StoryError(explain_rejection(place, method, visitor))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.offer is None or combo[1] == args.offer)
        and (args.method is None or combo[2] == args.method)
        and (args.visitor is None or combo[3] == args.visitor)
    ]
    if not combos:
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        method = METHODS[args.method] if args.method else next(iter(METHODS.values()))
        visitor = VISITORS[args.visitor] if args.visitor else next(iter(VISITORS.values()))
        raise StoryError(explain_rejection(place, method, visitor))

    place_id, offer_id, method_id, visitor_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or choose_name(rng, gender)
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandmother"])
    helper_name = args.helper_name or default_helper_name(helper_type)
    child_trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        offer=offer_id,
        method=method_id,
        visitor=visitor_id,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    place = require_choice(PLACES, params.place, "place")
    offer = require_choice(OFFERS, params.offer, "offer")
    method = require_choice(METHODS, params.method, "method")
    visitor = require_choice(VISITORS, params.visitor, "visitor")
    if not valid_combo(place, method, visitor):
        raise StoryError(explain_rejection(place, method, visitor))

    world = tell(
        place=place,
        offer=offer,
        method=method,
        visitor_cfg=visitor,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        child_trait=params.child_trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, offer, method, visitor) combinations:\n")
        for place_id, offer_id, method_id, visitor_id in combos:
            score = notice_score(PLACES[place_id], METHODS[method_id], VISITORS[visitor_id])
            print(f"  {place_id:16} {offer_id:10} {method_id:14} {visitor_id:16} [{score}]")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.offer} at {p.place} with {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
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
