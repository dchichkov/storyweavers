#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hindrance_railroad_crossing_rhyme_sound_effects_adventure.py
========================================================================================

A standalone story world for a small adventure at a railroad crossing.

Premise
-------
Two children set out on a little expedition toward a place beyond the tracks.
At the railroad crossing, the gate drops and the bell begins to ring. The
crossing becomes a real hindrance: they cannot keep going, and sometimes the
wind makes their precious cargo harder to hold. A calm helper turns the wait
into a safety rhyme. The children choose the safe action, let the train pass,
and then continue their adventure.

World logic
-----------
This world models:

* typed entities with physical meters and emotional memes
* a short causal chain around a lowered crossing gate and a passing train
* a reasonableness gate that refuses unsafe actions
* an inline ASP twin for destination/cargo compatibility, safe actions,
  and whether a windy paper cargo flutters at the crossing

Run it
------
python storyworlds/worlds/gpt-5.4/hindrance_railroad_crossing_rhyme_sound_effects_adventure.py
python storyworlds/worlds/gpt-5.4/hindrance_railroad_crossing_rhyme_sound_effects_adventure.py --all
python storyworlds/worlds/gpt-5.4/hindrance_railroad_crossing_rhyme_sound_effects_adventure.py --qa
python storyworlds/worlds/gpt-5.4/hindrance_railroad_crossing_rhyme_sound_effects_adventure.py --trace --seed 7
python storyworlds/worlds/gpt-5.4/hindrance_railroad_crossing_rhyme_sound_effects_adventure.py --verify
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
        female = {"girl", "mother", "grandmother", "woman", "aunt", "sister"}
        male = {"boy", "father", "grandfather", "man", "uncle", "brother"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    beyond: str
    arrival: str
    cargo_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    hold_text: str
    arrival_use: str
    cargo_tags: set[str] = field(default_factory=set)
    paper: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    phrase: str
    reassurance: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TrainCfg:
    id: str
    label: str
    sound: str
    motion: str
    tail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ActionCfg:
    id: str
    sense: int
    text: str
    why_bad: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    destination: str
    cargo: str
    helper: str
    train: str
    action: str
    wind: str
    hero_name: str
    hero_gender: str
    pal_name: str
    pal_gender: str
    seed: Optional[int] = None


DESTINATIONS = {
    "sunflower_hill": Destination(
        id="sunflower_hill",
        label="Sunflower Hill",
        phrase="Sunflower Hill",
        beyond="the bright hill beyond the railroad crossing",
        arrival="At the top, the sunflowers nodded taller than their shoulders.",
        cargo_tags={"map"},
        tags={"hill", "sunflower"},
    ),
    "mural": Destination(
        id="mural",
        label="the caboose mural",
        phrase="the caboose mural by the station wall",
        beyond="the station wall on the far side of the crossing",
        arrival="The painted caboose glowed red and gold, just waiting to be admired up close.",
        cargo_tags={"sketch"},
        tags={"mural", "train_art"},
    ),
    "garden_plot": Destination(
        id="garden_plot",
        label="the little garden plot",
        phrase="the little garden plot beside the depot fence",
        beyond="the depot fence beyond the tracks",
        arrival="By the fence, the empty patch of dirt looked ready for careful hands.",
        cargo_tags={"seeds"},
        tags={"garden"},
    ),
    "picnic_spot": Destination(
        id="picnic_spot",
        label="the picnic spot",
        phrase="the shady picnic spot near the signal house",
        beyond="the signal house on the far side of the crossing",
        arrival="The picnic blanket spread beneath a tree, and the whole place smelled like apples and grass.",
        cargo_tags={"picnic"},
        tags={"picnic"},
    ),
}

CARGO = {
    "treasure_map": Cargo(
        id="treasure_map",
        label="map",
        phrase="a folded treasure map",
        hold_text="kept one hand on the fluttery map",
        arrival_use="They opened the map and followed its curly red line like real explorers.",
        cargo_tags={"map"},
        paper=True,
        tags={"map", "paper"},
    ),
    "sketchbook": Cargo(
        id="sketchbook",
        label="sketchbook",
        phrase="a blue sketchbook",
        hold_text="hugged the sketchbook to their chest",
        arrival_use="They opened the sketchbook and began drawing the bright red caboose.",
        cargo_tags={"sketch"},
        paper=True,
        tags={"sketchbook", "paper"},
    ),
    "seed_packet": Cargo(
        id="seed_packet",
        label="seed packet",
        phrase="a seed packet full of bean seeds",
        hold_text="curled their fingers around the seed packet",
        arrival_use="They tipped the little seeds into the waiting dirt, one tiny treasure at a time.",
        cargo_tags={"seeds"},
        paper=True,
        tags={"seeds", "paper"},
    ),
    "picnic_basket": Cargo(
        id="picnic_basket",
        label="picnic basket",
        phrase="a small picnic basket",
        hold_text="held the basket carefully between them",
        arrival_use="They set down the basket and found warm muffins tucked inside a cloth.",
        cargo_tags={"picnic"},
        paper=False,
        tags={"picnic"},
    ),
}

HELPERS = {
    "grandpa": HelperCfg(
        id="grandpa",
        type="grandfather",
        phrase="their grandpa",
        reassurance="waiting was part of the adventure too",
        rhyme="Red light bright, wait back tight.",
        tags={"grownup", "rhyme"},
    ),
    "mom": HelperCfg(
        id="mom",
        type="mother",
        phrase="their mom",
        reassurance="a good explorer listens to bells and lights",
        rhyme="Bell goes ding, don't cross a thing.",
        tags={"grownup", "rhyme"},
    ),
    "crossing_guard": HelperCfg(
        id="crossing_guard",
        type="woman",
        phrase="the crossing guard",
        reassurance="the safest feet are patient feet",
        rhyme="Gate drops low, stop and slow.",
        tags={"grownup", "rhyme", "guard"},
    ),
}

TRAINS = {
    "freight": TrainCfg(
        id="freight",
        label="a long freight train",
        sound="Ding-ding-ding! Clack-clack-clack!",
        motion="boxcars thundered past in a windy line",
        tail="At last the final car rattled by with a rusty squeal.",
        tags={"freight", "train"},
    ),
    "passenger": TrainCfg(
        id="passenger",
        label="a silver passenger train",
        sound="Ding-ding-ding! Whooo-oo!",
        motion="silver windows flashed by like a string of mirrors",
        tail="Then the last bright car swept away around the bend.",
        tags={"passenger", "train"},
    ),
    "steam_excursion": TrainCfg(
        id="steam_excursion",
        label="a puffing old steam train",
        sound="Ding-ding-ding! Chuff-chuff! Toot-toot!",
        motion="white steam curled above the cars as they rolled along",
        tail="The caboose bobbed past at the very end like a waving red toy.",
        tags={"steam", "train"},
    ),
}

ACTIONS = {
    "wait_back": ActionCfg(
        id="wait_back",
        sense=3,
        text="stood behind the white line and waited for the gate to rise",
        why_bad="",
        tags={"safe", "wait"},
    ),
    "hold_hands_wait": ActionCfg(
        id="hold_hands_wait",
        sense=3,
        text="stepped back together, held hands, and waited for the train to pass",
        why_bad="",
        tags={"safe", "wait"},
    ),
    "duck_under_gate": ActionCfg(
        id="duck_under_gate",
        sense=1,
        text="ducked under the gate",
        why_bad="a lowered crossing gate means a train is coming, and going under it is never safe",
        tags={"unsafe"},
    ),
    "race_the_train": ActionCfg(
        id="race_the_train",
        sense=0,
        text="tried to race across before the train arrived",
        why_bad="trains move faster than children can judge, so racing one is far too dangerous",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
WINDS = ["calm", "breezy", "strong"]


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_bell_means_blocked(world: World) -> list[str]:
    crossing = world.get("crossing")
    if crossing.meters["bell"] < THRESHOLD:
        return []
    sig = ("blocked", "crossing")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crossing.meters["gate_down"] += 1
    for child in (world.get("hero"), world.get("pal")):
        child.memes["stopped"] += 1
        child.memes["frustration"] += 1
    return ["__blocked__"]


def _r_gate_causes_caution(world: World) -> list[str]:
    crossing = world.get("crossing")
    if crossing.meters["gate_down"] < THRESHOLD:
        return []
    sig = ("caution", "crossing")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for child in (world.get("hero"), world.get("pal")):
        child.memes["caution"] += 1
    return []


def _r_wind_flutters_paper(world: World) -> list[str]:
    cargo = world.get("cargo")
    crossing = world.get("crossing")
    if cargo.attrs.get("paper") is not True:
        return []
    if crossing.meters["wind_strong"] < THRESHOLD:
        return []
    sig = ("flutter", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["fluttering"] += 1
    for child in (world.get("hero"), world.get("pal")):
        child.memes["worry"] += 1
    return ["__flutter__"]


CAUSAL_RULES = [
    Rule(name="bell_means_blocked", tag="physical", apply=_r_bell_means_blocked),
    Rule(name="gate_causes_caution", tag="social", apply=_r_gate_causes_caution),
    Rule(name="wind_flutters_paper", tag="physical", apply=_r_wind_flutters_paper),
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
            if item == "__flutter__":
                hero = world.get("hero")
                cargo = world.get("cargo")
                world.say(
                    f"A gust gave {cargo.phrase} a flap-flap-flap, and {hero.id} grabbed it fast before it could skitter toward the rails."
                )
    return produced


def compatible(destination: Destination, cargo: Cargo) -> bool:
    return bool(destination.cargo_tags & cargo.cargo_tags)


def safe_actions() -> list[ActionCfg]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def strong_wind_paper_flutter(cargo: Cargo, wind: str) -> bool:
    return cargo.paper and wind == "strong"


def explain_combo_rejection(destination: Destination, cargo: Cargo) -> str:
    return (
        f"(No story: {cargo.phrase} does not fit the trip to {destination.phrase}. "
        f"The children need cargo that honestly belongs in that adventure.)"
    )


def explain_action_rejection(action_id: str) -> str:
    action = ACTIONS[action_id]
    better = ", ".join(sorted(a.id for a in safe_actions()))
    return (
        f"(Refusing action '{action_id}': {action.why_bad}. "
        f"Choose a safer action like {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for dest_id, dest in DESTINATIONS.items():
        for cargo_id, cargo in CARGO.items():
            if not compatible(dest, cargo):
                continue
            for action in safe_actions():
                combos.append((dest_id, cargo_id, action.id))
    return combos


def intro(world: World, hero: Entity, pal: Entity, helper: Entity,
          destination: Destination, cargo: Cargo) -> None:
    for child in (hero, pal):
        child.memes["joy"] += 1
        child.memes["wonder"] += 1
    world.say(
        f"{hero.id} and {pal.id} set out with {helper.label} on a little adventure to {destination.phrase}. "
        f"{hero.id} carried {cargo.phrase}, and {pal.id} walked beside {hero.pronoun('object')} with bright, quick steps."
    )
    world.say(
        f"They were sure something splendid waited beyond the tracks, and even the morning air felt full of secret plans."
    )


def reach_crossing(world: World, destination: Destination, wind: str) -> None:
    crossing = world.get("crossing")
    crossing.meters["approached"] += 1
    breeze = {
        "calm": "The air was still.",
        "breezy": "A little breeze brushed their cheeks.",
        "strong": "A stronger wind hurried along the road.",
    }[wind]
    world.say(
        f"Soon they reached the railroad crossing, the last short stretch before {destination.beyond}. {breeze}"
    )


def signal_starts(world: World, train: TrainCfg) -> None:
    crossing = world.get("crossing")
    crossing.meters["bell"] += 1
    world.say(
        f"Then the warning lights blinked red-red-red, and the bell sang, \"{train.sound}\""
    )
    propagate(world, narrate=False)
    world.say(
        "Down came the striped gate. It was a real hindrance now, standing across their path like a firm arm."
    )


def tempt(world: World, hero: Entity, action: ActionCfg) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f"{hero.id} bounced on {hero.pronoun('possessive')} toes. \"Oh, fiddlesticks,\" {hero.pronoun()} said. "
        f"\"I want to keep going.\""
    )
    if action.id in {"wait_back", "hold_hands_wait"}:
        world.say(
            f"For one quick heartbeat, hurrying forward looked tempting, but {hero.id} remembered the lights and stayed put."
        )


def wind_beat(world: World, cargo: Cargo, wind: str) -> None:
    crossing = world.get("crossing")
    if wind == "strong":
        crossing.meters["wind_strong"] += 1
    elif wind == "breezy":
        crossing.meters["wind_breezy"] += 1
    propagate(world, narrate=True)
    if wind == "breezy" and cargo.paper:
        world.say(
            f"The breeze made the edge of {cargo.phrase} whisper, \"frrp-frrp,\" but it stayed safely in small hands."
        )
    elif wind == "calm":
        world.say("Nothing moved except the blinking lights and the eager children.")


def rhyme_warning(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    hero = world.get("hero")
    pal = world.get("pal")
    for child in (hero, pal):
        child.memes["calm"] += 1
    world.say(
        f"{helper.label.capitalize()} smiled and said that {helper_cfg.reassurance}. "
        f"Then {helper.pronoun()} tapped the air to the bell and taught them a rhyme: "
        f"\"{helper_cfg.rhyme}\""
    )
    world.say(
        f"{hero.id} and {pal.id} whispered it back together until the waiting felt steadier."
    )


def choose_safe(world: World, action: ActionCfg) -> None:
    hero = world.get("hero")
    pal = world.get("pal")
    crossing = world.get("crossing")
    crossing.meters["safe_wait"] += 1
    for child in (hero, pal):
        child.memes["pride"] += 1
        child.memes["frustration"] = 0.0
    world.say(
        f"So they {action.text}. Choosing the safe thing felt slower, but also braver."
    )


def train_passes(world: World, train: TrainCfg) -> None:
    crossing = world.get("crossing")
    crossing.meters["train_passing"] += 1
    world.say(
        f"{train.label.capitalize()} rushed by: {train.motion}. The ground hummed under their shoes."
    )
    world.say(train.tail)
    crossing.meters["bell"] = 0.0
    crossing.meters["gate_down"] = 0.0
    crossing.meters["open"] += 1


def cross_and_arrive(world: World, destination: Destination, cargo: Cargo) -> None:
    hero = world.get("hero")
    pal = world.get("pal")
    for child in (hero, pal):
        child.memes["joy"] += 1
        child.memes["relief"] += 1
    world.say(
        "At last the bell fell silent. Up rose the gate. The children crossed only then, step by careful step, with the rails shining below."
    )
    world.say(destination.arrival)
    world.say(
        f"{cargo.arrival_use} The wait at the crossing had not ended the adventure. It had simply taught them how brave patience can be."
    )
    world.say(
        f"As they settled in, {hero.id} grinned and said the rhyme one more time, and this time it sounded like part of the treasure."
    )


def tell(params: StoryParams) -> World:
    destination = DESTINATIONS[params.destination]
    cargo_cfg = CARGO[params.cargo]
    helper_cfg = HELPERS[params.helper]
    train_cfg = TRAINS[params.train]
    action_cfg = ACTIONS[params.action]

    if not compatible(destination, cargo_cfg):
        raise StoryError(explain_combo_rejection(destination, cargo_cfg))
    if action_cfg.sense < SENSE_MIN:
        raise StoryError(explain_action_rejection(action_cfg.id))
    if params.wind not in WINDS:
        raise StoryError(f"(Unknown wind setting: {params.wind})")

    world = World()
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        role="hero",
        label=params.hero_name,
        phrase=params.hero_name,
        tags={"child"},
    ))
    pal = world.add(Entity(
        id=params.pal_name,
        kind="character",
        type=params.pal_gender,
        role="pal",
        label=params.pal_name,
        phrase=params.pal_name,
        tags={"child"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.phrase,
        phrase=helper_cfg.phrase,
        tags=set(helper_cfg.tags),
    ))
    crossing = world.add(Entity(
        id="crossing",
        type="crossing",
        label="railroad crossing",
        phrase="the railroad crossing",
        tags={"crossing"},
    ))
    cargo = world.add(Entity(
        id="cargo",
        type="cargo",
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        tags=set(cargo_cfg.tags),
        attrs={"paper": cargo_cfg.paper},
    ))

    intro(world, hero, pal, helper, destination, cargo_cfg)
    world.para()
    reach_crossing(world, destination, params.wind)
    signal_starts(world, train_cfg)
    tempt(world, hero, action_cfg)
    wind_beat(world, cargo_cfg, params.wind)
    rhyme_warning(world, helper, helper_cfg)
    choose_safe(world, action_cfg)
    world.para()
    train_passes(world, train_cfg)
    cross_and_arrive(world, destination, cargo_cfg)

    world.facts.update(
        destination=destination,
        cargo_cfg=cargo_cfg,
        helper_cfg=helper_cfg,
        train_cfg=train_cfg,
        action_cfg=action_cfg,
        wind=params.wind,
        hero=hero,
        pal=pal,
        helper=helper,
        crossing=crossing,
        cargo=cargo,
        fluttered=cargo.meters["fluttering"] >= THRESHOLD,
        rhyme=helper_cfg.rhyme,
    )
    return world


KNOWLEDGE = {
    "crossing": [
        (
            "What is a railroad crossing?",
            "A railroad crossing is the place where a road or path goes across train tracks. Gates, bells, and lights help people know when it is safe to wait and when it is safe to cross."
        )
    ],
    "train": [
        (
            "Why should children wait when crossing lights flash and bells ring?",
            "Flashing lights and ringing bells mean a train is coming or passing. Trains are very big and cannot stop quickly, so people must stay back and wait."
        )
    ],
    "gate": [
        (
            "Why should you never go under a crossing gate?",
            "A lowered gate is there to stop people from stepping onto the tracks when a train is near. Going under it is unsafe because the train can reach the crossing very fast."
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map helps you know where to go. It can show paths, landmarks, and the way to a special place."
        )
    ],
    "sketchbook": [
        (
            "What is a sketchbook for?",
            "A sketchbook is for drawing pictures and ideas. It lets you save what you see on paper."
        )
    ],
    "seeds": [
        (
            "What grows from seeds?",
            "Seeds can grow into plants when they have soil, water, sunlight, and time. Tiny seeds can become very tall plants."
        )
    ],
    "picnic": [
        (
            "What is a picnic?",
            "A picnic is a meal you eat outside, often on a blanket. People bring food in a basket and enjoy the fresh air."
        )
    ],
    "wind": [
        (
            "Why can wind make paper hard to hold?",
            "Paper is light, so moving air can push and flap it easily. A strong gust can tug it right out of your fingers."
        )
    ],
    "rhyme": [
        (
            "Why can a rhyme help you remember a safety rule?",
            "Rhymes are easy to say and easy to remember because the words sound alike. That makes them useful when you want to keep an important rule in your mind."
        )
    ],
}
KNOWLEDGE_ORDER = ["crossing", "train", "gate", "map", "sketchbook", "seeds", "picnic", "wind", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    pal = f["pal"]
    destination = f["destination"]
    cargo_cfg = f["cargo_cfg"]
    return [
        (
            f'Write a short adventure story for a 3-to-5-year-old set at a railroad crossing. '
            f'Include the word "hindrance," some playful sound effects, and a safety rhyme.'
        ),
        (
            f"Tell a gentle adventure where {hero.id} and {pal.id} are on the way to {destination.phrase} "
            f"with {cargo_cfg.phrase}, but a crossing gate and a passing train make them wait."
        ),
        (
            f"Write a child-facing story in which a railroad crossing becomes a hindrance, "
            f"the sounds of the train matter, and the children finish their trip only after waiting safely."
        ),
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    pal = f["pal"]
    helper = f["helper"]
    destination = f["destination"]
    cargo_cfg = f["cargo_cfg"]
    train_cfg = f["train_cfg"]
    action_cfg = f["action_cfg"]
    wind = f["wind"]
    fluttered = f["fluttered"]
    rhyme = f["rhyme"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {pal.id}, who were going on a little adventure with {helper.label}. "
            f"They were heading toward {destination.phrase}."
        ),
        (
            "What was the hindrance in the story?",
            f"The hindrance was the lowered gate at the railroad crossing. "
            f"The blinking lights and ringing bell meant they had to stop and wait for the train."
        ),
        (
            "Why did the children stop instead of hurrying across?",
            f"They stopped because the crossing lights were flashing and the gate was down, which meant a train was coming. "
            f"Waiting behind the line kept them away from the tracks until it was safe."
        ),
        (
            "What rhyme did they use?",
            f'They used the rhyme, "{rhyme}" It helped turn the waiting into something they could remember and say together.'
        ),
    ]
    if fluttered:
        qa.append(
            (
                f"What happened to the {cargo_cfg.label} in the wind?",
                f"The strong wind made {cargo_cfg.phrase} flap and tug in their hands. "
                f"That made the crossing feel even tenser, because they had to hold onto it carefully while they waited."
            )
        )
    else:
        qa.append(
            (
                f"Did the wind make trouble for the {cargo_cfg.label}?",
                f"Not much. The children still had to be careful, but the {cargo_cfg.label} stayed safely with them while the train passed."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the gate rising, the bell going quiet, and the children crossing only when it was safe. "
            f"Then they reached {destination.phrase} and used {cargo_cfg.phrase} for the adventure they had planned."
        )
    )
    if action_cfg.id == "hold_hands_wait":
        qa.append(
            (
                "How did the children help each other while they waited?",
                f"They stepped back together and held hands while the train passed. "
                f"That helped them stay calm and make the safe choice together."
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"crossing", "train", "gate", "rhyme"}
    cargo_tags = set(f["cargo_cfg"].tags)
    helper_tags = set(f["helper_cfg"].tags)
    if "paper" in cargo_tags and f["wind"] == "strong":
        tags.add("wind")
    if "map" in cargo_tags:
        tags.add("map")
    if "sketchbook" in cargo_tags:
        tags.add("sketchbook")
    if "seeds" in cargo_tags:
        tags.add("seeds")
    if "picnic" in cargo_tags:
        tags.add("picnic")
    if "rhyme" in helper_tags:
        tags.add("rhyme")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        destination="sunflower_hill",
        cargo="treasure_map",
        helper="grandpa",
        train="steam_excursion",
        action="wait_back",
        wind="strong",
        hero_name="Lily",
        hero_gender="girl",
        pal_name="Tom",
        pal_gender="boy",
    ),
    StoryParams(
        destination="mural",
        cargo="sketchbook",
        helper="crossing_guard",
        train="passenger",
        action="hold_hands_wait",
        wind="breezy",
        hero_name="Max",
        hero_gender="boy",
        pal_name="Mia",
        pal_gender="girl",
    ),
    StoryParams(
        destination="garden_plot",
        cargo="seed_packet",
        helper="mom",
        train="freight",
        action="wait_back",
        wind="calm",
        hero_name="Zoe",
        hero_gender="girl",
        pal_name="Ben",
        pal_gender="boy",
    ),
    StoryParams(
        destination="picnic_spot",
        cargo="picnic_basket",
        helper="grandpa",
        train="passenger",
        action="hold_hands_wait",
        wind="breezy",
        hero_name="Noah",
        hero_gender="boy",
        pal_name="Ella",
        pal_gender="girl",
    ),
]


ASP_RULES = r"""
compatible(D, C) :- destination(D), cargo(C), needs_tag(D, T), has_tag(C, T).
safe_action(A)   :- action(A), sense(A, S), sense_min(M), S >= M.
valid(D, C, A)   :- compatible(D, C), safe_action(A).

flutter :- chosen_cargo(C), paper(C), chosen_wind(strong).
no_flutter :- not flutter.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for dest_id, dest in DESTINATIONS.items():
        lines.append(asp.fact("destination", dest_id))
        for tag in sorted(dest.cargo_tags):
            lines.append(asp.fact("needs_tag", dest_id, tag))
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        for tag in sorted(cargo.cargo_tags):
            lines.append(asp.fact("has_tag", cargo_id, tag))
        if cargo.paper:
            lines.append(asp.fact("paper", cargo_id))
    for action_id, action in ACTIONS.items():
        lines.append(asp.fact("action", action_id))
        lines.append(asp.fact("sense", action_id, action.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for wind in WINDS:
        lines.append(asp.fact("wind", wind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_flutter(cargo_id: str, wind: str) -> bool:
    import asp

    extra = "\n".join([
        asp.fact("chosen_cargo", cargo_id),
        asp.fact("chosen_wind", wind),
    ])
    model = asp.one_model(asp_program(extra, "#show flutter/0."))
    return bool(asp.atoms(model, "flutter"))


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    flutter_cases = 0
    flutter_bad = 0
    for cargo_id, cargo in CARGO.items():
        for wind in WINDS:
            flutter_cases += 1
            if asp_flutter(cargo_id, wind) != strong_wind_paper_flutter(cargo, wind):
                flutter_bad += 1
    if flutter_bad == 0:
        print(f"OK: flutter inference matches on {flutter_cases} cases.")
    else:
        rc = 1
        print(f"MISMATCH: flutter inference differs on {flutter_bad}/{flutter_cases} cases.")

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a railroad crossing adventure with rhyme and sound effects."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--train", choices=TRAINS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.destination and args.cargo:
        if not compatible(DESTINATIONS[args.destination], CARGO[args.cargo]):
            raise StoryError(explain_combo_rejection(DESTINATIONS[args.destination], CARGO[args.cargo]))
    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        raise StoryError(explain_action_rejection(args.action))

    combos = [
        combo for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.action is None or combo[2] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, cargo, action = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    train = args.train or rng.choice(sorted(TRAINS))
    wind = args.wind or rng.choice(WINDS)
    hero_name, hero_gender = _pick_child(rng)
    pal_name, pal_gender = _pick_child(rng, avoid=hero_name)

    return StoryParams(
        destination=destination,
        cargo=cargo,
        helper=helper,
        train=train,
        action=action,
        wind=wind,
        hero_name=hero_name,
        hero_gender=hero_gender,
        pal_name=pal_name,
        pal_gender=pal_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("destination", DESTINATIONS),
        ("cargo", CARGO),
        ("helper", HELPERS),
        ("train", TRAINS),
        ("action", ACTIONS),
    ):
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Unknown {field_name}: {value})")
    world = tell(params)
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
        print(asp_program("", "#show valid/3.\n#show flutter/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (destination, cargo, action) combos:\n")
        for destination, cargo, action in combos:
            print(f"  {destination:16} {cargo:14} {action}")
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
            header = f"### {p.hero_name} and {p.pal_name}: {p.destination} with {p.cargo}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
