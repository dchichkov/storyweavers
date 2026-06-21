#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/envelope_suck_beep_sharing_humor_suspense_nursery.py
===============================================================================

A standalone story world for a tiny nursery-rhyme-like domain:

Two small friends find a mysterious envelope that goes beep in a quiet corner of
their day. One friend wants the surprise first. The other notices clues, slows
things down, and helps open it the sensible way. The turn comes when the mystery
inside proves meant to be shared, and the ending image shows the pair playing
together instead of clutching alone.

Required seed words appear naturally in the child-facing prose:
- envelope
- suck
- beep

This world keeps a simple common-sense gate:
- the opening method must fit the kind of seal on the envelope
- obviously silly / yucky methods are known but refused
- the inside gift must support a real sharing ending

It also includes an inline ASP twin for the compatibility gate and the sharing
mode inference, plus verification that compares the Python and ASP views and
smoke-tests ordinary story generation.

Run it
------
    python storyworlds/worlds/gpt-5.4/envelope_suck_beep_sharing_humor_suspense_nursery.py
    python storyworlds/worlds/gpt-5.4/envelope_suck_beep_sharing_humor_suspense_nursery.py --all
    python storyworlds/worlds/gpt-5.4/envelope_suck_beep_sharing_humor_suspense_nursery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/envelope_suck_beep_sharing_humor_suspense_nursery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


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
        female = {"girl", "hen", "duck", "mouse_girl"}
        male = {"boy", "mouse_boy", "frog", "toad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")
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
    verse: str
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
class Seal:
    id: str
    label: str
    description: str
    opener_ids: set[str]
    clue: str
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
class Opener:
    id: str
    label: str
    sense: int
    opens: set[str]
    action: str
    fail: str
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
class Gift:
    id: str
    label: str
    phrase: str
    share_mode: str
    ending: str
    count: int = 1
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
class Beeper:
    id: str
    label: str
    beep_word: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_beep_suspense(world: World) -> list[str]:
    env = world.entities.get("envelope")
    if env is None or env.meters["beeping"] < THRESHOLD:
        return []
    sig = ("beep_suspense",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid_id in ("finder", "friend"):
        if kid_id in world.entities:
            world.get(kid_id).memes["suspense"] += 1
            world.get(kid_id).memes["curiosity"] += 1
    return ["__beep__"]


def _r_sticky_humor(world: World) -> list[str]:
    env = world.entities.get("envelope")
    if env is None or env.meters["sticky"] < THRESHOLD or env.meters["silly_attempt"] < THRESHOLD:
        return []
    sig = ("sticky_humor",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid_id in ("finder", "friend"):
        if kid_id in world.entities:
            world.get(kid_id).memes["giggle"] += 1
    return ["__giggle__"]


def _r_open_relief(world: World) -> list[str]:
    env = world.entities.get("envelope")
    if env is None or env.meters["opened"] < THRESHOLD:
        return []
    sig = ("open_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid_id in ("finder", "friend"):
        if kid_id in world.entities:
            world.get(kid_id).memes["suspense"] = 0.0
            world.get(kid_id).memes["relief"] += 1
    return []


def _r_share_joy(world: World) -> list[str]:
    if world.facts.get("shared_mode", "") == "":
        return []
    sig = ("share_joy", world.facts["shared_mode"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid_id in ("finder", "friend"):
        if kid_id in world.entities:
            world.get(kid_id).memes["joy"] += 1
            world.get(kid_id).memes["kindness"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="beep_suspense", tag="emotional", apply=_r_beep_suspense),
    Rule(name="sticky_humor", tag="emotional", apply=_r_sticky_humor),
    Rule(name="open_relief", tag="emotional", apply=_r_open_relief),
    Rule(name="share_joy", tag="emotional", apply=_r_share_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "gate": Place(
        id="gate",
        label="the garden gate",
        verse="By the garden gate so green, where beans climbed up and birds were seen,",
        tags={"garden"},
    ),
    "step": Place(
        id="step",
        label="the mossy step",
        verse="On the mossy step one sunny noon, where snails went by a silver spoon,",
        tags={"doorstep"},
    ),
    "windowsill": Place(
        id="windowsill",
        label="the nursery windowsill",
        verse="On the nursery windowsill, where the shadows sat quite still,",
        tags={"window"},
    ),
}

SEALS = {
    "sticker": Seal(
        id="sticker",
        label="a round berry sticker",
        description="The flap wore a round berry sticker.",
        opener_ids={"peel"},
        clue="The sticker sat neat and smooth, waiting to be peeled the gentle way.",
        tags={"sticker"},
    ),
    "twine": Seal(
        id="twine",
        label="a blue twine bow",
        description="A blue twine bow looped the little flap tight.",
        opener_ids={"untie"},
        clue="The bow had loops like tiny ears, asking for patient fingers.",
        tags={"twine"},
    ),
    "wax": Seal(
        id="wax",
        label="a red wax dot",
        description="A red wax dot shone like a berry bead on the flap.",
        opener_ids={"warm_spoon"},
        clue="The wax looked firm and glossy, the kind that needs a grown-up's warm spoon.",
        tags={"wax"},
    ),
}

OPENERS = {
    "peel": Opener(
        id="peel",
        label="peel the flap",
        sense=3,
        opens={"sticker"},
        action="lifted the sticker edge and peeled the flap open with a slow, soft pull",
        fail="picked at the wrong sort of seal, and the envelope only crinkled and held fast",
        tags={"open"},
    ),
    "untie": Opener(
        id="untie",
        label="untie the bow",
        sense=3,
        opens={"twine"},
        action="pinched the bow loops and untied the twine with careful little paws",
        fail="tugged at the flap, but the knot only puckered tighter",
        tags={"open"},
    ),
    "warm_spoon": Opener(
        id="warm_spoon",
        label="ask for a warm spoon",
        sense=3,
        opens={"wax"},
        action="called for a grown-up, who touched the wax with a warm spoon until the flap came free",
        fail="waited politely, but without the right help the wax would not let go",
        tags={"grownup", "open"},
    ),
    "suck_corner": Opener(
        id="suck_corner",
        label="suck the corner",
        sense=1,
        opens=set(),
        action="gave the corner a silly suck",
        fail="made a funny face, and the paper tasted dreadful while the seal stayed shut",
        tags={"silly"},
    ),
}

GIFTS = {
    "two_badges": Gift(
        id="two_badges",
        label="two star badges",
        phrase="two star badges as bright as buttercups",
        share_mode="one_each",
        ending="Each friend pinned on one badge, and the pair went skip-skip down the path with matching stars.",
        count=2,
        tags={"sharing", "stars"},
    ),
    "bell_button": Gift(
        id="bell_button",
        label="a bell button",
        phrase="one round bell button with a tiny gold ring",
        share_mode="take_turns",
        ending="They took turns pressing the bell button, and every merry beep made both of them laugh.",
        count=1,
        tags={"sharing", "bell"},
    ),
    "long_ribbon": Gift(
        id="long_ribbon",
        label="a long ribbon",
        phrase="one long ribbon, red as jam and twice as twisty",
        share_mode="hold_ends",
        ending="They held one end each, and the ribbon danced between them like a little red stream.",
        count=1,
        tags={"sharing", "ribbon"},
    ),
}

BEEPERS = {
    "timer": Beeper(
        id="timer",
        label="a tiny timer chip",
        beep_word="beep",
        reveal="Inside sat a tiny timer chip that went beep every few breaths.",
        tags={"beep"},
    ),
    "chick": Beeper(
        id="chick",
        label="a peeping chick pin",
        beep_word="beep",
        reveal="Inside sat a peeping chick pin that answered the room with a brave little beep.",
        tags={"beep", "chick"},
    ),
    "button": Beeper(
        id="button",
        label="a comic beep button",
        beep_word="beep",
        reveal="Inside sat a comic beep button, so round and solemn that it looked important until it went beep again.",
        tags={"beep", "joke"},
    ),
}

FINDER_NAMES = ["Pip", "Mim", "Dot", "Nip", "Tess", "Moss"]
FRIEND_NAMES = ["Pip", "Mim", "Dot", "Nip", "Tess", "Moss"]
FINDER_TYPES = ["mouse_boy", "mouse_girl", "frog", "duck", "hen"]


@dataclass
class StoryParams:
    place: str
    seal: str
    opener: str
    gift: str
    beeper: str
    finder_name: str
    finder_type: str
    friend_name: str
    friend_type: str
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


def gift_supports_sharing(gift: Gift) -> bool:
    return gift.share_mode in {"one_each", "take_turns", "hold_ends"}


def opener_fits(seal: Seal, opener: Opener) -> bool:
    return opener.id in seal.opener_ids and seal.id in opener.opens


def sensible_openers() -> list[Opener]:
    return [o for o in OPENERS.values() if o.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for seal_id, seal in SEALS.items():
            for opener in sensible_openers():
                if not opener_fits(seal, opener):
                    continue
                for gift_id, gift in GIFTS.items():
                    if not gift_supports_sharing(gift):
                        continue
                    for beeper_id in BEEPERS:
                        combos.append((place_id, seal_id, opener.id, gift_id, beeper_id))
    return combos


def sharing_outcome(gift: Gift) -> str:
    return gift.share_mode


def predict_opening(world: World, seal_id: str, opener_id: str) -> dict:
    sim = world.copy()
    seal = SEALS[seal_id]
    opener = OPENERS[opener_id]
    env = sim.get("envelope")
    if seal.id == "sticker":
        env.meters["sticky"] = 1.0
    if opener.id == "suck_corner":
        env.meters["silly_attempt"] = 1.0
        propagate(sim, narrate=False)
    if opener_fits(seal, opener):
        env.meters["opened"] = 1.0
        propagate(sim, narrate=False)
    return {
        "opens": env.meters["opened"] >= THRESHOLD,
        "giggles": sum(sim.get(eid).memes["giggle"] for eid in ("finder", "friend") if eid in sim.entities),
    }


def introduce(world: World, finder: Entity, friend: Entity) -> None:
    world.say(world.place.verse)
    world.say(
        f"there skipped {finder.id} and {friend.id}, two little friends with bright quick feet."
    )
    world.say(
        f"They liked to rhyme, they liked to roam, and laugh their way from hedge to home."
    )


def find_envelope(world: World, finder: Entity, friend: Entity, seal: Seal) -> None:
    env = world.get("envelope")
    env.meters["found"] = 1.0
    world.say(
        f"Then {finder.id} cried, \"Look! A little envelope!\" "
        f"It rested by {world.place.label}, pale and plump and neat."
    )
    world.say(seal.description)
    world.say(
        f'"Who could it be for?" asked {friend.id}. '
        f'The pair bent close on tiptoe toes.'
    )


def hear_beep(world: World, finder: Entity, friend: Entity, beeper: Beeper) -> None:
    env = world.get("envelope")
    env.meters["beeping"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Before either friend could guess another guess, the envelope said {beeper.beep_word}! "
        f"Then {beeper.beep_word} again, small as a hiccup in a teacup."
    )
    world.say(
        f"{finder.id} blinked. {friend.id} blinked. "
        f"For one hushy moment, neither knew whether to giggle or gasp."
    )


def selfish_reach(world: World, finder: Entity, friend: Entity, gift: Gift) -> None:
    finder.memes["want_first"] += 1
    friend.memes["patience"] += 1
    world.say(
        f'"Maybe it is a prize for me first," said {finder.id}, reaching both paws toward it.'
    )
    if gift.share_mode == "one_each":
        world.say(
            f'"Or maybe," said {friend.id}, "it knows there are two of us, because that was a double beep."'
        )
    else:
        world.say(
            f'"Or maybe," said {friend.id}, "it is the kind of thing friends can use together."'
        )


def silly_suck_beat(world: World, finder: Entity, friend: Entity, seal: Seal) -> None:
    env = world.get("envelope")
    if seal.id == "sticker":
        env.meters["sticky"] = 1.0
    env.meters["silly_attempt"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{finder.id} puckered up. "Shall I suck the corner?" {finder.pronoun()} asked.'
    )
    world.say(
        f'"No, no, no," laughed {friend.id}. "Paper is for letters, not for lips."'
    )
    if env.meters["sticky"] >= THRESHOLD:
        world.say(
            f"That made them both snort, because the sticky flap looked far too bossy to taste nice."
        )
    else:
        world.say(
            f"That made them both snort, because the flap looked far too fussy to taste nice."
        )


def clue_and_choose(world: World, finder: Entity, friend: Entity, seal: Seal, opener: Opener) -> None:
    pred = predict_opening(world, seal.id, opener.id)
    world.facts["predicted_opens"] = pred["opens"]
    world.say(seal.clue)
    world.say(
        f'"Let us {opener.label}," said {friend.id}. '
        f'"A mystery is sweeter when the envelope stays whole."'
    )


def open_envelope(world: World, finder: Entity, friend: Entity, seal: Seal, opener: Opener) -> None:
    env = world.get("envelope")
    if opener_fits(seal, opener):
        env.meters["opened"] = 1.0
        propagate(world, narrate=False)
        world.say(
            f"So {finder.id} and {friend.id} leaned in close, and {finder.id} {opener.action}."
        )
    else:
        world.say(
            f"{finder.id} {opener.fail}."
        )


def reveal(world: World, finder: Entity, friend: Entity, beeper: Beeper, gift: Gift) -> None:
    world.say(beeper.reveal)
    world.say(
        f"Beside it lay {gift.phrase}, tucked in tissue thin as cloud."
    )
    if gift.share_mode == "one_each":
        world.say(
            f'"One for you, and one for me!" cried {finder.id}, and the grabby look fell right off {finder.pronoun("object")}.'
        )
    elif gift.share_mode == "take_turns":
        world.say(
            f'{finder.id} opened {finder.pronoun("possessive")} mouth to claim it all, then saw only one and paused. '
            f'"We can take turns," said {friend.id}, soft and sure.'
        )
    else:
        world.say(
            f'"It is long enough for both," said {friend.id}, holding the ribbon end in the light.'
        )


def share(world: World, finder: Entity, friend: Entity, gift: Gift) -> None:
    mode = sharing_outcome(gift)
    world.facts["shared_mode"] = mode
    propagate(world, narrate=False)
    if mode == "one_each":
        world.say(
            f"{finder.id} took one, and {friend.id} took one, and not a crumb of quarrel remained."
        )
    elif mode == "take_turns":
        world.say(
            f"They made a turn-taking rhyme -- \"One little press for you, one little press for me\" -- and the plan felt fair at once."
        )
    else:
        world.say(
            f"They held one end each, and the very shape of the gift told them how to share."
        )


def ending(world: World, finder: Entity, friend: Entity, gift: Gift, beeper: Beeper) -> None:
    world.say(
        gift.ending
    )
    world.say(
        f"And whether it went {beeper.beep_word} by nose or {beeper.beep_word} by thumb, "
        f"the best sound of all was the two-friend laugh that followed."
    )


def tell(
    place: Place,
    seal: Seal,
    opener: Opener,
    gift: Gift,
    beeper: Beeper,
    finder_name: str = "Pip",
    finder_type: str = "mouse_boy",
    friend_name: str = "Mim",
    friend_type: str = "mouse_girl",
) -> World:
    world = World(place=place)
    finder = world.add(Entity(id="finder", kind="character", type=finder_type, label=finder_name, role="finder"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    envelope = world.add(Entity(id="envelope", kind="thing", type="envelope", label="envelope"))

    finder.attrs["display"] = finder_name
    friend.attrs["display"] = friend_name
    finder.memes["want_first"] = 0.0
    friend.memes["patience"] = 0.0
    envelope.meters["found"] = 0.0
    envelope.meters["beeping"] = 0.0
    envelope.meters["opened"] = 0.0
    envelope.meters["sticky"] = 0.0
    envelope.meters["silly_attempt"] = 0.0
    world.facts["shared_mode"] = ""

    introduce(world, finder, friend)
    find_envelope(world, finder, friend, seal)

    world.para()
    hear_beep(world, finder, friend, beeper)
    selfish_reach(world, finder, friend, gift)
    silly_suck_beat(world, finder, friend, seal)
    clue_and_choose(world, finder, friend, seal, opener)

    world.para()
    open_envelope(world, finder, friend, seal, opener)
    reveal(world, finder, friend, beeper, gift)
    share(world, finder, friend, gift)

    world.para()
    ending(world, finder, friend, gift, beeper)

    world.facts.update(
        place=place,
        seal=seal,
        opener=opener,
        gift=gift,
        beeper=beeper,
        finder=finder,
        friend=friend,
        envelope=envelope,
        suspense_before_open=finder.memes["suspense"] >= 0 or friend.memes["suspense"] >= 0,
        opened=envelope.meters["opened"] >= THRESHOLD,
        humorous_attempt=envelope.meters["silly_attempt"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    gift = f["gift"]
    beeper = f["beeper"]
    return [
        f'Write a short nursery-rhyme-style story for a 3-to-5-year-old about a mysterious envelope that says "{beeper.beep_word}". Include sharing, humor, and suspense.',
        f"Tell a gentle rhyming story where two little friends find an envelope at {place.label}, hear a beep inside, and learn to share {gift.label}.",
        'Write a playful verse story that includes the exact words "envelope", "suck", and "beep", with a funny middle and a warm shared ending.',
    ]


KNOWLEDGE = {
    "envelope": [
        (
            "What is an envelope?",
            "An envelope is a folded paper cover that holds a letter or a little note inside. It keeps the message tucked away until someone opens it."
        )
    ],
    "beep": [
        (
            "What does beep mean?",
            "Beep is a short sound a tiny toy or machine can make. It is quick and bright, like a small sound saying hello."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting another person have some too, or taking turns in a fair way. It helps play feel kind and happy for everyone."
        )
    ],
    "sticker": [
        (
            "How do you open a sticker-sealed envelope?",
            "You lift the sticker edge gently and peel it back. Pulling slowly helps keep the paper from tearing."
        )
    ],
    "twine": [
        (
            "How do you open a twine bow?",
            "You find the loops and untie the bow instead of yanking it. Patient fingers work better than rough tugging."
        )
    ],
    "wax": [
        (
            "Why might a grown-up help with wax on an envelope?",
            "Wax can be firm and stuck fast, so a grown-up may use the right safe tool to loosen it. Getting help can protect the envelope and the thing inside."
        )
    ],
}


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    seal = f["seal"]
    opener = f["opener"]
    gift = f["gift"]
    beeper = f["beeper"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two little friends, {finder.label} and {friend.label}. They find a mysterious envelope together at {place.label}."
        ),
        (
            "Why did the envelope feel mysterious?",
            f"It felt mysterious because it suddenly said {beeper.beep_word} from the inside. That tiny sound made the friends pause and wonder what secret was tucked in there."
        ),
        (
            f'Why did {finder.label} not "{opener.label}" right away?',
            f"{finder.label} first reached for the surprise and even joked about the silly way to open it. Then {friend.label} slowed things down and noticed the clue on the {seal.label}, so they chose the proper method instead."
        ),
        (
            "What was the funny part?",
            f"The funny part was when {finder.label} asked about using a silly suck on the corner of the envelope. They both laughed because paper is not for lips, and the idea sounded ridiculous."
        ),
    ]
    if gift.share_mode == "one_each":
        qa.append(
            (
                "How did they share what was inside?",
                f"They shared it by taking one each. The gift itself solved the problem because there were two badges waiting inside, one for each friend."
            )
        )
    elif gift.share_mode == "take_turns":
        qa.append(
            (
                "How did they share when there was only one thing?",
                f"They shared by taking turns with the bell button. That was fair because there was only one, and their little turn-taking rhyme helped both friends agree happily."
            )
        )
    else:
        qa.append(
            (
                "How did they share the ribbon?",
                f"They shared it by holding one end each. The long shape of the ribbon made it easy for both of them to join the play at the same time."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the friends playing together instead of grabbing alone. {gift.ending}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"envelope", "beep", "sharing"} | set(f["seal"].tags)
    out: list[tuple[str, str]] = []
    for key in ["envelope", "beep", "sharing", "sticker", "twine", "wax"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:9} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  facts: shared_mode={world.facts.get('shared_mode')!r}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="gate",
        seal="sticker",
        opener="peel",
        gift="two_badges",
        beeper="chick",
        finder_name="Pip",
        finder_type="mouse_boy",
        friend_name="Mim",
        friend_type="mouse_girl",
    ),
    StoryParams(
        place="step",
        seal="twine",
        opener="untie",
        gift="bell_button",
        beeper="button",
        finder_name="Dot",
        finder_type="duck",
        friend_name="Moss",
        friend_type="frog",
    ),
    StoryParams(
        place="windowsill",
        seal="wax",
        opener="warm_spoon",
        gift="long_ribbon",
        beeper="timer",
        finder_name="Tess",
        finder_type="hen",
        friend_name="Nip",
        friend_type="mouse_boy",
    ),
]


def explain_opener(seal: Seal, opener: Opener) -> str:
    if opener.sense < SENSE_MIN:
        return (
            f"(Refusing opener '{opener.id}': it is a silly, low-sense choice for an envelope. "
            f"Try one that matches the seal, such as {', '.join(sorted(seal.opener_ids))}.)"
        )
    return (
        f"(No story: {opener.label} does not fit {seal.label}. "
        f"Pick a method meant for that kind of seal: {', '.join(sorted(seal.opener_ids))}.)"
    )


def resolve_entity_type_name(rng: random.Random, avoid_name: str = "") -> tuple[str, str]:
    name = rng.choice([n for n in FINDER_NAMES if n != avoid_name])
    etype = rng.choice(FINDER_TYPES)
    return name, etype


ASP_RULES = r"""
% sensible openers only
sensible_opener(O) :- opener(O), sense(O, S), sense_min(M), S >= M.

% compatibility gate
fit(S, O) :- seal(S), opener(O), opens(O, S).
shareable(G) :- gift(G), share_mode(G, one_each).
shareable(G) :- gift(G), share_mode(G, take_turns).
shareable(G) :- gift(G), share_mode(G, hold_ends).

valid(P, S, O, G, B) :- place(P), seal(S), opener(O), gift(G), beeper(B),
                        sensible_opener(O), fit(S, O), shareable(G).

% inferred ending mode
outcome(one_each) :- chosen_gift(G), share_mode(G, one_each).
outcome(take_turns) :- chosen_gift(G), share_mode(G, take_turns).
outcome(hold_ends) :- chosen_gift(G), share_mode(G, hold_ends).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for seal_id, seal in SEALS.items():
        lines.append(asp.fact("seal", seal_id))
        for opener_id in sorted(seal.opener_ids):
            lines.append(asp.fact("seal_accepts", seal_id, opener_id))
    for opener_id, opener in OPENERS.items():
        lines.append(asp.fact("opener", opener_id))
        lines.append(asp.fact("sense", opener_id, opener.sense))
        for seal_id in sorted(opener.opens):
            lines.append(asp.fact("opens", opener_id, seal_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        lines.append(asp.fact("share_mode", gift_id, gift.share_mode))
    for beeper_id in BEEPERS:
        lines.append(asp.fact("beeper", beeper_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(gift_id: str) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("chosen_gift", gift_id), "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rhyming mystery envelope, a silly almost-mistake, and a shared ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seal", choices=SEALS)
    ap.add_argument("--opener", choices=OPENERS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--beeper", choices=BEEPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.seal and args.opener:
        seal = SEALS[args.seal]
        opener = OPENERS[args.opener]
        if opener.sense < SENSE_MIN or not opener_fits(seal, opener):
            raise StoryError(explain_opener(seal, opener))
    if args.gift and not gift_supports_sharing(GIFTS[args.gift]):
        raise StoryError("(No story: that gift does not support a clear sharing ending.)")

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.seal is None or c[1] == args.seal)
        and (args.opener is None or c[2] == args.opener)
        and (args.gift is None or c[3] == args.gift)
        and (args.beeper is None or c[4] == args.beeper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, seal_id, opener_id, gift_id, beeper_id = rng.choice(sorted(combos))
    finder_name, finder_type = resolve_entity_type_name(rng)
    friend_name, friend_type = resolve_entity_type_name(rng, avoid_name=finder_name)
    return StoryParams(
        place=place_id,
        seal=seal_id,
        opener=opener_id,
        gift=gift_id,
        beeper=beeper_id,
        finder_name=finder_name,
        finder_type=finder_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        seal = SEALS[params.seal]
        opener = OPENERS[params.opener]
        gift = GIFTS[params.gift]
        beeper = BEEPERS[params.beeper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]!r}.)") from err

    if opener.sense < SENSE_MIN or not opener_fits(seal, opener):
        raise StoryError(explain_opener(seal, opener))
    if not gift_supports_sharing(gift):
        raise StoryError("(No story: that gift does not support a clear sharing ending.)")

    world = tell(
        place=place,
        seal=seal,
        opener=opener,
        gift=gift,
        beeper=beeper,
        finder_name=params.finder_name,
        finder_type=params.finder_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
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
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for gift_id, gift in GIFTS.items():
        py_out = sharing_outcome(gift)
        cl_out = asp_outcome(gift_id)
        if py_out != cl_out:
            rc = 1
            print(f"MISMATCH in outcome for {gift_id}: python={py_out} clingo={cl_out}")
    if rc == 0:
        print(f"OK: sharing outcome matches for {len(GIFTS)} gifts.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke story was empty")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(17))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default-resolved story was empty")
        print("OK: default resolve/generate succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, seal, opener, gift, beeper) combos:\n")
        for place_id, seal_id, opener_id, gift_id, beeper_id in combos:
            print(f"  {place_id:10} {seal_id:8} {opener_id:11} {gift_id:12} {beeper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.finder_name} & {p.friend_name}: {p.seal}, {p.gift}, {p.beeper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
