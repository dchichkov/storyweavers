#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bureaucracy_fertile_ize_bravery_bad_ending_problem.py
================================================================================

A standalone story world about a brave child, a dry town patch, and a mountain
of stamps. The child must solve two linked problems before sunset: the ground
must be fed enough to fertile-ize it, and the town hall bureaucracy must be
navigated quickly enough to release the water wagon. In happy variants, the
child solves the paperwork puzzle and the patch grows something absurdly grand.
In bad-ending variants, the child is brave and tries hard, but the wrong plan
takes too long and the seed shrivels before help reaches it.

The style leans tall-tale: concrete, child-facing, and a little larger than life.

Run it
------
    python storyworlds/worlds/gpt-5.4/bureaucracy_fertile_ize_bravery_bad_ending_problem.py
    python storyworlds/worlds/gpt-5.4/bureaucracy_fertile_ize_bravery_bad_ending_problem.py --plot clay_square --amendment compost --plan checklist --helper mule
    python storyworlds/worlds/gpt-5.4/bureaucracy_fertile_ize_bravery_bad_ending_problem.py --plan shortcut
    python storyworlds/worlds/gpt-5.4/bureaucracy_fertile_ize_bravery_bad_ending_problem.py --all
    python storyworlds/worlds/gpt-5.4/bureaucracy_fertile_ize_bravery_bad_ending_problem.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/bureaucracy_fertile_ize_bravery_bad_ending_problem.py --qa --json
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
SENSE_MIN = 2
BRAVERY_INIT = 5.0


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
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Plot:
    id: str
    label: str
    place: str
    seed_name: str
    hungry: int
    thirsty: int
    load: int
    skyline: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Amendment:
    id: str
    label: str
    phrase: str
    verb: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    sense: int
    speed: int
    open_text: str
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    bonus: int
    carry_text: str
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


def _r_growth(world: World) -> list[str]:
    plot = world.entities.get("plot")
    seed = world.entities.get("seed")
    hero = world.entities.get("hero")
    if not plot or not seed or not hero:
        return []
    if plot.meters["fertile"] < THRESHOLD or plot.meters["watered"] < THRESHOLD:
        return []
    sig = ("growth",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seed.meters["sprouted"] += 1
    plot.meters["grown"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    return ["__growth__"]


def _r_shrivel(world: World) -> list[str]:
    plot = world.entities.get("plot")
    seed = world.entities.get("seed")
    hero = world.entities.get("hero")
    if not plot or not seed or not hero:
        return []
    if plot.meters["sunset"] < THRESHOLD or plot.meters["watered"] >= THRESHOLD:
        return []
    sig = ("shrivel",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seed.meters["shriveled"] += 1
    hero.memes["sadness"] += 1
    return ["__shrivel__"]


CAUSAL_RULES = [
    Rule(name="growth", tag="physical", apply=_r_growth),
    Rule(name="shrivel", tag="physical", apply=_r_shrivel),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combo(plot: Plot, amendment: Amendment, plan: Plan) -> bool:
    return amendment.power >= plot.hungry and plan.sense >= SENSE_MIN


def effective_speed(plan: Plan, helper: Helper) -> int:
    return plan.speed + helper.bonus


def succeeds(plot: Plot, amendment: Amendment, plan: Plan, helper: Helper) -> bool:
    return amendment.power >= plot.hungry and effective_speed(plan, helper) >= plot.load


def sensible_plans() -> list[Plan]:
    return [plan for plan in PLANS.values() if plan.sense >= SENSE_MIN]


def predict_outcome(world: World, plot: Plot, amendment: Amendment, plan: Plan, helper: Helper) -> dict:
    sim = world.copy()
    sim_plot = sim.get("plot")
    if amendment.power >= plot.hungry:
        sim_plot.meters["fertile"] += 1
    if effective_speed(plan, helper) >= plot.load:
        sim_plot.meters["watered"] += 1
    else:
        sim_plot.meters["sunset"] += 1
    propagate(sim, narrate=False)
    seed = sim.get("seed")
    return {
        "sprouted": seed.meters["sprouted"] >= THRESHOLD,
        "shriveled": seed.meters["shriveled"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, grownup: Entity, plot: Plot) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In the little town beyond {plot.skyline}, {hero.id} was the kind of child "
        f"who would walk straight toward a problem instead of around it. {hero.id}'s "
        f"{grownup.label_word} pointed at {plot.place} and said the town fair would soon "
        f"need one grand thing to show off."
    )
    world.say(
        f'At the far edge of the place lay {plot.label}, a patch so tired it looked as if '
        f"the wind had chewed on it all morning. In the middle sat one lonely {plot.seed_name} seed."
    )


def name_problem(world: World, hero: Entity, grownup: Entity, plot: Plot, amendment: Amendment) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'"That ground is hungry and thirsty," said {grownup.label_word}. '
        f'"If we want anything to grow, we have to fertile-ize it with {amendment.label} '
        f'and get water on it before sunset."'
    )
    world.say(
        "That would have been simple in most places, but this town loved forms the way ducks love ponds."
    )
    world.say(
        f"To borrow the town water wagon, a person had to pass through a tiny bureaucracy "
        f"of desks, windows, and stamp pads inside the brick town hall."
    )


def vow(world: World, hero: Entity, plot: Plot) -> None:
    hero.memes["bravery"] = BRAVERY_INIT
    world.say(
        f'{hero.id} squared {hero.pronoun("possessive")} shoulders and said, '
        f'"Then I will feed {plot.label} and fetch those stamps too."'
    )


def carry_amendment(world: World, hero: Entity, amendment: Amendment, helper: Helper, plot_ent: Entity) -> None:
    plot_ent.meters["fed"] += 1
    if amendment.power >= world.facts["plot_cfg"].hungry:
        plot_ent.meters["fertile"] += 1
        hero.memes["hope"] += 1
    world.say(
        f"{hero.id} and {helper.phrase} hauled {amendment.phrase} to the patch. "
        f"They {amendment.verb}, and the dirt drank it up as if it had been waiting all year."
    )


def enter_hall(world: World, hero: Entity, plan: Plan, plot: Plot) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then {hero.id} marched into town hall, where the line curled past {plot.load} little windows "
        f"and seemed to have enough elbows to fill a barn."
    )
    world.say(plan.open_text)


def solve_bureaucracy(world: World, hero: Entity, grownup: Entity, plan: Plan, helper: Helper, plot_ent: Entity) -> None:
    hero.memes["cleverness"] += 1
    hero.memes["bravery"] += 1
    if effective_speed(plan, helper) >= world.facts["plot_cfg"].load:
        plot_ent.meters["watered"] += 1
        world.say(plan.success_text.format(helper=helper.label, grownup=grownup.label_word))
    else:
        plot_ent.meters["sunset"] += 1
        world.say(plan.fail_text.format(helper=helper.label, grownup=grownup.label_word))


def giant_ending(world: World, hero: Entity, plot: Plot) -> None:
    world.say(
        f"By morning the seed had burst into a vine that ran over the fence, waved at the hens, "
        f"and looped once around the cider shed just for fun."
    )
    world.say(
        f"At the end of that vine sat a {plot.seed_name} so huge that children used its shadow for recess. "
        f"{hero.id} touched the warm rind and grinned, because bravery and good problem solving had turned a dead patch into a bragging patch."
    )


def bad_ending(world: World, hero: Entity, plot: Plot, grownup: Entity) -> None:
    world.say(
        f"But when {hero.id} came running back, the sun was already sliding behind {plot.skyline}, "
        f"and the thirsty ground had gone hard again."
    )
    world.say(
        f"The little {plot.seed_name} curled into a sad green comma. {grownup.label_word.capitalize()} put an arm around "
        f"{hero.id} and said being brave matters, but next time they would solve the stamp puzzle sooner and better."
    )


def tell(plot: Plot, amendment: Amendment, plan: Plan, helper: Helper,
         hero_name: str = "Maisie", hero_gender: str = "girl",
         grownup_type: str = "uncle") -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            label=hero_name,
            traits=["brave", "stubborn"],
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grown-up",
        )
    )
    plot_ent = world.add(
        Entity(
            id="plot",
            type="plot",
            label=plot.label,
            phrase=plot.place,
            tags=set(plot.tags),
        )
    )
    seed = world.add(
        Entity(
            id="seed",
            type="seed",
            label=plot.seed_name,
            phrase=f"a {plot.seed_name} seed",
        )
    )
    world.add(
        Entity(
            id="hall",
            type="hall",
            label="town hall",
            tags={"bureaucracy"},
        )
    )

    introduce(world, hero, grownup, plot)
    name_problem(world, hero, grownup, plot, amendment)
    vow(world, hero, plot)

    world.para()
    carry_amendment(world, hero, amendment, helper, plot_ent)
    enter_hall(world, hero, plan, plot)
    solve_bureaucracy(world, hero, grownup, plan, helper, plot_ent)
    propagate(world, narrate=False)

    world.para()
    if plot_ent.meters["watered"] >= THRESHOLD and plot_ent.meters["fertile"] >= THRESHOLD:
        giant_ending(world, hero, plot)
        outcome = "giant"
    else:
        bad_ending(world, hero, plot, grownup)
        outcome = "bad"

    world.facts.update(
        hero=hero,
        grownup=grownup,
        plot_cfg=plot,
        amendment=amendment,
        plan=plan,
        helper=helper,
        outcome=outcome,
        solved=plot_ent.meters["watered"] >= THRESHOLD,
        fertile=plot_ent.meters["fertile"] >= THRESHOLD,
    )
    return world


PLOTS = {
    "dust_lot": Plot(
        id="dust_lot",
        label="the dust lot",
        place="a flat lot behind the grain mill",
        seed_name="pumpkin",
        hungry=2,
        thirsty=1,
        load=2,
        skyline="the windmill",
        tags={"pumpkin", "soil"},
    ),
    "clay_square": Plot(
        id="clay_square",
        label="the clay square",
        place="a hard square beside the courthouse",
        seed_name="melon",
        hungry=3,
        thirsty=2,
        load=3,
        skyline="the courthouse roof",
        tags={"melon", "soil"},
    ),
    "sandy_patch": Plot(
        id="sandy_patch",
        label="the sandy patch",
        place="a pale patch near the river bend",
        seed_name="sunflower",
        hungry=2,
        thirsty=2,
        load=2,
        skyline="the cottonwoods",
        tags={"sunflower", "soil"},
    ),
}

AMENDMENTS = {
    "compost": Amendment(
        id="compost",
        label="compost",
        phrase="three barrows of crumbly compost",
        verb="spread it over the ground with wide, patient sweeps",
        power=3,
        tags={"compost", "soil"},
    ),
    "worm_castings": Amendment(
        id="worm_castings",
        label="worm castings",
        phrase="two sacks of black worm castings",
        verb="worked the castings into every crack in the ground",
        power=2,
        tags={"worms", "soil"},
    ),
    "seaweed_tea": Amendment(
        id="seaweed_tea",
        label="seaweed tea",
        phrase="a sloshing tub of seaweed tea",
        verb="splashed it on until the dirt smelled wild and green",
        power=2,
        tags={"seaweed", "soil"},
    ),
}

PLANS = {
    "checklist": Plan(
        id="checklist",
        label="the checklist plan",
        sense=3,
        speed=2,
        open_text=(
            "Instead of guessing, the child asked the head clerk for one clear checklist and read it top to bottom."
        ),
        success_text=(
            "With the list in hand and {helper} moving quick, every form found the right window, every window got its stamp, "
            "and the water wagon rolled out before the shadows grew long."
        ),
        fail_text=(
            "The list helped, but even with {helper} hustling, one last stamp sat behind a shut window until the shadows grew long."
        ),
        qa_text="asked for one clear checklist and followed it from window to window",
        tags={"bureaucracy", "checklist"},
    ),
    "stamp_train": Plan(
        id="stamp_train",
        label="the stamp-train plan",
        sense=3,
        speed=3,
        open_text=(
            "The child lined the forms in order on a bench, made a little paper train out of them, and pushed that train from window to window so no stamp was missed."
        ),
        success_text=(
            "The paper train kept the whole job straight. Soon the last clerk thumped the final stamp, and the water wagon clattered out behind {helper} like a metal pony."
        ),
        fail_text=(
            "The paper train was clever, but the line still crept slower than syrup, and the water wagon stayed chained until sunset."
        ),
        qa_text="put the forms in order like a little train so the stamps came in the right sequence",
        tags={"bureaucracy", "stamps"},
    ),
    "polite_queue": Plan(
        id="polite_queue",
        label="the polite-queue plan",
        sense=2,
        speed=1,
        open_text=(
            "The child stood nicely in each line and did everything in perfect order, even when the order took forever."
        ),
        success_text=(
            "Patience worked at last, and the final clerk nodded {helper} through with the water wagon keys."
        ),
        fail_text=(
            "Patience kept everyone friendly, but the lines ate the afternoon one bite at a time, and the water wagon never left the shed."
        ),
        qa_text="waited politely in every line and followed the official order",
        tags={"bureaucracy", "patience"},
    ),
    "shortcut": Plan(
        id="shortcut",
        label="the shortcut plan",
        sense=1,
        speed=1,
        open_text=(
            "The child nearly tried to skip three windows at once and wave a blank form like a flag."
        ),
        success_text=(
            "By pure luck, the skipped steps did not matter this time, and the wagon came out anyway."
        ),
        fail_text=(
            "The skipped windows only woke the grumpiest clerk in the building, and the forms were sent all the way back to the first desk."
        ),
        qa_text="tried to skip the official steps",
        tags={"bureaucracy", "mistake"},
    ),
}

HELPERS = {
    "mule": Helper(
        id="mule",
        label="a bell-wearing mule",
        phrase="a bell-wearing mule named Tumble",
        bonus=1,
        carry_text="hauled the load without complaining once",
        tags={"mule"},
    ),
    "clerk": Helper(
        id="clerk",
        label="a speedy clerk",
        phrase="a speedy clerk named Miss Junie",
        bonus=1,
        carry_text="pointed to the next right window before the ink dried",
        tags={"clerk", "bureaucracy"},
    ),
    "wagon": Helper(
        id="wagon",
        label="a red wagon",
        phrase="a squeaky red wagon",
        bonus=0,
        carry_text="bumped along behind like a faithful tin dog",
        tags={"wagon"},
    ),
}

GIRL_NAMES = ["Maisie", "Tess", "Lula", "Nell", "Poppy", "June", "Mabel", "Ada"]
BOY_NAMES = ["Jeb", "Clem", "Otis", "Roy", "Beau", "Wade", "Eli", "Finn"]


@dataclass
class StoryParams:
    plot: str
    amendment: str
    plan: str
    helper: str
    hero: str
    gender: str
    grownup: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bureaucracy": [
        (
            "What is bureaucracy?",
            "Bureaucracy is a system with lots of official steps, forms, and rules. It can help keep things organized, but it can also make simple jobs take a long time.",
        )
    ],
    "soil": [
        (
            "Why do plants need good soil?",
            "Good soil holds water and food for roots. When soil is tired or hard, plants have a much harder time growing strong.",
        )
    ],
    "compost": [
        (
            "What does compost do for soil?",
            "Compost adds old plant bits back into the ground. That helps the soil hold water and feed new plants.",
        )
    ],
    "worms": [
        (
            "Why are worm castings good for a garden?",
            "Worm castings are tiny bits of digested soil and plant matter. They help fertile-ize the ground by adding food and helping roots grow.",
        )
    ],
    "seaweed": [
        (
            "What is seaweed tea for plants?",
            "Seaweed tea is a plant food made by soaking sea plants in water. Gardeners use it to give the soil extra goodness.",
        )
    ],
    "stamps": [
        (
            "Why do forms sometimes need stamps?",
            "A stamp on a form shows that an office checked one step and approved it. That way the next person knows the paper is ready.",
        )
    ],
    "checklist": [
        (
            "Why is a checklist useful?",
            "A checklist helps you remember the steps of a job in the right order. It is a good problem-solving tool when a task has many parts.",
        )
    ],
    "patience": [
        (
            "Why is patience helpful?",
            "Patience helps you stay calm while something takes time. But sometimes patience works best when you also have a smart plan.",
        )
    ],
    "pumpkin": [
        (
            "Can pumpkins grow very big?",
            "Yes. With rich soil, water, sunshine, and lots of care, pumpkins can grow surprisingly large.",
        )
    ],
    "melon": [
        (
            "What does a melon plant need?",
            "A melon plant needs warmth, water, sunlight, and healthy soil. If the ground dries out too soon, the plant may not grow well.",
        )
    ],
    "sunflower": [
        (
            "Why do sunflowers like sunlight?",
            "Sunflowers use sunlight to make food in their leaves. That energy helps them grow tall and make big flower heads.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "bureaucracy",
    "soil",
    "compost",
    "worms",
    "seaweed",
    "stamps",
    "checklist",
    "patience",
    "pumpkin",
    "melon",
    "sunflower",
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for plot_id, plot in PLOTS.items():
        for amendment_id, amendment in AMENDMENTS.items():
            for plan_id, plan in PLANS.items():
                if not valid_combo(plot, amendment, plan):
                    continue
                for helper_id in HELPERS:
                    combos.append((plot_id, amendment_id, plan_id, helper_id))
    return combos


def explain_rejection(plot: Plot, amendment: Amendment, plan: Plan) -> str:
    if amendment.power < plot.hungry:
        return (
            f"(No story: {amendment.label} is too weak to fertile-ize {plot.label}. "
            f"The patch is too hungry for that fix, so the world refuses the combo.)"
        )
    if plan.sense < SENSE_MIN:
        return (
            f"(No story: '{plan.id}' is not sensible enough for this world "
            f"(sense={plan.sense} < {SENSE_MIN}). A good problem-solving story should prefer a real plan.)"
        )
    return "(No story: this combination is unreasonable.)"


def outcome_of(params: StoryParams) -> str:
    plot = PLOTS[params.plot]
    amendment = AMENDMENTS[params.amendment]
    plan = PLANS[params.plan]
    helper = HELPERS[params.helper]
    return "giant" if succeeds(plot, amendment, plan, helper) else "bad"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    plot = f["plot_cfg"]
    amendment = f["amendment"]
    plan = f["plan"]
    outcome = f["outcome"]
    base = (
        f'Write a tall-tale story for a young child that uses the words "bureaucracy" and "fertile-ize". '
        f"The hero is a brave {hero.type} named {hero.id} trying to save {plot.label} with {amendment.label}."
    )
    if outcome == "giant":
        return [
            base,
            f"Tell a story where {hero.id} solves a stamp-filled town-hall problem by using {plan.label}, "
            f"gets water to the ground in time, and a giant {plot.seed_name} proves the plan worked.",
            f"Write a playful tall tale about bravery and problem solving in which a dry patch becomes a bragging patch.",
        ]
    return [
        base,
        f"Tell a story where {hero.id} is brave but the paperwork plan is too slow, so the seed dries up before help arrives.",
        f"Write a tall tale with a bad ending that still teaches problem solving: the child tries hard, but the wrong plan loses the race with sunset.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    grownup = f["grownup"]
    plot = f["plot_cfg"]
    amendment = f["amendment"]
    plan = f["plan"]
    helper = f["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a brave child, and {hero.pronoun('possessive')} {grownup.label_word}. "
            f"They are trying to save {plot.label} before sunset.",
        ),
        (
            "What was the big problem?",
            f"The ground was too hungry and thirsty for the {plot.seed_name} seed. "
            f"They had to fertile-ize the soil with {amendment.label} and get through the town hall bureaucracy to borrow water.",
        ),
        (
            f"What brave thing did {hero.id} do?",
            f"{hero.id} did not run away from the hard job. "
            f"{hero.pronoun().capitalize()} carried soil food to the patch and then walked straight into town hall to face the stamps and lines.",
        ),
        (
            "How did they try to solve the paperwork problem?",
            f"They used {plan.label}. {plan.qa_text.capitalize()}, which was their way of solving the many-step office problem instead of guessing.",
        ),
    ]
    if f["outcome"] == "giant":
        qa.append(
            (
                "Why did the patch grow at the end?",
                f"The soil got enough plant food and the water wagon arrived in time. "
                f"Because both problems were solved, the seed could sprout and grow huge.",
            )
        )
        qa.append(
            (
                f"How did {helper.label} help?",
                f"{helper.label.capitalize()} made the work faster. "
                f"That extra help mattered because the race was really against the clock and the office line.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a giant {plot.seed_name} growing so big it became a town wonder. "
                f"The ending image shows that brave problem solving changed the patch from dead and dry to rich and thriving.",
            )
        )
    else:
        qa.append(
            (
                "Why was the ending sad?",
                f"The child was brave, but the water did not reach the patch before sunset. "
                f"Without water in time, the little {plot.seed_name} seed shriveled instead of growing.",
            )
        )
        qa.append(
            (
                "Did bravery matter even in the bad ending?",
                f"Yes. {hero.id} still faced the hard work and tried to solve the problem honestly. "
                f"The sad ending shows that bravery is important, but a good plan has to be quick and sensible too.",
            )
        )
        qa.append(
            (
                "What did they learn for next time?",
                f"They learned to solve the stamp puzzle sooner and choose a stronger plan. "
                f"The lesson comes from seeing how a slow solution let the sunset win.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"bureaucracy", "soil"}
    plot = world.facts["plot_cfg"]
    amendment = world.facts["amendment"]
    plan = world.facts["plan"]
    tags |= set(plot.tags)
    tags |= set(amendment.tags)
    tags |= set(plan.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        plot="dust_lot",
        amendment="compost",
        plan="stamp_train",
        helper="mule",
        hero="Maisie",
        gender="girl",
        grownup="uncle",
    ),
    StoryParams(
        plot="clay_square",
        amendment="compost",
        plan="checklist",
        helper="clerk",
        hero="Jeb",
        gender="boy",
        grownup="aunt",
    ),
    StoryParams(
        plot="sandy_patch",
        amendment="worm_castings",
        plan="polite_queue",
        helper="wagon",
        hero="Tess",
        gender="girl",
        grownup="father",
    ),
    StoryParams(
        plot="clay_square",
        amendment="compost",
        plan="polite_queue",
        helper="wagon",
        hero="Roy",
        gender="boy",
        grownup="mother",
    ),
]


ASP_RULES = r"""
strong_enough(A, P) :- amendment(A), plot(P), amend_power(A, AP), hunger(P, H), AP >= H.
sensible_plan(Pl) :- plan(Pl), sense(Pl, S), sense_min(M), S >= M.

valid(P, A, Pl, H) :- plot(P), amendment(A), plan(Pl), helper(H), strong_enough(A, P), sensible_plan(Pl).

effective_speed(Pl, H, Sp + B) :- plan_speed(Pl, Sp), helper_bonus(H, B).
success(P, A, Pl, H) :- valid(P, A, Pl, H), effective_speed(Pl, H, E), load(P, L), E >= L.

outcome(P, A, Pl, H, giant) :- success(P, A, Pl, H).
outcome(P, A, Pl, H, bad) :- valid(P, A, Pl, H), not success(P, A, Pl, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for plot_id, plot in PLOTS.items():
        lines.append(asp.fact("plot", plot_id))
        lines.append(asp.fact("hunger", plot_id, plot.hungry))
        lines.append(asp.fact("load", plot_id, plot.load))
    for amendment_id, amendment in AMENDMENTS.items():
        lines.append(asp.fact("amendment", amendment_id))
        lines.append(asp.fact("amend_power", amendment_id, amendment.power))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("plan_speed", plan_id, plan.speed))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_bonus", helper_id, helper.bonus))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_plot", params.plot),
            asp.fact("chosen_amendment", params.amendment),
            asp.fact("chosen_plan", params.plan),
            asp.fact("chosen_helper", params.helper),
            "picked_outcome(O) :- chosen_plot(P), chosen_amendment(A), chosen_plan(Pl), chosen_helper(H), outcome(P, A, Pl, H, O).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
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

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale story world: a brave child, a dry patch, and too many stamps."
    )
    ap.add_argument("--plot", choices=sorted(PLOTS))
    ap.add_argument("--amendment", choices=sorted(AMENDMENTS))
    ap.add_argument("--plan", choices=sorted(PLANS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plot and args.amendment and args.plan:
        plot = PLOTS[args.plot]
        amendment = AMENDMENTS[args.amendment]
        plan = PLANS[args.plan]
        if not valid_combo(plot, amendment, plan):
            raise StoryError(explain_rejection(plot, amendment, plan))
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        plot = PLOTS[args.plot] if args.plot else next(iter(PLOTS.values()))
        amendment = AMENDMENTS[args.amendment] if args.amendment else next(iter(AMENDMENTS.values()))
        raise StoryError(explain_rejection(plot, amendment, PLANS[args.plan]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.plot is None or combo[0] == args.plot)
        and (args.amendment is None or combo[1] == args.amendment)
        and (args.plan is None or combo[2] == args.plan)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    plot_id, amendment_id, plan_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        plot=plot_id,
        amendment=amendment_id,
        plan=plan_id,
        helper=helper_id,
        hero=hero,
        gender=gender,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    if params.plot not in PLOTS:
        raise StoryError(f"(Unknown plot: {params.plot})")
    if params.amendment not in AMENDMENTS:
        raise StoryError(f"(Unknown amendment: {params.amendment})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    plot = PLOTS[params.plot]
    amendment = AMENDMENTS[params.amendment]
    plan = PLANS[params.plan]
    helper = HELPERS[params.helper]
    if not valid_combo(plot, amendment, plan):
        raise StoryError(explain_rejection(plot, amendment, plan))

    world = tell(
        plot=plot,
        amendment=amendment,
        plan=plan,
        helper=helper,
        hero_name=params.hero,
        hero_gender=params.gender,
        grownup_type=params.grownup,
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (plot, amendment, plan, helper) combos:\n")
        for plot, amendment, plan, helper in combos:
            print(f"  {plot:12} {amendment:14} {plan:12} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.plot} with {p.amendment} ({p.plan}, {outcome_of(p)})"
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
