#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/underoos_flashback_space_adventure.py
===============================================================

A standalone story world about a child who wants to go on a dramatic pretend
spacewalk wearing only underoos as a "space suit." The world model keeps that
wish honest: some places are chilly, wet, scratchy, or windy, so a calm grown-up
has a real reason to stop the launch and offer proper gear. The turn is a
flashback. The child remembers what happened the last time a rushed mission met
cold toes or scratched knees, and that memory changes the decision.

Run it
------
    python storyworlds/worlds/gpt-5.4/underoos_flashback_space_adventure.py
    python storyworlds/worlds/gpt-5.4/underoos_flashback_space_adventure.py --place backyard
    python storyworlds/worlds/gpt-5.4/underoos_flashback_space_adventure.py --place hallway
    python storyworlds/worlds/gpt-5.4/underoos_flashback_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/underoos_flashback_space_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/underoos_flashback_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/underoos_flashback_space_adventure.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "memory" | "place"
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    phrase: str
    outdoor: bool = True
    sky: str = ""
    ground: str = ""
    hazards: set[str] = field(default_factory=set)
    missions: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    title: str
    goal: str
    beacon: str
    path: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    score: int = 0
    prep: str = ""
    action: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mission: str
    hero: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "backyard": Place(
        id="backyard",
        label="backyard",
        phrase="the backyard",
        outdoor=True,
        sky="the evening sky looked deep and blue, with the first stars peeking out",
        ground="the grass held cool dew",
        hazards={"cold", "wet"},
        missions={"beacon", "moon_rocks"},
        tags={"cold", "wet", "yard"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the front porch",
        outdoor=True,
        sky="the porch light made a little moon of its own beside the dark street",
        ground="the wooden boards were chilly and rough",
        hazards={"cold", "splinters"},
        missions={"beacon", "satellite"},
        tags={"cold", "splinters", "porch"},
    ),
    "garden": Place(
        id="garden",
        label="garden",
        phrase="the garden path",
        outdoor=True,
        sky="the sky above the flowers looked wide enough for a thousand rockets",
        ground="the little stones beside the flowers felt sharp under small feet",
        hazards={"cold", "scratches"},
        missions={"moon_rocks", "satellite"},
        tags={"cold", "scratches", "garden"},
    ),
    "balcony": Place(
        id="balcony",
        label="balcony",
        phrase="the balcony",
        outdoor=True,
        sky="the high air hummed softly around the railing as if space itself were breathing",
        ground="the floor was smooth, but the evening wind slipped everywhere",
        hazards={"cold", "wind"},
        missions={"beacon", "satellite"},
        tags={"cold", "wind", "balcony"},
    ),
    # Decoy invalid option: no outdoor exposure means no honest warning/fix story.
    "hallway": Place(
        id="hallway",
        label="hallway",
        phrase="the hallway",
        outdoor=False,
        sky="",
        ground="the rug felt warm",
        hazards=set(),
        missions={"beacon"},
        tags={"indoors"},
    ),
}

MISSIONS = {
    "beacon": Mission(
        id="beacon",
        title="Beacon Rescue",
        goal="reach the blinking rescue beacon by the flowerpot planet",
        beacon="a blinking rescue beacon beside the flowerpot planet",
        path="across the launch ramp and past the sleeping comet umbrella stand",
        ending="planted one hand on the beacon and gave a triumphant captain nod",
        tags={"beacon", "rescue"},
    ),
    "moon_rocks": Mission(
        id="moon_rocks",
        title="Moon Rock Hunt",
        goal="collect the silver moon rocks by the stepping-stone crater",
        beacon="a basket of silver moon rocks by the stepping-stone crater",
        path="over the dark grass sea and around the tomato-cage antenna",
        ending="held the moon rocks high so they flashed like treasure from another world",
        tags={"rocks", "explore"},
    ),
    "satellite": Mission(
        id="satellite",
        title="Satellite Fix",
        goal="tighten the tiny satellite dish taped to the chair rocket",
        beacon="a wobbling satellite dish taped to the chair rocket",
        path="along the star bridge and around the potted fern nebula",
        ending="gave the satellite a careful tap until it pointed proudly at the stars",
        tags={"satellite", "repair"},
    ),
}

GEAR = {
    "moon_boots": Gear(
        id="moon_boots",
        label="moon boots",
        phrase="fuzzy moon boots",
        guards={"cold", "wet", "splinters", "scratches"},
        score=3,
        prep="slid fuzzy moon boots onto the little astronaut's feet",
        action="with warm feet and safe steps",
        tags={"boots"},
    ),
    "comet_suit": Gear(
        id="comet_suit",
        label="comet suit",
        phrase="a soft comet suit",
        guards={"cold", "wind", "scratches"},
        score=3,
        prep="helped the little astronaut step into a soft comet suit over the underoos",
        action="with sleeves hugging close and knees covered",
        tags={"suit"},
    ),
    "rain_shell": Gear(
        id="rain_shell",
        label="rain shell",
        phrase="a shiny rain shell and boots",
        guards={"cold", "wet", "wind"},
        score=4,
        prep="zipped a shiny rain shell over the underoos and added boots",
        action="with dry legs and brave little boot-steps",
        tags={"rain_shell", "boots"},
    ),
    "star_layers": Gear(
        id="star_layers",
        label="star layers",
        phrase="starry play clothes and slippers",
        guards={"cold", "wet", "splinters", "scratches", "wind"},
        score=5,
        prep="layered starry play clothes over the underoos and tucked on sturdy slippers",
        action="with every part of the space suit ready for the world outside",
        tags={"layers", "slippers"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Ava", "Nora", "Ellie", "Ruby", "Tara"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Sam", "Noah", "Eli", "Ben"]
TRAITS = ["brave", "curious", "bouncy", "careful", "sparky", "eager"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_exposed_discomfort(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    place = world.entities.get("place")
    if not hero or not place:
        return out
    if hero.meters["outside"] < THRESHOLD:
        return out
    if hero.meters["protected"] >= THRESHOLD:
        return out
    for hazard in sorted(place.attrs.get("hazards", set())):
        sig = ("exposed", hazard)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["discomfort"] += 1
        hero.meters[hazard] += 1
        hero.memes["alarm"] += 1
        out.append("__ouch__")
    return out


def _r_memory_caution(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    memory = world.entities.get("memory")
    if not hero or not memory:
        return out
    if memory.memes["active"] < THRESHOLD:
        return out
    sig = ("memory_caution", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["caution"] += 1
    hero.memes["wisdom"] += 1
    out.append("__flashback__")
    return out


def _r_suited_confidence(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["protected"] < THRESHOLD:
        return out
    sig = ("suited", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    hero.memes["joy"] += 1
    out.append("__ready__")
    return out


CAUSAL_RULES = [
    Rule(name="exposed_discomfort", tag="physical", apply=_r_exposed_discomfort),
    Rule(name="memory_caution", tag="memory", apply=_r_memory_caution),
    Rule(name="suited_confidence", tag="emotion", apply=_r_suited_confidence),
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
    return [s for s in produced if narrate]


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def place_is_risky(place: Place) -> bool:
    return place.outdoor and bool(place.hazards)


def choose_gear(place: Place) -> Optional[Gear]:
    options = [
        gear for gear in GEAR.values()
        if place.hazards.issubset(gear.guards)
    ]
    if not options:
        return None
    return max(sorted(options, key=lambda g: g.id), key=lambda g: g.score)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        if not place_is_risky(place):
            continue
        if choose_gear(place) is None:
            continue
        for mission_id in sorted(place.missions):
            combos.append((place_id, mission_id))
    return sorted(combos)


def explain_rejection(place: Place) -> str:
    if not place.outdoor:
        return (
            f"(No story: {place.phrase} is indoors, so running out there in underoos "
            f"does not create the chilly, wet, windy, or scratchy problem this world "
            f"needs. Pick an outdoor place with a real spacewalk risk.)"
        )
    if not place.hazards:
        return (
            f"(No story: {place.phrase} has no outdoor hazard here, so the grown-up "
            f"has no honest reason to stop the launch.)"
        )
    return (
        f"(No story: nothing in the gear catalog safely covers the hazards at "
        f"{place.phrase}.)"
    )


# ---------------------------------------------------------------------------
# Prediction and flashback
# ---------------------------------------------------------------------------
def predict_mission(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["outside"] += 1
    propagate(sim, narrate=False)
    place = sim.get("place")
    discomfort = hero.meters["discomfort"]
    return {
        "discomfort": discomfort,
        "hazards": sorted(place.attrs.get("hazards", set())),
    }


def memory_line(place: Place) -> str:
    haz = place.hazards
    if "wet" in haz:
        return "the last rushed launch, when cold dew kissed between the toes and made the brave marching stop at once"
    if "splinters" in haz:
        return "the last dash onto rough boards, when a tiny sting in one foot ended the mission before it began"
    if "scratches" in haz:
        return "the last garden landing, when a prickly stem brushed bare knees and turned a roar into a yelp"
    if "wind" in haz:
        return "the last windy countdown, when the evening breeze wrapped around bare arms and made the little astronaut shiver"
    return "the last mission that felt too cold and too quick"


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, mission: Mission) -> None:
    trait = hero.traits[0] if hero.traits else "bright"
    world.say(
        f"{hero.id} was a {trait} little {hero.type} who could turn an ordinary evening "
        f"into {mission.title}. Tonight the silver-star underoos felt, to {hero.pronoun('object')}, "
        f"like the most important space suit in the whole galaxy."
    )


def stage_space(world: World, hero: Entity, place: Place, mission: Mission) -> None:
    hero.memes["imagination"] += 1
    world.say(
        f"In {hero.pronoun('possessive')} mind, {place.phrase} was no longer just home. "
        f"It was a launch world, and {place.sky}."
    )
    world.say(
        f"The mission was to {mission.goal}. The path would lead {mission.path}."
    )


def urge_launch(world: World, hero: Entity, parent: Entity, place: Place) -> None:
    hero.memes["desire"] += 1
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} bounced to the door in the underoos and spread {hero.pronoun("possessive")} arms. '
        f'"Astronaut ready!" {hero.pronoun()} announced.'
    )
    world.say(
        f"But {hero.pronoun('possessive')} {parent.label_word} looked past the little captain to {place.ground}."
    )


def warn(world: World, hero: Entity, parent: Entity, place: Place) -> None:
    pred = predict_mission(world)
    world.facts["predicted_discomfort"] = pred["discomfort"]
    world.facts["predicted_hazards"] = list(pred["hazards"])
    hazards = pred["hazards"]
    if hazards == ["cold", "splinters"]:
        line = "Those boards are cold and rough. Bare feet can get hurt there."
    elif hazards == ["cold", "wet"]:
        line = "The grass is cold and wet. Underoos are brave, but they are not moon boots."
    elif hazards == ["cold", "scratches"]:
        line = "The stones and stems out there are cold and scratchy on bare knees and feet."
    elif hazards == ["cold", "wind"]:
        line = "The wind out there is sneaky and cold. It can nibble right through a tiny outfit."
    else:
        line = "Outside can feel much bigger and rougher than a game expects."
    world.say(
        f'"Hold your rockets a minute," {parent.label_word.capitalize()} said softly. "{line}"'
    )


def trigger_flashback(world: World, hero: Entity, place: Place) -> None:
    memory = world.get("memory")
    memory.memes["active"] += 1
    propagate(world, narrate=False)
    hero.memes["remembering"] += 1
    world.say(
        f"Then a flashback blinked inside {hero.id}'s mind: {memory_line(place)}."
    )
    world.say(
        f"{hero.id} stopped with one hand on the doorknob. The pretend stars were still shining, "
        f"but now {hero.pronoun()} remembered the real world too."
    )


def reconsider(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["defiance"] = 0.0
    hero.memes["trust"] += 1
    world.say(
        f'"I want the mission," {hero.id} said, smaller now, "just not the stingy part."'
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled and knelt down. "That is exactly what a smart captain says."'
    )


def suit_up(world: World, hero: Entity, parent: Entity, gear: Gear) -> None:
    suit = world.add(Entity(
        id="gear",
        kind="thing",
        type="gear",
        label=gear.label,
        phrase=gear.phrase,
        attrs={"guards": set(gear.guards)},
        tags=set(gear.tags),
    ))
    hero.meters["protected"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they got the launch right. {parent.label_word.capitalize()} {gear.prep}."
    )
    world.say(
        f"The underoos did not disappear. They became the secret first layer of the suit, hidden under all that astronaut glory."
    )
    world.facts["gear_entity"] = suit


def launch(world: World, hero: Entity, mission: Mission, gear: Gear, place: Place) -> None:
    hero.meters["outside"] += 1
    propagate(world, narrate=False)
    hero.memes["joy"] += 1
    world.say(
        f"Out went the little astronaut, {gear.action}, and suddenly {place.phrase} really did feel like another planet."
    )
    world.say(
        f"{hero.id} crossed the dark frontier, reached {mission.beacon}, and {mission.ending}."
    )


def resolve(world: World, hero: Entity, parent: Entity, gear: Gear) -> None:
    hero.memes["love"] += 1
    hero.memes["relief"] += 1
    world.say(
        f'When the mission was done, {hero.id} looked down at the sturdy suit and grinned. '
        f'"Best launch yet," {hero.pronoun()} said.'
    )
    world.say(
        f"{parent.label_word.capitalize()} squeezed {hero.pronoun('possessive')} shoulder. "
        f'"Space adventures work better when brave ideas wear proper layers."'
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(place: Place, mission: Mission, gear: Gear,
         hero_name: str = "Luna", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        traits=[trait],
        role="hero",
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    world.add(Entity(
        id="place",
        kind="place",
        type="place",
        label=place.label,
        phrase=place.phrase,
        attrs={"hazards": set(place.hazards)},
        tags=set(place.tags),
    ))
    world.add(Entity(
        id="memory",
        kind="memory",
        type="memory",
        label="the flashback",
        attrs={"hazards": set(place.hazards)},
    ))

    world.facts["hero_name"] = hero_name
    world.facts["place_cfg"] = place
    world.facts["mission_cfg"] = mission
    world.facts["gear_cfg"] = gear

    introduce(world, hero, mission)
    stage_space(world, hero, place, mission)

    world.para()
    urge_launch(world, hero, parent, place)
    warn(world, hero, parent, place)

    world.para()
    trigger_flashback(world, hero, place)
    reconsider(world, hero, parent)
    suit_up(world, hero, parent, gear)

    world.para()
    launch(world, hero, mission, gear, place)
    resolve(world, hero, parent, gear)

    world.facts.update(
        hero=hero,
        parent=parent,
        gear=world.get("gear"),
        flashback_used=world.get("memory").memes["active"] >= THRESHOLD,
        protected=hero.meters["protected"] >= THRESHOLD,
        mission_done=hero.meters["outside"] >= THRESHOLD and hero.meters["protected"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "underoos": [
        (
            "What are underoos?",
            "Underoos are underwear, often with fun colors or pictures on them. They are comfy for being inside, but by themselves they are not the same as outdoor clothes."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back at something that happened earlier. It helps a character remember an old feeling or lesson before making a new choice."
        )
    ],
    "cold": [
        (
            "Why can bare feet feel bad on cold ground?",
            "Bare feet lose heat quickly on cold ground, so they can start to sting or ache. Shoes or slippers help keep that warmth in."
        )
    ],
    "wet": [
        (
            "Why is wet grass uncomfortable on bare feet?",
            "Wet grass can make feet cold and slippery. That is why dry shoes or boots can make outside play feel much better."
        )
    ],
    "splinters": [
        (
            "What is a splinter?",
            "A splinter is a tiny sharp piece of wood that can poke into your skin. Shoes help protect your feet from rough wooden boards."
        )
    ],
    "scratches": [
        (
            "Why can a garden path feel scratchy?",
            "Little stones, stems, and rough ground can scrape knees or feet. Clothes and sturdy shoes help protect your skin."
        )
    ],
    "wind": [
        (
            "Why does wind feel colder than still air?",
            "Wind blows the warm air away from your skin, so your body feels colder faster. Layers help hold warmth close."
        )
    ],
    "boots": [
        (
            "What do boots help with?",
            "Boots help protect feet from cold, wet ground and from rough things underfoot. They also make stepping outside feel steadier."
        )
    ],
    "layers": [
        (
            "Why do layers help outside?",
            "Layers trap warmth and cover more of your body. That makes outdoor play safer and more comfortable."
        )
    ],
}

KNOWLEDGE_ORDER = ["underoos", "flashback", "cold", "wet", "splinters", "scratches", "wind", "boots", "layers"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place_cfg"]
    mission = f["mission_cfg"]
    return [
        f'Write a short Space Adventure story for a 3-to-5-year-old that includes the word "underoos" and uses a flashback.',
        f"Tell a gentle story where a little {hero.type} thinks underoos are enough for a pretend spacewalk to {mission.goal}, but a flashback helps {hero.pronoun('object')} choose proper gear.",
        f"Write a child-facing story set at {place.phrase} where a grown-up pauses a silly launch, a memory changes the plan, and the mission still ends happily.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    place = f["place_cfg"]
    mission = f["mission_cfg"]
    gear = f["gear_cfg"]
    name = f["hero_name"]
    pw = parent.label_word
    hazards = f.get("predicted_hazards", [])
    hazard_text = ", ".join(hazards) if hazards else "outside problems"
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little {hero.type} named {name} who wanted a big pretend spacewalk. {name}'s {pw} helps turn the game into a safe adventure instead of stopping it forever."
        ),
        (
            "Why did the child think underoos were a space suit?",
            f"{name} was deep in a pretend Space Adventure, so the silver-star underoos felt like an astronaut outfit. The game was so vivid that the ordinary place began to look like another planet."
        ),
        (
            f"Why did {name}'s {pw} stop the launch at first?",
            f"{pw.capitalize()} saw that {place.phrase} had real outside hazards like {hazard_text}. Going out in underoos alone would have made the mission cold, stingy, or uncomfortable instead of fun."
        ),
    ]
    if f.get("flashback_used"):
        qa.append(
            (
                "What was the flashback for?",
                f"The flashback reminded {name} of an earlier rushed mission that had gone badly. Because {hero.pronoun()} remembered that real discomfort, {hero.pronoun()} was ready to choose a smarter launch this time."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They kept the underoos as the secret first layer and added {gear.phrase} on top. That way the child could still feel like an astronaut while being protected from the outside hazards."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The mission still happened, but it happened safely. At the end, {name} reached {mission.beacon} and felt proud because bravery and good preparation were working together."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"underoos", "flashback", "cold"}
    place = world.facts["place_cfg"]
    gear = world.facts["gear_cfg"]
    tags |= set(place.hazards)
    if "boots" in gear.tags or gear.id in {"moon_boots", "rain_shell"}:
        tags.add("boots")
    if gear.id in {"star_layers", "comet_suit", "rain_shell"}:
        tags.add("layers")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        if ent.attrs:
            shown = {}
            for k, v in ent.attrs.items():
                if isinstance(v, set):
                    if v:
                        shown[k] = sorted(v)
                elif v:
                    shown[k] = v
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
risky(P) :- place(P), outdoor(P), hazard(P,_).

covers_all(P,G) :- gear(G), not missing(P,G).
missing(P,G) :- hazard(P,H), not guards(G,H).

usable_gear(P,G) :- risky(P), covers_all(P,G).
valid(P,M) :- affords(P,M), usable_gear(P,_).

better(P,G1) :- usable_gear(P,G1), usable_gear(P,G2), score(G2,S2), score(G1,S1), S2 > S1.
best_gear(P,G) :- usable_gear(P,G), not better(P,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.outdoor:
            lines.append(asp.fact("outdoor", place_id))
        for hazard in sorted(place.hazards):
            lines.append(asp.fact("hazard", place_id, hazard))
        for mission_id in sorted(place.missions):
            lines.append(asp.fact("affords", place_id, mission_id))
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        lines.append(asp.fact("score", gear_id, gear.score))
        for hazard in sorted(gear.guards):
            lines.append(asp.fact("guards", gear_id, hazard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_best_gears() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show best_gear/2."))
    return sorted(set(asp.atoms(model, "best_gear")))


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

    clingo_best = {}
    for place_id, gear_id in asp_best_gears():
        clingo_best[place_id] = gear_id
    python_best = {}
    for place_id, place in PLACES.items():
        gear = choose_gear(place)
        if gear is not None and place_is_risky(place):
            python_best[place_id] = gear.id
    if clingo_best == python_best:
        print("OK: best gear choices match.")
    else:
        rc = 1
        print("MISMATCH in best gear choices:")
        print("  clingo:", clingo_best)
        print("  python:", python_best)

    # Smoke test normal generation so --verify catches runtime regressions too.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:  # pragma: no cover - defensive in batch generation
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="backyard",
        mission="moon_rocks",
        hero="Luna",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="porch",
        mission="beacon",
        hero="Leo",
        gender="boy",
        parent="father",
        trait="brave",
    ),
    StoryParams(
        place="garden",
        mission="satellite",
        hero="Ruby",
        gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        place="balcony",
        mission="beacon",
        hero="Max",
        gender="boy",
        parent="father",
        trait="eager",
    ),
]


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child in underoos wants a pretend spacewalk, "
                    "a flashback changes the plan, and proper layers save the mission."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None:
        place = PLACES.get(args.place)
        if place is None:
            raise StoryError(f"(No story: unknown place {args.place!r}.)")
        if not place_is_risky(place) or choose_gear(place) is None:
            raise StoryError(explain_rejection(place))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mission is None or combo[1] == args.mission)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mission_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        mission=mission_id,
        hero=hero,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES.get(params.place)
    mission = MISSIONS.get(params.mission)
    if place is None:
        raise StoryError(f"(No story: unknown place {params.place!r}.)")
    if mission is None:
        raise StoryError(f"(No story: unknown mission {params.mission!r}.)")
    if params.mission not in place.missions:
        raise StoryError(f"(No story: {place.phrase} does not support the mission {params.mission!r}.)")
    if not place_is_risky(place):
        raise StoryError(explain_rejection(place))
    gear = choose_gear(place)
    if gear is None:
        raise StoryError(explain_rejection(place))

    world = tell(
        place=place,
        mission=mission,
        gear=gear,
        hero_name=params.hero,
        hero_type=params.gender,
        parent_type=params.parent,
        trait=params.trait,
    )
    story = world.render().replace("hero", params.hero)
    story = story.replace("parent", "parent")
    sample = StorySample(
        params=params,
        story=story.replace("the parent", world.get("parent").label_word).replace("hero", params.hero),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    # Replace the internal character id in text and QA answers/questions.
    sample.story = sample.story.replace("hero", params.hero)
    for item in sample.story_qa:
        item.question = item.question.replace("hero", params.hero).replace("parent", world.get("parent").label_word)
        item.answer = item.answer.replace("hero", params.hero).replace("parent", world.get("parent").label_word)
    for item in sample.world_qa:
        item.question = item.question.replace("hero", params.hero)
        item.answer = item.answer.replace("hero", params.hero)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show best_gear/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        best = dict(asp_best_gears())
        print(f"{len(combos)} compatible (place, mission) combos:\n")
        for place_id, mission_id in combos:
            print(f"  {place_id:9} {mission_id:10} gear={best.get(place_id, '?')}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
