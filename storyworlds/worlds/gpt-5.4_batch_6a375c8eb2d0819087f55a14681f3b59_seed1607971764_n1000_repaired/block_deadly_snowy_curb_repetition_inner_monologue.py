#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/block_deadly_snowy_curb_repetition_inner_monologue.py
=================================================================================

A standalone story world for a small snowy-curb slice-of-life domain.

Premise
-------
A child and a grown-up reach a snowy curb where a plow pile or icy ridge blocks
the easy way forward. The child is tempted to squeeze near the street or hurry
around it, but the road is slick and the risk is real. A calm grown-up notices,
explains that hidden traffic on ice can be deadly, and either clears the curb or
leads the child to a safer crossing. The ending proves what changed: the child
learns to pause, look, and choose the safe way.

This world uses:
- typed entities with physical meters and emotional memes
- a forward-chaining causal rule engine
- repetition in the prose
- brief inner monologue grounded in state
- a Python reasonableness gate plus an inline ASP twin

Run it
------
python storyworlds/worlds/gpt-5.4/block_deadly_snowy_curb_repetition_inner_monologue.py
python storyworlds/worlds/gpt-5.4/block_deadly_snowy_curb_repetition_inner_monologue.py --all
python storyworlds/worlds/gpt-5.4/block_deadly_snowy_curb_repetition_inner_monologue.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/block_deadly_snowy_curb_repetition_inner_monologue.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
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
class Goal:
    id: str
    need: str
    item: str
    place: str
    opening: str
    finish: str
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
class Block:
    id: str
    label: str
    phrase: str
    material: str
    height: str
    effect: str
    danger: int
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
class HelperPlan:
    id: str
    sense: int
    method: str
    use_for: set[str]
    clears: bool
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
class Setting:
    id: str
    place: str
    curb: str
    road: str
    snow_words: str
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


def _r_blocked_path(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    block = world.get("block")
    if block.meters["present"] < THRESHOLD:
        return out
    sig = ("blocked",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["frustration"] += 1
    child.memes["hurry"] += 1
    out.append("__blocked__")
    return out


def _r_street_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    road = world.get("road")
    if child.meters["near_street"] < THRESHOLD:
        return out
    sig = ("street_risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    road.meters["risk"] += 1
    child.memes["fear"] += 1
    out.append("__risk__")
    return out


def _r_cleared(world: World) -> list[str]:
    out: list[str] = []
    block = world.get("block")
    if block.meters["cleared"] < THRESHOLD:
        return out
    sig = ("cleared",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    block.meters["present"] = 0.0
    child = world.get("child")
    child.memes["relief"] += 1
    out.append("__cleared__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked_path", tag="social", apply=_r_blocked_path),
    Rule(name="street_risk", tag="physical", apply=_r_street_risk),
    Rule(name="cleared", tag="physical", apply=_r_cleared),
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
        for sent in produced:
            world.say(sent)
    return produced


def block_needs_clearance(block: Block) -> bool:
    return block.material in {"snow", "ice"}


def plan_fits(block: Block, plan: HelperPlan) -> bool:
    if plan.sense < SENSE_MIN:
        return False
    return block.material in plan.use_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for goal_id in GOALS:
            for block_id, block in BLOCKS.items():
                if block_needs_clearance(block):
                    combos.append((setting_id, goal_id, block_id))
    return combos


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["near_street"] += 1
    propagate(sim, narrate=False)
    return {
        "road_risk": sim.get("road").meters["risk"],
        "fear": sim.get("child").memes["fear"],
    }


def introduce(world: World, child: Entity, helper: Entity, goal: Goal) -> None:
    world.say(
        f"Snow had been pushed up along {world.setting.curb}, and the whole {world.setting.place} "
        f"looked quiet and white. {goal.opening}"
    )
    world.say(
        f"{child.id} walked beside {helper.label_word}, holding {goal.item} and watching the snow shine blue in the cold."
    )


def reveal_block(world: World, child: Entity, goal: Goal, block: Block) -> None:
    world.get("block").meters["present"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When they reached the curb, {child.id} stopped. {block.phrase} sat right where they needed to go, "
        f"like a hard little block across the way."
    )
    world.say(
        f"It was {block.height}, and it {block.effect}."
    )
    world.facts["need"] = goal.need


def inner_monologue(world: World, child: Entity, block: Block, goal: Goal) -> None:
    child.memes["desire"] += 1
    hurry = "I just want to keep going, keep going, keep going," if child.memes["hurry"] >= THRESHOLD else "I want to keep going."
    world.say(
        f"{child.id} looked at the snow, then at {goal.place}. Inside, {child.pronoun()} thought, "
        f'"{hurry} If I slip around the side, I can get there fast."'
    )
    world.say(
        f"But another thought came right after it: "
        f'The street is close. The snow is hiding the edge."'
    )


def warn(world: World, helper: Entity, child: Entity, block: Block) -> None:
    pred = predict_risk(world)
    world.facts["predicted_road_risk"] = pred["road_risk"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} saw {child.pronoun("possessive")} boots angle toward the street and said, '
        f'"Wait, wait, wait. Not by the road."'
    )
    world.say(
        f'"A car on icy snow can slide farther than people think," {helper.pronoun()} said softly. '
        f'"That kind of hurry can turn deadly, even on a small block."'
    )


def edge_toward_street(world: World, child: Entity) -> None:
    child.meters["near_street"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} took one careful step toward the gray edge of the street, then another."
    )


def near_miss(world: World, child: Entity) -> None:
    road = world.get("road")
    road.meters["car_pass"] += 1
    child.memes["fear"] += 1
    world.say(
        "At that moment a car whispered past on the slick road, slower than walking and still too close for comfort."
    )
    world.say(
        f"{child.id}'s stomach gave a little flip. Inside, {child.pronoun()} thought, "
        f'"Too close. Too close. I do not like this."'
    )


def choose_plan(world: World, helper: Entity, child: Entity, plan: HelperPlan, block: Block, goal: Goal) -> None:
    if plan.clears:
        world.get("block").meters["cleared"] += 1
        propagate(world, narrate=False)
    else:
        child.memes["patience"] += 1
        child.memes["relief"] += 1
    body = plan.text.format(
        helper=helper.label_word,
        block=block.label,
        place=goal.place,
    )
    world.say(body)


def finish_story(world: World, helper: Entity, child: Entity, plan: HelperPlan, goal: Goal) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} nodded. This time {child.pronoun()} stayed close, watched {helper.label_word} move, and did not rush."
    )
    world.say(
        f"Soon they were on their way again. {goal.finish}"
    )
    if plan.clears:
        world.say(
            f"As they went, the curb behind them no longer looked like a wall. It was just a place that had needed a safe, patient hand."
        )
    else:
        world.say(
            f"As they crossed at the safer corner, the old blocked curb stayed behind them, small and harmless now that they had not tried to fight it."
        )
@dataclass
class StoryParams:
    setting: str
    goal: str
    block: str
    plan: str
    child_name: str
    child_type: str
    helper_type: str
    trait: str
    attempt: str = "pause"
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
    "snow": [(
        "Why can snow piled by a curb be hard to cross?",
        "Plowed snow can freeze into a hard pile that covers the easy place to step down. That makes people climb higher or walk farther to find a clear spot."
    )],
    "curb": [(
        "What is a curb?",
        "A curb is the raised edge between a sidewalk and a street. It helps show where walking space ends and road space begins."
    )],
    "ice": [(
        "Why is ice slippery?",
        "Ice is slippery because its surface is very smooth and can melt into a tiny wet film. Shoes and tires grip it less, so slipping and sliding are easier."
    )],
    "crosswalk": [(
        "Why is a crosswalk safer than stepping into the street anywhere?",
        "A crosswalk is the place drivers are supposed to watch for people crossing. It also often has a clearer path and better sight lines than a blocked curb."
    )],
    "salt": [(
        "Why do people put salt on icy sidewalks?",
        "Salt helps ice melt so the surface gets rougher and less slick. That can make walking and stepping down safer."
    )],
    "shovel": [(
        "What does a shovel help with in winter?",
        "A shovel can move snow out of the way and open a clear path. That helps people see where to step and keeps feet out of the street."
    )],
    "street": [(
        "Why can a snowy street be dangerous?",
        "Cars need more time to stop on snow and ice. Even a slow car can slide, so people should stay out of the road until there is a safe place to cross."
    )],
}
KNOWLEDGE_ORDER = ["snow", "curb", "ice", "crosswalk", "salt", "shovel", "street"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    goal = f["goal"]
    block = f["block_cfg"]
    outcome = f["outcome"]
    if outcome.startswith("near_miss"):
        return [
            f'Write a short slice-of-life story for a 3-to-5-year-old set by a snowy curb. Include the words "block" and "deadly".',
            f"Tell a winter errand story where {child.id} almost edges into the street because a {block.label} blocks the curb, but a grown-up stops {child.pronoun('object')} in time.",
            "Write a gentle near-miss story with repetition and inner monologue, ending with the child choosing the safe way after a scary moment.",
        ]
    return [
        f'Write a short slice-of-life story for a 3-to-5-year-old set by a snowy curb on the way to {goal.place}. Include the words "block" and "deadly".',
        f"Tell a winter story where {child.id} wants to hurry past a blocked curb, but a calm grown-up helps {child.pronoun('object')} slow down and cross safely.",
        "Write a simple everyday story with repetition and inner monologue, where a child learns that being patient near the street matters.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    goal = f["goal"]
    block = f["block_cfg"]
    plan = f["plan"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.label_word}, walking by a snowy curb to {goal.place}. Their small errand turns into a lesson about slowing down near the street."
        ),
        (
            "What was blocking them?",
            f"A {block.label} blocked the easy way down from the curb. It changed a simple walk into a risky choice because the safe step was hidden."
        ),
        (
            f"Why did {helper.label_word} say to wait?",
            f"{helper.label_word.capitalize()} saw that the street was close and slick. {helper.pronoun().capitalize()} warned that a car on ice can slide, which is why the hurry felt dangerous and even deadly."
        ),
    ]
    if f["outcome"].startswith("near_miss"):
        qa.append((
            f"What happened when {child.id} edged toward the street?",
            f"{child.id} stepped toward the road just as a car passed on the slick street. Nothing hit {child.pronoun('object')}, but the close moment made the danger feel real and helped {child.pronoun('object')} listen."
        ))
    else:
        qa.append((
            f"How did {child.id} show that {child.pronoun()} was listening?",
            f"{child.id} stayed beside {helper.label_word} instead of stepping into the street. {child.pronoun().capitalize()} repeated a slower thought inside {child.pronoun('possessive')} head and waited for the safe plan."
        ))
    qa.append((
        "How did they solve the problem?",
        f"They solved it because {helper.label_word} {plan.qa_text}. That changed the scene from a blocked, risky curb into a safe way forward."
    ))
    qa.append((
        "How did the story end?",
        f"They finished their small errand safely and kept going together. The ending image shows the real change: {child.id} no longer tries to rush past the curb."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"snow", "curb", "street"} | set(world.facts["plan"].tags) | set(world.facts["block_cfg"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="snowy_curb",
        goal="mailbox",
        block="plow_pile",
        plan="shovel_clear",
        child_name="Nora",
        child_type="girl",
        helper_type="mother",
        trait="eager",
        attempt="pause",
    ),
    StoryParams(
        setting="snowy_curb",
        goal="library",
        block="icy_ridge",
        plan="salt_then_wait",
        child_name="Leo",
        child_type="boy",
        helper_type="father",
        trait="curious",
        attempt="edge",
    ),
    StoryParams(
        setting="snowy_curb",
        goal="bakery",
        block="slush_wall",
        plan="crosswalk_detour",
        child_name="Mia",
        child_type="girl",
        helper_type="teacher",
        trait="patient",
        attempt="pause",
    ),
    StoryParams(
        setting="snowy_curb",
        goal="mailbox",
        block="icy_ridge",
        plan="crosswalk_detour",
        child_name="Finn",
        child_type="boy",
        helper_type="mother",
        trait="thoughtful",
        attempt="edge",
    ),
]


def explain_rejection(block: Block, plan: HelperPlan) -> str:
    if plan.sense < SENSE_MIN:
        return (
            f"(No story: plan '{plan.id}' is known to the world but refused because it is low common sense. "
            f"Children should not solve a blocked curb by squeezing around the road edge.)"
        )
    if block.material not in plan.use_for:
        return (
            f"(No story: {plan.id} does not fit a {block.label}. The chosen help must actually work on "
            f"the block at the curb.)"
        )
    return "(No story: this combination does not make a reasonable safe plan.)"


ASP_RULES = r"""
needs_clearance(B) :- block(B), material(B,snow).
needs_clearance(B) :- block(B), material(B,ice).

valid(S,G,B) :- setting(S), goal(G), block(B), needs_clearance(B).

sensible_plan(P) :- plan(P), sense(P,S), sense_min(M), S >= M.
fits(B,P) :- block(B), plan(P), sensible_plan(P), material(B,M), works_on(P,M).

safe_choice(B,P) :- fits(B,P).

outcome(near_miss_cleared) :- attempt(edge), chosen_plan(P), clears(P).
outcome(near_miss_detour)  :- attempt(edge), chosen_plan(P), not clears(P).
outcome(listened_cleared)  :- attempt(pause), chosen_plan(P), clears(P).
outcome(listened_detour)   :- attempt(pause), chosen_plan(P), not clears(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for bid, block in BLOCKS.items():
        lines.append(asp.fact("block", bid))
        lines.append(asp.fact("material", bid, block.material))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, plan.sense))
        for mat in sorted(plan.use_for):
            lines.append(asp.fact("works_on", pid, mat))
        if plan.clears:
            lines.append(asp.fact("clears", pid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_plans() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_plan/1."))
    return sorted(p for (p,) in asp.atoms(model, "sensible_plan"))


def asp_safe_choices() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show safe_choice/2."))
    return sorted(set(asp.atoms(model, "safe_choice")))


def outcome_of(params: StoryParams) -> str:
    chosen_plan = PLANS[params.plan]
    if params.attempt == "edge":
        return "near_miss_cleared" if chosen_plan.clears else "near_miss_detour"
    return "listened_cleared" if chosen_plan.clears else "listened_detour"


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("attempt", params.attempt),
        asp.fact("chosen_plan", params.plan),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    got = asp.atoms(model, "outcome")
    return got[0][0] if got else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a blocked snowy curb, a tempted child, and a safer way forward."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--block", choices=BLOCKS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "teacher"])
    ap.add_argument("--attempt", choices=["pause", "edge"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos and safe plan fits derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_rejection(BLOCKS[args.block] if args.block else next(iter(BLOCKS.values())), PLANS[args.plan]))

    if args.block and args.plan:
        block = BLOCKS[args.block]
        plan = PLANS[args.plan]
        if not plan_fits(block, plan):
            raise StoryError(explain_rejection(block, plan))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.goal is None or combo[1] == args.goal)
        and (args.block is None or combo[2] == args.block)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, goal_id, block_id = rng.choice(sorted(combos))
    block = BLOCKS[block_id]
    plans = [
        pid for pid, plan in PLANS.items()
        if plan_fits(block, plan)
        and (args.plan is None or pid == args.plan)
    ]
    if not plans:
        raise StoryError("(No safe plan matches the given options.)")

    child_type = args.child_type or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    helper_type = args.helper_type or rng.choice(["mother", "father", "teacher"])
    trait = rng.choice(TRAITS)
    attempt = args.attempt or rng.choice(["pause", "edge"])
    return StoryParams(
        setting=setting_id,
        goal=goal_id,
        block=block_id,
        plan=rng.choice(sorted(plans)),
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        trait=trait,
        attempt=attempt,
    )


def _block_phrase(block_cfg: Block, child_name: str) -> Block:
    return Block(
        id=block_cfg.id,
        label=block_cfg.label,
        phrase=block_cfg.phrase,
        material=block_cfg.material,
        height=block_cfg.height.format(child=child_name),
        effect=block_cfg.effect,
        danger=block_cfg.danger,
        tags=set(block_cfg.tags),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        goal = GOALS[params.goal]
        block_cfg = BLOCKS[params.block]
        plan = PLANS[params.plan]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not block_needs_clearance(block_cfg):
        raise StoryError("(This block would not make a real curb problem.)")
    if not plan_fits(block_cfg, plan):
        raise StoryError(explain_rejection(block_cfg, plan))

    world = tell(
        setting=setting,
        goal=goal,
        block_cfg=_block_phrase(block_cfg, params.child_name),
        plan=plan,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
        trait=params.trait,
        attempt=params.attempt,
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
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_plans = {pid for pid, plan in PLANS.items() if plan.sense >= SENSE_MIN}
    asp_plans = set(asp_sensible_plans())
    if py_plans == asp_plans:
        print(f"OK: sensible plans match ({sorted(py_plans)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: python={sorted(py_plans)} clingo={sorted(asp_plans)}")

    safe_pairs_py = {
        (bid, pid)
        for bid, block in BLOCKS.items()
        for pid, plan in PLANS.items()
        if plan_fits(block, plan)
    }
    safe_pairs_asp = set(asp_safe_choices())
    if safe_pairs_py == safe_pairs_asp:
        print(f"OK: block/plan fits match ({len(safe_pairs_py)} pairs).")
    else:
        rc = 1
        print("MISMATCH in block/plan fits:")
        if safe_pairs_py - safe_pairs_asp:
            print("  only in python:", sorted(safe_pairs_py - safe_pairs_asp))
        if safe_pairs_asp - safe_pairs_py:
            print("  only in clingo:", sorted(safe_pairs_asp - safe_pairs_py))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_plan/1.\n#show safe_choice/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible plans:", ", ".join(asp_sensible_plans()))
        print()
        print("valid (setting, goal, block) combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        print()
        print("safe (block, plan) fits:")
        for pair in asp_safe_choices():
            print(" ", pair)
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
            header = f"### {p.child_name}: {p.goal} by the snowy curb ({p.block}, {p.plan}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    goal: Goal,
    block_cfg: Block,
    plan: HelperPlan,
    child_name: str = "Nora",
    child_type: str = "girl",
    helper_type: str = "mother",
    trait: str = "careful",
    attempt: str = "pause",
) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child", traits=[trait]))
    child.id = child_name
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper", traits=["calm"]))
    helper.id = "Parent" if helper_type in {"mother", "father"} else "Teacher"
    world.add(Entity(id="block", kind="thing", type="snow_block", label=block_cfg.label, role="block"))
    world.add(Entity(id="road", kind="thing", type="road", label=setting.road, role="road"))
    world.facts["attempt"] = attempt

    child.memes["care"] = 1.0
    child.memes["patience"] = 0.0
    child.meters["near_street"] = 0.0
    world.get("road").meters["risk"] = 0.0
    world.get("road").meters["car_pass"] = 0.0
    world.get("block").meters["present"] = 0.0
    world.get("block").meters["cleared"] = 0.0

    introduce(world, child, helper, goal)
    reveal_block(world, child, goal, block_cfg)

    world.para()
    inner_monologue(world, child, block_cfg, goal)
    warn(world, helper, child, block_cfg)

    world.para()
    if attempt == "edge":
        edge_toward_street(world, child)
        near_miss(world, child)
        world.say(
            f'{helper.label_word.capitalize()} reached for {child.id}\'s mitten and said, "Back with me. Step back, step back."'
        )
    else:
        child.memes["patience"] += 1
        world.say(
            f'{child.id} pressed {child.pronoun("possessive")} lips together and stayed beside {helper.label_word}.'
        )
        world.say(
            f'Inside, {child.pronoun()} told {child.pronoun("object")}self, "Slow feet now. Slow feet now."'
        )

    world.para()
    choose_plan(world, helper, child, plan, block_cfg, goal)
    finish_story(world, helper, child, plan, goal)

    outcome = "near_miss" if attempt == "edge" else "listened"
    if plan.clears:
        outcome = f"{outcome}_cleared"
    else:
        outcome = f"{outcome}_detour"

    world.facts.update(
        child=child,
        helper=helper,
        goal=goal,
        block_cfg=block_cfg,
        plan=plan,
        outcome=outcome,
        block_cleared=plan.clears,
        road_risk=world.get("road").meters["risk"],
        car_passed=world.get("road").meters["car_pass"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "snowy_curb": Setting(
        id="snowy_curb",
        place="snowy curb",
        curb="the snowy curb beside the street",
        road="the winter road",
        snow_words="white snow and silver slush",
        tags={"snow", "curb", "street"},
    ),
}

GOALS = {
    "mailbox": Goal(
        id="mailbox",
        need="mail",
        item="a bright red letter",
        place="the blue mailbox",
        opening="It was the sort of afternoon when one small errand felt important: they were going to mail a bright red letter.",
        finish="The red letter slipped into the blue mailbox with a neat little thunk, and that tiny sound felt bigger than before.",
        tags={"mailbox", "errand"},
    ),
    "library": Goal(
        id="library",
        need="return_book",
        item="a library book with a fox on the cover",
        place="the library drop slot",
        opening="They were only walking one block to return a library book with a fox on the cover.",
        finish="The book slid into the return slot, and the warm library windows glowed ahead like a promise kept.",
        tags={"library", "book"},
    ),
    "bakery": Goal(
        id="bakery",
        need="pick_up",
        item="a coin purse",
        place="the bakery door",
        opening="They were heading one block to the bakery for bread while the day was still pale and cold.",
        finish="A bell chimed when they reached the bakery door, and warm bread smell rolled out to meet them.",
        tags={"bakery", "bread"},
    ),
}

BLOCKS = {
    "plow_pile": Block(
        id="plow_pile",
        label="plow pile",
        phrase="A stiff plow pile of packed snow",
        material="snow",
        height="almost up to {child}'s knees",
        effect="blocked the low curb cut",
        danger=2,
        tags={"snowbank", "block"},
    ),
    "icy_ridge": Block(
        id="icy_ridge",
        label="icy ridge",
        phrase="A shiny icy ridge",
        material="ice",
        height="low but hard as stone",
        effect="covered the curb in a glassy strip",
        danger=3,
        tags={"ice", "block"},
    ),
    "slush_wall": Block(
        id="slush_wall",
        label="slush wall",
        phrase="A dirty slush wall",
        material="snow",
        height="lumpy and wide",
        effect="made the easy step down disappear",
        danger=2,
        tags={"slush", "block"},
    ),
}

PLANS = {
    "shovel_clear": HelperPlan(
        id="shovel_clear",
        sense=3,
        method="shovel",
        use_for={"snow", "ice"},
        clears=True,
        text='{helper} lifted the small trunk shovel from the stroller hook, chipped a path through the {block}, and brushed the loose snow aside until the curb opened again.',
        qa_text="cleared the blocked curb with a small shovel so there was a safe place to step",
        tags={"shovel", "snow"},
    ),
    "salt_then_wait": HelperPlan(
        id="salt_then_wait",
        sense=3,
        method="salt",
        use_for={"ice"},
        clears=True,
        text='{helper} shook salt over the slick edge, waited a minute, and tapped the crust until the dangerous shine broke apart.',
        qa_text="spread salt and broke the icy edge so it was safer to step",
        tags={"salt", "ice"},
    ),
    "crosswalk_detour": HelperPlan(
        id="crosswalk_detour",
        sense=3,
        method="detour",
        use_for={"snow", "ice"},
        clears=False,
        text='{helper} pointed to the corner and said, "We will take the longer way." Together they walked to the crosswalk where the snow had already been cleared.',
        qa_text="walked to a cleared crosswalk instead of squeezing by the blocked curb",
        tags={"crosswalk", "street"},
    ),
    "hop_around": HelperPlan(
        id="hop_around",
        sense=1,
        method="hop",
        use_for={"snow"},
        clears=False,
        text='{helper} told {helper}self to just hop around the {block}.',
        qa_text="hopped around it",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Lucy", "Ella", "Rose", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Max", "Theo", "Eli", "Sam", "Noah"]
TRAITS = ["careful", "patient", "curious", "eager", "thoughtful"]

if __name__ == "__main__":
    main()
