#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/descriptive_bra_cuisine_picnic_meadow_rhyme_moral.py
================================================================================

A standalone story world for a pirate-flavored picnic-meadow tale: two children
turn a blanket into a pirate ship, find something growing in the meadow, and
face a simple safety choice about whether found things are safe to eat.

The world is built around one grounded moral:
    Do not eat unknown plants or berries. Ask a grown-up first.

Like the other storyworlds, this script:
- models typed entities with physical meters and emotional memes,
- uses a small forward-chaining rule engine,
- renders prose from simulated state,
- generates three Q&A sets from world state,
- includes a Python reasonableness gate plus an inline ASP twin.

The seed words are woven directly into the stories:
- "descriptive" appears in the pirate-map / menu setup,
- "bra" appears as a harmless laundry mix-up in the picnic basket,
- "cuisine" appears in the picnic meal description.

Run it
------
    python storyworlds/worlds/gpt-5.4/descriptive_bra_cuisine_picnic_meadow_rhyme_moral.py
    python storyworlds/worlds/gpt-5.4/descriptive_bra_cuisine_picnic_meadow_rhyme_moral.py --find red_berries
    python storyworlds/worlds/gpt-5.4/descriptive_bra_cuisine_picnic_meadow_rhyme_moral.py --find clover
    python storyworlds/worlds/gpt-5.4/descriptive_bra_cuisine_picnic_meadow_rhyme_moral.py --response wait_and_see
    python storyworlds/worlds/gpt-5.4/descriptive_bra_cuisine_picnic_meadow_rhyme_moral.py --all --qa
    python storyworlds/worlds/gpt-5.4/descriptive_bra_cuisine_picnic_meadow_rhyme_moral.py --verify
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
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    edible: bool = False
    safe_food: bool = False
    wild_found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class PlayFrame:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    goal: str
    sendoff: str


@dataclass
class FoundThing:
    id: str
    label: str
    phrase: str
    patch: str
    warning: str
    danger: int
    safe_to_eat: bool = False
    edible: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class PicnicFood:
    id: str
    label: str
    phrase: str
    aroma: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    success: str
    failure: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_swallow(world: World) -> list[str]:
    out: list[str] = []
    found = world.get("found")
    if found.meters["tasted"] < THRESHOLD or found.safe_food:
        return out
    sig = ("swallow", found.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    eater = world.get(world.facts["instigator_id"])
    eater.meters["risk"] += found.meters["danger"]
    eater.meters["tummy"] += found.meters["danger"]
    eater.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__tummy__")
    return out


CAUSAL_RULES = [
    Rule(name="swallow", tag="physical", apply=_r_swallow),
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


def hazard_at_risk(found: FoundThing) -> bool:
    return found.edible and not found.safe_to_eat and found.danger > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def severity(found: FoundThing, bites: int) -> int:
    return found.danger + bites - 1


def is_resolved(response: Response, found: FoundThing, bites: int) -> bool:
    return response.power >= severity(found, bites)


def predict_tummy(world: World) -> dict:
    sim = world.copy()
    sim.get("found").meters["tasted"] += 1
    propagate(sim, narrate=False)
    eater = sim.get(sim.facts["instigator_id"])
    return {
        "risky": eater.meters["risk"] >= THRESHOLD,
        "tummy": eater.meters["tummy"],
    }


def play_setup(world: World, a: Entity, b: Entity, parent: Entity,
               frame: PlayFrame, food: PicnicFood) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a breezy afternoon in the picnic meadow, {a.id} and {b.id} spread a blanket "
        f"and turned it into {frame.scene}. {frame.rig}"
    )
    world.say(
        f'The basket held the nicest picnic cuisine: {food.phrase}, and {food.aroma}. '
        f'On top of the napkins sat one clean striped bra that had slipped in with the laundry, '
        f'which made everyone laugh.'
    )
    world.say(
        f"{a.id} had drawn a descriptive treasure menu in crayon, with arrows pointing to the "
        f"apple slices and sandwiches as if they were gold."
    )
    world.say(
        f'"{frame.titles[0]} {a.id} and {frame.titles[1]} {b.id}!" {a.id} cried. '
        f'"Let\'s find {frame.goal}!"'
    )
    world.facts["parent_word"] = parent.label_word


def spot_find(world: World, b: Entity, found: FoundThing) -> None:
    world.say(
        f"Beyond the blanket, {b.id} noticed {found.patch}. They looked shiny in the grass, "
        f"almost like treasure left by the meadow itself."
    )
    world.say(
        f'{b.id} pointed. "Those little things look interesting," {b.pronoun()} said.'
    )


def tempt(world: World, a: Entity, found: FoundThing) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} leaned close. "Maybe that can be pirate cuisine," {a.pronoun()} said. '
        f'"I could taste just one."'
    )


def warn(world: World, b: Entity, a: Entity, parent: Entity, found: FoundThing) -> None:
    pred = predict_tummy(world)
    b.memes["caution"] += 1
    world.facts["predicted_tummy"] = pred["tummy"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f' {b.pronoun().capitalize()} sounded sure, not bossy but brave.'
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, we do not eat things we find in the grass. '
        f'{parent.label_word.capitalize()} says to ask first. {found.warning}"{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, food: PicnicFood) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at {b.id}, then at the little find again, and the brave look melted out of '
        f'{a.pronoun("possessive")} face. "All right," {a.pronoun()} said. "Unknown food can stay unknown."'
    )
    world.say(
        f'Together they carried the question back to {parent.label_word}. Instead of tasting the meadow, '
        f'they opened the basket and shared {food.label}.'
    )


def defy(world: World, a: Entity, b: Entity, found: FoundThing) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"Don\'t fuss," {a.id} said. Because {a.id} was older, {b.id} could not stop '
            f'{a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"Don\'t fuss," {a.id} said, and reached for {found.label} anyway.')


def taste(world: World, a: Entity, found: FoundThing, bites: int) -> None:
    found_ent = world.get("found")
    found_ent.meters["tasted"] += 1
    found_ent.meters["bites"] = float(bites)
    propagate(world, narrate=False)
    if bites == 1:
        bit_text = "just one tiny bite"
    elif bites == 2:
        bit_text = "two quick bites"
    else:
        bit_text = "three hasty bites"
    world.say(
        f"{a.id} nibbled {bit_text}. At once, the adventure feeling went thin and wrong."
    )
    if a.meters["tummy"] >= THRESHOLD:
        world.say(
            f"{a.pronoun().capitalize()} pressed a hand to {a.pronoun('possessive')} tummy and made a small, unhappy face."
        )


def alarm(world: World, b: Entity, a: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}! {a.id} ate something from the meadow!" {b.id} shouted.')


def rescue(world: World, parent: Entity, response: Response, a: Entity, found: FoundThing) -> None:
    a.meters["risk"] = 0.0
    a.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came fast and calm. {parent.pronoun().capitalize()} {response.success}."
    )
    world.say(
        f"Soon the scary feeling eased, and {a.id} stayed tucked beside the blanket instead of getting sicker."
    )


def rescue_fail(world: World, parent: Entity, response: Response, a: Entity) -> None:
    a.memes["fear"] += 1
    a.meters["risk"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {response.failure}."
    )
    world.say(
        f"But {a.id}'s tummy still hurt, and the picnic had to end early."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, found: FoundThing) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say("For a moment, the meadow felt very quiet except for the bees in the clover.")
    world.say(
        f'Then {parent.label_word.capitalize()} knelt on the blanket and hugged them close. '
        f'"I am glad you called me," {parent.pronoun()} said. "Food from our basket is for eating. '
        f'{found.label.capitalize()} from the meadow are for asking about first."'
    )
    world.say(
        f'"If you don\'t know, let it go," {b.id} whispered.'
    )
    world.say(
        f'"If you don\'t know, let it go," {a.id} repeated, and this time the rhyme felt true.'
    )


def clinic_ending(world: World, parent: Entity, a: Entity, b: Entity, found: FoundThing) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} packed the basket, folded the blanket ship, and took {a.id} to the clinic to be checked."
    )
    world.say(
        f"{a.id} was safe, but tired and sorry. All the way home, {b.id} held the crayon map and did not tease even once."
    )
    world.say(
        f"They never forgot what the picnic meadow taught them: if you do not know what a growing thing is, you ask before you taste."
    )


def safe_feast(world: World, a: Entity, b: Entity, parent: Entity,
               frame: PlayFrame, food: PicnicFood) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"After that, {parent.label_word} spread out the safe feast again, and the picnic cuisine smelled even better than before."
    )
    world.say(
        f"{a.id} bit into {food.label}, and {b.id} laughed because treasure tasted much better when everybody knew what it was."
    )
    world.say(
        f'Together they sang, "Know then go; ask then chew," and the rhyme skipped across the grass like a little song.'
    )
    world.say(
        f"In the gold-leaning light, the blanket ship set sail once more, and the small pirates {frame.sendoff} -- wiser, gentler, and safe."
    )


def tell(frame: PlayFrame, found: FoundThing, food: PicnicFood, response: Response,
         instigator: str = "Tom", instigator_gender: str = "boy",
         cautioner: str = "Lily", cautioner_gender: str = "girl",
         parent_type: str = "mother", trait: str = "careful",
         relation: str = "siblings", instigator_age: int = 6,
         cautioner_age: int = 4, bites: int = 1) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(
        id="found",
        type="found_food",
        label=found.label,
        phrase=found.phrase,
        edible=found.edible,
        safe_food=found.safe_to_eat,
        wild_found=True,
        tags=set(found.tags),
    ))
    world.get("found").meters["danger"] = float(found.danger)

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    world.facts["instigator_id"] = a.id

    play_setup(world, a, b, parent, frame, food)
    spot_find(world, b, found)

    world.para()
    tempt(world, a, found)
    warn(world, b, a, parent, found)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent, food)
        world.para()
        safe_feast(world, a, b, parent, frame, food)
        ending = "averted"
        resolved = True
    else:
        defy(world, a, b, found)
        world.para()
        taste(world, a, found, bites)
        alarm(world, b, a, parent)
        ok = is_resolved(response, found, bites)
        world.para()
        if ok:
            rescue(world, parent, response, a, found)
            lesson(world, parent, a, b, found)
            world.para()
            safe_feast(world, a, b, parent, frame, food)
            ending = "contained"
            resolved = True
        else:
            rescue_fail(world, parent, response, a)
            clinic_ending(world, parent, a, b, found)
            ending = "clinic"
            resolved = False

    world.facts.update(
        frame=frame,
        found_cfg=found,
        food=food,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        relation=relation,
        bites=bites,
        tasted=world.get("found").meters["tasted"] >= THRESHOLD,
        predicted_risk=world.facts.get("predicted_tummy", 0),
        outcome=ending,
        resolved=resolved,
        rhyme="If you don't know, let it go.",
        moral="Ask a grown-up before eating things you find outside.",
    )
    return world


FRAMES = {
    "pirates": PlayFrame(
        id="pirates",
        scene="a bright pirate deck in a sea of waving grass",
        rig="The picnic blanket was their ship, a spoon became a silver hook, and a striped napkin served as a sail.",
        titles=("Captain", "Scout"),
        goal="the hidden snack island",
        sendoff="sailed after a safe new treasure map",
    ),
    "corsairs": PlayFrame(
        id="corsairs",
        scene="a meadow sea where every daisy looked like a tiny white foam-crest",
        rig="The basket was their treasure chest, two cups were lookout towers, and the blanket corners snapped like sails in the wind.",
        titles=("Captain", "Matey"),
        goal="the clover cove",
        sendoff="sailed toward clover cove with full bellies and careful hearts",
    ),
}

FINDS = {
    "red_berries": FoundThing(
        id="red_berries",
        label="red berries",
        phrase="a patch of bright red berries",
        patch="a patch of bright red berries under a hedge",
        warning="Some berries are not safe, even when they look pretty.",
        danger=2,
        safe_to_eat=False,
        edible=True,
        tags={"berries", "wild_food"},
    ),
    "white_mushroom": FoundThing(
        id="white_mushroom",
        label="a white mushroom",
        phrase="a small white mushroom",
        patch="one white mushroom standing up from the damp earth",
        warning="Wild mushrooms can make people very sick.",
        danger=3,
        safe_to_eat=False,
        edible=True,
        tags={"mushroom", "wild_food"},
    ),
    "purple_flower": FoundThing(
        id="purple_flower",
        label="a purple flower",
        phrase="a small purple flower",
        patch="a tuft of purple flowers beside the blanket",
        warning="Flowers in the meadow are for looking at, not tasting.",
        danger=2,
        safe_to_eat=False,
        edible=True,
        tags={"flower", "wild_food"},
    ),
    "clover": FoundThing(
        id="clover",
        label="clover leaves",
        phrase="some clover leaves",
        patch="a soft patch of clover",
        warning="This one was only clover.",
        danger=0,
        safe_to_eat=True,
        edible=True,
        tags={"clover"},
    ),
}

FOODS = {
    "sandwiches": PicnicFood(
        id="sandwiches",
        label="little triangle sandwiches",
        phrase="little triangle sandwiches and sliced pears",
        aroma="the bread smelled warm and the butter smelled sweet",
        tags={"sandwich", "picnic_food"},
    ),
    "muffins": PicnicFood(
        id="muffins",
        label="blueberry muffins",
        phrase="blueberry muffins and cheese cubes",
        aroma="the muffins smelled like warm sugar and sun",
        tags={"muffin", "picnic_food"},
    ),
    "salad": PicnicFood(
        id="salad",
        label="pasta salad",
        phrase="pasta salad and strawberry slices",
        aroma="the strawberries smelled bright and fresh",
        tags={"salad", "picnic_food"},
    ),
}

RESPONSES = {
    "rinse_and_call": Response(
        id="rinse_and_call",
        sense=3,
        power=4,
        success="had the little bite spat out, rinsed the mouth with water, and called the poison-help nurse right away",
        failure="rinsed the mouth and waited, but it was not enough to settle the worry quickly",
        qa_text="had the mouth rinsed and called the poison-help nurse",
        tags={"poison_help", "rinse"},
    ),
    "call_doctor": Response(
        id="call_doctor",
        sense=3,
        power=3,
        success="called the doctor, followed the careful instructions, and kept everyone calm on the blanket",
        failure="called the doctor, but the tummyache still meant the picnic had to end and a clinic visit was needed",
        qa_text="called the doctor and followed the instructions",
        tags={"doctor"},
    ),
    "wait_and_see": Response(
        id="wait_and_see",
        sense=1,
        power=1,
        success="just sat and hoped the feeling would pass",
        failure="waited to see what would happen, which was not a safe choice for an unknown bite",
        qa_text="waited and hoped",
        tags={"bad_response"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "clever", "cautious", "thoughtful", "sensible"]


@dataclass
class StoryParams:
    frame: str
    find: str
    food: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    bites: int = 1
    seed: Optional[int] = None


KNOWLEDGE = {
    "berries": [
        (
            "Why should you not eat berries you find outside unless a grown-up says they are safe?",
            "Some wild berries are safe, but some can hurt your tummy or make you very sick. If you do not know which is which, you should ask a grown-up first."
        )
    ],
    "mushroom": [
        (
            "Why can wild mushrooms be dangerous?",
            "Many wild mushrooms are not food for children, and some can make people very sick. That is why you never taste one unless a knowledgeable grown-up says it is safe."
        )
    ],
    "flower": [
        (
            "Should children eat flowers they find in a meadow?",
            "No, not unless a grown-up has prepared a safe flower to eat. Meadow flowers are usually for looking at, not tasting."
        )
    ],
    "wild_food": [
        (
            "What should you do before eating something you find outside?",
            "Ask a grown-up first and wait for an answer. Looking is safe, but tasting is only safe when you know what it is."
        )
    ],
    "poison_help": [
        (
            "Who can a grown-up call if a child eats something unknown?",
            "A grown-up can call a doctor or a poison-help line for fast advice. They know what questions to ask and what to do next."
        )
    ],
    "rinse": [
        (
            "Why might a grown-up rinse a child's mouth after an unsafe bite?",
            "Rinsing can help wash away the taste and any little bits still in the mouth. A grown-up still needs to get proper advice right away."
        )
    ],
    "doctor": [
        (
            "Why is it smart to call a doctor after eating something unknown?",
            "A doctor can help decide whether the child is safe or needs more care. Calling quickly gives the child a better chance of getting the right help."
        )
    ],
    "picnic_food": [
        (
            "Why is food from your picnic basket safer than food you find in the grass?",
            "Picnic food was packed by grown-ups who know what it is. Plants in the grass can look pretty even when they are not meant to be eaten."
        )
    ],
}
KNOWLEDGE_ORDER = ["berries", "mushroom", "flower", "wild_food", "poison_help", "rinse", "doctor", "picnic_food"]


CURATED = [
    StoryParams(
        frame="pirates",
        find="red_berries",
        food="sandwiches",
        response="rinse_and_call",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=6,
        cautioner_age=4,
        bites=1,
    ),
    StoryParams(
        frame="corsairs",
        find="white_mushroom",
        food="muffins",
        response="call_doctor",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        relation="friends",
        instigator_age=5,
        cautioner_age=5,
        bites=1,
    ),
    StoryParams(
        frame="pirates",
        find="purple_flower",
        food="salad",
        response="call_doctor",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
        bites=2,
    ),
    StoryParams(
        frame="corsairs",
        find="red_berries",
        food="muffins",
        response="rinse_and_call",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Tom",
        cautioner_gender="boy",
        parent="father",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        bites=1,
    ),
    StoryParams(
        frame="pirates",
        find="white_mushroom",
        food="sandwiches",
        response="call_doctor",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Ava",
        cautioner_gender="girl",
        parent="mother",
        trait="sensible",
        relation="siblings",
        instigator_age=6,
        cautioner_age=4,
        bites=2,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for frame in FRAMES:
        for fid, found in FINDS.items():
            if not hazard_at_risk(found):
                continue
            for food in FOODS:
                combos.append((frame, fid, food))
    return combos


def explain_rejection(found: FoundThing) -> str:
    if found.safe_to_eat or not found.danger:
        return (
            f"(No story: {found.phrase} is not a good hazard here, so there is no honest danger, no rescue, "
            f"and no strong lesson. Pick an unknown berry, flower, or mushroom instead.)"
        )
    if not found.edible:
        return (
            f"(No story: {found.phrase} is not something a child would plausibly try to eat here.)"
        )
    return "(No story: this meadow find does not make a clear safety problem.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of the safer responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    found = FINDS[params.find]
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_resolved(RESPONSES[params.response], found, params.bites) else "clinic"


ASP_RULES = r"""
hazard(F) :- edible(F), not safe_found(F), danger(F, D), D > 0.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Frame, F, Food) :- frame(Frame), hazard(F), food(Food).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

severity(D + B - 1) :- chosen_find(F), danger(F, D), bites(B).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(clinic) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fid in FRAMES:
        lines.append(asp.fact("frame", fid))
    for fid, found in FINDS.items():
        lines.append(asp.fact("found", fid))
        if found.edible:
            lines.append(asp.fact("edible", fid))
        if found.safe_to_eat:
            lines.append(asp.fact("safe_found", fid))
        lines.append(asp.fact("danger", fid, found.danger))
    for food in FOODS:
        lines.append(asp.fact("food", food))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_find", params.find),
        asp.fact("chosen_response", params.response),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
        asp.fact("bites", params.bites),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    if not sample.story or "{" in sample.story or "}" in sample.story:
        raise StoryError("smoke test failed: story text is empty or contains unresolved braces")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke generate/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    found = f["found_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a pirate-flavored meadow picnic story for a 3-to-5-year-old that uses the words "descriptive", "bra", and "cuisine" and includes a rhyme.',
            f"Tell a gentle story where {a.id} wants to taste {found.label} in a picnic meadow, but {b.id} warns {a.pronoun('object')} and no one gets hurt.",
            'Write a simple moral story with the line "If you don\'t know, let it go," where children choose safe picnic food instead of unknown meadow food.',
        ]
    if outcome == "contained":
        return [
            'Write a pirate-tale-style picnic meadow story with rhyme and a clear moral about asking a grown-up before tasting things found outside.',
            f"Tell a meadow adventure where {a.id} tastes {found.label}, a calm parent helps right away, and the story ends safely with a lesson.",
            'Write a descriptive child-facing story that uses the words "descriptive", "bra", and "cuisine" naturally and ends with a safe picnic again.',
        ]
    return [
        'Write a cautionary pirate picnic story for a young child where an unknown meadow snack leads to a clinic visit but everyone stays safe.',
        f"Tell a story where {a.id} ignores a warning about {found.label}, and the picnic ends early because the grown-up must take safety seriously.",
        'Write a rhyming moral tale that teaches children not to eat unknown plants or berries from outside.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    found = f["found_cfg"]
    food = f["food"]
    frame = f["frame"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who turned a blanket into a pirate ship in the picnic meadow. "
            f"It is also about their {pw}, who helped them make a safe choice."
        ),
        (
            "What were they pretending at the picnic?",
            f"They were pretending the blanket was part of {frame.scene}. "
            f"The pirate game made the meadow feel exciting, which is why the little wild find seemed like treasure."
        ),
        (
            f"What did {a.id} want to taste?",
            f"{a.id} wanted to taste {found.label} that had been growing in the meadow. "
            f"{a.pronoun().capitalize()} thought it might be pirate cuisine, even though nobody knew if it was safe."
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned {a.id} because the children did not know what the meadow find really was. "
            f"Unknown berries, flowers, or mushrooms can hurt your tummy, so the safe thing was to ask {pw} first."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after the warning?",
            f"{a.id} listened and backed down, so no one ate the meadow find at all. "
            f"Then the children went back to the basket and ate {food.label} instead."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a safe feast on the blanket ship and a rhyme to remember the rule. "
            f"The ending proves the children changed because they chose known picnic food instead of a risky guess."
        ))
    elif f["outcome"] == "contained":
        response = f["response"]
        qa.append((
            f"How did {a.id}'s {pw} help?",
            f"{pw.capitalize()} {response.qa_text}. "
            f"The help worked because the grown-up acted quickly and treated the bite like a real safety problem."
        ))
        qa.append((
            "What rhyme did they learn, and what did it mean?",
            f'They learned, "{f["rhyme"]}" It means that if you do not know whether something outside is food, you leave it alone and ask first.'
        ))
        qa.append((
            "What is the moral of the story?",
            f'{f["moral"]} The story shows this by letting a risky bite happen once, then ending with safe picnic food and a wiser choice.'
        ))
    else:
        qa.append((
            "Did the picnic stay happy the whole time?",
            f"No. {a.id}'s tummy still hurt, so the picnic had to end early and {pw} took {a.pronoun('object')} to the clinic. "
            f"Everyone stayed safe, but the ending shows that unknown bites can ruin a fun day very fast."
        ))
        qa.append((
            "What lesson did the children remember after the clinic visit?",
            f"They remembered never to taste a growing thing from outside without asking first. "
            f"The lesson felt stronger because the problem did not vanish right away."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["found_cfg"].tags) | set(f["food"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["response"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirate-flavored picnic meadow safety stories about not eating unknown things."
    )
    ap.add_argument("--frame", choices=FRAMES)
    ap.add_argument("--find", choices=FINDS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--bites", type=int, choices=[1, 2, 3], help="how many quick bites are taken before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render a curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump the world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.find:
        found = FINDS.get(args.find)
        if found is None:
            raise StoryError(f"(No story: unknown find '{args.find}'.)")
        if not hazard_at_risk(found):
            raise StoryError(explain_rejection(found))
    if args.response:
        response = RESPONSES.get(args.response)
        if response is None:
            raise StoryError(f"(No story: unknown response '{args.response}'.)")
        if response.sense < SENSE_MIN:
            raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.frame is None or combo[0] == args.frame)
        and (args.find is None or combo[1] == args.find)
        and (args.food is None or combo[2] == args.food)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    frame, find, food = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    bites = args.bites if args.bites is not None else rng.choice([1, 1, 2])

    return StoryParams(
        frame=frame,
        find=find,
        food=food,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        bites=bites,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        frame = FRAMES[params.frame]
        found = FINDS[params.find]
        food = FOODS[params.food]
        response = RESPONSES[params.response]
    except KeyError as exc:
        raise StoryError(f"(No story: invalid parameter value {exc}.)") from exc

    if not hazard_at_risk(found):
        raise StoryError(explain_rejection(found))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        frame=frame,
        found=found,
        food=food,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        bites=params.bites,
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (frame, find, food) combos:\n")
        for frame, find, food in combos:
            print(f"  {frame:8} {find:14} {food}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.find} in the meadow ({p.frame}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
