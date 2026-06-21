#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/art_scrounge_friend_s_backyard_foreshadowing_cautionary.py
=====================================================================================

A standalone storyworld about children making art in a friend's backyard, then
scrounging for a "mystery paint" that turns out to be a yard chemical. The
domain is shaped like a soft whodunit: the story plants clues first, the
children guess wrong, and the reveal shows what the real culprit was.

Run it
------
python storyworlds/worlds/gpt-5.4/art_scrounge_friend_s_backyard_foreshadowing_cautionary.py
python storyworlds/worlds/gpt-5.4/art_scrounge_friend_s_backyard_foreshadowing_cautionary.py --all
python storyworlds/worlds/gpt-5.4/art_scrounge_friend_s_backyard_foreshadowing_cautionary.py --found weed_spray --target stones
python storyworlds/worlds/gpt-5.4/art_scrounge_friend_s_backyard_foreshadowing_cautionary.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/art_scrounge_friend_s_backyard_foreshadowing_cautionary.py --verify
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
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "watchful", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    safe_art: bool = False
    risky: bool = False
    living: bool = False
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
class Project:
    id: str
    scene: str
    goal: str
    first_line: str
    clue_prop: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FoundItem:
    id: str
    label: str
    phrase: str
    where: str
    clue1: str
    clue2: str
    wrong_guess: str
    lesson: str
    smell: str
    danger: str
    makes_mess: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    the: str
    phrase: str
    living: bool
    delicate: int
    reacts: str
    after: str
    can_be_harmed: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class SafeSupply:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_harm(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.entities.get("culprit")
    target = world.entities.get("target")
    if not culprit or not target:
        return out
    if culprit.meters["used"] < THRESHOLD or target.meters["harm"] < THRESHOLD:
        return out
    sig = ("harm", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["guilt"] += 1
    room = world.entities.get("yard")
    if room:
        room.meters["danger"] += 1
    out.append("__harm__")
    return out


CAUSAL_RULES = [
    Rule(name="harm", tag="physical", apply=_r_harm),
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


def hazard_at_risk(found: FoundItem, target: Target) -> bool:
    return found.makes_mess and target.can_be_harmed and target.living


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def damage_severity(target: Target, delay: int) -> int:
    return target.delicate + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= damage_severity(target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, friend_age: int, trait: str) -> bool:
    older_friend = relation == "friends" and friend_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (2.5 if older_friend else 0.0)
    return older_friend and authority > BOLDNESS_INIT


def _do_use(world: World, target_ent: Entity, narrate: bool = True) -> None:
    target_ent.meters["harm"] += 1
    culprit = world.get("culprit")
    culprit.meters["used"] += 1
    culprit.meters["spilled"] += 1
    propagate(world, narrate=narrate)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    _do_use(sim, sim.get("target"), narrate=False)
    return {
        "harm": sim.get("target").meters["harm"] >= THRESHOLD,
        "danger": sim.get("yard").meters["danger"],
    }


def introduce(world: World, a: Entity, b: Entity, project: Project, host: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} was visiting {b.id} in {host.pronoun('possessive')} friend's backyard, "
        f"and soon the two of them turned the grass by the fence into an art studio."
    )
    world.say(project.first_line)
    world.say(
        f"They called themselves the Backyard Detectives because every picture needed "
        f"a clue, a question, and a clever answer."
    )


def setup_mystery(world: World, project: Project) -> None:
    world.say(
        f"Their big plan was {project.goal}. {project.clue_prop} sat in the middle like the first clue in a case."
    )


def scrounge(world: World, a: Entity, found: FoundItem) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'"We need one more special color," {a.id} said. {a.pronoun().capitalize()} went to scrounge around '
        f"{found.where} and came back holding {found.phrase}."
    )
    world.say(f'"Maybe this is {found.wrong_guess}," {a.pronoun()} whispered.')


def foreshadow(world: World, b: Entity, found: FoundItem, host: Entity) -> None:
    pred = predict_trouble(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"But two clues did not fit the nice idea. First, {found.clue1}. Second, {found.clue2}."
    )
    world.say(
        f'{b.id} narrowed {b.pronoun("possessive")} eyes. "That does not smell like paint," '
        f'{b.pronoun()} said. "It smells {found.smell}. We should ask {host.label_word} first."'
    )


def defy(world: World, a: Entity, b: Entity, found: FoundItem) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'{a.id} gave the bottle a little shake. "Maybe the clues are trying to trick us," '
        f'{a.pronoun()} said. Before {b.id} could stop {a.pronoun("object")}, {a.pronoun()} tipped a little onto the project.'
    )


def back_down(world: World, a: Entity, b: Entity, found: FoundItem, host: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked again at the odd bottle, then at the dry patch nearby, and stopped. '
        f'"No," {a.pronoun()} said quietly. "Real art should not begin with a bad clue."'
    )
    world.say(
        f"They set {found.phrase} back where they had found it and went to ask {host.label_word} for real supplies instead."
    )


def reveal(world: World, found: FoundItem, target: Target) -> None:
    _do_use(world, world.get("target"))
    world.say(
        f"For one blink nothing happened. Then {target.the} {target.reacts}, and the whole mystery solved itself in the worst way."
    )
    world.say(
        f"The culprit was not secret paint at all. It was {found.label}, and it was meant for {found.danger}, not for art."
    )


def alarm(world: World, b: Entity, target: Target, host: Entity) -> None:
    world.say(f'"{host.label_word.capitalize()}!" {b.id} cried. "{target.The} is changing!"')


def rescue(world: World, host: Entity, response: Response, target: Target) -> None:
    body = response.text.replace("{target}", target.label)
    world.get("target").meters["harm"] = 0.0
    world.get("yard").meters["danger"] = 0.0
    world.say(f"{host.label_word.capitalize()} came fast from the porch and {body}.")
    world.say(
        f"After a tense minute, the danger stopped growing. {target.after}"
    )


def lesson(world: World, host: Entity, a: Entity, b: Entity, found: FoundItem) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say(
        f'{host.label_word.capitalize()} knelt beside them and spoke softly. "The backyard holds many interesting things," '
        f'{host.pronoun()} said, "but not every bottle is for children, and not every clue is a good one."'
    )
    world.say(
        f'"{found.lesson}," {host.pronoun()} added. "{found.label.capitalize()} is for grown-ups to handle."'
    )
    world.say(f'"We should have asked first," {a.id} and {b.id} said together.')


def safe_ending(world: World, a: Entity, b: Entity, host: Entity, project: Project,
                s1: SafeSupply, s2: SafeSupply) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Then {host.label_word} brought out {s1.phrase} and {s2.phrase}. "
        f'"If you are making backyard art," {host.pronoun()} said, "use things meant for art."'
    )
    world.say(
        f"With the safe supplies, the Backyard Detectives finished {project.goal}. {s1.use.capitalize()}, and {s2.use}."
    )
    world.say(project.end_image)


def rescue_fail(world: World, host: Entity, response: Response, target: Target) -> None:
    world.get("yard").meters["danger"] += 1
    body = response.fail.replace("{target}", target.label)
    world.say(f"{host.label_word.capitalize()} hurried over and {body}.")
    world.say(
        f"But the damage had already settled in. {target.after}"
    )


def sad_ending(world: World, host: Entity, a: Entity, b: Entity, project: Project,
               found: FoundItem, target: Target) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"The detective game ended there. Instead of hanging up their picture, the children stood quietly beside {target.the} and looked at what one poor guess had done."
    )
    world.say(
        f'{host.label_word.capitalize()} put an arm around both of them. "This is why we do not scrounge mystery bottles for art," '
        f'{host.pronoun()} said. "{found.lesson}."'
    )
    world.say(
        f"Later they made a smaller picture on paper with safe crayons, but the real ending stayed in their minds: clues matter, and asking first is part of being careful."
    )


def tell(project: Project, found: FoundItem, target: Target, supplies: tuple[SafeSupply, SafeSupply],
         response: Response, instigator: str = "Nina", instigator_gender: str = "girl",
         friend: str = "Owen", friend_gender: str = "boy", host_type: str = "mother",
         trait: str = "watchful", delay: int = 0, instigator_age: int = 6,
         friend_age: int = 7, relation: str = "friends") -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=friend,
        kind="character",
        type=friend_gender,
        role="friend",
        age=friend_age,
        traits=[trait],
    ))
    host = world.add(Entity(
        id="Host",
        kind="character",
        type=host_type,
        role="host",
        label="the host",
    ))
    world.add(Entity(id="yard", type="yard", label="the yard"))
    culprit = world.add(Entity(
        id="culprit",
        type="found",
        label=found.label,
        phrase=found.phrase,
        risky=True,
        tags=set(found.tags),
    ))
    target_ent = world.add(Entity(
        id="target",
        type="target",
        label=target.label,
        phrase=target.phrase,
        living=target.living,
        tags=set(target.tags),
    ))
    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = initial_caution(trait)

    introduce(world, a, b, project, host)
    setup_mystery(world, project)

    world.para()
    scrounge(world, a, found)
    foreshadow(world, b, found, host)

    averted = would_avert(relation, instigator_age, friend_age, trait)
    if averted:
        back_down(world, a, b, found, host)
        world.para()
        safe_ending(world, a, b, host, project, supplies[0], supplies[1])
        contained = True
        severity = 0
    else:
        defy(world, a, b, found)

        world.para()
        reveal(world, found, target)
        alarm(world, b, target, host)

        severity = damage_severity(target, delay)
        contained = is_contained(response, target, delay)

        world.para()
        if contained:
            rescue(world, host, response, target)
            lesson(world, host, a, b, found)
            world.para()
            safe_ending(world, a, b, host, project, supplies[0], supplies[1])
        else:
            rescue_fail(world, host, response, target)
            sad_ending(world, host, a, b, project, found, target)

    outcome = "averted" if averted else ("contained" if contained else "spoiled")
    world.facts.update(
        project=project,
        found=found,
        target_cfg=target,
        target=target_ent,
        culprit=culprit,
        response=response,
        supplies=supplies,
        instigator=a,
        friend=b,
        host=host,
        relation=relation,
        outcome=outcome,
        severity=severity,
        delay=delay,
        ignited=target_ent.meters["harm"] >= THRESHOLD,
    )
    return world


PROJECTS = {
    "mural": Project(
        id="mural",
        scene="a long paper mural clipped to the fence",
        goal="a mystery mural of the backyard",
        first_line="They clipped a long paper mural to the fence and began drawing paw prints, leaf shadows, and one question mark under the birdbath.",
        clue_prop="A jar of clean water and a stubby brush",
        end_image="At the end, the fence held a bright backyard mystery mural, and every color on it was one they were allowed to use.",
        tags={"art", "mural", "detective"},
    ),
    "map": Project(
        id="map",
        scene="a giant treasure map on cardboard",
        goal="a detective map of the backyard",
        first_line="They spread a giant piece of cardboard on the grass and drew a winding path from the sandbox to the plum tree, with tiny magnifying glasses in the corners.",
        clue_prop="A box of crayons and a paper notebook of clues",
        end_image="Soon their detective map fluttered on the washing line, full of arrows and safe bright color.",
        tags={"art", "map", "detective"},
    ),
    "posters": Project(
        id="posters",
        scene="three little suspect posters on clipboards",
        goal="three silly suspect posters for a make-believe case",
        first_line="They set three clipboards on a picnic table and started making suspect posters for a missing strawberry case.",
        clue_prop="A cup for water and a stack of paper circles",
        end_image="By the end, three neat suspect posters leaned against a flowerpot, and none of the color had come from a mystery bottle.",
        tags={"art", "poster", "detective"},
    ),
}

FOUND_ITEMS = {
    "weed_spray": FoundItem(
        id="weed_spray",
        label="weed spray",
        phrase="a cloudy bottle of weed spray",
        where="by the shed wall",
        clue1="the grass around it looked patchy and tired",
        clue2="a warning picture of a gloved hand was printed on the side",
        wrong_guess="silver paint that had gone a little funny",
        lesson="never use mystery spray as paint",
        smell="sharp and bitter",
        danger="pulling weeds, not painting flowers",
        tags={"weed_spray", "chemical", "warning_label"},
    ),
    "wood_stain": FoundItem(
        id="wood_stain",
        label="wood stain",
        phrase="a sticky can of wood stain",
        where="under the workbench beside the fence",
        clue1="dark drips had dried on the outside like old syrup",
        clue2="the brush next to it was stiff as a twig",
        wrong_guess="secret brown paint for detective shadows",
        lesson="never use mystery cans as paint",
        smell="oily and strange",
        danger="grown-up repair work, not children's art",
        tags={"wood_stain", "chemical"},
    ),
    "bug_powder": FoundItem(
        id="bug_powder",
        label="bug powder",
        phrase="a dented shaker of bug powder",
        where="on a high shelf inside the open garden bench",
        clue1="tiny white dust ringed the lid",
        clue2="an ant picture stared from the label",
        wrong_guess="sparkly chalk dust for clues",
        lesson="never use mystery powders as art supplies",
        smell="dry and bitter",
        danger="dealing with bugs, not drawing pictures",
        tags={"bug_powder", "chemical", "ants"},
    ),
}

TARGETS = {
    "daisies": Target(
        id="daisies",
        label="daisies",
        the="the daisies",
        phrase="the daisy patch by the stepping stones",
        living=True,
        delicate=2,
        reacts="drooped and spotted at the edges",
        after="The white petals slowly stopped sagging, though several blooms still had to be trimmed away.",
        can_be_harmed=True,
        tags={"flowers", "garden"},
    ),
    "tomatoes": Target(
        id="tomatoes",
        label="tomato plants",
        the="the tomato plants",
        phrase="the tomato plants near the fence",
        living=True,
        delicate=2,
        reacts="curled and shivered under the drops",
        after="Some leaves recovered after rinsing, but a few had to be removed.",
        can_be_harmed=True,
        tags={"plants", "garden", "vegetables"},
    ),
    "herbs": Target(
        id="herbs",
        label="herb bed",
        the="the herb bed",
        phrase="the little herb bed under the window",
        living=True,
        delicate=1,
        reacts="darkened in little patches",
        after="The smell of mint returned after a good rinse, though one corner had to rest for a while.",
        can_be_harmed=True,
        tags={"plants", "garden", "herbs"},
    ),
    "stones": Target(
        id="stones",
        label="stepping stones",
        the="the stepping stones",
        phrase="the stepping stones by the gate",
        living=False,
        delicate=0,
        reacts="did not change at all",
        after="The stones could be scrubbed later.",
        can_be_harmed=False,
        tags={"stones"},
    ),
}

SAFE_SUPPLIES = {
    "washable_paint": SafeSupply(
        id="washable_paint",
        label="washable paint",
        phrase="a tray of washable paint",
        use="the blue and yellow puddles mixed into a green clue path",
        tags={"paint"},
    ),
    "sidewalk_chalk": SafeSupply(
        id="sidewalk_chalk",
        label="sidewalk chalk",
        phrase="a box of sidewalk chalk",
        use="chalk arrows hopped from stone to stone without hurting anything",
        tags={"chalk"},
    ),
    "crayons": SafeSupply(
        id="crayons",
        label="crayons",
        phrase="a tin of crayons",
        use="the red crayon circled every clue in cheerful loops",
        tags={"crayons"},
    ),
    "markers": SafeSupply(
        id="markers",
        label="markers",
        phrase="a pack of chunky markers",
        use="the markers made bold footprints and bright question marks",
        tags={"markers"},
    ),
}

RESPONSES = {
    "hose_rinse": Response(
        id="hose_rinse",
        sense=3,
        power=3,
        text="turned on the hose, rinsed the {target} carefully, and moved the mystery bottle well out of reach",
        fail="rinsed the {target} quickly with the hose, but the chemical had already soaked in too long",
        qa_text="rinsed the plants right away with the hose and moved the bottle away",
        tags={"hose", "wash", "chemical"},
    ),
    "gloves_and_bag": Response(
        id="gloves_and_bag",
        sense=3,
        power=2,
        text="pulled on gloves, bagged the bottle, and washed the {target} with clean water",
        fail="bagged the bottle and washed the {target}, but the damage had already spread",
        qa_text="used gloves, put the bottle away, and washed the plants with clean water",
        tags={"gloves", "wash", "chemical"},
    ),
    "paper_towel": Response(
        id="paper_towel",
        sense=1,
        power=1,
        text="dabbed at the {target} with a paper towel",
        fail="dabbed at the {target} with a paper towel, which was far too little",
        qa_text="dabbed at the spill with a paper towel",
        tags={"wipe"},
    ),
}

GIRL_NAMES = ["Nina", "Lily", "Maya", "Zoe", "Ava", "Ruby", "Ella", "Ivy"]
BOY_NAMES = ["Owen", "Ben", "Max", "Theo", "Finn", "Leo", "Sam", "Eli"]
TRAITS = ["watchful", "careful", "cautious", "curious", "sensible", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for project_id in PROJECTS:
        for found_id, found in FOUND_ITEMS.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(found, target):
                    combos.append((project_id, found_id, target_id))
    return combos


@dataclass
class StoryParams:
    project: str
    found: str
    target: str
    supply1: str
    supply2: str
    response: str
    instigator: str
    instigator_gender: str
    friend: str
    friend_gender: str
    host: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    friend_age: int = 7
    relation: str = "friends"
    seed: Optional[int] = None


KNOWLEDGE = {
    "chemical": [
        (
            "Why should children leave mystery bottles alone?",
            "A mystery bottle might hold something strong or harmful instead of art supplies. If you do not know what it is, you should ask a grown-up and keep your hands away."
        )
    ],
    "warning_label": [
        (
            "What is a warning label for?",
            "A warning label gives a clue that something needs special care. It tells people to stop, look closely, and use the item the safe way."
        )
    ],
    "flowers": [
        (
            "Why can flowers be hurt by yard chemicals?",
            "Flowers are living plants with soft petals and leaves. Strong yard chemicals can burn or damage them because they are not made for play."
        )
    ],
    "plants": [
        (
            "Why should you rinse a plant if something unsafe spills on it?",
            "Rinsing with lots of clean water can wash some of the unsafe stuff away. A grown-up should do it quickly, because waiting gives the spill more time to hurt the plant."
        )
    ],
    "garden": [
        (
            "What can you use for safe backyard art?",
            "You can use things meant for children, like washable paint, chalk, crayons, or markers. Safe art supplies are made to color paper or pavement, not to treat weeds or bugs."
        )
    ],
    "hose": [
        (
            "What can a hose help with in a garden emergency?",
            "A hose can pour lots of clean water quickly. A grown-up may use it to rinse dirt or some spills off outdoor plants."
        )
    ],
    "gloves": [
        (
            "Why do grown-ups sometimes wear gloves for yard work?",
            "Gloves help protect hands from rough, dirty, or unsafe things. They are a sign that the job is not for bare little hands."
        )
    ],
    "chalk": [
        (
            "What is sidewalk chalk?",
            "Sidewalk chalk is a soft kind of color stick for drawing on pavement. It washes away with water and is made for play."
        )
    ],
    "paint": [
        (
            "What makes washable paint good for children's art?",
            "Washable paint is meant for art, so its colors are made to go on paper or other art surfaces. It is much safer for play than mystery liquids from a shed."
        )
    ],
    "crayons": [
        (
            "What are crayons used for?",
            "Crayons are colored wax sticks used for drawing and coloring pictures. They are made for art and are easy for children to hold."
        )
    ],
    "markers": [
        (
            "What are markers?",
            "Markers are pens filled with colored ink for drawing bold lines. Children's markers are made for paper, not for garden plants."
        )
    ],
}
KNOWLEDGE_ORDER = ["chemical", "warning_label", "flowers", "plants", "garden", "hose", "gloves", "chalk", "paint", "crayons", "markers"]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    found = f["found"]
    project = f["project"]
    target = f["target_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short whodunit-style story for a 3-to-5-year-old set in a friend\'s backyard that includes the words "art" and "scrounge". Two children find {found.label}, notice clues, and stop before using it.',
            f"Tell a gentle cautionary mystery where {a.id} wants to use {found.label} in {project.goal}, but {b.id} spots the clues and solves the case before anyone gets hurt.",
            f"Write a foreshadowing story in a friend's backyard where the real detective move is asking a grown-up before using a mystery bottle."
        ]
    if outcome == "spoiled":
        return [
            f'Write a cautionary backyard whodunit for a young child that includes "art" and "scrounge". A child mistakes {found.label} for paint, and {target.the} is harmed before the grown-up arrives.',
            f"Tell a mystery story where clues warn the children, but they ignore them and learn that not every colorful bottle belongs in an art project.",
            f"Write a sad but child-safe cautionary tale in a friend's backyard about why mystery yard supplies should never be used for art."
        ]
    return [
        f'Write a short whodunit-style story for a 3-to-5-year-old set in a friend\'s backyard that includes the words "art" and "scrounge". A child finds {found.label}, mistakes it for art supplies, and a grown-up fixes the problem.',
        f"Tell a foreshadowing backyard mystery where {a.id} and {b.id} are making art, the clues point to danger, and the real culprit is {found.label}.",
        f"Write a cautionary story with a safe ending where children learn to ask first and use real art supplies instead of mystery bottles."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    host = f["host"]
    found = f["found"]
    project = f["project"]
    target = f["target_cfg"]
    response = f["response"]
    s1, s2 = f["supplies"]
    pair = pair_noun(a, b)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, making art in a friend's backyard. {host.label_word.capitalize()} also matters because {host.pronoun()} understands the danger and helps."
        ),
        (
            "What were they making?",
            f"They were making {project.goal}. The detective-style art project is what made them want one more special color."
        ),
        (
            f"What did {a.id} scrounge up?",
            f"{a.id} scrounged up {found.phrase}. {a.pronoun().capitalize()} guessed it might help the art, but it was really a yard chemical."
        ),
        (
            "What clues warned them that the bottle was wrong?",
            f"The clues were that {found.clue1} and that {found.clue2}. {b.id} also noticed the sharp smell, which made the mystery feel less like paint and more like trouble."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"Why did they stop before using {found.label}?",
            f"They stopped because the clues finally made sense. The children realized that a real detective listens to warning signs and asks a grown-up instead of guessing."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely with {s1.phrase} and {s2.phrase}. They finished the art project using supplies meant for children, which proves they had learned from the clues."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"What happened when {a.id} used the mystery bottle?",
            f"{target.The} {target.reacts}. That revealed the culprit at once, because real paint would not make living plants react that way."
        ))
        qa.append((
            f"How did {host.label_word} help?",
            f"{host.label_word.capitalize()} {response.qa_text}. The quick help stopped a small mistake from turning into a bigger backyard problem."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that not every found object belongs in art. The case was solved when they understood that mystery yard supplies should be left for grown-ups."
        ))
    else:
        qa.append((
            f"Could {host.label_word} save everything?",
            f"No. {host.label_word.capitalize()} tried, but the damage had already gone too far. The clue came too late because the children used the bottle before asking."
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly and sadly, with the children leaving the damaged garden patch behind and making a smaller safe picture later. The ending shows that one careless guess can spoil more than the art."
        ))
        qa.append((
            "What is the warning in this story?",
            f"The warning is that mystery bottles are not part of children's art, even if they look interesting. Clues, labels, smells, and strange places are signs to stop and ask a grown-up first."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["found"].tags) | set(f["target_cfg"].tags) | {"garden"}
    outcome = f["outcome"]
    response = f["response"]
    if outcome != "averted":
        tags |= set(response.tags)
    for supply in f["supplies"]:
        if outcome != "spoiled" or supply.id == f["supplies"][0].id:
            tags |= set(supply.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("safe_art", ent.safe_art), ("risky", ent.risky), ("living", ent.living)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="mural",
        found="weed_spray",
        target="daisies",
        supply1="washable_paint",
        supply2="sidewalk_chalk",
        response="hose_rinse",
        instigator="Nina",
        instigator_gender="girl",
        friend="Owen",
        friend_gender="boy",
        host="mother",
        trait="watchful",
        delay=0,
        instigator_age=6,
        friend_age=8,
        relation="friends",
    ),
    StoryParams(
        project="map",
        found="wood_stain",
        target="tomatoes",
        supply1="markers",
        supply2="crayons",
        response="gloves_and_bag",
        instigator="Ben",
        instigator_gender="boy",
        friend="Maya",
        friend_gender="girl",
        host="father",
        trait="careful",
        delay=0,
        instigator_age=7,
        friend_age=7,
        relation="friends",
    ),
    StoryParams(
        project="posters",
        found="bug_powder",
        target="daisies",
        supply1="sidewalk_chalk",
        supply2="markers",
        response="gloves_and_bag",
        instigator="Ruby",
        instigator_gender="girl",
        friend="Finn",
        friend_gender="boy",
        host="mother",
        trait="curious",
        delay=2,
        instigator_age=6,
        friend_age=6,
        relation="friends",
    ),
    StoryParams(
        project="mural",
        found="wood_stain",
        target="herbs",
        supply1="washable_paint",
        supply2="crayons",
        response="hose_rinse",
        instigator="Theo",
        instigator_gender="boy",
        friend="Ava",
        friend_gender="girl",
        host="father",
        trait="sensible",
        delay=1,
        instigator_age=7,
        friend_age=7,
        relation="friends",
    ),
]


def explain_rejection(found: FoundItem, target: Target) -> str:
    if not target.can_be_harmed or not target.living:
        return (
            f"(No story: {found.label} is dangerous because it can hurt living garden things, but {target.the} are not living. "
            f"That would not make a strong cautionary mystery. Pick flowers, herbs, or vegetables instead.)"
        )
    return "(No story: this combination does not create a believable backyard hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the safer responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.friend_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "spoiled"


ASP_RULES = r"""
hazard(F, T) :- makes_mess(F), living(T), harmable(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, F, T) :- project(P), found(F), target(T), hazard(F, T).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_friend :- relation(friends), instigator_age(IA), friend_age(FA), FA > IA.
bonus(25) :- older_friend.
bonus(0) :- not older_friend.
authority(C + 10 + B) :- init_caution(C), bonus(B).
averted :- older_friend, authority(A), boldness_init(B), A > B.

severity(Dc + Delay) :- chosen_target(T), delicate(T, Dc), delay(Delay).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spoiled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PROJECTS:
        lines.append(asp.fact("project", pid))
    for fid, found in FOUND_ITEMS.items():
        lines.append(asp.fact("found", fid))
        if found.makes_mess:
            lines.append(asp.fact("makes_mess", fid))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if target.living:
            lines.append(asp.fact("living", tid))
        if target.can_be_harmed:
            lines.append(asp.fact("harmable", tid))
        lines.append(asp.fact("delicate", tid, target.delicate))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT * 10)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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

    py_sens = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sens)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(p)
        except StoryError:
            continue
    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not isinstance(sample.story, str):
            raise StoryError("Generated empty story during verify.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"VERIFY SMOKE FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Backyard art mystery storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--found", choices=FOUND_ITEMS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--host", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP and Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].can_be_harmed:
        found = FOUND_ITEMS[args.found] if args.found else next(iter(FOUND_ITEMS.values()))
        raise StoryError(explain_rejection(found, TARGETS[args.target]))
    if args.found and args.target:
        found = FOUND_ITEMS[args.found]
        target = TARGETS[args.target]
        if not hazard_at_risk(found, target):
            raise StoryError(explain_rejection(found, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.found is None or combo[1] == args.found)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, found_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    supply1, supply2 = rng.sample(sorted(SAFE_SUPPLIES), 2)
    instigator, instigator_gender = _pick_child(rng)
    friend, friend_gender = _pick_child(rng, avoid=instigator)
    host = args.host or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    instigator_age, friend_age = rng.sample([5, 6, 7, 8], 2)
    return StoryParams(
        project=project_id,
        found=found_id,
        target=target_id,
        supply1=supply1,
        supply2=supply2,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        friend=friend,
        friend_gender=friend_gender,
        host=host,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        friend_age=friend_age,
        relation="friends",
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project '{params.project}')")
    if params.found not in FOUND_ITEMS:
        raise StoryError(f"(Unknown found item '{params.found}')")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target '{params.target}')")
    if params.supply1 not in SAFE_SUPPLIES or params.supply2 not in SAFE_SUPPLIES:
        raise StoryError("(Unknown safe supply)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}')")
    if not hazard_at_risk(FOUND_ITEMS[params.found], TARGETS[params.target]):
        raise StoryError(explain_rejection(FOUND_ITEMS[params.found], TARGETS[params.target]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        project=PROJECTS[params.project],
        found=FOUND_ITEMS[params.found],
        target=TARGETS[params.target],
        supplies=(SAFE_SUPPLIES[params.supply1], SAFE_SUPPLIES[params.supply2]),
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        friend=params.friend,
        friend_gender=params.friend_gender,
        host_type=params.host,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        friend_age=params.friend_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, found, target) combos:\n")
        for project_id, found_id, target_id in combos:
            print(f"  {project_id:8} {found_id:12} {target_id}")
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
            header = f"### {p.instigator} & {p.friend}: {p.found} near {p.target} ({p.project}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
