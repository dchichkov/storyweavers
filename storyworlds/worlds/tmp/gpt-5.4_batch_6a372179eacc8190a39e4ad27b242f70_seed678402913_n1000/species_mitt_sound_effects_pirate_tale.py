#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/species_mitt_sound_effects_pirate_tale.py
====================================================================

A standalone story world for a tiny pirate-style tale about children exploring a
tide pool, a touchy sea species, and the safer habit of using a mitt and
watching gently instead of grabbing fast.

Seed requirements carried into the world:
- includes the words "species" and "mitt"
- uses sound effects in the prose
- keeps a playful Pirate Tale style

The world model is small and classical:
- children play pirates at a rocky cove
- one child wants to grab a hidden sea creature too quickly
- another child warns that the species can pinch, prickle, or sting
- an older sibling may avert the mistake before it happens
- otherwise the child gets a small hurt, a grown-up helps, and the children
  later return with a mitt and a calmer method

Run it
------
    python storyworlds/worlds/gpt-5.4/species_mitt_sound_effects_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/species_mitt_sound_effects_pirate_tale.py --species hermit_crab
    python storyworlds/worlds/gpt-5.4/species_mitt_sound_effects_pirate_tale.py --method spyglass
    python storyworlds/worlds/gpt-5.4/species_mitt_sound_effects_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/species_mitt_sound_effects_pirate_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/species_mitt_sound_effects_pirate_tale.py --verify
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
CAREFUL_TRAITS = {"careful", "cautious", "steady", "sensible"}
BRAVERY_INIT = 6.0


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "ranger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "ranger": "ranger"}.get(self.type, self.type)


@dataclass
class CoveTheme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    goal: str
    ending: str


@dataclass
class SpeciesCfg:
    id: str
    label: str
    phrase: str
    defense: str
    habitat: str
    clue: str
    sound: str
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    line: str
    direct_touch: bool
    rough: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hurt_spooks(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("instigator")
    creature = world.entities.get("species")
    if hero is None or creature is None:
        return out
    if hero.meters["ouch"] < THRESHOLD:
        return out
    sig = ("hurt_spooks", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    creature.meters["hidden"] += 1
    creature.memes["alarm"] += 1
    out.append("__hurt__")
    return out


CAUSAL_RULES = [
    Rule(name="hurt_spooks", tag="physical", apply=_r_hurt_spooks),
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
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hazard_at_risk(species: SpeciesCfg, method: Method) -> bool:
    return method.direct_touch and species.defense in {"pinch", "prickle", "sting"}


def select_gear(species: SpeciesCfg) -> Optional[Gear]:
    for gear in GEARS.values():
        if species.defense in gear.guards:
            return gear
    return None


def careful_score(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = careful_score(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > BRAVERY_INIT


def predict_hurt(world: World, species_id: str, method_id: str) -> dict:
    sim = world.copy()
    creature = sim.get(species_id)
    hero = sim.get("instigator")
    method = METHODS[method_id]
    if hazard_at_risk(SPECIES[creature.attrs["cfg"]], method):
        hero.meters["ouch"] += 1
        propagate(sim, narrate=False)
    return {
        "hurt": hero.meters["ouch"] >= THRESHOLD,
        "species_hidden": creature.meters["hidden"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, theme: CoveTheme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    t1, t2 = theme.titles
    world.say(
        f"On a bright shore morning, {a.id} and {b.id} turned the little cove into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{t1} {a.id} and {t2} {b.id}!" {a.id} shouted. "Let\'s find {theme.goal}!"'
    )


def discover_clue(world: World, b: Entity, species: SpeciesCfg) -> None:
    world.say(
        f"They knelt by a tide pool where the water went {species.sound}. "
        f"Under {species.habitat}, {b.id} spotted {species.clue}."
    )
    world.say(f'"That must be the species we are hunting," {b.id} whispered.')


def tempt(world: World, a: Entity, method: Method, species: SpeciesCfg) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} grinned. "{method.line}" {a.pronoun().capitalize()} said, already reaching toward {species.phrase}.'
    )
    world.say("For one quick pirate moment, snatching it seemed faster than thinking.")


def warn(world: World, b: Entity, a: Entity, species: SpeciesCfg, method: Method, helper: Entity) -> None:
    pred = predict_hurt(world, "species", method.id)
    b.memes["caution"] += 1
    world.facts["predicted_hurt"] = pred["hurt"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} held out an arm to stop {a.id}."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. {species.warning}. '
        f'{helper.label_word.capitalize()} said tide-pool pirates must look first and touch gently."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, method: Method) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"I can do it fast," {a.id} said. Because {a.id} was {b.id}\'s older sibling, '
            f'{b.id} could not quite stop {a.pronoun("object")} before {a.pronoun()} darted in.'
        )
    else:
        world.say(f'"I can do it fast," {a.id} said, and darted in anyway.')


def back_down(world: World, a: Entity, b: Entity, helper: Entity, gear: Gear, theme: CoveTheme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} stopped with fingers still in the air. Then {a.pronoun()} looked at {b.id}, '
        f'thought better of it, and pulled back. "All right," {a.pronoun()} muttered.'
    )
    world.say(
        f'Together they went to {helper.label_word} and asked for {gear.phrase}. Soon they were kneeling still as shells, '
        f'and the pirate game changed from grabbing treasure to watching it.'
    )
    world.say(
        f'By the end of the morning, {theme.ending}.'
    )


def touch_hazard(world: World, a: Entity, species_ent: Entity, species: SpeciesCfg, method: Method) -> None:
    if hazard_at_risk(species, method):
        a.meters["ouch"] += 1
        species_ent.meters["touched"] += 1
        propagate(world, narrate=False)
    world.say(
        f'{species.sound.capitalize()}! {a.id} reached under {species.habitat}, and at once {a.pronoun("possessive")} hand jerked back.'
    )
    if species.defense == "pinch":
        world.say(
            f'"Ow!" cried {a.id}. "{species.label.capitalize()} pinched me!"'
        )
    elif species.defense == "prickle":
        world.say(
            f'"Ow!" cried {a.id}. "That {species.label} felt prickly!"'
        )
    else:
        world.say(
            f'"Ow!" cried {a.id}. "That {species.label} stung my fingers!"'
        )
    if species_ent.meters["hidden"] >= THRESHOLD:
        world.say(
            f"Zip-zip! The frightened little species tucked itself deep away where nobody could see it."
        )


def alarm(world: World, b: Entity, helper: Entity) -> None:
    world.say(f'"{helper.label_word.capitalize()}!" {b.id} called. "Please come help!"')


def help_and_lesson(world: World, helper: Entity, a: Entity, b: Entity, species: SpeciesCfg) -> None:
    a.meters["ouch"] = 0.0
    a.memes["fear"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"{helper.label_word.capitalize()} hurried over, washed {a.id}'s hand with cool water, checked each finger, "
        f"and wrapped the sore spot with a little bandage."
    )
    world.say(
        f'"Small sea creatures are not treasure to snatch," {helper.pronoun()} said softly. '
        f'"Each species is alive, and some of them defend themselves when scared. Next time, wear a mitt and watch first."'
    )


def safe_return(world: World, helper: Entity, a: Entity, b: Entity, species_ent: Entity,
                species: SpeciesCfg, gear: Gear, theme: CoveTheme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    species_ent.meters["hidden"] = 0.0
    species_ent.meters["visible"] += 1
    species_ent.memes["alarm"] = 0.0
    world.say(
        f"The next day, {helper.label_word} met them at the rocks with {gear.phrase}. "
        f'"Now we can be proper cove pirates," {helper.pronoun()} said.'
    )
    world.say(
        f'{b.id} slipped on the mitt. Swish-swish went the water as {a.id} held still beside {b.pronoun("object")}. '
        f'Together they lifted a bit of drifting weed without grabbing at all.'
    )
    world.say(
        f'Out peeped {species.phrase} again. This time nobody snatched. They watched its tiny brave body move from shell to stone, '
        f'and they learned that the best pirate captains leave every species safe in its home.'
    )
    world.say(theme.ending)


THEMES = {
    "pirates": CoveTheme(
        id="pirates",
        scene="a secret pirate cove",
        rig="A driftwood branch was their mast, a striped towel was their sail, and a bucket with two shiny shells was their treasure chest.",
        titles=("Captain", "Lookout"),
        goal="the hidden cove treasure",
        ending="the two pirates tiptoed away with wet knees, a borrowed mitt, and a story they were proud to tell",
    ),
    "corsairs": CoveTheme(
        id="corsairs",
        scene="a whispering corsair bay",
        rig="A flat rock was their ship deck, a stick was their spyglass, and a red scarf flapped like a captain's flag.",
        titles=("Captain", "Scout"),
        goal="the secret tide-pool prize",
        ending="the young corsairs headed home smiling, leaving the pool bright and undisturbed behind them",
    ),
}

SPECIES = {
    "hermit_crab": SpeciesCfg(
        id="hermit_crab",
        label="hermit crab",
        phrase="a tiny hermit crab",
        defense="pinch",
        habitat="a curled shell between two stones",
        clue="a shell that twitched all by itself",
        sound="scritch-scritch",
        warning="That species can pinch if you poke at it",
        tags={"crab", "species", "tide_pool"},
    ),
    "sea_urchin": SpeciesCfg(
        id="sea_urchin",
        label="sea urchin",
        phrase="a round sea urchin",
        defense="prickle",
        habitat="a dark bowl in the rock",
        clue="a round shadow with little spines around it",
        sound="plink-plink",
        warning="That species is covered in prickles",
        tags={"urchin", "species", "tide_pool"},
    ),
    "anemone": SpeciesCfg(
        id="anemone",
        label="sea anemone",
        phrase="a small sea anemone",
        defense="sting",
        habitat="a waving patch of green-brown weed",
        clue="soft arms opening and closing like a flower under water",
        sound="slosh-slosh",
        warning="That species can sting tender fingers",
        tags={"anemone", "species", "tide_pool"},
    ),
}

METHODS = {
    "bare_hand": Method(
        id="bare_hand",
        label="bare hand",
        line="I'll just grab it with my bare hand",
        direct_touch=True,
        rough=True,
        tags={"touch"},
    ),
    "quick_grab": Method(
        id="quick_grab",
        label="quick grab",
        line="I'll make one quick grab before it scoots away",
        direct_touch=True,
        rough=True,
        tags={"touch"},
    ),
    "finger_poke": Method(
        id="finger_poke",
        label="finger poke",
        line="I'll poke it out with one finger",
        direct_touch=True,
        rough=False,
        tags={"touch"},
    ),
    "spyglass": Method(
        id="spyglass",
        label="spyglass peek",
        line="I'll just look through the pretend spyglass",
        direct_touch=False,
        rough=False,
        tags={"look"},
    ),
}

GEARS = {
    "rubber_mitt": Gear(
        id="rubber_mitt",
        label="rubber mitt",
        phrase="a bright yellow rubber mitt",
        guards={"pinch", "prickle", "sting"},
        tags={"mitt"},
    ),
    "striped_mitt": Gear(
        id="striped_mitt",
        label="striped tide-pool mitt",
        phrase="a striped tide-pool mitt",
        guards={"pinch", "prickle", "sting"},
        tags={"mitt"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "steady", "sensible", "curious", "bold"]


@dataclass
class StoryParams:
    theme: str
    species: str
    method: str
    gear: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    helper: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="pirates",
        species="hermit_crab",
        method="bare_hand",
        gear="striped_mitt",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        helper="mother",
        trait="careful",
        relation="siblings",
        instigator_age=6,
        cautioner_age=4,
    ),
    StoryParams(
        theme="corsairs",
        species="sea_urchin",
        method="quick_grab",
        gear="rubber_mitt",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        helper="father",
        trait="steady",
        relation="friends",
        instigator_age=5,
        cautioner_age=5,
    ),
    StoryParams(
        theme="pirates",
        species="anemone",
        method="finger_poke",
        gear="striped_mitt",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Theo",
        cautioner_gender="boy",
        helper="ranger",
        trait="cautious",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for species_id, species in SPECIES.items():
            for method_id, method in METHODS.items():
                if hazard_at_risk(species, method) and select_gear(species) is not None:
                    combos.append((theme, species_id, method_id))
    return combos


def explain_rejection(species: SpeciesCfg, method: Method) -> str:
    if not method.direct_touch:
        return (
            f"(No story: {method.label} does not touch {species.phrase}, so nobody gets hurt and the warning has no real danger. "
            f"Pick a direct-touch method like bare_hand, quick_grab, or finger_poke.)"
        )
    return "(No story: this combination does not create a reasonable tide-pool hazard.)"


def explain_gear(species: SpeciesCfg, gear_id: str) -> str:
    gear = GEARS[gear_id]
    if species.defense not in gear.guards:
        return (
            f"(No story: {gear.label} does not guard against a {species.defense} defense, so it is not a believable safe fix.)"
        )
    return ""


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "helped"


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def introduce_people(world: World, a: Entity, b: Entity, helper: Entity, theme: CoveTheme) -> None:
    play_setup(world, a, b, theme)
    if helper.type == "ranger":
        world.say("A kind beach ranger was nearby, tidying the sign by the path and keeping an eye on the pools.")


def tell(theme: CoveTheme, species: SpeciesCfg, method: Method, gear: Gear,
         instigator: str, instigator_gender: str,
         cautioner: str, cautioner_gender: str,
         helper_type: str, trait: str,
         relation: str, instigator_age: int, cautioner_age: int) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        phrase=instigator,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation, "name": instigator},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        phrase=cautioner,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation, "name": cautioner},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        phrase="the helper",
        role="helper",
    ))
    species_ent = world.add(Entity(
        id="species",
        type="creature",
        label=species.label,
        phrase=species.phrase,
        attrs={"cfg": species.id},
        tags=set(species.tags),
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = careful_score(trait)

    world.facts["theme_cfg"] = theme
    world.facts["species_cfg"] = species
    world.facts["method_cfg"] = method
    world.facts["gear_cfg"] = gear
    world.facts["relation"] = relation

    # Act 1
    introduce_people(world, a, b, helper, theme)
    discover_clue(world, b, species)

    # Act 2
    world.para()
    tempt(world, a, method, species)
    warn(world, b, a, species, method, helper)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, helper, gear, theme)
        outcome = "averted"
    else:
        defy(world, a, b, method)

        # Act 3
        world.para()
        touch_hazard(world, a, species_ent, species, method)
        alarm(world, b, helper)

        # Act 4
        world.para()
        help_and_lesson(world, helper, a, b, species)

        # Act 5
        world.para()
        safe_return(world, helper, a, b, species_ent, species, gear, theme)
        outcome = "helped"

    world.facts.update(
        instigator=a,
        cautioner=b,
        helper=helper,
        species=species_ent,
        outcome=outcome,
        gear_used=gear.id,
        hurt_happened=(outcome == "helped"),
        lesson=(a.memes["lesson"] >= THRESHOLD or b.memes["lesson"] >= THRESHOLD or outcome == "averted"),
    )
    return world


KNOWLEDGE = {
    "species": [
        (
            "What does the word species mean?",
            "A species is one kind of living thing. Hermit crabs, sea urchins, and sea anemones are different species."
        )
    ],
    "tide_pool": [
        (
            "What is a tide pool?",
            "A tide pool is a little pool of sea water left behind among the rocks when the tide goes out. Small sea creatures can live there."
        )
    ],
    "crab": [
        (
            "Why can a hermit crab pinch?",
            "A hermit crab has little claws it uses to hold on and protect itself. If it gets scared, it may pinch."
        )
    ],
    "urchin": [
        (
            "Why should you be careful around a sea urchin?",
            "A sea urchin is covered in sharp little spines. Touching it can hurt your skin."
        )
    ],
    "anemone": [
        (
            "Why should you not poke a sea anemone?",
            "A sea anemone is a living animal, and some can sting tender fingers. It is kinder and safer to watch gently."
        )
    ],
    "mitt": [
        (
            "What is a mitt?",
            "A mitt is a thick hand covering. It helps protect your hand better than bare fingers."
        )
    ],
    "touch": [
        (
            "Why is grabbing wild sea creatures a bad idea?",
            "Grabbing can hurt you, and it can also scare the animal. It is better to look carefully and let the creature stay safe."
        )
    ],
}


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    species = f["species_cfg"]
    method = f["method_cfg"]
    gear = f["gear_cfg"]
    theme = f["theme_cfg"]
    outcome = f["outcome"]
    name_a = a.attrs["name"]
    name_b = b.attrs["name"]
    base = (
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "species" and "mitt", '
        f'uses sound effects, and takes place at a tide pool.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story where {name_a} wants to use a {method.label} on {species.phrase}, "
            f"but {name_b} stops the mistake before anyone gets hurt.",
            f"Write a small pirate cove tale where children learn to watch a sea species with {gear.phrase} and patience instead of grabbing treasure."
        ]
    return [
        base,
        f"Tell a pirate cove story where {name_a} ignores {name_b}'s warning and gets a small hurt from {species.phrase}, "
        f"then learns to use {gear.phrase}.",
        f"Write a child-facing story with sound effects, a tide-pool species, a mitt, and an ending where the children leave the creature safe in its home."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    species = f["species_cfg"]
    method = f["method_cfg"]
    gear = f["gear_cfg"]
    theme = f["theme_cfg"]
    name_a = a.attrs["name"]
    name_b = b.attrs["name"]
    relation = f.get("relation", "friends")
    pair = pair_noun(a, b, relation)
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {name_a} and {name_b}, pretending to be pirates at a rocky cove. "
            f"A {helper_word} nearby also helps them learn a safer way."
        ),
        (
            "What were the children trying to find?",
            f"They were hunting for a tiny sea species in a tide pool as if it were pirate treasure. "
            f"The game made the discovery feel exciting and a little secret."
        ),
        (
            f"Why did {name_b} warn {name_a}?",
            f"{name_b} warned {name_a} because {species.label} can {species.defense}, and {method.label} meant touching it directly. "
            f"The warning came before the children knew for sure what would happen, but it was based on real danger."
        ),
    ]
    if f["outcome"] == "averted":
        qa.extend([
            (
                f"What did {name_a} do after the warning?",
                f"{name_a} pulled back and chose not to grab at the creature. "
                f"That choice kept both the child and the species safe."
            ),
            (
                "How did the story end?",
                f"It ended calmly, with the children watching the tide pool more gently and using {gear.phrase}. "
                f"The ending shows they changed from snatching pirates into careful explorers."
            ),
        ])
    else:
        qa.extend([
            (
                f"What happened when {name_a} reached in?",
                f"{name_a} got a small hurt when {species.phrase} defended itself, and the frightened creature hid away. "
                f"The trouble started because grabbing was too rough and too close."
            ),
            (
                f"How did the {helper_word} help?",
                f"The {helper_word} washed {name_a}'s hand, checked the sore fingers, and put on a small bandage. "
                f"Then {helper.pronoun().capitalize()} explained that each species is alive and should be watched gently."
            ),
            (
                f"What changed the next day?",
                f"They came back with {gear.phrase} and a calmer plan. "
                f"Instead of grabbing for treasure, they watched quietly and left the creature safe in its home."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"species", "mitt"} | set(world.facts["species_cfg"].tags) | set(world.facts["method_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in ["species", "tide_pool", "crab", "urchin", "anemone", "mitt", "touch"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(S, M) :- defended(S), direct_touch(M).
valid(T, S, M) :- theme(T), species(S), method(M), hazard(S, M), has_gear(S).

has_gear(S) :- species(S), defense(S, D), gear(G), guards(G, D).

caution_now(T) :- trait(T), careful_trait(T).
init_caution(5) :- trait(T), caution_now(T).
init_caution(3) :- trait(T), not caution_now(T).
older_sib :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
bonus(3) :- older_sib.
bonus(0) :- not older_sib.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sib, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(helped) :- not averted.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for species_id, species in SPECIES.items():
        lines.append(asp.fact("species", species_id))
        lines.append(asp.fact("defended", species_id))
        lines.append(asp.fact("defense", species_id, species.defense))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        if method.direct_touch:
            lines.append(asp.fact("direct_touch", method_id))
    for gear_id, gear in GEARS.items():
        lines.append(asp.fact("gear", gear_id))
        for guard in sorted(gear.guards):
            lines.append(asp.fact("guards", gear_id, guard))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate children, a tide-pool species, and the safer habit of using a mitt."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--helper", choices=["mother", "father", "ranger"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.species and args.method:
        species = SPECIES[args.species]
        method = METHODS[args.method]
        if not hazard_at_risk(species, method):
            raise StoryError(explain_rejection(species, method))
    if args.gear and args.species:
        msg = explain_gear(SPECIES[args.species], args.gear)
        if msg:
            raise StoryError(msg)

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.species is None or combo[1] == args.species)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, species_id, method_id = rng.choice(sorted(combos))
    species = SPECIES[species_id]
    default_gear = select_gear(species)
    if default_gear is None:
        raise StoryError("(No safe gear exists for this species.)")
    gear_id = args.gear or default_gear.id
    if species.defense not in GEARS[gear_id].guards:
        raise StoryError(explain_gear(species, gear_id))

    instigator_gender = rng.choice(["girl", "boy"])
    cautioner_gender = rng.choice(["girl", "boy"])
    instigator_name = pick_name(rng, instigator_gender)
    cautioner_name = pick_name(rng, cautioner_gender, avoid=instigator_name)
    helper = args.helper or rng.choice(["mother", "father", "ranger"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme_id,
        species=species_id,
        method=method_id,
        gear=gear_id,
        instigator=instigator_name,
        instigator_gender=instigator_gender,
        cautioner=cautioner_name,
        cautioner_gender=cautioner_gender,
        helper=helper,
        trait=trait,
        relation=relation,
        instigator_age=ages[0],
        cautioner_age=ages[1],
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Invalid theme: {params.theme})")
    if params.species not in SPECIES:
        raise StoryError(f"(Invalid species: {params.species})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")
    if params.gear not in GEARS:
        raise StoryError(f"(Invalid gear: {params.gear})")

    species = SPECIES[params.species]
    method = METHODS[params.method]
    if not hazard_at_risk(species, method):
        raise StoryError(explain_rejection(species, method))
    if species.defense not in GEARS[params.gear].guards:
        raise StoryError(explain_gear(species, params.gear))

    world = tell(
        theme=THEMES[params.theme],
        species=species,
        method=method,
        gear=GEARS[params.gear],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        helper_type=params.helper,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
    )

    story = world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner)
    story = story.replace("helper", world.get("helper").label_word)
    story = story.replace("  ", " ")

    return StorySample(
        params=params,
        story=story,
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatch = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, species, method) combos:\n")
        for theme, species, method in combos:
            print(f"  {theme:8} {species:12} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.instigator} & {p.cautioner}: {p.species} with {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
