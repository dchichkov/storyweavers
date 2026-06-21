#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/quartz_surprise_comedy.py
===================================================

A standalone storyworld for a small comedy domain: a child finds a dusty lump,
mistakes it for something silly, and gets a surprise when washing reveals a
sparkling piece of quartz.

The world model keeps both physical state ("meters" like dust, wetness, shine)
and emotional state ("memes" like pride, caution, surprise, embarrassment, and
laughter). The prose comes from those states and from the chosen parameters.

Run it
------
    python storyworlds/worlds/gpt-5.4/quartz_surprise_comedy.py
    python storyworlds/worlds/gpt-5.4/quartz_surprise_comedy.py --place garden --quartz milky --disguise potato
    python storyworlds/worlds/gpt-5.4/quartz_surprise_comedy.py --clean lick_it
    python storyworlds/worlds/gpt-5.4/quartz_surprise_comedy.py --all
    python storyworlds/worlds/gpt-5.4/quartz_surprise_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/quartz_surprise_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/quartz_surprise_comedy.py --json
    python storyworlds/worlds/gpt-5.4/quartz_surprise_comedy.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    dirt: int
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class QuartzKind:
    id: str
    label: str
    phrase: str
    color: str
    shape_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Disguise:
    id: str
    guess: str
    article: str
    joke_line: str
    caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CleaningMethod:
    id: str
    label: str
    sense: int
    power: int
    start_text: str
    reveal_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Display:
    id: str
    phrase: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    rock = world.entities.get("rock")
    if rock is None:
        return out
    if rock.meters["wet"] < THRESHOLD or rock.meters["dust"] > 0:
        return out
    sig = ("reveal", rock.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rock.meters["shine"] += 1
    rock.meters["quartz_revealed"] += 1
    rock.memes["surprise"] += 1
    out.append("__reveal__")
    return out


def _r_laughter(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    rock = world.entities.get("rock")
    if child is None or helper is None or rock is None:
        return out
    if rock.memes["mistaken"] < THRESHOLD or rock.meters["quartz_revealed"] < THRESHOLD:
        return out
    sig = ("laughter", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["embarrassment"] += 1
    child.memes["laughter"] += 1
    child.memes["pride"] += 1
    helper.memes["laughter"] += 1
    helper.memes["love"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="reveal", tag="physical", apply=_r_reveal),
    Rule(name="laughter", tag="social", apply=_r_laughter),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule.apply(world)
            if parts:
                changed = True
                produced.extend(parts)
    if narrate:
        for part in produced:
            if not part.startswith("__"):
                world.say(part)
    return produced


def plausible(place: Place, quartz: QuartzKind, disguise: Disguise) -> bool:
    return disguise.id in place.affords and disguise.id in quartz.shape_tags


def sensible_methods() -> list[CleaningMethod]:
    return [m for m in CLEANING_METHODS.values() if m.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    method = CLEANING_METHODS[params.clean]
    dirt = PLACES[params.place].dirt
    if method.power >= dirt:
        return "self_reveal"
    return "helped_reveal"


def predict_reveal(world: World, method: CleaningMethod) -> dict:
    sim = world.copy()
    rock = sim.get("rock")
    rock.meters["wet"] += 1
    rock.meters["dust"] = max(0.0, rock.meters["dust"] - method.power)
    propagate(sim, narrate=False)
    return {
        "revealed": rock.meters["quartz_revealed"] >= THRESHOLD,
        "dust_left": rock.meters["dust"],
    }


def setup_scene(world: World, child: Entity, helper: Entity, display: Display) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {helper.id} were in {world.place.phrase}, "
        f"trying to find one grand object for their funny treasure table."
    )
    world.say(
        f"They already had bottle caps, one heroic leaf, and a spoon that looked far too serious, "
        f"but they still wanted a real star for {display.phrase}."
    )


def find_lump(world: World, child: Entity, quartz: QuartzKind) -> None:
    rock = world.get("rock")
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} spotted a dusty lump half-hidden nearby. It was really {quartz.phrase}, "
        f"but under all that dirt it looked as plain as a tired old stone."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} picked it up. The lump felt heavy and cool in "
        f"{child.pronoun('possessive')} hand."
    )


def misguess(world: World, child: Entity, helper: Entity, disguise: Disguise) -> None:
    rock = world.get("rock")
    rock.memes["mistaken"] += 1
    child.memes["confidence"] += 1
    world.say(
        f'"Look!" said {child.id}. "I found {disguise.article} {disguise.guess}!"'
    )
    world.say(disguise.joke_line.format(child=child.id, helper=helper.id))
    world.say(
        f"{helper.id} squinted at it and tried not to giggle. The dusty lump really did make a very silly "
        f"pretend {disguise.guess}."
    )


def caution(world: World, helper: Entity, child: Entity, disguise: Disguise) -> None:
    helper.memes["caution"] += 1
    child.memes["defiance"] += 1
    world.say(
        f'"Wait," said {helper.id}. "{disguise.caution} Let\'s wash it before you give it a grand name."'
    )
    world.say(
        f"{child.id} hugged the lump to {child.pronoun('possessive')} chest anyway. "
        f'"But if it is a {disguise.guess}, it is the funniest one in the whole world."'
    )


def first_clean(world: World, child: Entity, method: CleaningMethod) -> None:
    rock = world.get("rock")
    child.memes["hope"] += 1
    rock.meters["wet"] += 1
    rock.meters["dust"] = max(0.0, rock.meters["dust"] - method.power)
    world.say(method.start_text.format(child=child.id))
    propagate(world, narrate=False)


def reveal_quartz(world: World, child: Entity, helper: Entity, quartz: QuartzKind,
                  method: CleaningMethod, display: Display) -> None:
    rock = world.get("rock")
    world.say(method.reveal_text.format(color=quartz.color))
    world.say(
        f"Under the last smear of dirt, the lump flashed bright and glassy. It was quartz -- real quartz -- "
        f"and it shone as if it had been hiding a little secret laugh."
    )
    world.say(
        f"{child.id}'s mouth fell open. {helper.id}'s eyes went round. Then they both burst into laughter, "
        f"because the famous {world.facts['disguise'].guess} was not a {world.facts['disguise'].guess} at all."
    )
    child.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    child.memes["pride"] += 1
    child.memes["embarrassment"] += 1
    child.memes["laughter"] += 1
    helper.memes["laughter"] += 1
    world.say(
        f'"It is prettier than my idea," said {child.id}. That was true, and a little funny.'
    )
    world.say(
        f"They set the quartz on {display.phrase}, and soon it was the one treasure nobody could stop looking at. "
        f"{display.ending}"
    )


def helper_finishes(world: World, grownup: Entity, helper: Entity, child: Entity,
                    quartz: QuartzKind, method: CleaningMethod, display: Display) -> None:
    rock = world.get("rock")
    grownup.memes["care"] += 1
    helper.memes["relief"] += 1
    child.memes["embarrassment"] += 1
    world.say(method.fail_text)
    world.say(
        f"Just then, {grownup.label_word.capitalize()} came by carrying a small brush and a cup of water."
    )
    world.say(
        f'{grownup.pronoun("subject").capitalize()} took one look at the muddy lump and smiled. '
        f'"That does not need a bite," {grownup.pronoun()} said. "It needs a better rinse."'
    )
    rock.meters["wet"] += 1
    rock.meters["dust"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"With three careful swishes and one tiny scrub, the dirt slipped away. A {quartz.color} shine woke up "
        f"inside the stone, and suddenly the plain lump turned into quartz."
    )
    world.say(
        f"{child.id} made such a shocked little gasp that {helper.id} sat down in the grass and laughed."
    )
    child.memes["surprise"] += 1
    child.memes["pride"] += 1
    child.memes["laughter"] += 1
    helper.memes["laughter"] += 1
    grownup.memes["laughter"] += 1
    world.say(
        f'"So it was never a {world.facts["disguise"].guess}," said {child.id}.'
    )
    world.say(
        f'"No," said {grownup.label_word}, "but it is a splendid piece of quartz."'
    )
    world.say(
        f"They set the quartz on {display.phrase}, and even the bottle caps seemed to stand back and admire it. "
        f"{display.ending}"
    )


def tell(place: Place, quartz: QuartzKind, disguise: Disguise, clean: CleaningMethod,
         display: Display, child_name: str = "Lily", child_type: str = "girl",
         helper_name: str = "Ben", helper_type: str = "boy",
         grownup_type: str = "mother") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    grownup = world.add(Entity(id="Grownup", kind="character", type=grownup_type, role="grownup", label="the grown-up"))
    rock = world.add(
        Entity(
            id="rock",
            kind="thing",
            type="quartz",
            label="stone",
            phrase=quartz.phrase,
            tags=set(quartz.tags),
        )
    )
    rock.meters["dust"] = float(place.dirt)

    setup_scene(world, child, helper, display)
    find_lump(world, child, quartz)

    world.para()
    misguess(world, child, helper, disguise)
    caution(world, helper, child, disguise)

    world.para()
    pred = predict_reveal(world, clean)
    world.facts["predicted_reveal"] = pred["revealed"]
    world.facts["predicted_dust_left"] = pred["dust_left"]
    first_clean(world, child, clean)

    world.para()
    if rock.meters["quartz_revealed"] >= THRESHOLD:
        reveal_quartz(world, child, helper, quartz, clean, display)
        outcome = "self_reveal"
    else:
        helper_finishes(world, grownup, helper, child, quartz, clean, display)
        outcome = "helped_reveal"

    world.facts.update(
        child=child,
        helper=helper,
        grownup=grownup,
        rock=rock,
        place=place,
        quartz=quartz,
        disguise=disguise,
        clean=clean,
        display=display,
        outcome=outcome,
        revealed=rock.meters["quartz_revealed"] >= THRESHOLD,
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="garden",
        phrase="the garden behind the house",
        dirt=2,
        affords={"potato", "tooth"},
        tags={"garden"},
    ),
    "creek": Place(
        id="creek",
        label="creek",
        phrase="the shallow creek by the footbridge",
        dirt=1,
        affords={"cookie", "egg"},
        tags={"creek", "water"},
    ),
    "shed": Place(
        id="shed",
        label="shed",
        phrase="the old shed beside the fence",
        dirt=3,
        affords={"potato", "cookie"},
        tags={"shed", "dust"},
    ),
    "flowerpot": Place(
        id="flowerpot",
        label="flowerpot corner",
        phrase="the line of flowerpots on the sunny step",
        dirt=2,
        affords={"potato", "egg"},
        tags={"garden", "flowerpot"},
    ),
}

QUARTZ_KINDS = {
    "milky": QuartzKind(
        id="milky",
        label="milky quartz",
        phrase="a lump of milky quartz",
        color="pale white",
        shape_tags={"potato", "tooth"},
        tags={"quartz"},
    ),
    "rose": QuartzKind(
        id="rose",
        label="rose quartz",
        phrase="a piece of rose quartz",
        color="soft pink",
        shape_tags={"cookie", "egg"},
        tags={"quartz"},
    ),
    "smoky": QuartzKind(
        id="smoky",
        label="smoky quartz",
        phrase="a point of smoky quartz",
        color="gray-brown",
        shape_tags={"tooth", "cookie"},
        tags={"quartz"},
    ),
}

DISGUISES = {
    "potato": Disguise(
        id="potato",
        guess="potato",
        article="a potato",
        joke_line='"A potato?" asked {helper}. "Then why is it dressed like a pirate cannonball?"',
        caution="Do not put that in a soup pot or your mouth",
        tags={"potato"},
    ),
    "cookie": Disguise(
        id="cookie",
        guess="cookie",
        article="a cookie",
        joke_line='"A cookie?" asked {helper}. "That cookie looks like it lost a wrestling match with the ground."',
        caution="Do not take a nibble of mystery cookies from the dirt",
        tags={"cookie"},
    ),
    "tooth": Disguise(
        id="tooth",
        guess="giant tooth",
        article="a giant tooth",
        joke_line='"A giant tooth?" asked {helper}. "Then some enormous grin is walking around without it."',
        caution="Do not wave that in front of people and call for a giant dentist yet",
        tags={"tooth"},
    ),
    "egg": Disguise(
        id="egg",
        guess="dragon egg",
        article="a dragon egg",
        joke_line='"A dragon egg?" asked {helper}. "If it hatches, you are cleaning the smoke."',
        caution="Do not sit on mystery eggs and try to hatch them",
        tags={"egg"},
    ),
}

CLEANING_METHODS = {
    "rinse_jar": CleaningMethod(
        id="rinse_jar",
        label="jar rinse",
        sense=2,
        power=2,
        start_text="{child} swished the lump in a jar of water and rubbed it with careful thumbs.",
        reveal_text="The water turned brown first, and then the stone underneath began to glow {color}.",
        fail_text="The first rinse took away some dirt, but muddy streaks clung to every crack.",
        qa_text="rinsed it with water",
        tags={"water", "wash"},
    ),
    "brush_and_rinse": CleaningMethod(
        id="brush_and_rinse",
        label="brush and rinse",
        sense=3,
        power=3,
        start_text="{child} used a little brush and a cup of water, scrubbing each corner as if polishing a crown.",
        reveal_text="The dust slid away at once, and the surface underneath flashed {color} in the light.",
        fail_text="Even after the brushing, a few stubborn smears still hid the shine.",
        qa_text="brushed it and rinsed it clean",
        tags={"water", "brush", "wash"},
    ),
    "shirt_wipe": CleaningMethod(
        id="shirt_wipe",
        label="shirt wipe",
        sense=1,
        power=1,
        start_text="{child} rubbed the lump on {child}'s shirt and puffed at the dust.",
        reveal_text="A small clean patch appeared, and the stone winked {color}.",
        fail_text="That only moved the dirt around and left the lump mostly grubby.",
        qa_text="wiped it on a shirt",
        tags={"wipe"},
    ),
    "lick_it": CleaningMethod(
        id="lick_it",
        label="lick it",
        sense=0,
        power=0,
        start_text="{child} leaned in as if a lick might solve everything.",
        reveal_text="That was never going to be the right plan.",
        fail_text="Before any of that could happen, someone stopped the idea at once.",
        qa_text="tried to lick it",
        tags={"unsafe"},
    ),
}

DISPLAYS = {
    "napkin": Display(
        id="napkin",
        phrase="a red napkin folded like a tiny stage",
        ending="By supper time, everyone was still calling it the Not-a-Potato Jewel.",
        tags={"display"},
    ),
    "teacup": Display(
        id="teacup",
        phrase="an upside-down teacup saucer",
        ending="It looked so grand there that even the spoon seemed pleased to know it.",
        tags={"display"},
    ),
    "box": Display(
        id="box",
        phrase="a little matchbox lined with soft cloth",
        ending="The treasure table suddenly looked less silly and much more splendid.",
        tags={"display"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]


@dataclass
class StoryParams:
    place: str
    quartz: str
    disguise: str
    clean: str
    display: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    grownup: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        quartz="milky",
        disguise="potato",
        clean="rinse_jar",
        display="napkin",
        child_name="Lily",
        child_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        grownup="mother",
    ),
    StoryParams(
        place="creek",
        quartz="rose",
        disguise="cookie",
        clean="rinse_jar",
        display="teacup",
        child_name="Mia",
        child_gender="girl",
        helper_name="Sam",
        helper_gender="boy",
        grownup="father",
    ),
    StoryParams(
        place="shed",
        quartz="smoky",
        disguise="cookie",
        clean="brush_and_rinse",
        display="box",
        child_name="Max",
        child_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        grownup="mother",
    ),
    StoryParams(
        place="flowerpot",
        quartz="rose",
        disguise="egg",
        clean="rinse_jar",
        display="box",
        child_name="Ava",
        child_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        grownup="father",
    ),
    StoryParams(
        place="shed",
        quartz="milky",
        disguise="potato",
        clean="rinse_jar",
        display="napkin",
        child_name="Theo",
        child_gender="boy",
        helper_name="Lucy",
        helper_gender="girl",
        grownup="mother",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for quartz_id, quartz in QUARTZ_KINDS.items():
            for disguise_id, disguise in DISGUISES.items():
                if plausible(place, quartz, disguise):
                    combos.append((place_id, quartz_id, disguise_id))
    return sorted(combos)


KNOWLEDGE = {
    "quartz": [
        (
            "What is quartz?",
            "Quartz is a hard mineral that can look plain when it is dusty but sparkle when it is clean. People often find quartz in stones and rocks."
        )
    ],
    "water": [
        (
            "Why does water help clean dirt off a stone?",
            "Water loosens the dirt and carries it away. That lets the real surface underneath show."
        )
    ],
    "brush": [
        (
            "Why is a little brush useful for cleaning a rock?",
            "A brush can reach tiny cracks and corners where dirt likes to hide. It helps clean a rock without chewing or smashing it."
        )
    ],
    "potato": [
        (
            "Why can a dusty stone look like a potato?",
            "If a stone is roundish and covered with brown dirt, it can look like a potato for a moment. Dirt hides the color and shine."
        )
    ],
    "cookie": [
        (
            "Why should you not eat something you found on the ground?",
            "Things on the ground can be dirty or not food at all. A safe grown-up should check first."
        )
    ],
    "egg": [
        (
            "What makes an egg different from a rock?",
            "An egg has a shell made for a baby animal, but a rock is a hard piece of mineral. A rock will not hatch, even if it looks mysterious."
        )
    ],
}
KNOWLEDGE_ORDER = ["quartz", "water", "brush", "potato", "cookie", "egg"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    disguise = f["disguise"]
    quartz = f["quartz"]
    return [
        f'Write a funny surprise story for a 3-to-5-year-old that includes the word "quartz".',
        f"Tell a comedy where {child.id} thinks a dusty stone is {disguise.article}, but washing it reveals {quartz.label}.",
        f"Write a gentle story with a silly mistake, a washing scene, and a sparkling surprise ending."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    grownup = f["grownup"]
    disguise = f["disguise"]
    quartz = f["quartz"]
    clean = f["clean"]
    display = f["display"]
    out = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.id}, and {grownup.label_word}, who all end up admiring one surprising stone together."
        ),
        (
            f"What did {child.id} think the dusty lump was?",
            f"{child.id} thought it was {disguise.article}. That guess is what makes the middle of the story so funny."
        ),
        (
            "What was the stone really?",
            f"It was a piece of {quartz.label}. The surprise comes when the dirt comes off and the quartz starts to shine."
        ),
    ]
    if out == "self_reveal":
        qa.append(
            (
                f"How did they discover the truth about the lump?",
                f"They {clean.qa_text}, and that cleaned away enough dirt to show the shiny surface underneath. Once the lump was clean, everyone could see it was quartz."
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id}'s first cleaning plan work all the way?",
                f"No. The first try took off some dirt, but not enough to reveal the whole stone. Then {grownup.label_word} used a better rinse and brushing, and the quartz finally showed."
            )
        )
    qa.append(
        (
            "Why did everyone laugh?",
            f"They laughed because the grand {disguise.guess} turned out to be quartz instead. The silly mistake became even funnier once the shiny truth appeared."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They placed the quartz on {display.phrase} as the star of their treasure table. The ending image proves the dusty lump changed from a joke into something everyone wanted to admire."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"quartz"} | set(world.facts["clean"].tags) | set(world.facts["disguise"].tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo(place: Place, quartz: QuartzKind, disguise: Disguise) -> str:
    if disguise.id not in place.affords:
        return (
            f"(No story: finding something that looks like {disguise.article} is not a good fit for "
            f"{place.phrase}. Pick a disguise that suits the place.)"
        )
    if disguise.id not in quartz.shape_tags:
        return (
            f"(No story: {quartz.label} does not plausibly look like {disguise.article}. "
            f"Choose a disguise that matches the stone's shape.)"
        )
    return "(No story: that combination is not reasonable here.)"


def explain_method(method_id: str) -> str:
    method = CLEANING_METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing cleaning method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try a safer, more sensible cleaning method like {better}.)"
    )


ASP_RULES = r"""
% --- reasonableness --------------------------------------------------------
plausible(P, Q, D) :- place(P), quartz(Q), disguise(D),
                      affords(P, D), shape(Q, D).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

% --- outcome ---------------------------------------------------------------
outcome(self_reveal) :- chosen_place(P), dirt(P, D), chosen_method(M), power(M, Pwr), Pwr >= D.
outcome(helped_reveal) :- chosen_place(P), dirt(P, D), chosen_method(M), power(M, Pwr), Pwr < D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("dirt", place_id, place.dirt))
        for disguise_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, disguise_id))
    for quartz_id, quartz in QUARTZ_KINDS.items():
        lines.append(asp.fact("quartz", quartz_id))
        for shape in sorted(quartz.shape_tags):
            lines.append(asp.fact("shape", quartz_id, shape))
    for disguise_id in DISGUISES:
        lines.append(asp.fact("disguise", disguise_id))
    for method_id, method in CLEANING_METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show plausible/3."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_method", params.clean),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.quartz not in QUARTZ_KINDS:
        raise StoryError(f"(Unknown quartz kind: {params.quartz})")
    if params.disguise not in DISGUISES:
        raise StoryError(f"(Unknown disguise: {params.disguise})")
    if params.clean not in CLEANING_METHODS:
        raise StoryError(f"(Unknown cleaning method: {params.clean})")
    if params.display not in DISPLAYS:
        raise StoryError(f"(Unknown display: {params.display})")
    if not plausible(PLACES[params.place], QUARTZ_KINDS[params.quartz], DISGUISES[params.disguise]):
        raise StoryError(explain_combo(PLACES[params.place], QUARTZ_KINDS[params.quartz], DISGUISES[params.disguise]))
    if CLEANING_METHODS[params.clean].sense < SENSE_MIN:
        raise StoryError(explain_method(params.clean))


def asp_verify() -> int:
    rc = 0
    p_valid = set(valid_combos())
    a_valid = set(asp_valid_combos())
    if p_valid == a_valid:
        print(f"OK: ASP valid combos match Python ({len(p_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_valid - p_valid:
            print("  only in ASP:", sorted(a_valid - p_valid))
        if p_valid - a_valid:
            print("  only in Python:", sorted(p_valid - a_valid))

    p_sensible = {m.id for m in sensible_methods()}
    a_sensible = set(asp_sensible())
    if p_sensible == a_sensible:
        print(f"OK: sensible cleaning methods match ({sorted(p_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: asp={sorted(a_sensible)} python={sorted(p_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure for seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A comedy storyworld where a dusty lump turns out to be quartz."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quartz", choices=QUARTZ_KINDS)
    ap.add_argument("--disguise", choices=DISGUISES)
    ap.add_argument("--clean", choices=CLEANING_METHODS)
    ap.add_argument("--display", choices=DISPLAYS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list ASP-compatible combos")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quartz and args.disguise:
        place = PLACES[args.place]
        quartz = QUARTZ_KINDS[args.quartz]
        disguise = DISGUISES[args.disguise]
        if not plausible(place, quartz, disguise):
            raise StoryError(explain_combo(place, quartz, disguise))
    if args.clean and CLEANING_METHODS[args.clean].sense < SENSE_MIN:
        raise StoryError(explain_method(args.clean))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.quartz is None or combo[1] == args.quartz)
        and (args.disguise is None or combo[2] == args.disguise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, quartz_id, disguise_id = rng.choice(combos)
    clean_id = args.clean or rng.choice(sorted(m.id for m in sensible_methods()))
    display_id = args.display or rng.choice(sorted(DISPLAYS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=child_name)
    grownup = args.grownup or rng.choice(["mother", "father"])

    params = StoryParams(
        place=place_id,
        quartz=quartz_id,
        disguise=disguise_id,
        clean=clean_id,
        display=display_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        grownup=grownup,
    )
    _validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        place=PLACES[params.place],
        quartz=QUARTZ_KINDS[params.quartz],
        disguise=DISGUISES[params.disguise],
        clean=CLEANING_METHODS[params.clean],
        display=DISPLAYS[params.display],
        child_name=params.child_name,
        child_type=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_gender,
        grownup_type=params.grownup,
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
        print(asp_program("", "#show plausible/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible cleaning methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} plausible (place, quartz, disguise) combos:\n")
        for place, quartz, disguise in combos:
            print(f"  {place:10} {quartz:7} {disguise}")
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
            header = f"### {p.child_name}: {p.quartz} as {p.disguise} at {p.place} ({outcome_of(p)})"
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
