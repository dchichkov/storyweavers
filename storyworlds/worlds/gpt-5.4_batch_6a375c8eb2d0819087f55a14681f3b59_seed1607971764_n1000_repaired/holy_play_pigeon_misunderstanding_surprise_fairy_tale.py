#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/holy_play_pigeon_misunderstanding_surprise_fairy_tale.py
====================================================================================

A standalone story world for a small fairy-tale domain:

A child uses a holy festival object in pretend play. A pigeon snatches the shiny
little thing and flies to a nest. The child misunderstands the pigeon and thinks
it is being mean or stealing on purpose. A calm grown-up follows the clues,
discovers hungry chicks in the nest, explains the misunderstanding, and ends the
day with a gentle surprise that lets the play continue in a safer way.

The world is intentionally narrow and constraint-checked:
- only small, light, shiny festival objects make sense for a pigeon to grab
- only open village places make sense for a pigeon swoop
- only some helpers can reach some nest spots

Run it
------
python storyworlds/worlds/gpt-5.4/holy_play_pigeon_misunderstanding_surprise_fairy_tale.py
python storyworlds/worlds/gpt-5.4/holy_play_pigeon_misunderstanding_surprise_fairy_tale.py --all
python storyworlds/worlds/gpt-5.4/holy_play_pigeon_misunderstanding_surprise_fairy_tale.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/holy_play_pigeon_misunderstanding_surprise_fairy_tale.py --qa --json
python storyworlds/worlds/gpt-5.4/holy_play_pigeon_misunderstanding_surprise_fairy_tale.py --verify
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
    kind: str = "thing"            # character | animal | thing | place
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    shiny: bool = False
    holy: bool = False
    open_sky: bool = False
    # numeric axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "nun"}
        male = {"boy", "man", "father", "uncle", "monk"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
            "nun": "sister",
            "monk": "brother",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
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
class Place:
    id: str
    label: str
    phrase: str
    open_sky: bool
    perch_ids: set[str] = field(default_factory=set)
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
class PlayTheme:
    id: str
    scene: str
    opening: str
    role_word: str
    goal: str
    sendoff: str
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
class HolyThing:
    id: str
    label: str
    phrase: str
    sparkle: str
    use_line: str
    lightness: int
    holy_word: str
    portable: bool = True
    shiny: bool = True
    holy: bool = True
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
class NestSpot:
    id: str
    label: str
    phrase: str
    height: int
    clue: str
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
class Helper:
    id: str
    type: str
    label: str
    reach: int
    action: str
    gift: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


def _r_loss_sadness(world: World) -> list[str]:
    child = world.get("child")
    thing = world.get("holy_thing")
    if thing.meters["missing"] < THRESHOLD:
        return []
    sig = ("loss_sadness", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["sorrow"] += 1
    child.memes["alarm"] += 1
    return []


def _r_misunderstanding(world: World) -> list[str]:
    child = world.get("child")
    pigeon = world.get("pigeon")
    if child.memes["alarm"] < THRESHOLD or pigeon.meters["carrying"] < THRESHOLD:
        return []
    sig = ("misunderstanding", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["misunderstanding"] += 1
    return []


def _r_reveal_softens(world: World) -> list[str]:
    child = world.get("child")
    if world.facts.get("chicks_found") is not True:
        return []
    sig = ("reveal_softens", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["wonder"] += 1
    child.memes["sorrow"] = 0.0
    child.memes["misunderstanding"] = 0.0
    child.memes["kindness"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="loss_sadness", tag="emotion", apply=_r_loss_sadness),
    Rule(name="misunderstanding", tag="emotion", apply=_r_misunderstanding),
    Rule(name="reveal_softens", tag="emotion", apply=_r_reveal_softens),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                # a rule may change state without narrating
                pass
        current_count = len(world.fired)
        for rule in CAUSAL_RULES:
            pass
        if len(world.fired) != current_count:
            changed = True
    if narrate:
        for text in produced:
            world.say(text)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def pigeon_wants(holy_thing: HolyThing, place: Place) -> bool:
    return holy_thing.portable and holy_thing.shiny and holy_thing.lightness <= 2 and place.open_sky


def helper_can_reach(helper: Helper, nest: NestSpot) -> bool:
    return helper.reach >= nest.height


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for theme_id in THEMES:
            for thing_id, holy_thing in HOLY_THINGS.items():
                for nest_id, nest in NEST_SPOTS.items():
                    if nest_id not in place.perch_ids:
                        continue
                    if not pigeon_wants(holy_thing, place):
                        continue
                    if not any(helper_can_reach(helper, nest) for helper in HELPERS.values()):
                        continue
                    combos.append((place_id, theme_id, thing_id, nest_id))
    return combos


def suitable_helpers(nest_id: str) -> list[str]:
    nest = NEST_SPOTS[nest_id]
    return sorted(hid for hid, helper in HELPERS.items() if helper_can_reach(helper, nest))


def explain_combo_rejection(place: Place, thing: HolyThing, nest: NestSpot) -> str:
    if nest.id not in place.perch_ids:
        return (
            f"(No story: {nest.phrase} does not belong in {place.label}, so the pigeon "
            f"would have nowhere sensible to fly with the shiny thing.)"
        )
    if not place.open_sky:
        return (
            f"(No story: {place.label} is too closed in for a pigeon swoop, so the misunderstanding "
            f"cannot begin there.)"
        )
    if not thing.portable or thing.lightness > 2:
        return (
            f"(No story: {thing.phrase} is too awkward for a pigeon to carry, so the little theft "
            f"would not feel believable.)"
        )
    if not thing.shiny:
        return (
            f"(No story: {thing.phrase} is not shiny enough to catch a pigeon's eye, so the turn "
            f"of the tale has no reason to happen.)"
        )
    return "(No story: this combination does not make a believable pigeon misunderstanding.)"


def explain_helper_rejection(helper_id: str, nest_id: str) -> str:
    helper = HELPERS[helper_id]
    nest = NEST_SPOTS[nest_id]
    return (
        f"(No story: {helper.label.capitalize()} cannot reach {nest.phrase}. Try one of: "
        f"{', '.join(suitable_helpers(nest_id))}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_snatch(world: World) -> dict:
    sim = world.copy()
    thing = sim.get("holy_thing")
    pigeon = sim.get("pigeon")
    thing.meters["missing"] += 1
    pigeon.meters["carrying"] += 1
    propagate(sim, narrate=False)
    return {
        "missing": thing.meters["missing"] >= THRESHOLD,
        "misunderstanding": sim.get("child").memes["misunderstanding"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, elder: Entity, place: Place, theme: PlayTheme, holy_thing: HolyThing) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Once, in {place.phrase}, there lived a child named {child.id}. On the morning "
        f"of the {holy_thing.holy_word}, {child.pronoun()} found {holy_thing.phrase} so lovely "
        f"that the whole square seemed to shine."
    )
    world.say(
        f"{elder.label_word.capitalize()} had work to do nearby, but smiled when {child.id} "
        f"began to {theme.opening}. In that bright hour, even a little game felt as grand as a fairy tale."
    )


def play_with_holy_thing(world: World, child: Entity, theme: PlayTheme, holy_thing: HolyThing) -> None:
    child.memes["play"] += 1
    world.say(
        f"{child.id} used {holy_thing.label} in the game, pretending it was {theme.goal}. "
        f"{holy_thing.use_line}"
    )


def warning_glimmer(world: World, child: Entity, elder: Entity) -> None:
    pred = predict_snatch(world)
    world.facts["predicted_missing"] = pred["missing"]
    world.facts["predicted_misunderstanding"] = pred["misunderstanding"]
    world.say(
        f'{elder.label_word.capitalize()} glanced up at the eaves and the wires. "Hold it gently," '
        f'{elder.pronoun()} said. "Pigeons notice bright little things."'
    )


def snatch(world: World, child: Entity, pigeon: Entity, holy_thing: Entity, nest: NestSpot) -> None:
    holy_thing.meters["missing"] += 1
    pigeon.meters["carrying"] += 1
    world.facts["snatched"] = True
    propagate(world, narrate=False)
    world.say(
        f"Just then a gray pigeon swept down with a flutter like a tossed cloak. In one quick peck, "
        f"it caught the shining thing and flew toward {nest.phrase}."
    )


def misunderstand(world: World, child: Entity, pigeon: Entity, holy_thing: HolyThing) -> None:
    child.memes["blame"] += 1
    world.say(
        f'"Oh, wicked pigeon!" cried {child.id}. "{holy_thing.label.capitalize()} was for my play!" '
        f'Tears sprang into {child.pronoun("possessive")} eyes, for {child.pronoun()} thought the bird had stolen it out of spite.'
    )


def calm_and_follow(world: World, elder: Entity, child: Entity, nest: NestSpot) -> None:
    child.memes["trust"] += 1
    elder.memes["care"] += 1
    world.say(
        f'But {elder.label_word} laid a calm hand on {child.id}\'s shoulder. "Hush now," '
        f'{elder.pronoun()} said. "Let us follow the clue before we judge."'
    )
    world.say(f"They saw {nest.clue} leading them toward {nest.phrase}.")


def discover(world: World, elder: Entity, child: Entity, pigeon: Entity, nest: NestSpot, helper: Helper) -> None:
    world.facts["chicks_found"] = True
    propagate(world, narrate=False)
    world.say(
        f"{helper.label.capitalize()} came to help and {helper.action}. There, tucked into the nest, "
        f"were three tiny chicks with open beaks, and the pigeon was settling the bright thing beside them."
    )
    world.say(
        f"{nest.discovery} At once the hard knot in {child.id}'s heart began to loosen."
    )


def explain_misunderstanding(world: World, elder: Entity, child: Entity, holy_thing: HolyThing) -> None:
    world.say(
        f'"The pigeon was not mocking you," said {elder.label_word}. "It saw something bright and soft-looking '
        f'for its nest. It did not know about your holy game."'
    )
    child.memes["understanding"] += 1


def return_or_bless(world: World, helper: Helper, holy_thing: Entity, nest: NestSpot) -> None:
    if nest.height <= 1:
        holy_thing.meters["missing"] = 0.0
        world.facts["returned"] = True
        world.say(
            f"With gentle fingers, {helper.label} lifted the little thing free and handed it back."
        )
    else:
        world.facts["returned"] = False
        world.say(
            f"{helper.label.capitalize()} left the shining thing where it was, for the chicks were still leaning against it "
            f"like a wall of light, and kindness was wiser than hurry."
        )


def surprise_gift(world: World, elder: Entity, child: Entity, holy_thing: HolyThing, helper: Helper, theme: PlayTheme) -> None:
    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    world.facts["surprise"] = helper.gift
    world.say(
        f"Then came the surprise. From a pocket and a basket and an apron ribbon together, "
        f"{elder.label_word} and {helper.label} made {helper.gift} for {child.id}."
    )
    world.say(
        f"It gleamed warmly without troubling the nest at all. {child.id} laughed, lifted it high, "
        f"and went back to {theme.sendoff}."
    )


def closing_image(world: World, child: Entity, pigeon: Entity, place: Place) -> None:
    world.say(
        f"Above {place.label}, the pigeon settled its wings around the chicks, and below, "
        f"{child.id} played more gently than before. So the day ended with two small homes made happy at once."
    )


def tell(
    place: Place,
    theme: PlayTheme,
    holy_thing_cfg: HolyThing,
    nest: NestSpot,
    helper_cfg: Helper,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "aunt",
    child_trait: str = "gentle",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[child_trait],
        attrs={"trait": child_trait},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    pigeon = world.add(Entity(
        id="pigeon",
        kind="animal",
        type="pigeon",
        label="the pigeon",
        role="pigeon",
    ))
    holy_thing = world.add(Entity(
        id="holy_thing",
        kind="thing",
        type=holy_thing_cfg.id,
        label=holy_thing_cfg.label,
        role="holy_thing",
        portable=holy_thing_cfg.portable,
        shiny=holy_thing_cfg.shiny,
        holy=holy_thing_cfg.holy,
    ))
    world.add(Entity(
        id="place",
        kind="place",
        type="place",
        label=place.label,
        role="place",
        open_sky=place.open_sky,
    ))

    world.facts.update(
        place=place,
        theme=theme,
        holy_thing_cfg=holy_thing_cfg,
        nest=nest,
        helper=helper_cfg,
        child=child,
        elder=elder,
        pigeon=pigeon,
        holy_thing=holy_thing,
        chicks_found=False,
        snatched=False,
        returned=False,
        surprise="",
    )

    introduce(world, child, elder, place, theme, holy_thing_cfg)
    play_with_holy_thing(world, child, theme, holy_thing_cfg)

    world.para()
    warning_glimmer(world, child, elder)
    snatch(world, child, pigeon, holy_thing, nest)
    misunderstand(world, child, pigeon, holy_thing_cfg)

    world.para()
    calm_and_follow(world, elder, child, nest)
    discover(world, elder, child, pigeon, nest, helper_cfg)
    explain_misunderstanding(world, elder, child, holy_thing_cfg)
    return_or_bless(world, helper_cfg, holy_thing, nest)

    world.para()
    surprise_gift(world, elder, child, holy_thing_cfg, helper_cfg, theme)
    closing_image(world, child, pigeon, place)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "chapel_yard": Place(
        id="chapel_yard",
        label="the chapel yard",
        phrase="a little chapel yard with white stones and thyme between them",
        open_sky=True,
        perch_ids={"bell_arch", "apple_tree"},
        tags={"chapel", "holy"},
    ),
    "market_fountain": Place(
        id="market_fountain",
        label="the market fountain",
        phrase="the old market fountain where coins winked in the water",
        open_sky=True,
        perch_ids={"fountain_lion", "roof_gutter"},
        tags={"market", "fountain"},
    ),
    "cloister_garden": Place(
        id="cloister_garden",
        label="the cloister garden",
        phrase="a sheltered cloister garden wrapped in stone arches",
        open_sky=False,
        perch_ids={"stone_lintel"},
        tags={"garden", "quiet"},
    ),
}

THEMES = {
    "procession": PlayTheme(
        id="procession",
        scene="a holy procession",
        opening="play at being keeper of the little procession",
        role_word="keeper",
        goal="a star for a make-believe procession",
        sendoff="playing procession through the sunlight",
        tags={"play"},
    ),
    "fairy_court": PlayTheme(
        id="fairy_court",
        scene="a fairy court",
        opening="play at being queen of a fairy court",
        role_word="queen",
        goal="a crown jewel for a fairy court",
        sendoff="playing at a fairy court under the swallows",
        tags={"play", "fairy"},
    ),
    "pilgrim_quest": PlayTheme(
        id="pilgrim_quest",
        scene="a pilgrim quest",
        opening="play at being a brave pilgrim on a quest",
        role_word="pilgrim",
        goal="a guiding sign for a pilgrim road",
        sendoff="playing quest along the warm stones",
        tags={"play", "journey"},
    ),
}

HOLY_THINGS = {
    "ribbon_star": HolyThing(
        id="ribbon_star",
        label="holy ribbon star",
        phrase="a holy ribbon star tied with golden thread",
        sparkle="starry",
        use_line="When it turned in the sun, it looked almost alive.",
        lightness=1,
        holy_word="Blessing Day",
        portable=True,
        shiny=True,
        holy=True,
        tags={"holy", "star"},
    ),
    "silver_charm": HolyThing(
        id="silver_charm",
        label="holy silver charm",
        phrase="a holy silver charm no bigger than a plum leaf",
        sparkle="silver",
        use_line="It flashed like moonlight each time the child spun.",
        lightness=1,
        holy_word="Lantern Feast",
        portable=True,
        shiny=True,
        holy=True,
        tags={"holy", "silver"},
    ),
    "bell_token": HolyThing(
        id="bell_token",
        label="holy bell token",
        phrase="a holy bell token with a bright tin handle",
        sparkle="bright",
        use_line="It gave the play a brave and merry sound.",
        lightness=2,
        holy_word="Bell Morning",
        portable=True,
        shiny=True,
        holy=True,
        tags={"holy", "bell"},
    ),
    "candle_board": HolyThing(
        id="candle_board",
        label="holy candle board",
        phrase="a painted holy board for holding chapel candles",
        sparkle="painted",
        use_line="It was lovely, but broad as both hands together.",
        lightness=4,
        holy_word="Lantern Feast",
        portable=True,
        shiny=True,
        holy=True,
        tags={"holy", "candle"},
    ),
}

NEST_SPOTS = {
    "apple_tree": NestSpot(
        id="apple_tree",
        label="apple tree fork",
        phrase="the fork of the oldest apple tree",
        height=1,
        clue="a drifting feather and a curl of straw",
        discovery="The chicks blinked like three drops of soot with gold around their beaks.",
        tags={"tree", "nest"},
    ),
    "bell_arch": NestSpot(
        id="bell_arch",
        label="bell arch",
        phrase="the small arch below the chapel bell",
        height=2,
        clue="a silver thread caught on rough stone",
        discovery="The nest rocked softly whenever the bell rope moved in the breeze.",
        tags={"bell", "nest"},
    ),
    "fountain_lion": NestSpot(
        id="fountain_lion",
        label="fountain lion",
        phrase="the cracked stone lion above the fountain bowl",
        height=1,
        clue="a tiny straw stem lying by the water rim",
        discovery="The chicks peeped between the lion's paws as if the statue itself had begun to sing.",
        tags={"fountain", "nest"},
    ),
    "roof_gutter": NestSpot(
        id="roof_gutter",
        label="roof gutter",
        phrase="the sun-warmed gutter over the baker's stall",
        height=2,
        clue="one pale feather circling down beside the bread table",
        discovery="Warm air from the ovens rose around the nest like an invisible blanket.",
        tags={"roof", "nest"},
    ),
    "stone_lintel": NestSpot(
        id="stone_lintel",
        label="stone lintel",
        phrase="the quiet lintel over the cloister gate",
        height=2,
        clue="a scrap of dry moss caught in a crack",
        discovery="The nest sat hidden in a shadow where little feet would never have found it alone.",
        tags={"stone", "nest"},
    ),
}

HELPERS = {
    "gardener": Helper(
        id="gardener",
        type="man",
        label="the gardener",
        reach=1,
        action="steadying a small orchard ladder against the bark",
        gift="a new play star woven from willow leaves and marigold thread",
        tags={"ladder", "garden"},
    ),
    "bell_keeper": Helper(
        id="bell_keeper",
        type="woman",
        label="the bell keeper",
        reach=2,
        action="climbing carefully with a long, sure step",
        gift="a new play token made from a spare bell ribbon and a polished bead",
        tags={"bell", "climb"},
    ),
    "baker": Helper(
        id="baker",
        type="man",
        label="the baker",
        reach=2,
        action="standing on a flour crate and lifting a bread peel like a little bridge",
        gift="a round play badge cut from bright pastry foil and tied to blue string",
        tags={"baker", "reach"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Talia", "Rosa", "Elin", "Suri", "Nella", "Ada"]
BOY_NAMES = ["Tobin", "Milo", "Ren", "Ari", "Bram", "Luca", "Nico", "Oren"]
CHILD_TRAITS = ["gentle", "eager", "bright", "hopeful", "merry"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    theme: str
    holy_thing: str
    nest: str
    helper: str
    child_name: str
    child_gender: str
    elder_type: str
    child_trait: str
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
    "holy": [
        (
            "What does holy mean?",
            "Holy means something is treated as special and full of care, often for prayer or a festival. People handle holy things gently because they matter to the heart as well as to the hands."
        )
    ],
    "pigeon": [
        (
            "Why do pigeons carry little things to their nests?",
            "Pigeons gather small bits like straw, string, and shiny scraps when they build nests. They are not trying to be rude; they are following what helps them make a home."
        )
    ],
    "nest": [
        (
            "Why do baby birds need a nest?",
            "A nest keeps baby birds together and helps hold them safe and warm. It also gives the parent bird one place to bring food and watch over them."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know why something happened, but they are wrong. It can be fixed by slowing down, looking closely, and listening."
        )
    ],
    "surprise": [
        (
            "Can a surprise be kind?",
            "Yes. A kind surprise is something unexpected that helps, comforts, or delights someone. Good surprises often come after another person notices what you need."
        )
    ],
    "play": [
        (
            "Why is pretend play important?",
            "Pretend play lets children imagine, practice feelings, and turn ordinary places into adventures. It becomes even better when the play stays gentle and safe."
        )
    ],
}
KNOWLEDGE_ORDER = ["holy", "pigeon", "nest", "misunderstanding", "surprise", "play"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    thing = f["holy_thing_cfg"]
    theme = f["theme"]
    nest = f["nest"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that uses the words "holy", "play", and "pigeon".',
        f"Tell a gentle fairy-tale story where {child.id} is in {place.label}, uses {thing.label} in pretend play, and then misunderstands a pigeon that flies to {nest.phrase}.",
        f"Write a story with a misunderstanding and a surprise ending, where a child learns that a bird's puzzling act had a kind reason behind it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place"]
    theme = f["theme"]
    thing = f["holy_thing_cfg"]
    nest = f["nest"]
    helper = f["helper"]
    returned = f.get("returned", False)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child playing in {place.label}, and {elder.label_word} who helped when trouble came. A pigeon becomes important too, because the misunderstanding begins with it."
        ),
        (
            f"What was {child.id} doing before the trouble started?",
            f"{child.id} was using {thing.label} in pretend play and imagining {theme.scene}. The shining holy thing made the game feel grand and magical."
        ),
        (
            f"Why did {child.id} think the pigeon was mean?",
            f"{child.id} saw the pigeon grab the bright thing and fly away, so it looked like simple stealing. Because the loss happened in one quick flutter, {child.pronoun()} judged the bird before knowing the reason."
        ),
        (
            "What was the misunderstanding?",
            f"The misunderstanding was that {child.id} thought the pigeon wanted to spoil the game. Really, the bird was taking a bright little object toward its nest and did not understand the child's plans."
        ),
        (
            "What did they find at the nest?",
            f"They found tiny chicks in the nest, with the pigeon settling the shining thing beside them. That discovery changed the whole meaning of what had happened."
        ),
    ]
    if returned:
        qa.append(
            (
                f"Did {child.id} get the holy thing back?",
                f"Yes. {helper.label.capitalize()} could reach {nest.phrase} and gently handed it back. The return mattered, but even more important was that {child.id} had stopped blaming the pigeon."
            )
        )
    else:
        qa.append(
            (
                f"Why did they leave the holy thing in the nest?",
                f"They left it because the chicks were leaning against it and kindness mattered more than keeping the game exactly the same. The surprise ending still brought joy, because the grown-ups made a new play token for {child.id}."
            )
        )
    qa.append(
        (
            "What was the surprise at the end?",
            f"The surprise was {f['surprise']}. It let the play continue without troubling the nest, so the ending felt both happy and gentle."
        )
    )
    qa.append(
        (
            f"What did {child.id} learn?",
            f"{child.id} learned not to decide too quickly that another creature is being cruel. Looking closer brought understanding, and understanding made room for kindness."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"holy", "pigeon", "nest", "misunderstanding", "surprise", "play"}
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
# Trace
# ---------------------------------------------------------------------------
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
        flags = [name for name, on in (
            ("portable", ent.portable),
            ("shiny", ent.shiny),
            ("holy", ent.holy),
            ("open_sky", ent.open_sky),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: returned={world.facts.get('returned')} chicks_found={world.facts.get('chicks_found')} surprise={world.facts.get('surprise')!r}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Gate: a valid story needs an open place, a shiny portable holy thing light
% enough for a pigeon, a nest that belongs in that place, and at least one
% helper who can reach it.

pigeon_wants(Thing, Place) :- holy_thing(Thing), place(Place),
                              portable(Thing), shiny(Thing),
                              lightness(Thing, L), L <= 2,
                              open_sky(Place).

reachable_nest(Nest) :- helper(H), nest(Nest), reach(H, R), height(Nest, Ht), R >= Ht.

valid(Place, Theme, Thing, Nest) :- place(Place), theme(Theme), holy_thing(Thing), nest(Nest),
                                    nest_in(Place, Nest), pigeon_wants(Thing, Place),
                                    reachable_nest(Nest).

chosen_reachable :- chosen_helper(H), chosen_nest(N), reach(H, R), height(N, Ht), R >= Ht.
story_ok         :- chosen_place(P), chosen_theme(T), chosen_thing(Th), chosen_nest(N),
                    valid(P, T, Th, N), chosen_reachable.

returned         :- chosen_nest(N), height(N, Ht), Ht <= 1, story_ok.
kept_in_nest     :- story_ok, not returned.

outcome(returned) :- returned.
outcome(blessed)  :- kept_in_nest.

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.open_sky:
            lines.append(asp.fact("open_sky", pid))
        for nid in sorted(place.perch_ids):
            lines.append(asp.fact("nest_in", pid, nid))
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for hid, thing in HOLY_THINGS.items():
        lines.append(asp.fact("holy_thing", hid))
        if thing.portable:
            lines.append(asp.fact("portable", hid))
        if thing.shiny:
            lines.append(asp.fact("shiny", hid))
        lines.append(asp.fact("lightness", hid, thing.lightness))
    for nid, nest in NEST_SPOTS.items():
        lines.append(asp.fact("nest", nid))
        lines.append(asp.fact("height", nid, nest.height))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("reach", helper_id, helper.reach))
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
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_theme", params.theme),
        asp.fact("chosen_thing", params.holy_thing),
        asp.fact("chosen_nest", params.nest),
        asp.fact("chosen_helper", params.helper),
        "#show outcome/1.",
    ])
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    nest = NEST_SPOTS[params.nest]
    helper = HELPERS[params.helper]
    if not helper_can_reach(helper, nest):
        return "?"
    return "returned" if nest.height <= 1 else "blessed"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(50):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="")  # ordinary generation smoke test
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="chapel_yard",
        theme="procession",
        holy_thing="ribbon_star",
        nest="apple_tree",
        helper="gardener",
        child_name="Mira",
        child_gender="girl",
        elder_type="aunt",
        child_trait="gentle",
    ),
    StoryParams(
        place="chapel_yard",
        theme="fairy_court",
        holy_thing="silver_charm",
        nest="bell_arch",
        helper="bell_keeper",
        child_name="Luca",
        child_gender="boy",
        elder_type="nun",
        child_trait="bright",
    ),
    StoryParams(
        place="market_fountain",
        theme="pilgrim_quest",
        holy_thing="bell_token",
        nest="roof_gutter",
        helper="baker",
        child_name="Rosa",
        child_gender="girl",
        elder_type="uncle",
        child_trait="eager",
    ),
    StoryParams(
        place="market_fountain",
        theme="fairy_court",
        holy_thing="ribbon_star",
        nest="fountain_lion",
        helper="gardener",
        child_name="Milo",
        child_gender="boy",
        elder_type="father",
        child_trait="merry",
    ),
]


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a child, a holy plaything, a pigeon misunderstanding, and a surprise."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--holy-thing", dest="holy_thing", choices=HOLY_THINGS)
    ap.add_argument("--nest", choices=NEST_SPOTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("--elder", dest="elder_type", choices=["aunt", "uncle", "mother", "father", "nun", "monk"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.nest:
        if args.nest not in PLACES[args.place].perch_ids:
            raise StoryError(explain_combo_rejection(PLACES[args.place], HOLY_THINGS[args.holy_thing or next(iter(HOLY_THINGS))], NEST_SPOTS[args.nest]))
    if args.place and args.holy_thing:
        if not pigeon_wants(HOLY_THINGS[args.holy_thing], PLACES[args.place]):
            nest_id = args.nest or next(iter(PLACES[args.place].perch_ids))
            raise StoryError(explain_combo_rejection(PLACES[args.place], HOLY_THINGS[args.holy_thing], NEST_SPOTS[nest_id]))
    if args.helper and args.nest:
        if not helper_can_reach(HELPERS[args.helper], NEST_SPOTS[args.nest]):
            raise StoryError(explain_helper_rejection(args.helper, args.nest))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.theme is None or combo[1] == args.theme)
        and (args.holy_thing is None or combo[2] == args.holy_thing)
        and (args.nest is None or combo[3] == args.nest)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, theme_id, holy_thing_id, nest_id = rng.choice(sorted(combos))
    helper_choices = [
        hid for hid in suitable_helpers(nest_id)
        if args.helper is None or hid == args.helper
    ]
    if not helper_choices:
        raise StoryError(explain_helper_rejection(args.helper, nest_id))
    helper_id = rng.choice(helper_choices)

    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    elder_type = args.elder_type or rng.choice(["aunt", "uncle", "mother", "father", "nun", "monk"])
    child_trait = rng.choice(CHILD_TRAITS)

    return StoryParams(
        place=place_id,
        theme=theme_id,
        holy_thing=holy_thing_id,
        nest=nest_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.holy_thing not in HOLY_THINGS:
        raise StoryError(f"(Unknown holy thing: {params.holy_thing})")
    if params.nest not in NEST_SPOTS:
        raise StoryError(f"(Unknown nest: {params.nest})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    place = PLACES[params.place]
    holy_thing = HOLY_THINGS[params.holy_thing]
    nest = NEST_SPOTS[params.nest]
    helper = HELPERS[params.helper]

    if params.nest not in place.perch_ids or not pigeon_wants(holy_thing, place):
        raise StoryError(explain_combo_rejection(place, holy_thing, nest))
    if not helper_can_reach(helper, nest):
        raise StoryError(explain_helper_rejection(params.helper, params.nest))

    world = tell(
        place=place,
        theme=THEMES[params.theme],
        holy_thing_cfg=holy_thing,
        nest=nest,
        helper_cfg=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
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
        print(asp_program("#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, theme, holy_thing, nest) combos:\n")
        for place, theme, holy_thing, nest in combos:
            helpers = ", ".join(suitable_helpers(nest))
            print(f"  {place:15} {theme:13} {holy_thing:12} {nest:13}  helpers=[{helpers}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.holy_thing} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
