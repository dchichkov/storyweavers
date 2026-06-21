#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tetanus_surprise_dialogue_bedtime_story.py
=====================================================================

A standalone story world about a child on the edge of bedtime, a hidden sharp
object, and a calm grown-up response that teaches a real safety lesson about
tetanus without becoming scary. The domain is deliberately small and
constraint-checked:

- a place contains a hidden sharp thing
- the child goes there in some footwear
- the world model decides whether the point reaches skin
- if skin is punctured, the grown-up must choose a sensible care plan
- the story ends either as a safe near-miss or a gentle treated surprise

The prose is state-driven: protection, fear, relief, care, and surprise all come
from the simulated world.

Run it
------
    python storyworlds/worlds/gpt-5.4/tetanus_surprise_dialogue_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/tetanus_surprise_dialogue_bedtime_story.py --place shed --sharp nail --footwear boots
    python storyworlds/worlds/gpt-5.4/tetanus_surprise_dialogue_bedtime_story.py --footwear slippers
    python storyworlds/worlds/gpt-5.4/tetanus_surprise_dialogue_bedtime_story.py --care kiss_it
    python storyworlds/worlds/gpt-5.4/tetanus_surprise_dialogue_bedtime_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/tetanus_surprise_dialogue_bedtime_story.py --verify
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
    worn_by: Optional[str] = None
    protective: bool = False
    coverage: float = 0.0
    sterile: bool = False
    dirty_point: bool = False
    sharp: bool = False
    surprise: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "doctor_female"}
        male = {"boy", "father", "dad", "man", "doctor_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    bedtime_pull: str
    detail: str
    where_object: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharpThing:
    id: str
    label: str
    phrase: str
    sound: str
    dirty_point: bool
    poke_hardness: int
    found_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Footwear:
    id: str
    label: str
    phrase: str
    coverage: float
    protective: bool
    plural: bool = False
    bedtime_feel: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class CarePlan:
    id: str
    label: str
    sense: int
    cleans: bool
    clinic: bool
    text: str
    lesson: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SurpriseGift:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_puncture(world: World) -> list[str]:
    child = world.get("child")
    point = world.get("point")
    shoe = world.get("footwear")
    if child.meters["step"] < THRESHOLD or not point.sharp:
        return []
    sig = ("puncture", point.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if shoe.coverage < point.meters["pressure"]:
        child.meters["puncture"] += 1
        child.meters["dirty_wound"] += 1 if point.dirty_point else 0
        child.memes["fear"] += 1
        return ["__puncture__"]
    child.memes["surprise"] += 1
    shoe.meters["marked"] += 1
    return ["__blocked__"]


def _r_tetanus_risk(world: World) -> list[str]:
    child = world.get("child")
    point = world.get("point")
    if child.meters["puncture"] < THRESHOLD or not point.dirty_point:
        return []
    sig = ("tetanus_risk", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["tetanus_risk"] += 1
    child.memes["worry"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["cleaned"] < THRESHOLD:
        return []
    sig = ("relief", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="puncture", tag="physical", apply=_r_puncture),
    Rule(name="tetanus_risk", tag="physical", apply=_r_tetanus_risk),
    Rule(name="relief", tag="emotional", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in out:
            world.say(sent)
    return out


def puncture_happens(sharp: SharpThing, footwear: Footwear) -> bool:
    return sharp.poke_hardness > footwear.coverage


def tetanus_risk(sharp: SharpThing, footwear: Footwear) -> bool:
    return puncture_happens(sharp, footwear) and sharp.dirty_point


def sensible_care() -> list[CarePlan]:
    return [c for c in CARE.values() if c.sense >= SENSE_MIN]


def care_is_enough(sharp: SharpThing, footwear: Footwear, care: CarePlan) -> bool:
    if not puncture_happens(sharp, footwear):
        return True
    if care.sense < SENSE_MIN:
        return False
    if not care.cleans:
        return False
    if tetanus_risk(sharp, footwear) and not care.clinic:
        return False
    return True


def explain_combo_rejection(sharp: SharpThing, footwear: Footwear) -> str:
    if not puncture_happens(sharp, footwear):
        return (f"(No injury story: {footwear.label} stop {sharp.phrase}, so there is no puncture, "
                f"no tetanus risk, and no need for wound care. Pick lighter footwear for a care story.)")
    return "(No valid combination matches the requested options.)"


def explain_care_rejection(care: CarePlan) -> str:
    better = ", ".join(sorted(c.id for c in sensible_care()))
    return (f"(Refusing care '{care.id}': it scores too low on common sense "
            f"(sense={care.sense} < {SENSE_MIN}). Try one of: {better}.)")


def predict_step(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["step"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "puncture": child.meters["puncture"] >= THRESHOLD,
        "risk": child.meters["tetanus_risk"] >= THRESHOLD,
    }


def bedtime_setup(world: World, child: Entity, parent: Entity, place: Place, footwear: Footwear) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"It was the soft, yawn-y part of evening when {child.id}'s {parent.label_word} "
        f"was almost ready to tuck {child.pronoun('object')} in."
    )
    world.say(
        f'But then {child.id} remembered {place.bedtime_pull}. "{parent.label_word.capitalize()}, '
        f'can we peek in {place.label} first?" {child.pronoun()} asked.'
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled. "{child.id}, one tiny peek," '
        f'{parent.pronoun()} said. {place.detail}'
    )
    world.say(
        f"{child.id} padded along in {footwear.phrase}. {footwear.bedtime_feel}"
    )


def warn(world: World, child: Entity, parent: Entity, place: Place, sharp: SharpThing) -> None:
    pred = predict_step(world)
    world.facts["predicted_puncture"] = pred["puncture"]
    world.facts["predicted_risk"] = pred["risk"]
    if pred["puncture"]:
        line = f'"Slow feet," {parent.label_word} whispered. "Sometimes old sharp things hide {place.where_object}."'
        if pred["risk"]:
            line += f' Then {parent.pronoun()} added, "If one pokes skin and carries dirt, a doctor may check for tetanus."'
        world.say(line)
    else:
        world.say(
            f'"Stay close," {parent.label_word} whispered. "Even careful peeks are better with a grown-up."'
        )


def step_and_turn(world: World, child: Entity, sharp: SharpThing, footwear: Footwear) -> None:
    point = world.get("point")
    point.meters["pressure"] = float(sharp.poke_hardness)
    child.meters["step"] += 1
    propagate(world, narrate=False)
    if child.meters["puncture"] >= THRESHOLD:
        world.say(
            f'{sharp.sound} "{parent_word(world)}!" {child.id} squeaked, stopping short. '
            f'"Something poked my foot."'
        )
    else:
        world.say(
            f'{sharp.sound} {child.id} blinked and lifted one foot. "Oh!" {child.pronoun().capitalize()} said. '
            f'"There is something stuck under my {footwear.label}."'
        )


def parent_word(world: World) -> str:
    return world.get("parent").label_word.upper()


def reveal_blocked(world: World, parent: Entity, child: Entity, sharp: SharpThing, footwear: Footwear) -> None:
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt down and turned the {footwear.label} gently. "
        f"{sharp.found_line}"
    )
    world.say(
        f'"Surprise," {parent.pronoun()} said softly. "Your {footwear.label} caught it before it touched you."'
    )
    world.say(
        f'{child.id} let out a long breath. "So the point stayed outside?" {child.pronoun()} asked. '
        f'"Exactly," {parent.label_word} said.'
    )


def reveal_wound(world: World, parent: Entity, child: Entity, sharp: SharpThing) -> None:
    point = world.get("point")
    point.meters["found"] += 1
    world.say(
        f"{parent.label_word.capitalize()} lifted {child.pronoun('possessive')} foot and saw the tiny "
        f"red spot. Then {parent.pronoun()} spotted {sharp.phrase} {sharp.found_line.lower()}."
    )
    if child.meters["tetanus_risk"] >= THRESHOLD:
        world.say(
            f'"It is a little poke," {parent.label_word} said, keeping {parent.pronoun("possessive")} voice calm. '
            f'"Because that point was dirty, we should clean it well and let the doctor think about tetanus."'
        )
    else:
        world.say(
            f'"It is a little poke," {parent.label_word} said. "We will clean it right away and take good care of it."'
        )


def treat(world: World, parent: Entity, child: Entity, care: CarePlan) -> None:
    if care.cleans:
        child.meters["cleaned"] += 1
    if care.clinic:
        child.meters["checked"] += 1
    propagate(world, narrate=False)
    world.say(care.text.format(parent=parent.label_word.capitalize(), child=child.id))
    if child.meters["checked"] >= THRESHOLD:
        world.say(
            f'"The nurse said I was brave," {child.id} whispered later. "{child.pronoun().capitalize()} did," '
            f'{parent.label_word} answered.'
        )


def safe_return(world: World, child: Entity, parent: Entity, gift: SurpriseGift, footwear: Footwear, punctured: bool) -> None:
    child.memes["joy"] += 1
    child.memes["sleepy"] += 1
    if punctured:
        world.say(
            f"When they got home, the house was quiet again, as if bedtime had been waiting kindly at the door."
        )
        world.say(
            f"{parent.label_word.capitalize()} showed {child.id} a surprise: {gift.phrase} that {gift.glow}."
        )
        world.say(
            f'"For me?" {child.id} asked. "{parent.pronoun().capitalize()} thought a brave foot deserved a bright ending," '
            f'{parent.label_word} said.'
        )
    else:
        world.say(
            f"Back inside, {parent.label_word} set the dangerous thing far away and brought out a surprise: "
            f"{gift.phrase} that {gift.glow}."
        )
        world.say(
            f'"Now your feet can rest," {parent.pronoun()} said. "{footwear.label.capitalize()} did their job, '
            f'and these are for the cozy part of the night."'
        )
    world.say(
        f"Soon {child.id} was tucked in, looking at the little surprise and feeling the room grow still and safe."
    )


def lesson(world: World, child: Entity, parent: Entity, care: Optional[CarePlan], sharp: SharpThing, punctured: bool) -> None:
    if punctured:
        if child.meters["tetanus_risk"] >= THRESHOLD:
            world.say(
                f'"What is tetanus?" {child.id} asked into the pillow of {parent.pronoun("possessive")} shoulder.'
            )
            world.say(
                f'"Tetanus is a sickness doctors try to prevent when a dirty sharp thing pokes skin," '
                f'{parent.label_word} said. "That is why we cleaned the spot and let the clinic check you."'
            )
        else:
            world.say(
                f'"Next time I will call you first," {child.id} said. "{parent.pronoun().capitalize()} like that plan," '
                f'{parent.label_word} answered.'
            )
    else:
        world.say(
            f'"I did not know shoes could save a foot," {child.id} murmured. "{parent.pronoun().capitalize()} can," '
            f'{parent.label_word} said, kissing the top of {child.pronoun("possessive")} head.'
        )
    if care is not None:
        world.say(f'"{care.lesson}" {parent.label_word} added.')


def tell(place: Place, sharp: SharpThing, footwear: Footwear, care: CarePlan,
         gift: SurpriseGift, child_name: str = "Mila", child_gender: str = "girl",
         parent_type: str = "mother", child_trait: str = "curious") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[child_trait],
        label=child_name,
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    shoe = world.add(Entity(
        id="footwear",
        type="footwear",
        label=footwear.label,
        phrase=footwear.phrase,
        protective=footwear.protective,
        coverage=footwear.coverage,
        tags=set(footwear.tags),
    ))
    shoe.worn_by = child.id
    point = world.add(Entity(
        id="point",
        type="sharp",
        label=sharp.label,
        phrase=sharp.phrase,
        dirty_point=sharp.dirty_point,
        sharp=True,
        tags=set(sharp.tags),
    ))

    bedtime_setup(world, child, parent, place, footwear)
    world.para()
    warn(world, child, parent, place, sharp)
    step_and_turn(world, child, sharp, footwear)

    punctured = child.meters["puncture"] >= THRESHOLD
    world.para()
    if punctured:
        reveal_wound(world, parent, child, sharp)
        treat(world, parent, child, care)
    else:
        reveal_blocked(world, parent, child, sharp, footwear)

    world.para()
    lesson(world, child, parent, care if punctured else None, sharp, punctured)
    safe_return(world, child, parent, gift, footwear, punctured)

    outcome = "treated" if punctured else "blocked"
    world.facts.update(
        place=place,
        sharp_cfg=sharp,
        footwear_cfg=footwear,
        care=care,
        gift=gift,
        child=child,
        parent=parent,
        point=point,
        punctured=punctured,
        tetanus_risk=child.meters["tetanus_risk"] >= THRESHOLD,
        checked=child.meters["checked"] >= THRESHOLD,
        outcome=outcome,
    )
    return world


PLACES = {
    "shed": Place(
        id="shed",
        label="the garden shed",
        bedtime_pull="the little watering can with the painted moon on it",
        detail="The night air smelled like mint leaves, and the shed door stood half open.",
        where_object="near the old wood by the wall",
        tags={"shed"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        bedtime_pull="the tiny toy boat left by the flower pot",
        detail="The porch boards were cool, and one moth circled the light like a sleepy fairy.",
        where_object="beside the flower boxes",
        tags={"porch"},
    ),
    "garage": Place(
        id="garage",
        label="the garage",
        bedtime_pull="the small red bell on the scooter handle",
        detail="The garage smelled like chalk and bicycles, and the big door was open a crack.",
        where_object="near the tool shelf",
        tags={"garage"},
    ),
}

SHARPS = {
    "nail": SharpThing(
        id="nail",
        label="nail",
        phrase="a rusty nail",
        sound="Ow!",
        dirty_point=True,
        poke_hardness=3,
        found_line="There, beside the wall, lay a rusty nail with a bent little head.",
        tags={"nail", "tetanus", "sharp"},
    ),
    "tack": SharpThing(
        id="tack",
        label="tack",
        phrase="an old carpet tack",
        sound="Eep!",
        dirty_point=True,
        poke_hardness=2,
        found_line="There on the floor was an old carpet tack, dark with dust.",
        tags={"tack", "tetanus", "sharp"},
    ),
    "thorn": SharpThing(
        id="thorn",
        label="thorn",
        phrase="a long rose thorn",
        sound="Oh!",
        dirty_point=False,
        poke_hardness=2,
        found_line="A long rose thorn had rolled in from a garden pot.",
        tags={"thorn", "sharp"},
    ),
}

FOOTWEAR = {
    "boots": Footwear(
        id="boots",
        label="boots",
        phrase="little rubber boots",
        coverage=3.0,
        protective=True,
        plural=True,
        bedtime_feel="They made soft thump-thump sounds on the floorboards.",
        tags={"boots", "protective"},
    ),
    "sneakers": Footwear(
        id="sneakers",
        label="sneakers",
        phrase="old sneakers",
        coverage=2.0,
        protective=True,
        plural=True,
        bedtime_feel="Their laces were loose from the day, but they still hugged the feet.",
        tags={"sneakers"},
    ),
    "slippers": Footwear(
        id="slippers",
        label="slippers",
        phrase="sleepy bunny slippers",
        coverage=1.0,
        protective=False,
        plural=True,
        bedtime_feel="Their floppy ears bobbed every time {child} walked.".replace("{child}", "the child"),
        tags={"slippers", "bedtime"},
    ),
    "barefoot": Footwear(
        id="barefoot",
        label="bare feet",
        phrase="bare feet",
        coverage=0.0,
        protective=False,
        plural=True,
        bedtime_feel="The boards felt cool under each careful step.",
        tags={"barefoot"},
    ),
}

CARE = {
    "wash_and_clinic": CarePlan(
        id="wash_and_clinic",
        label="wash and clinic",
        sense=3,
        cleans=True,
        clinic=True,
        text=(
            '{parent} carried {child} to the sink, washed the little spot with warm water and soap, '
            'wrapped it in a clean bandage, and then they took a quiet drive to the evening clinic.'
        ),
        lesson="When skin gets poked by a dirty sharp thing, we clean it and let a doctor decide what comes next.",
        qa_text="They washed the wound, covered it with a clean bandage, and went to the clinic for a tetanus check.",
        tags={"soap", "doctor", "clinic", "tetanus"},
    ),
    "wash_and_call": CarePlan(
        id="wash_and_call",
        label="wash and call",
        sense=2,
        cleans=True,
        clinic=True,
        text=(
            '{parent} washed the little spot with soap and water, put on a clean bandage, '
            'and called the nurse line, which sent them to the clinic for a quick check.'
        ),
        lesson="A calm phone call can help a grown-up decide when a doctor should check a wound.",
        qa_text="They washed the wound, bandaged it, and called for medical advice before going to the clinic.",
        tags={"soap", "doctor", "clinic", "tetanus"},
    ),
    "wash_only": CarePlan(
        id="wash_only",
        label="wash only",
        sense=1,
        cleans=True,
        clinic=False,
        text=(
            '{parent} washed the little spot and tucked {child} straight into bed.'
        ),
        lesson="A dirty puncture may need more than a quick rinse.",
        qa_text="They only washed the wound.",
        tags={"soap"},
    ),
    "kiss_it": CarePlan(
        id="kiss_it",
        label="kiss it better",
        sense=0,
        cleans=False,
        clinic=False,
        text=(
            '{parent} kissed the foot and said it would be fine.'
        ),
        lesson="Kindness matters, but a dirty puncture still needs proper care.",
        qa_text="They only gave comfort and did not clean or check the wound.",
        tags=set(),
    ),
}

SURPRISES = {
    "star_bandage": SurpriseGift(
        id="star_bandage",
        label="star bandage",
        phrase="a packet of star bandages",
        glow="shone silver under the lamp",
        tags={"bandage", "surprise"},
    ),
    "moon_sticker": SurpriseGift(
        id="moon_sticker",
        label="moon sticker",
        phrase="a moon-and-cloud sticker from the clinic",
        glow="looked pale and bright, like a tiny night sky",
        tags={"sticker", "surprise"},
    ),
    "glow_socks": SurpriseGift(
        id="glow_socks",
        label="glow socks",
        phrase="a pair of soft socks with little glowing stars",
        glow="made the blankets look sprinkled with tiny lights",
        tags={"socks", "surprise"},
    ),
}

GIRL_NAMES = ["Mila", "Lina", "Nora", "Lucy", "Ava", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Leo", "Ben", "Finn", "Sam", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "gentle", "sleepy", "brave", "careful", "soft-voiced"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for sharp_id, sharp in SHARPS.items():
            for footwear_id, footwear in FOOTWEAR.items():
                if puncture_happens(sharp, footwear):
                    combos.append((place, sharp_id, footwear_id))
    return combos


@dataclass
class StoryParams:
    place: str
    sharp: str
    footwear: str
    care: str
    surprise: str
    child_name: str
    child_gender: str
    parent: str
    child_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "tetanus": [
        (
            "What is tetanus?",
            "Tetanus is a dangerous sickness that doctors work to prevent after a dirty sharp thing pokes skin. That is why grown-ups take puncture wounds seriously."
        )
    ],
    "nail": [
        (
            "Why can an old nail be dangerous?",
            "An old nail can be sharp and dirty. If it pokes your skin, it can make a deep little wound that needs a grown-up's help."
        )
    ],
    "tack": [
        (
            "What is a tack?",
            "A tack is a small sharp pin used to hold things down. Even small sharp things can hurt bare skin."
        )
    ],
    "thorn": [
        (
            "Why can a thorn hurt?",
            "A thorn has a hard point that can poke skin. Even a tiny poke should be washed and shown to a grown-up."
        )
    ],
    "boots": [
        (
            "Why are boots safer around sharp things?",
            "Boots have thick soles that help keep points from reaching your feet. Strong shoes can turn a poke into a near miss."
        )
    ],
    "soap": [
        (
            "Why do you wash a cut or puncture with soap and water?",
            "Soap and water help clean away dirt and germs. Cleaning a wound quickly is one of the first smart steps a grown-up takes."
        )
    ],
    "doctor": [
        (
            "When should a grown-up call a doctor for a puncture wound?",
            "A grown-up should call or visit a doctor when a sharp thing pokes the skin, especially if it was dirty. Doctors help decide if more care is needed."
        )
    ],
    "clinic": [
        (
            "What happens at a clinic?",
            "A clinic is a place where nurses and doctors check how your body is doing. They clean, look, and help make a safe plan."
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage covers a small wound and helps keep it clean. It can also make a sore spot feel more protected."
        )
    ],
    "sticker": [
        (
            "Why do some doctors give stickers?",
            "A sticker does not heal the body, but it can help a child feel proud and calm. Little kindnesses can make a hard moment gentler."
        )
    ],
}
KNOWLEDGE_ORDER = ["tetanus", "nail", "tack", "thorn", "boots", "soap", "doctor", "clinic", "bandage", "sticker"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    sharp = f["sharp_cfg"]
    place = f["place"]
    if f["outcome"] == "blocked":
        return [
            f'Write a bedtime story for a young child that includes the word "tetanus", a surprise, and gentle dialogue.',
            f"Tell a soft night story where {child.id} and {child.pronoun('possessive')} {parent.label_word} take one last peek in {place.label}, discover {sharp.phrase}, and learn that sturdy shoes prevented a poke.",
            f"Write a cozy near-miss story with whispered dialogue, a hidden sharp object, and a calming surprise before bed.",
        ]
    return [
        f'Write a bedtime story for a young child that includes the word "tetanus", a surprise, and gentle dialogue.',
        f"Tell a calm story where {child.id} gets a tiny puncture from {sharp.phrase}, {child.pronoun('possessive')} {parent.label_word} explains tetanus in a child-safe way, and bedtime still ends warmly.",
        f"Write a soft nighttime story with dialogue, a careful clinic visit, and a surprise gift that proves the child is safe at the end.",
    ]


def pair_answer(text: str) -> str:
    return text


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    sharp = f["sharp_cfg"]
    place = f["place"]
    footwear = f["footwear_cfg"]
    care = f["care"]
    gift = f["gift"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {parent.label_word}. They share one last bedtime errand that turns into a safety lesson."
        ),
        (
            f"Why did {child.id} go to {place.label} before bed?",
            f"{child.pronoun().capitalize()} wanted one last peek at {place.bedtime_pull}. That small wish is what brought {child.pronoun('object')} near the hidden sharp thing."
        ),
    ]
    if f["outcome"] == "blocked":
        qa.append(
            (
                f"What surprised {child.id}?",
                f"{child.id} discovered that {sharp.phrase} had caught under the {footwear.label} without touching skin. The surprise was that the shoe had quietly protected {child.pronoun('possessive')} foot."
            )
        )
        qa.append(
            (
                "Why was nobody hurt?",
                f"Nobody was hurt because the {footwear.label} were thick enough to stop the point. The grown-up also stayed close and checked what had happened right away."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a cozy surprise: {gift.phrase}. The final image shows {child.id} tucked in safely, with bedtime calm returned."
            )
        )
    else:
        qa.append(
            (
                f"Why did {parent.label_word} mention tetanus?",
                f"{parent.label_word.capitalize()} mentioned tetanus because {sharp.phrase} made a dirty puncture wound. The word explained why washing the wound and getting medical advice mattered."
            )
        )
        qa.append(
            (
                f"How did {parent.label_word} take care of {child.id}?",
                f"{parent.label_word.capitalize()} {care.qa_text.lower()} {child.id} was cared for with both comfort and sensible steps, not just soothing words."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly after the care was done and bedtime resumed. The surprise, {gift.phrase}, helped show that {child.id} was safe enough to rest."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["sharp_cfg"].tags) | set(f["gift"].tags)
    if f["outcome"] == "treated":
        tags |= set(f["care"].tags)
    if f["footwear_cfg"].id == "boots":
        tags.add("boots")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.coverage:
            bits.append(f"coverage={e.coverage}")
        flags = [name for name, on in (
            ("protective", e.protective),
            ("dirty_point", e.dirty_point),
            ("sharp", e.sharp),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="shed",
        sharp="nail",
        footwear="boots",
        care="wash_and_clinic",
        surprise="glow_socks",
        child_name="Mila",
        child_gender="girl",
        parent="mother",
        child_trait="curious",
    ),
    StoryParams(
        place="porch",
        sharp="tack",
        footwear="slippers",
        care="wash_and_clinic",
        surprise="moon_sticker",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        child_trait="sleepy",
    ),
    StoryParams(
        place="garage",
        sharp="thorn",
        footwear="barefoot",
        care="wash_and_call",
        surprise="star_bandage",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        child_trait="gentle",
    ),
    StoryParams(
        place="shed",
        sharp="nail",
        footwear="sneakers",
        care="wash_and_call",
        surprise="moon_sticker",
        child_name="Finn",
        child_gender="boy",
        parent="father",
        child_trait="brave",
    ),
]


ASP_RULES = r"""
puncture(F, S) :- footwear(F), sharp(S), hardness(S, H), coverage(F, C), H > C.
valid(P, S, F) :- place(P), sharp(S), footwear(F), puncture(F, S).

sensible(C) :- care(C), sense(C, N), sense_min(M), N >= M.

tetanus_risk(S, F) :- puncture(F, S), dirty_point(S).

care_enough(S, F, C) :- puncture(F, S), sensible(C), cleans(C), not tetanus_risk(S, F).
care_enough(S, F, C) :- puncture(F, S), sensible(C), cleans(C), clinic(C), tetanus_risk(S, F).

outcome(blocked) :- chosen_sharp(S), chosen_footwear(F), not puncture(F, S).
outcome(treated) :- chosen_sharp(S), chosen_footwear(F), chosen_care(C), care_enough(S, F, C).
outcome(badcare) :- chosen_sharp(S), chosen_footwear(F), chosen_care(C), puncture(F, S), not care_enough(S, F, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid, sharp in SHARPS.items():
        lines.append(asp.fact("sharp", sid))
        lines.append(asp.fact("hardness", sid, sharp.poke_hardness))
        if sharp.dirty_point:
            lines.append(asp.fact("dirty_point", sid))
    for fid, footwear in FOOTWEAR.items():
        lines.append(asp.fact("footwear", fid))
        lines.append(asp.fact("coverage", fid, int(footwear.coverage)))
    for cid, care in CARE.items():
        lines.append(asp.fact("care", cid))
        lines.append(asp.fact("sense", cid, care.sense))
        if care.cleans:
            lines.append(asp.fact("cleans", cid))
        if care.clinic:
            lines.append(asp.fact("clinic", cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_care() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_sharp", params.sharp),
        asp.fact("chosen_footwear", params.footwear),
        asp.fact("chosen_care", params.care),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    sharp = SHARPS[params.sharp]
    footwear = FOOTWEAR[params.footwear]
    care = CARE[params.care]
    if not puncture_happens(sharp, footwear):
        return "blocked"
    return "treated" if care_is_enough(sharp, footwear, care) else "badcare"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    emit(sample, trace=False, qa=False)


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_care = set(asp_sensible_care())
    python_care = {c.id for c in sensible_care()}
    if clingo_care == python_care:
        print(f"OK: sensible care matches ({sorted(clingo_care)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible care: clingo={sorted(clingo_care)} python={sorted(python_care)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            args = parser.parse_args([])
            cases.append(resolve_params(args, random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a hidden sharp thing at bedtime, a tetanus lesson, and a gentle surprise."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sharp", choices=SHARPS)
    ap.add_argument("--footwear", choices=FOOTWEAR)
    ap.add_argument("--care", choices=CARE)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.care and CARE[args.care].sense < SENSE_MIN:
        raise StoryError(explain_care_rejection(CARE[args.care]))
    if args.sharp and args.footwear and args.care:
        sharp = SHARPS[args.sharp]
        footwear = FOOTWEAR[args.footwear]
        care = CARE[args.care]
        if puncture_happens(sharp, footwear) and not care_is_enough(sharp, footwear, care):
            raise StoryError("(No story: that care plan is too weak for this puncture and possible tetanus risk.)")

    place = args.place or rng.choice(sorted(PLACES))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))

    puncture_possible = True
    if args.sharp and args.footwear:
        puncture_possible = puncture_happens(SHARPS[args.sharp], FOOTWEAR[args.footwear])

    if args.care and args.sharp and args.footwear and not puncture_possible:
        raise StoryError(explain_combo_rejection(SHARPS[args.sharp], FOOTWEAR[args.footwear]))

    if args.sharp and args.footwear:
        sharp_id = args.sharp
        footwear_id = args.footwear
    else:
        mode = rng.choice(["treated", "blocked"])
        if mode == "treated":
            choices = valid_combos()
            choices = [c for c in choices if (args.sharp is None or c[1] == args.sharp)
                       and (args.footwear is None or c[2] == args.footwear)
                       and (args.place is None or c[0] == args.place)]
            if not choices:
                raise StoryError("(No valid puncture combination matches the given options.)")
            place, sharp_id, footwear_id = rng.choice(sorted(choices))
        else:
            sharp_choices = [sid for sid in SHARPS if args.sharp is None or sid == args.sharp]
            footwear_choices = [fid for fid in FOOTWEAR if args.footwear is None or fid == args.footwear]
            blocked_choices = [
                (p, s, f)
                for p in PLACES
                for s in sharp_choices
                for f in footwear_choices
                if (args.place is None or p == args.place) and not puncture_happens(SHARPS[s], FOOTWEAR[f])
            ]
            if not blocked_choices:
                choices = valid_combos()
                choices = [c for c in choices if (args.sharp is None or c[1] == args.sharp)
                           and (args.footwear is None or c[2] == args.footwear)
                           and (args.place is None or c[0] == args.place)]
                if not choices:
                    raise StoryError("(No valid combination matches the given options.)")
                place, sharp_id, footwear_id = rng.choice(sorted(choices))
            else:
                place, sharp_id, footwear_id = rng.choice(sorted(blocked_choices))

    sharp = SHARPS[sharp_id]
    footwear = FOOTWEAR[footwear_id]

    if args.care:
        care_id = args.care
    else:
        if puncture_happens(sharp, footwear):
            care_options = [c.id for c in sensible_care() if care_is_enough(sharp, footwear, c)]
            if not care_options:
                raise StoryError("(No sensible care plan exists for this injury.)")
            care_id = rng.choice(sorted(care_options))
        else:
            care_id = "wash_and_clinic"

    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    child_trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        sharp=sharp_id,
        footwear=footwear_id,
        care=care_id,
        surprise=surprise,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.sharp not in SHARPS:
        raise StoryError(f"Unknown sharp object: {params.sharp}")
    if params.footwear not in FOOTWEAR:
        raise StoryError(f"Unknown footwear: {params.footwear}")
    if params.care not in CARE:
        raise StoryError(f"Unknown care plan: {params.care}")
    if params.surprise not in SURPRISES:
        raise StoryError(f"Unknown surprise: {params.surprise}")
    sharp = SHARPS[params.sharp]
    footwear = FOOTWEAR[params.footwear]
    care = CARE[params.care]
    if puncture_happens(sharp, footwear) and not care_is_enough(sharp, footwear, care):
        raise StoryError("(No story: the selected care plan is not sensible for this puncture.)")

    world = tell(
        place=PLACES[params.place],
        sharp=sharp,
        footwear=footwear,
        care=care,
        gift=SURPRISES[params.surprise],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible care: {', '.join(asp_sensible_care())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sharp, footwear) puncture combos:\n")
        for place, sharp, footwear in combos:
            print(f"  {place:8} {sharp:6} {footwear}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.sharp} at {p.place} in {p.footwear}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
