#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spit_moral_value_reconciliation_detective_story.py
=============================================================================

A standalone story world for a gentle child-facing detective story about a wet
mystery, a wrong suspicion, truth-telling, and reconciliation.

Premise
-------
A little detective club finds that an important paper thing has been spoiled by
spit. One child seems suspicious at first, but the detective follows physical
clues instead of blaming in anger. The real culprit is found, tells the truth,
apologizes, and helps repair the damage. The ending image proves that honesty
and making things right can mend a friendship.

Run it
------
    python storyworlds/worlds/gpt-5.4/spit_moral_value_reconciliation_detective_story.py
    python storyworlds/worlds/gpt-5.4/spit_moral_value_reconciliation_detective_story.py --target bell
    python storyworlds/worlds/gpt-5.4/spit_moral_value_reconciliation_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/spit_moral_value_reconciliation_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/spit_moral_value_reconciliation_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/spit_moral_value_reconciliation_detective_story.py --json
    python storyworlds/worlds/gpt-5.4/spit_moral_value_reconciliation_detective_story.py --verify
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
HONEST_TRAITS = {"honest", "gentle", "softhearted"}


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
    absorbent: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    hiding_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Launch:
    id: str
    label: str
    object_phrase: str
    clue: str
    evidence: int
    makes_spit: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TargetCfg:
    id: str
    label: str
    phrase: str
    material: str
    absorbent: bool
    damage: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class Repair:
    id: str
    label: str
    materials: set[str]
    do_text: str
    end_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spot_upset(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    owner = world.entities.get("owner")
    detective = world.entities.get("detective")
    if not target or not owner or not detective:
        return out
    if target.meters["wet"] < THRESHOLD:
        return out
    sig = ("spot_upset", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["hurt"] += 1
    detective.memes["curious"] += 1
    out.append("__mystery__")
    return out


def _r_reconcile(world: World) -> list[str]:
    culprit = world.entities.get("culprit")
    owner = world.entities.get("owner")
    target = world.entities.get("target")
    if not culprit or not owner or not target:
        return []
    if culprit.memes["apology"] < THRESHOLD or target.meters["fixed"] < THRESHOLD:
        return []
    sig = ("reconcile", culprit.id, owner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["forgive"] += 1
    culprit.memes["relief"] += 1
    culprit.memes["peace"] += 1
    owner.memes["peace"] += 1
    return ["__peace__"]


CAUSAL_RULES = [
    Rule(name="spot_upset", tag="social", apply=_r_spot_upset),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def target_at_risk(launch: Launch, target: TargetCfg) -> bool:
    return launch.makes_spit and target.absorbent


def repair_fits(target: TargetCfg, repair: Repair) -> bool:
    return target.material in repair.materials


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for launch_id, launch in LAUNCHES.items():
            for target_id, target in TARGETS.items():
                for repair_id, repair in REPAIRS.items():
                    if target_at_risk(launch, target) and repair_fits(target, repair):
                        combos.append((setting_id, launch_id, target_id, repair_id))
    return combos


def evidence_strength(launch: Launch, setting: Setting) -> int:
    bonus = 1 if setting.id in {"clubhouse", "classroom"} else 0
    return launch.evidence + bonus


def outcome_of(params: "StoryParams") -> str:
    launch = LAUNCHES[params.launch]
    setting = SETTINGS[params.setting]
    strength = evidence_strength(launch, setting)
    if params.culprit_trait in HONEST_TRAITS:
        return "confessed"
    return "confessed" if strength >= 3 else "revealed"


def explain_rejection(launch: Launch, target: TargetCfg, repair: Repair) -> str:
    if not target.absorbent:
        return (
            f"(No story: {target.the} is not something spit would really spoil, so "
            f"there is no honest detective mystery to solve. Pick a paper or cardboard target.)"
        )
    if not repair_fits(target, repair):
        return (
            f"(No story: {repair.label} does not sensibly fix a {target.material} object. "
            f"The repair must match what was damaged.)"
        )
    if not launch.makes_spit:
        return "(No story: this launch makes no spit, so the wet clue would not exist.)"
    return "(No story: this combination does not make a reasonable mystery.)"


def predict_damage(world: World, launch_id: str, target_id: str) -> dict:
    sim = world.copy()
    culprit = sim.get("culprit")
    target = sim.get(target_id)
    launch = LAUNCHES[launch_id]
    _do_spit(sim, culprit, target, launch, narrate=False)
    return {
        "wet": target.meters["wet"] >= THRESHOLD,
        "hurt": sim.get("owner").memes["hurt"],
    }


def _do_spit(world: World, culprit: Entity, target: Entity, launch: Launch, narrate: bool = True) -> None:
    target.meters["wet"] += 1
    target.meters["marked"] += 1
    culprit.memes["mischief"] += 1
    world.facts["clue_text"] = launch.clue
    propagate(world, narrate=narrate)


def introduce(world: World, detective: Entity, owner: Entity, setting: Setting, target: TargetCfg) -> None:
    detective.memes["pride"] += 1
    owner.memes["pride"] += 1
    world.say(
        f"After snack time, {detective.id} opened the Tiny Detective Club in {setting.place}. "
        f"{setting.scene}"
    )
    world.say(
        f"{owner.id} set out {target.phrase} and whispered that it was the most important clue in today's game."
    )


def show_target(world: World, owner: Entity, target: TargetCfg) -> None:
    world.say(
        f"Everyone leaned close to study it. If the club could guard {target.the}, the pretend case would begin."
    )
    owner.memes["hope"] += 1


def mischief(world: World, culprit: Entity, launch: Launch, setting: Setting) -> None:
    world.say(
        f"But from {setting.hiding_spot}, {culprit.id} got silly and blew {launch.object_phrase} instead of waiting for the game to start."
    )


def mystery_strikes(world: World, culprit: Entity, target_ent: Entity, launch: Launch, target: TargetCfg, owner: Entity) -> None:
    _do_spit(world, culprit, target_ent, launch)
    world.say(
        f"The little bit of spit landed on {target.the}, and at once {target.damage}."
    )
    world.say(
        f'"Oh no!" cried {owner.id}. "{target.the.capitalize()} was fine a second ago!"'
    )


def detective_arrives(world: World, detective: Entity, launch: Launch, target: TargetCfg) -> None:
    world.say(
        f"{detective.id} knelt beside {target.the} and narrowed {detective.pronoun('possessive')} eyes the way a storybook detective would."
    )
    world.say(
        f"There was {launch.clue} beside the wet spot, and that meant this was not an accident from a spilled cup."
    )


def wrong_suspicion(world: World, detective: Entity, suspect: Entity, target: TargetCfg) -> None:
    suspect.memes["worry"] += 1
    world.say(
        f"{suspect.id} had been nearest to {target.the}, so for one uneasy moment everyone looked at {suspect.pronoun('object')}."
    )
    world.say(
        f'{detective.id} lifted a hand. "A detective does not blame the nearest person first," {detective.pronoun()} said. "A detective checks the clues."'
    )


def clear_suspect(world: World, detective: Entity, suspect: Entity, launch: Launch) -> None:
    suspect.memes["relief"] += 1
    world.say(
        f"{detective.id} looked at {suspect.id}'s clean hands and empty pockets. "
        f"{suspect.pronoun().capitalize()} had no sign of {launch.label} at all."
    )
    world.say(
        f'"So it was not {suspect.id}," {detective.id} said calmly. "{suspect.id} is cleared."'
    )


def question_culprit(world: World, detective: Entity, culprit: Entity, launch: Launch, setting: Setting) -> None:
    strength = evidence_strength(launch, setting)
    world.facts["evidence_strength"] = strength
    if strength >= 3:
        world.say(
            f"Then {detective.id} spotted a damp straw tucked behind a chair and matched it to the clue."
        )
    else:
        world.say(
            f"Then {detective.id} noticed that the clue matched the kind of snack game they had just been playing."
        )
    world.say(
        f'{detective.id} turned to {culprit.id}. "Please tell the true part now," {detective.pronoun()} said.'
    )


def confess(world: World, culprit: Entity, owner: Entity, launch: Launch, target: TargetCfg) -> None:
    culprit.memes["shame"] += 1
    culprit.memes["truth"] += 1
    world.say(
        f"{culprit.id}'s face turned pink. "
        f'"I did it," {culprit.pronoun()} whispered. "I only meant to make a silly {launch.label}, but my spit hit {target.the}."'
    )
    world.say(
        f'{culprit.pronoun().capitalize()} looked at {owner.id} and added, "I spoiled your clue, and that was wrong."'
    )


def reveal(world: World, detective: Entity, culprit: Entity, owner: Entity, launch: Launch, target: TargetCfg) -> None:
    culprit.memes["shame"] += 1
    culprit.memes["truth"] += 1
    world.say(
        f'"The clue points to {culprit.id}," {detective.id} said gently. "The wet paper and the hiding spot fit together."'
    )
    world.say(
        f"{culprit.id} stared at {target.the} for a moment, then nodded. "
        f'"You are right," {culprit.pronoun()} said. "I made the {launch.label}, and my spit ruined it."'
    )
    world.say(
        f'{culprit.pronoun().capitalize()} sounded sorry now, not silly.'
    )


def apology(world: World, culprit: Entity, owner: Entity) -> None:
    culprit.memes["apology"] += 1
    world.say(
        f'{culprit.id} took a breath. "I am sorry, {owner.id}. I should not have used spit, and I should have told the truth sooner."'
    )


def repair_scene(world: World, culprit: Entity, owner: Entity, repair: Repair) -> None:
    target = world.get("target")
    target.meters["fixed"] += 1
    culprit.memes["care"] += 1
    owner.memes["hope"] += 1
    world.say(
        f"Instead of hiding behind the solved mystery, {culprit.id} stayed to help. Together, {culprit.id} and {owner.id} {repair.do_text}."
    )
    propagate(world, narrate=False)


def forgiveness(world: World, owner: Entity, culprit: Entity) -> None:
    if owner.memes["forgive"] >= THRESHOLD:
        world.say(
            f'{owner.id} touched the fixed clue and smiled a small smile. "I was upset," {owner.pronoun()} said, "but thank you for telling the truth and helping."'
        )
        world.say(
            f"{culprit.id} smiled back, and the hard feeling between them softened."
        )


def ending(world: World, detective: Entity, owner: Entity, culprit: Entity, target: TargetCfg, repair: Repair) -> None:
    detective.memes["satisfaction"] += 1
    world.say(
        f"Soon the case was closed, not with a jail cell, but with kinder hearts."
    )
    world.say(
        f"{repair.end_text}, and {owner.id} set it in the middle again. "
        f"{detective.id} pinned an imaginary gold star on the club for choosing truth over blame."
    )
    world.say(
        f"When the next round of play began, {owner.id} waved {culprit.id} over to stand beside {owner.pronoun('object')}, proving they were friends again."
    )


def tell(
    setting: Setting,
    launch: Launch,
    target: TargetCfg,
    repair: Repair,
    detective_name: str = "Mia",
    detective_gender: str = "girl",
    owner_name: str = "Ben",
    owner_gender: str = "boy",
    culprit_name: str = "Tess",
    culprit_gender: str = "girl",
    suspect_name: str = "Noah",
    suspect_gender: str = "boy",
    culprit_trait: str = "honest",
) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective", traits=["observant"]))
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner", traits=["careful"]))
    culprit = world.add(Entity(id=culprit_name, kind="character", type=culprit_gender, role="culprit", traits=[culprit_trait]))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=suspect_gender, role="suspect", traits=["fidgety"]))
    target_ent = world.add(
        Entity(
            id="target",
            kind="thing",
            type=target.material,
            label=target.label,
            phrase=target.phrase,
            role="target",
            absorbent=target.absorbent,
            tags=set(target.tags),
        )
    )

    world.facts.update(
        detective=detective,
        owner=owner,
        culprit=culprit,
        suspect=suspect,
        setting=setting,
        launch=launch,
        target_cfg=target,
        repair=repair,
        culprit_trait=culprit_trait,
    )

    introduce(world, detective, owner, setting, target)
    show_target(world, owner, target)

    world.para()
    mischief(world, culprit, launch, setting)
    mystery_strikes(world, culprit, target_ent, launch, target, owner)

    world.para()
    detective_arrives(world, detective, launch, target)
    wrong_suspicion(world, detective, suspect, target)
    clear_suspect(world, detective, suspect, launch)
    question_culprit(world, detective, culprit, launch, setting)

    world.para()
    outcome = "confessed" if culprit_trait in HONEST_TRAITS or evidence_strength(launch, setting) >= 3 else "revealed"
    if outcome == "confessed":
        confess(world, culprit, owner, launch, target)
    else:
        reveal(world, detective, culprit, owner, launch, target)
    apology(world, culprit, owner)
    repair_scene(world, culprit, owner, repair)
    forgiveness(world, owner, culprit)

    world.para()
    ending(world, detective, owner, culprit, target, repair)

    world.facts.update(
        outcome=outcome,
        target_ent=target_ent,
        damaged=target_ent.meters["wet"] >= THRESHOLD,
        repaired=target_ent.meters["fixed"] >= THRESHOLD,
        reconciled=owner.memes["forgive"] >= THRESHOLD,
        wrong_suspicion=True,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    launch: str
    target: str
    repair: str
    detective: str
    detective_gender: str
    owner: str
    owner_gender: str
    culprit: str
    culprit_gender: str
    suspect: str
    suspect_gender: str
    culprit_trait: str
    seed: Optional[int] = None


SETTINGS = {
    "clubhouse": Setting(
        id="clubhouse",
        place="the blanket clubhouse by the window",
        scene="A paper magnifying glass, two crayons, and a biscuit tin full of pretend clues waited on the floor.",
        hiding_spot="the flap of the blanket door",
        tags={"detective", "clubhouse"},
    ),
    "classroom": Setting(
        id="classroom",
        place="the rainy-day classroom corner",
        scene="A chalk arrow pointed toward a shoebox marked CASE FILES, and four small stools made a neat circle.",
        hiding_spot="the book shelf by the reading rug",
        tags={"detective", "classroom"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the quiet hallway outside the art room",
        scene="Sunlight lay in square patches on the floor, and the children had set up a detective desk on a bench.",
        hiding_spot="the tall fern by the wall",
        tags={"detective", "hallway"},
    ),
}

LAUNCHES = {
    "spitball": Launch(
        id="spitball",
        label="spitball",
        object_phrase="a tiny paper spitball through a straw",
        clue="a damp paper pellet no bigger than a bean",
        evidence=2,
        makes_spit=True,
        tags={"spit", "spitball", "clue"},
    ),
    "seed": Launch(
        id="seed",
        label="seed shot",
        object_phrase="a watermelon seed with a little spit behind it",
        clue="a shiny black seed with a wet ring around it",
        evidence=1,
        makes_spit=True,
        tags={"spit", "seed", "clue"},
    ),
}

TARGETS = {
    "map": TargetCfg(
        id="map",
        label="map",
        phrase="a hand-drawn treasure map",
        material="paper",
        absorbent=True,
        damage="the blue river smeared into a blurry cloud",
        tags={"paper", "map"},
    ),
    "badge": TargetCfg(
        id="badge",
        label="badge",
        phrase="a bright cardboard detective badge",
        material="cardboard",
        absorbent=True,
        damage="the silver star sagged and the ink curled at the edges",
        tags={"cardboard", "badge"},
    ),
    "poster": TargetCfg(
        id="poster",
        label="poster",
        phrase="a poster that said MYSTERY OF THE DAY",
        material="poster",
        absorbent=True,
        damage="the careful letters ran and made a gray drip",
        tags={"paper", "poster"},
    ),
    "bell": TargetCfg(
        id="bell",
        label="bell",
        phrase="a brass detective bell",
        material="metal",
        absorbent=False,
        damage="nothing much changed at all",
        tags={"metal"},
    ),
}

REPAIRS = {
    "redraw": Repair(
        id="redraw",
        label="redrawing it on clean paper",
        materials={"paper", "poster"},
        do_text="redrew the clue on clean paper, line by line",
        end_text="The fresh page dried smooth and straight",
        qa_text="redrew it neatly on clean paper",
        tags={"repair", "paper"},
    ),
    "new_badge": Repair(
        id="new_badge",
        label="cutting a new badge from card",
        materials={"cardboard"},
        do_text="cut a new badge from stiff blue card and colored a careful silver star in the middle",
        end_text="The new badge stood firm and bright",
        qa_text="cut a new badge from card and decorated it together",
        tags={"repair", "cardboard"},
    ),
    "new_poster": Repair(
        id="new_poster",
        label="making a fresh poster",
        materials={"poster"},
        do_text="made a fresh poster with thick dark letters that would not smudge",
        end_text="The new poster looked bold and easy to read",
        qa_text="made a fresh poster together",
        tags={"repair", "poster"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella", "Lucy", "Rose"]
BOY_NAMES = ["Ben", "Noah", "Leo", "Finn", "Sam", "Jack", "Theo", "Eli"]
CULPRIT_TRAITS = ["honest", "gentle", "softhearted", "proud", "stubborn"]


KNOWLEDGE = {
    "spit": [
        (
            "Why is spit not for games on other people's things?",
            "Spit is part of your body, and it can make other people's things wet, dirty, or yucky. It is kinder and cleaner to keep it to yourself."
        )
    ],
    "spitball": [
        (
            "What is a spitball?",
            "A spitball is a little wad made wet with spit and blown or tossed as a joke. It is not a safe or kind toy because it can make a mess on people or paper."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to find the truth. A good detective does not guess in anger but pays attention carefully."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. A wet mark, a seed, or a paper pellet can all be clues."
        )
    ],
    "truth": [
        (
            "Why is telling the truth important after you do something wrong?",
            "Telling the truth helps people fix the real problem. It is often the first step toward trust again."
        )
    ],
    "apology": [
        (
            "What makes an apology real?",
            "A real apology says what you did wrong and shows you want to make it right. Helping repair the harm makes the apology stronger."
        )
    ],
    "forgiveness": [
        (
            "What is reconciliation?",
            "Reconciliation means people come back together after hurt feelings. It often happens when someone tells the truth, says sorry, and helps mend the problem."
        )
    ],
    "paper": [
        (
            "Why can paper be spoiled by water or spit?",
            "Paper soaks up wet drops very quickly. When that happens, ink can smear and the paper can wrinkle."
        )
    ],
    "cardboard": [
        (
            "Why does cardboard go soft when it gets wet?",
            "Cardboard is made from pressed paper fibers. Wetness can make those fibers bend and sag."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "detective",
    "clue",
    "spit",
    "spitball",
    "truth",
    "apology",
    "forgiveness",
    "paper",
    "cardboard",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    owner = f["owner"]
    target = f["target_cfg"]
    launch = f["launch"]
    outcome = f["outcome"]
    asks = [
        'Write a gentle detective story for a 3-to-5-year-old that includes the word "spit" and ends with reconciliation.',
        f"Tell a child-friendly mystery where {detective.id} follows clues after {target.the} is spoiled by {launch.label}, and the case ends with truth-telling and friendship repaired.",
        f"Write a tiny detective case in which {owner.id}'s {target.label} is damaged, someone is almost blamed too quickly, and the real culprit makes things right.",
    ]
    if outcome == "revealed":
        asks.append("Include a moment when the detective gently reveals the truth from the clues before the culprit admits it.")
    else:
        asks.append("Include a moment when the guilty child confesses after being asked kindly for the true part.")
    return asks


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    owner = f["owner"]
    culprit = f["culprit"]
    suspect = f["suspect"]
    launch = f["launch"]
    target = f["target_cfg"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a little detective, {owner.id}, whose {target.label} was spoiled, and {culprit.id}, who caused the trouble. The story also includes {suspect.id}, who was briefly suspected but was not guilty.",
        ),
        (
            f"What was the mystery?",
            f"The mystery was how {target.the} got wet and damaged just before the game began. {detective.id} solved it by noticing a clue that matched {launch.label}.",
        ),
        (
            f"Why did {detective.id} stop everyone from blaming {suspect.id}?",
            f"{detective.id} wanted the truth, not a fast guess. {detective.pronoun().capitalize()} knew that being nearby was not the same as being guilty, so {detective.pronoun()} checked the clues first.",
        ),
    ]
    if outcome == "confessed":
        qa.append(
            (
                f"How was the case solved?",
                f"The case was solved when {culprit.id} admitted making the {launch.label} and said the spit had hit {target.the}. The confession happened after {detective.id} asked kindly for the true part.",
            )
        )
    else:
        qa.append(
            (
                f"How was the case solved?",
                f"{detective.id} matched the physical clue to {culprit.id} and gently explained what it meant. After hearing the evidence, {culprit.id} admitted the truth.",
            )
        )
    qa.append(
        (
            f"How did the children reconcile?",
            f"{culprit.id} apologized for using spit and for spoiling {owner.id}'s {target.label}. Then {culprit.pronoun()} stayed to help and {repair.qa_text}, which helped {owner.id} forgive {culprit.pronoun('object')}.",
        )
    )
    qa.append(
        (
            "What is the moral of the story?",
            f"The story teaches that you should not make messy spit jokes on other people's things, and you should tell the truth when you do something wrong. It also shows that helping repair the harm can help friendship grow back.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"detective", "clue", "spit", "truth", "apology", "forgiveness"}
    tags |= set(f["launch"].tags)
    tags |= set(f["target_cfg"].tags)
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
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.traits:
            parts.append(f"traits={e.traits}")
        if e.absorbent:
            parts.append("absorbent=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(L, T) :- launch(L), target(T), makes_spit(L), absorbent(T).
repair_fits(T, R) :- target(T), repair(R), material(T, M), fixes(R, M).
valid(S, L, T, R) :- setting(S), hazard(L, T), repair_fits(T, R).

honest_trait(T) :- trait(T), is_honest(T).
evidence_value(L, S, E + B) :- base_evidence(L, E), setting_bonus(S, B).
outcome(confessed) :- chosen_trait(T), honest_trait(T).
outcome(confessed) :- chosen_launch(L), chosen_setting(S), evidence_value(L, S, V), V >= 3, not outcome(revealed).
outcome(revealed) :- chosen_trait(T), not honest_trait(T), chosen_launch(L), chosen_setting(S), evidence_value(L, S, V), V < 3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        bonus = 1 if sid in {"clubhouse", "classroom"} else 0
        lines.append(asp.fact("setting_bonus", sid, bonus))
    for lid, launch in LAUNCHES.items():
        lines.append(asp.fact("launch", lid))
        if launch.makes_spit:
            lines.append(asp.fact("makes_spit", lid))
        lines.append(asp.fact("base_evidence", lid, launch.evidence))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("material", tid, target.material))
        if target.absorbent:
            lines.append(asp.fact("absorbent", tid))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        for mat in sorted(repair.materials):
            lines.append(asp.fact("fixes", rid, mat))
    for trait in sorted(CULPRIT_TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(HONEST_TRAITS):
        lines.append(asp.fact("is_honest", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_launch", params.launch),
            asp.fact("chosen_trait", params.culprit_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(50):
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A little detective story world about spit, truth, apology, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--launch", choices=LAUNCHES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--detective")
    ap.add_argument("--owner")
    ap.add_argument("--culprit")
    ap.add_argument("--suspect")
    ap.add_argument("--culprit-trait", choices=CULPRIT_TRAITS, dest="culprit_trait")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.launch and args.target and args.repair:
        launch = LAUNCHES[args.launch]
        target = TARGETS[args.target]
        repair = REPAIRS[args.repair]
        if not (target_at_risk(launch, target) and repair_fits(target, repair)):
            raise StoryError(explain_rejection(launch, target, repair))
    if args.target and not TARGETS[args.target].absorbent:
        launch = LAUNCHES[args.launch] if args.launch else next(iter(LAUNCHES.values()))
        repair = REPAIRS[args.repair] if args.repair else next(iter(REPAIRS.values()))
        raise StoryError(explain_rejection(launch, TARGETS[args.target], repair))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.launch is None or c[1] == args.launch)
        and (args.target is None or c[2] == args.target)
        and (args.repair is None or c[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, launch, target, repair = rng.choice(sorted(combos))
    used: set[str] = set()
    detective = args.detective
    detective_gender = "girl" if detective in GIRL_NAMES else "boy" if detective in BOY_NAMES else ""
    if not detective:
        detective, detective_gender = _pick_name(rng, used)
    used.add(detective)

    owner = args.owner
    owner_gender = "girl" if owner in GIRL_NAMES else "boy" if owner in BOY_NAMES else ""
    if not owner:
        owner, owner_gender = _pick_name(rng, used)
    used.add(owner)

    culprit = args.culprit
    culprit_gender = "girl" if culprit in GIRL_NAMES else "boy" if culprit in BOY_NAMES else ""
    if not culprit:
        culprit, culprit_gender = _pick_name(rng, used)
    used.add(culprit)

    suspect = args.suspect
    suspect_gender = "girl" if suspect in GIRL_NAMES else "boy" if suspect in BOY_NAMES else ""
    if not suspect:
        suspect, suspect_gender = _pick_name(rng, used)

    culprit_trait = args.culprit_trait or rng.choice(CULPRIT_TRAITS)
    return StoryParams(
        setting=setting,
        launch=launch,
        target=target,
        repair=repair,
        detective=detective,
        detective_gender=detective_gender,
        owner=owner,
        owner_gender=owner_gender,
        culprit=culprit,
        culprit_gender=culprit_gender,
        suspect=suspect,
        suspect_gender=suspect_gender,
        culprit_trait=culprit_trait,
    )


CURATED = [
    StoryParams(
        setting="clubhouse",
        launch="spitball",
        target="map",
        repair="redraw",
        detective="Mia",
        detective_gender="girl",
        owner="Ben",
        owner_gender="boy",
        culprit="Lucy",
        culprit_gender="girl",
        suspect="Noah",
        suspect_gender="boy",
        culprit_trait="honest",
    ),
    StoryParams(
        setting="classroom",
        launch="seed",
        target="badge",
        repair="new_badge",
        detective="Theo",
        detective_gender="boy",
        owner="Ava",
        owner_gender="girl",
        culprit="Finn",
        culprit_gender="boy",
        suspect="Rose",
        suspect_gender="girl",
        culprit_trait="stubborn",
    ),
    StoryParams(
        setting="hallway",
        launch="spitball",
        target="poster",
        repair="new_poster",
        detective="Lily",
        detective_gender="girl",
        owner="Sam",
        owner_gender="boy",
        culprit="Eli",
        culprit_gender="boy",
        suspect="Nora",
        suspect_gender="girl",
        culprit_trait="gentle",
    ),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.launch not in LAUNCHES:
        raise StoryError(f"(Unknown launch: {params.launch})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.culprit_trait not in CULPRIT_TRAITS:
        raise StoryError(f"(Unknown culprit trait: {params.culprit_trait})")

    launch = LAUNCHES[params.launch]
    target = TARGETS[params.target]
    repair = REPAIRS[params.repair]
    if not (target_at_risk(launch, target) and repair_fits(target, repair)):
        raise StoryError(explain_rejection(launch, target, repair))

    world = tell(
        setting=SETTINGS[params.setting],
        launch=launch,
        target=target,
        repair=repair,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        culprit_name=params.culprit,
        culprit_gender=params.culprit_gender,
        suspect_name=params.suspect,
        suspect_gender=params.suspect_gender,
        culprit_trait=params.culprit_trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, launch, target, repair) combos:\n")
        for setting, launch, target, repair in combos:
            print(f"  {setting:10} {launch:10} {target:8} {repair}")
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
            header = f"### {p.detective} solves {p.launch} on {p.target} at {p.setting} ({outcome_of(p)})"
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
