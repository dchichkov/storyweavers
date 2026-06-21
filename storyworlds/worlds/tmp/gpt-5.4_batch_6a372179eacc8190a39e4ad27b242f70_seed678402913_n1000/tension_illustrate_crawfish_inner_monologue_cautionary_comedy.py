#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tension_illustrate_crawfish_inner_monologue_cautionary_comedy.py
================================================================================================

A standalone storyworld for a cautionary comedy about a child who wants to use a
live crawfish to illustrate an art project. The world model prefers plausible,
child-facing choices: a crawfish needs a wet container, wild animals do not
belong loose on a craft table, and drawing from a picture is safer than turning
show-and-tell into a chase scene.

Run it
------
    python storyworlds/worlds/gpt-5.4/tension_illustrate_crawfish_inner_monologue_cautionary_comedy.py
    python storyworlds/worlds/gpt-5.4/tension_illustrate_crawfish_inner_monologue_cautionary_comedy.py --container lunchbox
    python storyworlds/worlds/gpt-5.4/tension_illustrate_crawfish_inner_monologue_cautionary_comedy.py --response shoebox_chase
    python storyworlds/worlds/gpt-5.4/tension_illustrate_crawfish_inner_monologue_cautionary_comedy.py --all --qa
    python storyworlds/worlds/gpt-5.4/tension_illustrate_crawfish_inner_monologue_cautionary_comedy.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


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
    tags: set[str] = field(default_factory=set)
    wet_safe: bool = False
    alive: bool = False
    wild: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher_f"}
        male = {"boy", "father", "dad", "man", "teacher_m"}
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
            "teacher_f": "teacher",
            "teacher_m": "teacher",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    project_place: str
    water_note: str
    adult_type: str
    audience: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    verb: str
    object_phrase: str
    reason: str
    final_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    wet_safe: bool
    escape_risk: int
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeReference:
    id: str
    label: str
    phrase: str
    line: str
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


def _r_dry_stress(world: World) -> list[str]:
    out: list[str] = []
    crawfish = world.entities.get("crawfish")
    if not crawfish:
        return out
    if crawfish.meters["out_of_water"] < THRESHOLD:
        return out
    sig = ("dry_stress", "crawfish")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crawfish.meters["stress"] += 1
    room = world.entities.get("room")
    if room:
        room.meters["tension"] += 1
    hero = world.entities.get("hero")
    if hero:
        hero.memes["worry"] += 1
    return out


def _r_escape_tension(world: World) -> list[str]:
    out: list[str] = []
    crawfish = world.entities.get("crawfish")
    if not crawfish:
        return out
    if crawfish.meters["escaped"] < THRESHOLD:
        return out
    sig = ("escape_tension", "crawfish")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room = world.entities.get("room")
    if room:
        room.meters["tension"] += 2
        room.meters["chaos"] += 1
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if hero:
        hero.memes["embarrassment"] += 1
    if helper:
        helper.memes["alarm"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="dry_stress", tag="physical", apply=_r_dry_stress),
    Rule(name="escape_tension", tag="social", apply=_r_escape_tension),
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
            if item and not item.startswith("__"):
                world.say(item)
    return produced


def hazard_at_risk(container: Container) -> bool:
    return container.wet_safe


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def escape_severity(container: Container, delay: int) -> int:
    return container.escape_risk + delay


def is_contained(response: Response, container: Container, delay: int) -> bool:
    return response.power >= escape_severity(container, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = initial_caution(trait) + 1.0 + (4.0 if helper_older else 0.0)
    return helper_older and authority > BRAVERY_INIT


def predict_escape(world: World) -> dict:
    sim = world.copy()
    crawfish = sim.get("crawfish")
    crawfish.meters["escaped"] += 1
    crawfish.meters["out_of_water"] += 1
    propagate(sim, narrate=False)
    room = sim.get("room")
    hero = sim.get("hero")
    return {
        "tension": room.meters["tension"],
        "worry": hero.memes["worry"],
    }


def introduce(world: World, hero: Entity, project: Project, setting: Setting) -> None:
    world.say(
        f"{hero.id} loved to illustrate little creatures with more excitement than accuracy. "
        f"Today {hero.pronoun()} was supposed to {project.verb} {project.object_phrase} at {setting.project_place}."
    )
    world.say(
        f"On the way there, {hero.pronoun()} had found a crawfish and decided its tiny claws looked like a joke the creek had told."
    )


def desire(world: World, hero: Entity, container: Container) -> None:
    hero.memes["desire"] += 1
    hero.memes["bravery"] = BRAVERY_INIT
    world.say(
        f"{hero.id} tucked the crawfish into {container.phrase}. {container.detail}"
    )
    world.say(
        f'{hero.id} thought, "If I bring a real crawfish, my picture will be so perfect it might clap for itself."'
    )


def warn(world: World, helper: Entity, hero: Entity, adult: Entity, container: Container) -> None:
    pred = predict_escape(world)
    helper.memes["caution"] += 1
    world.facts["predicted_tension"] = pred["tension"]
    world.say(
        f'{helper.id} peered into {container.phrase} and whispered, "{hero.id}, a crawfish is not a bookmark with legs. '
        f'If it gets loose, this whole room will have tension before the paint even opens."'
    )
    extra = ""
    if helper.memes["caution"] >= 6:
        extra = f" {helper.id} was already imagining {adult.label_word} standing on tiptoe while chairs scraped and children squealed."
    world.say(
        f'{helper.id} added, "Wild things need water and space, not a surprise audience."{extra}'
    )


def defy(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["defiance"] += 1
    older_clause = ""
    if hero.attrs.get("relation") == "siblings" and hero.age > helper.age:
        older_clause = f" Being the older one made {hero.id} feel even more certain."
    world.say(
        f'{hero.id} gave a brave little shrug.{older_clause} {hero.pronoun().capitalize()} thought, "It will stay still for two minutes. Probably. Maybe one and a half."'
    )


def back_down(world: World, hero: Entity, helper: Entity, adult: Entity, ref: SafeReference, project: Project) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f'{hero.id} looked at the crawfish, then at {helper.id}, and the joke stopped feeling funny. '
        f'"Okay," {hero.pronoun()} said. "I do not want my picture to come with claws."'
    )
    world.say(
        f"They brought the crawfish back to the creek edge before art time, and {adult.label_word} helped them set up {ref.phrase} instead."
    )
    world.say(
        f"{ref.line} {hero.id} still got to {project.verb} {project.object_phrase}, only now the model stayed where paper liked it."
    )


def arrive(world: World, hero: Entity, setting: Setting, project: Project) -> None:
    world.say(
        f"By the time they reached {setting.project_place}, {setting.audience} was already busy with glue, paper, and proud opinions about whose drawing looked most alive."
    )
    world.say(
        f"{setting.water_note} That only made the crawfish plan seem, for one silly moment, almost clever."
    )


def open_container(world: World, hero: Entity, container: Container) -> None:
    world.say(
        f"{hero.id} set {container.phrase} beside the paper and lifted it just enough to peek. "
        f'{hero.pronoun().capitalize()} thought, "One quick look at the claws, one quick line, and nobody will ever know."'
    )


def escape(world: World, hero: Entity, helper: Entity, crawfish: Entity) -> None:
    crawfish.meters["escaped"] += 1
    crawfish.meters["out_of_water"] += 1
    propagate(world, narrate=False)
    hero.memes["worry"] += 1
    helper.memes["alarm"] += 1
    world.say(
        "But the crawfish had its own plan. It popped over the rim, landed with a wet tap, and scuttled sideways across the art table like a tiny red comma that refused to end the sentence."
    )
    world.say(
        f'"My crawfish is making an escape!" {hero.id} squeaked.'
    )
    world.say(
        f'{hero.id} thought, "Oh no. The tension is real now."'
    )


def contain(world: World, adult: Entity, response: Response, ref: SafeReference, project: Project) -> None:
    crawfish = world.get("crawfish")
    room = world.get("room")
    crawfish.meters["escaped"] = 0.0
    crawfish.meters["out_of_water"] = 0.0
    crawfish.meters["safe"] += 1
    room.meters["tension"] = 0.0
    room.meters["chaos"] = 0.0
    body = response.text
    world.say(
        f"{adult.label_word.capitalize()} did not shout. {adult.pronoun().capitalize()} {body}."
    )
    world.say(
        f'Then {adult.pronoun()} said, "A real crawfish belongs in creek water, not next to the glitter glue. We can still illustrate it, but we will do it the kind way."'
    )
    world.say(
        f"After that, {ref.line.lower()} Soon the paper held bright claws, silly eyes, and no surprises with legs."
    )
    world.facts["returned_kindly"] = True


def contain_fail(world: World, adult: Entity, response: Response) -> None:
    crawfish = world.get("crawfish")
    room = world.get("room")
    room.meters["chaos"] += 1
    room.meters["tension"] += 1
    crawfish.meters["hidden"] += 1
    body = response.fail
    world.say(
        f"{adult.label_word.capitalize()} {body}."
    )
    world.say(
        "The crawfish vanished under the supply shelf, where even the crayons seemed too nervous to roll."
    )


def cleanup(world: World, adult: Entity, hero: Entity, ref: SafeReference, project: Project) -> None:
    crawfish = world.get("crawfish")
    room = world.get("room")
    crawfish.meters["hidden"] = 0.0
    crawfish.meters["out_of_water"] = 0.0
    crawfish.meters["safe"] += 1
    room.meters["tension"] = 0.0
    world.say(
        f"A little later, the crawfish was found in a damp mop bucket and carried carefully back outside. "
        f"{adult.label_word.capitalize()} made sure it went back to water where it could wave its claws at nobody in particular."
    )
    world.say(
        f'{hero.id} felt hot in the cheeks but wiser in the middle. {hero.pronoun().capitalize()} thought, "Next time I will bring a drawing, not a dash of creek trouble."'
    )
    world.say(
        f"Art time started again with {ref.phrase}, and {project.final_image}"
    )
    world.facts["returned_kindly"] = True


def ending_safe(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["lesson"] += 1
    helper.memes["joy"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"By the end, {hero.id} was laughing again, but more softly. The best part of the picture turned out not to be the real crawfish at all. It was the enormous funny claws {hero.pronoun()} had drawn from memory."
    )


def tell(
    setting: Setting,
    project: Project,
    container: Container,
    ref: SafeReference,
    response: Response,
    *,
    hero_name: str = "Nell",
    hero_gender: str = "girl",
    helper_name: str = "Tom",
    helper_gender: str = "boy",
    adult_type: str = "teacher_f",
    trait: str = "careful",
    delay: int = 0,
    hero_age: int = 6,
    helper_age: int = 4,
    relation: str = "siblings",
    pet_phrase: str = "",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["bold"],
        age=hero_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[trait],
        age=helper_age,
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the adult",
    ))
    room = world.add(Entity(id="room", type="room", label=setting.project_place))
    crawfish = world.add(Entity(
        id="crawfish",
        type="animal",
        label="crawfish",
        phrase="the crawfish",
        wet_safe=True,
        alive=True,
        wild=True,
        tags={"crawfish"},
    ))
    container_ent = world.add(Entity(
        id="container",
        type="container",
        label=container.label,
        phrase=container.phrase,
        wet_safe=container.wet_safe,
        tags=set(container.tags),
    ))

    helper.memes["caution"] = initial_caution(trait)
    world.facts["pet_phrase"] = pet_phrase

    introduce(world, hero, project, setting)
    desire(world, hero, container)

    world.para()
    warn(world, helper, hero, adult, container)

    averted = would_avert(relation, hero_age, helper_age, trait)
    if averted:
        back_down(world, hero, helper, adult, ref, project)
        world.para()
        ending_safe(world, hero, helper)
        severity = 0
        contained = True
    else:
        defy(world, hero, helper)
        world.para()
        arrive(world, hero, setting, project)
        open_container(world, hero, container)
        escape(world, hero, helper, crawfish)
        severity = escape_severity(container, delay)
        crawfish.meters["severity"] = float(severity)
        contained = is_contained(response, container, delay)

        world.para()
        if contained:
            contain(world, adult, response, ref, project)
            ending_safe(world, hero, helper)
        else:
            contain_fail(world, adult, response)
            cleanup(world, adult, hero, ref, project)
            hero.memes["lesson"] += 1

    outcome = "averted" if averted else ("contained" if contained else "chaos")
    world.facts.update(
        setting=setting,
        project=project,
        container_cfg=container,
        reference=ref,
        response=response,
        hero=hero,
        helper=helper,
        adult=adult,
        crawfish=crawfish,
        relation=relation,
        severity=severity,
        delay=delay,
        outcome=outcome,
        escaped=crawfish.meters["safe"] >= THRESHOLD or crawfish.meters["hidden"] >= THRESHOLD,
        lesson=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        label="classroom",
        project_place="the art room",
        water_note="There was a sink in the corner, but not one child there had come to paint beside a surprise animal.",
        adult_type="teacher_f",
        audience="a whole class",
        tags={"classroom"},
    ),
    "library": Setting(
        id="library",
        label="library",
        project_place="the library craft table",
        water_note="There was a neat little plant mister nearby, which was not at all the same thing as a creek.",
        adult_type="teacher_m",
        audience="a row of patient readers",
        tags={"library"},
    ),
    "kitchen": Setting(
        id="kitchen",
        label="kitchen",
        project_place="the kitchen table before school",
        water_note="There was a sink right there, but a sink is still not a wild home.",
        adult_type="mother",
        audience="only family",
        tags={"home"},
    ),
}

PROJECTS = {
    "poster": Project(
        id="poster",
        verb="illustrate",
        object_phrase="a creek-life poster",
        reason="for show-and-tell",
        final_image="the finished poster had blue ripples, green reeds, and one wonderfully overdramatic crawfish smiling from the corner.",
        tags={"poster"},
    ),
    "menu": Project(
        id="menu",
        verb="illustrate",
        object_phrase="a pretend swamp café menu",
        reason="for free drawing time",
        final_image="the menu ended up with bubble-letter soup names and a crawfish wearing a chef hat much too large for its head.",
        tags={"menu"},
    ),
    "card": Project(
        id="card",
        verb="illustrate",
        object_phrase="a nature thank-you card",
        reason="for the class wall",
        final_image="the card showed cattails, pebbles, and a polite little crawfish bowing as if it had been invited all along.",
        tags={"card"},
    ),
}

CONTAINERS = {
    "jar": Container(
        id="jar",
        label="jar",
        phrase="a glass jar with creek water",
        wet_safe=True,
        escape_risk=2,
        detail="The jar was clear enough to show every twitchy leg, which made the idea feel smart and the plan feel smarter than it was.",
        tags={"jar", "water"},
    ),
    "bucket": Container(
        id="bucket",
        label="bucket",
        phrase="a small bait bucket half full of water",
        wet_safe=True,
        escape_risk=1,
        detail="It sloshed when {hero} walked, which should have been a warning but mostly felt dramatic.",
        tags={"bucket", "water"},
    ),
    "mug": Container(
        id="mug",
        label="mug",
        phrase="a tall mug with a splash of water",
        wet_safe=True,
        escape_risk=3,
        detail="The mug looked sturdy until anyone remembered that mugs are for cocoa, not sideways adventures.",
        tags={"mug", "water"},
    ),
    "lunchbox": Container(
        id="lunchbox",
        label="lunchbox",
        phrase="a shiny lunchbox with a damp napkin",
        wet_safe=False,
        escape_risk=4,
        detail="It looked secret, which was exactly the problem.",
        tags={"lunchbox"},
    ),
    "shoebox": Container(
        id="shoebox",
        label="shoebox",
        phrase="a shoebox lined with notebook paper",
        wet_safe=False,
        escape_risk=4,
        detail="The box was dry and scratchy and fit for shoes, not creek creatures.",
        tags={"shoebox"},
    ),
}

SAFE_REFERENCES = {
    "photo": SafeReference(
        id="photo",
        label="photo",
        phrase="a printed creek photo",
        line="The photo showed the same bent claws and bead-bright eyes, only without any chance of running under a glue tray.",
        tags={"photo"},
    ),
    "book": SafeReference(
        id="book",
        label="book",
        phrase="an animal book opened to the crawfish page",
        line="The book held perfectly still, which was a useful talent in an art helper.",
        tags={"book"},
    ),
    "toy": SafeReference(
        id="toy",
        label="toy",
        phrase="a rubber crawfish toy beside the paper",
        line="The toy looked silly enough to be funny and still enough to be safe.",
        tags={"toy"},
    ),
}

RESPONSES = {
    "net_cup": Response(
        id="net_cup",
        sense=3,
        power=4,
        text="slid a plastic tub in front of the crawfish, covered it with a cup, and scooped the little escape artist back into water",
        fail="tried to trap it with a tub and cup, but the crawfish darted under the shelf first",
        qa_text="slid a tub and cup around the crawfish and guided it back into water",
        tags={"rescue", "water"},
    ),
    "wet_towel": Response(
        id="wet_towel",
        sense=2,
        power=3,
        text="dropped a wet towel gently over the crawfish, gathered it up carefully, and set it into a water bin",
        fail="reached with a wet towel, but the crawfish scooted past the edge and hid",
        qa_text="used a wet towel gently and moved the crawfish into water",
        tags={"rescue", "water"},
    ),
    "shoebox_chase": Response(
        id="shoebox_chase",
        sense=1,
        power=1,
        text="",
        fail="grabbed a shoebox and started a clattery chase that only made more feet hop out of the way",
        qa_text="chased it with a shoebox",
        tags={"chaos"},
    ),
}

GIRL_NAMES = ["Nell", "Lila", "Mia", "Ava", "Ruby", "June", "Ivy", "Tess"]
BOY_NAMES = ["Owen", "Max", "Leo", "Finn", "Ben", "Toby", "Eli", "Jude"]
TRAITS = ["careful", "cautious", "sensible", "thoughtful", "curious", "clever"]
PETS = ["the dog watched from the doorway", "the cat blinked from the chair", "their puppy sneezed at the bucket", ""]


@dataclass
class StoryParams:
    setting: str
    project: str
    container: str
    reference: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
    adult: str
    delay: int = 0
    hero_age: int = 6
    helper_age: int = 4
    relation: str = "siblings"
    pet_phrase: str = ""
    seed: Optional[int] = None


KNOWLEDGE = {
    "crawfish": [
        (
            "What is a crawfish?",
            "A crawfish is a small water animal with claws and a hard shell. It lives in fresh water like creeks and ponds."
        )
    ],
    "water": [
        (
            "Why does a crawfish need water?",
            "A crawfish is a water animal, so it needs a wet place that fits its body. A dry box or lunchbox is not a safe home for it."
        )
    ],
    "wild": [
        (
            "Why should wild animals stay wild?",
            "Wild animals belong in the places they live best, like creeks, ponds, and grass. When people carry them around for fun, the animals can get scared or hurt."
        )
    ],
    "illustrate": [
        (
            "What does illustrate mean?",
            "To illustrate means to make a picture that shows an idea or a story. You can illustrate an animal by drawing its shape, color, and details."
        )
    ],
    "photo": [
        (
            "Why is a photo helpful for drawing?",
            "A photo stays still, so you can look carefully at the details. That makes it easier to draw safely."
        )
    ],
    "book": [
        (
            "Why is a book a good art helper?",
            "A book can show you what an animal looks like without letting it run loose. It helps you learn while keeping the animal safe in its real home."
        )
    ],
    "toy": [
        (
            "Why can a toy be safer than a real animal for pretend play?",
            "A toy cannot get scared, thirsty, or lost under a shelf. That makes it easier to use in play or art time."
        )
    ],
    "rescue": [
        (
            "What should you do if a small animal gets loose inside?",
            "Stay calm and call a grown-up right away. A calm rescue is safer than a noisy chase."
        )
    ],
    "chaos": [
        (
            "Why can chasing a scared animal make things worse?",
            "When people rush and stomp, the animal gets more frightened and harder to catch. Calm movements help everyone stay safer."
        )
    ],
}
KNOWLEDGE_ORDER = ["crawfish", "water", "wild", "illustrate", "photo", "book", "toy", "rescue", "chaos"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for project_id in PROJECTS:
            for container_id, container in CONTAINERS.items():
                if hazard_at_risk(container):
                    combos.append((setting_id, project_id, container_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    project = f["project"]
    container = f["container_cfg"]
    ref = f["reference"]
    outcome = f["outcome"]
    base = (
        f'Write a short cautionary comedy for a 3-to-5-year-old where a child wants to use a live crawfish to {project.verb} '
        f'{project.object_phrase}. Include the words "tension", "illustrate", and "crawfish".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story where {helper.id}, an older sibling, talks {hero.id} out of bringing the crawfish inside, and they use {ref.phrase} instead.",
            f"Write a funny story with inner monologue where the child realizes a real crawfish is a bad art helper before any chaos starts.",
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a comedic story where {hero.id} ignores a warning, the crawfish escapes from {container.phrase}, and a calm grown-up fixes the problem kindly.",
            f"Write a story with inner monologue and a light cautionary lesson: the child causes tension in art time, then learns to draw from {ref.label} instead.",
        ]
    return [
        base,
        f"Tell a cautionary comedy where {hero.id} brings the crawfish in, a weak rescue turns the room into chaos, and the child later switches to {ref.phrase}.",
        f"Write a funny but clear lesson story where a crawfish chase interrupts art time and teaches that wild animals are not classroom props.",
    ]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    adult = f["adult"]
    project = f["project"]
    container = f["container_cfg"]
    ref = f["reference"]
    response = f["response"]
    pair = pair_noun(hero, helper, f["relation"])
    adult_word = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}, and the grown-up who helps when the crawfish plan goes wrong."
        ),
        (
            f"What did {hero.id} want to do?",
            f"{hero.id} wanted to {project.verb} {project.object_phrase} and thought a real crawfish would make the picture better. That wish is what started the trouble."
        ),
        (
            f"Why did {helper.id} warn {hero.id}?",
            f"{helper.id} knew a wild crawfish could get loose and make tension in the room. {helper.pronoun().capitalize()} also knew the animal needed water and a calmer place than the art table."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How was the problem solved before anything happened?",
                f"{hero.id} listened to {helper.id} and gave up the idea of bringing the crawfish in. They returned it outside and used {ref.phrase} so the art could stay fun and kind."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "What happened when the container was opened?",
                f"The crawfish popped out and ran across the table, which made everyone jump. That is when the silly plan turned into real tension."
            )
        )
        qa.append(
            (
                f"How did the {adult_word} fix it?",
                f"The {adult_word} {response.qa_text}. The calm rescue protected the crawfish and stopped the room from getting wilder."
            )
        )
    else:
        qa.append(
            (
                "Did the first rescue work?",
                f"No. The grown-up {response.fail}, and the crawfish hid under the shelf. The chase made the room even more chaotic before the crawfish was finally found and taken back to water."
            )
        )
    qa.append(
        (
            f"What did {hero.id} learn?",
            f"{hero.id} learned that a real crawfish is not a safe art tool. Drawing from {ref.label} was better because it kept the animal safe and let the picture happen without a chase."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"crawfish", "water", "wild", "illustrate"}
    tags |= set(f["reference"].tags)
    if f["outcome"] == "contained":
        tags |= set(f["response"].tags)
    elif f["outcome"] == "chaos":
        tags |= {"chaos"}
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, flag in (("wet_safe", ent.wet_safe), ("alive", ent.alive), ("wild", ent.wild)) if flag]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="classroom",
        project="poster",
        container="jar",
        reference="photo",
        response="net_cup",
        hero="Nell",
        hero_gender="girl",
        helper="Owen",
        helper_gender="boy",
        trait="careful",
        adult="teacher_f",
        delay=0,
        hero_age=6,
        helper_age=8,
        relation="siblings",
        pet_phrase="the dog watched from the doorway",
    ),
    StoryParams(
        setting="library",
        project="menu",
        container="mug",
        reference="book",
        response="wet_towel",
        hero="Max",
        hero_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        trait="cautious",
        adult="teacher_m",
        delay=0,
        hero_age=6,
        helper_age=6,
        relation="friends",
        pet_phrase="",
    ),
    StoryParams(
        setting="classroom",
        project="card",
        container="mug",
        reference="toy",
        response="shoebox_chase",
        hero="Ava",
        hero_gender="girl",
        helper="Ben",
        helper_gender="boy",
        trait="curious",
        adult="teacher_f",
        delay=1,
        hero_age=7,
        helper_age=6,
        relation="friends",
        pet_phrase="",
    ),
    StoryParams(
        setting="kitchen",
        project="poster",
        container="bucket",
        reference="book",
        response="wet_towel",
        hero="Leo",
        hero_gender="boy",
        helper="June",
        helper_gender="girl",
        trait="sensible",
        adult="mother",
        delay=0,
        hero_age=5,
        helper_age=7,
        relation="siblings",
        pet_phrase="the cat blinked from the chair",
    ),
]


def explain_rejection(container: Container) -> str:
    return (
        f"(No story: {container.phrase} is not a reasonable place for a crawfish. "
        f"A crawfish needs a wet container, so this choice would be unkind before the story even starts.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a calmer rescue such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.helper_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], CONTAINERS[params.container], params.delay) else "chaos"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(S, P, C) :- setting(S), project(P), container(C), wet_safe(C).
sensible(R)    :- response(R), sense(R, V), sense_min(M), V >= M.

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
helper_older    :- relation(siblings), hero_age(H), helper_age(K), K > H.
bonus(4)        :- helper_older.
bonus(0)        :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted         :- helper_older, authority(A), bravery_init(BR), A > BR.

severity(E + D) :- chosen_container(C), escape_risk(C, E), delay(D).
resp_power(P)   :- chosen_response(R), power(R, P).
contained       :- resp_power(P), severity(V), P >= V.

outcome(averted)   :- averted.
outcome(contained) :- not averted, contained.
outcome(chaos)     :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        if container.wet_safe:
            lines.append(asp.fact("wet_safe", container_id))
        lines.append(asp.fact("escape_risk", container_id, container.escape_risk))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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
    return sorted(item for (item,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_container", params.container),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def asp_verify() -> int:
    rc = 0

    py_gate = set(valid_combos())
    asp_gate = set(asp_valid_combos())
    if py_gate == asp_gate:
        print(f"OK: gate matches valid_combos() ({len(py_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if asp_gate - py_gate:
            print("  only in clingo:", sorted(asp_gate - py_gate))
        if py_gate - asp_gate:
            print("  only in python:", sorted(py_gate - asp_gate))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child tries to use a live crawfish as an art model. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--reference", choices=SAFE_REFERENCES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father", "teacher_f", "teacher_m"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start for the escaping crawfish")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [name for name in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.container:
        container = CONTAINERS[args.container]
        if not hazard_at_risk(container):
            raise StoryError(explain_rejection(container))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.project is None or combo[1] == args.project)
        and (args.container is None or combo[2] == args.container)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, project_id, container_id = rng.choice(sorted(combos))
    reference_id = args.reference or rng.choice(sorted(SAFE_REFERENCES))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero, hero_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=hero)
    trait = rng.choice(TRAITS)
    adult = args.adult or SETTINGS[setting_id].adult_type
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, helper_age = rng.sample([4, 5, 6, 7, 8], 2)
    pet_phrase = rng.choice(PETS)
    return StoryParams(
        setting=setting_id,
        project=project_id,
        container=container_id,
        reference=reference_id,
        response=response_id,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        trait=trait,
        adult=adult,
        delay=delay,
        hero_age=hero_age,
        helper_age=helper_age,
        relation=relation,
        pet_phrase=pet_phrase,
    )


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.reference not in SAFE_REFERENCES:
        raise StoryError(f"(Unknown reference: {params.reference})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.adult not in {"mother", "father", "teacher_f", "teacher_m"}:
        raise StoryError(f"(Unknown adult type: {params.adult})")
    container = CONTAINERS[params.container]
    if not hazard_at_risk(container):
        raise StoryError(explain_rejection(container))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)

    container = CONTAINERS[params.container]
    detail = container.detail.replace("{hero}", params.hero)
    container = Container(
        id=container.id,
        label=container.label,
        phrase=container.phrase,
        wet_safe=container.wet_safe,
        escape_risk=container.escape_risk,
        detail=detail,
        tags=set(container.tags),
    )

    world = tell(
        SETTINGS[params.setting],
        PROJECTS[params.project],
        container,
        SAFE_REFERENCES[params.reference],
        RESPONSES[params.response],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        relation=params.relation,
        pet_phrase=params.pet_phrase,
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
        print(f"{len(combos)} compatible (setting, project, container) combos:\n")
        for setting_id, project_id, container_id in combos:
            print(f"  {setting_id:10} {project_id:8} {container_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(item) for item in CURATED]
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
            header = f"### {p.hero} & {p.helper}: {p.project} with {p.container} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
