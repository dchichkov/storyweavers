#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sir_victory_repetition_rhyme_space_adventure.py
============================================================================

A standalone storyworld for a tiny space adventure with a repeating rhyme,
a little "sir" flourish, and a clear victory at the end.

Premise
-------
A child space explorer and a helper robot carry a small victory token toward a
beacon on a moon, planet, or comet path. A risky obstacle stands in the way.
The child is tempted to rush. A grown-up commander warns what will happen,
the child tries anyway, a near-accident happens, and then a sensible rescue and
matching safety gear lead to a careful, triumphant finish.

The world model tracks:
- physical meters: drift, slip, dark, dropped, mission_risk, delivered
- emotional memes: joy, hurry, fear, relief, pride, trust, lesson

This world prefers a strong, small set of plausible variations over weak
coverage. A gear choice and a rescue choice must actually match the obstacle's
risk. Invalid explicit choices raise StoryError with a clear reason.

Run it
------
python storyworlds/worlds/gpt-5.4/sir_victory_repetition_rhyme_space_adventure.py
python storyworlds/worlds/gpt-5.4/sir_victory_repetition_rhyme_space_adventure.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/sir_victory_repetition_rhyme_space_adventure.py --all
python storyworlds/worlds/gpt-5.4/sir_victory_repetition_rhyme_space_adventure.py --qa
python storyworlds/worlds/gpt-5.4/sir_victory_repetition_rhyme_space_adventure.py --json
python storyworlds/worlds/gpt-5.4/sir_victory_repetition_rhyme_space_adventure.py --asp
python storyworlds/worlds/gpt-5.4/sir_victory_repetition_rhyme_space_adventure.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    ground: str
    sky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    risk: str
    severity: int
    ahead: str
    danger_line: str
    stumble_line: str
    safe_cross: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    finish_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    prep: str = ""
    use_line: str = ""
    chant: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
    guards: set[str] = field(default_factory=set)
    sense: int = 0
    power: int = 0
    success: str = ""
    fail: str = ""
    qa_text: str = ""
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


def _r_dropped(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    cargo = world.entities.get("cargo")
    mission = world.entities.get("mission")
    if hero is None or cargo is None or mission is None:
        return out
    risk = world.facts.get("risk", "")
    if hero.meters[risk] < THRESHOLD or hero.meters["protected"] >= THRESHOLD:
        return out
    sig = ("dropped", risk)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["dropped"] += 1
    mission.meters["mission_risk"] += 1
    hero.memes["fear"] += 1
    out.append("__drop__")
    return out


def _r_scared(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.entities.get("cargo")
    robot = world.entities.get("robot")
    commander = world.entities.get("commander")
    if cargo is None or cargo.meters["dropped"] < THRESHOLD:
        return out
    for who in (robot, commander):
        if who is None:
            continue
        sig = ("fear", who.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        who.memes["alarm"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="dropped", tag="physical", apply=_r_dropped),
    Rule(name="scared", tag="emotional", apply=_r_scared),
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


def cargo_safe_line(cargo: Cargo) -> str:
    return {
        "pennant": "The little pennant stayed smooth and bright.",
        "cup": "The tiny cup did not even get a scratch.",
        "medal": "The gold medal kept its round, warm shine.",
    }.get(cargo.id, "The victory token stayed safe.")


def hazard_at_risk(obstacle: Obstacle, gear: Gear, rescue: Rescue) -> bool:
    return obstacle.risk in gear.guards and obstacle.risk in rescue.guards


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def obstacle_pressure(obstacle: Obstacle, delay: int) -> int:
    return obstacle.severity + delay


def is_contained(rescue: Rescue, obstacle: Obstacle, delay: int) -> bool:
    return rescue.power >= obstacle_pressure(obstacle, delay)


def predict_trouble(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters[obstacle.risk] += 1
    propagate(sim, narrate=False)
    cargo = sim.get("cargo")
    mission = sim.get("mission")
    return {
        "dropped": cargo.meters["dropped"] >= THRESHOLD,
        "mission_risk": mission.meters["mission_risk"],
    }


def intro(world: World, place: Place, hero: Entity, robot: Entity, cargo: Cargo) -> None:
    hero.memes["joy"] += 1
    robot.memes["joy"] += 1
    world.say(
        f"{place.opening} {hero.id} marched beside a round helper robot named {robot.id}. "
        f'The robot gave a bright beep and said, "Forward, sir {hero.id}!"'
    )
    world.say(
        f"They were carrying {cargo.phrase} to the beacon hill, because tonight was the little base's victory parade."
    )
    world.say(
        f'{place.sky} and {place.ground} made the whole place feel grand. {hero.id} whispered, '
        f'"Victory, victory, almost in sight."'
    )


def obstacle_appears(world: World, place: Place, obstacle: Obstacle, cargo: Cargo) -> None:
    world.say(
        f"But between the team and the beacon hill lay {obstacle.ahead}. "
        f"The path pinched small, and {cargo.phrase} suddenly felt important and delicate."
    )


def tempt(world: World, hero: Entity) -> None:
    hero.memes["hurry"] += 1
    world.say(
        f'{hero.id} hugged the prize close and said, "I can dash. I can flash. I can be there in a splash!"'
    )


def warn(world: World, commander: Entity, hero: Entity, robot: Entity, obstacle: Obstacle, cargo: Cargo) -> None:
    pred = predict_trouble(world, obstacle)
    world.facts["predicted_dropped"] = pred["dropped"]
    world.facts["predicted_mission_risk"] = pred["mission_risk"]
    commander.memes["care"] += 1
    robot.memes["trust"] += 1
    world.say(
        f'{robot.id} blinked blue. "{obstacle.danger_line}"'
    )
    world.say(
        f'{commander.label_word.capitalize()} added, "Slow and low, that is how we go. If you rush here, you may lose the {cargo.label} before the victory song can start."'
    )


def defy(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But the thought of the cheering beacon tugged hard. Before anyone could stop {hero.pronoun('object')}, {hero.id} took one quick step, then another, then another."
    )


def accident(world: World, hero: Entity, obstacle: Obstacle, cargo: Entity) -> None:
    hero.meters[obstacle.risk] += 1
    cargo.meters["at_edge"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.stumble_line)
    if cargo.meters["dropped"] >= THRESHOLD:
        world.say(
            f"The {cargo.label} slipped from {hero.pronoun('possessive')} gloves and spun away with a tiny, terrible twinkle."
        )


def rescue_success(world: World, commander: Entity, rescue: Rescue, cargo: Cargo) -> None:
    cargo_ent = world.get("cargo")
    mission = world.get("mission")
    hero = world.get("hero")
    cargo_ent.meters["dropped"] = 0.0
    cargo_ent.meters["saved"] += 1
    hero.meters[world.facts["risk"]] = 0.0
    mission.meters["mission_risk"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f"{commander.label_word.capitalize()} moved fast and {rescue.success}."
    )
    world.say(
        f'"Got it," {commander.pronoun()} said. "The prize is safe, and so are you."'
    )
    world.say(cargo_safe_line(cargo))


def rescue_fail(world: World, commander: Entity, rescue: Rescue, cargo: Cargo) -> None:
    cargo_ent = world.get("cargo")
    mission = world.get("mission")
    hero = world.get("hero")
    cargo_ent.meters["lost"] += 1
    mission.meters["mission_risk"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"{commander.label_word.capitalize()} tried and {rescue.fail}."
    )
    world.say(
        f"The {cargo.label} vanished into the shadows below, and the beacon hill stayed quiet for one sad minute."
    )


def lesson(world: World, commander: Entity, hero: Entity, robot: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["trust"] += 1
    robot.memes["relief"] += 1
    world.say(
        f"{commander.label_word.capitalize()} knelt in the dust and held one steady hand near {hero.id}'s shoulder."
    )
    world.say(
        f'"Brave does not mean fast," {commander.pronoun()} said softly. "Brave means you listen, you clip, you check, and then you go."'
    )
    world.say(
        f'{robot.id} gave a gentler beep this time. "Clip and check. Clip and check."'
    )


def gear_up(world: World, hero: Entity, gear: Gear) -> None:
    hero.meters["protected"] = 1.0
    hero.memes["pride"] += 1
    world.say(
        f"Then {hero.id} {gear.prep}. {gear.use_line}"
    )
    world.say(
        f'{hero.id} took a breath and repeated the new traveling rhyme: "{gear.chant}"'
    )


def cross_safely(world: World, hero: Entity, obstacle: Obstacle, cargo: Cargo, gear: Gear) -> None:
    world.say(
        f"{obstacle.safe_cross} {gear.label.capitalize()} did their job, and step by step, the little team reached the beacon hill."
    )
    world.say(
        f"{hero.id} lifted {cargo.phrase} high and {cargo.finish_line}"
    )
    world.say(
        f'"Victory, victory!" sang {hero.id}. "{gear.chant}"'
    )


def gentle_loss_ending(world: World, commander: Entity, hero: Entity, robot: Entity, gear: Gear, cargo: Cargo) -> None:
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1
    world.say(
        f'No one was hurt, and that mattered most. {commander.label_word.capitalize()} put an arm around {hero.id}, while {robot.id} rolled close enough to touch {hero.pronoun("possessive")} boot.'
    )
    world.say(
        f'"Tomorrow we try again the safe way," {commander.pronoun()} promised. "{gear.chant}"'
    )
    world.say(
        f"Up above them, the stars still blinked, and {hero.id} whispered the word victory more quietly, as a promise for next time."
    )


def tell(
    place: Place,
    obstacle: Obstacle,
    cargo: Cargo,
    gear: Gear,
    rescue: Rescue,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    robot_name: str = "Pip",
    commander_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    robot = world.add(Entity(id="robot", kind="character", type="robot", label=robot_name, phrase=robot_name, role="robot"))
    commander = world.add(Entity(id="commander", kind="character", type=commander_type, label="the commander", phrase="the commander", role="commander"))
    cargo_ent = world.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo.label, phrase=cargo.phrase))
    mission = world.add(Entity(id="mission", kind="thing", type="mission", label="mission", phrase="the mission"))
    world.facts["risk"] = obstacle.risk

    intro(world, place, Entity(id=hero_name, kind="character", type=hero_gender), Entity(id=robot_name, kind="character", type="robot"), cargo)
    obstacle_appears(world, place, obstacle, cargo)

    world.para()
    tempt(world, hero=Entity(id=hero_name, kind="character", type=hero_gender))
    warn(world, commander=commander, hero=hero, robot=robot, obstacle=obstacle, cargo=cargo)
    defy(world, hero=Entity(id=hero_name, kind="character", type=hero_gender))

    world.para()
    accident(world, hero=hero, obstacle=obstacle, cargo=cargo_ent)

    contained = is_contained(rescue, obstacle, delay)
    severity = obstacle_pressure(obstacle, delay)
    cargo_ent.meters["severity"] = float(severity)

    world.para()
    if contained:
        rescue_success(world, commander=commander, rescue=rescue, cargo=cargo)
        lesson(world, commander=commander, hero=hero, robot=robot)
        world.para()
        gear_up(world, hero=Entity(id=hero_name, kind="character", type=hero_gender), gear=gear)
        cross_safely(world, hero=Entity(id=hero_name, kind="character", type=hero_gender), obstacle=obstacle, cargo=cargo, gear=gear)
        outcome = "contained"
    else:
        rescue_fail(world, commander=commander, rescue=rescue, cargo=cargo)
        lesson(world, commander=commander, hero=hero, robot=robot)
        world.para()
        gear_up(world, hero=Entity(id=hero_name, kind="character", type=hero_gender), gear=gear)
        gentle_loss_ending(world, commander=commander, hero=Entity(id=hero_name, kind="character", type=hero_gender), robot=Entity(id=robot_name, kind="character", type="robot"), gear=gear, cargo=cargo)
        outcome = "lost"

    hero.attrs["display_name"] = hero_name
    robot.attrs["display_name"] = robot_name
    commander.attrs["display_name"] = commander.label_word
    world.facts.update(
        place=place,
        obstacle=obstacle,
        cargo_cfg=cargo,
        gear=gear,
        rescue=rescue,
        hero=hero,
        robot=robot,
        commander=commander,
        hero_name=hero_name,
        robot_name=robot_name,
        delay=delay,
        severity=severity,
        outcome=outcome,
        delivered=outcome == "contained",
    )
    return world


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display_name", ent.label or ent.id)


PLACES = {
    "moon": Place(
        id="moon",
        label="moon",
        opening="Far above the sleeping Earth, on a chalky moon path,",
        ground="Silver dust puffed under their boots",
        sky="Black sky curved over them like velvet",
        tags={"moon", "space"},
    ),
    "mars": Place(
        id="mars",
        label="Mars",
        opening="On a red path outside a small Mars dome,",
        ground="Soft red grit whispered around their boots",
        sky="A tiny blue sunset floated over the far hills",
        tags={"mars", "space"},
    ),
    "comet": Place(
        id="comet",
        label="comet",
        opening="On the bright back of a slow, singing comet,",
        ground="Sparkly frost glittered under every careful step",
        sky="The star field stretched wide and sharp",
        tags={"comet", "space"},
    ),
}

OBSTACLES = {
    "ice_bridge": Obstacle(
        id="ice_bridge",
        label="ice bridge",
        risk="slip",
        severity=2,
        ahead="a thin blue ice bridge over a small shadow crack",
        danger_line="Slippery, sir. One fast step and the path may skate your boots away.",
        stumble_line="The ice gave a tiny squeak. One boot shot sideways, and the world tilted.",
        safe_cross="This time the team crossed the ice bridge slowly, heel to toe, heel to toe.",
        tags={"ice", "slip", "bridge"},
    ),
    "moon_rocks": Obstacle(
        id="moon_rocks",
        label="moon rocks",
        risk="drift",
        severity=1,
        ahead="a field of springy moon rocks where every bounce was bigger than it looked",
        danger_line="Bouncy, sir. One wild hop and low gravity may toss both boots and prize.",
        stumble_line="A rock kicked back harder than expected. The next hop lifted too high, and the path slid away beneath the boots.",
        safe_cross="This time the team moved over the moon rocks in small planted steps, never letting a bounce grow too big.",
        tags={"moon", "rocks", "drift"},
    ),
    "dark_tunnel": Obstacle(
        id="dark_tunnel",
        label="dark tunnel",
        risk="dark",
        severity=1,
        ahead="a dark tunnel where the floor curled out of sight",
        danger_line="Dark ahead, sir. One rushed stride and the tunnel may hide the edge from you.",
        stumble_line="The dark folded around the path. A toe bumped stone, and the next step found only a wobble.",
        safe_cross="This time the team followed the tunnel wall carefully, step by step, with every corner plainly lit.",
        tags={"dark", "tunnel", "space"},
    ),
}

CARGOES = {
    "pennant": Cargo(
        id="pennant",
        label="victory pennant",
        phrase="a little silver victory pennant",
        finish_line="hooked it to the beacon ring, where it fluttered like a happy fish in the air fans.",
        tags={"victory", "flag"},
    ),
    "cup": Cargo(
        id="cup",
        label="victory cup",
        phrase="a tiny gold victory cup",
        finish_line="set it on the beacon shelf, where it flashed warm and bright.",
        tags={"victory", "cup"},
    ),
    "medal": Cargo(
        id="medal",
        label="victory medal",
        phrase="a round victory medal on a blue ribbon",
        finish_line="hung it on the beacon hook, and the ribbon gleamed like a tiny river.",
        tags={"victory", "medal"},
    ),
}

GEARS = {
    "magnet_boots": Gear(
        id="magnet_boots",
        label="magnet boots",
        phrase="a pair of magnet boots",
        guards={"slip", "drift"},
        prep="clicked on the magnet boots",
        use_line="Each sole answered with a neat little clack-clack as it kissed the ground.",
        chant="Clack and check, slow as we go.",
        tags={"boots", "space_gear"},
    ),
    "guide_line": Gear(
        id="guide_line",
        label="guide line",
        phrase="a bright guide line",
        guards={"slip", "drift"},
        prep="clipped the bright guide line to the belt ring",
        use_line="The line stayed snug and kind, never pulling hard, only reminding the body where safe balance lived.",
        chant="Clip and check, step by step.",
        tags={"rope", "space_gear"},
    ),
    "helmet_lamp": Gear(
        id="helmet_lamp",
        label="helmet lamp",
        phrase="a helmet lamp",
        guards={"dark"},
        prep="clicked on the helmet lamp",
        use_line="A warm white circle opened on the floor, and the scary dark became a simple path again.",
        chant="Glow and go, slow and low.",
        tags={"lamp", "space_gear"},
    ),
}

RESCUES = {
    "reel_arm": Rescue(
        id="reel_arm",
        label="reel arm",
        guards={"slip", "drift"},
        sense=3,
        power=3,
        success="swung out the rover's reel arm and caught the prize before it could vanish into the crack",
        fail="swung out the rover's reel arm, but the prize had already bounced too far to catch",
        qa_text="used the rover's reel arm to catch the prize",
        tags={"rescue", "rover"},
    ),
    "helper_drone": Rescue(
        id="helper_drone",
        label="helper drone",
        guards={"slip", "drift", "dark"},
        sense=2,
        power=2,
        success="sent a helper drone zipping under the spinning prize and lifted it neatly back to safe hands",
        fail="sent a helper drone after the prize, but it disappeared too quickly into the shadows",
        qa_text="sent a helper drone to grab the prize",
        tags={"rescue", "drone"},
    ),
    "beacon_floodlight": Rescue(
        id="beacon_floodlight",
        label="beacon floodlight",
        guards={"dark"},
        sense=3,
        power=2,
        success="hit the beacon floodlight switch, and a broad gold beam showed exactly where the prize had skidded",
        fail="hit the beacon floodlight switch, but the light came a breath too late to save the falling prize",
        qa_text="turned on the beacon floodlight to find and save the prize",
        tags={"rescue", "light"},
    ),
    "net_launcher": Rescue(
        id="net_launcher",
        label="net launcher",
        guards={"drift"},
        sense=1,
        power=1,
        success="fired a little net and snagged the prize",
        fail="fired a little net, but it only fluttered past the prize",
        qa_text="used a net launcher to snag the prize",
        tags={"rescue", "net"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Zia", "Ayla", "Tess", "Ruby", "Nia"]
BOY_NAMES = ["Orion", "Leo", "Finn", "Milo", "Arlo", "Theo", "Kai", "Ezra"]
ROBOT_NAMES = ["Pip", "Dot", "Blink", "Bop", "Tink", "Sprocket"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    cargo: str
    gear: str
    rescue: str
    hero_name: str
    hero_gender: str
    robot_name: str
    commander: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for cargo_id in CARGOES:
                for gear_id, gear in GEARS.items():
                    for rescue_id, rescue in RESCUES.items():
                        if hazard_at_risk(obstacle, gear, rescue) and rescue.sense >= SENSE_MIN:
                            combos.append((place_id, obstacle_id, cargo_id, gear_id, rescue_id))
    return combos


KNOWLEDGE = {
    "space": [(
        "What is a space beacon?",
        "A space beacon is a bright signal light or marker that helps explorers find the right place. It can also be a meeting point."
    )],
    "moon": [(
        "Why do people bounce on the moon?",
        "The moon has weaker gravity than Earth, so bodies feel lighter there. That can make hops and bounces much bigger."
    )],
    "mars": [(
        "What is Mars like?",
        "Mars is a dusty red planet with rocks, cold air, and a thin sky. Explorers need special gear to move around safely there."
    )],
    "comet": [(
        "What is a comet?",
        "A comet is a snowy, icy space rock that travels around the sun. Some comets shine because sunlight touches their ice and dust."
    )],
    "ice": [(
        "Why is ice slippery?",
        "Ice is smooth, and shoes do not grip it well. That makes feet slide if you move too fast."
    )],
    "dark": [(
        "Why is it harder to walk in the dark?",
        "In the dark, it is hard to see edges and bumps. A good light helps your eyes and feet work together."
    )],
    "boots": [(
        "What do magnet boots do?",
        "Magnet boots help an explorer stay planted on metal or prepared paths. They make slipping and drifting less likely."
    )],
    "rope": [(
        "What does a guide line do?",
        "A guide line clips to you and to a safe point. It helps you keep balance and not wander away from the path."
    )],
    "lamp": [(
        "What does a helmet lamp do?",
        "A helmet lamp shines where you are looking. That helps you see the path without using your hands."
    )],
    "drone": [(
        "What is a helper drone?",
        "A helper drone is a small flying robot that can carry or fetch things. It helps when something is hard to reach."
    )],
    "light": [(
        "What does a floodlight do?",
        "A floodlight spreads a wide bright beam over a big area. It helps people see clearly and quickly."
    )],
    "victory": [(
        "What does victory mean?",
        "Victory means you finished something well or reached your goal. It can be quiet and careful, not just fast and loud."
    )],
}
KNOWLEDGE_ORDER = [
    "space",
    "moon",
    "mars",
    "comet",
    "ice",
    "dark",
    "boots",
    "rope",
    "lamp",
    "drone",
    "light",
    "victory",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero_name"]
    obstacle = f["obstacle"]
    cargo = f["cargo_cfg"]
    gear = f["gear"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "sir" and "victory" and uses gentle repetition and rhyme.',
        f"Tell a story where {hero} carries a {cargo.label} toward a beacon, tries to hurry past a {obstacle.label}, and learns to move safely instead.",
        f'Write a child-facing story with a repeating travel rhyme like "{gear.chant}" and a happy ending earned through careful choices.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero_name = f["hero_name"]
    robot_name = f["robot_name"]
    commander = f["commander"]
    obstacle = f["obstacle"]
    cargo = f["cargo_cfg"]
    gear = f["gear"]
    rescue = f["rescue"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child explorer, {robot_name} the helper robot, and {commander.label_word} the commander. Together they are trying to carry a {cargo.label} to the beacon hill."
        ),
        (
            f"Why did {hero_name} want to hurry?",
            f"{hero_name} wanted to reach the beacon hill in time for the little victory parade. That made hurrying feel tempting even though the path was dangerous."
        ),
        (
            f"What was the problem on the way to the beacon?",
            f"The team had to get past {obstacle.ahead}. That obstacle was risky because {obstacle.danger_line[0].lower() + obstacle.danger_line[1:]}"
        ),
        (
            f"What warning did the commander give?",
            f"The commander said not to rush and reminded {hero_name} that careful bravery matters more than speed. The warning was about keeping both the child and the {cargo.label} safe."
        ),
    ]
    if outcome == "contained":
        qa.extend([
            (
                f"What happened when {hero_name} rushed?",
                f"{hero_name} stumbled, and the {cargo.label} slipped away for a moment. The danger came from hurrying across the {obstacle.label} without the right safety help."
            ),
            (
                f"How was the problem fixed?",
                f"The commander {rescue.qa_text}. After that, {hero_name} used {gear.label}, which matched the problem instead of trying to outrun it."
            ),
            (
                "How did the story end?",
                f"It ended with a true victory: the team reached the beacon hill and placed the {cargo.label} safely. The final cheers feel earned because the child changed from rushing to moving carefully."
            ),
        ])
    else:
        qa.extend([
            (
                f"Could the commander save the {cargo.label} in time?",
                f"No. The commander tried, but the prize was already too far gone. Even so, everyone stayed safe, and that mattered most."
            ),
            (
                "How did the ending still show a lesson?",
                f"The team stopped, breathed, and promised to try again the careful way next time. The quiet ending shows that victory can begin with learning, even before you win the prize."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["obstacle"].tags) | set(f["cargo_cfg"].tags) | set(f["gear"].tags) | set(f["rescue"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(obstacle: Obstacle, gear: Optional[Gear], rescue: Optional[Rescue]) -> str:
    if gear is not None and obstacle.risk not in gear.guards:
        return (
            f"(No story: {gear.label} does not solve the risk on {obstacle.label}. "
            f"It guards {sorted(gear.guards)}, but this obstacle needs help with {obstacle.risk}.)"
        )
    if rescue is not None and obstacle.risk not in rescue.guards:
        return (
            f"(No story: {rescue.label} is not a sensible rescue for {obstacle.label}. "
            f"It helps with {sorted(rescue.guards)}, but this obstacle's risk is {obstacle.risk}.)"
        )
    if rescue is not None and rescue.sense < SENSE_MIN:
        return (
            f"(No story: {rescue.label} is known to the world, but it scores too low on common sense "
            f"(sense={rescue.sense} < {SENSE_MIN}). Pick a safer rescue.)"
        )
    return "(No story: these options do not make a reasonable space mission.)"


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    rescue = RESCUES[params.rescue]
    return "contained" if is_contained(rescue, obstacle, params.delay) else "lost"


ASP_RULES = r"""
valid(P, O, C, G, R) :-
    place(P), obstacle(O), cargo(C), gear(G), rescue(R),
    risk(O, K), guards_gear(G, K), guards_rescue(R, K),
    sense(R, S), sense_min(M), S >= M.

severity(V) :- chosen_obstacle(O), base_severity(O, B), delay(D), V = B + D.
contained :- chosen_obstacle(O), chosen_rescue(R),
             severity(V), power(R, P), P >= V.
outcome(contained) :- contained.
outcome(lost) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("risk", oid, obstacle.risk))
        lines.append(asp.fact("base_severity", oid, obstacle.severity))
    for cid in CARGOES:
        lines.append(asp.fact("cargo", cid))
    for gid, gear in GEARS.items():
        lines.append(asp.fact("gear", gid))
        for risk in sorted(gear.guards):
            lines.append(asp.fact("guards_gear", gid, risk))
    for rid, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, rescue.sense))
        lines.append(asp.fact("power", rid, rescue.power))
        for risk in sorted(rescue.guards):
            lines.append(asp.fact("guards_rescue", rid, risk))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_rescue", params.rescue),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        place="moon",
        obstacle="moon_rocks",
        cargo="pennant",
        gear="magnet_boots",
        rescue="reel_arm",
        hero_name="Nova",
        hero_gender="girl",
        robot_name="Pip",
        commander="mother",
        delay=0,
    ),
    StoryParams(
        place="mars",
        obstacle="ice_bridge",
        cargo="cup",
        gear="guide_line",
        rescue="helper_drone",
        hero_name="Orion",
        hero_gender="boy",
        robot_name="Dot",
        commander="father",
        delay=0,
    ),
    StoryParams(
        place="comet",
        obstacle="dark_tunnel",
        cargo="medal",
        gear="helmet_lamp",
        rescue="beacon_floodlight",
        hero_name="Luna",
        hero_gender="girl",
        robot_name="Blink",
        commander="mother",
        delay=1,
    ),
    StoryParams(
        place="moon",
        obstacle="ice_bridge",
        cargo="cup",
        gear="magnet_boots",
        rescue="helper_drone",
        hero_name="Leo",
        hero_gender="boy",
        robot_name="Bop",
        commander="father",
        delay=1,
    ),
    StoryParams(
        place="moon",
        obstacle="moon_rocks",
        cargo="medal",
        gear="guide_line",
        rescue="helper_drone",
        hero_name="Mira",
        hero_gender="girl",
        robot_name="Tink",
        commander="mother",
        delay=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small state-driven space adventure with rhyme, repetition, sir, and victory."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--robot-name")
    ap.add_argument("--commander", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start for the problem before rescue")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump the world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.gear:
        obstacle = OBSTACLES[args.obstacle]
        gear = GEARS[args.gear]
        if obstacle.risk not in gear.guards:
            raise StoryError(explain_rejection(obstacle, gear, None))
    if args.obstacle and args.rescue:
        obstacle = OBSTACLES[args.obstacle]
        rescue = RESCUES[args.rescue]
        if obstacle.risk not in rescue.guards or rescue.sense < SENSE_MIN:
            raise StoryError(explain_rejection(obstacle, None, rescue))
    if args.rescue and RESCUES[args.rescue].sense < SENSE_MIN:
        obstacle = OBSTACLES[args.obstacle] if args.obstacle else next(iter(OBSTACLES.values()))
        raise StoryError(explain_rejection(obstacle, None, RESCUES[args.rescue]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.cargo is None or c[2] == args.cargo)
        and (args.gear is None or c[3] == args.gear)
        and (args.rescue is None or c[4] == args.rescue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obstacle, cargo, gear, rescue = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    robot_name = args.robot_name or rng.choice([n for n in ROBOT_NAMES if n != hero_name])
    commander = args.commander or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        obstacle=obstacle,
        cargo=cargo,
        gear=gear,
        rescue=rescue,
        hero_name=hero_name,
        hero_gender=hero_gender,
        robot_name=robot_name,
        commander=commander,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.gear not in GEARS:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")

    obstacle = OBSTACLES[params.obstacle]
    gear = GEARS[params.gear]
    rescue = RESCUES[params.rescue]
    if obstacle.risk not in gear.guards or obstacle.risk not in rescue.guards or rescue.sense < SENSE_MIN:
        raise StoryError(explain_rejection(obstacle, gear, rescue))

    world = tell(
        place=PLACES[params.place],
        obstacle=obstacle,
        cargo=CARGOES[params.cargo],
        gear=gear,
        rescue=rescue,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        robot_name=params.robot_name,
        commander_type=params.commander,
        delay=params.delay,
    )
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        py = outcome_of(params)
        asp_out = asp_outcome(params)
        if py != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "victory" not in sample.story.lower() or "sir" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story missing required seed words.)")
        _ = sample.to_json()
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, obstacle, cargo, gear, rescue) combos:\n")
        for place, obstacle, cargo, gear, rescue in combos:
            print(f"  {place:6} {obstacle:11} {cargo:7} {gear:12} {rescue}")
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
                f"### {p.hero_name}: {p.cargo} at {p.place} past {p.obstacle} "
                f"({p.gear}, {p.rescue}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
