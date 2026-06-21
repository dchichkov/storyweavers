#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crawl_mystery_to_solve_happy_ending_folk.py
======================================================================

A standalone story world for a small folk-tale mystery: something needed for a
village feast goes missing, a child follows kind-hearted clues, must crawl into
a hidden place, discovers the "thief" was trying to help someone, and solves the
mystery with generosity. Every valid story ends happily, but the world still has
explicit reasonableness gates for implausible pairings and unkind responses.

Run it
------
    python storyworlds/worlds/gpt-5.4/crawl_mystery_to_solve_happy_ending_folk.py
    python storyworlds/worlds/gpt-5.4/crawl_mystery_to_solve_happy_ending_folk.py --item bell --culprit magpie
    python storyworlds/worlds/gpt-5.4/crawl_mystery_to_solve_happy_ending_folk.py --item loaf --culprit magpie
    python storyworlds/worlds/gpt-5.4/crawl_mystery_to_solve_happy_ending_folk.py --response scold
    python storyworlds/worlds/gpt-5.4/crawl_mystery_to_solve_happy_ending_folk.py --all --qa
    python storyworlds/worlds/gpt-5.4/crawl_mystery_to_solve_happy_ending_folk.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "aunt": "aunt"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    path: str
    ending: str
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
    phrase: str
    needed_for: str
    trait: str
    clue_kind: str
    likes: set[str] = field(default_factory=set)
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
    clue_kind: str
    clue_text: str
    likes: set[str] = field(default_factory=set)
    hideout: str = ""
    need: str = ""
    need_text: str = ""
    gift: str = ""
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
class Hideout:
    id: str
    label: str
    entrance: str
    crawl_text: str
    inside_text: str
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
    helps: set[str] = field(default_factory=set)
    offer_text: str = ""
    solve_text: str = ""
    qa_text: str = ""
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "clue_seen": False,
            "predicted_culprit": "",
            "need_known": False,
            "item_returned": False,
            "celebration": False,
        }

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


def _r_missing_worry(world: World) -> list[str]:
    item = world.entities.get("item")
    elder = world.entities.get("elder")
    if item is None or elder is None:
        return []
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["worry"] += 1
    world.facts["mystery"] = True
    return []


def _r_clue_curiosity(world: World) -> list[str]:
    solver = world.entities.get("solver")
    clue = world.entities.get("clue")
    if solver is None or clue is None:
        return []
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_curiosity", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    solver.memes["curiosity"] += 1
    solver.memes["hope"] += 1
    world.facts["clue_seen"] = True
    return []


def _r_kindness_resolution(world: World) -> list[str]:
    solver = world.entities.get("solver")
    culprit = world.entities.get("culprit")
    item = world.entities.get("item")
    if solver is None or culprit is None or item is None:
        return []
    if culprit.meters["helped"] < THRESHOLD or item.meters["returned"] < THRESHOLD:
        return []
    sig = ("kindness_resolution", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    solver.memes["relief"] += 1
    solver.memes["joy"] += 1
    culprit.memes["gratitude"] += 1
    culprit.memes["trust"] += 1
    world.facts["item_returned"] = True
    world.facts["celebration"] = True
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="clue_curiosity", tag="social", apply=_r_clue_curiosity),
    Rule(name="kindness_resolution", tag="social", apply=_r_kindness_resolution),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "village_green": Setting(
        id="village_green",
        place="the village green",
        opening="In a valley village where smoke rose gently from round chimneys, every path seemed to know an old song.",
        path="Beyond the green lay a tangle of roots, moss, and berry canes.",
        ending="By evening the green glowed with lanterns, and the whole village looked softer and kinder than before.",
        tags={"village", "feast"},
    ),
    "mill_lane": Setting(
        id="mill_lane",
        place="Mill Lane",
        opening="On Mill Lane, where the waterwheel groaned like a sleepy giant, the villagers were preparing a merry evening feast.",
        path="Past the mill ran a narrow bank where reeds bowed over dark water.",
        ending="At sunset the wheel turned gold, and the lane hummed with thankful voices.",
        tags={"mill", "feast"},
    ),
    "orchard_square": Setting(
        id="orchard_square",
        place="orchard square",
        opening="Near the orchard square, apples shone like little lamps among the leaves, and everyone was busy with feast-day work.",
        path="Behind the square stretched a low hedge and a ferny hollow where small creatures could vanish in a blink.",
        ending="When dusk came, the square smelled of apples and bread, and laughter skipped from tree to tree.",
        tags={"orchard", "feast"},
    ),
}

ITEMS = {
    "bell": MissingItem(
        id="bell",
        label="bell",
        phrase="the little brass bell",
        needed_for="ringing the feast open",
        trait="shiny",
        clue_kind="feather",
        likes={"shiny"},
        tags={"bell", "festival"},
    ),
    "loaf": MissingItem(
        id="loaf",
        label="honey loaf",
        phrase="the round honey loaf",
        needed_for="the first feast supper",
        trait="sweet",
        clue_kind="crumb",
        likes={"food"},
        tags={"bread", "festival"},
    ),
    "shawl": MissingItem(
        id="shawl",
        label="red shawl",
        phrase="the red shawl",
        needed_for="wrapping the elder's shoulders at the story fire",
        trait="soft",
        clue_kind="hoofprint",
        likes={"soft"},
        tags={"cloth", "festival"},
    ),
}

CULPRITS = {
    "magpie": Culprit(
        id="magpie",
        label="a glossy magpie",
        type="bird",
        clue_kind="feather",
        clue_text="a black-and-white feather with a bit of dawn light on it",
        likes={"shiny"},
        hideout="oak_hollow",
        need="nest",
        need_text="Its nest had slipped crooked in the wind, and the bright bell was wedged there, keeping two wobbling chicks from tumbling out.",
        gift="a silver-gray feather",
        tags={"bird", "nest"},
    ),
    "hedgehog": Culprit(
        id="hedgehog",
        label="a round hedgehog mother",
        type="animal",
        clue_kind="crumb",
        clue_text="a scatter of sweet crumbs no bigger than raindrops",
        likes={"food"},
        hideout="bramble_burrow",
        need="hunger",
        need_text="Three tiny hoglets were huddled inside, hungry and squeaking, and the warm loaf had been dragged there for them.",
        gift="a glossy blackberry",
        tags={"hedgehog", "food"},
    ),
    "fawn": Culprit(
        id="fawn",
        label="a shy fawn",
        type="animal",
        clue_kind="hoofprint",
        clue_text="two delicate hoofprints pressed beside a torn red thread",
        likes={"soft"},
        hideout="willow_den",
        need="cold",
        need_text="Under the branches lay its little brother, still shivering from the morning mist, with the shawl tucked around him like a sunset cloud.",
        gift="a garland of willow leaves",
        tags={"deer", "warmth"},
    ),
}

HIDEOUTS = {
    "oak_hollow": Hideout(
        id="oak_hollow",
        label="the hollow oak",
        entrance="a split in the old oak roots",
        crawl_text="To reach it, the child had to get on hands and knees and crawl through the root-arch, where earth smelled cool and deep.",
        inside_text="Inside the hollow, green light fell through a crack in the bark.",
        tags={"tree"},
    ),
    "bramble_burrow": Hideout(
        id="bramble_burrow",
        label="the bramble burrow",
        entrance="a round opening under the berries",
        crawl_text="The opening was so low that the child had to crawl through the bramble tunnel, careful not to shake loose the dew.",
        inside_text="Inside the burrow it was snug and dim, smelling of leaves and rain.",
        tags={"burrow"},
    ),
    "willow_den": Hideout(
        id="willow_den",
        label="the willow den",
        entrance="a curtain of hanging willow branches",
        crawl_text="Beneath the branches, the child had to crawl along a green little tunnel where the ground was soft with moss.",
        inside_text="Inside the willow den, the light was green as pond water and quiet as a held breath.",
        tags={"willow"},
    ),
}

RESPONSES = {
    "untangle": Response(
        id="untangle",
        sense=3,
        helps={"nest"},
        offer_text="gently lifted and tucked the broken nest back into a safe fork of the tree",
        solve_text="Once the nest was steady, the magpie nudged the bell free at once",
        qa_text="steadied the nest so the bell could be given back",
        tags={"kindness", "repair"},
    ),
    "share_food": Response(
        id="share_food",
        sense=3,
        helps={"hunger"},
        offer_text="broke an apple cake in two and set the sweet pieces beside the hoglets",
        solve_text="With fresh food beside her babies, the hedgehog pushed the loaf back with her nose",
        qa_text="shared food so the hedgehog could return the loaf",
        tags={"kindness", "food"},
    ),
    "bring_blanket": Response(
        id="bring_blanket",
        sense=3,
        helps={"cold"},
        offer_text="ran home for a patched wool blanket and wrapped the little brother snugly in it",
        solve_text="When the fawn saw real warmth had come, it folded the shawl neatly and offered it back",
        qa_text="brought a blanket so the shawl could be returned",
        tags={"kindness", "warmth"},
    ),
    "scold": Response(
        id="scold",
        sense=1,
        helps=set(),
        offer_text="pointed a sharp finger and scolded the animal",
        solve_text="nothing gentle was mended",
        qa_text="scolded instead of helping",
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Tali", "Nell", "Pia", "Lina", "Suri", "Etta"]
BOY_NAMES = ["Ivo", "Milan", "Tobin", "Pavel", "Niko", "Oren", "Bram", "Luka"]
TRAITS = ["patient", "bright-eyed", "gentle", "curious", "steady", "kind"]
ELDER_TYPES = ["grandmother", "grandfather", "aunt"]


def valid_combo(item_id: str, culprit_id: str) -> bool:
    if item_id not in ITEMS or culprit_id not in CULPRITS:
        return False
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    return item.clue_kind == culprit.clue_kind and bool(item.likes & culprit.likes)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id in ITEMS:
            for culprit_id in CULPRITS:
                if valid_combo(item_id, culprit_id):
                    combos.append((setting_id, item_id, culprit_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_fits(culprit_id: str, response_id: str) -> bool:
    if culprit_id not in CULPRITS or response_id not in RESPONSES:
        return False
    return CULPRITS[culprit_id].need in RESPONSES[response_id].helps


def best_response_for(culprit_id: str) -> Optional[str]:
    options = [
        r.id for r in sensible_responses()
        if response_fits(culprit_id, r.id)
    ]
    return sorted(options)[0] if options else None


def outcome_of(params: "StoryParams") -> str:
    return "restored" if response_fits(params.culprit, params.response) else "stalled"


def predict_culprit_from_clue(world: World, clue_kind: str) -> str:
    for culprit_id, culprit in CULPRITS.items():
        if culprit.clue_kind == clue_kind:
            return culprit_id
    return ""


def discover_missing(world: World, elder: Entity, item_cfg: MissingItem) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"One morning, when the feast baskets were being lined up in {world.setting.place}, "
        f"{elder.id} suddenly clasped both hands. {item_cfg.phrase.capitalize()} was gone."
    )
    world.say(
        f'"Without it, we cannot finish {item_cfg.needed_for}," {elder.label_word} said, '
        f"and worry sat over the square like a small gray cloud."
    )


def volunteer(world: World, solver: Entity, elder: Entity) -> None:
    solver.memes["bravery"] += 1
    world.say(
        f'{solver.id}, a {solver.type} with a {solver.attrs["trait"]} heart, stepped forward. '
        f'"I will look for it," {solver.pronoun()} said.'
    )
    world.say(
        f"{elder.id} nodded and told {solver.pronoun('object')} to keep sharp eyes and a kind voice, "
        f"for old village mysteries were seldom as simple as they first appeared."
    )


def notice_clue(world: World, solver: Entity, item_cfg: MissingItem, culprit_cfg: Culprit) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_culprit"] = predict_culprit_from_clue(world, item_cfg.clue_kind)
    world.say(
        f"Near the empty basket, {solver.id} found {culprit_cfg.clue_text}."
    )
    world.say(
        f"That was no common accident. At once {solver.pronoun()} guessed the trail might lead to {culprit_cfg.label}."
    )


def follow_trail(world: World, solver: Entity, hideout_cfg: Hideout, culprit_cfg: Culprit) -> None:
    solver.memes["curiosity"] += 1
    world.say(world.setting.path)
    world.say(
        f"{solver.id} followed the sign of the mystery to {hideout_cfg.entrance}, the mouth of {hideout_cfg.label}."
    )
    world.say(hideout_cfg.crawl_text)
    world.say(hideout_cfg.inside_text)


def reveal_need(world: World, solver: Entity, item_cfg: MissingItem, culprit_cfg: Culprit) -> None:
    culprit = world.get("culprit")
    culprit.meters["holding_item"] += 1
    culprit.meters["need"] += 1
    world.facts["need_known"] = True
    world.say(
        f"There {solver.pronoun()} found {culprit_cfg.label} beside {item_cfg.phrase}. {culprit_cfg.need_text}"
    )
    world.say(
        f"Then {solver.id} understood the truth: this was not a greedy theft, only a hurried act of care."
    )


def help_kindly(world: World, solver: Entity, response_cfg: Response, culprit_cfg: Culprit) -> None:
    culprit = world.get("culprit")
    culprit.meters["helped"] += 1
    solver.memes["kindness"] += 1
    world.say(
        f"So {solver.id} {response_cfg.offer_text}."
    )
    world.say(
        f"{response_cfg.solve_text}, and the hard part of the mystery melted away."
    )


def return_item(world: World, solver: Entity, culprit_cfg: Culprit, item_cfg: MissingItem) -> None:
    item = world.get("item")
    item.meters["returned"] += 1
    item.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{culprit_cfg.label.capitalize()} placed {item_cfg.phrase} into {solver.id}'s hands and left {culprit_cfg.gift} as a shy thank-you."
    )


def feast_ending(world: World, solver: Entity, elder: Entity, item_cfg: MissingItem, culprit_cfg: Culprit) -> None:
    solver.memes["joy"] += 1
    world.say(
        f"When {solver.id} came back to {world.setting.place}, {elder.id} smiled so wide that the worry lines vanished from {elder.pronoun('possessive')} face."
    )
    world.say(
        f"Soon {item_cfg.phrase} was in its proper place, {item_cfg.needed_for} at last, and {solver.id} told the true tale of {culprit_cfg.label}."
    )
    world.say(
        f"No one spoke of punishment. Instead, the villagers sent a little kindness back to the hidden place, and {world.setting.ending}"
    )


def tell(
    setting: Setting,
    item_cfg: MissingItem,
    culprit_cfg: Culprit,
    response_cfg: Response,
    solver_name: str = "Anya",
    solver_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "patient",
) -> World:
    hideout_cfg = HIDEOUTS[culprit_cfg.hideout]
    world = World(setting)
    solver = world.add(Entity(
        id=solver_name,
        kind="character",
        type=solver_gender,
        label=solver_name,
        role="solver",
        attrs={"trait": trait},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        role="missing_item",
        attrs={"needed_for": item_cfg.needed_for, "trait": item_cfg.trait},
        tags=set(item_cfg.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=item_cfg.clue_kind,
        role="clue",
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type=culprit_cfg.type,
        label=culprit_cfg.label,
        role="culprit",
        attrs={"need": culprit_cfg.need},
        tags=set(culprit_cfg.tags),
    ))

    world.facts.update(
        setting=setting,
        item_cfg=item_cfg,
        culprit_cfg=culprit_cfg,
        hideout_cfg=hideout_cfg,
        response_cfg=response_cfg,
        solver=solver,
        elder=elder,
        culprit=culprit,
        item=item,
    )

    world.say(setting.opening)
    world.say(
        f"In that place lived {solver.id}, a {solver.attrs['trait']} child who listened when others hurried past."
    )

    world.para()
    discover_missing(world, elder, item_cfg)
    volunteer(world, solver, elder)

    world.para()
    notice_clue(world, solver, item_cfg, culprit_cfg)
    follow_trail(world, solver, hideout_cfg, culprit_cfg)
    reveal_need(world, solver, item_cfg, culprit_cfg)

    world.para()
    help_kindly(world, solver, response_cfg, culprit_cfg)
    return_item(world, solver, culprit_cfg, item_cfg)
    feast_ending(world, solver, elder, item_cfg, culprit_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    item_cfg = world.facts["item_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    setting = world.facts["setting"]
    solver = world.facts["solver"]
    return [
        f'Write a short folk tale for a young child about a missing {item_cfg.label}, a mystery to solve, and a happy ending. Include the word "crawl".',
        f"Tell a gentle village mystery where {solver.id} follows clues in {setting.place}, must crawl into a hidden place, and discovers that {culprit_cfg.label} needs help rather than blame.",
        f"Write a simple old-fashioned tale in which kindness solves the mystery of {item_cfg.phrase} and brings the whole village to a happy feast.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    solver = world.facts["solver"]
    elder = world.facts["elder"]
    item_cfg = world.facts["item_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    hideout_cfg = world.facts["hideout_cfg"]
    response_cfg = world.facts["response_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {item_cfg.phrase} disappeared before the feast. It mattered because the village needed it for {item_cfg.needed_for}.",
        ),
        (
            f"How did {solver.id} begin to solve the mystery?",
            f"{solver.id} found {culprit_cfg.clue_text} near the empty basket. That clue pointed toward {culprit_cfg.label} and gave {solver.pronoun('object')} a trail to follow.",
        ),
        (
            f"Where did {solver.id} go, and why did {solver.pronoun()} have to crawl?",
            f"{solver.pronoun().capitalize()} followed the trail to {hideout_cfg.label}. The entrance was so low and hidden that {solver.pronoun()} had to crawl to get inside and see the truth.",
        ),
        (
            f"Why had {culprit_cfg.label} taken the {item_cfg.label}?",
            f"{culprit_cfg.label.capitalize()} had not taken it out of meanness. {culprit_cfg.need_text}",
        ),
        (
            f"How was the mystery solved happily?",
            f"{solver.id} {response_cfg.qa_text}. Because {solver.pronoun()} helped instead of scolding, {item_cfg.phrase} was returned and the feast could begin.",
        ),
        (
            "What changed by the end of the story?",
            f"At first the village was worried and confused, but by the end everyone understood the truth and chose kindness. That turned a missing thing into a happy ending for both the village and {culprit_cfg.label}.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "bell": [(
        "What is a brass bell?",
        "A brass bell is a small metal bell that rings when it is shaken. People often use bells to call others together."
    )],
    "bread": [(
        "Why does warm bread smell strong?",
        "Warm bread sends little smells into the air as it cools. That is why animals and people can notice it quickly."
    )],
    "cloth": [(
        "Why does a shawl help someone feel warm?",
        "A shawl is a piece of cloth you wrap around shoulders or a body. It helps keep warm air close and cold air out."
    )],
    "bird": [(
        "Why do birds build nests up high?",
        "Birds build nests in safe places so their eggs or chicks are harder for danger to reach. Twigs and grass help hold the nest together."
    )],
    "hedgehog": [(
        "What is a hedgehog?",
        "A hedgehog is a small animal with prickles on its back. It curls up when it feels afraid and likes snug hiding places."
    )],
    "deer": [(
        "What is a fawn?",
        "A fawn is a young deer. It has small legs, soft fur, and often hides quietly in grass or under branches."
    )],
    "crawl": [(
        "What does crawl mean?",
        "To crawl means to move low to the ground on hands and knees, or in a slow close way. People crawl when a space is too small to walk through."
    )],
    "kindness": [(
        "Why can kindness solve a problem better than anger?",
        "Kindness helps people understand what is really wrong. When someone feels safe, it is easier to fix the problem together."
    )],
    "feast": [(
        "What is a feast?",
        "A feast is a special meal or celebration where many people gather together. A village feast often has food, music, and stories."
    )],
}
KNOWLEDGE_ORDER = ["crawl", "feast", "bell", "bread", "cloth", "bird", "hedgehog", "deer", "kindness"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item_cfg = world.facts["item_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    tags = {"crawl", "kindness", "feast"} | set(item_cfg.tags) | set(culprit_cfg.tags)
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
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in sorted(world.facts.items()) if k not in {'solver', 'elder', 'culprit', 'item', 'setting', 'item_cfg', 'culprit_cfg', 'hideout_cfg', 'response_cfg'})}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    setting: str
    item: str
    culprit: str
    response: str
    solver_name: str
    solver_gender: str
    elder_type: str
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


CURATED = [
    StoryParams(
        setting="village_green",
        item="bell",
        culprit="magpie",
        response="untangle",
        solver_name="Anya",
        solver_gender="girl",
        elder_type="grandmother",
        trait="patient",
    ),
    StoryParams(
        setting="mill_lane",
        item="loaf",
        culprit="hedgehog",
        response="share_food",
        solver_name="Tobin",
        solver_gender="boy",
        elder_type="aunt",
        trait="gentle",
    ),
    StoryParams(
        setting="orchard_square",
        item="shawl",
        culprit="fawn",
        response="bring_blanket",
        solver_name="Mira",
        solver_gender="girl",
        elder_type="grandfather",
        trait="bright-eyed",
    ),
]


def explain_combo_rejection(item_id: str, culprit_id: str) -> str:
    if item_id not in ITEMS or culprit_id not in CULPRITS:
        return "(No story: unknown item or culprit.)"
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    if item.clue_kind != culprit.clue_kind:
        return (
            f"(No story: {item.phrase} would leave a {item.clue_kind} trail in this world, "
            f"but {culprit.label} is linked to {culprit.clue_kind} clues. The mystery would not point honestly toward that culprit.)"
        )
    if not (item.likes & culprit.likes):
        return (
            f"(No story: {culprit.label} would not reasonably take {item.phrase}. "
            f"The item's pull and the culprit's liking do not match.)"
        )
    return "(No story: this item and culprit do not make a reasonable mystery together.)"


def explain_response_rejection(culprit_id: str, response_id: str) -> str:
    if response_id not in RESPONSES:
        return "(No story: unknown response.)"
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response_id}': it scores too low on kindness and common sense "
            f"(sense={response.sense} < {SENSE_MIN}). This world only tells gentle, repairing endings.)"
        )
    culprit = CULPRITS.get(culprit_id)
    if culprit is None:
        return "(No story: unknown culprit.)"
    return (
        f"(No story: response '{response_id}' does not solve {culprit.label}'s problem. "
        f"The ending must mend the real need, not just take the item back.)"
    )


ASP_RULES = r"""
valid_item_culprit(I,C) :- item(I), culprit(C), clue_kind(I,K), culprit_clue(C,K), likes(I,L), culprit_likes(C,L).
valid(S,I,C) :- setting(S), valid_item_culprit(I,C).

sensible_response(R) :- response(R), sense(R,S), sense_min(M), S >= M.
fits(C,R) :- culprit(C), response(R), need(C,N), helps(R,N).

outcome(restored) :- chosen_culprit(C), chosen_response(R), fits(C,R), sensible_response(R).
outcome(stalled)  :- chosen_culprit(C), chosen_response(R), not fits(C,R).
outcome(stalled)  :- chosen_response(R), not sensible_response(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("clue_kind", item_id, item.clue_kind))
        for like in sorted(item.likes):
            lines.append(asp.fact("likes", item_id, like))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("culprit_clue", culprit_id, culprit.clue_kind))
        lines.append(asp.fact("need", culprit_id, culprit.need))
        for like in sorted(culprit.likes):
            lines.append(asp.fact("culprit_likes", culprit_id, like))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        for need in sorted(response.helps):
            lines.append(asp.fact("helps", response_id, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_responses() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    emit(sample, trace=False, qa=False, header="")


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

    clingo_sensible = set(asp_sensible_responses())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
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
        _smoke_generate()
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale mystery world: a missing feast item, a clue trail, a crawl into a hidden place, and a kind happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDER_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.culprit and not valid_combo(args.item, args.culprit):
        raise StoryError(explain_combo_rejection(args.item, args.culprit))
    if args.response:
        if RESPONSES[args.response].sense < SENSE_MIN:
            culprit_id = args.culprit or sorted(CULPRITS)[0]
            raise StoryError(explain_response_rejection(culprit_id, args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, culprit_id = rng.choice(sorted(combos))
    if args.response is not None:
        response_id = args.response
        if not response_fits(culprit_id, response_id):
            raise StoryError(explain_response_rejection(culprit_id, response_id))
    else:
        fitted = [r.id for r in sensible_responses() if response_fits(culprit_id, r.id)]
        if not fitted:
            raise StoryError("(No sensible response matches the culprit's need.)")
        response_id = rng.choice(sorted(fitted))

    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    elder_type = args.elder or rng.choice(ELDER_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        culprit=culprit_id,
        response=response_id,
        solver_name=name,
        solver_gender=gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if not valid_combo(params.item, params.culprit):
        raise StoryError(explain_combo_rejection(params.item, params.culprit))
    if RESPONSES[params.response].sense < SENSE_MIN or not response_fits(params.culprit, params.response):
        raise StoryError(explain_response_rejection(params.culprit, params.response))

    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        culprit_cfg=CULPRITS[params.culprit],
        response_cfg=RESPONSES[params.response],
        solver_name=params.solver_name,
        solver_gender=params.solver_gender,
        elder_type=params.elder_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_response/1.\n#show fits/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible_responses()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (setting, item, culprit) combos:\n")
        for setting_id, item_id, culprit_id in combos:
            best = best_response_for(culprit_id)
            print(f"  {setting_id:14} {item_id:8} {culprit_id:10}  response={best}")
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
            header = f"### {p.solver_name}: {p.item} / {p.culprit} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
