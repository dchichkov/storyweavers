#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/triple_septic_movie_inner_monologue_repetition_ghost.py
===================================================================================

A standalone storyworld for a gentle ghost-story-shaped tale: after a spooky
movie, a child hears a repeated triple sound in the night, imagines a ghost,
and then learns that the old house is making an ordinary noise.

This world uses:
- inner monologue
- repetition
- the words "triple", "septic", and "movie"

Run it
------
    python storyworlds/worlds/gpt-5.4/triple_septic_movie_inner_monologue_repetition_ghost.py
    python storyworlds/worlds/gpt-5.4/triple_septic_movie_inner_monologue_repetition_ghost.py --setting farmhouse --cause vent_pipe
    python storyworlds/worlds/gpt-5.4/triple_septic_movie_inner_monologue_repetition_ghost.py --setting townhouse --cause vent_pipe
    python storyworlds/worlds/gpt-5.4/triple_septic_movie_inner_monologue_repetition_ghost.py --all
    python storyworlds/worlds/gpt-5.4/triple_septic_movie_inner_monologue_repetition_ghost.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/triple_septic_movie_inner_monologue_repetition_ghost.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
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
            "grandmother": "grandma",
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
class Setting:
    id: str
    place: str
    sleep_spot: str
    window_view: str
    adult_home: str
    has_tree: bool = False
    has_shutter: bool = False
    has_vent: bool = False
    has_pump: bool = False
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
class MovieNight:
    id: str
    title: str
    mood: str
    image: str
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
    sound: str
    repeated: str
    explain: str
    reveal: str
    needs: set[str] = field(default_factory=set)
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
    text: str
    reveal_text: str
    qa_text: str
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


def _r_noise_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    house = world.get("house")
    if house.meters["noise_hits"] >= 3 and ("fear", "triple") not in world.fired:
        world.fired.add(("fear", "triple"))
        child.memes["fear"] += 2
        child.memes["ghost_idea"] += 1
        out.append("__triple__")
    return out


def _r_reveal_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    adult = world.get("adult")
    if world.facts.get("cause_known") and ("calm", "reveal") not in world.fired:
        world.fired.add(("calm", "reveal"))
        child.memes["fear"] = 0.0
        child.memes["calm"] += 2
        child.memes["bravery"] += 1
        adult.memes["care"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_fear", tag="emotional", apply=_r_noise_fear),
    Rule(name="reveal_calm", tag="emotional", apply=_r_reveal_calm),
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


def cause_fits(setting: Setting, cause: Cause) -> bool:
    needed = set(cause.needs)
    if "tree" in needed and not setting.has_tree:
        return False
    if "shutter" in needed and not setting.has_shutter:
        return False
    if "vent" in needed and not setting.has_vent:
        return False
    if "pump" in needed and not setting.has_pump:
        return False
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def explain_rejection(setting: Setting, cause: Cause) -> str:
    if "vent" in cause.needs and not setting.has_vent:
        return (
            f"(No story: {setting.place} has no outside septic vent by the wall, "
            f"so {cause.label} cannot make the night noise there.)"
        )
    if "pump" in cause.needs and not setting.has_pump:
        return (
            f"(No story: {setting.place} has no septic pump room, so {cause.label} "
            f"is not a plausible source there.)"
        )
    if "tree" in cause.needs and not setting.has_tree:
        return (
            f"(No story: {setting.place} has no tree close enough to tap the house, "
            f"so that repeated sound would have no source.)"
        )
    if "shutter" in cause.needs and not setting.has_shutter:
        return (
            f"(No story: {setting.place} has no loose shutter at the window, so "
            f"that ghostly tapping cannot happen there.)"
        )
    return "(No story: this sound source does not fit the chosen place.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid, cause in CAUSES.items():
            if cause_fits(setting, cause):
                combos.append((sid, cid))
    return combos


def predict_ghost_worry(world: World, cause: Cause) -> dict:
    sim = world.copy()
    hear_triple(sim, cause, narrate=False)
    child = sim.get("child")
    return {
        "fear": child.memes["fear"],
        "ghost_idea": child.memes["ghost_idea"],
    }


def setup_evening(world: World, child: Entity, adult: Entity, movie: MovieNight) -> None:
    child.memes["cozy"] += 1
    adult.memes["care"] += 1
    world.say(
        f"That evening, {child.id} curled up in {world.setting.place} with "
        f"{child.pronoun('possessive')} {adult.label_word} and watched a {movie.mood} movie "
        f"called {movie.title}. On the screen, {movie.image}."
    )
    world.say(
        f"When the movie ended, the rooms around them felt much darker than before."
    )


def bedtime(world: World, child: Entity, adult: Entity) -> None:
    world.say(
        f"Later, {child.id} climbed into {world.setting.sleep_spot}. Outside the window, "
        f"{world.setting.window_view}."
    )
    world.say(
        f'From down the hall, {child.pronoun("possessive")} {adult.label_word} called, '
        f'"Good night."'
    )


def hear_triple(world: World, cause: Cause, narrate: bool = True) -> None:
    house = world.get("house")
    house.meters["noise_hits"] += 3
    house.meters["mystery"] += 1
    world.facts["heard_triple"] = True
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"Then it came: {cause.repeated} {cause.sound}. {cause.repeated} {cause.sound}. "
            f"{cause.repeated} {cause.sound}. It was a triple little knock, over and over, "
            f"as if the house itself were repeating a secret."
        )


def inner_monologue(world: World, child: Entity, cause: Cause) -> None:
    pred = predict_ghost_worry(world, cause)
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["thinking"] += 1
    world.say(
        f'{child.id} pulled the blanket to {child.pronoun("possessive")} chin. '
        f'"A ghost?" {child.pronoun()} thought. "No, not a ghost. But what if it was a ghost? '
        f'No, not a ghost. But what if it was?"'
    )
    world.say(
        f'The thought went round and round in {child.pronoun("possessive")} head: '
        f'"Tap, tap, tap. Tap, tap, tap. Why triple? Why again?"'
    )


def call_for_help(world: World, child: Entity, adult: Entity) -> None:
    child.memes["trust"] += 1
    adult.memes["care"] += 1
    world.say(
        f'At last {child.id} whispered, "{adult.label_word.capitalize()}?" Then louder: '
        f'"{adult.label_word.capitalize()}, can you come here?"'
    )


def investigate(world: World, child: Entity, adult: Entity, response: Response) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came in at once and sat beside {child.id}. "
        f"{response.text}"
    )


def reveal(world: World, adult: Entity, cause: Cause, response: Response) -> None:
    world.facts["cause_known"] = True
    propagate(world, narrate=False)
    world.say(
        f'{adult.label_word.capitalize()} listened once, then smiled a small, calm smile. '
        f'"I know that sound," {adult.pronoun()} said. "{cause.explain}"'
    )
    world.say(
        response.reveal_text.format(reveal=cause.reveal)
    )


def ending(world: World, child: Entity, adult: Entity, cause: Cause) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"{child.id} listened again. The sound was still there, but it was only a sound now, "
        f"not a ghost. The old {cause.label} had not been calling {child.pronoun('object')}; "
        f"it had only been doing its job."
    )
    world.say(
        f'Soon {child.id} gave a tiny laugh. "Not a ghost," {child.pronoun()} murmured. '
        f'"Not a ghost. Just the septic house talking in its sleepy way."'
    )
    world.say(
        f"With {adult.label_word} nearby and the dark no longer full of guesses, "
        f"{child.id} snuggled down and fell asleep."
    )


def tell(
    setting: Setting,
    movie: MovieNight,
    cause: Cause,
    response: Response,
    *,
    child_name: str = "Nora",
    child_gender: str = "girl",
    adult_type: str = "grandmother",
    trait: str = "thoughtful",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait],
            attrs={},
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            label="the grown-up",
            role="adult",
            attrs={},
        )
    )
    house = world.add(
        Entity(
            id="house",
            kind="thing",
            type="house",
            label="the house",
            attrs={},
        )
    )
    source = world.add(
        Entity(
            id="source",
            kind="thing",
            type="cause",
            label=cause.label,
            attrs={},
        )
    )

    child.memes["fear"] = 0.0
    child.memes["calm"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["ghost_idea"] = 0.0
    adult.memes["care"] = 0.0
    house.meters["noise_hits"] = 0.0
    house.meters["mystery"] = 0.0
    source.meters["ordinary"] = 1.0
    world.facts.update(
        child=child,
        adult=adult,
        house=house,
        source=source,
        setting=setting,
        movie=movie,
        cause=cause,
        response=response,
        heard_triple=False,
        cause_known=False,
    )

    setup_evening(world, child, adult, movie)
    bedtime(world, child, adult)

    world.para()
    hear_triple(world, cause)
    inner_monologue(world, child, cause)
    call_for_help(world, child, adult)

    world.para()
    investigate(world, child, adult, response)
    reveal(world, adult, cause, response)

    world.para()
    ending(world, child, adult, cause)
    return world


@dataclass
class StoryParams:
    setting: str
    movie: str
    cause: str
    response: str
    child_name: str
    child_gender: str
    adult_type: str
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


SETTINGS = {
    "farmhouse": Setting(
        id="farmhouse",
        place="an old farmhouse",
        sleep_spot="the creaky guest bed",
        window_view="a silver yard and the dark shape of the garden",
        adult_home="at the end of the hall",
        has_tree=True,
        has_shutter=True,
        has_vent=True,
        has_pump=False,
        tags={"yard", "old_house"},
    ),
    "lakeside_cabin": Setting(
        id="lakeside_cabin",
        place="a lakeside cabin",
        sleep_spot="a narrow pine bed",
        window_view="black water and reeds moving in the moonlight",
        adult_home="in the tiny next room",
        has_tree=True,
        has_shutter=False,
        has_vent=True,
        has_pump=False,
        tags={"lake", "cabin"},
    ),
    "townhouse": Setting(
        id="townhouse",
        place="a brick townhouse",
        sleep_spot="the upstairs bed under a patchwork quilt",
        window_view="a small fenced yard and the alley light",
        adult_home="in the room across the landing",
        has_tree=False,
        has_shutter=True,
        has_vent=False,
        has_pump=False,
        tags={"town"},
    ),
    "country_house": Setting(
        id="country_house",
        place="a country house with a cool basement",
        sleep_spot="the little bed beside a tall dresser",
        window_view="a gravel drive and a leaning fence",
        adult_home="downstairs by the lamp-lit kitchen",
        has_tree=False,
        has_shutter=False,
        has_vent=False,
        has_pump=True,
        tags={"basement"},
    ),
}

MOVIES = {
    "lantern_castle": MovieNight(
        id="lantern_castle",
        title="The Lantern in the Castle",
        mood="spooky-but-soft",
        image="a glowing hallway and a brave cat carrying a key",
        tags={"movie"},
    ),
    "moon_pirates": MovieNight(
        id="moon_pirates",
        title="Moon Pirates on the Mist",
        mood="creepy",
        image="a foggy ship and three bells ringing far away",
        tags={"movie"},
    ),
    "midnight_train": MovieNight(
        id="midnight_train",
        title="The Midnight Toy Train",
        mood="shivery",
        image="a tiny train puffing through blue moonlight",
        tags={"movie"},
    ),
}

CAUSES = {
    "vent_pipe": Cause(
        id="vent_pipe",
        label="septic vent pipe",
        sound="tok",
        repeated="Tap",
        explain="That is the septic vent pipe outside. When air moves through it, the pipe taps the wall.",
        reveal="They looked through the curtain and saw the slim septic pipe beside the window, making the neat little tapping sound.",
        needs={"vent"},
        tags={"septic", "pipe"},
    ),
    "pump_thump": Cause(
        id="pump_thump",
        label="septic pump",
        sound="thump",
        repeated="Thump",
        explain="That is the septic pump in the basement. When it wakes up for a moment, it gives three little thumps in the pipes.",
        reveal="Together they listened at the floor, and the soft basement pump answered below them: a working sound, not a whispering ghost.",
        needs={"pump"},
        tags={"septic", "pump"},
    ),
    "branch_tap": Cause(
        id="branch_tap",
        label="branch by the shutter",
        sound="tick",
        repeated="Tick",
        explain="That is only a branch tapping near the old wall after the movie made everything feel stranger than it was.",
        reveal="At the window they found a thin branch brushing the side of the house in the night breeze.",
        needs={"tree"},
        tags={"branch"},
    ),
    "loose_shutter": Cause(
        id="loose_shutter",
        label="loose shutter",
        sound="clack",
        repeated="Clack",
        explain="That is the loose shutter by the window. It keeps making the same triple knock when the night air nudges it.",
        reveal="The shutter moved once, then again, then a third time, exactly the way the sound had repeated in the dark.",
        needs={"shutter"},
        tags={"shutter"},
    ),
}

RESPONSES = {
    "bedside_lamp": Response(
        id="bedside_lamp",
        sense=3,
        text="Then the lamp clicked on, and the room stopped looking like a place for ghosts and started looking like a room again.",
        reveal_text="{reveal}",
        qa_text="turned on the bedside lamp and checked the sound together",
        tags={"light", "adult_help"},
    ),
    "flashlight_walk": Response(
        id="flashlight_walk",
        sense=3,
        text="Then {adult} took a flashlight from the shelf, and the two of them followed the sound instead of hiding from it.".replace("{adult}", "the grown-up"),
        reveal_text="{reveal}",
        qa_text="used a flashlight and followed the sound together",
        tags={"light", "adult_help"},
    ),
    "hide_under_blanket": Response(
        id="hide_under_blanket",
        sense=1,
        text="They pulled the blanket over everything and waited without learning anything at all.",
        reveal_text="{reveal}",
        qa_text="hid under the blanket",
        tags={"hide"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "Rose", "Ella", "June", "Tess"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Finn", "Max", "Sam", "Eli", "Theo"]
TRAITS = ["thoughtful", "curious", "careful", "wide-eyed", "gentle"]
ADULT_TYPES = ["mother", "father", "aunt", "grandmother"]

KNOWLEDGE = {
    "movie": [
        (
            "Why can a spooky movie make ordinary sounds seem scarier?",
            "A spooky movie can fill your mind with creepy pictures, so later an ordinary noise may feel bigger and stranger than it really is. Your ears hear the same sound, but your thoughts can make it seem like a ghost."
        )
    ],
    "septic": [
        (
            "What is a septic system?",
            "A septic system is part of how some homes handle dirty water underground. It can include tanks, pipes, and sometimes a pump, and those parts can make real house sounds."
        )
    ],
    "pipe": [
        (
            "Why do pipes make noises sometimes?",
            "Pipes can tap, hum, or thunk when water or air moves through them. In a quiet night, those little sounds can seem much louder."
        )
    ],
    "pump": [
        (
            "What does a pump do in a house?",
            "A pump helps move water from one place to another. When it turns on, it can make a short humming or thumping sound."
        )
    ],
    "branch": [
        (
            "Why can a tree branch sound like knocking?",
            "A branch can tap a wall or window again and again when the wind moves it. That repeated tapping can sound like someone knocking."
        )
    ],
    "shutter": [
        (
            "Why does a loose shutter make a spooky sound?",
            "A loose shutter can swing and knock against the wall when air pushes it. Because it repeats, it can sound like a secret knock in the dark."
        )
    ],
    "adult_help": [
        (
            "What should you do if a sound in the night scares you?",
            "Call a trusted grown-up and tell them what you heard. Looking together is safer and often helps you learn what the sound really is."
        )
    ],
    "light": [
        (
            "Why does turning on a light help when you feel scared?",
            "Light lets you see what is really there instead of guessing in the dark. When you can see clearly, your body often starts to feel calmer too."
        )
    ],
}
KNOWLEDGE_ORDER = ["movie", "septic", "pipe", "pump", "branch", "shutter", "adult_help", "light"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    movie = world.facts["movie"]
    cause = world.facts["cause"]
    return [
        (
            f'Write a gentle ghost-story-shaped tale for a 3-to-5-year-old that includes the words '
            f'"triple", "septic", and "movie". Use inner monologue and repetition.'
        ),
        (
            f"Tell a story where {child.id} watches a spooky movie, hears a triple night sound, "
            f"worries about a ghost, and then learns the noise came from {cause.label}."
        ),
        (
            f"Write a child-facing story with repeated sound words and worried thoughts, ending with "
            f"{adult.label_word} helping explain the ordinary cause of the noise."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    movie = world.facts["movie"]
    cause = world.facts["cause"]
    response = world.facts["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who felt scared after a spooky movie, and {child.pronoun('possessive')} {adult.label_word}, who came to help explain the night sound."
        ),
        (
            "Why did the house seem scary at first?",
            f"The movie had left spooky pictures in {child.id}'s mind, so the dark felt fuller than it really was. Then the repeated triple sound gave {child.pronoun('object')} something mysterious to worry about."
        ),
        (
            "What was the repeated sound like?",
            f"It came in a triple pattern again and again, which made it sound secret and ghostly. The repetition mattered because the same little sound kept returning in the quiet room."
        ),
        (
            f"Why did {child.id} think about a ghost?",
            f"{child.id} was alone in bed after the movie and heard the sound repeating in the dark. {child.pronoun().capitalize()} did not know the cause yet, so {child.pronoun('possessive')} thoughts turned the ordinary noise into something spooky."
        ),
        (
            f"How did {child.id}'s {adult.label_word} help?",
            f"{adult.label_word.capitalize()} {response.qa_text}. That helped because they did not just say 'do not worry' -- they checked the sound and found its real source."
        ),
        (
            "What was really making the sound?",
            f"It was {cause.label}. Once the cause was known, the noise stopped feeling like a ghost and started feeling ordinary."
        ),
        (
            "How did the story end?",
            f"It ended quietly, with {child.id} understanding the sound and feeling calm enough to sleep. The ending proves what changed because the same night noise was still there, but it no longer felt scary."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["movie"].tags) | set(world.facts["cause"].tags) | set(world.facts["response"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="farmhouse",
        movie="lantern_castle",
        cause="vent_pipe",
        response="bedside_lamp",
        child_name="Nora",
        child_gender="girl",
        adult_type="grandmother",
        trait="thoughtful",
    ),
    StoryParams(
        setting="country_house",
        movie="midnight_train",
        cause="pump_thump",
        response="flashlight_walk",
        child_name="Ben",
        child_gender="boy",
        adult_type="father",
        trait="curious",
    ),
    StoryParams(
        setting="townhouse",
        movie="moon_pirates",
        cause="loose_shutter",
        response="bedside_lamp",
        child_name="Ava",
        child_gender="girl",
        adult_type="aunt",
        trait="careful",
    ),
    StoryParams(
        setting="lakeside_cabin",
        movie="lantern_castle",
        cause="branch_tap",
        response="flashlight_walk",
        child_name="Theo",
        child_gender="boy",
        adult_type="mother",
        trait="wide-eyed",
    ),
]


ASP_RULES = r"""
cause_fits(S, C) :- setting(S), cause(C), needs(C, tree), has_tree(S).
cause_fits(S, C) :- setting(S), cause(C), needs(C, shutter), has_shutter(S).
cause_fits(S, C) :- setting(S), cause(C), needs(C, vent), has_vent(S).
cause_fits(S, C) :- setting(S), cause(C), needs(C, pump), has_pump(S).
fits_all_needs(S, C) :- setting(S), cause(C),
                        not missing_need(S, C).
missing_need(S, C) :- needs(C, tree), not has_tree(S).
missing_need(S, C) :- needs(C, shutter), not has_shutter(S).
missing_need(S, C) :- needs(C, vent), not has_vent(S).
missing_need(S, C) :- needs(C, pump), not has_pump(S).

valid(S, C) :- setting(S), cause(C), fits_all_needs(S, C).

sensible(R) :- response(R), sense(R, X), sense_min(M), X >= M.

outcome(solved) :- chosen_response(R), sensible(R).
bad_choice :- chosen_response(R), not sensible(R).
outcome(unsolved) :- bad_choice.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_tree:
            lines.append(asp.fact("has_tree", sid))
        if s.has_shutter:
            lines.append(asp.fact("has_shutter", sid))
        if s.has_vent:
            lines.append(asp.fact("has_vent", sid))
        if s.has_pump:
            lines.append(asp.fact("has_pump", sid))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for need in sorted(c.needs):
            lines.append(asp.fact("needs", cid, need))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_response", params.response)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if RESPONSES[params.response].sense >= SENSE_MIN else "unsolved"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: after a spooky movie, a repeated night sound seems ghostly until a grown-up explains it."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--movie", choices=MOVIES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULT_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.setting and args.cause:
        setting = SETTINGS[args.setting]
        cause = CAUSES[args.cause]
        if not cause_fits(setting, cause):
            raise StoryError(explain_rejection(setting, cause))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cause is None or combo[1] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cause_id = rng.choice(sorted(combos))
    movie_id = args.movie or rng.choice(sorted(MOVIES))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_type = args.adult or rng.choice(sorted(ADULT_TYPES))
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        movie=movie_id,
        cause=cause_id,
        response=response_id,
        child_name=name,
        child_gender=gender,
        adult_type=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.movie not in MOVIES:
        raise StoryError(f"(Unknown movie: {params.movie})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.response and RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    setting = SETTINGS[params.setting]
    cause = CAUSES[params.cause]
    if not cause_fits(setting, cause):
        raise StoryError(explain_rejection(setting, cause))

    world = tell(
        setting=setting,
        movie=MOVIES[params.movie],
        cause=cause,
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cause) combos:\n")
        for setting, cause in combos:
            print(f"  {setting:14} {cause}")
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
            header = f"### {p.child_name}: {p.movie} at {p.setting} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
