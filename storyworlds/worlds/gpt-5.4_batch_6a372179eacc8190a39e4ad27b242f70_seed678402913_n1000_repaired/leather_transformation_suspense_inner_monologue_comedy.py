#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/leather_transformation_suspense_inner_monologue_comedy.py
====================================================================================

A standalone storyworld for a child-facing comedy with a leather object, a tense
little mystery, inner monologue, and a transformation. A child discovers a
mysterious wobbling leather thing, worries it might be alive, then learns the
ordinary cause and turns the object into a silly puppet.

The world model prefers only combinations where:
- the chosen cause can plausibly make the chosen leather item move or sound, and
- the chosen craft project fits the shape of that item.

The prose is state-driven: fear, curiosity, relief, and joy accumulate on the
characters, and the object changes from "mysterious old leather thing" into a
finished puppet used in a comic ending.

Run it
------
python storyworlds/worlds/gpt-5.4/leather_transformation_suspense_inner_monologue_comedy.py
python storyworlds/worlds/gpt-5.4/leather_transformation_suspense_inner_monologue_comedy.py --item glove --cause marble --project dragon
python storyworlds/worlds/gpt-5.4/leather_transformation_suspense_inner_monologue_comedy.py --item satchel --cause mouse
python storyworlds/worlds/gpt-5.4/leather_transformation_suspense_inner_monologue_comedy.py --all
python storyworlds/worlds/gpt-5.4/leather_transformation_suspense_inner_monologue_comedy.py --qa --json
python storyworlds/worlds/gpt-5.4/leather_transformation_suspense_inner_monologue_comedy.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }
        return mapping.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    hiding_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LeatherItem:
    id: str
    label: str
    phrase: str
    one: str
    texture: str
    found_in: str
    sound_line: str
    supports: set[str] = field(default_factory=set)
    causes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    phrase: str
    motion: str
    reveal: str
    harmless: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    face: str
    voice: str
    finish: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mystery(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("item")
    if item.meters["moved"] < THRESHOLD:
        return []
    sig = ("mystery", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    return []


def _r_reveal_relief(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["truth"] < THRESHOLD:
        return []
    sig = ("relief", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    return []


def _r_transform_joy(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("item")
    if item.meters["decorated"] < THRESHOLD:
        return []
    sig = ("joy", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mystery", tag="meme", apply=_r_mystery),
    Rule(name="relief", tag="meme", apply=_r_reveal_relief),
    Rule(name="transform_joy", tag="meme", apply=_r_transform_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        current_size = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        changed = changed or len(world.fired) > current_size
    if narrate:
        for line in produced:
            world.say(line)
    return produced


THEMES_OF_THOUGHT = {
    "brave": "Maybe it is only a silly little secret,",
    "cautious": "What if it wiggles again the moment I touch it?",
    "curious": "If I do not peek, I will wonder about it all day,",
    "dramatic": "Oh dear, this is exactly how a funny disaster begins,",
    "thoughtful": "There must be a reason, even if I cannot see it yet,",
}


def compatible(item: LeatherItem, cause: Cause, project: Project) -> bool:
    return cause.id in item.causes and project.id in item.supports


def explain_rejection(item: LeatherItem, cause: Cause, project: Project) -> str:
    if cause.id not in item.causes:
        return (
            f"(No story: {cause.label} does not plausibly make {item.one} move or sound "
            f"the way this mystery needs. Pick a cause that fits the item's shape.)"
        )
    if project.id not in item.supports:
        return (
            f"(No story: {item.one.capitalize()} does not make a good {project.label}. "
            f"The transformation should match the leather object's shape.)"
        )
    return "(No story: that combination does not fit this world.)"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for item_id, item in ITEMS.items():
            for cause_id, cause in CAUSES.items():
                for project_id, project in PROJECTS.items():
                    if compatible(item, cause, project):
                        combos.append((place_id, item_id, cause_id, project_id))
    return combos


def predict_surprise(world: World, cause: Cause) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["moved"] += 1
    sim.facts["cause"] = cause
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "fear": child.memes["fear"],
        "curiosity": child.memes["curiosity"],
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"After lunch, {child.id} followed {helper.label_word} into {place.label}. "
        f"{place.detail}"
    )
    world.say(
        f"{child.id} liked poking through old things because every shelf looked as if it might be hiding a joke."
    )


def discover(world: World, child: Entity, item: LeatherItem, place: Place) -> None:
    world.say(
        f"Near {place.hiding_spot}, {child.id} found {item.phrase}. "
        f"The leather was {item.texture}, and it looked as if it had once had important adventures."
    )


def wobble(world: World, child: Entity, item_ent: Entity, item: LeatherItem, cause: Cause) -> None:
    item_ent.meters["moved"] += 1
    world.facts["cause"] = cause
    propagate(world, narrate=False)
    world.say(
        f"Then {item.sound_line} {cause.motion}."
    )
    world.say(
        f'{child.id} froze. "{THEMES_OF_THOUGHT.get(child.attrs.get("trait", ""), "What is that?"} {child.pronoun()} thought.'
    )


def think_more(world: World, child: Entity, item: LeatherItem, cause: Cause) -> None:
    fear = child.memes["fear"]
    curious = child.memes["curiosity"]
    if fear >= THRESHOLD and curious >= THRESHOLD:
        world.say(
            f'{child.id} took one tiny step back and then one tiny step forward. '
            f'"If that {item.label} is a monster," {child.pronoun()} thought, '
            f'"it is the most polite monster I have ever seen."'
        )
    world.say(
        f'{child.id} stared at the leather thing and listened hard. '
        f'"Please be something ordinary," {child.pronoun()} thought, '
        f'"but if you are something extraordinary, at least be funny."'
    )


def call_helper(world: World, child: Entity, helper: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f'"{helper.label_word.capitalize()}?" {child.id} whispered. "Could you come look at this before it decides to be dramatic?"'
    )


def inspect(world: World, helper: Entity, item_ent: Entity, item: LeatherItem, cause: Cause) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came over, lifted {item.one} carefully, and gave it a puzzled little squint."
    )
    item_ent.meters["opened"] += 1
    world.say(
        f"{cause.reveal}"
    )


def reveal(world: World, child: Entity, cause: Cause) -> None:
    child.meters["truth"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} blinked, and then a laugh popped out before {child.pronoun()} could stop it."
    )
    world.say(
        f"{cause.harmless}"
    )


def decide_transform(world: World, child: Entity, helper: Entity, item_ent: Entity, item: LeatherItem, project: Project) -> None:
    child.memes["inventive"] += 1
    world.say(
        f'"Wait," {child.id} said. "This leather {item.label} is too funny to put away now."'
    )
    world.say(
        f'{child.id} looked at it again and thought, "With the right face, you could become {project.phrase}."'
    )
    item_ent.meters["imagined"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'{helper.label_word.capitalize()} smiled. "Then let us give it a face and see what happens."'
    )


def transform(world: World, child: Entity, helper: Entity, item_ent: Entity, project: Project) -> None:
    item_ent.meters["decorated"] += 1
    item_ent.attrs["project"] = project.id
    propagate(world, narrate=False)
    world.say(
        f"They found button eyes, scraps of paper, and a dab of glue. Soon the old leather piece had {project.face}."
    )
    world.say(
        f"{project.finish}"
    )


def performance(world: World, child: Entity, helper: Entity, item: LeatherItem, project: Project) -> None:
    world.say(
        f"To test the new puppet, {child.id} slipped a hand into the leather {item.label} and made it bow."
    )
    world.say(
        f'"{project.voice}" said the puppet in a voice so ridiculous that even {helper.label_word} had to sit down and laugh.'
    )
    world.say(
        f"By the end, the scary mystery had turned into the silliest little show in {world.place.label}."
    )


def tell(
    place: Place,
    item: LeatherItem,
    cause: Cause,
    project: Project,
    child_name: str = "Mia",
    child_type: str = "girl",
    helper_type: str = "grandfather",
    trait: str = "curious",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            attrs={"trait": trait},
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    item_ent = world.add(
        Entity(
            id="item",
            kind="thing",
            type="leather_item",
            label=item.label,
            phrase=item.phrase,
            tags=set(item.tags),
        )
    )

    introduce(world, child, helper, place)
    discover(world, child, item, place)

    world.para()
    wobble(world, child, item_ent, item, cause)
    think_more(world, child, item, cause)
    call_helper(world, child, helper)

    world.para()
    inspect(world, helper, item_ent, item, cause)
    reveal(world, child, cause)
    decide_transform(world, child, helper, item_ent, item, project)

    world.para()
    transform(world, child, helper, item_ent, project)
    performance(world, child, helper, item, project)

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        item_cfg=item,
        cause=cause,
        project=project,
        item=item_ent,
        suspense=item_ent.meters["moved"] >= THRESHOLD,
        transformed=item_ent.meters["decorated"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        detail="Dust sparkled in the sunbeams, and every box looked too full to keep a straight face.",
        hiding_spot="a stack of hat boxes",
        tags={"attic"},
    ),
    "hall_closet": Place(
        id="hall_closet",
        label="the hall closet",
        detail="Scarves drooped from hooks, umbrellas leaned together, and the whole place smelled faintly of rainy days.",
        hiding_spot="the shoe shelf",
        tags={"closet"},
    ),
    "costume_trunk": Place(
        id="costume_trunk",
        label="the costume room",
        detail="Feather boas, old hats, and shiny capes spilled from a big trunk as if they had been rehearsing without permission.",
        hiding_spot="the open trunk",
        tags={"costume"},
    ),
}

ITEMS = {
    "glove": LeatherItem(
        id="glove",
        label="glove",
        phrase="an old leather glove",
        one="the glove",
        texture="soft, wrinkled, and a little creaky",
        found_in="a drawer",
        sound_line="the glove twitched at the fingers and gave a dry little flap",
        supports={"dragon", "duck", "lizard"},
        causes={"marble", "moth", "wind"},
        tags={"leather", "glove"},
    ),
    "boot": LeatherItem(
        id="boot",
        label="boot",
        phrase="a lonely leather boot",
        one="the boot",
        texture="scuffed, shiny at the toe, and wonderfully squeaky",
        found_in="the shoe shelf",
        sound_line="the boot tipped sideways and thumped once against the wall",
        supports={"dragon", "dog", "crocodile"},
        causes={"marble", "wind", "mouse"},
        tags={"leather", "boot"},
    ),
    "satchel": LeatherItem(
        id="satchel",
        label="satchel",
        phrase="a small leather satchel",
        one="the satchel",
        texture="smooth, buckle-bellied, and serious in the way old bags like to be",
        found_in="a peg",
        sound_line="the satchel gave a bump and its buckle clicked like nervous teeth",
        supports={"owl", "dog"},
        causes={"mouse", "wind"},
        tags={"leather", "satchel"},
    ),
}

CAUSES = {
    "marble": Cause(
        id="marble",
        label="a marble",
        phrase="a runaway marble",
        motion="Something rolled inside with a tiny clack-clack",
        reveal="Inside was only a bright blue marble that had gotten trapped and was now rolling around like it owned the place.",
        harmless="It was not a growl at all, only a marble making grand speeches against the inside wall.",
        tags={"marble"},
    ),
    "mouse": Cause(
        id="mouse",
        label="a toy mouse",
        phrase="a wind-up toy mouse",
        motion="A small hidden bump made the whole thing jiggle again",
        reveal="Tucked in the fold was a wind-up toy mouse, still shivering from one last brave click.",
        harmless="The terrible mystery turned out to be a toy mouse with the manners of a tap-dancing peanut.",
        tags={"toy_mouse"},
    ),
    "wind": Cause(
        id="wind",
        label="a draft",
        phrase="a wandering draft",
        motion="A sneaky draft slipped through the crack under the door and made it stir",
        reveal="The helper opened the door wider, and a puff of wind answered at once, fluttering the leather and making it wobble again.",
        harmless="The great creature was only a draft with too much spare time.",
        tags={"wind"},
    ),
    "moth": Cause(
        id="moth",
        label="a moth",
        phrase="a sleepy moth",
        motion="Something tickled from inside, as light as tissue paper",
        reveal="A sleepy moth fluttered out, blinked at the light, and landed on a box as if nothing exciting had happened at all.",
        harmless="All that suspense had come from a moth who looked more surprised than anybody.",
        tags={"moth"},
    ),
}

PROJECTS = {
    "dragon": Project(
        id="dragon",
        label="dragon puppet",
        phrase="a dragon puppet",
        face="paper spikes, round button eyes, and a grin much too pleased with itself",
        voice="Behold! I am Sir Crispy the Mighty, and I demand exactly one cracker!",
        finish="When the glue dried, the leather thing no longer looked alarming. It looked proud to be ridiculous.",
        tags={"dragon"},
    ),
    "duck": Project(
        id="duck",
        label="duck puppet",
        phrase="a duck puppet",
        face="a paper bill, wobbling eyes, and feather scribbles in yellow crayon",
        voice="Quack! I am the Duke of Puddles, and this room is now a pond!",
        finish="The old leather shape suddenly looked ready to waddle into trouble on purpose.",
        tags={"duck"},
    ),
    "lizard": Project(
        id="lizard",
        label="lizard puppet",
        phrase="a lizard puppet",
        face="green paper scales, tiny eyebrows, and a tongue made from a ribbon",
        voice="I do not chase flies, thank you. I interview them.",
        finish="Instead of seeming spooky, it now looked like a lizard who had read too many funny books.",
        tags={"lizard"},
    ),
    "dog": Project(
        id="dog",
        label="dog puppet",
        phrase="a dog puppet",
        face="floppy paper ears and a nose so round it almost looked surprised",
        voice="Woof! I am Inspector Sniff, and I suspect the biscuits!",
        finish="The leather shape turned into the kind of dog who would bark at his own tail and call it detective work.",
        tags={"dog"},
    ),
    "crocodile": Project(
        id="crocodile",
        label="crocodile puppet",
        phrase="a crocodile puppet",
        face="big toothy paper jaws and eyes perched high like tiny lookout towers",
        voice="Chomp! I only eat carrots, rubber bands, and very rude socks!",
        finish="Its grin became so enormous that it was impossible to be frightened of it anymore.",
        tags={"crocodile"},
    ),
    "owl": Project(
        id="owl",
        label="owl puppet",
        phrase="an owl puppet",
        face="wide circles for eyes and feathery paper eyebrows",
        voice="Hoo! I stay up late to think important thoughts about sandwiches!",
        finish="What had seemed mysterious now looked like an owl who had stayed awake mostly to tell jokes.",
        tags={"owl"},
    ),
}


@dataclass
class StoryParams:
    place: str
    item: str
    cause: str
    project: str
    child_name: str
    child_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="attic",
        item="glove",
        cause="moth",
        project="duck",
        child_name="Mia",
        child_type="girl",
        helper_type="grandfather",
        trait="curious",
    ),
    StoryParams(
        place="hall_closet",
        item="boot",
        cause="marble",
        project="dog",
        child_name="Leo",
        child_type="boy",
        helper_type="mother",
        trait="dramatic",
    ),
    StoryParams(
        place="costume_trunk",
        item="satchel",
        cause="mouse",
        project="owl",
        child_name="Nora",
        child_type="girl",
        helper_type="aunt",
        trait="thoughtful",
    ),
    StoryParams(
        place="attic",
        item="boot",
        cause="wind",
        project="crocodile",
        child_name="Sam",
        child_type="boy",
        helper_type="grandmother",
        trait="cautious",
    ),
    StoryParams(
        place="costume_trunk",
        item="glove",
        cause="marble",
        project="dragon",
        child_name="Ella",
        child_type="girl",
        helper_type="father",
        trait="brave",
    ),
]

GIRL_NAMES = ["Mia", "Ella", "Zoe", "Lily", "Nora", "Ava", "Lucy", "Rose"]
BOY_NAMES = ["Leo", "Sam", "Max", "Finn", "Ben", "Eli", "Theo", "Jack"]
CHILD_TRAITS = ["brave", "cautious", "curious", "dramatic", "thoughtful"]
HELPER_TYPES = ["mother", "father", "grandmother", "grandfather", "aunt", "uncle"]

KNOWLEDGE = {
    "leather": [
        (
            "What is leather?",
            "Leather is a strong material made from animal hide. It can feel smooth or soft, and people use it for things like boots, bags, and gloves.",
        )
    ],
    "marble": [
        (
            "Why does a marble make clacking sounds?",
            "A marble is hard and round, so when it rolls inside a box or shoe it taps and knocks against the sides. That can sound surprising if you do not know it is there.",
        )
    ],
    "toy_mouse": [
        (
            "What is a wind-up toy?",
            "A wind-up toy stores a little bit of energy when you turn it. Then it wiggles or moves by itself for a short time.",
        )
    ],
    "wind": [
        (
            "What is a draft?",
            "A draft is moving air that slips through a crack or open door. It can flutter light things and make them shake or rustle.",
        )
    ],
    "moth": [
        (
            "What is a moth?",
            "A moth is a small flying insect with dusty-looking wings. Some moths fly toward light and flutter softly.",
        )
    ],
    "dragon": [
        (
            "What is a puppet?",
            "A puppet is something you move with your hand or strings to make it seem alive. People often use puppets to tell funny stories.",
        )
    ],
    "duck": [
        (
            "Why are silly voices funny?",
            "A silly voice sounds different from the way people usually talk. The surprise of it can make everyone laugh.",
        )
    ],
    "lizard": [
        (
            "How can craft pieces change how something looks?",
            "Buttons, paper, and ribbon can add eyes, mouths, and shapes that were not there before. That can make an old object look like a character.",
        )
    ],
    "dog": [
        (
            "Why do stories use make-believe talking animals?",
            "Talking animal characters let a story be playful and surprising. They can say ridiculous things that make the story funny.",
        )
    ],
    "crocodile": [
        (
            "What does suspense mean in a story?",
            "Suspense is the feeling of waiting to find out what will happen next. It can make a story exciting, especially when the answer turns out to be harmless or funny.",
        )
    ],
    "owl": [
        (
            "What is inner monologue?",
            "Inner monologue is the voice of a character's thoughts inside their own head. It lets you hear what they worry about or imagine without saying it out loud.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item_cfg"]
    cause = f["cause"]
    project = f["project"]
    place = f["place"]
    return [
        f'Write a funny suspense story for a 3-to-5-year-old that includes the word "leather" and a child hearing a strange sound in {place.label}.',
        f"Tell a gentle transformation story where {child.id} finds {item.phrase}, worries about it in {child.pronoun('possessive')} inner thoughts, and then turns it into {project.phrase}.",
        f"Write a comedy story in which a scary-looking mystery turns out to be {cause.phrase}, and the ending becomes a silly puppet show.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item_cfg"]
    cause = f["cause"]
    project = f["project"]
    place = f["place"]
    helper_word = helper.label_word

    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who found {item.phrase} in {place.label}, and {child.pronoun('possessive')} {helper_word}, who helped solve the mystery.",
        ),
        (
            f"What made the story feel suspenseful at first?",
            f"The leather {item.label} moved and made a strange sound before anyone knew why. That made {child.id} stop and wonder if something alive was hiding inside it.",
        ),
        (
            f"What was {child.id} thinking when the leather {item.label} moved?",
            f"{child.id} felt nervous and curious at the same time. {child.pronoun().capitalize()} thought it might be something extraordinary, but hoped it would at least be funny instead of dangerous.",
        ),
        (
            f"What was really inside or behind the mystery?",
            f"The surprise came from {cause.label}. Once the truth was clear, the fear disappeared because the cause was harmless and ordinary.",
        ),
        (
            f"How did the leather {item.label} transform?",
            f"{child.id} and {helper_word} decorated it with craft pieces until it became {project.phrase}. The change mattered because the same object that had felt spooky now became the reason everyone laughed.",
        ),
        (
            "How did the story end?",
            f"It ended with a puppet performance and lots of laughter. The ending proves the change, because the old leather object became a comic character instead of a mystery.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"leather"} | set(f["cause"].tags) | set(f["project"].tags)
    order = ["leather", "marble", "toy_mouse", "wind", "moth", "dragon", "duck", "lizard", "dog", "crocodile", "owl"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
    for ent in list(world.entities.values()):
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(Item, Cause, Project) :- item(Item), cause(Cause), project(Project),
                                    item_allows_cause(Item, Cause),
                                    item_supports(Item, Project).

valid(Place, Item, Cause, Project) :- place(Place), compatible(Item, Cause, Project).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for cause_id in sorted(item.causes):
            lines.append(asp.fact("item_allows_cause", item_id, cause_id))
        for project_id in sorted(item.supports):
            lines.append(asp.fact("item_supports", item_id, project_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "leather" not in sample.story.lower():
            raise StoryError("smoke test story missing expected rendered text")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a mysterious leather object becomes a silly puppet. Unspecified choices are randomized."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPER_TYPES)
    ap.add_argument("--trait", choices=CHILD_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.cause and args.project:
        item = ITEMS[args.item]
        cause = CAUSES[args.cause]
        project = PROJECTS[args.project]
        if not compatible(item, cause, project):
            raise StoryError(explain_rejection(item, cause, project))
    elif args.item and args.cause and args.project is None:
        if args.cause not in ITEMS[args.item].causes:
            raise StoryError(
                f"(No story: {CAUSES[args.cause].label} does not fit {ITEMS[args.item].one}.)"
            )
    elif args.item and args.project and args.cause is None:
        if args.project not in ITEMS[args.item].supports:
            raise StoryError(
                f"(No story: {ITEMS[args.item].one.capitalize()} cannot plausibly become {PROJECTS[args.project].phrase}.)"
            )

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.item is None or c[1] == args.item)
        and (args.cause is None or c[2] == args.cause)
        and (args.project is None or c[3] == args.project)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, cause, project = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPER_TYPES)
    trait = args.trait or rng.choice(CHILD_TRAITS)

    return StoryParams(
        place=place,
        item=item,
        cause=cause,
        project=project,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        item = ITEMS[params.item]
        cause = CAUSES[params.cause]
        project = PROJECTS[params.project]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]}.)") from None

    if not compatible(item, cause, project):
        raise StoryError(explain_rejection(item, cause, project))

    world = tell(
        place=place,
        item=item,
        cause=cause,
        project=project,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, cause, project) combos:\n")
        for place, item, cause, project in combos:
            print(f"  {place:13} {item:8} {cause:8} {project}")
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
            header = f"### {p.child_name}: {p.item} + {p.cause} -> {p.project} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
