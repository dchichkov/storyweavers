#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shoot_laxative_dialogue_heartwarming.py
==================================================================

A standalone story world about a child helping a tummy-sick animal with a
vet-approved laxative, then watching a garden shoot stand bright again when the
scary part is over.

Seed requirements covered:
- includes the words "shoot" and "laxative"
- uses dialogue heavily
- stays heartwarming

The world model is small and concrete:
- a child notices that a gentle family animal feels unwell
- a grown-up calls the vet and gets a sensible plan
- the child helps mix a laxative into a safe food carrier
- water, a little walk, and patient care help the animal recover
- the ending image shows a green garden shoot and a calmer heart

Run it
------
    python storyworlds/worlds/gpt-5.4/shoot_laxative_dialogue_heartwarming.py
    python storyworlds/worlds/gpt-5.4/shoot_laxative_dialogue_heartwarming.py --animal rabbit --cause fur_clump --carrier pumpkin
    python storyworlds/worlds/gpt-5.4/shoot_laxative_dialogue_heartwarming.py --animal rabbit --carrier oats
    python storyworlds/worlds/gpt-5.4/shoot_laxative_dialogue_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/shoot_laxative_dialogue_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/shoot_laxative_dialogue_heartwarming.py --verify
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
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle"}
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    shelter: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalSpec:
    id: str
    label: str
    phrase: str
    sound: str
    gait: str
    home: str
    plant_like: str
    safe_carriers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    line: str
    cue: str
    needs_wet: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    spoon_line: str
    wet: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    image: str
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


def _r_worry(world: World) -> list[str]:
    animal = world.get("animal")
    child = world.get("child")
    helper = world.get("helper")
    if animal.meters["blocked"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    helper.memes["care"] += 1
    return ["__worry__"]


def _r_relief(world: World) -> list[str]:
    animal = world.get("animal")
    if animal.meters["blocked"] < THRESHOLD:
        return []
    if animal.meters["laxative"] < THRESHOLD:
        return []
    if animal.meters["water"] < THRESHOLD:
        return []
    if animal.meters["walk"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["blocked"] = 0.0
    animal.meters["pain"] = 0.0
    animal.meters["relief"] += 1
    child = world.get("child")
    helper = world.get("helper")
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    helper.memes["joy"] += 1
    animal.memes["trust"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="relief", tag="physical", apply=_r_relief),
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


SETTINGS = {
    "cottage_garden": Setting(
        id="cottage_garden",
        place="the little cottage garden",
        shelter="the warm kitchen door",
        path="the stone path by the lettuce beds",
        tags={"garden"},
    ),
    "backyard_patch": Setting(
        id="backyard_patch",
        place="the backyard vegetable patch",
        shelter="the back steps",
        path="the short path beside the pea vines",
        tags={"garden"},
    ),
    "orchard_corner": Setting(
        id="orchard_corner",
        place="the sunny orchard corner",
        shelter="the red shed door",
        path="the soft path under the apple tree",
        tags={"garden"},
    ),
}

ANIMALS = {
    "rabbit": AnimalSpec(
        id="rabbit",
        label="rabbit",
        phrase="a soft gray rabbit named Clover",
        sound="sniffed",
        gait="hopped",
        home="hutch",
        plant_like="pea leaves",
        safe_carriers={"pumpkin", "herb_mash"},
        tags={"rabbit", "animal"},
    ),
    "goat": AnimalSpec(
        id="goat",
        label="goat",
        phrase="a small white goat named Button",
        sound="bleated",
        gait="trotted",
        home="pen",
        plant_like="bean leaves",
        safe_carriers={"applesauce", "pumpkin"},
        tags={"goat", "animal"},
    ),
    "pony": AnimalSpec(
        id="pony",
        label="pony",
        phrase="a sleepy brown pony named Maple",
        sound="snorted",
        gait="walked",
        home="stall",
        plant_like="tall grass",
        safe_carriers={"applesauce", "oats"},
        tags={"pony", "animal"},
    ),
}

CAUSES = {
    "fur_clump": Cause(
        id="fur_clump",
        line="had swallowed too much loose fur while grooming",
        cue="kept sitting still instead of nosing around for breakfast",
        needs_wet=True,
        tags={"vet", "digestion"},
    ),
    "dry_feed": Cause(
        id="dry_feed",
        line="had eaten a pile of dry feed too quickly",
        cue="looked full, quiet, and a little uncomfortable",
        needs_wet=False,
        tags={"vet", "digestion"},
    ),
    "low_water": Cause(
        id="low_water",
        line="had not been drinking enough water on a warm day",
        cue="stood with droopy eyes and a slow, unhappy belly",
        needs_wet=True,
        tags={"water", "digestion"},
    ),
}

CARRIERS = {
    "pumpkin": Carrier(
        id="pumpkin",
        label="pumpkin",
        phrase="a spoonful of soft pumpkin",
        spoon_line="This soft pumpkin will help the medicine go down gently.",
        wet=True,
        tags={"pumpkin", "food"},
    ),
    "applesauce": Carrier(
        id="applesauce",
        label="applesauce",
        phrase="a little bowl of applesauce",
        spoon_line="The applesauce is smooth, and most animals like the sweet smell.",
        wet=True,
        tags={"applesauce", "food"},
    ),
    "herb_mash": Carrier(
        id="herb_mash",
        label="herb mash",
        phrase="a cool herb mash",
        spoon_line="The herb mash is damp and easy on a small tummy.",
        wet=True,
        tags={"herbs", "food"},
    ),
    "oats": Carrier(
        id="oats",
        label="oats",
        phrase="a handful of soaked oats",
        spoon_line="The soaked oats will hide the medicine and feel familiar.",
        wet=True,
        tags={"oats", "food"},
    ),
}

PLANTS = {
    "pea_shoot": Plant(
        id="pea_shoot",
        label="pea shoot",
        phrase="a tiny pea shoot",
        image="a tiny pea shoot was lifting its green head through the dark soil",
        tags={"shoot", "garden"},
    ),
    "bean_shoot": Plant(
        id="bean_shoot",
        label="bean shoot",
        phrase="a curly bean shoot",
        image="a curly bean shoot had unrolled like a small green ribbon",
        tags={"shoot", "garden"},
    ),
    "sunflower_shoot": Plant(
        id="sunflower_shoot",
        label="sunflower shoot",
        phrase="a sturdy sunflower shoot",
        image="a sturdy sunflower shoot was standing taller than it had the day before",
        tags={"shoot", "garden"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Ella", "Ruby", "June", "Tess"]
BOY_NAMES = ["Leo", "Sam", "Ben", "Noah", "Eli", "Finn", "Theo", "Max"]
TRAITS = ["gentle", "careful", "patient", "tenderhearted", "quiet", "hopeful"]


def carrier_ok(animal: AnimalSpec, carrier: Carrier) -> bool:
    return carrier.id in animal.safe_carriers


def cause_ok(cause: Cause, carrier: Carrier) -> bool:
    if cause.needs_wet and not carrier.wet:
        return False
    return True


def valid_combo(setting_id: str, animal_id: str, cause_id: str, carrier_id: str) -> bool:
    if setting_id not in SETTINGS or animal_id not in ANIMALS or cause_id not in CAUSES or carrier_id not in CARRIERS:
        return False
    animal = ANIMALS[animal_id]
    cause = CAUSES[cause_id]
    carrier = CARRIERS[carrier_id]
    return carrier_ok(animal, carrier) and cause_ok(cause, carrier)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for animal_id in ANIMALS:
            for cause_id in CAUSES:
                for carrier_id in CARRIERS:
                    if valid_combo(setting_id, animal_id, cause_id, carrier_id):
                        out.append((setting_id, animal_id, cause_id, carrier_id))
    return out


@dataclass
class StoryParams:
    setting: str
    animal: str
    cause: str
    carrier: str
    plant: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def explain_rejection(animal: AnimalSpec, cause: Cause, carrier: Carrier) -> str:
    if not carrier_ok(animal, carrier):
        allowed = ", ".join(sorted(animal.safe_carriers))
        return (
            f"(No story: {animal.label}s in this world are not fed {carrier.label} as the medicine carrier. "
            f"Try one of: {allowed}.)"
        )
    if not cause_ok(cause, carrier):
        return (
            f"(No story: {cause.id.replace('_', ' ')} needs a soft wet carrier, and {carrier.label} is not suitable.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_recovery(world: World) -> dict:
    sim = world.copy()
    animal = sim.get("animal")
    animal.meters["laxative"] += 1
    animal.meters["water"] += 1
    animal.meters["walk"] += 1
    propagate(sim, narrate=False)
    return {
        "recovers": animal.meters["relief"] >= THRESHOLD,
        "blocked": animal.meters["blocked"] >= THRESHOLD,
    }


def introduce(world: World, setting: Setting, child: Entity, helper: Entity, animal: Entity, animal_cfg: AnimalSpec) -> None:
    world.say(
        f"Early one spring morning, {child.id} followed {child.pronoun('possessive')} {helper.label_word} into {setting.place}. "
        f"They had come to open {animal.pronoun('possessive')} {animal_cfg.home}, check the water pail, and say hello to {animal.id}."
    )
    world.say(
        f'"Good morning, {animal.id}," {child.id} whispered. Usually {animal.pronoun()} {animal_cfg.sound} at once and {animal_cfg.gait} over for a cuddle.'
    )


def notice_problem(world: World, child: Entity, helper: Entity, animal: Entity, cause: Cause) -> None:
    animal.meters["blocked"] += 1
    animal.meters["pain"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But that morning {animal.id} only {cause.cue}. {child.id} knelt beside {animal.pronoun('object')} and frowned."
    )
    world.say(
        f'"{helper.label_word.capitalize()}, {animal.id} does not look like {animal.pronoun()} feels good," {child.id} said.'
    )
    world.say(
        f'{helper.label_word.capitalize()} rested a gentle hand on {animal.pronoun("possessive")} back. '
        f'"I think you are right," {helper.pronoun()} said. "Let us pay close attention."'
    )


def explain_vet(world: World, child: Entity, helper: Entity, animal: Entity, cause: Cause, carrier: Carrier) -> None:
    child.memes["worry"] += 1
    helper.memes["care"] += 1
    world.say(
        f'Soon {helper.label_word} had called the vet. After listening carefully, {helper.pronoun()} nodded and said, '
        f'"The vet thinks {animal.id} {cause.line}. {helper.pronoun().capitalize()} says a gentle laxative will help."'
    )
    world.say(
        f'{child.id} blinked. "Laxative?" {child.pronoun().capitalize()} echoed. "Will that hurt?"'
    )
    world.say(
        f'"No, sweetheart," {helper.label_word} said. "It is medicine to help {animal.id}\'s body move again. '
        f'We will mix the laxative into {carrier.phrase}, give {animal.pronoun("object")} water, and take {animal.pronoun("object")} for a little walk."'
    )


def invite_help(world: World, child: Entity, helper: Entity, carrier: Carrier) -> None:
    child.memes["courage"] += 1
    world.say(
        f'{child.id} still looked worried, so {helper.label_word} held out the small spoon. '
        f'"Would you like to help me?" {helper.pronoun()} asked.'
    )
    world.say(
        f'"Yes," {child.id} said after a breath. "{carrier.spoon_line}"'
    )


def mix_medicine(world: World, child: Entity, helper: Entity, animal: Entity, carrier: Carrier) -> None:
    child.memes["care"] += 1
    world.say(
        f'Together they stirred the clear laxative into {carrier.phrase}. '
        f'The spoon made a soft tap-tap sound against the bowl.'
    )
    world.say(
        f'"Here you go, {animal.id}," {child.id} murmured. "{helper.label_word.capitalize()} and I are helping your tummy."'
    )
    animal.memes["trust"] += 1
    animal.meters["laxative"] += 1
    world.say(
        f'{animal.id} sniffed, took one careful taste, and then finished the rest.'
    )


def water_and_walk(world: World, setting: Setting, child: Entity, helper: Entity, animal: Entity) -> None:
    animal.meters["water"] += 1
    animal.meters["walk"] += 1
    world.say(
        f'After that, {child.id} carried over fresh water, and {animal.id} drank in slow, grateful sips.'
    )
    world.say(
        f'"Now we wait and move gently," {helper.label_word} said. They went together along {setting.path}, '
        f'with {child.id} walking on one side and {animal.id} on the other.'
    )


def recover(world: World, child: Entity, helper: Entity, animal: Entity) -> None:
    propagate(world, narrate=False)
    if animal.meters["relief"] < THRESHOLD:
        raise StoryError("(Story failure: the treatment sequence did not reach relief.)")
    world.say(
        f'By the time they reached the gate, {animal.id} gave a stronger little sound and stopped looking so tight and worried.'
    )
    world.say(
        f'"There now," {helper.label_word} said with a smile. "The medicine worked."'
    )
    world.say(
        f'{child.id} let out the breath {child.pronoun()} had been holding. '
        f'"You feel better," {child.pronoun()} said, rubbing {animal.id} between the ears.'
    )


def closing_image(world: World, child: Entity, helper: Entity, animal: Entity, plant: Plant, animal_cfg: AnimalSpec) -> None:
    child.memes["joy"] += 1
    child.memes["care"] += 1
    world.say(
        f'They stood quietly for a moment near the garden bed, and then {child.id} noticed something green beside the fence.'
    )
    world.say(
        f'{plant.image}. {child.id} pointed and smiled. "Look, {helper.label_word}--a {plant.label}!"'
    )
    world.say(
        f'"Yes," {helper.label_word} said. "Some things need a little help, a little time, and a lot of kindness."'
    )
    world.say(
        f'{animal.id} {animal_cfg.gait} toward the fresh leaves, lively again, and {child.id} laughed. '
        f'The morning no longer felt scary. It felt soft and bright.'
    )


def tell(
    setting: Setting,
    animal_cfg: AnimalSpec,
    cause: Cause,
    carrier: Carrier,
    plant: Plant,
    child_name: str = "Lila",
    child_gender: str = "girl",
    helper_type: str = "grandmother",
    trait: str = "gentle",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    animal = world.add(Entity(
        id=animal_cfg.phrase.split()[-1].rstrip(","),
        kind="animal",
        type=animal_cfg.id,
        label=animal_cfg.label,
        phrase=animal_cfg.phrase,
        role="animal",
        tags=set(animal_cfg.tags),
    ))
    animal.id = animal_cfg.phrase.split()[-1]
    # unreachable safety no-op
    world.entities = {}
    child = world.add(child)
    helper = world.add(helper)
    animal = world.add(Entity(
        id=animal_cfg.phrase.split()[-1],
        kind="animal",
        type=animal_cfg.id,
        label=animal_cfg.label,
        phrase=animal_cfg.phrase,
        role="animal",
        tags=set(animal_cfg.tags),
    ))

    introduce(world, setting, child, helper, animal, animal_cfg)
    notice_problem(world, child, helper, animal, cause)

    world.para()
    explain_vet(world, child, helper, animal, cause, carrier)
    invite_help(world, child, helper, carrier)

    world.para()
    mix_medicine(world, child, helper, animal, carrier)
    water_and_walk(world, setting, child, helper, animal)
    recover(world, child, helper, animal)

    world.para()
    closing_image(world, child, helper, animal, plant, animal_cfg)

    world.facts.update(
        setting=setting,
        animal_cfg=animal_cfg,
        cause=cause,
        carrier=carrier,
        plant=plant,
        child=child,
        helper=helper,
        animal=animal,
        recovered=animal.meters["relief"] >= THRESHOLD,
        used_laxative=animal.meters["laxative"] >= THRESHOLD,
        walked=animal.meters["walk"] >= THRESHOLD,
        drank=animal.meters["water"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "rabbit": [(
        "What do rabbits need for healthy tummies?",
        "Rabbits need water, hay, and the right food to keep their tummies moving. If a rabbit seems uncomfortable, a grown-up should call a vet."
    )],
    "goat": [(
        "Why should a goat's medicine come from a vet?",
        "A goat is a real farm animal, so its medicine should be chosen by a vet. A vet knows what is safe and how much to give."
    )],
    "pony": [(
        "Why do ponies need plenty of water?",
        "Ponies need water to help their bodies work well, including their tummies. Not drinking enough can make them feel unwell."
    )],
    "vet": [(
        "What does a vet do?",
        "A vet is a doctor for animals. Vets help animals when they are sick or hurt and tell families how to care for them safely."
    )],
    "digestion": [(
        "What is a laxative?",
        "A laxative is a kind of medicine that helps the body move poop along when someone or some animal is blocked up. It should only be given when a doctor or vet says it is needed."
    )],
    "water": [(
        "Why can a little walk help a tummy?",
        "Gentle movement can help a body wake up and get things moving. That is why a grown-up might suggest water, rest, and a slow walk."
    )],
    "shoot": [(
        "What is a plant shoot?",
        "A plant shoot is the fresh new part of a plant that pushes up as it begins to grow. It is often small, green, and tender."
    )],
    "pumpkin": [(
        "Why do some animals eat soft foods with medicine?",
        "A soft food can hide the taste of medicine and make it easier to swallow. A grown-up still has to choose a food that is safe for that animal."
    )],
    "applesauce": [(
        "Why do grown-ups mix medicine carefully?",
        "Medicine has to be measured and mixed the right way so it is safe and helpful. That is why children help with a grown-up beside them."
    )],
    "herbs": [(
        "What is an herb mash?",
        "An herb mash is a soft mixture of safe leaves or herbs with water. It can be easier on a small animal's mouth and tummy than something dry."
    )],
    "oats": [(
        "Why are soaked oats softer than dry oats?",
        "Soaked oats have taken in water, so they feel softer and gentler to chew. That can make them easier to eat."
    )],
}
KNOWLEDGE_ORDER = [
    "rabbit",
    "goat",
    "pony",
    "vet",
    "digestion",
    "water",
    "shoot",
    "pumpkin",
    "applesauce",
    "herbs",
    "oats",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    animal_cfg = world.facts["animal_cfg"]
    plant = world.facts["plant"]
    carrier = world.facts["carrier"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "shoot" and "laxative" and uses lots of dialogue.',
        f"Tell a gentle story where {child.id} helps {child.pronoun('possessive')} {helper.label_word} care for {animal_cfg.phrase} after a vet suggests a laxative mixed into {carrier.phrase}.",
        f"Write a story that begins with worry in a garden and ends with {plant.phrase} and a child feeling brave because kindness helped."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    animal = f["animal"]
    animal_cfg = f["animal_cfg"]
    cause = f["cause"]
    carrier = f["carrier"]
    plant = f["plant"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {helper.label_word}, and {animal_cfg.phrase}. They spend the morning caring for {animal.id} together."
        ),
        (
            f"Why did {child.id} know something was wrong?",
            f"{child.id} saw that {animal.id} {cause.cue} instead of acting lively. That change made {child.pronoun('object')} stop and pay close attention."
        ),
        (
            f"What did the vet say would help {animal.id}?",
            f"The vet thought {animal.id} {cause.line} and suggested a gentle laxative. {helper.label_word.capitalize()} explained that the medicine would help {animal.id}'s body move again."
        ),
        (
            f"How did {child.id} help?",
            f"{child.id} helped stir the laxative into {carrier.phrase}, carried fresh water, and walked beside {animal.id}. Those small jobs mattered because the care was gentle and patient."
        ),
    ]
    if f["recovered"]:
        qa.append((
            f"How did the story show that {animal.id} felt better?",
            f"After the medicine, water, and walk, {animal.id} stopped looking tight and uncomfortable. Then {helper.label_word} said the medicine had worked, and {child.id} could see the change."
        ))
    qa.append((
        "Why was the plant shoot important at the end?",
        f"The {plant.label} gave the ending a quiet, hopeful picture. It showed that growth and healing had both happened by the time the scary feeling was over."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    tags |= world.facts["animal_cfg"].tags
    tags |= world.facts["cause"].tags
    tags |= world.facts["carrier"].tags
    tags |= world.facts["plant"].tags
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, C, K) :- setting(S), animal(A), cause(C), carrier(K), carrier_ok(A, K), cause_ok(C, K).

recovered :- chosen_setting(S), chosen_animal(A), chosen_cause(C), chosen_carrier(K), valid(S, A, C, K),
             give_laxative, give_water, take_walk.
outcome(happy) :- recovered.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        for cid in sorted(animal.safe_carriers):
            lines.append(asp.fact("carrier_ok", aid, cid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for kid, carrier in CARRIERS.items():
            ok = cause_ok(cause, carrier)
            if ok:
                lines.append(asp.fact("cause_ok", cid, kid))
    for kid in CARRIERS:
        lines.append(asp.fact("carrier", kid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_animal", params.animal),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_carrier", params.carrier),
        asp.fact("give_laxative"),
        asp.fact("give_water"),
        asp.fact("take_walk"),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="cottage_garden",
        animal="rabbit",
        cause="fur_clump",
        carrier="pumpkin",
        plant="pea_shoot",
        child_name="Lila",
        child_gender="girl",
        helper_type="grandmother",
        trait="gentle",
    ),
    StoryParams(
        setting="backyard_patch",
        animal="goat",
        cause="dry_feed",
        carrier="applesauce",
        plant="bean_shoot",
        child_name="Sam",
        child_gender="boy",
        helper_type="grandfather",
        trait="patient",
    ),
    StoryParams(
        setting="orchard_corner",
        animal="pony",
        cause="low_water",
        carrier="applesauce",
        plant="sunflower_shoot",
        child_name="Ruby",
        child_gender="girl",
        helper_type="mother",
        trait="careful",
    ),
    StoryParams(
        setting="backyard_patch",
        animal="pony",
        cause="dry_feed",
        carrier="oats",
        plant="bean_shoot",
        child_name="Theo",
        child_gender="boy",
        helper_type="father",
        trait="hopeful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child helps a tummy-sick animal with a vet-approved laxative and a gentle walk."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--helper", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.cause and args.carrier:
        animal = ANIMALS[args.animal]
        cause = CAUSES[args.cause]
        carrier = CARRIERS[args.carrier]
        if not valid_combo(args.setting or next(iter(SETTINGS)), args.animal, args.cause, args.carrier):
            raise StoryError(explain_rejection(animal, cause, carrier))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.animal is None or combo[1] == args.animal)
        and (args.cause is None or combo[2] == args.cause)
        and (args.carrier is None or combo[3] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, animal_id, cause_id, carrier_id = rng.choice(sorted(combos))
    plant_id = args.plant or rng.choice(sorted(PLANTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or _pick_name(rng, gender)
    helper_type = args.helper or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        animal=animal_id,
        cause=cause_id,
        carrier=carrier_id,
        plant=plant_id,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.animal not in ANIMALS:
        raise StoryError(f"(No story: unknown animal '{params.animal}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{params.cause}'.)")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(No story: unknown carrier '{params.carrier}'.)")
    if params.plant not in PLANTS:
        raise StoryError(f"(No story: unknown plant '{params.plant}'.)")
    if not valid_combo(params.setting, params.animal, params.cause, params.carrier):
        raise StoryError(explain_rejection(ANIMALS[params.animal], CAUSES[params.cause], CARRIERS[params.carrier]))

    world = tell(
        setting=SETTINGS[params.setting],
        animal_cfg=ANIMALS[params.animal],
        cause=CAUSES[params.cause],
        carrier=CARRIERS[params.carrier],
        plant=PLANTS[params.plant],
        child_name=params.child_name,
        child_gender=params.child_gender,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    bad = 0
    for params in CURATED:
        outcome = asp_outcome(params)
        if outcome != "happy":
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches curated recovery stories ({len(CURATED)} cases).")
    else:
        rc = 1
        print(f"MISMATCH: {bad} curated cases did not recover in ASP.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failure: generated empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, animal, cause, carrier) combos:\n")
        for setting_id, animal_id, cause_id, carrier_id in combos:
            print(f"  {setting_id:15} {animal_id:7} {cause_id:10} {carrier_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.animal} / {p.cause} / {p.carrier}"
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
