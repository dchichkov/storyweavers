#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/paste_soccer_field_foreshadowing_lesson_learned_magic.py
====================================================================================

A standalone storyworld about a child on a soccer field who wants a quick,
magical shortcut: shimmering paste. The world keeps the tone bright and heroic,
but the simulation insists on a grounded lesson: sticky magic is not a real fix
for sports gear.

The source-tale premise rebuilt here:
- A child arrives at a soccer field imagining everyone as superheroes.
- Something on their gear is loose or torn right before play.
- A tube of glowing "hero paste" promises an instant magical fix.
- A helper warns that fast sticky magic can trap more than it helps.
- Either the child listens, or they use the paste anyway and a sticky mishap
  proves the warning true.
- A calm coach uses the proper repair and the child learns the honest way.

Run it
------
    python storyworlds/worlds/gpt-5.4/paste_soccer_field_foreshadowing_lesson_learned_magic.py
    python storyworlds/worlds/gpt-5.4/paste_soccer_field_foreshadowing_lesson_learned_magic.py --issue lace --repair retie
    python storyworlds/worlds/gpt-5.4/paste_soccer_field_foreshadowing_lesson_learned_magic.py --issue badge --repair retie
    python storyworlds/worlds/gpt-5.4/paste_soccer_field_foreshadowing_lesson_learned_magic.py --all
    python storyworlds/worlds/gpt-5.4/paste_soccer_field_foreshadowing_lesson_learned_magic.py --qa --json
    python storyworlds/worlds/gpt-5.4/paste_soccer_field_foreshadowing_lesson_learned_magic.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "coach_f"}
        male = {"boy", "father", "man", "coach_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"coach_f", "coach_m"}:
            return "coach"
        return self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Motif:
    id: str
    squad: str
    intro: str
    title_a: str
    title_b: str
    chant: str
    ending: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Issue:
    id: str
    label: str
    phrase: str
    place_on_gear: str
    action: str
    warning: str
    mishap: str
    repair_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Repair:
    id: str
    label: str
    works_for: set[str] = field(default_factory=set)
    do_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_sticky_ball(world: World) -> list[str]:
    out: list[str] = []
    gear = world.get("gear")
    ball = world.get("ball")
    kid = world.get("kid")
    issue_id = gear.attrs.get("issue")
    if gear.meters["sticky"] < THRESHOLD:
        return out
    if issue_id not in {"lace", "glove"}:
        return out
    sig = ("sticky_ball", issue_id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ball.meters["trapped"] += 1
    kid.meters["off_balance"] += 1
    kid.memes["alarm"] += 1
    out.append("__sticky_ball__")
    return out


def _r_sticky_snag(world: World) -> list[str]:
    out: list[str] = []
    gear = world.get("gear")
    kid = world.get("kid")
    if gear.meters["sticky"] < THRESHOLD or gear.attrs.get("issue") != "badge":
        return out
    sig = ("sticky_snag", "badge")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gear.meters["snagged"] += 1
    kid.meters["stopped"] += 1
    kid.memes["alarm"] += 1
    out.append("__sticky_snag__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sticky_ball", tag="physical", apply=_r_sticky_ball),
    Rule(name="sticky_snag", tag="physical", apply=_r_sticky_snag),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def repair_fits(issue: Issue, repair: Repair) -> bool:
    return issue.id in repair.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for motif_id in MOTIFS:
        for issue_id, issue in ISSUES.items():
            for repair_id, repair in REPAIRS.items():
                if repair_fits(issue, repair):
                    combos.append((motif_id, issue_id, repair_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, kid_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > kid_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if helper_older else 0.0)
    return helper_older and authority > BRAVERY_INIT


def predict_mishap(world: World) -> dict[str, bool]:
    sim = world.copy()
    sim.get("gear").meters["sticky"] += 1
    propagate(sim, narrate=False)
    return {
        "sticky_ball": sim.get("ball").meters["trapped"] >= THRESHOLD,
        "sticky_snag": sim.get("gear").meters["snagged"] >= THRESHOLD,
    }


def introduce(world: World, kid: Entity, helper: Entity, motif: Motif) -> None:
    kid.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Late afternoon sun poured across the soccer field while {kid.id} and {helper.id} "
        f"raced onto the grass pretending they were the {motif.squad}. {motif.intro}"
    )
    world.say(
        f'"{motif.title_a} {kid.id} and {motif.title_b} {helper.id}!" {kid.id} shouted. '
        f'"{motif.chant}"'
    )


def setup_issue(world: World, kid: Entity, issue: Issue) -> None:
    gear = world.get("gear")
    gear.meters["loose"] += 1
    world.say(
        f"Just before practice began, {kid.id} noticed that {issue.phrase} "
        f"on {kid.pronoun('possessive')} gear was wrong. {issue.warning}"
    )


def foreshadow(world: World, coach: Entity) -> None:
    world.say(
        f"Near the bench sat a silver tube of shimmer paste from the costume box. "
        f"{coach.label_word.capitalize()} glanced at it and said, "
        f'"Quick sticky magic can look helpful, but if it grabs the wrong thing, '
        f'it makes a bigger problem on the field."'
    )


def tempt(world: World, kid: Entity, issue: Issue) -> None:
    kid.memes["bravado"] += 1
    world.say(
        f"{kid.id} picked up the tube and watched the paste sparkle like trapped starlight. "
        f'"I only need one tiny dab," {kid.pronoun()} said. "Then I can {issue.action} like a real hero."'
    )


def warn(world: World, helper: Entity, kid: Entity, issue: Issue, coach: Entity) -> None:
    pred = predict_mishap(world)
    helper.memes["caution"] += 1
    world.facts["predicted_sticky_ball"] = pred["sticky_ball"]
    world.facts["predicted_sticky_snag"] = pred["sticky_snag"]
    extra = ""
    if pred["sticky_ball"]:
        extra = " The ball could stick where it should bounce free."
    elif pred["sticky_snag"]:
        extra = " Your cape could catch and stop you in the middle of your dash."
    world.say(
        f'{helper.id} lowered {kid.id}\'s hand. "{coach.label_word.capitalize()} just warned us," '
        f'{helper.pronoun()} said. "That paste is magic, but not team magic.{extra} '
        f'If something is loose, we should fix it the proper way."'
    )


def back_down(world: World, kid: Entity, helper: Entity, coach: Entity, repair: Repair, issue: Issue) -> None:
    kid.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{kid.id} looked at the glittering tube, then at {helper.id}, and let out a slow breath. '
        f'"Okay," {kid.pronoun()} said. "Real heroes do not cheat with sticky shortcuts."'
    )
    world.say(
        f"{coach.label_word.capitalize()} smiled and {repair.do_text} {issue.place_on_gear} instead. "
        f"Soon the gear felt steady again, and the silver paste stayed closed on the bench."
    )


def use_paste(world: World, kid: Entity, issue: Issue) -> None:
    gear = world.get("gear")
    gear.meters["sticky"] += 1
    gear.meters["loose"] = 0.0
    kid.memes["defiance"] += 1
    world.say(
        f'Before anyone could stop {kid.pronoun("object")}, {kid.id} squeezed a shining line of paste '
        f"over {issue.place_on_gear}. For one second it seemed perfect. The glow sealed everything with a soft blue wink."
    )
    propagate(world, narrate=False)


def mishap(world: World, kid: Entity, issue: Issue) -> None:
    ball = world.get("ball")
    gear = world.get("gear")
    if ball.meters["trapped"] >= THRESHOLD:
        world.say(
            f"Then the whistle blew, {kid.id} tried to {issue.action}, and the ball did not pop free. "
            f"{issue.mishap}"
        )
    elif gear.meters["snagged"] >= THRESHOLD:
        world.say(
            f"Then the whistle blew, {kid.id} sprang forward, and {issue.mishap}"
        )
    else:
        world.say(
            f"Then the whistle blew, and the glowing fix felt wrong at once."
        )


def coach_help(world: World, coach: Entity, repair: Repair, issue: Issue, kid: Entity, helper: Entity) -> None:
    gear = world.get("gear")
    ball = world.get("ball")
    gear.meters["sticky"] = 0.0
    gear.meters["snagged"] = 0.0
    ball.meters["trapped"] = 0.0
    kid.meters["off_balance"] = 0.0
    kid.meters["stopped"] = 0.0
    for who in (kid, helper):
        who.memes["alarm"] = 0.0
        who.memes["relief"] += 1
        who.memes["lesson"] += 1
    world.say(
        f"{coach.label_word.capitalize()} hurried over, knelt in the grass, and spoke in a calm superhero voice. "
        f'"Freeze, team. We fix problems without panic."'
    )
    world.say(
        f"With a wet towel, patient fingers, and no scolding shout, "
        f"{coach.pronoun()} cleaned away the paste and {repair.do_text} {issue.place_on_gear} the right way."
    )


def lesson(world: World, coach: Entity, kid: Entity, helper: Entity) -> None:
    kid.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f'Then {coach.label_word} tapped the silver tube and said, '
        f'"Magic can be bright, but a bright trick is not always a good fix. '
        f'Teamwork, patience, and honest repair are stronger powers."'
    )
    world.say(
        f'{kid.id} nodded. "{helper.id} was right," {kid.pronoun()} said. '
        f'"Next time I will stop and fix the real problem first."'
    )


def ending(world: World, motif: Motif, kid: Entity, helper: Entity, issue: Issue, averted: bool) -> None:
    kid.memes["joy"] += 1
    helper.memes["joy"] += 1
    if averted:
        world.say(
            f"When practice began, {kid.id} ran light and free across the soccer field. "
            f"No glowing paste tugged at anything. The only magic left was the sunset on the net and the way the team moved together."
        )
    else:
        world.say(
            f"A little later, with {issue.label} fixed properly at last, {kid.id} passed the ball cleanly to {helper.id}. "
            f"They grinned at each other like true heroes, and {motif.ending}"
        )


def tell(
    motif: Motif,
    issue: Issue,
    repair: Repair,
    kid_name: str = "Mia",
    kid_gender: str = "girl",
    helper_name: str = "Leo",
    helper_gender: str = "boy",
    coach_gender: str = "coach_f",
    trait: str = "careful",
    relation: str = "siblings",
    kid_age: int = 5,
    helper_age: int = 7,
) -> World:
    world = World()
    kid = world.add(Entity(
        id=kid_name,
        kind="character",
        type=kid_gender,
        role="hero",
        age=kid_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    coach = world.add(Entity(
        id="Coach",
        kind="character",
        type=coach_gender,
        role="coach",
        label="the coach",
    ))
    gear = world.add(Entity(
        id="gear",
        type="gear",
        label=issue.label,
        attrs={"issue": issue.id},
    ))
    ball = world.add(Entity(
        id="ball",
        type="ball",
        label="soccer ball",
    ))
    world.facts["field"] = "soccer field"

    kid.memes["bravery"] = BRAVERY_INIT
    helper.memes["caution"] = initial_caution(trait)

    introduce(world, kid, helper, motif)
    setup_issue(world, kid, issue)

    world.para()
    foreshadow(world, coach)
    tempt(world, kid, issue)
    warn(world, helper, kid, issue, coach)

    averted = would_avert(relation, kid_age, helper_age, trait)
    world.facts["averted"] = averted

    world.para()
    if averted:
        back_down(world, kid, helper, coach, repair, issue)
    else:
        use_paste(world, kid, issue)
        mishap(world, kid, issue)
        world.para()
        coach_help(world, coach, repair, issue, kid, helper)
        lesson(world, coach, kid, helper)

    world.para()
    ending(world, motif, kid, helper, issue, averted)

    outcome = "averted" if averted else "sticky"
    world.facts.update(
        motif=motif,
        issue_cfg=issue,
        repair=repair,
        kid=kid,
        helper=helper,
        coach=coach,
        gear=gear,
        ball=ball,
        relation=relation,
        outcome=outcome,
        used_paste=not averted,
        learned=kid.memes["lesson"] >= THRESHOLD or averted,
    )
    return world


MOTIFS = {
    "meteor": Motif(
        id="meteor",
        squad="Meteor Guards",
        intro="Their shadows stretched long behind them like capes, and every orange cone looked like a tiny city waiting to be saved.",
        title_a="Captain",
        title_b="Wing",
        chant="Meteor Guards, defend the goal!",
        ending="the game felt faster, fairer, and brighter than any tube of pretend magic.",
    ),
    "thunder": Motif(
        id="thunder",
        squad="Thunder Boots",
        intro="The white field lines looked like secret runways for flying heroes, and the goal net shivered in the breeze like a giant silver shield.",
        title_a="Captain",
        title_b="Spark",
        chant="Thunder Boots, save the day!",
        ending="their small team looked more superhero-like than ever, even without a single glowing trick.",
    ),
    "comet": Motif(
        id="comet",
        squad="Comet Keepers",
        intro="Even the soccer ball seemed charged with moonlight, as if one brave pass could send it rolling through the sky.",
        title_a="Captain",
        title_b="Scout",
        chant="Comet Keepers, guard the field!",
        ending="the field did not need sticky spells after all; it needed careful feet and friends who told the truth.",
    ),
}

ISSUES = {
    "lace": Issue(
        id="lace",
        label="loose lace",
        phrase="one long lace",
        place_on_gear="the lace on one shoe",
        action="dash for the ball",
        warning="It flopped against the grass like a tiny white tail, easy to step on and hard to trust.",
        mishap="The paste clung to the side of the ball, and the ball stuck to the shoe for a jumpy second before wobbling away. "
               "Startled, {name} windmilled {poss} arms and nearly sat right down on the grass.",
        repair_tags={"retie"},
        tags={"shoelaces", "soccer", "paste"},
    ),
    "badge": Issue(
        id="badge",
        label="loose badge",
        phrase="the shining star badge",
        place_on_gear="the cape badge at the shoulder",
        action="sprint down the sideline",
        warning="It tilted and flapped whenever the breeze touched it, as if it might peel away at the wrong moment.",
        mishap="the sticky badge grabbed a loop of the goal net as the cape streamed behind. "
               "The cape tugged tight, and {name} stopped with a surprised squeak instead of a heroic slide.",
        repair_tags={"pin"},
        tags={"cape", "soccer", "paste"},
    ),
    "glove": Issue(
        id="glove",
        label="split glove seam",
        phrase="a split seam",
        place_on_gear="the seam on one goalie glove",
        action="block a fast shot",
        warning="A finger kept peeking through the split, and that made the glove feel more wiggly than strong.",
        mishap="The glowing paste kissed the ball and held on. Instead of a clean save and throw, the ball stuck to the glove, "
               "and {name} had to flap {poss} hand in surprise while everyone stared.",
        repair_tags={"tape"},
        tags={"glove", "soccer", "paste"},
    ),
}

REPAIRS = {
    "retie": Repair(
        id="retie",
        label="retie the lace",
        works_for={"lace"},
        do_text="retied",
        qa_text="retied the lace into a snug knot",
        tags={"laces", "repair"},
    ),
    "pin": Repair(
        id="pin",
        label="pin the badge",
        works_for={"badge"},
        do_text="fastened a safe pin through",
        qa_text="fastened the badge safely with a pin",
        tags={"badge", "repair"},
    ),
    "tape": Repair(
        id="tape",
        label="tape the glove seam",
        works_for={"glove"},
        do_text="wrapped sports tape around",
        qa_text="wrapped sports tape around the glove seam",
        tags={"glove", "repair"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Lily", "Ava", "Nora", "Ruby", "Ella", "June"]
BOY_NAMES = ["Leo", "Max", "Noah", "Ben", "Eli", "Finn", "Theo", "Sam"]
TRAITS = ["careful", "steady", "thoughtful", "wise", "curious", "bold"]


@dataclass
class StoryParams:
    motif: str
    issue: str
    repair: str
    kid_name: str
    kid_gender: str
    helper_name: str
    helper_gender: str
    coach_gender: str
    trait: str
    relation: str = "siblings"
    kid_age: int = 5
    helper_age: int = 7
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "paste": [
        (
            "What is paste?",
            "Paste is a sticky stuff used to make things hold together. If you put it on the wrong thing, it can glue parts together that still need to move.",
        )
    ],
    "soccer": [
        (
            "Why should a soccer ball move freely?",
            "A soccer ball needs to roll, bounce, and fly where players kick or throw it. If it sticks to a shoe or glove, the game stops feeling safe and fair.",
        )
    ],
    "shoelaces": [
        (
            "Why do you tie your shoelaces before running?",
            "Tied shoelaces help your shoes stay snug on your feet. Loose laces can catch under a shoe or distract you when you run.",
        )
    ],
    "cape": [
        (
            "Why can a cape snag on something?",
            "A cape is loose cloth, so it can catch on hooks, fences, or nets if it swings too close. That is why costumes should be careful around sports gear.",
        )
    ],
    "glove": [
        (
            "What does a goalie glove do?",
            "A goalie glove helps a player catch and block the ball with a better grip. It still needs to bend and open, so a bad sticky fix can make it work worse.",
        )
    ],
    "repair": [
        (
            "Why is a real repair better than a quick sticky trick?",
            "A real repair fixes the part that is loose or torn. A quick trick may hide the problem for a moment, but it can make a new problem later.",
        )
    ],
    "badge": [
        (
            "What is a badge on a costume?",
            "A badge is a small sign or decoration that shows a team, hero, or idea. If it gets loose, it should be fastened properly so it does not fall off or catch on something.",
        )
    ],
    "laces": [
        (
            "How can you fix a loose shoelace?",
            "You stop, make the loops, and tie the lace snugly so it stays in place. That takes a little longer than guessing, but it lets you run safely.",
        )
    ],
}
KNOWLEDGE_ORDER = ["paste", "soccer", "shoelaces", "cape", "glove", "badge", "repair", "laces"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    issue = f["issue_cfg"]
    motif = f["motif"]
    if f["outcome"] == "averted":
        return [
            f'Write a superhero-style story for a 3-to-5-year-old set on a soccer field that includes the word "paste" and a warning that turns out to be true before anything bad happens.',
            f"Tell a gentle story where {kid.id} wants to use glowing paste on {issue.place_on_gear}, but {helper.id} helps {kid.pronoun('object')} choose the honest fix instead.",
            f'Write a small magical sports story about the {motif.squad} where foreshadowing leads to a lesson learned and the hero listens in time.',
        ]
    return [
        f'Write a superhero-style story for a 3-to-5-year-old set on a soccer field that includes the word "paste", a magical shortcut, and a lesson learned.',
        f"Tell a story where {kid.id} uses glowing paste to fix {issue.place_on_gear}, the warning comes true, and a calm coach helps afterward.",
        f'Write a child-facing sports story with foreshadowing, magic, and a clear ending image that shows why a proper repair is better than a sticky shortcut.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    helper = f["helper"]
    coach = f["coach"]
    issue = f["issue_cfg"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid.id} and {helper.id}, two children pretending to be superheroes on a soccer field, and their coach who helps them. The big problem starts when {kid.id} wants a fast magical fix.",
        ),
        (
            "What problem did the child notice before practice?",
            f"{kid.id} noticed {issue.phrase} was wrong on {kid.pronoun('possessive')} gear. That made the quick tube of paste feel tempting because {kid.pronoun()} wanted to play right away.",
        ),
        (
            "What was the foreshadowing in the story?",
            f"The coach warned that quick sticky magic can grab the wrong thing and make a bigger problem on the field. That warning mattered because it came true later when the paste did exactly what the coach feared.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"Why did {kid.id} stop using the paste?",
                f"{helper.id} repeated the coach's warning and helped {kid.id} imagine what the sticky magic could do. Because {helper.id} had enough calm authority, {kid.id} listened and chose the proper repair instead.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the gear fixed the right way and the paste still closed on the bench. The ending shows that the real superhero choice was patience, not a flashy shortcut.",
            )
        )
    else:
        mishap_kind = "the ball stuck where it should have moved" if world.get("ball").label == "soccer ball" and f.get("predicted_sticky_ball") else "the cape snagged when it should have flown free"
        qa.append(
            (
                f"What happened after {kid.id} used the paste?",
                f"The warning came true: {mishap_kind}. The paste seemed magical for one second, but then it trapped part of play instead of helping.",
            )
        )
        qa.append(
            (
                f"How did the coach solve the problem?",
                f"The coach calmly cleaned away the paste and {repair.qa_text}. That fixed the real problem instead of covering it up with more sticky magic.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{kid.id} learned that a bright shortcut is not always a brave one. A proper repair takes more patience, but it keeps the game safe, fair, and ready to move.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"paste", "soccer", "repair"}
    issue = world.facts["issue_cfg"]
    repair = world.facts["repair"]
    tags |= set(issue.tags)
    tags |= set(repair.tags)
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        motif="meteor",
        issue="lace",
        repair="retie",
        kid_name="Mia",
        kid_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        coach_gender="coach_f",
        trait="careful",
        relation="siblings",
        kid_age=5,
        helper_age=7,
    ),
    StoryParams(
        motif="thunder",
        issue="badge",
        repair="pin",
        kid_name="Ben",
        kid_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        coach_gender="coach_m",
        trait="curious",
        relation="friends",
        kid_age=6,
        helper_age=6,
    ),
    StoryParams(
        motif="comet",
        issue="glove",
        repair="tape",
        kid_name="Zoe",
        kid_gender="girl",
        helper_name="Nora",
        helper_gender="girl",
        coach_gender="coach_f",
        trait="wise",
        relation="siblings",
        kid_age=4,
        helper_age=7,
    ),
]


def explain_rejection(issue: Issue, repair: Repair) -> str:
    return (
        f"(No story: '{repair.id}' is not a proper fix for {issue.label}. "
        f"The lesson only works when the coach can solve the same gear problem honestly.)"
    )


ASP_RULES = r"""
valid(M, I, R) :- motif(M), issue(I), repair(R), works_for(R, I).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

helper_older :- relation(siblings), kid_age(K), helper_age(H), H > K.
bonus(4) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(sticky) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for motif_id in MOTIFS:
        lines.append(asp.fact("motif", motif_id))
    for issue_id in ISSUES:
        lines.append(asp.fact("issue", issue_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for issue_id in sorted(repair.works_for):
            lines.append(asp.fact("works_for", repair_id, issue_id))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("kid_age", params.kid_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.kid_age, params.helper_age, params.trait) else "sticky"


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

    parser = build_parser()
    cases = list(CURATED)
    for s in range(120):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        emit(smoke, trace=False, qa=False, header="### smoke")
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: superhero children on a soccer field learn that magical paste is not a real repair."
    )
    ap.add_argument("--motif", choices=MOTIFS)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--coach-gender", choices=["coach_f", "coach_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (motif, issue, repair) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check inline ASP parity and run a smoke generation test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.issue and args.repair:
        issue = ISSUES[args.issue]
        repair = REPAIRS[args.repair]
        if not repair_fits(issue, repair):
            raise StoryError(explain_rejection(issue, repair))

    combos = [
        c
        for c in valid_combos()
        if (args.motif is None or c[0] == args.motif)
        and (args.issue is None or c[1] == args.issue)
        and (args.repair is None or c[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    motif, issue, repair = rng.choice(sorted(combos))
    kid_name, kid_gender = _pick_name(rng)
    helper_name, helper_gender = _pick_name(rng, avoid=kid_name)
    coach_gender = args.coach_gender or rng.choice(["coach_f", "coach_m"])
    trait = rng.choice(TRAITS)
    relation = args.relation or rng.choice(["siblings", "friends"])
    kid_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        motif=motif,
        issue=issue,
        repair=repair,
        kid_name=kid_name,
        kid_gender=kid_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        coach_gender=coach_gender,
        trait=trait,
        relation=relation,
        kid_age=kid_age,
        helper_age=helper_age,
    )


def _render_issue_mishap(issue: Issue, kid: Entity) -> str:
    return issue.mishap.format(name=kid.id, poss=kid.pronoun("possessive"))


def generate(params: StoryParams) -> StorySample:
    if params.motif not in MOTIFS:
        raise StoryError(f"(Unknown motif: {params.motif})")
    if params.issue not in ISSUES:
        raise StoryError(f"(Unknown issue: {params.issue})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    issue = ISSUES[params.issue]
    repair = REPAIRS[params.repair]
    if not repair_fits(issue, repair):
        raise StoryError(explain_rejection(issue, repair))

    issue_for_telling = Issue(
        id=issue.id,
        label=issue.label,
        phrase=issue.phrase,
        place_on_gear=issue.place_on_gear,
        action=issue.action,
        warning=issue.warning,
        mishap=issue.mishap,
        repair_tags=set(issue.repair_tags),
        tags=set(issue.tags),
    )

    world = tell(
        motif=MOTIFS[params.motif],
        issue=issue_for_telling,
        repair=repair,
        kid_name=params.kid_name,
        kid_gender=params.kid_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        coach_gender=params.coach_gender,
        trait=params.trait,
        relation=params.relation,
        kid_age=params.kid_age,
        helper_age=params.helper_age,
    )

    if world.facts["outcome"] == "sticky":
        # Replace issue-specific placeholder text with the actual child data.
        story = world.render().replace(issue_for_telling.mishap, _render_issue_mishap(issue_for_telling, world.facts["kid"]))
    else:
        story = world.render()

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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (motif, issue, repair) combos:\n")
        for motif, issue, repair in combos:
            print(f"  {motif:8} {issue:6} {repair}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.kid_name} & {p.helper_name}: {p.issue} on the soccer field ({p.motif}, {p.repair}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
