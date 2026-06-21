#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/analogy_humor_foreshadowing_transformation_fable.py

A small fable-like storyworld about a young caterpillar who wants wings too soon.

The world model tracks:
- physical meters: wearing a fake shortcut, tumbling, cocooning, transforming
- emotional memes: envy, impatience, embarrassment, patience, pride, wisdom

The story shape is:
1) a caterpillar admires flying creatures and wants a shortcut
2) a wise helper notices a real sign that change is near and gives an analogy
3) either the caterpillar waits, or tries a comic fake-wing stunt and tumbles
4) the caterpillar makes a chrysalis and truly transforms
5) the ending image proves the inward lesson changed too

The domain is designed to support:
- analogy
- humor
- foreshadowing
- transformation
- a child-facing fable tone
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
PATIENT_TRAITS = {"patient", "thoughtful", "careful"}


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
        if self.type in {"girl", "hen", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "rooster", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    opening: str
    materials: set[str] = field(default_factory=set)
    signs: set[str] = field(default_factory=set)
    perch: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    label: str
    phrase: str
    material: str
    wear_text: str
    jump_text: str
    fail_text: str
    funny_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    cue: str
    wisdom: str
    urgency: int
    chrysalis_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    phrase: str
    analogy: str
    style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    shortcut: str
    sign: str
    helper: str
    hero_name: str
    helper_name: str
    hero_trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_tumble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["leapt"] >= THRESHOLD and hero.meters["wearing_shortcut"] >= THRESHOLD:
        sig = ("tumble", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["tumbled"] += 1
            hero.memes["embarrassment"] += 1
            hero.memes["impatience"] = 0.0
            out.append("__tumble__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["in_chrysalis"] >= THRESHOLD:
        sig = ("transform", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["winged"] += 1
            hero.memes["patience"] += 1
            hero.memes["pride"] += 1
            hero.type = "butterfly"
            hero.label = "butterfly"
            out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule(name="tumble", tag="physical", apply=_r_tumble),
    Rule(name="transform", tag="physical", apply=_r_transform),
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
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


PLACES = {
    "cabbage_patch": Place(
        id="cabbage_patch",
        label="the cabbage patch",
        opening="under broad cabbage leaves beside a low garden wall",
        materials={"leaf", "twig"},
        signs={"silk_tickle", "snug_stem", "sunset_glow"},
        perch="a bent cabbage stem",
        tags={"garden", "leaf"},
    ),
    "flower_bank": Place(
        id="flower_bank",
        label="the flower bank",
        opening="among marigolds and clover on a sunny bank",
        materials={"petal", "twig"},
        signs={"silk_tickle", "sunset_glow"},
        perch="a clover stalk",
        tags={"flower", "petal"},
    ),
    "fence_corner": Place(
        id="fence_corner",
        label="the fence corner",
        opening="where the old fence met a patch of mint",
        materials={"feather", "leaf", "twig"},
        signs={"silk_tickle", "snug_stem"},
        perch="the top rail of the fence",
        tags={"fence", "twig"},
    ),
}

SHORTCUTS = {
    "leaf_wings": Shortcut(
        id="leaf_wings",
        label="leaf wings",
        phrase="two bright leaves tied on with grass",
        material="leaf",
        wear_text="tucked two bright leaves against his sides and tied them on with a blade of grass",
        jump_text="He climbed up, spread the leaves grandly, and gave the air a solemn nod",
        fail_text="The leaves folded like sleepy fans, and down he plopped into a soft heap",
        funny_image="For one moment he looked less like an eagle and more like a salad trying to sneeze.",
        tags={"leaf", "wings"},
    ),
    "petal_sail": Shortcut(
        id="petal_sail",
        label="a petal sail",
        phrase="a wide marigold petal strapped on like a tiny sail",
        material="petal",
        wear_text="strapped a wide marigold petal to his back and puffed out his chest",
        jump_text="He marched to the tip of the stalk as if he were captain of the sky",
        fail_text="The petal spun sideways, and he twirled down in a dizzy little spiral",
        funny_image="He did not descend like a prince of the breeze. He descended like a lost teacup lid.",
        tags={"petal", "sail"},
    ),
    "feather_cape": Shortcut(
        id="feather_cape",
        label="a feather cape",
        phrase="a fallen feather worn like a royal cape",
        material="feather",
        wear_text="dragged a fallen feather over his back and declared it a royal flying cape",
        jump_text="He wriggled to the rail, puffed his middle, and launched with splendid confidence",
        fail_text="The feather sailed away without him, and he landed on a mint leaf with a surprised squeak",
        funny_image="The feather flew beautifully. The caterpillar did not.",
        tags={"feather", "cape"},
    ),
}

SIGNS = {
    "silk_tickle": Sign(
        id="silk_tickle",
        cue="a tickly wish to spin silk",
        wisdom="Something inside him was preparing a true change",
        urgency=3,
        chrysalis_text="Soon he spun a quiet little chrysalis and hung still as a green lantern",
        tags={"silk", "change"},
    ),
    "snug_stem": Sign(
        id="snug_stem",
        cue="one stem that felt oddly perfect for resting",
        wisdom="The world seemed to be offering him a safe place to become something new",
        urgency=2,
        chrysalis_text="Before long he fastened himself to the snug stem and tucked into a tidy chrysalis",
        tags={"stem", "change"},
    ),
    "sunset_glow": Sign(
        id="sunset_glow",
        cue="an evening glow that made the leaves look full of secrets",
        wisdom="It was a gentle hint, but not a very strong one",
        urgency=1,
        chrysalis_text="At last he chose a still leaf, spun his case, and waited through the quiet evening",
        tags={"sunset", "change"},
    ),
}

HELPERS = {
    "snail": HelperKind(
        id="snail",
        label="snail",
        phrase="an old garden snail",
        analogy="Borrowed wings are like paper umbrellas on a fish. They look busy, but they do not teach flying.",
        style="slowly",
        tags={"snail", "analogy"},
    ),
    "cricket": HelperKind(
        id="cricket",
        label="cricket",
        phrase="a bright-eyed cricket",
        analogy="A shortcut to wings is like tying soup spoons to a seed and calling it a swallow. The name changes first; the nature does not.",
        style="with a cheerful chirp",
        tags={"cricket", "analogy"},
    ),
    "beetle": HelperKind(
        id="beetle",
        label="beetle",
        phrase="a shiny black beetle",
        analogy="Painted thunder is still silence. A costume can dress a wish, but it cannot grow a wing.",
        style="in a polished little voice",
        tags={"beetle", "analogy"},
    ),
}

HERO_NAMES = ["Pip", "Moss", "Dot", "Nib", "Bean", "Sprig", "Milo", "Tansy"]
HELPER_NAMES = ["Shellby", "Chirp", "Brass", "Mote", "Nettle", "Pebble"]
TRAITS = ["patient", "thoughtful", "careful", "hasty", "showy", "restless"]


def valid_combo(place_id: str, shortcut_id: str, sign_id: str) -> bool:
    place = PLACES[place_id]
    shortcut = SHORTCUTS[shortcut_id]
    return shortcut.material in place.materials and sign_id in place.signs


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for shortcut_id in SHORTCUTS:
            for sign_id in SIGNS:
                if valid_combo(place_id, shortcut_id, sign_id):
                    out.append((place_id, shortcut_id, sign_id))
    return out


def would_wait(hero_trait: str, sign_id: str) -> bool:
    sign = SIGNS[sign_id]
    return hero_trait in PATIENT_TRAITS and sign.urgency >= 2


def outcome_of(params: StoryParams) -> str:
    return "direct_change" if would_wait(params.hero_trait, params.sign) else "comic_tumble"


def explain_rejection(place: Place, shortcut: Shortcut, sign: Sign) -> str:
    if shortcut.material not in place.materials:
        have = ", ".join(sorted(place.materials))
        return (
            f"(No story: {place.label} does not offer the material for {shortcut.label}. "
            f"It has {have}, so that disguise would not exist there.)"
        )
    if sign.id not in place.signs:
        have = ", ".join(sorted(place.signs))
        return (
            f"(No story: {sign.cue} is not a sign this place supports. "
            f"Try one of: {have}.)"
        )
    return "(No story: that combination does not fit this little world.)"


def predict_attempt(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["wearing_shortcut"] += 1
    hero.meters["leapt"] += 1
    propagate(sim, narrate=False)
    return {
        "tumbled": hero.meters["tumbled"] >= THRESHOLD,
        "embarrassment": hero.memes["embarrassment"],
    }


def introduce(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"In {place.label}, {place.opening}, lived a little caterpillar named {hero.id}."
    )
    world.say(
        f"{hero.id} had a {hero.attrs['trait']} heart and a great opinion of what tomorrow ought to hurry up and bring."
    )


def admire(world: World, hero: Entity) -> None:
    hero.memes["envy"] += 1
    world.say(
        f"Each morning {hero.id} watched butterflies pass overhead like bits of painted laughter."
    )
    world.say(
        f'"Why should I crawl when they float?" {hero.id} grumbled. "I am tired of being a ribbon with knees."'
    )


def helper_arrives(world: World, helper: Entity, helper_kind: HelperKind, sign: Sign) -> None:
    world.say(
        f"Along came {helper.id}, {helper_kind.phrase}, who listened {helper_kind.style}."
    )
    world.say(
        f'{helper.id} noticed {sign.cue} and said, "{sign.wisdom}. {helper_kind.analogy}"'
    )


def choose_shortcut(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.meters["wearing_shortcut"] += 1
    hero.memes["impatience"] += 1
    world.say(
        f"But {hero.id} wanted wings at once, so he {shortcut.wear_text}."
    )
    world.say(
        f"He admired himself in a dew drop until even his own reflection seemed politely doubtful."
    )


def wait_instead(world: World, hero: Entity, helper: Entity, sign: Sign, place: Place) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"{hero.id} looked at {place.perch}, felt the strange stillness in his own small body, and swallowed his hurry."
    )
    world.say(
        f'"Then I will wait," he said. "{helper.id}, perhaps the wise road is slower because it knows where it is going."'
    )
    world.say(sign.chrysalis_text + ".")
    hero.meters["in_chrysalis"] += 1
    propagate(world, narrate=False)


def leap_and_tumble(world: World, hero: Entity, shortcut: Shortcut, place: Place) -> None:
    hero.meters["leapt"] += 1
    world.say(
        f"{shortcut.jump_text} from {place.perch}."
    )
    propagate(world, narrate=False)
    world.say(shortcut.fail_text + ".")
    world.say(shortcut.funny_image)
    world.say(
        f"After that, even the mint leaves seemed to be trying not to giggle."
    )


def accept_lesson(world: World, hero: Entity, helper: Entity, sign: Sign) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"{hero.id} brushed himself off and said, "
        f'"A true wing, then, must grow from the inside first."'
    )
    world.say(
        f'{helper.id} nodded. "Just so. Pride that runs ahead of its season usually trips over its own feet."'
    )
    world.say(sign.chrysalis_text + ".")
    hero.meters["in_chrysalis"] += 1
    propagate(world, narrate=False)


def emerge(world: World, hero: Entity, place: Place) -> None:
    world.para()
    world.say(
        f"When the waiting was finished, the little chrysalis split with a quiet seam of morning."
    )
    world.say(
        f"Out came {hero.id} with real wings, soft at first and then bright in the sun."
    )
    world.say(
        f"He rose over {place.label} not with a boast, but with wonder."
    )


def moral(world: World, hero: Entity, helper: Entity, shortcut: Shortcut, attempted: bool) -> None:
    if attempted:
        world.say(
            f'"I see it now," said {hero.id}. "A borrowed costume can make a joke, but not a self."'
        )
    else:
        world.say(
            f'"I nearly chased a costume when change was already on its way," said {hero.id}.'
        )
    world.say(
        f'{helper.id} smiled. "That is the happy trick of patience. It looks small while it is working and grand when it is done."'
    )


def tell(
    place: Place,
    shortcut: Shortcut,
    sign: Sign,
    helper_kind: HelperKind,
    hero_name: str,
    helper_name: str,
    hero_trait: str,
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type="caterpillar",
            label="caterpillar",
            role="hero",
            attrs={"trait": hero_trait},
            traits=[hero_trait],
            tags={"hero"},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_kind.label,
            label=helper_kind.label,
            role="helper",
            tags=set(helper_kind.tags),
        )
    )

    introduce(world, hero, place)
    admire(world, hero)

    world.para()
    helper_arrives(world, helper, helper_kind, sign)

    direct = would_wait(hero_trait, sign.id)
    world.facts["predicted_attempt"] = predict_attempt(world)
    world.facts["foreshadow_strength"] = sign.urgency

    world.para()
    if direct:
        wait_instead(world, hero, helper, sign, place)
        attempted = False
    else:
        choose_shortcut(world, hero, shortcut)
        leap_and_tumble(world, hero, shortcut, place)
        accept_lesson(world, hero, helper, sign)
        attempted = True

    emerge(world, hero, place)
    moral(world, hero, helper, shortcut, attempted)

    world.facts.update(
        hero=hero,
        helper=helper,
        place=place,
        shortcut=shortcut,
        sign=sign,
        helper_kind=helper_kind,
        attempted=attempted,
        transformed=hero.meters["winged"] >= THRESHOLD,
        outcome="direct_change" if direct else "comic_tumble",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    shortcut = f["shortcut"]
    sign = f["sign"]
    outcome = f["outcome"]
    prompts = [
        'Write a short fable for a 3-to-5-year-old that includes the word "analogy" and features humor, foreshadowing, and transformation.',
        f"Tell a gentle animal fable set in {place.label} about a caterpillar who wants wings too soon and notices {sign.cue}.",
        f"Write a funny fable where a small creature tries {shortcut.phrase}, learns patience, and truly changes at the end.",
    ]
    if outcome == "comic_tumble":
        prompts.append(
            f"Include a comic tumble before the real transformation, so {hero.id} first learns that pretending is not the same as becoming."
        )
    else:
        prompts.append(
            f"Let the wise warning work in time, so {hero.id} waits instead of trying the silly disguise."
        )
    return prompts


KNOWLEDGE = {
    "caterpillar": [
        (
            "What is a caterpillar?",
            "A caterpillar is the soft, crawling young form of a butterfly or moth. It eats, grows, and later changes into something new.",
        )
    ],
    "chrysalis": [
        (
            "What is a chrysalis?",
            "A chrysalis is the hard case some caterpillars make around themselves while they change. Inside it, their bodies slowly transform.",
        )
    ],
    "butterfly": [
        (
            "How does a butterfly begin life?",
            "A butterfly begins as an egg, then becomes a caterpillar, and later changes inside a chrysalis. After that it comes out with wings.",
        )
    ],
    "patience": [
        (
            "What is patience?",
            "Patience means waiting calmly for the right time instead of grabbing too fast. Some good things really do need time to grow.",
        )
    ],
    "analogy": [
        (
            "What is an analogy?",
            "An analogy is a way of explaining one thing by comparing it to another thing. It helps an idea feel easier to understand.",
        )
    ],
    "snail": [
        (
            "Why do people think snails are patient?",
            "Snails move slowly and steadily, so they often stand for patience in stories. They remind us that slow does not mean foolish.",
        )
    ],
    "cricket": [
        (
            "Why are crickets used in stories?",
            "Crickets make quick, lively sounds and often seem alert. In stories, they can feel cheerful, clever, and observant.",
        )
    ],
    "beetle": [
        (
            "What is a beetle?",
            "A beetle is an insect with a hard outer shell over its wings. Many beetles look shiny and sturdy.",
        )
    ],
}

KNOWLEDGE_ORDER = ["analogy", "caterpillar", "chrysalis", "butterfly", "patience", "snail", "cricket", "beetle"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    shortcut = f["shortcut"]
    sign = f["sign"]
    attempted = f["attempted"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little caterpillar in {place.label}, and {helper.id}, the wise {helper.label} who spoke to him. The story follows {hero.id}'s wish to become grand before he was ready.",
        ),
        (
            f"Why did {hero.id} want a shortcut?",
            f"{hero.id} envied the butterflies flying over him and felt tired of crawling. That envy made him want wings at once instead of waiting for true change.",
        ),
        (
            "What was the foreshadowing sign?",
            f"The sign was {sign.cue}. It mattered because it hinted that a real transformation was already drawing near.",
        ),
        (
            f"What analogy did {helper.id} use?",
            f"{helper.id} used an analogy to show that a costume is not the same as real change. The comparison helped {hero.id} understand that pretending to have wings cannot grow them.",
        ),
    ]
    if attempted:
        qa.append(
            (
                f"What happened when {hero.id} tried the shortcut?",
                f"{hero.id} tried {shortcut.label} and leapt, but he tumbled instead of flying. The silly fall is funny, yet it also teaches why hurry and pride can make trouble.",
            )
        )
        qa.append(
            (
                f"Why did {hero.id} change his mind afterward?",
                f"He felt embarrassed after the tumble and saw that the disguise had only decorated his wish. That made him ready to listen and wait for the real change inside him.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} try the shortcut?",
                f"No. {hero.id} listened in time and chose to wait instead of pretending. The warning worked because the sign was strong enough and he was ready to be patient.",
            )
        )
    qa.append(
        (
            f"How did the story end?",
            f"It ended with {hero.id} coming out of a chrysalis as a real butterfly and rising over {place.label}. The ending proves that the true transformation happened both in his body and in his thinking.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"analogy", "caterpillar", "chrysalis", "butterfly", "patience"}
    helper = world.facts["helper_kind"]
    tags |= set(helper.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE.get(tag, []))
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="cabbage_patch",
        shortcut="leaf_wings",
        sign="silk_tickle",
        helper="snail",
        hero_name="Pip",
        helper_name="Shellby",
        hero_trait="hasty",
    ),
    StoryParams(
        place="flower_bank",
        shortcut="petal_sail",
        sign="sunset_glow",
        helper="cricket",
        hero_name="Dot",
        helper_name="Chirp",
        hero_trait="showy",
    ),
    StoryParams(
        place="fence_corner",
        shortcut="feather_cape",
        sign="snug_stem",
        helper="beetle",
        hero_name="Moss",
        helper_name="Brass",
        hero_trait="patient",
    ),
    StoryParams(
        place="cabbage_patch",
        shortcut="leaf_wings",
        sign="snug_stem",
        helper="snail",
        hero_name="Bean",
        helper_name="Pebble",
        hero_trait="thoughtful",
    ),
]


ASP_RULES = r"""
% Validity gate: a story only exists when the place contains the material for
% the shortcut and the place supports the chosen foreshadowing sign.
valid(P, Sc, Sg) :- place(P), shortcut(Sc), sign(Sg),
                    needs_material(Sc, M), has_material(P, M), supports_sign(P, Sg).

% Outcome gate: patient traits heed stronger signs; otherwise the comic attempt happens first.
patient_trait(T) :- trait_kind(T), patient(T).
waits(T, Sg) :- patient_trait(T), sign_urgency(Sg, U), U >= 2.
outcome(direct_change) :- chosen_trait(T), chosen_sign(Sg), waits(T, Sg).
outcome(comic_tumble) :- chosen_trait(T), chosen_sign(Sg), not waits(T, Sg).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for mat in sorted(place.materials):
            lines.append(asp.fact("has_material", place_id, mat))
        for sign_id in sorted(place.signs):
            lines.append(asp.fact("supports_sign", place_id, sign_id))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("needs_material", shortcut_id, shortcut.material))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        lines.append(asp.fact("sign_urgency", sign_id, sign.urgency))
    for trait in TRAITS:
        lines.append(asp.fact("trait_kind", trait))
        if trait in PATIENT_TRAITS:
            lines.append(asp.fact("patient", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_trait", params.hero_trait),
            asp.fact("chosen_sign", params.sign),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos parity holds ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for i in range(50):
        rng = random.Random(i)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH in outcomes: {len(mismatches)} cases differ.")
    else:
        print(f"OK: outcome parity holds on {len(cases)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable storyworld: a caterpillar wants wings too soon, meets a wise analogy, and truly transforms."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS, dest="hero_trait")
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.shortcut and args.sign:
        place = PLACES[args.place]
        shortcut = SHORTCUTS[args.shortcut]
        sign = SIGNS[args.sign]
        if not valid_combo(args.place, args.shortcut, args.sign):
            raise StoryError(explain_rejection(place, shortcut, sign))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.shortcut is None or combo[1] == args.shortcut)
        and (args.sign is None or combo[2] == args.sign)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, shortcut_id, sign_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_trait = args.hero_trait or rng.choice(TRAITS)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])

    return StoryParams(
        place=place_id,
        shortcut=shortcut_id,
        sign=sign_id,
        helper=helper_id,
        hero_name=hero_name,
        helper_name=helper_name,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        shortcut = SHORTCUTS[params.shortcut]
        sign = SIGNS[params.sign]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not valid_combo(params.place, params.shortcut, params.sign):
        raise StoryError(explain_rejection(place, shortcut, sign))

    world = tell(
        place=place,
        shortcut=shortcut,
        sign=sign,
        helper_kind=helper,
        hero_name=params.hero_name,
        helper_name=params.helper_name,
        hero_trait=params.hero_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, shortcut, sign) combos:\n")
        for place, shortcut, sign in combos:
            print(f"  {place:14} {shortcut:13} {sign}")
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
            header = f"### {p.hero_name}: {p.shortcut} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
