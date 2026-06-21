#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dominant_reconciliation_slice_of_life.py
===================================================================

A small slice-of-life story world about a child who becomes too dominant during a
shared home project, notices the hurt it causes, and reconciles with the other
child by making room for both sets of hands.

This world models:
- typed entities with physical meters and emotional memes,
- a simple forward-chaining causal engine,
- a reasonableness gate for project/repair-plan compatibility,
- an inline ASP twin that matches the Python gate and outcome model,
- story-grounded Q&A built from world state rather than parsing English.

Run it
------
    python storyworlds/worlds/gpt-5.4/dominant_reconciliation_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/dominant_reconciliation_slice_of_life.py --project cookies
    python storyworlds/worlds/gpt-5.4/dominant_reconciliation_slice_of_life.py --plan let_finish
    python storyworlds/worlds/gpt-5.4/dominant_reconciliation_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/dominant_reconciliation_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dominant_reconciliation_slice_of_life.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Project:
    id: str
    place: str
    scene: str
    object_label: str
    opening: str
    material: str
    task1: str
    task2: str
    finish_good: str
    finish_small: str
    strain: int
    modes: set[str] = field(default_factory=set)
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
class Plan:
    id: str
    mode: str
    sense: int
    power: int
    title: str
    offer: str
    do_text: str
    fail_text: str
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


def _r_hurt_from_hogging(world: World) -> list[str]:
    dominant = world.get("dominant")
    partner = world.get("partner")
    project = world.get("project")
    if dominant.meters["hogging"] < THRESHOLD:
        return []
    sig = ("hurt_from_hogging",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    partner.memes["hurt"] += 1
    partner.memes["left_out"] += 1
    project.meters["strain"] += 1
    return ["__hurt__"]


def _r_stall_project(world: World) -> list[str]:
    project = world.get("project")
    if project.meters["strain"] < THRESHOLD:
        return []
    sig = ("stall_project",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    project.meters["stalled"] += 1
    world.get("dominant").memes["uneasy"] += 1
    return ["__stall__"]


def _r_repair_bond(world: World) -> list[str]:
    dominant = world.get("dominant")
    partner = world.get("partner")
    project = world.get("project")
    if dominant.memes["apology"] < THRESHOLD or project.meters["sharing"] < THRESHOLD:
        return []
    sig = ("repair_bond",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dominant.memes["relief"] += 1
    partner.memes["relief"] += 1
    dominant.memes["closeness"] += 1
    partner.memes["closeness"] += 1
    partner.memes["hurt"] = 0.0
    partner.memes["left_out"] = 0.0
    dominant.memes["guilt"] = 0.0
    project.meters["stalled"] = 0.0
    return ["__repair__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt_from_hogging", tag="social", apply=_r_hurt_from_hogging),
    Rule(name="stall_project", tag="physical", apply=_r_stall_project),
    Rule(name="repair_bond", tag="social", apply=_r_repair_bond),
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


def compatible(project: Project, plan: Plan) -> bool:
    return plan.mode in project.modes


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def project_pressure(project: Project, delay: int) -> int:
    return project.strain + delay


def repaired_enough(plan: Plan, project: Project, delay: int) -> bool:
    return plan.power >= project_pressure(project, delay)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, project in PROJECTS.items():
        for plan_id, plan in PLANS.items():
            if compatible(project, plan) and plan.sense >= SENSE_MIN:
                combos.append((pid, plan_id))
    return sorted(combos)


def _do_hog(world: World, narrate: bool = True) -> None:
    dominant = world.get("dominant")
    project = world.get("project")
    dominant.meters["hogging"] += 1
    project.meters["progress"] += 1
    propagate(world, narrate=narrate)


def predict_stall(world: World) -> dict:
    sim = world.copy()
    _do_hog(sim, narrate=False)
    return {
        "stalled": sim.get("project").meters["stalled"] >= THRESHOLD,
        "hurt": sim.get("partner").memes["hurt"] >= THRESHOLD,
        "strain": sim.get("project").meters["strain"],
    }


def introduce(world: World, dominant: Entity, partner: Entity, relation: str,
              project: Project) -> None:
    pair = "siblings" if relation == "siblings" else "friends"
    world.say(
        f"After breakfast, {dominant.id} and {partner.id} settled in {project.place} to make {project.object_label} together."
    )
    world.say(project.opening)
    world.say(
        f"They were {pair}, used to the small music of ordinary mornings: chairs scraping, paper rustling, and someone always asking for one more bit of help."
    )


def project_need(world: World, project: Project) -> None:
    world.say(
        f"This was the kind of job that worked best with two sets of hands. One person could {project.task1}, while the other could {project.task2}."
    )


def take_over(world: World, dominant: Entity, partner: Entity, project: Project) -> None:
    dominant.memes["eagerness"] += 1
    world.say(
        f"But {dominant.id} got excited and reached for the {project.material} first, then kept reaching for it again."
    )
    world.say(
        f'"I know how to do it," {dominant.pronoun()} said, voice turning too dominant for such a small room.'
    )
    world.say(
        f"{partner.id} tried to move in beside {dominant.pronoun('object')}, but there was hardly any space left at the work."
    )
    _do_hog(world, narrate=False)


def notice_hurt(world: World, dominant: Entity, partner: Entity, project: Project,
                adult: Entity) -> str:
    pred = predict_stall(world)
    world.facts["predicted_hurt"] = pred["hurt"]
    world.facts["predicted_stall"] = pred["stalled"]
    world.facts["predicted_strain"] = pred["strain"]
    partner.memes["quiet"] += 1
    if pred["stalled"]:
        world.say(
            f"Soon the whole thing felt wrong. {project.scene} slowed down, and {partner.id} drew {partner.pronoun('possessive')} hands back into {partner.pronoun('possessive')} lap."
        )
    world.say(
        f'{partner.id} looked down and said, "There is no room for me."'
    )
    if adult.attrs.get("mediates"):
        world.say(
            f"{adult.label_word.capitalize()} was wiping the counter nearby and heard the change in the room before anyone said more."
        )
        return "adult"
    world.say(
        f"{dominant.id} looked up at {partner.id}'s face and finally saw the hurt there."
    )
    return "self"


def apology(world: World, dominant: Entity, partner: Entity, source: str) -> None:
    dominant.memes["guilt"] += 1
    dominant.memes["apology"] += 1
    if source == "adult":
        world.say(
            f'"You do not have to be the only one doing it," {world.get("adult").label_word} said gently. "Making room is part of making it together."'
        )
    world.say(
        f'{dominant.id} let go of the work for a moment. "I am sorry," {dominant.pronoun()} said. "I was acting like it had to be my way."'
    )
    world.say(
        f"{partner.id} gave a small nod, still watching to see if the room would really change."
    )


def share_with_plan(world: World, dominant: Entity, partner: Entity, project: Project,
                    plan: Plan, adult: Entity, outcome: str) -> None:
    project.meters["sharing"] += 1
    project.meters["progress"] += 1
    propagate(world, narrate=False)
    if adult.attrs.get("mediates"):
        lead = f"{adult.label_word.capitalize()} smiled and {plan.offer}"
    else:
        lead = f"{dominant.id} took a breath and {plan.offer}"
    world.say(f"{lead}.")
    if outcome == "repaired":
        world.say(plan.do_text.format(
            dominant=dominant.id,
            partner=partner.id,
            task1=project.task1,
            task2=project.task2,
            object_label=project.object_label,
            material=project.material,
        ))
    else:
        world.say(plan.fail_text.format(
            dominant=dominant.id,
            partner=partner.id,
            task1=project.task1,
            task2=project.task2,
            object_label=project.object_label,
            material=project.material,
        ))


def ending(world: World, dominant: Entity, partner: Entity, project: Project,
           outcome: str) -> None:
    dominant.memes["joy"] += 1
    partner.memes["joy"] += 1
    if outcome == "repaired":
        world.say(project.finish_good.format(
            dominant=dominant.id,
            partner=partner.id,
        ))
    else:
        world.say(project.finish_small.format(
            dominant=dominant.id,
            partner=partner.id,
        ))
    world.say(
        f"By the end, the work on the table mattered less than the feeling between them. {partner.id} leaned close again, and this time {dominant.id} shifted over without being asked."
    )


def tell(project: Project, plan: Plan, dominant_name: str = "Nora",
         dominant_gender: str = "girl", partner_name: str = "Ben",
         partner_gender: str = "boy", relation: str = "siblings",
         partner_trait: str = "patient", adult_type: str = "mother",
         delay: int = 0, dominant_age: int = 7, partner_age: int = 6,
         adult_present: bool = True) -> World:
    world = World()
    dominant = world.add(Entity(
        id=dominant_name,
        kind="character",
        type=dominant_gender,
        role="dominant",
        age=dominant_age,
        traits=["quick", "confident"],
        attrs={"relation": relation},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        age=partner_age,
        traits=[partner_trait],
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
        attrs={"mediates": adult_present},
    ))
    project_ent = world.add(Entity(
        id="project",
        kind="thing",
        type="project",
        label=project.object_label,
        attrs={"project_id": project.id},
    ))

    dominant.memes["closeness"] = 1.0
    partner.memes["closeness"] = 1.0
    partner.memes["trust"] = 1.0
    project_ent.meters["progress"] = 0.0
    project_ent.meters["strain"] = 0.0
    project_ent.meters["stalled"] = 0.0
    project_ent.meters["sharing"] = 0.0
    world.facts["adult_present"] = adult_present
    world.facts["delay"] = delay
    world.facts["project_cfg"] = project
    world.facts["plan_cfg"] = plan
    world.facts["relation"] = relation

    introduce(world, dominant, partner, relation, project)
    project_need(world, project)

    world.para()
    take_over(world, dominant, partner, project)
    source = notice_hurt(world, dominant, partner, project, adult)

    for _ in range(delay):
        project_ent.meters["strain"] += 1
        project_ent.meters["progress"] += 0.5

    world.para()
    apology(world, dominant, partner, source)
    outcome = "repaired" if repaired_enough(plan, project, delay) else "restarted"
    share_with_plan(world, dominant, partner, project, plan, adult, outcome)

    world.para()
    ending(world, dominant, partner, project, outcome)

    world.facts.update(
        dominant=dominant,
        partner=partner,
        adult=adult,
        project=project_ent,
        source=source,
        outcome=outcome,
        pressure=project_pressure(project, delay),
        reconciled=dominant.memes["closeness"] >= THRESHOLD and partner.memes["closeness"] >= THRESHOLD,
    )
    return world


PROJECTS = {
    "cookies": Project(
        id="cookies",
        place="the warm kitchen",
        scene="the bowl and tray",
        object_label="a batch of cinnamon cookies",
        opening="A bowl waited on the table, flour already dusting the edge like a little ring of snow.",
        material="big wooden spoon",
        task1="measure the sugar",
        task2="stir the bowl",
        finish_good="{dominant} slid the tray in while {partner} set the timer, and later the kitchen smelled sweet and full. They ate the first warm cookie shoulder to shoulder at the table.",
        finish_small="The first bowl had gone too far, so they started a smaller second batch together. Soon two neat cookies sat on a plate between them, and both children laughed when the cinnamon sugar stuck to their lips.",
        strain=2,
        modes={"split"},
        tags={"cookies", "kitchen", "apology"},
    ),
    "fort": Project(
        id="fort",
        place="the living room",
        scene="the blankets and chairs",
        object_label="a blanket fort",
        opening="A sofa cushion leaned against one chair, and a blanket puddled on the rug while they planned where the roof should go.",
        material="last big chair",
        task1="hold the blanket edge high",
        task2="clip the corners in place",
        finish_good="When they were done, the fort stood wide enough for both of them and a flashlight glowing on the floor. {dominant} and {partner} crawled inside together and listened to the quiet cloth roof breathe above them.",
        finish_small="The tall fort they first imagined would not hold, so they made a smaller tent by the sofa instead. It was just big enough for two pillows, two children, and one shared whispering space.",
        strain=2,
        modes={"split", "turns"},
        tags={"fort", "home", "sharing"},
    ),
    "garden": Project(
        id="garden",
        place="the balcony",
        scene="the soil box and seed packet",
        object_label="a little window-box garden",
        opening="The seed packet crackled in the light breeze, and a row of empty spots waited in the dark soil.",
        material="small blue trowel",
        task1="dig little holes",
        task2="drop in the seeds",
        finish_good="{dominant} dug while {partner} dropped seeds into each little hole, and together they patted the soil smooth. By the window that evening, the box looked tidy and hopeful, with both of their fingerprints in the earth.",
        finish_small="The first row had turned messy, so they smoothed one corner and planted a smaller, careful line together. It looked humble and true, the kind of start that could still grow.",
        strain=1,
        modes={"split", "turns"},
        tags={"garden", "seeds", "sharing"},
    ),
}

PLANS = {
    "split_jobs": Plan(
        id="split_jobs",
        mode="split",
        sense=3,
        power=3,
        title="split the jobs",
        offer="gave each child a real job so no one had to fight for the same step",
        do_text="{dominant} could {task1}, and {partner} could {task2}. Once both jobs belonged somewhere, the work settled down and began to move again.",
        fail_text="they cleared a little space and gave each child one true job: {dominant} would {task1}, and {partner} would {task2}. The first try was too muddled to save, but the second start felt calmer from the very first minute.",
        qa_text="they split the work into two real jobs",
        tags={"turn_taking", "sharing"},
    ),
    "take_turns": Plan(
        id="take_turns",
        mode="turns",
        sense=2,
        power=2,
        title="take turns",
        offer="set up turns with the shared piece so each child would get a fair chance",
        do_text="{dominant} used the {material} first, then passed it over and waited while {partner} had a turn. The passing itself softened the room, because each child could feel the other being remembered.",
        fail_text="they slowed down and took turns with the {material}. It was too late to save the first version, but the new start felt fair, steady, and much kinder.",
        qa_text="they took turns with the shared part",
        tags={"turn_taking", "fairness"},
    ),
    "let_finish": Plan(
        id="let_finish",
        mode="solo",
        sense=1,
        power=0,
        title="let one child finish alone",
        offer="decided to let the faster child do all of it",
        do_text="{dominant} finished while {partner} watched.",
        fail_text="{dominant} finished while {partner} watched.",
        qa_text="one child finished alone",
        tags={"unfair"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Ava", "Mia", "Ella", "Zoe", "Anna", "Lucy", "Ruby", "Clara"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Eli", "Theo", "Noah", "Jack", "Finn", "Owen"]
TRAITS = ["patient", "careful", "quiet", "thoughtful", "steady", "gentle"]


@dataclass
class StoryParams:
    project: str
    plan: str
    dominant_name: str
    dominant_gender: str
    partner_name: str
    partner_gender: str
    relation: str
    partner_trait: str
    adult: str
    delay: int = 0
    dominant_age: int = 7
    partner_age: int = 6
    adult_present: bool = True
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
    "cookies": [
        ("Why is baking easier when people share jobs?",
         "Baking has different steps, like measuring and stirring, so two people can help without bumping into each other. Shared jobs make the work calmer and fairer.")
    ],
    "fort": [
        ("Why does a blanket fort work better with two people?",
         "One person can hold a blanket while another clips or tucks it in place. Two sets of hands keep the blanket from slipping down.")
    ],
    "garden": [
        ("Why do seeds need gentle hands?",
         "Seeds are tiny and easy to lose or squash if you rush. Gentle hands help put them in the soil neatly so they can grow.")
    ],
    "sharing": [
        ("What does sharing space mean?",
         "Sharing space means moving your body and your things so another person can join in too. It shows that their part matters.")
    ],
    "fairness": [
        ("Why do turns help when children want the same thing?",
         "Turns help because each person knows they will get a chance. That makes waiting feel fairer and helps people stay calm.")
    ],
    "apology": [
        ("What is an apology?",
         "An apology is when you say you were wrong and show you want to do better. A real apology is followed by a change in what you do next.")
    ],
}
KNOWLEDGE_ORDER = ["cookies", "fort", "garden", "sharing", "fairness", "apology"]


CURATED = [
    StoryParams(
        project="cookies",
        plan="split_jobs",
        dominant_name="Nora",
        dominant_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        relation="siblings",
        partner_trait="patient",
        adult="mother",
        delay=0,
        dominant_age=7,
        partner_age=6,
        adult_present=True,
    ),
    StoryParams(
        project="fort",
        plan="take_turns",
        dominant_name="Leo",
        dominant_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        relation="friends",
        partner_trait="quiet",
        adult="father",
        delay=1,
        dominant_age=6,
        partner_age=6,
        adult_present=False,
    ),
    StoryParams(
        project="garden",
        plan="split_jobs",
        dominant_name="Ava",
        dominant_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        relation="siblings",
        partner_trait="thoughtful",
        adult="mother",
        delay=2,
        dominant_age=8,
        partner_age=5,
        adult_present=True,
    ),
    StoryParams(
        project="fort",
        plan="split_jobs",
        dominant_name="Max",
        dominant_gender="boy",
        partner_name="Lily",
        partner_gender="girl",
        relation="siblings",
        partner_trait="gentle",
        adult="father",
        delay=0,
        dominant_age=7,
        partner_age=7,
        adult_present=True,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dominant = f["dominant"]
    partner = f["partner"]
    project = f["project_cfg"]
    plan = f["plan_cfg"]
    return [
        f'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "dominant" and ends in reconciliation.',
        f"Tell a home story where {dominant.id} becomes too controlling while making {project.object_label} with {partner.id}, notices the hurt, apologizes, and they repair the moment by trying to {plan.title}.",
        f"Write a gentle story about two children sharing {project.object_label}, where one child leaves too little room for the other and then learns how to make space again.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two siblings"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    dominant = f["dominant"]
    partner = f["partner"]
    adult = f["adult"]
    project_cfg = f["project_cfg"]
    plan = f["plan_cfg"]
    relation = f["relation"]
    outcome = f["outcome"]
    source = f["source"]
    pair = pair_noun(dominant, partner, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {dominant.id} and {partner.id}, working on {project_cfg.object_label}. The story also includes {dominant.id}'s {adult.label_word if relation == 'siblings' else adult.label_word} nearby in the home."
        ),
        (
            f"What were {dominant.id} and {partner.id} trying to make?",
            f"They were trying to make {project_cfg.object_label} together in {project_cfg.place}. The job worked best when one child could {project_cfg.task1} while the other could {project_cfg.task2}."
        ),
        (
            f"Why did {partner.id} feel hurt?",
            f"{partner.id} felt hurt because {dominant.id} kept taking over and left no room to help. When one child held onto the whole job, the project slowed down and {partner.id} felt pushed out."
        ),
        (
            f"Why does the story use the word dominant for {dominant.id}?",
            f"It says {dominant.id}'s voice turned too dominant because {dominant.pronoun()} was trying to control the whole project. The word fits the moment when {dominant.pronoun()} stopped sharing space, tools, and decisions."
        ),
    ]
    if source == "adult":
        qa.append((
            f"How did the grown-up help the children reconcile?",
            f"The grown-up gently named the problem and reminded {dominant.id} that making room was part of making it together. That helped turn the apology into a real change instead of just a quick sorry."
        ))
    else:
        qa.append((
            f"How did {dominant.id} realize something was wrong?",
            f"{dominant.id} saw {partner.id}'s face and heard {partner.pronoun('object')} say there was no room to join in. The stalled feeling around the project made the hurt impossible to miss."
        ))
    if outcome == "repaired":
        qa.append((
            "How did they solve the problem?",
            f"They reconciled by {plan.qa_text}. That gave both children a real place in the work, so the project could keep going and the room felt gentle again."
        ))
    else:
        qa.append((
            "Did they save the first project?",
            f"No, not fully. They still reconciled by {plan.qa_text}, but they had to start a smaller, calmer version because the first try had already been pushed too far."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with both children close together again and making room for each other. The ending image proves the reconciliation because {dominant.id} shifted over without being asked."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["project_cfg"].tags)
    if f["plan_cfg"].id == "take_turns":
        tags.add("fairness")
    if f["plan_cfg"].id == "split_jobs":
        tags.add("sharing")
    tags.add("apology")
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(project: Project, plan: Plan) -> str:
    if plan.sense < SENSE_MIN:
        return (
            f"(Refusing plan '{plan.id}': it scores too low on common sense "
            f"(sense={plan.sense} < {SENSE_MIN}). A reconciliation story should make real room for both children, not just let one finish alone.)"
        )
    return (
        f"(No story: {plan.title} does not fit {project.object_label}. "
        f"The repair has to match how that project can honestly be shared.)"
    )


def outcome_of(params: StoryParams) -> str:
    project = PROJECTS[params.project]
    plan = PLANS[params.plan]
    return "repaired" if repaired_enough(plan, project, params.delay) else "restarted"


ASP_RULES = r"""
compatible(P, Pl) :- project(P), plan(Pl), mode_of(Pl, M), supports(P, M).
sensible(Pl) :- plan(Pl), sense(Pl, S), sense_min(Min), S >= Min.
valid(P, Pl) :- compatible(P, Pl), sensible(Pl).

pressure(V) :- chosen_project(P), base_strain(P, B), delay(D), V = B + D.
repaired :- chosen_project(P), chosen_plan(Pl), power(Pl, Pw), pressure(V), Pw >= V.
outcome(repaired) :- repaired.
outcome(restarted) :- not repaired.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("base_strain", pid, project.strain))
        for mode in sorted(project.modes):
            lines.append(asp.fact("supports", pid, mode))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("mode_of", plan_id, plan.mode))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("power", plan_id, plan.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_project", params.project),
        asp.fact("chosen_plan", params.plan),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a too-dominant moment in an ordinary home project, followed by reconciliation."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2],
                    help="how long the taking-over lasts before the repair begins")
    ap.add_argument("--adult-present", dest="adult_present", action="store_true", default=None,
                    help="force a grown-up to be nearby and mediate")
    ap.add_argument("--no-adult-present", dest="adult_present", action="store_false",
                    help="force the children to repair the moment on their own")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible (project, plan) pairs derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.plan:
        project = PROJECTS[args.project]
        plan = PLANS[args.plan]
        if not (compatible(project, plan) and plan.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(project, plan))
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        project = PROJECTS[args.project] if args.project else next(iter(PROJECTS.values()))
        raise StoryError(explain_rejection(project, PLANS[args.plan]))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.plan is None or combo[1] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, plan_id = rng.choice(combos)
    dominant_name, dominant_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=dominant_name)
    relation = args.relation or rng.choice(["siblings", "friends"])
    partner_trait = rng.choice(TRAITS)
    adult = args.adult or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    adult_present = args.adult_present if args.adult_present is not None else rng.choice([True, False, True])
    dominant_age, partner_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        project=project_id,
        plan=plan_id,
        dominant_name=dominant_name,
        dominant_gender=dominant_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        relation=relation,
        partner_trait=partner_trait,
        adult=adult,
        delay=delay,
        dominant_age=dominant_age,
        partner_age=partner_age,
        adult_present=adult_present,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    project = PROJECTS[params.project]
    plan = PLANS[params.plan]
    if not (compatible(project, plan) and plan.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(project, plan))

    world = tell(
        project=project,
        plan=plan,
        dominant_name=params.dominant_name,
        dominant_gender=params.dominant_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        relation=params.relation,
        partner_trait=params.partner_trait,
        adult_type=params.adult,
        delay=params.delay,
        dominant_age=params.dominant_age,
        partner_age=params.partner_age,
        adult_present=params.adult_present,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    python_sensible = {p.id for p in sensible_plans()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible plans match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

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
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        _ = sample.to_json()
        print("OK: smoke test generated a normal story and JSON output.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible plans: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, plan) combos:\n")
        for project, plan in combos:
            print(f"  {project:10} {plan}")
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
            header = f"### {p.dominant_name} & {p.partner_name}: {p.project} with {p.plan} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
