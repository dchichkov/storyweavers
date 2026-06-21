#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/welfare_surprise_space_adventure.py
==============================================================

A standalone storyworld for a tiny "space welfare mission" domain.

Premise
-------
A child and a friend turn a room into a spaceship and set out on a welfare
mission: they must deliver a needed care crate to a small space outpost. The
temptation is always the same -- hurry past a hazard without the right support.
The surprise feature is built into the turn: Mission Control reveals a surprise
piece of helpful gear, and the ending includes a surprise thank-you from the
outpost when the mission goes well.

The world model keeps the story honest:
- each destination needs one specific kind of welfare cargo;
- some support tools are sensible, and some are known but refused;
- a mismatched or weak support leads to a late, damaged delivery ending.

Run it
------
python storyworlds/worlds/gpt-5.4/welfare_surprise_space_adventure.py
python storyworlds/worlds/gpt-5.4/welfare_surprise_space_adventure.py --destination moon_garden --cargo water_orbs
python storyworlds/worlds/gpt-5.4/welfare_surprise_space_adventure.py --destination moon_garden --cargo blanket_roll
python storyworlds/worlds/gpt-5.4/welfare_surprise_space_adventure.py --all
python storyworlds/worlds/gpt-5.4/welfare_surprise_space_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/welfare_surprise_space_adventure.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    fragile: bool = False
    protective: bool = False
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
    residents: str
    need: str
    need_line: str
    thanks: str
    surprise_gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    comfort_for: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    severity: int
    verb: str
    damage_line: str
    safe_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    covers: set[str] = field(default_factory=set)
    reveal: str = ""
    use_line: str = ""
    fail_line: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    destination: str
    cargo: str
    hazard: str
    support: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    hero_trait: str
    friend_trait: str
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


def _r_damage(world: World) -> list[str]:
    cargo = world.get("cargo")
    route = world.get("route")
    support = world.get("support")
    if route.meters["rough"] < THRESHOLD or cargo.meters["delivered"] >= THRESHOLD:
        return []
    if not cargo.fragile:
        return []
    sig = ("damage", cargo.id, support.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if support.meters["shielding"] >= THRESHOLD:
        return []
    cargo.meters["damaged"] += 1
    for kid_id in ("hero", "friend"):
        world.get(kid_id).memes["worry"] += 1
    return ["__damage__"]


def _r_relief(world: World) -> list[str]:
    cargo = world.get("cargo")
    outpost = world.get("outpost")
    if cargo.meters["delivered"] < THRESHOLD or cargo.meters["damaged"] >= THRESHOLD:
        return []
    sig = ("relief", outpost.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    outpost.memes["relief"] += 1
    for kid_id in ("hero", "friend"):
        world.get(kid_id).memes["pride"] += 1
        world.get(kid_id).memes["joy"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage", tag="physical", apply=_r_damage),
    Rule(name="relief", tag="social", apply=_r_relief),
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


DESTINATIONS = {
    "moon_garden": Destination(
        id="moon_garden",
        label="Moon Garden",
        phrase="the Moon Garden dome",
        residents="the moon sprouts",
        need="water_orbs",
        need_line="The moon sprouts were drooping, and their little silver leaves needed water.",
        thanks="The sprouts lifted their shiny leaves at once.",
        surprise_gift="a surprise packet of glow-seeds",
        tags={"welfare", "garden", "water"},
    ),
    "comet_nest": Destination(
        id="comet_nest",
        label="Comet Nest",
        phrase="the Comet Nest on the ridge",
        residents="the star chicks",
        need="blanket_roll",
        need_line="The star chicks were shivering in their nest and needed something warm.",
        thanks="The star chicks tucked themselves in and gave soft happy peeps.",
        surprise_gift="a surprise comet feather",
        tags={"welfare", "warmth", "nest"},
    ),
    "crater_clinic": Destination(
        id="crater_clinic",
        label="Crater Clinic",
        phrase="the Crater Clinic by the red rocks",
        residents="the rover pup",
        need="bandage_box",
        need_line="The rover pup had a bumped wheel and needed bandages and gentle care.",
        thanks="The rover pup wagged its little antenna tail and rolled in a neat circle.",
        surprise_gift="a surprise brass star badge",
        tags={"welfare", "clinic", "care"},
    ),
}

CARGOES = {
    "water_orbs": Cargo(
        id="water_orbs",
        label="water orbs",
        phrase="a welfare crate of bright blue water orbs",
        comfort_for="help thirsty plants drink again",
        fragile=True,
        tags={"welfare", "water"},
    ),
    "blanket_roll": Cargo(
        id="blanket_roll",
        label="blanket roll",
        phrase="a welfare crate with a soft blanket roll",
        comfort_for="keep cold little bodies warm",
        fragile=True,
        tags={"welfare", "warmth"},
    ),
    "bandage_box": Cargo(
        id="bandage_box",
        label="bandage box",
        phrase="a welfare crate with a bandage box and tiny wipes",
        comfort_for="help a hurt friend feel better",
        fragile=True,
        tags={"welfare", "care"},
    ),
    "party_flags": Cargo(
        id="party_flags",
        label="party flags",
        phrase="a box of party flags",
        comfort_for="decorate a place",
        fragile=False,
        tags={"party"},
    ),
}

HAZARDS = {
    "meteor_swirl": Hazard(
        id="meteor_swirl",
        label="meteor swirl",
        phrase="a swirling lane of pebbly meteors",
        severity=3,
        verb="rattled",
        damage_line="The bouncing trip knocked the welfare crate hard, and part of the cargo came loose inside.",
        safe_line="The shield held steady while little meteors tapped and bounced away.",
        tags={"meteor"},
    ),
    "shadow_tunnel": Hazard(
        id="shadow_tunnel",
        label="shadow tunnel",
        phrase="a dark tunnel where the floor curved away from the light",
        severity=2,
        verb="tilted",
        damage_line="In the dark bend, the welfare crate tipped and bumped the wall.",
        safe_line="Soft guide lights blinked on, and the crew could see every turn.",
        tags={"dark"},
    ),
    "dust_ring": Hazard(
        id="dust_ring",
        label="dust ring",
        phrase="a windy ring of red moon dust",
        severity=2,
        verb="shook",
        damage_line="Dust slapped the sides of the ship until the welfare crate slid sideways.",
        safe_line="A clear bubble wrapped the ship, and the dust whisked past without getting in.",
        tags={"dust"},
    ),
}

SUPPORTS = {
    "bubble_shield": Support(
        id="bubble_shield",
        label="bubble shield",
        phrase="a clear bubble shield",
        sense=3,
        power=4,
        covers={"meteor_swirl", "shadow_tunnel", "dust_ring"},
        reveal="Mission Control opened a cupboard and revealed a surprise bubble shield folded like a silver umbrella.",
        use_line="They clicked the bubble shield into place around the little ship.",
        fail_line="Even with the shield humming, the hazard hit harder than they expected.",
        qa_text="used the bubble shield to protect the ship and the welfare crate",
        tags={"shield"},
    ),
    "guide_beacons": Support(
        id="guide_beacons",
        label="guide beacons",
        phrase="two blinking guide beacons",
        sense=2,
        power=2,
        covers={"shadow_tunnel"},
        reveal="Mission Control reached under the table and pulled out a surprise pair of guide beacons.",
        use_line="They set the beacons ahead of them, and each tiny light showed the next safe step.",
        fail_line="The beacons could show the path, but they could not stop heavy bumps from jarring the crate.",
        qa_text="used guide beacons to light the path and keep the ship steady",
        tags={"light"},
    ),
    "cargo_clamps": Support(
        id="cargo_clamps",
        label="cargo clamps",
        phrase="strong cargo clamps",
        sense=2,
        power=3,
        covers={"meteor_swirl"},
        reveal="Mission Control smiled and brought out a surprise set of cargo clamps with click-click locks.",
        use_line="They fastened the welfare crate down with the cargo clamps until it could not wiggle at all.",
        fail_line="The clamps held the crate in place, but they could not clear away dust or light a dark turn.",
        qa_text="locked the welfare crate down with cargo clamps",
        tags={"cargo"},
    ),
    "speed_button": Support(
        id="speed_button",
        label="speed button",
        phrase="a shiny red speed button",
        sense=1,
        power=1,
        covers=set(),
        reveal="Mission Control had a shiny speed button, but it was only for silly pretend blasts, not careful missions.",
        use_line="They slapped the speed button and lurched forward too fast.",
        fail_line="Going faster only made the bumps worse.",
        qa_text="pressed a speed button",
        tags={"speed"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Ava", "Nora", "Zoe", "Ivy", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Noah", "Sam", "Ben"]
TRAITS = ["careful", "bright", "brave", "gentle", "curious", "steady"]


def cargo_matches(destination_id: str, cargo_id: str) -> bool:
    return DESTINATIONS[destination_id].need == cargo_id


def sensible_supports() -> list[Support]:
    return [s for s in SUPPORTS.values() if s.sense >= SENSE_MIN]


def is_protected(support: Support, hazard: Hazard) -> bool:
    return hazard.id in support.covers and support.power >= hazard.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for dest_id, dest in DESTINATIONS.items():
        for cargo_id in CARGOES:
            if not cargo_matches(dest_id, cargo_id):
                continue
            for hazard_id in HAZARDS:
                combos.append((dest_id, cargo_id, hazard_id))
    return combos


def explain_cargo(destination: Destination, cargo: Cargo) -> str:
    needed = CARGOES[destination.need]
    return (
        f"(No story: {destination.label} needs {needed.label}, not {cargo.label}. "
        f"A welfare mission works only when the cargo matches the outpost's need.)"
    )


def explain_support(support_id: str) -> str:
    support = SUPPORTS[support_id]
    better = ", ".join(sorted(s.id for s in sensible_supports()))
    return (
        f"(Refusing support '{support_id}': it scores too low on common sense "
        f"(sense={support.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    support = SUPPORTS[params.support]
    hazard = HAZARDS[params.hazard]
    return "safe" if is_protected(support, hazard) else "late"


def _predict_damage(world: World, hazard_id: str, support_id: str) -> bool:
    sim = world.copy()
    route = sim.get("route")
    support = sim.get("support")
    route.attrs["hazard_id"] = hazard_id
    support.attrs["support_id"] = support_id
    hazard = HAZARDS[hazard_id]
    tool = SUPPORTS[support_id]
    route.meters["rough"] += 1
    if is_protected(tool, hazard):
        support.meters["shielding"] += 1
    propagate(sim, narrate=False)
    return sim.get("cargo").meters["damaged"] >= THRESHOLD


def intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"After lunch, {hero.id} and {friend.id} turned the sofa, two chairs, and a striped blanket into a silver spaceship."
    )
    world.say(
        f"{hero.id} wore a saucepan lid like a captain's helmet, and {friend.id} held the crayon star map flat on the rug."
    )
    world.say(
        f'"Space couriers ready!" {hero.id} said. The room felt wide as the sky.'
    )


def mission_brief(world: World, parent: Entity, destination: Destination, cargo: Cargo) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    cargo_ent = world.get("cargo")
    cargo_ent.fragile = cargo.fragile
    cargo_ent.attrs["cargo_id"] = cargo.id
    cargo_ent.tags |= set(cargo.tags)
    world.say(
        f'Then {hero.id}\'s {parent.label_word} became Mission Control and set {cargo.phrase} between them.'
    )
    world.say(
        f'"This is a welfare mission," {parent.label_word} said. "You are taking it to {destination.phrase}, because {destination.need_line}"'
    )
    world.say(
        f"{friend.id} touched the crate gently. Inside was exactly what would {cargo.comfort_for}."
    )


def spot_hazard(world: World, destination: Destination, hazard: Hazard) -> None:
    world.say(
        f"On the map, the fastest way to {destination.phrase} crossed {hazard.phrase}."
    )
    world.say(
        f"It looked exciting, but the path also looked bumpy and hard to steer."
    )


def rush_idea(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["hurry"] += 1
    world.say(
        f'"Let\'s zip through the {hazard.label} before snack time," {hero.id} said. "{hero.pronoun("subject").capitalize()} can go fast."'
    )


def warning(world: World, friend: Entity, cargo: Cargo, hazard: Hazard) -> None:
    predicted = _predict_damage(world, hazard.id, "speed_button")
    friend.memes["care"] += 1
    world.facts["predicted_damage"] = predicted
    caution = "the welfare crate could get knocked open" if predicted else "the trip still looked too rough"
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. "If we hurry there, {caution}," {friend.pronoun()} said.'
    )
    world.say(
        f'"This mission is about helping somebody feel better, not about being first."'
    )


def surprise_support(world: World, parent: Entity, support: Support) -> None:
    support_ent = world.get("support")
    support_ent.attrs["support_id"] = support.id
    support_ent.tags |= set(support.tags)
    world.say(support.reveal)
    world.say(
        f'"Surprise," {parent.label_word} said. "Good crews use the right tool when they carry welfare supplies."'
    )


def launch(world: World, hero: Entity, friend: Entity, support: Support, hazard: Hazard) -> None:
    route = world.get("route")
    support_ent = world.get("support")
    route.attrs["hazard_id"] = hazard.id
    route.meters["rough"] += 1
    if is_protected(support, hazard):
        support_ent.meters["shielding"] += 1
    world.say(support.use_line)
    world.say(
        f"With a gentle whoosh, the ship rolled off across the rug and into {hazard.phrase}."
    )
    world.say(
        f"The floor seemed to tilt and sparkle as the {hazard.label} {hazard.verb} around them."
    )
    propagate(world, narrate=False)
    cargo = world.get("cargo")
    if cargo.meters["damaged"] >= THRESHOLD:
        world.say(hazard.damage_line)
    else:
        world.say(hazard.safe_line)


def deliver_safe(world: World, destination: Destination) -> None:
    cargo = world.get("cargo")
    outpost = world.get("outpost")
    cargo.meters["delivered"] += 1
    outpost.meters["served"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they reached {destination.phrase} and lifted out the welfare crate with both hands."
    )
    world.say(destination.thanks)


def deliver_late(world: World, destination: Destination) -> None:
    cargo = world.get("cargo")
    outpost = world.get("outpost")
    cargo.meters["delivered"] += 1
    outpost.meters["served"] += 1
    world.say(
        f"They still made it to {destination.phrase}, but when they opened the welfare crate, part of the help had spilled and the delivery was late."
    )
    world.say(
        f"The waiting friends were kind, yet {world.get('hero').id} could see they had needed that care sooner."
    )


def ending_safe(world: World, parent: Entity, destination: Destination, support: Support) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.say(
        f'Then came another surprise: from the outpost window, Mission Control pulled out {destination.surprise_gift} just for the crew.'
    )
    world.say(
        f'"For brave helpers," {parent.label_word} said. {hero.id} and {friend.id} laughed, because the best part of the adventure was knowing their welfare mission had worked.'
    )
    world.say(
        f"After that, the little ship always kept {support.label} in its pretend cargo bay, ready for the next kind trip among the stars."
    )


def ending_late(world: World, parent: Entity, destination: Destination, support: Support) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    cargo = world.get("cargo")
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them and spoke softly. "A welfare mission is for somebody else\'s comfort," {parent.pronoun()} said. "That means we plan for the cargo first."'
    )
    world.say(
        f"{hero.id} nodded and checked the dent in the {cargo.label}. Next time, the crew promised, they would not hurry past a space hazard with the wrong tool."
    )
    world.say(
        f"They parked the ship by the sofa and carefully set {support.phrase} beside the star map, ready to think harder on the next launch."
    )


def tell(
    destination: Destination,
    cargo: Cargo,
    hazard: Hazard,
    support: Support,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    hero_trait: str,
    friend_trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        attrs={"name": hero_name, "trait": hero_trait},
        tags={"crew"},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        phrase=friend_name,
        role="friend",
        attrs={"name": friend_name, "trait": friend_trait},
        tags={"crew"},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="Mission Control",
        role="parent",
        tags={"adult"},
    ))
    world.add(Entity(
        id="cargo",
        type="cargo",
        label=cargo.label,
        phrase=cargo.phrase,
        fragile=cargo.fragile,
        tags=set(cargo.tags),
    ))
    world.add(Entity(
        id="route",
        type="route",
        label=hazard.label,
        phrase=hazard.phrase,
        tags=set(hazard.tags),
    ))
    world.add(Entity(
        id="support",
        type="support",
        label=support.label,
        phrase=support.phrase,
        protective=True,
        tags=set(support.tags),
    ))
    world.add(Entity(
        id="outpost",
        type="outpost",
        label=destination.label,
        phrase=destination.phrase,
        tags=set(destination.tags),
    ))

    intro(world, hero, friend)
    mission_brief(world, parent, destination, cargo)
    spot_hazard(world, destination, hazard)

    world.para()
    rush_idea(world, hero, hazard)
    warning(world, friend, cargo, hazard)
    surprise_support(world, parent, support)

    world.para()
    launch(world, hero, friend, support, hazard)
    if world.get("cargo").meters["damaged"] >= THRESHOLD:
        deliver_late(world, destination)
        world.para()
        ending_late(world, parent, destination, support)
        outcome = "late"
    else:
        deliver_safe(world, destination)
        world.para()
        ending_safe(world, parent, destination, support)
        outcome = "safe"

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        destination=destination,
        cargo_cfg=cargo,
        hazard=hazard,
        support_cfg=support,
        outcome=outcome,
        delivered=world.get("cargo").meters["delivered"] >= THRESHOLD,
        damaged=world.get("cargo").meters["damaged"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "welfare": [(
        "What does welfare mean in this story?",
        "Here, welfare means helping someone stay safe, warm, watered, or cared for. It is about doing something kind that helps another person or creature feel better."
    )],
    "water": [(
        "Why do plants need water?",
        "Plants need water to stay alive and stand up strong. Without enough water, their leaves can droop."
    )],
    "warmth": [(
        "Why does a blanket help when someone is cold?",
        "A blanket helps hold warm air close to the body. That makes a cold creature feel warmer and safer."
    )],
    "care": [(
        "Why do bandages help after a bump or scrape?",
        "Bandages cover a sore spot and help protect it. Gentle care can also help someone feel calmer."
    )],
    "meteor": [(
        "What is a meteor?",
        "A meteor is a small piece of rock from space. In stories, a lot of little meteors can make travel feel bumpy and dangerous."
    )],
    "dark": [(
        "Why are lights helpful in a dark tunnel?",
        "Lights help you see where to step and where to steer. Seeing clearly helps you move more safely."
    )],
    "dust": [(
        "Why can blowing dust make travel hard?",
        "Blowing dust can get in your eyes or hide the path. It can also push light things around."
    )],
    "shield": [(
        "What does a shield do?",
        "A shield protects something important from bumps or flying bits. It is a cover that helps keep danger out."
    )],
    "light": [(
        "What are guide beacons for?",
        "Guide beacons are little lights that show the way. They help travelers follow a safe path."
    )],
    "cargo": [(
        "Why should cargo be fastened down?",
        "Fastening cargo keeps it from sliding or falling when a ride gets bumpy. That helps the things inside arrive safely."
    )],
}
KNOWLEDGE_ORDER = ["welfare", "water", "warmth", "care", "meteor", "dark", "dust", "shield", "light", "cargo"]


def display_name(ent: Entity) -> str:
    return ent.label or ent.attrs.get("name", ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = display_name(f["hero"])
    friend = display_name(f["friend"])
    destination = f["destination"]
    cargo = f["cargo_cfg"]
    hazard = f["hazard"]
    outcome = f["outcome"]
    if outcome == "safe":
        return [
            'Write a short story for a 3-to-5-year-old that includes the word "welfare" and feels like a space adventure.',
            f"Tell a gentle space story where {hero} and {friend} deliver {cargo.label} on a welfare mission to {destination.label}, face {hazard.label}, and get a surprise that helps them succeed.",
            "Write a story about children learning that helping others matters more than rushing, with a bright surprise near the end.",
        ]
    return [
        'Write a short story for a 3-to-5-year-old that includes the word "welfare" and feels like a space adventure.',
        f"Tell a cautionary space story where {hero} and {friend} try to carry welfare supplies through {hazard.label}, arrive late, and learn to choose the right tool next time.",
        "Write a story about a pretend mission that teaches planning and kindness, with a calm ending after a mistake.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    destination = f["destination"]
    cargo = f["cargo_cfg"]
    hazard = f["hazard"]
    support = f["support_cfg"]
    hero_name = display_name(hero)
    friend_name = display_name(friend)
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name} and {friend_name}, two children pretending to be space couriers, and {hero_name}'s {pw} as Mission Control."
        ),
        (
            "What was their mission?",
            f"They had a welfare mission to carry {cargo.label} to {destination.phrase}. The cargo mattered because the friends there needed that exact kind of help."
        ),
        (
            f"Why did {friend_name} not want to rush through the {hazard.label}?",
            f"{friend_name} worried the ride would be too rough for the welfare crate. That mattered because the cargo was supposed to comfort someone else, not just get there quickly."
        ),
        (
            "What was the surprise in the middle of the story?",
            f"Mission Control revealed {support.phrase} as a surprise tool for the trip. The surprise changed the mission because the children stopped thinking only about speed and started thinking about safety."
        ),
    ]
    if f["outcome"] == "safe":
        qa.extend([
            (
                f"How did they keep the welfare crate safe?",
                f"They {support.qa_text}. That worked because {support.label} matched the danger in the {hazard.label}."
            ),
            (
                "How did the story end?",
                f"They delivered the welfare crate safely, the outpost friends felt better, and the crew got {destination.surprise_gift}. The ending shows that careful help can still feel exciting and joyful."
            ),
        ])
    else:
        qa.extend([
            (
                "Did the mission go perfectly?",
                f"No. The crew still arrived, but the welfare crate was damaged and the help came late. The trouble happened because their tool was not the right one for the hazard."
            ),
            (
                "What did the children learn?",
                f"They learned that a welfare mission is about somebody else's comfort, so careful planning matters. Next time they would match the tool to the danger before rushing ahead."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"welfare"}
    tags |= set(f["destination"].tags)
    tags |= set(f["hazard"].tags)
    tags |= set(f["support_cfg"].tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.fragile:
            bits.append("fragile=True")
        if ent.protective:
            bits.append("protective=True")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        destination="moon_garden",
        cargo="water_orbs",
        hazard="meteor_swirl",
        support="cargo_clamps",
        hero="Luna",
        hero_gender="girl",
        friend="Max",
        friend_gender="boy",
        parent="mother",
        hero_trait="brave",
        friend_trait="careful",
    ),
    StoryParams(
        destination="comet_nest",
        cargo="blanket_roll",
        hazard="shadow_tunnel",
        support="guide_beacons",
        hero="Leo",
        hero_gender="boy",
        friend="Mia",
        friend_gender="girl",
        parent="father",
        hero_trait="curious",
        friend_trait="gentle",
    ),
    StoryParams(
        destination="crater_clinic",
        cargo="bandage_box",
        hazard="dust_ring",
        support="bubble_shield",
        hero="Nora",
        hero_gender="girl",
        friend="Finn",
        friend_gender="boy",
        parent="mother",
        hero_trait="steady",
        friend_trait="bright",
    ),
    StoryParams(
        destination="moon_garden",
        cargo="water_orbs",
        hazard="dust_ring",
        support="cargo_clamps",
        hero="Theo",
        hero_gender="boy",
        friend="Ivy",
        friend_gender="girl",
        parent="father",
        hero_trait="brave",
        friend_trait="careful",
    ),
]


ASP_RULES = r"""
% --- welfare cargo gate ----------------------------------------------------
matches_need(D, C) :- destination(D), cargo(C), needs(D, C).
valid(D, C, H) :- destination(D), cargo(C), hazard(H), matches_need(D, C).

% --- sensible supports -----------------------------------------------------
sensible(S) :- support(S), sense(S, V), sense_min(M), V >= M.

% --- outcome model ---------------------------------------------------------
protected :- chosen_support(S), chosen_hazard(H), covers(S, H), power(S, P), severity(H, V), P >= V.
outcome(safe) :- protected.
outcome(late) :- not protected.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for dest_id, dest in DESTINATIONS.items():
        lines.append(asp.fact("destination", dest_id))
        lines.append(asp.fact("needs", dest_id, dest.need))
    for cargo_id in CARGOES:
        lines.append(asp.fact("cargo", cargo_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("severity", hazard_id, hazard.severity))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("sense", support_id, support.sense))
        lines.append(asp.fact("power", support_id, support.power))
        for hazard_id in sorted(support.covers):
            lines.append(asp.fact("covers", support_id, hazard_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(s for (s,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_support", params.support),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "welfare" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story did not include 'welfare'.")
    _ = format_qa(sample)


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {s.id for s in sensible_supports()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible supports match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible supports:")
        print("  clingo:", sorted(clingo_sensible))
        print("  python:", sorted(python_sensible))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated a normal story successfully.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a small welfare space adventure with a surprise tool and a careful-delivery lesson."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (destination, cargo, hazard) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.destination and args.cargo:
        destination = DESTINATIONS[args.destination]
        cargo = CARGOES[args.cargo]
        if not cargo_matches(args.destination, args.cargo):
            raise StoryError(explain_cargo(destination, cargo))
    if args.support and SUPPORTS[args.support].sense < SENSE_MIN:
        raise StoryError(explain_support(args.support))

    combos = [
        combo for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination_id, cargo_id, hazard_id = rng.choice(sorted(combos))
    support_id = args.support or rng.choice(sorted(s.id for s in sensible_supports()))
    hero, hero_gender = _pick_name(rng)
    friend, friend_gender = _pick_name(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        destination=destination_id,
        cargo=cargo_id,
        hazard=hazard_id,
        support=support_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        hero_trait=rng.choice(TRAITS),
        friend_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")
    if not cargo_matches(params.destination, params.cargo):
        raise StoryError(explain_cargo(DESTINATIONS[params.destination], CARGOES[params.cargo]))
    if SUPPORTS[params.support].sense < SENSE_MIN:
        raise StoryError(explain_support(params.support))

    world = tell(
        destination=DESTINATIONS[params.destination],
        cargo=CARGOES[params.cargo],
        hazard=HAZARDS[params.hazard],
        support=SUPPORTS[params.support],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace(" hero ", f" {params.hero} ").replace(" friend ", f" {params.friend} "),
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
        combos = asp_valid_combos()
        print(f"sensible supports: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (destination, cargo, hazard) combos:\n")
        for destination, cargo, hazard in combos:
            print(f"  {destination:14} {cargo:12} {hazard}")
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
            header = (
                f"### {p.hero} & {p.friend}: {p.destination} / {p.cargo} / "
                f"{p.hazard} / {p.support} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
