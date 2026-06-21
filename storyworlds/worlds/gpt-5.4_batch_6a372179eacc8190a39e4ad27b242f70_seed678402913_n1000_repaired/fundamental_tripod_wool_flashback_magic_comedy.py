#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fundamental_tripod_wool_flashback_magic_comedy.py
============================================================================

A standalone story world about a child preparing a funny magic trick for a small
show. The trick needs three things to work together:

* a "fundamental" rule of the trick (stay still while the audience looks),
* a tripod that holds the stage lamp,
* and a puff of wool used as a pretend cloud or beard.

The model rebuilds a family-sized comedy from state instead of swapping nouns
into a fixed paragraph. A child wants a magical-looking reveal. The stage setup
is a bit wobbly. A helper remembers a flashback of an earlier wobble, predicts
what will go wrong, and offers the sensible fix. If the child listens, the trick
works and everyone laughs for the right reason. If not, the lamp tilts, the wool
drops, and the grown-up rescues the show with a calmer version of the trick.

Run it
------
    python storyworlds/worlds/gpt-5.4/fundamental_tripod_wool_flashback_magic_comedy.py
    python storyworlds/worlds/gpt-5.4/fundamental_tripod_wool_flashback_magic_comedy.py --show puppet --problem wobble --fix sandbag
    python storyworlds/worlds/gpt-5.4/fundamental_tripod_wool_flashback_magic_comedy.py --fix tape
    python storyworlds/worlds/gpt-5.4/fundamental_tripod_wool_flashback_magic_comedy.py --verify
    python storyworlds/worlds/gpt-5.4/fundamental_tripod_wool_flashback_magic_comedy.py --all --qa
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
# add storyworlds/ to sys.path from the nested worlds/gpt-5.4/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "thing"
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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class ShowTheme:
    id: str
    stage_place: str
    opening: str
    costume_line: str
    finale: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    lamp_effect: str
    wool_effect: str
    flashback_line: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    success_line: str
    rescue_line: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class PropStyle:
    id: str
    label: str
    phrase: str
    cloud_line: str
    joke_line: str
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


def _r_instability(world: World) -> list[str]:
    out: list[str] = []
    stand = world.entities.get("tripod")
    lamp = world.entities.get("lamp")
    wool = world.entities.get("wool")
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not stand or not lamp or not wool or not hero or not helper:
        return out
    if stand.meters["stable"] >= THRESHOLD:
        return out
    sig = ("instability",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lamp.meters["tilt_risk"] += 1
    wool.meters["drop_risk"] += 1
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_tilt(world: World) -> list[str]:
    out: list[str] = []
    stand = world.entities.get("tripod")
    lamp = world.entities.get("lamp")
    if not stand or not lamp:
        return out
    if stand.meters["stable"] >= THRESHOLD or lamp.meters["bumped"] < THRESHOLD:
        return out
    sig = ("tilt",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lamp.meters["tilted"] += 1
    lamp.meters["light_mess"] += 1
    out.append("__tilt__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.entities.get("lamp")
    wool = world.entities.get("wool")
    hero = world.entities.get("hero")
    if not lamp or not wool or not hero:
        return out
    if lamp.meters["tilted"] < THRESHOLD:
        return out
    sig = ("drop",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wool.meters["fallen"] += 1
    hero.memes["embarrassed"] += 1
    out.append("__drop__")
    return out


CAUSAL_RULES = [
    Rule(name="instability", tag="physical", apply=_r_instability),
    Rule(name="tilt", tag="physical", apply=_r_tilt),
    Rule(name="drop", tag="social", apply=_r_drop),
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


THEMES = {
    "parlor": ShowTheme(
        id="parlor",
        stage_place="the living room",
        opening="turned the rug into a tiny magic stage",
        costume_line="A chair became the backstage curtain, a spoon became a wand, and everything looked almost grand enough for a royal show.",
        finale="The room felt like the happiest little theater in the house.",
        tags={"magic", "show"},
    ),
    "kitchen": ShowTheme(
        id="kitchen",
        stage_place="the kitchen",
        opening="cleared a corner by the table and called it the Moonbeam Theater",
        costume_line="A mixing bowl became a hat, a wooden spoon became a wand, and the refrigerator hummed like a patient audience member.",
        finale="The kitchen looked less like supper-time and more like silly magic-time.",
        tags={"magic", "show"},
    ),
    "hallway": ShowTheme(
        id="hallway",
        stage_place="the hallway",
        opening="spread a bath mat on the floor and declared it the Grand Hall of Astonishment",
        costume_line="An umbrella stand became the curtain tower, a ruler became a wand, and the coat hooks looked ready to clap.",
        finale="The hallway felt like a very serious theater that had forgotten how not to giggle.",
        tags={"magic", "show"},
    ),
}

PROBLEMS = {
    "wobble": Problem(
        id="wobble",
        label="wobble",
        lamp_effect="the lamp trembled when anyone shuffled past",
        wool_effect="the wool cloud quivered on its string",
        flashback_line="Yesterday the same tripod had wiggled, and the fake moon had shone right into the cookie jar instead of the stage.",
        severity=2,
        tags={"tripod", "wobble"},
    ),
    "crooked_leg": Problem(
        id="crooked_leg",
        label="crooked leg",
        lamp_effect="one tripod leg sat on a thick picture book, so the lamp leaned sideways",
        wool_effect="the wool beard drooped as if it were falling asleep",
        flashback_line="Last time one leg stood on a book, and the whole 'mystery glow' slid across the wall and landed on a sock.",
        severity=2,
        tags={"tripod", "crooked"},
    ),
    "tangled_cord": Problem(
        id="tangled_cord",
        label="tangled cord",
        lamp_effect="the cord looped around one tripod foot and tugged the lamp whenever somebody turned",
        wool_effect="the wool puff bounced like a nervous sheep",
        flashback_line="Earlier that week the cord had hooked a slipper, and the grand reveal had become a grand oops.",
        severity=2,
        tags={"tripod", "cord"},
    ),
}

FIXES = {
    "sandbag": Fix(
        id="sandbag",
        label="sandbag",
        phrase="a little beanbag from the toy basket",
        method="nestled the beanbag across the tripod feet so the stand could not skitter",
        success_line="The tripod stopped fussing and stood as still as a good audience member.",
        rescue_line="set the beanbag on the tripod feet, straightened the lamp, and made the stage calm again",
        sense=3,
        power=3,
        tags={"stability", "beanbag"},
    ),
    "move_book": Fix(
        id="move_book",
        label="move_book",
        phrase="two flat coasters",
        method="lifted the crooked leg off the book and gave the short side two flat coasters instead",
        success_line="The tripod stood level at last, no longer pretending to be a sleepy flamingo.",
        rescue_line="pulled the book away, tucked the coasters under the short side, and leveled the lamp",
        sense=3,
        power=3,
        tags={"stability", "level"},
    ),
    "untangle": Fix(
        id="untangle",
        label="untangle",
        phrase="a neat loop for the cord",
        method="unwound the cord from the tripod foot and tucked it in a neat safe loop",
        success_line="Nothing tugged the stand now, so the light behaved itself.",
        rescue_line="freed the cord from the tripod foot and tucked it safely away from dancing feet",
        sense=3,
        power=3,
        tags={"stability", "cord"},
    ),
    "tape": Fix(
        id="tape",
        label="tape",
        phrase="one tiny bit of tape",
        method="stuck down one dangling corner and hoped for the best",
        success_line="The tape looked busy, but the tripod still looked doubtful.",
        rescue_line="added tape here and there, but the stand was still too fussy to trust",
        sense=1,
        power=1,
        tags={"weak_fix"},
    ),
}

PROP_STYLES = {
    "cloud": PropStyle(
        id="cloud",
        label="cloud",
        phrase="a puff of wool tied to a string",
        cloud_line="The wool was meant to drift by like a tiny magic cloud.",
        joke_line="It looked less like weather and more like a sheep trying to learn theater.",
        tags={"wool", "cloud"},
    ),
    "beard": PropStyle(
        id="beard",
        label="beard",
        phrase="a fluffy wool beard on a ribbon",
        cloud_line="The wool was meant to hang under the hat like the beard of a very important wizard.",
        joke_line="It made the wizard look as if he had borrowed his chin from a pillow.",
        tags={"wool", "beard"},
    ),
    "rabbit": PropStyle(
        id="rabbit",
        label="rabbit",
        phrase="a wool puff with paper ears",
        cloud_line="The wool was meant to peek from a hat like a magical rabbit.",
        joke_line="It looked like a rabbit that had rolled through the laundry basket.",
        tags={"wool", "rabbit"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["dramatic", "careful", "bouncy", "clever", "hopeful", "silly"]
HELPER_TRAITS = ["careful", "calm", "observant", "sensible"]


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def select_fix(problem_id: str) -> Optional[Fix]:
    mapping = {
        "wobble": "sandbag",
        "crooked_leg": "move_book",
        "tangled_cord": "untangle",
    }
    fid = mapping.get(problem_id)
    return FIXES[fid] if fid else None


def valid_combo(problem_id: str, fix_id: str) -> bool:
    expected = select_fix(problem_id)
    fix = FIXES[fix_id]
    return expected is not None and fix.id == expected.id and fix.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for problem_id in PROBLEMS:
            expected = select_fix(problem_id)
            if expected and expected.sense >= SENSE_MIN:
                combos.append((theme_id, problem_id, expected.id))
    return combos


def predict_oops(world: World, problem: Problem) -> dict:
    sim = world.copy()
    apply_problem(sim, problem, narrate=False)
    rehearse_without_fix(sim, narrate=False)
    return {
        "tilted": sim.get("lamp").meters["tilted"] >= THRESHOLD,
        "fallen": sim.get("wool").meters["fallen"] >= THRESHOLD,
    }


def apply_problem(world: World, problem: Problem, narrate: bool = True) -> None:
    stand = world.get("tripod")
    stand.meters["stable"] = 0.0
    stand.meters["wobbly"] += 1
    world.facts["problem_seen"] = problem.id
    propagate(world, narrate=narrate)


def apply_fix(world: World, fix: Fix) -> None:
    stand = world.get("tripod")
    stand.meters["stable"] = 1.0
    stand.meters["wobbly"] = 0.0
    world.get("lamp").meters["tilt_risk"] = 0.0
    world.get("wool").meters["drop_risk"] = 0.0
    world.facts["fix_used"] = fix.id


def rehearse_without_fix(world: World, narrate: bool = True) -> None:
    world.get("lamp").meters["bumped"] += 1
    propagate(world, narrate=False)
    if narrate:
        wool_style = world.facts["prop_style"]
        world.say(
            f"The trick began with a whisper and a flourish. Then the lamp tipped, the shadow jumped, and the {wool_style.label} did not float at all."
        )
        world.say("Instead, it plopped down at exactly the wrong time, which was funny to everyone except the magician.")


def setup_stage(world: World, hero: Entity, helper: Entity, parent: Entity,
                theme: ShowTheme, prop_style: PropStyle) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After lunch, {hero.id} and {helper.id} {theme.opening} in {theme.stage_place}. {theme.costume_line}"
    )
    world.say(
        f"{hero.id} had a grand plan for a magic show. A lamp on a tripod would make moonlight, and {prop_style.phrase} would become the surprise in the air."
    )
    world.say(prop_style.cloud_line)
    world.say(prop_style.joke_line)
    world.say(
        f'"The most fundamental rule," {hero.id} announced, tapping the spoon-wand, "is that everyone must gasp at the right moment."'
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled from the doorway. "A fine rule," {parent.pronoun()} said, "but the stage has to stand still first."'
    )


def notice_problem(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["showoff"] += 1
    world.say(
        f"When {hero.id} gave the tripod a proud little pat, {problem.lamp_effect}. {problem.wool_effect}"
    )
    apply_problem(world, problem, narrate=False)
    helper.memes["caution"] += 1


def flashback_warning(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    pred = predict_oops(world, problem)
    world.facts["predicted_tilt"] = pred["tilted"]
    world.facts["predicted_fall"] = pred["fallen"]
    world.say(
        f"{helper.id} blinked and remembered something from before. {problem.flashback_line}"
    )
    if pred["tilted"] and pred["fallen"]:
        world.say(
            f'"Wait," {helper.id} said. "This is the same kind of wobble. If you do the trick now, the lamp will tilt and the wool will fall before the magic part."'
        )
    else:
        world.say(
            f'"Wait," {helper.id} said. "Something about this feels wrong, and funny in the wrong way."'
        )


def insist(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'{hero.id} puffed up and held the spoon-wand higher. "Maybe the wobble is part of the magic," {hero.pronoun()} said.'
    )


def choose_fix(world: World, helper: Entity, fix: Fix) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} pointed at {fix.phrase}. "Let us use that," {helper.pronoun()} said. "Magic can be silly, but the tripod should be serious."'
    )
    world.say(f"{helper.id} {fix.method}. {fix.success_line}")
    apply_fix(world, fix)


def perform_success(world: World, hero: Entity, helper: Entity, parent: Entity,
                    theme: ShowTheme, prop_style: PropStyle) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then the show began for real. The tripod held the lamp steady, the room glowed softly, and the {prop_style.label} floated exactly when {hero.id} whispered the spell."
    )
    world.say(
        f"{parent.label_word.capitalize()} gasped in a very extra way, then laughed so hard that {parent.pronoun('possessive')} shoulders shook."
    )
    world.say(
        f"{hero.id} bowed, {helper.id} bowed lower, and both of them nearly bumped heads from giggling."
    )
    world.say(theme.finale)


def perform_oops(world: World, hero: Entity, helper: Entity, parent: Entity,
                 prop_style: PropStyle) -> None:
    insist(world, hero)
    rehearse_without_fix(world, narrate=True)
    world.say(
        f'{helper.id} threw both hands over {helper.pronoun("possessive")} mouth, trying not to laugh and worry at the same time.'
    )
    world.say(
        f'{parent.label_word.capitalize()} hurried in before the lamp could tip any farther.'
    )


def parent_rescue(world: World, hero: Entity, helper: Entity, parent: Entity,
                  fix: Fix, prop_style: PropStyle) -> None:
    apply_fix(world, fix)
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["embarrassed"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} {fix.rescue_line}. Then {parent.pronoun()} picked up the wool and dusted it with two gentle pats."
    )
    world.say(
        f'"The fundamental rule of home magic," {parent.pronoun()} said, "is that the funny part should surprise people, not fall on their shoes."'
    )
    world.say(
        f"That made {hero.id} snort with laughter, because the {prop_style.label} had indeed tried to land on a shoe."
    )
    world.say(
        f"They started again. This time the tripod behaved, the light stayed where it belonged, and the trick worked well enough to make everyone clap and laugh together."
    )


def tell(theme: ShowTheme, problem: Problem, fix: Fix, prop_style: PropStyle,
         hero_name: str = "Lily", hero_gender: str = "girl",
         helper_name: str = "Tom", helper_gender: str = "boy",
         parent_type: str = "mother", trait: str = "dramatic",
         helper_trait: str = "careful", listen: bool = True) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[helper_trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    tripod = world.add(Entity(
        id="tripod",
        type="tripod",
        label="tripod",
        phrase="a shaky little tripod",
        tags={"tripod"},
    ))
    lamp = world.add(Entity(
        id="lamp",
        type="lamp",
        label="lamp",
        phrase="a lamp",
        tags={"lamp"},
    ))
    wool = world.add(Entity(
        id="wool",
        type="wool",
        label="wool",
        phrase=prop_style.phrase,
        tags={"wool"},
    ))
    tripod.meters["stable"] = 1.0

    setup_stage(world, hero, helper, parent, theme, prop_style)

    world.para()
    notice_problem(world, hero, helper, problem)
    flashback_warning(world, hero, helper, problem)

    world.para()
    if listen:
        choose_fix(world, helper, fix)
        perform_success(world, hero, helper, parent, theme, prop_style)
        outcome = "smooth"
    else:
        perform_oops(world, hero, helper, parent, prop_style)
        parent_rescue(world, hero, helper, parent, fix, prop_style)
        outcome = "oops_then_fix"

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        tripod=tripod,
        lamp=lamp,
        wool=wool,
        theme=theme,
        problem=problem,
        fix=fix,
        prop_style=prop_style,
        listened=listen,
        outcome=outcome,
        tilted=lamp.meters["tilted"] >= THRESHOLD,
        fallen=wool.meters["fallen"] >= THRESHOLD,
        fundamental_rule="the stage has to stand still first",
    )
    return world


KNOWLEDGE = {
    "tripod": [(
        "What is a tripod?",
        "A tripod is a stand with three legs that holds something up. It works best when all three legs are steady."
    )],
    "wool": [(
        "What is wool?",
        "Wool is soft fiber, often from sheep. It feels fluffy, so children sometimes use it for crafts and pretend clouds or beards."
    )],
    "magic": [(
        "What is a magic trick?",
        "A magic trick is a performance that makes something seem surprising or impossible. It is planned very carefully even when it looks silly."
    )],
    "flashback": [(
        "What is a flashback in a story?",
        "A flashback is when a story remembers something that happened earlier. It helps characters use the past to understand what is happening now."
    )],
    "stability": [(
        "Why does a stand need to be stable?",
        "A stable stand does not wobble or tip easily. That keeps lights and other objects from sliding or falling."
    )],
    "cord": [(
        "Why should cords stay out of the way?",
        "Loose cords can catch on feet or furniture and tug objects down. Keeping them tidy helps everyone move safely."
    )],
    "level": [(
        "Why does it matter if something is level?",
        "When something is level, it sits flat instead of leaning. That helps it stay balanced."
    )],
    "beanbag": [(
        "How can a beanbag help something stand still?",
        "A small beanbag can add weight and stop a light stand from skittering. The extra weight helps the feet stay put."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    prop_style = f["prop_style"]
    outcome = f["outcome"]
    base = (
        f'Write a funny magic story for a 3-to-5-year-old that includes the words "fundamental", "tripod", and "wool". '
        f"Use a flashback to help a child notice a problem before or during a magic show."
    )
    if outcome == "smooth":
        return [
            base,
            f"Tell a cozy comedy where {hero.id} wants a magical reveal with a tripod lamp and {prop_style.phrase}, but {helper.id}'s flashback about an earlier {problem.label} helps save the show.",
            f'Write a playful story in which the fundamental rule turns out to be about keeping the stage steady, not about saying the fanciest spell.',
        ]
    return [
        base,
        f"Tell a comedy where {hero.id} ignores {helper.id}'s warning, the tripod misbehaves, and the wool prop falls at the worst possible moment before a grown-up calmly rescues the trick.",
        f'Write a story with a silly oops first and a better second try, showing that past mistakes in a flashback can become useful magic-show wisdom.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    problem = f["problem"]
    fix = f["fix"]
    prop_style = f["prop_style"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who wanted to put on a magic show, {helper.id}, who helped notice the trouble, and {parent.label_word} who watched and later helped too."
        ),
        (
            "What was the magic trick supposed to use?",
            f"The trick used a lamp on a tripod for the special light and {prop_style.phrase} for the funny magical surprise. Those pieces had to work together for the show to look right."
        ),
        (
            'What was the "fundamental" rule in the story?',
            f'The story says the fundamental rule was that the stage had to stand still first. The children learned that a magical show still needs a steady setup.'
        ),
        (
            "How did the flashback help?",
            f"{helper.id} remembered an earlier wobble and used that memory to predict what would happen next. The flashback turned an old mistake into a warning for the present."
        ),
    ]
    if f["listened"]:
        qa.append((
            f"Why did {helper.id} want to use {fix.phrase}?",
            f"{helper.id} could see that the {problem.label} would make the tripod misbehave. {fix.phrase.capitalize()} fixed the stand so the lamp and wool prop would stay where they belonged."
        ))
        qa.append((
            "How did the story end?",
            f"The trick worked, the wool surprise floated at the right moment, and everyone laughed happily. The ending proves the children changed the stage instead of hoping the problem would magically fix itself."
        ))
    else:
        qa.append((
            f"What went wrong when {hero.id} tried the trick too soon?",
            f"The tripod tilted the lamp and the wool prop fell at exactly the wrong time. That happened because the warning from the flashback was true and the stand had not been fixed yet."
        ))
        qa.append((
            f"How did {parent.label_word} help?",
            f"{parent.label_word.capitalize()} calmly used the better fix and reset the stage before trying again. After that, the trick became funny in a good way instead of a messy way."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set()
    tags |= f["theme"].tags
    tags |= f["problem"].tags
    tags |= f["fix"].tags
    tags |= f["prop_style"].tags
    tags.add("tripod")
    tags.add("wool")
    tags.add("magic")
    tags.add("flashback")
    out: list[tuple[str, str]] = []
    order = ["tripod", "wool", "magic", "flashback", "stability", "cord", "level", "beanbag"]
    for tag in order:
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


@dataclass
class StoryParams:
    theme: str
    problem: str
    fix: str
    prop_style: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    helper_trait: str
    listen: bool
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="parlor",
        problem="wobble",
        fix="sandbag",
        prop_style="cloud",
        hero_name="Lily",
        hero_gender="girl",
        helper_name="Tom",
        helper_gender="boy",
        parent="mother",
        trait="dramatic",
        helper_trait="careful",
        listen=True,
    ),
    StoryParams(
        theme="kitchen",
        problem="crooked_leg",
        fix="move_book",
        prop_style="beard",
        hero_name="Max",
        hero_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        parent="father",
        trait="silly",
        helper_trait="observant",
        listen=True,
    ),
    StoryParams(
        theme="hallway",
        problem="tangled_cord",
        fix="untangle",
        prop_style="rabbit",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="mother",
        trait="hopeful",
        helper_trait="sensible",
        listen=False,
    ),
]


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_problem_fix(problem_id: str, fix_id: str) -> str:
    if FIXES[fix_id].sense < SENSE_MIN:
        return (
            f"(No story: '{fix_id}' is known in the world, but it is too weak and silly to trust as the chosen fix. "
            f"Pick a steadier fix like {select_fix(problem_id).id if select_fix(problem_id) else 'a safer option' }.)"
        )
    expected = select_fix(problem_id)
    if expected is None:
        return "(No story: this problem has no sensible fix in the catalog.)"
    return (
        f"(No story: {fix_id} does not honestly solve the {problem_id} problem here. "
        f"The world only allows fixes that match the actual wobble.)"
    )


ASP_RULES = r"""
% a sensible fix must meet the common-sense threshold
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.

% each problem has one domain-matching fix
valid(T, P, F) :- theme(T), problem(P), preferred_fix(P, F), sensible_fix(F).

% simple outcome twin
outcome(smooth) :- listened(yes), valid(_, P, F), chosen_problem(P), chosen_fix(F).
outcome(oops_then_fix) :- listened(no), valid(_, P, F), chosen_problem(P), chosen_fix(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
    for pid in PROBLEMS:
        preferred = select_fix(pid)
        if preferred is not None:
            lines.append(asp.fact("preferred_fix", pid, preferred.id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_fix", params.fix),
        asp.fact("listened", "yes" if params.listen else "no"),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "smooth" if params.listen else "oops_then_fix"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a funny magic show with a tripod, wool, and a flashback warning."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--prop-style", dest="prop_style", choices=PROP_STYLES)
    ap.add_argument("--listen", choices=["yes", "no"],
                    help="whether the hero listens to the helper before the first try")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and args.problem:
        if not valid_combo(args.problem, args.fix):
            raise StoryError(explain_problem_fix(args.problem, args.fix))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        problem_id = args.problem or sorted(PROBLEMS)[0]
        raise StoryError(explain_problem_fix(problem_id, args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.problem is None or combo[1] == args.problem)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, problem_id, fix_id = rng.choice(sorted(combos))
    prop_style = args.prop_style or rng.choice(sorted(PROP_STYLES))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    helper_trait = rng.choice(HELPER_TRAITS)
    listen = {"yes": True, "no": False}.get(args.listen, rng.choice([True, False]))
    return StoryParams(
        theme=theme_id,
        problem=problem_id,
        fix=fix_id,
        prop_style=prop_style,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        helper_trait=helper_trait,
        listen=listen,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Invalid theme: {params.theme})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Invalid problem: {params.problem})")
    if params.fix not in FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")
    if params.prop_style not in PROP_STYLES:
        raise StoryError(f"(Invalid prop style: {params.prop_style})")
    if not valid_combo(params.problem, params.fix):
        raise StoryError(explain_problem_fix(params.problem, params.fix))

    world = tell(
        theme=THEMES[params.theme],
        problem=PROBLEMS[params.problem],
        fix=FIXES[params.fix],
        prop_style=PROP_STYLES[params.prop_style],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
        helper_trait=params.helper_trait,
        listen=params.listen,
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


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected parameter resolution failure for seed {seed}.")
            continue
        params.seed = seed
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

    # smoke test: normal generation and rendering must not crash
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
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
        print(f"{len(combos)} compatible (theme, problem, fix) combos:\n")
        for theme_id, problem_id, fix_id in combos:
            print(f"  {theme_id:8} {problem_id:12} {fix_id}")
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
            header = f"### {p.hero_name} & {p.helper_name}: {p.problem} -> {p.fix} ({outcome_of(p)})"
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
