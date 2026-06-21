#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prop_parking_lot_transformation_rhyme_reconciliation_animal.py
==========================================================================================

A standalone storyworld about two little animals in a parking lot, one cherished
prop, a small quarrel, a make-do transformation, a shared rhyme, and a warm
reconciliation.

The world is narrow on purpose. A child animal brings a prop to a quiet edge of
a parking lot while a grown-up loads groceries. The friends imagine turning the
prop into something else, but a tug-of-war damages it. The exact kind of damage
comes from where they are in the lot, and the repair comes from the material of
the prop. They can only get a story when the prop, place, and imagined shape
make common sense together.

Run it
------
    python storyworlds/worlds/gpt-5.4/prop_parking_lot_transformation_rhyme_reconciliation_animal.py
    python storyworlds/worlds/gpt-5.4/prop_parking_lot_transformation_rhyme_reconciliation_animal.py --zone puddle_edge --prop box --shape boat
    python storyworlds/worlds/gpt-5.4/prop_parking_lot_transformation_rhyme_reconciliation_animal.py --prop cone --shape mushroom
    python storyworlds/worlds/gpt-5.4/prop_parking_lot_transformation_rhyme_reconciliation_animal.py --all
    python storyworlds/worlds/gpt-5.4/prop_parking_lot_transformation_rhyme_reconciliation_animal.py --qa --json
    python storyworlds/worlds/gpt-5.4/prop_parking_lot_transformation_rhyme_reconciliation_animal.py --verify
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
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def animal(self) -> str:
        return self.attrs.get("species", self.label or self.type)

    @property
    def title(self) -> str:
        return f"{self.id} the {self.animal}"


@dataclass
class Zone:
    id: str
    label: str
    detail: str
    afford_shapes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class PropCfg:
    id: str
    label: str
    phrase: str
    material: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ShapeCfg:
    id: str
    label: str
    build_text: str
    opening_rhyme: str
    closing_rhyme: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairCfg:
    id: str
    label: str
    action: str
    why: str
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


def _r_hurt(world: World) -> list[str]:
    lead = world.get("lead")
    friend = world.get("friend")
    prop = world.get("prop")
    if lead.memes["grabby"] < THRESHOLD or prop.meters["damaged"] < THRESHOLD:
        return []
    sig = ("hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    lead.memes["guilt"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    lead = world.get("lead")
    friend = world.get("friend")
    prop = world.get("prop")
    if lead.memes["apology"] < THRESHOLD or friend.memes["forgiveness"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["peace"] += 1
    friend.memes["peace"] += 1
    prop.memes["shared"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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
            world.say(sent)
    return produced


ZONES = {
    "stripe_lines": Zone(
        id="stripe_lines",
        label="the white parking lines",
        detail="At the edge of the lot, the white parking lines made neat little roads between the parked cars.",
        afford_shapes={"bus", "crown", "flower"},
        tags={"parking_lot", "lines"},
    ),
    "puddle_edge": Zone(
        id="puddle_edge",
        label="the edge of a rain puddle",
        detail="Near a wheel stop, a rain puddle shone like a small gray mirror.",
        afford_shapes={"boat", "mushroom"},
        tags={"parking_lot", "puddle"},
    ),
    "cart_corral": Zone(
        id="cart_corral",
        label="the quiet cart corral",
        detail="By the cart corral, the metal rails made a little nook away from the doors.",
        afford_shapes={"bus", "mushroom"},
        tags={"parking_lot", "cart_corral"},
    ),
}

PROPS = {
    "box": PropCfg(
        id="box",
        label="box",
        phrase="a cardboard box painted with blue stars",
        material="cardboard",
        supports={"bus", "boat"},
        tags={"box", "prop"},
    ),
    "cone": PropCfg(
        id="cone",
        label="cone",
        phrase="a clean orange traffic cone borrowed as a prop",
        material="plastic",
        supports={"crown"},
        tags={"cone", "prop"},
    ),
    "umbrella": PropCfg(
        id="umbrella",
        label="umbrella",
        phrase="a little striped umbrella used as a prop",
        material="fabric",
        supports={"flower", "mushroom"},
        tags={"umbrella", "prop"},
    ),
}

SHAPES = {
    "bus": ShapeCfg(
        id="bus",
        label="bus",
        build_text="made the prop into a pretend bus with a front window, a driver seat, and a stop sign drawn on the side",
        opening_rhyme='"Bumpy bus, do not fuss,"',
        closing_rhyme='"Bumpy bus, friends with us; ride with trust, not with fuss."',
        ending_image="Soon the little bus rolled along the white lines, stopping beside each painted space as if every parking place were a tiny station.",
        tags={"bus", "rhyme"},
    ),
    "boat": ShapeCfg(
        id="boat",
        label="boat",
        build_text="folded and shaped the prop into a small pretend boat with a brave paper nose",
        opening_rhyme='"Little boat, little float,"',
        closing_rhyme='"Little boat, little float; kind words keep us all afloat."',
        ending_image="Soon the little boat bobbed at the puddle's calm edge while the two friends crouched beside it, smiling at their wobbly captain.",
        tags={"boat", "rhyme"},
    ),
    "crown": ShapeCfg(
        id="crown",
        label="crown",
        build_text="turned the prop into a grand make-believe crown with chalk stars all around it",
        opening_rhyme='"Golden crown, no one frown,"',
        closing_rhyme='"Golden crown, no one frown; we take turns and pass it round."',
        ending_image="Soon the bright crown sat gently on first one head, then the other, while the parking lines below looked like a palace floor.",
        tags={"crown", "rhyme"},
    ),
    "flower": ShapeCfg(
        id="flower",
        label="flower",
        build_text="opened and tied the prop so it looked like a giant parking-lot flower with striped petals",
        opening_rhyme='"Parking flower, rainy hour,"',
        closing_rhyme='"Parking flower, rainy hour; shared hands give a gentle power."',
        ending_image="Soon the striped flower swayed above the white lines, bright enough to make the dull parking lot feel almost like a garden.",
        tags={"flower", "rhyme"},
    ),
    "mushroom": ShapeCfg(
        id="mushroom",
        label="mushroom",
        build_text="shaped the prop into a cozy make-believe mushroom roof for two small animals to huddle under",
        opening_rhyme='"Mushroom room, no more gloom,"',
        closing_rhyme='"Mushroom room, no more gloom; sorry words make kindness bloom."',
        ending_image="Soon the mushroom roof leaned over both friends together, making a tiny dry room in the middle of the parking lot.",
        tags={"mushroom", "rhyme"},
    ),
}

REPAIRS = {
    "towel": RepairCfg(
        id="towel",
        label="a towel",
        action="patted it dry with a soft towel from the car",
        why="drying was the sensible way to help a wet prop hold its shape again",
        tags={"towel"},
    ),
    "tape": RepairCfg(
        id="tape",
        label="a roll of tape",
        action="smoothed its hurt spots and patched them with a little roll of tape from the glove box",
        why="tape could hold cardboard or plastic together after a scrape or squash",
        tags={"tape"},
    ),
    "straighten": RepairCfg(
        id="straighten",
        label="careful paws",
        action="used careful paws to straighten the bent parts little by little",
        why="gentle straightening could help a bent thing stand proud again",
        tags={"straighten"},
    ),
    "ribbon": RepairCfg(
        id="ribbon",
        label="a ribbon",
        action="tied a ribbon around the twisty part so the scuff looked like decoration",
        why="a ribbon could hide a small fabric scrape and turn it into part of the show",
        tags={"ribbon"},
    ),
}

ANIMALS = [
    {"name": "Pip", "species": "raccoon", "gender": "boy"},
    {"name": "Mimi", "species": "mouse", "gender": "girl"},
    {"name": "Tansy", "species": "rabbit", "gender": "girl"},
    {"name": "Bramble", "species": "fox", "gender": "boy"},
    {"name": "Nora", "species": "squirrel", "gender": "girl"},
    {"name": "Otis", "species": "otter", "gender": "boy"},
]

ADULT_TYPES = ["mother", "father", "aunt", "uncle"]


def damage_for(prop: PropCfg, zone: Zone) -> str:
    if zone.id == "puddle_edge":
        return "wet"
    if zone.id == "stripe_lines":
        return "scuffed"
    if zone.id == "cart_corral":
        if prop.id == "box":
            return "squashed"
        return "bent"
    raise StoryError(f"(Unknown zone: {zone.id})")


def select_repair(prop: PropCfg, zone: Zone) -> Optional[RepairCfg]:
    damage = damage_for(prop, zone)
    if damage == "wet":
        return REPAIRS["towel"]
    if damage in {"scuffed", "squashed"} and prop.material in {"cardboard", "plastic"}:
        return REPAIRS["tape"]
    if damage == "scuffed" and prop.material == "fabric":
        return REPAIRS["ribbon"]
    if damage == "bent" and prop.material in {"plastic", "fabric"}:
        return REPAIRS["straighten"]
    return None


def transformation_possible(zone: Zone, prop: PropCfg, shape: ShapeCfg) -> bool:
    return shape.id in zone.afford_shapes and shape.id in prop.supports and select_repair(prop, zone) is not None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for zid, zone in ZONES.items():
        for pid, prop in PROPS.items():
            for sid, shape in SHAPES.items():
                if transformation_possible(zone, prop, shape):
                    combos.append((zid, pid, sid))
    return sorted(combos)


@dataclass
class StoryParams:
    zone: str
    prop: str
    shape: str
    lead_name: str
    lead_species: str
    lead_gender: str
    friend_name: str
    friend_species: str
    friend_gender: str
    adult_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        zone="stripe_lines",
        prop="box",
        shape="bus",
        lead_name="Pip",
        lead_species="raccoon",
        lead_gender="boy",
        friend_name="Tansy",
        friend_species="rabbit",
        friend_gender="girl",
        adult_type="aunt",
    ),
    StoryParams(
        zone="puddle_edge",
        prop="box",
        shape="boat",
        lead_name="Mimi",
        lead_species="mouse",
        lead_gender="girl",
        friend_name="Otis",
        friend_species="otter",
        friend_gender="boy",
        adult_type="mother",
    ),
    StoryParams(
        zone="stripe_lines",
        prop="cone",
        shape="crown",
        lead_name="Nora",
        lead_species="squirrel",
        lead_gender="girl",
        friend_name="Bramble",
        friend_species="fox",
        friend_gender="boy",
        adult_type="father",
    ),
    StoryParams(
        zone="stripe_lines",
        prop="umbrella",
        shape="flower",
        lead_name="Tansy",
        lead_species="rabbit",
        lead_gender="girl",
        friend_name="Mimi",
        friend_species="mouse",
        friend_gender="girl",
        adult_type="uncle",
    ),
    StoryParams(
        zone="cart_corral",
        prop="umbrella",
        shape="mushroom",
        lead_name="Otis",
        lead_species="otter",
        lead_gender="boy",
        friend_name="Nora",
        friend_species="squirrel",
        friend_gender="girl",
        adult_type="mother",
    ),
]


def explain_rejection(zone: Zone, prop: PropCfg, shape: ShapeCfg) -> str:
    if shape.id not in prop.supports:
        return (
            f"(No story: {prop.phrase} does not sensibly turn into a {shape.label}. "
            f"Pick a shape that suits the prop.)"
        )
    if shape.id not in zone.afford_shapes:
        return (
            f"(No story: {shape.label} does not fit {zone.label} in this parking-lot world. "
            f"Pick a shape that matches the place.)"
        )
    repair = select_repair(prop, zone)
    if repair is None:
        return (
            f"(No story: in {zone.label}, {prop.label} would be {damage_for(prop, zone)}, "
            f"and this world has no simple child-facing repair for that.)"
        )
    return "(No story: that combination is not reasonable here.)"


def introduce(world: World, lead: Entity, friend: Entity, adult: Entity, zone: Zone, prop: PropCfg) -> None:
    lead.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright shopping morning, {lead.title} and {friend.title} waited with "
        f"{lead.pronoun('possessive')} {adult.type} at a quiet edge of the parking lot."
    )
    world.say(zone.detail)
    world.say(
        f"{lead.id} had brought a prop: {prop.phrase}. To {lead.pronoun('object')}, "
        f"it did not look plain at all. It looked ready to become something splendid."
    )


def dream(world: World, lead: Entity, friend: Entity, shape: ShapeCfg) -> None:
    lead.memes["pride"] += 1
    world.say(
        f'{lead.id} lifted the prop and whispered {shape.opening_rhyme} '
        f'{lead.pronoun()} said, already imagining the new {shape.label}.'
    )
    world.say(
        f"{friend.id}'s eyes shone too. {friend.pronoun().capitalize()} wanted a turn in the game, "
        f"because the rhyme sounded too good to miss."
    )


def quarrel(world: World, lead: Entity, friend: Entity) -> None:
    lead.memes["grabby"] += 1
    friend.memes["want"] += 1
    world.say(
        f'"Wait, let me hold it too," said {friend.id}. But {lead.id} hugged the prop tight. '
        f'"Just for one more minute," {lead.pronoun()} said.'
    )
    world.say(
        f"One more minute turned into a little tug. It was not a fierce quarrel, only the sad kind "
        f"that starts when two friends both want the same bright thing at once."
    )


def damage_prop(world: World, prop_ent: Entity, zone: Zone, prop: PropCfg) -> None:
    damage = damage_for(prop, zone)
    prop_ent.meters["damaged"] += 1
    prop_ent.meters[damage] += 1
    propagate(world, narrate=False)
    if damage == "wet":
        world.say(
            f"The prop slipped from their paws and landed at {zone.label}. When they picked it up again, "
            f"it was wet and droopy."
        )
    elif damage == "scuffed":
        world.say(
            f"The prop skidded over {zone.label} and came back with a rough scuff across it."
        )
    elif damage == "squashed":
        world.say(
            f"The prop bumped the rail by {zone.label} and one side went squashy and bent."
        )
    else:
        world.say(
            f"The prop knocked against the metal beside {zone.label} and came back a little bent."
        )


def apologize(world: World, lead: Entity, friend: Entity) -> None:
    lead.memes["apology"] += 1
    friend.memes["forgiveness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{lead.id} looked at the hurt prop, then at {friend.id}'s face. "
        f'"I am sorry," {lead.pronoun()} said softly. "I should have shared the prop before it got hurt."'
    )
    world.say(
        f'{friend.id} touched the torn or crooked place with one careful paw. '
        f'"I am sorry too," {friend.pronoun()} said. "I pulled too hard."'
    )


def transform(world: World, lead: Entity, friend: Entity, adult: Entity, prop_ent: Entity,
              zone: Zone, prop: PropCfg, shape: ShapeCfg, repair: RepairCfg) -> None:
    prop_ent.meters["repaired"] += 1
    prop_ent.meters["transformed"] += 1
    lead.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{adult.type.capitalize()} was still stacking groceries in the trunk, but {lead.id} and {friend.id} "
        f"did not need a big rescue. They needed kind paws and one small sensible idea."
    )
    world.say(
        f"So they sat together on the safe side of the wheel stop and {repair.action}. "
        f"{repair.why.capitalize()}."
    )
    world.say(
        f"Then, instead of arguing about the old plan, they {shape.build_text}."
    )


def celebrate(world: World, lead: Entity, friend: Entity, shape: ShapeCfg) -> None:
    world.say(
        f'This time they spoke the rhyme together: {shape.closing_rhyme}'
    )
    world.say(
        f"{shape.ending_image} The parking lot was still a parking lot, of course, "
        f"but now it held two peaceful friends and one much happier prop."
    )


def tell(params: StoryParams) -> World:
    zone = ZONES[params.zone]
    prop = PROPS[params.prop]
    shape = SHAPES[params.shape]
    repair = select_repair(prop, zone)
    if repair is None or not transformation_possible(zone, prop, shape):
        raise StoryError(explain_rejection(zone, prop, shape))

    world = World()
    lead = world.add(Entity(
        id="lead",
        kind="character",
        type=params.lead_gender,
        label=params.lead_name,
        role="lead",
        attrs={"species": params.lead_species, "display": params.lead_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_gender,
        label=params.friend_name,
        role="friend",
        attrs={"species": params.friend_species, "display": params.friend_name},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=params.adult_type,
        label=params.adult_type,
        role="adult",
        attrs={},
    ))
    prop_ent = world.add(Entity(
        id="prop",
        kind="thing",
        type=prop.material,
        label=prop.label,
        phrase=prop.phrase,
        role="prop",
        tags=set(prop.tags),
    ))

    world.facts.update(
        zone=zone,
        prop_cfg=prop,
        shape_cfg=shape,
        repair_cfg=repair,
        lead=lead,
        friend=friend,
        adult=adult,
        prop=prop_ent,
        damage=damage_for(prop, zone),
    )

    introduce(world, lead, friend, adult, zone, prop)
    dream(world, lead, friend, shape)

    world.para()
    quarrel(world, lead, friend)
    damage_prop(world, prop_ent, zone, prop)
    apologize(world, lead, friend)

    world.para()
    transform(world, lead, friend, adult, prop_ent, zone, prop, shape, repair)
    celebrate(world, lead, friend, shape)

    world.facts["reconciled"] = lead.memes["peace"] >= THRESHOLD and friend.memes["peace"] >= THRESHOLD
    world.facts["transformed"] = prop_ent.meters["transformed"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "parking_lot": [
        ("What is a parking lot?",
         "A parking lot is a place where cars stop and wait. It has painted spaces and people should stay close to a grown-up there.")
    ],
    "puddle": [
        ("Why does cardboard get droopy in a puddle?",
         "Cardboard drinks in water and becomes soft. That makes it sag instead of holding a stiff shape.")
    ],
    "lines": [
        ("Why are white parking lines painted on the ground?",
         "White parking lines show where cars should stop. They help drivers keep neat spaces between cars.")
    ],
    "cart_corral": [
        ("What is a cart corral?",
         "A cart corral is the place where shopping carts are lined up together. It helps keep carts from rolling around the lot.")
    ],
    "box": [
        ("What can a cardboard box become in pretend play?",
         "A cardboard box can become many things in pretend play, like a bus, a boat, or a little house. Children use imagination to transform plain things.")
    ],
    "cone": [
        ("What is a traffic cone for?",
         "A traffic cone is a bright marker that helps people notice where to slow down or stay away. Its pointed shape is easy to see.")
    ],
    "umbrella": [
        ("What does an umbrella do?",
         "An umbrella opens wide to keep rain off your head and shoulders. It can also make a cozy pretend roof in a game.")
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is when words have matching sounds, like 'float' and 'boat.' Rhymes can make a little chant easy to remember.")
    ],
    "apology": [
        ("Why does saying sorry help friends?",
         "Saying sorry shows that you understand someone was hurt. It helps make room for trust and kindness to come back.")
    ],
}
KNOWLEDGE_ORDER = ["parking_lot", "puddle", "lines", "cart_corral", "box", "cone", "umbrella", "rhyme", "apology"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    lead = world.facts["lead"]
    friend = world.facts["friend"]
    zone = world.facts["zone"]
    prop = world.facts["prop_cfg"]
    shape = world.facts["shape_cfg"]
    return [
        f'Write an animal story for a 3-to-5-year-old set in a parking lot that includes the word "prop" and ends in reconciliation.',
        f"Tell a gentle story where {display_name(lead)} the {lead.animal} and {display_name(friend)} the {friend.animal} quarrel over {prop.phrase}, then transform it into a {shape.label}.",
        f'Write a child-facing story with a small rhyme, a damaged prop, and a repaired ending image at {zone.label}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    lead = world.facts["lead"]
    friend = world.facts["friend"]
    adult = world.facts["adult"]
    zone = world.facts["zone"]
    prop = world.facts["prop_cfg"]
    shape = world.facts["shape_cfg"]
    repair = world.facts["repair_cfg"]
    damage = world.facts["damage"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {display_name(lead)} the {lead.animal} and {display_name(friend)} the {friend.animal}. "
            f"They were waiting with {lead.pronoun('possessive')} {adult.type} in a parking lot."
        ),
        (
            "What was the prop?",
            f"The prop was {prop.phrase}. {display_name(lead)} thought it could become something splendid in their pretend game."
        ),
        (
            "Why did the friends start to quarrel?",
            f"They both wanted the same prop at the same time. {display_name(lead)} held it too tightly, and {display_name(friend)} tried to pull it too, so the little quarrel grew."
        ),
        (
            "What happened to the prop?",
            f"It was {damage} at {zone.label}. The damage came from the tug and from where they were playing in the parking lot."
        ),
        (
            "How did the friends make up?",
            f"They both said sorry and stopped tugging. That mattered because the apology let them work side by side instead of pulling against each other."
        ),
        (
            f"How did the prop become a {shape.label}?",
            f"They {repair.action} and then {shape.build_text}. The repair matched the kind of damage, so the transformation felt possible instead of magical."
        ),
        (
            "How did the story end?",
            f"It ended with the two friends speaking a rhyme together and sharing the transformed prop. "
            f"The last image shows that the quarrel changed into cooperation."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    zone = world.facts["zone"]
    prop = world.facts["prop_cfg"]
    tags |= zone.tags
    tags |= prop.tags
    tags |= {"rhyme", "apology"}
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
supports(box,bus). supports(box,boat).
supports(cone,crown).
supports(umbrella,flower). supports(umbrella,mushroom).

allows(stripe_lines,bus). allows(stripe_lines,crown). allows(stripe_lines,flower).
allows(puddle_edge,boat). allows(puddle_edge,mushroom).
allows(cart_corral,bus). allows(cart_corral,mushroom).

damage(P,Z,wet)      :- prop(P), zone(Z), Z = puddle_edge.
damage(P,Z,scuffed)  :- prop(P), zone(Z), Z = stripe_lines.
damage(box,Z,squashed) :- zone(Z), Z = cart_corral.
damage(P,Z,bent)     :- prop(P), zone(Z), Z = cart_corral, P != box.

repair(P,Z,towel)      :- damage(P,Z,wet).
repair(P,Z,tape)       :- damage(P,Z,scuffed), material(P,cardboard).
repair(P,Z,tape)       :- damage(P,Z,scuffed), material(P,plastic).
repair(P,Z,ribbon)     :- damage(P,Z,scuffed), material(P,fabric).
repair(P,Z,tape)       :- damage(P,Z,squashed), material(P,cardboard).
repair(P,Z,straighten) :- damage(P,Z,bent), material(P,plastic).
repair(P,Z,straighten) :- damage(P,Z,bent), material(P,fabric).

valid(Z,P,S) :- zone(Z), prop(P), shape(S), supports(P,S), allows(Z,S), repair(P,Z,_).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for zid in ZONES:
        lines.append(asp.fact("zone", zid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("material", pid, prop.material))
    for sid in SHAPES:
        lines.append(asp.fact("shape", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_repairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show repair/3."))
    return sorted(set(asp.atoms(model, "repair")))


def python_repairs() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for zid, zone in ZONES.items():
        for pid, prop in PROPS.items():
            repair = select_repair(prop, zone)
            if repair is not None:
                out.append((pid, zid, repair.id))
    return sorted(out)


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: valid combo gate matches ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_repair = set(asp_repairs())
    python_repair = set(python_repairs())
    if clingo_repair == python_repair:
        print(f"OK: repair derivation matches ({len(clingo_repair)} cases).")
    else:
        rc = 1
        print("MISMATCH in repairs:")
        if clingo_repair - python_repair:
            print("  only in clingo:", sorted(clingo_repair - python_repair))
        if python_repair - clingo_repair:
            print("  only in python:", sorted(python_repair - clingo_repair))

    smoke_params = list(CURATED)
    smoke_params.append(resolve_params(build_parser().parse_args([]), random.Random(7)))
    for idx, params in enumerate(smoke_params, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header=f"[smoke {idx}]")
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"SMOKE TEST FAILED on case {idx}: {err}")
            break

    if rc == 0:
        print("OK: smoke generation succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: a prop in a parking lot, a quarrel, a transformation, a rhyme, and reconciliation."
    )
    ap.add_argument("--zone", choices=ZONES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--shape", choices=SHAPES)
    ap.add_argument("--adult", choices=ADULT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.zone and args.prop and args.shape:
        zone = ZONES[args.zone]
        prop = PROPS[args.prop]
        shape = SHAPES[args.shape]
        if not transformation_possible(zone, prop, shape):
            raise StoryError(explain_rejection(zone, prop, shape))

    combos = [
        combo for combo in valid_combos()
        if (args.zone is None or combo[0] == args.zone)
        and (args.prop is None or combo[1] == args.prop)
        and (args.shape is None or combo[2] == args.shape)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    zone_id, prop_id, shape_id = rng.choice(sorted(combos))
    pair = rng.sample(ANIMALS, 2)
    lead_pick, friend_pick = pair[0], pair[1]
    adult_type = args.adult or rng.choice(ADULT_TYPES)
    return StoryParams(
        zone=zone_id,
        prop=prop_id,
        shape=shape_id,
        lead_name=lead_pick["name"],
        lead_species=lead_pick["species"],
        lead_gender=lead_pick["gender"],
        friend_name=friend_pick["name"],
        friend_species=friend_pick["species"],
        friend_gender=friend_pick["gender"],
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.zone not in ZONES:
        raise StoryError(f"(Unknown zone: {params.zone})")
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop: {params.prop})")
    if params.shape not in SHAPES:
        raise StoryError(f"(Unknown shape: {params.shape})")

    world = tell(params)
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
        print(asp_program("#show valid/3.\n#show repair/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (zone, prop, shape) combos:\n")
        for zone, prop, shape in combos:
            print(f"  {zone:13} {prop:10} {shape}")
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
            header = f"### {p.lead_name} the {p.lead_species}: {p.prop} -> {p.shape} at {p.zone}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
