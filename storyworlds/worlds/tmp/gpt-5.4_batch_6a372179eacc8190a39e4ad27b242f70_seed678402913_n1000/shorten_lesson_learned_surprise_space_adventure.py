#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shorten_lesson_learned_surprise_space_adventure.py
=============================================================================

A small storyworld about a child on a pretend space mission who wants to
shorten the trip by taking a risky shortcut. A helpful robot warns about the
cargo, the world state decides whether the shortcut is avoided or causes a
problem, and the ending always includes a spacey surprise and a lesson learned.

Run it
------
python storyworlds/worlds/gpt-5.4/shorten_lesson_learned_surprise_space_adventure.py
python storyworlds/worlds/gpt-5.4/shorten_lesson_learned_surprise_space_adventure.py --cargo comet_jar
python storyworlds/worlds/gpt-5.4/shorten_lesson_learned_surprise_space_adventure.py --shortcut wide_ramp
python storyworlds/worlds/gpt-5.4/shorten_lesson_learned_surprise_space_adventure.py --all
python storyworlds/worlds/gpt-5.4/shorten_lesson_learned_surprise_space_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/shorten_lesson_learned_surprise_space_adventure.py --json
python storyworlds/worlds/gpt-5.4/shorten_lesson_learned_surprise_space_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
IMPULSE_INIT = 5.0
CAREFUL_TRAITS = {"careful", "patient", "thoughtful", "steady"}


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
    size: int = 1
    fragile: bool = False
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
class Destination:
    id: str
    label: str
    phrase: str
    place_line: str
    surprise_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    size: int
    fragile: bool
    contents: str
    problem_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    label: str
    phrase: str
    clearance: int
    jostle: int
    scenic: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    handles_stuck: bool
    handles_spill: bool
    action_line: str
    qa_line: str
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


def _r_problem_to_feelings(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    hero = world.get("hero")
    robot = world.get("robot")
    if cargo.meters["stuck"] >= THRESHOLD:
        sig = ("fear_stuck",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            robot.memes["concern"] += 1
            out.append("__stuck__")
    if cargo.meters["spilled"] >= THRESHOLD:
        sig = ("fear_spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            robot.memes["concern"] += 1
            out.append("__spill__")
    return out


CAUSAL_RULES = [
    Rule(name="problem_to_feelings", tag="social", apply=_r_problem_to_feelings),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def cargo_at_risk(cargo: Cargo, shortcut: Shortcut) -> bool:
    return cargo.size > shortcut.clearance or (cargo.fragile and shortcut.jostle >= 2)


def incident_kind(cargo: Cargo, shortcut: Shortcut) -> str:
    if cargo.size > shortcut.clearance:
        return "stuck"
    if cargo.fragile and shortcut.jostle >= 2:
        return "spill"
    return "none"


def compatible_fixes(kind: str) -> list[Fix]:
    out: list[Fix] = []
    for fix in FIXES.values():
        if fix.sense < SENSE_MIN:
            continue
        if kind == "stuck" and fix.handles_stuck:
            out.append(fix)
        if kind == "spill" and fix.handles_spill:
            out.append(fix)
    return out


def best_fix(kind: str) -> Fix:
    options = compatible_fixes(kind)
    if not options:
        raise StoryError(f"(No sensible fix is available for incident type '{kind}'.)")
    return max(options, key=lambda f: (f.sense, f.label))


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(trait: str, trust: int) -> bool:
    authority = initial_care(trait) + 1.0 + (2.0 if trust >= 6 else 0.0)
    return authority > IMPULSE_INIT


def _do_shortcut(world: World, cargo_cfg: Cargo, shortcut_cfg: Shortcut, narrate: bool = True) -> None:
    cargo = world.get("cargo")
    hero = world.get("hero")
    hero.meters["distance"] += 1
    hero.memes["haste"] += 1
    kind = incident_kind(cargo_cfg, shortcut_cfg)
    if kind == "stuck":
        cargo.meters["stuck"] += 1
        cargo.meters["delayed"] += 1
    elif kind == "spill":
        cargo.meters["spilled"] += 1
        cargo.meters["delayed"] += 1
    propagate(world, narrate=narrate)


def predict_shortcut(world: World, cargo_cfg: Cargo, shortcut_cfg: Shortcut) -> dict:
    sim = world.copy()
    _do_shortcut(sim, cargo_cfg, shortcut_cfg, narrate=False)
    cargo = sim.get("cargo")
    return {
        "stuck": cargo.meters["stuck"] >= THRESHOLD,
        "spilled": cargo.meters["spilled"] >= THRESHOLD,
        "incident": incident_kind(cargo_cfg, shortcut_cfg),
    }


def intro(world: World, hero: Entity, robot: Entity, commander: Entity,
          cargo_cfg: Cargo, destination: Destination) -> None:
    hero.memes["joy"] += 1
    robot.memes["care"] += 1
    world.say(
        f"{hero.id} was spending the afternoon aboard a make-believe moon ship built from chairs, "
        f"blankets, and one silver cardboard panel. Beside {hero.pronoun('object')} rolled "
        f"{robot.id}, a helper robot with a blinking blue eye."
    )
    world.say(
        f'Commander {commander.label_word.capitalize()} gave them a mission: carry {cargo_cfg.phrase} '
        f"all the way to {destination.phrase}. {destination.place_line}"
    )


def launch(world: World, hero: Entity, cargo_cfg: Cargo) -> None:
    hero.meters["carrying"] += 1
    world.say(
        f"{hero.id} hugged {cargo_cfg.phrase} carefully against {hero.pronoun('possessive')} suit shirt. "
        f"Inside were {cargo_cfg.contents}, and the mission felt important."
    )


def tempt(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["impulse"] += 1
    world.say(
        f"Halfway there, {hero.id} spotted {shortcut.phrase}. {shortcut.scenic}"
    )
    world.say(
        f'"Look," {hero.id} said, "we can shorten the trip if we go through {shortcut.label}!"'
    )


def warn(world: World, robot: Entity, hero: Entity, cargo_cfg: Cargo, shortcut_cfg: Shortcut) -> None:
    pred = predict_shortcut(world, cargo_cfg, shortcut_cfg)
    robot.memes["caution"] += 1
    world.facts["predicted_incident"] = pred["incident"]
    if pred["stuck"]:
        world.say(
            f'{robot.id} gave a worried beep. "{cargo_cfg.label.capitalize()} is too big for {shortcut_cfg.label}. '
            f'If we rush, it could get stuck, and the mission will slow down instead of getting shorter."'
        )
    elif pred["spilled"]:
        world.say(
            f'{robot.id} whirred softly. "{cargo_cfg.label.capitalize()} would wobble in {shortcut_cfg.label}. '
            f'If it bumps too hard, {cargo_cfg.contents} could spill, and we would have to stop and clean up."'
        )
    else:
        world.say(
            f'{robot.id} blinked once. "This path is not the safest path for careful cargo."'
        )


def back_down(world: World, hero: Entity, robot: Entity, destination: Destination) -> None:
    hero.memes["relief"] += 1
    robot.memes["pride"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{hero.id} looked at the cargo, then at {robot.id}, and took a slower breath. "
        f'"You are right," {hero.pronoun()} said. "A mission does not get better just because it gets faster."'
    )
    world.say(
        f"So they stayed on the wide star path, step by step, until {destination.phrase} came into view."
    )


def defy(world: World, hero: Entity, robot: Entity, shortcut_cfg: Shortcut) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I think it will be fine," {hero.id} said, and hurried toward {shortcut_cfg.label} before '
        f"{robot.id} could roll around in front of {hero.pronoun('object')}."
    )


def incident(world: World, hero: Entity, cargo_cfg: Cargo, shortcut_cfg: Shortcut) -> None:
    _do_shortcut(world, cargo_cfg, shortcut_cfg, narrate=False)
    cargo = world.get("cargo")
    kind = incident_kind(cargo_cfg, shortcut_cfg)
    if kind == "stuck":
        world.say(
            f"But the shortcut was not really short. {cargo_cfg.problem_line} "
            f"{hero.id} tugged once and then froze, hearing the box scrape with a sad little rrk."
        )
    elif kind == "spill":
        world.say(
            f"But the shortcut shook harder than it looked. {cargo_cfg.problem_line} "
            f"A trail of shining bits hopped out and twinkled across the floor like tiny lost stars."
        )
    else:
        world.say("For one second it seemed the plan might work, but the mission still felt wrong.")


def call_help(world: World, robot: Entity, commander: Entity) -> None:
    world.say(
        f'"Commander {commander.label_word.capitalize()}!" {robot.id} beeped. '
        f'"We need the careful-mission plan!"'
    )


def repair(world: World, commander: Entity, fix: Fix, cargo_cfg: Cargo, destination: Destination) -> None:
    cargo = world.get("cargo")
    cargo.meters["stuck"] = 0.0
    cargo.meters["spilled"] = 0.0
    cargo.meters["repaired"] += 1
    cargo.meters["safe"] += 1
    hero = world.get("hero")
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"Commander {commander.label_word.capitalize()} came in with calm space boots and {fix.action_line}"
    )
    world.say(
        f"Soon the cargo was safe again, and they continued the mission the steady way to {destination.phrase}."
    )


def surprise_end(world: World, hero: Entity, robot: Entity, commander: Entity,
                 destination: Destination, cargo_cfg: Cargo, outcome: str) -> None:
    hero.memes["joy"] += 1
    hero.memes["wonder"] += 1
    robot.memes["joy"] += 1
    if outcome == "averted":
        opener = "When they arrived"
    else:
        opener = "When they finally arrived"
    world.say(
        f"{opener}, a surprise was waiting. {destination.surprise_line}"
    )
    world.say(
        f'Commander {commander.label_word.capitalize()} smiled. "I planned that as the last part of your mission."'
    )
    world.say(
        f"{hero.id} grinned at {robot.id} and held {cargo_cfg.label} a little more carefully. "
        f'"Next time," {hero.pronoun()} said, "I will not try to shorten a careful job. '
        f'The safe way can be the best way."'
    )
    world.say(destination.ending_line)


def tell(destination: Destination, cargo_cfg: Cargo, shortcut_cfg: Shortcut, fix: Fix,
         hero_name: str = "Nova", hero_gender: str = "girl",
         robot_name: str = "Pip", commander_type: str = "mother",
         trait: str = "careful", trust: int = 7) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
    ))
    robot = world.add(Entity(
        id="robot",
        kind="character",
        type="robot",
        label=robot_name,
        phrase=robot_name,
        role="robot",
        traits=["helpful"],
    ))
    commander = world.add(Entity(
        id="commander",
        kind="character",
        type=commander_type,
        label="the commander",
        phrase="Commander",
        role="commander",
    ))
    cargo = world.add(Entity(
        id="cargo",
        kind="thing",
        type="cargo",
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        role="cargo",
        size=cargo_cfg.size,
        fragile=cargo_cfg.fragile,
        tags=set(cargo_cfg.tags),
    ))
    hero.memes["trust"] = float(trust)
    hero.memes["care"] = initial_care(trait)

    intro(world, hero, robot, commander, cargo_cfg, destination)
    launch(world, hero, cargo_cfg)

    world.para()
    tempt(world, hero, shortcut_cfg)
    warn(world, robot, hero, cargo_cfg, shortcut_cfg)

    averted = would_avert(trait, trust)
    if averted:
        back_down(world, hero, robot, destination)
        outcome = "averted"
    else:
        defy(world, hero, robot, shortcut_cfg)
        world.para()
        incident(world, hero, cargo_cfg, shortcut_cfg)
        call_help(world, robot, commander)
        world.para()
        repair(world, commander, fix, cargo_cfg, destination)
        outcome = "repaired"

    world.para()
    surprise_end(world, hero, robot, commander, destination, cargo_cfg, outcome)

    world.facts.update(
        hero=hero,
        robot=robot,
        commander=commander,
        destination=destination,
        cargo_cfg=cargo_cfg,
        shortcut_cfg=shortcut_cfg,
        fix=fix,
        cargo=cargo,
        outcome=outcome,
        incident=incident_kind(cargo_cfg, shortcut_cfg),
        averted=averted,
        repaired=outcome == "repaired",
        trust=trust,
        trait=trait,
    )
    return world


DESTINATIONS = {
    "window_dome": Destination(
        id="window_dome",
        label="the window dome",
        phrase="the window dome",
        place_line="Past the cushions, a round blanket window glowed like the front glass of a real station.",
        surprise_line="Beyond the blanket window, the evening sky had turned deep purple, and the first bright star seemed to sit exactly above the ship.",
        ending_line="The little ship stayed in the living room, but for a while it felt as if the whole crew were floating quietly under the stars.",
        tags={"stars", "window"},
    ),
    "ring_garden": Destination(
        id="ring_garden",
        label="the ring garden",
        phrase="the ring garden",
        place_line="On the far side of the room, paper vines and silver hoops made a tiny garden for moon plants.",
        surprise_line="Tiny fairy lights hidden in the paper vines blinked on all at once, turning the ring garden into a soft green galaxy.",
        ending_line="Even the paper leaves looked alive, and the mission ended in a glow of green light and careful smiles.",
        tags={"garden", "lights"},
    ),
    "comet_deck": Destination(
        id="comet_deck",
        label="the comet deck",
        phrase="the comet deck",
        place_line="Near the bookshelf stood a high lookout deck with foil stars taped all around it.",
        surprise_line="A silver streamer comet suddenly uncurled from the top shelf and drifted down in a sparkling tail.",
        ending_line="The crew watched the silver tail sway overhead, and the long careful walk became the part they wanted to remember.",
        tags={"comet", "stars"},
    ),
}

CARGOES = {
    "star_cake": Cargo(
        id="star_cake",
        label="star cake",
        phrase="a round star cake in a clear box",
        size=3,
        fragile=True,
        contents="soft blue frosting and sugar stars",
        problem_line="The cake box wedged between the tunnel pads.",
        tags={"cake", "fragile"},
    ),
    "comet_jar": Cargo(
        id="comet_jar",
        label="comet jar",
        phrase="a glass comet jar full of glowing beads",
        size=1,
        fragile=True,
        contents="glowing beads",
        problem_line="The jar knocked the tunnel wall with a clink.",
        tags={"jar", "fragile"},
    ),
    "moon_seed_crate": Cargo(
        id="moon_seed_crate",
        label="moon-seed crate",
        phrase="a wide moon-seed crate with silver handles",
        size=3,
        fragile=False,
        contents="tiny paper seed packets",
        problem_line="The crate jammed sideways and would not scoot another inch.",
        tags={"seeds", "crate"},
    ),
}

SHORTCUTS = {
    "vent_tunnel": Shortcut(
        id="vent_tunnel",
        label="the vent tunnel",
        phrase="a low vent tunnel under two couch cushions",
        clearance=1,
        jostle=2,
        scenic="It looked like a secret astronaut passage, narrow and quick.",
        tags={"tunnel", "shortcut"},
    ),
    "meteor_gap": Shortcut(
        id="meteor_gap",
        label="the meteor gap",
        phrase="the meteor gap between scattered pillows",
        clearance=3,
        jostle=3,
        scenic="The pillows were supposed to be quiet meteors, but they wobbled when anyone stepped between them.",
        tags={"gap", "shortcut"},
    ),
    "wide_ramp": Shortcut(
        id="wide_ramp",
        label="the wide ramp",
        phrase="a broad foil ramp with tape stars on the sides",
        clearance=3,
        jostle=1,
        scenic="It was shiny and smooth, but it was really just another safe part of the main route.",
        tags={"ramp"},
    ),
}

FIXES = {
    "helper_cart": Fix(
        id="helper_cart",
        label="helper cart",
        sense=3,
        handles_stuck=True,
        handles_spill=False,
        action_line="set the cargo on a helper cart and rolled it around the narrow place instead.",
        qa_line="used a helper cart and took the cargo around the narrow shortcut",
        tags={"cart", "careful_tools"},
    ),
    "steady_tray": Fix(
        id="steady_tray",
        label="steady tray",
        sense=3,
        handles_stuck=False,
        handles_spill=True,
        action_line="gathered every shining bit onto a steady tray and carried the jar with two careful hands.",
        qa_line="used a steady tray and carried the shaken cargo carefully",
        tags={"tray", "careful_tools"},
    ),
    "vacuum_gloves": Fix(
        id="vacuum_gloves",
        label="vacuum gloves",
        sense=2,
        handles_stuck=False,
        handles_spill=True,
        action_line="put on soft vacuum gloves, picked up the scattered shining bits, and packed them safely again.",
        qa_line="used soft vacuum gloves to pick up the spilled pieces and pack them again",
        tags={"gloves", "careful_tools"},
    ),
    "push_harder": Fix(
        id="push_harder",
        label="push harder",
        sense=1,
        handles_stuck=False,
        handles_spill=False,
        action_line="pushed harder, which only would have made a careful mission rougher.",
        qa_line="tried to push harder",
        tags={"bad_fix"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for dest_id in DESTINATIONS:
        for cargo_id, cargo in CARGOES.items():
            for shortcut_id, shortcut in SHORTCUTS.items():
                if not cargo_at_risk(cargo, shortcut):
                    continue
                kind = incident_kind(cargo, shortcut)
                if compatible_fixes(kind):
                    combos.append((dest_id, cargo_id, shortcut_id))
    return combos


@dataclass
class StoryParams:
    destination: str
    cargo: str
    shortcut: str
    fix: str
    hero_name: str
    hero_gender: str
    robot_name: str
    commander: str
    trait: str
    trust: int
    seed: Optional[int] = None


GIRL_NAMES = ["Nova", "Luna", "Mira", "Zuri", "Tess", "Ivy", "Aria", "Nia"]
BOY_NAMES = ["Leo", "Milo", "Finn", "Jace", "Owen", "Theo", "Ezra", "Nico"]
ROBOT_NAMES = ["Pip", "Blink", "Comet", "Boop", "Zip"]
TRAITS = ["careful", "patient", "thoughtful", "steady", "curious", "bold"]

KNOWLEDGE = {
    "shortcut": [(
        "Why is a shortcut not always the best path?",
        "A shortcut is only good if it is also safe. If it makes you drop, bump, or break something, it can turn one quick trip into a much longer one."
    )],
    "robot": [(
        "What can a helper robot do on a space mission game?",
        "A helper robot can watch for problems, carry tools, and remind the crew to be careful. In a pretend mission, it is like a helpful friend who notices danger early."
    )],
    "fragile": [(
        "What does fragile mean?",
        "Fragile means something can break or spill if it gets bumped too hard. Fragile things need slow hands and careful paths."
    )],
    "cart": [(
        "What is a cart good for?",
        "A cart helps carry something heavy or bulky without squeezing it through a tight place. Rolling carefully can be safer than pushing with your arms."
    )],
    "tray": [(
        "Why use a tray for small things?",
        "A tray keeps little things together so they do not roll away. It gives them a flat safe place while you carry them."
    )],
    "gloves": [(
        "Why might gloves help on a careful job?",
        "Gloves can help your hands hold things gently and safely. They are useful when you need to pick up tiny pieces one by one."
    )],
    "stars": [(
        "Why do stars seem to twinkle?",
        "Stars look as if they twinkle because their light moves through Earth's air before it reaches your eyes. The moving air bends the light a tiny bit."
    )],
    "comet": [(
        "What is a comet?",
        "A comet is a small icy space object that can grow a bright tail when it travels near the Sun. Its tail glows because sunlight warms it and blows dust and gas away."
    )],
    "garden": [(
        "What is a garden?",
        "A garden is a place where people grow plants and help them stay healthy. In a pretend space story, a ring garden can be a special place for moon plants."
    )],
}
KNOWLEDGE_ORDER = ["shortcut", "robot", "fragile", "cart", "tray", "gloves", "stars", "comet", "garden"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cargo_cfg = f["cargo_cfg"]
    destination = f["destination"]
    shortcut_cfg = f["shortcut_cfg"]
    return [
        'Write a short space adventure for a 3-to-5-year-old that includes the word "shorten" and ends with a lesson learned.',
        f"Tell a gentle mission story where {hero.label} wants to shorten the trip by using {shortcut_cfg.label}, but careful thinking matters more than speed.",
        f"Write a surprise ending story about carrying {cargo_cfg.label} to {destination.label}, where the child learns that a careful path can be the best path.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    robot = f["robot"]
    commander = f["commander"]
    cargo_cfg = f["cargo_cfg"]
    destination = f["destination"]
    shortcut_cfg = f["shortcut_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]
    incident = f["incident"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child on a pretend space mission, {robot.label} the helper robot, and Commander {commander.label_word}. They were trying to carry {cargo_cfg.label} to {destination.label}."
        ),
        (
            "What did the child want to do?",
            f"{hero.label} wanted to shorten the trip by going through {shortcut_cfg.label}. That felt exciting because the shortcut looked quick and secret."
        ),
        (
            f"Why did {robot.label} warn {hero.label}?",
            (
                f"{robot.label} warned {hero.label} because {shortcut_cfg.label} was not safe for {cargo_cfg.label}. "
                + (
                    f"The cargo could get stuck there, which would make the mission slower instead of faster."
                    if incident == "stuck"
                    else f"The cargo could get bumped and spill, which would stop the mission and make a mess."
                )
            ),
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What happened after the warning?",
            f"{hero.label} listened and chose the wide safe path instead. That kept the cargo safe, and it showed that {hero.pronoun('subject')} learned before anything went wrong."
        ))
    else:
        qa.append((
            "What problem happened in the shortcut?",
            (
                f"The shortcut caused trouble for {cargo_cfg.label}. "
                + (
                    f"It got stuck because the path was too tight."
                    if incident == "stuck"
                    else f"It was shaken too hard, so some of the cargo spilled out."
                )
            ),
        ))
        qa.append((
            f"How did Commander {commander.label_word} help?",
            f"Commander {commander.label_word} {fix.qa_line}. The help worked because it matched the real problem instead of rushing again."
        ))
    qa.append((
        "What was the surprise at the end?",
        f"The surprise was waiting at {destination.label}: {destination.surprise_line[0].lower() + destination.surprise_line[1:]} It turned the ending into a reward for finishing the mission carefully."
    ))
    qa.append((
        "What lesson did the child learn?",
        f"{hero.label} learned that trying to shorten a careful job can make it take longer. A safe path protects the mission, the cargo, and everyone's calm feelings."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"shortcut", "robot"}
    cargo_cfg = f["cargo_cfg"]
    destination = f["destination"]
    fix = f["fix"]
    if cargo_cfg.fragile:
        tags.add("fragile")
    if "cart" in fix.tags:
        tags.add("cart")
    if "tray" in fix.tags:
        tags.add("tray")
    if "gloves" in fix.tags:
        tags.add("gloves")
    if "stars" in destination.tags:
        tags.add("stars")
    if "comet" in destination.tags:
        tags.add("comet")
    if "garden" in destination.tags:
        tags.add("garden")
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.size:
            bits.append(f"size={ent.size}")
        if ent.fragile:
            bits.append("fragile=True")
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
        destination="window_dome",
        cargo="moon_seed_crate",
        shortcut="vent_tunnel",
        fix="helper_cart",
        hero_name="Nova",
        hero_gender="girl",
        robot_name="Pip",
        commander="mother",
        trait="careful",
        trust=8,
    ),
    StoryParams(
        destination="comet_deck",
        cargo="comet_jar",
        shortcut="meteor_gap",
        fix="steady_tray",
        hero_name="Leo",
        hero_gender="boy",
        robot_name="Blink",
        commander="father",
        trait="bold",
        trust=4,
    ),
    StoryParams(
        destination="ring_garden",
        cargo="star_cake",
        shortcut="vent_tunnel",
        fix="helper_cart",
        hero_name="Mira",
        hero_gender="girl",
        robot_name="Boop",
        commander="mother",
        trait="patient",
        trust=7,
    ),
]


def explain_rejection(cargo: Cargo, shortcut: Shortcut) -> str:
    if not cargo_at_risk(cargo, shortcut):
        return (
            f"(No story: {shortcut.label} is not actually risky for {cargo.label}, so there is no honest warning, no problem, and no lesson to learn. "
            f"Pick a tighter or shakier shortcut.)"
        )
    kind = incident_kind(cargo, shortcut)
    if not compatible_fixes(kind):
        return (
            f"(No story: {shortcut.label} would cause a '{kind}' problem for {cargo.label}, but no sensible fix in this world can solve that problem.)"
        )
    return "(No story: this combination is not reasonable.)"


def explain_fix(fix_id: str, cargo: Cargo, shortcut: Shortcut) -> str:
    fix = FIXES[fix_id]
    kind = incident_kind(cargo, shortcut)
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix_id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). Try a calmer, more careful tool.)"
        )
    if kind == "stuck" and not fix.handles_stuck:
        return (
            f"(Refusing fix '{fix_id}': {cargo.label} would get stuck in {shortcut.label}, and this fix does not solve a stuck cargo problem.)"
        )
    if kind == "spill" and not fix.handles_spill:
        return (
            f"(Refusing fix '{fix_id}': {cargo.label} would spill in {shortcut.label}, and this fix does not solve a spilled cargo problem.)"
        )
    return ""


def outcome_of(params: StoryParams) -> str:
    cargo = CARGOES[params.cargo]
    shortcut = SHORTCUTS[params.shortcut]
    if would_avert(params.trait, params.trust):
        return "averted"
    kind = incident_kind(cargo, shortcut)
    fix = FIXES[params.fix]
    if kind == "stuck" and fix.handles_stuck and fix.sense >= SENSE_MIN:
        return "repaired"
    if kind == "spill" and fix.handles_spill and fix.sense >= SENSE_MIN:
        return "repaired"
    raise StoryError(explain_fix(params.fix, cargo, shortcut) or "(Invalid outcome configuration.)")


ASP_RULES = r"""
% --- gate ---------------------------------------------------------
risk(C, S) :- cargo(C), shortcut(S), size(C, Z), clearance(S, K), Z > K.
risk(C, S) :- cargo(C), shortcut(S), fragile(C), jostle(S, J), J >= 2.

incident(C, S, stuck) :- size(C, Z), clearance(S, K), Z > K.
incident(C, S, spill) :- not incident(C, S, stuck), fragile(C), jostle(S, J), J >= 2.

sensible_fix(F) :- fix(F), sense(F, N), sense_min(M), N >= M.
compatible_fix(C, S, F) :- incident(C, S, stuck), sensible_fix(F), handles_stuck(F).
compatible_fix(C, S, F) :- incident(C, S, spill), sensible_fix(F), handles_spill(F).

valid(D, C, S) :- destination(D), cargo(C), shortcut(S), risk(C, S), compatible_fix(C, S, _).

% --- outcome ------------------------------------------------------
care_now(5) :- chosen_trait(T), careful_trait(T).
care_now(3) :- chosen_trait(T), not careful_trait(T).
trust_bonus(2) :- chosen_trust(N), N >= 6.
trust_bonus(0) :- chosen_trust(N), N < 6.
authority(C + 1 + B) :- care_now(C), trust_bonus(B).

averted :- authority(A), impulse_init(I), A > I.

repaired :- not averted, chosen_cargo(C), chosen_shortcut(S), chosen_fix(F),
            incident(C, S, stuck), handles_stuck(F), sensible_fix(F).
repaired :- not averted, chosen_cargo(C), chosen_shortcut(S), chosen_fix(F),
            incident(C, S, spill), handles_spill(F), sensible_fix(F).

outcome(averted) :- averted.
outcome(repaired) :- repaired.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did in DESTINATIONS:
        lines.append(asp.fact("destination", did))
    for cid, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("size", cid, cargo.size))
        if cargo.fragile:
            lines.append(asp.fact("fragile", cid))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("clearance", sid, shortcut.clearance))
        lines.append(asp.fact("jostle", sid, shortcut.jostle))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        if fix.handles_stuck:
            lines.append(asp.fact("handles_stuck", fid))
        if fix.handles_spill:
            lines.append(asp.fact("handles_spill", fid))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
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
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_shortcut", params.shortcut),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_trust", params.trust),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    if not atoms:
        return "?"
    return atoms[0][0]


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
    for s in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
            asp_out = asp_outcome(params)
            if py != asp_out:
                bad += 1
        except StoryError:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome checks differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "shorten" not in sample.story:
            raise StoryError("(Smoke test: generated story is empty or missing required word 'shorten'.)")
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old_stdout
        rendered = buf.getvalue()
        if "### smoke" not in rendered or "Generation prompts" not in rendered:
            raise StoryError("(Smoke test: emit() did not produce expected sections.)")
        print("OK: smoke test generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child tries to shorten a space mission with a shortcut and learns a careful lesson."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--robot-name")
    ap.add_argument("--commander", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
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
    if args.cargo and args.shortcut:
        cargo = CARGOES[args.cargo]
        shortcut = SHORTCUTS[args.shortcut]
        if not cargo_at_risk(cargo, shortcut):
            raise StoryError(explain_rejection(cargo, shortcut))
        if args.fix:
            msg = explain_fix(args.fix, cargo, shortcut)
            if msg:
                raise StoryError(msg)
    elif args.fix and not (args.cargo and args.shortcut):
        if FIXES[args.fix].sense < SENSE_MIN:
            raise StoryError(
                f"(Refusing fix '{args.fix}': it scores too low on common sense (sense={FIXES[args.fix].sense} < {SENSE_MIN}).)"
            )

    combos = [
        combo for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.shortcut is None or combo[2] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, cargo_id, shortcut_id = rng.choice(sorted(combos))
    cargo = CARGOES[cargo_id]
    shortcut = SHORTCUTS[shortcut_id]
    incident = incident_kind(cargo, shortcut)
    fixes = compatible_fixes(incident)
    if args.fix:
        msg = explain_fix(args.fix, cargo, shortcut)
        if msg:
            raise StoryError(msg)
        fix_id = args.fix
    else:
        fix_id = rng.choice(sorted(f.id for f in fixes))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    robot_name = args.robot_name or rng.choice(ROBOT_NAMES)
    commander = args.commander or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(0, 10)

    return StoryParams(
        destination=destination,
        cargo=cargo_id,
        shortcut=shortcut_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        robot_name=robot_name,
        commander=commander,
        trait=trait,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination '{params.destination}'.)")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo '{params.cargo}'.)")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut '{params.shortcut}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix '{params.fix}'.)")
    cargo = CARGOES[params.cargo]
    shortcut = SHORTCUTS[params.shortcut]
    if not cargo_at_risk(cargo, shortcut):
        raise StoryError(explain_rejection(cargo, shortcut))
    msg = explain_fix(params.fix, cargo, shortcut)
    if msg:
        raise StoryError(msg)

    world = tell(
        destination=DESTINATIONS[params.destination],
        cargo_cfg=cargo,
        shortcut_cfg=shortcut,
        fix=FIXES[params.fix],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        robot_name=params.robot_name,
        commander_type=params.commander,
        trait=params.trait,
        trust=params.trust,
    )
    story_text = world.render().replace(" hero ", f" {params.hero_name} ")
    story_text = story_text.replace("hero", params.hero_name)
    story_text = story_text.replace("robot", params.robot_name)
    story_text = story_text.replace("Commander mom", "Commander Mom")
    story_text = story_text.replace("Commander dad", "Commander Dad")

    hero_label = params.hero_name
    robot_label = params.robot_name
    story_text = story_text.replace("hero.id", hero_label).replace("robot.id", robot_label)
    story_text = story_text.replace("commander.label_word", params.commander)

    story_text = story_text.replace("hero.label", hero_label).replace("robot.label", robot_label)

    # Repair internal labels from entity ids to child-facing display names.
    story_text = story_text.replace("hero", hero_label)
    story_text = story_text.replace("robot", robot_label)

    return StorySample(
        params=params,
        story=story_text,
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
        print(f"{len(combos)} compatible (destination, cargo, shortcut) combos:\n")
        for destination, cargo, shortcut in combos:
            print(f"  {destination:12} {cargo:16} {shortcut}")
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
            header = f"### {p.hero_name}: {p.cargo} via {p.shortcut} to {p.destination} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
