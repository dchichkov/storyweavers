#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/asthma_cellophane_curiosity_space_adventure.py
=========================================================================

A standalone story world about curious children playing space adventure, a risky
idea involving cellophane over a pretend helmet, and an asthma-safe fix. The
world models physical meters and emotional memes, checks for reasonable
combinations, and includes an inline ASP twin for parity checks.

Run it
------
    python storyworlds/worlds/gpt-5.4/asthma_cellophane_curiosity_space_adventure.py
    python storyworlds/worlds/gpt-5.4/asthma_cellophane_curiosity_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/asthma_cellophane_curiosity_space_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/asthma_cellophane_curiosity_space_adventure.py --qa
    python storyworlds/worlds/gpt-5.4/asthma_cellophane_curiosity_space_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/asthma_cellophane_curiosity_space_adventure.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CURIOSITY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
    age: int = 0
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
class Mission:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    goal: str
    dark_spot: str
    place_word: str
    plural_role: str
    send_off: str


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    where: str
    transparent: bool = False
    blocks_air: bool = False
    crinkle: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rebuild:
    id: str
    label: str
    text: str
    keeps_air_open: bool = True
    gives_view: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
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
        return [e for e in self.entities.values() if e.role in {"explorer", "partner"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_breathing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    room = world.entities.get("room")
    helmet = world.entities.get("helmet")
    if not hero or not room or not helmet:
        return out
    if helmet.meters["air_blocked"] < THRESHOLD:
        return out
    sig = ("breathing", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["tight_breathing"] += 1
    room.meters["danger"] += 1
    hero.memes["fear"] += 1
    hero.memes["need_help"] += 1
    partner = world.entities.get("partner")
    if partner is not None:
        partner.memes["fear"] += 1
    out.append("__breathing__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="breathing", tag="physical", apply=_r_breathing),
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
        for s in produced:
            world.say(s)
    return produced


def risky_combo(material: Material, rebuild: Rebuild) -> bool:
    return material.transparent and material.blocks_air and rebuild.gives_view and rebuild.keeps_air_open


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def exertion_severity(delay: int) -> int:
    return 2 + delay


def is_relieved(response: Response, delay: int) -> bool:
    return response.power >= exertion_severity(delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, explorer_age: int, partner_age: int, trait: str) -> bool:
    older_partner = relation == "siblings" and partner_age > explorer_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_partner else 0.0)
    return older_partner and authority > CURIOSITY_INIT


def predict_breathing(world: World, material_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    helmet = sim.get("helmet")
    material = MATERIALS[material_id]
    helmet.meters["air_blocked"] += 1 if material.blocks_air else 0
    hero.memes["curiosity"] += 1
    propagate(sim, narrate=False)
    return {
        "tight_breathing": hero.meters["tight_breathing"],
        "danger": sim.get("room").meters["danger"],
    }


def play_setup(world: World, hero: Entity, partner: Entity, mission: Mission) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"One rainy afternoon, {hero.id} and {partner.id} turned the living room into "
        f"{mission.scene}. {mission.rig}"
    )
    world.say(
        f"'{mission.title_a} {hero.id} and {mission.title_b} {partner.id}!' {hero.id} said. "
        f"'Let's reach {mission.goal}!'"
    )


def mention_asthma(world: World, hero: Entity) -> None:
    inhaler = hero.attrs.get("inhaler", "inhaler")
    world.say(
        f"{hero.id} was especially proud to be the captain because {hero.pronoun()} kept "
        f"{hero.pronoun('possessive')} asthma {inhaler} nearby and liked doing brave things carefully."
    )


def need_helmet(world: World, partner: Entity, mission: Mission) -> None:
    world.say(
        f"But {mission.dark_spot} looked deep and shadowy, like a real {mission.place_word} with no air."
    )
    world.say(
        f"{partner.id} peered into it and whispered, 'A space explorer needs a helmet window to see.'"
    )


def tempt(world: World, hero: Entity, material: Material) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"On the craft shelf, {hero.id} spotted {material.phrase} {material.where}. "
        f"{material.crinkle.capitalize()} sounded almost like tiny stars rubbing together."
    )
    world.say(
        f"'What if we use {material.label} for the helmet visor?' {hero.id} asked, full of curiosity."
    )


def warn(world: World, partner: Entity, hero: Entity, material: Material, parent: Entity) -> None:
    pred = predict_breathing(world, material.id)
    partner.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if partner.memes["caution"] >= 6:
        extra = f" {partner.pronoun().capitalize()} already knew that shiny ideas were not always safe ideas."
    world.say(
        f"{partner.id} shook {partner.pronoun('possessive')} head. "
        f"'Not over your face. You have asthma, and air has to move in and out.'{extra}"
    )
    world.say(
        f"{parent.label_word.capitalize()} had said the same thing before: a pretend helmet should never make breathing harder."
    )


def back_down(world: World, hero: Entity, partner: Entity, material: Material, parent: Entity) -> None:
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    hero.memes["curiosity"] = 0.0
    sib = "brother" if partner.type == "boy" else "sister"
    world.say(
        f"{hero.id} looked at {material.label}, then at {partner.id}, {hero.pronoun('possessive')} big {sib}, "
        f"and let out a slow breath. 'Okay,' {hero.pronoun()} said. 'I want to explore, not make my chest feel tight.'"
    )
    world.say(
        f"They left the {material.label} on the table and went to ask {parent.label_word} for a better idea."
    )


def defy(world: World, hero: Entity, partner: Entity, material: Material) -> None:
    hero.memes["defiance"] += 1
    older_hero = hero.attrs.get("relation") == "siblings" and hero.age > partner.age
    if older_hero:
        world.say(
            f"'I just want to see what it looks like,' {hero.id} said, and because {hero.pronoun()} was the older one, "
            f"{partner.id} could not stop {hero.pronoun('object')} in time."
        )
    else:
        world.say(
            f"'Just for one countdown,' {hero.id} said, still too curious to listen."
        )


def try_visor(world: World, hero: Entity, material: Material) -> None:
    helmet = world.get("helmet")
    helmet.meters["air_blocked"] += 1 if material.blocks_air else 0
    helmet.meters["visor_on"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} stretched the {material.label} across the front of the cardboard helmet. "
        f"It shone and crackled, and for half a second the costume really did look spacey."
    )
    if hero.meters["tight_breathing"] >= THRESHOLD:
        world.say(
            f"Then {hero.id}'s smile changed. The air felt wrong at once, and {hero.pronoun('possessive')} breathing turned tight and small."
        )


def alarm(world: World, partner: Entity, hero: Entity, parent: Entity) -> None:
    if hero.meters["tight_breathing"] >= THRESHOLD:
        world.say(f"'{hero.id}, stop!' {partner.id} cried.")
        world.say(
            f"'{parent.label_word.upper()}! {hero.id} needs help!'"
        )


def rescue(world: World, parent: Entity, hero: Entity, response: Response) -> None:
    hero.meters["tight_breathing"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.get("helmet").meters["air_blocked"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    partner = world.get("partner")
    partner.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {response.text}."
    )


def lesson(world: World, parent: Entity, hero: Entity, material: Material) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt beside {hero.id} and spoke softly. "
        f"'Your curiosity is a good thing,' {parent.pronoun()} said, 'but we never put {material.label} over a face. "
        f"With asthma, safe breathing comes first.'"
    )
    world.say(
        f"{hero.id} nodded and held {hero.pronoun('possessive')} helmet in both hands. "
        f"'Next time I'll ask before I test a space idea,' {hero.pronoun()} said."
    )


def slower_recovery(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["tired"] += 1
    world.say(
        f"For a while, the adventure had to grow very quiet. {hero.id} sat propped up on the sofa, "
        f"breathing more slowly while {parent.label_word} stayed beside {hero.pronoun('object')}."
    )
    world.say(
        f"When the tight feeling finally faded, {hero.id} knew even more strongly that pretend gear must never get in the way of real air."
    )


def rebuild_safe(world: World, parent: Entity, hero: Entity, partner: Entity, mission: Mission, material: Material, rebuild: Rebuild) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"After that, they rebuilt the mission a safer way. {parent.label_word.capitalize()} {rebuild.text}"
    )
    world.say(
        f"The {material.label} still got to sparkle, but now it stayed off faces where it belonged."
    )
    world.say(
        f"Soon {hero.id} and {partner.id} were back in {mission.plural_role}, and this time they {mission.send_off}."
    )


def tell(
    mission: Mission,
    material: Material,
    rebuild: Rebuild,
    response: Response,
    explorer: str = "Lily",
    explorer_gender: str = "girl",
    partner_name: str = "Tom",
    partner_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    explorer_age: int = 5,
    partner_age: int = 7,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=explorer_gender,
        label=explorer,
        role="explorer",
        age=explorer_age,
        traits=["curious"],
        attrs={"name": explorer, "relation": relation, "inhaler": "inhaler"},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        age=partner_age,
        traits=[trait],
        attrs={"name": partner_name, "relation": relation, "trust": trust},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(id="room", type="room", label="the room"))
    helmet = world.add(Entity(id="helmet", type="helmet", label="cardboard helmet"))
    hero.memes["curiosity"] = CURIOSITY_INIT
    partner.memes["caution"] = initial_caution(trait)
    partner.memes["trust"] = float(trust)
    hero.tags.add("asthma")
    helmet.tags.add("helmet")

    world.facts["hero_name"] = explorer
    world.facts["partner_name"] = partner_name

    play_setup(world, hero, partner, mission)
    mention_asthma(world, hero)
    need_helmet(world, partner, mission)

    world.para()
    tempt(world, hero, material)
    warn(world, partner, hero, material, parent)

    averted = would_avert(relation, explorer_age, partner_age, trait)
    if averted:
        back_down(world, hero, partner, material, parent)
        world.para()
        rebuild_safe(world, parent, hero, partner, mission, material, rebuild)
        outcome = "averted"
        severity = 0
    else:
        defy(world, hero, partner, material)
        world.para()
        try_visor(world, hero, material)
        alarm(world, partner, hero, parent)
        severity = exertion_severity(delay)
        hero.meters["severity"] = float(severity)
        relieved = is_relieved(response, delay)
        world.para()
        rescue(world, parent, hero, response)
        if relieved:
            lesson(world, parent, hero, material)
            world.para()
            rebuild_safe(world, parent, hero, partner, mission, material, rebuild)
            outcome = "relieved"
        else:
            slower_recovery(world, parent, hero)
            world.para()
            rebuild_safe(world, parent, hero, partner, mission, material, rebuild)
            outcome = "rested"

    world.facts.update(
        mission=mission,
        material=material,
        rebuild=rebuild,
        response=response,
        hero=hero,
        partner=partner,
        parent=parent,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        relieved=(outcome == "relieved"),
        averted=(outcome == "averted"),
    )
    return world


MISSIONS = {
    "moon": Mission(
        id="moon",
        scene="a silver moon base",
        rig="The sofa was their rocket, a laundry basket was the rover, and a blanket tunnel became the moon cave.",
        title_a="Captain",
        title_b="Scout",
        goal="the moon cave",
        dark_spot="the blanket tunnel",
        place_word="crater",
        plural_role="their space adventure",
        send_off="rolled the rover toward the cave, bright-eyed and careful",
    ),
    "mars": Mission(
        id="mars",
        scene="a dusty Mars station",
        rig="The sofa was their landing ship, two pillows were red hills, and a chair cave became the research tunnel.",
        title_a="Commander",
        title_b="Pilot",
        goal="the red tunnel",
        dark_spot="the chair cave",
        place_word="tunnel",
        plural_role="their Mars mission",
        send_off="marched across the red pillows as if the planet had room for both wonder and good choices",
    ),
    "comet": Mission(
        id="comet",
        scene="a glowing comet ship",
        rig="The sofa was their comet ship, a box fan was the star engine, and a fort under the table became the ice cave.",
        title_a="Captain",
        title_b="Navigator",
        goal="the ice cave",
        dark_spot="the fort under the table",
        place_word="cave",
        plural_role="their space adventure",
        send_off="slid under the table fort with their safe gear and their imaginations still blazing",
    ),
}

MATERIALS = {
    "cellophane": Material(
        id="cellophane",
        label="cellophane",
        phrase="a roll of blue cellophane",
        where="beside the crayons",
        transparent=True,
        blocks_air=True,
        crinkle="it crinkled",
        tags={"cellophane", "breathing"},
    ),
    "plastic_bag": Material(
        id="plastic_bag",
        label="a plastic bag",
        phrase="a clear plastic bag",
        where="from the art bin",
        transparent=True,
        blocks_air=True,
        crinkle="it rustled",
        tags={"bag", "breathing"},
    ),
    "foil": Material(
        id="foil",
        label="foil",
        phrase="a sheet of shiny foil",
        where="on the kitchen counter",
        transparent=False,
        blocks_air=True,
        crinkle="it crackled",
        tags={"foil"},
    ),
}

REBUILDS = {
    "helmet_window": Rebuild(
        id="helmet_window",
        label="helmet window",
        text="taped the shiny sheet onto the outside of the cardboard helmet like a little side window, leaving the whole front and bottom open for easy breathing",
        keeps_air_open=True,
        gives_view=True,
        tags={"safe_gear", "cellophane"},
    ),
    "cockpit_window": Rebuild(
        id="cockpit_window",
        label="cockpit window",
        text="turned the shiny sheet into a spaceship window on the cardboard rocket instead of a face covering, so the explorers could peek through it from behind",
        keeps_air_open=True,
        gives_view=True,
        tags={"safe_gear", "cellophane"},
    ),
    "paper_stars": Rebuild(
        id="paper_stars",
        label="paper stars",
        text="cut the shiny sheet into tiny stars for the control panel, but it no longer worked as a window at all",
        keeps_air_open=True,
        gives_view=False,
        tags={"craft"},
    ),
}

RESPONSES = {
    "remove_inhaler": Response(
        id="remove_inhaler",
        sense=3,
        power=3,
        text="peeled the cellophane away at once, sat the child upright, and helped with the prescribed inhaler and spacer until the breathing settled",
        qa_text="removed the cellophane right away and helped with the prescribed inhaler and spacer",
        tags={"asthma", "inhaler"},
    ),
    "remove_rest": Response(
        id="remove_rest",
        sense=2,
        power=2,
        text="lifted the helmet away, opened the room to calm air, and stayed close while the child rested and took slow breaths",
        qa_text="lifted the helmet away and stayed close while the child rested and took slow breaths",
        tags={"asthma", "rest"},
    ),
    "poke_holes": Response(
        id="poke_holes",
        sense=1,
        power=1,
        text="poked little holes in the cellophane and tried to keep the game going",
        qa_text="poked little holes in the cellophane",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "steady", "sensible", "kind", "thoughtful"]


@dataclass
class StoryParams:
    mission: str
    material: str
    rebuild: str
    response: str
    explorer: str
    explorer_gender: str
    partner: str
    partner_gender: str
    parent: str
    trait: str
    delay: int = 0
    explorer_age: int = 5
    partner_age: int = 7
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for material_id, material in MATERIALS.items():
            for rebuild_id, rebuild in REBUILDS.items():
                if risky_combo(material, rebuild):
                    combos.append((mission_id, material_id, rebuild_id))
    return combos


KNOWLEDGE = {
    "asthma": [
        (
            "What is asthma?",
            "Asthma is a breathing problem some people have. Their airways can get tight, so calm help and the right medicine can make breathing easier.",
        )
    ],
    "cellophane": [
        (
            "What is cellophane?",
            "Cellophane is a thin, crinkly, see-through wrapping sheet. It can be fun for crafts, but it does not belong over anyone's mouth or nose.",
        )
    ],
    "breathing": [
        (
            "Why should you never put plastic or wrapping over a face?",
            "A face needs open air for easy breathing. Wrapping can make it hard or unsafe to breathe, so it should stay away from mouths and noses.",
        )
    ],
    "inhaler": [
        (
            "What does an inhaler do?",
            "An inhaler is medicine some people use for asthma. It can help open the airways so breathing gets easier.",
        )
    ],
    "rest": [
        (
            "Why do slow breaths and calm help when someone feels tight in the chest?",
            "Calm help can stop the feeling from getting worse, and slow breaths can help the body settle. A grown-up should stay close and follow the child's asthma plan.",
        )
    ],
    "safe_gear": [
        (
            "How can you make a pretend helmet safely?",
            "You can decorate a helmet or put pretend windows on the outside, but you should never cover a real face. Safe pretend gear leaves room for easy breathing.",
        )
    ],
}
KNOWLEDGE_ORDER = ["asthma", "cellophane", "breathing", "inhaler", "rest", "safe_gear"]


def pair_noun(hero: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and partner.type == "boy":
            return "two brothers"
        if hero.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    mission = f["mission"]
    material = f["material"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a space-adventure story for a 3-to-5-year-old that includes the word "{material.label}" and teaches an asthma-safe choice before anything goes wrong.',
            f"Tell a gentle story where {hero.label} gets curious about using {material.label} on a pretend helmet, but {partner.label} stops the idea and the mission continues safely.",
            "Write a child-facing story about curiosity, breathing safely, and turning a risky craft idea into a smarter spaceship design.",
        ]
    if outcome == "rested":
        return [
            f'Write a space-adventure story for a 3-to-5-year-old that includes the words "asthma" and "{material.label}".',
            f"Tell a cautious story where curiosity leads to a breathing scare during a pretend {mission.id} mission, and the child has to rest before playing again.",
            "Write a simple story where a grown-up responds calmly to a bad helmet idea and the ending shows a safer rebuild.",
        ]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the words "asthma" and "{material.label}".',
        f"Tell a gentle story where {hero.label} gets too curious about a shiny pretend visor, then a grown-up helps and the children rebuild the game safely.",
        "Write a story where curiosity causes a problem, but the ending proves the children learned how to keep play and breathing safe at the same time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    parent = f["parent"]
    mission = f["mission"]
    material = f["material"]
    rebuild = f["rebuild"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(hero, partner, relation)
    hero_name = hero.label
    partner_name = partner.label
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero_name} and {partner_name}, who were playing a space adventure. It also includes {hero_name}'s {pw}, who helped them choose a safer way to play.",
        ),
        (
            "What were the children pretending to do?",
            f"They turned the living room into {mission.scene} and planned to reach {mission.goal}. The dark pretend place made them want a helmet window for the mission.",
        ),
        (
            f"Why did {hero_name} want to use {material.label}?",
            f"{hero_name} was curious because the shiny, crinkly material looked like a real space visor. The idea seemed clever for a moment because it was see-through and dramatic.",
        ),
        (
            f"Why was {partner_name} worried?",
            f"{partner_name} was worried because {hero_name} has asthma and a face needs open air. Covering a pretend helmet the wrong way could make breathing harder instead of helping the game.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed the story before anyone got hurt?",
                f"{hero_name} listened when {partner_name} warned {hero.pronoun('object')}, so the risky test never happened. They asked {pw} for help and turned the idea into a safer build instead.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero_name} tried the visor idea?",
                f"The cellophane made the air feel wrong, and {hero_name}'s breathing turned tight. That scare happened because the shiny sheet was put where real air needed to move freely.",
            )
        )
        qa.append(
            (
                f"How did {hero_name}'s {pw} help?",
                f"{pw.capitalize()} {response.qa_text}. The fast, calm help stopped the problem from growing bigger.",
            )
        )
        if f["outcome"] == "rested":
            qa.append(
                (
                    "How did the adventure continue after the scare?",
                    f"It slowed down first, because {hero_name} needed quiet time to recover. Later the children rebuilt the mission safely, which showed they had learned from the mistake.",
                )
            )
        else:
            qa.append(
                (
                    "How did the story end?",
                    f"It ended with a safer spaceship design using {material.label} in a new way. The final image shows the children exploring again with room to breathe and a better plan.",
                )
            )
    qa.append(
        (
            f"What did the children do with {material.label} in the safe version?",
            f"They used it for {rebuild.label} instead of putting it over a face. That kept the sparkle of the space game while protecting breathing.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"asthma"}
    material = world.facts["material"]
    response = world.facts["response"]
    rebuild = world.facts["rebuild"]
    if "cellophane" in material.tags:
        tags.add("cellophane")
    if "breathing" in material.tags or material.blocks_air:
        tags.add("breathing")
    tags |= set(response.tags)
    tags |= set(rebuild.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="moon",
        material="cellophane",
        rebuild="helmet_window",
        response="remove_inhaler",
        explorer="Lily",
        explorer_gender="girl",
        partner="Tom",
        partner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        explorer_age=5,
        partner_age=7,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        mission="mars",
        material="cellophane",
        rebuild="cockpit_window",
        response="remove_rest",
        explorer="Ben",
        explorer_gender="boy",
        partner="Mia",
        partner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=1,
        explorer_age=6,
        partner_age=6,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        mission="comet",
        material="plastic_bag",
        rebuild="helmet_window",
        response="remove_inhaler",
        explorer="Zoe",
        explorer_gender="girl",
        partner="Nora",
        partner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=0,
        explorer_age=4,
        partner_age=7,
        relation="siblings",
        trust=4,
    ),
]


def explain_rejection(material: Material, rebuild: Rebuild) -> str:
    if not material.transparent:
        return (
            f"(No story: {material.label} is shiny, but it is not see-through, so it does not honestly tempt anyone as a visor.)"
        )
    if not material.blocks_air:
        return (
            f"(No story: {material.label} would not create the breathing risk this world is built around.)"
        )
    if not rebuild.gives_view:
        return (
            f"(No story: {rebuild.label} does not solve the same 'I need a window' problem, so it is too weak as the story's fix.)"
        )
    if not rebuild.keeps_air_open:
        return (
            f"(No story: {rebuild.label} still does not leave enough room for easy breathing.)"
        )
    return "(No story: this combination does not fit the world's breathing-safety logic.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.explorer_age, params.partner_age, params.trait):
        return "averted"
    return "relieved" if is_relieved(RESPONSES[params.response], params.delay) else "rested"


ASP_RULES = r"""
valid(Mis, Mat, Reb) :- mission(Mis), material(Mat), rebuild(Reb),
                        transparent(Mat), blocks_air(Mat),
                        gives_view(Reb), keeps_air_open(Reb).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

caution_now(5) :- trait(T), is_cautious(T).
caution_now(3) :- trait(T), not is_cautious(T).

older_partner :- relation(siblings), explorer_age(EA), partner_age(PA), PA > EA.
authority(C + 1 + B) :- caution_now(C), bonus(B), older_partner.
authority(C + 1 + 0) :- caution_now(C), not older_partner.
bonus(3) :- older_partner.

averted :- older_partner, authority(A), curiosity_init(CI), A > CI.

severity(2 + D) :- delay(D).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(relieved) :- not averted, contained.
outcome(rested) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        if material.transparent:
            lines.append(asp.fact("transparent", material_id))
        if material.blocks_air:
            lines.append(asp.fact("blocks_air", material_id))
    for rebuild_id, rebuild in REBUILDS.items():
        lines.append(asp.fact("rebuild", rebuild_id))
        if rebuild.gives_view:
            lines.append(asp.fact("gives_view", rebuild_id))
        if rebuild.keeps_air_open:
            lines.append(asp.fact("keeps_air_open", rebuild_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("explorer_age", params.explorer_age),
            asp.fact("partner_age", params.partner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
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
            raise StoryError("smoke test produced an empty story")
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: curiosity, asthma safety, and a space-adventure costume problem."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--rebuild", choices=REBUILDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra exertion before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.rebuild:
        material = MATERIALS[args.material]
        rebuild = REBUILDS[args.rebuild]
        if not risky_combo(material, rebuild):
            raise StoryError(explain_rejection(material, rebuild))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.material is None or combo[1] == args.material)
        and (args.rebuild is None or combo[2] == args.rebuild)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission, material, rebuild = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    explorer, explorer_gender = _pick_kid(rng)
    partner, partner_gender = _pick_kid(rng, avoid=explorer)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    relation = rng.choice(["siblings", "friends"])
    explorer_age, partner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(3, 8)
    return StoryParams(
        mission=mission,
        material=material,
        rebuild=rebuild,
        response=response,
        explorer=explorer,
        explorer_gender=explorer_gender,
        partner=partner,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        explorer_age=explorer_age,
        partner_age=partner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.rebuild not in REBUILDS:
        raise StoryError(f"(Unknown rebuild: {params.rebuild})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not risky_combo(MATERIALS[params.material], REBUILDS[params.rebuild]):
        raise StoryError(explain_rejection(MATERIALS[params.material], REBUILDS[params.rebuild]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        mission=MISSIONS[params.mission],
        material=MATERIALS[params.material],
        rebuild=REBUILDS[params.rebuild],
        response=RESPONSES[params.response],
        explorer=params.explorer,
        explorer_gender=params.explorer_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        explorer_age=params.explorer_age,
        partner_age=params.partner_age,
        relation=params.relation,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.explorer).replace("partner", params.partner),
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
        print(f"{len(combos)} compatible (mission, material, rebuild) combos:\n")
        for mission, material, rebuild in combos:
            print(f"  {mission:8} {material:12} {rebuild}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.explorer} & {p.partner}: {p.material} on the {p.mission} mission ({outcome_of(p)})"
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
