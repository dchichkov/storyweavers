#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/know_minute_bad_ending_friendship_detective_story.py
================================================================================

A standalone storyworld for a tiny detective-story domain: two friends run a
small detective club, a treasured case item goes missing, one child makes a
hasty accusation, and the real clue reveals what happened.

This world is built around friendship pressure and a detective-story turn:
the children search for evidence, interpret clues, and then face the harder
question of what to do after the truth is known. Some endings repair the
friendship with an apology; some end badly when the apology never comes.

Run it
------
    python storyworlds/worlds/gpt-5.4/know_minute_bad_ending_friendship_detective_story.py
    python storyworlds/worlds/gpt-5.4/know_minute_bad_ending_friendship_detective_story.py --item paper_map --cause wind
    python storyworlds/worlds/gpt-5.4/know_minute_bad_ending_friendship_detective_story.py --item brass_badge --cause wind
    python storyworlds/worlds/gpt-5.4/know_minute_bad_ending_friendship_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/know_minute_bad_ending_friendship_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/know_minute_bad_ending_friendship_detective_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/know_minute_bad_ending_friendship_detective_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        neutral_it = {"kitten", "wind", "thing", "item"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral_it:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    short_role: str
    paper: bool = False
    small: bool = False
    shiny: bool = False
    plaything: bool = False
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
class CauseCfg:
    id: str
    actor_type: str
    actor_label: str
    clue: str
    trail: str
    hideout: str
    reveal: str
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
class ResponseCfg:
    id: str
    repairs: bool
    apology_text: str
    ending_text: str
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


ITEMS = {
    "brass_badge": ItemCfg(
        id="brass_badge",
        label="brass badge",
        phrase="their brass detective badge",
        short_role="badge",
        small=True,
        shiny=True,
        plaything=False,
        tags={"badge", "detective", "shiny"},
    ),
    "paper_map": ItemCfg(
        id="paper_map",
        label="paper map",
        phrase="their folded paper map of secret paths",
        short_role="map",
        paper=True,
        plaything=True,
        tags={"map", "paper", "detective"},
    ),
    "silver_whistle": ItemCfg(
        id="silver_whistle",
        label="silver whistle",
        phrase="their silver signal whistle",
        short_role="whistle",
        small=True,
        shiny=True,
        plaything=True,
        tags={"whistle", "shiny", "detective"},
    ),
    "clue_notebook": ItemCfg(
        id="clue_notebook",
        label="clue notebook",
        phrase="their red clue notebook",
        short_role="notebook",
        paper=True,
        plaything=False,
        tags={"notebook", "paper", "detective"},
    ),
}

CAUSES = {
    "kitten": CauseCfg(
        id="kitten",
        actor_type="kitten",
        actor_label="the striped kitten",
        clue="a row of tiny muddy pawprints beside the table",
        trail="The pawprints led under the porch step.",
        hideout="under the porch step",
        reveal="The striped kitten had batted the missing thing away and tucked it under the porch step.",
        tags={"kitten", "pawprints"},
    ),
    "wind": CauseCfg(
        id="wind",
        actor_type="wind",
        actor_label="the wind",
        clue="a torn paper corner caught on the gate",
        trail="The paper corner pointed them toward the rose hedge.",
        hideout="in the rose hedge",
        reveal="A sharp gust had lifted the missing paper and pinned it in the rose hedge.",
        tags={"wind", "paper"},
    ),
    "sibling": CauseCfg(
        id="sibling",
        actor_type="boy",
        actor_label="the little brother",
        clue="a crayon arrow on the path and a humming voice near the toy box",
        trail="The humming voice came from the shed where the toy box sat open.",
        hideout="inside the toy box in the shed",
        reveal="The little brother had borrowed the missing thing for his own pretend game and tucked it into the toy box.",
        tags={"sibling", "toy_box"},
    ),
}

RESPONSES = {
    "apologize": ResponseCfg(
        id="apologize",
        repairs=True,
        apology_text="The detective swallowed hard and said, \"I was wrong to blame you. I should have waited one more minute and looked at the clues.\"",
        ending_text="The two friends pinned the found item back in their club box and wrote their first rule in big letters: friends listen before they decide what they know.",
        qa_text="apologized and admitted the accusation was unfair",
        tags={"apology", "friendship"},
    ),
    "refuse": ResponseCfg(
        id="refuse",
        repairs=False,
        apology_text="The detective looked away and would not say sorry, even after the truth stood plain as daylight.",
        ending_text="The found item went back into the club box, but the bench stayed empty beside it, and by evening the detective sign hung crooked with only one name left on it.",
        qa_text="refused to apologize even after the real clue was found",
        tags={"bad_ending", "friendship"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Maya", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Noah", "Eli"]
TRAITS = ["careful", "quick", "earnest", "curious", "quiet", "bright"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    item: str
    cause: str
    response: str
    detective_name: str
    detective_gender: str
    friend_name: str
    friend_gender: str
    caretaker: str
    detective_trait: str
    friend_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World and rules
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_accusation_hurts(world: World) -> list[str]:
    out: list[str] = []
    det = world.get("detective")
    friend = world.get("friend")
    if det.memes["accused_friend"] >= THRESHOLD:
        sig = ("hurt",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["hurt"] += 1
            friend.memes["distance"] += 1
            det.memes["certainty"] += 1
            world.facts["accusation_happened"] = True
            out.append("__hurt__")
    return out


def _r_found_brings_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["found"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("detective").memes["relief"] += 1
            world.get("friend").memes["relief"] += 1
            out.append("__relief__")
    return out


def _r_apology_repairs(world: World) -> list[str]:
    out: list[str] = []
    det = world.get("detective")
    friend = world.get("friend")
    if det.memes["apologized"] >= THRESHOLD and friend.memes["hurt"] >= THRESHOLD:
        sig = ("repair",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["hurt"] = 0.0
            friend.memes["distance"] = 0.0
            friend.memes["trust"] += 1
            det.memes["guilt"] += 1
            det.memes["friendship"] += 1
            friend.memes["friendship"] += 1
            out.append("__repair__")
    return out


def _r_refusal_breaks(world: World) -> list[str]:
    out: list[str] = []
    det = world.get("detective")
    friend = world.get("friend")
    if det.memes["refused_apology"] >= THRESHOLD and friend.memes["hurt"] >= THRESHOLD:
        sig = ("break",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["distance"] += 1
            det.memes["distance"] += 1
            world.facts["club_closed"] = True
            out.append("__break__")
    return out


CAUSAL_RULES = [
    Rule(name="accusation_hurts", apply=_r_accusation_hurts),
    Rule(name="found_brings_relief", apply=_r_found_brings_relief),
    Rule(name="apology_repairs", apply=_r_apology_repairs),
    Rule(name="refusal_breaks", apply=_r_refusal_breaks),
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
            if not s.startswith("__"):
                world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def valid_combo(item_id: str, cause_id: str) -> bool:
    if item_id not in ITEMS or cause_id not in CAUSES:
        return False
    item = ITEMS[item_id]
    if cause_id == "kitten":
        return item.small and item.shiny
    if cause_id == "wind":
        return item.paper
    if cause_id == "sibling":
        return item.plaything
    return False


def valid_combos() -> list[tuple[str, str]]:
    return [
        (item_id, cause_id)
        for item_id in sorted(ITEMS)
        for cause_id in sorted(CAUSES)
        if valid_combo(item_id, cause_id)
    ]


def explain_rejection(item_id: str, cause_id: str) -> str:
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if cause_id not in CAUSES:
        return f"(No story: unknown cause '{cause_id}'.)"
    item = ITEMS[item_id]
    cause = CAUSES[cause_id]
    if cause_id == "kitten":
        return (
            f"(No story: {cause.actor_label} is only plausible for something small and shiny, "
            f"but {item.phrase} does not fit that trail of clues.)"
        )
    if cause_id == "wind":
        return (
            f"(No story: the wind can carry a paper clue, but {item.phrase} is not a paper item, "
            f"so the detective trail would not make sense.)"
        )
    return (
        f"(No story: {cause.actor_label} only fits items a child might borrow for a pretend game, "
        f"and {item.phrase} does not fit that kind of borrowing.)"
    )


# ---------------------------------------------------------------------------
# Silent prediction
# ---------------------------------------------------------------------------
def predict_reveal(world: World, cause: CauseCfg) -> dict:
    sim = world.copy()
    _find_item(sim, cause, narrate=False)
    item = sim.get("item")
    return {
        "found": item.meters["found"] >= THRESHOLD,
        "hideout": sim.facts.get("hideout", ""),
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, detective: Entity, friend: Entity, item_cfg: ItemCfg) -> None:
    detective.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{detective.id} and {friend.id} were best friends and the only members of the Willow Step Detective Club. "
        f"Every afternoon they opened their case box, shared one stubby pencil, and promised to tell each other what they know."
    )
    world.say(
        f"That day the club's most important clue-thing was missing: {item_cfg.phrase}. "
        f"Without it, the whole case table looked wrong."
    )


def set_case(world: World, detective: Entity, friend: Entity, item_cfg: ItemCfg) -> None:
    world.say(
        f'"Case of the Missing {item_cfg.short_role.capitalize()}," whispered {detective.id}, pressing a finger to the tabletop. '
        f'{friend.id} nodded and knelt beside the bench as if a real detective might appear at any minute to inspect their work.'
    )
    world.say(
        f"{friend.id} said, \"We have to look slowly so we really know what happened.\""
    )


def hasty_accusation(world: World, detective: Entity, friend: Entity, item_cfg: ItemCfg) -> None:
    detective.memes["accused_friend"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {detective.id} remembered that {friend.id} had carried {item_cfg.short_role} last. "
        f'"I know you touched it last," {detective.pronoun()} said too quickly. '
        f'"Did you hide it from me?"'
    )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s face changed at once. {friend.pronoun().capitalize()} did not shout, but the quiet between them grew thin and sharp."
        )


def first_clue(world: World, cause: CauseCfg) -> None:
    world.say(
        f"Before {friend.id if 'friend' in world.entities else 'the friend'} could answer, they both saw {cause.clue}."
    )
    world.say(
        f"For one small minute nobody spoke. A real clue had finally entered the case."
    )


def search(world: World, detective: Entity, friend: Entity, cause: CauseCfg) -> None:
    pred = predict_reveal(world, cause)
    world.facts["predicted_found"] = pred["found"]
    world.facts["predicted_hideout"] = pred["hideout"]
    world.say(
        f"{detective.id} and {friend.id} followed the sign together. {cause.trail}"
    )


def _find_item(world: World, cause: CauseCfg, narrate: bool = True) -> None:
    item = world.get("item")
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    world.facts["hideout"] = cause.hideout
    world.facts["real_cause"] = cause.id
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"There, {cause.hideout}, lay the missing {item.label}. {cause.reveal}"
        )


def revelation(world: World, cause: CauseCfg) -> None:
    _find_item(world, cause, narrate=True)


def response_scene(world: World, detective: Entity, friend: Entity, response: ResponseCfg) -> None:
    if response.repairs:
        detective.memes["apologized"] += 1
    else:
        detective.memes["refused_apology"] += 1
    propagate(world, narrate=False)
    world.say(response.apology_text)
    if response.repairs:
        world.say(
            f"{friend.id} looked at the found item, then back at {detective.id}, and gave a small nod. "
            f"The hurt did not vanish in a blink, but it softened enough for the club to breathe again."
        )
    else:
        world.say(
            f"{friend.id} touched the found item only long enough to put it back. "
            f"After that, {friend.pronoun()} stepped away from the bench as if it belonged to somebody else."
        )


def ending(world: World, detective: Entity, friend: Entity, response: ResponseCfg) -> None:
    world.say(response.ending_text)
    if response.repairs:
        world.say(
            f"By sunset the two detectives were shoulder to shoulder again, writing neat clues and waiting for the next tiny mystery."
        )
    else:
        world.say(
            f"{detective.id} still had the badge of detective work, but not the friend who had once shared every case."
        )


def tell(
    item_cfg: ItemCfg,
    cause_cfg: CauseCfg,
    response_cfg: ResponseCfg,
    detective_name: str,
    detective_gender: str,
    friend_name: str,
    friend_gender: str,
    caretaker_type: str,
    detective_trait: str,
    friend_trait: str,
) -> World:
    world = World()
    detective = world.add(
        Entity(
            id="detective",
            kind="character",
            type=detective_gender,
            label=detective_name,
            role="detective",
            traits=[detective_trait],
            attrs={"display_name": detective_name},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            traits=[friend_trait],
            attrs={"display_name": friend_name},
        )
    )
    caretaker = world.add(
        Entity(
            id="caretaker",
            kind="character",
            type=caretaker_type,
            label="the grown-up",
            role="caretaker",
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="missing_item",
        )
    )
    cause_actor = world.add(
        Entity(
            id="cause_actor",
            kind="thing",
            type=cause_cfg.actor_type,
            label=cause_cfg.actor_label,
            role="cause_actor",
        )
    )

    item.meters["missing"] = 1.0
    world.facts["detective_name"] = detective_name
    world.facts["friend_name"] = friend_name
    world.facts["caretaker"] = caretaker.label_word
    world.facts["item_cfg"] = item_cfg
    world.facts["cause_cfg"] = cause_cfg
    world.facts["response_cfg"] = response_cfg
    world.facts["detective"] = detective
    world.facts["friend"] = friend
    world.facts["item"] = item
    world.facts["clue"] = cause_cfg.clue
    world.facts["accusation_happened"] = False
    world.facts["club_closed"] = False
    world.facts["predicted_found"] = False
    world.facts["predicted_hideout"] = ""

    introduce(world, detective, friend, item_cfg)
    set_case(world, detective, friend, item_cfg)

    world.para()
    hasty_accusation(world, detective, friend, item_cfg)
    first_clue(world, cause_cfg)
    search(world, detective, friend, cause_cfg)

    world.para()
    revelation(world, cause_cfg)
    response_scene(world, detective, friend, response_cfg)

    world.para()
    ending(world, detective, friend, response_cfg)

    world.facts["outcome"] = "repaired" if response_cfg.repairs else "broken"
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to figure out what happened. Good detectives do not rush; they pay close attention before they decide."
        )
    ],
    "friendship": [
        (
            "Why is saying sorry important in a friendship?",
            "Saying sorry shows that you understand you caused hurt and want to repair it. It helps trust grow again after a mistake."
        )
    ],
    "pawprints": [
        (
            "What can pawprints tell you?",
            "Pawprints can show that an animal walked through a place. A careful detective can follow them to see where the animal went."
        )
    ],
    "wind": [
        (
            "How can wind move paper?",
            "Wind can catch light paper, lift it, and blow it somewhere else. That is why paper clues can end up in bushes or on fences."
        )
    ],
    "toy_box": [
        (
            "Why do little children sometimes borrow things without asking?",
            "Little children often copy games they see and want a turn right away. They do not always stop to think that someone else may be worried about the missing thing."
        )
    ],
    "badge": [
        (
            "What is a badge?",
            "A badge is a small sign or token that shows a role or club. Children often treat a badge like an important symbol."
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map helps you see where places are and which way to go. Even a pretend map can feel very important in a game."
        )
    ],
    "whistle": [
        (
            "What is a whistle used for?",
            "A whistle makes a sharp sound that can call attention or send a signal. In pretend games, children may use one like a detective tool."
        )
    ],
    "notebook": [
        (
            "Why do detectives use notebooks?",
            "A notebook helps a detective remember clues and questions. Writing things down keeps a case from turning into a guess."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "detective",
    "friendship",
    "pawprints",
    "wind",
    "toy_box",
    "badge",
    "map",
    "whistle",
    "notebook",
]


def generation_prompts(world: World) -> list[str]:
    item_cfg = world.facts["item_cfg"]
    cause_cfg = world.facts["cause_cfg"]
    outcome = world.facts["outcome"]
    detective = world.facts["detective"]
    friend = world.facts["friend"]
    prompts = [
        f'Write a detective story for a young child that includes the words "know" and "minute". The story should center on two friends searching for a missing {item_cfg.short_role}.',
        f"Tell a gentle mystery where {detective.label} wrongly blames {friend.label} before a real clue reveals what happened to {item_cfg.phrase}.",
    ]
    if outcome == "broken":
        prompts.append(
            f"Write a sad detective-story ending where the real clue points to {cause_cfg.actor_label}, but the friendship is still hurt because nobody repairs the accusation."
        )
    else:
        prompts.append(
            f"Write a detective story where the clue trail leads to {cause_cfg.hideout}, and the friendship is saved because one friend apologizes after the truth is known."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    item_cfg = world.facts["item_cfg"]
    cause_cfg = world.facts["cause_cfg"]
    response_cfg = world.facts["response_cfg"]
    detective = world.facts["detective"]
    friend = world.facts["friend"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two best friends, {detective.label} and {friend.label}, who run a little detective club together. Their friendship matters because the missing {item_cfg.short_role} turns a small case into a bigger hurt."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item_cfg.phrase}. It mattered because it was one of the club's special detective tools."
        ),
        (
            f"Why did {detective.label} accuse {friend.label}?",
            f"{detective.label} accused {friend.label} because {friend.label} had touched the {item_cfg.short_role} last, and {detective.pronoun()} jumped to a fast guess. The accusation came before the real clue was studied, which is why it hurt the friendship."
        ),
        (
            "What clue helped solve the case?",
            f"The clue was {cause_cfg.clue}. It mattered because it pointed away from blame and toward the real trail."
        ),
        (
            "Where did they find the missing thing?",
            f"They found it {cause_cfg.hideout}. The hiding place matched the clue, so the children could finally know what had really happened."
        ),
    ]
    if outcome == "repaired":
        qa.append(
            (
                f"How was the friendship repaired?",
                f"{detective.label} {response_cfg.qa_text}. That mattered because the true clue solved the case, but the apology solved the hurt."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the club together again and a new rule about listening before deciding what they know. The ending image of the two friends writing clues side by side shows that the friendship was mended."
            )
        )
    else:
        qa.append(
            (
                f"Why is this a bad ending even though the item was found?",
                f"It is a bad ending because {detective.label} {response_cfg.qa_text}. The case was solved, but the friendship was left damaged, so the club no longer felt whole."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the found {item_cfg.short_role} back in the box, but with one friend gone from the bench. That final image shows that knowing the truth is not enough when hurt is left untouched."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item_cfg = world.facts["item_cfg"]
    cause_cfg = world.facts["cause_cfg"]
    response_cfg = world.facts["response_cfg"]
    tags = {"detective", "friendship"} | set(item_cfg.tags) | set(cause_cfg.tags) | set(response_cfg.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for name, *_ in world.fired)}")
    lines.append(
        f"  facts: outcome={world.facts.get('outcome')} hideout={world.facts.get('hideout')} "
        f"club_closed={world.facts.get('club_closed')}"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        item="paper_map",
        cause="wind",
        response="apologize",
        detective_name="Nora",
        detective_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        caretaker="mother",
        detective_trait="quick",
        friend_trait="careful",
    ),
    StoryParams(
        item="silver_whistle",
        cause="kitten",
        response="refuse",
        detective_name="Max",
        detective_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        caretaker="father",
        detective_trait="bright",
        friend_trait="quiet",
    ),
    StoryParams(
        item="paper_map",
        cause="sibling",
        response="refuse",
        detective_name="Ella",
        detective_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        caretaker="mother",
        detective_trait="curious",
        friend_trait="earnest",
    ),
    StoryParams(
        item="brass_badge",
        cause="kitten",
        response="apologize",
        detective_name="Finn",
        detective_gender="boy",
        friend_name="Rose",
        friend_gender="girl",
        caretaker="father",
        detective_trait="quick",
        friend_trait="careful",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Item, kitten)  :- item(Item), small(Item), shiny(Item).
valid(Item, wind)    :- item(Item), paper(Item).
valid(Item, sibling) :- item(Item), plaything(Item).

outcome(repaired) :- chosen_response(R), repairs(R).
outcome(broken)   :- chosen_response(R), not repairs(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.paper:
            lines.append(asp.fact("paper", item_id))
        if item.small:
            lines.append(asp.fact("small", item_id))
        if item.shiny:
            lines.append(asp.fact("shiny", item_id))
        if item.plaything:
            lines.append(asp.fact("plaything", item_id))
    for cause_id in CAUSES:
        lines.append(asp.fact("cause", cause_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        if response.repairs:
            lines.append(asp.fact("repairs", response_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(response_id: str) -> str:
    import asp

    model = asp.one_model(
        asp_program(f"chosen_response({response_id}).", "#show outcome/1.")
    )
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    return "repaired" if RESPONSES[params.response].repairs else "broken"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for response_id in sorted(RESPONSES):
        py = "repaired" if RESPONSES[response_id].repairs else "broken"
        asp_res = asp_outcome(response_id)
        if py != asp_res:
            rc = 1
            print(f"MISMATCH in outcome for {response_id}: python={py} clingo={asp_res}")
    if rc == 0:
        print("OK: outcome model matches response repair logic.")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("smoke test produced incomplete QA or prompts")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generated and emitted a story.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: detective friends, a missing clue-item, and a friendship tested by a hasty accusation."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--detective-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (item, cause) pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{args.item}'.)")
    if args.cause and args.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{args.cause}'.)")
    if args.response and args.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{args.response}'.)")
    if args.item and args.cause and not valid_combo(args.item, args.cause):
        raise StoryError(explain_rejection(args.item, args.cause))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.cause is None or combo[1] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, cause_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(RESPONSES))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=detective_name)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    detective_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        item=item_id,
        cause=cause_id,
        response=response_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        caretaker=caretaker,
        detective_trait=detective_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{params.cause}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if not valid_combo(params.item, params.cause):
        raise StoryError(explain_rejection(params.item, params.cause))

    world = tell(
        item_cfg=ITEMS[params.item],
        cause_cfg=CAUSES[params.cause],
        response_cfg=RESPONSES[params.response],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        caretaker_type=params.caretaker,
        detective_trait=params.detective_trait,
        friend_trait=params.friend_trait,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, cause) pairs:\n")
        for item_id, cause_id in combos:
            print(f"  {item_id:14} {cause_id}")
        print("\noutcomes by response:\n")
        for response_id in sorted(RESPONSES):
            print(f"  {response_id:10} {asp_outcome(response_id)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} & {p.friend_name}: {p.item} by {p.cause} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
