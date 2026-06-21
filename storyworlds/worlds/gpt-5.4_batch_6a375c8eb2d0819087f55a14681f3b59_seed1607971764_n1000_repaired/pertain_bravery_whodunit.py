#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pertain_bravery_whodunit.py
=====================================================

A standalone story world for a gentle whodunit: something important for a
children's show goes missing, a clue points the way, and a child must be brave
enough to follow the clue into a hiding place and ask a kind question.

The world is built from simulated state rather than frozen templates:
- a case item is hidden after being damaged by accident
- a clue that *pertains* to that item is left behind
- a child investigator follows the clue
- dark hiding places require a real light source
- bravery changes how the search is carried out
- the culprit confesses, a grown-up helps mend the item, and the ending proves
  what changed

Run it
------
    python storyworlds/worlds/gpt-5.4/pertain_bravery_whodunit.py
    python storyworlds/worlds/gpt-5.4/pertain_bravery_whodunit.py --case rabbit_mask --place curtain_nook
    python storyworlds/worlds/gpt-5.4/pertain_bravery_whodunit.py --place costume_trunk --tool none
    python storyworlds/worlds/gpt-5.4/pertain_bravery_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/pertain_bravery_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pertain_bravery_whodunit.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class CaseFile:
    id: str
    label: str
    phrase: str
    event: str
    damage: str
    repair: str
    clue_id: str
    opening: str
    ending: str
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    dark: bool
    spooky: str
    discovery: str
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
class Clue:
    id: str
    label: str
    phrase: str
    pertains_to: str
    spot: str
    inference: str
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
class Tool:
    id: str
    label: str
    phrase: str
    gives_light: bool
    use_text: str
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
class StoryParams:
    case: str
    place: str
    clue: str
    tool: str
    investigator: str
    investigator_gender: str
    culprit: str
    culprit_gender: str
    helper: str
    helper_gender: str
    adult: str
    bravery: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_clue_points(world: World) -> list[str]:
    clue_ent = world.get("clue")
    item = world.get("item")
    culprit = world.get("culprit")
    investigator = world.get("investigator")
    if clue_ent.meters["noticed"] < THRESHOLD:
        return []
    if item.attrs.get("expected_clue") != clue_ent.attrs.get("clue_id"):
        return []
    sig = ("clue_points", clue_ent.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["suspected"] += 1
    investigator.memes["certainty"] += 1
    world.facts["suspect_named"] = culprit.id
    return ["__clue__"]


def _r_lit_courage(world: World) -> list[str]:
    place = world.get("place")
    tool = world.get("tool")
    investigator = world.get("investigator")
    helper = world.get("helper")
    if place.meters["searched"] < THRESHOLD or place.attrs.get("dark") is not True:
        return []
    if not tool.attrs.get("gives_light"):
        return []
    sig = ("lit_courage", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    investigator.memes["bravery"] += 1
    investigator.memes["fear"] = max(0.0, investigator.memes["fear"] - 1.0)
    helper.memes["support"] += 1
    return ["__light__"]


def _r_kind_confession(world: World) -> list[str]:
    culprit = world.get("culprit")
    investigator = world.get("investigator")
    item = world.get("item")
    if culprit.memes["guilt"] < THRESHOLD:
        return []
    if culprit.memes["suspected"] < THRESHOLD:
        return []
    if investigator.memes["kindness"] < THRESHOLD:
        return []
    sig = ("kind_confession", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["honesty"] += 1
    item.meters["found"] += 1
    return ["__confess__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="clue_points", tag="reasoning", apply=_r_clue_points),
    Rule(name="lit_courage", tag="emotion", apply=_r_lit_courage),
    Rule(name="kind_confession", tag="social", apply=_r_kind_confession),
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


CASES = {
    "parade_star": CaseFile(
        id="parade_star",
        label="parade star",
        phrase="the big gold parade star",
        event="the opening march",
        damage="one point had bent and wrinkled",
        repair="smooth the point and press on a strip of fresh gold tape",
        clue_id="gold_sparkles",
        opening="hung over the stage door and told everyone where to line up",
        ending="The gold star gleamed above the line again as the opening march began.",
        tags={"show", "star", "repair"},
    ),
    "rabbit_mask": CaseFile(
        id="rabbit_mask",
        label="rabbit mask",
        phrase="the white rabbit mask",
        event="the animal song",
        damage="its side strap had slipped loose",
        repair="tie on a fresh blue ribbon so it would sit straight again",
        clue_id="blue_ribbon",
        opening="was the silliest prop in the basket, with long floppy ears",
        ending="When the song started, the rabbit mask bobbed happily in time with the music.",
        tags={"show", "mask", "repair"},
    ),
    "silver_bell": CaseFile(
        id="silver_bell",
        label="silver bell",
        phrase="the shiny silver bell",
        event="the quiet parade turn",
        damage="the handle wrap had come undone",
        repair="wind the handle tight with silver thread so it would not slip",
        clue_id="silver_thread",
        opening="was meant to ring once at the hush before the children stepped out",
        ending="The silver bell gave one clear note, and every child smiled at the sound.",
        tags={"show", "bell", "repair"},
    ),
}

PLACES = {
    "costume_trunk": HidingPlace(
        id="costume_trunk",
        label="costume trunk",
        phrase="the big costume trunk by the curtain",
        dark=True,
        spooky="The trunk stood in a dim corner where the curtain made a little cave of shadow.",
        discovery="inside the trunk, half hidden under a feather cape",
        tags={"trunk", "dark"},
    ),
    "curtain_nook": HidingPlace(
        id="curtain_nook",
        label="curtain nook",
        phrase="the nook behind the heavy red curtain",
        dark=True,
        spooky="Behind the curtain, the air felt still and hushed, and the stage light barely reached.",
        discovery="behind the curtain, crouched beside a box of spare tape",
        tags={"curtain", "dark"},
    ),
    "reading_bench": HidingPlace(
        id="reading_bench",
        label="reading bench",
        phrase="the reading bench under the window",
        dark=False,
        spooky="Sunlight lay across the bench in a bright square.",
        discovery="under the bench beside the basket of picture books",
        tags={"bench", "bright"},
    ),
}

CLUES = {
    "gold_sparkles": Clue(
        id="gold_sparkles",
        label="gold sparkles",
        phrase="a little trail of gold sparkles",
        pertains_to="parade_star",
        spot="on the floor near the prop basket",
        inference="The glitter did not belong to the bell or the mask. It seemed to pertain only to the missing parade star.",
        tags={"clue", "sparkles"},
    ),
    "blue_ribbon": Clue(
        id="blue_ribbon",
        label="blue ribbon",
        phrase="a loose strip of blue ribbon",
        pertains_to="rabbit_mask",
        spot="caught on the corner of a chair",
        inference="The ribbon did not match the star or the bell. It seemed to pertain only to the rabbit mask.",
        tags={"clue", "ribbon"},
    ),
    "silver_thread": Clue(
        id="silver_thread",
        label="silver thread",
        phrase="a curl of silver thread",
        pertains_to="silver_bell",
        spot="shining against the dark rug",
        inference="The thread did not belong to the star or the mask. It seemed to pertain only to the missing bell.",
        tags={"clue", "thread"},
    ),
}

TOOLS = {
    "none": Tool(
        id="none",
        label="no special tool",
        phrase="no special tool",
        gives_light=False,
        use_text="",
        tags=set(),
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        gives_light=True,
        use_text="clicked on a small flashlight, and its round beam pushed the dark back",
        tags={"flashlight", "light"},
    ),
    "paper_lantern": Tool(
        id="paper_lantern",
        label="paper lantern",
        phrase="a paper lantern",
        gives_light=True,
        use_text="lifted a paper lantern, and its soft glow made the shadows gentle",
        tags={"lantern", "light"},
    ),
}

BRAVERY_LEVELS = {
    "shaky": 1,
    "steady": 2,
    "bold": 3,
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Tess"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Owen"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for case_id, case in CASES.items():
        for clue_id, clue in CLUES.items():
            if clue.pertains_to != case_id:
                continue
            for place_id, place in PLACES.items():
                for tool_id, tool in TOOLS.items():
                    if place.dark and not tool.gives_light:
                        continue
                    combos.append((case_id, clue_id, place_id, tool_id))
    return combos


def explain_rejection(case: CaseFile, clue: Clue, place: HidingPlace, tool: Tool) -> str:
    if clue.pertains_to != case.id:
        return (
            f"(No story: {clue.label} does not honestly point to the {case.label}. "
            f"A fair whodunit needs a clue that really pertains to the missing item.)"
        )
    if place.dark and not tool.gives_light:
        return (
            f"(No story: {place.phrase} is dark, so the child needs a real light before searching there. "
            f"Pick a flashlight, a paper lantern, or a bright hiding place.)"
        )
    return "(No story: this combination is not reasonable.)"


def search_mode(params: StoryParams) -> str:
    place = PLACES[params.place]
    bravery = BRAVERY_LEVELS[params.bravery]
    if not place.dark:
        return "bright"
    if bravery >= 3:
        return "solo"
    return "together"


def predict_confession(world: World) -> dict:
    sim = world.copy()
    sim.get("investigator").memes["kindness"] += 1
    propagate(sim, narrate=False)
    culprit = sim.get("culprit")
    item = sim.get("item")
    return {
        "confesses": culprit.memes["honesty"] >= THRESHOLD,
        "found": item.meters["found"] >= THRESHOLD,
    }


def introduce(world: World, investigator: Entity, helper: Entity, adult: Entity, case: CaseFile) -> None:
    world.say(
        f"On show day, the room hummed with whispers, costume rustles, and tiny shoes tapping on the floor. "
        f"{case.phrase.capitalize()} {case.opening}."
    )
    world.say(
        f"{investigator.id} and {helper.id} were meant to stand near the front for {case.event}, "
        f"while their {adult.label_word} checked ribbons, masks, and song cards."
    )


def discover_loss(world: World, investigator: Entity, culprit: Entity, case: CaseFile) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    culprit.memes["guilt"] += 1
    culprit.meters["repairing"] += 1
    world.say(
        f"But when the basket was opened, {case.phrase} was gone."
    )
    world.say(
        f"At once the room turned into a little whodunit. Children looked at one another, then at the empty place where it should have been."
    )
    world.facts["mystery_started"] = True


def list_suspects(world: World, investigator: Entity, culprit: Entity, helper: Entity) -> None:
    world.say(
        f'"Who took it?" someone whispered. {helper.id} had been near the props, and so had {culprit.id}, and even {investigator.id} felt the mystery tugging at {investigator.pronoun("object")}.'
    )


def notice_clue(world: World, investigator: Entity, case: CaseFile, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    investigator.memes["focus"] += 1
    world.say(
        f"Then {investigator.id} noticed {clue.phrase} {clue.spot}."
    )
    world.say(clue.inference)
    propagate(world, narrate=False)
    world.facts["clue_seen"] = clue.label


def choose_search(world: World, investigator: Entity, helper: Entity, place: HidingPlace, tool: Tool, bravery: str) -> None:
    place_ent = world.get("place")
    investigator.memes["fear"] += 1 if place.dark else 0
    if place.dark:
        world.say(place.spooky)
    mode = search_mode(world.facts["params"])
    world.facts["search_mode"] = mode
    if mode == "solo":
        investigator.memes["bravery"] += 1
        world.say(
            f'{investigator.id} swallowed hard. "{place.phrase.capitalize()} looks spooky," {investigator.pronoun()} said, '
            f'"but clues are clues."'
        )
        world.say(
            f"{investigator.id} {tool.use_text} and stepped forward alone, brave even while the shadows still felt big."
        )
    elif mode == "together":
        investigator.memes["bravery"] += 1
        helper.memes["support"] += 1
        world.say(
            f'{investigator.id} took a slow breath. "{place.phrase.capitalize()} is dark," {investigator.pronoun()} said, '
            f'"so come with me."'
        )
        world.say(
            f"Together the two children {tool.use_text} and moved closer, shoulder to shoulder."
        )
    else:
        investigator.memes["bravery"] += 1
        world.say(
            f'"The clue leads to {place.phrase}," {investigator.id} said, and this time the place did not feel scary at all.'
        )
    place_ent.meters["searched"] += 1
    propagate(world, narrate=False)


def find_culprit(world: World, investigator: Entity, culprit: Entity, case: CaseFile, place: HidingPlace) -> None:
    culprit.meters["found_in_place"] += 1
    world.say(
        f"There, {place.discovery}, was {culprit.id}."
    )
    world.say(
        f"{culprit.pronoun().capitalize()} was not sneaking away with the prize. {culprit.pronoun().capitalize()} was trying to fix it, because {case.damage}."
    )


def ask_kindly(world: World, investigator: Entity, culprit: Entity) -> None:
    pred = predict_confession(world)
    investigator.memes["kindness"] += 1
    world.facts["predicted_confession"] = pred["confesses"]
    world.say(
        f'{investigator.id} did not shout. "{culprit.id}," {investigator.pronoun()} asked softly, "did something go wrong?"'
    )
    propagate(world, narrate=False)


def confession(world: World, culprit: Entity, case: CaseFile) -> None:
    culprit.memes["relief"] += 1
    world.say(
        f'{culprit.id} nodded, eyes shiny. "{case.phrase.capitalize()} slipped when I was carrying it," {culprit.pronoun()} said. '
        f'"I was afraid everyone would be upset, so I hid and tried to {case.repair}."'
    )
    world.say(
        f'It had never been a mean trick at all. It was a scared mistake.'
    )


def adult_resolves(world: World, adult: Entity, investigator: Entity, culprit: Entity, helper: Entity, case: CaseFile) -> None:
    item = world.get("item")
    item.meters["fixed"] += 1
    item.meters["missing"] = 0.0
    culprit.meters["repairing"] = 0.0
    investigator.memes["relief"] += 1
    helper.memes["relief"] += 1
    culprit.memes["fear"] = 0.0
    culprit.memes["guilt"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} knelt beside {culprit.id} and {investigator.id}. "
        f'"Thank you for telling the truth," {adult.pronoun()} said. "Next time, ask for help sooner."'
    )
    world.say(
        f"Then {adult.pronoun()} helped {culprit.id} {case.repair}, and soon {case.phrase} was ready again."
    )
    world.facts["truth_told"] = True


def ending(world: World, investigator: Entity, culprit: Entity, helper: Entity, case: CaseFile) -> None:
    culprit.memes["belonging"] += 1
    investigator.memes["bravery"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'When the children lined up at last, {culprit.id} stood taller, because telling the truth had turned a knot in {culprit.pronoun("possessive")} chest into a calm breath.'
    )
    world.say(
        f"{case.ending}"
    )
    world.say(
        f"{investigator.id} smiled, knowing bravery had meant more than entering a spooky place. It had also meant asking kindly and making room for the truth."
    )


def tell(
    case: CaseFile,
    place: HidingPlace,
    clue: Clue,
    tool: Tool,
    investigator_name: str,
    investigator_gender: str,
    culprit_name: str,
    culprit_gender: str,
    helper_name: str,
    helper_gender: str,
    adult_type: str,
    bravery: str,
    params: StoryParams,
) -> World:
    world = World()
    investigator = world.add(Entity(id="investigator", kind="character", type=investigator_gender, role="investigator", label=investigator_name))
    culprit = world.add(Entity(id="culprit", kind="character", type=culprit_gender, role="culprit", label=culprit_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, role="helper", label=helper_name))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    item = world.add(Entity(id="item", kind="thing", type="prop", label=case.label, attrs={"expected_clue": case.clue_id}))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.label, attrs={"clue_id": clue.id}))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label, attrs={"dark": place.dark}))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, attrs={"gives_light": tool.gives_light}))

    investigator.attrs["name"] = investigator_name
    culprit.attrs["name"] = culprit_name
    helper.attrs["name"] = helper_name
    adult.attrs["name"] = adult_type
    investigator.memes["bravery"] = float(BRAVERY_LEVELS[bravery])
    culprit.memes["guilt"] = 0.0
    culprit.memes["suspected"] = 0.0
    culprit.memes["honesty"] = 0.0
    investigator.memes["kindness"] = 0.0
    investigator.memes["fear"] = 0.0
    helper.memes["support"] = 0.0
    item.meters["missing"] = 0.0
    item.meters["fixed"] = 0.0
    item.meters["found"] = 0.0
    place_ent.meters["searched"] = 0.0
    clue_ent.meters["noticed"] = 0.0

    world.facts.update(
        params=params,
        case=case,
        place_cfg=place,
        clue_cfg=clue,
        tool_cfg=tool,
        investigator=investigator,
        culprit=culprit,
        helper=helper,
        adult=adult,
    )

    introduce(world, investigator, helper, adult, case)
    discover_loss(world, investigator, culprit, case)
    list_suspects(world, investigator, culprit, helper)

    world.para()
    notice_clue(world, investigator, case, clue)
    choose_search(world, investigator, helper, place, tool, bravery)
    find_culprit(world, investigator, culprit, case, place)

    world.para()
    ask_kindly(world, investigator, culprit)
    confession(world, culprit, case)
    adult_resolves(world, adult, investigator, culprit, helper, case)

    world.para()
    ending(world, investigator, culprit, helper, case)

    world.facts.update(
        found=item.meters["found"] >= THRESHOLD,
        fixed=item.meters["fixed"] >= THRESHOLD,
        clue_seen=clue.label,
        place_dark=place.dark,
        search_mode=world.facts.get("search_mode", "bright"),
    )
    return world


KNOWLEDGE = {
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, clues help a detective know where to look next.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when something feels scary. A brave person can still have butterflies inside and keep going kindly.",
        )
    ],
    "truth": [
        (
            "Why is it brave to tell the truth after a mistake?",
            "Telling the truth can feel hard because you worry about what will happen next. It is brave because honesty helps people fix the problem together.",
        )
    ],
    "flashlight": [
        (
            "What does a flashlight do?",
            "A flashlight makes a bright beam so you can see in a dark place. It helps shadows feel smaller because you can tell what is really there.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light you can carry with you. It glows around you and helps you see gently in dim places.",
        )
    ],
    "repair": [
        (
            "What does repair mean?",
            "To repair something means to fix it after it gets bent, torn, or broken. Repairing can help an object be useful again.",
        )
    ],
}
KNOWLEDGE_ORDER = ["clue", "bravery", "truth", "flashlight", "lantern", "repair"]


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    clue = world.facts["clue_cfg"]
    investigator = world.facts["investigator"]
    culprit = world.facts["culprit"]
    place = world.facts["place_cfg"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old about a missing stage prop, and include the word "pertain".',
        f"Tell a mystery where {investigator.label} notices {clue.phrase}, realizes it seems to pertain to {case.phrase}, and bravely follows the clue to {place.phrase}.",
        f"Write a child-facing mystery in which {culprit.label} is hiding a damaged prop to fix it, and the ending teaches that bravery can mean both searching kindly and telling the truth.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    investigator = world.facts["investigator"]
    culprit = world.facts["culprit"]
    helper = world.facts["helper"]
    adult = world.facts["adult"]
    case = world.facts["case"]
    clue = world.facts["clue_cfg"]
    place = world.facts["place_cfg"]
    tool = world.facts["tool_cfg"]
    mode = world.facts["search_mode"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {case.phrase} had gone missing right before {case.event}. That mattered because the children needed it for the show.",
        ),
        (
            f"What clue did {investigator.label} find?",
            f"{investigator.label} found {clue.phrase} {clue.spot}. {clue.inference}",
        ),
        (
            f"Why did the clue matter?",
            f"The clue mattered because it honestly pointed toward the missing item instead of being random. In the story, {investigator.label} understood that the clue seemed to pertain to {case.phrase}.",
        ),
    ]
    if place.dark:
        if mode == "solo":
            qa.append(
                (
                    f"How was {investigator.label} brave?",
                    f"{investigator.label} was brave by going into {place.phrase} even though it felt spooky. {investigator.pronoun('subject').capitalize()} used {tool.phrase} and kept following the clue instead of backing away.",
                )
            )
        else:
            qa.append(
                (
                    f"How was {investigator.label} brave in the dark place?",
                    f"{investigator.label} admitted that {place.phrase} felt scary and still chose to search it. That was brave because {investigator.pronoun('subject')} asked {helper.label} to come along and kept going anyway.",
                )
            )
    else:
        qa.append(
            (
                f"How was {investigator.label} brave?",
                f"{investigator.label} was brave by following the clue and asking careful questions instead of joining the panic. The bravery in this story was quiet and thoughtful, not loud.",
            )
        )
    qa.append(
        (
            f"Why had {culprit.label} hidden {case.phrase}?",
            f"{culprit.label} had damaged it by accident and tried to fix it in secret. {culprit.pronoun('subject').capitalize()} was scared people would be upset, so the hiding began as fear, not meanness.",
        )
    )
    qa.append(
        (
            f"How was the mystery solved?",
            f"{investigator.label} found {culprit.label} in {place.phrase}, asked kindly what had happened, and {culprit.pronoun()} told the truth. Then the {adult.label_word} helped repair the prop so the show could still begin.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"clue", "bravery", "truth", "repair"}
    tool = world.facts["tool_cfg"]
    if tool.id == "flashlight":
        tags.add("flashlight")
    if tool.id == "paper_lantern":
        tags.add("lantern")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        shown_attrs = {k: v for k, v in ent.attrs.items() if v or v is False}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        case="parade_star",
        place="costume_trunk",
        clue="gold_sparkles",
        tool="flashlight",
        investigator="Lily",
        investigator_gender="girl",
        culprit="Ben",
        culprit_gender="boy",
        helper="Mia",
        helper_gender="girl",
        adult="teacher",
        bravery="steady",
    ),
    StoryParams(
        case="rabbit_mask",
        place="curtain_nook",
        clue="blue_ribbon",
        tool="paper_lantern",
        investigator="Tom",
        investigator_gender="boy",
        culprit="Zoe",
        culprit_gender="girl",
        helper="Ella",
        helper_gender="girl",
        adult="teacher",
        bravery="bold",
    ),
    StoryParams(
        case="silver_bell",
        place="reading_bench",
        clue="silver_thread",
        tool="none",
        investigator="Nora",
        investigator_gender="girl",
        culprit="Max",
        culprit_gender="boy",
        helper="Lucy",
        helper_gender="girl",
        adult="teacher",
        bravery="shaky",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small whodunit about a missing prop, a fair clue, and bravery."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--adult", choices=["teacher", "mother", "father"])
    ap.add_argument("--bravery", choices=sorted(BRAVERY_LEVELS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: set[str], gender: Optional[str] = None) -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    options = [name for name in pool if name not in avoid]
    return rng.choice(options), chosen_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    case_id = args.case
    clue_id = args.clue
    place_id = args.place
    tool_id = args.tool

    if case_id and clue_id and place_id and tool_id:
        case = CASES[case_id]
        clue = CLUES[clue_id]
        place = PLACES[place_id]
        tool = TOOLS[tool_id]
        if (case_id, clue_id, place_id, tool_id) not in set(valid_combos()):
            raise StoryError(explain_rejection(case, clue, place, tool))
    elif case_id and clue_id:
        if CLUES[clue_id].pertains_to != case_id:
            dummy_place = PLACES[place_id] if place_id else next(iter(PLACES.values()))
            dummy_tool = TOOLS[tool_id] if tool_id else next(iter(TOOLS.values()))
            raise StoryError(explain_rejection(CASES[case_id], CLUES[clue_id], dummy_place, dummy_tool))
    elif place_id and tool_id:
        if PLACES[place_id].dark and not TOOLS[tool_id].gives_light:
            case = CASES[case_id] if case_id else next(iter(CASES.values()))
            clue = CLUES[clue_id] if clue_id else CLUES[case.clue_id]
            raise StoryError(explain_rejection(case, clue, PLACES[place_id], TOOLS[tool_id]))

    combos = [
        combo for combo in valid_combos()
        if (args.case is None or combo[0] == args.case)
        and (args.clue is None or combo[1] == args.clue)
        and (args.place is None or combo[2] == args.place)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, clue_id, place_id, tool_id = rng.choice(sorted(combos))
    adult = args.adult or rng.choice(["teacher", "mother", "father"])
    bravery = args.bravery or rng.choice(sorted(BRAVERY_LEVELS))
    used: set[str] = set()
    investigator, ig = _pick_name(rng, used)
    used.add(investigator)
    culprit, cg = _pick_name(rng, used)
    used.add(culprit)
    helper, hg = _pick_name(rng, used)

    return StoryParams(
        case=case_id,
        place=place_id,
        clue=clue_id,
        tool=tool_id,
        investigator=investigator,
        investigator_gender=ig,
        culprit=culprit,
        culprit_gender=cg,
        helper=helper,
        helper_gender=hg,
        adult=adult,
        bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"(Unknown case: {params.case})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.bravery not in BRAVERY_LEVELS:
        raise StoryError(f"(Unknown bravery level: {params.bravery})")
    case = CASES[params.case]
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    tool = TOOLS[params.tool]
    if (params.case, params.clue, params.place, params.tool) not in set(valid_combos()):
        raise StoryError(explain_rejection(case, clue, place, tool))

    world = tell(
        case=case,
        place=place,
        clue=clue,
        tool=tool,
        investigator_name=params.investigator,
        investigator_gender=params.investigator_gender,
        culprit_name=params.culprit,
        culprit_gender=params.culprit_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        bravery=params.bravery,
        params=params,
    )
    return StorySample(
        params=params,
        story=world.render().replace("investigator", params.investigator).replace("culprit", params.culprit).replace("helper", params.helper),
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


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid_case_clue(C, Cl) :- case(C), clue(Cl), pertains_to(Cl, C).
safe_search(P, T) :- place(P), tool(T), bright(P).
safe_search(P, T) :- place(P), tool(T), dark(P), gives_light(T).
valid(C, Cl, P, T) :- valid_case_clue(C, Cl), safe_search(P, T).

% --- outcome model ---------------------------------------------------------
search_mode(bright) :- chosen_place(P), bright(P).
search_mode(solo) :- chosen_place(P), dark(P), bravery(bold).
search_mode(together) :- chosen_place(P), dark(P), bravery(shaky).
search_mode(together) :- chosen_place(P), dark(P), bravery(steady).

#show valid/4.
#show search_mode/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for case_id in CASES:
        lines.append(asp.fact("case", case_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("pertains_to", clue_id, clue.pertains_to))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("dark" if place.dark else "bright", place_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.gives_light:
            lines.append(asp.fact("gives_light", tool_id))
    for level in BRAVERY_LEVELS:
        lines.append(asp.fact("bravery_level", level))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_search_mode(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("bravery", params.bravery),
        ]
    )
    model = asp.one_model(asp_program(extra))
    found = asp.atoms(model, "search_mode")
    return found[0][0] if found else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py:
            print("  only in ASP:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in Python:", sorted(py - asp_set))

    cases = list(CURATED)
    for s in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_search_mode(params) != search_mode(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: search outcome matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} search outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True)
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (case, clue, place, tool) combos:\n")
        for case_id, clue_id, place_id, tool_id in combos:
            print(f"  {case_id:12} {clue_id:14} {place_id:14} {tool_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.investigator}: {p.case} at {p.place} ({search_mode(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
