#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mango_terry_ornery_bravery_suspense_ghost_story.py
==============================================================================

A standalone story world for a gentle ghost-story domain: Terry hears a spooky
sound in the dark, feels afraid, chooses a brave next step, and discovers that
the "ghost" is really something ordinary. The world always keeps the suspense
child-facing and safe, and the ending image proves what changed.

Seed requirements folded into the world:
- includes the words "mango", "terry", and "ornery"
- features Bravery and Suspense
- style close to a Ghost Story

Run it
------
    python storyworlds/worlds/gpt-5.4/mango_terry_ornery_bravery_suspense_ghost_story.py
    python storyworlds/worlds/gpt-5.4/mango_terry_ornery_bravery_suspense_ghost_story.py --place porch --sign banging
    python storyworlds/worlds/gpt-5.4/mango_terry_ornery_bravery_suspense_ghost_story.py --cause shutter --light hall_switch
    python storyworlds/worlds/gpt-5.4/mango_terry_ornery_bravery_suspense_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/mango_terry_ornery_bravery_suspense_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mango_terry_ornery_bravery_suspense_ghost_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
    detail: str
    dark_word: str
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
class Sign:
    id: str
    sound_text: str
    question_text: str
    approach_text: str
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
class Cause:
    id: str
    label: str
    signs: set[str]
    places: set[str]
    reveal_text: str
    fix_text: str
    ending_image: str
    helper_action: str
    needs_help: bool = False
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
class Light:
    id: str
    label: str
    phrase: str
    places: set[str]
    start_text: str
    glow_text: str
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


def _r_spook(world: World) -> list[str]:
    source = world.get("source")
    terry = world.get("Terry")
    place = world.get("place")
    if source.meters["active"] < THRESHOLD or source.meters["revealed"] >= THRESHOLD:
        return []
    sig = ("spook", world.facts["sign"].id, world.facts["cause"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    terry.memes["fear"] += 1
    terry.memes["suspense"] += 1
    place.memes["uneasy"] += 1
    return []


def _r_brave(world: World) -> list[str]:
    terry = world.get("Terry")
    light = world.get("light")
    if terry.meters["approach"] < THRESHOLD or light.meters["working"] < THRESHOLD:
        return []
    sig = ("brave", world.facts["light"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    terry.memes["bravery"] += 1
    return []


def _r_reveal(world: World) -> list[str]:
    terry = world.get("Terry")
    light = world.get("light")
    source = world.get("source")
    if terry.meters["approach"] < THRESHOLD or light.meters["working"] < THRESHOLD:
        return []
    if source.meters["active"] < THRESHOLD or source.meters["revealed"] >= THRESHOLD:
        return []
    sig = ("reveal", world.facts["cause"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["revealed"] += 1
    terry.memes["fear"] = 0.0
    terry.memes["relief"] += 1
    terry.memes["wonder"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spook", tag="emotional", apply=_r_spook),
    Rule(name="brave", tag="emotional", apply=_r_brave),
    Rule(name="reveal", tag="physical", apply=_r_reveal),
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
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "hallway": Place(
        id="hallway",
        label="hallway",
        phrase="the long upstairs hallway",
        detail="The framed pictures along the wall looked silver in the moonlight.",
        dark_word="the hallway bend",
        tags={"hallway"},
    ),
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the narrow attic stair",
        detail="The beams above made dark little triangles over the steps.",
        dark_word="the attic door",
        tags={"attic"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the back porch",
        detail="Outside, the wind brushed the hanging fern and the boards gave tiny sighs.",
        dark_word="the porch corner",
        tags={"porch"},
    ),
}

SIGNS = {
    "scratching": Sign(
        id="scratching",
        sound_text='Then came a soft scratch-scratch-scratch from the dark.',
        question_text='"Did you hear that?"',
        approach_text="The sound skipped once, then came again from the same spot.",
        tags={"sound"},
    ),
    "glowing_eyes": Sign(
        id="glowing_eyes",
        sound_text="Two little points of light blinked in the dark like ghost eyes.",
        question_text='"What was shining over there?"',
        approach_text="They did not move at first, which somehow made them feel even spookier.",
        tags={"eyes"},
    ),
    "banging": Sign(
        id="banging",
        sound_text='A hollow bang... bang... bang rolled through the dark.',
        question_text='"What keeps banging like that?"',
        approach_text="Each thump seemed to come after the wind took a breath.",
        tags={"sound"},
    ),
}

CAUSES = {
    "mango_cat": Cause(
        id="mango_cat",
        label="Mango the cat",
        signs={"scratching", "glowing_eyes"},
        places={"hallway", "attic", "porch"},
        reveal_text="It was only Mango, the family's mango-colored cat, with round bright eyes and one paw reaching through the crack.",
        fix_text="Terry opened the stuck door just enough for Mango to squeeze out, and Mango rubbed against Terry's legs as if saying thank you.",
        ending_image="Mango curled in Terry's lap, purring so steadily that the whole house felt softer.",
        helper_action="held the door while Terry made a gap",
        needs_help=True,
        tags={"cat", "bravery"},
    ),
    "shutter": Cause(
        id="shutter",
        label="an ornery shutter",
        signs={"banging"},
        places={"attic", "porch"},
        reveal_text="There was no ghost at all, only an ornery shutter tapping the wall whenever the wind pushed it open.",
        fix_text="Terry and the grown-up fastened the latch, and the banging stopped at once.",
        ending_image="The moon laid one quiet stripe across the floor, and nothing knocked anymore.",
        helper_action="reached up to fasten the loose latch",
        needs_help=True,
        tags={"shutter", "wind"},
    ),
    "coat_rack": Cause(
        id="coat_rack",
        label="a coat rack",
        signs={"glowing_eyes"},
        places={"hallway", "attic"},
        reveal_text="The glowing 'eyes' were only shiny buttons on a coat hanging from the rack, with a hat brim making the shape look tall and ghostly.",
        fix_text="Terry laughed, turned the coat the right way, and the scary face disappeared.",
        ending_image="After that, the hallway looked like a hallway again, not a place for ghosts.",
        helper_action="stood nearby with a warm hand on Terry's shoulder",
        needs_help=False,
        tags={"buttons", "light"},
    ),
}


LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        places={"hallway", "attic", "porch"},
        start_text="Terry took a small flashlight from the hook by the stairs.",
        glow_text="The clean white beam cut a brave little path through the dark.",
        tags={"flashlight", "light"},
    ),
    "hall_switch": Light(
        id="hall_switch",
        label="hall light",
        phrase="the hall light switch",
        places={"hallway"},
        start_text="Terry reached for the hall light switch by the picture frame.",
        glow_text="Warm yellow light spread along the wallpaper and chased the shadows into the corners.",
        tags={"switch", "light"},
    ),
    "attic_pull": Light(
        id="attic_pull",
        label="attic pull-cord",
        phrase="the attic pull-cord",
        places={"attic"},
        start_text="Terry stretched up and found the attic pull-cord in the dark.",
        glow_text="A dusty bulb blinked awake above the steps and made the air look less full of secrets.",
        tags={"bulb", "light"},
    ),
    "porch_lamp": Light(
        id="porch_lamp",
        label="porch lamp",
        phrase="the porch lamp",
        places={"porch"},
        start_text="Terry clicked on the porch lamp beside the door.",
        glow_text="A warm circle of porch light spilled over the boards and the flowerpots.",
        tags={"lamp", "light"},
    ),
}

GROWNUPS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["careful", "curious", "steady", "sleepy", "thoughtful"]


def sign_matches(cause_id: str, sign_id: str) -> bool:
    return sign_id in CAUSES[cause_id].signs


def cause_fits_place(cause_id: str, place_id: str) -> bool:
    return place_id in CAUSES[cause_id].places


def light_works(light_id: str, place_id: str) -> bool:
    return place_id in LIGHTS[light_id].places


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id in PLACES:
        for sign_id in SIGNS:
            for cause_id in CAUSES:
                if not (cause_fits_place(cause_id, place_id) and sign_matches(cause_id, sign_id)):
                    continue
                for light_id in LIGHTS:
                    if light_works(light_id, place_id):
                        combos.append((place_id, sign_id, cause_id, light_id))
    return combos


@dataclass
class StoryParams:
    place: str
    sign: str
    cause: str
    light: str
    grownup: str
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


def setup_night(world: World, terry: Entity, grownup: Entity, place: Place) -> None:
    terry.memes["cozy"] += 1
    world.say(
        f"One windy night, Terry was supposed to be walking quietly to bed when the house gave one long sigh. "
        f"Mango, the family's mango-colored cat, was nowhere on Terry's blanket where he usually slept."
    )
    world.say(
        f"Terry paused near {place.phrase}. {place.detail}"
    )
    world.say(
        f"The old place had an ornery way of creaking when the weather changed, and tonight every creak seemed to be listening back."
    )
    world.say(
        f"{grownup.label_word.capitalize()} was folding laundry nearby, close enough to hear if Terry called."
    )


def hear_sign(world: World, terry: Entity, place: Place, sign: Sign) -> None:
    source = world.get("source")
    source.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(sign.sound_text)
    world.say(
        f'Terry stopped so fast that even {terry.pronoun("possessive")} breathing felt loud. {sign.question_text} Terry whispered.'
    )
    if place.id == "attic":
        world.say("The dark above the stair looked deep enough to hide a whole ghost parade.")
    elif place.id == "porch":
        world.say("Beyond the screen door, the shadows shook whenever the wind touched them.")
    else:
        world.say("The hallway bend looked farther away than it had in the daytime.")


def choose_bravery(world: World, terry: Entity, grownup: Entity, light: Light, sign: Sign) -> None:
    tool = world.get("light")
    tool.meters["working"] = 0.0
    world.say(
        f'{grownup.label_word.capitalize()} looked up, listened once, and did not laugh. "We can check together," {grownup.pronoun()} said. "Bravery is doing the next careful thing."'
    )
    world.say(light.start_text)
    tool.meters["working"] += 1
    terry.meters["approach"] = 0.0
    world.say(light.glow_text)
    world.say(sign.approach_text)


def approach(world: World, terry: Entity, place: Place) -> None:
    terry.meters["approach"] += 1
    propagate(world, narrate=False)
    if terry.memes["bravery"] >= THRESHOLD:
        world.say(
            f"Terry's knees still felt wiggly, but {terry.pronoun()} took one step, then another, toward {place.dark_word}."
        )
    else:
        world.say(
            f"Terry took a small step toward {place.dark_word}, wishing the floorboards would please stop talking."
        )


def reveal(world: World, terry: Entity, grownup: Entity, cause: Cause) -> None:
    propagate(world, narrate=False)
    source = world.get("source")
    if source.meters["revealed"] < THRESHOLD:
        raise StoryError("(Story logic error: Terry approached with working light but nothing was revealed.)")
    world.say(cause.reveal_text)
    if cause.needs_help:
        world.say(
            f'{grownup.label_word.capitalize()} {cause.helper_action}, and Terry stayed close instead of running away.'
        )


def fix_problem(world: World, terry: Entity, cause: Cause) -> None:
    world.say(cause.fix_text)
    terry.memes["pride"] += 1
    terry.memes["bravery"] += 1
    if cause.id == "mango_cat":
        world.get("Mango").meters["safe"] += 1
        world.get("Mango").memes["relief"] += 1


def ending(world: World, terry: Entity, grownup: Entity, cause: Cause) -> None:
    terry.memes["safe"] += 1
    terry.memes["fear"] = 0.0
    world.say(
        f'Terry let out the laugh that had been hiding behind all that suspense. "{grownup.label_word.capitalize()}, it wasn\'t a ghost after all," {terry.pronoun()} said.'
    )
    world.say(
        f'"Most shadows are only waiting for a little light," {grownup.label_word} said.'
    )
    world.say(cause.ending_image)
    world.say(
        "When Terry climbed into bed at last, the dark did not feel full of ghosts anymore. It felt full of ordinary things with ordinary names."
    )


def tell(place: Place, sign: Sign, cause: Cause, light: Light,
         grownup_type: str = "grandmother", terry_trait: str = "steady") -> World:
    world = World()
    terry = world.add(Entity(
        id="Terry",
        kind="character",
        type="boy",
        label="Terry",
        role="hero",
        traits=["little", terry_trait],
        attrs={"trait": terry_trait},
    ))
    grownup = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        role="helper",
        attrs={},
    ))
    place_ent = world.add(Entity(id="place", type="place", label=place.label, attrs={"place_id": place.id}))
    source = world.add(Entity(id="source", type="cause", label=cause.label, attrs={"cause_id": cause.id}))
    mango = world.add(Entity(id="Mango", kind="character", type="cat", label="Mango", role="pet", attrs={}))
    light_ent = world.add(Entity(id="light", type="light", label=light.label, attrs={"light_id": light.id}))

    # Pre-initialize every fact/rule input before any propagate() call.
    terry.memes["fear"] = 0.0
    terry.memes["bravery"] = 0.0
    terry.memes["relief"] = 0.0
    terry.memes["suspense"] = 0.0
    terry.meters["approach"] = 0.0
    source.meters["active"] = 0.0
    source.meters["revealed"] = 0.0
    light_ent.meters["working"] = 0.0
    place_ent.memes["uneasy"] = 0.0
    mango.meters["safe"] = 0.0
    mango.memes["relief"] = 0.0

    world.facts.update(
        place=place,
        sign=sign,
        cause=cause,
        light=light,
        terry=terry,
        grownup=grownup,
    )

    setup_night(world, terry, grownup, place)
    world.para()
    hear_sign(world, terry, place, sign)
    choose_bravery(world, terry, grownup, light, sign)
    approach(world, terry, place)
    world.para()
    reveal(world, terry, grownup, cause)
    fix_problem(world, terry, cause)
    world.para()
    ending(world, terry, grownup, cause)
    world.facts.update(
        revealed=source.meters["revealed"] >= THRESHOLD,
        brave=terry.memes["bravery"] >= THRESHOLD,
        fear_peak=1 if terry.memes["suspense"] >= THRESHOLD else 0,
        mango_safe=mango.meters["safe"] >= THRESHOLD if cause.id == "mango_cat" else True,
    )
    return world


KNOWLEDGE = {
    "cat": [
        (
            "Why do cat eyes seem to glow in the dark?",
            "A cat's eyes can shine when light hits them because the back of the eye reflects light. That can look spooky if you only see the eyes first."
        )
    ],
    "shutter": [
        (
            "What is a shutter?",
            "A shutter is a wooden or metal cover by a window. If it comes loose, the wind can make it bang and knock."
        )
    ],
    "buttons": [
        (
            "Why can shiny buttons look scary at night?",
            "At night, a small bit of reflected light can look bigger and stranger than it really is. Your eyes are trying to guess from only a little information."
        )
    ],
    "flashlight": [
        (
            "What does a flashlight do?",
            "A flashlight makes a bright beam so you can see in the dark. Seeing clearly often turns a scary mystery into an ordinary thing."
        )
    ],
    "light": [
        (
            "Why do shadows look different at night?",
            "At night there is less light, so shapes lose their clear edges. Your brain may imagine a face or a ghost until you get a better look."
        )
    ],
    "wind": [
        (
            "How can wind make spooky sounds?",
            "Wind can push shutters, doors, plants, and loose things so they tap, scrape, or moan. The sound can seem mysterious until you find what the wind is moving."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is not pretending you are never scared. It is choosing a careful next step even while you still feel afraid."
        )
    ],
}
KNOWLEDGE_ORDER = ["cat", "shutter", "buttons", "flashlight", "light", "wind", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    sign = f["sign"]
    cause = f["cause"]
    light = f["light"]
    return [
        f'Write a gentle ghost-story for a 3-to-5-year-old where Terry hears {sign.id.replace("_", " ")} near the {place.label} and finds a brave way to look closer. Include the word "mango".',
        f"Tell a suspenseful but safe bedtime story in which Terry thinks something ghostly is hiding by the {place.label}, uses {light.phrase}, and discovers it is really {cause.label}.",
        'Write a child-facing ghost story that includes the words "mango" and "ornery" and ends with fear turning into relief.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    terry = f["terry"]
    grownup = f["grownup"]
    place = f["place"]
    sign = f["sign"]
    cause = f["cause"]
    light = f["light"]
    pw = grownup.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Terry, Mango the cat, and Terry's {pw}. Terry hears something spooky in the night and has to decide whether to run away or look carefully."
        ),
        (
            "What made the story feel spooky at first?",
            f"The dark place by the {place.label} and the {sign.id.replace('_', ' ')} made Terry think of a ghost. The house already sounded ornery in the wind, so every little sound felt bigger."
        ),
        (
            "How was Terry brave?",
            f"Terry was brave by checking the dark place instead of letting the fear grow and grow. {pw.capitalize()} helped by staying close and choosing {light.phrase}, so Terry could take a careful next step."
        ),
        (
            "What was the 'ghost' really?",
            f"It was really {cause.label}, not a ghost. The scary part came from seeing or hearing only a small clue before the light showed the whole truth."
        ),
    ]
    if cause.id == "mango_cat":
        qa.append(
            (
                "Why did Mango matter in the story?",
                "Mango was the real reason for the spooky mystery. Once Terry saw that Mango was stuck and needed help, fear changed into concern and then relief."
            )
        )
    else:
        qa.append(
            (
                "How did the problem stop being scary?",
                f"It stopped being scary when Terry got close enough to see exactly what was there. After that, {cause.fix_text[0].lower() + cause.fix_text[1:]}."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended quietly and safely. {cause.ending_image} That ending proves the scary feeling is gone."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["cause"].tags) | set(world.facts["light"].tags) | {"bravery"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hallway",
        sign="glowing_eyes",
        cause="coat_rack",
        light="hall_switch",
        grownup="grandmother",
        trait="careful",
        seed=101,
    ),
    StoryParams(
        place="porch",
        sign="banging",
        cause="shutter",
        light="porch_lamp",
        grownup="father",
        trait="steady",
        seed=102,
    ),
    StoryParams(
        place="attic",
        sign="scratching",
        cause="mango_cat",
        light="flashlight",
        grownup="mother",
        trait="curious",
        seed=103,
    ),
    StoryParams(
        place="attic",
        sign="banging",
        cause="shutter",
        light="attic_pull",
        grownup="grandfather",
        trait="thoughtful",
        seed=104,
    ),
]


def explain_combo_rejection(place_id: str, sign_id: str, cause_id: str, light_id: str) -> str:
    bits = []
    if place_id not in PLACES:
        bits.append(f"unknown place '{place_id}'")
    if sign_id not in SIGNS:
        bits.append(f"unknown sign '{sign_id}'")
    if cause_id not in CAUSES:
        bits.append(f"unknown cause '{cause_id}'")
    if light_id not in LIGHTS:
        bits.append(f"unknown light '{light_id}'")
    if bits:
        return "(No story: " + ", ".join(bits) + ".)"
    if not cause_fits_place(cause_id, place_id):
        return (
            f"(No story: {CAUSES[cause_id].label} does not fit the {PLACES[place_id].label}. "
            f"That cause belongs in {sorted(CAUSES[cause_id].places)}.)"
        )
    if not sign_matches(cause_id, sign_id):
        return (
            f"(No story: {CAUSES[cause_id].label} would not reasonably make {sign_id.replace('_', ' ')}. "
            f"Pick a sign it can cause: {sorted(CAUSES[cause_id].signs)}.)"
        )
    if not light_works(light_id, place_id):
        return (
            f"(No story: {LIGHTS[light_id].label} is not available in the {PLACES[place_id].label}. "
            f"Use a light that works there.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


ASP_RULES = r"""
fits_place(C, P) :- cause_place(C, P).
fits_sign(C, S)  :- cause_sign(C, S).
usable_light(L, P) :- light_place(L, P).

valid(P, S, C, L) :- place(P), sign(S), cause(C), light(L),
                     fits_place(C, P), fits_sign(C, S), usable_light(L, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for sign_id in SIGNS:
        lines.append(asp.fact("sign", sign_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for place_id in sorted(cause.places):
            lines.append(asp.fact("cause_place", cause_id, place_id))
        for sign_id in sorted(cause.signs):
            lines.append(asp.fact("cause_sign", cause_id, sign_id))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        for place_id in sorted(light.places):
            lines.append(asp.fact("light_place", light_id, place_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


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
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    # Smoke test ordinary generation so --verify fails if prose generation crashes.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    # Exercise a small batch of random valid generations.
    try:
        parser = build_parser()
        for seed in range(5):
            args = parser.parse_args(["--seed", str(seed)])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError(f"(Random smoke test produced empty story for seed {seed}.)")
        print("OK: random generation smoke tests succeeded.")
    except Exception as err:
        rc = 1
        print(f"RANDOM GENERATION TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Terry hears a ghostly sign, chooses a brave light, and finds the ordinary truth."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--sign", choices=sorted(SIGNS))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--light", choices=sorted(LIGHTS))
    ap.add_argument("--grownup", choices=sorted(GROWNUPS))
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
    explicit_place = args.place
    explicit_sign = args.sign
    explicit_cause = args.cause
    explicit_light = args.light

    if all(v is not None for v in (explicit_place, explicit_sign, explicit_cause, explicit_light)):
        combo = (explicit_place, explicit_sign, explicit_cause, explicit_light)
        if combo not in set(valid_combos()):
            raise StoryError(explain_combo_rejection(*combo))

    combos = [
        combo for combo in valid_combos()
        if (explicit_place is None or combo[0] == explicit_place)
        and (explicit_sign is None or combo[1] == explicit_sign)
        and (explicit_cause is None or combo[2] == explicit_cause)
        and (explicit_light is None or combo[3] == explicit_light)
    ]
    if not combos:
        place_id = explicit_place or next(iter(PLACES))
        sign_id = explicit_sign or next(iter(SIGNS))
        cause_id = explicit_cause or next(iter(CAUSES))
        light_id = explicit_light or next(iter(LIGHTS))
        raise StoryError(explain_combo_rejection(place_id, sign_id, cause_id, light_id))

    place_id, sign_id, cause_id, light_id = rng.choice(sorted(combos))
    grownup = args.grownup or rng.choice(sorted(GROWNUPS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        sign=sign_id,
        cause=cause_id,
        light=light_id,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.sign not in SIGNS:
        raise StoryError(f"(No story: unknown sign '{params.sign}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{params.cause}'.)")
    if params.light not in LIGHTS:
        raise StoryError(f"(No story: unknown light '{params.light}'.)")
    if params.grownup not in GROWNUPS:
        raise StoryError(f"(No story: unknown grownup '{params.grownup}'.)")

    combo = (params.place, params.sign, params.cause, params.light)
    if combo not in set(valid_combos()):
        raise StoryError(explain_combo_rejection(*combo))

    world = tell(
        place=PLACES[params.place],
        sign=SIGNS[params.sign],
        cause=CAUSES[params.cause],
        light=LIGHTS[params.light],
        grownup_type=params.grownup,
        terry_trait=params.trait,
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
        print(f"{len(combos)} compatible (place, sign, cause, light) combos:\n")
        for place_id, sign_id, cause_id, light_id in combos:
            print(f"  {place_id:8} {sign_id:13} {cause_id:10} {light_id}")
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
            header = f"### Terry at {p.place}: {p.sign} -> {p.cause} with {p.light}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
