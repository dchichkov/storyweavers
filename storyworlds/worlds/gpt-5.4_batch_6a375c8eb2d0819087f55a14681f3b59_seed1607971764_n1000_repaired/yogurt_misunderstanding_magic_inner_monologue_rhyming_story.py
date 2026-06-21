#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yogurt_misunderstanding_magic_inner_monologue_rhyming_story.py
==========================================================================================

A standalone story world for a tiny rhyming tale about yogurt, a sweet
misunderstanding, and a little bit of magic.

Premise
-------
A child hears a grown-up talk about a "moon bowl", "fairy bowl", or "brownie
bowl" of yogurt and misunderstands the phrase. The child thinks a magical guest
is meant to eat the yogurt, carries the bowl to the matching place, and whispers
a secret wish. A matching magical helper wakes, hears the child's inner
monologue, and helps the grown-up explain the mix-up kindly. Sometimes the bowl
waits long enough to make a small sticky mess first; either way, the ending is
gentle and complete.

The world model tracks:
- typed entities with physical meters (tilt, drip, sticky, cleaned)
- emotional memes (wonder, worry, relief, trust, clarity)
- a small causal rule engine
- a reasonableness gate plus an inline ASP twin
- three Q&A sets grounded in world state rather than parsing rendered English

Run it
------
    python storyworlds/worlds/gpt-5.4/yogurt_misunderstanding_magic_inner_monologue_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/yogurt_misunderstanding_magic_inner_monologue_rhyming_story.py --guest moon
    python storyworlds/worlds/gpt-5.4/yogurt_misunderstanding_magic_inner_monologue_rhyming_story.py --place pantry
    python storyworlds/worlds/gpt-5.4/yogurt_misunderstanding_magic_inner_monologue_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/yogurt_misunderstanding_magic_inner_monologue_rhyming_story.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class GuestIdea:
    id: str
    label: str
    bowl_name: str
    actual_meaning: str
    place: str
    helper: str
    whisper_word: str
    sign: str
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
class Place:
    id: str
    label: str
    phrase: str
    intro: str
    vulnerability: int
    visitor: str
    cleanup: str
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
    label: str
    phrase: str
    wake_line: str
    sparkle: str
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
class Topping:
    id: str
    label: str
    shape: str
    swirl: str
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


def _r_drip(world: World) -> list[str]:
    bowl = world.entities.get("bowl")
    place = world.entities.get("place")
    child = world.entities.get("child")
    if not bowl or not place or not child:
        return []
    if bowl.attrs.get("set_down") != 1:
        return []
    if world.facts.get("delay", 0) < place.attrs.get("vulnerability", 0):
        return []
    sig = ("drip", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bowl.meters["drip"] += 1
    place.meters["sticky"] += 1
    child.memes["worry"] += 1
    return ["__drip__"]


def _r_workload(world: World) -> list[str]:
    place = world.entities.get("place")
    grownup = world.entities.get("grownup")
    if not place or not grownup:
        return []
    if place.meters["sticky"] < THRESHOLD:
        return []
    sig = ("workload", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    grownup.meters["workload"] += 1
    return []


def _r_clarity(world: World) -> list[str]:
    helper = world.entities.get("helper")
    child = world.entities.get("child")
    if not helper or not child:
        return []
    if helper.meters["awake"] < THRESHOLD:
        return []
    sig = ("clarity", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["wonder"] += 1
    child.memes["clarity"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="drip", tag="physical", apply=_r_drip),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="clarity", tag="emotional", apply=_r_clarity),
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


def valid_combo(guest_id: str, place_id: str, helper_id: str) -> bool:
    guest = GUESTS[guest_id]
    return guest.place == place_id and guest.helper == helper_id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for gid, guest in GUESTS.items():
        if guest.place in PLACES and guest.helper in HELPERS:
            combos.append((gid, guest.place, guest.helper))
    return combos


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    return "sticky_then_shared" if params.delay >= place.vulnerability else "shared"


def explain_rejection(guest_id: str, place_id: str, helper_id: str) -> str:
    guest = GUESTS[guest_id]
    place = PLACES[place_id]
    helper = HELPERS[helper_id]
    return (
        f"(No story: {guest.label} belongs with {PLACES[guest.place].phrase} and "
        f"{HELPERS[guest.helper].phrase}, not with {place.phrase} and {helper.phrase}. "
        "This tiny world only tells misunderstandings when the place and magic match.)"
    )


def predict_stickiness(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.facts["delay"] = delay
    sim.get("bowl").attrs["set_down"] = 1
    propagate(sim, narrate=False)
    return {
        "sticky": sim.get("place").meters["sticky"] >= THRESHOLD,
        "workload": sim.get("grownup").meters["workload"],
    }


def opening(world: World, child: Entity, grownup: Entity, topping: Topping) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} hummed through the kitchen light, soft and bright and small, "
        f"while {grownup.pronoun('possessive')} spoon made {topping.swirl} loops around the bowl."
    )
    world.say(
        f"Cool yogurt shone like morning snow, a creamy, sleepy white, "
        f"and everything looked ready for a gentle little night."
    )


def grownup_line(world: World, grownup: Entity, guest: GuestIdea) -> None:
    world.say(
        f'"Set this {guest.bowl_name} in the right place later," '
        f"{grownup.pronoun()} said with easy cheer. "
        f'"It goes with {guest.actual_meaning}."'
    )


def inner_monologue(world: World, child: Entity, guest: GuestIdea) -> None:
    child.memes["curiosity"] += 1
    thought = (
        f"If it is the {guest.bowl_name}, maybe the real {guest.label} is coming. "
        f"Maybe {guest.pronoun_word if False else guest.label} feels shy and hungry in the hush."
    )
    world.facts["thought_text"] = thought
    world.say(
        f'{child.id} blinked and thought, "If a real {guest.label} is coming near, '
        f'I should be brave and set the yogurt here."'
    )


def sneak_bowl(world: World, child: Entity, place_ent: Entity, guest: GuestIdea, place: Place) -> None:
    bowl = world.get("bowl")
    bowl.attrs["set_down"] = 1
    bowl.attrs["location"] = place.id
    bowl.meters["tilt"] += 1
    child.memes["secret"] += 1
    world.say(
        f"So tiptoe-soft, with careful toes and one small balancing hand, "
        f"{child.id} carried the yogurt bowl to {place.phrase} as planned."
    )
    world.say(
        f"{place.intro} There {child.pronoun()} set the bowl down slow and low, "
        f"for {guest.label} to find in silver glow."
    )


def whisper(world: World, child: Entity, guest: GuestIdea) -> None:
    child.memes["hope"] += 1
    world.say(
        f'{child.id} bent close and whispered, "{guest.whisper_word}, if you are near, '
        f'here is a creamy cup of cheer."'
    )


def narrate_drip(world: World, place: Place) -> None:
    if world.get("place").meters["sticky"] >= THRESHOLD:
        world.say(
            f"But while the bowl sat quiet there, a little dollop took a slide; "
            f"it made {place.cleanup}, and {place.visitor} came to sniff beside."
        )


def awaken_helper(world: World, helper: Helper, child: Entity, guest: GuestIdea) -> None:
    helper_ent = world.get("helper")
    helper_ent.meters["awake"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.sparkle}, and {helper.phrase} gave a tiny, twinkling sign. "
        f'{helper.wake_line} "{guest.label.capitalize()} likes kind hearts," it seemed to chime, '
        f'"but ask what words mean next time."'
    )


def grownup_finds(world: World, grownup: Entity, child: Entity, guest: GuestIdea, place: Place) -> None:
    sticky = world.get("place").meters["sticky"] >= THRESHOLD
    if sticky:
        world.say(
            f"{grownup.label_word.capitalize()} came and saw the shiny drip, the bowl, the hopeful face, "
            f"and knelt beside {child.id} right there in {place.phrase}."
        )
    else:
        world.say(
            f"{grownup.label_word.capitalize()} came and found the waiting bowl and {child.id} tucked nearby, "
            f"with one big question in {child.pronoun('possessive')} eyes and moonlight in the sky."
        )
    world.say(
        f'"Oh, sweet pea, I meant {guest.actual_meaning}," {grownup.pronoun()} said. '
        f'"I did not mean the real {guest.label} needed to be fed."'
    )


def explain_and_clean(world: World, grownup: Entity, child: Entity, place: Place) -> None:
    sticky = world.get("place").meters["sticky"] >= THRESHOLD
    child.memes["trust"] += 1
    child.memes["relief"] += 1
    child.memes["clarity"] += 1
    child.memes["worry"] = 0.0
    if sticky:
        world.get("place").meters["cleaned"] += 1
        world.say(
            f"Together they wiped the little spot till everything was neat, "
            f"and {grownup.label_word} said, \"Questions first can make mistakes much sweeter to complete.\""
        )
    else:
        world.say(
            f'{child.id} let out a soft "ohhh" sound, the kind that melts a knot, '
            f'and {grownup.label_word} smiled and said, "You asked with love a lot."'
        )


def finish_snack(world: World, child: Entity, grownup: Entity, guest: GuestIdea, topping: Topping) -> None:
    bowl = world.get("bowl")
    bowl.attrs["set_down"] = 0
    bowl.attrs["location"] = "table"
    bowl.meters["served"] += 1
    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    sign = guest.sign
    world.say(
        f"Back at the table, {grownup.label_word} tucked {topping.shape} on top just right, "
        f"so the yogurt wore {sign} and gleamed with cozy light."
    )
    world.say(
        f'{child.id} took a spoon and thought, "Next time I will ask before I race. '
        f'But magic still may wink at me in any quiet place."'
    )
    world.say(
        f"So creamy yogurt, kind clear words, and one small rhyming night "
        f"turned mix-up into sharing, and the ending tasted right."
    )


def tell(
    guest: GuestIdea,
    place: Place,
    helper: Helper,
    topping: Topping,
    child_name: str = "Nora",
    child_gender: str = "girl",
    grownup_type: str = "mother",
    trait: str = "dreamy",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"trait": trait},
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            label="the grown-up",
            role="grownup",
        )
    )
    bowl = world.add(
        Entity(
            id="bowl",
            type="bowl",
            label="the yogurt bowl",
            attrs={"set_down": 0, "location": "table"},
        )
    )
    place_ent = world.add(
        Entity(
            id="place",
            type="place",
            label=place.label,
            attrs={"vulnerability": place.vulnerability},
        )
    )
    helper_ent = world.add(
        Entity(
            id="helper",
            type="magic",
            label=helper.label,
        )
    )

    world.facts.update(
        child=child,
        grownup=grownup,
        bowl=bowl,
        place_cfg=place,
        place=place_ent,
        helper_cfg=helper,
        helper=helper_ent,
        guest=guest,
        topping=topping,
        delay=delay,
        outcome="shared",
        thought_text="",
    )

    opening(world, child, grownup, topping)
    grownup_line(world, grownup, guest)

    world.para()
    inner_monologue(world, child, guest)
    sneak_bowl(world, child, place_ent, guest, place)
    whisper(world, child, guest)
    propagate(world, narrate=False)
    narrate_drip(world, place)

    world.para()
    awaken_helper(world, helper, child, guest)
    grownup_finds(world, grownup, child, guest, place)
    explain_and_clean(world, grownup, child, place)

    world.para()
    finish_snack(world, child, grownup, guest, topping)

    world.facts["outcome"] = "sticky_then_shared" if place_ent.meters["sticky"] >= THRESHOLD else "shared"
    world.facts["sticky"] = place_ent.meters["sticky"] >= THRESHOLD
    world.facts["cleaned"] = place_ent.meters["cleaned"] >= THRESHOLD
    world.facts["magic_seen"] = helper_ent.meters["awake"] >= THRESHOLD
    return world


GUESTS = {
    "moon": GuestIdea(
        id="moon",
        label="moon",
        bowl_name="moon bowl",
        actual_meaning="our moon-shaped bedtime snack",
        place="windowsill",
        helper="moonbeam",
        whisper_word="Moon, moon",
        sign="a pale crescent on its smooth white face",
        tags={"moon", "asking", "magic"},
    ),
    "fairy": GuestIdea(
        id="fairy",
        label="fairy",
        bowl_name="fairy bowl",
        actual_meaning="the pretend fairy picnic for the dollhouse friends",
        place="garden_step",
        helper="fireflies",
        whisper_word="Fairy, fairy",
        sign="a ring of petal dots around the rim",
        tags={"fairy", "asking", "magic"},
    ),
    "brownie": GuestIdea(
        id="brownie",
        label="brownie",
        bowl_name="brownie bowl",
        actual_meaning="the little bowl that goes beside warm brownie squares",
        place="pantry",
        helper="whisk",
        whisper_word="Brownie, brownie",
        sign="a tiny cocoa heart on top",
        tags={"brownie", "asking", "magic"},
    ),
}

PLACES = {
    "windowsill": Place(
        id="windowsill",
        label="windowsill",
        phrase="the windowsill",
        intro="The curtains made a silver tent, and stars looked close enough to keep.",
        vulnerability=2,
        visitor="a curious moth",
        cleanup="a cool white bead on the painted ledge",
        tags={"window"},
    ),
    "garden_step": Place(
        id="garden_step",
        label="garden step",
        phrase="the garden step",
        intro="Outside, the leaves were whisper-thin, and flowerpots were still.",
        vulnerability=1,
        visitor="two small ants",
        cleanup="a creamy dot beside the stones",
        tags={"garden"},
    ),
    "pantry": Place(
        id="pantry",
        label="pantry shelf",
        phrase="the pantry shelf",
        intro="The pantry smelled of sugar and flour, snug and shadow-deep.",
        vulnerability=1,
        visitor="a house-cat nose at the door",
        cleanup="a sticky moon on the wooden shelf",
        tags={"pantry"},
    ),
}

HELPERS = {
    "moonbeam": Helper(
        id="moonbeam",
        label="moonbeam",
        phrase="a moonbeam",
        wake_line="A ribbon of light slid across the bowl and sang in a hush",
        sparkle="a silver stripe skipped over the spoon",
        tags={"moonbeam", "magic"},
    ),
    "fireflies": Helper(
        id="fireflies",
        label="fireflies",
        phrase="a ring of fireflies",
        wake_line="Three fireflies blinked above the bowl like lanterns on a string",
        sparkle="green-gold dots bobbed in the leaves",
        tags={"fireflies", "magic"},
    ),
    "whisk": Helper(
        id="whisk",
        label="whispering whisk",
        phrase="a whispering whisk",
        wake_line="The little whisk by the flour jar gave a soft tin-tinny swing",
        sparkle="flour dust twinkled like stars in a jar",
        tags={"whisk", "magic"},
    ),
}

TOPPINGS = {
    "berries": Topping(
        id="berries",
        label="berries",
        shape="berry dots",
        swirl="bright berry",
        tags={"berries", "yogurt"},
    ),
    "banana": Topping(
        id="banana",
        label="banana",
        shape="banana moons",
        swirl="banana",
        tags={"banana", "yogurt"},
    ),
    "honey": Topping(
        id="honey",
        label="honey",
        shape="honey curls",
        swirl="honey",
        tags={"honey", "yogurt"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lila", "Zoe", "Ava", "Tessa", "Ruby", "Ella"]
BOY_NAMES = ["Owen", "Ben", "Max", "Leo", "Finn", "Theo", "Eli", "Sam"]
TRAITS = ["dreamy", "careful", "curious", "gentle", "hopeful"]


@dataclass
class StoryParams:
    guest: str
    place: str
    helper: str
    topping: str
    child_name: str
    child_gender: str
    grownup: str
    trait: str
    delay: int = 0
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
    "yogurt": [
        (
            "What is yogurt?",
            "Yogurt is a soft, creamy food made from milk. People often eat it with fruit or honey.",
        )
    ],
    "asking": [
        (
            "What should you do if you are not sure what a grown-up means?",
            "You can stop and ask a question. Asking kindly helps clear up a misunderstanding before it turns into a bigger problem.",
        )
    ],
    "moon": [
        (
            "Why does the moon look bright at night?",
            "The moon looks bright because sunlight bounces off it. It shines in the night sky even though it does not make its own light.",
        )
    ],
    "fairy": [
        (
            "What is a fairy in stories?",
            "A fairy is a make-believe magical helper from storybooks. Fairies are part of pretend play and imagination.",
        )
    ],
    "brownie": [
        (
            "What is a brownie?",
            "A brownie is a soft chocolate treat that is baked in a pan and cut into squares. It is a dessert, not a pet.",
        )
    ],
    "moonbeam": [
        (
            "What is a moonbeam?",
            "A moonbeam is a way of talking about moonlight shining in a line or stripe. It is a poetic name for light from the moon.",
        )
    ],
    "fireflies": [
        (
            "Why do fireflies glow?",
            "Fireflies glow because their bodies make a tiny light. They use that light to signal in the dark.",
        )
    ],
    "whisk": [
        (
            "What is a whisk used for?",
            "A whisk is a kitchen tool used for stirring and beating foods. It helps mix things until they are smooth.",
        )
    ],
}
KNOWLEDGE_ORDER = ["yogurt", "asking", "moon", "fairy", "brownie", "moonbeam", "fireflies", "whisk"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guest = f["guest"]
    place = f["place_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a rhyming story for a 3-to-5-year-old that includes the word "yogurt", '
        f"a misunderstanding, a little magic, and a child's inner monologue."
    )
    if outcome == "sticky_then_shared":
        return [
            base,
            f"Tell a gentle rhyming story where {child.id} thinks a real {guest.label} is coming for a {guest.bowl_name}, "
            f"carries yogurt to {place.phrase}, makes a small sticky mess, and learns to ask first.",
            f"Write a magical bedtime poem-story in which a child misunderstands a grown-up's words about yogurt, "
            f"a helper appears, and the ending shows the child asking questions before hurrying off.",
        ]
    return [
        base,
        f"Tell a rhyming story where {child.id} thinks a real {guest.label} should be fed yogurt at {place.phrase}, "
        f"but a magical sign and a kind grown-up clear up the misunderstanding.",
        f"Write a sweet poem-story with inner thoughts, yogurt, and a tiny magical helper, ending in shared food and clearer words.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    guest = f["guest"]
    place = f["place_cfg"]
    helper = f["helper_cfg"]
    topping = f["topping"]
    sticky = f["sticky"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who heard something confusing about a bowl of yogurt, and {grownup.label_word} who explained it kindly.",
        ),
        (
            f"Why did {child.id} carry the yogurt to {place.phrase}?",
            f"{child.id} thought the words {guest.bowl_name!r} meant a real {guest.label} was coming to eat it. The misunderstanding made {child.pronoun('object')} try to leave the yogurt in the place that matched the idea.",
        ),
        (
            f"What was {child.id} thinking inside {child.pronoun('possessive')} head?",
            f'{child.pronoun("subject").capitalize()} was thinking that a real {guest.label} might be shy and hungry and need help. That inner monologue is why {child.pronoun()} acted so carefully instead of trying to be naughty.',
        ),
        (
            "How did the magic appear?",
            f"{helper.phrase.capitalize()} woke after {child.id} whispered to the imagined guest. The magic answered the feeling behind the mistake and nudged the story toward understanding.",
        ),
        (
            "What did the grown-up really mean?",
            f"{grownup.label_word.capitalize()} meant {guest.actual_meaning}, not a real hungry {guest.label}. The kind explanation turned the confusing phrase into something clear and ordinary.",
        ),
    ]
    if sticky:
        qa.append(
            (
                "Did anything messy happen before the misunderstanding was fixed?",
                f"Yes. A little bit of yogurt dripped and made {place.cleanup}. That happened because the bowl sat there long enough to become sticky before {grownup.label_word} arrived.",
            )
        )
        qa.append(
            (
                "How was the problem solved?",
                f"They cleaned the small sticky spot together and brought the bowl back to the table. After that, {grownup.label_word} explained the mistake and finished the snack in a calm, loving way.",
            )
        )
    else:
        qa.append(
            (
                "How was the problem solved?",
                f"The magic helper woke, and then {grownup.label_word} explained the words before there was any mess. After that, they took the yogurt back and shared it together.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with yogurt on the table, {topping.shape} on top, and a child who had learned to ask first. The last image proves that the misunderstanding changed into trust without losing the magic feeling.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"yogurt", "asking"}
    tags |= set(f["guest"].tags)
    tags |= set(f["helper_cfg"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or isinstance(v, int)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts.outcome: {world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        guest="moon",
        place="windowsill",
        helper="moonbeam",
        topping="banana",
        child_name="Nora",
        child_gender="girl",
        grownup="mother",
        trait="dreamy",
        delay=0,
    ),
    StoryParams(
        guest="fairy",
        place="garden_step",
        helper="fireflies",
        topping="berries",
        child_name="Max",
        child_gender="boy",
        grownup="father",
        trait="curious",
        delay=1,
    ),
    StoryParams(
        guest="brownie",
        place="pantry",
        helper="whisk",
        topping="honey",
        child_name="Lila",
        child_gender="girl",
        grownup="mother",
        trait="careful",
        delay=2,
    ),
    StoryParams(
        guest="moon",
        place="windowsill",
        helper="moonbeam",
        topping="berries",
        child_name="Theo",
        child_gender="boy",
        grownup="father",
        trait="hopeful",
        delay=2,
    ),
]


ASP_RULES = r"""
valid(G,P,H) :- guest(G), place(P), helper(H), guest_place(G,P), guest_helper(G,H).

sticky_then_shared :- chosen_place(P), delay(D), vulnerability(P,V), D >= V.
shared_only        :- chosen_place(P), delay(D), vulnerability(P,V), D < V.

outcome(sticky_then_shared) :- sticky_then_shared.
outcome(shared) :- shared_only.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid, guest in GUESTS.items():
        lines.append(asp.fact("guest", gid))
        lines.append(asp.fact("guest_place", gid, guest.place))
        lines.append(asp.fact("guest_helper", gid, guest.helper))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("vulnerability", pid, place.vulnerability))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming yogurt storyworld about misunderstanding, magic, and asking what words mean."
    )
    ap.add_argument("--guest", choices=sorted(GUESTS))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--topping", choices=sorted(TOPPINGS))
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the bowl sits before the grown-up arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (guest, place, helper) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.guest and args.place and args.helper:
        if not valid_combo(args.guest, args.place, args.helper):
            raise StoryError(explain_rejection(args.guest, args.place, args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.guest is None or combo[0] == args.guest)
        and (args.place is None or combo[1] == args.place)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    guest, place, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(pool)
    topping = args.topping or rng.choice(sorted(TOPPINGS))
    grownup = args.grownup or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        guest=guest,
        place=place,
        helper=helper,
        topping=topping,
        child_name=child_name,
        child_gender=gender,
        grownup=grownup,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.guest not in GUESTS:
        raise StoryError(f"(No story: unknown guest '{params.guest}'.)")
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.topping not in TOPPINGS:
        raise StoryError(f"(No story: unknown topping '{params.topping}'.)")
    if not valid_combo(params.guest, params.place, params.helper):
        raise StoryError(explain_rejection(params.guest, params.place, params.helper))

    world = tell(
        guest=GUESTS[params.guest],
        place=PLACES[params.place],
        helper=HELPERS[params.helper],
        topping=TOPPINGS[params.topping],
        child_name=params.child_name,
        child_gender=params.child_gender,
        grownup_type=params.grownup,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos matches ASP ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

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
        sample = generate(cases[0] if cases else CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verification failed: generated empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (guest, place, helper) combos:\n")
        for guest, place, helper in combos:
            print(f"  {guest:8} {place:12} {helper}")
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
            header = f"### {p.child_name}: {p.guest} / {p.place} / delay={p.delay} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
