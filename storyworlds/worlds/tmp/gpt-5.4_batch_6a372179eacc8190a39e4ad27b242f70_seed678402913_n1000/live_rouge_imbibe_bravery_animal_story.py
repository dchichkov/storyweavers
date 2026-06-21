#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/live_rouge_imbibe_bravery_animal_story.py
====================================================================

A standalone story world for a small animal tale about bravery.

Seed obligations carried directly into the world:
- "live" appears in the opening about where the animals live.
- "rouge" appears in the healing drink: rouge berry tea.
- "imbibe" appears in the owl healer's instruction about drinking the tea.

World premise
-------------
A small animal needs a warm drink from the owl healer. The drink must be carried
across a forest obstacle by a young helper. The helper's bravery, the obstacle's
scariness, and the chosen tool all matter. The story always ends in a plausible,
happy rescue; unreasonable choices are rejected before narration.

Run it
------
python storyworlds/worlds/gpt-5.4/live_rouge_imbibe_bravery_animal_story.py
python storyworlds/worlds/gpt-5.4/live_rouge_imbibe_bravery_animal_story.py --all
python storyworlds/worlds/gpt-5.4/live_rouge_imbibe_bravery_animal_story.py --obstacle misty_log --tool glow_bug_lantern
python storyworlds/worlds/gpt-5.4/live_rouge_imbibe_bravery_animal_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "aunt", "doe", "hen", "girl"}
        male = {"father", "uncle", "buck", "boar", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        if self.label:
            return self.label
        return self.type


@dataclass
class Setting:
    id: str
    home: str
    opening: str
    healer_place: str
    patient_place: str
    landmark: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    kind: str
    scare: int
    risk_line: str
    crossing_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    bonus: int
    carry_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mentor:
    id: str
    type: str
    label: str
    support: int
    comfort_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Patient:
    id: str
    type: str
    label: str
    ailment: str
    weak_line: str
    recovery_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HeroKind:
    id: str
    type: str
    label: str
    likes_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    tool: str
    mentor: str
    patient: str
    trait: str
    hero_kind: str
    hero_name: str
    patient_name: str
    seed: Optional[int] = None


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


def _r_wobble(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None or hero.meters["crossing"] < THRESHOLD:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    margin = world.facts.get("margin", 0)
    if margin > 1:
        return []
    world.fired.add(sig)
    hero.meters["wobble"] += 1
    hero.memes["fear"] += 1
    return ["__wobble__"]


def _r_heal(world: World) -> list[str]:
    patient = world.entities.get("patient")
    hero = world.entities.get("hero")
    if patient is None or patient.meters["served"] < THRESHOLD:
        return []
    sig = ("heal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patient.meters["comfort"] += 1
    patient.memes["relief"] += 1
    if hero is not None:
        hero.memes["pride"] += 1
        hero.memes["relief"] += 1
    return ["__heal__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="heal", tag="physical", apply=_r_heal),
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
        for item in produced:
            if not item.startswith("__"):
                world.say(item)
    return produced


TRAIT_BRAVERY = {
    "timid": 1,
    "careful": 2,
    "steady": 3,
    "bold": 4,
}

SETTINGS = {
    "willow_burrow": Setting(
        id="willow_burrow",
        home="a willow-root burrow",
        opening="At the edge of the meadow, little animals live in a willow-root burrow with round windows of moss.",
        healer_place="Old Owl's hollow stump",
        patient_place="a fern nest on the far bank",
        landmark="the silver brook",
        affords={"stepping_stones", "misty_log"},
    ),
    "pine_hollow": Setting(
        id="pine_hollow",
        home="a pine-cone den",
        opening="Under the tall pines, little animals live in a warm pine-cone den that smells of needles and rain.",
        healer_place="Old Owl's bark house",
        patient_place="a nook beneath the bramble arch",
        landmark="the bramble path",
        affords={"bramble_tunnel", "misty_log"},
    ),
    "reed_marsh": Setting(
        id="reed_marsh",
        home="a reed-woven nest",
        opening="Beside the pond, little animals live in a reed-woven nest where cattails sway all day long.",
        healer_place="Old Owl's dry basket by the reeds",
        patient_place="a soft nest near the lily pads",
        landmark="the narrow water edge",
        affords={"stepping_stones", "bramble_tunnel"},
    ),
}

OBSTACLES = {
    "stepping_stones": Obstacle(
        id="stepping_stones",
        label="the stepping stones",
        kind="balance",
        scare=3,
        risk_line="Between the healer and the patient, the stepping stones shone wet and slippery.",
        crossing_line="The stones were small, and the tea would have to stay steady all the way across.",
        tags={"crossing", "water"},
    ),
    "misty_log": Obstacle(
        id="misty_log",
        label="the misty log",
        kind="light",
        scare=4,
        risk_line="A fallen log crossed the ditch, but evening mist had wrapped it in gray blur.",
        crossing_line="One wrong paw-step in the blur could tip the cup.",
        tags={"crossing", "dark"},
    ),
    "bramble_tunnel": Obstacle(
        id="bramble_tunnel",
        label="the bramble tunnel",
        kind="shield",
        scare=3,
        risk_line="The quickest way was a bramble tunnel with scratchy twigs that liked to grab passing fur.",
        crossing_line="If the cup brushed the thorns, the warm tea would spill.",
        tags={"crossing", "thorns"},
    ),
}

TOOLS = {
    "vine_handle": Tool(
        id="vine_handle",
        label="a vine handle tied around the cup",
        kind="balance",
        bonus=1,
        carry_line="Old Owl looped a soft vine around the cup so it could hang steady from one paw.",
        qa_line="The vine handle kept the cup from wobbling too much on the stones.",
        tags={"tool", "balance"},
    ),
    "glow_bug_lantern": Tool(
        id="glow_bug_lantern",
        label="a glow-bug lantern",
        kind="light",
        bonus=1,
        carry_line="Old Owl tucked three glow-bugs into a tiny lantern so the path ahead would shine pale gold.",
        qa_line="The glow-bug lantern made the misty log bright enough to see.",
        tags={"tool", "light"},
    ),
    "bark_sleeve": Tool(
        id="bark_sleeve",
        label="a bark sleeve around the cup",
        kind="shield",
        bonus=1,
        carry_line="Old Owl slid the cup into a smooth bark sleeve so the thorns could not snag it easily.",
        qa_line="The bark sleeve protected the cup from the brambles.",
        tags={"tool", "shield"},
    ),
}

MENTORS = {
    "mother": Mentor(
        id="mother",
        type="mother",
        label="mother",
        support=1,
        comfort_line='"%s, brave does not mean never shaking," Mother said. "It means carrying kindness even while you shake."',
        tags={"family"},
    ),
    "aunt": Mentor(
        id="aunt",
        type="aunt",
        label="aunt",
        support=1,
        comfort_line='Aunt touched %s on the shoulder. "Take one small step, then another. I will be right here watching."',
        tags={"family"},
    ),
    "beaver": Mentor(
        id="beaver",
        type="beaver",
        label="Beaver",
        support=2,
        comfort_line='Beaver gave %s a steady nod. "You know how to place careful paws. Trust them."',
        tags={"friend"},
    ),
}

PATIENTS = {
    "nestling": Patient(
        id="nestling",
        type="bird",
        label="nestling",
        ailment="a tiny, scratchy chirp",
        weak_line="The little nestling could hardly peep at all; the sound came out thin and dry.",
        recovery_line="Soon the nestling's chirp turned round and bright again, like a bead of song.",
        tags={"bird", "sick"},
    ),
    "hedgehog": Patient(
        id="hedgehog",
        type="hedgehog",
        label="hedgehog",
        ailment="a dry little cough",
        weak_line="The hedgehog curled and uncurled with a dry little cough and a tired nose.",
        recovery_line="Soon the hedgehog uncurled all the way and gave a relieved, prickly sigh.",
        tags={"hedgehog", "sick"},
    ),
    "mole": Patient(
        id="mole",
        type="mole",
        label="mole",
        ailment="a dusty throat",
        weak_line="The young mole blinked in the doorway and kept swallowing, as if dust were stuck in the throat.",
        recovery_line="Soon the mole's voice came back soft and clear, and the nose stopped twitching with worry.",
        tags={"mole", "sick"},
    ),
}

HERO_KINDS = {
    "rabbit": HeroKind(
        id="rabbit",
        type="rabbit",
        label="rabbit",
        likes_line="liked to listen for the tiny sounds hidden in tall grass",
        tags={"rabbit"},
    ),
    "squirrel": HeroKind(
        id="squirrel",
        type="squirrel",
        label="squirrel",
        likes_line="liked to scamper fast, then stop and look very carefully before the next leap",
        tags={"squirrel"},
    ),
    "mouse": HeroKind(
        id="mouse",
        type="mouse",
        label="mouse",
        likes_line="liked to carry seeds and secrets in quick, neat paws",
        tags={"mouse"},
    ),
}

NAMES = {
    "rabbit": ["Pip", "Mallow", "Thimble", "Clover"],
    "squirrel": ["Nip", "Hazel", "Tumble", "Fern"],
    "mouse": ["Nib", "Mimi", "Poppy", "Dusty"],
}

PATIENT_NAMES = ["Peep", "Bramble", "Moss", "Dot"]


def tool_fits(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.kind == tool.kind


def courage_total(trait: str, mentor_id: str, tool_id: str) -> int:
    return TRAIT_BRAVERY[trait] + MENTORS[mentor_id].support + TOOLS[tool_id].bonus


def valid_story(setting_id: str, obstacle_id: str, tool_id: str, trait: str, mentor_id: str) -> bool:
    setting = SETTINGS[setting_id]
    obstacle = OBSTACLES[obstacle_id]
    tool = TOOLS[tool_id]
    if obstacle_id not in setting.affords:
        return False
    if not tool_fits(obstacle, tool):
        return False
    return courage_total(trait, mentor_id, tool_id) >= obstacle.scare


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in sorted(SETTINGS):
        for obstacle_id in sorted(SETTINGS[setting_id].affords):
            for tool_id in sorted(TOOLS):
                for trait in sorted(TRAIT_BRAVERY):
                    for mentor_id in sorted(MENTORS):
                        if valid_story(setting_id, obstacle_id, tool_id, trait, mentor_id):
                            combos.append((setting_id, obstacle_id, tool_id, trait, mentor_id))
    return combos


def crossing_style(params: StoryParams) -> str:
    total = courage_total(params.trait, params.mentor, params.tool)
    scare = OBSTACLES[params.obstacle].scare
    return "steady" if total >= scare + 2 else "shaky"


def explain_tool(obstacle: Obstacle, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not solve {obstacle.label}. "
        f"This obstacle needs a {obstacle.kind} kind of help.)"
    )


def explain_setting(setting: Setting, obstacle: Obstacle) -> str:
    return (
        f"(No story: {obstacle.label} is not part of {setting.id.replace('_', ' ')}. "
        f"Pick an obstacle the setting actually has.)"
    )


def explain_bravery(trait: str, mentor_id: str, tool_id: str, obstacle_id: str) -> str:
    total = courage_total(trait, mentor_id, tool_id)
    scare = OBSTACLES[obstacle_id].scare
    return (
        f"(No story: with trait={trait}, mentor={mentor_id}, and tool={tool_id}, "
        f"the helper's courage reaches {total}, but {obstacle_id} needs {scare}. "
        f"Choose a steadier helper, a stronger guide, or an easier obstacle.)"
    )


def predict_crossing(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["crossing"] += 1
    sim.facts["margin"] = courage_total(params.trait, params.mentor, params.tool) - OBSTACLES[params.obstacle].scare
    propagate(sim, narrate=False)
    return {
        "wobbles": hero.meters["wobble"] >= THRESHOLD,
        "margin": sim.facts["margin"],
    }


def introduce(world: World, hero: Entity, hero_kind: HeroKind) -> None:
    world.say(world.setting.opening)
    world.say(
        f"{hero.id} was a young {hero_kind.label} who {hero_kind.likes_line}."
    )


def illness(world: World, patient: Entity, patient_cfg: Patient) -> None:
    patient.meters["needs_drink"] += 1
    patient.meters["weak"] += 1
    world.say(
        f"That afternoon, {patient.id} in {world.setting.patient_place} had {patient_cfg.ailment}. "
        f"{patient_cfg.weak_line}"
    )


def healer_scene(world: World, hero: Entity, patient: Entity, mentor: Entity, patient_cfg: Patient) -> None:
    world.say(
        f"{hero.id} hurried with {mentor.label} to {world.setting.healer_place}, where Old Owl listened and nodded."
    )
    world.say(
        f'Old Owl brewed warm rouge berry tea and said, "Please carry this to {patient.id}. '
        f'Let {patient.pronoun("object")} imbibe it in small sips, and the throat should soften."'
    )


def obstacle_scene(world: World, obstacle: Obstacle) -> None:
    world.say(obstacle.risk_line)
    world.say(obstacle.crossing_line)


def encouragement(world: World, hero: Entity, mentor: Mentor) -> None:
    line = mentor.comfort_line % hero.id
    world.say(line)


def equip_tool(world: World, tool: Tool) -> None:
    world.say(tool.carry_line)


def decide(world: World, hero: Entity, params: StoryParams) -> None:
    pred = predict_crossing(world, params)
    hero.memes["fear"] += 1
    world.facts["predicted_wobble"] = pred["wobbles"]
    world.facts["margin"] = pred["margin"]
    if pred["wobbles"]:
        world.say(
            f"{hero.id}'s paws felt very small for a moment, and the warm cup smelled even more important."
        )
    else:
        world.say(
            f"{hero.id} took a long breath and felt the brave part inside grow a little larger."
        )


def cross(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.meters["crossing"] += 1
    propagate(world, narrate=False)
    if hero.meters["wobble"] >= THRESHOLD:
        world.say(
            f"{hero.id} stepped onto {obstacle.label} slowly. Once, the cup trembled, but {hero.pronoun()} hugged it close and kept going."
        )
    else:
        world.say(
            f"{hero.id} stepped onto {obstacle.label} with careful courage and carried the cup straight and true."
        )
    hero.meters["arrived"] += 1
    hero.memes["bravery"] += 1


def deliver(world: World, hero: Entity, patient: Entity, patient_cfg: Patient) -> None:
    patient.meters["served"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last {hero.id} reached {patient.id} and held out the steaming cup. {patient.id} took a sip, then another."
    )
    world.say(patient_cfg.recovery_line)
    world.say(
        f"{hero.id} smiled then, because bravery had carried something gentle all the way across."
    )


def ending(world: World, hero: Entity, patient: Entity, mentor: Entity, tool: Tool) -> None:
    if hero.meters["wobble"] >= THRESHOLD:
        world.say(
            f"Back at home, everyone said {hero.id} had been brave not because the path was easy, but because {hero.pronoun()} kept going kindly anyway."
        )
    else:
        world.say(
            f"Back at home, everyone said {hero.id} had been brave and steady, and even the evening air seemed softer."
        )
    world.say(
        f"{patient.id} rested warm and calm, and {tool.label} was hung by the door as a little reminder of the brave trip."
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    tool: Tool,
    mentor_cfg: Mentor,
    patient_cfg: Patient,
    hero_kind: HeroKind,
    hero_name: str,
    patient_name: str,
    trait: str,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_kind.type,
            label=hero_name,
            role="hero",
            attrs={"trait": trait},
            tags=set(hero_kind.tags),
        )
    )
    mentor = world.add(
        Entity(
            id="mentor",
            kind="character",
            type=mentor_cfg.type,
            label=mentor_cfg.label,
            role="mentor",
            tags=set(mentor_cfg.tags),
        )
    )
    patient = world.add(
        Entity(
            id=patient_name,
            kind="character",
            type=patient_cfg.type,
            label=patient_name,
            role="patient",
            tags=set(patient_cfg.tags),
        )
    )
    tea = world.add(
        Entity(
            id="tea",
            kind="thing",
            type="tea",
            label="rouge berry tea",
            phrase="warm rouge berry tea",
            role="medicine",
            tags={"tea", "drink"},
        )
    )

    hero.memes["courage_base"] = float(TRAIT_BRAVERY[trait])
    world.facts["margin"] = courage_total(trait, mentor_cfg.id, tool.id) - obstacle.scare

    introduce(world, hero, hero_kind)
    illness(world, patient, patient_cfg)

    world.para()
    healer_scene(world, hero, patient, mentor, patient_cfg)
    obstacle_scene(world, obstacle)
    encouragement(world, hero, mentor_cfg)
    equip_tool(world, tool)
    decide(world, hero, StoryParams(
        setting=setting.id,
        obstacle=obstacle.id,
        tool=tool.id,
        mentor=mentor_cfg.id,
        patient=patient_cfg.id,
        trait=trait,
        hero_kind=hero_kind.id,
        hero_name=hero_name,
        patient_name=patient_name,
        seed=None,
    ))

    world.para()
    cross(world, hero, obstacle)
    deliver(world, hero, patient, patient_cfg)

    world.para()
    ending(world, hero, patient, mentor, tool)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        patient=patient,
        tea=tea,
        setting=setting,
        obstacle=obstacle,
        tool=tool,
        mentor_cfg=mentor_cfg,
        patient_cfg=patient_cfg,
        hero_kind=hero_kind,
        trait=trait,
        outcome="shaky" if hero.meters["wobble"] >= THRESHOLD else "steady",
        imbibed=patient.meters["served"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    patient = world.facts["patient"]
    obstacle = world.facts["obstacle"]
    return [
        'Write an Animal Story for a 3-to-5-year-old that includes the words "live", "rouge", and "imbibe".',
        f"Tell a gentle forest story where {hero.id} must carry warm rouge berry tea across {obstacle.label} to help {patient.id}.",
        "Write a bravery story where being brave means carrying kindness even while feeling afraid.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    patient = world.facts["patient"]
    mentor = world.facts["mentor"]
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    patient_cfg = world.facts["patient_cfg"]
    outcome = world.facts["outcome"]

    qa = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {world.facts['hero_kind'].label}, and {patient.id}, who needed help. {mentor.label.capitalize()} and Old Owl also helped {hero.id} get ready.",
        ),
        (
            f"Why did {hero.id} have to carry the tea?",
            f"{patient.id} had {patient_cfg.ailment} and was too weak to come to the healer. Old Owl made warm rouge berry tea so {patient.id} could imbibe it and feel better.",
        ),
        (
            f"What problem stood between {hero.id} and {patient.id}?",
            f"The path crossed {obstacle.label}, which looked hard and a little scary. The cup had to stay safe the whole way, or the healing tea would be lost.",
        ),
        (
            f"How did {tool.label} help?",
            f"{tool.qa_line} That made the brave trip more possible, because the tool matched the danger on the path.",
        ),
    ]
    if outcome == "shaky":
        qa.append(
            (
                f"Was {hero.id} afraid?",
                f"Yes. {hero.id} felt frightened and wobbled once on the way, but kept going carefully. The story shows bravery as doing the kind thing even while shaking.",
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} show bravery?",
                f"{hero.id} took a deep breath, trusted the help that was given, and crossed the path steadily. The bravery mattered because it brought comfort to {patient.id}.",
            )
        )
    qa.append(
        (
            f"What changed at the end?",
            f"{patient.id} drank the tea and felt better, and {hero.id} felt proud and relieved. The ending proves that the brave trip turned worry into comfort.",
        )
    )
    return qa


KNOWLEDGE = {
    "imbibe": [
        (
            "What does imbibe mean?",
            "Imbibe is a fancy word that means drink. In this story, it means taking the warm tea in little sips.",
        )
    ],
    "rouge": [
        (
            "What does rouge mean?",
            "Rouge is a word for a rosy red color. The tea in the story is made from red berries, so it is called rouge berry tea.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery does not always mean feeling fearless. Sometimes it means doing a kind, helpful thing even when you feel a little scared.",
        )
    ],
    "owl": [
        (
            "Why is an owl a good healer in a forest story?",
            "Owls are often shown as wise and careful in animal stories. That makes them a good fit for giving calm advice and helpful medicine.",
        )
    ],
    "tea": [
        (
            "Why do warm drinks sometimes help a sore throat?",
            "A warm drink can feel gentle on a scratchy throat. It can make swallowing easier and help someone feel comforted.",
        )
    ],
    "crossing": [
        (
            "Why is carrying a cup across a tricky path hard?",
            "A cup can tip or spill if your steps are shaky. That means you have to move slowly and keep good balance.",
        )
    ],
}

KNOWLEDGE_ORDER = ["imbibe", "rouge", "bravery", "tea", "crossing", "owl"]


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags = {"imbibe", "rouge", "bravery", "tea", "crossing", "owl"}
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="willow_burrow",
        obstacle="stepping_stones",
        tool="vine_handle",
        mentor="beaver",
        patient="nestling",
        trait="careful",
        hero_kind="rabbit",
        hero_name="Pip",
        patient_name="Peep",
        seed=None,
    ),
    StoryParams(
        setting="pine_hollow",
        obstacle="misty_log",
        tool="glow_bug_lantern",
        mentor="mother",
        patient="mole",
        trait="bold",
        hero_kind="mouse",
        hero_name="Mimi",
        patient_name="Moss",
        seed=None,
    ),
    StoryParams(
        setting="reed_marsh",
        obstacle="bramble_tunnel",
        tool="bark_sleeve",
        mentor="aunt",
        patient="hedgehog",
        trait="steady",
        hero_kind="squirrel",
        hero_name="Hazel",
        patient_name="Bramble",
        seed=None,
    ),
    StoryParams(
        setting="pine_hollow",
        obstacle="misty_log",
        tool="glow_bug_lantern",
        mentor="beaver",
        patient="nestling",
        trait="timid",
        hero_kind="rabbit",
        hero_name="Mallow",
        patient_name="Dot",
        seed=None,
    ),
]


ASP_RULES = r"""
% Setting compatibility.
available(S, O) :- setting(S), affords(S, O).

% Tool compatibility.
fits(O, T) :- obstacle(O), tool(T), obstacle_kind(O, K), tool_kind(T, K).

% Courage budget.
total_courage(Tr, M, T, B + S + G) :-
    trait(Tr), mentor(M), tool(T),
    bravery(Tr, B), support(M, S), bonus(T, G).

possible(S, O, T, Tr, M) :-
    available(S, O),
    fits(O, T),
    total_courage(Tr, M, T, C),
    scare(O, Need),
    C >= Need.

outcome(S, O, T, Tr, M, steady) :-
    possible(S, O, T, Tr, M),
    total_courage(Tr, M, T, C),
    scare(O, Need),
    C >= Need + 2.

outcome(S, O, T, Tr, M, shaky) :-
    possible(S, O, T, Tr, M),
    total_courage(Tr, M, T, C),
    scare(O, Need),
    C >= Need,
    C < Need + 2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for oid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, oid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_kind", oid, obstacle.kind))
        lines.append(asp.fact("scare", oid, obstacle.scare))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_kind", tid, tool.kind))
        lines.append(asp.fact("bonus", tid, tool.bonus))
    for trait, bravery in TRAIT_BRAVERY.items():
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("bravery", trait, bravery))
    for mid, mentor in MENTORS.items():
        lines.append(asp.fact("mentor", mid))
        lines.append(asp.fact("support", mid, mentor.support))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show possible/5."))
    return sorted(set(asp.atoms(model, "possible")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_mentor", params.mentor),
            "pick_outcome(X) :- outcome(chosen_setting, chosen_obstacle, chosen_tool, chosen_trait, chosen_mentor, X).",
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show pick_outcome/1."))
    atoms = asp.atoms(model, "pick_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in asp:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != crossing_style(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcomes match Python outcomes on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a small helper carries rouge berry tea across a tricky path with bravery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mentor", choices=MENTORS)
    ap.add_argument("--patient", choices=PATIENTS)
    ap.add_argument("--trait", choices=sorted(TRAIT_BRAVERY))
    ap.add_argument("--hero-kind", choices=HERO_KINDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--patient-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle and args.obstacle not in SETTINGS[args.setting].affords:
        raise StoryError(explain_setting(SETTINGS[args.setting], OBSTACLES[args.obstacle]))
    if args.obstacle and args.tool and not tool_fits(OBSTACLES[args.obstacle], TOOLS[args.tool]):
        raise StoryError(explain_tool(OBSTACLES[args.obstacle], TOOLS[args.tool]))
    if args.setting and args.obstacle and args.tool and args.trait and args.mentor:
        if not valid_story(args.setting, args.obstacle, args.tool, args.trait, args.mentor):
            raise StoryError(explain_bravery(args.trait, args.mentor, args.tool, args.obstacle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
        and (args.trait is None or combo[3] == args.trait)
        and (args.mentor is None or combo[4] == args.mentor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, tool_id, trait, mentor_id = rng.choice(sorted(combos))
    hero_kind = args.hero_kind or rng.choice(sorted(HERO_KINDS))
    hero_name = args.hero_name or rng.choice(NAMES[hero_kind])
    patient_id = args.patient or rng.choice(sorted(PATIENTS))
    patient_name = args.patient_name or rng.choice([n for n in PATIENT_NAMES if n != hero_name])

    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        tool=tool_id,
        mentor=mentor_id,
        patient=patient_id,
        trait=trait,
        hero_kind=hero_kind,
        hero_name=hero_name,
        patient_name=patient_name,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.mentor not in MENTORS:
        raise StoryError(f"(Unknown mentor: {params.mentor})")
    if params.patient not in PATIENTS:
        raise StoryError(f"(Unknown patient: {params.patient})")
    if params.trait not in TRAIT_BRAVERY:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.hero_kind not in HERO_KINDS:
        raise StoryError(f"(Unknown hero kind: {params.hero_kind})")
    if not valid_story(params.setting, params.obstacle, params.tool, params.trait, params.mentor):
        raise StoryError(explain_bravery(params.trait, params.mentor, params.tool, params.obstacle))

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle=OBSTACLES[params.obstacle],
        tool=TOOLS[params.tool],
        mentor_cfg=MENTORS[params.mentor],
        patient_cfg=PATIENTS[params.patient],
        hero_kind=HERO_KINDS[params.hero_kind],
        hero_name=params.hero_name,
        patient_name=params.patient_name,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show possible/5.\n#show outcome/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, tool, trait, mentor) combos:\n")
        for setting_id, obstacle_id, tool_id, trait, mentor_id in combos:
            print(f"  {setting_id:14} {obstacle_id:15} {tool_id:17} {trait:7} {mentor_id}")
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
            header = (
                f"### {p.hero_name}: {p.obstacle} with {p.tool} "
                f"({p.setting}, {crossing_style(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
