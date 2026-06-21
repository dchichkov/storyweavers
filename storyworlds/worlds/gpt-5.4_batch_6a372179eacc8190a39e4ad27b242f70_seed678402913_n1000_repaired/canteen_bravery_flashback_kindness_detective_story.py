#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/canteen_bravery_flashback_kindness_detective_story.py
================================================================================

A standalone story world for a tiny child-facing detective tale set in a school
canteen. A child notices that something from lunch has gone missing, studies a
small clue, remembers an earlier moment in a flashback, gathers enough bravery
to ask the right person, and solves the case with kindness instead of blame.

The world prefers a few strong, reasonable mystery patterns over broad coverage:
the clue must honestly fit the cause, the missing object must make sense for
that cause, and the hero must have enough courage/support to ask the needed
question. Every generated sample aims for a complete shape:

    premise   -> lunchtime in the canteen, detective mood, missing item
    tension   -> clue + worry + a flashback that changes what the hero thinks
    turn      -> a brave question to the right person
    ending    -> a kind fix that shows what changed in the room

Run it
------
    python storyworlds/worlds/gpt-5.4/canteen_bravery_flashback_kindness_detective_story.py
    python storyworlds/worlds/gpt-5.4/canteen_bravery_flashback_kindness_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/canteen_bravery_flashback_kindness_detective_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/canteen_bravery_flashback_kindness_detective_story.py --qa
    python storyworlds/worlds/gpt-5.4/canteen_bravery_flashback_kindness_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/canteen_bravery_flashback_kindness_detective_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "cook_woman"}
        male = {"boy", "father", "man", "cook_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    place_text: str
    opener: str
    plural: bool = False
    allowed_causes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Clue:
    id: str
    label: str
    notice: str
    flashback: str
    points_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    actor_role: str
    challenge: int
    reveal: str
    reason: str
    kind_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    label: str
    fits: set[str] = field(default_factory=set)
    act: str = ""
    ending: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    bonus: int
    intro: str
    brave_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return World(
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_flashback(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.meters["noticed_clue"] < THRESHOLD:
        return []
    if world.facts.get("flashback_text") is None:
        return []
    sig = ("flashback", world.facts.get("clue_id"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["insight"] += 1
    world.facts["flashback_happened"] = True
    return ["__flashback__"]


def _r_bravery(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.memes["insight"] < THRESHOLD:
        return []
    sig = ("courage", world.facts.get("support_id"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += world.facts.get("support_bonus", 0)
    if world.facts.get("support_id") != "alone":
        hero.memes["supported"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if world.facts.get("solved") is not True:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="flashback", tag="memory", apply=_r_flashback),
    Rule(name="bravery", tag="emotion", apply=_r_bravery),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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
        for sent in produced:
            if sent == "__flashback__":
                world.say(world.facts["flashback_text"])
    return produced


MYSTERIES = {
    "roll": Mystery(
        id="roll",
        label="sesame roll",
        phrase="a warm sesame roll",
        place_text="beside the soup bowl",
        opener="The roll had smelled buttery and warm all through the line.",
        plural=False,
        allowed_causes={"tray_mixup", "hungry_child"},
        tags={"bread", "canteen"},
    ),
    "spoon": Mystery(
        id="spoon",
        label="silver soup spoon",
        phrase="a silver soup spoon",
        place_text="on the striped tray",
        opener="The spoon had shone like a tiny moon beside the tomato soup.",
        plural=False,
        allowed_causes={"tray_mixup", "safekeeping"},
        tags={"spoon", "canteen"},
    ),
    "card": Mystery(
        id="card",
        label="canteen lunch card",
        phrase="a blue canteen lunch card",
        place_text="under the cup",
        opener="The little blue card was how lunch got counted at the canteen.",
        plural=False,
        allowed_causes={"tray_mixup", "safekeeping"},
        tags={"canteen_card", "canteen"},
    ),
}

CLUES = {
    "star_sticker": Clue(
        id="star_sticker",
        label="gold star sticker",
        notice="a tiny gold star sticker stuck to the edge of the empty place",
        flashback="At once, a picture flashed into {hero}'s mind: in the lunch line, {hero} had seen a taller child at the next table with the very same gold star on a tray corner.",
        points_to="tray_mixup",
        tags={"sticker", "memory"},
    ),
    "soap_drops": Clue(
        id="soap_drops",
        label="lemon-soap drops",
        notice="three lemony soap drops drying near the tray",
        flashback="Then came a bright flashback: a little earlier, {hero} had watched the canteen helper lift things out of the way while wiping up a spill with a lemony cloth.",
        points_to="safekeeping",
        tags={"soap", "memory"},
    ),
    "crumb_trail": Clue(
        id="crumb_trail",
        label="crumb trail",
        notice="a shy trail of sesame crumbs leading toward the end bench",
        flashback="A memory clicked into place: before lunch, {hero} had noticed a new child staring at the bread basket and holding {poss} tummy very still, as if trying not to feel hungry.",
        points_to="hungry_child",
        tags={"crumbs", "memory"},
    ),
}

CAUSES = {
    "tray_mixup": Cause(
        id="tray_mixup",
        label="tray mix-up",
        actor_role="older_child",
        challenge=2,
        reveal="{actor} blinked, then looked down and found the missing {item} on the wrong tray. In the busy canteen line, the trays had been bumped together by mistake.",
        reason="It was not stealing at all. It was a mix-up made by two trays that looked almost the same.",
        kind_image="They traded the trays back with small embarrassed smiles.",
        tags={"mixup", "detective"},
    ),
    "safekeeping": Cause(
        id="safekeeping",
        label="safekeeping",
        actor_role="canteen_helper",
        challenge=1,
        reveal="{actor} nodded and opened the shelf by the sink. The missing {item} had been tucked there while a spill was cleaned, so it would stay dry and safe.",
        reason="The helper had moved it to protect it, not to hide it.",
        kind_image="The shelf door clicked softly, and the little mystery felt much smaller at once.",
        tags={"helper", "detective"},
    ),
    "hungry_child": Cause(
        id="hungry_child",
        label="hungry child",
        actor_role="new_child",
        challenge=3,
        reveal="{actor} looked down at the floor and admitted taking the missing {item}. {pron_cap} had thought it was extra and had been too hungry and too shy to ask.",
        reason="The real problem was an empty stomach and a worried heart, not meanness.",
        kind_image="After the truth came out, the bench no longer felt gloomy.",
        tags={"hunger", "detective"},
    ),
}

RESOLUTIONS = {
    "trade_back": Resolution(
        id="trade_back",
        label="trade back kindly",
        fits={"tray_mixup"},
        act="{hero} smiled first and said the case was only a bump-and-swap, so nobody needed to feel bad. The trays were traded back neatly.",
        ending="Soon the missing {item} was back where it belonged, and the canteen sounded ordinary again instead of mysterious.",
        qa_text="They swapped the trays back kindly after noticing it was only a mix-up.",
        tags={"kindness", "sharing"},
    ),
    "thank_helper": Resolution(
        id="thank_helper",
        label="thank the helper",
        fits={"safekeeping"},
        act="{hero} thanked {actor} for keeping the {item} safe, and {actor} thanked {hero} for asking so politely instead of accusing anyone.",
        ending="The {item} came out from the shelf, and even the lemon-soap smell seemed friendly now.",
        qa_text="The hero thanked the helper and got the item back from the safe shelf.",
        tags={"kindness", "helper"},
    ),
    "share_and_extra": Resolution(
        id="share_and_extra",
        label="share and get extra",
        fits={"hungry_child"},
        act="{hero} broke the worry with kindness, offering half and asking the helper whether there was another roll for the new child. There was.",
        ending="A fresh roll arrived, two children sat together, and the solved case made the long canteen bench feel warm instead of lonely.",
        qa_text="The hero shared kindly and helped the hungry child get another roll.",
        tags={"kindness", "sharing", "bread"},
    ),
}

SUPPORTS = {
    "alone": Support(
        id="alone",
        label="alone",
        bonus=0,
        intro="{hero} tucked the clue into a quiet detective thought and looked around alone.",
        brave_line="{hero} took a breath and walked over without anyone beside {obj}.",
        tags={"bravery"},
    ),
    "friend": Support(
        id="friend",
        label="best friend",
        bonus=1,
        intro="{helper} slid closer and whispered that great detectives notice little things together.",
        brave_line="With {helper} beside {obj}, {hero} felt brave enough to ask the next question.",
        tags={"friend", "bravery"},
    ),
    "monitor": Support(
        id="monitor",
        label="table monitor",
        bonus=1,
        intro="{helper}, the table monitor, said the clue looked important and promised to stand nearby.",
        brave_line="Knowing the table monitor was standing close, {hero} found a steadier voice.",
        tags={"bravery", "school"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Ella", "Ruby", "Tess", "Mila"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Max", "Eli", "Noah", "Sam", "Leo"]
TRAITS = {
    "shy": 1,
    "steady": 2,
    "bold": 3,
    "gentle": 2,
}

OTHER_NAMES = {
    "older_child": ["Mina", "Jasper", "Rory", "Pia"],
    "canteen_helper": ["Mrs. Bell", "Mr. Stone", "Ms. June"],
    "new_child": ["Ivo", "Nia", "Tariq", "Bea"],
}


def bravery_total(trait: str, support: str) -> int:
    return TRAITS[trait] + SUPPORTS[support].bonus


def resolution_fits(cause_id: str, resolution_id: str) -> bool:
    return cause_id in RESOLUTIONS[resolution_id].fits


def clue_fits(cause_id: str, clue_id: str) -> bool:
    return CLUES[clue_id].points_to == cause_id


def mystery_fits(mystery_id: str, cause_id: str) -> bool:
    return cause_id in MYSTERIES[mystery_id].allowed_causes


def valid_case(mystery_id: str, clue_id: str, cause_id: str,
               resolution_id: str, trait: str, support: str) -> bool:
    return (
        mystery_fits(mystery_id, cause_id)
        and clue_fits(cause_id, clue_id)
        and resolution_fits(cause_id, resolution_id)
        and bravery_total(trait, support) >= CAUSES[cause_id].challenge
    )


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for mystery_id in sorted(MYSTERIES):
        for clue_id in sorted(CLUES):
            for cause_id in sorted(CAUSES):
                for resolution_id in sorted(RESOLUTIONS):
                    for trait in sorted(TRAITS):
                        for support in sorted(SUPPORTS):
                            if valid_case(mystery_id, clue_id, cause_id, resolution_id, trait, support):
                                combos.append((mystery_id, clue_id, cause_id, resolution_id, trait, support))
    return combos


@dataclass
class StoryParams:
    mystery: str
    clue: str
    cause: str
    resolution: str
    trait: str
    support: str
    hero_name: str
    hero_gender: str
    parent: str
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, friend: Optional[Entity], mystery: Mystery) -> None:
    world.say(
        f"At lunchtime, {hero.id} walked into the school canteen feeling like a small detective. "
        f"{mystery.opener}"
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked to pretend every lunch tray hid a tiny case to solve, "
        f"even when the only clues were spoons, crumbs, and shiny cups."
    )
    if friend is not None:
        world.say(friend.attrs["support_intro"])


def discover_missing(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"But when {hero.id} sat down, the {mystery.label} that should have been {mystery.place_text} was gone."
    )
    world.say(
        f'"My {mystery.label}!" {hero.id} whispered. Suddenly the canteen felt less like lunchtime and more like a real mystery.'
    )


def inspect_clue(world: World, hero: Entity, clue: Clue) -> None:
    hero.meters["noticed_clue"] += 1
    world.facts["clue_id"] = clue.id
    world.say(
        f"{hero.id} looked carefully and found {clue.notice}."
    )
    world.facts["flashback_text"] = clue.flashback.format(
        hero=hero.id,
        poss=hero.pronoun("possessive"),
    )
    propagate(world, narrate=True)


def decide_to_ask(world: World, hero: Entity, helper: Optional[Entity], support: Support, cause: Cause) -> None:
    if helper is not None:
        world.say(helper.attrs["support_brave"])
    else:
        world.say(support.brave_line.format(hero=hero.id, obj=hero.pronoun("object"), helper=""))
    world.say(
        f"The clue pointed toward {cause.label}, and asking about it felt a little scary. "
        f"Still, {hero.id} kept the detective voice gentle instead of sharp."
    )


def reveal_truth(world: World, hero: Entity, actor: Entity, mystery: Mystery, cause: Cause) -> None:
    world.say(
        cause.reveal.format(
            actor=actor.id,
            item=mystery.label,
            pron_cap=actor.pronoun().capitalize(),
        )
    )
    world.say(cause.reason)


def resolve_case(world: World, hero: Entity, actor: Entity, mystery: Mystery,
                 cause: Cause, resolution: Resolution) -> None:
    hero.memes["kindness"] += 1
    hero.memes["courage_used"] += 1
    world.facts["solved"] = True
    propagate(world, narrate=False)
    world.say(
        resolution.act.format(hero=hero.id, actor=actor.id, item=mystery.label)
    )
    actor.memes["relief"] += 1
    hero.memes["relief"] += 1
    world.say(cause.kind_image)
    world.say(
        resolution.ending.format(hero=hero.id, actor=actor.id, item=mystery.label)
    )


def final_image(world: World, hero: Entity, mystery: Mystery, cause: Cause) -> None:
    if cause.id == "hungry_child":
        world.say(
            f"By the end of lunch, {hero.id} was eating in the canteen beside a new friend, "
            f"and the solved mystery tasted almost as good as the bread."
        )
    elif cause.id == "safekeeping":
        world.say(
            f"{hero.id} held the {mystery.label} again and grinned. The case had been solved with brave asking and kind manners."
        )
    else:
        world.say(
            f"{hero.id} tapped the table like a detective closing a notebook. The case was finished, and the canteen buzzed happily around {hero.pronoun('object')}."
        )


def actor_for_cause(rng: random.Random, cause: Cause) -> tuple[str, str]:
    name = rng.choice(OTHER_NAMES[cause.actor_role])
    if cause.actor_role == "canteen_helper":
        if name.startswith("Mr."):
            return name, "cook_man"
        return name, "cook_woman"
    if name in {"Mina", "Pia", "Nia", "Bea"}:
        return name, "girl"
    return name, "boy"


def tell(params: StoryParams) -> World:
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery '{params.mystery}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue '{params.clue}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause '{params.cause}'.)")
    if params.resolution not in RESOLUTIONS:
        raise StoryError(f"(Unknown resolution '{params.resolution}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait '{params.trait}'.)")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support '{params.support}'.)")
    if not valid_case(params.mystery, params.clue, params.cause, params.resolution, params.trait, params.support):
        raise StoryError(explain_rejection(params.mystery, params.clue, params.cause, params.resolution, params.trait, params.support))

    mystery = MYSTERIES[params.mystery]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    resolution = RESOLUTIONS[params.resolution]
    support = SUPPORTS[params.support]

    rng = random.Random(params.seed)
    world = World()

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        role="hero",
        label=params.hero_name,
        traits=[params.trait, "observant"],
    ))
    hero.memes["courage"] = float(TRAITS[params.trait])
    hero.memes["kindness"] = 1.0 if params.trait == "gentle" else 0.0

    world.add(Entity(
        id="canteen",
        kind="place",
        type="canteen",
        label="school canteen",
        phrase="the school canteen",
    ))
    missing = world.add(Entity(
        id="item",
        kind="thing",
        type="lunch_item",
        label=mystery.label,
        phrase=mystery.phrase,
        tags=set(mystery.tags),
    ))

    helper_ent: Optional[Entity] = None
    if support.id != "alone":
        if support.id == "friend":
            helper_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero.id])
            helper_gender = "girl" if helper_name in GIRL_NAMES else "boy"
        else:
            helper_name = rng.choice(["Rina", "Cal", "Moss", "June"])
            helper_gender = "girl" if helper_name in {"Rina", "June"} else "boy"
        helper_ent = world.add(Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="support",
            label=support.label,
            attrs={
                "support_intro": support.intro.format(hero=hero.id, helper=helper_name, obj=hero.pronoun("object")),
                "support_brave": support.brave_line.format(hero=hero.id, helper=helper_name, obj=hero.pronoun("object")),
            },
        ))

    actor_name, actor_gender = actor_for_cause(rng, cause)
    actor = world.add(Entity(
        id=actor_name,
        kind="character",
        type=actor_gender,
        role="actor",
        label=cause.actor_role.replace("_", " "),
    ))

    world.facts.update(
        mystery=mystery,
        clue=clue,
        cause=cause,
        resolution=resolution,
        support=support,
        hero=hero,
        helper=helper_ent,
        actor=actor,
        item=missing,
        support_id=support.id,
        support_bonus=support.bonus,
        solved=False,
    )

    introduce(world, hero, helper_ent, mystery)
    world.para()
    discover_missing(world, hero, mystery)
    inspect_clue(world, hero, clue)
    world.para()
    decide_to_ask(world, hero, helper_ent, support, cause)
    reveal_truth(world, hero, actor, mystery, cause)
    world.para()
    resolve_case(world, hero, actor, mystery, cause, resolution)
    final_image(world, hero, mystery, cause)

    world.facts["bravery_total"] = bravery_total(params.trait, params.support)
    world.facts["flashback_happened"] = bool(world.facts.get("flashback_happened"))
    world.facts["kind_ending"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    mystery = world.facts["mystery"]
    cause = world.facts["cause"]
    return [
        'Write a short detective-style story for a 3-to-5-year-old set in a school canteen. Include the word "canteen" and show bravery, a flashback, and kindness.',
        f"Tell a gentle mystery where {hero.id} notices a missing {mystery.label}, uses a flashback to understand a clue, and solves the case kindly.",
        f"Write a child-friendly detective story in which a lunchtime clue leads to {cause.label}, and the ending proves that being brave does not mean being mean.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    mystery = world.facts["mystery"]
    clue = world.facts["clue"]
    cause = world.facts["cause"]
    resolution = world.facts["resolution"]
    actor = world.facts["actor"]
    helper = world.facts["helper"]
    support = world.facts["support"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child in the school canteen who tries to solve a missing-lunch mystery. The story follows {hero.pronoun('object')} as {hero.pronoun()} notices a clue, remembers something important, and chooses kindness."
        ),
        (
            f"What went missing in the canteen?",
            f"The missing thing was the {mystery.label}. That missing lunch item is what turned an ordinary canteen meal into a detective case."
        ),
        (
            "What clue did the child find?",
            f"{hero.id} found {clue.notice}. That clue mattered because it matched something {hero.pronoun()} had noticed earlier, so it led into the flashback."
        ),
    ]
    if world.facts.get("flashback_happened"):
        qa.append((
            "How did the flashback help solve the case?",
            f"The flashback reminded {hero.id} of an earlier moment from the canteen line. Because of that memory, {hero.pronoun()} understood what the clue really meant instead of guessing wildly."
        ))
    who_helped = helper.id if helper is not None else f"{hero.id} alone"
    qa.append((
        "How was bravery shown in the story?",
        f"Bravery showed when {hero.id} used a calm voice and asked about the missing {mystery.label} even though it felt scary. {support.label.capitalize()} support from {who_helped} helped {hero.pronoun('object')} speak gently and clearly."
    ))
    qa.append((
        "What was the real answer to the mystery?",
        f"The truth was {cause.label}. {cause.reason}"
    ))
    qa.append((
        "How did kindness help at the end?",
        f"{resolution.qa_text} Kindness solved the problem without making the other person feel smaller, so the canteen felt safe again."
    ))
    return qa


KNOWLEDGE = {
    "canteen": [
        (
            "What is a canteen?",
            "A canteen is a place where people eat meals together, often at a school or camp. It is usually busy, with trays, cups, and many people at tables."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks carefully for clues and asks questions to solve a mystery. Good detectives do not just guess; they pay attention and think."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick return to an earlier moment. It helps a character remember something important that changes what they understand now."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel nervous. It does not have to be loud; sometimes bravery is a quiet question asked in a steady voice."
        )
    ],
    "kindness": [
        (
            "Why can kindness help solve problems?",
            "Kindness helps people tell the truth and feel safe enough to fix a mistake. When someone feels less scared, it is easier to make things right."
        )
    ],
    "bread": [
        (
            "Why might someone act badly when they are very hungry?",
            "Hunger can make people worried, rushed, or upset. That does not make the choice right, but it can help explain why they need help as well as correction."
        )
    ],
    "spoon": [
        (
            "What is a soup spoon for?",
            "A soup spoon has a round bowl for lifting broth or soup. It helps you eat warm soup without spilling it."
        )
    ],
    "canteen_card": [
        (
            "What is a lunch card?",
            "A lunch card is a small card used to help count or pay for meals. At school, children may keep it on a tray or in a pocket during lunch."
        )
    ],
    "helper": [
        (
            "What does a lunch helper do?",
            "A lunch helper keeps the eating area tidy and safe. They may wipe spills, move things out of the way, and help children if something is missing."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "canteen",
    "detective",
    "flashback",
    "bravery",
    "kindness",
    "bread",
    "spoon",
    "canteen_card",
    "helper",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    mystery = world.facts["mystery"]
    cause = world.facts["cause"]
    tags = {"canteen", "detective", "flashback", "bravery", "kindness"} | set(mystery.tags) | set(cause.tags)
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
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(r[0] for r in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mystery="roll",
        clue="crumb_trail",
        cause="hungry_child",
        resolution="share_and_extra",
        trait="bold",
        support="friend",
        hero_name="Maya",
        hero_gender="girl",
        parent="mother",
        seed=11,
    ),
    StoryParams(
        mystery="spoon",
        clue="soap_drops",
        cause="safekeeping",
        resolution="thank_helper",
        trait="shy",
        support="friend",
        hero_name="Ben",
        hero_gender="boy",
        parent="father",
        seed=22,
    ),
    StoryParams(
        mystery="card",
        clue="star_sticker",
        cause="tray_mixup",
        resolution="trade_back",
        trait="steady",
        support="alone",
        hero_name="Lina",
        hero_gender="girl",
        parent="mother",
        seed=33,
    ),
    StoryParams(
        mystery="spoon",
        clue="star_sticker",
        cause="tray_mixup",
        resolution="trade_back",
        trait="shy",
        support="friend",
        hero_name="Theo",
        hero_gender="boy",
        parent="father",
        seed=44,
    ),
]


def explain_rejection(mystery_id: str, clue_id: str, cause_id: str,
                      resolution_id: str, trait: str, support: str) -> str:
    pieces: list[str] = []
    if cause_id not in MYSTERIES[mystery_id].allowed_causes:
        pieces.append(
            f"{MYSTERIES[mystery_id].label} does not fit the cause '{cause_id}'"
        )
    if CLUES[clue_id].points_to != cause_id:
        pieces.append(
            f"the clue '{clue_id}' points to '{CLUES[clue_id].points_to}', not '{cause_id}'"
        )
    if cause_id not in RESOLUTIONS[resolution_id].fits:
        pieces.append(
            f"the resolution '{resolution_id}' does not fix '{cause_id}'"
        )
    if bravery_total(trait, support) < CAUSES[cause_id].challenge:
        pieces.append(
            f"{trait} courage plus {support} support is too weak for this case"
        )
    if not pieces:
        return "(No valid case for the given options.)"
    return "(No story: " + "; ".join(pieces) + ".)"


ASP_RULES = r"""
allowed(M, C) :- mystery(M), cause(C), mystery_allows(M, C).
clue_fits(C, Cl) :- clue(Cl), cause(C), points_to(Cl, C).
resolution_fits(C, R) :- resolution(R), cause(C), resolves(R, C).
bravery(T, S, B) :- trait(T), support(S), trait_power(T, TP), support_bonus(S, SB), B = TP + SB.
strong_enough(C, T, S) :- cause(C), bravery(T, S, B), challenge(C, Need), B >= Need.

valid(M, Cl, C, R, T, S) :- allowed(M, C), clue_fits(C, Cl), resolution_fits(C, R), strong_enough(C, T, S).

chosen_valid :- chosen_mystery(M), chosen_clue(Cl), chosen_cause(C), chosen_resolution(R), chosen_trait(T), chosen_support(S), valid(M, Cl, C, R, T, S).
outcome(solved) :- chosen_valid.
outcome(rejected) :- not chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        for cause_id in sorted(mystery.allowed_causes):
            lines.append(asp.fact("mystery_allows", mystery_id, cause_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("points_to", clue_id, clue.points_to))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("challenge", cause_id, cause.challenge))
    for resolution_id, resolution in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", resolution_id))
        for cause_id in sorted(resolution.fits):
            lines.append(asp.fact("resolves", resolution_id, cause_id))
    for trait, power in TRAITS.items():
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("trait_power", trait, power))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("support_bonus", support_id, support.bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_mystery", params.mystery),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_resolution", params.resolution),
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_support", params.support),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combo gate matches ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    check_cases = list(CURATED)
    rng = random.Random(99)
    parser = build_parser()
    for i in range(30):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(rng.randint(0, 10_000)))
        except StoryError:
            continue
        p.seed = i + 100
        check_cases.append(p)
    bad = 0
    for params in check_cases:
        expected = "solved" if valid_case(params.mystery, params.clue, params.cause, params.resolution, params.trait, params.support) else "rejected"
        got = asp_outcome(params)
        if expected != got:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(check_cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(check_cases)} outcome checks differed.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "canteen" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story was empty or missing 'canteen'.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a detective-style canteen mystery solved with bravery, flashback, and kindness."
    )
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--resolution", choices=sorted(RESOLUTIONS))
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--support", choices=sorted(SUPPORTS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from ASP")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def explain_gender(name: str, gender: str) -> str:
    return f"(No story: the name '{name}' does not match the chosen gender '{gender}' in this tiny registry.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.name and args.gender:
        if args.gender == "girl" and args.name not in GIRL_NAMES:
            raise StoryError(explain_gender(args.name, args.gender))
        if args.gender == "boy" and args.name not in BOY_NAMES:
            raise StoryError(explain_gender(args.name, args.gender))

    if all([args.mystery, args.clue, args.cause, args.resolution, args.trait, args.support]):
        if not valid_case(args.mystery, args.clue, args.cause, args.resolution, args.trait, args.support):
            raise StoryError(explain_rejection(args.mystery, args.clue, args.cause, args.resolution, args.trait, args.support))

    combos = [
        combo for combo in valid_combos()
        if (args.mystery is None or combo[0] == args.mystery)
        and (args.clue is None or combo[1] == args.clue)
        and (args.cause is None or combo[2] == args.cause)
        and (args.resolution is None or combo[3] == args.resolution)
        and (args.trait is None or combo[4] == args.trait)
        and (args.support is None or combo[5] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mystery, clue, cause, resolution, trait, support = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        mystery=mystery,
        clue=clue,
        cause=cause,
        resolution=resolution,
        trait=trait,
        support=support,
        hero_name=hero_name,
        hero_gender=gender,
        parent=parent,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (mystery, clue, cause, resolution, trait, support) combos:\n")
        for combo in combos:
            print("  " + "  ".join(combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 60, 60):
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
            header = f"### {p.hero_name}: {p.mystery} / {p.cause} / {p.trait}+{p.support}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
