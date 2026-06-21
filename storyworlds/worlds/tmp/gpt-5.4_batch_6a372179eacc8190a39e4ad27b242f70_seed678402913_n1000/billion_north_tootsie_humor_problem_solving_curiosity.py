#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/billion_north_tootsie_humor_problem_solving_curiosity.py
===================================================================================

A standalone storyworld for a nursery-rhyme-style tale about a curious child,
a duck named Tootsie, and a round little thing that the north wind blows away.

The tiny domain is deliberately narrow and state-driven:

- a child is counting something with comic exaggeration ("a billion")
- the north wind nudges one piece away
- Tootsie the duck helps the child investigate where it went
- the child solves the problem with a sensible tool
- the ending proves the lesson by showing a calmer new way to keep count

The script supports the standard Storyweavers world interface:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
and --show-asp.
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
# This file lives under storyworlds/worlds/gpt-5.4/, so three dirname() calls
# reach storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"duck", "bird", "animal"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    ground: str
    north_spot: str
    breeze_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CountingThing:
    id: str
    label: str
    phrase: str
    plural: str
    tiny_sound: str
    rolls: bool = True
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    clue: str
    need: str = ""
    wet: bool = False
    gentle_only: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    affordances: set[str] = field(default_factory=set)
    gentle: bool = False
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    thing: str
    hiding_place: str
    tool: str
    child_name: str
    child_gender: str
    child_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World + causal rules
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lost_makes_worry(world: World) -> list[str]:
    child = world.entities.get("child")
    thing = world.entities.get("thing")
    if not child or not thing:
        return []
    if thing.meters["lost"] < THRESHOLD:
        return []
    sig = ("worry", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return []


def _r_clue_feeds_curiosity(world: World) -> list[str]:
    child = world.entities.get("child")
    if not child:
        return []
    if world.facts.get("clue_seen", 0.0) < THRESHOLD:
        return []
    sig = ("curious", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    return []


def _r_found_brings_relief(world: World) -> list[str]:
    child = world.entities.get("child")
    duck = world.entities.get("duck")
    thing = world.entities.get("thing")
    if not child or not duck or not thing:
        return []
    if thing.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", thing.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    duck.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="lost_makes_worry", tag="emotion", apply=_r_lost_makes_worry),
    Rule(name="clue_feeds_curiosity", tag="emotion", apply=_r_clue_feeds_curiosity),
    Rule(name="found_brings_relief", tag="emotion", apply=_r_found_brings_relief),
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
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def tool_works(tool: Tool, hiding_place: HidingPlace, thing: CountingThing) -> bool:
    if hiding_place.need and hiding_place.need not in tool.affordances:
        return False
    if hiding_place.wet and "scoop" not in tool.affordances:
        return False
    if hiding_place.gentle_only and thing.fragile and not tool.gentle:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for thing_id, thing in THINGS.items():
            if not thing.rolls:
                continue
            for hiding_id, hiding in HIDING_PLACES.items():
                for tool_id, tool in TOOLS.items():
                    if tool_works(tool, hiding, thing):
                        combos.append((setting_id, thing_id, hiding_id, tool_id))
    return combos


def explain_rejection(thing: CountingThing, hiding_place: HidingPlace, tool: Tool) -> str:
    if hiding_place.need and hiding_place.need not in tool.affordances:
        return (
            f"(No story: {tool.label} does not fit the problem. "
            f"{hiding_place.phrase.capitalize()} needs a tool that can {hiding_place.need}.)"
        )
    if hiding_place.wet and "scoop" not in tool.affordances:
        return (
            f"(No story: {hiding_place.phrase.capitalize()} is wet, so the child needs a tool "
            f"that can scoop the {thing.label} out instead of just poking at it.)"
        )
    if hiding_place.gentle_only and thing.fragile and not tool.gentle:
        return (
            f"(No story: {thing.phrase.capitalize()} is too delicate for {tool.label}. "
            f"This storyworld prefers a gentler fix.)"
        )
    return "(No story: this combination is not reasonable in the world model.)"


# ---------------------------------------------------------------------------
# Prediction helper
# ---------------------------------------------------------------------------
def predict_recovery(thing: CountingThing, hiding_place: HidingPlace, tool: Tool) -> dict:
    return {
        "works": tool_works(tool, hiding_place, thing),
        "wet": hiding_place.wet,
        "gentle_needed": hiding_place.gentle_only and thing.fragile,
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, duck: Entity, setting: Setting, thing: CountingThing) -> None:
    child.memes["joy"] += 1
    duck.memes["joy"] += 1
    world.say(
        f"{child.id} skipped through {setting.place}, curious as could be. "
        f"Beside {child.pronoun('object')} waddled Tootsie the duck, bobbing like a little yellow boat."
    )
    world.say(
        f'Together they counted {thing.plural} on the {setting.ground}: '
        f'"One, two, ten, twenty, maybe a billion!" laughed {child.id}.'
    )


def north_wind_turn(world: World, child: Entity, duck: Entity, setting: Setting, thing: CountingThing) -> None:
    item = world.get("thing")
    item.meters["rolling"] += 1
    item.meters["lost"] += 1
    world.facts["northward"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then came the north wind, nimble and bold. {setting.breeze_line.capitalize()}, "
        f"and one {thing.label} went {thing.tiny_sound} away."
    )
    world.say(
        f'Over the path it spun and skipped. "Oh, my little {thing.label}!" cried {child.id}. '
        f'Tootsie gave a comical "quup!" and hurried north.'
    )


def inspect_clue(world: World, child: Entity, duck: Entity, hiding_place: HidingPlace) -> None:
    world.facts["clue_seen"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{child.id} followed Tootsie to {hiding_place.phrase}. "
        f"There {child.pronoun()} saw {hiding_place.clue}."
    )
    world.say(
        f'"Now that is queer," said {child.id}. "{child.pronoun().capitalize()} went north, so where did it nestle?"'
    )


def ponder(world: World, child: Entity, hiding_place: HidingPlace, tool: Tool, thing: CountingThing) -> None:
    pred = predict_recovery(thing, hiding_place, tool)
    world.facts["predicted_works"] = pred["works"]
    child.memes["thinking"] += 1
    if pred["wet"]:
        extra = f" {child.pronoun().capitalize()} needed something that could scoop, not just scratch."
    elif pred["gentle_needed"]:
        extra = f" {child.pronoun().capitalize()} needed something soft and gentle, so the little treat would not break."
    else:
        extra = f" {child.pronoun().capitalize()} needed something that matched the nook."
    world.say(
        f"{child.id} tapped {child.pronoun('possessive')} chin and thought a thoughtful thought.{extra}"
    )


def solve(world: World, child: Entity, duck: Entity, hiding_place: HidingPlace, tool: Tool, thing: CountingThing) -> None:
    item = world.get("thing")
    item.meters["found"] += 1
    item.meters["lost"] = 0.0
    world.facts["solved_with"] = tool.label
    world.facts["found_at"] = hiding_place.label
    propagate(world, narrate=False)
    if hiding_place.id == "reed_puddle":
        action = f"slid {tool.phrase} under the water, lifted slowly, and brought the {thing.label} up shining"
    elif hiding_place.id == "hedge_gap":
        action = f"reached with {tool.phrase}, hooked the {thing.label}, and drew it out with a tidy tug"
    else:
        action = f"looped {tool.phrase} around the {thing.label} and lifted it free without a crack"
    world.say(
        f"So {child.id} fetched {tool.phrase}, {action}. "
        f'Tootsie flapped her wings as if to say, "Well done, well done!"'
    )


def closing(world: World, child: Entity, duck: Entity, setting: Setting, thing: CountingThing, tool: Tool) -> None:
    child.memes["calm"] += 1
    world.say(
        f"Back on the warm {setting.ground}, {child.id} counted again, only slower this time. "
        f'"Not a billion all at once," {child.pronoun()} giggled. "Just enough for me, and one for Tootsie."'
    )
    world.say(
        f"So the north wind hummed, Tootsie munched her share, and the last little {thing.label} sat safe beside {tool.label}. "
        f"That was the joke and the lesson together: curious eyes and a clever plan can make a muddle merry."
    )


# ---------------------------------------------------------------------------
# Story builder
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    thing: CountingThing,
    hiding_place: HidingPlace,
    tool: Tool,
    child_name: str = "Mina",
    child_gender: str = "girl",
    child_trait: str = "curious",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[child_trait],
        )
    )
    duck = world.add(
        Entity(
            id="Tootsie",
            kind="character",
            type="duck",
            label="Tootsie",
            phrase="Tootsie the duck",
            role="helper",
            tags={"tootsie", "duck"},
        )
    )
    item = world.add(
        Entity(
            id="thing",
            kind="thing",
            type=thing.id,
            label=thing.label,
            phrase=thing.phrase,
            tags=set(thing.tags),
        )
    )

    introduce(world, child, duck, setting, thing)
    world.para()
    north_wind_turn(world, child, duck, setting, thing)
    inspect_clue(world, child, duck, hiding_place)
    world.para()
    ponder(world, child, hiding_place, tool, thing)
    solve(world, child, duck, hiding_place, tool, thing)
    world.para()
    closing(world, child, duck, setting, thing, tool)

    world.facts.update(
        child=child,
        duck=duck,
        setting=setting,
        thing_cfg=thing,
        hiding_cfg=hiding_place,
        tool_cfg=tool,
        found=item.meters["found"] >= THRESHOLD,
        worried=child.memes["worry"] >= THRESHOLD,
        curious=child.memes["curiosity"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lane": Setting(
        id="lane",
        place="a cobbled lane",
        ground="stones",
        north_spot="the lane's north bend",
        breeze_line="up from the north came a whisking breeze",
        tags={"lane"},
    ),
    "garden": Setting(
        id="garden",
        place="a tulip garden",
        ground="grass",
        north_spot="the garden's north hedge",
        breeze_line="from the north came a whistling puff",
        tags={"garden"},
    ),
    "yard": Setting(
        id="yard",
        place="a sunny yard",
        ground="flagstones",
        north_spot="the yard's north fence",
        breeze_line="down from the north came a hopping gust",
        tags={"yard"},
    ),
}

THINGS = {
    "bun": CountingThing(
        id="bun",
        label="bun",
        phrase="a round honey bun",
        plural="buns",
        tiny_sound="bumpity-bump",
        fragile=False,
        tags={"bun", "counting"},
    ),
    "plum": CountingThing(
        id="plum",
        label="plum",
        phrase="a purple plum",
        plural="plums",
        tiny_sound="plip-plop",
        fragile=True,
        tags={"plum", "counting"},
    ),
    "button": CountingThing(
        id="button",
        label="button",
        phrase="a bright brass button",
        plural="buttons",
        tiny_sound="ting-a-ting",
        fragile=False,
        tags={"button", "counting"},
    ),
}

HIDING_PLACES = {
    "hedge_gap": HidingPlace(
        id="hedge_gap",
        label="hedge gap",
        phrase="the north hedge gap",
        clue="two leaves wobbling and a tiny round shine beneath them",
        need="hook",
        wet=False,
        gentle_only=False,
        tags={"hedge"},
    ),
    "reed_puddle": HidingPlace(
        id="reed_puddle",
        label="reed puddle",
        phrase="the reedy puddle by the north fence",
        clue="a small circle wobbling under the water and reeds",
        need="scoop",
        wet=True,
        gentle_only=False,
        tags={"puddle"},
    ),
    "basket_crack": HidingPlace(
        id="basket_crack",
        label="basket crack",
        phrase="the crack beside an old market basket",
        clue="one purple peek between the wicker sticks",
        need="loop",
        wet=False,
        gentle_only=True,
        tags={"basket"},
    ),
}

TOOLS = {
    "rake": Tool(
        id="rake",
        label="rake",
        phrase="the little rake",
        affordances={"hook"},
        gentle=False,
        tags={"rake"},
    ),
    "ladle": Tool(
        id="ladle",
        label="ladle",
        phrase="the long-handled ladle",
        affordances={"scoop"},
        gentle=True,
        tags={"ladle"},
    ),
    "ribbon_loop": Tool(
        id="ribbon_loop",
        label="ribbon loop",
        phrase="a ribbon loop on a stick",
        affordances={"loop"},
        gentle=True,
        tags={"ribbon"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Poppy", "Nora", "Daisy", "Tilly"]
BOY_NAMES = ["Ollie", "Toby", "Ned", "Milo", "Pip", "Jory"]
TRAITS = ["curious", "merry", "bright", "bouncy", "thoughtful"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "north": [
        (
            "What does north mean?",
            "North is one of the directions on a compass. It helps people say which way something went."
        )
    ],
    "wind": [
        (
            "What can wind do to small round things?",
            "Wind can push light little things and make them roll or slide away. Round things move especially easily because they do not stay still."
        )
    ],
    "duck": [
        (
            "What is a duck good at noticing?",
            "A duck notices little splashes, shiny spots, and wiggly things on the ground. That is why a duck can make a funny helper in a small story."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means stopping to think about what is wrong and choosing a tool or plan that fits. A clever plan works better than grabbing the first thing you see."
        )
    ],
    "counting": [
        (
            "Do people really count to a billion in one breath?",
            "No, that is a joke. Stories often use giant numbers like a billion to sound funny and playful."
        )
    ],
    "tool": [
        (
            "Why should a tool match the job?",
            "Different problems need different tools. A scoop helps with wet things, while a hook or loop helps with things stuck in narrow places."
        )
    ],
}

KNOWLEDGE_ORDER = ["north", "wind", "duck", "problem_solving", "counting", "tool"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    thing = f["thing_cfg"]
    hiding = f["hiding_cfg"]
    tool = f["tool_cfg"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "billion", "north", and "Tootsie".',
        f"Tell a playful story where a {child.type} named {child.id} loses one {thing.label} to the north wind, follows Tootsie the duck, and solves the problem with {tool.phrase}.",
        f"Write a funny, curious little rhyme-story where counting grows silly, a tiny thing hides in {hiding.phrase}, and the child uses the right tool instead of guessing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    duck = f["duck"]
    thing = f["thing_cfg"]
    hiding = f["hiding_cfg"]
    tool = f["tool_cfg"]
    setting = f["setting"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and Tootsie the duck in {setting.place}. They start by counting {thing.plural} together."
        ),
        (
            f"Why did {child.id} say 'a billion'?",
            f"{child.id} was joking while counting and made the number much bigger than real life. The silly exaggeration gives the story its nursery-rhyme humor."
        ),
        (
            f"What went wrong in the story?",
            f"The north wind blew one {thing.label} away, and it rolled out of the child's neat counting line. That made {child.id} worry and then start looking for clues."
        ),
        (
            f"How did Tootsie help?",
            f"Tootsie hurried north and led {child.id} to {hiding.phrase}. Her waddling search turned the child's worry into curiosity because it gave a clue about where the missing {thing.label} had gone."
        ),
        (
            f"How did {child.id} solve the problem?",
            f"{child.id} stopped to think about what kind of place the {thing.label} had fallen into and then chose {tool.phrase}. The tool matched the job, so the lost {thing.label} could be brought back safely."
        ),
        (
            "How did the story end?",
            f"It ended with {child.id} counting more calmly and sharing with Tootsie. The final image shows that the muddle became manageable once the child used a clever plan."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"north", "wind", "duck", "problem_solving", "counting", "tool"}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="garden",
        thing="bun",
        hiding_place="hedge_gap",
        tool="rake",
        child_name="Mina",
        child_gender="girl",
        child_trait="curious",
    ),
    StoryParams(
        setting="yard",
        thing="button",
        hiding_place="reed_puddle",
        tool="ladle",
        child_name="Ollie",
        child_gender="boy",
        child_trait="thoughtful",
    ),
    StoryParams(
        setting="lane",
        thing="plum",
        hiding_place="basket_crack",
        tool="ribbon_loop",
        child_name="Lulu",
        child_gender="girl",
        child_trait="merry",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
rollable(T) :- thing(T), rolls(T).

works(Tool, Hide, Thing) :-
    tool(Tool), hiding_place(Hide), thing(Thing),
    rollable(Thing),
    need(Hide, Need), affordance(Tool, Need),
    not wet(Hide),
    not fragile(Thing).

works(Tool, Hide, Thing) :-
    tool(Tool), hiding_place(Hide), thing(Thing),
    rollable(Thing),
    need(Hide, Need), affordance(Tool, Need),
    not wet(Hide),
    fragile(Thing), gentle(Tool), gentle_only(Hide).

works(Tool, Hide, Thing) :-
    tool(Tool), hiding_place(Hide), thing(Thing),
    rollable(Thing),
    affordance(Tool, scoop),
    wet(Hide),
    not fragile(Thing).

works(Tool, Hide, Thing) :-
    tool(Tool), hiding_place(Hide), thing(Thing),
    rollable(Thing),
    affordance(Tool, scoop),
    wet(Hide),
    fragile(Thing), not gentle_only(Hide).

works(Tool, Hide, Thing) :-
    tool(Tool), hiding_place(Hide), thing(Thing),
    rollable(Thing),
    affordance(Tool, scoop),
    wet(Hide),
    fragile(Thing), gentle_only(Hide), gentle(Tool).

valid(Setting, Thing, Hide, Tool) :-
    setting(Setting), thing(Thing), hiding_place(Hide), tool(Tool),
    works(Tool, Hide, Thing).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for thing_id, thing in THINGS.items():
        lines.append(asp.fact("thing", thing_id))
        if thing.rolls:
            lines.append(asp.fact("rolls", thing_id))
        if thing.fragile:
            lines.append(asp.fact("fragile", thing_id))
    for hiding_id, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding_place", hiding_id))
        lines.append(asp.fact("need", hiding_id, hiding.need))
        if hiding.wet:
            lines.append(asp.fact("wet", hiding_id))
        if hiding.gentle_only:
            lines.append(asp.fact("gentle_only", hiding_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for affordance in sorted(tool.affordances):
            lines.append(asp.fact("affordance", tool_id, affordance))
        if tool.gentle:
            lines.append(asp.fact("gentle", tool_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    # Smoke test ordinary generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: Tootsie, the north wind, and a small counting problem."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--hiding-place", dest="hiding_place", choices=HIDING_PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--trait", dest="child_trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and args.hiding_place and args.tool:
        thing = THINGS[args.thing]
        hiding = HIDING_PLACES[args.hiding_place]
        tool = TOOLS[args.tool]
        if not tool_works(tool, hiding, thing):
            raise StoryError(explain_rejection(thing, hiding, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.thing is None or combo[1] == args.thing)
        and (args.hiding_place is None or combo[2] == args.hiding_place)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, thing_id, hiding_id, tool_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    child_trait = args.child_trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        thing=thing_id,
        hiding_place=hiding_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=child_gender,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.thing not in THINGS:
        raise StoryError(f"(Unknown thing: {params.thing})")
    if params.hiding_place not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding_place})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    setting = SETTINGS[params.setting]
    thing = THINGS[params.thing]
    hiding = HIDING_PLACES[params.hiding_place]
    tool = TOOLS[params.tool]

    if not tool_works(tool, hiding, thing):
        raise StoryError(explain_rejection(thing, hiding, tool))

    world = tell(
        setting=setting,
        thing=thing,
        hiding_place=hiding,
        tool=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_trait=params.child_trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, thing, hiding_place, tool) combos:\n")
        for setting_id, thing_id, hiding_id, tool_id in combos:
            print(f"  {setting_id:8} {thing_id:7} {hiding_id:12} {tool_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.thing} in {p.hiding_place} at {p.setting} ({p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
