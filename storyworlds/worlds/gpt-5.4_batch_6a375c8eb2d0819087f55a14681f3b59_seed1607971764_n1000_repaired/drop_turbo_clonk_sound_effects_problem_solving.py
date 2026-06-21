#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/drop_turbo_clonk_sound_effects_problem_solving.py
==============================================================================

A standalone story world for a small animal tale about a speedy cart, a bumpy
path, a dropped picnic treat, and a clever fix. Every story includes the words
"drop", "turbo", and "clonk", uses sound effects in the prose, turns on a
problem-solving beat, and ends happily.

Run it
------
python storyworlds/worlds/gpt-5.4/drop_turbo_clonk_sound_effects_problem_solving.py
python storyworlds/worlds/gpt-5.4/drop_turbo_clonk_sound_effects_problem_solving.py --cargo pie_tin --path root_trail --fix blanket_nest
python storyworlds/worlds/gpt-5.4/drop_turbo_clonk_sound_effects_problem_solving.py --path moss_lane
python storyworlds/worlds/gpt-5.4/drop_turbo_clonk_sound_effects_problem_solving.py --all
python storyworlds/worlds/gpt-5.4/drop_turbo_clonk_sound_effects_problem_solving.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/drop_turbo_clonk_sound_effects_problem_solving.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import io
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        table = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return table[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Species:
    id: str
    kind: str
    home: str
    snack: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class PathCfg:
    id: str
    label: str
    phrase: str
    feature: str
    bump: int
    sound: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class CargoCfg:
    id: str
    label: str
    phrase: str
    treat: str
    container: str
    shape: str
    stability: int
    drop_sound: str
    spill_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class FixCfg:
    id: str
    label: str
    phrase: str
    shapes: set[str]
    power: int
    method: str
    retry_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_wobble(world: World) -> list[str]:
    cart = world.get("cart")
    cargo = world.get("cargo")
    if cart.meters["speed"] < THRESHOLD or cargo.meters["arrived"] >= THRESHOLD:
        return []
    path_bump = world.facts["path_bump"]
    stability = cargo.attrs["stability"]
    secured = cargo.meters["secured"]
    if path_bump <= stability + secured:
        return []
    sig = ("wobble", int(cart.meters["speed"]), cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["wobble"] += 1
    world.get("hero").memes["alarm"] += 1
    world.get("helper").memes["worry"] += 1
    return ["__wobble__"]


def _r_drop(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.meters["wobble"] < THRESHOLD or cargo.meters["dropped"] >= THRESHOLD:
        return []
    sig = ("drop", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["dropped"] += 1
    cargo.meters["on_ground"] += 1
    cargo.meters["mess"] += 1
    world.get("hero").memes["sad"] += 1
    world.get("helper").memes["care"] += 1
    return ["__drop__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drop", tag="physical", apply=_r_drop),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


SPECIES = {
    "rabbit": Species(
        id="rabbit",
        kind="rabbit",
        home="burrow",
        snack="clover sandwiches",
        tags={"rabbit"},
    ),
    "squirrel": Species(
        id="squirrel",
        kind="squirrel",
        home="oak tree",
        snack="acorn cakes",
        tags={"squirrel"},
    ),
    "hedgehog": Species(
        id="hedgehog",
        kind="hedgehog",
        home="fern patch",
        snack="berry buns",
        tags={"hedgehog"},
    ),
    "otter": Species(
        id="otter",
        kind="otter",
        home="river bend",
        snack="minty fish-shaped biscuits",
        tags={"otter"},
    ),
}

PATHS = {
    "root_trail": PathCfg(
        id="root_trail",
        label="root trail",
        phrase="the root trail up to the picnic stump",
        feature="roots that stuck up like knobby fingers",
        bump=3,
        sound="ratta-tat",
        tags={"trail", "bumpy"},
    ),
    "plank_bridge": PathCfg(
        id="plank_bridge",
        label="plank bridge",
        phrase="the plank bridge over the little stream",
        feature="old boards that knocked under little wheels",
        bump=2,
        sound="tok-tok",
        tags={"bridge", "stream"},
    ),
    "pebble_bend": PathCfg(
        id="pebble_bend",
        label="pebble bend",
        phrase="the pebble bend by the daisies",
        feature="round stones that clicked under the cart",
        bump=2,
        sound="tik-tik",
        tags={"pebbles"},
    ),
    "moss_lane": PathCfg(
        id="moss_lane",
        label="moss lane",
        phrase="the soft moss lane behind the ferns",
        feature="a springy green floor as soft as a pillow",
        bump=1,
        sound="fuff-fuff",
        tags={"moss"},
    ),
}

CARGO = {
    "pie_tin": CargoCfg(
        id="pie_tin",
        label="pie tin",
        phrase="a little blueberry pie in a shiny tin",
        treat="blueberry pie",
        container="tin",
        shape="round",
        stability=1,
        drop_sound="clonk",
        spill_text="The lid hopped crooked, and a blue line of jam peeped out at the edge.",
        ending_text="The pie reached the picnic stump in one neat, sweet-smelling piece.",
        tags={"pie", "blueberries"},
    ),
    "acorn_jar": CargoCfg(
        id="acorn_jar",
        label="acorn jar",
        phrase="a tall glass jar of acorn cookies",
        treat="acorn cookies",
        container="jar",
        shape="tall",
        stability=1,
        drop_sound="clonk",
        spill_text="The jar tipped on its side, but the cork stayed in and the cookies were safe inside.",
        ending_text="The jar stood straight and proud on the picnic cloth, full of crunchy cookies.",
        tags={"jar", "cookies"},
    ),
    "berry_basket": CargoCfg(
        id="berry_basket",
        label="berry basket",
        phrase="a small basket of red berries",
        treat="red berries",
        container="basket",
        shape="loose",
        stability=1,
        drop_sound="clonk",
        spill_text="A few berries rolled into the grass, but most of them stayed tucked in the basket.",
        ending_text="The basket arrived with every bright berry ready for nibbling.",
        tags={"berries", "basket"},
    ),
}

FIXES = {
    "blanket_nest": FixCfg(
        id="blanket_nest",
        label="moss blanket nest",
        phrase="a moss blanket nest",
        shapes={"round"},
        power=2,
        method="tucked a soft moss blanket into the cart and made a snug little nest around the tin",
        retry_line="No turbo this time. Let the wheels hum slowly.",
        tags={"blanket", "padding"},
    ),
    "vine_strap": FixCfg(
        id="vine_strap",
        label="springy vine strap",
        phrase="a springy vine strap",
        shapes={"tall"},
        power=3,
        method="wrapped a springy vine around the jar and tied it to the cart so it could not lean",
        retry_line="Let's roll carefully and keep the jar standing tall.",
        tags={"strap", "vine"},
    ),
    "leaf_lid": FixCfg(
        id="leaf_lid",
        label="broad leaf lid",
        phrase="a broad leaf lid",
        shapes={"loose"},
        power=2,
        method="laid a broad leaf over the basket and tied it down with grass so the berries would stay tucked in",
        retry_line="Easy wheels now. The berries can ride like sleepy babies.",
        tags={"leaf", "cover"},
    ),
}


def hazard_exists(path: PathCfg, cargo: CargoCfg) -> bool:
    return path.bump > cargo.stability


def fix_works(path: PathCfg, cargo: CargoCfg, fix: FixCfg) -> bool:
    return (
        hazard_exists(path, cargo)
        and cargo.shape in fix.shapes
        and cargo.stability + fix.power > path.bump
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cargo_id, cargo in CARGO.items():
        for path_id, path in PATHS.items():
            for fix_id, fix in FIXES.items():
                if fix_works(path, cargo, fix):
                    combos.append((cargo_id, path_id, fix_id))
    return sorted(combos)


@dataclass
class StoryParams:
    cargo: str
    path: str
    fix: str
    hero_species: str
    helper_species: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


NAME_POOLS = {
    "rabbit": ["Pip", "Mallow", "Nip", "Tansy", "Bramble"],
    "squirrel": ["Nutmeg", "Skip", "Hazel", "Pico", "Twig"],
    "hedgehog": ["Pebble", "Tumble", "Poppy", "Burr", "Mossy"],
    "otter": ["Ripple", "Finn", "Drift", "Mina", "Splash"],
}

WORLD_KNOWLEDGE = {
    "trail": [
        (
            "Why can a bumpy trail shake a little cart?",
            "When wheels bump over roots or stones, the cart jiggles up and down. If something inside is not tucked in well, it can wobble and slide.",
        )
    ],
    "bridge": [
        (
            "Why do wooden bridges make knocking sounds under wheels?",
            "Wooden planks can sound hollow when wheels tap across them. That is why a bridge can go tok-tok under a cart.",
        )
    ],
    "moss": [
        (
            "Why is moss softer than stones?",
            "Moss is springy and gentle, so it cushions little feet and wheels. Stones are hard, so they make stronger bumps.",
        )
    ],
    "pie": [
        (
            "Why is a pie easier to jostle when it rides in a cart?",
            "A pie in a tin can slide if the cart tips or bounces. Soft padding helps keep it from slipping around.",
        )
    ],
    "jar": [
        (
            "Why should a tall jar be tied on carefully?",
            "A tall jar can lean when the cart turns or bumps. A strap helps keep it upright.",
        )
    ],
    "basket": [
        (
            "Why put a cover on a berry basket?",
            "A cover helps little berries stay tucked inside when the basket jiggles. That way they do not bounce out on the road.",
        )
    ],
    "blanket": [
        (
            "What does padding do in a cart?",
            "Padding makes a soft nest around what you carry. It helps absorb bumps so things wobble less.",
        )
    ],
    "strap": [
        (
            "What does a strap do?",
            "A strap holds something in place so it does not tip or slide away. It is a simple way to make carrying safer.",
        )
    ],
    "leaf": [
        (
            "How can a big leaf help in the forest?",
            "A big leaf can work like a light lid or cover. Animals in stories often use leaves to protect things gently.",
        )
    ],
}
KNOWLEDGE_ORDER = ["trail", "bridge", "moss", "pie", "jar", "basket", "blanket", "strap", "leaf"]


CURATED = [
    StoryParams(
        cargo="pie_tin",
        path="root_trail",
        fix="blanket_nest",
        hero_species="rabbit",
        helper_species="hedgehog",
        hero_name="Pip",
        helper_name="Tumble",
        seed=1,
    ),
    StoryParams(
        cargo="acorn_jar",
        path="plank_bridge",
        fix="vine_strap",
        hero_species="squirrel",
        helper_species="otter",
        hero_name="Hazel",
        helper_name="Drift",
        seed=2,
    ),
    StoryParams(
        cargo="berry_basket",
        path="pebble_bend",
        fix="leaf_lid",
        hero_species="hedgehog",
        helper_species="rabbit",
        hero_name="Pebble",
        helper_name="Mallow",
        seed=3,
    ),
    StoryParams(
        cargo="pie_tin",
        path="plank_bridge",
        fix="blanket_nest",
        hero_species="otter",
        helper_species="squirrel",
        hero_name="Ripple",
        helper_name="Nutmeg",
        seed=4,
    ),
]


def choose_name(rng: random.Random, species: str, avoid: str = "") -> str:
    pool = [n for n in NAME_POOLS[species] if n != avoid]
    return rng.choice(pool)


def explain_rejection(cargo: CargoCfg, path: PathCfg, fix: Optional[FixCfg] = None) -> str:
    if not hazard_exists(path, cargo):
        return (
            f"(No story: {cargo.phrase} would ride safely over {path.phrase}. "
            f"The path is too gentle, so there is no honest drop problem to solve.)"
        )
    if fix is not None and cargo.shape not in fix.shapes:
        return (
            f"(No story: {fix.label} does not suit {cargo.phrase}. "
            f"It cannot steady a {cargo.shape} load.)"
        )
    if fix is not None and cargo.stability + fix.power <= path.bump:
        return (
            f"(No story: {fix.label} is too weak for {path.phrase}. "
            f"The fix must really solve the wobble problem.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def setup_story(world: World, hero: Entity, helper: Entity, cargo_cfg: CargoCfg, path_cfg: PathCfg) -> None:
    cart = world.get("cart")
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"One bright morning in the little woods, {hero.id} the {hero.type} and "
        f"{helper.id} the {helper.type} packed {cargo_cfg.phrase} for a picnic."
    )
    world.say(
        f"They wanted to take it along {path_cfg.phrase}, all the way to a stump "
        f"set with daisy cups and tiny napkins."
    )
    world.say(
        f"{hero.id} pulled out {cart.phrase}. The word turbo was painted on the side "
        f"in wiggly yellow letters, and the wheels looked eager to spin."
    )


def warning(world: World, hero: Entity, helper: Entity, cargo_cfg: CargoCfg, path_cfg: PathCfg) -> None:
    helper.memes["worry"] += 1
    world.say(
        f'{helper.id} looked at the {path_cfg.feature} and then at the {cargo_cfg.container}. '
        f'"If you go too fast, the cart might wobble and the {cargo_cfg.treat} could drop," '
        f'{helper.pronoun()} warned.'
    )


def first_ride(world: World, hero: Entity, helper: Entity, cargo_cfg: CargoCfg, path_cfg: PathCfg) -> None:
    cart = world.get("cart")
    cargo = world.get("cargo")
    hero.memes["pride"] += 1
    cart.meters["speed"] = 2.0
    cargo.meters["secured"] = 0.0
    world.say(
        f'"Turbo ride!" cried {hero.id}. Whirr! went the wheels. {path_cfg.sound}! '
        f'went the path under the cart as it hurried along.'
    )
    markers = propagate(world, narrate=False)
    if "__drop__" in markers or cargo.meters["dropped"] >= THRESHOLD:
        world.say(
            f"Then the cart gave a sharp hop. {cargo_cfg.drop_sound.capitalize()}! "
            f"went the {cargo_cfg.container} as it bounced out and did a worried little drop onto the grass."
        )
        world.say(cargo_cfg.spill_text)
        world.say(
            f"{hero.id} stopped so fast that the cart squeaked. {helper.id} hurried over, "
            f"and both friends peered down to see what could still be saved."
        )
    else:
        world.say(
            f"The cart rattled but somehow kept going. Even so, {helper.id} looked more worried than before."
        )


def think_together(world: World, hero: Entity, helper: Entity, cargo_cfg: CargoCfg, fix_cfg: FixCfg) -> None:
    hero.memes["sad"] += 1
    helper.memes["clever"] += 1
    world.say(
        f"For a moment, {hero.id}'s ears drooped. \"I only wanted a fast ride,\" {hero.pronoun()} murmured."
    )
    world.say(
        f"But {helper.id} did not fuss. {helper.pronoun().capitalize()} touched the cart, "
        f"looked at the {cargo_cfg.container}, and thought hard with a kind, steady face."
    )
    world.say(
        f'"I know a better plan," said {helper.id}. "We do not need more turbo. We need a smart fix."'
    )


def apply_fix(world: World, hero: Entity, helper: Entity, fix_cfg: FixCfg) -> None:
    cargo = world.get("cargo")
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    cargo.meters["secured"] = float(fix_cfg.power)
    cargo.meters["wobble"] = 0.0
    cargo.meters["on_ground"] = 0.0
    world.facts["solved_with"] = fix_cfg.label
    world.say(
        f"Together they {fix_cfg.method}. Small paws worked slowly, and soon the load sat snug and still."
    )
    world.say(f'"{fix_cfg.retry_line}" said {helper.id}. {hero.id} nodded this time.')


def second_ride(world: World, hero: Entity, helper: Entity, cargo_cfg: CargoCfg, path_cfg: PathCfg) -> None:
    cart = world.get("cart")
    cargo = world.get("cargo")
    cart.meters["speed"] = 1.0
    world.say(
        f"Off they went again. Creak-creak, hummm, went the little cart. "
        f"This time the wheels rolled gently over {path_cfg.phrase}."
    )
    markers = propagate(world, narrate=False)
    if "__drop__" in markers or cargo.meters["dropped"] > THRESHOLD:
        raise StoryError("The repair should keep the cargo safe on the second ride.")
    cargo.meters["arrived"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["lesson"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"The {cargo_cfg.container} stayed right where it belonged. Not a slip, not a bounce, not even a tiny clonk."
    )


def happy_ending(world: World, hero: Entity, helper: Entity, cargo_cfg: CargoCfg, path_cfg: PathCfg) -> None:
    world.say(
        f"At the picnic stump, the other animals clapped their paws when they saw the treat arrive."
    )
    world.say(
        f"{cargo_cfg.ending_text} {hero.id} laughed, and even {helper.id} gave the cart an admiring pat."
    )
    world.say(
        f'After that, whenever {hero.id} felt like shouting "turbo," {helper.id} would grin and ask, '
        f'"Fast first, or think first?" And {hero.id} always answered, "Think first."'
    )


def tell(
    hero_species: str,
    helper_species: str,
    hero_name: str,
    helper_name: str,
    cargo_id: str,
    path_id: str,
    fix_id: str,
) -> World:
    cargo_cfg = CARGO[cargo_id]
    path_cfg = PATHS[path_id]
    fix_cfg = FIXES[fix_id]

    world = World()
    world.facts["path_bump"] = path_cfg.bump
    world.facts["cargo_shape"] = cargo_cfg.shape
    world.facts["cargo_stability"] = cargo_cfg.stability

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_species,
            role="hero",
            label=hero_name,
            traits=["eager"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_species,
            role="helper",
            label=helper_name,
            traits=["careful"],
        )
    )
    cart = world.add(
        Entity(
            id="cart",
            type="cart",
            label="cart",
            phrase="a tiny red cart",
            attrs={"painted_word": "turbo"},
        )
    )
    cargo = world.add(
        Entity(
            id="cargo",
            type="cargo",
            label=cargo_cfg.label,
            phrase=cargo_cfg.phrase,
            attrs={
                "shape": cargo_cfg.shape,
                "stability": cargo_cfg.stability,
                "container": cargo_cfg.container,
                "treat": cargo_cfg.treat,
            },
        )
    )

    setup_story(world, hero, helper, cargo_cfg, path_cfg)
    world.para()
    warning(world, hero, helper, cargo_cfg, path_cfg)
    first_ride(world, hero, helper, cargo_cfg, path_cfg)
    world.para()
    think_together(world, hero, helper, cargo_cfg, fix_cfg)
    apply_fix(world, hero, helper, fix_cfg)
    second_ride(world, hero, helper, cargo_cfg, path_cfg)
    world.para()
    happy_ending(world, hero, helper, cargo_cfg, path_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        cargo_cfg=cargo_cfg,
        path_cfg=path_cfg,
        fix_cfg=fix_cfg,
        dropped=world.get("cargo").meters["dropped"] >= THRESHOLD,
        arrived=world.get("cargo").meters["arrived"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    cargo_cfg = world.facts["cargo_cfg"]
    path_cfg = world.facts["path_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the words "drop", "turbo", and "clonk".',
        f"Tell a gentle forest story where {hero.id} the {hero.type} tries to rush {cargo_cfg.treat} along {path_cfg.phrase}, something drops with a clonk, and {helper.id} helps solve the problem.",
        f"Write a happy story with sound effects where friends use {fix_cfg.label} to make a bumpy cart ride safe.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    cargo_cfg = world.facts["cargo_cfg"]
    path_cfg = world.facts["path_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {helper.id} the {helper.type}. They were taking {cargo_cfg.treat} to a picnic together.",
        ),
        (
            f"Why did the {cargo_cfg.container} drop from the cart?",
            f"It dropped because {hero.id} tried a turbo ride over {path_cfg.phrase}, which was too bumpy for that load. The cart wobbled, so the {cargo_cfg.container} bounced out with a clonk.",
        ),
        (
            "What problem did the friends have to solve?",
            f"They had to figure out how to carry the {cargo_cfg.treat} safely after the first ride went wrong. The problem was not the picnic itself, but the shaky trip along the bumpy path.",
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} stayed calm and studied the cart instead of scolding. Then {helper.pronoun().capitalize()} suggested {fix_cfg.phrase}, which matched the shape of the load and kept it steady.",
        ),
        (
            "How did the story end?",
            f"The friends rolled slowly on the second try, and the treat arrived safely at the picnic stump. The ending shows that {hero.id} learned to think first instead of shouting turbo first.",
        ),
    ]
    if world.facts["dropped"]:
        items.append(
            (
                'What did the word "clonk" mean in the story?',
                f'It was the sound of the {cargo_cfg.container} hitting the ground when it fell out of the cart. That sound showed the exact moment the problem became real.',
            )
        )
    return items


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    path_cfg = world.facts["path_cfg"]
    cargo_cfg = world.facts["cargo_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    tags: set[str] = set(path_cfg.tags) | set(cargo_cfg.tags) | set(fix_cfg.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risky(C, P) :- cargo(C), path(P), bump(P, B), stability(C, S), B > S.
works(F, C, P) :- risky(C, P), fix(F), shape(C, Sh), supports(F, Sh),
                  power(F, Pw), bump(P, B), stability(C, S), S + Pw > B.
valid(C, P, F) :- cargo(C), path(P), fix(F), works(F, C, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("shape", cargo_id, cargo.shape))
        lines.append(asp.fact("stability", cargo_id, cargo.stability))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("bump", path_id, path.bump))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("power", fix_id, fix.power))
        for shape in sorted(fix.shapes):
            lines.append(asp.fact("supports", fix_id, shape))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a turbo cart, a drop with a clonk, and a smart happy fix."
    )
    ap.add_argument("--cargo", choices=sorted(CARGO))
    ap.add_argument("--path", choices=sorted(PATHS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--hero-species", choices=sorted(SPECIES))
    ap.add_argument("--helper-species", choices=sorted(SPECIES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.path:
        cargo = CARGO[args.cargo]
        path = PATHS[args.path]
        if not hazard_exists(path, cargo):
            raise StoryError(explain_rejection(cargo, path))
    if args.cargo and args.path and args.fix:
        cargo = CARGO[args.cargo]
        path = PATHS[args.path]
        fix = FIXES[args.fix]
        if not fix_works(path, cargo, fix):
            raise StoryError(explain_rejection(cargo, path, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.path is None or combo[1] == args.path)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, path_id, fix_id = rng.choice(combos)

    hero_species = args.hero_species or rng.choice(sorted(SPECIES))
    helper_pool = [s for s in sorted(SPECIES) if s != hero_species]
    helper_species = args.helper_species or rng.choice(helper_pool)
    if helper_species == hero_species and len(SPECIES) > 1:
        helper_pool = [s for s in sorted(SPECIES) if s != hero_species]
        helper_species = rng.choice(helper_pool)

    hero_name = choose_name(rng, hero_species)
    helper_name = choose_name(rng, helper_species)

    return StoryParams(
        cargo=cargo_id,
        path=path_id,
        fix=fix_id,
        hero_species=hero_species,
        helper_species=helper_species,
        hero_name=hero_name,
        helper_name=helper_name,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGO:
        raise StoryError(f"Unknown cargo '{params.cargo}'.")
    if params.path not in PATHS:
        raise StoryError(f"Unknown path '{params.path}'.")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix '{params.fix}'.")
    if params.hero_species not in SPECIES:
        raise StoryError(f"Unknown hero species '{params.hero_species}'.")
    if params.helper_species not in SPECIES:
        raise StoryError(f"Unknown helper species '{params.helper_species}'.")

    cargo = CARGO[params.cargo]
    path = PATHS[params.path]
    fix = FIXES[params.fix]
    if not fix_works(path, cargo, fix):
        raise StoryError(explain_rejection(cargo, path, fix))

    world = tell(
        hero_species=params.hero_species,
        helper_species=params.helper_species,
        hero_name=params.hero_name,
        helper_name=params.helper_name,
        cargo_id=params.cargo,
        path_id=params.path,
        fix_id=params.fix,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "turbo" not in sample.story.lower() or "clonk" not in sample.story.lower():
            raise StoryError("Smoke test story missing required words.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story:
                raise StoryError("Generated empty story.")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation succeeded on 20 seeds.")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (cargo, path, fix) combos:\n")
        for cargo_id, path_id, fix_id in combos:
            print(f"  {cargo_id:12} {path_id:12} {fix_id}")
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.cargo} on {p.path} with {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
