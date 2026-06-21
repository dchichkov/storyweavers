#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/juvenile_grow_pulley_transformation_comedy.py
========================================================================

A standalone story world for a small comedy about a child, a "juvenile" garden
thing, a bottle that makes it grow, and a pulley used to solve the silly mess.

Premise
-------
A child is preparing for a backyard show-and-tell. The star item is a very small
garden thing -- often described as juvenile because it is still young. The child
adds a little too much grow tonic, the thing transforms into something much
bigger, and suddenly it cannot simply be carried to the table. A handy grown-up
and a pulley help hoist it into a cart or wheelbarrow. The ending image proves
that the child has gone from panicked to proud, and the whole episode stays
comic rather than scary.

Coverage rule
-------------
Not every transformed thing can be moved with every pulley rig and carrier. A
reasonable story needs:
- a pulley strong enough for the grown result
- a carrier strong enough too
- a carrier shape that suits the grown thing

That gate is enforced both in Python and with an inline ASP twin.

Run it
------
python storyworlds/worlds/gpt-5.4/juvenile_grow_pulley_transformation_comedy.py
python storyworlds/worlds/gpt-5.4/juvenile_grow_pulley_transformation_comedy.py --all
python storyworlds/worlds/gpt-5.4/juvenile_grow_pulley_transformation_comedy.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/juvenile_grow_pulley_transformation_comedy.py --qa
python storyworlds/worlds/gpt-5.4/juvenile_grow_pulley_transformation_comedy.py --json
python storyworlds/worlds/gpt-5.4/juvenile_grow_pulley_transformation_comedy.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    owner: Optional[str] = None
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Growable:
    id: str
    label: str
    juvenile_phrase: str
    grown_phrase: str
    shape: str
    mild_weight: int
    giant_weight: int
    transform_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rig:
    id: str
    label: str
    anchor: str
    capacity: int
    setup_text: str
    lift_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    capacity: int
    shapes: set[str] = field(default_factory=set)
    roll_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Dose:
    id: str
    label: str
    growth: int
    spill_text: str
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


def weight_for(world: World) -> int:
    return int(world.facts.get("weight", 0))


def _r_too_big(world: World) -> list[str]:
    produce: list[str] = []
    plant = world.get("plant")
    if plant.meters["grown"] < THRESHOLD:
        return produce
    sig = ("too_big", plant.id)
    if sig in world.fired:
        return produce
    world.fired.add(sig)
    if weight_for(world) >= 2:
        plant.meters["too_big"] += 1
        world.get("kid").memes["panic"] += 1
        world.get("helper").memes["amusement"] += 1
        produce.append("__too_big__")
    return produce


def _r_loaded(world: World) -> list[str]:
    plant = world.get("plant")
    carrier = world.get("carrier")
    if plant.meters["lifted"] < THRESHOLD or carrier.meters["ready"] < THRESHOLD:
        return []
    sig = ("loaded", plant.id, carrier.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["loaded"] += 1
    world.get("kid").memes["relief"] += 1
    world.get("kid").memes["pride"] += 1
    return ["__loaded__"]


CAUSAL_RULES = [
    Rule(name="too_big", tag="physical", apply=_r_too_big),
    Rule(name="loaded", tag="physical", apply=_r_loaded),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


GROWABLES = {
    "pumpkin": Growable(
        id="pumpkin",
        label="pumpkin",
        juvenile_phrase="a juvenile pumpkin no bigger than a soup bowl",
        grown_phrase="a plump giant pumpkin with a silly orange grin of a stem",
        shape="round",
        mild_weight=2,
        giant_weight=3,
        transform_text="The little pumpkin puffed, rounded, and swelled until it looked like it had swallowed three sunsets.",
        ending_image="The pumpkin rode past like a grand orange parade float.",
        tags={"pumpkin", "garden", "transformation"},
    ),
    "beanstalk": Growable(
        id="beanstalk",
        label="beanstalk",
        juvenile_phrase="a juvenile bean plant with two hopeful leaves",
        grown_phrase="a curly green beanstalk with loops like springy ribbons",
        shape="tall",
        mild_weight=1,
        giant_weight=2,
        transform_text="The tiny bean plant shot upward in a green corkscrew, as if it had remembered a very important appointment with the sky.",
        ending_image="The beanstalk nodded over the cart like a green flag in a parade.",
        tags={"beans", "garden", "transformation"},
    ),
    "melon": Growable(
        id="melon",
        label="melon",
        juvenile_phrase="a juvenile melon striped like a green marble",
        grown_phrase="a giant melon round enough to deserve its own seat",
        shape="round",
        mild_weight=2,
        giant_weight=3,
        transform_text="The melon bulged wider and wider until it looked ready to roll off with a mind of its own.",
        ending_image="The melon rolled along like a proud green moon in daylight.",
        tags={"melon", "garden", "transformation"},
    ),
}

RIGS = {
    "laundry": Rig(
        id="laundry",
        label="laundry-line pulley",
        anchor="the backyard laundry post",
        capacity=1,
        setup_text="A little laundry-line pulley hung from the backyard post, good for socks and very hopeful plans.",
        lift_text="threaded the rope through the laundry-line pulley and tugged with careful little huffs",
        tags={"pulley"},
    ),
    "porch": Rig(
        id="porch",
        label="porch-beam pulley",
        anchor="the porch beam",
        capacity=2,
        setup_text="A porch-beam pulley was already tied up from last autumn's leaf bags.",
        lift_text="looped the rope over the porch-beam pulley and pulled hand over hand",
        tags={"pulley"},
    ),
    "oak": Rig(
        id="oak",
        label="oak-branch pulley",
        anchor="the low oak branch",
        capacity=3,
        setup_text="From the low oak branch hung the sturdiest pulley in the yard, the one usually trusted with picnic baskets.",
        lift_text="ran the rope through the oak-branch pulley and leaned back with a big steady pull",
        tags={"pulley"},
    ),
}

CARRIERS = {
    "basket": Carrier(
        id="basket",
        label="basket",
        phrase="a wicker basket",
        capacity=1,
        shapes={"round"},
        roll_text="The basket bumped over the grass in tiny brave hops.",
        tags={"carrier", "basket"},
    ),
    "wheelbarrow": Carrier(
        id="wheelbarrow",
        label="wheelbarrow",
        phrase="a squeaky wheelbarrow",
        capacity=2,
        shapes={"round", "tall"},
        roll_text="The wheelbarrow squeaked toward the table like it was telling jokes to itself.",
        tags={"carrier", "wheelbarrow"},
    ),
    "garden_cart": Carrier(
        id="garden_cart",
        label="garden cart",
        phrase="a red garden cart",
        capacity=3,
        shapes={"round", "tall"},
        roll_text="The red cart rolled grandly over the path, looking almost too pleased with its job.",
        tags={"carrier", "cart"},
    ),
}

DOSES = {
    "sip": Dose(
        id="sip",
        label="one careful sip of grow tonic",
        growth=1,
        spill_text="Only a neat little sip splashed onto the soil.",
        tags={"grow"},
    ),
    "glug": Dose(
        id="glug",
        label="one comic glug of grow tonic",
        growth=2,
        spill_text="The bottle gave a rude glug, and far more tonic splashed out than anyone had planned.",
        tags={"grow"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Poppy", "Nell", "June", "Tess", "Ruby", "Mabel"]
BOY_NAMES = ["Ollie", "Milo", "Benny", "Ned", "Toby", "Jasper", "Finn", "Lou"]
TRAITS = ["eager", "bouncy", "curious", "hopeful", "chatty", "dramatic"]


def grown_weight(growable: Growable, dose: Dose) -> int:
    return growable.mild_weight if dose.growth == 1 else growable.giant_weight


def valid_combo(growable: Growable, rig: Rig, carrier: Carrier, dose: Dose) -> bool:
    weight = grown_weight(growable, dose)
    return (
        rig.capacity >= weight
        and carrier.capacity >= weight
        and growable.shape in carrier.shapes
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for gid, growable in GROWABLES.items():
        for rid, rig in RIGS.items():
            for cid, carrier in CARRIERS.items():
                for did, dose in DOSES.items():
                    if valid_combo(growable, rig, carrier, dose):
                        combos.append((gid, rid, cid, did))
    return sorted(combos)


@dataclass
class StoryParams:
    growable: str
    rig: str
    carrier: str
    dose: str
    kid_name: str
    kid_gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        growable="pumpkin",
        rig="oak",
        carrier="garden_cart",
        dose="glug",
        kid_name="Poppy",
        kid_gender="girl",
        helper_type="aunt",
        trait="dramatic",
        seed=None,
    ),
    StoryParams(
        growable="beanstalk",
        rig="porch",
        carrier="wheelbarrow",
        dose="sip",
        kid_name="Milo",
        kid_gender="boy",
        helper_type="father",
        trait="curious",
        seed=None,
    ),
    StoryParams(
        growable="melon",
        rig="oak",
        carrier="garden_cart",
        dose="glug",
        kid_name="Nell",
        kid_gender="girl",
        helper_type="uncle",
        trait="hopeful",
        seed=None,
    ),
    StoryParams(
        growable="beanstalk",
        rig="laundry",
        carrier="basket",
        dose="sip",
        kid_name="Ollie",
        kid_gender="boy",
        helper_type="mother",
        trait="chatty",
        seed=None,
    ),
    StoryParams(
        growable="pumpkin",
        rig="porch",
        carrier="wheelbarrow",
        dose="sip",
        kid_name="June",
        kid_gender="girl",
        helper_type="father",
        trait="eager",
        seed=None,
    ),
]


def outcome_of(params: StoryParams) -> str:
    growable = GROWABLES[params.growable]
    rig = RIGS[params.rig]
    carrier = CARRIERS[params.carrier]
    dose = DOSES[params.dose]
    weight = grown_weight(growable, dose)
    if rig.capacity == weight or carrier.capacity == weight:
        return "wobble"
    return "smooth"


def explain_rejection(growable: Growable, rig: Rig, carrier: Carrier, dose: Dose) -> str:
    weight = grown_weight(growable, dose)
    if rig.capacity < weight:
        return (
            f"(No story: {rig.label} can only handle {rig.capacity}, but a grown "
            f"{growable.label} after {dose.label} weighs about {weight}. "
            f"Pick a stronger pulley rig.)"
        )
    if carrier.capacity < weight:
        return (
            f"(No story: {carrier.label} cannot carry a grown {growable.label} "
            f"after {dose.label}. Pick a stronger carrier.)"
        )
    if growable.shape not in carrier.shapes:
        return (
            f"(No story: {carrier.label} is a poor shape match for a {growable.shape} "
            f"{growable.label}. Pick a carrier that fits the transformed shape.)"
        )
    return "(No story: that combination is not reasonable.)"


def introduce(world: World, kid: Entity, helper: Entity, growable: Growable, rig: Rig) -> None:
    kid.memes["joy"] += 1
    world.say(
        f"On the morning of the backyard show-and-tell, {kid.id} hurried outside with "
        f"{growable.juvenile_phrase} in a flowerpot. {kid.pronoun('possessive').capitalize()} plan was to win the silliest ribbon in the neighborhood."
    )
    world.say(
        f"{kid.id} kept calling it a juvenile {growable.label}, which made {helper.label_word} smile every time. {rig.setup_text}"
    )


def admire(world: World, kid: Entity, growable: Growable) -> None:
    world.say(
        f'"If this little {growable.label} would only grow a bit," {kid.id} said, '
        f'"it could sit right in the middle of the table and look important."'
    )


def spill_tonic(world: World, kid: Entity, helper: Entity, dose: Dose) -> None:
    kid.memes["hope"] += 1
    world.say(
        f"{kid.id} uncorked the bottle of grow tonic. {dose.spill_text}"
    )
    world.say(
        f'{helper.label_word.capitalize()} lifted one eyebrow. "That was meant for one polite leaf," {helper.pronoun()} said.'
    )


def transform(world: World, kid: Entity, growable: Growable, dose: Dose) -> None:
    plant = world.get("plant")
    weight = grown_weight(growable, dose)
    world.facts["weight"] = weight
    plant.meters["grown"] += dose.growth
    plant.meters["weight"] = float(weight)
    kid.memes["shock"] += 1
    world.say(growable.transform_text)
    world.say(
        f"In one blink, the pot held {growable.grown_phrase}."
    )
    propagate(world, narrate=False)
    if plant.meters["too_big"] >= THRESHOLD:
        world.say(
            f"{kid.id} tried to hug the pot, then tried to lift it, then made the face of somebody discovering that surprise muscles do not exist."
        )


def call_for_help(world: World, kid: Entity, helper: Entity, rig: Rig, carrier: Carrier) -> None:
    kid.memes["trust"] += 1
    carrier_ent = world.get("carrier")
    carrier_ent.meters["ready"] += 1
    world.say(
        f'"It grew too much!" {kid.id} squeaked. "{helper.label_word.capitalize()}, I need the pulley!"'
    )
    world.say(
        f'{helper.label_word.capitalize()} nodded, rolled out {carrier.phrase}, and pointed up at {rig.anchor}. "Good thing the yard came with ideas," {helper.pronoun()} said.'
    )


def hoist(world: World, kid: Entity, helper: Entity, rig: Rig, carrier: Carrier, outcome: str) -> None:
    plant = world.get("plant")
    plant.meters["lifted"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Together they {rig.lift_text}, while the giant {plant.label} rose as slowly as a sleepy moon."
    )
    if outcome == "wobble":
        kid.memes["panic"] += 1
        world.say(
            f"For one funny second it wobbled over the {carrier.label}, and both of them leaned the wrong way at once. The pulley squeaked, the cart squeaked back, and then everything settled with a plop."
        )
    else:
        world.say(
            f"The rope stayed snug, the pulley hummed, and the landing was neat enough to make even the ants stop and watch."
        )
    propagate(world, narrate=False)


def celebrate(world: World, kid: Entity, helper: Entity, carrier: Carrier, growable: Growable, outcome: str) -> None:
    kid.memes["joy"] += 1
    kid.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(
        carrier.roll_text
    )
    if outcome == "wobble":
        world.say(
            f"At the table, everyone laughed when {kid.id} bowed as if wobbling giant vegetables were part of the act all along."
        )
    else:
        world.say(
            f"At the table, {kid.id} stood tall beside it and tried not to grin too hard, which did not work at all."
        )
    world.say(
        f'{helper.label_word.capitalize()} tucked the rope away and whispered, "Next time, we measure the tonic first." {kid.id} giggled and whispered back, "Maybe."'
    )
    world.say(
        growable.ending_image
    )


def tell(
    growable: Growable,
    rig: Rig,
    carrier: Carrier,
    dose: Dose,
    kid_name: str = "Poppy",
    kid_gender: str = "girl",
    helper_type: str = "aunt",
    trait: str = "eager",
) -> World:
    world = World()
    kid = world.add(
        Entity(
            id=kid_name,
            kind="character",
            type=kid_gender,
            label=kid_name,
            role="kid",
            attrs={"trait": trait},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
        )
    )
    plant = world.add(
        Entity(
            id="plant",
            kind="thing",
            type="plant",
            label=growable.label,
            phrase=growable.juvenile_phrase,
            tags=set(growable.tags),
        )
    )
    world.add(
        Entity(
            id="rig",
            kind="thing",
            type="rig",
            label=rig.label,
            tags=set(rig.tags),
        )
    )
    world.add(
        Entity(
            id="carrier",
            kind="thing",
            type="carrier",
            label=carrier.label,
            phrase=carrier.phrase,
            tags=set(carrier.tags),
        )
    )

    introduce(world, kid, helper, growable, rig)
    admire(world, kid, growable)

    world.para()
    spill_tonic(world, kid, helper, dose)
    transform(world, kid, growable, dose)

    world.para()
    call_for_help(world, kid, helper, rig, carrier)
    outcome = "wobble" if (rig.capacity == grown_weight(growable, dose) or carrier.capacity == grown_weight(growable, dose)) else "smooth"
    hoist(world, kid, helper, rig, carrier, outcome)

    world.para()
    celebrate(world, kid, helper, carrier, growable, outcome)

    world.facts.update(
        kid=kid,
        helper=helper,
        growable=growable,
        rig_cfg=rig,
        carrier_cfg=carrier,
        dose_cfg=dose,
        outcome=outcome,
        weight=grown_weight(growable, dose),
        transformed=plant.meters["grown"] >= THRESHOLD,
        loaded=plant.meters["loaded"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "juvenile": [
        (
            "What does juvenile mean?",
            "Juvenile means young and not fully grown yet. A juvenile plant or animal is still in its early stage."
        )
    ],
    "grow": [
        (
            "What does grow mean?",
            "Grow means to get bigger over time. Plants grow by taking in water, light, and food from the soil."
        )
    ],
    "pulley": [
        (
            "What is a pulley?",
            "A pulley is a wheel with a rope that helps lift things. It makes pulling easier by changing the direction of the force."
        )
    ],
    "transformation": [
        (
            "What is a transformation?",
            "A transformation is a big change from one form into another. In stories, it often turns something small or ordinary into something surprising."
        )
    ],
    "pumpkin": [
        (
            "Why are pumpkins heavy?",
            "Pumpkins hold a lot of thick flesh and water inside. That is why even one pumpkin can feel surprisingly heavy."
        )
    ],
    "beans": [
        (
            "Why do bean plants climb?",
            "Bean plants climb so their leaves can reach more sunlight. Their stems like to curl around supports as they grow."
        )
    ],
    "melon": [
        (
            "Why can a melon roll away?",
            "A melon is round and smooth, so it can roll if it is on a slope. That shape makes it funny in stories and tricky in real life."
        )
    ],
    "wheelbarrow": [
        (
            "What is a wheelbarrow for?",
            "A wheelbarrow helps carry heavy things in a yard or garden. Its wheel lets one person move a load more easily."
        )
    ],
    "cart": [
        (
            "What is a garden cart?",
            "A garden cart is a strong little wagon used to carry tools, soil, or heavy plants. It can hold more weight than a small basket."
        )
    ],
    "basket": [
        (
            "What is a basket good for?",
            "A basket is good for carrying light things like flowers or snacks. It is not the best choice for very heavy loads."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "juvenile",
    "grow",
    "pulley",
    "transformation",
    "pumpkin",
    "beans",
    "melon",
    "basket",
    "wheelbarrow",
    "cart",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    growable = f["growable"]
    outcome = f["outcome"]
    rig = f["rig_cfg"]
    return [
        f'Write a funny transformation story for a 3-to-5-year-old that includes the words "juvenile", "grow", and "pulley".',
        f"Tell a backyard comedy where {kid.id} uses grow tonic on a juvenile {growable.label}, it becomes far too big, and a {rig.label} helps save the day.",
        f"Write a short story where a child's proud little garden plan turns into a bigger and sillier problem, then ends with a {outcome} pulley rescue and a happy laugh.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    growable = f["growable"]
    rig = f["rig_cfg"]
    carrier = f["carrier_cfg"]
    dose = f["dose_cfg"]
    weight = f["weight"]
    outcome = f["outcome"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid.id}, a child with a funny garden plan, and {kid.pronoun('possessive')} {helper_word} who helps when the plan gets too big."
        ),
        (
            f"What was in the flowerpot at the start?",
            f"There was {growable.juvenile_phrase} in the pot. It started very small, which is why the later transformation felt so surprising."
        ),
        (
            f"Why did {kid.id} use the grow tonic?",
            f"{kid.id} wanted the little {growable.label} to grow enough for the backyard show-and-tell table. {kid.pronoun('possessive').capitalize()} idea was proud and hopeful, not mean or careless."
        ),
        (
            "What changed after the tonic splashed out?",
            f"The tiny {growable.label} transformed into {growable.grown_phrase}. That sudden change made it too heavy to carry by hand."
        ),
        (
            "Why did they need the pulley?",
            f"They needed the pulley because the grown {growable.label} weighed about {weight} and was too awkward to lift safely. The pulley let them hoist it into the {carrier.label} without dropping it."
        ),
    ]
    if outcome == "wobble":
        qa.append(
            (
                "Did the rescue go perfectly?",
                f"Not quite. It wobbled for a funny second over the {carrier.label}, but the rope held and the giant {growable.label} landed safely anyway."
            )
        )
    else:
        qa.append(
            (
                "How did the rescue work?",
                f"{helper_word.capitalize()} and {kid.id} used the {rig.label} carefully, and the landing was smooth. The pulley turned a too-heavy problem into a manageable one."
            )
        )
    qa.append(
        (
            f"How did {kid.id} feel at the end?",
            f"{kid.id} felt relieved first and proud after that. The ending shows the change clearly, because {kid.pronoun()} stands beside the giant {growable.label} laughing instead of panicking."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"juvenile", "grow", "pulley", "transformation"}
    growable = world.facts["growable"]
    tags |= set(growable.tags)
    carrier = world.facts["carrier_cfg"]
    tags |= set(carrier.tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
weight(G, D, W) :- growable(G), dose(D), mild_weight(G, W), growth(D, 1).
weight(G, D, W) :- growable(G), dose(D), giant_weight(G, W), growth(D, 2).

fits_shape(G, C) :- growable(G), carrier(C), shape(G, S), carrier_shape(C, S).
strong_rig(G, R, D) :- rig(R), weight(G, D, W), rig_capacity(R, Cap), Cap >= W.
strong_carrier(G, C, D) :- carrier(C), weight(G, D, W), carrier_capacity(C, Cap), Cap >= W.

valid(G, R, C, D) :- growable(G), rig(R), carrier(C), dose(D),
                     strong_rig(G, R, D), strong_carrier(G, C, D), fits_shape(G, C).

outcome(G, R, C, D, wobble) :- valid(G, R, C, D), weight(G, D, W),
                               rig_capacity(R, W).
outcome(G, R, C, D, wobble) :- valid(G, R, C, D), weight(G, D, W),
                               carrier_capacity(C, W).
outcome(G, R, C, D, smooth) :- valid(G, R, C, D),
                               not outcome(G, R, C, D, wobble).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid, growable in GROWABLES.items():
        lines.append(asp.fact("growable", gid))
        lines.append(asp.fact("shape", gid, growable.shape))
        lines.append(asp.fact("mild_weight", gid, growable.mild_weight))
        lines.append(asp.fact("giant_weight", gid, growable.giant_weight))
    for rid, rig in RIGS.items():
        lines.append(asp.fact("rig", rid))
        lines.append(asp.fact("rig_capacity", rid, rig.capacity))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("carrier_capacity", cid, carrier.capacity))
        for shape in sorted(carrier.shapes):
            lines.append(asp.fact("carrier_shape", cid, shape))
    for did, dose in DOSES.items():
        lines.append(asp.fact("dose", did))
        lines.append(asp.fact("growth", did, dose.growth))
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
            asp.fact("chosen_growable", params.growable),
            asp.fact("chosen_rig", params.rig),
            asp.fact("chosen_carrier", params.carrier),
            asp.fact("chosen_dose", params.dose),
            "picked_outcome(X) :- outcome(G,R,C,D,X), chosen_growable(G), chosen_rig(R), chosen_carrier(C), chosen_dose(D).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    outs = asp.atoms(model, "picked_outcome")
    return outs[0][0] if outs else "?"


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

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp_out = asp_outcome(params)
        if py != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        with redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generation/emit passed.")
    except Exception as err:  # pragma: no cover - defensive verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a juvenile garden thing, grow tonic, and a pulley rescue."
    )
    ap.add_argument("--growable", choices=GROWABLES)
    ap.add_argument("--rig", choices=RIGS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--dose", choices=DOSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
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
    if args.growable and args.rig and args.carrier and args.dose:
        growable = GROWABLES[args.growable]
        rig = RIGS[args.rig]
        carrier = CARRIERS[args.carrier]
        dose = DOSES[args.dose]
        if not valid_combo(growable, rig, carrier, dose):
            raise StoryError(explain_rejection(growable, rig, carrier, dose))

    combos = [
        combo
        for combo in valid_combos()
        if (args.growable is None or combo[0] == args.growable)
        and (args.rig is None or combo[1] == args.rig)
        and (args.carrier is None or combo[2] == args.carrier)
        and (args.dose is None or combo[3] == args.dose)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    growable_id, rig_id, carrier_id, dose_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    helper_type = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        growable=growable_id,
        rig=rig_id,
        carrier=carrier_id,
        dose=dose_id,
        kid_name=name,
        kid_gender=gender,
        helper_type=helper_type,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        growable = GROWABLES[params.growable]
        rig = RIGS[params.rig]
        carrier = CARRIERS[params.carrier]
        dose = DOSES[params.dose]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not valid_combo(growable, rig, carrier, dose):
        raise StoryError(explain_rejection(growable, rig, carrier, dose))

    world = tell(
        growable=growable,
        rig=rig,
        carrier=carrier,
        dose=dose,
        kid_name=params.kid_name,
        kid_gender=params.kid_gender,
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (growable, rig, carrier, dose) combos:\n")
        for growable, rig, carrier, dose in combos:
            print(f"  {growable:10} {rig:8} {carrier:12} {dose}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = (
                f"### {p.kid_name}: {p.growable} with {p.dose} "
                f"({p.rig}, {p.carrier}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
