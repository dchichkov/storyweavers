#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/slip_fizz_dialogue_sharing_magic_animal_story.py
============================================================================

A standalone story world for a small animal tale about a fizzy treat, a slippery
path, a magic helper, and the change from grabbing to sharing.

Premise
-------
Two little animals find a bubbling spring that can make a sweet forest fizz.
One childlike animal wants the biggest share. On the way to a picnic spot, the
path is slippery. If the eager animal clutches everything and rushes, they
slip, the fizz spills, and a magical helper only restores the treat after the
animals share. In gentler variants, the warning is heard in time and the animals
share before anything spills.

The world model tracks:
- physical meters: full, spill, slippery, safe, shared, magic
- emotional memes: joy, want, worry, greed, relief, gratitude, trust

The prose is rendered from simulated state, not from frozen templates.

Run it
------
python storyworlds/worlds/gpt-5.4/slip_fizz_dialogue_sharing_magic_animal_story.py
python storyworlds/worlds/gpt-5.4/slip_fizz_dialogue_sharing_magic_animal_story.py --carrier fox --friend rabbit
python storyworlds/worlds/gpt-5.4/slip_fizz_dialogue_sharing_magic_animal_story.py --surface dry_dirt
python storyworlds/worlds/gpt-5.4/slip_fizz_dialogue_sharing_magic_animal_story.py --all
python storyworlds/worlds/gpt-5.4/slip_fizz_dialogue_sharing_magic_animal_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/slip_fizz_dialogue_sharing_magic_animal_story.py --verify
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
    slippery: bool = False
    magic: bool = False
    hold_liquid: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"


@dataclass
class AnimalKind:
    id: str
    label: str
    phrase: str
    move: str
    call: str
    trait: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DrinkKind:
    id: str
    label: str
    phrase: str
    color: str
    smell: str
    fizz_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ContainerKind:
    id: str
    label: str
    phrase: str
    plural: bool = False
    hold_liquid: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SurfaceKind:
    id: str
    label: str
    phrase: str
    slippery: bool = False
    slip_text: str = ""
    safe_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicKind:
    id: str
    label: str
    phrase: str
    appear_text: str
    gift_text: str
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    path = world.get("path")
    carrier = world.get("carrier")
    treat = world.get("treat")
    if not path.slippery:
        return out
    if carrier.memes["rush"] < THRESHOLD:
        return out
    if treat.meters["full"] < THRESHOLD:
        return out
    sig = ("spill", path.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carrier.meters["stumbled"] += 1
    treat.meters["full"] = 0.0
    treat.meters["spill"] += 1
    carrier.memes["worry"] += 1
    carrier.memes["sad"] += 1
    world.get("friend").memes["worry"] += 1
    out.append("__spill__")
    return out


def _r_share_calms(world: World) -> list[str]:
    out: list[str] = []
    carrier = world.get("carrier")
    friend = world.get("friend")
    treat = world.get("treat")
    if treat.meters["shared"] < THRESHOLD:
        return out
    sig = ("share_calms",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carrier.memes["greed"] = 0.0
    carrier.memes["relief"] += 1
    friend.memes["relief"] += 1
    carrier.memes["gratitude"] += 1
    friend.memes["gratitude"] += 1
    out.append("__shared__")
    return out


CAUSAL_RULES = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="share_calms", tag="social", apply=_r_share_calms),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                produced.extend(items)
                changed = True
    if narrate:
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


ANIMALS = {
    "rabbit": AnimalKind(
        id="rabbit",
        label="rabbit",
        phrase="a little rabbit",
        move="hopped",
        call="soft ears",
        trait="gentle",
        tags={"rabbit", "animal"},
    ),
    "fox": AnimalKind(
        id="fox",
        label="fox",
        phrase="a small fox",
        move="trotted",
        call="bright tail",
        trait="quick",
        tags={"fox", "animal"},
    ),
    "otter": AnimalKind(
        id="otter",
        label="otter",
        phrase="a playful otter",
        move="padded",
        call="shiny whiskers",
        trait="playful",
        tags={"otter", "animal"},
    ),
    "squirrel": AnimalKind(
        id="squirrel",
        label="squirrel",
        phrase="a busy squirrel",
        move="scampered",
        call="striped tail",
        trait="busy",
        tags={"squirrel", "animal"},
    ),
}

DRINKS = {
    "berry_fizz": DrinkKind(
        id="berry_fizz",
        label="berry fizz",
        phrase="a cup of berry fizz",
        color="pink",
        smell="sweet like crushed berries",
        fizz_word="fizz",
        tags={"berries", "fizz"},
    ),
    "apple_fizz": DrinkKind(
        id="apple_fizz",
        label="apple fizz",
        phrase="a cup of apple fizz",
        color="golden",
        smell="fresh like cut apples",
        fizz_word="fizz",
        tags={"apple", "fizz"},
    ),
    "flower_fizz": DrinkKind(
        id="flower_fizz",
        label="flower fizz",
        phrase="a cup of flower fizz",
        color="pale purple",
        smell="light and honey-sweet",
        fizz_word="fizz",
        tags={"flower", "fizz"},
    ),
}

CONTAINERS = {
    "leaf_cup": ContainerKind(
        id="leaf_cup",
        label="leaf cup",
        phrase="a folded leaf cup",
        plural=False,
        hold_liquid=True,
        tags={"leaf_cup"},
    ),
    "acorn_bowls": ContainerKind(
        id="acorn_bowls",
        label="acorn bowls",
        phrase="two little acorn bowls",
        plural=True,
        hold_liquid=True,
        tags={"acorn_bowls"},
    ),
    "shell_cup": ContainerKind(
        id="shell_cup",
        label="shell cup",
        phrase="a shiny shell cup",
        plural=False,
        hold_liquid=True,
        tags={"shell_cup"},
    ),
    "basket": ContainerKind(
        id="basket",
        label="basket",
        phrase="a woven basket",
        plural=False,
        hold_liquid=False,
        tags={"basket"},
    ),
}

SURFACES = {
    "mossy_log": SurfaceKind(
        id="mossy_log",
        label="mossy log",
        phrase="a mossy log over a little brook",
        slippery=True,
        slip_text="The green moss was slick as soap.",
        safe_text="The log was narrow, so careful paws mattered.",
        tags={"slip", "moss"},
    ),
    "wet_stones": SurfaceKind(
        id="wet_stones",
        label="wet stones",
        phrase="a path of wet stepping-stones",
        slippery=True,
        slip_text="Tiny beads of water made the stones shiny and slippery.",
        safe_text="The stones asked for slow feet and steady paws.",
        tags={"slip", "stones"},
    ),
    "muddy_bank": SurfaceKind(
        id="muddy_bank",
        label="muddy bank",
        phrase="a muddy bank beside the spring",
        slippery=True,
        slip_text="The mud was soft and slick under quick feet.",
        safe_text="The bank looked easy, but one fast step could slide.",
        tags={"slip", "mud"},
    ),
    "dry_dirt": SurfaceKind(
        id="dry_dirt",
        label="dry dirt path",
        phrase="a dry dirt path",
        slippery=False,
        slip_text="The path was firm and plain.",
        safe_text="Nothing on the ground would make a careful animal slide.",
        tags={"path"},
    ),
}

MAGIC = {
    "firefly": MagicKind(
        id="firefly",
        label="firefly",
        phrase="a gold firefly with a lantern glow",
        appear_text="A gold firefly rose from the reeds and drew a little shining circle in the air.",
        gift_text="With a bright blink and a happy hum, the firefly touched the spring, and bubbles danced up again.",
        lesson_text='The firefly said, "Magic shines brightest when friends make room for each other."',
        tags={"magic", "firefly"},
    ),
    "frog": MagicKind(
        id="frog",
        label="moon frog",
        phrase="a moon frog with silver spots",
        appear_text="A moon frog peeped from under a fern and blinked as if it knew a secret song.",
        gift_text="The frog tapped the water with one silver toe, and the spring began to sparkle and fizz again.",
        lesson_text='The frog said, "A shared sip tastes sweeter than a lonely gulp."',
        tags={"magic", "frog"},
    ),
    "wren": MagicKind(
        id="wren",
        label="star wren",
        phrase="a star wren with twinkly feathers",
        appear_text="A star wren fluttered down and shook tiny lights from its wings like falling stars.",
        gift_text="The wren sang one clear note, and the bubbles in the spring popped up in a fresh, bright ribbon.",
        lesson_text='The wren said, "Kind hearts call kind magic."',
        tags={"magic", "bird"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal in ANIMALS:
        for container_id, container in CONTAINERS.items():
            if not container.hold_liquid:
                continue
            for surface_id, surface in SURFACES.items():
                if surface.slippery:
                    combos.append((animal, container_id, surface_id))
    return combos


@dataclass
class StoryParams:
    carrier: str
    friend: str
    drink: str
    container: str
    surface: str
    magic_helper: str
    carrier_name: str
    friend_name: str
    parent_seed_note: str = ""
    greedy: bool = True
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        carrier="fox",
        friend="rabbit",
        drink="berry_fizz",
        container="leaf_cup",
        surface="mossy_log",
        magic_helper="firefly",
        carrier_name="Pip",
        friend_name="Moss",
        greedy=True,
    ),
    StoryParams(
        carrier="squirrel",
        friend="otter",
        drink="apple_fizz",
        container="acorn_bowls",
        surface="wet_stones",
        magic_helper="frog",
        carrier_name="Nip",
        friend_name="Ripple",
        greedy=False,
    ),
    StoryParams(
        carrier="rabbit",
        friend="fox",
        drink="flower_fizz",
        container="shell_cup",
        surface="muddy_bank",
        magic_helper="wren",
        carrier_name="Clover",
        friend_name="Fern",
        greedy=True,
    ),
]


def explain_rejection(container: ContainerKind, surface: SurfaceKind) -> str:
    if not container.hold_liquid:
        return (
            f"(No story: {container.phrase} cannot hold a fizzy drink, so the animals "
            f"would have nothing sloshy to carry or share. Pick a cup or bowls.)"
        )
    if not surface.slippery:
        return (
            f"(No story: {surface.phrase} is not slippery enough for a slip story. "
            f"Pick mossy_log, wet_stones, or muddy_bank.)"
        )
    return "(No story: this combination does not support the slip-and-sharing tale.)"


def distinct_animals(aid: str, bid: str) -> bool:
    return aid != bid


def predict_slip(world: World) -> bool:
    sim = world.copy()
    sim.get("carrier").memes["rush"] += 1
    propagate(sim, narrate=False)
    return sim.get("treat").meters["spill"] >= THRESHOLD


def introduce(world: World, carrier_cfg: AnimalKind, friend_cfg: AnimalKind) -> None:
    carrier = world.get("carrier")
    friend = world.get("friend")
    drink = world.facts["drink_cfg"]
    world.say(
        f"In a ferny glade, {carrier.id} the {carrier_cfg.label} and {friend.id} the "
        f"{friend_cfg.label} found a bubbling spring. It smelled {drink.smell}, and every "
        f"bubble made a tiny {drink.fizz_word} in the air."
    )
    world.say(
        f'"Listen," whispered {friend.id}. "The spring is singing." '
        f'"And maybe it is making {drink.label}," said {carrier.id}.'
    )


def fill_treat(world: World) -> None:
    carrier = world.get("carrier")
    friend = world.get("friend")
    treat = world.get("treat")
    container = world.facts["container_cfg"]
    treat.meters["full"] += 1
    carrier.memes["joy"] += 1
    friend.memes["joy"] += 1
    if container.plural:
        world.say(
            f"They dipped {container.phrase} into the spring, and soon the little bowls were "
            f"full of sparkling {world.facts['drink_cfg'].color} bubbles."
        )
    else:
        world.say(
            f"They filled {container.phrase} with sparkling {world.facts['drink_cfg'].color} "
            f"{world.facts['drink_cfg'].label} until it almost tickled over the rim."
        )


def wanting(world: World) -> None:
    carrier = world.get("carrier")
    friend = world.get("friend")
    container = world.facts["container_cfg"]
    carrier.memes["want"] += 1
    friend.memes["trust"] += 1
    if container.plural:
        world.say(
            f'"Let us take these to the picnic stone," said {friend.id}. '
            f'{carrier.id} looked at the bowls and felt glad there was enough for two.'
        )
    else:
        carrier.memes["greed"] += 1
        world.say(
            f'{carrier.id} curled both paws around the single cup. '
            f'"I found the spring first," {carrier.pronoun()} said. "Maybe I should carry all of it."'
        )
        world.say(
            f'{friend.id} blinked. "We can share," {friend.pronoun()} said softly. '
            f'"Things that sparkle are nicer when two friends laugh over them."'
        )


def warning(world: World) -> None:
    carrier = world.get("carrier")
    friend = world.get("friend")
    path_cfg = world.facts["surface_cfg"]
    risk = predict_slip(world)
    world.facts["predicted_slip"] = risk
    world.say(path_cfg.slip_text if risk else path_cfg.safe_text)
    if risk:
        friend.memes["worry"] += 1
        world.say(
            f'"Slow down," said {friend.id}. "If you hurry over {path_cfg.phrase}, you might slip."'
        )


def choose(world: World, greedy: bool) -> None:
    carrier = world.get("carrier")
    friend = world.get("friend")
    container = world.facts["container_cfg"]
    if container.plural:
        world.get("treat").meters["shared"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{carrier.id} nodded. "One for you and one for me," {carrier.pronoun()} said. '
            f'They carried the little bowls side by side.'
        )
        world.facts["outcome"] = "shared_early"
        return
    if greedy:
        carrier.memes["rush"] += 1
        carrier.memes["greed"] += 1
        world.say(
            f'"Just for a minute, I want it all to myself," said {carrier.id}. '
            f'With the brimming cup held tight, {carrier.pronoun()} hurried ahead.'
        )
        propagate(world, narrate=False)
        if world.get("treat").meters["spill"] >= THRESHOLD:
            world.facts["outcome"] = "spilled_then_shared"
        else:
            world.facts["outcome"] = "kept_balance"
    else:
        carrier.meters["careful"] += 1
        world.get("treat").meters["shared"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{carrier.id} stopped and looked at the wobbling bubbles. '
            f'"You are right," {carrier.pronoun()} said. "I do not want a lonely cup. Let us share."'
        )
        world.facts["outcome"] = "shared_early"


def slip_scene(world: World) -> None:
    if world.get("treat").meters["spill"] < THRESHOLD:
        return
    carrier = world.get("carrier")
    friend = world.get("friend")
    path = world.facts["surface_cfg"]
    world.say(
        f'Halfway across {path.phrase}, {carrier.id} felt one paw slide. '
        f'"Oh!" cried {carrier.id}. {carrier.pronoun().capitalize()} gave a slip, and the fizzy drink flew in a bright arc.'
    )
    world.say(
        f'The bubbles landed with a soft splash and one last tiny fizz. '
        f'{friend.id} ran close at once and steadied {carrier.id}.'
    )


def comfort(world: World) -> None:
    if world.get("treat").meters["spill"] < THRESHOLD:
        return
    carrier = world.get("carrier")
    friend = world.get("friend")
    carrier.memes["sad"] += 1
    friend.memes["care"] = 1.0
    world.say(
        f'"I should have listened," said {carrier.id}, with wet whiskers and a droopy face. '
        f'"Now there is none left to share."'
    )
    world.say(
        f'"There is still me to share the sad part with," said {friend.id}. '
        f'{friend.pronoun().capitalize()} sat beside {carrier.id} until the rushing feeling grew small.'
    )


def magic_help(world: World) -> None:
    helper_cfg = world.facts["magic_cfg"]
    helper = world.get("helper")
    carrier = world.get("carrier")
    friend = world.get("friend")
    treat = world.get("treat")
    spilled = treat.meters["spill"] >= THRESHOLD
    helper.meters["magic"] += 1
    world.say(helper_cfg.appear_text)
    if spilled:
        world.say(helper_cfg.lesson_text)
        world.say(
            f'{carrier.id} looked at {friend.id}. "If the spring sings again," {carrier.pronoun()} said, '
            f'"the first sip will be yours."'
        )
        friend.memes["trust"] += 1
        treat.meters["shared"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{friend.id} smiled. "Then we will both sip slowly," {friend.pronoun()} said.'
        )
        world.say(helper_cfg.gift_text)
        treat.meters["full"] = 1.0
        treat.meters["magic"] += 1
        world.facts["magic_restored"] = True
    else:
        world.say(helper_cfg.lesson_text)
        world.say(
            f'The helper circled once over the cups, pleased that the animals were already making room for each other.'
        )
        treat.meters["magic"] += 1
        world.facts["magic_restored"] = False


def ending(world: World) -> None:
    carrier = world.get("carrier")
    friend = world.get("friend")
    treat = world.get("treat")
    container = world.facts["container_cfg"]
    drink = world.facts["drink_cfg"]
    if treat.meters["shared"] >= THRESHOLD and container.plural:
        world.say(
            f'At the picnic stone, {carrier.id} and {friend.id} clinked the little bowls together. '
            f'The {drink.label} fizz tickled their noses, and the glade sounded full of giggles.'
        )
        world.say(
            f'From then on, whenever something wonderful bubbled up, they remembered to pass it paw to paw.'
        )
        return
    if treat.meters["magic"] >= THRESHOLD and treat.meters["spill"] >= THRESHOLD:
        world.say(
            f'Back at the spring, {carrier.id} held the fresh cup low while {friend.id} took the first careful sip. '
            f'Then {carrier.id} drank, and the sweet {drink.label} tasted even better because it was shared.'
        )
        world.say(
            f'They crossed the slippery place together, slow as moonlight, and not one bubble was lost.'
        )
        return
    if treat.meters["shared"] >= THRESHOLD:
        world.say(
            f'Together they reached the picnic stone with the cup safe between them. '
            f'They took turns sipping until both whiskers shone with tiny bubbles.'
        )
        world.say(
            f'The path had been tricky, but sharing had made their steps steady.'
        )
        return
    world.say(
        f'Even without magic, they sat side by side until the sad feeling passed, and that was a kind of treasure too.'
    )


def tell(
    carrier_cfg: AnimalKind,
    friend_cfg: AnimalKind,
    drink_cfg: DrinkKind,
    container_cfg: ContainerKind,
    surface_cfg: SurfaceKind,
    magic_cfg: MagicKind,
    carrier_name: str,
    friend_name: str,
    greedy: bool,
) -> World:
    world = World()
    carrier = world.add(
        Entity(
            id=carrier_name,
            kind="character",
            type=carrier_cfg.id,
            label=carrier_cfg.label,
            phrase=carrier_cfg.phrase,
            role="carrier",
            traits=[carrier_cfg.trait],
            tags=set(carrier_cfg.tags),
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_cfg.id,
            label=friend_cfg.label,
            phrase=friend_cfg.phrase,
            role="friend",
            traits=[friend_cfg.trait],
            tags=set(friend_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="path",
            kind="thing",
            type="surface",
            label=surface_cfg.label,
            phrase=surface_cfg.phrase,
            slippery=surface_cfg.slippery,
            tags=set(surface_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="treat",
            kind="thing",
            type="drink",
            label=drink_cfg.label,
            phrase=drink_cfg.phrase,
            tags=set(drink_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="container",
            kind="thing",
            type="container",
            label=container_cfg.label,
            phrase=container_cfg.phrase,
            hold_liquid=container_cfg.hold_liquid,
            attrs={"plural": container_cfg.plural},
            tags=set(container_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="helper",
            kind="character",
            type=magic_cfg.id,
            label=magic_cfg.label,
            phrase=magic_cfg.phrase,
            role="helper",
            magic=True,
            tags=set(magic_cfg.tags),
        )
    )

    world.facts.update(
        carrier=carrier,
        friend=friend,
        drink_cfg=drink_cfg,
        container_cfg=container_cfg,
        surface_cfg=surface_cfg,
        magic_cfg=magic_cfg,
        greedy=greedy,
    )

    introduce(world, carrier_cfg, friend_cfg)
    fill_treat(world)

    world.para()
    wanting(world)
    warning(world)
    choose(world, greedy=greedy)

    world.para()
    if world.facts["outcome"] == "spilled_then_shared":
        slip_scene(world)
        comfort(world)
        world.para()
        magic_help(world)
    elif world.facts["outcome"] in {"shared_early", "kept_balance"}:
        magic_help(world)

    world.para()
    ending(world)

    world.facts.update(
        slipped=world.get("treat").meters["spill"] >= THRESHOLD,
        shared=world.get("treat").meters["shared"] >= THRESHOLD or container_cfg.plural,
        magical=world.get("treat").meters["magic"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "slip": [
        (
            "Why can moss or wet stones make you slip?",
            "Moss and wet stones can be slick, so feet or paws do not grip them well. That is why slow steps help on shiny ground."
        )
    ],
    "fizz": [
        (
            "What does fizz mean?",
            "Fizz means lots of tiny bubbles popping and hurrying in a drink. Those little bubbles can make a soft, sparkling sound."
        )
    ],
    "sharing": [
        (
            "Why does sharing help friends?",
            "Sharing helps both friends feel included and cared for. It can turn grabbing and worry into calm, happy play."
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is something wondrous that cannot happen in ordinary life, like a glowing helper renewing a spring. It often appears when a character learns to be kind or brave."
        )
    ],
    "firefly": [
        (
            "Why do fireflies glow?",
            "Fireflies glow by making light inside their bodies. In real life they use that light to signal in the dark."
        )
    ],
    "frog": [
        (
            "Where do frogs like to live?",
            "Frogs like damp places such as ponds, reeds, and muddy banks. Wet places help keep their skin comfortable."
        )
    ],
    "bird": [
        (
            "Why can a bird seem magical in a story?",
            "A bird can seem magical because it arrives lightly and quickly, as if it came from the sky with a secret. Story magic often uses bright feathers or song to show wonder."
        )
    ],
}

KNOWLEDGE_ORDER = ["slip", "fizz", "sharing", "magic", "firefly", "frog", "bird"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    carrier = f["carrier"]
    friend = f["friend"]
    drink = f["drink_cfg"]
    surface = f["surface_cfg"]
    helper = f["magic_cfg"]
    return [
        f'Write a short animal story for a young child that includes the words "slip" and "fizz".',
        f"Tell a gentle story where {carrier.id} the {carrier.label} and {friend.id} the {friend.label} find {drink.label}, face trouble on {surface.phrase}, and learn to share.",
        f"Write a story with dialogue, sharing, and magic, where a {helper.label} helps two animal friends after a selfish moment turns into a kinder one.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    carrier = f["carrier"]
    friend = f["friend"]
    drink = f["drink_cfg"]
    surface = f["surface_cfg"]
    helper = f["magic_cfg"]
    container = f["container_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {carrier.id} the {carrier.label} and {friend.id} the {friend.label}. They are two small animal friends who find a sparkling spring together."
        ),
        (
            "What did they find in the glade?",
            f"They found a bubbling spring that made {drink.label}. The drink smelled {drink.smell} and sounded full of tiny fizzing bubbles."
        ),
        (
            f"Why did {friend.id} warn {carrier.id} to slow down?",
            f"{friend.id} warned {carrier.id} because {surface.phrase} was slippery. If {carrier.id} rushed while carrying the fizzy drink, {carrier.pronoun()} might slip and spill it."
        ),
    ]
    if container.plural:
        qa.append(
            (
                "How did they share the drink?",
                f"They each had a little bowl, so they carried the drink side by side and drank together. The sharing happened early, before the path could cause trouble."
            )
        )
    elif f.get("slipped"):
        qa.append(
            (
                f"What happened when {carrier.id} hurried?",
                f"{carrier.id} gave a slip on {surface.phrase}, and the drink spilled. The loss happened because {carrier.pronoun()} tried to keep it all instead of slowing down and sharing."
            )
        )
        qa.append(
            (
                f"How did the magic helper change the story?",
                f"The {helper.label} came when the friends chose kindness after the spill. Its magic brought the bubbles back, and the new drink tasted sweeter because the friends shared it."
            )
        )
    else:
        qa.append(
            (
                f"What did {carrier.id} decide after hearing the warning?",
                f"{carrier.id} stopped trying to keep the whole cup and chose to share. That decision made the walk steadier because the rushing feeling was gone."
            )
        )
    qa.append(
        (
            "What lesson did the animals learn?",
            f"They learned that sparkling treats and happy moments are better when shared. The story shows that kindness can steady quick feet and even invite magic."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"slip", "fizz", "sharing", "magic"}
    helper = world.facts["magic_cfg"]
    if helper.id == "firefly":
        tags.add("firefly")
    elif helper.id == "frog":
        tags.add("frog")
    else:
        tags.add("bird")
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.slippery:
            bits.append("slippery=True")
        if ent.magic:
            bits.append("magic=True")
        if ent.hold_liquid:
            bits.append("hold_liquid=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Valid story materials: the carrier animal exists, the container can hold liquid,
% and the chosen path is genuinely slippery.
valid(A, C, S) :- animal(A), container(C), holds_liquid(C), surface(S), slippery(S).

% Outcome model:
% two bowls means the drink is already shareable, so the friends share early.
shared_early :- chosen_container(C), container_plural(C).

% with one cup, a greedy carrier rushes unless they are not greedy.
rushes :- chosen_container(C), not container_plural(C), greedy.
slipped :- chosen_surface(S), slippery(S), rushes.

magic_restores :- slipped.
magic_visits :- shared_early.
magic_visits :- magic_restores.

outcome(shared_early) :- shared_early.
outcome(spilled_then_shared) :- slipped.
outcome(shared_carefully) :- not slipped, not shared_early.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for cid, container in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if container.hold_liquid:
            lines.append(asp.fact("holds_liquid", cid))
        if container.plural:
            lines.append(asp.fact("container_plural", cid))
    for sid, surface in SURFACES.items():
        lines.append(asp.fact("surface", sid))
        if surface.slippery:
            lines.append(asp.fact("slippery", sid))
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
            asp.fact("chosen_container", params.container),
            asp.fact("chosen_surface", params.surface),
            asp.fact("greedy") if params.greedy else "",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    container = CONTAINERS[params.container]
    surface = SURFACES[params.surface]
    if container.plural:
        return "shared_early"
    if params.greedy and surface.slippery:
        return "spilled_then_shared"
    return "shared_carefully"


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
            cases.append(params)
        except StoryError:
            rc = 1
            print("Unexpected StoryError during random param resolution.")
            break

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
        sample = generate(CURATED[0])
        if not sample.story or "slip" not in sample.story.lower() or "fizz" not in sample.story.lower():
            raise StoryError("Smoke test failed: generated story missing expected story content.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a fizzy spring, a slippery path, sharing, and magic."
    )
    ap.add_argument("--carrier", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--magic-helper", choices=MAGIC, dest="magic_helper")
    ap.add_argument("--greedy", choices=["yes", "no"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


NAME_POOL = {
    "rabbit": ["Moss", "Clover", "Thimble", "Poppy"],
    "fox": ["Pip", "Fern", "Ember", "Rill"],
    "otter": ["Ripple", "Pebble", "Drift", "Sunny"],
    "squirrel": ["Nip", "Hazel", "Twig", "Bramble"],
}


def pick_name(rng: random.Random, animal_id: str, avoid: str = "") -> str:
    choices = [n for n in NAME_POOL[animal_id] if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.container and not CONTAINERS[args.container].hold_liquid:
        surface = SURFACES[args.surface] if args.surface else next(v for v in SURFACES.values())
        raise StoryError(explain_rejection(CONTAINERS[args.container], surface))
    if args.surface and not SURFACES[args.surface].slippery:
        container = CONTAINERS[args.container] if args.container else next(v for v in CONTAINERS.values() if v.hold_liquid)
        raise StoryError(explain_rejection(container, SURFACES[args.surface]))
    if args.carrier and args.friend and not distinct_animals(args.carrier, args.friend):
        raise StoryError("(No story: the carrier and friend should be different kinds of animals for a clearer little tale.)")

    combos = [
        combo
        for combo in valid_combos()
        if (args.carrier is None or combo[0] == args.carrier)
        and (args.container is None or combo[1] == args.container)
        and (args.surface is None or combo[2] == args.surface)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    carrier_id, container_id, surface_id = rng.choice(sorted(combos))
    friend_choices = [aid for aid in sorted(ANIMALS) if aid != carrier_id]
    if args.friend:
        if args.friend == carrier_id:
            raise StoryError("(No story: the carrier and friend cannot be the same animal kind.)")
        friend_id = args.friend
    else:
        friend_id = rng.choice(friend_choices)

    drink_id = args.drink or rng.choice(sorted(DRINKS))
    magic_id = args.magic_helper or rng.choice(sorted(MAGIC))
    greedy = {"yes": True, "no": False}.get(args.greedy, rng.choice([True, False]))
    carrier_name = pick_name(rng, carrier_id)
    friend_name = pick_name(rng, friend_id, avoid=carrier_name)
    return StoryParams(
        carrier=carrier_id,
        friend=friend_id,
        drink=drink_id,
        container=container_id,
        surface=surface_id,
        magic_helper=magic_id,
        carrier_name=carrier_name,
        friend_name=friend_name,
        greedy=greedy,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        carrier_cfg = ANIMALS[params.carrier]
        friend_cfg = ANIMALS[params.friend]
        drink_cfg = DRINKS[params.drink]
        container_cfg = CONTAINERS[params.container]
        surface_cfg = SURFACES[params.surface]
        magic_cfg = MAGIC[params.magic_helper]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not distinct_animals(params.carrier, params.friend):
        raise StoryError("(No story: the carrier and friend cannot be the same animal kind.)")
    if not container_cfg.hold_liquid or not surface_cfg.slippery:
        raise StoryError(explain_rejection(container_cfg, surface_cfg))

    world = tell(
        carrier_cfg=carrier_cfg,
        friend_cfg=friend_cfg,
        drink_cfg=drink_cfg,
        container_cfg=container_cfg,
        surface_cfg=surface_cfg,
        magic_cfg=magic_cfg,
        carrier_name=params.carrier_name,
        friend_name=params.friend_name,
        greedy=params.greedy,
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
        print(f"{len(combos)} compatible (carrier, container, surface) combos:\n")
        for carrier, container, surface in combos:
            print(f"  {carrier:10} {container:12} {surface}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.carrier_name} the {p.carrier} and {p.friend_name} the {p.friend}: "
                f"{p.drink} on {p.surface} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
