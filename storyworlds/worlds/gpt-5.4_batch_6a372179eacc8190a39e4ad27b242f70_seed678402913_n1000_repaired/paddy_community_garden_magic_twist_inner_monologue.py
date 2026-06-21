#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/paddy_community_garden_magic_twist_inner_monologue.py
================================================================================

A standalone story world about Paddy in a community garden at dusk.

This tiny domain models one bedtime-shaped problem: Paddy finds his little garden
bed in trouble, discovers a magical tool, and first hopes the magic will fix his
own patch at once. The twist is that the tool only wakes for shared care. When
Paddy helps a neighbor's bed first, the charm glows, the garden changes, and
Paddy learns that the strongest magic in the community garden is kindness.

Run it
------
    python storyworlds/worlds/gpt-5.4/paddy_community_garden_magic_twist_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/paddy_community_garden_magic_twist_inner_monologue.py --crop lettuce --trouble thirsty --charm moon_can
    python storyworlds/worlds/gpt-5.4/paddy_community_garden_magic_twist_inner_monologue.py --crop peas --trouble chilly
    python storyworlds/worlds/gpt-5.4/paddy_community_garden_magic_twist_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/paddy_community_garden_magic_twist_inner_monologue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/paddy_community_garden_magic_twist_inner_monologue.py --trace
    python storyworlds/worlds/gpt-5.4/paddy_community_garden_magic_twist_inner_monologue.py --json
    python storyworlds/worlds/gpt-5.4/paddy_community_garden_magic_twist_inner_monologue.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Crop:
    id: str
    label: str
    phrase: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    need: str
    symptom: str
    thought: str
    share_action: str
    own_action: str
    healed: str
    neighbor_result: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    first_glow: str = ""
    awake_glow: str = ""
    hint: str = ""
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


def _r_plot_distress(world: World) -> list[str]:
    out: list[str] = []
    paddy = world.get("Paddy")
    for plot_id in ("own_plot", "neighbor_plot"):
        plot = world.get(plot_id)
        crop = world.get(plot.attrs["crop"])
        need = plot.attrs.get("need", "")
        if not need or plot.meters[need] < THRESHOLD:
            continue
        sig = ("distress", plot_id, need)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        crop.meters["distress"] += 1
        crop.meters[need] += 1
        if plot_id == "own_plot":
            paddy.memes["worry"] += 1
        out.append("__distress__")
    return out


def _r_shared_care_wakes_charm(world: World) -> list[str]:
    paddy = world.get("Paddy")
    neighbor_plot = world.get("neighbor_plot")
    charm = world.get("charm")
    if paddy.memes["kindness"] < THRESHOLD or neighbor_plot.meters["helped"] < THRESHOLD:
        return []
    if charm.meters["awake"] >= THRESHOLD:
        return []
    charm.meters["awake"] += 1
    paddy.memes["wonder"] += 1
    return ["__awake__"]


def _r_healed_plot_thrives(world: World) -> list[str]:
    out: list[str] = []
    paddy = world.get("Paddy")
    for plot_id in ("own_plot", "neighbor_plot"):
        plot = world.get(plot_id)
        crop = world.get(plot.attrs["crop"])
        need = plot.attrs.get("need", "")
        if not need or plot.meters[need] >= THRESHOLD:
            continue
        if plot.meters["cared_for"] < THRESHOLD:
            continue
        sig = ("thriving", plot_id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        crop.meters["thriving"] += 1
        crop.meters["distress"] = 0.0
        if plot_id == "own_plot":
            paddy.memes["relief"] += 1
            paddy.memes["joy"] += 1
        out.append("__thriving__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="plot_distress", tag="physical", apply=_r_plot_distress),
    Rule(name="shared_care_wakes_charm", tag="magic", apply=_r_shared_care_wakes_charm),
    Rule(name="healed_plot_thrives", tag="physical", apply=_r_healed_plot_thrives),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


CROPS = {
    "lettuce": Crop(
        id="lettuce",
        label="lettuce",
        phrase="a row of little lettuce",
        needs={"water"},
        tags={"lettuce", "water", "garden"},
    ),
    "basil": Crop(
        id="basil",
        label="basil",
        phrase="a neat patch of basil",
        needs={"water", "warmth"},
        tags={"basil", "water", "warmth", "garden"},
    ),
    "peas": Crop(
        id="peas",
        label="peas",
        phrase="a row of climbing peas",
        needs={"support"},
        tags={"peas", "support", "garden"},
    ),
    "tomatoes": Crop(
        id="tomatoes",
        label="tomatoes",
        phrase="two brave tomato plants",
        needs={"support", "water"},
        tags={"tomato", "support", "water", "garden"},
    ),
    "seedlings": Crop(
        id="seedlings",
        label="seedlings",
        phrase="a tray of tiny seedlings",
        needs={"warmth", "water"},
        tags={"seedlings", "warmth", "water", "garden"},
    ),
}

TROUBLES = {
    "thirsty": Trouble(
        id="thirsty",
        need="water",
        symptom="looked droopy and dry",
        thought="What if my little plants stay thirsty all night?",
        share_action="tilted a slow silver drink over {crop}",
        own_action="tilted a slow silver drink over {crop}",
        healed="{crop} lifted its leaves as if it had remembered a song",
        neighbor_result="{crop} stopped drooping and smelled fresh again",
        lesson="Some growing things need a careful drink before they can stand tall again.",
        tags={"water", "plants"},
    ),
    "slumping": Trouble(
        id="slumping",
        need="support",
        symptom="leaned sideways in the dusk",
        thought="Oh dear, what if the stems snap before morning?",
        share_action="looped soft silver twine around {crop} and the little stake beside it",
        own_action="looped soft silver twine around {crop} and its waiting stake",
        healed="{crop} stood straighter, as if the night itself were holding it up",
        neighbor_result="{crop} stopped wobbling and stood neatly in line",
        lesson="Some tall plants grow best when a steady support helps them climb.",
        tags={"support", "plants"},
    ),
    "chilly": Trouble(
        id="chilly",
        need="warmth",
        symptom="shivered in the cool evening air",
        thought="Maybe the night is too cold for such tiny leaves.",
        share_action="set the little starry cover over {crop}",
        own_action="set the little starry cover over {crop}",
        healed="{crop} uncurled in the gentle warmth and looked ready for dreaming",
        neighbor_result="{crop} no longer trembled in the evening breeze",
        lesson="Young plants can need a little warmth when the air turns cool.",
        tags={"warmth", "plants"},
    ),
}

CHARMS = {
    "moon_can": Charm(
        id="moon_can",
        label="moon watering can",
        phrase="a moon watering can no bigger than a teapot",
        fixes={"water"},
        first_glow="It only gave one pale blink, and then it went still in his hands.",
        awake_glow="Silver drops shimmered from its spout like tiny moons.",
        hint="The scratched stars on the side seemed to whisper, Share first.",
        tags={"watering_can", "water", "magic"},
    ),
    "silver_twine": Charm(
        id="silver_twine",
        label="silver twine",
        phrase="a spool of silver twine that glittered like spider silk",
        fixes={"support"},
        first_glow="The twine flashed once and then sagged softly, as plain as string.",
        awake_glow="The silver thread lifted lightly and curled where kind hands were needed.",
        hint="The tiny knot at the end seemed to whisper, Help the next bed too.",
        tags={"twine", "support", "magic"},
    ),
    "star_cloche": Charm(
        id="star_cloche",
        label="starry cloche",
        phrase="a little glass cloche dotted with sleepy stars",
        fixes={"warmth"},
        first_glow="The stars inside it dimmed, as if they were waiting for something better.",
        awake_glow="Warm pinpricks of light glowed under the glass like a pocket sky.",
        hint="The stars seemed to murmur, Warm another patch before your own.",
        tags={"cloche", "warmth", "magic"},
    ),
}

HELPER_NAMES = {
    "girl": ["Nia", "Maya", "Ruby", "Tess"],
    "boy": ["Owen", "Benji", "Theo", "Jude"],
    "woman": ["Mrs. Vale", "Auntie June", "Ms. Poppy"],
    "man": ["Mr. Reed", "Uncle Ash", "Mr. Rowan"],
}

PARENT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for crop_id, crop in CROPS.items():
        for trouble_id, trouble in TROUBLES.items():
            if trouble.need not in crop.needs:
                continue
            for charm_id, charm in CHARMS.items():
                if trouble.need not in charm.fixes:
                    continue
                for neighbor_id, neighbor_crop in CROPS.items():
                    if neighbor_id == crop_id:
                        continue
                    if trouble.need in neighbor_crop.needs:
                        combos.append((crop_id, trouble_id, charm_id, neighbor_id))
    return sorted(combos)


@dataclass
class StoryParams:
    crop: str
    trouble: str
    charm: str
    neighbor_crop: str
    helper_name: str
    helper_type: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        crop="lettuce",
        trouble="thirsty",
        charm="moon_can",
        neighbor_crop="basil",
        helper_name="Nia",
        helper_type="girl",
        parent="mother",
    ),
    StoryParams(
        crop="peas",
        trouble="slumping",
        charm="silver_twine",
        neighbor_crop="tomatoes",
        helper_name="Mr. Rowan",
        helper_type="man",
        parent="father",
    ),
    StoryParams(
        crop="seedlings",
        trouble="chilly",
        charm="star_cloche",
        neighbor_crop="basil",
        helper_name="Ruby",
        helper_type="girl",
        parent="mother",
    ),
    StoryParams(
        crop="tomatoes",
        trouble="thirsty",
        charm="moon_can",
        neighbor_crop="seedlings",
        helper_name="Auntie June",
        helper_type="woman",
        parent="father",
    ),
]


def explain_rejection(crop: Crop, trouble: Trouble, charm: Optional[Charm], neighbor: Optional[Crop]) -> str:
    if trouble.need not in crop.needs:
        return (
            f"(No story: {crop.phrase} would not normally have the '{trouble.id}' problem here. "
            f"This world only tells grounded garden stories where the crop's need matches the trouble.)"
        )
    if charm is not None and trouble.need not in charm.fixes:
        return (
            f"(No story: the {charm.label} does not solve a {trouble.id} patch. "
            f"Choose a charm that really helps with {trouble.need}.)"
        )
    if neighbor is not None and trouble.need not in neighbor.needs:
        return (
            f"(No story: the neighbor crop must be able to share the same need, but {neighbor.phrase} "
            f"does not fit a {trouble.id} twist in this world.)"
        )
    return "(No story: that combination is not supported in this world.)"


def helper_phrase(helper: Entity) -> str:
    if helper.type in {"girl", "boy"}:
        return helper.id
    return helper.id


def predict_direct_magic(world: World) -> dict:
    sim = world.copy()
    charm = sim.get("charm")
    own_plot = sim.get("own_plot")
    need = own_plot.attrs["need"]
    own_plot.meters["asked_for_magic"] += 1
    if charm.meters["awake"] >= THRESHOLD:
        own_plot.meters[need] = 0.0
        own_plot.meters["cared_for"] += 1
    propagate(sim, narrate=False)
    return {
        "fixed": own_plot.meters[need] < THRESHOLD,
        "awake": charm.meters["awake"] >= THRESHOLD,
    }


def introduce(world: World, crop: Crop, trouble: Trouble, helper: Entity, parent: Entity) -> None:
    paddy = world.get("Paddy")
    own_crop = world.get("own_crop")
    world.say(
        f"In the community garden, when the evening sky was turning soft and blue, "
        f"Paddy walked between the little beds with {parent.label_word}."
    )
    world.say(
        f"He always liked to check {own_crop.phrase} before going home, and tonight "
        f"{helper_phrase(helper)} was there too, minding the next bed over."
    )
    world.say(
        f"But Paddy stopped with a small catch in his breath. His {crop.label} {trouble.symptom}."
    )
    world.say(f'"{trouble.thought}" Paddy thought.')


def find_charm(world: World, charm: Charm) -> None:
    world.say(
        f"Near the rain barrel he spotted {charm.phrase}. It did not look like the sort "
        f"of thing that belonged in the tool shed at all."
    )
    world.say(
        f'Paddy looked around and thought, "Maybe this is real garden magic. Maybe it can help."'
    )


def try_own_first(world: World, trouble: Trouble, charm: Charm) -> None:
    own_crop = world.get("own_crop")
    own_plot = world.get("own_plot")
    paddy = world.get("Paddy")
    paddy.memes["impatience"] += 1
    own_plot.meters["asked_for_magic"] += 1
    pred = predict_direct_magic(world)
    world.facts["first_attempt_fixed"] = pred["fixed"]
    world.say(
        f"He reached for {own_crop.phrase} first and {trouble.own_action.format(crop=own_crop.phrase)}."
    )
    world.say(charm.first_glow)
    world.say(
        "Nothing in his own bed changed. The leaves and stems stayed exactly as worried as before."
    )


def hint(world: World, charm: Charm, helper: Entity) -> None:
    paddy = world.get("Paddy")
    paddy.memes["wonder"] += 1
    line = charm.hint
    if helper.type in {"girl", "boy"}:
        world.say(
            f"{helper.id} blinked at the charm and whispered, \"Maybe the garden wants everyone helped, not just one bed.\""
        )
    else:
        world.say(
            f'{helper.id} smiled in that quiet way grown-ups do and said, "Community gardens like shared hands best."'
        )
    world.say(line)
    world.say('"Oh," Paddy thought. "Maybe the magic is listening for kindness."')


def help_neighbor(world: World, trouble: Trouble, helper: Entity) -> None:
    paddy = world.get("Paddy")
    neighbor_plot = world.get("neighbor_plot")
    neighbor_crop = world.get("neighbor_crop")
    neighbor_plot.meters[neighbor_plot.attrs["need"]] = 0.0
    neighbor_plot.meters["helped"] += 1
    neighbor_plot.meters["cared_for"] += 1
    paddy.memes["kindness"] += 1
    helper.memes["gratitude"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So Paddy turned to the next bed and {trouble.share_action.format(crop=neighbor_crop.phrase)} first."
    )
    world.say(f"At once, {trouble.neighbor_result.format(crop=neighbor_crop.phrase)}.")
    world.say(
        f"{helper_phrase(helper)} smiled, and the whole corner of the community garden felt a little less lonely."
    )


def heal_own_plot(world: World, trouble: Trouble, charm: Charm) -> None:
    own_plot = world.get("own_plot")
    own_crop = world.get("own_crop")
    paddy = world.get("Paddy")
    if world.get("charm").meters["awake"] < THRESHOLD:
        raise StoryError("The charm never woke, so the story cannot reach its bedtime turn.")
    own_plot.meters[own_plot.attrs["need"]] = 0.0
    own_plot.meters["cared_for"] += 1
    propagate(world, narrate=False)
    paddy.memes["trust"] += 1
    world.say(charm.awake_glow)
    world.say(
        f"Then Paddy tried again and {trouble.own_action.format(crop=own_crop.phrase)}."
    )
    world.say(f"Soon {trouble.healed.format(crop=own_crop.phrase)}.")


def reveal_twist(world: World, trouble: Trouble, helper: Entity, parent: Entity) -> None:
    paddy = world.get("Paddy")
    paddy.memes["lesson"] += 1
    world.say(
        f'Paddy let out the breath he had been holding. "{helper_phrase(helper)} was right," he thought. '
        f'"The magic was never only for me."'
    )
    world.say(
        f"{parent.label_word.capitalize()} touched his shoulder and said, "
        f'"The loveliest gardens grow when neighbors care for one another."'
    )
    world.say(
        f"That was the twist Paddy carried home in his heart: the charm truly shone, "
        f"but it only woke when his hands chose the shared, gentle thing first."
    )
    world.say(trouble.lesson)


def ending(world: World, parent: Entity) -> None:
    paddy = world.get("Paddy")
    own_crop = world.get("own_crop")
    world.say(
        f"As the first stars came out, Paddy and {parent.label_word} walked toward the gate."
    )
    world.say(
        f"Paddy looked back once more. {own_crop.phrase.capitalize()} rested quietly in the dusk, "
        f"and the whole community garden seemed to glow as if it were tucking itself in for the night."
    )
    world.say(
        '"Tomorrow," Paddy thought, "I will check my own bed, and then I will check the others too."'
    )


def tell(crop: Crop, trouble: Trouble, charm_cfg: Charm, neighbor_crop_cfg: Crop,
         helper_name: str, helper_type: str, parent_type: str) -> World:
    world = World()
    paddy = world.add(Entity(id="Paddy", kind="character", type="boy", role="hero", label="Paddy"))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    own_crop = world.add(Entity(
        id="own_crop",
        type="crop",
        label=crop.label,
        phrase=crop.phrase,
        tags=set(crop.tags),
    ))
    neighbor_crop = world.add(Entity(
        id="neighbor_crop",
        type="crop",
        label=neighbor_crop_cfg.label,
        phrase=neighbor_crop_cfg.phrase,
        tags=set(neighbor_crop_cfg.tags),
    ))
    own_plot = world.add(Entity(
        id="own_plot",
        type="plot",
        label="Paddy's bed",
        attrs={"crop": "own_crop", "need": trouble.need},
    ))
    neighbor_plot = world.add(Entity(
        id="neighbor_plot",
        type="plot",
        label="the next bed",
        attrs={"crop": "neighbor_crop", "need": trouble.need},
    ))
    charm = world.add(Entity(
        id="charm",
        type="magic",
        label=charm_cfg.label,
        phrase=charm_cfg.phrase,
        tags=set(charm_cfg.tags),
    ))

    own_plot.meters[trouble.need] = 1.0
    neighbor_plot.meters[trouble.need] = 1.0
    propagate(world, narrate=False)

    introduce(world, crop, trouble, helper, parent)
    world.para()
    find_charm(world, charm_cfg)
    try_own_first(world, trouble, charm_cfg)
    hint(world, charm_cfg, helper)
    world.para()
    help_neighbor(world, trouble, helper)
    heal_own_plot(world, trouble, charm_cfg)
    world.para()
    reveal_twist(world, trouble, helper, parent)
    ending(world, parent)

    world.facts.update(
        crop=crop,
        trouble=trouble,
        charm=charm_cfg,
        neighbor_crop_cfg=neighbor_crop_cfg,
        helper=helper,
        parent=parent,
        paddy=paddy,
        own_crop=own_crop,
        neighbor_crop=neighbor_crop,
        own_plot=own_plot,
        neighbor_plot=neighbor_plot,
        charm_ent=charm,
        magic_awake=charm.meters["awake"] >= THRESHOLD,
        twist="The charm woke only after Paddy helped the neighboring bed first.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    crop = world.facts["crop"]
    trouble = world.facts["trouble"]
    charm = world.facts["charm"]
    helper = world.facts["helper"]
    return [
        'Write a bedtime story set in a community garden with a child named Paddy, a magical object, inner monologue, and a gentle twist.',
        f"Tell a soft evening story where Paddy finds that his {crop.label} is {trouble.id}, discovers a {charm.label}, and learns that the magic works only after he helps {helper_phrase(helper)} first.",
        f'Write a child-facing story that includes the word "paddy", uses inner thoughts like "Paddy thought," and ends with the garden glowing peacefully at night.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    crop = world.facts["crop"]
    trouble = world.facts["trouble"]
    charm = world.facts["charm"]
    helper = world.facts["helper"]
    parent = world.facts["parent"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Paddy in a community garden, plus {helper_phrase(helper)} in the next bed and Paddy's {parent.label_word}. The story follows the way Paddy's feelings change from worry to wonder to calm joy.",
        ),
        (
            f"What was wrong with Paddy's {crop.label}?",
            f"His {crop.label} {trouble.symptom}. That is why Paddy felt worried as evening came and began wishing for magic.",
        ),
        (
            f"What did Paddy think when he first saw the {charm.label}?",
            f"He hoped it would fix his own bed right away. Inside his head, he thought the magic might be only for his patch.",
        ),
        (
            "Why did the magic not work at first?",
            f"It stayed quiet when Paddy tried to help only himself. In this story, the charm wakes for shared care, not for a selfish first wish.",
        ),
        (
            "What did Paddy do that changed the garden?",
            f"He helped the neighboring bed before coming back to his own. That kind choice woke the charm, and then both the feeling of the garden and Paddy's own patch changed.",
        ),
        (
            "What was the twist?",
            f"The twist was that the object really was magical, but its magic did not belong to one child alone. It shone only after Paddy treated the community garden like something everyone shared.",
        ),
        (
            "How did the story end?",
            f"It ended quietly, with Paddy walking home under the first stars and looking back at the peaceful garden. He had learned to care for his own bed and the neighboring ones too.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "community_garden": [
        (
            "What is a community garden?",
            "A community garden is a place where neighbors grow plants together in shared beds. Different people care for their own patches, but they also help the whole garden stay healthy.",
        )
    ],
    "water": [
        (
            "Why do plants need water?",
            "Plants need water to stay firm and alive. Without enough water, leaves can droop and look tired.",
        )
    ],
    "support": [
        (
            "Why do some plants need support?",
            "Some plants have tall or climbing stems that bend easily. A stake or string helps them grow upward without falling over.",
        )
    ],
    "warmth": [
        (
            "Why can tiny plants need warmth at night?",
            "Small young plants can feel the cold more quickly than big strong ones. A little cover can help keep them cozy when the air turns cool.",
        )
    ],
    "watering_can": [
        (
            "What does a watering can do?",
            "A watering can pours water gently onto the soil around a plant. The gentle flow helps the roots drink without washing the plant away.",
        )
    ],
    "twine": [
        (
            "What is garden twine for?",
            "Garden twine is a soft string used to tie a plant carefully to a support. It helps the plant stand up without squeezing it too hard.",
        )
    ],
    "cloche": [
        (
            "What is a cloche in a garden?",
            "A cloche is a cover that sits over a plant like a little house. It can help protect a plant from cold air.",
        )
    ],
    "magic": [
        (
            "What kind of magic does this story teach?",
            "It teaches a gentle story kind of magic: kindness can change what happens next. When children share care, the world can feel brighter and safer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["community_garden", "water", "support", "warmth", "watering_can", "twine", "cloche", "magic"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    trouble = world.facts["trouble"]
    charm = world.facts["charm"]
    tags = {"community_garden", "magic"} | set(trouble.tags) | set(charm.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:13} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
need_of_trouble(T, N) :- trouble(T), causes_need(T, N).
fits_crop(C, T) :- crop(C), trouble(T), need_of_trouble(T, N), crop_needs(C, N).
fits_charm(Ch, T) :- charm(Ch), trouble(T), need_of_trouble(T, N), charm_fixes(Ch, N).
fits_neighbor(Nb, T) :- crop(Nb), trouble(T), need_of_trouble(T, N), crop_needs(Nb, N).

valid(C, T, Ch, Nb) :- crop(C), crop(Nb), C != Nb, trouble(T), charm(Ch),
                       fits_crop(C, T), fits_charm(Ch, T), fits_neighbor(Nb, T).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        for need in sorted(crop.needs):
            lines.append(asp.fact("crop_needs", crop_id, need))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("causes_need", trouble_id, trouble.need))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        for need in sorted(charm.fixes):
            lines.append(asp.fact("charm_fixes", charm_id, need))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Paddy, a community garden, a magical tool, and a kindness twist."
    )
    ap.add_argument("--crop", choices=sorted(CROPS))
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--charm", choices=sorted(CHARMS))
    ap.add_argument("--neighbor-crop", choices=sorted(CROPS))
    ap.add_argument("--helper-type", choices=sorted(HELPER_NAMES))
    ap.add_argument("--helper-name")
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python gate")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crop and args.crop not in CROPS:
        raise StoryError("(No story: unknown crop.)")
    if args.trouble and args.trouble not in TROUBLES:
        raise StoryError("(No story: unknown trouble.)")
    if args.charm and args.charm not in CHARMS:
        raise StoryError("(No story: unknown charm.)")
    if args.neighbor_crop and args.neighbor_crop not in CROPS:
        raise StoryError("(No story: unknown neighbor crop.)")

    if args.crop and args.trouble:
        crop = CROPS[args.crop]
        trouble = TROUBLES[args.trouble]
        charm = CHARMS[args.charm] if args.charm else None
        neighbor = CROPS[args.neighbor_crop] if args.neighbor_crop else None
        if trouble.need not in crop.needs:
            raise StoryError(explain_rejection(crop, trouble, charm, neighbor))
        if charm is not None and trouble.need not in charm.fixes:
            raise StoryError(explain_rejection(crop, trouble, charm, neighbor))
        if neighbor is not None and trouble.need not in neighbor.needs:
            raise StoryError(explain_rejection(crop, trouble, charm, neighbor))
        if args.neighbor_crop == args.crop:
            raise StoryError("(No story: Paddy's bed and the neighbor bed should be different crops in this world.)")

    combos = [
        combo for combo in valid_combos()
        if (args.crop is None or combo[0] == args.crop)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.charm is None or combo[2] == args.charm)
        and (args.neighbor_crop is None or combo[3] == args.neighbor_crop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crop_id, trouble_id, charm_id, neighbor_crop_id = rng.choice(sorted(combos))
    helper_type = args.helper_type or rng.choice(sorted(HELPER_NAMES))
    helper_name = args.helper_name or rng.choice(HELPER_NAMES[helper_type])
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(
        crop=crop_id,
        trouble=trouble_id,
        charm=charm_id,
        neighbor_crop=neighbor_crop_id,
        helper_name=helper_name,
        helper_type=helper_type,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.crop not in CROPS:
        raise StoryError(f"(No story: unknown crop '{params.crop}'.)")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(No story: unknown trouble '{params.trouble}'.)")
    if params.charm not in CHARMS:
        raise StoryError(f"(No story: unknown charm '{params.charm}'.)")
    if params.neighbor_crop not in CROPS:
        raise StoryError(f"(No story: unknown neighbor crop '{params.neighbor_crop}'.)")
    if params.helper_type not in HELPER_NAMES:
        raise StoryError(f"(No story: unknown helper type '{params.helper_type}'.)")
    crop = CROPS[params.crop]
    trouble = TROUBLES[params.trouble]
    charm = CHARMS[params.charm]
    neighbor_crop = CROPS[params.neighbor_crop]
    if params.crop == params.neighbor_crop:
        raise StoryError("(No story: Paddy's crop and the neighbor crop must be different.)")
    if trouble.need not in crop.needs or trouble.need not in charm.fixes or trouble.need not in neighbor_crop.needs:
        raise StoryError(explain_rejection(crop, trouble, charm, neighbor_crop))

    world = tell(
        crop=crop,
        trouble=trouble,
        charm_cfg=charm,
        neighbor_crop_cfg=neighbor_crop,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        parent_type=params.parent,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify smoke test.")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (crop, trouble, charm, neighbor_crop) combos:\n")
        for crop, trouble, charm, neighbor in combos:
            print(f"  {crop:10} {trouble:9} {charm:12} {neighbor}")
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
            header = f"### Paddy: {p.crop} / {p.trouble} / {p.charm} / neighbor {p.neighbor_crop}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
