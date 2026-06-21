#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/derive_darling_sodium_bad_ending_mystery.py
======================================================================

A standalone storyworld for a small child-facing mystery with a bad ending:
a child detective follows a salty clue trail at night, tries to derive who
took a missing snack, and makes a hasty choice that spoils a surprise and
leads to tears instead of triumph.

The world model keeps the mystery grounded in physical state:
- a snack can leave visible crumbs
- a hiding place can be reachable only with a stool
- climbing while sleepy and excited can cause a spill
- a spoiled surprise creates the sad ending image

The seed words appear naturally in the story world:
- "derive" in the detective reasoning beat
- "darling" in the grown-up's soft response
- "sodium" in the explanation of the salty crumbs

Run it
------
    python storyworlds/worlds/gpt-5.4/derive_darling_sodium_bad_ending_mystery.py
    python storyworlds/worlds/gpt-5.4/derive_darling_sodium_bad_ending_mystery.py --all
    python storyworlds/worlds/gpt-5.4/derive_darling_sodium_bad_ending_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/derive_darling_sodium_bad_ending_mystery.py --verify
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
    movable: bool = False
    reachable: bool = True
    # shared state axes
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


@dataclass
class MysteryTheme:
    id: str
    missing_name: str
    opening_image: str
    clue_name: str
    clue_desc: str
    scene_line: str
    discovery_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    crumb_kind: str
    salty: bool
    sodium_wording: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    type: str
    motive: str
    careful: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    high: bool
    wobble_risk: int
    surprise_object: str
    spill_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    uses_stool: bool
    sense: int
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


def _r_notice_crumbs(world: World) -> list[str]:
    snack = world.get("snack")
    clue = world.get("clue")
    if snack.meters["crumbs_left"] < THRESHOLD:
        return []
    sig = ("noticed_crumbs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["visible"] += 1
    return []


def _r_stool_risk(world: World) -> list[str]:
    child = world.get("detective")
    place = world.get("place")
    method = world.get("method")
    if method.meters["used"] < THRESHOLD or not method.attrs.get("uses_stool"):
        return []
    sig = ("stool_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["height"] += 1
    child.meters["risk"] += float(place.attrs.get("wobble_risk", 0))
    child.memes["worry"] += 1
    return []


def _r_spill_surprise(world: World) -> list[str]:
    child = world.get("detective")
    place = world.get("place")
    if child.meters["risk"] < THRESHOLD:
        return []
    sig = ("spill_surprise",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["spilled"] += 1
    world.get("surprise").meters["ruined"] += 1
    child.memes["sadness"] += 1
    child.memes["guilt"] += 1
    world.get("parent").memes["work"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="notice_crumbs", tag="physical", apply=_r_notice_crumbs),
    Rule(name="stool_risk", tag="physical", apply=_r_stool_risk),
    Rule(name="spill_surprise", tag="physical", apply=_r_spill_surprise),
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
        for s in produced:
            world.say(s)
    return produced


def clue_exists(snack: Snack, culprit: Culprit) -> bool:
    return snack.salty and not culprit.careful


def risky_path(method: Method, place: HidingPlace) -> bool:
    return method.uses_stool and place.high


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for theme_id in THEMES:
        for snack_id, snack in SNACKS.items():
            for culprit_id, culprit in CULPRITS.items():
                if not clue_exists(snack, culprit):
                    continue
                for place_id, place in HIDING_PLACES.items():
                    for method_id, method in METHODS.items():
                        if method.sense < SENSE_MIN:
                            continue
                        if risky_path(method, place):
                            combos.append((theme_id, snack_id, culprit_id, place_id, method_id))
    return combos


def predict_misstep(world: World) -> dict:
    sim = world.copy()
    sim.get("method").meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": sim.get("place").meters["spilled"] >= THRESHOLD,
        "ruined": sim.get("surprise").meters["ruined"] >= THRESHOLD,
        "risk": sim.get("detective").meters["risk"],
    }


def introduce(world: World, detective: Entity, helper: Entity, theme: MysteryTheme, parent: Entity) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{theme.opening_image} {theme.scene_line} {detective.id} loved tiny mysteries, "
        f"and {helper.id} always padded after {detective.pronoun('object')} to see what would happen next."
    )
    world.say(theme.discovery_line)
    world.say(
        f'"A real case," whispered {detective.id}. "{theme.missing_name} is gone."'
    )
    world.say(
        f'{helper.id} tucked close and asked, "Who took it?"'
    )
    world.facts["parent_word"] = parent.label_word


def lay_clue(world: World, detective: Entity, snack: Snack, culprit: Culprit, theme: MysteryTheme) -> None:
    world.get("snack").meters["crumbs_left"] += 1
    propagate(world, narrate=False)
    world.say(
        f"On the floor below the cupboard lay {theme.clue_desc}. {detective.id} crouched down and touched one with one careful finger."
    )
    world.say(
        f'"We can derive a clue from this," {detective.pronoun()} said. '
        f'"These are {snack.crumb_kind}, and they taste salty."'
    )
    world.say(
        f"The little trail pointed toward {world.get('place').phrase}, as if it wanted to tell the secret all by itself."
    )
    world.facts["guessed_culprit"] = culprit.label


def explain_sodium(world: World, helper: Entity, snack: Snack) -> None:
    helper.memes["wonder"] += 1
    world.say(
        f'"Why are they so salty?" asked {helper.id}.'
    )
    world.say(
        f'{world.get("parent").label_word.capitalize()} had said before that {snack.sodium_wording}. '
        f'{helper.id} remembered the word sodium because it sounded big and important.'
    )


def follow_trail(world: World, detective: Entity, helper: Entity, place: HidingPlace) -> None:
    detective.memes["confidence"] += 1
    world.say(
        f"Step by step, the two children followed the pale specks across the kitchen tiles until they reached {place.phrase}."
    )
    if place.high:
        world.say(
            f"It was high above their heads, and the shadows under it made the case feel even deeper and stranger."
        )


def choose_method(world: World, detective: Entity, helper: Entity, method: Method, place: HidingPlace) -> None:
    pred = predict_misstep(world)
    world.facts["predicted_risk"] = pred["risk"]
    helper.memes["worry"] += 1
    if place.high and method.uses_stool:
        world.say(
            f'{helper.id} looked at the little stool beside the counter. "{detective.id}, maybe we should get a grown-up," {helper.pronoun()} whispered.'
        )
        world.say(
            f'"If we wait, the mystery might hide itself," said {detective.id}.'
        )
    else:
        world.say(
            f'{detective.id} decided to look more closely.'
        )


def misstep(world: World, detective: Entity, helper: Entity, method: Method, place: HidingPlace) -> None:
    world.get("method").meters["used"] += 1
    propagate(world, narrate=False)
    detective.memes["shock"] += 1
    helper.memes["fear"] += 1
    world.say(
        f"{detective.id} dragged the stool over, climbed up, and reached toward {place.label}."
    )
    world.say(
        f"For one breath everything held still. Then the stool gave a tiny wobble."
    )
    world.say(place.spill_text)
    world.say(
        f'{helper.id} gasped. "{detective.id}!"'
    )


def reveal_and_bad_end(world: World, parent: Entity, detective: Entity, helper: Entity, culprit: Culprit, place: HidingPlace, theme: MysteryTheme) -> None:
    detective.memes["remorse"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried in at the sound and stopped short."
    )
    world.say(
        f'"Oh, darling," {parent.pronoun()} said softly. "The mystery was only that {culprit.phrase} had nibbled the {theme.missing_name}. '
        f'I put the rest near {place.label} because it was part of a surprise for tomorrow."'
    )
    world.say(
        f"{parent.pronoun().capitalize()} knelt to check that both children were safe first. Then {parent.pronoun()} looked at the mess and gave a sad little sigh."
    )
    world.say(
        f'"The salty crumbs came from {world.get("snack").label}, and yes, they had sodium in them," {parent.pronoun()} said. '
        f'"But climbing in the dark ruined the surprise before morning could come."'
    )
    world.say(
        f"The case was solved at last, but it did not feel like winning. {place.attrs['surprise_object'].capitalize()} lay spoiled on the floor, and the kitchen smelled sweet and broken instead of secret and bright."
    )
    world.say(
        f"{detective.id} held very still while {helper.id} leaned against {detective.pronoun('object')}. No one felt like playing detective anymore."
    )


def tell(
    theme: MysteryTheme,
    snack: Snack,
    culprit: Culprit,
    place: HidingPlace,
    method: Method,
    detective_name: str = "Mina",
    detective_type: str = "girl",
    helper_name: str = "Owen",
    helper_type: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="snack", type="snack", label=snack.label, phrase=snack.phrase, tags=set(snack.tags)))
    world.add(Entity(id="clue", type="clue", label=theme.clue_name))
    world.add(
        Entity(
            id="place",
            type="place",
            label=place.label,
            phrase=place.phrase,
            reachable=not place.high,
            attrs={"wobble_risk": place.wobble_risk, "surprise_object": place.surprise_object},
            tags=set(place.tags),
        )
    )
    world.add(Entity(id="method", type="method", label=method.label, attrs={"uses_stool": method.uses_stool}, tags=set(method.tags)))
    world.add(Entity(id="surprise", type="surprise", label=place.surprise_object))
    world.add(Entity(id="culprit", kind="character", type=culprit.type, label=culprit.label))
    world.facts.update(
        theme=theme,
        snack=snack,
        culprit=culprit,
        hiding_place=place,
        method_cfg=method,
        detective=detective,
        helper=helper,
        parent=parent,
    )

    introduce(world, detective, helper, theme, parent)
    world.para()
    lay_clue(world, detective, snack, culprit, theme)
    explain_sodium(world, helper, snack)
    follow_trail(world, detective, helper, place)
    world.para()
    choose_method(world, detective, helper, method, place)
    misstep(world, detective, helper, method, place)
    world.para()
    reveal_and_bad_end(world, parent, detective, helper, culprit, place, theme)

    world.facts.update(
        ruined=world.get("surprise").meters["ruined"] >= THRESHOLD,
        spilled=world.get("place").meters["spilled"] >= THRESHOLD,
        outcome="bad" if world.get("surprise").meters["ruined"] >= THRESHOLD else "safe",
    )
    return world


THEMES = {
    "midnight_snack": MysteryTheme(
        id="midnight_snack",
        missing_name="the missing cheese straws",
        opening_image="The house was sleepy and silver with moonlight.",
        clue_name="crumb trail",
        clue_desc="a dusting of pale, salty crumbs",
        scene_line="From the kitchen came one soft tick from the cooling stove and one even softer rustle.",
        discovery_line="On the counter, the round blue tin stood open where it should have been shut.",
        tags={"mystery", "night"},
    ),
    "party_crackers": MysteryTheme(
        id="party_crackers",
        missing_name="the vanished star crackers",
        opening_image="Rain tapped the window while the kitchen clock clicked like a tiny detective's shoe.",
        clue_name="cracker trail",
        clue_desc="small white flecks and one broken yellow star",
        scene_line="A warm lamp glowed over the sink, leaving the corners dim and full of guesses.",
        discovery_line="The bright party plate was lighter than it had been at bedtime.",
        tags={"mystery", "night"},
    ),
}

SNACKS = {
    "pretzels": Snack(
        id="pretzels",
        label="pretzels",
        phrase="a bowl of pretzels",
        crumb_kind="twisted pretzel crumbs",
        salty=True,
        sodium_wording="pretzels were full of sodium, the salty part that makes snacks taste sharp on the tongue",
        tags={"pretzel", "sodium", "salt"},
    ),
    "cheese_crackers": Snack(
        id="cheese_crackers",
        label="cheese crackers",
        phrase="a box of cheese crackers",
        crumb_kind="tiny orange cracker flakes",
        salty=True,
        sodium_wording="cheese crackers carried lots of sodium, which is why they tasted so salty",
        tags={"cracker", "sodium", "salt"},
    ),
    "rice_cakes": Snack(
        id="rice_cakes",
        label="rice cakes",
        phrase="a sleeve of rice cakes",
        crumb_kind="powdery rice crumbs",
        salty=True,
        sodium_wording="even rice cakes could have sodium if they were the salty kind",
        tags={"rice_cake", "sodium", "salt"},
    ),
}

CULPRITS = {
    "mouse": Culprit(
        id="mouse",
        label="a tiny mouse",
        phrase="a tiny mouse",
        type="animal",
        motive="followed the smell of salt",
        careful=False,
        tags={"mouse"},
    ),
    "puppy": Culprit(
        id="puppy",
        label="the puppy",
        phrase="the puppy",
        type="animal",
        motive="could not resist a crunchy snack",
        careful=False,
        tags={"dog"},
    ),
    "older_brother": Culprit(
        id="older_brother",
        label="an older brother",
        phrase="an older brother sneaking one late cracker",
        type="boy",
        motive="was hungry after bedtime",
        careful=False,
        tags={"sibling"},
    ),
}

HIDING_PLACES = {
    "top_shelf": HidingPlace(
        id="top_shelf",
        label="the top pantry shelf",
        phrase="the top pantry shelf",
        high=True,
        wobble_risk=2,
        surprise_object="a frosted birthday cake",
        spill_text="A covered cake box tipped, slid, and fell. The lid burst open, and a soft frosted birthday cake slumped sideways across the tiles.",
        tags={"shelf", "cake"},
    ),
    "fridge_top": HidingPlace(
        id="fridge_top",
        label="the top of the refrigerator",
        phrase="the top of the refrigerator",
        high=True,
        wobble_risk=2,
        surprise_object="a tray of iced cupcakes",
        spill_text="A tray hidden on top of the refrigerator skidded forward. Cupcakes tumbled down, and their swirls of icing smeared into one another on the floor.",
        tags={"fridge", "cupcakes"},
    ),
    "high_cabinet": HidingPlace(
        id="high_cabinet",
        label="the highest cabinet",
        phrase="the highest cabinet",
        high=True,
        wobble_risk=3,
        surprise_object="a paper bag of bakery cookies",
        spill_text="A paper bakery bag caught on the edge, tore wide open, and cookies rained down in a crackly shower of crumbs and broken chocolate.",
        tags={"cabinet", "cookies"},
    ),
}

METHODS = {
    "stool_climb": Method(
        id="stool_climb",
        label="climb on the stool",
        uses_stool=True,
        sense=2,
        tags={"stool", "risk"},
    ),
    "tiptoe_reach": Method(
        id="tiptoe_reach",
        label="tiptoe and stretch",
        uses_stool=True,
        sense=2,
        tags={"reach", "risk"},
    ),
    "stack_bowls": Method(
        id="stack_bowls",
        label="stack bowls and reach",
        uses_stool=True,
        sense=1,
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ruby", "Tess", "Nora", "Ava", "Lucy", "Ella"]
BOY_NAMES = ["Owen", "Max", "Theo", "Ben", "Sam", "Eli", "Finn", "Noah"]


@dataclass
class StoryParams:
    theme: str
    snack: str
    culprit: str
    hiding_place: str
    method: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="midnight_snack",
        snack="pretzels",
        culprit="mouse",
        hiding_place="top_shelf",
        method="stool_climb",
        detective_name="Mina",
        detective_type="girl",
        helper_name="Owen",
        helper_type="boy",
        parent="mother",
    ),
    StoryParams(
        theme="party_crackers",
        snack="cheese_crackers",
        culprit="puppy",
        hiding_place="fridge_top",
        method="tiptoe_reach",
        detective_name="Theo",
        detective_type="boy",
        helper_name="Ruby",
        helper_type="girl",
        parent="father",
    ),
    StoryParams(
        theme="midnight_snack",
        snack="rice_cakes",
        culprit="older_brother",
        hiding_place="high_cabinet",
        method="stool_climb",
        detective_name="Lucy",
        detective_type="girl",
        helper_name="Max",
        helper_type="boy",
        parent="mother",
    ),
]


KNOWLEDGE = {
    "sodium": [
        (
            "What is sodium?",
            "Sodium is a part of salt. Too much of it can make food taste very salty.",
        )
    ],
    "salt": [
        (
            "Why do crumbs taste salty?",
            "Salty crumbs come from foods with salt in them. Snacks like pretzels and crackers often leave that kind of taste behind.",
        )
    ],
    "mouse": [
        (
            "Why might a mouse come into a kitchen at night?",
            "A mouse may sneak into a kitchen to look for crumbs or food smells. Quiet night rooms can make that easier for it.",
        )
    ],
    "dog": [
        (
            "Why do puppies sniff around food?",
            "Puppies use their noses to find interesting smells. Crunchy snacks can be very tempting to them.",
        )
    ],
    "mystery": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure something out. Footprints, crumbs, and sounds can all be clues.",
        )
    ],
    "stool": [
        (
            "Why can climbing on a stool be risky?",
            "A stool can wobble if you lean too far. That is why children should ask a grown-up for help reaching high places.",
        )
    ],
    "cake": [
        (
            "Why does a cake get ruined when it falls?",
            "A cake is soft, so a fall can squash the frosting and break it apart. Once it is smashed, it no longer looks the way it was meant to.",
        )
    ],
    "cupcakes": [
        (
            "What happens when cupcakes tumble?",
            "Their icing can smear and their tops can break. Even if they still taste sweet, the surprise look is gone.",
        )
    ],
    "cookies": [
        (
            "Why do cookies break easily?",
            "Cookies are crisp and crumbly. A hard fall can snap them into pieces very fast.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "sodium", "salt", "mouse", "dog", "stool", "cake", "cupcakes", "cookies"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    snack = f["snack"]
    place = f["hiding_place"]
    culprit = f["culprit"]
    detective = f["detective"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "derive", "darling", and "sodium", and ends sadly.',
        f"Tell a gentle kitchen mystery where {detective.id} follows salty crumbs from {snack.label} toward {place.label} and discovers that {culprit.phrase} started the trouble.",
        f"Write a child-facing mystery with a bad ending where a detective child tries to solve a missing-snack case at night and ruins a surprise by reaching somewhere too high.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    parent = f["parent"]
    theme = f["theme"]
    snack = f["snack"]
    culprit = f["culprit"]
    place = f["hiding_place"]
    surprise = world.get("surprise")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child who wanted to solve a kitchen mystery, and {helper.id}, who followed close behind. {parent.label_word.capitalize()} came in when the mystery turned into a mess.",
        ),
        (
            f"What was the mystery at the start?",
            f"The mystery was that {theme.missing_name} had gone missing in the night. The open container and the crumb trail made it feel like a real case.",
        ),
        (
            f"How did {detective.id} try to derive a clue?",
            f"{detective.id} studied the salty crumbs on the floor and used them to reason about what had happened. The crumbs pointed toward {place.label}, so they became the first real clue.",
        ),
        (
            "Why did the story mention sodium?",
            f"The story mentioned sodium because the salty crumbs came from {snack.label}. Remembering that word helped the children connect the taste of the clue to the snack.",
        ),
        (
            f"What mistake did {detective.id} make?",
            f"{detective.id} tried to reach {place.label} by climbing instead of getting a grown-up. Because the place was high and the stool wobbled, that choice caused the hidden surprise to fall.",
        ),
        (
            "What was the bad ending?",
            f"The mystery was solved, but {surprise.label} was ruined on the floor. That sad image shows the children learned the truth too late and in the wrong way.",
        ),
        (
            f"Why did {parent.label_word} say 'darling'?",
            f'{parent.label_word.capitalize()} said "darling" softly because the children were upset and needed comfort first. The grown-up cared more about their safety than about scolding them.',
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "sodium", "salt", "stool"}
    culprit = world.facts["culprit"]
    place = world.facts["hiding_place"]
    tags |= set(culprit.tags)
    tags |= set(place.tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(snack: Snack, culprit: Culprit, place: HidingPlace, method: Method) -> str:
    if not clue_exists(snack, culprit):
        return (
            f"(No story: {culprit.label} would not leave a clear salty clue from {snack.label}, "
            f"so there is no fair mystery trail to follow.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Choose a method the world will tell.)"
        )
    if not risky_path(method, place):
        return (
            f"(No story: {method.label} does not create the risky high-reach mistake needed for this bad ending.)"
        )
    return "(No story: this combination does not fit the mystery.)"


ASP_RULES = r"""
% reasonableness gate
clue_exists(S, C) :- salty(S), culprit(C), not careful(C).
sensible(M) :- method(M), sense(M, V), sense_min(Min), V >= Min.
risky_path(M, P) :- uses_stool(M), high(P).
valid(T, S, C, P, M) :- theme(T), clue_exists(S, C), sensible(M), risky_path(M, P).

% outcome model
bad_ending :- chosen_place(P), high(P), chosen_method(M), uses_stool(M), chosen_method_sensible.
chosen_method_sensible :- chosen_method(M), sensible(M).
outcome(bad) :- bad_ending.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        if snack.salty:
            lines.append(asp.fact("salty", snack_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        if culprit.careful:
            lines.append(asp.fact("careful", culprit_id))
    for place_id, place in HIDING_PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.high:
            lines.append(asp.fact("high", place_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.uses_stool:
            lines.append(asp.fact("uses_stool", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.hiding_place),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    method = METHODS[params.method]
    place = HIDING_PLACES[params.hiding_place]
    return "bad" if risky_path(method, place) and method.sense >= SENSE_MIN else "safe"


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

    c_sens = set(asp_sensible())
    p_sens = {m.id for m in sensible_methods()}
    if c_sens == p_sens:
        print(f"OK: sensible methods match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print("Unexpected StoryError during random verification sample.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation ran.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a salty kitchen mystery with a bad ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--hiding-place", dest="hiding_place", choices=HIDING_PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack and args.culprit and not clue_exists(SNACKS[args.snack], CULPRITS[args.culprit]):
        place = HIDING_PLACES[args.hiding_place] if args.hiding_place else next(iter(HIDING_PLACES.values()))
        method = METHODS[args.method] if args.method else next(iter(METHODS.values()))
        raise StoryError(explain_rejection(SNACKS[args.snack], CULPRITS[args.culprit], place, method))

    if args.method and METHODS[args.method].sense < SENSE_MIN:
        snack = SNACKS[args.snack] if args.snack else next(iter(SNACKS.values()))
        culprit = CULPRITS[args.culprit] if args.culprit else next(iter(CULPRITS.values()))
        place = HIDING_PLACES[args.hiding_place] if args.hiding_place else next(iter(HIDING_PLACES.values()))
        raise StoryError(explain_rejection(snack, culprit, place, METHODS[args.method]))

    if args.method and args.hiding_place and not risky_path(METHODS[args.method], HIDING_PLACES[args.hiding_place]):
        snack = SNACKS[args.snack] if args.snack else next(iter(SNACKS.values()))
        culprit = CULPRITS[args.culprit] if args.culprit else next(iter(CULPRITS.values()))
        raise StoryError(explain_rejection(snack, culprit, HIDING_PLACES[args.hiding_place], METHODS[args.method]))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.snack is None or c[1] == args.snack)
        and (args.culprit is None or c[2] == args.culprit)
        and (args.hiding_place is None or c[3] == args.hiding_place)
        and (args.method is None or c[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, snack, culprit, hiding_place, method = rng.choice(sorted(combos))
    detective_name, detective_type = _pick_name(rng)
    helper_name, helper_type = _pick_name(rng, avoid=detective_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme,
        snack=snack,
        culprit=culprit,
        hiding_place=hiding_place,
        method=method,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
        parent=parent,
    )


def _require_key(table: dict, key: str, field_name: str):
    if key not in table:
        raise StoryError(f"(Invalid {field_name}: {key})")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    theme = _require_key(THEMES, params.theme, "theme")
    snack = _require_key(SNACKS, params.snack, "snack")
    culprit = _require_key(CULPRITS, params.culprit, "culprit")
    place = _require_key(HIDING_PLACES, params.hiding_place, "hiding_place")
    method = _require_key(METHODS, params.method, "method")

    if not clue_exists(snack, culprit):
        raise StoryError(explain_rejection(snack, culprit, place, method))
    if method.sense < SENSE_MIN or not risky_path(method, place):
        raise StoryError(explain_rejection(snack, culprit, place, method))

    world = tell(
        theme=theme,
        snack=snack,
        culprit=culprit,
        place=place,
        method=method,
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/5.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, snack, culprit, hiding_place, method) combos:\n")
        for theme, snack, culprit, place, method in combos:
            print(f"  {theme:14} {snack:16} {culprit:14} {place:12} {method}")
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
            header = (
                f"### {p.detective_name} & {p.helper_name}: {p.snack} / {p.culprit} / "
                f"{p.hiding_place} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
