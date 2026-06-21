#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cafe_goalie_bicycle_sound_effects_detective_story.py
===============================================================================

A standalone story world sketch for a tiny child-facing detective story built
around a cafe, a goalie, and a bicycle.

Premise
-------
A child who likes being a goalie visits a neighborhood cafe. A special café bell
goes missing just when a bicycle delivery rider arrives. The child notices sound
effects -- jingle, clink, squeak, hiss -- and uses them like clues in a gentle
detective case. The mystery only works when the chosen hiding place plausibly
makes the bell hard to hear and the chosen clue can honestly reveal where it is.
The ending restores the bell and proves the child learned to listen carefully.

Core reasonableness rule
------------------------
Not every hiding place makes for a real mystery, and not every clue can solve
every hide. The world model enforces two linked constraints:

* A hiding place must muffle or delay the bell enough that it can seem missing.
* The chosen clue must actually be the clue that reveals that hiding place.

So, for example, a bell hidden in a flour sack can be found by a little
"clink-clink" when the sack is bumped, while a bell tucked in a bicycle basket
is better revealed by a bicycle-bell jingle near the door. Invalid combinations
are refused with an explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/cafe_goalie_bicycle_sound_effects_detective_story.py
    python storyworlds/worlds/gpt-5.4/cafe_goalie_bicycle_sound_effects_detective_story.py --hide flour_sack --clue clink
    python storyworlds/worlds/gpt-5.4/cafe_goalie_bicycle_sound_effects_detective_story.py --hide chalkboard --clue clink
    python storyworlds/worlds/gpt-5.4/cafe_goalie_bicycle_sound_effects_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/cafe_goalie_bicycle_sound_effects_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cafe_goalie_bicycle_sound_effects_detective_story.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SHY_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "barista_woman"}
        male = {"boy", "father", "dad", "man", "barista_man"}
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
            "barista_woman": "barista",
            "barista_man": "barista",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    cafe_name: str
    street: str
    goal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidePlace:
    id: str
    label: str
    phrase: str
    near: str
    sound: str
    muffled: bool
    shy: int
    reveal_by: str
    found_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    sound: str
    action: str
    discover_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BikeStyle:
    id: str
    label: str
    phrase: str
    sound: str
    tags: set[str] = field(default_factory=set)


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


def _r_missing_alarm(world: World) -> list[str]:
    bell = world.get("bell")
    if bell.meters["missing"] < THRESHOLD:
        return []
    sig = ("alarm", "bell")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in world.characters():
        if ent.role in {"hero", "barista"}:
            ent.memes["concern"] += 1
    return ["__missing__"]


def _r_detective_mode(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["concern"] < THRESHOLD or hero.memes["goalie_pride"] < THRESHOLD:
        return []
    sig = ("detective_mode", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["focus"] += 1
    hero.memes["detective"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    bell = world.get("bell")
    if bell.meters["found"] < THRESHOLD:
        return []
    sig = ("found", "bell")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in world.characters():
        ent.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_alarm", tag="social", apply=_r_missing_alarm),
    Rule(name="detective_mode", tag="emotional", apply=_r_detective_mode),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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


def hide_is_reasonable(hide: HidePlace) -> bool:
    return hide.muffled and hide.shy >= SHY_MIN


def clue_matches(hide: HidePlace, clue: Clue) -> bool:
    return hide.reveal_by == clue.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for hide_id, hide in HIDES.items():
            if not hide_is_reasonable(hide):
                continue
            for clue_id, clue in CLUES.items():
                if clue_matches(hide, clue):
                    combos.append((setting_id, hide_id, clue_id))
    return combos


def explain_hide_rejection(hide: HidePlace) -> str:
    if not hide.muffled:
        return (
            f"(No story: {hide.phrase} does not really hide a jingly bell. "
            f"It would be seen or heard too easily, so there is no fair mystery.)"
        )
    if hide.shy < SHY_MIN:
        return (
            f"(No story: {hide.phrase} only muffles the bell a tiny bit. "
            f"A detective story needs a clue-worthy hiding place, not an obvious one.)"
        )
    return "(No story: this hiding place does not make a plausible mystery.)"


def explain_clue_rejection(hide: HidePlace, clue: Clue) -> str:
    return (
        f"(No story: the clue '{clue.label}' does not honestly reveal {hide.phrase}. "
        f"That hiding place is solved by {CLUES[hide.reveal_by].label} instead.)"
    )


def predict_search(world: World, hide: HidePlace, clue: Clue) -> dict:
    sim = world.copy()
    bell = sim.get("bell")
    bell.meters["missing"] += 1
    propagate(sim, narrate=False)
    if clue_matches(hide, clue):
        bell.meters["found"] += 1
        bell.meters["missing"] = 0.0
        propagate(sim, narrate=False)
    return {
        "found": bell.meters["found"] >= THRESHOLD,
        "hero_focus": sim.get("hero").memes["focus"],
        "barista_concern": sim.get("barista").memes["concern"],
    }


def introduce(world: World, hero: Entity, barista: Entity, setting: Setting, bike: BikeStyle) -> None:
    hero.memes["joy"] += 1
    hero.memes["goalie_pride"] += 1
    world.say(
        f"After soccer practice, {hero.id} parked {hero.pronoun('possessive')} {bike.label} "
        f"outside {setting.cafe_name} on {setting.street}. {hero.pronoun().capitalize()} still wore "
        f"{hero.pronoun('possessive')} goalie gloves tucked through a backpack strap, because "
        f"{setting.goal} was never far from {hero.pronoun('possessive')} mind."
    )
    world.say(
        f"Inside the cafe, cups clinked, milk hissed, and the door gave a cheerful "
        f'"ding-ding" each time someone came in. {barista.id}, the barista, liked to say '
        f'the little bell made the whole room sound awake.'
    )


def setup_missing_bell(world: World, hero: Entity, barista: Entity) -> None:
    bell = world.get("bell")
    bell.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {barista.id} reached for the counter bell that called waiting customers. "
        f'"Tap-tap," went {barista.pronoun("possessive")} finger on the wood. But there was no bell, '
        f"and no bright ring at all."
    )
    world.say(
        f'"That is strange," {barista.id} said. "{world.get("bell").label.capitalize()} should be right here."'
    )


def declare_case(world: World, hero: Entity, bike: BikeStyle) -> None:
    world.say(
        f"{hero.id} straightened up at once. {hero.pronoun().capitalize()} liked stopping fast balls, "
        f"and now {hero.pronoun()} felt ready to stop a mystery from rolling away. "
        f'Outside, {bike.sound}, and inside {hero.pronoun()} whispered, "This sounds like a case."'
    )


def suspect_list(world: World, hero: Entity, hide: HidePlace) -> None:
    world.say(
        f"{hero.id} looked at the room the way a detective looks at footprints. "
        f"There was flour near the baking shelf, chalk dust by the menu board, and a basket by the door. "
        f"The missing bell could have slipped {hide.near}."
    )


def follow_clue(world: World, hero: Entity, bike: BikeStyle, hide: HidePlace, clue: Clue) -> None:
    pred = predict_search(world, hide, clue)
    world.facts["predicted_focus"] = pred["hero_focus"]
    world.facts["predicted_found"] = pred["found"]
    hero.memes["listening"] += 1
    world.say(
        f"{hero.id} held up one hand like a goalie waiting for a corner kick. "
        f"{hero.pronoun().capitalize()} listened hard. {clue.sound} {clue.discover_text}"
    )
    if clue.id == "jingle":
        world.say(
            f"The sound came from near the door, where {bike.phrase} had just made the room go "
            f"{bike.sound.lower()}."
        )
    elif clue.id == "clink":
        world.say(
            f"It was a tiny sound, but detectives trust tiny sounds when the room goes quiet."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} noticed the scrape before anyone else did, and that made "
            f"{hero.pronoun('object')} feel even more certain."
        )


def discover(world: World, hero: Entity, barista: Entity, hide: HidePlace, clue: Clue) -> None:
    bell = world.get("bell")
    bell.meters["found"] += 1
    bell.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} {clue.action}. {hide.found_text} {hero.pronoun().capitalize()} lifted the bell high. "
        f'"Cling!" it sang at last.'
    )
    world.say(
        f'"Mystery solved," {hero.id} said, and {barista.id} laughed with a long relieved breath.'
    )


def resolution(world: World, hero: Entity, barista: Entity, bike: BikeStyle) -> None:
    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{barista.id} set a warm roll and a cup of cocoa on the table for the young detective. "
        f'"A goalie watches the whole field," {barista.pronoun()} said. "Today you watched the whole cafe."'
    )
    world.say(
        f"On the way home, {hero.id} hopped onto {hero.pronoun('possessive')} {bike.label}. "
        f"{bike.sound} went the wheels and bell, and the sound no longer felt ordinary. "
        f"It felt like a clue waiting to be heard."
    )


def tell(
    setting: Setting,
    hide: HidePlace,
    clue: Clue,
    bike: BikeStyle,
    hero_name: str = "Milo",
    hero_type: str = "boy",
    barista_name: str = "Nia",
    barista_type: str = "barista_woman",
    helper_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["careful", "curious"],
    ))
    barista = world.add(Entity(
        id="barista",
        kind="character",
        type=barista_type,
        label=barista_name,
        role="barista",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the grown-up",
        role="helper",
    ))
    bell = world.add(Entity(
        id="bell",
        type="bell",
        label="counter bell",
        phrase="the little brass counter bell",
        tags={"bell", "sound"},
    ))
    bike_ent = world.add(Entity(
        id="bicycle",
        type="bicycle",
        label=bike.label,
        phrase=bike.phrase,
        tags=set(bike.tags),
    ))

    world.facts["hero_name"] = hero_name
    world.facts["barista_name"] = barista_name

    introduce(world, hero, barista, setting, bike)
    world.para()
    setup_missing_bell(world, hero, barista)
    declare_case(world, hero, bike)
    suspect_list(world, hero, hide)
    world.para()
    follow_clue(world, hero, bike, hide, clue)
    discover(world, hero, barista, hide, clue)
    world.para()
    resolution(world, hero, barista, bike)

    world.facts.update(
        hero=hero,
        barista=barista,
        helper=helper,
        bell=bell,
        bicycle=bike_ent,
        setting=setting,
        hide=hide,
        clue=clue,
        bike=bike,
        solved=bell.meters["found"] >= THRESHOLD,
        predicted_found=world.facts.get("predicted_found", False),
    )
    return world


SETTINGS = {
    "corner_cafe": Setting(
        id="corner_cafe",
        cafe_name="Maple Corner Cafe",
        street="Willow Street",
        goal="keeping everything in view like a net",
        tags={"cafe"},
    ),
    "station_cafe": Setting(
        id="station_cafe",
        cafe_name="Sunny Station Cafe",
        street="Pine Lane",
        goal="guarding any surprise that tried to slip past",
        tags={"cafe"},
    ),
    "garden_cafe": Setting(
        id="garden_cafe",
        cafe_name="Garden Gate Cafe",
        street="Robin Road",
        goal="watching every angle the way a goalie watches a goal",
        tags={"cafe"},
    ),
}

HIDES = {
    "flour_sack": HidePlace(
        id="flour_sack",
        label="flour sack",
        phrase="inside a big paper flour sack",
        near="into the flour sacks by the baking shelf",
        sound='"clink-clink"',
        muffled=True,
        shy=3,
        reveal_by="clink",
        found_text="From inside the flour sack came a small metal knock under the soft flour.",
        tags={"flour", "sound"},
    ),
    "apron_pocket": HidePlace(
        id="apron_pocket",
        label="apron pocket",
        phrase="inside a deep apron pocket",
        near="into the apron hanging on the hook",
        sound='"swick"',
        muffled=True,
        shy=2,
        reveal_by="swish",
        found_text="The apron pocket sagged in a funny little bump, and the bell was tucked safely inside.",
        tags={"apron", "sound"},
    ),
    "bike_basket": HidePlace(
        id="bike_basket",
        label="bicycle basket",
        phrase="inside the bicycle basket by the door",
        near="into the bicycle basket by the door",
        sound='"jingle-jingle"',
        muffled=True,
        shy=2,
        reveal_by="jingle",
        found_text="Beneath a folded napkin in the bicycle basket sat the bell, shining beside the handlebars.",
        tags={"bicycle", "sound"},
    ),
    "chalkboard": HidePlace(
        id="chalkboard",
        label="chalkboard ledge",
        phrase="on the chalkboard ledge",
        near="onto the chalkboard ledge",
        sound='"tick"',
        muffled=False,
        shy=0,
        reveal_by="swish",
        found_text="There it was on the chalkboard ledge.",
        tags={"chalkboard"},
    ),
}

CLUES = {
    "clink": Clue(
        id="clink",
        label="a tiny metal clink",
        sound='"clink... clink..."',
        action="nudged the flour sack with one glove",
        discover_text="Something small answered from the shelf with a careful metal clink.",
        tags={"sound", "metal"},
    ),
    "swish": Clue(
        id="swish",
        label="a pocket swish",
        sound='"swish-swish..."',
        action="touched the hanging apron and felt a weight swing back",
        discover_text="The hanging apron gave a soft swish, as if something heavier than cloth was hiding in it.",
        tags={"sound", "cloth"},
    ),
    "jingle": Clue(
        id="jingle",
        label="a bicycle jingle",
        sound='"jingle-jingle!"',
        action="peeked into the basket by the bicycle handlebars",
        discover_text="Near the door, a bright little jingle answered the bigger bicycle sound.",
        tags={"sound", "bicycle"},
    ),
}

BIKES = {
    "red": BikeStyle(
        id="red",
        label="red bicycle",
        phrase="the red bicycle outside the window",
        sound='"trrring-trrring"',
        tags={"bicycle"},
    ),
    "blue": BikeStyle(
        id="blue",
        label="blue bicycle",
        phrase="the blue bicycle with streamers",
        sound='"tring-tring"',
        tags={"bicycle"},
    ),
    "green": BikeStyle(
        id="green",
        label="green bicycle",
        phrase="the green bicycle with a silver bell",
        sound='"dring-dring"',
        tags={"bicycle"},
    ),
}

HEROES = {
    "girl": ["Lina", "Maya", "Zoe", "Iris", "Nora"],
    "boy": ["Milo", "Ben", "Theo", "Eli", "Noah"],
}
BARISTA_NAMES = ["Nia", "Omar", "June", "Tess", "Ravi"]
TRAITS = ["careful", "curious", "steady", "sharp-eyed", "thoughtful"]


@dataclass
class StoryParams:
    setting: str
    hide: str
    clue: str
    bike: str
    hero_name: str
    hero_type: str
    barista_name: str
    barista_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cafe": [
        (
            "What is a cafe?",
            "A cafe is a place where people can sit, drink something warm or cool, and eat small foods. It often has a counter, tables, and busy sounds."
        )
    ],
    "goalie": [
        (
            "What does a goalie do?",
            "A goalie watches the goal and tries to stop the ball from getting past. A good goalie pays close attention and reacts quickly."
        )
    ],
    "bicycle": [
        (
            "What is a bicycle bell for?",
            "A bicycle bell makes a ringing sound to let people know a bicycle is nearby. It helps riders warn others in a polite, safe way."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues and uses them to solve a mystery. Detectives look carefully and think about what each clue means."
        )
    ],
    "sound": [
        (
            "How can sounds be clues?",
            "Sounds can tell you where something is, what moved, or what was bumped. A tiny jingle or clink can help you notice what eyes missed."
        )
    ],
    "bell": [
        (
            "What is a counter bell?",
            "A counter bell is a small bell on a desk or counter that makes a clear ring when someone taps it. People use it to get attention politely."
        )
    ],
    "flour": [
        (
            "Why would metal sound different in flour?",
            "Flour is soft and muffles sound, so metal inside it may only make a quiet clink. That makes the sound small but still real."
        )
    ],
    "apron": [
        (
            "What is an apron?",
            "An apron is a cloth people wear over their clothes to help keep them clean while they cook or work."
        )
    ],
}
KNOWLEDGE_ORDER = ["cafe", "goalie", "bicycle", "detective", "sound", "bell", "flour", "apron"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    barista = f["barista"]
    setting = f["setting"]
    hide = f["hide"]
    clue = f["clue"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old set in a cafe that includes the words "cafe", "goalie", and "bicycle", and uses sound effects as clues.',
        f"Tell a tiny mystery where {hero.label}, a child who thinks like a goalie, notices sounds in {setting.cafe_name} and finds a missing bell {hide.phrase}.",
        f'Write a child-facing detective story where a barista, a bicycle, and the sound {clue.sound} help solve a missing-object case.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    barista = f["barista"]
    setting = f["setting"]
    hide = f["hide"]
    clue = f["clue"]
    bike = f["bike"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child who thinks like a goalie, and {barista.label}, the barista at {setting.cafe_name}. They work together in the cafe when the counter bell goes missing."
        ),
        (
            "What was the mystery?",
            "The little counter bell was missing from the cafe counter. That mattered because the bell was part of how the cafe called and welcomed people."
        ),
        (
            f"Why did {hero.label} act like a detective?",
            f"{hero.label} already liked watching carefully like a goalie, so the missing bell made {hero.pronoun('object')} focus even more. Instead of guessing wildly, {hero.pronoun()} listened for a real clue."
        ),
        (
            "How did sound help solve the mystery?",
            f"The clue was {clue.label}: {clue.sound}. That sound matched where the bell was hidden, so listening carefully led straight to the right place."
        ),
        (
            "Where was the bell found?",
            f"The bell was found {hide.phrase}. {hide.found_text} That is why the sound clue mattered more than just looking quickly around the room."
        ),
        (
            "How did the story end?",
            f"The bell rang again, the barista felt relieved, and {hero.label} rode home on {hero.pronoun('possessive')} {bike.label}. The ending shows that careful listening turned an ordinary afternoon into a solved detective case."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cafe", "goalie", "bicycle", "detective", "sound", "bell"}
    if f["hide"].id == "flour_sack":
        tags.add("flour")
    if f["hide"].id == "apron_pocket":
        tags.add("apron")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="corner_cafe",
        hide="flour_sack",
        clue="clink",
        bike="red",
        hero_name="Milo",
        hero_type="boy",
        barista_name="Nia",
        barista_type="barista_woman",
        helper_type="mother",
        trait="careful",
        seed=101,
    ),
    StoryParams(
        setting="garden_cafe",
        hide="bike_basket",
        clue="jingle",
        bike="green",
        hero_name="Lina",
        hero_type="girl",
        barista_name="Ravi",
        barista_type="barista_man",
        helper_type="father",
        trait="sharp-eyed",
        seed=102,
    ),
    StoryParams(
        setting="station_cafe",
        hide="apron_pocket",
        clue="swish",
        bike="blue",
        hero_name="Theo",
        hero_type="boy",
        barista_name="June",
        barista_type="barista_woman",
        helper_type="mother",
        trait="thoughtful",
        seed=103,
    ),
]


def outcome_of(params: StoryParams) -> str:
    if not hide_is_reasonable(HIDES[params.hide]):
        return "invalid"
    return "solved" if clue_matches(HIDES[params.hide], CLUES[params.clue]) else "unsolved"


ASP_RULES = r"""
reasonable_hide(H) :- hide(H), muffled(H), shy(H, S), shy_min(M), S >= M.
match(H, C) :- reveal_by(H, C).
valid(S, H, C) :- setting(S), reasonable_hide(H), clue(C), match(H, C).

solved :- chosen_hide(H), chosen_clue(C), reasonable_hide(H), match(H, C).
outcome(solved) :- solved.
outcome(invalid) :- chosen_hide(H), not reasonable_hide(H).
outcome(unsolved) :- chosen_hide(H), reasonable_hide(H), chosen_clue(C), not match(H, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, hide in HIDES.items():
        lines.append(asp.fact("hide", hid))
        if hide.muffled:
            lines.append(asp.fact("muffled", hid))
        lines.append(asp.fact("shy", hid, hide.shy))
        lines.append(asp.fact("reveal_by", hid, hide.reveal_by))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    lines.append(asp.fact("shy_min", SHY_MIN))
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
        asp.fact("chosen_hide", params.hide),
        asp.fact("chosen_clue", params.clue),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cafe mystery solved by a child goalie listening for sound clues."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hide", choices=HIDES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--bike", choices=BIKES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--barista-name")
    ap.add_argument("--barista-type", choices=["barista_woman", "barista_man"])
    ap.add_argument("--helper-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hide is not None and not hide_is_reasonable(HIDES[args.hide]):
        raise StoryError(explain_hide_rejection(HIDES[args.hide]))
    if args.hide is not None and args.clue is not None:
        if not clue_matches(HIDES[args.hide], CLUES[args.clue]):
            raise StoryError(explain_clue_rejection(HIDES[args.hide], CLUES[args.clue]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.hide is None or c[1] == args.hide)
        and (args.clue is None or c[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hide_id, clue_id = rng.choice(sorted(combos))
    bike = args.bike or rng.choice(sorted(BIKES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HEROES[hero_type])
    barista_name = args.barista_name or rng.choice(BARISTA_NAMES)
    barista_type = args.barista_type or rng.choice(["barista_woman", "barista_man"])
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        hide=hide_id,
        clue=clue_id,
        bike=bike,
        hero_name=hero_name,
        hero_type=hero_type,
        barista_name=barista_name,
        barista_type=barista_type,
        helper_type=helper_type,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.hide not in HIDES:
        raise StoryError(f"(Unknown hide: {params.hide})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.bike not in BIKES:
        raise StoryError(f"(Unknown bike: {params.bike})")
    if not hide_is_reasonable(HIDES[params.hide]):
        raise StoryError(explain_hide_rejection(HIDES[params.hide]))
    if not clue_matches(HIDES[params.hide], CLUES[params.clue]):
        raise StoryError(explain_clue_rejection(HIDES[params.hide], CLUES[params.clue]))

    world = tell(
        setting=SETTINGS[params.setting],
        hide=HIDES[params.hide],
        clue=CLUES[params.clue],
        bike=BIKES[params.bike],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        barista_name=params.barista_name,
        barista_type=params.barista_type,
        helper_type=params.helper_type,
    )
    world.get("hero").traits.append(params.trait)
    return StorySample(
        params=params,
        story=world.render().replace("hero", world.facts["hero_name"]),
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
        print(f"{len(combos)} compatible (setting, hide, clue) combos:\n")
        for setting, hide, clue in combos:
            print(f"  {setting:12} {hide:12} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.hide} via {p.clue} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
