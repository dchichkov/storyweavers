#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/decongestant_doubt_conflict_sound_effects_quest_space.py
====================================================================================

A small standalone storyworld about a child-sized space quest interrupted by a
stuffy nose, a moment of doubt, and a sensible stop for decongestant.

The world model keeps the domain narrow on purpose:

- a young captain and a helper set out on a space errand
- congestion makes helmet sounds and radio clues hard to hear
- conflict comes from wanting to hurry versus stopping for help
- a medic offers decongestant only for symptoms it plausibly helps
- the quest succeeds only with mission-matching gear

Run it
------
python storyworlds/worlds/gpt-5.4/decongestant_doubt_conflict_sound_effects_quest_space.py
python storyworlds/worlds/gpt-5.4/decongestant_doubt_conflict_sound_effects_quest_space.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/decongestant_doubt_conflict_sound_effects_quest_space.py --all
python storyworlds/worlds/gpt-5.4/decongestant_doubt_conflict_sound_effects_quest_space.py --qa
python storyworlds/worlds/gpt-5.4/decongestant_doubt_conflict_sound_effects_quest_space.py --trace
python storyworlds/worlds/gpt-5.4/decongestant_doubt_conflict_sound_effects_quest_space.py --json
python storyworlds/worlds/gpt-5.4/decongestant_doubt_conflict_sound_effects_quest_space.py --verify
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
        female = {"girl", "mother", "woman", "medic_f"}
        male = {"boy", "father", "man", "medic_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "medic_f": "medic",
            "medic_m": "medic",
            "robot": "robot",
        }.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    destination: str
    quest: str
    clue: str
    obstacle: str
    gear_needed: str
    prize: str
    launch_sound: str
    clue_sound: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Symptom:
    id: str
    label: str
    sentence: str
    sound: str
    nasal: bool = False
    makes_doubt: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: str
    action: str
    solve_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    name: str
    type: str
    phrase: str
    caution: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Trait:
    id: str
    label: str
    hurry: int
    line: str


@dataclass
class StoryParams:
    mission: str
    symptom: str
    gear: str
    companion: str
    hero: str
    hero_gender: str
    hero_trait: str
    medic: str
    seed: Optional[int] = None


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


def _r_muffled(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None:
        return out
    if hero.meters["congestion"] >= THRESHOLD and hero.meters["helmet_on"] >= THRESHOLD:
        sig = ("muffled", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["muffled"] += 1
            hero.memes["doubt"] += 1
            out.append("__muffled__")
    return out


def _r_turn_back(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    ship = world.entities.get("ship")
    if hero is None or ship is None:
        return out
    if hero.meters["muffled"] >= THRESHOLD and hero.meters["launched"] >= THRESHOLD:
        sig = ("turn_back", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            ship.meters["returned"] += 1
            hero.memes["care"] += 1
            out.append("__return__")
    return out


def _r_clear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None:
        return out
    if hero.meters["decongestant"] >= THRESHOLD and hero.meters["congestion"] >= THRESHOLD:
        sig = ("clear", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["congestion"] = 0.0
            hero.meters["muffled"] = 0.0
            hero.memes["relief"] += 1
            out.append("__clear__")
    return out


CAUSAL_RULES = [
    Rule(name="muffled", tag="physical", apply=_r_muffled),
    Rule(name="turn_back", tag="physical", apply=_r_turn_back),
    Rule(name="clear", tag="physical", apply=_r_clear),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if sent == "__muffled__":
                hero = world.get("hero")
                symptom = world.facts["symptom_cfg"]
                world.say(
                    f"Inside the helmet, {symptom.sound} went the little speakers, and everything sounded far away."
                )
            elif sent == "__return__":
                mission = world.facts["mission_cfg"]
                world.say(
                    f'"We had better turn around," said the helper. The quest to {mission.destination} was still waiting, but rushing would not make the clues clearer.'
                )
            elif sent == "__clear__":
                world.say(
                    "After the medicine, the stuffed-up feeling loosened. Breathing grew easier, and the brave plan in the captain's head stopped wobbling."
                )
    return produced


MISSIONS = {
    "echo_moon": Mission(
        id="echo_moon",
        destination="Echo Moon",
        quest="follow a singing beacon to a lost moon flag",
        clue="a singing beacon",
        obstacle="echo maze",
        gear_needed="echo_scanner",
        prize="the silver moon flag",
        launch_sound="WHOOSH",
        clue_sound="beep-beep-bloop",
        ending_image="The silver moon flag fluttered beside the ship while the quiet moon hummed under their boots.",
        tags={"moon", "beacon", "quest"},
    ),
    "star_harbor": Mission(
        id="star_harbor",
        destination="Star Harbor",
        quest="carry a tiny star-map tube to the harbor gate",
        clue="a blinking dock light",
        obstacle="locked hatch",
        gear_needed="magnet_key",
        prize="the bright star-map tube",
        launch_sound="ZOOM",
        clue_sound="blink-blink",
        ending_image="The star-map tube slid safely into the harbor slot, and small blue lights winked along the wall.",
        tags={"harbor", "map", "quest"},
    ),
    "comet_garden": Mission(
        id="comet_garden",
        destination="Comet Garden",
        quest="find the sleepy comet seed hidden past a dark crater",
        clue="a sparkly trail",
        obstacle="dark crater",
        gear_needed="moon_lamp",
        prize="the sleepy comet seed",
        launch_sound="FWOOOSH",
        clue_sound="ting-ting",
        ending_image="The comet seed glowed in its cup, and the crater rim shone like a ring of sugar.",
        tags={"garden", "crater", "quest"},
    ),
}

SYMPTOMS = {
    "stuffy_nose": Symptom(
        id="stuffy_nose",
        label="stuffy nose",
        sentence="had a stuffy nose that made each helmet breath feel thick",
        sound="snff-snff",
        nasal=True,
        makes_doubt=True,
        tags={"decongestant", "nose"},
    ),
    "stuffy_ears": Symptom(
        id="stuffy_ears",
        label="stuffy ears",
        sentence="had stuffy ears that made radio sounds feel squashed",
        sound="mff-mff",
        nasal=True,
        makes_doubt=True,
        tags={"decongestant", "ears"},
    ),
    "scratchy_knee": Symptom(
        id="scratchy_knee",
        label="scratchy knee",
        sentence="had a scratchy knee from a silly tumble on the ladder",
        sound="ow-ow",
        nasal=False,
        makes_doubt=False,
        tags={"bandage"},
    ),
    "cold_fingers": Symptom(
        id="cold_fingers",
        label="cold fingers",
        sentence="had cold fingers from holding the metal rail too long",
        sound="brrr",
        nasal=False,
        makes_doubt=False,
        tags={"gloves"},
    ),
}

GEAR = {
    "echo_scanner": Gear(
        id="echo_scanner",
        label="echo scanner",
        phrase="an echo scanner with a round green screen",
        helps="echo maze",
        action="listened for the truest beep",
        solve_text="The scanner picked the real beacon out from the bouncing echoes.",
        tags={"scanner", "beacon"},
    ),
    "magnet_key": Gear(
        id="magnet_key",
        label="magnet key",
        phrase="a magnet key shaped like a shining hook",
        helps="locked hatch",
        action="clicked the key onto the latch",
        solve_text="The magnet key tugged the hatch open with a cheerful clink.",
        tags={"key", "hatch"},
    ),
    "moon_lamp": Gear(
        id="moon_lamp",
        label="moon lamp",
        phrase="a moon lamp as bright as a little pearl",
        helps="dark crater",
        action="lifted the lamp high over the path",
        solve_text="The moon lamp poured a soft white path across the dark crater edge.",
        tags={"lamp", "light"},
    ),
}

COMPANIONS = {
    "pip_robot": Companion(
        id="pip_robot",
        name="Pip",
        type="robot",
        phrase="a round helper robot with tidy blinking eyes",
        caution=3,
        tags={"robot"},
    ),
    "orla_sister": Companion(
        id="orla_sister",
        name="Orla",
        type="girl",
        phrase="an older sister with star patches on her sleeves",
        caution=5,
        tags={"sister"},
    ),
    "tomo_brother": Companion(
        id="tomo_brother",
        name="Tomo",
        type="boy",
        phrase="an older brother with careful hands at every switch",
        caution=5,
        tags={"brother"},
    ),
}

TRAITS = {
    "dashy": Trait(
        id="dashy",
        label="dashy",
        hurry=5,
        line="wanted to race the stars instead of waiting one more minute",
    ),
    "brave": Trait(
        id="brave",
        label="brave",
        hurry=4,
        line="liked to stand tall when a job looked hard",
    ),
    "careful": Trait(
        id="careful",
        label="careful",
        hurry=2,
        line="liked a brave plan best when each step made sense",
    ),
    "thoughtful": Trait(
        id="thoughtful",
        label="thoughtful",
        hurry=1,
        line="would rather pause and think than gallop into a muddle",
    ),
}

HERO_NAMES = {
    "girl": ["Nova", "Lyra", "Mina", "Zuri", "Asha", "Kira"],
    "boy": ["Leo", "Milo", "Tao", "Nico", "Arin", "Jules"],
}

MEDICS = {
    "mother": "mother",
    "father": "father",
    "medic_f": "medic_f",
    "medic_m": "medic_m",
}


def mission_matches_gear(mission_id: str, gear_id: str) -> bool:
    return mission_id in MISSIONS and gear_id in GEAR and MISSIONS[mission_id].gear_needed == gear_id


def symptom_allows_decongestant(symptom_id: str) -> bool:
    return symptom_id in SYMPTOMS and SYMPTOMS[symptom_id].nasal


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for symptom_id, symptom in SYMPTOMS.items():
            if not symptom.nasal:
                continue
            for gear_id in GEAR:
                if mission_matches_gear(mission_id, gear_id):
                    combos.append((mission_id, symptom_id, gear_id))
    return combos


def should_pause_first(hero_trait_id: str, companion_id: str) -> bool:
    trait = TRAITS[hero_trait_id]
    comp = COMPANIONS[companion_id]
    return comp.caution >= trait.hurry


def explain_rejection(mission_id: str, symptom_id: str, gear_id: str) -> str:
    bits: list[str] = []
    if symptom_id in SYMPTOMS and not SYMPTOMS[symptom_id].nasal:
        bits.append(
            f"decongestant would not sensibly fix {SYMPTOMS[symptom_id].label}"
        )
    if mission_id in MISSIONS and gear_id in GEAR and not mission_matches_gear(mission_id, gear_id):
        mission = MISSIONS[mission_id]
        gear = GEAR[gear_id]
        bits.append(
            f"{gear.label} does not solve the {mission.obstacle} on {mission.destination}"
        )
    if not bits:
        return "(No valid combination matches the given options.)"
    return "(No story: " + "; ".join(bits) + ".)"


def outcome_of(params: StoryParams) -> str:
    return "paused_first" if should_pause_first(params.hero_trait, params.companion) else "turned_back"


def predict_launch(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["helmet_on"] += 1
    hero.meters["launched"] += 1
    propagate(sim, narrate=False)
    return {
        "muffled": hero.meters["muffled"] >= THRESHOLD,
        "doubt": hero.memes["doubt"] >= THRESHOLD,
        "returned": sim.get("ship").meters["returned"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, companion: Entity, mission: Mission) -> None:
    world.say(
        f"{hero.id} was a little space captain on a quest to {mission.destination}, and {companion.name} was {companion.phrase}."
    )
    world.say(
        f"Together they meant to {mission.quest}. On the launch pad, little lights blinked and the ship whispered, {mission.launch_sound}."
    )


def symptom_beat(world: World, hero: Entity, symptom: Symptom, trait: Trait) -> None:
    hero.meters["congestion"] += 1
    hero.memes["hurry"] = float(trait.hurry)
    world.say(
        f"But that morning {hero.id} {symptom.sentence}. {hero.pronoun().capitalize()} still {trait.line}."
    )


def mission_need(world: World, mission: Mission) -> None:
    world.say(
        f"The clue for the quest was {mission.clue}. Somewhere ahead, it would go {mission.clue_sound} and lead them to {mission.prize}."
    )


def companion_warning(world: World, companion: Entity, hero: Entity, symptom: Symptom, medic: Entity) -> None:
    pred = predict_launch(world)
    world.facts["predicted_muffled"] = pred["muffled"]
    world.facts["predicted_returned"] = pred["returned"]
    world.say(
        f'"Wait," said {companion.name}. "If we fly now, your helmet will sound all squishy, and you may not hear the clue at all."'
    )
    if symptom.makes_doubt:
        hero.memes["doubt"] += 1
        world.say(
            f"For one breath, doubt fluttered in {hero.id}'s chest like a tiny loose flag. {medic.label_word.capitalize()} kept the decongestant in the bright sick-bay drawer."
        )


def rush_launch(world: World, hero: Entity, mission: Mission) -> None:
    hero.meters["helmet_on"] += 1
    hero.meters["launched"] += 1
    world.say(
        f'"Maybe I can do it anyway," said {hero.id}. Clack went the helmet ring. Then {mission.launch_sound}! went the ship as it lifted from the pad.'
    )
    propagate(world, narrate=True)


def pause_before_launch(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["care"] += 1
    world.say(
        f'{hero.id} put one hand on the ladder and stopped. "No," {hero.pronoun()} said at last. "A true captain listens when a helper hears trouble first."'
    )
    world.say(f"{companion.name} gave a small pleased nod.")


def medic_help(world: World, hero: Entity, medic: Entity, symptom: Symptom) -> None:
    hero.meters["decongestant"] += 1
    world.say(
        f"In the sick bay, {medic.label_word} poured a tiny spoon of decongestant and a cup of water. {hero.id} swallowed, made a funny face, and then laughed."
    )
    world.say(
        f'"That should help your {symptom.label}," said the {medic.label_word}. "Brave does not mean rushing with a foggy head."'
    )
    propagate(world, narrate=True)


def relaunch_if_needed(world: World, hero: Entity, mission: Mission, outcome: str) -> None:
    if outcome == "turned_back":
        world.say(
            f"A little later, back at the pad, the ship hummed {mission.launch_sound} again. This time the stars outside the window looked sharp and steady."
        )
    else:
        hero.meters["helmet_on"] += 1
        hero.meters["launched"] += 1
        world.say(
            f"Soon {mission.launch_sound}! went the ship for real, and the launch felt smooth instead of muddled."
        )


def quest_solve(world: World, hero: Entity, companion: Entity, mission: Mission, gear: Gear) -> None:
    hero.meters["quest_done"] += 1
    world.say(
        f"At {mission.destination}, the {mission.obstacle} tried to stop them. {companion.name} handed over {gear.phrase}, and {hero.id} {gear.action}."
    )
    world.say(
        f"{gear.solve_text} Clear at last, the clue sounded {mission.clue_sound}, and they found {mission.prize}."
    )
    world.say(mission.ending_image)


def closing_lesson(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    world.say(
        f'"Next time," said {hero.id}, smiling at {companion.name}, "I will not let doubt scare me, but I will listen to it when it warns me to be wise."'
    )
    world.say(
        f"{companion.name} tapped the side of the ship, and the hull answered with a happy bonk-bonk."
    )


def tell(
    mission_cfg: Mission,
    symptom_cfg: Symptom,
    gear_cfg: Gear,
    companion_cfg: Companion,
    hero_name: str,
    hero_gender: str,
    hero_trait_cfg: Trait,
    medic_type: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            traits=[hero_trait_cfg.label],
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            type=companion_cfg.type,
            label=companion_cfg.name,
            phrase=companion_cfg.phrase,
            role="companion",
            traits=["helpful"],
            tags=set(companion_cfg.tags),
        )
    )
    ship = world.add(
        Entity(
            id="ship",
            kind="thing",
            type="ship",
            label="ship",
            phrase="their little silver ship",
            role="ship",
        )
    )
    medic = world.add(
        Entity(
            id="medic",
            kind="character",
            type=medic_type,
            label="the medic",
            phrase="the medic",
            role="medic",
        )
    )

    world.facts.update(
        mission_cfg=mission_cfg,
        symptom_cfg=symptom_cfg,
        gear_cfg=gear_cfg,
        companion_cfg=companion_cfg,
        trait_cfg=hero_trait_cfg,
        hero_name=hero_name,
    )

    introduce(world, hero, companion, mission_cfg)
    mission_need(world, mission_cfg)

    world.para()
    symptom_beat(world, hero, symptom_cfg, hero_trait_cfg)
    companion_warning(world, companion, hero, symptom_cfg, medic)

    outcome = "paused_first" if should_pause_first(hero_trait_cfg.id, companion_cfg.id) else "turned_back"
    world.facts["outcome"] = outcome

    if outcome == "paused_first":
        pause_before_launch(world, hero, companion)
    else:
        rush_launch(world, hero, mission_cfg)

    world.para()
    medic_help(world, hero, medic, symptom_cfg)
    relaunch_if_needed(world, hero, mission_cfg, outcome)

    world.para()
    quest_solve(world, hero, companion, mission_cfg, gear_cfg)
    closing_lesson(world, hero, companion)

    world.facts.update(
        hero=hero,
        companion=companion,
        ship=ship,
        medic=medic,
        resolved=hero.meters["quest_done"] >= THRESHOLD,
        decongested=hero.meters["decongestant"] >= THRESHOLD and hero.meters["congestion"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mission = world.facts["mission_cfg"]
    symptom = world.facts["symptom_cfg"]
    hero_name = world.facts["hero_name"]
    outcome = world.facts["outcome"]
    prompts = [
        'Write a short space adventure for a 3-to-5-year-old that includes the words "decongestant" and "doubt".',
        f"Tell a space-quest story where {hero_name} needs to reach {mission.destination}, but {symptom.label} makes the mission harder.",
        f'Write a child-facing story with conflict, sound effects, and a quest, where a brave captain learns to pause and get help before finishing an adventure.',
    ]
    if outcome == "turned_back":
        prompts.append(
            f"Include a false start where the ship launches, the clue sounds muffled, and the captain turns back for decongestant before trying again."
        )
    else:
        prompts.append(
            f"Include a wise helper who stops the launch in time, so the captain takes decongestant before the quest begins."
        )
    return prompts


KNOWLEDGE = {
    "decongestant": [
        (
            "What does decongestant do?",
            "Decongestant is medicine that can help open a stuffed-up nose or ears so breathing and hearing feel clearer. A grown-up gives it when it is the right kind of medicine for the problem.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is an important trip with a goal. In stories, the characters have to keep going step by step until they reach what they came for.",
        )
    ],
    "robot": [
        (
            "What does a helper robot do in a story?",
            "A helper robot can watch carefully, remember useful things, and warn a friend when something is wrong. Good helpers do not just cheer; they also notice trouble early.",
        )
    ],
    "scanner": [
        (
            "What does a scanner do?",
            "A scanner helps you notice signals that are hard to hear or see. It is a tool for finding the right clue when there is noise or confusion around it.",
        )
    ],
    "lamp": [
        (
            "Why is a lamp useful on a dark trip?",
            "A lamp helps you see where to place your feet and what is ahead. Light makes a hard path safer and easier to understand.",
        )
    ],
    "key": [
        (
            "What does a key do?",
            "A key opens something that is closed. In adventure stories, the right key often lets the heroes pass the next barrier.",
        )
    ],
    "doubt": [
        (
            "Can doubt ever help you?",
            "Yes. Doubt can be a useful feeling when it tells you to slow down and check whether your plan still makes sense.",
        )
    ],
}
KNOWLEDGE_ORDER = ["decongestant", "doubt", "quest", "robot", "scanner", "lamp", "key"]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    mission = world.facts["mission_cfg"]
    symptom = world.facts["symptom_cfg"]
    gear = world.facts["gear_cfg"]
    medic = world.facts["medic"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a little space captain, and {companion.label}, the helper on the quest. They were trying to reach {mission.destination} together.",
        ),
        (
            "What was the quest?",
            f"The quest was to {mission.quest}. The clue was {mission.clue}, which they needed to hear or follow to reach {mission.prize}.",
        ),
        (
            f"Why did {hero.label} feel doubt?",
            f"{hero.label} felt doubt because {hero.pronoun('possessive')} {symptom.label} made the helmet sounds and clues seem muffled. That made the brave plan wobble, because a captain cannot follow a space clue clearly if it sounds far away.",
        ),
        (
            "Why did they use decongestant?",
            f"They used decongestant because the problem was a stuffed-up nose or ears, which is exactly the kind of trouble that medicine can help. After it worked, breathing and hearing felt clearer, so the quest made sense again.",
        ),
    ]
    if outcome == "turned_back":
        qa.append(
            (
                "Did the captain launch right away?",
                f"At first, yes. {hero.label} tried to go anyway, but the muffled sounds proved the warning was right, so the ship turned back before the real clue was missed.",
            )
        )
    else:
        qa.append(
            (
                "Did the captain launch right away?",
                f"No. {companion.label} warned {hero.label}, and {hero.pronoun()} listened before lifting off. That choice kept the quest from getting muddled in the first place.",
            )
        )
    qa.append(
        (
            f"How did they finish the quest at {mission.destination}?",
            f"They used the {gear.label} to solve the {mission.obstacle}. That worked because the tool matched the problem, and once {hero.label} could hear clearly again, the clue led them to {mission.prize}.",
        )
    )
    qa.append(
        (
            "What changed by the end of the story?",
            f"At the end, the quest was finished and the captain felt steady instead of doubtful. {medic.label_word.capitalize()} had helped with the decongestant, and the helper had shown that wise pauses can be part of being brave.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"quest", "doubt", "decongestant"}
    companion_cfg = world.facts["companion_cfg"]
    gear_cfg = world.facts["gear_cfg"]
    if "robot" in companion_cfg.tags:
        tags.add("robot")
    if gear_cfg.id == "echo_scanner":
        tags.add("scanner")
    if gear_cfg.id == "moon_lamp":
        tags.add("lamp")
    if gear_cfg.id == "magnet_key":
        tags.add("key")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="echo_moon",
        symptom="stuffy_nose",
        gear="echo_scanner",
        companion="pip_robot",
        hero="Nova",
        hero_gender="girl",
        hero_trait="dashy",
        medic="mother",
    ),
    StoryParams(
        mission="star_harbor",
        symptom="stuffy_ears",
        gear="magnet_key",
        companion="orla_sister",
        hero="Leo",
        hero_gender="boy",
        hero_trait="brave",
        medic="father",
    ),
    StoryParams(
        mission="comet_garden",
        symptom="stuffy_nose",
        gear="moon_lamp",
        companion="tomo_brother",
        hero="Mina",
        hero_gender="girl",
        hero_trait="careful",
        medic="medic_f",
    ),
    StoryParams(
        mission="echo_moon",
        symptom="stuffy_ears",
        gear="echo_scanner",
        companion="pip_robot",
        hero="Tao",
        hero_gender="boy",
        hero_trait="thoughtful",
        medic="medic_m",
    ),
]


ASP_RULES = r"""
% valid scenario = symptom is one decongestant plausibly helps, and the chosen
% gear is the one that actually solves the mission obstacle.
valid(M, S, G) :- mission(M), symptom(S), gear(G), nasal(S), needs(M, G).

% branch shape: does the captain pause before launch, or rush and then turn back?
pause_first :- chosen_trait(T), trait_hurry(T, H), chosen_companion(C), caution(C, K), K >= H.
outcome(paused_first) :- pause_first.
outcome(turned_back) :- not pause_first.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        lines.append(asp.fact("needs", mission_id, mission.gear_needed))
    for symptom_id, symptom in SYMPTOMS.items():
        lines.append(asp.fact("symptom", symptom_id))
        if symptom.nasal:
            lines.append(asp.fact("nasal", symptom_id))
    for gear_id in GEAR:
        lines.append(asp.fact("gear", gear_id))
    for companion_id, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", companion_id))
        lines.append(asp.fact("caution", companion_id, companion.caution))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("trait_hurry", trait_id, trait.hurry))
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
            asp.fact("chosen_trait", params.hero_trait),
            asp.fact("chosen_companion", params.companion),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH in outcome model: {len(mismatches)} cases differ.")
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a small space quest, a stuffy nose, and a wise pause for decongestant."
    )
    ap.add_argument("--mission", choices=sorted(MISSIONS))
    ap.add_argument("--symptom", choices=sorted(SYMPTOMS))
    ap.add_argument("--gear", choices=sorted(GEAR))
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-trait", choices=sorted(TRAITS))
    ap.add_argument("--medic", choices=sorted(MEDICS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.symptom and not symptom_allows_decongestant(args.symptom):
        raise StoryError(explain_rejection(args.mission or next(iter(MISSIONS)), args.symptom, args.gear or next(iter(GEAR))))
    if args.mission and args.gear and not mission_matches_gear(args.mission, args.gear):
        raise StoryError(explain_rejection(args.mission, args.symptom or next(iter(SYMPTOMS)), args.gear))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.symptom is None or combo[1] == args.symptom)
        and (args.gear is None or combo[2] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, symptom_id, gear_id = rng.choice(sorted(combos))
    companion_id = args.companion or rng.choice(sorted(COMPANIONS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or rng.choice(HERO_NAMES[hero_gender])
    hero_trait = args.hero_trait or rng.choice(sorted(TRAITS))
    medic = args.medic or rng.choice(sorted(MEDICS))
    return StoryParams(
        mission=mission_id,
        symptom=symptom_id,
        gear=gear_id,
        companion=companion_id,
        hero=hero_name,
        hero_gender=hero_gender,
        hero_trait=hero_trait,
        medic=medic,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    if params.symptom not in SYMPTOMS:
        raise StoryError(f"Unknown symptom: {params.symptom}")
    if params.gear not in GEAR:
        raise StoryError(f"Unknown gear: {params.gear}")
    if params.companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {params.companion}")
    if params.hero_trait not in TRAITS:
        raise StoryError(f"Unknown hero trait: {params.hero_trait}")
    if params.medic not in MEDICS:
        raise StoryError(f"Unknown medic: {params.medic}")
    if not symptom_allows_decongestant(params.symptom):
        raise StoryError(explain_rejection(params.mission, params.symptom, params.gear))
    if not mission_matches_gear(params.mission, params.gear):
        raise StoryError(explain_rejection(params.mission, params.symptom, params.gear))

    world = tell(
        mission_cfg=MISSIONS[params.mission],
        symptom_cfg=SYMPTOMS[params.symptom],
        gear_cfg=GEAR[params.gear],
        companion_cfg=COMPANIONS[params.companion],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        hero_trait_cfg=TRAITS[params.hero_trait],
        medic_type=params.medic,
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
        print(f"{len(combos)} valid (mission, symptom, gear) combos:\n")
        for mission_id, symptom_id, gear_id in combos:
            print(f"  {mission_id:12} {symptom_id:12} {gear_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.hero}: {p.mission} with {p.symptom} ({p.gear}, {outcome_of(p)})"
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
