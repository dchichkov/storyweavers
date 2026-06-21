#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hoove_humor_foreshadowing_superhero_story.py
=======================================================================

A standalone storyworld for a tiny superhero rescue domain with humor and
foreshadowing. A child in a homemade superhero costume notices a silly clue,
realizes a small animal is in trouble, and solves the problem with the right
kind of help.

The seed word "hoove" is included exactly as requested. In this world it appears
as a comic, childlike way the characters talk about one little hoof.

Run it
------
    python storyworlds/worlds/gpt-5.4/hoove_humor_foreshadowing_superhero_story.py
    python storyworlds/worlds/gpt-5.4/hoove_humor_foreshadowing_superhero_story.py --animal pony --snag bucket
    python storyworlds/worlds/gpt-5.4/hoove_humor_foreshadowing_superhero_story.py --method yank
    python storyworlds/worlds/gpt-5.4/hoove_humor_foreshadowing_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/hoove_humor_foreshadowing_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hoove_humor_foreshadowing_superhero_story.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    clue_spot: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalCfg:
    id: str
    label: str
    phrase: str
    sound: str
    gait: str
    funny: str
    plural_toes: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Snag:
    id: str
    label: str
    phrase: str
    clue: str
    clue_sound: str
    severity: int
    needs_kind: str
    release_text: str
    risk_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    kind: str
    sense: int
    gentle_power: int
    text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueStyle:
    id: str
    text: str
    foreshadow: str
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


def _r_stuck_distress(world: World) -> list[str]:
    animal = world.get("animal")
    if animal.meters["stuck"] < THRESHOLD:
        return []
    sig = ("distress", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["fear"] += 1
    animal.memes["need_help"] += 1
    hero = world.get("hero")
    hero.memes["concern"] += 1
    return []


def _r_calm_after_help(world: World) -> list[str]:
    animal = world.get("animal")
    if animal.meters["freed"] < THRESHOLD:
        return []
    sig = ("calm", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["fear"] = 0.0
    animal.memes["relief"] += 1
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    hero.memes["pride"] += 1
    sidekick.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stuck_distress", tag="physical", apply=_r_stuck_distress),
    Rule(name="calm_after_help", tag="physical", apply=_r_calm_after_help),
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
            world.say(sent)
    return produced


SETTINGS = {
    "alley": Setting(
        id="alley",
        place="Maple Street Alley",
        clue_spot="between the recycling bins and the brick wall",
        ending_image="The cape fluttered over the puddles while the little animal trotted home.",
        tags={"alley"},
    ),
    "playground": Setting(
        id="playground",
        place="the playground behind the library",
        clue_spot="beside the slide and the sandbox fence",
        ending_image="The cape snapped in the breeze while the little animal skipped toward the gate.",
        tags={"playground"},
    ),
    "market": Setting(
        id="market",
        place="the Saturday market square",
        clue_spot="behind the flower stall",
        ending_image="The cape bobbed through the crowd while the little animal clip-clopped after its owner.",
        tags={"market"},
    ),
}

ANIMALS = {
    "pony": AnimalCfg(
        id="pony",
        label="pony",
        phrase="a little brown pony",
        sound="neigh",
        gait="clip-clopped",
        funny="Its forelock kept falling into its eyes like a messy wig.",
        tags={"pony", "animal"},
    ),
    "goat": AnimalCfg(
        id="goat",
        label="goat",
        phrase="a bouncy white goat",
        sound="maa",
        gait="hopped",
        funny="It looked offended in a way only a goat can.",
        tags={"goat", "animal"},
    ),
    "calf": AnimalCfg(
        id="calf",
        label="calf",
        phrase="a wobbly black-and-white calf",
        sound="moo",
        gait="clopped",
        funny="Its ears stuck out so proudly that they looked like tiny capes.",
        tags={"calf", "animal"},
    ),
}

SNAGS = {
    "bucket": Snag(
        id="bucket",
        label="bucket",
        phrase="a dented silver bucket",
        clue="a lonely metal clonk that did not sound like a toy at all",
        clue_sound="clonk-clonk",
        severity=1,
        needs_kind="lift",
        release_text="eased the bucket up and away from the little hoove",
        risk_text="yanking too hard could scrape the animal and make it panic",
        tags={"bucket", "stuck"},
    ),
    "kite": Snag(
        id="kite",
        label="kite string",
        phrase="a tangled kite string",
        clue="a bright scrap of paper fluttering where no breeze should have reached",
        clue_sound="frrrip-frrrip",
        severity=1,
        needs_kind="untangle",
        release_text="picked the string loose, loop by loop, until the little hoove slipped free",
        risk_text="a hard tug could tighten the string and make the knot worse",
        tags={"kite", "string", "stuck"},
    ),
    "crate": Snag(
        id="crate",
        label="crate slats",
        phrase="the slats of a wooden crate",
        clue="a shaky thump and a pair of worried eyes peeking through the boards",
        clue_sound="thump-thump",
        severity=2,
        needs_kind="open",
        release_text="tilted the crate and opened enough space for the little hoove to slide out",
        risk_text="pulling at the leg instead of the crate could hurt the animal badly",
        tags={"crate", "stuck"},
    ),
}

METHODS = {
    "lift_bucket": Method(
        id="lift_bucket",
        label="lift carefully",
        kind="lift",
        sense=3,
        gentle_power=2,
        text="knelt low, held the bucket steady with both hands, and lifted it straight up",
        fail_text="tried to lift, but the snag was not the kind that a plain lift could solve",
        qa_text="lifted the bucket straight up with both hands",
        tags={"gentle", "careful"},
    ),
    "untangle_ribbon": Method(
        id="untangle_ribbon",
        label="untangle gently",
        kind="untangle",
        sense=3,
        gentle_power=2,
        text="used slow fingers and patient little twists to loosen the tangle",
        fail_text="picked at the wrong thing, and the knot stayed tight",
        qa_text="loosened the tangle slowly with careful fingers",
        tags={"gentle", "careful"},
    ),
    "open_crate": Method(
        id="open_crate",
        label="open space",
        kind="open",
        sense=3,
        gentle_power=2,
        text="braced the crate, tipped it sideways, and made a safe gap",
        fail_text="pushed and puffed, but the snag needed a different kind of help",
        qa_text="tipped the crate and made a safe gap",
        tags={"gentle", "careful"},
    ),
    "yank": Method(
        id="yank",
        label="super yank",
        kind="pull",
        sense=1,
        gentle_power=1,
        text="gave one giant superhero yank",
        fail_text="yanked at once, which was exactly the wrong idea",
        qa_text="yanked hard",
        tags={"rough"},
    ),
}

CLUES = {
    "clonk": ClueStyle(
        id="clonk",
        text="A strange clonk-clonk followed the children like a shy drumbeat.",
        foreshadow="That silly sound would turn out to matter in a minute.",
        tags={"sound", "foreshadow"},
    ),
    "flutter": ClueStyle(
        id="flutter",
        text="A bright flutter winked behind a corner and vanished again.",
        foreshadow="It looked funny then, but it was the first clue.",
        tags={"visual", "foreshadow"},
    ),
    "thump": ClueStyle(
        id="thump",
        text="From far off came a nervous thump-thump, as if a box were trying to whisper.",
        foreshadow="The sound made the hero slow down and listen twice.",
        tags={"sound", "foreshadow"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Zoe", "Ava", "Nina", "Pia", "Lucy", "Maya"]
BOY_NAMES = ["Theo", "Max", "Ben", "Leo", "Eli", "Noah", "Finn", "Jack"]
TITLES = ["Captain Comet", "Thunder Bean", "The Daring Flash", "Moon Mask", "Rocket Robin"]
SIDEKICKS = ["Buttons", "Boom", "Spark", "Noodle", "Zap"]
PARENT_TYPES = ["mother", "father"]


def snag_compatible(animal: AnimalCfg, snag: Snag) -> bool:
    return True


def sensible_methods_for(snag: Snag) -> list[str]:
    return [
        mid for mid, method in METHODS.items()
        if method.sense >= SENSE_MIN and method.kind == snag.needs_kind
    ]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for animal_id, animal in ANIMALS.items():
            for snag_id, snag in SNAGS.items():
                if not snag_compatible(animal, snag):
                    continue
                for clue_id in CLUES:
                    combos.append((setting_id, animal_id, snag_id, clue_id))
    return combos


def explain_method_rejection(method_id: str, snag_id: str) -> str:
    method = METHODS[method_id]
    snag = SNAGS[snag_id]
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method_id}': it is too rough for a story about helping. "
            f"Yanking is a poor idea because {snag.risk_text}. Pick a gentle method instead.)"
        )
    if method.kind != snag.needs_kind:
        return (
            f"(No story: {method.label} does not match the problem. This snag needs a method "
            f"that can {snag.needs_kind}, not one that tries to {method.kind}.)"
        )
    return "(No story: this method does not fit the rescue.)"


def outcome_of(params: "StoryParams") -> str:
    snag = SNAGS[params.snag]
    method = METHODS[params.method]
    if method.sense < SENSE_MIN or method.kind != snag.needs_kind:
        return "oops"
    return "rescued"


def predict_attempt(snag: Snag, method: Method) -> dict:
    success = method.sense >= SENSE_MIN and method.kind == snag.needs_kind and method.gentle_power >= snag.severity
    return {
        "success": success,
        "panic": not success,
    }


def introduce(world: World, hero: Entity, sidekick: Entity) -> None:
    title = hero.attrs["title"]
    world.say(
        f"After school, {hero.id} tied on a towel cape and became {title}, defender of small troubles."
    )
    world.say(
        f"Beside {hero.pronoun('object')} marched {sidekick.id}, the official sidekick, who had drawn a lightning bolt on a paper hat and kept saluting at pigeons."
    )


def patrol(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"The two of them patrolled {world.setting.place}, trying to look fierce and tripping only a little."
    )
    if hero.attrs.get("cape_color"):
        world.say(
            f"{hero.id}'s {hero.attrs['cape_color']} cape kept swishing into {hero.pronoun('possessive')} knees, which was not very fierce but was a little impressive."
        )


def plant_clue(world: World, clue: ClueStyle, snag: Snag) -> None:
    world.say(clue.text)
    world.say(clue.foreshadow)
    world.say(
        f"Soon they noticed {snag.clue} {world.setting.clue_spot}."
    )


def investigate(world: World, hero: Entity, sidekick: Entity, animal: Entity, animal_cfg: AnimalCfg, snag: Snag) -> None:
    animal.meters["stuck"] += 1
    animal.attrs["snag"] = snag.id
    propagate(world, narrate=False)
    world.say(
        f'"Emergency ears on," whispered {sidekick.id}. They tiptoed closer and found {animal_cfg.phrase}.'
    )
    world.say(
        f"One little hoove was trapped in {snag.phrase}, and {animal.pronoun()} kept making a worried {animal_cfg.sound}."
    )
    world.say(animal_cfg.funny)
    world.facts["foreshadowed"] = True


def worry(world: World, hero: Entity, sidekick: Entity, snag: Snag) -> None:
    hero.memes["bravery"] += 1
    sidekick.memes["concern"] += 1
    pred = predict_attempt(snag, METHODS[world.facts["method"].id])
    world.facts["predicted_success"] = pred["success"]
    world.say(
        f'{hero.id} crouched low. "This is a real rescue," {hero.pronoun()} said. "{snag.risk_text.capitalize()}."'
    )
    world.say(
        f'{sidekick.id} nodded so hard the paper hat slipped over one eye. "So we do not use the Big Dramatic Tug," {sidekick.pronoun()} said.'
    )


def rescue(world: World, hero: Entity, animal: Entity, snag: Snag, method: Method) -> None:
    animal.meters["freed"] += 1
    animal.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Very slowly, {hero.id} {method.text}. Then {hero.pronoun()} {snag.release_text}."
    )
    world.say(
        f"{animal.label.capitalize()} blinked, shook itself, and took one surprised step, then another."
    )


def comfort_and_return(world: World, hero: Entity, sidekick: Entity, animal: Entity, animal_cfg: AnimalCfg, parent: Entity) -> None:
    hero.memes["kindness"] += 1
    sidekick.memes["joy"] += 1
    animal.memes["trust"] += 1
    world.say(
        f'{sidekick.id} let out the breath {sidekick.pronoun()} had been holding. "{hero.attrs["title"]} saves the day again," {sidekick.pronoun()} announced to absolutely everyone.'
    )
    world.say(
        f"The little {animal_cfg.label} gave {hero.id}'s hand a damp nudge, as if saying thank you in animal language."
    )
    world.say(
        f"A moment later, {parent.label_word.capitalize()} from a nearby stall came hurrying over, laughing with relief. "
        f'"There you are!" {parent.pronoun()} said, reaching for the little {animal_cfg.label}.'
    )
    world.say(world.setting.ending_image)


def oops_attempt(world: World, hero: Entity, sidekick: Entity, animal: Entity, snag: Snag, method: Method) -> None:
    animal.memes["fear"] += 1
    hero.memes["embarrassment"] += 1
    world.say(
        f"{hero.id} started with a burst of courage and {method.text}."
    )
    world.say(
        f"It did not work. {animal.pronoun().capitalize()} jerked back, and {sidekick.id} gasped because {snag.risk_text}."
    )
    world.say(
        f'{hero.id} froze. "That was not my best superhero idea," {hero.pronoun()} admitted.'
    )


def call_grownup(world: World, hero: Entity, sidekick: Entity, animal: Entity, snag: Snag, parent: Entity) -> None:
    animal.meters["freed"] += 1
    animal.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} did the bravest thing: {hero.pronoun()} called for a grown-up instead of pretending to know everything."
    )
    world.say(
        f"{parent.label_word.capitalize()} hurried over, steadied the problem, and {snag.release_text}."
    )
    world.say(
        f'This time the little animal stepped free at once. {sidekick.id} whispered, "Even superheroes can ask for backup."'
    )
    world.say(world.setting.ending_image)


def tell(
    setting: Setting,
    animal_cfg: AnimalCfg,
    snag: Snag,
    clue: ClueStyle,
    method: Method,
    hero_name: str,
    hero_type: str,
    sidekick_name: str,
    parent_type: str,
    title: str,
    cape_color: str,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            role="hero",
            label=hero_name,
            attrs={"title": title, "cape_color": cape_color},
            traits=["helpful", "dramatic"],
            tags={"hero"},
        )
    )
    sidekick = world.add(
        Entity(
            id=sidekick_name,
            kind="character",
            type="child",
            role="sidekick",
            label=sidekick_name,
            traits=["funny", "loyal"],
            tags={"sidekick"},
        )
    )
    parent = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=parent_type,
            role="adult",
            label="the grown-up",
            tags={"adult"},
        )
    )
    animal = world.add(
        Entity(
            id="animal",
            kind="thing",
            type=animal_cfg.id,
            label=animal_cfg.label,
            phrase=animal_cfg.phrase,
            role="animal",
            tags=set(animal_cfg.tags),
        )
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        animal=animal,
        animal_cfg=animal_cfg,
        snag=snag,
        clue=clue,
        method=method,
        setting=setting,
    )

    introduce(world, hero, sidekick)
    patrol(world, hero, sidekick)

    world.para()
    plant_clue(world, clue, snag)
    investigate(world, hero, sidekick, animal, animal_cfg, snag)

    world.para()
    worry(world, hero, sidekick, snag)

    if outcome_of(
        StoryParams(
            setting=setting.id,
            animal=animal_cfg.id,
            snag=snag.id,
            clue=clue.id,
            method=method.id,
            hero_name=hero_name,
            hero_gender=hero_type,
            sidekick_name=sidekick_name,
            parent=parent_type,
            title=title,
            cape_color=cape_color,
            seed=None,
        )
    ) == "rescued":
        rescue(world, hero, animal, snag, method)
        world.para()
        comfort_and_return(world, hero, sidekick, animal, animal_cfg, parent)
        outcome = "rescued"
    else:
        oops_attempt(world, hero, sidekick, animal, snag, method)
        world.para()
        call_grownup(world, hero, sidekick, animal, snag, parent)
        outcome = "backup"

    world.facts.update(
        outcome=outcome,
        foreshadow_used=world.facts.get("foreshadowed", False),
        asked_backup=(outcome == "backup"),
        freed=animal.meters["freed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "pony": [(
        "What is a pony?",
        "A pony is a small kind of horse. It has hooves and can trot and neigh."
    )],
    "goat": [(
        "What is a goat?",
        "A goat is a farm animal with hooves and a quick, springy way of moving. Some goats are very curious."
    )],
    "calf": [(
        "What is a calf?",
        "A calf is a baby cow. Calves can be wobbly and gentle when they are young."
    )],
    "stuck": [(
        "What should you do if an animal is stuck?",
        "Stay calm and do not scare the animal more. Get gentle help from a grown-up if you are not sure how to free it safely."
    )],
    "gentle": [(
        "Why should you be gentle with a trapped animal?",
        "A trapped animal may already feel scared. Gentle hands and calm movements help keep it from getting hurt worse."
    )],
    "foreshadow": [(
        "What is foreshadowing in a story?",
        "Foreshadowing is when a story gives you a small clue before something important happens later. It helps the turn feel surprising and right at the same time."
    )],
    "superhero": [(
        "What makes someone a real superhero?",
        "A real superhero helps others, stays brave, and chooses the safest kind action. Big muscles are less important than good choices."
    )],
    "backup": [(
        "Why is asking for backup brave?",
        "Asking for backup means you care more about solving the problem safely than about showing off. That is a strong and honest choice."
    )],
}

KNOWLEDGE_ORDER = ["superhero", "foreshadow", "stuck", "gentle", "backup", "pony", "goat", "calf"]


@dataclass
class StoryParams:
    setting: str
    animal: str
    snag: str
    clue: str
    method: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    parent: str
    title: str
    cape_color: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="playground",
        animal="pony",
        snag="bucket",
        clue="clonk",
        method="lift_bucket",
        hero_name="Mira",
        hero_gender="girl",
        sidekick_name="Buttons",
        parent="mother",
        title="Captain Comet",
        cape_color="red",
        seed=None,
    ),
    StoryParams(
        setting="market",
        animal="goat",
        snag="kite",
        clue="flutter",
        method="untangle_ribbon",
        hero_name="Theo",
        hero_gender="boy",
        sidekick_name="Spark",
        parent="father",
        title="Thunder Bean",
        cape_color="blue",
        seed=None,
    ),
    StoryParams(
        setting="alley",
        animal="calf",
        snag="crate",
        clue="thump",
        method="open_crate",
        hero_name="Lena",
        hero_gender="girl",
        sidekick_name="Zap",
        parent="mother",
        title="Moon Mask",
        cape_color="gold",
        seed=None,
    ),
    StoryParams(
        setting="playground",
        animal="pony",
        snag="kite",
        clue="flutter",
        method="yank",
        hero_name="Max",
        hero_gender="boy",
        sidekick_name="Noodle",
        parent="father",
        title="The Daring Flash",
        cape_color="green",
        seed=None,
    ),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    animal = world.facts["animal_cfg"]
    snag = world.facts["snag"]
    outcome = world.facts["outcome"]
    prompts = [
        f'Write a funny superhero story for a 3-to-5-year-old that includes the word "hoove" and begins with a small clue that matters later.',
        f"Tell a child-facing rescue story where {hero.id} and {sidekick.id} act like superheroes and discover that a {animal.label} has one hoove stuck in {snag.phrase}.",
    ]
    if outcome == "backup":
        prompts.append(
            "Write a superhero story where the hero first tries the wrong idea, then bravely asks for grown-up backup and learns that safe help matters more than showing off."
        )
    else:
        prompts.append(
            "Write a superhero story with humor and foreshadowing where the hero notices a silly clue, understands the problem, and solves it gently."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    animal = world.facts["animal_cfg"]
    snag = world.facts["snag"]
    method = world.facts["method"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child pretending to be a superhero, and {sidekick.id}, the eager sidekick. Together they find a {animal.label} that needs help."
        ),
        (
            "What clue came before the rescue?",
            f"They first noticed {snag.clue}. That funny clue was foreshadowing because it pointed them toward the real problem before they saw it."
        ),
        (
            f"Why was the {animal.label} upset?",
            f"The {animal.label} was upset because one little hoove was trapped in {snag.phrase}. Being stuck made the animal scared and unable to walk away."
        ),
    ]
    if outcome == "rescued":
        qa.append(
            (
                f"How did {hero.id} help the {animal.label}?",
                f"{hero.id} helped by moving carefully and choosing the right kind of rescue. {hero.pronoun('subject').capitalize()} {method.qa_text}, which let the little hoove come free without a rough pull."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with relief and a funny superhero feeling. The animal was free, the grown-up arrived smiling, and the hero's cape fluttered while everyone calmed down."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} call for a grown-up?",
                f"{hero.id} realized the first rough idea was not safe. Calling for backup was the bravest choice because it protected the trapped animal from being hurt more."
            )
        )
        qa.append(
            (
                "What did the hero learn?",
                "The hero learned that being a superhero is not about doing everything alone. It is about helping kindly and asking for backup when that is the safest move."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"superhero", "foreshadow", "stuck", "gentle"}
    animal_id = world.facts["animal_cfg"].id
    tags.add(animal_id)
    if world.facts["asked_backup"]:
        tags.add("backup")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, Sn, C) :- setting(S), animal(A), snag(Sn), clue(C).

good_method(M, Sn) :- method(M), sense(M, X), sense_min(Min), X >= Min,
                      method_kind(M, K), needs_kind(Sn, K).

outcome(rescued) :- chosen_snag(Sn), chosen_method(M), good_method(M, Sn).
outcome(oops) :- chosen_snag(Sn), chosen_method(M), not good_method(M, Sn).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for snag_id, snag in SNAGS.items():
        lines.append(asp.fact("snag", snag_id))
        lines.append(asp.fact("needs_kind", snag_id, snag.needs_kind))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_kind", mid, method.kind))
        lines.append(asp.fact("sense", mid, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_snag", params.snag),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a funny superhero rescue with foreshadowing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and args.snag:
        method = METHODS[args.method]
        snag = SNAGS[args.snag]
        if method.sense < SENSE_MIN or method.kind != snag.needs_kind:
            raise StoryError(explain_method_rejection(args.method, args.snag))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.animal is None or c[1] == args.animal)
        and (args.snag is None or c[2] == args.snag)
        and (args.clue is None or c[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, animal_id, snag_id, clue_id = rng.choice(sorted(combos))
    if args.method:
        method_id = args.method
    else:
        if rng.random() < 0.2:
            method_id = "yank"
        else:
            method_id = rng.choice(sorted(sensible_methods_for(SNAGS[snag_id])))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick_name = rng.choice([n for n in SIDEKICKS if n != hero_name])
    parent = args.parent or rng.choice(PARENT_TYPES)
    title = rng.choice(TITLES)
    cape_color = rng.choice(["red", "blue", "gold", "green", "purple"])
    return StoryParams(
        setting=setting_id,
        animal=animal_id,
        snag=snag_id,
        clue=clue_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=gender,
        sidekick_name=sidekick_name,
        parent=parent,
        title=title,
        cape_color=cape_color,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        animal = ANIMALS[params.animal]
        snag = SNAGS[params.snag]
        clue = CLUES[params.clue]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid option: {err.args[0]})") from None

    if method.sense < SENSE_MIN and params.method != "yank":
        raise StoryError(explain_method_rejection(params.method, params.snag))
    if method.kind != snag.needs_kind and params.method != "yank":
        raise StoryError(explain_method_rejection(params.method, params.snag))

    world = tell(
        setting=setting,
        animal_cfg=animal,
        snag=snag,
        clue=clue,
        method=method,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        sidekick_name=params.sidekick_name,
        parent_type=params.parent,
        title=params.title,
        cape_color=params.cape_color,
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
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in combo gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, animal, snag, clue) combos:\n")
        for setting_id, animal_id, snag_id, clue_id in combos:
            print(f"  {setting_id:10} {animal_id:6} {snag_id:7} {clue_id}")
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
                f"### {p.hero_name}: {p.animal} in {p.snag} at {p.setting} "
                f"({p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
