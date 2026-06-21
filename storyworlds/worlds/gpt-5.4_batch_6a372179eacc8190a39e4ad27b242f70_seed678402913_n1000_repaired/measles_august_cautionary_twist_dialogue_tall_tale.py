#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/measles_august_cautionary_twist_dialogue_tall_tale.py
================================================================================

A standalone story world for a tall-tale August outing with a cautionary turn:
a bold child wants to hurry a recently recovered cousin into a grand summer
adventure, but the August heat and too-soon exertion after measles make that a
bad idea. A grown-up steps in with a sensible cooling-and-rest plan, or the day
ends early when the fix is too weak.

The stories are state-driven, with typed entities carrying physical meters and
emotional memes. A small reasonableness gate rejects weak "fixes", and an inline
ASP twin mirrors the gate and outcome logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/measles_august_cautionary_twist_dialogue_tall_tale.py
    python storyworlds/worlds/gpt-5.4/measles_august_cautionary_twist_dialogue_tall_tale.py --place orchard --adventure bell_hill
    python storyworlds/worlds/gpt-5.4/measles_august_cautionary_twist_dialogue_tall_tale.py --remedy paper_fan
    python storyworlds/worlds/gpt-5.4/measles_august_cautionary_twist_dialogue_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/measles_august_cautionary_twist_dialogue_tall_tale.py --verify
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
AUGUST_HEAT = 1


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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    vista: str
    affords: set[str] = field(default_factory=set)
    twist_true: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Adventure:
    id: str
    verb: str
    path: str
    boast: str
    spectacle: str
    strain: int
    dust: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    sense: int
    cool: int
    rest: int
    ride: int
    label: str
    phrase: str
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    @property
    def power(self) -> int:
        return self.cool + self.rest + self.ride


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    cousin = world.get("cousin")
    if cousin.meters["fatigue"] + cousin.meters["heat"] < 3:
        return out
    sig = ("wobble", cousin.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cousin.meters["wobble"] += 1
    cousin.memes["fear"] += 1
    world.get("guardian").memes["urgency"] += 1
    out.append("__wobble__")
    return out


def _r_bold_guilt(world: World) -> list[str]:
    out: list[str] = []
    bold = world.get("bold")
    cousin = world.get("cousin")
    if cousin.meters["wobble"] < THRESHOLD or bold.memes["boast"] < THRESHOLD:
        return out
    sig = ("guilt", bold.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bold.memes["guilt"] += 1
    out.append("__guilt__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="guilt", tag="social", apply=_r_bold_guilt),
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
    if narrate:
        for sent in produced:
            if sent == "__wobble__":
                cousin = world.get("cousin")
                world.say(
                    f"Then {cousin.id}'s knees gave a tiny shake, and the big August world "
                    f"suddenly seemed too bright."
                )
            elif sent == "__guilt__":
                bold = world.get("bold")
                world.say(
                    f"{bold.id}'s brag shrank to the size of a pebble."
                )
    return produced


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def adventure_allowed(place: Place, adventure: Adventure) -> bool:
    return adventure.id in place.affords


def severity_of(adventure: Adventure, delay: int) -> int:
    return AUGUST_HEAT + adventure.strain + delay


def contained(remedy: Remedy, adventure: Adventure, delay: int) -> bool:
    return remedy.power >= severity_of(adventure, delay)


def predict_woozy(world: World, adventure: Adventure) -> dict:
    sim = world.copy()
    cousin = sim.get("cousin")
    _do_adventure(sim, cousin, adventure, narrate=False)
    return {
        "wobble": cousin.meters["wobble"] >= THRESHOLD,
        "fatigue": cousin.meters["fatigue"],
        "heat": cousin.meters["heat"],
    }


def _do_adventure(world: World, cousin: Entity, adventure: Adventure, narrate: bool = True) -> None:
    cousin.meters["fatigue"] += float(adventure.strain)
    cousin.meters["heat"] += float(AUGUST_HEAT)
    cousin.meters["dust"] += float(adventure.dust)
    cousin.memes["desire"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, bold: Entity, cousin: Entity, guardian: Entity, place: Place) -> None:
    bold.memes["joy"] += 1
    cousin.memes["hope"] += 1
    cousin.meters["recovery"] += 1
    world.say(
        f"In August, when the sun looked as big as a brass drum and twice as loud, "
        f"{guardian.label_word} took {bold.id} and {cousin.id} to {place.label}. "
        f"{place.opening}"
    )
    world.say(
        f"{cousin.id} had only lately gotten over the measles, and the spots were gone, "
        f"but {cousin.pronoun('possessive')} strength was still tiptoeing back."
    )
    world.say(place.vista)


def wanting(world: World, bold: Entity, cousin: Entity, adventure: Adventure) -> None:
    bold.memes["boast"] += 1
    cousin.memes["hope"] += 1
    world.say(
        f'"Let\'s {adventure.verb}!" cried {bold.id}. "{adventure.boast}"'
    )
    world.say(
        f'{cousin.id} shaded {cousin.pronoun("possessive")} eyes and whispered, '
        f'"If I go slowly, I want to see {adventure.spectacle} too."'
    )


def warning(world: World, guardian: Entity, bold: Entity, cousin: Entity, adventure: Adventure) -> None:
    pred = predict_woozy(world, adventure)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_fatigue"] = pred["fatigue"]
    world.facts["predicted_heat"] = pred["heat"]
    world.say(
        f'{guardian.label_word.capitalize()} knelt in the dust. "{cousin.id} is feeling better, '
        f'but after measles and in this August heat, {adventure.path} can turn steady '
        f'legs wobbly. We need a slower, cooler way."'
    )
    if pred["wobble"]:
        world.say(
            f'"No mountain, hill, or kite is worth a spinning head," '
            f'{guardian.label_word} added.'
        )


def defy(world: World, bold: Entity, cousin: Entity, adventure: Adventure) -> None:
    world.say(
        f'"Just a little way," said {bold.id}. "I could pull a wagon uphill with one '
        f'eyebrow. {cousin.id} can surely manage {adventure.path}."'
    )
    world.say(
        f"So the two children started off, with the August light pouring over them like hot honey."
    )
    _do_adventure(world, cousin, adventure, narrate=True)


def alarm(world: World, guardian: Entity, cousin: Entity) -> None:
    if cousin.meters["wobble"] >= THRESHOLD:
        world.say(
            f'"Stop right there," called {guardian.label_word}. "{cousin.id}, sit before the '
            f'ground starts pretending it is a boat."'
        )


def rescue(world: World, guardian: Entity, bold: Entity, cousin: Entity, remedy: Remedy, place: Place) -> None:
    cousin.meters["heat"] = max(0.0, cousin.meters["heat"] - float(remedy.cool))
    cousin.meters["fatigue"] = max(0.0, cousin.meters["fatigue"] - float(remedy.rest + remedy.ride))
    cousin.meters["wobble"] = 0.0
    cousin.memes["fear"] = 0.0
    cousin.memes["relief"] += 1
    bold.memes["guilt"] += 1
    bold.memes["care"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} {remedy.text}."
    )
    world.say(
        f"Little by little, the bright glare stopped wobbling, and {cousin.id} could breathe "
        f"without hurrying."
    )
    world.say(
        f"Then came the twist: the dreadful golden giant on the far side of {place.label} "
        f"was no giant at all. {place.twist_true}"
    )


def lesson(world: World, guardian: Entity, bold: Entity, cousin: Entity) -> None:
    bold.memes["lesson"] += 1
    cousin.memes["lesson"] += 1
    world.say(
        f'"I was boasting bigger than a barn," {bold.id} admitted.'
    )
    world.say(
        f'{guardian.label_word.capitalize()} squeezed both their hands. "A brave day is not the day '
        f'you push too hard. A brave day is the day you notice when someone needs shade, rest, and time."'
    )
    world.say(
        f'"Next time," said {cousin.id}, smiling a little, "we go the slow way first."'
    )


def safe_ending(world: World, bold: Entity, cousin: Entity, adventure: Adventure) -> None:
    bold.memes["joy"] += 1
    cousin.memes["joy"] += 1
    world.say(
        f"From the cool place, they still got to see {adventure.spectacle}, and it was wonderful "
        f"without any racing at all."
    )
    world.say(
        f"After that, whenever August puffed itself up like a hot old king, {bold.id} remembered "
        f"that even tall-tale heroes must walk at the speed of the one who is healing."
    )


def rescue_fail(world: World, guardian: Entity, cousin: Entity, remedy: Remedy, place: Place) -> None:
    cousin.meters["heat"] += 1
    cousin.meters["fatigue"] += 1
    cousin.memes["fear"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} {remedy.fail}."
    )
    world.say(
        f"But the heat had already piled itself too high, and {cousin.id}'s eyes looked glassy with tiredness."
    )
    world.say(
        f"The twist came all the same: the fearsome shape beyond {place.label} was no monster. "
        f"{place.twist_true}"
    )


def weary_ending(world: World, guardian: Entity, bold: Entity, cousin: Entity) -> None:
    bold.memes["lesson"] += 1
    cousin.memes["lesson"] += 1
    world.say(
        f'{guardian.label_word.capitalize()} lifted {cousin.id} and carried {cousin.pronoun("object")} back to the wagon, '
        f'while {bold.id} walked quietly beside them.'
    )
    world.say(
        f'"I thought faster was finer," {bold.id} murmured.'
    )
    world.say(
        f'"Not after measles, and not in August heat," said {guardian.label_word}. '
        f'"Healing bodies need time more than daring."'
    )
    world.say(
        f"They went home before the grand fun began, and that early ride home was lesson enough for everybody."
    )


def tell(
    place: Place,
    adventure: Adventure,
    remedy: Remedy,
    *,
    bold_name: str = "Gus",
    bold_gender: str = "boy",
    cousin_name: str = "June",
    cousin_gender: str = "girl",
    guardian_type: str = "aunt",
    trait: str = "boastful",
    delay: int = 0,
) -> World:
    world = World(place)
    bold = world.add(Entity(
        id=bold_name,
        kind="character",
        type=bold_gender,
        role="bold",
        traits=[trait],
        label=bold_name,
    ))
    cousin = world.add(Entity(
        id=cousin_name,
        kind="character",
        type=cousin_gender,
        role="cousin",
        traits=["recovering", "hopeful"],
        label=cousin_name,
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_type,
        role="guardian",
        label="the grown-up",
    ))

    opening(world, bold, cousin, guardian, place)
    world.para()
    wanting(world, bold, cousin, adventure)
    warning(world, guardian, bold, cousin, adventure)

    if delay > 0:
        cousin.meters["fatigue"] += float(delay)

    world.para()
    defy(world, bold, cousin, adventure)
    alarm(world, guardian, cousin)

    okay = contained(remedy, adventure, delay)
    world.para()
    if okay:
        rescue(world, guardian, bold, cousin, remedy, place)
        lesson(world, guardian, bold, cousin)
        world.para()
        safe_ending(world, bold, cousin, adventure)
        outcome = "contained"
    else:
        rescue_fail(world, guardian, cousin, remedy, place)
        weary_ending(world, guardian, bold, cousin)
        outcome = "weary"

    world.facts.update(
        place=place,
        adventure=adventure,
        remedy=remedy,
        bold=bold,
        cousin=cousin,
        guardian=guardian,
        delay=delay,
        outcome=outcome,
        severity=severity_of(adventure, delay),
        wobble=cousin.meters["wobble"] < THRESHOLD if outcome == "contained" else True,
    )
    return world


PLACES = {
    "orchard": Place(
        id="orchard",
        label="the peach orchard fair",
        opening="The peaches hung so fat and golden that they seemed to tug the branches down by their own sleepy weight.",
        vista="At the edge of the lane stood a bell hill of hay bales and a ribbon kite line flickering above the trees.",
        affords={"bell_hill", "kite_chase"},
        twist_true="It was only the peach parade wagon, with a painted dragon snout and brass horns shining in the sun.",
        tags={"august", "fair"},
    ),
    "sunflower_field": Place(
        id="sunflower_field",
        label="the giant sunflower field",
        opening="The sunflowers were so tall they looked fit to whisper into the ears of clouds.",
        vista="Beyond the rows, a lookout ladder rose over the blooms and bright ribbons snapped on a windy pole.",
        affords={"ladder_climb", "kite_chase"},
        twist_true="It was a sunflower-threshing machine draped in yellow bunting, creaking along with three laughing farmers.",
        tags={"august", "field"},
    ),
    "fairground": Place(
        id="fairground",
        label="the county fairground",
        opening="The booths popped with red stripes and blue flags, and the whole place smelled of hay, lemons, and hot dust.",
        vista="There was a drum tower by the gate and a race lane curling past the pie tents.",
        affords={"drum_tower", "dust_race"},
        twist_true="It was only the county band wagon, with a lion painted on the side and tubas gleaming like suns.",
        tags={"august", "fair"},
    ),
}

ADVENTURES = {
    "bell_hill": Adventure(
        id="bell_hill",
        verb="climb Bell Hill and ring the fair bell",
        path="climbing Bell Hill",
        boast="I could ring that bell hard enough to wake pumpkins in November!",
        spectacle="the bell booming over the orchard",
        strain=2,
        dust=1,
        tags={"hill", "bell"},
    ),
    "kite_chase": Adventure(
        id="kite_chase",
        verb="race after the ribbon kite",
        path="racing under that ribbon kite",
        boast="I could catch that kite if it flew all the way to the moon!",
        spectacle="the ribbon kite dipping and dancing",
        strain=2,
        dust=1,
        tags={"kite", "race"},
    ),
    "ladder_climb": Adventure(
        id="ladder_climb",
        verb="climb the lookout ladder",
        path="climbing that long ladder",
        boast="I could hop up that ladder like a grasshopper wearing springs!",
        spectacle="the sunflower tops swaying like a yellow sea",
        strain=3,
        dust=0,
        tags={"ladder", "height"},
    ),
    "drum_tower": Adventure(
        id="drum_tower",
        verb="march up Drum Tower and beat the giant drum",
        path="marching up Drum Tower",
        boast="I could beat that drum so loud the crows would salute me!",
        spectacle="the giant drum shaking the bunting",
        strain=3,
        dust=1,
        tags={"drum", "tower"},
    ),
    "dust_race": Adventure(
        id="dust_race",
        verb="run the race lane to the pie tents",
        path="running that race lane",
        boast="I could outrun my own shadow before it blinked!",
        spectacle="the pie tents fluttering at the finish",
        strain=2,
        dust=2,
        tags={"race", "dust"},
    ),
}

REMEDIES = {
    "shade_wagon": Remedy(
        id="shade_wagon",
        sense=3,
        cool=1,
        rest=1,
        ride=2,
        label="shade wagon",
        phrase="a shady wagon with a cool jug tucked under the seat",
        text="pulled over the shade wagon, settled a damp cloth on the back of the child's neck, and let the horse do the hauling",
        fail="hurried over with the shade wagon, but there had already been too much hot walking before the child sat down",
        qa_text="used the shade wagon, a damp cloth, and a cool drink to let the child rest",
        tags={"shade", "wagon", "water"},
    ),
    "lemon_tent": Remedy(
        id="lemon_tent",
        sense=3,
        cool=2,
        rest=1,
        ride=0,
        label="lemonade tent",
        phrase="the lemon tent with striped canvas and cool cups",
        text="guided them into the lemon tent, set a cool cup in small hands, and made a shady seat out of folded blankets",
        fail="got the child into the lemon tent and offered a cool cup, but the walk there had already been too much",
        qa_text="brought the child into the lemon tent for shade, a cool drink, and rest",
        tags={"shade", "lemonade", "water"},
    ),
    "porch_hammock": Remedy(
        id="porch_hammock",
        sense=2,
        cool=1,
        rest=2,
        ride=1,
        label="porch hammock",
        phrase="the long porch hammock in the breezy shade",
        text="carried the child to the porch hammock, fanned the air once, and let the shade and the slow swinging do the rest",
        fail="reached the porch hammock at last, but the child had already gone past simple tiredness into real wooziness",
        qa_text="moved the child to the porch hammock to cool down and rest",
        tags={"shade", "rest"},
    ),
    "paper_fan": Remedy(
        id="paper_fan",
        sense=1,
        cool=1,
        rest=0,
        ride=0,
        label="paper fan",
        phrase="a flapping paper fan",
        text="waved a paper fan in a great hurry",
        fail="waved a paper fan in a great hurry, but that was not enough for heat and tired legs",
        qa_text="tried a paper fan",
        tags={"fan"},
    ),
}

GIRL_NAMES = ["June", "Mabel", "Tilly", "Nora", "Sadie", "Pearl", "Lula", "Ivy"]
BOY_NAMES = ["Gus", "Jeb", "Otis", "Beau", "Cal", "Ned", "Roy", "Finn"]
TRAITS = ["boastful", "eager", "lively", "reckless", "sparky"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for adv_id, adv in ADVENTURES.items():
            if not adventure_allowed(place, adv):
                continue
            for remedy_id, remedy in REMEDIES.items():
                if remedy.sense >= SENSE_MIN:
                    combos.append((place_id, adv_id, remedy_id))
    return combos


@dataclass
class StoryParams:
    place: str
    adventure: str
    remedy: str
    bold_name: str
    bold_gender: str
    cousin_name: str
    cousin_gender: str
    guardian: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "measles": [
        (
            "What is measles?",
            "Measles is an illness that can make someone feel very sick and tired and can cause a rash. When someone is getting better, they may still need rest and gentle care."
        )
    ],
    "august": [
        (
            "Why can August feel hard on your body?",
            "August can be very hot, and heat makes your body work harder. When it is hot, people need shade, drinks, and rest breaks."
        )
    ],
    "shade": [
        (
            "Why does shade help on a hot day?",
            "Shade keeps the sun from shining right on your body, so you do not heat up as quickly. It gives your body a chance to cool down."
        )
    ],
    "water": [
        (
            "Why do people drink water or cool drinks on hot days?",
            "Your body loses water when it gets hot and sweaty. Drinking helps you stay comfortable and keeps you from feeling weak or dizzy."
        )
    ],
    "rest": [
        (
            "Why is rest important after being sick?",
            "Rest gives your body time to keep healing. If you push too hard too soon, you can feel tired or woozy again."
        )
    ],
    "wagon": [
        (
            "Why can a wagon help someone who is tired?",
            "A wagon lets wheels do the hard work instead of tired legs. That means the person can still join the outing without using up all their strength."
        )
    ],
    "lemonade": [
        (
            "Why is a shady tent a good place to cool down?",
            "A shady tent gets you out of the sun and gives you a place to sit. Cooling down works better when you are both resting and out of the heat."
        )
    ],
}
KNOWLEDGE_ORDER = ["measles", "august", "shade", "water", "rest", "wagon", "lemonade"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bold = f["bold"]
    cousin = f["cousin"]
    guardian = f["guardian"]
    adventure = f["adventure"]
    place = f["place"]
    outcome = f["outcome"]
    base = (
        f'Write a tall-tale-style story for a 3-to-5-year-old that includes the words '
        f'"measles" and "August", uses dialogue, and has a cautionary twist.'
    )
    if outcome == "contained":
        return [
            base,
            f"Tell a child-friendly tall tale where {bold.id} wants to {adventure.verb} at {place.label}, "
            f"but {guardian.label_word} warns that {cousin.id} is still recovering from measles and needs a cooler, slower plan.",
            f"Write a story with boastful dialogue, a heat-and-rest lesson, and a twist where a supposed giant turns out to be something ordinary and funny."
        ]
    return [
        base,
        f"Tell a cautionary tall tale where {bold.id} pushes ahead too fast in August even though {cousin.id} is still weak after measles.",
        f"Write a story with lively dialogue and a twist reveal, but end by showing that brave people stop and go home when a healing body needs rest."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    bold = f["bold"]
    cousin = f["cousin"]
    guardian = f["guardian"]
    place = f["place"]
    adventure = f["adventure"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {bold.id}, {cousin.id}, and their {guardian.label_word} on a hot August outing. "
            f"The story matters because {cousin.id} is still getting strength back after measles."
        ),
        (
            f"What did {bold.id} want to do?",
            f"{bold.id} wanted to {adventure.verb}. {bold.pronoun('subject').capitalize()} talked in big tall-tale boasts because the adventure looked exciting."
        ),
        (
            f"Why did {guardian.label_word} warn them to slow down?",
            f"{guardian.label_word.capitalize()} knew that August heat and hard effort were a risky mix for someone still recovering from measles. "
            f"The warning came before the trouble because the grown-up could see that {adventure.path} might make {cousin.id} woozy."
        ),
    ]
    if outcome == "contained":
        qa.extend([
            (
                f"How did {guardian.label_word} help {cousin.id}?",
                f"{guardian.label_word.capitalize()} {remedy.qa_text}. That worked because the fix gave cooling, rest, and enough support to stop the wobbliness."
            ),
            (
                "What was the twist in the story?",
                f"The children thought a huge golden giant was coming across {place.label}, but it was really something ordinary. "
                f"{place.twist_true}"
            ),
            (
                "What did the children learn?",
                f"They learned that healing bodies should not be rushed, even in a grand adventure. "
                f"The safe ending proves they could still enjoy the day after choosing shade, rest, and time."
            ),
        ])
    else:
        qa.extend([
            (
                f"Did the first fix solve the problem?",
                f"No. {guardian.label_word.capitalize()} tried to help, but the day had already become too much for {cousin.id}. "
                f"That is why the outing ended early instead of turning back into fun."
            ),
            (
                "What was the twist in the story?",
                f"The scary shape everyone noticed was not a monster at all. {place.twist_true}"
            ),
            (
                "How did the story end?",
                f"It ended quietly, with the family going home early so {cousin.id} could rest. "
                f"The cautionary ending shows that after measles, pushing through August heat is not brave at all."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"measles", "august", "rest"}
    remedy = world.facts["remedy"]
    tags |= set(remedy.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="orchard",
        adventure="bell_hill",
        remedy="shade_wagon",
        bold_name="Gus",
        bold_gender="boy",
        cousin_name="June",
        cousin_gender="girl",
        guardian="aunt",
        trait="boastful",
        delay=0,
    ),
    StoryParams(
        place="sunflower_field",
        adventure="kite_chase",
        remedy="lemon_tent",
        bold_name="Mabel",
        bold_gender="girl",
        cousin_name="Otis",
        cousin_gender="boy",
        guardian="mother",
        trait="eager",
        delay=0,
    ),
    StoryParams(
        place="fairground",
        adventure="drum_tower",
        remedy="porch_hammock",
        bold_name="Jeb",
        bold_gender="boy",
        cousin_name="Pearl",
        cousin_gender="girl",
        guardian="father",
        trait="reckless",
        delay=1,
    ),
    StoryParams(
        place="fairground",
        adventure="dust_race",
        remedy="lemon_tent",
        bold_name="Ivy",
        bold_gender="girl",
        cousin_name="Roy",
        cousin_gender="boy",
        guardian="aunt",
        trait="lively",
        delay=1,
    ),
]


def explain_place(place: Place, adventure: Adventure) -> str:
    return (
        f"(No story: {place.label} does not support {adventure.verb}. "
        f"Pick a place where that adventure could really happen.)"
    )


def explain_remedy(remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    better = ", ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{remedy_id}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try a remedy that offers real shade, rest, or a ride, such as: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "contained" if contained(REMEDIES[params.remedy], ADVENTURES[params.adventure], params.delay) else "weary"


ASP_RULES = r"""
valid(P, A, R) :- place(P), adventure(A), remedy(R),
                  affords(P, A), sensible(R).

severity(S) :- chosen_adventure(A), strain(A, X), delay(D), august_heat(H), S = X + D + H.
contained :- chosen_remedy(R), power(R, P), severity(S), P >= S.
outcome(contained) :- contained.
outcome(weary) :- not contained.
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for adv_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, adv_id))
    for adv_id, adv in ADVENTURES.items():
        lines.append(asp.fact("adventure", adv_id))
        lines.append(asp.fact("strain", adv_id, adv.strain))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        lines.append(asp.fact("power", remedy_id, remedy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("august_heat", AUGUST_HEAT))
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
    extra = "\n".join([
        asp.fact("chosen_adventure", params.adventure),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_remedies()}
    if c_sens == p_sens:
        print(f"OK: sensible remedies match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale cautionary story world: August heat, measles recovery, and a sensible slower plan."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--guardian", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra effort before the grown-up fix reaches the child")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.adventure:
        if not adventure_allowed(PLACES[args.place], ADVENTURES[args.adventure]):
            raise StoryError(explain_place(PLACES[args.place], ADVENTURES[args.adventure]))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.adventure is None or combo[1] == args.adventure)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, adventure_id, remedy_id = rng.choice(sorted(combos))
    bold_gender = rng.choice(["girl", "boy"])
    cousin_gender = rng.choice(["girl", "boy"])
    bold_name = _pick_name(rng, bold_gender)
    cousin_name = _pick_name(rng, cousin_gender, avoid=bold_name)
    guardian = args.guardian or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 1, 2])
    return StoryParams(
        place=place_id,
        adventure=adventure_id,
        remedy=remedy_id,
        bold_name=bold_name,
        bold_gender=bold_gender,
        cousin_name=cousin_name,
        cousin_gender=cousin_gender,
        guardian=guardian,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        adventure = ADVENTURES[params.adventure]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Invalid params: unknown key {err.args[0]!r}.)") from err

    if not adventure_allowed(place, adventure):
        raise StoryError(explain_place(place, adventure))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_remedy(params.remedy))

    world = tell(
        place=place,
        adventure=adventure,
        remedy=remedy,
        bold_name=params.bold_name,
        bold_gender=params.bold_gender,
        cousin_name=params.cousin_name,
        cousin_gender=params.cousin_gender,
        guardian_type=params.guardian,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, adventure, remedy) combos:\n")
        for place_id, adventure_id, remedy_id in combos:
            print(f"  {place_id:16} {adventure_id:12} {remedy_id}")
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
            header = f"### {p.bold_name} & {p.cousin_name}: {p.adventure} at {p.place} ({p.remedy}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
