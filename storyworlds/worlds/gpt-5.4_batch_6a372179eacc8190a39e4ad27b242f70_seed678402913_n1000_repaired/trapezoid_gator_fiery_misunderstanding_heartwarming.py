#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trapezoid_gator_fiery_misunderstanding_heartwarming.py
==================================================================================

A standalone story world about a child who misunderstands a glowing shape at dusk.
The child thinks a fiery gator has appeared, but the scary sight turns out to be
a harmless object with warm light on it. The misunderstanding resolves into a
gentle, heartwarming ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/trapezoid_gator_fiery_misunderstanding_heartwarming.py
    python storyworlds/worlds/gpt-5.4/trapezoid_gator_fiery_misunderstanding_heartwarming.py --place pond --decoy statue --light lantern
    python storyworlds/worlds/gpt-5.4/trapezoid_gator_fiery_misunderstanding_heartwarming.py --light moonbeam
    python storyworlds/worlds/gpt-5.4/trapezoid_gator_fiery_misunderstanding_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/trapezoid_gator_fiery_misunderstanding_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/trapezoid_gator_fiery_misunderstanding_heartwarming.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    decoys: set[str] = field(default_factory=set)
    closing_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    fiery: bool = False
    outdoor: bool = True
    glow_line: str = ""
    reveal_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Decoy:
    id: str
    label: str
    phrase: str
    far_shape: str
    near_truth: str
    carries_item: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    shape_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    decoy: str
    light: str
    item: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    child_trait: str
    seed: Optional[int] = None


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


def _r_fear_from_glow(world: World) -> list[str]:
    child = world.get("child")
    decoy = world.get("decoy")
    light = world.get("light")
    item = world.get("item")
    if decoy.meters["glowing"] < THRESHOLD or item.meters["lost"] < THRESHOLD:
        return []
    sig = ("fear_from_glow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["misunderstanding"] += 1
    return ["__misunderstood__"]


def _r_calm_spreads(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if helper.memes["calm"] < THRESHOLD or child.memes["fear"] < THRESHOLD:
        return []
    sig = ("calm_spreads",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["courage"] += 1
    return []


def _r_reveal_relief(world: World) -> list[str]:
    child = world.get("child")
    decoy = world.get("decoy")
    if decoy.meters["harmless"] < THRESHOLD or child.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("reveal_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["warmth"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="fear_from_glow", tag="emotion", apply=_r_fear_from_glow),
    Rule(name="calm_spreads", tag="emotion", apply=_r_calm_spreads),
    Rule(name="reveal_relief", tag="emotion", apply=_r_reveal_relief),
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


PLACES = {
    "pond": Place(
        id="pond",
        label="pond",
        phrase="the duck pond behind the library",
        decoys={"statue", "float"},
        closing_image="The pond no longer looked spooky; it looked like a place that could keep a tiny secret and then give it back kindly.",
        tags={"pond"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="greenhouse",
        phrase="the little greenhouse by the community garden",
        decoys={"watering_can", "statue"},
        closing_image="The glass panes glowed softly, and the whole greenhouse looked like it was smiling with them.",
        tags={"garden"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the wide front porch with flower boxes",
        decoys={"boots", "statue"},
        closing_image="The porch steps felt cozy again, and the evening gathered around them like a blanket.",
        tags={"porch"},
    ),
}

LIGHTS = {
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a paper lantern",
        fiery=True,
        outdoor=True,
        glow_line="Its orange light made everything nearby look fiery and larger than life.",
        reveal_line="Up close, the glow was only lantern-light, warm and wobbly, not dangerous at all.",
        tags={"lantern", "light"},
    ),
    "sunset": Light(
        id="sunset",
        label="sunset",
        phrase="the late sunset",
        fiery=True,
        outdoor=True,
        glow_line="The low sun poured a fiery stripe of orange over the edges of everything.",
        reveal_line="When they stepped nearer, it was only sunset shining across painted wood and shiny puddles.",
        tags={"sunset", "light"},
    ),
    "pumpkin": Light(
        id="pumpkin",
        label="pumpkin",
        phrase="a pumpkin lamp",
        fiery=True,
        outdoor=False,
        glow_line="The pumpkin lamp sent a fiery little glow over the floor and the nearby corners.",
        reveal_line="Up close, the light came from a safe little bulb inside the pumpkin lamp.",
        tags={"pumpkin", "light"},
    ),
    "moonbeam": Light(
        id="moonbeam",
        label="moonbeam",
        phrase="the moonlight",
        fiery=False,
        outdoor=True,
        glow_line="The moon made pale silver patches on the ground.",
        reveal_line="In the softer light, every shape looked plain and easy to understand.",
        tags={"moon", "light"},
    ),
}

DECOYS = {
    "statue": Decoy(
        id="statue",
        label="gator statue",
        phrase="a small green gator statue with a silly grin",
        far_shape="From far away, the statue's open mouth and the orange glow made it look like a fiery gator waiting by the path.",
        near_truth="it was only the little garden gator statue, with paint on its nose and a grin that looked more funny than fierce",
        carries_item=True,
        tags={"gator", "statue"},
    ),
    "float": Decoy(
        id="float",
        label="toy gator float",
        phrase="a faded toy gator float tied to the dock rail",
        far_shape="From the path, the float rocked in the glow and looked like a fiery gator lifting its nose from the water.",
        near_truth="it was just the old toy gator float bobbing against the dock, harmless and a little lopsided",
        carries_item=True,
        tags={"gator", "toy"},
    ),
    "watering_can": Decoy(
        id="watering_can",
        label="gator watering can",
        phrase="a green watering can shaped like a smiling gator",
        far_shape="In the bright orange reflection, the watering can looked for one breath like a fiery gator crouched among the pots.",
        near_truth="it was only the gator-shaped watering can by the tomato vines, with water droplets shining on its back",
        carries_item=True,
        tags={"gator", "garden"},
    ),
    "boots": Decoy(
        id="boots",
        label="gator rain boots",
        phrase="a pair of child-sized rain boots with gator faces on the toes",
        far_shape="With the orange glow across them, the boots looked like a fiery gator head peeking from the steps.",
        near_truth="it was just a pair of rain boots with cheerful gator faces, toes pointing toward the yard",
        carries_item=True,
        tags={"gator", "boots"},
    ),
}

ITEMS = {
    "lantern": LostItem(
        id="lantern",
        label="trapezoid lantern",
        phrase="a little trapezoid lantern made from folded paper",
        shape_line="The lantern was not round at all. It had neat trapezoid sides that the child had worked very hard to fold.",
        tags={"trapezoid", "craft"},
    ),
    "card": LostItem(
        id="card",
        label="trapezoid card",
        phrase="a bright thank-you card cut into a trapezoid shape",
        shape_line="The card had a trapezoid top and bottom, because the child wanted it to look like the roof of a tiny house.",
        tags={"trapezoid", "card"},
    ),
    "kite": LostItem(
        id="kite",
        label="trapezoid kite",
        phrase="a small kite with a trapezoid patch sewn near the middle",
        shape_line="Right in the center was a trapezoid patch of red cloth, and the child liked smoothing it flat with careful fingers.",
        tags={"trapezoid", "kite"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]
HELPERS = [
    ("Nana", "grandmother"),
    ("Grandpa", "grandfather"),
    ("Mom", "mother"),
    ("Dad", "father"),
]
TRAITS = ["careful", "gentle", "curious", "hopeful", "thoughtful"]


def valid_combo(place_id: str, decoy_id: str, light_id: str) -> bool:
    place = PLACES[place_id]
    light = LIGHTS[light_id]
    return (
        decoy_id in place.decoys
        and light.fiery
        and (light.outdoor or place_id in {"greenhouse", "porch"})
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for decoy_id in sorted(DECOYS):
            for light_id in sorted(LIGHTS):
                if valid_combo(place_id, decoy_id, light_id):
                    combos.append((place_id, decoy_id, light_id))
    return combos


def explain_rejection(place_id: str, decoy_id: str, light_id: str) -> str:
    place = PLACES[place_id]
    if decoy_id not in place.decoys:
        return (
            f"(No story: {DECOYS[decoy_id].label} does not belong at {place.phrase}. "
            f"Pick a decoy that fits the place so the misunderstanding feels real.)"
        )
    if not LIGHTS[light_id].fiery:
        return (
            f"(No story: {LIGHTS[light_id].phrase} is too soft to make a 'fiery gator' misunderstanding. "
            f"Pick lantern, sunset, or pumpkin.)"
        )
    if LIGHTS[light_id].outdoor and place_id not in {"pond", "greenhouse", "porch"}:
        return "(No story: that light does not fit the place.)"
    return "(No story: this combination does not support the misunderstanding.)"


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    sim.get("decoy").meters["glowing"] += 1
    sim.get("item").meters["lost"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "fear": child.memes["fear"],
        "misunderstanding": child.memes["misunderstanding"],
    }


def introduce(world: World, child: Entity, helper: Entity, item_cfg: LostItem) -> None:
    world.say(
        f"{child.id} had spent the afternoon with {helper.label_word}, making {item_cfg.phrase}."
    )
    world.say(item_cfg.shape_line)
    world.say(
        f"When the work was done, {child.pronoun()} held it up and smiled as if evening itself might clap."
    )


def arrive(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["trust"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At dusk, {child.id} and {helper.label_word} carried it out to {place.phrase} so they could see how it looked in the fading light."
    )


def lose_item(world: World, child: Entity, item: Entity) -> None:
    item.meters["lost"] += 1
    child.memes["worry"] += 1
    world.say(
        f"A small gust skipped through the air and tugged the {item.label} from {child.id}'s hands."
    )
    world.say(
        f"It skittered away before either of them could catch it."
    )


def sighting(world: World, child: Entity, decoy: Entity, light: Light) -> None:
    decoy.meters["glowing"] += 1
    pred = predict_misunderstanding(world)
    world.facts["predicted_fear"] = pred["fear"]
    propagate(world, narrate=False)
    world.say(light.glow_line)
    world.say(DECOYS[decoy.attrs["cfg"]].far_shape)
    world.say(
        f'{child.id} stopped short. "My {world.get("item").label} is over there," {child.pronoun()} whispered. "What if that gator is guarding it?"'
    )


def comfort(world: World, child: Entity, helper: Entity) -> None:
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f'{helper.label_word.capitalize()} rested a gentle hand on {child.id}\'s shoulder. "Let us look carefully before we decide what we are seeing," {helper.pronoun()} said.'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} smiled. "Sometimes far-away things borrow the wrong shape from the dark," {helper.pronoun()} said.'
        )


def approach(world: World, child: Entity, helper: Entity) -> None:
    child.memes["courage"] += 1
    world.say(
        f"They took three slow steps together, then three more, with {helper.label_word} walking on the side nearest the shadow."
    )


def reveal(world: World, child: Entity, helper: Entity, decoy: Entity, light: Light, item: Entity) -> None:
    decoy.meters["harmless"] += 1
    item.meters["found"] += 1
    item.meters["lost"] = 0.0
    propagate(world, narrate=False)
    world.say(light.reveal_line)
    world.say(
        f"Then they saw the truth: {DECOYS[decoy.attrs['cfg']].near_truth}."
    )
    if decoy.attrs.get("holds_item"):
        world.say(
            f"The {item.label} had simply caught against it instead of blowing any farther away."
        )
    else:
        world.say(
            f"The {item.label} lay just behind it, safe and still."
        )


def warm_end(world: World, child: Entity, helper: Entity, place: Place, item: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["warmth"] += 1
    world.say(
        f"{child.id} let out the breath {child.pronoun()} had been holding and laughed a little."
    )
    world.say(
        f'{helper.label_word.capitalize()} handed back the {item.label}. "Not every fiery thing is fierce," {helper.pronoun()} said. "Sometimes it is only light doing dress-up."'
    )
    world.say(
        f"{child.id} nodded and tucked closer to {helper.label_word}. {place.closing_image}"
    )


def tag_friendliness(world: World, child: Entity, decoy: Entity) -> None:
    child.memes["kindness"] += 1
    world.say(
        f"Before they went inside, {child.id} turned back and gave the little {decoy.label} an extra friendly glance, as if even a mistaken gator deserved a kind goodbye."
    )


def tell(
    place_cfg: Place,
    decoy_cfg: Decoy,
    light_cfg: Light,
    item_cfg: LostItem,
    child_name: str = "Lily",
    child_gender: str = "girl",
    helper_name: str = "Nana",
    helper_type: str = "grandmother",
    child_trait: str = "careful",
) -> World:
    world = World(place_cfg)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"trait": child_trait},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_name,
        phrase=helper_name,
        role="helper",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="keepsake",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="item",
        tags=set(item_cfg.tags),
    ))
    decoy = world.add(Entity(
        id="decoy",
        kind="thing",
        type="decoy",
        label=decoy_cfg.label,
        phrase=decoy_cfg.phrase,
        role="decoy",
        attrs={"cfg": decoy_cfg.id, "holds_item": decoy_cfg.carries_item},
        tags=set(decoy_cfg.tags),
    ))
    light = world.add(Entity(
        id="light",
        kind="thing",
        type="light",
        label=light_cfg.label,
        phrase=light_cfg.phrase,
        role="light",
        attrs={"cfg": light_cfg.id},
        tags=set(light_cfg.tags),
    ))

    introduce(world, child, helper, item_cfg)
    arrive(world, child, helper, place_cfg)

    world.para()
    lose_item(world, child, item)
    sighting(world, child, decoy, light_cfg)
    comfort(world, child, helper)

    world.para()
    approach(world, child, helper)
    reveal(world, child, helper, decoy, light_cfg, item)
    warm_end(world, child, helper, place_cfg, item)
    tag_friendliness(world, child, decoy)

    world.facts.update(
        place=place_cfg,
        light_cfg=light_cfg,
        decoy_cfg=decoy_cfg,
        item_cfg=item_cfg,
        child=child,
        helper=helper,
        item=item,
        decoy=decoy,
        misunderstanding=child.memes["misunderstanding"] >= THRESHOLD,
        resolved=item.meters["found"] >= THRESHOLD and decoy.meters["harmless"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "trapezoid": [
        (
            "What is a trapezoid?",
            "A trapezoid is a shape with four sides. One pair of sides is parallel, so it can look a little like a roof or a slanted box.",
        )
    ],
    "gator": [
        (
            "What is a gator?",
            "A gator is a short word for an alligator. It is a large reptile with a long body, strong tail, and many teeth.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what they saw or heard. Looking again and asking calm questions can help fix it.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light in the dark. Some lanterns use candles, and some use safe little bulbs.",
        )
    ],
    "sunset": [
        (
            "Why can sunset make things look different?",
            "At sunset, orange light shines from a low angle and stretches shadows. That can make ordinary things look brighter, bigger, or stranger from far away.",
        )
    ],
    "pumpkin": [
        (
            "What is a pumpkin lamp?",
            "A pumpkin lamp is a pumpkin-shaped light. If it uses a bulb, it can glow warmly without a real flame.",
        )
    ],
    "pond": [
        (
            "Why do ponds have reflections?",
            "Still water can bounce light back like a mirror. That is why colors and shapes can look doubled near a pond.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "trapezoid",
    "gator",
    "misunderstanding",
    "lantern",
    "sunset",
    "pumpkin",
    "pond",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    light_cfg = world.facts["light_cfg"]
    return [
        (
            f'Write a heartwarming story for a 3-to-5-year-old that includes the words '
            f'"trapezoid", "gator", and "fiery", and centers on a misunderstanding at {place.label}.'
        ),
        (
            f"Tell a gentle dusk story where {child.label} loses {item_cfg.phrase}, mistakes a glowing shape for a fiery gator, and is helped by {helper.label_word}."
        ),
        (
            f"Write a cozy story where orange light from {light_cfg.phrase} makes something look scary at first, but the truth turns out to be safe and sweet."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    decoy_cfg = world.facts["decoy_cfg"]
    light_cfg = world.facts["light_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label} and {helper.label_word}. They go together to {place.phrase} with {item_cfg.phrase}.",
        ),
        (
            f"What special thing did {child.label} have?",
            f"{child.label} had {item_cfg.phrase}. It mattered because {child.pronoun()} had helped make it and did not want to lose it.",
        ),
        (
            f"Why did {child.label} think there was a fiery gator?",
            f"{light_cfg.phrase.capitalize()} made the shape look bright orange and strange from far away. Because the {item_cfg.label} had blown near it, {child.label} thought a gator was guarding it.",
        ),
        (
            "Was the gator real?",
            f"No. It only looked that way at first, but when they came closer they saw that {decoy_cfg.near_truth}.",
        ),
        (
            f"How was the misunderstanding solved?",
            f"{helper.label_word.capitalize()} stayed calm and walked closer with {child.label} instead of running away. Looking carefully helped them see the true shape and find the {item_cfg.label} safely.",
        ),
        (
            "How did the story end?",
            f"It ended warmly, with {child.label} relieved and smiling beside {helper.label_word}. The place felt cozy again once the scary mistake had turned into an ordinary, friendly sight.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"trapezoid", "gator", "misunderstanding"}
    light_id = world.facts["light_cfg"].id
    place_id = world.facts["place"].id
    if light_id in {"lantern", "sunset", "pumpkin"}:
        tags.add(light_id)
    if place_id == "pond":
        tags.add("pond")
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pond",
        decoy="float",
        light="sunset",
        item="lantern",
        child_name="Lily",
        child_gender="girl",
        helper_name="Nana",
        helper_type="grandmother",
        child_trait="careful",
    ),
    StoryParams(
        place="greenhouse",
        decoy="watering_can",
        light="pumpkin",
        item="card",
        child_name="Ben",
        child_gender="boy",
        helper_name="Grandpa",
        helper_type="grandfather",
        child_trait="thoughtful",
    ),
    StoryParams(
        place="porch",
        decoy="boots",
        light="lantern",
        item="kite",
        child_name="Mia",
        child_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        child_trait="gentle",
    ),
    StoryParams(
        place="pond",
        decoy="statue",
        light="lantern",
        item="card",
        child_name="Theo",
        child_gender="boy",
        helper_name="Dad",
        helper_type="father",
        child_trait="curious",
    ),
]


ASP_RULES = r"""
valid(Place, Decoy, Light) :-
    place(Place), decoy(Decoy), light(Light),
    placed_at(Place, Decoy),
    fiery(Light),
    fits_light(Place, Light).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for decoy_id in sorted(place.decoys):
            lines.append(asp.fact("placed_at", place_id, decoy_id))
    for decoy_id in DECOYS:
        lines.append(asp.fact("decoy", decoy_id))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        if light.fiery:
            lines.append(asp.fact("fiery", light_id))
        if light.outdoor:
            for place_id in ("pond", "greenhouse", "porch"):
                lines.append(asp.fact("fits_light", place_id, light_id))
        else:
            for place_id in ("greenhouse", "porch"):
                lines.append(asp.fact("fits_light", place_id, light_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fiery misunderstanding turns into a warm discovery."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--decoy", choices=sorted(DECOYS))
    ap.add_argument("--light", choices=sorted(LIGHTS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[h[1] for h in HELPERS])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check inline ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.decoy and args.light:
        if not valid_combo(args.place, args.decoy, args.light):
            raise StoryError(explain_rejection(args.place, args.decoy, args.light))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.decoy is None or combo[1] == args.decoy)
        and (args.light is None or combo[2] == args.light)
    ]
    if not combos:
        if args.place and args.decoy and args.light:
            raise StoryError(explain_rejection(args.place, args.decoy, args.light))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, decoy_id, light_id = rng.choice(sorted(combos))
    item_id = args.item or rng.choice(sorted(ITEMS))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_choices = [h for h in HELPERS if args.helper is None or h[1] == args.helper]
    helper_name, helper_type = rng.choice(helper_choices)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        decoy=decoy_id,
        light=light_id,
        item=item_id,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        child_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.decoy not in DECOYS:
        raise StoryError(f"(Unknown decoy: {params.decoy})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if not valid_combo(params.place, params.decoy, params.light):
        raise StoryError(explain_rejection(params.place, params.decoy, params.light))

    world = tell(
        place_cfg=PLACES[params.place],
        decoy_cfg=DECOYS[params.decoy],
        light_cfg=LIGHTS[params.light],
        item_cfg=ITEMS[params.item],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        child_trait=params.child_trait,
    )

    story = world.render()
    if "trapezoid" not in story or "gator" not in story or "fiery" not in story:
        raise StoryError("The rendered story failed to include the required seed words.")

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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, decoy, light) combos:\n")
        for place_id, decoy_id, light_id in combos:
            print(f"  {place_id:10} {decoy_id:12} {light_id}")
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
            header = f"### {p.child_name}: {p.place}, {p.decoy}, {p.light}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
