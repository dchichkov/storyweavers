#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ignite_crevice_fatten_lesson_learned_mystery_to.py
==============================================================================

A small detective-story storyworld about a child solving the mystery of missing
food near a dark hiding place. The key turn is not "who did it?" alone, but
"how do we look safely?" The child first wants to ignite a tiny paper torch to
peer into a crevice, then learns to use a safe light instead.

The domain is deliberately narrow and constraint-checked:
- the suspect must actually like the missing food
- the suspect must plausibly fit in the chosen hideout
- the chosen tool must be a sensible way to inspect a dark gap

The stories aim for a complete arc:
premise -> clues -> risky idea -> wiser method -> mystery solved -> lesson learned
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    wall_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    crumbs: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    track: str
    motive: str
    likes: set[str] = field(default_factory=set)
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    dark_word: str
    dry: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    gives_light: bool
    risky: bool
    inspect_text: str
    lesson_text: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clue_trail(world: World) -> list[str]:
    out: list[str] = []
    pantry = world.get("pantry")
    hideout = world.get("hideout")
    if pantry.meters["food_missing"] >= THRESHOLD and hideout.meters["stash"] >= THRESHOLD:
        sig = ("clue_trail",)
        if sig not in world.fired:
            world.fired.add(sig)
            hideout.meters["clue_found"] += 1
            for eid in ("detective", "helper"):
                if eid in world.entities:
                    world.get(eid).memes["curiosity"] += 1
            out.append("__clue__")
    return out


def _r_safe_light(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    hideout = world.get("hideout")
    if tool.meters["used"] >= THRESHOLD and tool.attrs.get("gives_light"):
        sig = ("safe_light",)
        if sig not in world.fired:
            world.fired.add(sig)
            hideout.meters["visible"] += 1
            out.append("__light__")
    return out


CAUSAL_RULES = [
    Rule(name="clue_trail", tag="mystery", apply=_r_clue_trail),
    Rule(name="safe_light", tag="physical", apply=_r_safe_light),
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
        for sent in produced:
            world.say(sent)
    return produced


def suspect_likes_food(suspect: Suspect, food: Food) -> bool:
    return food.id in suspect.likes


def suspect_fits_hideout(suspect: Suspect, hideout: Hideout) -> bool:
    return hideout.id in suspect.fits


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN and tool.gives_light and not tool.risky]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for food_id, food in FOODS.items():
            for suspect_id, suspect in SUSPECTS.items():
                for hideout_id, hideout in HIDEOUTS.items():
                    if suspect_likes_food(suspect, food) and suspect_fits_hideout(suspect, hideout):
                        combos.append((place_id, food_id, suspect_id, hideout_id))
    return combos


def predict_risk(world: World) -> dict:
    sim = world.copy()
    tool = sim.get("tool")
    hideout = sim.get("hideout")
    if tool.attrs.get("risky") and hideout.attrs.get("dry"):
        hideout.meters["risk"] += 1
    return {
        "risk": hideout.meters["risk"],
        "dry": bool(hideout.attrs.get("dry")),
    }


def opening(world: World, detective: Entity, helper: Entity, adult: Entity,
            place: Place, food: Food) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    pantry = world.get("pantry")
    pantry.meters["food_missing"] += 1
    world.say(
        f"After lunch in {place.label}, {detective.id} stopped short beside the picnic basket. "
        f"{food.phrase.capitalize()} were missing again."
    )
    world.say(
        f"{detective.id} loved mysteries and whispered, "
        f'"This is a case." {helper.id} nodded at once, and even {adult.label_word} smiled.'
    )
    world.say(
        f"The only clues were {food.crumbs} leading away from the basket and toward {place.wall_word}."
    )


def inspect_clues(world: World, detective: Entity, helper: Entity, suspect: Suspect,
                  hideout: Hideout, place: Place, food: Food) -> None:
    hideout_ent = world.get("hideout")
    hideout_ent.meters["stash"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The two little detectives followed the trail across {place.scene}. "
        f"Near {hideout.phrase}, they found {suspect.track} and one last bit of {food.label}."
    )
    world.say(
        f'"The thief must be close," {helper.id} said. But {hideout.phrase} was dark, '
        f"and the inside looked deeper than it had from far away."
    )


def risky_idea(world: World, detective: Entity, helper: Entity, tool: Tool) -> None:
    detective.memes["impatience"] += 1
    world.say(
        f'{detective.id} leaned closer. "Maybe I can ignite a tiny paper twist and peek inside," '
        f"{detective.pronoun()} said."
    )
    world.say(
        f"{helper.id}'s eyes widened. The mystery still mattered, but so did whatever might be hiding there."
    )


def wiser_warning(world: World, detective: Entity, helper: Entity, adult: Entity,
                  hideout: Hideout) -> None:
    pred = predict_risk(world)
    helper.memes["caution"] += 1
    adult.memes["care"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'"No," {helper.id} said quickly. "A flame near a dark place like that could scare an animal or start trouble in the dry little space."'
    )
    world.say(
        f'{adult.label_word.capitalize()} crouched beside them and nodded. '
        f'"A careful detective uses safe tools first."'
    )


def choose_safe_tool(world: World, detective: Entity, helper: Entity, tool: Tool) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["used"] += 1
    propagate(world, narrate=False)
    detective.memes["patience"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Instead, {helper.id} handed {detective.id} {tool.phrase}. "
        f"{tool.inspect_text.capitalize()}."
    )


def reveal(world: World, detective: Entity, helper: Entity, suspect: Suspect,
           food: Food, hideout: Hideout) -> None:
    detective.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    hideout_ent = world.get("hideout")
    if hideout_ent.meters["visible"] < THRESHOLD:
        raise StoryError("(Story logic failed: the hideout never became visible.)")
    world.say(
        f"The beam slid into {hideout.phrase} and found the answer at last: {suspect.phrase}."
    )
    world.say(
        f"Inside the little hiding place were bits of {food.label}, tucked in neatly. "
        f"{suspect.label.capitalize()} was not being mean. {suspect.motive}"
    )


def resolution(world: World, detective: Entity, helper: Entity, adult: Entity,
               suspect: Suspect, food: Food, place: Place, tool: Tool) -> None:
    detective.memes["pride"] += 1
    helper.memes["pride"] += 1
    detective.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f'{adult.label_word.capitalize()} set a small dish of extra {food.label} near the edge of {place.label}, far from the basket. '
        f'"Now our guest can nibble there instead," {adult.pronoun()} said.'
    )
    world.say(
        f'{detective.id} grinned. "We solved the mystery without smoke or sparks." '
        f'{helper.id} grinned back and brushed a crumb from {helper.pronoun("possessive")} sleeve.'
    )
    world.say(
        f"That evening, the case went into {detective.id}'s notebook with a bright red title: "
        f'"The Mystery of the Missing {food.label.capitalize()}." Under it, {detective.pronoun()} wrote the lesson learned: '
        f'"When you want to solve a mystery, {tool.lesson_text}."'
    )


def tell(place: Place, food: Food, suspect: Suspect, hideout: Hideout, tool: Tool,
         detective_name: str = "Nora", detective_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         adult_type: str = "aunt") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the adult"))
    world.add(Entity(id="pantry", type="basket", label="picnic basket"))
    world.add(Entity(
        id="hideout",
        type="hideout",
        label=hideout.label,
        phrase=hideout.phrase,
        attrs={"dry": hideout.dry},
        tags=set(hideout.tags),
    ))
    world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        attrs={"gives_light": tool.gives_light, "risky": tool.risky},
        tags=set(tool.tags),
    ))

    opening(world, detective, helper, adult, place, food)
    world.para()
    inspect_clues(world, detective, helper, suspect, hideout, place, food)
    risky_idea(world, detective, helper, tool)
    wiser_warning(world, detective, helper, adult, hideout)
    world.para()
    choose_safe_tool(world, detective, helper, tool)
    reveal(world, detective, helper, suspect, food, hideout)
    world.para()
    resolution(world, detective, helper, adult, suspect, food, place, tool)

    world.facts.update(
        place=place,
        food=food,
        suspect=suspect,
        hideout_cfg=hideout,
        tool_cfg=tool,
        detective=detective,
        helper=helper,
        adult=adult,
        solved=True,
        risky_idea=True,
        lesson=True,
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        scene="the warm stepping stones and the bean patch",
        wall_word="the old stone wall",
        tags={"garden"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        scene="the brick path and the rain barrel",
        wall_word="the cracked brick step",
        tags={"courtyard"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard",
        scene="the grass under the pear trees",
        wall_word="the low orchard wall",
        tags={"orchard"},
    ),
}

FOODS = {
    "seeds": Food(
        id="seeds",
        label="sunflower seeds",
        phrase="sunflower seeds",
        crumbs="tiny striped seed shells",
        tags={"seeds", "food"},
    ),
    "pear": Food(
        id="pear",
        label="pear slices",
        phrase="pear slices",
        crumbs="sticky pear drops",
        tags={"pear", "food"},
    ),
    "corn": Food(
        id="corn",
        label="corn kernels",
        phrase="corn kernels",
        crumbs="bright yellow kernels",
        tags={"corn", "food"},
    ),
}

SUSPECTS = {
    "chipmunk": Suspect(
        id="chipmunk",
        label="chipmunk",
        phrase="a chipmunk with bulging cheeks and bright pebble eyes",
        track="tiny claw prints",
        motive="It was gathering snacks to fatten up before cold weather came.",
        likes={"seeds", "corn"},
        fits={"crevice", "step_gap"},
        tags={"chipmunk", "winter"},
    ),
    "field_mouse": Suspect(
        id="field_mouse",
        label="field mouse",
        phrase="a field mouse with whiskers twitching like little threads",
        track="soft mouse prints",
        motive="It was making a snug stash to fatten itself for winter nights.",
        likes={"seeds", "pear", "corn"},
        fits={"crevice", "floor_crack", "step_gap"},
        tags={"mouse", "winter"},
    ),
    "squirrel": Suspect(
        id="squirrel",
        label="squirrel",
        phrase="a young squirrel with a curled tail and busy paws",
        track="quick scratch marks",
        motive="It was hiding food to fatten up for winter, one stolen bite at a time.",
        likes={"pear", "corn"},
        fits={"floor_crack", "step_gap"},
        tags={"squirrel", "winter"},
    ),
}

HIDEOUTS = {
    "crevice": Hideout(
        id="crevice",
        label="crevice",
        phrase="a narrow crevice in the wall",
        dark_word="crevice",
        dry=True,
        tags={"crevice", "wall"},
    ),
    "floor_crack": Hideout(
        id="floor_crack",
        label="floor crack",
        phrase="a dark crack under the shed floor",
        dark_word="crack",
        dry=True,
        tags={"crack", "shed"},
    ),
    "step_gap": Hideout(
        id="step_gap",
        label="step gap",
        phrase="the hollow gap under the back step",
        dark_word="gap",
        dry=True,
        tags={"gap", "step"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        sense=3,
        gives_light=True,
        risky=False,
        inspect_text="Its clear circle of light reached the dark hiding place without touching it",
        lesson_text="use light, patience, and kind eyes before you use anything dangerous",
        tags={"flashlight", "safe_light"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a camping lantern",
        sense=2,
        gives_light=True,
        risky=False,
        inspect_text="The soft lantern glow filled the hiding place gently",
        lesson_text="gentle light is better than a hot, hasty idea",
        tags={"lantern", "safe_light"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a magnifying glass and a pocket lamp",
        sense=2,
        gives_light=True,
        risky=False,
        inspect_text="The pocket lamp shone while the magnifying glass made every crumb and whisker mark easier to see",
        lesson_text="the best detectives look closely instead of rushing",
        tags={"magnifier", "safe_light"},
    ),
    "paper_torch": Tool(
        id="paper_torch",
        label="paper torch",
        phrase="a rolled paper torch",
        sense=0,
        gives_light=False,
        risky=True,
        inspect_text="",
        lesson_text="",
        tags={"fire", "unsafe"},
    ),
    "match": Tool(
        id="match",
        label="match",
        phrase="a match",
        sense=1,
        gives_light=False,
        risky=True,
        inspect_text="",
        lesson_text="",
        tags={"fire", "unsafe"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lucy", "Ava", "Ella", "Zoe", "Ivy", "Lena"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Owen", "Theo", "Eli"]


@dataclass
class StoryParams:
    place: str
    food: str
    suspect: str
    hideout: str
    tool: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    adult: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "crevice": [
        (
            "What is a crevice?",
            "A crevice is a very narrow crack or opening in stone, wood, or another hard thing. Small animals can hide things inside it."
        )
    ],
    "ignite": [
        (
            "What does ignite mean?",
            "Ignite means to start a fire or make something begin to burn. That is why children should let grown-ups handle flames."
        )
    ],
    "fatten": [
        (
            "What does fatten up for winter mean?",
            "It means an animal eats and stores extra food before cold weather comes. The extra food helps it stay strong when winter is harder."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight safer than a flame in a dark crack?",
            "A flashlight gives light without fire or smoke. That makes it a much safer way to look into a dark place."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light that can brighten a space. A battery lantern can help you see without making a flame."
        )
    ],
    "magnifier": [
        (
            "What does a magnifying glass do?",
            "A magnifying glass makes tiny things look bigger. Detectives use it to notice clues they might miss."
        )
    ],
    "chipmunk": [
        (
            "Why do chipmunks store food?",
            "Chipmunks hide food so they can eat later. They are busy gatherers, especially when colder weather is coming."
        )
    ],
    "mouse": [
        (
            "Why does a field mouse hide food?",
            "A field mouse hides food to keep a small safe supply nearby. That helps it when food is harder to find."
        )
    ],
    "squirrel": [
        (
            "Why do squirrels hide snacks?",
            "Squirrels hide snacks in many places so they can find them later. Storing food helps them get ready for leaner days."
        )
    ],
}
KNOWLEDGE_ORDER = ["ignite", "crevice", "fatten", "flashlight", "lantern", "magnifier", "chipmunk", "mouse", "squirrel"]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two young detectives"
    if a.type == "boy" and b.type == "boy":
        return "two young detectives"
    return "two young detectives"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    food = f["food"]
    suspect = f["suspect"]
    hideout = f["hideout_cfg"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the words "ignite", "crevice", and "fatten".',
        f"Tell a mystery-to-solve story where {detective.id} and {helper.id} follow clues about missing {food.label} to {hideout.phrase} and discover {suspect.label}.",
        f"Write a child-friendly detective tale with a lesson learned: the children solve the case by using a safe light instead of trying to ignite something dangerous.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    adult = f["adult"]
    food = f["food"]
    suspect = f["suspect"]
    hideout = f["hideout_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(detective, helper)}, {detective.id} and {helper.id}, who try to solve the mystery of the missing {food.label}. {adult.label_word.capitalize()} helps them make a safe choice."
        ),
        (
            f"What was the mystery to solve?",
            f"The children wanted to know who kept taking the {food.label} from the basket. The clue trail led them toward {hideout.phrase}."
        ),
        (
            f"Why did {detective.id} want to ignite something?",
            f"{detective.id} wanted a quick way to see into the dark hiding place. {detective.pronoun().capitalize()} thought a tiny flame might help, but it was not a safe idea."
        ),
        (
            f"Why did {helper.id} say no?",
            f"{helper.id} knew a flame in a dry dark place could scare the hidden animal or start bigger trouble. That is why {helper.pronoun()} urged {detective.id} to use a safer tool."
        ),
        (
            f"How did they solve the mystery?",
            f"They used {tool.phrase} to look inside {hideout.phrase}. The safe light showed them {suspect.phrase}, along with the stolen food tucked away inside."
        ),
        (
            f"Why was the {suspect.label} taking the food?",
            f"The {suspect.label} was storing food, not trying to be naughty on purpose. {suspect.motive}"
        ),
        (
            "What lesson did the children learn?",
            f"They learned that a good detective does not rush toward sparks just because a mystery feels exciting. They solved the case better by staying calm, kind, and safe."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ignite", "crevice", "fatten"}
    tool = f["tool_cfg"]
    suspect = f["suspect"]
    if tool.id == "flashlight":
        tags.add("flashlight")
    elif tool.id == "lantern":
        tags.add("lantern")
    elif tool.id == "magnifier":
        tags.add("magnifier")
    if suspect.id == "chipmunk":
        tags.add("chipmunk")
    elif suspect.id == "field_mouse":
        tags.add("mouse")
    elif suspect.id == "squirrel":
        tags.add("squirrel")
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        food="seeds",
        suspect="chipmunk",
        hideout="crevice",
        tool="flashlight",
        detective="Nora",
        detective_gender="girl",
        helper="Ben",
        helper_gender="boy",
        adult="aunt",
    ),
    StoryParams(
        place="courtyard",
        food="pear",
        suspect="field_mouse",
        hideout="step_gap",
        tool="lantern",
        detective="Max",
        detective_gender="boy",
        helper="Lucy",
        helper_gender="girl",
        adult="father",
    ),
    StoryParams(
        place="orchard",
        food="corn",
        suspect="squirrel",
        hideout="floor_crack",
        tool="magnifier",
        detective="Ella",
        detective_gender="girl",
        helper="Theo",
        helper_gender="boy",
        adult="mother",
    ),
]


def explain_combo(food: Food, suspect: Suspect, hideout: Hideout) -> str:
    if not suspect_likes_food(suspect, food):
        return (
            f"(No story: a {suspect.label} would not plausibly steal {food.label} in this little world. "
            f"Pick food that the suspect actually likes.)"
        )
    if not suspect_fits_hideout(suspect, hideout):
        return (
            f"(No story: a {suspect.label} would not plausibly hide in {hideout.phrase}. "
            f"Pick a smaller suspect or a roomier hiding place.)"
        )
    return "(No story: that mystery setup is not supported.)"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it is not a sensible inspection tool for this story "
        f"(sense={tool.sense}). Try one of: {better}.)"
    )


ASP_RULES = r"""
likes_food(S, F) :- likes(S, F).
fits_hideout(S, H) :- fits(S, H).

valid(P, F, S, H) :- place(P), food(F), suspect(S), hideout(H),
                     likes_food(S, F), fits_hideout(S, H).

sensible_tool(T) :- tool(T), sense(T, N), sense_min(M), N >= M,
                    gives_light(T), not risky(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for liked in sorted(suspect.likes):
            lines.append(asp.fact("likes", sid, liked))
        for hid in sorted(suspect.fits):
            lines.append(asp.fact("fits", sid, hid))
    for hid in HIDEOUTS:
        lines.append(asp.fact("hideout", hid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        if tool.gives_light:
            lines.append(asp.fact("gives_light", tid))
        if tool.risky:
            lines.append(asp.fact("risky", tid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


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

    clingo_tools = set(asp_sensible_tools())
    python_tools = {tool.id for tool in sensible_tools()}
    if clingo_tools == python_tools:
        print(f"OK: sensible tools match ({sorted(clingo_tools)}).")
    else:
        rc = 1
        print("MISMATCH in sensible tools:")
        print("  clingo:", sorted(clingo_tools))
        print("  python:", sorted(python_tools))

    smoke_cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"SMOKE ERROR: resolve_params failed at seed {seed}.")
            break

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if sample.world is None:
                raise StoryError("missing world")
        except Exception as err:
            rc = 1
            print(f"SMOKE ERROR in generate case {i}: {err}")
            break

    if rc == 0:
        print(f"OK: generated {len(smoke_cases)} smoke-test stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective storyworld: a child solves the mystery of missing food with safe clues and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery setups from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.suspect and not suspect_likes_food(SUSPECTS[args.suspect], FOODS[args.food]):
        raise StoryError(explain_combo(FOODS[args.food], SUSPECTS[args.suspect], HIDEOUTS[args.hideout or "crevice"]))
    if args.suspect and args.hideout and not suspect_fits_hideout(SUSPECTS[args.suspect], HIDEOUTS[args.hideout]):
        food = FOODS[args.food] if args.food else next(iter(FOODS.values()))
        raise StoryError(explain_combo(food, SUSPECTS[args.suspect], HIDEOUTS[args.hideout]))
    if args.tool and args.tool not in {t.id for t in sensible_tools()}:
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.food is None or combo[1] == args.food)
        and (args.suspect is None or combo[2] == args.suspect)
        and (args.hideout is None or combo[3] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, food, suspect, hideout = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(t.id for t in sensible_tools()))
    detective, detective_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=detective)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        place=place,
        food=food,
        suspect=suspect,
        hideout=hideout,
        tool=tool,
        detective=detective,
        detective_gender=detective_gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        food = FOODS[params.food]
        suspect = SUSPECTS[params.suspect]
        hideout = HIDEOUTS[params.hideout]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err})") from err

    if not suspect_likes_food(suspect, food) or not suspect_fits_hideout(suspect, hideout):
        raise StoryError(explain_combo(food, suspect, hideout))
    if tool.id not in {t.id for t in sensible_tools()}:
        raise StoryError(explain_tool(tool.id))

    world = tell(
        place=place,
        food=food,
        suspect=suspect,
        hideout=hideout,
        tool=tool,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
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
        print(asp_program("#show valid/4.\n#show sensible_tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        tools = asp_sensible_tools()
        print(f"sensible tools: {', '.join(tools)}\n")
        print(f"{len(combos)} compatible (place, food, suspect, hideout) combos:\n")
        for place, food, suspect, hideout in combos:
            print(f"  {place:10} {food:6} {suspect:11} {hideout}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.detective} & {p.helper}: {p.food} mystery at {p.place} ({p.suspect} in {p.hideout})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
