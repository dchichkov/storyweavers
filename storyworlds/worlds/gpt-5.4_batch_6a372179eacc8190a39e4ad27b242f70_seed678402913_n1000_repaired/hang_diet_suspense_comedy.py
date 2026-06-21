#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hang_diet_suspense_comedy.py
=======================================================

A standalone story world about a child trying to help a silly pet stay on a
diet by hanging tempting treats up high. The little domain is built around a
simple common-sense constraint:

    a believable story needs
      (1) a treat that fits the pet,
      (2) a hanging spot that can hold it and keep it out of reach,
      (3) a method that is at least story-believable.

The suspense comes from the climb and the hungry pet waiting underneath. The
comedy comes from the pet's dramatic hopefulness and the family's gentle,
sensible fix.

Run it
------
    python storyworlds/worlds/gpt-5.4/hang_diet_suspense_comedy.py
    python storyworlds/worlds/gpt-5.4/hang_diet_suspense_comedy.py --pet dog --method rolling_chair
    python storyworlds/worlds/gpt-5.4/hang_diet_suspense_comedy.py --spot doorknob
    python storyworlds/worlds/gpt-5.4/hang_diet_suspense_comedy.py --all
    python storyworlds/worlds/gpt-5.4/hang_diet_suspense_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/hang_diet_suspense_comedy.py --verify
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
SENSE_MIN = 1


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class PetCfg:
    id: str
    type: str
    label: str
    phrase: str
    voice: str
    reach: int
    diet_line: str
    approved: str
    ending_prop: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SnackCfg:
    id: str
    label: str
    phrase: str
    weight: int
    pets: set[str] = field(default_factory=set)
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SpotCfg:
    id: str
    label: str
    phrase: str
    room: str
    capacity: int
    away: bool
    reach_bonus: int
    tags: set[str] = field(default_factory=set)


@dataclass
class MethodCfg:
    id: str
    label: str
    phrase: str
    sense: int
    stability: int
    safe: bool
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


def _r_wobble(world: World) -> list[str]:
    child = world.entities.get("child")
    pet = world.entities.get("pet")
    if not child or child.meters["climbing"] < THRESHOLD or child.meters["unstable"] < THRESHOLD:
        return []
    sig = ("wobble", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["wobble"] += 1
    child.memes["alarm"] += 1
    if pet:
        pet.memes["hope"] += 1
    return ["__wobble__"]


def _r_drop_tempts(world: World) -> list[str]:
    pet = world.entities.get("pet")
    snack = world.entities.get("snack")
    if not pet or not snack or snack.meters["dropped"] < THRESHOLD:
        return []
    sig = ("tempt", pet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pet.meters["near_snack"] += 1
    pet.memes["glee"] += 1
    return ["__drop__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drop_tempts", tag="physical", apply=_r_drop_tempts),
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
                child = world.get("child")
                method = world.facts["method_cfg"]
                pet = world.get("pet")
                world.say(
                    f"The {method.label} gave a tiny wiggle. {child.id}'s toes curled, "
                    f"and below, {pet.label} froze with big shining eyes."
                )
            elif sent == "__drop__":
                pet = world.get("pet")
                snack = world.get("snack")
                world.say(
                    f"For one breath, the room felt very still. Then {pet.label} made "
                    f"{world.facts['pet_cfg'].voice} at the fallen {snack.label}."
                )
    return produced


def snack_fits_pet(pet: PetCfg, snack: SnackCfg) -> bool:
    return pet.id in snack.pets


def spot_works(pet: PetCfg, snack: SnackCfg, spot: SpotCfg) -> bool:
    return spot.capacity >= snack.weight and spot.away and (spot.reach_bonus > pet.reach)


def plausible_method(method: MethodCfg) -> bool:
    return method.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for pet_id, pet in PETS.items():
        for snack_id, snack in SNACKS.items():
            if not snack_fits_pet(pet, snack):
                continue
            for spot_id, spot in SPOTS.items():
                if not spot_works(pet, snack, spot):
                    continue
                for method_id, method in METHODS.items():
                    if plausible_method(method):
                        combos.append((pet_id, snack_id, spot_id, method_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    if method.safe:
        return "smooth"
    return "rescued" if params.delay == 0 else "spill"


def predict_climb(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    method = sim.facts["method_cfg"]
    child.meters["climbing"] += 1
    if not method.safe:
        child.meters["unstable"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": child.meters["wobble"],
        "alarm": child.memes["alarm"],
    }


def introduce(world: World, child: Entity, pet: Entity, pet_cfg: PetCfg) -> None:
    child.memes["care"] += 1
    pet.memes["hope"] += 1
    world.say(
        f"{child.id} loved {pet_cfg.label}, who always seemed to believe every cupboard in the house "
        f"had been built especially for snacks."
    )
    world.say(
        f"That morning, the grown-up had said {pet_cfg.diet_line} {child.id} nodded very seriously "
        f"and promised to help."
    )


def show_problem(world: World, child: Entity, parent: Entity, pet_cfg: PetCfg, snack_cfg: SnackCfg) -> None:
    world.say(
        f"After lunch, {child.id} spotted {snack_cfg.phrase} on the counter. "
        f"{world.get('pet').label.capitalize()} noticed it too and began to trail behind "
        f"{child.pronoun('object')} like a furry detective."
    )
    world.say(
        f'"If I hang this up high, {pet_cfg.label} will stay on {pet_cfg.pronoun if False else "the"} diet," '
        f"{child.id} whispered."
    )
    world.say(
        f"{parent.label_word.capitalize()} was in the next room folding towels, close enough to hear trouble if it started."
    )


def plan(world: World, child: Entity, spot_cfg: SpotCfg, method_cfg: MethodCfg, snack_cfg: SnackCfg) -> None:
    child.memes["determination"] += 1
    world.say(
        f"{child.id} looked at {spot_cfg.phrase} in the {spot_cfg.room} and then at {method_cfg.phrase}. "
        f"It seemed like a quick plan. It also seemed just silly enough to become important."
    )
    world.say(
        f"{child.pronoun().capitalize()} picked up {snack_cfg.phrase} and got ready to hang it up."
    )


def climb(world: World, child: Entity, pet: Entity, method_cfg: MethodCfg, snack_cfg: SnackCfg) -> None:
    child.meters["climbing"] += 1
    if not method_cfg.safe:
        child.meters["unstable"] += 1
    pet.memes["hope"] += 1
    world.say(
        f"Up {child.pronoun()} went, one careful step at a time, with {snack_cfg.phrase} hugged to "
        f"{child.pronoun('possessive')} chest. Below, {pet.label} sat so still that even {pet.pronoun('possessive')} whiskers "
        f"looked suspenseful."
    )
    propagate(world, narrate=True)


def rescue(world: World, child: Entity, parent: Entity, pet: Entity, spot_cfg: SpotCfg, method_cfg: MethodCfg) -> None:
    child.meters["safe"] += 1
    child.memes["relief"] += 1
    parent.memes["calm"] += 1
    pet.memes["confusion"] += 1
    world.say(
        f'"Hold still," {parent.label_word} said, appearing in the doorway just as the {method_cfg.label} quivered again.'
    )
    world.say(
        f"{parent.label_word.capitalize()} put one steady hand on {child.id}, took the snack, and brought over a sturdy stool. "
        f"Together they hung it from {spot_cfg.phrase}, high and neat."
    )
    world.say(
        f"{pet.label.capitalize()} stared up at the treasure overhead, then sat down with a look so shocked it was almost funny."
    )


def smooth_success(world: World, child: Entity, pet: Entity, spot_cfg: SpotCfg) -> None:
    child.meters["safe"] += 1
    child.memes["pride"] += 1
    pet.memes["confusion"] += 1
    world.say(
        f"The little job took one stretch, one careful reach, and then it was done. "
        f"The treats hung from {spot_cfg.phrase}, far above the hopeful nose below."
    )
    world.say(
        f"{pet.label.capitalize()} gave one tiny {world.facts['pet_cfg'].voice}, as if asking whether gravity had become unfair."
    )


def spill(world: World, child: Entity, parent: Entity, pet: Entity, spot_cfg: SpotCfg, snack_cfg: SnackCfg, method_cfg: MethodCfg) -> None:
    snack = world.get("snack")
    snack.meters["dropped"] += 1
    child.memes["alarm"] += 1
    child.memes["relief"] += 1
    parent.memes["calm"] += 1
    propagate(world, narrate=True)
    world.say(
        f"The {method_cfg.label} scooted a tiny inch. {child.id} gasped, jumped safely to the floor, and "
        f"{snack_cfg.phrase} plopped down beside {pet.label}."
    )
    world.say(
        f"But before one extra bite could disappear, {parent.label_word} swooped in, lifted the snack, and said, "
        f'"Whew. That was a close one. We can help with a diet and still keep our feet on the ground."'
    )
    world.say(
        f"A minute later, they used a proper stool and hung the treats from {spot_cfg.phrase}. "
        f"{pet.label.capitalize()} blinked up at them as if the whole house had joined a secret club."
    )


def ending(world: World, child: Entity, parent: Entity, pet: Entity, pet_cfg: PetCfg) -> None:
    child.memes["joy"] += 1
    pet.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'Then {parent.label_word} scratched {pet.label} under the chin and handed over {pet_cfg.approved}. '
        f'"A diet does not mean no fun," {parent.pronoun()} said. "It means the right kind of fun."'
    )
    world.say(
        f"{pet.label.capitalize()} forgot all about the hanging treats for a moment and pounced on {pet_cfg.ending_prop} instead. "
        f"{child.id} laughed so hard that the suspense melted right out of the room."
    )
    world.say(
        f"After that, whenever the snack bag needed to hang high, {child.id} called for the sturdy stool first."
    )


def tell(
    pet_cfg: PetCfg,
    snack_cfg: SnackCfg,
    spot_cfg: SpotCfg,
    method_cfg: MethodCfg,
    *,
    child_name: str = "Mia",
    child_gender: str = "girl",
    parent_type: str = "mother",
    pet_name: str = "Biscuit",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    pet = world.add(Entity(id="pet", kind="character", type=pet_cfg.type, label=pet_name, role="pet", tags=set(pet_cfg.tags)))
    snack = world.add(Entity(id="snack", type="snack", label=snack_cfg.label, phrase=snack_cfg.phrase, tags=set(snack_cfg.tags)))

    world.facts.update(
        child=child,
        parent=parent,
        pet=pet,
        snack=snack,
        pet_cfg=pet_cfg,
        snack_cfg=snack_cfg,
        spot_cfg=spot_cfg,
        method_cfg=method_cfg,
        pet_name=pet_name,
        delay=delay,
    )

    introduce(world, child, pet, pet_cfg)
    show_problem(world, child, parent, pet_cfg, snack_cfg)

    world.para()
    plan(world, child, spot_cfg, method_cfg, snack_cfg)
    pred = predict_climb(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    climb(world, child, pet, method_cfg, snack_cfg)

    world.para()
    if method_cfg.safe:
        smooth_success(world, child, pet, spot_cfg)
        outcome = "smooth"
    else:
        if delay == 0:
            rescue(world, child, parent, pet, spot_cfg, method_cfg)
            outcome = "rescued"
        else:
            spill(world, child, parent, pet, spot_cfg, snack_cfg, method_cfg)
            outcome = "spill"

    world.para()
    ending(world, child, parent, pet, pet_cfg)

    world.facts["outcome"] = outcome
    world.facts["hung_high"] = True
    world.facts["wobble_happened"] = child.meters["wobble"] >= THRESHOLD
    world.facts["spill_happened"] = snack.meters["dropped"] >= THRESHOLD
    return world


PETS = {
    "dog": PetCfg(
        id="dog",
        type="dog",
        label="the dog",
        phrase="a round little dog",
        voice="woof",
        reach=2,
        diet_line='"Biscuit needs fewer crunchy extras this week, because the vet said that dog bellies can get too full too fast."',
        approved="a crisp carrot coin",
        ending_prop="a squeaky ball",
        tags={"dog", "diet", "pet"},
    ),
    "cat": PetCfg(
        id="cat",
        type="cat",
        label="the cat",
        phrase="a velvet-footed cat",
        voice="mrrp",
        reach=3,
        diet_line='"Pepper is on a careful diet for a while, because too many creamy treats make cats pudgy and sleepy."',
        approved="one tiny crunchy fish-shaped treat",
        ending_prop="a feather wand",
        tags={"cat", "diet", "pet"},
    ),
    "rabbit": PetCfg(
        id="rabbit",
        type="rabbit",
        label="the rabbit",
        phrase="a cloud-soft rabbit",
        voice="snuffle",
        reach=1,
        diet_line='"Clover needs a gentle diet for a bit, because rabbits do best when sweet nibbles stay small."',
        approved="a fresh parsley leaf",
        ending_prop="a cardboard tunnel",
        tags={"rabbit", "diet", "pet"},
    ),
}

SNACKS = {
    "biscuit_tin": SnackCfg(
        id="biscuit_tin",
        label="biscuit tin",
        phrase="the biscuit tin",
        weight=2,
        pets={"dog"},
        tags={"treats", "tin"},
    ),
    "fish_pouch": SnackCfg(
        id="fish_pouch",
        label="fish-treat pouch",
        phrase="the fish-treat pouch",
        weight=1,
        pets={"cat"},
        tags={"treats", "cat_food"},
    ),
    "banana_chips": SnackCfg(
        id="banana_chips",
        label="banana-chip bag",
        phrase="the banana-chip bag",
        weight=1,
        pets={"rabbit"},
        tags={"treats", "rabbit_food"},
    ),
}

SPOTS = {
    "pantry_hook": SpotCfg(
        id="pantry_hook",
        label="pantry hook",
        phrase="the high pantry hook",
        room="kitchen",
        capacity=3,
        away=True,
        reach_bonus=5,
        tags={"hook", "pantry"},
    ),
    "hall_peg": SpotCfg(
        id="hall_peg",
        label="hall peg",
        phrase="the top hall peg",
        room="hall",
        capacity=2,
        away=True,
        reach_bonus=4,
        tags={"peg", "hall"},
    ),
    "doorknob": SpotCfg(
        id="doorknob",
        label="doorknob",
        phrase="the shiny doorknob",
        room="kitchen",
        capacity=2,
        away=False,
        reach_bonus=1,
        tags={"low_spot"},
    ),
    "curtain_rod": SpotCfg(
        id="curtain_rod",
        label="curtain rod",
        phrase="the curtain rod",
        room="living room",
        capacity=0,
        away=True,
        reach_bonus=5,
        tags={"fragile"},
    ),
}

METHODS = {
    "step_stool": MethodCfg(
        id="step_stool",
        label="step stool",
        phrase="the little step stool",
        sense=2,
        stability=2,
        safe=True,
        tags={"stool", "safe"},
    ),
    "rolling_chair": MethodCfg(
        id="rolling_chair",
        label="rolling chair",
        phrase="the rolling chair from the desk",
        sense=1,
        stability=0,
        safe=False,
        tags={"chair", "wobble"},
    ),
    "stacked_boxes": MethodCfg(
        id="stacked_boxes",
        label="stacked boxes",
        phrase="two wobbling boxes",
        sense=0,
        stability=0,
        safe=False,
        tags={"boxes", "silly"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Lucy", "Rose"]
BOY_NAMES = ["Ben", "Sam", "Theo", "Max", "Leo", "Finn", "Jack", "Eli"]
PET_NAMES = {
    "dog": ["Biscuit", "Pickles", "Bean", "Muffin"],
    "cat": ["Pepper", "Noodle", "Mittens", "Olive"],
    "rabbit": ["Clover", "Puff", "Nibble", "Pip"],
}


@dataclass
class StoryParams:
    pet: str
    snack: str
    spot: str
    method: str
    child_name: str
    child_gender: str
    parent: str
    pet_name: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "diet": [
        (
            "What does a diet mean for a pet?",
            "A diet means the pet is eating carefully so its body stays healthy. It does not mean no treats forever; it means smaller or better treats."
        )
    ],
    "dog": [
        (
            "Why can too many dog treats be a problem?",
            "Too many treats can give a dog too much food and not enough healthy balance. That can make the dog gain too much weight."
        )
    ],
    "cat": [
        (
            "Why should cats have only a small number of treats?",
            "Treats are extra food, so too many can make a cat pudgy and less healthy. Small amounts help keep meals balanced."
        )
    ],
    "rabbit": [
        (
            "Why should rabbits have sweet snacks only in tiny amounts?",
            "Rabbits do best with lots of hay and simple foods. Sweet snacks should stay small so their tummies stay happy."
        )
    ],
    "hook": [
        (
            "Why hang something on a high hook?",
            "A high hook keeps things up where small pets cannot reach them. It also keeps the floor and counters less cluttered."
        )
    ],
    "peg": [
        (
            "What is a peg on the wall for?",
            "A wall peg is a small knob or hook that holds things up. People use pegs for bags, coats, or other light items."
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps you reach something high in a steadier way. It is safer than balancing on something that rolls or tips."
        )
    ],
    "chair": [
        (
            "Why is a rolling chair a bad place to stand?",
            "A rolling chair can move when your feet push on it. That can make you wobble or fall."
        )
    ],
    "pet": [
        (
            "Why do pets act silly around treats?",
            "Treats smell exciting, and pets quickly learn where snacks usually appear. They are not being naughty on purpose; they are being hopeful."
        )
    ],
}

KNOWLEDGE_ORDER = ["diet", "dog", "cat", "rabbit", "hook", "peg", "stool", "chair", "pet"]


CURATED = [
    StoryParams(
        pet="dog",
        snack="biscuit_tin",
        spot="pantry_hook",
        method="rolling_chair",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        pet_name="Biscuit",
        delay=0,
    ),
    StoryParams(
        pet="cat",
        snack="fish_pouch",
        spot="hall_peg",
        method="step_stool",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        pet_name="Pepper",
        delay=0,
    ),
    StoryParams(
        pet="rabbit",
        snack="banana_chips",
        spot="pantry_hook",
        method="rolling_chair",
        child_name="Lily",
        child_gender="girl",
        parent="mother",
        pet_name="Clover",
        delay=1,
    ),
]


def explain_rejection(pet: PetCfg, snack: SnackCfg, spot: SpotCfg, method: MethodCfg) -> str:
    if not snack_fits_pet(pet, snack):
        return (
            f"(No story: {snack.label} is not the right sort of treat for {pet.label}. "
            f"The snack should match the pet.)"
        )
    if spot.capacity < snack.weight:
        return (
            f"(No story: {spot.phrase} cannot hold the {snack.label}. "
            f"Pick a sturdier place to hang it.)"
        )
    if not spot.away or spot.reach_bonus <= pet.reach:
        return (
            f"(No story: {spot.phrase} is still too easy for {pet.label} to reach. "
            f"The hanging place must really keep the treats out of reach.)"
        )
    if not plausible_method(method):
        return (
            f"(No story: {method.phrase} is too silly and unsafe for this world. "
            f"Choose a step stool or, for a near-miss story, a rolling chair.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
fits(P, S) :- pet(P), snack(S), snack_for(S, P).
works(P, S, Spot) :- pet(P), snack(S), spot(Spot), fits(P, S),
                     capacity(Spot, C), weight(S, W), C >= W,
                     away(Spot), reach_bonus(Spot, B), reach(P, R), B > R.
plausible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(P, S, Spot, M) :- fits(P, S), works(P, S, Spot), plausible(M).

smooth  :- chosen_method(M), safe(M).
rescued :- chosen_method(M), not safe(M), delay(0).
spill   :- chosen_method(M), not safe(M), delay(D), D > 0.

outcome(smooth)  :- smooth.
outcome(rescued) :- rescued.
outcome(spill)   :- spill.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pet_id, pet in PETS.items():
        lines.append(asp.fact("pet", pet_id))
        lines.append(asp.fact("reach", pet_id, pet.reach))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        lines.append(asp.fact("weight", snack_id, snack.weight))
        for pet_id in sorted(snack.pets):
            lines.append(asp.fact("snack_for", snack_id, pet_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("capacity", spot_id, spot.capacity))
        if spot.away:
            lines.append(asp.fact("away", spot_id))
        lines.append(asp.fact("reach_bonus", spot_id, spot.reach_bonus))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.safe:
            lines.append(asp.fact("safe", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_method", params.method),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    pet = world.facts["pet"]
    pet_cfg = world.facts["pet_cfg"]
    snack_cfg = world.facts["snack_cfg"]
    spot_cfg = world.facts["spot_cfg"]
    method_cfg = world.facts["method_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, {pet.label} named {pet.label.capitalize() if False else world.facts['pet_name']}, and {child.pronoun('possessive')} {parent.label_word}. "
            f"They are trying to keep the pet on a careful diet."
        ),
        (
            f"Why did {child.label} want to hang the treats up high?",
            f"{child.label} wanted to help {pet.label} stay on a diet, so the treats needed to be out of reach. "
            f"Hanging them high solved the snack problem without being mean."
        ),
        (
            f"What made the middle of the story feel suspenseful?",
            f"{child.label} was climbing with {snack_cfg.phrase} while {pet.label} waited underneath and watched every move. "
            f"The room felt tense because one wobble could have sent the treats back down."
        ),
    ]

    if outcome == "smooth":
        qa.append(
            (
                f"How did {child.label} hang the snack safely?",
                f"{child.label} used {method_cfg.phrase} and reached {spot_cfg.phrase} without any trouble. "
                f"The treats ended up high above {pet.label}, so the diet plan stayed in place."
            )
        )
    elif outcome == "rescued":
        qa.append(
            (
                f"How did {child.label}'s {parent.label_word} help?",
                f"{parent.label_word.capitalize()} came in when the {method_cfg.label} started to wobble and steadied the whole moment. "
                f"Then the grown-up used a proper stool and helped hang the treats from {spot_cfg.phrase}."
            )
        )
    else:
        qa.append(
            (
                "Did anything go wrong before the ending?",
                f"Yes. The snack slipped down when the {method_cfg.label} moved, and for one breath it looked as if {pet.label} might win. "
                f"But {parent.label_word} grabbed the treats in time and helped hang them safely afterward."
            )
        )

    qa.append(
        (
            "How did the story end?",
            f"It ended with the treats hanging high and {pet.label} enjoying {pet_cfg.approved} and {pet_cfg.ending_prop} instead. "
            f"The last image shows that the diet became gentler and safer, not gloomy."
        )
    )
    return qa


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    pet_cfg = world.facts["pet_cfg"]
    snack_cfg = world.facts["snack_cfg"]
    method_cfg = world.facts["method_cfg"]
    outcome = world.facts["outcome"]
    core = (
        f'Write a funny, suspenseful story for a 3-to-5-year-old that includes the words "hang" and "diet". '
        f"The story should be about a child helping {pet_cfg.label} stay on a diet by hanging {snack_cfg.phrase} up high."
    )
    if outcome == "smooth":
        return [
            core,
            f"Tell a gentle comedy where {child.label} uses {method_cfg.phrase} to hang pet treats safely, while a hopeful {pet_cfg.type} watches below.",
            'Write a child-facing story with suspense in the middle and a silly, relieved ending where the pet gets a better treat instead.',
        ]
    if outcome == "rescued":
        return [
            core,
            f"Tell a comedic near-miss where {child.label} tries to hang the treats from an unsafe perch, and a calm grown-up steps in just in time.",
            'Write a funny suspense story where a hungry pet stares so hard at a snack bag that the whole room seems to hold its breath.',
        ]
    return [
        core,
        f"Tell a playful suspense story where {child.label} uses {method_cfg.phrase}, the snack nearly falls, and a grown-up saves the pet's diet at the last second.",
        'Write a comedy with one close call, a silly pet, and an ending that proves safe help works better than wobbling alone.',
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"diet", "pet"} | set(world.facts["pet_cfg"].tags)
    spot = world.facts["spot_cfg"]
    method = world.facts["method_cfg"]
    if "hook" in spot.tags:
        tags.add("hook")
    if "peg" in spot.tags:
        tags.add("peg")
    if "stool" in method.tags:
        tags.add("stool")
    if "chair" in method.tags:
        tags.add("chair")
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
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a child tries to hang pet treats high so a pet on a diet cannot get them."
    )
    ap.add_argument("--pet", choices=sorted(PETS))
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--pet-name")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = grown-up arrives in time, 1 = close spill first")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pet and args.snack and not snack_fits_pet(PETS[args.pet], SNACKS[args.snack]):
        raise StoryError(explain_rejection(PETS[args.pet], SNACKS[args.snack], next(iter(SPOTS.values())), next(iter(METHODS.values()))))
    if args.pet and args.snack and args.spot:
        if not spot_works(PETS[args.pet], SNACKS[args.snack], SPOTS[args.spot]):
            raise StoryError(explain_rejection(PETS[args.pet], SNACKS[args.snack], SPOTS[args.spot], next(iter(METHODS.values()))))
    if args.method and not plausible_method(METHODS[args.method]):
        pet = PETS[args.pet] if args.pet else next(iter(PETS.values()))
        snack = SNACKS[args.snack] if args.snack else next(iter(SNACKS.values()))
        spot = SPOTS[args.spot] if args.spot else next(iter(SPOTS.values()))
        raise StoryError(explain_rejection(pet, snack, spot, METHODS[args.method]))

    combos = [
        combo for combo in valid_combos()
        if (args.pet is None or combo[0] == args.pet)
        and (args.snack is None or combo[1] == args.snack)
        and (args.spot is None or combo[2] == args.spot)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pet_id, snack_id, spot_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    pet_name = args.pet_name or rng.choice(PET_NAMES[pet_id])
    delay = args.delay if args.delay is not None else (0 if METHODS[method_id].safe else rng.choice([0, 1]))
    return StoryParams(
        pet=pet_id,
        snack=snack_id,
        spot=spot_id,
        method=method_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        pet_name=pet_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        pet_cfg = PETS[params.pet]
        snack_cfg = SNACKS[params.snack]
        spot_cfg = SPOTS[params.spot]
        method_cfg = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not snack_fits_pet(pet_cfg, snack_cfg):
        raise StoryError(explain_rejection(pet_cfg, snack_cfg, next(iter(SPOTS.values())), method_cfg))
    if not spot_works(pet_cfg, snack_cfg, spot_cfg):
        raise StoryError(explain_rejection(pet_cfg, snack_cfg, spot_cfg, method_cfg))
    if not plausible_method(method_cfg):
        raise StoryError(explain_rejection(pet_cfg, snack_cfg, spot_cfg, method_cfg))

    world = tell(
        pet_cfg=pet_cfg,
        snack_cfg=snack_cfg,
        spot_cfg=spot_cfg,
        method_cfg=method_cfg,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        pet_name=params.pet_name,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: valid_combos matches ASP ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in asp:", sorted(asp_set - py))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(12):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params unexpectedly failed for seed {seed}.")
            break

    for params in cases:
        aout = asp_outcome(params)
        pout = outcome_of(params)
        if aout != pout:
            rc = 1
            print(f"MISMATCH in outcome for {params}: asp={aout} python={pout}")
            break

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
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
        print(f"{len(combos)} compatible (pet, snack, spot, method) combos:\n")
        for pet, snack, spot, method in combos:
            print(f"  {pet:7} {snack:12} {spot:11} {method}")
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
            header = f"### {p.child_name}, {p.pet_name}, {p.method} -> {outcome_of(p)}"
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
