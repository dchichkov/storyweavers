#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mechanic_penny_project_magic_humor_tall_tale.py
===========================================================================

A standalone story world about a child, a mechanic, a penny, and a school
project, told in a playful tall-tale voice with gentle magic and humor.

Premise
-------
A child brings a wobbling homemade project to a neighborhood mechanic. The child
trusts a lucky penny almost as much as the mechanic trusts a wrench. The world
model decides what kind of problem the project has, which repair is sensible,
and whether the lucky penny truly belongs in the fix or should simply cheer from
the toolbox.

The domain stays deliberately small and concrete:

* project kinds: a moon cart, a parade dragon, a wind wagon
* problems: loose wheel, sticky gear, tail-heavy balance
* fixes: tighten the wheel, oil the gear, or use the penny as a counterweight

A reasonableness gate refuses impossible repair combinations. The rendered prose
then exaggerates the action into a child-facing tall tale: the mechanic's shop
can sound like thunder in a teacup, the penny can wink like a tiny moon, and
the repaired project can roll as proudly as if it had borrowed a little magic.

Run it
------
    python storyworlds/worlds/gpt-5.4/mechanic_penny_project_magic_humor_tall_tale.py
    python storyworlds/worlds/gpt-5.4/mechanic_penny_project_magic_humor_tall_tale.py --project moon_cart --problem tail_heavy --fix penny_counterweight
    python storyworlds/worlds/gpt-5.4/mechanic_penny_project_magic_humor_tall_tale.py --problem sticky_gear --fix penny_counterweight
    python storyworlds/worlds/gpt-5.4/mechanic_penny_project_magic_humor_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/mechanic_penny_project_magic_humor_tall_tale.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/mechanic_penny_project_magic_humor_tall_tale.py --qa --json
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.label or self.type)


@dataclass
class ProjectKind:
    id: str
    label: str
    phrase: str
    boast: str
    opening: str
    ending: str
    motion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ProblemKind:
    id: str
    label: str
    warning: str
    symptom: str
    cause: str
    meter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixKind:
    id: str
    label: str
    method: str
    qa_text: str
    effect: str
    solves: set[str] = field(default_factory=set)
    uses_penny: bool = False
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


def _r_problem_to_failure(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    if project.meters["problem"] < THRESHOLD:
        return out
    kind = world.facts["problem_kind"]
    sig = ("problem_to_failure", kind.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if kind.meter == "wobble":
        project.meters["wobble"] += 1
    elif kind.meter == "drag":
        project.meters["drag"] += 1
    project.meters["stalled"] += 1
    project.memes["embarrassment"] += 1
    child = world.get("child")
    child.memes["worry"] += 1
    out.append("__problem__")
    return out


def _r_too_much_wobble(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    if project.meters["wobble"] < THRESHOLD:
        return out
    sig = ("too_much_wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["performance_loss"] += 1
    out.append("__wobble__")
    return out


def _r_too_much_drag(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    if project.meters["drag"] < THRESHOLD:
        return out
    sig = ("too_much_drag",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["performance_loss"] += 1
    out.append("__drag__")
    return out


def _r_repair_success(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    fix = world.facts.get("fix_kind")
    problem = world.facts.get("problem_kind")
    if project.meters["repair_attempt"] < THRESHOLD or not fix or not problem:
        return out
    sig = ("repair_success", fix.id, problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if problem.id in fix.solves:
        project.meters["problem"] = 0.0
        project.meters["wobble"] = 0.0
        project.meters["drag"] = 0.0
        project.meters["stalled"] = 0.0
        project.meters["performance_loss"] = 0.0
        project.meters["running"] += 1
        project.memes["pride"] += 1
        child = world.get("child")
        mechanic = world.get("mechanic")
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        mechanic.memes["satisfaction"] += 1
        out.append("__repaired__")
    return out


CAUSAL_RULES = [
    Rule(name="problem_to_failure", tag="physical", apply=_r_problem_to_failure),
    Rule(name="too_much_wobble", tag="physical", apply=_r_too_much_wobble),
    Rule(name="too_much_drag", tag="physical", apply=_r_too_much_drag),
    Rule(name="repair_success", tag="physical", apply=_r_repair_success),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for item in produced:
            if not item.startswith("__"):
                world.say(item)
    return produced


PROJECTS = {
    "moon_cart": ProjectKind(
        id="moon_cart",
        label="moon cart",
        phrase="a shoebox moon cart with bottle-cap wheels",
        boast="looked ready to deliver cookies to the moon and back before lunchtime",
        opening="The silver paper sides flashed whenever it turned.",
        ending="the moon cart rolled so straight it could have delivered toast to the stars",
        motion="rolled",
        tags={"wheel", "project"},
    ),
    "parade_dragon": ProjectKind(
        id="parade_dragon",
        label="parade dragon",
        phrase="a parade dragon on a painted wagon",
        boast="looked big enough to sneeze confetti over the whole street",
        opening="Its paper scales shivered whenever a breeze passed by.",
        ending="the parade dragon glided as proudly as if it expected applause from clouds",
        motion="glided",
        tags={"wheel", "project"},
    ),
    "wind_wagon": ProjectKind(
        id="wind_wagon",
        label="wind wagon",
        phrase="a wind wagon with a cardboard sail and clicking gears",
        boast="looked as if one puff could send it clear to Tuesday",
        opening="Its little sail leaned forward like it was in a hurry.",
        ending="the wind wagon hummed along as neatly as a tune on wheels",
        motion="hummed",
        tags={"gear", "project"},
    ),
}

PROBLEMS = {
    "loose_wheel": ProblemKind(
        id="loose_wheel",
        label="a loose wheel",
        warning="That wheel is wobbling like a jelly sandwich on skates.",
        symptom="one wheel flapped sideways instead of minding its manners",
        cause="The axle nut had wriggled loose.",
        meter="wobble",
        tags={"wheel", "repair"},
    ),
    "sticky_gear": ProblemKind(
        id="sticky_gear",
        label="a sticky gear",
        warning="That gear is chewing harder than a goat with a mouthful of buttons.",
        symptom="the little gear kept sticking and making a grumpy clicking noise",
        cause="Glue had dried where the teeth were supposed to turn freely.",
        meter="drag",
        tags={"gear", "repair"},
    ),
    "tail_heavy": ProblemKind(
        id="tail_heavy",
        label="a tail-heavy balance",
        warning="The back end is so heavy it thinks it is the boss.",
        symptom="the back sagged and the front kept hopping up",
        cause="Too much decoration had piled up on the rear end.",
        meter="wobble",
        tags={"balance", "repair"},
    ),
}

FIXES = {
    "tighten_wheel": FixKind(
        id="tighten_wheel",
        label="tighten the wheel nut",
        method="turned a small wrench exactly twice and snugged the wheel back into line",
        qa_text="tightened the wheel nut with a small wrench",
        effect="The wheel stopped flapping and began to behave like a proper wheel.",
        solves={"loose_wheel"},
        uses_penny=False,
        tags={"wrench", "repair"},
    ),
    "drop_of_oil": FixKind(
        id="drop_of_oil",
        label="add a drop of oil",
        method="touched the stubborn gear with one tiny drop of oil from a long-spouted can",
        qa_text="used a tiny drop of oil on the gear",
        effect="The gear gave one polite click and remembered how to turn.",
        solves={"sticky_gear"},
        uses_penny=False,
        tags={"oil", "repair"},
    ),
    "penny_counterweight": FixKind(
        id="penny_counterweight",
        label="use the penny as a counterweight",
        method="polished the lucky penny, tucked it under the nose, and fastened it there as a bright little counterweight",
        qa_text="fastened the lucky penny to the front as a counterweight",
        effect="The nose dipped just enough, and suddenly the whole machine balanced as if it had learned a magic trick",
        solves={"tail_heavy"},
        uses_penny=True,
        tags={"penny", "balance", "repair"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Lily", "Nora", "Ava", "Lucy", "Tess", "Poppy"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Theo", "Owen", "Jack"]
MECHANIC_NAMES = ["Rosa", "June", "Mabel", "Dot", "Hank", "Otis", "Gus", "Milo"]
CHILD_TRAITS = ["hopeful", "careful", "busy", "cheerful", "earnest", "bouncy"]
MECHANIC_TRAITS = ["calm", "funny", "nimble", "clever", "patient", "whistly"]


def fix_matches(problem_id: str, fix_id: str) -> bool:
    return problem_id in FIXES[fix_id].solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for project_id in PROJECTS:
        for problem_id in PROBLEMS:
            for fix_id in FIXES:
                if fix_matches(problem_id, fix_id):
                    combos.append((project_id, problem_id, fix_id))
    return combos


@dataclass
class StoryParams:
    project: str
    problem: str
    fix: str
    child_name: str
    child_gender: str
    mechanic_name: str
    mechanic_gender: str
    child_trait: str
    mechanic_trait: str
    penny_year: int
    seed: Optional[int] = None


def predict_failure(world: World) -> dict:
    sim = world.copy()
    project = sim.get("project")
    project.meters["problem"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("project").meters["wobble"],
        "drag": sim.get("project").meters["drag"],
        "stalled": sim.get("project").meters["stalled"],
    }


def opening_scene(world: World, child: Entity, mechanic: Entity, project: Entity,
                  penny: Entity, project_kind: ProjectKind) -> None:
    child.memes["hope"] += 1
    project.memes["pride"] += 1
    world.say(
        f"{child.id} carried {project_kind.phrase} into the little garage where {mechanic.id}, "
        f"the town mechanic, could listen to a sneeze in a wheel from half a block away."
    )
    world.say(
        f"It was {child.id}'s school project, and {project_kind.boast}. {project_kind.opening}"
    )
    world.say(
        f"In {child.pronoun('possessive')} pocket rode a lucky penny from {penny.attrs['year']}, "
        f"rubbed so bright it looked ready to wink at every tool in the shop."
    )


def test_run(world: World, child: Entity, project: Entity, project_kind: ProjectKind,
             problem_kind: ProblemKind) -> None:
    project.meters["problem"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Watch this!" said {child.id}. But when {child.pronoun()} gave the {project_kind.label} a gentle push, '
        f"{problem_kind.symptom}."
    )
    if project.meters["wobble"] >= THRESHOLD:
        world.say("It wiggled across the floor like a duck trying to dance in oversized boots.")
    if project.meters["drag"] >= THRESHOLD:
        world.say("It made a sound like a spoon arguing with a biscuit tin.")
    child.memes["worry"] += 1


def mechanic_warning(world: World, mechanic: Entity, project_kind: ProjectKind,
                     problem_kind: ProblemKind) -> None:
    pred = predict_failure(world)
    world.facts["predicted"] = pred
    extra = ""
    if pred["stalled"] >= THRESHOLD:
        extra = f" If we ignore it, that {project_kind.label} will stop before it can even {project_kind.motion} past your teacher's shoes."
    world.say(
        f'{mechanic.id} crouched down, tipped {mechanic.pronoun("possessive")} head, and said, '
        f'"{problem_kind.warning}{extra}"'
    )


def child_offer(world: World, child: Entity, penny: Entity, fix_kind: FixKind) -> None:
    if fix_kind.uses_penny:
        world.say(
            f'{child.id} held up the penny between two fingers. "Maybe my lucky penny wants a real job today," '
            f'{child.pronoun()} said.'
        )
    else:
        world.say(
            f'{child.id} held up the penny anyway. "It is very shiny," {child.pronoun()} said. '
            f'"If it cannot fix anything, maybe it can supervise."'
        )
    penny.memes["importance"] += 1


def perform_fix(world: World, mechanic: Entity, child: Entity, project: Entity,
                penny: Entity, fix_kind: FixKind) -> None:
    project.meters["repair_attempt"] += 1
    if fix_kind.uses_penny:
        penny.meters["attached"] += 1
        penny.memes["magic"] += 1
        world.say(
            f"{mechanic.id} grinned. In that shop, even a penny could apply for mechanic work."
        )
    else:
        penny.meters["watching"] += 1
        penny.memes["magic"] += 1
        world.say(
            f"{mechanic.id} set the penny on the toolbox lid to watch. It sat there so proudly it seemed to grow two invisible eyebrows."
        )
    mechanic.memes["focus"] += 1
    mechanic.memes["showmanship"] += 1
    world.say(
        f"Then {mechanic.pronoun()} {fix_kind.method}. The wrench gave a tiny ping, the oil can gave a tiny sigh, "
        f"and the whole garage seemed to lean closer, just in case a bit of magic wanted to happen."
    )
    propagate(world, narrate=False)
    world.say(fix_kind.effect + ".")


def second_run(world: World, child: Entity, mechanic: Entity, project_kind: ProjectKind,
               fix_kind: FixKind) -> None:
    project = world.get("project")
    if project.meters["running"] >= THRESHOLD:
        world.say(
            f'"Try it now," said {mechanic.id}. {child.id} gave the project another push, and {project_kind.ending}.'
        )
        if fix_kind.uses_penny:
            world.say(
                "The penny flashed on the front like a tiny brass moon that had decided to help with homework."
            )
        else:
            world.say(
                "From the toolbox, the penny gleamed as if it planned to brag about the whole thing later."
            )
    else:
        world.say(
            f'{child.id} tried again, but the poor project still looked confused.'
        )


def closing_lesson(world: World, child: Entity, mechanic: Entity, project_kind: ProjectKind,
                   fix_kind: FixKind, penny: Entity) -> None:
    child.memes["pride"] += 1
    child.memes["gratitude"] += 1
    if fix_kind.uses_penny:
        world.say(
            f'{child.id} laughed so hard {child.pronoun("possessive")} shoulders bounced. '
            f'"My school project got repaired by a mechanic and one brave penny," {child.pronoun()} said.'
        )
        world.say(
            f'{mechanic.id} wiped {mechanic.pronoun("possessive")} hands and bowed toward the coin. '
            f'"A good helper is still a helper, even if it only costs one cent."'
        )
    else:
        world.say(
            f'{child.id} tucked the penny back into {child.pronoun("possessive")} pocket. '
            f'"You did not fix it," {child.pronoun()} whispered to the coin, "but you were excellent company."'
        )
        world.say(
            f'{mechanic.id} chuckled. "{fix_kind.label.capitalize()} did the repair, but luck kept everybody smiling."'
        )
    world.say(
        f"When {child.id} carried the {project_kind.label} home, it no longer looked like a problem wearing craft paper. "
        f"It looked like a story with wheels, and maybe just a crumb of magic."
    )
    world.facts["penny_used"] = fix_kind.uses_penny
    world.facts["penny_attached"] = penny.meters["attached"] >= THRESHOLD
    world.facts["resolved"] = world.get("project").meters["running"] >= THRESHOLD


def tell(project_kind: ProjectKind, problem_kind: ProblemKind, fix_kind: FixKind,
         child_name: str, child_gender: str, mechanic_name: str, mechanic_gender: str,
         child_trait: str, mechanic_trait: str, penny_year: int) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        traits=[child_trait],
    ))
    mechanic = world.add(Entity(
        id=mechanic_name,
        kind="character",
        type=mechanic_gender,
        role="mechanic",
        label=mechanic_name,
        traits=[mechanic_trait],
    ))
    project = world.add(Entity(
        id="project",
        kind="thing",
        type="project",
        label=project_kind.label,
        phrase=project_kind.phrase,
        tags=set(project_kind.tags),
    ))
    penny = world.add(Entity(
        id="penny",
        kind="thing",
        type="coin",
        label="penny",
        phrase="a lucky penny",
        attrs={"year": penny_year},
        tags={"penny"},
    ))

    world.facts.update(
        child=child,
        mechanic=mechanic,
        project_kind=project_kind,
        problem_kind=problem_kind,
        fix_kind=fix_kind,
        penny=penny,
    )

    opening_scene(world, child, mechanic, project, penny, project_kind)
    world.para()
    test_run(world, child, project, project_kind, problem_kind)
    mechanic_warning(world, mechanic, project_kind, problem_kind)
    child_offer(world, child, penny, fix_kind)
    world.para()
    perform_fix(world, mechanic, child, project, penny, fix_kind)
    second_run(world, child, mechanic, project_kind, fix_kind)
    world.para()
    closing_lesson(world, child, mechanic, project_kind, fix_kind, penny)
    return world


KNOWLEDGE = {
    "mechanic": [
        (
            "What does a mechanic do?",
            "A mechanic fixes machines and moving parts when they are loose, stuck, or broken. Mechanics use tools and careful listening to figure out what a problem is."
        )
    ],
    "penny": [
        (
            "What is a penny?",
            "A penny is a small coin worth one cent. It is tiny, light, and easy to hold, but it can still be useful in simple little jobs."
        )
    ],
    "wheel": [
        (
            "Why is a loose wheel a problem?",
            "A loose wheel wobbles instead of rolling straight. That makes a project shaky and can stop it from moving the way it should."
        )
    ],
    "gear": [
        (
            "What happens when a gear gets sticky?",
            "A sticky gear cannot turn smoothly. The machine slows down or stops because the teeth do not move past each other easily."
        )
    ],
    "balance": [
        (
            "What is a counterweight?",
            "A counterweight is a small weight added in one place to help balance something heavy somewhere else. It helps a project sit or move more evenly."
        )
    ],
    "oil": [
        (
            "Why can a drop of oil help a stuck part?",
            "A tiny drop of oil can help moving parts slide more smoothly. That makes it easier for the parts to turn without scraping."
        )
    ],
    "wrench": [
        (
            "What does a wrench do?",
            "A wrench helps turn nuts and bolts so they can be tightened or loosened. It gives your hand a stronger grip on the part."
        )
    ],
    "project": [
        (
            "What is a school project?",
            "A school project is something you make or build to show what you learned. It can be simple, but it still works best when its parts are steady and careful."
        )
    ],
}
KNOWLEDGE_ORDER = ["mechanic", "project", "penny", "wheel", "gear", "balance", "oil", "wrench"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mechanic = f["mechanic"]
    project_kind = f["project_kind"]
    problem_kind = f["problem_kind"]
    fix_kind = f["fix_kind"]
    return [
        'Write a funny tall tale for a 3-to-5-year-old that includes the words "mechanic", "penny", and "project".',
        f"Tell a playful story where a child named {child.id} brings a homemade {project_kind.label} project to a mechanic because it has {problem_kind.label}.",
        f"Write a magical, humorous repair story where {mechanic.id} the mechanic uses {fix_kind.label} to help a school project and a lucky penny is part of the scene.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    mechanic = f["mechanic"]
    project_kind = f["project_kind"]
    problem_kind = f["problem_kind"]
    fix_kind = f["fix_kind"]
    penny = f["penny"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} school project, and {mechanic.id}, the mechanic who helped. A lucky penny came along too and felt important the whole time."
        ),
        (
            f"What was wrong with {child.id}'s project?",
            f"The project had {problem_kind.label}. {problem_kind.cause} That is why it would not move the way {child.id} hoped."
        ),
        (
            f"Why did {child.id} bring the project to the mechanic?",
            f"{child.id} brought the project to the mechanic because it was acting wrong during the test run. The mechanic could tell what kind of trouble the moving parts were causing."
        ),
        (
            f"How did {mechanic.id} fix the project?",
            f"{mechanic.id} {fix_kind.qa_text}. That matched the real problem, so the project could move smoothly again."
        ),
    ]
    if f.get("penny_used"):
        qa.append(
            (
                "How did the penny help?",
                f"The penny became part of the repair. It was attached to the front as a counterweight, which helped balance the project so it could roll properly."
            )
        )
    else:
        qa.append(
            (
                "Did the penny fix the project?",
                f"No. The penny did not do the mechanical repair, but it stayed nearby while {mechanic.id} worked. It still mattered in the story because it gave {child.id} a funny, hopeful feeling."
            )
        )
    if f.get("resolved"):
        qa.append(
            (
                "How did the story end?",
                f"The project worked at the end and moved the way it was supposed to. That happy ending showed that the right repair, not guessing, solved the trouble."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mechanic", "project", "penny"}
    problem = f["problem_kind"]
    fix = f["fix_kind"]
    if "wheel" in problem.tags:
        tags.add("wheel")
    if "gear" in problem.tags:
        tags.add("gear")
    if "balance" in problem.tags or "balance" in fix.tags:
        tags.add("balance")
    if "oil" in fix.tags:
        tags.add("oil")
    if "wrench" in fix.tags:
        tags.add("wrench")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="moon_cart",
        problem="tail_heavy",
        fix="penny_counterweight",
        child_name="Mia",
        child_gender="girl",
        mechanic_name="Gus",
        mechanic_gender="man",
        child_trait="hopeful",
        mechanic_trait="funny",
        penny_year=1998,
    ),
    StoryParams(
        project="parade_dragon",
        problem="loose_wheel",
        fix="tighten_wheel",
        child_name="Ben",
        child_gender="boy",
        mechanic_name="Rosa",
        mechanic_gender="woman",
        child_trait="cheerful",
        mechanic_trait="patient",
        penny_year=2004,
    ),
    StoryParams(
        project="wind_wagon",
        problem="sticky_gear",
        fix="drop_of_oil",
        child_name="Lily",
        child_gender="girl",
        mechanic_name="Otis",
        mechanic_gender="man",
        child_trait="earnest",
        mechanic_trait="clever",
        penny_year=2011,
    ),
]


def explain_rejection(problem_id: str, fix_id: str) -> str:
    problem = PROBLEMS[problem_id]
    fix = FIXES[fix_id]
    return (
        f"(No story: {fix.label} does not sensibly solve {problem.label}. "
        f"Pick a fix that matches the real problem instead of a random trick.)"
    )


ASP_RULES = r"""
problem(loose_wheel; sticky_gear; tail_heavy).
fix(tighten_wheel; drop_of_oil; penny_counterweight).

solves(loose_wheel, tighten_wheel).
solves(sticky_gear, drop_of_oil).
solves(tail_heavy, penny_counterweight).

valid(Project, Problem, Fix) :- project(Project), problem(Problem), fix(Fix), solves(Problem, Fix).

repaired :- chosen_problem(P), chosen_fix(F), solves(P, F).
outcome(repaired) :- repaired.
outcome(stuck) :- not repaired.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "repaired" if fix_matches(params.problem, params.fix) else "stuck"


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
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mechanic, a penny, and a funny little project."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--mechanic-name")
    ap.add_argument("--mechanic-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix and not fix_matches(args.problem, args.fix):
        raise StoryError(explain_rejection(args.problem, args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.problem is None or combo[1] == args.problem)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, problem_id, fix_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    mechanic_gender = args.mechanic_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    mechanic_name = args.mechanic_name or rng.choice(MECHANIC_NAMES)
    child_trait = rng.choice(CHILD_TRAITS)
    mechanic_trait = rng.choice(MECHANIC_TRAITS)
    penny_year = rng.randint(1985, 2018)

    return StoryParams(
        project=project_id,
        problem=problem_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=child_gender,
        mechanic_name=mechanic_name,
        mechanic_gender=mechanic_gender,
        child_trait=child_trait,
        mechanic_trait=mechanic_trait,
        penny_year=penny_year,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if not fix_matches(params.problem, params.fix):
        raise StoryError(explain_rejection(params.problem, params.fix))

    world = tell(
        project_kind=PROJECTS[params.project],
        problem_kind=PROBLEMS[params.problem],
        fix_kind=FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        mechanic_name=params.mechanic_name,
        mechanic_gender=params.mechanic_gender,
        child_trait=params.child_trait,
        mechanic_trait=params.mechanic_trait,
        penny_year=params.penny_year,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, problem, fix) combos:\n")
        for project_id, problem_id, fix_id in combos:
            print(f"  {project_id:14} {problem_id:12} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.project} / {p.problem} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
