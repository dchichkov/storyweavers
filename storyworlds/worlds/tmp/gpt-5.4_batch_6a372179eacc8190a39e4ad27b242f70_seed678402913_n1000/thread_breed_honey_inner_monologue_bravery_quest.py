#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/thread_breed_honey_inner_monologue_bravery_quest.py
==============================================================================

A standalone storyworld for a small adventure tale about a child on a honey
quest. The child carries a jar of honey through a wild place, a satchel strap
snags and tears, and the child must decide -- in an inner monologue -- whether
to be brave. A spool of thread lets the child mend the strap, and a dog
companion of the right breed helps with the hardest part of the path.

Reasonableness constraints:
- the chosen thread must be strong enough to hold the chosen jar of honey
- the chosen dog breed must be suited to the chosen obstacle

The world model uses typed entities with physical meters and emotional memes.
State changes drive the turn: the satchel tears, fear rises, the child thinks,
mends, crosses, and delivers the honey.

Run it
------
python storyworlds/worlds/gpt-5.4/thread_breed_honey_inner_monologue_bravery_quest.py
python storyworlds/worlds/gpt-5.4/thread_breed_honey_inner_monologue_bravery_quest.py --all
python storyworlds/worlds/gpt-5.4/thread_breed_honey_inner_monologue_bravery_quest.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/thread_breed_honey_inner_monologue_bravery_quest.py --trace
python storyworlds/worlds/gpt-5.4/thread_breed_honey_inner_monologue_bravery_quest.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str = ""
    path_name: str = ""
    opening: str = ""
    destination: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str = ""
    label: str = ""
    need: str = ""
    scare: str = ""
    guide_text: str = ""
    crossing_text: str = ""
    snag_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Breed:
    id: str = ""
    label: str = ""
    phrase: str = ""
    skills: set[str] = field(default_factory=set)
    brave_style: str = ""
    help_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ThreadTool:
    id: str = ""
    label: str = ""
    phrase: str = ""
    strength: int = 1
    stitch_text: str = ""
    color: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HoneyJar:
    id: str = ""
    label: str = ""
    phrase: str = ""
    weight: int = 1
    scent: str = ""
    purpose: str = ""
    thanks: str = ""
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


def _r_tear_risk(world: World) -> list[str]:
    out: list[str] = []
    satchel = world.entities.get("satchel")
    honey = world.entities.get("honey")
    hero = world.entities.get("hero")
    if not satchel or not honey or not hero:
        return out
    if satchel.meters["torn"] < THRESHOLD or honey.meters["carried"] < THRESHOLD:
        return out
    sig = ("tear_risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    honey.meters["wobble"] += 1
    hero.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_stitched_secure(world: World) -> list[str]:
    out: list[str] = []
    satchel = world.entities.get("satchel")
    honey = world.entities.get("honey")
    if not satchel or not honey:
        return out
    if satchel.meters["stitched"] < THRESHOLD:
        return out
    sig = ("stitched_secure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    satchel.meters["secure"] += 1
    satchel.meters["torn"] = 0.0
    honey.meters["safe"] += 1
    honey.meters["wobble"] = 0.0
    out.append("__secure__")
    return out


def _r_crossed_courage(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    if not hero or not obstacle:
        return out
    if obstacle.meters["crossed"] < THRESHOLD:
        return out
    sig = ("crossed_courage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["bravery"] += 1
    out.append("__crossed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="tear_risk", tag="physical", apply=_r_tear_risk),
    Rule(name="stitched_secure", tag="physical", apply=_r_stitched_secure),
    Rule(name="crossed_courage", tag="emotional", apply=_r_crossed_courage),
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


PLACES = {
    "orchard": Place(
        id="orchard",
        path_name="the orchard path",
        opening="Past the last fence, the orchard path wound between apple trees and long grass.",
        destination="Grandma Wren's little orchard cottage",
        ending_image="The cottage windows shone gold, and bees drifted lazily over the late blossoms.",
        tags={"orchard"},
    ),
    "pinewoods": Place(
        id="pinewoods",
        path_name="the pinewood trail",
        opening="The pinewood trail ran under tall dark trees that whispered in the wind.",
        destination="Grandma Wren's warm cabin by the pines",
        ending_image="Smoke curled from the cabin chimney, and the pines no longer seemed so dark.",
        tags={"forest"},
    ),
    "meadow": Place(
        id="meadow",
        path_name="the meadow lane",
        opening="The meadow lane bent through clover and daisies bright enough to make the day feel wide.",
        destination="Grandma Wren's hill cottage above the flowers",
        ending_image="From the hill, the whole meadow looked soft and green under the evening sky.",
        tags={"meadow"},
    ),
}

OBSTACLES = {
    "log_tunnel": Obstacle(
        id="log_tunnel",
        label="the hollow log tunnel",
        need="small",
        scare="The tunnel looked dark and close, with roots hanging down like little claws.",
        guide_text="The dog slipped in first and found the clear middle where the ground stayed dry.",
        crossing_text="Soon hero and dog were crawling through the cool wooden tunnel, following the ribbon of light ahead.",
        snag_text="A splinter on the tunnel rim caught the satchel strap with a sharp little tug.",
        tags={"dark", "tunnel"},
    ),
    "mist_bridge": Obstacle(
        id="mist_bridge",
        label="the misty plank bridge",
        need="steady",
        scare="The bridge swayed above the stream, and the mist below made it look taller than it really was.",
        guide_text="The dog placed careful paws on the planks, showing exactly where the wood was safest.",
        crossing_text="Soon hero and dog were crossing one patient step at a time while the stream talked below them.",
        snag_text="A rough nail in the rail scraped the satchel strap as hero squeezed past.",
        tags={"bridge", "height"},
    ),
    "fern_maze": Obstacle(
        id="fern_maze",
        label="the fern maze",
        need="nose",
        scare="The ferns rose over hero's shoulders, and every green turn looked almost the same.",
        guide_text="The dog lifted its nose, caught the right scent, and picked the path that still smelled of sun-warmed clover.",
        crossing_text="Soon hero and dog were weaving between the ferns, trusting scent more than sight.",
        snag_text="A hooked stem tugged the satchel strap and pulled one seam half open.",
        tags={"maze", "lost"},
    ),
}

BREEDS = {
    "terrier": Breed(
        id="terrier",
        label="terrier",
        phrase="a little terrier breed with bright button eyes",
        skills={"small"},
        brave_style="small legs, quick heart",
        help_text="Terriers are a digging, darting breed, good at slipping into narrow places without fuss.",
        tags={"dog", "breed", "small"},
    ),
    "collie": Breed(
        id="collie",
        label="collie",
        phrase="a gentle collie breed with careful paws",
        skills={"steady"},
        brave_style="slow breath, careful feet",
        help_text="Collies are a watchful breed, good at choosing the safe step and keeping others calm.",
        tags={"dog", "breed", "steady"},
    ),
    "hound": Breed(
        id="hound",
        label="hound",
        phrase="a floppy-eared hound breed with a splendid nose",
        skills={"nose"},
        brave_style="nose high, tail sure",
        help_text="Hounds are a scent-finding breed, good at tracing the right way when the path looks confusing.",
        tags={"dog", "breed", "nose"},
    ),
}

THREADS = {
    "red_sewing": ThreadTool(
        id="red_sewing",
        label="red thread",
        phrase="a little spool of red thread",
        strength=1,
        stitch_text="looped the red thread through the torn strap in neat brave little stitches",
        color="red",
        tags={"thread", "sewing"},
    ),
    "blue_kite": ThreadTool(
        id="blue_kite",
        label="blue thread",
        phrase="a strong spool of blue kite thread",
        strength=2,
        stitch_text="pulled the blue thread tight and stitched the strap back into a firm blue line",
        color="blue",
        tags={"thread", "string"},
    ),
    "gold_waxed": ThreadTool(
        id="gold_waxed",
        label="gold thread",
        phrase="a waxed spool of gold thread",
        strength=3,
        stitch_text="worked the gold thread through the strap until the seam felt stout and smooth",
        color="gold",
        tags={"thread", "waxed"},
    ),
}

HONEYS = {
    "clover": HoneyJar(
        id="clover",
        label="clover honey",
        phrase="a small jar of clover honey",
        weight=1,
        scent="sweet like warm grass",
        purpose="for tea to soothe Grandma Wren's scratchy throat",
        thanks="Grandma Wren stirred the clover honey into her tea and smiled as if the whole room had sweetened.",
        tags={"honey", "tea"},
    ),
    "wildflower": HoneyJar(
        id="wildflower",
        label="wildflower honey",
        phrase="a round jar of wildflower honey",
        weight=2,
        scent="rich like summer flowers",
        purpose="for bread and tea after a long day of mending fences",
        thanks="Grandma Wren spread the wildflower honey on warm bread and said the brave trip had made it taste even better.",
        tags={"honey", "bread"},
    ),
    "heather": HoneyJar(
        id="heather",
        label="heather honey",
        phrase="a heavy jar of heather honey",
        weight=3,
        scent="dark and warm, almost like sunshine folded into syrup",
        purpose="for a special cough syrup she made each autumn",
        thanks="Grandma Wren held up the heather honey to the lamplight and said it was exactly what her autumn remedy needed.",
        tags={"honey", "medicine"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Poppy", "Ava", "Elsie", "June", "Tessa"]
BOY_NAMES = ["Rowan", "Finn", "Milo", "Theo", "Eli", "Sam", "Ben", "Leo"]
DOG_NAMES = ["Pip", "Moss", "Bracken", "Nell", "Tumble", "Skipper"]
TRAITS = ["curious", "gentle", "eager", "thoughtful", "lively", "careful"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    breed: str
    thread: str
    honey: str
    hero_name: str
    hero_gender: str
    dog_name: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


def obstacle_needs_breed(obstacle: Obstacle, breed: Breed) -> bool:
    return obstacle.need in breed.skills


def thread_holds_honey(thread: ThreadTool, honey: HoneyJar) -> bool:
    return thread.strength >= honey.weight


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for breed_id, breed in BREEDS.items():
                if not obstacle_needs_breed(obstacle, breed):
                    continue
                for thread_id, thread in THREADS.items():
                    for honey_id, honey in HONEYS.items():
                        if thread_holds_honey(thread, honey):
                            combos.append((place_id, obstacle_id, breed_id, thread_id, honey_id))
    return combos


def explain_rejection(obstacle: Obstacle, breed: Breed, thread: ThreadTool, honey: HoneyJar) -> str:
    if not obstacle_needs_breed(obstacle, breed):
        return (
            f"(No story: {breed.label} is the wrong breed for {obstacle.label}. "
            f"That obstacle needs help with {obstacle.need}, and this dog would not give honest help there.)"
        )
    if not thread_holds_honey(thread, honey):
        return (
            f"(No story: {thread.label} is too weak for {honey.label}. "
            f"If the strap tears, that thread would not hold the jar safely.)"
        )
    return "(No story: this combination is not reasonable.)"


@dataclass
class ThoughtBeat:
    first: str = ""
    second: str = ""


def predicted_trouble(obstacle: Obstacle, breed: Breed, thread: ThreadTool, honey: HoneyJar) -> ThoughtBeat:
    worry = ""
    answer = ""
    if not thread_holds_honey(thread, honey):
        worry = "If this thread snaps, the honey will spill before I even reach the far side."
        answer = "I need a stronger way to carry it."
    elif not obstacle_needs_breed(obstacle, breed):
        worry = "If we guess wrong here, we could be stuck in the middle."
        answer = "I need a helper who understands this kind of path."
    else:
        worry = f"This looks scary, but the jar can be mended and {breed.label} knows this sort of place."
        answer = "I do not have to be fearless; I only have to be careful and keep going."
    return ThoughtBeat(first=worry, second=answer)


def introduce(world: World, hero: Entity, parent: Entity, dog: Entity, place: Place, honey: HoneyJar, breed: Breed) -> None:
    world.say(
        f"{hero.id} was a little {hero.attrs.get('trait', hero.type)} {hero.type} who loved small adventures. "
        f"That morning, {parent.label_word} asked {hero.pronoun('object')} to carry {honey.phrase} to Grandma Wren."
    )
    world.say(
        f"{place.opening} At {hero.pronoun('possessive')} side trotted {dog.id}, {breed.phrase}."
    )
    world.say(
        f"The jar smelled {honey.scent}, and the errand felt like a true quest."
    )


def set_out(world: World, hero: Entity, dog: Entity, place: Place, obstacle: Obstacle, honey: HoneyJar) -> None:
    hero.memes["eagerness"] += 1
    world.say(
        f"{hero.id} tucked the honey into a little satchel and followed {place.path_name} toward {place.destination}."
    )
    world.say(
        f"Before long, they reached {obstacle.label}. {obstacle.scare}"
    )


def snag(world: World, hero: Entity, obstacle: Obstacle) -> None:
    satchel = world.get("satchel")
    honey = world.get("honey")
    satchel.meters["torn"] += 1
    honey.meters["carried"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{obstacle.snag_text} The satchel sagged, and the jar of honey gave one worried wobble."
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s stomach fluttered. If the strap broke all the way, the quest would end right there."
        )


def inner_monologue(world: World, hero: Entity, breed: Breed, thread: ThreadTool, obstacle: Obstacle, honey: HoneyJar) -> None:
    thought = predicted_trouble(obstacle, breed, thread, honey)
    hero.memes["fear"] += 1
    world.facts["thought"] = thought
    world.say(
        f'{hero.id} pressed one hand to the satchel and thought, '
        f'"{thought.first}"'
    )
    world.say(
        f'Then {hero.pronoun()} took a breath and told {hero.pronoun("object")}self, '
        f'"{thought.second}"'
    )


def mend(world: World, hero: Entity, thread: ThreadTool) -> None:
    satchel = world.get("satchel")
    satchel.meters["stitched"] += 1
    hero.memes["craft"] += 1
    propagate(world, narrate=False)
    world.say(
        f"From a pocket, {hero.id} pulled {thread.phrase} and {thread.stitch_text}."
    )
    world.say(
        f"When {hero.pronoun()} tugged the strap again, it held fast."
    )


def gain_bravery(world: World, hero: Entity, breed: Breed) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} looked at {world.get('dog').id}. {breed.help_text}"
    )
    world.say(
        f"Seeing that {breed.brave_style}, {hero.id} felt bravery gather instead of run away."
    )


def cross(world: World, hero: Entity, dog: Entity, obstacle: Obstacle, breed: Breed) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["crossed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{dog.id} went first. {obstacle.guide_text}"
    )
    world.say(obstacle.crossing_text.replace("hero", hero.id).replace("dog", dog.id))
    world.say(
        f"By the time they reached the far side, the scary place behind them seemed smaller than it had a moment before."
    )


def deliver(world: World, hero: Entity, place: Place, honey: HoneyJar) -> None:
    honey_ent = world.get("honey")
    honey_ent.meters["delivered"] += 1
    world.say(
        f"At last they came to {place.destination}. Grandma Wren opened the door before {hero.id} could knock."
    )
    world.say(
        f'{hero.id} lifted the satchel proudly. "I brought the {honey.label}," {hero.pronoun()} said.'
    )
    world.say(honey.thanks)
    world.say(
        f"{place.ending_image} {hero.id} had started the walk feeling small, but came home feeling like someone who could mend trouble and walk past it."
    )


def tell(
    place: Place,
    obstacle: Obstacle,
    breed: Breed,
    thread: ThreadTool,
    honey: HoneyJar,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    dog_name: str = "Pip",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            attrs={"trait": trait},
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    dog = world.add(
        Entity(
            id=dog_name,
            kind="character",
            type="dog",
            role="helper",
            label=breed.label,
            attrs={"breed": breed.id},
        )
    )
    satchel = world.add(
        Entity(
            id="satchel",
            type="satchel",
            label="satchel",
            phrase="a little satchel",
        )
    )
    honey_ent = world.add(
        Entity(
            id="honey",
            type="jar",
            label=honey.label,
            phrase=honey.phrase,
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle.label,
        )
    )

    introduce(world, hero, parent, dog, place, honey, breed)
    world.para()
    set_out(world, hero, dog, place, obstacle, honey)
    snag(world, hero, obstacle)
    inner_monologue(world, hero, breed, thread, obstacle, honey)
    mend(world, hero, thread)
    gain_bravery(world, hero, breed)
    world.para()
    cross(world, hero, dog, obstacle, breed)
    world.para()
    deliver(world, hero, place, honey)

    world.facts.update(
        hero=hero,
        parent=parent,
        dog=dog,
        satchel=satchel,
        honey_cfg=honey,
        honey=honey_ent,
        place=place,
        obstacle_cfg=obstacle,
        obstacle=obstacle_ent,
        breed=breed,
        thread=thread,
        delivered=honey_ent.meters["delivered"] >= THRESHOLD,
        repaired=satchel.meters["secure"] >= THRESHOLD,
        crossed=obstacle_ent.meters["crossed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "thread": [
        (
            "What is thread?",
            "Thread is a long, thin strand used for sewing things together. Strong thread can help mend a small tear."
        )
    ],
    "breed": [
        (
            "What does breed mean when we talk about a dog?",
            "A breed is a kind of dog with common traits, like size or a good nose. Different breeds are good at different jobs."
        )
    ],
    "honey": [
        (
            "Where does honey come from?",
            "Honey is made by bees from flower nectar. People often use it in food or warm drinks."
        )
    ],
    "bridge": [
        (
            "Why should you walk slowly on a bridge?",
            "Walking slowly helps you keep your balance and notice safe places to step. That is especially helpful if the bridge is narrow or shaky."
        )
    ],
    "maze": [
        (
            "How can a good nose help in a maze?",
            "A good nose can follow a smell when your eyes are not enough. That helps you choose the right path."
        )
    ],
    "tunnel": [
        (
            "Why can a tunnel feel scary?",
            "A tunnel can feel scary because it is dark and close, and you cannot always see what is ahead. Going carefully can make it safer."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel scared. It does not mean you never feel fear."
        )
    ],
    "mending": [
        (
            "What does it mean to mend something?",
            "To mend something is to fix it after it tears or breaks. Sewing with thread is one way to mend cloth."
        )
    ],
}
KNOWLEDGE_ORDER = ["thread", "breed", "honey", "tunnel", "bridge", "maze", "mending", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    dog = f["dog"]
    thread = f["thread"]
    honey = f["honey_cfg"]
    breed = f["breed"]
    obstacle = f["obstacle_cfg"]
    place = f["place"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "thread", "breed", and "honey".',
        f"Tell a quest story where {hero.id} carries {honey.phrase} along {place.path_name}, the satchel tears at {obstacle.label}, and {hero.pronoun()} uses inner monologue to find courage.",
        f"Write a gentle bravery story where a child and {dog.id}, a {breed.label} breed dog, mend a problem with {thread.label} and keep going.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    dog = f["dog"]
    thread = f["thread"]
    honey = f["honey_cfg"]
    obstacle = f["obstacle_cfg"]
    place = f["place"]
    thought = f.get("thought", ThoughtBeat())
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child on a quest, and {dog.id}, the dog helper. {hero.id}'s {parent.label_word} starts the errand by asking {hero.pronoun('object')} to carry honey to Grandma Wren."
        ),
        (
            f"What was {hero.id}'s quest?",
            f"{hero.id}'s quest was to carry {honey.phrase} to {place.destination}. The honey had a purpose, because it was {honey.purpose}."
        ),
        (
            f"What problem happened at {obstacle.label}?",
            f"The satchel strap snagged and tore there, so the honey jar wobbled and might have fallen. That made the middle of the journey feel suddenly risky."
        ),
        (
            f"What did {hero.id} think inside {hero.pronoun('possessive')} head?",
            f'{hero.id} had an inner monologue: "{thought.first}" Then {hero.pronoun()} answered that fear with, "{thought.second}"'
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} used {thread.phrase} to mend the torn strap. After that repair, the satchel held the honey safely again."
        ),
        (
            f"How did {dog.id} help?",
            f"{dog.id} helped because {dog.pronoun('subject')} was a {f['breed'].label} breed suited to that obstacle. The dog showed {hero.id} the safe way through, which turned fear into movement."
        ),
        (
            "How did the story end?",
            f"{hero.id} reached {place.destination} and delivered the honey. The ending image shows the quest is complete and proves that bravery grew after the hard part, not before it."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"thread", "breed", "honey", "mending", "bravery"}
    obstacle_id = f["obstacle_cfg"].id
    if obstacle_id == "log_tunnel":
        tags.add("tunnel")
    elif obstacle_id == "mist_bridge":
        tags.add("bridge")
    elif obstacle_id == "fern_maze":
        tags.add("maze")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="orchard",
        obstacle="log_tunnel",
        breed="terrier",
        thread="red_sewing",
        honey="clover",
        hero_name="Lina",
        hero_gender="girl",
        dog_name="Pip",
        parent_type="mother",
        trait="curious",
    ),
    StoryParams(
        place="pinewoods",
        obstacle="mist_bridge",
        breed="collie",
        thread="blue_kite",
        honey="wildflower",
        hero_name="Rowan",
        hero_gender="boy",
        dog_name="Nell",
        parent_type="father",
        trait="thoughtful",
    ),
    StoryParams(
        place="meadow",
        obstacle="fern_maze",
        breed="hound",
        thread="gold_waxed",
        honey="heather",
        hero_name="Mira",
        hero_gender="girl",
        dog_name="Bracken",
        parent_type="mother",
        trait="gentle",
    ),
    StoryParams(
        place="orchard",
        obstacle="mist_bridge",
        breed="collie",
        thread="gold_waxed",
        honey="heather",
        hero_name="Theo",
        hero_gender="boy",
        dog_name="Moss",
        parent_type="father",
        trait="eager",
    ),
]


ASP_RULES = r"""
% Reasonableness gate:
valid(P, O, B, T, H) :- place(P), obstacle(O), breed(B), thread(T), honey(H),
                        needs(O, N), skill(B, N),
                        strength(T, TS), weight(H, HW), TS >= HW.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for breed_id, breed in BREEDS.items():
        lines.append(asp.fact("breed", breed_id))
        for skill in sorted(breed.skills):
            lines.append(asp.fact("skill", breed_id, skill))
    for thread_id, thread in THREADS.items():
        lines.append(asp.fact("thread", thread_id))
        lines.append(asp.fact("strength", thread_id, thread.strength))
    for honey_id, honey in HONEYS.items():
        lines.append(asp.fact("honey", honey_id))
        lines.append(asp.fact("weight", honey_id, honey.weight))
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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty generated story")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests passed.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a honey quest, a torn satchel, thread, breed, and bravery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--breed", choices=BREEDS)
    ap.add_argument("--thread", choices=THREADS)
    ap.add_argument("--honey", choices=HONEYS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--dog-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.breed:
        obstacle = OBSTACLES[args.obstacle]
        breed = BREEDS[args.breed]
        thread = THREADS[args.thread] if args.thread else next(iter(THREADS.values()))
        honey = HONEYS[args.honey] if args.honey else next(iter(HONEYS.values()))
        if not obstacle_needs_breed(obstacle, breed):
            raise StoryError(explain_rejection(obstacle, breed, thread, honey))
    if args.thread and args.honey:
        obstacle = OBSTACLES[args.obstacle] if args.obstacle else next(iter(OBSTACLES.values()))
        breed = BREEDS[args.breed] if args.breed else next(iter(BREEDS.values()))
        thread = THREADS[args.thread]
        honey = HONEYS[args.honey]
        if not thread_holds_honey(thread, honey):
            raise StoryError(explain_rejection(obstacle, breed, thread, honey))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.breed is None or combo[2] == args.breed)
        and (args.thread is None or combo[3] == args.thread)
        and (args.honey is None or combo[4] == args.honey)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, breed_id, thread_id, honey_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    dog_name = args.dog_name or rng.choice(DOG_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        breed=breed_id,
        thread=thread_id,
        honey=honey_id,
        hero_name=hero_name,
        hero_gender=gender,
        dog_name=dog_name,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.breed not in BREEDS:
        raise StoryError(f"(Unknown breed: {params.breed})")
    if params.thread not in THREADS:
        raise StoryError(f"(Unknown thread: {params.thread})")
    if params.honey not in HONEYS:
        raise StoryError(f"(Unknown honey: {params.honey})")

    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    breed = BREEDS[params.breed]
    thread = THREADS[params.thread]
    honey = HONEYS[params.honey]

    if not obstacle_needs_breed(obstacle, breed) or not thread_holds_honey(thread, honey):
        raise StoryError(explain_rejection(obstacle, breed, thread, honey))

    world = tell(
        place=place,
        obstacle=obstacle,
        breed=breed,
        thread=thread,
        honey=honey,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        dog_name=params.dog_name,
        parent_type=params.parent_type,
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
        print(f"{len(combos)} compatible (place, obstacle, breed, thread, honey) combos:\n")
        for place, obstacle, breed, thread, honey in combos:
            print(f"  {place:10} {obstacle:12} {breed:8} {thread:11} {honey}")
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
                f"### {p.hero_name} and {p.dog_name}: {p.honey} by {p.obstacle} "
                f"({p.place}, {p.breed}, {p.thread})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
