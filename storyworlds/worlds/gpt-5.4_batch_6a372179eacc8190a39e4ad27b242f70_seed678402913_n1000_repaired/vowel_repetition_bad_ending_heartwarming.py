#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vowel_repetition_bad_ending_heartwarming.py
======================================================================

A standalone story world about a child who makes a string of bright vowel cards
and longs to show them off outside. The world models a small, concrete conflict:
some craft materials do not stand up to wind or rain, and only certain fixes
really protect them.

The seed asked for:
- the word "vowel"
- repetition
- a bad ending
- a heartwarming style

This world bakes repetition into the tale through a little vowel chant:
"A, E, I, O, U."
It also supports both protected and sad outcomes, with curated examples that
include bad endings. Even the sad endings stay child-facing and warm: the craft
can be spoiled, but the caring relationship remains.

Run it
------
    python storyworlds/worlds/gpt-5.4/vowel_repetition_bad_ending_heartwarming.py
    python storyworlds/worlds/gpt-5.4/vowel_repetition_bad_ending_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/vowel_repetition_bad_ending_heartwarming.py --setting garden --material paper_chain
    python storyworlds/worlds/gpt-5.4/vowel_repetition_bad_ending_heartwarming.py --response pocket
    python storyworlds/worlds/gpt-5.4/vowel_repetition_bad_ending_heartwarming.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
class Setting:
    id: str
    place: str
    hazard: str
    sky: str
    sound: str
    invitation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    make_line: str
    vulnerable: set[str] = field(default_factory=set)
    fragility: int = 1
    damage_text: str = ""
    bad_image: str = ""
    safe_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    power: int
    protects: set[str] = field(default_factory=set)
    offer: str = ""
    success: str = ""
    failure: str = ""
    qa_text: str = ""
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


def _r_damage_sadness(world: World) -> list[str]:
    out: list[str] = []
    craft = world.entities.get("craft")
    child = world.entities.get("child")
    if craft is None or child is None:
        return out
    if craft.meters["spoiled"] < THRESHOLD:
        return out
    sig = ("sadness", craft.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["sadness"] += 1
    child.memes["hope"] -= 0.5
    out.append("__spoiled__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_sadness", tag="emotional", apply=_r_damage_sadness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            new_bits = rule.apply(world)
            if new_bits:
                changed = True
                produced.extend(s for s in new_bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the little garden",
        hazard="rain",
        sky="gray clouds hanging low",
        sound="soft rain tapping the leaves",
        invitation="the wet path outside the back door",
        tags={"rain", "outside"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        hazard="wind",
        sky="a bright sky and quick racing clouds",
        sound="wind skipping around the wooden posts",
        invitation="the breezy steps by the porch rail",
        tags={"wind", "outside"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the stone courtyard",
        hazard="wind",
        sky="white clouds sailing past the roof",
        sound="wind fluttering through the gate",
        invitation="the open square between the flower beds",
        tags={"wind", "outside"},
    ),
    "yard": Setting(
        id="yard",
        place="the backyard",
        hazard="rain",
        sky="a silver sky full of drizzle",
        sound="tiny drops pattering on the fence",
        invitation="the shiny grass past the kitchen step",
        tags={"rain", "outside"},
    ),
}

MATERIALS = {
    "paper_chain": Material(
        id="paper_chain",
        label="paper chain",
        phrase="a string of paper cards, each with one careful vowel painted on it",
        make_line="They painted one card after another: A, E, I, O, U.",
        vulnerable={"rain"},
        fragility=2,
        damage_text="the colors ran together until the neat vowel letters turned soft and blurry",
        bad_image="The soggy chain drooped over the child's hands like a wilted ribbon.",
        safe_image="The cards stayed bright and flat, and every vowel could still be read at a glance.",
        tags={"paper", "vowel", "rain"},
    ),
    "chalk_cards": Material(
        id="chalk_cards",
        label="chalk cards",
        phrase="five dark cards dusted with chalky vowel letters",
        make_line="The child whispered and then sang the same line each time: A, E, I, O, U.",
        vulnerable={"rain"},
        fragility=3,
        damage_text="the chalk slid into pale streaks, and the vowel shapes vanished under damp smudges",
        bad_image="Only gray smears were left where the proud vowels had been.",
        safe_image="The dark cards stayed crisp, with white vowel lines shining on top.",
        tags={"chalk", "vowel", "rain"},
    ),
    "tissue_streamer": Material(
        id="tissue_streamer",
        label="tissue streamer",
        phrase="a tissue-paper streamer with the vowels tied along it in order",
        make_line='Every tie came with the same happy murmur: "A, E, I, O, U."',
        vulnerable={"wind"},
        fragility=2,
        damage_text="the thin streamer tore and the vowel pieces flapped away in the gusts",
        bad_image="A few torn scraps clung to the string while the rest danced off across the stones.",
        safe_image="The streamer only trembled a little, and the vowels lined up like tiny flags.",
        tags={"wind", "vowel", "paper"},
    ),
    "leaf_garland": Material(
        id="leaf_garland",
        label="leaf garland",
        phrase="a leaf garland with round vowel letters brushed onto the leaves",
        make_line="Leaf after leaf, they said it together: A, E, I, O, U.",
        vulnerable={"wind"},
        fragility=1,
        damage_text="the light leaves snapped loose from the string and whirled away before anyone could catch them",
        bad_image="The bare string hung from the child's fingers with only one leaf left at the end.",
        safe_image="The leaves swayed gently but stayed tied in place, each vowel rocking in order.",
        tags={"wind", "leaf", "vowel"},
    ),
    "foam_tiles": Material(
        id="foam_tiles",
        label="foam tiles",
        phrase="five soft foam tiles with big vowel letters on them",
        make_line="They pressed the vowels in order: A, E, I, O, U.",
        vulnerable=set(),
        fragility=1,
        damage_text="nothing much happened to them at all",
        bad_image="The tiles were still fine.",
        safe_image="The tiles bounced lightly and stayed clear and safe.",
        tags={"vowel"},
    ),
}

RESPONSES = {
    "indoors": Response(
        id="indoors",
        label="stay indoors",
        sense=3,
        power=4,
        protects={"rain", "wind"},
        offer="keep the craft by the window instead and sing the vowels to the outside from indoors",
        success="They carried the craft to the window seat instead, where the weather could be seen but not touch it.",
        failure="They headed for the window too late, after the weather had already spoiled the craft.",
        qa_text="kept the craft indoors by the window",
        tags={"indoors", "window"},
    ),
    "umbrella": Response(
        id="umbrella",
        label="umbrella",
        sense=2,
        power=2,
        protects={"rain"},
        offer="take the craft out only under the big red umbrella",
        success="The helper opened the big red umbrella over both heads and over the careful vowels too.",
        failure="The umbrella came up too slowly, and the rain had already kissed the letters.",
        qa_text="held the craft under a big umbrella",
        tags={"umbrella", "rain"},
    ),
    "clothespins": Response(
        id="clothespins",
        label="clothespins",
        sense=2,
        power=2,
        protects={"wind"},
        offer="clip the craft safely to the line with little clothespins before showing it outside",
        success="The helper clipped the craft fast with little clothespins so the breeze could tug without stealing it.",
        failure="The clothespins came too late, and the wind had already jerked the craft out of reach.",
        qa_text="clipped the craft with little clothespins",
        tags={"clothespins", "wind"},
    ),
    "pocket": Response(
        id="pocket",
        label="pocket",
        sense=1,
        power=1,
        protects={"rain", "wind"},
        offer="stuff it into a coat pocket and hope for the best",
        success="They crammed it into a pocket.",
        failure="They tried to hide it in a pocket, but that only crumpled it more.",
        qa_text="stuffed the craft into a pocket",
        tags={"pocket"},
    ),
}


GIRL_NAMES = ["Lila", "Mina", "Nora", "Ella", "Ruby", "Zoe"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Eli", "Noah", "Finn"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["careful", "eager", "gentle", "curious", "hopeful"]


def hazard_at_risk(setting: Setting, material: Material) -> bool:
    return setting.hazard in material.vulnerable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def can_protect(setting: Setting, material: Material, response: Response) -> bool:
    return setting.hazard in response.protects and response.sense >= SENSE_MIN


def best_response_ids_for(setting: Setting, material: Material) -> list[str]:
    return [
        rid for rid, resp in RESPONSES.items()
        if can_protect(setting, material, resp)
    ]


def severity(material: Material, delay: int) -> int:
    return material.fragility + delay


def is_saved(setting: Setting, material: Material, response: Response, delay: int) -> bool:
    return can_protect(setting, material, response) and response.power >= severity(material, delay)


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for sid, setting in SETTINGS.items():
        for mid, material in MATERIALS.items():
            if hazard_at_risk(setting, material) and best_response_ids_for(setting, material):
                out.append((sid, mid))
    return out


@dataclass
class StoryParams:
    setting: str
    material: str
    response: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def chant() -> str:
    return "A, E, I, O, U."


def _do_damage(world: World, material: Material, setting: Setting, narrate: bool = True) -> None:
    craft = world.get("craft")
    craft.meters["spoiled"] += 1
    craft.meters[setting.hazard] += 1
    propagate(world, narrate=narrate)


def predict_damage(world: World, material: Material, setting: Setting) -> dict:
    sim = world.copy()
    _do_damage(sim, material, setting, narrate=False)
    craft = sim.get("craft")
    child = sim.get("child")
    return {
        "spoiled": craft.meters["spoiled"] >= THRESHOLD,
        "sadness": child.memes["sadness"],
    }


def introduce(world: World, child: Entity, helper: Entity, material: Material) -> None:
    child.memes["joy"] += 1
    world.say(
        f"One soft afternoon, {child.id} sat at the kitchen table with {child.pronoun('possessive')} "
        f"{helper.label_word}. Between them lay glue, string, bright paint, and {material.phrase}."
    )
    world.say(material.make_line)
    world.say(
        f'Each time a fresh letter was finished, {child.id} tapped the table and said it again: '
        f'"{chant()}"'
    )


def desire_outside(world: World, child: Entity, setting: Setting) -> None:
    child.memes["hope"] += 1
    world.say(
        f"When the last card was tied on, {child.id} hurried to {setting.invitation}. "
        f"{setting.sky} could be seen outside, and there was {setting.sound}."
    )
    world.say(
        f'"I want to show my vowel string in {setting.place}," {child.id} said. '
        f'"{chant()}"'
    )


def warn(world: World, child: Entity, helper: Entity, material: Material, setting: Setting) -> None:
    pred = predict_damage(world, material, setting)
    world.facts["predicted_spoiled"] = pred["spoiled"]
    child.memes["impatience"] += 1
    world.say(
        f'{helper.label_word.capitalize()} looked at the sky and then at the careful craft. '
        f'"Wait a moment," {helper.pronoun()} said. "That {setting.hazard} is not kind to a {material.label}. '
        f'If we rush out, {material.damage_text}."'
    )


def offer_fix(world: World, helper: Entity, response: Response) -> None:
    world.say(
        f'"Let us {response.offer}," {helper.pronoun()} said gently.'
    )


def dash(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But the wish to show it right now tugged harder. {child.id} hugged the string to {child.pronoun('possessive')} chest and ran ahead anyway."
    )


def use_fix(world: World, child: Entity, helper: Entity, response: Response) -> None:
    child.memes["trust"] += 1
    child.memes["hope"] += 1
    world.say(
        f"{child.id} stopped, listened, and nodded. {response.success}"
    )


def bad_turn(world: World, child: Entity, helper: Entity, material: Material, setting: Setting, response: Response) -> None:
    _do_damage(world, material, setting, narrate=False)
    world.say(
        f"Outside, the {setting.hazard} found the craft at once. {material.damage_text}."
    )
    world.say(material.bad_image)
    child.memes["love"] += 1
    helper.memes["care"] += 1
    world.say(
        f'{child.id} stood very still. "{chant()}" {child.pronoun()} whispered, but the sound came out small.'
    )
    world.say(
        f"{helper.label_word.capitalize()} knelt beside {child.id} and put an arm around {child.pronoun('object')}. "
        f'"Oh, my dear," {helper.pronoun()} said softly. "The string is hurt, but you are not, and the vowels are still with us."'
    )
    world.say(
        f'Together they said the line once more, slower this time: "{chant()}"'
    )
    world.say(
        f"The craft was spoiled, and that was sad. Still, the two voices stayed warm in the damp air, and they walked back inside holding hands."
    )


def good_turn(world: World, child: Entity, helper: Entity, material: Material, setting: Setting, response: Response) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In that safer place, the weather could only watch. {material.safe_image}"
    )
    world.say(
        f'{child.id} grinned and sang it proudly once more: "{chant()}"'
    )
    world.say(
        f"{helper.label_word.capitalize()} joined in, and soon the room felt full of bright little sounds. "
        f"The vowel string stayed safe, and so did the moment."
    )


def tell(
    setting: Setting,
    material: Material,
    response: Response,
    child_name: str = "Lila",
    child_gender: str = "girl",
    helper_type: str = "grandmother",
    trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        label=child_name,
        tags={"child"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        tags={"adult"},
    ))
    craft = world.add(Entity(
        id="craft",
        kind="thing",
        type="craft",
        label=material.label,
        phrase=material.phrase,
        tags=set(material.tags),
    ))

    introduce(world, child, helper, material)
    world.para()
    desire_outside(world, child, setting)
    warn(world, child, helper, material, setting)
    offer_fix(world, helper, response)
    world.para()

    saved = is_saved(setting, material, response, delay)
    if saved:
        use_fix(world, child, helper, response)
        good_turn(world, child, helper, material, setting, response)
        outcome = "saved"
    else:
        dash(world, child)
        if delay > 0:
            world.say(
                f"For one tiny moment, everyone was too slow."
            )
        bad_turn(world, child, helper, material, setting, response)
        outcome = "spoiled"

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        material=material,
        response=response,
        craft=craft,
        delay=delay,
        outcome=outcome,
        spoiled=craft.meters["spoiled"] >= THRESHOLD,
        saved=(outcome == "saved"),
    )
    return world


KNOWLEDGE = {
    "vowel": [
        (
            "What is a vowel?",
            "A vowel is one of the special letters A, E, I, O, and U. We use vowels in many words when we speak and write."
        )
    ],
    "rain": [
        (
            "Why can rain ruin paper crafts?",
            "Rain makes paper wet and soft. When paper gets too wet, colors can run and the shape can sag or tear."
        )
    ],
    "wind": [
        (
            "Why can wind carry light things away?",
            "Wind pushes on light things like leaves and thin paper. If they are not held tight, the air can whisk them away."
        )
    ],
    "umbrella": [
        (
            "What does an umbrella do?",
            "An umbrella opens above you and helps keep rain off. It can protect heads, hands, and small things you are carrying."
        )
    ],
    "clothespins": [
        (
            "What are clothespins for?",
            "Clothespins are little clips that hold cloth or paper in place. They help keep light things from blowing away."
        )
    ],
    "indoors": [
        (
            "Why is indoors safer in bad weather?",
            "Indoors means inside a house or room, away from rain and wind. A craft can stay dry and calm there."
        )
    ],
    "paper": [
        (
            "Why is paper easy to damage?",
            "Paper is thin and light. Water can make it soggy, and rough wind can bend or tear it."
        )
    ],
    "leaf": [
        (
            "Why do leaves blow away easily?",
            "Leaves are light and flat, so moving air can lift them. That is why they skitter and spin on windy days."
        )
    ],
}
KNOWLEDGE_ORDER = ["vowel", "rain", "wind", "umbrella", "clothespins", "indoors", "paper", "leaf"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    material = f["material"]
    response = f["response"]
    outcome = f["outcome"]
    if outcome == "spoiled":
        return [
            'Write a heartwarming story for a young child that includes the word "vowel" and the repeated line "A, E, I, O, U."',
            f"Tell a gentle sad story where {child.id} makes a {material.label}, hurries outside to {setting.place}, and the {setting.hazard} ruins it.",
            f"Write a child-facing story with repetition and a bad ending, but keep the ending loving: the craft is lost, yet a caring grown-up helps the child say the vowels again.",
        ]
    return [
        'Write a heartwarming story for a young child that includes the word "vowel" and the repeated line "A, E, I, O, U."',
        f"Tell a gentle story where {child.id} makes a {material.label}, wants to show it in {setting.place}, and a grown-up uses {response.label} to keep it safe.",
        f"Write a story with repetition, weather, and a caring fix that lets the child keep the vowel craft safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    material = f["material"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {helper.label_word}, who made a {material.label} together. The craft mattered because they built it with care and a shared little chant."
        ),
        (
            "What did they make together?",
            f"They made {material.phrase}. As they worked, they kept repeating the same vowel line: {chant()}"
        ),
        (
            f"Why did {helper.label_word} warn {child.id}?",
            f"{helper.label_word.capitalize()} warned {child.id} because the weather outside was dangerous for the craft. In this story, {setting.hazard} could spoil a {material.label}, so the warning came from a real risk, not from fussing."
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                "How did they keep the craft safe?",
                f"They used {response.label} to protect it before the weather could touch it. That worked because {response.label} was a sensible way to guard the craft from {setting.hazard}."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the vowel craft still bright and clear. {child.id} and {helper.label_word} said the vowels together again, and the safe ending showed that listening helped."
            )
        )
    else:
        qa.append(
            (
                "What bad thing happened to the craft?",
                f"The {setting.hazard} spoiled it, and {material.damage_text}. The ending is sad because the careful work could not be saved in time."
            )
        )
        qa.append(
            (
                "Was the ending only sad?",
                f"No. The craft was ruined, which was the bad ending, but {helper.label_word} stayed close and kind. They repeated the vowels together again, so the child was comforted even after the loss."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"vowel"} | set(f["setting"].tags) | set(f["material"].tags) | set(f["response"].tags)
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        material="paper_chain",
        response="umbrella",
        child_name="Lila",
        child_gender="girl",
        helper_type="grandmother",
        trait="eager",
        delay=1,
    ),
    StoryParams(
        setting="porch",
        material="tissue_streamer",
        response="clothespins",
        child_name="Owen",
        child_gender="boy",
        helper_type="grandfather",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        setting="yard",
        material="chalk_cards",
        response="umbrella",
        child_name="Mina",
        child_gender="girl",
        helper_type="mother",
        trait="hopeful",
        delay=0,
    ),
    StoryParams(
        setting="courtyard",
        material="leaf_garland",
        response="clothespins",
        child_name="Theo",
        child_gender="boy",
        helper_type="father",
        trait="curious",
        delay=1,
    ),
    StoryParams(
        setting="garden",
        material="paper_chain",
        response="indoors",
        child_name="Ruby",
        child_gender="girl",
        helper_type="grandfather",
        trait="gentle",
        delay=0,
    ),
]


def explain_rejection(setting: Setting, material: Material) -> str:
    if not material.vulnerable:
        return (
            f"(No story: a {material.label} is not really at risk from the weather in {setting.place}, "
            f"so there is no honest warning and no turn.)"
        )
    return (
        f"(No story: {setting.place} has {setting.hazard}, but a {material.label} is not vulnerable to that. "
        f"Pick a material the weather could really spoil.)"
    )


def explain_response(response_id: str) -> str:
    resp = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too weak or silly for this world "
        f"(sense={resp.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    setting = SETTINGS[params.setting]
    material = MATERIALS[params.material]
    response = RESPONSES[params.response]
    return "saved" if is_saved(setting, material, response, params.delay) else "spoiled"


ASP_RULES = r"""
hazard_at_risk(S, M) :- setting(S), material(M), hazard(S, H), vulnerable(M, H).
sensible(R) :- response(R), sense(R, V), sense_min(Min), V >= Min.
can_protect(S, M, R) :- hazard_at_risk(S, M), response(R), hazard(S, H), protects(R, H), sensible(R).
valid(S, M) :- hazard_at_risk(S, M), can_protect(S, M, _).

severity(F + D) :- chosen_material(M), fragility(M, F), delay(D).
works :- chosen_setting(S), chosen_material(M), chosen_response(R),
         can_protect(S, M, R), power(R, P), severity(V), P >= V.

outcome(saved) :- works.
outcome(spoiled) :- not works.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("hazard", sid, setting.hazard))
    for mid, material in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        lines.append(asp.fact("fragility", mid, material.fragility))
        for haz in sorted(material.vulnerable):
            lines.append(asp.fact("vulnerable", mid, haz))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for haz in sorted(response.protects):
            lines.append(asp.fact("protects", rid, haz))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_material", params.material),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a vowel craft, weather, repetition, and a caring ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how late the fix is")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.material:
        setting = SETTINGS[args.setting]
        material = MATERIALS[args.material]
        if not hazard_at_risk(setting, material):
            raise StoryError(explain_rejection(setting, material))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.material is None or combo[1] == args.material)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, material_id = rng.choice(sorted(combos))
    setting = SETTINGS[setting_id]
    material = MATERIALS[material_id]
    response_choices = [
        rid for rid, resp in RESPONSES.items()
        if can_protect(setting, material, resp)
    ]
    if args.response is not None:
        response_id = args.response
        if response_id not in response_choices:
            raise StoryError(
                f"(No story: {RESPONSES[response_id].label} does not really protect a {material.label} from {setting.hazard}.)"
            )
    else:
        response_id = rng.choice(sorted(response_choices))

    gender = args.child_gender or rng.choice(["girl", "boy"])
    name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    return StoryParams(
        setting=setting_id,
        material=material_id,
        response=response_id,
        child_name=name,
        child_gender=gender,
        helper_type=helper,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Invalid material: {params.material})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")

    setting = SETTINGS[params.setting]
    material = MATERIALS[params.material]
    response = RESPONSES[params.response]

    if not hazard_at_risk(setting, material):
        raise StoryError(explain_rejection(setting, material))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        material=material,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        trait=params.trait,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, material) combos:\n")
        for setting, material in combos:
            print(f"  {setting:10} {material}")
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
            header = f"### {p.child_name}: {p.material} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
