#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/quote_problem_solving_rhyme_sharing_comedy.py
=========================================================================

A standalone story world about two children making a funny quote prop for a
little comedy performance. The world centers on:

- a silly quote written on a prop
- a small physical problem that threatens the act
- sharing instead of grabbing
- a short rhyme that helps them solve it together
- a cheerful comedy ending

Run it
------
python storyworlds/worlds/gpt-5.4/quote_problem_solving_rhyme_sharing_comedy.py
python storyworlds/worlds/gpt-5.4/quote_problem_solving_rhyme_sharing_comedy.py --all
python storyworlds/worlds/gpt-5.4/quote_problem_solving_rhyme_sharing_comedy.py --qa
python storyworlds/worlds/gpt-5.4/quote_problem_solving_rhyme_sharing_comedy.py --trace
python storyworlds/worlds/gpt-5.4/quote_problem_solving_rhyme_sharing_comedy.py --asp
python storyworlds/worlds/gpt-5.4/quote_problem_solving_rhyme_sharing_comedy.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "teacher", "woman"}
        male = {"boy", "father", "uncle", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher": "teacher",
            "aunt": "aunt",
            "grandpa": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    event: str
    audience: str
    helper_type: str
    opening: str
    ending_image: str
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


@dataclass
class PropCfg:
    id: str
    label: str
    phrase: str
    quote_text: str
    detail: str
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
class ProblemCfg:
    id: str
    label: str
    damage: str
    beat: str
    visible: str
    severity: int
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


@dataclass
class FixCfg:
    id: str
    label: str
    repairs: set[str]
    power: int
    text: str
    qa_text: str
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


@dataclass
class ShareCfg:
    id: str
    label: str
    cooperation: int
    setup_line: str
    perform_line: str
    qa_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "shared": False,
            "fixed": False,
            "giggles_ready": False,
            "problem_seen": False,
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"kid_a", "kid_b"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_conflict_tension(world: World) -> list[str]:
    kids = world.kids()
    if len(kids) != 2:
        return []
    if not all(k.memes["conflict"] >= THRESHOLD for k in kids):
        return []
    sig = ("tension", "kids")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["tension"] += 1
    return ["__tension__"]


def _r_damage_risk(world: World) -> list[str]:
    prop = world.get("prop")
    if prop.meters["damaged"] < THRESHOLD:
        return []
    sig = ("risk", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["risk"] += 1
    return ["__risk__"]


def _r_teamwork_giggles(world: World) -> list[str]:
    prop = world.get("prop")
    if prop.meters["fixed"] < THRESHOLD:
        return []
    if prop.meters["shared"] < THRESHOLD:
        return []
    sig = ("giggles", prop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["giggles"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.facts["giggles_ready"] = True
    return ["__giggles__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="conflict_tension", tag="social", apply=_r_conflict_tension),
    Rule(name="damage_risk", tag="physical", apply=_r_damage_risk),
    Rule(name="teamwork_giggles", tag="social", apply=_r_teamwork_giggles),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


def valid_fix(problem: ProblemCfg, fix: FixCfg) -> bool:
    return problem.damage in fix.repairs and fix.power >= problem.severity


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for sid in SETTINGS:
        for pid in PROPS:
            for prob_id, prob in PROBLEMS.items():
                for fix_id, fix in FIXES.items():
                    if not valid_fix(prob, fix):
                        continue
                    for share_id in SHARES:
                        combos.append((sid, pid, prob_id, fix_id, share_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    share = SHARES[params.share]
    score = fix.power + share.cooperation
    needed = problem.severity + 2
    return "big_laugh" if score >= needed else "gentle_laugh"


def explain_fix(problem: ProblemCfg, fix: FixCfg) -> str:
    if problem.damage not in fix.repairs:
        can = ", ".join(sorted(problem.damage for problem in PROBLEMS.values()))
        return (
            f"(No story: {fix.label} does not solve a {problem.label}. "
            f"Pick a fix that really repairs the problem.)"
        )
    if fix.power < problem.severity:
        return (
            f"(No story: {fix.label} is too weak for a {problem.label}. "
            f"The repair should honestly work before the children perform.)"
        )
    return "(No story: that fix does not suit this problem.)"


def predict_show(world: World, share: ShareCfg, fix: FixCfg) -> dict:
    sim = world.copy()
    prop = sim.get("prop")
    prop.meters["fixed"] = float(fix.power)
    prop.meters["shared"] = float(share.cooperation)
    propagate(sim, narrate=False)
    return {
        "giggles": sim.get("room").meters["giggles"],
        "ready": sim.facts["giggles_ready"],
    }


def introduce(world: World, kid_a: Entity, kid_b: Entity, prop_cfg: PropCfg) -> None:
    prop = world.get("prop")
    for kid in (kid_a, kid_b):
        kid.memes["joy"] += 1
        kid.memes["eagerness"] += 1
    world.say(
        f"{world.setting.opening} {kid_a.id} and {kid_b.id} were getting ready for "
        f"{world.setting.event} at {world.setting.place}."
    )
    world.say(
        f"They had made {prop_cfg.phrase}, and in the middle was a funny quote: "
        f'"{prop_cfg.quote_text}" {prop_cfg.detail}'
    )
    world.say(
        f"The children loved it so much that both of them reached for {prop.label} at the same time."
    )


def tug(world: World, kid_a: Entity, kid_b: Entity) -> None:
    prop = world.get("prop")
    kid_a.memes["want_prop"] += 1
    kid_b.memes["want_prop"] += 1
    kid_a.memes["conflict"] += 1
    kid_b.memes["conflict"] += 1
    prop.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I should hold it!" said {kid_a.id}. "No, I should!" said {kid_b.id}. '
        f"The prop wobbled between them like a startled pancake."
    )


def problem_hits(world: World, problem: ProblemCfg) -> None:
    prop = world.get("prop")
    prop.meters["damaged"] += float(problem.severity)
    world.facts["problem_seen"] = True
    propagate(world, narrate=False)
    world.say(problem.beat)
    world.say(problem.visible)


def helper_pauses(world: World, helper: Entity, kid_a: Entity, kid_b: Entity,
                  share: ShareCfg, fix: FixCfg) -> None:
    pred = predict_show(world, share, fix)
    world.facts["predicted_ready"] = pred["ready"]
    world.facts["predicted_giggles"] = pred["giggles"]
    world.say(
        f"{helper.label_word.capitalize()} stepped over before the little fight could grow any bigger."
    )
    world.say(
        f'"Two funny people with one funny prop need two calm ideas," {helper.pronoun()} said. '
        f'"First we fix it. Then we share it."'
    )


def think_rhyme(world: World, kid_a: Entity, kid_b: Entity) -> None:
    for kid in (kid_a, kid_b):
        kid.memes["thinking"] += 1
    world.say(
        f"{kid_a.id} blinked. {kid_b.id} blinked back. Then they made up a rhyme "
        f"right there: \"Share and care, both stand there!\""
    )


def repair(world: World, fix: FixCfg) -> None:
    prop = world.get("prop")
    prop.meters["fixed"] = float(fix.power)
    prop.meters["damaged"] = 0.0
    world.facts["fixed"] = True
    propagate(world, narrate=False)
    world.say(fix.text)


def share_plan(world: World, kid_a: Entity, kid_b: Entity, share: ShareCfg) -> None:
    prop = world.get("prop")
    prop.meters["shared"] = float(share.cooperation)
    kid_a.memes["conflict"] = 0.0
    kid_b.memes["conflict"] = 0.0
    kid_a.memes["generosity"] += 1
    kid_b.memes["generosity"] += 1
    world.facts["shared"] = True
    propagate(world, narrate=False)
    world.say(share.setup_line.format(a=kid_a.id, b=kid_b.id))


def perform(world: World, kid_a: Entity, kid_b: Entity, prop_cfg: PropCfg,
            share: ShareCfg, outcome: str) -> None:
    room = world.get("room")
    for kid in (kid_a, kid_b):
        kid.memes["relief"] += 1
    world.say(
        share.perform_line.format(a=kid_a.id, b=kid_b.id, quote=prop_cfg.quote_text)
    )
    if outcome == "big_laugh":
        room.meters["big_laugh"] += 1
        world.say(
            f"{world.setting.audience.capitalize()} laughed so hard that one chair squeaked, "
            f"someone snorted, and even {kid_a.id} and {kid_b.id} had to stop and giggle too."
        )
    else:
        room.meters["gentle_laugh"] += 1
        world.say(
            f"{world.setting.audience.capitalize()} gave a warm, wiggly laugh, and the room felt easy again."
        )
    world.say(
        f"In the end, {world.setting.ending_image}, and nobody cared who got the center spot anymore."
    )


@dataclass
class StoryParams:
    setting: str
    prop: str
    problem: str
    fix: str
    share: str
    name_a: str
    gender_a: str
    name_b: str
    gender_b: str
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


def tell(setting: Setting, prop_cfg: PropCfg, problem: ProblemCfg, fix: FixCfg,
         share: ShareCfg, name_a: str = "Mia", gender_a: str = "girl",
         name_b: str = "Leo", gender_b: str = "boy") -> World:
    world = World(setting)
    room = world.add(Entity(id="room", type="room", label=setting.place))
    room.meters["tension"] = 0.0
    room.meters["risk"] = 0.0
    room.meters["giggles"] = 0.0
    room.meters["big_laugh"] = 0.0
    room.meters["gentle_laugh"] = 0.0

    kid_a = world.add(Entity(
        id=name_a,
        kind="character",
        type=gender_a,
        role="kid_a",
        traits=["silly", "eager"],
    ))
    kid_b = world.add(Entity(
        id=name_b,
        kind="character",
        type=gender_b,
        role="kid_b",
        traits=["silly", "bright"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=setting.helper_type,
        role="helper",
        label="the helper",
    ))
    prop = world.add(Entity(
        id="prop",
        type="prop",
        label=prop_cfg.label,
        phrase=prop_cfg.phrase,
        tags=set(prop_cfg.tags),
    ))
    prop.meters["wobble"] = 0.0
    prop.meters["damaged"] = 0.0
    prop.meters["fixed"] = 0.0
    prop.meters["shared"] = 0.0

    for kid in (kid_a, kid_b):
        kid.memes["joy"] = 0.0
        kid.memes["eagerness"] = 0.0
        kid.memes["want_prop"] = 0.0
        kid.memes["conflict"] = 0.0
        kid.memes["thinking"] = 0.0
        kid.memes["generosity"] = 0.0
        kid.memes["pride"] = 0.0
        kid.memes["relief"] = 0.0

    introduce(world, kid_a, kid_b, prop_cfg)

    world.para()
    tug(world, kid_a, kid_b)
    problem_hits(world, problem)

    world.para()
    helper_pauses(world, helper, kid_a, kid_b, share, fix)
    think_rhyme(world, kid_a, kid_b)
    repair(world, fix)
    share_plan(world, kid_a, kid_b, share)

    world.para()
    result = outcome_of(StoryParams(
        setting=setting.id,
        prop=prop_cfg.id,
        problem=problem.id,
        fix=fix.id,
        share=share.id,
        name_a=name_a,
        gender_a=gender_a,
        name_b=name_b,
        gender_b=gender_b,
        seed=None,
    ))
    perform(world, kid_a, kid_b, prop_cfg, share, result)

    world.facts.update(
        setting=setting,
        prop_cfg=prop_cfg,
        problem=problem,
        fix=fix,
        share_cfg=share,
        helper=helper,
        kid_a=kid_a,
        kid_b=kid_b,
        outcome=result,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom rug",
        event="the Friday Giggle Show",
        audience="their classmates",
        helper_type="teacher",
        opening="On Friday morning, the room still smelled a little like crayons",
        ending_image="the two children stood shoulder to shoulder under the bright paper stars",
        tags={"school"},
    ),
    "kitchen": Setting(
        id="kitchen",
        place="the sunny kitchen",
        event="family joke time",
        audience="the family by the table",
        helper_type="aunt",
        opening="After lunch, when spoons still clinked in bowls",
        ending_image="the prop leaned against the fruit bowl while the children bowed together",
        tags={"home"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        event="the tiny sidewalk comedy parade",
        audience="the neighbors by the fence",
        helper_type="grandpa",
        opening="On a breezy afternoon, when the porch boards gave little creaks",
        ending_image="the children waved at the fence with the prop balanced happily between them",
        tags={"outside"},
    ),
}

PROPS = {
    "speech_bubble": PropCfg(
        id="speech_bubble",
        label="the speech-bubble sign",
        phrase="a giant cardboard speech bubble",
        quote_text="I told my sock a joke, and now it wants a bow tie!",
        detail="A curly blue border made it look as if the sign itself had just popped up to talk.",
        tags={"quote", "cardboard"},
    ),
    "mustache_paddle": PropCfg(
        id="mustache_paddle",
        label="the mustache paddle",
        phrase="a paddle with a huge paper mustache and a quote underneath",
        quote_text="This banana is my lawyer!",
        detail="The mustache was so swoopy that it made both children laugh every time they looked at it.",
        tags={"quote", "mustache"},
    ),
    "giggle_board": PropCfg(
        id="giggle_board",
        label="the giggle board",
        phrase="a bright joke board on a stick",
        quote_text="My hat says moo only on Tuesdays!",
        detail="Three crooked stars danced around the words as if they were trying to hear the joke too.",
        tags={"quote", "poster"},
    ),
}

PROBLEMS = {
    "tear": ProblemCfg(
        id="tear",
        label="torn edge",
        damage="tear",
        beat="Then came a small rrriiip. One side of the prop tore where both little hands had tugged.",
        visible="The funny quote drooped to one side, and suddenly the joke looked tired instead of silly.",
        severity=2,
        tags={"tear"},
    ),
    "smudge": ProblemCfg(
        id="smudge",
        label="smudged letters",
        damage="smudge",
        beat="A thumb slid across the fresh words. The black letters blurred into a wobbly fog.",
        visible="Now the quote looked as if it were mumbling into a pillow, and neither child could read it cleanly.",
        severity=1,
        tags={"marker", "smudge"},
    ),
    "droop": ProblemCfg(
        id="droop",
        label="droopy stick",
        damage="droop",
        beat="The stick under the prop gave a tired bend, and the whole thing sagged like a sleepy noodle.",
        visible="The sign kept tipping downward until the quote was almost talking to the floor.",
        severity=2,
        tags={"stick", "droop"},
    ),
}

FIXES = {
    "tape_patch": FixCfg(
        id="tape_patch",
        label="a tape patch",
        repairs={"tear", "droop"},
        power=2,
        text="They smoothed the cardboard flat and added a neat tape patch. The prop straightened up at once, as if it had remembered an important joke.",
        qa_text="They used tape to patch the torn or drooping part so the prop could stay up again.",
        tags={"tape"},
    ),
    "bold_redraw": FixCfg(
        id="bold_redraw",
        label="a bold redraw",
        repairs={"smudge"},
        power=2,
        text="They took a thick crayon and traced the words again, bigger and darker than before. The quote came back looking proud and impossible to ignore.",
        qa_text="They redrew the blurred words in thick lines so everyone could read the quote again.",
        tags={"crayon", "quote"},
    ),
    "brace_and_tape": FixCfg(
        id="brace_and_tape",
        label="a brace and tape fix",
        repairs={"tear", "droop"},
        power=3,
        text="They taped a clean craft stick across the back like a tiny brace. After that, the prop stood tall and steady, almost puffing out its cardboard chest.",
        qa_text="They taped a stiff support on the back so the prop would not bend or tear again.",
        tags={"tape", "stick"},
    ),
}

SHARES = {
    "turns": ShareCfg(
        id="turns",
        label="taking turns",
        cooperation=1,
        setup_line="{a} and {b} agreed that one would hold the prop first and the other would hold it second. Suddenly the problem felt smaller, because the spotlight had room to move.",
        perform_line="{a} held the prop first while {b} said the rhyme, and then they switched. Together they shouted, \"Share and care, both stand there!\" under the quote, \"{quote}\"",
        qa_text="They took turns so each child got a fair chance to hold the prop.",
        tags={"sharing", "turns"},
    ),
    "split_jobs": ShareCfg(
        id="split_jobs",
        label="splitting jobs",
        cooperation=2,
        setup_line="{a} chose to hold the prop while {b} pointed at the words and delivered the silliest face in the room. Each child had a job, so neither had to snatch.",
        perform_line="{a} held the prop high while {b} boomed the rhyme, \"Share and care, both stand there!\" Then {b} pointed grandly at the quote, \"{quote}\"",
        qa_text="They shared by giving each child a different job, so both were important at the same time.",
        tags={"sharing", "jobs"},
    ),
    "both_hands": ShareCfg(
        id="both_hands",
        label="holding it together",
        cooperation=3,
        setup_line="{a} and {b} each took one side and decided to carry the prop together. Once both hands were helping, the tugging turned into teamwork.",
        perform_line="With one hand from {a} and one hand from {b}, the prop floated between them while they chanted, \"Share and care, both stand there!\" Then they grinned at the quote, \"{quote}\"",
        qa_text="They solved the sharing problem by holding the prop together instead of fighting over it.",
        tags={"sharing", "together"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Ruby", "Pia"]
BOY_NAMES = ["Leo", "Max", "Ben", "Sam", "Theo", "Finn", "Eli", "Jack"]


KNOWLEDGE = {
    "quote": [
        (
            "What is a quote?",
            "A quote is the exact words that someone says or that you choose to copy and show. You often put it in quotation marks so people know those are the special words.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like care and share. Rhymes are fun to say because they bounce in your ears.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting another person use something too instead of keeping it all for yourself. It helps everyone feel included.",
        )
    ],
    "tape": [
        (
            "What does tape do?",
            "Tape helps hold things together. It can patch paper or cardboard so they do not flop apart.",
        )
    ],
    "crayon": [
        (
            "Why is a thick crayon useful on a sign?",
            "A thick crayon makes dark, easy-to-see lines. That helps people read words from farther away.",
        )
    ],
    "cardboard": [
        (
            "What is cardboard?",
            "Cardboard is thick, stiff paper. People use it for boxes and signs because it can stand up better than thin paper.",
        )
    ],
}
KNOWLEDGE_ORDER = ["quote", "rhyme", "sharing", "tape", "crayon", "cardboard"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["kid_a"]
    b = f["kid_b"]
    setting = f["setting"]
    prop = f["prop_cfg"]
    problem = f["problem"]
    share = f["share_cfg"]
    return [
        f'Write a short comedy story for a 3-to-5-year-old that includes the word "quote" and ends with sharing.',
        f"Tell a funny story where {a.id} and {b.id} prepare a silly act for {setting.event}, hit a {problem.label} problem, and solve it with a rhyme and teamwork.",
        f"Write a gentle story about two children who both want {prop.label}, learn to share by {share.label}, and make the audience laugh together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["kid_a"]
    b = f["kid_b"]
    setting = f["setting"]
    prop = f["prop_cfg"]
    problem = f["problem"]
    fix = f["fix"]
    share = f["share_cfg"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children getting ready for {setting.event}. {helper.label_word.capitalize()} also helps them when the prop goes wrong.",
        ),
        (
            "What made the prop funny?",
            f"The prop had a silly quote on it: \"{prop.quote_text}\". That line was funny because it made an ordinary thing sound delightfully ridiculous.",
        ),
        (
            "What problem happened?",
            f"The children both grabbed for the same prop, and that led to a {problem.label}. The problem happened because wanting the same thing at the same time made them tug instead of share.",
        ),
        (
            f"How did {helper.label_word} help?",
            f"{helper.label_word.capitalize()} told them to calm down, fix the prop, and share it. That gave them a simple plan, so the little fight could turn into problem solving.",
        ),
        (
            "What rhyme did the children make up?",
            "They said, \"Share and care, both stand there!\" The rhyme helped them remember to work together instead of pulling against each other.",
        ),
        (
            "How did they fix the problem?",
            f"{fix.qa_text} That made the prop ready for the show again instead of messy or droopy.",
        ),
        (
            "How did they share?",
            f"{share.qa_text} Because both children got a fair part, the prop stopped feeling like something to fight over.",
        ),
    ]
    if outcome == "big_laugh":
        qa.append(
            (
                "How did the story end?",
                f"It ended with a big laugh from {setting.audience}. The children performed together, so the same prop that caused trouble became part of the joke.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with a warm laugh and two proud smiles. Even a small sharing plan worked because the children solved the problem before performing.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"quote", "rhyme", "sharing", "cardboard"}
    problem = world.facts["problem"]
    fix = world.facts["fix"]
    if "tape" in fix.tags:
        tags.add("tape")
    if "crayon" in fix.tags:
        tags.add("crayon")
    if "marker" in problem.tags:
        tags.add("crayon")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: { {k: v for k, v in world.facts.items() if k in {'shared', 'fixed', 'giggles_ready', 'problem_seen', 'outcome'}} }")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="classroom",
        prop="speech_bubble",
        problem="tear",
        fix="brace_and_tape",
        share="both_hands",
        name_a="Mia",
        gender_a="girl",
        name_b="Leo",
        gender_b="boy",
        seed=101,
    ),
    StoryParams(
        setting="kitchen",
        prop="mustache_paddle",
        problem="smudge",
        fix="bold_redraw",
        share="split_jobs",
        name_a="Ava",
        gender_a="girl",
        name_b="Max",
        gender_b="boy",
        seed=102,
    ),
    StoryParams(
        setting="porch",
        prop="giggle_board",
        problem="droop",
        fix="tape_patch",
        share="turns",
        name_a="Nora",
        gender_a="girl",
        name_b="Finn",
        gender_b="boy",
        seed=103,
    ),
    StoryParams(
        setting="classroom",
        prop="mustache_paddle",
        problem="droop",
        fix="brace_and_tape",
        share="split_jobs",
        name_a="Ruby",
        gender_a="girl",
        name_b="Sam",
        gender_b="boy",
        seed=104,
    ),
    StoryParams(
        setting="kitchen",
        prop="speech_bubble",
        problem="tear",
        fix="tape_patch",
        share="both_hands",
        name_a="Ella",
        gender_a="girl",
        name_b="Theo",
        gender_b="boy",
        seed=105,
    ),
]


ASP_RULES = r"""
valid_fix(P, F) :- problem(P), fix(F), repairs(F, D), damage(P, D), power(F, PW), severity(P, SV), PW >= SV.
valid(S, Pr, P, F, Sh) :- setting(S), prop(Pr), problem(P), fix(F), share(Sh), valid_fix(P, F).

score(F, Sh, PW + C) :- chosen_fix(F), chosen_share(Sh), power(F, PW), cooperation(Sh, C).
need(P, SV + 2) :- chosen_problem(P), severity(P, SV).
outcome(big_laugh) :- score(F, Sh, S), need(P, N), S >= N.
outcome(gentle_laugh) :- score(F, Sh, S), need(P, N), S < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    for prob_id, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", prob_id))
        lines.append(asp.fact("damage", prob_id, prob.damage))
        lines.append(asp.fact("severity", prob_id, prob.severity))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("power", fix_id, fix.power))
        for rep in sorted(fix.repairs):
            lines.append(asp.fact("repairs", fix_id, rep))
    for share_id, share in SHARES.items():
        lines.append(asp.fact("share", share_id))
        lines.append(asp.fact("cooperation", share_id, share.cooperation))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_share", params.share),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        _ = format_qa(smoke)
        _ = smoke.to_json()
        print("OK: smoke test generation/QA/JSON succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Funny prop story world: a quote, a small problem, a rhyme, and sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--name-a")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix:
        problem = PROBLEMS[args.problem]
        fix = FIXES[args.fix]
        if not valid_fix(problem, fix):
            raise StoryError(explain_fix(problem, fix))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.prop is None or c[1] == args.prop)
        and (args.problem is None or c[2] == args.problem)
        and (args.fix is None or c[3] == args.fix)
        and (args.share is None or c[4] == args.share)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, prop_id, problem_id, fix_id, share_id = rng.choice(sorted(combos))
    gender_a = args.gender_a or rng.choice(["girl", "boy"])
    gender_b = args.gender_b or rng.choice(["girl", "boy"])
    name_a = args.name_a or pick_name(rng, gender_a)
    name_b = args.name_b or pick_name(rng, gender_b, avoid=name_a)
    return StoryParams(
        setting=setting_id,
        prop=prop_id,
        problem=problem_id,
        fix=fix_id,
        share=share_id,
        name_a=name_a,
        gender_a=gender_a,
        name_b=name_b,
        gender_b=gender_b,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop: {params.prop})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.share not in SHARES:
        raise StoryError(f"(Unknown share plan: {params.share})")

    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    if not valid_fix(problem, fix):
        raise StoryError(explain_fix(problem, fix))

    world = tell(
        setting=SETTINGS[params.setting],
        prop_cfg=PROPS[params.prop],
        problem=problem,
        fix=fix,
        share=SHARES[params.share],
        name_a=params.name_a,
        gender_a=params.gender_a,
        name_b=params.name_b,
        gender_b=params.gender_b,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, prop, problem, fix, share) combos:\n")
        for item in combos:
            print("  " + "  ".join(f"{part:14}" for part in item))
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
            header = (
                f"### {p.name_a} & {p.name_b}: {p.prop} / {p.problem} / "
                f"{p.fix} / {p.share} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
