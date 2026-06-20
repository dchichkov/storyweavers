#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/meme_vegetable_garden_conflict_bedtime_story.py
===========================================================================

A standalone story world for a gentle bedtime conflict in a vegetable garden.

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: meme
Setting: vegetable garden
Features: Conflict
Style: Bedtime Story

World premise
-------------
A small child loves the vegetable garden so much that bedtime becomes hard.
At dusk, the child worries about one garden bed: maybe the night will turn cold,
maybe the leaves are thirsty, or maybe snails will nibble the plants. The parent
does not simply say "go to bed." Instead, the grown-up predicts the real garden
risk and offers the right small fix. The child helps, the conflict softens, and
the ending image shows both the child and the vegetables resting safely.

The reasonableness gate is physical:
- each crop has only certain plausible night risks
- each remedy only solves certain risks
- some remedies only fit certain crop shapes
Invalid explicit choices are refused with a legible StoryError.

Run it
------
python storyworlds/worlds/gpt-5.4/meme_vegetable_garden_conflict_bedtime_story.py
python storyworlds/worlds/gpt-5.4/meme_vegetable_garden_conflict_bedtime_story.py --crop lettuce --risk cold --remedy row_cover
python storyworlds/worlds/gpt-5.4/meme_vegetable_garden_conflict_bedtime_story.py --crop tomatoes --risk snails
python storyworlds/worlds/gpt-5.4/meme_vegetable_garden_conflict_bedtime_story.py --all
python storyworlds/worlds/gpt-5.4/meme_vegetable_garden_conflict_bedtime_story.py --qa --json
python storyworlds/worlds/gpt-5.4/meme_vegetable_garden_conflict_bedtime_story.py --verify
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

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"       # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    height: str = ""
    needs: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    fits: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
@dataclass
class Crop:
    id: str
    label: str
    patch: str
    height: str                  # low | vine | row
    needs: set[str]
    leaf_text: str
    sleep_text: str
    meme_name: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    sign: str
    danger: str
    night_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    guards: set[str]
    fits: set[str]
    action: str
    result: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    offer: str
    bed_image: str
    tags: set[str] = field(default_factory=set)


CROPS = {
    "lettuce": Crop(
        "lettuce",
        "lettuce",
        "the cool lettuce bed",
        "low",
        {"cold", "snails"},
        "their leaves cupped the last light like little green hands",
        "the lettuce looked tucked in already",
        "meme lettuce",
        tags={"lettuce", "leafy"},
    ),
    "tomatoes": Crop(
        "tomatoes",
        "tomatoes",
        "the tomato patch by the fence",
        "vine",
        {"dry"},
        "small green tomatoes hid under the leaves like shy lanterns",
        "the tomato vines rested against the fence",
        "meme tomato",
        tags={"tomato", "vine"},
    ),
    "beans": Crop(
        "beans",
        "bean seedlings",
        "the bean row beside the path",
        "row",
        {"cold", "dry"},
        "their thin stems leaned together as if whispering",
        "the bean row lay still and straight",
        "meme bean",
        tags={"beans", "seedling"},
    ),
    "carrots": Crop(
        "carrots",
        "carrots",
        "the carrot row near the stepping stones",
        "row",
        {"dry"},
        "their feathery tops shivered in the evening air",
        "the carrot tops made a soft dark lace against the soil",
        "meme carrot",
        tags={"carrot", "root"},
    ),
}

RISKS = {
    "cold": Risk(
        "cold",
        "cold air",
        "the air was turning chilly",
        "tender leaves could droop before morning",
        "the night was clear enough to let the chill sink down into the soil",
        tags={"cold"},
    ),
    "dry": Risk(
        "dry",
        "dry soil",
        "the dirt had gone pale and crumbly",
        "the plants could wake up droopy and thirsty",
        "the day had been warm, and the bed still held the tired look of thirst",
        tags={"dry"},
    ),
    "snails": Risk(
        "snails",
        "snails",
        "silver snail trails shone by the leaves",
        "the snails could nibble holes before dawn",
        "night was exactly when snails liked to come out and chew quietly",
        tags={"snails"},
    ),
}

REMEDIES = {
    "row_cover": Remedy(
        "row_cover",
        "a soft row cover",
        {"cold"},
        {"low", "row"},
        "spread the soft row cover over the bed and tucked its edges under the soil",
        "The cover made a little tent of warm air over the leaves.",
        "put a soft row cover over the bed to keep the cold off",
        tags={"row_cover"},
    ),
    "watering_can": Remedy(
        "watering_can",
        "the watering can",
        {"dry"},
        {"low", "row", "vine"},
        "tilted the watering can slowly until the soil turned dark and rich again",
        "The roots drank, and the whole bed looked less tired.",
        "watered the bed slowly until the soil was dark again",
        tags={"watering_can"},
    ),
    "cloche": Remedy(
        "cloche",
        "a clear cloche cover",
        {"snails", "cold"},
        {"low"},
        "set a clear cloche cover over the tender leaves like a small glassy dome",
        "The cover kept little teeth and cold air away from the leaves.",
        "set a clear cloche cover over the leaves to keep them safe",
        tags={"cloche"},
    ),
}

COMFORTS = {
    "window": Comfort(
        "window",
        "After that, we can peek once from your bedroom window and see the quiet garden together.",
        "From bed, {name} could see a dark square of garden beyond the window, peaceful and safe.",
        tags={"window"},
    ),
    "hum": Comfort(
        "hum",
        "After that, I will carry you inside and hum your sleepy garden song.",
        "In bed, {name} listened to the low garden-song hum and imagined the vegetables sleeping too.",
        tags={"hum"},
    ),
    "story": Comfort(
        "story",
        "After that, I will tell you a tiny story about brave vegetables who know how to rest at night.",
        "Under the blanket, {name} smiled at the thought of quiet vegetables resting in the moonlight.",
        tags={"story"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Eli", "Jack", "Finn", "Noah", "Theo", "Owen"]
TRAITS = ["tender-hearted", "stubborn", "careful", "curious", "earnest", "gentle"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_night_harm(world: World) -> list[str]:
    out: list[str] = []
    bed = world.get("bed")
    child = world.get("child")
    risk = world.facts["risk"]
    if bed.meters[risk.id] < THRESHOLD:
        return out
    if bed.meters["protected"] >= THRESHOLD:
        return out
    sig = ("night_harm", risk.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bed.meters["health_loss"] += 1
    bed.meters["trouble"] += 1
    child.memes["worry"] += 1
    out.append("__night_trouble__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes["defiance"] < THRESHOLD or parent.memes["bedtime_call"] < THRESHOLD:
        return out
    sig = ("conflict", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] += 1
    parent.memes["conflict"] += 1
    out.append("__conflict__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    bed = world.get("bed")
    child = world.get("child")
    if bed.meters["protected"] < THRESHOLD:
        return out
    sig = ("relief", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    if child.memes["worry"] >= THRESHOLD:
        child.memes["worry"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("night_harm", "physical", _r_night_harm),
    Rule("conflict", "social", _r_conflict),
    Rule("relief", "emotional", _r_relief),
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
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def crop_at_risk(crop: Crop, risk: Risk) -> bool:
    return risk.id in crop.needs


def remedy_fits(crop: Crop, remedy: Remedy) -> bool:
    return crop.height in remedy.fits


def remedy_solves(risk: Risk, remedy: Remedy) -> bool:
    return risk.id in remedy.guards


def valid_story(crop: Crop, risk: Risk, remedy: Remedy) -> bool:
    return crop_at_risk(crop, risk) and remedy_fits(crop, remedy) and remedy_solves(risk, remedy)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for crop_id, crop in CROPS.items():
        for risk_id, risk in RISKS.items():
            for remedy_id, remedy in REMEDIES.items():
                if valid_story(crop, risk, remedy):
                    combos.append((crop_id, risk_id, remedy_id))
    return combos


def explain_rejection(crop: Crop, risk: Risk, remedy: Optional[Remedy] = None) -> str:
    if not crop_at_risk(crop, risk):
        return (
            f"(No story: {crop.label} are not the sort of plants this world treats as "
            f"at risk from {risk.label} overnight. Pick a risk that matches the crop.)"
        )
    if remedy is not None and not remedy_solves(risk, remedy):
        return (
            f"(No story: {remedy.label} does not actually solve {risk.label}. "
            f"The bedtime fix must address the real garden problem.)"
        )
    if remedy is not None and not remedy_fits(crop, remedy):
        return (
            f"(No story: {remedy.label} does not fit {crop.label} well enough in this world. "
            f"The remedy must suit the shape of the crop bed.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_night(world: World) -> dict:
    sim = world.copy()
    bed = sim.get("bed")
    risk = sim.facts["risk"]
    bed.meters[risk.id] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "trouble": bed.meters["trouble"],
        "worry": child.memes["worry"],
        "danger_text": risk.danger,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, crop: Crop) -> None:
    trait = child.traits[0] if child.traits else "little"
    world.say(
        f"In the vegetable garden, {child.id} was such a {trait} little gardener "
        f"that even the rows of dirt felt like friends."
    )
    world.say(
        f"That evening, {crop.patch} glowed softly in the last gold light, and {crop.leaf_text}."
    )


def meme_marker(world: World, child: Entity, crop: Crop) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} had even made a tiny stick sign for the bed and whispered, "
        f'"Good night, {crop.meme_name}," as if the vegetables might giggle back.'
    )


def show_risk(world: World, risk: Risk) -> None:
    world.say(
        f"But the garden was changing with the evening. {risk.sign}, and {risk.night_line}."
    )


def bedtime_call(world: World, parent: Entity, child: Entity) -> None:
    parent.memes["bedtime_call"] += 1
    world.say(
        f'From the path, {child.id}\'s {parent.label_word} said softly, '
        f'"It is bedtime now, little gardener."'
    )


def resist(world: World, child: Entity, crop: Crop) -> None:
    child.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} held the garden sign close. "Not yet," {child.pronoun()} said. '
        f'"{crop.label.capitalize()} should not be all alone out here."'
    )
    if child.memes["conflict"] >= THRESHOLD:
        world.say(
            f"{child.id}'s voice came out small and sharp at the same time, because "
            f"love and tiredness were tugging in opposite directions."
        )


def grounded_warning(world: World, parent: Entity, child: Entity, crop: Crop) -> None:
    pred = predict_night(world)
    world.facts["predicted_trouble"] = pred["trouble"]
    world.facts["predicted_danger"] = pred["danger_text"]
    child.memes["worry"] += 1
    world.say(
        f'{parent.label_word.capitalize()} looked carefully at {crop.patch}. '
        f'"You are right to notice the garden," {parent.pronoun()} said. '
        f'"If we left it just like this, {pred["danger_text"]}."'
    )


def offer_fix(world: World, parent: Entity, remedy: Remedy, comfort: Comfort) -> None:
    world.say(
        f'"So let us do one small helping job together," {parent.pronoun()} said. '
        f'"We can use {remedy.label}, and then {comfort.offer}"'
    )


def apply_remedy(world: World, child: Entity, bed: Entity, remedy: Remedy) -> None:
    bed.meters["protected"] += 1
    for guard in remedy.guards:
        bed.meters[guard] = 0.0
    propagate(world, narrate=False)
    child.memes["helpfulness"] += 1
    world.say(
        f"Together they {remedy.action}. {remedy.result}"
    )


def soften(world: World, parent: Entity, child: Entity, crop: Crop) -> None:
    child.memes["conflict"] = 0.0
    parent.memes["conflict"] = 0.0
    child.memes["trust"] += 1
    child.memes["love"] += 1
    world.say(
        f"{child.id} let out the breath {child.pronoun()} had been holding. "
        f'"There," {child.pronoun()} whispered. "Now {crop.label} can sleep."'
    )
    world.say(
        f'{parent.label_word.capitalize()} squeezed {child.pronoun("possessive")} hand. '
        f'"Yes," {parent.pronoun()} said, "and now you can too."'
    )


def bed_ending(world: World, child: Entity, comfort: Comfort, crop: Crop) -> None:
    child.memes["sleepy"] += 1
    world.say(comfort.bed_image.format(name=child.id))
    world.say(
        f"{crop.sleep_text}, and at last {child.id}'s eyes grew heavy enough to close."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    crop: Crop,
    risk: Risk,
    remedy: Remedy,
    comfort: Comfort,
    name: str = "Lily",
    gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "tender-hearted",
) -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type=gender, role="child", traits=[trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    bed = world.add(Entity(
        id="bed",
        kind="thing",
        type="garden_bed",
        label=crop.label,
        height=crop.height,
        needs=set(crop.needs),
    ))
    world.facts["crop"] = crop
    world.facts["risk"] = risk
    world.facts["remedy"] = remedy
    world.facts["comfort"] = comfort

    introduce(world, child, crop)
    meme_marker(world, child, crop)
    show_risk(world, risk)

    world.para()
    bedtime_call(world, parent, child)
    resist(world, child, crop)
    grounded_warning(world, parent, child, crop)
    offer_fix(world, parent, remedy, comfort)

    world.para()
    apply_remedy(world, child, bed, remedy)
    soften(world, parent, child, crop)

    world.para()
    bed_ending(world, child, comfort, crop)

    world.facts.update(
        child=child,
        parent=parent,
        bed=bed,
        resolved=bed.meters["protected"] >= THRESHOLD,
        conflict_seen=True,
        trouble_predicted=world.facts.get("predicted_trouble", 0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    crop: str
    risk: str
    remedy: str
    comfort: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "cold": [(
        "Why can a cold night bother small plants?",
        "Tender leaves can lose warmth fast at night. That can make them droop or turn weak by morning."
    )],
    "dry": [(
        "Why do plants need water in dry soil?",
        "Plants use water to stay firm and keep growing. When the soil is too dry, the leaves can droop and look tired."
    )],
    "snails": [(
        "Why are snails a problem in a vegetable garden?",
        "Snails like to nibble soft leaves, especially at night. They can leave little holes in vegetables."
    )],
    "row_cover": [(
        "What does a row cover do?",
        "A row cover is a light cloth that rests over plants. It helps hold in warmth and protects tender leaves."
    )],
    "watering_can": [(
        "What is a watering can for?",
        "A watering can lets you pour water gently onto soil and roots. That helps plants drink without washing the dirt away."
    )],
    "cloche": [(
        "What is a cloche cover?",
        "A cloche is a clear cover placed over a plant like a little dome. It helps keep out cold air and hungry garden pests."
    )],
    "lettuce": [(
        "What does lettuce grow like?",
        "Lettuce grows in soft leafy heads or loose leaves close to the ground. The leaves are tender and easy to bite."
    )],
    "tomato": [(
        "Where do tomatoes grow?",
        "Tomatoes grow on vines or tall plants with leaves and stems. The fruit hangs under the leaves as it ripens."
    )],
    "beans": [(
        "What are bean seedlings?",
        "Bean seedlings are very young bean plants. Their stems are thin and still need gentle care."
    )],
    "carrot": [(
        "Where do carrots grow?",
        "Carrots grow under the soil as roots. Their leafy tops show above the ground."
    )],
}
KNOWLEDGE_ORDER = [
    "cold", "dry", "snails", "row_cover", "watering_can", "cloche",
    "lettuce", "tomato", "beans", "carrot",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    crop = f["crop"]
    risk = f["risk"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old set in a vegetable garden that includes the word "meme".',
        f"Tell a gentle conflict story where a little {child.type} named {child.id} does not want to leave the vegetable garden at bedtime because {child.pronoun('possessive')} {crop.label} might face {risk.label}.",
        f"Write a calm story where a parent takes a child's garden worry seriously, helps with one small real fix, and ends with both the child and the vegetables ready to rest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    crop = f["crop"]
    risk = f["risk"]
    remedy = f["remedy"]
    comfort = f["comfort"]
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little gardener, and {child.pronoun('possessive')} {pw}. The story happens in the vegetable garden at bedtime."
        ),
        (
            "Why did bedtime turn into a conflict?",
            f"{child.id} did not want to leave because {child.pronoun()} was worried about the {crop.label} in the night. Love for the garden and tired bedtime feelings pulled in different directions, so the moment became sharp."
        ),
        (
            'Why did the story include the word "meme"?',
            f'{child.id} had made a tiny garden sign and jokingly called the bed "{crop.meme_name}." The silly word showed how fond {child.pronoun()} was of the vegetables.'
        ),
        (
            f"What problem did {child.id}'s {pw} notice in the garden?",
            f"{pw.capitalize()} noticed that {risk.sign}. {parent.pronoun().capitalize()} understood that {risk.danger}, so the worry was about a real garden need and not just delay."
        ),
        (
            f"How did {child.id}'s {pw} solve the problem?",
            f"{pw.capitalize()} and {child.id} used {remedy.label} and {remedy.qa_text}. That changed the garden state, so {child.id} no longer had to choose between caring and resting."
        ),
        (
            "How did the story end?",
            f"It ended quietly after the bed was safe. {comfort.bed_image.format(name=child.id)}"
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    crop = f["crop"]
    risk = f["risk"]
    remedy = f["remedy"]
    tags = set(risk.tags) | set(remedy.tags) | set(crop.tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.height:
            bits.append(f"height={e.height}")
        if e.needs:
            bits.append(f"needs={sorted(e.needs)}")
        if e.guards:
            bits.append(f"guards={sorted(e.guards)}")
        if e.fits:
            bits.append(f"fits={sorted(e.fits)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
crop_at_risk(C, R) :- crop(C), risk(R), needs(C, R).
remedy_fits(C, M) :- crop(C), remedy(M), height(C, H), fits(M, H).
remedy_solves(R, M) :- risk(R), remedy(M), guards(M, R).

valid(C, R, M) :- crop_at_risk(C, R), remedy_fits(C, M), remedy_solves(R, M).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, crop in CROPS.items():
        lines.append(asp.fact("crop", cid))
        lines.append(asp.fact("height", cid, crop.height))
        for need in sorted(crop.needs):
            lines.append(asp.fact("needs", cid, need))
    for rid in RISKS:
        lines.append(asp.fact("risk", rid))
    for mid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", mid))
        for g in sorted(remedy.guards):
            lines.append(asp.fact("guards", mid, g))
        for fit in sorted(remedy.fits):
            lines.append(asp.fact("fits", mid, fit))
    return "\n".join(lines)


def asp_program(extra_show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra_show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    # Smoke-test ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("lettuce", "cold", "row_cover", "window", "Lily", "girl", "mother", "tender-hearted"),
    StoryParams("lettuce", "snails", "cloche", "story", "Ben", "boy", "father", "careful"),
    StoryParams("tomatoes", "dry", "watering_can", "hum", "Mia", "girl", "mother", "earnest"),
    StoryParams("beans", "cold", "row_cover", "story", "Theo", "boy", "father", "stubborn"),
    StoryParams("carrots", "dry", "watering_can", "window", "Nora", "girl", "mother", "gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime conflict in a vegetable garden. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (crop, risk, remedy) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crop and args.risk:
        crop, risk = CROPS[args.crop], RISKS[args.risk]
        if not crop_at_risk(crop, risk):
            raise StoryError(explain_rejection(crop, risk))
    if args.crop and args.risk and args.remedy:
        crop, risk, remedy = CROPS[args.crop], RISKS[args.risk], REMEDIES[args.remedy]
        if not valid_story(crop, risk, remedy):
            raise StoryError(explain_rejection(crop, risk, remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.crop is None or combo[0] == args.crop)
        and (args.risk is None or combo[1] == args.risk)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crop_id, risk_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    trait = rng.choice(TRAITS)
    return StoryParams(crop_id, risk_id, remedy_id, comfort, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CROPS[params.crop],
        RISKS[params.risk],
        REMEDIES[params.remedy],
        COMFORTS[params.comfort],
        params.name,
        params.gender,
        params.parent,
        params.trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (crop, risk, remedy) combos:\n")
        for crop, risk, remedy in combos:
            print(f"  {crop:10} {risk:8} {remedy}")
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
            header = f"### {p.name}: {p.crop} / {p.risk} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
