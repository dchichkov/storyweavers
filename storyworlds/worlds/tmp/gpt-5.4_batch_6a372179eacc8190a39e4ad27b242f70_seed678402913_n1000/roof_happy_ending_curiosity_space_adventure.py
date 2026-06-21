#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/roof_happy_ending_curiosity_space_adventure.py
==========================================================================

A standalone storyworld for a tiny "space adventure on the roof" domain.

Premise
-------
A curious child spots something strange on the roof during a pretend space game.
The child wants to climb up by an unsafe route to investigate. A helper warns
them, the world model predicts wobble and danger, and a grown-up satisfies the
same curiosity in a safer way. Every ending is happy, but the turn is driven by
simulated risk and relief rather than by a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/roof_happy_ending_curiosity_space_adventure.py
    python storyworlds/worlds/gpt-5.4/roof_happy_ending_curiosity_space_adventure.py --mystery glint --solution telescope
    python storyworlds/worlds/gpt-5.4/roof_happy_ending_curiosity_space_adventure.py --route balloon
    python storyworlds/worlds/gpt-5.4/roof_happy_ending_curiosity_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/roof_happy_ending_curiosity_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/roof_happy_ending_curiosity_space_adventure.py --verify
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
    scene: str
    crew1: str
    crew2: str
    mission: str
    launch_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    opening: str
    reveal: str
    need: str
    height: int
    wonder: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    kind: str
    reach: int
    risk: int
    sense: int
    wobble: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    power: int = 0
    sense: int = 0
    action: str = ""
    result: str = ""
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "helper"}]

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
    child = world.get("child")
    route = world.get("route")
    if child.meters["climbing"] < THRESHOLD or route.meters["unstable"] < THRESHOLD:
        return out
    sig = ("wobble", child.id, route.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("roof").meters["danger"] += 1
    child.memes["fear"] += 1
    for kid in world.kids():
        if kid.id != child.id:
            kid.memes["fear"] += 1
    out.append("__wobble__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
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
        for sent in produced:
            world.say(sent)
    return produced


def route_can_tempt(route: Route, mystery: Mystery) -> bool:
    return route.reach + 1 >= mystery.height and route.sense >= SENSE_MIN


def solution_can_satisfy(solution: Solution, mystery: Mystery) -> bool:
    return mystery.need in solution.handles and solution.power >= mystery.height and solution.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for mystery_id, mystery in MYSTERIES.items():
            for route_id, route in ROUTES.items():
                if not route_can_tempt(route, mystery):
                    continue
                for solution_id, solution in SOLUTIONS.items():
                    if solution_can_satisfy(solution, mystery):
                        combos.append((theme_id, mystery_id, route_id, solution_id))
    return combos


def explain_route(route_id: str) -> str:
    route = ROUTES[route_id]
    if route.sense < SENSE_MIN:
        better = ", ".join(sorted(rid for rid, r in ROUTES.items() if r.sense >= SENSE_MIN))
        return (
            f"(No story: '{route.label}' is too fantastical or unreasonable as a real way to reach a roof. "
            f"Try one of these grounded routes instead: {better}.)"
        )
    return f"(No story: {route.label} would not even bring the child close enough to the roof to create this problem.)"


def explain_solution(solution_id: str, mystery_id: str) -> str:
    solution = SOLUTIONS[solution_id]
    mystery = MYSTERIES[mystery_id]
    if solution.sense < SENSE_MIN:
        better = ", ".join(sorted(sid for sid, s in SOLUTIONS.items() if s.sense >= SENSE_MIN))
        return (
            f"(No story: '{solution.label}' is not a sensible grown-up fix here. "
            f"Try one of these safer solutions: {better}.)"
        )
    return (
        f"(No story: {solution.label} cannot safely satisfy this curiosity. "
        f"The mystery on the roof needs a grown-up method that can {mystery.need} it.)"
    )


def predict_attempt(world: World, route: Route) -> dict:
    sim = world.copy()
    child = sim.get("child")
    route_ent = sim.get("route")
    child.meters["climbing"] += 1
    route_ent.meters["unstable"] += route.risk / 2
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("roof").meters["danger"],
        "fear": child.memes["fear"],
    }


def introduce(world: World, child: Entity, helper: Entity, theme: Theme) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"At dusk, {child.id} and {helper.id} turned the backyard into {theme.scene}. "
        f"{theme.launch_line}"
    )
    world.say(
        f'"{theme.crew1} {child.id} and {theme.crew2} {helper.id}!" {child.id} said. '
        f'"Tonight we will {theme.mission}."'
    )


def discover(world: World, child: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"Then {child.id} stopped and pointed up. On the roof, {mystery.opening}."
    )
    world.say(
        f'{helper.id} squinted. "What is it?" {helper.pronoun()} asked.'
    )
    world.say(
        f"{child.id}'s curiosity grew bright and warm, as if a tiny star had switched on inside {child.pronoun('object')}."
    )


def tempt(world: World, child: Entity, route: Route, mystery: Mystery) -> None:
    child.memes["boldness"] += 1
    world.say(
        f'"Maybe I can find out," {child.id} whispered. {child.pronoun().capitalize()} looked at {route.phrase} '
        f"and imagined climbing high enough to reach the roof."
    )
    world.say(
        f"The idea felt adventurous for one quick second, like the start of a real space rescue."
    )


def warn(world: World, child: Entity, helper: Entity, parent: Entity, route: Route) -> None:
    pred = predict_attempt(world, route)
    helper.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{helper.id} tugged at {child.pronoun("possessive")} sleeve. "{route.label.capitalize()} can wobble," '
        f'{helper.pronoun()} said. "If you climb that way, you could slip before you ever touch the roof."'
    )
    world.say(
        f'{helper.id} glanced toward the house. "Let\'s ask {parent.label_word} instead."'
    )


def attempt(world: World, child: Entity, route: Route) -> None:
    child.meters["climbing"] += 1
    world.get("route").meters["unstable"] += route.risk / 2
    propagate(world, narrate=False)
    world.say(
        f"But curiosity pulled harder. {child.id} put one foot on {route.phrase}, then another."
    )
    world.say(route.wobble)
    if world.get("roof").meters["danger"] >= THRESHOLD:
        world.say(
            f"{child.id}'s heart gave a frightened jump. The mission suddenly felt less like a game and more like a real fall waiting to happen."
        )


def intervene(world: World, parent: Entity, child: Entity, helper: Entity) -> None:
    child.memes["fear"] += 0
    parent.memes["care"] += 1
    world.say(
        f'"Freeze, space explorer," called {parent.label_word} from the back door.'
    )
    world.say(
        f"{parent.label_word.capitalize()} hurried over, lifted {child.id} down, and set {child.pronoun('object')} back on the grass."
    )
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.get("roof").meters["danger"] = 0.0
    world.get("route").meters["unstable"] = 0.0
    child.meters["climbing"] = 0.0


def reassure(world: World, parent: Entity, child: Entity, helper: Entity) -> None:
    for kid in (child, helper):
        kid.memes["love"] += 1
    world.say(
        f'"I know you wanted to learn what was up there," {parent.label_word} said softly. '
        f'"Curiosity is wonderful. Climbing to the roof without a grown-up is not safe."'
    )
    world.say(
        f"{child.id} nodded, still breathing fast, while {helper.id} stood close beside {child.pronoun('object')}."
    )


def solve(world: World, parent: Entity, child: Entity, helper: Entity, mystery: Mystery, solution: Solution) -> None:
    for kid in (child, helper):
        kid.memes["wonder"] += 1
        kid.memes["joy"] += 1
        kid.memes["curiosity"] = 0.0
        kid.memes["relief"] += 1
    world.say(
        f"Then {parent.label_word} smiled. {parent.pronoun().capitalize()} {solution.action}."
    )
    world.say(solution.result.format(reveal=mystery.reveal))
    if mystery.need == "see":
        world.say(
            f"{child.id} laughed. {mystery.wonder} The mystery had stayed on the roof, but the answer had come safely down to them."
        )
    else:
        world.say(
            f"When {parent.pronoun()} brought it down from the roof, {child.id} clapped. {mystery.wonder}"
        )


def ending(world: World, child: Entity, helper: Entity, theme: Theme) -> None:
    world.say(
        f'Soon the mission changed. "{theme.ending_line}" {helper.id} said.'
    )
    world.say(
        f"{child.id} and {helper.id} lay on a blanket and kept watching the sky, bright-eyed and safe, while the roof rested quietly above them."
    )


def tell(
    theme: Theme,
    mystery: Mystery,
    route: Route,
    solution: Solution,
    *,
    child_name: str = "Nova",
    child_gender: str = "girl",
    helper_name: str = "Finn",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="instigator", traits=[trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper", traits=["careful"]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    roof = world.add(Entity(id="roof", type="roof", label="roof", phrase="the roof", tags={"roof"}))
    route_ent = world.add(Entity(id="route", type="route", label=route.label, phrase=route.phrase, tags=set(route.tags)))
    mystery_ent = world.add(Entity(id="mystery", type="mystery", label=mystery.label, phrase=mystery.label, tags=set(mystery.tags)))

    introduce(world, child, helper, theme)
    discover(world, child, helper, mystery)

    world.para()
    tempt(world, child, route, mystery)
    warn(world, child, helper, parent, route)
    attempt(world, child, route)

    world.para()
    intervene(world, parent, child, helper)
    reassure(world, parent, child, helper)
    solve(world, parent, child, helper, mystery, solution)

    world.para()
    ending(world, child, helper, theme)

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        roof=roof,
        route_cfg=route,
        solution_cfg=solution,
        mystery_cfg=mystery,
        curiosity_started=True,
        danger_seen=world.facts.get("predicted_danger", 0) >= THRESHOLD,
        discovered=mystery.reveal,
        safe=True,
    )
    return world


THEMES = {
    "space_patrol": Theme(
        id="space_patrol",
        scene="a little moon base under the evening sky",
        crew1="Captain",
        crew2="Scout",
        mission="solve the mystery signal from above",
        launch_line="A silver mixing bowl became a helmet, two cardboard tubes became rocket controls, and the steps beside the porch became their launch pad.",
        ending_line="Best mission report ever",
        tags={"space", "roof"},
    ),
    "star_ship": Theme(
        id="star_ship",
        scene="the launch deck of a brave star ship",
        crew1="Commander",
        crew2="Navigator",
        mission="investigate the strange thing shining overhead",
        launch_line="A laundry basket became a cockpit, a blanket became the star map, and the garden path became the runway to the stars.",
        ending_line="Our ship stayed on the safe side of the galaxy",
        tags={"space", "roof"},
    ),
    "planet_scouts": Theme(
        id="planet_scouts",
        scene="a tiny station on the edge of Mars",
        crew1="Pilot",
        crew2="Beacon Keeper",
        mission="learn what secret waited above the house",
        launch_line="A flashlight became a scanner, a red bucket became a sample pod, and three flat stones became the launch buttons.",
        ending_line="The smartest explorers ask for help before they climb",
        tags={"space", "roof"},
    ),
}

MYSTERIES = {
    "glint": Mystery(
        id="glint",
        label="a silver glint",
        opening="a silver glint flashed beside the chimney whenever the moon came out",
        reveal="it was only moonlight shining on the round metal cap of the chimney",
        need="see",
        height=3,
        wonder="They had solved a moon puzzle without taking a single unsafe step.",
        tags={"moon", "roof"},
    ),
    "kite": Mystery(
        id="kite",
        label="a star kite",
        opening="the corner of a paper star kite was peeking over the roof like a trapped comet tail",
        reveal="it was their paper star kite, caught gently on a loose branch that rested by the roof edge",
        need="reach",
        height=2,
        wonder="The lost comet came home to its astronauts after all.",
        tags={"kite", "roof"},
    ),
    "owl": Mystery(
        id="owl",
        label="a round shadow",
        opening="a round shadow blinked twice near the gutter, almost like a tiny creature from another planet",
        reveal="it was a small owl, puffed up and sleepy, blinking in the moonlight",
        need="see",
        height=2,
        wonder="The night felt even bigger now that they knew who had been visiting the roof.",
        tags={"owl", "roof"},
    ),
}

ROUTES = {
    "porch_rail": Route(
        id="porch_rail",
        label="the porch rail",
        phrase="the porch rail",
        kind="climb",
        reach=2,
        risk=2,
        sense=2,
        wobble="The rail gave a little shiver under the weight, and the whole plan suddenly looked thin and shaky.",
        tags={"climb"},
    ),
    "ladder_alone": Route(
        id="ladder_alone",
        label="the old ladder",
        phrase="the old ladder leaning by the shed",
        kind="climb",
        reach=3,
        risk=3,
        sense=2,
        wobble="The ladder scraped the wall and wiggled sideways just enough to make both children gasp.",
        tags={"ladder", "climb"},
    ),
    "trash_bin": Route(
        id="trash_bin",
        label="the trash bin",
        phrase="the big trash bin by the wall",
        kind="climb",
        reach=1,
        risk=2,
        sense=2,
        wobble="The lid tipped with a hollow clunk, and one more step would have sent feet skidding.",
        tags={"climb"},
    ),
    "balloon": Route(
        id="balloon",
        label="a bunch of balloons",
        phrase="a bunch of balloons tied to a toy wagon",
        kind="fantasy",
        reach=5,
        risk=0,
        sense=1,
        wobble="The balloons bobbed, but they were never a real way up.",
        tags={"fantasy"},
    ),
}

SOLUTIONS = {
    "telescope": Solution(
        id="telescope",
        label="the telescope",
        phrase="a telescope",
        handles={"see"},
        power=3,
        sense=3,
        action="brought out the little telescope from the hall closet and aimed it carefully upward",
        result='Through the lens, the strange shape snapped into focus: {reveal}.',
        qa_text="used a telescope to look at the roof safely",
        tags={"telescope", "stars"},
    ),
    "binoculars": Solution(
        id="binoculars",
        label="binoculars",
        phrase="binoculars",
        handles={"see"},
        power=2,
        sense=3,
        action="lifted a pair of binoculars from the shelf by the back door and let the children look one at a time",
        result='The blur became clear at once: {reveal}.',
        qa_text="used binoculars to look up at the roof safely",
        tags={"binoculars", "stars"},
    ),
    "adult_ladder": Solution(
        id="adult_ladder",
        label="the grown-up ladder",
        phrase="a grown-up with a steady ladder",
        handles={"reach"},
        power=3,
        sense=3,
        action="held the ladder steady, climbed it carefully alone, and reached the roof edge while both children watched from the grass",
        result='{reveal}.',
        qa_text="climbed a steady ladder alone and brought the thing down safely",
        tags={"ladder", "help"},
    ),
    "grabber": Solution(
        id="grabber",
        label="the grabber stick",
        phrase="a long grabber stick",
        handles={"reach"},
        power=2,
        sense=3,
        action="fetched a long grabber stick from the laundry room and stretched it up from the porch steps",
        result='A soft snag, a careful pull, and then the answer came free: {reveal}.',
        qa_text="used a long grabber stick to bring the thing down safely",
        tags={"tool", "help"},
    ),
    "toy_rocket": Solution(
        id="toy_rocket",
        label="a toy rocket",
        phrase="a toy rocket",
        handles={"reach"},
        power=1,
        sense=1,
        action="rolled a toy rocket across the yard",
        result='It did not help with the roof at all.',
        qa_text="rolled a toy rocket uselessly",
        tags={"toy"},
    ),
}


GIRL_NAMES = ["Nova", "Luna", "Mira", "Zoe", "Ava", "Ivy", "Maya", "Nora"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Theo", "Eli", "Noah", "Max", "Sam"]
TRAITS = ["curious", "eager", "bright", "thoughtful", "wondering"]


@dataclass
class StoryParams:
    theme: str
    mystery: str
    route: str
    solution: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "roof": [
        (
            "Why should children not climb onto a roof alone?",
            "Roofs are high, and a child can slip or lose balance very quickly. A grown-up should handle anything that needs to be checked up there."
        )
    ],
    "telescope": [
        (
            "What does a telescope do?",
            "A telescope makes faraway things look bigger and clearer. It helps people study the moon, stars, or something high up without climbing closer."
        )
    ],
    "binoculars": [
        (
            "What are binoculars for?",
            "Binoculars help your eyes see faraway things more clearly. People can use them to watch birds, the sky, or something on a roof from a safe place."
        )
    ],
    "ladder": [
        (
            "How should a ladder be used safely?",
            "A ladder should be steady, on firm ground, and used by a careful grown-up when the job is high. Wobbly climbing is never a game."
        )
    ],
    "owl": [
        (
            "Why do owls come out at night?",
            "Owls are night animals, so they are awake when the sky is dark. Their big eyes help them see in dim light."
        )
    ],
    "kite": [
        (
            "Why can a kite get stuck on a roof?",
            "Wind can push a kite up and over a high edge. Once it catches on something, it may need a grown-up to get it down safely."
        )
    ],
    "moon": [
        (
            "Why can moonlight make things look strange?",
            "Moonlight is softer than sunlight, so it can turn ordinary objects into shiny or shadowy shapes. That is why a roof can look mysterious at night."
        )
    ],
    "stars": [
        (
            "Why do the stars seem brighter when you stop and look carefully?",
            "When you slow down and let your eyes adjust, faint points of light are easier to notice. Quiet watching can reveal more of the night sky."
        )
    ],
}
KNOWLEDGE_ORDER = ["roof", "moon", "owl", "kite", "telescope", "binoculars", "ladder", "stars"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery_cfg"]
    solution = f["solution_cfg"]
    return [
        f'Write a happy bedtime-style space adventure for a 3-to-5-year-old that includes the word "roof" and begins with curiosity about something mysterious overhead.',
        f"Tell a gentle story where {child.label} wants to investigate something on the roof, but {helper.label} helps slow the mission down until a grown-up uses {solution.phrase}.",
        f'Write a child-facing story about curiosity and safety where a strange thing on the roof turns out to be {mystery.reveal}, and the ending feels bright and calm.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    mystery = f["mystery_cfg"]
    route = f["route_cfg"]
    solution = f["solution_cfg"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label} and {helper.label}, two children pretending to be space explorers, and {child.label}'s {pw} who helps them at the important moment."
        ),
        (
            "What made the children curious?",
            f"They saw {mystery.opening} on the roof and wanted to know what it was. The mystery pulled {child.label} toward action because it looked like part of their pretend space mission."
        ),
        (
            f"Why was climbing by {route.label} a bad idea?",
            f"It was unsafe because {route.label} could wobble while {child.label} was trying to get close to the roof. That meant curiosity could turn into a fall before the mystery was even solved."
        ),
        (
            f"What did {helper.label} do?",
            f"{helper.label} warned {child.label} and said they should ask a grown-up instead. The warning mattered because {helper.label} noticed the risk before the climb went any farther."
        ),
        (
            f"How did {child.label}'s {pw} solve the problem?",
            f"{pw.capitalize()} {solution.qa_text}. That let the children learn the answer without climbing onto the roof."
        ),
        (
            "What was really on the roof?",
            f"{mystery.reveal[0].upper()}{mystery.reveal[1:]}. The answer satisfied their curiosity and changed the scary moment back into a peaceful adventure."
        ),
        (
            "How did the story end?",
            f"It ended happily with the mystery solved and both children safe on the ground. They kept their space adventure, but in a calmer and wiser way."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"roof"}
    tags |= set(f["mystery_cfg"].tags)
    tags |= set(f["solution_cfg"].tags)
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="space_patrol",
        mystery="glint",
        route="ladder_alone",
        solution="telescope",
        child_name="Nova",
        child_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        theme="star_ship",
        mystery="kite",
        route="porch_rail",
        solution="adult_ladder",
        child_name="Leo",
        child_gender="boy",
        helper_name="Mira",
        helper_gender="girl",
        parent="father",
        trait="eager",
    ),
    StoryParams(
        theme="planet_scouts",
        mystery="owl",
        route="trash_bin",
        solution="binoculars",
        child_name="Luna",
        child_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        parent="mother",
        trait="bright",
    ),
    StoryParams(
        theme="space_patrol",
        mystery="kite",
        route="ladder_alone",
        solution="grabber",
        child_name="Theo",
        child_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        parent="father",
        trait="wondering",
    ),
]


ASP_RULES = r"""
reasonable_route(R) :- route(R), route_sense(R, S), sense_min(M), S >= M.
reasonable_solution(Sl) :- solution(Sl), solution_sense(Sl, S), sense_min(M), S >= M.

tempts(M, R) :- mystery(M), route(R), reasonable_route(R),
                mystery_height(M, H), route_reach(R, RR), RR + 1 >= H.

solves(M, Sl) :- mystery(M), solution(Sl), reasonable_solution(Sl),
                 needs(M, N), handles(Sl, N),
                 mystery_height(M, H), solution_power(Sl, P), P >= H.

valid(T, M, R, Sl) :- theme(T), mystery(M), route(R), solution(Sl), tempts(M, R), solves(M, Sl).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("needs", mid, mystery.need))
        lines.append(asp.fact("mystery_height", mid, mystery.height))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("route_reach", rid, route.reach))
        lines.append(asp.fact("route_sense", rid, route.sense))
    for sid, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("solution_power", sid, solution.power))
        lines.append(asp.fact("solution_sense", sid, solution.sense))
        for handle in sorted(solution.handles):
            lines.append(asp.fact("handles", sid, handle))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: curiosity, a roof mystery, and a safe space-adventure ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route:
        route = ROUTES[args.route]
        if route.sense < SENSE_MIN:
            raise StoryError(explain_route(args.route))
        if args.mystery and not route_can_tempt(route, MYSTERIES[args.mystery]):
            raise StoryError(explain_route(args.route))
    if args.solution and args.mystery:
        if not solution_can_satisfy(SOLUTIONS[args.solution], MYSTERIES[args.mystery]):
            raise StoryError(explain_solution(args.solution, args.mystery))
    elif args.solution and SOLUTIONS[args.solution].sense < SENSE_MIN:
        mystery_id = args.mystery or next(iter(MYSTERIES))
        raise StoryError(explain_solution(args.solution, mystery_id))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.route is None or combo[2] == args.route)
        and (args.solution is None or combo[3] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, mystery, route, solution = rng.choice(sorted(combos))
    child_name, child_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=child_name)
    return StoryParams(
        theme=theme,
        mystery=mystery,
        route=route,
        solution=solution,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")

    mystery = MYSTERIES[params.mystery]
    route = ROUTES[params.route]
    solution = SOLUTIONS[params.solution]
    if not route_can_tempt(route, mystery):
        raise StoryError(explain_route(params.route))
    if not solution_can_satisfy(solution, mystery):
        raise StoryError(explain_solution(params.solution, params.mystery))

    world = tell(
        THEMES[params.theme],
        mystery,
        route,
        solution,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
    )

    child = world.get("child")
    helper = world.get("helper")
    parent = world.get("parent")
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["parent"] = parent

    rendered = world.render()
    rendered = rendered.replace("child", child.label).replace("helper", helper.label)
    return StorySample(
        params=params,
        story=rendered,
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
        print(f"{len(combos)} compatible (theme, mystery, route, solution) combos:\n")
        for theme, mystery, route, solution in combos:
            print(f"  {theme:13} {mystery:7} {route:12} {solution}")
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
            header = f"### {p.child_name} & {p.helper_name}: {p.mystery} on the roof ({p.theme}, {p.route} -> {p.solution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
