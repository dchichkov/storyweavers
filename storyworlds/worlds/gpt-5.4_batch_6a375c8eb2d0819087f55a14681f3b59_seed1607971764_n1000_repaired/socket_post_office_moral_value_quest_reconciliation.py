#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/socket_post_office_moral_value_quest_reconciliation.py
=================================================================================

A standalone story world about a child who goes on a small fairy-tale quest to
the post office to mend a quarrel before the last mail coach leaves.

The seed asks for:
- the word "socket"
- a post office setting
- moral value
- quest
- reconciliation
- a fairy-tale style

This world models a child carrying an apology parcel through a little post
office full of brass boxes, ticking clocks, and kind workers. A practical
problem arises while the child tries to send the parcel before dusk. The child
must choose a sensible way to solve it, and the ending proves what changed:
truth and patience bring reconciliation, even if the parcel arrives a little
late.

Run it
------
    python storyworlds/worlds/gpt-5.4/socket_post_office_moral_value_quest_reconciliation.py
    python storyworlds/worlds/gpt-5.4/socket_post_office_moral_value_quest_reconciliation.py --obstacle near_socket
    python storyworlds/worlds/gpt-5.4/socket_post_office_moral_value_quest_reconciliation.py --response metal_ruler
    python storyworlds/worlds/gpt-5.4/socket_post_office_moral_value_quest_reconciliation.py --all
    python storyworlds/worlds/gpt-5.4/socket_post_office_moral_value_quest_reconciliation.py --qa --json
    python storyworlds/worlds/gpt-5.4/socket_post_office_moral_value_quest_reconciliation.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "postmistress"}
        male = {"boy", "father", "man", "postmaster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "postmistress": "postmistress",
            "postmaster": "postmaster",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class Quarrel:
    id: str
    wrong: str
    token_reason: str
    lesson: str
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
class Token:
    id: str
    label: str
    phrase: str
    image: str
    material: str
    plural: bool = False
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
class Obstacle:
    id: str
    label: str
    trouble_type: str
    difficulty: int
    setup: str
    risk_text: str
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
class Response:
    id: str
    sense: int
    power: int
    handles: set[str]
    qa_text: str
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
class ClerkStyle:
    id: str
    title: str
    type: str
    manner: str
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


QUARRELS = {
    "harsh_words": Quarrel(
        id="harsh_words",
        wrong="spoke sharp words when the game went badly",
        token_reason="to show that gentle words could begin again",
        lesson="sharp words can wound, but honest kindness can mend",
        tags={"apology", "kindness"},
    ),
    "broken_promise": Quarrel(
        id="broken_promise",
        wrong="forgot a promise to meet by the gate after lessons",
        token_reason="to show that promises matter when they are kept at last",
        lesson="a promise should be carried carefully, like a letter with the right name on it",
        tags={"promise", "honesty"},
    ),
    "torn_drawing": Quarrel(
        id="torn_drawing",
        wrong="snatched a picture too quickly and tore one corner",
        token_reason="to show that care and truth are stronger than pride",
        lesson="when your hands make a hurt, your truth must help heal it",
        tags={"truth", "care"},
    ),
}

TOKENS = {
    "paper_star": Token(
        id="paper_star",
        label="paper star",
        phrase="a folded paper star",
        image="five neat points that caught the window light",
        material="paper",
        tags={"paper_star", "apology"},
    ),
    "honey_cookie": Token(
        id="honey_cookie",
        label="honey cookie",
        phrase="a honey cookie shaped like a moon",
        image="a little crescent glazed with sugar",
        material="food",
        tags={"cookie", "apology"},
    ),
    "blue_ribbon": Token(
        id="blue_ribbon",
        label="blue ribbon",
        phrase="a soft blue ribbon bookmark",
        image="a ribbon as blue as a twilight stream",
        material="cloth",
        tags={"ribbon", "apology"},
    ),
}

OBSTACLES = {
    "smudged_address": Obstacle(
        id="smudged_address",
        label="smudged address",
        trouble_type="paper",
        difficulty=1,
        setup="a drop from the hero's damp sleeve blurred the friend's name on the parcel label",
        risk_text="Without a clear name, the parcel might wander to the wrong door.",
        tags={"address", "post_office"},
    ),
    "missing_stamp": Obstacle(
        id="missing_stamp",
        label="missing stamp",
        trouble_type="postage",
        difficulty=1,
        setup="the hero counted the envelope corners twice and saw there was no stamp at all",
        risk_text="Without postage, the parcel could not ride with the evening mail coach.",
        tags={"stamp", "post_office"},
    ),
    "near_socket": Obstacle(
        id="near_socket",
        label="fallen tag by the socket",
        trouble_type="reach",
        difficulty=2,
        setup="the address tag slipped from the string and skated behind a sorting shelf, close to the brass wall socket where the big scale was plugged in",
        risk_text="The tag was too near the socket for hasty hands or shiny tools.",
        tags={"socket", "safety", "post_office"},
    ),
    "torn_wrap": Obstacle(
        id="torn_wrap",
        label="torn wrapping",
        trouble_type="wrap",
        difficulty=2,
        setup="the parcel paper caught on a corner of the counter and tore open like a sigh",
        risk_text="If the wrapping stayed torn, the peace gift might fall out on the road.",
        tags={"wrapping", "post_office"},
    ),
}

RESPONSES = {
    "ask_clerk": Response(
        id="ask_clerk",
        sense=3,
        power=3,
        handles={"paper", "postage", "reach", "wrap"},
        qa_text="asked the clerk for proper help",
        tags={"ask_help", "post_office"},
    ),
    "wait_queue": Response(
        id="wait_queue",
        sense=2,
        power=1,
        handles={"paper", "postage"},
        qa_text="waited patiently in line for the counter to open",
        tags={"patience", "post_office"},
    ),
    "twine_kit": Response(
        id="twine_kit",
        sense=2,
        power=1,
        handles={"wrap"},
        qa_text="used the wrapping table's twine and paper the right way",
        tags={"wrapping", "post_office"},
    ),
    "long_tongs": Response(
        id="long_tongs",
        sense=3,
        power=2,
        handles={"reach"},
        qa_text="used the clerk's long tongs to reach the tag safely",
        tags={"socket", "ask_help", "safety"},
    ),
    "metal_ruler": Response(
        id="metal_ruler",
        sense=1,
        power=1,
        handles={"reach"},
        qa_text="tried to fish the tag out with a metal ruler",
        tags={"socket", "unsafe"},
    ),
}

CLERKS = {
    "postmistress": ClerkStyle(
        id="postmistress",
        title="Mistress Rowan",
        type="postmistress",
        manner="with a voice as calm as warm tea",
    ),
    "postmaster": ClerkStyle(
        id="postmaster",
        title="Master Elm",
        type="postmaster",
        manner="with a beard that trembled when he smiled",
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Wren", "Nora", "Elsie"]
BOY_NAMES = ["Oren", "Tobin", "Finn", "Jory", "Silas", "Milo"]
FRIEND_GIRL_NAMES = ["Pip", "May", "Ivy", "Fern", "June", "Bess"]
FRIEND_BOY_NAMES = ["Pip", "Ash", "Benji", "Kit", "Rowan", "Hale"]
TRAITS = ["gentle", "earnest", "quick", "thoughtful", "brave", "restless"]


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
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_problem_pressure(world: World) -> list[str]:
    parcel = world.get("parcel")
    clock = world.get("clock")
    hero = world.get("hero")
    if parcel.meters["problem"] < THRESHOLD:
        return []
    sig = ("pressure",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clock.meters["risk"] += 1
    hero.memes["worry"] += 1
    return []


def _r_ask_help_relief(world: World) -> list[str]:
    hero = world.get("hero")
    parcel = world.get("parcel")
    if hero.memes["asked_help"] < THRESHOLD or parcel.meters["problem"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hope"] += 1
    return []


def _r_mail_and_peace(world: World) -> list[str]:
    parcel = world.get("parcel")
    friend = world.get("friend")
    hero = world.get("hero")
    if parcel.meters["mailed"] < THRESHOLD or friend.memes["softened"] >= THRESHOLD:
        return []
    sig = ("peace",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["softened"] += 1
    hero.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="problem_pressure", tag="physical", apply=_r_problem_pressure),
    Rule(name="ask_help_relief", tag="social", apply=_r_ask_help_relief),
    Rule(name="mail_and_peace", tag="social", apply=_r_mail_and_peace),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name or sig == (rule.name,) for sig in world.fired):
                pass
        if not changed:
            newly_fired = sum(1 for _ in [])
            if newly_fired:
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def obstacle_supported(response: Response, obstacle: Obstacle) -> bool:
    return obstacle.trouble_type in response.handles


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response_for(obstacle: Obstacle) -> Response:
    choices = [r for r in RESPONSES.values() if obstacle_supported(r, obstacle) and r.sense >= SENSE_MIN]
    if not choices:
        raise StoryError(f"(No sensible response can handle {obstacle.label}.)")
    return max(choices, key=lambda r: (r.sense, r.power, r.id))


def pressure_value(obstacle: Obstacle, delay: int) -> int:
    return obstacle.difficulty + delay


def catches_coach(response: Response, obstacle: Obstacle, delay: int) -> bool:
    return response.power >= pressure_value(obstacle, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for qid in QUARRELS:
        for tid in TOKENS:
            for oid, obstacle in OBSTACLES.items():
                if any(obstacle_supported(r, obstacle) and r.sense >= SENSE_MIN for r in RESPONSES.values()):
                    combos.append((qid, tid, oid))
    return combos


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_incompatible(obstacle: Obstacle, response: Response) -> str:
    return (
        f"(No story: response '{response.id}' does not properly handle "
        f"{obstacle.label}. Pick a response meant for {obstacle.trouble_type} trouble.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def response_text(response: Response, obstacle: Obstacle, clerk: Entity) -> str:
    if response.id == "ask_clerk":
        if obstacle.id == "smudged_address":
            return (
                f"{clerk.id} slid over a fresh label, copied the name in clear ink, "
                f"and pressed it smooth with a careful thumb"
            )
        if obstacle.id == "missing_stamp":
            return (
                f"{clerk.id} opened the stamp drawer, chose the right stamp, and showed "
                f"the hero where it belonged"
            )
        if obstacle.id == "near_socket":
            return (
                f"{clerk.id} unplugged the scale from the wall socket first, moved the shelf a finger-width, "
                f"and lifted the fallen tag out with a wooden grip"
            )
        return (
            f"{clerk.id} brought strong paper and twine, then wrapped the parcel snugly "
            f"so nothing could slip away"
        )
    if response.id == "wait_queue":
        if obstacle.id == "smudged_address":
            return "the hero waited patiently until the counter opened and then received a clean new label"
        return "the hero waited patiently until the counter opened and then bought the proper stamp"
    if response.id == "twine_kit":
        return "the hero carried the parcel to the wrapping table and used the public twine and paper the right way"
    if response.id == "long_tongs":
        return (
            f"{clerk.id} fetched the long tongs kept for fallen letters and drew the tag away from the socket without a spark"
        )
    if response.id == "metal_ruler":
        return "the hero reached with a metal ruler toward the tag near the socket"
    return "the problem was handled"


def introduce(world: World, hero: Entity, friend: Entity, quarrel: Quarrel, token: Token) -> None:
    hero.memes["guilt"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"Once, in a town where the lamps glowed early and the pigeons knew every roof, "
        f"{hero.id} and {friend.id} had been close companions. But that morning {hero.id} "
        f"{quarrel.wrong}, and the hurt between them felt larger than the market square."
    )
    world.say(
        f"By afternoon, {hero.id} had tucked {token.phrase} into a small parcel, hoping "
        f"{token.image} would help say what a shy heart could not."
    )


def quest_call(world: World, hero: Entity, clerk_style: ClerkStyle, quarrel: Quarrel) -> None:
    world.say(
        f"So {hero.id} set out on a little quest to the old post office, where brass boxes lined the walls "
        f"and the last mail coach left at dusk. {hero.pronoun().capitalize()} whispered the lesson already "
        f"stirring inside: {quarrel.lesson}."
    )
    world.say(
        f"Inside, a yellow sorting lamp hummed from a wall socket, and the clock above the pigeonholes "
        f"clicked toward evening like a tiny marching drum."
    )
    world.facts["clerk_style_id"] = clerk_style.id


def post_office_scene(world: World, hero: Entity, clerk: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"At the counter stood {clerk.id}, the {clerk.label_word}, {clerk.attrs['manner']}. "
        f"Before {hero.id} could send the parcel on its way, {obstacle.setup}"
    )
    world.say(obstacle.risk_text)


def hesitate(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"For one small moment, {hero.id} wanted to hide the trouble and pretend everything was fine. "
        f"But secrets made the parcel feel heavier in {hero.pronoun('possessive')} hands."
    )
    if obstacle.id == "near_socket":
        world.say(
            f"The brass wall socket gleamed nearby, and even {hero.id} could see that this was no place for a hurried grab."
        )


def face_problem(world: World, parcel: Entity) -> None:
    parcel.meters["problem"] += 1
    propagate(world, narrate=False)


def ask_for_help(world: World, hero: Entity, clerk: Entity) -> None:
    hero.memes["asked_help"] += 1
    hero.memes["honesty"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Please," {hero.id} said, lifting honest eyes to {clerk.id}, "I want to make this right."'
    )


def solve_problem(world: World, hero: Entity, clerk: Entity, parcel: Entity,
                  response: Response, obstacle: Obstacle) -> None:
    if response.id == "metal_ruler":
        raise StoryError(explain_response(response.id))
    parcel.meters["problem"] = 0.0
    parcel.meters["repaired"] += 1
    world.say(response_text(response, obstacle, clerk) + ".")
    hero.memes["hope"] += 1


def mail_parcel(world: World, parcel: Entity, hero: Entity, in_time: bool) -> None:
    parcel.meters["mailed"] += 1
    propagate(world, narrate=False)
    if in_time:
        world.say(
            f"The parcel was tied, stamped, and tucked into the evening bag just before the coachman's horn sang outside."
        )
    else:
        world.say(
            f"The evening bag had already been sealed, so the parcel was laid in the first basket for dawn, neat and ready for the morning round."
        )
    hero.memes["patience"] += 1


def reconciliation(world: World, hero: Entity, friend: Entity, quarrel: Quarrel,
                   token: Token, in_time: bool) -> None:
    world.para()
    if in_time:
        world.say(
            f"That very evening, {friend.id} opened the parcel by the window. Inside lay {token.phrase}, "
            f"and beneath it a note in {hero.id}'s careful hand: sorry, true, and brave."
        )
        world.say(
            f"{friend.id}'s face softened at once. Before the stars were high, {friend.pronoun()} came to the lane, "
            f"and the two friends stood together again."
        )
    else:
        world.say(
            f"At dawn the next day, the parcel reached {friend.id}. The little gift was still safe inside, "
            f"and the note told the truth without hiding behind excuses."
        )
        world.say(
            f"{friend.id} did not stay hurt forever. By breakfast light, {friend.pronoun()} knocked at the gate, "
            f"and the quarrel was smaller than the morning birds."
        )
    friend.memes["forgiveness"] += 1
    hero.memes["love"] += 1
    world.say(
        f'"I was wrong," {hero.id} said. "{quarrel.token_reason.capitalize()}." '
        f'"And I missed you," said {friend.id}.'
    )
    world.say(
        f"So they were reconciled, and {hero.id} remembered that truth and patience carry peace farther than pride ever can."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    quarrel: Quarrel,
    token: Token,
    obstacle: Obstacle,
    response: Response,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    friend_name: str = "Pip",
    friend_gender: str = "boy",
    clerk_style: ClerkStyle = CLERKS["postmistress"],
    trait: str = "gentle",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    clerk = world.add(Entity(
        id=clerk_style.title,
        kind="character",
        type=clerk_style.type,
        role="clerk",
        label="the clerk",
        attrs={"manner": clerk_style.manner},
    ))
    parcel = world.add(Entity(id="parcel", kind="thing", type="parcel", label="parcel"))
    world.add(Entity(id="clock", kind="thing", type="clock", label="clock"))
    world.add(Entity(id="socket", kind="thing", type="socket", label="wall socket"))

    world.facts.update(
        hero=hero,
        friend=friend,
        clerk=clerk,
        quarrel=quarrel,
        token=token,
        obstacle=obstacle,
        response=response,
        delay=delay,
    )

    introduce(world, hero, friend, quarrel, token)
    quest_call(world, hero, clerk_style, quarrel)

    world.para()
    post_office_scene(world, hero, clerk, obstacle)
    hesitate(world, hero, obstacle)
    face_problem(world, parcel)
    ask_for_help(world, hero, clerk)
    solve_problem(world, hero, clerk, parcel, response, obstacle)

    in_time = catches_coach(response, obstacle, delay)
    world.facts["outcome"] = "same_day" if in_time else "next_day"
    world.facts["pressure"] = pressure_value(obstacle, delay)
    world.facts["in_time"] = in_time

    world.para()
    mail_parcel(world, parcel, hero, in_time)
    reconciliation(world, hero, friend, quarrel, token, in_time)
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    quarrel: str
    token: str
    obstacle: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    clerk: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "socket": [(
        "What is a socket?",
        "A socket is a place in the wall where a plug goes to get electricity. Children should not poke fingers or metal things near it, and they should ask a grown-up for help."
    )],
    "post_office": [(
        "What does a post office do?",
        "A post office is a place where letters and parcels are weighed, stamped, sorted, and sent from one person to another. It helps messages travel safely."
    )],
    "stamp": [(
        "Why does a parcel need a stamp?",
        "A stamp shows that the sender has paid for the mail to travel. Without it, the post office cannot send the parcel on its journey."
    )],
    "address": [(
        "Why must an address be clear on a parcel?",
        "The address tells the post office where the parcel should go. If the name or place is smudged, the parcel can get lost or delayed."
    )],
    "apology": [(
        "What is an apology?",
        "An apology is when you truthfully say you were wrong and want to mend a hurt. A real apology tries to bring comfort, not excuses."
    )],
    "patience": [(
        "Why is patience helpful?",
        "Patience helps you do the right thing even when you want everything fixed at once. It keeps a small problem from growing bigger."
    )],
    "ask_help": [(
        "Why is asking for help brave?",
        "Asking for help is brave because it means telling the truth when something is hard. It often keeps people safe and helps problems get solved the right way."
    )],
}
KNOWLEDGE_ORDER = ["post_office", "socket", "stamp", "address", "apology", "patience", "ask_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    quarrel, token, obstacle = f["quarrel"], f["token"], f["obstacle"]
    outcome = f["outcome"]
    if outcome == "same_day":
        end = "the apology arrives that same evening and the friends are reconciled"
    else:
        end = "the apology arrives the next morning, and patience still leads to reconciliation"
    return [
        (
            f'Write a short fairy-tale story for a 3-to-5-year-old set in a post office. '
            f'Include the word "socket", a small quest, and a gentle moral about truth and patience.'
        ),
        (
            f"Tell a story where {hero.id} goes to mail {token.phrase} to {friend.id} after {hero.pronoun('subject')} "
            f"{quarrel.wrong}, but {obstacle.label} threatens the parcel before dusk."
        ),
        (
            f"Write a child-facing reconciliation story in which a clerk helps with a post-office problem, "
            f"and {end}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, clerk = f["hero"], f["friend"], f["clerk"]
    quarrel, token = f["quarrel"], f["token"]
    obstacle, response = f["obstacle"], f["response"]
    in_time = f["in_time"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who went on a little quest to the post office to make peace with {friend.id}. "
            f"The {clerk.label_word} also helped when the parcel ran into trouble."
        ),
        (
            f"Why did {hero.id} go to the post office?",
            f"{hero.id} wanted to send {token.phrase} and a truthful note after {hero.pronoun('subject')} {quarrel.wrong}. "
            f"The trip became a quest because {hero.pronoun('subject')} hoped to mend the friendship before the last mail coach left."
        ),
        (
            "What problem happened to the parcel?",
            f"The problem was {obstacle.label}. {obstacle.risk_text}"
        ),
        (
            f"How was the problem solved?",
            f"{hero.id} did not hide the mistake. {hero.pronoun().capitalize()} {response.qa_text}, which fixed the trouble the right way."
        ),
    ]
    if obstacle.id == "near_socket":
        qa.append((
            "Why did the story mention the socket?",
            f"The fallen tag had slipped close to a wall socket, so it was not safe to grab with shiny tools or quick hands. "
            f"That is why {hero.id} needed proper help instead of a risky shortcut."
        ))
    if in_time:
        qa.append((
            "Did the apology arrive in time?",
            f"Yes. The parcel went into the evening mail bag before the coach left, so {friend.id} read the note that same evening. "
            f"Because the apology arrived quickly and truthfully, the reconciliation happened before night was deep."
        ))
    else:
        qa.append((
            "Did the friends still make peace even though the parcel was late?",
            f"Yes. The parcel had to wait for the morning round, but the honest note and gift still reached {friend.id}. "
            f"The story shows that patience can still carry kindness where it needs to go."
        ))
    qa.append((
        "What was the moral of the story?",
        f"The story teaches that {quarrel.lesson}. It also shows that telling the truth and asking for help can mend a mistake better than pride can."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"post_office", "apology"}
    obstacle = world.facts["obstacle"]
    response = world.facts["response"]
    if obstacle.id == "near_socket":
        tags.add("socket")
        tags.add("ask_help")
    if obstacle.id == "missing_stamp":
        tags.add("stamp")
    if obstacle.id == "smudged_address":
        tags.add("address")
    if response.id in {"ask_clerk", "long_tongs"}:
        tags.add("ask_help")
    if world.facts["outcome"] == "next_day" or response.id == "wait_queue":
        tags.add("patience")
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
# Trace / CLI helpers
# ---------------------------------------------------------------------------
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
        lines.append(f"  {ent.id:16} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quarrel="harsh_words",
        token="paper_star",
        obstacle="near_socket",
        response="long_tongs",
        hero_name="Lina",
        hero_gender="girl",
        friend_name="Pip",
        friend_gender="boy",
        clerk="postmistress",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        quarrel="broken_promise",
        token="blue_ribbon",
        obstacle="missing_stamp",
        response="wait_queue",
        hero_name="Oren",
        hero_gender="boy",
        friend_name="May",
        friend_gender="girl",
        clerk="postmaster",
        trait="earnest",
        delay=1,
    ),
    StoryParams(
        quarrel="torn_drawing",
        token="honey_cookie",
        obstacle="torn_wrap",
        response="ask_clerk",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Kit",
        friend_gender="boy",
        clerk="postmistress",
        trait="thoughtful",
        delay=0,
    ),
    StoryParams(
        quarrel="broken_promise",
        token="paper_star",
        obstacle="smudged_address",
        response="wait_queue",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        clerk="postmaster",
        trait="restless",
        delay=2,
    ),
]


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    response = RESPONSES[params.response]
    return "same_day" if catches_coach(response, obstacle, params.delay) else "next_day"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Reasonableness gate.
valid(Q, T, O) :- quarrel(Q), token(T), obstacle(O), can_handle(R, O), sense(R, S), sense_min(M), S >= M.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% Outcome model.
pressure(V) :- chosen_obstacle(O), difficulty(O, D), delay(L), V = D + L.
compatible :- chosen_response(R), chosen_obstacle(O), can_handle(R, O).
in_time :- compatible, chosen_response(R), power(R, P), pressure(V), P >= V.

outcome(same_day) :- in_time.
outcome(next_day) :- not in_time.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid in QUARRELS:
        lines.append(asp.fact("quarrel", qid))
    for tid in TOKENS:
        lines.append(asp.fact("token", tid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("difficulty", oid, obstacle.difficulty))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for tt in sorted(response.handles):
            lines.append(asp.fact("handles", rid, tt))
    for oid, obstacle in OBSTACLES.items():
        for rid, response in RESPONSES.items():
            if obstacle_supported(response, obstacle):
                lines.append(asp.fact("can_handle", rid, oid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: valid_combos parity matches ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:", sorted(clingo_sens), sorted(python_sens))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolve for seed {seed}.")
            break

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Empty story in smoke test.")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(smoke, trace=True, qa=True, header="### smoke")
            rendered = buf.getvalue()
        if "socket" not in smoke.story:
            raise StoryError("Smoke story did not include required seed word 'socket'.")
        if "smoke" not in rendered:
            raise StoryError("emit() smoke test did not print header.")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a child takes an apology quest to the post office."
    )
    ap.add_argument("--quarrel", choices=QUARRELS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--clerk", choices=CLERKS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra waiting before the parcel is fixed")
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"], help="hero gender")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "", friend: bool = False) -> str:
    if gender == "girl":
        pool = FRIEND_GIRL_NAMES if friend else GIRL_NAMES
    else:
        pool = FRIEND_BOY_NAMES if friend else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response:
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN:
            raise StoryError(explain_response(args.response))
        if args.obstacle:
            obstacle = OBSTACLES[args.obstacle]
            if not obstacle_supported(response, obstacle):
                raise StoryError(explain_incompatible(obstacle, response))

    combos = [
        combo for combo in valid_combos()
        if (args.quarrel is None or combo[0] == args.quarrel)
        and (args.token is None or combo[1] == args.token)
        and (args.obstacle is None or combo[2] == args.obstacle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quarrel_id, token_id, obstacle_id = rng.choice(sorted(combos))
    obstacle = OBSTACLES[obstacle_id]

    possible_responses = [
        r.id for r in sensible_responses() if obstacle_supported(r, obstacle)
    ]
    if args.response is not None:
        response_id = args.response
    else:
        response_id = rng.choice(sorted(possible_responses))

    hero_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender, friend=True if False else False)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name, friend=True)
    clerk_id = args.clerk or rng.choice(sorted(CLERKS))
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        quarrel=quarrel_id,
        token=token_id,
        obstacle=obstacle_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        clerk=clerk_id,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quarrel not in QUARRELS:
        raise StoryError(f"(Unknown quarrel '{params.quarrel}'.)")
    if params.token not in TOKENS:
        raise StoryError(f"(Unknown token '{params.token}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle '{params.obstacle}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    if params.clerk not in CLERKS:
        raise StoryError(f"(Unknown clerk '{params.clerk}'.)")

    obstacle = OBSTACLES[params.obstacle]
    response = RESPONSES[params.response]
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not obstacle_supported(response, obstacle):
        raise StoryError(explain_incompatible(obstacle, response))

    world = tell(
        quarrel=QUARRELS[params.quarrel],
        token=TOKENS[params.token],
        obstacle=obstacle,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        clerk_style=CLERKS[params.clerk],
        trait=params.trait,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (quarrel, token, obstacle) combos:\n")
        for quarrel, token, obstacle in combos:
            print(f"  {quarrel:15} {token:12} {obstacle}")
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
                f"### {p.hero_name}: {p.quarrel}, {p.token}, {p.obstacle} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
