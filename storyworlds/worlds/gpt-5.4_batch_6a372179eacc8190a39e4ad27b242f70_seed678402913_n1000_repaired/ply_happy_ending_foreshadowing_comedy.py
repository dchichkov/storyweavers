#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ply_happy_ending_foreshadowing_comedy.py
===================================================================

A small storyworld about a child making a ridiculous costume prop for a funny
little show. The core constraint is physical: a floppy material cannot hold up a
big, bouncy prop during a lively performance, while a sturdier multi-ply
material can.

The seed required the word "ply", a happy ending, and foreshadowing in a comic
style. This world therefore centers "ply" in the material vocabulary
("three-ply cardboard"), makes the coming wobble visible before the show, and
lands on a kind, silly ending where the problem is fixed and the show becomes
even better.

Run it
------
    python storyworlds/worlds/gpt-5.4/ply_happy_ending_foreshadowing_comedy.py
    python storyworlds/worlds/gpt-5.4/ply_happy_ending_foreshadowing_comedy.py --theme moose --material cardboard_three_ply
    python storyworlds/worlds/gpt-5.4/ply_happy_ending_foreshadowing_comedy.py --material tissue_one_ply
    python storyworlds/worlds/gpt-5.4/ply_happy_ending_foreshadowing_comedy.py --all
    python storyworlds/worlds/gpt-5.4/ply_happy_ending_foreshadowing_comedy.py --qa
    python storyworlds/worlds/gpt-5.4/ply_happy_ending_foreshadowing_comedy.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so go up three levels to
# reach storyworlds/ and import results.py from there.
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
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
class Theme:
    id: str
    prop_name: str
    prop_phrase: str
    head_part: str
    opening_image: str
    boast: str
    finale: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    stiffness: int
    silliness: str
    ply_text: str
    flimsy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Motion:
    id: str
    verb: str
    gerund: str
    force: int
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    bonus: int
    text: str
    qa_text: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    prop = world.get("prop")
    if prop.meters["strain"] < THRESHOLD:
        return out
    if ("wobble", "prop") in world.fired:
        return out
    world.fired.add(("wobble", "prop"))
    prop.meters["wobble"] += 1
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["alarm"] += 1
    helper.memes["notice"] += 1
    out.append("__wobble__")
    return out


def _r_collapse(world: World) -> list[str]:
    out: list[str] = []
    prop = world.get("prop")
    if prop.meters["strain"] < 2 * THRESHOLD:
        return out
    if ("collapse", "prop") in world.fired:
        return out
    world.fired.add(("collapse", "prop"))
    prop.meters["collapsed"] += 1
    hero = world.get("hero")
    audience = world.get("audience")
    hero.memes["embarrassment"] += 1
    audience.memes["surprise"] += 1
    out.append("__collapse__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="collapse", tag="physical", apply=_r_collapse),
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
        for s in produced:
            world.say(s)
    return produced


def support_margin(material: Material, motion: Motion, fix: Fix) -> int:
    return material.stiffness + fix.bonus - motion.force


def valid_combo(material: Material, motion: Motion, fix: Fix) -> bool:
    return fix.sense >= SENSE_MIN and support_margin(material, motion, fix) >= 0


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def predict_trouble(world: World, motion: Motion) -> dict:
    sim = world.copy()
    perform(sim, motion, narrate=False)
    prop = sim.get("prop")
    return {
        "wobble": prop.meters["wobble"] >= THRESHOLD,
        "collapse": prop.meters["collapsed"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, theme: Theme, material: Material) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    prop = world.get("prop")
    world.say(
        f"On the morning of the neighborhood talent picnic, {hero.id} decided to wear "
        f"{theme.prop_phrase} for a silly one-song show. {theme.opening_image}"
    )
    world.say(
        f"{helper.id} helped tape together the {material.label} {theme.head_part}, and "
        f"the kitchen table disappeared under scraps, string, and very serious faces."
    )
    world.say(
        f'"{theme.boast}" {hero.id} said, lifting the {prop.label} high. '
        f'"It is made of {material.ply_text}, so it looks extra grand."'
    )


def foreshadow(world: World, hero: Entity, helper: Entity, theme: Theme, material: Material, motion: Motion) -> None:
    pred = predict_trouble(world, motion)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_collapse"] = pred["collapse"]
    if pred["collapse"]:
        helper.memes["concern"] += 1
        world.say(
            f"But when {hero.id} tried one proud {motion.verb} in the kitchen, the "
            f"{theme.head_part} gave a soft {motion.sound}. One side drooped, then sprang back as if it were thinking about giving up."
        )
        world.say(
            f'{helper.id} squinted at it. "That {material.label} looks a little {material.silliness}," '
            f'{helper.pronoun()} said. "Maybe the show should stay gentle."'
        )
    elif pred["wobble"]:
        helper.memes["concern"] += 1
        world.say(
            f"When {hero.id} practiced a tiny {motion.verb}, the {theme.head_part} bobbed from side to side. "
            f"It did not fall yet, but it looked as if it had ideas of its own."
        )
        world.say(
            f'{helper.id} laughed. "Your {theme.prop_name} is already trying to dance before the music starts," '
            f'{helper.pronoun()} said.'
        )
    else:
        world.say(
            f"When {hero.id} practiced a tiny {motion.verb}, the {theme.head_part} stayed brave and straight. "
            f'Even so, {helper.id} tapped it and said, "Good thing that sturdy {material.ply_text} is doing its job."'
        )


def parade_to_show(world: World, hero: Entity) -> None:
    world.say(
        f"By afternoon, {hero.id} marched into the picnic yard as if a parade had been invented only for {hero.pronoun('object')}. "
        f"Children turned around. A dog barked once. Someone dropped half a cracker from laughing."
    )


def perform(world: World, motion: Motion, narrate: bool = True) -> None:
    prop = world.get("prop")
    hero = world.get("hero")
    prop.meters["strain"] += motion.force
    hero.memes["showoff"] += 1
    propagate(world, narrate=narrate)


def comic_disaster(world: World, hero: Entity, theme: Theme, motion: Motion) -> None:
    perform(world, motion, narrate=False)
    prop = world.get("prop")
    if prop.meters["collapsed"] >= THRESHOLD:
        world.say(
            f"Then the music started, and {hero.id} tried the biggest {motion.verb} of the day. "
            f"{motion.sound.capitalize()} The {theme.head_part} folded forward and plopped over {hero.pronoun('possessive')} eyes."
        )
        world.say(
            f"For one second, all anyone could see was a pair of shoes, two waving arms, and a wandering {theme.prop_name}. "
            f"Then the whole yard burst into laughter, including {hero.id}."
        )
    elif prop.meters["wobble"] >= THRESHOLD:
        world.say(
            f"Then the music started, and {hero.id} gave one delighted {motion.verb}. "
            f"The {theme.head_part} wobbled so hard that it bounced down over one eyebrow and made {hero.pronoun('object')} look gloriously lopsided."
        )
        world.say(
            f"The audience laughed, not in a mean way, but in the happy way people laugh when something is too silly to resist."
        )
    else:
        world.say(
            f"When the music started, {hero.id} gave a proud {motion.verb}, and the {theme.head_part} stayed put. "
            f"It looked ridiculous in exactly the right way."
        )


def kind_pause(world: World, helper: Entity, parent: Entity, hero: Entity) -> None:
    hero.memes["relief"] += 1
    parent.memes["calm"] += 1
    world.say(
        f"{parent.label_word.capitalize()} did not fuss. {parent.pronoun().capitalize()} knelt beside {hero.id}, straightened the tape on one cheek, and smiled."
    )
    world.say(
        f'"That was a very funny entrance," {parent.pronoun()} said. "{helper.id}, shall we make it funny on purpose next time instead of by accident?"'
    )


def fix_prop(world: World, hero: Entity, helper: Entity, parent: Entity, theme: Theme, fixed_material: Material, fix: Fix) -> None:
    prop = world.get("prop")
    prop.attrs["material"] = fixed_material.id
    prop.meters["strain"] = 0.0
    prop.meters["wobble"] = 0.0
    prop.meters["collapsed"] = 0.0
    prop.meters["reinforced"] += 1
    hero.memes["hope"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"So the three of them hurried to the craft box, found {fixed_material.phrase}, and {fix.text}. "
        f"Fresh tape zipped, scissors snipped, and the {theme.prop_name} grew properly bold."
    )
    world.say(
        f'"Now that is a hat with some manners," {helper.id} said. "{fixed_material.ply_text.capitalize()} can take a joke."'
    )


def happy_retry(world: World, hero: Entity, theme: Theme, motion: Motion) -> None:
    perform(world, motion, narrate=False)
    hero.memes["joy"] += 1
    audience = world.get("audience")
    audience.memes["delight"] += 1
    world.say(
        f"When the music started again, {hero.id} tried the very same {motion.verb}. This time the {theme.head_part} bounced once and stayed proud."
    )
    world.say(
        f"{theme.finale} Everyone clapped, and {hero.id} bowed so low that even the grass seemed to grin."
    )


THEMES = {
    "moose": Theme(
        id="moose",
        prop_name="moose hat",
        prop_phrase="a giant moose hat",
        head_part="antlers",
        opening_image="Two wide antlers stretched so far to each side that the sugar bowl had to be moved for safety.",
        boast="Behold the noblest moose in town",
        finale="The antlers framed the sunset like two curly branches, and the whole silly costume finally looked exactly as grand as it had sounded",
        tags={"costume", "hat"},
    ),
    "dragon": Theme(
        id="dragon",
        prop_name="dragon hat",
        prop_phrase="a dragon hat with a swinging snout",
        head_part="crest",
        opening_image="Its long paper snout was so dramatic that it nearly inspected the jam jar by itself.",
        boast="Behold the fieriest dragon in town",
        finale="The dragon crest bobbed above the crowd like a proud little flame, and the song ended with a perfect silly roar",
        tags={"costume", "hat"},
    ),
    "chef": Theme(
        id="chef",
        prop_name="chef hat",
        prop_phrase="an enormous chef hat",
        head_part="puff",
        opening_image="The tall white puff leaned over the fruit bowl like it was planning soup for the bananas.",
        boast="Behold the fanciest chef in town",
        finale="The giant puff stood high and round, and the final noodle-stir dance looked wonderfully absurd",
        tags={"costume", "hat"},
    ),
}

MATERIALS = {
    "tissue_one_ply": Material(
        id="tissue_one_ply",
        label="one-ply tissue paper",
        phrase="a stack of one-ply tissue paper",
        stiffness=0,
        silliness="floppy",
        ply_text="one-ply tissue paper",
        flimsy=True,
        tags={"tissue", "ply", "flimsy"},
    ),
    "paper_two_ply": Material(
        id="paper_two_ply",
        label="two-ply poster paper",
        phrase="some two-ply poster paper",
        stiffness=1,
        silliness="springy",
        ply_text="two-ply poster paper",
        flimsy=False,
        tags={"paper", "ply"},
    ),
    "cardboard_three_ply": Material(
        id="cardboard_three_ply",
        label="three-ply cardboard",
        phrase="a sheet of three-ply cardboard",
        stiffness=2,
        silliness="sturdy",
        ply_text="three-ply cardboard",
        flimsy=False,
        tags={"cardboard", "ply"},
    ),
}

MOTIONS = {
    "nod": Motion(
        id="nod",
        verb="nod",
        gerund="nodding",
        force=1,
        sound="fwip",
        tags={"movement"},
    ),
    "twirl": Motion(
        id="twirl",
        verb="twirl",
        gerund="twirling",
        force=2,
        sound="flap",
        tags={"movement", "dance"},
    ),
    "hop": Motion(
        id="hop",
        verb="hop",
        gerund="hopping",
        force=2,
        sound="boing",
        tags={"movement", "dance"},
    ),
}

FIXES = {
    "extra_tape": Fix(
        id="extra_tape",
        sense=2,
        bonus=1,
        text="wrapped the base with a neat belt of extra tape",
        qa_text="wrapped the base with extra tape to help it stay firm",
        tags={"tape"},
    ),
    "brace_cardboard": Fix(
        id="brace_cardboard",
        sense=3,
        bonus=2,
        text="slid in a firm inner brace and taped it snugly",
        qa_text="added a firm inner brace and taped it snugly",
        tags={"tape", "brace"},
    ),
    "wish_harder": Fix(
        id="wish_harder",
        sense=1,
        bonus=0,
        text="stared at it with hopeful eyes and wished very hard",
        qa_text="only wished hard instead of making it stronger",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
HELPER_NAMES = ["Pip", "June", "Toby", "Mina", "Nell", "Owen", "Ruby", "Kit"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for material_id in MATERIALS:
            for motion_id in MOTIONS:
                if any(valid_combo(MATERIALS[material_id], MOTIONS[motion_id], fix) for fix in sensible_fixes()):
                    combos.append((theme_id, material_id, motion_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    material: str
    motion: str
    fix: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


def tell(
    theme: Theme,
    material: Material,
    motion: Motion,
    fix: Fix,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    helper_name: str = "Pip",
    helper_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(fix.id))
    if theme.id not in THEMES or material.id not in MATERIALS or motion.id not in MOTIONS or fix.id not in FIXES:
        raise StoryError("(No story: one of the requested options is unknown.)")
    if support_margin(material, motion, fix) < 0:
        raise StoryError(explain_rejection(material, motion, fix))

    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    audience = world.add(Entity(id="audience", kind="thing", type="crowd", label="the audience"))
    prop = world.add(
        Entity(
            id="prop",
            kind="thing",
            type="costume",
            label=theme.prop_name,
            phrase=theme.prop_phrase,
            attrs={"material": material.id},
            tags=set(theme.tags) | set(material.tags),
        )
    )

    introduce(world, hero, helper, theme, material)
    foreshadow(world, hero, helper, theme, material, motion)

    world.para()
    parade_to_show(world, hero)
    comic_disaster(world, hero, theme, motion)

    world.para()
    kind_pause(world, helper, parent, hero)
    fixed_material = material
    if material.stiffness + fix.bonus < 2:
        fixed_material = MATERIALS["cardboard_three_ply"]
    fix_prop(world, hero, helper, parent, theme, fixed_material, fix)
    happy_retry(world, hero, theme, motion)

    world.facts.update(
        theme=theme,
        material=material,
        fixed_material=fixed_material,
        motion=motion,
        fix=fix,
        hero=hero,
        helper=helper,
        parent=parent,
        audience=audience,
        prop=prop,
        foreshadowed=bool(world.facts.get("predicted_wobble") or world.facts.get("predicted_collapse")),
        trouble_happened=True,
        happy_ending=True,
    )
    return world


KNOWLEDGE = {
    "ply": [
        (
            "What does ply mean in material words like three-ply cardboard?",
            "Ply means layers. Three-ply cardboard has three layers pressed together, so it is usually stiffer than something with only one layer."
        )
    ],
    "cardboard": [
        (
            "Why is cardboard stronger than tissue paper for a costume hat?",
            "Cardboard is thicker and stiffer, so it keeps its shape better. Tissue paper bends and droops very easily."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives a small clue before something bigger happens later. It helps the surprise feel earned instead of random."
        )
    ],
    "tape": [
        (
            "Why does extra tape help a paper craft stay together?",
            "Tape holds pieces in place and can make a weak edge firmer. A neat band of tape can stop a floppy part from pulling apart so quickly."
        )
    ],
    "brace": [
        (
            "What does a brace do in a craft project?",
            "A brace is an extra piece inside something that helps support it. It spreads the push and pull so the outside does not flop as much."
        )
    ],
    "costume": [
        (
            "Why do funny costumes make people laugh?",
            "Funny costumes can make a person look bigger, wobblier, or stranger than usual. That silly surprise often makes people laugh in a happy way."
        )
    ],
}
KNOWLEDGE_ORDER = ["ply", "cardboard", "foreshadowing", "tape", "brace", "costume"]


def generation_prompts(world: World) -> list[str]:
    theme = world.facts["theme"]
    material = world.facts["material"]
    motion = world.facts["motion"]
    hero = world.facts["hero"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "ply" and ends happily.',
        f"Tell a comedy about {hero.label} making {theme.prop_phrase} from {material.ply_text}, with a clue before the big wobble and a warm fix at the end.",
        f"Write a playful story where a silly hat almost fails during a {motion.gerund} performance, but the family repairs it and the show ends with laughter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    parent = world.facts["parent"]
    theme = world.facts["theme"]
    material = world.facts["material"]
    fixed_material = world.facts["fixed_material"]
    motion = world.facts["motion"]
    fix = world.facts["fix"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who wanted to wear {theme.prop_phrase} in a funny show, and {helper.label} and {parent.label_word} who helped. Together they turned a silly problem into part of the fun."
        ),
        (
            f"What was {hero.label} wearing?",
            f"{hero.label} was wearing {theme.prop_phrase} made from {material.ply_text}. The costume was meant to look huge and ridiculous, which is why everyone noticed it at once."
        ),
        (
            "What clue showed that trouble might happen later?",
            f"When {hero.label} practiced a small {motion.verb}, the {theme.head_part} already bobbed or drooped. That foreshadowed the later wobble because the material was showing weakness before the real show began."
        ),
        (
            f"What happened during the show?",
            f"During the big {motion.verb}, the hat bent and turned the performance into a surprise joke. Everyone laughed because the costume suddenly did something sillier than {hero.label} had planned."
        ),
        (
            f"How did they fix the problem?",
            f"They used {fixed_material.ply_text} and {fix.qa_text}. That made the hat sturdy enough for the same movement the second time."
        ),
        (
            "How did the story end?",
            f"It ended happily: the repaired hat stayed up, the crowd clapped, and the joke became part of a successful show. The ending proves what changed because the same kind of movement no longer knocked the costume over."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ply", "foreshadowing", "costume"}
    material = world.facts["material"]
    fixed_material = world.facts["fixed_material"]
    fix = world.facts["fix"]
    if "cardboard" in material.id or "cardboard" in fixed_material.id:
        tags.add("cardboard")
    if "tape" in fix.tags:
        tags.add("tape")
    if "brace" in fix.tags:
        tags.add("brace")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="moose",
        material="paper_two_ply",
        motion="twirl",
        fix="brace_cardboard",
        hero_name="Lily",
        hero_gender="girl",
        helper_name="Pip",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        theme="dragon",
        material="cardboard_three_ply",
        motion="hop",
        fix="extra_tape",
        hero_name="Max",
        hero_gender="boy",
        helper_name="June",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        theme="chef",
        material="paper_two_ply",
        motion="hop",
        fix="brace_cardboard",
        hero_name="Mia",
        hero_gender="girl",
        helper_name="Toby",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        theme="moose",
        material="cardboard_three_ply",
        motion="nod",
        fix="extra_tape",
        hero_name="Theo",
        hero_gender="boy",
        helper_name="Nell",
        helper_gender="girl",
        parent="father",
    ),
]


def explain_rejection(material: Material, motion: Motion, fix: Fix) -> str:
    margin = support_margin(material, motion, fix)
    return (
        f"(No story: {material.ply_text} is not strong enough for a big {motion.verb}, "
        f"even with {fix.id.replace('_', ' ')}. The prop would still crumple instead of reaching a happy ending. "
        f"Pick sturdier material or a stronger fix.)"
    ) if margin < 0 else "(No story: this combination is unreasonable.)"


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of the sturdier fixes: {better}.)"
    )


ASP_RULES = r"""
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(T, M, Mo) :- theme(T), material(M), motion(Mo), sensible_fix(F),
                   stiffness(M, St), bonus(F, B), force(Mo, Fo), St + B >= Fo.

chosen_safe :- chosen_fix(F), sense(F, S), sense_min(M), S >= M.
holds :- chosen_material(M), chosen_motion(Mo), chosen_fix(F),
         stiffness(M, St), bonus(F, B), force(Mo, Fo), St + B >= Fo.

story_ok :- chosen_safe, holds.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("stiffness", material_id, material.stiffness))
    for motion_id, motion in MOTIONS.items():
        lines.append(asp.fact("motion", motion_id))
        lines.append(asp.fact("force", motion_id, motion.force))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("bonus", fix_id, fix.bonus))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_ok(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_material", params.material),
            asp.fact("chosen_motion", params.motion),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show story_ok/0."))
    return bool(asp.atoms(model, "story_ok"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child makes a comic costume prop, a wobble is foreshadowed, and a sturdier fix saves the show."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--motion", choices=MOTIONS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    if args.material and args.motion and args.fix:
        material = MATERIALS[args.material]
        motion = MOTIONS[args.motion]
        fix = FIXES[args.fix]
        if support_margin(material, motion, fix) < 0:
            raise StoryError(explain_rejection(material, motion, fix))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.material is None or c[1] == args.material)
        and (args.motion is None or c[2] == args.motion)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, material_id, motion_id = rng.choice(sorted(combos))
    possible_fixes = [
        fix.id for fix in sensible_fixes()
        if support_margin(MATERIALS[material_id], MOTIONS[motion_id], fix) >= 0
    ]
    if args.fix:
        fix_id = args.fix
    else:
        fix_id = rng.choice(sorted(possible_fixes))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme_id,
        material=material_id,
        motion=motion_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        material = MATERIALS[params.material]
        motion = MOTIONS[params.motion]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(No story: unknown option {err.args[0]!r}.)") from err

    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if support_margin(material, motion, fix) < 0:
        raise StoryError(explain_rejection(material, motion, fix))

    world = tell(
        theme=theme,
        material=material,
        motion=motion,
        fix=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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

    smoke_cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random params for seed {seed}.")
            continue

    for i, params in enumerate(smoke_cases):
        ok = asp_story_ok(params)
        py_ok = support_margin(MATERIALS[params.material], MOTIONS[params.motion], FIXES[params.fix]) >= 0 and FIXES[params.fix].sense >= SENSE_MIN
        if ok != py_ok:
            rc = 1
            print(f"MISMATCH on scenario {i}: ASP={ok} Python={py_ok} params={params}")
        try:
            sample = generate(params)
            if not sample.story.strip():
                rc = 1
                print(f"Empty story for params={params}")
        except Exception as err:
            rc = 1
            print(f"Smoke test failed for params={params}: {err}")

    if rc == 0:
        print(f"OK: generated {len(smoke_cases)} smoke-test stories without crashing.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, material, motion) combos:\n")
        for theme_id, material_id, motion_id in combos:
            print(f"  {theme_id:8} {material_id:22} {motion_id}")
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
            header = f"### {p.hero_name}: {p.theme} with {p.material} ({p.motion}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
