#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hoist_telemarketing_bouillon_rhyme_cautionary_superhero_story.py
================================================================================================

A standalone story world for a tiny rhyming superhero cautionary tale.

Premise
-------
Two children are playing superheroes at home when a grown-up is briefly stuck on
a silly telemarketing phone call. One child is tempted to climb and hoist a hot
cup or bowl of bouillon alone, hoping for "hero fuel." The other child warns that
hot liquid and wobbly furniture do not mix. Sometimes the wiser child stops the
plan before anything happens. Sometimes the child tries anyway, a spill starts,
and the grown-up fixes the situation calmly. The ending always proves what changed:
real heroes wait, call for help, and use safe hands instead of risky bravado.

This world keeps the schema deliberately small:
- one shared Entity dataclass for people and things
- typed meters (physical) and memes (emotional)
- a tiny reasonableness gate
- an inline ASP twin for the gate and ending model
- story, prompts, grounded QA, and world-knowledge QA from world state

Run it
------
    python storyworlds/worlds/gpt-5.4/hoist_telemarketing_bouillon_rhyme_cautionary_superhero_story.py
    python storyworlds/worlds/gpt-5.4/hoist_telemarketing_bouillon_rhyme_cautionary_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/hoist_telemarketing_bouillon_rhyme_cautionary_superhero_story.py --qa
    python storyworlds/worlds/gpt-5.4/hoist_telemarketing_bouillon_rhyme_cautionary_superhero_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/hoist_telemarketing_bouillon_rhyme_cautionary_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this nested script is run directly.
# File lives under storyworlds/worlds/gpt-5.4/, so go up three levels to storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "sensible"}


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
    hot: bool = False
    unstable: bool = False
    safe_tool: bool = False
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
class Theme:
    id: str
    hideout: str
    opening: str
    duo_name: str
    hero_title: str
    sidekick_title: str
    ending_image: str


@dataclass
class Load:
    id: str
    label: str
    phrase: str
    heat: int
    steam: str
    vessel: str
    tags: set[str] = field(default_factory=set)

    @property
    def hot_phrase(self) -> str:
        return f"hot {self.label}"


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    instability: int
    place: str
    tags: set[str] = field(default_factory=set)

    @property
    def unstable(self) -> bool:
        return self.instability > 0


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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill_alarm(world: World) -> list[str]:
    out: list[str] = []
    load = world.entities.get("load")
    if load is None or load.meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill_alarm", "load")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    if "room" in world.entities:
        world.get("room").meters["mess"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill_alarm", tag="physical", apply=_r_spill_alarm),
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


THEMES = {
    "kitchen_comet": Theme(
        id="kitchen_comet",
        hideout="the kitchen comet cave",
        opening="The kitchen floor became a launch pad, the towels became capes, and the children whispered hero names with a swoop-and-zoom tune.",
        duo_name="the Comet Crew",
        hero_title="Captain",
        sidekick_title="Scout",
        ending_image="their capes fluttered by the table while the safe cups waited low and cool"
    ),
    "balcony_beacon": Theme(
        id="balcony_beacon",
        hideout="the beacon base",
        opening="Near the bright window, pot lids became shields, dish towels became capes, and the children marched in a rhyme of boom and bloom.",
        duo_name="the Beacon Team",
        hero_title="Blaze",
        sidekick_title="Guard",
        ending_image="their paper stars shone on the wall while the soup rested where small hands could reach"
    ),
    "laundry_laser": Theme(
        id="laundry_laser",
        hideout="the laser laundry lab",
        opening="A basket became a moon rover, socks became secret flags, and the children hummed a brave little tune that rhymed room with zoom.",
        duo_name="the Laser League",
        hero_title="Jet",
        sidekick_title="Shield",
        ending_image="their capes lay folded on the chair while the warm broth sat safely on the low tray"
    ),
}

LOADS = {
    "mug_bouillon": Load(
        id="mug_bouillon",
        label="mug of bouillon",
        phrase="a mug of golden bouillon",
        heat=2,
        steam="little curls of steam",
        vessel="mug",
        tags={"bouillon", "hot_liquid"},
    ),
    "bowl_bouillon": Load(
        id="bowl_bouillon",
        label="bowl of bouillon",
        phrase="a bowl of salty bouillon",
        heat=3,
        steam="a soft cloud of steam",
        vessel="bowl",
        tags={"bouillon", "hot_liquid"},
    ),
    "pot_bouillon": Load(
        id="pot_bouillon",
        label="small pot of bouillon",
        phrase="a small pot of savory bouillon",
        heat=4,
        steam="big silvery steam",
        vessel="pot",
        tags={"bouillon", "hot_liquid"},
    ),
}

PERCHES = {
    "wobbly_stool": Perch(
        id="wobbly_stool",
        label="wobbly stool",
        phrase="a wobbly stool by the counter",
        instability=2,
        place="by the counter",
        tags={"stool", "climbing"},
    ),
    "swivel_chair": Perch(
        id="swivel_chair",
        label="swivel chair",
        phrase="a swivel chair that loved to roll",
        instability=3,
        place="near the shelf",
        tags={"chair", "climbing"},
    ),
    "stacked_crate": Perch(
        id="stacked_crate",
        label="stacked crate",
        phrase="a stacked crate with a shaky top",
        instability=2,
        place="under the shelf",
        tags={"crate", "climbing"},
    ),
    "low_bench": Perch(
        id="low_bench",
        label="low bench",
        phrase="a low bench that sat steady and still",
        instability=0,
        place="under the hooks",
        tags={"bench"},
    ),
}

RESPONSES = {
    "call_adult": Response(
        id="call_adult",
        sense=3,
        power=5,
        text="ended the telemarketing call, crossed the room in three quick steps, took the hot {load} from small hands, and set it on the table to cool",
        fail="ended the telemarketing call and reached for the hot {load}, but a bigger splash had already slipped over the rim",
        qa_text="took the hot {load} away and set it down to cool",
        tags={"help", "adult", "hot_liquid"},
    ),
    "cool_and_wipe": Response(
        id="cool_and_wipe",
        sense=3,
        power=4,
        text="ended the telemarketing call, slid a towel under the hot {load}, and guided it safely to the sink before the spill could spread",
        fail="slid a towel under the hot {load}, but some of the broth had already splashed too far",
        qa_text="used a towel and guided the hot {load} safely away",
        tags={"help", "adult", "towel", "hot_liquid"},
    ),
    "super_lunge": Response(
        id="super_lunge",
        sense=1,
        power=2,
        text="tried a superhero lunge at the hot {load} and somehow caught it",
        fail="tried a superhero lunge at the hot {load}, but that wild move made the splash worse",
        qa_text="made a risky superhero lunge",
        tags={"bad_idea", "hot_liquid"},
    ),
}


def hazard_at_risk(load: Load, perch: Perch) -> bool:
    return load.heat > 0 and perch.instability > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(load: Load, perch: Perch, delay: int) -> int:
    return load.heat + perch.instability + delay


def is_contained(response: Response, load: Load, perch: Perch, delay: int) -> bool:
    return response.power >= severity_of(load, perch, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for load_id, load in LOADS.items():
            for perch_id, perch in PERCHES.items():
                if hazard_at_risk(load, perch):
                    combos.append((theme_id, load_id, perch_id))
    return combos


def explain_rejection(load: Load, perch: Perch) -> str:
    if perch.instability <= 0:
        return (
            f"(No story: {perch.phrase} is steady, so there is no honest reason for a superhero-style "
            f"warning about trying to hoist {load.phrase} from it. Pick a wobbly stool, swivel chair, or stacked crate.)"
        )
    if load.heat <= 0:
        return "(No story: the load is not hot, so the cautionary problem disappears.)"
    return "(No story: this combination does not create a plausible hot-spill risk.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too low-sense for this world "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_spill(world: World, perch_id: str) -> dict:
    sim = world.copy()
    perch = sim.get(perch_id)
    do_defy(sim, sim.get("instigator"), perch, narrate=False)
    do_hoist(sim, sim.get("instigator"), sim.get("load"), perch, narrate=False)
    return {
        "spill": sim.get("load").meters["spilled"] >= THRESHOLD,
        "fear": sum(kid.memes["fear"] for kid in sim.kids()),
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} were playing superheroes in {theme.hideout}. {theme.opening}"
    )
    world.say(
        f'"{theme.hero_title} {a.id} and {theme.sidekick_title} {b.id} of {theme.duo_name}!" '
        f"{a.id} cried. \"Zoom in the room, make space, make room!\""
    )


def parent_busy(world: World, parent: Entity) -> None:
    world.say(
        f"At the counter, {parent.label_word} was trying to end a telemarketing call that kept stretching long and wrong."
    )


def spot_hero_fuel(world: World, a: Entity, load: Load, perch: Perch) -> None:
    world.say(
        f"On the high counter sat {load.phrase}, sending up {load.steam}. "
        f"Beside it waited {perch.phrase}."
    )
    world.say(
        f"\"Hero fuel!\" {a.id} whispered. \"I can hoist that {load.vessel} myself, quick as a kite, quick as a light.\""
    )


def warn(world: World, b: Entity, a: Entity, load: Load, perch: Perch, parent: Entity) -> None:
    pred = predict_spill(world, "perch")
    b.memes["caution"] += 1
    world.facts["predicted_spill"] = pred["spill"]
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. '
        f'That is hot bouillon, and {perch.label} could wiggle and sway. '
        f'If you try to hoist it alone, it could splash before {parent.label_word} can help."'
    )


def do_defy(world: World, a: Entity, perch: Entity, narrate: bool = True) -> None:
    a.memes["defiance"] += 1
    a.meters["height"] += 1
    perch.meters["used"] += 1
    if narrate:
        world.say(
            f'"I am super fast," {a.id} said, climbing onto the {perch.label} with a brave-but-wrong song.'
        )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked at {b.id}, heard the warning, and climbed back down. "
        f"Real heroes, {b.id} said softly, wait when the heat is great."
    )
    world.say(
        f"Together they called to {parent.label_word}, and the kitchen felt less zoom and more room."
    )


def do_hoist(world: World, a: Entity, load_ent: Entity, perch: Entity, narrate: bool = True) -> None:
    spill = load_ent.meters["heat"] + perch.meters["instability"]
    if spill >= 4:
        load_ent.meters["spilled"] += 1
    if spill >= 6:
        a.meters["red_hands"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{a.id} reached up to hoist the {load_ent.label}. The {perch.label} gave a wobble, bobble, and wobble again."
        )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}! Hot bouillon!" {b.id} yelped.')
    if world.get("load").meters["spilled"] >= THRESHOLD:
        world.say("A golden splash skipped over the rim and spotted the floor.")


def rescue(world: World, parent: Entity, response: Response, load: Load) -> None:
    body = response.text.replace("{load}", load.label)
    world.get("load").meters["spilled"] = 0.0
    world.get("room").meters["mess"] = 0.0
    world.say(f"{parent.label_word.capitalize()} {body}.")
    world.say(
        f'Then {parent.pronoun()} knelt down and said, "Superheroes use safe help, not secret hoists by themselves."'
    )


def rescue_fail(world: World, parent: Entity, response: Response, load: Load) -> None:
    body = response.fail.replace("{load}", load.label)
    world.get("room").meters["mess"] += 1
    world.say(f"{parent.label_word.capitalize()} {body}.")
    world.say(
        "The splash was not huge, but it was enough to make everyone jump and stare."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} hugged them close. "
        f'"You were right to call me fast," {parent.pronoun()} said. '
        f'"Hot soup and climbing furniture are not a game. Brave hearts still wait for grown-up hands."'
    )


def stronger_lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    if a.meters["red_hands"] >= THRESHOLD:
        world.say(
            f"{parent.label_word.capitalize()} ran cool water over {a.id}'s fingers until the sting went down."
        )
    world.say(
        f'"That was a close one," {parent.label_word} said. '
        f'"A cape is for play. When something is hot, you call, you wait, and you do not climb to hoist it alone."'
    )


def safe_ending(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, load: Load) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"A little later, when the {load.label} was cool enough, {parent.label_word} poured it into safe low cups."
    )
    world.say(
        f"{a.id} and {b.id} sipped their bouillon at the table and tapped their toes in a tiny rhyme: "
        f"\"Low and slow, that is the hero way to go.\""
    )
    world.say(f"In the end, {theme.ending_image}.")


def tell(
    theme: Theme,
    load: Load,
    perch: Perch,
    response: Response,
    *,
    instigator: str = "Max",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 4,
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        phrase=instigator,
        role="instigator",
        traits=["bold"],
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        phrase=cautioner,
        role="cautioner",
        traits=[trait],
        attrs={"name": cautioner, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
        attrs={"name": parent_type},
        tags={"adult"},
    ))
    load_ent = world.add(Entity(
        id="load",
        type="food",
        label=load.label,
        phrase=load.phrase,
        hot=True,
        tags=set(load.tags),
    ))
    perch_ent = world.add(Entity(
        id="perch",
        type="furniture",
        label=perch.label,
        phrase=perch.phrase,
        unstable=perch.unstable,
        tags=set(perch.tags),
    ))
    world.add(Entity(id="room", type="room", label="kitchen"))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    a.attrs["age"] = instigator_age
    b.attrs["age"] = cautioner_age
    load_ent.meters["heat"] = float(load.heat)
    perch_ent.meters["instability"] = float(perch.instability)

    play_setup(world, a, b, theme)
    parent_busy(world, parent)
    spot_hero_fuel(world, a, load, perch)

    world.para()
    warn(world, b, a, load, perch, parent)
    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, parent)
        world.para()
        lesson(world, parent, a, b)
        safe_ending(world, parent, a, b, theme, load)
        severity = 0
        contained = True
        outcome = "averted"
    else:
        do_defy(world, a, perch_ent, narrate=True)
        world.para()
        do_hoist(world, a, load_ent, perch_ent, narrate=True)
        alarm(world, b, parent)
        severity = severity_of(load, perch, delay)
        load_ent.meters["severity"] = float(severity)
        contained = is_contained(response, load, perch, delay)

        world.para()
        if contained:
            rescue(world, parent, response, load)
            lesson(world, parent, a, b)
            world.para()
            safe_ending(world, parent, a, b, theme, load)
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, load)
            stronger_lesson(world, parent, a, b)
            world.para()
            safe_ending(world, parent, a, b, theme, load)
            outcome = "ouch"

    world.facts.update(
        theme=theme,
        load_cfg=load,
        perch_cfg=perch,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        load=load_ent,
        perch=perch_ent,
        relation=relation,
        delay=delay,
        severity=severity,
        outcome=outcome,
        contained=contained,
        averted=averted,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    theme: str
    load: str
    perch: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    delay: int = 0
    seed: Optional[int] = None


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Max", "Ben", "Leo", "Sam", "Finn", "Theo"]
TRAITS = ["careful", "steady", "thoughtful", "sensible", "curious", "brave"]


CURATED = [
    StoryParams(
        theme="kitchen_comet",
        load="mug_bouillon",
        perch="wobbly_stool",
        response="call_adult",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        delay=0,
    ),
    StoryParams(
        theme="balcony_beacon",
        load="bowl_bouillon",
        perch="swivel_chair",
        response="cool_and_wipe",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="thoughtful",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        delay=0,
    ),
    StoryParams(
        theme="laundry_laser",
        load="pot_bouillon",
        perch="stacked_crate",
        response="cool_and_wipe",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="mother",
        trait="steady",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
        delay=1,
    ),
]


KNOWLEDGE = {
    "bouillon": [
        (
            "What is bouillon?",
            "Bouillon is a light soup or broth. When it is hot, it can splash and burn, so grown-ups should carry it for little children."
        )
    ],
    "telemarketing": [
        (
            "What is telemarketing?",
            "Telemarketing is when someone calls on the phone to try to sell something. It can be distracting, but grown-ups should still pause risky things before helping children."
        )
    ],
    "hot_liquid": [
        (
            "Why is hot soup dangerous to carry alone?",
            "Hot soup can slosh and spill. Even a small splash can hurt skin, especially if you are climbing or reaching high."
        )
    ],
    "climbing": [
        (
            "Why is it unsafe to climb on wobbly furniture?",
            "Wobbly furniture can tip, slide, or roll. If you are holding something hot, the danger is even bigger because both you and the drink can fall."
        )
    ],
    "adult": [
        (
            "What should a child do with hot food on a high counter?",
            "Call a grown-up and wait. Real courage means asking for help before something spills."
        )
    ],
    "towel": [
        (
            "Why can a towel help with a hot spill?",
            "A towel can help a grown-up hold or steady something safely and wipe up a spill. Children should still let the grown-up do that job."
        )
    ],
}
KNOWLEDGE_ORDER = ["bouillon", "telemarketing", "hot_liquid", "climbing", "adult", "towel"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = display_name(f["instigator"])
    b = display_name(f["cautioner"])
    parent = f["parent"].label_word
    load = f["load_cfg"]
    perch = f["perch_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a rhyming superhero story for a 3-to-5-year-old that includes the words "hoist," "telemarketing," and "bouillon."',
            f"Tell a cautionary story where {a} wants to hoist a hot {load.label} from {perch.phrase}, but {b} stops the mistake before anything spills.",
            f"Write a gentle superhero tale where a telemarketing call distracts a {parent} for a moment, yet the children still choose safety and wait for help.",
        ]
    if outcome == "ouch":
        return [
            'Write a rhyming superhero cautionary story that includes the words "hoist," "telemarketing," and "bouillon," and shows a risky choice leading to a close call.',
            f"Tell a story where {a} tries to hoist hot bouillon while pretending to be a superhero, and the lesson is to call a grown-up instead of climbing.",
            "Write a child-facing cautionary tale with a calm ending image after a hot spill and a safety lesson.",
        ]
    return [
        'Write a short rhyming superhero story that includes the words "hoist," "telemarketing," and "bouillon."',
        f"Tell a cautionary story where {a} ignores a warning and tries to hoist {load.phrase} from {perch.phrase}, but a grown-up fixes the danger.",
        "Write a simple story with a musical, child-facing rhythm and a lesson that real heroes ask for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    load = f["load_cfg"]
    perch = f["perch_cfg"]
    response = f["response"]
    an = display_name(a)
    bn = display_name(b)
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {an} and {bn}, pretending to be superheroes at home. Their {pw} is nearby too, stuck on a telemarketing call at first."
        ),
        (
            f"What did {an} want to do?",
            f"{an} wanted to climb up and hoist the hot {load.label} alone like superhero fuel. That was risky because the {perch.label} could wobble while the bouillon was still hot."
        ),
        (
            f"Why did {bn} warn {an}?",
            f"{bn} warned {an} because the bouillon was hot and the {perch.label} was not steady. If {an} tried to lift it alone, the broth could spill before a grown-up reached them."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How was the danger stopped?",
                f"The danger stopped when {an} listened and climbed back down. Then the children called their {pw}, so no spill happened at all."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"How did the {pw} help?",
                f"The {pw} {response.qa_text.replace('{load}', load.label)}. That quick help stopped the hot spill from becoming a bigger mess."
            )
        )
    else:
        extra = ""
        if f["load"].meters["red_hands"] >= THRESHOLD:
            extra = f" {an}'s fingers were stung a little, so the {pw} cooled them under water."
        qa.append(
            (
                "What was the close call in the story?",
                f"The close call was the hot bouillon splashing when {an} tried to hoist it from the {perch.label}.{extra} The lesson was that pretending to be a hero is not the same as doing a hot, high job alone."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the bouillon cooled and served in safe low cups at the table. The final image shows that the children learned to wait and ask for help instead of grabbing hot things from high places."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"telemarketing"}
    f = world.facts
    tags |= set(f["load_cfg"].tags)
    tags |= set(f["perch_cfg"].tags)
    tags |= set(f["response"].tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in (("hot", ent.hot), ("unstable", ent.unstable), ("safe_tool", ent.safe_tool)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(L, P) :- load(L), perch(P), heat(L, H), instability(P, I), H > 0, I > 0.
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, L, P) :- theme(T), hazard(L, P).

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(H + I + D) :- chosen_load(L), heat(L, H), chosen_perch(P), instability(P, I), delay(D).
resp_power(PW) :- chosen_response(R), power(R, PW).
contained :- not averted, resp_power(PW), severity(SV), PW >= SV.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(ouch) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for load_id, load in LOADS.items():
        lines.append(asp.fact("load", load_id))
        lines.append(asp.fact("heat", load_id, load.heat))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("instability", perch_id, perch.instability))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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

    scenario = "\n".join([
        asp.fact("chosen_load", params.load),
        asp.fact("chosen_perch", params.perch),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    if is_contained(RESPONSES[params.response], LOADS[params.load], PERCHES[params.perch], params.delay):
        return "contained"
    return "ouch"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming superhero cautionary story world: hot bouillon, a risky hoist, and a calm lesson."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra beat before help reaches the spill")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="show valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check Python and ASP parity plus smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.perch and PERCHES[args.perch].instability <= 0:
        load = LOADS[args.load] if args.load else next(iter(LOADS.values()))
        raise StoryError(explain_rejection(load, PERCHES[args.perch]))
    if args.load and args.perch:
        load = LOADS[args.load]
        perch = PERCHES[args.perch]
        if not hazard_at_risk(load, perch):
            raise StoryError(explain_rejection(load, perch))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.load is None or c[1] == args.load)
        and (args.perch is None or c[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, load_id, perch_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    return StoryParams(
        theme=theme_id,
        load=load_id,
        perch=perch_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.load not in LOADS:
        raise StoryError(f"(Unknown load: {params.load})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.response in RESPONSES and RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(LOADS[params.load], PERCHES[params.perch]):
        raise StoryError(explain_rejection(LOADS[params.load], PERCHES[params.perch]))

    world = tell(
        THEMES[params.theme],
        LOADS[params.load],
        PERCHES[params.perch],
        RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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


def asp_verify() -> int:
    rc = 0

    py_gate = set(valid_combos())
    asp_gate = set(asp_valid_combos())
    if py_gate == asp_gate:
        print(f"OK: gate matches valid_combos() ({len(py_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_gate - py_gate:
            print("  only in asp:", sorted(asp_gate - py_gate))
        if py_gate - asp_gate:
            print("  only in python:", sorted(py_gate - asp_gate))

    py_sens = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: asp={sorted(asp_sens)} python={sorted(py_sens)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "{" in sample.story or "}" in sample.story:
            raise StoryError("(Smoke test failed: story text is empty or has unresolved braces.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sens = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (theme, load, perch) combos:\n")
        for theme_id, load_id, perch_id in combos:
            print(f"  {theme_id:15} {load_id:13} {perch_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = (
                f"### {p.instigator} & {p.cautioner}: hoist {p.load} from {p.perch} "
                f"({p.theme}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
