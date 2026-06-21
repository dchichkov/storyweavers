#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/captive_mum_suspense_comedy.py
=========================================================

A standalone story world about a child who accidentally traps mum in a silly
pretend-play fort. The word "captive" belongs inside the tale itself: mum may
declare, with comic dignity, that she seems to be a captive queen, captain, or
explorer while trying not to spill what she is carrying.

The domain is small and classical:

- A child and a helper build a make-believe scene.
- Mum walks in carrying something tippy.
- A trap from the game catches on her clothing or around her legs.
- The child must choose a rescue method that actually fits the trap.
- Delay and clumsy methods can turn suspense into a splashy comic mess.

The world model tracks physical meters (trapped, wobble, spilled, mess) and
emotional memes (pride, worry, relief, giggles). Prose is driven by those
states, not by frozen templates with swapped nouns.

Run it
------
    python storyworlds/worlds/gpt-5.4/captive_mum_suspense_comedy.py
    python storyworlds/worlds/gpt-5.4/captive_mum_suspense_comedy.py --theme castle --trap ribbon
    python storyworlds/worlds/gpt-5.4/captive_mum_suspense_comedy.py --response yank
    python storyworlds/worlds/gpt-5.4/captive_mum_suspense_comedy.py --all
    python storyworlds/worlds/gpt-5.4/captive_mum_suspense_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/captive_mum_suspense_comedy.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/captive_mum_suspense_comedy.py --json
    python storyworlds/worlds/gpt-5.4/captive_mum_suspense_comedy.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly:
# add storyworlds/ to sys.path from .../storyworlds/worlds/gpt-5.4/<file>.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mum", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mum", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
@dataclass
class Theme:
    id: str
    scene: str
    props: str
    title_for_mum: str
    danger_word: str
    final_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trap:
    id: str
    label: str
    phrase: str
    snag_text: str
    release_verb: str
    difficulty: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    wobble_text: str
    splash_text: str
    tippiness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    power: int
    works_on: set[str]
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_trapped_wobbles(world: World) -> list[str]:
    mum = world.get("mum")
    cargo = world.get("cargo")
    child = world.get("child")
    helper = world.get("helper")
    if mum.meters["trapped"] < THRESHOLD:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["wobble"] += 1
    child.memes["worry"] += 1
    helper.memes["worry"] += 1
    return ["__wobble__"]


def _r_wobble_builds_suspense(world: World) -> list[str]:
    cargo = world.get("cargo")
    room = world.get("room")
    if cargo.meters["wobble"] < THRESHOLD:
        return []
    sig = ("suspense",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.memes["suspense"] += 1
    return ["__suspense__"]


RULES = [
    Rule(name="trapped_wobbles", apply=_r_trapped_wobbles),
    Rule(name="wobble_builds_suspense", apply=_r_wobble_builds_suspense),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness and outcome helpers
# ---------------------------------------------------------------------------
def trap_compatible(response: Response, trap: Trap) -> bool:
    return trap.id in response.works_on


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def trap_severity(trap: Trap, cargo: Cargo, delay: int) -> int:
    return trap.difficulty + cargo.tippiness + delay


def clean_rescue(response: Response, trap: Trap, cargo: Cargo, delay: int) -> bool:
    return response.power >= trap_severity(trap, cargo, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for trap_id, trap in TRAPS.items():
            for cargo_id, cargo in CARGO.items():
                if any(trap_compatible(r, trap) for r in sensible_responses()):
                    combos.append((theme_id, trap_id, cargo_id))
    return combos


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(rr.id for rr in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a calmer rescue such as: {good}.)"
    )


def explain_rejection(trap: Trap, response: Response) -> str:
    return (
        f"(No story: '{response.id}' does not honestly fix {trap.phrase}. "
        f"Choose a method that matches the trap instead of a random gag.)"
    )


def outcome_of(params: "StoryParams") -> str:
    trap = TRAPS[params.trap]
    cargo = CARGO[params.cargo]
    response = RESPONSES[params.response]
    return "clean" if clean_rescue(response, trap, cargo, params.delay) else "splashy"


def predict_mess(world: World, trap_id: str, response_id: str, delay: int) -> dict:
    sim = world.copy()
    trap = TRAPS[trap_id]
    cargo = CARGO[sim.facts["cargo_cfg"].id]
    response = RESPONSES[response_id]
    sim.get("mum").meters["trapped"] += 1
    propagate(sim, narrate=False)
    will_splash = not clean_rescue(response, trap, cargo, delay)
    if will_splash:
        sim.get("cargo").meters["spilled"] += 1
    return {
        "wobble": sim.get("cargo").meters["wobble"],
        "will_splash": will_splash,
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def setup_play(world: World, child: Entity, helper: Entity, theme: Theme) -> None:
    child.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After lunch, {child.id} and {helper.id} turned the hallway into {theme.scene}. "
        f"{theme.props}"
    )
    world.say(
        f"They were so pleased with their work that they kept whispering and then giggling, "
        f"as if the game had become important business."
    )


def announce_mum(world: World, mum: Entity, cargo: Cargo) -> None:
    world.say(
        f"Then {mum.label_word.capitalize()} came along carrying {cargo.phrase}. "
        f"She was trying to walk very carefully so nothing on it would wobble."
    )


def snag(world: World, mum: Entity, trap: Trap, theme: Theme, cargo: Cargo) -> None:
    mum.meters["trapped"] += 1
    cargo_ent = world.get("cargo")
    world.get("trap").meters["tight"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {trap.snag_text}, and {mum.label_word} stopped with one shoe still in the air. "
        f'"Oh dear," she said, going very still. "I appear to be a captive {theme.title_for_mum}."'
    )
    if cargo_ent.meters["wobble"] >= THRESHOLD:
        world.say(
            f"{cargo.wobble_text}. Suddenly the whole hallway felt full of {theme.danger_word}."
        )


def child_reacts(world: World, child: Entity, helper: Entity, mum: Entity, trap: Trap, cargo: Cargo, delay: int) -> None:
    pred = predict_mess(world, trap.id, world.facts["response_cfg"].id, delay)
    world.facts["predicted_splash"] = pred["will_splash"]
    world.facts["predicted_wobble"] = pred["wobble"]
    extra = " even smaller" if pred["will_splash"] else ""
    world.say(
        f'{child.id} stared at the tray. "{helper.id}, don\'t bump anything," {child.pronoun()} whispered. '
        f'The room grew {extra} and quieter, except for one tiny wobble.'
    )


def helper_quip(world: World, helper: Entity, theme: Theme) -> None:
    helper.memes["giggle"] += 1
    world.say(
        f'"Should I bow to the captive {theme.title_for_mum} first?" {helper.id} asked in a squeaky voice. '
        f'Even {helper.pronoun()} looked nervous after saying it.'
    )


def rescue_clean(world: World, child: Entity, mum: Entity, trap: Trap, response: Response, cargo: Cargo) -> None:
    mum.meters["trapped"] = 0.0
    world.get("trap").meters["tight"] = 0.0
    world.get("cargo").meters["wobble"] = 0.0
    child.memes["relief"] += 1
    mum.memes["relief"] += 1
    mum.memes["giggle"] += 1
    world.say(
        f"{child.id} {response.success_text}. In one neat little moment, {trap.phrase} stopped being a trap at all."
    )
    world.say(
        f'{mum.label_word.capitalize()} breathed out and grinned. "Free at last," she said, still holding {cargo.label} without spilling a drop.'
    )


def rescue_splashy(world: World, child: Entity, mum: Entity, trap: Trap, response: Response, cargo: Cargo) -> None:
    mum.meters["trapped"] = 0.0
    world.get("trap").meters["tight"] = 0.0
    world.get("cargo").meters["spilled"] += 1
    world.get("cargo").meters["wobble"] += 1
    child.memes["shock"] += 1
    mum.memes["surprise"] += 1
    mum.memes["giggle"] += 1
    world.say(
        f"{child.id} {response.fail_text}. {cargo.splash_text}"
    )
    world.say(
        f"For half a heartbeat nobody moved. Then {mum.label_word} looked at the splashes on the floor and started to laugh first."
    )


def ending_clean(world: World, child: Entity, helper: Entity, mum: Entity, theme: Theme) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    mum.memes["joy"] += 1
    world.say(
        f'"Next time," {mum.label_word} said, "my rescuers can leave a door for walking through."'
    )
    world.say(
        f"They moved one bit of the fort aside and made a grand safe entrance. Soon {theme.final_image}."
    )


def ending_splashy(world: World, child: Entity, helper: Entity, mum: Entity, cargo: Cargo, theme: Theme) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    mum.memes["relief"] += 1
    world.say(
        f'{mum.label_word.capitalize()} set down what was left of {cargo.label} and handed them a dish towel. '
        f'"A brave rescue team cleans up too," she said, smiling.'
    )
    world.say(
        f"They mopped the floor together, then rebuilt the game with a wide gap in front. Soon {theme.final_image}."
    )


def tell(
    theme: Theme,
    trap: Trap,
    cargo: Cargo,
    response: Response,
    *,
    child_name: str = "Lily",
    child_gender: str = "girl",
    helper_name: str = "Tom",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    delay: int = 0,
    pet: str = "",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    mum = world.add(Entity(id="mum", kind="character", type=parent_type, role="mum", label="the parent"))
    world.add(Entity(id="room", kind="thing", type="hallway", label="hallway"))
    world.add(Entity(id="trap", kind="thing", type="trap", label=trap.label, phrase=trap.phrase))
    world.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo.label, phrase=cargo.phrase))
    world.facts["pet"] = pet
    world.facts["theme"] = theme
    world.facts["trap_cfg"] = trap
    world.facts["cargo_cfg"] = cargo
    world.facts["response_cfg"] = response

    setup_play(world, child, helper, theme)
    world.para()
    announce_mum(world, mum, cargo)
    snag(world, mum, trap, theme, cargo)
    child_reacts(world, child, helper, mum, trap, cargo, delay)
    helper_quip(world, helper, theme)

    world.para()
    if clean_rescue(response, trap, cargo, delay):
        rescue_clean(world, child, mum, trap, response, cargo)
        world.para()
        ending_clean(world, child, helper, mum, theme)
        outcome = "clean"
    else:
        rescue_splashy(world, child, mum, trap, response, cargo)
        world.para()
        ending_splashy(world, child, helper, mum, cargo, theme)
        outcome = "splashy"

    if pet:
        world.say(f"Even {pet} came to inspect the new safe doorway with important little sniffs.")

    world.facts.update(
        child=child,
        helper=helper,
        mum=mum,
        trap=world.get("trap"),
        cargo=world.get("cargo"),
        response=response,
        delay=delay,
        outcome=outcome,
        spilled=world.get("cargo").meters["spilled"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
THEMES = {
    "castle": Theme(
        id="castle",
        scene="a wobbling castle made of chairs and blankets",
        props="A striped blanket was the roof, sofa cushions were the walls, and a shiny mixing bowl stood guard as the royal gong.",
        title_for_mum="queen",
        danger_word="suspense",
        final_image="mum ducked through the new castle gate while the children beat the royal gong and cheered",
        tags={"castle", "fort"},
    ),
    "spaceship": Theme(
        id="spaceship",
        scene="a cardboard spaceship with a very serious launch tunnel",
        props="A cardboard box was the cockpit, two cushions were moon rocks, and a colander became a blinking silver helmet.",
        title_for_mum="captain",
        danger_word="suspense",
        final_image="they counted down from five and watched mum stride through the launch tunnel without touching a thing",
        tags={"spaceship", "fort"},
    ),
    "jungle": Theme(
        id="jungle",
        scene="a leafy jungle trail made from scarves and stools",
        props="Green scarves hung like vines, a laundry basket was the hidden cave, and a wooden spoon served as the explorer flag.",
        title_for_mum="explorer",
        danger_word="suspense",
        final_image="they marched through the trail in a line, laughing because every vine had been tied high and safely away",
        tags={"jungle", "fort"},
    ),
}

TRAPS = {
    "ribbon": Trap(
        id="ribbon",
        label="ribbon",
        phrase="the ribbon loop across the doorway",
        snag_text="the satin ribbon looped around her apron tie",
        release_verb="untie",
        difficulty=1,
        tags={"ribbon", "snag"},
    ),
    "basket": Trap(
        id="basket",
        label="laundry basket",
        phrase="the upside-down laundry basket by the gate",
        snag_text="her foot slipped under the upside-down laundry basket",
        release_verb="lift",
        difficulty=2,
        tags={"basket", "trip"},
    ),
    "tape": Trap(
        id="tape",
        label="sticky tape",
        phrase="the sticky tape holding the cardboard wall",
        snag_text="the sticky tape clung to her cardigan sleeve and tugged the cardboard wall with it",
        release_verb="peel",
        difficulty=2,
        tags={"tape", "snag"},
    ),
}

CARGO = {
    "lemonade": Cargo(
        id="lemonade",
        label="three little cups of lemonade",
        phrase="a tray with three little cups of lemonade",
        wobble_text="The lemonade trembled in the cups",
        splash_text="A bright yellow wave sloshed over the tray and splashed onto the floor",
        tippiness=2,
        tags={"lemonade", "spill"},
    ),
    "muffins": Cargo(
        id="muffins",
        label="a plate of blueberry muffins",
        phrase="a plate of blueberry muffins and two napkins",
        wobble_text="One muffin rolled so close to the edge that both children gasped",
        splash_text="One muffin plopped onto the floor and left a funny purple crumb trail behind it",
        tippiness=1,
        tags={"muffin", "spill"},
    ),
    "soup": Cargo(
        id="soup",
        label="two bowls of tomato soup",
        phrase="a tray with two bowls of tomato soup",
        wobble_text="The red soup made slow shiny circles near the tops of the bowls",
        splash_text="A red splash hopped over the side and dotted the floor like comic little commas",
        tippiness=3,
        tags={"soup", "spill"},
    ),
}

RESPONSES = {
    "untie": Response(
        id="untie",
        label="untie the knot",
        sense=3,
        power=4,
        works_on={"ribbon"},
        success_text="pinched the bow and untied the ribbon before it could pull any tighter",
        fail_text="fumbled at the ribbon bow, and the tray gave a worried wobble before the drinks sloshed",
        qa_text="untied the ribbon carefully and freed mum",
        tags={"untie", "careful"},
    ),
    "lift": Response(
        id="lift",
        label="lift the basket away",
        sense=3,
        power=4,
        works_on={"basket"},
        success_text="lifted the basket straight up and set it aside without bumping mum at all",
        fail_text="hauled at the basket awkwardly, and the sudden jerk made everything on the tray hop",
        qa_text="lifted the basket away carefully and freed mum",
        tags={"lift", "careful"},
    ),
    "peel": Response(
        id="peel",
        label="peel the tape slowly",
        sense=3,
        power=4,
        works_on={"tape"},
        success_text="peeled the tape away slowly so the cardboard wall sagged instead of yanking at mum's sleeve",
        fail_text="picked at the tape too slowly, and the wobble turned into a splash before mum was fully free",
        qa_text="peeled the tape away slowly and freed mum",
        tags={"peel", "careful"},
    ),
    "yank": Response(
        id="yank",
        label="yank hard",
        sense=1,
        power=2,
        works_on={"ribbon", "basket", "tape"},
        success_text="gave the trap a wild yank and, by pure luck, it came loose",
        fail_text="gave the trap a wild yank, which was exactly the wrong sort of excitement for a wobbly tray",
        qa_text="yanked at the trap",
        tags={"clumsy"},
    ),
    "tickle": Response(
        id="tickle",
        label="tickle mum's elbow",
        sense=0,
        power=0,
        works_on=set(),
        success_text="tickled mum's elbow",
        fail_text="tickled mum's elbow, which did absolutely nothing to free her",
        qa_text="tickled mum's elbow",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
PETS = ["the cat", "the puppy", "the little dog", "the kitten", ""]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    theme: str
    trap: str
    cargo: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    delay: int = 0
    pet: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ribbon": [
        (
            "What can happen if you stretch a ribbon across a doorway?",
            "Someone can catch it with a foot or with their clothes and get stuck. Doorways should stay clear so people can walk through safely.",
        )
    ],
    "basket": [
        (
            "Why is a basket on the floor easy to trip on?",
            "A basket on the floor can catch a shoe because it sits where people step. That is why toys and baskets should be put away after play.",
        )
    ],
    "tape": [
        (
            "Why can sticky tape make a mess in a fort?",
            "Sticky tape can cling to sleeves, walls, and paper. If you pull too hard, it can tug the whole fort in a clumsy way.",
        )
    ],
    "lemonade": [
        (
            "Why does lemonade spill when a tray wobbles?",
            "When a tray shakes, the lemonade sloshes from side to side. If it reaches the edge of the cup, it spills out.",
        )
    ],
    "muffin": [
        (
            "Why can a muffin roll off a plate?",
            "A muffin can roll if the plate tilts or jiggles. Food stays safer when you carry it slowly and keep it flat.",
        )
    ],
    "soup": [
        (
            "Why is soup hard to carry without spilling?",
            "Soup is a liquid, so it moves when the bowl moves. Even a small wobble can make it slosh over the edge.",
        )
    ],
    "careful": [
        (
            "What does it mean to rescue someone carefully?",
            "It means helping in a calm way that fits the problem. A careful rescue solves the trouble without making a new mess.",
        )
    ],
    "clumsy": [
        (
            "Why can a clumsy rescue make things worse?",
            "A clumsy rescue adds more bumps and shakes. That can turn a small problem into a spill or a crash.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ribbon", "basket", "tape", "lemonade", "muffin", "soup", "careful", "clumsy"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    theme = world.facts["theme"]
    trap = world.facts["trap_cfg"]
    cargo = world.facts["cargo_cfg"]
    outcome = world.facts["outcome"]
    prompts = [
        f'Write a funny suspense story for a 3-to-5-year-old that includes the words "captive" and "mum".',
        f"Tell a gentle comedy where {child.id} accidentally makes {child.pronoun('possessive')} mum a captive {theme.title_for_mum} with {trap.label} while she carries {cargo.label}.",
    ]
    if outcome == "clean":
        prompts.append(
            "Write a story with a breath-holding middle and a neat rescue, ending in laughter and a safer way to keep playing."
        )
    else:
        prompts.append(
            "Write a story with comic suspense where the rescue is a little too late, something splashes, and the family ends by laughing and cleaning together."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    mum = world.facts["mum"]
    theme = world.facts["theme"]
    trap_cfg = world.facts["trap_cfg"]
    cargo_cfg = world.facts["cargo_cfg"]
    response = world.facts["response"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.id}, and their mum. The children were playing make-believe when mum got caught in part of the game.",
        ),
        (
            "Why did mum become captive?",
            f"Mum became captive because {trap_cfg.snag_text}, so she could not step forward normally. She had to stand very still because she was also carrying {cargo_cfg.label}.",
        ),
        (
            "Why did the moment feel suspenseful?",
            f"It felt suspenseful because {cargo_cfg.wobble_text.lower()}. Everyone knew one wrong bump could make the whole tray tip or splash.",
        ),
        (
            f"What did {helper.id} say that made the moment funny?",
            f"{helper.id} asked whether {helper.pronoun()} should bow to the captive {theme.title_for_mum} first. The joke was silly, but it also showed that everyone was trying not to panic.",
        ),
    ]
    if outcome == "clean":
        qa.append(
            (
                "How did the child solve the problem?",
                f"{child.id} {response.qa_text}. That worked because the rescue matched the trap instead of adding more shaking.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily and neatly. They made a safe doorway in the fort, and mum could walk through while everyone laughed.",
            )
        )
    else:
        qa.append(
            (
                "Did anything spill?",
                f"Yes. {cargo_cfg.splash_text}, but nobody was hurt. The spill happened because the rescue was not strong or calm enough for that trap and wobble.",
            )
        )
        qa.append(
            (
                "How did the family fix things after the splash?",
                f"They cleaned the floor together and rebuilt the game with a safer opening. The ending stays funny because the mistake turns into a better plan instead of a big scolding.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["trap_cfg"].tags) | set(world.facts["cargo_cfg"].tags) | set(world.facts["response"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="castle",
        trap="ribbon",
        cargo="lemonade",
        response="untie",
        child_name="Lily",
        child_gender="girl",
        helper_name="Tom",
        helper_gender="boy",
        parent="mother",
        delay=0,
        pet="the kitten",
    ),
    StoryParams(
        theme="spaceship",
        trap="basket",
        cargo="muffins",
        response="lift",
        child_name="Ben",
        child_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        parent="mother",
        delay=0,
        pet="",
    ),
    StoryParams(
        theme="jungle",
        trap="tape",
        cargo="soup",
        response="peel",
        child_name="Ava",
        child_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        parent="mother",
        delay=0,
        pet="the puppy",
    ),
    StoryParams(
        theme="castle",
        trap="basket",
        cargo="soup",
        response="lift",
        child_name="Theo",
        child_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        parent="mother",
        delay=1,
        pet="the cat",
    ),
    StoryParams(
        theme="spaceship",
        trap="ribbon",
        cargo="lemonade",
        response="untie",
        child_name="Ella",
        child_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="mother",
        delay=1,
        pet="",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(T, Tr, C) :- theme(T), trap(Tr), cargo(C), sensible_fix_exists(Tr).
sensible_fix_exists(Tr) :- response(R), sense(R, S), sense_min(M), S >= M, works_on(R, Tr).

% --- outcome model ---------------------------------------------------------
compatible :- chosen_trap(Tr), chosen_response(R), works_on(R, Tr).
severity(Df + Tp + Dl) :- chosen_trap(Tr), difficulty(Tr, Df),
                          chosen_cargo(C), tippiness(C, Tp), delay(Dl).
clean :- compatible, chosen_response(R), power(R, P), severity(S), P >= S.
outcome(clean) :- clean.
outcome(splashy) :- not clean.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for trap_id, trap in TRAPS.items():
        lines.append(asp.fact("trap", trap_id))
        lines.append(asp.fact("difficulty", trap_id, trap.difficulty))
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("tippiness", cargo_id, cargo.tippiness))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for trap_id in sorted(response.works_on):
            lines.append(asp.fact("works_on", rid, trap_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_trap", params.trap),
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child accidentally makes mum a captive part of a fort, then must rescue her sensibly."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--trap", choices=TRAPS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra wobble pressure before the rescue")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.trap and args.response:
        if not trap_compatible(RESPONSES[args.response], TRAPS[args.trap]):
            raise StoryError(explain_rejection(TRAPS[args.trap], RESPONSES[args.response]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.trap is None or combo[1] == args.trap)
        and (args.cargo is None or combo[2] == args.cargo)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, trap_id, cargo_id = rng.choice(sorted(combos))
    response_id = args.response
    if response_id is None:
        compatible = [
            r.id
            for r in sensible_responses()
            if trap_compatible(r, TRAPS[trap_id])
        ]
        response_id = rng.choice(sorted(compatible))

    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child_name = _pick_name(rng, child_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=child_name)
    parent = args.parent or "mother"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    pet = rng.choice(PETS)

    return StoryParams(
        theme=theme_id,
        trap=trap_id,
        cargo=cargo_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        delay=delay,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        trap = TRAPS[params.trap]
        cargo = CARGO[params.cargo]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not trap_compatible(response, trap):
        raise StoryError(explain_rejection(trap, response))

    world = tell(
        theme=theme,
        trap=trap,
        cargo=cargo,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        delay=params.delay,
        pet=params.pet,
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
        print(f"{len(combos)} compatible (theme, trap, cargo) combos:\n")
        for theme, trap, cargo in combos:
            print(f"  {theme:10} {trap:8} {cargo}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.theme} with {p.trap} and {p.cargo} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
