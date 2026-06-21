#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/roam_suspicious_solitaire_repetition_mystery_to_solve.py
===================================================================================

A standalone storyworld about a little superhero solving a small repeated mystery.

Premise
-------
A child on pretend superhero patrol keeps finding that one small shiny object
goes missing each day. A grown-up nearby is playing solitaire, the child begins
to feel suspicious, and the child starts to roam from place to place looking
for repeated clues. The world model decides whether the chosen culprit could
really carry the object and reach the hiding place, then renders a complete
mystery story with a bright superhero ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/roam_suspicious_solitaire_repetition_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/roam_suspicious_solitaire_repetition_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/roam_suspicious_solitaire_repetition_mystery_to_solve.py --asp
    python storyworlds/worlds/gpt-5.4/roam_suspicious_solitaire_repetition_mystery_to_solve.py --verify
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
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    roam_line: str
    hideouts: set[str] = field(default_factory=set)


@dataclass
class ShinyThing:
    id: str
    label: str
    phrase: str
    size: str
    costume_place: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    type: str
    carry: set[str] = field(default_factory=set)
    reach: set[str] = field(default_factory=set)
    trail: str = ""
    motive: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    clue_found: str
    roomy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    entrance: str
    comfort: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspicion(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.meters["missing_count"] < 2 or hero.memes["suspicious"] >= THRESHOLD:
        return []
    world.fired.add(("suspicion",))
    hero.memes["suspicious"] += 1
    return ["__suspicious__"]


def _r_clue_to_plan(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.meters["clues"] < 1 or hero.memes["detective"] >= THRESHOLD:
        return []
    world.fired.add(("plan",))
    hero.memes["detective"] += 1
    return ["__plan__"]


CAUSAL_RULES = [
    Rule(name="suspicion", tag="mystery", apply=_r_suspicion),
    Rule(name="plan", tag="mystery", apply=_r_clue_to_plan),
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
        for s in produced:
            world.say(s)
    return produced


def can_hide(culprit: Culprit, shiny: ShinyThing, hideout: Hideout, setting: Setting) -> bool:
    return shiny.size in culprit.carry and hideout.id in culprit.reach and hideout.id in setting.hideouts


def solver_mode(helper: Helper, culprit: Culprit, hideout: Hideout) -> str:
    if helper.id == "self" and hideout.id != "high_shelf":
        return "solo"
    if culprit.id == "kitten" and hideout.id == "under_sofa":
        return "solo"
    return "team"


def predict_reasonable(setting: Setting, shiny: ShinyThing, culprit: Culprit, hideout: Hideout) -> dict:
    return {
        "possible": can_hide(culprit, shiny, hideout, setting),
        "mode": solver_mode(HELPERS["self"], culprit, hideout),
    }


def patrol_setup(world: World, hero: Entity, helper_ent: Entity, setting: Setting, shiny: ShinyThing) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} tied on a bright cape and declared that the day needed a superhero."
    )
    world.say(
        f"In {setting.place}, {hero.pronoun()} liked to roam from room to room on patrol, "
        f"checking pillows, peeking behind doors, and making sure everything felt brave and tidy."
    )
    world.say(
        f"On a low stool nearby, {helper_ent.label} was playing solitaire, turning cards one by one while "
        f"{hero.id} kept watch over {hero.pronoun('possessive')} {shiny.phrase}."
    )


def repeated_loss(world: World, hero: Entity, shiny: ShinyThing) -> None:
    hero.meters["missing_count"] += 1
    world.say(
        f"On Monday, one {shiny.label} vanished from {hero.pronoun('possessive')} {shiny.costume_place}. "
        f"On Tuesday, it happened again. On Wednesday, yet another was gone."
    )
    propagate(world, narrate=False)
    if hero.memes["suspicious"] >= THRESHOLD:
        world.say(
            f"That repetition made {hero.id} feel suspicious. A true hero knew that the same odd thing "
            f"happening again and again meant a mystery was asking to be solved."
        )


def inspect_scene(world: World, hero: Entity, culprit: Culprit, shiny: ShinyThing) -> None:
    hero.meters["clues"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} did not stomp or shout. Instead, {hero.pronoun()} knelt by the stool, looked at the neat "
        f"solitaire piles, and noticed something else: {culprit.trail}."
    )
    world.say(
        f'"That is very suspicious," {hero.pronoun()} whispered. "My {shiny.label} do not walk away by themselves."'
    )


def roam_search(world: World, hero: Entity, setting: Setting, hideout: Hideout) -> None:
    hero.memes["brave"] += 1
    world.say(
        f"So Captain {hero.id} began to roam. {setting.roam_line}"
    )
    world.say(
        f"At last the trail led toward {hideout.phrase}, where {hero.pronoun()} spotted {hideout.clue_found}."
    )


def ask_for_help(world: World, hero: Entity, helper_ent: Entity, helper: Helper) -> None:
    hero.memes["trust"] += 1
    helper_ent.memes["care"] += 1
    world.say(
        f"{helper.entrance} {helper_ent.label.capitalize()} came over and listened carefully instead of laughing."
    )
    world.say(
        f'{helper_ent.label.capitalize()} said, "{helper.comfort} Let us follow the clue together."'
    )


def reveal(world: World, hero: Entity, helper_ent: Entity, shiny: ShinyThing,
           culprit_ent: Entity, culprit: Culprit, hideout: Hideout, mode: str) -> None:
    culprit_ent.meters["found"] += 1
    hero.meters["solved"] += 1
    world.say(
        f"Inside {hideout.phrase} lay the missing {shiny.label}, all three of them, shining in a little pile."
    )
    if mode == "solo":
        world.say(
            f"Curled beside them was {culprit.phrase}. {hero.id} had solved the mystery alone, and the answer was simple: "
            f"{culprit.motive}."
        )
    else:
        world.say(
            f"Behind them peeped {culprit.phrase}. Together {hero.id} and {helper_ent.label} solved the mystery: "
            f"{culprit.motive}."
        )


def gentle_fix(world: World, hero: Entity, helper_ent: Entity, shiny: ShinyThing,
               culprit: Culprit, helper: Helper, mode: str) -> None:
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f"{helper_ent.label.capitalize()} lifted the shiny things out gently and made a safe little tin just for them."
    )
    world.say(
        f"No one called {culprit.label} naughty. {helper_ent.label.capitalize()} explained that {culprit.label} liked small "
        f"sparkly treasures and had been collecting them without understanding."
    )
    if mode == "solo":
        world.say(
            f"{hero.id} stood taller in {hero.pronoun('possessive')} cape. Being a superhero, {hero.pronoun()} decided, meant "
            f"using sharp eyes and a kind heart at the same time."
        )
    else:
        world.say(
            f"{hero.id} grinned. Even superheroes, {hero.pronoun()} decided, can ask for help and still be brave."
        )


def bright_ending(world: World, hero: Entity, helper_ent: Entity, shiny: ShinyThing) -> None:
    world.say(
        f"That evening, while the solitaire cards clicked softly on the table again, the {shiny.label} stayed safe in their tin."
    )
    world.say(
        f"{hero.id} roamed past on one more happy patrol, no longer suspicious now that the mystery was solved."
    )


def tell(setting: Setting, shiny: ShinyThing, culprit: Culprit, hideout: Hideout,
         helper: Helper, hero_name: str = "Nova", hero_type: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper.type, label=helper.label, role="helper"))
    culprit_ent = world.add(Entity(id="culprit", kind="thing", type=culprit.type, label=culprit.label, role="culprit"))
    world.facts["hero_name"] = hero_name

    patrol_setup(world, hero, helper_ent, setting, shiny)
    world.para()
    repeated_loss(world, hero, shiny)
    inspect_scene(world, hero, culprit, shiny)
    world.para()
    roam_search(world, hero, setting, hideout)
    mode = solver_mode(helper, culprit, hideout)
    if mode == "team":
        ask_for_help(world, hero, helper_ent, helper)
    world.para()
    reveal(world, hero, helper_ent, shiny, culprit_ent, culprit, hideout, mode)
    gentle_fix(world, hero, helper_ent, shiny, culprit, helper, mode)
    world.para()
    bright_ending(world, hero, helper_ent, shiny)

    world.facts.update(
        hero=hero,
        helper_ent=helper_ent,
        culprit_ent=culprit_ent,
        setting=setting,
        shiny=shiny,
        culprit=culprit,
        hideout=hideout,
        helper=helper,
        mode=mode,
        repeated=hero.meters["missing_count"] >= 3,
        suspicious=hero.memes["suspicious"] >= THRESHOLD,
        solved=hero.meters["solved"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "apartment": Setting(
        id="apartment",
        place="the sunny apartment",
        roam_line="Past the couch, past the hall shoes, and past the fern by the window, the little hero padded with detective steps.",
        hideouts={"under_sofa", "shoe_closet"},
    ),
    "house": Setting(
        id="house",
        place="the creaky little house",
        roam_line="Up the hall, around the dining table, and past the coat hooks, the tiny hero searched with cape fluttering behind.",
        hideouts={"under_sofa", "laundry_basket", "shoe_closet"},
    ),
    "clubhouse": Setting(
        id="clubhouse",
        place="the community clubhouse",
        roam_line="Across the reading rug, behind the folding chairs, and near the craft shelves, the little hero searched for the truth.",
        hideouts={"laundry_basket", "high_shelf"},
    ),
}

SHINY_THINGS = {
    "star_button": ShinyThing(
        id="star_button",
        label="star button",
        phrase="belt of golden star buttons",
        size="tiny",
        costume_place="hero belt",
        clue="one thread of gold glitter",
        tags={"shiny", "costume"},
    ),
    "moon_gem": ShinyThing(
        id="moon_gem",
        label="moon gem",
        phrase="cape clasp with little moon gems",
        size="tiny",
        costume_place="cape clasp",
        clue="a silver sparkle in the dust",
        tags={"shiny", "costume"},
    ),
    "badge_disk": ShinyThing(
        id="badge_disk",
        label="badge disk",
        phrase="pocket pouch of round badge disks",
        size="small",
        costume_place="pouch",
        clue="one small round mark on the floor",
        tags={"shiny", "costume"},
    ),
}

CULPRITS = {
    "kitten": Culprit(
        id="kitten",
        label="kitten",
        phrase="the gray kitten with bright whiskers",
        type="animal",
        carry={"tiny"},
        reach={"under_sofa", "laundry_basket"},
        trail="a tiny jingle from under the couch and one soft pawprint by the stool",
        motive="the kitten loved batting sparkly things and hiding them in cozy places",
        tags={"pet", "kitten"},
    ),
    "ferret": Culprit(
        id="ferret",
        label="ferret",
        phrase="the cream-colored ferret with a clever nose",
        type="animal",
        carry={"tiny", "small"},
        reach={"under_sofa", "shoe_closet", "laundry_basket"},
        trail="a slipping little rustle near the wall and a shiny thread leading away",
        motive="the ferret liked to collect bright treasures for a secret nest",
        tags={"pet", "ferret"},
    ),
    "magpie_toy": Culprit(
        id="magpie_toy",
        label="wind-up magpie toy",
        phrase="the black-and-white wind-up magpie toy",
        type="toy",
        carry={"tiny"},
        reach={"high_shelf"},
        trail="small clockwork clicks and one straight line of wheel marks",
        motive="the toy had been bumping shiny pieces along until they gathered in one hidden corner",
        tags={"toy", "magpie"},
    ),
}

HIDEOUTS = {
    "under_sofa": Hideout(
        id="under_sofa",
        label="under the sofa",
        phrase="the dusty space under the sofa",
        clue_found="a silver sparkle beside a lost crayon",
        roomy=False,
        tags={"sofa"},
    ),
    "laundry_basket": Hideout(
        id="laundry_basket",
        label="the laundry basket",
        phrase="the warm laundry basket",
        clue_found="a flash of gold between two socks",
        roomy=True,
        tags={"laundry"},
    ),
    "shoe_closet": Hideout(
        id="shoe_closet",
        label="the shoe closet",
        phrase="the shoe closet by the door",
        clue_found="a bright wink beside the rain boots",
        roomy=True,
        tags={"shoes"},
    ),
    "high_shelf": Hideout(
        id="high_shelf",
        label="the high shelf",
        phrase="the high shelf above the game cupboard",
        clue_found="a glittering edge just out of reach",
        roomy=False,
        tags={"shelf"},
    ),
}

HELPERS = {
    "self": Helper(
        id="self",
        label="the grown-up",
        type="grandmother",
        entrance="",
        comfort="You noticed a real clue.",
        tags={"solo"},
    ),
    "grandma": Helper(
        id="grandma",
        label="grandma",
        type="grandmother",
        entrance="Just then Grandma set down her solitaire cards.",
        comfort="That was careful noticing.",
        tags={"grandma", "solitaire"},
    ),
    "grandpa": Helper(
        id="grandpa",
        label="grandpa",
        type="grandfather",
        entrance="Just then Grandpa set down his solitaire cards.",
        comfort="That was careful noticing.",
        tags={"grandpa", "solitaire"},
    ),
    "mom": Helper(
        id="mom",
        label="mom",
        type="mother",
        entrance="Just then Mom looked up from the table where the solitaire cards lay in neat rows.",
        comfort="That was careful noticing.",
        tags={"mom", "solitaire"},
    ),
}

GIRL_NAMES = ["Nova", "Ruby", "Maya", "Skye", "Luna", "Zoe", "Ivy", "Mina"]
BOY_NAMES = ["Ace", "Leo", "Finn", "Max", "Theo", "Eli", "Jude", "Noah"]


@dataclass
class StoryParams:
    setting: str
    shiny: str
    culprit: str
    hideout: str
    helper: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for shiny_id, shiny in SHINY_THINGS.items():
            for culprit_id, culprit in CULPRITS.items():
                for hideout_id, hideout in HIDEOUTS.items():
                    if can_hide(culprit, shiny, hideout, setting):
                        combos.append((setting_id, shiny_id, culprit_id, hideout_id))
    return combos


KNOWLEDGE = {
    "solitaire": [
        (
            "What is solitaire?",
            "Solitaire is a card game one person can play alone. People sort the cards into piles in a careful order."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem with an answer that is hidden at first. You solve it by noticing clues and thinking carefully."
        )
    ],
    "suspicious": [
        (
            "What does suspicious mean?",
            "Suspicious means something feels odd or not quite right. It can be a sign that you should stop and look for clues."
        )
    ],
    "roam": [
        (
            "What does roam mean?",
            "To roam means to move around from place to place without staying in one spot. A child might roam while exploring a room or a yard."
        )
    ],
    "kitten": [
        (
            "Why do kittens bat at shiny things?",
            "Kittens like things that glint or jiggle because they notice quick little movements. To a kitten, a shiny object can feel like a toy."
        )
    ],
    "ferret": [
        (
            "Why do ferrets hide little objects?",
            "Ferrets often like carrying small things away and tucking them into secret places. It is part of their curious, nest-making behavior."
        )
    ],
    "magpie": [
        (
            "Why is a magpie toy linked with shiny things in stories?",
            "Magpies are often imagined as liking bright objects, so a magpie toy makes a playful mystery clue. In stories, that helps children guess the answer."
        )
    ],
    "kindness": [
        (
            "Why is it good to solve a problem gently?",
            "When you solve a problem gently, you protect feelings as well as things. Kindness helps everyone learn what happened without making the moment worse."
        )
    ],
}
KNOWLEDGE_ORDER = ["solitaire", "mystery", "suspicious", "roam", "kitten", "ferret", "magpie", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    culprit = f["culprit"]
    shiny = f["shiny"]
    return [
        f'Write a superhero story for a 3-to-5-year-old that uses the words "roam," "suspicious," and "solitaire."',
        f"Tell a gentle mystery-to-solve story where {hero.label} notices the same {shiny.label} going missing again and again and follows clues to the answer.",
        f"Write a bright cape-and-clue story where a repeated disappearance turns out to be caused by {culprit.label}, and the child solves it with kindness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    shiny = f["shiny"]
    culprit = f["culprit"]
    hideout = f["hideout"]
    helper = f["helper"]
    mode = f["mode"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a little superhero on patrol. The story also includes {helper.label}, some solitaire cards, and a small mystery about the missing {shiny.label}."
        ),
        (
            f"What kept happening to the {shiny.label}?",
            f"One {shiny.label} went missing again and again on different days. That repetition is what made the mystery feel real instead of like one simple mistake."
        ),
        (
            f"Why did {hero.label} feel suspicious?",
            f"{hero.label} noticed that the same kind of shiny thing kept disappearing, and then found a repeating clue near the stool and the solitaire table. The pattern told {hero.pronoun('object')} that someone or something was carrying them away."
        ),
        (
            f"How did {hero.label} try to solve the mystery?",
            f"{hero.label} began to roam carefully from place to place and followed the clue trail instead of guessing wildly. That calm searching led straight to {hideout.label}."
        ),
    ]
    if mode == "solo":
        qa.append(
            (
                "Did the hero solve the mystery alone?",
                f"Yes. {hero.label} found the hidden pile without needing extra hands. The answer was {culprit.label}, who had been hiding the shiny things in {hideout.label}."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.label} ask {helper.label} for help?",
                f"{hero.label} had found a real clue, but the hiding place or the moment called for a grown-up's help. Working together let them reach the hiding place safely and solve the mystery kindly."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the mystery solved and the missing {shiny.label} stored safely in a tin. {hero.label} kept patrolling happily, no longer suspicious because the answer was finally clear."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"solitaire", "mystery", "suspicious", "roam", "kindness"}
    culprit_id = f["culprit"].id
    if culprit_id == "kitten":
        tags.add("kitten")
    elif culprit_id == "ferret":
        tags.add("ferret")
    else:
        tags.add("magpie")
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
    for ent in list(world.entities.values()):
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
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="apartment",
        shiny="star_button",
        culprit="kitten",
        hideout="under_sofa",
        helper="self",
        hero_name="Nova",
        hero_type="girl",
    ),
    StoryParams(
        setting="house",
        shiny="badge_disk",
        culprit="ferret",
        hideout="shoe_closet",
        helper="grandpa",
        hero_name="Ace",
        hero_type="boy",
    ),
    StoryParams(
        setting="clubhouse",
        shiny="moon_gem",
        culprit="magpie_toy",
        hideout="high_shelf",
        helper="mom",
        hero_name="Ruby",
        hero_type="girl",
    ),
    StoryParams(
        setting="house",
        shiny="moon_gem",
        culprit="ferret",
        hideout="laundry_basket",
        helper="grandma",
        hero_name="Finn",
        hero_type="boy",
    ),
]


def explain_rejection(setting: Setting, shiny: ShinyThing, culprit: Culprit, hideout: Hideout) -> str:
    if hideout.id not in setting.hideouts:
        return (
            f"(No story: {hideout.label} is not a plausible hiding place in {setting.place}. "
            f"Pick one of {sorted(setting.hideouts)} instead.)"
        )
    if shiny.size not in culprit.carry:
        return (
            f"(No story: {culprit.label} could not carry a {shiny.size} object like the {shiny.label}. "
            f"Choose a smaller shiny thing or a stronger culprit.)"
        )
    if hideout.id not in culprit.reach:
        return (
            f"(No story: {culprit.label} could not reasonably reach {hideout.label}. "
            f"Pick a hiding place the culprit can actually get to.)"
        )
    return "(No story: that mystery setup is not physically reasonable.)"


ASP_RULES = r"""
can_hide(C, S, H, St) :- culprit(C), shiny(S), hideout(H), setting(St),
                         carry(C, Size), size(S, Size),
                         reach(C, H), in_setting(St, H).

solo_mode(C, H) :- culprit(C), hideout(H), C = kitten, H = under_sofa.
solo_mode(C, H) :- culprit(C), hideout(H), H != high_shelf.

team_mode(C, H) :- can_hide(C, _, H, _), not solo_mode(C, H).

valid(St, S, C, H) :- can_hide(C, S, H, St).

mode(solo) :- chosen_culprit(C), chosen_hideout(H), helper(self), solo_mode(C, H).
mode(team) :- chosen_culprit(C), chosen_hideout(H), helper(Hp), Hp != self.
mode(team) :- chosen_culprit(C), chosen_hideout(H), helper(self), not solo_mode(C, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for hideout_id in sorted(setting.hideouts):
            lines.append(asp.fact("in_setting", setting_id, hideout_id))
    for shiny_id, shiny in SHINY_THINGS.items():
        lines.append(asp.fact("shiny", shiny_id))
        lines.append(asp.fact("size", shiny_id, shiny.size))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for size in sorted(culprit.carry):
            lines.append(asp.fact("carry", culprit_id, size))
        for hideout_id in sorted(culprit.reach):
            lines.append(asp.fact("reach", culprit_id, hideout_id))
    for hideout_id in HIDEOUTS:
        lines.append(asp.fact("hideout", hideout_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper_name", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_mode(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show mode/1."))
    atoms = asp.atoms(model, "mode")
    return atoms[0][0] if atoms else "?"


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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        py = solver_mode(HELPERS[params.helper], CULPRITS[params.culprit], HIDEOUTS[params.hideout])
        cl = asp_mode(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: solver mode matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} solver modes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a little superhero solves a repeated shiny-object mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shiny", choices=SHINY_THINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mystery setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.shiny and args.culprit and args.hideout:
        setting = SETTINGS[args.setting]
        shiny = SHINY_THINGS[args.shiny]
        culprit = CULPRITS[args.culprit]
        hideout = HIDEOUTS[args.hideout]
        if not can_hide(culprit, shiny, hideout, setting):
            raise StoryError(explain_rejection(setting, shiny, culprit, hideout))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.shiny is None or c[1] == args.shiny)
        and (args.culprit is None or c[2] == args.culprit)
        and (args.hideout is None or c[3] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, shiny_id, culprit_id, hideout_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_options = sorted(HELPERS.keys())
    mode_if_self = solver_mode(HELPERS["self"], CULPRITS[culprit_id], HIDEOUTS[hideout_id])
    if args.helper:
        helper_id = args.helper
        if helper_id == "self" and mode_if_self != "solo":
            raise StoryError("(No story: this mystery needs a grown-up helper to reach or confirm the hiding place.)")
    else:
        if mode_if_self == "solo":
            helper_id = rng.choice(["self", "grandma", "grandpa"])
        else:
            helper_id = rng.choice([h for h in helper_options if h != "self"])

    return StoryParams(
        setting=setting_id,
        shiny=shiny_id,
        culprit=culprit_id,
        hideout=hideout_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.shiny not in SHINY_THINGS:
        raise StoryError(f"Unknown shiny object: {params.shiny}")
    if params.culprit not in CULPRITS:
        raise StoryError(f"Unknown culprit: {params.culprit}")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"Unknown hideout: {params.hideout}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    setting = SETTINGS[params.setting]
    shiny = SHINY_THINGS[params.shiny]
    culprit = CULPRITS[params.culprit]
    hideout = HIDEOUTS[params.hideout]
    helper = HELPERS[params.helper]

    if not can_hide(culprit, shiny, hideout, setting):
        raise StoryError(explain_rejection(setting, shiny, culprit, hideout))
    if helper.id == "self" and solver_mode(helper, culprit, hideout) != "solo":
        raise StoryError("(No story: this mystery needs a grown-up helper to reach or confirm the hiding place.)")

    world = tell(
        setting=setting,
        shiny=shiny,
        culprit=culprit,
        hideout=hideout,
        helper=helper,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
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
        print(asp_program("", "#show valid/4.\n#show mode/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, shiny, culprit, hideout) combos:\n")
        for setting_id, shiny_id, culprit_id, hideout_id in combos:
            print(f"  {setting_id:10} {shiny_id:12} {culprit_id:12} {hideout_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.culprit} hid {p.shiny} in {p.hideout} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
