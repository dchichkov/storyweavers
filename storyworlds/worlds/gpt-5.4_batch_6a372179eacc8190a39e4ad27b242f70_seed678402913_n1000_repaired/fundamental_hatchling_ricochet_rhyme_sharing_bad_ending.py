#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fundamental_hatchling_ricochet_rhyme_sharing_bad_ending.py
=====================================================================================

A standalone storyworld about two hatchlings, a sharing rhyme, and a sad little
accident caused by a ricochet. The world models a small pond-side play scene:
children gather treats, an adult teaches a rhyme about sharing, and one child is
tempted to flick a flat pebble instead of sharing fairly. Depending on the
relationship and the warning, the accident may be averted or the treat may be
lost in the water.

The seed requested these words and features:
    fundamental, hatchling, ricochet
    Rhyme, Sharing, Bad Ending
    Heartwarming style

This script keeps the heartwarming tone by making the adults gentle and loving,
even when the ending is sad.

Run it
------
    python storyworlds/worlds/gpt-5.4/fundamental_hatchling_ricochet_rhyme_sharing_bad_ending.py
    python storyworlds/worlds/gpt-5.4/fundamental_hatchling_ricochet_rhyme_sharing_bad_ending.py --surface dock --treat berry_tart
    python storyworlds/worlds/gpt-5.4/fundamental_hatchling_ricochet_rhyme_sharing_bad_ending.py --surface moss
    python storyworlds/worlds/gpt-5.4/fundamental_hatchling_ricochet_rhyme_sharing_bad_ending.py --all --qa
    python storyworlds/worlds/gpt-5.4/fundamental_hatchling_ricochet_rhyme_sharing_bad_ending.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/fundamental_hatchling_ricochet_rhyme_sharing_bad_ending.py --verify
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
IMPULSE_INIT = 5.0
CAREFUL_TRAITS = {"careful", "patient", "gentle", "thoughtful"}


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
    hard: bool = False
    flat: bool = False
    breakable: bool = False
    floating: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "hen"}
        male = {"boy", "father", "uncle", "man", "drake"}
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
        }.get(self.type, self.type)


@dataclass
class Surface:
    id: str
    label: str
    phrase: str
    bounce: int
    safe: int
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    scent: str
    plural_name: str
    float_line: str
    sink_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Stone:
    id: str
    label: str
    phrase: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    fragile_line: str
    loss_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    surface: str
    treat: str
    stone: str
    target: str
    comfort: str
    instigator: str
    instigator_gender: str
    sharer: str
    sharer_gender: str
    adult: str
    careful_trait: str
    relation: str = "siblings"
    instigator_age: int = 4
    sharer_age: int = 5
    trust: int = 6
    delay: int = 1
    seed: Optional[int] = None


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "sharer"}]

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


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    treat = world.get("treat")
    if treat.meters["in_water"] < THRESHOLD:
        return out
    sig = ("lost", "treat")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treat.meters["lost"] += 1
    for kid in world.kids():
        kid.memes["sadness"] += 1
    out.append("__loss__")
    return out


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    if world.get("target").meters["hit"] < THRESHOLD:
        return out
    sig = ("splash", "target")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__hit__")
    return out


CAUSAL_RULES = [
    Rule(name="loss", tag="physical", apply=_r_loss),
    Rule(name="splash", tag="physical", apply=_r_splash),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SURFACES = {
    "dock": Surface(
        id="dock",
        label="dock rail",
        phrase="the smooth wooden dock rail",
        bounce=2,
        safe=1,
        scene="At the edge of the pond, the old dock smelled like sun-warmed boards.",
        tags={"pond", "ricochet"},
    ),
    "stone_ring": Surface(
        id="stone_ring",
        label="stone border",
        phrase="the round stone border by the reeds",
        bounce=2,
        safe=1,
        scene="By the pond, a ring of old stones held the reeds in a quiet circle.",
        tags={"pond", "ricochet"},
    ),
    "moss": Surface(
        id="moss",
        label="mossy bank",
        phrase="the soft mossy bank",
        bounce=0,
        safe=3,
        scene="The pond bank was soft with moss, and everything there felt hushed.",
        tags={"pond"},
    ),
}

TREATS = {
    "berry_tart": Treat(
        id="berry_tart",
        label="berry tart",
        phrase="a small berry tart in a tin",
        scent="sweet berries and warm crust",
        plural_name="pieces of berry tart",
        float_line="For one worried moment the tart tin bobbed like a tiny boat.",
        sink_line="Then the tin tipped, the berry tart slipped into the dark water, and it was gone.",
        tags={"sharing", "food"},
    ),
    "seed_cake": Treat(
        id="seed_cake",
        label="seed cake",
        phrase="a round seed cake wrapped in a cloth",
        scent="toasted seeds and honey",
        plural_name="pieces of seed cake",
        float_line="The little cloth bundle spun once on the water like a pale leaf.",
        sink_line="Then the cloth opened, and the seed cake broke apart into the pond.",
        tags={"sharing", "food"},
    ),
    "plum_bun": Treat(
        id="plum_bun",
        label="plum bun",
        phrase="a soft plum bun on a plate",
        scent="warm bread and sweet plum jam",
        plural_name="pieces of plum bun",
        float_line="The plate skimmed the top of the pond for a blink.",
        sink_line="Then the plum bun slid off, and the ripples carried it away.",
        tags={"sharing", "food"},
    ),
}

STONES = {
    "flat_pebble": Stone(
        id="flat_pebble",
        label="flat pebble",
        phrase="a flat gray pebble",
        sound="tick-tick",
        tags={"stone", "ricochet"},
    ),
    "shell_chip": Stone(
        id="shell_chip",
        label="shell chip",
        phrase="a pale shell chip",
        sound="tik-tik",
        tags={"stone", "ricochet"},
    ),
    "river_stone": Stone(
        id="river_stone",
        label="river stone",
        phrase="a smooth river stone",
        sound="tap-tap",
        tags={"stone", "ricochet"},
    ),
}

TARGETS = {
    "tin": Target(
        id="tin",
        label="tin",
        phrase="the treat tin",
        fragile_line="The pebble gave the tin a sharp nudge.",
        loss_line="The tin skidded sideways and knocked the treat into the pond.",
        tags={"spill"},
    ),
    "plate": Target(
        id="plate",
        label="plate",
        phrase="the little plate",
        fragile_line="The pebble clipped the plate with a hard little sound.",
        loss_line="The plate spun, and the treat slid straight into the water.",
        tags={"spill"},
    ),
    "cloth_bundle": Target(
        id="cloth_bundle",
        label="bundle",
        phrase="the cloth bundle",
        fragile_line="The pebble struck the knot and jerked it loose.",
        loss_line="The bundle flipped open, and the treat tumbled into the pond.",
        tags={"spill"},
    ),
}

COMFORTS = {
    "song": Comfort(
        id="song",
        label="song",
        phrase="their aunt's soft song",
        tags={"comfort"},
    ),
    "hug": Comfort(
        id="hug",
        label="hug",
        phrase="a warm wing-hug",
        tags={"comfort"},
    ),
    "blanket": Comfort(
        id="blanket",
        label="blanket",
        phrase="the little pond blanket",
        tags={"comfort"},
    ),
}

GIRL_NAMES = ["Pip", "Mina", "Lulu", "Nia", "Tess", "Daisy"]
BOY_NAMES = ["Ollie", "Finn", "Reed", "Toby", "Milo", "Jem"]
TRAITS = ["careful", "patient", "gentle", "thoughtful", "calm"]


def valid_combo(surface: Surface, stone: Stone, target: Target) -> bool:
    return surface.bounce >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for surface_id, surface in SURFACES.items():
        for stone_id, stone in STONES.items():
            for target_id, target in TARGETS.items():
                if valid_combo(surface, stone, target):
                    out.append((surface_id, stone_id, target_id))
    return out


def initial_careful(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, sharer_age: int, trait: str, trust: int) -> bool:
    older = relation == "siblings" and sharer_age > instigator_age
    authority = initial_careful(trait) + (2.0 if older else 0.0) + (1.0 if trust >= 6 else 0.0)
    return older and authority > IMPULSE_INIT


def ricochet_strength(surface: Surface, delay: int) -> int:
    return surface.bounce + delay


def is_loss(surface: Surface, delay: int) -> bool:
    return ricochet_strength(surface, delay) > surface.safe


def explain_rejection(surface: Surface) -> str:
    return (
        f"(No story: {surface.phrase} is too soft for a pebble to ricochet. "
        f"Without a ricochet, there is no believable accident and no sad turn.)"
    )


def predict_accident(world: World, surface_id: str, delay: int) -> dict:
    sim = world.copy()
    surface = SURFACES[surface_id]
    if is_loss(surface, delay):
        sim.get("target").meters["hit"] += 1
        sim.get("treat").meters["in_water"] += 1
        propagate(sim, narrate=False)
    return {
        "loss": sim.get("treat").meters["lost"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, adult: Entity, treat: Treat) -> None:
    world.say(
        f"{adult.id} spread a cloth by the pond, and the air smelled like {treat.scent}. "
        f"There was {treat.phrase} waiting to be shared."
    )
    world.say(
        f"{a.id} and {b.id}, two little hatchlings with bright feet and brighter eyes, "
        f"settled beside the cloth."
    )


def sharing_rhyme(world: World, adult: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["warmth"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{adult.id} smiled and taught them a little rhyme: '
        f'"Share what is sweet, share what is small; '
        f'share with kind wings, and there is enough for all."'
    )
    world.say(
        f'{b.id} said the last line with a grin, and {a.id} tapped the rhythm on the cloth.'
    )


def division_problem(world: World, a: Entity, b: Entity, treat: Treat) -> None:
    a.memes["want"] += 1
    b.memes["hope"] += 1
    world.say(
        f"When it was time to divide the {treat.label}, {a.id} saw the larger side first."
    )
    world.say(
        f'{b.id} whispered, "We can split it fair," but {a.id} hugged the plate a little closer.'
    )


def warn(world: World, sharer: Entity, instigator: Entity, surface: Surface, adult: Entity, delay: int) -> None:
    pred = predict_accident(world, surface.id, delay)
    sharer.memes["caution"] += 1
    world.facts["predicted_loss"] = pred["loss"]
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if sharer.memes["caution"] >= 6:
        extra = f" {sharer.id} knew in a deep, quiet way that sharing was the fundamental fair thing to do."
    world.say(
        f'{sharer.id} looked at {surface.phrase} and shook {sharer.pronoun("possessive")} head. '
        f'"Please do not flick the pebble there," {sharer.pronoun()} said. '
        f'"It could ricochet and hit the treat."{extra}'
    )
    world.say(
        f'{adult.id} added gently, "The fundamental rule at this blanket is simple: '
        f'we share, and we keep our food safe."'
    )


def defy(world: World, instigator: Entity, sharer: Entity, stone: Stone, relation: str) -> None:
    instigator.memes["defiance"] += 1
    if relation == "siblings" and instigator.age > sharer.age:
        world.say(
            f'{instigator.id} lifted {stone.phrase} and said, "Just one tiny bounce." '
            f'Because {instigator.pronoun()} was the older hatchling, {sharer.id} could not stop '
            f'{instigator.pronoun("object")} in time.'
        )
    else:
        world.say(
            f'{instigator.id} lifted {stone.phrase} and said, "Just one tiny bounce." '
            f'The wish to keep the bigger piece made {instigator.pronoun("object")} bold and foolish.'
        )


def back_down(world: World, instigator: Entity, sharer: Entity, treat: Treat) -> None:
    instigator.memes["relief"] += 1
    sharer.memes["relief"] += 1
    instigator.memes["defiance"] = 0.0
    world.say(
        f"{instigator.id} stared at the pebble, then at {sharer.id}, and slowly set it down."
    )
    world.say(
        f"Together they cut the {treat.label} into two neat shares, and even the smaller crumbs felt bright."
    )


def accident(world: World, instigator: Entity, stone: Stone, surface: Surface, target: Target, treat: Treat) -> None:
    world.get("target").meters["hit"] += 1
    world.get("treat").meters["in_water"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{instigator.id} flicked the pebble. {stone.sound}! It skipped from {surface.phrase}, "
        f"made a sudden ricochet, and flew back the wrong way."
    )
    world.say(target.fragile_line)
    world.say(target.loss_line)
    world.say(treat.float_line)
    world.say(treat.sink_line)


def sorrow(world: World, instigator: Entity, sharer: Entity, adult: Entity, comfort: Comfort, treat: Treat) -> None:
    instigator.memes["regret"] += 1
    sharer.memes["sadness"] += 1
    adult.memes["care"] += 1
    world.say(
        f"For a moment nobody spoke. Then {instigator.id}'s beak wobbled, and {sharer.id} leaned close even though "
        f"{sharer.pronoun()} was sad too."
    )
    if comfort.id == "hug":
        world.say(
            f"{adult.id} gathered both hatchlings into {comfort.phrase}. "
            f'"Oh, my dears," {adult.pronoun()} said softly, "the treat is gone, and that is sad."'
        )
    elif comfort.id == "song":
        world.say(
            f"{adult.id} wrapped the quiet around them with {comfort.phrase}. "
            f'"Oh, my dears," {adult.pronoun()} said softly, "the treat is gone, and that is sad."'
        )
    else:
        world.say(
            f"{adult.id} pulled {comfort.phrase} over their backs and sat between them. "
            f'"Oh, my dears," {adult.pronoun()} said softly, "the treat is gone, and that is sad."'
        )
    world.say(
        f'"Sharing would have been smaller in the moment," {adult.pronoun()} went on, '
        f'"but kinder and wiser. Now there is nothing left to share at all."'
    )
    world.say(
        f"The pond kept widening its circles where the {treat.label} had disappeared."
    )


def gentle_end(world: World, adult: Entity, instigator: Entity, sharer: Entity) -> None:
    instigator.memes["lesson"] += 1
    sharer.memes["lesson"] += 1
    world.say(
        f"Before they went home, {adult.id} asked them to say the rhyme once more, very quietly."
    )
    world.say(
        f'{instigator.id} and {sharer.id} whispered, '
        f'"Share what is sweet, share what is small; share with kind wings, and there is enough for all."'
    )
    world.say(
        "This time the rhyme sounded lonelier, because the blanket was empty and the lesson had come too late."
    )


def happy_end(world: World, adult: Entity, instigator: Entity, sharer: Entity, treat: Treat) -> None:
    instigator.memes["lesson"] += 1
    sharer.memes["lesson"] += 1
    instigator.memes["joy"] += 1
    sharer.memes["joy"] += 1
    world.say(
        f"{adult.id} cut the {treat.label} into fair pieces and handed one to each hatchling."
    )
    world.say(
        f"They said the rhyme again, louder this time, and the pond seemed to listen."
    )
    world.say(
        f"The afternoon ended with sticky crumbs, warm shoulders, and two hatchlings who had learned that sharing was the fundamental way to keep sweetness sweet."
    )


def tell(
    surface: Surface,
    treat: Treat,
    stone: Stone,
    target: Target,
    comfort: Comfort,
    *,
    instigator_name: str,
    instigator_gender: str,
    sharer_name: str,
    sharer_gender: str,
    adult_type: str,
    careful_trait: str,
    relation: str,
    instigator_age: int,
    sharer_age: int,
    trust: int,
    delay: int,
) -> World:
    world = World()
    instigator = world.add(
        Entity(
            id=instigator_name,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            traits=["impulsive"],
            attrs={"relation": relation},
        )
    )
    sharer = world.add(
        Entity(
            id=sharer_name,
            kind="character",
            type=sharer_gender,
            role="sharer",
            age=sharer_age,
            traits=[careful_trait],
            attrs={"relation": relation},
        )
    )
    adult = world.add(
        Entity(
            id="Aunt Wren",
            kind="character",
            type=adult_type,
            role="adult",
            label="the grown-up",
        )
    )
    world.add(Entity(id="room", type="place", label="the picnic place"))
    world.add(Entity(id="surface", type="surface", label=surface.label, hard=surface.bounce > 0))
    world.add(Entity(id="stone", type="stone", label=stone.label, hard=True, flat=True))
    world.add(Entity(id="target", type="target", label=target.label, breakable=True))
    world.add(Entity(id="treat", type="treat", label=treat.label, breakable=False, floating=True))

    instigator.memes["impulse"] = IMPULSE_INIT
    sharer.memes["trust"] = float(trust)
    sharer.memes["caution"] = initial_careful(careful_trait)

    world.say(surface.scene)
    play_setup(world, instigator, sharer, adult, treat)
    sharing_rhyme(world, adult, instigator, sharer)

    world.para()
    division_problem(world, instigator, sharer, treat)
    warn(world, sharer, instigator, surface, adult, delay)

    averted = would_avert(relation, instigator_age, sharer_age, careful_trait, trust)
    if averted:
        back_down(world, instigator, sharer, treat)
        world.para()
        happy_end(world, adult, instigator, sharer, treat)
        outcome = "averted"
    else:
        defy(world, instigator, sharer, stone, relation)
        world.para()
        accident(world, instigator, stone, surface, target, treat)
        world.para()
        sorrow(world, instigator, sharer, adult, comfort, treat)
        gentle_end(world, adult, instigator, sharer)
        outcome = "lost"

    world.facts.update(
        surface=surface,
        treat_cfg=treat,
        stone_cfg=stone,
        target_cfg=target,
        comfort_cfg=comfort,
        instigator=instigator,
        sharer=sharer,
        adult=adult,
        relation=relation,
        averted=averted,
        outcome=outcome,
        delay=delay,
        loss=world.get("treat").meters["lost"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ricochet": [
        (
            "What does ricochet mean?",
            "Ricochet means something bounces off one hard surface and shoots away in a new direction. That can make a small throw hard to predict."
        )
    ],
    "sharing": [
        (
            "Why is sharing important?",
            "Sharing helps everyone feel included and cared for. It is a kind way to enjoy something together instead of fighting over it."
        )
    ],
    "hatchling": [
        (
            "What is a hatchling?",
            "A hatchling is a very young bird or other animal that has just come out of an egg. It is still little and learning how the world works."
        )
    ],
    "pond": [
        (
            "Why do things sometimes float and then sink in a pond?",
            "Some things float for a moment because the water holds them up at first. Then they tip, fill, or get heavier, and they sink."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a little pattern of words with matching sounds, like all and small. Rhymes can help people remember a lesson."
        )
    ],
    "fairness": [
        (
            "What does fair sharing mean?",
            "Fair sharing means dividing something so each person gets a proper part. It helps stop one person from taking too much."
        )
    ],
}
KNOWLEDGE_ORDER = ["hatchling", "sharing", "fairness", "rhyme", "ricochet", "pond"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        return "two hatchling siblings"
    return "two hatchling friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    instigator = f["instigator"]
    sharer = f["sharer"]
    treat = f["treat_cfg"]
    if f["outcome"] == "lost":
        return [
            'Write a heartwarming but sad story for a 3-to-5-year-old that includes the words "fundamental", "hatchling", and "ricochet".',
            f"Tell a gentle pond-side story where {instigator.id} and {sharer.id} are little hatchlings learning a sharing rhyme over {treat.label}, but a ricochet accident leaves them with nothing to eat.",
            "Write a simple story with a rhyme about sharing, a loving grown-up, and a bad ending that still feels tender and true.",
        ]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "fundamental", "hatchling", and "ricochet".',
        f"Tell a gentle story where two hatchlings almost spoil their treat with a ricochet trick, but choose sharing instead.",
        "Write a simple story with a rhyme about sharing, a loving grown-up, and an ending where fairness keeps the sweetness safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["sharer"]
    adult = f["adult"]
    treat = f["treat_cfg"]
    surface = f["surface"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, relation)}, {a.id} and {b.id}, and their gentle grown-up, {adult.id}. They sat by the pond with {treat.phrase}."
        ),
        (
            "What rhyme did they learn?",
            'They learned a sharing rhyme: "Share what is sweet, share what is small; share with kind wings, and there is enough for all." The rhyme was meant to help them remember fairness.'
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned {a.id} because the pebble could ricochet from {surface.phrase} and hit the treat. {b.pronoun().capitalize()} could see that one careless bounce might ruin everything instead of helping anyone."
        ),
    ]
    if f["outcome"] == "lost":
        qa.extend(
            [
                (
                    f"What happened when {a.id} flicked the pebble?",
                    f"The pebble made a ricochet, struck the treat holder, and knocked the {treat.label} into the pond. It floated for only a moment before it was lost."
                ),
                (
                    "Why is the ending sad?",
                    f"The ending is sad because the hatchlings were trying to keep more sweetness, and instead there was nothing left to share. The loss came from choosing a reckless trick over fairness."
                ),
                (
                    f"How did {adult.id} respond?",
                    f"{adult.id} was gentle and stayed close while they felt sad. {adult.pronoun().capitalize()} told them that sharing would have been smaller in the moment but kinder and wiser, because then the treat would still have been there."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"What did {a.id} do after the warning?",
                    f"{a.id} set the pebble down and chose not to try the ricochet trick. That decision kept the treat safe."
                ),
                (
                    "How did the problem get solved?",
                    f"The grown-up cut the {treat.label} into fair pieces so both hatchlings could have some. The sharing rhyme became real because they acted on it."
                ),
                (
                    "How did the story end?",
                    "It ended warmly, with fair pieces, sticky crumbs, and a calm pond beside them. The ending shows that sharing protected both the treat and their feelings."
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hatchling", "sharing", "rhyme"}
    if world.facts["surface"].id in {"dock", "stone_ring"}:
        tags.add("ricochet")
    if world.facts["outcome"] == "lost":
        tags.add("pond")
        tags.add("fairness")
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        surface="dock",
        treat="berry_tart",
        stone="flat_pebble",
        target="tin",
        comfort="hug",
        instigator="Ollie",
        instigator_gender="boy",
        sharer="Pip",
        sharer_gender="girl",
        adult="aunt",
        careful_trait="careful",
        relation="siblings",
        instigator_age=5,
        sharer_age=4,
        trust=6,
        delay=1,
    ),
    StoryParams(
        surface="stone_ring",
        treat="seed_cake",
        stone="river_stone",
        target="cloth_bundle",
        comfort="song",
        instigator="Mina",
        instigator_gender="girl",
        sharer="Finn",
        sharer_gender="boy",
        adult="aunt",
        careful_trait="patient",
        relation="friends",
        instigator_age=5,
        sharer_age=5,
        trust=4,
        delay=1,
    ),
    StoryParams(
        surface="dock",
        treat="plum_bun",
        stone="shell_chip",
        target="plate",
        comfort="blanket",
        instigator="Toby",
        instigator_gender="boy",
        sharer="Lulu",
        sharer_gender="girl",
        adult="aunt",
        careful_trait="gentle",
        relation="siblings",
        instigator_age=4,
        sharer_age=6,
        trust=8,
        delay=0,
    ),
]


ASP_RULES = r"""
valid(S, St, T) :- surface(S), stone(St), target(T), bounce(S, B), B >= 1.

careful_now(T) :- trait(T), careful_trait(T).
base_caution(5) :- trait(T), careful_now(T).
base_caution(3) :- trait(T), not careful_now(T).

older_sibling :- relation(siblings), sharer_age(SA), instigator_age(IA), SA > IA.
trust_bonus(1) :- trust(V), V >= 6.
trust_bonus(0) :- trust(V), V < 6.
older_bonus(2) :- older_sibling.
older_bonus(0) :- not older_sibling.

authority(C + O + TB) :- base_caution(C), older_bonus(O), trust_bonus(TB).
averted :- older_sibling, authority(A), impulse_init(I), A > I.

strength(B + D) :- chosen_surface(S), bounce(S, B), delay(D).
loss :- strength(V), chosen_surface(S), safe_limit(S, L), V > L.

outcome(averted) :- averted.
outcome(lost) :- not averted, loss.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, surface in SURFACES.items():
        lines.append(asp.fact("surface", sid))
        lines.append(asp.fact("bounce", sid, surface.bounce))
        lines.append(asp.fact("safe_limit", sid, surface.safe))
    for stone_id in STONES:
        lines.append(asp.fact("stone", stone_id))
    for target_id in TARGETS:
        lines.append(asp.fact("target", target_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_surface", params.surface),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("sharer_age", params.sharer_age),
            asp.fact("trait", params.careful_trait),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(
        params.relation,
        params.instigator_age,
        params.sharer_age,
        params.careful_trait,
        params.trust,
    ):
        return "averted"
    return "lost" if is_loss(SURFACES[params.surface], params.delay) else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as exc:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: hatchlings, a sharing rhyme, and a ricochet accident."
    )
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--stone", choices=STONES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--adult", choices=["aunt"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how much head start the accident has")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface:
        surface = SURFACES[args.surface]
        if surface.bounce < 1:
            raise StoryError(explain_rejection(surface))

    combos = [
        combo
        for combo in valid_combos()
        if (args.surface is None or combo[0] == args.surface)
        and (args.stone is None or combo[1] == args.stone)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    surface_id, stone_id, target_id = rng.choice(sorted(combos))
    treat_id = args.treat or rng.choice(sorted(TREATS))
    comfort_id = args.comfort or rng.choice(sorted(COMFORTS))
    instigator_name, instigator_gender = _pick_name(rng)
    sharer_name, sharer_gender = _pick_name(rng, avoid=instigator_name)
    adult = args.adult or "aunt"
    careful_trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, sharer_age = rng.sample([3, 4, 5, 6], 2)
    trust = rng.randint(3, 8)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)

    return StoryParams(
        surface=surface_id,
        treat=treat_id,
        stone=stone_id,
        target=target_id,
        comfort=comfort_id,
        instigator=instigator_name,
        instigator_gender=instigator_gender,
        sharer=sharer_name,
        sharer_gender=sharer_gender,
        adult=adult,
        careful_trait=careful_trait,
        relation=relation,
        instigator_age=instigator_age,
        sharer_age=sharer_age,
        trust=trust,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.stone not in STONES:
        raise StoryError(f"(Unknown stone: {params.stone})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")
    if SURFACES[params.surface].bounce < 1 and not would_avert(
        params.relation,
        params.instigator_age,
        params.sharer_age,
        params.careful_trait,
        params.trust,
    ):
        raise StoryError(explain_rejection(SURFACES[params.surface]))

    world = tell(
        SURFACES[params.surface],
        TREATS[params.treat],
        STONES[params.stone],
        TARGETS[params.target],
        COMFORTS[params.comfort],
        instigator_name=params.instigator,
        instigator_gender=params.instigator_gender,
        sharer_name=params.sharer,
        sharer_gender=params.sharer_gender,
        adult_type=params.adult,
        careful_trait=params.careful_trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        sharer_age=params.sharer_age,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (surface, stone, target) combos:\n")
        for surface, stone, target in combos:
            print(f"  {surface:11} {stone:12} {target}")
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
            header = f"### {p.instigator} and {p.sharer}: {p.treat} by {p.surface} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
