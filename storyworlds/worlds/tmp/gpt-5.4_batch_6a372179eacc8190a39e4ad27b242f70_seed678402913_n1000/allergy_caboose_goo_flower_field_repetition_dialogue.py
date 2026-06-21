#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/allergy_caboose_goo_flower_field_repetition_dialogue.py
==================================================================================

A standalone storyworld for a tiny detective-story domain set in a flower field:
a child notices sticky goo in the caboose of a little garden train, a friend's
allergy keeps interrupting the investigation with sneezes, and the children use
real clues to solve the mystery and make the ride safe again.

Seed ingredients rebuilt as world state
---------------------------------------
- setting: flower field
- words: allergy, caboose, goo
- features: repetition, dialogue, flashback
- style: detective story

World logic
-----------
A garden train circles a flower field. In the caboose, the detective notices
some sticky goo and a sneezy witness. Different flowers shed different pollen;
some children have a flower allergy. Different goo sources leave different
colors and scents. The detective can only solve the case if the clue really
matches the goo source, and the helper item must actually help with the allergy.

The engine tracks:
- physical meters like sticky, sneezing, cleaned, and safe
- emotional memes like curiosity, worry, relief, and pride

The caution/repair constraint is deliberately narrow:
- the chosen allergy trigger must be plausible in the chosen field
- the chosen goo source must leave the chosen clue
- the chosen helper must actually fit the allergy situation

This keeps the stories small, coherent, and state-driven.

Run it
------
python storyworlds/worlds/gpt-5.4/allergy_caboose_goo_flower_field_repetition_dialogue.py
python storyworlds/worlds/gpt-5.4/allergy_caboose_goo_flower_field_repetition_dialogue.py --all
python storyworlds/worlds/gpt-5.4/allergy_caboose_goo_flower_field_repetition_dialogue.py --flower sunflower --goo honey
python storyworlds/worlds/gpt-5.4/allergy_caboose_goo_flower_field_repetition_dialogue.py --goo mud       # rejected
python storyworlds/worlds/gpt-5.4/allergy_caboose_goo_flower_field_repetition_dialogue.py --qa --json
python storyworlds/worlds/gpt-5.4/allergy_caboose_goo_flower_field_repetition_dialogue.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from inside storyworlds/worlds/gpt-5.4/.
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


@dataclass
class FlowerField:
    id: str
    label: str
    blooms: str
    pollen_level: int
    scent: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AllergyType:
    id: str
    label: str
    trigger_flowers: set[str]
    symptom: str
    care: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GooSource:
    id: str
    label: str
    phrase: str
    color: str
    scent: str
    clue: str
    culprit_kind: str
    plausible_flowers: set[str]
    clean_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    helps_allergy: set[str]
    action: str
    ending: str
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


def _r_allergy(world: World) -> list[str]:
    out: list[str] = []
    witness = world.entities.get("witness")
    field_ent = world.entities.get("field")
    if witness is None or field_ent is None:
        return out
    trigger = witness.attrs.get("allergy_match", False)
    if not trigger or field_ent.meters["pollen"] < THRESHOLD:
        return out
    sig = ("allergy", witness.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    witness.meters["sneezing"] += 1
    witness.memes["worry"] += 1
    out.append("__sneeze__")
    return out


def _r_sticky_worry(world: World) -> list[str]:
    caboose = world.entities.get("caboose")
    detective = world.entities.get("detective")
    if caboose is None or detective is None:
        return []
    if caboose.meters["sticky"] < THRESHOLD:
        return []
    sig = ("sticky_worry", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["curiosity"] += 1
    detective.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="allergy", tag="physical", apply=_r_allergy),
    Rule(name="sticky_worry", tag="emotional", apply=_r_sticky_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            new = rule.apply(world)
            if new:
                changed = True
                produced.extend(new)
    if narrate:
        for item in produced:
            if item == "__sneeze__":
                witness = world.get("witness")
                symptom = world.facts["allergy"].symptom
                world.say(f'{witness.id} went, "{symptom}!" and rubbed {witness.pronoun("possessive")} nose.')
    return produced


FIELDS = {
    "sunflower": FlowerField(
        id="sunflower",
        label="sunflower field",
        blooms="tall yellow sunflowers",
        pollen_level=3,
        scent="warm and dusty-sweet",
        tags={"sunflower", "flower_field"},
    ),
    "daisy": FlowerField(
        id="daisy",
        label="daisy field",
        blooms="white daisies nodding in the wind",
        pollen_level=2,
        scent="light and peppery",
        tags={"daisy", "flower_field"},
    ),
    "lavender": FlowerField(
        id="lavender",
        label="lavender field",
        blooms="purple lavender rows",
        pollen_level=1,
        scent="soft and sleepy-sweet",
        tags={"lavender", "flower_field"},
    ),
}

ALLERGIES = {
    "sunflower_pollen": AllergyType(
        id="sunflower_pollen",
        label="sunflower pollen allergy",
        trigger_flowers={"sunflower"},
        symptom="Ah-choo",
        care="less pollen",
        tags={"allergy", "pollen"},
    ),
    "daisy_pollen": AllergyType(
        id="daisy_pollen",
        label="daisy pollen allergy",
        trigger_flowers={"daisy"},
        symptom="Choo",
        care="less pollen",
        tags={"allergy", "pollen"},
    ),
    "lavender_scent": AllergyType(
        id="lavender_scent",
        label="lavender scent allergy",
        trigger_flowers={"lavender"},
        symptom="Hih-tchoo",
        care="fresh air away from the flowers",
        tags={"allergy", "scent"},
    ),
}

GOO = {
    "honey": GooSource(
        id="honey",
        label="honey goo",
        phrase="a stripe of gold goo",
        color="gold",
        scent="sweet like honey",
        clue="a bee's fuzzy stripe stuck in the goo",
        culprit_kind="bee",
        plausible_flowers={"sunflower", "daisy", "lavender"},
        clean_word="sticky honey",
        tags={"goo", "honey", "bee"},
    ),
    "petal_jam": GooSource(
        id="petal_jam",
        label="petal jam goo",
        phrase="a dab of pink goo",
        color="pink",
        scent="rosy and sugary",
        clue="a tiny pink spoon mark in the goo",
        culprit_kind="gardener_cart",
        plausible_flowers={"daisy", "lavender"},
        clean_word="petal jam",
        tags={"goo", "jam"},
    ),
    "sap": GooSource(
        id="sap",
        label="sap goo",
        phrase="a clear string of goo",
        color="clear",
        scent="green and grassy",
        clue="a broken flower stem lying by the step",
        culprit_kind="flower_stem",
        plausible_flowers={"sunflower", "daisy"},
        clean_word="plant sap",
        tags={"goo", "sap"},
    ),
    "mud": GooSource(
        id="mud",
        label="mud goo",
        phrase="a brown splat of goo",
        color="brown",
        scent="earthy",
        clue="a muddy boot print on the floor",
        culprit_kind="boot",
        plausible_flowers=set(),
        clean_word="mud",
        tags={"goo", "mud"},
    ),
}

HELPERS = {
    "handkerchief": Helper(
        id="handkerchief",
        label="handkerchief",
        phrase="a soft blue handkerchief",
        helps_allergy={"sunflower_pollen", "daisy_pollen"},
        action="held the cloth over the sneezy nose and moved to the breezier side of the little train stop",
        ending="The sneezes slowed, and the witness could look at clues without blinking so hard.",
        tags={"handkerchief", "allergy_help"},
    ),
    "mask": Helper(
        id="mask",
        label="paper mask",
        phrase="a little paper mask from the conductor's pocket",
        helps_allergy={"sunflower_pollen", "daisy_pollen", "lavender_scent"},
        action="slipped on the mask and stepped back from the thickest flowers",
        ending="Behind the mask, breathing grew easier and the sneezes became small instead of stormy.",
        tags={"mask", "allergy_help"},
    ),
    "mint_tea": Helper(
        id="mint_tea",
        label="mint tea",
        phrase="a cup of warm mint tea",
        helps_allergy={"lavender_scent"},
        action="sipped the tea beside the open gate where the breeze was plain and fresh",
        ending="The warm steam helped the tight little tickle fade from the witness's nose.",
        tags={"tea", "allergy_help"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "June", "Ruby", "Elsie", "Poppy"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Max", "Finn", "Theo", "Eli", "Owen"]
TRAITS = ["careful", "sharp-eyed", "patient", "curious", "brisk", "thoughtful"]


def clue_matches(goo: GooSource, clue_id: str) -> bool:
    return goo.id == clue_id


def allergy_matches(field_id: str, allergy: AllergyType) -> bool:
    return field_id in allergy.trigger_flowers


def helper_fits(allergy_id: str, helper: Helper) -> bool:
    return allergy_id in helper.helps_allergy


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for field_id in FIELDS:
        for allergy_id, allergy in ALLERGIES.items():
            if not allergy_matches(field_id, allergy):
                continue
            for goo_id, goo in GOO.items():
                if field_id not in goo.plausible_flowers:
                    continue
                if not clue_matches(goo, goo_id):
                    continue
                for helper_id, helper in HELPERS.items():
                    if helper_fits(allergy_id, helper):
                        combos.append((field_id, allergy_id, goo_id, helper_id))
    return combos


def explain_rejection(field_id: str, allergy_id: str, goo_id: str, helper_id: str) -> str:
    if field_id and allergy_id:
        if field_id not in FIELDS:
            return "(No story: unknown flower field.)"
        if allergy_id not in ALLERGIES:
            return "(No story: unknown allergy.)"
        if not allergy_matches(field_id, ALLERGIES[allergy_id]):
            return (
                f"(No story: {ALLERGIES[allergy_id].label} does not fit a "
                f"{FIELDS[field_id].label}. The witness needs an allergy the flowers can really trigger.)"
            )
    if field_id and goo_id and field_id in FIELDS and goo_id in GOO:
        if field_id not in GOO[goo_id].plausible_flowers:
            return (
                f"(No story: {GOO[goo_id].label} is not a sensible caboose clue in a "
                f"{FIELDS[field_id].label}. Pick honey, petal jam, or sap where they belong.)"
            )
    if allergy_id and helper_id and allergy_id in ALLERGIES and helper_id in HELPERS:
        if not helper_fits(allergy_id, HELPERS[helper_id]):
            return (
                f"(No story: {HELPERS[helper_id].label} is not this world's best help for "
                f"{ALLERGIES[allergy_id].label}. The helper must really ease the witness's sneezing.)"
            )
    if goo_id == "mud":
        return "(No story: plain mud is too weak for this little detective mystery. It does not fit the flower-field caboose clues.)"
    return "(No valid combination matches the given options.)"


def predict_sneeze(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    witness = sim.get("witness")
    return witness.meters["sneezing"] >= THRESHOLD


def setup_scene(world: World, detective: Entity, witness: Entity, conductor: Entity,
                field_cfg: FlowerField) -> None:
    for ent in (detective, witness):
        ent.memes["joy"] += 1
    field = world.get("field")
    field.meters["pollen"] = float(field_cfg.pollen_level)
    world.say(
        f"On a bright morning, {detective.id} and {witness.id} rode the little garden train past "
        f"{field_cfg.blooms}. The whole flower field smelled {field_cfg.scent}."
    )
    world.say(
        f"The conductor tapped the red caboose and said, "
        f'"Last stop, last car, best view in the whole field."'
    )
    world.say(
        f'{detective.id} loved mysteries, so {detective.pronoun()} whispered, '
        f'"A caboose is a fine place for a case."'
    )


def discover_goo(world: World, detective: Entity, goo_cfg: GooSource) -> None:
    caboose = world.get("caboose")
    caboose.meters["sticky"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when they climbed into the caboose, {detective.id} stopped short. "
        f"On the shiny wooden seat lay {goo_cfg.phrase}."
    )
    world.say(
        f'"Goo in the caboose," {detective.id} said. "Goo in the caboose."'
    )


def allergy_beat(world: World, witness: Entity, allergy_cfg: AllergyType) -> None:
    predict = predict_sneeze(world)
    world.facts["predicted_sneeze"] = predict
    if predict:
        propagate(world, narrate=True)
        world.say(
            f'"It is my {allergy_cfg.label}," {witness.id} said in a small voice. '
            f'"The flowers tickle my nose before I can think straight."'
        )


def question_clues(world: World, detective: Entity, witness: Entity, goo_cfg: GooSource) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f'{detective.id} bent close, but not too close. "{goo_cfg.color.capitalize()}," '
        f'{detective.pronoun()} murmured. "And it smells {goo_cfg.scent}."'
    )
    world.say(
        f'"Do you see anything else?" asked {detective.id}.'
    )
    world.say(
        f'"Yes," said {witness.id}. "There is {goo_cfg.clue}."'
    )


def flashback(world: World, detective: Entity, witness: Entity, goo_cfg: GooSource) -> None:
    world.para()
    world.say(
        f"Then {detective.id} remembered something from a few minutes before. "
        f"In a quick flashback, {detective.pronoun()} saw the train stop again: "
        f"a tiny shuffle, a glint, a dab of {goo_cfg.color} near the caboose rail."
    )
    if goo_cfg.culprit_kind == "bee":
        world.say(
            f'"A bee!" {detective.id} whispered. "I remember now. A fat bee bumped a paper cup, '
            f'and a drop of honey slid onto the caboose seat."'
        )
    elif goo_cfg.culprit_kind == "gardener_cart":
        world.say(
            f'"The jam cart!" {witness.id} said. "I remember a gardener carrying a jar and pink spoon. '
            f'When the caboose rattled, one sweet drop jumped."'
        )
    else:
        world.say(
            f'"A broken stem!" {detective.id} said. "I remember a child carrying flowers. '
            f'One stem snapped on the step, and clear sap stretched like string."'
        )


def soothe_witness(world: World, witness: Entity, helper_cfg: Helper) -> None:
    witness.meters["sneezing"] = 0.0
    witness.memes["relief"] += 1
    world.say(
        f'The conductor handed over {helper_cfg.phrase}. {witness.id} {helper_cfg.action}.'
    )
    world.say(helper_cfg.ending)


def solve_case(world: World, detective: Entity, goo_cfg: GooSource) -> None:
    detective.memes["pride"] += 1
    caboose = world.get("caboose")
    caboose.attrs["cause"] = goo_cfg.id
    world.say(
        f'{detective.id} straightened up. "Case solved," {detective.pronoun()} said. '
        f'"This was not monster goo. It was {goo_cfg.clean_word}, and the clue told us so."'
    )


def clean_and_end(world: World, detective: Entity, witness: Entity, conductor: Entity,
                  goo_cfg: GooSource, helper_cfg: Helper) -> None:
    caboose = world.get("caboose")
    caboose.meters["sticky"] = 0.0
    caboose.meters["clean"] += 1
    caboose.meters["safe"] += 1
    detective.memes["relief"] += 1
    witness.memes["joy"] += 1
    world.say(
        f'Together they wiped away the {goo_cfg.clean_word}. "{caboose.id.capitalize()} clean, '
        f'case clean," said {detective.id}.'
    )
    world.say(
        f'The conductor laughed. "Detective work and kind help," {conductor.pronoun()} said. '
        f'"That is how a mystery ride should go."'
    )
    world.say(
        f"When the little train rolled on again, the caboose shone, the sneezing had stopped, "
        f"and {witness.id} could finally point at the flowers instead of hiding from them."
    )
    world.say(
        f'{detective.id} looked out over the flower field and whispered one last time, '
        f'"Goo in the caboose, clue in the caboose, and now no goo in the caboose."'
    )


def tell(field_cfg: FlowerField, allergy_cfg: AllergyType, goo_cfg: GooSource, helper_cfg: Helper,
         detective_name: str = "Nora", detective_gender: str = "girl",
         witness_name: str = "Ben", witness_gender: str = "boy",
         parent_type: str = "father", detective_trait: str = "curious") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=[detective_trait],
    ))
    witness = world.add(Entity(
        id=witness_name,
        kind="character",
        type=witness_gender,
        role="witness",
        traits=["sneezy"],
    ))
    conductor = world.add(Entity(
        id="Conductor",
        kind="character",
        type=parent_type,
        role="helper",
        label="the conductor",
    ))
    field = world.add(Entity(
        id="field",
        type="place",
        label=field_cfg.label,
        attrs={"flower_id": field_cfg.id},
        tags=set(field_cfg.tags),
    ))
    caboose = world.add(Entity(
        id="caboose",
        type="train_car",
        label="the caboose",
    ))
    witness.attrs["allergy_id"] = allergy_cfg.id
    witness.attrs["allergy_match"] = allergy_matches(field_cfg.id, allergy_cfg)

    setup_scene(world, detective, witness, conductor, field_cfg)

    world.para()
    discover_goo(world, detective, goo_cfg)
    allergy_beat(world, witness, allergy_cfg)
    question_clues(world, detective, witness, goo_cfg)

    world.para()
    flashback(world, detective, witness, goo_cfg)
    soothe_witness(world, witness, helper_cfg)
    solve_case(world, detective, goo_cfg)

    world.para()
    clean_and_end(world, detective, witness, conductor, goo_cfg, helper_cfg)

    world.facts.update(
        detective=detective,
        witness=witness,
        conductor=conductor,
        field_cfg=field_cfg,
        allergy=allergy_cfg,
        goo=goo_cfg,
        helper=helper_cfg,
        caboose=caboose,
        solved=caboose.attrs.get("cause") == goo_cfg.id,
        cleaned=caboose.meters["clean"] >= THRESHOLD,
        helped=witness.memes["relief"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "allergy": [
        (
            "What is an allergy?",
            "An allergy is when your body reacts strongly to something like pollen, food, or fur. It can make you sneeze, itch, or feel uncomfortable."
        )
    ],
    "pollen": [
        (
            "What is pollen?",
            "Pollen is tiny powder made by flowers and other plants. Wind or insects move it from one flower to another."
        )
    ],
    "caboose": [
        (
            "What is a caboose?",
            "A caboose is the little car at the back of a train. In stories, it is often the very last car."
        )
    ],
    "goo": [
        (
            "What is goo?",
            "Goo is sticky, squishy stuff that can smear or drip. Honey, jam, and sap can all feel gooey."
        )
    ],
    "bee": [
        (
            "Why do bees like flowers?",
            "Bees visit flowers to gather nectar and pollen. As they move from flower to flower, they also help plants grow seeds."
        )
    ],
    "jam": [
        (
            "What is jam made from?",
            "Jam is usually made by cooking fruit or petals with sugar until it gets thick and sweet."
        )
    ],
    "sap": [
        (
            "What is plant sap?",
            "Plant sap is sticky liquid that moves through a plant. If a stem breaks, some sap can leak out."
        )
    ],
    "mask": [
        (
            "Why can a mask help with pollen?",
            "A mask can block some tiny bits of pollen from going into your nose and mouth. That can make sneezing calmer."
        )
    ],
    "handkerchief": [
        (
            "What is a handkerchief?",
            "A handkerchief is a small cloth used to wipe a nose or dry tears. It can help a sneezy child feel more comfortable."
        )
    ],
    "tea": [
        (
            "Why can warm tea feel soothing?",
            "Warm tea can feel gentle in your throat and nose. The steam and warmth can make you feel calmer for a little while."
        )
    ],
}
KNOWLEDGE_ORDER = ["allergy", "pollen", "caboose", "goo", "bee", "jam", "sap", "mask", "handkerchief", "tea"]


@dataclass
class StoryParams:
    flower: str
    allergy: str
    goo: str
    helper: str
    detective_name: str
    detective_gender: str
    witness_name: str
    witness_gender: str
    conductor: str
    detective_trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    witness = f["witness"]
    field_cfg = f["field_cfg"]
    goo_cfg = f["goo"]
    allergy_cfg = f["allergy"]
    return [
        (
            f'Write a tiny detective story for a 3-to-5-year-old set in a {field_cfg.label} '
            f'that includes the words "allergy", "caboose", and "goo".'
        ),
        (
            f"Tell a mystery where {detective.id} finds {goo_cfg.phrase} in a caboose, while "
            f"{witness.id}'s allergy keeps interrupting the investigation with sneezes, and solve it gently."
        ),
        (
            f"Write a child-friendly flower-field case with dialogue, repetition, and a flashback, "
            f"where the final clue shows the goo was really {goo_cfg.clean_word}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    witness = f["witness"]
    field_cfg = f["field_cfg"]
    goo_cfg = f["goo"]
    helper_cfg = f["helper"]
    allergy_cfg = f["allergy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a little detective, and {witness.id}, the sneezy witness. They ride a small train through a {field_cfg.label}."
        ),
        (
            "What mystery did they find in the caboose?",
            f"They found {goo_cfg.phrase} on the caboose seat. That sticky mess turned the train ride into a detective case."
        ),
        (
            f"Why did {witness.id} keep sneezing?",
            f"{witness.id} had a {allergy_cfg.label}, and the flowers in the field bothered {witness.pronoun('possessive')} nose. The sneezing made it harder to look at clues until help arrived."
        ),
        (
            "How did the detective solve the case?",
            f"{detective.id} noticed the color, smell, and clue near the goo, then remembered an earlier moment in a flashback. Those details showed that the goo was really {goo_cfg.clean_word}."
        ),
        (
            f"How did they help the witness?",
            f"They used {helper_cfg.phrase} so {witness.id} could feel better. After that, the sneezing slowed, and the witness could help with the mystery again."
        ),
        (
            "How did the story end?",
            f"They cleaned the caboose, solved the mystery, and rode on safely through the flower field. The ending shows both problems changed: the goo was gone, and the sneezing had calmed."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"allergy", "caboose", "goo", "pollen"}
    goo_id = f["goo"].id
    helper_id = f["helper"].id
    if goo_id == "honey":
        tags.add("bee")
    elif goo_id == "petal_jam":
        tags.add("jam")
    elif goo_id == "sap":
        tags.add("sap")
    if helper_id == "mask":
        tags.add("mask")
    elif helper_id == "handkerchief":
        tags.add("handkerchief")
    elif helper_id == "mint_tea":
        tags.add("tea")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in e.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        flower="sunflower",
        allergy="sunflower_pollen",
        goo="honey",
        helper="mask",
        detective_name="Nora",
        detective_gender="girl",
        witness_name="Ben",
        witness_gender="boy",
        conductor="father",
        detective_trait="sharp-eyed",
    ),
    StoryParams(
        flower="daisy",
        allergy="daisy_pollen",
        goo="petal_jam",
        helper="handkerchief",
        detective_name="Leo",
        detective_gender="boy",
        witness_name="Ruby",
        witness_gender="girl",
        conductor="mother",
        detective_trait="patient",
    ),
    StoryParams(
        flower="sunflower",
        allergy="sunflower_pollen",
        goo="sap",
        helper="mask",
        detective_name="Ava",
        detective_gender="girl",
        witness_name="Finn",
        witness_gender="boy",
        conductor="father",
        detective_trait="thoughtful",
    ),
    StoryParams(
        flower="lavender",
        allergy="lavender_scent",
        goo="honey",
        helper="mint_tea",
        detective_name="Sam",
        detective_gender="boy",
        witness_name="Elsie",
        witness_gender="girl",
        conductor="mother",
        detective_trait="curious",
    ),
]


ASP_RULES = r"""
allergy_matches(F, A) :- field(F), allergy(A), triggered_by(A, F).
goo_fits(F, G) :- field(F), goo(G), goo_flower(G, F).
helper_fits(A, H) :- allergy(A), helper(H), helps(H, A).

valid(F, A, G, H) :- allergy_matches(F, A), goo_fits(F, G), helper_fits(A, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for field_id in FIELDS:
        lines.append(asp.fact("field", field_id))
    for allergy_id, allergy in ALLERGIES.items():
        lines.append(asp.fact("allergy", allergy_id))
        for field_id in sorted(allergy.trigger_flowers):
            lines.append(asp.fact("triggered_by", allergy_id, field_id))
    for goo_id, goo in GOO.items():
        lines.append(asp.fact("goo", goo_id))
        for field_id in sorted(goo.plausible_flowers):
            lines.append(asp.fact("goo_flower", goo_id, field_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for allergy_id in sorted(helper.helps_allergy):
            lines.append(asp.fact("helps", helper_id, allergy_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
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
        if not sample.story or "caboose" not in sample.story.lower():
            raise StoryError("Smoke test failed: generated story missing expected content.")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective solves goo in a caboose while helping a sneezy friend in a flower field."
    )
    ap.add_argument("--flower", choices=FIELDS)
    ap.add_argument("--allergy", choices=ALLERGIES)
    ap.add_argument("--goo", choices=GOO)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--conductor", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goo == "mud":
        raise StoryError(explain_rejection(args.flower or "", args.allergy or "", "mud", args.helper or ""))

    if args.flower and args.allergy:
        if not allergy_matches(args.flower, ALLERGIES[args.allergy]):
            raise StoryError(explain_rejection(args.flower, args.allergy, args.goo or "", args.helper or ""))

    if args.flower and args.goo:
        if args.goo not in GOO:
            raise StoryError("(No story: unknown goo source.)")
        if args.flower not in GOO[args.goo].plausible_flowers:
            raise StoryError(explain_rejection(args.flower, args.allergy or "", args.goo, args.helper or ""))

    if args.allergy and args.helper:
        if not helper_fits(args.allergy, HELPERS[args.helper]):
            raise StoryError(explain_rejection(args.flower or "", args.allergy, args.goo or "", args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.flower is None or combo[0] == args.flower)
        and (args.allergy is None or combo[1] == args.allergy)
        and (args.goo is None or combo[2] == args.goo)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    flower, allergy_id, goo_id, helper_id = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    witness_gender = rng.choice(["girl", "boy"])
    detective_name = _pick_name(rng, detective_gender)
    witness_name = _pick_name(rng, witness_gender, avoid=detective_name)
    conductor = args.conductor or rng.choice(["mother", "father"])
    detective_trait = rng.choice(TRAITS)
    return StoryParams(
        flower=flower,
        allergy=allergy_id,
        goo=goo_id,
        helper=helper_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        witness_name=witness_name,
        witness_gender=witness_gender,
        conductor=conductor,
        detective_trait=detective_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.flower not in FIELDS:
        raise StoryError(f"(No story: unknown flower field '{params.flower}'.)")
    if params.allergy not in ALLERGIES:
        raise StoryError(f"(No story: unknown allergy '{params.allergy}'.)")
    if params.goo not in GOO:
        raise StoryError(f"(No story: unknown goo source '{params.goo}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not allergy_matches(params.flower, ALLERGIES[params.allergy]):
        raise StoryError(explain_rejection(params.flower, params.allergy, params.goo, params.helper))
    if params.flower not in GOO[params.goo].plausible_flowers or params.goo == "mud":
        raise StoryError(explain_rejection(params.flower, params.allergy, params.goo, params.helper))
    if not helper_fits(params.allergy, HELPERS[params.helper]):
        raise StoryError(explain_rejection(params.flower, params.allergy, params.goo, params.helper))

    world = tell(
        field_cfg=FIELDS[params.flower],
        allergy_cfg=ALLERGIES[params.allergy],
        goo_cfg=GOO[params.goo],
        helper_cfg=HELPERS[params.helper],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        witness_name=params.witness_name,
        witness_gender=params.witness_gender,
        parent_type=params.conductor,
        detective_trait=params.detective_trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (flower, allergy, goo, helper) combos:\n")
        for flower, allergy_id, goo_id, helper_id in combos:
            print(f"  {flower:10} {allergy_id:18} {goo_id:10} {helper_id}")
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
            header = f"### {p.detective_name} and {p.witness_name}: {p.goo} in the caboose at {p.flower}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
