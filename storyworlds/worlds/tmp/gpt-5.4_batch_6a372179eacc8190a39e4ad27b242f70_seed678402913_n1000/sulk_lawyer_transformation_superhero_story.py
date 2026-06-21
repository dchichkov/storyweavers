#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sulk_lawyer_transformation_superhero_story.py
========================================================================

A small storyworld for a child-facing superhero tale about a child who starts to
sulk, learns a clear-and-kind way to help from a lawyer grown-up, transforms
into a neighborhood superhero, and fixes a problem in a bright, concrete way.

The domain is intentionally narrow: each story has one local mission, one
superhero emblem, and one lawyer mentor. The reasonableness gate only allows
missions and emblems that truly match. A justice cape can help solve a fairness
problem; repair gloves can help fix a broken banner; a calm mask can help with a
scared child or pet. The world model then decides whether the transformed child
solves the mission mostly alone or as a team with the lawyer mentor.

Run it
------
    python storyworlds/worlds/gpt-5.4/sulk_lawyer_transformation_superhero_story.py
    python storyworlds/worlds/gpt-5.4/sulk_lawyer_transformation_superhero_story.py --place playground --mission swing_turn
    python storyworlds/worlds/gpt-5.4/sulk_lawyer_transformation_superhero_story.py --mission banner_rip --emblem sun_mask
    python storyworlds/worlds/gpt-5.4/sulk_lawyer_transformation_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/sulk_lawyer_transformation_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sulk_lawyer_transformation_superhero_story.py --verify
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
    role: str = ""
    occupation: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "mother":
            return "mom"
        if self.type == "father":
            return "dad"
        return self.type


@dataclass
class Place:
    id: str
    label: str
    sight: str
    missions: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    place: str
    need: str
    problem: str
    worry: str
    call: str
    action: str
    fix_image: str
    difficulty: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Emblem:
    id: str
    label: str
    phrase: str
    alter_ego: str
    tags: set[str] = field(default_factory=set)
    power: int = 1
    shine: str = ""
    vow: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_sulk_slumps(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    sig = ("sulk_slumps", hero.id)
    if hero.memes["sulk"] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["hiding"] += 1
    hero.memes["courage"] -= 1
    return []


def _r_transform_lifts(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    sig = ("transform_lifts", hero.id)
    if hero.meters["transformed"] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hope"] += 1
    hero.memes["courage"] += 2
    if hero.memes["sulk"] > 0:
        hero.memes["sulk"] = 0.0
    return []


def _r_fix_relief(world: World) -> list[str]:
    mission = world.entities.get("mission")
    crowd = world.entities.get("crowd")
    if mission is None or crowd is None:
        return []
    sig = ("fix_relief", mission.id)
    if mission.meters["fixed"] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.memes["relief"] += 1
    crowd.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="sulk_slumps", tag="emotion", apply=_r_sulk_slumps),
    Rule(name="transform_lifts", tag="emotion", apply=_r_transform_lifts),
    Rule(name="fix_relief", tag="social", apply=_r_fix_relief),
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
                produced.extend(out)
    if narrate:
        for text in produced:
            world.say(text)
    return produced


def mission_supported(place_id: str, mission_id: str) -> bool:
    place = PLACES[place_id]
    return mission_id in place.missions and MISSIONS[mission_id].place == place_id


def emblem_matches(mission_id: str, emblem_id: str) -> bool:
    mission = MISSIONS[mission_id]
    emblem = EMBLEMS[emblem_id]
    return mission.need in emblem.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for mission_id in sorted(place.missions):
            for emblem_id in EMBLEMS:
                if mission_supported(place_id, mission_id) and emblem_matches(mission_id, emblem_id):
                    combos.append((place_id, mission_id, emblem_id))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    if not mission_supported(params.place, params.mission):
        raise StoryError(explain_place_mission(params.place, params.mission))
    if not emblem_matches(params.mission, params.emblem):
        raise StoryError(explain_emblem(MISSIONS[params.mission], EMBLEMS[params.emblem]))
    mission = MISSIONS[params.mission]
    emblem = EMBLEMS[params.emblem]
    return "solo" if emblem.power >= mission.difficulty else "team"


def predict_success(world: World, mission: Mission, emblem: Emblem) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["transformed"] += 1
    propagate(sim, narrate=False)
    success = emblem.power >= mission.difficulty
    return {
        "sulk_cleared": hero.memes["sulk"] <= 0,
        "success_mode": "solo" if success else "team",
    }


def introduce(world: World, hero: Entity, mentor: Entity, place: Place) -> None:
    world.say(
        f"{hero.id} loved pretending that {place.label} was a whole secret city. "
        f"{place.sight}"
    )
    world.say(
        f"On that day, {mentor.id}, {hero.pronoun('possessive')} {mentor.type} who worked as a lawyer, "
        f"was there too, carrying a bright bag and watching with kind eyes."
    )


def trouble(world: World, hero: Entity, mission: Mission) -> None:
    crowd = world.get("crowd")
    crowd.memes["worry"] += 1
    hero.memes["care"] += 1
    world.say(
        f"Then trouble popped up. {mission.problem} {mission.worry}"
    )
    world.say(
        f'{hero.id} heard the little cries of "{mission.call}" and wanted to help at once.'
    )


def sulk(world: World, hero: Entity) -> None:
    hero.memes["sulk"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when everyone else rushed forward first, {hero.id} felt small and left out. "
        f"For one unhappy minute, {hero.pronoun()} went to the side and began to sulk."
    )


def mentor_talk(world: World, hero: Entity, mentor: Entity, mission: Mission, emblem: Emblem) -> None:
    pred = predict_success(world, mission, emblem)
    hero.memes["heard_advice"] += 1
    world.facts["predicted_mode"] = pred["success_mode"]
    clear_line = {
        "fairness": "A lawyer listens to both sides and then speaks so everyone can understand.",
        "repair": "A lawyer looks closely before fixing a problem, one careful step at a time.",
        "calm": "A lawyer does not shout over fear. A lawyer helps people slow down and feel safe.",
        "courage": "A lawyer can stand up for what is right even when a room feels big.",
    }[mission.need]
    world.say(
        f'{mentor.id} sat beside {hero.id}. "Even superheroes can feel droopy," '
        f'{mentor.pronoun()} said softly. "{clear_line}"'
    )
    world.say(
        f'"If you put on {emblem.phrase}, you do not become meaner or louder. '
        f'You become more ready to help."'
    )


def transform(world: World, hero: Entity, emblem: Emblem) -> None:
    hero.meters["transformed"] += 1
    propagate(world, narrate=False)
    hero.attrs["alter_ego"] = emblem.alter_ego
    world.say(
        f"{hero.id} straightened up, tied on {emblem.phrase}, and whispered, "
        f'"{emblem.vow}"'
    )
    world.say(
        f"At once, the day felt different. {emblem.shine} In that brave little moment, "
        f"{hero.id} transformed into {emblem.alter_ego}."
    )


def solve_solo(world: World, hero: Entity, mentor: Entity, mission: Mission, emblem: Emblem) -> None:
    mission_ent = world.get("mission")
    mission_ent.meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{emblem.alter_ego} hurried in. {mission.action} {hero.pronoun().capitalize()} did it with a steady face and a clear voice."
    )
    world.say(
        f"Soon {mission.fix_image} The people nearby broke into happy claps, and even {mentor.id} grinned."
    )


def solve_team(world: World, hero: Entity, mentor: Entity, mission: Mission, emblem: Emblem) -> None:
    mission_ent = world.get("mission")
    mission_ent.meters["fixed"] += 1
    hero.memes["teamwork"] += 1
    mentor.memes["teamwork"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{emblem.alter_ego} ran over first, but this mission was a little bigger than one small hero. "
        f"{mentor.id} came too, still calm as a lawyer in a busy courtroom."
    )
    world.say(
        f"Together they worked it out. {mission.action} {mentor.id} helped with the last careful part, and soon {mission.fix_image}"
    )


def ending(world: World, hero: Entity, mentor: Entity, emblem: Emblem, mission: Mission, outcome: str) -> None:
    hero.memes["pride"] += 1
    mentor.memes["love"] += 1
    world.say(
        f'After that, {hero.id} did not feel like hiding anymore. "{hero.attrs.get("alter_ego", emblem.alter_ego)} can come back any time," '
        f'{hero.pronoun()} said.'
    )
    if outcome == "solo":
        world.say(
            f'{mentor.id} squeezed {hero.pronoun("possessive")} shoulder. "That is what real power looks like," '
            f'{mentor.pronoun()} said. "A brave heart, a fair mind, and words that help."'
        )
    else:
        world.say(
            f'"And even heroes can ask for help," {mentor.id} said. '
            f'"That is not a smaller kind of brave. It is a wiser one."'
        )
    world.say(
        f"As the light turned gold over {world.place.label}, {hero.id} swished {emblem.label} once more and smiled instead of trying to sulk."
    )


def tell(
    place: Place,
    mission: Mission,
    emblem: Emblem,
    *,
    hero_name: str = "Maya",
    hero_gender: str = "girl",
    mentor_name: str = "Aunt Rosa",
    mentor_type: str = "aunt",
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    mentor = world.add(
        Entity(
            id="mentor",
            kind="character",
            type=mentor_type,
            label=mentor_name,
            phrase=mentor_name,
            role="mentor",
            occupation="lawyer",
        )
    )
    crowd = world.add(Entity(id="crowd", kind="group", type="group", label="the crowd"))
    mission_ent = world.add(Entity(id="mission", kind="thing", type="problem", label=mission.id, tags=set(mission.tags)))
    hero.id = hero_name
    mentor.id = mentor_name
    world.entities["hero"] = hero
    world.entities["mentor"] = mentor

    introduce(world, hero, mentor, place)
    world.para()
    trouble(world, hero, mission)
    sulk(world, hero)
    world.para()
    mentor_talk(world, hero, mentor, mission, emblem)
    transform(world, hero, emblem)
    world.para()
    outcome = "solo" if emblem.power >= mission.difficulty else "team"
    if outcome == "solo":
        solve_solo(world, hero, mentor, mission, emblem)
    else:
        solve_team(world, hero, mentor, mission, emblem)
    world.para()
    ending(world, hero, mentor, emblem, mission, outcome)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        place=place,
        mission=mission,
        emblem=emblem,
        outcome=outcome,
        solved=mission_ent.meters["fixed"] >= THRESHOLD,
    )
    return world


PLACES = {
    "playground": Place(
        id="playground",
        label="the playground",
        sight="The slide flashed silver, and the swing chains jingled like tiny bells.",
        missions={"swing_turn"},
    ),
    "street_fair": Place(
        id="street_fair",
        label="the street fair",
        sight="Paper stars fluttered between the booths, and music bounced between the houses.",
        missions={"banner_rip"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        sight="Flowerpots sat by the brick wall, and scooters rested in a neat row by the gate.",
        missions={"shy_new_kid", "scared_puppy"},
    ),
}

MISSIONS = {
    "swing_turn": Mission(
        id="swing_turn",
        place="playground",
        need="fairness",
        problem="Two children had both grabbed the same swing at once.",
        worry="Their faces were getting red, and each one kept saying, \"Me first!\"",
        call="This isn't fair!",
        action="Hero by hero, side by side, the waiting order was sorted out, and everyone could see whose turn came next.",
        fix_image="a neat line formed, the swing moved again, and the angry voices melted into laughing ones.",
        difficulty=1,
        tags={"fairness", "playground"},
    ),
    "banner_rip": Mission(
        id="banner_rip",
        place="street_fair",
        need="repair",
        problem="A gust of wind had torn the welcome banner across the middle.",
        worry="The cloth flapped sadly, and the cake table looked lonely underneath it.",
        call="Oh no, it's broken!",
        action="Careful hands lined up the torn edges, tied the loose cords straight, and held the banner steady until it sat smooth again.",
        fix_image="the banner stretched bright across the street once more, and the fair looked ready for heroes and cupcakes alike.",
        difficulty=1,
        tags={"repair", "fair"},
    ),
    "shy_new_kid": Mission(
        id="shy_new_kid",
        place="courtyard",
        need="calm",
        problem="A new child stood by the gate with a ball tucked under one arm and would not come in.",
        worry="The game had stopped because nobody knew how to begin.",
        call="Will somebody talk to them?",
        action="A slow smile, a softer voice, and one simple invitation turned the worried stillness into a safe little opening.",
        fix_image="the new child stepped forward at last, rolled the ball into the circle, and the game started with room for one more.",
        difficulty=1,
        tags={"calm", "friendship"},
    ),
    "scared_puppy": Mission(
        id="scared_puppy",
        place="courtyard",
        need="calm",
        problem="A tiny puppy had wriggled out of its leash and hid under a bench.",
        worry="Every loud call made it scoot farther back.",
        call="Please help my puppy!",
        action="Knees bent low, voices turned gentle, and patient little steps made a safe path back out from the shadows.",
        fix_image="the puppy crept into waiting arms, its tail gave one hopeful wag, and the whole courtyard let out a happy breath.",
        difficulty=2,
        tags={"calm", "pet"},
    ),
}

EMBLEMS = {
    "justice_cape": Emblem(
        id="justice_cape",
        label="the justice cape",
        phrase="the red justice cape",
        alter_ego="Captain Clear Voice",
        tags={"fairness", "courage"},
        power=2,
        shine="The red cloth snapped behind those shoulders like a tiny flag of truth.",
        vow="I stand tall, I listen well, and I help things turn out fair.",
    ),
    "comet_gloves": Emblem(
        id="comet_gloves",
        label="the comet gloves",
        phrase="the silver comet gloves",
        alter_ego="Comet Fixer",
        tags={"repair"},
        power=2,
        shine="The silver fingertips flashed as if they had caught two pieces of moonlight.",
        vow="Small hands can do careful work.",
    ),
    "sun_mask": Emblem(
        id="sun_mask",
        label="the sun mask",
        phrase="the yellow sun mask",
        alter_ego="Sunbeam Scout",
        tags={"calm"},
        power=1,
        shine="The yellow mask made those eyes seem warmer, as if sunrise itself had leaned close.",
        vow="I slow the storm and make room for brave hearts.",
    ),
    "ribbon_shield": Emblem(
        id="ribbon_shield",
        label="the ribbon shield",
        phrase="the blue ribbon shield",
        alter_ego="Shield of Kindly Order",
        tags={"fairness", "calm"},
        power=1,
        shine="The blue ribbon curled around one wrist like a soft little stream of courage.",
        vow="Kind and fair can be strong together.",
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ava", "Lucy", "Ella", "Zoe", "Anna"]
BOY_NAMES = ["Theo", "Max", "Ben", "Sam", "Leo", "Finn", "Noah", "Eli"]
MENTOR_NAMES = {
    "aunt": ["Aunt Rosa", "Aunt June", "Aunt Elena", "Aunt Mira"],
    "uncle": ["Uncle Ray", "Uncle Mateo", "Uncle Omar", "Uncle Luis"],
    "mother": ["Mom"],
    "father": ["Dad"],
}


@dataclass
class StoryParams:
    place: str
    mission: str
    emblem: str
    hero_name: str
    hero_gender: str
    mentor_name: str
    mentor_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="playground",
        mission="swing_turn",
        emblem="justice_cape",
        hero_name="Maya",
        hero_gender="girl",
        mentor_name="Aunt Rosa",
        mentor_type="aunt",
    ),
    StoryParams(
        place="street_fair",
        mission="banner_rip",
        emblem="comet_gloves",
        hero_name="Theo",
        hero_gender="boy",
        mentor_name="Uncle Mateo",
        mentor_type="uncle",
    ),
    StoryParams(
        place="courtyard",
        mission="shy_new_kid",
        emblem="sun_mask",
        hero_name="Lucy",
        hero_gender="girl",
        mentor_name="Mom",
        mentor_type="mother",
    ),
    StoryParams(
        place="courtyard",
        mission="scared_puppy",
        emblem="sun_mask",
        hero_name="Ben",
        hero_gender="boy",
        mentor_name="Dad",
        mentor_type="father",
    ),
]


KNOWLEDGE = {
    "lawyer": [
        (
            "What does a lawyer do?",
            "A lawyer helps people talk about rules, promises, and problems in a clear way. Lawyers listen carefully and use words to help things become fairer."
        )
    ],
    "fairness": [
        (
            "What does fair mean?",
            "Fair means people follow the same rules and get turns in a way everyone can understand. It does not always mean everyone gets the same thing at the same second."
        )
    ],
    "repair": [
        (
            "What does repair mean?",
            "Repair means fixing something that is torn, broken, or not working right. Careful hands and patient steps can turn a problem back into something useful."
        )
    ],
    "calm": [
        (
            "Why can a calm voice help?",
            "A calm voice helps scared or upset people feel safer. When bodies slow down, it becomes easier to listen and make a good choice."
        )
    ],
    "transformation": [
        (
            "What is a transformation in a story?",
            "A transformation is when a character changes in an important way. Sometimes the change is a costume or superhero look, and sometimes it is a brave new feeling inside."
        )
    ],
    "sulk": [
        (
            "What does sulk mean?",
            "To sulk means to sit with hurt feelings and stay grumpy instead of talking about the problem. Sulking shows a feeling, but it usually does not fix anything by itself."
        )
    ],
    "superhero": [
        (
            "Do superheroes always use punching to help?",
            "No. Many superheroes help by noticing a problem, protecting others, and choosing the right action. Clear words, calm choices, and teamwork can be heroic too."
        )
    ],
}
KNOWLEDGE_ORDER = ["sulk", "lawyer", "fairness", "repair", "calm", "transformation", "superhero"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    mission = f["mission"]
    emblem = f["emblem"]
    place = f["place"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "sulk" and "lawyer" and features a transformation.',
        f"Tell a gentle superhero story where a child named {hero.id} starts to sulk at {place.label}, but a {mentor.type} who is a lawyer helps {hero.pronoun('object')} transform into {emblem.alter_ego}.",
        f"Write a child-facing story about {mission.problem.lower()} and end with a bright image that shows the child has changed on the inside as well as the outside.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    mission = f["mission"]
    emblem = f["emblem"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who wanted to help, and {mentor.id}, a {mentor.type} who worked as a lawyer. Together they faced one small neighborhood problem."
        ),
        (
            f"Why did {hero.id} begin to sulk?",
            f"{hero.id} wanted to help right away, but other people rushed in first and made {hero.pronoun('object')} feel small and left out. The sulk came from hurt feelings, not from not caring."
        ),
        (
            f"What did the lawyer grown-up teach {hero.id}?",
            f"{mentor.id} taught that helping starts with listening and speaking clearly. That advice changed the mission from a grumpy feeling into a smart plan."
        ),
        (
            f"How did {hero.id} transform?",
            f"{hero.pronoun().capitalize()} put on {emblem.phrase} and whispered, \"{emblem.vow}\" Then {hero.id} became {emblem.alter_ego}, which showed a brave change on the outside and inside."
        ),
    ]
    if outcome == "solo":
        qa.append(
            (
                f"How was the problem solved?",
                f"{hero.id} solved it as {emblem.alter_ego} by using the exact kind of help the problem needed. {mission.action} That is why the trouble faded instead of growing."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} solve the mission alone?",
                f"No. {hero.id} began the rescue, but the mission was bigger than one small hero, so {mentor.id} helped too. The happy ending came from teamwork and calm thinking together."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the problem fixed and {hero.id} smiling in the golden light instead of trying to sulk. The ending image proves that {hero.pronoun()} had grown braver and steadier."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mission = f["mission"]
    tags = {"sulk", "lawyer", "transformation", "superhero", mission.need}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.occupation:
            parts.append(f"occupation={ent.occupation}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_place_mission(place_id: str, mission_id: str) -> str:
    place = PLACES[place_id]
    mission = MISSIONS[mission_id]
    return (
        f"(No story: {mission.id} belongs in {PLACES[mission.place].label}, not {place.label}. "
        f"The local trouble has to fit the setting.)"
    )


def explain_emblem(mission: Mission, emblem: Emblem) -> str:
    needs = mission.need
    has = ", ".join(sorted(emblem.tags))
    return (
        f"(No story: {emblem.label} helps with {has}, but this mission needs {needs}. "
        f"The transformation must give the child the kind of help the problem really calls for.)"
    )


ASP_RULES = r"""
% --- setting and compatibility gate ----------------------------------------
supported(P, M) :- place(P), mission(M), mission_place(M, P).
matches(M, E)   :- mission(M), emblem(E), mission_need(M, N), emblem_tag(E, N).
valid(P, M, E)  :- supported(P, M), matches(M, E).

% --- outcome model ----------------------------------------------------------
solo(M, E) :- valid(_, M, E), mission_difficulty(M, D), emblem_power(E, P), P >= D.
team(M, E) :- valid(_, M, E), mission_difficulty(M, D), emblem_power(E, P), P < D.

outcome(M, E, solo) :- solo(M, E).
outcome(M, E, team) :- team(M, E).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_place", mid, mission.place))
        lines.append(asp.fact("mission_need", mid, mission.need))
        lines.append(asp.fact("mission_difficulty", mid, mission.difficulty))
    for eid, emblem in EMBLEMS.items():
        lines.append(asp.fact("emblem", eid))
        lines.append(asp.fact("emblem_power", eid, emblem.power))
        for tag in sorted(emblem.tags):
            lines.append(asp.fact("emblem_tag", eid, tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(place: str, mission: str, emblem: str) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", place),
            asp.fact("chosen_mission", mission),
            asp.fact("chosen_emblem", emblem),
            "selected_outcome(O) :- chosen_place(P), chosen_mission(M), chosen_emblem(E), valid(P,M,E), outcome(M,E,O).",
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    bad = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params.place, params.mission, params.emblem)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome comparisons differ.")

    try:
        sample = generate(CURATED[0])
        if "sulk" not in sample.story.lower() or "lawyer" not in sample.story.lower():
            raise StoryError("Smoke test story missing required seed words.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a sulk, a lawyer mentor, and a superhero transformation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--emblem", choices=EMBLEMS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--mentor-type", choices=["aunt", "uncle", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mission and not mission_supported(args.place, args.mission):
        raise StoryError(explain_place_mission(args.place, args.mission))
    if args.mission and args.emblem and not emblem_matches(args.mission, args.emblem):
        raise StoryError(explain_emblem(MISSIONS[args.mission], EMBLEMS[args.emblem]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mission is None or combo[1] == args.mission)
        and (args.emblem is None or combo[2] == args.emblem)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mission_id, emblem_id = rng.choice(sorted(combos))
    gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor_type = args.mentor_type or rng.choice(["aunt", "uncle", "mother", "father"])
    mentor_name = rng.choice(MENTOR_NAMES[mentor_type])

    return StoryParams(
        place=place_id,
        mission=mission_id,
        emblem=emblem_id,
        hero_name=hero_name,
        hero_gender=gender,
        mentor_name=mentor_name,
        mentor_type=mentor_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.emblem not in EMBLEMS:
        raise StoryError(f"(Unknown emblem: {params.emblem})")
    if not mission_supported(params.place, params.mission):
        raise StoryError(explain_place_mission(params.place, params.mission))
    if not emblem_matches(params.mission, params.emblem):
        raise StoryError(explain_emblem(MISSIONS[params.mission], EMBLEMS[params.emblem]))

    world = tell(
        PLACES[params.place],
        MISSIONS[params.mission],
        EMBLEMS[params.emblem],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        mentor_name=params.mentor_name,
        mentor_type=params.mentor_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mission, emblem) combos:\n")
        for place, mission, emblem in combos:
            print(f"  {place:11} {mission:12} {emblem}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name}: {p.mission} at {p.place} with {p.emblem} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
