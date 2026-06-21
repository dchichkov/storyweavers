#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/night_damp_land_quest_twist_fable.py
===============================================================

A standalone storyworld about a small creature on a night quest across damp
ground, looking for safe land where a precious seed can be planted. The fable's
twist is that the frightening shape or glow in the dark is not a danger at all,
but a helper.

The world model tracks physical state (wetness, safety, plantedness) and
emotional state (fear, hope, trust, humility). The story is rendered from that
state, not from slot-swapped fixed prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/night_damp_land_quest_twist_fable.py
    python storyworlds/worlds/gpt-5.4/night_damp_land_quest_twist_fable.py --land bog_bank
    python storyworlds/worlds/gpt-5.4/night_damp_land_quest_twist_fable.py --helper owl
    python storyworlds/worlds/gpt-5.4/night_damp_land_quest_twist_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/night_damp_land_quest_twist_fable.py --all --qa
    python storyworlds/worlds/gpt-5.4/night_damp_land_quest_twist_fable.py --trace
    python storyworlds/worlds/gpt-5.4/night_damp_land_quest_twist_fable.py --verify
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

# Make the shared result containers importable when this script is run directly:
# this file lives under storyworlds/worlds/gpt-5.4/, so the package dir is three
# levels up.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe"}
        male = {"boy", "father", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class SeekerCfg:
    id: str
    type: str
    title: str
    gait: str
    home: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SeedCfg:
    id: str
    label: str
    phrase: str
    future: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LandCfg:
    id: str
    label: str
    phrase: str
    terrain: str
    dryness: int
    safe_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    eerie: str
    reveal: str
    voice: str
    terrains: set[str] = field(default_factory=set)
    sense: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class TraitCfg:
    id: str
    trusting: bool
    humility: int
    caution: int
    flavor: str
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


def _r_damp(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    seed = world.get("seed")
    land = world.get("land")
    if seeker.meters["travel"] < THRESHOLD:
        return out
    if land.meters["dryness"] >= 2:
        return out
    sig = ("damp_seed", int(seeker.meters["travel"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.meters["damp"] += 1
    seeker.memes["worry"] += 1
    out.append("__damp__")
    return out


def _r_scare(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    helper = world.get("helper")
    if helper.memes["misread"] < THRESHOLD:
        return out
    sig = ("fear", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["fear"] += 1
    out.append("__fear__")
    return out


def _r_plant(world: World) -> list[str]:
    out: list[str] = []
    seed = world.get("seed")
    land = world.get("land")
    if seed.meters["carried"] < THRESHOLD or land.meters["reached"] < THRESHOLD:
        return out
    if seed.meters["damp"] >= 2:
        return out
    sig = ("planted", land.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.meters["planted"] += 1
    seeker = world.get("seeker")
    seeker.memes["hope"] += 1
    out.append("__planted__")
    return out


CAUSAL_RULES = [
    Rule(name="damp_seed", tag="physical", apply=_r_damp),
    Rule(name="fear_from_misread", tag="emotional", apply=_r_scare),
    Rule(name="plant_if_ready", tag="physical", apply=_r_plant),
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
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def helper_can_guide(helper: HelperCfg, land: LandCfg) -> bool:
    return land.terrain in helper.terrains


def land_is_worth_quest(land: LandCfg) -> bool:
    return land.dryness >= 2


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for helper_id, helper in HELPERS.items():
        if helper.sense < SENSE_MIN:
            continue
        for land_id, land in LANDS.items():
            if land_is_worth_quest(land) and helper_can_guide(helper, land):
                combos.append((helper_id, land_id))
    return combos


def trusts_helper(trait: TraitCfg, delay: int) -> bool:
    return trait.trusting and (trait.humility - delay) >= 1


def outcome_of(params: "StoryParams") -> str:
    trait = TRAITS[params.trait]
    seed = SEEDS[params.seed_kind]
    land = LANDS[params.land]
    helper = HELPERS[params.helper]
    if not helper_can_guide(helper, land) or not land_is_worth_quest(land):
        raise StoryError("(No outcome: this helper-land pair is not a reasonable story.)")
    if trusts_helper(trait, params.delay):
        return "thrived"
    if params.delay >= 2:
        return "saved_for_morning"
    if land.dryness >= 3 and helper.sense >= 3:
        return "saved_for_morning"
    return "saved_for_morning"


def predict_path(world: World) -> dict:
    sim = world.copy()
    seeker = sim.get("seeker")
    helper = sim.get("helper")
    land = sim.get("land")
    helper_cfg = sim.facts["helper_cfg"]
    land_cfg = sim.facts["land_cfg"]
    helper.memes["misread"] += 1
    propagate(sim, narrate=False)
    seeker.meters["travel"] += 1
    if helper_can_guide(helper_cfg, land_cfg):
        land.meters["reached"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": seeker.memes["fear"],
        "damp": sim.get("seed").meters["damp"],
        "reached": land.meters["reached"],
    }


def introduce(world: World, seeker: Entity, seed: Entity, night_word: str) -> None:
    world.say(
        f"On a {night_word} night, {seeker.id} the {seeker.type} stood by {seeker.attrs['home']} "
        f"with {seed.phrase} tucked close."
    )
    world.say(
        f"{seeker.pronoun().capitalize()} had found it before sunset and believed it might one day become {world.facts['seed_cfg'].future}."
    )


def need(world: World, seeker: Entity, land: Entity) -> None:
    seeker.memes["care"] += 1
    world.say(
        f"But the field was already damp, and the low ground shone with cold beads of water. "
        f'"This seed needs dry land," {seeker.pronoun()} whispered. "I must find {land.phrase} before the dark grows heavier."'
    )


def begin_quest(world: World, seeker: Entity) -> None:
    seeker.meters["travel"] += 1
    seeker.memes["quest"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {seeker.id} set out over the sleeping land, step by careful step, making a little quest of one honest promise."
    )


def glimpse_helper(world: World, seeker: Entity, helper: Entity, helper_cfg: HelperCfg) -> None:
    helper.memes["misread"] += 1
    propagate(world, narrate=False)
    world.say(
        f"After a while, {seeker.id} saw {helper_cfg.eerie} moving ahead. In the dark it looked so strange that {seeker.pronoun()} stopped at once."
    )
    if seeker.memes["fear"] >= THRESHOLD:
        world.say(
            f"{seeker.pronoun().capitalize()} felt fear prickle through {seeker.pronoun('possessive')} paws and wondered whether the night itself had grown eyes."
        )


def warning(world: World, seeker: Entity, helper_cfg: HelperCfg) -> None:
    pred = predict_path(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_damp"] = pred["damp"]
    world.say(
        f'Then a small voice said, "{helper_cfg.voice}" The words were gentle, but they came from the very shape that had frightened {seeker.id}.'
    )


def refuse_path(world: World, seeker: Entity, seed: Entity, delay: int) -> None:
    seeker.memes["pride"] += 1
    seeker.meters["travel"] += 1 + delay
    seed.meters["carried"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I can manage alone," said {seeker.id}, and {seeker.pronoun()} hurried on without listening.'
    )
    if seed.meters["damp"] >= THRESHOLD:
        world.say(
            f"But the ground was wet in hidden places, and a chill crept into the little seed bundle as {seeker.pronoun()} wandered."
        )


def follow_path(world: World, seeker: Entity, helper: Entity, land: Entity,
                helper_cfg: HelperCfg, delay: int) -> None:
    seeker.memes["trust"] += 1
    seeker.memes["humility"] += 1
    helper.memes["kindness"] += 1
    seeker.meters["travel"] += 1 + delay
    land.meters["reached"] += 1
    world.get("seed").meters["carried"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{seeker.id} took a breath and answered, "Then show me."'
    )
    world.say(
        f"{helper_cfg.reveal} went ahead, and {seeker.id} followed over the safer ground until {land.phrase} rose out of the dark."
    )


def reveal_twist(world: World, seeker: Entity, helper_cfg: HelperCfg) -> None:
    seeker.memes["fear"] = 0.0
    seeker.memes["relief"] += 1
    world.say(
        f"Only then did {seeker.id} understand the twist of the night: the thing {seeker.pronoun()} had feared was not a danger at all, but a friend."
    )


def plant_seed(world: World, seeker: Entity, seed: Entity, land_cfg: LandCfg) -> None:
    world.get("land").meters["reached"] += 1
    seed.meters["carried"] += 1
    propagate(world, narrate=False)
    if seed.meters["planted"] >= THRESHOLD:
        seeker.memes["gratitude"] += 1
        world.say(
            f"On that high patch of land, {seeker.id} pressed the seed into the earth where the soil was cool but not soaking."
        )
        world.say(
            f"{land_cfg.safe_line} Soon {seed.label} was resting where it could wait for morning without drowning."
        )


def save_for_morning(world: World, seeker: Entity, seed: Entity, helper_cfg: HelperCfg, land_cfg: LandCfg) -> None:
    seed.meters["saved"] += 1
    seeker.memes["lesson"] += 1
    seeker.memes["gratitude"] += 1
    world.get("land").meters["reached"] += 1
    world.say(
        f"When {seeker.id} finally reached {land_cfg.phrase}, {seed.phrase} had grown too damp for planting that night."
    )
    world.say(
        f'But {helper_cfg.label} said, "Dry it by your heart till sunrise, and begin again when the world is kinder."'
    )
    world.say(
        f"So {seeker.id} tucked the seed into warm fur and sat quietly on the higher land, wiser than when the quest began."
    )


def ending(world: World, seeker: Entity, helper_cfg: HelperCfg, land_cfg: LandCfg, outcome: str) -> None:
    if outcome == "thrived":
        world.say(
            f"Before sleep took the meadow, {seeker.id} thanked the {helper_cfg.label}. {land_cfg.ending_image}"
        )
        world.say(
            "And that is why some travelers learn, even in the dark, that a humble ear can find the safest road."
        )
    else:
        world.say(
            f"Before dawn, {seeker.id} thanked the {helper_cfg.label} anyway, for help offered late is still kinder than pride."
        )
        world.say(
            "And that is why wise creatures do not let fear or stubbornness walk ahead of them on a damp night."
        )


def tell(seeker_cfg: SeekerCfg, seed_cfg: SeedCfg, helper_cfg: HelperCfg, land_cfg: LandCfg,
         trait_cfg: TraitCfg, delay: int, name: str) -> World:
    world = World()
    seeker = world.add(Entity(
        id=name,
        kind="character",
        type=seeker_cfg.type,
        label=seeker_cfg.title,
        phrase=f"{name} the {seeker_cfg.type}",
        role="seeker",
        traits=[trait_cfg.id],
        attrs={"home": seeker_cfg.home, "gait": seeker_cfg.gait},
        tags=set(seeker_cfg.tags) | set(trait_cfg.tags),
    ))
    seed = world.add(Entity(
        id="seed",
        kind="thing",
        type="seed",
        label=seed_cfg.label,
        phrase=seed_cfg.phrase,
        role="burden",
        tags=set(seed_cfg.tags),
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="helper",
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        tags=set(helper_cfg.tags),
    ))
    land = world.add(Entity(
        id="land",
        kind="thing",
        type="land",
        label=land_cfg.label,
        phrase=land_cfg.phrase,
        role="destination",
        tags=set(land_cfg.tags),
    ))
    land.meters["dryness"] = float(land_cfg.dryness)
    seed.meters["carried"] += 1
    seeker.memes["humility"] = float(trait_cfg.humility)
    seeker.memes["caution"] = float(trait_cfg.caution)

    world.facts.update(
        seeker=seeker,
        seed=seed,
        helper=helper,
        land=land,
        seeker_cfg=seeker_cfg,
        seed_cfg=seed_cfg,
        helper_cfg=helper_cfg,
        land_cfg=land_cfg,
        trait_cfg=trait_cfg,
        delay=delay,
    )

    introduce(world, seeker, seed, "moonlit")
    need(world, seeker, land)

    world.para()
    begin_quest(world, seeker)
    glimpse_helper(world, seeker, helper, helper_cfg)
    warning(world, seeker, helper_cfg)

    trusted = trusts_helper(trait_cfg, delay)
    world.facts["trusted"] = trusted

    world.para()
    if trusted:
        follow_path(world, seeker, helper, land, helper_cfg, delay)
        reveal_twist(world, seeker, helper_cfg)
        plant_seed(world, seeker, seed, land_cfg)
        outcome = "thrived" if seed.meters["planted"] >= THRESHOLD else "saved_for_morning"
        if outcome != "thrived":
            save_for_morning(world, seeker, seed, helper_cfg, land_cfg)
    else:
        refuse_path(world, seeker, seed, delay)
        reveal_twist(world, seeker, helper_cfg)
        save_for_morning(world, seeker, seed, helper_cfg, land_cfg)
        outcome = "saved_for_morning"

    world.para()
    ending(world, seeker, helper_cfg, land_cfg, outcome)

    world.facts.update(
        outcome=outcome,
        planted=seed.meters["planted"] >= THRESHOLD,
        damp=seed.meters["damp"],
    )
    return world


KNOWLEDGE = {
    "night": [(
        "Why can things look different at night?",
        "At night there is less light, so shapes and shadows are harder to understand. A harmless thing can seem scary until you see it clearly."
    )],
    "damp": [(
        "What does damp mean?",
        "Damp means a little wet, not dripping but not dry either. Damp ground can slowly soak into seeds, fur, paper, or cloth."
    )],
    "land": [(
        "Why is high land often drier than low ground?",
        "Water runs downhill, so little hollows and low ground stay wetter. A small rise of land can stay safer and drier."
    )],
    "seed": [(
        "What does a seed need to grow well?",
        "A seed needs the right mix of soil, water, and air. Too much wetness all at once can make it rot instead of sprout."
    )],
    "firefly": [(
        "What is a firefly?",
        "A firefly is a small insect that can glow. Its little light can help another creature notice where to go."
    )],
    "frog": [(
        "Why would a frog know the wet ground well?",
        "Frogs live close to wet places, so they know where puddles, reeds, and safe stepping spots are. What feels ordinary to one creature can help another."
    )],
    "owl": [(
        "Why can an owl move well at night?",
        "Owls can see and hear very well in the dark. That helps them notice paths and shapes when other creatures feel unsure."
    )],
    "humility": [(
        "Why is it wise to accept help sometimes?",
        "Another creature may know something you do not. Listening can save time, trouble, and hurt feelings."
    )],
    "twist": [(
        "What is a twist in a story?",
        "A twist is a surprise that changes what you thought was happening. It can turn fear into understanding."
    )],
}
KNOWLEDGE_ORDER = ["night", "damp", "land", "seed", "firefly", "frog", "owl", "humility", "twist"]


SEEKERS = {
    "mouse": SeekerCfg(
        id="mouse",
        type="mouse",
        title="field mouse",
        gait="quick little steps",
        home="a root under the hedge",
        tags={"night", "land"},
    ),
    "hedgehog": SeekerCfg(
        id="hedgehog",
        type="hedgehog",
        title="hedgehog",
        gait="small sturdy steps",
        home="a nest of leaves by the stone wall",
        tags={"night", "land"},
    ),
    "rabbit": SeekerCfg(
        id="rabbit",
        type="rabbit",
        title="young rabbit",
        gait="soft hopping steps",
        home="a burrow near the clover patch",
        tags={"night", "land"},
    ),
}

SEEDS = {
    "bean": SeedCfg(
        id="bean",
        label="bean seed",
        phrase="a pale bean seed",
        future="a climbing vine with green pods",
        tags={"seed"},
    ),
    "acorn": SeedCfg(
        id="acorn",
        label="acorn",
        phrase="a round brown acorn",
        future="a great oak with room for nests and shade",
        tags={"seed"},
    ),
    "wheat": SeedCfg(
        id="wheat",
        label="grain of wheat",
        phrase="a single grain of wheat",
        future="a waving stalk with golden heads",
        tags={"seed"},
    ),
}

LANDS = {
    "hillock": LandCfg(
        id="hillock",
        label="hillock",
        phrase="a little hillock above the meadow",
        terrain="open",
        dryness=3,
        safe_line="There the damp could not gather in a puddle around it.",
        ending_image="A silver line of dawn touched the hillock, and the little patch of earth looked ready to keep a promise.",
        tags={"land", "damp"},
    ),
    "stump": LandCfg(
        id="stump",
        label="old stump",
        phrase="the old stump on the high side of the field",
        terrain="woods",
        dryness=2,
        safe_line="Its cracked earth held the seed above the slick grass below.",
        ending_image="By the stump, the first birds began to sing, and the earth looked firm enough for hope.",
        tags={"land", "damp"},
    ),
    "stone_rise": LandCfg(
        id="stone_rise",
        label="stone rise",
        phrase="a flat rise of land beside the stones",
        terrain="open",
        dryness=2,
        safe_line="The ground there was plain and firm, with no cold shine of soaking water.",
        ending_image="The stone rise waited under the paling sky like a quiet little island of safety.",
        tags={"land", "damp"},
    ),
    "bog_bank": LandCfg(
        id="bog_bank",
        label="bog bank",
        phrase="the low bank by the bog",
        terrain="marsh",
        dryness=0,
        safe_line="But the mud there held water in every print.",
        ending_image="The bog bank stayed black and shining, a poor cradle for any seed.",
        tags={"land", "damp"},
    ),
}

HELPERS = {
    "firefly": HelperCfg(
        id="firefly",
        label="firefly",
        phrase="a bright little firefly",
        eerie="a green wink of light",
        reveal="The tiny firefly",
        voice="Follow the places that do not shine, and your feet will stay on the drier path.",
        terrains={"open"},
        sense=3,
        tags={"firefly", "night", "twist"},
    ),
    "frog": HelperCfg(
        id="frog",
        label="frog",
        phrase="a mossy frog",
        eerie="two wet bright eyes near the reeds",
        reveal="The frog with the wet bright eyes",
        voice="I know which clumps hold and which ones sink. Step where I step.",
        terrains={"marsh"},
        sense=3,
        tags={"frog", "night", "twist"},
    ),
    "owl": HelperCfg(
        id="owl",
        label="owl",
        phrase="a small brown owl",
        eerie="a round shadow with moonlit eyes",
        reveal="The little owl",
        voice="From above I can see the higher ground. Trust the places I point to.",
        terrains={"open", "woods"},
        sense=3,
        tags={"owl", "night", "twist"},
    ),
    "mole": HelperCfg(
        id="mole",
        label="mole",
        phrase="a sleepy mole",
        eerie="a bump of earth that suddenly moved",
        reveal="The mole",
        voice="I know tunnels, not moon paths. I would only slow you down tonight.",
        terrains={"woods"},
        sense=1,
        tags={"night"},
    ),
}

TRAITS = {
    "humble": TraitCfg(
        id="humble",
        trusting=True,
        humility=3,
        caution=2,
        flavor="humble and steady",
        tags={"humility"},
    ),
    "proud": TraitCfg(
        id="proud",
        trusting=False,
        humility=0,
        caution=1,
        flavor="quick and proud",
        tags=set(),
    ),
    "careful": TraitCfg(
        id="careful",
        trusting=True,
        humility=2,
        caution=3,
        flavor="careful and thoughtful",
        tags={"humility"},
    ),
}


@dataclass
class StoryParams:
    seeker: str
    seed_kind: str
    helper: str
    land: str
    trait: str
    delay: int = 0
    name: str = "Pip"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        seeker="mouse",
        seed_kind="bean",
        helper="firefly",
        land="hillock",
        trait="humble",
        delay=0,
        name="Pip",
    ),
    StoryParams(
        seeker="rabbit",
        seed_kind="acorn",
        helper="owl",
        land="stump",
        trait="careful",
        delay=1,
        name="Moss",
    ),
    StoryParams(
        seeker="hedgehog",
        seed_kind="wheat",
        helper="owl",
        land="stone_rise",
        trait="proud",
        delay=2,
        name="Bramble",
    ),
    StoryParams(
        seeker="mouse",
        seed_kind="acorn",
        helper="frog",
        land="bog_bank",
        trait="humble",
        delay=0,
        name="Pip",
    ),
]


def explain_rejection(helper: HelperCfg, land: LandCfg) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: {helper.label} is known here, but not as a sensible night guide. "
            f"Pick a helper like firefly, frog, or owl.)"
        )
    if not land_is_worth_quest(land):
        return (
            f"(No story: {land.phrase} is too wet to solve the problem. A quest for dry land "
            f"needs a destination that is actually dry enough.)"
        )
    return (
        f"(No story: {helper.label} does not know how to guide a traveler to {land.phrase} at night. "
        f"Choose a helper whose skills fit that ground.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    seed = f["seed_cfg"]
    helper = f["helper_cfg"]
    land = f["land_cfg"]
    outcome = f["outcome"]
    if outcome == "thrived":
        return [
            f'Write a short fable for a 3-to-5-year-old that includes the words "night", "damp", and "land".',
            f"Tell a quest story where {seeker.id} carries {seed.phrase} through the night looking for dry land, and the frightening figure in the dark turns out to be a helpful {helper.label}.",
            "Write a gentle animal fable with a twist: what looks scary in the dark becomes the guide that leads to safety.",
        ]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "night", "damp", and "land".',
        f"Tell a quest story where {seeker.id} carries {seed.phrase} across damp land at night, misjudges a {helper.label}, and learns a lesson about asking for help.",
        "Write a gentle fable with a twist in which a traveler fears the dark, reaches higher land at last, and ends wiser than before.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    seed = f["seed_cfg"]
    helper = f["helper_cfg"]
    land = f["land_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id} the {seeker.type}, who carried {seed.phrase} across the night. The quest began because the ground below was damp and the seed needed safer land."
        ),
        (
            f"Why did {seeker.id} leave home at night?",
            f"{seeker.id} believed the seed might one day grow into {seed.future}, so {seeker.pronoun()} did not want the damp ground to spoil it. That is why {seeker.pronoun()} went looking for higher land before morning."
        ),
        (
            f"What frightened {seeker.id} in the dark?",
            f"{seeker.id} first saw {helper.eerie}, and in the dark it looked strange and scary. The fear came from not knowing what the shape really was."
        ),
        (
            "What was the twist in the story?",
            f"The twist was that the frightening thing was really a helpful {helper.label}. What seemed like a danger became the guide."
        ),
    ]
    if f.get("trusted"):
        qa.append((
            f"How did {seeker.id} solve the problem?",
            f"{seeker.id} listened to the {helper.label} and followed the safer path to {land.phrase}. Because {seeker.pronoun()} accepted help early enough, the seed could be planted before too much damp reached it."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the seed resting safely on higher land. The ending shows that humility changed the night from something frightening into something hopeful."
        ))
    else:
        qa.append((
            f"Why was the seed not planted that night?",
            f"{seeker.id} tried to manage alone first, so the quest took longer and the seed grew too damp. By the time {seeker.pronoun()} reached {land.phrase}, it was better to wait for morning than force it into wet ground."
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly, with {seeker.id} keeping the seed warm and learning to listen sooner next time. The higher land still mattered, because it gave {seeker.pronoun()} a safe place to wait and think."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"night", "damp", "land", "seed", "twist"}
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["trait_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_helper(H) :- helper(H), sense(H,S), sense_min(M), S >= M.
worthy_land(L) :- land(L), dryness(L,D), D >= 2.
compatible(H,L) :- sensible_helper(H), worthy_land(L), guides(H,T), terrain(L,T).

trusts :- chosen_trait(T), trusting(T), humility(T,H), delay(D), H - D >= 1.

outcome(thrived) :- trusts.
outcome(saved_for_morning) :- not trusts.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for seeker_id in SEEKERS:
        lines.append(asp.fact("seeker", seeker_id))
    for seed_id in SEEDS:
        lines.append(asp.fact("seed_kind", seed_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        for terrain in sorted(helper.terrains):
            lines.append(asp.fact("guides", helper_id, terrain))
    for land_id, land in LANDS.items():
        lines.append(asp.fact("land", land_id))
        lines.append(asp.fact("terrain", land_id, land.terrain))
        lines.append(asp.fact("dryness", land_id, land.dryness))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        if trait.trusting:
            lines.append(asp.fact("trusting", trait_id))
        lines.append(asp.fact("humility", trait_id, trait.humility))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: helper-land gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid helper-land pairs:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = []
    for params in CURATED:
        if params.helper in HELPERS and params.land in LANDS:
            if helper_can_guide(HELPERS[params.helper], LANDS[params.land]) and land_is_worth_quest(LANDS[params.land]):
                cases.append(params)
    for s in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a night quest across damp land with a fable twist."
    )
    ap.add_argument("--seeker", choices=SEEKERS)
    ap.add_argument("--seed-kind", choices=SEEDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--land", choices=LANDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2],
                    help="extra hesitation before the seeker commits to a path")
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible helper-land pairs derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_rejection(HELPERS[args.helper], next(iter(LANDS.values()))))
    if args.land and not land_is_worth_quest(LANDS[args.land]):
        helper = HELPERS[args.helper] if args.helper else next(h for h in HELPERS.values() if h.sense >= SENSE_MIN)
        raise StoryError(explain_rejection(helper, LANDS[args.land]))
    if args.helper and args.land:
        helper = HELPERS[args.helper]
        land = LANDS[args.land]
        if not (land_is_worth_quest(land) and helper_can_guide(helper, land) and helper.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(helper, land))

    combos = [c for c in valid_combos()
              if (args.helper is None or c[0] == args.helper)
              and (args.land is None or c[1] == args.land)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    helper_id, land_id = rng.choice(sorted(combos))
    seeker_id = args.seeker or rng.choice(sorted(SEEKERS))
    seed_kind = args.seed_kind or rng.choice(sorted(SEEDS))
    trait_id = args.trait or rng.choice(sorted(TRAITS))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    default_names = ["Pip", "Moss", "Bramble", "Nettle", "Fern", "Pebble"]
    name = args.name or rng.choice(default_names)
    return StoryParams(
        seeker=seeker_id,
        seed_kind=seed_kind,
        helper=helper_id,
        land=land_id,
        trait=trait_id,
        delay=delay,
        name=name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        seeker_cfg = SEEKERS[params.seeker]
        seed_cfg = SEEDS[params.seed_kind]
        helper_cfg = HELPERS[params.helper]
        land_cfg = LANDS[params.land]
        trait_cfg = TRAITS[params.trait]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if helper_cfg.sense < SENSE_MIN or not land_is_worth_quest(land_cfg) or not helper_can_guide(helper_cfg, land_cfg):
        raise StoryError(explain_rejection(helper_cfg, land_cfg))

    world = tell(
        seeker_cfg=seeker_cfg,
        seed_cfg=seed_cfg,
        helper_cfg=helper_cfg,
        land_cfg=land_cfg,
        trait_cfg=trait_cfg,
        delay=params.delay,
        name=params.name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("", "#show compatible/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (helper, land) pairs:\n")
        for helper_id, land_id in combos:
            print(f"  {helper_id:8} {land_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            try:
                sample = generate(params)
            except StoryError:
                continue
            samples.append(sample)
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.helper} to {p.land} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
