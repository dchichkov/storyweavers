#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/merry_snapper_still_sound_effects_rhyming_story.py
==============================================================================

A standalone story world for a tiny rhyming domain:

A child brings a clicky "snapper" on a nature walk and wants to make noise to
draw a shy creature closer. But shy creatures do not like loud surprises.
The sensible fix is to become still and use a fitting quiet lure. Then the
creature comes close on its own.

This world models a child-facing beginning, tension, turn, and ending image
through simulated state: noise raises alarm, alarm drives retreat, and quiet
waiting plus the right lure invites a creature back. The rendered story is a
rhyming story with sound effects.

Run it
------
    python storyworlds/worlds/gpt-5.4/merry_snapper_still_sound_effects_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/merry_snapper_still_sound_effects_rhyming_story.py --place pond --creature duck --lure crumbs
    python storyworlds/worlds/gpt-5.4/merry_snapper_still_sound_effects_rhyming_story.py --creature rabbit --lure crumbs
    python storyworlds/worlds/gpt-5.4/merry_snapper_still_sound_effects_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/merry_snapper_still_sound_effects_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/merry_snapper_still_sound_effects_rhyming_story.py --trace
    python storyworlds/worlds/gpt-5.4/merry_snapper_still_sound_effects_rhyming_story.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    path: str
    hush: str
    affords: set[str] = field(default_factory=set)
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
class Creature:
    id: str
    label: str
    phrase: str
    home: str
    step: str
    sound: str
    approach_line: str
    patience_need: int
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
class Snapper:
    id: str
    label: str
    phrase: str
    sound1: str
    sound2: str
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
class Lure:
    id: str
    label: str
    phrase: str
    quiet_action: str
    resting_spot: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "noise_event": False,
            "retreated": False,
            "approached": False,
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_noise_startles(world: World) -> list[str]:
    child = world.get("child")
    creature = world.get("creature")
    if child.meters["noise"] < THRESHOLD:
        return []
    sig = ("noise_startles", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["alarm"] += 1
    creature.memes["fear"] += 1
    child.memes["oops"] += 1
    world.facts["noise_event"] = True
    return ["__startle__"]


def _r_alarm_retreats(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["alarm"] < THRESHOLD:
        return []
    sig = ("alarm_retreats", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["distance"] += 1
    creature.memes["shy"] += 1
    world.facts["retreated"] = True
    return ["__retreat__"]


def _r_still_plus_lure(world: World) -> list[str]:
    child = world.get("child")
    creature = world.get("creature")
    lure = world.get("lure")
    if child.meters["still"] < THRESHOLD:
        return []
    if child.meters["patience"] < creature.attrs["patience_need"]:
        return []
    if child.attrs.get("lure") not in creature.attrs.get("likes", set()):
        return []
    sig = ("still_plus_lure", creature.id, lure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["distance"] = 0.0
    creature.meters["alarm"] = 0.0
    creature.memes["trust"] += 1
    child.memes["wonder"] += 1
    child.memes["joy"] += 1
    world.facts["approached"] = True
    return ["__approach__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_startles", tag="physical", apply=_r_noise_startles),
    Rule(name="alarm_retreats", tag="physical", apply=_r_alarm_retreats),
    Rule(name="still_plus_lure", tag="social", apply=_r_still_plus_lure),
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
        for sent in produced:
            world.say(sent)
    return produced


def creature_fits_place(place: Place, creature: Creature) -> bool:
    return creature.id in place.affords


def lure_fits_creature(creature: Creature, lure: Lure) -> bool:
    return lure.id in creature.likes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for creature_id, creature in CREATURES.items():
            if not creature_fits_place(place, creature):
                continue
            for lure_id, lure in LURES.items():
                if lure_fits_creature(creature, lure):
                    combos.append((place_id, creature_id, lure_id))
    return combos


def explain_rejection(place: Place, creature: Creature, lure: Lure) -> str:
    if not creature_fits_place(place, creature):
        return (
            f"(No story: {creature.phrase} does not belong at {place.label} in this little world. "
            f"Pick a creature that really fits that place.)"
        )
    if not lure_fits_creature(creature, lure):
        return (
            f"(No story: {lure.phrase} would not honestly tempt {creature.phrase}. "
            f"The quiet lure has to be something that creature actually likes.)"
        )
    return "(No story: this combination does not make a reasonable nature-watching story.)"


def predict_with_noise(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["noise"] += 1
    propagate(sim, narrate=False)
    creature = sim.get("creature")
    return {
        "retreated": sim.facts["retreated"],
        "distance": creature.meters["distance"],
        "alarm": creature.meters["alarm"],
    }


def setup_walk(world: World, child: Entity, parent: Entity, snapper: Snapper, creature: Creature) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} skipped with a merry grin beside {child.pronoun('possessive')} "
        f"{parent.label_word} through {world.place.phrase}. "
        f"{world.place.hush}"
    )
    world.say(
        f"In {child.pronoun('possessive')} pocket waited {snapper.phrase}, a little clicky snapper "
        f"that went {snapper.sound1}! and {snapper.sound2}!"
    )
    world.say(
        f"Near {creature.home}, {child.id} whispered, "
        f"\"I hope we see {creature.phrase} before the sun slides low.\""
    )


def spot_creature(world: World, child: Entity, creature: Creature) -> None:
    world.say(
        f"Soon {child.pronoun()} saw a small shape by {creature.home}. "
        f"It was {creature.phrase}, quiet and shy, with a {creature.step} step and a {creature.sound} cry."
    )


def tempting_idea(world: World, child: Entity, snapper: Snapper) -> None:
    child.memes["impatience"] += 1
    world.say(
        f'"Maybe my snapper can make it come quicker," said {child.id}. '
        f'"Just {snapper.sound1}! {snapper.sound2}! -- a bright little flicker!"'
    )


def warning(world: World, parent: Entity, child: Entity, creature: Creature) -> None:
    pred = predict_with_noise(world)
    world.facts["predicted_retreat"] = pred["retreated"]
    world.facts["predicted_alarm"] = pred["alarm"]
    child.memes["caution"] += 1
    world.say(
        f'{parent.label_word.capitalize()} shook {parent.pronoun("possessive")} head and said, '
        f'"Loud clicks do not help shy feet. They make {creature.label} hurry back instead."'
    )
    if pred["retreated"]:
        world.say(
            f'"If you clap and snap, it will scoot away. '
            f'The best hello is gentle: be still, and wait."'
        )


def noisy_try(world: World, child: Entity, snapper: Snapper, creature: Creature) -> None:
    child.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {child.id} gave the merry snapper a try: "
        f"{snapper.sound1}! {snapper.sound2}! went the toy nearby."
    )
    if world.facts["retreated"]:
        world.say(
            f"At once {creature.label} gave a start -- "
            f"zip! skip! hush! -- and darted back to the dim green part."
        )


def regret(world: World, child: Entity) -> None:
    child.memes["regret"] += 1
    world.say(
        f"{child.id} let the snapper droop. "
        f'"Oh dear," {child.pronoun()} sighed, "my noisy plan was wrong, not right."'
    )


def teach_stillness(world: World, parent: Entity, child: Entity, lure: Lure, creature: Creature) -> None:
    child.meters["still"] += 1
    child.meters["patience"] += float(creature.patience_need)
    child.attrs["lure"] = lure.id
    world.say(
        f'{parent.label_word.capitalize()} smiled and set down {lure.phrase} on {lure.resting_spot}. '
        f'"Now fold your hands. Be still as a hill. Let quiet do the clever skill."'
    )
    world.say(
        f"{child.id} crouched low, held very still, and watched without a peep or shrill."
    )
    propagate(world, narrate=False)


def creature_returns(world: World, creature: Creature, lure: Lure) -> None:
    if world.facts["approached"]:
        world.say(
            f"Then came a tiny sound -- {creature.sound}! {creature.sound}! -- "
            f"and back came {creature.label} with a careful bound. "
            f"{creature.approach_line} toward {lure.label}, calm and slow."
        )


def ending(world: World, child: Entity, parent: Entity, snapper: Snapper, creature: Creature) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'Soon {creature.label} was close enough for {child.id} to see bright eyes and gentle toes. '
        f'"I know now," said {child.pronoun()}, "fast noise makes fast good-byes."'
    )
    world.say(
        f'{parent.label_word.capitalize()} nodded. "Yes. For shy hearts, quiet is the kinder art."'
    )
    world.say(
        f"So home they went through evening light. "
        f"The snapper stayed still in {child.pronoun('possessive')} pocket that night, "
        f"and the merry child kept one softer song: hush-hush, wait-wait, and wonder comes along."
    )


def tell(
    place: Place,
    creature_cfg: Creature,
    snapper_cfg: Snapper,
    lure_cfg: Lure,
    *,
    child_name: str = "Mia",
    child_gender: str = "girl",
    parent_type: str = "mother",
    child_trait: str = "patient",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            traits=[child_trait, "merry"],
            attrs={"lure": ""},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    creature = world.add(
        Entity(
            id="creature",
            kind="thing",
            type="creature",
            label=creature_cfg.label,
            phrase=creature_cfg.phrase,
            role="creature",
            attrs={
                "likes": set(creature_cfg.likes),
                "patience_need": creature_cfg.patience_need,
            },
            tags=set(creature_cfg.tags),
        )
    )
    snapper = world.add(
        Entity(
            id="snapper",
            kind="thing",
            type="tool",
            label=snapper_cfg.label,
            phrase=snapper_cfg.phrase,
            role="tool",
            tags=set(snapper_cfg.tags),
        )
    )
    lure = world.add(
        Entity(
            id="lure",
            kind="thing",
            type="lure",
            label=lure_cfg.label,
            phrase=lure_cfg.phrase,
            role="lure",
            tags=set(lure_cfg.tags),
        )
    )

    creature.meters["distance"] = 0.0
    creature.meters["alarm"] = 0.0
    child.meters["noise"] = 0.0
    child.meters["still"] = 0.0
    child.meters["patience"] = 0.0

    setup_walk(world, child, parent, snapper_cfg, creature_cfg)
    spot_creature(world, child, creature_cfg)

    world.para()
    tempting_idea(world, child, snapper_cfg)
    warning(world, parent, child, creature_cfg)
    noisy_try(world, child, snapper_cfg, creature_cfg)
    regret(world, child)

    world.para()
    teach_stillness(world, parent, child, lure_cfg, creature_cfg)
    creature_returns(world, creature_cfg, lure_cfg)
    ending(world, child, parent, snapper_cfg, creature_cfg)

    world.facts.update(
        child=child,
        parent=parent,
        creature_cfg=creature_cfg,
        creature=creature,
        snapper_cfg=snapper_cfg,
        snapper=snapper,
        lure_cfg=lure_cfg,
        lure=lure,
        place=place,
        lesson_learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


PLACES = {
    "pond": Place(
        id="pond",
        label="the pond",
        phrase="the pond path",
        path="the pond path",
        hush="The reeds made a soft swish-swish, and the water kept still as glass.",
        affords={"duck", "frog"},
        tags={"pond"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        phrase="the garden gate",
        path="the garden path",
        hush="The leaves went rustle-rustle, and the flowers nodded in the sun.",
        affords={"rabbit", "butterfly"},
        tags={"garden"},
    ),
    "meadow": Place(
        id="meadow",
        label="the meadow",
        phrase="the meadow lane",
        path="the meadow lane",
        hush="Tall grass went shhh-shhh around their knees, and the air smelled sweet.",
        affords={"rabbit", "butterfly", "frog"},
        tags={"meadow"},
    ),
}

CREATURES = {
    "duck": Creature(
        id="duck",
        label="the duck",
        phrase="a shy little duck",
        home="the reeds",
        step="waddle-tip",
        sound="quack",
        approach_line="Waddle-waddle, closer it came",
        patience_need=1,
        likes={"crumbs"},
        tags={"duck", "pond"},
    ),
    "frog": Creature(
        id="frog",
        label="the frog",
        phrase="a shy green frog",
        home="the lily pads",
        step="hop-pop",
        sound="ribbit",
        approach_line="Hop-hop, soft as a drop, it came",
        patience_need=2,
        likes={"berry"},
        tags={"frog", "pond"},
    ),
    "rabbit": Creature(
        id="rabbit",
        label="the rabbit",
        phrase="a shy brown rabbit",
        home="the clover patch",
        step="tip-hop",
        sound="sniff",
        approach_line="Tip-hop, tip-hop, closer it came",
        patience_need=2,
        likes={"leaf"},
        tags={"rabbit", "garden"},
    ),
    "butterfly": Creature(
        id="butterfly",
        label="the butterfly",
        phrase="a shy gold butterfly",
        home="the marigolds",
        step="flutter-drift",
        sound="flit",
        approach_line="Flit-flit, down through the glow it came",
        patience_need=1,
        likes={"flower"},
        tags={"butterfly", "garden"},
    ),
}

SNAPPERS = {
    "clicker": Snapper(
        id="clicker",
        label="snapper",
        phrase="a red toy snapper",
        sound1="click-click",
        sound2="snap-snap",
        tags={"snapper", "noise"},
    ),
    "clacker": Snapper(
        id="clacker",
        label="snapper",
        phrase="a blue pocket snapper",
        sound1="clack-clack",
        sound2="snap-snap",
        tags={"snapper", "noise"},
    ),
}

LURES = {
    "crumbs": Lure(
        id="crumbs",
        label="crumbs",
        phrase="a few soft crumbs",
        quiet_action="scatter a few soft crumbs",
        resting_spot="a flat stone",
        tags={"crumbs"},
    ),
    "berry": Lure(
        id="berry",
        label="a berry",
        phrase="one bright berry",
        quiet_action="set down one bright berry",
        resting_spot="a dry leaf",
        tags={"berry"},
    ),
    "leaf": Lure(
        id="leaf",
        label="a clover leaf",
        phrase="a fresh clover leaf",
        quiet_action="set down a fresh clover leaf",
        resting_spot="a warm patch of dirt",
        tags={"leaf"},
    ),
    "flower": Lure(
        id="flower",
        label="a flower",
        phrase="a sunny flower",
        quiet_action="hold still beside a sunny flower",
        resting_spot="the low stone wall",
        tags={"flower"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Theo"]
TRAITS = ["patient", "curious", "gentle", "eager", "bright"]


@dataclass
class StoryParams:
    place: str
    creature: str
    lure: str
    snapper: str
    child_name: str
    child_gender: str
    parent: str
    child_trait: str
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


KNOWLEDGE = {
    "snapper": [
        (
            "What is a snapper in this story?",
            "It is a little clicky toy that makes a snapping sound. A loud toy can be fun, but it is not a good way to greet shy animals.",
        )
    ],
    "still": [
        (
            "Why does staying still help with shy animals?",
            "Many shy animals feel safer when people stop moving and making noise. Quiet waiting gives them time to look, listen, and come closer on their own.",
        )
    ],
    "duck": [
        (
            "Why might a duck walk away from a loud sound?",
            "A duck does not know if a sudden loud sound is safe. Moving away helps it protect itself.",
        )
    ],
    "frog": [
        (
            "Why are frogs easy to scare?",
            "Frogs are small and watchful, so quick noise or movement can make them hop away fast. Staying calm helps them feel safer.",
        )
    ],
    "rabbit": [
        (
            "Why do rabbits freeze or run when they feel unsure?",
            "Rabbits are prey animals, so they pay close attention to danger. If something feels sudden or loud, they often dash away.",
        )
    ],
    "butterfly": [
        (
            "Why can butterflies be hard to watch up close?",
            "Butterflies are light and delicate, and they flutter off when the space around them feels disturbed. Calm waiting near flowers gives them a better chance to settle.",
        )
    ],
    "quiet": [
        (
            "What is a quiet way to watch an animal?",
            "Stand or sit calmly, keep your hands gentle, and let the animal choose the distance. Quiet watching is kinder than chasing or surprising it.",
        )
    ],
    "lure": [
        (
            "Why does the right food or flower matter?",
            "Different creatures notice different things they like. A good quiet lure works because it fits the creature instead of forcing it with noise.",
        )
    ],
}
KNOWLEDGE_ORDER = ["snapper", "still", "quiet", "lure", "duck", "frog", "rabbit", "butterfly"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    creature = f["creature_cfg"]
    place = f["place"]
    lure = f["lure_cfg"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the words "merry", "snapper", and "still". Use sound effects.',
        f"Tell a gentle nature story where {child.id} tries a merry snapper near {place.label}, scares {creature.label}, and then learns to be still so it can come back.",
        f"Write a child-facing poem-story with clicky sound effects in which the right quiet lure is {lure.label} and the lesson is that shy animals like calm waiting better than noisy snapping.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    creature_cfg = f["creature_cfg"]
    lure_cfg = f["lure_cfg"]
    snapper_cfg = f["snapper_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a merry child on a walk with {child.pronoun('possessive')} {parent.label_word}. They were hoping to see {creature_cfg.phrase} at {place.label}.",
        ),
        (
            f"Why did {child.id} use the snapper at first?",
            f"{child.id} wanted {creature_cfg.label} to come faster, so {child.pronoun()} tried the {snapper_cfg.label}. The idea seemed cheerful and clever, but it did not match what a shy creature needs.",
        ),
    ]
    if f.get("retreated"):
        qa.append(
            (
                f"What happened when the snapper went {snapper_cfg.sound1} and {snapper_cfg.sound2}?",
                f"{creature_cfg.label.capitalize()} jumped away instead of coming closer. The sudden noise made it feel alarmed, so it hurried back toward {creature_cfg.home}.",
            )
        )
    qa.append(
        (
            f"How did {child.id} help {creature_cfg.label} come back?",
            f"{child.id} stopped making noise, held very still, and waited with {lure_cfg.phrase}. That gentle plan worked because quiet and the right lure made the creature feel safer.",
        )
    )
    if f.get("approached"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with {creature_cfg.label} coming close in a calm way while {child.id} watched softly. The ending shows what changed: the snapper stayed still, and quiet patience brought the wonder back.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"snapper", "still", "quiet", "lure"}
    tags |= set(f["creature_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pond",
        creature="duck",
        lure="crumbs",
        snapper="clicker",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        child_trait="curious",
    ),
    StoryParams(
        place="pond",
        creature="frog",
        lure="berry",
        snapper="clacker",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        child_trait="patient",
    ),
    StoryParams(
        place="garden",
        creature="rabbit",
        lure="leaf",
        snapper="clicker",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        child_trait="gentle",
    ),
    StoryParams(
        place="garden",
        creature="butterfly",
        lure="flower",
        snapper="clacker",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        child_trait="bright",
    ),
]


ASP_RULES = r"""
fits(P,C) :- place(P), creature(C), affords(P,C).
likes(C,L) :- creature(C), lure(L), creature_likes(C,L).
valid(P,C,L) :- fits(P,C), likes(C,L).

noise_happens :- chosen_snapper(_).
retreated :- noise_happens, chosen_creature(C), shy(C).
still_plan :- chosen_lure(L), chosen_creature(C), likes(C,L).
approached :- still_plan.
lesson(learned) :- retreated, approached.

#show valid/3.
#show lesson/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for creature_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, creature_id))
    for creature_id in CREATURES:
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("shy", creature_id))
    for lure_id in LURES:
        lines.append(asp.fact("lure", lure_id))
    for snapper_id in SNAPPERS:
        lines.append(asp.fact("snapper", snapper_id))
    for creature_id, creature in CREATURES.items():
        for lure_id in sorted(creature.likes):
            lines.append(asp.fact("creature_likes", creature_id, lure_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_lesson_for(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_creature", params.creature),
            asp.fact("chosen_lure", params.lure),
            asp.fact("chosen_snapper", params.snapper),
        ]
    )
    model = asp.one_model(asp_program(extra=scenario, show="#show lesson/1."))
    items = asp.atoms(model, "lesson")
    return items[0][0] if items else "none"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
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
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    bad = 0
    for params in CURATED:
        if asp_lesson_for(params) != "learned":
            bad += 1
    if bad == 0:
        print(f"OK: ASP lesson model matches curated outcomes ({len(CURATED)} cases).")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(CURATED)} curated ASP lesson checks failed.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a merry child, a clicky snapper, and the lesson of being still."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--snapper", choices=SNAPPERS)
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
    if args.place and args.creature and args.lure:
        place = PLACES[args.place]
        creature = CREATURES[args.creature]
        lure = LURES[args.lure]
        if not (creature_fits_place(place, creature) and lure_fits_creature(creature, lure)):
            raise StoryError(explain_rejection(place, creature, lure))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.lure is None or combo[2] == args.lure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, lure_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    snapper = args.snapper or rng.choice(sorted(SNAPPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        creature=creature_id,
        lure=lure_id,
        snapper=snapper,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        child_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.snapper not in SNAPPERS:
        raise StoryError(f"(Unknown snapper: {params.snapper})")

    place = PLACES[params.place]
    creature = CREATURES[params.creature]
    lure = LURES[params.lure]
    if not creature_fits_place(place, creature) or not lure_fits_creature(creature, lure):
        raise StoryError(explain_rejection(place, creature, lure))

    world = tell(
        place=place,
        creature_cfg=creature,
        snapper_cfg=SNAPPERS[params.snapper],
        lure_cfg=lure,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creature, lure) combos:\n")
        for place_id, creature_id, lure_id in combos:
            print(f"  {place_id:8} {creature_id:10} {lure_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.creature} at {p.place} with {p.lure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
