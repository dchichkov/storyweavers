#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/foot_baton_inner_monologue_surprise_transformation_nursery.py
=========================================================================================

A standalone storyworld for a nursery-rhyme-like tale about a child leading a
toy parade with a baton. One toy has trouble with a foot, the child thinks the
problem through in an inner monologue, a surprise bit of small magic transforms
the baton into the right kind of helper, and the parade ends in a new, happier
shape.

The world is deliberately small and constraint-checked:
- a setting provides one kind of surprise source (moonbeam, sunbeam, or raindrop)
- a foot problem needs a compatible surprise source
- a baton has one practical gift (chime, brush, or wrap)
- only compatible (setting, problem, baton) triples become stories

Run it
------
python storyworlds/worlds/gpt-5.4/foot_baton_inner_monologue_surprise_transformation_nursery.py
python storyworlds/worlds/gpt-5.4/foot_baton_inner_monologue_surprise_transformation_nursery.py --all
python storyworlds/worlds/gpt-5.4/foot_baton_inner_monologue_surprise_transformation_nursery.py --seed 7 --qa
python storyworlds/worlds/gpt-5.4/foot_baton_inner_monologue_surprise_transformation_nursery.py --asp
python storyworlds/worlds/gpt-5.4/foot_baton_inner_monologue_surprise_transformation_nursery.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    floor: str
    source: str
    glow: str
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
class FootProblem:
    id: str
    adjective: str
    cause: str
    warning: str
    need: str
    transform_label: str
    transform_line: str
    fix_line: str
    close_line: str
    allowed_sources: set[str] = field(default_factory=set)
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
class BatonKind:
    id: str
    label: str
    phrase: str
    gift: str
    sway: str
    transformed_to: str
    use_line: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {"setting": setting}

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    toy = world.entities.get("toy")
    child = world.entities.get("child")
    if toy is None or child is None:
        return out
    if toy.meters["trouble"] < THRESHOLD:
        return out
    if child.meters["tempo"] < THRESHOLD:
        return out
    if toy.attrs.get("helped"):
        return out
    sig = ("wobble", toy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy.meters["wobble"] += 1
    toy.memes["fear"] += 1
    child.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_steady(world: World) -> list[str]:
    out: list[str] = []
    toy = world.entities.get("toy")
    baton = world.entities.get("baton")
    child = world.entities.get("child")
    if toy is None or baton is None or child is None:
        return out
    if baton.attrs.get("gift") != toy.attrs.get("need"):
        return out
    if baton.meters["transformed"] < THRESHOLD:
        return out
    if child.meters["gentle_tempo"] < THRESHOLD:
        return out
    sig = ("steady", toy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy.attrs["helped"] = True
    toy.meters["trouble"] = 0.0
    toy.meters["wobble"] = 0.0
    toy.memes["fear"] = 0.0
    toy.memes["joy"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    out.append("__steady__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="steady", tag="physical", apply=_r_steady),
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


SETTINGS = {
    "nursery_moon": Setting(
        id="nursery_moon",
        place="the nursery",
        opening="In the nursery, where the quilt made little hills and the blocks made little towers,",
        floor="the moonlit rug",
        source="moonbeam",
        glow="A moonbeam slipped through the curtain like a silver ribbon.",
        tags={"moonbeam", "nursery"},
    ),
    "window_sun": Setting(
        id="window_sun",
        place="the window nook",
        opening="By the window nook, where picture books leaned and the rocking horse waited still,",
        floor="the warm floorboards",
        source="sunbeam",
        glow="A sunbeam slid across the floor like a stripe of honey.",
        tags={"sunbeam", "nursery"},
    ),
    "rain_sill": Setting(
        id="rain_sill",
        place="the rain-sill corner",
        opening="Near the rain-sill corner, where toy cups stood in a row and the pane hummed softly,",
        floor="the shining boards",
        source="raindrop",
        glow="A bright raindrop bounced from the sill and winked upon the floor.",
        tags={"raindrop", "nursery"},
    ),
}

PROBLEMS = {
    "sleepy_foot": FootProblem(
        id="sleepy_foot",
        adjective="sleepy",
        cause="one little foot drooped as if it wanted a nap",
        warning="If I beat too quick, that drowsy foot will drag, and my small friend will topple.",
        need="chime",
        transform_label="a chiming baton",
        transform_line="At once the baton grew a row of tiny bells and turned into a chiming baton.",
        fix_line="Each sweet tinkle lifted the drooping foot, and the marching steps woke up in time.",
        close_line="Soon the toy stepped bright and brisk, with both feet keeping time.",
        allowed_sources={"moonbeam", "sunbeam"},
        tags={"sleep", "foot"},
    ),
    "muddy_foot": FootProblem(
        id="muddy_foot",
        adjective="muddy",
        cause="one little foot was dabbed with potting soil from the flower box",
        warning="If I beat too smartly, that sticky foot will cling and twist, and my small friend will tumble.",
        need="brush",
        transform_label="a brushing baton",
        transform_line="At once the baton sprouted silky ribbons and turned into a brushing baton.",
        fix_line="The ribbons whisked the sticky foot clean, and the marching steps could slide along again.",
        close_line="Soon the toy stepped neat and nimble, with a clean foot tapping the tune.",
        allowed_sources={"moonbeam", "raindrop"},
        tags={"mud", "foot"},
    ),
    "cold_foot": FootProblem(
        id="cold_foot",
        adjective="cold",
        cause="one little foot shivered from the draft under the curtain",
        warning="If I beat too loud, that chilly foot will tuck away, and my small friend will stop.",
        need="wrap",
        transform_label="a woolly baton",
        transform_line="At once the baton puffed into a soft starry tassel and turned into a woolly baton.",
        fix_line="The soft tassel wrapped the chilly foot warm, and the marching steps came back with a bounce.",
        close_line="Soon the toy stepped cozy and bold, with a warmed foot patting the rug.",
        allowed_sources={"moonbeam", "sunbeam"},
        tags={"cold", "foot"},
    ),
    "splinter_foot": FootProblem(
        id="splinter_foot",
        adjective="splintery",
        cause="one little foot had a splinter in it",
        warning="If I beat too quick, the sore foot will hurt.",
        need="none",
        transform_label="nothing useful",
        transform_line="",
        fix_line="",
        close_line="",
        allowed_sources=set(),
        tags={"foot"},
    ),
}

BATONS = {
    "bell_baton": BatonKind(
        id="bell_baton",
        label="bell baton",
        phrase="a slim bell baton",
        gift="chime",
        sway="made a tidy ting at the tip",
        transformed_to="chiming baton",
        use_line="Pip tapped lightly and let the silver bells ring the marching count.",
        tags={"bell", "sound"},
    ),
    "ribbon_baton": BatonKind(
        id="ribbon_baton",
        label="ribbon baton",
        phrase="a fluttering ribbon baton",
        gift="brush",
        sway="trailed a soft ribbon tail",
        transformed_to="brushing baton",
        use_line="Pip circled the ribbons low and let them sweep the marching path.",
        tags={"ribbon", "brush"},
    ),
    "tassel_baton": BatonKind(
        id="tassel_baton",
        label="tassel baton",
        phrase="a little tassel baton",
        gift="wrap",
        sway="bobbed a velvet tuft at the end",
        transformed_to="woolly baton",
        use_line="Pip dipped the tassel close and let it cuddle the marching beat.",
        tags={"tassel", "warmth"},
    ),
    "painted_baton": BatonKind(
        id="painted_baton",
        label="painted baton",
        phrase="a painted wooden baton",
        gift="none",
        sway="shone with neat red stripes",
        transformed_to="plain baton",
        use_line="Pip waved the painted stick, but it had no special trick for a sore foot.",
        tags={"plain"},
    ),
}

TOYS = {
    "duck": {"label": "duck", "phrase": "a yellow duck on wheels", "type": "toy"},
    "rabbit": {"label": "rabbit", "phrase": "a cotton rabbit with bright button eyes", "type": "toy"},
    "drummer": {"label": "drummer", "phrase": "a tin drummer with a round blue coat", "type": "toy"},
}

CHILD_NAMES = ["Pip", "Nell", "Mimi", "Toby", "June", "Kit"]
TOY_ORDER = ["duck", "rabbit", "drummer"]


def needs_match(problem: FootProblem, baton: BatonKind) -> bool:
    return problem.need != "none" and baton.gift == problem.need


def valid_combo(setting: Setting, problem: FootProblem, baton: BatonKind) -> bool:
    return setting.source in problem.allowed_sources and needs_match(problem, baton)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for bid, baton in BATONS.items():
                if valid_combo(setting, problem, baton):
                    combos.append((sid, pid, bid))
    return combos


@dataclass
class StoryParams:
    setting: str
    problem: str
    baton: str
    toy: str
    child_name: str
    child_gender: str
    parent: str
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


def introduce(world: World, child: Entity, toy: Entity, baton: Entity, setting: Setting, baton_cfg: BatonKind) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{setting.opening} {child.id} set {toy.phrase} in a tidy line and took up {baton_cfg.phrase}."
    )
    world.say(
        f'"Tap and twirl, do not be late; march, my toys, in nursery state," thought {child.id}, '
        f"while the {baton_cfg.label} {baton_cfg.sway}."
    )


def trouble_appears(world: World, child: Entity, toy: Entity, problem: FootProblem, setting: Setting) -> None:
    toy.meters["trouble"] = 1.0
    toy.attrs["need"] = problem.need
    toy.attrs["helped"] = False
    child.memes["care"] += 1
    world.say(
        f"But when the little parade reached {setting.floor}, {toy.label}'s {problem.cause}."
    )
    world.say(
        f"{child.id} saw it and held still, because a parade must mind every foot."
    )


def predict_wobble(world: World, child: Entity, problem: FootProblem) -> None:
    pred = predict_fall(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    child.memes["thoughtful"] += 1
    worry = "wobble" if pred["wobble"] else "go wrong"
    world.say(
        f'"Oh dear," thought {child.id}. "{problem.warning} I must not make a grand parade if it will only {worry}."'
    )


def try_and_wobble(world: World, child: Entity, toy: Entity) -> None:
    child.meters["tempo"] = 1.0
    propagate(world, narrate=False)
    if toy.meters["wobble"] >= THRESHOLD:
        world.say(
            f"Still, {child.id} gave one quick tap; clip, clap, went the line, and {toy.label} made a tiny bobbling hop."
        )
        world.say(
            f'"No, no," thought {child.id}. "A clever leader listens before leading."'
        )


def surprise_transform(world: World, child: Entity, baton: Entity, setting: Setting, problem: FootProblem) -> None:
    baton.meters["transformed"] = 1.0
    baton.attrs["form"] = problem.transform_label
    world.facts["surprise_source"] = setting.source
    world.say(setting.glow)
    world.say(
        f"It kissed the baton in {child.id}'s hand, and {problem.transform_line}"
    )


def gentle_fix(world: World, child: Entity, toy: Entity, baton: Entity, baton_cfg: BatonKind, problem: FootProblem) -> None:
    child.meters["tempo"] = 0.0
    child.meters["gentle_tempo"] = 1.0
    baton.attrs["gift"] = baton_cfg.gift
    propagate(world, narrate=False)
    world.say(baton_cfg.use_line)
    world.say(problem.fix_line)
    if toy.attrs.get("helped"):
        world.say(problem.close_line)


def ending(world: World, child: Entity, toy: Entity, setting: Setting) -> None:
    world.say(
        f"Then round they went on {setting.floor} -- tip for the child, tap for the toy, soft went every foot with joy."
    )
    world.say(
        f"And {child.id} laughed to see the little march made new: not loud and proud, but kind and true."
    )


def predict_fall(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    toy = sim.get("toy")
    child.meters["tempo"] = 1.0
    propagate(sim, narrate=False)
    return {"wobble": toy.meters["wobble"] >= THRESHOLD}


def tell(setting: Setting, problem: FootProblem, baton_cfg: BatonKind, toy_key: str,
         child_name: str = "Pip", child_gender: str = "girl", parent_type: str = "mother") -> World:
    toy_cfg = TOYS[toy_key]
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
    ))
    toy = world.add(Entity(
        id="toy",
        kind="thing",
        type=toy_cfg["type"],
        label=toy_cfg["label"],
        phrase=toy_cfg["phrase"],
        role="toy",
        attrs={"need": problem.need, "helped": False},
    ))
    baton = world.add(Entity(
        id="baton",
        kind="thing",
        type="baton",
        label=baton_cfg.label,
        phrase=baton_cfg.phrase,
        role="tool",
        attrs={"gift": baton_cfg.gift, "form": baton_cfg.label},
    ))
    world.facts.update(
        child=child,
        parent=parent,
        toy=toy,
        toy_key=toy_key,
        problem=problem,
        baton_cfg=baton_cfg,
        setting=setting,
    )

    introduce(world, child, toy, baton, setting, baton_cfg)
    world.para()
    trouble_appears(world, child, toy, problem, setting)
    predict_wobble(world, child, problem)
    try_and_wobble(world, child, toy)
    world.para()
    surprise_transform(world, child, baton, setting, problem)
    gentle_fix(world, child, toy, baton, baton_cfg, problem)
    ending(world, child, toy, setting)

    world.facts.update(
        transformed=baton.meters["transformed"] >= THRESHOLD,
        helped=toy.attrs.get("helped", False),
        wobble_seen=toy.meters["wobble"] >= THRESHOLD or bool(world.facts.get("predicted_wobble")),
        final_form=baton.attrs.get("form", baton_cfg.label),
    )
    return world


def explain_rejection(setting: Setting, problem: FootProblem, baton: BatonKind) -> str:
    if setting.source not in problem.allowed_sources:
        allowed = ", ".join(sorted(problem.allowed_sources)) or "no known surprise source"
        return (
            f"(No story: {setting.source} does not suit a {problem.adjective} foot here. "
            f"This problem wants {allowed}.)"
        )
    if problem.need == "none" or baton.gift != problem.need:
        return (
            f"(No story: a {problem.adjective} foot needs a baton that can {problem.need}, "
            f"but {baton.label} can only {baton.gift}. Pick a matching baton.)"
        )
    return "(No story: this combination does not make a sensible little rhyme.)"


def _need_key(value: str) -> int:
    return {"chime": 0, "brush": 1, "wrap": 2, "none": 3}.get(value, 99)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    problem = f["problem"]
    toy = f["toy"]
    return [
        f'Write a nursery-rhyme-style story that includes the words "foot" and "baton", and has a child thinking to {child.pronoun("object")}self before a small magical surprise.',
        f"Tell a gentle toy-parade story where {child.id} notices that {toy.label} has a {problem.adjective} foot, worries quietly, and then sees the baton transform.",
        f"Write a short rhyming story for a young child where kindness changes the rhythm of a parade and solves a foot problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    toy = f["toy"]
    problem = f["problem"]
    setting = f["setting"]
    baton_cfg = f["baton_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child leading a toy parade, and a little {toy.label} who had trouble with one foot. "
            f"The story stays in {setting.place}, where the parade changes from hurried to gentle."
        ),
        (
            f"What was wrong with the {toy.label}?",
            f"The {toy.label} had a {problem.adjective} foot: {problem.cause}. "
            f"That is why {child.id} stopped to think instead of hurrying the march."
        ),
        (
            f"What did {child.id} think in the middle of the story?",
            f"{child.id} quietly thought that a fast beat would make the little parade go wrong. "
            f"{problem.warning} The thought shows {child.id} was paying attention to the toy instead of only to the music."
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                "What was the surprise?",
                f"A {f['surprise_source']} touched the baton, and it changed into {f['final_form']}. "
                f"The surprise mattered because the new baton could give exactly the help the toy's foot needed."
            )
        )
    if f.get("helped"):
        qa.append(
            (
                f"How did the problem get solved?",
                f"{child.id} changed to a gentle marching beat and used the transformed baton to help the {toy.label}. "
                f"{problem.fix_line} After that, the parade could go on kindly instead of quickly."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the parade moving softly together, every foot in time. "
                f"The ending image proves the transformation changed more than the baton: it changed the whole way the march was led."
            )
        )
    return qa


KNOWLEDGE = {
    "baton": [
        (
            "What is a baton?",
            "A baton is a small stick or wand a leader can wave to show the beat. It helps everyone know when to move together."
        )
    ],
    "foot": [
        (
            "Why is it hard to march if one foot hurts or feels wrong?",
            "Marching needs balance and rhythm from both feet. If one foot is sore, cold, or sticky, it is much easier to wobble or stop."
        )
    ],
    "moonbeam": [
        (
            "What is a moonbeam?",
            "A moonbeam is the soft light that seems to shine down from the moon. In stories, it often feels gentle and magical."
        )
    ],
    "sunbeam": [
        (
            "What is a sunbeam?",
            "A sunbeam is a bright stripe of light from the sun. It can make a room feel warm and lively."
        )
    ],
    "raindrop": [
        (
            "What is a raindrop?",
            "A raindrop is one small drop of rain. When light catches it, it can sparkle like a tiny jewel."
        )
    ],
    "sleep": [
        (
            "Why do sleepy feet move slowly?",
            "When someone feels sleepy, their whole body wants to rest. That can make their steps drag and feel heavy."
        )
    ],
    "mud": [
        (
            "Why does mud make walking harder?",
            "Mud sticks and pulls at your steps. A muddy foot can feel heavy and slippery at the same time."
        )
    ],
    "cold": [
        (
            "Why do cold feet want to curl up?",
            "Cold can make toes and feet feel stiff and uncomfortable. Warmth helps them relax and move again."
        )
    ],
}
KNOWLEDGE_ORDER = ["baton", "foot", "moonbeam", "sunbeam", "raindrop", "sleep", "mud", "cold"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"baton", "foot"}
    tags |= set(world.facts["setting"].tags)
    tags |= set(world.facts["problem"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible_source(S, P) :- setting_source(S, Src), problem_source(P, Src).
matching_baton(P, B) :- problem_need(P, Need), baton_gift(B, Need), Need != "none".
valid(S, P, B) :- setting(S), problem(P), baton(B), compatible_source(S, P), matching_baton(P, B).

wobble :- chosen_problem(P), problem_need(P, Need), Need != "none", chosen_tempo(fast).
transformed :- chosen_setting(S), chosen_problem(P), chosen_baton(B), valid(S, P, B).
helped :- transformed, chosen_problem(P), chosen_baton(B), problem_need(P, Need), baton_gift(B, Need), chosen_tempo(gentle).

outcome(wobble_then_helped) :- wobble, helped.
outcome(bad_choice) :- not helped.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_source", sid, setting.source))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_need", pid, problem.need))
        for src in sorted(problem.allowed_sources):
            lines.append(asp.fact("problem_source", pid, src))
    for bid, baton in BATONS.items():
        lines.append(asp.fact("baton", bid))
        lines.append(asp.fact("baton_gift", bid, baton.gift))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_baton", params.baton),
            asp.fact("chosen_tempo", "fast"),
            asp.fact("chosen_tempo", "gentle"),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="nursery_moon",
        problem="sleepy_foot",
        baton="bell_baton",
        toy="duck",
        child_name="Pip",
        child_gender="girl",
        parent="mother",
        seed=101,
    ),
    StoryParams(
        setting="rain_sill",
        problem="muddy_foot",
        baton="ribbon_baton",
        toy="rabbit",
        child_name="Nell",
        child_gender="girl",
        parent="father",
        seed=102,
    ),
    StoryParams(
        setting="window_sun",
        problem="cold_foot",
        baton="tassel_baton",
        toy="drummer",
        child_name="Toby",
        child_gender="boy",
        parent="mother",
        seed=103,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a child, a foot problem, a baton, and a small surprise transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--baton", choices=BATONS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.problem and args.baton:
        if not valid_combo(SETTINGS[args.setting], PROBLEMS[args.problem], BATONS[args.baton]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], PROBLEMS[args.problem], BATONS[args.baton]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.problem is None or c[1] == args.problem)
        and (args.baton is None or c[2] == args.baton)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, problem, baton = rng.choice(sorted(combos))
    toy = args.toy or rng.choice(TOY_ORDER)
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        problem=problem,
        baton=baton,
        toy=toy,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.baton not in BATONS:
        raise StoryError(f"(Unknown baton: {params.baton})")
    if params.toy not in TOYS:
        raise StoryError(f"(Unknown toy: {params.toy})")

    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    baton = BATONS[params.baton]
    if not valid_combo(setting, problem, baton):
        raise StoryError(explain_rejection(setting, problem, baton))

    world = tell(
        setting=setting,
        problem=problem,
        baton_cfg=baton,
        toy_key=params.toy,
        child_name=params.child_name,
        child_gender=params.child_gender,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    for params in CURATED:
        outcome = asp_outcome(params)
        if outcome != "wobble_then_helped":
            rc = 1
            print(f"MISMATCH in outcome for curated params: {params} -> {outcome}")

    try:
        smoke_params = CURATED[0]
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if "foot" not in sample.story or "baton" not in sample.story:
            raise StoryError("required seed words missing from story text")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("resolved default story was empty")
        print("OK: default resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, baton) triples:\n")
        for setting, problem, baton in combos:
            print(f"  {setting:13} {problem:12} {baton}")
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
            header = f"### {p.child_name}: {p.problem} with {p.baton} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
