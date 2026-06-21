#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nation_calvary_poi_wet_stairs_surprise_curiosity.py
================================================================================

A standalone story world for a tiny whodunit on wet stairs.

The seed asked for these words and instruments:
- words: nation, calvary, poi
- setting: wet stairs
- features: Surprise, Curiosity, Humor
- style: Whodunit

This world models a child detective at a small outdoor show on rainy stairs.
Something important seems to vanish. The stairs are slippery, so a worried helper
quietly moves the item to a dry hiding place and leaves a clue behind. The child
detective follows the clue, interviews the suspects, and discovers that the
"thief" was trying to keep everyone safe.

Run it
------
    python storyworlds/worlds/gpt-5.4/nation_calvary_poi_wet_stairs_surprise_curiosity.py
    python storyworlds/worlds/gpt-5.4/nation_calvary_poi_wet_stairs_surprise_curiosity.py --item bell --suspect baker
    python storyworlds/worlds/gpt-5.4/nation_calvary_poi_wet_stairs_surprise_curiosity.py --all
    python storyworlds/worlds/gpt-5.4/nation_calvary_poi_wet_stairs_surprise_curiosity.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/nation_calvary_poi_wet_stairs_surprise_curiosity.py --trace
    python storyworlds/worlds/gpt-5.4/nation_calvary_poi_wet_stairs_surprise_curiosity.py --asp
    python storyworlds/worlds/gpt-5.4/nation_calvary_poi_wet_stairs_surprise_curiosity.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
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
class Festival:
    id: str
    label: str
    opening: str
    ending: str
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


@dataclass
class MissingItem:
    id: str
    phrase: str
    short: str
    size: str
    dry_only: bool
    reveal_line: str
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
class Spot:
    id: str
    phrase: str
    dry: bool
    fits: set[str] = field(default_factory=set)
    reveal: str = ""
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
class SuspectCfg:
    id: str
    label: str
    type: str
    job: str
    clue_seen: str
    clue_left: str
    spot: str
    motive: str
    alibi: str
    laugh: str
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


FESTIVALS = {
    "nation_day": Festival(
        id="nation_day",
        label="Little Nation Day",
        opening="The town hall steps were dressed for Little Nation Day.",
        ending="The show began at last, and the wet stairs no longer felt like a problem.",
    ),
    "harbor_nation": Festival(
        id="harbor_nation",
        label="Harbor Nation Parade",
        opening="The harbor steps were fluttering with ribbons for the Harbor Nation Parade.",
        ending="Soon the parade music bounced across the wet stone, and everyone stood in the safe dry places.",
    ),
}

ITEMS = {
    "bell": MissingItem(
        id="bell",
        phrase="the brass bell",
        short="bell",
        size="small",
        dry_only=True,
        reveal_line="When the bell rang at the end, everyone laughed because the whole mystery had begun with a safety fix.",
        tags={"bell", "safety"},
    ),
    "map": MissingItem(
        id="map",
        phrase="the paper nation map",
        short="map",
        size="flat",
        dry_only=True,
        reveal_line="When the map was opened at the end, the raindrops had missed it completely, and the detective bowed like a grand sleuth.",
        tags={"nation", "paper", "safety"},
    ),
    "poi": MissingItem(
        id="poi",
        phrase="the basket of poi",
        short="poi",
        size="round",
        dry_only=True,
        reveal_line="When the poi began to swing in bright circles, even the suspects clapped for the detective.",
        tags={"poi", "dance", "safety"},
    ),
}

SPOTS = {
    "closet": Spot(
        id="closet",
        phrase="the dry coat closet inside the doorway",
        dry=True,
        fits={"small", "flat"},
        reveal="Inside the coat closet, tucked between two raincoats, sat the missing thing as dry as toast.",
        tags={"closet", "dry"},
    ),
    "bench": Spot(
        id="bench",
        phrase="the band bench under the awning",
        dry=True,
        fits={"small", "round"},
        reveal="Under the awning, beneath the band bench, the missing thing waited where no raindrop could touch it.",
        tags={"bench", "dry"},
    ),
    "umbrella": Spot(
        id="umbrella",
        phrase="the umbrella stand by the side door",
        dry=True,
        fits={"flat", "round"},
        reveal="By the side door, hidden behind a row of umbrellas, was the missing thing in a neat safe nook.",
        tags={"umbrella", "dry"},
    ),
}

SUSPECTS = {
    "baker": SuspectCfg(
        id="baker",
        label="Pru",
        type="woman",
        job="baker",
        clue_seen="a soft dusting of flour on one wet step",
        clue_left="flour",
        spot="closet",
        motive="saw the wet stone and could not bear the thought of someone slipping while carrying a tray or ringing the bell",
        alibi="I was carrying sweet buns for the judges, and I only stopped long enough to stare at the puddles.",
        laugh='A seagull tried to steal a roll from my basket, so if anyone looked guilty, it was that bird.',
        tags={"baker", "flour"},
    ),
    "drummer": SuspectCfg(
        id="drummer",
        label="Kit",
        type="boy",
        job="drummer",
        clue_seen="two neat tap marks where a drumstick had clicked on the rail",
        clue_left="tap",
        spot="bench",
        motive="knew the band would charge down the steps in big boots and wanted the path clear and safe",
        alibi="I was tightening my drum strap and keeping my sticks dry.",
        laugh='If my drum had feet, it would have marched off and solved the case before us.',
        tags={"drummer", "band"},
    ),
    "dancer": SuspectCfg(
        id="dancer",
        label="Sol",
        type="girl",
        job="dancer",
        clue_seen="a bright tassel thread snagged on the rail",
        clue_left="tassel",
        spot="umbrella",
        motive="did not want anyone slipping before the dance with the poi began",
        alibi="I was practicing tiny careful steps on the landing where it was not slippery.",
        laugh='I am graceful, but even I do not twirl on stairs that look like soap.',
        tags={"dancer", "dance"},
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Tess", "Lucy", "Ava", "Zoe"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Max", "Sam", "Finn"]
HELPERS = [
    ("Pip", "girl"),
    ("Jun", "boy"),
    ("Mina", "girl"),
    ("Theo", "boy"),
]
TRAITS = ["curious", "careful", "bright", "thoughtful", "nosy"]
ORGANIZERS = ["aunt", "uncle", "mother", "father"]


# ---------------------------------------------------------------------------
# World and rules
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


def _r_wet_risk(world: World) -> list[str]:
    out: list[str] = []
    stairs = world.get("stairs")
    item = world.get("item")
    if stairs.meters["wet"] < THRESHOLD:
        return out
    if item.attrs.get("location") != "stairs":
        return out
    sig = ("risk", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stairs.meters["slip_risk"] += 1
    world.get("detective").memes["curiosity"] += 1
    world.get("organizer").memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_move_item(world: World) -> list[str]:
    out: list[str] = []
    stairs = world.get("stairs")
    item = world.get("item")
    culprit = world.get("culprit")
    spot = world.facts["spot_cfg"]
    if stairs.meters["slip_risk"] < THRESHOLD:
        return out
    if item.attrs.get("location") != "stairs":
        return out
    sig = ("move", item.id, culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.attrs["location"] = spot.id
    item.meters["moved"] += 1
    culprit.memes["guilt"] += 1
    culprit.memes["care"] += 1
    world.facts["clue_visible"] = True
    out.append("__moved__")
    return out


CAUSAL_RULES = [
    Rule(name="wet_risk", tag="physical", apply=_r_wet_risk),
    Rule(name="move_item", tag="social", apply=_r_move_item),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def fits_spot(item: MissingItem, spot: Spot) -> bool:
    return item.size in spot.fits


def valid_combo(item_id: str, suspect_id: str) -> bool:
    if item_id not in ITEMS or suspect_id not in SUSPECTS:
        return False
    item = ITEMS[item_id]
    suspect = SUSPECTS[suspect_id]
    spot = SPOTS[suspect.spot]
    if item.dry_only and not spot.dry:
        return False
    return fits_spot(item, spot)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for item_id in ITEMS:
        for suspect_id in SUSPECTS:
            if valid_combo(item_id, suspect_id):
                combos.append((item_id, suspect_id))
    return combos


def explain_rejection(item_id: str, suspect_id: str) -> str:
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if suspect_id not in SUSPECTS:
        return f"(No story: unknown suspect '{suspect_id}'.)"
    item = ITEMS[item_id]
    suspect = SUSPECTS[suspect_id]
    spot = SPOTS[suspect.spot]
    if item.dry_only and not spot.dry:
        return f"(No story: {item.phrase} needs a dry hiding place, but {spot.phrase} is not dry.)"
    return (
        f"(No story: {item.phrase} does not fit well in {spot.phrase}. "
        f"This mystery world only allows hiding places that make physical sense.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def setup_scene(world: World, festival: Festival, detective: Entity, helper: Entity,
                organizer: Entity, item: MissingItem) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{festival.opening} Rain had made the stairs shiny and dark, and each step wore a thin silver lick of water."
    )
    world.say(
        f"{detective.id} had been asked to watch {item.phrase} until the show began. "
        f"Beside the rail stood cardboard calvary horses, a paper nation banner, and a practice basket of poi for the later dance."
    )
    world.say(
        f'{helper.id} whispered, "This looks like the start of a grand mystery," and {organizer.label_word} only smiled and told them not to race on the wet stairs.'
    )


def rain_and_risk(world: World, item: MissingItem) -> None:
    stairs = world.get("stairs")
    stairs.meters["wet"] += 1
    world.get("item").attrs["location"] = "stairs"
    propagate(world, narrate=False)
    world.say(
        f"A light drizzle came pattering back, and the wet stairs grew slicker. For one busy minute, nobody noticed what danger that made for {item.phrase} and the people hurrying past it."
    )
    world.say(
        "Then the crowd gasped. The place on the step where the important thing had rested was empty."
    )


def discover_loss(world: World, detective: Entity, item: MissingItem) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f'"{item.short.capitalize()} gone!" cried {detective.id}. The mystery was not huge enough for the whole nation, perhaps, but it felt huge enough for one rainy morning.'
    )


def inspect_clue(world: World, detective: Entity, suspect_cfg: SuspectCfg) -> None:
    world.facts["seen_clue"] = suspect_cfg.clue_seen
    world.say(
        f"{detective.id} crouched and saw {suspect_cfg.clue_seen}. That was the first true clue, and it made {detective.pronoun('object')} lean closer instead of running about."
    )


def comic_wrong_guess(world: World, helper: Entity) -> None:
    helper.memes["humor"] += 1
    world.say(
        f'"Perhaps one of the calvary horses stole it," {helper.id} murmured. '
        f'When nobody answered, {helper.pronoun()} added, "A wooden horse is very quiet, which is exactly what makes it suspicious."'
    )


def question_suspects(world: World, culprit_id: str) -> None:
    order = [sid for sid in SUSPECTS if sid != culprit_id] + [culprit_id]
    for idx, sid in enumerate(order):
        cfg = SUSPECTS[sid]
        speaker = world.get(sid)
        prefix = "First" if idx == 0 else ("Next" if idx == 1 else "At last")
        world.say(
            f"{prefix}, {world.get('detective').id} asked {speaker.id} the {cfg.job}. "
            f'"{cfg.alibi}" {speaker.pronoun().capitalize()} said. Then {speaker.pronoun()} gave a tiny shrug and added, "{cfg.laugh}"'
        )


def deduce(world: World, detective: Entity, suspect_cfg: SuspectCfg, item: MissingItem) -> None:
    spot = SPOTS[suspect_cfg.spot]
    detective.memes["certainty"] += 1
    world.say(
        f"All at once, the clue, the wet steps, and the empty place fit together in {detective.id}'s mind. "
        f'"Nobody stole {item.phrase}," {detective.pronoun()} said. "Someone moved it to {spot.phrase} because these stairs were too slippery."'
    )
    world.say(
        f"{detective.id} turned to {suspect_cfg.label}. {suspect_cfg.label} blinked, surprised that the answer had been reached so quickly."
    )


def reveal(world: World, item: MissingItem, suspect_cfg: SuspectCfg) -> None:
    culprit = world.get("culprit")
    spot = SPOTS[suspect_cfg.spot]
    world.say(
        f'{culprit.id} sighed and nodded. "I did move it," {culprit.pronoun()} admitted. "I {suspect_cfg.motive}."'
    )
    world.say(spot.reveal)
    world.say(
        f"{item.reveal_line} That was the surprise: the culprit had been a helper all along, not a sneaky thief."
    )


def resolve(world: World, festival: Festival, detective: Entity, helper: Entity,
            organizer: Entity, item: MissingItem) -> None:
    detective.memes["relief"] += 1
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    organizer.memes["pride"] += 1
    world.say(
        f'{organizer.label_word.capitalize()} ruffled {detective.id}\'s hair. "Good noticing," {organizer.pronoun()} said. "A real detective looks for the why, not only the who."'
    )
    world.say(
        f"{helper.id} bowed so low that nearly everyone laughed. \"Case closed,\" {helper.pronoun()} declared, \"and no horses from the calvary were arrested.\""
    )
    world.say(
        f"{festival.ending} {item.phrase.capitalize()} was carried down safely, and {detective.id} walked beside it with bright careful steps and a grin."
    )


# ---------------------------------------------------------------------------
# Build one world
# ---------------------------------------------------------------------------
def tell(festival: Festival, item_cfg: MissingItem, suspect_cfg: SuspectCfg,
         detective_name: str = "Mira", detective_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "girl",
         organizer_type: str = "aunt", trait: str = "curious") -> World:
    world = World()

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        label=detective_name,
        role="detective",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        traits=["funny"],
    ))
    organizer = world.add(Entity(
        id="Organizer",
        kind="character",
        type=organizer_type,
        label="the organizer",
        role="organizer",
        traits=["calm"],
    ))
    culprit = world.add(Entity(
        id=suspect_cfg.label,
        kind="character",
        type=suspect_cfg.type,
        label=suspect_cfg.label,
        role="suspect",
        traits=[suspect_cfg.job],
    ))
    world.add(Entity(
        id="stairs",
        kind="thing",
        type="stairs",
        label="the wet stairs",
        role="place",
    ))
    world.add(Entity(
        id="item",
        kind="thing",
        type=item_cfg.id,
        label=item_cfg.short,
        role="missing_item",
        attrs={"location": "stairs"},
    ))

    # Add the innocent suspects too, so trace and QA can mention them.
    for sid, cfg in SUSPECTS.items():
        if sid == suspect_cfg.id:
            continue
        world.add(Entity(
            id=sid,
            kind="character",
            type=cfg.type,
            label=cfg.label,
            role="suspect",
            traits=[cfg.job],
        ))

    world.facts.update(
        festival=festival,
        item_cfg=item_cfg,
        suspect_cfg=suspect_cfg,
        spot_cfg=SPOTS[suspect_cfg.spot],
        detective=detective,
        helper=helper,
        organizer=organizer,
        culprit=culprit,
        clue_visible=False,
        seen_clue="",
    )

    setup_scene(world, festival, detective, helper, organizer, item_cfg)
    world.para()
    rain_and_risk(world, item_cfg)
    discover_loss(world, detective, item_cfg)
    inspect_clue(world, detective, suspect_cfg)
    comic_wrong_guess(world, helper)
    world.para()
    question_suspects(world, suspect_cfg.id)
    deduce(world, detective, suspect_cfg, item_cfg)
    world.para()
    reveal(world, item_cfg, suspect_cfg)
    resolve(world, festival, detective, helper, organizer, item_cfg)
    world.facts.update(
        solved=True,
        hiding_place=SPOTS[suspect_cfg.spot].phrase,
        culprit_job=suspect_cfg.job,
        motive=suspect_cfg.motive,
    )
    return world


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    festival: str = "nation_day"
    item: str = "bell"
    suspect: str = "baker"
    detective: str = "Mira"
    detective_gender: str = "girl"
    helper: str = "Pip"
    helper_gender: str = "girl"
    organizer: str = "aunt"
    trait: str = "curious"
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
    "wet_stairs": [
        (
            "Why are wet stairs slippery?",
            "A thin layer of water can make your shoes slide instead of grip. That is why people slow down and hold the rail on wet stairs."
        )
    ],
    "poi": [
        (
            "What is poi in a dance show?",
            "Poi are weighted balls on cords that people swing in circles during some dances. They need space and careful hands so nobody gets bumped."
        )
    ],
    "nation": [
        (
            "What does the word nation mean?",
            "A nation is a country or a people who belong together. In a little parade or school show, children might use the word to mean everyone joining one big celebration."
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure something out. Good detectives notice clues and ask what they mean."
        )
    ],
    "safety": [
        (
            "Why might someone move an object away from wet stairs?",
            "They might want to stop someone from slipping or dropping it. Moving something to a dry place can be a safety choice, not a mean trick."
        )
    ],
}

KNOWLEDGE_ORDER = ["wet_stairs", "clue", "nation", "poi", "safety"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    culprit = f["suspect_cfg"]
    festival = f["festival"]
    detective = f["detective"]
    return [
        f'Write a child-friendly whodunit set on wet stairs during {festival.label} where {item.phrase} seems to vanish.',
        f"Tell a mystery story with surprise, curiosity, and humor in which {detective.id} follows a clue and discovers that the {culprit.job} moved the missing item for safety.",
        'Write a gentle rainy whodunit that includes the words "nation", "calvary", and "poi" and ends with the detective learning to ask why before blaming anyone.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    organizer = f["organizer"]
    item = f["item_cfg"]
    suspect = f["suspect_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective at a rainy festival, plus {helper.id} the joking helper and {organizer.label_word} who is running the show."
        ),
        (
            f"What went missing on the wet stairs?",
            f"{item.phrase.capitalize()} seemed to vanish from the stairs. That missing object starts the mystery and makes everyone look around in surprise."
        ),
        (
            "What clue helped solve the mystery?",
            f"The key clue was {f['seen_clue']}. That clue pointed toward {suspect.label} because it matched {suspect.pronoun('possessive')} work and movements."
        ),
        (
            f"Why did {suspect.label} move the item?",
            f"{suspect.label} moved it because {suspect.motive}. So the culprit was trying to protect people and the show, not spoil it."
        ),
        (
            "How did the detective solve the case?",
            f"{detective.id} noticed that the clue and the slippery stairs belonged together. Then {detective.pronoun()} guessed the item had been moved to a dry place instead of stolen, which turned the mystery around."
        ),
        (
            "What was funny in the story?",
            f"{helper.id} joked that one of the calvary horses might be the thief. The joke makes the mystery feel playful even while everyone is curious and worried."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"wet_stairs", "clue", "safety", "nation"}
    if world.facts["item_cfg"].id == "poi":
        tags.add("poi")
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
# CLI and trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  clue_seen: {world.facts.get('seen_clue', '')}")
    lines.append(f"  hiding_place: {world.facts.get('hiding_place', '')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        festival="nation_day",
        item="bell",
        suspect="baker",
        detective="Mira",
        detective_gender="girl",
        helper="Pip",
        helper_gender="girl",
        organizer="aunt",
        trait="curious",
    ),
    StoryParams(
        festival="harbor_nation",
        item="poi",
        suspect="drummer",
        detective="Leo",
        detective_gender="boy",
        helper="Mina",
        helper_gender="girl",
        organizer="uncle",
        trait="bright",
    ),
    StoryParams(
        festival="nation_day",
        item="map",
        suspect="dancer",
        detective="Nora",
        detective_gender="girl",
        helper="Theo",
        helper_gender="boy",
        organizer="mother",
        trait="careful",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(I,S) :- item(I), suspect(S), prefers_spot(S,Sp), fit(Sp,I), dry(Sp).
chosen_spot(Sp) :- chosen_suspect(S), prefers_spot(S,Sp).
solvable :- chosen_item(I), chosen_suspect(S), valid(I,S).
outcome(solved) :- solvable.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for sid, cfg in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("prefers_spot", sid, cfg.spot))
    for spid, spot in SPOTS.items():
        lines.append(asp.fact("spot", spid))
        if spot.dry:
            lines.append(asp.fact("dry", spid))
    for iid, item in ITEMS.items():
        for spid, spot in SPOTS.items():
            if fits_spot(item, spot):
                lines.append(asp.fact("fit", spid, iid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_spot(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_suspect", params.suspect),
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_spot/1."))
    spots = asp.atoms(model, "chosen_spot")
    return spots[0][0] if spots else "?"


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_suspect", params.suspect),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad_spot = 0
    bad_outcome = 0
    for params in cases:
        py_spot = SUSPECTS[params.suspect].spot if valid_combo(params.item, params.suspect) else "?"
        if asp_spot(params) != py_spot:
            bad_spot += 1
        py_out = "solved" if valid_combo(params.item, params.suspect) else "?"
        if asp_outcome(params) != py_out:
            bad_outcome += 1

    if bad_spot == 0:
        print(f"OK: hiding-spot inference matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad_spot}/{len(cases)} hiding spots differ.")

    if bad_outcome == 0:
        print(f"OK: outcome inference matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad_outcome}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny whodunit on wet stairs. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--organizer", choices=ORGANIZERS)
    ap.add_argument("--detective")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (item, suspect) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_detective(rng: random.Random, gender: Optional[str], name: Optional[str]) -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    if name:
        return name, g
    pool = GIRL_NAMES if g == "girl" else BOY_NAMES
    return rng.choice(pool), g


def _pick_helper(rng: random.Random, avoid: str) -> tuple[str, str]:
    choices = [pair for pair in HELPERS if pair[0] != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.suspect and not valid_combo(args.item, args.suspect):
        raise StoryError(explain_rejection(args.item, args.suspect))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.suspect is None or combo[1] == args.suspect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, suspect_id = rng.choice(sorted(combos))
    festival = args.festival or rng.choice(sorted(FESTIVALS))
    detective_name, detective_gender = _pick_detective(rng, args.gender, args.detective)
    helper_name, helper_gender = _pick_helper(rng, detective_name)
    organizer = args.organizer or rng.choice(ORGANIZERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        festival=festival,
        item=item_id,
        suspect=suspect_id,
        detective=detective_name,
        detective_gender=detective_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        organizer=organizer,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.festival not in FESTIVALS:
        raise StoryError(f"(No story: unknown festival '{params.festival}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(No story: unknown suspect '{params.suspect}'.)")
    if params.organizer not in ORGANIZERS:
        raise StoryError(f"(No story: unknown organizer '{params.organizer}'.)")
    if not valid_combo(params.item, params.suspect):
        raise StoryError(explain_rejection(params.item, params.suspect))

    world = tell(
        festival=FESTIVALS[params.festival],
        item_cfg=ITEMS[params.item],
        suspect_cfg=SUSPECTS[params.suspect],
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        organizer_type=params.organizer,
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
        print(asp_program("", "#show valid/2.\n#show chosen_spot/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, suspect) combos:\n")
        for item_id, suspect_id in combos:
            print(f"  {item_id:6} {suspect_id:8} -> {SUSPECTS[suspect_id].spot}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.detective}: {p.item} mystery ({p.suspect} on wet stairs)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
