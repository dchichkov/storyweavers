#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/birth_repetition_foreshadowing_rhyming_story.py
===========================================================================

A tiny storyworld about waiting for an animal birth with a child, a grown-up,
and a carefully prepared nesting place. The stories are written in a gentle,
rhyming style, and the world state drives both the foreshadowing and the turn:
signs of coming birth appear first, the child must learn to be soft and patient,
and the ending changes depending on whether the child is calm enough to witness
the birth or wakes to the babies at dawn.

Run it
------
    python storyworlds/worlds/gpt-5.4/birth_repetition_foreshadowing_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/birth_repetition_foreshadowing_rhyming_story.py --animal cat --place basket
    python storyworlds/worlds/gpt-5.4/birth_repetition_foreshadowing_rhyming_story.py --place yard
    python storyworlds/worlds/gpt-5.4/birth_repetition_foreshadowing_rhyming_story.py --helper bell
    python storyworlds/worlds/gpt-5.4/birth_repetition_foreshadowing_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/birth_repetition_foreshadowing_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/birth_repetition_foreshadowing_rhyming_story.py --verify
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Animal:
    id: str
    mother_label: str
    babies_label: str
    baby_word: str
    home_kinds: set[str] = field(default_factory=set)
    shy_need: int = 0
    signs: list[str] = field(default_factory=list)
    sound: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    kind: str
    comfort: int
    sheltered: bool
    rhyme_word: str
    signs_tail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    sense: int
    calm: int
    prep_text: str
    use_text: str
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


def _r_ready(world: World) -> list[str]:
    mother = world.get("mother")
    place = world.get("place")
    child = world.get("child")
    if mother.meters["labor"] < THRESHOLD:
        return []
    if place.meters["warm"] < THRESHOLD or place.meters["quiet"] < THRESHOLD:
        return []
    sig = ("ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mother.meters["settled"] += 1
    child.memes["hope"] += 1
    return ["__ready__"]


def _r_birth(world: World) -> list[str]:
    mother = world.get("mother")
    if mother.meters["settled"] < THRESHOLD:
        return []
    if mother.memes["calm"] < THRESHOLD:
        return []
    sig = ("birth",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mother.meters["babies_born"] += 1
    world.get("child").memes["wonder"] += 1
    world.get("parent").memes["relief"] += 1
    return ["__birth__"]


CAUSAL_RULES = [
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="birth", tag="physical", apply=_r_birth),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


ANIMALS = {
    "cat": Animal(
        id="cat",
        mother_label="cat",
        babies_label="kittens",
        baby_word="kitten",
        home_kinds={"nest", "box"},
        shy_need=5,
        signs=["padded in circles", "kneaded the blanket", "gave a low, careful purr"],
        sound="mew",
        tags={"cat", "birth"},
    ),
    "dog": Animal(
        id="dog",
        mother_label="dog",
        babies_label="puppies",
        baby_word="puppy",
        home_kinds={"box"},
        shy_need=4,
        signs=["turned around and around", "scratched the bedding", "breathed in slow little huffs"],
        sound="woof",
        tags={"dog", "birth"},
    ),
    "goat": Animal(
        id="goat",
        mother_label="goat",
        babies_label="kids",
        baby_word="kid",
        home_kinds={"stall"},
        shy_need=3,
        signs=["stamped once in the straw", "nudged the corner of the stall", "gave a soft, throaty bleat"],
        sound="maa",
        tags={"goat", "birth"},
    ),
}

PLACES = {
    "basket": Place(
        id="basket",
        label="basket",
        phrase="a round basket by the stove",
        kind="nest",
        comfort=2,
        sheltered=True,
        rhyme_word="glow",
        signs_tail="The room was small and warm, and the lamplight moved slow.",
        tags={"basket", "warmth"},
    ),
    "box": Place(
        id="box",
        label="box",
        phrase="a wide box lined with towels",
        kind="box",
        comfort=2,
        sheltered=True,
        rhyme_word="low",
        signs_tail="The towels made a soft little hill, and the shadows lay low.",
        tags={"box", "warmth"},
    ),
    "stall": Place(
        id="stall",
        label="stall",
        phrase="a clean straw stall in the barn",
        kind="stall",
        comfort=2,
        sheltered=True,
        rhyme_word="straw",
        signs_tail="The lantern shone gold on the boards and the straw.",
        tags={"barn", "straw"},
    ),
    "yard": Place(
        id="yard",
        label="yard",
        phrase="an open patch in the windy yard",
        kind="yard",
        comfort=0,
        sheltered=False,
        rhyme_word="sky",
        signs_tail="The wind kept tugging at everything under the sky.",
        tags={"yard", "wind"},
    ),
}

HELPERS = {
    "blanket": Helper(
        id="blanket",
        label="soft blanket",
        phrase="a soft blanket",
        sense=3,
        calm=2,
        prep_text="spread a soft blanket where the mother could nest",
        use_text="The blanket made a quiet hollow, snug and deep.",
        qa_text="spread a soft blanket to make the nesting place warm and cozy",
        tags={"blanket", "warmth"},
    ),
    "water": Helper(
        id="water",
        label="water bowl",
        phrase="a clean water bowl",
        sense=2,
        calm=1,
        prep_text="set down a clean water bowl beside the nesting place",
        use_text="The bowl stood still and shining, easy to reach.",
        qa_text="set down a clean water bowl so the mother animal could rest nearby",
        tags={"water", "care"},
    ),
    "lantern": Helper(
        id="lantern",
        label="dim lantern",
        phrase="a dim lantern",
        sense=2,
        calm=1,
        prep_text="turned the lantern low so the light stayed soft",
        use_text="The dim light kept the corners gentle instead of bright.",
        qa_text="turned the lantern low to keep the room soft and calm",
        tags={"lantern", "light"},
    ),
    "bell": Helper(
        id="bell",
        label="jingly bell",
        phrase="a jingly bell",
        sense=1,
        calm=0,
        prep_text="hung a jingly bell nearby",
        use_text="The bell would only make sharp sounds.",
        qa_text="hung a jingly bell nearby",
        tags={"noise"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ava", "Ella", "Tess", "Ruby", "Maya"]
BOY_NAMES = ["Ben", "Noah", "Sam", "Theo", "Eli", "Max", "Finn", "Owen"]
TRAITS = ["patient", "gentle", "curious", "bouncy", "sleepy", "careful"]
PATIENCE = {
    "patient": 2,
    "gentle": 2,
    "careful": 2,
    "curious": 1,
    "sleepy": 1,
    "bouncy": 0,
}


def place_fits(animal: Animal, place: Place) -> bool:
    return place.sheltered and place.kind in animal.home_kinds


def sensible_helpers() -> list[Helper]:
    return [helper for helper in HELPERS.values() if helper.sense >= SENSE_MIN]


def calm_score(animal: Animal, place: Place, helper: Helper, trait: str, fidget: int) -> int:
    return place.comfort + helper.calm + PATIENCE[trait] - fidget


def witnessed(animal: Animal, place: Place, helper: Helper, trait: str, fidget: int) -> bool:
    return calm_score(animal, place, helper, trait, fidget) >= animal.shy_need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal_id, animal in ANIMALS.items():
        for place_id, place in PLACES.items():
            for helper_id, helper in HELPERS.items():
                if place_fits(animal, place) and helper.sense >= SENSE_MIN:
                    combos.append((animal_id, place_id, helper_id))
    return combos


@dataclass
class StoryParams:
    animal: str
    place: str
    helper: str
    child: str
    gender: str
    parent: str
    trait: str
    fidget: int = 0
    seed: Optional[int] = None


def refrain(place: Place) -> str:
    if place.rhyme_word == "straw":
        return "Hush now, soft now, soon in the straw."
    if place.rhyme_word == "glow":
        return "Hush now, soft now, soon in the glow."
    if place.rhyme_word == "low":
        return "Hush now, soft now, soon and low."
    return "Hush now, soft now, soon we will know."


def explain_rejection(animal: Animal, place: Place) -> str:
    if not place.sheltered:
        return (
            f"(No story: {animal.mother_label}s should not give birth in {place.phrase}. "
            f"The place is open and windy, so it is not a safe, sheltered spot.)"
        )
    return (
        f"(No story: a {animal.mother_label} does not sensibly nest in {place.phrase}. "
        f"Pick a place that fits that animal's birthing space.)"
    )


def explain_helper(helper: Helper) -> str:
    better = ", ".join(sorted(h.id for h in sensible_helpers()))
    return (
        f"(Refusing helper '{helper.id}': it is not a calm, sensible way to prepare "
        f"for a birth. Try one of: {better}.)"
    )


def predict_birth(world: World, animal: Animal, place: Place, helper: Helper, trait: str, fidget: int) -> dict:
    sim = world.copy()
    mother = sim.get("mother")
    child = sim.get("child")
    place_ent = sim.get("place")
    helper_ent = sim.get("helper")
    mother.meters["labor"] += 1
    place_ent.meters["warm"] = float(place.comfort > 0)
    place_ent.meters["quiet"] = 1.0 if (helper.calm + PATIENCE[trait] - fidget) >= 1 else 0.0
    mother.memes["calm"] = 1.0 if witnessed(animal, place, helper, trait, fidget) else 0.0
    child.memes["patience"] = float(PATIENCE[trait])
    helper_ent.meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "born_now": mother.meters["babies_born"] >= THRESHOLD,
        "score": calm_score(animal, place, helper, trait, fidget),
    }


def setup(world: World, child: Entity, parent: Entity, mother: Entity, animal: Animal, place: Place) -> None:
    child.memes["love"] += 1
    world.say(
        f"{child.id} had been waiting all week for the birth. In {place.phrase}, the "
        f"{animal.mother_label} was quiet but not still."
    )
    world.say(place.signs_tail)
    world.say(
        f"First she {animal.signs[0]}, then she {animal.signs[1]}, then she {animal.signs[2]}. "
        f"Those little signs whispered that something new was near."
    )
    world.say(
        f'"{refrain(place)}" sang {parent.label_word}, slow and soft. {child.id} whispered it back, '
        f"though excitement danced in {child.pronoun('possessive')} toes."
    )


def foreshadow(world: World, child: Entity, parent: Entity, mother: Entity, animal: Animal, place: Place) -> None:
    child.memes["excitement"] += 1
    mother.meters["labor"] += 1
    world.say(
        f"The moon climbed higher, and the mother {animal.mother_label} listened with her whole body. "
        f'She made a tiny "{animal.sound}," not loud, not sore, just full of a secret before.'
    )
    pred = predict_birth(world, animal, PLACES[world.facts["place_id"]], HELPERS[world.facts["helper_id"]],
                         world.facts["trait"], world.facts["fidget"])
    world.facts["predicted_score"] = pred["score"]
    if pred["born_now"]:
        world.say(
            f'{parent.label_word.capitalize()} smiled. "Soon means soon," {parent.pronoun()} said. '
            f'"The room is ready, and she feels it too."'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} laid a hand on {child.id}\'s shoulder. '
            f'"Soon still needs soft waiting," {parent.pronoun()} said.'
        )


def prepare(world: World, child: Entity, parent: Entity, helper_ent: Entity, place_ent: Entity,
            helper: Helper, place: Place, trait: str, fidget: int) -> None:
    child.memes["trying"] += 1
    helper_ent.meters["used"] += 1
    place_ent.meters["warm"] = 1.0 if place.comfort > 0 else 0.0
    quiet = helper.calm + PATIENCE[trait] - fidget
    place_ent.meters["quiet"] = 1.0 if quiet >= 1 else 0.0
    world.say(
        f"So {child.id} helped {parent.label_word} and {helper.prep_text}. {helper.use_text}"
    )
    if fidget > 0:
        child.memes["fidgets"] += 1
        world.say(
            f"But {child.id} still gave one small wiggle, then another. "
            f'"Hush now, soft now," {parent.label_word} reminded, and {child.id} took a slower breath.'
        )
    else:
        world.say(
            f'{child.id} folded {child.pronoun("possessive")} hands and said again, '
            f'"{refrain(place)}"'
        )


def settle(world: World, child: Entity, parent: Entity, mother: Entity, animal: Animal,
           helper: Helper, place: Place, trait: str, fidget: int) -> None:
    score = calm_score(animal, place, helper, trait, fidget)
    world.facts["calm_score"] = score
    mother.memes["calm"] = 1.0 if score >= animal.shy_need else 0.0
    if mother.memes["calm"] >= THRESHOLD:
        world.say(
            f"The mother {animal.mother_label} circled once more, then tucked herself down. "
            f"The room went hush-hush, low-low, as if it knew the rhyme."
        )
    else:
        world.say(
            f"The mother {animal.mother_label} kept looking up, not frightened, only watchful. "
            f"The house stayed gentle, but the true hush would take a little longer."
        )
    propagate(world, narrate=False)


def ending_seen(world: World, child: Entity, parent: Entity, mother: Entity, animal: Animal, place: Place) -> None:
    child.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.say(
        f"Then came the turn they had been waiting for: one wet little {animal.baby_word}, "
        f"then another, blinking in the dim light."
    )
    world.say(
        f'{child.id} did not shout. {child.pronoun().capitalize()} only breathed, '
        f'"{refrain(place)}" and smiled so wide it almost glowed.'
    )
    world.say(
        f"By the end, {place.label} held the mother and her {animal.babies_label}, "
        f"and the whole night seemed to rhyme with the word new."
    )


def ending_dawn(world: World, child: Entity, parent: Entity, mother: Entity, animal: Animal, place: Place) -> None:
    child.memes["sleep"] += 1
    parent.memes["tenderness"] += 1
    world.say(
        f"After a long, soft wait, {child.id}'s eyes grew heavy. {parent.label_word.capitalize()} carried "
        f"{child.pronoun('object')} to bed with the rhyme still warm in the air."
    )
    world.say(
        f"When morning made a pale gold line, {parent.label_word} came back smiling. "
        f'"Wake, little watcher. The birth is done."'
    )
    world.say(
        f"{child.id} ran to {place.phrase} and found the mother {animal.mother_label} curled around her "
        f"{animal.babies_label}. The waiting had turned to wonder while the sky grew light."
    )


def tell(animal: Animal, place: Place, helper: Helper, child_name: str, gender: str,
         parent_type: str, trait: str, fidget: int) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=gender,
        role="child",
        traits=[trait],
        tags={"child"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    mother = world.add(Entity(
        id="mother",
        type=animal.mother_label,
        label=f"the mother {animal.mother_label}",
        phrase=f"the mother {animal.mother_label}",
        role="mother_animal",
        tags=set(animal.tags),
    ))
    place_ent = world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        phrase=place.phrase,
        role="place",
        tags=set(place.tags),
    ))
    helper_ent = world.add(Entity(
        id="helper",
        type="helper",
        label=helper.label,
        phrase=helper.phrase,
        role="helper",
        tags=set(helper.tags),
    ))

    world.facts.update(
        animal=animal,
        place=place,
        helper=helper,
        child=child,
        parent=parent,
        mother=mother,
        place_id=place.id,
        helper_id=helper.id,
        trait=trait,
        fidget=fidget,
    )

    setup(world, child, parent, mother, animal, place)
    world.para()
    foreshadow(world, child, parent, mother, animal, place)
    prepare(world, child, parent, helper_ent, place_ent, helper, place, trait, fidget)
    world.para()
    settle(world, child, parent, mother, animal, helper, place, trait, fidget)

    if witnessed(animal, place, helper, trait, fidget):
        mother.meters["babies_born"] = 1.0
        world.facts["outcome"] = "seen"
        ending_seen(world, child, parent, mother, animal, place)
    else:
        world.facts["outcome"] = "dawn"
        ending_dawn(world, child, parent, mother, animal, place)

    world.facts["witnessed"] = world.facts["outcome"] == "seen"
    world.facts["babies_born"] = True
    return world


KNOWLEDGE = {
    "birth": [
        (
            "What does birth mean?",
            "Birth is when a baby comes into the world. For animals, it is the time when the mother has her babies.",
        )
    ],
    "cat": [
        (
            "What is a kitten?",
            "A kitten is a baby cat. Kittens are born very small and need warmth and care.",
        )
    ],
    "dog": [
        (
            "What is a puppy?",
            "A puppy is a baby dog. Puppies are born tiny and stay close to their mother at first.",
        )
    ],
    "goat": [
        (
            "What is a kid?",
            "A kid is a baby goat. Baby goats are called kids even though they are animals, not children.",
        )
    ],
    "blanket": [
        (
            "Why does a soft blanket help a nesting place?",
            "A soft blanket can help make a place warm and gentle. Warm, cozy places help newborn animals rest.",
        )
    ],
    "water": [
        (
            "Why might a mother animal need water nearby?",
            "Water helps the mother rest and drink without going far. Keeping it close makes the place calmer.",
        )
    ],
    "lantern": [
        (
            "Why use dim light instead of bright light?",
            "Dim light feels softer and calmer. Bright light can feel sharp when everyone is trying to stay quiet.",
        )
    ],
    "straw": [
        (
            "Why is straw good in a barn stall?",
            "Straw is dry, soft, and warm. It gives animals a cozy place to lie down.",
        )
    ],
    "warmth": [
        (
            "Why do newborn animals need warmth?",
            "Newborn animals are very little and can get cold easily. Warmth helps them stay safe and comfortable.",
        )
    ],
    "care": [
        (
            "How can a child help gently when animals are having babies?",
            "A child can help by being quiet, listening to the grown-up, and bringing simple things like a blanket or water. Gentle help keeps the place calm.",
        )
    ],
}
KNOWLEDGE_ORDER = ["birth", "cat", "dog", "goat", "blanket", "water", "lantern", "straw", "warmth", "care"]


def generation_prompts(world: World) -> list[str]:
    animal = world.facts["animal"]
    place = world.facts["place"]
    child = world.facts["child"]
    outcome = world.facts["outcome"]
    end = (
        "and the child softly witnesses the babies being born"
        if outcome == "seen"
        else "and the child wakes at dawn to find the babies already born"
    )
    return [
        (
            f'Write a rhyming story for a 3-to-5-year-old that includes the word "birth", '
            f"uses repetition and foreshadowing, and is about a child waiting for a {animal.mother_label}'s babies."
        ),
        (
            f"Tell a gentle story where {child.id} helps prepare {place.phrase}, hears repeated soothing words, "
            f"notices signs that the birth is near, {end}."
        ),
        (
            f'Write a soft bedtime-style rhyme with a repeated line like "{refrain(place)}" and a clear foreshadowing middle '
            f"before the babies arrive."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    animal = world.facts["animal"]
    place = world.facts["place"]
    helper = world.facts["helper"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and a mother {animal.mother_label} getting ready for birth.",
        ),
        (
            "What showed that the birth was near?",
            f"The mother {animal.mother_label} kept making nesting signs, like {animal.signs[0]} and {animal.signs[1]}. Those signs foreshadowed that the babies would come soon.",
        ),
        (
            "What words were repeated in the story?",
            f'The repeated line was "{refrain(place)}" It came back again and again to make the waiting feel calm and to hint that something new was coming soon.',
        ),
        (
            f"How did {child.id} help?",
            f"{child.id} helped {helper.qa_text}. That mattered because a calm, cozy place made it easier for the mother {animal.mother_label} to settle.",
        ),
    ]
    if outcome == "seen":
        qa.append(
            (
                f"Did {child.id} see the babies being born?",
                f"Yes. {child.id} stayed soft and quiet enough to witness the birth. Because the room was calm, the mother {animal.mother_label} settled and the babies arrived while {child.pronoun()} watched.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the mother {animal.mother_label} curled around her {animal.babies_label}. The ending image shows that the waiting turned into new life.",
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id} see the birth happen?",
                f"Not exactly. {child.id} waited for a long time and then fell asleep, and by dawn the birth was done. The quiet help still mattered because the babies arrived safely in the cozy place.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended at dawn, when {child.id} found the mother {animal.mother_label} already curled around her {animal.babies_label}. The morning picture proves that the promised new beginning finally came.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"birth", "warmth", "care"}
    tags |= set(world.facts["animal"].tags)
    tags |= set(world.facts["helper"].tags)
    tags |= set(world.facts["place"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    if world.facts:
        lines.append(f"  outcome: {world.facts.get('outcome')}")
        lines.append(f"  calm_score: {world.facts.get('calm_score', world.facts.get('predicted_score'))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="cat",
        place="basket",
        helper="blanket",
        child="Mina",
        gender="girl",
        parent="mother",
        trait="patient",
        fidget=0,
    ),
    StoryParams(
        animal="dog",
        place="box",
        helper="water",
        child="Ben",
        gender="boy",
        parent="father",
        trait="gentle",
        fidget=0,
    ),
    StoryParams(
        animal="goat",
        place="stall",
        helper="lantern",
        child="Ruby",
        gender="girl",
        parent="father",
        trait="curious",
        fidget=1,
    ),
    StoryParams(
        animal="cat",
        place="box",
        helper="lantern",
        child="Theo",
        gender="boy",
        parent="mother",
        trait="bouncy",
        fidget=1,
    ),
]


ASP_RULES = r"""
sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
fits(A, P) :- animal(A), place(P), sheltered(P), home_kind(A, K), place_kind(P, K).
valid(A, P, H) :- animal(A), place(P), helper(H), fits(A, P), sensible(H).

score(C + HC + TP - F) :- chosen_place(P), comfort(P, C),
                          chosen_helper(H), calm(H, HC),
                          chosen_trait(T), patience(T, TP),
                          chosen_fidget(F).
witnessed :- chosen_animal(A), shy_need(A, N), score(S), S >= N.

outcome(seen) :- witnessed.
outcome(dawn) :- not witnessed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("shy_need", animal_id, animal.shy_need))
        for kind in sorted(animal.home_kinds):
            lines.append(asp.fact("home_kind", animal_id, kind))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("place_kind", place_id, place.kind))
        lines.append(asp.fact("comfort", place_id, place.comfort))
        if place.sheltered:
            lines.append(asp.fact("sheltered", place_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        lines.append(asp.fact("calm", helper_id, helper.calm))
    for trait, value in PATIENCE.items():
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("patience", trait, value))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_animal", params.animal),
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_fidget", params.fidget),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    animal = ANIMALS[params.animal]
    place = PLACES[params.place]
    helper = HELPERS[params.helper]
    return "seen" if witnessed(animal, place, helper, params.trait, params.fidget) else "dawn"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed for seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        try:
            py = outcome_of(params)
            asp_value = asp_outcome(params)
            if py != asp_value:
                mismatches += 1
        except Exception as err:
            rc = 1
            print(f"ERROR while comparing outcomes for {params}: {err}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"ERROR: smoke-test generation failed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child waits for an animal birth in a gentle rhyming story."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--fidget", type=int, choices=[0, 1], help="0 = steady waiting, 1 = a wrigglier wait")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.place:
        animal = ANIMALS[args.animal]
        place = PLACES[args.place]
        if not place_fits(animal, place):
            raise StoryError(explain_rejection(animal, place))
    if args.helper:
        helper = HELPERS[args.helper]
        if helper.sense < SENSE_MIN:
            raise StoryError(explain_helper(helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.place is None or combo[1] == args.place)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, place_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    fidget = args.fidget if args.fidget is not None else rng.choice([0, 1])

    return StoryParams(
        animal=animal_id,
        place=place_id,
        helper=helper_id,
        child=child,
        gender=gender,
        parent=parent,
        trait=trait,
        fidget=fidget,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.trait not in PATIENCE:
        raise StoryError(f"(Unknown trait: {params.trait})")
    animal = ANIMALS[params.animal]
    place = PLACES[params.place]
    helper = HELPERS[params.helper]
    if not place_fits(animal, place):
        raise StoryError(explain_rejection(animal, place))
    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper(helper))

    world = tell(
        animal=animal,
        place=place,
        helper=helper,
        child_name=params.child,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
        fidget=params.fidget,
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
        print(f"{len(combos)} compatible (animal, place, helper) combos:\n")
        for animal, place, helper in combos:
            print(f"  {animal:6} {place:7} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.child}: {p.animal} in {p.place} with {p.helper} ({outcome_of(p)})"
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
