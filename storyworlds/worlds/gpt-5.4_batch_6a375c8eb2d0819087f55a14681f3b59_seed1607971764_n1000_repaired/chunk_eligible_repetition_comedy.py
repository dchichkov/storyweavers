#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chunk_eligible_repetition_comedy.py
==============================================================

A standalone story world for a small comedy domain built around a repeated
misunderstanding of the word "eligible".

Premise
-------
A child reaches a tasting table where a sign promises one free snack chunk for
each eligible token. The child does not understand "eligible" and keeps offering
the wrong little objects with perfect confidence. A patient helper repeats the
same correction, the parent joins the search, and the story resolves when the
right proof turns up -- or, at a place with a hand-stamp policy, when a helper
kindly checks the child's stamp instead.

The comedy comes from repetition, but the repetitions are state-driven:
confusion, amusement, queue pressure, searching, proof, and the final lesson all
live in the world model.

Run it
------
    python storyworlds/worlds/gpt-5.4/chunk_eligible_repetition_comedy.py
    python storyworlds/worlds/gpt-5.4/chunk_eligible_repetition_comedy.py --place fair --proof none
    python storyworlds/worlds/gpt-5.4/chunk_eligible_repetition_comedy.py --place bakery --proof none
    python storyworlds/worlds/gpt-5.4/chunk_eligible_repetition_comedy.py --all
    python storyworlds/worlds/gpt-5.4/chunk_eligible_repetition_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/chunk_eligible_repetition_comedy.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REPEAT_LIMIT = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    sign_text: str
    helper_role: str
    token_kind: str
    snacks: set[str] = field(default_factory=set)
    allows_reissue: bool = False
    reissue_text: str = ""
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
class Snack:
    id: str
    label: str
    phrase: str
    tray_text: str
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
class Token:
    id: str
    label: str
    phrase: str
    accepted_at: set[str] = field(default_factory=set)
    flat: bool = True
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
class Prop:
    id: str
    label: str
    phrase: str
    ticket_like: bool = False
    flat: bool = True
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
class ProofSpot:
    id: str
    label: str
    phrase: str
    has_token: bool = False
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


def _r_wrong_offer(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    parent = world.get("parent")
    if child.meters["wrong_offer"] <= child.meters["wrong_offer_resolved"]:
        return []
    sig = ("wrong_offer", int(child.meters["wrong_offer"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["confusion"] += 1
    helper.memes["amusement"] += 1
    helper.memes["patience"] += 1
    world.get("line").meters["delay"] += 1
    if child.meters["wrong_offer"] >= REPEAT_LIMIT:
        parent.memes["searching"] += 1
    return []


def _r_found_token(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.meters["proof"] < THRESHOLD:
        return []
    sig = ("proof",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["learning"] += 1
    helper.memes["kindness"] += 1
    return []


def _r_sample(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["sample"] < THRESHOLD:
        return []
    sig = ("sample",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["joy"] += 1
    child.meters["crumbs"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wrong_offer", tag="social", apply=_r_wrong_offer),
    Rule(name="proof", tag="social", apply=_r_found_token),
    Rule(name="sample", tag="physical", apply=_r_sample),
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
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "bakery": Place(
        id="bakery",
        label="the bakery counter",
        sign_text='A little sign said, "Each eligible bakery token gets one cake chunk."',
        helper_role="baker",
        token_kind="bakery_token",
        snacks={"cake", "brownie"},
        allows_reissue=False,
        reissue_text="",
        tags={"bakery", "token"},
    ),
    "fair": Place(
        id="fair",
        label="the school fair table",
        sign_text='A bright sign said, "Each eligible fair ticket gets one fudge chunk."',
        helper_role="ticket lady",
        token_kind="fair_ticket",
        snacks={"fudge", "apple"},
        allows_reissue=True,
        reissue_text="At this table, a blue hand stamp could stand in for a lost ticket.",
        tags={"fair", "ticket", "stamp"},
    ),
    "market": Place(
        id="market",
        label="the Saturday market stall",
        sign_text='A chalkboard said, "Each eligible sample chip gets one cheese chunk."',
        helper_role="seller",
        token_kind="sample_chip",
        snacks={"cheese", "melon"},
        allows_reissue=False,
        reissue_text="",
        tags={"market", "chip"},
    ),
}

SNACKS = {
    "cake": Snack(
        id="cake",
        label="cake chunk",
        phrase="a soft cake chunk",
        tray_text="little squares of cake sat in neat rows",
        tags={"cake"},
    ),
    "brownie": Snack(
        id="brownie",
        label="brownie chunk",
        phrase="a fudgy brownie chunk",
        tray_text="brownie bites shone with sticky crumbs",
        tags={"brownie"},
    ),
    "fudge": Snack(
        id="fudge",
        label="fudge chunk",
        phrase="a glossy fudge chunk",
        tray_text="small dark squares of fudge waited on wax paper",
        tags={"fudge"},
    ),
    "apple": Snack(
        id="apple",
        label="apple chunk",
        phrase="a crisp apple chunk",
        tray_text="bright apple cubes sparkled in a bowl",
        tags={"apple"},
    ),
    "cheese": Snack(
        id="cheese",
        label="cheese chunk",
        phrase="a pale cheese chunk",
        tray_text="tiny cheese cubes sat beside toothpicks",
        tags={"cheese"},
    ),
    "melon": Snack(
        id="melon",
        label="melon chunk",
        phrase="a cool melon chunk",
        tray_text="melon cubes glowed like little lanterns",
        tags={"melon"},
    ),
}

TOKENS = {
    "bakery_token": Token(
        id="bakery_token",
        label="bakery token",
        phrase="the small pink bakery token",
        accepted_at={"bakery"},
        flat=True,
        tags={"token"},
    ),
    "fair_ticket": Token(
        id="fair_ticket",
        label="fair ticket",
        phrase="the striped fair ticket",
        accepted_at={"fair"},
        flat=True,
        tags={"ticket"},
    ),
    "sample_chip": Token(
        id="sample_chip",
        label="sample chip",
        phrase="the round sample chip",
        accepted_at={"market"},
        flat=True,
        tags={"chip"},
    ),
}

PROPS = {
    "sticker": Prop(
        id="sticker",
        label="sticker",
        phrase="a shiny star sticker",
        ticket_like=True,
        flat=True,
        tags={"sticker"},
    ),
    "drawing": Prop(
        id="drawing",
        label="drawing",
        phrase="a folded crayon drawing",
        ticket_like=True,
        flat=True,
        tags={"drawing"},
    ),
    "receipt": Prop(
        id="receipt",
        label="receipt",
        phrase="a crinkly little receipt",
        ticket_like=True,
        flat=True,
        tags={"receipt"},
    ),
    "leaf": Prop(
        id="leaf",
        label="leaf",
        phrase="a very serious leaf",
        ticket_like=False,
        flat=True,
        tags={"leaf"},
    ),
    "button": Prop(
        id="button",
        label="button",
        phrase="a loose blue button",
        ticket_like=False,
        flat=False,
        tags={"button"},
    ),
    "bandage": Prop(
        id="bandage",
        label="bandage",
        phrase="a clean little bandage wrapper",
        ticket_like=True,
        flat=True,
        tags={"bandage"},
    ),
}

PROOF_SPOTS = {
    "pocket": ProofSpot(
        id="pocket",
        label="pocket",
        phrase="in the tiny pocket of the child's overalls",
        has_token=True,
        tags={"pocket"},
    ),
    "hat": ProofSpot(
        id="hat",
        label="hat",
        phrase="tucked inside the child's floppy hat band",
        has_token=True,
        tags={"hat"},
    ),
    "shoe": ProofSpot(
        id="shoe",
        label="shoe",
        phrase="under the child's heel inside one shoe",
        has_token=True,
        tags={"shoe"},
    ),
    "none": ProofSpot(
        id="none",
        label="nowhere handy",
        phrase="nowhere they could find",
        has_token=False,
        tags={"lost"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ella", "Ava", "Lucy"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Theo", "Finn", "Jack"]
TRAITS = ["eager", "bouncy", "curious", "hopeful", "chatty", "dramatic"]


def snack_served(place_id: str, snack_id: str) -> bool:
    return snack_id in PLACES[place_id].snacks


def token_accepted(place_id: str, token_id: str) -> bool:
    return place_id in TOKENS[token_id].accepted_at


def proof_possible(place_id: str, proof_id: str) -> bool:
    place = PLACES[place_id]
    spot = PROOF_SPOTS[proof_id]
    return spot.has_token or place.allows_reissue


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for snack_id in sorted(PLACES[place_id].snacks):
            for token_id in TOKENS:
                if not token_accepted(place_id, token_id):
                    continue
                for proof_id in PROOF_SPOTS:
                    if proof_possible(place_id, proof_id):
                        combos.append((place_id, snack_id, token_id, proof_id))
    return combos


@dataclass
class StoryParams:
    place: str
    snack: str
    token: str
    proof: str
    prop1: str
    prop2: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
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


def explain_rejection(place_id: str, snack_id: str, token_id: str, proof_id: str) -> str:
    if place_id not in PLACES:
        return "(No story: that place is unknown.)"
    if snack_id not in SNACKS:
        return "(No story: that snack is unknown.)"
    if token_id not in TOKENS:
        return "(No story: that token is unknown.)"
    if proof_id not in PROOF_SPOTS:
        return "(No story: that proof location is unknown.)"
    if not snack_served(place_id, snack_id):
        return (f"(No story: {PLACES[place_id].label} does not serve {SNACKS[snack_id].label}. "
                f"Pick one of {', '.join(sorted(PLACES[place_id].snacks))}.)")
    if not token_accepted(place_id, token_id):
        return (f"(No story: {TOKENS[token_id].label} is not accepted at {PLACES[place_id].label}. "
                f"An eligible token has to match the place.)")
    if not proof_possible(place_id, proof_id):
        return (f"(No story: if the proof is lost at {PLACES[place_id].label}, there is no "
                f"reissue or stamp policy, so the child cannot honestly receive a sample.)")
    return "(No story: that combination is unreasonable.)"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    spot = PROOF_SPOTS[params.proof]
    return "found" if spot.has_token else ("reissued" if place.allows_reissue else "stuck")


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    place = sim.facts["place"]
    spot = sim.facts["proof_spot"]
    child.meters["wrong_offer"] += 2
    propagate(sim, narrate=False)
    found = spot.has_token
    reissued = (not found) and place.allows_reissue
    return {
        "found": found,
        "reissued": reissued,
        "delay": sim.get("line").meters["delay"],
    }


def introduce(world: World, child: Entity, parent: Entity, place: Place, snack: Snack) -> None:
    trait = child.attrs.get("trait", "")
    world.say(
        f"One busy afternoon, {child.id} skipped beside {child.pronoun('possessive')} "
        f"{parent.label_word} to {place.label}. {snack.tray_text}, and {child.id} stopped so "
        f"fast that {child.pronoun('possessive')} shoes squeaked."
    )
    world.say(
        f"{child.id} was a {trait} little {child.type} who could smell a treat from half a room away."
    )


def spot_sign(world: World, child: Entity, place: Place, snack: Snack) -> None:
    child.memes["hunger"] += 1
    world.say(
        f"There, right beside the tray of {snack.label}, {place.sign_text}"
    )
    world.say(
        f'"I want that chunk," {child.id} whispered, already leaning in as if the tray might drift away.'
    )


def misread(world: World, child: Entity, parent: Entity, place: Place) -> None:
    pred = predict_outcome(world)
    world.facts["predicted_delay"] = pred["delay"]
    child.memes["confidence"] += 1
    world.say(
        f'"Eligible must mean tiny and important," {child.id} decided. '
        f'{parent.label_word.capitalize()} opened {parent.pronoun("possessive")} mouth to explain, '
        f'but {child.id} was already patting every pocket and fold {child.pronoun()} had.'
    )


def wrong_offer(world: World, child: Entity, helper: Entity, prop: Prop, turn: int) -> None:
    child.meters["wrong_offer"] += 1
    propagate(world, narrate=False)
    child.meters["wrong_offer_resolved"] = child.meters["wrong_offer"]
    if turn == 1:
        opener = f"First {child.id} proudly held up {prop.phrase}."
    else:
        opener = f"Then, with even more confidence, {child.id} produced {prop.phrase}."
    world.say(opener)
    world.say(
        f'"Is this eligible?" {child.id} asked.'
    )
    if prop.ticket_like:
        world.say(
            f'The {helper.label} smiled and said, "That is a fine {prop.label}, but it is not the right token."'
        )
    else:
        world.say(
            f'The {helper.label} blinked once and said, "That is not eligible, and it is also not even pretending to be a token."'
        )
    if world.get("line").meters["delay"] >= THRESHOLD:
        world.say("A little laugh wiggled through the line behind them.")


def parent_search(world: World, child: Entity, parent: Entity, spot: ProofSpot, token: Token) -> None:
    parent.memes["searching"] += 1
    if spot.has_token:
        world.say(
            f"By now {child.id}'s {parent.label_word} was searching too -- pockets, sleeves, hat, everything. "
            f'At last {parent.pronoun().capitalize()} found {token.phrase} {spot.phrase}.'
        )
    else:
        world.say(
            f"By now {child.id}'s {parent.label_word} had checked pockets, sleeves, and shoes. "
            f"The real token was {spot.phrase}."
        )


def reissue_or_find(world: World, child: Entity, helper: Entity, place: Place, token: Token, spot: ProofSpot) -> None:
    if spot.has_token:
        child.meters["proof"] += 1
        propagate(world, narrate=False)
        world.say(
            f'"Here it is!" {child.id} cried. This time the {helper.label} nodded. '
            f'"Yes," {helper.pronoun()} said, "that one is eligible."'
        )
        world.facts["proof_method"] = "token"
    else:
        child.meters["proof"] += 1
        propagate(world, narrate=False)
        world.say(
            f'The {helper.label} looked at {child.id}\'s blue hand stamp and remembered the rule for this table. '
            f'"A lost ticket is sad," {helper.pronoun()} said, "but that stamp still makes you eligible."'
        )
        world.facts["proof_method"] = "stamp"
        world.facts["reissue_text"] = place.reissue_text


def serve(world: World, child: Entity, helper: Entity, snack: Snack) -> None:
    child.meters["sample"] += 1
    propagate(world, narrate=False)
    world.say(
        f'The {helper.label} set {snack.phrase} on a napkin and handed it over with a tiny bow.'
    )
    world.say(
        f"{child.id} took one bite, closed {child.pronoun('possessive')} eyes, and made the sort of happy noise that was almost too large for one mouth."
    )


def lesson(world: World, child: Entity, parent: Entity, place: Place) -> None:
    child.memes["embarrassment"] += 1
    child.memes["pride"] += 1
    method = world.facts.get("proof_method", "token")
    if method == "stamp":
        middle = "the right proof can be a real ticket or the hand stamp the fair uses"
    else:
        middle = f"an eligible token is the one that belongs at {place.label}, not just any small flat thing"
    world.say(
        f'{parent.label_word.capitalize()} crouched beside {child.id} and whispered, '
        f'"Now do you know what eligible means?"'
    )
    world.say(
        f'{child.id} nodded hard enough to wobble. "It means {middle}," {child.pronoun()} said.'
    )


def ending(world: World, child: Entity, helper: Entity, snack: Snack) -> None:
    repeat = world.get("child").meters["wrong_offer"]
    if repeat >= 2:
        world.say(
            f"On the way home, {child.id} kept patting the safe proof in {child.pronoun('possessive')} hand and announcing to nobody in particular, "
            f'"This chunk was eligible. The leaf was not. The sticker was not. The drawing was definitely not."'
        )
    else:
        world.say(
            f"On the way home, {child.id} walked as carefully as if one more {snack.label} might appear for excellent behavior."
        )
    world.say(
        f"Every few steps the {helper.label}'s tiny bow popped back into {child.pronoun('possessive')} mind, and {child.pronoun()} laughed all over again."
    )


def tell(
    place: Place,
    snack: Snack,
    token: Token,
    spot: ProofSpot,
    prop1: Prop,
    prop2: Prop,
    child_name: str = "Mia",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "eager",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        label=place.helper_role,
        role="helper",
    ))
    world.add(Entity(
        id="line",
        kind="thing",
        type="line",
        label="the line",
    ))
    world.facts.update(
        place=place,
        snack=snack,
        token=token,
        proof_spot=spot,
        props=[prop1, prop2],
    )

    child.meters["wrong_offer"] = 0.0
    child.meters["wrong_offer_resolved"] = 0.0
    child.meters["proof"] = 0.0
    child.meters["sample"] = 0.0
    child.meters["crumbs"] = 0.0
    child.memes["confusion"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["learning"] = 0.0
    child.memes["embarrassment"] = 0.0
    helper.memes["amusement"] = 0.0
    helper.memes["kindness"] = 0.0
    helper.memes["patience"] = 0.0
    parent.memes["searching"] = 0.0
    world.get("line").meters["delay"] = 0.0

    introduce(world, child, parent, place, snack)
    spot_sign(world, child, place, snack)

    world.para()
    misread(world, child, parent, place)
    wrong_offer(world, child, helper, prop1, 1)
    wrong_offer(world, child, helper, prop2, 2)

    world.para()
    parent_search(world, child, parent, spot, token)
    reissue_or_find(world, child, helper, place, token, spot)
    serve(world, child, helper, snack)
    lesson(world, child, parent, place)

    world.para()
    ending(world, child, helper, snack)

    world.facts.update(
        child=child,
        parent=parent,
        helper=helper,
        outcome="served" if child.meters["sample"] >= THRESHOLD else "stuck",
        repeats=int(child.meters["wrong_offer"]),
        line_delay=int(world.get("line").meters["delay"]),
        proof_found=spot.has_token,
        sample_given=child.meters["sample"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "eligible": [
        (
            "What does eligible mean?",
            "Eligible means something fits the rule and is allowed to count. It is not the same as being small, cute, or nearby."
        )
    ],
    "token": [
        (
            "What is a token?",
            "A token is a small thing that stands for permission, payment, or a turn. People use tokens so everyone follows the same rule."
        )
    ],
    "ticket": [
        (
            "What does a ticket do?",
            "A ticket shows that your turn or entry has been counted already. It helps a helper know who should get what."
        )
    ],
    "stamp": [
        (
            "Why might a hand stamp count like a ticket?",
            "A hand stamp can prove that someone already checked you in. It works as a backup sign when a paper ticket gets lost."
        )
    ],
    "cake": [
        (
            "What is a cake chunk?",
            "A cake chunk is a small piece of cake cut from a bigger cake. It is just enough for a little taste."
        )
    ],
    "fudge": [
        (
            "What is fudge?",
            "Fudge is a sweet, soft candy made in little squares. A fudge chunk is a tiny piece for tasting."
        )
    ],
    "cheese": [
        (
            "Why do stores give tiny cheese samples?",
            "Tiny samples let people taste the cheese before choosing what to buy. A small chunk is enough to tell if they like it."
        )
    ],
}
KNOWLEDGE_ORDER = ["eligible", "token", "ticket", "stamp", "cake", "fudge", "cheese"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    snack = f["snack"]
    return [
        f'Write a short comedy story for a 3-to-5-year-old that uses the words "chunk" and "eligible".',
        f"Tell a repetitive, funny story where {child.id} wants a {snack.label} at {place.label} and keeps asking, \"Is this eligible?\" with the wrong objects first.",
        f"Write a gentle story about a child misunderstanding a rule, a patient adult helper, and a happy ending with a snack sample.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper = f["helper"]
    place = f["place"]
    snack = f["snack"]
    token = f["token"]
    prop1, prop2 = f["props"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who wanted a {snack.label}, {child.id}'s {parent.label_word}, and the {helper.label} at {place.label}."
        ),
        (
            f"Why did {child.id} keep asking if things were eligible?",
            f"{child.id} misunderstood the sign and thought eligible meant any little object that seemed important. Because of that mistake, {child.pronoun()} kept offering the wrong things with complete confidence."
        ),
        (
            f"What were the first two wrong things {child.id} offered?",
            f"First {child.id} offered {prop1.phrase}, and then {prop2.phrase}. Those objects were not the right proof for the table, even if one of them looked a bit ticket-like."
        ),
    ]
    if f["proof_found"]:
        qa.append(
            (
                f"How did they solve the problem?",
                f"{parent.label_word.capitalize()} searched carefully and found {token.phrase}. Once the right token appeared, the {helper.label} could honestly say it was eligible and hand over the sample."
            )
        )
    else:
        qa.append(
            (
                f"How did {helper.label} still let {child.id} have the sample?",
                f"The real ticket was lost, but the fair used a blue hand stamp as backup proof. The {helper.label} checked that stamp and used the fair's rule to decide that {child.id} was still eligible."
            )
        )
    qa.append(
        (
            f"What did {child.id} learn at the end?",
            f"{child.id} learned that eligible means fitting the rule for that table, not just being small or flat. The repeated mistakes made the meaning clearer by the end."
        )
    )
    qa.append(
        (
            f"Why was the story funny?",
            f"It was funny because {child.id} asked the same question again and again with different objects, and each wrong try grew sillier. The helper stayed calm, so the repetition felt playful instead of scary."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"eligible"}
    place = world.facts["place"]
    snack = world.facts["snack"]
    token = world.facts["token"]
    if "token" in token.id or place.id == "bakery":
        tags.add("token")
    if "ticket" in token.id or place.id == "fair":
        tags.add("ticket")
    if place.allows_reissue:
        tags.add("stamp")
    if snack.id == "cake":
        tags.add("cake")
    if snack.id == "fudge":
        tags.add("fudge")
    if snack.id == "cheese":
        tags.add("cheese")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
serves(P,S) :- place(P), snack(S), served_at(P,S).
eligible_token(P,T) :- place(P), token(T), accepted_at(T,P).
proof_possible(P,Spot) :- proof_spot(Spot), has_token(Spot).
proof_possible(P,Spot) :- proof_spot(Spot), allows_reissue(P), not has_token(Spot).

valid(P,S,T,Spot) :- serves(P,S), eligible_token(P,T), proof_possible(P,Spot).

found(Spot) :- has_token(Spot).
reissued(P,Spot) :- valid(P,_,_,Spot), allows_reissue(P), not has_token(Spot).

outcome(found) :- chosen_place(P), chosen_proof(Spot), valid(P,_,_,Spot), found(Spot).
outcome(reissued) :- chosen_place(P), chosen_proof(Spot), valid(P,_,_,Spot), reissued(P,Spot).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.allows_reissue:
            lines.append(asp.fact("allows_reissue", pid))
        for snack_id in sorted(place.snacks):
            lines.append(asp.fact("served_at", pid, snack_id))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
    for tid, token in TOKENS.items():
        lines.append(asp.fact("token", tid))
        for pid in sorted(token.accepted_at):
            lines.append(asp.fact("accepted_at", tid, pid))
    for spot_id, spot in PROOF_SPOTS.items():
        lines.append(asp.fact("proof_spot", spot_id))
        if spot.has_token:
            lines.append(asp.fact("has_token", spot_id))
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
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_proof", params.proof),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        place="bakery",
        snack="cake",
        token="bakery_token",
        proof="pocket",
        prop1="sticker",
        prop2="drawing",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        trait="eager",
    ),
    StoryParams(
        place="fair",
        snack="fudge",
        token="fair_ticket",
        proof="none",
        prop1="receipt",
        prop2="leaf",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        trait="dramatic",
    ),
    StoryParams(
        place="market",
        snack="cheese",
        token="sample_chip",
        proof="shoe",
        prop1="bandage",
        prop2="button",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="chatty",
    ),
    StoryParams(
        place="bakery",
        snack="brownie",
        token="bakery_token",
        proof="hat",
        prop1="drawing",
        prop2="receipt",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        trait="hopeful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child misunderstands 'eligible' at a tasting table."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--proof", choices=PROOF_SPOTS)
    ap.add_argument("--prop1", choices=PROPS)
    ap.add_argument("--prop2", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.snack and args.token and args.proof:
        if (args.place, args.snack, args.token, args.proof) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.snack, args.token, args.proof))
    elif args.place and args.snack and not snack_served(args.place, args.snack):
        token_id = args.token if args.token else PLACES[args.place].token_kind
        proof_id = args.proof if args.proof else "pocket"
        raise StoryError(explain_rejection(args.place, args.snack, token_id, proof_id))
    elif args.place and args.token and not token_accepted(args.place, args.token):
        snack_id = args.snack if args.snack else sorted(PLACES[args.place].snacks)[0]
        proof_id = args.proof if args.proof else "pocket"
        raise StoryError(explain_rejection(args.place, snack_id, args.token, proof_id))
    elif args.place and args.proof and not proof_possible(args.place, args.proof):
        snack_id = args.snack if args.snack else sorted(PLACES[args.place].snacks)[0]
        token_id = args.token if args.token else PLACES[args.place].token_kind
        raise StoryError(explain_rejection(args.place, snack_id, token_id, args.proof))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.snack is None or combo[1] == args.snack)
        and (args.token is None or combo[2] == args.token)
        and (args.proof is None or combo[3] == args.proof)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, snack_id, token_id, proof_id = rng.choice(sorted(combos))

    prop_choices = sorted(PROPS.keys())
    if args.prop1 and args.prop2 and args.prop1 == args.prop2:
        raise StoryError("(No story: prop1 and prop2 should be different so the repetition can escalate.)")
    if args.prop1 and args.prop1 == token_id:
        raise StoryError("(No story: the first wrong object cannot be the real token.)")
    if args.prop2 and args.prop2 == token_id:
        raise StoryError("(No story: the second wrong object cannot be the real token.)")

    if args.prop1 and args.prop2:
        prop1 = args.prop1
        prop2 = args.prop2
    elif args.prop1:
        others = [p for p in prop_choices if p != args.prop1]
        prop1 = args.prop1
        prop2 = rng.choice(others)
    elif args.prop2:
        others = [p for p in prop_choices if p != args.prop2]
        prop2 = args.prop2
        prop1 = rng.choice(others)
    else:
        prop1, prop2 = rng.sample(prop_choices, 2)

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        snack=snack_id,
        token=token_id,
        proof=proof_id,
        prop1=prop1,
        prop2=prop2,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("(No story: unknown place.)")
    if params.snack not in SNACKS:
        raise StoryError("(No story: unknown snack.)")
    if params.token not in TOKENS:
        raise StoryError("(No story: unknown token.)")
    if params.proof not in PROOF_SPOTS:
        raise StoryError("(No story: unknown proof location.)")
    if params.prop1 not in PROPS or params.prop2 not in PROPS:
        raise StoryError("(No story: unknown repeated prop.)")
    if params.prop1 == params.prop2:
        raise StoryError("(No story: repetition needs two different wrong objects.)")
    if (params.place, params.snack, params.token, params.proof) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.snack, params.token, params.proof))

    world = tell(
        place=PLACES[params.place],
        snack=SNACKS[params.snack],
        token=TOKENS[params.token],
        spot=PROOF_SPOTS[params.proof],
        prop1=PROPS[params.prop1],
        prop2=PROPS[params.prop2],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
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
        print(f"{len(combos)} compatible (place, snack, token, proof) combos:\n")
        for place_id, snack_id, token_id, proof_id in combos:
            print(f"  {place_id:8} {snack_id:8} {token_id:13} {proof_id}")
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
            header = f"### {p.child_name}: {p.snack} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
