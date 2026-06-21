#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/compost_bad_ending_space_adventure.py
================================================================

A standalone story world about a pretend space mission in a garden. Two children
are growing a "space crop" for launch day. One child reaches for fresh compost
to make the plants grow faster, even though a grown-up said the compost must be
ready first. Fresh compost is still hot, so it can burn tender roots. If the
grown-up arrives in time, the plants can be saved. If not, the little mission
ends sadly: the plants wilt and launch day is cancelled.

The world model drives the story:
- typed entities carry physical meters and emotional memes
- a short rule engine propagates fresh-compost harm into wilting and sadness
- a reasonableness gate only allows risky compost with vulnerable plants
- an inline ASP twin mirrors both the gate and the ending logic

Run it
------
    python storyworlds/worlds/gpt-5.4/compost_bad_ending_space_adventure.py
    python storyworlds/worlds/gpt-5.4/compost_bad_ending_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/compost_bad_ending_space_adventure.py --compost finished
    python storyworlds/worlds/gpt-5.4/compost_bad_ending_space_adventure.py --response just_water
    python storyworlds/worlds/gpt-5.4/compost_bad_ending_space_adventure.py --verify
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
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    mission: str
    base_word: str
    sendoff: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Compost:
    id: str
    label: str
    phrase: str
    where: str
    warning: str
    hotness: int
    ready: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    bed: str
    crop_word: str
    vulnerability: int
    tender: bool = True
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


def _r_root_stress(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["fresh_compost"] < THRESHOLD:
        return out
    sig = ("root_stress",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    harm = plant.meters["fresh_compost"] + plant.meters["vulnerability"]
    plant.meters["root_stress"] += harm
    for kid_id in ("instigator", "cautioner"):
        if kid_id in world.entities:
            world.get(kid_id).memes["worry"] += 1
    out.append("__stress__")
    return out


def _r_wilt(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["root_stress"] < 3:
        return out
    sig = ("wilt",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["wilting"] += 1
    mission = world.get("mission")
    mission.memes["trouble"] += 1
    out.append("__wilt__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["wilting"] < THRESHOLD:
        return out
    if world.get("mission").meters["saved"] >= THRESHOLD:
        return out
    sig = ("loss",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("mission").memes["sad"] += 1
    for kid_id in ("instigator", "cautioner"):
        if kid_id in world.entities:
            world.get(kid_id).memes["sad"] += 1
    out.append("__loss__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="root_stress", tag="physical", apply=_r_root_stress),
    Rule(name="wilt", tag="physical", apply=_r_wilt),
    Rule(name="loss", tag="emotional", apply=_r_loss),
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


def hazard_at_risk(compost: Compost, plant: Plant) -> bool:
    return (not compost.ready) and compost.hotness > 0 and plant.tender


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(compost: Compost, plant: Plant, delay: int) -> int:
    return compost.hotness + plant.vulnerability + delay


def is_saved(response: Response, compost: Compost, plant: Plant, delay: int) -> bool:
    return response.power >= severity_of(compost, plant, delay)


def explain_rejection(compost: Compost, plant: Plant) -> str:
    if compost.ready:
        return (
            f"(No story: {compost.label} is already ready and gentle for plants, so it would not hurt "
            f"{plant.phrase}. Pick fresh or half-done compost for a real mistake.)"
        )
    if not plant.tender:
        return (
            f"(No story: {plant.phrase} is sturdy enough that this compost shortcut would not make a clear "
            f"problem. Pick a tender plant such as bean sprouts or lettuce seedlings.)"
        )
    return "(No story: this combination does not create a clear compost hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_harm(world: World) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    plant.meters["fresh_compost"] += sim.facts["compost"].hotness
    propagate(sim, narrate=False)
    return {
        "stress": plant.meters["root_stress"],
        "wilting": plant.meters["wilting"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, plant: Plant) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After school, {a.id} and {b.id} turned the little garden bed into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f"In the middle of it all grew {plant.phrase} in {plant.bed}. "
        f"The children called them their {plant.crop_word} for {theme.mission}."
    )


def deadline(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    world.say(
        f'"Launch day is tomorrow," {a.id} said. "{theme.sendoff} needs to look ready tonight!"'
    )
    world.say(
        f"{b.id} crouched beside the bed and brushed a crumb of dirt away. "
        f"Both children wanted the mission to succeed."
    )


def tempt(world: World, a: Entity, compost: Compost) -> None:
    a.memes["haste"] += 1
    world.say(
        f"Then {a.id} spotted {compost.phrase} {compost.where}. "
        f'"I know how to help," {a.pronoun()} said. "If we give the plants lots of compost, '
        f'they will grow faster."'
    )


def warn(world: World, b: Entity, a: Entity, teacher: Entity, compost: Compost) -> None:
    pred = predict_harm(world)
    world.facts["predicted_stress"] = pred["stress"]
    b.memes["caution"] += 1
    extra = " It can still be hot inside." if pred["stress"] >= 3 else ""
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{teacher.label_word.capitalize()} said '
        f'{compost.warning}.{extra} Fresh compost can hurt the roots instead of helping them."'
    )


def defy(world: World, a: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'But {a.id} was thinking about launch day, not patience. '
        f'"Just this once," {a.pronoun()} whispered, and reached for the scoop.'
    )


def apply_compost(world: World, compost: Compost, plant: Entity) -> None:
    plant.meters["fresh_compost"] += compost.hotness
    plant.meters["heat"] += compost.hotness
    propagate(world, narrate=False)
    world.say(
        f"A dark, steamy heap slid down around the stems. At first it looked rich and important, "
        f"almost like moon soil in a picture book. Then a sharp, warm smell rose from the bed."
    )
    if plant.meters["wilting"] >= THRESHOLD:
        world.say(
            f"The little leaves curled at the edges and sagged. The whole tray looked tired in one sad breath."
        )


def alarm(world: World, b: Entity, a: Entity, teacher: Entity) -> None:
    b.memes["fear"] += 1
    world.say(
        f'"{a.id}, stop!" {b.id} cried. "The plants are drooping!"'
    )
    world.say(f'"{teacher.label_word.upper()}!"')


def rescue(world: World, teacher: Entity, response: Response, plant: Entity) -> None:
    plant.meters["fresh_compost"] = 0.0
    plant.meters["root_stress"] = max(0.0, plant.meters["root_stress"] - response.power)
    if plant.meters["root_stress"] < 3:
        plant.meters["wilting"] = 0.0
    world.get("mission").meters["saved"] += 1
    body = response.text
    world.say(
        f"{teacher.label_word.capitalize()} came quickly and {body}."
    )
    world.say(
        "The leaves stayed limp for a minute, but then they lifted a little. The mission was shaken, not lost."
    )


def lesson(world: World, teacher: Entity, a: Entity, b: Entity, compost: Compost) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{teacher.label_word.capitalize()} knelt beside them. "Compost is helpful when it is ready," '
        f'{teacher.pronoun()} said softly. "But {compost.label} is still cooking, and roots are gentle. '
        f'When we rush living things, we can hurt them."'
    )
    world.say(f'"We should have waited," {a.id} murmured. {b.id} nodded.')


def safe_end(world: World, a: Entity, b: Entity, theme: Theme, plant_cfg: Plant) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"The next afternoon, the children came back with small watering cans and patient hands. "
        f"They checked the {plant_cfg.crop_word}, whispered countdown numbers, and let the bed rest."
    )
    world.say(
        f"When sunset turned the glass gold, {a.id} and {b.id} saluted their tiny base. "
        f"This time, {theme.sendoff} would be slow, careful, and true."
    )


def rescue_fail(world: World, teacher: Entity, response: Response, plant_cfg: Plant) -> None:
    body = response.fail
    world.say(f"{teacher.label_word.capitalize()} hurried over and {body}.")
    world.say(
        f"But the heat had already settled deep in the roots of the {plant_cfg.crop_word}. "
        f"More leaves bent lower and lower."
    )


def loss_end(world: World, teacher: Entity, a: Entity, b: Entity, theme: Theme, plant_cfg: Plant) -> None:
    for kid in (a, b):
        kid.memes["sad"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"By morning, the bed that had looked like {theme.scene} looked small and tired again. "
        f"The {plant_cfg.crop_word} hung pale and flat against the soil."
    )
    world.say(
        f'"There will be no launch today," {teacher.label_word} said gently. '
        f'"We will have to plant again and wait the right way."'
    )
    world.say(
        f"{a.id} held the cardboard rocket sign against {a.pronoun('possessive')} chest. "
        f"{b.id} stood very still beside the wilted bed. Their mission had ended before it ever left the ground."
    )


def tell(
    theme: Theme,
    compost: Compost,
    plant_cfg: Plant,
    response: Response,
    *,
    instigator_name: str = "Nia",
    instigator_gender: str = "girl",
    cautioner_name: str = "Owen",
    cautioner_gender: str = "boy",
    teacher_type: str = "teacher",
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(Entity(id="instigator", kind="character", type=instigator_gender, label=instigator_name, role="instigator"))
    b = world.add(Entity(id="cautioner", kind="character", type=cautioner_gender, label=cautioner_name, role="cautioner"))
    teacher = world.add(Entity(id="teacher", kind="character", type=teacher_type, label="the teacher", role="adult"))
    mission = world.add(Entity(id="mission", kind="thing", type="mission", label=theme.mission))
    plant = world.add(Entity(id="plant", kind="thing", type="plant", label=plant_cfg.label, phrase=plant_cfg.phrase))
    plant.meters["vulnerability"] = float(plant_cfg.vulnerability)
    world.facts["compost"] = compost

    play_setup(world, a, b, theme, plant_cfg)
    deadline(world, a, b, theme)

    world.para()
    tempt(world, a, compost)
    warn(world, b, a, teacher, compost)
    defy(world, a)

    world.para()
    apply_compost(world, compost, plant)
    alarm(world, b, a, teacher)

    world.para()
    if is_saved(response, compost, plant_cfg, delay):
        rescue(world, teacher, response, plant)
        lesson(world, teacher, a, b, compost)
        world.para()
        safe_end(world, a, b, theme, plant_cfg)
        outcome = "saved"
    else:
        rescue_fail(world, teacher, response, plant_cfg)
        loss_end(world, teacher, a, b, theme, plant_cfg)
        outcome = "lost"

    world.facts.update(
        theme=theme,
        plant_cfg=plant_cfg,
        response=response,
        outcome=outcome,
        severity=severity_of(compost, plant_cfg, delay),
        delay=delay,
        instigator=a,
        cautioner=b,
        teacher=teacher,
        plant=plant,
        harmed=plant.meters["root_stress"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    theme: str
    compost: str
    plant: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    teacher: str
    delay: int = 0
    seed: Optional[int] = None


THEMES = {
    "mars": Theme(
        id="mars",
        scene="a tiny Mars base",
        rig="A red bucket became a rover, the hose was a silver space snake, and a cardboard box stood up as mission control.",
        mission="the Red Planet Garden",
        base_word="base",
        sendoff="the Red Planet Garden",
        tags={"space"},
    ),
    "moon": Theme(
        id="moon",
        scene="a bright moon station",
        rig="A white stool became a landing rock, a watering wand turned into a comet scanner, and chalk circles marked the airlock.",
        mission="the Moon Sprout Mission",
        base_word="station",
        sendoff="the Moon Sprout Mission",
        tags={"space"},
    ),
    "comet": Theme(
        id="comet",
        scene="a comet camp",
        rig="A wheelbarrow became a shuttle, seed packets were star maps, and a shiny spoon served as the captain's antenna.",
        mission="the Comet Garden Run",
        base_word="camp",
        sendoff="the Comet Garden Run",
        tags={"space"},
    ),
}

COMPOSTS = {
    "fresh": Compost(
        id="fresh",
        label="fresh compost",
        phrase="a tub of fresh compost",
        where="beside the shed",
        warning="the compost had to cool and turn crumbly before anyone used it",
        hotness=2,
        ready=False,
        tags={"compost", "fresh_compost"},
    ),
    "half_done": Compost(
        id="half_done",
        label="half-done compost",
        phrase="a bucket of half-done compost",
        where="near the greenhouse door",
        warning="half-done compost was still busy breaking down",
        hotness=1,
        ready=False,
        tags={"compost", "fresh_compost"},
    ),
    "finished": Compost(
        id="finished",
        label="finished compost",
        phrase="a bucket of finished compost",
        where="on the neat potting bench",
        warning="finished compost was safe because it had rested long enough",
        hotness=0,
        ready=True,
        tags={"compost"},
    ),
}

PLANTS = {
    "beans": Plant(
        id="beans",
        label="bean sprouts",
        phrase="a tray of bean sprouts",
        bed="a long wooden planter",
        crop_word="bean sprouts",
        vulnerability=2,
        tender=True,
        tags={"beans", "tender_plants"},
    ),
    "lettuce": Plant(
        id="lettuce",
        label="lettuce seedlings",
        phrase="a row of lettuce seedlings",
        bed="a shallow silver bed",
        crop_word="lettuce seedlings",
        vulnerability=2,
        tender=True,
        tags={"lettuce", "tender_plants"},
    ),
    "pumpkin": Plant(
        id="pumpkin",
        label="pumpkin vines",
        phrase="a patch of young pumpkin vines",
        bed="a wide soil box",
        crop_word="pumpkin vines",
        vulnerability=0,
        tender=False,
        tags={"pumpkin"},
    ),
}

RESPONSES = {
    "repot": Response(
        id="repot",
        sense=3,
        power=4,
        text="carefully scooped the hot compost away, lifted the little plants into fresh soil, and watered them with a gentle stream",
        fail="carefully scooped the hot compost away and watered the bed, but the roots had already been burned too long",
        qa_text="scooped the hot compost away, replanted the seedlings in fresh soil, and watered them",
        tags={"rescue", "replant"},
    ),
    "scrape_mix": Response(
        id="scrape_mix",
        sense=3,
        power=3,
        text="scraped most of the fresh compost off, mixed cool soil back in, and watered the bed right away",
        fail="scraped the top layer away and watered quickly, but the heat underneath had already done too much harm",
        qa_text="scraped the fresh compost off, mixed in cool soil, and watered the bed",
        tags={"rescue", "soil"},
    ),
    "just_water": Response(
        id="just_water",
        sense=1,
        power=1,
        text="splashed water on the bed",
        fail="splashed water on the bed, but that could not undo the heat in the roots",
        qa_text="splashed water on the bed",
        tags={"water"},
    ),
}

GIRL_NAMES = ["Nia", "Luna", "Mira", "Ava", "Zoe", "Ella", "Ruby", "Nora"]
BOY_NAMES = ["Owen", "Leo", "Max", "Finn", "Theo", "Sam", "Eli", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for compost_id, compost in COMPOSTS.items():
            for plant_id, plant in PLANTS.items():
                if hazard_at_risk(compost, plant):
                    combos.append((theme_id, compost_id, plant_id))
    return combos


KNOWLEDGE = {
    "compost": [
        (
            "What is compost?",
            "Compost is old food scraps and plant bits that have broken down into dark soil-like stuff. Gardeners use it to help plants grow.",
        )
    ],
    "fresh_compost": [
        (
            "Why can fresh compost hurt plants?",
            "Fresh compost can still be hot while it breaks down. That heat can hurt tender roots instead of helping them.",
        )
    ],
    "beans": [
        (
            "What are bean sprouts?",
            "Bean sprouts are very young bean plants. They are small and tender, so they need gentle care.",
        )
    ],
    "lettuce": [
        (
            "Why are lettuce seedlings delicate?",
            "Lettuce seedlings are tiny young plants with soft roots and leaves. They can wilt quickly if something stresses them.",
        )
    ],
    "replant": [
        (
            "Why does replanting sometimes help a hurt seedling?",
            "Moving a seedling into fresh, cooler soil can give its roots a safer place to recover. It only works if you do it soon enough.",
        )
    ],
    "soil": [
        (
            "Why do roots need cool, gentle soil?",
            "Roots take in water and plant food from the soil around them. If the soil is too hot or harsh, the roots can get hurt.",
        )
    ],
    "space": [
        (
            "Why do children pretend a garden is a space base?",
            "Pretend play lets ordinary things become part of an adventure. A planter can feel like a tiny world when children imagine it that way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["space", "compost", "fresh_compost", "beans", "lettuce", "replant", "soil"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    plant = f["plant_cfg"]
    compost = world.facts["compost"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            f'Write a short space-adventure story for a 3-to-5-year-old that includes the word "compost" and ends sadly.',
            f"Tell a story where children pretend their garden is {theme.scene}, but one child uses {compost.label} too soon and the {plant.crop_word} wilt.",
            f'Write a gentle bad-ending cautionary tale about rushing a garden mission, using the word "compost" and ending with a cancelled launch.',
        ]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the word "compost".',
        f"Tell a story where children pretend their garden is {theme.scene}, make a compost mistake, and a grown-up saves the {plant.crop_word} in time.",
        f'Write a simple story about patience, plants, and compost, with a playful space-mission feeling and a safe ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    teacher = f["teacher"]
    theme = f["theme"]
    plant_cfg = f["plant_cfg"]
    compost = world.facts["compost"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label}, two children who turned a garden into {theme.scene}. Their teacher is the grown-up who comes to help.",
        ),
        (
            "What were they pretending?",
            f"They were pretending their garden bed was part of {theme.mission}. That space game made the plants feel like a mission they wanted to hurry along.",
        ),
        (
            f"Why did {b.label} warn {a.label} about the compost?",
            f"{b.label} remembered that {compost.label} was not ready yet. It could still be hot inside, so it might hurt the roots instead of helping them grow.",
        ),
        (
            "What happened when the compost touched the plants?",
            f"The bed gave off a warm, sharp smell and the {plant_cfg.crop_word} began to droop. The trouble started because the compost was still too fresh for tender roots.",
        ),
    ]
    if f["outcome"] == "saved":
        qa.append(
            (
                "How were the plants saved?",
                f"The teacher {response.qa_text}. That worked because help came quickly, before the heat had hurt the roots for too long.",
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that compost must be ready before you use it on delicate plants. They also learned that living things cannot be rushed just because a pretend mission feels exciting.",
            )
        )
    else:
        qa.append(
            (
                "Why was there no launch the next day?",
                f"There was no launch because the {plant_cfg.crop_word} had wilted too badly to recover. The mission ended sadly when the rushed shortcut hurt the plants.",
            )
        )
        qa.append(
            (
                "What did the ending show had changed?",
                f"At first the bed felt like a shining space base, but by morning it looked tired and still. The wilted plants and the unused rocket sign showed that the adventure had turned into a hard lesson.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["theme"].tags) | set(world.facts["plant_cfg"].tags) | set(world.facts["compost"].tags)
    if world.facts["outcome"] == "saved":
        tags |= set(world.facts["response"].tags)
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
        if e.label and e.label != e.id:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="mars",
        compost="fresh",
        plant="beans",
        response="repot",
        instigator="Nia",
        instigator_gender="girl",
        cautioner="Owen",
        cautioner_gender="boy",
        teacher="teacher",
        delay=0,
    ),
    StoryParams(
        theme="moon",
        compost="half_done",
        plant="lettuce",
        response="scrape_mix",
        instigator="Luna",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        teacher="teacher",
        delay=0,
    ),
    StoryParams(
        theme="comet",
        compost="fresh",
        plant="lettuce",
        response="scrape_mix",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        teacher="teacher",
        delay=2,
    ),
    StoryParams(
        theme="mars",
        compost="fresh",
        plant="beans",
        response="repot",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Mira",
        cautioner_gender="girl",
        teacher="teacher",
        delay=1,
    ),
]


ASP_RULES = r"""
hazard(C, P) :- risky(C), tender(P).
valid(T, C, P) :- theme(T), compost(C), plant(P), hazard(C, P).

severity(S) :- chosen_compost(C), hotness(C, H), chosen_plant(P), vulnerability(P, V), delay(D), S = H + V + D.
saved :- chosen_response(R), power(R, P), severity(S), P >= S.
outcome(saved) :- saved.
outcome(lost) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for compost_id, compost in COMPOSTS.items():
        lines.append(asp.fact("compost", compost_id))
        lines.append(asp.fact("hotness", compost_id, compost.hotness))
        if not compost.ready and compost.hotness > 0:
            lines.append(asp.fact("risky", compost_id))
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        lines.append(asp.fact("vulnerability", plant_id, plant.vulnerability))
        if plant.tender:
            lines.append(asp.fact("tender", plant_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("power", response_id, response.power))
        lines.append(asp.fact("sense", response_id, response.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_compost", params.compost),
            asp.fact("chosen_plant", params.plant),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "saved" if is_saved(RESPONSES[params.response], COMPOSTS[params.compost], PLANTS[params.plant], params.delay) else "lost"


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

    p_sens = {r.id for r in sensible_responses()}
    expected = {"repot", "scrape_mix"}
    if p_sens == expected:
        print(f"OK: sensible responses match ({sorted(p_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(p_sens)} expected={sorted(expected)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story during smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a pretend space garden, risky compost, and a lesson about patience."
    )
    ap.add_argument("--theme", choices=sorted(THEMES))
    ap.add_argument("--compost", choices=sorted(COMPOSTS))
    ap.add_argument("--plant", choices=sorted(PLANTS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--teacher", choices=["teacher"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the roots sit in the hot compost before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.compost and args.plant:
        compost = COMPOSTS[args.compost]
        plant = PLANTS[args.plant]
        if not hazard_at_risk(compost, plant):
            raise StoryError(explain_rejection(compost, plant))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.compost is None or combo[1] == args.compost)
        and (args.plant is None or combo[2] == args.plant)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, compost, plant = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_name(rng)
    cautioner, cg = _pick_name(rng, avoid=instigator)
    teacher = args.teacher or "teacher"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        theme=theme,
        compost=compost,
        plant=plant,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        teacher=teacher,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"Unknown theme: {params.theme}")
    if params.compost not in COMPOSTS:
        raise StoryError(f"Unknown compost: {params.compost}")
    if params.plant not in PLANTS:
        raise StoryError(f"Unknown plant: {params.plant}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")

    compost = COMPOSTS[params.compost]
    plant = PLANTS[params.plant]
    response = RESPONSES[params.response]

    if not hazard_at_risk(compost, plant):
        raise StoryError(explain_rejection(compost, plant))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        THEMES[params.theme],
        compost,
        plant,
        response,
        instigator_name=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner_name=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        teacher_type=params.teacher,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (theme, compost, plant) combos:\n")
        for theme, compost, plant in combos:
            print(f"  {theme:8} {compost:10} {plant}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.instigator} & {p.cautioner}: {p.compost} on {p.plant} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
