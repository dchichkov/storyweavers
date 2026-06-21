#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ful_arrow_bound_mystery_to_solve_twist.py
===================================================================

A small superhero storyworld about a missing treasure, a misleading clue, and a
kind twist. A young hero must solve a mystery: a glowing object vanishes before
a town celebration, an arrow points toward the wrong suspect, and a scrap
marked "ful" seems to prove guilt. But the hero learns that clues can mislead,
someone is literally bound and needs help, and fairness matters more than fast
blame.

Run it
------
    python storyworlds/worlds/gpt-5.4/ful_arrow_bound_mystery_to_solve_twist.py
    python storyworlds/worlds/gpt-5.4/ful_arrow_bound_mystery_to_solve_twist.py --place library
    python storyworlds/worlds/gpt-5.4/ful_arrow_bound_mystery_to_solve_twist.py --hazard wind --trap vines
    python storyworlds/worlds/gpt-5.4/ful_arrow_bound_mystery_to_solve_twist.py --all
    python storyworlds/worlds/gpt-5.4/ful_arrow_bound_mystery_to_solve_twist.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ful_arrow_bound_mystery_to_solve_twist.py --trace
    python storyworlds/worlds/gpt-5.4/ful_arrow_bound_mystery_to_solve_twist.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    opening: str
    safe_spot: str
    hazards: set[str] = field(default_factory=set)
    traps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    glow: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    sign: str
    move_reason: str
    safe_place_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trap:
    id: str
    label: str
    phrase: str
    verb: str
    rescue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectRole:
    id: str
    label: str
    phrase: str
    helpful_job: str
    badge: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_bound_alarm(world: World) -> list[str]:
    suspect = world.entities.get("suspect")
    hero = world.entities.get("hero")
    if not suspect or not hero:
        return []
    if suspect.meters["bound"] < THRESHOLD:
        return []
    sig = ("bound_alarm", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["urgency"] += 1
    suspect.memes["fear"] += 1
    return []


def _r_item_danger(world: World) -> list[str]:
    item = world.entities.get("item")
    drone = world.entities.get("drone")
    if not item or not drone:
        return []
    if item.meters["threatened"] < THRESHOLD:
        return []
    sig = ("item_danger", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    drone.memes["duty"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="bound_alarm", tag="social", apply=_r_bound_alarm),
    Rule(name="item_danger", tag="physical", apply=_r_item_danger),
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
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "library": Place(
        id="library",
        label="library",
        phrase="the tall glass library",
        opening="The city library rose like a silver tower above the street.",
        safe_spot="the dry map drawer in the reading room",
        hazards={"rain", "sparks"},
        traps={"ribbon", "cord"},
        tags={"library"},
    ),
    "museum": Place(
        id="museum",
        label="museum",
        phrase="the moon museum",
        opening="The moon museum shone with polished floors and bright banners.",
        safe_spot="the stone display chest by the front hall",
        hazards={"wind", "sparks"},
        traps={"ribbon", "vines"},
        tags={"museum"},
    ),
    "garden": Place(
        id="garden",
        label="garden",
        phrase="the rooftop garden",
        opening="The rooftop garden fluttered with flags above the busy town.",
        safe_spot="the little tool shed under the awning",
        hazards={"rain", "wind"},
        traps={"vines", "cord"},
        tags={"garden"},
    ),
}

ITEMS = {
    "star_arrow": MissingItem(
        id="star_arrow",
        label="Star Arrow",
        phrase="the Star Arrow",
        glow="glowed blue like a tiny comet",
        purpose="to start the evening hero parade",
        tags={"arrow", "festival"},
    ),
    "sun_badge": MissingItem(
        id="sun_badge",
        label="Sun Badge",
        phrase="the Sun Badge",
        glow="shone gold like a small morning sun",
        purpose="to light the celebration stage",
        tags={"badge", "festival"},
    ),
    "sky_orb": MissingItem(
        id="sky_orb",
        label="Sky Orb",
        phrase="the Sky Orb",
        glow="hummed with a soft silver light",
        purpose="to power the music for the town cheer",
        tags={"orb", "festival"},
    ),
}

HAZARDS = {
    "rain": Hazard(
        id="rain",
        label="rain leak",
        sign="a trail of raindrops on the floor",
        move_reason="a leak had started dripping from the ceiling right above the display",
        safe_place_line="The safest dry place was nearby, away from the leak.",
        tags={"rain", "safety"},
    ),
    "wind": Hazard(
        id="wind",
        label="wild vent wind",
        sign="papers flapping near a rattling vent",
        move_reason="a gust from a loud vent could have knocked the treasure down",
        safe_place_line="The safest heavy place was nearby, where the wind could not push it.",
        tags={"wind", "safety"},
    ),
    "sparks": Hazard(
        id="sparks",
        label="tiny sparks",
        sign="a blinking repair panel and a sharp zzt sound",
        move_reason="tiny sparks had begun to jump from a loose repair panel beside the display",
        safe_place_line="The safest place was the cool box kept away from the sparks.",
        tags={"electric", "safety"},
    ),
}

TRAPS = {
    "ribbon": Trap(
        id="ribbon",
        label="ribbon",
        phrase="a knot of parade ribbon",
        verb="ribbon had wound around",
        rescue="untangled the ribbon with quick careful fingers",
        tags={"bound"},
    ),
    "cord": Trap(
        id="cord",
        label="cord",
        phrase="a loop of stage cord",
        verb="cord had wrapped around",
        rescue="loosened the cord and slipped it free",
        tags={"bound"},
    ),
    "vines": Trap(
        id="vines",
        label="vines",
        phrase="a curl of climbing vines",
        verb="vines had twisted around",
        rescue="lifted the vines away one green loop at a time",
        tags={"bound"},
    ),
}

SUSPECTS = {
    "caretaker": SuspectRole(
        id="caretaker",
        label="caretaker",
        phrase="the night caretaker",
        helpful_job="checked doors and fixed little problems before big crowds arrived",
        badge="HELPFUL HELPER",
        tags={"helper"},
    ),
    "gardener": SuspectRole(
        id="gardener",
        label="gardener",
        phrase="the rooftop gardener",
        helpful_job="watered plants and tied bright festival ribbons where children could see them",
        badge="HELPFUL GROWER",
        tags={"helper"},
    ),
    "guide": SuspectRole(
        id="guide",
        label="guide",
        phrase="the museum guide",
        helpful_job="showed visitors where to go and kept treasures behind the safety line",
        badge="HELPFUL GUIDE",
        tags={"helper"},
    ),
}

GIRL_NAMES = ["Luna", "Maya", "Zoe", "Ivy", "Nora", "Ava"]
BOY_NAMES = ["Kai", "Leo", "Max", "Finn", "Eli", "Noah"]
SIDEKICK_NAMES = ["Pip", "Sparky", "Glim", "Dot", "Flash", "Pebble"]


@dataclass
class StoryParams:
    place: str
    item: str
    hazard: str
    trap: str
    suspect: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    parent_type: str
    seed: Optional[int] = None


def hazard_fits(place_id: str, hazard_id: str) -> bool:
    return hazard_id in PLACES[place_id].hazards


def trap_fits(place_id: str, trap_id: str) -> bool:
    return trap_id in PLACES[place_id].traps


def suspect_fits(place_id: str, suspect_id: str) -> bool:
    if place_id == "library":
        return suspect_id == "caretaker"
    if place_id == "museum":
        return suspect_id in {"guide", "caretaker"}
    if place_id == "garden":
        return suspect_id in {"gardener", "caretaker"}
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for item_id in sorted(ITEMS):
            for hazard_id in sorted(HAZARDS):
                for trap_id in sorted(TRAPS):
                    for suspect_id in sorted(SUSPECTS):
                        if hazard_fits(place_id, hazard_id) and trap_fits(place_id, trap_id) and suspect_fits(place_id, suspect_id):
                            combos.append((place_id, item_id, hazard_id, trap_id, suspect_id))
    return combos


def explain_rejection(place_id: str, hazard_id: Optional[str], trap_id: Optional[str], suspect_id: Optional[str]) -> str:
    if hazard_id and not hazard_fits(place_id, hazard_id):
        return f"(No story: {PLACES[place_id].label} does not have the right setup for the hazard '{hazard_id}'.)"
    if trap_id and not trap_fits(place_id, trap_id):
        return f"(No story: {PLACES[place_id].label} does not plausibly contain the trap '{trap_id}'.)"
    if suspect_id and not suspect_fits(place_id, suspect_id):
        return f"(No story: the suspect '{suspect_id}' does not fit the setting '{place_id}'.)"
    return "(No valid combination matches the given options.)"


def _pick_name(rng: random.Random) -> tuple[str, str]:
    hero_type = rng.choice(["girl", "boy"])
    if hero_type == "girl":
        return rng.choice(GIRL_NAMES), hero_type
    return rng.choice(BOY_NAMES), hero_type


def _pick_sidekick(rng: random.Random, avoid: str) -> tuple[str, str]:
    pool = [n for n in SIDEKICK_NAMES if n != avoid]
    sidekick_type = rng.choice(["girl", "boy"])
    return rng.choice(pool), sidekick_type


def intro(world: World, hero: Entity, sidekick: Entity, place: Place, item: MissingItem) -> None:
    hero.memes["brave"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"{place.opening} On Hero Day, {hero.id} and {sidekick.id} hurried there in their capes."
    )
    world.say(
        f"{hero.id} was the kind of small superhero who looked for trouble to fix before anyone had to cry."
    )
    world.say(
        f"Inside, everyone had come to see {item.phrase}, which {item.glow} and was needed {item.purpose}."
    )


def mystery_starts(world: World, hero: Entity, sidekick: Entity, item_ent: Entity, suspect: Entity) -> None:
    item_ent.meters["missing"] += 1
    hero.memes["curious"] += 1
    world.say(
        f"But when the curtain was pulled back, the stand was empty. {item_ent.label} was gone."
    )
    world.say(
        f'{sidekick.id} gasped. "{item_ent.label}! Who took it?"'
    )
    world.say(
        f"On the floor, {hero.id} saw a chalk arrow and a tiny paper scrap with only one word part on it: ful."
    )
    world.say(
        f"The scrap made {hero.id} think of {suspect.attrs['badge']}, because that big badge had the letters ful at the end."
    )


def predict_truth(world: World) -> dict:
    sim = world.copy()
    item = sim.get("item")
    suspect = sim.get("suspect")
    item.meters["threatened"] += 1
    suspect.meters["bound"] += 1
    propagate(sim, narrate=False)
    return {
        "item_danger": item.meters["threatened"],
        "suspect_bound": suspect.meters["bound"],
        "hero_urgency": sim.get("hero").memes["urgency"],
    }


def investigate(world: World, hero: Entity, sidekick: Entity, suspect: Entity, hazard: Hazard, trap: Trap) -> None:
    clue = predict_truth(world)
    world.facts["predicted_urgency"] = clue["hero_urgency"]
    world.say(
        f"{hero.id} followed the arrow with {sidekick.id} close behind. {hazard.sign} pointed the same way."
    )
    world.say(
        f"At first that only made {suspect.phrase} seem guiltier, and {hero.id} felt a quick hot jump of suspicion."
    )
    suspect.meters["bound"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then they heard a muffled call for help from behind some crates. {suspect.phrase} was there, and {trap.phrase} {trap.verb} {suspect.pronoun('object')}."
    )


def rescue(world: World, hero: Entity, suspect: Entity, trap: Trap) -> None:
    suspect.meters["bound"] = 0.0
    suspect.memes["relief"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.id} did not stop to blame. {hero.pronoun().capitalize()} {trap.rescue} and helped {suspect.pronoun('object')} stand."
    )


def reveal_twist(world: World, hero: Entity, suspect: Entity, item_ent: Entity, place: Place, hazard: Hazard) -> None:
    item_ent.meters["threatened"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I did not steal {item_ent.label}," {suspect.phrase} said. "I drew the arrow so someone would follow me."'
    )
    world.say(
        f'"The scrap came off my {suspect.attrs["badge"]} badge while I was running. {hazard.move_reason}."'
    )
    world.say(
        f'"The little safety drone saw the danger first and carried {item_ent.label} to {place.safe_spot}. I chased it, tripped, and got bound before I could explain."'
    )
    world.facts["twist"] = "suspect_innocent"


def recover_item(world: World, hero: Entity, sidekick: Entity, item_ent: Entity, place: Place, hazard: Hazard) -> None:
    drone = world.get("drone")
    item_ent.meters["hidden_safe"] += 1
    item_ent.meters["missing"] = 0.0
    hero.memes["understanding"] += 1
    sidekick.memes["relief"] += 1
    drone.memes["duty"] += 1
    world.say(
        f"Now the mystery turned upside down. The arrow was not a thief mark. It was a helper mark."
    )
    world.say(
        f"{hero.id}, {sidekick.id}, and the freed helper hurried to {place.safe_spot}."
    )
    world.say(
        f"There sat the tiny safety drone beside {item_ent.phrase}, blinking as if to say it had only tried to protect it. {hazard.safe_place_line}"
    )


def ending(world: World, hero: Entity, sidekick: Entity, suspect: Entity, item_ent: Entity) -> None:
    hero.memes["apology"] += 1
    hero.memes["joy"] += 1
    suspect.memes["forgiven"] += 1
    world.say(
        f'{hero.id} lifted {item_ent.phrase} high. "Mystery solved!" {hero.pronoun()} cried.'
    )
    world.say(
        f"Before the cheering started, {hero.id} turned to {suspect.phrase}. "
        f'"I am sorry I guessed before I knew the truth," {hero.pronoun()} said.'
    )
    world.say(
        f'{suspect.phrase.capitalize()} smiled. "A real hero looks twice and helps first."'
    )
    world.say(
        f"That night {item_ent.phrase} shone above the celebration, and {hero.id} remembered the best superpower of all was being fair."
    )
    world.facts["moral"] = "be_fair_help_first"


def tell(
    place: Place,
    item: MissingItem,
    hazard: Hazard,
    trap: Trap,
    suspect_cfg: SuspectRole,
    hero_name: str,
    hero_type: str,
    sidekick_name: str,
    sidekick_type: str,
    parent_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, phrase=hero_name, role="hero"))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=sidekick_type, label=sidekick_name, phrase=sidekick_name, role="sidekick"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", phrase="the parent", role="adult"))
    suspect = world.add(
        Entity(
            id="suspect",
            kind="character",
            type="person",
            label=suspect_cfg.label,
            phrase=suspect_cfg.phrase,
            role="helper",
            attrs={"badge": suspect_cfg.badge},
            tags=set(suspect_cfg.tags),
        )
    )
    item_ent = world.add(
        Entity(
            id="item",
            kind="thing",
            type="treasure",
            label=item.label,
            phrase=item.phrase,
            role="item",
            tags=set(item.tags),
        )
    )
    drone = world.add(Entity(id="drone", kind="thing", type="drone", label="safety drone", phrase="the little safety drone", role="drone"))
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        suspect=suspect,
        place=place,
        item_cfg=item,
        item=item_ent,
        hazard=hazard,
        trap=trap,
        suspect_cfg=suspect_cfg,
    )

    intro(world, hero, sidekick, place, item)
    world.para()
    mystery_starts(world, hero, sidekick, item_ent, suspect)
    investigate(world, hero, sidekick, suspect, hazard, trap)
    world.para()
    rescue(world, hero, suspect, trap)
    reveal_twist(world, hero, suspect, item_ent, place, hazard)
    world.para()
    recover_item(world, hero, sidekick, item_ent, place, hazard)
    ending(world, hero, sidekick, suspect, item_ent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    item = f["item_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old set at {place.phrase}, with a missing treasure mystery to solve.',
        f'Include the words "ful", "arrow", and "bound", and make the clues point the hero the wrong way before a kind twist.',
        f"Tell a gentle mystery where {hero.label} learns that being fair and helping first is a hero's best power.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    suspect = f["suspect"]
    item = f["item"]
    place = f["place"]
    hazard = f["hazard"]
    trap = f["trap"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a young superhero named {hero.label}, {hero.pronoun('possessive')} friend {sidekick.label}, and {suspect.phrase} at {place.phrase}. They work together to find {item.phrase}.",
        ),
        (
            f"What mystery did {hero.label} have to solve?",
            f"{hero.label} had to solve the mystery of why {item.phrase} had vanished before the celebration. The empty stand and the strange clues made it look like someone had taken it.",
        ),
        (
            "What clues did they find first?",
            f"They found a chalk arrow and a little paper scrap that said ful. Those clues seemed to point at the helper's HELPFUL badge, so the hero guessed the wrong thing at first.",
        ),
        (
            f"Why did {hero.label} stop blaming and start helping?",
            f"{hero.label} found {suspect.phrase} bound in {trap.label}, so helping mattered more than guessing. Rescue came first because someone was in trouble right then.",
        ),
        (
            "What was the twist?",
            f"The helper was innocent. The arrow had been a guide mark, and the scrap with ful had fallen from the helper's badge while the helper was trying to warn everyone.",
        ),
        (
            f"Why had {item.phrase} been moved?",
            f"It had been moved for safety because {hazard.move_reason}. The little safety drone carried it to a safer place instead of letting it stay in danger.",
        ),
        (
            "What lesson did the hero learn?",
            f"{hero.label} learned not to blame people before knowing the whole truth. {hero.pronoun().capitalize()} also learned that helping first is part of being a real hero.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "arrow": [
        (
            "What can an arrow sign do?",
            "An arrow sign can point the way somewhere. It helps people know where to go or what to notice.",
        )
    ],
    "bound": [
        (
            "What does bound mean?",
            "Bound means tied up or held so you cannot move easily. A bound person needs help to get free.",
        )
    ],
    "rain": [
        (
            "Why should you move things away from a leak?",
            "Water from a leak can drip onto important things and ruin them. Moving them to a dry place keeps them safe.",
        )
    ],
    "wind": [
        (
            "Why can strong wind be a problem indoors?",
            "Strong wind can blow papers and light objects around. It can also knock something off a stand if it is not safe.",
        )
    ],
    "electric": [
        (
            "Why are sparks dangerous?",
            "Sparks can burn things and start bigger trouble. Grown-ups should fix spark problems right away.",
        )
    ],
    "safety": [
        (
            "Why is it smart to check facts before blaming someone?",
            "Sometimes clues can trick you or only show part of the truth. Checking facts helps you be fair and kind.",
        )
    ],
    "helper": [
        (
            "What does a helper do?",
            "A helper looks after people or places and tries to solve problems. Helpers often do quiet jobs that keep everyone safe.",
        )
    ],
}

KNOWLEDGE_ORDER = ["arrow", "bound", "rain", "wind", "electric", "safety", "helper"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["item_cfg"].tags) | set(f["hazard"].tags) | set(f["trap"].tags) | set(f["suspect_cfg"].tags)
    tags.add("safety")
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="library",
        item="star_arrow",
        hazard="rain",
        trap="ribbon",
        suspect="caretaker",
        hero_name="Luna",
        hero_type="girl",
        sidekick_name="Pip",
        sidekick_type="boy",
        parent_type="mother",
    ),
    StoryParams(
        place="museum",
        item="sun_badge",
        hazard="wind",
        trap="vines",
        suspect="guide",
        hero_name="Max",
        hero_type="boy",
        sidekick_name="Dot",
        sidekick_type="girl",
        parent_type="father",
    ),
    StoryParams(
        place="garden",
        item="sky_orb",
        hazard="wind",
        trap="cord",
        suspect="gardener",
        hero_name="Ivy",
        hero_type="girl",
        sidekick_name="Flash",
        sidekick_type="boy",
        parent_type="mother",
    ),
]


ASP_RULES = r"""
valid(P, I, H, T, S) :- place(P), item(I), hazard(H), trap(T), suspect(S),
                        allows_hazard(P, H), allows_trap(P, T), allows_suspect(P, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hazard_id in sorted(place.hazards):
            lines.append(asp.fact("allows_hazard", place_id, hazard_id))
        for trap_id in sorted(place.traps):
            lines.append(asp.fact("allows_trap", place_id, trap_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for hazard_id in HAZARDS:
        lines.append(asp.fact("hazard", hazard_id))
    for trap_id in TRAPS:
        lines.append(asp.fact("trap", trap_id))
    for suspect_id in SUSPECTS:
        lines.append(asp.fact("suspect", suspect_id))
    for place_id in PLACES:
        for suspect_id in SUSPECTS:
            if suspect_fits(place_id, suspect_id):
                lines.append(asp.fact("allows_suspect", place_id, suspect_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gates:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "ful" not in sample.story or "arrow" not in sample.story or "bound" not in sample.story:
            raise StoryError("Smoke test story did not render the required seed words.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story:
            raise StoryError("Random smoke test generated an empty story.")
        print("OK: random generate() smoke test succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero mystery storyworld with a misleading clue, a bound helper, and a kind twist."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--trap", choices=sorted(TRAPS))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place:
        if args.hazard and not hazard_fits(args.place, args.hazard):
            raise StoryError(explain_rejection(args.place, args.hazard, None, None))
        if args.trap and not trap_fits(args.place, args.trap):
            raise StoryError(explain_rejection(args.place, None, args.trap, None))
        if args.suspect and not suspect_fits(args.place, args.suspect):
            raise StoryError(explain_rejection(args.place, None, None, args.suspect))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.hazard is None or combo[2] == args.hazard)
        and (args.trap is None or combo[3] == args.trap)
        and (args.suspect is None or combo[4] == args.suspect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, hazard_id, trap_id, suspect_id = rng.choice(sorted(combos))
    hero_name, hero_type = _pick_name(rng)
    sidekick_name, sidekick_type = _pick_sidekick(rng, hero_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        item=item_id,
        hazard=hazard_id,
        trap=trap_id,
        suspect=suspect_id,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        item = ITEMS[params.item]
        hazard = HAZARDS[params.hazard]
        trap = TRAPS[params.trap]
        suspect_cfg = SUSPECTS[params.suspect]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not hazard_fits(params.place, params.hazard):
        raise StoryError(explain_rejection(params.place, params.hazard, None, None))
    if not trap_fits(params.place, params.trap):
        raise StoryError(explain_rejection(params.place, None, params.trap, None))
    if not suspect_fits(params.place, params.suspect):
        raise StoryError(explain_rejection(params.place, None, None, params.suspect))

    world = tell(
        place=place,
        item=item,
        hazard=hazard,
        trap=trap,
        suspect_cfg=suspect_cfg,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        sidekick_name=params.sidekick_name,
        sidekick_type=params.sidekick_type,
        parent_type=params.parent_type,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, item, hazard, trap, suspect) combos:\n")
        for place_id, item_id, hazard_id, trap_id, suspect_id in combos:
            print(f"  {place_id:8} {item_id:10} {hazard_id:7} {trap_id:6} {suspect_id}")
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
            header = f"### {p.hero_name}: {p.item} at {p.place} ({p.hazard}, {p.trap})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
