#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/behold_tight_mystery_to_solve_humor_flashback.py
============================================================================

A standalone story world for a tiny fairy-tale mystery with humor and a
flashback. A child notices that something important has gone missing before a
village celebration, follows a clue with a small helper, remembers a funny scene
from earlier, and discovers that the "thief" was really a muddled borrower with
a silly problem.

The world prefers a small set of *plausible* pairings:
- each culprit only borrows the one item that actually solves their problem
- each culprit leaves a characteristic clue
- each hiding place needs the right helper to reach or notice it

So the story is never just a frozen paragraph with swapped nouns. The object,
clue, helper, flashback, reveal, and ending image all come from simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/behold_tight_mystery_to_solve_humor_flashback.py
    python storyworlds/worlds/gpt-5.4/behold_tight_mystery_to_solve_humor_flashback.py --item ribbon_roll --culprit goat
    python storyworlds/worlds/gpt-5.4/behold_tight_mystery_to_solve_humor_flashback.py --helper frog --culprit goat
    python storyworlds/worlds/gpt-5.4/behold_tight_mystery_to_solve_humor_flashback.py --all
    python storyworlds/worlds/gpt-5.4/behold_tight_mystery_to_solve_humor_flashback.py --qa --json
    python storyworlds/worlds/gpt-5.4/behold_tight_mystery_to_solve_humor_flashback.py --verify
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
        female = {"girl", "mother", "queen", "witch", "hen"}
        male = {"boy", "father", "king", "wizard", "goat", "bear"}
        neutral = {"frog", "squirrel", "goose"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    id: str
    place: str
    opening: str
    celebration: str
    ending_image: str
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
class MysteryItem:
    id: str
    label: str
    phrase: str
    article: str
    use_at_feast: str
    edible: bool
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
class Culprit:
    id: str
    label: str
    type: str
    wants_item: str
    clue: str
    clue_text: str
    place: str
    comic_image: str
    flashback: str
    explanation: str
    apology: str
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
class HidingPlace:
    id: str
    label: str
    trail_text: str
    arrival_text: str
    helper_ids: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    type: str
    style: str
    find_text: str
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
class StoryParams:
    setting: str
    item: str
    culprit: str
    helper: str
    hero: str
    hero_gender: str
    elder: str
    elder_type: str
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


def _r_missing_stirs(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_stirs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_clue_points(world: World) -> list[str]:
    hero = world.get("hero")
    if world.get("clue").meters["noticed"] < THRESHOLD:
        return []
    if world.get("helper").meters["guiding"] < THRESHOLD:
        return []
    sig = ("clue_points",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["search_progress"] += 1
    return []


def _r_reunion_softens(world: World) -> list[str]:
    hero = world.get("hero")
    culprit = world.get("culprit")
    item = world.get("item")
    if culprit.meters["found"] < THRESHOLD or item.meters["returned"] < THRESHOLD:
        return []
    sig = ("reunion_softens",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["kindness"] += 1
    culprit.memes["embarrassment"] += 1
    culprit.memes["trust"] += 1
    world.get("elder").memes["approval"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_stirs", tag="emotional", apply=_r_missing_stirs),
    Rule(name="clue_points", tag="physical", apply=_r_clue_points),
    Rule(name="reunion_softens", tag="social", apply=_r_reunion_softens),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                # rule may have changed state without prose
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "moonwell": Setting(
        id="moonwell",
        place="Moonwell Green",
        opening="At the edge of Moonwell Green stood a tiny feast table under silver lanterns.",
        celebration="the Moonrise Feast",
        ending_image="the lanterns winked on the well water like tiny laughing stars",
        tags={"village", "feast"},
    ),
    "thimble_castle": Setting(
        id="thimble_castle",
        place="the courtyard of Thimble Castle",
        opening="In the courtyard of Thimble Castle, even the flagstones looked ready for a story.",
        celebration="the Lantern Supper",
        ending_image="the little banners fluttered as if the whole castle had learned the joke",
        tags={"castle", "feast"},
    ),
    "clover_hollow": Setting(
        id="clover_hollow",
        place="Clover Hollow",
        opening="In Clover Hollow, mushroom lamps glowed softly beside a table set for neighbors and songs.",
        celebration="the Dewdrop Picnic",
        ending_image="the mushroom lamps shone warm and the grass bent in a sleepy shining ring",
        tags={"hollow", "picnic"},
    ),
}

ITEMS = {
    "ribbon_roll": MysteryItem(
        id="ribbon_roll",
        label="ribbon roll",
        phrase="a sky-blue ribbon roll",
        article="the ribbon roll",
        use_at_feast="to tie bright bows around the feast napkins",
        edible=False,
        tags={"ribbon", "borrowing"},
    ),
    "honey_cake": MysteryItem(
        id="honey_cake",
        label="honey cake",
        phrase="a round honey cake",
        article="the honey cake",
        use_at_feast="to sit in the middle of the table like a golden moon",
        edible=True,
        tags={"cake", "sharing"},
    ),
    "copper_pot": MysteryItem(
        id="copper_pot",
        label="copper pot",
        phrase="a polished copper pot",
        article="the copper pot",
        use_at_feast="to carry cinnamon soup while it was still steaming",
        edible=False,
        tags={"pot", "borrowing"},
    ),
}

CULPRITS = {
    "goat": Culprit(
        id="goat",
        label="Gib the goat",
        type="goat",
        wants_item="ribbon_roll",
        clue="blue_threads",
        clue_text="a curl of sky-blue thread snagged on a thorn",
        place="bramble_gate",
        comic_image="his beard had been tied into three bouncing bows, all of them much too tight",
        flashback="Then a flashback fluttered into {hero}'s mind: that morning Gib had groaned that his beard kept tangling in the dance bells.",
        explanation='"I only meant to borrow it," bleated Gib. "I wanted my beard to behave for the feast dance."',
        apology='"I should have asked first," he said, with a sheepish little bow that made the ribbons bob again.',
        tags={"goat", "ribbon", "humor"},
    ),
    "bear": Culprit(
        id="bear",
        label="Bram the bear cub",
        type="bear",
        wants_item="honey_cake",
        clue="sticky_crumbs",
        clue_text="golden crumbs stuck in a neat little trail",
        place="hollow_stump",
        comic_image="he was trying to pour tea for a pine-cone doll with one paw while keeping icing off his nose with the other",
        flashback="A flashback warmed {hero}'s thoughts: at breakfast Bram had sighed that his doll queen had a birthday and every proper party needed a cake.",
        explanation='"I wanted one grand surprise slice for my doll queen," mumbled Bram. "Then I thought maybe just a crumb. Then maybe two."',
        apology='"I was a muddle-headed cub," he said. "I should have asked, not nibbled."',
        tags={"bear", "cake", "humor"},
    ),
    "goose": Culprit(
        id="goose",
        label="Tilda the goose",
        type="goose",
        wants_item="copper_pot",
        clue="wet_prints",
        clue_text="a row of wet prints shining on the stones",
        place="lily_pond",
        comic_image="she had set the copper pot on her head like a knight's helmet, and two ducklings were saluting her",
        flashback="Then {hero} remembered, in a bright little flashback, how Tilda had honked that her ducklings wanted a captain for their boat parade.",
        explanation='"I borrowed it for one brave minute," honked Tilda. "A captain needs a helmet, and a pond parade needs a captain."',
        apology='"I ought to have asked before marching off with it," she admitted, lowering her beak.',
        tags={"goose", "pot", "humor"},
    ),
}

PLACES = {
    "bramble_gate": HidingPlace(
        id="bramble_gate",
        label="the bramble gate",
        trail_text="The trail skipped toward the bramble gate where blackberry vines laced themselves together.",
        arrival_text="Behind the gate, the thorns made a green curtain with one small gap near the roots.",
        helper_ids={"hedgehog"},
        tags={"bramble"},
    ),
    "hollow_stump": HidingPlace(
        id="hollow_stump",
        label="the hollow stump",
        trail_text="The trail curled past the bean patch to the old hollow stump at the edge of the path.",
        arrival_text="Inside the stump, it was dim and snug, with room for secrets and crumbs.",
        helper_ids={"squirrel"},
        tags={"stump"},
    ),
    "lily_pond": HidingPlace(
        id="lily_pond",
        label="the lily pond",
        trail_text="The trail went all the way to the lily pond where the reeds whispered together.",
        arrival_text="At the pond's edge, the water made small silver rings under the lily leaves.",
        helper_ids={"frog"},
        tags={"pond"},
    ),
}

HELPERS = {
    "hedgehog": Helper(
        id="hedgehog",
        label="Pip the hedgehog",
        type="hedgehog",
        style="snuffled close to the ground",
        find_text="Pip tucked his nose low, puffed himself narrow, and slipped through the thorn gap.",
        tags={"hedgehog", "helper"},
    ),
    "squirrel": Helper(
        id="squirrel",
        label="Nip the squirrel",
        type="squirrel",
        style="twitched her tail and peered into dark nooks",
        find_text="Nip darted up the stump, knocked twice, and peeped down through the hollow top.",
        tags={"squirrel", "helper"},
    ),
    "frog": Helper(
        id="frog",
        label="Plop the frog",
        type="frog",
        style="hopped where the mud still remembered feet",
        find_text="Plop gave one brave hop to a stone and pointed his chin toward the reeds.",
        tags={"frog", "helper"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Nora", "Elsie", "Tansy", "Wren", "Poppy", "Ivy"]
BOY_NAMES = ["Oren", "Theo", "Finn", "Milo", "Robin", "Bramble", "Jory", "Ned"]

KNOWLEDGE = {
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet, like a missing thing or a strange clue. You solve it by noticing details and thinking carefully.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back at something that happened earlier. It helps you understand what is happening now.",
        )
    ],
    "ribbon": [
        (
            "What can a ribbon be used for?",
            "A ribbon can tie bows, wrap gifts, or hold things together. It is soft, bendy, and useful for decorations.",
        )
    ],
    "cake": [
        (
            "Why do people share cake at a celebration?",
            "Cake is often shared because celebrations feel happier when everyone gets a piece. Sharing also turns one special treat into a group joy.",
        )
    ],
    "pot": [
        (
            "What is a pot for?",
            "A pot is used to carry or cook food. It is not really a helmet, even if a goose thinks it looks grand.",
        )
    ],
    "helper": [
        (
            "Why can a small helper matter in a story?",
            "A small helper can notice things other characters miss. Sometimes the cleverest help comes from the littlest friend.",
        )
    ],
    "sharing": [
        (
            "What should you do if you want to borrow something?",
            "You should ask first and wait for the answer. Asking shows respect, and it helps everyone trust each other.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "flashback", "ribbon", "cake", "pot", "helper", "sharing"]


def culprit_cfg(culprit_id: str) -> Culprit:
    if culprit_id not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {culprit_id})")
    return CULPRITS[culprit_id]


def item_cfg(item_id: str) -> MysteryItem:
    if item_id not in ITEMS:
        raise StoryError(f"(Unknown item: {item_id})")
    return ITEMS[item_id]


def helper_cfg(helper_id: str) -> Helper:
    if helper_id not in HELPERS:
        raise StoryError(f"(Unknown helper: {helper_id})")
    return HELPERS[helper_id]


def place_cfg(place_id: str) -> HidingPlace:
    if place_id not in PLACES:
        raise StoryError(f"(Unknown place: {place_id})")
    return PLACES[place_id]


def valid_combo(item_id: str, culprit_id: str, helper_id: str) -> bool:
    culprit = culprit_cfg(culprit_id)
    if item_id != culprit.wants_item:
        return False
    place = place_cfg(culprit.place)
    return helper_id in place.helper_ids


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for culprit_id, culprit in CULPRITS.items():
            place = place_cfg(culprit.place)
            for helper_id in sorted(place.helper_ids):
                out.append((setting_id, culprit.wants_item, culprit_id, helper_id))
    return sorted(out)


def ending_kind(item_id: str) -> str:
    item = item_cfg(item_id)
    return "shared" if item.edible else "returned"


def explain_invalid(item_id: str, culprit_id: str, helper_id: str) -> str:
    culprit = culprit_cfg(culprit_id)
    if item_id != culprit.wants_item:
        wanted = ITEMS[culprit.wants_item].label
        got = ITEMS[item_id].label
        return (
            f"(No story: {culprit.label} would not take the {got}. In this world, "
            f"{culprit.pronoun('subject') if isinstance(culprit, Entity) else 'the culprit'} "
            f"is only plausibly linked to the {wanted}.)"
        )
    place = place_cfg(culprit.place)
    if helper_id not in place.helper_ids:
        helper = helper_cfg(helper_id)
        good = ", ".join(sorted(place.helper_ids))
        return (
            f"(No story: {helper.label} is the wrong helper for {place.label}. "
            f"Try a helper that can reach or notice that place: {good}.)"
        )
    return "(No story: that combination does not make sense in this world.)"


ASP_RULES = r"""
% each culprit is only a plausible borrower of one item
valid_item(C, I) :- wants(C, I).

% the right helper must match the culprit's hiding place
valid_helper(C, H) :- hides_at(C, P), helper_for(P, H).

valid(S, I, C, H) :- setting(S), culprit(C), item(I), helper(H),
                     valid_item(C, I), valid_helper(C, H).

ending(shared)   :- chosen_item(I), edible(I).
ending(returned) :- chosen_item(I), not edible(I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.edible:
            lines.append(asp.fact("edible", iid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("wants", cid, culprit.wants_item))
        lines.append(asp.fact("hides_at", cid, culprit.place))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for hid in sorted(place.helper_ids):
            lines.append(asp.fact("helper_for", pid, hid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_ending(item_id: str) -> str:
    import asp

    model = asp.one_model(asp_program(f"{asp.fact('chosen_item', item_id)}", "#show ending/1."))
    atoms = asp.atoms(model, "ending")
    return atoms[0][0] if atoms else "?"


def predict_find(world: World) -> dict:
    sim = world.copy()
    sim.get("clue").meters["noticed"] += 1
    sim.get("helper").meters["guiding"] += 1
    propagate(sim, narrate=False)
    return {
        "progress": sim.get("hero").meters["search_progress"],
        "place": sim.facts.get("place_cfg").label,
    }


def introduce(world: World, hero: Entity, elder: Entity, item: Entity, item_def: MysteryItem) -> None:
    world.say(world.setting.opening)
    world.say(
        f"{hero.id} was helping {elder.label_word} set out supper for {world.setting.celebration}, "
        f"and {item_def.article} was meant {item_def.use_at_feast}."
    )
    hero.memes["joy"] += 1


def discover_missing(world: World, hero: Entity, item: Entity, item_def: MysteryItem) -> None:
    item.meters["missing"] += 1
    world.facts["mystery_started"] = True
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} reached for {item_def.article}, it was gone. Only the round place where it had rested still shone on the table."
    )
    world.say(
        f'{hero.id} blinked. "That is odd," {hero.pronoun()} whispered. "A feast thing cannot just grow feet and walk away."'
    )


def elder_trusts(world: World, hero: Entity, elder: Entity) -> None:
    elder.memes["trust"] += 1
    world.say(
        f'{elder.label_word.capitalize()} did not scold or fuss. "{hero.id}," {elder.pronoun()} said, '
        f'"look sharp and look kind. A mystery is easier when your heart stays gentle."'
    )


def notice_clue(world: World, hero: Entity, culprit: Culprit) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near the table leg, {hero.id} found {culprit.clue_text}. That was no ordinary scrap at all."
    )
    world.facts["clue_text"] = culprit.clue_text


def flashback(world: World, hero: Entity, culprit: Culprit) -> None:
    hero.memes["insight"] += 1
    line = culprit.flashback.format(hero=hero.id)
    world.say(line)
    world.say("The remembered moment did not solve everything, but it made the mystery feel smaller and brighter.")


def recruit_helper(world: World, hero: Entity, helper: Entity, helper_def: Helper) -> None:
    helper.memes["loyalty"] += 1
    world.say(
        f"So {hero.id} called for {helper_def.label}. {helper_def.find_text}"
    )
    world.say(
        f"{helper_def.label} {helper_def.style}, and {hero.id} followed close behind."
    )
    helper.meters["guiding"] += 1
    propagate(world, narrate=False)


def travel(world: World, place: HidingPlace) -> None:
    world.say(place.trail_text)
    world.say(place.arrival_text)


def reveal(world: World, hero: Entity, culprit_ent: Entity, culprit_def: Culprit, item_def: MysteryItem) -> None:
    culprit_ent.meters["found"] += 1
    world.say(
        f"Behold: there was {culprit_def.label}, and {culprit_def.comic_image}."
    )
    if item_def.edible:
        world.say(
            f"{hero.id} tried to look stern, but the sight was so silly that a laugh popped out first."
        )
    else:
        world.say(
            f"For one tiny moment, even the mystery forgot to be solemn."
        )


def explain(world: World, culprit_ent: Entity, culprit_def: Culprit, item: Entity, item_def: MysteryItem) -> None:
    culprit_ent.memes["embarrassment"] += 1
    world.say(culprit_def.explanation)
    world.say(culprit_def.apology)
    if item_def.edible:
        item.meters["nibbled"] += 1
    else:
        item.meters["borrowed"] += 1


def mend(world: World, hero: Entity, elder: Entity, culprit_ent: Entity, item: Entity, item_def: MysteryItem) -> None:
    if item_def.edible:
        item.meters["returned"] += 1
        item.meters["shared"] += 1
        world.say(
            f'{hero.id} held the plate steady and said, "Next time, ask. Today we can still mend it."'
        )
        world.say(
            f"{elder.label_word.capitalize()} cut the untouched part into neat pieces, and even the crooked slice looked grand once everyone agreed to share."
        )
    else:
        item.meters["returned"] += 1
        world.say(
            f'{hero.id} held out both hands, and {culprit_ent.label} gave back {item_def.article}.'
        )
        world.say(
            f"{hero.id} helped set things right, and the borrowed trouble became a laugh instead of a quarrel."
        )
    propagate(world, narrate=False)


def ending(world: World, hero: Entity, elder: Entity, culprit_def: Culprit, item_def: MysteryItem) -> None:
    hero.memes["joy"] += 1
    world.say(
        f'Soon the feast began after all. {elder.label_word.capitalize()} smiled at {hero.id} and said, '
        f'"You solved the puzzle without losing your kindness."'
    )
    if item_def.edible:
        world.say(
            f"{culprit_def.label} ate his slice politely this time, and nobody needed to hide dessert from him again."
        )
    else:
        world.say(
            f"{culprit_def.label} asked before borrowing anything else, which made the neighbors trust the next funny idea much more."
        )
    world.say(
        f"And in the soft evening, {world.setting.ending_image}."
    )


def tell(
    setting: Setting,
    item_def: MysteryItem,
    culprit_def: Culprit,
    helper_def: Helper,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    elder_name: str = "Grandma Vale",
    elder_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=["curious", "gentle"],
        )
    )
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_type,
            label=elder_name,
            role="elder",
            traits=["calm", "wise"],
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=item_def.label,
            role="missing_item",
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            kind="thing",
            type="clue",
            label=culprit_def.clue,
            role="clue",
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_def.type,
            label=helper_def.label,
            role="helper",
        )
    )
    culprit_ent = world.add(
        Entity(
            id="culprit",
            kind="character",
            type=culprit_def.type,
            label=culprit_def.label,
            role="culprit",
        )
    )
    world.facts.update(
        setting=setting,
        item_cfg=item_def,
        culprit_cfg=culprit_def,
        helper_cfg=helper_def,
        place_cfg=place_cfg(culprit_def.place),
        hero=hero,
        elder=elder,
        item=item,
        clue=clue,
        helper=helper,
        culprit=culprit_ent,
        ending_kind=ending_kind(item_def.id),
    )

    introduce(world, hero, elder, item, item_def)
    discover_missing(world, hero, item, item_def)
    elder_trusts(world, hero, elder)

    world.para()
    notice_clue(world, hero, culprit_def)
    flashback(world, hero, culprit_def)
    recruit_helper(world, hero, helper, helper_def)
    travel(world, place_cfg(culprit_def.place))

    world.para()
    reveal(world, hero, culprit_ent, culprit_def, item_def)
    explain(world, culprit_ent, culprit_def, item, item_def)
    mend(world, hero, elder, culprit_ent, item, item_def)

    world.para()
    ending(world, hero, elder, culprit_def, item_def)

    world.facts.update(
        mystery_solved=culprit_ent.meters["found"] >= THRESHOLD,
        item_returned=item.meters["returned"] >= THRESHOLD,
        item_shared=item.meters["shared"] >= THRESHOLD,
        clue_noticed=clue.meters["noticed"] >= THRESHOLD,
        progress=hero.meters["search_progress"],
        hero_relief=hero.memes["relief"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    helper = f["helper_cfg"]
    place = f["place_cfg"]
    setting = f["setting"]
    return [
        f'Write a fairy-tale mystery for a young child that includes the word "behold" and the word "tight". The missing object is {item.phrase}.',
        f"Tell a gentle, funny story set in {setting.place} where a child follows {culprit.clue_text} with help from {helper.label} and discovers a silly misunderstanding at {place.label}.",
        f"Write a fairy-tale with a flashback, a small mystery to solve, and a warm ending where borrowing is mended by kindness instead of anger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    helper = f["helper_cfg"]
    place = f["place_cfg"]
    end_kind = f["ending_kind"]

    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {item.article} disappeared just before {f['setting'].celebration}. {hero.label} had to figure out who took it and why before the feast could feel whole again.",
        ),
        (
            f"What clue did {hero.label} find?",
            f"{hero.label} found {culprit.clue_text}. That clue mattered because it pointed away from the table and toward the real borrower.",
        ),
        (
            f"How did the flashback help {hero.label} solve the mystery?",
            f"The flashback reminded {hero.label} of the culprit's earlier problem, so the clue suddenly made more sense. It did not give the whole answer by itself, but it helped {hero.pronoun()} guess the right reason for the borrowing.",
        ),
        (
            f"How did {helper.label} help?",
            f"{helper.label} helped lead {hero.label} to {place.label}. Without that small helper, the clue might have stayed only a guess instead of becoming a real discovery.",
        ),
    ]
    if end_kind == "shared":
        qa.append(
            (
                f"Why had {culprit.label} taken the {item.label}?",
                f"{culprit.label} wanted it for a silly private celebration and then nibbled before asking. In the end, the problem was mended by sharing what was left and telling the truth.",
            )
        )
    else:
        qa.append(
            (
                f"Why had {culprit.label} taken the {item.label}?",
                f"{culprit.label} borrowed it to solve a funny little problem and forgot that borrowing still needs permission. Once {hero.label} found {culprit.pronoun('object')}, the item was returned and the joke became safe to laugh at.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the feast beginning after the mystery was solved. The ending shows that kindness held the village together more tightly than blame would have done.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item = f["item_cfg"]
    tags = {"mystery", "flashback", "helper", "sharing"} | set(item.tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moonwell",
        item="ribbon_roll",
        culprit="goat",
        helper="hedgehog",
        hero="Mira",
        hero_gender="girl",
        elder="Grandma Vale",
        elder_type="mother",
    ),
    StoryParams(
        setting="thimble_castle",
        item="honey_cake",
        culprit="bear",
        helper="squirrel",
        hero="Theo",
        hero_gender="boy",
        elder="Cook Rowan",
        elder_type="father",
    ),
    StoryParams(
        setting="clover_hollow",
        item="copper_pot",
        culprit="goose",
        helper="frog",
        hero="Lila",
        hero_gender="girl",
        elder="Aunt Fen",
        elder_type="mother",
    ),
]


def explain_gender(name: str, gender: str) -> str:
    return f"(No story: the name {name!r} does not fit the requested gender {gender!r} in this tiny world.)"


def outcome_of(params: StoryParams) -> str:
    return ending_kind(params.item)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale mystery world: a missing feast object, a clue, a flashback, and a humorous reveal."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.culprit and args.helper:
        if not valid_combo(args.item, args.culprit, args.helper):
            raise StoryError(explain_invalid(args.item, args.culprit, args.helper))

    filtered = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not filtered:
        if args.item and args.culprit and args.helper:
            raise StoryError(explain_invalid(args.item, args.culprit, args.helper))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, culprit_id, helper_id = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    default_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero = args.hero or rng.choice(default_pool)
    elder = args.elder or rng.choice(["Grandma Vale", "Aunt Fen"] if args.parent != "father" else ["Cook Rowan", "Uncle Thorn"])
    elder_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        item=item_id,
        culprit=culprit_id,
        helper=helper_id,
        hero=hero,
        hero_gender=gender,
        elder=elder,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not valid_combo(params.item, params.culprit, params.helper):
        raise StoryError(explain_invalid(params.item, params.culprit, params.helper))

    world = tell(
        setting=SETTINGS[params.setting],
        item_def=ITEMS[params.item],
        culprit_def=CULPRITS[params.culprit],
        helper_def=HELPERS[params.helper],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        elder_name=params.elder,
        elder_type=params.elder_type,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combo gate matches ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    bad = []
    for iid in ITEMS:
        if asp_ending(iid) != ending_kind(iid):
            bad.append((iid, asp_ending(iid), ending_kind(iid)))
    if not bad:
        print("OK: ending-kind model matches for all items.")
    else:
        rc = 1
        print("MISMATCH in ending-kind model:", bad)

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        auto = resolve_params(build_parser().parse_args([]), random.Random(7))
        auto.seed = 7
        auto_sample = generate(auto)
        if not auto_sample.story.strip():
            raise StoryError("(Smoke test failed: default generation produced empty story.)")
        print("OK: smoke test passed for curated and default generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, culprit, helper) combos:\n")
        for setting_id, item_id, culprit_id, helper_id in combos:
            print(f"  {setting_id:15} {item_id:12} {culprit_id:8} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.hero}: {p.item} / {p.culprit} / {p.helper} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
