#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/practise_appendix_bravery_cautionary_whodunit.py
============================================================================

A standalone storyworld for a tiny, child-facing whodunit with a cautionary turn:
during detective practise, a small mystery points toward a hiding place above a
child's reach. The children can be brave the safe way by getting a grown-up, or
they can try to climb alone and get a wobbling scare before the mystery is solved.

Two seed words are built into the world and its prose:
- practise
- appendix

The seed shape rebuilt as simulation:
- premise: two children are at detective-club practise
- tension: a missing object turns their game into a real whodunit
- turn: the clue points to a high hiding place, tempting a risky climb
- resolution: the item is recovered safely, and the children learn that bravery
  can include asking for help

Run it
------
    python storyworlds/worlds/gpt-5.4/practise_appendix_bravery_cautionary_whodunit.py
    python storyworlds/worlds/gpt-5.4/practise_appendix_bravery_cautionary_whodunit.py --setting library --item bell
    python storyworlds/worlds/gpt-5.4/practise_appendix_bravery_cautionary_whodunit.py --culprit magpie --spot prop_loft
    python storyworlds/worlds/gpt-5.4/practise_appendix_bravery_cautionary_whodunit.py --all --qa
    python storyworlds/worlds/gpt-5.4/practise_appendix_bravery_cautionary_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "teacher"}
        male = {"boy", "father", "man", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"magpie"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"kitten", "mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "librarian": "librarian",
            "teacher": "teacher",
            "caretaker": "caretaker",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    room_phrase: str
    practice_phrase: str
    adult_type: str
    spots: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    the: str
    kind: str
    owner_phrase: str
    importance: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Culprit:
    id: str
    label: str
    type: str
    likes: set[str]
    spots: set[str]
    clue: str
    mark: str
    action: str
    motive: str
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
class Spot:
    id: str
    label: str
    where: str
    reach_text: str
    found_text: str
    risky_surface: str
    high: bool = True
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
class Approach:
    id: str
    label: str
    sense: int
    text: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(setting=self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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
    hero = world.get("hero")
    spot = world.facts["spot_cfg"]
    if hero.meters["climbing"] < THRESHOLD or not spot.high:
        return []
    sig = ("wobble", hero.id, spot.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["wobble"] += 1
    hero.memes["fear"] += 1
    world.get("friend").memes["fear"] += 1
    world.get("room").meters["danger"] += 1
    return ["__wobble__"]


def _r_deduce(world: World) -> list[str]:
    hero = world.get("hero")
    culprit = world.get("culprit")
    if hero.meters["clue_read"] < THRESHOLD:
        return []
    sig = ("deduce", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["suspected"] += 1
    hero.memes["confidence"] += 1
    return ["__deduced__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="deduce", tag="social", apply=_r_deduce),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "library": Setting(
        id="library",
        label="the little library",
        room_phrase="between the tall shelves and the reading rug",
        practice_phrase="library-detective practise",
        adult_type="librarian",
        spots={"window_ledge", "atlas_shelf"},
        tags={"library"},
    ),
    "theater": Setting(
        id="theater",
        label="the school theater",
        room_phrase="behind the velvet curtain and the prop table",
        practice_phrase="junior-sleuth practise",
        adult_type="teacher",
        spots={"prop_loft", "curtain_rail"},
        tags={"theater"},
    ),
    "hall": Setting(
        id="hall",
        label="the village hall",
        room_phrase="near the folding chairs and the notice board",
        practice_phrase="mystery-club practise",
        adult_type="caretaker",
        spots={"window_ledge", "snack_cubby"},
        tags={"hall"},
    ),
}

ITEMS = {
    "bell": MissingItem(
        id="bell",
        label="bell",
        the="the bell",
        kind="shiny",
        owner_phrase="the clue bell for the next round",
        importance="Without it, their mystery game could not begin.",
        tags={"bell", "shiny"},
    ),
    "badge": MissingItem(
        id="badge",
        label="badge",
        the="the badge",
        kind="shiny",
        owner_phrase="the gold detective badge",
        importance="It was the prize for the neatest clues.",
        tags={"badge", "shiny"},
    ),
    "ribbon": MissingItem(
        id="ribbon",
        label="ribbon",
        the="the ribbon",
        kind="soft",
        owner_phrase="the blue winner's ribbon",
        importance="It was meant to tie around the solved casebook.",
        tags={"ribbon", "soft"},
    ),
    "sandwich": MissingItem(
        id="sandwich",
        label="sandwich",
        the="the sandwich",
        kind="smelly",
        owner_phrase="the cheese sandwich for after practise",
        importance="By the time they noticed, only the paper napkin remained on the table.",
        tags={"sandwich", "food"},
    ),
}

CULPRITS = {
    "magpie": Culprit(
        id="magpie",
        label="a magpie",
        type="magpie",
        likes={"shiny"},
        spots={"window_ledge", "atlas_shelf"},
        clue="a black feather with a silver shine",
        mark="feather",
        action="had hopped in through a cracked window and carried it off",
        motive="magpies in this world love small shiny things",
        reveal="A magpie blinked beside the hidden prize, proud of its sparkling find.",
        tags={"magpie", "bird"},
    ),
    "kitten": Culprit(
        id="kitten",
        label="a striped kitten",
        type="kitten",
        likes={"soft"},
        spots={"prop_loft", "curtain_rail"},
        clue="a tiny paw print and one pale whisker",
        mark="pawprint",
        action="had tugged it away to make a soft little nest",
        motive="kittens in this world love soft things to curl around",
        reveal="A striped kitten was tucked there, batting at the soft prize with bright eyes.",
        tags={"kitten", "cat"},
    ),
    "mouse": Culprit(
        id="mouse",
        label="a small mouse",
        type="mouse",
        likes={"smelly"},
        spots={"snack_cubby", "atlas_shelf"},
        clue="a neat little nibble in the paper and a crumb trail",
        mark="crumb",
        action="had dragged it away because it smelled delicious",
        motive="mice in this world follow tasty smells wherever they can climb",
        reveal="A small mouse froze beside the prize, its whiskers trembling over the crumbs.",
        tags={"mouse"},
    ),
}

SPOTS = {
    "window_ledge": Spot(
        id="window_ledge",
        label="the window ledge",
        where="up on the wide window ledge",
        reach_text="It was higher than the children could reach from the floor.",
        found_text="the prize tucked beside a pot of dusty geraniums",
        risky_surface="a rolling book cart",
        high=True,
        tags={"high_place", "window"},
    ),
    "atlas_shelf": Spot(
        id="atlas_shelf",
        label="the top atlas shelf",
        where="on the top atlas shelf",
        reach_text="It sat above even the tallest shelf label.",
        found_text="the prize behind a stack of giant atlases",
        risky_surface="a wobbling wooden chair",
        high=True,
        tags={"high_place", "shelf"},
    ),
    "prop_loft": Spot(
        id="prop_loft",
        label="the prop loft",
        where="up in the prop loft",
        reach_text="It was tucked above the stage, far over the children's heads.",
        found_text="the prize half-hidden in a nest of old fabric",
        risky_surface="a paint-splashed stool",
        high=True,
        tags={"high_place", "loft"},
    ),
    "curtain_rail": Spot(
        id="curtain_rail",
        label="the curtain rail",
        where="along the curtain rail",
        reach_text="It ran high over the velvet curtain, much too far up to touch.",
        found_text="the prize looped over the rail beside the curtain folds",
        risky_surface="a narrow prop trunk",
        high=True,
        tags={"high_place", "curtain"},
    ),
    "snack_cubby": Spot(
        id="snack_cubby",
        label="the snack cubby",
        where="in the snack cubby above the kettle shelf",
        reach_text="Even standing on tiptoe was nowhere near enough.",
        found_text="the prize behind a stack of paper cups",
        risky_surface="a folding chair",
        high=True,
        tags={"high_place", "cubby"},
    ),
}

APPROACHES = {
    "ask_adult": Approach(
        id="ask_adult",
        label="ask a grown-up first",
        sense=3,
        text="Real detectives can ask for safe help before they reach high places.",
        tags={"ask_adult", "safe"},
    ),
    "climb_alone": Approach(
        id="climb_alone",
        label="climb alone",
        sense=1,
        text="The urge to solve the case fast can make a child forget how high and shaky things are.",
        tags={"climb", "unsafe"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Rosa", "Tara", "Nina", "Asha", "Zoe", "Maya"]
BOY_NAMES = ["Ravi", "Owen", "Sam", "Leo", "Theo", "Ben", "Eli", "Noah"]
TRAITS = ["careful", "curious", "steady", "thoughtful", "eager", "gentle"]


def valid_combo(setting_id: str, item_id: str, culprit_id: str, spot_id: str) -> bool:
    if setting_id not in SETTINGS or item_id not in ITEMS or culprit_id not in CULPRITS or spot_id not in SPOTS:
        return False
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    return (
        spot_id in setting.spots
        and item.kind in culprit.likes
        and spot_id in culprit.spots
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id in ITEMS:
            for culprit_id in CULPRITS:
                for spot_id in SPOTS:
                    if valid_combo(setting_id, item_id, culprit_id, spot_id):
                        combos.append((setting_id, item_id, culprit_id, spot_id))
    return sorted(combos)


def explain_rejection(setting_id: str, item_id: str, culprit_id: str, spot_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if culprit_id not in CULPRITS:
        return f"(No story: unknown culprit '{culprit_id}'.)"
    if spot_id not in SPOTS:
        return f"(No story: unknown spot '{spot_id}'.)"
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    if spot_id not in setting.spots:
        return (
            f"(No story: {setting.label} does not contain {SPOTS[spot_id].label}, "
            f"so the clue cannot honestly lead there.)"
        )
    if item.kind not in culprit.likes:
        return (
            f"(No story: {culprit.label} would not plausibly steal {item.the} here. "
            f"This culprit goes for {sorted(culprit.likes)}, not {item.kind} things.)"
        )
    if spot_id not in culprit.spots:
        return (
            f"(No story: {culprit.label} cannot plausibly stash the prize at {SPOTS[spot_id].label}.)"
        )
    return "(No story: this mystery combination is not reasonable.)"


def outcome_of(params: "StoryParams") -> str:
    if params.approach == "ask_adult":
        return "safe_help"
    return "scare_then_help"


def predict_risk(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["climbing"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "wobble": hero.meters["wobble"],
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} and {friend.id} loved to practise being detectives in {world.setting.label}. "
        f"That afternoon they were meeting {world.setting.room_phrase} for {world.setting.practice_phrase}."
    )
    world.say(
        "At the back of their little case notebook, in the appendix, "
        "they had drawn a clue page with feathers, paw prints, and crumb trails."
    )


def setup_mystery(world: World, hero: Entity, friend: Entity, item: MissingItem) -> None:
    world.say(
        f"Just as the game was about to start, {item.the} was gone. It had been "
        f"{item.owner_phrase}, and now the table sat empty."
    )
    world.say(item.importance)
    world.say(f'"Who took {item.the}?" {friend.id} whispered. It felt like a real whodunit at once.')


def find_clue(world: World, hero: Entity, culprit_cfg: Culprit, spot_cfg: Spot) -> None:
    hero.meters["clue_read"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} spotted {culprit_cfg.clue} near the floor below {spot_cfg.label}. "
        f"{hero.pronoun().capitalize()} flipped to the appendix page and matched it at once."
    )
    world.say(
        f'"That mark means {culprit_cfg.label}," {hero.id} said. '
        f'"The clue points {spot_cfg.where}."'
    )
    world.facts["clue_text"] = culprit_cfg.clue


def tempt(world: World, hero: Entity, spot_cfg: Spot) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"They peered up. {spot_cfg.reach_text} "
        f"{hero.id}'s heart beat faster with the wish to solve the case first."
    )


def warn(world: World, friend: Entity, hero: Entity, spot_cfg: Spot) -> None:
    pred = predict_risk(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_wobble"] = pred["wobble"]
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} reached for {hero.id}\'s sleeve. "Wait," {friend.pronoun()} said. '
        f'"If you climb on {spot_cfg.risky_surface}, it could wobble. '
        f'Let\'s be brave the safe way and get {world.get("adult").label_word}."'
    )


def choose_help(world: World, hero: Entity) -> None:
    hero.memes["prudence"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} took one more look upward, then nodded. "
        f'"You\'re right," {hero.pronoun()} said. "We can solve it without climbing alone."'
    )


def climb_anyway(world: World, hero: Entity, spot_cfg: Spot) -> None:
    hero.meters["climbing"] += 1
    hero.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But the case felt too close. "{hero.id} can get it," {hero.pronoun()} whispered, '
        f"and dragged {spot_cfg.risky_surface} over."
    )
    if hero.meters["wobble"] >= THRESHOLD:
        world.say(
            f"The moment {hero.pronoun()} stepped up, it rocked under {hero.pronoun('object')}. "
            f"{hero.id} windmilled both arms, and the mystery suddenly felt much less like a game."
        )


def adult_helps(world: World, adult: Entity, spot_cfg: Spot, culprit_cfg: Culprit, item_cfg: MissingItem) -> None:
    item = world.get("item")
    item.meters["found"] += 1
    item.meters["hidden"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} came over with a steady step ladder and a small light. "
        f"{adult.pronoun().capitalize()} looked where the children pointed, climbed carefully, and found "
        f"{spot_cfg.found_text}."
    )
    world.say(culprit_cfg.reveal)
    world.say(
        f"So that was the answer: {culprit_cfg.label} {culprit_cfg.action}. "
        f"The children had guessed right from the clue."
    )
    world.facts["solved_by"] = "adult_help"


def lesson(world: World, adult: Entity, hero: Entity, friend: Entity, approach: Approach) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    if approach.id == "climb_alone":
        hero.memes["fear"] = 0.0
        friend.memes["fear"] = 0.0
        world.say(
            f'{adult.label_word.capitalize()} set the ladder away and knelt beside them. '
            f'"A brave heart is good," {adult.pronoun()} said gently, '
            f'"but high places are not for children alone."'
        )
    else:
        world.say(
            f'{adult.label_word.capitalize()} smiled at both of them. '
            f'"That was brave detective work," {adult.pronoun()} said. '
            f'"You solved the clue and chose the safe way too."'
        )
    world.say(
        f"{approach.text} The case felt better once everyone could breathe again."
    )


def bright_ending(world: World, hero: Entity, friend: Entity, item_cfg: MissingItem) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"A little later, {item_cfg.the} was back where it belonged, and detective practise began at last."
    )
    world.say(
        f"This time {hero.id} and {friend.id} added one more note to the appendix: "
        f'"First clue, then calm thinking, then safe help if the case is up high."'
    )
    world.say(
        "With that rule in place, the room felt full of mystery again, but not of danger."
    )
def tell(
    item_cfg: Item,
    culprit_cfg: Culprit,
    spot_cfg: Spot,
    approach_cfg: Approach,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    hero_trait: HeroTrait,
    friend_trait: FriendTrait,
    setting_cfg=None,
) -> World:
    world = World(setting=setting_cfg)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, attrs={"trait": hero_trait}))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, attrs={"trait": friend_trait}))
    adult = world.add(Entity(id="adult", kind="character", type=setting_cfg.adult_type, label="the adult"))
    culprit = world.add(Entity(id="culprit", kind="thing", type=culprit_cfg.type, label=culprit_cfg.label, tags=set(culprit_cfg.tags)))
    item = world.add(Entity(id="item", kind="thing", type=item_cfg.id, label=item_cfg.label, tags=set(item_cfg.tags)))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting_cfg.label))

    item.meters["hidden"] = 1.0
    item.meters["found"] = 0.0
    hero.meters["climbing"] = 0.0
    hero.meters["wobble"] = 0.0
    hero.meters["clue_read"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["bravery"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["prudence"] = 0.0
    hero.memes["lesson"] = 0.0
    hero.memes["confidence"] = 0.0
    friend.memes["joy"] = 0.0
    friend.memes["fear"] = 0.0
    friend.memes["caution"] = 0.0
    friend.memes["lesson"] = 0.0
    room.meters["danger"] = 0.0
    culprit.memes["suspected"] = 0.0

    world.facts.update(
        setting=setting_cfg,
        item_cfg=item_cfg,
        culprit_cfg=culprit_cfg,
        spot_cfg=spot_cfg,
        approach_cfg=approach_cfg,
        hero=hero,
        friend=friend,
        adult=adult,
        culprit=culprit,
        item=item,
        clue_text="",
        predicted_danger=0.0,
        predicted_wobble=0.0,
        solved_by="",
    )

    introduce(world, hero, friend)
    setup_mystery(world, hero, friend, item_cfg)

    world.para()
    find_clue(world, hero, culprit_cfg, spot_cfg)
    tempt(world, hero, spot_cfg)
    warn(world, friend, hero, spot_cfg)

    world.para()
    if approach_cfg.id == "ask_adult":
        choose_help(world, hero)
        adult_helps(world, adult, spot_cfg, culprit_cfg, item_cfg)
    else:
        climb_anyway(world, hero, spot_cfg)
        world.say(f'"{adult.label_word.capitalize()}!" {friend.label} shouted.')
        adult_helps(world, adult, spot_cfg, culprit_cfg, item_cfg)

    world.para()
    lesson(world, adult, hero, friend, approach_cfg)
    bright_ending(world, hero, friend, item_cfg)

    world.facts.update(
        outcome=outcome_of(StoryParams(
            setting=setting_cfg.id,
            item=item_cfg.id,
            culprit=culprit_cfg.id,
            spot=spot_cfg.id,
            approach=approach_cfg.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            hero_trait=hero_trait,
            friend_trait=friend_trait,
            seed=None,
        )),
        danger_happened=room.meters["danger"] >= THRESHOLD or hero.meters["wobble"] >= THRESHOLD,
        mystery_solved=item.meters["found"] >= THRESHOLD,
    )
    return world
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
    "appendix": [
        (
            "What is an appendix in a book?",
            "An appendix is an extra part at the back of a book with helpful information. It can hold lists, notes, or clue pages that you look up later.",
        )
    ],
    "bravery": [
        (
            "Can asking a grown-up for help be brave?",
            "Yes. Brave does not only mean rushing in first. It can also mean staying calm and choosing the safe thing when something feels risky.",
        )
    ],
    "whodunit": [
        (
            "What is a whodunit?",
            "A whodunit is a mystery story that asks who did something. The fun comes from following clues until the answer is revealed.",
        )
    ],
    "high_place": [
        (
            "Why should children not climb to high places alone?",
            "High places can wobble, tip, or make you fall. A grown-up can use the right ladder and keep everyone safe.",
        )
    ],
    "magpie": [
        (
            "Why might a magpie take something shiny?",
            "Magpies are often drawn to things that sparkle. A shiny bell or badge can catch a magpie's eye like a little treasure.",
        )
    ],
    "kitten": [
        (
            "Why would a kitten carry off a ribbon?",
            "A kitten likes soft, light things it can bat and tug. A ribbon can feel like a toy or a cozy nest piece.",
        )
    ],
    "mouse": [
        (
            "Why would a mouse drag away a sandwich?",
            "A mouse follows smells and looks for food. A sandwich is worth hauling off if it smells tasty enough.",
        )
    ],
    "clue": [
        (
            "What can clues tell you in a mystery?",
            "Clues are small signs that point toward what happened. A feather, paw print, or crumb can help you guess the right answer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["whodunit", "appendix", "clue", "bravery", "high_place", "magpie", "kitten", "mouse"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    friend = f["friend"].label
    item = f["item_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    base = (
        f'Write a short whodunit for a 3-to-5-year-old where two children practise being detectives, '
        f'use the word "appendix", and solve the mystery of a missing {item.label}.'
    )
    if outcome == "safe_help":
        return [
            base,
            f"Tell a gentle mystery set in {setting.label} where {hero} and {friend} find a clue, want to reach a high hiding place, and bravely ask a grown-up for help instead of climbing alone.",
            'Write a cautionary story that teaches that bravery can mean choosing safe help first, not just being the fastest one to solve the case.',
        ]
    return [
        base,
        f"Tell a cautionary whodunit where {hero} almost climbs alone to solve the mystery, gets a wobbling scare, and then learns a safer kind of bravery.",
        'Write a mystery story with a gentle warning: clues are exciting, but children should not climb to high places without a grown-up.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label}, two children at detective practise. They turn a missing {item.label} into a little whodunit.",
        ),
        (
            f"What was missing?",
            f"{item.The} was missing at the start of the story. It mattered because {item.importance.lower()}",
        ),
        (
            "How did they know who took it?",
            f"They found {f['clue_text']} and matched it with the appendix in their case notebook. That clue pointed to {culprit.label}, so the answer came from evidence, not guessing.",
        ),
        (
            f"Why was the hiding place risky?",
            f"The prize was hidden at {spot.label}, and {spot.reach_text.lower()} {friend.label} warned that climbing on {spot.risky_surface} could wobble. That made the mystery exciting, but also dangerous for children.",
        ),
    ]
    if outcome == "safe_help":
        qa.append(
            (
                f"How were they brave?",
                f"They were brave because they still followed the clue and solved the mystery, but they chose to get {adult.label_word} first. The story shows that calm caution can be part of real bravery.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.label} tried to climb alone?",
                f"The seat wobbled under {hero.label}, and the game suddenly felt scary. After that, {adult.label_word} helped safely, so the case could be solved without a fall.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {item.the} safely back in place and the children adding a new safety note to the appendix. The ending image proves they changed how they would solve high-up mysteries next time.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"appendix", "bravery", "whodunit", "clue", "high_place"}
    culprit_id = f["culprit_cfg"].id
    if culprit_id in KNOWLEDGE:
        tags.add(culprit_id)
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
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    setting: str
    item: str
    culprit: str
    spot: str
    approach: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        setting="library",
        item="bell",
        culprit="magpie",
        spot="window_ledge",
        approach="ask_adult",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Ravi",
        friend_gender="boy",
        hero_trait="curious",
        friend_trait="careful",
    ),
    StoryParams(
        setting="theater",
        item="ribbon",
        culprit="kitten",
        spot="prop_loft",
        approach="climb_alone",
        hero_name="Owen",
        hero_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
        hero_trait="eager",
        friend_trait="thoughtful",
    ),
    StoryParams(
        setting="hall",
        item="sandwich",
        culprit="mouse",
        spot="snack_cubby",
        approach="ask_adult",
        hero_name="Rosa",
        hero_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        hero_trait="steady",
        friend_trait="gentle",
    ),
    StoryParams(
        setting="library",
        item="badge",
        culprit="magpie",
        spot="atlas_shelf",
        approach="climb_alone",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        hero_trait="curious",
        friend_trait="careful",
    ),
]


ASP_RULES = r"""
valid(S,I,C,Sp) :- setting(S), item(I), culprit(C), spot(Sp),
                   affords(S,Sp), likes(C,K), item_kind(I,K), reaches(C,Sp).

risky(Sp) :- chosen_spot(Sp), high(Sp), chosen_approach(climb_alone).
safe_choice :- chosen_approach(ask_adult).

outcome(safe_help) :- safe_choice.
outcome(scare_then_help) :- risky(Sp).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in sorted(setting.spots):
            lines.append(asp.fact("affords", sid, spot))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_kind", iid, item.kind))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for like in sorted(culprit.likes):
            lines.append(asp.fact("likes", cid, like))
        for spot in sorted(culprit.spots):
            lines.append(asp.fact("reaches", cid, spot))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if spot.high:
            lines.append(asp.fact("high", sid))
    for aid in APPROACHES:
        lines.append(asp.fact("approach", aid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_approach", params.approach),
    ])
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=True, qa=True, header="### smoke")
    if not sample.prompts or not sample.story_qa or not sample.world_qa:
        raise StoryError("Smoke test failed: missing QA or prompts.")


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))

    cases: list[StoryParams] = list(CURATED)
    for s in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: detective practise, a tiny whodunit, and the brave safe choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.culprit and args.spot:
        if not valid_combo(args.setting, args.item, args.culprit, args.spot):
            raise StoryError(explain_rejection(args.setting, args.item, args.culprit, args.spot))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.spot is None or combo[3] == args.spot)
    ]
    if not combos:
        if args.setting and args.item and args.culprit and args.spot:
            raise StoryError(explain_rejection(args.setting, args.item, args.culprit, args.spot))
        raise StoryError("(No valid combination matches the given options.)")

    setting, item, culprit, spot = rng.choice(combos)
    approach = args.approach or rng.choice(sorted(APPROACHES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        item=item,
        culprit=culprit,
        spot=spot,
        approach=approach,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.item, params.culprit, params.spot):
        raise StoryError(explain_rejection(params.setting, params.item, params.culprit, params.spot))
    if params.approach not in APPROACHES:
        raise StoryError(f"(No story: unknown approach '{params.approach}'.)")
    if params.setting not in SETTINGS or params.item not in ITEMS or params.culprit not in CULPRITS or params.spot not in SPOTS:
        raise StoryError("(No story: one or more parameters are unknown.)")

    world = tell(
        setting_cfg=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        culprit_cfg=CULPRITS[params.culprit],
        spot_cfg=SPOTS[params.spot],
        approach_cfg=APPROACHES[params.approach],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
    )
    sample = StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("friend", params.friend_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    # Replace entity ids with labels only in prose/QA-facing strings.
    sample.story = sample.story.replace("hero", params.hero_name).replace("friend", params.friend_name)
    for item in sample.story_qa:
        item.answer = item.answer.replace("hero", params.hero_name).replace("friend", params.friend_name)
        item.question = item.question.replace("hero", params.hero_name).replace("friend", params.friend_name)
    for prompt_index, prompt in enumerate(sample.prompts):
        sample.prompts[prompt_index] = prompt.replace("hero", params.hero_name).replace("friend", params.friend_name)
    return sample


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, culprit, spot) combos:\n")
        for setting, item, culprit, spot in combos:
            print(f"  {setting:8} {item:9} {culprit:7} {spot}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name} & {p.friend_name}: {p.item} / {p.culprit} / "
                f"{p.spot} ({p.setting}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
