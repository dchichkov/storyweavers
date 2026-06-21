#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/passenger_shopping_mall_repetition_sound_effects_fable.py
=====================================================================================

A standalone storyworld for a small fable-like mall tale: a child pretends to be
a "passenger" on a rolling ride inside a shopping mall, keeps repeating a noisy,
unsafe habit, meets a clear turning point, and learns that a softer, safer choice
lets everyone share the space.

The world model tracks a rider, a companion, nearby shoppers, and the physical
and emotional effects of noise and movement. The story is state-driven: repeated
clang-clang play builds disturbance; a wobble and near-accident create the turn;
then a safer plan resolves the tension.

Run it
------
    python storyworlds/worlds/gpt-5.4/passenger_shopping_mall_repetition_sound_effects_fable.py
    python storyworlds/worlds/gpt-5.4/passenger_shopping_mall_repetition_sound_effects_fable.py --cart stroller --noise bell
    python storyworlds/worlds/gpt-5.4/passenger_shopping_mall_repetition_sound_effects_fable.py --cargo glass_bottle
    python storyworlds/worlds/gpt-5.4/passenger_shopping_mall_repetition_sound_effects_fable.py --all
    python storyworlds/worlds/gpt-5.4/passenger_shopping_mall_repetition_sound_effects_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/passenger_shopping_mall_repetition_sound_effects_fable.py --qa --json
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
    wheels: bool = False
    fragile: bool = False
    ringable: bool = False
    quiet_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class CartKind:
    id: str
    label: str
    phrase: str
    rider_spot: str
    glide: str
    stop: str
    ring_allowed: bool = False
    suitable_cargo: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class NoiseKind:
    id: str
    cry: str
    sound: str
    verb: str
    disturbance: int
    sense: int
    text: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CargoKind:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    heavy: bool = False
    suitable_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class FixKind:
    id: str
    label: str
    phrase: str
    quiet_gain: int
    steady_gain: int
    sense: int
    text: str
    ending: str
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


def _r_noise_disturbs(world: World) -> list[str]:
    out: list[str] = []
    cart = world.get("cart")
    rider = world.get("rider")
    companion = world.get("companion")
    shoppers = world.get("shoppers")
    if cart.meters["noise"] >= THRESHOLD:
        sig = ("noise_disturbs", int(cart.meters["noise"]))
        if sig not in world.fired:
            world.fired.add(sig)
            shoppers.memes["annoyed"] += 1
            companion.memes["concern"] += 1
            out.append("__noise__")
    if rider.memes["showing_off"] >= 2 and cart.meters["noise"] >= 2:
        sig = ("echo_pride",)
        if sig not in world.fired:
            world.fired.add(sig)
            rider.memes["pride"] += 1
    return out


def _r_wobble_risk(world: World) -> list[str]:
    out: list[str] = []
    cart = world.get("cart")
    cargo = world.get("cargo")
    rider = world.get("rider")
    if cart.meters["jolts"] >= THRESHOLD:
        sig = ("wobble", int(cart.meters["jolts"]))
        if sig in world.fired:
            return out
        world.fired.add(sig)
        cart.meters["wobble"] += 1
        rider.memes["surprise"] += 1
        if cargo.fragile:
            cargo.meters["risk"] += 1
        out.append("__wobble__")
    return out


def _r_near_break(world: World) -> list[str]:
    out: list[str] = []
    cart = world.get("cart")
    cargo = world.get("cargo")
    companion = world.get("companion")
    if cargo.meters["risk"] >= THRESHOLD and cart.meters["wobble"] >= THRESHOLD:
        sig = ("near_break",)
        if sig not in world.fired:
            world.fired.add(sig)
            companion.memes["alarm"] += 1
            cargo.meters["clinked"] += 1
            out.append("__near_break__")
    return out


def _r_fix_calms(world: World) -> list[str]:
    out: list[str] = []
    rider = world.get("rider")
    companion = world.get("companion")
    shoppers = world.get("shoppers")
    if rider.memes["listened"] >= THRESHOLD:
        sig = ("calm_after_listen",)
        if sig not in world.fired:
            world.fired.add(sig)
            companion.memes["relief"] += 1
            shoppers.memes["relief"] += 1
            rider.memes["care"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="noise_disturbs", tag="social", apply=_r_noise_disturbs),
    Rule(name="wobble_risk", tag="physical", apply=_r_wobble_risk),
    Rule(name="near_break", tag="physical", apply=_r_near_break),
    Rule(name="fix_calms", tag="social", apply=_r_fix_calms),
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


def cargo_fits(cart: CartKind, cargo: CargoKind) -> bool:
    return cargo.id in cart.suitable_cargo and cart.id in cargo.suitable_for


def sensible_noise(noise: NoiseKind) -> bool:
    return noise.sense >= SENSE_MIN


def sensible_fix(fix: FixKind) -> bool:
    return fix.sense >= SENSE_MIN


def predict_turn(cart: CartKind, noise: NoiseKind, cargo: CargoKind) -> dict:
    sim = World()
    sim.add(Entity(id="rider", kind="character", type="child"))
    sim.add(Entity(id="companion", kind="character", type="adult"))
    sim.add(Entity(id="shoppers", type="group"))
    sim.add(Entity(id="cart", type=cart.id, label=cart.label, wheels=True))
    sim.add(Entity(id="cargo", type=cargo.id, label=cargo.label, fragile=cargo.fragile))
    for _ in range(3):
        sim.get("cart").meters["noise"] += noise.disturbance
        sim.get("cart").meters["jolts"] += 1
        sim.get("rider").memes["showing_off"] += 1
        propagate(sim, narrate=False)
    return {
        "wobble": sim.get("cart").meters["wobble"] >= THRESHOLD,
        "risk": sim.get("cargo").meters["risk"] >= THRESHOLD,
        "annoyed": sim.get("shoppers").memes["annoyed"] >= THRESHOLD,
    }


def introduce(world: World, rider: Entity, companion: Entity, cart: CartKind, cargo: CargoKind) -> None:
    world.say(
        f"In the middle of the shopping mall, {rider.id} walked beside {rider.pronoun('possessive')} "
        f"{companion.label_word} and a {cart.label} carrying {cargo.phrase}."
    )
    world.say(
        f"The shiny floor made the wheels {cart.glide}, and the bright shop windows "
        f"looked like little ponds of light."
    )


def invite_game(world: World, rider: Entity, cart: CartKind) -> None:
    rider.memes["joy"] += 1
    world.say(
        f'{rider.id} looked at the rolling {cart.label} and whispered, "I am the passenger today. '
        f'I am the passenger today. I am the passenger today."'
    )
    world.say(
        f"{rider.pronoun().capitalize()} climbed into {cart.rider_spot}, and the game began."
    )


def repeat_noise(world: World, rider: Entity, cart_ent: Entity, noise: NoiseKind) -> None:
    rider.memes["showing_off"] += 1
    cart_ent.meters["noise"] += noise.disturbance
    cart_ent.meters["jolts"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{noise.sound}! {noise.sound}! {noise.sound}! {rider.id} kept {noise.verb}, and the {cart_ent.label} '
        f'shuddered a little each time.'
    )


def adult_warning(world: World, rider: Entity, companion: Entity, cart: CartKind, noise: NoiseKind, cargo: CargoKind) -> None:
    pred = predict_turn(cart, noise, cargo)
    world.facts["predicted_annoyed"] = pred["annoyed"]
    world.facts["predicted_risk"] = pred["risk"]
    tail = ""
    if pred["risk"]:
        tail = f" {cargo.phrase.capitalize()} might tumble or break."
    world.say(
        f'"Soft wheels are happy wheels," said {companion.label_word}. '
        f'"A {cart.label} is for carrying, not for {noise.verb}.{tail}"'
    )


def defy(world: World, rider: Entity, noise: NoiseKind) -> None:
    rider.memes["defiance"] += 1
    world.say(
        f'But {rider.id} liked the echo too much. "{noise.cry}! {noise.cry}! {noise.cry}!" '
        f'{rider.pronoun().capitalize()} sang again.'
    )


def near_miss(world: World, rider: Entity, companion: Entity, cart_ent: Entity, cargo_ent: Entity, cargo: CargoKind) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then the front wheel went wibble-wobble. The {cart_ent.label} tipped, then caught itself."
    )
    if cargo.fragile:
        world.say(
            f"{cargo.phrase.capitalize()} gave a tiny clink-clink inside the basket, and {rider.id}'s heart went bump."
        )
    else:
        world.say(
            f"{cargo.phrase.capitalize()} slid to one side, and {rider.id}'s heart went bump."
        )
    rider.memes["fear"] += 1
    companion.memes["care"] += 1


def teach(world: World, rider: Entity, companion: Entity, noise: NoiseKind) -> None:
    world.say(
        f'{companion.label_word.capitalize()} steadied the handle and bent down. '
        f'"A loud game can make small trouble grow into big trouble. {noise.moral}"'
    )


def apply_fix(world: World, rider: Entity, cart_ent: Entity, companion: Entity, fix: FixKind) -> None:
    rider.memes["listened"] += 1
    cart_ent.meters["quiet"] += fix.quiet_gain
    cart_ent.meters["steady"] += fix.steady_gain
    cart_ent.meters["noise"] = 0.0
    cart_ent.meters["jolts"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{rider.id} climbed down at once, {fix.text}"
    )
    world.say(
        f"{companion.label_word.capitalize()} smiled when the wheels rolled {fix.ending}."
    )


def ending(world: World, rider: Entity, companion: Entity, cart: CartKind) -> None:
    rider.memes["joy"] += 1
    rider.memes["care"] += 1
    world.say(
        f'Soon {rider.id} walked beside the {cart.label} like a careful helper, not a shouting passenger.'
    )
    world.say(
        f"And in the shopping mall, the lesson went with them as softly as the wheels: "
        f"what repeats in noise may grow into trouble, but what repeats in care may grow into peace."
    )


def tell(
    rider_name: str,
    rider_gender: str,
    companion_type: str,
    companion_name: str,
    cart: CartKind,
    noise: NoiseKind,
    cargo: CargoKind,
    fix: FixKind,
) -> World:
    world = World()
    rider = world.add(Entity(id=rider_name, kind="character", type=rider_gender, role="rider"))
    companion = world.add(
        Entity(
            id=companion_name,
            kind="character",
            type=companion_type,
            role="companion",
            label="the parent",
        )
    )
    world.add(Entity(id="shoppers", type="group", label="other shoppers"))
    cart_ent = world.add(
        Entity(
            id="cart",
            type=cart.id,
            label=cart.label,
            phrase=cart.phrase,
            role="cart",
            wheels=True,
            tags=set(cart.tags),
        )
    )
    cargo_ent = world.add(
        Entity(
            id="cargo",
            type=cargo.id,
            label=cargo.label,
            phrase=cargo.phrase,
            role="cargo",
            fragile=cargo.fragile,
            tags=set(cargo.tags),
        )
    )

    introduce(world, rider, companion, cart, cargo)
    invite_game(world, rider, cart)

    world.para()
    repeat_noise(world, rider, cart_ent, noise)
    repeat_noise(world, rider, cart_ent, noise)
    adult_warning(world, rider, companion, cart, noise, cargo)
    defy(world, rider, noise)

    world.para()
    repeat_noise(world, rider, cart_ent, noise)
    near_miss(world, rider, companion, cart_ent, cargo_ent, cargo)
    teach(world, rider, companion, noise)

    world.para()
    apply_fix(world, rider, cart_ent, companion, fix)
    ending(world, rider, companion, cart)

    world.facts.update(
        rider=rider,
        companion=companion,
        cart_cfg=cart,
        noise_cfg=noise,
        cargo_cfg=cargo,
        fix_cfg=fix,
        cart=cart_ent,
        cargo=cargo_ent,
        repeated=True,
        near_miss=cart_ent.meters["wobble"] >= THRESHOLD,
        fragile_risk=cargo_ent.meters["risk"] >= THRESHOLD,
        calm_end=cart_ent.meters["quiet"] >= THRESHOLD,
    )
    return world


THEMES = ("mall",)

CARTS = {
    "shopping_cart": CartKind(
        id="shopping_cart",
        label="shopping cart",
        phrase="a shopping cart",
        rider_spot="the front child seat",
        glide="swish-swish",
        stop="rolled to a gentle stop",
        ring_allowed=False,
        suitable_cargo={"eggs", "glass_bottle", "bread"},
        tags={"cart", "mall"},
    ),
    "stroller": CartKind(
        id="stroller",
        label="stroller",
        phrase="a stroller",
        rider_spot="the small seat",
        glide="hush-hush",
        stop="came to a soft stop",
        ring_allowed=False,
        suitable_cargo={"toy_bag", "bread"},
        tags={"stroller", "mall"},
    ),
    "wagon": CartKind(
        id="wagon",
        label="mall wagon",
        phrase="a rented mall wagon",
        rider_spot="the padded seat",
        glide="rum-rum",
        stop="settled to a stop",
        ring_allowed=False,
        suitable_cargo={"toy_bag", "bread", "eggs"},
        tags={"wagon", "mall"},
    ),
}

NOISES = {
    "bell": NoiseKind(
        id="bell",
        cry="Ding",
        sound="Ding-ding",
        verb="ringing an imaginary bell against the handle",
        disturbance=1,
        sense=2,
        text="ringing",
        moral="A merry sound is only merry when it does not shake someone else's day.",
        tags={"sound", "noise"},
    ),
    "drum": NoiseKind(
        id="drum",
        cry="Bang",
        sound="Bang-bang",
        verb="drumming on the metal side",
        disturbance=2,
        sense=2,
        text="drumming",
        moral="Hands that make too much thunder can forget what quiet hands protect.",
        tags={"sound", "noise"},
    ),
    "horn": NoiseKind(
        id="horn",
        cry="Honk",
        sound="Honk-honk",
        verb="blowing a toy horn",
        disturbance=3,
        sense=1,
        text="blowing a horn",
        moral="A borrowed space is no place for a blast that startles everybody else.",
        tags={"sound", "noise", "horn"},
    ),
}

CARGO = {
    "eggs": CargoKind(
        id="eggs",
        label="egg carton",
        phrase="a carton of eggs",
        fragile=True,
        heavy=False,
        suitable_for={"shopping_cart", "wagon"},
        tags={"eggs", "fragile"},
    ),
    "glass_bottle": CargoKind(
        id="glass_bottle",
        label="glass bottle",
        phrase="a glass bottle of apple juice",
        fragile=True,
        heavy=False,
        suitable_for={"shopping_cart"},
        tags={"glass", "fragile"},
    ),
    "bread": CargoKind(
        id="bread",
        label="bread loaf",
        phrase="a warm loaf of bread",
        fragile=False,
        heavy=False,
        suitable_for={"shopping_cart", "stroller", "wagon"},
        tags={"bread"},
    ),
    "toy_bag": CargoKind(
        id="toy_bag",
        label="shopping bag",
        phrase="a bag with a new toy inside",
        fragile=False,
        heavy=False,
        suitable_for={"stroller", "wagon"},
        tags={"toy"},
    ),
}

FIXES = {
    "walk_beside": FixKind(
        id="walk_beside",
        label="walk beside",
        phrase="walk beside the cart",
        quiet_gain=2,
        steady_gain=2,
        sense=3,
        text="and put both feet on the floor. Then {rider} held one side of the basket and walked beside it".replace("{rider}", "carefully"),
        ending="straight and almost whisper-quiet",
        tags={"quiet", "walk"},
    ),
    "hold_list": FixKind(
        id="hold_list",
        label="hold the list",
        phrase="hold the shopping list",
        quiet_gain=2,
        steady_gain=1,
        sense=3,
        text="and took the shopping list instead, reading each little item in a soft voice",
        ending="smoothly past the bright windows",
        tags={"quiet", "help"},
    ),
    "hug_toy": FixKind(
        id="hug_toy",
        label="hug a toy",
        phrase="hug the soft toy",
        quiet_gain=1,
        steady_gain=1,
        sense=2,
        text="and hugged a soft toy from the bag so {sub} had something quiet to squeeze".replace("{sub}", "they"),
        ending="lightly and safely",
        tags={"quiet", "toy"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Ava", "Nora", "Ella", "Lucy"]
BOY_NAMES = ["Owen", "Ben", "Milo", "Sam", "Leo", "Finn"]
TRAITS = ["eager", "bright", "bouncy", "curious", "cheerful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for cart_id, cart in CARTS.items():
        for noise_id, noise in NOISES.items():
            if not sensible_noise(noise):
                continue
            for cargo_id, cargo in CARGO.items():
                if not cargo_fits(cart, cargo):
                    continue
                for fix_id, fix in FIXES.items():
                    if sensible_fix(fix):
                        combos.append((THEMES[0], cart_id, noise_id, cargo_id))
                        break
    return sorted(set(combos))


@dataclass
class StoryParams:
    cart: str
    noise: str
    cargo: str
    fix: str
    rider_name: str
    rider_gender: str
    companion_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cart": [
        (
            "What is a shopping cart for?",
            "A shopping cart is for carrying groceries or bags through a store or shopping mall. It should roll smoothly so people and things stay safe."
        )
    ],
    "stroller": [
        (
            "What is a stroller for?",
            "A stroller is for carrying a small child or a few small things. It should be pushed gently so it does not tip or bump."
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon is a little rolling carrier that can hold children or bags. It needs calm pulling or pushing so it stays steady."
        )
    ],
    "fragile": [
        (
            "What does fragile mean?",
            "Fragile means something can crack or break easily. Eggs and glass are fragile, so they need gentle handling."
        )
    ],
    "noise": [
        (
            "Why can loud noises bother people in a shared place?",
            "A loud noise can surprise people, interrupt their thinking, or make a peaceful place feel harsh. In a shared place, quiet helps everyone use the space together."
        )
    ],
    "mall": [
        (
            "What is a shopping mall?",
            "A shopping mall is a place with many stores gathered together in one building. Lots of people walk through it, so careful movement matters."
        )
    ],
    "quiet": [
        (
            "Why is it good to move quietly around other people?",
            "Moving quietly helps people feel calm and safe. It also makes it easier to notice what you are carrying and where you are going."
        )
    ],
    "eggs": [
        (
            "Why do eggs need gentle carrying?",
            "Egg shells are thin and can crack when they are bumped. That is why eggs should ride in a cart that moves carefully."
        )
    ],
    "glass": [
        (
            "Why can a glass bottle be risky in a moving cart?",
            "Glass can break if it falls or bangs hard against something. A steady cart lowers that risk."
        )
    ],
}

KNOWLEDGE_ORDER = ["mall", "cart", "stroller", "wagon", "noise", "fragile", "quiet", "eggs", "glass"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rider = f["rider"]
    cart = f["cart_cfg"]
    noise = f["noise_cfg"]
    cargo = f["cargo_cfg"]
    fix = f["fix_cfg"]
    return [
        f'Write a short fable set in a shopping mall about a child who calls themself a passenger and keeps making a repeated "{noise.sound}" sound in a {cart.label}.',
        f"Tell a gentle moral tale where {rider.id} treats a {cart.label} like a ride, bothers people with repeated noise, then learns to help carry {cargo.phrase} safely.",
        f'Write a child-facing story with repetition and sound effects that ends with the child choosing to {fix.phrase} instead of making a racket.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rider = f["rider"]
    companion = f["companion"]
    cart = f["cart_cfg"]
    noise = f["noise_cfg"]
    cargo = f["cargo_cfg"]
    fix = f["fix_cfg"]
    pw = companion.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {rider.id}, a child in a shopping mall, and {rider.pronoun('possessive')} {pw}. The story follows what happened when {rider.id} pretended to be a passenger in a {cart.label}."
        ),
        (
            f"Why did {rider.id} keep making the {noise.sound} sound?",
            f"{rider.id} thought the sound made the game feel exciting and liked hearing it repeat through the mall. The repeated noise also made {rider.pronoun('object')} forget that the cart was carrying real things, not just the game."
        ),
        (
            f"What was the danger in the {cart.label}?",
            f"The {cart.label} was carrying {cargo.phrase}, and the jolting made it wobble. Because the play kept shaking the cart, something fragile could have tipped or broken."
        ),
        (
            f"What changed {rider.id}'s mind?",
            f"The turning point came when the wheel went wibble-wobble and the load nearly tipped. That small scare showed {rider.pronoun('object')} that the repeated noise and shaking were becoming real trouble."
        ),
        (
            f"How did the story end?",
            f"{rider.id} chose to {fix.phrase} and help instead of acting like a noisy passenger. The ending proves the lesson because the wheels rolled softly and the mall felt peaceful again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"mall", "noise", "quiet"}
    cart = f["cart_cfg"]
    cargo = f["cargo_cfg"]
    tags |= set(cart.tags)
    tags |= set(cargo.tags)
    if cargo.fragile:
        tags.add("fragile")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("wheels", ent.wheels), ("fragile", ent.fragile), ("ringable", ent.ringable), ("quiet_tool", ent.quiet_tool)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cart="shopping_cart",
        noise="bell",
        cargo="eggs",
        fix="walk_beside",
        rider_name="Maya",
        rider_gender="girl",
        companion_type="mother",
        trait="eager",
    ),
    StoryParams(
        cart="stroller",
        noise="drum",
        cargo="toy_bag",
        fix="hold_list",
        rider_name="Leo",
        rider_gender="boy",
        companion_type="father",
        trait="curious",
    ),
    StoryParams(
        cart="wagon",
        noise="bell",
        cargo="bread",
        fix="hug_toy",
        rider_name="Ava",
        rider_gender="girl",
        companion_type="mother",
        trait="cheerful",
    ),
    StoryParams(
        cart="shopping_cart",
        noise="drum",
        cargo="glass_bottle",
        fix="hold_list",
        rider_name="Finn",
        rider_gender="boy",
        companion_type="father",
        trait="bouncy",
    ),
]


def explain_rejection(cart: CartKind, noise: NoiseKind, cargo: CargoKind, fix: Optional[FixKind] = None) -> str:
    if not sensible_noise(noise):
        return (
            f"(No story: {noise.id} is too unreasonable for this gentle fable. "
            f"Pick a sound like bell or drum that can be corrected without the story becoming harsh.)"
        )
    if not cargo_fits(cart, cargo):
        return (
            f"(No story: {cargo.phrase} does not belong in a {cart.label} here, so the danger would feel fake. "
            f"Choose cargo that plausibly rides in that rolling carrier.)"
        )
    if fix is not None and not sensible_fix(fix):
        return (
            f"(No story: the fix '{fix.id}' is not sensible enough. The ending must show a calm, safer habit.)"
        )
    return "(No story: this combination does not make a reasonable mall fable.)"


ASP_RULES = r"""
sensible_noise(N) :- noise(N), noise_sense(N, S), sense_min(M), S >= M.
sensible_fix(F)   :- fix(F), fix_sense(F, S), sense_min(M), S >= M.

cargo_fits(Cart, Cargo) :- cart(Cart), cargo(Cargo),
                           cart_accepts(Cart, Cargo), cargo_for(Cargo, Cart).

valid(theme_mall, Cart, Noise, Cargo) :- cart(Cart), noise(Noise), cargo(Cargo),
                                         sensible_noise(Noise),
                                         cargo_fits(Cart, Cargo),
                                         sensible_fix(_).

fragile_risk :- chosen_cargo(C), fragile(C), chosen_noise(N), noise_disturbance(N, D), D >= 1.
annoys_people :- chosen_noise(N), noise_disturbance(N, D), D >= 1.
near_miss :- annoys_people.
near_miss :- fragile_risk.

ending(calm) :- chosen_fix(F), sensible_fix(F).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for cart_id, cart in CARTS.items():
        lines.append(asp.fact("cart", cart_id))
        for cargo_id in sorted(cart.suitable_cargo):
            lines.append(asp.fact("cart_accepts", cart_id, cargo_id))
    for noise_id, noise in NOISES.items():
        lines.append(asp.fact("noise", noise_id))
        lines.append(asp.fact("noise_sense", noise_id, noise.sense))
        lines.append(asp.fact("noise_disturbance", noise_id, noise.disturbance))
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        if cargo.fragile:
            lines.append(asp.fact("fragile", cargo_id))
        for cart_id in sorted(cargo.suitable_for):
            lines.append(asp.fact("cargo_for", cargo_id, cart_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_sense", fix_id, fix.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a fable in a shopping mall about a noisy passenger learning a calmer way."
    )
    ap.add_argument("--cart", choices=sorted(CARTS))
    ap.add_argument("--noise", choices=sorted(NOISES))
    ap.add_argument("--cargo", choices=sorted(CARGO))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.cart and args.noise and args.cargo:
        cart = CARTS[args.cart]
        noise = NOISES[args.noise]
        cargo = CARGO[args.cargo]
        fix = FIXES[args.fix] if args.fix else None
        if not sensible_noise(noise) or not cargo_fits(cart, cargo) or (fix is not None and not sensible_fix(fix)):
            raise StoryError(explain_rejection(cart, noise, cargo, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.cart is None or combo[1] == args.cart)
        and (args.noise is None or combo[2] == args.noise)
        and (args.cargo is None or combo[3] == args.cargo)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    _, cart_id, noise_id, cargo_id = rng.choice(sorted(combos))
    fix_choices = [fix_id for fix_id, fix in FIXES.items() if sensible_fix(fix)]
    if args.fix is not None:
        if args.fix not in FIXES or not sensible_fix(FIXES[args.fix]):
            raise StoryError(f"(No story: fix '{args.fix}' is not a sensible calm ending.)")
        fix_id = args.fix
    else:
        fix_id = rng.choice(sorted(fix_choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    rider_name = args.name or rng.choice(name_pool)
    companion_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        cart=cart_id,
        noise=noise_id,
        cargo=cargo_id,
        fix=fix_id,
        rider_name=rider_name,
        rider_gender=gender,
        companion_type=companion_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cart not in CARTS:
        raise StoryError(f"(Unknown cart: {params.cart})")
    if params.noise not in NOISES:
        raise StoryError(f"(Unknown noise: {params.noise})")
    if params.cargo not in CARGO:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    cart = CARTS[params.cart]
    noise = NOISES[params.noise]
    cargo = CARGO[params.cargo]
    fix = FIXES[params.fix]

    if not sensible_noise(noise):
        raise StoryError(explain_rejection(cart, noise, cargo, fix))
    if not sensible_fix(fix):
        raise StoryError(explain_rejection(cart, noise, cargo, fix))
    if not cargo_fits(cart, cargo):
        raise StoryError(explain_rejection(cart, noise, cargo, fix))

    world = tell(
        rider_name=params.rider_name,
        rider_gender=params.rider_gender,
        companion_type=params.companion_type,
        companion_name="Parent",
        cart=cart,
        noise=noise,
        cargo=cargo,
        fix=fix,
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
        print(asp_program("", "#show valid/4.\n#show sensible_noise/1.\n#show sensible_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, cart, noise, cargo) combos:\n")
        for theme, cart, noise, cargo in combos:
            print(f"  {theme:10} {cart:14} {noise:8} {cargo}")
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
            header = f"### {p.rider_name}: {p.cart}, {p.noise}, {p.cargo}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
