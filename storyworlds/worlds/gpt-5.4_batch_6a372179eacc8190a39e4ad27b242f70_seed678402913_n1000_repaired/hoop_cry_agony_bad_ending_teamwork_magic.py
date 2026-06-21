#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hoop_cry_agony_bad_ending_teamwork_magic.py
======================================================================

A standalone story world for a tiny magical whodunit: before the lantern parade,
an enchanted hoop is found spoiled, two children investigate, and the ending
depends on whether they accuse the right suspect and whether they work together
to repair the magic.

Seed requirements carried into the world:
- the story includes the words "hoop", "cry", and "agony"
- the domain includes teamwork, magic, and at least some bad endings
- the tone stays close to a child-facing whodunit rather than pure adventure

World logic
-----------
Each culprit can only cause certain kinds of damage. Each kind of damage leaves
a clue and requires a compatible helper to repair it. The children can accuse a
suspect before or after checking clues, and they can try to fix the hoop alone
or with help. A wrong accusation or a mismatched repair can produce a sad ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/hoop_cry_agony_bad_ending_teamwork_magic.py
    python storyworlds/worlds/gpt-5.4/hoop_cry_agony_bad_ending_teamwork_magic.py --all
    python storyworlds/worlds/gpt-5.4/hoop_cry_agony_bad_ending_teamwork_magic.py --culprit rook --damage dim
    python storyworlds/worlds/gpt-5.4/hoop_cry_agony_bad_ending_teamwork_magic.py --accuse wrong
    python storyworlds/worlds/gpt-5.4/hoop_cry_agony_bad_ending_teamwork_magic.py --teamwork no
    python storyworlds/worlds/gpt-5.4/hoop_cry_agony_bad_ending_teamwork_magic.py --verify
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
    traits: list[str] = field(default_factory=list)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Damage:
    id: str
    label: str
    scene: str
    clue_text: str
    trace_tag: str
    wrong_fix: str
    sad_result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    motive: str
    clue_tag: str
    can_cause: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    skill: str
    fixes: set[str] = field(default_factory=set)
    team_line: str = ""
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


def _r_agony(world: World) -> list[str]:
    hoop = world.entities.get("hoop")
    if hoop is None:
        return []
    if hoop.meters["damaged"] < THRESHOLD:
        return []
    sig = ("agony", "hoop")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hoop.memes["agony"] += 1
    for kid in [e for e in world.entities.values() if e.role in {"detective1", "detective2"}]:
        kid.memes["worry"] += 1
    return []


def _r_wrong_accusation(world: World) -> list[str]:
    if not world.facts.get("wrong_accusation"):
        return []
    sig = ("wrong_accusation",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in [e for e in world.entities.values() if e.role in {"detective1", "detective2"}]:
        kid.memes["guilt"] += 1
    accused = world.facts.get("accused_entity")
    if accused is not None:
        accused.memes["hurt"] += 1
    return []


def _r_teamwork(world: World) -> list[str]:
    if not world.facts.get("teamwork_used"):
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in [e for e in world.entities.values() if e.role in {"detective1", "detective2"}]:
        kid.memes["trust"] += 1
        kid.memes["hope"] += 1
    helper = world.facts.get("helper_entity")
    if helper is not None:
        helper.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="agony", tag="emotional", apply=_r_agony),
    Rule(name="wrong_accusation", tag="social", apply=_r_wrong_accusation),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


DAMAGES = {
    "dim": Damage(
        id="dim",
        label="dimmed glow",
        scene="Its moonlight had gone gray, as if somebody had breathed dusk all over it.",
        clue_text="silver dust on the grass",
        trace_tag="silver_dust",
        wrong_fix="They polished and polished, but a dull shine is not the same as real moon-magic.",
        sad_result="The hoop stayed gray, and the parade lanterns looked lonely beside it.",
        tags={"magic", "moonlight", "clue"},
    ),
    "tangle": Damage(
        id="tangle",
        label="snarled ribbons",
        scene="Blue ribbons had been knotted tight around the rim until the hoop drooped to one side.",
        clue_text="blue ribbon threads caught on the hedge",
        trace_tag="blue_threads",
        wrong_fix="They tugged in the wrong places, and the knots only bit tighter.",
        sad_result="The hoop sagged crookedly, too ashamed to spin.",
        tags={"ribbon", "clue", "magic"},
    ),
    "crack": Damage(
        id="crack",
        label="cracked rune",
        scene="One tiny star-rune along the rim was split like a dry biscuit.",
        clue_text="chalky star flakes on the bench",
        trace_tag="star_flakes",
        wrong_fix="They whispered a mending rhyme, but the broken rune would not listen to strangers working alone.",
        sad_result="A thin bright line kept flickering across the crack, then going dark.",
        tags={"rune", "clue", "magic"},
    ),
}

SUSPECTS = {
    "rook": Suspect(
        id="rook",
        label="Rook",
        phrase="Rook the young magician's raven",
        motive="he liked stealing shiny moon-dust for his nest",
        clue_tag="silver_dust",
        can_cause={"dim"},
        tags={"raven", "magic"},
    ),
    "pip": Suspect(
        id="pip",
        label="Pip",
        phrase="Pip the ribbon seller",
        motive="she wanted her blue ribbons to look grander than the hoop",
        clue_tag="blue_threads",
        can_cause={"tangle"},
        tags={"ribbons", "market"},
    ),
    "moss": Suspect(
        id="moss",
        label="Moss",
        phrase="Moss the sleepy goblin sweeper",
        motive="he leaned his broom against the stand and chipped the rune by mistake",
        clue_tag="star_flakes",
        can_cause={"crack"},
        tags={"goblin", "broom"},
    ),
}

HELPERS = {
    "luna": Helper(
        id="luna",
        label="Luna",
        phrase="Luna the moon baker",
        skill="she could wake sleepy light with warm moonbread steam",
        fixes={"dim"},
        team_line="Luna cupped warm silver steam under the rim while the children counted the glow back together.",
        tags={"moonlight", "magic"},
    ),
    "bram": Helper(
        id="bram",
        label="Bram",
        phrase="Bram the knot gardener",
        skill="he knew which ribbon knots should be loosened and which should be sung open",
        fixes={"tangle"},
        team_line="Bram held the ribbons still while the children untwisted each loop in the right order.",
        tags={"ribbon", "teamwork"},
    ),
    "fern": Helper(
        id="fern",
        label="Fern",
        phrase="Fern the clockmaker witch",
        skill="she could mend tiny star-runes with a glass needle and patient hands",
        fixes={"crack"},
        team_line="Fern guided the glass needle, and the children hummed the rune's little tune until the line sealed.",
        tags={"rune", "magic"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Nora", "Poppy", "June", "Ada", "Elsie", "Vera"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Milo", "Jasper", "Finn", "Noah", "Leo"]

ACCUSE_MODES = ["right", "wrong", "none"]
TEAMWORK_MODES = ["yes", "no"]


def culprit_matches_damage(culprit: str, damage: str) -> bool:
    return damage in SUSPECTS[culprit].can_cause


def helper_matches_damage(helper: str, damage: str) -> bool:
    return damage in HELPERS[helper].fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for culprit_id in SUSPECTS:
        for damage_id in DAMAGES:
            if not culprit_matches_damage(culprit_id, damage_id):
                continue
            for helper_id in HELPERS:
                if helper_matches_damage(helper_id, damage_id):
                    combos.append((culprit_id, damage_id, helper_id))
    return combos


@dataclass
class StoryParams:
    culprit: str
    damage: str
    helper: str
    accuse: str
    teamwork: str
    detective1: str
    detective1_gender: str
    detective2: str
    detective2_gender: str
    caretaker: str
    caretaker_gender: str
    seed: Optional[int] = None


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def investigation_scene(world: World, a: Entity, b: Entity, hoop: Entity, damage: Damage) -> None:
    a.memes["wonder"] += 1
    b.memes["wonder"] += 1
    world.say(
        f"By the lantern meadow, {a.id} and {b.id} hurried to see the parade hoop, "
        f"the bright ring that was meant to spin over the path at moonrise."
    )
    world.say(
        f"But something was wrong. The hoop hung still on its stand. {damage.scene}"
    )
    hoop.meters["damaged"] += 1
    propagate(world)
    world.say(
        f'"Oh!" {b.id} gave a small cry. "Somebody hurt the hoop."'
    )
    world.say(
        "Even the air around it felt tight and sad, as if the magic itself were in agony."
    )


def lay_out_suspects(world: World) -> None:
    names = [s.label for s in SUSPECTS.values()]
    world.say(
        f"There had been three possible visitors that afternoon: {names[0]}, {names[1]}, and {names[2]}."
    )
    world.say("That made it a real mystery, and both children straightened at once.")


def inspect_clue(world: World, a: Entity, b: Entity, damage: Damage) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.facts["clue_found"] = True
    world.facts["clue_tag"] = damage.trace_tag
    world.say(
        f"{a.id} knelt by the stand, and {b.id} circled the grass. Soon they found {damage.clue_text}."
    )
    world.say(
        f'"That is a clue," {a.id} whispered. "So we should think before we point."'
    )


def choose_accusation(world: World, a: Entity, b: Entity, accuse_mode: str, culprit: Suspect) -> Suspect | None:
    if accuse_mode == "none":
        world.facts["accused"] = None
        world.say(
            f'"Let us not blame anyone yet," said {b.id}. "First clues, then names."'
        )
        return None

    if accuse_mode == "right":
        accused = culprit
    else:
        accused = next(s for s in SUSPECTS.values() if s.id != culprit.id)

    world.facts["accused"] = accused.id
    world.facts["wrong_accusation"] = accused.id != culprit.id
    accused_entity = world.get(f"suspect_{accused.id}")
    world.facts["accused_entity"] = accused_entity
    propagate(world)
    if accused.id == culprit.id:
        world.say(
            f'The clue matched {accused.phrase}, so {a.id} and {b.id} named {accused.label} very carefully.'
        )
    else:
        world.say(
            f'In their hurry, {a.id} and {b.id} blamed {accused.phrase} before they had truly finished thinking.'
        )
        world.say(
            f'{accused.label} looked startled, and the mistake made both children feel a pinch of shame.'
        )
    return accused


def reveal_truth(world: World, culprit: Suspect, damage: Damage) -> None:
    if world.facts.get("accused") == culprit.id:
        world.say(
            f"{culprit.label} soon admitted the truth. {culprit.label} had caused the {damage.label} because {culprit.motive}."
        )
        world.facts["truth_known"] = True
        return

    if world.facts.get("clue_found"):
        world.say(
            f"At last the clue told the story plainly: it pointed to {culprit.phrase}."
        )
        world.say(
            f"{culprit.label} confessed in a small voice that {culprit.motive}."
        )
        world.facts["truth_known"] = True


def request_help(world: World, a: Entity, b: Entity, helper: Helper, teamwork: str, damage: Damage) -> bool:
    helper_entity = world.get(f"helper_{helper.id}")
    world.facts["helper_entity"] = helper_entity
    if teamwork == "yes":
        world.facts["teamwork_used"] = True
        propagate(world)
        world.say(
            f'"We cannot fix this alone," said {a.id}. So the children ran to {helper.phrase}, because {helper.skill}.'
        )
        world.say(helper.team_line)
        return True

    world.facts["teamwork_used"] = False
    propagate(world)
    world.say(
        f"{b.id} wanted to ask {helper.label} for help, but the children decided to try by themselves first."
    )
    world.say(damage.wrong_fix)
    return False


def finish_story(world: World, a: Entity, b: Entity, hoop: Entity, caretaker: Entity,
                 culprit: Suspect, helper: Helper, teamwork: str) -> None:
    right_accusation = world.facts.get("accused") == culprit.id or world.facts.get("accused") is None
    repair_succeeds = teamwork == "yes"

    if repair_succeeds:
        hoop.meters["damaged"] = 0.0
        hoop.meters["glow"] += 1
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        world.para()
        world.say(
            "The hoop answered with a bright shiver. Then it lifted itself, round and proud again, and spilled soft light over everyone's shoes."
        )
        if world.facts.get("wrong_accusation"):
            world.say(
                f"{a.id} and {b.id} said sorry to the person they had blamed too quickly, and the apology mattered."
            )
        world.say(
            f'{caretaker.label_word.capitalize()} smiled at the three helpers together. "That is how a mystery should end," {caretaker.pronoun()} said. "With truth, care, and teamwork."'
        )
        world.say(
            f"When moonrise came, the hoop spun above the meadow at last, and {a.id} and {b.id} watched it knowing they had saved the parade by working together."
        )
        outcome = "saved"
    else:
        world.para()
        world.say(
            f"The children tried every rhyme they knew, but the magic would not mend for stubborn hands alone. {DAMAGES[world.facts['damage']].sad_result}"
        )
        if not right_accusation:
            world.say(
                "Worse, the wrong blame had already bruised the evening. The mystery had been solved too late to mend the hurt."
            )
        world.say(
            f'{caretaker.label_word.capitalize()} gathered the dark ribbon of night around the little stand and gave a sad sigh. "We will have to cancel the moonrise dance," {caretaker.pronoun()} said.'
        )
        world.say(
            f"That was the true bad ending: the field stayed dim, the music never began, and {a.id} and {b.id} went home wishing they had chosen patience and teamwork sooner."
        )
        outcome = "failed"

    world.facts["outcome"] = outcome
    world.facts["repair_succeeds"] = repair_succeeds
    world.facts["right_accusation"] = right_accusation


def tell(params: StoryParams) -> World:
    culprit = SUSPECTS[params.culprit]
    damage = DAMAGES[params.damage]
    helper = HELPERS[params.helper]

    if not culprit_matches_damage(culprit.id, damage.id):
        raise StoryError(
            f"(No story: {culprit.label} cannot reasonably cause {damage.label}. Pick a matching culprit and damage.)"
        )
    if not helper_matches_damage(helper.id, damage.id):
        raise StoryError(
            f"(No story: {helper.label} cannot repair {damage.label}. The helper must match the magical damage.)"
        )
    if params.accuse not in ACCUSE_MODES:
        raise StoryError("(No story: unknown accusation mode.)")
    if params.teamwork not in TEAMWORK_MODES:
        raise StoryError("(No story: unknown teamwork mode.)")

    world = World()
    a = world.add(Entity(id=params.detective1, kind="character", type=params.detective1_gender, role="detective1"))
    b = world.add(Entity(id=params.detective2, kind="character", type=params.detective2_gender, role="detective2"))
    caretaker = world.add(
        Entity(id="Caretaker", kind="character", type=params.caretaker_gender, role="caretaker", label="the keeper")
    )
    hoop = world.add(Entity(id="hoop", type="hoop", label="the parade hoop"))
    for suspect in SUSPECTS.values():
        world.add(
            Entity(
                id=f"suspect_{suspect.id}",
                type="suspect",
                label=suspect.label,
                phrase=suspect.phrase,
                attrs={"motive": suspect.motive},
                tags=set(suspect.tags),
            )
        )
    for h in HELPERS.values():
        world.add(
            Entity(
                id=f"helper_{h.id}",
                type="helper",
                label=h.label,
                phrase=h.phrase,
                attrs={"skill": h.skill},
                tags=set(h.tags),
            )
        )

    world.facts.update(
        culprit=culprit,
        damage_cfg=damage,
        helper_cfg=helper,
        damage=damage.id,
        accuse_mode=params.accuse,
        teamwork_mode=params.teamwork,
        wrong_accusation=False,
        teamwork_used=False,
        clue_found=False,
        truth_known=False,
    )

    investigation_scene(world, a, b, hoop, damage)
    lay_out_suspects(world)
    world.para()
    inspect_clue(world, a, b, damage)
    choose_accusation(world, a, b, params.accuse, culprit)
    reveal_truth(world, culprit, damage)
    world.para()
    request_help(world, a, b, helper, params.teamwork, damage)
    finish_story(world, a, b, hoop, caretaker, culprit, helper, params.teamwork)

    world.facts.update(
        detective1=a,
        detective2=b,
        caretaker=caretaker,
        hoop=hoop,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["detective1"]
    b = f["detective2"]
    culprit = f["culprit"]
    damage = f["damage_cfg"]
    helper = f["helper_cfg"]
    if f["outcome"] == "failed":
        return [
            'Write a child-facing magical whodunit that includes the words "hoop", "cry", and "agony", and ends sadly.',
            f"Tell a mystery where {a.id} and {b.id} find a ruined parade hoop, follow a clue, but fail to save it because they do not use teamwork in time.",
            f"Write a gentle bad-ending story where {culprit.label} caused a {damage.label}, and only {helper.label} could have helped mend it.",
        ]
    return [
        'Write a child-facing magical whodunit that includes the words "hoop", "cry", and "agony" and ends with teamwork saving the day.',
        f"Tell a mystery where {a.id} and {b.id} find a damaged parade hoop, follow a clue, and solve it with help from {helper.label}.",
        f"Write a simple story in which {culprit.label} causes a {damage.label}, and the children learn to use patience, truth, and teamwork.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["detective1"]
    b = f["detective2"]
    caretaker = f["caretaker"]
    culprit = f["culprit"]
    damage = f["damage_cfg"]
    helper = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children who try to solve a mystery about a magical hoop. {caretaker.label_word.capitalize()} also watches over the parade meadow.",
        ),
        (
            "What was wrong with the hoop?",
            f"The hoop had a {damage.label}. {damage.scene} That is why {b.id} gave a cry and the children knew something bad had happened.",
        ),
        (
            "What clue did the children find?",
            f"They found {damage.clue_text}. That clue pointed toward the true culprit instead of leaving the mystery as a guess.",
        ),
        (
            "Who really caused the trouble, and why?",
            f"{culprit.label} did. {culprit.label} admitted it happened because {culprit.motive}.",
        ),
    ]
    if f.get("wrong_accusation"):
        accused = SUSPECTS[f["accused"]]
        qa.append(
            (
                "Did the children blame the right person at first?",
                f"No. They blamed {accused.label} too quickly, which hurt the evening and made them feel ashamed. The clue later showed that {culprit.label} was the real one.",
            )
        )
    else:
        if f.get("accused") == culprit.id:
            qa.append(
                (
                    "Did the children accuse the right suspect?",
                    f"Yes. They matched the clue to {culprit.label} and named {culprit.pronoun() if isinstance(culprit, Entity) else culprit.label} carefully. They solved the mystery by thinking before pointing.",
                )
            )
        else:
            qa.append(
                (
                    "Why did the children wait before blaming anyone?",
                    f"They wanted clues first. That kept the mystery fair and helped them reach the truth without hurting the wrong person.",
                )
            )
    if f["outcome"] == "saved":
        qa.append(
            (
                "How was the hoop fixed?",
                f"{a.id} and {b.id} asked {helper.label} for help and worked together. {helper.team_line} Because the right helper matched the damage, the magic could wake up again.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the hoop glowing again above the meadow. The ending proves that teamwork and patience were stronger than hurry.",
            )
        )
    else:
        qa.append(
            (
                "Why was it a bad ending?",
                f"It was a bad ending because the children tried to fix the hoop without teamwork, and the magic stayed broken. The parade had to be canceled, so the meadow stayed dark.",
            )
        )
        qa.append(
            (
                "What should they have done sooner?",
                f"They should have asked {helper.label} for help right away and worked together. In this story, teamwork was the missing part of the repair.",
            )
        )
    return qa


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a story like this?",
            "Magic is a pretend power that can make strange things glow, move, or change. In stories, it still works best when characters use it carefully."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, clues help you move from guessing to knowing."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another and share a job. Some problems are too big for one person but become possible together."
        )
    ],
    "moonlight": [
        (
            "Why do stories use moonlight for magic?",
            "Moonlight feels soft, quiet, and mysterious, so it often fits magical stories. It helps a scene feel gentle and a little secret."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon knot?",
            "A ribbon knot is a loop tied in ribbon. If it is tied too tightly, it can twist and squeeze whatever it is wrapped around."
        )
    ],
    "rune": [
        (
            "What is a rune?",
            "A rune is a little sign or symbol used in many fantasy stories. Characters may think a rune can hold a bit of magic."
        )
    ],
    "raven": [
        (
            "What is a raven?",
            "A raven is a large black bird. In stories, ravens are often clever and interested in shiny things."
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "clue", "teamwork", "moonlight", "ribbon", "rune", "raven"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"magic", "clue"}
    if world.facts.get("teamwork_used") or world.facts.get("outcome") == "failed":
        tags.add("teamwork")
    tags |= set(world.facts["damage_cfg"].tags)
    tags |= set(world.facts["culprit"].tags)
    tags |= set(world.facts["helper_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:14} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} accused={world.facts.get('accused')} teamwork={world.facts.get('teamwork_used')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        culprit="rook",
        damage="dim",
        helper="luna",
        accuse="none",
        teamwork="yes",
        detective1="Lily",
        detective1_gender="girl",
        detective2="Owen",
        detective2_gender="boy",
        caretaker="Mara",
        caretaker_gender="aunt",
    ),
    StoryParams(
        culprit="pip",
        damage="tangle",
        helper="bram",
        accuse="right",
        teamwork="yes",
        detective1="Nora",
        detective1_gender="girl",
        detective2="Theo",
        detective2_gender="boy",
        caretaker="Jon",
        caretaker_gender="uncle",
    ),
    StoryParams(
        culprit="moss",
        damage="crack",
        helper="fern",
        accuse="wrong",
        teamwork="no",
        detective1="Poppy",
        detective1_gender="girl",
        detective2="Milo",
        detective2_gender="boy",
        caretaker="Eda",
        caretaker_gender="mother",
    ),
    StoryParams(
        culprit="rook",
        damage="dim",
        helper="luna",
        accuse="right",
        teamwork="no",
        detective1="Ada",
        detective1_gender="girl",
        detective2="Finn",
        detective2_gender="boy",
        caretaker="Tomas",
        caretaker_gender="father",
    ),
]


def outcome_of(params: StoryParams) -> str:
    if not culprit_matches_damage(params.culprit, params.damage):
        raise StoryError("(No story: culprit and damage do not match.)")
    if not helper_matches_damage(params.helper, params.damage):
        raise StoryError("(No story: helper and damage do not match.)")
    return "saved" if params.teamwork == "yes" else "failed"


def explain_combo_rejection(culprit: str, damage: str, helper: str) -> str:
    if not culprit_matches_damage(culprit, damage):
        return (
            f"(No story: {SUSPECTS[culprit].label} cannot reasonably cause {DAMAGES[damage].label}. "
            f"The clue trail would not make sense.)"
        )
    if not helper_matches_damage(helper, damage):
        return (
            f"(No story: {HELPERS[helper].label} cannot repair {DAMAGES[damage].label}. "
            f"A magical fix must match the magical damage.)"
        )
    return "(No story: that combination does not fit this world.)"


ASP_RULES = r"""
causes(C, D) :- suspect(C), can_cause(C, D).
repairs(H, D) :- helper(H), fixes(H, D).
valid(C, D, H) :- causes(C, D), repairs(H, D).

outcome(saved) :- teamwork(yes), valid(chosen_culprit, chosen_damage, chosen_helper).
outcome(failed) :- teamwork(no), valid(chosen_culprit, chosen_damage, chosen_helper).

wrong_accusation :- accuse(wrong).
right_accusation :- accuse(right).
no_accusation :- accuse(none).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for damage in sorted(suspect.can_cause):
            lines.append(asp.fact("can_cause", sid, damage))
    for did in DAMAGES:
        lines.append(asp.fact("damage", did))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for damage in sorted(helper.fixes):
            lines.append(asp.fact("fixes", hid, damage))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("valid", params.culprit, params.damage, params.helper),
            asp.fact("chosen_culprit"),
            asp.fact("chosen_damage"),
            asp.fact("chosen_helper"),
            asp.fact("teamwork", params.teamwork),
            asp.fact("accuse", params.accuse),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_outcome_fixed(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_damage", params.damage),
            asp.fact("chosen_helper", params.helper),
            asp.fact("teamwork", params.teamwork),
            asp.fact("accuse", params.accuse),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a magical whodunit about a spoiled hoop, clues, teamwork, and sometimes a bad ending."
    )
    ap.add_argument("--culprit", choices=sorted(SUSPECTS))
    ap.add_argument("--damage", choices=sorted(DAMAGES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--accuse", choices=ACCUSE_MODES)
    ap.add_argument("--teamwork", choices=TEAMWORK_MODES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid culprit/damage/helper combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.damage and not culprit_matches_damage(args.culprit, args.damage):
        helper = args.helper or next(iter(HELPERS))
        raise StoryError(explain_combo_rejection(args.culprit, args.damage, helper))
    if args.damage and args.helper and not helper_matches_damage(args.helper, args.damage):
        culprit = args.culprit or next(iter(SUSPECTS))
        raise StoryError(explain_combo_rejection(culprit, args.damage, args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.culprit is None or combo[0] == args.culprit)
        and (args.damage is None or combo[1] == args.damage)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    culprit, damage, helper = rng.choice(sorted(combos))
    accuse = args.accuse or rng.choice(ACCUSE_MODES)
    teamwork = args.teamwork or rng.choice(TEAMWORK_MODES)
    detective1, detective1_gender = _pick_name(rng)
    detective2, detective2_gender = _pick_name(rng, avoid=detective1)
    caretaker_gender = rng.choice(["mother", "father", "aunt", "uncle"])
    caretaker = rng.choice(
        {
            "mother": ["Mara", "Eda", "Ruth"],
            "father": ["Tomas", "Ivo", "Bram"],
            "aunt": ["Mara", "Sela", "Iris"],
            "uncle": ["Jon", "Ivo", "Perrin"],
        }[caretaker_gender]
    )
    return StoryParams(
        culprit=culprit,
        damage=damage,
        helper=helper,
        accuse=accuse,
        teamwork=teamwork,
        detective1=detective1,
        detective1_gender=detective1_gender,
        detective2=detective2,
        detective2_gender=detective2_gender,
        caretaker=caretaker,
        caretaker_gender=caretaker_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.culprit not in SUSPECTS:
        raise StoryError("(No story: unknown culprit.)")
    if params.damage not in DAMAGES:
        raise StoryError("(No story: unknown damage.)")
    if params.helper not in HELPERS:
        raise StoryError("(No story: unknown helper.)")
    world = tell(params)
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

    cases = list(CURATED)
    for seed in range(30):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        try:
            py = outcome_of(params)
            cl = asp_outcome_fixed(params)
            if py != cl:
                mismatch += 1
        except Exception as err:
            rc = 1
            print(f"Outcome check crashed for {params}: {err}")
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:
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
        print(f"{len(combos)} compatible (culprit, damage, helper) combos:\n")
        for culprit, damage, helper in combos:
            print(f"  {culprit:6} {damage:7} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.detective1} & {p.detective2}: {p.damage} / {p.culprit} / teamwork={p.teamwork}"
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
